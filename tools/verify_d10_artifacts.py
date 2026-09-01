#!/usr/bin/env python3
"""Independent D10 artifact verifier (finite code executor).

TRULY independent: this module NEVER imports, calls or reads the catalog
generator, the oracle generator, their functions, constants or audits. It is
stdlib-only and reads ONLY the frozen contract, the typed fixture catalog,
the expected-outcome oracle, the challenge registry, the quota manifest and
the fixed fixture authority registry.

It rebuilds, from its own exact schemas, closed enums, rule tables and
typed-fact projection:
  * every disposition/gate + primary reason,
  * the expected/source/trace/forbidden leaf sets,
  * all recomputable object hashes (legal row, scope, mode, source revision,
    descendant set, origin, query, visibility decision, model, assignment),
  * the stable unit core and content identity from the ACCEPTED fixture
    authority (never from case ids/indexes),
  * per-case authority conformance (the catalog must equal the fixed
    authority entry on every decisive field),
  * global chain checks (contract SHA, catalog schema + null expected leaves,
    partition/attack quotas, registry bijection, oracle schema/hash,
    authority schema/hash/coverage/pin, cross-chain hashes).

Public entry points: `verify_all() -> dict` (for tests) and `main()`/`check()`
(CLI, exit code 0/1). No runtime/UI/service code; no network; no wall-clock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md"
CATALOG = ROOT / "reviews/medical_monitoring_r4_d10_typed_fixture_catalog_v1_20260816.json"
ORACLE = ROOT / "reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"
REGISTRY = ROOT / "reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json"
QUOTA = ROOT / "reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json"
AUTHORITY = ROOT / "reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"

CONTRACT_FILE_SHA256 = "c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95"
CONTRACT_SEMANTIC_HASH = CONTRACT_FILE_SHA256
REQUIRED_TOTAL = 312
EXPECTED_CASE_COUNT = 312

# ---------------------------------------------------------------------------
# FIXED non-replaceable artifact identities (frozen snapshot pins; NOT read
# from tests or production modules - hardcoded in this verifier itself).
# Placeholders (all-zero hex) are replaced by the frozen values at freeze
# time; VERIFIER_SELF_SHA256 is self-referential (its literal is normalized
# to 64 zeros before hashing, so the pin never feeds back into the hash).
# ---------------------------------------------------------------------------
AUTHORITY_GENERATOR_FILE_SHA256 = "4faa1317eb184fc91b2d934f944a25c484788469fb5cd1dc6221b875272f9e1d"
AUTHORITY_GENERATOR_PIN = "71c91c7d61baf48fa028ec3c95d1ab402b72bae4482314c9030ffa22b74a5fa2"
AUTHORITY_RAW_SHA256 = "191f4b4fcddfebfbc29d48111bf8b45477d435ae62def0199bed0edd587fa7f0"
AUTHORITY_CONTENT_SHA256 = "77301e4b832cdd9e576f451e12e3b4b5a76fc7c6869b32f2e7f4c037985361fd"
CATALOG_GENERATOR_FILE_SHA256 = "84c43a81952a1b33fbfcaf6cf244b13cf6eeda5625a501f0bc76b369a6df3dfe"
CATALOG_GENERATOR_PIN = "2984d7fe908d08343e2289ff9d8ec0c5c221dd1cde532113b61c058bd17def8b"
CATALOG_RAW_SHA256 = "40ce96b2e5c188167cacbe03a8b5a80260886276cbacd1edbd1261f9b7927939"
CATALOG_CONTENT_SHA256 = "3b864d4be7c810c00dd3174b16d48dd4470a76e529365930fd56023e20a5e6db"
ORACLE_GENERATOR_FILE_SHA256 = "1a98ea1948001dd72d5069a8418fa12cc7b5018c456d5b886e62a56cd0ffd1c5"
ORACLE_RAW_SHA256 = "435492cd2c86ef0e3a6b6061f9cd992d12396579a07b8f186c3c533fd9260ec3"
ORACLE_CONTENT_SHA256 = "de2864c2bffdb8e2f338d3d84bc878adff03e5db6ccb5883f7bced4ab0251814"
REGISTRY_RAW_SHA256 = "2f2763c5b351331ab103882dab72d996f10ede08e45d627a4baacb3fdb3709d6"
REGISTRY_CONTENT_SHA256 = "75f828ee5fff91aea7cd52f9d66ebd290e470621a30dcf94aae85f247ef4c6cb"
QUOTA_RAW_SHA256 = "7041cd4167ba5c604d20bfefbbe9c6aaa136ed3d0d933d064f80cf819ba88ffa"
QUOTA_CONTENT_SHA256 = "cdb6874d4ed3d3e029b5e79e42f1719e1c95edfecc0616af1eded65b3c421697"
VERIFIER_SELF_SHA256 = "817a40713090184be9be65dae619daef739dc486d39a9956683ce27f24a9291f"
_SELF_PIN_SENTINEL = "0" * 64


def _self_code_hash() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    return sha256_text(source.replace(VERIFIER_SELF_SHA256, _SELF_PIN_SENTINEL))


# Closed partition/attack identities (contract section 15), hardcoded here.
PARTITION_IDS = (
    "p01_signal_kind_disposition", "p02_owner_routing_zero_medical",
    "p03_identity_scope_duplicate", "p04_numerator_denominator_time",
    "p05_cross_site_comparability", "p06_safety_trend",
    "p07_efficacy_trend", "p08_change_cause_lineage", "p09_query_deeplink",
    "p10_visibility_blindness", "p11_unicode_tamper_bijection",
    "p12_anti_overfit",
)
ATTACK_IDS = (
    "cross_project_scope", "legal_row_mismatch",
    "initial_full_fake_change", "strict_cutoff_predicate_tamper_same_window_replay",
    "cutoff_first_positive_create", "cutoff_rule_or_mode_mixed_first_positive",
    "required_l1_hole", "gap_only_provenance",
    "measure_origin_cross_envelope_mixed", "d09_parent_descendant_duplication",
    "d07_risk_safety_measure_same_origin", "denominator_time_segment_tamper",
    "small_site_stigma", "blind_hidden_set_omission",
    "hidden_deeplink_eligible_subset_violation", "treatment_assignment_missing",
    "formal_safety_efficacy_wording", "model_majority_ensemble1_positive",
    "r2_wrong_prior_lineage_carry_forward",
    "query_reorder_source_pd_redundancy_tamper",
    "projection_deeplink_visibility_tamper",
    "unicode_confusable_engineering_inject",
    "rule_method_visibility_mixed_change", "hotspot_singleton_not_hidden",
    "d09_within_site_trend_recompute", "cross_layer_count_mixing",
    "non_data_change_as_improvement",
    "zero_event_empty_denominator_negative", "blind_treatment_inference",
    "efficacy_estimand_mismatch_forced_comparison",
    "rehash_bypass_evaluator_identity", "audience_engineering_injection",
)
AUTHORITY_GENERATOR_PATH = ROOT / "tools/generate_d10_fixture_authority.py"
CATALOG_GENERATOR_PATH = ROOT / "tools/generate_d10_challenge_registry.py"
ORACLE_GENERATOR_PATH = ROOT / "tools/generate_d10_expected_oracle.py"

# ---------------------------------------------------------------------------
# Independent exact schema copies (frozen contract + generator documents)
# ---------------------------------------------------------------------------
CATALOG_TOP_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
CASE_KEYS = [
    "case_id", "primary_partition", "family_id", "grain", "owner_route",
    "clinical_claim_token", "disposition", "fixture_id", "fixture_hash",
    "oracle_case_id", "manifest_case_id", "expected_leaf_set",
    "expected_trace_leaf_set", "expected_source_leaf_set", "mutation_class",
    "audience_contract", "typed_input",
]
AUDIENCE_CONTRACT_KEYS = [
    "audience_contract_id", "audience_scope_id", "display_language",
    "blind_status", "lexicon_ref", "forbidden_internal_terms",
    "injection_blocked",
]
TYPED_INPUT_KEYS = [
    "input_schema", "envelope_id", "project_ref", "run_ref", "snapshot_ref",
    "source_revision_content_pairs", "project_scope_binding", "mode_contract",
    "signal_definition", "legal_matrix_row", "expected_set",
    "analysis_windows", "stratum", "comparison_gate", "window_pair_gate",
    "site_ledger", "members", "numerator_ledger", "measure_origin_binding",
    "denominator", "time_segments", "opportunity", "analysis_population",
    "coverage", "change_decision", "visibility_decision", "query_decision",
    "audience_text", "deep_links", "model_evidence", "safety_context",
    "efficacy_context", "rule_hit", "hotspot", "count_layers",
    "evaluation_limits", "numeric_policy", "mutation_context",
    "anti_overfit_variant", "evidence_refs",
]
SCOPE_BINDING_KEYS = ["scope_binding_id", "scope_type",
                      "scope_equality_decision", "scope_binding_hash"]
MODE_CONTRACT_KEYS = ["mode_contract_version", "mode_contract_content_hash",
                      "design_clause_ref", "design_applicable_state"]
SIGNAL_DEFINITION_KEYS = [
    "signal_definition_id", "signal_kind", "clinical_claim_token", "d10_action",
    "risk_or_outcome_domain", "required_producer_domains", "positive_rule_ref",
    "counterevidence_rule_refs", "legal_matrix_row_ref", "authority_locator",
]
LEGAL_MATRIX_ROW_KEYS = ["row_id", "signal_kind", "clinical_claim_token",
                         "d10_action", "row_hash"]
EXPECTED_SET_KEYS = ["expected_set_state", "admission_gate"]
ADMISSION_GATE_KEYS = ["gate_kind", "reason_codes"]
WINDOW_KEYS = ["analysis_window_stable_id", "window_instance_id",
               "window_definition_id", "window_definition_hash", "window_kind",
               "window_state", "window_start", "window_end", "cutoff_ref"]
STRATUM_KEYS = ["stratum_contract_id", "stratum_key", "stratum_state",
                "stratum_admission"]
COMPARISON_GATE_KEYS = ["comparison_state", "required_site_count_ref",
                        "observed_eligible_site_count", "eligible_site_refs",
                        "excluded_site_refs", "reason_codes",
                        "permitted_output", "comparison_reference_stable_id"]
WINDOW_PAIR_GATE_KEYS = ["pair_state", "required_window_count_ref",
                         "observed_unique_window_count", "reason_codes",
                         "permitted_output"]
SITE_LEDGER_KEYS = ["ledger_id", "site_ref", "eligible_subject_refs",
                    "treated_subject_refs", "evaluable_subject_refs",
                    "d09_pattern_refs", "coverage_refs",
                    "site_activation_ref", "site_activation_state",
                    "identity_state"]
MEMBER_KEYS = ["member_ref", "member_kind", "aggregation_plane",
               "producer_domain", "member_scope_state", "site_stable_id",
               "subject_stable_id", "monitoring_priority",
               "accepted_current_state", "locator_resolution_state",
               "source_locator_refs", "descendant_member_refs",
               "descendant_set_hash", "treatment_role_ref"]
NUMERATOR_LEDGER_KEYS = ["individual_risk_count", "center_pattern_count",
                         "affected_subject_count", "event_or_outcome_count",
                         "affected_site_count", "numerator_member_count"]
MEASURE_ORIGIN_BINDING_KEYS = ["binding_id", "measure_ref", "origin_decision",
                               "verified_risk_refs", "distinct_risk_refs",
                               "ambiguous_risk_refs", "candidate_risk_refs",
                               "candidate_partition_hash",
                               "numerator_plane_state", "binding_hash"]
DENOMINATOR_KEYS = ["denominator_kind", "denominator_member_refs",
                    "denominator_value", "recomputed_value",
                    "denominator_unit", "denominator_state",
                    "exclusion_reason_codes", "excluded_member_refs"]
TIME_SEGMENT_KEYS = ["segment_id", "member_ref", "segment_kind", "start_value",
                     "end_value", "raw_duration", "normalized_duration",
                     "unit", "inclusivity", "overlap_resolution_ref"]
OPPORTUNITY_KEYS = ["opportunity_definition_ref", "expected_opportunity_count",
                    "observed_opportunity_count", "missing_opportunity_refs",
                    "opportunity_provenance", "opportunity_state", "complete"]
ANALYSIS_POPULATION_KEYS = ["analysis_population_ref", "present",
                            "analysis_population_contract_id"]
COVERAGE_KEYS = ["producer_domain", "l0_status",
                 "l1_medical_completeness_state", "accepted_current",
                 "coverage_locator_ids"]
CHANGE_DECISION_KEYS = [
    "execution_basis", "comparison_state", "prior_snapshot_ref_or_none",
    "data_change_refs", "denominator_change_refs", "coverage_change_refs",
    "knowledge_change_refs", "rule_change_refs", "mapping_change_refs",
    "model_change_refs", "method_change_refs", "population_change_refs",
    "visibility_change_refs", "mode_change_refs", "cutoff_advance",
    "r2_prior_ref_or_none", "r2_action", "lineage_relation",
    "carry_forward_state", "claimed_clinical_change_kind",
    "claimed_primary_change_cause", "claimed_cutoff_state",
    "data_change_kind",
]
CUTOFF_ADVANCE_KEYS = ["decision_state", "strict_advance_predicate_passed",
                       "policy_semantic_hash_equal", "prior_boundary_value",
                       "current_boundary_value"]
VISIBILITY_KEYS = [
    "blind_status", "audience_scope_id", "evaluation_member_refs",
    "projectable_member_refs", "hidden_member_refs", "hidden_reason_codes",
    "evaluation_site_refs", "projectable_site_refs", "hidden_site_refs",
    "visible_n", "eligible_n", "hidden_member_count", "hidden_site_count",
    "rate_projection_state", "deep_link_eligible_member_refs",
    "deep_link_eligible_site_refs", "hidden_set_omitted",
    "deep_link_eligible_violation", "treatment_inference_attempt",
    "projectable_subject_site_pairs",
    "deep_link_eligible_subject_site_pairs",
    "decision_id",
]
QUERY_DECISION_KEYS = ["decision", "covered_member_refs", "uncovered_member_refs",
                       "member_query_content_identities",
                       "unit_member_set_hash", "coverage_proof_hash",
                       "max_query_member_fanout",
                       "member_unlistable", "pd_wording_state",
                       "duplicate_query_attempt", "query_content_hash"]
AUDIENCE_TEXT_KEYS = ["audience_contract_id", "display_language",
                      "sentence_part_kind", "basis_zh", "finding_zh",
                      "action_zh", "engineering_reference_attempt",
                      "injection_blocked"]
DEEP_LINK_KEYS = ["target_kind", "site_ref", "subject_ref", "member_object_ref",
                  "visibility_decision_ref", "return_state_key"]
MODEL_EVIDENCE_KEYS = ["model_evidence_id", "role",
                       "evaluation_content_identity", "input_content_hash",
                       "source_revision_content_pairs", "source_refs",
                       "model_id", "model_version", "independent_context_hash",
                       "ensemble_id", "ensemble_size", "member_analysis_refs",
                       "permitted_leaf", "member_analysis_ref_set_hash",
                       "output_identity", "output_hash", "adjudication_state",
                       "model_binding_hash"]
SAFETY_CONTEXT_KEYS = ["context_id", "context_complete", "exposure_definition_ref",
                       "coding_dictionary_ref", "severity_scale_ref",
                       "risk_window_ref", "descriptive_monitoring_only"]
EFFICACY_CONTEXT_KEYS = [
    "context_id", "context_complete", "endpoint_definition_ref",
    "estimand_ref", "missing_data_rule_ref", "intercurrent_event_rule_ref",
    "treatment_role_authority_ref", "treatment_assignment_exposure_identity_ref",
    "treatment_role_required", "blind_visibility_contract_ref",
    "descriptive_monitoring_only", "estimate_kind",
    "treatment_assignment_mapping_hash",
]
RULE_HIT_KEYS = ["positive_rule_ref", "hit_state", "evidence_sources",
                 "counterevidence_matched_refs", "counterevidence_declared_refs"]
HOTSPOT_KEYS = ["hotspot_member_refs", "hidden_in_display"]
COUNT_LAYERS_KEYS = ["layers_in_common_numerator", "mixed"]
NUMERIC_POLICY_KEYS = ["policy_id", "allowed_estimate_kinds", "decimal_context",
                       "rounding_mode", "display_precision", "subject_time_unit",
                       "exposure_time_unit", "overlap_policy"]
MUTATION_CONTEXT_KEYS = ["mutation_class", "desc", "variant_id", "base_fixture_id"]
ANTI_OVERFIT_KEYS = ["base_fixture_id", "semantic_equivalence_ref",
                     "surface_changes", "variant_id"]
SURFACE_CHANGE_KEYS = ["changed_token", "from_value", "to_value"]
EVIDENCE_REF_KEYS = ["locator_id", "locator_kind", "source_file",
                     "row_or_cell_ref", "lineage_ref"]
EVALUATION_LIMITS_KEYS = ["small_sample", "limited_evidence", "limited_reason"]

ORACLE_TOP_KEYS = [
    "artifact_kind", "oracle_id", "schema_version", "contract_semantic_hash",
    "case_count", "ordered_expectations", "fixture_authority_registry_hash",
    "content_hash",
]
ORDERED_EXPECTATION_KEYS = [
    "case_id", "oracle_case_id", "fixture_id", "expected_leaf_set",
    "expected_trace_leaf_set", "expected_source_leaf_set",
    "expected_disposition_or_gate", "forbidden_leaf_set", "oracle_hash",
]
LEAF_KEYS = [
    "leaf_kind", "signal_kind", "expected_disposition", "gate_kind",
    "reason_codes", "unit_stable_core_ref", "numerator_member_count",
    "numerator_individual_risk_count", "numerator_affected_subject_count",
    "numerator_event_or_outcome_count", "numerator_center_pattern_count",
    "numerator_affected_site_count", "denominator_kind", "denominator_value",
    "denominator_state", "estimate_kind", "project_signal_count",
    "clue_count", "query_count", "risk_handoff_count", "change_kind",
    "change_cause", "lineage_relation", "handoff_action",
    "rate_projection_state", "hidden_member_count", "hidden_site_count",
    "deep_link_target_count", "member_expansion_state",
    "query_redundancy_decision", "pd_wording_state",
    "audience_injection_blocked", "counterevidence_rule_matches",
    "model_evidence_role", "hotspot_member_refs",
]
TRACE_LEAF_KEYS = ["trace_kind", "stable_core_ref", "content_identity",
                   "replay_byte_equal", "terminal_state"]
SOURCE_LEAF_KEYS = ["member_ref", "source_locator_ref", "resolution_state",
                    "site_stable_id", "subject_stable_id"]
FORBIDDEN_LEAF_KEYS = ["leaf_kind", "expected_disposition", "gate_kind",
                       "change_kind", "reason_code"]

REGISTRY_TOP_KEYS = [
    "artifact_kind", "registry_id", "schema_version", "contract_semantic_hash",
    "catalog_hash", "quota_manifest_hash", "generator_hash",
    "oracle_reference_state", "rows", "bijection_audit", "content_hash",
]
REGISTRY_ROW_KEYS = ["case_id", "fixture_id", "oracle_case_id",
                     "manifest_case_id", "test_id"]
BIJECTION_COLUMNS = ["case_id", "fixture_id", "oracle_case_id",
                     "manifest_case_id", "test_id"]
ORACLE_REFERENCE_STATE_KEYS = [
    "state", "reserved_for", "oracle_artifact_path", "expected_leaf_policy",
    "catalog_expected_fields",
]

QUOTA_TOP_KEYS = [
    "manifest_id", "required_total", "primary_partition_requirements",
    "mandatory_attack_requirements", "actual_mandatory_attack_counts",
    "case_to_mandatory_attack_rows", "actual_primary_partition_counts",
    "case_id_union", "pairwise_intersection_counts", "union_count",
    "duplicate_case_ids", "missing_case_ids", "catalog_hash", "oracle_hash",
    "registry_hash", "generator_hash", "manifest_hash",
]

AUTHORITY_TOP_KEYS = ["authority_id", "schema_version", "contract_semantic_hash",
                      "case_count", "generator_hash", "entries",
                      "bijection_audit", "content_hash"]
AUTHORITY_ENTRY_KEYS = [
    "case_id", "authority_id", "partition", "signal_definition",
    "legal_matrix_row", "scope_binding", "project_ref", "run_ref",
    "snapshot_ref", "mode_contract", "expected_set", "analysis_windows",
    "stratum", "comparison_reference_stable_id", "analysis_population",
    "members", "numerator_ledger", "denominator",
    "denominator_member_set_hash", "time_segments", "d09_patterns",
    "measure_origin", "treatment", "visibility", "deep_links", "query",
    "model_evidence", "audience_contract", "source_revisions",
    "source_locator_set_hash", "evidence_refs", "change",
    "hotspot_member_ref", "authority_hash",
]
AUTHORITY_EVIDENCE_REF_KEYS = ["locator_id", "locator_kind", "source_file",
                               "row_or_cell_ref", "lineage_ref"]
AUTHORITY_CHANGE_KEYS = ["execution_basis", "comparison_state", "prior_present",
                         "prior_evaluation_identity_ref", "r2_prior_ref",
                         "r2_action", "r2_lineage", "carry_forward",
                         "data_change_ref_set_hash", "denominator_change_ref_set_hash",
                         "coverage_change_ref_set_hash", "knowledge_change_ref_set_hash",
                         "rule_change_ref_set_hash", "mapping_change_ref_set_hash",
                         "model_change_ref_set_hash", "method_change_ref_set_hash",
                         "population_change_ref_set_hash", "visibility_change_ref_set_hash",
                         "mode_change_ref_set_hash", "cutoff_decision_state",
                         "cutoff_predicate", "cutoff_policy_equal",
                         "prior_boundary_value", "current_boundary_value"]
AUTHORITY_MEMBER_KEYS = ["member_ref", "member_kind", "aggregation_plane",
                         "subject_stable_id", "site_stable_id",
                         "member_scope_state", "locator_resolution_state",
                         "monitoring_priority", "producer_domain", "locator_ref"]

# ---------------------------------------------------------------------------
# Independent closed enums (frozen contract v0.6)
# ---------------------------------------------------------------------------
SIGNAL_KINDS = ("project_risk_distribution", "cross_site_pattern",
                "project_time_trend", "project_safety_trend",
                "project_efficacy_trend")
OWNED_TOKENS = frozenset({
    "d10_project_risk_distribution", "d10_cross_site_pattern",
    "d10_project_time_trend", "d10_project_safety_trend",
    "d10_project_efficacy_trend",
})
CONSUME_ONLY_TOKENS = ("d09_within_site_pattern", "d01_d08_individual_claim")
HANDOFF_ONLY_TOKENS = ("formal_benefit_risk_conclusion",
                       "confirmatory_treatment_effect",
                       "site_quality_judgment")
OWNER_ROUTES = ("evaluate_and_own", "consume_only", "handoff_only",
                "context_only", "routing_gate")
DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")
GATE_DISPOSITIONS = frozenset({"global_gate", "comparison_set_gate",
                               "window_pair_gate", "routing_gate",
                               "integrity_gate", "handoff_gate"})
EXPECTED_DISPOSITION_OR_GATE = DISPOSITIONS + tuple(sorted(GATE_DISPOSITIONS))
MEMBER_KINDS = ("individual_risk", "center_pattern", "accepted_gap",
                "safety_measure", "efficacy_measure", "denominator_member")
AGGREGATION_PLANES = ("individual", "site_pattern", "project_measure")
DENOMINATOR_KINDS = ("enrolled_subjects", "treated_subjects",
                     "safety_evaluable_subjects", "efficacy_evaluable_subjects",
                     "subject_time", "exposure_time",
                     "expected_assessment_opportunities",
                     "analysis_population_members")
DENOMINATOR_STATES = ("closed_positive", "closed_zero", "unclosed")
ESTIMATE_KINDS = ("count", "proportion", "incidence_rate",
                  "exposure_adjusted_rate", "summary_statistic",
                  "responder_rate", "model_estimate")
L0_STATUSES = ("covered", "missing", "partial", "truncated", "not_evaluable", "failed")
L1_STATES = ("complete", "partial", "not_evaluable", "missing")
COMPARISON_STATES = ("insufficient_sites", "incomparable_sites", "ready")
PAIR_STATES = ("insufficient_windows", "incomparable_windows", "ready")
CHANGE_KINDS = ("initial_current", "new", "continued", "upgraded",
                "downgraded", "resolved", "reopened", "not_comparable")
CHANGE_CAUSES = ("data", "denominator", "coverage", "knowledge", "rule",
                 "mapping", "model", "method", "population", "visibility",
                 "mode", "mixed")
LINEAGE_RELATIONS = ("initial_full_snapshot", "continued_from_data_revision",
                     "continued_from_cutoff_advance",
                     "superseded_by_knowledge_change",
                     "superseded_by_rule_or_mapping_change",
                     "superseded_by_method_or_population_change",
                     "superseded_by_mode_change",
                     "superseded_by_visibility_change",
                     "coverage_regressed", "not_comparable", "none")
HANDOFF_ACTIONS = ("create", "continue", "update", "propose_close",
                   "reopen", "supersede")
CUTOFF_DECISION_STATES = ("strict_advance", "same_window", "policy_changed",
                          "not_evaluable")
ORIGIN_DECISIONS = ("all_verified_same_origin", "all_distinct",
                    "mixed_verified_and_distinct", "ambiguous", "wrong_scope",
                    "not_evaluable")
BLIND_STATUSES = ("blinded", "unblinded_authorized")
RATE_PROJECTION_STATES = ("permitted", "suppressed", "qualified")
QUERY_REDUNDANCY_DECISIONS = ("project_delta_present",
                              "fully_covered_by_member_queries",
                              "members_unlistable", "not_applicable")
PD_WORDING_STATES = ("not_pd", "verify_whether_pd")
MEMBER_EXPANSION_STATES = ("expanded", "unexpandable", "not_applicable")
DEEP_LINK_TARGET_KINDS = ("member", "site", "subject_site_pair")
MODEL_EVIDENCE_ROLES = ("candidate_explanation", "counterevidence_suggestion")
MEMBER_SCOPE_STATES = ("in_scope", "wrong_project", "wrong_site",
                       "wrong_subject", "unresolvable")
SITE_ACTIVATION_STATES = ("active", "late")
SCOPE_EQUALITY_DECISIONS = ("exact_match", "mismatch")
RULE_HIT_STATES = ("hit", "no_hit", "not_applicable")
EVIDENCE_SOURCES = ("typed_member", "verified_measure", "pvalue", "model_majority")
EXPECTED_SET_STATES = ("admitted", "global_admission_failed",
                       "routed_consume_only", "routing_gate_unresolved",
                       "control_plane_gate")
DESIGN_APPLICABLE_STATES = ("applicable", "not_applicable", "unresolved")
LEAF_KINDS = ("medical_unit", "hotspot_member_leaf",
              "control_plane_comparison_gate", "control_plane_window_pair_gate",
              "global_integrity_gate", "routing_gate", "handoff_gate",
              "analysis_only_change_leaf")
ALLOWED_CREATE_LINEAGES = frozenset({
    "initial_full_snapshot", "continued_from_data_revision",
    "continued_from_cutoff_advance",
})
DATA_CHANGE_KINDS = ("new", "continued", "upgraded", "downgraded",
                     "resolved", "reopened")
NOT_EVALUABLE_COMP_CODES = frozenset({
    "method_validity_insufficient", "site_evidence_incomplete",
    "case_mix_missing", "site_quality_judgment",
})
BOUNDARY_COMP_CODES = frozenset({
    "site_small", "site_small_outlier", "site_late_start",
    "site_late_start_outlier", "case_mix_mismatch", "followup_shortfall",
    "exposure_shortfall", "heterogeneous_sites",
})
STIGMA_CODES = frozenset({"site_small", "site_small_outlier",
                          "site_late_start_outlier"})
NON_DATA_CAUSE_KEYS = ("denom_n", "coverage_n", "knowledge_n", "rule_n",
                       "mapping_n", "model_n", "method_n", "population_n",
                       "visibility_n", "mode_n")
CAUSE_BY_KEY = {"denom_n": "denominator", "coverage_n": "coverage",
                "knowledge_n": "knowledge", "rule_n": "rule",
                "mapping_n": "mapping", "model_n": "model",
                "method_n": "method", "population_n": "population",
                "visibility_n": "visibility", "mode_n": "mode"}
CHANGE_KIND_FORBIDDEN_FOR_NON_DATA = ("new", "continued", "upgraded",
                                      "downgraded", "resolved", "reopened")
DEFAULT_REQUIRED_DOMAINS = {
    "project_risk_distribution": ["D01", "D02", "D03", "D04"],
    "cross_site_pattern": ["D09", "D01"],
    "project_time_trend": ["D09", "D10"],
    "project_safety_trend": ["D07", "D01"],
    "project_efficacy_trend": ["D06", "D01"],
}
DEN_KIND_ESTIMATE = {"subject_time": "incidence_rate",
                     "exposure_time": "exposure_adjusted_rate"}
AUDIT_CODES = frozenset({
    "legal_row_hash_bad", "legal_row_sd_mismatch", "scope_hash_bad",
    "mode_hash_bad", "source_hash_bad", "origin_hash_bad",
    "origin_refs_external", "origin_partition_bad", "origin_decision_bad",
    "source_pair_duplicate", "source_authority_bad", "den_refs_bad",
    "seg_recompute_bad", "ledger_bad", "cutoff_order_bad", "r2_prior_bad",
    "dl_eligible_bad", "dl_target_bad", "visibility_noncanonical",
    "visibility_algebra_bad", "visibility_pair_rebuild_bad",
    "visibility_pair_eligible_bad", "vis_decision_hash_bad", "q_covered_bad",
    "q_identity_bad", "q_partition_bad", "q_content_bad", "assignment_bad",
    "desc_hash_bad", "model_hash_bad",
    "audience_scan_hit",
})
IDENTITY_EXCLUDED_KEYS = frozenset({
    "idx", "case_id", "oracle_case_id", "fixture_id", "partition", "family",
    "required_sites", "vis_hidden_counts_bad", "site_ref_for_members",
    "authority_entry", "surface_alt",
} | AUDIT_CODES)

# ---------------------------------------------------------------------------
# Canonical JSON / hashing
# ---------------------------------------------------------------------------
def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {normalize_value(k): normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(normalize_value(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_hash(obj: dict[str, Any], own_hash_key: str = "content_hash") -> str:
    core = {key: item for key, item in obj.items() if key != own_hash_key}
    return sha256_text(canonical_json(core))


def normalize_contract(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


class VerifyError(Exception):
    pass


def _exact_keys(obj: Any, keys: list[str], label: str, problems: list[str]) -> None:
    if not isinstance(obj, dict):
        problems.append(f"{label}: not an object")
        return
    if sorted(obj.keys()) != sorted(keys):
        problems.append(f"{label}: exact-key mismatch "
                        f"got {sorted(obj.keys())} want {sorted(keys)}")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_all() -> dict[str, Any]:
    if not CONTRACT.exists() or not CATALOG.exists() or not ORACLE.exists() \
            or not REGISTRY.exists() or not QUOTA.exists() or not AUTHORITY.exists():
        raise VerifyError("one or more artifacts missing")
    return {
        "contract": CONTRACT.read_bytes(),
        "catalog": load_json(CATALOG),
        "oracle": load_json(ORACLE),
        "registry": load_json(REGISTRY),
        "quota": load_json(QUOTA),
        "authority": load_json(AUTHORITY),
    }


# ---------------------------------------------------------------------------
# Independent typed-input semantic audit (own recomputation; never reads the
# generators' audit)
# ---------------------------------------------------------------------------
_ENGINEERING_KEY_RE = re.compile(
    r"(?:pattern|rule|mode|window|revision|scope|policy|hash|ref|key|id)"
    r"\s*[:=＝]")
_FULLWIDTH_LATIN = frozenset(
    list(range(0xFF10, 0xFF1A)) + list(range(0xFF21, 0xFF3B))
    + list(range(0xFF41, 0xFF5B)))
_INVISIBLE_CHARS = frozenset("\u200b\u200c\u200d\u2060\ufeff")


def _audience_scan_hit(audience_text: dict[str, Any],
                       audience_contract: dict[str, Any]) -> bool:
    texts = [audience_text["basis_zh"], audience_text["finding_zh"],
             audience_text["action_zh"]]
    forbidden = [term.lower() for term in
                 audience_contract["forbidden_internal_terms"]]
    for text in texts:
        if not isinstance(text, str) or not text:
            return True
        if unicodedata.normalize("NFC", text) != text:
            return True
        if any(unicodedata.category(ch).startswith("C")
               or ch in _INVISIBLE_CHARS for ch in text):
            return True
        if any(ord(ch) in _FULLWIDTH_LATIN for ch in text):
            return True
        if _ENGINEERING_KEY_RE.search(text):
            return True
        low = text.lower()
        if any(term in low for term in forbidden):
            return True
    return False


def audit_case(case: dict[str, Any], authority_entry: dict[str, Any] | None = None) -> list[str]:
    """Own recomputation of every cross-object hash/binding/set relation."""
    typed = case["typed_input"]
    out: list[str] = []
    lr = typed["legal_matrix_row"]
    if lr["row_hash"] != sha256_text(canonical_json({
            "row_id": lr["row_id"], "signal_kind": lr["signal_kind"],
            "clinical_claim_token": lr["clinical_claim_token"],
            "d10_action": lr["d10_action"]})):
        out.append("legal_row_hash_bad")
    sd = typed["signal_definition"]
    if (lr["signal_kind"] != sd["signal_kind"]
            or lr["clinical_claim_token"] != sd["clinical_claim_token"]
            or lr["d10_action"] != sd["d10_action"]):
        out.append("legal_row_sd_mismatch")
    sb = typed["project_scope_binding"]
    if sb["scope_binding_hash"] != content_hash(sb, "scope_binding_hash"):
        out.append("scope_hash_bad")
    mode = typed["mode_contract"]
    if mode["mode_contract_content_hash"] != content_hash(
            mode, "mode_contract_content_hash"):
        out.append("mode_hash_bad")
    locator_ids = _locator_ids(typed)
    accepted_source_pairs = None
    if authority_entry is not None and authority_entry.get("source_revisions"):
        # Authority is a superset of the submitted envelope's admitted source
        # membership.  Submitted pairs must belong to accepted authority;
        # missing accepted pairs are valid unit-level subset semantics, while
        # extra/duplicate submitted pairs remain semantic attacks.
        accepted_source_pairs = {
            (pair["revision_id"], pair["content_hash"])
            for pair in authority_entry["source_revisions"]
        }
    seen_source_pairs: set[tuple[str, str]] = set()
    for pair in typed["source_revision_content_pairs"]:
        if pair["content_hash"] != sha256_text(canonical_json({
                "revision_id": pair["revision_id"],
                "source_locators": locator_ids})):
            out.append("source_hash_bad")
        pair_key = (pair["revision_id"], pair["content_hash"])
        if pair_key in seen_source_pairs:
            out.append("source_pair_duplicate")
        seen_source_pairs.add(pair_key)
        if accepted_source_pairs is not None and pair_key not in accepted_source_pairs:
            out.append("source_authority_bad")
    members = typed["members"]
    member_refs = [m["member_ref"] for m in members]
    mob = typed["measure_origin_binding"]
    if mob is not None:
        for key in ("verified_risk_refs", "distinct_risk_refs",
                    "ambiguous_risk_refs", "candidate_risk_refs"):
            for ref in mob[key]:
                if ref not in member_refs:
                    out.append("origin_refs_external")
            if mob[key] != sorted(set(mob[key])):
                out.append("origin_partition_bad")
        verified = set(mob["verified_risk_refs"])
        distinct = set(mob["distinct_risk_refs"])
        ambiguous = set(mob["ambiguous_risk_refs"])
        candidate = set(mob["candidate_risk_refs"])
        if candidate != verified | distinct | ambiguous or \
                verified & distinct or verified & ambiguous or \
                distinct & ambiguous:
            out.append("origin_partition_bad")
        if ambiguous:
            derived_origin = "ambiguous"
        elif verified and distinct:
            derived_origin = "mixed_verified_and_distinct"
        elif verified:
            derived_origin = "all_verified_same_origin"
        elif distinct:
            derived_origin = "all_distinct"
        elif mob["origin_decision"] == "wrong_scope":
            derived_origin = "wrong_scope"
        else:
            derived_origin = "not_evaluable"
        if mob["origin_decision"] != derived_origin:
            out.append("origin_decision_bad")
        if mob["candidate_partition_hash"] != sha256_text(
                canonical_json(sorted(candidate))):
            out.append("origin_hash_bad")
        if mob["binding_hash"] != content_hash(mob, "binding_hash"):
            out.append("origin_hash_bad")
    den = typed["denominator"]
    segments = typed["time_segments"]
    time_kind = den["denominator_kind"] in ("subject_time", "exposure_time")
    if not time_kind:
        if den["denominator_value"] >= 0 and \
                len(den["denominator_member_refs"]) != den["denominator_value"]:
            out.append("den_refs_bad")
    else:
        total = sum(seg["normalized_duration"] for seg in segments)
        if total != den["denominator_value"] or \
                len(den["denominator_member_refs"]) != den["denominator_value"]:
            out.append("den_refs_bad")
        if not {seg["member_ref"] for seg in segments} <= \
                set(den["denominator_member_refs"]):
            out.append("den_refs_bad")
    for seg in segments:
        if seg["raw_duration"] != seg["end_value"] - seg["start_value"] + 1 \
                or seg["normalized_duration"] != seg["raw_duration"]:
            out.append("seg_recompute_bad")
    nl = typed["numerator_ledger"]
    pattern_descendants = [d for m in members
                           if m["member_kind"] == "center_pattern"
                           for d in m["descendant_member_refs"]]
    indiv_refs = [m["member_ref"] for m in members
                  if m["member_kind"] == "individual_risk"
                  and m["member_ref"] not in pattern_descendants]
    indiv_subjects = {m["subject_stable_id"] for m in members
                      if m["member_kind"] == "individual_risk"
                      and m["subject_stable_id"]}
    if nl["individual_risk_count"] != len(set(indiv_refs)):
        out.append("ledger_bad")
    if nl["center_pattern_count"] != len({m["member_ref"] for m in members
                                          if m["member_kind"] == "center_pattern"}):
        out.append("ledger_bad")
    if nl["affected_subject_count"] != len(indiv_subjects):
        out.append("ledger_bad")
    if nl["numerator_member_count"] != len(set(member_refs)):
        out.append("ledger_bad")
    for m in members:
        if m["member_kind"] == "center_pattern" and \
                m["descendant_set_hash"] != sha256_text(canonical_json(
                    sorted(m["descendant_member_refs"]))):
            out.append("desc_hash_bad")
    ch = typed["change_decision"]
    if ch is not None:
        ca = ch["cutoff_advance"]
        derived_strict = bool(ca["strict_advance_predicate_passed"]
                              and ca["policy_semantic_hash_equal"]
                              and str(ca["current_boundary_value"])
                              > str(ca["prior_boundary_value"]))
        if ca["decision_state"] == "strict_advance" and not derived_strict:
            out.append("cutoff_order_bad")
        if ch["r2_action"] in ("continue", "update", "propose_close",
                               "reopen", "supersede") and \
                ch["r2_prior_ref_or_none"] is None:
            out.append("r2_prior_bad")
        if ch["carry_forward_state"] == "active" and \
                ch["r2_prior_ref_or_none"] is None:
            out.append("r2_prior_bad")
    vis = typed["visibility_decision"]
    if vis["decision_id"] != content_hash(vis, "decision_id"):
        out.append("vis_decision_hash_bad")
    evaluation_refs = vis["evaluation_member_refs"]
    projectable_refs = vis["projectable_member_refs"]
    hidden_refs = vis["hidden_member_refs"]
    if any(values != sorted(set(values)) for values in
           (evaluation_refs, projectable_refs, hidden_refs,
            vis["deep_link_eligible_member_refs"],
            vis["evaluation_site_refs"], vis["projectable_site_refs"],
            vis["hidden_site_refs"], vis["deep_link_eligible_site_refs"])):
        out.append("visibility_noncanonical")
    projectable = set(projectable_refs)
    if set(projectable_refs) | set(hidden_refs) != set(evaluation_refs) or \
            set(projectable_refs) & set(hidden_refs):
        out.append("visibility_algebra_bad")
    if vis["visible_n"] != len(set(projectable_refs)) or \
            vis["eligible_n"] != len(set(evaluation_refs)) or \
            vis["hidden_member_count"] != len(set(hidden_refs)) or \
            vis["hidden_site_count"] != len(set(vis["hidden_site_refs"])):
        out.append("visibility_algebra_bad")
    if not set(vis["deep_link_eligible_member_refs"]) <= projectable:
        out.append("dl_eligible_bad")
    proj_sites = set(vis["projectable_site_refs"])
    member_by_ref = {m["member_ref"]: m for m in members}
    pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in projectable_refs if ref in member_by_ref
        and member_by_ref[ref]["subject_stable_id"]
        and member_by_ref[ref]["site_stable_id"] in proj_sites})
    eligible_pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in vis["deep_link_eligible_member_refs"]
        if ref in member_by_ref and member_by_ref[ref]["subject_stable_id"]
        and member_by_ref[ref]["site_stable_id"] in proj_sites})
    submitted_pairs = [tuple(pair) for pair in
                       vis["projectable_subject_site_pairs"]]
    submitted_eligible_pairs = [tuple(pair) for pair in
                                vis["deep_link_eligible_subject_site_pairs"]]
    if submitted_pairs != sorted(set(submitted_pairs)) or \
            submitted_eligible_pairs != sorted(set(submitted_eligible_pairs)):
        out.append("visibility_noncanonical")
    if submitted_pairs != pairs:
        out.append("visibility_pair_rebuild_bad")
    if set(submitted_eligible_pairs) - set(pairs) or \
            set(submitted_eligible_pairs) != set(eligible_pairs):
        out.append("visibility_pair_eligible_bad")
    if not set(vis["deep_link_eligible_site_refs"]) <= proj_sites:
        out.append("dl_eligible_bad")
    for dl in typed["deep_links"]:
        if dl["visibility_decision_ref"] != vis["decision_id"]:
            out.append("dl_target_bad")
        if dl["target_kind"] == "member":
            ref = dl["member_object_ref"]
            member = member_by_ref.get(ref)
            if ref not in set(vis["deep_link_eligible_member_refs"]) or \
                    member is None or dl["subject_ref"] != member["subject_stable_id"] \
                    or dl["site_ref"] != member["site_stable_id"]:
                out.append("dl_target_bad")
        elif dl["target_kind"] == "site":
            if dl["site_ref"] not in proj_sites:
                out.append("dl_target_bad")
            if dl["subject_ref"] is not None or dl["member_object_ref"] is not None:
                out.append("dl_target_bad")
        else:
            if (dl["subject_ref"], dl["site_ref"]) not in \
                    set(submitted_eligible_pairs):
                out.append("dl_target_bad")
            if dl["member_object_ref"] is not None:
                out.append("dl_target_bad")
    qd = typed["query_decision"]
    covered_refs = qd["covered_member_refs"]
    uncovered_refs = qd["uncovered_member_refs"]
    if any(ref not in member_refs for ref in covered_refs):
        out.append("q_covered_bad")
    if any(ref not in member_refs for ref in uncovered_refs):
        out.append("q_covered_bad")
    if covered_refs != sorted(set(covered_refs)) or \
            uncovered_refs != sorted(set(uncovered_refs)):
        out.append("q_identity_bad")
    if (set(covered_refs) & set(uncovered_refs) or \
            set(covered_refs) | set(uncovered_refs) != set(member_refs)):
        out.append("q_partition_bad")
    identities = qd["member_query_content_identities"]
    if len(identities) != len(covered_refs) or \
            len(set(identities)) != len(identities):
        out.append("q_identity_bad")
    elif any(identity != sha256_text(canonical_json({"member_ref": ref}))
             for identity, ref in zip(identities, covered_refs)):
        out.append("q_identity_bad")
    if qd["unit_member_set_hash"] != sha256_text(
            canonical_json(sorted(set(member_refs)))):
        out.append("q_partition_bad")
    proof = {
        "unit_member_refs": sorted(set(member_refs)),
        "covered_member_refs": covered_refs,
        "uncovered_member_refs": uncovered_refs,
        "member_query_content_identities": identities,
    }
    if qd["coverage_proof_hash"] != sha256_text(canonical_json(proof)):
        out.append("q_partition_bad")
    if qd["query_content_hash"] != content_hash(qd, "query_content_hash"):
        out.append("q_content_bad")
    model = typed["model_evidence"]
    if model is not None:
        expected_leaf = ("model_candidate_only"
                         if model["role"] == "candidate_explanation"
                         else "counterevidence_suggestion_only")
        if model["permitted_leaf"] != expected_leaf or \
                (model["ensemble_size"] == 1
                 and model["permitted_leaf"] != "model_candidate_only"):
            out.append("model_hash_bad")
        binding_core = {key: model[key] for key in (
            "model_evidence_id", "role", "evaluation_content_identity",
            "input_content_hash", "source_revision_content_pairs", "source_refs",
            "model_id", "model_version", "independent_context_hash",
            "ensemble_id", "ensemble_size", "member_analysis_refs",
            "permitted_leaf", "member_analysis_ref_set_hash",
            "output_identity", "adjudication_state")}
        if model["model_binding_hash"] != sha256_text(
                canonical_json(binding_core)):
            out.append("model_hash_bad")
        if model["member_analysis_refs"] != sorted(set(model["member_analysis_refs"])) or \
                model["member_analysis_ref_set_hash"] != sha256_text(
                    canonical_json(sorted(set(model["member_analysis_refs"])) )):
            out.append("model_hash_bad")
        if model["output_hash"] != sha256_text(canonical_json({
                "output_identity": model["output_identity"],
                "model_binding_hash": model["model_binding_hash"],
                "permitted_leaf": model["permitted_leaf"],
                "adjudication_state": model["adjudication_state"],
        })):
            out.append("model_hash_bad")
    ec = typed["efficacy_context"]
    if ec is not None and \
            ec["treatment_assignment_exposure_identity_ref"] is not None:
        authority = ec["treatment_role_authority_ref"]
        if authority is None:
            out.append("assignment_bad")
        recomputed = sha256_text(canonical_json({
            "authority": authority, "project": typed["project_ref"],
            "run": typed["run_ref"]}))
        if ec["treatment_assignment_exposure_identity_ref"] != recomputed:
            out.append("assignment_bad")
        if ec["treatment_assignment_mapping_hash"] != recomputed:
            out.append("assignment_bad")
    if _audience_scan_hit(typed["audience_text"], case["audience_contract"]):
        out.append("audience_scan_hit")
    return out


# ---------------------------------------------------------------------------
# Typed-fact projection (independent; key-for-key parity with the oracle's f)
# ---------------------------------------------------------------------------
def project_facts(case: dict[str, Any],
                  authority_entry: dict[str, Any] | None = None) -> dict[str, Any]:
    t = case["typed_input"]
    sd = t["signal_definition"]
    lr = t["legal_matrix_row"]
    es = t["expected_set"]
    den = t["denominator"]
    vis = t["visibility_decision"]
    qd = t["query_decision"]
    at = t["audience_text"]
    rh = t["rule_hit"]
    el = t["evaluation_limits"]
    nl = t["numerator_ledger"]
    members = t["members"]
    member_refs = [m["member_ref"] for m in members]
    kinds = [m["member_kind"] for m in members]
    accepted_source_pairs = None
    if authority_entry is not None and authority_entry.get("source_revisions"):
        accepted_source_pairs = {
            (pair["revision_id"], pair["content_hash"])
            for pair in authority_entry["source_revisions"]
        }
    submitted_pairs = t["source_revision_content_pairs"]
    submitted_pair_keys = {
        (pair["revision_id"], pair["content_hash"])
        for pair in submitted_pairs
    }
    envelope_ok = (accepted_source_pairs is None or bool(submitted_pairs)) and (
        accepted_source_pairs is None
        or submitted_pair_keys <= accepted_source_pairs)
    f: dict[str, Any] = {
        "idx": int(case["case_id"].rsplit("-", 1)[-1]),
        "case_id": case["case_id"],
        "oracle_case_id": case["oracle_case_id"],
        "fixture_id": case["fixture_id"],
        "partition": None,
        "family": None,
        "kind": sd["signal_kind"],
        "token": sd["clinical_claim_token"],
        "owner": sd["d10_action"],
        "legal_match": (
            lr["signal_kind"] == sd["signal_kind"]
            and lr["clinical_claim_token"] == sd["clinical_claim_token"]
            and lr["d10_action"] == sd["d10_action"]),
        "scope_eq": t["project_scope_binding"]["scope_equality_decision"],
        "envelope_ok": envelope_ok,
        "identity_ok": t["site_ledger"]["identity_state"] == "stable",
        "es_state": es["expected_set_state"],
        "gate_kind": es["admission_gate"]["gate_kind"] if es["admission_gate"]
        else None,
        "gate_reasons": list(es["admission_gate"]["reason_codes"])
        if es["admission_gate"] else [],
        "cov": {c["producer_domain"]: [c["l0_status"],
                                       c["l1_medical_completeness_state"]]
                for c in t["coverage"]},
        "required_domains": list(sd["required_producer_domains"]),
        "den_kind": den["denominator_kind"],
        "den_value": den["denominator_value"],
        "den_state": den["denominator_state"],
        "den_excl": list(den["exclusion_reason_codes"]),
        "den_tamper": den["denominator_value"] != den["recomputed_value"],
        "seg_tamper": any(s["normalized_duration"] != s["raw_duration"]
                          for s in t["time_segments"]),
        "seg_overlap": any(s["overlap_resolution_ref"] is not None
                           for s in t["time_segments"]),
        "pop_present": t["analysis_population"]["present"],
        "opp": None,
        "num_subject": nl["affected_subject_count"],
        "num_event": nl["event_or_outcome_count"],
        "num_site": nl["affected_site_count"],
        "individual": nl["individual_risk_count"],
        "pattern": nl["center_pattern_count"],
        "safety_present": "safety_measure" in kinds,
        "efficacy_present": "efficacy_measure" in kinds,
        "gap_present": "accepted_gap" in kinds,
        "member_scope_bad": any(m["member_scope_state"] != "in_scope"
                                for m in members),
        "member_scope_kind": next(
            (m["member_scope_state"] for m in members
             if m["member_scope_state"] != "in_scope"), None),
        "dup_member_ref": len(set(member_refs)) != len(member_refs),
        "desc_in_numerator": False,
        "dup_locator": len({e["locator_id"] for e in t["evidence_refs"]})
        != len(t["evidence_refs"]),
        "dup_revision": False,
        "origin_decision": None,
        "origin_plane_duplicate": False,
        "excluded_in_numerator": False,
        "member_producer_d06": any(
            m["member_kind"] == "center_pattern"
            and m["producer_domain"] == "D06" for m in members),
        "safety_missing": [],
        "efficacy_missing": [],
        "treatment_role_required": False,
        "assignment_present": False,
        "model_role": None,
        "model_ensemble": None,
        "comp_state": t["comparison_gate"]["comparison_state"],
        "comp_reasons": [code for code in t["comparison_gate"]["reason_codes"]
                         if not code.startswith("comparison_")
                         and not code.startswith("window_pair_")],
        "eligible_sites": t["comparison_gate"]["observed_eligible_site_count"],
        "excluded_sites": len(t["comparison_gate"]["excluded_site_refs"]),
        "site_activation": t["site_ledger"]["site_activation_state"],
        "pair_state": t["window_pair_gate"]["pair_state"],
        "wins": len(t["analysis_windows"]),
        "unique_windows": len({w["analysis_window_stable_id"]
                               for w in t["analysis_windows"]}),
        "segments": len(t["time_segments"]),
        "change": None,
        "vis_hidden_members": vis["hidden_member_count"],
        "vis_hidden_sites": vis["hidden_site_count"],
        "rate_state": vis["rate_projection_state"],
        "blind_status": vis["blind_status"],
        "hidden_omission": vis["hidden_set_omitted"],
        "dl_violation": vis["deep_link_eligible_violation"],
        "blind_inference": vis["treatment_inference_attempt"],
        "dl_n": len(t["deep_links"]),
        "locator_missing": any(
            m["locator_resolution_state"] != "locatable" for m in members),
        "q_decision": qd["decision"],
        "q_uncovered": len(qd["uncovered_member_refs"]),
        "q_covered": len(qd["covered_member_refs"]),
        "q_fanout": qd["max_query_member_fanout"],
        "q_unlistable": qd["member_unlistable"],
        "q_pd": qd["pd_wording_state"],
        "q_ids_mismatch": (len(qd["member_query_content_identities"])
                           != len(qd["covered_member_refs"])),
        "q_duplicate": qd["duplicate_query_attempt"],
        "injection": at["engineering_reference_attempt"],
        "injection_blocked": at["injection_blocked"],
        "rehash": qd["unit_member_set_hash"] != sha256_text(
            canonical_json(sorted(set(member_refs)))),
        "hotspot": t["hotspot"] is not None,
        "hotspot_hidden": bool(t["hotspot"] and t["hotspot"]["hidden_in_display"]),
        "count_layers": list(t["count_layers"]["layers_in_common_numerator"]),
        "small": el["small_sample"],
        "limited": el["limited_evidence"],
        "limited_reason": el["limited_reason"],
        "design_applicable": t["mode_contract"]["design_applicable_state"],
        "estimate": None,
        "hit": rh["hit_state"],
        "sources": list(rh["evidence_sources"]),
        "ce_declared": len(rh["counterevidence_declared_refs"]),
        "ce_matched": len(rh["counterevidence_matched_refs"]),
        "surface_alt": t["anti_overfit_variant"] is not None and
        t["anti_overfit_variant"]["variant_id"] == 2,
        "project_ref": t["project_ref"],
    }
    opp = t["opportunity"]
    if opp is not None:
        f["opp"] = {"expected": opp["expected_opportunity_count"],
                    "observed": opp["observed_opportunity_count"],
                    "provenance": opp["opportunity_provenance"],
                    "complete": opp["complete"]}
    pattern_descendants = [d for m in members
                           if m["member_kind"] == "center_pattern"
                           for d in m["descendant_member_refs"]]
    f["desc_in_numerator"] = any(ref in pattern_descendants
                                 for ref in member_refs)
    rev_ids: set[str] = set()
    for pair in t["source_revision_content_pairs"]:
        if pair["revision_id"] in rev_ids:
            f["dup_revision"] = True
        rev_ids.add(pair["revision_id"])
    mob = t["measure_origin_binding"]
    if mob is not None:
        f["origin_decision"] = mob["origin_decision"]
        f["origin_plane_duplicate"] = mob["numerator_plane_state"] == "duplicate"
    excluded_subjects = set(den["excluded_member_refs"])
    member_subjects = {m["subject_stable_id"] for m in members
                       if m["subject_stable_id"]}
    f["excluded_in_numerator"] = bool(excluded_subjects & member_subjects)
    sc = t["safety_context"]
    if sc is not None:
        f["safety_missing"] = sorted(
            key for key, ref in (
                ("exposure", sc["exposure_definition_ref"]),
                ("coding", sc["coding_dictionary_ref"]),
                ("severity", sc["severity_scale_ref"]),
                ("risk_window", sc["risk_window_ref"]))
            if ref is None)
    ec = t["efficacy_context"]
    if ec is not None:
        f["efficacy_missing"] = sorted(
            key for key, ref in (
                ("endpoint", ec["endpoint_definition_ref"]),
                ("estimand", ec["estimand_ref"]),
                ("missing", ec["missing_data_rule_ref"]),
                ("intercurrent", ec["intercurrent_event_rule_ref"]))
            if ref is None)
        f["treatment_role_required"] = ec["treatment_role_required"]
        f["assignment_present"] = \
            ec["treatment_assignment_exposure_identity_ref"] is not None
        f["estimate"] = ec["estimate_kind"]
    me = t["model_evidence"]
    if me is not None:
        f["model_role"] = me["role"]
        f["model_ensemble"] = me["ensemble_size"]
    ch = t["change_decision"]
    if ch is not None:
        ca = ch["cutoff_advance"]
        f["change"] = {
            "basis": ch["execution_basis"],
            "comparison_state": ch["comparison_state"],
            "prior": ch["prior_snapshot_ref_or_none"] is not None,
            "data_n": len(ch["data_change_refs"]),
            "denom_n": len(ch["denominator_change_refs"]),
            "coverage_n": len(ch["coverage_change_refs"]),
            "knowledge_n": len(ch["knowledge_change_refs"]),
            "rule_n": len(ch["rule_change_refs"]),
            "mapping_n": len(ch["mapping_change_refs"]),
            "model_n": len(ch["model_change_refs"]),
            "method_n": len(ch["method_change_refs"]),
            "population_n": len(ch["population_change_refs"]),
            "visibility_n": len(ch["visibility_change_refs"]),
            "mode_n": len(ch["mode_change_refs"]),
            "cutoff_state": ca["decision_state"],
            "cutoff_predicate": ca["strict_advance_predicate_passed"],
            "cutoff_policy_equal": ca["policy_semantic_hash_equal"],
            "prior_boundary": ca["prior_boundary_value"],
            "current_boundary": ca["current_boundary_value"],
            "data_kind": ch["data_change_kind"],
            "claimed_kind": ch["claimed_clinical_change_kind"],
            "claimed_cause": ch["claimed_primary_change_cause"],
            "claimed_cutoff": ch["claimed_cutoff_state"],
            "r2_action": ch["r2_action"],
            "r2_prior": ch["r2_prior_ref_or_none"] is not None,
            "r2_lineage": ch["lineage_relation"],
            "carry_forward": ch["carry_forward_state"] == "active",
        }
    evaluation = set(vis["evaluation_member_refs"])
    projectable = set(vis["projectable_member_refs"])
    hidden = set(vis["hidden_member_refs"])
    f["vis_algebra_ok"] = bool(
        projectable | hidden == evaluation
        and not (projectable & hidden)
        and hidden <= evaluation
        and vis["visible_n"] == len(vis["projectable_member_refs"])
        and vis["hidden_member_count"] == len(vis["hidden_member_refs"])
        and vis["hidden_site_count"] == len(vis["hidden_site_refs"])
        and vis["decision_id"] == content_hash(vis, "decision_id"))
    f["vis_decision_hash_bad"] = vis["decision_id"] != content_hash(
        vis, "decision_id")
    f["vis_hidden_dropped"] = set(vis["evaluation_member_refs"]) != set(
        member_refs)
    f["vis_hidden_counts_bad"] = vis["hidden_member_count"] != len(
        vis["hidden_member_refs"])
    unit_member_refs = set(member_refs)
    f["q_set_violation"] = bool(
        set(qd["covered_member_refs"]) | set(qd["uncovered_member_refs"])
        != unit_member_refs
        or set(qd["covered_member_refs"]) & set(qd["uncovered_member_refs"])
        or any(ref not in unit_member_refs
               for ref in qd["covered_member_refs"] +
               qd["uncovered_member_refs"]))
    f["count_mixed"] = len(set(f["count_layers"])) > 1
    f["replay"] = bool(
        f["change"] and f["change"]["basis"] == "full"
        and f["change"]["cutoff_state"] == "same_window"
        and f["change"]["claimed_cutoff"] is None)
    audit_codes = set(audit_case(case, authority_entry))
    for code in AUDIT_CODES:
        f[code] = code in audit_codes
    f["authority_entry"] = None  # filled by authority binding below
    return f


# ---------------------------------------------------------------------------
# Change derivation (contract section 14)
# ---------------------------------------------------------------------------
def derive_change(ch: dict[str, Any] | None) -> tuple[str, str | None, str, bool]:
    if ch is None or ch.get("basis") == "full":
        return "initial_current", None, "initial_full_snapshot", False
    if ch.get("comparison_state") == "not_comparable":
        return "not_comparable", None, "not_comparable", True
    non_data = [key for key in NON_DATA_CAUSE_KEYS if ch.get(key, 0) > 0]
    if non_data:
        causes = [CAUSE_BY_KEY[key] for key in non_data]
        cause = causes[0] if len(causes) == 1 else "mixed"
        if "method" in causes or "population" in causes:
            lineage = "superseded_by_method_or_population_change"
        elif "rule" in causes or "mapping" in causes or "model" in causes:
            lineage = "superseded_by_rule_or_mapping_change"
        elif "knowledge" in causes:
            lineage = "superseded_by_knowledge_change"
        elif "mode" in causes:
            lineage = "superseded_by_mode_change"
        elif "visibility" in causes:
            lineage = "superseded_by_visibility_change"
        elif "coverage" in causes:
            lineage = "coverage_regressed"
        else:
            lineage = "not_comparable"
        return "not_comparable", cause, lineage, True
    if (ch.get("cutoff_state") == "strict_advance"
            and ch.get("cutoff_predicate") and ch.get("cutoff_policy_equal")
            and ch.get("prior")):
        lineage = "continued_from_cutoff_advance"
    else:
        lineage = "continued_from_data_revision"
    return ch.get("data_kind") or "continued", "data", lineage, False


# ---------------------------------------------------------------------------
# Decision rule table (independent implementation of contract sections
# 2.1/3.3/6/7/8/9/10/13/14)
# ---------------------------------------------------------------------------
def derive_disposition(f: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    token, owner = f["token"], f["owner"]
    kind = f["kind"]
    if token == "unresolved":
        return "routing_gate", "claim_token_unresolved", {"zero_unit": True}
    if owner == "consume_only":
        if token not in CONSUME_ONLY_TOKENS:
            return "integrity_gate", "legal_row_mismatch", {"zero_unit": True}
        return "routing_gate", "consume_only_no_medical_unit", {"zero_unit": True}
    if owner == "handoff_only":
        if token not in HANDOFF_ONLY_TOKENS:
            return "integrity_gate", "legal_row_mismatch", {"zero_unit": True}
        return "handoff_gate", "handoff_only_no_medical_unit", {"zero_unit": True}
    if owner == "routing_gate":
        return "routing_gate", "routing_gate_no_medical_unit", {"zero_unit": True}
    if token not in OWNED_TOKENS:
        return "integrity_gate", "owner_route_unauthorized", {"zero_unit": True}
    if not f["legal_match"]:
        return "integrity_gate", "legal_matrix_row_mismatch", {"zero_unit": True}
    if f["legal_row_hash_bad"]:
        return "integrity_gate", "legal_matrix_row_tamper", {"zero_unit": True}
    if f["scope_eq"] != "exact_match":
        return "global_gate", "scope_binding_mismatch", {"zero_unit": True}
    if f["scope_hash_bad"]:
        return "integrity_gate", "scope_binding_tamper", {"zero_unit": True}
    if f["source_authority_bad"]:
        return "integrity_gate", "source_authority_mismatch", {"zero_unit": True}
    if not f["envelope_ok"]:
        return "global_gate", "envelope_source_revision_mismatch", {"zero_unit": True}
    if not f["identity_ok"]:
        return "global_gate", "identity_state_unstable", {"zero_unit": True}
    if f["mode_hash_bad"]:
        return "integrity_gate", "mode_contract_tamper", {"zero_unit": True}
    if f["es_state"] == "global_admission_failed":
        return "global_gate", "global_admission_failed", {"zero_unit": True}
    if f["es_state"] in ("routed_consume_only", "routing_gate_unresolved"):
        return "routing_gate", f"expected_set_{f['es_state']}", {"zero_unit": True}
    if f["es_state"] == "control_plane_gate":
        if f["gate_kind"] == "comparison_set_gate":
            return "comparison_set_gate", "control_plane_comparison_gate", \
                {"zero_unit": True}
        return "window_pair_gate", "control_plane_window_pair_gate", \
            {"zero_unit": True}

    ch = f["change"]
    derived = derive_change(ch) if ch else None
    derived_kind = derived[0] if derived else "initial_current"
    derived_cause = derived[1] if derived else None
    derived_lineage = derived[2] if derived else "initial_full_snapshot"
    analysis_only = derived[3] if derived else False

    if (ch and ch.get("claimed_cutoff") == "strict_advance" and
            ch.get("cutoff_state") in ("same_window", "policy_changed")) or \
            f["cutoff_order_bad"]:
        return "integrity_gate", "cutoff_advance_tamper", {"zero_unit": True}
    if ch and ch.get("r2_lineage") == "continued_from_cutoff_advance" and \
            ch.get("cutoff_state") == "not_evaluable":
        return "not_evaluable", "cutoff_not_evaluable", {}
    if (ch and ch.get("r2_action") == "create" and ch.get("r2_prior")) or \
            f["r2_prior_bad"]:
        return "integrity_gate", "r2_wrong_prior", {"zero_unit": True}
    if ch and ch.get("r2_action") == "create" and \
            ch.get("r2_lineage") not in ALLOWED_CREATE_LINEAGES:
        return "integrity_gate", "r2_wrong_lineage", {"zero_unit": True}
    if ch and ch.get("r2_action") == "create" and analysis_only:
        return "integrity_gate", "r2_create_non_data_mixed", {"zero_unit": True}
    if ch and ch.get("r2_lineage") and derived and \
            ch.get("r2_lineage") != derived_lineage:
        return "integrity_gate", "r2_wrong_lineage", {"zero_unit": True}
    if ch and ch.get("claimed_kind") and derived and \
            ch["claimed_kind"] != derived_kind:
        return "integrity_gate", "fake_change_claim", {"zero_unit": True}
    if ch and ch.get("claimed_cause") and derived and \
            ch["claimed_cause"] != derived_cause:
        return "integrity_gate", "fake_change_cause", {"zero_unit": True}
    if f["den_tamper"]:
        return "integrity_gate", "denominator_tamper", {"zero_unit": True}
    if f["den_refs_bad"]:
        return "integrity_gate", "denominator_recompute_mismatch", {"zero_unit": True}
    if f["seg_tamper"] or f["seg_recompute_bad"]:
        return "integrity_gate", "time_segment_tamper", {"zero_unit": True}
    if f["seg_overlap"]:
        return "integrity_gate", "time_segment_overlap", {"zero_unit": True}
    if f["count_mixed"]:
        return "integrity_gate", "cross_layer_count_mixing", {"zero_unit": True}
    if f["desc_in_numerator"]:
        return "integrity_gate", "d09_parent_descendant_duplication", \
            {"zero_unit": True}
    if f["ledger_bad"]:
        return "integrity_gate", "numerator_ledger_mismatch", {"zero_unit": True}
    if f["origin_decision"] == "all_verified_same_origin" and \
            f["origin_plane_duplicate"]:
        return "integrity_gate", "same_origin_double_count", {"zero_unit": True}
    if f["origin_refs_external"] or f["origin_hash_bad"] or \
            f["origin_partition_bad"] or f["origin_decision_bad"]:
        return "integrity_gate", "measure_origin_binding_tamper", {"zero_unit": True}
    if f["member_producer_d06"]:
        return "integrity_gate", "d06_efficacy_not_d09_pattern", {"zero_unit": True}
    if f["excluded_in_numerator"]:
        return "integrity_gate", "excluded_member_counted", {"zero_unit": True}
    if f["dup_member_ref"]:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f["dup_locator"]:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f["dup_revision"] or f["source_pair_duplicate"]:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f["source_hash_bad"]:
        return "integrity_gate", "source_revision_hash_tamper", {"zero_unit": True}
    if f["desc_hash_bad"]:
        return "integrity_gate", "descendant_set_tamper", {"zero_unit": True}
    if f["den_value"] < 0:
        return "integrity_gate", "invalid_numeric", {"zero_unit": True}
    if f["rehash"]:
        return "integrity_gate", "rehash_bypass_evaluator_identity", \
            {"zero_unit": True}
    if f["vis_hidden_dropped"]:
        return "integrity_gate", "hidden_member_dropped", {"zero_unit": True}
    if f["hidden_omission"]:
        return "integrity_gate", "hidden_set_omitted", {"zero_unit": True}
    if f["dl_violation"] or f["dl_eligible_bad"] or \
            f["visibility_pair_eligible_bad"]:
        return "integrity_gate", "deep_link_eligible_violation", {"zero_unit": True}
    if f["dl_target_bad"]:
        return "integrity_gate", "deep_link_target_tamper", {"zero_unit": True}
    if not f["vis_algebra_ok"] or f["vis_decision_hash_bad"] or \
            f["visibility_noncanonical"] or f["visibility_algebra_bad"] or \
            f["visibility_pair_rebuild_bad"]:
        return "integrity_gate", "visibility_algebra", {"zero_unit": True}
    if f["blind_inference"]:
        return "integrity_gate", "blind_treatment_inference", {"zero_unit": True}
    if not f["injection_blocked"] and \
            (f["injection"] or f["audience_scan_hit"]):
        return "integrity_gate", "audience_injection_blocked", {"zero_unit": True}
    if f["hotspot_hidden"]:
        return "integrity_gate", "hotspot_hidden", {"zero_unit": True}
    if f["q_set_violation"] or f["q_covered_bad"] or f["q_partition_bad"]:
        return "integrity_gate", "query_redundancy_tamper", {"zero_unit": True}
    if f["q_ids_mismatch"] or f["q_identity_bad"]:
        return "integrity_gate", "query_source_tamper", {"zero_unit": True}
    if f["q_content_bad"]:
        return "integrity_gate", "query_source_tamper", {"zero_unit": True}
    if f["q_duplicate"]:
        return "integrity_gate", "duplicate_query_per_unit", {"zero_unit": True}
    if f["assignment_bad"]:
        return "integrity_gate", "treatment_assignment_tamper", {"zero_unit": True}
    if f["model_hash_bad"]:
        return "integrity_gate", "model_evidence_tamper", {"zero_unit": True}
    if f["member_scope_bad"]:
        return "not_evaluable", "member_resolution_failed", {}

    for domain in f["required_domains"]:
        l0, l1 = f["cov"].get(domain, ("covered", "complete"))
        if l0 != "covered" or l1 != "complete":
            return "not_evaluable", "required_l1_hole", {}
    if f["den_state"] == "unclosed":
        return "not_evaluable", "denominator_unclosed", {}
    if f["den_state"] == "closed_zero":
        if f["design_applicable"] == "not_applicable":
            return "not_applicable", "design_not_applicable", {}
        return "not_evaluable", "zero_denominator_not_negative", {}
    if not f["pop_present"]:
        return "not_evaluable", "analysis_population_missing", {}
    if f.get("opp") and not f["opp"]["complete"]:
        return "not_evaluable", "opportunity_ledger_incomplete", {}
    if f.get("opp") and f["opp"]["provenance"] == "raw_only":
        return "not_evaluable", "gap_only_provenance", {}
    if f["origin_decision"] in ("ambiguous", "wrong_scope", "not_evaluable"):
        return "not_evaluable", f"origin_{f['origin_decision']}", {}
    if kind == "project_safety_trend" and f["safety_missing"]:
        return "not_evaluable", "safety_context_incomplete", {}
    if kind == "project_efficacy_trend":
        if f["efficacy_missing"]:
            return "not_evaluable", "efficacy_context_incomplete", {}
        if f["treatment_role_required"] and not f["assignment_present"]:
            return "not_evaluable", "treatment_assignment_missing", {}
    for code in f["comp_reasons"]:
        if code in NOT_EVALUABLE_COMP_CODES:
            return "not_evaluable", code, {}
    if f["design_applicable"] == "unresolved":
        return "not_evaluable", "authority_unresolvable", {}
    if f["design_applicable"] == "not_applicable":
        return "not_applicable", "design_not_applicable", {}

    if kind == "cross_site_pattern" and f["comp_state"] != "ready":
        return "comparison_set_gate", f"comparison_{f['comp_state']}", \
            {"zero_unit": True}
    if kind in ("project_time_trend", "project_safety_trend",
                "project_efficacy_trend") and f["pair_state"] != "ready":
        return "window_pair_gate", f"window_pair_{f['pair_state']}", \
            {"zero_unit": True}

    for code in f["comp_reasons"]:
        if code in BOUNDARY_COMP_CODES:
            return "boundary", code, {}
    if f["origin_decision"] == "mixed_verified_and_distinct":
        return "boundary", "mixed_origin_separate_leaves", {}
    typed_evidence = any(source in ("typed_member", "verified_measure")
                         for source in f["sources"])
    if f["hit"] != "not_applicable" and not typed_evidence:
        return "boundary", "evidence_not_typed_positive_forbidden", {}
    if f["ce_declared"] > 0 and f["ce_matched"] >= f["ce_declared"]:
        return "negative", "counterevidence_explains", {}
    if f["small"]:
        return "boundary", "small_sample", {}
    if f["limited"]:
        return "boundary", f["limited_reason"] or "limited_evidence", {}
    if 0 < f["ce_matched"] < f["ce_declared"]:
        return "boundary", "counterevidence_partial", {}
    if f["locator_missing"]:
        return "boundary", "deep_link_deficient", {}
    if f["hit"] == "no_hit":
        return "negative", "no_hit_complete", {}
    if f["hit"] == "not_applicable":
        return "not_applicable", "rule_not_applicable", {}
    return "positive", "rule_hit_counterevidence_insufficient", {}


# ---------------------------------------------------------------------------
# Leaf builders (own implementations; identity values come from the ACCEPTED
# fixture authority entry, never from case-id conventions)
# ---------------------------------------------------------------------------
def _estimate_kind(f: dict[str, Any]) -> str:
    if f.get("estimate"):
        return f["estimate"]
    return DEN_KIND_ESTIMATE.get(f["den_kind"], "proportion")


def _query_count(f: dict[str, Any], disposition: str) -> int:
    if disposition != "positive":
        return 0
    if f["q_decision"] != "project_delta_present":
        return 0
    if f["q_uncovered"] <= 0 or f["q_unlistable"]:
        return 0
    if f["q_uncovered"] > f["q_fanout"]:
        return 0
    if (f["injection"] or f["audience_scan_hit"]) and f["injection_blocked"]:
        return 0
    return 1


def _unit_member_count(f: dict[str, Any]) -> int:
    return (f["individual"] + f["pattern"]
            + (1 if f.get("gap_present") else 0)
            + (1 if f.get("safety_present") else 0)
            + (1 if f.get("efficacy_present") else 0)
            + (1 if f.get("desc_in_numerator") else 0))


def _stable_core_ref(f: dict[str, Any]) -> str:
    entry = f["authority_entry"]
    first_window = entry["analysis_windows"][0]["analysis_window_stable_id"]
    return "|".join([entry["project_ref"],
                     entry["signal_definition"]["signal_definition_id"],
                     first_window,
                     entry["stratum"]["stratum_contract_id"],
                     entry["stratum"]["stratum_key"],
                     entry["comparison_reference_stable_id"]])


def _gate_leaf_kind(disposition_or_gate: str) -> str:
    return {
        "comparison_set_gate": "control_plane_comparison_gate",
        "window_pair_gate": "control_plane_window_pair_gate",
        "global_gate": "global_integrity_gate",
        "integrity_gate": "global_integrity_gate",
        "routing_gate": "routing_gate",
        "handoff_gate": "handoff_gate",
    }[disposition_or_gate]


_ZERO_LEAF_COUNT_KEYS = (
    "numerator_member_count", "numerator_individual_risk_count",
    "numerator_affected_subject_count", "numerator_event_or_outcome_count",
    "numerator_center_pattern_count", "numerator_affected_site_count",
    "project_signal_count", "clue_count", "query_count",
    "risk_handoff_count", "hidden_member_count", "hidden_site_count",
    "deep_link_target_count", "counterevidence_rule_matches")


def build_expected_leaf_set(f: dict[str, Any], disposition_or_gate: str,
                            reason: str, extra: dict[str, Any]) -> list[dict[str, Any]]:
    if extra.get("zero_unit") or disposition_or_gate in GATE_DISPOSITIONS:
        leaf: dict[str, Any] = {key: None for key in LEAF_KEYS}
        leaf["leaf_kind"] = _gate_leaf_kind(disposition_or_gate)
        leaf["signal_kind"] = f["kind"]
        leaf["gate_kind"] = disposition_or_gate
        leaf["reason_codes"] = sorted(set(f["gate_reasons"] or [reason]))
        leaf["expected_disposition"] = None
        for key in _ZERO_LEAF_COUNT_KEYS:
            leaf[key] = 0
        leaf["denominator_value"] = f["den_value"] if f["den_value"] >= 0 else 0
        leaf["member_expansion_state"] = "not_applicable"
        leaf["audience_injection_blocked"] = bool(f["injection"])
        return [leaf]

    derived = derive_change(f["change"]) if f["change"] else \
        ("initial_current", None, "initial_full_snapshot", False)
    derived_kind, derived_cause, derived_lineage, analysis_only = derived
    positive = disposition_or_gate == "positive"
    boundary = disposition_or_gate == "boundary"
    leaf: dict[str, Any] = {
        "leaf_kind": "medical_unit",
        "signal_kind": f["kind"],
        "expected_disposition": disposition_or_gate,
        "gate_kind": None,
        "reason_codes": [reason],
        "unit_stable_core_ref": _stable_core_ref(f),
        "numerator_member_count": _unit_member_count(f),
        "numerator_individual_risk_count": f["individual"],
        "numerator_affected_subject_count": f["num_subject"],
        "numerator_event_or_outcome_count": f["num_event"],
        "numerator_center_pattern_count": f["pattern"],
        "numerator_affected_site_count": f["num_site"],
        "denominator_kind": f["den_kind"],
        "denominator_value": f["den_value"] if f["den_value"] >= 0 else 0,
        "denominator_state": f["den_state"],
        "estimate_kind": _estimate_kind(f),
        "project_signal_count": 1 if positive else 0,
        "clue_count": 1 if boundary else 0,
        "query_count": _query_count(f, disposition_or_gate),
        "risk_handoff_count": 1 if positive else 0,
        "change_kind": derived_kind,
        "change_cause": derived_cause,
        "lineage_relation": derived_lineage,
        "handoff_action": f["change"].get("r2_action") if (
            f["change"] and positive) else None,
        "rate_projection_state": f["rate_state"],
        "hidden_member_count": f["vis_hidden_members"],
        "hidden_site_count": f["vis_hidden_sites"],
        "deep_link_target_count": 0 if f["locator_missing"] else f["dl_n"],
        "member_expansion_state": ("unexpandable" if f["q_unlistable"]
                                   else "expanded"),
        "query_redundancy_decision": f["q_decision"],
        "pd_wording_state": f["q_pd"],
        "audience_injection_blocked": bool(f["injection"] and f["injection_blocked"]),
        "counterevidence_rule_matches": f["ce_matched"],
        "model_evidence_role": f["model_role"],
        "hotspot_member_refs": [],
    }
    leaves = [leaf]
    if f["hotspot"]:
        hotspot = {key: None for key in LEAF_KEYS}
        hotspot["leaf_kind"] = "hotspot_member_leaf"
        hotspot["signal_kind"] = f["kind"]
        hotspot["expected_disposition"] = None
        hotspot["reason_codes"] = ["hotspot_preserved"]
        hotspot["hotspot_member_refs"] = [
            f["authority_entry"]["hotspot_member_ref"]]
        for key in _ZERO_LEAF_COUNT_KEYS:
            hotspot[key] = 0
        hotspot["denominator_value"] = f["den_value"] if f["den_value"] >= 0 else 0
        hotspot["member_expansion_state"] = "expanded"
        hotspot["audience_injection_blocked"] = bool(f["injection"])
        leaves.append(hotspot)
    if analysis_only:
        analysis = {key: None for key in LEAF_KEYS}
        analysis["leaf_kind"] = "analysis_only_change_leaf"
        analysis["signal_kind"] = f["kind"]
        analysis["expected_disposition"] = None
        analysis["reason_codes"] = ["analysis_scope_change_only"]
        analysis["change_kind"] = "not_comparable"
        analysis["change_cause"] = derived_cause
        analysis["lineage_relation"] = derived_lineage
        for key in _ZERO_LEAF_COUNT_KEYS:
            analysis[key] = 0
        analysis["denominator_value"] = f["den_value"] if f["den_value"] >= 0 else 0
        analysis["member_expansion_state"] = "not_applicable"
        analysis["audience_injection_blocked"] = bool(f["injection"])
        leaves.append(analysis)
    return leaves


def build_source_leaf_set(f: dict[str, Any],
                          disposition_or_gate: str) -> list[dict[str, Any]]:
    if disposition_or_gate in GATE_DISPOSITIONS:
        return []
    entry = f["authority_entry"]
    out = []
    for member in sorted(entry["members"], key=lambda m: m["member_ref"]):
        out.append({
            "member_ref": member["member_ref"],
            "source_locator_ref": member["locator_ref"],
            "resolution_state": member["locator_resolution_state"],
            "site_stable_id": member["site_stable_id"],
            "subject_stable_id": member["subject_stable_id"],
        })
    return out


def build_trace_leaf_set(f: dict[str, Any], disposition_or_gate: str,
                         reason: str) -> list[dict[str, Any]]:
    replay = bool(f["replay"])
    if f.get("source_authority_bad"):
        content_identity = sha256_text(canonical_json({
            "authority_gate": "source_authority_mismatch",
            "signal_kind": f["kind"],
        }))
    else:
        identity_core = {key: value for key, value in f.items()
                         if key not in IDENTITY_EXCLUDED_KEYS}
        content_identity = sha256_text(canonical_json(identity_core))
    return [{
        "trace_kind": "admission_replay" if replay else "evaluation_identity",
        "stable_core_ref": None if disposition_or_gate in GATE_DISPOSITIONS
        else _stable_core_ref(f),
        "content_identity": content_identity,
        "replay_byte_equal": replay,
        "terminal_state": "blocked" if disposition_or_gate == "integrity_gate"
        else "stable",
    }]


def build_forbidden_leaf_set(f: dict[str, Any], disposition_or_gate: str,
                             reason: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if disposition_or_gate in GATE_DISPOSITIONS:
        out.append({"leaf_kind": "medical_unit", "expected_disposition": None,
                    "gate_kind": None, "change_kind": None,
                    "reason_code": f"zero_medical_output:{reason}"})
        return out
    ch = f["change"]
    derived = derive_change(ch) if ch else None
    if ch is None or ch.get("basis") == "full" or f["replay"]:
        for kind_name in CHANGE_KIND_FORBIDDEN_FOR_NON_DATA:
            out.append({"leaf_kind": "medical_unit", "expected_disposition": None,
                        "gate_kind": None, "change_kind": kind_name,
                        "reason_code": "initial_full_or_replay_no_change_unit"})
    if derived and derived[3]:
        for kind_name in CHANGE_KIND_FORBIDDEN_FOR_NON_DATA:
            out.append({"leaf_kind": "medical_unit", "expected_disposition": None,
                        "gate_kind": None, "change_kind": kind_name,
                        "reason_code": "non_data_change_analysis_only"})
        out.append({"leaf_kind": "medical_unit", "expected_disposition": None,
                    "gate_kind": None, "change_kind": None,
                    "reason_code": "non_data_change_not_clinical"})
    if f["den_state"] == "closed_zero" or f["den_value"] == 0:
        out.append({"leaf_kind": "medical_unit", "expected_disposition": "negative",
                    "gate_kind": None, "change_kind": None,
                    "reason_code": "zero_event_not_negative"})
    if any(code in STIGMA_CODES for code in f["comp_reasons"]):
        out.append({"leaf_kind": "medical_unit", "expected_disposition": "positive",
                    "gate_kind": None, "change_kind": None,
                    "reason_code": "small_site_no_stigma"})
    if f["hit"] != "not_applicable" and not any(
            source in ("typed_member", "verified_measure")
            for source in f["sources"]):
        out.append({"leaf_kind": "medical_unit", "expected_disposition": "positive",
                    "gate_kind": None, "change_kind": None,
                    "reason_code": "nontyped_evidence_no_positive"})
    if f["kind"] == "project_efficacy_trend" and (
            f["efficacy_missing"] or
            (f["treatment_role_required"] and not f["assignment_present"])):
        out.append({"leaf_kind": "medical_unit", "expected_disposition": "positive",
                    "gate_kind": None, "change_kind": None,
                    "reason_code": "efficacy_gate_no_positive"})
    return out


def rebuild_expectation(case: dict[str, Any], f: dict[str, Any],
                        entry: dict[str, Any]) -> dict[str, Any]:
    f["authority_entry"] = entry
    disposition_or_gate, reason, extra = derive_disposition(f)
    expected = {
        "case_id": case["case_id"],
        "oracle_case_id": case["oracle_case_id"],
        "fixture_id": case["fixture_id"],
        "expected_leaf_set": build_expected_leaf_set(
            f, disposition_or_gate, reason, extra),
        "expected_trace_leaf_set": build_trace_leaf_set(
            f, disposition_or_gate, reason),
        "expected_source_leaf_set": build_source_leaf_set(
            f, disposition_or_gate),
        "expected_disposition_or_gate": disposition_or_gate,
        "forbidden_leaf_set": build_forbidden_leaf_set(
            f, disposition_or_gate, reason),
        "oracle_hash": "",
    }
    expected["oracle_hash"] = content_hash(expected, "oracle_hash")
    return expected


# ---------------------------------------------------------------------------
# Authority conformance (own implementation)
# ---------------------------------------------------------------------------
def _member_tuples(members: list[dict[str, Any]]) -> list[tuple]:
    out = []
    for m in members:
        out.append((m["member_ref"], m["member_kind"], m["aggregation_plane"],
                    m["subject_stable_id"], m["site_stable_id"],
                    m["member_scope_state"], m["locator_resolution_state"],
                    m["monitoring_priority"], m["producer_domain"],
                    m["source_locator_refs"][0]
                    if m["source_locator_refs"] else None))
    return sorted(out)


def _locator_ids(typed: dict[str, Any]) -> list[str]:
    ids = set()
    for m in typed["members"]:
        ids.update(m["source_locator_refs"])
    for ref in typed["evidence_refs"]:
        ids.add(ref["locator_id"])
    return sorted(ids)


def _change_block_from_typed(typed: dict[str, Any]) -> dict[str, Any] | None:
    ch = typed["change_decision"]
    if ch is None:
        return None
    def set_hash(refs_list: list[str]) -> str:
        return sha256_text(canonical_json(sorted(refs_list)))
    ca = ch["cutoff_advance"]
    return {
        "execution_basis": ch["execution_basis"],
        "comparison_state": ch["comparison_state"],
        "prior_present": ch["prior_snapshot_ref_or_none"] is not None,
        "prior_evaluation_identity_ref": ch["prior_snapshot_ref_or_none"],
        "r2_prior_ref": ch["r2_prior_ref_or_none"],
        "r2_action": ch["r2_action"],
        "r2_lineage": ch["lineage_relation"],
        "carry_forward": ch["carry_forward_state"] == "active",
        "data_change_ref_set_hash": set_hash(ch["data_change_refs"]),
        "denominator_change_ref_set_hash": set_hash(ch["denominator_change_refs"]),
        "coverage_change_ref_set_hash": set_hash(ch["coverage_change_refs"]),
        "knowledge_change_ref_set_hash": set_hash(ch["knowledge_change_refs"]),
        "rule_change_ref_set_hash": set_hash(ch["rule_change_refs"]),
        "mapping_change_ref_set_hash": set_hash(ch["mapping_change_refs"]),
        "model_change_ref_set_hash": set_hash(ch["model_change_refs"]),
        "method_change_ref_set_hash": set_hash(ch["method_change_refs"]),
        "population_change_ref_set_hash": set_hash(ch["population_change_refs"]),
        "visibility_change_ref_set_hash": set_hash(ch["visibility_change_refs"]),
        "mode_change_ref_set_hash": set_hash(ch["mode_change_refs"]),
        "cutoff_decision_state": ca["decision_state"],
        "cutoff_predicate": ca["strict_advance_predicate_passed"],
        "cutoff_policy_equal": ca["policy_semantic_hash_equal"],
        "prior_boundary_value": ca["prior_boundary_value"],
        "current_boundary_value": ca["current_boundary_value"],
    }


def _segment_hash(segments: list[dict[str, Any]]) -> str:
    ordered = sorted(segments, key=lambda s: s["segment_id"])
    return sha256_text(canonical_json(ordered))


def authority_problems(case: dict[str, Any],
                       entry: dict[str, Any]) -> list[str]:
    """Return conformance violations of the catalog case vs the fixed
    authority entry (empty = conformant)."""
    problems: list[str] = []
    cid = case["case_id"]
    typed = case["typed_input"]

    def check(label: str, expected: Any, got: Any) -> None:
        if expected != got:
            problems.append(f"{cid} authority mismatch {label}: "
                            f"authority={expected!r} catalog={got!r}")

    check("partition", entry["partition"], case["primary_partition"])
    check("project_ref", entry["project_ref"], typed["project_ref"])
    check("run_ref", entry["run_ref"], typed["run_ref"])
    check("snapshot_ref", entry["snapshot_ref"], typed["snapshot_ref"])
    sd = typed["signal_definition"]
    check("signal_definition.signal_definition_id",
          entry["signal_definition"]["signal_definition_id"],
          sd["signal_definition_id"])
    check("signal_definition.signal_kind",
          entry["signal_definition"]["signal_kind"], sd["signal_kind"])
    check("signal_definition.clinical_claim_token",
          entry["signal_definition"]["clinical_claim_token"],
          sd["clinical_claim_token"])
    check("signal_definition.d10_action",
          entry["signal_definition"]["d10_action"], sd["d10_action"])
    check("signal_definition.required_producer_domains",
          entry["signal_definition"]["required_producer_domains"],
          sd["required_producer_domains"])
    lr = typed["legal_matrix_row"]
    check("legal_matrix_row.row_id", entry["legal_matrix_row"]["row_id"],
          lr["row_id"])
    check("legal_matrix_row.signal_kind",
          entry["legal_matrix_row"]["signal_kind"], lr["signal_kind"])
    check("legal_matrix_row.clinical_claim_token",
          entry["legal_matrix_row"]["clinical_claim_token"],
          lr["clinical_claim_token"])
    check("legal_matrix_row.d10_action",
          entry["legal_matrix_row"]["d10_action"], lr["d10_action"])
    sb = typed["project_scope_binding"]
    check("scope_binding.scope_binding_id",
          entry["scope_binding"]["scope_binding_id"], sb["scope_binding_id"])
    check("scope_binding.scope_type",
          entry["scope_binding"]["scope_type"], sb["scope_type"])
    check("scope_binding.scope_equality_decision",
          entry["scope_binding"]["scope_equality_decision"],
          sb["scope_equality_decision"])
    mode = typed["mode_contract"]
    check("mode_contract.mode_contract_version",
          entry["mode_contract"]["mode_contract_version"],
          mode["mode_contract_version"])
    check("mode_contract.design_applicable_state",
          entry["mode_contract"]["design_applicable_state"],
          mode["design_applicable_state"])
    check("mode_contract.mode_contract_content_hash",
          entry["mode_contract"]["mode_contract_content_hash"],
          mode["mode_contract_content_hash"])
    check("mode_contract.design_clause_ref",
          entry["mode_contract"]["design_clause_ref"],
          mode["design_clause_ref"])
    es = typed["expected_set"]
    gate = es["admission_gate"]
    check("expected_set.expected_set_state",
          entry["expected_set"]["expected_set_state"], es["expected_set_state"])
    check("expected_set.admission_gate_kind",
          entry["expected_set"]["admission_gate_kind"],
          gate["gate_kind"] if gate else None)
    check("expected_set.admission_gate_reasons",
          entry["expected_set"]["admission_gate_reasons"],
          gate["reason_codes"] if gate else [])
    windows = [{
        "analysis_window_stable_id": w["analysis_window_stable_id"],
        "window_instance_id": w["window_instance_id"],
        "window_definition_id": w["window_definition_id"],
        "window_kind": w["window_kind"],
        "window_state": w["window_state"],
        "cutoff_ref": w["cutoff_ref"],
    } for w in typed["analysis_windows"]]
    check("analysis_windows", entry["analysis_windows"], windows)
    st = typed["stratum"]
    check("stratum.stratum_contract_id",
          entry["stratum"]["stratum_contract_id"], st["stratum_contract_id"])
    check("stratum.stratum_key", entry["stratum"]["stratum_key"],
          st["stratum_key"])
    check("stratum.stratum_state", entry["stratum"]["stratum_state"],
          st["stratum_state"])
    check("stratum.stratum_admission", entry["stratum"]["stratum_admission"],
          st["stratum_admission"])
    check("comparison_reference_stable_id",
          entry["comparison_reference_stable_id"],
          typed["comparison_gate"]["comparison_reference_stable_id"])
    pop = typed["analysis_population"]
    check("analysis_population.analysis_population_ref",
          entry["analysis_population"]["analysis_population_ref"],
          pop["analysis_population_ref"])
    check("analysis_population.analysis_population_contract_id",
          entry["analysis_population"]["analysis_population_contract_id"],
          pop["analysis_population_contract_id"])
    check("members",
          sorted(entry["members"],
                 key=lambda m: (m["member_ref"], m["member_kind"])),
          [dict(zip(("member_ref", "member_kind", "aggregation_plane",
                     "subject_stable_id", "site_stable_id",
                     "member_scope_state", "locator_resolution_state",
                     "monitoring_priority", "producer_domain", "locator_ref"),
                    t))
           for t in _member_tuples(typed["members"])])
    nl = typed["numerator_ledger"]
    for key in ("individual_risk_count", "center_pattern_count",
                "affected_subject_count", "event_or_outcome_count",
                "affected_site_count", "numerator_member_count"):
        check(f"numerator_ledger.{key}", entry["numerator_ledger"][key],
              nl[key])
    den = typed["denominator"]
    check("denominator.denominator_kind",
          entry["denominator"]["denominator_kind"], den["denominator_kind"])
    check("denominator.denominator_value",
          entry["denominator"]["denominator_value"], den["denominator_value"])
    check("denominator.denominator_unit",
          entry["denominator"]["denominator_unit"], den["denominator_unit"])
    check("denominator.denominator_state",
          entry["denominator"]["denominator_state"], den["denominator_state"])
    check("denominator.exclusion_reason_codes",
          entry["denominator"]["exclusion_reason_codes"],
          den["exclusion_reason_codes"])
    check("denominator_member_set_hash",
          entry["denominator_member_set_hash"],
          sha256_text(canonical_json(sorted(den["denominator_member_refs"]))))
    segments = typed["time_segments"]
    check("time_segments.count", entry["time_segments"]["count"],
          len(segments))
    check("time_segments.set_hash", entry["time_segments"]["set_hash"],
          _segment_hash(segments))
    entry_patterns = {p["member_ref"]: p for p in entry["d09_patterns"]}
    for member in typed["members"]:
        if member["member_kind"] != "center_pattern":
            continue
        pinned = entry_patterns.get(member["member_ref"])
        if pinned is None:
            problems.append(f"{cid} d09 pattern {member['member_ref']} "
                            "not pinned")
            continue
        check(f"d09_patterns[{member['member_ref']}].owner_domain",
              pinned["owner_domain"], member["producer_domain"])
        check(f"d09_patterns[{member['member_ref']}].descendant_refs",
              pinned["descendant_refs"], member["descendant_member_refs"])
    mob = typed["measure_origin_binding"]
    pinned_mo = entry["measure_origin"]
    if pinned_mo is None:
        check("measure_origin", None, mob)
    else:
        check("measure_origin.binding_id", pinned_mo["binding_id"],
              mob["binding_id"])
        check("measure_origin.measure_ref", pinned_mo["measure_ref"],
              mob["measure_ref"])
        check("measure_origin.origin_decision",
              pinned_mo["origin_decision"], mob["origin_decision"])
        for key in ("verified_risk_refs", "distinct_risk_refs",
                    "ambiguous_risk_refs", "candidate_risk_refs"):
            check(f"measure_origin.{key}", pinned_mo[key], mob[key])
        check("measure_origin.numerator_plane_state",
              pinned_mo["numerator_plane_state"],
              mob["numerator_plane_state"])
        for key, pinned_key in (("verified_risk_refs", "verified_ref_set_hash"),
                                ("distinct_risk_refs", "distinct_ref_set_hash"),
                                ("ambiguous_risk_refs", "ambiguous_ref_set_hash")):
            check(f"measure_origin.{key}_set_hash", pinned_mo[pinned_key],
                  sha256_text(canonical_json(sorted(mob[key]))))
        check("measure_origin.source_provenance_hash",
              pinned_mo["source_provenance_hash"],
              mob["source_provenance_hash"])
        check("measure_origin.candidate_partition_hash",
              pinned_mo["candidate_ref_set_hash"],
              mob["candidate_partition_hash"])
        check("measure_origin.binding_hash",
              content_hash(mob, "binding_hash"), mob["binding_hash"])
    ec = typed["efficacy_context"]
    treatment = entry["treatment"]
    check("treatment.treatment_role_required",
          treatment["treatment_role_required"],
          bool(ec and ec["treatment_role_required"]))
    check("treatment.authority_ref", treatment["authority_ref"],
          ec["treatment_role_authority_ref"] if ec else None)
    check("treatment.assignment_identity_ref",
          treatment["assignment_identity_ref"],
          ec["treatment_assignment_exposure_identity_ref"] if ec else None)
    check("treatment.mapping_hash", treatment["mapping_hash"],
          ec["treatment_assignment_mapping_hash"] if ec else None)
    vis = typed["visibility_decision"]
    pinned_vis = entry["visibility"]
    check("visibility.blind_status", pinned_vis["blind_status"],
          vis["blind_status"])
    check("visibility.hidden_member_count",
          pinned_vis["hidden_member_count"], vis["hidden_member_count"])
    check("visibility.hidden_site_count",
          pinned_vis["hidden_site_count"], vis["hidden_site_count"])
    check("visibility.rate_projection_state",
          pinned_vis["rate_projection_state"], vis["rate_projection_state"])
    check("visibility.eligible_n", pinned_vis["eligible_n"], vis["eligible_n"])
    check("visibility.visible_n", pinned_vis["visible_n"], vis["visible_n"])
    check("visibility.hidden_set_omitted",
          pinned_vis["hidden_set_omitted"], vis["hidden_set_omitted"])
    check("visibility.deep_link_eligible_violation",
          pinned_vis["deep_link_eligible_violation"],
          vis["deep_link_eligible_violation"])
    check("visibility.treatment_inference_attempt",
          pinned_vis["treatment_inference_attempt"],
          vis["treatment_inference_attempt"])
    for key, ref_key in (("evaluation_member_set_hash",
                          "evaluation_member_refs"),
                         ("projectable_member_set_hash",
                          "projectable_member_refs"),
                         ("hidden_member_set_hash", "hidden_member_refs"),
                         ("deep_link_eligible_member_set_hash",
                          "deep_link_eligible_member_refs")):
        check(f"visibility.{key}", pinned_vis[key],
              sha256_text(canonical_json(sorted(set(vis[ref_key])))))
    deep_links = [{
        "target_kind": d["target_kind"], "site_ref": d["site_ref"],
        "subject_ref": d["subject_ref"],
        "member_object_ref": d["member_object_ref"],
    } for d in typed["deep_links"]]
    check("deep_links", entry["deep_links"], deep_links)
    qd = typed["query_decision"]
    pinned_q = entry["query"]
    check("query.decision", pinned_q["decision"], qd["decision"])
    check("query.max_query_member_fanout",
          pinned_q["max_query_member_fanout"], qd["max_query_member_fanout"])
    check("query.pd_wording_state", pinned_q["pd_wording_state"],
          qd["pd_wording_state"])
    check("query.member_unlistable", pinned_q["member_unlistable"],
          qd["member_unlistable"])
    for key in ("covered_member_refs", "uncovered_member_refs",
                "member_query_content_identities"):
        check(f"query.{key}", pinned_q[key], qd[key])
    check("query.unit_member_set_hash", pinned_q["unit_member_set_hash"],
          qd["unit_member_set_hash"])
    check("query.coverage_proof_hash", pinned_q["coverage_proof_hash"],
          qd["coverage_proof_hash"])
    check("query.covered_member_set_hash",
          pinned_q["covered_member_set_hash"],
          sha256_text(canonical_json(sorted(set(qd["covered_member_refs"])))))
    check("query.uncovered_member_set_hash",
          pinned_q["uncovered_member_set_hash"],
          sha256_text(canonical_json(sorted(set(qd["uncovered_member_refs"])))))
    check("query.union_member_set_hash",
          pinned_q["union_member_set_hash"],
          sha256_text(canonical_json(
              sorted(set(qd["covered_member_refs"])
                     | set(qd["uncovered_member_refs"])))))
    check("query.disjoint", pinned_q["disjoint"],
          not (set(qd["covered_member_refs"])
               & set(qd["uncovered_member_refs"])))
    me = typed["model_evidence"]
    pinned_me = entry["model_evidence"]
    if pinned_me is None:
        check("model_evidence", None, me)
    else:
        for key in ("role", "evaluation_content_identity", "input_content_hash",
                    "source_revision_content_pairs", "source_refs", "model_id",
                    "model_version", "independent_context_hash", "ensemble_id",
                    "ensemble_size", "member_analysis_refs", "permitted_leaf",
                    "member_analysis_ref_set_hash", "output_identity", "output_hash",
                    "adjudication_state", "model_binding_hash", "model_evidence_id"):
            check(f"model_evidence.{key}", pinned_me[key], me[key])
    check("audience_contract.forbidden_internal_terms",
          entry["audience_contract"]["forbidden_internal_terms"],
          case["audience_contract"]["forbidden_internal_terms"])
    accepted_source_pairs = entry["source_revisions"]
    submitted_source_pairs = typed["source_revision_content_pairs"]
    missing_source_pairs = [
        pair for pair in accepted_source_pairs
        if pair not in submitted_source_pairs
    ]
    if missing_source_pairs:
        problems.append(
            f"{cid} authority mismatch source_revisions: accepted pair(s) "
            f"not present in submitted set {missing_source_pairs!r}")
    check("source_locator_set_hash", entry["source_locator_set_hash"],
          sha256_text(canonical_json(_locator_ids(typed))))
    check("evidence_refs", entry["evidence_refs"], typed["evidence_refs"])
    check("change", entry["change"], _change_block_from_typed(typed))
    check("visibility.evaluation_site_set_hash",
          entry["visibility"]["evaluation_site_set_hash"],
          sha256_text(canonical_json(sorted(set(vis["evaluation_site_refs"])))))
    check("visibility.projectable_site_set_hash",
          entry["visibility"]["projectable_site_set_hash"],
          sha256_text(canonical_json(sorted(set(vis["projectable_site_refs"])))))
    check("visibility.hidden_site_set_hash",
          entry["visibility"]["hidden_site_set_hash"],
          sha256_text(canonical_json(sorted(set(vis["hidden_site_refs"])))))
    check("visibility.deep_link_eligible_site_set_hash",
          entry["visibility"]["deep_link_eligible_site_set_hash"],
          sha256_text(canonical_json(
              sorted(set(vis["deep_link_eligible_site_refs"])))))
    projectable_refs = set(vis["projectable_member_refs"])
    pair_list = sorted({
        (m["subject_stable_id"], m["site_stable_id"])
        for m in typed["members"]
        if m["member_ref"] in projectable_refs
        and m["subject_stable_id"]
        and m["site_stable_id"] in set(vis["projectable_site_refs"])})
    check("visibility.projectable_subject_site_pair_set_hash",
          entry["visibility"]["projectable_subject_site_pair_set_hash"],
          sha256_text(canonical_json(pair_list)))
    check("visibility.projectable_subject_site_pairs",
          entry["visibility"]["projectable_subject_site_pairs"],
          vis["projectable_subject_site_pairs"])
    check("visibility.deep_link_eligible_subject_site_pairs",
          entry["visibility"]["deep_link_eligible_subject_site_pairs"],
          vis["deep_link_eligible_subject_site_pairs"])
    eligible_pair_list = sorted({
        tuple(pair) for pair in vis["deep_link_eligible_subject_site_pairs"]})
    check("visibility.deep_link_eligible_subject_site_pair_set_hash",
          entry["visibility"]["deep_link_eligible_subject_site_pair_set_hash"],
          sha256_text(canonical_json([list(pair)
                                      for pair in eligible_pair_list])))
    hotspot = typed["hotspot"]
    check("hotspot_member_ref", entry["hotspot_member_ref"],
          hotspot["hotspot_member_refs"][0] if hotspot else None)
    return problems


# ---------------------------------------------------------------------------
# Fixed identity + rebuilt chain checks
# ---------------------------------------------------------------------------
def _fixed_identity_problems(artifacts: dict[str, Any]) -> list[str]:
    """Reject ANY replacement of contract/authority/catalog/oracle/registry/
    quota/generator/verifier identity - not just self-consistent hashes."""
    problems: list[str] = []
    raw_contract = artifacts["contract"]
    if hashlib.sha256(raw_contract).hexdigest() != CONTRACT_FILE_SHA256:
        problems.append("fixed identity: contract raw SHA replaced")
    if _self_code_hash() != VERIFIER_SELF_SHA256:
        problems.append("fixed identity: verifier source replaced")

    def raw_sha(path: Path, pin: str, label: str) -> None:
        if not path.exists():
            problems.append(f"fixed identity: {label} source missing")
            return
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
            problems.append(f"fixed identity: {label} source SHA replaced")

    raw_sha(AUTHORITY_GENERATOR_PATH, AUTHORITY_GENERATOR_FILE_SHA256,
            "authority generator")
    raw_sha(CATALOG_GENERATOR_PATH, CATALOG_GENERATOR_FILE_SHA256,
            "catalog generator")
    raw_sha(ORACLE_GENERATOR_PATH, ORACLE_GENERATOR_FILE_SHA256,
            "oracle generator")

    def artifact_sha(path: Path, raw_pin: str, content_pin: str,
                     content_key: str, label: str) -> None:
        if hashlib.sha256(path.read_bytes()).hexdigest() != raw_pin:
            problems.append(f"fixed identity: {label} raw SHA replaced")
        obj = load_json(path)
        if content_hash(obj, content_key) != content_pin:
            problems.append(f"fixed identity: {label} content replaced")

    artifact_sha(AUTHORITY, AUTHORITY_RAW_SHA256, AUTHORITY_CONTENT_SHA256,
                 "content_hash", "authority registry")
    artifact_sha(CATALOG, CATALOG_RAW_SHA256, CATALOG_CONTENT_SHA256,
                 "catalog_hash", "catalog")
    artifact_sha(ORACLE, ORACLE_RAW_SHA256, ORACLE_CONTENT_SHA256,
                 "content_hash", "oracle")
    artifact_sha(REGISTRY, REGISTRY_RAW_SHA256, REGISTRY_CONTENT_SHA256,
                 "content_hash", "challenge registry")
    artifact_sha(QUOTA, QUOTA_RAW_SHA256, QUOTA_CONTENT_SHA256,
                 "manifest_hash", "quota manifest")

    authority = artifacts["authority"]
    # in-memory override identities: any re-signed/replaced artifact (even a
    # fully self-consistent chain) fails closed against the frozen pins
    for label, obj, key, pin in (
            ("authority", authority, "content_hash", AUTHORITY_CONTENT_SHA256),
            ("catalog", artifacts["catalog"], "catalog_hash",
             CATALOG_CONTENT_SHA256),
            ("oracle", artifacts["oracle"], "content_hash", ORACLE_CONTENT_SHA256),
            ("registry", artifacts["registry"], "content_hash",
             REGISTRY_CONTENT_SHA256),
            ("quota", artifacts["quota"], "manifest_hash",
             QUOTA_CONTENT_SHA256)):
        if content_hash(obj, key) != pin:
            problems.append(f"fixed identity: {label} content replaced "
                            "(re-signed chain rejected)")
    if authority.get("generator_hash") != AUTHORITY_GENERATOR_PIN:
        problems.append("fixed identity: authority generator pin replaced")
    if authority.get("contract_semantic_hash") != CONTRACT_SEMANTIC_HASH:
        problems.append("fixed identity: authority contract identity replaced")
    if authority.get("schema_version") != "1.0.0":
        problems.append("fixed identity: authority schema version replaced")
    if authority.get("authority_id") != \
            "medical-monitoring-r4-d10-fixture-authority-registry-v1":
        problems.append("fixed identity: authority id replaced")
    catalog = artifacts["catalog"]
    if catalog.get("generator_hash", None) is not None:
        problems.append("catalog must not carry a generator hash")
    if catalog.get("catalog_hash") != CATALOG_CONTENT_SHA256:
        problems.append("fixed identity: catalog content hash replaced")
    oracle = artifacts["oracle"]
    if oracle.get("oracle_id") != "medical-monitoring-r4-d10-expected-outcome-oracle":
        problems.append("fixed identity: oracle id replaced")
    return problems


def _rebuilt_chain_problems(artifacts: dict[str, Any]) -> list[str]:
    """Rebuild registry bijection, partition/attack quotas and the
    case-to-attack mapping from the ACTUAL catalog/authority/oracle content."""
    problems: list[str] = []
    catalog = artifacts["catalog"]
    registry = artifacts["registry"]
    quota = artifacts["quota"]
    authority = artifacts["authority"]
    cases = catalog.get("cases", [])
    case_by_id = {c["case_id"]: c for c in cases}
    partition_by_id: dict[str, int] = {}
    for case in cases:
        partition_by_id[case["primary_partition"]] = \
            partition_by_id.get(case["primary_partition"], 0) + 1
    # quota partition identities + counts rebuilt from the catalog
    req_partitions = [e.get("partition_id")
                      for e in quota.get("primary_partition_requirements", [])]
    if sorted(req_partitions) != sorted(PARTITION_IDS):
        problems.append("rebuilt chain: quota partition ids replaced")
    for pid in PARTITION_IDS:
        if quota.get("actual_primary_partition_counts", {}).get(pid) != \
                partition_by_id.get(pid, 0):
            problems.append(f"rebuilt chain: partition {pid} count mismatch")
    if quota.get("case_id_union") != sorted(case_by_id):
        problems.append("rebuilt chain: quota case_id_union replaced")
    if quota.get("union_count") != len(case_by_id):
        problems.append("rebuilt chain: quota union_count mismatch")
    # quota attack identities + case-to-attack forward/reverse mapping
    req_attacks = [e.get("attack_id")
                   for e in quota.get("mandatory_attack_requirements", [])]
    if sorted(req_attacks) != sorted(ATTACK_IDS):
        problems.append("rebuilt chain: quota attack ids replaced")
    rows = quota.get("case_to_mandatory_attack_rows", [])
    attack_counts = {aid: 0 for aid in ATTACK_IDS}
    seen_rows: set[str] = set()
    for row in rows:
        cid = row.get("case_id")
        if cid not in case_by_id:
            problems.append(f"rebuilt chain: attack row unknown case {cid}")
            continue
        if cid in seen_rows:
            problems.append(f"rebuilt chain: duplicate attack row {cid}")
        seen_rows.add(cid)
        ids = row.get("attack_ids", [])
        if sorted(ids) != sorted(set(ids)):
            problems.append(f"rebuilt chain: attack row {cid} not sorted-unique")
        for aid in ids:
            if aid not in ATTACK_IDS:
                problems.append(f"rebuilt chain: unknown attack {aid}")
            attack_counts[aid] = attack_counts.get(aid, 0) + 1
        mutation_class = case_by_id[cid].get("mutation_class")
        if mutation_class not in ("none",) and \
                mutation_class not in ids:
            problems.append(f"rebuilt chain: {cid} mutation_class {mutation_class} "
                            "missing from its attack row (forward mapping)")
    for aid in ATTACK_IDS:
        if attack_counts[aid] < 1:
            problems.append(f"rebuilt chain: attack {aid} has no case (reverse)")
        if attack_counts[aid] != \
                quota.get("actual_mandatory_attack_counts", {}).get(aid):
            problems.append(f"rebuilt chain: attack {aid} count mismatch")
    # registry five-column bijection rebuilt from the catalog
    row_by_case: dict[str, dict] = {}
    for row in registry.get("rows", []):
        row_by_case[row.get("case_id")] = row
    for cid, case in case_by_id.items():
        row = row_by_case.get(cid)
        if row is None:
            problems.append(f"rebuilt chain: registry row missing {cid}")
            continue
        for col, key in (("fixture_id", "fixture_id"),
                         ("oracle_case_id", "oracle_case_id"),
                         ("manifest_case_id", "manifest_case_id")):
            if row.get(col) != case.get(key):
                problems.append(f"rebuilt chain: registry {col} for {cid} "
                                "does not match the catalog")
        number = cid.rsplit("-", 1)[-1]
        if row.get("test_id") != f"D10-TEST-{number}":
            problems.append(f"rebuilt chain: registry test_id for {cid} replaced")
    if len(row_by_case) != len(case_by_id):
        problems.append("rebuilt chain: registry row coverage mismatch")
    # authority case coverage vs catalog
    auth_by_case = {e["case_id"]: e for e in authority.get("entries", [])}
    if sorted(auth_by_case) != sorted(case_by_id):
        problems.append("rebuilt chain: authority/catalog case sets differ")
    return problems


def _global_problems(artifacts: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    problems.extend(_fixed_identity_problems(artifacts))
    catalog = artifacts["catalog"]
    oracle = artifacts["oracle"]
    registry = artifacts["registry"]
    quota = artifacts["quota"]
    authority = artifacts["authority"]
    problems.extend(_rebuilt_chain_problems(artifacts))

    raw_contract = artifacts["contract"]
    if hashlib.sha256(raw_contract).hexdigest() != CONTRACT_FILE_SHA256:
        problems.append("contract file SHA-256 mismatch")
    if hashlib.sha256(normalize_contract(
            raw_contract.decode("utf-8")).encode("utf-8")).hexdigest() \
            != CONTRACT_SEMANTIC_HASH:
        problems.append("contract semantic hash mismatch")

    _exact_keys(catalog, CATALOG_TOP_KEYS, "catalog top-level", problems)
    cases = catalog.get("cases", [])
    if len(cases) != catalog.get("case_count"):
        problems.append("catalog case_count mismatch")
    if len(cases) != EXPECTED_CASE_COUNT:
        problems.append(f"catalog case_count {len(cases)} != 312")
    case_ids = set()
    for index, case in enumerate(cases, start=1):
        _exact_keys(case, CASE_KEYS, f"catalog case {index}", problems)
        if case.get("case_id") != f"D10-CASE-{index:03d}":
            problems.append(f"catalog case {index} case_id mismatch")
        if case.get("case_id") in case_ids:
            problems.append(f"duplicate case {case.get('case_id')}")
        case_ids.add(case.get("case_id"))
        for key in ("expected_leaf_set", "expected_trace_leaf_set",
                    "expected_source_leaf_set"):
            if case.get(key) is not None:
                problems.append(f"{case.get('case_id')} {key} not null")
        if "typed_input" in case:
            _exact_keys(case["typed_input"], TYPED_INPUT_KEYS,
                        f"{case.get('case_id')} typed_input", problems)
    if catalog.get("catalog_hash") != content_hash(catalog, "catalog_hash"):
        problems.append("catalog content hash mismatch")

    _exact_keys(oracle, ORACLE_TOP_KEYS, "oracle top-level", problems)
    expectations = oracle.get("ordered_expectations", [])
    if len(expectations) != oracle.get("case_count"):
        problems.append("oracle case_count mismatch")
    for index, entry in enumerate(expectations):
        _exact_keys(entry, ORDERED_EXPECTATION_KEYS,
                    f"oracle expectation {index}", problems)
        if entry.get("case_id") != f"D10-CASE-{index + 1:03d}":
            problems.append(f"oracle expectation {index} case_id mismatch")
        for key in ("expected_leaf_set", "expected_trace_leaf_set",
                    "expected_source_leaf_set", "forbidden_leaf_set"):
            for leaf in entry.get(key, []) or []:
                leaf_keys = TRACE_LEAF_KEYS if key == "expected_trace_leaf_set" \
                    else SOURCE_LEAF_KEYS if key == "expected_source_leaf_set" \
                    else FORBIDDEN_LEAF_KEYS if key == "forbidden_leaf_set" \
                    else LEAF_KEYS
                _exact_keys(leaf, leaf_keys,
                            f"{entry.get('case_id')} {key} leaf", problems)
        if entry.get("oracle_hash") != content_hash(entry, "oracle_hash"):
            problems.append(f"{entry.get('case_id')} oracle_hash mismatch")
        if entry.get("expected_disposition_or_gate") not in \
                EXPECTED_DISPOSITION_OR_GATE:
            problems.append(f"{entry.get('case_id')} disposition not closed")
    if oracle.get("content_hash") != content_hash(oracle, "content_hash"):
        problems.append("oracle content hash mismatch")
    if oracle.get("fixture_authority_registry_hash") != \
            authority.get("content_hash"):
        problems.append("oracle authority registry hash != authority content")

    _exact_keys(registry, REGISTRY_TOP_KEYS, "registry top-level", problems)
    rows = registry.get("rows", [])
    if len(rows) != len(cases):
        problems.append("registry row count mismatch")
    seen: dict[str, set[str]] = {col: set() for col in BIJECTION_COLUMNS}
    for row in rows:
        _exact_keys(row, REGISTRY_ROW_KEYS, "registry row", problems)
        for col in BIJECTION_COLUMNS:
            value = row.get(col)
            if value in seen[col]:
                problems.append(f"registry {col} duplicate {value}")
            seen[col].add(value)
    if registry.get("content_hash") != content_hash(registry, "content_hash"):
        problems.append("registry content hash mismatch")

    _exact_keys(quota, QUOTA_TOP_KEYS, "quota top-level", problems)
    if quota.get("required_total") != REQUIRED_TOTAL:
        problems.append("quota required_total mismatch")
    actual = quota.get("actual_primary_partition_counts", {})
    total = sum(actual.values())
    if total != len(cases) or quota.get("union_count") != len(cases):
        problems.append("quota union/count mismatch")
    if quota.get("duplicate_case_ids") or quota.get("missing_case_ids"):
        problems.append("quota duplicate/missing case ids")
    if any(v != 0 for v in quota.get("pairwise_intersection_counts", {}).values()):
        problems.append("quota partitions not pairwise disjoint")
    attack_counts = quota.get("actual_mandatory_attack_counts", {})
    if any(v < 1 for v in attack_counts.values()):
        problems.append("quota mandatory attack below 1")
    if quota.get("catalog_hash") != catalog.get("catalog_hash"):
        problems.append("quota catalog_hash mismatch")
    if quota.get("oracle_hash") != oracle.get("content_hash"):
        problems.append("quota oracle_hash mismatch")
    if quota.get("registry_hash") != registry.get("content_hash"):
        problems.append("quota registry_hash mismatch")
    if quota.get("manifest_hash") != content_hash(quota, "manifest_hash"):
        problems.append("quota manifest hash mismatch")

    _exact_keys(authority, AUTHORITY_TOP_KEYS, "authority top-level", problems)
    entries = authority.get("entries", [])
    if len(entries) != authority.get("case_count"):
        problems.append("authority case_count mismatch")
    if len(entries) != EXPECTED_CASE_COUNT:
        problems.append("authority entries != 312")
    auth_ids = set()
    for index, entry in enumerate(entries):
        _exact_keys(entry, AUTHORITY_ENTRY_KEYS,
                    f"authority entry {index}", problems)
        if entry.get("case_id") != f"D10-CASE-{index + 1:03d}":
            problems.append(f"authority entry {index} case_id mismatch")
        if entry.get("case_id") in auth_ids:
            problems.append(f"duplicate authority entry {entry.get('case_id')}")
        auth_ids.add(entry.get("case_id"))
        if entry.get("authority_hash") != content_hash(entry, "authority_hash"):
            problems.append(f"{entry.get('case_id')} authority_hash mismatch")
        for member in entry.get("members", []):
            _exact_keys(member, AUTHORITY_MEMBER_KEYS,
                        f"{entry.get('case_id')} authority member", problems)
        for ref in entry.get("evidence_refs", []):
            _exact_keys(ref, AUTHORITY_EVIDENCE_REF_KEYS,
                        f"{entry.get('case_id')} authority evidence_ref", problems)
        if entry.get("change") is not None:
            _exact_keys(entry["change"], AUTHORITY_CHANGE_KEYS,
                        f"{entry.get('case_id')} authority change", problems)
    if authority.get("content_hash") != content_hash(authority, "content_hash"):
        problems.append("authority content hash mismatch")
    audit = authority.get("bijection_audit", {})
    if audit.get("row_count") != len(entries) or not audit.get("bijection_ok"):
        problems.append("authority bijection audit failed")
    return problems


# ---------------------------------------------------------------------------
# Public verification entry
# ---------------------------------------------------------------------------
def verify_all(catalog: Any = None, oracle: Any = None, registry: Any = None,
               quota: Any = None, authority: Any = None) -> dict[str, Any]:
    """Verify every artifact chain relation. Optional artifact overrides (for
    tamper testing) replace the on-disk artifacts; the fixed authority is the
    default reference. Returns {"ok", "problems", "per_case"}."""
    artifacts = _load_all()
    if catalog is not None:
        artifacts["catalog"] = catalog
    if oracle is not None:
        artifacts["oracle"] = oracle
    if registry is not None:
        artifacts["registry"] = registry
    if quota is not None:
        artifacts["quota"] = quota
    if authority is not None:
        artifacts["authority"] = authority
    problems = _global_problems(artifacts)
    catalog = artifacts["catalog"]
    oracle = artifacts["oracle"]
    authority = artifacts["authority"]
    authority_index = {e["case_id"]: e for e in authority["entries"]}
    oracle_index = {e["case_id"]: e for e in oracle["ordered_expectations"]}
    per_case: dict[str, dict[str, Any]] = {}
    for case in catalog["cases"]:
        cid = case["case_id"]
        case_problems: list[str] = []
        entry = authority_index.get(cid)
        if entry is None:
            case_problems.append(f"{cid} missing authority entry")
            per_case[cid] = {"ok": False, "problems": case_problems}
            continue
        case_problems.extend(authority_problems(case, entry))
        f = project_facts(case, entry)
        rebuilt = rebuild_expectation(case, f, entry)
        expected = oracle_index.get(cid)
        if expected is None:
            case_problems.append(f"{cid} missing oracle entry")
        elif canonical_json(rebuilt) != canonical_json(expected):
            case_problems.append(f"{cid} rebuilt expectation differs from oracle")
        per_case[cid] = {"ok": not case_problems, "problems": case_problems}
        problems.extend(case_problems)
    return {"ok": not problems, "problems": problems, "per_case": per_case}


def check(verbose: bool = True) -> int:
    result = verify_all()
    if verbose:
        problems = result["problems"]
        print(f"independent verifier: {'OK' if result['ok'] else 'FAILED'} "
              f"({len(problems)} problems, "
              f"{sum(1 for v in result['per_case'].values() if not v['ok'])} "
              f"cases failing)")
        for problem in problems[:20]:
            print(f"  - {problem}")
    return 0 if result["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent D10 artifact verifier")
    parser.add_argument("--quiet", action="store_true", help="suppress output")
    args = parser.parse_args()
    try:
        return check(verbose=not args.quiet)
    except VerifyError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"FAILED: unreadable artifact: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
