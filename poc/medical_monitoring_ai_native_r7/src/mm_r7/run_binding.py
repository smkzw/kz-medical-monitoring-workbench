"""R7 slice-01: deterministic effective-profile freeze and immutable Run binding.

Delegates effective-profile freeze to the accepted R6 ``agent_harness`` registry.
Persists immutable Monitoring Run bindings with idempotent same-input replay and
fail-closed conflict rejection. Stdlib only; no model/provider calls.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# R6 adapter import (read-only; never mutate R6 bytes)
# ---------------------------------------------------------------------------

_R6_SRC = (
    Path(__file__).resolve().parents[3] / "medical_monitoring_ai_native_r6" / "src"
)
if _R6_SRC.is_dir() and str(_R6_SRC) not in sys.path:
    sys.path.insert(0, str(_R6_SRC))

from mm_r6 import agent_harness as _ah  # noqa: E402
from mm_r6.agent_harness import (  # noqa: E402
    ADAPTER_ID,
    ADAPTER_VERSION,
    AgentHarnessError,
    ExecutionProfileLayer,
    FrozenExecutionProfile,
    content_digest,
    freeze_deepseek_flash_max_profile,
    freeze_default_mtplx_profile,
    freeze_execution_profile,
    refuse_auto_fallback,
    validate_frozen_profile,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_MODES = frozenset({"daily", "pre_lock", "post_lock_pre_cfdi"})
KNOWN_EXECUTION_BASES = frozenset({"full", "incremental"})
ALLOWED_MONITORING_MODES = KNOWN_MODES
ALLOWED_EXECUTION_BASES = KNOWN_EXECUTION_BASES

SCHEMA_VERSION = "r7-slice01-run-binding-v1"

_BINDING_DIGEST_KEYS = (
    "adapter_id",
    "adapter_version",
    "data_cutoff",
    "execution_basis",
    "execution_profile_digest",
    "execution_profile_id",
    "fallback_profile_ids",
    "mode",
    "prior_accepted_snapshot_ref",
    "project_id",
    "run_id",
    "schema_version",
    "source_revision_id",
)

_MEDICAL_LEAK_KEYS = frozenset(
    {
        "modeoutput",
        "risk_instance",
        "patientjourney",
        "query_draft",
        "timeline",
        "canonical_fact",
        "report_claim",
        "credential_value",
    }
)


class RunBindingError(RuntimeError):
    """Fail-closed error for Run binding / effective-profile freeze rules."""


# ---------------------------------------------------------------------------
# Effective-profile freeze (R6 delegation)
# ---------------------------------------------------------------------------


def freeze_effective_profile(
    *layers: Optional[ExecutionProfileLayer],
    run_id: str = "",
) -> FrozenExecutionProfile:
    """Freeze one effective R6 ExecutionProfile for a Monitoring Run."""
    try:
        frozen = freeze_execution_profile(*layers, run_id=run_id)
        validate_frozen_profile(frozen)
    except AgentHarnessError as exc:
        raise RunBindingError("effective_profile_freeze_failed:%s" % exc) from exc
    return frozen


def freeze_default_mtplx_effective_profile(
    run_id: str = "",
) -> FrozenExecutionProfile:
    try:
        frozen = freeze_default_mtplx_profile(run_id=run_id)
        validate_frozen_profile(frozen)
    except AgentHarnessError as exc:
        raise RunBindingError("effective_profile_freeze_failed:%s" % exc) from exc
    return frozen


def freeze_deepseek_flash_max_effective_profile(
    run_id: str = "",
) -> FrozenExecutionProfile:
    try:
        frozen = freeze_deepseek_flash_max_profile(run_id=run_id)
        validate_frozen_profile(frozen)
    except AgentHarnessError as exc:
        raise RunBindingError("effective_profile_freeze_failed:%s" % exc) from exc
    return frozen


def assert_no_auto_fallback(
    reason: str = "r7-slice01 forbids automatic fallback",
) -> None:
    try:
        refuse_auto_fallback(reason)
    except AgentHarnessError as exc:
        raise RunBindingError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Immutable Monitoring Run binding
# ---------------------------------------------------------------------------


def _require_non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or value.strip() == "" or value != value.strip():
        raise RunBindingError("invalid_%s" % field)
    return value


def _normalize_prior_ref(
    execution_basis: str, prior_accepted_snapshot_ref: Optional[str]
) -> Optional[str]:
    if execution_basis == "incremental":
        if prior_accepted_snapshot_ref is None:
            raise RunBindingError("incremental_requires_prior_accepted_snapshot_ref")
        if not isinstance(prior_accepted_snapshot_ref, str):
            raise RunBindingError("incremental_requires_prior_accepted_snapshot_ref")
        if prior_accepted_snapshot_ref.strip() == "":
            raise RunBindingError("incremental_requires_prior_accepted_snapshot_ref")
        return _require_non_empty_str(
            prior_accepted_snapshot_ref, "prior_accepted_snapshot_ref"
        )
    if execution_basis == "full":
        if prior_accepted_snapshot_ref is None:
            return None
        if isinstance(prior_accepted_snapshot_ref, str) and (
            prior_accepted_snapshot_ref.strip() == ""
        ):
            return None
        raise RunBindingError("full_forbids_prior_accepted_snapshot_ref")
    raise RunBindingError("unknown_execution_basis:%s" % execution_basis)


def _frozen_profile_blob(frozen: FrozenExecutionProfile) -> Dict[str, Any]:
    return {
        "adapter_id": frozen.adapter_id,
        "adapter_version": frozen.adapter_version,
        "allowed_tools": list(frozen.allowed_tools),
        "capability_id": frozen.capability_id,
        "context_isolation": frozen.context_isolation,
        "credential_ref": frozen.credential_ref,
        "effective_selector": frozen.effective_selector,
        "execution_profile_digest": frozen.execution_profile_digest,
        "execution_profile_id": frozen.execution_profile_id,
        "fallback_profile_ids": list(frozen.fallback_profile_ids),
        "profile_id": frozen.profile_id,
        "profile_revision": frozen.profile_revision,
        "reasoning_effort": frozen.reasoning_effort,
        "requested_model": frozen.requested_model,
        "requested_provider": frozen.requested_provider,
        "timeout_seconds": frozen.timeout_seconds,
        "user_config_name": frozen.user_config_name,
    }


def _frozen_from_blob(blob: Mapping[str, Any]) -> FrozenExecutionProfile:
    try:
        return FrozenExecutionProfile(
            profile_id=str(blob["profile_id"]),
            profile_revision=str(blob["profile_revision"]),
            capability_id=str(blob["capability_id"]),
            requested_provider=str(blob["requested_provider"]),
            requested_model=str(blob["requested_model"]),
            user_config_name=str(blob["user_config_name"]),
            effective_selector=str(blob["effective_selector"]),
            reasoning_effort=str(blob["reasoning_effort"]),
            timeout_seconds=int(blob["timeout_seconds"]),
            allowed_tools=tuple(str(t) for t in blob["allowed_tools"]),
            context_isolation=str(blob["context_isolation"]),
            credential_ref=str(blob["credential_ref"]),
            adapter_id=str(blob["adapter_id"]),
            adapter_version=str(blob["adapter_version"]),
            fallback_profile_ids=tuple(str(x) for x in blob["fallback_profile_ids"]),
            execution_profile_id=str(blob["execution_profile_id"]),
            execution_profile_digest=str(blob["execution_profile_digest"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RunBindingError("forged_or_corrupt_frozen_profile:%s" % exc) from exc


def compute_binding_digest(body: Mapping[str, Any]) -> str:
    canonical = {key: body[key] for key in _BINDING_DIGEST_KEYS}
    return content_digest(canonical)


@dataclass(frozen=True)
class MonitoringRunBinding:
    """Immutable Monitoring Run ↔ effective ExecutionProfile binding."""

    run_id: str
    project_id: str
    mode: str
    execution_basis: str
    data_cutoff: str
    source_revision_id: str
    prior_accepted_snapshot_ref: Optional[str]
    execution_profile_id: str
    execution_profile_digest: str
    profile_id: str
    user_config_name: str
    effective_selector: str
    adapter_id: str
    adapter_version: str
    fallback_profile_ids: Tuple[str, ...]
    binding_digest: str
    schema_version: str = SCHEMA_VERSION

    def digest_body(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "data_cutoff": self.data_cutoff,
            "execution_basis": self.execution_basis,
            "execution_profile_digest": self.execution_profile_digest,
            "execution_profile_id": self.execution_profile_id,
            "fallback_profile_ids": list(self.fallback_profile_ids),
            "mode": self.mode,
            "prior_accepted_snapshot_ref": self.prior_accepted_snapshot_ref,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "schema_version": self.schema_version,
            "source_revision_id": self.source_revision_id,
        }


def build_monitoring_run_binding(
    *,
    run_id: str,
    project_id: str,
    mode: str,
    execution_basis: str,
    data_cutoff: str,
    source_revision_id: str,
    frozen: FrozenExecutionProfile,
    prior_accepted_snapshot_ref: Optional[str] = None,
) -> MonitoringRunBinding:
    run_id = _require_non_empty_str(run_id, "run_id")
    project_id = _require_non_empty_str(project_id, "project_id")
    mode = _require_non_empty_str(mode, "mode")
    execution_basis = _require_non_empty_str(execution_basis, "execution_basis")
    data_cutoff = _require_non_empty_str(data_cutoff, "data_cutoff")
    source_revision_id = _require_non_empty_str(source_revision_id, "source_revision_id")

    if mode not in KNOWN_MODES:
        raise RunBindingError("unknown_mode:%s" % mode)
    if execution_basis not in KNOWN_EXECUTION_BASES:
        raise RunBindingError("unknown_execution_basis:%s" % execution_basis)

    prior = _normalize_prior_ref(execution_basis, prior_accepted_snapshot_ref)

    if not isinstance(frozen, FrozenExecutionProfile):
        raise RunBindingError("invalid_frozen_type")
    try:
        validate_frozen_profile(frozen)
    except AgentHarnessError as exc:
        raise RunBindingError("forged_frozen_profile:%s" % exc) from exc

    if frozen.adapter_id != ADAPTER_ID or frozen.adapter_version != ADAPTER_VERSION:
        raise RunBindingError(
            "unsupported_adapter:%s/%s" % (frozen.adapter_id, frozen.adapter_version)
        )

    fallback = tuple(frozen.fallback_profile_ids)
    body = {
        "adapter_id": frozen.adapter_id,
        "adapter_version": frozen.adapter_version,
        "data_cutoff": data_cutoff,
        "execution_basis": execution_basis,
        "execution_profile_digest": frozen.execution_profile_digest,
        "execution_profile_id": frozen.execution_profile_id,
        "fallback_profile_ids": list(fallback),
        "mode": mode,
        "prior_accepted_snapshot_ref": prior,
        "project_id": project_id,
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "source_revision_id": source_revision_id,
    }
    digest = compute_binding_digest(body)
    return MonitoringRunBinding(
        run_id=run_id,
        project_id=project_id,
        mode=mode,
        execution_basis=execution_basis,
        data_cutoff=data_cutoff,
        source_revision_id=source_revision_id,
        prior_accepted_snapshot_ref=prior,
        execution_profile_id=frozen.execution_profile_id,
        execution_profile_digest=frozen.execution_profile_digest,
        profile_id=frozen.profile_id,
        user_config_name=frozen.user_config_name,
        effective_selector=frozen.effective_selector,
        adapter_id=frozen.adapter_id,
        adapter_version=frozen.adapter_version,
        fallback_profile_ids=fallback,
        binding_digest=digest,
        schema_version=SCHEMA_VERSION,
    )


def validate_binding_against_frozen(
    binding: MonitoringRunBinding, frozen: FrozenExecutionProfile
) -> None:
    try:
        validate_frozen_profile(frozen)
    except AgentHarnessError as exc:
        raise RunBindingError("forged_frozen_profile:%s" % exc) from exc
    if frozen.execution_profile_id != binding.execution_profile_id:
        raise RunBindingError("execution_profile_id_mismatch")
    if frozen.execution_profile_digest != binding.execution_profile_digest:
        raise RunBindingError("execution_profile_digest_mismatch")
    if frozen.adapter_id != binding.adapter_id or frozen.adapter_version != binding.adapter_version:
        raise RunBindingError("adapter_identity_mismatch")
    if frozen.user_config_name != binding.user_config_name:
        raise RunBindingError("user_config_name_mismatch")
    if frozen.profile_id != binding.profile_id:
        raise RunBindingError("profile_id_mismatch")
    if frozen.effective_selector != binding.effective_selector:
        raise RunBindingError("effective_selector_mismatch")
    if tuple(frozen.fallback_profile_ids) != tuple(binding.fallback_profile_ids):
        raise RunBindingError("fallback_profile_ids_mismatch")
    expected = compute_binding_digest(binding.digest_body())
    if expected != binding.binding_digest:
        raise RunBindingError("binding_digest_mismatch")


def _scrub_projection(payload: Mapping[str, Any], *, surface: str) -> Dict[str, Any]:
    out = dict(payload)
    lowered_keys = {str(k).lower() for k in out.keys()}
    for bad in _MEDICAL_LEAK_KEYS | {"credential_ref"}:
        if bad in lowered_keys:
            raise RunBindingError("projection_forbidden_field:%s:%s" % (surface, bad))
    blob = json.dumps(out, ensure_ascii=False)
    lowered = blob.lower()
    if "sk-" in lowered or "credential_value" in lowered or "credential_ref" in lowered:
        raise RunBindingError("%s_projection_leaked_credential_material" % surface)
    for medical_key in _MEDICAL_LEAK_KEYS:
        if medical_key in lowered:
            raise RunBindingError("projection_medical_leak:%s:%s" % (surface, medical_key))
    return out


def public_projection(binding: MonitoringRunBinding) -> Dict[str, Any]:
    """User-facing projection: configuration names; no secrets or selectors."""
    out = {
        "run_id": binding.run_id,
        "project_id": binding.project_id,
        "mode": binding.mode,
        "execution_basis": binding.execution_basis,
        "data_cutoff": binding.data_cutoff,
        "source_revision_id": binding.source_revision_id,
        "prior_accepted_snapshot_ref": binding.prior_accepted_snapshot_ref,
        "user_config_name": binding.user_config_name,
        "adapter_id": binding.adapter_id,
        "adapter_version": binding.adapter_version,
        "schema_version": binding.schema_version,
    }
    return _scrub_projection(out, surface="public")


def audit_projection(binding: MonitoringRunBinding) -> Dict[str, Any]:
    """Audit projection: may include effective selector and exact digests."""
    out = {
        "run_id": binding.run_id,
        "project_id": binding.project_id,
        "mode": binding.mode,
        "execution_basis": binding.execution_basis,
        "data_cutoff": binding.data_cutoff,
        "source_revision_id": binding.source_revision_id,
        "prior_accepted_snapshot_ref": binding.prior_accepted_snapshot_ref,
        "user_config_name": binding.user_config_name,
        "effective_selector": binding.effective_selector,
        "profile_id": binding.profile_id,
        "execution_profile_id": binding.execution_profile_id,
        "execution_profile_digest": binding.execution_profile_digest,
        "adapter_id": binding.adapter_id,
        "adapter_version": binding.adapter_version,
        "fallback_profile_ids": list(binding.fallback_profile_ids),
        "binding_digest": binding.binding_digest,
        "schema_version": binding.schema_version,
    }
    return _scrub_projection(out, surface="audit")


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS monitoring_run_bindings (
    run_id TEXT PRIMARY KEY NOT NULL,
    binding_digest TEXT NOT NULL,
    project_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    execution_basis TEXT NOT NULL,
    data_cutoff TEXT NOT NULL,
    source_revision_id TEXT NOT NULL,
    prior_accepted_snapshot_ref TEXT,
    execution_profile_id TEXT NOT NULL,
    execution_profile_digest TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    user_config_name TEXT NOT NULL,
    effective_selector TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    fallback_profile_ids_json TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    frozen_profile_json TEXT NOT NULL,
    record_json TEXT NOT NULL
);
"""


