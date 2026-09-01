#!/usr/bin/env python3
"""Generate the renderer-neutral R5-S6 navigation contract package.

This file is contract tooling only.  It reads the accepted R5/S5 bytes, emits
S6 JSON and review/context views, and never imports a product, runtime,
browser, service, real project, or model.

Binding graph: exact_contract is semantic requirements and validation paths;
quota references exact_contract.contract_content_hash; manifest owns raw-byte
hashes for present artifacts and excludes its own raw hash.  Mutable worker-02
links are reported as pending until their rebind is observed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s6-navigation-density-accessibility-contract-v0.1"
SCHEMA_VERSION = "2026-08-26.1"
STAGE = "R5-S6"

ARTIFACT_DIR = Path("artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1")
CONTEXT_REL = Path("context/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_20260826_context.md")
REVIEW_REL = Path("reviews/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_20260826.md")
SCHEMA_REL = ARTIFACT_DIR / "navigation_schema.json"
ENCODING_REL = ARTIFACT_DIR / "audience_encoding_registry.json"
PERFORMANCE_REL = ARTIFACT_DIR / "performance_corpus_registry.json"
EXACT_REL = ARTIFACT_DIR / "exact_contract.json"
MANIFEST_REL = ARTIFACT_DIR / "manifest.json"
GENERATOR_REL = Path("scripts/generate_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py")
CHALLENGE_REL = ARTIFACT_DIR / "challenge_registry.json"
QUOTA_REL = ARTIFACT_DIR / "quota_ledger.json"
VERIFIER_REL = Path("scripts/verify_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py")
TEST_REL = Path("scripts/test_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py")

OWNED_REL = (
    CONTEXT_REL,
    REVIEW_REL,
    SCHEMA_REL,
    ENCODING_REL,
    PERFORMANCE_REL,
    EXACT_REL,
    MANIFEST_REL,
    GENERATOR_REL,
)

UPSTREAM_RAW_PINS = {
    "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md":
        "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6",
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json":
        "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "context/medical_monitoring_r5_contract_acceptance_record_20260818.md":
        "c086a19772be498b560a7fea6b5eab5b6e897283b1cd87ff3f139b823e79e6f2",
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md":
        "3d5410c85d3ab2426bd599c228f5d58b910ec719ea9970f4bb51bed0a6ae6327",
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_acceptance_record_20260826.md":
        "fed3ae96d95aa43bb6eda3fe2df175371c5fe3d7a4654818316294eec4b82f52",
    "context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md":
        "6f623c4b285cbf003f06e3378deb69583b14ceb1ef0a30b404518c7588e995d1",
    "context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_pause_20260826.md":
        "729457382123e368b9f38c955f5668d3b43925f184f0a400e4839a879e39c899",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json":
        "5b674b16159295052afb56a0736dc8fc87a6070a0ea5524a2b8bfc7850d29cac",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json":
        "e5143edda759685fccedd9c696429454f2e1924175171d89f7c3948e5d61f00c",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json":
        "868815c74b4fb4ee33eb738d9de0f20c3148e9339f56a18745b0afccb32a34d8",
}

PARENT_EXACT_REL = Path("artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
S5_EXACT_REL = Path("artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json")
S5_MANIFEST_REL = Path("artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json")
STAGE_REL = Path("reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md")

CONTRACT_FREEZE_VALIDATION_PATHS = (
    CHALLENGE_REL,
    QUOTA_REL,
    VERIFIER_REL,
    TEST_REL,
)

S6_RUNTIME_ALLOWLIST = (
    Path("poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_contracts.py"),
    Path("poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_navigation.py"),
    Path("poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_accessibility.py"),
    Path("poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_validator.py"),
    Path("poc/medical_monitoring_ai_native_r5/tests/s6_runtime_fixtures.py"),
    Path("poc/medical_monitoring_ai_native_r5/tests/test_s6_contracts.py"),
    Path("poc/medical_monitoring_ai_native_r5/tests/test_s6_navigation.py"),
    Path("poc/medical_monitoring_ai_native_r5/tests/test_s6_validator.py"),
    Path("poc/medical_monitoring_ai_native_r5/tests/challenges/test_s6_runtime_challenges.py"),
    Path("poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s6_navigation_readonly_sha256.json"),
)

DOMAINS = (
    {"domain": "ae", "short_label_zh": "AE", "event_shape": "rounded_rect", "line_style": "solid"},
    {"domain": "mh", "short_label_zh": "MH", "event_shape": "bookmark", "line_style": "dot_dash"},
    {"domain": "cm", "short_label_zh": "合并用药", "event_shape": "capsule", "line_style": "solid"},
    {"domain": "ip", "short_label_zh": "试验药", "event_shape": "hexagon", "line_style": "step"},
    {"domain": "lab_exam", "short_label_zh": "检验/检查", "event_shape": "square", "line_style": "trend"},
    {"domain": "hospital_procedure", "short_label_zh": "住院/操作", "event_shape": "doorframe", "line_style": "solid"},
    {"domain": "symptom_efficacy", "short_label_zh": "症状/疗效", "event_shape": "circle", "line_style": "trend"},
    {"domain": "protocol_compliance", "short_label_zh": "方案符合", "event_shape": "single_flag", "line_style": "bracket"},
)

DOMAIN_SUBTYPES = {
    "ae": ["ae"],
    "mh": ["mh"],
    "cm": ["concomitant_medication"],
    "ip": ["ip_dose", "ip_pause", "ip_resume"],
    "lab_exam": ["lab", "exam"],
    "hospital_procedure": ["hospitalization", "procedure"],
    "symptom_efficacy": ["symptom", "efficacy", "scale", "outcome", "trend"],
    "protocol_compliance": ["protocol_deviation"],
}

SEVERITIES = (
    {"severity": "critical", "label_zh": "紧急"},
    {"severity": "high", "label_zh": "高"},
    {"severity": "medium", "label_zh": "中"},
    {"severity": "low", "label_zh": "低"},
)

FORBIDDEN_TERMS = ["已记录事项", "正式事实", "候选信号", "通用风险点", "只读xx", "Checklist", "待行动", "未读"]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(rel: Path) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def field(type_name: str, *, cardinality: str = "one", nullable: bool = False) -> dict[str, Any]:
    return {"type": type_name, "cardinality": cardinality, "nullable": nullable}


def validate_upstream() -> dict[str, str]:
    observed: dict[str, str] = {}
    for rel, expected in UPSTREAM_RAW_PINS.items():
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"MISSING_UPSTREAM {rel}")
        observed[rel] = raw_sha(path)
        if observed[rel] != expected:
            raise SystemExit(f"UPSTREAM_PIN_DRIFT {rel} {observed[rel]} != {expected}")
    return observed


def validate_contract_freeze_artifacts() -> dict[str, str]:
    observed: dict[str, str] = {}
    expected_paths = {path.as_posix() for path in CONTRACT_FREEZE_VALIDATION_PATHS}
    if len(expected_paths) != len(CONTRACT_FREEZE_VALIDATION_PATHS):
        raise SystemExit("CONTRACT_FREEZE_PATH_SET_DRIFT")
    for path in CONTRACT_FREEZE_VALIDATION_PATHS:
        rel = path.as_posix()
        path = ROOT / path
        if not path.exists():
            raise SystemExit(f"MISSING_CONTRACT_FREEZE_ARTIFACT {rel}")
        observed[rel] = raw_sha(path)
    return dict(sorted(observed.items()))


def validate_future_runtime_absent() -> None:
    for rel in S6_RUNTIME_ALLOWLIST:
        if (ROOT / rel).exists():
            raise SystemExit(f"FUTURE_RUNTIME_PATH_PRESENT {rel.as_posix()}")


def semantic_link_status(exact: dict[str, Any], exact_raw_sha256: str) -> dict[str, Any]:
    """Classify mutable worker-02 links without making them exact-contract inputs."""
    expected_content_hash = exact["contract_content_hash"]
    observed_quota_content_hash = load_json(QUOTA_REL).get("contract_content_hash")
    verifier_text = (ROOT / VERIFIER_REL).read_text(encoding="utf-8")
    reasons: list[str] = []
    if observed_quota_content_hash != expected_content_hash:
        reasons.append("quota_contract_content_hash_stale")
    if exact_raw_sha256 not in verifier_text:
        reasons.append("verifier_exact_raw_sha256_stale")
    return {
        "state": "ready" if not reasons else "pending_worker_02_rebind",
        "exact_contract_content_hash": expected_content_hash,
        "exact_contract_raw_sha256": exact_raw_sha256,
        "quota_contract_content_hash": observed_quota_content_hash,
        "verifier_contains_current_exact_raw_sha256": exact_raw_sha256 in verifier_text,
        "pending_reasons": reasons,
    }


def build_enums() -> dict[str, list[str]]:
    return {
        "target_kind": ["subject_workspace", "risk_inspector", "source_locator"],
        "view": ["journey", "profile", "timeline"],
        "axis_mode": ["calendar", "study_day"],
        "cutoff_state": ["present", "absent"],
        "fallback_policy": ["none"],
        "date_state": ["exact", "partial", "conflicted", "missing"],
        "severity": ["critical", "high", "medium", "low"],
        "domain": [item["domain"] for item in DOMAINS],
        "journey_subtype": sorted({subtype for values in DOMAIN_SUBTYPES.values() for subtype in values}),
        "change_kind": ["initial_current", "new", "upgraded", "continued", "downgraded", "resolved", "reopened", "superseded", "not_evaluable", "not_comparable"],
        "sort_key": ["priority", "change", "evidence", "site_stable"],
        "sort_direction": ["asc", "desc"],
        "event_shape": ["rounded_rect", "bookmark", "capsule", "hexagon", "square", "doorframe", "circle", "triangle", "single_flag"],
        "line_style": ["solid", "dashed", "dot_dash", "step", "trend", "bracket"],
        "density_mode": ["standard", "high"],
        "semantic_zoom_level": ["overview", "detail", "evidence"],
        "aggregation_policy": ["low_risk_by_domain_window", "none", "none_source_expanded"],
        "risk_visibility_policy": ["all_critical_high_medium", "all_projectable"],
        "source_locator_policy": ["risk_only", "event_and_risk", "all_projectable"],
        "keyboard_key": ["Tab", "Shift+Tab", "Enter", "Space", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "+", "-", "0"],
        "keyboard_action": [
            "focus_next_region", "focus_previous_region", "activate_focused_target", "toggle_focused_control",
            "close_ephemeral_surface", "move_previous", "move_next", "focus_first", "focus_last",
            "semantic_zoom_in", "semantic_zoom_out", "semantic_zoom_reset",
        ],
        "keyboard_scope": ["global", "risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"],
        "restoration_outcome": ["restored", "not_restored"],
        "performance_mode": ["cold", "warm"],
        "benchmark_statistic": ["p95_nearest_rank", "p05_nearest_rank"],
        "performance_result_state": ["unmeasured_contract_only", "measured_pass", "measured_fail"],
    }


def build_objects() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "S6DeepLinkIdentity": {
            "target_kind": field("enum:target_kind"),
            "project_ref": field("str"), "run_ref": field("str"), "snapshot_ref": field("str"),
            "cutoff_state": field("enum:cutoff_state"), "cutoff_ref": field("str", nullable=True),
            "site_ref": field("str", nullable=True), "subject_ref": field("str"), "risk_ref": field("str"),
            "spine_ref": field("str"), "view": field("enum:view"), "axis_mode": field("enum:axis_mode"),
            "window_start": field("date", nullable=True), "window_end": field("date", nullable=True),
            "visit_ref": field("str", nullable=True), "event_ref": field("str", nullable=True),
            "risk_anchor_ref": field("str", nullable=True), "source_locator_ref": field("str", nullable=True),
            "target_projection_content_hash": field("sha256"), "return_context_key": field("str"),
            "fallback_policy": field("enum:fallback_policy"),
        },
        "S6FilterState": {
            "change_kind": field("enum:change_kind", cardinality="many"),
            "domain": field("enum:domain", cardinality="many"),
            "severity": field("enum:severity", cardinality="many"),
            "site_refs": field("str", cardinality="many"), "include_low": field("bool"),
        },
        "S6SortState": {"key": field("enum:sort_key"), "direction": field("enum:sort_direction")},
        "S6PageState": {"page_index": field("int"), "page_size": field("int")},
        "S6SelectionAnchor": {
            "selected_event_ref": field("str", nullable=True), "selected_risk_ref": field("str", nullable=True),
            "selected_visit_ref": field("str", nullable=True), "risk_anchor_ref": field("str", nullable=True),
            "source_locator_ref": field("str", nullable=True),
        },
        "S6CanonicalReturnState": {
            "deep_link_identity": field("S6DeepLinkIdentity"), "filter_state": field("S6FilterState"),
            "sort_state": field("S6SortState"), "page_state": field("S6PageState"),
            "selection_anchor": field("S6SelectionAnchor"), "semantic_zoom_state": field("S6SemanticZoomState"),
            "axis_mode": field("enum:axis_mode"),
            "window_start": field("date", nullable=True), "window_end": field("date", nullable=True),
            "canonical_state_hash": field("sha256"),
        },
        "S6EphemeralReturnState": {
            "scroll_refs": field("str", cardinality="many"), "inspector_width": field("int"),
            "inspector_expanded": field("bool"), "temporary_expansion_refs": field("str", cardinality="many"),
            "focus_ref": field("str", nullable=True),
        },
        "S6ReturnContext": {
            "return_context_key": field("str"), "canonical": field("S6CanonicalReturnState"),
            "ephemeral": field("S6EphemeralReturnState"), "restoration_outcome": field("enum:restoration_outcome"),
        },
        "S6SemanticZoomState": {
            "density_mode": field("enum:density_mode"), "semantic_zoom_level": field("enum:semantic_zoom_level"),
            "aggregation_policy": field("enum:aggregation_policy"),
            "risk_visibility_policy": field("enum:risk_visibility_policy"),
            "source_locator_policy": field("enum:source_locator_policy"),
        },
        "S6KeyboardBinding": {
            "key": field("enum:keyboard_key"), "action": field("enum:keyboard_action"),
            "scope": field("enum:keyboard_scope"), "prevent_default": field("bool"),
            "medical_state_mutation": field("bool"),
        },
        "S6KeyboardContract": {
            "region_order": field("enum:keyboard_scope", cardinality="many"),
            "bindings": field("S6KeyboardBinding", cardinality="many"),
            "focus_policy": field("str"), "selection_policy": field("str"),
        },
        "S6DomainEncodingItem": {
            "domain": field("enum:domain"), "short_label_zh": field("str"),
            "event_shape": field("enum:event_shape"), "line_style": field("enum:line_style"),
            "subtypes": field("enum:journey_subtype", cardinality="many"),
        },
        "S6SeverityEncodingItem": {"severity": field("enum:severity"), "label_zh": field("str")},
        "S6RiskOverlayEncoding": {
            "shape": field("str"), "outer_ring": field("bool"), "text_pattern": field("str"),
            "colour_only": field("bool"),
        },
        "S6AudienceEncodingRegistry": {
            "domain_items": field("S6DomainEncodingItem", cardinality="many"),
            "severity_items": field("S6SeverityEncodingItem", cardinality="many"),
            "risk_overlay": field("S6RiskOverlayEncoding"),
            "event_forbidden_shapes": field("str", cardinality="many"),
            "forbidden_terms": field("str", cardinality="many"),
            "content_hash": field("sha256"),
        },
        "S6PerformanceCorpusIdentity": {
            "corpus_id": field("str"), "schema_version": field("str"),
            "event_count": field("int"), "indicator_count": field("int"), "risk_anchor_count": field("int"),
            "record_order": field("str", cardinality="many"), "content_hash": field("sha256"),
        },
        "S6PerformanceProfile": {
            "corpus": field("S6PerformanceCorpusIdentity"), "modes": field("enum:performance_mode", cardinality="many"),
            "samples_per_mode": field("int"), "latency_statistic": field("enum:benchmark_statistic"),
            "fps_statistic": field("enum:benchmark_statistic"), "thresholds": field("S6PerformanceThresholds"),
            "viewport": field("int", cardinality="many"), "marks": field("S6PerformanceMarks"),
            "result_state": field("enum:performance_result_state"),
        },
        "S6PerformanceThresholds": {
            "cold_interactive_ms_p95": field("int"), "warm_interactive_ms_p95": field("int"),
            "brush_zoom_select_ms_p95": field("int"), "pan_fps_p05": field("int"),
        },
        "S6PerformanceMarks": {
            "interactive_start": field("str"), "interactive_end": field("str"),
            "response_start": field("str"), "response_end": field("str"),
        },
    }


def build_schema(enums: dict[str, list[str]], objects: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    schema = {
        "schema": "medical-monitoring-r5-s6-navigation-density-accessibility-schema-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "renderer_neutral": True,
        "exact_keys_recursive": True,
        "enums": enums,
        "objects": objects,
        "canonical_state_fields": [
            "deep_link_identity", "filter_state", "sort_state", "page_state", "selection_anchor",
            "semantic_zoom_state", "axis_mode", "window_start", "window_end",
        ],
        "ephemeral_state_fields": ["scroll_refs", "inspector_width", "inspector_expanded", "temporary_expansion_refs", "focus_ref"],
        "canonical_hash_recipe": "sha256(canonical_json(all S6CanonicalReturnState fields except canonical_state_hash))",
        "corpus_hash_recipe": "sha256(canonical_json(all S6PerformanceCorpusIdentity fields except content_hash))",
        "content_hash": None,
    }
    schema["content_hash"] = digest({key: value for key, value in schema.items() if key != "content_hash"})
    return schema


def build_encoding_registry() -> dict[str, Any]:
    registry = {
        "schema": "medical-monitoring-r5-s6-audience-encoding-registry-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "domain_items": [
            {**item, "subtypes": DOMAIN_SUBTYPES[item["domain"]]} for item in DOMAINS
        ],
        "severity_items": list(SEVERITIES),
        "risk_overlay": {
            "shape": "double_chevron_badge",
            "outer_ring": True,
            "text_pattern": "{domain_short_label}·{severity_zh}",
            "colour_only": False,
        },
        "event_forbidden_shapes": ["double_chevron_badge"],
        "forbidden_terms": list(FORBIDDEN_TERMS),
        "severity_rules": {
            "critical_authority_required": True,
            "high_must_not_promote_to_critical": True,
            "legacy_mapping": {"severe": "high", "moderate": "medium", "mild": "low"},
            "unmapped_legacy_value": "fail_closed",
        },
        "domain_rules": {
            "exact_domain_count": 8,
            "unknown_domain": "fail_closed_to_domain_confirmation_surface",
            "other_domain": "forbidden",
            "unlisted_domain_subtype_pair": "fail_closed",
            "symptom_efficacy_is_one_domain": True,
        },
        "content_hash": None,
    }
    registry["content_hash"] = digest({key: value for key, value in registry.items() if key != "content_hash"})
    return registry


def build_performance_registry() -> dict[str, Any]:
    corpus = {
        "schema": "medical-monitoring-r5-s6-offline-performance-corpus-v0.1",
        "corpus_id": "r5-s6-offline-density-performance-corpus-v0.1",
        "schema_version": SCHEMA_VERSION,
        "event_count": 1000,
        "indicator_count": 40,
        "risk_anchor_count": 300,
        "record_order": ["event", "indicator", "risk_anchor"],
        "identity_recipe": {
            "record_key_fields": ["record_kind", "ordinal"],
            "ordinal_base": 0,
            "content_fields": ["record_kind", "ordinal", "domain", "source_locator_ref"],
            "ordinal_is_not_medical_authority": True,
            "fixture_name_and_row_count_are_not_authority": True,
        },
        "content_hash": None,
    }
    corpus["content_hash"] = digest({key: value for key, value in corpus.items() if key != "content_hash"})
    profile = {
        "schema": "medical-monitoring-r5-s6-performance-profile-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "corpus": corpus,
        "modes": ["cold", "warm"],
        "samples_per_mode": 7,
        "latency_statistic": "p95_nearest_rank",
        "fps_statistic": "p05_nearest_rank",
        "thresholds": {
            "cold_interactive_ms_p95": 2500,
            "warm_interactive_ms_p95": 1500,
            "brush_zoom_select_ms_p95": 100,
            "pan_fps_p05": 30,
        },
        "viewport": [1440, 900],
        "marks": {
            "interactive_start": "navigationStart",
            "interactive_end": "risk-list, center-map, inspector and journey controls enabled",
            "response_start": "trusted pointer or keyboard event",
            "response_end": "next painted frame with updated canonical selection",
        },
        "required_workloads": [
            "cold_interactive", "warm_interactive", "brush_response", "zoom_response",
            "selection_response", "pan_fps", "high_risk_visibility", "layout_overflow",
        ],
        "result_state": "unmeasured_contract_only",
        "offline_boundary": {
            "synthetic_only": True,
            "real_project": False,
            "real_model": False,
            "starts_8911": False,
            "browser_acceptance": "S7_only",
            "result_state_at_contract_stage": "unmeasured_contract_only",
        },
        "content_hash": None,
    }
    profile["content_hash"] = digest({key: value for key, value in profile.items() if key != "content_hash"})
    return profile


def build_exact(
    schema: dict[str, Any],
    encoding: dict[str, Any],
    performance: dict[str, Any],
) -> dict[str, Any]:
    parent = load_json(PARENT_EXACT_REL)
    s5 = load_json(S5_EXACT_REL)
    exact = {
        "schema": "medical-monitoring-r5-s6-navigation-density-accessibility-exact-contract-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "stage": STAGE,
        "renderer_neutral": True,
        "contract_only": True,
        "parent_contract": {
            "contract_id": parent.get("schema"),
            "content_sha256": parent.get("contract_content_hash"),
            "accepted_stage_ref": STAGE_REL.as_posix(),
        },
        "s5_contract": {
            "contract_id": s5.get("contract_id"),
            "content_sha256": s5.get("contract_content_hash"),
            "runtime_acceptance_ref": "context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md",
        },
        "schema_ref": SCHEMA_REL.as_posix(),
        "audience_encoding_ref": ENCODING_REL.as_posix(),
        "performance_corpus_ref": PERFORMANCE_REL.as_posix(),
        "enums": schema["enums"],
        "objects": schema["objects"],
        "vocabulary": {
            "domain_order": [item["domain"] for item in DOMAINS],
            "severity_order": [item["severity"] for item in SEVERITIES],
            "severity_zh": {item["severity"]: item["label_zh"] for item in SEVERITIES},
            "forbidden_terms": list(FORBIDDEN_TERMS),
            "fallback_policy": "none",
        },
        "deep_link_contract": {
            "identity_fields": [
                "target_kind", "project_ref", "run_ref", "snapshot_ref", "cutoff_state", "cutoff_ref",
                "site_ref", "subject_ref", "risk_ref", "spine_ref", "view", "axis_mode", "window_start",
                "window_end", "visit_ref", "event_ref", "risk_anchor_ref", "source_locator_ref",
                "target_projection_content_hash", "return_context_key", "fallback_policy",
            ],
            "exact_target_rule": "every non-null identity field equals the target projection; target content hash and receipt identity are checked before emission",
            "cutoff_absent_rule": "cutoff_state=absent requires cutoff_ref=null and preserves absence; no empty string or inferred date",
            "member_rule": "site, subject, risk, spine, visit, event, risk anchor and source locator must be projectable members of the same verified target",
            "failure_outcome": "not_emitted",
            "failure_codes": [
                "DEEP_LINK_IDENTITY_MISMATCH", "DEEP_LINK_TARGET_NOT_PROJECTABLE", "DEEP_LINK_ANCHOR_NOT_MEMBER",
                "DEEP_LINK_ARTIFACT_MISSING", "NEAREST_FALLBACK_FORBIDDEN",
            ],
            "fallback_policy": "none",
        },
        "return_context_contract": {
            "canonical_fields": schema["canonical_state_fields"],
            "ephemeral_fields": schema["ephemeral_state_fields"],
            "canonical_hash_recipe": schema["canonical_hash_recipe"],
            "restore_rule": "canonical fields restore exactly after identity and membership validation; declared ephemeral fields restore exactly when valid, otherwise the declared empty/default value is used",
            "url_byte_identity_required": False,
            "canonical_equivalence_required": True,
            "medical_state_mutation": False,
            "failure_outcome": "not_restored",
            "failure_codes": [
                "RETURN_CONTEXT_KEY_MISMATCH", "CANONICAL_STATE_HASH_MISMATCH", "RETURN_TARGET_NOT_PROJECTABLE",
                "RETURN_ANCHOR_NOT_MEMBER", "RETURN_CONTEXT_ARTIFACT_MISSING", "NEAREST_FALLBACK_FORBIDDEN",
            ],
        },
        "density_and_zoom_contract": {
            "desktop_min_viewport": [1440, 900],
            "density_modes": {
                "standard": "preserve all contract content with normal spacing",
                "high": "reduce redundant spacing only; never hide, relabel or demote a required risk",
            },
            "semantic_zoom_levels": {
                "overview": {
                    "aggregation_policy": "low_risk_by_domain_window",
                    "risk_visibility_policy": "all_critical_high_medium",
                    "source_locator_policy": "risk_only",
                    "content_omission_policy": "low_risk_only",
                },
                "detail": {
                    "aggregation_policy": "none",
                    "risk_visibility_policy": "all_critical_high_medium",
                    "source_locator_policy": "event_and_risk",
                    "content_omission_policy": "none",
                },
                "evidence": {
                    "aggregation_policy": "none_source_expanded",
                    "risk_visibility_policy": "all_projectable",
                    "source_locator_policy": "all_projectable",
                    "content_omission_policy": "none",
                },
            },
            "invariants": [
                "all critical/high/medium risk anchors remain individually represented at every semantic zoom level",
                "overview aggregation is limited to low-risk ordinary events within one domain and time window",
                "detail and evidence do not aggregate events or risk anchors",
                "semantic zoom changes representation, not identity, membership, authority or canonical return state",
                "density changes spacing only and cannot be used as an omission or fallback mechanism",
            ],
        },
        "keyboard_contract": {
            "region_order": ["risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"],
            "bindings": [
                {"key": "Tab", "action": "focus_next_region", "scope": "global", "prevent_default": False, "medical_state_mutation": False},
                {"key": "Shift+Tab", "action": "focus_previous_region", "scope": "global", "prevent_default": False, "medical_state_mutation": False},
                {"key": "Enter", "action": "activate_focused_target", "scope": "global", "prevent_default": True, "medical_state_mutation": False},
                {"key": "Space", "action": "toggle_focused_control", "scope": "global", "prevent_default": True, "medical_state_mutation": False},
                {"key": "Escape", "action": "close_ephemeral_surface", "scope": "global", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowUp", "action": "move_previous", "scope": "risk_list", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowDown", "action": "move_next", "scope": "risk_list", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowUp", "action": "move_previous", "scope": "center_map", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowDown", "action": "move_next", "scope": "center_map", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowLeft", "action": "move_previous", "scope": "temporal_spine", "prevent_default": True, "medical_state_mutation": False},
                {"key": "ArrowRight", "action": "move_next", "scope": "temporal_spine", "prevent_default": True, "medical_state_mutation": False},
                {"key": "Home", "action": "focus_first", "scope": "workspace", "prevent_default": True, "medical_state_mutation": False},
                {"key": "End", "action": "focus_last", "scope": "workspace", "prevent_default": True, "medical_state_mutation": False},
                {"key": "+", "action": "semantic_zoom_in", "scope": "temporal_spine", "prevent_default": True, "medical_state_mutation": False},
                {"key": "-", "action": "semantic_zoom_out", "scope": "temporal_spine", "prevent_default": True, "medical_state_mutation": False},
                {"key": "0", "action": "semantic_zoom_reset", "scope": "temporal_spine", "prevent_default": True, "medical_state_mutation": False},
            ],
            "focus_policy": "one visible roving focus target per region; Tab crosses regions in region_order; hidden or non-projectable targets are not focusable",
            "selection_policy": "activation selects only a verified projectable target and preserves canonical identity; no key creates, edits, closes or regrades medical state",
        },
        "non_colour_encoding_contract": {
            "registry_content_hash": encoding["content_hash"],
            "event_then_risk_order": ["event", "domain", "severity"],
            "risk_overlay_is_not_event_shape": True,
            "colour_is_auxiliary_only": True,
            "domain_count": 8,
            "unknown_and_other_fail_closed": True,
        },
        "performance_contract": {
            "registry_content_hash": performance["content_hash"],
        "dataset": {"events": 1000, "indicators": 40, "risk_anchors": 300},
        "parent_compatibility": {"r5_v0_3_field": "metrics", "s6_field": "indicators", "value": 40},
            "offline_only": True,
            "browser_and_8911_acceptance": "S7_only",
            "result_state": "unmeasured_contract_only",
            "thresholds": performance["thresholds"],
            "sampling": {"samples_per_mode": 7, "latency": "p95_nearest_rank", "fps": "p05_nearest_rank"},
        },
        "invariants": [
            {"invariant_id": "deep_link_identity_exact", "error_code": "DEEP_LINK_IDENTITY_MISMATCH", "predicate": "all identity fields and target content hash match one projectable target; no nearest fallback"},
            {"invariant_id": "deep_link_no_nearest_fallback", "error_code": "NEAREST_FALLBACK_FORBIDDEN", "predicate": "mismatch, missing, hidden or non-projectable target emits no adjacent subject/site/risk/source"},
            {"invariant_id": "canonical_return_exact", "error_code": "CANONICAL_STATE_HASH_MISMATCH", "predicate": "canonical return fields restore with equal canonical state hash after membership validation"},
            {"invariant_id": "ephemeral_return_separate", "error_code": "EPHEMERAL_STATE_IN_CANONICAL_HASH", "predicate": "scroll, inspector presentation, temporary expansion and focus are not canonical identity"},
            {"invariant_id": "shared_s5_spine", "error_code": "SHARED_SPINE_MISMATCH", "predicate": "Journey/Profile/Timeline retain the accepted S5 spine, axis, window and selection references"},
            {"invariant_id": "density_no_omission", "error_code": "DENSITY_REQUIRED_RISK_HIDDEN", "predicate": "high density changes spacing only and preserves all critical/high/medium anchors"},
            {"invariant_id": "semantic_zoom_closed", "error_code": "SEMANTIC_ZOOM_POLICY_MISMATCH", "predicate": "only the three closed levels and their exact aggregation/source policies are legal"},
            {"invariant_id": "keyboard_non_mutating", "error_code": "KEYBOARD_MEDICAL_STATE_MUTATION", "predicate": "every binding has medical_state_mutation=false"},
            {"invariant_id": "non_colour_encoding_complete", "error_code": "NON_COLOUR_ENCODING_INCOMPLETE", "predicate": "eight domains exactly once; risk overlay double_chevron_badge is forbidden as an event shape; severity text is explicit"},
            {"invariant_id": "performance_corpus_exact", "error_code": "PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "predicate": "offline corpus has exactly 1000 events, 40 indicators and 300 risk anchors and uses the frozen content hash"},
            {"invariant_id": "performance_unmeasured_until_runtime", "error_code": "PERFORMANCE_RESULT_PREMATURE", "predicate": "contract generation cannot claim measured pass/fail or browser acceptance"},
            {"invariant_id": "protected_boundary", "error_code": "PROTECTED_BOUNDARY_DRIFT", "predicate": "8911 remains stopped and accepted R1-R5/medical-writing inputs remain immutable"},
        ],
        "contract_freeze_validation": {
            "artifact_paths": sorted(path.as_posix() for path in CONTRACT_FREEZE_VALIDATION_PATHS),
            "artifact_state": "present_contract_freeze_evidence",
            "raw_byte_binding": "manifest_only",
            "downstream_semantic_link": "worker_02_rebinds_quota_to_exact_contract_content_hash",
            "required_oracle_categories": [
                "deep_link_identity", "deep_link_no_nearest_fallback", "canonical_return_context",
                "density_semantic_zoom", "keyboard_non_colour_encoding", "performance_corpus_identity",
            ],
            "runtime_implementation": "not_authorized_by_this_contract_freeze",
            "browser_or_real_project": "not_authorized_by_this_contract_freeze",
        },
        "future_runtime_unlock": {
            "allowlist_ref": "manifest.future_runtime_allowlist",
            "allowlist_count": len(S6_RUNTIME_ALLOWLIST),
            "all_paths_absent_required": True,
            "runtime_kind": "synthetic_offline_renderer_neutral_only",
            "unlock_requires": "ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT",
            "does_not_unlock": [
                "frontend", "browser", "services", "real projects", "real models", "security", "medical-writing", "8911",
            ],
        },
        "boundaries": {
            "port_8911": "stopped_required",
            "medical_writing": "protected_and_untouched",
            "accepted_r1_r5_artifacts": "immutable_inputs",
            "no_frontend": True,
            "no_browser": True,
            "no_security": True,
            "no_real_project_or_model": True,
            "worker_self_acceptance": False,
            "acceptance_token_emitted": False,
        },
        "contract_content_hash": None,
    }
    exact["contract_content_hash"] = digest({key: value for key, value in exact.items() if key != "contract_content_hash"})
    return exact


def build_manifest(
    schema: dict[str, Any],
    encoding: dict[str, Any],
    performance: dict[str, Any],
    exact: dict[str, Any],
    upstream: dict[str, str],
    contract_freeze_raw_sha256: dict[str, str],
    semantic_links: dict[str, Any],
) -> dict[str, Any]:
    freeze_validation = [
        {
            "path": rel,
            "present": True,
            "role": "worker_02_final_contract_freeze_evidence",
            "binding": "raw_bytes_sha256",
            "raw_sha256": raw_sha,
            "runtime": False,
            "browser": False,
            "real_project_or_model": False,
            "starts_8911": False,
            "medical_writing": False,
        }
        for rel, raw_sha in sorted(contract_freeze_raw_sha256.items())
    ]
    future_runtime = [
        {
            "path": path.as_posix(),
            "create_only": True,
            "present": False,
            "kind": "synthetic_offline_renderer_neutral_runtime_or_test",
            "allowed_only_after": "ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT",
            "runtime": True,
            "browser": False,
            "real_project_or_model": False,
            "starts_8911": False,
            "medical_writing": False,
        }
        for path in S6_RUNTIME_ALLOWLIST
    ]
    manifest = {
        "schema": "medical-monitoring-r5-s6-navigation-density-accessibility-contract-manifest-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "candidate_unaccepted",
        "self_acceptance": False,
        "acceptance_token_emitted": False,
        "acceptance_token": "ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT",
        "exact_owned_paths": [path.as_posix() for path in OWNED_REL],
        "expected_complete_paths": [path.as_posix() for path in OWNED_REL],
        "contract_freeze_validation_artifacts": freeze_validation,
        "contract_freeze_validation_raw_sha256": dict(sorted(contract_freeze_raw_sha256.items())),
        "binding_graph": {
            "exact_contract": "semantic_requirements_and_validation_paths_only",
            "quota": "references_exact_contract.contract_content_hash",
            "manifest": "raw_bytes_for_exact_quota_challenge_verifier_tests_and_all_other_present_owned_artifacts",
            "manifest_self_raw_hash": "excluded",
        },
        "semantic_links": semantic_links,
        "future_runtime_allowlist": future_runtime,
        "input_raw_sha256": dict(sorted(upstream.items())),
        "input_content_identities": {
            PARENT_EXACT_REL.as_posix(): digest(load_json(PARENT_EXACT_REL)),
            S5_EXACT_REL.as_posix(): digest(load_json(S5_EXACT_REL)),
            S5_MANIFEST_REL.as_posix(): digest(load_json(S5_MANIFEST_REL)),
        },
        "contract_content_hash": exact["contract_content_hash"],
        "schema_content_hash": schema["content_hash"],
        "audience_encoding_content_hash": encoding["content_hash"],
        "performance_corpus_content_hash": performance["content_hash"],
        "performance_dataset": {"events": 1000, "indicators": 40, "risk_anchors": 300},
        "counts": {
            "owned_paths": len(OWNED_REL),
            "contract_freeze_validation_paths": len(freeze_validation),
            "future_runtime_allowlist_paths": len(future_runtime),
            "upstream_input_pins": len(upstream),
        },
        "protected_boundaries": {
            "port_8911": "stopped_required",
            "medical_writing_file_count": 542,
            "medical_writing_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
            "accepted_r1_r5_inputs_immutable": True,
            "production_paths_written": False,
        },
        "forbidden_scope": [
            "frontend", "browser", "security", "production", "medical-writing", "real projects", "real models", "8911 start",
        ],
        "unlock": {
            "contract_freeze_evidence": "present_and_raw_hash_bound",
            "future_runtime_allowlist_ref": "future_runtime_allowlist",
            "future_runtime_paths_must_be_absent": True,
            "future_runtime_kind": "synthetic_offline_renderer_neutral_only",
            "does_not_unlock": [
                "frontend", "browser", "services", "real projects", "real models", "security", "medical-writing", "8911",
            ],
        },
        "manifest_hash_recipe": "sha256(canonical_json(all manifest fields except manifest_content_hash))",
        "file_raw_sha256": None,
        "manifest_content_hash": None,
    }
    return manifest


def context_text(exact: dict[str, Any], manifest: dict[str, Any]) -> str:
    return f"""# R5-S6 Navigation / Density / Accessibility Contract v0.1 Context

