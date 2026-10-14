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
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    ConflictDecision,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    EvidenceReference,
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
    submit_document_authority_adjudication_pair,
    submit_document_authority_review_pair,
)
from services.api.app.monitoring_document_authority_workflow import (
    MonitoringDocumentAuthorityWorkflow,
)

from tests.test_monitoring_document_authority_jobs import (
    _Provider,
    _ReviewProvider,
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


def test_advance_proceeds_to_adjudication_when_operator_bound_same_runtime(
    tmp_path,
) -> None:
    """R44轮（R44-01）回归：同身份对在裁决提交阶段不再被fail-closed死锁。

    修复前 build_anonymous_adjudication_context 漏穿R40放行开关——运维同
    绑定项目在复核有分歧、advance进入submit_document_authority_adjudication_
    pair时以document_authority_runs_not_independent持久阻断（R44A实测
    46分43秒无恢复，显式重核同败：已完成作业无从重排，每次advance在
    同一构建点重抛同一诊断）。
    """

    batch = _batch()
    project_id = "project-shared-runtime-adjudication"
    workspace = tmp_path / "workspace"
    batch_dir = workspace / "document_authority_candidates" / "batches"
    batch_dir.mkdir(parents=True)
    (batch_dir / f"{batch['batch_id']}.json").write_text(
        json.dumps(batch, ensure_ascii=False),
        encoding="utf-8",
    )
    repository = MonitoringAiRepository(tmp_path / "shared-adjudication.sqlite")
    revision = _revision(project_id, batch)
    analysis_services = []
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
        analysis_services.append(service)
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        analysis_services[0],
        analysis_services[1],
        None,
        worker_wake=lambda: None,
    )
    assert workflow.advance(
        project_id=project_id,
        workspace_dir=workspace,
        batch_id=batch["batch_id"],
    )["state"] == "reviewing"

    # 复核驱动到终态分歧：primary维持selected、verifier改判unresolved——
    # 复核不收敛，advance应提交裁决对（修复前在提交前构建上下文即死锁）。
    primary_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=analysis_services[0].repository.list_jobs(
            project_id,
            task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
            business_key_prefix="document-authority-analysis:primary:",
        )[0].job_id,
        candidate_batch=batch,
        role="primary",
    )
    verifier_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=analysis_services[1].repository.list_jobs(
            project_id,
            task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
            business_key_prefix="document-authority-analysis:verifier:",
        )[0].job_id,
        candidate_batch=batch,
        role="verifier",
    )
    packet = build_anonymous_conflict_packet(
        batch,
        primary_run,
        verifier_run,
        allow_shared_runtime_identity=True,
    )
    selected_review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.97,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                supplementary_candidate_ids=(),
                evidence_references=(
                    EvidenceReference(
                        candidate_id="candidate_protocol", locator="doc:p1"
                    ),
                    EvidenceReference(
                        candidate_id="candidate_ecrf", locator="xlsx:sheet:1"
                    ),
                ),
            ),
        ),
    )
    unresolved_review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            selected_review.decisions[0].model_copy(
                update={
                    "decision": "unresolved",
                    "selected_candidate_id": "",
                    "document_version": "",
                    "confidence": 0.4,
                }
            ),
        ),
    )
    review_services = []
    for role, review in (
        ("primary", selected_review),
        ("verifier", unresolved_review),
    ):
        service = MonitoringAiService(
            repository,
            runtime_resolver=lambda role=role: _runtime(
                _SHARED_PROVIDER,
                _SHARED_MODEL,
                f"monitoring-document-authority-{role}",
            ),
            provider_factory=lambda _env, review=review: _ReviewProvider(
                _SHARED_PROVIDER,
                _SHARED_MODEL,
                review,
            ),
        )
        review_services.append(service)
    for role_index, role in enumerate(("primary", "verifier")):
        review_services[role_index].run_next(
            role, claim_identity=review_services[role_index].claim_identity()
        )

    result = workflow.advance(
        project_id=project_id,
        workspace_dir=workspace,
        batch_id=batch["batch_id"],
    )

    # 修复前此处重抛document_authority_runs_not_independent（作业已全部
    # 完成、无从重排，显式重试亦同败）。
    assert result["state"] == "adjudicating"
    adjudications = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW.value,
        business_key_prefix="document-authority-adjudication:",
    )
    assert {job.business_key.split(":")[1] for job in adjudications} == {
        "primary",
        "verifier",
    }
    assert all(
        job.provider == _SHARED_PROVIDER
        and job.requested_model == _SHARED_MODEL
        for job in adjudications
    )


