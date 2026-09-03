from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Mapping

from packages.medical_monitoring.admission.document_authority import (
    PRIMARY_PROMPT_VERSION,
    PRIMARY_REVIEW_PROMPT_VERSION,
    VERIFIER_PROMPT_VERSION,
    VERIFIER_REVIEW_PROMPT_VERSION,
    DocumentAuthorityAnalysis,
    DocumentAuthorityConflictRunEnvelope,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    DocumentAuthorityRunEnvelope,
    build_anonymous_conflict_packet,
    document_authority_batch_sha256,
    resolve_document_authority_conflicts,
    validate_document_authority_analysis,
    validate_document_authority_conflict_review,
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

if TYPE_CHECKING:
    from .monitoring_ai_contracts import MonitoringAiInputRevision, MonitoringAiJob
    from .monitoring_ai_service import MonitoringAiService
    from .source_intake import SourceRegistryService


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

    attempt, final_output = _successful_attempt_output(repository, job)
    if not _output_contains_analysis(final_output, analysis):
        raise DocumentAuthorityError("document_authority_job_attempt_invalid")

    return DocumentAuthorityRunEnvelope(
        run_id=str(attempt["attempt_id"]),
        job_id=job.job_id,
        role=role,
        provider=job.provider,
        model=job.requested_model,
        prompt_version=job.prompt_version,
        input_sha256=batch_sha256,
        job_input_revision_sha256=job.input_revision_sha256,
        output_sha256=content_sha256(analysis.model_dump(mode="json")),
        analysis=analysis,
    )


def submit_document_authority_review_pair(
    primary_service: "MonitoringAiService",
    verifier_service: "MonitoringAiService",
    *,
    input_revision: "MonitoringAiInputRevision",
    candidate_batch: Mapping[str, Any],
    primary_analysis_job_id: str,
    verifier_analysis_job_id: str,
) -> tuple[dict[str, Any], "MonitoringAiJob", "MonitoringAiJob"]:
    repository = primary_service.repository
    if verifier_service.repository is not repository:
        raise DocumentAuthorityError("document_authority_repository_mismatch")
    project_id = input_revision.project_id
    primary_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=primary_analysis_job_id,
        candidate_batch=candidate_batch,
        role="primary",
    )
    verifier_run = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=verifier_analysis_job_id,
        candidate_batch=candidate_batch,
        role="verifier",
    )
    if input_revision.revision_sha256 != primary_run.job_input_revision_sha256:
        raise DocumentAuthorityError("document_authority_input_revision_mismatch")
    packet = build_anonymous_conflict_packet(
        candidate_batch, primary_run, verifier_run
    )
    bindings = [
        {
            "candidate_id": str(item["candidate_id"]),
            "source_entry_id": str(item["file_id"]),
            "source_content_sha256": str(item["content_sha256"]),
        }
        for item in candidate_batch["candidates"]
    ]
    primary_job = primary_service.submit_document_authority_review(
        project_id=project_id,
        input_revision=input_revision,
        conflict_packet=packet,
        source_bindings=bindings,
        role="primary",
    )
    verifier_job = verifier_service.submit_document_authority_review(
        project_id=project_id,
        input_revision=input_revision,
        conflict_packet=packet,
        source_bindings=bindings,
        role="verifier",
    )
    return packet, primary_job, verifier_job


def load_document_authority_review_run(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    job_id: str,
    candidate_batch: Mapping[str, Any],
    conflict_packet: Mapping[str, Any],
    role: Literal["primary", "verifier"],
) -> DocumentAuthorityConflictRunEnvelope:
    job = repository.get(project_id, job_id)
    expected = (
        (
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            PRIMARY_REVIEW_PROMPT_VERSION,
        )
        if role == "primary"
        else (
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            VERIFIER_REVIEW_PROMPT_VERSION,
        )
    )
    if (
        job.status != MonitoringAiJobStatus.COMPLETED
        or job.task_type != MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW
        or (job.provider, job.requested_model, job.prompt_version) != expected
        or job.response_model != job.requested_model
    ):
        raise DocumentAuthorityError("document_authority_review_job_identity_invalid")
    expected_bindings = [
        {
            "candidate_id": str(item["candidate_id"]),
            "source_entry_id": str(item["file_id"]),
            "source_content_sha256": str(item["content_sha256"]),
        }
        for item in candidate_batch["candidates"]
    ]
    payload = repository.input_payload(project_id, job_id)
    if payload != {
        "document_authority_conflict_packet": conflict_packet,
        "document_authority_conflict_packet_sha256": conflict_packet[
            "conflict_packet_sha256"
        ],
        "document_authority_role": role,
        "document_authority_source_bindings": expected_bindings,
    }:
        raise DocumentAuthorityError("document_authority_review_job_input_mismatch")

    candidates = repository.candidates(project_id, job_id)
    if (
        len(candidates) != 1
        or candidates[0].status != MonitoringAiCandidateStatus.PROPOSED
        or candidates[0].candidate_type != "document_authority_review"
    ):
        raise DocumentAuthorityError("document_authority_review_job_output_invalid")
    try:
        review = DocumentAuthorityConflictReview.model_validate(
            candidates[0].structured_payload
        )
        validate_document_authority_conflict_review(conflict_packet, review)
    except (ValueError, DocumentAuthorityError) as exc:
        raise DocumentAuthorityError(
            "document_authority_review_job_output_invalid"
        ) from exc

    attempt, final_output = _successful_attempt_output(repository, job)
    if not _output_contains_review(final_output, review):
        raise DocumentAuthorityError("document_authority_review_job_attempt_invalid")
    return DocumentAuthorityConflictRunEnvelope(
        run_id=str(attempt["attempt_id"]),
        job_id=job.job_id,
        role=role,
        provider=job.provider,
        model=job.requested_model,
        prompt_version=job.prompt_version,
        conflict_packet_sha256=review.conflict_packet_sha256,
        job_input_revision_sha256=job.input_revision_sha256,
        output_sha256=content_sha256(review.model_dump(mode="json")),
        review=review,
    )


