"""C3 listing field-mapping model gate for zhipu-coding-plan direct routing.

The gate is the single source of truth for the provider/model identity that
AdmissionMappingPipeline accepts before submitting candidate jobs. Product
registry presets and role profiles must stay aligned with these constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION = "mm-c3-mapping-gate-v1"
MONITORING_C3_MAPPING_PROVIDER = "zhipu-coding-plan"
MONITORING_C3_MAPPING_MODEL = "glm-5.3-flash"
MONITORING_C3_MAPPING_PROFILE_ID = "independent_ai__zhipu_coding_plan_glm_flash"
ZHIPU_CODING_PLAN_PRESET_ID = "zhipu_coding_plan"
ZHIPU_CODING_PLAN_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"
ZHIPU_CODING_PLAN_API_KEY_ENV = "ZAI_CODING_CN_API_KEY"
ZHIPU_CODING_PLAN_API_KEY_ENV_ALIASES = (
    ZHIPU_CODING_PLAN_API_KEY_ENV,
    "ZHIPU_CODING_PLAN_API_KEY",
)


def normalize_monitoring_mapping_model(model: str) -> str:
    """Return the canonical configured model id, preserving unknown values."""

    cleaned = str(model or "").strip()
    if cleaned.casefold() == MONITORING_C3_MAPPING_MODEL.casefold():
        return MONITORING_C3_MAPPING_MODEL
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
    return (
        available
        and provider == required_provider
        and model.casefold() == required_model.casefold()
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
            preset_id=ZHIPU_CODING_PLAN_PRESET_ID,
            base_url=ZHIPU_CODING_PLAN_BASE_URL,
            api_key_env=ZHIPU_CODING_PLAN_API_KEY_ENV,
        )


__all__ = [
    "MONITORING_C3_MAPPING_GATE_SCHEMA_VERSION",
    "MONITORING_C3_MAPPING_MODEL",
    "MONITORING_C3_MAPPING_PROFILE_ID",
    "MONITORING_C3_MAPPING_PROVIDER",
    "MonitoringC3MappingGateContract",
    "ZHIPU_CODING_PLAN_API_KEY_ENV",
    "ZHIPU_CODING_PLAN_API_KEY_ENV_ALIASES",
    "ZHIPU_CODING_PLAN_BASE_URL",
    "ZHIPU_CODING_PLAN_PRESET_ID",
    "monitoring_mapping_runtime_matches",
    "normalize_monitoring_mapping_model",
]
