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

from mm_r1.store import Store as R1Store

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

class ProjectBackupManager:
    """Backup, preflight, restore, and atomic rollback for one project."""

    def __init__(
        self,
        root: Union[str, Path],
        canonical_project_id: Optional[str] = None,
        *,
        project_dir: Optional[Union[str, Path]] = None,
        workspace_dir: Optional[Union[str, Path]] = None,
        publication_dir: Optional[Union[str, Path]] = None,
        backup_dir: Optional[Union[str, Path]] = None,
        ledger: Optional[OperationLedger] = None,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        max_archive_members: int = MAX_ARCHIVE_MEMBERS,
        max_member_bytes: int = MAX_MEMBER_BYTES,
        max_archive_bytes: int = MAX_ARCHIVE_BYTES,
        project_name: Optional[str] = None,
        failure_hook: Optional[Callable[[str], None]] = None,
        failure_injector: Optional[Callable[[str], None]] = None,
    ) -> None:
        root_path = Path(root)
        chosen_workspace = project_dir if project_dir is not None else workspace_dir
        if chosen_workspace is not None:
            self.runtime_root = root_path
            self.workspace_dir = Path(chosen_workspace)
            if canonical_project_id is None:
                canonical_project_id = self.workspace_dir.name
        elif canonical_project_id is None:
            self.workspace_dir = root_path
            self.runtime_root = root_path.parent
            canonical_project_id = root_path.name
        else:
            self.runtime_root = root_path
            self.workspace_dir = root_path / canonical_project_id
        self.canonical_project_id = _required_project_id(canonical_project_id)
        self.project_name = project_name if isinstance(project_name, str) and project_name else None
        self.publication_dir = Path(
            publication_dir
            if publication_dir is not None
            else (backup_dir if backup_dir is not None else self.runtime_root / BACKUP_PUBLICATION_DIR_NAME)
        )
        self.ledger = ledger if ledger is not None else OperationLedger(self.runtime_root)
        try:
            wait = float(wait_seconds)
        except (TypeError, ValueError) as exc:
            raise ProjectBackupError("invalid_idempotency_key") from exc
        if wait < 0 or wait > 120:
            raise ProjectBackupError("invalid_idempotency_key")
        self.wait_seconds = wait
        self.max_archive_members = int(max_archive_members)
        self.max_member_bytes = int(max_member_bytes)
        self.max_archive_bytes = int(max_archive_bytes)
        if self.max_archive_members < 1 or self.max_member_bytes < 1 or self.max_archive_bytes < 1:
            raise ProjectBackupError("package_corrupt")
        self.failure_hook = failure_hook if failure_hook is not None else failure_injector

    @property
    def project_dir(self) -> Path:
        return self.workspace_dir

    @property
    def operations_db_path(self) -> Path:
        return self.ledger.path

    def set_failure_hook(self, hook: Optional[Callable[[str], None]]) -> None:
        self.failure_hook = hook

    def _hook(self, point: str) -> None:
        callback = self.failure_hook
        if callback is None:
            return
        try:
            result = callback(str(point))
            if isinstance(result, BaseException):
                raise result
            if result is True:
                raise InjectedFailure(point)
        except ProjectBackupError:
            raise
        except BaseException as exc:
            raise InjectedFailure(point) from exc

    def _record_update(self, operation_id: str, operation_kind: str, **kwargs: Any) -> OperationRecord:
        prefix = "restore" if operation_kind == OP_RESTORE else "backup"
        self._hook(prefix + ".operation_record_submit.before")
        record = self.ledger.update(operation_id, **kwargs)
        self._hook(prefix + ".operation_record_submit.after")
        return record

    def _safe_record_update(self, operation_id: str, **kwargs: Any) -> None:
        try:
            self.ledger.update(operation_id, allow_terminal_reopen=True, **kwargs)
        except (ProjectBackupError, sqlite3.Error):
            pass

    def _gate_event(self, operation_id: str, event: str) -> None:
        try:
            if event == "waiting_for_project":
                self.ledger.update(
                    operation_id,
                    status=STATUS_WAITING_FOR_PROJECT,
                    current_step="正在等待项目空闲",
                    maintenance_state=event,
                )
            else:
                self.ledger.record_maintenance(operation_id, event)
        except (ProjectBackupError, sqlite3.Error):
            # A ledger observation must never retain a project lock.  The
            # operation path still records a terminal error when possible.
            pass

    def _gate(self, operation_id: str) -> ProjectMaintenanceGate:
        return ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(operation_id, event),
        )

    def _validate_workspace_layout(self, workspace: Optional[Path] = None) -> None:
        root = workspace if workspace is not None else self.workspace_dir
        if not root.exists():
            raise ProjectBackupError("workspace_not_found")
        _assert_directory(root)
        for child in sorted(root.iterdir(), key=lambda p: p.name.encode("utf-8")):
            if _is_ignorable(child):
                continue
            if _is_sqlite_sidecar(child.name):
                continue
            if child.name in _ALLOWED_ROOT_FILES:
                _assert_regular(child)
                continue
            if child.name != RUNTIME_DIR_NAME:
                raise ProjectBackupError("workspace_unknown_member")
            _assert_directory(child)
            for nested in sorted(child.iterdir(), key=lambda p: p.name.encode("utf-8")):
                if _is_ignorable(nested):
                    continue
                if _is_sqlite_sidecar(nested.name):
                    continue
                if nested.name == RUNTIME_DB_NAME:
                    _assert_regular(nested)
                elif nested.name == ARTIFACT_DIR_NAME:
                    _assert_directory(nested)
                    for artifact in sorted(nested.iterdir(), key=lambda p: p.name.encode("utf-8")):
                        if _is_ignorable(artifact):
                            continue
                        _assert_regular(artifact)
                        if artifact.suffix == ".tmp":
                            raise ProjectBackupError("artifact_closure_invalid")
                        if artifact.suffix != ".json" or not _HEX64.match(artifact.stem):
                            raise ProjectBackupError("artifact_closure_invalid")
                else:
                    raise ProjectBackupError("workspace_unknown_member")
        if not (root / PROFILE_DB_NAME).exists():
            raise ProjectBackupError("workspace_member_missing")
        if not (root / RUN_BINDING_DB_NAME).exists():
            raise ProjectBackupError("workspace_member_missing")

    @staticmethod
    def _schema_version(conn: sqlite3.Connection, relative_path: str) -> str:
        tables = _table_names(conn)
        name = Path(relative_path).name
        if name == PROFILE_DB_NAME:
            if "profile_store_meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute(
                "SELECT value FROM profile_store_meta WHERE key='schema_version'"
            ).fetchone()
            value = "" if row is None else str(row[0])
            if value != _SUPPORTED_PROFILE_SCHEMA:
                raise ProjectBackupError("unsupported_schema")
            return value
        if name == RUN_BINDING_DB_NAME:
            if "monitoring_run_bindings" not in tables:
                raise ProjectBackupError("unsupported_schema")
            columns = _table_columns(conn, "monitoring_run_bindings")
            if "schema_version" not in columns:
                raise ProjectBackupError("unsupported_schema")
            rows = conn.execute(
                "SELECT DISTINCT schema_version FROM monitoring_run_bindings"
            ).fetchall()
            values = {str(row[0]) for row in rows}
            if values and values != {_SUPPORTED_BINDING_SCHEMA}:
                raise ProjectBackupError("unsupported_schema")
            return _SUPPORTED_BINDING_SCHEMA
        if name == LAUNCH_REGISTRY_DB_NAME:
            if "r7_launch_registry_meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute(
                "SELECT value FROM r7_launch_registry_meta WHERE key='schema_version'"
            ).fetchone()
            value = "" if row is None else str(row[0])
            if value not in _SUPPORTED_LAUNCH_SCHEMAS:
                raise ProjectBackupError("unsupported_schema")
            return value
        if name == RISK_RULE_DB_NAME:
            if "r7_risk_rule_revisions" not in tables:
                raise ProjectBackupError("unsupported_schema")
            return "mm-r7-risk-rule-v1"
        if name == RUNTIME_DB_NAME:
            if "meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            value = "" if row is None else str(row[0])
            if value not in _SUPPORTED_RUNTIME_SCHEMAS:
                raise ProjectBackupError("unsupported_schema")
            required = {"projects", "monitoring_runs", "artifacts", "listing_snapshots"}
            if not required.issubset(tables):
                raise ProjectBackupError("unsupported_schema")
            return value
        raise ProjectBackupError("unsupported_schema")

    def _sqlite_snapshot(self, source: Path, target: Path) -> str:
        _assert_regular(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        source_conn: Optional[sqlite3.Connection] = None
        target_conn: Optional[sqlite3.Connection] = None
        try:
            source_conn = sqlite3.connect(_sqlite_uri(source), uri=True, timeout=10.0)
            source_conn.row_factory = sqlite3.Row
            _quick_check(source_conn)
            target_conn = sqlite3.connect(str(target), timeout=10.0)
            target_conn.row_factory = sqlite3.Row
            source_conn.backup(target_conn)
            # A WAL source can carry the WAL mode bit into the destination
            # header.  Package members intentionally exclude -wal/-shm, so
            # normalize the isolated snapshot to rollback-journal mode before
            # closing it; otherwise a reopened member would need sidecars.
            target_conn.execute("PRAGMA journal_mode=DELETE")
            target_conn.commit()
            _quick_check(target_conn)
        except ProjectBackupError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc
        finally:
            if target_conn is not None:
                target_conn.close()
            if source_conn is not None:
                source_conn.close()
        try:
            verify_conn = _open_ro(target)
            version = self._schema_version(verify_conn, target.name)
            verify_conn.close()
            return version
        except ProjectBackupError:
            raise
        except (sqlite3.Error, OSError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    def _member_bytes(self, workspace: Path) -> Dict[str, bytes]:
        result: Dict[str, bytes] = {}
        for relative in _member_rel_paths(workspace):
            path = workspace / Path(relative)
            _assert_regular(path)
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("workspace_member_missing") from exc
            if len(data) > self.max_member_bytes:
                raise ProjectBackupError("package_corrupt")
            result[relative] = data
        return {key: result[key] for key in sorted(result, key=lambda value: value.encode("utf-8"))}

    def member_bytes(self, workspace: Optional[Path] = None) -> Dict[str, bytes]:
        """Return verified bytes for the selected workspace members."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        return self._member_bytes(target)

    @staticmethod
    def _fingerprint(member_bytes: Mapping[str, bytes]) -> str:
        return workspace_fingerprint(member_bytes)

    @staticmethod
    def _verify_audit_chain(conn: sqlite3.Connection) -> None:
        """Use R1's public verifier as the single chain algorithm."""

        try:
            readonly_store = R1Store.__new__(R1Store)
            readonly_store._conn = conn
            result = readonly_store.verify_audit_chain()
            if not isinstance(result, tuple) or not result or not bool(result[0]):
                raise ProjectBackupError("sqlite_integrity_failed")
        except ProjectBackupError:
            raise
        except (sqlite3.Error, TypeError, ValueError, UnicodeError, AttributeError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    @staticmethod
    def _artifact_hashes(conn: sqlite3.Connection) -> Tuple[str, ...]:
        hashes: set[str] = set()
        tables = _table_names(conn)
        for table in ("artifacts", "listing_snapshots"):
            if table not in tables:
                continue
            columns = _table_columns(conn, table)
            if "content_hash" not in columns:
                raise ProjectBackupError("unsupported_schema")
            rows = conn.execute("SELECT content_hash FROM %s" % table).fetchall()
            for row in rows:
                value = str(row[0])
                if not _HEX64.match(value):
                    raise ProjectBackupError("artifact_closure_invalid")
                hashes.add(value)
        return tuple(sorted(hashes))

    @staticmethod
    def _set_digest(values: Iterable[str]) -> str:
        return sha256_hex(canonical_json_bytes(list(sorted(values))))

    def _summarize_workspace(
        self, workspace: Path, *, project_name_override: Optional[str] = None
    ) -> Dict[str, Any]:
        self._validate_workspace_layout(workspace)
        schema_versions: Dict[str, str] = {}
        project_ids: set[str] = set()
        project_name = project_name_override or self.project_name or self.canonical_project_id
        runs: List[Dict[str, Any]] = []
        run_states: List[str] = []
        mode_counts: Dict[str, int] = {}
        basis_counts: Dict[str, int] = {}
        artifact_hashes: Tuple[str, ...] = tuple()
        publications = continuity_plans = continuity_items = risk_rules = 0
        launch_active = False
        node_attempts_running = 0
        for relative in _member_rel_paths(workspace):
            if relative.endswith(".json"):
                continue
            if relative not in _ALLOWED_ROOT_FILES and relative != RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME:
                continue
            path = workspace / Path(relative)
            if path.name == ARTIFACT_DIR_NAME or relative.endswith("/" + ARTIFACT_DIR_NAME):
                continue
            conn = _open_ro(path)
            try:
                schema_versions[relative] = self._schema_version(conn, relative)
                tables = _table_names(conn)
                # Every authoritative table that carries project_id must
                # point at the route-selected canonical project.  This also
                # covers launch publications and continuity plans/items,
                # whose project columns are easy to miss when counting only
                # the primary launch table.
                for table in sorted(tables):
                    if "project_id" not in _table_columns(conn, table):
                        continue
                    project_ids.update(
                        str(row[0])
                        for row in conn.execute(
                            "SELECT DISTINCT project_id FROM %s" % table
                        ).fetchall()
                    )
                if path.name == RUNTIME_DB_NAME:
                    self._verify_audit_chain(conn)
                    if "projects" in tables:
                        for row in conn.execute(
                            "SELECT project_id, name, is_synthetic FROM projects ORDER BY project_id"
                        ).fetchall():
                            pid = str(row[0])
                            project_ids.add(pid)
                            if pid == self.canonical_project_id and row[1]:
                                project_name = str(row[1])
                            if not bool(row[2]):
                                raise ProjectBackupError("package_identity_mismatch")
                    if "source_revisions" in tables:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM source_revisions"
                            ).fetchall()
                        )
                    if "listing_snapshots" in tables:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM listing_snapshots"
                            ).fetchall()
                        )
                    if "monitoring_runs" in tables:
                        rows = conn.execute(
                            "SELECT project_id, mode, execution_basis, analysis_state, data_cutoff"
                            " FROM monitoring_runs ORDER BY run_id"
                        ).fetchall()
                        for row in rows:
                            project_ids.add(str(row[0]))
                            mode = str(row[1])
                            basis = str(row[2])
                            state = str(row[3])
                            mode_counts[mode] = mode_counts.get(mode, 0) + 1
                            basis_counts[basis] = basis_counts.get(basis, 0) + 1
                            run_states.append(state)
                            runs.append(
                                {
                                    "analysis_state": state,
                                    "data_cutoff": str(row[4]),
                                    "execution_basis": basis,
                                    "mode": mode,
                                }
                            )
                    if "node_attempts" in tables:
                        node_attempts_running = int(
                            conn.execute(
                                "SELECT COUNT(*) FROM node_attempts WHERE status='running'"
                            ).fetchone()[0]
                        )
                    artifact_hashes = self._artifact_hashes(conn)
                elif path.name == LAUNCH_REGISTRY_DB_NAME:
                    if "r7_launch_registry" in tables:
                        columns = _table_columns(conn, "r7_launch_registry")
                        if "project_id" in columns:
                            project_ids.update(
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT DISTINCT project_id FROM r7_launch_registry"
                                ).fetchall()
                            )
                        if "run_state" in columns:
                            launch_states = [
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT run_state FROM r7_launch_registry ORDER BY sequence"
                                ).fetchall()
                            ]
                            launch_active = any(
                                state in {"waiting_start", "running", "stopping"}
                                for state in launch_states
                            )
                    if "r7_result_publications" in tables:
                        publications = int(
                            conn.execute("SELECT COUNT(*) FROM r7_result_publications").fetchone()[0]
                        )
                    if "r7_continuity_plans" in tables:
                        continuity_plans = int(
                            conn.execute("SELECT COUNT(*) FROM r7_continuity_plans").fetchone()[0]
                        )
                    if "r7_continuity_items" in tables:
                        continuity_items = int(
                            conn.execute("SELECT COUNT(*) FROM r7_continuity_items").fetchone()[0]
                        )
                elif path.name == RISK_RULE_DB_NAME:
                    if "r7_risk_rule_revisions" in tables:
                        columns = _table_columns(conn, "r7_risk_rule_revisions")
                        if "project_id" in columns:
                            project_ids.update(
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT DISTINCT project_id FROM r7_risk_rule_revisions"
                                ).fetchall()
                            )
                        risk_rules = int(
                            conn.execute("SELECT COUNT(*) FROM r7_risk_rule_revisions").fetchone()[0]
                        )
                elif path.name == RUN_BINDING_DB_NAME:
                    columns = _table_columns(conn, "monitoring_run_bindings")
                    if "project_id" in columns:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM monitoring_run_bindings"
                            ).fetchall()
                        )
            finally:
                conn.close()
        if project_ids and project_ids != {self.canonical_project_id}:
            raise ProjectBackupError("package_identity_mismatch")
        cutoffs = sorted({item["data_cutoff"] for item in runs if item["data_cutoff"]})
        backup_cutoff = cutoffs[-1] if cutoffs else "未建立监查运行"
        unfinished_states = [
            item["analysis_state"] for item in runs if item["analysis_state"] != "complete"
        ]
        unfinished = bool(unfinished_states or launch_active or node_attempts_running)
        counts = {
            "runs": len(runs),
            "completed_runs": sum(1 for item in runs if item["analysis_state"] == "complete"),
            "unfinished_runs": len(unfinished_states),
            "publications": publications,
            "continuity_plans": continuity_plans,
            "continuity_items": continuity_items,
            "risk_rules": risk_rules,
            "listing_snapshots": 0,
            "artifacts": len(artifact_hashes),
        }
        runtime_db = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime_db.exists():
            conn = _open_ro(runtime_db)
            try:
                if "listing_snapshots" in _table_names(conn):
                    counts["listing_snapshots"] = int(
                        conn.execute("SELECT COUNT(*) FROM listing_snapshots").fetchone()[0]
                    )
            finally:
                conn.close()
        summary: Dict[str, Any] = {
            "project_name": project_name,
            "backup_cutoff": backup_cutoff,
            "mode_summary": {key: mode_counts[key] for key in sorted(mode_counts)},
            "execution_basis_summary": {key: basis_counts[key] for key in sorted(basis_counts)},
            "run_states": sorted(run_states),
            "counts": counts,
            "unfinished_work": unfinished,
            "schema_versions": {
                key: schema_versions[key]
                for key in sorted(schema_versions, key=lambda value: value.encode("utf-8"))
            },
            "artifact_hashes": list(artifact_hashes),
        }
        summary["semantic_digest"] = sha256_hex(
            canonical_json_bytes({key: value for key, value in summary.items() if key != "semantic_digest"})
        )
        return summary

    def summarize_workspace(
        self,
        workspace: Optional[Path] = None,
        *,
        project_name_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return the validated semantic summary for one workspace."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        return self._summarize_workspace(
            target,
            project_name_override=project_name_override,
        )
    def _copy_artifacts(
        self,
        source_workspace: Path,
        staged_workspace: Path,
        artifact_hashes: Sequence[str],
        *,
        emit_hooks: bool,
    ) -> None:
        source_dir = source_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        target_dir = staged_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        if not artifact_hashes:
            return
        _assert_directory(source_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        for content_hash in sorted(artifact_hashes):
            source = source_dir / (content_hash + ".json")
            target = target_dir / source.name
            _assert_regular(source)
            before_stat = _lstat(source)
            if emit_hooks:
                self._hook("backup.artifact_copy.before")
            try:
                payload = source.read_bytes()
                if len(payload) > self.max_member_bytes:
                    raise ProjectBackupError("artifact_closure_invalid")
                target.write_bytes(payload)
                with target.open("rb") as handle:
                    os.fsync(handle.fileno())
            except ProjectBackupError:
                raise
            except OSError as exc:
                raise ProjectBackupError("artifact_closure_invalid") from exc
            after_stat = _lstat(source)
            try:
                after_payload = source.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("artifact_closure_invalid") from exc
            if (
                before_stat.st_size != after_stat.st_size
                or before_stat.st_mtime_ns != after_stat.st_mtime_ns
                or payload != after_payload
                or sha256_hex(payload) != content_hash
                or sha256_hex(target.read_bytes()) != content_hash
            ):
                raise ProjectBackupError("artifact_closure_invalid")
            if emit_hooks:
                self._hook("backup.artifact_copy.after")

    def _snapshot_workspace(
        self,
        operation_id: str,
        *,
        destination: Optional[Path] = None,
        emit_hooks: bool = True,
    ) -> _WorkspaceSnapshot:
        source_workspace = self.workspace_dir
        self._validate_workspace_layout(source_workspace)
        if destination is None:
            destination = self.runtime_root / STAGING_DIR_NAME / operation_id / "workspace"
        if destination.exists():
            raise ProjectBackupError("backup_operation_conflict")
        destination.mkdir(parents=True, exist_ok=True)
        db_map = {
            PROFILE_DB_NAME: source_workspace / PROFILE_DB_NAME,
            RUN_BINDING_DB_NAME: source_workspace / RUN_BINDING_DB_NAME,
            LAUNCH_REGISTRY_DB_NAME: source_workspace / LAUNCH_REGISTRY_DB_NAME,
            RISK_RULE_DB_NAME: source_workspace / RISK_RULE_DB_NAME,
            RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME: source_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        }
        for relative in sorted(db_map, key=lambda value: value.encode("utf-8")):
            source = db_map[relative]
            if not source.exists():
                if relative in {PROFILE_DB_NAME, RUN_BINDING_DB_NAME}:
                    raise ProjectBackupError("workspace_member_missing")
                continue
            target = destination / Path(relative)
            if emit_hooks:
                self._hook("backup.sqlite_snapshot.before")
            self._sqlite_snapshot(source, target)
            if emit_hooks:
                self._hook("backup.sqlite_snapshot.after")
        runtime_source_db = source_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        runtime_stage_db = destination / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        artifact_hashes: Tuple[str, ...] = tuple()
        if runtime_source_db.exists():
            conn = _open_ro(runtime_stage_db)
            try:
                if emit_hooks:
                    self._hook("backup.artifact_set_freeze.before")
                artifact_hashes = self._artifact_hashes(conn)
                if emit_hooks:
                    self._hook("backup.artifact_set_freeze.after")
            finally:
                conn.close()
            source_artifact_dir = source_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
            actual_artifact_files: set[str] = set()
            if source_artifact_dir.exists():
                _assert_directory(source_artifact_dir)
                for child in source_artifact_dir.iterdir():
                    if _is_ignorable(child):
                        continue
                    _assert_regular(child)
                    if child.suffix != ".json" or not _HEX64.match(child.stem):
                        raise ProjectBackupError("artifact_closure_invalid")
                    actual_artifact_files.add(child.stem)
            if actual_artifact_files != set(artifact_hashes):
                raise ProjectBackupError("artifact_closure_invalid")
            self._copy_artifacts(
                source_workspace,
                destination,
                artifact_hashes,
                emit_hooks=emit_hooks,
            )
            if emit_hooks:
                self._hook("backup.artifact_closure_verification.before")
            staged_conn = _open_ro(runtime_stage_db)
            try:
                staged_hashes = self._artifact_hashes(staged_conn)
            finally:
                staged_conn.close()
            for content_hash in staged_hashes:
                file_path = destination / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME / (content_hash + ".json")
                _assert_regular(file_path)
                if sha256_hex(file_path.read_bytes()) != content_hash:
                    raise ProjectBackupError("artifact_closure_invalid")
            if staged_hashes != tuple(sorted(artifact_hashes)):
                raise ProjectBackupError("artifact_closure_invalid")
            if emit_hooks:
                self._hook("backup.artifact_closure_verification.after")
        members = self._member_bytes(destination)
        fingerprint = self._fingerprint(members)
        summary = self._summarize_workspace(
            destination,
            project_name_override=self.project_name,
        )
        return _WorkspaceSnapshot(destination, members, summary, fingerprint)

    def _manifest_content_digest(
        self, manifest: Mapping[str, Any], member_bytes: Mapping[str, bytes]
    ) -> str:
        body = {key: manifest[key] for key in sorted(manifest) if key != "content_digest"}
        payload = canonical_json_bytes(body)
        for relative in sorted(member_bytes, key=lambda value: value.encode("utf-8")):
            payload += member_bytes[relative]
        return sha256_hex(payload)

    def _build_manifest(self, snapshot: _WorkspaceSnapshot) -> Dict[str, Any]:
        if self.failure_hook is not None:
            self._hook("backup.manifest_generation.before")
        descriptors = [
            {
                "path": "members/" + relative,
                "size": len(snapshot.members[relative]),
                "sha256": sha256_hex(snapshot.members[relative]),
            }
            for relative in sorted(snapshot.members, key=lambda value: value.encode("utf-8"))
        ]
        artifact_hashes = list(snapshot.summary.get("artifact_hashes", []))
        manifest: Dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "canonical_project_id": self.canonical_project_id,
            "project_name": str(snapshot.summary.get("project_name", self.canonical_project_id)),
            "backup_cutoff": str(snapshot.summary.get("backup_cutoff", "未建立监查运行")),
            "members": descriptors,
            "artifact_closure": {
                "content_hashes": artifact_hashes,
                "count": len(artifact_hashes),
                "set_digest": self._set_digest(artifact_hashes),
            },
            "project_summary": dict(snapshot.summary),
            "source_workspace_fingerprint": snapshot.fingerprint,
        }
        manifest["content_digest"] = self._manifest_content_digest(manifest, snapshot.members)
        if self.failure_hook is not None:
            self._hook("backup.manifest_generation.after")
        return manifest

    @staticmethod
    def _zip_info(name: str) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        info.create_system = 3
        info.create_version = 20
        info.extract_version = 20
        info.extra = b""
        info.comment = b""
        info.external_attr = 0o100644 << 16
        info.internal_attr = 0
        info.flag_bits = 0x800
        return info

    def _write_package(
        self,
        operation_id: str,
        manifest: Mapping[str, Any],
        member_bytes: Mapping[str, bytes],
    ) -> Tuple[str, Path]:
        self.publication_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.runtime_root / ("." + operation_id + ".mmbackup.tmp")
        package_bytes: bytes
        try:
            if self.failure_hook is not None:
                self._hook("backup.package_generation.before")
            manifest_bytes = canonical_json_bytes(dict(manifest)) + b"\n"
            with zipfile.ZipFile(
                str(temp_path), mode="w", compression=zipfile.ZIP_STORED, allowZip64=False
            ) as archive:
                archive.writestr(self._zip_info("manifest.json"), manifest_bytes)
                for relative in sorted(member_bytes, key=lambda value: value.encode("utf-8")):
                    archive.writestr(
                        self._zip_info("members/" + relative), member_bytes[relative]
                    )
            with temp_path.open("rb") as handle:
                os.fsync(handle.fileno())
                package_bytes = handle.read()
            package_id = sha256_hex(package_bytes)
            with temp_path.open("rb") as handle:
                if handle.read() != package_bytes:
                    raise ProjectBackupError("backup_package_publish_failed")
            if self.failure_hook is not None:
                self._hook("backup.package_generation.after")
        except ProjectBackupError:
            raise
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            raise ProjectBackupError("backup_package_publish_failed") from exc
        published = self.publication_dir / (package_id + BACKUP_SUFFIX)
        if published.exists():
            _assert_regular(published)
            try:
                existing = published.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("backup_package_publish_failed") from exc
            if existing != package_bytes:
                raise ProjectBackupError("backup_package_publish_failed")
            try:
                temp_path.unlink()
            except OSError:
                pass
            return package_id, published
        try:
            if self.failure_hook is not None:
                self._hook("backup.package_publish.before")
            os.replace(str(temp_path), str(published))
            self._fsync_dir(self.publication_dir)
            if self.failure_hook is not None:
                self._hook("backup.package_publish.after")
        except ProjectBackupError:
            raise
        except OSError as exc:
            raise ProjectBackupError("backup_package_publish_failed") from exc
        return package_id, published

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        try:
            fd = os.open(str(directory), os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    @staticmethod
    def _cleanup_path(path: Optional[Path]) -> None:
        if path is None or not path.exists():
            return
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(str(path))
            else:
                path.unlink()
        except OSError:
            pass

    def _manifest_from_package(self, package_path: Path) -> Dict[str, Any]:
        try:
            with zipfile.ZipFile(str(package_path), "r") as archive:
                raw = archive.read("manifest.json")
            manifest = json.loads(raw.decode("utf-8"))
        except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            raise ProjectBackupError("package_corrupt") from exc
        if not isinstance(manifest, dict):
            raise ProjectBackupError("package_corrupt")
        return manifest

    def _package_path(self, package: Union[str, Path, PreflightResult]) -> Path:
        if isinstance(package, PreflightResult):
            return package.package_path
        path = Path(package)
        if not path.exists() and path.name and not path.suffix:
            path = self.publication_dir / (path.name + BACKUP_SUFFIX)
        if not path.exists():
            raise ProjectBackupError("package_corrupt")
        _assert_regular(path)
        try:
            if path.stat().st_size > self.max_archive_bytes:
                raise ProjectBackupError("package_corrupt")
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        return path

    def _backup_result(self, record: OperationRecord) -> BackupResult:
        path = Path(record.package_path) if record.package_path else None
        manifest: Dict[str, Any] = {}
        if path is not None and path.exists():
            try:
                manifest = self._manifest_from_package(path)
            except ProjectBackupError:
                manifest = {}
        return BackupResult(
            operation=record,
            package_id=record.package_id,
            package_path=path,
            source_workspace_fingerprint=record.source_workspace_fingerprint,
            manifest=manifest,
        )

    def _restore_result_from_record(self, record: OperationRecord) -> RestoreResult:
        payload = dict(record.payload)
        return RestoreResult(
            operation=record,
            result_label=str(payload.get("result_label", "恢复完成")),
            project_name=str(
                payload.get("project_name", self.project_name or self.canonical_project_id)
            ),
            restored_cutoff_label=str(payload.get("restored_cutoff_label", "")),
            verification_summary=str(payload.get("verification_summary", "")),
            next_action_label=str(
                payload.get("next_action_label", "继续查看监查结果")
            ),
            rollback_path=Path(record.rollback_path) if record.rollback_path else None,
        )
    def _wait_for_replayed_operation(
        self,
        record: OperationRecord,
        terminal_statuses: Sequence[str],
        *,
        timeout_seconds: float = 120.0,
    ) -> OperationRecord:
        """Join an operation already owned by another process/thread."""

        deadline = time.monotonic() + min(max(float(timeout_seconds), 0.0), 120.0)
        terminal = set(terminal_statuses)
        current = record
        while current.status not in terminal:
            if time.monotonic() >= deadline:
                return current
            time.sleep(0.01)
            current = self.ledger.get(record.operation_id)
        return current


    def snapshot_workspace(
        self,
        operation_id: str,
        *,
        destination: Optional[Path] = None,
        emit_hooks: bool = False,
    ) -> WorkspaceSnapshot:
        """Create a closure-verified workspace snapshot through the stable seam."""

        if destination is None:
            snapshot = self._current_snapshot(operation_id)
            if snapshot is None:
                raise ProjectBackupError("workspace_not_found")
            return snapshot
        return self._snapshot_workspace(
            operation_id,
            destination=destination,
            emit_hooks=emit_hooks,
        )

    current_workspace_snapshot = snapshot_workspace

    def _current_snapshot(self, operation_id: str) -> Optional[_WorkspaceSnapshot]:
        if not self.workspace_dir.exists():
            return None
        parent = Path(tempfile.mkdtemp(prefix=".mmbackup-check-", dir=str(self.runtime_root)))
        destination = parent / "workspace"
        try:
            snapshot = self._snapshot_workspace(
                operation_id,
                destination=destination,
                emit_hooks=False,
            )
        finally:
            self._cleanup_path(parent)
        return snapshot


    def backup(
        self,
        idempotency_key: Optional[str] = None,
        *,
        operation_id: Optional[str] = None,
        reserved_operation_id: Optional[str] = None,
    ) -> BackupResult:
        key = _required_key(idempotency_key) if idempotency_key is not None else "backup-" + uuid.uuid4().hex
        try:
            record = self.ledger.create_or_replay(OP_BACKUP, key, self.canonical_project_id)
        except MaintenanceGateError as exc:
            raise ProjectBackupError(exc.code, exc.message) from exc
        reserved_owner = False
        if reserved_operation_id is not None:
            if (
                not isinstance(reserved_operation_id, str)
                or _SAFE_OPERATION_ID.fullmatch(reserved_operation_id) is None
                or not record.replayed
                or record.operation_id != reserved_operation_id
                or (
                    operation_id is not None
                    and operation_id != reserved_operation_id
                )
            ):
                raise ProjectBackupError("backup_operation_conflict")
            if record.status not in {STATUS_AVAILABLE, STATUS_FAILED}:
                record = dataclass_replace(record, replayed=False)
                reserved_owner = True
        op_id = operation_id or record.operation_id
        stage_parent = self.runtime_root / STAGING_DIR_NAME / op_id
        stage_workspace = stage_parent / "workspace"
        temp_package = self.runtime_root / ("." + op_id + ".mmbackup.tmp")
        if record.replayed and record.status not in {STATUS_AVAILABLE, STATUS_FAILED}:
            joined = self._wait_for_replayed_operation(
                record,
                (STATUS_AVAILABLE, STATUS_FAILED),
            )
            if joined.status in {STATUS_AVAILABLE, STATUS_FAILED}:
                return self._backup_result(joined)
            if stage_parent.exists():
                raise ProjectBackupError("backup_operation_conflict")
            record = joined
        if record.replayed and record.status == STATUS_AVAILABLE:
            gate = self._gate(record.operation_id)
            try:
                with gate.exclusive():
                    current = self._current_snapshot(record.operation_id)
                    if current is None or current.fingerprint != record.source_workspace_fingerprint:
                        raise ProjectBackupError("backup_operation_conflict")
                    if record.package_path is None or not Path(record.package_path).is_file():
                        raise ProjectBackupError("backup_package_publish_failed")
                    return self._backup_result(record)
            except ProjectBusyError as exc:
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_FAILED,
                    error_code=exc.code,
                    error_message=exc.message,
                )
                raise ProjectBackupError(exc.code, exc.message) from exc
        if record.replayed and record.status == STATUS_FAILED and not record.source_workspace_fingerprint:
            return self._backup_result(record)
        try:
            with self._gate(record.operation_id).exclusive():
                if reserved_owner:
                    latest = self.ledger.get(record.operation_id)
                    if latest.status in {STATUS_AVAILABLE, STATUS_FAILED}:
                        return self._backup_result(latest)
                    record = latest
                    self._cleanup_path(stage_parent)
                    if temp_package.exists():
                        self._cleanup_path(temp_package)
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_COLLECTING,
                    progress_percent=PROGRESS_IDENTITY_CONFIRMED,
                    current_step="项目身份与状态已确认",
                )
                snapshot = self._snapshot_workspace(
                    record.operation_id,
                    destination=stage_workspace,
                    emit_hooks=True,
                )
                if (
                    record.source_workspace_fingerprint is not None
                    and record.source_workspace_fingerprint != snapshot.fingerprint
                ):
                    raise ProjectBackupError("backup_operation_conflict")
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_SNAPSHOTTING,
                    progress_percent=PROGRESS_SNAPSHOT_COMPLETE,
                    current_step="项目副本已准备",
                    source_workspace_fingerprint=snapshot.fingerprint,
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING,
                    progress_percent=PROGRESS_ARTIFACT_CLOSURE_COMPLETE,
                    current_step="监查结果已核对",
                )
                manifest = self._build_manifest(snapshot)
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="成员核验完成",
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_PACKAGING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="备份文件正在生成",
                )
                package_id, published = self._write_package(
                    record.operation_id, manifest, snapshot.members
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_PACKAGING,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="最终对账完成",
                )
                final_record = self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_AVAILABLE,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="已可下载",
                    package_id=package_id,
                    source_workspace_fingerprint=snapshot.fingerprint,
                    terminal_outcome=STATUS_AVAILABLE,
                    package_path=str(published),
                    staging_path="",
                    payload={"manifest": manifest},
                )
                self._cleanup_path(stage_parent)
                return BackupResult(
                    operation=final_record,
                    package_id=package_id,
                    package_path=published,
                    source_workspace_fingerprint=snapshot.fingerprint,
                    manifest=manifest,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            if temp_package.exists():
                self._cleanup_path(temp_package)
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code="sqlite_integrity_failed",
                error_message=_ERROR_MESSAGES["sqlite_integrity_failed"],
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    create_backup = backup
    export_backup = backup
    export = backup

    def _validate_archive_names(self, infos: Sequence[zipfile.ZipInfo]) -> None:
        if len(infos) > self.max_archive_members:
            raise ProjectBackupError("package_corrupt")
        names: set[str] = set()
        total = 0
        for info in infos:
            name = str(info.filename)
            if not name or "\x00" in name or "\\" in name:
                raise ProjectBackupError("package_corrupt")
            if not name.isascii():
                raise ProjectBackupError("package_corrupt")
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
                raise ProjectBackupError("package_corrupt")
            if name in names:
                raise ProjectBackupError("package_corrupt")
            names.add(name)
            if info.is_dir() or name.endswith("/"):
                raise ProjectBackupError("package_corrupt")
            mode = (int(info.external_attr) >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ProjectBackupError("package_corrupt")
            if info.compress_type != zipfile.ZIP_STORED:
                raise ProjectBackupError("package_corrupt")
            if info.date_time != (1980, 1, 1, 0, 0, 0):
                raise ProjectBackupError("package_corrupt")
            if info.create_system != 3 or info.create_version != 20 or info.extract_version != 20:
                raise ProjectBackupError("package_corrupt")
            if info.extra or info.comment:
                raise ProjectBackupError("package_corrupt")
            if info.file_size < 0 or info.file_size > self.max_member_bytes:
                raise ProjectBackupError("package_corrupt")
            total += int(info.file_size)
            if total > self.max_archive_bytes:
                raise ProjectBackupError("package_corrupt")
        if "manifest.json" not in names:
            raise ProjectBackupError("package_corrupt")

    def _inspect_archive(
        self,
        operation_id: str,
        package_path: Path,
    ) -> Tuple[Dict[str, Any], Path, Dict[str, bytes], str]:
        try:
            archive_bytes = package_path.read_bytes()
            package_id = sha256_hex(archive_bytes)
            archive = zipfile.ZipFile(str(package_path), "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ProjectBackupError("package_corrupt") from exc
        try:
            infos = archive.infolist()
            self._validate_archive_names(infos)
            manifest_raw = archive.read("manifest.json")
            try:
                manifest = json.loads(manifest_raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProjectBackupError("package_corrupt") from exc
            if not isinstance(manifest, dict):
                raise ProjectBackupError("package_corrupt")
            if set(manifest) != set(_SUPPORTED_MANIFEST_KEYS):
                raise ProjectBackupError("package_corrupt")
            if manifest_raw != canonical_json_bytes(manifest) + b"\n":
                raise ProjectBackupError("package_corrupt")
            if manifest.get("contract_version") != CONTRACT_VERSION:
                raise ProjectBackupError("unsupported_contract")
            if manifest.get("schema_version") != SCHEMA_VERSION:
                raise ProjectBackupError("unsupported_contract")
            package_project = manifest.get("canonical_project_id")
            if not isinstance(package_project, str) or package_project != self.canonical_project_id:
                raise ProjectBackupError("package_identity_mismatch")
            descriptors = manifest.get("members")
            if not isinstance(descriptors, list) or not descriptors:
                raise ProjectBackupError("package_corrupt")
            descriptor_paths: List[str] = []
            for item in descriptors:
                if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
                    raise ProjectBackupError("package_corrupt")
                path = item.get("path")
                size = item.get("size")
                digest = item.get("sha256")
                if (
                    not isinstance(path, str)
                    or not path.startswith("members/")
                    or path == "members/"
                    or not isinstance(size, int)
                    or isinstance(size, bool)
                    or size < 0
                    or size > self.max_member_bytes
                    or not isinstance(digest, str)
                    or not _HEX64.match(digest)
                ):
                    raise ProjectBackupError("package_corrupt")
                relative = path[len("members/") :]
                if "\\" in relative or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
                    raise ProjectBackupError("package_corrupt")
                descriptor_paths.append(path)
            if descriptor_paths != sorted(set(descriptor_paths), key=lambda value: value.encode("utf-8")):
                raise ProjectBackupError("package_corrupt")
            names = [info.filename for info in infos if info.filename != "manifest.json"]
            if names != descriptor_paths or set(names) != set(descriptor_paths):
                raise ProjectBackupError("package_corrupt")
            stage_parent = self.runtime_root / STAGING_DIR_NAME / operation_id
            if stage_parent.exists():
                raise ProjectBackupError("backup_operation_conflict")
            stage_workspace = stage_parent / "workspace"
            stage_workspace.mkdir(parents=True, exist_ok=False)
            if self.failure_hook is not None:
                self._hook("preflight.unpack.before")
            members: Dict[str, bytes] = {}
            for path in descriptor_paths:
                info = archive.getinfo(path)
                raw = archive.read(path)
                relative = path[len("members/") :]
                expected = next(item for item in descriptors if item["path"] == path)
                if len(raw) != expected["size"] or sha256_hex(raw) != expected["sha256"]:
                    raise ProjectBackupError("package_corrupt")
                target = stage_workspace / Path(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                members[relative] = raw
            if self.failure_hook is not None:
                self._hook("preflight.unpack.after")
            if self._manifest_content_digest(manifest, members) != manifest.get("content_digest"):
                raise ProjectBackupError("manifest_semantic_mismatch")
            if self.failure_hook is not None:
                self._hook("preflight.member_verification.before")
            actual_fp = self._fingerprint(members)
            if actual_fp != manifest.get("source_workspace_fingerprint"):
                raise ProjectBackupError("manifest_semantic_mismatch")
            if self.failure_hook is not None:
                self._hook("preflight.member_verification.after")
            return manifest, stage_parent, members, package_id
        finally:
            archive.close()

    def verify_artifact_closure(
        self,
        workspace: Path,
        summary: Mapping[str, Any],
    ) -> None:
        """Verify the exact registered-to-file artifact closure."""

        self._verify_artifact_closure(workspace, summary)

    def artifact_closure(self, workspace: Optional[Path] = None) -> Dict[str, bytes]:
        """Return verified content-addressed artifact bytes keyed by hash."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        summary = self._summarize_workspace(target)
        self._verify_artifact_closure(target, summary)
        members = self._member_bytes(target)
        result: Dict[str, bytes] = {}
        prefix = RUNTIME_DIR_NAME + "/" + ARTIFACT_DIR_NAME + "/"
        for relative, data in members.items():
            if relative.startswith(prefix):
                result[Path(relative).stem] = data
        return {key: result[key] for key in sorted(result)}
    def _verify_artifact_closure(self, workspace: Path, summary: Mapping[str, Any]) -> None:
        runtime_db = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        expected_hashes = tuple(summary.get("artifact_hashes", ()))
        if not runtime_db.exists():
            if expected_hashes:
                raise ProjectBackupError("artifact_closure_invalid")
            return
        artifact_dir = workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        if expected_hashes:
            _assert_directory(artifact_dir)
        actual_files: set[str] = set()
        if artifact_dir.exists():
            _assert_directory(artifact_dir)
            for child in artifact_dir.iterdir():
                if _is_ignorable(child):
                    continue
                _assert_regular(child)
                if child.suffix != ".json" or not _HEX64.match(child.stem):
                    raise ProjectBackupError("artifact_closure_invalid")
                actual_files.add(child.stem)
                if sha256_hex(child.read_bytes()) != child.stem:
                    raise ProjectBackupError("artifact_closure_invalid")
        if actual_files != set(expected_hashes):
            raise ProjectBackupError("artifact_closure_invalid")

    def _verify_workspace(
        self,
        workspace: Path,
        manifest: Mapping[str, Any],
        *,
        verify_manifest_summary: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        self._validate_workspace_layout(workspace)
        members = self._member_bytes(workspace)
        fingerprint = self._fingerprint(members)
        if manifest.get("source_workspace_fingerprint") != fingerprint:
            raise ProjectBackupError("manifest_semantic_mismatch")
        summary = self._summarize_workspace(
            workspace,
            project_name_override=str(manifest.get("project_name", self.canonical_project_id)),
        )
        self._verify_artifact_closure(workspace, summary)
        closure = manifest.get("artifact_closure")
        expected_hashes = tuple(summary.get("artifact_hashes", ()))
        if not isinstance(closure, dict) or set(closure) != {"content_hashes", "count", "set_digest"}:
            raise ProjectBackupError("manifest_semantic_mismatch")
        if (
            tuple(closure.get("content_hashes", ())) != expected_hashes
            or closure.get("count") != len(expected_hashes)
            or closure.get("set_digest") != self._set_digest(expected_hashes)
        ):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if verify_manifest_summary and summary != manifest.get("project_summary"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if summary.get("project_name") != manifest.get("project_name"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if summary.get("backup_cutoff") != manifest.get("backup_cutoff"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        return summary, members, fingerprint

    def _current_state(self, operation_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        snapshot = self._current_snapshot(operation_id)
        if snapshot is None:
            return None, None
        return snapshot.summary, snapshot.fingerprint

    @staticmethod
    def _impact(current: Optional[Mapping[str, Any]], target: Mapping[str, Any]) -> Dict[str, int]:
        current_counts = dict((current or {}).get("counts", {}))
        target_counts = dict(target.get("counts", {}))
        result: Dict[str, int] = {}
        for key in ("runs", "publications", "risk_rules", "continuity_plans"):
            difference = int(current_counts.get(key, 0)) - int(target_counts.get(key, 0))
            if difference > 0:
                result[key] = difference
        return result

    def _preflight_result_from_record(self, record: OperationRecord, package_path: Path) -> PreflightResult:
        payload = dict(record.payload)
        try:
            return PreflightResult(
                operation=record,
                package_id=str(payload["package_id"]),
                package_path=package_path,
                canonical_project_id=self.canonical_project_id,
                project_name=str(payload["project_name"]),
                backup_cutoff_label=str(payload["backup_cutoff_label"]),
                current_cutoff_label=str(payload["current_cutoff_label"]),
                decision=str(payload["decision"]),
                decision_label=str(payload["decision_label"]),
                impact_summary=str(payload["impact_summary"]),
                items_preserved=tuple(str(value) for value in payload.get("items_preserved", [])),
                items_rolled_back=dict(payload.get("items_rolled_back", {})),
                recommended_action=str(payload["recommended_action"]),
                confirmation_required=bool(payload["confirmation_required"]),
                unfinished_work_notice=payload.get("unfinished_work_notice"),
                source_workspace_fingerprint=str(payload["source_workspace_fingerprint"]),
                current_workspace_fingerprint=payload.get("current_workspace_fingerprint"),
                staging_path=Path(payload["staging_path"]) if payload.get("staging_path") else None,
                manifest=dict(payload.get("manifest", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    def preflight(
        self,
        package: Union[str, Path, PreflightResult],
        idempotency_key: Optional[str] = None,
        *,
        operation_id: Optional[str] = None,
    ) -> PreflightResult:
        package_path = self._package_path(package)
        try:
            package_id = sha256_hex(package_path.read_bytes())
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        key = _required_key(idempotency_key) if idempotency_key is not None else "preflight-" + package_id
        record = self.ledger.create_or_replay(
            OP_PREFLIGHT,
            key,
            self.canonical_project_id,
            package_id=package_id,
        )
        if record.replayed and record.status == STATUS_READY_FOR_CONFIRMATION and record.payload:
            return self._preflight_result_from_record(record, package_path)
        op_id = operation_id or record.operation_id
        stage_parent = self.runtime_root / STAGING_DIR_NAME / op_id
        try:
            with self._gate(record.operation_id).shared():
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_INSPECTING,
                    progress_percent=PROGRESS_REQUEST_ACCEPTED,
                    current_step="正在检查备份内容",
                )
                manifest, stage_parent, members, actual_package_id = self._inspect_archive(
                    record.operation_id, package_path
                )
                if actual_package_id != package_id:
                    raise ProjectBackupError("package_corrupt")
                summary, _, source_fp = self._verify_workspace(
                    stage_parent / "workspace", manifest, verify_manifest_summary=True
                )
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.before")
                # A second pass catches a staging directory that gained an
                # unlisted file between extraction and verification.
                self._verify_workspace(stage_parent / "workspace", manifest, verify_manifest_summary=True)
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.after")
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING_MEMBERS,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="恢复前检查已完成",
                )
                current_summary, current_fp = self._current_state(record.operation_id)
                if current_summary is not None and current_summary.get("project_name") == self.canonical_project_id and self.project_name:
                    current_summary = dict(current_summary)
                    current_summary["project_name"] = self.project_name
                if self._existing_rollbacks():
                    decision = "blocked"
                    decision_label = "无法恢复"
                    confirmation_required = False
                    recommended = "请先核对已有回退版本"
                elif current_fp is not None and current_fp == source_fp and current_summary == summary:
                    decision = "already_current"
                    decision_label = "已是当前版本"
                    confirmation_required = False
                    recommended = "继续查看当前监查结果"
                else:
                    older = bool(
                        current_summary is not None
                        and str(summary.get("backup_cutoff", "")) < str(current_summary.get("backup_cutoff", ""))
                    )
                    decision = "rollback_required" if older else "ready"
                    decision_label = "需确认回退" if older else "可恢复"
                    confirmation_required = True
                    recommended = "保留当前状态，并先导出一份当前备份" if older else "确认后恢复此备份"
                impact = self._impact(current_summary, summary)
                impact_text = "无预计回退事项" if not impact else "、".join(
                    "%s %d 项" % (key, value) for key, value in sorted(impact.items())
                )
                unfinished_notice = (
                    "此备份包含未完成的监查任务，恢复后仍需继续处理"
                    if summary.get("unfinished_work")
                    else None
                )
                payload: Dict[str, Any] = {
                    "package_id": package_id,
                    "project_name": str(manifest["project_name"]),
                    "backup_cutoff_label": str(manifest["backup_cutoff"]),
                    "current_cutoff_label": str(
                        (current_summary or {}).get("backup_cutoff", "当前项目尚未建立")
                    ),
                    "decision": decision,
                    "decision_label": decision_label,
                    "impact_summary": impact_text,
                    "items_preserved": ["监查结果", "风险规则", "受试者历程", "中心汇总"],
                    "items_rolled_back": impact,
                    "recommended_action": recommended,
                    "confirmation_required": confirmation_required,
                    "unfinished_work_notice": unfinished_notice,
                    "source_workspace_fingerprint": source_fp,
                    "current_workspace_fingerprint": current_fp,
                    "staging_path": str(stage_parent),
                    "manifest": dict(manifest),
                }
                final_status = STATUS_READY_FOR_CONFIRMATION
                final_record = self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=final_status,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="已完成恢复预检",
                    package_id=package_id,
                    source_workspace_fingerprint=source_fp,
                    staging_path=str(stage_parent),
                    payload=payload,
                )
                return PreflightResult(
                    operation=final_record,
                    package_id=package_id,
                    package_path=package_path,
                    canonical_project_id=self.canonical_project_id,
                    project_name=str(manifest["project_name"]),
                    backup_cutoff_label=str(manifest["backup_cutoff"]),
                    current_cutoff_label=str(
                        (current_summary or {}).get("backup_cutoff", "当前项目尚未建立")
                    ),
                    decision=decision,
                    decision_label=decision_label,
                    impact_summary=impact_text,
                    items_preserved=("监查结果", "风险规则", "受试者历程", "中心汇总"),
                    items_rolled_back=impact,
                    recommended_action=recommended,
                    confirmation_required=confirmation_required,
                    unfinished_work_notice=unfinished_notice,
                    source_workspace_fingerprint=source_fp,
                    current_workspace_fingerprint=current_fp,
                    staging_path=stage_parent,
                    manifest=manifest,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code="package_corrupt", error_message=_ERROR_MESSAGES["package_corrupt"])
            self._cleanup_path(stage_parent)
            raise ProjectBackupError("package_corrupt") from exc

    restore_preflight = preflight
    inspect = preflight

    def _existing_rollbacks(self) -> List[Path]:
        if not self.runtime_root.exists():
            return []
        prefix = ".rollback-" + sha256_hex(self.canonical_project_id.encode("utf-8"))[:24] + "-"
        result: List[Path] = []
        for child in self.runtime_root.iterdir():
            if child.name.startswith(prefix) and child.name != prefix:
                result.append(child)
        return sorted(result, key=lambda path: path.name)

    def _active_project_work(self, workspace: Path) -> bool:
        launch = workspace / LAUNCH_REGISTRY_DB_NAME
        if launch.exists():
            conn = _open_ro(launch)
            try:
                if "r7_launch_registry" in _table_names(conn):
                    columns = _table_columns(conn, "r7_launch_registry")
                    if "run_state" in columns:
                        row = conn.execute(
                            "SELECT 1 FROM r7_launch_registry WHERE run_state IN"
                            " ('waiting_start','running','stopping') LIMIT 1"
                        ).fetchone()
                        if row is not None:
                            return True
            finally:
                conn.close()
        runtime = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime.exists():
            conn = _open_ro(runtime)
            try:
                tables = _table_names(conn)
                if "node_attempts" in tables:
                    row = conn.execute(
                        "SELECT 1 FROM node_attempts WHERE status='running' LIMIT 1"
                    ).fetchone()
                    if row is not None:
                        return True
                if "monitoring_runs" in tables:
                    row = conn.execute(
                        "SELECT 1 FROM monitoring_runs WHERE analysis_state IN"
                        " ('running','preparing') LIMIT 1"
                    ).fetchone()
                    if row is not None:
                        return True
            finally:
                conn.close()
        return False

    def _probe_transactions(self, workspace: Path) -> None:
        for relative in _member_rel_paths(workspace):
            if relative.endswith("/" + ARTIFACT_DIR_NAME) or "/" in relative and relative.split("/")[-1].endswith(".json"):
                continue
            path = workspace / Path(relative)
            conn: Optional[sqlite3.Connection] = None
            try:
                conn = sqlite3.connect(str(path), timeout=0.0, isolation_level=None)
                conn.execute("PRAGMA busy_timeout=0")
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError as exc:
                if conn is not None:
                    try:
                        conn.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                raise ProjectBackupError("project_busy_retry_later") from exc
            except sqlite3.Error as exc:
                raise ProjectBackupError("sqlite_integrity_failed") from exc
            finally:
                if conn is not None:
                    conn.close()

    def _quiesce(self) -> None:
        if self._active_project_work(self.workspace_dir):
            raise ProjectBackupError("project_busy_retry_later")
        self._probe_transactions(self.workspace_dir)

    def _verify_live_workspace(
        self, manifest: Mapping[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        if self.failure_hook is not None:
            self._hook("restore.live_reopen.before")
        summary, members, fingerprint = self._verify_workspace(
            self.workspace_dir, manifest, verify_manifest_summary=True
        )
        # Opening each database again after the verification pass makes the
        # close/reopen invariant explicit rather than relying on one connection.
        for relative in _member_rel_paths(self.workspace_dir):
            if relative.endswith(".json"):
                continue
            conn = _open_ro(self.workspace_dir / Path(relative))
            conn.close()
        if self.failure_hook is not None:
            self._hook("restore.live_reopen.after")
        if self.failure_hook is not None:
            self._hook("restore.identity_verification.before")
        if manifest.get("canonical_project_id") != self.canonical_project_id:
            raise ProjectBackupError("package_identity_mismatch")
        if self.failure_hook is not None:
            self._hook("restore.identity_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.artifact_verification.before")
        self._verify_artifact_closure(self.workspace_dir, summary)
        if self.failure_hook is not None:
            self._hook("restore.artifact_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.publication_verification.before")
        if summary.get("counts", {}).get("publications") != manifest.get("project_summary", {}).get("counts", {}).get("publications"):
            raise ProjectBackupError("restore_verification_failed")
        if self.failure_hook is not None:
            self._hook("restore.publication_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.continuity_verification.before")
        if summary.get("counts", {}).get("continuity_plans") != manifest.get("project_summary", {}).get("counts", {}).get("continuity_plans"):
            raise ProjectBackupError("restore_verification_failed")
        if self.failure_hook is not None:
            self._hook("restore.continuity_verification.after")
        return summary, members, fingerprint

    def _verify_workspace_independent(
        self, workspace: Path
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        """Reopen and verify a live workspace without manifest self-reporting.

        Manual rollback targets the older live version, so it cannot be checked
        against the newer restore manifest.  It still must pass the same
        schema, identity, artifact-closure, and SQLite reopen checks.
        """

        self._validate_workspace_layout(workspace)
        members = self._member_bytes(workspace)
        fingerprint = self._fingerprint(members)
        summary = self._summarize_workspace(workspace, project_name_override=self.project_name)
        self._verify_artifact_closure(workspace, summary)
        for relative in _member_rel_paths(workspace):
            if relative.endswith(".json"):
                continue
            conn = _open_ro(workspace / Path(relative))
            conn.close()
        return summary, members, fingerprint

    def _rollback_after_failure(
        self,
        operation_id: str,
        rollback_path: Optional[Path],
        staging_parent: Path,
        *,
        old_live_moved: bool,
    ) -> bool:
        if not old_live_moved or rollback_path is None or not rollback_path.exists():
            return True
        try:
            self._safe_record_update(
                operation_id,
                status=STATUS_ROLLBACK_IN_PROGRESS,
                current_step="正在恢复原项目版本",
            )
            self._hook("restore.rollback.before")
            failed_live = staging_parent / "failed-live"
            if self.workspace_dir.exists():
                if failed_live.exists():
                    self._cleanup_path(failed_live)
                os.replace(str(self.workspace_dir), str(failed_live))
            os.replace(str(rollback_path), str(self.workspace_dir))
            self._fsync_dir(self.runtime_root)
            self._hook("restore.rollback.after")
            return True
        except BaseException:
            return False

    def restore(
        self,
        package: Union[str, Path, PreflightResult],
        idempotency_key: Optional[str] = None,
        *,
        confirmation: bool = False,
        confirmed: Optional[bool] = None,
        preflight_result: Optional[PreflightResult] = None,
        operation_id: Optional[str] = None,
        reserved_operation_id: Optional[str] = None,
    ) -> RestoreResult:
        if confirmed is not None:
            confirmation = bool(confirmed)
        package_path = self._package_path(package)
        try:
            package_id = sha256_hex(package_path.read_bytes())
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        key = _required_key(idempotency_key) if idempotency_key is not None else "restore-" + package_id
        record = self.ledger.create_or_replay(
            OP_RESTORE,
            key,
            self.canonical_project_id,
            package_id=package_id,
            initial_status=STATUS_CONFIRMED,
        )
        reserved_owner = False
        if reserved_operation_id is not None:
            if (
                not isinstance(reserved_operation_id, str)
                or _SAFE_OPERATION_ID.fullmatch(reserved_operation_id) is None
                or not record.replayed
                or record.operation_id != reserved_operation_id
                or (
                    operation_id is not None
                    and operation_id != reserved_operation_id
                )
            ):
                raise ProjectBackupError("backup_operation_conflict")
        if (
            record.replayed
            and record.status == STATUS_FAILED
            and record.error_code == "project_busy_retry_later"
        ):
            record = self.ledger.update(
                record.operation_id,
                status=STATUS_CONFIRMED,
                current_step="恢复请求已重新开始",
                error_code="",
                error_message="",
                terminal_outcome="",
                allow_terminal_reopen=True,
            )
            if reserved_operation_id is not None:
                reserved_owner = True
        if (
            reserved_operation_id is not None
            and not reserved_owner
            and record.status
            not in {
                STATUS_COMPLETED,
                STATUS_ALREADY_CURRENT,
                STATUS_RETAINED_FOR_TRIAGE,
                STATUS_FAILED,
            }
        ):
            record = dataclass_replace(record, replayed=False)
            reserved_owner = True
        if record.replayed and record.status in {
            STATUS_COMPLETED,
            STATUS_ALREADY_CURRENT,
            STATUS_RETAINED_FOR_TRIAGE,
        }:
            return self._restore_result_from_record(record)
        if preflight_result is None:
            preflight_result = self.preflight(
                package_path,
                idempotency_key="restore-preflight-" + key,
            )
        if preflight_result.package_id != package_id:
            raise ProjectBackupError("backup_operation_conflict")
        if preflight_result.decision == "blocked":
            raise ProjectBackupError("rollback_requires_review")
        if preflight_result.decision == "already_current":
            payload = {
                "result_label": "项目已是此版本",
                "project_name": preflight_result.project_name,
                "restored_cutoff_label": preflight_result.backup_cutoff_label,
                "verification_summary": "项目状态与备份版本一致",
                "next_action_label": "继续查看当前监查结果",
            }
            final_record = self._record_update(
                record.operation_id,
                OP_RESTORE,
                status=STATUS_ALREADY_CURRENT,
                progress_percent=PROGRESS_COMPLETE,
                current_step="恢复完成",
                terminal_outcome=STATUS_ALREADY_CURRENT,
                payload=payload,
            )
            return RestoreResult(
                operation=final_record,
                result_label="项目已是此版本",
                project_name=preflight_result.project_name,
                restored_cutoff_label=preflight_result.backup_cutoff_label,
                verification_summary="项目状态与备份版本一致",
                next_action_label="继续查看当前监查结果",
            )
        if preflight_result.confirmation_required and not confirmation:
            payload = {
                "result_label": "保持原项目未变",
                "project_name": preflight_result.project_name,
                "restored_cutoff_label": preflight_result.current_cutoff_label,
                "verification_summary": "尚未确认恢复，当前项目未变",
                "next_action_label": "确认后再恢复此备份",
            }
            kept = self._record_update(
                record.operation_id,
                OP_RESTORE,
                status=STATUS_KEPT_CURRENT,
                progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                current_step="等待恢复确认",
                terminal_outcome=STATUS_KEPT_CURRENT,
                payload=payload,
            )
            raise ProjectBackupError("restore_confirmation_required")
        stage_parent = (
            preflight_result.staging_path
            if preflight_result.staging_path is not None
            else self.runtime_root / STAGING_DIR_NAME / record.operation_id
        )
        stage_workspace = stage_parent / "workspace"
        rollback_path = self.runtime_root / (
            ".rollback-" + sha256_hex(self.canonical_project_id.encode("utf-8"))[:24] + "-" + record.operation_id
        )
        old_live_moved = False
        try:
            with self._gate(record.operation_id).exclusive():
                if reserved_owner:
                    latest = self.ledger.get(record.operation_id)
                    if latest.status in {
                        STATUS_COMPLETED,
                        STATUS_ALREADY_CURRENT,
                        STATUS_RETAINED_FOR_TRIAGE,
                    }:
                        return self._restore_result_from_record(latest)
                    record = latest
                current_summary, current_fp = self._current_state(record.operation_id)
                if current_fp != preflight_result.current_workspace_fingerprint:
                    raise ProjectBackupError("restore_source_changed")
                if self._existing_rollbacks():
                    raise ProjectBackupError("rollback_requires_review")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_STAGING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="恢复副本已准备",
                    staging_path=str(stage_parent),
                )
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.before")
                self._verify_workspace(stage_workspace, preflight_result.manifest, verify_manifest_summary=True)
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.after")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_VERIFYING_STAGED_WORKSPACE,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="恢复前检查已完成",
                )
                if self.failure_hook is not None:
                    self._hook("restore.quiesce.before")
                self._quiesce()
                if self.failure_hook is not None:
                    self._hook("restore.quiesce.after")
                if rollback_path.exists():
                    raise ProjectBackupError("rollback_requires_review")
                if os.stat(self.runtime_root).st_dev != os.stat(stage_parent).st_dev:
                    raise ProjectBackupError("restore_switch_failed")
                rollback_path.parent.mkdir(parents=True, exist_ok=True)
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_SWITCHING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="正在切换项目版本",
                )
                if self.workspace_dir.exists():
                    if self.failure_hook is not None:
                        self._hook("restore.current_to_rollback.before")
                    os.replace(str(self.workspace_dir), str(rollback_path))
                    old_live_moved = True
                    self._fsync_dir(self.runtime_root)
                    if self.failure_hook is not None:
                        self._hook("restore.current_to_rollback.after")
                if self.failure_hook is not None:
                    self._hook("restore.staging_to_live.before")
                os.replace(str(stage_workspace), str(self.workspace_dir))
                self._fsync_dir(self.runtime_root)
                if self.failure_hook is not None:
                    self._hook("restore.staging_to_live.after")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_VERIFYING_LIVE_WORKSPACE,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="正在重新核对项目",
                )
                live_summary, _, live_fp = self._verify_live_workspace(preflight_result.manifest)
                if live_fp != preflight_result.source_workspace_fingerprint or live_summary != preflight_result.manifest.get("project_summary"):
                    raise ProjectBackupError("restore_verification_failed")
                payload = {
                    "result_label": "恢复完成",
                    "project_name": preflight_result.project_name,
                    "restored_cutoff_label": preflight_result.backup_cutoff_label,
                    "verification_summary": "项目、监查结果、风险规则和连续性资料已重新核对",
                    "next_action_label": "继续查看监查结果",
                    "manifest": dict(preflight_result.manifest),
                }
                final_record = self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_COMPLETED,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="恢复完成",
                    rollback_path=str(rollback_path) if old_live_moved else "",
                    staging_path="",
                    payload=payload,
                )
                self._cleanup_path(stage_parent)
                return RestoreResult(
                    operation=final_record,
                    result_label="恢复完成",
                    project_name=preflight_result.project_name,
                    restored_cutoff_label=preflight_result.backup_cutoff_label,
                    verification_summary="项目、监查结果、风险规则和连续性资料已重新核对",
                    next_action_label="继续查看监查结果",
                    rollback_path=rollback_path if old_live_moved else None,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            rolled_back = self._rollback_after_failure(
                record.operation_id,
                rollback_path,
                stage_parent,
                old_live_moved=old_live_moved,
            )
            if rolled_back:
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_FAILED,
                    error_code=exc.code,
                    error_message=exc.message,
                    rollback_path=None,
                    staging_path=str(stage_parent) if stage_parent.exists() else None,
                )
                if not stage_parent.exists():
                    self._cleanup_path(stage_parent)
            else:
                retained_path = rollback_path
                failed_live = stage_parent / "failed-live"
                if retained_path is None or not retained_path.exists():
                    retained_path = failed_live if failed_live.exists() else stage_parent
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    error_code="restore_rollback_failed",
                    error_message=_ERROR_MESSAGES["restore_rollback_failed"],
                    rollback_path=str(retained_path),
                    staging_path=str(stage_parent),
                )
                raise ProjectBackupError("restore_rollback_failed") from exc
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            wrapped = ProjectBackupError("restore_switch_failed")
            rolled_back = self._rollback_after_failure(
                record.operation_id,
                rollback_path,
                stage_parent,
                old_live_moved=old_live_moved,
            )
            if not rolled_back:
                retained_path = rollback_path
                failed_live = stage_parent / "failed-live"
                if retained_path is None or not retained_path.exists():
                    retained_path = failed_live if failed_live.exists() else stage_parent
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    error_code="restore_rollback_failed",
                    error_message=_ERROR_MESSAGES["restore_rollback_failed"],
                    rollback_path=str(retained_path),
                    staging_path=str(stage_parent),
                )
                raise ProjectBackupError("restore_rollback_failed") from exc
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=wrapped.code,
                error_message=wrapped.message,
                staging_path=str(stage_parent) if stage_parent.exists() else None,
            )
            raise wrapped from exc

    restore_backup = restore
    import_restore = restore

    def rollback(self, operation: Union[str, OperationRecord, RestoreResult]) -> RestoreResult:
        if isinstance(operation, RestoreResult):
            operation_id = operation.operation_id
        elif isinstance(operation, OperationRecord):
            operation_id = operation.operation_id
        else:
            operation_id = str(operation)
        record = self.ledger.get(operation_id)
        if not record.rollback_path:
            raise ProjectBackupError("operation_not_found")
        rollback_path = Path(record.rollback_path)
        if not rollback_path.exists():
            raise ProjectBackupError("restore_rollback_failed")
        stage_parent = self.runtime_root / STAGING_DIR_NAME / (operation_id + "-manual-rollback")
        if stage_parent.exists():
            raise ProjectBackupError("backup_operation_conflict")
        stage_parent.mkdir(parents=True, exist_ok=False)
        try:
            with self._gate(operation_id).exclusive():
                self._hook("restore.rollback.before")
                if self.workspace_dir.exists():
                    os.replace(str(self.workspace_dir), str(stage_parent / "current-live"))
                os.replace(str(rollback_path), str(self.workspace_dir))
                self._fsync_dir(self.runtime_root)
                self._verify_workspace_independent(self.workspace_dir)
                self._hook("restore.rollback.after")
                payload = {
                    "result_label": "恢复完成",
                    "project_name": self.project_name or self.canonical_project_id,
                    "restored_cutoff_label": "",
                    "verification_summary": "原项目版本已重新打开并核对",
                    "next_action_label": "继续查看监查结果",
                }
                final = self._safe_update_result(
                    operation_id,
                    status=STATUS_COMPLETED,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="恢复完成",
                    terminal_outcome=STATUS_COMPLETED,
                    rollback_path=str(stage_parent / "current-live"),
                    staging_path="",
                    payload=payload,
                )
                return RestoreResult(
                    operation=final,
                    result_label="恢复完成",
                    project_name=self.project_name or self.canonical_project_id,
                    restored_cutoff_label="",
                    verification_summary="原项目版本已重新打开并核对",
                    next_action_label="继续查看监查结果",
                    rollback_path=stage_parent / "current-live",
                )
        except ProjectBackupError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise ProjectBackupError("restore_rollback_failed") from exc

    def _safe_update_result(self, operation_id: str, **kwargs: Any) -> OperationRecord:
        return self.ledger.update(operation_id, allow_terminal_reopen=True, **kwargs)

    def get_operation(self, operation_id: str) -> OperationRecord:
        return self.ledger.get(operation_id)

    status = get_operation
    operation_status = get_operation


ProjectBackup = ProjectBackupManager
BackupManager = ProjectBackupManager
ProjectBackupRestore = ProjectBackupManager


def backup_project(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    *,
    idempotency_key: Optional[str] = None,
    **kwargs: Any,
) -> BackupResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).backup(idempotency_key)


def preflight_backup(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    package: Union[str, Path],
    *,
    idempotency_key: Optional[str] = None,
    **kwargs: Any,
) -> PreflightResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).preflight(package, idempotency_key)


def restore_project(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    package: Union[str, Path, PreflightResult],
    *,
    idempotency_key: Optional[str] = None,
    confirmation: bool = False,
    **kwargs: Any,
) -> RestoreResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).restore(
        package, idempotency_key, confirmation=confirmation
    )


__all__ = [
    "ARTIFACT_DIR_NAME",
    "BACKUP_PUBLICATION_DIR_NAME",
    "BACKUP_SUFFIX",
    "BackupError",
    "BackupManager",
    "BackupResult",
    "CONTRACT_VERSION",
    "FAILURE_HOOK_POINTS",
    "HOOK_POINTS",
    "InjectedFailure",
    "LAUNCH_REGISTRY_DB_NAME",
    "MAX_ARCHIVE_BYTES",
    "MAX_ARCHIVE_MEMBERS",
    "MAX_MEMBER_BYTES",
    "OPERATIONS_DB_NAME",
    "OP_BACKUP",
    "OP_PREFLIGHT",
    "OP_RESTORE",
    "OperationLedger",
    "OperationRecord",
    "PreflightError",
    "PreflightResult",
    "PROFILE_DB_NAME",
    "ProjectBackup",
    "ProjectBackupError",
    "ProjectBackupManager",
    "ProjectBackupRestore",
    "WorkspaceSnapshot",
    "workspace_fingerprint",
    "RestoreError",
    "RestoreResult",
    "RISK_RULE_DB_NAME",
    "RUN_BINDING_DB_NAME",
    "RUNTIME_DB_NAME",
    "RUNTIME_DIR_NAME",
    "SCHEMA_VERSION",
    "backup_project",
    "canonical_json",
    "canonical_json_bytes",
    "preflight_backup",
    "restore_project",
    "sha256_hex",
]
