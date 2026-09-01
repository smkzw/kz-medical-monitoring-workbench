"""Capability work-unit completion and progress projections."""

from __future__ import annotations

from .store_common import *
from .store_common import (
    _runtime_schema_shape,
    _shape_from_ddl,
    _ANALYSIS_TRANSITIONS,
    _REVIEW_TRANSITIONS,
    _OUTPUT_ORDER,
    _WORK_UNIT_IDENTITY_KEYS,
    _IMMUTABLE_DOMAIN_OBJECT_KINDS,
    _CAPABILITY_ASSIGNMENT_KIND,
    _CAPABILITY_ASSIGNMENT_SCHEMA,
    _RESERVED_INTERNAL_AUDIT_EVENTS,
    _IdempotencyLedgerConflict,
    _RuntimeAttemptJournal,
    _SCHEMA,
    _build_current_runtime_schema_shape,
    _CURRENT_RUNTIME_SCHEMA_SHAPE,
    _assert_current_schema,
)

class StoreWorkUnitMixin:
    """Complete work units and project immutable progress feeds."""
    def bind_capability_attempt_to_work_unit(
        self,
        run_id: str,
        work_unit_id: str,
        attempt_id: str,
        detail: str,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Start or continue an AI work unit from one journaled attempt.

        The caller supplies only the durable attempt id and an audience-readable
        progress sentence. Provider/model/profile identity is re-derived from
        the immutable request journal. A later attempt may replace the current
        identity only through an exact ``continued_from`` chain.
        """

        if not attempt_id:
            raise StoreError("capability attempt_id is required")
        detail = self._normalize_work_unit_detail(detail)
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision
        stable_key = f"capability-work-unit:{run_id}:{revision}:{work_unit_id}"

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            # Re-resolve inside BEGIN IMMEDIATE so a manifest change or direct
            # journal corruption cannot slip between validation and binding.
            current_manifest, current_unit = self._current_work_unit_manifest(
                run_id, work_unit_id, revision
            )
            attempt, identity = self._capability_work_unit_identity(
                current_manifest, current_unit, attempt_id
            )
            if attempt["status"] == "declared":
                raise StoreError(
                    "capability attempt must be claimed before work-unit binding"
                )
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            bindings = self._list_work_unit_capability_attempts(
                run_id, revision, work_unit_id
            )
            existing_binding = next(
                (item for item in bindings if item["attempt_id"] == attempt_id), None
            )
            if existing_binding is not None:
                if existing_binding["detail"] != detail:
                    raise IdempotencyConflictError(
                        "capability attempt binding replay changed its progress detail"
                    )
                if bindings[-1]["attempt_id"] != attempt_id:
                    raise StaleCallbackError(
                        "an older capability attempt cannot replace the latest binding"
                    )
                return current
            used_elsewhere = self._conn.execute(
                "SELECT run_id, manifest_revision, work_unit_id"
                " FROM work_unit_capability_attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if used_elsewhere is not None:
                raise IdempotencyConflictError(
                    "capability attempt is already bound to another work unit"
                )
            if not bindings:
                if current.status in TERMINAL_NODE_STATUSES:
                    raise StaleCallbackError(
                        "terminal work unit cannot accept a first capability binding"
                    )
                if attempt["continued_from"]:
                    raise StaleCallbackError(
                        "a continuation attempt cannot be the first work-unit binding"
                    )
                dependency_states: Dict[str, str] = {}
                for dependency in current_unit.depends_on:
                    row = self._conn.execute(
                        "SELECT status FROM work_unit_runs WHERE run_id=?"
                        " AND manifest_revision=? AND work_unit_id=?",
                        (run_id, revision, dependency),
                    ).fetchone()
                    if row is None:
                        raise StoreError(
                            f"dependency work unit row is missing: {dependency}"
                        )
                    dependency_states[dependency] = row[0]
                unsatisfied = {
                    key: value for key, value in dependency_states.items()
                    if NodeStatus(value) not in domain.DEPENDENCY_SATISFYING_STATUSES
                }
                if unsatisfied:
                    raise StoreError(
                        f"work unit dependencies are not satisfied: {unsatisfied}"
                    )
                if current.status != NodeStatus.PENDING:
                    raise StoreError(
                        "AI work unit has running state without a capability binding"
                    )
                ordinal = 1
                started = now_iso()
                begin_hash = content_hash({
                    "detail": detail, "execution_identity": identity,
                })
                self._conn.execute(
                    "INSERT INTO work_unit_capability_attempts("
                    " run_id, manifest_revision, work_unit_id, attempt_ordinal, attempt_id,"
                    " detail, execution_identity_json, identity_hash, bound_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        run_id, revision, work_unit_id, ordinal, attempt_id, detail,
                        canonical_json(identity), content_hash(identity), started,
                    ),
                )
                self._conn.execute(
                    "UPDATE work_unit_runs SET status=?, idempotency_key=?, begin_hash=?,"
                    " detail=?, execution_identity_json=?, started_at=?, finished_at=NULL,"
                    " updated_at=? WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                    (
                        NodeStatus.RUNNING.value, stable_key, begin_hash, detail,
                        canonical_json(identity), started, started,
                        run_id, revision, work_unit_id,
                    ),
                )
                self._append_audit_row(
                    self._conn, domain.EVENT_WORK_UNIT_BEGIN,
                    {
                        "run_id": run_id, "manifest_revision": revision,
                        "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                        "label": current_unit.label, "stage": current_unit.stage,
                        "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                        "status": NodeStatus.RUNNING.value, "detail": detail,
                        "execution_identity": identity, "evidence_count": 0,
                    },
                    run_id,
                )
                return self.get_work_unit_run(run_id, revision, work_unit_id)

            if current.status not in {
                NodeStatus.RUNNING, NodeStatus.FAILED, NodeStatus.BLOCKED,
            }:
                raise StoreError(
                    "capability retry requires a running, failed or blocked work unit"
                )
            previous_binding = bindings[-1]
            previous = self.get_capability_attempt(previous_binding["attempt_id"])
            if previous is None:  # pragma: no cover - FK plus prior validation
                raise StoreError("previous capability attempt is missing")
            self._validate_capability_result_envelope(previous)
            retryable_statuses = frozenset({
                "interrupted", "failed", "timeout", "cancelled", "partial", "truncated",
            })
            if previous["status"] not in retryable_statuses:
                raise StoreError(
                    "latest capability attempt is not in a retryable terminal/interrupted state"
                )
            if attempt["continued_from"] != previous["attempt_id"]:
                raise StaleCallbackError(
                    "capability continuation does not reference the latest bound attempt"
                )
            ordinal = len(bindings) + 1
            bound_at = now_iso()
            self._conn.execute(
                "INSERT INTO work_unit_capability_attempts("
                " run_id, manifest_revision, work_unit_id, attempt_ordinal, attempt_id,"
                " detail, execution_identity_json, identity_hash, bound_at)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    run_id, revision, work_unit_id, ordinal, attempt_id, detail,
                    canonical_json(identity), content_hash(identity), bound_at,
                ),
            )
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=0, completion_hash='', finished_at=NULL, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (
                    NodeStatus.RUNNING.value, detail, canonical_json(identity), bound_at,
                    run_id, revision, work_unit_id,
                ),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_ATTEMPT_BOUND,
                {
                    "run_id": run_id, "manifest_revision": revision,
                    "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                    "label": current_unit.label, "stage": current_unit.stage,
                    "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                    "status": NodeStatus.RUNNING.value, "detail": detail,
                    "execution_identity": identity, "evidence_count": 0,
                    "attempt_ordinal": ordinal,
                    "continued_from": previous["attempt_id"],
                },
                run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def complete_work_unit(
        self, run_id: str, work_unit_id: str, idempotency_key: str,
        status: NodeStatus, detail: str, evidence_count: int = 0,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Complete a non-AI work unit through the direct deterministic path."""

        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        if self._manifest_node_type(manifest, unit.node_id) == NodeType.AI_CANDIDATE:
            raise StoreError(
                "AI work units must complete through complete_capability_work_unit"
            )
        return self._complete_work_unit_direct(
            run_id, work_unit_id, idempotency_key, status, detail,
            evidence_count, execution_identity, manifest_revision,
        )

    def _complete_work_unit_direct(
        self, run_id: str, work_unit_id: str, idempotency_key: str,
        status: NodeStatus, detail: str, evidence_count: int = 0,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Commit one immutable terminal work-unit outcome in the current revision."""
        if status not in TERMINAL_NODE_STATUSES:
            raise StoreError(f"work unit completion requires terminal status: {status.value}")
        if not idempotency_key:
            raise StoreError("work unit idempotency key is required")
        if isinstance(evidence_count, bool) or not isinstance(evidence_count, int) \
                or evidence_count < 0:
            raise StoreError("work unit evidence_count must be a non-negative integer")
        detail = self._normalize_work_unit_detail(detail)
        supplied_identity = (
            self._normalize_work_unit_identity(execution_identity)
            if execution_identity is not None else None
        )
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            identity = (
                current.execution_identity if supplied_identity is None else supplied_identity
            )
            if (supplied_identity is not None and current.execution_identity
                    and supplied_identity != current.execution_identity):
                raise IdempotencyConflictError(
                    f"work unit {work_unit_id!r} execution identity cannot change at completion"
                )
            fingerprint = content_hash({
                "status": status.value, "detail": detail,
                "execution_identity": identity, "evidence_count": evidence_count,
            })
            if current.status in TERMINAL_NODE_STATUSES:
                if (current.idempotency_key == idempotency_key
                        and current.completion_hash == fingerprint):
                    return current
                raise IdempotencyConflictError(
                    f"terminal work unit {work_unit_id!r} received a conflicting replay"
                )
            if current.status != NodeStatus.RUNNING:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} was not started before completion"
                )
            if current.idempotency_key != idempotency_key:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} completion key is stale"
                )
            finished = now_iso()
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=?, completion_hash=?, finished_at=?, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (status.value, detail, canonical_json(identity), evidence_count,
                 fingerprint, finished, finished, run_id, revision, work_unit_id),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_COMPLETE,
                {"run_id": run_id, "manifest_revision": revision,
                 "work_unit_id": work_unit_id, "node_id": unit.node_id,
                 "label": unit.label, "stage": unit.stage, "scope": unit.scope,
                 "target_ref": unit.target_ref, "status": status.value,
                 "detail": detail, "execution_identity": identity,
                 "evidence_count": evidence_count}, run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def _capability_persistence_evidence_count(
        self,
        attempt: Mapping[str, Any],
    ) -> int:
        """Verify the complete Store footprint produced by capability persistence.

        A terminal journal row proves execution, not persistence.  Audience
        progress may therefore close only after every object written by
        ``persist_capability_attempt`` is present, hash-verified and bound to
        the same frozen attempt.  No caller-supplied receipt or count is
        trusted.
        """

        if not attempt.get("terminal") or not isinstance(attempt.get("result"), Mapping):
            raise StoreError("terminal capability attempt has no persisted result envelope")
        result = attempt["result"]
        adapter_run = result.get("adapter_run")
        events = result.get("work_events")
        if not isinstance(adapter_run, Mapping) or not isinstance(events, list):
            raise StoreError("capability persistence result envelope is invalid")
        binding = adapter_run.get("binding")
        analysis = adapter_run.get("analysis")
        raw = adapter_run.get("raw_output")
        if not isinstance(binding, Mapping) \
                or not isinstance(analysis, Mapping) \
                or not isinstance(raw, Mapping):
            raise StoreError(
                "terminal capability attempt has no complete persisted evidence envelope"
            )

        def require_domain(kind: str, object_id: str, expected: Any) -> None:
            row = self.get_domain_object(kind, object_id, version=1)
            if row is None or row[1] != to_jsonable(expected):
                raise StoreError(
                    "capability attempt evidence is not fully persisted: %s" % kind
                )

        raw_ref = raw.get("raw_output_ref")
        if not isinstance(raw_ref, str) or not raw_ref:
            raise StoreError("terminal capability attempt raw evidence reference is invalid")
        require_domain("adapter_raw_output", "adapter-raw:%s" % raw_ref, raw)
        if not self.verify_adapter_raw_output(raw_ref):
            raise StoreError("terminal capability attempt raw evidence failed verification")

        params = attempt["request"].get("params")
        if not isinstance(params, Mapping):
            raise StoreError("capability attempt request params are invalid")
        binding_id = binding.get("binding_id")
        input_hash = binding.get("input_hash")
        if binding_id != params.get("binding", {}).get("binding_id") \
                or input_hash != attempt["input_hash"]:
            raise StoreError("persisted capability binding identity is invalid")
        require_domain(
            "adapter_binding",
            "adapter-binding:%s:%s" % (binding_id, input_hash or "unbound"),
            binding,
        )

        analysis_id = analysis.get("analysis_id")
        if not isinstance(analysis_id, str) or not analysis_id:
            raise StoreError("persisted capability analysis identity is invalid")
        require_domain(
            "adapter_analysis", "adapter-analysis:%s" % analysis_id, analysis
        )

        candidate = adapter_run.get("candidate_artifact")
        artifact_id = None
        artifact_count = 0
        if candidate is not None:
            if not isinstance(candidate, Mapping):
                raise StoreError("capability candidate artifact envelope is invalid")
            try:
                envelope = from_jsonable(ArtifactEnvelope, candidate)
                artifact_id = envelope.canonical_hash()
                committed = self.get_artifact(artifact_id)
            except (StoreError, TypeError, ValueError) as exc:
                raise StoreError(
                    "capability candidate artifact is not fully persisted"
                ) from exc
            if committed.content_dict() != envelope.content_dict() \
                    or committed.run_id != attempt["run_id"] \
                    or committed.node_id != attempt["node_id"] \
                    or committed.node_type != NodeType.AI_CANDIDATE \
                    or committed.payload_role != domain.PAYLOAD_ROLE_CANDIDATE \
                    or raw_ref not in committed.evidence_refs \
                    or not self.verify_artifact(artifact_id):
                raise StoreError("persisted capability candidate artifact is invalid")
            artifact_count = 1

        expected_run_snapshot = {
            "adapter_run_id": attempt["attempt_id"],
            "monitoring_run_id": adapter_run.get("monitoring_run_id", ""),
            "node_id": adapter_run.get("node_id", ""),
            "status": adapter_run.get("status"),
            "binding_id": binding_id,
            "input_hash": input_hash,
            "analysis_id": analysis_id,
            "raw_output_ref": raw_ref,
            "candidate_artifact_id": artifact_id,
            "failure_reason": adapter_run.get("failure_reason"),
            "independent": adapter_run.get("independent", True),
            "continued_from": adapter_run.get("continued_from"),
            "created_at": adapter_run.get("created_at", ""),
            "finished_at": adapter_run.get("finished_at", ""),
        }
        if expected_run_snapshot["monitoring_run_id"] != attempt["run_id"] \
                or expected_run_snapshot["node_id"] != attempt["node_id"] \
                or expected_run_snapshot["status"] != attempt["status"]:
            raise StoreError("persisted capability run snapshot identity is invalid")
        require_domain(
            "adapter_run", "adapter-run:%s" % attempt["attempt_id"],
            expected_run_snapshot,
        )

        profile_row = self.get_domain_object(
            "execution_profile",
            "execution-profile:%s" % attempt["profile_fingerprint"],
            version=1,
        )
        if profile_row is None \
                or content_hash(profile_row[1]) != attempt["profile_fingerprint"]:
            raise StoreError("capability execution profile is not fully persisted")
        expected_request = {
            "attempt_id": attempt["attempt_id"],
            "monitoring_run_id": attempt["run_id"],
            "node_id": attempt["node_id"],
            "manifest_revision": attempt["manifest_revision"],
            "profile_fingerprint": attempt["profile_fingerprint"],
            "binding_id": binding_id,
            "input_hash": attempt["input_hash"],
            "versions": params.get("versions", {}),
            "expected_units": params.get("expected_coverage", []),
            "continued_from": attempt.get("continued_from", ""),
            "request_hash": attempt["request_hash"],
        }
        require_domain(
            "adapter_attempt_request",
            "adapter-attempt-request:%s" % attempt["attempt_id"],
            expected_request,
        )
        for index, event in enumerate(events, start=1):
            if not isinstance(event, Mapping) \
                    or event.get("attempt_id") != attempt["attempt_id"] \
                    or event.get("sequence") != index:
                raise StoreError("capability work-event evidence is invalid")
            require_domain(
                "adapter_work_event",
                "adapter-work-event:%s:%03d" % (attempt["attempt_id"], index),
                event,
            )
        # profile + request, four adapter domain objects, work events, optional artifact
        return 2 + 4 + len(events) + artifact_count

    def complete_capability_work_unit(
        self,
        run_id: str,
        work_unit_id: str,
        attempt_id: str,
        detail: str,
        evidence_count: Optional[int] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Finish an AI work unit from the latest bound durable attempt.

        Capability ``complete`` is the only success path. Interrupted attempts
        become blocked; failed/timeout/cancelled/partial/truncated attempts
        become failed. Callers cannot supply or upgrade the status.
        """

        if not attempt_id:
            raise StoreError("capability attempt_id is required")
        if evidence_count is not None and (
            isinstance(evidence_count, bool)
            or not isinstance(evidence_count, int)
            or evidence_count < 0
        ):
            raise StoreError("work unit evidence_count must be a non-negative integer")
        detail = self._normalize_work_unit_detail(detail)
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision
        stable_key = f"capability-work-unit:{run_id}:{revision}:{work_unit_id}"

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            current_manifest, current_unit = self._current_work_unit_manifest(
                run_id, work_unit_id, revision
            )
            attempt, identity = self._capability_work_unit_identity(
                current_manifest, current_unit, attempt_id
            )
            bindings = self._list_work_unit_capability_attempts(
                run_id, revision, work_unit_id
            )
            if not bindings or bindings[-1]["attempt_id"] != attempt_id:
                raise StaleCallbackError(
                    "only the latest bound capability attempt may finish the work unit"
                )
            if attempt["status"] == "complete" and attempt["terminal"]:
                status = NodeStatus.PASSED
            elif attempt["status"] == "interrupted" and not attempt["terminal"]:
                status = NodeStatus.BLOCKED
            elif attempt["terminal"] and attempt["status"] in {
                "failed", "timeout", "cancelled", "partial", "truncated",
            }:
                status = NodeStatus.FAILED
            else:
                raise StoreError(
                    "capability attempt must be terminal or interrupted before work-unit completion"
                )
            if attempt["terminal"]:
                persisted_evidence_count = self._capability_persistence_evidence_count(
                    attempt
                )
                if evidence_count is not None \
                        and evidence_count != persisted_evidence_count:
                    raise StoreError(
                        "work unit evidence_count does not match persisted capability evidence"
                    )
                resolved_evidence_count = persisted_evidence_count
            else:
                if evidence_count not in (None, 0):
                    raise StoreError(
                        "interrupted capability attempt cannot claim persisted terminal evidence"
                    )
                resolved_evidence_count = 0
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            fingerprint = content_hash({
                "status": status.value,
                "detail": detail,
                "execution_identity": identity,
                "evidence_count": resolved_evidence_count,
            })
            if current.status in TERMINAL_NODE_STATUSES:
                if current.idempotency_key == stable_key \
                        and current.completion_hash == fingerprint:
                    return current
                raise IdempotencyConflictError(
                    f"terminal work unit {work_unit_id!r} received a conflicting replay"
                )
            if current.status != NodeStatus.RUNNING:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} was not started before completion"
                )
            if current.idempotency_key != stable_key \
                    or current.execution_identity != identity:
                raise StaleCallbackError(
                    "work unit current identity does not match the latest capability binding"
                )
            finished = now_iso()
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=?, completion_hash=?, finished_at=?, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (
                    status.value, detail, canonical_json(identity),
                    resolved_evidence_count,
                    fingerprint, finished, finished, run_id, revision, work_unit_id,
                ),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_COMPLETE,
                {
                    "run_id": run_id, "manifest_revision": revision,
                    "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                    "label": current_unit.label, "stage": current_unit.stage,
                    "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                    "status": status.value, "detail": detail,
                    "execution_identity": identity,
                    "evidence_count": resolved_evidence_count,
                },
                run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def _validated_work_unit_feed_payload(
        self, event_type: str, payload: Mapping[str, Any], manifest: ExecutionManifest,
        unit_by_id: Mapping[str, ManifestWorkUnit],
    ) -> Dict[str, Any]:
        expected_keys = {
            "run_id", "manifest_revision", "work_unit_id", "node_id", "label",
            "stage", "scope", "target_ref", "status", "detail",
            "execution_identity", "evidence_count",
        }
        if event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
            expected_keys = expected_keys | {"attempt_ordinal", "continued_from"}
        if set(payload) != expected_keys:
            raise StoreError("work-unit audit payload shape is invalid")
        if payload.get("run_id") != manifest.run_id \
                or payload.get("manifest_revision") != manifest.revision:
            raise StoreError("work-unit audit payload manifest identity is invalid")
        work_unit_id = payload.get("work_unit_id")
        unit = unit_by_id.get(str(work_unit_id))
        if unit is None:
            raise StoreError("work-unit audit payload references an unknown unit")
        expected_identity = {
            "node_id": unit.node_id,
            "label": unit.label,
            "stage": unit.stage,
            "scope": unit.scope,
            "target_ref": unit.target_ref,
        }
        if any(payload.get(key) != value for key, value in expected_identity.items()):
            raise StoreError("work-unit audit payload definition does not match manifest")
        detail = self._normalize_work_unit_detail(str(payload.get("detail", "")))
        if detail != payload.get("detail"):
            raise StoreError("work-unit audit detail is not normalized")
        execution_identity = payload.get("execution_identity")
        if not isinstance(execution_identity, Mapping) \
                or self._normalize_work_unit_identity(execution_identity) != execution_identity:
            raise StoreError("work-unit audit execution identity is invalid")
        evidence_count = payload.get("evidence_count")
        if isinstance(evidence_count, bool) or not isinstance(evidence_count, int) \
                or evidence_count < 0:
            raise StoreError("work-unit audit evidence count is invalid")
        try:
            status = NodeStatus(str(payload.get("status")))
        except ValueError as exc:
            raise StoreError("work-unit audit status is invalid") from exc
        if event_type == domain.EVENT_WORK_UNIT_BEGIN:
            if status != NodeStatus.RUNNING or evidence_count != 0:
                raise StoreError("work-unit begin audit state is invalid")
        elif event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
            attempt_ordinal = payload.get("attempt_ordinal")
            if status != NodeStatus.RUNNING or evidence_count != 0 \
                    or isinstance(attempt_ordinal, bool) \
                    or not isinstance(attempt_ordinal, int) \
                    or attempt_ordinal < 2 \
                    or not isinstance(payload.get("continued_from"), str) \
                    or not payload.get("continued_from"):
                raise StoreError("work-unit attempt binding audit state is invalid")
        elif event_type == domain.EVENT_WORK_UNIT_COMPLETE:
            if status not in TERMINAL_NODE_STATUSES:
                raise StoreError("work-unit completion audit state is invalid")
        else:  # pragma: no cover - caller query fixes the event types
            raise StoreError("unexpected work-unit audit event type")
        return dict(payload)

    def _validated_work_unit_projection(
        self, manifest: ExecutionManifest,
    ) -> Tuple[List[WorkUnitRun], List[Dict[str, Any]]]:
        """Cross-check manifest, ledger and immutable transition events.

        SQLite rows carry the efficient current state, while the hash-chained
        begin/complete events prove how that state was reached.  A projection
        is authoritative only when all three representations agree exactly.
        """

        try:
            rows = self.list_work_unit_runs(manifest.run_id, manifest.revision)
        except ValueError as exc:
            raise StoreError(
                "authoritative work unit ledger contains an invalid status"
            ) from exc
        unit_by_id = {unit.work_unit_id: unit for unit in manifest.work_units}
        row_by_id = {row.work_unit_id: row for row in rows}
        if len(rows) != manifest.total_units() or set(row_by_id) != set(unit_by_id):
            raise StoreError(
                "authoritative work unit ledger does not match the manifest denominator"
            )
        for work_unit_id, row in row_by_id.items():
            if row.node_id != unit_by_id[work_unit_id].node_id:
                raise StoreError(
                    "authoritative work unit ledger definition does not match the manifest"
                )

        audit_ok, first_bad_seq, _ = self.verify_audit_chain()
        if not audit_ok:
            raise StoreError(f"audit chain is invalid at sequence {first_bad_seq}")
        event_rows = self._conn.execute(
            "SELECT seq, event_type, payload_json, created_at FROM audit_events"
            " WHERE run_id=? AND event_type IN (?,?,?) ORDER BY seq",
            (manifest.run_id, domain.EVENT_WORK_UNIT_BEGIN,
             domain.EVENT_WORK_UNIT_ATTEMPT_BOUND,
             domain.EVENT_WORK_UNIT_COMPLETE),
        ).fetchall()
        derived_status = {
            work_unit_id: NodeStatus.PENDING for work_unit_id in unit_by_id
        }
        begin_payloads: Dict[str, Dict[str, Any]] = {}
        latest_running_payloads: Dict[str, Dict[str, Any]] = {}
        attempt_binding_payloads: Dict[str, List[Dict[str, Any]]] = {
            work_unit_id: [] for work_unit_id in unit_by_id
        }
        completion_payloads: Dict[str, Dict[str, Any]] = {}
        validated_events: List[Dict[str, Any]] = []
        for seq, event_type, payload_json, created_at in event_rows:
            payload = json.loads(payload_json)
            if int(payload.get("manifest_revision", -1)) != manifest.revision:
                continue
            validated = self._validated_work_unit_feed_payload(
                event_type, payload, manifest, unit_by_id
            )
            work_unit_id = str(validated["work_unit_id"])
            if event_type == domain.EVENT_WORK_UNIT_BEGIN:
                if derived_status[work_unit_id] != NodeStatus.PENDING:
                    raise StoreError("work-unit audit transition sequence is invalid")
                derived_status[work_unit_id] = NodeStatus.RUNNING
                begin_payloads[work_unit_id] = validated
                latest_running_payloads[work_unit_id] = validated
                if validated["execution_identity"].get("attempt_id"):
                    attempt_binding_payloads[work_unit_id].append(validated)
            elif event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
                if derived_status[work_unit_id] not in {
                    NodeStatus.RUNNING, NodeStatus.FAILED, NodeStatus.BLOCKED,
                }:
                    raise StoreError("work-unit retry binding sequence is invalid")
                derived_status[work_unit_id] = NodeStatus.RUNNING
                latest_running_payloads[work_unit_id] = validated
                attempt_binding_payloads[work_unit_id].append(validated)
                completion_payloads.pop(work_unit_id, None)
            else:
                if derived_status[work_unit_id] != NodeStatus.RUNNING:
                    raise StoreError("work-unit audit transition sequence is invalid")
                derived_status[work_unit_id] = NodeStatus(str(validated["status"]))
                completion_payloads[work_unit_id] = validated
            validated_events.append({
                **validated,
                "sequence": int(seq),
                "event_type": event_type,
                "created_at": created_at,
            })

        for work_unit_id, row in row_by_id.items():
            if row.status != derived_status[work_unit_id]:
                raise StoreError(
                    "authoritative work unit ledger status does not match its audit history"
                )
            unit = unit_by_id[work_unit_id]
            is_ai = self._manifest_node_type(manifest, unit.node_id) == NodeType.AI_CANDIDATE
            bindings = self._list_work_unit_capability_attempts(
                manifest.run_id, manifest.revision, work_unit_id
            )
            if not is_ai and bindings:
                raise StoreError(
                    "non-AI work unit cannot retain capability attempt bindings"
                )
            if is_ai and row.status != NodeStatus.PENDING and not bindings:
                raise StoreError(
                    "started AI work unit has no authoritative capability binding"
                )
            if is_ai and bindings:
                if [item["attempt_ordinal"] for item in bindings] \
                        != list(range(1, len(bindings) + 1)):
                    raise StoreError("work-unit capability attempt ordinals are invalid")
                transition_bindings = attempt_binding_payloads[work_unit_id]
                if len(transition_bindings) != len(bindings):
                    raise StoreError(
                        "work-unit capability binding ledger does not match its audit history"
                    )
                previous_attempt: Optional[Dict[str, Any]] = None
                retryable_statuses = frozenset({
                    "interrupted", "failed", "timeout", "cancelled",
                    "partial", "truncated",
                })
                for index, (binding_row, binding_event) in enumerate(
                    zip(bindings, transition_bindings), start=1
                ):
                    attempt, expected_identity = self._capability_work_unit_identity(
                        manifest, unit, binding_row["attempt_id"]
                    )
                    if binding_row["execution_identity"] != expected_identity \
                            or binding_row["detail"] != self._normalize_work_unit_detail(
                                binding_row["detail"]
                            ):
                        raise StoreError(
                            "work-unit capability binding does not match the attempt journal"
                        )
                    if binding_event["execution_identity"] != expected_identity \
                            or binding_event["detail"] != binding_row["detail"]:
                        raise StoreError(
                            "work-unit capability binding event does not match its ledger"
                        )
                    if index == 1:
                        if attempt["continued_from"]:
                            raise StoreError(
                                "first work-unit capability binding is a continuation"
                            )
                    else:
                        if previous_attempt is None \
                                or previous_attempt["status"] not in retryable_statuses \
                                or attempt["continued_from"] != previous_attempt["attempt_id"] \
                                or binding_event.get("attempt_ordinal") != index \
                                or binding_event.get("continued_from") \
                                != previous_attempt["attempt_id"]:
                            raise StoreError(
                                "work-unit capability continuation chain is invalid"
                            )
                    previous_attempt = attempt
            if row.status == NodeStatus.PENDING:
                if (row.idempotency_key or row.begin_hash or row.detail
                        or row.execution_identity or row.evidence_count
                        or row.completion_hash or row.started_at or row.finished_at):
                    raise StoreError("pending work-unit ledger state is not pristine")
                continue
            begin = begin_payloads.get(work_unit_id)
            if begin is None or not row.idempotency_key or not row.started_at:
                raise StoreError("started work-unit ledger evidence is incomplete")
            expected_begin_hash = content_hash({
                "detail": begin["detail"],
                "execution_identity": begin["execution_identity"],
            })
            if row.begin_hash != expected_begin_hash:
                raise StoreError("work-unit begin fingerprint does not match its audit event")
            if row.status == NodeStatus.RUNNING:
                latest_running = latest_running_payloads.get(work_unit_id)
                if (latest_running is None
                        or row.detail != latest_running["detail"]
                        or row.execution_identity != latest_running["execution_identity"]
                        or row.evidence_count != 0 or row.completion_hash
                        or row.finished_at):
                    raise StoreError("running work-unit ledger state is inconsistent")
                continue
            complete = completion_payloads.get(work_unit_id)
            if complete is None or not row.finished_at:
                raise StoreError("terminal work-unit ledger evidence is incomplete")
            if is_ai:
                latest_attempt = self.get_capability_attempt(bindings[-1]["attempt_id"])
                if latest_attempt is None:  # pragma: no cover - FK plus binding validation
                    raise StoreError("latest capability attempt is missing")
                if latest_attempt["status"] == "complete" and latest_attempt["terminal"]:
                    expected_status = NodeStatus.PASSED
                elif latest_attempt["status"] == "interrupted" \
                        and not latest_attempt["terminal"]:
                    expected_status = NodeStatus.BLOCKED
                elif latest_attempt["terminal"] and latest_attempt["status"] in {
                    "failed", "timeout", "cancelled", "partial", "truncated",
                }:
                    expected_status = NodeStatus.FAILED
                else:
                    raise StoreError(
                        "terminal AI work unit references a non-terminal capability attempt"
                    )
                if NodeStatus(str(complete["status"])) != expected_status:
                    raise StoreError(
                        "AI work-unit status does not match its capability attempt outcome"
                    )
            expected_completion_hash = content_hash({
                "status": complete["status"],
                "detail": complete["detail"],
                "execution_identity": complete["execution_identity"],
                "evidence_count": complete["evidence_count"],
            })
            if (row.detail != complete["detail"]
                    or row.execution_identity != complete["execution_identity"]
                    or row.evidence_count != complete["evidence_count"]
                    or row.completion_hash != expected_completion_hash):
                raise StoreError("terminal work-unit ledger state is inconsistent")
        return rows, validated_events

    def structured_progress(
        self, run_id: str, manifest_revision: Optional[int] = None,
        feed_limit: int = 20,
    ) -> Dict[str, Any]:
        """Project the authoritative ledger into a bounded UI-safe progress view."""
        if isinstance(feed_limit, bool) or not isinstance(feed_limit, int) \
                or not 1 <= feed_limit <= 100:
            raise StoreError("feed_limit must be an integer between 1 and 100")
        run = self.get_run(run_id)
        revision = run.manifest_revision if manifest_revision is None else manifest_revision
        manifest = self.get_manifest(run_id, revision)
        if manifest is None:
            raise StoreError(f"manifest revision not found: {run_id}/{revision}")
        if manifest.work_units:
            rows, validated_events = self._validated_work_unit_projection(manifest)
            by_status: Dict[str, int] = {}
            for row in rows:
                by_status[row.status.value] = by_status.get(row.status.value, 0) + 1
            completed = sum(
                count for status, count in by_status.items()
                if NodeStatus(status) in TERMINAL_NODE_STATUSES
            )
            unit_by_id = {unit.work_unit_id: unit for unit in manifest.work_units}
            running = []
            for row in rows:
                if row.status != NodeStatus.RUNNING:
                    continue
                unit = unit_by_id[row.work_unit_id]
                elapsed = 0
                if row.started_at:
                    started = datetime.datetime.fromisoformat(row.started_at)
                    elapsed = max(0, int((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()))
                running.append({
                    "work_unit_id": row.work_unit_id, "node_id": row.node_id,
                    "label": unit.label, "stage": unit.stage, "scope": unit.scope,
                    "target_ref": unit.target_ref, "detail": row.detail,
                    "execution_identity": row.execution_identity,
                    "started_at": row.started_at, "elapsed_seconds": elapsed,
                })
            feed = validated_events[-feed_limit:]
            total = manifest.total_units()
        else:
            legacy = self.manifest_progress(run_id, revision)
            completed, total, by_status = (
                legacy["completed"], legacy["total"], legacy["by_status"]
            )
            running, feed = [], []
        return {
            "run_id": run_id,
            "manifest_revision": revision,
            "is_current_revision": revision == run.manifest_revision,
            "denominator_hash": self._denominator_hash(manifest, revision),
            "completed": completed,
            "total": total,
            "percent": round((completed * 100.0 / total), 2) if total else 0.0,
            "by_status": by_status,
            "running": running,
            "feed": feed,
        }

    def _work_unit_completion_gate_reasons(
        self, run_id: str, node_id: str, status: NodeStatus,
    ) -> List[str]:
        run = self.get_run(run_id)
        manifest = self.get_manifest(run_id, run.manifest_revision)
        if manifest is None or not manifest.work_units:
            return []
        units = [unit for unit in manifest.work_units if unit.node_id == node_id]
        if not units:
            return []
        rows = {
            row.work_unit_id: row
            for row in self.list_work_unit_runs(run_id, run.manifest_revision)
        }
        reasons = []
        for unit in units:
            row = rows.get(unit.work_unit_id)
            if row is None:
                reasons.append(f"work unit {unit.work_unit_id} is missing")
            elif row.status not in TERMINAL_NODE_STATUSES:
                reasons.append(
                    f"work unit {unit.work_unit_id} is not terminal ({row.status.value})"
                )
            elif (status in domain.DEPENDENCY_SATISFYING_STATUSES
                  and row.status in (NodeStatus.BLOCKED, NodeStatus.FAILED)):
                reasons.append(
                    f"successful node outcome conflicts with work unit "
                    f"{unit.work_unit_id}={row.status.value}"
                )
        return reasons

    # --------------------------------------------------------- nodes/attempts
