"""Project-scoped C3 mapping-candidate and confirmation routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from ...admission.mapping_confirmation import enrich_candidates
from ...admission.mapping_pipeline import AdmissionMappingPipelineError
from ...admission.pipeline import AdmissionPipelineError
from ...runtime import project_backup as pb
from .errors import _error_response, _run_entry_error_response
from .admission_routes import _validated_attempt_id

MAPPING_CANDIDATE_SCHEMA_VERSION = "mm-c3-mapping-candidate-v1"
MAPPING_CONFIRMATION_SCHEMA_VERSION = "mm-c3-mapping-confirmation-v1"

_MAPPING_STATUS_CODES = {
    "mapping_admission_not_found": 404,
    "mapping_candidates_not_found": 404,
    "mapping_profile_not_ready": 409,
    "mapping_bridge_unconfigured": 503,
    "mapping_model_not_configured": 503,
    "mapping_draft_unconfigured": 503,
    "mapping_bridge_failed": 500,
    "mapping_attempt_id_invalid": 422,
    "mapping_focus_invalid": 422,
    "mapping_run_incomplete": 409,
    "mapping_candidate_not_adoptable": 409,
    "mapping_draft_conflict": 409,
    "mapping_draft_invalid": 422,
    "mapping_advice_incomplete": 422,
}

_MAPPING_MESSAGES = {
    "mapping_admission_not_found": "未找到对应的数据导入记录。请先完成数据导入后再生成字段对应建议。",
    "mapping_candidates_not_found": "尚未生成字段对应建议。请先发起生成。",
    "mapping_profile_not_ready": "数据结构识别尚未完成，暂时无法生成字段对应建议。请等待导入完成后再试。",
    "mapping_bridge_unconfigured": "字段对应服务尚未配置，暂时无法生成建议。请联系管理员完成配置后再试。",
    "mapping_model_not_configured": "字段识别模型尚未按当前项目要求完成配置，本次未发送数据。请完成模型配置后重试。",
    "mapping_draft_unconfigured": "字段对应确认服务尚未配置，暂时无法进入修订。请联系管理员完成配置后再试。",
    "mapping_bridge_failed": "生成字段对应建议时出现问题，本次结果未保存。请重试；如再次失败请联系管理员。",
    "mapping_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
    "mapping_focus_invalid": "筛选条件无效。请使用“重点优先”或“全部建议”。",
    "mapping_run_incomplete": "字段对应建议尚未完整完成，暂时不能进入确认。请等待生成完成或只重试失败部分。",
    "mapping_candidate_not_adoptable": "部分字段建议已不可采用。请重新生成建议后再确认。",
    "mapping_draft_conflict": "字段对应草稿发生冲突，本次未保存。请刷新后重试。",
    "mapping_draft_invalid": "字段修订内容无效。请检查填写内容后重试。",
    "mapping_advice_incomplete": "还有字段缺少具体的中文核对建议。请补充后再整体确认。",
}


class AdmissionMappingPipeline(Protocol):
    def generate_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Any
    ) -> Mapping[str, Any]: ...

    def list_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Any
    ) -> Mapping[str, Any]: ...


class MappingDraftAdoptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2_000)
    actor: str = Field(default="medical_manager", min_length=2, max_length=160)


class MappingDraftFieldEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)
    domain: str = Field(min_length=1, max_length=80)
    source_field: str = Field(min_length=1, max_length=240)
    patch: dict[str, Any]
    expected_version: StrictInt = Field(ge=1)
    actor: str = Field(default="medical_manager", min_length=2, max_length=160)
    idempotency_key: str = Field(min_length=2, max_length=240)


class MappingDraftConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)
    expected_version: StrictInt = Field(ge=1)
    confirmed_by: str = Field(
        default="medical_manager",
        min_length=2,
        max_length=160,
    )
    confirmation_reason: str = Field(min_length=10, max_length=2_000)
    idempotency_key: str = Field(min_length=2, max_length=240)


@dataclass(frozen=True)
class MappingCandidateRouteContext:
    root: Any
    resolve_project: Any
    authorize: Any
    acquire_product_write_gate: Any
    workspace_dir: Any
    monitoring_action: Any
    admission_mapping_pipeline: Any
    admission_mapping_confirmation: Any = None


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


def _repo_error_code(exc: Exception) -> Optional[str]:
    name = type(exc).__name__
    if "NotFound" in name:
        return "mapping_candidates_not_found"
    if "Conflict" in name or "StateConflict" in name:
        return "mapping_draft_conflict"
    if "DraftError" in name or isinstance(exc, ValueError):
        return "mapping_draft_invalid"
    return None


def register_mapping_candidate_routes(
    router: APIRouter,
    context: MappingCandidateRouteContext,
) -> None:
    def _pipeline_or_error() -> Any:
        pipeline = context.admission_mapping_pipeline
        if pipeline is None:
            return _mapping_error("mapping_bridge_unconfigured")
        return pipeline

    def _confirmation_or_error() -> Any:
        service = context.admission_mapping_confirmation
        if service is None:
            return _mapping_error("mapping_draft_unconfigured")
        return service

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
        project_id: str,
        attempt_id: str,
        request: Request,
        focus: str = Query(default="critical"),
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
            confirmation = context.admission_mapping_confirmation
            workspace = context.workspace_dir(context.root, canonical)
            if confirmation is not None:
                result = confirmation.list_for_review(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=workspace,
                    focus=focus,
                )
            else:
                result = enrich_candidates(
                    pipeline.list_candidates(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=workspace,
                    ),
                    focus=focus,
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

    @router.post(
        "/data-admissions/{attempt_id}/mapping-draft",
        status_code=201,
    )
    async def adopt_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftAdoptRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = getattr(auth, "principal_id", None) or body.actor
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = confirmation.adopt_draft(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=context.workspace_dir(context.root, canonical),
                actor=str(actor),
                reason=body.reason,
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                "attempt_id": validated_attempt,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.patch("/data-admissions/{attempt_id}/mapping-draft/field")
    async def edit_mapping_draft_field(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftFieldEditRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = getattr(auth, "principal_id", None) or body.actor
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = confirmation.edit_field(
                project_id=canonical,
                attempt_id=validated_attempt,
                draft_id=body.draft_id,
                domain=body.domain,
                source_field=body.source_field,
                patch=body.patch,
                expected_version=body.expected_version,
                actor=str(actor),
                idempotency_key=body.idempotency_key,
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.post("/data-admissions/{attempt_id}/mapping-draft/confirm")
    async def confirm_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftConfirmRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = getattr(auth, "principal_id", None) or body.confirmed_by
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = confirmation.confirm_draft(
                project_id=canonical,
                attempt_id=validated_attempt,
                draft_id=body.draft_id,
                expected_version=body.expected_version,
                confirmed_by=str(actor),
                confirmation_reason=body.confirmation_reason,
                idempotency_key=body.idempotency_key,
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()


__all__ = [
    "AdmissionMappingPipeline",
    "MAPPING_CANDIDATE_SCHEMA_VERSION",
    "MAPPING_CONFIRMATION_SCHEMA_VERSION",
    "MappingCandidateRouteContext",
    "MappingDraftAdoptRequest",
    "MappingDraftConfirmRequest",
    "MappingDraftFieldEditRequest",
    "register_mapping_candidate_routes",
]
