"""Publication packet assembly and runtime receipt-gate validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from ...domain.execution import NodeStatus, NodeType
from ...graph.store import Store
from ...runtime import launch_registry as lr
from ...runtime.background_recovery import list_bound_capability_attempts
from ...runtime.capability import CapabilityRequest, InvocationVersions
from ...runtime.run_entry import MonitoringRunEntry
from ...runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .contracts import ProductPublicationError
from .publication_providers import (
    _publication_product_factory,
    _publication_provider_value,
    _r5_publication_types,
    _validate_r5_publication_packet,
)
from .runtime_manifest import _publication_manifest_identity, _runtime_manifest_digest


def build_r5_publication_packet(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
    bridge: Any = None,
    product_packet_factory: Optional[Callable[[Any], Any]] = None,
):
    (
        packet_type,
        bridge_type,
        bridge_error_type,
        input_type,
        _,
    ) = _r5_publication_types()
    value = _publication_provider_value(
        provider, identity, attempts=attempts
    )
    if type(value) is packet_type:
        return _validate_r5_publication_packet(
            value, identity, packet_type=packet_type
        )
    if type(value) is not input_type:
        raise ProductPublicationError("authority_provider_invalid")
    factory = (
        product_packet_factory
        if product_packet_factory is not None
        else _publication_product_factory(provider)
    )
    authority_bridge = bridge
    if authority_bridge is None:
        try:
            authority_bridge = bridge_type(product_packet_factory=factory)
        except Exception as exc:
            raise ProductPublicationError(
                "authority_provider_invalid"
            ) from exc
    build = getattr(authority_bridge, "build", None)
    if not callable(build):
        raise ProductPublicationError("authority_provider_invalid")
    try:
        packet = build(value)
    except bridge_error_type as exc:
        code = str(getattr(exc, "code", "") or "")
        recoverable = code in {
            "S4_BUILD_FAILED",
            "S4_VALIDATION_FAILED",
            "PRODUCT_PACKET_ASSEMBLY_FAILED",
        }
        raise ProductPublicationError(
            "authority_provider_unavailable"
            if recoverable
            else "authority_identity_mismatch",
            recoverable=recoverable,
        ) from exc
    except Exception as exc:
        raise ProductPublicationError(
            "authority_provider_unavailable", recoverable=True
        ) from exc
    return _validate_r5_publication_packet(
        packet, identity, packet_type=packet_type
    )


def _capability_request_from_attempt(
    attempt: Mapping[str, Any],
    profile: Any,
) -> CapabilityRequest:
    try:
        request_json = attempt["request"]
        params = request_json["params"]
        versions_json = params["versions"]
        versions = InvocationVersions(**dict(versions_json))
        expected = params["expected_coverage"]
        request = CapabilityRequest.build(
            attempt_id=str(attempt["attempt_id"]),
            monitoring_run_id=str(attempt["run_id"]),
            node_id=str(attempt["node_id"]),
            manifest_revision=int(attempt["manifest_revision"]),
            profile=profile,
            versions=versions,
            payload=params["input"],
            expected_units=expected,
            continued_from=str(params.get("continued_from") or ""),
        )
    except Exception as exc:
        raise ProductPublicationError("receipt_gate_blocked") from exc
    if (
        request.request_hash != attempt.get("request_hash")
        or request.input_hash != attempt.get("input_hash")
        or request.profile_fingerprint != attempt.get("profile_fingerprint")
        or request.manifest_revision != int(attempt.get("manifest_revision", 0))
    ):
        raise ProductPublicationError("receipt_gate_blocked")
    return request


def read_publication_gate(
    workspace: Path,
    run_id: str,
    *,
    entry: MonitoringRunEntry,
    harness_r1_profile: Any,
) -> dict[str, Any]:
    """Read and validate runtime, deterministic units, and final receipts."""

    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        raise ProductPublicationError("runtime_read_failed", recoverable=True)
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        run = store.get_run(run_id)
        revision = int(run.manifest_revision)
        if revision < 1:
            raise ProductPublicationError(
                "runtime_read_failed", recoverable=True
            )
        manifest = store.get_manifest(run_id, revision)
        if manifest is None:
            raise ProductPublicationError(
                "runtime_read_failed", recoverable=True
            )
        audit = store.verify_audit_chain()
        if (
            not isinstance(audit, tuple)
            or len(audit) != 3
            or audit[0] is not True
        ):
            raise ProductPublicationError("receipt_gate_blocked")
        rows = store.list_work_unit_runs(run_id, revision)
        units = tuple(manifest.work_units)
        row_by_id = {row.work_unit_id: row for row in rows}
        unit_ids = {unit.work_unit_id for unit in units}
        if (
            len(row_by_id) != len(rows)
            or set(row_by_id) != unit_ids
            or any(int(row.manifest_revision) != revision for row in rows)
        ):
            raise ProductPublicationError("runtime_read_failed", recoverable=True)
        node_types = {
            node.node_id: getattr(node.node_type, "value", node.node_type)
            for node in manifest.nodes
        }
        mandatory_units = tuple(unit for unit in units if unit.mandatory)
        deterministic_units = tuple(
            unit
            for unit in mandatory_units
            if node_types.get(unit.node_id) != NodeType.AI_CANDIDATE.value
        )
        ai_units = tuple(
            unit
            for unit in mandatory_units
            if node_types.get(unit.node_id) == NodeType.AI_CANDIDATE.value
        )
        success_statuses = {
            NodeStatus.PASSED,
            NodeStatus.REUSED,
            NodeStatus.SKIPPED,
            NodeStatus.NOT_APPLICABLE,
        }
        if any(row_by_id[unit.work_unit_id].status not in success_statuses for unit in deterministic_units):
            raise ProductPublicationError("deterministic_gate_blocked")
        receipt_ids: list[str] = []
        receipt_attempts: list[dict[str, Any]] = []
        profile_bridge = None
        if ai_units:
            try:
                from packages.medical_monitoring.runtime.harness_runtime import (
                    bridge_from_run_binding,
                    build_r6_prompt,
                    classify_r6_receipt,
                )
                profile_bridge = bridge_from_run_binding(
                    entry.run_binding_store,
                    run_id,
                    r1_profile=harness_r1_profile,
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
        for unit in ai_units:
            try:
                history = list_bound_capability_attempts(
                    store, run_id, revision, unit.work_unit_id
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
            if not history:
                raise ProductPublicationError("receipt_gate_blocked")
            latest = history[-1]
            attempt = latest.get("attempt")
            if (
                not isinstance(attempt, Mapping)
                or attempt.get("status") != "complete"
                or attempt.get("terminal") is not True
                or latest.get("manifest_revision") != revision
                or attempt.get("run_id") != run_id
                or attempt.get("manifest_revision") != revision
                or row_by_id[unit.work_unit_id].status is not NodeStatus.PASSED
            ):
                raise ProductPublicationError("receipt_gate_blocked")
            result = attempt.get("result")
            transport = result.get("transport_execution") if isinstance(result, Mapping) else None
            receipt = transport.get("raw_output") if isinstance(transport, Mapping) else None
            if not isinstance(receipt, Mapping):
                raise ProductPublicationError("receipt_gate_blocked")
            request = _capability_request_from_attempt(
                attempt, profile_bridge.r1_profile
            )
            expected_tokens = tuple(
                f"{coverage.scope}:{coverage.key}"
                for coverage in request.expected_units
            )
            try:
                prompt = build_r6_prompt(request.payload, expected_tokens)
                status, _, _, _ = classify_r6_receipt(
                    request, profile_bridge, receipt, prompt
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
            if status != "complete":
                raise ProductPublicationError("receipt_gate_blocked")
            receipt_id = str(receipt.get("invocation_id", "") or "")
            if not receipt_id or receipt_id in receipt_ids:
                raise ProductPublicationError("receipt_gate_blocked")
            receipt_ids.append(receipt_id)
            receipt_attempts.append(
                {
                    "attempt_id": str(attempt["attempt_id"]),
                    "work_unit_id": unit.work_unit_id,
                    "receipt": dict(receipt),
                }
            )
        identity = _publication_manifest_identity(manifest)
        return {
            "revision": revision,
            "manifest": manifest,
            "identity": identity,
            "digest": _runtime_manifest_digest(manifest),
            "mandatory_denominator": int(identity["mandatory_denominator"]),
            "receipt_ids": tuple(sorted(receipt_ids)),
            "receipt_attempts": tuple(receipt_attempts),
            "receipt_set_digest": lr.content_digest(sorted(receipt_ids)),
        }
    finally:
        if store is not None:
            store.close()

__all__ = [
    "build_r5_publication_packet",
    "read_publication_gate",
]
