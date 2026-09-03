from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from packages.medical_monitoring.admission.document_authority import (
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    CandidateAssessment,
    ConflictDecision,
    DocumentAuthorityAnalysis,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    EvidenceReference,
    RoleSelection,
    build_anonymous_conflict_packet,
    document_authority_batch_sha256,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)
from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from services.api.app.monitoring_document_authority_jobs import (
    load_document_authority_analysis_run,
    promote_document_authority_from_jobs,
    resolve_document_authority_from_jobs,
    submit_document_authority_review_pair,
    verify_document_authority_promotion_receipt,
)
from services.api.app.monitoring_document_authority_workflow import (
    MonitoringDocumentAuthorityWorkflow,
)
from services.api.app.monitoring_document_candidates import (
    MonitoringDocumentCandidateDecomposer,
)
from services.api.app.source_intake import SourceRegistryService, SourceRegistryStore
from tests.test_source_registry import _minimal_docx_bytes, _minimal_xlsx_bytes


def _batch() -> dict[str, Any]:
    return {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_product",
        "authority_status": "not_adjudicated",
        "candidates": [
            {
                "candidate_id": "candidate_protocol",
                "file_id": "file_protocol",
                "content_sha256": "a" * 64,
                "filename": "protocol.docx",
                "role_hypotheses": ["protocol"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 1,
                "excerpts": [{"locator": "doc:p1", "text": "研究方案 V1.0"}],
                "sheets": [],
            },
            {
                "candidate_id": "candidate_ecrf",
                "file_id": "file_ecrf",
                "content_sha256": "b" * 64,
                "filename": "ecrf.xlsx",
                "role_hypotheses": ["ecrf"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 1,
                "excerpts": [],
                "sheets": [{"locator": "xlsx:sheet:1", "sheet_name": "AE"}],
            },
        ],
    }


def _analysis(
    batch: dict[str, Any], *, select_ecrf: bool = True
) -> DocumentAuthorityAnalysis:
    return DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=batch["batch_id"],
        input_sha256=document_authority_batch_sha256(batch),
        candidate_assessments=(
            CandidateAssessment(
                candidate_id="candidate_protocol",
                inferred_role="protocol",
                usable=True,
                confidence=0.98,
                document_version="V1.0",
                evidence_locators=("doc:p1",),
            ),
            CandidateAssessment(
                candidate_id="candidate_ecrf",
                inferred_role="ecrf",
                usable=True,
                confidence=0.97,
                evidence_locators=("xlsx:sheet:1",),
            ),
        ),
        role_selections=(
            RoleSelection(
                role="protocol",
                decision="selected",
                selected_candidate_id="candidate_protocol",
                confidence=0.98,
                evidence_locators=("doc:p1",),
            ),
            RoleSelection(
                role="investigator_brochure", decision="missing", confidence=0.95
            ),
            RoleSelection(
                role="ecrf",
                decision="selected" if select_ecrf else "unresolved",
                selected_candidate_id=("candidate_ecrf" if select_ecrf else ""),
                confidence=0.97 if select_ecrf else 0.5,
                evidence_locators=("xlsx:sheet:1",) if select_ecrf else (),
            ),
            RoleSelection(role="sap", decision="missing", confidence=0.95),
        ),
    )


class _Provider:
    transport_name = "openai_compatible"

    def __init__(
        self,
        provider: str,
        model: str,
        analysis: Any,
        *,
        title: str = "研究文件识别结果",
        text: str = "基于冻结文件完成识别。",
    ):
        self.provider_name = provider
        self.model_name = model
        self.expected_response_model = model
        self.response_model = model
        self.analysis = analysis
        self.title = title
        self.text = text
        self.envelopes = []

    def run(self, envelope):
        self.envelopes.append(envelope)
        return {
            "schema_version": MONITORING_AI_SCHEMA_VERSION,
            "task_id": envelope.task_id,
            "task_type": "document_authority_analysis",
            "input_revision_sha256": envelope.payload["input_revision_sha256"],
            "candidates": [{
                "candidate_type": "document_authority_analysis",
                "title": self.title,
                "text": self.text,
                "structured_payload": (
                    self.analysis
                    if isinstance(self.analysis, dict)
                    else self.analysis.model_dump(mode="json")
                ),
            }],
        }


class _ReviewProvider:
    transport_name = "openai_compatible"

    def __init__(self, provider: str, model: str, review: DocumentAuthorityConflictReview):
        self.provider_name = provider
        self.model_name = model
        self.expected_response_model = model
        self.response_model = model
        self.review = review
        self.envelopes = []

    def run(self, envelope):
        self.envelopes.append(envelope)
        return {
            "schema_version": MONITORING_AI_SCHEMA_VERSION,
            "task_id": envelope.task_id,
            "task_type": "document_authority_review",
            "input_revision_sha256": envelope.payload["input_revision_sha256"],
            "candidates": [{
                "candidate_type": "document_authority_review",
                "title": "研究文件冲突复核",
                "text": "基于匿名冻结证据完成复核。",
                "structured_payload": self.review.model_dump(mode="json"),
            }],
        }


def _runtime(provider: str, model: str, profile: str) -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id=profile,
        provider=provider,
        model=model,
        env={
            "WORKBENCH_AI_PROVIDER": provider,
            "WORKBENCH_AI_MODEL": model,
            "WORKBENCH_AI_EXPECTED_RESPONSE_MODEL": model,
            "WORKBENCH_AI_TRANSPORT": "openai_compatible",
            "WORKBENCH_AI_BASE_URL": "https://example.invalid/v1",
            "WORKBENCH_AI_API_KEY": "synthetic-key",
            "WORKBENCH_AI_DEPLOYMENT_PROFILE": "local_private_clinical",
        },
    )


