"""Read-only R7 project verification and recovery-boundary coordination.

The verifier is deliberately small at the product boundary: it reads the
project members in the frozen source-to-run-to-publication-to-continuity order,
reuses the public R1 audit-chain method, and records only its own verification
pair in the root :class:`ProjectAuditLedger`.  Recovery coordination delegates
copy/rename/rollback work to the accepted 09A/09B runners; it never implements a
second migration or backup protocol.
"""

from __future__ import annotations

import hashlib
import inspect as _inspect
import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence
from urllib.parse import quote

from ..graph.store import Store

from . import migration as _migration
from . import project_backup as _backup
from .project_audit import (
    PROJECT_AUDIT_SCHEMA_VERSION,
    ProjectAuditError,
    ProjectAuditEvent,
    ProjectAuditEventKind,
    ProjectAuditLedger,
)
from .schema_manifest import (
    BINDING_DB_RELATIVE_PATH,
    BINDING_MEMBER,
    EXECUTION_CONTROL_MEMBER,
    LAUNCH_DB_RELATIVE_PATH,
    LAUNCH_MEMBER,
    MEMBER_ORDER,
    PROFILE_DB_RELATIVE_PATH,
    PROFILE_MEMBER,
    RISK_DB_RELATIVE_PATH,
    RISK_MEMBER,
    RUNTIME_DB_RELATIVE_PATH,
    RUNTIME_MEMBER,
    SchemaClassification,
    inspect_project_schema,
)


VERIFIER_VERSION = "mm-r7-slice09c-project-verifier-v1"
AUDIT_SCHEMA_VERSION = PROJECT_AUDIT_SCHEMA_VERSION

# Public result labels are intentionally the exact frozen Chinese outcomes.
RESULT_RECORD_COMPLETE = "记录完整"
RESULT_ANOMALY = "发现异常"
RESULT_RECOVERY_REQUIRED = "需重新恢复"

# Internal audit result codes are not emitted by the synchronous DTO.
_RESULT_CODE_COMPLETE = "record_complete"
_RESULT_CODE_ANOMALY = "anomaly"
_RESULT_CODE_RECOVERY = "recovery_required"

_DEFAULT_MESSAGE = {
    RESULT_RECORD_COMPLETE: "项目审计记录已核验完整。",
    RESULT_ANOMALY: "项目审计记录存在异常，请保留原项目并联系支持。",
    RESULT_RECOVERY_REQUIRED: "项目存在未完成恢复证据，请先完成恢复。",
}
_DEFAULT_NEXT_ACTION = {
    RESULT_RECORD_COMPLETE: "可继续查看项目",
    RESULT_ANOMALY: "保留原项目并联系支持",
    RESULT_RECOVERY_REQUIRED: "完成恢复后重试",
}

_SAFE_PROJECT = re.compile(r"^[^/\\\x00-\x1f\x7f]{1,512}$")
_SAFE_TOKEN = re.compile(r"^[^/\\\x00-\x1f\x7f]{1,512}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The source/workspace members are fixed by the schema manifest.  The verifier
# also observes these sibling evidence directories but never follows them.
_EVIDENCE_DIRS = (
    ".migration-staging",
    ".migration-rollback",
    ".mmbackup-staging",
)
_ROLLBACK_EVIDENCE_PREFIX = ".rollback-"
_FINGERPRINT_ROOTS = (
    "runtime",
    "artifacts",
    ".migration-staging",
    ".migration-rollback",
    ".mmbackup-staging",
)
_FIXED_MEMBER_FILES = (
    PROFILE_DB_RELATIVE_PATH,
    BINDING_DB_RELATIVE_PATH,
    LAUNCH_DB_RELATIVE_PATH,
    RISK_DB_RELATIVE_PATH,
    RUNTIME_DB_RELATIVE_PATH,
)

# 09A/09B public recovery states.  ``retryable_failed`` and
# ``retained_for_triage`` are deliberately never auto-recovered here.
_MIGRATION_RECOVERY_STATES = frozenset(
    str(value) for value in getattr(_migration, "PUBLIC_RECOVERY_STATES", ())
)
_MIGRATION_RETAINED_STATE = str(
    getattr(_migration, "STATUS_RETAINED_FOR_TRIAGE", "retained_for_triage")
)
_MIGRATION_RETRYABLE_STATE = str(
    getattr(_migration, "STATUS_RETRYABLE_FAILED", "retryable_failed")
)
_BACKUP_RECOVERY_STATES = frozenset(
    {
        str(getattr(_backup, "STATUS_STAGING", "staging")),
        str(getattr(_backup, "STATUS_VERIFYING_STAGED_WORKSPACE", "verifying_staged_workspace")),
        str(getattr(_backup, "STATUS_QUIESCING_PROJECT", "quiescing_project")),
        str(getattr(_backup, "STATUS_SWITCHING", "switching")),
        str(getattr(_backup, "STATUS_VERIFYING_LIVE_WORKSPACE", "verifying_live_workspace")),
        str(getattr(_backup, "STATUS_ROLLBACK_IN_PROGRESS", "rollback_in_progress")),
    }
)
_BACKUP_RETAINED_STATE = str(
    getattr(_backup, "STATUS_RETAINED_FOR_TRIAGE", "retained_for_triage")
)


class ProjectVerificationError(RuntimeError):
    """Stable internal error; product routes map it to a safe Chinese DTO."""

    def __init__(self, code: str = "project_verification_failed") -> None:
        self.code = str(code)
        super().__init__(self.code)


class RecoveryCoordinationError(RuntimeError):
    """Raised when an accepted 09A/09B recovery cannot be safely continued."""

    def __init__(self, code: str = "recovery_coordination_failed") -> None:
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class ProjectVerificationDTO:
    """Minimal Chinese product DTO; no handles, IDs, paths, or diagnostics."""

    result: str
    message: str
    next_action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "result": self.result,
            "message": self.message,
            "nextAction": self.next_action,
        }

    to_dict = as_dict

    def model_dump(self, *, exclude_none: bool = True, **_: Any) -> dict[str, str]:
        return self.as_dict()


@dataclass(frozen=True)
class ProjectVerificationResult:
    """Internal verifier result with private anchors for boundary wiring."""

    result: str
    message: str
    next_action: str
    snapshot_fingerprint: str
    before_digest: str
    after_digest: str
    reason_enum: str
    domain_anchors: Mapping[str, str] = field(default_factory=dict)
    started_event_id: Optional[str] = None
    completed_event_id: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        return self.result == RESULT_RECORD_COMPLETE

    def as_public_dict(self) -> dict[str, str]:
        return ProjectVerificationDTO(
            self.result,
            self.message,
            self.next_action,
        ).as_dict()

    def as_dto(self) -> ProjectVerificationDTO:
        return ProjectVerificationDTO(
            self.result,
            self.message,
            self.next_action,
        )

    # The product router historically asks result objects for a dict.
    as_dict = as_public_dict
    to_dict = as_public_dict


@dataclass(frozen=True)
class BoundaryReceipt:
    """Opaque internal receipt for one 09A/09B boundary sequence."""

    operation_id: str
    operation_kind: str
    boundary_token: str
    expected_state: str
    before_digest: str
    principal_snapshot_hash: str
    authorization_decision_hash: str
    intent_event_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "operation_id": self.operation_id,
            "operation_kind": self.operation_kind,
            "boundary_token": self.boundary_token,
            "expected_state": self.expected_state,
            "before_digest": self.before_digest,
            "principal_snapshot_hash": self.principal_snapshot_hash,
            "authorization_decision_hash": self.authorization_decision_hash,
            "intent_event_id": self.intent_event_id,
        }

    to_dict = as_dict


@dataclass(frozen=True)
class _WorkspaceSnapshot:
    fingerprint: str
    inspection: Any
    issues: tuple[str, ...] = ()


class _VerificationIssues:
    """Internal severity accumulator with stable, non-sensitive reason enums."""

    def __init__(self) -> None:
        self.anomalies: list[str] = []
        self.recoveries: list[str] = []
        self.anchors: dict[str, str] = {}

    def anomaly(self, reason: str) -> None:
        value = _safe_reason(reason, "audit_anomaly")
        if value not in self.anomalies:
            self.anomalies.append(value)

    def recovery(self, reason: str) -> None:
        value = _safe_reason(reason, "recovery_required")
        if value not in self.recoveries:
            self.recoveries.append(value)

    def anchor(self, name: str, value: Any) -> None:
        self.anchors[name] = _digest(value)

    @property
    def result(self) -> str:
        if self.anomalies:
            return RESULT_ANOMALY
        if self.recoveries:
            return RESULT_RECOVERY_REQUIRED
        return RESULT_RECORD_COMPLETE

    @property
    def reason_enum(self) -> str:
        if self.anomalies:
            return self.anomalies[0]
        if self.recoveries:
            return self.recoveries[0]
        return _RESULT_CODE_COMPLETE


