"""Focused contract tests for configurable medical-monitoring routes."""

from __future__ import annotations

from services.api.app.ai_role_runtime_settings import (
    INDEPENDENT_AI_DEEPSEEK_FLASH_PROFILE_ID,
    MEDICAL_MONITORING_AI_ROLE,
    AiRoleRuntimeSettingsStore,
    _builtin_profiles,
)
from services.api.app.ai_runtime_settings import AiRuntimeSettingsStore
from services.api.app.monitoring_ai_service import MonitoringAiRuntimeBinding
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
    MonitoringC3MappingGateContract,
    monitoring_mapping_runtime_matches,
    normalize_monitoring_mapping_model,
)


def test_gate_contract_aligns_primary_profile_and_verifier_preset() -> None:
    contract = MonitoringC3MappingGateContract.current()
    verifier = MonitoringC3MappingGateContract.verifier()
    profile = next(
        item for item in _builtin_profiles()
        if item.profile_id == MONITORING_C3_MAPPING_PROFILE_ID
    )

    assert contract.provider == MONITORING_C3_MAPPING_PROVIDER == profile.provider
    assert contract.model == MONITORING_C3_MAPPING_MODEL == profile.model
    assert profile.provider == contract.provider
    assert profile.model == contract.model
    assert profile.expected_response_model == contract.model
    assert profile.base_url == contract.base_url
    assert profile.api_key_env == contract.api_key_env
    assert contract.preset_id == "cms_router"
    assert verifier.provider == MONITORING_C3_VERIFIER_PROVIDER == "ollama-cloud"
    assert verifier.model == MONITORING_C3_VERIFIER_MODEL == "deepseek-v4.1-flash"
    assert verifier.base_url == "https://ollama.com/v1"


def test_zhipu_profile_does_not_replace_deepseek_capability() -> None:
    profile_ids = {item.profile_id for item in _builtin_profiles()}
    assert MONITORING_C3_MAPPING_PROFILE_ID in profile_ids
    assert INDEPENDENT_AI_DEEPSEEK_FLASH_PROFILE_ID in profile_ids


def test_monitoring_role_defaults_to_configured_pair_without_changing_independent_ai(tmp_path) -> None:
    provider_store = AiRuntimeSettingsStore(tmp_path / "providers.json")
    store = AiRoleRuntimeSettingsStore(tmp_path / "roles.json", provider_store)
    monitoring = store.binding(MEDICAL_MONITORING_AI_ROLE)
    independent = store.binding("independent_ai")

    assert monitoring.profile_id == MONITORING_C3_MAPPING_PROFILE_ID
    assert monitoring.model == MONITORING_C3_MAPPING_MODEL
    assert monitoring.thinking == "enabled"
    assert monitoring.reasoning_effort == "high"
    assert independent.profile_id == INDEPENDENT_AI_DEEPSEEK_FLASH_PROFILE_ID


def test_normalize_monitoring_mapping_model_is_case_insensitive() -> None:
    assert normalize_monitoring_mapping_model("glm-5.3-flash") == MONITORING_C3_MAPPING_MODEL
    assert normalize_monitoring_mapping_model("GLM-5.3-FLASH") == MONITORING_C3_MAPPING_MODEL
    assert normalize_monitoring_mapping_model("DEEPSEEK-V4.1-FLASH") == MONITORING_C3_VERIFIER_MODEL


def test_monitoring_mapping_runtime_matches_accepts_case_variant_model() -> None:
    runtime = MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        provider=MONITORING_C3_MAPPING_PROVIDER,
        model="GLM-5.3-FLASH",
        env={},
        available=True,
    )
    assert monitoring_mapping_runtime_matches(runtime) is True


def test_monitoring_mapping_runtime_matches_accepts_explicit_custom_route() -> None:
    runtime = MonitoringAiRuntimeBinding(
        profile_id="medical_monitoring_ai__custom",
        provider="custom-router",
        model="custom-medical-model",
        env={},
        available=True,
    )

    assert monitoring_mapping_runtime_matches(
        runtime,
        required_provider="custom-router",
        required_model="custom-medical-model",
    ) is True


def test_monitoring_mapping_runtime_rejects_deepseek_fallback() -> None:
    runtime = MonitoringAiRuntimeBinding(
        profile_id="independent_ai__deepseek_v4_flash",
        provider="deepseek",
        model="deepseek-v4-flash",
        env={},
        available=True,
    )
    assert monitoring_mapping_runtime_matches(runtime) is False


def test_primary_gate_rejects_verifier_route() -> None:
    runtime = MonitoringAiRuntimeBinding(
        profile_id="independent_ai__zhipu_coding_plan_glm_flash",
        provider=MONITORING_C3_VERIFIER_PROVIDER,
        model=MONITORING_C3_VERIFIER_MODEL,
        env={},
        available=True,
    )
    assert monitoring_mapping_runtime_matches(runtime) is False
    assert monitoring_mapping_runtime_matches(
        runtime,
        required_provider=MONITORING_C3_VERIFIER_PROVIDER,
        required_model=MONITORING_C3_VERIFIER_MODEL,
    ) is True
