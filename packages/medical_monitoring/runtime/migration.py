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
        if launch_version in (LAUNCH_V1, LAUNCH_V2, LAUNCH_V3):
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
            }
            steps.append(MigrationStep(LAUNCH_MEMBER, launch_version, LAUNCH_V4, actions_by_version[launch_version]))
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
# Workspace and schema oracles
# ---------------------------------------------------------------------------


def _canonical_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__repr__": repr(value)}


def _table_rows(connection: sqlite3.Connection, table: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    quoted = '"' + table.replace('"', '""') + '"'
    info = connection.execute("PRAGMA table_info(%s)" % quoted).fetchall()
    columns = [str(row[1]) for row in info]
    rows = connection.execute("SELECT * FROM %s" % quoted).fetchall()
    values = [tuple(_canonical_value(value) for value in row) for row in rows]
    values.sort(key=lambda row: canonical_json_bytes(list(row)))
    return columns, values


def _database_oracle(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"present": False, "tables": {}}
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = _open_ro(path)
        tables: Dict[str, Any] = {}
        for table in sorted(_table_names(connection), key=lambda value: value.encode("utf-8")):
            columns, rows = _table_rows(connection, table)
            if table in {"meta", "r7_launch_registry_meta", "profile_store_meta"}:
                filtered: List[Tuple[Any, ...]] = []
                key_index = columns.index("key") if "key" in columns else -1
                for row in rows:
                    if key_index >= 0 and row[key_index] == "schema_version":
                        continue
                    filtered.append(row)
                rows = filtered
            tables[table] = {"columns": columns, "rows": rows}
        return {"present": True, "tables": tables}
    except (ProjectBackupError, sqlite3.Error, OSError) as exc:
        raise MigrationError("sqlite_integrity_failed") from exc
    finally:
        if connection is not None:
            connection.close()


def _workspace_oracle(workspace: Path) -> Dict[str, Any]:
    if not workspace.is_dir():
        raise MigrationError("workspace_not_found")
    db_paths = {
        RUNTIME_MEMBER: workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        PROFILE_MEMBER: workspace / PROFILE_DB_NAME,
        BINDING_MEMBER: workspace / RUN_BINDING_DB_NAME,
        LAUNCH_MEMBER: workspace / LAUNCH_REGISTRY_DB_NAME,
        RISK_MEMBER: workspace / RISK_RULE_DB_NAME,
    }
    databases = {member: _database_oracle(path) for member, path in db_paths.items()}
    project_ids: set[str] = set()
    run_ids: set[str] = set()
    profile_ids: set[str] = set()
    for database in databases.values():
        for table in database.get("tables", {}).values():
            columns = table["columns"]
            rows = table["rows"]
            for row in rows:
                if "project_id" in columns:
                    project_ids.add(str(row[columns.index("project_id")]))
                if "run_id" in columns:
                    run_ids.add(str(row[columns.index("run_id")]))
                for column in ("execution_profile_id", "profile_id"):
                    if column in columns:
                        profile_ids.add(str(row[columns.index(column)]))
    return {
        "databases": databases,
        "project_ids": sorted(project_ids),
        "run_ids": sorted(run_ids),
        "profile_ids": sorted(profile_ids),
    }


def _compare_database_oracles(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    before_databases = before.get("databases", {})
    after_databases = after.get("databases", {})
    if before.get("project_ids") != after.get("project_ids"):
        raise MigrationError("migration_verification_failed")
    if before.get("run_ids") != after.get("run_ids"):
        raise MigrationError("migration_verification_failed")
    if before.get("profile_ids") != after.get("profile_ids"):
        raise MigrationError("migration_verification_failed")
    for member, old_database in before_databases.items():
        if not old_database.get("present"):
            continue
        new_database = after_databases.get(member, {})
        if not new_database.get("present"):
            raise MigrationError("migration_verification_failed")
        old_tables = old_database.get("tables", {})
        new_tables = new_database.get("tables", {})
        for table_name, old_table in old_tables.items():
            new_table = new_tables.get(table_name)
            if new_table is None:
                raise MigrationError("migration_verification_failed")
            old_columns = list(old_table.get("columns", []))
            new_columns = list(new_table.get("columns", []))
            common_columns = [column for column in old_columns if column in new_columns]
            old_index = [old_columns.index(column) for column in common_columns]
            new_index = [new_columns.index(column) for column in common_columns]
            old_rows = [tuple(row[index] for index in old_index) for row in old_table.get("rows", [])]
            new_rows = [tuple(row[index] for index in new_index) for row in new_table.get("rows", [])]
            old_rows.sort(key=lambda row: canonical_json_bytes(list(row)))
            new_rows.sort(key=lambda row: canonical_json_bytes(list(row)))
            if old_rows != new_rows:
                raise MigrationError("migration_verification_failed")


def _artifact_hashes_and_bytes(manager: ProjectBackupManager, workspace: Path) -> Dict[str, bytes]:
    """Use the public 09A closure primitive for migration verification."""

    try:
        return manager.artifact_closure(workspace)
    except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise MigrationError("migration_verification_failed") from exc


def _compare_artifacts(before: Mapping[str, bytes], after: Mapping[str, bytes]) -> None:
    if tuple(before) != tuple(after):
        raise MigrationError("migration_verification_failed")
    for key in before:
        if before[key] != after[key]:
            raise MigrationError("migration_verification_failed")


def _remove_sqlite_sidecars(workspace: Path) -> None:
    """Remove SQLite sidecars from an isolated, closed staging copy."""
    for root, dirs, files in os.walk(str(workspace)):
        for name in files:
            if name.endswith("-wal") or name.endswith("-shm") or name.endswith("-journal"):
                try:
                    (Path(root) / name).unlink()
                except OSError as exc:
                    raise MigrationError("migration_verification_failed") from exc


def _assert_no_sqlite_sidecars(workspace: Path) -> None:
    for root, dirs, files in os.walk(str(workspace)):
        dirs[:] = [
            name for name in dirs
            if name not in {".migration-staging", MIGRATION_ROLLBACK_DIR_NAME}
        ]
        for name in files:
            if name.endswith("-wal") or name.endswith("-shm") or name.endswith("-journal"):
                raise MigrationError("migration_verification_failed")


def _assert_same_device(*paths: Path) -> None:
    devices: set[int] = set()
    for path in paths:
        candidate = path
        while not candidate.exists() and candidate != candidate.parent:
            candidate = candidate.parent
        try:
            devices.add(int(os.stat(str(candidate)).st_dev))
        except OSError as exc:
            raise MigrationError("cross_filesystem_staging_not_supported") from exc
    if len(devices) != 1:
        raise MigrationError("cross_filesystem_staging_not_supported")

def _replace_or_raise(source: Path, destination: Path) -> None:
    try:
        os.replace(str(source), str(destination))
    except OSError as exc:
        if exc.errno == errno.EXDEV:
            raise MigrationError("cross_filesystem_staging_not_supported") from exc
        raise


def _replaceable(path: Path) -> bool:
    try:
        return path.is_dir() and not path.is_symlink()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# SQLite migration steps
# ---------------------------------------------------------------------------

_RUNTIME_CAPABILITY_DDL = """
CREATE TABLE IF NOT EXISTS work_unit_capability_attempts (
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    work_unit_id TEXT NOT NULL,
    attempt_ordinal INTEGER NOT NULL CHECK (attempt_ordinal >= 1),
    attempt_id TEXT NOT NULL UNIQUE REFERENCES capability_attempt_journal(attempt_id),
    detail TEXT NOT NULL,
    execution_identity_json TEXT NOT NULL,
    identity_hash TEXT NOT NULL,
    bound_at TEXT NOT NULL,
    PRIMARY KEY (run_id, manifest_revision, work_unit_id, attempt_ordinal),
    UNIQUE (run_id, manifest_revision, work_unit_id, attempt_id),
    FOREIGN KEY (run_id, manifest_revision, work_unit_id)
        REFERENCES work_unit_runs(run_id, manifest_revision, work_unit_id)
);
CREATE INDEX IF NOT EXISTS idx_work_unit_capability_attempts_unit
    ON work_unit_capability_attempts(run_id, manifest_revision, work_unit_id);
"""

# Launch table/index DDL is centralized in ``launch_schema`` and shared by
# construction, manifest inspection, and these marker-last migrations.


def _split_sql(sql: str) -> Tuple[str, ...]:
    return tuple(statement.strip() for statement in sql.split(";") if statement.strip())


def _shape_for(connection: sqlite3.Connection, member: str) -> Dict[str, Any]:
    try:
        shape = copy.deepcopy(_schema._connection_shape(connection))
    except (AttributeError, sqlite3.Error) as exc:
        raise MigrationError("migration_verification_failed") from exc
    if member == RUNTIME_MEMBER:
        shape["tables"].pop("r7_execution_control", None)
    return shape


def _target_variant(member: str, version: str) -> Mapping[str, Any]:
    manifest = get_schema_manifest()
    try:
        return manifest["members"][member]["versions"][version]
    except (KeyError, TypeError) as exc:
        raise MigrationError("migration_ledger_corrupt") from exc


def _assert_shape_on_connection(
    connection: sqlite3.Connection, member: str, version: str
) -> None:
    expected = _target_variant(member, version)["shape"]
    actual = _shape_for(connection, member)
    if actual != expected:
        raise MigrationError("migration_verification_failed")


def _read_meta_marker(connection: sqlite3.Connection, member: str) -> Optional[str]:
    if member == RUNTIME_MEMBER:
        row = connection.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return None if row is None else str(row[0])
    if member == LAUNCH_MEMBER:
        row = connection.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key='schema_version'"
        ).fetchone()
        return None if row is None else str(row[0])
    return None


def _table_columns_ordered(connection: sqlite3.Connection, table: str) -> List[str]:
    quoted = '"' + table.replace('"', '""') + '"'
    return [str(row[1]) for row in connection.execute("PRAGMA table_info(%s)" % quoted).fetchall()]
def _frozen_create_statement(ddl: str, table: str) -> str:
    """Extract one independent CREATE TABLE statement from frozen DDL."""
    pattern = re.compile(
        r"^CREATE TABLE IF NOT EXISTS\s+" + re.escape(table) + r"\s*\(",
        re.IGNORECASE,
    )
    for statement in _split_sql(ddl):
        if pattern.search(statement):
            return statement
    raise MigrationError("migration_ledger_corrupt")


def _frozen_index_statements(ddl: str, table: str) -> Tuple[str, ...]:
    pattern = re.compile(
        r"^CREATE INDEX IF NOT EXISTS\s+\S+\s+ON\s+" + re.escape(table) + r"\s*\(",
        re.IGNORECASE,
    )
    return tuple(statement for statement in _split_sql(ddl) if pattern.search(statement))


def _runtime_manifest_revision(
    connection: sqlite3.Connection, run_id: Any, observed_at: Any
) -> int:
    row = connection.execute(
        "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
        "ORDER BY revision DESC LIMIT 1",
        (run_id, observed_at or ""),
    ).fetchone()
    return 0 if row is None else int(row[0])


def _rebuild_runtime_table(
    connection: sqlite3.Connection,
    table: str,
    old_columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    revisions: Sequence[int],
) -> None:
    """Rebuild a v4 table so the added column has frozen-order placement."""
    old_name = "__migration_old_" + table
    create = _frozen_create_statement(_schema._R1_DDL, table)
    if table == "node_attempts":
        expected_old = [
            "run_id",
            "node_id",
            "attempt_seq",
            "idempotency_key",
            "logical_key",
            "status",
            "payload_hash",
            "created_at",
        ]
    else:
        expected_old = [
            "run_id",
            "node_id",
            "node_type",
            "status",
            "idempotency_key",
            "attempts",
            "artifact_id",
            "output_json",
            "error",
            "reason",
            "started_at",
            "finished_at",
        ]
    if list(old_columns) != expected_old:
        raise MigrationError("migration_verification_failed")
    # Drop the old named indexes before renaming the table.  SQLite keeps
    # index names across ALTER TABLE ... RENAME, so leaving them in place
    # would prevent recreating the frozen current indexes.
    for statement in _frozen_index_statements(_schema._R1_DDL, table):
        match = re.search(
            r"^CREATE INDEX IF NOT EXISTS\s+(\S+)", statement, re.IGNORECASE
        )
        if match:
            connection.execute("DROP INDEX IF EXISTS " + match.group(1))
    connection.execute("ALTER TABLE %s RENAME TO %s" % (table, old_name))
    connection.execute(create)
    target_columns = _table_columns_ordered(connection, table)
    placeholders = ",".join("?" for _ in target_columns)
    connection.executemany(
        "INSERT INTO %s (%s) VALUES (%s)" % (
            table,
            ",".join(target_columns),
            placeholders,
        ),
        [
            tuple(
                (revision if column == "manifest_revision" else row[old_columns.index(column)])
                for column in target_columns
            )
            for row, revision in zip(rows, revisions)
        ],
    )
    connection.execute("DROP TABLE %s" % old_name)
    for statement in _frozen_index_statements(_schema._R1_DDL, table):
        connection.execute(statement)
def _drop_named_indexes(
    connection: sqlite3.Connection, statements: Sequence[str]
) -> None:
    for statement in statements:
        match = re.search(
            r"^CREATE(?: UNIQUE)? INDEX IF NOT EXISTS\s+(\S+)",
            statement,
            re.IGNORECASE,
        )
        if match:
            connection.execute("DROP INDEX IF EXISTS " + match.group(1))


def _rebuild_table_from_ddl(
    connection: sqlite3.Connection,
    table: str,
    ddl: str,
    old_columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    defaults: Optional[Mapping[str, Any]] = None,
) -> None:
    old_name = "__migration_old_" + table
    if old_name in _table_names(connection):
        raise MigrationError("migration_operation_conflict")
    create = _frozen_create_statement(ddl, table)
    connection.execute("ALTER TABLE %s RENAME TO %s" % (table, old_name))
    connection.execute(create)
    target_columns = _table_columns_ordered(connection, table)
    values = []
    defaults = dict(defaults or {})
    for row in rows:
        values.append(
            tuple(
                row[old_columns.index(column)]
                if column in old_columns
                else defaults.get(column)
                for column in target_columns
            )
        )
    placeholders = ",".join("?" for _ in target_columns)
    if values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                table,
                ",".join(target_columns),
                placeholders,
            ),
            values,
        )
    connection.execute("DROP TABLE %s" % old_name)