日期：2026-08-26  
状态：`CANDIDATE_CONTRACT_ONLY`

## 范围

本批次只冻结 renderer-neutral 的 R5-S6 深链、canonical 返回上下文、桌面高密度与 semantic zoom、键盘和非颜色编码，以及离线性能 corpus 身份。它不实现 frontend、browser、service、security、真实项目或模型，也不启动 8911。

## 上游权威

- R5 stage：`{STAGE_REL.as_posix()}`；raw SHA 由 manifest 固定。
- 已接受 S5 contract/runtime：`{S5_EXACT_REL.as_posix()}`、其 acceptance record 与 runtime acceptance record；raw SHA 由 manifest 固定。
- S6 机器权威：`{EXACT_REL.as_posix()}`；schema、非颜色注册表和 performance corpus registry 分别由 `{SCHEMA_REL.as_posix()}`、`{ENCODING_REL.as_posix()}`、`{PERFORMANCE_REL.as_posix()}` 提供。

## 冻结语义

- 深链逐项绑定 project/run/snapshot/cutoff/site/subject/risk/spine、view、axis/window、visit/event/risk-anchor/source-locator、target projection content hash 和 return-context key；目标不一致、不可投影、缺失或 artifact 缺失时 `not_emitted`，fallback policy 只有 `none`。
- 返回上下文把 canonical identity/filter/sort/page/selection/axis/window 与 ephemeral scroll/Inspector/temporary expansion/focus 分开；canonical hash 只覆盖 canonical fields，恢复必须 canonical-equivalent，不要求 URL 字节相同。
- semantic zoom 只有 `overview/detail/evidence`；overview 只能聚合低风险普通事件，critical/high/medium risk anchor 在每一级保持单独可见；density 只改变间距，不得成为隐藏内容的机制。
- 键盘绑定为闭集，所有动作 `medical_state_mutation=false`。事件使用固定域形状/短标签/线型，风险使用独立 `double_chevron_badge + outer ring + explicit severity text`，颜色仅为辅助。
- 离线性能 corpus 精确为 1000 events / 40 indicators / 300 risk anchors，cold/warm 各 7 次，latency p95、pan FPS p05；当前结果状态必须保持 `unmeasured_contract_only`。
- exact contract 只冻结四个 worker-02 contract-freeze validation path、present-evidence role、oracle categories 和 scope restrictions；不含任何 raw hash。四个 present artifact 的 raw bytes 只在 manifest 绑定。
- acyclic binding graph：exact contract -> semantic requirements/paths；quota -> `exact_contract.contract_content_hash`；manifest -> raw hashes for exact/quota/challenge/verifier/tests and other present owned artifacts；manifest excludes its own raw hash。
- 当前 worker-02 semantic-link state：`{manifest['semantic_links']['state']}`；worker-02 rebind 完成前，verifier/quota checks 保持 pending，不得宣称最终 `CHECK_OK`。
- 后续 synthetic/offline S6 runtime 另用 `manifest.future_runtime_allowlist` 的十个 exact absent create-only 路径，接受前不得创建，且不解锁 frontend、browser、services、真实项目/模型、security、medical-writing 或 8911。

