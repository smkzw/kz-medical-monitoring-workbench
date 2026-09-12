"""C3 listing field-mapping gate for approved direct harness routes.

The gate is the single source of truth for the provider/model identity that
AdmissionMappingPipeline accepts before submitting candidate jobs. Product
registry presets and role profiles must stay aligned with these constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION = "mm-c3-dual-mapping-gate-v1"
# The dual-cohort contract gives the primary analysis and the independent
# verifier distinct runtime identities, queue namespaces, and prompt versions
# over the same shared job repository.
MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION = "mm-c3-dual-mapping-cohort-v1"
# The primary route is the direct CMS endpoint.  ``cms-router`` remains a
# supported transport identity for installations that expose the same route
# through the local CMS router, but it is not an OMP invocation.
# 2026-09-12 user redesignation: the primary analysis route is DeepSeek
# flash at max thinking (api.deepseek.com, request==response identity
# ``deepseek-flash``). The previous cms-router MiniMax route remains a
# supported historical identity: persisted primary jobs and receipts under
# cms-smk/MiniMax-M3 (and the cms-router alternate) must keep revalidating.
MONITORING_C3_MAPPING_PROVIDER = "deepseek"
MONITORING_C3_MAPPING_MODEL = "deepseek-flash"
MONITORING_C3_MAPPING_PROFILE_ID = "medical_monitoring_ai__deepseek_flash"
MONITORING_C3_CMS_PRIMARY_PROVIDER = "cms-smk"
MONITORING_C3_CMS_PRIMARY_MODEL = "MiniMax-M3"
MONITORING_C3_CMS_PRIMARY_PROFILE_ID = "medical_monitoring_ai__cms_smk_minimax_m3"
MONITORING_C3_ALTERNATE_PROVIDER = "cms-router"
MONITORING_C3_ALTERNATE_MODEL = "minimax-m3"
# 2026-09-12 user redesignation: the verifier cohort is the LOCAL MTPLX VLM
# (Youssofal--Qwen3.8-Flash-Next-MTPLX-Optimized-Speed served as
# ``mtplx-flash-next-optimized-speed``, thinking xhigh, ~200k effective
# context, native VLM). The previous cloud GLM pair remains a supported
# verifier transport for historical receipts and as the remote substitute;
# new submissions bind to mtplx.
MONITORING_C3_VERIFIER_PROVIDER = "mtplx"
MONITORING_C3_VERIFIER_MODEL = "mtplx-flash-next-optimized-speed"
MONITORING_C3_VERIFIER_PROFILE_ID = (
    "medical_monitoring_verifier__mtplx_qwen38_flash_next"
)
MONITORING_C3_GLM_VERIFIER_PROVIDER = "zhipu-coding-plan"
MONITORING_C3_GLM_VERIFIER_MODEL = "glm-5.3-flash"
MONITORING_C3_GLM_VERIFIER_PROFILE_ID = (
    "independent_ai__zhipu_coding_plan_glm_flash"
)
MONITORING_MAPPING_COHORT_PRIMARY = "primary"
MONITORING_MAPPING_COHORT_VERIFIER = "verifier"
MONITORING_MAPPING_COHORTS = frozenset({
    MONITORING_MAPPING_COHORT_PRIMARY,
    MONITORING_MAPPING_COHORT_VERIFIER,
})
# Business-key namespaces. The primary prefix keeps its historical value so
# existing primary jobs stay addressable; the verifier prefix must never match
# the primary prefix or the draft-assembly/confirmation prefix filters.
MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX = "listing-field-mapping"
MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX = "listing-field-mapping-verifier"
# The verifier prompt version lives in this namespace contract because the
# verifier prompt must evolve independently of the primary prompt owned by
# the service layer.
MONITORING_C3_VERIFIER_PROMPT_VERSION = (
    "monitoring-listing-field-mapping-verifier-v1"
)
MONITORING_C3_LOCAL_FALLBACK_PROVIDER = "mtplx"
MONITORING_C3_LOCAL_FALLBACK_MODEL = "mtplx-flash-next-optimized-speed"
# Post-hoc classification of what actually executed, used by the migration
# gate and by the dual-model-pass contract. Deterministic system-owned jobs
# (for example metadata-only mapping) are not classified here; callers inject
# their own identities where those identities are defined.
MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY = "primary"
MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK = "primary_fallback"
MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER = "verifier"
MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED = "unrecognized"
# Cohort-summary-only value for a job set that executed no LLM route at all.
MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY = "system_only"
MONITORING_C3_SUPPORTED_RUNTIMES = frozenset({
    (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
    (MONITORING_C3_ALTERNATE_PROVIDER, MONITORING_C3_ALTERNATE_MODEL),
    (MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL),
    (
        MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
        MONITORING_C3_LOCAL_FALLBACK_MODEL,
    ),
})
# Every verifier identity that persisted jobs may legally carry: the current
# local MTPLX verifier plus the historical cloud GLM verifier whose completed
# jobs/receipts must keep revalidating after the redesignation.
MONITORING_C3_VERIFIER_RUNTIME_PAIRS = frozenset({
    (MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL),
    (MONITORING_C3_GLM_VERIFIER_PROVIDER, MONITORING_C3_GLM_VERIFIER_MODEL),
})
MONITORING_C3_PRIMARY_RUNTIME_PAIRS = frozenset({
    (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
    (MONITORING_C3_CMS_PRIMARY_PROVIDER, MONITORING_C3_CMS_PRIMARY_MODEL),
    (MONITORING_C3_ALTERNATE_PROVIDER, MONITORING_C3_ALTERNATE_MODEL),
})


def is_monitoring_primary_runtime(provider: str, model: str) -> bool:
    return (str(provider or ""), str(model or "")) in (
        MONITORING_C3_PRIMARY_RUNTIME_PAIRS
    )


def is_monitoring_verifier_runtime(provider: str, model: str) -> bool:
    return (str(provider or ""), str(model or "")) in (
        MONITORING_C3_VERIFIER_RUNTIME_PAIRS
    )
ZHIPU_CODING_PLAN_PRESET_ID = "zhipu_coding_plan"
ZHIPU_CODING_PLAN_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"
ZHIPU_CODING_PLAN_API_KEY_ENV = "ZAI_CODING_CN_API_KEY"
ZHIPU_CODING_PLAN_API_KEY_ENV_ALIASES = (
    ZHIPU_CODING_PLAN_API_KEY_ENV,
    "ZHIPU_CODING_PLAN_API_KEY",
)
CMS_SMK_PRESET_ID = "cms_smk"
CMS_SMK_BASE_URL = "https://new-api.mediportal.com.cn/v1"
CMS_SMK_API_KEY_ENV = "CMS_SMK_API_KEY"


def normalize_monitoring_mapping_model(model: str) -> str:
    """Return the canonical configured model id, preserving unknown values."""

    cleaned = str(model or "").strip()
    if cleaned.casefold() == MONITORING_C3_MAPPING_MODEL.casefold():
        return MONITORING_C3_MAPPING_MODEL
    if cleaned.casefold() == MONITORING_C3_VERIFIER_MODEL.casefold():
        return MONITORING_C3_VERIFIER_MODEL
    return cleaned


def _runtime_field(runtime: Mapping[str, Any] | Any, name: str, default: Any = "") -> Any:
    if hasattr(runtime, name):
        return getattr(runtime, name)
    if isinstance(runtime, Mapping):
        return runtime.get(name, default)
    return default


def monitoring_mapping_runtime_matches(
    runtime: Mapping[str, Any] | Any,
    *,
    required_provider: str = MONITORING_C3_MAPPING_PROVIDER,
    required_model: str = MONITORING_C3_MAPPING_MODEL,
) -> bool:
    """Return whether *runtime* satisfies the C3 mapping gate."""

    available = bool(_runtime_field(runtime, "available", False))
    provider = str(_runtime_field(runtime, "provider", "")).strip()
    model = normalize_monitoring_mapping_model(str(_runtime_field(runtime, "model", "")))
    required_model = normalize_monitoring_mapping_model(required_model)
    requested = (required_provider, required_model.casefold())
    actual = (provider, model.casefold())
    if requested == (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL.casefold()):
        if actual == (
            MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
            MONITORING_C3_LOCAL_FALLBACK_MODEL.casefold(),
        ):
            # Local admission needs repository-backed terminal evidence from
            # both remote routes; a runtime/env declaration is never proof.
            return False
        return available and is_monitoring_primary_runtime(
            provider, model
        )
    return available and actual == requested


def monitoring_mapping_execution_route(provider: str, model: str) -> str:
    """Classify an executed (provider, model) identity against the gate.

    This is post-hoc classification of what actually ran, not admission:
    the local fallback is recognized without the remote-unavailable env,
    because that env governs submission admission, not history.
    """

    cleaned_provider = str(provider or "").strip()
    cleaned_model = normalize_monitoring_mapping_model(str(model or ""))
    identity = (cleaned_provider, cleaned_model.casefold())
    if identity in {
        (MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL.casefold()),
        (MONITORING_C3_ALTERNATE_PROVIDER, MONITORING_C3_ALTERNATE_MODEL.casefold()),
    }:
        return MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
    if identity == (
        MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
        MONITORING_C3_LOCAL_FALLBACK_MODEL.casefold(),
    ):
        return MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
    if identity == (
        MONITORING_C3_VERIFIER_PROVIDER,
        MONITORING_C3_VERIFIER_MODEL.casefold(),
    ):
        return MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER
    return MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED


def monitoring_mapping_cohort_dual_model_eligible(routes: Any) -> bool:
    """Return whether an executed LLM route set can back a dual-model pass.

    Only a remote primary route can. A local-fallback first pass must never
    be presented as dual-model agreement, even when a verifier cohort later
    agrees with it.
    """

    executed = [
        route
        for route in (routes or ())
        if route
        in {
            MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
            MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK,
        }
    ]
    return bool(executed) and all(
        route == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
        for route in executed
    )


@dataclass(frozen=True)
class MonitoringC3MappingGateContract:
    schema_version: str
    provider: str
    model: str
    profile_id: str
    preset_id: str
    base_url: str
    api_key_env: str

    @classmethod
    def current(cls) -> "MonitoringC3MappingGateContract":
        return cls(
            schema_version=MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION,
            provider=MONITORING_C3_MAPPING_PROVIDER,
            model=MONITORING_C3_MAPPING_MODEL,
            profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
            preset_id=CMS_SMK_PRESET_ID,
            base_url=CMS_SMK_BASE_URL,
            api_key_env=CMS_SMK_API_KEY_ENV,
        )

    @classmethod
    def verifier(cls) -> "MonitoringC3MappingGateContract":
        return cls(
            schema_version=MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION,
            provider=MONITORING_C3_VERIFIER_PROVIDER,
            model=MONITORING_C3_VERIFIER_MODEL,
            profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
            preset_id=ZHIPU_CODING_PLAN_PRESET_ID,
            base_url=ZHIPU_CODING_PLAN_BASE_URL,
            api_key_env=ZHIPU_CODING_PLAN_API_KEY_ENV,
        )


@dataclass(frozen=True)
class MonitoringMappingCohortContract:
    """Runtime identity and queue namespace for one mapping cohort.

    ``primary`` is the MiniMax direct-analysis cohort; ``verifier`` is the
    independent GLM blind-verification cohort. Both submit into the same
    durable job repository but never share business keys, prompt versions, or
    runtime identities.
    """

    cohort: str
    provider: str
    model: str
    profile_id: str
    business_key_prefix: str
    # Empty means the service-layer default prompt version stays authoritative
    # (primary keeps its historical behavior). The verifier owns its version.
    prompt_version: str

    def runtime_matches(self, runtime: Mapping[str, Any] | Any) -> bool:
        return monitoring_mapping_runtime_matches(
            runtime,
            required_provider=self.provider,
            required_model=self.model,
        )

    def job_business_key_prefix(self, attempt_id: str) -> str:
        cleaned = str(attempt_id or "").strip()
        if not cleaned:
            raise ValueError("mapping cohort business key requires an attempt id")
        return f"{self.business_key_prefix}:{cleaned}:"


def monitoring_mapping_cohort_contract(
    cohort: str,
) -> MonitoringMappingCohortContract:
    """Return the gate contract for a mapping cohort name (fail-closed)."""

    cleaned = str(cohort or "").strip()
    if cleaned not in MONITORING_MAPPING_COHORTS:
        raise ValueError("mapping cohort is invalid")
    if cleaned == MONITORING_MAPPING_COHORT_VERIFIER:
        return MonitoringMappingCohortContract(
            cohort=cleaned,
            provider=MONITORING_C3_VERIFIER_PROVIDER,
            model=MONITORING_C3_VERIFIER_MODEL,
            profile_id=MONITORING_C3_VERIFIER_PROFILE_ID,
            business_key_prefix=MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX,
            prompt_version=MONITORING_C3_VERIFIER_PROMPT_VERSION,
        )
    return MonitoringMappingCohortContract(
        cohort=cleaned,
        provider=MONITORING_C3_MAPPING_PROVIDER,
        model=MONITORING_C3_MAPPING_MODEL,
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        business_key_prefix=MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
        prompt_version="",
    )


__all__ = [
    "MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION",
    "MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION",
    "MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY",
    "MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK",
    "MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY",
    "MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED",
    "MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER",
    "MONITORING_C3_ALTERNATE_MODEL",
    "MONITORING_C3_ALTERNATE_PROVIDER",
    "MONITORING_C3_MAPPING_MODEL",
    "MONITORING_C3_MAPPING_PROFILE_ID",
    "MONITORING_C3_MAPPING_PROVIDER",
    "MONITORING_C3_VERIFIER_MODEL",
    "MONITORING_C3_VERIFIER_PROFILE_ID",
    "MONITORING_C3_VERIFIER_PROVIDER",
    "MONITORING_C3_VERIFIER_PROMPT_VERSION",
    "MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX",
    "MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX",
    "MONITORING_C3_CMS_PRIMARY_MODEL",
    "MONITORING_C3_CMS_PRIMARY_PROFILE_ID",
    "MONITORING_C3_CMS_PRIMARY_PROVIDER",
    "MONITORING_C3_LOCAL_FALLBACK_MODEL",
    "MONITORING_C3_LOCAL_FALLBACK_PROVIDER",
    "MONITORING_C3_SUPPORTED_RUNTIMES",
    "MONITORING_MAPPING_COHORTS",
    "MONITORING_MAPPING_COHORT_PRIMARY",
    "MONITORING_MAPPING_COHORT_VERIFIER",
    "MonitoringC3MappingGateContract",
    "MonitoringMappingCohortContract",
    "ZHIPU_CODING_PLAN_API_KEY_ENV",
    "ZHIPU_CODING_PLAN_API_KEY_ENV_ALIASES",
    "ZHIPU_CODING_PLAN_BASE_URL",
    "ZHIPU_CODING_PLAN_PRESET_ID",
    "monitoring_mapping_cohort_contract",
    "monitoring_mapping_cohort_dual_model_eligible",
    "monitoring_mapping_execution_route",
    "monitoring_mapping_runtime_matches",
    "normalize_monitoring_mapping_model",
]
