from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Mapping

from packages.medical_monitoring.admission.document_authority import (
    PRIMARY_ADJUDICATION_PROMPT_VERSION,
    LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION,
    LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION,
    PREVIOUS_PRIMARY_ADJUDICATION_PROMPT_VERSION,
    PREVIOUS_VERIFIER_ADJUDICATION_PROMPT_VERSION,
    PRIMARY_PROMPT_VERSION,
    PRIMARY_REVIEW_PROMPT_VERSION,
    VERIFIER_PROMPT_VERSION,
    VERIFIER_ADJUDICATION_PROMPT_VERSION,
    VERIFIER_REVIEW_PROMPT_VERSION,
    DocumentAuthorityAnalysis,
    DocumentAuthorityAdjudicationReview,
    DocumentAuthorityConflictRunEnvelope,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    DocumentAuthorityRunEnvelope,
    build_anonymous_conflict_packet,
    build_anonymous_adjudication_context,
    document_authority_batch_sha256,
    reconcile_document_authority,
    resolve_document_authority_conflicts,
    resolve_document_authority_adjudication,
    validate_document_authority_analysis,
    validate_document_authority_conflict_review,
    validate_document_authority_adjudication_context,
    validate_document_authority_adjudication_review,
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

PROMOTION_RECEIPT_SCHEMA_VERSION = "monitoring-document-authority-promotion-v3"
_PREVIOUS_PROMOTION_RECEIPT_SCHEMA_VERSION = (
    "monitoring-document-authority-promotion-v2"
)
_PRIMARY_REGISTRATION_KEYS = frozenset({
    "role",
    "candidate_id",
    "source_entry_id",
    "content_sha256",
    "binding_kind",
    "supplementary_source_entry_ids",
})
_SUPPLEMENTARY_REGISTRATION_KEYS = frozenset({
    "role",
    "candidate_id",
    "source_entry_id",
    "content_sha256",
    "binding_kind",
    "primary_candidate_id",
    "supplementary_of",
})

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


def submit_document_authority_adjudication_pair(
    primary_service: "MonitoringAiService",
    verifier_service: "MonitoringAiService",
    *,
    input_revision: "MonitoringAiInputRevision",
    candidate_batch: Mapping[str, Any],
    primary_analysis_job_id: str,
    verifier_analysis_job_id: str,
    primary_review_job_id: str,
    verifier_review_job_id: str,
) -> tuple[dict[str, Any], "MonitoringAiJob", "MonitoringAiJob"]:
    repository = primary_service.repository
    if verifier_service.repository is not repository:
        raise DocumentAuthorityError("document_authority_repository_mismatch")
    project_id = input_revision.project_id
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
    packet = build_anonymous_conflict_packet(
        candidate_batch, primary_analysis, verifier_analysis
    )
    primary_review = load_document_authority_review_run(
        repository,
        project_id=project_id,
        job_id=primary_review_job_id,
        candidate_batch=candidate_batch,
        conflict_packet=packet,
        role="primary",
    )
    verifier_review = load_document_authority_review_run(
        repository,
        project_id=project_id,
        job_id=verifier_review_job_id,
        candidate_batch=candidate_batch,
        conflict_packet=packet,
        role="verifier",
    )
    context = build_anonymous_adjudication_context(
        candidate_batch,
        primary_analysis,
        verifier_analysis,
        packet,
        primary_review,
        verifier_review,
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
        adjudication_context=context,
    )
    verifier_job = verifier_service.submit_document_authority_review(
        project_id=project_id,
        input_revision=input_revision,
        conflict_packet=packet,
        source_bindings=bindings,
        role="verifier",
        adjudication_context=context,
    )
    return context, primary_job, verifier_job


def load_document_authority_review_run(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    job_id: str,
    candidate_batch: Mapping[str, Any],
    conflict_packet: Mapping[str, Any],
    role: Literal["primary", "verifier"],
    adjudication_context: Mapping[str, Any] | None = None,
) -> DocumentAuthorityConflictRunEnvelope:
    job = repository.get(project_id, job_id)
    legacy_adjudication = (
        adjudication_context is not None
        and adjudication_context.get("schema_version")
        == "monitoring-document-authority-adjudication-v1"
    )
    expected_provider_model = (
        (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL)
        if role == "primary"
        else (MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL)
    )
    allowed_prompt_versions = (
        {
            LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION
            if role == "primary"
            else LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION
        }
        if legacy_adjudication
        else {
            PRIMARY_ADJUDICATION_PROMPT_VERSION,
            PREVIOUS_PRIMARY_ADJUDICATION_PROMPT_VERSION,
        }
        if role == "primary" and adjudication_context is not None
        else {
            VERIFIER_ADJUDICATION_PROMPT_VERSION,
            PREVIOUS_VERIFIER_ADJUDICATION_PROMPT_VERSION,
        }
        if adjudication_context is not None
        else {
            PRIMARY_REVIEW_PROMPT_VERSION
            if role == "primary"
            else VERIFIER_REVIEW_PROMPT_VERSION
        }
    )
    if (
        job.status != MonitoringAiJobStatus.COMPLETED
        or job.task_type != MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW
        or job.prompt_version not in allowed_prompt_versions
        or (job.provider, job.requested_model) != expected_provider_model
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
    expected_payload = {
        "document_authority_conflict_packet": conflict_packet,
        "document_authority_conflict_packet_sha256": conflict_packet[
            "conflict_packet_sha256"
        ],
        "document_authority_role": role,
        "document_authority_source_bindings": expected_bindings,
    }
    if adjudication_context is not None:
        validate_document_authority_adjudication_context(
            conflict_packet, adjudication_context
        )
        expected_payload["document_authority_adjudication_context"] = (
            adjudication_context
        )
    payload = repository.input_payload(project_id, job_id)
    if payload != expected_payload:
        raise DocumentAuthorityError("document_authority_review_job_input_mismatch")

    candidates = repository.candidates(project_id, job_id)
    if (
        len(candidates) != 1
        or candidates[0].status != MonitoringAiCandidateStatus.PROPOSED
        or candidates[0].candidate_type != "document_authority_review"
    ):
        raise DocumentAuthorityError("document_authority_review_job_output_invalid")
    try:
        review_model = (
            DocumentAuthorityAdjudicationReview
            if adjudication_context is not None
            and adjudication_context.get("schema_version")
            == "monitoring-document-authority-adjudication-v2"
            else DocumentAuthorityConflictReview
        )
        review = review_model.model_validate(candidates[0].structured_payload)
        if adjudication_context is not None:
            validate_document_authority_adjudication_review(
                conflict_packet, adjudication_context, review
            )
        else:
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
    conflict_packet: Mapping[str, Any] | None = None,
    primary_review_job_id: str = "",
    verifier_review_job_id: str = "",
    primary_adjudication_job_id: str = "",
    verifier_adjudication_job_id: str = "",
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
    reconciliation = reconcile_document_authority(
        candidate_batch, primary_analysis, verifier_analysis
    )
    if reconciliation["state"] == "resolved":
        return {
            "schema_version": reconciliation["schema_version"],
            "batch_id": reconciliation["batch_id"],
            "input_sha256": reconciliation["input_sha256"],
            "state": "resolved",
            "resolved_roles": reconciliation["resolved_roles"],
            "unresolved_roles": [],
            "user_question": "",
            "analysis_run_ids": reconciliation["run_ids"],
            "review_run_ids": [],
            "document_identities": _analysis_document_identities(
                primary_analysis, reconciliation["resolved_roles"]
            ),
        }
    if not primary_review_job_id or not verifier_review_job_id:
        raise DocumentAuthorityError("document_authority_review_jobs_required")
    expected_packet = build_anonymous_conflict_packet(
        candidate_batch, primary_analysis, verifier_analysis
    )
    if conflict_packet is not None and conflict_packet != expected_packet:
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
    resolved = resolve_document_authority_conflicts(
        candidate_batch,
        primary_analysis,
        verifier_analysis,
        expected_packet,
        primary_review,
        verifier_review,
    )
    identity_decisions = {
        decision.role: decision for decision in primary_review.review.decisions
    }
    if resolved["state"] != "resolved" and (
        primary_adjudication_job_id or verifier_adjudication_job_id
    ):
        if not primary_adjudication_job_id or not verifier_adjudication_job_id:
            raise DocumentAuthorityError(
                "document_authority_adjudication_jobs_required"
            )
        primary_adjudication_job = repository.get(
            project_id, primary_adjudication_job_id
        )
        verifier_adjudication_job = repository.get(
            project_id, verifier_adjudication_job_id
        )
        adjudication_prompt_versions = {
            primary_adjudication_job.prompt_version,
            verifier_adjudication_job.prompt_version,
        }
        legacy_v1 = adjudication_prompt_versions == {
            LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION,
            LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION,
        }
        adjudication_context = build_anonymous_adjudication_context(
            candidate_batch,
            primary_analysis,
            verifier_analysis,
            expected_packet,
            primary_review,
            verifier_review,
            legacy_v1=legacy_v1,
        )
        primary_adjudication = load_document_authority_review_run(
            repository,
            project_id=project_id,
            job_id=primary_adjudication_job_id,
            candidate_batch=candidate_batch,
            conflict_packet=expected_packet,
            role="primary",
            adjudication_context=adjudication_context,
        )
        verifier_adjudication = load_document_authority_review_run(
            repository,
            project_id=project_id,
            job_id=verifier_adjudication_job_id,
            candidate_batch=candidate_batch,
            conflict_packet=expected_packet,
            role="verifier",
            adjudication_context=adjudication_context,
        )
        unresolved_before_adjudication = set(resolved["unresolved_roles"])
        resolved = resolve_document_authority_adjudication(
            candidate_batch,
            primary_analysis,
            verifier_analysis,
            expected_packet,
            primary_review,
            verifier_review,
            adjudication_context,
            primary_adjudication,
            verifier_adjudication,
        )
        identity_decisions.update({
            decision.role: decision
            for decision in primary_adjudication.review.decisions
            if decision.role in unresolved_before_adjudication
        })
    document_identities = _analysis_document_identities(
        primary_analysis, resolved["resolved_roles"]
    )
    document_identities = [
        (
            {
                **identity,
                "document_version": identity_decisions[
                    identity["role"]
                ].document_version,
                "document_date": identity_decisions[identity["role"]].document_date,
            }
            if identity["role"] in identity_decisions
            else identity
        )
        for identity in document_identities
    ]
    return {
        **resolved,
        "input_sha256": reconciliation["input_sha256"],
        "analysis_run_ids": reconciliation["run_ids"],
        "document_identities": document_identities,
    }


def promote_document_authority_from_jobs(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    candidate_batch: Mapping[str, Any],
    candidate_root: Path,
    source_registry: "SourceRegistryService",
    primary_analysis_job_id: str,
    verifier_analysis_job_id: str,
    conflict_packet: Mapping[str, Any] | None = None,
    primary_review_job_id: str = "",
    verifier_review_job_id: str = "",
    primary_adjudication_job_id: str = "",
    verifier_adjudication_job_id: str = "",
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    frozen_batch = _load_json(
        candidate_root / "batches" / f"{candidate_batch['batch_id']}.json",
        "document_authority_batch_manifest_missing",
    )
    if frozen_batch != _json_value(candidate_batch):
        raise DocumentAuthorityError("document_authority_batch_manifest_mismatch")
    resolution = resolve_document_authority_from_jobs(
        repository,
        project_id=project_id,
        candidate_batch=candidate_batch,
        primary_analysis_job_id=primary_analysis_job_id,
        verifier_analysis_job_id=verifier_analysis_job_id,
        conflict_packet=conflict_packet,
        primary_review_job_id=primary_review_job_id,
        verifier_review_job_id=verifier_review_job_id,
        primary_adjudication_job_id=primary_adjudication_job_id,
        verifier_adjudication_job_id=verifier_adjudication_job_id,
    )
    if resolution["state"] != "resolved":
        return {**resolution, "authority_status": "not_promoted"}

    candidates = {
        str(item["candidate_id"]): item for item in candidate_batch["candidates"]
    }
    claims, main_candidate_by_role = _resolved_authority_claims(resolution)

    prepared: list[tuple[str, str, Mapping[str, Any], bytes]] = []
    for role, binding_kind, candidate_id in claims:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise DocumentAuthorityError(
                "document_authority_supplementary_candidate_unknown"
                if binding_kind == "supplementary"
                else "document_authority_candidate_not_promotable"
            )
        if (
            candidate.get("technical_status") != "ready"
            or candidate.get("extraction_status") != "parsed"
            or candidate.get("file_id")
            != f"mmfile_{candidate.get('content_sha256', '')}"
            or (
                binding_kind == "primary"
                and role not in candidate.get("role_hypotheses", ())
            )
        ):
            raise DocumentAuthorityError("document_authority_candidate_not_promotable")
        manifest = _load_json(
            candidate_root / "manifests" / f"{candidate['candidate_id']}.json",
            "document_authority_candidate_manifest_missing",
        )
        if manifest != _json_value(candidate):
            raise DocumentAuthorityError("document_authority_candidate_manifest_mismatch")
        suffix = Path(str(candidate["filename"])).suffix.lower()
        path = Path(candidate_root) / "files" / f"{candidate['content_sha256']}{suffix}"
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise DocumentAuthorityError("document_authority_isolated_file_missing") from exc
        if hashlib.sha256(content).hexdigest() != candidate["content_sha256"]:
            raise DocumentAuthorityError("document_authority_isolated_file_hash_mismatch")
        if len(content) != candidate.get("size_bytes"):
            raise DocumentAuthorityError("document_authority_isolated_file_size_mismatch")
        prepared.append((role, binding_kind, candidate, content))

    registrations = []
    entry_id_by_claim: dict[tuple[str, str, str], str] = {}
    with source_registry.store.transaction():
        for role, binding_kind, candidate, content in prepared:
            registration = source_registry.register_monitoring_mapping_document(
                project_id,
                str(candidate["filename"]),
                content,
                document_role=role,
                document_relation=binding_kind,
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
            claim = (role, binding_kind, str(candidate["candidate_id"]))
            item = {
                "role": role,
                "candidate_id": claim[2],
                "source_entry_id": registration.entry.entry_id,
                "content_sha256": registration.entry.content_hash,
                "binding_kind": binding_kind,
            }
            if binding_kind == "supplementary":
                item["primary_candidate_id"] = main_candidate_by_role[role]
                item["supplementary_of"] = entry_id_by_claim[
                    (role, "primary", main_candidate_by_role[role])
                ]
            registrations.append(item)
            entry_id_by_claim[claim] = registration.entry.entry_id
        supplement_entry_ids_by_role: dict[str, list[str]] = {}
        for item in registrations:
            if item["binding_kind"] == "supplementary":
                supplement_entry_ids_by_role.setdefault(item["role"], []).append(
                    item["source_entry_id"]
                )
        for item in registrations:
            if item["binding_kind"] == "primary":
                item["supplementary_source_entry_ids"] = (
                    supplement_entry_ids_by_role.get(item["role"], [])
                )
        receipt = {
            "schema_version": PROMOTION_RECEIPT_SCHEMA_VERSION,
            "batch_id": resolution["batch_id"],
            "input_sha256": resolution["input_sha256"],
            "analysis_job_ids": sorted(
                (primary_analysis_job_id, verifier_analysis_job_id)
            ),
            "review_job_ids": sorted(
                job_id
                for job_id in (primary_review_job_id, verifier_review_job_id)
                if job_id
            ),
            "adjudication_job_ids": sorted(
                job_id
                for job_id in (
                    primary_adjudication_job_id,
                    verifier_adjudication_job_id,
                )
                if job_id
            ),
            "analysis_run_ids": resolution["analysis_run_ids"],
            "review_run_ids": resolution["review_run_ids"],
            "adjudication_run_ids": resolution.get("adjudication_run_ids", []),
            "document_identities": resolution["document_identities"],
            "registrations": registrations,
        }
        receipt_sha256 = content_sha256(receipt)
        for registration in registrations:
            source_registry.store.annotate_pending_entry(
                registration["source_entry_id"],
                {
                    "monitoring_authority_status": "promoted",
                    "document_authority_receipt_sha256": receipt_sha256,
                    "document_authority_receipt": receipt,
                },
            )
    return {
        **resolution,
        "authority_status": "promoted",
        "promotion_receipt_sha256": receipt_sha256,
        "registrations": registrations,
    }


def verify_document_authority_promotion_receipt(
    repository: MonitoringAiRepository,
    *,
    project_id: str,
    receipt: Mapping[str, Any],
) -> bool:
    """Rebuild a promotion decision from immutable job evidence."""

    try:
        receipt_schema = str(receipt["schema_version"])
        if receipt_schema not in {
            _PREVIOUS_PROMOTION_RECEIPT_SCHEMA_VERSION,
            PROMOTION_RECEIPT_SCHEMA_VERSION,
        }:
            return False
        analysis_jobs = [
            repository.get(project_id, str(job_id))
            for job_id in receipt["analysis_job_ids"]
        ]
        analysis_by_role = {
            (
                "primary"
                if job.provider == MONITORING_C3_MAPPING_PROVIDER
                and job.requested_model == MONITORING_C3_MAPPING_MODEL
                else "verifier"
                if job.provider == MONITORING_C3_VERIFIER_PROVIDER
                and job.requested_model == MONITORING_C3_VERIFIER_MODEL
                else ""
            ): job
            for job in analysis_jobs
        }
        if set(analysis_by_role) != {"primary", "verifier"}:
            return False
        primary_payload = repository.input_payload(
            project_id,
            analysis_by_role["primary"].job_id,
        )
        candidate_batch = primary_payload["document_authority_batch"]
        if not isinstance(candidate_batch, Mapping):
            return False
        review_jobs = [
            repository.get(project_id, str(job_id))
            for job_id in receipt["review_job_ids"]
        ]
        review_by_role = {
            (
                "primary"
                if job.provider == MONITORING_C3_MAPPING_PROVIDER
                and job.requested_model == MONITORING_C3_MAPPING_MODEL
                else "verifier"
                if job.provider == MONITORING_C3_VERIFIER_PROVIDER
                and job.requested_model == MONITORING_C3_VERIFIER_MODEL
                else ""
            ): job
            for job in review_jobs
        }
        if review_jobs and set(review_by_role) != {"primary", "verifier"}:
            return False
        adjudication_jobs = [
            repository.get(project_id, str(job_id))
            for job_id in receipt.get("adjudication_job_ids", ())
        ]
        adjudication_by_role = {
            (
                "primary"
                if job.provider == MONITORING_C3_MAPPING_PROVIDER
                and job.requested_model == MONITORING_C3_MAPPING_MODEL
                else "verifier"
                if job.provider == MONITORING_C3_VERIFIER_PROVIDER
                and job.requested_model == MONITORING_C3_VERIFIER_MODEL
                else ""
            ): job
            for job in adjudication_jobs
        }
        if adjudication_jobs and set(adjudication_by_role) != {
            "primary",
            "verifier",
        }:
            return False
        resolution = resolve_document_authority_from_jobs(
            repository,
            project_id=project_id,
            candidate_batch=candidate_batch,
            primary_analysis_job_id=analysis_by_role["primary"].job_id,
            verifier_analysis_job_id=analysis_by_role["verifier"].job_id,
            primary_review_job_id=(
                review_by_role["primary"].job_id if review_by_role else ""
            ),
            verifier_review_job_id=(
                review_by_role["verifier"].job_id if review_by_role else ""
            ),
            primary_adjudication_job_id=(
                adjudication_by_role["primary"].job_id
                if adjudication_by_role else ""
            ),
            verifier_adjudication_job_id=(
                adjudication_by_role["verifier"].job_id
                if adjudication_by_role else ""
            ),
        )
        candidates = {
            str(item["candidate_id"]): item
            for item in candidate_batch["candidates"]
        }
        claims, _main_by_role = _resolved_authority_claims(resolution)
        registrations = list(receipt["registrations"])
        return bool(
            resolution["state"] == "resolved"
            and receipt_schema
            in {
                _PREVIOUS_PROMOTION_RECEIPT_SCHEMA_VERSION,
                PROMOTION_RECEIPT_SCHEMA_VERSION,
            }
            and receipt["batch_id"] == resolution["batch_id"]
            and receipt["input_sha256"] == resolution["input_sha256"]
            and sorted(receipt["analysis_job_ids"])
            == sorted(job.job_id for job in analysis_jobs)
            and sorted(receipt["review_job_ids"])
            == sorted(job.job_id for job in review_jobs)
            and sorted(receipt.get("adjudication_job_ids", ()))
            == sorted(job.job_id for job in adjudication_jobs)
            and sorted(receipt["analysis_run_ids"])
            == sorted(resolution["analysis_run_ids"])
            and sorted(receipt["review_run_ids"])
            == sorted(resolution["review_run_ids"])
            and sorted(receipt.get("adjudication_run_ids", ()))
            == sorted(resolution.get("adjudication_run_ids", []))
            and receipt["document_identities"] == resolution["document_identities"]
            and _registrations_bind_resolution(registrations, claims, candidates)
        )
    except (KeyError, RuntimeError, TypeError, ValueError):
        return False


def _resolved_supplementary_ids(item: Mapping[str, Any]) -> list[str]:
    """Read one resolved role's supplementary candidate IDs fail-closed."""

    raw = item.get("supplementary_candidate_ids")
    if raw is None:
        return []
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise DocumentAuthorityError(
            "document_authority_supplementary_selection_invalid"
        )
    ids = [str(value) for value in raw]
    if any(not value.strip() for value in ids) or len(ids) != len(set(ids)):
        raise DocumentAuthorityError(
            "document_authority_supplementary_selection_invalid"
        )
    return ids


def _resolved_authority_claims(
    resolution: Mapping[str, Any],
) -> tuple[list[tuple[str, str, str]], dict[str, str]]:
    """Flatten resolved roles into (role, binding_kind, candidate_id) claims.

    Every selected role contributes exactly one primary claim followed by its
    supplementary claims; a candidate claimed twice, by any combination of
    bindings or roles, is a collision.
    """

    claims: list[tuple[str, str, str]] = []
    main_candidate_by_role: dict[str, str] = {}
    for item in resolution["resolved_roles"]:
        if item["status"] != "selected":
            continue
        role = str(item["role"])
        main_candidate_id = str(item["candidate_id"])
        if role in main_candidate_by_role:
            raise DocumentAuthorityError("document_authority_candidate_role_collision")
        main_candidate_by_role[role] = main_candidate_id
        claims.append((role, "primary", main_candidate_id))
        for candidate_id in _resolved_supplementary_ids(item):
            claims.append((role, "supplementary", candidate_id))
    owner_by_candidate: dict[str, tuple[str, str]] = {}
    for role, binding_kind, candidate_id in claims:
        owner = owner_by_candidate.setdefault(candidate_id, (role, binding_kind))
        if owner != (role, binding_kind):
            raise DocumentAuthorityError("document_authority_candidate_role_collision")
    return claims, main_candidate_by_role


def _registrations_bind_resolution(
    registrations: Any,
    claims: list[tuple[str, str, str]],
    candidates: Mapping[str, Mapping[str, Any]],
) -> bool:
    """Check receipt registrations bind every resolved file and relationship."""

    if not isinstance(registrations, list):
        return False
    claim_keys = set(claims)
    registration_items: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    entry_id_by_claim: dict[tuple[str, str, str], str] = {}
    for item in registrations:
        if not isinstance(item, Mapping):
            return False
        claim = (
            str(item.get("role") or ""),
            str(item.get("binding_kind") or ""),
            str(item.get("candidate_id") or ""),
        )
        source_entry_id = str(item.get("source_entry_id") or "")
        if (
            claim not in claim_keys
            or claim in registration_items
            or not source_entry_id
            or candidates.get(claim[2], {}).get("content_sha256")
            != item.get("content_sha256")
        ):
            return False
        registration_items[claim] = item
        entry_id_by_claim[claim] = source_entry_id
    if set(registration_items) != claim_keys:
        return False
    main_candidate_by_role = {
        claim[0]: claim[2] for claim in claims if claim[1] == "primary"
    }
    for role, binding_kind, candidate_id in claims:
        item = registration_items[(role, binding_kind, candidate_id)]
        expected_keys = (
            _PRIMARY_REGISTRATION_KEYS
            if binding_kind == "primary"
            else _SUPPLEMENTARY_REGISTRATION_KEYS
        )
        if set(item) != expected_keys:
            return False
        if binding_kind == "primary":
            expected_supplement_entry_ids = sorted(
                entry_id_by_claim[claim]
                for claim in claims
                if claim[0] == role and claim[1] == "supplementary"
            )
            if (
                sorted(
                    str(value) for value in item["supplementary_source_entry_ids"]
                )
                != expected_supplement_entry_ids
            ):
                return False
        else:
            main_candidate_id = main_candidate_by_role.get(role)
            if (
                main_candidate_id is None
                or item["primary_candidate_id"] != main_candidate_id
                or item["supplementary_of"]
                != entry_id_by_claim.get((role, "primary", main_candidate_id))
            ):
                return False
    return True


def _load_json(path: Path, error_code: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DocumentAuthorityError(error_code) from exc


def _json_value(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _analysis_document_identities(
    run: DocumentAuthorityRunEnvelope,
    resolved_roles: Any,
) -> list[dict[str, str]]:
    assessments = {
        item.candidate_id: item for item in run.analysis.candidate_assessments
    }
    return [
        {
            "role": str(item["role"]),
            "candidate_id": str(item["candidate_id"]),
            "document_version": assessments[str(item["candidate_id"])].document_version,
            "document_date": assessments[str(item["candidate_id"])].document_date,
        }
        for item in resolved_roles
        if item["status"] == "selected"
    ]


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
    output: Any,
    review: DocumentAuthorityConflictReview | DocumentAuthorityAdjudicationReview,
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
        model = (
            DocumentAuthorityAdjudicationReview
            if isinstance(review, DocumentAuthorityAdjudicationReview)
            else DocumentAuthorityConflictReview
        )
        raw = model.model_validate(
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
