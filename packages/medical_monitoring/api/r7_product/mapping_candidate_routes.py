"""Project-scoped C3 mapping-candidate and confirmation routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

from fastapi import APIRouter, File, Query, Request, UploadFile
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
    "mapping_verifier_unconfigured": 503,
    "mapping_cohort_invalid": 422,
    "mapping_cohort_legacy_route": 409,
    "mapping_verifier_incomplete": 409,
    "mapping_reconciliation_required": 409,
    "mapping_draft_unconfigured": 503,
    "mapping_bridge_failed": 500,
    "mapping_document_evidence_resolver_unavailable": 503,
    "mapping_document_evidence_missing": 409,
    "mapping_document_evidence_incomplete": 422,
    "document_packet_project_mismatch": 409,
    "mapping_document_selection_invalid": 422,
    "mapping_document_selection_not_found_or_role_mismatch": 404,
    "mapping_document_selection_unusable": 409,
    "mapping_document_registration_unavailable": 503,
    "mapping_document_registration_invalid": 422,
    "mapping_document_selection_pending": 409,
    "mapping_document_refresh_pending": 409,
    "mapping_attempt_id_invalid": 422,
    "mapping_focus_invalid": 422,
    "mapping_run_incomplete": 409,
    "mapping_candidate_not_adoptable": 409,
    "mapping_draft_conflict": 409,
    "mapping_quality_blocked": 409,
    "mapping_draft_invalid": 422,
    "mapping_questions_unresolved": 422,
}

_MAPPING_MESSAGES = {
    "mapping_admission_not_found": "未找到对应的数据导入记录。请先完成数据导入后再生成字段对应建议。",
    "mapping_candidates_not_found": "尚未生成字段对应建议。请先发起生成。",
    "mapping_profile_not_ready": "数据结构识别尚未完成，暂时无法生成字段对应建议。请等待导入完成后再试。",
    "mapping_bridge_unconfigured": "系统识别服务暂不可用，请稍后重试。",
    "mapping_model_not_configured": "系统识别服务暂不可用，本次未发送数据。请稍后重试。",
    "mapping_verifier_unconfigured": "系统暂未完成复核准备，请稍后重试。",
    "mapping_cohort_invalid": "系统识别状态异常，请重新进入本页。",
    "mapping_cohort_legacy_route": (
        "此前的字段识别结果已过期，系统需要重新识别后才能继续。"
        "请点击重试。"
    ),
    "mapping_verifier_incomplete": "系统仍在复核，当前不需要您确认。",
    "mapping_reconciliation_required": "两次独立分析仍有实质差异，系统将先继续核实；当前不需要您逐项确认。",
    "mapping_draft_unconfigured": "系统暂时无法保存识别结果，请稍后重试。",
    "mapping_bridge_failed": "生成字段对应建议时出现问题，本次结果未保存。请重试；如再次失败请联系管理员。",
    "mapping_document_evidence_resolver_unavailable": (
        "研究文档识别服务尚未就绪，本次未发送数据。请稍后重试。"
    ),
    "mapping_document_evidence_missing": (
        "系统还没有完成研究方案和电子病例报告表的识别。"
        "请先补充这两类文件，系统会自行核对，无需逐字段确认。"
    ),
    "mapping_document_evidence_incomplete": (
        "研究方案或电子病例报告表尚未通过完整性核对。"
        "请按页面提示补充或更换文件，系统会自动重新识别。"
    ),
    "document_packet_project_mismatch": (
        "研究文档与当前项目不一致，本次未发送数据。请返回项目首页重新选择文件。"
    ),
    "mapping_document_selection_invalid": (
        "所选研究文档无效或已更新。请重新选择对应文件。"
    ),
    "mapping_document_selection_not_found_or_role_mismatch": (
        "未找到该文件，或文件类型与所选位置不符。请重新选择。"
    ),
    "mapping_document_selection_unusable": (
        "该文件已过期、不完整或未通过内容核对，暂时不能使用。"
    ),
    "mapping_document_registration_unavailable": (
        "研究文档导入服务尚未就绪，请稍后重试。"
    ),
    "mapping_document_registration_invalid": (
        "系统无法识别所选研究文件，请确认文件类型后重新添加。"
    ),
    "mapping_document_selection_pending": (
        "文件已保存，但系统暂未完成关联。请稍后重新添加该文件。"
    ),
    "mapping_document_refresh_pending": (
        "文件已保存，系统暂未完成状态更新。请点击“重新核对研究文件”，无需再次上传。"
    ),
    "mapping_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
    "mapping_focus_invalid": "筛选条件无效。请使用“重点优先”或“全部建议”。",
    "mapping_run_incomplete": "字段对应建议尚未完整完成，暂时不能进入确认。请等待生成完成或只重试失败部分。",
    "mapping_candidate_not_adoptable": "部分字段建议已不可采用。请重新生成建议后再确认。",
    "mapping_draft_conflict": "字段对应草稿发生冲突，本次未保存。请刷新后重试。",
    "mapping_quality_blocked": (
        "系统核对发现部分字段对应关系仍存在问题，暂时不能整体确认。"
        "请按系统提示修订对应字段后再确认。"
    ),
    "mapping_draft_invalid": "字段修订内容无效。请检查填写内容后重试。",
    "mapping_questions_unresolved": (
        "还有需要您确认的医学问题。请先逐条回答问题卡片"
        "（或在修订中给出对应关系和核对结论），再进行整体确认。"
    ),
}


class AdmissionMappingPipeline(Protocol):
    def generate_dual_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
    ) -> Mapping[str, Any]: ...

    def generate_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        cohort: str = "primary",
    ) -> Mapping[str, Any]: ...

    def list_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        cohort: str = "primary",
    ) -> Mapping[str, Any]: ...

    def select_document(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        role: str,
        source_entry_id: str,
    ) -> Mapping[str, Any]: ...

    def document_readiness(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
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


class MappingDraftAdjudicateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)


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
    automatic: bool = False


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
    monitoring_document_registrar: Any = None


def _mapping_error(code: str) -> JSONResponse:
    return _error_response(
        _MAPPING_STATUS_CODES.get(code, 500),
        code,
        _MAPPING_MESSAGES.get(code, "字段对应建议暂时不可用。"),
    )


_PUBLIC_SUMMARY_FIELDS = frozenset({
    "job_count",
    "completed_job_count",
    "candidate_count",
    "pending_confirmation_count",
    "field_count",
    "user_question_count",
    "critical_count",
    "displayed_count",
    "system_adopted_count",
    "system_adjudicated_count",
})
_PUBLIC_MAPPING_FIELD_FIELDS = frozenset({
    "domain",
    "source_field",
    "recommended_role",
    "field_kind",
    "confidence",
    "uncertainty",
    "user_action",
    "user_decision_required",
    "related_fields",
    "standards_reference",
    "derivation_lineage",
    "value_constraints",
    "object_identity",
    "dose_semantics",
    "quality_gate_actions",
    "attention_reason",
    "needs_attention",
    "question_text",
    "system_adopted",
    "confirmation_status",
    "evidence_summary",
})


def _public_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: value[key]
        for key in _PUBLIC_SUMMARY_FIELDS
        if key in value
    }


def _public_mapping_field(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: value[key]
        for key in _PUBLIC_MAPPING_FIELD_FIELDS
        if key in value
    }


def _public_draft(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    public = {
        key: value[key]
        for key in ("draft_id", "version", "status", "facts_generated")
        if key in value
    }
    public["fields"] = [
        _public_mapping_field(item) for item in value.get("fields") or ()
    ]
    public["user_questions"] = [
        _public_mapping_field(item)
        for item in value.get("user_questions") or ()
    ]
    if isinstance(value.get("semantic_quality"), Mapping):
        quality = value["semantic_quality"]
        public["semantic_quality"] = {
            key: quality[key]
            for key in (
                "status",
                "activation_disposition",
                "global_blocker_count",
                "capability_blocker_count",
                "warning_count",
            )
            if key in quality
        }
        public["semantic_quality"]["finding_groups"] = [
            {
                key: item[key]
                for key in (
                    "severity",
                    "title_zh",
                    "summary_zh",
                    "affected_capability_ids",
                )
                if key in item
            }
            for item in quality.get("finding_groups") or ()
            if isinstance(item, Mapping)
        ]
        public["semantic_quality"]["capability_states"] = [
            {
                key: item[key]
                for key in ("capability_id", "state")
                if key in item
            }
            for item in quality.get("capability_states") or ()
            if isinstance(item, Mapping)
        ]
    public["review_summary"] = _public_summary(value.get("review_summary"))
    return public


def _public_mapping_projection(
    payload: Mapping[str, Any],
) -> dict[str, Any] | JSONResponse:
    public = {
        key: payload[key]
        for key in (
            "state",
            "confirmation_status",
            "facts_generated",
            "next_action",
            "draft_id",
            "version",
            "status",
        )
        if key in payload
    }
    public["summary"] = _public_summary(payload.get("summary"))
    public["candidates"] = [
        _public_mapping_field(item) for item in payload.get("candidates") or ()
    ]
    if isinstance(payload.get("verification"), Mapping):
        public["verification"] = {
            "state": payload["verification"].get("state"),
            "summary": _public_summary(payload["verification"].get("summary")),
        }
    if isinstance(payload.get("draft"), Mapping):
        public["draft"] = _public_draft(payload["draft"])
    elif "fields" in payload or "user_questions" in payload:
        public.update(_public_draft(payload))
    if isinstance(payload.get("adjudication"), Mapping):
        public["adjudication"] = {
            key: payload["adjudication"][key]
            for key in (
                "state",
                "resolved_count",
                "remaining_question_count",
            )
            if key in payload["adjudication"]
        }
    forbidden = {
        "provider",
        "model",
        "source_entry_id",
        "sha256",
        "job_id",
        "candidate_id",
    }

    def contains_forbidden_key(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                any(token in str(key).lower() for token in forbidden)
                or contains_forbidden_key(item)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(contains_forbidden_key(item) for item in value)
        return False

    if contains_forbidden_key(public):
        return _mapping_error("mapping_bridge_failed")
    return public


def _repo_error_code(exc: Exception) -> Optional[str]:
    name = type(exc).__name__
    if "NotFound" in name:
        return "mapping_candidates_not_found"
    message = str(exc)
    if "mapping semantic quality gate is blocked" in message:
        return "mapping_quality_blocked"
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

    @router.post(
        "/data-admissions/{attempt_id}/study-documents",
        status_code=201,
    )
    async def register_mapping_document(
        project_id: str,
        attempt_id: str,
        request: Request,
        role: str = Query(...),
        file: UploadFile = File(...),
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
        if context.monitoring_document_registrar is None:
            return _mapping_error("mapping_document_registration_unavailable")
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            await file.close()
            return _run_entry_error_response(exc)
        try:
            content = await file.read(50 * 1024 * 1024 + 1)
            if not content or len(content) > 50 * 1024 * 1024:
                return _mapping_error("mapping_document_registration_invalid")
            result = context.monitoring_document_registrar(
                project_id=canonical,
                role=role,
                filename=file.filename or "",
                content=content,
            )
            source_entry_id = str(result.get("source_entry_id") or "").strip()
            if not source_entry_id:
                return _mapping_error("mapping_document_registration_invalid")
            workspace = context.workspace_dir(context.root, canonical)
            try:
                pipeline.select_document(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=workspace,
                    role=role,
                    source_entry_id=source_entry_id,
                )
            except AdmissionMappingPipelineError:
                raise
            except Exception:
                return _mapping_error("mapping_document_selection_pending")
            try:
                readiness = pipeline.document_readiness(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=workspace,
                )
            except Exception:
                return _mapping_error("mapping_document_refresh_pending")
            return {"project_id": canonical, **dict(readiness)}
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_document_registration_invalid")
        finally:
            await file.close()
            write_permit.release()

    @router.get("/data-admissions/{attempt_id}/study-documents")
    async def mapping_document_readiness(
        project_id: str,
        attempt_id: str,
        request: Request,
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
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        try:
            result = pipeline.document_readiness(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            return {"project_id": canonical, **dict(result)}
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_document_evidence_incomplete")

    @router.post("/data-admissions/{attempt_id}/mapping-candidates", status_code=201)
    async def generate_mapping_candidates(
        project_id: str,
        attempt_id: str,
        request: Request,
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
            workspace = context.workspace_dir(context.root, canonical)
            result = pipeline.generate_dual_candidates(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=workspace,
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
        cohort: str = Query(default="dual"),
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
            effective_cohort = "primary" if cohort == "dual" else cohort
            if confirmation is not None and effective_cohort == "primary":
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
                        cohort=effective_cohort,
                    ),
                    focus=focus,
                )
            if cohort == "dual":
                try:
                    verifier = pipeline.list_candidates(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=workspace,
                        cohort="verifier",
                    )
                    result = {
                        **dict(result),
                        "verification": {
                            "state": verifier.get("state"),
                            "summary": verifier.get("summary"),
                        },
                    }
                except AdmissionMappingPipelineError as exc:
                    if exc.code != "mapping_candidates_not_found":
                        raise
                    result = {
                        **dict(result),
                        "verification": {
                            "state": "waiting",
                            "summary": {"job_count": 0, "completed_job_count": 0},
                        },
                    }
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

    @router.post("/data-admissions/{attempt_id}/mapping-draft/adjudicate")
    async def adjudicate_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftAdjudicateRequest,
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
            result = confirmation.adjudicate_draft(
                project_id=canonical,
                attempt_id=validated_attempt,
                draft_id=body.draft_id,
                workspace_dir=context.workspace_dir(context.root, canonical),
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
        actor = (
            "system_harness"
            if body.automatic
            else getattr(auth, "principal_id", None) or body.confirmed_by
        )
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
                workspace_dir=context.workspace_dir(context.root, canonical),
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
    "MappingDraftAdjudicateRequest",
    "MappingDraftAdoptRequest",
    "MappingDraftConfirmRequest",
    "MappingDraftFieldEditRequest",
    "register_mapping_candidate_routes",
]
