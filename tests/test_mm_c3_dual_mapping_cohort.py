"""Dual-cohort identity, blind input and namespace tests for C3 mapping.

The primary cohort (MiniMax direct analysis) and the independent verifier
cohort (GLM blind re-check) must submit into the same durable repository
without ever sharing runtime identity, business-key namespace, or prompt
version, and the verifier input must stay bit-identical to the blind profile.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest

from packages.medical_monitoring.admission import (
    AdmissionMappingPipeline,
    AdmissionMappingPipelineError,
    DataAdmissionPipeline,
    MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
    MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX,
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
    MONITORING_MAPPING_COHORT_PRIMARY,
    MONITORING_MAPPING_COHORT_VERIFIER,
    monitoring_mapping_cohort_contract,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_ALTERNATE_MODEL,
    MONITORING_C3_ALTERNATE_PROVIDER,
    MONITORING_C3_LOCAL_FALLBACK_MODEL,
    MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_REMOTE_UNAVAILABLE_ENV,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROFILE_ID,
    MONITORING_C3_VERIFIER_PROVIDER,
)
from services.api.app.listing_file_parser import parse_listing_file
from services.api.app.ai_gateway import AiPromptEnvelope
from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiInputRevision,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from tests.medical_monitoring.relationship_profiler_stub import (
    build_relationship_profile as _stub_profiler,
)


PROJECT_ID = "c3-dual-cohort-demo"


def _xlsx_bytes() -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = "生命体征"
    first.append([
        "受试者编号(SUBJID)",
        "访视(VISIT)",
        "测量日期(VSDAT)",
        "收缩压(SYSBP)",
    ])
    first.append(["S001", "筛选期", "2026-01-05", 120])
    first.append(["S002", "筛选期", "2026-01-06", 118])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _workspace(tmp_path: Path) -> Path:
    return tmp_path / "runtime" / PROJECT_ID


def _admit(tmp_path: Path) -> tuple[str, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.xlsx").write_bytes(_xlsx_bytes())
    workspace = _workspace(tmp_path)
    result = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )
    return str(result["attempt_id"]), workspace


def _runtime_env(provider: str, model: str) -> dict[str, str]:
    return {
        "WORKBENCH_AI_PROVIDER": provider,
        "WORKBENCH_AI_TRANSPORT": "openai_compatible",
        "WORKBENCH_AI_BASE_URL": "https://example.invalid/v1",
        "WORKBENCH_AI_API_KEY": "test-key",
        "WORKBENCH_AI_MODEL": model,
        "WORKBENCH_AI_EXPECTED_RESPONSE_MODEL": model,
        "WORKBENCH_AI_DEPLOYMENT_PROFILE": "local_private_clinical",
    }


def _primary_runtime() -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        provider=MONITORING_C3_MAPPING_PROVIDER,
        model=MONITORING_C3_MAPPING_MODEL,
        env=_runtime_env(MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
        available=True,
    )


def _verifier_runtime() -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
        provider=MONITORING_C3_VERIFIER_PROVIDER,
        model=MONITORING_C3_VERIFIER_MODEL,
        env=_runtime_env(MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL),
        available=True,
    )


class _CohortProvider:
    """Minimal openai_compatible provider stamped with one cohort identity."""

    transport_name = "openai_compatible"

    def __init__(self, *, provider_name: str, model_name: str) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.expected_response_model = model_name
        self.response_model = model_name
        self.envelopes: list[AiPromptEnvelope] = []

    def run(self, envelope: AiPromptEnvelope) -> dict[str, Any]:
        self.envelopes.append(envelope)
        payload = envelope.payload
        original = payload.get("original_task") or payload
        original_payload = original["input_payload"]
        task_type = MonitoringAiTaskType(
            payload["monitoring_task_type"]
            if "monitoring_task_type" in payload
            else original["monitoring_task_type"]
        )
        revision_hash = payload.get("input_revision_sha256")
        if revision_hash is None:
            revision_hash = original["input_revision_sha256"]
        fields = original_payload["field_profile"]["fields"]
        source = payload["authorized_source_pairs"][0]
        evidence = []
        field_mappings = []
        for index, field in enumerate(fields, start=1):
            evidence_id = f"evidence-{index}"
            evidence.append({
                "evidence_id": evidence_id,
                "source_entry_id": source["source_entry_id"],
                "source_content_sha256": source["source_content_sha256"],
                "locator": f"profile://{field['domain']}/{field['field']}",
                "quote": "",
                "raw_fields": {
                    "domain": field["domain"],
                    "field": field["field"],
                    "inferred_type": field["inferred_type"],
                },
            })
            field_mappings.append({
                "domain": field["domain"],
                "source_field": field["field"],
                "recommended_role": "lab_result_candidate",
                "field_kind": "source_collected",
                "confidence": 0.82,
                "uncertainty": "仍需核对单位和参考范围字段。",
                "user_action": "请逐项确认或修订。",
                "user_decision_required": False,
                "related_fields": [],
                "evidence_ids": [evidence_id],
            })
        return {
            "schema_version": MONITORING_AI_SCHEMA_VERSION,
            "task_id": envelope.task_id,
            "task_type": task_type.value,
            "input_revision_sha256": revision_hash,
            "candidates": [{
                "candidate_type": "listing_field_mapping_set",
                "title": "完整字段语义映射候选",
                "text": "完整覆盖冻结批次字段画像，供医学经理确认。",
                "structured_payload": {"field_mappings": field_mappings},
                "claims": [],
                "evidence": evidence,
            }],
        }


def _dual_pipeline(
    tmp_path: Path,
    *,
    primary_runtime=None,
    verifier_runtime=None,
) -> tuple[AdmissionMappingPipeline, MonitoringAiRepository]:
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    primary_service = MonitoringAiService(
        repository,
        runtime_resolver=primary_runtime or _primary_runtime,
        provider_factory=lambda _env: _CohortProvider(
            provider_name=MONITORING_C3_MAPPING_PROVIDER,
            model_name=MONITORING_C3_MAPPING_MODEL,
        ),
    )
    verifier_service = MonitoringAiService(
        repository,
        runtime_resolver=verifier_runtime or _verifier_runtime,
        provider_factory=lambda _env: _CohortProvider(
            provider_name=MONITORING_C3_VERIFIER_PROVIDER,
            model_name=MONITORING_C3_VERIFIER_MODEL,
        ),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=primary_service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        verifier_ai_service=verifier_service,
        relationship_profiler=_stub_profiler,
    )
    return pipeline, repository


def test_cohort_contracts_carry_distinct_identity_and_namespace() -> None:
    primary = monitoring_mapping_cohort_contract(MONITORING_MAPPING_COHORT_PRIMARY)
    verifier = monitoring_mapping_cohort_contract(MONITORING_MAPPING_COHORT_VERIFIER)

    assert (primary.provider, primary.model, primary.profile_id) == (
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        MONITORING_C3_MAPPING_PROFILE_ID,
    )
    assert (verifier.provider, verifier.model, verifier.profile_id) == (
        MONITORING_C3_VERIFIER_PROVIDER,
        MONITORING_C3_VERIFIER_MODEL,
        MONITORING_C3_VERIFIER_PROFILE_ID,
    )
    assert (
        primary.business_key_prefix
        == MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX
        != MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX
        == verifier.business_key_prefix
    )
    assert primary.prompt_version == ""
    assert verifier.prompt_version == MONITORING_C3_VERIFIER_PROMPT_VERSION
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        AdmissionMappingPipeline()._cohort_contract("shadow")
    assert exc_info.value.code == "mapping_cohort_invalid"


def test_verifier_cohort_gate_is_strict_without_fallback_routes() -> None:
    verifier = monitoring_mapping_cohort_contract(MONITORING_MAPPING_COHORT_VERIFIER)

    assert verifier.runtime_matches(_verifier_runtime()) is True
    # The cms-router alternate route belongs to the primary cohort only.
    assert (
        verifier.runtime_matches(
            MonitoringAiRuntimeBinding(
                profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
                provider=MONITORING_C3_ALTERNATE_PROVIDER,
                model=MONITORING_C3_ALTERNATE_MODEL,
                env={},
                available=True,
            )
        )
        is False
    )
    # The admitted local MTPLX fallback must never pass as the verifier.
    assert (
        verifier.runtime_matches(
            MonitoringAiRuntimeBinding(
                profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
                provider=MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
                model=MONITORING_C3_LOCAL_FALLBACK_MODEL,
                env={MONITORING_C3_REMOTE_UNAVAILABLE_ENV: "true"},
                available=True,
            )
        )
        is False
    )


def test_verifier_submission_uses_blind_input_and_own_namespace(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    pipeline, repository = _dual_pipeline(tmp_path)

    primary = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    verifier = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
        cohort=MONITORING_MAPPING_COHORT_VERIFIER,
    )

    assert primary["cohort"] == MONITORING_MAPPING_COHORT_PRIMARY
    assert verifier["cohort"] == MONITORING_MAPPING_COHORT_VERIFIER
    assert verifier["execution"]["providers"] == [MONITORING_C3_VERIFIER_PROVIDER]
    assert verifier["execution"]["requested_models"] == [MONITORING_C3_VERIFIER_MODEL]

    primary_jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=f"{MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX}:{attempt_id}:",
    )
    verifier_jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=f"{MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX}:{attempt_id}:",
    )
    assert primary_jobs and verifier_jobs
    assert all(
        job.prompt_version == "monitoring-listing-field-mapping-v19"
        for job in primary_jobs
    )
    assert all(
        job.prompt_version == MONITORING_C3_VERIFIER_PROMPT_VERSION
        for job in verifier_jobs
    )
    assert all(
        job.provider == MONITORING_C3_VERIFIER_PROVIDER
        and job.requested_model == MONITORING_C3_VERIFIER_MODEL
        for job in verifier_jobs
    )
    # Dual-cohort input validation premise: both cohorts map the identical
    # frozen input, relationship evidence included, so every job of the same
    # attempt carries one shared input revision digest.
    assert {
        str(job.input_revision_sha256) for job in primary_jobs
    } == {
        str(job.input_revision_sha256) for job in verifier_jobs
    }

    # Blind input: the verifier payload is the identical deterministic
    # profile — same digest, no primary analysis results, no adjudication
    # context of any kind.
    primary_payload = repository.input_payload(
        PROJECT_ID, primary_jobs[0].job_id
    )
    verifier_payload = repository.input_payload(
        PROJECT_ID, verifier_jobs[0].job_id
    )
    primary_profile = primary_payload["field_profile"]
    verifier_profile = verifier_payload["field_profile"]
    assert verifier_profile["profile_sha256"] == primary_profile["profile_sha256"]
    assert verifier_profile == primary_profile
    forbidden_keys = {
        "adjudication_contract",
        "first_pass_mappings",
        "read_only_adjudication_context_profiles",
    }
    assert not forbidden_keys.intersection(verifier_profile)
    assert not forbidden_keys.intersection(str(verifier_payload))


def test_cohort_listings_stay_isolated_by_namespace(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    pipeline, repository = _dual_pipeline(tmp_path)
    pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
        cohort=MONITORING_MAPPING_COHORT_VERIFIER,
    )

    primary_view = pipeline.list_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    verifier_view = pipeline.list_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
        cohort=MONITORING_MAPPING_COHORT_VERIFIER,
    )

    assert primary_view["cohort"] == MONITORING_MAPPING_COHORT_PRIMARY
    assert primary_view["execution"]["providers"] == [MONITORING_C3_MAPPING_PROVIDER]
    assert verifier_view["cohort"] == MONITORING_MAPPING_COHORT_VERIFIER
    assert verifier_view["execution"]["providers"] == [MONITORING_C3_VERIFIER_PROVIDER]


def test_verifier_generation_without_verifier_runtime_sends_nothing(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    # Misconfiguration: the verifier service is bound to the primary runtime.
    pipeline, repository = _dual_pipeline(
        tmp_path,
        verifier_runtime=_primary_runtime,
    )

    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
            cohort=MONITORING_MAPPING_COHORT_VERIFIER,
        )
    assert exc_info.value.code == "mapping_model_not_configured"
    assert repository.list_jobs(
        PROJECT_ID,
        business_key_prefix=f"{MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX}:{attempt_id}:",
    ) == ()

    # An admitted local fallback must not count as the verifier either.
    fallback_runtime = MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
        provider=MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
        model=MONITORING_C3_LOCAL_FALLBACK_MODEL,
        env={
            **_runtime_env(
                MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
                MONITORING_C3_LOCAL_FALLBACK_MODEL,
            ),
            MONITORING_C3_REMOTE_UNAVAILABLE_ENV: "true",
        },
        available=True,
    )
    pipeline, repository = _dual_pipeline(
        tmp_path,
        verifier_runtime=lambda: fallback_runtime,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
            cohort=MONITORING_MAPPING_COHORT_VERIFIER,
        )
    assert exc_info.value.code == "mapping_model_not_configured"
    assert repository.list_jobs(PROJECT_ID) == ()


def test_verifier_cohort_requires_verifier_service_configuration(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(
            repository,
            runtime_resolver=_primary_runtime,
            provider_factory=lambda _env: _CohortProvider(
                provider_name=MONITORING_C3_MAPPING_PROVIDER,
                model_name=MONITORING_C3_MAPPING_MODEL,
            ),
        ),
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
            cohort=MONITORING_MAPPING_COHORT_VERIFIER,
        )
    assert exc_info.value.code == "mapping_verifier_unconfigured"


def test_claim_identity_filter_keeps_cohorts_from_stealing_jobs(
    tmp_path: Path,
) -> None:
    attempt_id, _workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")

    def _queue_job(job_id: str, provider: str, model: str, profile_id: str) -> None:
        revision = MonitoringAiInputRevision(
            project_id=PROJECT_ID,
            batch_revision=attempt_id,
            sources=(
                MonitoringAiSourceBinding(
                    source_entry_id="source-listing",
                    source_content_sha256="a" * 64,
                ),
            ),
        )
        repository.create_or_get(
            _job_create(
                job_id=job_id,
                provider=provider,
                model=model,
                profile_id=profile_id,
                revision=revision,
            )
        )

    def _job_create(
        *,
        job_id: str,
        provider: str,
        model: str,
        profile_id: str,
        revision: MonitoringAiInputRevision,
    ):
        from services.api.app.monitoring_ai_contracts import MonitoringAiJobCreate

        return MonitoringAiJobCreate(
            project_id=PROJECT_ID,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload={"field_profile": {"fields": []}},
            prompt_version="monitoring-listing-field-mapping-v19",
            profile_id=profile_id,
            provider=provider,
            requested_model=model,
            max_attempts=2,
            business_key=f"listing-field-mapping:{attempt_id}:{job_id}",
        )

    _queue_job(
        "primary-1",
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        MONITORING_C3_MAPPING_PROFILE_ID,
    )
    _queue_job(
        "verifier-1",
        MONITORING_C3_VERIFIER_PROVIDER,
        MONITORING_C3_VERIFIER_MODEL,
        MONITORING_C3_VERIFIER_PROFILE_ID,
    )

    primary_claim = repository.claim_next(
        "primary-owner",
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        provider=MONITORING_C3_MAPPING_PROVIDER,
        requested_model=MONITORING_C3_MAPPING_MODEL,
    )
    assert primary_claim is not None
    assert primary_claim.business_key.endswith(":primary-1")
    verifier_claim = repository.claim_next(
        "verifier-owner",
        profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
        provider=MONITORING_C3_VERIFIER_PROVIDER,
        requested_model=MONITORING_C3_VERIFIER_MODEL,
    )
    assert verifier_claim is not None
    assert verifier_claim.business_key.endswith(":verifier-1")
    # Each cohort's queue is drained for its own identity: the other identity
    # filter must not observe jobs of the first cohort.
    assert (
        repository.claim_next(
            "verifier-owner-2",
            profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
            provider=MONITORING_C3_VERIFIER_PROVIDER,
            requested_model=MONITORING_C3_VERIFIER_MODEL,
        )
        is None
    )


def test_dual_cohort_queue_completes_both_cohorts_without_cross_failures(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    pipeline, repository = _dual_pipeline(tmp_path)
    primary_result = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    verifier_result = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
        cohort=MONITORING_MAPPING_COHORT_VERIFIER,
    )
    assert primary_result["summary"]["job_count"] >= 1
    assert verifier_result["summary"]["job_count"] >= 1

    primary_service = pipeline._service
    verifier_service = pipeline._verifier_service
    for _ in range(12):
        result = primary_service.run_next(
            "primary-worker",
            claim_identity=primary_service.claim_identity(),
        )
        if not result.processed:
            break
    for _ in range(12):
        result = verifier_service.run_next(
            "verifier-worker",
            claim_identity=verifier_service.claim_identity(),
        )
        if not result.processed:
            break

    for cohort_prefix in (
        MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
        MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX,
    ):
        jobs = repository.list_jobs(
            PROJECT_ID,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
            business_key_prefix=f"{cohort_prefix}:{attempt_id}:",
        )
        assert jobs
        assert all(
            str(_value_status(job.status)) == "completed" for job in jobs
        ), [str(_value_status(job.status)) for job in jobs]


def _value_status(status: Any) -> Any:
    return getattr(status, "value", status)


def test_verifier_role_defaults_to_glm_verifier_profile(tmp_path: Path) -> None:
    from services.api.app.ai_role_runtime_settings import (
        MEDICAL_MONITORING_VERIFIER_AI_ROLE,
        AiRoleRuntimeSettingsStore,
    )
    from services.api.app.ai_runtime_settings import AiRuntimeSettingsStore

    provider_store = AiRuntimeSettingsStore(tmp_path / "providers.json")
    store = AiRoleRuntimeSettingsStore(tmp_path / "roles.json", provider_store)
    binding = store.binding(MEDICAL_MONITORING_VERIFIER_AI_ROLE)
    profile = provider_store.profile(binding.profile_id)

    assert binding.profile_id == MONITORING_C3_VERIFIER_PROFILE_ID
    assert binding.model == MONITORING_C3_VERIFIER_MODEL
    assert binding.enabled is True
    assert profile.provider == MONITORING_C3_VERIFIER_PROVIDER
    assert profile.model == MONITORING_C3_VERIFIER_MODEL
