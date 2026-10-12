"""R37轮（R37-02）：多文档同批核对的确定性归并回归。

R37B实测（report_C.md发现1）：同一项目上传方案docx+eCRF docx一次核对时，
独立模型把「每个角色/每份文件的决定」输出成多个候选，单候选契约
fail-closed拒绝（invalid_ai_output: document authority review requires
exactly one candidate），4次失败错误原文一致；单文件对照实验通过。而映射
生成又要求方案+eCRF配齐——两文档同批核对必败、单文档必配不齐，真实材料
无任何出路。

修复：`_normalize_document_authority_provider_output` 新增确定性归并——
全部候选的structured_payload均能按本任务模型解析、身份字段彼此一致、按
身份键（candidate_id/role）严格不相交时拼接为单候选并留痕；任何解析失败、
身份不一致或键重叠原样返回，照旧fail-closed。归并后下游全部内容校验不变。
"""

from __future__ import annotations

import hashlib
import json
import types

import pytest
from pydantic import ValidationError

from packages.medical_monitoring.admission.document_authority import (
    CandidateAssessment,
    ConflictDecision,
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    DocumentAuthorityAnalysis,
    DocumentAuthorityConflictReview,
    RoleSelection,
    StudyIdentityAssessment,
    StudyIdentityEvidenceReference,
    document_authority_batch_sha256,
    validate_document_authority_analysis,
)
from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_service import (
    MonitoringAiOutputValidationError,
    MonitoringAiService,
    TASK_CANDIDATE_TYPES,
)


def _digest(value: object) -> str:
    if isinstance(value, dict) and "candidates" in value:
        value = {
            **value,
            "candidates": sorted(
                value["candidates"], key=lambda item: item["candidate_id"]
            ),
        }
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _batch() -> dict:
    return {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_r37",
        "authority_status": "not_adjudicated",
        "candidates": [
            {
                "candidate_id": "candidate_protocol",
                "filename": "protocol.docx",
                "role_hypotheses": ["protocol"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 1,
                "excerpts": [{"locator": "doc:p1", "text": "研究方案"}],
                "sheets": [],
            },
            {
                "candidate_id": "candidate_ecrf",
                "filename": "ecrf.docx",
                "role_hypotheses": ["ecrf"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 1,
                "excerpts": [],
                "sheets": [{"locator": "xlsx:sheet:1", "sheet_name": "AE"}],
            },
        ],
    }


def _job(task_type: MonitoringAiTaskType) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        task_type=task_type,
        job_id="job_r37_1",
        input_revision_sha256="a" * 64,
    )


def _analysis_candidate(
    batch: dict,
    *,
    assessments: tuple,
    selections: tuple,
    study_identity: StudyIdentityAssessment | None = None,
) -> dict:
    payload = DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=batch["batch_id"],
        input_sha256=_digest(batch),
        candidate_assessments=assessments,
        role_selections=selections,
        study_identity=study_identity or StudyIdentityAssessment(),
    )
    return {
        "candidate_type": TASK_CANDIDATE_TYPES[
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS
        ][0],
        "title": "研究文件识别结果",
        "text": "基于冻结文件完成识别。",
        "structured_payload": payload.model_dump(mode="json"),
    }


def _protocol_only_candidate(batch: dict) -> dict:
    return _analysis_candidate(
        batch,
        assessments=(
            CandidateAssessment(
                candidate_id="candidate_protocol",
                inferred_role="protocol",
                usable=True,
                confidence=0.98,
                evidence_locators=("doc:p1",),
            ),
        ),
        selections=(
            RoleSelection(
                role="protocol",
                decision="selected",
                selected_candidate_id="candidate_protocol",
                confidence=0.98,
                evidence_locators=("doc:p1",),
                supplementary_bindings=(),
            ),
        ),
    )


def _ecrf_only_candidate(batch: dict) -> dict:
    return _analysis_candidate(
        batch,
        assessments=(
            CandidateAssessment(
                candidate_id="candidate_ecrf",
                inferred_role="ecrf",
                usable=True,
                confidence=0.97,
                evidence_locators=("xlsx:sheet:1",),
            ),
        ),
        selections=(
            RoleSelection(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                confidence=0.97,
                evidence_locators=("xlsx:sheet:1",),
                supplementary_bindings=(),
            ),
        ),
    )


def _envelope(job: object, candidates: list[dict]) -> dict:
    return {
        "schema_version": MONITORING_AI_SCHEMA_VERSION,
        "task_id": job.job_id,
        "task_type": job.task_type.value,
        "input_revision_sha256": job.input_revision_sha256,
        "candidates": candidates,
    }


def _review_candidate(
    batch: dict,
    *,
    decision_roles: tuple,
) -> dict:
    decisions = tuple(
        ConflictDecision(
            role=role,
            decision="selected",
            selected_candidate_id="candidate_protocol"
            if role == "protocol"
            else "candidate_ecrf",
            document_version="V1.0",
            document_date="2026-01-01",
            confidence=0.95,
            considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
            supplementary_candidate_ids=(),
            evidence_references=(
                {
                    "candidate_id": "candidate_protocol"
                    if role == "protocol"
                    else "candidate_ecrf",
                    "locator": "doc:p1" if role == "protocol" else "xlsx:sheet:1",
                },
            ),
        )
        for role in decision_roles
    )
    payload = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=document_authority_batch_sha256(batch),
        decisions=decisions,
    )
    return {
        "candidate_type": TASK_CANDIDATE_TYPES[
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW
        ][0],
        "title": "研究文件冲突复核",
        "text": "基于匿名冻结证据完成复核。",
        "structured_payload": payload.model_dump(mode="json"),
    }


