"""Project-scoped R7 product mount adapter (Slice-07C-1/2/4).

Thin FastAPI adapters over the frozen ``mm_r7`` run-entry, run-setup and
launch-registry contracts. Import and router construction perform no R7
directory / SQLite / schema / seed writes. Existing runtime routes resolve the
project and authorize first, then open a per-project ``MonitoringRunEntry``
and close it in ``finally``. Setup and product-launch routes use deterministic
synthetic inputs and lazily open project-scoped registries after the same
workspace check.

Product errors are local top-level ``{code, message}`` Chinese envelopes.
This module never registers app-wide exception handlers and never mounts the
isolated ``/api/medical-monitoring/r7`` prefix.
"""

from __future__ import annotations

from datetime import date
import hashlib
import inspect
import json
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import ValidationError
from fastapi.responses import JSONResponse

from packages.medical_monitoring.runtime import profile_store as ps
from packages.medical_monitoring.api.run_entry import (
    ProfileFieldsRequest,
    chinese_message_for,
)
from packages.medical_monitoring.runtime.run_entry import (
    PROFILE_DB_NAME,
    RUN_BINDING_DB_NAME,
    MonitoringRunEntry,
    RunEntryError,
)
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
    RuntimeProgressError,
    validate_public_data_cutoff,
)