@pytest.mark.parametrize(
    ("role", "provider", "model", "profile"),
    (
        (
            "primary",
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            "monitoring-document-authority-primary",
        ),
        (
            "verifier",
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            "monitoring-document-authority-verifier",
        ),
    ),
)
def test_direct_job_history_builds_server_owned_run_envelope(
    tmp_path, role: str, provider: str, model: str, profile: str
) -> None:
    batch = _batch()
    analysis = _analysis(batch)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    runtime = _runtime(provider, model, profile)
    fake = _Provider(provider, model, analysis)
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: runtime,
        provider_factory=lambda _env: fake,
    )
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )

    queued = service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role=role,
    )
    result = service.run_next("synthetic-worker", claim_identity=service.claim_identity())
    run = load_document_authority_analysis_run(
        repository,
        project_id=revision.project_id,
        job_id=queued.job_id,
        candidate_batch=batch,
        role=role,
    )

    assert result.job is not None and result.job.status.value == "completed"
    assert run.job_id == queued.job_id
    assert run.run_id.startswith("monattempt_")
    assert run.analysis == analysis
    assert fake.envelopes[0].payload["input_payload"]["document_authority_role"] == role
    assert "另一模型" not in str(fake.envelopes[0].payload["input_payload"])


def test_loader_rejects_role_swap(tmp_path) -> None:
    batch = _batch()
    analysis = _analysis(batch)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    runtime = _runtime(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        "monitoring-document-authority-primary",
    )
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: runtime,
        provider_factory=lambda _env: _Provider(
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            analysis,
        ),
    )
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )
    job = service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="primary",
    )
    service.run_next("synthetic-worker", claim_identity=service.claim_identity())

    with pytest.raises(DocumentAuthorityError, match="job_identity_invalid"):
        load_document_authority_analysis_run(
            repository,
            project_id=revision.project_id,
            job_id=job.job_id,
            candidate_batch=batch,
            role="verifier",
        )


