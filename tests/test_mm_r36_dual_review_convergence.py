"""R36轮（R36-01/R36-02）：双盲复核收敛性与上传主路径的回归测试。

R36-01（C位实测）：双盲复核等待零进度展示、自救重入、自动重排队无预算、
同草稿复核推进无在途防重入——四因素叠加把映射确认环节变成全链阻断。
本文件钉住修复后的契约：

1. 复核等待的running载荷携带复核分片聚合进度（已完成/总数/执行中/排队中）。
2. adjudicate轮询驱动的自动重排队受自动恢复预算约束（耗尽后计0、如实
   blocked），不再无界fail→requeue→fail循环。
3. 确认门允许显式知情降级（allow_unverified_dual_review），降级事实写入
   确认留痕；不传标志时原门契约不变；revision漂移不可降级。
4. 浏览器上传入口（选择数据文件夹的真实形态=数据工作簿+研究文档混选）
   不再因非数据后缀整体硬拒：文档照常安全落盘并记入skipped_non_data_files，
   一个数据文件都没有时落admission_no_data_files。
"""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission import DataAdmissionPipeline
from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.admission.pipeline import AdmissionPipelineError
from services.api.app.listing_file_parser import parse_listing_file


def _draft():
    return SimpleNamespace(
        batch_id="attempt-1",
        draft_id="draft-1",
        version=1,
        model_dump=lambda mode="json": {
            "project_id": "p1",
            "draft_id": "draft-1",
            "batch_id": "attempt-1",
            "version": 1,
            "fields": [
                {
                    "domain": "AE",
                    "source_field": "AETERM",
                    "recommended_role": "ae_term",
                    "field_kind": "source_collected",
                    "confidence": 0.9,
                    "user_action": "系统已按建议采用，无需额外操作。",
                    "user_decision_required": False,
                },
            ],
        },
    )


def _repo(draft, confirm_recorder=None):
    return SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: draft,
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
        **(
            {"confirm": confirm_recorder}
            if confirm_recorder is not None
            else {}
        ),
    )


def _service(repo, *, require_dual=False, ai_repository=None):
    return AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=ai_repository if ai_repository is not None else SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
        require_dual_reconciliation=require_dual,
    )


def test_adjudicate_running_carries_cohort_progress() -> None:
    """复核未收敛时running载荷必须携带复核分片聚合进度（无作业身份）。"""

    service = _service(_repo(_draft()), require_dual=True)

    def _raise_incomplete(**_kwargs):
        exc = AdmissionMappingPipelineError("mapping_verifier_incomplete")
        exc.cohort_progress = {
            "total_job_count": 10,
            "completed_job_count": 6,
            "pending_job_count": 4,
            "pending_running_count": 1,
            "pending_queued_count": 3,
            "pending_since": "2026-10-12T02:24:50+00:00",
        }
        raise exc

    service.reconcile_with_verifier = _raise_incomplete  # type: ignore[method-assign]

    payload = service.adjudicate_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        workspace_dir="/generated/non-real",
    )

    adjudication = payload["adjudication"]
    assert adjudication["state"] == "running"
    assert adjudication["total_job_count"] == 10
    assert adjudication["completed_job_count"] == 6
    assert adjudication["pending_running_count"] == 1
    assert adjudication["pending_queued_count"] == 3


def test_retry_failed_mapping_jobs_is_bounded_by_automatic_budget() -> None:
    """adjudicate驱动的自动重排队必须传自动恢复预算；预算耗尽计0。"""

    from packages.medical_monitoring.admission.mapping_pipeline import (
        _ADJUDICATION_AUTO_RECOVERY_LIMIT,
    )

    seen_limits = []

    def _retry_terminal(project_id, job_id, *, current_input_revision_sha256, automatic_recovery_limit=None):
        seen_limits.append(automatic_recovery_limit)
        # 预算耗尽：retry_terminal原样返回终态作业（不抛错）。
        return SimpleNamespace(status=SimpleNamespace(value="failed"))

    failed_job = SimpleNamespace(
        job_id="job-v-1",
        project_id="p1",
        status=SimpleNamespace(value="failed"),
        input_revision_sha256="rev",
        prompt_version="prompt",
        provider="primary",
        requested_model="model-a",
        created_at="2026-10-12T02:24:50+00:00",
    )
    service = _service(
        _repo(_draft()),
        ai_repository=SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: [failed_job],
            retry_terminal=_retry_terminal,
            input_payload=lambda *_args, **_kwargs: {
                "field_profile": {"full_profile_sha256": "sha"}
            },
        ),
    )

    retried = service._retry_failed_mapping_jobs(
        project_id="p1",
        attempt_id="attempt-1",
    )

    assert retried == 0
    assert seen_limits
    assert all(limit == _ADJUDICATION_AUTO_RECOVERY_LIMIT for limit in seen_limits)