def _rebuild_launch_publication_v3(connection: sqlite3.Connection) -> None:
    table = "r7_result_publications"
    old_columns = _table_columns_ordered(connection, table)
    rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % table).fetchall()
    _drop_named_indexes(
        connection,
        _split_sql(_PUBLICATION_DDL) + _split_sql(_RESULT_CONTEXT_INDEX_DDL),
    )
    _rebuild_table_from_ddl(
        connection,
        table,
        _PUBLICATION_DDL,
        old_columns,
        rows,
        {
            "r6_output_set_digest": None,
            "artifact_member_ids_json": "[]",
            "artifact_member_set_digest": None,
        },
    )
    _execute = _split_sql(_PUBLICATION_DDL)
    for statement in _execute:
        if statement.upper().startswith("CREATE INDEX"):
            connection.execute(statement)
    for statement in _split_sql(_RESULT_CONTEXT_INDEX_DDL):
        connection.execute(statement)


def _rebuild_launch_continuity_v3(connection: sqlite3.Connection) -> None:
    plan_table = "r7_continuity_plans"
    item_table = "r7_continuity_items"
    plan_columns = _table_columns_ordered(connection, plan_table)
    item_columns = _table_columns_ordered(connection, item_table)
    plan_rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % plan_table).fetchall()
    item_rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % item_table).fetchall()
    _drop_named_indexes(connection, _split_sql(_CONTINUITY_INDEX_DDL))
    old_plan = "__migration_old_" + plan_table
    old_item = "__migration_old_" + item_table
    connection.execute("ALTER TABLE %s RENAME TO %s" % (item_table, old_item))
    connection.execute("ALTER TABLE %s RENAME TO %s" % (plan_table, old_plan))
    connection.execute(_frozen_create_statement(_CONTINUITY_PLANS_DDL, plan_table))
    connection.execute(_frozen_create_statement(_CONTINUITY_ITEMS_DDL, item_table))
    new_plan_columns = _table_columns_ordered(connection, plan_table)
    new_item_columns = _table_columns_ordered(connection, item_table)
    plan_values = [
        tuple(
            row[plan_columns.index(column)] if column in plan_columns
            else ("" if column == "r6_output_set_digest" else None)
            for column in new_plan_columns
        )
        for row in plan_rows
    ]
    item_values = [
        tuple(
            row[item_columns.index(column)] for column in new_item_columns
        )
        for row in item_rows
    ]
    if plan_values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                plan_table,
                ",".join(new_plan_columns),
                ",".join("?" for _ in new_plan_columns),
            ),
            plan_values,
        )
    if item_values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                item_table,
                ",".join(new_item_columns),
                ",".join("?" for _ in new_item_columns),
            ),
            item_values,
        )
    connection.execute("DROP TABLE %s" % old_item)
    connection.execute("DROP TABLE %s" % old_plan)
    for statement in _split_sql(_CONTINUITY_INDEX_DDL):
        connection.execute(statement)


