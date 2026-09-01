"""Isolated R7 Slice-02 FastAPI surface over :mod:`mm_r7.run_entry`."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, List, Literal, Mapping, Optional, Union

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .run_entry import MonitoringRunEntry, RunEntryError

API_PREFIX = "/api/medical-monitoring/r7"
API_SCHEMA = "mm-r7-product-api-v1"

_MESSAGES = {
    "request_validation_failed": "请求参数不符合约定，请检查字段与取值。",
    "forbidden_secret_field": "请求包含禁止的机密字段，已拒绝。",
    "credential_ref_must_not_be_secret_value": "凭据引用不得写成凭据值本身。",
    "unknown_override_field": "包含未知的执行配置字段。",
    "unknown_request_field": "请求包含不支持的字段。",
    "empty_override_payload": "执行配置内容不能为空。",
    "profile_layer_not_found": "未找到指定的执行配置。",
    "run_binding_not_found": "未找到指定的监查运行绑定。",
    "global_default_missing": "请先完成工作区初始化。",
    "conflicting_replay": "同一运行标识的输入与已有绑定冲突，拒绝覆盖。",
    "conflicting_replay_effective_profile": "同一运行标识已绑定不同执行配置，拒绝覆盖。",
    "conflicting_replay_data_identity": "同一运行标识已绑定不同数据版本，拒绝覆盖。",
    "incremental_requires_prior_accepted_snapshot_ref": "增量运行必须引用先前已接受的快照。",
    "full_forbids_prior_accepted_snapshot_ref": "全量运行不得携带先前已接受快照引用。",
    "unknown_mode": "不支持的监查运行模式。",
    "unknown_execution_basis": "不支持的运行基准。",
    "invalid_run_id": "运行标识无效。",
    "invalid_project_id": "项目标识无效。",
    "invalid_data_cutoff": "数据截止标识无效。",
    "invalid_source_revision_id": "数据源修订标识无效。",
    "empty_or_illegal_scope_key": "配置范围标识无效。",
    "internal_error": "运行入口处理失败。",
}
_NOT_FOUND = {"profile_layer_not_found", "run_binding_not_found"}
_CONFLICT = {
    "conflicting_replay",
    "conflicting_replay_effective_profile",
    "conflicting_replay_data_identity",
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


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BootstrapRequest(_StrictModel):
    pass


class ProfileFieldsRequest(_StrictModel):
    profile_id: Optional[str] = None
    profile_revision: Optional[str] = None
    capability_id: Optional[str] = None
    requested_provider: Optional[str] = None
    requested_model: Optional[str] = None
    user_config_name: Optional[str] = None
    effective_selector: Optional[str] = None
    reasoning_effort: Optional[str] = None
    timeout_seconds: Optional[int] = Field(default=None, gt=0)
    allowed_tools: Optional[List[str]] = None
    context_isolation: Optional[str] = None
    credential_ref: Optional[str] = None
    adapter_id: Optional[str] = None
    adapter_version: Optional[str] = None
    fallback_profile_ids: Optional[List[str]] = None

    @field_validator("credential_ref")
    @classmethod
    def validate_credential_ref(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and _SECRET_VALUE.search(value):
            raise ValueError("credential_ref_must_not_be_secret_value")
        return value

    def fields(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class CreateRunRequest(_StrictModel):
    run_id: str
    project_id: str
    mode: Literal["daily", "pre_lock", "post_lock_pre_cfdi"]
    execution_basis: Literal["full", "incremental"]
    data_cutoff: str
    source_revision_id: str
    prior_accepted_snapshot_ref: Optional[str] = None
    capability_scope_key: str = ""
    project_scope_key: str = ""
    run_override_scope_key: str = ""

    @field_validator("run_id", "project_id", "data_cutoff", "source_revision_id")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError("invalid_identity")
        return value

    @field_validator("prior_accepted_snapshot_ref")
    @classmethod
    def validate_prior_ref(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("invalid_prior_accepted_snapshot_ref")
        return value


class ErrorBody(_StrictModel):
    code: str
    message: str


EntryProvider = Union[MonitoringRunEntry, Callable[[], MonitoringRunEntry]]


def chinese_message_for(code: str) -> str:
    return _MESSAGES.get(code, "请求未能完成，请检查输入后重试。")


def _status(code: str) -> int:
    if code in _NOT_FOUND:
        return 404
    if code in _CONFLICT:
        return 409
    if code == "internal_error":
        return 500
    return 422


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, RunEntryError):
        code = exc.code
        message = exc.message
    else:
        code = "internal_error"
        message = _MESSAGES[code]
    if _SECRET_VALUE.search(str(message)):
        code, message = "forbidden_secret_field", _MESSAGES["forbidden_secret_field"]
    return HTTPException(_status(code), detail={"code": code, "message": message})


def _projection(result: Any, *, replayed: bool = False) -> dict[str, Any]:
    if isinstance(result, Mapping):
        body = dict(result)
    else:
        value = getattr(result, "profile", None)
        if not isinstance(value, Mapping):
            value = getattr(result, "binding", None)
        if not isinstance(value, Mapping):
            raise HTTPException(500, detail={"code": "internal_error", "message": _MESSAGES["internal_error"]})
        body = dict(value)
        if replayed:
            body["replayed"] = bool(getattr(result, "replayed"))
    lowered_keys = {str(key).lower() for key in body}
    if lowered_keys & _FORBIDDEN_PUBLIC:
        raise HTTPException(500, detail={"code": "internal_error", "message": _MESSAGES["internal_error"]})
    blob = json.dumps(body, ensure_ascii=False)
    if _SECRET_VALUE.search(blob) or "credential_value" in blob.lower():
        raise HTTPException(500, detail={"code": "internal_error", "message": _MESSAGES["internal_error"]})
    return body


def _invoke(provider: EntryProvider, method: str, *args: Any, **kwargs: Any) -> Any:
    owned = callable(provider)
    entry = provider() if owned else provider
    try:
        return getattr(entry, method)(*args, **kwargs)
    finally:
        if owned:
            entry.close()


def create_router(entry: EntryProvider) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX, tags=["medical-monitoring-r7"])

    @router.post("/workspace/bootstrap")
    def bootstrap(_: Optional[BootstrapRequest] = None) -> dict[str, Any]:
        try:
            return _projection(_invoke(entry, "bootstrap_workspace"), replayed=True)
        except HTTPException:
            raise
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.post("/execution-profiles/{layer_kind}/{scope_key}")
    def append_profile(
        layer_kind: Literal["global_default", "capability_agent", "project", "run_override"],
        scope_key: str,
        body: ProfileFieldsRequest,
    ) -> dict[str, Any]:
        fields = body.fields()
        if not fields:
            raise HTTPException(422, detail={"code": "empty_override_payload", "message": _MESSAGES["empty_override_payload"]})
        try:
            return _projection(_invoke(entry, "append_execution_profile", layer_kind, scope_key, fields))
        except HTTPException:
            raise
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.get("/execution-profiles/{layer_kind}/{scope_key}")
    def get_profile(
        layer_kind: Literal["global_default", "capability_agent", "project", "run_override"],
        scope_key: str,
    ) -> dict[str, Any]:
        try:
            return _projection(_invoke(entry, "get_execution_profile", layer_kind, scope_key))
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.post("/runs")
    def bind_run(body: CreateRunRequest) -> dict[str, Any]:
        try:
            return _projection(_invoke(entry, "bind_run", **body.model_dump()), replayed=True)
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        try:
            return _projection(_invoke(entry, "get_run", run_id))
        except Exception as exc:
            raise _http_error(exc) from exc

    return router


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(_, exc: RequestValidationError) -> JSONResponse:
        locations = {str(part).lower() for error in exc.errors() for part in error.get("loc", ())}
        messages = " ".join(str(error.get("msg", "")) for error in exc.errors())
        if locations & _SECRET_FIELDS:
            code = "forbidden_secret_field"
        elif "credential_ref_must_not_be_secret_value" in messages:
            code = "credential_ref_must_not_be_secret_value"
        elif any(error.get("type") == "extra_forbidden" for error in exc.errors()):
            code = "unknown_request_field"
        else:
            code = "request_validation_failed"
        return JSONResponse(
            status_code=422,
            content={"code": code, "message": chinese_message_for(code)},
        )

    @app.exception_handler(HTTPException)
    async def http_error(_, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and {"code", "message"} <= exc.detail.keys():
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": _MESSAGES["internal_error"]},
        )


def create_isolated_app(entry: EntryProvider) -> FastAPI:
    app = FastAPI(title="mm-r7-isolated-api", version="0.2")
    install_exception_handlers(app)
    app.include_router(create_router(entry))
    return app


def create_router_from_run_entry(workspace_dir: Union[str, Path]) -> APIRouter:
    """Build the low-level router; the host app must install error handlers."""
    root = Path(workspace_dir)
    return create_router(lambda: MonitoringRunEntry(root))


def create_isolated_app_from_run_entry(workspace_dir: Union[str, Path]) -> FastAPI:
    """Build the complete isolated app with Chinese error envelopes."""
    root = Path(workspace_dir)
    return create_isolated_app(lambda: MonitoringRunEntry(root))


__all__ = [
    "API_PREFIX",
    "API_SCHEMA",
    "BootstrapRequest",
    "CreateRunRequest",
    "EntryProvider",
    "ErrorBody",
    "ProfileFieldsRequest",
    "chinese_message_for",
    "create_isolated_app",
    "create_isolated_app_from_run_entry",
    "create_router",
    "create_router_from_run_entry",
    "install_exception_handlers",
]
