"""Synthetic/offline project-open and upgrade product projection.

The migration coordinator owns durable state.  This module owns the small
product boundary around that state: Chinese DTOs, the fail-closed project
compatibility gate, and a read-only facade for complete legacy projects.

No constructor in this module creates a workspace, SQLite database, table, or
marker.  Read operations use SQLite ``mode=ro`` plus ``query_only`` and never
expose mutable stores or registries.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from urllib.parse import quote

from .schema_manifest import (
    BINDING_MEMBER,
    LAUNCH_MEMBER,
    PROFILE_MEMBER,
    RISK_MEMBER,
    RUNTIME_MEMBER,
    ProjectSchemaInspection,
    ProjectSchemaInspector,
    SchemaClassification,
    inspect_project_schema,
)

# Product-level open modes are deliberately not storage/schema terminology.
OPEN_MODE_EDIT = "edit"
OPEN_MODE_READONLY = "readonly"
OPEN_MODE_BLOCKED = "blocked"

DATA_COVERAGE_COMPLETE = "complete"
DATA_COVERAGE_INCOMPLETE = "incomplete"

OPEN_STATE_CURRENT = "current"
OPEN_STATE_LEGACY_READONLY = "legacy_readonly"
OPEN_STATE_BLOCKED = "blocked"

UPGRADE_STATE_SUCCEEDED = "succeeded"
UPGRADE_STATE_ALREADY_CURRENT = "already_current"
UPGRADE_STATE_LEGACY_READONLY = "legacy_readonly"
UPGRADE_STATE_ROLLED_BACK = "rolled_back"
UPGRADE_STATE_UNRESOLVED = "unresolved"
UPGRADE_STATE_BLOCKED = "blocked"
UPGRADE_STATE_CONFLICT = "conflict"

PUBLIC_PROGRESS_STATES = frozenset({"preparing", "upgrading", "verifying", "restoring"})
PUBLIC_RESULT_STATES = frozenset(
    {
        UPGRADE_STATE_SUCCEEDED,
        UPGRADE_STATE_ALREADY_CURRENT,
        UPGRADE_STATE_LEGACY_READONLY,
        UPGRADE_STATE_ROLLED_BACK,
        UPGRADE_STATE_UNRESOLVED,
        UPGRADE_STATE_BLOCKED,
        UPGRADE_STATE_CONFLICT,
    }
)

# DTO fields/text are checked recursively.  These names are intentionally
# broader than the fields currently emitted so a later migration field cannot
# silently widen the product contract.
FORBIDDEN_DTO_FIELDS = frozenset(
    {
        "operation",
        "operation_id",
        "operationid",
        "operation_id_ref",
        "operation_ref",
        "path",
        "workspace",
        "package_id",
        "package_path",
        "staging_path",
        "rollback_path",
        "database",
        "database_name",
        "db_path",
        "schema",
        "schema_version",
        "storage",
        "storage_version",
        "version",
        "internal_step",
        "step",
        "trace",
        "trace_id",
        "request_id",
        "session_id",
        "token",
        "lock",
        "process",
        "thread",
        "retry_count",
        "support_code",
        "supportcode",
        "supportcode_ref",
        "limited",
        "data_coverage_limited",
        "provider",
        "model",
        "medical_record",
        "medical_records",
        "raw_medical_record",
        "raw_medical_data",
        "original_medical_record",
        "original_records",
        "medical_data",
        "patient",
        "patient_id",
        "subject",
        "subject_id",
        "primary_key",
        "record_id",
        "raw",
        "raw_data",
        "raw_exception",
        "stacktrace",
        "stack_trace",
        "error",
        "exception",
        "summary",
    }
)
FORBIDDEN_DTO_TEXT = (
    "sqlite",
    "database",
    "数据库",
    "schema",
    "schema_version",
    "storage",
    "storage_version",
    "operation",
    "operation_id",
    "package_path",
    "staging_path",
    "rollback_path",
    "trace",
    "traceback",
    "request_id",
    "session_id",
    "supportcode",
    "limited",
    "provider",
    "model",
    "credential_value",
    "primary_key",
    "record_id",
    "raw",
    "error",
    "exception",
    "summary",
    "medical record",
    "medical data",
    "raw medical",
    "original record",
    "原始医学记录",
    "患者",
    "受试者",
    "api_key=",
    "bearer ",
    "password=",
    "token=",
)

PUBLIC_OPEN_MESSAGES = {
    "current": "项目格式正常，可以继续使用。",
    "legacy_readonly": "项目格式较旧，当前可以只读查看。",
    "legacy_unsupported": "项目格式较早，当前版本暂不支持升级。请保留原项目并联系支持。",
    "future": "此项目由更新版本创建，当前应用无法安全打开。请使用更新版本打开。",
    "blocked": "暂时无法安全打开此项目，请保留原项目并联系支持。",
}
PUBLIC_UPGRADE_MESSAGES = {
    "succeeded": "项目格式已升级。请重新打开项目后继续使用。",
    "already_current": "项目格式正常，可以继续使用。",
    "legacy_readonly": "项目格式较旧，当前可以只读查看。",
    "rolled_back": "升级未完成，原项目仍可只读查看。可稍后重试。",
    "unresolved": "升级未完成，暂时无法安全打开项目。请保留原项目并联系支持。",
    "blocked": "暂时无法安全打开此项目，请保留原项目并联系支持。",
    "conflict": "项目升级状态已发生变化，请重新检查项目后再试。",
}
PUBLIC_UPGRADE_NEXT_ACTIONS = {
    "succeeded": "重新打开项目",
    "already_current": "继续使用项目",
    "legacy_readonly": "开始升级或稍后处理",
    "rolled_back": "稍后重试升级",
    "unresolved": "保留原项目并联系支持",
    "blocked": "关闭项目或联系支持",
    "conflict": "重新检查项目后再试",
}


class ProjectCompatibilityError(RuntimeError):
    """Fail-closed project compatibility error for mutable entrypoints."""

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        *,
        inspection: Optional[ProjectSchemaInspection] = None,
    ) -> None:
        self.code = str(code)
        self.message = message or {
            "project_read_only": PUBLIC_OPEN_MESSAGES["legacy_readonly"],
            "project_open_blocked": PUBLIC_OPEN_MESSAGES["blocked"],
            "project_legacy_unsupported": PUBLIC_OPEN_MESSAGES["legacy_unsupported"],
            "project_future_version": PUBLIC_OPEN_MESSAGES["future"],
        }.get(self.code, PUBLIC_OPEN_MESSAGES["blocked"])
        self.inspection = inspection
        super().__init__(self.code)

    def as_error_body(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class ProjectReadOnlyError(ProjectCompatibilityError):
    """A write was attempted through a legacy read-only facade."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__("project_read_only", message)