class _StepRunner:
    def __init__(self, owner: "MigrationRunner", step: MigrationStep) -> None:
        self.owner = owner
        self.step = step
        self.committed = False

    def _hook(self, suffix: str) -> None:
        self.owner._hook("migration.%s.%s" % (self.step.member, suffix))

    def _execute_statements(self, connection: sqlite3.Connection, sql: str) -> None:
        for statement in _split_sql(sql):
            connection.execute(statement)
    def _runtime_backfill(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != RUNTIME_V4:
            return
        # Added columns default to 0.  Reconstruct historical revisions from
        # immutable manifest timestamps, matching R1's accepted v4 migration
        # oracle without importing the mutable Store constructor.
        node_attempt_columns = _table_columns_ordered(connection, "node_attempts")
        if "manifest_revision" in node_attempt_columns:
            rows = connection.execute(
                "SELECT run_id,node_id,attempt_seq,created_at FROM node_attempts "
                "ORDER BY run_id,node_id,attempt_seq"
            ).fetchall()
            for run_id, node_id, attempt_seq, created_at in rows:
                revision_row = connection.execute(
                    "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
                    "ORDER BY revision DESC LIMIT 1",
                    (run_id, created_at or ""),
                ).fetchone()
                revision = 0 if revision_row is None else int(revision_row[0])
                connection.execute(
                    "UPDATE node_attempts SET manifest_revision=? WHERE run_id=? "
                    "AND node_id=? AND attempt_seq=?",
                    (revision, run_id, node_id, int(attempt_seq)),
                )
        node_run_columns = _table_columns_ordered(connection, "node_runs")
        if "manifest_revision" in node_run_columns:
            rows = connection.execute(
                "SELECT run_id,node_id,started_at FROM node_runs ORDER BY run_id,node_id"
            ).fetchall()
            for run_id, node_id, started_at in rows:
                latest = connection.execute(
                    "SELECT manifest_revision FROM node_attempts WHERE run_id=? AND node_id=? "
                    "ORDER BY attempt_seq DESC LIMIT 1",
                    (run_id, node_id),
                ).fetchone()
                if latest is not None:
                    revision = int(latest[0])
                else:
                    revision_row = connection.execute(
                        "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
                        "ORDER BY revision DESC LIMIT 1",
                        (run_id, started_at or ""),
                    ).fetchone()
                    revision = 0 if revision_row is None else int(revision_row[0])
                connection.execute(
                    "UPDATE node_runs SET manifest_revision=? WHERE run_id=? AND node_id=?",
                    (revision, run_id, node_id),
                )

    def _rebuild_runtime_columns(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != RUNTIME_V4:
            return
        for table in ("node_attempts", "node_runs"):
            old_columns = _table_columns_ordered(connection, table)
            rows = connection.execute(
                "SELECT * FROM %s ORDER BY rowid" % table
            ).fetchall()
            if table == "node_attempts":
                revisions = [
                    _runtime_manifest_revision(connection, row[0], row[7])
                    for row in rows
                ]
            else:
                revisions = [
                    _runtime_manifest_revision(connection, row[0], row[10])
                    for row in rows
                ]
            _rebuild_runtime_table(connection, table, old_columns, rows, revisions)

    def _rebuild_launch_v4_columns(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != LAUNCH_V3:
            return
        _rebuild_launch_publication_v3(connection)
        _rebuild_launch_continuity_v3(connection)

    def _launch_ddl(self, connection: sqlite3.Connection) -> None:
        version = self.step.source_version
        # v1 has no publication or continuity tables, v2 has no continuity,
        # and v3 has the tables but lacks four v4 columns.  CREATE IF NOT EXISTS
        # and ADD-if-absent make a committed step replay-safe.
        if version == LAUNCH_V1:
            self._execute_statements(connection, _PUBLICATION_DDL)
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_PLANS_DDL)
            self._execute_statements(connection, _CONTINUITY_ITEMS_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        elif version == LAUNCH_V2:
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_PLANS_DDL)
            self._execute_statements(connection, _CONTINUITY_ITEMS_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        elif version == LAUNCH_V3:
            self._rebuild_launch_v4_columns(connection)
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        else:
            raise MigrationError("migration_operation_conflict")

    def run(self, path: Path) -> None:
        if not self.owner._is_staging_path(path):
            raise MigrationError("migration_requires_staging")
        connection: Optional[sqlite3.Connection] = None
        transaction_started = False
        try:
            connection = sqlite3.connect(
                str(path), timeout=10.0, isolation_level=None, check_same_thread=False
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA foreign_keys=ON")
            marker = _read_meta_marker(connection, self.step.member)
            if marker != self.step.source_version:
                # A committed step may have advanced the target marker while
                # the ledger was not advanced.  Structural + marker oracles
                # make that state safely idempotent.
                if marker == self.step.target_version:
                    _assert_shape_on_connection(connection, self.step.member, str(self.step.target_version))
                    return
                raise MigrationError("migration_operation_conflict")
            self._hook("ddl.before")
            connection.execute("BEGIN IMMEDIATE")
            transaction_started = True
            if self.step.member == RUNTIME_MEMBER:
                self._rebuild_runtime_columns(connection)
                self._execute_statements(connection, _RUNTIME_CAPABILITY_DDL)
            elif self.step.member == LAUNCH_MEMBER:
                self._launch_ddl(connection)
            else:
                raise MigrationError("migration_operation_conflict")
            self._hook("ddl.after")
            if self.step.member == RUNTIME_MEMBER and self.step.source_version == RUNTIME_V4:
                self._hook("backfill.before")
                self._runtime_backfill(connection)
                self._hook("backfill.after")
            self._hook("oracle.before")
            _assert_shape_on_connection(connection, self.step.member, str(self.step.target_version))
            foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_rows:
                raise MigrationError("migration_verification_failed")
            self._hook("oracle.after")
            self._hook("marker.before")
            if self.step.member == RUNTIME_MEMBER:
                connection.execute(
                    "UPDATE meta SET value=? WHERE key='schema_version'",
                    (self.step.target_version,),
                )
            else:
                connection.execute(
                    "UPDATE r7_launch_registry_meta SET value=? WHERE key='schema_version'",
                    (self.step.target_version,),
                )
            self._hook("marker.after")
            self._hook("commit.before")
            connection.commit()
            self.committed = True
            try:
                self._hook("commit.after")
            except BaseException as exc:
                raise _CommittedStepFailure(
                    "migration.%s.commit.after" % self.step.member, exc
                ) from exc
        except _CommittedStepFailure:
            raise
        except BaseException:
            if connection is not None and transaction_started and not self.committed:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            raise
        finally:
            if connection is not None:
                connection.close()


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class MigrationRunner:
    """Run one synthetic/offline legacy-to-current project migration."""

    def __init__(
        self,
        runtime_root: Union[str, Path],
        canonical_project_id: str,
        *,
        project_dir: Optional[Union[str, Path]] = None,
        workspace_dir: Optional[Union[str, Path]] = None,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        failure_hook: Optional[Callable[[str], Any]] = None,
        failure_injector: Optional[Callable[[str], Any]] = None,
        ledger: Optional[MigrationOperationLedger] = None,
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _safe_project_id(
            canonical_project_id,
            "migration_project_blocked",
        )
        chosen = project_dir if project_dir is not None else workspace_dir
        self.workspace_dir = (
            Path(chosen)
            if chosen is not None
            else self.runtime_root / self.canonical_project_id
        )
        try:
            self.wait_seconds = float(wait_seconds)
        except (TypeError, ValueError) as exc:
            raise MigrationError("migration_project_blocked") from exc
        if self.wait_seconds < 0 or self.wait_seconds > 120:
            raise MigrationError("migration_project_blocked")
        self.failure_hook = failure_hook if failure_hook is not None else failure_injector
        self.ledger = ledger
        self._manager: Optional[ProjectBackupManager] = None
        self._manager_ledger: Optional[OperationLedger] = None

    @property
    def staging_root(self) -> Path:
        return self.runtime_root / MIGRATION_STAGING_DIR_NAME

    @property
    def rollback_root(self) -> Path:
        return self.runtime_root / MIGRATION_ROLLBACK_DIR_NAME

    def close(self) -> None:
        if self._manager is not None and self._manager_ledger is not None:
            self._manager_ledger.close()
            self._manager = None
            self._manager_ledger = None
        if self.ledger is not None:
            self.ledger.close()
            self.ledger = None

    def __enter__(self) -> "MigrationRunner":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _ledger(self) -> MigrationOperationLedger:
        if self.ledger is None:
            self.ledger = MigrationOperationLedger(self.runtime_root)
        return self.ledger

    def _backup_manager(self) -> ProjectBackupManager:
        if self._manager is None:
            self._manager_ledger = OperationLedger(self.runtime_root)
            self._manager = ProjectBackupManager(
                self.runtime_root,
                self.canonical_project_id,
                project_dir=self.workspace_dir,
                ledger=self._manager_ledger,
                wait_seconds=self.wait_seconds,
                failure_hook=self._backup_hook,
            )
        return self._manager

    def _backup_hook(self, point: str) -> Any:
        # Pass through real 09A hook names.  A migration callback can therefore
        # inject faults at both shared backup primitives and 09B boundaries.
        return self._invoke_failure_hook(str(point))

    def _invoke_failure_hook(self, point: str) -> Any:
        callback = self.failure_hook
        if callback is None:
            return None
        try:
            result = callback(str(point))
        except InjectedMigrationFailure:
            raise
        except BaseException as exc:
            raise InjectedMigrationFailure(point) from exc
        if isinstance(result, BaseException):
            raise InjectedMigrationFailure(point) from result
        if result is True:
            raise InjectedMigrationFailure(point)
        return result

    def _hook(self, point: str) -> None:
        self._invoke_failure_hook(point)

    def _is_staging_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
            root = self.staging_root.resolve()
            return resolved == root or root in resolved.parents
        except OSError:
            return False

    def inspect(self) -> ProjectSchemaInspection:
        # This is intentionally the first persistence operation in opening and
        # start-upgrade paths.  ProjectSchemaInspector uses mode=ro/query_only.
        return ProjectSchemaInspector(self.workspace_dir).inspect()

    def _ensure_complete_legacy(self, inspection: ProjectSchemaInspection) -> None:
        if inspection.classification is not SchemaClassification.LEGACY:
            raise MigrationError("migration_not_supported")
        if not inspection.can_view or not inspection.can_upgrade:
            raise MigrationError("migration_project_blocked")
        try:
            oracle = _workspace_oracle(self.workspace_dir)
            project_ids = set(oracle["project_ids"])
            if project_ids and project_ids != {self.canonical_project_id}:
                raise MigrationError("migration_project_blocked")
            runtime = self.workspace_dir / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
            if runtime.is_file():
                connection = _open_ro(runtime)
                try:
                    tables = _table_names(connection)
                    if "projects" in tables:
                        invalid = connection.execute(
                            "SELECT 1 FROM projects WHERE is_synthetic != 1 OR project_id != ? LIMIT 1",
                            (self.canonical_project_id,),
                        ).fetchone()
                        if invalid is not None:
                            raise MigrationError("migration_project_blocked")
                finally:
                    connection.close()
            manager = self._backup_manager()
            _artifact_hashes_and_bytes(manager, self.workspace_dir)
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc

    def _result(
        self,
        operation: Optional[MigrationOperation],
        state: str,
        *,
        plan: Optional[MigrationPlan] = None,
        requires_reopen: bool = False,
        message: str = "",
        next_action: str = "",
    ) -> MigrationResult:
        return MigrationResult(
            operation=operation,
            state=state,
            requires_reopen=requires_reopen,
            source_schema_set_digest=None if plan is None else plan.source_schema_set_digest,
            target_schema_set_digest=None if plan is None else plan.target_schema_set_digest,
            plan_digest=None if plan is None else plan.plan_digest,
            message=message,
            next_action=next_action,
        )

    def _cleanup_terminal_evidence(
        self,
        record: MigrationOperation,
        inspection: ProjectSchemaInspection,
    ) -> None:
        if record.status not in {STATUS_COMPLETED, STATUS_ROLLED_BACK}:
            return
        if record.status == STATUS_COMPLETED and inspection.classification is not SchemaClassification.CURRENT:
            return
        if (
            record.status == STATUS_ROLLED_BACK
            and inspection.classification
            not in {SchemaClassification.LEGACY, SchemaClassification.CURRENT}
        ):
            return
        stage_parent, _ = self._staging_paths(record.operation_id)
        rollback_path = self._rollback_path(record.operation_id)
        if record.staging_path and Path(record.staging_path) != stage_parent:
            raise MigrationError("migration_operation_conflict")
        if record.rollback_path and Path(record.rollback_path) != rollback_path:
            raise MigrationError("migration_operation_conflict")
        manager = self._backup_manager()
        if rollback_path.exists():
            manager._cleanup_path(rollback_path)
        if stage_parent.exists():
            manager._cleanup_path(stage_parent)

    def start_upgrade(
        self,
        idempotency_key: str,
        *,
        confirmation: bool = True,
        confirmed: Optional[bool] = None,
    ) -> MigrationResult:
        if confirmed is not None:
            confirmation = bool(confirmed)
        inspection = self.inspect()
        key = _safe_key(idempotency_key)
        ledger = self._ledger()
        records = ledger.list_for_project(self.canonical_project_id)
        existing: Optional[MigrationOperation] = None
        for candidate in records:
            if candidate.idempotency_key == key:
                existing = candidate
                break
        if any(candidate.status == STATUS_RETAINED_FOR_TRIAGE for candidate in records):
            raise MigrationError("migration_rollback_failed")

        if existing is not None:
            if existing.status == STATUS_MIGRATION_OPERATION_CONFLICT:
                raise MigrationError("migration_operation_conflict")
            plan = self._operation_plan(existing)
            if existing.status == STATUS_COMPLETED:
                self._cleanup_terminal_evidence(existing, inspection)
                return self._result(
                    existing,
                    STATUS_COMPLETED,
                    plan=plan,
                    requires_reopen=True,
                    message="项目格式已升级。请重新打开项目后继续使用。",
                    next_action="重新打开项目",
                )
            if existing.status == STATUS_ROLLED_BACK:
                self._cleanup_terminal_evidence(existing, inspection)
                return self._result(
                    existing,
                    STATUS_ROLLED_BACK,
                    plan=plan,
                    message="升级未完成，原项目仍可只读查看。可稍后重试。",
                    next_action="稍后重试升级",
                )
            if not confirmation:
                return self._result(
                    existing,
                    STATUS_LEGACY_READONLY,
                    plan=plan,
                    message="项目格式较旧，当前可以只读查看。",
                    next_action="开始升级或稍后处理",
                )
            directory_recovery = existing.status in {
                STATUS_SWITCHING,
                STATUS_LIVE_VERIFYING,
                STATUS_ROLLBACK_IN_PROGRESS,
            }
            if (
                not directory_recovery
                and inspection.classification
                not in {SchemaClassification.LEGACY, SchemaClassification.CURRENT}
            ):
                raise MigrationError("migration_not_supported")
            if inspection.classification is SchemaClassification.LEGACY:
                self._ensure_complete_legacy(inspection)
            try:
                if existing.status in {
                    STATUS_SWITCHING,
                    STATUS_LIVE_VERIFYING,
                    STATUS_ROLLBACK_IN_PROGRESS,
                }:
                    current = ledger.get(existing.operation_id)
                else:
                    self._ledger_update(
                        existing.operation_id,
                        status=STATUS_INSPECTING,
                        progress_percent=PROGRESS_INSPECTION_COMPLETE,
                        current_step="项目检查完成",
                        payload=plan.as_dict(),
                    )
                    current = ledger.get(existing.operation_id)
                return self._resume_or_execute(current, plan)
            except MigrationError:
                raise
            except (
                ProjectBackupError,
                MaintenanceGateError,
                sqlite3.Error,
                OSError,
                ValueError,
                TypeError,
            ) as exc:
                self._safe_failure(existing.operation_id, "sqlite_integrity_failed", str(exc))
                raise MigrationError("sqlite_integrity_failed") from exc

        if inspection.classification is SchemaClassification.CURRENT:
            return self._result(
                None,
                STATUS_ALREADY_CURRENT,
                message="项目格式已是当前版本。",
                next_action="继续使用项目",
            )
        if inspection.classification is not SchemaClassification.LEGACY:
            raise MigrationError("migration_not_supported")
        self._ensure_complete_legacy(inspection)
        plan = MigrationPlan.from_inspection(inspection)
        if not confirmation:
            return self._result(
                None,
                STATUS_LEGACY_READONLY,
                plan=plan,
                message="项目格式较旧，当前可以只读查看。",
                next_action="开始升级或稍后处理",
            )
        record = ledger.create_or_replay(
            key,
            self.canonical_project_id,
            source_schema_set_digest=plan.source_schema_set_digest,
            target_schema_set_digest=plan.target_schema_set_digest,
            plan_digest=plan.plan_digest,
            plan=plan.as_dict(),
        )
        try:
            self._ledger_update(
                record.operation_id,
                status=STATUS_INSPECTING,
                progress_percent=PROGRESS_INSPECTION_COMPLETE,
                current_step="项目检查完成",
                payload=plan.as_dict(),
            )
            current = ledger.get(record.operation_id)
            return self._resume_or_execute(current, plan)
        except MigrationError:
            raise
        except (
            ProjectBackupError,
            MaintenanceGateError,
            sqlite3.Error,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            self._safe_failure(record.operation_id, "sqlite_integrity_failed", str(exc))
            raise MigrationError("sqlite_integrity_failed") from exc

    upgrade = start_upgrade
    migrate = start_upgrade

    def _ledger_update(self, operation_id: str, **updates: Any) -> MigrationOperation:
        self._hook("migration.ledger_commit.before")
        record = self._ledger().update(operation_id, **updates)
        try:
            self._hook("migration.ledger_commit.after")
        except BaseException as exc:
            # The row is durable; retry/recovery must inspect actual stage state.
            raise _CommittedStepFailure("migration.ledger_commit.after", exc) from exc
        return record

    def _safe_failure(self, operation_id: str, code: str, detail: str = "") -> None:
        try:
            self._ledger().update(
                operation_id,
                status=STATUS_RETRYABLE_FAILED,
                error_code=code,
                error_message=_ERROR_MESSAGES.get(code, detail or "项目升级未完成。"),
                terminal_outcome=None,
            )
        except BaseException:
            pass

    def _operation_plan(self, record: MigrationOperation) -> MigrationPlan:
        payload = record.payload
        if "steps" not in payload:
            raise MigrationError("migration_ledger_corrupt")
        return MigrationPlan.from_mapping(payload)

    def _live_fingerprint(self, manager: ProjectBackupManager) -> str:
        try:
            # 09A fingerprints a consistent SQLite snapshot, not the main
            # database header while a WAL sidecar is active.  Reuse that
            # helper so the comparison is byte-identical to the backup
            # manifest and remains read-only for live project files.
            snapshot = manager.snapshot_workspace(
                "migration-fingerprint-" + self.canonical_project_id
            )
            return snapshot.fingerprint
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc

    def _prepare_backup(self, record: MigrationOperation, plan: MigrationPlan) -> MigrationOperation:
        manager = self._backup_manager()
        self._ledger_update(
            record.operation_id,
            status=STATUS_BACKUP_REQUIRED,
            progress_percent=PROGRESS_INSPECTION_COMPLETE,
            current_step="等待准备恢复点",
        )
        try:
            self._ledger_update(
                record.operation_id,
                status=STATUS_BACKUP_IN_PROGRESS,
                progress_percent=PROGRESS_INSPECTION_COMPLETE,
                current_step="正在准备恢复点",
            )
            backup = manager.backup("migration-backup-" + record.idempotency_key)
            if backup.package_path is None or backup.package_id is None:
                raise MigrationError("migration_project_blocked")
            manifest = dict(backup.manifest)
            source_fp = str(backup.source_workspace_fingerprint or manifest.get("source_workspace_fingerprint", ""))
            if not source_fp or source_fp != manifest.get("source_workspace_fingerprint"):
                raise MigrationError("migration_project_blocked")
            # 09A backup() already performs closure and reopen verification.  A
            # second preflight validates the published package independently.
            preflight = manager.preflight(
                backup.package_path,
                "migration-preflight-" + record.idempotency_key,
            )
            if preflight.staging_path is not None:
                manager._cleanup_path(preflight.staging_path.parent)
            payload = dict(plan.as_dict())
            payload.update(
                {
                    "package_id": backup.package_id,
                    "package_path": str(backup.package_path),
                    "source_workspace_fingerprint": source_fp,
                    "source_manifest": manifest,
                    "member_step_digests": dict(plan.member_step_digests),
                }
            )
            return self._ledger_update(
                record.operation_id,
                status=STATUS_BACKUP_VERIFIED,
                progress_percent=PROGRESS_BACKUP_VERIFIED,
                current_step="恢复点已完成",
                package_id=backup.package_id,
                package_path=str(backup.package_path),
                source_workspace_fingerprint=source_fp,
                payload=payload,
            )
        except MigrationError:
            raise
        except (ProjectBackupError, MaintenanceGateError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_failure(record.operation_id, "migration_project_blocked", str(exc))
            raise MigrationError("migration_project_blocked") from exc

    def _gate_event(self, operation_id: str, event: str) -> None:
        try:
            if event == "waiting_for_project":
                self._ledger().update(
                    operation_id,
                    status=STATUS_WAITING_FOR_PROJECT,
                    current_step="正在等待项目空闲",
                    maintenance_state=event,
                )
            elif event == "maintenance_acquired":
                self._ledger().update(
                    operation_id,
                    status=STATUS_MAINTENANCE_ACQUIRED,
                    progress_percent=PROGRESS_PROJECT_IDLE,
                    current_step="项目已空闲",
                    maintenance_state=event,
                )
            else:
                self._ledger().update(operation_id, maintenance_state=event)
        except BaseException:
            # A progress observation must not leak the maintenance lock.
            pass

    def _staging_paths(self, operation_id: str) -> Tuple[Path, Path]:
        operation_id = _safe_operation_id(operation_id)
        parent = self.staging_root / operation_id
        return parent, parent / "workspace"

    def _rollback_path(self, operation_id: str) -> Path:
        operation_id = _safe_operation_id(operation_id)
        return self.rollback_root / (self.canonical_project_id + "-" + operation_id)

    def _ensure_staging(
        self,
        record: MigrationOperation,
        manager: ProjectBackupManager,
        source_oracle: Mapping[str, Any],
    ) -> Tuple[Path, WorkspaceSnapshot, Mapping[str, bytes]]:
        parent, workspace = self._staging_paths(record.operation_id)
        if record.staging_path:
            recorded = Path(record.staging_path)
            if recorded != parent:
                raise MigrationError("migration_operation_conflict")
        if parent.exists() and not _replaceable(parent):
            raise MigrationError("migration_operation_conflict")
        if parent.exists() and workspace.exists():
            _assert_directory(workspace)
            _remove_sqlite_sidecars(workspace)
            _assert_no_sqlite_sidecars(workspace)
            members = manager.member_bytes(workspace)
            return parent, WorkspaceSnapshot(
                workspace,
                members,
                {},
                workspace_fingerprint(members),
            ), members
        if parent.exists() and not workspace.exists():
            manager._cleanup_path(parent)
        self._hook("migration.staging_create.before")
        _assert_directory(self.runtime_root)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        parent.mkdir(parents=True, exist_ok=False)
        _assert_same_device(self.runtime_root, self.staging_root, parent)
        try:
            snapshot = manager.snapshot_workspace(
                record.operation_id,
                destination=workspace,
                emit_hooks=False,
            )
            _remove_sqlite_sidecars(workspace)
            _assert_no_sqlite_sidecars(workspace)
            stage_oracle = _workspace_oracle(workspace)
            _compare_database_oracles(source_oracle, stage_oracle)
            source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
            stage_artifacts = _artifact_hashes_and_bytes(manager, workspace)
            _compare_artifacts(source_artifacts, stage_artifacts)
            self._hook("migration.staging_create.after")
            return parent, snapshot, snapshot.members
        except BaseException:
            manager._cleanup_path(parent)
            raise

    def _verify_stage_current(
        self,
        manager: ProjectBackupManager,
        stage_workspace: Path,
        source_oracle: Mapping[str, Any],
        source_artifacts: Mapping[str, bytes],
    ) -> None:
        inspection = ProjectSchemaInspector(stage_workspace).inspect()
        if inspection.classification is not SchemaClassification.CURRENT:
            raise MigrationError("migration_verification_failed")
        stage_oracle = _workspace_oracle(stage_workspace)
        _compare_database_oracles(source_oracle, stage_oracle)
        stage_artifacts = _artifact_hashes_and_bytes(manager, stage_workspace)
        _compare_artifacts(source_artifacts, stage_artifacts)
        _assert_no_sqlite_sidecars(stage_workspace)
        runtime = stage_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime.is_file():
            connection = _open_ro(runtime)
            try:
                manager._verify_audit_chain(connection)
            except ProjectBackupError as exc:
                raise MigrationError("migration_verification_failed") from exc
            finally:
                connection.close()

    def _step_target_applied(self, step: MigrationStep, stage_workspace: Path) -> bool:
        path = self._member_path(stage_workspace, step.member)
        if path is None or not path.is_file():
            return False
        report = inspect_member(path, step.member)
        if step.member == RUNTIME_MEMBER:
            return report.classification is SchemaClassification.CURRENT and report.schema_version == RUNTIME_V6
        return report.classification is SchemaClassification.CURRENT and report.schema_version == LAUNCH_V4

    @staticmethod
    def _member_path(workspace: Path, member: str) -> Optional[Path]:
        relative = {
            RUNTIME_MEMBER: Path(RUNTIME_DIR_NAME) / RUNTIME_DB_NAME,
            PROFILE_MEMBER: Path(PROFILE_DB_NAME),
            BINDING_MEMBER: Path(RUN_BINDING_DB_NAME),
            LAUNCH_MEMBER: Path(LAUNCH_REGISTRY_DB_NAME),
            RISK_MEMBER: Path(RISK_RULE_DB_NAME),
        }.get(member)
        return None if relative is None else workspace / relative

    def _run_steps(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
        stage_workspace: Path,
    ) -> MigrationOperation:
        source_oracle = _workspace_oracle(self.workspace_dir)
        manager = self._backup_manager()
        source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
        current = record
        for step in plan.steps:
            if self._step_target_applied(step, stage_workspace):
                current = self._ledger_update(
                    current.operation_id,
                    status=STATUS_MIGRATING,
                    progress_percent=PROGRESS_CONTENT_UPDATED,
                    current_step="%s内容已更新" % step.member,
                    current_member=step.member,
                    member_step_digest=step.step_digest,
                )
                continue
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_MIGRATING,
                progress_percent=PROGRESS_CONTENT_UPDATED,
                current_step="正在更新%s" % step.member,
                current_member=step.member,
                member_step_digest=step.step_digest,
            )
            runner = _StepRunner(self, step)
            try:
                runner.run(self._member_path(stage_workspace, step.member) or Path(""))
            except _CommittedStepFailure:
                raise
            except BaseException:
                if runner.committed:
                    raise _CommittedStepFailure("migration.%s.commit.after" % step.member, RuntimeError("committed"))
                raise
            if not self._step_target_applied(step, stage_workspace):
                raise MigrationError("migration_verification_failed")
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_MIGRATING,
                progress_percent=PROGRESS_CONTENT_UPDATED,
                current_step="%s内容已更新" % step.member,
                current_member=step.member,
                member_step_digest=step.step_digest,
            )
        self._hook("migration.project_oracle.before")
        self._verify_stage_current(manager, stage_workspace, source_oracle, source_artifacts)
        self._hook("migration.project_oracle.after")
        return self._ledger_update(
            current.operation_id,
            status=STATUS_STAGED_VERIFIED,
            progress_percent=PROGRESS_STAGED_VERIFIED,
            current_step="升级副本核验完成",
            current_member=None,
            member_step_digest=None,
        )

    def _checkpoint_workspace(self, workspace: Path) -> None:
        for relative in _member_rel_paths(workspace):
            if relative.endswith(".json") or relative.endswith("/artifacts"):
                continue
            path = workspace / Path(relative)
            if not path.is_file():
                continue
            connection: Optional[sqlite3.Connection] = None
            try:
                connection = sqlite3.connect(str(path), timeout=0.0, isolation_level=None)
                connection.execute("PRAGMA busy_timeout=0")
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                connection.execute("PRAGMA journal_mode=DELETE")
            except sqlite3.OperationalError as exc:
                raise MigrationError("project_busy_retry_later") from exc
            except sqlite3.Error as exc:
                raise MigrationError("migration_verification_failed") from exc
            finally:
                if connection is not None:
                    connection.close()

    def _quiesce_live(self, manager: ProjectBackupManager) -> None:
        self._hook("migration.live_quiesce.before")
        try:
            manager._quiesce()
        except ProjectBackupError as exc:
            raise MigrationError(exc.code) from exc
        self._hook("migration.live_quiesce.after")

    def _verify_live_target(
        self,
        manager: ProjectBackupManager,
        expected_oracle: Mapping[str, Any],
        expected_artifacts: Mapping[str, bytes],
    ) -> None:
        self._hook("migration.live_reopen.before")
        inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
        if inspection.classification is not SchemaClassification.CURRENT:
            raise MigrationError("migration_verification_failed")
        actual_oracle = _workspace_oracle(self.workspace_dir)
        _compare_database_oracles(expected_oracle, actual_oracle)
        actual_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
        _compare_artifacts(expected_artifacts, actual_artifacts)
        _assert_no_sqlite_sidecars(self.workspace_dir)
        for relative in _member_rel_paths(self.workspace_dir):
            if relative.endswith(".json"):
                continue
            connection = _open_ro(self.workspace_dir / Path(relative))
            connection.close()
        self._hook("migration.live_reopen.after")
        self._hook("migration.identity_verification.before")
        if actual_oracle.get("project_ids") and actual_oracle.get("project_ids") != [self.canonical_project_id]:
            raise MigrationError("migration_verification_failed")
        self._hook("migration.identity_verification.after")

    def _mark_rollback_in_progress(self, operation_id: str) -> None:
        try:
            self._ledger().update(
                operation_id,
                status=STATUS_ROLLBACK_IN_PROGRESS,
                current_step="正在恢复原项目",
                directory_switch_stage="rollback_in_progress",
            )
        except BaseException:
            # Safety action continues even if the observability write is down.
            pass

    def _rollback_after_failure(
        self,
        record: MigrationOperation,
        rollback_path: Path,
        stage_parent: Path,
    ) -> bool:
        try:
            self._hook("migration.rollback.before")
            failed_live = stage_parent / "failed-live"
            if self.workspace_dir.exists():
                if failed_live.exists():
                    self._backup_manager()._cleanup_path(failed_live)
                _replace_or_raise(self.workspace_dir, failed_live)
            if rollback_path.exists():
                _replace_or_raise(rollback_path, self.workspace_dir)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            self._hook("migration.rollback.after")
            return self.workspace_dir.is_dir()
        except BaseException:
            return False

    def _verify_source_workspace(
        self,
        manager: ProjectBackupManager,
        record: MigrationOperation,
        workspace: Path,
    ) -> None:
        if not workspace.is_dir():
            raise MigrationError("workspace_not_found")
        package_path = Path(record.package_path or "")
        if not package_path.is_file():
            raise MigrationError("migration_project_blocked")
        source_operation = "migration-source-" + record.operation_id
        fallback_parent = self.runtime_root / ".mmbackup-staging" / source_operation
        fallback_preexisting = fallback_parent.exists()
        source_manager = ProjectBackupManager(
            self.runtime_root,
            self.canonical_project_id,
            workspace_dir=workspace,
            ledger=manager.ledger,
            wait_seconds=self.wait_seconds,
            max_archive_members=manager.max_archive_members,
            max_member_bytes=manager.max_member_bytes,
            max_archive_bytes=manager.max_archive_bytes,
        )
        try:
            manifest, extracted_parent, _, package_id = source_manager._inspect_archive(
                source_operation,
                package_path,
            )
            if record.package_id is None or package_id != record.package_id:
                raise MigrationError("migration_operation_conflict")
            source_workspace = extracted_parent / "workspace"
            source_manager._verify_workspace(
                source_workspace,
                manifest,
                verify_manifest_summary=True,
            )
            expected_oracle = _workspace_oracle(source_workspace)
            expected_artifacts = _artifact_hashes_and_bytes(source_manager, source_workspace)
            inspection = ProjectSchemaInspector(workspace).inspect()
            if inspection.classification is not SchemaClassification.LEGACY:
                raise MigrationError("migration_verification_failed")
            actual_oracle = _workspace_oracle(workspace)
            _compare_database_oracles(expected_oracle, actual_oracle)
            actual_artifacts = _artifact_hashes_and_bytes(manager, workspace)
            _compare_artifacts(expected_artifacts, actual_artifacts)
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc
        finally:
            if extracted_parent is not None or not fallback_preexisting:
                source_manager._cleanup_path(extracted_parent or fallback_parent)

    def _recover_directory_state(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
    ) -> Optional[MigrationResult]:
        if record.status not in {
            STATUS_SWITCHING,
            STATUS_LIVE_VERIFYING,
            STATUS_ROLLBACK_IN_PROGRESS,
        }:
            return None
        stage_parent, stage_workspace = self._staging_paths(record.operation_id)
        rollback_path = self._rollback_path(record.operation_id)
        if record.staging_path and Path(record.staging_path) != stage_parent:
            raise MigrationError("migration_operation_conflict")
        if record.rollback_path and Path(record.rollback_path) != rollback_path:
            raise MigrationError("migration_operation_conflict")

        def retain(detail: str) -> MigrationResult:
            try:
                self._ledger().update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    current_step="升级现场已保留待处置",
                    error_code="migration_rollback_failed",
                    error_message=_ERROR_MESSAGES["migration_rollback_failed"],
                    rollback_path=str(rollback_path) if rollback_path.exists() else None,
                    staging_path=str(stage_parent) if stage_parent.exists() else None,
                    directory_switch_stage="retained_for_triage",
                )
            except BaseException:
                pass
            raise MigrationError(
                "migration_rollback_failed",
                details={"operation_id": record.operation_id, "detail": detail},
            )

        def rolled_back() -> MigrationResult:
            current = self._ledger().update(
                record.operation_id,
                status=STATUS_ROLLED_BACK,
                progress_percent=max(record.progress_percent, PROGRESS_SWITCHED),
                current_step="原项目已恢复",
                terminal_outcome=STATUS_ROLLED_BACK,
                rollback_path=str(rollback_path) if rollback_path.exists() else None,
                staging_path=str(stage_parent) if stage_parent.exists() else None,
                directory_switch_stage="rolled_back",
                error_code=None,
                error_message=None,
            )
            manager = self._backup_manager()
            if rollback_path.exists():
                manager._cleanup_path(rollback_path)
            if stage_parent.exists():
                manager._cleanup_path(stage_parent)
            return self._result(
                current,
                STATUS_ROLLED_BACK,
                plan=plan,
                message="升级未完成，原项目仍可只读查看。可稍后重试。",
                next_action="稍后重试升级",
            )

        def restore_and_finish(manager: ProjectBackupManager) -> MigrationResult:
            self._mark_rollback_in_progress(record.operation_id)
            if not self._rollback_after_failure(record, rollback_path, stage_parent):
                return retain("恢复点切换失败")
            try:
                self._verify_source_workspace(manager, record, self.workspace_dir)
            except BaseException as exc:
                return retain(str(exc))
            return rolled_back()

        if not rollback_path.exists():
            if self.workspace_dir.is_dir() and record.status == STATUS_SWITCHING:
                inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
                if inspection.classification is SchemaClassification.LEGACY:
                    # The ledger checkpoint can precede the first rename.
                    return None
            if self.workspace_dir.is_dir():
                return retain("切换记录存在但原项目恢复点缺失")
            return retain("切换记录存在但项目目录缺失")

        manager = self._backup_manager()
        gate = ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(record.operation_id, event),
        )
        with gate.exclusive():
            try:
                _assert_directory(rollback_path)
                self._checkpoint_workspace(rollback_path)
                _remove_sqlite_sidecars(rollback_path)
                _assert_no_sqlite_sidecars(rollback_path)
            except BaseException as exc:
                return retain(str(exc))

            if self.workspace_dir.is_dir():
                inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
                if inspection.classification is SchemaClassification.CURRENT:
                    try:
                        self._verify_source_workspace(manager, record, rollback_path)
                        expected_workspace = self.workspace_dir
                        if stage_workspace.is_dir():
                            stage_inspection = ProjectSchemaInspector(stage_workspace).inspect()
                            if stage_inspection.classification is not SchemaClassification.CURRENT:
                                return retain("切换副本格式无法核对")
                            expected_workspace = stage_workspace
                        expected_oracle = _workspace_oracle(expected_workspace)
                        expected_artifacts = _artifact_hashes_and_bytes(manager, expected_workspace)
                        self._verify_live_target(manager, expected_oracle, expected_artifacts)
                    except BaseException:
                        return restore_and_finish(manager)
                    current = self._ledger().update(
                        record.operation_id,
                        status=STATUS_COMPLETED,
                        progress_percent=PROGRESS_COMPLETE,
                        current_step="升级完成",
                        terminal_outcome=STATUS_COMPLETED,
                        rollback_path=str(rollback_path),
                        staging_path=str(stage_parent),
                        directory_switch_stage="verified",
                        error_code=None,
                        error_message=None,
                    )
                    manager._cleanup_path(rollback_path)
                    if stage_parent.exists():
                        manager._cleanup_path(stage_parent)
                    return self._result(
                        current,
                        STATUS_COMPLETED,
                        plan=plan,
                        requires_reopen=True,
                        message="项目格式已升级。请重新打开项目后继续使用。",
                        next_action="重新打开项目",
                    )

                if inspection.classification is SchemaClassification.LEGACY:
                    try:
                        self._verify_source_workspace(manager, record, self.workspace_dir)
                        self._verify_source_workspace(manager, record, rollback_path)
                    except BaseException:
                        return restore_and_finish(manager)
                    return rolled_back()

            return restore_and_finish(manager)

    def _switch_and_verify(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
        stage_parent: Path,
        stage_workspace: Path,
    ) -> MigrationOperation:
        manager = self._backup_manager()
        rollback_path = self._rollback_path(record.operation_id)
        expected_oracle = _workspace_oracle(stage_workspace)
        expected_artifacts = _artifact_hashes_and_bytes(manager, stage_workspace)
        _assert_same_device(self.runtime_root, stage_parent, self.rollback_root)
        self.rollback_root.mkdir(parents=True, exist_ok=True)
        _assert_same_device(self.runtime_root, self.rollback_root)
        if rollback_path.exists():
            raise MigrationError("migration_operation_conflict")
        current = self._ledger_update(
            record.operation_id,
            status=STATUS_SWITCHING,
            progress_percent=PROGRESS_SWITCHED,
            current_step="正在切换项目",
            rollback_path=str(rollback_path),
            staging_path=str(stage_parent),
            directory_switch_stage="ready",
        )
        old_live_moved = False
        try:
            self._hook("migration.switch.live_to_rollback.before")
            if not self.workspace_dir.exists():
                raise MigrationError("migration_source_changed")
            _replace_or_raise(self.workspace_dir, rollback_path)
            old_live_moved = True
            self._checkpoint_workspace(rollback_path)
            _remove_sqlite_sidecars(rollback_path)
            _assert_no_sqlite_sidecars(rollback_path)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            current = self._ledger_update(
                current.operation_id,
                directory_switch_stage="live_to_rollback",
                current_step="原项目已保留",
            )
            self._hook("migration.switch.live_to_rollback.after")
            self._hook("migration.switch.staging_to_live.before")
            _replace_or_raise(stage_workspace, self.workspace_dir)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_LIVE_VERIFYING,
                progress_percent=PROGRESS_SWITCHED,
                current_step="项目已切换，正在重新核对",
                directory_switch_stage="staging_to_live",
            )
            self._hook("migration.switch.staging_to_live.after")
            self._verify_live_target(manager, expected_oracle, expected_artifacts)
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_COMPLETED,
                progress_percent=PROGRESS_COMPLETE,
                current_step="升级完成",
                terminal_outcome=STATUS_COMPLETED,
                rollback_path=str(rollback_path),
                staging_path=str(stage_parent),
                directory_switch_stage="verified",
                payload=dict(current.payload),
            )
            # The rollback copy is no longer needed after independent reopen
            # verification, but the ledger keeps its path as evidence.
            manager._cleanup_path(rollback_path)
            manager._cleanup_path(stage_parent)
            return current
        except _CommittedStepFailure:
            raise
        except BaseException as exc:
            if old_live_moved:
                self._mark_rollback_in_progress(current.operation_id)
                rolled_back = self._rollback_after_failure(current, rollback_path, stage_parent)
                if rolled_back:
                    self._ledger().update(
                        current.operation_id,
                        status=STATUS_ROLLED_BACK,
                        progress_percent=current.progress_percent,
                        current_step="原项目已恢复",
                        terminal_outcome=STATUS_ROLLED_BACK,
                        rollback_path=str(rollback_path),
                        staging_path=str(stage_parent) if stage_parent.exists() else None,
                        directory_switch_stage="rolled_back",
                        error_code=(exc.code if isinstance(exc, MigrationError) else "migration_switch_failed"),
                        error_message=(
                            exc.message if isinstance(exc, MigrationError) else _ERROR_MESSAGES["migration_switch_failed"]
                        ),
                    )
                    # Preserve evidence only when a failed-live remains; the
                    # restored source itself is the live truth.
                    if stage_parent.exists():
                        manager._cleanup_path(stage_parent)
                    return self._ledger().get(current.operation_id)
                self._ledger().update(
                    current.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    current_step="升级现场已保留待处置",
                    error_code="migration_rollback_failed",
                    error_message=_ERROR_MESSAGES["migration_rollback_failed"],
                    rollback_path=str(rollback_path) if rollback_path.exists() else str(stage_parent),
                    staging_path=str(stage_parent),
                    directory_switch_stage="retained_for_triage",
                )
                raise MigrationError("migration_rollback_failed") from exc
            # No directory was switched; old live is intact.  A committed DB
            # step or an injected ledger boundary leaves staging for retry.
            if isinstance(exc, _CommittedStepFailure):
                raise
            manager._cleanup_path(stage_parent)
            self._safe_failure(current.operation_id, getattr(exc, "code", "migration_verification_failed"), str(exc))
            raise

    def _resume_or_execute(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
    ) -> MigrationResult:
        manager = self._backup_manager()
        recovered = self._recover_directory_state(record, plan)
        if recovered is not None:
            return recovered
        if record.package_path is None or record.source_workspace_fingerprint is None:
            record = self._prepare_backup(record, plan)
        package_path = Path(record.package_path or "")
        if not package_path.is_file():
            raise MigrationError("migration_project_blocked")
        stage_parent, stage_workspace = self._staging_paths(record.operation_id)
        gate = ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(record.operation_id, event),
        )
        try:
            with gate.exclusive():
                self._hook("migration.source_recheck.before")
                live_fp = self._live_fingerprint(manager)
                if live_fp != record.source_workspace_fingerprint:
                    conflict = self._ledger().update(
                        record.operation_id,
                        status=STATUS_MIGRATION_OPERATION_CONFLICT,
                        terminal_outcome=STATUS_MIGRATION_OPERATION_CONFLICT,
                        current_step="项目内容已变化",
                        error_code=STATUS_MIGRATION_OPERATION_CONFLICT,
                        error_message=_ERROR_MESSAGES[STATUS_MIGRATION_OPERATION_CONFLICT],
                        directory_switch_stage="source_drift",
                    )
                    manager._cleanup_path(stage_parent)
                    raise MigrationError(
                        "migration_operation_conflict",
                        details={"operation_id": conflict.operation_id},
                    )
                self._hook("migration.source_recheck.after")
                self._quiesce_live(manager)
                source_oracle = _workspace_oracle(self.workspace_dir)
                source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
                current = self._ledger().get(record.operation_id)
                if current.status in {
                    STATUS_BACKUP_VERIFIED,
                    STATUS_BACKUP_REQUIRED,
                    STATUS_BACKUP_IN_PROGRESS,
                    STATUS_INSPECTING,
                    STATUS_REQUESTED,
                    STATUS_RETRYABLE_FAILED,
                }:
                    current = self._ledger_update(
                        current.operation_id,
                        status=STATUS_STAGING,
                        progress_percent=PROGRESS_STAGING_COMPLETE,
                        current_step="正在建立升级副本",
                        staging_path=str(stage_parent),
                    )
                self._ensure_staging(current, manager, source_oracle)
                current = self._ledger().get(current.operation_id)
                if not plan.steps:
                    raise MigrationError("migration_operation_conflict")
                current = self._run_steps(current, plan, stage_workspace)
                current = self._switch_and_verify(
                    current,
                    plan,
                    stage_parent,
                    stage_workspace,
                )
                if current.status == STATUS_COMPLETED:
                    return self._result(
                        current,
                        STATUS_COMPLETED,
                        plan=plan,
                        requires_reopen=True,
                        message="项目格式已升级。请重新打开项目后继续使用。",
                        next_action="重新打开项目",
                    )
                if current.status == STATUS_ROLLED_BACK:
                    return self._result(
                        current,
                        STATUS_ROLLED_BACK,
                        plan=plan,
                        message="升级未完成，原项目仍可只读查看。可稍后重试。",
                        next_action="稍后重试升级",
                    )
                return self._result(current, current.status, plan=plan)
        except _CommittedStepFailure:
            # Preserve sibling staging and ledger checkpoint for same-key replay.
            raise
        except ProjectBusyError as exc:
            self._safe_failure(record.operation_id, exc.code, exc.message)
            manager._cleanup_path(stage_parent)
            raise MigrationError(exc.code, exc.message) from exc
        except MigrationError as exc:
            current = self._ledger().get(record.operation_id)
            if current.status not in TERMINAL_STATES:
                self._safe_failure(record.operation_id, exc.code, exc.message)
            raise
        except (
            ProjectBackupError,
            MaintenanceGateError,
            OSError,
            sqlite3.Error,
            ValueError,
            TypeError,
        ) as exc:
            manager._cleanup_path(stage_parent)
            self._safe_failure(
                record.operation_id,
                "migration_verification_failed",
                str(exc),
            )
            raise MigrationError("migration_verification_failed") from exc

    def recover(self, operation_id: Optional[str] = None) -> Tuple[MigrationResult, ...]:
        # Recovery is explicitly separate from ordinary open; it still takes a
        # fresh read-only schema snapshot before replaying a selected operation.
        initial = self.inspect()
        ledger = self._ledger()
        records = (
            [ledger.get(operation_id)]
            if operation_id
            else ledger.list_recovery(self.canonical_project_id)
        )
        results: List[MigrationResult] = []
        for record in records:
            plan = self._operation_plan(record)
            if record.status in TERMINAL_STATES:
                if record.status == STATUS_COMPLETED:
                    self._cleanup_terminal_evidence(record, initial)
                    results.append(
                        self._result(
                            record,
                            STATUS_COMPLETED,
                            plan=plan,
                            requires_reopen=True,
                            message="项目格式已升级。请重新打开项目后继续使用。",
                            next_action="重新打开项目",
                        )
                    )
                elif record.status == STATUS_ROLLED_BACK:
                    self._cleanup_terminal_evidence(record, initial)
                continue
            try:
                self._hook("migration.recovery.before")
                result = self._resume_or_execute(record, plan)
                self._hook("migration.recovery.after")
                results.append(result)
            except MigrationError as exc:
                current = ledger.get(record.operation_id)
                if current.status in TERMINAL_STATES:
                    results.append(self._result(current, current.status, plan=plan))
                else:
                    raise exc
        return tuple(results)

    recover_pending = recover
    startup_recovery_scan = recover

    def open_project(self) -> ProjectSchemaInspection:
        initial = self.inspect()
        # The read-only inspector remains first.  The subsequent root-ledger
        # scan is the only durable lookup needed to detect crash leftovers.
        records = self._ledger().list_for_project(self.canonical_project_id)
        if any(record.status == STATUS_RETAINED_FOR_TRIAGE for record in records):
            raise MigrationError("migration_rollback_failed")
        for record in records:
            self._cleanup_terminal_evidence(record, initial)
        pending = [record for record in records if record.status in PUBLIC_RECOVERY_STATES]
        if pending:
            self.recover()
            return self.inspect()
        return initial


    def apply_callback(
        self,
        operation_id: str,
        *,
        plan_digest: str,
        expected_state: str,
        **updates: Any,
    ) -> MigrationOperation:
        return self._ledger().apply_callback(
            operation_id,
            plan_digest=plan_digest,
            expected_state=expected_state,
            **updates,
        )



