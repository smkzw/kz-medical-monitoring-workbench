"""Synthetic/offline R7 Slice-09B schema migration coordinator.

The coordinator deliberately keeps the live project immutable until a complete
sibling workspace has been migrated and independently verified.  It reuses the
09A backup manager for workspace member enumeration, SQLite snapshots,
workspace fingerprints, artifact closure checks, maintenance gates, and the
root operation database.  No provider, service, real project, or medical
writing path is involved.
"""
from __future__ import annotations

import copy
import errno
import json
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from . import schema_manifest as _schema
from .maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectBusyError,
    ProjectMaintenanceGate,
)
from .launch_schema import (
    CONTINUITY_INDEX_DDL as _CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL as _CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL as _CONTINUITY_PLANS_DDL,
    PUBLICATION_DDL as _PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL as _RESULT_CONTEXT_INDEX_DDL,
)
from .project_backup import (
    LAUNCH_REGISTRY_DB_NAME,
    OPERATIONS_DB_NAME,
    PROFILE_DB_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RUN_BINDING_DB_NAME,
    RISK_RULE_DB_NAME,
    ProjectBackupError,
    ProjectBackupManager,
    OperationLedger,
    WorkspaceSnapshot,
    workspace_fingerprint,
    _assert_directory,
    _assert_regular,
    _is_ignorable,
    _member_rel_paths,
    _open_ro,
    _table_names,
    canonical_json_bytes,
    sha256_hex,
)
from .schema_manifest import (
    BINDING_MEMBER,
    EXECUTION_CONTROL_MEMBER,
    LAUNCH_MEMBER,
    LAUNCH_V1,
    LAUNCH_V2,
    LAUNCH_V3,
    LAUNCH_V4,
    LAUNCH_V5,
    MEMBER_ORDER,
    PROFILE_MEMBER,
    RISK_MEMBER,
    RUNTIME_MEMBER,
    RUNTIME_V4,
    RUNTIME_V5,
    RUNTIME_V6,
    ProjectSchemaInspection,
    ProjectSchemaInspector,
    SchemaClassification,
    SCHEMA_MANIFEST_DIGEST,
    get_schema_manifest,
    inspect_member,
)


# ---------------------------------------------------------------------------
# Stable paths, states, and public result facts
# ---------------------------------------------------------------------------

MIGRATION_STAGING_DIR_NAME = ".migration-staging"
MIGRATION_ROLLBACK_DIR_NAME = ".migration-rollback"
MIGRATION_OPERATION_KIND = "migration"

STATUS_REQUESTED = "requested"
STATUS_INSPECTING = "inspecting"
STATUS_LEGACY_READONLY = "legacy_readonly"
STATUS_BACKUP_REQUIRED = "backup_required"
STATUS_BACKUP_IN_PROGRESS = "backup_in_progress"
STATUS_BACKUP_VERIFIED = "backup_verified"
STATUS_WAITING_FOR_PROJECT = "waiting_for_project"
STATUS_MAINTENANCE_ACQUIRED = "maintenance_acquired"
STATUS_STAGING = "staging"
STATUS_MIGRATING = "migrating"
STATUS_STAGED_VERIFIED = "staged_verified"
STATUS_SWITCHING = "switching"
STATUS_LIVE_VERIFYING = "live_verifying"
STATUS_COMPLETED = "completed"
STATUS_ALREADY_CURRENT = "already_current"
STATUS_RETRYABLE_FAILED = "retryable_failed"
STATUS_ROLLBACK_IN_PROGRESS = "rollback_in_progress"
STATUS_ROLLED_BACK = "rolled_back"
STATUS_RETAINED_FOR_TRIAGE = "retained_for_triage"
STATUS_BLOCKED = "blocked"
STATUS_MIGRATION_OPERATION_CONFLICT = "migration_operation_conflict"

