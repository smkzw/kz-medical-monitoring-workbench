"""Root-level, per-project append-only R7 business audit ledger.

The ledger is deliberately independent from the R1 runtime audit chain.  It
lives beside the 09A/09B operation projection in ``backup_operations.sqlite3``
and keeps one hash chain per canonical project.  Only this module owns the
project-audit schema and append protocol; callers cannot select another SQLite
store as an audit target.

This is a synthetic/offline core.  It stores opaque lifecycle references and
canonical digests, never project files or medical payloads.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

from .root_ledger_schema import PROJECT_AUDIT_DDL, ROOT_LEDGER_DDL


OPERATIONS_DB_NAME = "backup_operations.sqlite3"
PROJECT_AUDIT_SCHEMA_VERSION = "mm-r7-slice09c-project-audit-v1"
SCHEMA_VERSION = PROJECT_AUDIT_SCHEMA_VERSION
PROJECT_AUDIT_GENESIS = hashlib.sha256(b"mm_r7:project_audit:genesis:v1").hexdigest()
AUDIT_GENESIS = PROJECT_AUDIT_GENESIS

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_TOKEN = re.compile(r"^[^/\\\x00-\x1f\x7f]{1,512}$")
_SAFE_ENUM = re.compile(r"^[^/\\\x00-\x1f\x7f\s]{1,128}$")

_FORBIDDEN_NESTED_KEYS = frozenset(
    {
        "actor",
        "client_actor",
        "center",
        "center_id",
        "database",
        "database_name",
        "model",
        "path",
        "prompt",
        "provider",
        "raw_output",
        "risk",
        "session",
        "stack_trace",
        "subject",
        "subject_id",
        "table",
        "table_name",
        "workspace",
        "workspace_path",
    }
)


class ProjectAuditEventKind(str, Enum):
    BOUNDARY_INTENT = "boundary_intent"
    BOUNDARY_COMMITTED = "boundary_committed"
    BOUNDARY_VERIFIED = "boundary_verified"
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_COMPLETED = "verification_completed"
    RECOVERY_CLASSIFIED = "recovery_classified"
    RECOVERY_COMPLETED = "recovery_completed"
    TRIAGE_RETAINED = "triage_retained"
    ROLLBACK_RELEASE_INTENT = "rollback_release_intent"
    ROLLBACK_EVIDENCE_RELEASED = "rollback_evidence_released"
    ROLLBACK_EVIDENCE_RELEASE_FAILED = "rollback_evidence_release_failed"


# The payload is intentionally not a free-form JSON extension.  Metadata such
# as principal/authorization hashes, operation reference, and chain fields are
# columns, while this fixed map contains only the per-kind class fields.
_EVENT_REQUIRED_FIELDS: Dict[str, frozenset[str]] = {
    ProjectAuditEventKind.BOUNDARY_INTENT.value: frozenset(
        {"operation", "boundary_token", "expected_state", "before_digest"}
    ),
    ProjectAuditEventKind.BOUNDARY_COMMITTED.value: frozenset(
        {"operation", "boundary_token", "observed_durable_phase", "after_digest"}
    ),
    ProjectAuditEventKind.BOUNDARY_VERIFIED.value: frozenset(
        {"operation", "boundary_token", "verifier_outcome", "after_digest"}
    ),
    ProjectAuditEventKind.VERIFICATION_STARTED.value: frozenset(
        {"verifier_version", "snapshot_fingerprint", "before_digest"}
    ),
    ProjectAuditEventKind.VERIFICATION_COMPLETED.value: frozenset(
        {"verifier_version", "snapshot_fingerprint", "verification_result"}
    ),
    ProjectAuditEventKind.RECOVERY_CLASSIFIED.value: frozenset(
        {"operation", "observed_durable_phase", "classification"}
    ),
    ProjectAuditEventKind.RECOVERY_COMPLETED.value: frozenset(
        {"operation", "terminal_outcome", "after_digest"}
    ),
    ProjectAuditEventKind.TRIAGE_RETAINED.value: frozenset(
        {"operation", "observed_durable_phase", "reason_enum"}
    ),
    ProjectAuditEventKind.ROLLBACK_RELEASE_INTENT.value: frozenset(
        {"operation", "verified_event_id", "rollback_digest"}
    ),
    ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASED.value: frozenset(
        {"operation", "release_intent_id", "outcome"}
    ),
    ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASE_FAILED.value: frozenset(
        {"operation", "release_intent_id", "outcome"}
    ),
}

_EVENT_OPTIONAL_FIELDS: Dict[str, frozenset[str]] = {
    ProjectAuditEventKind.BOUNDARY_INTENT.value: frozenset(
        {"package_digest", "source_digest", "plan_digest", "slot_presence"}
    ),
    ProjectAuditEventKind.BOUNDARY_COMMITTED.value: frozenset(
        {"marker_digest", "member_digest", "workspace_digest"}
    ),
    ProjectAuditEventKind.BOUNDARY_VERIFIED.value: frozenset(
        {"r1_anchor", "publication_anchor", "continuity_anchor"}
    ),
    ProjectAuditEventKind.VERIFICATION_STARTED.value: frozenset(
        {"requested_domain_set"}
    ),
    ProjectAuditEventKind.VERIFICATION_COMPLETED.value: frozenset(
        {"exact_domain_anchors", "reason_enum"}
    ),
    ProjectAuditEventKind.RECOVERY_CLASSIFIED.value: frozenset(
        {"slot_anchor", "marker_anchor", "root_ledger_anchor"}
    ),
    ProjectAuditEventKind.RECOVERY_COMPLETED.value: frozenset(
        {"exact_domain_anchors"}
    ),
    ProjectAuditEventKind.TRIAGE_RETAINED.value: frozenset(
        {"slot_anchor", "marker_anchor"}
    ),
    ProjectAuditEventKind.ROLLBACK_RELEASE_INTENT.value: frozenset(),
    ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASED.value: frozenset(
        {"diagnostic_enum"}
    ),
    ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASE_FAILED.value: frozenset(
        {"diagnostic_enum"}
    ),
}

EVENT_KIND_ALLOWLIST: Mapping[str, frozenset[str]] = {
    kind: _EVENT_REQUIRED_FIELDS[kind] | _EVENT_OPTIONAL_FIELDS[kind]
    for kind in _EVENT_REQUIRED_FIELDS
}
EVENT_REQUIRED_FIELDS: Mapping[str, frozenset[str]] = dict(_EVENT_REQUIRED_FIELDS)
EVENT_OPTIONAL_FIELDS: Mapping[str, frozenset[str]] = dict(_EVENT_OPTIONAL_FIELDS)
# Names used by callers that prefer an explicit project prefix.
PROJECT_AUDIT_EVENT_ALLOWLIST = EVENT_KIND_ALLOWLIST
PROJECT_AUDIT_REQUIRED_FIELDS = EVENT_REQUIRED_FIELDS
PROJECT_AUDIT_EVENT_KINDS = tuple(ProjectAuditEventKind)
EVENT_KINDS = tuple(kind.value for kind in ProjectAuditEventKind)
PAYLOAD_ALLOWLIST = EVENT_KIND_ALLOWLIST
REQUIRED_FIELDS_BY_KIND = EVENT_REQUIRED_FIELDS


_OPERATION_MUTABLE_COLUMNS = frozenset(
    {
        "status",
        "progress_percent",
        "current_step",
        "package_id",
        "source_workspace_fingerprint",
        "terminal_outcome",
        "error_code",
        "error_message",
        "rollback_path",
        "staging_path",
        "package_path",
        "maintenance_state",
        "payload",
        "payload_json",
    }
)
_OPERATION_IDENTITY_COLUMNS = frozenset(
    {
        "operation_id",
        "operation_kind",
        "idempotency_key",
        "canonical_project_id",
        "created_at",
        "updated_at",
    }
)
_TERMINAL_OPERATION_STATES = frozenset(
    {
        "available",
        "failed",
        "completed",
        "already_current",
        "retained_for_triage",
        "kept_current",
    }
)


class ProjectAuditError(RuntimeError):
    """Fail-closed error with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = str(code)
        self.message = message or self.code
        self.details = dict(details or {})
        super().__init__(self.code)

    def as_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message}