## 保护边界

manifest 固定 8911 stopped、medical-writing 542 文件及 inventory SHA、已接受 R1-R5 输入 immutable。当前 contract-freeze evidence 计数为 {manifest['counts']['contract_freeze_validation_paths']}，后续 runtime allowlist 计数为 {manifest['counts']['future_runtime_allowlist_paths']} 且全部 absent。

worker 不发出接受 token；最终 verifier、独立 review 和 Codex acceptance 另行完成。
"""


def review_text(
    exact: dict[str, Any],
    schema: dict[str, Any],
    encoding: dict[str, Any],
    performance: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    return f"""# R5-S6 Navigation / Density / Accessibility Contract v0.1 Review

## Review scope

这是 contract architect 的机器生成复核视图，不是接受记录，不发出 `ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT`。

## Mechanical contract facts

- contract：`{CONTRACT_ID}` / schema `{SCHEMA_VERSION}`。
- exact contract content SHA：`{exact['contract_content_hash']}`。
- schema objects：`{len(schema['objects'])}`；closed enums：`{len(schema['enums'])}`。
- exact deep-link identity fields：`{len(exact['deep_link_contract']['identity_fields'])}`；fallback policy：`none`；mismatch projection：`not_emitted`。
- canonical return fields：`{len(schema['canonical_state_fields'])}`；ephemeral fields：`{len(schema['ephemeral_state_fields'])}`；URL byte identity required：`False`。
- non-colour domain items：`{len(encoding['domain_items'])}`；risk overlay：`{encoding['risk_overlay']['shape']}`；forbidden event shapes：`{encoding['event_forbidden_shapes']}`。
- performance corpus：events `{performance['corpus']['event_count']}`, indicators `{performance['corpus']['indicator_count']}`, risk anchors `{performance['corpus']['risk_anchor_count']}`；cold/warm samples `{performance['samples_per_mode']}`；result state `{performance['offline_boundary']['result_state_at_contract_stage']}`。
- present contract-freeze validation artifacts：`{len(exact['contract_freeze_validation']['artifact_paths'])}`；exact contract raw-byte binding：`{exact['contract_freeze_validation']['raw_byte_binding']}`。
- acyclic graph：exact contract -> semantic requirements/paths；quota -> `exact_contract.contract_content_hash`；manifest -> raw hashes for exact/quota/challenge/verifier/tests and other present owned artifacts；manifest self raw hash excluded。
- worker-02 semantic-link state：`{manifest['semantic_links']['state']}`；pending reasons：`{manifest['semantic_links']['pending_reasons']}`。
- later synthetic/offline runtime allowlist：`{len(S6_RUNTIME_ALLOWLIST)}` exact absent create-only paths；no frontend/browser/services/real-project/model/security/medical-writing/8911 unlock。