def _record_payload(
    binding: MonitoringRunBinding, frozen_blob: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        **binding.digest_body(),
        "binding_digest": binding.binding_digest,
        "effective_selector": binding.effective_selector,
        "profile_id": binding.profile_id,
        "user_config_name": binding.user_config_name,
        "frozen_profile": dict(frozen_blob),
    }


def _assert_current_schema(path: Path) -> None:
    """Reject an existing non-current file before any writable SQLite call."""
    if not path.exists():
        return
    from .schema_manifest import SchemaClassification, inspect_member

    report = inspect_member(path, "run_binding")
    if report.classification is not SchemaClassification.CURRENT:
        raise RunBindingError(
            "unsupported_schema_version:%s" % report.reason_code
        )


class RunBindingStore:
    """Append-once SQLite store for immutable Monitoring Run bindings."""

    def __init__(
        self,
        db_path: Union[str, Path],
        profile_store: Any = None,
    ) -> None:
        self.db_path = Path(db_path)
        _assert_current_schema(self.db_path)
        if self.db_path.parent and str(self.db_path.parent) not in ("", "."):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._profile_store = profile_store  # optional; freeze is module-level
        self._conn: Optional[sqlite3.Connection] = None
        self.open()

    def open(self) -> None:
        if self._conn is not None:
            return
        _assert_current_schema(self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(_DDL)
        conn.commit()
        self._conn = conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def reopen(self) -> None:
        self.close()
        self.open()

    def __enter__(self) -> "RunBindingStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RunBindingError("store_closed")
        return self._conn

    def bind(
        self,
        *,
        run_id: str,
        project_id: str,
        mode: str,
        execution_basis: str,
        data_cutoff: str,
        source_revision_id: str,
        frozen: FrozenExecutionProfile,
        prior_accepted_snapshot_ref: Optional[str] = None,
    ) -> MonitoringRunBinding:
        """Persist a binding. Same input is idempotent; conflicts fail closed."""
        binding = build_monitoring_run_binding(
            run_id=run_id,
            project_id=project_id,
            mode=mode,
            execution_basis=execution_basis,
            data_cutoff=data_cutoff,
            source_revision_id=source_revision_id,
            frozen=frozen,
            prior_accepted_snapshot_ref=prior_accepted_snapshot_ref,
        )
        validate_binding_against_frozen(binding, frozen)
        frozen_blob = _frozen_profile_blob(frozen)

        existing = self._fetch_row(binding.run_id)
        if existing is not None:
            return self._replay_or_conflict(existing, binding, frozen)

        record = _record_payload(binding, frozen_blob)
        conn = self._require_conn()
        conn.execute(
            """
            INSERT INTO monitoring_run_bindings (
                run_id, binding_digest, project_id, mode, execution_basis,
                data_cutoff, source_revision_id, prior_accepted_snapshot_ref,
                execution_profile_id, execution_profile_digest, profile_id,
                user_config_name, effective_selector, adapter_id, adapter_version,
                fallback_profile_ids_json, schema_version, frozen_profile_json,
                record_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                binding.run_id,
                binding.binding_digest,
                binding.project_id,
                binding.mode,
                binding.execution_basis,
                binding.data_cutoff,
                binding.source_revision_id,
                binding.prior_accepted_snapshot_ref,
                binding.execution_profile_id,
                binding.execution_profile_digest,
                binding.profile_id,
                binding.user_config_name,
                binding.effective_selector,
                binding.adapter_id,
                binding.adapter_version,
                json.dumps(
                    list(binding.fallback_profile_ids),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                binding.schema_version,
                json.dumps(
                    frozen_blob,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        conn.commit()
        return binding

    def get(self, run_id: str) -> MonitoringRunBinding:
        row = self._fetch_row(run_id)
        if row is None:
            raise RunBindingError("run_binding_not_found:%s" % run_id)
        binding, frozen = self._row_to_binding(row)
        validate_binding_against_frozen(binding, frozen)
        return binding

    def get_with_frozen(
        self, run_id: str
    ) -> Tuple[MonitoringRunBinding, FrozenExecutionProfile]:
        row = self._fetch_row(run_id)
        if row is None:
            raise RunBindingError("run_binding_not_found:%s" % run_id)
        binding, frozen = self._row_to_binding(row)
        validate_binding_against_frozen(binding, frozen)
        return binding, frozen

    def reopen_and_validate(self, run_id: str) -> MonitoringRunBinding:
        self._require_conn().commit()
        self.reopen()
        binding, frozen = self.get_with_frozen(run_id)
        try:
            validate_frozen_profile(frozen)
        except AgentHarnessError as exc:
            raise RunBindingError("reopen_profile_identity_failed:%s" % exc) from exc
        expected = compute_binding_digest(binding.digest_body())
        if expected != binding.binding_digest:
            raise RunBindingError("reopen_binding_digest_mismatch")
        return binding

    def _fetch_row(self, run_id: str) -> Optional[sqlite3.Row]:
        return self._require_conn().execute(
            "SELECT * FROM monitoring_run_bindings WHERE run_id = ?", (run_id,)
        ).fetchone()

    def _row_to_binding(
        self, row: sqlite3.Row
    ) -> Tuple[MonitoringRunBinding, FrozenExecutionProfile]:
        try:
            frozen_blob = json.loads(row["frozen_profile_json"])
            fallback_raw = json.loads(row["fallback_profile_ids_json"])
            stored_record = json.loads(row["record_json"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise RunBindingError("corrupt_run_binding_json:%s" % exc) from exc
        if not isinstance(frozen_blob, dict):
            raise RunBindingError("corrupt_frozen_profile_json")
        if not isinstance(fallback_raw, list):
            raise RunBindingError("corrupt_fallback_profile_ids_json")
        if not isinstance(stored_record, dict):
            raise RunBindingError("corrupt_record_json")
        frozen = _frozen_from_blob(frozen_blob)
        try:
            validate_frozen_profile(frozen)
        except AgentHarnessError as exc:
            raise RunBindingError("stored_frozen_profile_invalid:%s" % exc) from exc

        fallback = tuple(str(value) for value in fallback_raw)
        binding = MonitoringRunBinding(
            run_id=row["run_id"],
            project_id=row["project_id"],
            mode=row["mode"],
            execution_basis=row["execution_basis"],
            data_cutoff=row["data_cutoff"],
            source_revision_id=row["source_revision_id"],
            prior_accepted_snapshot_ref=row["prior_accepted_snapshot_ref"],
            execution_profile_id=row["execution_profile_id"],
            execution_profile_digest=row["execution_profile_digest"],
            profile_id=row["profile_id"],
            user_config_name=row["user_config_name"],
            effective_selector=row["effective_selector"],
            adapter_id=row["adapter_id"],
            adapter_version=row["adapter_version"],
            fallback_profile_ids=fallback,
            binding_digest=row["binding_digest"],
            schema_version=row["schema_version"],
        )
        validate_binding_against_frozen(binding, frozen)
        if stored_record != _record_payload(binding, frozen_blob):
            raise RunBindingError("record_json_mismatch")
        return binding, frozen

    def _replay_or_conflict(
        self,
        existing_row: sqlite3.Row,
        candidate: MonitoringRunBinding,
        frozen: FrozenExecutionProfile,
    ) -> MonitoringRunBinding:
        existing, existing_frozen = self._row_to_binding(existing_row)
        validate_binding_against_frozen(existing, existing_frozen)

        same_data = (
            existing.project_id == candidate.project_id
            and existing.mode == candidate.mode
            and existing.execution_basis == candidate.execution_basis
            and existing.data_cutoff == candidate.data_cutoff
            and existing.source_revision_id == candidate.source_revision_id
            and existing.prior_accepted_snapshot_ref
            == candidate.prior_accepted_snapshot_ref
        )
        same_profile = (
            existing.execution_profile_id == candidate.execution_profile_id
            and existing.execution_profile_digest == candidate.execution_profile_digest
            and existing.adapter_id == candidate.adapter_id
            and existing.adapter_version == candidate.adapter_version
        )
        if (
            same_data
            and same_profile
            and existing.binding_digest == candidate.binding_digest
        ):
            validate_binding_against_frozen(existing, frozen)
            return existing

        if not same_profile:
            raise RunBindingError(
                "conflicting_replay_effective_profile:%s" % candidate.run_id
            )
        if not same_data:
            raise RunBindingError(
                "conflicting_replay_data_identity:%s" % candidate.run_id
            )
        raise RunBindingError("conflicting_replay:%s" % candidate.run_id)


def bind_monitoring_run(
    store: RunBindingStore,
    *,
    run_id: str,
    project_id: str,
    mode: str,
    execution_basis: str,
    data_cutoff: str,
    source_revision_id: str,
    layers: Sequence[Optional[ExecutionProfileLayer]] = (),
    prior_accepted_snapshot_ref: Optional[str] = None,
    frozen: Optional[FrozenExecutionProfile] = None,
) -> MonitoringRunBinding:
    """Convenience: freeze (unless provided) then immutable-bind into ``store``."""
    if frozen is None:
        frozen = freeze_effective_profile(*layers, run_id=run_id)
    else:
        try:
            validate_frozen_profile(frozen)
        except AgentHarnessError as exc:
            raise RunBindingError("forged_frozen_profile:%s" % exc) from exc
    return store.bind(
        run_id=run_id,
        project_id=project_id,
        mode=mode,
        execution_basis=execution_basis,
        data_cutoff=data_cutoff,
        source_revision_id=source_revision_id,
        frozen=frozen,
        prior_accepted_snapshot_ref=prior_accepted_snapshot_ref,
    )


__all__ = [
    "ADAPTER_ID",
    "ADAPTER_VERSION",
    "ALLOWED_EXECUTION_BASES",
    "ALLOWED_MONITORING_MODES",
    "KNOWN_EXECUTION_BASES",
    "KNOWN_MODES",
    "SCHEMA_VERSION",
    "ExecutionProfileLayer",
    "FrozenExecutionProfile",
    "MonitoringRunBinding",
    "RunBindingError",
    "RunBindingStore",
    "assert_no_auto_fallback",
    "audit_projection",
    "bind_monitoring_run",
    "build_monitoring_run_binding",
    "compute_binding_digest",
    "freeze_deepseek_flash_max_effective_profile",
    "freeze_default_mtplx_effective_profile",
    "freeze_effective_profile",
    "public_projection",
    "validate_binding_against_frozen",
]
