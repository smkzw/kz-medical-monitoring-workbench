"""R40轮（R40-01）回归：研究文件核对后台作业创建失败（ISE + document_authority_job_missing）。

根因：2026-10-13用户指令把盲核角色与主分析一并改绑cms-router/glm-5.3-flash
（Ollama额度耗尽）后，submit_document_authority_analysis/_review仍把运行身份
硬比对到mapping_gate的陈旧种子常量（verifier期望ollama-cloud/deepseek-v4.1-
flash）→ 上传研究文件时作业创建前即抛MonitoringAiRuntimeUnavailableError，
analyze端点未捕获→裸ISE；而批次清单已落盘→后续advance永远document_authority_
job_missing，无任何界面恢复出口。

本文件守住修复后的四个契约：
1. 提交身份以持久化角色绑定为准（同身份可用绑定照常建作业）；
2. advance对「批次在库、作业缺失」就地重建（重新核对不再是死局）；
3. 运维同绑定（同通道同模型）时双通道复诵按知情降级放行，响应如实披露；
4. 未放行（默认）时同身份对仍fail-closed拒绝。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from packages.medical_monitoring.admission.document_authority import (
    DocumentAuthorityError,
    build_anonymous_conflict_packet,
    reconcile_document_authority,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
    MonitoringAiServiceError,
)
from services.api.app.monitoring_document_authority_jobs import (
    load_document_authority_analysis_run,
)
from services.api.app.monitoring_document_authority_workflow import (
    MonitoringDocumentAuthorityWorkflow,
)

from tests.test_monitoring_document_authority_jobs import (
    _Provider,
    _analysis,
    _batch,
    _runtime,
)

# 2026-10-13运维同绑定的现行身份（cms-router/glm-5.3-flash）。
_SHARED_PROVIDER = "cms-router"
_SHARED_MODEL = "glm-5.3-flash"


def _revision(project_id: str, batch: dict[str, Any]) -> MonitoringAiInputRevision:
    return MonitoringAiInputRevision(
        project_id=project_id,
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )


def _shared_service(
    repository: MonitoringAiRepository,
    role: str,
    analysis: Any,
) -> MonitoringAiService:
    return MonitoringAiService(
        repository,
        runtime_resolver=lambda: _runtime(
            _SHARED_PROVIDER,
            _SHARED_MODEL,
            f"monitoring-document-authority-{role}",
        ),
        provider_factory=lambda _env, analysis=analysis: _Provider(
            _SHARED_PROVIDER,
            _SHARED_MODEL,
            analysis,
        ),
    )


def test_same_identity_submission_creates_both_analysis_jobs(tmp_path) -> None:
    """提交身份门以持久化角色绑定为准：同身份可用绑定照常创建作业。"""

    batch = _batch()
    repository = MonitoringAiRepository(tmp_path / "shared-identity.sqlite")
    revision = _revision("project-shared-identity", batch)

    primary = _shared_service(repository, "primary", _analysis(batch))
    verifier = _shared_service(repository, "verifier", _analysis(batch))

    primary.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="primary",
    )
    verifier.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="verifier",
    )

    jobs = repository.list_jobs(
        revision.project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
    )
    assert {job.business_key.split(":")[1] for job in jobs} == {
        "primary",
        "verifier",
    }
    assert all(
        job.provider == _SHARED_PROVIDER and job.requested_model == _SHARED_MODEL
        for job in jobs
    )


def test_advance_rebuilds_missing_analysis_jobs_from_persisted_batch(tmp_path) -> None:
    """批次清单在库而分析作业缺失时，advance就地重建，job_missing不再是死局。"""

    batch = _batch()
    project_id = "project-heal-missing-jobs"
    workspace = tmp_path / "workspace"
    batch_dir = workspace / "document_authority_candidates" / "batches"
    batch_dir.mkdir(parents=True)
    (batch_dir / f"{batch['batch_id']}.json").write_text(
        json.dumps(batch, ensure_ascii=False),
        encoding="utf-8",
    )
    repository = MonitoringAiRepository(tmp_path / "heal-missing.sqlite")
    revision = _revision(project_id, batch)
    primary = _shared_service(repository, "primary", _analysis(batch))
    verifier = _shared_service(repository, "verifier", _analysis(batch))
    wake_calls: list[bool] = []
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        primary,
        verifier,
        None,
        worker_wake=lambda: wake_calls.append(True),
    )

    assert repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
    ) == ()

    result = workflow.advance(
        project_id=project_id,
        workspace_dir=workspace,
        batch_id=batch["batch_id"],
    )

    assert result["state"] == "analyzing"
    assert result["batch_id"] == batch["batch_id"]
    # 运维同绑定：响应如实披露知情降级。
    assert result["shared_runtime_identity"] is True
    jobs = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
    )
    assert {job.business_key.split(":")[1] for job in jobs} == {
        "primary",
        "verifier",
    }
    assert wake_calls == [True]


def test_advance_proceeds_to_review_when_operator_bound_same_runtime(tmp_path) -> None:
    """同身份双运行在运维同绑定下放行推进（修复前reconcile即抛not_independent）。"""

    batch = _batch()
    project_id = "project-shared-runtime-advance"
    workspace = tmp_path / "workspace"
    batch_dir = workspace / "document_authority_candidates" / "batches"
    batch_dir.mkdir(parents=True)
    (batch_dir / f"{batch['batch_id']}.json").write_text(
        json.dumps(batch, ensure_ascii=False),
        encoding="utf-8",
    )
    repository = MonitoringAiRepository(tmp_path / "shared-advance.sqlite")
    revision = _revision(project_id, batch)
    services = []
    for role, analysis in (
        ("primary", _analysis(batch, select_ecrf=False)),
        ("verifier", _analysis(batch)),
    ):
        service = _shared_service(repository, role, analysis)
        service.submit_document_authority_analysis(
            project_id=project_id,
            input_revision=revision,
            candidate_batch=batch,
            role=role,
        )
        service.run_next(role, claim_identity=service.claim_identity())
        services.append(service)
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        services[0],
        services[1],
        None,
        worker_wake=lambda: None,
    )

    result = workflow.advance(
        project_id=project_id,
        workspace_dir=workspace,
        batch_id=batch["batch_id"],
    )

    # 两侧结论有分歧→进入双盲复核作业提交（此前同身份对在reconcile即被拒）。
    assert result == {"state": "reviewing", "batch_id": batch["batch_id"]}
    reviews = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW.value,
    )
    assert len(reviews) == 2
    assert {job.provider for job in reviews} == {_SHARED_PROVIDER}


def test_reconcile_same_identity_stays_fail_closed_without_allowance(tmp_path) -> None:
    """默认（未放行）时同身份对仍拒绝；显式放行仅解除身份同源一条检查。"""

    batch = _batch()
    project_id = "project-shared-reconcile"
    repository = MonitoringAiRepository(tmp_path / "shared-reconcile.sqlite")
    revision = _revision(project_id, batch)
    services = []
    for role, analysis in (
        ("primary", _analysis(batch, select_ecrf=False)),
        ("verifier", _analysis(batch)),
    ):
        service = _shared_service(repository, role, analysis)
        service.submit_document_authority_analysis(
            project_id=project_id,
            input_revision=revision,
            candidate_batch=batch,
            role=role,
        )
        service.run_next(role, claim_identity=service.claim_identity())
        services.append(service)
    primary_job = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
        business_key_prefix="document-authority-analysis:primary:",
    )[0]
    verifier_job = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
        business_key_prefix="document-authority-analysis:verifier:",
    )[0]
    primary_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=primary_job.job_id,
        candidate_batch=batch,
        role="primary",
    )
    verifier_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=verifier_job.job_id,
        candidate_batch=batch,
        role="verifier",
    )

    with pytest.raises(DocumentAuthorityError) as excinfo:
        reconcile_document_authority(batch, primary_run, verifier_run)
    assert str(excinfo.value) == "document_authority_runs_not_independent"

    # 放行仅当调用方核实运维当前确把两角色绑定为同一身份（workflow层
    # _shared_runtime_identity的口径）；放行后内容校验照旧全量执行。
    reconciliation = reconcile_document_authority(
        batch,
        primary_run,
        verifier_run,
        allow_shared_runtime_identity=True,
    )
    assert reconciliation["state"] == "needs_dual_review"
    assert build_anonymous_conflict_packet(
        batch,
        primary_run,
        verifier_run,
        allow_shared_runtime_identity=True,
    )["conflict_roles"]


def test_start_wraps_submit_failure_as_diagnosable_error(
    tmp_path, monkeypatch
) -> None:
    """作业创建失败不得再以裸ISE逃逸：包装为可诊断的DocumentAuthorityError。"""

    from services.api.app import monitoring_document_authority_workflow as wf_module

    batch = _batch()
    repository = MonitoringAiRepository(tmp_path / "submit-failure.sqlite")

    def _reject(**_kwargs):
        raise MonitoringAiServiceError(
            "document authority verifier runtime is not available: "
            "independent AI role or provider profile is disabled"
        )

    primary = SimpleNamespace(
        repository=repository,
        runtime_resolver=lambda: MonitoringAiRuntimeBinding.unavailable(
            "primary disabled"
        ),
        submit_document_authority_analysis=_reject,
    )
    verifier = SimpleNamespace(
        repository=repository,
        runtime_resolver=lambda: MonitoringAiRuntimeBinding.unavailable(
            "verifier disabled"
        ),
        submit_document_authority_analysis=_reject,
    )
    workflow = object.__new__(MonitoringDocumentAuthorityWorkflow)
    workflow.repository = repository
    workflow.primary_service = primary
    workflow.verifier_service = verifier
    workflow.worker_wake = lambda: None

    class _FakeDecomposer:
        def __init__(self, _root, **_kwargs):
            return None

        def decompose_many(self, _files, project_context=None):
            return SimpleNamespace(to_dict=lambda: batch)

    monkeypatch.setattr(
        wf_module, "MonitoringDocumentCandidateDecomposer", _FakeDecomposer
    )

    with pytest.raises(DocumentAuthorityError) as excinfo:
        workflow.start(
            project_id="project-submit-failure",
            workspace_dir=tmp_path / "workspace",
            files=[("protocol.docx", b"docx-bytes")],
        )
    assert str(excinfo.value) == "document_authority_submit_unavailable"