def _infer_staging_runtime_root(staged_path: Path) -> Path:
    resolved = staged_path.resolve()
    parts = resolved.parts
    try:
        marker_index = parts.index(MIGRATION_STAGING_DIR_NAME)
    except ValueError as exc:
        raise MigrationError("migration_requires_staging") from exc
    if marker_index == 0:
        return Path(parts[0])
    return Path(*parts[:marker_index])


def migrate_staged_member(
    staged_path: Union[str, Path],
    member: str,
    source_version: str,
    *,
    target_version: Optional[str] = None,
    runtime_root: Optional[Union[str, Path]] = None,
    failure_hook: Optional[Callable[[str], Any]] = None,
    failure_injector: Optional[Callable[[str], Any]] = None,
) -> MigrationStep:
    """Apply one legacy member step to an already-created sibling staging DB.

    This is the narrow migration seam for storage-specific tests and offline
    tooling.  It never accepts a live-project path, creates a ledger row, or
    opens a mutable product store; the full :class:`MigrationRunner` remains
    responsible for backup, cross-member verification, directory switching,
    and recovery.
    """
    path = Path(staged_path)
    if member not in {RUNTIME_MEMBER, LAUNCH_MEMBER}:
        raise MigrationError("migration_operation_conflict")
    expected_target = (
        RUNTIME_V6 if member == RUNTIME_MEMBER else LAUNCH_V4
    )
    if target_version is None:
        target_version = expected_target
    if target_version != expected_target:
        raise MigrationError("migration_operation_conflict")
    allowed_sources = (
        {RUNTIME_V4, RUNTIME_V5}
        if member == RUNTIME_MEMBER
        else {LAUNCH_V1, LAUNCH_V2, LAUNCH_V3}
    )
    if source_version not in allowed_sources or not path.is_file():
        raise MigrationError("migration_requires_staging")
    root = (
        Path(runtime_root)
        if runtime_root is not None
        else _infer_staging_runtime_root(path)
    )
    runner = MigrationRunner(
        root,
        "staged-member",
        failure_hook=failure_hook if failure_hook is not None else failure_injector,
    )
    try:
        if not runner._is_staging_path(path):
            raise MigrationError("migration_requires_staging")
        step = MigrationStep(
            member=member,
            source_version=source_version,
            target_version=target_version,
            actions=("explicit_staging_step", "verify_exact_target_shape", "update_marker_last"),
        )
        _StepRunner(runner, step).run(path)
        return step
    finally:
        runner.close()