PUBLIC_RECOVERY_STATES = frozenset(
    {
        STATUS_MAINTENANCE_ACQUIRED,
        STATUS_STAGING,
        STATUS_MIGRATING,
        STATUS_STAGED_VERIFIED,
        STATUS_SWITCHING,
        STATUS_LIVE_VERIFYING,
        STATUS_ROLLBACK_IN_PROGRESS,
    }
)
TERMINAL_STATES = frozenset(
    {
        STATUS_COMPLETED,
        STATUS_ALREADY_CURRENT,
        STATUS_ROLLED_BACK,
        STATUS_RETAINED_FOR_TRIAGE,
        STATUS_BLOCKED,
        STATUS_MIGRATION_OPERATION_CONFLICT,
    }
)

PROGRESS_REQUEST_ACCEPTED = 5
PROGRESS_INSPECTION_COMPLETE = 12
PROGRESS_BACKUP_VERIFIED = 28
PROGRESS_PROJECT_IDLE = 35
PROGRESS_STAGING_COMPLETE = 45
PROGRESS_CONTENT_UPDATED = 72
PROGRESS_STAGED_VERIFIED = 86
PROGRESS_SWITCHED = 94
PROGRESS_COMPLETE = 100

_ERROR_MESSAGES = {
    "migration_requires_confirmation": "请确认开始升级后再继续。",
    "migration_not_supported": "此项目格式暂不支持安全升级。",
    "migration_project_blocked": "暂时无法安全打开此项目，请保留原项目并联系支持。",
    "migration_operation_conflict": "项目升级状态已发生变化，请重新检查项目后再试。",
    "migration_requires_staging": "升级只能在受控副本中进行。",
    "migration_source_changed": "项目内容在升级前发生变化，请重新准备恢复点。",
    "cross_filesystem_staging_not_supported": "暂时无法在当前位置升级项目。",
    "migration_switch_failed": "项目切换未完成，原项目仍需重新核对。",
    "migration_verification_failed": "升级副本未通过完整核验。",
    "migration_rollback_failed": "升级未完成，暂时无法安全打开此项目。",
    "migration_ledger_corrupt": "升级记录无法核对，请保留原项目并联系支持。",
    "migration_in_progress": "项目升级正在处理中，请稍后重试。",
    "sqlite_integrity_failed": "项目内容无法安全核对。",
    "workspace_not_found": "未找到医学监查项目。",
    "unsupported_schema": "此项目格式暂不支持安全升级。",
}


class MigrationError(RuntimeError):
    """Fail-closed migration error with a stable internal code."""

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = str(code)
        self.message = message or _ERROR_MESSAGES.get(self.code, "项目升级未完成。")
        self.details = dict(details or {})
        super().__init__(self.code)

    def as_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": dict(self.details)}


class InjectedMigrationFailure(MigrationError):
    """Failure hook result.  The point is evidence, not a product message."""

    def __init__(self, point: str) -> None:
        self.point = str(point)
        super().__init__("injected_failure", details={"point": self.point})


class _CommittedStepFailure(MigrationError):
    """A hook failed after one SQLite step committed.

    The staging directory must remain available so a retry can use the target
    marker, member step digest, and structural oracle instead of repeating a
    business migration.
    """

    def __init__(self, point: str, cause: BaseException) -> None:
        self.point = str(point)
        self.cause = cause
        super().__init__("injected_failure", details={"point": self.point, "committed": True})


