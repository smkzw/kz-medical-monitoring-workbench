"""R39轮（R39-01）：文档权威输出身份字段的确定性服务端注入回归。

R39B实测（report_B:36,109）：上传方案docx+eCRF pdf后自动核对4/4次确定性
失败（错误逐字相同）：document authority provider output failed its
fail-closed contract: MonitoringAiOutputValidationError: [string_pattern_
mismatch @ input_sha256]。契约要求模型把服务端计算的冻结批次摘要
（input_sha256 / conflict_packet_sha256）逐字复制进structured_payload，
deepseek-v4.1-flash确定性做不到，fail-closed拒绝后第3步核对→映射→运行
→发布全链不可达且无自救路径。

修复：服务端在内容校验前把自有身份字段注入候选载荷副本（模型分析内容
逐字保留、照旧全部校验）；完整性由服务端在validate_document_authority_
analysis / conflict_review重新计算比对保证，模型回显不提供额外完整性。
"""

from __future__ import annotations

import types

from packages.medical_monitoring.admission.document_authority import (
    CandidateAssessment,
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    DocumentAuthorityAnalysis,
    DocumentAuthorityConflictReview,
    RoleSelection,
    document_authority_batch_sha256,
    validate_document_authority_analysis,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_service import (
    MonitoringAiService,
)


def _job(task_type: MonitoringAiTaskType) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        task_type=task_type,
        job_id="job_r39_1",
        input_revision_sha256="a" * 64,
    )


def _batch() -> dict:
    return {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_r39",
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
        ],
    }


def _analysis_payload(batch: dict, *, input_sha256: str) -> dict:
    """模型视角的分析载荷：input_sha256为模型自填（可错）。

    用裸dict构造而非先过模型——坏回显本来就过不了
    DocumentAuthorityAnalysis的pattern校验（这正是R39-01的失败点）。
    """

    return {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": batch["batch_id"],
        "input_sha256": input_sha256,
        "candidate_assessments": [
            {
                "candidate_id": "candidate_protocol",
                "inferred_role": "protocol",
                "usable": True,
                "confidence": 0.98,
                "evidence_locators": ["doc:p1"],
            },
        ],
        "role_selections": [
            {
                "role": "protocol",
                "decision": "selected",
                "selected_candidate_id": "candidate_protocol",
                "confidence": 0.98,
                "evidence_locators": ["doc:p1"],
                "supplementary_bindings": [],
            },
            # 其余角色无候选、声明缺失（无usable评估→缺位可证）
            *[
                {
                    "role": role,
                    "decision": "missing",
                    "selected_candidate_id": "",
                    "confidence": 0.9,
                    "evidence_locators": [],
                    "supplementary_bindings": [],
                }
                for role in ("investigator_brochure", "ecrf", "sap")
            ],
        ],
        "study_identity": {
            "status": "not_assessed",
            "project_context_sha256": "",
            "evidence_references": [],
            "rationale": "",
        },
    }


def _analysis_envelope(job, batch: dict, *, input_sha256: str) -> dict:
    return {
        "schema_version": "monitoring_ai_output_v1",
        "task_id": job.job_id,
        "task_type": job.task_type.value,
        "input_revision_sha256": job.input_revision_sha256,
        "candidates": [
            {
                "candidate_type": "document_authority_analysis",
                "title": "研究文件识别结果",
                "text": "基于冻结文件完成识别。",
                "structured_payload": _analysis_payload(
                    batch, input_sha256=input_sha256
                ),
            },
        ],
    }


def test_analysis_invalid_sha_is_replaced_by_server_value_and_passes_validation() -> None:
    """R39B主场景：非64位hex回显被服务端值覆盖，内容校验照旧全过。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    batch_sha = document_authority_batch_sha256(batch)
    input_payload = {
        "document_authority_batch": batch,
        "document_authority_batch_sha256": batch_sha,
        "document_authority_role": "primary",
    }
    raw_output = _analysis_envelope(
        job, batch, input_sha256="不是哈希的模型回显"
    )
    notes: list[dict] = []
    normalized = MonitoringAiService._normalize_document_authority_provider_output(
        job, raw_output, notes, input_payload=input_payload,
    )
    payload = normalized["candidates"][0]["structured_payload"]
    # 注入的是服务端已知批次摘要
    assert payload["input_sha256"] == batch_sha
    # 模型自己的分析内容逐字保留
    assert payload["candidate_assessments"][0]["candidate_id"] == (
        "candidate_protocol"
    )
    analysis = DocumentAuthorityAnalysis.model_validate(payload)
    validate_document_authority_analysis(batch, analysis)
    # 注入动作留痕
    assert any(
        note.get("normalization")
        == "document_authority_identity_field_server_injected"
        and note.get("field") == "input_sha256"
        for note in notes
    )
    # 调用方持有的原始输出不被就地改写（raw留痕仍是模型原话）
    assert (
        raw_output["candidates"][0]["structured_payload"]["input_sha256"]
        == "不是哈希的模型回显"
    )


def test_analysis_missing_sha_is_injected() -> None:
    """模型整段漏掉身份字段时同样注入。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    batch_sha = document_authority_batch_sha256(batch)
    input_payload = {
        "document_authority_batch": batch,
        "document_authority_batch_sha256": batch_sha,
        "document_authority_role": "primary",
    }
    envelope = _analysis_envelope(
        job, batch, input_sha256=document_authority_batch_sha256(batch)
    )
    del envelope["candidates"][0]["structured_payload"]["input_sha256"]
    notes: list[dict] = []
    normalized = MonitoringAiService._normalize_document_authority_provider_output(
        job, envelope, notes, input_payload=input_payload,
    )
    payload = normalized["candidates"][0]["structured_payload"]
    assert payload["input_sha256"] == batch_sha
    assert DocumentAuthorityAnalysis.model_validate(payload).input_sha256 == (
        batch_sha
    )


