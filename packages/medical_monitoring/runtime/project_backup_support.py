"""Synthetic/offline R7 Slice-09A project backup and restore core.

This module intentionally has no dependency on FastAPI, the product router,
or third-party archive libraries.  It operates on the six frozen
workspace member families with SQLite's online backup API, verifies the R1
content-addressed artifact closure, and publishes one deterministic ZIP.

The public product adapter can project the small dataclasses in this module to
Chinese DTOs.  Internal paths, database names, hashes, and operation IDs remain
available here for the synthetic test harness but are not a product response.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass, field, replace as dataclass_replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from ..graph.store import Store as R1Store

from .maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectBusyError,
    ProjectMaintenanceGate,
)
from .root_ledger_schema import ROOT_LEDGER_DDL


CONTRACT_VERSION = "FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3"
SCHEMA_VERSION = "mm-r7-slice09a-project-backup-v1"
BACKUP_SUFFIX = ".mmbackup"
PROFILE_DB_NAME = "execution_profiles.sqlite3"
RUN_BINDING_DB_NAME = "monitoring_run_bindings.sqlite3"
LAUNCH_REGISTRY_DB_NAME = "launch_registry.sqlite3"
RISK_RULE_DB_NAME = "risk_rules.sqlite3"
RUNTIME_DIR_NAME = "runtime"
RUNTIME_DB_NAME = "monitoring_runtime.sqlite3"
ARTIFACT_DIR_NAME = "artifacts"
OPERATIONS_DB_NAME = "backup_operations.sqlite3"
BACKUP_PUBLICATION_DIR_NAME = "backups"
STAGING_DIR_NAME = ".mmbackup-staging"

OP_BACKUP = "backup"
OP_PREFLIGHT = "restore_preflight"
OP_RESTORE = "restore"

STATUS_REQUESTED = "requested"
STATUS_RECEIVED = "received"
STATUS_WAITING_FOR_PROJECT = "waiting_for_project"
STATUS_COLLECTING = "collecting"
STATUS_SNAPSHOTTING = "snapshotting"
STATUS_VERIFYING = "verifying"
STATUS_PACKAGING = "packaging"
STATUS_AVAILABLE = "available"
STATUS_INSPECTING = "inspecting"
STATUS_VERIFYING_MEMBERS = "verifying_members"
STATUS_RECONCILING_IDENTITY = "reconciling_identity"
STATUS_READY_FOR_CONFIRMATION = "ready_for_confirmation"
STATUS_CONFIRMED = "confirmed"
STATUS_STAGING = "staging"
STATUS_VERIFYING_STAGED_WORKSPACE = "verifying_staged_workspace"
STATUS_QUIESCING_PROJECT = "quiescing_project"
STATUS_SWITCHING = "switching"
STATUS_VERIFYING_LIVE_WORKSPACE = "verifying_live_workspace"
STATUS_COMPLETED = "completed"
STATUS_ALREADY_CURRENT = "already_current"
STATUS_KEPT_CURRENT = "kept_current"
STATUS_ROLLBACK_IN_PROGRESS = "rollback_in_progress"
STATUS_RETAINED_FOR_TRIAGE = "retained_for_triage"
STATUS_FAILED = "failed"

PROGRESS_REQUEST_ACCEPTED = 5
PROGRESS_IDENTITY_CONFIRMED = 12
PROGRESS_SNAPSHOT_COMPLETE = 35
PROGRESS_ARTIFACT_CLOSURE_COMPLETE = 50
PROGRESS_MEMBER_VERIFICATION_COMPLETE = 65
PROGRESS_STAGING_COMPLETE = 78
PROGRESS_RECONCILIATION_COMPLETE = 94
PROGRESS_COMPLETE = 100

MAX_ARCHIVE_MEMBERS = 1024
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_ALLOWED_ROOT_FILES = frozenset(
    {
        PROFILE_DB_NAME,
        RUN_BINDING_DB_NAME,
        LAUNCH_REGISTRY_DB_NAME,
        RISK_RULE_DB_NAME,
    }
)
_IGNORABLE_NAMES = frozenset({".DS_Store", "Thumbs.db"})
_SUPPORTED_PROFILE_SCHEMA = "mm-r7-profile-store-v1"
_SUPPORTED_BINDING_SCHEMA = "r7-slice01-run-binding-v1"
_SUPPORTED_RUNTIME_SCHEMAS = frozenset({"6", "5", "4"})
_SUPPORTED_LAUNCH_SCHEMAS = frozenset(
    {
        "mm-r7-slice07c2-launch-registry-v1",
        "mm-r7-slice07c3-launch-registry-v2",
        "mm-r7-slice08a-launch-registry-v3",
        "mm-r7-slice08b-launch-registry-v4",
    }
)
_SUPPORTED_MANIFEST_KEYS = frozenset(
    {
        "artifact_closure",
        "backup_cutoff",
        "canonical_project_id",
        "content_digest",
        "contract_version",
        "project_name",
        "project_summary",
        "schema_version",
        "source_workspace_fingerprint",
        "members",
    }
)

# The names are intentionally source-enumerated rather than padded to a
# contract number.  Tests can enumerate this tuple and inject each real
# transition/file/switch boundary.
FAILURE_HOOK_POINTS = (
    "backup.sqlite_snapshot.before",
    "backup.sqlite_snapshot.after",
    "backup.artifact_set_freeze.before",
    "backup.artifact_set_freeze.after",
    "backup.artifact_copy.before",
    "backup.artifact_copy.after",
    "backup.artifact_closure_verification.before",
    "backup.artifact_closure_verification.after",
    "backup.manifest_generation.before",
    "backup.manifest_generation.after",
    "backup.package_generation.before",
    "backup.package_generation.after",
    "backup.package_publish.before",
    "backup.package_publish.after",
    "backup.operation_record_submit.before",
    "backup.operation_record_submit.after",
    "preflight.unpack.before",
    "preflight.unpack.after",
    "preflight.member_verification.before",
    "preflight.member_verification.after",
    "preflight.staging_workspace_verification.before",
    "preflight.staging_workspace_verification.after",
    "restore.quiesce.before",
    "restore.quiesce.after",
    "restore.current_to_rollback.before",
    "restore.current_to_rollback.after",
    "restore.staging_to_live.before",
    "restore.staging_to_live.after",
    "restore.live_reopen.before",
    "restore.live_reopen.after",
    "restore.identity_verification.before",
    "restore.identity_verification.after",
    "restore.artifact_verification.before",
    "restore.artifact_verification.after",
    "restore.publication_verification.before",
    "restore.publication_verification.after",
    "restore.continuity_verification.before",
    "restore.continuity_verification.after",
    "restore.rollback.before",
    "restore.rollback.after",
    "restore.operation_record_submit.before",
    "restore.operation_record_submit.after",
)
HOOK_POINTS = FAILURE_HOOK_POINTS


_ERROR_MESSAGES = {
    "invalid_project_id": "医学监查项目标识无效。",
    "invalid_idempotency_key": "医学监查操作请求无效。",
    "backup_operation_conflict": "同一操作请求对应的项目状态已发生变化。",
    "project_busy_retry_later": "项目正在处理数据，请稍后重试",
    "workspace_not_found": "未找到当前医学监查项目。",
    "workspace_member_missing": "项目备份所需资料尚不完整。",
    "workspace_unknown_member": "项目中存在无法核对的资料，备份已阻断。",
    "workspace_member_symlink": "项目资料包含无法核对的链接，备份已阻断。",
    "sqlite_integrity_failed": "项目数据无法完成一致性核对。",
    "unsupported_schema": "项目数据版本暂不支持。",
    "unsupported_contract": "备份包版本暂不支持。",
    "artifact_closure_invalid": "项目中有未完成清理的数据，请先核对后再备份",
    "package_corrupt": "备份包已损坏，无法恢复。",
    "package_identity_mismatch": "备份包与当前医学监查项目不一致。",
    "manifest_semantic_mismatch": "备份包内容与项目状态不一致。",
    "restore_confirmation_required": "恢复较早项目版本前需要确认。",
    "restore_source_changed": "项目状态在核对后发生变化，请重新预检。",
    "rollback_requires_review": "项目存在尚未核对的回退版本，请稍后处理。",
    "restore_verification_failed": "恢复后的项目未通过重新核对。",
    "restore_switch_failed": "项目版本切换未能完成。",
    "restore_rollback_failed": "项目恢复尚未完成，请稍后核对",
    "backup_package_publish_failed": "备份文件未能发布，请稍后重试。",
    "operation_not_found": "未找到对应的医学监查操作。",
    "injected_failure": "医学监查操作未能完成。",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def sha256_hex(value: Union[bytes, bytearray, str]) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(bytes(value)).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _required_project_id(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ProjectBackupError("invalid_project_id")
    if "\x00" in value or any(ord(char) < 32 for char in value):
        raise ProjectBackupError("invalid_project_id")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ProjectBackupError("invalid_project_id")
    return value


def _required_key(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise ProjectBackupError("invalid_idempotency_key")
    return value


class ProjectBackupError(RuntimeError):
    """Fail-closed core error with a stable code and Chinese message."""

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = str(code)
        self.message = message or _ERROR_MESSAGES.get(self.code, "医学监查操作未能完成。")
        self.details = dict(details or {})
        super().__init__(self.code)

    def as_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message}


BackupError = ProjectBackupError
RestoreError = ProjectBackupError
PreflightError = ProjectBackupError


class InjectedFailure(ProjectBackupError):
    def __init__(self, point: str) -> None:
        self.point = str(point)
        super().__init__("injected_failure", details={"point": self.point})


@dataclass(frozen=True)
class OperationRecord:
    operation_id: str
    operation_kind: str
    idempotency_key: str
    canonical_project_id: str
    status: str
    progress_percent: int
    current_step: str
    package_id: Optional[str] = None
    source_workspace_fingerprint: Optional[str] = None
    terminal_outcome: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    rollback_path: Optional[str] = None
    staging_path: Optional[str] = None
    package_path: Optional[str] = None
    maintenance_state: Optional[str] = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    replayed: bool = False

    def as_dict(self, *, include_internal: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "operation_id": self.operation_id,
            "operation_kind": self.operation_kind,
            "idempotency_key": self.idempotency_key,
            "canonical_project_id": self.canonical_project_id,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "package_id": self.package_id,
            "source_workspace_fingerprint": self.source_workspace_fingerprint,
            "terminal_outcome": self.terminal_outcome,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "rollback_path": self.rollback_path,
            "staging_path": self.staging_path,
            "package_path": self.package_path,
            "maintenance_state": self.maintenance_state,
            "payload": dict(self.payload),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "replayed": self.replayed,
        }
        if not include_internal:
            for key in (
                "idempotency_key",
                "canonical_project_id",
                "source_workspace_fingerprint",
                "rollback_path",
                "staging_path",
                "package_path",
                "maintenance_state",
                "payload",
                "created_at",
                "updated_at",
            ):
                result.pop(key, None)
        return result

    to_dict = as_dict

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.as_dict().get(key, default)


@dataclass(frozen=True)
class BackupResult:
    operation: OperationRecord
    package_id: Optional[str]
    package_path: Optional[Path]
    source_workspace_fingerprint: Optional[str]
    manifest: Mapping[str, Any]

    @property
    def operation_id(self) -> str:
        return self.operation.operation_id

    @property
    def status(self) -> str:
        return self.operation.status

    def as_dict(self, *, include_internal: bool = True) -> Dict[str, Any]:
        body = {
            "operation": self.operation.as_dict(include_internal=include_internal),
            "operation_id": self.operation.operation_id,
            "status": self.operation.status,
            "package_id": self.package_id,
            "package_path": str(self.package_path) if self.package_path is not None else None,
            "source_workspace_fingerprint": self.source_workspace_fingerprint,
            "manifest": dict(self.manifest),
        }
        if not include_internal:
            for key in (
                "package_id",
                "package_path",
                "source_workspace_fingerprint",
                "manifest",
            ):
                body.pop(key, None)
        return body

    to_dict = as_dict

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]
@dataclass(frozen=True)
class PreflightResult:
    operation: OperationRecord
    package_id: str
    package_path: Path
    canonical_project_id: str
    project_name: str
    backup_cutoff_label: str
    current_cutoff_label: str
    decision: str
    decision_label: str
    impact_summary: str
    items_preserved: Tuple[str, ...]
    items_rolled_back: Mapping[str, Any]
    recommended_action: str
    confirmation_required: bool
    unfinished_work_notice: Optional[str]
    source_workspace_fingerprint: str
    current_workspace_fingerprint: Optional[str]
    staging_path: Optional[Path]
    manifest: Mapping[str, Any]

    @property
    def operation_id(self) -> str:
        return self.operation.operation_id

    def as_dict(self, *, include_internal: bool = True) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "operation": self.operation.as_dict(include_internal=include_internal),
            "operation_id": self.operation.operation_id,
            "package_id": self.package_id,
            "package_path": str(self.package_path),
            "canonical_project_id": self.canonical_project_id,
            "project_name": self.project_name,
            "backup_cutoff_label": self.backup_cutoff_label,
            "current_cutoff_label": self.current_cutoff_label,
            "decision": self.decision,
            "decision_label": self.decision_label,
            "impact_summary": self.impact_summary,
            "items_preserved": list(self.items_preserved),
            "items_rolled_back": dict(self.items_rolled_back),
            "recommended_action": self.recommended_action,
            "confirmation_required": self.confirmation_required,
            "source_workspace_fingerprint": self.source_workspace_fingerprint,
            "current_workspace_fingerprint": self.current_workspace_fingerprint,
            "staging_path": str(self.staging_path) if self.staging_path is not None else None,
            "manifest": dict(self.manifest),
        }
        if self.unfinished_work_notice is not None:
            body["unfinished_work_notice"] = self.unfinished_work_notice
        if not include_internal:
            for key in (
                "package_id",
                "package_path",
                "canonical_project_id",
                "source_workspace_fingerprint",
                "current_workspace_fingerprint",
                "staging_path",
                "manifest",
            ):
                body.pop(key, None)
        return body

    to_dict = as_dict

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


@dataclass(frozen=True)
class RestoreResult:
    operation: OperationRecord
    result_label: str
    project_name: str
    restored_cutoff_label: str
    verification_summary: str
    next_action_label: str
    rollback_path: Optional[Path] = None

    @property
    def operation_id(self) -> str:
        return self.operation.operation_id

    def as_dict(self, *, include_internal: bool = True) -> Dict[str, Any]:
        result = {
            "operation": self.operation.as_dict(include_internal=include_internal),
            "operation_id": self.operation.operation_id,
            "result_label": self.result_label,
            "project_name": self.project_name,
            "restored_cutoff_label": self.restored_cutoff_label,
            "verification_summary": self.verification_summary,
            "next_action_label": self.next_action_label,
            "rollback_path": str(self.rollback_path) if self.rollback_path else None,
        }
        if not include_internal:
            result.pop("rollback_path", None)
        return result

    to_dict = as_dict

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


_LEDGER_DDL = ROOT_LEDGER_DDL


class OperationLedger:
    """Root-level operation ledger; never part of a project backup package."""

    def __init__(self, root_or_db_path: Union[str, Path]) -> None:
        candidate = Path(root_or_db_path)
        self.path = candidate if candidate.suffix == ".sqlite3" else candidate / OPERATIONS_DB_NAME
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.path), timeout=10.0, isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_LEDGER_DDL)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "OperationLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _row(self, operation_id: str, *, replayed: bool = False) -> OperationRecord:
        row = self._conn.execute(
            "SELECT * FROM backup_operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
        if row is None:
            raise ProjectBackupError("operation_not_found")
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc
        if not isinstance(payload, dict):
            raise ProjectBackupError("sqlite_integrity_failed")
        return OperationRecord(
            operation_id=str(row["operation_id"]),
            operation_kind=str(row["operation_kind"]),
            idempotency_key=str(row["idempotency_key"]),
            canonical_project_id=str(row["canonical_project_id"]),
            status=str(row["status"]),
            progress_percent=int(row["progress_percent"]),
            current_step=str(row["current_step"]),
            package_id=row["package_id"] or None,
            source_workspace_fingerprint=row["source_workspace_fingerprint"] or None,
            terminal_outcome=row["terminal_outcome"] or None,
            error_code=row["error_code"] or None,
            error_message=row["error_message"] or None,
            rollback_path=row["rollback_path"] or None,
            staging_path=row["staging_path"] or None,
            package_path=row["package_path"] or None,
            maintenance_state=row["maintenance_state"] or None,
            payload=payload,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            replayed=replayed,
        )

    def get(self, operation_id: str) -> OperationRecord:
        if not isinstance(operation_id, str) or not operation_id:
            raise ProjectBackupError("operation_not_found")
        return self._row(operation_id)

    def create_or_replay(
        self,
        operation_kind: str,
        idempotency_key: str,
        canonical_project_id: str,
        *,
        package_id: Optional[str] = None,
        source_workspace_fingerprint: Optional[str] = None,
        initial_status: Optional[str] = None,
    ) -> OperationRecord:
        kind = _required_key(operation_kind)
        key = _required_key(idempotency_key)
        project = _required_project_id(canonical_project_id)
        status = initial_status or (STATUS_REQUESTED if kind == OP_BACKUP else STATUS_RECEIVED)
        now = _now_iso()
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT operation_id, package_id, source_workspace_fingerprint"
                " FROM backup_operations WHERE operation_kind=? AND idempotency_key=?"
                " AND canonical_project_id=?",
                (kind, key, project),
            ).fetchone()
            if row is not None:
                existing_package = row["package_id"]
                existing_fp = row["source_workspace_fingerprint"]
                if package_id is not None and existing_package not in (None, package_id):
                    raise ProjectBackupError("backup_operation_conflict")
                if (
                    source_workspace_fingerprint is not None
                    and existing_fp not in (None, source_workspace_fingerprint)
                ):
                    raise ProjectBackupError("backup_operation_conflict")
                self._conn.execute("COMMIT")
                return self._row(str(row["operation_id"]), replayed=True)
            operation_id = uuid.uuid4().hex
            if not _SAFE_OPERATION_ID.match(operation_id):
                raise ProjectBackupError("operation_not_found")
            self._conn.execute(
                "INSERT INTO backup_operations(operation_id, operation_kind,"
                " idempotency_key, canonical_project_id, status, progress_percent,"
                " current_step, package_id, source_workspace_fingerprint, payload_json,"
                " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    operation_id,
                    kind,
                    key,
                    project,
                    status,
                    PROGRESS_REQUEST_ACCEPTED,
                    "请求已接收",
                    package_id,
                    source_workspace_fingerprint,
                    "{}",
                    now,
                    now,
                ),
            )
            self._conn.execute("COMMIT")
            return self._row(operation_id)
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    def update(
        self,
        operation_id: str,
        *,
        status: Optional[str] = None,
        progress_percent: Optional[int] = None,
        current_step: Optional[str] = None,
        package_id: Optional[str] = None,
        source_workspace_fingerprint: Optional[str] = None,
        terminal_outcome: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        rollback_path: Optional[str] = None,
        staging_path: Optional[str] = None,
        package_path: Optional[str] = None,
        maintenance_state: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        allow_terminal_reopen: bool = False,
    ) -> OperationRecord:
        current = self.get(operation_id)
        terminal = {
            STATUS_AVAILABLE,
            STATUS_FAILED,
            STATUS_COMPLETED,
            STATUS_ALREADY_CURRENT,
            STATUS_RETAINED_FOR_TRIAGE,
        }
        if (
            current.status in terminal
            and status is not None
            and status != current.status
            and not allow_terminal_reopen
            and current.status != STATUS_KEPT_CURRENT
        ):
            raise ProjectBackupError("backup_operation_conflict")
        if progress_percent is not None:
            if isinstance(progress_percent, bool) or not 0 <= int(progress_percent) <= 100:
                raise ProjectBackupError("sqlite_integrity_failed")
            progress = max(current.progress_percent, int(progress_percent))
        else:
            progress = current.progress_percent
        fields: Dict[str, Any] = {
            "status": status if status is not None else current.status,
            "progress_percent": progress,
            "current_step": current_step if current_step is not None else current.current_step,
            "package_id": package_id if package_id is not None else current.package_id,
            "source_workspace_fingerprint": (
                source_workspace_fingerprint
                if source_workspace_fingerprint is not None
                else current.source_workspace_fingerprint
            ),
            "terminal_outcome": (
                terminal_outcome if terminal_outcome is not None else current.terminal_outcome
            ),
            "error_code": error_code if error_code is not None else current.error_code,
            "error_message": (
                error_message if error_message is not None else current.error_message
            ),
            "rollback_path": rollback_path if rollback_path is not None else current.rollback_path,
            "staging_path": staging_path if staging_path is not None else current.staging_path,
            "package_path": package_path if package_path is not None else current.package_path,
            "maintenance_state": (
                maintenance_state
                if maintenance_state is not None
                else current.maintenance_state
            ),
            "payload_json": canonical_json(dict(payload)) if payload is not None else canonical_json(dict(current.payload)),
            "updated_at": _now_iso(),
        }
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE backup_operations SET status=?, progress_percent=?, current_step=?,"
                " package_id=?, source_workspace_fingerprint=?, terminal_outcome=?,"
                " error_code=?, error_message=?, rollback_path=?, staging_path=?,"
                " package_path=?, maintenance_state=?, payload_json=?, updated_at=?"
                " WHERE operation_id=?",
                (
                    fields["status"],
                    fields["progress_percent"],
                    fields["current_step"],
                    fields["package_id"],
                    fields["source_workspace_fingerprint"],
                    fields["terminal_outcome"],
                    fields["error_code"],
                    fields["error_message"],
                    fields["rollback_path"],
                    fields["staging_path"],
                    fields["package_path"],
                    fields["maintenance_state"],
                    fields["payload_json"],
                    fields["updated_at"],
                    operation_id,
                ),
            )
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        return self._row(operation_id)

    def record_maintenance(self, operation_id: str, state: str) -> OperationRecord:
        return self.update(operation_id, maintenance_state=str(state))

    def list_for_project(self, canonical_project_id: str) -> List[OperationRecord]:
        project = _required_project_id(canonical_project_id)
        rows = self._conn.execute(
            "SELECT operation_id FROM backup_operations WHERE canonical_project_id=?"
            " ORDER BY created_at, operation_id",
            (project,),
        ).fetchall()
        return [self._row(str(row[0])) for row in rows]


def _is_ignorable(path: Path) -> bool:
    return path.name in _IGNORABLE_NAMES or path.name.startswith("._")


def _is_sqlite_sidecar(name: str) -> bool:
    bases = set(_ALLOWED_ROOT_FILES) | {RUNTIME_DB_NAME}
    return any(
        name == base + suffix
        for base in bases
        for suffix in ("-wal", "-shm", "-journal")
    )


def _lstat(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise ProjectBackupError("workspace_member_missing") from exc


def _assert_regular(path: Path, *, symlink_code: str = "workspace_member_symlink") -> None:
    mode = _lstat(path).st_mode
    if stat.S_ISLNK(mode):
        raise ProjectBackupError(symlink_code)
    if not stat.S_ISREG(mode):
        raise ProjectBackupError("workspace_unknown_member")


def _assert_directory(path: Path) -> None:
    mode = _lstat(path).st_mode
    if stat.S_ISLNK(mode):
        raise ProjectBackupError("workspace_member_symlink")
    if not stat.S_ISDIR(mode):
        raise ProjectBackupError("workspace_unknown_member")


def _sqlite_uri(path: Path) -> str:
    return path.resolve().as_uri() + "?mode=ro"


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = conn.execute("PRAGMA table_info(%s)" % table).fetchall()
    except sqlite3.DatabaseError as exc:
        raise ProjectBackupError("sqlite_integrity_failed") from exc
    return {str(row[1]) for row in rows}


def _quick_check(conn: sqlite3.Connection) -> None:
    try:
        row = conn.execute("PRAGMA quick_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise ProjectBackupError("sqlite_integrity_failed") from exc
    if row is None or str(row[0]).lower() != "ok":
        raise ProjectBackupError("sqlite_integrity_failed")


def _open_ro(path: Path) -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(_sqlite_uri(path), uri=True, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        _quick_check(conn)
        return conn
    except ProjectBackupError:
        raise
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise ProjectBackupError("sqlite_integrity_failed") from exc


def _member_rel_paths(workspace: Path) -> List[str]:
    paths: List[str] = []
    for name in sorted(_ALLOWED_ROOT_FILES):
        path = workspace / name
        if path.exists():
            _assert_regular(path)
            paths.append(name)
    runtime = workspace / RUNTIME_DIR_NAME
    if runtime.exists():
        _assert_directory(runtime)
        runtime_db = runtime / RUNTIME_DB_NAME
        if runtime_db.exists():
            _assert_regular(runtime_db)
            paths.append(RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME)
        artifacts = runtime / ARTIFACT_DIR_NAME
        if artifacts.exists():
            _assert_directory(artifacts)
            for child in sorted(artifacts.iterdir(), key=lambda p: p.name.encode("utf-8")):
                if _is_ignorable(child):
                    continue
                _assert_regular(child)
                if child.suffix != ".json" or not _HEX64.match(child.stem):
                    raise ProjectBackupError("artifact_closure_invalid")
                paths.append(
                    RUNTIME_DIR_NAME + "/" + ARTIFACT_DIR_NAME + "/" + child.name
                )
    return sorted(paths, key=lambda value: value.encode("utf-8"))


def workspace_fingerprint(member_bytes: Mapping[str, bytes]) -> str:
    """Compute the stable fingerprint for one verified workspace snapshot."""

    identity = {
        str(member_id): sha256_hex(member_bytes[member_id])
        for member_id in sorted(member_bytes, key=lambda value: value.encode("utf-8"))
    }
    return sha256_hex(canonical_json_bytes(identity))


class WorkspaceSnapshot:
    """Verified member bytes, semantic summary, and stable workspace identity."""

    def __init__(
        self,
        root: Path,
        members: Mapping[str, bytes],
        summary: Mapping[str, Any],
        fingerprint: str,
    ) -> None:
        self.root = root
        self.members = dict(members)
        self.summary = dict(summary)
        self.fingerprint = fingerprint

    @property
    def artifact_hashes(self) -> Tuple[str, ...]:
        return tuple(str(value) for value in self.summary.get("artifact_hashes", ()))


_WorkspaceSnapshot = WorkspaceSnapshot


# Internal split modules intentionally share the complete frozen contract surface.
__all__ = [name for name in globals() if not name.startswith("__")]
