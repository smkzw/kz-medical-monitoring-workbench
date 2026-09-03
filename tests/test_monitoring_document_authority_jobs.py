from __future__ import annotations

from typing import Any

import pytest

from packages.medical_monitoring.admission.document_authority import (
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    CandidateAssessment,
    DocumentAuthorityAnalysis,
    DocumentAuthorityError,
    RoleSelection,
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
    MonitoringAiSourceBinding,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from services.api.app.monitoring_document_authority_jobs import (
    load_document_authority_analysis_run,
)


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


def _analysis(batch: dict[str, Any]) -> DocumentAuthorityAnalysis:
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
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                confidence=0.97,
                evidence_locators=("xlsx:sheet:1",),
            ),
            RoleSelection(role="sap", decision="missing", confidence=0.95),
        ),
    )


class _Provider:
    transport_name = "openai_compatible"

    def __init__(self, provider: str, model: str, analysis: DocumentAuthorityAnalysis):
        self.provider_name = provider
        self.model_name = model
        self.expected_response_model = model
        self.response_model = model
        self.analysis = analysis
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
                "title": "研究文件识别结果",
                "text": "基于冻结文件完成识别。",
                "structured_payload": self.analysis.model_dump(mode="json"),
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