def test_matching_analysis_jobs_resolve_without_conflict_reviews(tmp_path) -> None:
    batch = _batch()
    analysis = _analysis(batch)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )
    jobs = []
    for role, provider, model in (
        ("primary", MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
        ("verifier", MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL),
    ):
        service = MonitoringAiService(
            repository,
            runtime_resolver=lambda provider=provider, model=model, role=role: _runtime(
                provider, model, f"monitoring-document-authority-{role}"
            ),
            provider_factory=lambda _env, provider=provider, model=model: _Provider(
                provider, model, analysis
            ),
        )
        job = service.submit_document_authority_analysis(
            project_id=revision.project_id,
            input_revision=revision,
            candidate_batch=batch,
            role=role,
        )
        service.run_next(
            f"{role}-analysis-worker", claim_identity=service.claim_identity()
        )
        jobs.append(job)

    result = resolve_document_authority_from_jobs(
        repository,
        project_id=revision.project_id,
        candidate_batch=batch,
        primary_analysis_job_id=jobs[0].job_id,
        verifier_analysis_job_id=jobs[1].job_id,
    )

    assert result["state"] == "resolved"
    assert result["review_run_ids"] == []
    assert {item["role"] for item in result["document_identities"]} == {
        "protocol",
        "ecrf",
    }


def test_product_workflow_starts_both_models_and_promotes_direct_agreement(
    tmp_path,
) -> None:
    protocol = _minimal_docx_bytes()
    ecrf = _minimal_xlsx_bytes()
    expected_batch = MonitoringDocumentCandidateDecomposer(
        tmp_path / "preview"
    ).decompose_many([
        ("protocol.docx", protocol),
        ("ecrf.xlsx", ecrf),
    ]).to_dict()
    candidate_ids = {
        item["filename"]: item["candidate_id"]
        for item in expected_batch["candidates"]
    }
    analysis = DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=expected_batch["batch_id"],
        input_sha256=document_authority_batch_sha256(expected_batch),
        candidate_assessments=(
            CandidateAssessment(
                candidate_id=candidate_ids["protocol.docx"],
                inferred_role="protocol",
                usable=True,
                confidence=0.99,
                evidence_locators=tuple(
                    item["locator"]
                    for item in next(
                        candidate
                        for candidate in expected_batch["candidates"]
                        if candidate["filename"] == "protocol.docx"
                    )["excerpts"][:1]
                ),
            ),
            CandidateAssessment(
                candidate_id=candidate_ids["ecrf.xlsx"],
                inferred_role="ecrf",
                usable=True,
                confidence=0.99,
                evidence_locators=tuple(
                    item["locator"]
                    for item in next(
                        candidate
                        for candidate in expected_batch["candidates"]
                        if candidate["filename"] == "ecrf.xlsx"
                    )["sheets"][:1]
                ),
            ),
        ),
        role_selections=(
            RoleSelection(
                role="protocol",
                decision="selected",
                selected_candidate_id=candidate_ids["protocol.docx"],
                confidence=0.99,
                evidence_locators=tuple(
                    item["locator"]
                    for item in next(
                        candidate
                        for candidate in expected_batch["candidates"]
                        if candidate["filename"] == "protocol.docx"
                    )["excerpts"][:1]
                ),
            ),
            RoleSelection(
                role="investigator_brochure", decision="missing", confidence=0.99
            ),
            RoleSelection(
                role="ecrf",
                decision="selected",
                selected_candidate_id=candidate_ids["ecrf.xlsx"],
                confidence=0.99,
                evidence_locators=tuple(
                    item["locator"]
                    for item in next(
                        candidate
                        for candidate in expected_batch["candidates"]
                        if candidate["filename"] == "ecrf.xlsx"
                    )["sheets"][:1]
                ),
            ),
            RoleSelection(role="sap", decision="missing", confidence=0.99),
        ),
    )
    repository = MonitoringAiRepository(tmp_path / "workflow.sqlite")
    services = []
    for role, provider, model in (
        ("primary", MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
        ("verifier", MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL),
    ):
        services.append(MonitoringAiService(
            repository,
            runtime_resolver=lambda provider=provider, model=model, role=role: _runtime(
                provider, model, f"monitoring-document-authority-{role}"
            ),
            provider_factory=lambda _env, provider=provider, model=model: _Provider(
                provider, model, analysis
            ),
        ))
    wake_calls = []
    registry = SourceRegistryService(SourceRegistryStore(tmp_path / "registry.jsonl"))
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        services[0],
        services[1],
        registry,
        worker_wake=lambda: wake_calls.append(True),
    )

    started = workflow.start(
        project_id="project-document-authority",
        workspace_dir=tmp_path / "workspace",
        files=[("protocol.docx", protocol), ("ecrf.xlsx", ecrf)],
    )
    assert started == {"state": "analyzing", "batch_id": expected_batch["batch_id"]}
    for index, service in enumerate(services):
        service.run_next(
            f"workflow-{index}", claim_identity=service.claim_identity()
        )
    promoted = workflow.advance(
        project_id="project-document-authority",
        workspace_dir=tmp_path / "workspace",
        batch_id=started["batch_id"],
    )

    assert promoted["authority_status"] == "promoted"
    assert len(registry.list_entries("project-document-authority")) == 2
    assert wake_calls == [True]
    receipt = registry.list_entries("project-document-authority")[0].metadata[
        "document_authority_receipt"
    ]
    assert verify_document_authority_promotion_receipt(
        repository,
        project_id="project-document-authority",
        receipt=receipt,
    ) is True
    forged = {**receipt, "analysis_job_ids": ["missing-primary", "missing-verifier"]}
    assert verify_document_authority_promotion_receipt(
        repository,
        project_id="project-document-authority",
        receipt=forged,
    ) is False