def test_analysis_multi_candidate_split_by_document_is_deterministically_joined() -> None:
    """按文档拆分的两个分析候选（角色不相交）应归并回单候选。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    notes: list[dict] = []
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _envelope(
            job,
            [
                _protocol_only_candidate(batch),
                _ecrf_only_candidate(batch),
            ],
        ),
        notes,
    )
    assert merged is not None
    assert len(merged["candidates"]) == 1
    payload = merged["candidates"][0]["structured_payload"]
    analysis = DocumentAuthorityAnalysis.model_validate(payload)
    assert {item.candidate_id for item in analysis.candidate_assessments} == {
        "candidate_protocol",
        "candidate_ecrf",
    }
    assert {item.role for item in analysis.role_selections} == {
        "protocol",
        "ecrf",
    }
    assert notes and notes[0]["normalization"] == (
        "document_authority_multi_candidate_deterministically_joined"
    )


def test_analysis_merge_with_single_non_default_study_identity_adopts_it() -> None:
    """身份结论只出现在一个拆分候选时照常归并（默认空结论是中性项）。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    batch["project_context"] = build_project_context()
    identity = StudyIdentityAssessment(
        status="aligned",
        project_context_sha256=batch["project_context"]["context_sha256"],
        evidence_references=(
            StudyIdentityEvidenceReference(
                candidate_id="candidate_protocol",
                locator="doc:p1",
            ),
        ),
        rationale="方案正文研究编号与项目登记一致。",
    )
    protocol_candidate = _protocol_only_candidate(batch)
    protocol_candidate["structured_payload"]["study_identity"] = (
        identity.model_dump(mode="json")
    )
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _envelope(job, [protocol_candidate, _ecrf_only_candidate(batch)]),
    )
    assert merged is not None
    assert (
        merged["candidates"][0]["structured_payload"]["study_identity"]["status"]
        == "aligned"
    )


def build_project_context() -> dict:
    from packages.medical_monitoring.admission.document_authority import (
        build_document_authority_project_context,
    )

    return build_document_authority_project_context({
        "project_id": "proj_r37",
        "project_code": "MG-K10-R37-001",
        "project_name": "MG-K10研究",
        "indication": "慢性自发性荨麻疹",
        "product_name": "MG-K10人源化单抗注射液",
        "study_phase": "III期",
        "protocol_id": "MG-K10-R37-001",
        "protocol_version": "V1.0",
        "protocol_date": "2026-01-01",
    })


def test_analysis_merge_refuses_overlapping_roles_and_stays_fail_closed() -> None:
    """两个候选都选了protocol角色（键重叠）→ 不归并，单候选契约照旧拒绝。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    output = _envelope(
        job,
        [
            _protocol_only_candidate(batch),
            _protocol_only_candidate(batch),
        ],
    )
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        output,
    )
    # 不归并时归一化器原样返回原输出（候选数不变），由既有单候选契约拒绝。
    assert merged is not None
    assert len(merged["candidates"]) == 2
    assert len(merged["candidates"][0]["structured_payload"]["role_selections"]) == 1
    parsed = types.SimpleNamespace(candidates=merged["candidates"])
    with pytest.raises(
        MonitoringAiOutputValidationError,
        match="requires exactly one candidate",
    ):
        MonitoringAiService._validate_task_specific_output(
            _service_stub(),
            _as_job(job),
            parsed,
            {},
        )


def test_review_multi_candidate_split_by_role_is_deterministically_joined() -> None:
    """按角色拆分的两个复核候选应归并回单候选（conflict_packet一致）。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW)
    batch = _batch()
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _envelope(
            job,
            [
                _review_candidate(batch, decision_roles=("protocol",)),
                _review_candidate(batch, decision_roles=("ecrf",)),
            ],
        ),
    )
    assert merged is not None
    assert len(merged["candidates"]) == 1
    review = DocumentAuthorityConflictReview.model_validate(
        merged["candidates"][0]["structured_payload"]
    )
    assert {item.role for item in review.decisions} == {"protocol", "ecrf"}


def test_review_merge_refuses_conflicting_packet_hashes() -> None:
    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW)
    batch = _batch()
    first = _review_candidate(batch, decision_roles=("protocol",))
    second = _review_candidate(batch, decision_roles=("ecrf",))
    second["structured_payload"]["conflict_packet_sha256"] = "b" * 64
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _envelope(job, [first, second]),
    )
    # 身份哈希不一致 → 不归并，原样返回（单候选契约照旧拒绝）。
    assert merged is not None
    assert len(merged["candidates"]) == 2


def test_merged_analysis_still_passes_full_content_validation() -> None:
    """归并产物必须仍通过既有全量内容校验（fail-closed边界不后移）。"""

    batch = _batch()
    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _envelope(
            job,
            [
                _protocol_only_candidate(batch),
                _ecrf_only_candidate(batch),
            ],
        ),
    )
    assert merged is not None
    analysis = DocumentAuthorityAnalysis.model_validate(
        merged["candidates"][0]["structured_payload"]
    )
    # 全量内容校验要求四类角色完整覆盖：拆分候选只覆盖2角色，因此
    # validate 必须拒绝（本断言守住「归并没有放松内容门」）。
    with pytest.raises(Exception, match="document_authority_role_coverage_invalid"):
        validate_document_authority_analysis(batch, analysis)


def _as_job(job: types.SimpleNamespace) -> types.SimpleNamespace:
    return job


def _service_stub() -> MonitoringAiService:
    return MonitoringAiService.__new__(MonitoringAiService)