def test_confirm_draft_degraded_records_honest_receipt() -> None:
    """显式知情降级可越过未收敛的双盲门，且降级事实写入确认留痕。"""

    recorded = {}

    def _confirm(_project_id, _draft_id, **kwargs):
        recorded.update(kwargs)
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "mapping_revision": "rev-1",
                "draft_id": "draft-1",
                "status": "confirmed",
            }
        )

    draft = _draft()
    service = _service(_repo(draft, _confirm), require_dual=True)

    def _raise_incomplete(**_kwargs):
        raise AdmissionMappingPipelineError("mapping_verifier_incomplete")

    service.reconcile_with_verifier = _raise_incomplete  # type: ignore[method-assign]

    payload = service.confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="medical_manager",
        confirmation_reason="医学问题已逐条回答完成。",
        idempotency_key="idem-degrade-1",
        allow_unverified_dual_review=True,
    )

    assert payload["confirmation_status"] == "confirmed"
    assert payload["dual_review_degraded"]
    assert recorded["confirmation_reason"].startswith("双盲复核未完成")

    # 不传降级标志：原门契约不变（409 mapping_verifier_incomplete向上抛）。
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=2,
            confirmed_by="medical_manager",
            confirmation_reason="医学问题已逐条回答完成。",
            idempotency_key="idem-strict-1",
        )
    assert exc.value.code == "mapping_verifier_incomplete"


def test_confirm_draft_cannot_degrade_past_revision_drift() -> None:
    """输入证据漂移（revision drift）必须fail-closed——降级标志不放行。"""

    service = _service(_repo(_draft(), lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not confirm"))), require_dual=True)

    def _raise_drift(**_kwargs):
        raise AdmissionMappingPipelineError("mapping_verifier_revision_drift")

    service.reconcile_with_verifier = _raise_drift  # type: ignore[method-assign]

    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="medical_manager",
            confirmation_reason="医学问题已逐条回答完成。",
            idempotency_key="idem-drift-1",
            allow_unverified_dual_review=True,
        )
    assert exc.value.code == "mapping_verifier_revision_drift"


def _xlsx_bytes(sheet: str = "DM") -> bytes:
    """最小可解析xlsx（单表两行）——直接复用仓库内的openpyxl。"""

    from openpyxl import Workbook

    workbook = Workbook()
    workbook.active.title = sheet
    workbook.active.append(["SUBJID", "VISIT"])
    workbook.active.append(["S001", "V1"])
    target = io.BytesIO()
    workbook.save(target)
    return target.getvalue()


def test_uploaded_attempt_admits_folder_with_research_documents(tmp_path) -> None:
    """「选择数据文件夹」真实形态：数据工作簿与方案/eCRF文档混选。

    R36-02：此前非数据后缀与路径攻击同一分支硬拒整个上报——主路径首步
    即报「目录不存在」。现文档照常安全落盘并记入skipped_non_data_files。
    """

    uploads = [
        ("study_folder/MY008_DataListing.xlsx", io.BytesIO(_xlsx_bytes())),
        ("study_folder/MY008_研究方案_V1.1.docx", io.BytesIO(b"protocol")),
        ("study_folder/MY008_DraftCRF_V0.1.docx", io.BytesIO(b"crf")),
    ]
    pipeline = DataAdmissionPipeline(parse_listing_file)
    result = pipeline.create_uploaded_attempt(
        project_id="proj-r36",
        uploads=uploads,
        workspace_dir=tmp_path,
    )

    assert result["state"] == "profile_ready"
    skipped = list(
        result.get("technical_details", {}).get("skipped_non_data_files") or []
    )
    assert any("研究方案" in item for item in skipped)
    assert any("DraftCRF" in item for item in skipped)


def test_uploaded_attempt_with_only_documents_reports_no_data_files(tmp_path) -> None:
    """一个数据文件都没有：admission_no_data_files（文案如实指引文档在第3步上传）。"""

    uploads = [
        ("study_folder/MY008_研究方案_V1.1.docx", io.BytesIO(b"protocol")),
    ]
    pipeline = DataAdmissionPipeline(parse_listing_file)
    with pytest.raises(AdmissionPipelineError) as exc:
        pipeline.create_uploaded_attempt(
            project_id="proj-r36",
            uploads=uploads,
            workspace_dir=tmp_path,
        )
    assert exc.value.code == "admission_no_data_files"


def test_uploaded_attempt_still_rejects_path_traversal(tmp_path) -> None:
    """路径安全校验保持fail-closed：穿越/绝对路径/盘符仍整体拒收。"""

    pipeline = DataAdmissionPipeline(parse_listing_file)
    with pytest.raises(AdmissionPipelineError) as exc:
        pipeline.create_uploaded_attempt(
            project_id="proj-r36",
            uploads=[("../escape.xlsx", io.BytesIO(_xlsx_bytes()))],
            workspace_dir=tmp_path,
        )
    assert exc.value.code == "admission_source_invalid"