# ---------------------------------------------------------------------------
# Canonical and filesystem helpers


def _safe_reason(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or re.fullmatch(r"[^/\\\x00-\x1f\x7f\s]{1,128}", text) is None:
        return fallback
    return text


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, bytes):
        return {"byte_count": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return str(value)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _normalise_project_id(value: Any) -> str:
    text = str(value or "")
    if (
        not text
        or text != text.strip()
        or _SAFE_PROJECT.fullmatch(text) is None
        or text in {".", ".."}
    ):
        raise ValueError("invalid_project_id")
    return text


def _opaque_reference(value: Any, *, prefix: str = "ref") -> str:
    text = str(value or "")
    if text and text == text.strip() and _SAFE_TOKEN.fullmatch(text) is not None:
        return text
    return "%s-%s" % (prefix, hashlib.sha256(text.encode("utf-8")).hexdigest())


def _normalise_hash(value: Any, seed: str) -> str:
    text = str(value or "")
    if _HEX64.fullmatch(text):
        return text
    return hashlib.sha256((seed + "\0" + text).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def _sqlite_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    return value


def _sqlite_logical_digest(path: Path) -> tuple[str, int]:
    """Hash SQLite schema and rows, not page layout or WAL/SHM sidecars."""

    connection = _readonly_connection(path)
    try:
        objects = connection.execute(
            "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        logical: dict[str, Any] = {
            "schema": [list(row) for row in objects],
            "tables": {},
        }
        table_names = sorted(
            str(row[1]) for row in objects if str(row[0]) == "table"
        )
        for table in table_names:
            quoted = '"' + table.replace('"', '""') + '"'
            columns = [
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({quoted})").fetchall()
            ]
            order = ", ".join(
                '"' + column.replace('"', '""') + '"' for column in columns
            )
            rows = connection.execute(
                f"SELECT * FROM {quoted}" + (f" ORDER BY {order}" if order else "")
            ).fetchall()
            values = [
                [_sqlite_value(value) for value in row]
                for row in rows
                if not (
                    table == "meta"
                    and columns
                    and str(row[0]) == "store_id"
                )
            ]
            logical["tables"][table] = {"columns": columns, "rows": values}
        encoded = json.dumps(
            logical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest(), len(encoded)
    finally:
        connection.close()


def _walk_digest_roots(workspace: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    issues: list[str] = []
    if workspace.is_symlink():
        return [], ["workspace_symlink"]
    for relative in _FIXED_MEMBER_FILES:
        path = workspace / relative
        if path.is_symlink():
            issues.append("member_symlink")
            continue
        if path.is_file():
            try:
                file_hash, size = _sqlite_logical_digest(path)
            except (OSError, ValueError):
                issues.append("member_unreadable")
                continue
            records.append({"relative": relative, "sha256": file_hash, "size": size})
    for root_name in _FINGERPRINT_ROOTS:
        base = workspace / root_name
        if not base.exists():
            continue
        if base.is_symlink():
            issues.append("evidence_symlink")
            continue
        if not base.is_dir():
            issues.append("evidence_not_directory")
            continue
        for current, directories, files in os.walk(base, topdown=True, followlinks=False):
            current_path = Path(current)
            kept_dirs: list[str] = []
            for name in sorted(directories):
                child = current_path / name
                if child.is_symlink():
                    issues.append("evidence_symlink")
                else:
                    kept_dirs.append(name)
            directories[:] = kept_dirs
            for name in sorted(files):
                child = current_path / name
                relative = child.relative_to(workspace).as_posix()
                if relative in _FIXED_MEMBER_FILES or any(
                    relative == fixed + suffix
                    for fixed in _FIXED_MEMBER_FILES
                    for suffix in ("-wal", "-shm")
                ):
                    continue
                if child.is_symlink():
                    issues.append("evidence_symlink")
                    continue
                if not child.is_file():
                    issues.append("evidence_unreadable")
                    continue
                try:
                    file_hash, size = _file_digest(child)
                except (OSError, ValueError):
                    issues.append("evidence_unreadable")
                    continue
                records.append({"relative": relative, "sha256": file_hash, "size": size})
    records.sort(key=lambda item: str(item["relative"]))
    return records, sorted(set(issues))


def _readonly_connection(path: Path) -> sqlite3.Connection:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(str(path))
    resolved = path.resolve()
    uri = "file:%s?mode=ro" % quote(str(resolved), safe="/")
    connection = sqlite3.connect(
        uri,
        uri=True,
        isolation_level=None,
        timeout=5.0,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute("PRAGMA query_only=ON")
    return connection


def _quick_check(connection: sqlite3.Connection) -> tuple[str, int]:
    row = connection.execute("PRAGMA quick_check").fetchone()
    quick = str(row[0]) if row is not None else ""
    violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    return quick, violations


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(%s)" % table).fetchall()
    }


def _read_rows(
    connection: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
) -> list[dict[str, Any]]:
    if not _table_exists(connection, table):
        return []
    available = _table_columns(connection, table)
    selected = [column for column in columns if column in available]
    if not selected:
        return []
    projection = ", ".join('"%s"' % column.replace('"', '""') for column in selected)
    rows = connection.execute(
        "SELECT %s FROM \"%s\"" % (projection, table.replace('"', '""'))
    ).fetchall()
    return [dict(row) for row in rows]


def _json_value(value: Any, *, default: Any) -> Any:
    if value is None or value == "":
        return default
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("json_not_canonical")
    return decoded


def _event_mapping(event: Any) -> dict[str, Any]:
    if isinstance(event, Mapping):
        return dict(event)
    if hasattr(event, "as_dict"):
        try:
            value = event.as_dict()
            if isinstance(value, Mapping):
                return dict(value)
        except Exception:
            pass
    result: dict[str, Any] = {}
    for name in (
        "canonical_project_id",
        "project_scope",
        "project_seq",
        "sequence",
        "head_seq",
        "event_id",
        "event_kind",
        "event_class",
        "kind",
        "operation_ref",
        "operation_id",
        "boundary_token",
        "payload",
        "domain_anchors",
        "chain_hash",
        "head_hash",
    ):
        if hasattr(event, name):
            result[name] = getattr(event, name)
    return result


def _event_id(event: Any) -> str:
    value = _event_mapping(event).get("event_id")
    return str(value or "")


def _event_kind(event: Any) -> str:
    data = _event_mapping(event)
    return str(data.get("event_kind", data.get("event_class", data.get("kind", ""))) or "")


def _event_operation(event: Any) -> str:
    data = _event_mapping(event)
    return str(data.get("operation_ref", data.get("operation_id", "")) or "")


# ---------------------------------------------------------------------------
# Audit ledger adapter


def _call_factory(factory: Callable[..., Any], root: Path, project_id: str) -> Any:
    """Call an injected ledger factory without speculative duplicate calls."""

    try:
        signature = _inspect.signature(factory)
        parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (_inspect.Parameter.POSITIONAL_ONLY, _inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
    except (TypeError, ValueError):
        return factory(root)
    required = [parameter for parameter in parameters if parameter.default is _inspect.Parameter.empty]
    if not parameters:
        return factory()
    if len(required) <= 1:
        return factory(root)
    return factory(root, project_id)


def _new_audit_ledger(
    root: Path,
    project_id: str,
    factory: Optional[Callable[..., Any]],
) -> Any:
    if factory is not None:
        ledger = _call_factory(factory, root, project_id)
    else:
        ledger = ProjectAuditLedger(root)
    if ledger is None:
        raise ProjectVerificationError("audit_ledger_unavailable")
    return ledger


class ProjectAuditBridge:
    """Project-bound explicit event bridge; no scope-switching append API."""

    def __init__(
        self,
        ledger: Any,
        canonical_project_id: str,
        *,
        principal_snapshot_hash: str = "",
        authorization_decision_hash: str = "",
    ) -> None:
        self.ledger = ledger
        self.canonical_project_id = _normalise_project_id(canonical_project_id)
        self.principal_snapshot_hash = _normalise_hash(
            principal_snapshot_hash, "synthetic-principal"
        )
        self.authorization_decision_hash = _normalise_hash(
            authorization_decision_hash, "synthetic-authorization"
        )

    def _append(
        self,
        event_kind: str,
        *,
        operation_kind: str = "",
        operation_ref: str = "",
        boundary_token: str = "",
        before_digest: str = "",
        after_digest: str = "",
        domain_anchors: Optional[Mapping[str, Any]] = None,
        result_code: str = "",
        reason_code: str = "",
        operation_update: Optional[Mapping[str, Any]] = None,
        **event_fields: Any,
    ) -> Any:
        # Metadata aliases below are also required payload fields for boundary
        # events; the ledger infers them from the explicit metadata arguments.
        # Remove them from the keyword payload to avoid duplicate Python
        # keywords while preserving the allowlisted persisted fields.
        event_fields.pop("boundary_token", None)
        event_fields.pop("before_digest", None)
        event_fields.pop("after_digest", None)
        # ``append_event`` is the sole ledger mutation seam.  Event-specific
        # fields are passed as explicit keywords, never wrapped in a free map.
        append = getattr(self.ledger, "append_event", None)
        if not callable(append):
            raise ProjectVerificationError("audit_append_unavailable")
        try:
            return append(
                self.canonical_project_id,
                event_kind,
                principal_snapshot_hash=self.principal_snapshot_hash,
                authorization_decision_hash=self.authorization_decision_hash,
                operation_kind=_opaque_reference(operation_kind, prefix="kind")
                if operation_kind
                else "",
                operation_ref=_opaque_reference(operation_ref, prefix="operation")
                if operation_ref
                else "",
                boundary_token=_opaque_reference(boundary_token, prefix="boundary")
                if boundary_token
                else "",
                before_digest=str(before_digest or ""),
                after_digest=str(after_digest or ""),
                domain_anchors=dict(domain_anchors or {}),
                result_code=str(result_code or event_kind),
                reason_code=str(reason_code or event_kind),
                operation_update=operation_update,
                **event_fields,
            )
        except (ProjectAuditError, sqlite3.Error, OSError, TypeError, ValueError) as exc:
            code = getattr(exc, "code", "audit_append_failed")
            raise ProjectVerificationError(_safe_reason(code, "audit_append_failed")) from exc

    def boundary_intent(
        self,
        operation: str,
        *,
        operation_kind: str,
        boundary_token: str,
        expected_state: str,
        before_digest: str,
        package_digest: Optional[str] = None,
        source_digest: Optional[str] = None,
        plan_digest: Optional[str] = None,
        slot_presence: Optional[Mapping[str, Any]] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "expected_state": _safe_reason(expected_state, "unknown_state"),
        }
        # boundary_token and before_digest are inferred by the ledger from
        # the explicit metadata arguments below.
        for name, value in (
            ("package_digest", package_digest),
            ("source_digest", source_digest),
            ("plan_digest", plan_digest),
            ("slot_presence", dict(slot_presence) if slot_presence is not None else None),
        ):
            if value is not None:
                fields[name] = value
        return self._append(
            ProjectAuditEventKind.BOUNDARY_INTENT.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            boundary_token=boundary_token,
            before_digest=before_digest,
            after_digest=before_digest,
            result_code="boundary_intent",
            reason_code="boundary_intent",
            operation_update=operation_update,
            **fields,
        )

    def boundary_committed(
        self,
        operation: str,
        *,
        operation_kind: str,
        boundary_token: str,
        observed_durable_phase: str,
        after_digest: str,
        marker_digest: Optional[str] = None,
        member_digest: Optional[str] = None,
        workspace_digest: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "observed_durable_phase": _safe_reason(observed_durable_phase, "unknown_state"),
        }
        # boundary_token and after_digest are inferred by the ledger.
        for name, value in (
            ("marker_digest", marker_digest),
            ("member_digest", member_digest),
            ("workspace_digest", workspace_digest),
        ):
            if value is not None:
                fields[name] = value
        return self._append(
            ProjectAuditEventKind.BOUNDARY_COMMITTED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            boundary_token=boundary_token,
            before_digest=after_digest,
            after_digest=after_digest,
            result_code="boundary_committed",
            reason_code="boundary_committed",
            operation_update=operation_update,
            **fields,
        )

    def boundary_verified(
        self,
        operation: str,
        *,
        operation_kind: str,
        boundary_token: str,
        verifier_outcome: str,
        after_digest: str,
        r1_anchor: Optional[str] = None,
        publication_anchor: Optional[str] = None,
        continuity_anchor: Optional[str] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "verifier_outcome": str(verifier_outcome or RESULT_RECOVERY_REQUIRED),
        }
        # boundary_token and after_digest are inferred by the ledger.
        anchors: dict[str, Any] = {}
        for name, value in (
            ("r1_anchor", r1_anchor),
            ("publication_anchor", publication_anchor),
            ("continuity_anchor", continuity_anchor),
        ):
            if value is not None:
                fields[name] = value
                anchors[name] = value
        return self._append(
            ProjectAuditEventKind.BOUNDARY_VERIFIED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            boundary_token=boundary_token,
            before_digest=after_digest,
            after_digest=after_digest,
            domain_anchors=anchors,
            result_code=_result_code(verifier_outcome),
            reason_code="boundary_verified",
            **fields,
        )

    def recovery_classified(
        self,
        operation: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        classification: str,
        slot_anchor: Optional[str] = None,
        marker_anchor: Optional[str] = None,
        root_ledger_anchor: Optional[str] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "observed_durable_phase": _safe_reason(observed_durable_phase, "unknown_state"),
            "classification": str(classification or RESULT_RECOVERY_REQUIRED),
        }
        anchors: dict[str, Any] = {}
        for name, value in (
            ("slot_anchor", slot_anchor),
            ("marker_anchor", marker_anchor),
            ("root_ledger_anchor", root_ledger_anchor),
        ):
            if value is not None:
                fields[name] = value
                anchors[name] = value
        return self._append(
            ProjectAuditEventKind.RECOVERY_CLASSIFIED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            result_code=_result_code(classification),
            reason_code="recovery_classified",
            domain_anchors=anchors,
            **fields,
        )

    def recovery_completed(
        self,
        operation: str,
        *,
        operation_kind: str,
        terminal_outcome: str,
        after_digest: str,
        exact_domain_anchors: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        anchors = dict(exact_domain_anchors or {})
        return self._append(
            ProjectAuditEventKind.RECOVERY_COMPLETED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            before_digest=after_digest,
            after_digest=after_digest,
            domain_anchors=anchors,
            result_code=_result_code(terminal_outcome),
            reason_code="recovery_completed",
            operation= _opaque_reference(operation, prefix="operation"),
            terminal_outcome=_safe_reason(terminal_outcome, "recovery_required"),
            exact_domain_anchors=anchors,
        )

    def triage_retained(
        self,
        operation: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        reason_enum: str,
        slot_anchor: Optional[str] = None,
        marker_anchor: Optional[str] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "observed_durable_phase": _safe_reason(observed_durable_phase, "unknown_state"),
            "reason_enum": _safe_reason(reason_enum, "triage_retained"),
        }
        for name, value in (("slot_anchor", slot_anchor), ("marker_anchor", marker_anchor)):
            if value is not None:
                fields[name] = value
        return self._append(
            ProjectAuditEventKind.TRIAGE_RETAINED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            result_code="triage_retained",
            reason_code="triage_retained",
            **fields,
        )

    def rollback_release_intent(
        self,
        operation: str,
        *,
        operation_kind: str,
        verified_event_id: str,
        rollback_digest: str,
    ) -> Any:
        return self._append(
            ProjectAuditEventKind.ROLLBACK_RELEASE_INTENT.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            before_digest=rollback_digest,
            after_digest=rollback_digest,
            result_code="rollback_release_intent",
            reason_code="rollback_release_intent",
            operation=_opaque_reference(operation, prefix="operation"),
            verified_event_id=_opaque_reference(verified_event_id, prefix="event"),
            rollback_digest=str(rollback_digest or ""),
        )

    def rollback_evidence_released(
        self,
        operation: str,
        *,
        operation_kind: str,
        release_intent_id: str,
        outcome: str = "released",
        diagnostic_enum: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        fields: dict[str, Any] = {
            "operation": _opaque_reference(operation, prefix="operation"),
            "release_intent_id": _opaque_reference(release_intent_id, prefix="event"),
            "outcome": _safe_reason(outcome, "released"),
        }
        if diagnostic_enum is not None:
            fields["diagnostic_enum"] = _safe_reason(diagnostic_enum, "release_failed")
        return self._append(
            ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            result_code="rollback_evidence_released",
            reason_code="rollback_evidence_released",
            operation_update=operation_update,
            **fields,
        )

    def rollback_evidence_release_failed(
        self,
        operation: str,
        *,
        operation_kind: str,
        release_intent_id: str,
        outcome: str = "release_failed",
        diagnostic_enum: str = "release_failed",
    ) -> Any:
        return self._append(
            ProjectAuditEventKind.ROLLBACK_EVIDENCE_RELEASE_FAILED.value,
            operation_kind=operation_kind,
            operation_ref=operation,
            result_code="rollback_evidence_release_failed",
            reason_code="rollback_evidence_release_failed",
            operation=_opaque_reference(operation, prefix="operation"),
            release_intent_id=_opaque_reference(release_intent_id, prefix="event"),
            outcome=_safe_reason(outcome, "release_failed"),
            diagnostic_enum=_safe_reason(diagnostic_enum, "release_failed"),
        )


def _result_code(result: str) -> str:
    if result == RESULT_RECORD_COMPLETE:
        return _RESULT_CODE_COMPLETE
    if result == RESULT_ANOMALY:
        return _RESULT_CODE_ANOMALY
    if result == RESULT_RECOVERY_REQUIRED:
        return _RESULT_CODE_RECOVERY
    return _safe_reason(result, _RESULT_CODE_RECOVERY)


# ---------------------------------------------------------------------------
# Project verifier


class ProjectVerifier:
    """Fixed-order, read-only project verifier with own root event pair."""

    def __init__(
        self,
        runtime_root: str | Path,
        canonical_project_id: str,
        *,
        project_dir: Optional[str | Path] = None,
        audit_ledger_factory: Optional[Callable[..., Any]] = None,
        audit_ledger: Any = None,
        principal_snapshot_hash: str = "",
        authorization_decision_hash: str = "",
        requested_domain_set: Optional[Sequence[str]] = None,
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _normalise_project_id(canonical_project_id)
        self.project_dir = Path(project_dir) if project_dir is not None else (
            self.runtime_root / self.canonical_project_id
        )
        self.audit_ledger_factory = audit_ledger_factory
        self._ledger = audit_ledger
        self._owns_ledger = audit_ledger is None
        self._principal_snapshot_hash = _normalise_hash(
            principal_snapshot_hash, "synthetic-principal"
        )
        self._authorization_decision_hash = _normalise_hash(
            authorization_decision_hash, "synthetic-authorization"
        )
        domains = tuple(requested_domain_set or (
            "root",
            "identity",
            "operation",
            "live",
            "r1",
            "publication",
            "continuity",
            "verification",
        ))
        self.requested_domain_set = tuple(
            _safe_reason(domain, "domain") for domain in domains
        )

    def _get_ledger(self) -> Any:
        if self._ledger is None:
            self._ledger = _new_audit_ledger(
                self.runtime_root,
                self.canonical_project_id,
                self.audit_ledger_factory,
            )
        return self._ledger

    def _bridge(self) -> ProjectAuditBridge:
        return ProjectAuditBridge(
            self._get_ledger(),
            self.canonical_project_id,
            principal_snapshot_hash=self._principal_snapshot_hash,
            authorization_decision_hash=self._authorization_decision_hash,
        )

    def close(self) -> None:
        ledger = self._ledger
        self._ledger = None
        if ledger is not None and self._owns_ledger:
            close = getattr(ledger, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "ProjectVerifier":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _snapshot(self) -> _WorkspaceSnapshot:
        issues: list[str] = []
        try:
            inspection = inspect_project_schema(self.project_dir)
        except Exception:
            inspection = None
            issues.append("schema_inspection_failed")
        try:
            files, file_issues = _walk_digest_roots(self.project_dir)
            issues.extend(file_issues)
        except (OSError, ValueError):
            files = []
            issues.append("workspace_unreadable")
        members: list[dict[str, Any]] = []
        if inspection is not None:
            for name in MEMBER_ORDER:
                report = inspection.members.get(name)
                if report is None:
                    members.append({"member": name, "present": False})
                    continue
                members.append(
                    {
                        "member": name,
                        "classification": str(report.classification.value),
                        "schema_version": report.schema_version,
                        "reason_code": report.reason_code,
                        "present": bool(report.present),
                        "quick_check": report.quick_check,
                        "foreign_key_violations": int(report.foreign_key_violations),
                        "shape_digest": report.shape_digest,
                        "marker_value": report.marker_value,
                    }
                )
        fingerprint = _digest(
            {
                "verifier_version": VERIFIER_VERSION,
                "members": members,
                "files": files,
                "workspace_present": self.project_dir.exists(),
                "snapshot_issues": sorted(set(issues)),
            }
        )
        return _WorkspaceSnapshot(fingerprint, inspection, tuple(sorted(set(issues))))

    def snapshot_fingerprint(self) -> str:
        """Return a deterministic workspace fingerprint without audit writes."""

        return self._snapshot().fingerprint

    def _append_verification_started(self, fingerprint: str) -> Any:
        bridge = self._bridge()
        return bridge._append(
            ProjectAuditEventKind.VERIFICATION_STARTED.value,
            operation_kind="verification",
            before_digest=fingerprint,
            after_digest=fingerprint,
            result_code="verification_started",
            reason_code="verification_started",
            verifier_version=VERIFIER_VERSION,
            snapshot_fingerprint=fingerprint,
            requested_domain_set=list(self.requested_domain_set),
        )

    def _append_verification_completed(
        self,
        result: str,
        fingerprint: str,
        anchors: Mapping[str, str],
        reason_enum: str,
    ) -> Any:
        bridge = self._bridge()
        exact = dict(anchors)
        return bridge._append(
            ProjectAuditEventKind.VERIFICATION_COMPLETED.value,
            operation_kind="verification",
            before_digest=fingerprint,
            after_digest=fingerprint,
            domain_anchors=exact,
            result_code=_result_code(result),
            reason_code=reason_enum,
            verifier_version=VERIFIER_VERSION,
            snapshot_fingerprint=fingerprint,
            verification_result=_result_code(result),
            exact_domain_anchors=exact,
            reason_enum=reason_enum,
        )

    def verify(self) -> ProjectVerificationResult:
        # Fingerprinting is a read-only preparation step.  It deliberately
        # excludes the root audit DB so repeated verification of one snapshot
        # yields the same fingerprint despite the appended event pair.
        snapshot = self._snapshot()
        fingerprint = snapshot.fingerprint
        issues = _VerificationIssues()
        for issue in snapshot.issues:
            if issue.endswith("symlink") or issue == "evidence_not_directory":
                issues.anomaly(issue)
            else:
                issues.recovery(issue)

        # The root event chain is checked before this invocation's own events.
        # An empty project chain is a valid first-verification baseline.
        started_event: Any = None
        try:
            ledger = self._get_ledger()
            events = self._audit_events(ledger, self.canonical_project_id)
            chain = self._verify_root_chain(ledger, self.canonical_project_id)
            if not events and not chain[0]:
                # ProjectAuditLedger has no per-project head until first append.
                # Other failed empty-chain implementations still indicate a
                # malformed root and are handled below.
                head = self._audit_head(ledger, self.canonical_project_id)
                if head is None or int(head.get("head_seq", 0)) == 0:
                    chain = (True, None, 0)
            if not chain[0]:
                issues.anomaly("root_audit_chain_mismatch")
                issues.anchor("root_ledger_anchor", {
                    "chain_ok": False,
                    "event_count": int(chain[2]),
                    "first_bad_seq": chain[1],
                })
                return self._result_from_issues(
                    issues,
                    fingerprint,
                    started_event=None,
                    completed_event=None,
                )
            issues.anchor("root_ledger_anchor", {
                "chain_ok": True,
                "event_count": int(chain[2]),
                "first_bad_seq": chain[1],
            })
            started_event = self._append_verification_started(fingerprint)
        except ProjectVerificationError:
            # A tampered root may reject all further appends.  Preserve the
            # deterministic anomaly result rather than hiding it behind a
            # transport exception; healthy roots always append both events.
            if issues.anomalies:
                return self._result_from_issues(
                    issues,
                    fingerprint,
                    started_event=None,
                    completed_event=None,
                )
            raise
        except Exception as exc:
            raise ProjectVerificationError(_safe_reason(
                getattr(exc, "code", "audit_ledger_unavailable"),
                "audit_ledger_unavailable",
            )) from exc

        try:
            # 1. Root schema/scope/event sequence/hash/head.
            self._check_root_scope(issues, events)
            # 2. Project identity/package/source/plan/operation.
            self._check_project_identity(issues)
            # 3. Current operation projection versus last boundary.
            self._check_operation_projection(issues)
            # 4. Live/staging/rollback/marker and independent SQLite reopen.
            self._check_live_evidence(issues, snapshot)
            # 5. R1 source/run/artifact/audit closure, using the public method.
            self._check_r1(issues)
            # 6. Publication identity/R5/R6/receipt/exact output.
            self._check_publication(issues)
            # 7. Continuity baseline/target/items/digest.
            self._check_continuity(issues)
            # 8. Own verification event anchors are appended below.
        except Exception:
            # The public surface must remain bounded even for an unexpected
            # read-only adapter failure.  The event still records recovery need.
            issues.recovery("verification_read_failed")

        result = issues.result
        try:
            completed_event = self._append_verification_completed(
                result,
                fingerprint,
                issues.anchors,
                issues.reason_enum,
            )
        except ProjectVerificationError:
            raise
        return self._result_from_issues(
            issues,
            fingerprint,
            started_event=started_event,
            completed_event=completed_event,
        )

    def _result_from_issues(
        self,
        issues: _VerificationIssues,
        fingerprint: str,
        *,
        started_event: Any,
        completed_event: Any,
    ) -> ProjectVerificationResult:
        result = issues.result
        return ProjectVerificationResult(
            result=result,
            message=_DEFAULT_MESSAGE[result],
            next_action=_DEFAULT_NEXT_ACTION[result],
            snapshot_fingerprint=fingerprint,
            before_digest=fingerprint,
            after_digest=fingerprint,
            reason_enum=issues.reason_enum,
            domain_anchors=dict(issues.anchors),
            started_event_id=_event_id(started_event) or None,
            completed_event_id=_event_id(completed_event) or None,
        )

    @staticmethod
    def _verify_root_chain(
        ledger: Any,
        canonical_project_id: str,
    ) -> tuple[bool, Optional[int], int]:
        method = getattr(ledger, "verify_chain", None)
        if not callable(method):
            method = getattr(ledger, "verify_audit_chain", None)
        if not callable(method):
            method = getattr(ledger, "verify", None)
        if not callable(method):
            raise ProjectVerificationError("audit_verify_unavailable")
        try:
            value = method(canonical_project_id)
        except TypeError:
            value = method()
        if isinstance(value, tuple):
            if len(value) >= 3:
                return bool(value[0]), value[1], int(value[2])
            if value:
                return bool(value[0]), None, 0
        if isinstance(value, list):
            if len(value) >= 3:
                return bool(value[0]), value[1], int(value[2])
            if value:
                return bool(value[0]), None, 0
        return bool(value), None, 0

    @staticmethod
    def _audit_head(
        ledger: Any,
        canonical_project_id: str,
    ) -> Optional[Mapping[str, Any]]:
        method = getattr(ledger, "head", None)
        if not callable(method):
            return None
        try:
            value = method(canonical_project_id)
        except Exception:
            return None
        data = _event_mapping(value)
        if data:
            return data
        if isinstance(value, Mapping):
            return value
        return None

    @staticmethod
    def _audit_events(
        ledger: Any,
        canonical_project_id: str,
    ) -> tuple[Any, ...]:
        method = getattr(ledger, "events", None)
        if not callable(method):
            method = getattr(ledger, "list_events", None)
        if not callable(method):
            method = getattr(ledger, "events_for_project", None)
        if not callable(method):
            raise ProjectVerificationError("audit_events_unavailable")
        try:
            value = method(canonical_project_id)
        except TypeError:
            value = method()
        if value is None:
            return ()
        return tuple(value)

    def _check_root_scope(
        self,
        issues: _VerificationIssues,
        events: Sequence[Any],
    ) -> None:
        scoped: list[dict[str, Any]] = []
        for event in events:
            data = _event_mapping(event)
            project = str(
                data.get("canonical_project_id", data.get("project_scope", "")) or ""
            )
            if project and project != self.canonical_project_id:
                issues.anomaly("root_scope_mismatch")
            scoped.append({
                "seq": data.get("project_seq", data.get("sequence", 0)),
                "kind": _event_kind(event),
                "event_id": _event_id(event),
                "operation": _event_operation(event),
                "boundary": data.get("boundary_token", ""),
                "chain": data.get("chain_hash", ""),
            })
        issues.anchor("root_event_anchor", scoped)

    def _check_project_identity(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / RUNTIME_DB_RELATIVE_PATH
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.recovery("runtime_unavailable")
            issues.anchor("identity_anchor", {"runtime": "missing"})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("runtime_integrity_failed")
            projects = _read_rows(
                connection,
                "projects",
                ("project_id", "is_synthetic", "created_at"),
            )
            source_rows = _read_rows(
                connection,
                "source_revisions",
                ("revision_id", "project_id", "source_type", "version", "content_hash", "valid_from"),
            )
            snapshot_rows = _read_rows(
                connection,
                "listing_snapshots",
                ("snapshot_id", "project_id", "revision_id", "snapshot_version", "content_hash", "row_count", "is_synthetic"),
            )
            run_rows = _read_rows(
                connection,
                "monitoring_runs",
                ("run_id", "project_id", "mode", "data_cutoff", "source_revision_id", "execution_basis", "analysis_state", "evidence_state", "review_state", "output_state", "manifest_revision"),
            )
            project_rows = projects
            for row in project_rows + source_rows + snapshot_rows + run_rows:
                row_project = row.get("project_id")
                if row_project and str(row_project) != self.canonical_project_id:
                    issues.anomaly("project_identity_mismatch")
            for row in projects:
                if "is_synthetic" in row and int(row.get("is_synthetic") or 0) != 1:
                    issues.anomaly("non_synthetic_project")
            revision_ids = {str(row.get("revision_id")) for row in source_rows}
            for row in snapshot_rows:
                if row.get("revision_id") and str(row["revision_id"]) not in revision_ids:
                    issues.anomaly("source_snapshot_mismatch")
            source_id_set = revision_ids
            for row in run_rows:
                if row.get("source_revision_id") and str(row["source_revision_id"]) not in source_id_set:
                    issues.anomaly("run_source_mismatch")
            issues.anchor("identity_anchor", {
                "projects": project_rows,
                "sources": source_rows,
                "snapshots": snapshot_rows,
                "runs": run_rows,
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("identity_read_failed")
        finally:
            connection.close()

    def _check_operation_projection(self, issues: _VerificationIssues) -> None:
        path = self.runtime_root / _backup.OPERATIONS_DB_NAME
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anchor("operation_anchor", [])
            return
        try:
            rows = _read_rows(
                connection,
                "backup_operations",
                (
                    "operation_id",
                    "operation_kind",
                    "canonical_project_id",
                    "status",
                    "progress_percent",
                    "terminal_outcome",
                    "error_code",
                    "rollback_path",
                    "staging_path",
                    "package_path",
                    "updated_at",
                ),
            )
            scoped = [
                row for row in rows
                if str(row.get("canonical_project_id") or "") == self.canonical_project_id
            ]
            if len(scoped) != len(rows):
                issues.anomaly("operation_scope_mismatch")
            boundary_events = self._audit_events(
                self._get_ledger(),
                self.canonical_project_id,
            )
            last_boundary: dict[str, dict[str, Any]] = {}
            for event in boundary_events:
                kind = _event_kind(event)
                if kind not in {
                    ProjectAuditEventKind.BOUNDARY_INTENT.value,
                    ProjectAuditEventKind.BOUNDARY_COMMITTED.value,
                    ProjectAuditEventKind.BOUNDARY_VERIFIED.value,
                }:
                    continue
                operation = _event_operation(event)
                if not operation:
                    continue
                last_boundary[operation] = {
                    "kind": kind,
                    "payload": _event_mapping(event).get("payload", {}),
                }
            projection: list[dict[str, Any]] = []
            for row in scoped:
                operation = str(row.get("operation_id") or "")
                status = str(row.get("status") or "")
                if status in _MIGRATION_RECOVERY_STATES or status in _BACKUP_RECOVERY_STATES:
                    issues.recovery("operation_recovery_pending")
                if status in {_MIGRATION_RETAINED_STATE, _BACKUP_RETAINED_STATE}:
                    issues.recovery("operation_retained_for_triage")
                if status == _MIGRATION_RETRYABLE_STATE:
                    issues.recovery("explicit_retry_required")
                if row.get("rollback_path") or row.get("staging_path"):
                    # Rollback evidence is expected to remain until this
                    # verifier completes and the coordinator emits the
                    # release event.  Its presence alone must not deadlock
                    # release; active/non-terminal projections are recovery.
                    if status not in {
                        "completed",
                        "available",
                        "already_current",
                        "kept_current",
                        "rolled_back",
                        "ready_for_confirmation",
                        "confirmed",
                    }:
                        issues.recovery("rollback_evidence_retained")
                boundary = last_boundary.get(operation)
                if boundary is not None:
                    payload = boundary.get("payload")
                    if not isinstance(payload, Mapping):
                        issues.anomaly("boundary_payload_invalid")
                    else:
                        observed = payload.get("observed_durable_phase")
                        if (
                            boundary.get("kind") in {
                                ProjectAuditEventKind.BOUNDARY_COMMITTED.value,
                                ProjectAuditEventKind.BOUNDARY_VERIFIED.value,
                            }
                            and observed
                            and str(observed) != status
                        ):
                            issues.recovery("operation_boundary_mismatch")
                        if (
                            boundary.get("kind") == ProjectAuditEventKind.BOUNDARY_INTENT.value
                            and status not in {"requested", "received", "confirmed", "staging"}
                        ):
                            issues.recovery("boundary_commit_missing")
                projection.append({
                    "operation": operation,
                    "kind": str(row.get("operation_kind") or ""),
                    "status": status,
                    "progress": row.get("progress_percent"),
                    "terminal": row.get("terminal_outcome"),
                    "error": row.get("error_code"),
                    "has_rollback": bool(row.get("rollback_path")),
                    "has_staging": bool(row.get("staging_path")),
                    "updated": row.get("updated_at"),
                })
            issues.anchor("operation_anchor", projection)
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("operation_read_failed")
        finally:
            connection.close()

    def _check_live_evidence(
        self,
        issues: _VerificationIssues,
        snapshot: _WorkspaceSnapshot,
    ) -> None:
        if snapshot.inspection is None:
            issues.recovery("schema_inspection_failed")
            return
        classification = snapshot.inspection.classification
        if classification is SchemaClassification.LEGACY:
            issues.recovery("legacy_project_requires_recovery")
        elif classification is SchemaClassification.UNKNOWN:
            issues.recovery("schema_unknown")
        elif classification is SchemaClassification.CORRUPT:
            issues.anomaly("schema_corrupt")
        elif classification is not SchemaClassification.CURRENT:
            issues.recovery("schema_not_current")
        for base in (self.runtime_root, self.project_dir):
            if base.is_symlink():
                issues.anomaly("evidence_symlink")
                continue
            for name in _EVIDENCE_DIRS:
                path = base / name
                if path.is_symlink():
                    issues.anomaly("evidence_symlink")
                elif path.exists():
                    if not path.is_dir():
                        issues.anomaly("evidence_not_directory")
                    else:
                        try:
                            if any(path.iterdir()):
                                issues.recovery("recovery_evidence_present")
                        except OSError:
                            issues.recovery("recovery_evidence_unreadable")
        try:
            rollback_entries = sorted(
                entry
                for entry in self.runtime_root.iterdir()
                if entry.name.startswith(_ROLLBACK_EVIDENCE_PREFIX)
            )
        except OSError:
            rollback_entries = []
            issues.recovery("recovery_evidence_unreadable")
        for path in rollback_entries:
            if path.is_symlink():
                issues.anomaly("evidence_symlink")
            elif not path.is_dir():
                issues.anomaly("evidence_not_directory")
            else:
                issues.recovery("recovery_evidence_present")
        paths_seen: set[str] = set()
        for report in snapshot.inspection.members.values():
            if not report.present:
                continue
            path = Path(report.path)
            key = str(path)
            if key in paths_seen:
                continue
            paths_seen.add(key)
            try:
                connection = _readonly_connection(path)
            except (OSError, sqlite3.Error):
                issues.anomaly("member_reopen_failed")
                continue
            try:
                quick, foreign_count = _quick_check(connection)
                if quick != "ok" or foreign_count:
                    issues.anomaly("member_integrity_failed")
            except (OSError, sqlite3.Error):
                issues.anomaly("member_reopen_failed")
            finally:
                connection.close()
        issues.anchor("live_anchor", {
            "classification": classification.value,
            "member_count": len(snapshot.inspection.members),
            "snapshot_issues": list(snapshot.issues),
        })

    def _check_r1(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / RUNTIME_DB_RELATIVE_PATH
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.recovery("r1_runtime_unavailable")
            issues.anchor("r1_anchor", {"available": False})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("r1_runtime_integrity_failed")
            # Call the established public verifier directly.  Do not copy its
            # chain algorithm into R7.
            readonly_store = Store.__new__(Store)
            readonly_store._conn = connection
            readonly_store.artifact_dir = self.project_dir / "artifacts"
            chain = readonly_store.verify_audit_chain()
            if not isinstance(chain, tuple) or not chain or not bool(chain[0]):
                issues.anomaly("r1_audit_chain_mismatch")
            artifact_rows = _read_rows(
                connection,
                "artifacts",
                ("artifact_id", "content_hash", "run_id", "node_id", "artifact_type", "completeness"),
            )
            artifact_checks: list[dict[str, Any]] = []
            for row in artifact_rows:
                artifact_id = str(row.get("artifact_id") or "")
                if not artifact_id or not str(row.get("content_hash") or ""):
                    issues.anomaly("artifact_identity_invalid")
                    continue
                try:
                    valid = bool(readonly_store.verify_artifact(artifact_id))
                except Exception:
                    valid = False
                if not valid:
                    issues.anomaly("artifact_integrity_failed")
                artifact_checks.append({
                    "artifact": artifact_id,
                    "content_hash": row.get("content_hash"),
                    "run": row.get("run_id"),
                    "valid": valid,
                })
            try:
                orphans = tuple(readonly_store.find_orphan_artifacts())
            except Exception:
                orphans = ()
            if orphans:
                issues.recovery("orphan_artifact_evidence")
            issues.anchor("r1_anchor", {
                "quick_check": quick,
                "foreign_key_violations": foreign_count,
                "audit": chain,
                "artifacts": artifact_checks,
                "orphans": sorted(str(item) for item in orphans),
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("r1_read_failed")
        finally:
            connection.close()

    def _check_publication(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / LAUNCH_DB_RELATIVE_PATH
        if not path.exists():
            issues.anchor("publication_anchor", [])
            return
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anomaly("publication_reopen_failed")
            issues.anchor("publication_anchor", {"available": False})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("publication_integrity_failed")
            registry = _read_rows(
                connection,
                "r7_launch_registry",
                ("run_id", "project_id", "public_run_token", "current_snapshot_token", "source_revision_id", "run_state", "result_available"),
            )
            publications = _read_rows(
                connection,
                "r7_result_publications",
                (
                    "run_id", "project_id", "public_run_token", "result_context_token",
                    "publication_revision", "publication_fingerprint", "snapshot_token",
                    "source_revision_id", "publication_state", "receipt_identities_json",
                    "receipt_set_digest", "r5_authority_packet_id", "r5_authority_packet_digest",
                    "s4_authority_packet_identities_json", "s4_authority_packet_digests_json",
                    "r6_output_set_digest", "artifact_member_ids_json", "artifact_member_set_digest",
                ),
            )
            registry_by_run = {
                str(row.get("run_id") or ""): row for row in registry
            }
            projected_publications: list[dict[str, Any]] = []
            for row in publications:
                if str(row.get("project_id") or "") != self.canonical_project_id:
                    issues.anomaly("publication_scope_mismatch")
                run_id = str(row.get("run_id") or "")
                launch = registry_by_run.get(run_id)
                if launch is None:
                    issues.anomaly("publication_run_missing")
                elif str(row.get("public_run_token") or "") != str(launch.get("public_run_token") or ""):
                    issues.anomaly("publication_identity_mismatch")
                state = str(row.get("publication_state") or "")
                if state in {"publishing", "recoverable_failed", "blocked"}:
                    issues.recovery("publication_recovery_pending")
                if state == "available" and not row.get("result_context_token"):
                    issues.anomaly("publication_context_missing")
                if row.get("r5_authority_packet_id") and not row.get("r5_authority_packet_digest"):
                    issues.anomaly("publication_r5_anchor_missing")
                for json_name, digest_name in (
                    ("receipt_identities_json", "receipt_set_digest"),
                    ("artifact_member_ids_json", "artifact_member_set_digest"),
                ):
                    try:
                        values = _json_value(row.get(json_name), default=[])
                    except ValueError:
                        issues.anomaly("publication_json_invalid")
                        values = []
                    if not isinstance(values, list):
                        issues.anomaly("publication_json_invalid")
                    elif values and not row.get(digest_name):
                        issues.anomaly("publication_anchor_missing")
                try:
                    s4_ids = _json_value(row.get("s4_authority_packet_identities_json"), default=[])
                    s4_digests = _json_value(row.get("s4_authority_packet_digests_json"), default=[])
                    if not isinstance(s4_ids, list) or not isinstance(s4_digests, list) or len(s4_ids) != len(s4_digests):
                        issues.anomaly("publication_s4_anchor_mismatch")
                except ValueError:
                    issues.anomaly("publication_json_invalid")
                projected_publications.append({
                    "run": run_id,
                    "project": row.get("project_id"),
                    "public_token": row.get("public_run_token"),
                    "context": row.get("result_context_token"),
                    "revision": row.get("publication_revision"),
                    "fingerprint": row.get("publication_fingerprint"),
                    "snapshot": row.get("snapshot_token"),
                    "source": row.get("source_revision_id"),
                    "state": state,
                    "r5": row.get("r5_authority_packet_digest"),
                    "r6": row.get("r6_output_set_digest"),
                    "receipt": row.get("receipt_set_digest"),
                    "artifact": row.get("artifact_member_set_digest"),
                })
            issues.anchor("publication_anchor", {
                "quick_check": quick,
                "foreign_key_violations": foreign_count,
                "registry": registry,
                "publications": projected_publications,
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("publication_read_failed")
        finally:
            connection.close()

    def _check_continuity(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / LAUNCH_DB_RELATIVE_PATH
        if not path.exists():
            issues.anchor("continuity_anchor", [])
            return
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anomaly("continuity_reopen_failed")
            issues.anchor("continuity_anchor", {"available": False})
            return
        try:
            plans = _read_rows(
                connection,
                "r7_continuity_plans",
                (
                    "plan_id", "project_id", "target_run_id", "target_public_run_token",
                    "source_run_id", "source_publication_id", "source_public_run_token",
                    "target_snapshot_id", "baseline_source_run_id", "baseline_source_publication_id",
                    "baseline_source_public_run_token", "r5_authority_digest", "r6_publication_digest",
                    "r6_receipt_digest", "r6_output_set_digest", "plan_digest", "status",
                    "counts_json", "plan_json",
                ),
            )
            items = _read_rows(
                connection,
                "r7_continuity_items",
                (
                    "plan_id", "ordinal", "object_type", "object_ref", "disposition",
                    "source_run_id", "source_publication_id", "source_public_run_token",
                    "source_artifact_id", "source_artifact_sha256", "item_digest", "item_json",
                ),
            )
            registry_rows = _read_rows(
                connection,
                "r7_launch_registry",
                ("run_id", "project_id", "public_run_token"),
            )
            publication_rows = _read_rows(
                connection,
                "r7_result_publications",
                ("run_id", "project_id", "public_run_token", "result_context_token"),
            )
            registry_by_run = {str(row.get("run_id")): row for row in registry_rows}
            publication_by_run = {str(row.get("run_id")): row for row in publication_rows}
            items_by_plan: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                items_by_plan.setdefault(str(item.get("plan_id") or ""), []).append(item)
            projected: list[dict[str, Any]] = []
            for plan in plans:
                if str(plan.get("project_id") or "") != self.canonical_project_id:
                    issues.anomaly("continuity_scope_mismatch")
                target_run = str(plan.get("target_run_id") or "")
                target = registry_by_run.get(target_run)
                if target is None:
                    issues.anomaly("continuity_target_missing")
                elif plan.get("target_public_run_token") and str(plan.get("target_public_run_token")) != str(target.get("public_run_token") or ""):
                    issues.anomaly("continuity_target_identity_mismatch")
                source_run = str(plan.get("source_run_id") or "")
                if source_run and source_run not in publication_by_run:
                    issues.anomaly("continuity_source_missing")
                status = str(plan.get("status") or "")
                if status in {"staging", "blocked"}:
                    issues.recovery("continuity_recovery_pending")
                try:
                    counts = _json_value(plan.get("counts_json"), default={})
                    plan_json = _json_value(plan.get("plan_json"), default={})
                    if not isinstance(counts, dict) or not isinstance(plan_json, dict):
                        issues.anomaly("continuity_json_invalid")
                except ValueError:
                    issues.anomaly("continuity_json_invalid")
                plan_items = sorted(
                    items_by_plan.get(str(plan.get("plan_id") or ""), []),
                    key=lambda item: int(item.get("ordinal") or 0),
                )
                ordinals = [int(item.get("ordinal") or 0) for item in plan_items]
                if ordinals != list(range(len(ordinals))):
                    issues.anomaly("continuity_ordinal_gap")
                for item in plan_items:
                    if not item.get("item_digest"):
                        issues.anomaly("continuity_item_digest_missing")
                    try:
                        item_json = _json_value(item.get("item_json"), default={})
                        if not isinstance(item_json, dict):
                            issues.anomaly("continuity_item_json_invalid")
                    except ValueError:
                        issues.anomaly("continuity_item_json_invalid")
                projected.append({
                    "plan": plan.get("plan_id"),
                    "project": plan.get("project_id"),
                    "target": target_run,
                    "source": source_run,
                    "status": status,
                    "plan_digest": plan.get("plan_digest"),
                    "r5": plan.get("r5_authority_digest"),
                    "r6": plan.get("r6_publication_digest"),
                    "receipt": plan.get("r6_receipt_digest"),
                    "output": plan.get("r6_output_set_digest"),
                    "item_count": len(plan_items),
                    "items": [
                        {
                            "ordinal": item.get("ordinal"),
                            "object_type": item.get("object_type"),
                            "object_ref": item.get("object_ref"),
                            "disposition": item.get("disposition"),
                            "item_digest": item.get("item_digest"),
                        }
                        for item in plan_items
                    ],
                })
            issues.anchor("continuity_anchor", projected)
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("continuity_read_failed")
        finally:
            connection.close()


# ---------------------------------------------------------------------------
# 09A/09B recovery coordinator


class RecoveryCoordinator:
    """One coordinator for startup, open, retry, boundary, and rollback paths."""

    def __init__(
        self,
        runtime_root: str | Path,
        canonical_project_id: str,
        *,
        project_dir: Optional[str | Path] = None,
        wait_seconds: float = 0.5,
        audit_ledger_factory: Optional[Callable[..., Any]] = None,
        audit_ledger: Any = None,
        principal_snapshot_hash: str = "",
        authorization_decision_hash: str = "",
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _normalise_project_id(canonical_project_id)
        self.project_dir = Path(project_dir) if project_dir is not None else (
            self.runtime_root / self.canonical_project_id
        )
        self.wait_seconds = float(wait_seconds)
        self.audit_ledger_factory = audit_ledger_factory
        self._ledger = audit_ledger
        self._owns_ledger = audit_ledger is None
        self._principal_snapshot_hash = principal_snapshot_hash
        self._authorization_decision_hash = authorization_decision_hash

    def _get_ledger(self) -> Any:
        if self._ledger is None:
            self._ledger = _new_audit_ledger(
                self.runtime_root,
                self.canonical_project_id,
                self.audit_ledger_factory,
            )
        return self._ledger

    def _bridge(self) -> ProjectAuditBridge:
        return ProjectAuditBridge(
            self._get_ledger(),
            self.canonical_project_id,
            principal_snapshot_hash=self._principal_snapshot_hash,
            authorization_decision_hash=self._authorization_decision_hash,
        )

    def close(self) -> None:
        ledger = self._ledger
        self._ledger = None
        if ledger is not None and self._owns_ledger:
            close = getattr(ledger, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "RecoveryCoordinator":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def open_project(self) -> Any:
        """Inspect first, then use the accepted migration runner's open path."""

        try:
            initial = inspect_project_schema(self.project_dir)
        except Exception as exc:
            raise RecoveryCoordinationError("schema_inspection_failed") from exc
        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            if initial.classification is SchemaClassification.LEGACY:
                runner._ensure_complete_legacy(initial)
            return runner.open_project()
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "recovery_required"),
                "recovery_required",
            )) from exc
        finally:
            runner.close()

    def startup_recovery_scan(
        self,
        operation_id: Optional[str] = None,
    ) -> tuple[Any, ...]:
        """Scan 09A recovery evidence and resume only 09B public states.

        09A restore boundaries require the original same-key/package request,
        so startup reports their durable records without replaying filesystem
        switches.  09B owns a complete evidence-based recovery runner and may
        be resumed here.  Retained triage and retryable failures remain
        excluded from both paths.
        """

        try:
            initial = inspect_project_schema(self.project_dir)
        except Exception as exc:
            raise RecoveryCoordinationError("schema_inspection_failed") from exc
        backup_pending: tuple[Any, ...] = ()
        ledger_path = self.runtime_root / str(
            getattr(_backup, "OPERATIONS_DB_NAME", "backup_operations.sqlite3")
        )
        if ledger_path.is_file():
            backup_ledger = _backup.OperationLedger(ledger_path)
            try:
                backup_pending = tuple(
                    record
                    for record in backup_ledger.list_for_project(
                        self.canonical_project_id
                    )
                    if str(record.operation_kind)
                    == str(getattr(_backup, "OP_RESTORE", "restore"))
                    and str(record.status) in _BACKUP_RECOVERY_STATES
                )
            finally:
                backup_ledger.close()
        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            if operation_id:
                ledger = runner._ledger()
                record = ledger.get(operation_id)
                status = str(record.status)
                if status in {_MIGRATION_RETRYABLE_STATE, _MIGRATION_RETAINED_STATE}:
                    raise RecoveryCoordinationError("explicit_retry_or_triage_required")
                if status not in _MIGRATION_RECOVERY_STATES and status not in set(
                    getattr(_migration, "TERMINAL_STATES", ())
                ):
                    raise RecoveryCoordinationError("operation_not_recoverable")
            return backup_pending + tuple(runner.recover(operation_id))
        except RecoveryCoordinationError:
            raise
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "recovery_required"),
                "recovery_required",
            )) from exc
        finally:
            runner.close()

    recover = startup_recovery_scan
    recover_pending = startup_recovery_scan

    def start_upgrade(self, idempotency_key: str, *, confirmation: bool = True) -> Any:
        """Use the same coordinator object for explicit same-key migration retry."""

        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            return runner.start_upgrade(idempotency_key, confirmation=confirmation)
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "retry_failed"),
                "retry_failed",
            )) from exc
        finally:
            runner.close()

    def begin_boundary(
        self,
        operation_ref: str,
        *,
        operation_kind: str,
        expected_state: str,
        before_digest: str,
        boundary_token: str,
        package_digest: Optional[str] = None,
        source_digest: Optional[str] = None,
        plan_digest: Optional[str] = None,
        slot_presence: Optional[Mapping[str, Any]] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> BoundaryReceipt:
        safe_operation = _opaque_reference(operation_ref, prefix="operation")
        safe_token = _opaque_reference(boundary_token, prefix="boundary")
        try:
            event = self._bridge().boundary_intent(
                safe_operation,
                operation_kind=operation_kind,
                boundary_token=safe_token,
                expected_state=expected_state,
                before_digest=before_digest,
                package_digest=package_digest,
                source_digest=source_digest,
                plan_digest=plan_digest,
                slot_presence=slot_presence,
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        return BoundaryReceipt(
            operation_id=safe_operation,
            operation_kind=_opaque_reference(operation_kind, prefix="kind"),
            boundary_token=safe_token,
            expected_state=_safe_reason(expected_state, "unknown_state"),
            before_digest=str(before_digest or ""),
            principal_snapshot_hash=self._bridge().principal_snapshot_hash,
            authorization_decision_hash=self._bridge().authorization_decision_hash,
            intent_event_id=_event_id(event),
        )

    def mark_committed(
        self,
        receipt: BoundaryReceipt,
        *,
        observed_durable_phase: str,
        after_digest: str,
        marker_digest: Optional[str] = None,
        member_digest: Optional[str] = None,
        workspace_digest: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        try:
            return self._bridge().boundary_committed(
                receipt.operation_id,
                operation_kind=receipt.operation_kind,
                boundary_token=receipt.boundary_token,
                observed_durable_phase=observed_durable_phase,
                after_digest=after_digest,
                marker_digest=marker_digest,
                member_digest=member_digest,
                workspace_digest=workspace_digest,
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def mark_verified(
        self,
        receipt: BoundaryReceipt,
        *,
        verifier_outcome: str,
        after_digest: str,
        r1_anchor: Optional[str] = None,
        publication_anchor: Optional[str] = None,
        continuity_anchor: Optional[str] = None,
    ) -> Any:
        try:
            return self._bridge().boundary_verified(
                receipt.operation_id,
                operation_kind=receipt.operation_kind,
                boundary_token=receipt.boundary_token,
                verifier_outcome=verifier_outcome,
                after_digest=after_digest,
                r1_anchor=r1_anchor,
                publication_anchor=publication_anchor,
                continuity_anchor=continuity_anchor,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def classify_recovery(
        self,
        operation_ref: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        classification: str,
        slot_anchor: Optional[str] = None,
        marker_anchor: Optional[str] = None,
        root_ledger_anchor: Optional[str] = None,
    ) -> Any:
        try:
            return self._bridge().recovery_classified(
                operation_ref,
                operation_kind=operation_kind,
                observed_durable_phase=observed_durable_phase,
                classification=classification,
                slot_anchor=slot_anchor,
                marker_anchor=marker_anchor,
                root_ledger_anchor=root_ledger_anchor,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def release_rollback_evidence(
        self,
        operation_ref: str,
        *,
        verified_event_id: str,
        rollback_digest: str,
        release: Callable[[], Any],
        operation_kind: str,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """Release rollback evidence only after a verified completion event."""

        bridge = self._bridge()
        try:
            intent = bridge.rollback_release_intent(
                operation_ref,
                operation_kind=operation_kind,
                verified_event_id=verified_event_id,
                rollback_digest=rollback_digest,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        intent_id = _event_id(intent)
        if not intent_id:
            raise RecoveryCoordinationError("release_intent_event_missing")
        try:
            released = release()
            if released is False:
                raise OSError("release_rejected")
        except Exception:
            try:
                bridge.rollback_evidence_release_failed(
                    operation_ref,
                    operation_kind=operation_kind,
                    release_intent_id=intent_id,
                    outcome="release_failed",
                    diagnostic_enum="release_failed",
                )
            except ProjectVerificationError as exc:
                raise RecoveryCoordinationError(exc.code) from exc
            return False
        try:
            bridge.rollback_evidence_released(
                operation_ref,
                operation_kind=operation_kind,
                release_intent_id=intent_id,
                outcome="released",
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        return True


# Public aliases used by integrations that name the coordinator explicitly.
ProjectRecoveryCoordinator = RecoveryCoordinator
ProjectAuditEventBridge = ProjectAuditBridge
ProjectVerifierResult = ProjectVerificationResult


def startup_recovery_scan(
    runtime_root: str | Path,
    canonical_project_id: str,
    *,
    project_dir: Optional[str | Path] = None,
    operation_id: Optional[str] = None,
    wait_seconds: float = 0.5,
    audit_ledger_factory: Optional[Callable[..., Any]] = None,
) -> tuple[Any, ...]:
    coordinator = RecoveryCoordinator(
        runtime_root,
        canonical_project_id,
        project_dir=project_dir,
        wait_seconds=wait_seconds,
        audit_ledger_factory=audit_ledger_factory,
    )
    try:
        return coordinator.startup_recovery_scan(operation_id)
    finally:
        coordinator.close()


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "BoundaryReceipt",
    "ProjectAuditBridge",
    "ProjectAuditEventBridge",
    "ProjectRecoveryCoordinator",
    "ProjectVerificationDTO",
    "ProjectVerificationError",
    "ProjectVerificationResult",
    "ProjectVerifierResult",
    "RecoveryCoordinationError",
    "RecoveryCoordinator",
    "RESULT_ANOMALY",
    "RESULT_RECORD_COMPLETE",
    "RESULT_RECOVERY_REQUIRED",
    "VERIFIER_VERSION",
    "ProjectVerifier",
    "startup_recovery_scan",
]