def test_adjudication_context_threads_allow_flag_for_direct_submitters(
    tmp_path,
) -> None:
    """R44轮（R44-01）回归：submit_adjudication/critique_pair直调路径同源
    放行——上下文构建在显式传入放行开关时不得再以同身份对为由拒绝。"""

    batch = _batch()
    project_id = "project-shared-adjudication-pair"
    repository = MonitoringAiRepository(tmp_path / "shared-pair.sqlite")
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
    jobs = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS.value,
    )
    analysis_by_role = {job.business_key.split(":")[1]: job for job in jobs}

    # 复核作业驱动到分歧终态（selected vs unresolved）。
    packet = build_anonymous_conflict_packet(
        batch,
        load_document_authority_analysis_run(
            repository,
            project_id=project_id,
            job_id=analysis_by_role["primary"].job_id,
            candidate_batch=batch,
            role="primary",
        ),
        load_document_authority_analysis_run(
            repository,
            project_id=project_id,
            job_id=analysis_by_role["verifier"].job_id,
            candidate_batch=batch,
            role="verifier",
        ),
        allow_shared_runtime_identity=True,
    )
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.97,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                supplementary_candidate_ids=(),
                evidence_references=(
                    EvidenceReference(
                        candidate_id="candidate_protocol", locator="doc:p1"
                    ),
                    EvidenceReference(
                        candidate_id="candidate_ecrf", locator="xlsx:sheet:1"
                    ),
                ),
            ),
        ),
    )
    unresolved_review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            review.decisions[0].model_copy(
                update={
                    "decision": "unresolved",
                    "selected_candidate_id": "",
                    "document_version": "",
                    "confidence": 0.4,
                }
            ),
        ),
    )
    review_services = []
    for role, review_payload in (
        ("primary", review),
        ("verifier", unresolved_review),
    ):
        service = MonitoringAiService(
            repository,
            runtime_resolver=lambda role=role: _runtime(
                _SHARED_PROVIDER,
                _SHARED_MODEL,
                f"monitoring-document-authority-{role}",
            ),
            provider_factory=lambda _env, payload=review_payload: (
                _ReviewProvider(_SHARED_PROVIDER, _SHARED_MODEL, payload)
            ),
        )
        review_services.append(service)

    # 先经submit_review_pair把复核对驱动到分歧终态。
    _, primary_review, verifier_review = submit_document_authority_review_pair(
        review_services[0],
        review_services[1],
        input_revision=revision,
        candidate_batch=batch,
        primary_analysis_job_id=analysis_by_role["primary"].job_id,
        verifier_analysis_job_id=analysis_by_role["verifier"].job_id,
        allow_shared_runtime_identity=True,
    )
    for role_index, role in enumerate(("primary", "verifier")):
        review_services[role_index].run_next(
            role, claim_identity=review_services[role_index].claim_identity()
        )

    # 放行开关显式传入时提交裁决对不得抛not_independent（修复前
    # submit_adjudication_pair内构建adjudication上下文即死锁）。
    _, primary_adjudication, verifier_adjudication = (
        submit_document_authority_adjudication_pair(
            review_services[0],
            review_services[1],
            input_revision=revision,
            candidate_batch=batch,
            primary_analysis_job_id=analysis_by_role["primary"].job_id,
            verifier_analysis_job_id=analysis_by_role["verifier"].job_id,
            primary_review_job_id=primary_review.job_id,
            verifier_review_job_id=verifier_review.job_id,
            allow_shared_runtime_identity=True,
        )
    )
    assert primary_adjudication.business_key.startswith(
        "document-authority-adjudication:primary:"
    )
    assert verifier_adjudication.business_key.startswith(
        "document-authority-adjudication:verifier:"
    )

    # 同一批作业、不传放行开关（默认严格）时仍fail-closed——放行仅限
    # 调用方核实运维同绑定的场景。
    with pytest.raises(DocumentAuthorityError) as excinfo:
        submit_document_authority_adjudication_pair(
            review_services[0],
            review_services[1],
            input_revision=revision,
            candidate_batch=batch,
            primary_analysis_job_id=analysis_by_role["primary"].job_id,
            verifier_analysis_job_id=analysis_by_role["verifier"].job_id,
            primary_review_job_id=primary_review.job_id,
            verifier_review_job_id=verifier_review.job_id,
        )
    assert str(excinfo.value) == "document_authority_runs_not_independent"


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