@dataclass(frozen=True)
class MigrationStep:
    member: str
    source_version: Optional[str]
    target_version: Optional[str]
    actions: Tuple[str, ...]

    @property
    def step_manifest(self) -> Dict[str, Any]:
        return {
            "member": self.member,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "actions": list(self.actions),
        }

    @property
    def step_digest(self) -> str:
        return sha256_hex(canonical_json_bytes(self.step_manifest))

    def as_dict(self) -> Dict[str, Any]:
        result = dict(self.step_manifest)
        result["step_digest"] = self.step_digest
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MigrationStep":
        try:
            step = cls(
                member=str(value["member"]),
                source_version=(
                    None if value.get("source_version") is None else str(value["source_version"])
                ),
                target_version=(
                    None if value.get("target_version") is None else str(value["target_version"])
                ),
                actions=tuple(str(item) for item in value.get("actions", ())),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MigrationError("migration_ledger_corrupt") from exc
        expected = value.get("step_digest")
        if expected is not None and str(expected) != step.step_digest:
            raise MigrationError("migration_ledger_corrupt")
        return step


@dataclass(frozen=True)
class MigrationPlan:
    schema_manifest_digest: str
    source_schema_set: Mapping[str, Mapping[str, Any]]
    target_schema_set: Mapping[str, Mapping[str, Any]]
    steps: Tuple[MigrationStep, ...]

    @property
    def source_schema_set_digest(self) -> str:
        return sha256_hex(canonical_json_bytes(self.source_schema_set))

    @property
    def target_schema_set_digest(self) -> str:
        return sha256_hex(canonical_json_bytes(self.target_schema_set))

    @property
    def member_step_digests(self) -> Mapping[str, str]:
        return {step.member: step.step_digest for step in self.steps}

    @property
    def plan_manifest(self) -> Dict[str, Any]:
        return {
            "schema_manifest_digest": self.schema_manifest_digest,
            "source_schema_set": dict(self.source_schema_set),
            "target_schema_set": dict(self.target_schema_set),
            "steps": [step.as_dict() for step in self.steps],
        }

    @property
    def plan_digest(self) -> str:
        return sha256_hex(canonical_json_bytes(self.plan_manifest))

    def as_dict(self) -> Dict[str, Any]:
        value = dict(self.plan_manifest)
        value.update(
            {
                "source_schema_set_digest": self.source_schema_set_digest,
                "target_schema_set_digest": self.target_schema_set_digest,
                "member_step_digests": dict(self.member_step_digests),
                "plan_digest": self.plan_digest,
            }
        )
        return value

    @classmethod
    def from_inspection(cls, inspection: ProjectSchemaInspection) -> "MigrationPlan":
        manifest = get_schema_manifest()
        source: Dict[str, Mapping[str, Any]] = {}
        target: Dict[str, Mapping[str, Any]] = {}
        for member in MEMBER_ORDER:
            report = inspection.members[member]
            source[member] = {
                "present": bool(report.present),
                "schema_version": report.schema_version,
                "marker_value": report.marker_value,
                "shape_digest": report.shape_digest,
                "classification": str(report.classification.value),
            }
            definition = manifest["members"][member]
            versions = definition.get("versions", {})
            current = next(
                (
                    variant
                    for variant in versions.values()
                    if variant.get("classification") == SchemaClassification.CURRENT.value
                ),
                None,
            )
            target[member] = {
                "present": bool(report.present),
                "schema_version": None if current is None else current.get("schema_version"),
                "shape_digest": None if current is None else current.get("shape_digest"),
                "classification": SchemaClassification.CURRENT.value,
            }
        unsupported_legacy = [
            member
            for member in (PROFILE_MEMBER, BINDING_MEMBER, EXECUTION_CONTROL_MEMBER, RISK_MEMBER)
            if inspection.members[member].classification is SchemaClassification.LEGACY
        ]
        if unsupported_legacy:
            raise MigrationError("migration_not_supported")
        steps: List[MigrationStep] = []
        runtime_version = inspection.members[RUNTIME_MEMBER].schema_version
        if runtime_version in (RUNTIME_V4, RUNTIME_V5):
            actions = (
                "create_work_unit_capability_attempts",
                "add_manifest_revision_columns" if runtime_version == RUNTIME_V4 else "",
                "backfill_manifest_revision" if runtime_version == RUNTIME_V4 else "",
                "verify_exact_target_shape",
                "update_marker_last",
            )
            steps.append(
                MigrationStep(
                    RUNTIME_MEMBER,
                    runtime_version,
                    RUNTIME_V6,
                    tuple(item for item in actions if item),
                )
            )
        launch_version = inspection.members[LAUNCH_MEMBER].schema_version
        if launch_version in (LAUNCH_V1, LAUNCH_V2, LAUNCH_V3, LAUNCH_V4):
            actions_by_version = {
                LAUNCH_V1: (
                    "create_publication_tables",
                    "create_continuity_tables",
                    "create_current_indexes",
                    "verify_exact_target_shape",
                    "update_marker_last",
                ),
                LAUNCH_V2: (
                    "create_continuity_tables",
                    "create_current_indexes",
                    "verify_exact_target_shape",
                    "update_marker_last",
                ),
                LAUNCH_V3: (
                    "add_v4_publication_columns",
                    "add_v4_continuity_columns",
                    "create_current_indexes",
                    "verify_exact_target_shape",
                    "update_marker_last",
                ),
                # W01-R26（20260926）：v4→v5仅新增两个可空引用列，守卫式
                # ALTER原地补列，不重建表、不改写既有行数据。
                LAUNCH_V4: (
                    "add_v5_publication_columns",
                    "verify_exact_target_shape",
                    "update_marker_last",
                ),
            }
            steps.append(MigrationStep(LAUNCH_MEMBER, launch_version, LAUNCH_V5, actions_by_version[launch_version]))
        return cls(
            schema_manifest_digest=SCHEMA_MANIFEST_DIGEST,
            source_schema_set={key: source[key] for key in MEMBER_ORDER},
            target_schema_set={key: target[key] for key in MEMBER_ORDER},
            steps=tuple(steps),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MigrationPlan":
        try:
            steps = tuple(MigrationStep.from_mapping(item) for item in value.get("steps", ()))
            plan = cls(
                schema_manifest_digest=str(value["schema_manifest_digest"]),
                source_schema_set=copy.deepcopy(dict(value["source_schema_set"])),
                target_schema_set=copy.deepcopy(dict(value["target_schema_set"])),
                steps=steps,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MigrationError("migration_ledger_corrupt") from exc
        expected = value.get("plan_digest")
        if expected is not None and str(expected) != plan.plan_digest:
            raise MigrationError("migration_ledger_corrupt")
        if plan.schema_manifest_digest != SCHEMA_MANIFEST_DIGEST:
            raise MigrationError("migration_operation_conflict")
        expected_sources = value.get("source_schema_set_digest")
        expected_targets = value.get("target_schema_set_digest")
        if expected_sources is not None and str(expected_sources) != plan.source_schema_set_digest:
            raise MigrationError("migration_ledger_corrupt")
        if expected_targets is not None and str(expected_targets) != plan.target_schema_set_digest:
            raise MigrationError("migration_ledger_corrupt")
        return plan


@dataclass(frozen=True)
class MigrationOperation:
    operation_id: str
    operation_kind: str
    idempotency_key: str
    canonical_project_id: str
    status: str
    progress_percent: int
    current_step: str
    package_id: Optional[str]
    source_workspace_fingerprint: Optional[str]
    terminal_outcome: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    rollback_path: Optional[str]
    staging_path: Optional[str]
    package_path: Optional[str]
    maintenance_state: Optional[str]
    source_schema_set_digest: Optional[str]
    target_schema_set_digest: Optional[str]
    plan_digest: Optional[str]
    current_member: Optional[str]
    member_step_digest: Optional[str]
    directory_switch_stage: Optional[str]
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    replayed: bool = False

    @property
    def operation(self) -> "MigrationOperation":
        return self

    def as_dict(self) -> Dict[str, Any]:
        return {
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
            "source_schema_set_digest": self.source_schema_set_digest,
            "target_schema_set_digest": self.target_schema_set_digest,
            "plan_digest": self.plan_digest,
            "current_member": self.current_member,
            "member_step_digest": self.member_step_digest,
            "directory_switch_stage": self.directory_switch_stage,
            "payload": copy.deepcopy(dict(self.payload)),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "replayed": self.replayed,
        }

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


@dataclass(frozen=True)
class MigrationResult:
    operation: Optional[MigrationOperation]
    state: str
    requires_reopen: bool
    source_schema_set_digest: Optional[str] = None
    target_schema_set_digest: Optional[str] = None
    plan_digest: Optional[str] = None
    message: str = ""
    next_action: str = ""

    @property
    def operation_id(self) -> Optional[str]:
        return None if self.operation is None else self.operation.operation_id

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "requires_reopen": self.requires_reopen,
            "source_schema_set_digest": self.source_schema_set_digest,
            "target_schema_set_digest": self.target_schema_set_digest,
            "plan_digest": self.plan_digest,
            "message": self.message,
            "next_action": self.next_action,
            "operation": None if self.operation is None else self.operation.as_dict(),
        }


# ---------------------------------------------------------------------------
# Root ledger extension
# ---------------------------------------------------------------------------

_LEDGER_EXTENSIONS: Mapping[str, str] = {
    "source_schema_set_digest": "TEXT",
    "target_schema_set_digest": "TEXT",
    "plan_digest": "TEXT",
    "current_member": "TEXT",
    "member_step_digest": "TEXT",
    "directory_switch_stage": "TEXT",
}
_UNSET = object()

_SAFE_MIGRATION_OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _safe_key(value: Any, code: str = "migration_operation_conflict") -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise MigrationError(code)
    return value


def _safe_operation_id(value: Any, code: str = "migration_ledger_corrupt") -> str:
    if not isinstance(value, str) or _SAFE_MIGRATION_OPERATION_ID.fullmatch(value) is None:
        raise MigrationError(code)
    return value

def _safe_project_id(value: Any, code: str = "migration_project_blocked") -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\x00" in value
        or any(ord(char) < 32 for char in value)
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise MigrationError(code)
    return value


class MigrationOperationLedger:
    """Extension view over the 09A root ``backup_operations`` table.

    The table remains outside every project directory.  Existing 09A rows and
    APIs are left intact; migration rows carry explicit schema/plan/member and
    directory-switch columns in addition to the common operation columns.
    """

    def __init__(self, root_or_db_path: Union[str, Path], *, initialize: bool = True) -> None:
        candidate = Path(root_or_db_path)
        self.path = candidate if candidate.suffix == ".sqlite3" else candidate / OPERATIONS_DB_NAME
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if initialize:
            base = OperationLedger(self.path)
            base.close()
        self._conn = sqlite3.connect(
            str(self.path), timeout=10.0, isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_extensions()

    def _ensure_extensions(self) -> None:
        try:
            columns = {
                str(row[1])
                for row in self._conn.execute("PRAGMA table_info(backup_operations)").fetchall()
            }
        except sqlite3.Error as exc:
            raise MigrationError("migration_ledger_corrupt") from exc
        if not columns:
            raise MigrationError("migration_ledger_corrupt")
        for name, declared_type in _LEDGER_EXTENSIONS.items():
            if name not in columns:
                try:
                    self._conn.execute(
                        "ALTER TABLE backup_operations ADD COLUMN %s %s" % (name, declared_type)
                    )
                except sqlite3.Error as exc:
                    raise MigrationError("migration_ledger_corrupt") from exc

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "MigrationOperationLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _row(self, operation_id: str, *, replayed: bool = False) -> MigrationOperation:
        operation_id = _safe_operation_id(operation_id)
        row = self._conn.execute(
            "SELECT * FROM backup_operations WHERE operation_id=? AND operation_kind=?",
            (operation_id, MIGRATION_OPERATION_KIND),
        ).fetchone()
        if row is None:
            raise MigrationError("migration_ledger_corrupt")
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MigrationError("migration_ledger_corrupt") from exc
        if not isinstance(payload, dict):
            raise MigrationError("migration_ledger_corrupt")
        return MigrationOperation(
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
            source_schema_set_digest=row["source_schema_set_digest"] or None,
            target_schema_set_digest=row["target_schema_set_digest"] or None,
            plan_digest=row["plan_digest"] or None,
            current_member=row["current_member"] or None,
            member_step_digest=row["member_step_digest"] or None,
            directory_switch_stage=row["directory_switch_stage"] or None,
            payload=payload,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            replayed=replayed,
        )

    def get(self, operation_id: str) -> MigrationOperation:
        if not isinstance(operation_id, str) or not operation_id:
            raise MigrationError("migration_ledger_corrupt")
        return self._row(operation_id)

    def _active_for_project(self, project: str) -> Optional[MigrationOperation]:
        rows = self._conn.execute(
            "SELECT operation_id FROM backup_operations WHERE operation_kind=? "
            "AND canonical_project_id=? ORDER BY created_at, operation_id",
            (MIGRATION_OPERATION_KIND, project),
        ).fetchall()
        for row in rows:
            record = self._row(str(row[0]))
            if record.status not in TERMINAL_STATES or record.status == STATUS_RETAINED_FOR_TRIAGE:
                return record
        return None

    def create_or_replay(
        self,
        idempotency_key: str,
        canonical_project_id: str,
        *,
        source_schema_set_digest: str,
        target_schema_set_digest: str,
        plan_digest: str,
        plan: Mapping[str, Any],
    ) -> MigrationOperation:
        key = _safe_key(idempotency_key)
        project = _safe_project_id(canonical_project_id, "migration_operation_conflict")
        source_digest = _safe_key(source_schema_set_digest)
        target_digest = _safe_key(target_schema_set_digest)
        plan_hash = _safe_key(plan_digest)
        now = _now_iso()
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT operation_id FROM backup_operations WHERE operation_kind=? "
                "AND idempotency_key=? AND canonical_project_id=?",
                (MIGRATION_OPERATION_KIND, key, project),
            ).fetchone()
            if row is not None:
                record = self._row(str(row[0]))
                if (
                    record.plan_digest not in (None, plan_hash)
                    or record.source_schema_set_digest not in (None, source_digest)
                    or record.target_schema_set_digest not in (None, target_digest)
                ):
                    raise MigrationError("migration_operation_conflict")
                self._conn.execute("COMMIT")
                return MigrationOperation(**{**record.as_dict(), "replayed": True})
            active = self._active_for_project(project)
            if active is not None:
                raise MigrationError(
                    "migration_operation_conflict",
                    details={"operation_id": active.operation_id},
                )
            operation_id = uuid.uuid4().hex
            self._conn.execute(
                "INSERT INTO backup_operations(operation_id, operation_kind, idempotency_key, "
                "canonical_project_id, status, progress_percent, current_step, package_id, "
                "source_workspace_fingerprint, terminal_outcome, error_code, error_message, "
                "rollback_path, staging_path, package_path, maintenance_state, payload_json, "
                "created_at, updated_at, source_schema_set_digest, target_schema_set_digest, "
                "plan_digest, current_member, member_step_digest, directory_switch_stage) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    operation_id,
                    MIGRATION_OPERATION_KIND,
                    key,
                    project,
                    STATUS_REQUESTED,
                    PROGRESS_REQUEST_ACCEPTED,
                    "请求已受理",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    canonical_json_bytes(dict(plan)).decode("utf-8"),
                    now,
                    now,
                    source_digest,
                    target_digest,
                    plan_hash,
                    None,
                    None,
                    "none",
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
        status: Any = _UNSET,
        progress_percent: Any = _UNSET,
        current_step: Any = _UNSET,
        package_id: Any = _UNSET,
        source_workspace_fingerprint: Any = _UNSET,
        terminal_outcome: Any = _UNSET,
        error_code: Any = _UNSET,
        error_message: Any = _UNSET,
        rollback_path: Any = _UNSET,
        staging_path: Any = _UNSET,
        package_path: Any = _UNSET,
        maintenance_state: Any = _UNSET,
        source_schema_set_digest: Any = _UNSET,
        target_schema_set_digest: Any = _UNSET,
        plan_digest: Any = _UNSET,
        current_member: Any = _UNSET,
        member_step_digest: Any = _UNSET,
        directory_switch_stage: Any = _UNSET,
        payload: Any = _UNSET,
        allow_terminal_reopen: bool = False,
    ) -> MigrationOperation:
        current = self.get(operation_id)
        next_status = current.status if status is _UNSET else str(status)
        if (
            current.status in TERMINAL_STATES
            and next_status != current.status
            and not allow_terminal_reopen
        ):
            raise MigrationError("migration_operation_conflict")
        if progress_percent is _UNSET:
            progress = current.progress_percent
        else:
            if isinstance(progress_percent, bool) or not 0 <= int(progress_percent) <= 100:
                raise MigrationError("migration_ledger_corrupt")
            progress = max(current.progress_percent, int(progress_percent))
        fields: Dict[str, Any] = {
            "status": next_status,
            "progress_percent": progress,
            "current_step": current.current_step if current_step is _UNSET else str(current_step),
            "package_id": current.package_id if package_id is _UNSET else package_id,
            "source_workspace_fingerprint": (
                current.source_workspace_fingerprint
                if source_workspace_fingerprint is _UNSET
                else source_workspace_fingerprint
            ),
            "terminal_outcome": current.terminal_outcome if terminal_outcome is _UNSET else terminal_outcome,
            "error_code": current.error_code if error_code is _UNSET else error_code,
            "error_message": current.error_message if error_message is _UNSET else error_message,
            "rollback_path": current.rollback_path if rollback_path is _UNSET else rollback_path,
            "staging_path": current.staging_path if staging_path is _UNSET else staging_path,
            "package_path": current.package_path if package_path is _UNSET else package_path,
            "maintenance_state": current.maintenance_state if maintenance_state is _UNSET else maintenance_state,
            "source_schema_set_digest": (
                current.source_schema_set_digest
                if source_schema_set_digest is _UNSET
                else source_schema_set_digest
            ),
            "target_schema_set_digest": (
                current.target_schema_set_digest
                if target_schema_set_digest is _UNSET
                else target_schema_set_digest
            ),
            "plan_digest": current.plan_digest if plan_digest is _UNSET else plan_digest,
            "current_member": current.current_member if current_member is _UNSET else current_member,
            "member_step_digest": (
                current.member_step_digest if member_step_digest is _UNSET else member_step_digest
            ),
            "directory_switch_stage": (
                current.directory_switch_stage
                if directory_switch_stage is _UNSET
                else directory_switch_stage
            ),
            "payload_json": (
                canonical_json_bytes(dict(current.payload)).decode("utf-8")
                if payload is _UNSET
                else canonical_json_bytes(dict(payload)).decode("utf-8")
            ),
            "updated_at": _now_iso(),
        }
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE backup_operations SET status=?, progress_percent=?, current_step=?, "
                "package_id=?, source_workspace_fingerprint=?, terminal_outcome=?, error_code=?, "
                "error_message=?, rollback_path=?, staging_path=?, package_path=?, "
                "maintenance_state=?, source_schema_set_digest=?, target_schema_set_digest=?, "
                "plan_digest=?, current_member=?, member_step_digest=?, directory_switch_stage=?, "
                "payload_json=?, updated_at=? WHERE operation_id=? AND operation_kind=?",
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
                    fields["source_schema_set_digest"],
                    fields["target_schema_set_digest"],
                    fields["plan_digest"],
                    fields["current_member"],
                    fields["member_step_digest"],
                    fields["directory_switch_stage"],
                    fields["payload_json"],
                    fields["updated_at"],
                    operation_id,
                    MIGRATION_OPERATION_KIND,
                ),
            )
            if self._conn.total_changes <= 0:
                raise MigrationError("migration_ledger_corrupt")
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        return self._row(operation_id)

    def list_for_project(self, canonical_project_id: str) -> List[MigrationOperation]:
        project = _safe_project_id(canonical_project_id, "migration_operation_conflict")
        rows = self._conn.execute(
            "SELECT operation_id FROM backup_operations WHERE operation_kind=? "
            "AND canonical_project_id=? ORDER BY created_at, operation_id",
            (MIGRATION_OPERATION_KIND, project),
        ).fetchall()
        return [self._row(str(row[0])) for row in rows]

    def list_recovery(self, canonical_project_id: Optional[str] = None) -> List[MigrationOperation]:
        query = "SELECT operation_id FROM backup_operations WHERE operation_kind=?"
        params: List[Any] = [MIGRATION_OPERATION_KIND]
        if canonical_project_id is not None:
            query += " AND canonical_project_id=?"
            params.append(_safe_project_id(canonical_project_id, "migration_operation_conflict"))
        query += " AND status IN (%s) ORDER BY created_at, operation_id" % ",".join("?" for _ in PUBLIC_RECOVERY_STATES)
        params.extend(sorted(PUBLIC_RECOVERY_STATES))
        rows = self._conn.execute(query, tuple(params)).fetchall()
        return [self._row(str(row[0])) for row in rows]

    def apply_callback(
        self,
        operation_id: str,
        *,
        plan_digest: str,
        expected_state: str,
        **updates: Any,
    ) -> MigrationOperation:
        record = self.get(operation_id)
        if record.plan_digest != plan_digest or record.status != expected_state:
            raise MigrationError("migration_operation_conflict")
        return self.update(operation_id, **updates)


# ---------------------------------------------------------------------------


__all__ = [name for name in globals() if not name.startswith("__")]