def test_worker_rejects_downstream_medical_conclusion_hidden_in_output(
    tmp_path,
) -> None:
    batch = _batch()
    raw_analysis = _analysis(batch).model_dump(mode="json")
    raw_analysis["candidate_assessments"][0]["uncertainty"] = (
        "该患者不良反应判定为3级，应向研究中心发出质疑。"
    )
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    runtime = _runtime(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        "monitoring-document-authority-primary",
    )
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: runtime,
        provider_factory=lambda _env: _Provider(
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            raw_analysis,
        ),
    )
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )
    job = service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="primary",
    )

    result = service.run_next(
        "synthetic-worker", claim_identity=service.claim_identity()
    )

    assert result.job is not None and result.job.status.value == "failed"
    assert repository.candidates(revision.project_id, job.job_id) == ()


def test_product_workflow_starts_blind_conflict_review_without_user_choice(
    tmp_path,
) -> None:
    batch = _batch()
    project_id = "project-document-authority"
    workspace = tmp_path / "workspace"
    batch_dir = workspace / "document_authority_candidates" / "batches"
    batch_dir.mkdir(parents=True)
    (batch_dir / f"{batch['batch_id']}.json").write_text(
        json.dumps(batch, ensure_ascii=False),
        encoding="utf-8",
    )
    repository = MonitoringAiRepository(tmp_path / "workflow-conflict.sqlite")
    revision = MonitoringAiInputRevision(
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
    services = []
    for role, provider, model, analysis in (
        (
            "primary",
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            _analysis(batch, select_ecrf=False),
        ),
        (
            "verifier",
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            _analysis(batch),
        ),
    ):
        service = MonitoringAiService(
            repository,
            runtime_resolver=lambda provider=provider, model=model, role=role: _runtime(
                provider, model, f"monitoring-document-authority-{role}"
            ),
            provider_factory=lambda _env, provider=provider, model=model, analysis=analysis: _Provider(
                provider, model, analysis
            ),
        )
        service.submit_document_authority_analysis(
            project_id=project_id,
            input_revision=revision,
            candidate_batch=batch,
            role=role,
        )
        service.run_next(role, claim_identity=service.claim_identity())
        services.append(service)
    wake_calls = []
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        services[0],
        services[1],
        SourceRegistryService(SourceRegistryStore(tmp_path / "registry.jsonl")),
        worker_wake=lambda: wake_calls.append(True),
    )

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
    packet = build_anonymous_conflict_packet(batch, primary_run, verifier_run)
    services[0].submit_document_authority_review(
        project_id=project_id,
        input_revision=revision,
        conflict_packet=packet,
        source_bindings=[
            {
                "candidate_id": item["candidate_id"],
                "source_entry_id": item["file_id"],
                "source_content_sha256": item["content_sha256"],
            }
            for item in batch["candidates"]
        ],
        role="primary",
    )

    result = workflow.advance(
        project_id=project_id,
        workspace_dir=workspace,
        batch_id=batch["batch_id"],
    )

    reviews = repository.list_jobs(
        project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW.value,
    )
    assert result == {"state": "reviewing", "batch_id": batch["batch_id"]}
    assert len(reviews) == 2
    assert {job.provider for job in reviews} == {
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_VERIFIER_PROVIDER,
    }
    assert wake_calls == [True]


