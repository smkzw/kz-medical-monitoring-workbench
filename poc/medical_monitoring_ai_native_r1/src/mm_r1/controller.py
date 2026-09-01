"""Application-owned capability/work-unit controller for the isolated R1 POC.

The controller is intentionally small.  ``CapabilityRuntime`` owns one
provider-neutral attempt and ``Store`` owns authoritative work-unit progress;
this module binds the two without creating a second scheduler or promoting AI
output into medical facts.

Every assignment is written before dispatch and is immutable.  After a crash,
``reconcile`` rebuilds the exact frozen request and lets the durable attempt
journal decide whether execution must start, resume by replay, or remain
interrupted.  Terminal evidence is persisted before a work unit can pass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

from .capability_runtime import (
    AttemptLifecycleObserver,
    CapabilityAttemptResult,
    CapabilityRequest,
    CapabilityRuntime,
    InvocationVersions,
    persist_capability_attempt,
)
from .domain import (
    CoverageUnit,
    IdempotencyConflictError,
    NodeType,
    StaleCallbackError,
    StoreError,
    canonical_json,
    content_hash,
)


ASSIGNMENT_KIND = "capability_work_assignment"
ASSIGNMENT_SCHEMA = "mm-capability-work-assignment-r1"


@dataclass(frozen=True)
class CapabilityWorkAssignment:
    """Immutable pre-dispatch link between one request and one manifest unit."""

    attempt_id: str
    run_id: str
    manifest_revision: int
    work_unit_id: str
    node_id: str
    profile_fingerprint: str
    request_hash: str
    request: Mapping[str, Any]
    running_detail: str
    passed_detail: str
    failed_detail: str
    blocked_detail: str
    schema_version: str = ASSIGNMENT_SCHEMA

    @property
    def object_id(self) -> str:
        return "capability-work-assignment:%s" % self.attempt_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_id": self.attempt_id,
            "run_id": self.run_id,
            "manifest_revision": self.manifest_revision,
            "work_unit_id": self.work_unit_id,
            "node_id": self.node_id,
            "profile_fingerprint": self.profile_fingerprint,
            "request_hash": self.request_hash,
            "request": json.loads(canonical_json(self.request)),
            "running_detail": self.running_detail,
            "passed_detail": self.passed_detail,
            "failed_detail": self.failed_detail,
            "blocked_detail": self.blocked_detail,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "CapabilityWorkAssignment":
        if not isinstance(payload, Mapping):
            raise StoreError("capability work assignment must be an object")
        expected = {
            "schema_version", "attempt_id", "run_id", "manifest_revision",
            "work_unit_id", "node_id", "profile_fingerprint", "request_hash",
            "request", "running_detail", "passed_detail", "failed_detail",
            "blocked_detail",
        }
        if set(payload) != expected or payload.get("schema_version") != ASSIGNMENT_SCHEMA:
            raise StoreError("capability work assignment shape is invalid")
        request = payload.get("request")
        if not isinstance(request, Mapping):
            raise StoreError("capability work assignment request is invalid")
        strings = (
            "attempt_id", "run_id", "work_unit_id", "node_id",
            "profile_fingerprint", "request_hash", "running_detail",
            "passed_detail", "failed_detail", "blocked_detail",
        )
        if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in strings):
            raise StoreError("capability work assignment identity/text is invalid")
        revision = payload.get("manifest_revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise StoreError("capability work assignment revision is invalid")
        if content_hash(request) != payload["request_hash"]:
            raise StoreError("capability work assignment request hash mismatch")
        return cls(
            attempt_id=payload["attempt_id"],
            run_id=payload["run_id"],
            manifest_revision=revision,
            work_unit_id=payload["work_unit_id"],
            node_id=payload["node_id"],
            profile_fingerprint=payload["profile_fingerprint"],
            request_hash=payload["request_hash"],
            request=json.loads(canonical_json(request)),
            running_detail=payload["running_detail"],
            passed_detail=payload["passed_detail"],
            failed_detail=payload["failed_detail"],
            blocked_detail=payload["blocked_detail"],
        )


class CapabilityWorkUnitController(AttemptLifecycleObserver):
    """Bind attempts to manifest work units and close them idempotently."""

    def __init__(self, store: Any) -> None:
        required = (
            "get_run", "get_manifest", "get_work_unit_run",
            "get_capability_attempt", "bind_capability_attempt_to_work_unit",
            "complete_capability_work_unit", "put_domain_object",
            "get_domain_object", "list_domain_objects", "verify_audit_chain",
            "audit_trail",
        )
        if any(not hasattr(store, name) for name in required):
            raise TypeError("store does not expose the R1 controller contract")
        self.store = store

    @staticmethod
    def _request_for(
        runtime: CapabilityRuntime,
        *,
        attempt_id: str,
        monitoring_run_id: str,
        node_id: str,
        manifest_revision: int,
        versions: InvocationVersions,
        payload: Any,
        expected_units: Sequence[Union[CoverageUnit, Mapping[str, Any], str]],
        continued_from: str,
    ) -> CapabilityRequest:
        return CapabilityRequest.build(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            profile=runtime.profile,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=continued_from,
        )

    def _manifest_unit(self, request: CapabilityRequest, work_unit_id: str) -> Any:
        run = self.store.get_run(request.monitoring_run_id)
        if int(run.manifest_revision) != request.manifest_revision:
            raise StaleCallbackError("controller request does not use the current manifest")
        manifest = self.store.get_manifest(request.monitoring_run_id, request.manifest_revision)
        if manifest is None or not manifest.work_units:
            raise StoreError("controller requires an explicit work-unit manifest")
        units = {unit.work_unit_id: unit for unit in manifest.work_units}
        unit = units.get(work_unit_id)
        if unit is None:
            raise StoreError("controller work unit is not in the current manifest")
        nodes = {node.node_id: node for node in manifest.nodes}
        node = nodes.get(unit.node_id)
        if node is None or node.node_type != NodeType.AI_CANDIDATE:
            raise StoreError("controller may assign only AI analysis work units")
        if unit.node_id != request.node_id:
            raise StaleCallbackError("controller request node does not match the work unit")
        return unit

    def _assignment_for(
        self,
        request: CapabilityRequest,
        work_unit_id: str,
    ) -> CapabilityWorkAssignment:
        unit = self._manifest_unit(request, work_unit_id)
        label = " ".join(str(unit.label).split())
        if not label:
            raise StoreError("manifest work-unit label must be audience-readable")
        return CapabilityWorkAssignment(
            attempt_id=request.attempt_id,
            run_id=request.monitoring_run_id,
            manifest_revision=request.manifest_revision,
            work_unit_id=unit.work_unit_id,
            node_id=request.node_id,
            profile_fingerprint=request.profile_fingerprint,
            request_hash=request.request_hash,
            request=request.to_jsonrpc(),
            running_detail="正在%s" % label,
            passed_detail="已完成：%s" % label,
            failed_detail="未完成：%s" % label,
            blocked_detail="已暂停：%s" % label,
        )

    def register(
        self,
        request: CapabilityRequest,
        work_unit_id: str,
    ) -> CapabilityWorkAssignment:
        """Persist one immutable assignment before any transport can start."""

        assignment = self._assignment_for(request, work_unit_id)
        existing = self.store.get_domain_object(ASSIGNMENT_KIND, assignment.object_id)
        if existing is not None:
            stored = self._load(assignment.attempt_id)
            if stored.to_dict() != assignment.to_dict():
                raise IdempotencyConflictError(
                    "capability attempt is already assigned to a different frozen request"
                )
            return stored
        version = self.store.put_domain_object(
            ASSIGNMENT_KIND,
            assignment.object_id,
            assignment.to_dict(),
            run_id=assignment.run_id,
            idempotency_key="controller-assignment:%s:%s" % (
                assignment.attempt_id,
                assignment.request_hash,
            ),
        )
        stored_row = self.store.get_domain_object(
            ASSIGNMENT_KIND,
            assignment.object_id,
            version=int(version),
        )
        if stored_row is None or int(version) != 1:
            raise StoreError("capability work assignment was not durably sealed")
        stored = CapabilityWorkAssignment.from_dict(stored_row[1])
        if stored.to_dict() != assignment.to_dict():
            raise StoreError("capability work assignment changed during registration")
        return stored

    def _load(self, attempt_id: str) -> CapabilityWorkAssignment:
        object_id = "capability-work-assignment:%s" % attempt_id
        row = self.store.get_domain_object(ASSIGNMENT_KIND, object_id)
        if row is None:
            raise StoreError("capability attempt has no pre-registered work assignment")
        version, payload = row
        if version != 1:
            raise StoreError("capability work assignment must remain immutable")
        assignment = CapabilityWorkAssignment.from_dict(payload)
        if assignment.attempt_id != attempt_id:
            raise StoreError("capability work assignment identity mismatch")
        audit_ok, first_bad_seq, _ = self.store.verify_audit_chain()
        if not audit_ok:
            raise StoreError(
                "capability work assignment audit chain is invalid at sequence %s"
                % first_bad_seq
            )
        matching = [
            event for event in self.store.audit_trail()
            if event.event_type == "domain_object_put"
            and event.payload.get("kind") == ASSIGNMENT_KIND
            and event.payload.get("object_id") == object_id
            and int(event.payload.get("version", 0)) == version
        ]
        if len(matching) != 1 \
                or matching[0].payload.get("run_id") != assignment.run_id \
                or matching[0].payload.get("content_hash") != content_hash(payload):
            raise StoreError("capability work assignment audit evidence is invalid")
        return assignment

    @staticmethod
    def _validate_request(
        assignment: CapabilityWorkAssignment,
        request: CapabilityRequest,
    ) -> None:
        if (
            request.attempt_id != assignment.attempt_id
            or request.monitoring_run_id != assignment.run_id
            or request.manifest_revision != assignment.manifest_revision
            or request.node_id != assignment.node_id
            or request.profile_fingerprint != assignment.profile_fingerprint
            or request.request_hash != assignment.request_hash
            or request.to_jsonrpc() != assignment.request
        ):
            raise IdempotencyConflictError(
                "runtime request does not match its frozen work assignment"
            )

    def on_attempt_prepared(
        self,
        request: CapabilityRequest,
        *,
        replaying: bool,
    ) -> None:
        assignment = self._load(request.attempt_id)
        self._validate_request(assignment, request)
        self.store.bind_capability_attempt_to_work_unit(
            assignment.run_id,
            assignment.work_unit_id,
            assignment.attempt_id,
            assignment.running_detail,
            manifest_revision=assignment.manifest_revision,
        )

    @staticmethod
    def _evidence_count(result: CapabilityAttemptResult, receipt: Any) -> int:
        count = 2 + len(receipt.work_event_versions) + len(receipt.adapter.domain_versions)
        if receipt.adapter.artifact_id:
            count += 1
        if result.adapter_run.raw_output is None:
            # Terminal progress must never imply evidence that was not sealed.
            return 0
        return count

    def on_attempt_terminal(self, result: CapabilityAttemptResult) -> None:
        assignment = self._load(result.request.attempt_id)
        self._validate_request(assignment, result.request)
        # A replay may arrive after registration but before the prior process
        # bound the work unit.  Binding is idempotent and must precede closure.
        self.on_attempt_prepared(result.request, replaying=True)
        receipt = persist_capability_attempt(self.store, result)
        detail = (
            assignment.passed_detail
            if result.status.value == "complete"
            else assignment.failed_detail
        )
        self.store.complete_capability_work_unit(
            assignment.run_id,
            assignment.work_unit_id,
            assignment.attempt_id,
            detail,
            evidence_count=self._evidence_count(result, receipt),
            manifest_revision=assignment.manifest_revision,
        )

    def on_attempt_interrupted(
        self,
        request: CapabilityRequest,
        *,
        reason: str,
    ) -> None:
        assignment = self._load(request.attempt_id)
        self._validate_request(assignment, request)
        attempt = self.store.get_capability_attempt(request.attempt_id)
        if attempt is None or attempt.get("terminal"):
            return
        if attempt.get("status") != "interrupted":
            raise StoreError("non-terminal capability attempt is not interrupted")
        self.on_attempt_prepared(request, replaying=True)
        self.store.complete_capability_work_unit(
            assignment.run_id,
            assignment.work_unit_id,
            assignment.attempt_id,
            assignment.blocked_detail,
            evidence_count=0,
            manifest_revision=assignment.manifest_revision,
        )

    def execute(
        self,
        runtime: CapabilityRuntime,
        *,
        work_unit_id: str,
        attempt_id: str,
        monitoring_run_id: str,
        node_id: str,
        manifest_revision: int,
        versions: InvocationVersions,
        payload: Any,
        expected_units: Sequence[Union[CoverageUnit, Mapping[str, Any], str]],
        continued_from: str = "",
    ) -> CapabilityAttemptResult:
        """Pre-register, execute, persist and close one manifest work unit."""

        if getattr(runtime, "_attempt_journal", None) is None:
            raise ValueError("controller execution requires the durable attempt journal")
        request = self._request_for(
            runtime,
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=continued_from,
        )
        self.register(request, work_unit_id)
        return runtime.invoke(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=continued_from,
            lifecycle_observer=self,
        )

    def _invoke_assignment(
        self,
        runtime: CapabilityRuntime,
        assignment: CapabilityWorkAssignment,
    ) -> CapabilityAttemptResult:
        if runtime.profile.fingerprint != assignment.profile_fingerprint:
            raise IdempotencyConflictError(
                "recovery runtime does not match the frozen execution profile"
            )
        rpc = assignment.request
        params = rpc.get("params")
        if rpc.get("id") != assignment.attempt_id or not isinstance(params, Mapping):
            raise StoreError("frozen controller request envelope is invalid")
        versions = InvocationVersions(**dict(params.get("versions", {})))
        request = self._request_for(
            runtime,
            attempt_id=assignment.attempt_id,
            monitoring_run_id=assignment.run_id,
            node_id=assignment.node_id,
            manifest_revision=assignment.manifest_revision,
            versions=versions,
            payload=params.get("input"),
            expected_units=tuple(params.get("expected_coverage", ())),
            continued_from=str(params.get("continued_from") or ""),
        )
        self._validate_request(assignment, request)
        return runtime.invoke(
            attempt_id=request.attempt_id,
            monitoring_run_id=request.monitoring_run_id,
            node_id=request.node_id,
            manifest_revision=request.manifest_revision,
            versions=request.versions,
            payload=request.payload,
            expected_units=request.expected_units,
            continued_from=request.continued_from,
            lifecycle_observer=self,
        )

    def resume(
        self,
        runtime: CapabilityRuntime,
        previous_attempt_id: str,
        *,
        attempt_id: str,
        manifest_revision: int,
    ) -> CapabilityAttemptResult:
        """Pre-register and run an exact continuation on the same work unit."""

        if getattr(runtime, "_attempt_journal", None) is None:
            raise ValueError("controller continuation requires the durable attempt journal")
        previous_assignment = self._load(previous_attempt_id)
        previous = self.store.get_capability_attempt(previous_attempt_id)
        if previous is None:
            raise StoreError("previous capability attempt is missing")
        if previous.get("profile_fingerprint") != runtime.profile.fingerprint:
            raise IdempotencyConflictError(
                "continuation runtime does not match the frozen execution profile"
            )
        if previous.get("status") not in {
            "timeout", "partial", "truncated", "interrupted",
        }:
            raise StoreError("previous capability attempt is not continuable")
        rpc = previous.get("request")
        params = rpc.get("params") if isinstance(rpc, Mapping) else None
        if not isinstance(params, Mapping):
            raise StoreError("previous capability request envelope is invalid")
        request = self._request_for(
            runtime,
            attempt_id=attempt_id,
            monitoring_run_id=previous_assignment.run_id,
            node_id=previous_assignment.node_id,
            manifest_revision=manifest_revision,
            versions=InvocationVersions(**dict(params.get("versions", {}))),
            payload=params.get("input"),
            expected_units=tuple(params.get("expected_coverage", ())),
            continued_from=previous_attempt_id,
        )
        if request.input_hash != previous.get("input_hash"):
            raise IdempotencyConflictError(
                "continuation changed the frozen input/version/profile identity"
            )
        self.register(request, previous_assignment.work_unit_id)
        return runtime.resume(
            previous_attempt_id,
            attempt_id=attempt_id,
            manifest_revision=manifest_revision,
            lifecycle_observer=self,
        )

    def reconcile(
        self,
        runtime: CapabilityRuntime,
        attempt_id: str,
    ) -> Optional[CapabilityAttemptResult]:
        """Idempotently recover one pre-registered assignment after restart."""

        assignment = self._load(attempt_id)
        if runtime.profile.fingerprint != assignment.profile_fingerprint:
            raise IdempotencyConflictError(
                "recovery runtime does not match the frozen execution profile"
            )
        attempt = self.store.get_capability_attempt(attempt_id)
        if attempt is not None and attempt.get("status") == "interrupted" \
                and not attempt.get("terminal"):
            rpc = assignment.request
            params = rpc.get("params")
            if not isinstance(params, Mapping):
                raise StoreError("frozen controller request envelope is invalid")
            request = self._request_for(
                runtime,
                attempt_id=assignment.attempt_id,
                monitoring_run_id=assignment.run_id,
                node_id=assignment.node_id,
                manifest_revision=assignment.manifest_revision,
                versions=InvocationVersions(**dict(params.get("versions", {}))),
                payload=params.get("input"),
                expected_units=tuple(params.get("expected_coverage", ())),
                continued_from=str(params.get("continued_from") or ""),
            )
            self._validate_request(assignment, request)
            self.on_attempt_interrupted(request, reason="reconciled after interruption")
            return None
        return self._invoke_assignment(runtime, assignment)

    def registered_attempts(self) -> Tuple[str, ...]:
        """Return verified assignment ids for process-start reconciliation."""

        attempts = []
        for object_id, _ in self.store.list_domain_objects(ASSIGNMENT_KIND):
            prefix = "capability-work-assignment:"
            if not object_id.startswith(prefix):
                raise StoreError("capability work assignment object id is invalid")
            assignment = self._load(object_id[len(prefix):])
            attempts.append(assignment.attempt_id)
        return tuple(attempts)


__all__ = [
    "ASSIGNMENT_KIND",
    "ASSIGNMENT_SCHEMA",
    "CapabilityWorkAssignment",
    "CapabilityWorkUnitController",
]