def test_analysis_correct_echo_stays_untouched_and_unnoted() -> None:
    """模型正确回显时不改写、不留注入痕（行为与修复前一致）。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    batch_sha = document_authority_batch_sha256(batch)
    input_payload = {
        "document_authority_batch": batch,
        "document_authority_batch_sha256": batch_sha,
        "document_authority_role": "primary",
    }
    notes: list[dict] = []
    normalized = MonitoringAiService._normalize_document_authority_provider_output(
        job,
        _analysis_envelope(job, batch, input_sha256=batch_sha),
        notes,
        input_payload=input_payload,
    )
    assert normalized["candidates"][0]["structured_payload"]["input_sha256"] == (
        batch_sha
    )
    assert not any(
        note.get("normalization")
        == "document_authority_identity_field_server_injected"
        for note in notes
    )


def test_review_invalid_packet_sha_is_replaced_by_server_value() -> None:
    """复核路径conflict_packet_sha256同口径注入（完整性核对在服务端）。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW)
    packet_sha = "b" * 64
    input_payload = {
        "document_authority_conflict_packet_sha256": packet_sha,
        "document_authority_role": "primary",
    }
    review_payload = {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "conflict_packet_sha256": "zzzz-not-a-digest",
        "decisions": [],
    }
    envelope = {
        "schema_version": "monitoring_ai_output_v1",
        "task_id": job.job_id,
        "task_type": job.task_type.value,
        "input_revision_sha256": job.input_revision_sha256,
        "candidates": [
            {
                "candidate_type": "document_authority_conflict_review",
                "title": "研究文件冲突复核",
                "text": "基于匿名冻结证据完成复核。",
                "structured_payload": review_payload,
            },
        ],
    }
    notes: list[dict] = []
    normalized = MonitoringAiService._normalize_document_authority_provider_output(
        job, envelope, notes, input_payload=input_payload,
    )
    payload = normalized["candidates"][0]["structured_payload"]
    assert payload["conflict_packet_sha256"] == packet_sha
    assert DocumentAuthorityConflictReview.model_validate(
        payload
    ).conflict_packet_sha256 == packet_sha
    assert any(
        note.get("field") == "conflict_packet_sha256" for note in notes
    )


def test_injection_absent_input_digest_keeps_fail_closed() -> None:
    """输入载荷未带服务端摘要时不动输出（照旧由内容校验拒绝）。"""

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = _batch()
    input_payload = {"document_authority_batch": batch}
    envelope = _analysis_envelope(job, batch, input_sha256="bad-echo")
    notes: list[dict] = []
    normalized = MonitoringAiService._normalize_document_authority_provider_output(
        job, envelope, notes, input_payload=input_payload,
    )
    assert (
        normalized["candidates"][0]["structured_payload"]["input_sha256"]
        == "bad-echo"
    )


def test_multi_candidate_merge_survives_invalid_identity_echoes() -> None:
    """R37-02归并链路：身份回显全错时注入先行，归并照常成立。"""

    from services.api.app.monitoring_ai_contracts import (
        MONITORING_AI_SCHEMA_VERSION,
    )

    def _split_candidate(batch: dict, *, candidate_id: str, role: str,
                         locator: str) -> dict:
        payload = {
            "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
            "batch_id": batch["batch_id"],
            "input_sha256": "模型又复制错了",
            "candidate_assessments": [
                {
                    "candidate_id": candidate_id,
                    "inferred_role": role,
                    "usable": True,
                    "confidence": 0.95,
                    "evidence_locators": [locator],
                },
            ],
            "role_selections": [
                {
                    "role": role,
                    "decision": "selected",
                    "selected_candidate_id": candidate_id,
                    "confidence": 0.95,
                    "evidence_locators": [locator],
                    "supplementary_bindings": [],
                },
            ],
            "study_identity": {
                "status": "not_assessed",
                "project_context_sha256": "",
                "evidence_references": [],
                "rationale": "",
            },
        }
        return {
            "candidate_type": "document_authority_analysis",
            "title": "研究文件识别结果",
            "text": "基于冻结文件完成识别。",
            "structured_payload": payload,
        }

    job = _job(MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS)
    batch = {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_r39b",
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
    batch_sha = document_authority_batch_sha256(batch)
    input_payload = {
        "document_authority_batch": batch,
        "document_authority_batch_sha256": batch_sha,
        "document_authority_role": "primary",
    }
    envelope = {
        "schema_version": MONITORING_AI_SCHEMA_VERSION,
        "task_id": job.job_id,
        "task_type": job.task_type.value,
        "input_revision_sha256": job.input_revision_sha256,
        "candidates": [
            _split_candidate(
                batch, candidate_id="candidate_protocol",
                role="protocol", locator="doc:p1",
            ),
            _split_candidate(
                batch, candidate_id="candidate_ecrf",
                role="ecrf", locator="xlsx:sheet:1",
            ),
        ],
    }
    notes: list[dict] = []
    merged = MonitoringAiService._normalize_document_authority_provider_output(
        job, envelope, notes, input_payload=input_payload,
    )
    assert len(merged["candidates"]) == 1
    payload = merged["candidates"][0]["structured_payload"]
    assert payload["input_sha256"] == batch_sha
    assert {item["candidate_id"] for item in payload["candidate_assessments"]} == {
        "candidate_protocol",
        "candidate_ecrf",
    }
    # 归并产物过得了任务模型（角色全量覆盖由内容校验层负责，与本条无关）
    analysis = DocumentAuthorityAnalysis.model_validate(payload)
    assert analysis.input_sha256 == batch_sha