from packages.medical_monitoring.runtime.background_recovery import (
    list_bound_capability_attempts,
)
from packages.medical_monitoring.runtime.capability import (
    CapabilityRequest,
    InvocationVersions,
)
from packages.medical_monitoring.domain.execution import (
    NodeStatus,
    NodeType,
    content_hash,
    to_jsonable,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime import run_setup as rs
from packages.medical_monitoring.runtime import project_backup as pb
from packages.medical_monitoring.runtime.maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from packages.medical_monitoring.runtime import launch_registry as lr
from packages.medical_monitoring.runtime.migration import (
    MigrationError,
    MigrationOperationLedger,
    MigrationRunner,
    TERMINAL_STATES,
)
from packages.medical_monitoring.runtime.project_lifecycle import (
    DATA_COVERAGE_COMPLETE,
    DATA_COVERAGE_INCOMPLETE,
    OPEN_MODE_BLOCKED,
    OPEN_MODE_EDIT,
    OPEN_MODE_READONLY,
    ProjectCompatibilityError,
    ProjectOpenDTO,
    ReadOnlyProjectView,
    inspect_project_schema,
    open_project_result,
    open_read_only_project_view,
    require_current_project,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from packages.medical_monitoring.runtime.schema_manifest import (
    SchemaClassification,
    inspect_member,
)
from packages.medical_monitoring.runtime.project_verifier import (
    ProjectVerificationDTO,
    ProjectVerificationError,
    RecoveryCoordinationError,
    RecoveryCoordinator,
    ProjectVerifier,
    RESULT_RECORD_COMPLETE,
    RESULT_RECOVERY_REQUIRED,
)
from packages.medical_monitoring.projections.product_adapter import (
    R5ProductAdapter,
    R5ProductAdapterError,
)
from .monitoring_identity_authorization import (
    MonitoringAction,
    authorize_monitoring_action,
)
from .monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
    MonitoringRuntimePrincipalDenied,
)
from .monitoring_runtime_route_context import (
    MonitoringRuntimeRouteContextError,
    build_monitoring_runtime_route_context,
)


R7_PRODUCT_PREFIX = "/api/projects/{project_id}/modules/medical-monitoring/r7"
R7_PRODUCT_SCHEMA = "mm-r7-product-mount-v1"
R7_WORKSPACE_ROOT_NAME = "medical_monitoring_r7"
R7_RISK_RULE_DB_NAME = "risk_rules.sqlite3"
#
# These are the only product write workflows intentionally reachable while a
# supported legacy project is read-only. Every ordinary project mutation calls
# ``mutable_project_error`` and remains blocked until an upgrade/reopen.
LEGACY_WORKFLOW_WRITE_ROUTES = frozenset(
    {
        "/project/upgrade",
        "/backups",
        "/restores/preflight",
        "/restores",
    }
)
_NOT_FOUND = {
    "profile_layer_not_found",
    "run_binding_not_found",
    "risk_rule_not_found",
    "risk_rule_preview_not_found",
    "public_run_not_found",
    "publication_not_found",
    "result_context_not_found",
    "migration_operation_not_found",
}
_CONFLICT = {
    "conflicting_replay",
    "conflicting_replay_effective_profile",
    "conflicting_replay_data_identity",
    "risk_rule_conflict",
    "idempotency_conflict",
    "publication_cas_conflict",
    "publication_blocked",
    "publication_not_available",
    "authority_identity_mismatch",
    "manifest_identity_mismatch",
    "receipt_gate_blocked",
    "in_flight_conflict",
    "result_context_unavailable",
    "result_center_out_of_scope",
    "continuity_unavailable",
    "migration_operation_conflict",
    "project_read_only",
    "project_legacy_unsupported",
    "project_future_version",
    "project_open_blocked",
}
_BACKUP_NOT_FOUND = {"operation_not_found", "workspace_not_found"}
_BACKUP_CONFLICT = {
    "backup_operation_conflict",
    "project_busy_retry_later",
    "package_identity_mismatch",
    "manifest_semantic_mismatch",
    "restore_confirmation_required",
    "restore_source_changed",
    "rollback_requires_review",
}
_BACKUP_INTERNAL = {
    "sqlite_integrity_failed",
    "backup_package_publish_failed",
    "restore_verification_failed",
    "restore_switch_failed",
    "restore_rollback_failed",
    "injected_failure",
}
_EXECUTION_STATE_CONFLICT = {
    "already_finished",
    "already_running",
    "not_interrupted",
    "nothing_to_resume",
    "not_running",
    "prepare_while_running",
}
_SECRET_FIELDS = {
    "credential",
    "credential_value",
    "credential_secret",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "authorization",
    "bearer",
    "access_token",
    "secret_key",
}
_FORBIDDEN_PUBLIC = _SECRET_FIELDS | {
    "modeoutput",
    "risk_instance",
    "patientjourney",
    "query_draft",
    "timeline",
    "canonical_fact",
    "report_claim",
}
_SECRET_VALUE = re.compile(r"(?i)(sk-[a-z0-9]{8,}|bearer\s+\S+|api_key=|password=|token=)")
_RUNTIME_INTERNAL_TOKENS = (
    "owner",
    "lease",
    "generation",
    "thread",
    "pid",
    "token",
    "sqlite",
    "provider",
    "model",
    "manifest_revision",
    "run_id",
    "project_id",
)

_PRODUCT_BACKUP_WORKERS: dict[tuple[str, str, str, str], threading.Thread] = {}
_PRODUCT_BACKUP_WORKERS_LOCK = threading.RLock()
_PRODUCT_BACKUP_TERMINAL = frozenset({pb.STATUS_AVAILABLE, pb.STATUS_FAILED})
_PRODUCT_RESTORE_TERMINAL = frozenset(
    {
        pb.STATUS_COMPLETED,
        pb.STATUS_ALREADY_CURRENT,
        pb.STATUS_RETAINED_FOR_TRIAGE,
    }
)

_LAYER_KINDS = frozenset(ps.LAYER_KINDS)

class _BlockedLegacyView:
    """Non-readable sentinel used when legacy semantic checks fail."""

    def close(self) -> None:
        return None

    def __getattr__(self, _name: str) -> Any:
        raise ProjectCompatibilityError("project_open_blocked")



_AUTH_MESSAGES = {
    "principal_required": "服务器未提供有效验证身份，医学监查 R7 操作已阻断。",
    "principal_unavailable": "服务器验证身份尚未接入或读取失败，医学监查 R7 操作已阻断。",
    "principal_denied": "服务器验证身份不满足医学监查 R7 操作条件。",
    "authorization_invalid": "医学监查 R7 授权请求无效，操作已阻断。",
    "not_permitted": "当前身份无权执行该医学监查 R7 操作。",
    "project_not_found": "未找到当前医学监查项目，或该项目未配置医学监查模块。",
    "workspace_not_ready": "请先完成工作区初始化。",
    "route_not_found": "未找到对应的医学监查功能，请检查访问路径。",
}
_RUNTIME_MESSAGES = {
    "already_finished": "本次监查已结束，无需再次开始。",
    "execution_not_prepared": "请先准备本次监查工作范围。",
    "already_running": "本次监查正在执行。",
    "not_interrupted": "本次监查当前不可继续。",
    "nothing_to_resume": "本次监查没有可继续的工作。",
    "not_running": "本次监查当前未在执行。",
    "prepare_while_running": "本次监查正在执行，不能变更工作范围。",
    "worker_start_failed": "本次监查后台执行未能启动。",
    "invalid_work_units": "本次监查工作范围无效，请检查工作项定义。",
    "runtime_identity_mismatch": "已准备的监查运行身份与当前绑定不一致，已阻断。",
    "runtime_integrity_failed": "本次监查进度无法核对，已阻断。",
    "superseded_scope_replay_forbidden": "已存在当前监查范围，不允许重新采用历史范围。",
    "frozen_scope_revision_forbidden": "核查前监查范围已冻结，不允许变更。",
    "unsupported_mode": "不支持的监查运行模式。",
    "unsupported_execution_basis": "不支持的运行基准。",
    "unsafe_data_cutoff": "数据截止点不符合展示约定。",
}

_PUBLICATION_MESSAGES = {
    "publication_not_available": "结果尚未整理完成",
    "publication_publishing": "结果正在整理，请稍候。",
    "publication_available": "结果已整理完成。",
    "publication_recoverable_failed": "结果整理暂时失败，可重试。",
    "publication_blocked": "结果尚未整理完成",
    "authority_provider_unavailable": "结果权威暂不可用，结果整理未完成。",
    "authority_provider_invalid": "结果权威接口无效，结果整理未完成。",
    "authority_identity_mismatch": "本次结果权威身份不一致，结果入口已关闭。",
    "manifest_identity_mismatch": "本次监查范围身份不一致，结果整理已阻断。",
    "receipt_gate_blocked": "本次结果材料未完整通过核对，结果整理已阻断。",
    "deterministic_gate_blocked": "本次监查的确定性工作项未完整完成，结果整理已阻断。",
    "runtime_read_failed": "本次监查运行记录暂时无法读取，结果整理可重试。",
    "result_context_not_found": "本次结果暂不可查看，请返回进度页",
    "result_context_unavailable": "本次结果暂不可查看，请返回进度页",
    "result_center_out_of_scope": "该中心不在本次监查范围",
    "continuity_unavailable": "连续性比较结果暂不可查看，请返回结果页",
}


from packages.medical_monitoring.api.r7_product.contracts import (
    ProductPublicationError,
    _StrictModel,
    ProductBackupRequest,
    ProductRestorePreflightRequest,
    ProductRestoreRequest,
    ProductProjectUpgradeRequest,
    ProjectOpenResult,
    ProjectUpgradeProgress,
    ProjectUpgradeResult,
    ProductBootstrapRequest,
    ProductCreateRunRequest,
    ProductPrepareExecutionRequest,
    ProductExecutionActionRequest,
    ProductRiskRulePreviewRequest,
    ProductRiskRuleRequest,
    ProductPrepareAndStartRequest,
    ProductPublicationRequest,
)


_CONTINUITY_RISK_CHANGE_KINDS_ZH = {
    "new": "新增",
    "upgraded": "升级",
    "continued": "持续",
    "downgraded": "降级",
    "closed": "关闭",
    "reopened": "重开",
    "needs_rejudgment": "需重新判断",
}
_CONTINUITY_DISPOSITIONS_ZH = {
    "reuse_unchanged": "沿用不变",
    "re_evaluate_changed_data": "数据变化，已重新分析",
    "re_evaluate_rule_change": "规则变化，已重新分析",
    "re_evaluate_prior_uncertain": "上轮依据不足，本轮重新分析",
    "close_with_evidence": "已有证据支持关闭",
    "blocked_incompatible": "前后版本不可直接比较",
}
_CONTINUITY_DATA_CHANGE_KINDS_ZH = {
    "unchanged": "无变化",
    "added": "新增数据",
    "revised": "数据修订",
    "deleted": "数据删除",
    "cannot_compare": "无法直接比较",
    "missing": "本轮未见对应记录",
}
_CONTINUITY_ATTENTION_TEXTS = frozenset(
    {
        "",
        "未见记录不代表风险已解除",
        "身份或数据不完整，需重新判断",
        "等级变化待确认",
        "原始记录位置待确认",
    }
)
_CONTINUITY_SEVERITIES = frozenset({"", "高", "中", "低"})
_CONTINUITY_OBJECT_TYPES_ZH = {
    "risk": "风险",
    "query_draft": "Query 草稿",
    "monitoring_output": "监查结果项",
}
_SEVERITY_TEXT_MAP = {
    "high": "高",
    "medium": "中",
    "low": "低",
}
_SEVERITY_RANK = {"高": 3, "中": 2, "低": 1}


class ProductContinuityChangeCounts(_StrictModel):
    new: int
    upgraded: int
    continued: int
    downgraded: int
    closed: int
    reopened: int
    needs_rejudgment: int
    mid_high_total: int
    changed_subject_count: int


class ProductContinuityRow(_StrictModel):
    row_ref: str
    object_type: str
    object_type_text: str
    ordinal: int
    change_kind: str
    change_text: str
    disposition: str
    disposition_text: str
    data_change_kind: str
    data_change_text: str
    severity_before_text: str
    severity_after_text: str
    title: str
    reason_text: str
    attention_text: str
    site_ref: str
    site_label: str
    subject_ref: str
    subject_label: str
    date_label: str
    window_start: str
    window_end: str
    risk_ref: str
    risk_instance_ref: str
    risk_anchor_ref: str
    event_ref: str
    source_locator_ref: str
    source_count: int


class ProductContinuityComparison(_StrictModel):
    available: bool
    basis_text: str
    comparison_text: str
    source_run_text: str
    change_counts: ProductContinuityChangeCounts
    rows: list[ProductContinuityRow]
    shown_count: int
    total_count: int
    truncated: bool


class ProductContinuityIdentity(_StrictModel):
    project_ref: str
    public_run_token: str
    snapshot_token: str
    data_cutoff_text: str
    mode_text: str
    site_scope_text: str
    site_ref: Optional[str] = None


class ProductContinuityResponse(_StrictModel):
    result_context_token: str
    identity: ProductContinuityIdentity
    comparison: ProductContinuityComparison
    response_digest: str


def _normalize_severity_zh(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    try:
        return _SEVERITY_TEXT_MAP[text]
    except KeyError as exc:
        raise ProductPublicationError("continuity_unavailable") from exc


def _public_continuity_text(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.casefold()
    if _SECRET_VALUE.search(text) or any(
        marker in lowered
        for marker in (
            "run_id",
            "run_ref",
            "snapshot_ref",
            "cutoff_ref",
            "packet_digest",
            "authority_hash",
            "artifact_member",
            "source_snapshot_sha256",
            "file://",
            "/users/",
            "traceback",
            "stdout",
            "stderr",
        )
    ):
        raise ProductPublicationError("continuity_unavailable")
    return text


def _validate_continuity_risk_semantics(item: Any, change_kind: str) -> None:
    from packages.medical_monitoring.runtime.continuity import (
        RiskProjectionError,
        project_risk_change_kind,
    )

    try:
        projected = project_risk_change_kind(
            from_state=getattr(item, "prior_risk_state", None),
            to_state=getattr(item, "current_risk_state", None),
            transition_type=(getattr(item, "r2_transition_type", "") or None),
            from_severity=getattr(item, "prior_severity", None),
            to_severity=getattr(item, "current_severity", None),
            identity_ambiguous=bool(getattr(item, "identity_ambiguous", False))
            or not getattr(item, "identity_compatible", True),
            lineage_changed=bool(getattr(item, "lineage_changed", False))
            or not getattr(item, "source_compatible", True),
            data_missing=bool(getattr(item, "data_missing", False))
            or not getattr(item, "output_contract_compatible", True)
            or not getattr(item, "current_present", True)
            or getattr(item, "data_change_kind", "")
            in {"missing", "cannot_compare"},
        )
    except (RiskProjectionError, TypeError, ValueError) as exc:
        raise ProductPublicationError("continuity_unavailable") from exc
    if projected.value != change_kind:
        raise ProductPublicationError("continuity_unavailable")
    if change_kind == "closed" and not (
        item.disposition == "close_with_evidence"
        and bool(item.closure_evidence_refs)
        and item.closure_allowed
        and item.current_listing_complete
        and item.baseline_eligible
    ):
        raise ProductPublicationError("continuity_unavailable")


def _continuity_row_sort_key(row: Mapping[str, Any]) -> tuple[int, int, str]:
    obj_type = str(row.get("object_type", ""))
    change_kind = str(row.get("change_kind", ""))
    sev_after = str(row.get("severity_after_text", ""))
    sev_before = str(row.get("severity_before_text", ""))
    ordinal = int(row.get("ordinal", 0))
    row_ref = str(row.get("row_ref", ""))

    priority_kinds = {"upgraded", "new", "reopened", "needs_rejudgment"}
    if obj_type == "risk":
        if sev_after == "高" and change_kind in priority_kinds:
            group = 0
        elif sev_after == "中" and change_kind in priority_kinds:
            group = 1
        elif (sev_after in {"高", "中"}) or (
            change_kind == "closed" and sev_before in {"高", "中"}
        ):
            group = 2
        else:
            group = 3
    elif obj_type == "query_draft":
        group = 4
    elif obj_type == "monitoring_output":
        group = 5
    else:
        group = 6
    return (group, ordinal, row_ref)

def _status_for(code: str) -> int:
    if code in _NOT_FOUND or code in _BACKUP_NOT_FOUND:
        return 404
    if code in _CONFLICT or code in _BACKUP_CONFLICT:
        return 409
    if code in {
        "superseded_scope_replay_forbidden",
        "frozen_scope_revision_forbidden",
    } | _EXECUTION_STATE_CONFLICT:
        return 409
    if code in {
        "internal_error",
        "worker_start_failed",
        "store_closed",
        "publication_recoverable_failed",
        "runtime_read_failed",
    } | _BACKUP_INTERNAL:
        return 500
    if code in {
        "principal_denied",
        "authorization_invalid",
        "not_permitted",
    }:
        return 403
    if code in {
        "principal_required",
        "principal_unavailable",
    }:
        return 401
    if code in {
        "authority_provider_unavailable",
        "authority_provider_invalid",
    }:
        return 503
    if code == "project_not_found":
        return 404
    return 422


def _error_response(
    status_code: int,
    code: str,
    message: Optional[str] = None,
) -> JSONResponse:
    text = (
        message
        or _AUTH_MESSAGES.get(code)
        or _RUNTIME_MESSAGES.get(code)
        or _PUBLICATION_MESSAGES.get(code)
        or chinese_message_for(code)
    )
    if _SECRET_VALUE.search(str(text)):
        code = "forbidden_secret_field"
        text = chinese_message_for(code)
        status_code = 422
    return JSONResponse(status_code=status_code, content={"code": code, "message": text})


def _run_entry_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, pb.ProjectBackupError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    if isinstance(exc, rs.RunSetupError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    if isinstance(exc, MigrationError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    if isinstance(exc, ProjectCompatibilityError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    if isinstance(exc, (RunEntryError, RuntimeProgressError)):
        return _error_response(_status_for(exc.code), exc.code)
    return _error_response(500, "internal_error")


_BACKUP_STATUS_LABEL = {
    pb.STATUS_REQUESTED: "准备中",
    pb.STATUS_RECEIVED: "准备中",
    pb.STATUS_WAITING_FOR_PROJECT: "准备中",
    pb.STATUS_COLLECTING: "正在整理项目",
    pb.STATUS_SNAPSHOTTING: "正在整理项目",
    pb.STATUS_VERIFYING: "正在核对",
    pb.STATUS_PACKAGING: "正在整理项目",
    pb.STATUS_AVAILABLE: "已可下载",
    pb.STATUS_INSPECTING: "正在核对",
    pb.STATUS_VERIFYING_MEMBERS: "正在核对",
    pb.STATUS_RECONCILING_IDENTITY: "正在核对",
    pb.STATUS_READY_FOR_CONFIRMATION: "正在核对",
    pb.STATUS_CONFIRMED: "正在恢复项目",
    pb.STATUS_STAGING: "正在恢复项目",
    pb.STATUS_VERIFYING_STAGED_WORKSPACE: "正在核对",
    pb.STATUS_QUIESCING_PROJECT: "正在恢复项目",
    pb.STATUS_SWITCHING: "正在恢复项目",
    pb.STATUS_VERIFYING_LIVE_WORKSPACE: "正在核对",
    pb.STATUS_COMPLETED: "恢复完成",
    pb.STATUS_ALREADY_CURRENT: "项目已是此版本",
    pb.STATUS_KEPT_CURRENT: "保持原项目未变",
    pb.STATUS_ROLLBACK_IN_PROGRESS: "需要人工处理",
    pb.STATUS_RETAINED_FOR_TRIAGE: "需要人工处理",
    pb.STATUS_FAILED: "未能完成",
}
_BACKUP_STEP_LABEL = {
    pb.STATUS_REQUESTED: "正在准备项目",
    pb.STATUS_RECEIVED: "正在准备项目",
    pb.STATUS_WAITING_FOR_PROJECT: "正在等待项目空闲",
    pb.STATUS_COLLECTING: "正在整理项目",
    pb.STATUS_SNAPSHOTTING: "正在整理项目",
    pb.STATUS_VERIFYING: "正在核对",
    pb.STATUS_PACKAGING: "正在整理项目",
    pb.STATUS_AVAILABLE: "已可下载",
    pb.STATUS_INSPECTING: "正在核对",
    pb.STATUS_VERIFYING_MEMBERS: "正在核对",
    pb.STATUS_RECONCILING_IDENTITY: "正在核对",
    pb.STATUS_READY_FOR_CONFIRMATION: "恢复前检查已完成",
    pb.STATUS_CONFIRMED: "正在恢复项目",
    pb.STATUS_STAGING: "正在恢复项目",
    pb.STATUS_VERIFYING_STAGED_WORKSPACE: "正在核对",
    pb.STATUS_QUIESCING_PROJECT: "正在恢复项目",
    pb.STATUS_SWITCHING: "正在恢复项目",
    pb.STATUS_VERIFYING_LIVE_WORKSPACE: "正在核对",
    pb.STATUS_COMPLETED: "恢复完成",
    pb.STATUS_ALREADY_CURRENT: "恢复完成",
    pb.STATUS_KEPT_CURRENT: "等待恢复确认",
    pb.STATUS_ROLLBACK_IN_PROGRESS: "需要人工处理",
    pb.STATUS_RETAINED_FOR_TRIAGE: "需要人工处理",
    pb.STATUS_FAILED: "未能完成",
}
_BACKUP_IMPACT_LABEL = {
    "runs": "监查运行",
    "publications": "结果发布",
    "risk_rules": "风险规则",
    "continuity_plans": "连续性计划",
}


def _backup_payload_manifest(record: pb.OperationRecord) -> Mapping[str, Any]:
    payload = record.payload
    if not isinstance(payload, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    manifest = payload.get("manifest", {})
    if manifest is None:
        return {}
    if not isinstance(manifest, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return manifest


def _backup_progress(record: pb.OperationRecord) -> int:
    value = record.progress_percent
    if isinstance(value, bool) or not isinstance(value, int):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return max(0, min(100, value))


def _backup_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value


def _backup_scope_summary(manifest: Mapping[str, Any]) -> str:
    summary = manifest.get("project_summary", {})
    if not isinstance(summary, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    counts = summary.get("counts", {})
    if not isinstance(counts, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    runs = counts.get("runs", 0)
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 0:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return f"已整理 {runs} 次监查运行" if runs else "已整理当前项目监查资料"


def _public_backup_projection(
    record: pb.OperationRecord,
    canonical_project_id: str,
) -> dict[str, Any]:
    status = str(record.status)
    if status not in _BACKUP_STATUS_LABEL:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    manifest = _backup_payload_manifest(record)
    summary = manifest.get("project_summary", {})
    if summary is not None and not isinstance(summary, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    project_name = _backup_text(
        manifest.get("project_name") if manifest else None,
        canonical_project_id,
    )
    cutoff = _backup_text(
        manifest.get("backup_cutoff") if manifest else None,
        "尚未建立监查运行",
    )
    body: dict[str, Any] = {
        "operation_id": record.operation_id,
        "status_label": _BACKUP_STATUS_LABEL[status],
        "project_name": project_name,
        "backup_cutoff_label": cutoff,
        "monitoring_scope_summary": _backup_scope_summary(manifest),
        "recommended_next_action": (
            "下载备份文件"
            if status == pb.STATUS_AVAILABLE
            else "请稍后重试"
            if status == pb.STATUS_FAILED
            else "请查看备份进度"
        ),
        "progress_percent": _backup_progress(record),
        "current_step_label": _BACKUP_STEP_LABEL[status],
    }
    if isinstance(summary, Mapping) and summary.get("unfinished_work"):
        body["unfinished_work_notice"] = (
            "此备份包含未完成的监查任务，恢复后仍需继续处理"
        )
    return body


def _public_impact_items(value: Any) -> dict[str, int]:
    if value is None:
        value = {}
    if not isinstance(value, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    result: dict[str, int] = {}
    for key, label in _BACKUP_IMPACT_LABEL.items():
        count = value.get(key, 0)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise pb.ProjectBackupError("sqlite_integrity_failed")
        result[label] = count
    return result


def _public_preflight_projection(
    result: pb.PreflightResult,
    backup_operation_id: str,
) -> dict[str, Any]:
    items_rolled_back = _public_impact_items(result.items_rolled_back)
    impact_summary = (
        "无预计回退事项"
        if not any(items_rolled_back.values())
        else "、".join(
            f"{label} {count} 项"
            for label, count in items_rolled_back.items()
            if count
        )
    )
    operation = result.operation
    status = str(operation.status)
    step = _BACKUP_STEP_LABEL.get(status, "正在核对")
    body: dict[str, Any] = {
        "operation_id": result.operation_id,
        "backup_operation_id": backup_operation_id,
        "decision_label": result.decision_label,
        "backup_project_name": result.project_name,
        "backup_cutoff_label": result.backup_cutoff_label,
        "current_cutoff_label": result.current_cutoff_label,
        "impact_summary": impact_summary,
        "items_preserved": list(result.items_preserved),
        "items_rolled_back": items_rolled_back,
        "recommended_action": result.recommended_action,
        "confirmation_required": bool(result.confirmation_required),
        "unfinished_work_notice": (
            result.unfinished_work_notice or ""
        ),
        "progress_percent": _backup_progress(operation),
        "current_step_label": step,
    }
    return body


def _public_restore_projection(
    record: pb.OperationRecord,
    canonical_project_id: str,
) -> dict[str, Any]:
    status = str(record.status)
    if status not in _BACKUP_STATUS_LABEL:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    payload = record.payload
    if not isinstance(payload, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    if status == pb.STATUS_COMPLETED:
        result_label = "恢复完成"
    elif status == pb.STATUS_ALREADY_CURRENT:
        result_label = "项目已是此版本"
    elif status == pb.STATUS_KEPT_CURRENT:
        result_label = "保持原项目未变"
    elif status in {
        pb.STATUS_RETAINED_FOR_TRIAGE,
        pb.STATUS_ROLLBACK_IN_PROGRESS,
        pb.STATUS_FAILED,
    }:
        result_label = "需要人工处理"
    else:
        result_label = "正在恢复项目"
    return {
        "operation_id": record.operation_id,
        "result_label": result_label,
        "project_name": _backup_text(
            payload.get("project_name"), canonical_project_id
        ),
        "restored_cutoff_label": _backup_text(
            payload.get("restored_cutoff_label"), "当前项目尚未建立"
        ),
        "verification_summary": _backup_text(
            payload.get("verification_summary"),
            "项目恢复尚未完成，请稍后核对",
        ),
        "next_action_label": _backup_text(
            payload.get("next_action_label"),
            "请稍后核对项目状态",
        ),
        "progress_percent": _backup_progress(record),
        "current_step_label": _BACKUP_STEP_LABEL[status],
    }
def _launch_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, lr.LaunchRegistryError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    return _error_response(500, "internal_error")


def _launch_projection(record: lr.LaunchRecord, *, replayed: bool) -> dict[str, Any]:
    body = record.public_projection()
    body["replayed"] = bool(replayed)
    return _projection(body)

def _publication_status_text(state: str, *, run_state: str = "") -> str:
    if (
        run_state == lr.STATE_COMPLETED
        and state != lr.PUBLICATION_STATE_AVAILABLE
    ):
        return "分析已结束，结果整理未完成"
    if state == lr.PUBLICATION_STATE_AVAILABLE:
        return _PUBLICATION_MESSAGES["publication_available"]
    if state == lr.PUBLICATION_STATE_PUBLISHING:
        return _PUBLICATION_MESSAGES["publication_publishing"]
    if state == lr.PUBLICATION_STATE_RECOVERABLE_FAILED:
        return _PUBLICATION_MESSAGES["publication_recoverable_failed"]
    if state == lr.PUBLICATION_STATE_BLOCKED:
        return _PUBLICATION_MESSAGES["publication_blocked"]
    return _PUBLICATION_MESSAGES["publication_not_available"]


def _publication_projection(
    public_run_token: str,
    state: str,
    *,
    replayed: bool = False,
    run_state: str = "",
) -> dict[str, Any]:
    if state not in lr.PUBLICATION_STATE_VALUES and state != "not_started":
        raise ProductPublicationError("internal_error")
    return {
        "public_run_token": public_run_token,
        "publication_state": state,
        "result_available": state == lr.PUBLICATION_STATE_AVAILABLE,
        "publication_status_text": _publication_status_text(
            state, run_state=run_state
        ),
        "replayed": bool(replayed),
    }


_PUBLIC_RESULT_LOCATOR_KEYS = (
    "site_ref",
    "subject_ref",
    "spine_ref",
    "window_start",
    "window_end",
    "risk_instance_ref",
    "risk_anchor_ref",
    "visit_ref",
    "event_ref",
    "source_locator_ref",
)
_PUBLIC_RESULT_FORBIDDEN_KEYS = frozenset(
    {
        "run_id",
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "cutoff_state",
        "opaque_run_ref",
        "opaque_snapshot_ref",
        "authority_hash",
        "authority_receipt",
        "authority_receipt_ref",
        "receipt_id",
        "receipt_ref",
        "receipt_set_digest",
        "packet_identity",
        "packet_digest",
        "r5_authority_packet_id",
        "r5_authority_packet_digest",
        "s4_authority_packet_identities",
        "s4_authority_packet_digests",
        "source_snapshot_sha256",
        "source_revision_content_hash",
        "response_snapshot_sha256",
        "return_context_key",
        "r6_output_set_digest",
        "artifact_member_ids",
        "artifact_member_ids_json",
        "artifact_member_set_digest",
        "r6_publication_digest",
        "r6_receipt_digest",
    }
)


def _public_result_projection(value: Any) -> Any:
    """Strip internal authority identity while retaining the R5 audience shape."""
    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            lowered = key.casefold()
            if (
                lowered in _PUBLIC_RESULT_FORBIDDEN_KEYS
                or lowered.startswith(("authority_", "receipt_", "s4_", "r5_"))
                or lowered.endswith("_snapshot_ref")
                or lowered.endswith("_cutoff_ref")
            ):
                continue
            projected[key] = _public_result_projection(item)
        if "content_hash" in projected:
            projected["content_hash"] = lr.content_digest(
                {**projected, "content_hash": ""}
            )
        return projected
    if isinstance(value, list):
        return [_public_result_projection(item) for item in value]
    if isinstance(value, tuple):
        return [_public_result_projection(item) for item in value]
    return value


async def _reject_public_result_body(request: Request) -> Optional[JSONResponse]:
    if await request.body():
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return None


def _parse_public_result_query(
    request: Request,
    *,
    allowed: frozenset[str],
    required: frozenset[str] = frozenset(),
) -> Union[dict[str, str], JSONResponse]:
    values: dict[str, str] = {}
    for key, raw_value in request.query_params.multi_items():
        if key not in allowed or key in values:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        value = str(raw_value or "").strip()
        if not value:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        values[key] = value
    if not required.issubset(values):
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return values


def _canonical_public_result_value(
    value: Any, *, field_name: str
) -> Union[str, JSONResponse]:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return value


def _parse_public_result_date(
    value: str,
) -> Union[date, JSONResponse]:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    if parsed.isoformat() != value:
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return parsed

def _comparison_range_text(
    mode: str,
    execution_basis: str,
    baseline: Optional[rs.PublishedBaseline],
) -> str:
    if baseline is not None:
        return f"{baseline.scope_description}（数据截止 {baseline.data_cutoff}）"
    if mode == rs.MODE_POST_LOCK_PRE_CFDI:
        return "当前固定总量完整数据（不使用比较基线）"
    if execution_basis == rs.BASIS_INCREMENTAL:
        return "同项目已发布数据基线"
    return "当前完整数据（不使用比较基线）"


def _validation_error_response(exc: ValidationError) -> JSONResponse:
    locations = {
        str(part).lower()
        for error in exc.errors()
        for part in error.get("loc", ())
    }
    messages = " ".join(str(error.get("msg", "")) for error in exc.errors())
    if locations & _SECRET_FIELDS:
        code = "forbidden_secret_field"
    elif "credential_ref_must_not_be_secret_value" in messages:
        code = "credential_ref_must_not_be_secret_value"
    elif any(error.get("type") == "extra_forbidden" for error in exc.errors()):
        code = "unknown_request_field"
    elif "unknown_mode" in messages:
        code = "unknown_mode"
    elif "unknown_execution_basis" in messages:
        code = "unknown_execution_basis"
    elif "empty_or_illegal_scope_key" in messages:
        code = "empty_or_illegal_scope_key"
    elif "unsafe_data_cutoff" in messages:
        code = "unsafe_data_cutoff"
        return _error_response(422, code, _RUNTIME_MESSAGES[code])
    elif "invalid_identity" in messages or "invalid_prior" in messages:
        code = "request_validation_failed"
    else:
        code = "request_validation_failed"
    return _error_response(422, code, chinese_message_for(code))


def _projection(result: Any, *, replayed: bool = False) -> dict[str, Any]:
    if isinstance(result, Mapping):
        body = dict(result)
    else:
        value = getattr(result, "profile", None)
        if not isinstance(value, Mapping):
            value = getattr(result, "binding", None)
        if not isinstance(value, Mapping):
            raise RunEntryError("internal_error")
        body = dict(value)
        if replayed:
            body["replayed"] = bool(getattr(result, "replayed"))
    lowered_keys = {str(key).lower() for key in body}
    if lowered_keys & _FORBIDDEN_PUBLIC:
        raise RunEntryError("internal_error")
    blob = json.dumps(body, ensure_ascii=False)
    if _SECRET_VALUE.search(blob) or "credential_value" in blob.lower():
        raise RunEntryError("internal_error")
    return body
 
def _legacy_profile_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Rebuild the existing public profile shape without opening a store."""
    payload = row.get("payload_json")
    if not isinstance(payload, Mapping):
        raise RunEntryError("internal_error")
    try:
        validated_row = dict(row)
        validated_row["payload_json"] = ps.canonical_json_bytes(
            payload
        ).decode("utf-8")
        record = ps._row_to_record(validated_row)
        return _projection(ps.public_projection(record))
    except Exception as exc:
        raise RunEntryError("internal_error") from exc


def _legacy_binding_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the binding's bounded public fields from a read-only row."""
    body = {
        "run_id": row.get("run_id"),
        "project_id": row.get("project_id"),
        "mode": row.get("mode"),
        "execution_basis": row.get("execution_basis"),
        "data_cutoff": row.get("data_cutoff"),
        "source_revision_id": row.get("source_revision_id"),
        "prior_accepted_snapshot_ref": row.get("prior_accepted_snapshot_ref"),
        "user_config_name": row.get("user_config_name"),
        "adapter_id": row.get("adapter_id"),
        "adapter_version": row.get("adapter_version"),
        "schema_version": row.get("schema_version"),
    }
    if any(value is None for value in body.values()):
        raise RunEntryError("internal_error")
    return _projection(body)


def _legacy_launch_record(row: Mapping[str, Any]) -> lr.LaunchRecord:
    """Materialize an immutable public-history record from a read-only row."""
    raw_rule_tokens = row.get("rule_tokens_json", ())
    if raw_rule_tokens is None:
        raw_rule_tokens = ()
    if not isinstance(raw_rule_tokens, (list, tuple)):
        raise lr.LaunchRegistryError("store_closed")
    try:
        return lr.LaunchRecord(
            sequence=int(row.get("sequence", 0)),
            project_id=str(row.get("project_id", "")),
            idempotency_key=str(row.get("idempotency_key", "")),
            run_id=str(row.get("run_id", "")),
            public_run_token=str(row.get("public_run_token", "")),
            request_fingerprint=str(row.get("request_fingerprint", "")),
            mode=str(row.get("mode", "")),
            execution_basis=str(row.get("execution_basis", "")),
            current_snapshot_token=str(row.get("current_snapshot_token", "")),
            baseline_token=(
                None
                if row.get("baseline_token") is None
                else str(row.get("baseline_token"))
            ),
            rule_tokens=tuple(str(value) for value in raw_rule_tokens),
            data_cutoff=str(row.get("data_cutoff", "")),
            comparison_range_text=str(row.get("comparison_range_text", "")),
            run_state=str(row.get("run_state", "")),
            result_available=bool(row.get("result_available", False)),
            main_action=str(row.get("main_action", "")),
            manifest_digest=(
                None
                if row.get("manifest_digest") is None
                else str(row.get("manifest_digest"))
            ),
            created_at=str(row.get("created_at", "")),
            updated_at=str(row.get("updated_at", "")),
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise lr.LaunchRegistryError("store_closed") from exc


def _legacy_risk_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the same bounded rule-revision projection as the live registry."""
    try:
        body = {
            "project_id": str(row["project_id"]),
            "revision": int(row["revision"]),
            "revision_token": str(row["revision_token"]),
            "summary": str(row["summary"]),
            "applicable_scope": str(row["applicable_scope"]),
            "starting_run": str(row["starting_run"]),
            "selectable": bool(row["selectable"]),
            "created_at": str(row["created_at"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise rs.RunSetupError("risk_rule_not_found") from exc
    return _setup_projection(body)


def _legacy_progress_projection(
    view: ReadOnlyProjectView,
    run_id: str,
    launch: Optional[lr.LaunchRecord],
) -> dict[str, Any]:
    """Project legacy execution rows without opening the mutable runtime."""
    bindings = [
        row for row in view.list_run_bindings()
        if row.get("run_id") == run_id
    ]
    if not bindings:
        raise RuntimeProgressError("run_binding_not_found")
    binding = bindings[0]
    runtime_rows = [
        row for row in view.list_monitoring_runs()
        if row.get("run_id") == run_id
    ]
    if not runtime_rows:
        raise RuntimeProgressError("execution_not_prepared")
    work_rows = list(view.list_work_unit_runs(run_id))
    status_order = (
        "pending",
        "running",
        "passed",
        "reused",
        "skipped",
        "not_applicable",
        "blocked",
        "failed",
    )
    if any(str(row.get("status")) not in status_order for row in work_rows):
        raise RuntimeProgressError("runtime_integrity_failed")
    counts = {
        status: sum(1 for row in work_rows if str(row.get("status")) == status)
        for status in status_order
    }
    total = len(work_rows)
    completed = sum(
        counts[status]
        for status in status_order
        if status not in {"pending", "running"}
    )
    percent = round((completed * 100.0 / total), 2) if total else 0.0
    state = launch.run_state if launch is not None else ""
    if state not in lr.RUN_STATE_VALUES:
        if counts["running"]:
            state = lr.STATE_RUNNING
        elif total and completed == total:
            state = lr.STATE_COMPLETED
        else:
            state = lr.STATE_WAITING_START
    mode_text = {
        lr.MODE_DAILY: "日常监查",
        lr.MODE_PRE_LOCK: "锁库前监查",
        lr.MODE_POST_LOCK_PRE_CFDI: "核查前监查",
    }.get(str(binding.get("mode")), "本次监查")
    basis_text = {
        lr.BASIS_FULL: "全面分析",
        lr.BASIS_INCREMENTAL: "增量比较",
    }.get(str(binding.get("execution_basis")), "本次分析")
    status_text = {
        lr.STATE_WAITING_START: "等待开始医学监查",
        lr.STATE_RUNNING: "医学监查进行中",
        lr.STATE_STOPPING: "正在停止医学监查",
        lr.STATE_INTERRUPTED_RESUMABLE: "已停止，可继续",
        lr.STATE_COMPLETED: "本次医学监查已完成",
        lr.STATE_ENDED_INCOMPLETE: "本次监查已结束，部分工作未完成",
        lr.STATE_FAILED: "本次监查未完成",
    }[state]
    publication_rows = list(view.list_publications(run_id=run_id))
    publication_state = (
        str(publication_rows[0].get("publication_state", ""))
        if publication_rows
        else "not_started"
    )
    if publication_state not in lr.PUBLICATION_STATE_VALUES and publication_state != "not_started":
        publication_state = lr.PUBLICATION_STATE_RECOVERABLE_FAILED
    if state == lr.STATE_COMPLETED and publication_state != lr.PUBLICATION_STATE_AVAILABLE:
        headline = "分析已结束，结果整理未完成"
    elif state == lr.STATE_COMPLETED:
        headline = "本次医学监查已完成"
    elif state == lr.STATE_RUNNING:
        headline = "医学监查进行中"
    elif state == lr.STATE_WAITING_START:
        headline = "等待开始医学监查"
    else:
        headline = status_text
    actions = {
        lr.STATE_WAITING_START: ["开始"],
        lr.STATE_RUNNING: ["停止"],
        lr.STATE_INTERRUPTED_RESUMABLE: ["继续"],
    }.get(state, [])
    if state == lr.STATE_COMPLETED:
        if publication_state == "not_started":
            actions = ["整理结果"]
        elif publication_state in {
            lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
            lr.PUBLICATION_STATE_BLOCKED,
        }:
            actions = ["重新整理"]
    status_labels = {
        "pending": "等待开始",
        "running": "进行中",
        "passed": "已完成",
        "reused": "已沿用已有结果",
        "skipped": "本次无需处理",
        "not_applicable": "本研究不适用",
        "blocked": "暂时受阻",
        "failed": "未完成",
    }
    status_overview = [
        {"state_label": status_labels[status], "count": counts[status]}
        for status in status_order
        if counts[status]
    ]
    manifest_revision = max(
        [int(row.get("manifest_revision", 0)) for row in work_rows]
        + [int(runtime_rows[0].get("manifest_revision", 0))],
    )
    cutoff = validate_public_data_cutoff(binding.get("data_cutoff"))
    return {
        "scope_version_text": f"第 {manifest_revision} 版监查范围",
        "mode_text": mode_text,
        "basis_text": basis_text,
        "data_cutoff_text": cutoff,
        "headline": headline,
        "completed": completed,
        "total": total,
        "percent": float(percent),
        "progress_text": f"已处理 {completed}/{total} 项（{float(percent):g}%）",
        "status_overview": status_overview,
        "stage_progress": [],
        "current_work": [],
        "latest_updates": [],
        "run_status_text": status_text,
        "available_actions": actions,
        "run_state": state,
        "publication_state": publication_state,
        "result_available": publication_state == lr.PUBLICATION_STATE_AVAILABLE,
        "publication_status_text": _publication_status_text(
            publication_state,
            run_state=state,
        ),
    }


def _execution_action_projection(result: Any) -> dict[str, Any]:
    """Keep start/resume/stop responses to the product-safe overlay only."""
    expected = {"replayed", "run_status_text", "available_actions"}
    if not isinstance(result, Mapping) or set(result) != expected:
        raise RunEntryError("internal_error")
    if not isinstance(result["replayed"], bool):
        raise RunEntryError("internal_error")
    status_text = result["run_status_text"]
    actions = result["available_actions"]
    if (
        not isinstance(status_text, str)
        or not status_text.strip()
        or not any("\u4e00" <= char <= "\u9fff" for char in status_text)
        or not isinstance(actions, list)
        or any(
            not isinstance(action, str)
            or not action.strip()
            or not any("\u4e00" <= char <= "\u9fff" for char in action)
            for action in actions
        )
    ):
        raise RunEntryError("internal_error")
    blob = json.dumps(result, ensure_ascii=False).casefold()
    if _SECRET_VALUE.search(blob) or any(token in blob for token in _RUNTIME_INTERNAL_TOKENS):
        raise RunEntryError("internal_error")
    return dict(result)


def _safe_setup_projection(value: Any, *, key: str = "") -> Any:
    """Project opaque setup tokens without exposing internal rule identity."""
    if isinstance(value, Mapping):
        return {
            item_key: _safe_setup_projection(item, key=str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe_setup_projection(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_setup_projection(item) for item in value]
    if key == "revision_token" and isinstance(value, str):
        return rs.public_revision_token(value)
    return value


def _setup_projection(result: Any) -> dict[str, Any]:
    return _projection(_safe_setup_projection(result))


def _runtime_work_units(manifest: rs.WorkUnitManifest) -> list[dict[str, Any]]:
    """Adapt setup labels to the established R1 audience work-unit shape."""
    stage_text = {
        "common": "通用检查",
        rs.MODE_DAILY: "日常监查",
        rs.MODE_PRE_LOCK: "锁库前监查",
        rs.MODE_POST_LOCK_PRE_CFDI: "核查前监查",
        "daily_diff": "数据变化",
        "special_risk_rule": "特殊关注",
    }
    units: list[dict[str, Any]] = []
    for unit in manifest:
        label = (
            unit.label.replace("/", "、").replace("\\", "、")
            if any("\u4e00" <= char <= "\u9fff" for char in unit.label)
            else f"监查：{unit.label}"
        )
        if unit.stage == "special_risk_rule":
            revision_text = unit.target_ref.rsplit(":", 1)[-1]
            if revision_text.isdigit():
                label = f"{label}（已确认规则第 {revision_text} 版）"
        units.append(
            {
                **unit.as_dict(),
                "stage": stage_text.get(unit.stage, "监查检查"),
                "scope": "project",
                "target_ref": label,
                "label": label,
            }
        )
    return units


def _publication_manifest_identity(manifest: Any) -> dict[str, Any]:
    """Return the cross-manifest identity subset frozen by 07C-3."""

    units = getattr(manifest, "work_units", None)
    if units is None:
        units = getattr(manifest, "units", None)
    values: list[dict[str, Any]] = []
    seen: set[str] = set()
    for unit in units:
        work_unit_id = getattr(unit, "work_unit_id", None)
        mandatory = getattr(unit, "mandatory", None)
        if (
            not isinstance(work_unit_id, str)
            or not work_unit_id.strip()
            or not isinstance(mandatory, bool)
            or work_unit_id in seen
        ):
            raise ProductPublicationError("manifest_identity_mismatch")
        seen.add(work_unit_id)
        values.append({"work_unit_id": work_unit_id, "mandatory": mandatory})
    values.sort(key=lambda item: item["work_unit_id"])
    return {
        "work_units": values,
        "mandatory_denominator": sum(
            bool(item["mandatory"]) for item in values
        ),
    }


def _runtime_manifest_digest(manifest: Any) -> str:
    try:
        return content_hash(to_jsonable(manifest))
    except Exception as exc:
        raise ProductPublicationError("manifest_identity_mismatch") from exc




def _runtime_manifest_metadata(
    workspace: Path,
    run_id: str,
) -> Optional[dict[str, Any]]:
    """Read existing R1 manifest metadata without creating runtime state."""

    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        return None
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        run = store.get_run(run_id)
        revision = int(run.manifest_revision)
        if revision < 1:
            return None
        manifest = store.get_manifest(run_id, revision)
        if manifest is None:
            raise ProductPublicationError(
                "runtime_read_failed", recoverable=True
            )
        return {
            "revision": revision,
            "manifest": manifest,
            "identity": _publication_manifest_identity(manifest),
            "digest": _runtime_manifest_digest(manifest),
        }
    except ProductPublicationError:
        raise
    except Exception as exc:
        raise ProductPublicationError(
            "runtime_read_failed", recoverable=True
        ) from exc
    finally:
        if store is not None:
            store.close()


def _runtime_audit_chain_is_invalid(
    workspace: Path,
    run_id: str,
) -> bool:
    """Detect audit corruption after a progress read fails closed."""

    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        return False
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        store.get_run(run_id)
        result = store.verify_audit_chain()
        return (
            isinstance(result, tuple)
            and len(result) == 3
            and result[0] is False
        )
    except Exception:
        return False
    finally:
        if store is not None:
            store.close()


def _r5_publication_types() -> tuple[Any, Any, Any, Any, Any]:
    """Load R5 publication types lazily at the synthetic integration seam."""

    try:
        from packages.medical_monitoring.projections.publication.r5_publication_authority import (
            R5AuthorityPacket,
            R5PublicationAuthorityBridge,
            R5PublicationAuthorityError,
            R5PublicationAuthorityInput,
            R5PublicationRunIdentity,
        )
    except Exception as exc:
        raise ProductPublicationError(
            "authority_provider_unavailable", recoverable=True
        ) from exc
    return (
        R5AuthorityPacket,
        R5PublicationAuthorityBridge,
        R5PublicationAuthorityError,
        R5PublicationAuthorityInput,
        R5PublicationRunIdentity,
    )


def _call_publication_method(
    method: Callable[..., Any],
    identity: Any,
    context: Mapping[str, Any],
    *,
    packet_argument: Any = None,
) -> Any:
    """Call an injected read-only provider without guessing medical facts."""

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        if packet_argument is not None:
            return method(packet_argument)
        return method(identity)

    parameters = tuple(signature.parameters.values())
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    named = {
        name: value
        for name, value in context.items()
        if name in signature.parameters
    }
    if accepts_kwargs:
        named = dict(context)

    if packet_argument is not None:
        if "packet" in signature.parameters:
            named["packet"] = packet_argument
            return method(**named)
        positional = [
            parameter
            for parameter in parameters
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if positional:
            return method(packet_argument, **named)
        return method(**named)

    identity_names = {
        "identity",
        "run_identity",
        "publication_identity",
        "authority_identity",
    }
    if any(name in signature.parameters for name in identity_names):
        name = next(
            name for name in identity_names if name in signature.parameters
        )
        named[name] = identity
        return method(**named)
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if positional:
        if positional[0].name in named:
            return method(**named)
        return method(identity, **named)
    return method(**named)


def _publication_provider_value(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
) -> Any:
    if provider is None:
        raise ProductPublicationError("authority_provider_invalid")
    _, _, _, input_type, packet_identity_type = _r5_publication_types()
    if isinstance(provider, (input_type, packet_identity_type)):
        return provider
    context = {
        "run_identity": identity,
        "identity": identity,
        "project_ref": identity.project_ref,
        "run_ref": identity.run_ref,
        "public_run_token": identity.public_run_token,
        "snapshot_ref": identity.snapshot_ref,
        "snapshot_token": identity.snapshot_token,
        "cutoff_ref": identity.cutoff_ref,
        "site_refs": identity.site_refs,
        "attempts": tuple(attempts),
        "receipts": tuple(attempts),
        "raw_receipts": tuple(attempts),
        "r6_receipts": tuple(attempts),
        "receipt_attempts": tuple(attempts),
    }
    method_names = (
        "get_publication_input",
        "get_authority",
        "get_publication_authority",
        "get_publication_authority_input",
        "get_authority_input",
        "build_publication_authority_input",
        "build_authority_input",
        "assemble_publication_input",
        "assemble_authority_input",
        "assemble",
        "get_publication_authority_packet",
        "get_authority_packet",
        "build_publication_authority_packet",
        "get_publication_packet",
        "build_publication_packet",
        "get_packet",
    )
    for name in method_names:
        method = getattr(provider, name, None)
        if callable(method):
            try:
                return _call_publication_method(method, identity, context)
            except ProductPublicationError:
                raise
            except Exception as exc:
                raise ProductPublicationError(
                    "authority_provider_unavailable", recoverable=True
                ) from exc
    for name in ("authority_input", "publication_input", "publication_packet"):
        value = getattr(provider, name, None)
        if isinstance(value, (input_type, packet_identity_type)):
            return value
    if callable(provider):
        try:
            return _call_publication_method(provider, identity, context)
        except ProductPublicationError:
            raise
        except Exception as exc:
            raise ProductPublicationError(
                "authority_provider_unavailable", recoverable=True
            ) from exc
    raise ProductPublicationError("authority_provider_invalid")


def _publication_product_factory(
    provider: Any,
) -> Optional[Callable[[Any], Any]]:
    for name in ("product_packet_factory", "build_product_packet"):
        method = getattr(provider, name, None)
        if callable(method):
            return lambda packet, method=method: _call_publication_method(
                method,
                packet,
                {"packet": packet},
                packet_argument=packet,
            )
    return None

def _r6_publication_types() -> tuple[Any, Any]:
    """Load R6 publication types lazily at the synthetic integration seam."""
    try:
        from packages.medical_monitoring.reports import mode_output as mo
        from packages.medical_monitoring.runtime import continuity_bridge as cb
    except Exception as exc:
        raise ProductPublicationError(
            "receipt_gate_blocked", recoverable=False
        ) from exc
    return mo, cb


def _call_r6_provider_method(
    method: Callable[..., Any],
    run_binding: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(run_binding)

    parameters = tuple(signature.parameters.values())
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    named = {
        name: value
        for name, value in context.items()
        if name in signature.parameters
    }
    if accepts_kwargs:
        named = dict(context)

    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if positional:
        first_name = positional[0].name
        if first_name not in named:
            return method(run_binding, **named)
    return method(**named)


def _obtain_r6_mode_outputs(
    provider: Any,
    run_binding: Mapping[str, Any],
    *,
    r5_packet: Optional[Any] = None,
    attempts: Sequence[Mapping[str, Any]] = (),
) -> Optional[Sequence[Mapping[str, Any]]]:
    if provider is None:
        return None
    if isinstance(provider, (tuple, list)):
        return tuple(provider)
    mo, _ = _r6_publication_types()
    binding = dict(run_binding)
    binding.setdefault("carry_forward_run_ids", [])
    binding.setdefault("mode_transition", "explicit_new_run")
    binding.setdefault("actor", "system_synthetic")
    if not binding.get("created_at"):
        binding["created_at"] = "2026-08-28T00:00:00Z"
    if not binding.get("knowledge_pack_version"):
        binding["knowledge_pack_version"] = "kp-08b-v1"
    if not binding.get("rule_activation_version"):
        binding["rule_activation_version"] = "rav-08b-v1"
    if not binding.get("mapping_version"):
        binding["mapping_version"] = "map-08b-v1"
    if not binding.get("identity_algorithm_version"):
        binding["identity_algorithm_version"] = "ia-08b-v1"
    if not binding.get("identity_algorithm_digest"):
        binding["identity_algorithm_digest"] = "ia-digest-08b-v1"
    mode = str(binding.get("mode", ""))
    if mode == "post_lock_pre_cfdi":
        binding.setdefault("fixed_total", True)
        if not binding.get("locked_snapshot_hash"):
            binding["locked_snapshot_hash"] = "snap-hash-fixed-001"
        if not binding.get("output_cutoff_ref"):
            binding["output_cutoff_ref"] = binding.get("data_cutoff")
        if not binding.get("output_revision_ref"):
            binding["output_revision_ref"] = binding.get("source_revision_id")
        if not binding.get("local_os_user"):
            binding["local_os_user"] = "local-user-synthetic"
        if not binding.get("acceptance_evidence_hash"):
            binding["acceptance_evidence_hash"] = "accept-hash-fixed-001"
    mode_contract = mo.build_mode_contract(mode) if mode in mo.MODES else None
    context = {
        "run_binding": binding,
        "binding": binding,
        "mode": mode,
        "mode_contract": mode_contract,
        "contract": mode_contract,
        "project_id": binding.get("project_id"),
        "run_id": binding.get("run_id"),
        "r5_packet": r5_packet,
        "packet": r5_packet,
        "attempts": tuple(attempts),
        "receipts": tuple(attempts),
    }
    run_binding = binding
    method_names = (
        "get_mode_outputs",
        "build_mode_outputs",
        "get_outputs",
        "build_outputs",
        "get_r6_outputs",
        "build_r6_outputs",
        "get_publication_outputs",
        "build_publication_outputs",
    )
    for name in method_names:
        method = getattr(provider, name, None)
        if callable(method):
            try:
                result = _call_r6_provider_method(method, run_binding, context)
                if isinstance(result, (tuple, list)):
                    return tuple(result)
            except Exception as exc:
                raise ProductPublicationError(
                    "receipt_gate_blocked", recoverable=False
                ) from exc
    if callable(provider):
        try:
            result = _call_r6_provider_method(provider, run_binding, context)
            if isinstance(result, (tuple, list)):
                return tuple(result)
        except Exception as exc:
            raise ProductPublicationError(
                "receipt_gate_blocked", recoverable=False
            ) from exc
    raise ProductPublicationError("receipt_gate_blocked", recoverable=False)


def _validate_r5_publication_packet(
    packet: Any,
    identity: Any,
    *,
    packet_type: Any,
) -> Any:
    if type(packet) is not packet_type:
        raise ProductPublicationError("authority_provider_invalid")
    if (
        packet.project_ref != identity.project_ref
        or packet.run_ref != identity.run_ref
        or packet.public_run_token != identity.public_run_token
        or packet.snapshot_ref != identity.snapshot_ref
        or packet.cutoff_ref != identity.cutoff_ref
        or tuple(sorted(packet.site_refs)) != tuple(identity.site_refs)
    ):
        raise ProductPublicationError("authority_identity_mismatch")
    if (
        not isinstance(packet.packet_identity, str)
        or not isinstance(packet.packet_digest, str)
        or packet.packet_identity != "r5-publication-authority:" + packet.packet_digest
        or packet.authority_hash != packet.packet_digest
        or not packet.s4_packets
    ):
        raise ProductPublicationError("authority_provider_invalid")
    coverage = set(identity.site_refs)
    sites = {getattr(value, "site_ref", None) for value in packet.sites}
    if sites != coverage:
        raise ProductPublicationError("authority_identity_mismatch")
    subjects = {
        getattr(value, "subject_ref", None) for value in packet.subjects
    }
    subject_sites = {
        getattr(value, "site_ref", None) for value in packet.subjects
    }
    if not subjects or not subject_sites.issubset(coverage):
        raise ProductPublicationError("authority_identity_mismatch")
    risks = {
        getattr(value, "risk_ref", None) for value in packet.risks
    }
    events = {
        getattr(value, "event_ref", None) for value in packet.events
    }
    visits = {
        getattr(value, "visit_ref", None) for value in packet.visits
    }
    sources = {
        getattr(value, "locator_ref", None) for value in packet.sources
    }
    source_pairs = {
        (
            getattr(value, "source_revision_ref", None),
            getattr(value, "source_revision_content_hash", None),
        )
        for value in packet.sources
    }
    if any(
        getattr(value, "snapshot_ref", None) != identity.snapshot_ref
        for value in packet.sources
    ):
        raise ProductPublicationError("authority_identity_mismatch")
    for category in ("risks", "events", "visits"):
        for value in getattr(packet, category):
            if (
                getattr(value, "site_ref", None) not in coverage
                or getattr(value, "subject_ref", None) not in subjects
            ):
                raise ProductPublicationError("authority_identity_mismatch")
    for s4_packet in packet.s4_packets:
        risk = getattr(s4_packet, "risk_identity", None)
        journey = getattr(s4_packet, "journey_link", None)
        if (
            risk is None
            or risk.project_ref != identity.project_ref
            or risk.run_ref != identity.run_ref
            or risk.snapshot_ref != identity.snapshot_ref
            or risk.cutoff_ref != identity.cutoff_ref
            or risk.site_ref not in coverage
            or risk.subject_ref not in subjects
            or risk.risk_ref not in risks
            or journey is None
        ):
            raise ProductPublicationError("authority_identity_mismatch")
        if (
            getattr(journey, "deep_link_event_ref", None) is not None
            and journey.deep_link_event_ref not in events
        ) or (
            getattr(journey, "deep_link_visit_ref", None) is not None
            and journey.deep_link_visit_ref not in visits
        ) or (
            getattr(journey, "deep_link_source_locator_ref", None) is not None
            and journey.deep_link_source_locator_ref not in sources
        ):
            raise ProductPublicationError("authority_identity_mismatch")
        receipt = getattr(s4_packet, "authority_receipt", None)
        if receipt is None:
            raise ProductPublicationError("authority_identity_mismatch")
        for pair in getattr(receipt, "source_revision_content_pairs", ()):
            if (
                getattr(pair, "revision_id", None),
                getattr(pair, "content_hash", None),
            ) not in source_pairs:
                raise ProductPublicationError("authority_identity_mismatch")
    return packet
def _build_r5_publication_packet(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
    bridge: Any = None,
    product_packet_factory: Optional[Callable[[Any], Any]] = None,
):
    (
        packet_type,
        bridge_type,
        bridge_error_type,
        input_type,
        _,
    ) = _r5_publication_types()
    value = _publication_provider_value(
        provider, identity, attempts=attempts
    )
    if type(value) is packet_type:
        return _validate_r5_publication_packet(
            value, identity, packet_type=packet_type
        )
    if type(value) is not input_type:
        raise ProductPublicationError("authority_provider_invalid")
    factory = (
        product_packet_factory
        if product_packet_factory is not None
        else _publication_product_factory(provider)
    )
    authority_bridge = bridge
    if authority_bridge is None:
        try:
            authority_bridge = bridge_type(product_packet_factory=factory)
        except Exception as exc:
            raise ProductPublicationError(
                "authority_provider_invalid"
            ) from exc
    build = getattr(authority_bridge, "build", None)
    if not callable(build):
        raise ProductPublicationError("authority_provider_invalid")
    try:
        packet = build(value)
    except bridge_error_type as exc:
        code = str(getattr(exc, "code", "") or "")
        recoverable = code in {
            "S4_BUILD_FAILED",
            "S4_VALIDATION_FAILED",
            "PRODUCT_PACKET_ASSEMBLY_FAILED",
        }
        raise ProductPublicationError(
            "authority_provider_unavailable"
            if recoverable
            else "authority_identity_mismatch",
            recoverable=recoverable,
        ) from exc
    except Exception as exc:
        raise ProductPublicationError(
            "authority_provider_unavailable", recoverable=True
        ) from exc
    return _validate_r5_publication_packet(
        packet, identity, packet_type=packet_type
    )


def _capability_request_from_attempt(
    attempt: Mapping[str, Any],
    profile: Any,
) -> CapabilityRequest:
    try:
        request_json = attempt["request"]
        params = request_json["params"]
        versions_json = params["versions"]
        versions = InvocationVersions(**dict(versions_json))
        expected = params["expected_coverage"]
        request = CapabilityRequest.build(
            attempt_id=str(attempt["attempt_id"]),
            monitoring_run_id=str(attempt["run_id"]),
            node_id=str(attempt["node_id"]),
            manifest_revision=int(attempt["manifest_revision"]),
            profile=profile,
            versions=versions,
            payload=params["input"],
            expected_units=expected,
            continued_from=str(params.get("continued_from") or ""),
        )
    except Exception as exc:
        raise ProductPublicationError("receipt_gate_blocked") from exc
    if (
        request.request_hash != attempt.get("request_hash")
        or request.input_hash != attempt.get("input_hash")
        or request.profile_fingerprint != attempt.get("profile_fingerprint")
        or request.manifest_revision != int(attempt.get("manifest_revision", 0))
    ):
        raise ProductPublicationError("receipt_gate_blocked")
    return request


def _read_publication_gate(
    workspace: Path,
    run_id: str,
    *,
    entry: MonitoringRunEntry,
    harness_r1_profile: Any,
) -> dict[str, Any]:
    """Read and validate runtime, deterministic units, and final receipts."""

    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        raise ProductPublicationError("runtime_read_failed", recoverable=True)
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        run = store.get_run(run_id)
        revision = int(run.manifest_revision)
        if revision < 1:
            raise ProductPublicationError(
                "runtime_read_failed", recoverable=True
            )
        manifest = store.get_manifest(run_id, revision)
        if manifest is None:
            raise ProductPublicationError(
                "runtime_read_failed", recoverable=True
            )
        audit = store.verify_audit_chain()
        if (
            not isinstance(audit, tuple)
            or len(audit) != 3
            or audit[0] is not True
        ):
            raise ProductPublicationError("receipt_gate_blocked")
        rows = store.list_work_unit_runs(run_id, revision)
        units = tuple(manifest.work_units)
        row_by_id = {row.work_unit_id: row for row in rows}
        unit_ids = {unit.work_unit_id for unit in units}
        if (
            len(row_by_id) != len(rows)
            or set(row_by_id) != unit_ids
            or any(int(row.manifest_revision) != revision for row in rows)
        ):
            raise ProductPublicationError("runtime_read_failed", recoverable=True)
        node_types = {
            node.node_id: getattr(node.node_type, "value", node.node_type)
            for node in manifest.nodes
        }
        mandatory_units = tuple(unit for unit in units if unit.mandatory)
        deterministic_units = tuple(
            unit
            for unit in mandatory_units
            if node_types.get(unit.node_id) != NodeType.AI_CANDIDATE.value
        )
        ai_units = tuple(
            unit
            for unit in mandatory_units
            if node_types.get(unit.node_id) == NodeType.AI_CANDIDATE.value
        )
        success_statuses = {
            NodeStatus.PASSED,
            NodeStatus.REUSED,
            NodeStatus.SKIPPED,
            NodeStatus.NOT_APPLICABLE,
        }
        if any(row_by_id[unit.work_unit_id].status not in success_statuses for unit in deterministic_units):
            raise ProductPublicationError("deterministic_gate_blocked")
        receipt_ids: list[str] = []
        receipt_attempts: list[dict[str, Any]] = []
        profile_bridge = None
        if ai_units:
            try:
                from packages.medical_monitoring.runtime.harness_runtime import (
                    bridge_from_run_binding,
                    build_r6_prompt,
                    classify_r6_receipt,
                )
                profile_bridge = bridge_from_run_binding(
                    entry.run_binding_store,
                    run_id,
                    r1_profile=harness_r1_profile,
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
        for unit in ai_units:
            try:
                history = list_bound_capability_attempts(
                    store, run_id, revision, unit.work_unit_id
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
            if not history:
                raise ProductPublicationError("receipt_gate_blocked")
            latest = history[-1]
            attempt = latest.get("attempt")
            if (
                not isinstance(attempt, Mapping)
                or attempt.get("status") != "complete"
                or attempt.get("terminal") is not True
                or latest.get("manifest_revision") != revision
                or attempt.get("run_id") != run_id
                or attempt.get("manifest_revision") != revision
                or row_by_id[unit.work_unit_id].status is not NodeStatus.PASSED
            ):
                raise ProductPublicationError("receipt_gate_blocked")
            result = attempt.get("result")
            transport = result.get("transport_execution") if isinstance(result, Mapping) else None
            receipt = transport.get("raw_output") if isinstance(transport, Mapping) else None
            if not isinstance(receipt, Mapping):
                raise ProductPublicationError("receipt_gate_blocked")
            request = _capability_request_from_attempt(
                attempt, profile_bridge.r1_profile
            )
            expected_tokens = tuple(
                f"{coverage.scope}:{coverage.key}"
                for coverage in request.expected_units
            )
            try:
                prompt = build_r6_prompt(request.payload, expected_tokens)
                status, _, _, _ = classify_r6_receipt(
                    request, profile_bridge, receipt, prompt
                )
            except Exception as exc:
                raise ProductPublicationError("receipt_gate_blocked") from exc
            if status != "complete":
                raise ProductPublicationError("receipt_gate_blocked")
            receipt_id = str(receipt.get("invocation_id", "") or "")
            if not receipt_id or receipt_id in receipt_ids:
                raise ProductPublicationError("receipt_gate_blocked")
            receipt_ids.append(receipt_id)
            receipt_attempts.append(
                {
                    "attempt_id": str(attempt["attempt_id"]),
                    "work_unit_id": unit.work_unit_id,
                    "receipt": dict(receipt),
                }
            )
        identity = _publication_manifest_identity(manifest)
        return {
            "revision": revision,
            "manifest": manifest,
            "identity": identity,
            "digest": _runtime_manifest_digest(manifest),
            "mandatory_denominator": int(identity["mandatory_denominator"]),
            "receipt_ids": tuple(sorted(receipt_ids)),
            "receipt_attempts": tuple(receipt_attempts),
            "receipt_set_digest": lr.content_digest(sorted(receipt_ids)),
        }
    finally:
        if store is not None:
            store.close()


def _request_id(request: Request) -> str:
    supplied = str(request.headers.get("X-Request-ID", "") or "").strip()
    if supplied and len(supplied) <= 200 and all(
        char.isalnum() or char in "._:/-" for char in supplied
    ):
        return supplied
    return f"r7-request:{uuid4().hex}"


def _workspace_dir(runtime_dir: Path, canonical_project_id: str) -> Path:
    return Path(runtime_dir) / R7_WORKSPACE_ROOT_NAME / canonical_project_id


def _workspace_is_ready(workspace: Path) -> bool:
    return all(
        (workspace / database_name).is_file()
        for database_name in (PROFILE_DB_NAME, RUN_BINDING_DB_NAME)
    )


def _synthetic_setup_inputs(
    canonical_project_id: str,
) -> tuple[tuple[rs.DataSnapshot, ...], tuple[rs.PublishedBaseline, ...]]:
    """Return deterministic, project-isolated inputs for the product surface."""
    prior_rows = (
        {
            "canonical_key": "site-01/S-001/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-001",
            "value": 42,
        },
        {
            "canonical_key": "site-01/S-002/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-002",
            "value": 35,
        },
    )
    current_rows = (
        {
            "canonical_key": "site-01/S-001/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-001",
            "value": 47,
        },
        {
            "canonical_key": "site-01/S-002/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-002",
            "value": 35,
        },
        {
            "canonical_key": "site-02/S-003/lab-alt",
            "site_ref": "site-02",
            "subject_ref": "S-003",
            "value": 29,
        },
    )
    prior = rs.DataSnapshot(
        snapshot_ref=f"{canonical_project_id}:synthetic:daily-prior",
        project_id=canonical_project_id,
        data_cutoff="2026-08-27",
        rows=prior_rows,
        key_fields=("canonical_key",),
        imported_at="2026-08-27T09:00:00Z",
        scope_description="上一批完整合成数据",
        source_revision_id="synthetic-source-prior",
    )
    current = rs.DataSnapshot(
        snapshot_ref=f"{canonical_project_id}:synthetic:current",
        project_id=canonical_project_id,
        data_cutoff="2026-08-28",
        rows=current_rows,
        key_fields=("canonical_key",),
        imported_at="2026-08-28T09:00:00Z",
        scope_description="当前完整合成数据",
        source_revision_id="synthetic-source-current",
    )
    baselines = (
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_DAILY,
            snapshot_ref=prior.snapshot_ref,
            data_cutoff=prior.data_cutoff,
            run_id=f"{canonical_project_id}:synthetic:daily-run",
            published=True,
            published_at="2026-08-27T12:00:00Z",
            scope_description="上一轮已发布日常监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_PRE_LOCK,
            snapshot_ref=f"{canonical_project_id}:synthetic:pre-lock-prior",
            data_cutoff="2026-08-27",
            run_id=f"{canonical_project_id}:synthetic:pre-lock-run",
            published=True,
            published_at="2026-08-27T13:00:00Z",
            scope_description="上一轮已发布锁库前监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_PRE_LOCK,
            snapshot_ref=f"{canonical_project_id}:synthetic:pre-lock-older",
            data_cutoff="2026-08-26",
            run_id=f"{canonical_project_id}:synthetic:pre-lock-older-run",
            published=True,
            published_at="2026-08-26T13:00:00Z",
            scope_description="更早一轮已发布锁库前监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_POST_LOCK_PRE_CFDI,
            snapshot_ref=f"{canonical_project_id}:synthetic:post-lock-fixed",
            data_cutoff="2026-08-27",
            run_id=f"{canonical_project_id}:synthetic:post-lock-run",
            published=True,
            published_at="2026-08-27T14:00:00Z",
            scope_description="固定总量核查前结果",
            fixed_total=True,
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
    )
    return (prior, current), baselines


def create_medical_monitoring_r7_product_router(
    *,
    runtime_dir: Union[str, Path],
    project_resolver: Callable[[str], str] = lambda project_id: project_id,
    principal_resolver: Optional[
        Callable[[Request], MonitoringAuthenticatedPrincipal | None]
    ] = None,
    require_server_principal: bool = True,
    maintenance_wait_seconds: float = DEFAULT_WAIT_SECONDS,
    harness_runtime_factory: Optional[Callable[..., Any]] = None,
    harness_adapter: Any = None,
    harness_catalog: Any = None,
    harness_r1_profile: Any = None,
    authority_provider: Any = None,
    r5_authority_provider: Any = None,
    publication_authority_provider: Any = None,
    r5_publication_provider: Any = None,
    r5_authority_bridge: Any = None,
    publication_authority_bridge: Any = None,
    r5_product_packet_factory: Optional[Callable[[Any], Any]] = None,
    r6_output_provider: Any = None,
    r6_publication_provider: Any = None,
    mode_output_provider: Any = None,
    r6_mode_output_provider: Any = None,
    continuity_bridge: Any = None,
    audit_ledger_factory: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    """Create the project-scoped R7 product router; no workspace I/O here."""
    # Publication never synthesizes authority.  A caller must inject one
    # explicit R5 publication provider (or the already constructed bridge
    # input); the aliases preserve naming compatibility with R5 routes.
    publication_provider = next(
        (
            value
            for value in (
                publication_authority_provider,
                r5_publication_provider,
                r5_authority_provider,
                authority_provider,
            )
            if value is not None
        ),
        None,
    )
    publication_bridge = next(
        (
            value
            for value in (r5_authority_bridge, publication_authority_bridge)
            if value is not None
        ),
        None,
    )
    r6_provider = next(
        (
            value
            for value in (
                r6_output_provider,
                r6_publication_provider,
                mode_output_provider,
                r6_mode_output_provider,
            )
            if value is not None
        ),
        None,
    )

    root = Path(runtime_dir)
    router = APIRouter(prefix=R7_PRODUCT_PREFIX, tags=["medical-monitoring-r7-product"])
    risk_registries: dict[str, rs.RiskRuleRegistry] = {}
    risk_registry_lock = threading.RLock()
    backup_runtime_root = root / R7_WORKSPACE_ROOT_NAME

    @router.on_event("startup")
    def recover_r7_projects_on_startup() -> None:
        """Cold-scan canonical projects through the shared 09C coordinator."""

        try:
            project_dirs = sorted(
                path
                for path in backup_runtime_root.iterdir()
                if path.is_dir()
                and not path.is_symlink()
                and not path.name.startswith(".")
            )
        except (FileNotFoundError, OSError):
            return
        for workspace in project_dirs:
            try:
                coordinator = RecoveryCoordinator(
                    backup_runtime_root,
                    workspace.name,
                    project_dir=workspace,
                    wait_seconds=maintenance_wait_seconds,
                    audit_ledger_factory=audit_ledger_factory,
                )
                try:
                    coordinator.startup_recovery_scan()
                finally:
                    coordinator.close()
            except Exception:
                # The durable state remains available to project-open or the
                # explicit same-key path; one project cannot block startup.
                continue

    def acquire_product_write_gate(canonical_project_id: str):
        try:
            gate = ProjectMaintenanceGate(
                backup_runtime_root,
                canonical_project_id,
                wait_seconds=maintenance_wait_seconds,
            )
            return gate.acquire(exclusive=False)
        except MaintenanceGateError as exc:
            raise pb.ProjectBackupError(exc.code, exc.message) from exc

    def close_cached_risk_registry(canonical_project_id: str) -> None:
        registry: Optional[rs.RiskRuleRegistry]
        with risk_registry_lock:
            registry = risk_registries.pop(canonical_project_id, None)
            if registry is not None:
                registry.close()

    def operation_record(
        canonical_project_id: str,
        operation_id: str,
        expected_kind: str,
    ) -> pb.OperationRecord:
        if (
            not isinstance(operation_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]+", operation_id) is None
        ):
            raise pb.ProjectBackupError("operation_not_found")
        ledger_path = backup_runtime_root / pb.OPERATIONS_DB_NAME
        if not ledger_path.is_file():
            raise pb.ProjectBackupError("operation_not_found")
        ledger: Optional[pb.OperationLedger] = None
        try:
            ledger = pb.OperationLedger(ledger_path)
            record = ledger.get(operation_id)
        finally:
            if ledger is not None:
                ledger.close()
        if (
            record.canonical_project_id != canonical_project_id
            or record.operation_kind != expected_kind
        ):
            raise pb.ProjectBackupError("operation_not_found")
        return record

    def backup_source(
        canonical_project_id: str,
        operation_id: str,
    ) -> tuple[pb.OperationRecord, Path]:
        record = operation_record(
            canonical_project_id, operation_id, pb.OP_BACKUP
        )
        package_name = record.package_path
        if not package_name:
            raise pb.ProjectBackupError("operation_not_found")
        package_root = (
            backup_runtime_root / pb.BACKUP_PUBLICATION_DIR_NAME
        ).resolve()
        package_path = Path(package_name)
        if (
            not package_path.is_absolute()
            or package_path.is_symlink()
            or package_path.suffix != pb.BACKUP_SUFFIX
        ):
            raise pb.ProjectBackupError("operation_not_found")
        try:
            package_path = package_path.resolve()
            package_path.relative_to(package_root)
        except (OSError, ValueError):
            raise pb.ProjectBackupError("operation_not_found")
        if not package_path.is_file():
            raise pb.ProjectBackupError("operation_not_found")
        return record, package_path

    def requested_operation_id(
        backup_operation_id: Optional[str],
        operation_id: Optional[str],
    ) -> Optional[str]:
        if (
            backup_operation_id is not None
            and operation_id is not None
            and backup_operation_id != operation_id
        ):
            raise pb.ProjectBackupError("backup_operation_conflict")
        return backup_operation_id or operation_id

    def operation_key(
        request: Request,
        supplied: Optional[str],
        prefix: str,
    ) -> str:
        header = str(request.headers.get("X-Idempotency-Key", "") or "").strip()
        return supplied or header or f"{prefix}-{_request_id(request)}"

    def reserve_operation(
        operation_kind: str,
        canonical_project_id: str,
        idempotency_key: str,
        *,
        package_id: Optional[str] = None,
        initial_status: Optional[str] = None,
    ) -> pb.OperationRecord:
        ledger: Optional[pb.OperationLedger] = None
        try:
            ledger = pb.OperationLedger(
                backup_runtime_root / pb.OPERATIONS_DB_NAME
            )
            return ledger.create_or_replay(
                operation_kind,
                idempotency_key,
                canonical_project_id,
                package_id=package_id,
                initial_status=initial_status,
            )
        finally:
            if ledger is not None:
                ledger.close()

    def product_worker_key(
        operation_kind: str,
        canonical_project_id: str,
        operation_id: str,
    ) -> tuple[str, str, str, str]:
        return (
            str(backup_runtime_root.resolve()),
            canonical_project_id,
            operation_kind,
            operation_id,
        )

    def start_worker_once(
        operation_kind: str,
        canonical_project_id: str,
        operation_id: str,
        target: Callable[[], None],
    ) -> None:
        worker_key = product_worker_key(
            operation_kind, canonical_project_id, operation_id
        )

        def run_and_forget() -> None:
            try:
                target()
            finally:
                with _PRODUCT_BACKUP_WORKERS_LOCK:
                    if (
                        _PRODUCT_BACKUP_WORKERS.get(worker_key)
                        is threading.current_thread()
                    ):
                        _PRODUCT_BACKUP_WORKERS.pop(worker_key, None)

        with _PRODUCT_BACKUP_WORKERS_LOCK:
            existing = _PRODUCT_BACKUP_WORKERS.get(worker_key)
            if existing is not None and existing.is_alive():
                return
            worker = threading.Thread(
                target=run_and_forget,
                name=f"r7-{operation_kind}-{operation_id[:12]}",
                daemon=True,
            )
            _PRODUCT_BACKUP_WORKERS[worker_key] = worker
            try:
                worker.start()
            except BaseException:
                if _PRODUCT_BACKUP_WORKERS.get(worker_key) is worker:
                    _PRODUCT_BACKUP_WORKERS.pop(worker_key, None)
                raise

    def mark_worker_failed(
        operation_id: str,
        exc: Exception,
        *,
        canonical_project_id: Optional[str] = None,
        operation_kind: Optional[str] = None,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        ledger: Optional[pb.OperationLedger] = None
        should_classify = False
        observed_phase = pb.STATUS_FAILED
        try:
            ledger = pb.OperationLedger(
                backup_runtime_root / pb.OPERATIONS_DB_NAME
            )
            record = ledger.get(operation_id)
            terminal = (
                _PRODUCT_BACKUP_TERMINAL
                | _PRODUCT_RESTORE_TERMINAL
                | {pb.STATUS_KEPT_CURRENT}
            )
            if record.status in terminal:
                # A late verifier/callback failure must still leave an
                # auditable recovery classification; terminal status alone
                # does not close the boundary.
                observed_phase = record.status
                should_classify = boundary_receipt is not None
            else:
                failure = (
                    exc
                    if isinstance(exc, pb.ProjectBackupError)
                    else pb.ProjectBackupError("sqlite_integrity_failed")
                )
                ledger.update(
                    operation_id,
                    status=pb.STATUS_FAILED,
                    current_step="操作未完成",
                    terminal_outcome=pb.STATUS_FAILED,
                    error_code=failure.code,
                    error_message=failure.message,
                )
                should_classify = boundary_receipt is not None
        except Exception:
            pass
        finally:
            if ledger is not None:
                ledger.close()
        if should_classify:
            try:
                classify_product_recovery(
                    canonical_project_id or "",
                    operation_id,
                    operation_kind=operation_kind or "",
                    observed_durable_phase=observed_phase,
                    classification="需重新恢复",
                    request=request,
                    principal=principal,
                )
            except Exception:
                pass

    def start_backup_worker(
        canonical_project_id: str,
        operation_id: str,
        idempotency_key: str,
        *,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        def run() -> None:
            manager: Optional[pb.ProjectBackupManager] = None
            try:
                manager = pb.ProjectBackupManager(
                    backup_runtime_root,
                    canonical_project_id,
                    wait_seconds=maintenance_wait_seconds,
                )
                manager.backup(
                    idempotency_key,
                    reserved_operation_id=operation_id,
                )
                if boundary_receipt is not None and request is not None:
                    manager.ledger.close()
                    manager = None
                    final_record = operation_record(
                        canonical_project_id,
                        operation_id,
                        pb.OP_BACKUP,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        operation_update=operation_projection_for(final_record),
                    )
                    verification_result = boundary_verification_result(
                        canonical_project_id,
                        boundary_receipt,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        verification_result=verification_result,
                        commit=False,
                    )
            except Exception as exc:
                mark_worker_failed(
                    operation_id,
                    exc,
                    canonical_project_id=canonical_project_id,
                    operation_kind=pb.OP_BACKUP,
                    boundary_receipt=boundary_receipt,
                    request=request,
                    principal=principal,
                )
            finally:
                if manager is not None:
                    manager.ledger.close()

        start_worker_once(
            pb.OP_BACKUP,
            canonical_project_id,
            operation_id,
            run,
        )

    def start_restore_worker(
        canonical_project_id: str,
        operation_id: str,
        idempotency_key: str,
        package_path: Path,
        preflight_id: Optional[str],
        confirmation: bool,
        *,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        def run() -> None:
            manager: Optional[pb.ProjectBackupManager] = None
            try:
                manager = pb.ProjectBackupManager(
                    backup_runtime_root,
                    canonical_project_id,
                    wait_seconds=maintenance_wait_seconds,
                )
                preflight_result: Optional[pb.PreflightResult] = None
                if preflight_id is not None:
                    preflight_record = operation_record(
                        canonical_project_id,
                        preflight_id,
                        pb.OP_PREFLIGHT,
                    )
                    if (
                        preflight_record.status
                        != pb.STATUS_READY_FOR_CONFIRMATION
                    ):
                        raise pb.ProjectBackupError(
                            "backup_operation_conflict"
                        )
                    preflight_result = manager.preflight(
                        package_path,
                        preflight_record.idempotency_key,
                    )
                close_cached_risk_registry(canonical_project_id)
                manager.restore(
                    package_path,
                    idempotency_key,
                    confirmation=confirmation,
                    preflight_result=preflight_result,
                    reserved_operation_id=operation_id,
                )
                if boundary_receipt is not None and request is not None:
                    manager.ledger.close()
                    manager = None
                    final_record = operation_record(
                        canonical_project_id,
                        operation_id,
                        pb.OP_RESTORE,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        operation_update=operation_projection_for(final_record),
                    )
                    verification_result = boundary_verification_result(
                        canonical_project_id,
                        boundary_receipt,
                    )
                    verified_event = finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        verification_result=verification_result,
                        commit=False,
                    )
                    release_product_rollback(
                        canonical_project_id,
                        boundary_receipt,
                        final_record,
                        verified_event=verified_event,
                        verification_result=verification_result,
                    )
            except Exception as exc:
                mark_worker_failed(
                    operation_id,
                    exc,
                    canonical_project_id=canonical_project_id,
                    operation_kind=pb.OP_RESTORE,
                    boundary_receipt=boundary_receipt,
                    request=request,
                    principal=principal,
                )
            finally:
                if manager is not None:
                    manager.ledger.close()

        start_worker_once(
            pb.OP_RESTORE,
            canonical_project_id,
            operation_id,
            run,
        )

    def restore_should_start(
        record: pb.OperationRecord,
        confirmation: bool,
    ) -> bool:
        if record.status in _PRODUCT_RESTORE_TERMINAL:
            return False
        if record.status == pb.STATUS_KEPT_CURRENT:
            return bool(confirmation)
        if record.status == pb.STATUS_FAILED:
            return record.error_code == "project_busy_retry_later"
        return True


    def setup_registry(
        canonical_project_id: str,
    ) -> Union[rs.RiskRuleRegistry, JSONResponse]:
        workspace = _workspace_dir(root, canonical_project_id)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        with risk_registry_lock:
            registry = risk_registries.get(canonical_project_id)
        if registry is not None:
            return registry
        try:
            write_permit = acquire_product_write_gate(canonical_project_id)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            with risk_registry_lock:
                registry = risk_registries.get(canonical_project_id)
                if registry is None:
                    registry = rs.RiskRuleRegistry(
                        workspace / R7_RISK_RULE_DB_NAME
                    )
                    risk_registries[canonical_project_id] = registry
                return registry
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    def setup_catalog(
        canonical_project_id: str,
    ) -> Union[rs.RunSetupCatalog, JSONResponse]:
        registry = setup_registry(canonical_project_id)
        if isinstance(registry, JSONResponse):
            return registry
        snapshots, baselines = _synthetic_setup_inputs(canonical_project_id)
        return rs.RunSetupCatalog(
            project_id=canonical_project_id,
            snapshots=snapshots,
            published_baselines=baselines,
            risk_rule_registry=registry,
        )

    def open_launch_registry(
        canonical_project_id: str,
    ) -> Union[lr.LaunchRegistry, JSONResponse]:
        workspace = _workspace_dir(root, canonical_project_id)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(canonical_project_id)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            return lr.LaunchRegistry(
                workspace / lr.LAUNCH_REGISTRY_DB_NAME,
                project_id=canonical_project_id,
            )
        except Exception as exc:
            return _launch_error_response(exc)
        finally:
            write_permit.release()

    def resolve_launch_inputs(
        canonical_project_id: str,
        parsed: ProductPrepareAndStartRequest,
    ) -> Union[
        tuple[
            rs.DataSnapshot,
            Optional[rs.PublishedBaseline],
            tuple[rs.RiskRuleRevision, ...],
            rs.WorkUnitManifest,
        ],
        JSONResponse,
    ]:
        catalog = setup_catalog(canonical_project_id)
        if isinstance(catalog, JSONResponse):
            return catalog
        current = catalog.snapshot_for_token(
            canonical_project_id,
            parsed.current_snapshot_token,
        )
        if parsed.current_snapshot_token != current.snapshot_token:
            raise rs.RunSetupError("invalid_snapshot")

        baseline: Optional[rs.PublishedBaseline] = None
        if parsed.baseline_token is not None:
            if parsed.mode == rs.MODE_DAILY and parsed.execution_basis == rs.BASIS_FULL:
                raise rs.RunSetupError("invalid_baseline")
            if parsed.mode == rs.MODE_POST_LOCK_PRE_CFDI:
                raise rs.RunSetupError("invalid_baseline")
            baseline = catalog.baseline_for_token(
                canonical_project_id,
                parsed.mode,
                parsed.baseline_token,
            )
            if parsed.baseline_token != baseline.baseline_token:
                raise rs.RunSetupError("invalid_baseline")
        elif (
            parsed.mode == rs.MODE_DAILY
            and parsed.execution_basis == rs.BASIS_INCREMENTAL
        ):
            raise rs.RunSetupError("baseline_not_published")

        revisions: list[rs.RiskRuleRevision] = []
        for token in sorted(set(parsed.risk_rule_tokens)):
            revision = catalog.risk_rule_registry.resolve_public_token(
                canonical_project_id,
                token,
            )
            if not revision.selectable:
                raise rs.RunSetupError("invalid_rule_revision")
            revisions.append(revision)

        diff: Optional[rs.CanonicalKeyedDiff] = None
        if baseline is not None:
            key_fields = current.key_fields or baseline.key_fields or None
            diff = rs.canonical_keyed_diff(
                current.rows,
                baseline.rows,
                key_fields=key_fields,
            )
        manifest = rs.generate_work_units(
            parsed.mode,
            parsed.execution_basis,
            current_snapshot_token=parsed.current_snapshot_token,
            prior_baseline_token=parsed.baseline_token,
            diff=diff,
            rule_revisions=revisions,
        )
        return current, baseline, tuple(revisions), manifest

    def progress_adapter(
        workspace: Path, entry: MonitoringRunEntry, canonical_id: str
    ) -> RuntimeProgressAdapter:
        return RuntimeProgressAdapter(
            workspace,
            binding_store=entry.run_binding_store,
            canonical_project_id=canonical_id,
            harness_runtime_factory=harness_runtime_factory,
            harness_adapter=harness_adapter,
            harness_catalog=harness_catalog,
            harness_r1_profile=harness_r1_profile,
        )

    def resolve_project(project_id: str) -> Union[str, JSONResponse]:
        text = str(project_id or "")
        if not text.strip() or text != text.strip():
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        try:
            canonical = project_resolver(text)
        except Exception:
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        cleaned = str(canonical or "").strip()
        if not cleaned or cleaned != str(canonical):
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        return cleaned

    def mutable_project_error(
        canonical_project_id: str,
        *,
        allow_uninitialized: bool = False,
    ) -> Optional[JSONResponse]:
        """Reject legacy/unknown projects before any mutable constructor."""
        workspace = _workspace_dir(root, canonical_project_id)
        runtime_path = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        guarded_paths = runtime_path.exists()
        member_paths = (
            (workspace / PROFILE_DB_NAME, "profile_store"),
            (workspace / RUN_BINDING_DB_NAME, "run_binding"),
            (workspace / lr.LAUNCH_REGISTRY_DB_NAME, "launch_registry"),
            (workspace / R7_RISK_RULE_DB_NAME, "risk_rules"),
        )
        if not guarded_paths:
            for path, member in member_paths:
                if not path.exists():
                    continue
                report = inspect_member(path, member)
                if report.classification is not SchemaClassification.CURRENT:
                    code = (
                        "project_read_only"
                        if report.classification is SchemaClassification.LEGACY
                        else "project_open_blocked"
                    )
                    compatibility = ProjectCompatibilityError(code)
                    return _error_response(
                        _status_for(code),
                        code,
                        compatibility.message,
                    )
        if not workspace.exists() or not guarded_paths:
            # A missing runtime is the normal pre-bootstrap state: the
            # mutable entry may establish profile/binding stores explicitly.
            return None
        try:
            require_current_project(workspace)
        except ProjectCompatibilityError as exc:
            return _error_response(_status_for(exc.code), exc.code, exc.message)
        return None

    def open_project_inspection(
        canonical_project_id: str,
    ) -> Any:
        """Inspect first, then share 09A/09B recovery coordination."""
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
        )
        try:
            return coordinator.open_project()
        finally:
            coordinator.close()

    def verification_context_hashes(
        canonical_project_id: str,
        request: Request,
        principal: Any,
        *,
        action: MonitoringAction = MonitoringAction.READ_AI_RUN,
    ) -> tuple[str, str]:
        principal_hash = str(getattr(principal, "identity_hash", "") or "")
        # The authorization decision is a stable policy projection.  Request
        # ids identify transport attempts, not a different authorization
        # decision; excluding them preserves same-key boundary replay.
        decision = {
            "action": action.value,
            "project_id": canonical_project_id,
        }
        decision_hash = hashlib.sha256(
            json.dumps(
                decision,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return principal_hash, decision_hash

    def verification_projection(
        canonical_project_id: str,
        request: Request,
        principal: Any,
    ) -> dict[str, str]:
        principal_hash, decision_hash = verification_context_hashes(
            canonical_project_id,
            request,
            principal,
        )
        verifier = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            return verifier.verify().as_public_dict()
        finally:
            verifier.close()

    def operation_projection_for(record: Any) -> dict[str, Any]:
        """Select only mutable root-operation fields for atomic audit append."""

        fields: dict[str, Any] = {}
        for name in (
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
        ):
            if hasattr(record, name):
                fields[name] = getattr(record, name)
        if hasattr(record, "payload"):
            payload = getattr(record, "payload")
            if isinstance(payload, Mapping):
                fields["payload"] = dict(payload)
        return fields


    def begin_product_boundary(
        canonical_project_id: str,
        operation_ref: str,
        *,
        operation_kind: str,
        expected_state: str,
        request: Request,
        principal: Any,
    ) -> Any:
        principal_hash, decision_hash = verification_context_hashes(
            canonical_project_id,
            request,
            principal,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        snapshot = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
        )
        try:
            before_digest = snapshot.snapshot_fingerprint()
        finally:
            snapshot.close()
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            boundary_token = hashlib.sha256(
                f"r7-boundary:{operation_kind}:{operation_ref}:{expected_state}".encode("utf-8")
            ).hexdigest()
            return coordinator.begin_boundary(
                operation_ref,
                operation_kind=operation_kind,
                expected_state=expected_state,
                before_digest=before_digest,
                boundary_token=boundary_token,
            )
        finally:
            coordinator.close()

    def finish_product_boundary(
        canonical_project_id: str,
        receipt: Any,
        *,
        observed_durable_phase: str,
        request: Request,
        principal: Any,
        verification_result: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
        commit: bool = True,
    ) -> Any:
        receipt_principal_hash = str(
            getattr(receipt, "principal_snapshot_hash", "") or ""
        )
        receipt_decision_hash = str(
            getattr(receipt, "authorization_decision_hash", "") or ""
        )
        if receipt_principal_hash and receipt_decision_hash:
            principal_hash, decision_hash = (
                receipt_principal_hash,
                receipt_decision_hash,
            )
        else:
            principal_hash, decision_hash = verification_context_hashes(
                canonical_project_id,
                request,
                principal,
                action=MonitoringAction.ADMINISTER_RUNTIME,
            )
        snapshot = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
        )
        try:
            after_digest = snapshot.snapshot_fingerprint()
        finally:
            snapshot.close()
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        verified_event: Any = None
        try:
            if commit:
                coordinator.mark_committed(
                    receipt,
                    observed_durable_phase=observed_durable_phase,
                    after_digest=after_digest,
                    operation_update=operation_update,
                )
            if verification_result is not None:
                verified_event = coordinator.mark_verified(
                    receipt,
                    verifier_outcome=verification_result,
                    after_digest=after_digest,
                )
        finally:
            coordinator.close()
        return verified_event

    def boundary_verification_result(
        canonical_project_id: str,
        receipt: Any,
    ) -> str:
        verifier = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=str(
                getattr(receipt, "principal_snapshot_hash", "") or ""
            ),
            authorization_decision_hash=str(
                getattr(receipt, "authorization_decision_hash", "") or ""
            ),
        )
        try:
            return verifier.verify().result
        finally:
            verifier.close()

    def rollback_evidence_digest(path: Path) -> str:
        digest = hashlib.sha256()
        if path.is_symlink() or not path.is_dir():
            raise OSError("rollback_evidence_unreadable")
        for entry in sorted(
            path.rglob("*"),
            key=lambda candidate: candidate.relative_to(path).as_posix(),
        ):
            relative = entry.relative_to(path).as_posix().encode("utf-8")
            if entry.is_symlink():
                digest.update(b"symlink\0" + relative)
            elif entry.is_dir():
                digest.update(b"directory\0" + relative)
            elif entry.is_file():
                digest.update(b"file\0" + relative + b"\0")
                with entry.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            else:
                raise OSError("rollback_evidence_unreadable")
        return digest.hexdigest()

    def release_product_rollback(
        canonical_project_id: str,
        receipt: Any,
        final_record: Any,
        *,
        verified_event: Any,
        verification_result: str,
    ) -> bool:
        if verification_result != RESULT_RECORD_COMPLETE:
            return False
        rollback_raw = getattr(final_record, "rollback_path", None)
        if not rollback_raw:
            return False
        rollback_path = Path(str(rollback_raw))
        if not rollback_path.is_absolute():
            rollback_path = backup_runtime_root / rollback_path
        runtime_root_resolved = backup_runtime_root.resolve()
        try:
            rollback_path.resolve().relative_to(runtime_root_resolved)
            rollback_in_scope = True
        except (OSError, ValueError):
            rollback_in_scope = False
        if rollback_in_scope:
            try:
                rollback_digest = rollback_evidence_digest(rollback_path)
            except OSError:
                rollback_digest = hashlib.sha256(
                    ("unreadable:" + str(rollback_raw)).encode("utf-8")
                ).hexdigest()
        else:
            rollback_digest = hashlib.sha256(
                ("out-of-scope:" + str(rollback_raw)).encode("utf-8")
            ).hexdigest()
        event_id = (
            verified_event.get("event_id")
            if isinstance(verified_event, Mapping)
            else getattr(verified_event, "event_id", None)
        )
        if not event_id:
            raise ProjectVerificationError("boundary_verified_event_missing")

        def remove_rollback() -> None:
            resolved = rollback_path.resolve()
            resolved.relative_to(runtime_root_resolved)
            if rollback_path.is_symlink() or not rollback_path.is_dir():
                raise OSError("rollback_evidence_unreadable")
            shutil.rmtree(rollback_path)

        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=str(
                getattr(receipt, "principal_snapshot_hash", "") or ""
            ),
            authorization_decision_hash=str(
                getattr(receipt, "authorization_decision_hash", "") or ""
            ),
        )
        try:
            return coordinator.release_rollback_evidence(
                receipt.operation_id,
                verified_event_id=str(event_id),
                rollback_digest=rollback_digest,
                release=remove_rollback,
                operation_kind=str(getattr(receipt, "operation_kind", "") or ""),
                operation_update={"rollback_path": ""},
            )
        finally:
            coordinator.close()

    def classify_product_recovery(
        canonical_project_id: str,
        operation_ref: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        classification: str,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        principal_hash = ""
        decision_hash = ""
        if request is not None:
            principal_hash, decision_hash = verification_context_hashes(
                canonical_project_id,
                request,
                principal,
                action=MonitoringAction.ADMINISTER_RUNTIME,
            )
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            coordinator.classify_recovery(
                operation_ref,
                operation_kind=operation_kind,
                observed_durable_phase=observed_durable_phase,
                classification=classification,
            )
        finally:
            coordinator.close()

    def migration_records(
        canonical_project_id: str,
    ) -> tuple[Any, ...]:
        ledger_path = backup_runtime_root / pb.OPERATIONS_DB_NAME
        if not ledger_path.is_file():
            raise MigrationError("migration_operation_not_found")
        ledger: Optional[MigrationOperationLedger] = None
        try:
            ledger = MigrationOperationLedger(ledger_path, initialize=False)
            return tuple(ledger.list_for_project(canonical_project_id))
        finally:
            if ledger is not None:
                ledger.close()

    def migration_record(
        canonical_project_id: str,
        operation_id: str,
    ) -> Any:
        if (
            not isinstance(operation_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]+", operation_id) is None
        ):
            raise MigrationError("migration_operation_not_found")
        for record in migration_records(canonical_project_id):
            if record.operation_id == operation_id:
                return record
        raise MigrationError("migration_operation_not_found")

    def migration_projection(record: Any) -> dict[str, Any]:
        if record.status in TERMINAL_STATES:
            return upgrade_result_from_state(record.status).as_dict()
        return upgrade_progress_from_operation(record).as_dict()

    def blocked_project_open_projection() -> dict[str, Any]:
        return ProjectOpenDTO(
            state="blocked",
            open_mode=OPEN_MODE_BLOCKED,
            data_coverage=DATA_COVERAGE_INCOMPLETE,
            can_view=False,
            can_edit=False,
            message="暂时无法安全打开此项目，请保留原项目并联系支持。",
            next_action="关闭项目或联系支持",
        ).as_dict()

    def open_legacy_view(
        canonical_project_id: str,
    ) -> Optional[Union[ReadOnlyProjectView, _BlockedLegacyView]]:
        """Return the only readable handle permitted for a legacy project."""
        workspace = _workspace_dir(root, canonical_project_id)
        inspection = inspect_project_schema(workspace)
        if inspection.classification is not SchemaClassification.LEGACY:
            return None
        runner = MigrationRunner(
            backup_runtime_root,
            canonical_project_id,
            project_dir=workspace,
            wait_seconds=maintenance_wait_seconds,
        )
        try:
            # Read routes must apply the same cross-member completeness oracle
            # as project-open; structural legacy status alone is insufficient.
            runner._ensure_complete_legacy(inspection)
        except MigrationError:
            return _BlockedLegacyView()
        finally:
            runner.close()
        try:
            return open_read_only_project_view(workspace, inspection=inspection)
        except ProjectCompatibilityError:
            return _BlockedLegacyView()

    def legacy_setup_projection(
        canonical_project_id: str,
    ) -> Optional[dict[str, Any]]:
        """Build setup options without creating a legacy risk database."""
        view = open_legacy_view(canonical_project_id)
        if view is None:
            return None
        try:
            rules = [
                _legacy_risk_projection(row)
                for row in view.list_risk_rules()
            ]
        finally:
            view.close()
        snapshots, baselines = _synthetic_setup_inputs(canonical_project_id)
        memory_registry = rs.RiskRuleRegistry()
        catalog = rs.RunSetupCatalog(
            project_id=canonical_project_id,
            snapshots=snapshots,
            published_baselines=baselines,
            risk_rule_registry=memory_registry,
        )
        try:
            options = catalog.get_options(canonical_project_id)
            body = options.public_projection()
        finally:
            catalog.close()
        body["rule_revisions"] = rules
        return _setup_projection(body)


    def authorize(
        request: Request,
        *,
        project_id: str,
        action: MonitoringAction,
    ) -> Union[MonitoringAuthenticatedPrincipal, None, JSONResponse]:
        if not require_server_principal:
            # Explicit offline TestClient harness only; production host keeps True.
            return None
        if principal_resolver is None:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        try:
            principal = principal_resolver(request)
        except Exception:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        if not isinstance(principal, MonitoringAuthenticatedPrincipal):
            return _error_response(
                503,
                "principal_required",
                _AUTH_MESSAGES["principal_required"],
            )
        try:
            route_context = build_monitoring_runtime_route_context(
                principal,
                request_id=_request_id(request),
                route_project_id=project_id,
                tenant_id=principal.tenant_id,
                target_scope="trial",
                action=action,
            )
            decision = authorize_monitoring_action(
                route_context.principal.to_monitoring_principal(
                    now=route_context.validated_at,
                ),
                route_context.request,
            )
        except MonitoringRuntimePrincipalDenied:
            return _error_response(
                403, "principal_denied", _AUTH_MESSAGES["principal_denied"]
            )
        except (MonitoringRuntimeRouteContextError, ValueError):
            return _error_response(
                403,
                "authorization_invalid",
                _AUTH_MESSAGES["authorization_invalid"],
            )
        if not decision.allowed:
            return _error_response(
                403, "not_permitted", _AUTH_MESSAGES["not_permitted"]
            )
        return principal

    async def _read_json_object(request: Request) -> Union[dict[str, Any], JSONResponse]:
        raw = await request.body()
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        return payload

    def _validated_layer_scope(
        *,
        layer_kind: str,
        scope_key: str,
        canonical_project_id: str,
    ) -> Union[str, JSONResponse]:
        if layer_kind not in _LAYER_KINDS:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if (
            not isinstance(scope_key, str)
            or not scope_key.strip()
            or scope_key != scope_key.strip()
        ):
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_GLOBAL_DEFAULT and scope_key != ps.GLOBAL_SCOPE_KEY:
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_PROJECT:
            resolved_scope = resolve_project(scope_key)
            if (
                isinstance(resolved_scope, JSONResponse)
                or resolved_scope != canonical_project_id
            ):
                return _error_response(
                    422,
                    "empty_or_illegal_scope_key",
                    chinese_message_for("empty_or_illegal_scope_key"),
                )
            return canonical_project_id
        return scope_key

    def _auto_scopes(
        entry: MonitoringRunEntry,
        *,
        canonical_project_id: str,
        run_id: str,
        capability_scope_key: str,
    ) -> dict[str, str]:
        project_scope = ""
        if (
            entry.profile_store.latest_revision(ps.LAYER_PROJECT, canonical_project_id)
            is not None
        ):
            project_scope = canonical_project_id
        run_scope = ""
        if entry.profile_store.latest_revision(ps.LAYER_RUN_OVERRIDE, run_id) is not None:
            run_scope = run_id
        return {
            "capability_scope_key": capability_scope_key or "",
            "project_scope_key": project_scope,
            "run_override_scope_key": run_scope,
        }

    def _open_entry(
        workspace: Path,
        *,
        allow_create: bool,
    ) -> Union[MonitoringRunEntry, JSONResponse]:
        if not allow_create and not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(workspace.name)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            return MonitoringRunEntry(workspace)
        except RunEntryError as exc:
            return _run_entry_error_response(exc)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    def _publication_overlay(
        canonical_project_id: str,
        run_id: str,
        base: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Overlay registry publication state without changing R1 progress."""

        public_token = lr.derive_public_run_token(
            canonical_project_id, run_id
        )
        state = "not_started"
        has_launch = False
        launch_path = (
            _workspace_dir(root, canonical_project_id)
            / lr.LAUNCH_REGISTRY_DB_NAME
        )
        registry: Optional[lr.LaunchRegistry] = None
        try:
            if launch_path.is_file():
                registry = lr.LaunchRegistry(
                    launch_path, project_id=canonical_project_id
                )
                launch = registry.get(run_id, project_id=canonical_project_id)
                has_launch = True
                try:
                    publication = registry.get_publication(
                        project_id=canonical_project_id,
                        run_id=run_id,
                    )
                    state = publication.publication_state
                except lr.LaunchRegistryError as exc:
                    if exc.code != "publication_not_found":
                        raise
                    state = "not_started"
                public_token = launch.public_run_token
            return {
                **dict(base),
                "publication_state": state,
                "result_available": state == lr.PUBLICATION_STATE_AVAILABLE,
                "publication_status_text": _publication_status_text(
                    state, run_state=str(base.get("run_state", ""))
                ),
                "_publication_has_launch": has_launch,
                "_publication_public_token": public_token,
            }
        except lr.LaunchRegistryError as exc:
            if exc.code in {"run_not_found", "public_run_not_found"}:
                return {
                    **dict(base),
                    "publication_state": "not_started",
                    "result_available": False,
                    "publication_status_text": _publication_status_text(
                        "not_started",
                        run_state=str(base.get("run_state", "")),
                    ),
                    "_publication_has_launch": False,
                    "_publication_public_token": public_token,
                }
            raise
        except Exception:
            # A corrupt/temporarily unreadable publication row must not hide
            # the authoritative R1 progress or expose a false result link.
            return {
                **dict(base),
                "publication_state": lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                "result_available": False,
                "publication_status_text": _PUBLICATION_MESSAGES[
                    "publication_recoverable_failed"
                ],
                "_publication_has_launch": has_launch,
                "_publication_public_token": public_token,
            }
        finally:
            if registry is not None:
                registry.close()

    def _publication_setup_inputs(
        canonical_project_id: str,
        launch: lr.LaunchRecord,
    ) -> tuple[rs.DataSnapshot, rs.WorkUnitManifest, tuple[str, ...], dict[str, Any], str]:
        parsed = ProductPrepareAndStartRequest(
            current_snapshot_token=launch.current_snapshot_token,
            mode=launch.mode,
            execution_basis=launch.execution_basis,
            baseline_token=launch.baseline_token,
            risk_rule_tokens=list(launch.rule_tokens),
            idempotency_key=launch.idempotency_key,
        )
        resolved = resolve_launch_inputs(canonical_project_id, parsed)
        if isinstance(resolved, JSONResponse):
            raise ProductPublicationError("manifest_identity_mismatch")
        current, _, _, manifest = resolved
        setup_identity = _publication_manifest_identity(manifest)
        setup_digest = manifest.manifest_digest
        if (
            launch.manifest_digest is not None
            and launch.manifest_digest != setup_digest
        ):
            raise ProductPublicationError("manifest_identity_mismatch")
        coverage = tuple(
            sorted(
                {
                    str(row["site_ref"])
                    for row in current.rows
                    if isinstance(row, Mapping)
                    and isinstance(row.get("site_ref"), str)
                    and row.get("site_ref")
                }
            )
        )
        if not coverage:
            raise ProductPublicationError("authority_identity_mismatch")
        return current, manifest, coverage, setup_identity, setup_digest


    def _record_publication_failure(
        registry: lr.LaunchRegistry,
        publication: lr.ResultPublication,
        *,
        code: str,
        recoverable: bool,
    ) -> lr.ResultPublication:
        target = (
            lr.PUBLICATION_STATE_RECOVERABLE_FAILED
            if recoverable
            else lr.PUBLICATION_STATE_BLOCKED
        )
        message = _PUBLICATION_MESSAGES.get(
            code,
            _PUBLICATION_MESSAGES[
                "runtime_read_failed" if recoverable else "publication_blocked"
            ],
        )
        try:
            return registry.record_publication_failure(
                project_id=publication.project_id,
                run_id=publication.run_id,
                revision=publication.publication_revision,
                target_state=target,
                expected_state=publication.publication_state,
                error_code=code,
                error_message=message,
            )
        except lr.LaunchRegistryError:
            # A concurrent retry may have advanced the row.  Re-read it rather
            # than exposing a false local state to the caller.
            return registry.get_publication(
                project_id=publication.project_id,
                run_id=publication.run_id,
                revision=publication.publication_revision,
            )


    def _publication_failure_response(
        publication: lr.ResultPublication,
    ) -> JSONResponse:
        if publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE:
            return _publication_projection(
                publication.public_run_token,
                publication.publication_state,
                replayed=True,
            )
        if publication.publication_state == lr.PUBLICATION_STATE_RECOVERABLE_FAILED:
            return _error_response(
                500,
                "publication_recoverable_failed",
                _PUBLICATION_MESSAGES["publication_recoverable_failed"],
            )
        if publication.publication_state == lr.PUBLICATION_STATE_BLOCKED:
            return _error_response(
                409,
                "publication_blocked",
                _PUBLICATION_MESSAGES["publication_blocked"],
            )
        return _error_response(
            422,
            "publication_not_available",
            _PUBLICATION_MESSAGES["publication_not_available"],
        )

    def _load_public_result_context(
        canonical_project_id: str,
        result_context_token: str,
        *,
        site_ref: Optional[str] = None,
        require_product_adapter: bool = True,
        continuity_context: bool = False,
    ) -> tuple[
        lr.LaunchRegistry,
        MonitoringRunEntry,
        lr.LaunchRecord,
        lr.ResultPublication,
        Optional[R5ProductAdapter],
    ]:
        """Resolve one persisted context and rebuild the accepted R5 view."""
        legacy_view = open_legacy_view(canonical_project_id)
        if legacy_view is not None:
            # Legacy result data is readable only through the bounded facade;
            # this R5 adapter requires mutable current-schema stores.
            legacy_view.close()
            raise ProductPublicationError("result_context_unavailable")
        registry = open_launch_registry(canonical_project_id)
        if isinstance(registry, JSONResponse):
            raise ProductPublicationError("result_context_unavailable")
        entry: Optional[MonitoringRunEntry] = None
        try:
            try:
                publication = registry.get_publication_by_result_context_token(
                    result_context_token,
                    project_id=canonical_project_id,
                )
            except lr.LaunchRegistryError as exc:
                raise ProductPublicationError(
                    "result_context_unavailable"
                ) from exc
            if (
                publication.publication_state
                != lr.PUBLICATION_STATE_AVAILABLE
                or publication.result_context_token != result_context_token
            ):
                raise ProductPublicationError("result_context_unavailable")
            try:
                launch = registry.get_by_public_token(
                    publication.public_run_token,
                    project_id=canonical_project_id,
                )
            except lr.LaunchRegistryError as exc:
                raise ProductPublicationError(
                    "result_context_unavailable"
                ) from exc
            if (
                launch.run_id != publication.run_id
                or launch.public_run_token != publication.public_run_token
                or launch.run_state != lr.STATE_COMPLETED
                or not launch.result_available
            ):
                raise ProductPublicationError("result_context_unavailable")

            (
                current,
                _setup_manifest,
                coverage,
                setup_identity,
                setup_digest,
            ) = _publication_setup_inputs(canonical_project_id, launch)
            current_source_revision = (
                current.source_revision_id or current.snapshot_ref
            )
            if (
                site_ref is not None
                and site_ref not in publication.site_coverage
            ):
                raise ProductPublicationError("result_center_out_of_scope")
            if (
                launch.current_snapshot_token != publication.snapshot_token
                or current.snapshot_token != publication.snapshot_token
                or current.snapshot_ref != publication.snapshot_ref
                or current.data_cutoff != publication.data_cutoff
                or current_source_revision != publication.source_revision_id
                or tuple(coverage) != tuple(publication.site_coverage)
                or setup_digest != publication.setup_manifest_digest
                or setup_identity != dict(publication.setup_manifest_identity)
            ):
                raise ProductPublicationError("result_context_unavailable")

            entry_candidate = _open_entry(
                _workspace_dir(root, canonical_project_id),
                allow_create=False,
            )
            if isinstance(entry_candidate, JSONResponse):
                raise ProductPublicationError("result_context_unavailable")
            entry = entry_candidate
            gate = _read_publication_gate(
                _workspace_dir(root, canonical_project_id),
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            if (
                gate["revision"] != publication.manifest_revision
                or gate["digest"] != publication.manifest_digest
                or gate["identity"]
                != dict(publication.runtime_manifest_identity)
                or tuple(gate["receipt_ids"])
                != tuple(publication.receipt_identities)
                or gate["receipt_set_digest"]
                != publication.receipt_set_digest
            ):
                raise ProductPublicationError("result_context_unavailable")

            (
                _packet_type,
                _bridge_type,
                _bridge_error_type,
                _input_type,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical_project_id,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_refs=publication.site_coverage,
                snapshot_token=publication.snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            if (
                packet.packet_identity != publication.r5_authority_packet_id
                or packet.packet_digest != publication.r5_authority_packet_digest
                or tuple(packet.site_refs) != tuple(publication.site_coverage)
            ):
                raise ProductPublicationError("result_context_unavailable")
            if (
                not publication.r6_output_set_digest
                or len(publication.artifact_member_ids) != 4
                or publication.artifact_member_set_digest
                != lr.content_digest(list(publication.artifact_member_ids))
            ):
                raise ProductPublicationError(
                    "continuity_unavailable"
                    if continuity_context
                    else "result_context_unavailable"
                )
            runtime_dir = _workspace_dir(root, canonical_project_id) / RUNTIME_DIR_NAME
            r1_store = Store(
                runtime_dir / RUNTIME_DB_NAME,
                runtime_dir / ARTIFACT_DIR_NAME,
            )
            try:
                if any(
                    not r1_store.verify_artifact(member_id)
                    for member_id in publication.artifact_member_ids
                ):
                    raise ProductPublicationError("result_context_unavailable")
            finally:
                r1_store.close()
            product_packet = getattr(packet, "product_packet", None)
            if product_packet is None:
                raise ProductPublicationError("authority_provider_invalid")
            if (
                getattr(product_packet, "project_ref", canonical_project_id)
                != canonical_project_id
                or getattr(product_packet, "run_ref", launch.run_id)
                != launch.run_id
                or getattr(
                    product_packet,
                    "snapshot_ref",
                    publication.snapshot_ref or publication.snapshot_token,
                )
                != (publication.snapshot_ref or publication.snapshot_token)
                or getattr(product_packet, "cutoff_ref", publication.data_cutoff)
                != publication.data_cutoff
            ):
                raise ProductPublicationError("result_context_unavailable")
            for collection_name, reference_name in (
                    ("sites", "site_ref"),
                    ("subjects", "subject_ref"),
                    ("events", "event_ref"),
                    ("visits", "visit_ref"),
                    ("risks", "risk_ref"),
                    ("sources", "locator_ref"),
            ):
                if not hasattr(packet, collection_name):
                    continue
                bridge_refs = {
                    getattr(item, reference_name, None)
                    for item in getattr(packet, collection_name, ())
                }
                product_refs = {
                    getattr(item, reference_name, None)
                    for item in getattr(product_packet, collection_name, ())
                }
                if bridge_refs != product_refs:
                    raise ProductPublicationError("result_context_unavailable")

            def product_packet_provider(
                project_ref: str,
                run_ref: Optional[str] = None,
                snapshot_ref: Optional[str] = None,
                cutoff_ref: Optional[str] = None,
            ) -> Any:
                if (
                    project_ref != canonical_project_id
                    or run_ref is not None
                    and run_ref != launch.run_id
                    or snapshot_ref is not None
                    and snapshot_ref != (
                        publication.snapshot_ref or publication.snapshot_token
                    )
                    or cutoff_ref is not None
                    and cutoff_ref != publication.data_cutoff
                ):
                    raise R5ProductAdapterError(
                        "AUTHORITY_IDENTITY_MISMATCH"
                    )
                return product_packet

            adapter = R5ProductAdapter(product_packet_provider)
            return (
                registry,
                entry,
                launch,
                publication,
                adapter if require_product_adapter else None,
            )
        except Exception:
            if entry is not None:
                entry.close()
            registry.close()
            raise

    def _public_result_envelope(
        result: Mapping[str, Any],
        *,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        result_context_token: str,
    ) -> dict[str, Any]:
        raw_identity = result.get("identity")
        if not isinstance(raw_identity, Mapping):
            raise ProductPublicationError("result_context_unavailable")
        projection = _public_result_projection(result.get("projection"))
        if not isinstance(projection, Mapping):
            raise ProductPublicationError("result_context_unavailable")
        identity: dict[str, Any] = {
            "project_ref": launch.project_id,
            "public_run_token": launch.public_run_token,
            "snapshot_token": publication.snapshot_token,
            "data_cutoff_text": publication.data_cutoff,
            "view": str(raw_identity.get("view") or ""),
            "mode_text": launch.mode_text,
            "site_scope_text": "、".join(
                f"中心 {site_ref}" for site_ref in publication.site_coverage
            ),
        }
        for key in _PUBLIC_RESULT_LOCATOR_KEYS:
            value = raw_identity.get(key)
            if value is not None:
                identity[key] = value
        if identity["view"] not in {"overview", "journey", "evidence"}:
            raise ProductPublicationError("result_context_unavailable")
        public_blob = json.dumps(
            {"identity": identity, "projection": projection},
            ensure_ascii=False,
        ).casefold()
        if _SECRET_VALUE.search(public_blob) or any(
            marker in public_blob
            for marker in (
                '"run_id"',
                '"run_ref"',
                '"snapshot_ref"',
                '"cutoff_ref"',
                '"authority_hash"',
                '"authority_receipt',
                '"packet_digest"',
                '"packet_identity"',
                '"s4_',
                '"r5_',
            )
        ):
            raise ProductPublicationError("result_context_unavailable")
        response_digest = lr.content_digest(
            {"identity": identity, "projection": projection}
        )
        return {
            "identity": identity,
            "projection": dict(projection),
            "result_context_token": result_context_token,
            "response_digest": response_digest,
        }

    def _public_result_error(exc: Exception) -> JSONResponse:
        if isinstance(exc, ProductPublicationError) and exc.code == (
            "result_center_out_of_scope"
        ):
            return _error_response(
                409,
                "result_center_out_of_scope",
                _PUBLICATION_MESSAGES["result_center_out_of_scope"],
            )
        if isinstance(exc, ProductPublicationError) and exc.code == (
            "continuity_unavailable"
        ):
            return _error_response(
                409,
                "continuity_unavailable",
                _PUBLICATION_MESSAGES["continuity_unavailable"],
            )
        return _error_response(
            409,
            "result_context_unavailable",
            _PUBLICATION_MESSAGES["result_context_unavailable"],
        )

    def _build_public_continuity_envelope(
        *,
        registry: lr.LaunchRegistry,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        adapter: R5ProductAdapter,
        result_context_token: str,
        site_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            plan = registry.get_continuity_plan(
                project_id=launch.project_id, target_run_id=launch.run_id
            )
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc

        if (
            plan.status != lr.CONTINUITY_PLAN_STATE_PUBLISHED
            or plan.project_id != launch.project_id
            or plan.target_run_id != launch.run_id
            or plan.mode != launch.mode
            or plan.target_snapshot_id != publication.snapshot_token
            or plan.target_data_cutoff != publication.data_cutoff
            or plan.r5_authority_digest != publication.r5_authority_packet_digest
            or plan.r6_publication_digest != publication.publication_fingerprint
            or plan.r6_receipt_digest != publication.receipt_set_digest
        ):
            raise ProductPublicationError("continuity_unavailable")
        if plan.r6_output_set_digest != publication.r6_output_set_digest:
            raise ProductPublicationError("continuity_unavailable")

        try:
            packet = adapter.get_authority_packet(
                project_ref=launch.project_id,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
            )
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc
        def unique_map(values: Sequence[Any], key_name: str) -> dict[str, Any]:
            mapped: dict[str, Any] = {}
            for value in values:
                key = str(getattr(value, key_name, "") or "").strip()
                if not key or key in mapped:
                    raise ProductPublicationError("continuity_unavailable")
                mapped[key] = value
            return mapped

        site_map = unique_map(packet.sites, "site_ref")
        site_audience_map = unique_map(packet.site_audience, "site_ref")
        if set(site_audience_map) != set(site_map):
            raise ProductPublicationError("continuity_unavailable")
        subject_map = unique_map(packet.subjects, "subject_ref")
        event_map = unique_map(packet.events, "event_ref")
        source_map = unique_map(packet.sources, "locator_ref")
        risk_by_ref = unique_map(packet.risks, "risk_ref")
        risk_by_instance = unique_map(packet.risks, "risk_instance_ref")

        runtime_dir = _workspace_dir(root, launch.project_id) / RUNTIME_DIR_NAME
        artifact_envelopes: dict[str, Any] = {}
        artifact_atoms: dict[tuple[str, str, str], Any] = {}
        r1_store = Store(
            runtime_dir / RUNTIME_DB_NAME,
            runtime_dir / ARTIFACT_DIR_NAME,
        )
        try:
            for member_id in publication.artifact_member_ids:
                envelope = r1_store.get_artifact(member_id)
                if not r1_store.verify_artifact(member_id):
                    raise ProductPublicationError("continuity_unavailable")
                artifact_envelopes[member_id] = envelope
                from packages.medical_monitoring.runtime.continuity_bridge import (
                    extract_atomic_items,
                )

                for atom in extract_atomic_items(
                    [envelope.payload],
                    mode=launch.mode,
                    output_artifact_map={envelope.node_id: envelope.artifact_id},
                ):
                    atom_key = (member_id, atom.object_type, atom.object_id)
                    if atom_key in artifact_atoms:
                        raise ProductPublicationError("continuity_unavailable")
                    artifact_atoms[atom_key] = atom
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc
        finally:
            r1_store.close()

        basis_raw = (
            str(plan.execution_basis or launch.execution_basis or "")
            .strip()
            .lower()
        )
        if basis_raw in {"incremental", "增量分析"}:
            basis_text = "增量分析"
        elif basis_raw in {"full", "全量分析", ""}:
            basis_text = "全量分析"
        else:
            raise ProductPublicationError("continuity_unavailable")

        if plan.baseline is None:
            source_run_text = ""
            comparison_text = "本轮为首次全面分析，无比较基线"
        else:
            baseline_cutoff = str(
                plan.baseline.source_data_cutoff or ""
            ).strip()
            if not baseline_cutoff:
                source_run_text = ""
                comparison_text = "本轮为首次全面分析，无比较基线"
            else:
                try:
                    date.fromisoformat(baseline_cutoff)
                except ValueError as exc:
                    raise ProductPublicationError("continuity_unavailable") from exc
                source_run_text = f"{baseline_cutoff} 监查批次"
                comparison_text = "已与上次监查结果比较"

        rows: list[dict[str, Any]] = []
        all_risk_rows: list[dict[str, Any]] = []
        seen_risk_instances: set[str] = set()

        for item in plan.items:
            if item.object_type == "evidence_binding":
                continue
            if item.object_type not in {
                "risk_instance",
                "query_draft",
                "mode_output_item",
            }:
                raise ProductPublicationError("continuity_unavailable")

            if (
                item.artifact_verified is False
                or item.artifact_member_verified is False
                or not item.source_artifact_id
                or item.source_artifact_id not in publication.artifact_member_ids
            ):
                raise ProductPublicationError("continuity_unavailable")
            source_artifact = artifact_envelopes[item.source_artifact_id]
            if (
                not item.source_artifact_sha256
                or item.source_artifact_sha256 != source_artifact.content_hash
                or item.source_run_id
                and item.source_run_id != source_artifact.run_id
                or not item.source_object_id
                or not item.source_identity
                or not item.target_object_id
                or item.target_object_id != item.object_ref
            ):
                raise ProductPublicationError("continuity_unavailable")
            source_atom = artifact_atoms.get(
                (
                    item.source_artifact_id,
                    item.object_type,
                    item.source_object_id,
                )
            )
            if source_atom is None or source_atom.item_digest != item.source_identity:
                raise ProductPublicationError("continuity_unavailable")
            if item.object_type == "risk_instance":
                obj_type = "risk"
                obj_type_text = "风险"
            elif item.object_type == "query_draft":
                obj_type = "query_draft"
                obj_type_text = "Query 草稿"
            else:
                obj_type = "monitoring_output"
                obj_type_text = "监查结果项"

            change_kind = str(getattr(item, "risk_change_kind", None) or getattr(item, "change_kind", None) or "").strip().lower()
            if change_kind not in _CONTINUITY_RISK_CHANGE_KINDS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            if obj_type == "risk":
                _validate_continuity_risk_semantics(item, change_kind)
            change_text = _CONTINUITY_RISK_CHANGE_KINDS_ZH[change_kind]

            disposition = str(item.disposition or "").strip().lower()
            if disposition not in _CONTINUITY_DISPOSITIONS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            disposition_text = _CONTINUITY_DISPOSITIONS_ZH[disposition]

            data_change_kind = str(item.data_change_kind or "").strip().lower()
            if data_change_kind not in _CONTINUITY_DATA_CHANGE_KINDS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            data_change_text = _CONTINUITY_DATA_CHANGE_KINDS_ZH[data_change_kind]

            sev_before_raw = getattr(item, "prior_severity", None)
            sev_after_raw = getattr(item, "current_severity", None)
            sev_before_zh = _normalize_severity_zh(sev_before_raw)
            sev_after_zh = _normalize_severity_zh(sev_after_raw)

            need_severity_attention = False
            if obj_type == "risk" and change_kind == "new":
                if sev_before_zh != "" or sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True
                sev_before_zh = ""
            elif change_kind == "closed":
                if sev_before_zh not in {"高", "中", "低"} or sev_after_zh != "":
                    need_severity_attention = True
                sev_after_zh = ""
            elif change_kind in {"upgraded", "downgraded", "continued"}:
                if (
                    sev_before_zh not in {"高", "中", "低"}
                    or sev_after_zh not in {"高", "中", "低"}
                ):
                    raise ProductPublicationError("continuity_unavailable")
                rank_before = _SEVERITY_RANK[sev_before_zh]
                rank_after = _SEVERITY_RANK[sev_after_zh]
                if change_kind == "upgraded" and not (rank_after > rank_before):
                    raise ProductPublicationError("continuity_unavailable")
                if change_kind == "downgraded" and not (rank_after < rank_before):
                    raise ProductPublicationError("continuity_unavailable")
                if change_kind == "continued" and not (rank_after == rank_before):
                    raise ProductPublicationError("continuity_unavailable")
            elif obj_type == "risk" and change_kind == "reopened":
                if sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True
            elif obj_type == "risk" and change_kind == "needs_rejudgment":
                if sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True

            ev_summary = (
                item.evidence_summary
                if isinstance(item.evidence_summary, Mapping)
                else {}
            )
            risk_ref_hint = str(ev_summary.get("risk_ref") or "").strip()
            risk_instance_hint = str(
                ev_summary.get("risk_instance_ref") or ""
            ).strip()
            matching_risk = (
                risk_by_instance.get(risk_instance_hint)
                or risk_by_ref.get(risk_ref_hint)
                or risk_by_instance.get(item.object_ref)
                or risk_by_ref.get(item.object_ref)
            )
            if obj_type == "risk":
                if matching_risk is None:
                    raise ProductPublicationError("continuity_unavailable")
                if (
                    risk_ref_hint and risk_ref_hint != matching_risk.risk_ref
                    or risk_instance_hint
                    and risk_instance_hint != matching_risk.risk_instance_ref
                ):
                    raise ProductPublicationError("continuity_unavailable")
                event_ref = matching_risk.event_ref or ""
                event = event_map.get(event_ref) if event_ref else None
                if event_ref and event is None:
                    raise ProductPublicationError("continuity_unavailable")
                row_site_ref = matching_risk.site_ref
                row_subject_ref = matching_risk.subject_ref
                row_risk_ref = matching_risk.risk_ref
                row_risk_instance_ref = matching_risk.risk_instance_ref
                row_risk_anchor_ref = matching_risk.risk_anchor_ref
                authoritative_locators = tuple(matching_risk.source_locator_refs)
                if event is not None and (
                    matching_risk.risk_anchor_ref not in event.risk_anchor_refs
                ):
                    raise ProductPublicationError("continuity_unavailable")
                authority_severity_zh = _normalize_severity_zh(matching_risk.severity)
                if not need_severity_attention and (
                    (change_kind == "closed" and sev_before_zh != authority_severity_zh)
                    or (change_kind != "closed" and sev_after_zh != authority_severity_zh)
                ):
                    raise ProductPublicationError("continuity_unavailable")
            else:
                risk_ref_match = risk_by_ref.get(risk_ref_hint) if risk_ref_hint else None
                risk_instance_match = (
                    risk_by_instance.get(risk_instance_hint)
                    if risk_instance_hint
                    else None
                )
                if (
                    risk_ref_hint
                    and risk_ref_match is None
                    or risk_instance_hint
                    and risk_instance_match is None
                    or risk_ref_match is not None
                    and risk_instance_match is not None
                    and risk_ref_match is not risk_instance_match
                ):
                    raise ProductPublicationError("continuity_unavailable")
                event_ref = str(ev_summary.get("event_ref") or "").strip()
                event = event_map.get(event_ref)
                if event is None:
                    raise ProductPublicationError("continuity_unavailable")
                row_site_ref = event.site_ref
                row_subject_ref = event.subject_ref
                row_risk_ref = matching_risk.risk_ref if matching_risk is not None else ""
                row_risk_instance_ref = (
                    matching_risk.risk_instance_ref if matching_risk is not None else ""
                )
                row_risk_anchor_ref = (
                    matching_risk.risk_anchor_ref if matching_risk is not None else ""
                )
                authoritative_locators = tuple(event.source_locator_refs)
                if (
                    matching_risk is not None
                    and (matching_risk.event_ref or "") != event_ref
                ):
                    raise ProductPublicationError("continuity_unavailable")

            subject = subject_map.get(row_subject_ref)
            if (
                subject is None
                or row_site_ref not in site_map
                or subject.site_ref != row_site_ref
                or event is not None
                and (event.subject_ref != row_subject_ref or event.site_ref != row_site_ref)
            ):
                raise ProductPublicationError("continuity_unavailable")
            for hint, expected in (
                (ev_summary.get("site_ref"), row_site_ref),
                (ev_summary.get("subject_ref"), row_subject_ref),
                (ev_summary.get("risk_anchor_ref"), row_risk_anchor_ref),
                (ev_summary.get("event_ref"), event_ref),
            ):
                if hint not in (None, "") and str(hint).strip() != expected:
                    raise ProductPublicationError("continuity_unavailable")

            row_site_label = _public_continuity_text(
                site_audience_map[row_site_ref].site_label
            )
            row_subject_label = _public_continuity_text(subject.subject_label)
            row_title = _public_continuity_text(
                event.label_zh
                if event is not None
                else matching_risk.risk_type_zh
            )
            row_reason_text = _public_continuity_text(item.reason)
            row_date_label = (
                event.start_date.isoformat()
                if event is not None and event.start_date is not None
                else ""
            )
            row_window_start = str(ev_summary.get("window_start") or "").strip()
            row_window_end = str(ev_summary.get("window_end") or "").strip()
            try:
                parsed_window_start = date.fromisoformat(row_window_start)
                parsed_window_end = date.fromisoformat(row_window_end)
            except ValueError as exc:
                raise ProductPublicationError("continuity_unavailable") from exc
            if parsed_window_start > parsed_window_end:
                raise ProductPublicationError("continuity_unavailable")

            row_event_ref = event_ref

            if any(locator not in source_map for locator in authoritative_locators):
                raise ProductPublicationError("continuity_unavailable")
            requested_locator = str(
                ev_summary.get("source_locator_ref") or ""
            ).strip()
            if requested_locator and requested_locator not in authoritative_locators:
                raise ProductPublicationError("continuity_unavailable")
            loc_ref = requested_locator or (
                authoritative_locators[0] if len(authoritative_locators) == 1 else ""
            )
            src_count = len(authoritative_locators) if loc_ref else 0
            raw_source_count = ev_summary.get("source_count")
            if raw_source_count is not None and (
                type(raw_source_count) is not int
                or raw_source_count < 0
                or raw_source_count != src_count
            ):
                raise ProductPublicationError("continuity_unavailable")

            if data_change_kind == "missing":
                attention_text = "未见记录不代表风险已解除"
            elif (
                change_kind == "needs_rejudgment"
                or disposition == "blocked_incompatible"
                or data_change_kind == "cannot_compare"
                or not getattr(item, "identity_compatible", True)
                or not getattr(item, "source_compatible", True)
                or not getattr(item, "output_contract_compatible", True)
                or getattr(item, "identity_ambiguous", False)
                or getattr(item, "lineage_changed", False)
                or getattr(item, "data_missing", False)
            ):
                attention_text = "身份或数据不完整，需重新判断"
            elif need_severity_attention:
                attention_text = "等级变化待确认"
            elif not loc_ref or src_count == 0:
                attention_text = "原始记录位置待确认"
            else:
                attention_text = ""

            if attention_text not in _CONTINUITY_ATTENTION_TEXTS:
                raise ProductPublicationError("continuity_unavailable")

            ordinal = int(item.ordinal)
            if ordinal < 0:
                raise ProductPublicationError("continuity_unavailable")
            row_ref = f"continuity-row-{ordinal}"

            row_dict = {
                "row_ref": row_ref,
                "object_type": obj_type,
                "object_type_text": obj_type_text,
                "ordinal": ordinal,
                "change_kind": change_kind,
                "change_text": change_text,
                "disposition": disposition,
                "disposition_text": disposition_text,
                "data_change_kind": data_change_kind,
                "data_change_text": data_change_text,
                "severity_before_text": sev_before_zh,
                "severity_after_text": sev_after_zh,
                "title": row_title,
                "reason_text": row_reason_text,
                "attention_text": attention_text,
                "site_ref": row_site_ref,
                "site_label": row_site_label,
                "subject_ref": row_subject_ref,
                "subject_label": row_subject_label,
                "date_label": row_date_label,
                "window_start": row_window_start,
                "window_end": row_window_end,
                "risk_ref": row_risk_ref,
                "risk_instance_ref": row_risk_instance_ref,
                "risk_anchor_ref": row_risk_anchor_ref,
                "event_ref": row_event_ref,
                "source_locator_ref": loc_ref,
                "source_count": src_count,
            }
            validated_row = ProductContinuityRow(**row_dict).model_dump()

            if site_ref is not None and row_site_ref != site_ref:
                continue

            if obj_type == "risk":
                if (
                    not row_risk_instance_ref
                    or row_risk_instance_ref in seen_risk_instances
                ):
                    raise ProductPublicationError("continuity_unavailable")
                seen_risk_instances.add(row_risk_instance_ref)
                all_risk_rows.append(validated_row)

            rows.append(validated_row)

        counts = {
            "new": 0,
            "upgraded": 0,
            "continued": 0,
            "downgraded": 0,
            "closed": 0,
            "reopened": 0,
            "needs_rejudgment": 0,
            "mid_high_total": 0,
            "changed_subject_count": 0,
        }
        changed_subjects: set[str] = set()
        for r in all_risk_rows:
            k = r["change_kind"]
            if k in counts:
                counts[k] += 1
            else:
                raise ProductPublicationError("continuity_unavailable")
            if r["severity_after_text"] in {"高", "中"}:
                counts["mid_high_total"] += 1
            if k in {
                "new",
                "upgraded",
                "downgraded",
                "closed",
                "reopened",
                "needs_rejudgment",
            }:
                s = r["subject_ref"]
                if s:
                    changed_subjects.add(s)

        counts["changed_subject_count"] = len(changed_subjects)

        if (
            counts["new"]
            + counts["upgraded"]
            + counts["continued"]
            + counts["downgraded"]
            + counts["closed"]
            + counts["reopened"]
            + counts["needs_rejudgment"]
            != len(all_risk_rows)
        ):
            raise ProductPublicationError("continuity_unavailable")

        validated_counts = ProductContinuityChangeCounts(**counts).model_dump()
        sorted_rows = sorted(rows, key=_continuity_row_sort_key)
        total_count = len(sorted_rows)
        truncated = total_count > 200
        shown_rows = sorted_rows[:200]
        shown_count = len(shown_rows)

        comparison_dict = {
            "available": True,
            "basis_text": basis_text,
            "comparison_text": comparison_text,
            "source_run_text": source_run_text,
            "change_counts": validated_counts,
            "rows": shown_rows,
            "shown_count": shown_count,
            "total_count": total_count,
            "truncated": truncated,
        }
        validated_comparison = ProductContinuityComparison(
            **comparison_dict
        ).model_dump()

        identity_dict: dict[str, Any] = {
            "project_ref": launch.project_id,
            "public_run_token": launch.public_run_token,
            "snapshot_token": publication.snapshot_token,
            "data_cutoff_text": publication.data_cutoff,
            "mode_text": launch.mode_text,
            "site_scope_text": "、".join(
                _public_continuity_text(site_audience_map[s].site_label)
                for s in publication.site_coverage
            ),
        }
        if site_ref is not None:
            identity_dict["site_ref"] = site_ref

        validated_identity = ProductContinuityIdentity(**identity_dict).model_dump(
            exclude_none=True
        )

        public_blob = json.dumps(
            {"identity": validated_identity, "comparison": validated_comparison},
            ensure_ascii=False,
        ).casefold()
        if _SECRET_VALUE.search(public_blob) or any(
            marker in public_blob
            for marker in (
                '"run_id"',
                '"run_ref"',
                '"snapshot_ref"',
                '"cutoff_ref"',
                '"authority_hash"',
                '"authority_receipt',
                '"packet_digest"',
                '"packet_identity"',
                '"s4_',
                '"r5_',
            )
        ):
            raise ProductPublicationError("continuity_unavailable")

        response_digest = lr.content_digest(
            {"identity": validated_identity, "comparison": validated_comparison}
        )

        response_dict = {
            "result_context_token": result_context_token,
            "identity": validated_identity,
            "comparison": validated_comparison,
            "response_digest": response_digest,
        }
        return ProductContinuityResponse(**response_dict).model_dump(
            exclude_none=True
        )

    @router.get("/project/open")
    async def open_project(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            inspection = open_project_inspection(canonical)
            return open_project_result(inspection).as_dict()
        except (MigrationError, ProjectCompatibilityError):
            return blocked_project_open_projection()
        except Exception:
            return blocked_project_open_projection()

    @router.api_route("/project/audit/verify", methods=["GET", "POST"])
    async def verify_project_audit(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            return verification_projection(canonical, request, auth)
        except (
            ProjectVerificationError,
            RecoveryCoordinationError,
        ):
            return ProjectVerificationDTO(
                RESULT_RECOVERY_REQUIRED,
                "暂时无法完成项目核验，请保留当前项目并联系支持。",
                "保留当前项目并联系支持",
            ).as_dict()
        except Exception:
            return ProjectVerificationDTO(
                RESULT_RECOVERY_REQUIRED,
                "暂时无法完成项目核验，请保留当前项目并联系支持。",
                "保留当前项目并联系支持",
            ).as_dict()

    @router.post("/project/upgrade")
    async def start_project_upgrade(
        project_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductProjectUpgradeRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        runner = MigrationRunner(
            backup_runtime_root,
            canonical,
            project_dir=_workspace_dir(root, canonical),
            wait_seconds=maintenance_wait_seconds,
        )
        receipt: Any = None
        try:
            key = operation_key(request, parsed.idempotency_key, "migration")
            receipt = begin_product_boundary(
                canonical,
                key,
                operation_kind="migration",
                expected_state="requested",
                request=request,
                principal=auth,
            )
            result = runner.start_upgrade(
                key,
                confirmation=parsed.confirmation,
            )
            finish_product_boundary(
                canonical,
                receipt,
                observed_durable_phase=result.state,
                request=request,
                principal=auth,
                operation_update=(
                    operation_projection_for(result.operation)
                    if (
                        result.operation is not None
                        and result.operation.operation_id == receipt.operation_id
                    )
                    else None
                ),
            )
            verification_result = boundary_verification_result(
                canonical,
                receipt,
            )
            finish_product_boundary(
                canonical,
                receipt,
                observed_durable_phase=result.state,
                request=request,
                principal=auth,
                verification_result=verification_result,
                commit=False,
            )
            return upgrade_result_from_state(result.state).as_dict()
        except (MigrationError, ProjectCompatibilityError) as exc:
            if receipt is not None:
                try:
                    classify_product_recovery(
                        canonical,
                        receipt.operation_id,
                        operation_kind="migration",
                        observed_durable_phase="requested",
                        classification="需重新恢复",
                        request=request,
                        principal=auth,
                    )
                except Exception:
                    pass
            return _run_entry_error_response(exc)
        except Exception as exc:
            if receipt is not None:
                try:
                    classify_product_recovery(
                        canonical,
                        receipt.operation_id,
                        operation_kind="migration",
                        observed_durable_phase="requested",
                        classification="需重新恢复",
                        request=request,
                        principal=auth,
                    )
                except Exception:
                    pass
            return _run_entry_error_response(exc)
        finally:
            runner.close()

    @router.get("/project/upgrade")
    async def get_latest_project_upgrade(
        project_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            records = migration_records(canonical)
            if not records:
                raise MigrationError("migration_operation_not_found")
            return migration_projection(records[-1])
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/project/upgrade/{operation_id}/progress")
    async def get_project_upgrade_progress(
        project_id: str,
        operation_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            record = migration_record(canonical, operation_id)
            if record.status in TERMINAL_STATES:
                return upgrade_result_from_state(record.status).as_dict()
            return upgrade_progress_from_operation(record).as_dict()
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/project/upgrade/{operation_id}")
    async def get_project_upgrade(
        project_id: str,
        operation_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            return migration_projection(migration_record(canonical, operation_id))
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/backups")
    async def create_backup(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductBackupRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            key = operation_key(request, parsed.idempotency_key, "backup")
            record = reserve_operation(
                pb.OP_BACKUP,
                canonical,
                key,
            )
            if record.status not in _PRODUCT_BACKUP_TERMINAL:
                receipt = begin_product_boundary(
                    canonical,
                    record.operation_id,
                    operation_kind=pb.OP_BACKUP,
                    expected_state=record.status,
                    request=request,
                    principal=auth,
                )
                start_backup_worker(
                    canonical,
                    record.operation_id,
                    key,
                    boundary_receipt=receipt,
                    request=request,
                    principal=auth,
                )
            return _public_backup_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/backups/{operation_id}")
    async def get_backup(
        project_id: str,
        operation_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            record = operation_record(canonical, operation_id, pb.OP_BACKUP)
            return _public_backup_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/restores/preflight")
    async def restore_preflight(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRestorePreflightRequest.model_validate(body)
            source_id = requested_operation_id(
                parsed.backup_operation_id, parsed.operation_id
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        if source_id is None:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        manager: Optional[pb.ProjectBackupManager] = None
        try:
            _, package_path = backup_source(canonical, source_id)
            manager = pb.ProjectBackupManager(backup_runtime_root, canonical)
            result = manager.preflight(
                package_path,
                operation_key(request, parsed.idempotency_key, "preflight"),
            )
            return _public_preflight_projection(result, source_id)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            if manager is not None:
                manager.ledger.close()

    @router.post("/restores")
    async def restore_project(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRestoreRequest.model_validate(body)
            source_id = requested_operation_id(
                parsed.backup_operation_id, parsed.operation_id
            )
            preflight_id = parsed.preflight_operation_id
        except ValidationError as exc:
            return _validation_error_response(exc)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        if source_id is None:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        try:
            source_record, package_path = backup_source(canonical, source_id)
            if preflight_id is not None:
                preflight_record = operation_record(
                    canonical, preflight_id, pb.OP_PREFLIGHT
                )
                if (
                    preflight_record.status
                    != pb.STATUS_READY_FOR_CONFIRMATION
                    or preflight_record.package_id != source_record.package_id
                ):
                    raise pb.ProjectBackupError("backup_operation_conflict")
            key = operation_key(request, parsed.idempotency_key, "restore")
            record = reserve_operation(
                pb.OP_RESTORE,
                canonical,
                key,
                package_id=source_record.package_id,
                initial_status=pb.STATUS_CONFIRMED,
            )
            if restore_should_start(record, parsed.confirmation):
                receipt = begin_product_boundary(
                    canonical,
                    record.operation_id,
                    operation_kind=pb.OP_RESTORE,
                    expected_state=record.status,
                    request=request,
                    principal=auth,
                )
                start_restore_worker(
                    canonical,
                    record.operation_id,
                    key,
                    package_path,
                    preflight_id,
                    parsed.confirmation,
                    boundary_receipt=receipt,
                    request=request,
                    principal=auth,
                )
            return _public_restore_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/restores/{operation_id}")
    async def get_restore(
        project_id: str,
        operation_id: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        try:
            record = operation_record(canonical, operation_id, pb.OP_RESTORE)
            return _public_restore_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/workspace/bootstrap")
    async def bootstrap(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductBootstrapRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=True)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            result = entry.bootstrap_workspace()
            return _projection(result, replayed=True)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.get("/run-setup/options")
    async def get_run_setup_options(
        project_id: str,
        request: Request,
        current_snapshot_token: Optional[str] = None,
        snapshot_token: Optional[str] = None,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        for selector in (current_snapshot_token, snapshot_token):
            if selector is not None and not selector.strip():
                return _run_entry_error_response(rs.RunSetupError("invalid_snapshot"))
        try:
            legacy_options = legacy_setup_projection(canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)
        if legacy_options is not None:
            return legacy_options
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        catalog = setup_catalog(canonical)
        if isinstance(catalog, JSONResponse):
            return catalog
        try:
            options = catalog.get_options(
                canonical,
                current_snapshot_token=current_snapshot_token or snapshot_token,
            )
            return _setup_projection(options.public_projection())
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/risk-rules/preview")
    async def preview_risk_rule(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.DRAFT_QUERY,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRiskRulePreviewRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            registry = setup_registry(canonical)
            if isinstance(registry, JSONResponse):
                return registry
            preview = registry.preview(
                canonical,
                parsed.source_text,
                applicable_scope=parsed.applicable_scope,
                starting_run=parsed.starting_run,
            )
            return _setup_projection(preview.as_dict())
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    @router.post("/risk-rules")
    async def append_risk_rule(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.DRAFT_QUERY,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRiskRuleRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            with risk_registry_lock:
                registry = setup_registry(canonical)
                if isinstance(registry, JSONResponse):
                    return registry
                if parsed.preview is not None:
                    draft: Any = parsed.preview
                elif parsed.draft is not None:
                    draft = parsed.draft
                elif parsed.preview_token:
                    draft = parsed.preview_token
                else:
                    draft = {}
                kwargs: dict[str, Any] = {}
                if parsed.candidate_id is not None:
                    kwargs["candidate_id"] = parsed.candidate_id
                if parsed.starting_run is not None:
                    kwargs["starting_run"] = parsed.starting_run
                if parsed.created_at:
                    kwargs["created_at"] = parsed.created_at
                if parsed.idempotency_key is not None:
                    kwargs["idempotency_key"] = parsed.idempotency_key
                revision = registry.append_revision(canonical, draft, **kwargs)
                return _setup_projection(revision.as_dict())
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    @router.get("/risk-rules")
    async def get_risk_rules(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_RISK_AUDIT,
        )
        if isinstance(auth, JSONResponse):
            return auth
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                return _setup_projection(
                    {
                        "schema_version": rs.SCHEMA_VERSION,
                        "project_id": canonical,
                        "rule_revisions": [
                            _legacy_risk_projection(row)
                            for row in view.list_risk_rules()
                        ],
                    }
                )
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        registry = setup_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        try:
            return _setup_projection(
                {
                    "schema_version": rs.SCHEMA_VERSION,
                    "project_id": canonical,
                    "rule_revisions": registry.public_revisions(canonical),
                }
            )
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/execution-profiles/{layer_kind}/{scope_key}")
    async def append_profile(
        project_id: str,
        layer_kind: str,
        scope_key: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        validated_scope = _validated_layer_scope(
            layer_kind=layer_kind,
            scope_key=scope_key,
            canonical_project_id=canonical,
        )
        if isinstance(validated_scope, JSONResponse):
            return validated_scope
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProfileFieldsRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        fields = parsed.fields()
        if not fields:
            return _error_response(
                422,
                "empty_override_payload",
                chinese_message_for("empty_override_payload"),
            )
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            result = entry.append_execution_profile(
                layer_kind, validated_scope, fields
            )
            return _projection(result)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.get("/execution-profiles/{layer_kind}/{scope_key}")
    async def get_profile(
        project_id: str,
        layer_kind: str,
        scope_key: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        validated_scope = _validated_layer_scope(
            layer_kind=layer_kind,
            scope_key=scope_key,
            canonical_project_id=canonical,
        )
        if isinstance(validated_scope, JSONResponse):
            return validated_scope
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                rows = view.list_execution_profiles(
                    layer_kind=layer_kind,
                    scope_key=validated_scope,
                )
                if not rows:
                    return _error_response(
                        404,
                        "profile_layer_not_found",
                        chinese_message_for("profile_layer_not_found"),
                    )
                return _legacy_profile_projection(rows[-1])
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            return entry
        try:
            return _projection(
                entry.get_execution_profile(layer_kind, validated_scope)
            )
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()

    @router.post("/runs/prepare-and-start")
    async def prepare_and_start(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            # Starting a medical-monitoring run is a user-facing AI-run
            # action.  The lower-level execution controls remain admin-only.
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductPrepareAndStartRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)

        workspace = _workspace_dir(root, canonical)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            resolved = resolve_launch_inputs(canonical, parsed)
        except Exception as exc:
            if isinstance(exc, (rs.RunSetupError, RunEntryError, RuntimeProgressError)):
                response = _run_entry_error_response(exc)
            else:
                response = _error_response(500, "internal_error")
            write_permit.release()
            return response
        if isinstance(resolved, JSONResponse):
            write_permit.release()
            return resolved
        current, baseline, revisions, manifest = resolved

        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            reservation = registry.reserve(
                canonical,
                idempotency_key=parsed.idempotency_key,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                current_snapshot_token=parsed.current_snapshot_token,
                baseline_token=parsed.baseline_token,
                rule_tokens=(
                    rs.public_revision_token(revision.revision_token)
                    for revision in revisions
                ),
                data_cutoff=current.data_cutoff,
                comparison_range_text=_comparison_range_text(
                    parsed.mode,
                    parsed.execution_basis,
                    baseline,
                ),
                enforce_in_flight=True,
            )
            # A retry after the durable reservation but before manifest
            # preparation must finish the same run instead of leaving an
            # unstartable history row.  Once the manifest is recorded, the
            # request is a normal replay and must never start a second worker.
            if reservation.replayed and reservation.record.manifest_digest is not None:
                return _launch_projection(reservation.record, replayed=True)

            entry = _open_entry(workspace, allow_create=False)
            if isinstance(entry, JSONResponse):
                return entry
            run_id = reservation.run_id
            scopes = _auto_scopes(
                entry,
                canonical_project_id=canonical,
                run_id=run_id,
                capability_scope_key="",
            )
            entry.bind_run(
                run_id=run_id,
                project_id=canonical,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                data_cutoff=current.data_cutoff,
                source_revision_id=current.source_revision_id or current.snapshot_ref,
                prior_accepted_snapshot_ref=(
                    baseline.snapshot_ref
                    if parsed.mode == rs.MODE_DAILY
                    and parsed.execution_basis == rs.BASIS_INCREMENTAL
                    and baseline is not None
                    else None
                ),
                **scopes,
            )
            adapter = progress_adapter(workspace, entry, canonical)
            adapter.prepare_execution(run_id, _runtime_work_units(manifest))
            registry.record_manifest(
                run_id,
                manifest.manifest_digest,
                project_id=canonical,
            )
            try:
                adapter.start_execution(run_id)
            except (RuntimeProgressError, RunEntryError) as exc:
                if exc.code != "worker_start_failed":
                    raise
                record = registry.record_start_failure(
                    run_id,
                    project_id=canonical,
                )
                return _launch_projection(record, replayed=False)
            record = registry.mark_running(run_id, project_id=canonical)
            return _launch_projection(record, replayed=reservation.replayed)
        except lr.LaunchRegistryError as exc:
            return _launch_error_response(exc)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

    @router.get("/runs")
    async def get_runs(
        project_id: str,
        request: Request,
        limit: Optional[str] = None,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                history_limit: Optional[int] = None
                if limit is not None:
                    try:
                        history_limit = int(limit)
                    except (TypeError, ValueError) as exc:
                        raise lr.LaunchRegistryError(
                            "invalid_history_limit"
                        ) from exc
                    if history_limit < 0:
                        raise lr.LaunchRegistryError("invalid_history_limit")
                    history_limit = min(history_limit, 100)
                rows = sorted(
                    view.list_launches(),
                    key=lambda row: (
                        str(row.get("created_at", "")),
                        int(row.get("sequence", 0)),
                    ),
                    reverse=True,
                )
                if history_limit is not None:
                    rows = rows[:history_limit]
                records = [_legacy_launch_record(row) for row in rows]
                return {
                    "runs": [record.public_projection() for record in records]
                }
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            history_limit: Optional[int] = None
            if limit is not None:
                try:
                    history_limit = int(limit)
                except (TypeError, ValueError) as exc:
                    raise lr.LaunchRegistryError("invalid_history_limit") from exc
            records = list(registry.list_records(canonical, limit=history_limit))
            active = registry.get_in_flight(canonical)
            if active is not None and active.manifest_digest is not None:
                workspace = _workspace_dir(root, canonical)
                entry = _open_entry(workspace, allow_create=False)
                if not isinstance(entry, JSONResponse):
                    adapter = progress_adapter(workspace, entry, canonical)
                    try:
                        state = adapter.read_progress(active.run_id).get(
                            "run_state"
                        )
                        if (
                            state in lr.RUN_STATE_VALUES
                            and state != active.run_state
                        ):
                            updated = registry.update_state(
                                active.run_id,
                                state,
                                project_id=canonical,
                            )
                            records = [
                                updated
                                if record.sequence == active.sequence
                                else record
                                for record in records
                            ]
                    except (
                        RuntimeProgressError,
                        RunEntryError,
                        lr.LaunchRegistryError,
                    ):
                        # A launch reserved before preparation remains a
                        # visible waiting item and is recoverable by the
                        # same idempotent request.
                        pass
            return {"runs": [record.public_projection() for record in records]}
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

    @router.post("/runs/{public_run_token}/publication")
    async def publish_result(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductPublicationRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)

        workspace = _workspace_dir(root, canonical)
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        publication: Optional[lr.ResultPublication] = None
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            (
                current,
                _setup_manifest,
                coverage,
                setup_identity,
                setup_digest,
            ) = _publication_setup_inputs(canonical, launch)
            fingerprint = lr.compute_publication_fingerprint(
                canonical,
                launch.run_id,
                launch.public_run_token,
                snapshot_token=launch.current_snapshot_token,
                source_revision_id=(
                    current.source_revision_id or current.snapshot_ref
                ),
                data_cutoff=current.data_cutoff,
                site_coverage=coverage,
                setup_manifest_identity=setup_identity,
            )
            publication = registry.reserve_publication(
                project_id=canonical,
                run_id=launch.run_id,
                idempotency_key=parsed.idempotency_key,
                publication_fingerprint=fingerprint,
                publication_revision=lr.PUBLICATION_REVISION,
                snapshot_token=launch.current_snapshot_token,
                snapshot_ref=current.snapshot_ref,
                source_revision_id=(
                    current.source_revision_id or current.snapshot_ref
                ),
                data_cutoff=current.data_cutoff,
                setup_manifest_digest=setup_digest,
                manifest_revision=None,
                runtime_manifest_revision=None,
                manifest_digest=None,
                runtime_manifest_digest=None,
                mandatory_denominator=int(
                    setup_identity["mandatory_denominator"]
                ),
                site_coverage=coverage,
                setup_manifest_identity=setup_identity,
                runtime_manifest_identity=None,
            )
            publication_replayed = bool(publication.replayed)
            if publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE:
                return _publication_projection(
                    launch.public_run_token,
                    publication.publication_state,
                    replayed=True,
                    run_state=launch.run_state,
                )
            if publication.publication_state in {
                lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                lr.PUBLICATION_STATE_BLOCKED,
            }:
                publication = registry.retry_publication(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                )

            if entry is None:
                entry = _open_entry(workspace, allow_create=False)
                if isinstance(entry, JSONResponse):
                    publication = _record_publication_failure(
                        registry,
                        publication,
                        code="runtime_read_failed",
                        recoverable=True,
                    )
                    return _publication_failure_response(publication)
            adapter = progress_adapter(workspace, entry, canonical)
            try:
                progress = adapter.read_progress(launch.run_id)
            except (RuntimeProgressError, RunEntryError) as exc:
                audit_invalid = (
                    exc.code == "runtime_integrity_failed"
                    and _runtime_audit_chain_is_invalid(
                        workspace, launch.run_id
                    )
                )
                normalized_code = (
                    "receipt_gate_blocked"
                    if audit_invalid
                    else (
                        "runtime_read_failed"
                        if exc.code
                        in {
                            "execution_not_prepared",
                            "runtime_integrity_failed",
                            "runtime_identity_mismatch",
                        }
                        else exc.code
                    )
                )
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code=normalized_code,
                    recoverable=(
                        False
                        if audit_invalid
                        else exc.code
                        in {
                            "execution_not_prepared",
                            "runtime_integrity_failed",
                            "store_closed",
                        }
                    ),
                )
                return _publication_failure_response(publication)
            run_state = str(progress.get("run_state", ""))
            if run_state not in lr.RUN_STATE_VALUES:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="runtime_read_failed",
                    recoverable=True,
                )
                return _publication_failure_response(publication)
            if launch.run_state != run_state:
                try:
                    launch = registry.update_state(
                        launch.run_id,
                        run_state,
                        project_id=canonical,
                    )
                except lr.LaunchRegistryError:
                    publication = _record_publication_failure(
                        registry,
                        publication,
                        code="runtime_read_failed",
                        recoverable=True,
                    )
                    return _publication_failure_response(publication)

            runtime_metadata = _runtime_manifest_metadata(
                workspace, launch.run_id
            )
            if runtime_metadata is None:
                raise ProductPublicationError(
                    "runtime_read_failed", recoverable=True
                )
            if (
                runtime_metadata["identity"] != setup_identity
                or int(
                    runtime_metadata["identity"]["mandatory_denominator"]
                )
                != int(setup_identity["mandatory_denominator"])
            ):
                raise ProductPublicationError("manifest_identity_mismatch")
            try:
                publication = registry.bind_publication_runtime_manifest(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                    fingerprint=publication.publication_fingerprint,
                    runtime_manifest_revision=runtime_metadata["revision"],
                    runtime_manifest_digest=runtime_metadata["digest"],
                    runtime_manifest_identity=runtime_metadata["identity"],
                    mandatory_denominator=int(
                        runtime_metadata["identity"][
                            "mandatory_denominator"
                        ]
                    ),
                )
            except lr.LaunchRegistryError as exc:
                if exc.code == "store_closed":
                    raise ProductPublicationError(
                        "runtime_read_failed", recoverable=True
                    ) from exc
                if exc.code in {
                    "publication_cas_conflict",
                    "invalid_publication_metadata",
                    "invalid_manifest_digest",
                    "invalid_publication_revision",
                }:
                    raise ProductPublicationError(
                        "manifest_identity_mismatch"
                    ) from exc
                raise
            if run_state != lr.STATE_COMPLETED:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="run_not_completed",
                    recoverable=False,
                )
                return _publication_failure_response(publication)
            current_source_revision = (
                current.source_revision_id or current.snapshot_ref
            )

            gate = _read_publication_gate(
                workspace,
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            stored_runtime = {
                "revision": publication.manifest_revision,
                "identity": dict(publication.runtime_manifest_identity),
                "digest": publication.manifest_digest,
            }
            if (
                stored_runtime["revision"] != gate["revision"]
                or stored_runtime["identity"] != gate["identity"]
                or stored_runtime["digest"] != gate["digest"]
                or gate["identity"] != setup_identity
                or gate["mandatory_denominator"]
                != int(setup_identity["mandatory_denominator"])
                or publication.site_coverage != coverage
                or publication.setup_manifest_digest != setup_digest
                or publication.snapshot_token
                != launch.current_snapshot_token
                or publication.snapshot_ref != current.snapshot_ref
                or publication.source_revision_id != current_source_revision
                or publication.data_cutoff != current.data_cutoff
            ):
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="manifest_identity_mismatch",
                    recoverable=False,
                )
                return _publication_failure_response(publication)

            (
                _,
                _,
                _,
                _,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=current.snapshot_ref,
                cutoff_ref=current.data_cutoff,
                site_refs=coverage,
                snapshot_token=launch.current_snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            r6_output_set_digest: Optional[str] = None
            artifact_member_ids: Optional[tuple[str, ...]] = None
            artifact_member_set_digest: Optional[str] = None

            if r6_provider is not None:
                _, cb = _r6_publication_types()
                run_binding = dict(entry.get_run(launch.run_id))
                run_binding.setdefault("carry_forward_run_ids", [])
                run_binding.setdefault("mode_transition", "explicit_new_run")
                run_binding.setdefault("actor", "system_synthetic")
                if not run_binding.get("created_at"):
                    run_binding["created_at"] = getattr(
                        launch, "created_at", "2026-08-28T00:00:00Z"
                    )
                if not run_binding.get("knowledge_pack_version"):
                    run_binding["knowledge_pack_version"] = "kp-08b-v1"
                if not run_binding.get("rule_activation_version"):
                    run_binding["rule_activation_version"] = "rav-08b-v1"
                if not run_binding.get("mapping_version"):
                    run_binding["mapping_version"] = "map-08b-v1"
                if not run_binding.get("identity_algorithm_version"):
                    run_binding["identity_algorithm_version"] = "ia-08b-v1"
                if not run_binding.get("identity_algorithm_digest"):
                    run_binding["identity_algorithm_digest"] = "ia-digest-08b-v1"
                if run_binding.get("mode") == "post_lock_pre_cfdi":
                    run_binding.setdefault("fixed_total", True)
                    if not run_binding.get("locked_snapshot_hash"):
                        run_binding["locked_snapshot_hash"] = "snap-hash-fixed-001"
                    if not run_binding.get("output_cutoff_ref"):
                        run_binding["output_cutoff_ref"] = run_binding.get("data_cutoff")
                    if not run_binding.get("output_revision_ref"):
                        run_binding["output_revision_ref"] = run_binding.get("source_revision_id")
                    if not run_binding.get("local_os_user"):
                        run_binding["local_os_user"] = "local-user-synthetic"
                    if not run_binding.get("acceptance_evidence_hash"):
                        run_binding["acceptance_evidence_hash"] = "accept-hash-fixed-001"
                raw_outputs = _obtain_r6_mode_outputs(
                    r6_provider,
                    run_binding,
                    r5_packet=packet,
                    attempts=gate["receipt_attempts"],
                )
                if not raw_outputs or len(raw_outputs) != 4:
                    raise ProductPublicationError(
                        "receipt_gate_blocked", recoverable=False
                    )
                runtime_dir = workspace / RUNTIME_DIR_NAME
                db_path = runtime_dir / RUNTIME_DB_NAME
                artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
                r1_store = Store(db_path, artifact_dir)
                try:
                    committed_set = cb.commit_mode_outputs(
                        r1_store,
                        raw_outputs,
                        run_binding=run_binding,
                        r5_packet=packet,
                    )
                except cb.R5AuthorityVerificationError as exc:
                    raise ProductPublicationError(
                        "authority_identity_mismatch", recoverable=False
                    ) from exc
                except (cb.ContinuityBridgeError, Exception) as exc:
                    raise ProductPublicationError(
                        "receipt_gate_blocked", recoverable=False
                    ) from exc
                finally:
                    r1_store.close()
                r6_output_set_digest = committed_set.r6_output_set_digest
                artifact_member_ids = committed_set.artifact_member_ids
                artifact_member_set_digest = committed_set.artifact_member_set_digest

            try:
                publication = registry.finalize_publication(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                    fingerprint=publication.publication_fingerprint,
                    receipt_identities=gate["receipt_ids"],
                    receipt_set_digest=gate["receipt_set_digest"],
                    r5_authority_packet_id=packet.packet_identity,
                    r5_authority_packet_digest=packet.packet_digest,
                    s4_authority_packet_identities=packet.s4_packet_ids,
                    s4_authority_packet_digests=packet.s4_packet_digests,
                    r6_output_set_digest=r6_output_set_digest,
                    artifact_member_ids=artifact_member_ids,
                    artifact_member_set_digest=artifact_member_set_digest,
                )
            except lr.LaunchRegistryError as exc:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code=(
                        "runtime_read_failed"
                        if exc.code in {"store_closed", "publication_cas_conflict"}
                        else exc.code
                    ),
                    recoverable=exc.code
                    in {"store_closed", "publication_cas_conflict"},
                )
                return _publication_failure_response(publication)
            return _publication_projection(
                launch.public_run_token,
                publication.publication_state,
                replayed=publication_replayed or bool(publication.replayed),
                run_state=launch.run_state,
            )
        except ProductPublicationError as exc:
            if publication is None:
                return _error_response(
                    _status_for(exc.code),
                    exc.code,
                    _PUBLICATION_MESSAGES.get(exc.code),
                )
            publication = _record_publication_failure(
                registry,
                publication,
                code=exc.code,
                recoverable=exc.recoverable,
            )
            return _publication_failure_response(publication)
        except (rs.RunSetupError, RuntimeProgressError, RunEntryError) as exc:
            if publication is None:
                return _run_entry_error_response(exc)
            publication = _record_publication_failure(
                registry,
                publication,
                code="runtime_read_failed",
                recoverable=True,
            )
            return _publication_failure_response(publication)
        except Exception:
            if publication is None:
                return _error_response(500, "internal_error")
            publication = _record_publication_failure(
                registry,
                publication,
                code="internal_error",
                recoverable=False,
            )
            return _publication_failure_response(publication)
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

    @router.get("/runs/{public_run_token}/publication")
    async def get_publication(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                launch_rows = [
                    row
                    for row in view.list_launches()
                    if row.get("public_run_token") == public_run_token
                ]
                if not launch_rows:
                    return _error_response(
                        404,
                        "public_run_not_found",
                        "未找到指定的监查运行。",
                    )
                launch = _legacy_launch_record(launch_rows[0])
                publication_rows = view.list_publications(run_id=launch.run_id)
                if not publication_rows:
                    return _publication_projection(
                        launch.public_run_token,
                        "not_started",
                        run_state=launch.run_state,
                    )
                state = str(
                    publication_rows[0].get("publication_state", "")
                )
                return _publication_projection(
                    launch.public_run_token,
                    state,
                    replayed=False,
                    run_state=launch.run_state,
                )
            except lr.LaunchRegistryError as exc:
                return _launch_error_response(exc)
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        launch_path = (
            _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
        )
        if not launch_path.is_file():
            return _error_response(
                404,
                "public_run_not_found",
                "未找到指定的监查运行。",
            )
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            try:
                publication = registry.get_publication(
                    project_id=canonical, run_id=launch.run_id
                )
            except lr.LaunchRegistryError as exc:
                if exc.code != "publication_not_found":
                    raise
                return _publication_projection(
                    launch.public_run_token,
                    "not_started",
                    run_state=launch.run_state,
                )
            return _publication_projection(
                launch.public_run_token,
                publication.publication_state,
                replayed=False,
                run_state=launch.run_state,
            )
        except lr.LaunchRegistryError as exc:
            return _launch_error_response(exc)
        finally:
            registry.close()

    @router.post("/runs")
    async def bind_run(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductCreateRunRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            scopes = _auto_scopes(
                entry,
                canonical_project_id=canonical,
                run_id=parsed.run_id,
                capability_scope_key=parsed.capability_scope_key,
            )
            result = entry.bind_run(
                run_id=parsed.run_id,
                project_id=canonical,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                data_cutoff=parsed.data_cutoff,
                source_revision_id=parsed.source_revision_id,
                prior_accepted_snapshot_ref=parsed.prior_accepted_snapshot_ref,
                **scopes,
            )
            return _projection(result, replayed=True)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/prepare")
    async def prepare_execution(project_id: str, run_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductPrepareExecutionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            adapter = progress_adapter(workspace, entry, canonical)
            return adapter.prepare_execution(
                run_id,
                parsed.work_units,
                execution_kind=parsed.execution_mode or parsed.execution_kind,
            )
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/start")
    async def start_execution(project_id: str, run_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.start_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/resume")
    async def resume_execution(project_id: str, run_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.resume_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/cancel")
    async def cancel_execution(project_id: str, run_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.cancel_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.get("/runs/{public_run_token}/progress")
    async def get_progress(
        project_id: str, public_run_token: str, request: Request
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        run_id = public_run_token
        resolved_run_id = run_id
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                launch: Optional[lr.LaunchRecord] = None
                if run_id.startswith("run:"):
                    launch_rows = [
                        row
                        for row in view.list_launches()
                        if row.get("public_run_token") == run_id
                    ]
                    if not launch_rows:
                        return _error_response(
                            404,
                            "public_run_not_found",
                            "未找到指定的监查运行。",
                        )
                    launch = _legacy_launch_record(launch_rows[0])
                    resolved_run_id = launch.run_id
                else:
                    launch_rows = [
                        row
                        for row in view.list_launches()
                        if row.get("run_id") == run_id
                    ]
                    if launch_rows:
                        launch = _legacy_launch_record(launch_rows[0])
                result = _legacy_progress_projection(
                    view,
                    resolved_run_id,
                    launch,
                )
                if auth is not None:
                    action_auth = authorize(
                        request,
                        project_id=canonical,
                        action=MonitoringAction.ADMINISTER_RUNTIME,
                    )
                    if isinstance(action_auth, JSONResponse):
                        result = {**result, "available_actions": []}
                return result
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        resolved_run_id = run_id
        if run_id.startswith("run:"):
            launch_path = (
                _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
            )
            if not launch_path.is_file():
                return _error_response(
                    404,
                    "public_run_not_found",
                    "未找到指定的监查运行。",
                )
            launch_registry = open_launch_registry(canonical)
            if isinstance(launch_registry, JSONResponse):
                return launch_registry
            try:
                resolved_run_id = launch_registry.get_by_public_token(
                    run_id, project_id=canonical
                ).run_id
            except lr.LaunchRegistryError as exc:
                return _launch_error_response(exc)
            finally:
                launch_registry.close()
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            adapter = progress_adapter(workspace, entry, canonical)
            result = adapter.read_progress(resolved_run_id)
            overlay = _publication_overlay(canonical, resolved_run_id, result)
            has_launch = bool(overlay.pop("_publication_has_launch", False))
            overlay.pop("_publication_public_token", None)
            result = overlay
            # Progress is readable by medical monitors, but run controls and
            # publication actions are only useful to runtime administrators.
            admin_allowed = True
            if auth is not None:
                action_auth = authorize(
                    request,
                    project_id=canonical,
                    action=MonitoringAction.ADMINISTER_RUNTIME,
                )
                admin_allowed = not isinstance(action_auth, JSONResponse)
            if not admin_allowed:
                result = {**result, "available_actions": []}
            elif has_launch and result.get("run_state") == lr.STATE_COMPLETED:
                actions = list(result.get("available_actions", []))
                publication_state = result.get("publication_state")
                action = (
                    "整理结果"
                    if publication_state == "not_started"
                    else (
                        "重新整理"
                        if publication_state
                        in {
                            lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                            lr.PUBLICATION_STATE_BLOCKED,
                        }
                        else None
                    )
                )
                if action is not None and action not in actions:
                    actions.append(action)
            return result
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            try:
                entry.close()
            finally:
                write_permit.release()
    @router.get("/results/{result_context_token}/overview")
    async def get_public_result_overview(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"site_ref"}),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query.get("site_ref"),
            )
            _registry, _entry, launch, publication, adapter = context
            result = adapter.overview(
                project_ref=canonical,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_ref=query.get("site_ref"),
            )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/results/{result_context_token}/subjects/{subject_ref}")
    async def get_public_result_subject(
        project_id: str,
        result_context_token: str,
        subject_ref: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        subject = _canonical_public_result_value(
            subject_ref, field_name="subject_ref"
        )
        if isinstance(token, JSONResponse):
            return token
        if isinstance(subject, JSONResponse):
            return subject
        query = _parse_public_result_query(
            request,
            allowed=frozenset(
                {
                    "site_ref",
                    "spine_ref",
                    "window_start",
                    "window_end",
                    "risk_instance_ref",
                    "risk_anchor_ref",
                    "visit_ref",
                    "event_ref",
                }
            ),
            required=frozenset(
                {"site_ref", "spine_ref", "window_start", "window_end"}
            ),
        )
        if isinstance(query, JSONResponse):
            return query
        window_start = _parse_public_result_date(query["window_start"])
        window_end = _parse_public_result_date(query["window_end"])
        if isinstance(window_start, JSONResponse):
            return window_start
        if isinstance(window_end, JSONResponse):
            return window_end
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query["site_ref"],
            )
            _registry, _entry, launch, publication, adapter = context
            result = adapter.subject_workspace(
                project_ref=canonical,
                subject_ref=subject,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_ref=query["site_ref"],
                spine_ref=query["spine_ref"],
                window_start=window_start,
                window_end=window_end,
                risk_instance_ref=query.get("risk_instance_ref"),
                risk_anchor_ref=query.get("risk_anchor_ref"),
                visit_ref=query.get("visit_ref"),
                event_ref=query.get("event_ref"),
            )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/results/{result_context_token}/source-evidence")
    async def get_public_result_source_evidence(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"risk_instance_ref", "source_locator_ref"}),
            required=frozenset({"risk_instance_ref", "source_locator_ref"}),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(canonical, token)
            _registry, _entry, launch, publication, adapter = context
            result = adapter.source_evidence(
                project_ref=canonical,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                risk_instance_ref=query["risk_instance_ref"],
                source_locator_ref=query["source_locator_ref"],
            )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()


    @router.get("/results/{result_context_token}/continuity")
    async def get_public_result_continuity(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"site_ref"}),
            required=frozenset(),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                Optional[R5ProductAdapter],
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query.get("site_ref"),
                continuity_context=True,
            )
            registry, _entry, launch, publication, adapter = context
            if adapter is None:
                raise ProductPublicationError("continuity_unavailable")
            return _build_public_continuity_envelope(
                registry=registry,
                launch=launch,
                publication=publication,
                adapter=adapter,
                result_context_token=token,
                site_ref=query.get("site_ref"),
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/runs/{public_run_token}/result-entry")
    async def get_result_entry(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        legacy_view = open_legacy_view(canonical)
        if legacy_view is not None:
            try:
                matching_launch = any(
                    row.get("public_run_token") == public_run_token
                    for row in legacy_view.list_launches()
                )
                if not matching_launch:
                    return _error_response(
                        404,
                        "public_run_not_found",
                        "未找到指定的监查运行。",
                    )
                return _error_response(
                    409,
                    "result_context_unavailable",
                    _PUBLICATION_MESSAGES["result_context_unavailable"],
                )
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                legacy_view.close()
        launch_path = (
            _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
        )
        if not launch_path.is_file():
            return _error_response(
                404,
                "public_run_not_found",
                "未找到指定的监查运行。",
            )
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            publication = registry.get_publication(
                project_id=canonical, run_id=launch.run_id
            )
            if publication.publication_state != lr.PUBLICATION_STATE_AVAILABLE:
                return _error_response(
                    409,
                    "publication_not_available",
                    _PUBLICATION_MESSAGES["publication_not_available"],
                )
            if not publication.result_context_token:
                return _error_response(
                    409,
                    "result_context_unavailable",
                    _PUBLICATION_MESSAGES["result_context_unavailable"],
                )
            if (
                not publication.r5_authority_packet_digest
                or not publication.r5_authority_packet_id
            ):
                return _error_response(
                    409,
                    "authority_identity_mismatch",
                    _PUBLICATION_MESSAGES["authority_identity_mismatch"],
                )
            entry_candidate = _open_entry(
                _workspace_dir(root, canonical), allow_create=False
            )
            if isinstance(entry_candidate, JSONResponse):
                raise ProductPublicationError(
                    "runtime_read_failed", recoverable=True
                )
            entry = entry_candidate
            gate = _read_publication_gate(
                _workspace_dir(root, canonical),
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            if (
                gate["revision"] != publication.manifest_revision
                or gate["digest"] != publication.manifest_digest
                or gate["identity"]
                != dict(publication.runtime_manifest_identity)
                or tuple(gate["receipt_ids"])
                != tuple(publication.receipt_identities)
                or gate["receipt_set_digest"]
                != publication.receipt_set_digest
            ):
                raise ProductPublicationError("receipt_gate_blocked")
            (
                _,
                _,
                _,
                _,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_refs=publication.site_coverage,
                snapshot_token=publication.snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            if (
                packet.packet_identity != publication.r5_authority_packet_id
                or packet.packet_digest
                != publication.r5_authority_packet_digest
                or tuple(packet.site_refs) != publication.site_coverage
            ):
                return _error_response(
                    409,
                    "authority_identity_mismatch",
                    _PUBLICATION_MESSAGES["authority_identity_mismatch"],
                )
            if (
                publication.artifact_member_ids
                and publication.r6_output_set_digest
            ):
                runtime_dir = _workspace_dir(root, canonical) / RUNTIME_DIR_NAME
                db_path = runtime_dir / RUNTIME_DB_NAME
                artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
                if not db_path.is_file() or not artifact_dir.is_dir():
                    raise ProductPublicationError("receipt_gate_blocked")
                r1_store = Store(db_path, artifact_dir)
                try:
                    for member_id in publication.artifact_member_ids:
                        if not r1_store.verify_artifact(member_id):
                            raise ProductPublicationError("receipt_gate_blocked")
                finally:
                    r1_store.close()
            body = {
                "project_ref": canonical,
                "public_run_token": launch.public_run_token,
                "snapshot_token": publication.snapshot_token,
                "data_cutoff_text": publication.data_cutoff,
                "site_options": [
                    {
                        "site_ref": site_ref,
                        "site_label": f"中心 {site_ref}",
                    }
                    for site_ref in publication.site_coverage
                ],
                "result_context_token": publication.result_context_token,
            }
            if set(body) != {
                "project_ref",
                "public_run_token",
                "snapshot_token",
                "data_cutoff_text",
                "site_options",
                "result_context_token",
            }:
                return _error_response(500, "internal_error")
            return body
        except ProductPublicationError as exc:
            return _error_response(
                _status_for(exc.code),
                exc.code,
                _PUBLICATION_MESSAGES.get(
                    exc.code, _PUBLICATION_MESSAGES["authority_identity_mismatch"]
                ),
            )
        except lr.LaunchRegistryError as exc:
            if exc.code == "publication_not_found":
                return _error_response(
                    409,
                    "publication_not_available",
                    _PUBLICATION_MESSAGES["publication_not_available"],
                )
            return _launch_error_response(exc)
        finally:
            if entry is not None and not isinstance(entry, JSONResponse):
                entry.close()
            registry.close()

    @router.get("/runs/{run_id}")
    async def get_run(project_id: str, run_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                rows = [
                    row
                    for row in view.list_run_bindings()
                    if row.get("run_id") == run_id
                ]
                if not rows:
                    return _error_response(
                        404,
                        "run_binding_not_found",
                        chinese_message_for("run_binding_not_found"),
                    )
                return _legacy_binding_projection(rows[0])
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            return entry
        try:
            binding = entry.get_run(run_id)
            if str(binding.get("project_id", "")) != canonical:
                return _error_response(
                    404,
                    "run_binding_not_found",
                    chinese_message_for("run_binding_not_found"),
                )
            return _projection(binding)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()

    @router.api_route(
        "/{r7_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    async def unmatched_r7_route(r7_path: str) -> JSONResponse:
        del r7_path
        return _error_response(404, "route_not_found", _AUTH_MESSAGES["route_not_found"])

    return router


__all__ = [
    "ProductBackupRequest",
    "ProductContinuityChangeCounts",
    "ProductContinuityComparison",
    "ProductContinuityIdentity",
    "ProductContinuityResponse",
    "ProductContinuityRow",
    "ProductProjectUpgradeRequest",
    "ProjectOpenResult",
    "ProjectUpgradeProgress",
    "ProjectUpgradeResult",
    "ProductCreateRunRequest",
    "ProductExecutionActionRequest",
    "ProductRestorePreflightRequest",
    "ProductRestoreRequest",
    "ProductPublicationError",
    "ProductPublicationRequest",
    "ProductRiskRulePreviewRequest",
    "ProductRiskRuleRequest",
    "R7_PRODUCT_PREFIX",
    "R7_PRODUCT_SCHEMA",
    "R7_RISK_RULE_DB_NAME",
    "R7_WORKSPACE_ROOT_NAME",
    "create_medical_monitoring_r7_product_router",
]