AuditLedgerError = ProjectAuditError
ProjectAuditLedgerError = ProjectAuditError


@dataclass(frozen=True)
class ProjectAuditHead:
    canonical_project_id: str
    head_seq: int
    head_hash: str

    @property
    def project_scope(self) -> str:
        return self.canonical_project_id

    @property
    def sequence(self) -> int:
        return self.head_seq

    @property
    def chain_hash(self) -> str:
        return self.head_hash

    def as_dict(self) -> Dict[str, Any]:
        return {
            "canonical_project_id": self.canonical_project_id,
            "project_scope": self.canonical_project_id,
            "head_seq": self.head_seq,
            "head_hash": self.head_hash,
        }

    to_dict = as_dict


@dataclass(frozen=True)
class ProjectAuditEvent:
    schema_version: str
    canonical_project_id: str
    project_seq: int
    event_id: str
    event_kind: str
    operation_kind: str
    operation_ref: str
    boundary_token: str
    principal_snapshot_hash: str
    authorization_decision_hash: str
    before_digest: str
    after_digest: str
    domain_anchors: Mapping[str, Any]
    result_code: str
    reason_code: str
    occurred_at: str
    previous_hash: str
    payload: Mapping[str, Any]
    payload_hash: str
    chain_hash: str
    replayed: bool = False

    @property
    def project_scope(self) -> str:
        return self.canonical_project_id

    @property
    def sequence(self) -> int:
        return self.project_seq

    @property
    def event_class(self) -> str:
        return self.event_kind

    @property
    def kind(self) -> str:
        return self.event_kind

    @property
    def operation_id(self) -> str:
        return self.operation_ref

    @property
    def previous_hash_value(self) -> str:
        return self.previous_hash

    @property
    def before_aggregate_digest(self) -> str:
        return self.before_digest

    @property
    def after_aggregate_digest(self) -> str:
        return self.after_digest

    @property
    def result(self) -> str:
        return self.result_code

    @property
    def reason(self) -> str:
        return self.reason_code

    @property
    def timestamp(self) -> str:
        return self.occurred_at

    def as_dict(self, *, include_payload: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "canonical_project_id": self.canonical_project_id,
            "project_scope": self.canonical_project_id,
            "project_seq": self.project_seq,
            "sequence": self.project_seq,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "event_class": self.event_kind,
            "operation_kind": self.operation_kind,
            "operation_ref": self.operation_ref,
            "operation_id": self.operation_ref,
            "boundary_token": self.boundary_token,
            "principal_snapshot_hash": self.principal_snapshot_hash,
            "authorization_decision_hash": self.authorization_decision_hash,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
            "domain_anchors": dict(self.domain_anchors),
            "result_code": self.result_code,
            "reason_code": self.reason_code,
            "occurred_at": self.occurred_at,
            "previous_hash": self.previous_hash,
            "payload_hash": self.payload_hash,
            "chain_hash": self.chain_hash,
            "replayed": self.replayed,
        }
        if include_payload:
            result["payload"] = dict(self.payload)
        return result

    to_dict = as_dict

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


