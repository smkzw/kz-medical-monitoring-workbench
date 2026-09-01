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


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


class ProjectAuditLedger:
    """One root SQLite ledger with one CAS hash chain per project."""

    def __init__(
        self,
        root_or_db_path: Union[str, Path],
        *,
        clock: Optional[Callable[[], Any]] = None,
        event_id_factory: Optional[Callable[[], Any]] = None,
        failure_hook: Optional[Callable[[str], None]] = None,
    ) -> None:
        candidate = Path(root_or_db_path)
        if candidate.suffix == ".sqlite3":
            if candidate.name != OPERATIONS_DB_NAME:
                raise ProjectAuditError("invalid_root_ledger_path")
            self.path = candidate
        else:
            self.path = candidate / OPERATIONS_DB_NAME
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._event_id_factory = event_id_factory or (lambda: uuid.uuid4().hex)
        self._failure_hook = failure_hook
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            str(self.path), timeout=10.0, isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        try:
            self._reject_r1_store()
            self._conn.executescript(ROOT_LEDGER_DDL)
            self._assert_schema()
        except ProjectAuditError:
            self._conn.close()
            raise
        except sqlite3.Error as exc:
            self._conn.close()
            raise ProjectAuditError("project_audit_schema_error") from exc

    def _reject_r1_store(self) -> None:
        rows = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)",
            ("audit_events", "audit_chain_head"),
        ).fetchall()
        if rows:
            raise ProjectAuditError("wrong_audit_store")

    def _assert_schema(self) -> None:
        expected = {
            "project_audit_events": {
                "canonical_project_id", "project_seq", "event_id", "schema_version",
                "event_kind", "operation_kind", "operation_ref", "boundary_token",
                "principal_snapshot_hash", "authorization_decision_hash", "before_digest",
                "after_digest", "domain_anchors_json", "result_code", "reason_code",
                "occurred_at", "previous_hash", "payload_json", "payload_hash", "chain_hash",
            },
            "project_audit_heads": {"canonical_project_id", "head_seq", "head_hash"},
        }
        for table, columns in expected.items():
            actual = {
                str(row[1])
                for row in self._conn.execute("PRAGMA table_info(%s)" % table).fetchall()
            }
            if not columns.issubset(actual):
                raise ProjectAuditError("project_audit_schema_error", details={"table": table})

    @property
    def connection(self) -> sqlite3.Connection:
        """The root connection for synthetic fault-injection tests."""
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "ProjectAuditLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def set_failure_hook(self, hook: Optional[Callable[[str], None]]) -> None:
        self._failure_hook = hook

    def _hook(self, point: str) -> None:
        if self._failure_hook is not None:
            self._failure_hook(point)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Expose one guarded root transaction for integration adapters.

        The context is intentionally connection-scoped and does not provide a
        generic cross-store append helper.  Audit append methods remain the
        only place that can advance a project chain head.
        """
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
                self._conn.execute("COMMIT")
            except BaseException:
                try:
                    self._conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise

    def _begin(self) -> None:
        try:
            self._conn.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as exc:
            raise ProjectAuditError("project_audit_busy") from exc

    def _rollback(self) -> None:
        try:
            self._conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass

    def _head_row(self, project_id: str) -> Optional[sqlite3.Row]:
        return self._conn.execute(
            "SELECT canonical_project_id, head_seq, head_hash FROM project_audit_heads "
            "WHERE canonical_project_id=?",
            (project_id,),
        ).fetchone()

    def head(self, canonical_project_id: str) -> ProjectAuditHead:
        project = _validate_project_id(canonical_project_id)
        with self._lock:
            row = self._head_row(project)
            if row is None:
                return ProjectAuditHead(project, 0, PROJECT_AUDIT_GENESIS)
            return ProjectAuditHead(project, int(row["head_seq"]), str(row["head_hash"]))

    get_head = head
    chain_head = head

    def heads(self) -> Tuple[ProjectAuditHead, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT canonical_project_id, head_seq, head_hash "
                "FROM project_audit_heads ORDER BY canonical_project_id"
            ).fetchall()
            return tuple(
                ProjectAuditHead(str(row[0]), int(row[1]), str(row[2])) for row in rows
            )

    def _ensure_head(self, project_id: str) -> Tuple[int, str]:
        row = self._head_row(project_id)
        if row is None:
            existing = self._conn.execute(
                "SELECT 1 FROM project_audit_events WHERE canonical_project_id=? LIMIT 1",
                (project_id,),
            ).fetchone()
            if existing is not None:
                raise ProjectAuditError("project_audit_head_missing")
            self._conn.execute(
                "INSERT INTO project_audit_heads(canonical_project_id, head_seq, head_hash) VALUES(?,?,?)",
                (project_id, 0, PROJECT_AUDIT_GENESIS),
            )
            return 0, PROJECT_AUDIT_GENESIS
        return int(row["head_seq"]), str(row["head_hash"])

    def _tail_matches_head(self, project_id: str, head_seq: int, head_hash: str) -> bool:
        row = self._conn.execute(
            "SELECT project_seq, chain_hash FROM project_audit_events "
            "WHERE canonical_project_id=? ORDER BY project_seq DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if row is None:
            return head_seq == 0 and head_hash == PROJECT_AUDIT_GENESIS
        return int(row["project_seq"]) == head_seq and str(row["chain_hash"]) == head_hash

    def _event_from_row(self, row: sqlite3.Row, *, replayed: bool = False) -> ProjectAuditEvent:
        try:
            anchors = json.loads(str(row["domain_anchors_json"]))
            payload = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProjectAuditError("project_audit_row_corrupt") from exc
        if not isinstance(anchors, dict) or not isinstance(payload, dict):
            raise ProjectAuditError("project_audit_row_corrupt")
        return ProjectAuditEvent(
            schema_version=str(row["schema_version"]),
            canonical_project_id=str(row["canonical_project_id"]),
            project_seq=int(row["project_seq"]),
            event_id=str(row["event_id"]),
            event_kind=str(row["event_kind"]),
            operation_kind=str(row["operation_kind"]),
            operation_ref=str(row["operation_ref"]),
            boundary_token=str(row["boundary_token"]),
            principal_snapshot_hash=str(row["principal_snapshot_hash"]),
            authorization_decision_hash=str(row["authorization_decision_hash"]),
            before_digest=str(row["before_digest"]),
            after_digest=str(row["after_digest"]),
            domain_anchors=anchors,
            result_code=str(row["result_code"]),
            reason_code=str(row["reason_code"]),
            occurred_at=str(row["occurred_at"]),
            previous_hash=str(row["previous_hash"]),
            payload=payload,
            payload_hash=str(row["payload_hash"]),
            chain_hash=str(row["chain_hash"]),
            replayed=replayed,
        )

    def _find_duplicate(
        self,
        *,
        project_id: str,
        event_id: str,
        operation_ref: str,
        boundary_token: str,
        event_kind: str,
    ) -> Optional[sqlite3.Row]:
        row = self._conn.execute(
            "SELECT * FROM project_audit_events WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is not None:
            return row
        if operation_ref and boundary_token:
            return self._conn.execute(
                "SELECT * FROM project_audit_events WHERE operation_ref=? "
                "AND boundary_token=? AND event_kind=?",
                (operation_ref, boundary_token, event_kind),
            ).fetchone()
        return None

    @staticmethod
    def _identity_projection(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "canonical_project_id": str(row["canonical_project_id"]),
            "schema_version": str(row["schema_version"]),
            "event_kind": str(row["event_kind"]),
            "operation_kind": str(row["operation_kind"]),
            "operation_ref": str(row["operation_ref"]),
            "boundary_token": str(row["boundary_token"]),
            "principal_snapshot_hash": str(row["principal_snapshot_hash"]),
            "authorization_decision_hash": str(row["authorization_decision_hash"]),
            "before_digest": str(row["before_digest"]),
            "after_digest": str(row["after_digest"]),
            "domain_anchors_json": str(row["domain_anchors_json"]),
            "result_code": str(row["result_code"]),
            "reason_code": str(row["reason_code"]),
            "occurred_at": str(row["occurred_at"]),
            "payload_json": str(row["payload_json"]),
        }

    def _candidate_identity(
        self,
        *,
        project_id: str,
        event_kind: str,
        operation_kind: str,
        operation_ref: str,
        boundary_token: str,
        principal_snapshot_hash: str,
        authorization_decision_hash: str,
        before_digest: str,
        after_digest: str,
        domain_anchors_json: str,
        result_code: str,
        reason_code: str,
        occurred_at: str,
        payload_json: str,
    ) -> Dict[str, Any]:
        return {
            "canonical_project_id": project_id,
            "schema_version": PROJECT_AUDIT_SCHEMA_VERSION,
            "event_kind": event_kind,
            "operation_kind": operation_kind,
            "operation_ref": operation_ref,
            "boundary_token": boundary_token,
            "principal_snapshot_hash": principal_snapshot_hash,
            "authorization_decision_hash": authorization_decision_hash,
            "before_digest": before_digest,
            "after_digest": after_digest,
            "domain_anchors_json": domain_anchors_json,
            "result_code": result_code,
            "reason_code": reason_code,
            "occurred_at": occurred_at,
            "payload_json": payload_json,
        }

    @staticmethod
    def _same_identity(
        existing: Mapping[str, Any],
        candidate: Mapping[str, Any],
        *,
        boundary_replay: bool,
    ) -> bool:
        left = dict(existing)
        right = dict(candidate)
        # Boundary idempotency is keyed by (operation, token, kind); retries
        # often generate a fresh opaque event id and timestamp, but may not
        # change any business field.  An explicit event_id remains stricter.
        if boundary_replay:
            left.pop("occurred_at", None)
            right.pop("occurred_at", None)
        return left == right

    def _normalise_operation_update(
        self,
        operation_id: Optional[str],
        update: Optional[Mapping[str, Any]],
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        if update is None:
            return operation_id, {}
        if not isinstance(update, Mapping):
            raise ProjectAuditError("operation_projection_must_be_object")
        values = dict(update)
        embedded = values.pop("operation_id", None)
        if operation_id is None:
            operation_id = embedded
        elif embedded is not None and embedded != operation_id:
            raise ProjectAuditError("operation_projection_conflict")
        if operation_id is not None:
            operation_id = _validate_token(operation_id, "operation_id", required=True)
        allow_terminal_reopen = values.pop("allow_terminal_reopen", False)
        if not isinstance(allow_terminal_reopen, bool):
            raise ProjectAuditError("operation_projection_conflict")
        unknown = set(values) - _OPERATION_MUTABLE_COLUMNS
        if unknown:
            # Identity columns are called out separately so callers get a
            # stable conflict code rather than an arbitrary SQL error.
            if unknown & _OPERATION_IDENTITY_COLUMNS:
                raise ProjectAuditError("operation_identity_immutable")
            raise ProjectAuditError("unknown_operation_projection_field")
        if "payload" in values and "payload_json" in values:
            raise ProjectAuditError("operation_projection_conflict")
        if "payload" in values:
            payload = values.pop("payload")
            if not isinstance(payload, Mapping):
                raise ProjectAuditError("operation_payload_must_be_object")
            values["payload_json"] = canonical_json(dict(payload))
        if "payload_json" in values:
            raw = values["payload_json"]
            if not isinstance(raw, str):
                raise ProjectAuditError("operation_payload_must_be_object")
            try:
                decoded = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ProjectAuditError("operation_payload_must_be_object") from exc
            if not isinstance(decoded, dict) or canonical_json(decoded) != raw:
                raise ProjectAuditError("operation_payload_not_canonical")
        if allow_terminal_reopen:
            values["_allow_terminal_reopen"] = True
        return operation_id, values

    def _apply_operation_projection(
        self,
        *,
        project_id: str,
        operation_id: Optional[str],
        updates: Mapping[str, Any],
        occurred_at: str,
    ) -> None:
        if not updates and operation_id is None:
            return
        if operation_id is None:
            raise ProjectAuditError("operation_projection_requires_operation")
        row = self._conn.execute(
            "SELECT * FROM backup_operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
        if row is None:
            raise ProjectAuditError("operation_not_found")
        if str(row["canonical_project_id"]) != project_id:
            raise ProjectAuditError("operation_project_mismatch")
        fields: Dict[str, Any] = {
            str(key): row[key] for key in _OPERATION_MUTABLE_COLUMNS if key in row.keys()
        }
        # payload is an API alias and is not a database column.
        if "payload_json" in fields:
            fields.pop("payload", None)
        fields.update(dict(updates))
        next_status = str(fields.get("status", row["status"]))
        if (
            str(row["status"]) in _TERMINAL_OPERATION_STATES
            and next_status != str(row["status"])
            and not bool(updates.get("_allow_terminal_reopen", False))
        ):
            raise ProjectAuditError("operation_terminal_conflict")
        fields.pop("_allow_terminal_reopen", None)
        progress = fields.get("progress_percent", row["progress_percent"])
        if isinstance(progress, bool):
            raise ProjectAuditError("operation_progress_invalid")
        try:
            progress_int = int(progress)
        except (TypeError, ValueError) as exc:
            raise ProjectAuditError("operation_progress_invalid") from exc
        if not 0 <= progress_int <= 100:
            raise ProjectAuditError("operation_progress_invalid")
        progress_int = max(int(row["progress_percent"]), progress_int)
        fields["progress_percent"] = progress_int
        fields["updated_at"] = occurred_at
        update_columns = [
            column
            for column in (
                "status", "progress_percent", "current_step", "package_id",
                "source_workspace_fingerprint", "terminal_outcome", "error_code",
                "error_message", "rollback_path", "staging_path", "package_path",
                "maintenance_state", "payload_json", "updated_at",
            )
            if column in fields
        ]
        if not update_columns:
            return
        assignments = ", ".join("%s=?" % column for column in update_columns)
        params = [fields[column] for column in update_columns]
        params.append(operation_id)
        self._hook("operation_projection.before")
        cursor = self._conn.execute(
            "UPDATE backup_operations SET %s WHERE operation_id=?" % assignments,
            tuple(params),
        )
        if cursor.rowcount != 1:
            raise ProjectAuditError("operation_not_found")
        self._hook("operation_projection.after")

    def _prepare_append(
        self,
        canonical_project_id: Optional[str],
        event_kind: Optional[Union[str, ProjectAuditEventKind]],
        payload: Optional[Mapping[str, Any]],
        *,
        project_scope: Optional[str],
        kind: Optional[Union[str, ProjectAuditEventKind]],
        event_id: Optional[Any],
        operation_kind: Optional[Any],
        operation_ref: Optional[Any],
        operation_id: Optional[Any],
        boundary_token: Optional[Any],
        principal_snapshot_hash: Any,
        authorization_decision_hash: Any,
        before_digest: Optional[Any],
        after_digest: Optional[Any],
        domain_anchors: Optional[Mapping[str, Any]],
        result_code: Optional[Any],
        reason_code: Optional[Any],
        occurred_at: Optional[Any],
        expected_head_seq: Optional[Any],
        expected_head_hash: Optional[Any],
        event_fields: Mapping[str, Any],
        operation_update: Optional[Mapping[str, Any]],
        operation_projection: Optional[Mapping[str, Any]],
        operation_patch: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        if canonical_project_id is None:
            canonical_project_id = project_scope
        elif project_scope is not None and canonical_project_id != project_scope:
            raise ProjectAuditError("project_scope_conflict")
        project = _validate_project_id(canonical_project_id)
        if event_kind is None:
            event_kind = kind
        elif kind is not None:
            left_kind = event_kind.value if isinstance(event_kind, ProjectAuditEventKind) else str(event_kind)
            right_kind = kind.value if isinstance(kind, ProjectAuditEventKind) else str(kind)
            if left_kind != right_kind:
                raise ProjectAuditError("event_kind_conflict")
        if isinstance(event_kind, ProjectAuditEventKind):
            event_kind = event_kind.value
        if not isinstance(event_kind, str) or event_kind not in EVENT_KIND_ALLOWLIST:
            raise ProjectAuditError("unknown_event_kind")
        body = _copy_payload(payload)
        body_fields = dict(event_fields)
        # Metadata kwargs are accepted as ergonomic aliases for the required
        # class fields, while the persisted payload remains allowlisted.
        for field_name, field_value in (
            ("operation", operation_ref if operation_ref is not None else operation_id),
            ("boundary_token", boundary_token),
            ("before_digest", before_digest),
            ("after_digest", after_digest),
        ):
            if field_name in EVENT_KIND_ALLOWLIST[event_kind] and field_value is not None:
                body_fields.setdefault(field_name, field_value)
        # A few integrations use ``kind``/``project_scope`` as keyword aliases;
        # they are consumed above and must not become payload extensions.
        body_fields.pop("kind", None)
        body_fields.pop("project_scope", None)
        body = _normalise_aliases(body, body_fields, kind=event_kind)
        body = _validate_payload(event_kind, body)

        event_token = event_id
        if event_token is None:
            event_token = self._event_id_factory()
        if isinstance(event_token, uuid.UUID):
            event_token = event_token.hex
        event_token = _validate_token(event_token, "event_id", required=True)

        if operation_ref is not None and operation_id is not None and operation_ref != operation_id:
            raise ProjectAuditError("operation_reference_conflict")
        op_ref_value = operation_ref if operation_ref is not None else operation_id
        if op_ref_value is None:
            op_ref_value = body.get("operation", "")
        op_ref = _validate_token(op_ref_value, "operation_ref")
        op_kind = _validate_token(
            operation_kind if operation_kind is not None else body.get("operation_kind", ""),
            "operation_kind",
        )
        boundary = _validate_token(
            boundary_token if boundary_token is not None else body.get("boundary_token", ""),
            "boundary_token",
        )
        principal = _validate_token(
            principal_snapshot_hash, "principal_snapshot_hash", required=True
        )
        authorization = _validate_token(
            authorization_decision_hash, "authorization_decision_hash", required=True
        )
        before = _validate_token(
            before_digest if before_digest is not None else body.get("before_digest", ""),
            "before_digest",
        )
        after = _validate_token(
            after_digest if after_digest is not None else body.get("after_digest", ""),
            "after_digest",
        )
        if domain_anchors is None:
            inferred: Dict[str, Any] = {}
            for anchor_name in (
                "r1_anchor", "publication_anchor", "continuity_anchor",
                "exact_domain_anchors", "root_ledger_anchor",
            ):
                if anchor_name in body:
                    inferred[anchor_name] = body[anchor_name]
            domain_anchors = inferred
        if not isinstance(domain_anchors, Mapping):
            raise ProjectAuditError("domain_anchors_must_be_object")
        anchors = _copy_payload(domain_anchors)
        _reject_forbidden_nested_content(anchors)
        result = _validate_enum(
            result_code
            if result_code is not None
            else body.get("result_enum", body.get("result", body.get("outcome", ""))),
            "result_code",
        )
        reason = _validate_enum(
            reason_code
            if reason_code is not None
            else body.get("reason_enum", body.get("reason", "")),
            "reason_code",
        )
        timestamp = _utc_timestamp(occurred_at, self._clock)
        if expected_head_seq is not None:
            if isinstance(expected_head_seq, bool):
                raise ProjectAuditError("invalid_expected_head_seq")
            try:
                expected_head_seq = int(expected_head_seq)
            except (TypeError, ValueError) as exc:
                raise ProjectAuditError("invalid_expected_head_seq") from exc
            if expected_head_seq < 0:
                raise ProjectAuditError("invalid_expected_head_seq")
        if expected_head_hash is not None:
            expected_head_hash = _validate_token(
                expected_head_hash, "expected_head_hash", required=True
            )

        aliases = [
            value
            for value in (operation_update, operation_projection, operation_patch)
            if value is not None
        ]
        merged_update: Optional[Mapping[str, Any]] = None
        if aliases:
            merged = dict(aliases[0]) if isinstance(aliases[0], Mapping) else aliases[0]
            for other in aliases[1:]:
                if not isinstance(other, Mapping) or dict(other) != dict(merged):
                    raise ProjectAuditError("operation_projection_conflict")
            merged_update = merged
        projection_operation_id: Optional[Any] = None
        if merged_update is not None:
            embedded_operation_id = (
                merged_update.get("operation_id")
                if isinstance(merged_update, Mapping)
                else None
            )
            if operation_id is not None:
                projection_operation_id = operation_id
            elif embedded_operation_id is None:
                projection_operation_id = op_ref or None
        resolved_operation_id, normalised_update = self._normalise_operation_update(
            projection_operation_id,
            merged_update,
        )
        payload_json = canonical_json(body)
        anchors_json = canonical_json(anchors)
        return {
            "project_id": project,
            "event_kind": event_kind,
            "payload": body,
            "payload_json": payload_json,
            "operation_kind": op_kind,
            "operation_ref": op_ref,
            "operation_id": resolved_operation_id,
            "boundary_token": boundary,
            "principal_snapshot_hash": principal,
            "authorization_decision_hash": authorization,
            "before_digest": before,
            "after_digest": after,
            "domain_anchors": anchors,
            "domain_anchors_json": anchors_json,
            "result_code": result,
            "reason_code": reason,
            "occurred_at": timestamp,
            "event_id": event_token,
            "expected_head_seq": expected_head_seq,
            "expected_head_hash": expected_head_hash,
            "operation_update": normalised_update,
        }

    def append_event(
        self,
        canonical_project_id: Optional[str] = None,
        event_kind: Optional[Union[str, ProjectAuditEventKind]] = None,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        project_scope: Optional[str] = None,
        kind: Optional[Union[str, ProjectAuditEventKind]] = None,
        event_id: Optional[Any] = None,
        operation_kind: Optional[Any] = None,
        operation_ref: Optional[Any] = None,
        operation_id: Optional[Any] = None,
        boundary_token: Optional[Any] = None,
        principal_snapshot_hash: Any = "",
        authorization_decision_hash: Any = "",
        before_digest: Optional[Any] = None,
        after_digest: Optional[Any] = None,
        domain_anchors: Optional[Mapping[str, Any]] = None,
        result_code: Optional[Any] = None,
        reason_code: Optional[Any] = None,
        occurred_at: Optional[Any] = None,
        expected_head_seq: Optional[Any] = None,
        expected_head_hash: Optional[Any] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
        operation_projection: Optional[Mapping[str, Any]] = None,
        operation_patch: Optional[Mapping[str, Any]] = None,
        **event_fields: Any,
    ) -> ProjectAuditEvent:
        if canonical_project_id is None:
            alias_project = event_fields.pop("project_id", event_fields.pop("scope", None))
            if alias_project is not None:
                canonical_project_id = alias_project
        alias_kind = event_fields.pop("event_class", event_fields.pop("event_type", None))
        if alias_kind is not None:
            if event_kind is None:
                event_kind = alias_kind
            else:
                left_kind = event_kind.value if isinstance(event_kind, ProjectAuditEventKind) else str(event_kind)
                right_kind = alias_kind.value if isinstance(alias_kind, ProjectAuditEventKind) else str(alias_kind)
                if left_kind != right_kind:
                    raise ProjectAuditError("event_kind_conflict")
        alias_payload = event_fields.pop("event_payload", event_fields.pop("fields", None))
        if alias_payload is not None:
            if not isinstance(alias_payload, Mapping):
                raise ProjectAuditError("payload_must_be_object")
            if payload is not None:
                if not isinstance(payload, Mapping) or dict(payload) != dict(alias_payload):
                    raise ProjectAuditError("payload_conflict")
            payload = alias_payload
        prepared = self._prepare_append(
            canonical_project_id,
            event_kind,
            payload,
            project_scope=project_scope,
            kind=kind,
            event_id=event_id,
            operation_kind=operation_kind,
            operation_ref=operation_ref,
            operation_id=operation_id,
            boundary_token=boundary_token,
            principal_snapshot_hash=principal_snapshot_hash,
            authorization_decision_hash=authorization_decision_hash,
            before_digest=before_digest,
            after_digest=after_digest,
            domain_anchors=domain_anchors,
            result_code=result_code,
            reason_code=reason_code,
            occurred_at=occurred_at,
            expected_head_seq=expected_head_seq,
            expected_head_hash=expected_head_hash,
            event_fields=event_fields,
            operation_update=operation_update,
            operation_projection=operation_projection,
            operation_patch=operation_patch,
        )
        with self._lock:
            self._begin()
            try:
                duplicate = self._find_duplicate(
                    project_id=prepared["project_id"],
                    event_id=prepared["event_id"],
                    operation_ref=prepared["operation_ref"],
                    boundary_token=prepared["boundary_token"],
                    event_kind=prepared["event_kind"],
                )
                if duplicate is not None:
                    existing_identity = self._identity_projection(duplicate)
                    candidate_identity = self._candidate_identity(
                        project_id=prepared["project_id"],
                        event_kind=prepared["event_kind"],
                        operation_kind=prepared["operation_kind"],
                        operation_ref=prepared["operation_ref"],
                        boundary_token=prepared["boundary_token"],
                        principal_snapshot_hash=prepared["principal_snapshot_hash"],
                        authorization_decision_hash=prepared["authorization_decision_hash"],
                        before_digest=prepared["before_digest"],
                        after_digest=prepared["after_digest"],
                        domain_anchors_json=prepared["domain_anchors_json"],
                        result_code=prepared["result_code"],
                        reason_code=prepared["reason_code"],
                        occurred_at=prepared["occurred_at"],
                        payload_json=prepared["payload_json"],
                    )
                    boundary_replay = bool(
                        prepared["operation_ref"] and prepared["boundary_token"]
                    )
                    if not self._same_identity(
                        existing_identity, candidate_identity,
                        boundary_replay=boundary_replay,
                    ):
                        raise ProjectAuditError("project_audit_event_conflict")
                    self._conn.execute("COMMIT")
                    return self._event_from_row(duplicate, replayed=True)

                head_seq, head_hash = self._ensure_head(prepared["project_id"])
                if prepared["expected_head_seq"] is not None and (
                    head_seq != prepared["expected_head_seq"]
                ):
                    raise ProjectAuditError("project_audit_head_conflict")
                if prepared["expected_head_hash"] is not None and (
                    head_hash != prepared["expected_head_hash"]
                ):
                    raise ProjectAuditError("project_audit_head_conflict")
                if not self._tail_matches_head(
                    prepared["project_id"], head_seq, head_hash
                ):
                    raise ProjectAuditError("project_audit_tail_mismatch")
                sequence = head_seq + 1
                payload_hash = sha256_hex(prepared["payload_json"].encode("utf-8"))
                body = _hash_body(
                    schema_version=PROJECT_AUDIT_SCHEMA_VERSION,
                    project_id=prepared["project_id"],
                    project_seq=sequence,
                    event_id=prepared["event_id"],
                    event_kind=prepared["event_kind"],
                    operation_kind=prepared["operation_kind"],
                    operation_ref=prepared["operation_ref"],
                    boundary_token=prepared["boundary_token"],
                    principal_snapshot_hash=prepared["principal_snapshot_hash"],
                    authorization_decision_hash=prepared["authorization_decision_hash"],
                    before_digest=prepared["before_digest"],
                    after_digest=prepared["after_digest"],
                    domain_anchors=prepared["domain_anchors"],
                    result_code=prepared["result_code"],
                    reason_code=prepared["reason_code"],
                    occurred_at=prepared["occurred_at"],
                    previous_hash=head_hash,
                    payload_hash=payload_hash,
                )
                chain_hash = sha256_hex(canonical_json_bytes(body))
                self._apply_operation_projection(
                    project_id=prepared["project_id"],
                    operation_id=prepared["operation_id"],
                    updates=prepared["operation_update"],
                    occurred_at=prepared["occurred_at"],
                )
                self._hook("event_insert.before")
                self._conn.execute(
                    "INSERT INTO project_audit_events("
                    "canonical_project_id, project_seq, event_id, schema_version, event_kind,"
                    "operation_kind, operation_ref, boundary_token, principal_snapshot_hash,"
                    "authorization_decision_hash, before_digest, after_digest, domain_anchors_json,"
                    "result_code, reason_code, occurred_at, previous_hash, payload_json, payload_hash,"
                    "chain_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        prepared["project_id"], sequence, prepared["event_id"],
                        PROJECT_AUDIT_SCHEMA_VERSION, prepared["event_kind"],
                        prepared["operation_kind"], prepared["operation_ref"],
                        prepared["boundary_token"], prepared["principal_snapshot_hash"],
                        prepared["authorization_decision_hash"], prepared["before_digest"],
                        prepared["after_digest"], prepared["domain_anchors_json"],
                        prepared["result_code"], prepared["reason_code"],
                        prepared["occurred_at"], head_hash, prepared["payload_json"],
                        payload_hash, chain_hash,
                    ),
                )
                self._hook("event_insert.after")
                self._hook("head_cas.before")
                cursor = self._conn.execute(
                    "UPDATE project_audit_heads SET head_seq=?, head_hash=? "
                    "WHERE canonical_project_id=? AND head_seq=? AND head_hash=?",
                    (
                        sequence, chain_hash, prepared["project_id"], head_seq, head_hash
                    ),
                )
                if cursor.rowcount != 1:
                    raise ProjectAuditError("project_audit_head_conflict")
                self._hook("head_cas.after")
                self._conn.execute("COMMIT")
            except BaseException:
                self._rollback()
                raise
            row = self._conn.execute(
                "SELECT * FROM project_audit_events WHERE canonical_project_id=? AND project_seq=?",
                (prepared["project_id"], sequence),
            ).fetchone()
            if row is None:
                raise ProjectAuditError("project_audit_row_missing")
            return self._event_from_row(row)

    def append_event_with_operation(self, *args: Any, **kwargs: Any) -> ProjectAuditEvent:
        """Append an event and update the root operation projection atomically."""
        return self.append_event(*args, **kwargs)

    append_with_operation = append_event_with_operation
    append_operation_event = append_event_with_operation
    append_audit_event = append_event
    append_project_event = append_event
    append = append_event
    record_event = append_event
    append_event_and_update_operation = append_event_with_operation
    append_event_with_operation_projection = append_event_with_operation
    append_with_operation_projection = append_event_with_operation

    def _events_for_project(self, project_id: str) -> List[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM project_audit_events WHERE canonical_project_id=? ORDER BY project_seq",
            (project_id,),
        ).fetchall()

    def events(
        self,
        canonical_project_id: Optional[str] = None,
        *,
        limit: Optional[int] = None,
    ) -> Tuple[ProjectAuditEvent, ...]:
        project = _validate_project_id(canonical_project_id) if canonical_project_id is not None else None
        with self._lock:
            if project is None:
                sql = "SELECT * FROM project_audit_events ORDER BY canonical_project_id, project_seq"
                params: Sequence[Any] = ()
            else:
                sql = "SELECT * FROM project_audit_events WHERE canonical_project_id=? ORDER BY project_seq"
                params = (project,)
            if limit is not None:
                if isinstance(limit, bool) or int(limit) < 0:
                    raise ProjectAuditError("invalid_event_limit")
                sql += " LIMIT ?"
                params = tuple(params) + (int(limit),)
            rows = self._conn.execute(sql, tuple(params)).fetchall()
            return tuple(self._event_from_row(row) for row in rows)

    audit_trail = events
    list_events = events
    events_for_project = events
    project_events = events
    audit_events = events

    def _verify_one(self, project_id: str) -> Tuple[bool, Optional[int], int]:
        rows = self._events_for_project(project_id)
        head = self._head_row(project_id)
        if head is None:
            return False, 1 if rows else 1, len(rows)
        expected_previous = PROJECT_AUDIT_GENESIS
        for index, row in enumerate(rows, start=1):
            try:
                sequence = int(row["project_seq"])
                if sequence != index:
                    return False, sequence, len(rows)
                if str(row["schema_version"]) != PROJECT_AUDIT_SCHEMA_VERSION:
                    return False, sequence, len(rows)
                if str(row["previous_hash"]) != expected_previous:
                    return False, sequence, len(rows)
                payload_json = str(row["payload_json"])
                payload = json.loads(payload_json)
                if not isinstance(payload, dict) or canonical_json(payload) != payload_json:
                    return False, sequence, len(rows)
                event_kind = str(row["event_kind"])
                if event_kind not in EVENT_KIND_ALLOWLIST:
                    return False, sequence, len(rows)
                try:
                    _validate_payload(event_kind, payload)
                    canonical_anchors = canonical_json(json.loads(str(row["domain_anchors_json"])))
                except (ProjectAuditError, TypeError, ValueError, json.JSONDecodeError):
                    return False, sequence, len(rows)
                if canonical_anchors != str(row["domain_anchors_json"]):
                    return False, sequence, len(rows)
                if not str(row["principal_snapshot_hash"]) or not str(row["authorization_decision_hash"]):
                    return False, sequence, len(rows)
                if _utc_timestamp(str(row["occurred_at"]), lambda: None) != str(row["occurred_at"]):
                    return False, sequence, len(rows)
                payload_hash = sha256_hex(payload_json.encode("utf-8"))
                if payload_hash != str(row["payload_hash"]):
                    return False, sequence, len(rows)
                body = _hash_body(
                    schema_version=str(row["schema_version"]),
                    project_id=str(row["canonical_project_id"]),
                    project_seq=sequence,
                    event_id=str(row["event_id"]),
                    event_kind=event_kind,
                    operation_kind=str(row["operation_kind"]),
                    operation_ref=str(row["operation_ref"]),
                    boundary_token=str(row["boundary_token"]),
                    principal_snapshot_hash=str(row["principal_snapshot_hash"]),
                    authorization_decision_hash=str(row["authorization_decision_hash"]),
                    before_digest=str(row["before_digest"]),
                    after_digest=str(row["after_digest"]),
                    domain_anchors=json.loads(str(row["domain_anchors_json"])),
                    result_code=str(row["result_code"]),
                    reason_code=str(row["reason_code"]),
                    occurred_at=str(row["occurred_at"]),
                    previous_hash=str(row["previous_hash"]),
                    payload_hash=payload_hash,
                )
                if sha256_hex(canonical_json_bytes(body)) != str(row["chain_hash"]):
                    return False, sequence, len(rows)
                expected_previous = str(row["chain_hash"])
            except (KeyError, TypeError, ValueError, sqlite3.Error):
                return False, index, len(rows)
        expected_seq = int(head["head_seq"])
        expected_hash = str(head["head_hash"])
        if expected_seq != len(rows) or expected_hash != expected_previous:
            return False, min(len(rows) + 1, max(1, expected_seq)), len(rows)
        return True, None, len(rows)

    def verify_chain(
        self,
        canonical_project_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[int], int]:
        """Recompute payload/event hashes and the per-project CAS head.

        The return shape intentionally matches the established R1 verifier:
        ``(ok, first_bad_sequence, event_count)``.  With no project argument,
        every project chain is checked and the count is the total event count.
        """
        project = _validate_project_id(canonical_project_id) if canonical_project_id is not None else None
        with self._lock:
            if project is not None:
                return self._verify_one(project)
            project_rows = self._conn.execute(
                "SELECT canonical_project_id FROM project_audit_heads "
                "UNION SELECT canonical_project_id FROM project_audit_events "
                "ORDER BY canonical_project_id"
            ).fetchall()
            total = 0
            for row in project_rows:
                ok, bad, count = self._verify_one(str(row[0]))
                total += count
                if not ok:
                    return False, bad, total
            return True, None, total

    verify_audit_chain = verify_chain
    verify_project_chain = verify_chain

    def verify(self, canonical_project_id: Optional[str] = None) -> bool:
        return self.verify_chain(canonical_project_id)[0]

    def verify_all_chains(self) -> Mapping[str, Tuple[bool, Optional[int], int]]:
        with self._lock:
            projects = {
                str(row[0])
                for row in self._conn.execute(
                    "SELECT canonical_project_id FROM project_audit_heads "
                    "UNION SELECT canonical_project_id FROM project_audit_events"
                ).fetchall()
            }
            return {project: self._verify_one(project) for project in sorted(projects)}

    def operation_projection(self, operation_id: str) -> Mapping[str, Any]:
        op = _validate_token(operation_id, "operation_id", required=True)
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM backup_operations WHERE operation_id=?", (op,)
            ).fetchone()
            if row is None:
                raise ProjectAuditError("operation_not_found")
            result = {str(key): row[key] for key in row.keys()}
            try:
                result["payload"] = json.loads(str(result.get("payload_json", "{}")))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ProjectAuditError("operation_projection_corrupt") from exc
            return result

    get_operation_projection = operation_projection


__all__ = [
    "OPERATIONS_DB_NAME",
    "PROJECT_AUDIT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "PROJECT_AUDIT_GENESIS",
    "AUDIT_GENESIS",
    "ProjectAuditEventKind",
    "EVENT_KIND_ALLOWLIST",
    "EVENT_REQUIRED_FIELDS",
    "EVENT_OPTIONAL_FIELDS",
    "PROJECT_AUDIT_EVENT_ALLOWLIST",
    "PROJECT_AUDIT_REQUIRED_FIELDS",
    "PROJECT_AUDIT_EVENT_KINDS",
    "EVENT_KINDS",
    "PAYLOAD_ALLOWLIST",
    "REQUIRED_FIELDS_BY_KIND",
    "PROJECT_AUDIT_DDL",
    "ProjectAuditError",
    "AuditLedgerError",
    "ProjectAuditLedgerError",
    "ProjectAuditHead",
    "ProjectAuditEvent",
    "ProjectAuditLedger",
    "canonical_json_bytes",
    "canonical_json",
    "canonical_digest",
    "content_digest",
    "sha256_hex",
]