def test_product_workflow_retries_one_terminal_failure_once() -> None:
    retries = []
    wakes = []
    workflow = object.__new__(MonitoringDocumentAuthorityWorkflow)
    workflow.repository = SimpleNamespace(
        retry_terminal=lambda project_id, job_id, **kwargs: retries.append(
            (project_id, job_id, kwargs["current_input_revision_sha256"])
        )
    )
    workflow.worker_wake = lambda: wakes.append(True)
    failed = SimpleNamespace(
        project_id="project",
        job_id="failed-job",
        status=MonitoringAiJobStatus.FAILED,
        max_attempts=2,
        contract_retirement_code="",
        input_revision_sha256="a" * 64,
    )
    complete = SimpleNamespace(
        project_id="project",
        job_id="complete-job",
        status=MonitoringAiJobStatus.COMPLETED,
        max_attempts=2,
        contract_retirement_code="",
        input_revision_sha256="a" * 64,
    )

    assert workflow._recover_failed_once((failed, complete)) is True
    assert retries == [("project", "failed-job", "a" * 64)]
    assert wakes == [True]
    failed.max_attempts = 4
    assert workflow._recover_failed_once((failed, complete)) is False


def test_worker_rejects_downstream_medical_conclusion_in_outer_copy(
    tmp_path,
) -> None:
    batch = _batch()
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    runtime = _runtime(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        "monitoring-document-authority-primary",
    )
    provider = _Provider(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        _analysis(batch),
        text="该患者不良反应判定为3级，应向研究中心发出质疑。",
    )
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: runtime,
        provider_factory=lambda _env: provider,
    )
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )
    job = service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="primary",
    )

    result = service.run_next(
        "synthetic-worker", claim_identity=service.claim_identity()
    )

    assert result.job is not None and result.job.status.value == "failed"
    assert repository.candidates(revision.project_id, job.job_id) == ()
    assert len(provider.envelopes) == 1
    attempts = repository.attempts(revision.project_id, job.job_id)
    assert len(attempts) == 1
    assert attempts[0]["outcome"] == "invalid_output"
    assert len(attempts[0]["response"]["provider_outputs"]) == 1