# ---------------------------------------------------------------------------
# Canonical encoding and input validation
# ---------------------------------------------------------------------------


def _canonical_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not accept non-finite numbers")
        return value
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical mappings require string keys")
            result[key] = _canonical_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    raise TypeError("unsupported canonical value: %s" % type(value).__name__)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


content_digest = canonical_digest


def sha256_hex(value: Union[bytes, bytearray, str]) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(bytes(value)).hexdigest()


def _validate_project_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not _SAFE_TOKEN.fullmatch(value)
        or value in {".", ".."}
    ):
        raise ProjectAuditError("invalid_project_id")
    return value


def _validate_token(value: Any, field: str, *, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ProjectAuditError("invalid_%s" % field)
    if not value:
        if required:
            raise ProjectAuditError("missing_%s" % field)
        return ""
    if value != value.strip() or not _SAFE_TOKEN.fullmatch(value):
        raise ProjectAuditError("invalid_%s" % field)
    return value


def _validate_enum(value: Any, field: str, *, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ProjectAuditError("invalid_%s" % field)
    if not value:
        if required:
            raise ProjectAuditError("missing_%s" % field)
        return ""
    if not _SAFE_ENUM.fullmatch(value):
        raise ProjectAuditError("invalid_%s" % field)
    return value


def _utc_timestamp(value: Any, clock: Callable[[], Any]) -> str:
    raw = clock() if value is None else value
    if isinstance(raw, datetime):
        parsed = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ProjectAuditError("invalid_occurred_at") from exc
    else:
        raise ProjectAuditError("invalid_occurred_at")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProjectAuditError("occurred_at_must_be_utc")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _copy_payload(value: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProjectAuditError("payload_must_be_object")
    try:
        encoded = canonical_json_bytes(dict(value))
        if len(encoded) > 256 * 1024:
            raise ProjectAuditError("payload_too_large")
        result = json.loads(encoded.decode("utf-8"))
    except ProjectAuditError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProjectAuditError("payload_not_canonical") from exc
    if not isinstance(result, dict):
        raise ProjectAuditError("payload_must_be_object")
    return result


def _reject_forbidden_nested_content(value: Any, *, nested: bool = False) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProjectAuditError("payload_not_canonical")
            lower = key.lower()
            if nested and (
                lower in _FORBIDDEN_NESTED_KEYS
                or lower.endswith("_path")
                or lower.endswith("_token")
            ):
                raise ProjectAuditError("payload_contains_forbidden_field")
            _reject_forbidden_nested_content(item, nested=True)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_forbidden_nested_content(item, nested=nested)
        return
    if isinstance(value, str) and nested and ("/" in value or "\\" in value):
        raise ProjectAuditError("payload_contains_forbidden_value")


def _validate_payload(kind: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
    allowed = EVENT_KIND_ALLOWLIST[kind]
    keys = set(payload)


    unknown = keys - allowed
    if unknown:
        raise ProjectAuditError(
            "unknown_payload_field",
            details={"fields": sorted(unknown)},
        )
    missing = EVENT_REQUIRED_FIELDS[kind] - keys
    if missing:
        raise ProjectAuditError(
            "missing_payload_field",
            details={"fields": sorted(missing)},
        )
    # Re-encode once to reject NaN/Infinity, non-string nested keys, and
    # unsupported objects even when the top-level map passed validation.
    _reject_forbidden_nested_content(payload)
    return dict(payload)


def _normalise_aliases(
    payload: Dict[str, Any],
    fields: Mapping[str, Any],
    *,
    kind: str,
) -> Dict[str, Any]:
    allowed = EVENT_KIND_ALLOWLIST[kind]
    for name, value in fields.items():
        if name not in allowed:
            raise ProjectAuditError("unknown_event_field", details={"field": name})
        if name in payload and payload[name] != value:
            raise ProjectAuditError("payload_field_conflict", details={"field": name})
        payload[name] = value
    return payload


def _hash_body(
    *,
    schema_version: str,
    project_id: str,
    project_seq: int,
    event_id: str,
    event_kind: str,
    operation_kind: str,
    operation_ref: str,
    boundary_token: str,
    principal_snapshot_hash: str,
    authorization_decision_hash: str,
    before_digest: str,
    after_digest: str,
    domain_anchors: Mapping[str, Any],
    result_code: str,
    reason_code: str,
    occurred_at: str,
    previous_hash: str,
    payload_hash: str,
) -> Dict[str, Any]:
    return {
        "schema_version": schema_version,
        "canonical_project_id": project_id,
        "project_seq": project_seq,
        "event_id": event_id,
        "event_kind": event_kind,
        "operation_kind": operation_kind,
        "operation_ref": operation_ref,
        "boundary_token": boundary_token,
        "principal_snapshot_hash": principal_snapshot_hash,
        "authorization_decision_hash": authorization_decision_hash,
        "before_digest": before_digest,
        "after_digest": after_digest,
        "domain_anchors": dict(domain_anchors),
        "result_code": result_code,
        "reason_code": reason_code,
        "occurred_at": occurred_at,
        "previous_hash": previous_hash,
        "payload_hash": payload_hash,
    }



