"""Project-scoped C3 mapping-candidate routes for admitted listings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...admission.mapping_pipeline import AdmissionMappingPipelineError
from ...admission.pipeline import AdmissionPipelineError
from ...runtime import project_backup as pb
from .errors import _error_response, _run_entry_error_response
from .admission_routes import _validated_attempt_id

MAPPING_CANDIDATE_SCHEMA_VERSION = "mm-c3-mapping-candidate-v1"

_MAPPING_STATUS_CODES = {
    "mapping_admission_not_found": 404,
    "mapping_candidates_not_found": 404,
    "mapping_profile_not_ready": 409,
    "mapping_bridge_unconfigured": 503,
    "mapping_model_not_configured": 503,
    "mapping_bridge_failed": 500,
    "mapping_attempt_id_invalid": 422,
}

_MAPPING_MESSAGES = {
    "mapping_admission_not_found": "未找到对应的数据导入记录。请先完成数据导入后再生成字段对应建议。",
    "mapping_candidates_not_found": "尚未生成字段对应建议。请先发起生成。",
    "mapping_profile_not_ready": "数据结构识别尚未完成，暂时无法生成字段对应建议。请等待导入完成后再试。",
    "mapping_bridge_unconfigured": "字段对应服务尚未配置，暂时无法生成建议。请联系管理员完成配置后再试。",
    "mapping_model_not_configured": "字段识别模型尚未按当前项目要求完成配置，本次未发送数据。请完成模型配置后重试。",
    "mapping_bridge_failed": "生成字段对应建议时出现问题，本次结果未保存。请重试；如再次失败请联系管理员。",
    "mapping_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
}


class AdmissionMappingPipeline(Protocol):
    def generate_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Any
    ) -> Mapping[str, Any]: ...

    def list_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Any
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class MappingCandidateRouteContext:
    root: Any
    resolve_project: Any
    authorize: Any
    acquire_product_write_gate: Any
    workspace_dir: Any
    monitoring_action: Any
    admission_mapping_pipeline: Any


def _mapping_error(code: str) -> JSONResponse:
    return _error_response(
        _MAPPING_STATUS_CODES.get(code, 500),
        code,
        _MAPPING_MESSAGES.get(code, "字段对应建议暂时不可用。"),
    )


def _public_mapping_projection(payload: Mapping[str, Any]) -> dict[str, Any] | JSONResponse:
    forbidden = {
        "canonical_fact",
        "mapping_definition",
        "mapping_result",
        "traceback",
        "sqlite",
        "source_dir",
        "db_path",
    }
    blob = str(payload).lower()
    for token in forbidden:
        if token in blob:
            return _mapping_error("mapping_bridge_failed")
    return dict(payload)


def register_mapping_candidate_routes(
    router: APIRouter,
    context: MappingCandidateRouteContext,
) -> None:
    def _pipeline_or_error() -> Any:
        pipeline = context.admission_mapping_pipeline
        if pipeline is None:
            return _mapping_error("mapping_bridge_unconfigured")
        return pipeline

    @router.post("/data-admissions/{attempt_id}/mapping-candidates", status_code=201)
    async def generate_mapping_candidates(
        project_id: str, attempt_id: str, request: Request
    ) -> Any:
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
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = pipeline.generate_candidates(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CANDIDATE_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except AdmissionPipelineError:
            return _mapping_error("mapping_admission_not_found")
        except Exception:
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.get("/data-admissions/{attempt_id}/mapping-candidates")
    async def list_mapping_candidates(
        project_id: str, attempt_id: str, request: Request
    ) -> Any:
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
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            result = pipeline.list_candidates(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CANDIDATE_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_bridge_failed")


__all__ = [
    "AdmissionMappingPipeline",
    "MAPPING_CANDIDATE_SCHEMA_VERSION",
    "MappingCandidateRouteContext",
    "register_mapping_candidate_routes",
]