def resolve_document_authority_from_jobs(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    candidate_batch: Mapping[str, Any],
    primary_analysis_job_id: str,
    verifier_analysis_job_id: str,
    conflict_packet: Mapping[str, Any],
    primary_review_job_id: str,
    verifier_review_job_id: str,
) -> dict[str, Any]:
    primary_analysis = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=primary_analysis_job_id,
        candidate_batch=candidate_batch,
        role="primary",
    )
    verifier_analysis = load_document_authority_analysis_run(
        repository,
        project_id=project_id,
        job_id=verifier_analysis_job_id,
        candidate_batch=candidate_batch,
        role="verifier",
    )
    expected_packet = build_anonymous_conflict_packet(
        candidate_batch, primary_analysis, verifier_analysis
    )
    if conflict_packet != expected_packet:
        raise DocumentAuthorityError("document_authority_conflict_packet_tampered")
    primary_review = load_document_authority_review_run(
        repository,
        project_id=project_id,
        job_id=primary_review_job_id,
        candidate_batch=candidate_batch,
        conflict_packet=expected_packet,
        role="primary",
    )
    verifier_review = load_document_authority_review_run(
        repository,
        project_id=project_id,
        job_id=verifier_review_job_id,
        candidate_batch=candidate_batch,
        conflict_packet=expected_packet,
        role="verifier",
    )
    return resolve_document_authority_conflicts(
        candidate_batch,
        primary_analysis,
        verifier_analysis,
        expected_packet,
        primary_review,
        verifier_review,
    )


def promote_document_authority_from_jobs(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    candidate_batch: Mapping[str, Any],
    candidate_root: Path,
    source_registry: "SourceRegistryService",
    primary_analysis_job_id: str,
    verifier_analysis_job_id: str,
    conflict_packet: Mapping[str, Any],
    primary_review_job_id: str,
    verifier_review_job_id: str,
) -> dict[str, Any]:
    resolution = resolve_document_authority_from_jobs(
        repository,
        project_id=project_id,
        candidate_batch=candidate_batch,
        primary_analysis_job_id=primary_analysis_job_id,
        verifier_analysis_job_id=verifier_analysis_job_id,
        conflict_packet=conflict_packet,
        primary_review_job_id=primary_review_job_id,
        verifier_review_job_id=verifier_review_job_id,
    )
    if resolution["state"] != "resolved":
        return {**resolution, "authority_status": "not_promoted"}

    candidates = {
        str(item["candidate_id"]): item for item in candidate_batch["candidates"]
    }
    selected = [
        item for item in resolution["resolved_roles"] if item["status"] == "selected"
    ]
    selected_ids = [str(item["candidate_id"]) for item in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise DocumentAuthorityError("document_authority_candidate_role_collision")

    prepared: list[tuple[str, Mapping[str, Any], bytes]] = []
    for item in selected:
        role = str(item["role"])
        candidate = candidates[str(item["candidate_id"])]
        if (
            candidate.get("technical_status") != "ready"
            or candidate.get("extraction_status") != "parsed"
            or role not in candidate.get("role_hypotheses", ())
        ):
            raise DocumentAuthorityError("document_authority_candidate_not_promotable")
        suffix = Path(str(candidate["filename"])).suffix.lower()
        path = Path(candidate_root) / "files" / f"{candidate['content_sha256']}{suffix}"
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise DocumentAuthorityError("document_authority_isolated_file_missing") from exc
        if hashlib.sha256(content).hexdigest() != candidate["content_sha256"]:
            raise DocumentAuthorityError("document_authority_isolated_file_hash_mismatch")
        prepared.append((role, candidate, content))

    registrations = []
    with source_registry.store.transaction():
        for role, candidate, content in prepared:
            registration = source_registry.register_monitoring_mapping_document(
                project_id,
                str(candidate["filename"]),
                content,
                document_role=role,
            )
            if registration.entry.content_hash != candidate["content_sha256"]:
                raise DocumentAuthorityError("document_authority_registration_hash_mismatch")
            if source_registry.content_validation_service is not None:
                validation = source_registry.current_content_validation(
                    project_id, registration.entry.entry_id
                )
                if (
                    validation is None
                    or validation.technical_status != "ready"
                    or validation.use_status not in {"allowed", "confirmed_after_warning"}
                ):
                    raise DocumentAuthorityError(
                        "document_authority_registration_validation_blocked"
                    )
            registrations.append({
                "role": role,
                "candidate_id": str(candidate["candidate_id"]),
                "source_entry_id": registration.entry.entry_id,
                "content_sha256": registration.entry.content_hash,
            })
    return {
        **resolution,
        "authority_status": "promoted",
        "registrations": registrations,
    }


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


def _output_contains_review(
    output: Any, review: DocumentAuthorityConflictReview
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
        raw = DocumentAuthorityConflictReview.model_validate(
            candidate.get("structured_payload")
        )
    except ValueError:
        return False
    return raw == review


def _successful_attempt_output(
    repository: MonitoringAiRepository,
    job: "MonitoringAiJob",
) -> tuple[dict[str, Any], Any]:
    successful = [
        attempt
        for attempt in repository.attempts(job.project_id, job.job_id)
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
    ):
        raise DocumentAuthorityError("document_authority_job_attempt_invalid")
    return attempt, final_output
