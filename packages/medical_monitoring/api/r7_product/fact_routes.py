"""Thin product routes for deterministic C3 fact materialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...admission.fact_materialization import FactMaterializationError
from ...runtime import project_backup as pb
from .admission_routes import _validated_attempt_id
from .errors import _error_response, _run_entry_error_response

FACT_ROUTE_SCHEMA_VERSION = "mm-c3-fact-materialization-v2"

_STATUS = {
    "facts_admission_not_found": 404,
    "facts_mapping_not_confirmed": 409,
    "facts_mapping_conflict": 409,
    "facts_mapping_incomplete": 409,
    "facts_snapshot_incomplete": 409,
    "facts_snapshot_state_invalid": 409,
    "facts_snapshot_digest_mismatch": 409,
    "facts_locator_invalid": 409,
    "facts_attempt_id_invalid": 422,
    "facts_service_unconfigured": 503,
    "facts_generation_failed": 500,
}

_MESSAGES = {
    "facts_admission_not_found": "未找到对应的数据导入记录。请重新进入本次数据接入。",
    "facts_mapping_not_confirmed": "字段对应尚未确认，系统会先完成字段识别再生成监查数据。",
    "facts_mapping_conflict": "字段对应与本次导入不一致，本次未生成监查数据。请刷新后重试。",
    "facts_mapping_incomplete": "仍有字段没有明确处理方式，本次未生成监查数据。请让系统重新识别。",
    "facts_snapshot_incomplete": "本次导入的数据表不完整，本次未生成监查数据。请重新导入。",
    "facts_snapshot_state_invalid": "数据版本状态不一致，本次未生成监查数据。请刷新后重试。",
    "facts_snapshot_digest_mismatch": "数据副本校验未通过，本次未生成监查数据，原始文件未受影响。",
    "facts_locator_invalid": "系统无法精确定位部分原始单元格，本次未生成监查数据，原始文件未受影响。",
    "facts_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
    "facts_service_unconfigured": "监查数据生成服务尚未配置，请联系管理员。",
    "facts_generation_failed": "生成监查数据时出现问题，本次操作未完成，原始数据未受影响。请重试。",
}


@dataclass(frozen=True)
class FactRouteContext:
    root: Any
    resolve_project: Any
    authorize: Any
    acquire_product_write_gate: Any
    workspace_dir: Any
    monitoring_action: Any
    fact_materializer: Any


def _fact_error(code: str) -> JSONResponse:
    return _error_response(
        _STATUS.get(code, 500),
        code,
        _MESSAGES.get(code, _MESSAGES["facts_generation_failed"]),
    )


def register_fact_routes(router: APIRouter, context: FactRouteContext) -> None:
    def _service() -> Any:
        return context.fact_materializer or _fact_error("facts_service_unconfigured")

    @router.post("/data-admissions/{attempt_id}/facts", status_code=201)
    async def materialize_facts(project_id: str, attempt_id: str, request: Request) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        service = _service()
        if isinstance(service, JSONResponse):
            return service
        validated = _validated_attempt_id(attempt_id)
        if validated is None:
            return _fact_error("facts_attempt_id_invalid")
        try:
            permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = service.materialize(
                project_id=canonical,
                attempt_id=validated,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            return {"project_id": canonical, **dict(result), "schema_version": FACT_ROUTE_SCHEMA_VERSION}
        except FactMaterializationError as exc:
            return _fact_error(exc.code)
        except Exception:
            return _fact_error("facts_generation_failed")
        finally:
            permit.release()

    @router.get("/data-admissions/{attempt_id}/facts")
    async def fact_status(project_id: str, attempt_id: str, request: Request) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        service = _service()
        if isinstance(service, JSONResponse):
            return service
        validated = _validated_attempt_id(attempt_id)
        if validated is None:
            return _fact_error("facts_attempt_id_invalid")
        try:
            result = service.status(
                project_id=canonical,
                attempt_id=validated,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            return {"project_id": canonical, **dict(result), "schema_version": FACT_ROUTE_SCHEMA_VERSION}
        except FactMaterializationError as exc:
            return _fact_error(exc.code)
        except Exception:
            return _fact_error("facts_generation_failed")