def test_repository_jobs_drive_blind_second_review_and_final_resolution(
    tmp_path,
) -> None:
    batch = _batch()
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite")
    revision = MonitoringAiInputRevision(
        project_id="project-document-authority",
        batch_revision=batch["batch_id"],
        sources=tuple(
            MonitoringAiSourceBinding(
                source_entry_id=item["file_id"],
                source_content_sha256=item["content_sha256"],
            )
            for item in batch["candidates"]
        ),
    )
    primary_runtime = _runtime(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        "monitoring-document-authority-primary",
    )
    verifier_runtime = _runtime(
        MONITORING_C3_VERIFIER_PROVIDER,
        MONITORING_C3_VERIFIER_MODEL,
        "monitoring-document-authority-verifier",
    )
    primary_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: primary_runtime,
        provider_factory=lambda _env: _Provider(
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            _analysis(batch, select_ecrf=False),
        ),
    )
    verifier_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: verifier_runtime,
        provider_factory=lambda _env: _Provider(
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            _analysis(batch),
        ),
    )
    primary_job = primary_service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="primary",
    )
    verifier_job = verifier_service.submit_document_authority_analysis(
        project_id=revision.project_id,
        input_revision=revision,
        candidate_batch=batch,
        role="verifier",
    )
    primary_service.run_next(
        "primary-analysis-worker", claim_identity=primary_service.claim_identity()
    )
    verifier_service.run_next(
        "verifier-analysis-worker", claim_identity=verifier_service.claim_identity()
    )

    primary_review_provider: dict[str, _ReviewProvider] = {}
    verifier_review_provider: dict[str, _ReviewProvider] = {}
    primary_review_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: primary_runtime,
        provider_factory=lambda _env: primary_review_provider["value"],
    )
    verifier_review_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: verifier_runtime,
        provider_factory=lambda _env: verifier_review_provider["value"],
    )
    packet, primary_review_job, verifier_review_job = (
        submit_document_authority_review_pair(
            primary_review_service,
            verifier_review_service,
            input_revision=revision,
            candidate_batch=batch,
            primary_analysis_job_id=primary_job.job_id,
            verifier_analysis_job_id=verifier_job.job_id,
        )
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
    primary_review_provider["value"] = _ReviewProvider(
        MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL, review
    )
    verifier_review_provider["value"] = _ReviewProvider(
        MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL, review
    )
    primary_review_service.run_next(
        "primary-review-worker", claim_identity=primary_review_service.claim_identity()
    )
    verifier_review_service.run_next(
        "verifier-review-worker", claim_identity=verifier_review_service.claim_identity()
    )

    result = resolve_document_authority_from_jobs(
        repository,
        project_id=revision.project_id,
        candidate_batch=batch,
        primary_analysis_job_id=primary_job.job_id,
        verifier_analysis_job_id=verifier_job.job_id,
        primary_review_job_id=primary_review_job.job_id,
        verifier_review_job_id=verifier_review_job.job_id,
    )

    assert result["state"] == "resolved"
    assert result["user_question"] == ""
    assert all(
        "document_authority_source_bindings"
        not in provider.envelopes[0].payload["input_payload"]
        for provider in (
            primary_review_provider["value"],
            verifier_review_provider["value"],
        )
    )


def test_resolved_authority_promotes_selected_documents_atomically(
    tmp_path,
    monkeypatch,
) -> None:
    protocol = _minimal_docx_bytes()
    ecrf = _minimal_xlsx_bytes()
    candidate_root = tmp_path / "candidates"
    batch = MonitoringDocumentCandidateDecomposer(candidate_root).decompose_many([
        ("protocol.docx", protocol),
        ("ecrf.xlsx", ecrf),
    ]).to_dict()
    candidate_ids = {
        candidate["filename"]: candidate["candidate_id"]
        for candidate in batch["candidates"]
    }
    monkeypatch.setattr(
        "services.api.app.monitoring_document_authority_jobs."
        "resolve_document_authority_from_jobs",
        lambda *_args, **_kwargs: {
            "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
            "batch_id": batch["batch_id"],
            "input_sha256": document_authority_batch_sha256(batch),
            "state": "resolved",
            "resolved_roles": [
                {
                    "role": "protocol",
                    "status": "selected",
                    "candidate_id": candidate_ids["protocol.docx"],
                },
                {"role": "investigator_brochure", "status": "missing", "candidate_id": ""},
                {
                    "role": "ecrf",
                    "status": "selected",
                    "candidate_id": candidate_ids["ecrf.xlsx"],
                },
                {"role": "sap", "status": "missing", "candidate_id": ""},
            ],
            "unresolved_roles": [],
            "user_question": "",
            "review_run_ids": ["run_primary", "run_verifier"],
            "analysis_run_ids": ["analysis_run_primary", "analysis_run_verifier"],
            "document_identities": [
                {
                    "role": "protocol",
                    "candidate_id": candidate_ids["protocol.docx"],
                    "document_version": "V1.0",
                    "document_date": "2026-09-03",
                },
                {
                    "role": "ecrf",
                    "candidate_id": candidate_ids["ecrf.xlsx"],
                    "document_version": "V1.0",
                    "document_date": "2026-09-03",
                },
            ],
        },
    )
    registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "registry.jsonl")
    )

    result = promote_document_authority_from_jobs(
        MonitoringAiRepository(tmp_path / "jobs.sqlite"),
        project_id="project-document-authority",
        candidate_batch=batch,
        candidate_root=candidate_root,
        source_registry=registry,
        primary_analysis_job_id="analysis-primary",
        verifier_analysis_job_id="analysis-verifier",
        conflict_packet={},
        primary_review_job_id="review-primary",
        verifier_review_job_id="review-verifier",
    )

    assert result["authority_status"] == "promoted"
    assert {item["role"] for item in result["registrations"]} == {"protocol", "ecrf"}
    entries = registry.list_entries("project-document-authority")
    assert {entry.source_kind for entry in entries} == {
        "protocol_docx",
        "ecrf",
    }
    assert all(
        entry.metadata["document_authority_receipt_sha256"]
        == result["promotion_receipt_sha256"]
        for entry in entries
    )
    replay = promote_document_authority_from_jobs(
        MonitoringAiRepository(tmp_path / "jobs.sqlite"),
        project_id="project-document-authority",
        candidate_batch=batch,
        candidate_root=candidate_root,
        source_registry=registry,
        primary_analysis_job_id="analysis-primary",
        verifier_analysis_job_id="analysis-verifier",
        conflict_packet={},
        primary_review_job_id="review-primary",
        verifier_review_job_id="review-verifier",
    )
    assert replay["promotion_receipt_sha256"] == result["promotion_receipt_sha256"]
    assert len(registry.list_entries("project-document-authority")) == 2
    re_adjudicated = promote_document_authority_from_jobs(
        MonitoringAiRepository(tmp_path / "jobs.sqlite"),
        project_id="project-document-authority",
        candidate_batch=batch,
        candidate_root=candidate_root,
        source_registry=registry,
        primary_analysis_job_id="analysis-primary-2",
        verifier_analysis_job_id="analysis-verifier-2",
        conflict_packet={},
        primary_review_job_id="review-primary-2",
        verifier_review_job_id="review-verifier-2",
    )
    assert re_adjudicated["promotion_receipt_sha256"] != (
        result["promotion_receipt_sha256"]
    )
    assert all(
        entry.metadata["document_authority_receipt_sha256"]
        == re_adjudicated["promotion_receipt_sha256"]
        for entry in registry.list_entries("project-document-authority")
    )

    rollback_registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "rollback-registry.jsonl")
    )
    register = rollback_registry.register_monitoring_mapping_document

    def fail_second_registration(*args, **kwargs):
        if kwargs.get("document_role") == "ecrf":
            raise RuntimeError("synthetic second registration failure")
        return register(*args, **kwargs)

    monkeypatch.setattr(
        rollback_registry,
        "register_monitoring_mapping_document",
        fail_second_registration,
    )
    with pytest.raises(RuntimeError, match="second registration failure"):
        promote_document_authority_from_jobs(
            MonitoringAiRepository(tmp_path / "rollback-jobs.sqlite"),
            project_id="project-document-authority",
            candidate_batch=batch,
            candidate_root=candidate_root,
            source_registry=rollback_registry,
            primary_analysis_job_id="analysis-primary",
            verifier_analysis_job_id="analysis-verifier",
            conflict_packet={},
            primary_review_job_id="review-primary",
            verifier_review_job_id="review-verifier",
        )
    assert rollback_registry.list_entries("project-document-authority") == []

    batch_manifest = candidate_root / "batches" / f"{batch['batch_id']}.json"
    batch_manifest.unlink()
    missing_batch_registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "missing-batch-registry.jsonl")
    )
    with pytest.raises(DocumentAuthorityError, match="batch_manifest_missing"):
        promote_document_authority_from_jobs(
            MonitoringAiRepository(tmp_path / "missing-batch-jobs.sqlite"),
            project_id="project-document-authority",
            candidate_batch=batch,
            candidate_root=candidate_root,
            source_registry=missing_batch_registry,
            primary_analysis_job_id="analysis-primary",
            verifier_analysis_job_id="analysis-verifier",
        )
    assert missing_batch_registry.list_entries("project-document-authority") == []

    MonitoringDocumentCandidateDecomposer(candidate_root).decompose_many([
        ("protocol.docx", protocol),
        ("ecrf.xlsx", ecrf),
    ])
    candidate_manifest = (
        candidate_root
        / "manifests"
        / f"{candidate_ids['protocol.docx']}.json"
    )
    candidate_manifest.unlink()
    missing_candidate_registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "missing-candidate-registry.jsonl")
    )
    with pytest.raises(DocumentAuthorityError, match="candidate_manifest_missing"):
        promote_document_authority_from_jobs(
            MonitoringAiRepository(tmp_path / "missing-candidate-jobs.sqlite"),
            project_id="project-document-authority",
            candidate_batch=batch,
            candidate_root=candidate_root,
            source_registry=missing_candidate_registry,
            primary_analysis_job_id="analysis-primary",
            verifier_analysis_job_id="analysis-verifier",
        )
    assert missing_candidate_registry.list_entries("project-document-authority") == []