def migrate_runtime_staging(
    staged_path: Union[str, Path],
    source_version: str,
    **kwargs: Any,
) -> MigrationStep:
    return migrate_staged_member(
        staged_path,
        RUNTIME_MEMBER,
        source_version,
        **kwargs,
    )


def migrate_launch_registry_staging(
    staged_path: Union[str, Path],
    source_version: str,
    **kwargs: Any,
) -> MigrationStep:
    return migrate_staged_member(
        staged_path,
        LAUNCH_MEMBER,
        source_version,
        **kwargs,
    )


# Functional entry points keep tests and small offline callers concise.
def inspect_project_schema(workspace: Union[str, Path]) -> ProjectSchemaInspection:
    return ProjectSchemaInspector(workspace).inspect()


def start_project_upgrade(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    idempotency_key: str,
    *,
    confirmation: bool = True,
    confirmed: Optional[bool] = None,
    **kwargs: Any,
) -> MigrationResult:
    runner = MigrationRunner(runtime_root, canonical_project_id, **kwargs)
    try:
        return runner.start_upgrade(
            idempotency_key,
            confirmation=confirmation,
            confirmed=confirmed,
        )
    finally:
        runner.close()


# A source-enumerated list for deterministic failure-injection matrices.  The
# list intentionally includes every boundary implemented above, while DB step
# hooks are generated from the actual plan member/version in _StepRunner.
FAILURE_HOOK_POINTS = (
    "migration.source_recheck.before",
    "migration.source_recheck.after",
    "migration.staging_create.before",
    "migration.staging_create.after",
    "migration.live_quiesce.before",
    "migration.live_quiesce.after",
    "migration.project_oracle.before",
    "migration.project_oracle.after",
    "migration.switch.live_to_rollback.before",
    "migration.switch.live_to_rollback.after",
    "migration.switch.staging_to_live.before",
    "migration.switch.staging_to_live.after",
    "migration.live_reopen.before",
    "migration.live_reopen.after",
    "migration.identity_verification.before",
    "migration.identity_verification.after",
    "migration.rollback.before",
    "migration.rollback.after",
    "migration.ledger_commit.before",
    "migration.ledger_commit.after",
    "migration.recovery.before",
    "migration.recovery.after",
) + tuple(
    "migration.%s.%s.%s" % (member, stage, boundary)
    for member, stages in (
        (RUNTIME_MEMBER, ("ddl", "backfill", "oracle", "marker", "commit")),
        (LAUNCH_MEMBER, ("ddl", "oracle", "marker", "commit")),
    )
    for stage in stages
    for boundary in ("before", "after")
)
HOOK_POINTS = FAILURE_HOOK_POINTS


