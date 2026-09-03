from __future__ import annotations

from typing import Any, Literal, Mapping

from packages.medical_monitoring.admission.document_authority import (
    PRIMARY_PROMPT_VERSION,
    VERIFIER_PROMPT_VERSION,
    DocumentAuthorityAnalysis,
    DocumentAuthorityError,
    DocumentAuthorityRunEnvelope,
    document_authority_batch_sha256,
    validate_document_authority_analysis,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)

from .monitoring_ai_contracts import (
    MonitoringAiCandidateStatus,
    MonitoringAiJobStatus,
    MonitoringAiTaskType,
    content_sha256,
)
from .monitoring_ai_repository import MonitoringAiRepository


def load_document_authority_analysis_run(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    job_id: str,
    candidate_batch: Mapping[str, Any],
    role: Literal["primary", "verifier"],
) -> DocumentAuthorityRunEnvelope:
    job = repository.get(project_id, job_id)
    expected = (
        (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL, PRIMARY_PROMPT_VERSION)
        if role == "primary"
        else (
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            VERIFIER_PROMPT_VERSION,
        )
    )
    if (
        job.status != MonitoringAiJobStatus.COMPLETED
        or job.task_type != MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS
        or (job.provider, job.requested_model, job.prompt_version) != expected
        or job.response_model != job.requested_model
    ):
        raise DocumentAuthorityError("document_authority_job_identity_invalid")

    batch_sha256 = document_authority_batch_sha256(candidate_batch)
    payload = repository.input_payload(project_id, job_id)
    if payload != {
        "document_authority_batch": candidate_batch,
        "document_authority_batch_sha256": batch_sha256,
        "document_authority_role": role,
    }:
        raise DocumentAuthorityError("document_authority_job_input_mismatch")

    candidates = repository.candidates(project_id, job_id)
    if (
        len(candidates) != 1
        or candidates[0].status != MonitoringAiCandidateStatus.PROPOSED
        or candidates[0].candidate_type != "document_authority_analysis"
    ):
        raise DocumentAuthorityError("document_authority_job_output_invalid")
    try:
        analysis = DocumentAuthorityAnalysis.model_validate(
            candidates[0].structured_payload
        )
        validate_document_authority_analysis(candidate_batch, analysis)
    except (ValueError, DocumentAuthorityError) as exc:
        raise DocumentAuthorityError("document_authority_job_output_invalid") from exc

    successful = [
        attempt
        for attempt in repository.attempts(project_id, job_id)
        if attempt["outcome"] in {"success", "success_repaired"}
    ]
    if len(successful) != 1:
        raise DocumentAuthorityError("document_authority_job_attempt_invalid")
    attempt = successful[0]
    response = attempt["response"]
    outputs = response.get("provider_outputs") if isinstance(response, dict) else None
    if not isinstance(outputs, list) or not outputs:
        raise DocumentAuthorityError("document_authority_job_attempt_invalid")
    final_output = outputs[-1]
    if (
        attempt["response_model"] != job.requested_model
        or content_sha256(final_output) != job.output_sha256
        or not _output_contains_analysis(final_output, analysis)
    ):
        raise DocumentAuthorityError("document_authority_job_attempt_invalid")

    return DocumentAuthorityRunEnvelope(
        run_id=str(attempt["attempt_id"]),
        job_id=job.job_id,
        role=role,
        provider=job.provider,
        model=job.requested_model,
        prompt_version=job.prompt_version,
        input_sha256=batch_sha256,
        output_sha256=content_sha256(analysis.model_dump(mode="json")),
        analysis=analysis,
    )


def _output_contains_analysis(
    output: Any, analysis: DocumentAuthorityAnalysis
) -> bool:
    if not isinstance(output, dict):
        return False
    candidates = output.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        return False
    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return False
    try:
        raw = DocumentAuthorityAnalysis.model_validate(
            candidate.get("structured_payload")
        )
    except ValueError:
        return False
    return raw == analysis
