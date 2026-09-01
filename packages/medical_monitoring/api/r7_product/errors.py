"""Stable Chinese error envelopes for the R7 product API."""

from __future__ import annotations

from typing import Optional

from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ...runtime import launch_registry as lr
from ...runtime import project_backup as pb
from ...runtime import run_setup as rs
from ...runtime.migration import MigrationError
from ...runtime.project_lifecycle import ProjectCompatibilityError
from ...runtime.run_entry import RunEntryError
from ...runtime.runtime_progress import RuntimeProgressError
from ..run_entry import chinese_message_for
from .public_text import _SECRET_FIELDS, _SECRET_VALUE
from .result_projections import _PUBLICATION_MESSAGES

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

def _launch_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, lr.LaunchRegistryError):
        return _error_response(_status_for(exc.code), exc.code, exc.message)
    return _error_response(500, "internal_error")

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

__all__ = [
    "_NOT_FOUND",
    "_CONFLICT",
    "_BACKUP_NOT_FOUND",
    "_BACKUP_CONFLICT",
    "_BACKUP_INTERNAL",
    "_EXECUTION_STATE_CONFLICT",
    "_AUTH_MESSAGES",
    "_RUNTIME_MESSAGES",
    "_status_for",
    "_error_response",
    "_run_entry_error_response",
    "_launch_error_response",
    "_validation_error_response",
]