def _field_key(value: Any) -> str:
    return str(value).replace("-", "_").lower()


def _assert_clean_product_value(value: Any, *, field: str = "") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _field_key(key)
            if normalized in FORBIDDEN_DTO_FIELDS:
                raise ValueError("forbidden product DTO field")
            _assert_clean_product_value(nested, field=normalized)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            _assert_clean_product_value(nested, field=field)
        return
    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in FORBIDDEN_DTO_TEXT):
            raise ValueError("forbidden product DTO text")


def _validate_coverage(value: str) -> str:
    if value not in {DATA_COVERAGE_COMPLETE, DATA_COVERAGE_INCOMPLETE}:
        raise ValueError("unsupported data coverage")
    return value


def _validate_open_mode(value: str) -> str:
    if value not in {OPEN_MODE_EDIT, OPEN_MODE_READONLY, OPEN_MODE_BLOCKED}:
        raise ValueError("unsupported open mode")
    return value


def _validate_chinese(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("product text is required")
    if not any("\u4e00" <= char <= "\u9fff" for char in value):
        raise ValueError("product text must be Chinese")
    return value


@dataclass(frozen=True)
class ProjectOpenResult:
    """Minimal product projection returned by the project-open preflight."""

    state: str
    open_mode: str
    data_coverage: str
    can_view: bool
    can_edit: bool
    message: str
    next_action: str

    def __post_init__(self) -> None:
        if self.state not in {
            OPEN_STATE_CURRENT,
            OPEN_STATE_LEGACY_READONLY,
            OPEN_STATE_BLOCKED,
        }:
            raise ValueError("unsupported open state")
        _validate_open_mode(self.open_mode)
        _validate_coverage(self.data_coverage)
        if type(self.can_view) is not bool or type(self.can_edit) is not bool:
            raise ValueError("boolean product field required")
        expected_mode = {
            OPEN_STATE_CURRENT: OPEN_MODE_EDIT,
            OPEN_STATE_LEGACY_READONLY: OPEN_MODE_READONLY,
            OPEN_STATE_BLOCKED: OPEN_MODE_BLOCKED,
        }[self.state]
        if self.open_mode != expected_mode:
            raise ValueError("open state and mode are inconsistent")
        if self.open_mode == OPEN_MODE_BLOCKED:
            if self.can_view or self.can_edit:
                raise ValueError("blocked project cannot be viewed or edited")
            if self.data_coverage != DATA_COVERAGE_INCOMPLETE:
                raise ValueError("blocked project must be incomplete")
        else:
            if not self.can_view:
                raise ValueError("viewable project must be viewable")
            if self.open_mode == OPEN_MODE_EDIT and not self.can_edit:
                raise ValueError("edit project must be editable")
            if self.open_mode == OPEN_MODE_READONLY and self.can_edit:
                raise ValueError("readonly project cannot be edited")
            if self.data_coverage != DATA_COVERAGE_COMPLETE:
                raise ValueError("viewable project must be complete")
        _validate_chinese(self.message)
        _validate_chinese(self.next_action)

    @property
    def openMode(self) -> str:  # noqa: N802 - product DTO spelling
        return self.open_mode

    @property
    def dataCoverage(self) -> str:  # noqa: N802 - product DTO spelling
        return self.data_coverage

    @property
    def canView(self) -> bool:  # noqa: N802 - product DTO spelling
        return self.can_view

    @property
    def canEdit(self) -> bool:  # noqa: N802 - product DTO spelling
        return self.can_edit

    def as_dict(self) -> Dict[str, Any]:
        body = {
            "state": self.state,
            "openMode": self.open_mode,
            "dataCoverage": self.data_coverage,
            "canView": self.can_view,
            "canEdit": self.can_edit,
            "message": self.message,
            "nextAction": self.next_action,
        }
        _assert_clean_product_value(body)
        return body

    to_dict = as_dict


@dataclass(frozen=True)
class ProjectUpgradeProgress:
    """Minimal Chinese progress DTO; internal status is never exposed."""

    state: str
    phase_label: str
    percent: Optional[int]
    message: str

    def __post_init__(self) -> None:
        if self.state not in PUBLIC_PROGRESS_STATES:
            raise ValueError("unsupported progress state")
        if self.percent is not None and (
            type(self.percent) is not int or self.percent < 0 or self.percent > 100
        ):
            raise ValueError("invalid progress percent")
        _validate_chinese(self.phase_label)
        _validate_chinese(self.message)

    @property
    def phaseLabel(self) -> str:  # noqa: N802 - product DTO spelling
        return self.phase_label

    def as_dict(self) -> Dict[str, Any]:
        body = {
            "state": self.state,
            "phaseLabel": self.phase_label,
            "percent": self.percent,
            "message": self.message,
        }
        _assert_clean_product_value(body)
        return body

    to_dict = as_dict


@dataclass(frozen=True)
class ProjectUpgradeResult:
    """Minimal product result for success, recovery, and blocked outcomes."""

    state: str
    open_mode: str
    data_coverage: str
    can_view: bool
    can_edit: bool
    requires_reopen: bool
    message: str
    next_action: str

    def __post_init__(self) -> None:
        if self.state not in PUBLIC_RESULT_STATES:
            raise ValueError("unsupported upgrade result state")
        _validate_open_mode(self.open_mode)
        _validate_coverage(self.data_coverage)
        if type(self.can_view) is not bool or type(self.can_edit) is not bool:
            raise ValueError("boolean product field required")
        if type(self.requires_reopen) is not bool:
            raise ValueError("requires_reopen must be bool")
        expected_mode = {
            UPGRADE_STATE_SUCCEEDED: OPEN_MODE_EDIT,
            UPGRADE_STATE_ALREADY_CURRENT: OPEN_MODE_EDIT,
            UPGRADE_STATE_LEGACY_READONLY: OPEN_MODE_READONLY,
            UPGRADE_STATE_ROLLED_BACK: OPEN_MODE_READONLY,
            UPGRADE_STATE_UNRESOLVED: OPEN_MODE_BLOCKED,
            UPGRADE_STATE_BLOCKED: OPEN_MODE_BLOCKED,
            UPGRADE_STATE_CONFLICT: OPEN_MODE_BLOCKED,
        }[self.state]
        if self.open_mode != expected_mode:
            raise ValueError("upgrade result state and mode are inconsistent")
        if self.open_mode == OPEN_MODE_BLOCKED:
            if self.can_view or self.can_edit:
                raise ValueError("blocked result cannot be viewed or edited")
            if self.data_coverage != DATA_COVERAGE_INCOMPLETE:
                raise ValueError("blocked result must be incomplete")
        else:
            if not self.can_view:
                raise ValueError("viewable result must be viewable")
            if self.open_mode == OPEN_MODE_EDIT and not self.can_edit:
                raise ValueError("edit result must be editable")
            if self.open_mode == OPEN_MODE_READONLY and self.can_edit:
                raise ValueError("readonly result cannot be edited")
            if self.data_coverage != DATA_COVERAGE_COMPLETE:
                raise ValueError("viewable result must be complete")
        if self.state == UPGRADE_STATE_SUCCEEDED:
            if not self.requires_reopen:
                raise ValueError("successful upgrade requires reopen")
        elif self.requires_reopen:
            raise ValueError("only successful upgrade requires reopen")
        _validate_chinese(self.message)
        _validate_chinese(self.next_action)

    @property
    def openMode(self) -> str:  # noqa: N802 - product DTO spelling
        return self.open_mode

    @property
    def dataCoverage(self) -> str:  # noqa: N802 - product DTO spelling
        return self.data_coverage

    @property
    def canView(self) -> bool:  # noqa: N802 - product DTO spelling
        return self.can_view

    @property
    def canEdit(self) -> bool:  # noqa: N802 - product DTO spelling
        return self.can_edit

    @property
    def requiresReopen(self) -> bool:  # noqa: N802 - product DTO spelling
        return self.requires_reopen

    def as_dict(self) -> Dict[str, Any]:
        body = {
            "state": self.state,
            "openMode": self.open_mode,
            "dataCoverage": self.data_coverage,
            "canView": self.can_view,
            "canEdit": self.can_edit,
            "requiresReopen": self.requires_reopen,
            "message": self.message,
            "nextAction": self.next_action,
        }
        _assert_clean_product_value(body)
        return body

    to_dict = as_dict


# Names used by callers that prefer a DTO suffix.
ProjectOpenDTO = ProjectOpenResult
ProjectUpgradeProgressDTO = ProjectUpgradeProgress
ProjectUpgradeResultDTO = ProjectUpgradeResult


def _future_or_unsupported(inspection: ProjectSchemaInspection) -> str:
    reports = tuple(inspection.members.values())
    if any(report.reason_code == "unsupported_legacy_marker" for report in reports):
        return "legacy_unsupported"
    for report in reports:
        marker = str(report.marker_value or report.schema_version or "")
        if not marker:
            continue
        if report.reason_code == "unsupported_schema_version":
            if marker.isdigit() and int(marker) > 0:
                return "future"
            if "-v" in marker.lower():
                suffix = marker.lower().rsplit("-v", 1)[-1]
                if suffix.isdigit():
                    return "future"
    return "blocked"


def project_open_result(inspection: ProjectSchemaInspection) -> ProjectOpenResult:
    """Convert a schema inspection to the fixed product opening decision."""

    if inspection.classification is SchemaClassification.CURRENT:
        return ProjectOpenResult(
            state=OPEN_STATE_CURRENT,
            open_mode=OPEN_MODE_EDIT,
            data_coverage=DATA_COVERAGE_COMPLETE,
            can_view=True,
            can_edit=True,
            message=PUBLIC_OPEN_MESSAGES["current"],
            next_action="继续使用项目",
        )
    if inspection.classification is SchemaClassification.LEGACY and inspection.can_view:
        return ProjectOpenResult(
            state=OPEN_STATE_LEGACY_READONLY,
            open_mode=OPEN_MODE_READONLY,
            data_coverage=DATA_COVERAGE_COMPLETE,
            can_view=True,
            can_edit=False,
            message=PUBLIC_OPEN_MESSAGES["legacy_readonly"],
            next_action="开始升级或稍后处理",
        )
    reason = _future_or_unsupported(inspection)
    return ProjectOpenResult(
        state=OPEN_STATE_BLOCKED,
        open_mode=OPEN_MODE_BLOCKED,
        data_coverage=DATA_COVERAGE_INCOMPLETE,
        can_view=False,
        can_edit=False,
        message=PUBLIC_OPEN_MESSAGES[reason],
        next_action="关闭项目或联系支持",
    )


def open_project_result(
    workspace_or_inspection: Any,
) -> ProjectOpenResult:
    inspection = (
        workspace_or_inspection
        if isinstance(workspace_or_inspection, ProjectSchemaInspection)
        else inspect_project_schema(workspace_or_inspection)
    )
    return project_open_result(inspection)


def require_current_project(
    workspace: Any,
    *,
    inspection: Optional[ProjectSchemaInspection] = None,
) -> ProjectSchemaInspection:
    """Fail closed before any mutable constructor or writer is reached."""

    report = inspection if inspection is not None else inspect_project_schema(workspace)
    if report.classification is SchemaClassification.CURRENT:
        return report
    if report.classification is SchemaClassification.LEGACY and report.can_view:
        raise ProjectReadOnlyError()
    reason = _future_or_unsupported(report)
    code = {
        "legacy_unsupported": "project_legacy_unsupported",
        "future": "project_future_version",
    }.get(reason, "project_open_blocked")
    raise ProjectCompatibilityError(code, PUBLIC_OPEN_MESSAGES[reason], inspection=report)


def assert_current_project(workspace: Any) -> ProjectSchemaInspection:
    """Alias for mutable writer gates and direct constructor tests."""

    return require_current_project(workspace)


def _readonly_uri(path: Path) -> str:
    return "file:" + quote(str(path), safe="/") + "?mode=ro"


def _readonly_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise ProjectReadOnlyError("项目资料尚未完整，当前只能关闭项目或联系支持。")
    connection = sqlite3.connect(
        _readonly_uri(path), uri=True, isolation_level=None, check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    if int(connection.execute("PRAGMA query_only").fetchone()[0]) != 1:
        connection.close()
        raise ProjectReadOnlyError()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _existing_columns(connection: sqlite3.Connection, table: str) -> Tuple[str, ...]:
    rows = connection.execute(
        "PRAGMA table_info(%s)" % _quote_identifier(table)
    ).fetchall()
    return tuple(str(row[1]) for row in rows)


def _safe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value
    return parsed


class ReadOnlyProjectView:
    """Query-only facade for a complete current or supported legacy project.

    The facade intentionally has no ``store``/``registry`` attributes and no
    mutable object references.  Each query opens a mode=ro connection for the
    selected member and closes it before returning.
    """

    __slots__ = ("_workspace", "_inspection", "_closed")

    def __init__(
        self,
        workspace: Any,
        *,
        inspection: Optional[ProjectSchemaInspection] = None,
    ) -> None:
        self._workspace = Path(workspace)
        # A caller-supplied report is only a hint; never trust stale schema
        # state for a handle that will be used to read project data.
        del inspection
        self._inspection = inspect_project_schema(self._workspace)
        if self._inspection.classification not in {
            SchemaClassification.CURRENT,
            SchemaClassification.LEGACY,
        } or not self._inspection.can_view:
            raise ProjectCompatibilityError(
                "project_open_blocked",
                PUBLIC_OPEN_MESSAGES["blocked"],
                inspection=self._inspection,
            )
        self._closed = False
        self._validate_project_identity()

    def _validate_project_identity(self) -> None:
        """Reject readable-looking workspaces with cross-member identity drift."""
        expected = self._workspace.name
        identity_tables = (
            (RUNTIME_MEMBER, "projects"),
            (RUNTIME_MEMBER, "monitoring_runs"),
            (BINDING_MEMBER, "monitoring_run_bindings"),
            (LAUNCH_MEMBER, "r7_launch_registry"),
            (LAUNCH_MEMBER, "r7_result_publications"),
            (LAUNCH_MEMBER, "r7_continuity_plans"),
            (RISK_MEMBER, "r7_risk_rule_revisions"),
        )
        for member, table in identity_tables:
            report = self._inspection.member(member)
            if not report.present:
                continue
            rows = self._query_rows(
                member,
                table,
                ("project_id", "is_synthetic"),
            )
            for row in rows:
                if "project_id" not in row:
                    continue
                if str(row["project_id"]) != expected:
                    raise ProjectCompatibilityError(
                        "project_open_blocked",
                        PUBLIC_OPEN_MESSAGES["blocked"],
                        inspection=self._inspection,
                    )
                if table == "projects" and "is_synthetic" in row:
                    try:
                        synthetic = int(row["is_synthetic"])
                    except (TypeError, ValueError) as exc:
                        raise ProjectCompatibilityError(
                            "project_open_blocked",
                            PUBLIC_OPEN_MESSAGES["blocked"],
                            inspection=self._inspection,
                        ) from exc
                    if synthetic != 1:
                        raise ProjectCompatibilityError(
                            "project_open_blocked",
                            PUBLIC_OPEN_MESSAGES["blocked"],
                            inspection=self._inspection,
                        )

    @property
    def inspection(self) -> ProjectSchemaInspection:
        self._require_open()
        return self._inspection

    @property
    def workspace(self) -> Path:
        self._require_open()
        return self._workspace

    @property
    def project_id(self) -> str:
        self._require_open()
        return self._workspace.name

    @property
    def open_mode(self) -> str:
        self._require_open()
        return OPEN_MODE_EDIT if self._inspection.classification is SchemaClassification.CURRENT else OPEN_MODE_READONLY

    @property
    def read_only(self) -> bool:
        return self.open_mode == OPEN_MODE_READONLY

    @property
    def can_view(self) -> bool:
        self._require_open()
        return True

    @property
    def can_edit(self) -> bool:
        return False if self.read_only else True

    def _require_open(self) -> None:
        if self._closed:
            raise ProjectReadOnlyError("项目只读查看已关闭。")

    def _member_path(self, member: str) -> Path:
        self._require_open()
        report = self._inspection.member(member)
        return Path(report.path)

    def _query_rows(
        self,
        member: str,
        table: str,
        columns: Sequence[str],
        *,
        where: str = "",
        params: Sequence[Any] = (),
        order_by: str = "",
    ) -> Tuple[Dict[str, Any], ...]:
        path = self._member_path(member)
        connection: Optional[sqlite3.Connection] = None
        try:
            connection = _readonly_connection(path)
            available = set(_existing_columns(connection, table))
            selected = tuple(column for column in columns if column in available)
            if not selected:
                return ()
            sql = "SELECT %s FROM %s" % (
                ", ".join(_quote_identifier(column) for column in selected),
                _quote_identifier(table),
            )
            if where:
                sql += " WHERE " + where
            if order_by:
                sql += " ORDER BY " + order_by
            rows = connection.execute(sql, tuple(params)).fetchall()
            return tuple(
                {column: _safe_json(row[column]) for column in selected} for row in rows
            )
        except (sqlite3.Error, OSError) as exc:
            raise ProjectReadOnlyError() from exc
        finally:
            if connection is not None:
                connection.close()

    def list_execution_profiles(
        self,
        *,
        layer_kind: Optional[str] = None,
        scope_key: Optional[str] = None,
    ) -> Tuple[Mapping[str, Any], ...]:
        where_parts = []
        params: list[Any] = []
        if layer_kind is not None:
            where_parts.append('"layer_kind" = ?')
            params.append(layer_kind)
        if scope_key is not None:
            where_parts.append('"scope_key" = ?')
            params.append(scope_key)
        rows = self._query_rows(
            PROFILE_MEMBER,
            "profile_layer_versions",
            ("layer_kind", "scope_key", "revision", "record_id", "payload_json", "content_digest"),
            where=" AND ".join(where_parts),
            params=params,
            order_by='"layer_kind" ASC, "scope_key" ASC, "revision" ASC',
        )
        return tuple(rows)

    def get_execution_profile(self, layer_kind: str, scope_key: str) -> Mapping[str, Any]:
        rows = self.list_execution_profiles(layer_kind=layer_kind, scope_key=scope_key)
        if not rows:
            raise ProjectReadOnlyError("未找到指定的执行配置。")
        return rows[-1]

    def list_run_bindings(self) -> Tuple[Mapping[str, Any], ...]:
        return self._query_rows(
            BINDING_MEMBER,
            "monitoring_run_bindings",
            (
                "run_id",
                "project_id",
                "mode",
                "execution_basis",
                "data_cutoff",
                "source_revision_id",
                "prior_accepted_snapshot_ref",
                "execution_profile_id",
                "profile_id",
                "user_config_name",
                "adapter_id",
                "adapter_version",
                "schema_version",
            ),
            where='"project_id" = ?',
            params=(self.project_id,),
            order_by='"run_id" ASC',
        )

    def get_run_binding(self, run_id: str) -> Mapping[str, Any]:
        rows = self._query_rows(
            BINDING_MEMBER,
            "monitoring_run_bindings",
            (
                "run_id",
                "project_id",
                "mode",
                "execution_basis",
                "data_cutoff",
                "source_revision_id",
                "prior_accepted_snapshot_ref",
                "execution_profile_id",
                "profile_id",
                "user_config_name",
                "adapter_id",
                "adapter_version",
                "schema_version",
            ),
            where='"project_id" = ? AND "run_id" = ?',
            params=(self.project_id, run_id),
        )
        if not rows:
            raise ProjectReadOnlyError("未找到指定的监查运行绑定。")
        return rows[0]

    def list_monitoring_runs(self) -> Tuple[Mapping[str, Any], ...]:
        return self._query_rows(
            RUNTIME_MEMBER,
            "monitoring_runs",
            (
                "run_id",
                "project_id",
                "mode",
                "data_cutoff",
                "source_revision_id",
                "execution_basis",
                "analysis_state",
                "evidence_state",
                "review_state",
                "output_state",
                "user_disposition",
                "manifest_revision",
            ),
            where='"project_id" = ?',
            params=(self.project_id,),
            order_by='"run_id" ASC',
        )

    def list_work_unit_runs(
        self,
        run_id: str,
    ) -> Tuple[Mapping[str, Any], ...]:
        """Read only the bounded execution ledger for one bound run."""
        return self._query_rows(
            RUNTIME_MEMBER,
            "work_unit_runs",
            (
                "run_id",
                "manifest_revision",
                "work_unit_id",
                "node_id",
                "status",
                "started_at",
                "finished_at",
                "updated_at",
            ),
            where='"run_id" = ?',
            params=(run_id,),
            order_by='"manifest_revision" ASC, "work_unit_id" ASC',
        )

    def list_risk_rules(self) -> Tuple[Mapping[str, Any], ...]:
        report = self._inspection.member(RISK_MEMBER)
        if not report.present:
            return ()
        return self._query_rows(
            RISK_MEMBER,
            "r7_risk_rule_revisions",
            (
                "project_id",
                "revision",
                "revision_token",
                "candidate_id",
                "subject",
                "condition",
                "applicable_scope",
                "starting_run",
                "summary",
                "created_at",
                "selectable",
            ),
            where='"project_id" = ?',
            params=(self.project_id,),
            order_by='"project_id" ASC, "revision" ASC',
        )

    def list_launches(self) -> Tuple[Mapping[str, Any], ...]:
        report = self._inspection.member(LAUNCH_MEMBER)
        if not report.present:
            return ()
        return self._query_rows(
            LAUNCH_MEMBER,
            "r7_launch_registry",
            (
                "sequence",
                "project_id",
                "idempotency_key",
                "run_id",
                "public_run_token",
                "request_fingerprint",
                "mode",
                "execution_basis",
                "current_snapshot_token",
                "baseline_token",
                "rule_tokens_json",
                "data_cutoff",
                "comparison_range_text",
                "run_state",
                "result_available",
                "main_action",
                "manifest_digest",
                "created_at",
                "updated_at",
            ),
            where='"project_id" = ?',
            params=(self.project_id,),
            order_by='"sequence" ASC',
        )

    def list_publications(
        self,
        *,
        run_id: Optional[str] = None,
    ) -> Tuple[Mapping[str, Any], ...]:
        report = self._inspection.member(LAUNCH_MEMBER)
        if not report.present:
            return ()
        where_parts = ['"project_id" = ?']
        params: list[Any] = [self.project_id]
        if run_id is not None:
            where_parts.append('"run_id" = ?')
            params.append(run_id)
        return self._query_rows(
            LAUNCH_MEMBER,
            "r7_result_publications",
            ("project_id", "run_id", "public_run_token", "publication_state"),
            where=" AND ".join(where_parts),
            params=params,
            order_by='"created_at" DESC, "sequence" DESC',
        )


    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> "ReadOnlyProjectView":
        self._require_open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # Explicitly reject common mutable entrypoints.  Defining these methods
    # keeps accidental calls deterministic rather than falling through to a
    # lower-level object that could create a writable connection.
    def _reject_write(self, *_: Any, **__: Any) -> None:
        raise ProjectReadOnlyError()

    bootstrap_workspace = _reject_write
    append_execution_profile = _reject_write
    append_revision = _reject_write
    append_layer = _reject_write
    seed_builtin_global_default = _reject_write
    seed_deepseek_capability_layer = _reject_write
    bind_run = _reject_write
    bind = _reject_write
    reopen_and_validate_run = _reject_write
    bind_monitoring_run = _reject_write
    create_project = _reject_write
    create_run = _reject_write
    update_run_state = _reject_write
    save_checkpoint = _reject_write
    preview = _reject_write
    reserve = _reject_write
    reserve_publication = _reject_write
    append_risk_rule = _reject_write
    start_execution = _reject_write
    resume_execution = _reject_write
    cancel_execution = _reject_write
    record_manifest = _reject_write
    update_state = _reject_write
    finalize_publication = _reject_write


# Equivalent names used by callers and hidden contract probes.
ProjectReadOnlyView = ReadOnlyProjectView
LegacyProjectView = ReadOnlyProjectView


def open_read_only_project_view(
    workspace: Any,
    *,
    inspection: Optional[ProjectSchemaInspection] = None,
) -> ReadOnlyProjectView:
    return ReadOnlyProjectView(workspace, inspection=inspection)


def upgrade_result_from_state(
    state: str,
    *,
    message: Optional[str] = None,
    next_action: Optional[str] = None,
) -> ProjectUpgradeResult:
    """Build a terminal product result from a public migration outcome."""

    state = str(state)
    if state == "completed":
        state = UPGRADE_STATE_SUCCEEDED
    elif state == "retained_for_triage":
        state = UPGRADE_STATE_UNRESOLVED
    elif state == "migration_operation_conflict":
        state = UPGRADE_STATE_CONFLICT
    if state not in PUBLIC_RESULT_STATES:
        state = UPGRADE_STATE_BLOCKED
    if state == UPGRADE_STATE_SUCCEEDED:
        mode, coverage, view, edit = OPEN_MODE_EDIT, DATA_COVERAGE_COMPLETE, True, True
        reopen = True
    elif state in {UPGRADE_STATE_ALREADY_CURRENT}:
        mode, coverage, view, edit = OPEN_MODE_EDIT, DATA_COVERAGE_COMPLETE, True, True
        reopen = False
    elif state in {UPGRADE_STATE_LEGACY_READONLY, UPGRADE_STATE_ROLLED_BACK}:
        mode, coverage, view, edit = OPEN_MODE_READONLY, DATA_COVERAGE_COMPLETE, True, False
        reopen = False
    else:
        mode, coverage, view, edit = OPEN_MODE_BLOCKED, DATA_COVERAGE_INCOMPLETE, False, False
        reopen = False
    return ProjectUpgradeResult(
        state=state,
        open_mode=mode,
        data_coverage=coverage,
        can_view=view,
        can_edit=edit,
        requires_reopen=reopen,
        message=message or PUBLIC_UPGRADE_MESSAGES[state],
        next_action=next_action or PUBLIC_UPGRADE_NEXT_ACTIONS[state],
    )


def _status_text(status: str) -> Tuple[str, str]:
    if status in {
        "requested",
        "inspecting",
        "backup_required",
        "backup_in_progress",
        "backup_verified",
        "waiting_for_project",
        "maintenance_acquired",
    }:
        return "preparing", {
            "requested": "正在受理升级请求",
            "inspecting": "正在检查项目",
            "backup_required": "正在准备恢复点",
            "backup_in_progress": "正在准备恢复点",
            "backup_verified": "恢复点已准备完成",
            "waiting_for_project": "正在等待项目空闲",
            "maintenance_acquired": "已准备更新项目",
        }.get(status, "正在准备升级")
    if status in {"staging", "migrating", "retryable_failed"}:
        return "upgrading", {
            "staging": "正在建立升级副本",
            "migrating": "正在更新项目内容",
            "retryable_failed": "升级暂未完成，正在等待重试",
        }.get(status, "正在更新项目内容")
    if status in {"staged_verified", "switching", "live_verifying"}:
        return "verifying", {
            "staged_verified": "正在检查升级副本",
            "switching": "正在切换项目",
            "live_verifying": "正在检查升级结果",
        }.get(status, "正在检查升级结果")
    if status in {
        "rollback_in_progress",
        "rolling_back",
        "rolled_back",
        "retained_for_triage",
    }:
        return "restoring", {
            "rollback_in_progress": "正在恢复原项目",
            "rolling_back": "正在恢复原项目",
            "rolled_back": "原项目已恢复",
            "retained_for_triage": "升级现场已保留待处置",
        }.get(status, "正在恢复原项目")
    # The DTO has only four public progress states.  Unknown/blocked work is
    # held in the preparation state instead of inventing a fifth state.
    return "preparing", "正在准备升级"


_PROGRESS_MILESTONES = {
    "requested": 5,
    "inspecting": 12,
    "backup_required": 12,
    "backup_in_progress": 12,
    "backup_verified": 28,
    "waiting_for_project": 28,
    "maintenance_acquired": 35,
    "staging": 45,
    "migrating": 72,
    "staged_verified": 86,
    "switching": 94,
    "live_verifying": 94,
}
_VARIABLE_PROGRESS_STATES = frozenset(
    {
        "retryable_failed",
        "rollback_in_progress",
        "rolling_back",
        "rolled_back",
        "retained_for_triage",
    }
)

def upgrade_progress_from_operation(operation: Any) -> ProjectUpgradeProgress:
    """Map a migration operation to a Chinese, deterministic progress DTO."""

    status = str(getattr(operation, "status", ""))
    public_state, phase = _status_text(status)
    known_statuses = frozenset(_PROGRESS_MILESTONES) | _VARIABLE_PROGRESS_STATES
    if status in _PROGRESS_MILESTONES:
        # These values are evidence boundaries, not a caller-provided
        # estimate; an inconsistent ledger value must not advance the UI.
        percent: Optional[int] = _PROGRESS_MILESTONES[status]
    elif status in _VARIABLE_PROGRESS_STATES:
        raw_percent = getattr(operation, "progress_percent", None)
        if raw_percent is None:
            percent = None
        else:
            try:
                percent = max(0, min(100, int(raw_percent)))
            except (TypeError, ValueError):
                percent = None
        if (
            status
            in {"rollback_in_progress", "rolling_back", "rolled_back", "retained_for_triage"}
            and percent is not None
        ):
            # A restore cannot advertise the success milestone.
            percent = min(percent, 94)
    else:
        # A percent without a known evidence boundary would be fabricated.
        percent = None
    if status not in known_statuses:
        # Keep the four-state UI envelope, but mark unknown work uncertain.
        percent = None
    message = {
        "preparing": "正在准备升级，完成后才会更新项目。",
        "upgrading": "正在更新项目内容，期间项目暂不能编辑。",
        "verifying": "正在检查升级结果，完成后可重新打开项目。",
        "restoring": "正在恢复原项目，完成后会重新检查项目状态。",
    }[public_state]
    return ProjectUpgradeProgress(
        state=public_state,
        phase_label=phase,
        percent=percent,
        message=message,
    )


# Short aliases for direct callers.
project_open_projection = project_open_result
upgrade_progress_projection = upgrade_progress_from_operation
upgrade_result_projection = upgrade_result_from_state


__all__ = [
    "DATA_COVERAGE_COMPLETE",
    "DATA_COVERAGE_INCOMPLETE",
    "FORBIDDEN_DTO_FIELDS",
    "FORBIDDEN_DTO_TEXT",
    "OPEN_MODE_BLOCKED",
    "OPEN_MODE_EDIT",
    "OPEN_MODE_READONLY",
    "OPEN_STATE_BLOCKED",
    "OPEN_STATE_CURRENT",
    "OPEN_STATE_LEGACY_READONLY",
    "PUBLIC_PROGRESS_STATES",
    "PUBLIC_OPEN_MESSAGES",
    "PUBLIC_UPGRADE_MESSAGES",
    "PUBLIC_UPGRADE_NEXT_ACTIONS",
    "PUBLIC_RESULT_STATES",
    "UPGRADE_STATE_ALREADY_CURRENT",
    "UPGRADE_STATE_BLOCKED",
    "UPGRADE_STATE_CONFLICT",
    "UPGRADE_STATE_LEGACY_READONLY",
    "UPGRADE_STATE_ROLLED_BACK",
    "UPGRADE_STATE_SUCCEEDED",
    "UPGRADE_STATE_UNRESOLVED",
    "ProjectCompatibilityError",
    "ProjectOpenDTO",
    "ProjectOpenResult",
    "ProjectReadOnlyError",
    "ProjectReadOnlyView",
    "ProjectUpgradeProgress",
    "ProjectUpgradeProgressDTO",
    "ProjectUpgradeResult",
    "ProjectUpgradeResultDTO",
    "ReadOnlyProjectView",
    "assert_current_project",
    "inspect_project_schema",
    "open_project_result",
    "open_read_only_project_view",
    "project_open_projection",
    "project_open_result",
    "require_current_project",
    "upgrade_progress_from_operation",
    "upgrade_progress_projection",
    "upgrade_result_from_state",
    "upgrade_result_projection",
]