## Independent checks still required

Verifier/test work must mutate only one frozen field per challenge and mechanically cover deep-link exact identity, no-nearest fallback, canonical return restoration, zoom/density omission rules, keyboard non-mutation, non-colour registry completeness, corpus identity and protected boundaries in normal/`-O`/`-OO` modes. No runtime/browser or real-project claim follows from this package.
"""


def build_all() -> tuple[dict[str, bytes], dict[str, Any]]:
    upstream = validate_upstream()
    contract_freeze_raw_sha256 = validate_contract_freeze_artifacts()
    validate_future_runtime_absent()
    schema = build_schema(build_enums(), build_objects())
    encoding = build_encoding_registry()
    performance = build_performance_registry()
    exact = build_exact(schema, encoding, performance)
    exact_bytes = pretty(exact)
    semantic_links = semantic_link_status(exact, hashlib.sha256(exact_bytes).hexdigest())
    manifest = build_manifest(schema, encoding, performance, exact, upstream, contract_freeze_raw_sha256, semantic_links)
    context = context_text(exact, manifest)
    review = review_text(exact, schema, encoding, performance, manifest)
    output = {
        CONTEXT_REL.as_posix(): context.encode("utf-8"),
        REVIEW_REL.as_posix(): review.encode("utf-8"),
        SCHEMA_REL.as_posix(): pretty(schema),
        ENCODING_REL.as_posix(): pretty(encoding),
        PERFORMANCE_REL.as_posix(): pretty(performance),
        EXACT_REL.as_posix(): exact_bytes,
    }
    hashes = {path: hashlib.sha256(data).hexdigest() for path, data in sorted(output.items())}
    hashes[GENERATOR_REL.as_posix()] = raw_sha(ROOT / GENERATOR_REL)
    hashes.update(contract_freeze_raw_sha256)
    manifest["file_raw_sha256"] = dict(sorted(hashes.items()))
    manifest["manifest_content_hash"] = digest({key: value for key, value in manifest.items() if key != "manifest_content_hash"})
    output[MANIFEST_REL.as_posix()] = pretty(manifest)
    return output, semantic_links


def write_or_check(expected: dict[str, bytes], semantic_links: dict[str, Any], check: bool) -> None:
    if check:
        problems = []
        for rel, data in expected.items():
            path = ROOT / rel
            if not path.exists():
                problems.append(f"missing:{rel}")
            elif path.read_bytes() != data:
                problems.append(f"drift:{rel}")
        if problems:
            raise SystemExit("CHECK_FAILED " + ",".join(problems))
        if semantic_links["state"] != "ready":
            print(
                "CHECK_PENDING "
                f"semantic_links={semantic_links['state']} "
                f"reasons={','.join(semantic_links['pending_reasons'])}"
            )
            raise SystemExit(2)
        print(f"CHECK_OK files={len(expected)} contract={CONTRACT_ID}")
        return
    for rel, data in expected.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(
        f"GENERATED files={len(expected)} contract={CONTRACT_ID} "
        f"semantic_links={semantic_links['state']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify owned bytes without writing")
    expected, semantic_links = build_all()
    write_or_check(expected, semantic_links, parser.parse_args().check)


if __name__ == "__main__":
    main()
