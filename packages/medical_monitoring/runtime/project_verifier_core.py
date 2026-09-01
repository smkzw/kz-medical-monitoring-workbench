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