__all__ = [
    "MigrationError",
    "FAILURE_HOOK_POINTS",
    "HOOK_POINTS",
    "LAUNCH_V1",
    "LAUNCH_V2",
    "LAUNCH_V3",
    "LAUNCH_V4",
    "MIGRATION_OPERATION_KIND",
    "MIGRATION_ROLLBACK_DIR_NAME",
    "MIGRATION_STAGING_DIR_NAME",
    "InjectedMigrationFailure",
    "MigrationOperation",
    "MigrationOperationLedger",
    "MigrationPlan",
    "MigrationResult",
    "migrate_launch_registry_staging",
    "migrate_runtime_staging",
    "migrate_staged_member",
    "MigrationRunner",
    "MigrationStep",
    "PROGRESS_BACKUP_VERIFIED",
    "PROGRESS_REQUEST_ACCEPTED",
    "PROGRESS_COMPLETE",
    "PROGRESS_CONTENT_UPDATED",
    "PROGRESS_INSPECTION_COMPLETE",
    "PROGRESS_PROJECT_IDLE",
    "PROGRESS_SWITCHED",
    "PROGRESS_STAGED_VERIFIED",
    "PROGRESS_STAGING_COMPLETE",
    "PUBLIC_RECOVERY_STATES",
    "RUNTIME_V4",
    "RUNTIME_V5",
    "RUNTIME_V6",
    "STATUS_REQUESTED",
    "STATUS_ALREADY_CURRENT",
    "STATUS_BACKUP_IN_PROGRESS",
    "STATUS_BACKUP_REQUIRED",
    "STATUS_BACKUP_VERIFIED",
    "STATUS_BLOCKED",
    "STATUS_COMPLETED",
    "STATUS_INSPECTING",
    "STATUS_LEGACY_READONLY",
    "STATUS_LIVE_VERIFYING",
    "STATUS_MAINTENANCE_ACQUIRED",
    "STATUS_MIGRATING",
    "STATUS_MIGRATION_OPERATION_CONFLICT",
    "STATUS_ROLLED_BACK",
    "STATUS_RETAINED_FOR_TRIAGE",
    "STATUS_RETRYABLE_FAILED",
    "TERMINAL_STATES",
    "STATUS_ROLLBACK_IN_PROGRESS",
    "STATUS_STAGED_VERIFIED",
    "STATUS_STAGING",
    "STATUS_SWITCHING",
    "STATUS_WAITING_FOR_PROJECT",
    "inspect_project_schema",
    "start_project_upgrade",
]
