#!/usr/bin/env python3
"""Independent mechanical verifier for the frozen R5 v0.3 contract package."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import NoReturn, get_type_hints

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md"
DEFAULT_OUT = ROOT / "artifacts/medical_monitoring_r5_contract_v0_3"

PINNED_CONTRACT_SHA = "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6"
PINNED_GENERATOR_SHA = "250863b74b9e74696ccbc6c2a7e27e97f18a24e1a0467314b5aee5ec4e329e55"
PINNED_ARTIFACT_SHA = {
    "challenge_registry.json": "ef459f58ad6997a823c3ff57d51256cdf531b806d9033df636ab2912085b0887",
    "exact_contract.json": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "quota_ledger.json": "aeec1482b1c374d175a89660dd11cc312b6ba2612cf6c5a709379f2b05163b37",
    "manifest.json": "2298ff58a5f693e5d3deca7200920cfc12d54f59a9e04cae4aed41fd780363dd",
}

EXPECTED_CATEGORY_SLOTS = {
    "authority_identity": "project_ref run_ref snapshot_ref cutoff_ref projection_id projection_content_hash evaluation_content_identity audience_contract_id".split(),
    "authority_visibility": "visibility_decision_id visibility_decision_hash projectable_member hidden_member projectable_site hidden_site source_revision source_content_hash".split(),
    "change_comparability": "initial_current new upgraded continued downgraded resolved reopened not_comparable".split(),
    "change_cause_plane": "data denominator coverage knowledge rule mapping model method population visibility mode user_decision".split(),
    "count_layer_conservation": "individual_risk query clue center_pattern affected_subject event affected_site project_signal".split(),
    "numerator_denominator_rate": "numerator_duplicate denominator_zero denominator_unknown denominator_unclosed exclusion unit authoritative_value rate_state".split(),
    "coverage_cutoff_limits": "coverage_partial coverage_truncated coverage_unknown cutoff_before cutoff_after cutoff_spans small_sample short_followup".split(),
    "center_pattern_individual": "single_case pattern_member pattern_descendant d09_owner d10_owner absolute_count explicit_rate member_expand".split(),
    "center_stable_order": "input_permutation stable_site_id score_field rank_field".split(),
    "inspector_evidence_order": "support counterevidence baseline_recheck source_locator".split(),
    "ensemble_visibility": "zero_worker single_worker no_single_consensus unique_finding graded_conflict mutual_negation baseline_miss independent_adjudicator".split(),
    "deep_link_identity": "project run snapshot cutoff site subject risk spine".split(),
    "return_context": "filter sort page canonical_selection canonical_axis canonical_window scroll inspector_width".split(),
    "visit_semantics": "nominal_date actual_date unscheduled_visit between_visit_event phase_band first_dose last_dose cutoff_marker".split(),
    "axis_conversion": "calendar_default study_day_valid study_day_missing_anchor timezone_boundary partial_anchor phase_anchor cutoff_anchor conversion_replay".split(),
    "uncertain_dates": "partial_start partial_end conflicted_start conflicted_end missing_point missing_interval open_start open_end".split(),
    "eight_domain_adaptation": "ae_event ae_risk mh_event mh_risk cm_event ip_event lab_event hospital_event symptom_event efficacy_subtype protocol_event protocol_risk background_mapping non_drug_mapping unknown_other_forbidden not_applicable_vs_not_provided".split(),
    "encoding_registry": "event_risk_overlay unique_risk_shape severity_high_not_critical severity_critical_authority legacy_severe_mapping legacy_moderate_mapping legacy_mild_mapping severity_text_line".split(),
    "aemh_projection": "ae_risk ae_journey ae_profile ae_timeline mh_risk mh_journey mh_profile mh_timeline".split(),
    "aemh_match_history": "ae_exact mh_exact ambiguous rejected withdrawn reappeared append_only no_auto_close".split(),
    "source_one_hop": "listing_row listing_cell protocol_clause ib_clause support counterevidence unavailable_source nearest_fallback".split(),
    "audience_lexicon": "internal_fact_terms task_terms runtime_terms safety_pv_heading signal_misuse review_banner technical_identity translationese".split(),
    "interaction_no_mutation": "filter zoom select tab_switch open_source close_source back replay".split(),
    "deterministic_replay": "input_order member_order site_order source_order worker_order opaque_run_identity canonical_url serialization".split(),
    "high_density_performance": "cold_interactive warm_interactive brush_response zoom_response selection_response pan_fps high_risk_visibility layout_overflow".split(),
}
EXPECTED_ENUMS = {
    "severity": ["critical", "high", "medium", "low"], "severity_zh": ["紧急", "高", "中", "低"],
    "domain": ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"],
    "symptom_efficacy_subtype": ["symptom", "efficacy", "scale", "outcome", "trend"],
    "change_kind": ["initial_current", "new", "upgraded", "continued", "downgraded", "resolved", "reopened", "superseded", "not_evaluable", "not_comparable"],
    "change_cause": ["data", "knowledge", "rule", "mapping", "model", "method", "coverage", "denominator", "population", "visibility", "mode", "user_decision"],
    "denominator_state": ["closed_positive", "closed_zero", "unknown", "unclosed"],
    "coverage_state": ["complete", "partial", "truncated", "unknown", "not_applicable"],
    "axis_mode": ["calendar", "study_day"], "date_state": ["exact", "partial", "conflicted", "missing"],
    "match_state": ["exact", "ambiguous", "rejected"], "visibility_state": ["projectable", "hidden", "not_evaluable"],
    "numerator_kind": ["individual_risk", "center_pattern", "affected_subject", "event", "affected_site", "project_signal", "clue", "query"],
    "denominator_kind": ["enrolled_subjects", "treated_subjects", "safety_evaluable_subjects", "efficacy_evaluable_subjects", "subject_time", "exposure_time"],
    "rate_state": ["permitted", "qualified", "not_evaluable"], "measure_unit": ["subject", "event", "site", "day", "subject_day", "percent"],
    "workspace_view": ["journey", "trend", "events"], "visit_kind": ["nominal", "actual", "unscheduled"],
    "applicability_state": ["applicable", "not_applicable", "not_provided", "unknown"],
    "journey_subtype": ["ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume", "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy", "scale", "outcome", "trend", "protocol_deviation"],
    "pending_item_kind": ["event", "risk", "visit"], "sort_key": ["priority", "change", "evidence", "site_stable"], "sort_direction": ["asc", "desc"],
    "projection_kind": ["d09_audience", "d10_project", "ensemble", "subject_temporal", "aemh_history"],
    "event_shape": ["rounded_rect", "bookmark", "capsule", "hexagon", "square", "doorframe", "circle", "triangle", "single_flag"],
    "line_style": ["solid", "dashed", "dot_dash", "step", "trend", "bracket"], "legacy_treatment_kind": ["background_treatment", "non_drug_treatment"],
    "legacy_mapping_state": ["mapped", "unmapped_fail_closed"],
}
EXPECTED_OBJECTS = {"SourceRevisionContentPair", "R5FilterState", "R5SortState", "R5PageState", "R5ScrollState", "R5DomainEncodingItem", "R5SeverityLexiconItem", "R5LegacyTreatmentMappingItem", "R5LexiconItem", "R5AuthorityReceipt", "R5ProjectionInstance", "R5ChangeBand", "R5CurrentRiskSet", "R5QuantitativeMeasure", "R5ProjectCockpitProjection", "R5CenterMapCell", "R5CenterMapProjection", "R5RiskInspectorProjection", "R5DeepLinkState", "R5ReturnContext", "R5SubjectWorkspaceState", "R5TemporalSpineProjection", "R5VisitNode", "R5JourneyTrack", "R5JourneyEvent", "R5RiskAnchor", "R5PendingDateItem", "R5AEMHMatchHistory", "R5AudienceEncodingRegistry", "R5AudienceLexicon"}
ROW_KEYS = {"case_id", "category", "precondition", "single_mutation", "expected_typed_outcome_or_error", "forbidden_audience_output", "stage_oracle_contract", "severity"}
ORACLE_KEYS = {"kind", "planned_stage", "rule_id", "test_locator", "expected_outcome", "expected_projection", "required_non_llm_anchor"}

EXPECTED_ACCEPT_RULES = {
    *(f"change_comparability.{x}" for x in EXPECTED_CATEGORY_SLOTS["change_comparability"]),
    "numerator_denominator_rate.denominator_zero", "numerator_denominator_rate.denominator_unclosed",
    "coverage_cutoff_limits.coverage_partial", "coverage_cutoff_limits.coverage_truncated",
    "coverage_cutoff_limits.small_sample", "coverage_cutoff_limits.short_followup",
    "center_stable_order.input_permutation", "center_stable_order.stable_site_id",
    "ensemble_visibility.zero_worker", "ensemble_visibility.single_worker", "ensemble_visibility.unique_finding",
    "ensemble_visibility.graded_conflict", "ensemble_visibility.mutual_negation", "ensemble_visibility.baseline_miss",
    *(f"return_context.{x}" for x in EXPECTED_CATEGORY_SLOTS["return_context"]),
    "axis_conversion.calendar_default", "axis_conversion.study_day_valid", "axis_conversion.conversion_replay",
    *(f"aemh_match_history.{x}" for x in EXPECTED_CATEGORY_SLOTS["aemh_match_history"] if x != "no_auto_close"),
    *(f"deterministic_replay.{x}" for x in EXPECTED_CATEGORY_SLOTS["deterministic_replay"]),
}

def fail(code: str, detail: str = "") -> NoReturn:
    raise SystemExit(f"{code}: {detail}" if detail else code)

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(v: object) -> bytes: return (json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
def load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))

def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        fail(code, detail)

def severity_for(category: str, slot: str) -> str:
    if (category, slot) in {
        ("authority_identity", "project_ref"), ("authority_visibility", "hidden_member"),
        ("authority_visibility", "hidden_site"), ("deep_link_identity", "project"),
        ("deep_link_identity", "site"), ("deep_link_identity", "subject"),
        ("source_one_hop", "listing_row"), ("source_one_hop", "listing_cell"),
        ("source_one_hop", "nearest_fallback"),
    }:
        return "P0"
    category_defaults = {"center_stable_order": "P3", "encoding_registry": "P3", "deterministic_replay": "P3", "high_density_performance": "P3", "audience_lexicon": "P4", "interaction_no_mutation": "P0", "center_pattern_individual": "P2", "inspector_evidence_order": "P2", "return_context": "P2", "eight_domain_adaptation": "P2", "aemh_projection": "P2", "aemh_match_history": "P2"}
    return category_defaults.get(category, "P1")

def verify_case_spec(row: dict, exact: dict) -> None:
    category = row.get("category")
    require(category in EXPECTED_CATEGORY_SLOTS, "unknown_category", str(category))
    mutation = row.get("single_mutation")
    require(isinstance(mutation, dict) and set(mutation) == {"op", "path", "value"}, "mutation_shape")
    require(mutation["op"] == "replace", "mutation_op")
    prefix = f"/input/{category}/"
    require(isinstance(mutation["path"], str) and mutation["path"].startswith(prefix), "mutation_path")
    slot = mutation["path"][len(prefix):]
    require(slot in EXPECTED_CATEGORY_SLOTS[category], "mutation_slot", slot)
    rule_id = f"{category}.{slot}"
    expected = row.get("expected_typed_outcome_or_error")
    expected_status = "accept:" if rule_id in EXPECTED_ACCEPT_RULES else "reject:"
    require(expected == expected_status + rule_id, "expected_rule_mismatch")
    oracle = row.get("stage_oracle_contract")
    require(isinstance(oracle, dict) and set(oracle) == ORACLE_KEYS, "oracle_shape")
    require(oracle["kind"] == "planned_pytest", "oracle_kind")
    require(oracle["rule_id"] == rule_id, "oracle_rule")
    projection = "emitted" if expected.startswith("accept:") else "not_emitted"
    require(oracle["expected_projection"] == projection, "oracle_projection")
    rules = {item["rule_id"]: item for item in exact["challenge_rules"]}
    require(rule_id in rules, "oracle_rule_missing")
    rule = rules[rule_id]
    require(rule == {"rule_id": rule_id, "category": category, "slot": slot, "valid_value": f"valid::{category}::{slot}", "mutated_value": f"mutated::{category}::{slot}", "expected_outcome": expected, "expected_projection": projection}, "rule_definition")
    require(mutation["value"] == rule["mutated_value"], "mutation_value")
    require(oracle["expected_outcome"] == expected and oracle["expected_projection"] == projection, "oracle_expected")
    require(oracle["test_locator"] == f"poc/medical_monitoring_ai_native_r5/tests/challenges/test_{category}.py::test_{slot}", "oracle_test_locator")
    require(oracle["planned_stage"] in {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}, "oracle_stage")
    require(row["severity"] == severity_for(category, slot), "rule_severity")

def resolve_source_path(path: str) -> None:
    module_name, remainder = path.split(":", 1)
    class_name, *field_names = remainder.split(".")
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    current = cls
    for field_name in field_names:
        fields = getattr(current, "__dataclass_fields__", {})
        require(field_name in fields, "source_path_missing", path)
        current = get_type_hints(current)[field_name]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out.resolve()
    require(sha(CONTRACT) == PINNED_CONTRACT_SHA, "contract_pin")
    require(sha(ROOT / "scripts/generate_medical_monitoring_r5_contract_v0_3_artifacts.py") == PINNED_GENERATOR_SHA, "generator_pin")
    require({p.name for p in out.glob("*.json")} == set(PINNED_ARTIFACT_SHA), "artifact_set")
    for name, expected in PINNED_ARTIFACT_SHA.items():
        require(sha(out / name) == expected, "artifact_pin", name)

    manifest, exact = load(out / "manifest.json"), load(out / "exact_contract.json")
    registry, ledger = load(out / "challenge_registry.json"), load(out / "quota_ledger.json")
    require(set(manifest) == {"schema", "contract_sha256", "artifact_names", "artifacts", "generator_sha256"}, "manifest_keys")
    require(manifest["contract_sha256"] == PINNED_CONTRACT_SHA and manifest["generator_sha256"] == PINNED_GENERATOR_SHA, "manifest_pins")
    require(manifest["artifact_names"] == ["challenge_registry.json", "exact_contract.json", "quota_ledger.json"], "manifest_names")
    require(manifest["artifacts"] == {k: PINNED_ARTIFACT_SHA[k] for k in manifest["artifact_names"]}, "manifest_artifacts")

    require(set(exact) == {"schema", "contract_sha256", "enums", "objects", "field_mappings", "invariants", "challenge_rules", "risk_overlay_shape", "event_forbidden_shapes", "unknown_domain_policy", "legacy_domain_policy", "performance_profile"}, "exact_contract_keys")
    require(exact["contract_sha256"] == PINNED_CONTRACT_SHA, "exact_contract_pin")
    require(exact["enums"] == EXPECTED_ENUMS, "enum_drift")
    require(set(exact["objects"]) == EXPECTED_OBJECTS, "object_set")
    for object_name, fields in exact["objects"].items():
        require(isinstance(fields, dict) and fields, "object_fields", object_name)
        for field_name, spec in fields.items():
            require(set(spec) == {"type", "cardinality", "nullable"}, "field_spec_keys", f"{object_name}.{field_name}")
            require(spec["cardinality"] in {"one", "many"} and isinstance(spec["nullable"], bool), "field_spec_value", f"{object_name}.{field_name}")
            require(spec["type"] != "json", "bare_json_type", f"{object_name}.{field_name}")
    expected_targets = {f"{object_name}.{field_name}" for object_name, fields in exact["objects"].items() for field_name in fields}
    mappings = exact["field_mappings"]
    require(all(set(item) == {"target", "source_kind", "source_paths", "recipe_id", "validation_paths", "deferred_contract"} for item in mappings), "field_mapping_keys")
    require(len(mappings) == len(expected_targets) == len({item["target"] for item in mappings}), "field_mapping_cardinality")
    require({item["target"] for item in mappings} == expected_targets, "field_mapping_coverage")
    require(all(item["source_kind"] in {"r4_direct", "derived", "canonical_derived", "ui_state", "contract_constant", "deferred"} for item in mappings), "field_mapping_source_kind")
    for generation in ("r1", "r2", "r3", "r4"):
        sys.path.insert(0, str(ROOT / f"poc/medical_monitoring_ai_native_{generation}/src"))
    for item in mappings:
        if item["source_kind"] in {"r4_direct", "derived"}:
            require(bool(item["source_paths"]), "source_paths_empty", item["target"])
            for path in item["source_paths"]:
                resolve_source_path(path)
        else:
            require(not item["source_paths"], "non_authority_source_paths", item["target"])
        if item["source_kind"] == "canonical_derived":
            require(item["recipe_id"].startswith("canonical_sha256."), "canonical_recipe", item["target"])
        if item["source_kind"] == "deferred":
            require(bool(item["deferred_contract"]), "deferred_contract_missing", item["target"])
        else:
            require(item["deferred_contract"] is None, "unexpected_deferred_contract", item["target"])
        for path in item["validation_paths"]:
            resolve_source_path(path)
    rules = exact["challenge_rules"]
    require(len(rules) == 204 == len({item["rule_id"] for item in rules}), "challenge_rule_count")
    require(all(set(item) == {"rule_id", "category", "slot", "valid_value", "mutated_value", "expected_outcome", "expected_projection"} for item in rules), "challenge_rule_keys")
    invariants = exact["invariants"]
    required_invariants = {"receipt_identity_exact", "deep_link_identity_exact", "canonical_content_hash", "unique_reference_sets", "denominator_rate_consistency", "date_geometry_consistency", "domain_subtype_matrix", "aemh_append_only_transition", "severity_lexicon_bijection", "severity_authority_no_promotion", "legacy_severity_mapping", "risk_overlay_unique", "domain_encoding_complete_unique", "legacy_treatment_fail_closed"}
    require(len(invariants) == len(required_invariants) and {item["invariant_id"] for item in invariants} == required_invariants, "invariant_set")
    require(all(set(item) == {"invariant_id", "objects", "predicate", "error_code"} for item in invariants), "invariant_keys")
    canonical_invariant = next(item for item in invariants if item["invariant_id"] == "canonical_content_hash")
    require({"R5SubjectWorkspaceState", "R5ReturnContext"}.issubset(canonical_invariant["objects"]), "canonical_hash_object_coverage")
    domain_encoding_invariant = next(item for item in invariants if item["invariant_id"] == "domain_encoding_complete_unique")
    require("eight closed domains exactly once" in domain_encoding_invariant["predicate"] and "event_shape=circle" in domain_encoding_invariant["predicate"], "domain_encoding_invariant_exact")
    require(exact["risk_overlay_shape"] == "double_chevron_badge" and exact["risk_overlay_shape"] in exact["event_forbidden_shapes"], "risk_event_shape_collision")
    require(exact["legacy_domain_policy"] == {"background_treatment": "frozen_mapping_or_fail_closed", "non_drug_treatment": "frozen_mapping_or_fail_closed", "OTHER": "forbidden"}, "legacy_domain_policy")
    perf = exact["performance_profile"]
    require(perf["dataset"] == {"events": 1000, "metrics": 40, "risk_anchors": 300}, "performance_dataset")
    require(perf["samples_per_mode"] == 7 and perf["summary_statistic"] == "p95_nearest_rank", "performance_sampling")
    require(perf["thresholds"] == {"cold_interactive_ms_p95": 2500, "warm_interactive_ms_p95": 1500, "brush_zoom_select_ms_p95": 100, "pan_fps_p05": 30}, "performance_thresholds")

    rows, instances = registry["rows"], ledger["instances"]
    expected_quotas = {k: len(v) for k, v in EXPECTED_CATEGORY_SLOTS.items()}
    require(registry["row_count"] == len(rows) == 204, "registry_count")
    require(ledger["category_quotas"] == expected_quotas and ledger["expected_total"] == ledger["instance_count"] == len(instances) == 204, "ledger_quota")
    require(len({r["case_id"] for r in rows}) == 204, "case_id_unique")
    require(len({r["single_mutation"]["path"] for r in rows}) == 204, "mutation_unique")
    require(Counter(r["category"] for r in rows) == Counter(expected_quotas), "category_coverage")
    for row in rows:
        require(set(row) == ROW_KEYS, "row_keys", str(row.get("case_id")))
        require(row["severity"] in {"P0", "P1", "P2", "P3", "P4"}, "severity")
        verify_case_spec(row, exact)
    require(len({i["quota_instance_id"] for i in instances}) == 204, "quota_id_unique")
    require(len({i["case_id"] for i in instances}) == 204, "ledger_case_one_to_one")
    require(all(set(i) == {"quota_instance_id", "category", "case_id"} for i in instances), "ledger_instance_keys")
    by_id = {r["case_id"]: r for r in rows}
    require(all(i["case_id"] in by_id and i["category"] == by_id[i["case_id"]]["category"] for i in instances), "ledger_binding")

    required_rules = {
        "encoding_registry.severity_high_not_critical", "encoding_registry.severity_critical_authority",
        "encoding_registry.legacy_severe_mapping", "encoding_registry.legacy_moderate_mapping", "encoding_registry.legacy_mild_mapping",
        "eight_domain_adaptation.efficacy_subtype", "eight_domain_adaptation.background_mapping",
        "eight_domain_adaptation.non_drug_mapping", "eight_domain_adaptation.unknown_other_forbidden",
        "high_density_performance.cold_interactive", "high_density_performance.brush_response", "high_density_performance.pan_fps",
    }
    actual_rules = {r["stage_oracle_contract"]["rule_id"] for r in rows}
    require(required_rules <= actual_rules, "required_semantic_rules")
    print(json.dumps({"ok": True, "contract_sha256": PINNED_CONTRACT_SHA, "registry_rows": 204, "quota_instances": 204, "distinct_rules": len(actual_rules), "pinned_artifacts": PINNED_ARTIFACT_SHA}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
