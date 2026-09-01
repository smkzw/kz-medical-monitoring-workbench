#!/usr/bin/env python3
"""D10 typed artifact generator (worker_01, finite code executor).

Builds the offline synthetic R4-D10 v0.6 typed fixture catalog (>= 312
exact-key immutable cases across 12 mutually-exclusive primary partitions),
the five-column challenge-manifest registry, and the partition-quota /
mandatory-attack manifest.

Independence contract (task context + contract section 15/16):
  * This module NEVER reads the expected-outcome oracle artifact and never
    derives expected leaves: the catalog's three expected_* fields are literal
    JSON null; the registry holds deterministic identity rows with
    oracle_reference_state="unresolved" for worker_02; expected leaves exist
    only in the independent oracle artifact.
  * Generation derives exclusively from the embedded typed case/family
    specification tables below (contract section 15 challenge matrix) and the
    frozen v0.6 contract; standard library only; no network, no wall-clock,
    no randomness, no runtime/UI/service code.
  * Two-stage registry contract (proven D09 pattern, worker_03 documented
    decision): stage A is this module - it deterministically assembles the
    catalog + quota manifest + a PROVISIONAL registry whose
    oracle_reference_state.state="unresolved". Stage B is worker_02's accepted
    resolution: the on-disk registry is resolved in place (state="resolved",
    expected_leaf_policy gains the suffix '; oracle artifact content_hash=<h>',
    top-level content_hash resealed) and the quota manifest's oracle_hash /
    registry_hash / manifest_hash are finalized; both resolution deltas are
    restricted to the declared delta key sets below. This module validates the
    stage-B linkage oracle-blind (it never reads the oracle artifact) and
    refuses to clobber resolved artifacts.
  * The quota manifest carries the five-chain hashes: catalog_hash,
    oracle_hash, registry_hash, generator_hash, manifest_hash (contract
    section 15 D10PartitionQuotaManifest exact schema).
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
REGISTRY = ROOT / "reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json"
QUOTA = ROOT / "reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json"
AUTHORITY = ROOT / "reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"

# ---------------------------------------------------------------------------
# Two-stage registry contract (proven D09 structural pattern; D10 adaptation)
# ---------------------------------------------------------------------------
# Path of the independent oracle artifact. Declared for stage-B verification
# only; this module NEVER reads the file or its content.
DECLARED_ORACLE_ARTIFACT_PATH = "reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"
# Suffix worker_02 appends to oracle_reference_state.expected_leaf_policy when
# resolving the provisional registry (followed by the oracle content_hash).
RESOLVED_POLICY_SUFFIX_PREFIX = "; oracle artifact content_hash="
# Closed resolution states for the registry artifact.
REGISTRY_RESOLUTION_STATES = ("unresolved", "resolved")
# Stage-B delta: the ONLY fields worker_02 may change on the provisional
# registry. Everything else must be byte-identical between the fresh
# provisional registry and the accepted resolved registry. `generator_hash`
# is NOT a delta: the resolved registry must carry the frozen stage-A
# generator SHA (STAGE_A_GENERATOR_SHA256 below), validated exactly.
RESOLVED_DELTA_TOP = frozenset({"content_hash"})
RESOLVED_DELTA_REFERENCE = frozenset({"state", "expected_leaf_policy"})
# Quota manifest stage-B delta: the three chain hashes worker_02 finalizes.
# Everything else must be byte-identical between provisional and resolved.
QUOTA_RESOLVED_DELTA_KEYS = frozenset({"oracle_hash", "registry_hash", "manifest_hash"})
# Provisional quota-manifest placeholder for the oracle/registry chain hashes.
PROVISIONAL_HASH_SENTINEL = "0" * 64
# Frozen stage-A generator SHA: the exact catalog-generator revision that
# produced the catalog/quota/registry chain. The resolved registry's and
# resolved quota manifest's `generator_hash` field must equal this pin
# exactly; altered generator_hash fails closed.
#
# The pin is self-referential by design: it hashes THIS generator file with
# the pin literal itself normalized to 64 zeros (_generator_code_hash), so the
# pin value does not feed back into the hash. Any other edit to the generator
# source changes the code hash and fails closed.
_PIN_SENTINEL = "0" * 64
STAGE_A_GENERATOR_SHA256 = "2984d7fe908d08343e2289ff9d8ec0c5c221dd1cde532113b61c058bd17def8b"


def _generator_code_hash() -> str:
    """SHA-256 of this generator file with the self-referential pin literal
    normalized to 64 zeros (proven D09 pattern)."""
    text = Path(__file__).read_text(encoding="utf-8")
    return sha256_text(text.replace(STAGE_A_GENERATOR_SHA256, _PIN_SENTINEL))


def _compute_generator_pin() -> str:
    """Compute the frozen stage-A pin for this source revision and print it."""
    print(_generator_code_hash())
    return _generator_code_hash()


# ---------------------------------------------------------------------------
# Frozen contract snapshot (accepted immutable SHA, acceptance record 2026-08-16)
# ---------------------------------------------------------------------------
CONTRACT_FILE_SHA256 = "c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95"
CONTRACT_SEMANTIC_HASH = CONTRACT_FILE_SHA256

# ---------------------------------------------------------------------------
# Artifact identity constants
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "1.0.0"
CATALOG_ID = "medical-monitoring-r4-d10-typed-fixture-catalog-v1"
REGISTRY_ID = "medical-monitoring-r4-d10-challenge-manifest-registry-v1"
QUOTA_MANIFEST_ID = "medical-monitoring-r4-d10-partition-quota-manifest-v1"
TYPED_INPUT_SCHEMA = "d10-typed-input-v1"
ALGORITHM_VERSION = "d10_v1"
REQUIRED_TOTAL = 312

# Canonical synthetic scope (offline only; no real project/patient data).
PROJECT_REF = "SYN-D10-PROJECT-001"
SITE_REF = "SYN-D10-SITE-001"
SITE_REFS = ("SYN-D10-SITE-001", "SYN-D10-SITE-002", "SYN-D10-SITE-003")
RUN_REF = "SYN-D10-RUN-001"
SNAPSHOT_REF = "SYN-D10-SNAP-001"
MONITORING_MODE = "offline_synthetic"

# ---------------------------------------------------------------------------
# Closed enums (frozen from contract v0.6 text; exact closed sets)
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
UNRESOLVED_TOKEN = "unresolved"
OWNER_ROUTES = ("evaluate_and_own", "consume_only", "handoff_only",
                "context_only", "routing_gate")
DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")
GATE_DISPOSITIONS = ("global_gate", "comparison_set_gate", "window_pair_gate",
                     "routing_gate", "integrity_gate", "handoff_gate")
EXPECTED_DISPOSITION_OR_GATE = DISPOSITIONS + GATE_DISPOSITIONS
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
MEMBER_SCOPE_STATES = ("in_scope", "wrong_project", "wrong_site", "wrong_subject",
                       "unresolvable")
SITE_ACTIVATION_STATES = ("active", "late")
SCOPE_EQUALITY_DECISIONS = ("exact_match", "mismatch")
RULE_HIT_STATES = ("hit", "no_hit", "not_applicable")
EVIDENCE_SOURCES = ("typed_member", "verified_measure", "pvalue", "model_majority")
ADJUDICATION_STATES = ("accepted", "divergent", "pending")
OPPORTUNITY_STATES = ("sufficient", "insufficient", "unknown")
OPPORTUNITY_PROVENANCES = ("accepted_d05_plan", "raw_only")
EXPECTED_SET_STATES = ("admitted", "global_admission_failed",
                       "routed_consume_only", "routing_gate_unresolved",
                       "control_plane_gate")
GRAINS = ("project", "site", "subject", "member", "unit", "control_plane")
WINDOW_KINDS = ("calendar_interval", "study_day_interval", "exposure_interval")
WINDOW_STATES = ("closed", "open")
STRATUM_STATES = ("closed", "open", "empty")
STRATUM_ADMISSIONS = ("admitted", "rejected_empty", "fanout_rejected", "not_required")
PERMITTED_OUTPUTS = ("gate_only", "admit_cross_site_unit", "admit_trend_unit")
DESIGN_APPLICABLE_STATES = ("applicable", "not_applicable", "unresolved")
LEAF_KINDS = ("medical_unit", "hotspot_member_leaf",
              "control_plane_comparison_gate", "control_plane_window_pair_gate",
              "global_integrity_gate", "routing_gate", "handoff_gate",
              "analysis_only_change_leaf")

# ---------------------------------------------------------------------------
# Mandatory attack ids (contract section 15): the 12 required attacks plus the
# 24 single-listed mandatory_attack_requirements (5 shared ids) = 31 distinct.
# A case may prove several attacks; its primary partition counts once only.
# ---------------------------------------------------------------------------
CORE_ATTACKS = (
    "initial_full_fake_change",
    "d09_within_site_trend_recompute",
    "cross_layer_count_mixing",
    "non_data_change_as_improvement",
    "zero_event_empty_denominator_negative",
    "small_site_stigma",
    "blind_treatment_inference",
    "efficacy_estimand_mismatch_forced_comparison",
    "model_majority_ensemble1_positive",
    "hotspot_singleton_not_hidden",
    "rehash_bypass_evaluator_identity",
    "audience_engineering_injection",
)
ENUMERATED_ATTACKS = (
    "cross_project_scope",
    "legal_row_mismatch",
    "initial_full_fake_change",
    "strict_cutoff_predicate_tamper_same_window_replay",
    "cutoff_first_positive_create",
    "cutoff_rule_or_mode_mixed_first_positive",
    "required_l1_hole",
    "gap_only_provenance",
    "measure_origin_cross_envelope_mixed",
    "d09_parent_descendant_duplication",
    "d07_risk_safety_measure_same_origin",
    "denominator_time_segment_tamper",
    "small_site_stigma",
    "blind_hidden_set_omission",
    "hidden_deeplink_eligible_subset_violation",
    "treatment_assignment_missing",
    "formal_safety_efficacy_wording",
    "model_majority_ensemble1_positive",
    "r2_wrong_prior_lineage_carry_forward",
    "query_reorder_source_pd_redundancy_tamper",
    "projection_deeplink_visibility_tamper",
    "unicode_confusable_engineering_inject",
    "rule_method_visibility_mixed_change",
    "hotspot_singleton_not_hidden",
)
ATTACK_IDS = tuple(dict.fromkeys(CORE_ATTACKS + ENUMERATED_ATTACKS))
ATTACK_LABELS_ZH = {
    "cross_project_scope": "跨项目 scope 混入",
    "legal_row_mismatch": "legal matrix 行不匹配",
    "initial_full_fake_change": "首次 full 伪造新增/关闭",
    "strict_cutoff_predicate_tamper_same_window_replay": "strict-cutoff 断言篡改/same-window 重放",
    "cutoff_first_positive_create": "cutoff first-positive create 违规",
    "cutoff_rule_or_mode_mixed_first_positive": "cutoff 与非数据变化混合 first-positive",
    "required_l1_hole": "required L1 缺口被判 zero/negative",
    "gap_only_provenance": "仅 raw gap 来源入 admission",
    "measure_origin_cross_envelope_mixed": "measure-origin 跨 envelope/mixed",
    "d09_parent_descendant_duplication": "D09 parent/descendant 重复计量",
    "d07_risk_safety_measure_same_origin": "D07 风险与 safety measure 同源双计",
    "denominator_time_segment_tamper": "分母/time-segment 篡改",
    "small_site_stigma": "小中心异常率置顶污名",
    "blind_hidden_set_omission": "盲态 hidden 集遗漏",
    "hidden_deeplink_eligible_subset_violation": "hidden 深链/eligible 子集越界",
    "treatment_assignment_missing": "疗效 treatment assignment 缺失",
    "formal_safety_efficacy_wording": "正式安全/疗效结论措辞",
    "model_majority_ensemble1_positive": "模型多数票/ensemble=1 直接 positive",
    "r2_wrong_prior_lineage_carry_forward": "R2 错误 prior/lineage/carry-forward",
    "query_reorder_source_pd_redundancy_tamper": "Query 重排/来源/PD/冗余篡改",
    "projection_deeplink_visibility_tamper": "projection/deep-link visibility 篡改",
    "unicode_confusable_engineering_inject": "Unicode/confusable 工程引用注入",
    "rule_method_visibility_mixed_change": "规则/方法/visibility 混合变化",
    "hotspot_singleton_not_hidden": "高风险单例未隐藏",
    "d09_within_site_trend_recompute": "D09 单中心趋势被 D10 重算",
    "cross_layer_count_mixing": "跨层计数相加为总风险数",
    "non_data_change_as_improvement": "非数据变化伪装临床改善",
    "zero_event_empty_denominator_negative": "零事件/空分母/缺 coverage 判 negative",
    "blind_treatment_inference": "未授权盲态推断治疗组",
    "efficacy_estimand_mismatch_forced_comparison": "estimand/缺失处理不同仍强制比较",
    "rehash_bypass_evaluator_identity": "rehash 对象绕过 evaluator identity",
    "audience_engineering_injection": "audience 中文字段注入工程引用",
}
MUTATION_CLASSES = ("none",) + ATTACK_IDS

# ---------------------------------------------------------------------------
# 12 mutually-exclusive primary partitions (contract section 15 floors; the
# floors sum to exactly 312; every case counts in exactly one partition).
# ---------------------------------------------------------------------------
PARTITIONS = (
    ("p01_signal_kind_disposition", "信号类型×五类处置/反证/FP/FN/hidden/replay/gate", 60),
    ("p02_owner_routing_zero_medical", "owner routing/越权/consume-only/handoff-only/零医学输出", 24),
    ("p03_identity_scope_duplicate", "project/site/subject/member identity、wrong scope、duplicate、同源歧义", 24),
    ("p04_numerator_denominator_time", "分子/分母/subject-time/exposure-time/opportunity/analysis population", 28),
    ("p05_cross_site_comparability", "跨中心可比性：小中心/晚启动/病例构成/随访暴露/coverage/method", 28),
    ("p06_safety_trend", "safety：AE/严重度/SAE/AESI/停药/实验室/暴露调整/特殊人群/单例不隐藏", 24),
    ("p07_efficacy_trend", "efficacy：endpoint/timepoint/baseline/missing/intercurrent/estimand/盲态治疗角色", 24),
    ("p08_change_cause_lineage", "initial full/incremental/cutoff/规则/映射/方法/人群/visibility/coverage 变化", 28),
    ("p09_query_deeplink", "Query 冗余/fanout/PD 措辞/Project→Site→Subject→Journey/source 深链", 20),
    ("p10_visibility_blindness", "visibility/盲态/hidden 分母/不披露", 16),
    ("p11_unicode_tamper_bijection", "Unicode/key 精确性/hash/篡改/catalog-oracle-registry 双射", 20),
    ("p12_anti_overfit", "反过拟合：改名/重排/非语义版本字段变化", 16),
)
MIN_CASE_COUNT = sum(entry[2] for entry in PARTITIONS)  # 312
PARTITION_MINIMUMS = {entry[0]: entry[2] for entry in PARTITIONS}
PARTITION_LABELS = {entry[0]: entry[1] for entry in PARTITIONS}

# ---------------------------------------------------------------------------
# Frozen schema: exact key sets (contract section 15 + typed contract objects)
# ---------------------------------------------------------------------------
CATALOG_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
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
PARTITION_REQUIREMENT_KEYS = ["partition_id", "partition_label_zh",
                              "required_minimum"]
ATTACK_REQUIREMENT_KEYS = ["attack_id", "attack_label_zh", "required_minimum"]
CASE_ATTACK_ROW_KEYS = ["case_id", "attack_ids"]

# typed_input envelope (37 exact keys)
TYPED_INPUT_KEYS = [
    "input_schema", "envelope_id", "project_ref", "run_ref", "snapshot_ref",
    "source_revision_content_pairs", "project_scope_binding", "mode_contract",
    "signal_definition", "legal_matrix_row", "expected_set",
    "analysis_windows", "stratum", "comparison_gate", "window_pair_gate",
    "site_ledger", "members", "numerator_ledger", "measure_origin_binding",
    "denominator",
    "time_segments", "opportunity", "analysis_population", "coverage",
    "change_decision", "visibility_decision", "query_decision",
    "audience_text", "deep_links", "model_evidence", "safety_context",
    "efficacy_context", "rule_hit", "hotspot", "count_layers",
    "evaluation_limits", "numeric_policy", "mutation_context",
    "anti_overfit_variant", "evidence_refs",
]
EVALUATION_LIMITS_KEYS = ["small_sample", "limited_evidence", "limited_reason"]
NUMERATOR_LEDGER_KEYS = ["individual_risk_count", "center_pattern_count",
                         "affected_subject_count", "event_or_outcome_count",
                         "affected_site_count", "numerator_member_count"]
SCOPE_BINDING_KEYS = ["scope_binding_id", "scope_type", "scope_equality_decision",
                     "scope_binding_hash"]
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
MEASURE_ORIGIN_BINDING_KEYS = ["binding_id", "measure_ref", "origin_decision",
                               "verified_risk_refs", "distinct_risk_refs",
                               "ambiguous_risk_refs", "candidate_risk_refs",
                               "candidate_partition_hash",
                               "numerator_plane_state", "binding_hash",
                               "source_provenance_hash"]
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

# ---------------------------------------------------------------------------
# Canonical JSON and hashing (proven D06/D07/D08/D09 infrastructure conventions)
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


def validate_contract() -> str:
    """Verify the frozen contract file bytes/semantic SHA-256 (read-only)."""
    raw = CONTRACT.read_bytes()
    if sha256_bytes(raw) != CONTRACT_FILE_SHA256:
        raise D10ArtifactError("contract", "sha_mismatch",
                               f"contract file SHA-256 mismatch (expected "
                               f"{CONTRACT_FILE_SHA256})")
    semantic = sha256_text(normalize_contract(raw.decode("utf-8")))
    if semantic != CONTRACT_SEMANTIC_HASH:
        raise D10ArtifactError("contract", "semantic_hash_mismatch",
                               f"contract semantic hash mismatch (expected "
                               f"{CONTRACT_SEMANTIC_HASH})")
    return semantic


# ---------------------------------------------------------------------------
# Validation primitives
# ---------------------------------------------------------------------------
class D10ArtifactError(Exception):
    def __init__(self, stage: str, error_class: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.error_class = error_class


def expect_exact_keys(obj: Any, keys: list[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} must be an object")
    if sorted(obj.keys()) != sorted(keys):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} exact-key mismatch: "
                               f"got {sorted(obj.keys())}, want {sorted(keys)}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} must be a non-empty string")
    return value


def require_enum(value: Any, closed: tuple[str, ...], label: str) -> str:
    if value not in closed:
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} {value!r} not in closed set")
    return value


def require_nonneg_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} must be a non-negative int")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} must be a list of non-empty strings")
    return value


def sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _sorted_unique(values: list[str], label: str) -> list[str]:
    if len(set(values)) != len(values):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{label} contains duplicates")
    return sorted(values)


# ---------------------------------------------------------------------------
# Deterministic synthetic content hashes and id helpers
# ---------------------------------------------------------------------------
def _content_sha(label: str) -> str:
    """Deterministic synthetic authority/content hash derived from a stable label."""
    return sha256_text(f"d10-content-v1:{label}")


def _subject_ids(idx: int, count: int, *, alt: bool = False, offset: int = 0,
                 site: int = 1) -> list[str]:
    prefix = "SYN-D10-ALT-SUBJ" if alt else "SYN-D10-SUBJ"
    return [f"{prefix}-{idx:03d}-{site:02d}-{offset + m:02d}" for m in range(1, count + 1)]


def _site_ref(site: int, *, alt: bool = False) -> str:
    if alt:
        return f"SYN-D10-ALT-SITE-{site:03d}"
    return f"SYN-D10-SITE-{site:03d}"


def _project_ref(alt: bool = False) -> str:
    return "SYN-D10-ALT-PROJECT-001" if alt else PROJECT_REF


def _member_ids(idx: int, count: int, prefix: str) -> list[str]:
    return [f"SYN-D10-{prefix}-{idx:03d}-{m:02d}" for m in range(1, count + 1)]


def _event_ids(idx: int, count: int) -> list[str]:
    return _member_ids(idx, count, "EVT")


def _locator_ids(idx: int, count: int) -> list[str]:
    return _member_ids(idx, count, "LOC")


# ---------------------------------------------------------------------------
# Object builders (every emitted object uses its EXACT frozen key set)
# ---------------------------------------------------------------------------
def _scope_binding(idx: int, spec: dict[str, Any], *, alt: bool = False) -> dict[str, Any]:
    binding = {
        "scope_binding_id": f"SYN-D10-SCOPE-{idx:03d}",
        "scope_type": spec.get("scope_type", "project"),
        "scope_equality_decision": spec.get("scope_eq", "exact_match"),
        "scope_binding_hash": "",
    }
    binding["scope_binding_hash"] = content_hash(binding, "scope_binding_hash")
    return binding


def _mode_contract(idx: int, spec: dict[str, Any], *, alt: bool = False) -> dict[str, Any]:
    design_ref = None
    if spec.get("design_applicable", "applicable") != "applicable":
        design_ref = f"SYN-D10-DESIGN-{idx:03d}"
    mode = {
        "mode_contract_version": ("SYN-D10-MODE-001-ALT" if alt
                                  else "SYN-D10-MODE-001"),
        "mode_contract_content_hash": "",
        "design_clause_ref": design_ref,
        "design_applicable_state": spec.get("design_applicable", "applicable"),
    }
    mode["mode_contract_content_hash"] = content_hash(
        mode, "mode_contract_content_hash")
    return mode


def _signal_definition(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    kind = spec["kind"]
    domain = {
        "project_risk_distribution": "risk_distribution",
        "cross_site_pattern": "cross_site",
        "project_time_trend": "project_time",
        "project_safety_trend": "safety",
        "project_efficacy_trend": "efficacy",
    }[kind]
    default_required = {
        "project_risk_distribution": ["D01", "D02", "D03", "D04"],
        "cross_site_pattern": ["D09", "D01"],
        "project_time_trend": ["D09", "D10"],
        "project_safety_trend": ["D07", "D01"],
        "project_efficacy_trend": ["D06", "D01"],
    }[kind]
    return {
        "signal_definition_id": f"SYN-D10-DEF-{idx:03d}",
        "signal_kind": kind,
        "clinical_claim_token": spec["token"],
        "d10_action": spec["owner"],
        "risk_or_outcome_domain": domain,
        "required_producer_domains": spec.get("required_domains", default_required),
        "positive_rule_ref": f"SYN-D10-RULE-POS-{idx:03d}",
        "counterevidence_rule_refs": [f"SYN-D10-RULE-CE-{idx:03d}-{n}"
                                      for n in range(1, spec.get("ce_declared", 1) + 1)],
        "legal_matrix_row_ref": f"SYN-D10-LEGAL-{idx:03d}",
        "authority_locator": f"SYN-D10-AUTH-LOC-{idx:03d}",
    }


def _legal_matrix_row(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("legal_match", True):
        kind, token, action = spec["kind"], spec["token"], spec["owner"]
    else:
        # Conflicting row: kind/token/action deliberately mismatch the
        # signal definition (legal matrix compile-time authority).
        kind = "cross_site_pattern"
        token = "d10_cross_site_pattern"
        action = "consume_only"
    row = {
        "row_id": f"SYN-D10-LEGAL-{idx:03d}",
        "signal_kind": kind,
        "clinical_claim_token": token,
        "d10_action": action,
        "row_hash": "",
    }
    row["row_hash"] = sha256_text(canonical_json({
        "row_id": row["row_id"], "signal_kind": kind,
        "clinical_claim_token": token, "d10_action": action}))
    return row


def _expected_set(spec: dict[str, Any]) -> dict[str, Any]:
    state = spec.get("es_state", "admitted")
    gate = None
    if state != "admitted":
        if state == "control_plane_gate":
            gate_kind = spec.get("gate_kind", "comparison_set_gate")
        elif state == "global_admission_failed":
            gate_kind = "global_gate"
        else:
            gate_kind = "routing_gate"
        gate = {
            "gate_kind": gate_kind,
            "reason_codes": spec.get("gate_reasons", []),
        }
    return {"expected_set_state": state, "admission_gate": gate}


def _window(idx: int, widx: int, *, cutoff_ref: str | None = None) -> dict[str, Any]:
    return {
        "analysis_window_stable_id": f"SYN-D10-WIN-{idx:03d}-{widx}",
        "window_instance_id": f"SYN-D10-WIN-{idx:03d}-{widx}-INST",
        "window_definition_id": f"SYN-D10-WD-{idx:03d}-{widx}",
        "window_definition_hash": _content_sha(f"wd:{idx:03d}:{widx}"),
        "window_kind": "calendar_interval",
        "window_state": "closed",
        "window_start": "2026-01-01",
        "window_end": "2026-03-31" if widx == 1 else "2026-06-30",
        "cutoff_ref": cutoff_ref,
    }


def _windows(idx: int, spec: dict[str, Any]) -> list[dict[str, Any]]:
    cutoff_ref = None
    if spec.get("change"):
        cutoff_ref = f"SYN-D10-CUT-{idx:03d}"
    return [_window(idx, widx, cutoff_ref=cutoff_ref)
            for widx in range(1, spec.get("wins", 1) + 1)]


def _stratum(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "stratum_contract_id": f"SYN-D10-SC-{idx:03d}",
        "stratum_key": spec.get("stratum_key", "overall"),
        "stratum_state": spec.get("stratum_state", "closed"),
        "stratum_admission": spec.get("stratum_admission", "admitted"),
    }


def _comparison_gate(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    comp = spec.get("comp_state", "ready")
    eligible = spec.get("eligible_sites", 3)
    required = spec.get("required_sites", 3)
    excluded = spec.get("excluded_sites", 0)
    reasons: list[str] = []
    if comp != "ready":
        reasons.append(f"comparison_{comp}")
    reasons.extend(spec.get("comp_reasons", []))
    permitted = "admit_cross_site_unit" if comp == "ready" else "gate_only"
    return {
        "comparison_state": comp,
        "required_site_count_ref": f"SYN-D10-REQ-SITE-{idx:03d}",
        "observed_eligible_site_count": eligible,
        "eligible_site_refs": [_site_ref(s) for s in range(1, eligible + 1)],
        "excluded_site_refs": [_site_ref(s) for s in range(eligible + 1,
                                                            eligible + excluded + 1)],
        "reason_codes": reasons,
        "permitted_output": permitted,
        "comparison_reference_stable_id": "SYN-D10-REF-OVERALL",
    }


def _window_pair_gate(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    pair = spec.get("pair_state", "ready")
    unique_windows = spec.get("unique_windows", 2 if spec.get("wins", 1) >= 2 else 1)
    reasons = [] if pair == "ready" else [f"window_pair_{pair}"]
    permitted = "admit_trend_unit" if pair == "ready" else "gate_only"
    return {
        "pair_state": pair,
        "required_window_count_ref": f"SYN-D10-REQ-WIN-{idx:03d}",
        "observed_unique_window_count": unique_windows,
        "reason_codes": reasons,
        "permitted_output": permitted,
    }


def _site_ledger(idx: int, spec: dict[str, Any], *, alt: bool = False) -> dict[str, Any]:
    sites = spec.get("ledger_sites", 1)
    subjects_per_site = spec.get("ledger_subjects", 42)
    return {
        "ledger_id": f"SYN-D10-LEDGER-{idx:03d}",
        "site_ref": _site_ref(1, alt=alt) if sites == 1 else
                    f"[{', '.join(_site_ref(s, alt=alt) for s in range(1, sites + 1))}]",
        "eligible_subject_refs": _subject_ids(idx, subjects_per_site, alt=alt, site=1),
        "treated_subject_refs": _subject_ids(idx, subjects_per_site, alt=alt, site=1),
        "evaluable_subject_refs": _subject_ids(idx, subjects_per_site, alt=alt, site=1),
        "d09_pattern_refs": _member_ids(idx, spec.get("d09_pattern_n", 0), "PAT"),
        "coverage_refs": [f"SYN-D10-LOC-CV-{idx:03d}"],
        "site_activation_ref": f"SYN-D10-ACT-{idx:03d}",
        "site_activation_state": spec.get("site_activation", "active"),
        "identity_state": spec.get("identity_state", "stable"),
    }


def _member(idx: int, m: int, kind: str, *, spec: dict[str, Any] = None,
            plane: str | None = None, site: int = 1, subject: str | None = None,
            priority: str = "medium", scope_state: str = "in_scope",
            loc_state: str = "locatable", descendants: int = 0,
            treatment_role: str | None = None, alt: bool = False) -> dict[str, Any]:
    spec = spec or {}
    prefix = {"individual_risk": "RISK", "center_pattern": "PAT",
              "accepted_gap": "GAP", "safety_measure": "SAFE",
              "efficacy_measure": "EFF"}[kind]
    member_ref = f"SYN-D10-{prefix}-{idx:03d}-{m:02d}"
    site_ref = _site_ref(site, alt=alt)
    subject_prefix = "SYN-D10-ALT-SUBJ" if alt else "SYN-D10-SUBJ"
    subject_id = subject or f"{subject_prefix}-{idx:03d}-{site:02d}-{m:02d}"
    if scope_state == "wrong_project":
        site_ref = "SYN-OTHER-PROJECT-SITE-001"
    if scope_state == "wrong_site":
        site_ref = "SYN-OTHER-SITE-001"
    if scope_state == "wrong_subject":
        subject_id = f"SYN-OTHER-SUBJECT-{idx:03d}-{m:02d}"
    desc_refs = _member_ids(idx, descendants, "DESC")
    return {
        "member_ref": member_ref,
        "member_kind": kind,
        "aggregation_plane": plane or {
            "center_pattern": "site_pattern",
            "safety_measure": "project_measure",
            "efficacy_measure": "project_measure",
        }.get(kind, "individual"),
        "producer_domain": ("D06" if (kind == "center_pattern"
                                      and spec.get("member_producer_d06"))
                            else spec.get("member_producer", {
            "individual_risk": "D01", "center_pattern": "D09",
            "accepted_gap": "D05", "safety_measure": "D07",
            "efficacy_measure": "D06",
        }[kind])),
        "member_scope_state": scope_state,
        "site_stable_id": site_ref,
        "subject_stable_id": subject_id,
        "monitoring_priority": priority,
        "accepted_current_state": spec.get("member_accepted", "accepted_current"),
        "locator_resolution_state": loc_state,
        "source_locator_refs": _member_ids(idx, 1, "LOC"),
        "descendant_member_refs": desc_refs,
        "descendant_set_hash": sha256_text(canonical_json(sorted(desc_refs)))
        if desc_refs else None,
        "treatment_role_ref": treatment_role,
    }


def _members(idx: int, spec: dict[str, Any], *, alt: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    n_subject = spec.get("num", {}).get("subject", 7)
    n_pattern = spec.get("pattern", 0)
    n_gap = 1 if spec.get("opp") else 0
    n_safety = 1 if spec.get("safety") else 0
    n_eff = 1 if spec.get("efficacy") else 0
    hotspot = spec.get("hotspot", False)
    # individual risk members (subject-plane)
    for m in range(1, n_subject + 1):
        priority = "high" if (hotspot and m == 1) else "medium"
        scope_state = "in_scope"
        if spec.get("member_wrong_project"):
            scope_state = "wrong_project"
        elif spec.get("member_wrong_site"):
            scope_state = "wrong_site"
        elif spec.get("member_wrong_subject"):
            scope_state = "wrong_subject"
        elif spec.get("member_unresolvable"):
            scope_state = "unresolvable"
        loc_state = "missing" if (spec.get("locator_missing") and m == 1) else \
            "locatable"
        out.append(_member(idx, m, "individual_risk", spec=spec, site=1,
                           priority=priority, scope_state=scope_state,
                           loc_state=loc_state, alt=alt))
    for m in range(1, n_pattern + 1):
        descendants = spec.get("descendants", 0)
        out.append(_member(idx, m, "center_pattern", spec=spec, site=1,
                           descendants=descendants, alt=alt))
    if spec.get("desc_in_numerator"):
        # D09 parent pattern descendant ALSO counted as an individual member:
        # the descendant ref appears both as pattern descendant and numerator.
        out.append({
            **_member(idx, 1, "individual_risk", spec=spec, site=1, alt=alt),
            "member_ref": f"SYN-D10-DESC-{idx:03d}-01",
        })
    if n_gap:
        out.append(_member(idx, 1, "accepted_gap", spec=spec, site=1, alt=alt))
    if n_safety:
        out.append(_member(idx, 1, "safety_measure", spec=spec, site=1, alt=alt))
    if n_eff:
        out.append(_member(idx, 1, "efficacy_measure", spec=spec, site=1, alt=alt))
    if spec.get("dup_member_ref"):
        out.append(dict(out[0]))
    return out


def _measure_origin_binding(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    origin = spec.get("origin")
    if origin is None:
        return None
    verified = origin.get("verified", 0)
    distinct = origin.get("distinct", 0)
    ambiguous = origin.get("ambiguous", 0)
    risk_refs = _member_ids(idx, spec.get("num", {}).get("subject", 7),
                            "RISK")
    cursor = 0
    verified_refs = sorted(set(risk_refs[cursor:cursor + verified]))
    cursor += verified
    distinct_refs = sorted(set(risk_refs[cursor:cursor + distinct]))
    cursor += distinct
    ambiguous_refs = sorted(set(risk_refs[cursor:cursor + ambiguous]))
    candidate_refs = sorted(set(verified_refs) | set(distinct_refs)
                            | set(ambiguous_refs))
    if origin.get("decision") == "wrong_scope" and not candidate_refs:
        # The synthetic row deliberately carries no resolvable candidate;
        # the closed outcome is the contract's scope-failure state.  For any
        # resolvable refs below, the partition still owns the decision.
        decision = "wrong_scope"
    elif ambiguous_refs:
        decision = "ambiguous"
    elif verified_refs and distinct_refs:
        decision = "mixed_verified_and_distinct"
    elif verified_refs:
        decision = "all_verified_same_origin"
    elif distinct_refs:
        decision = "all_distinct"
    else:
        decision = "not_evaluable"
    binding = {
        "binding_id": f"SYN-D10-ORIGIN-{idx:03d}",
        "measure_ref": f"SYN-D10-SAFE-{idx:03d}-01",
        "origin_decision": decision,
        "verified_risk_refs": verified_refs,
        "distinct_risk_refs": distinct_refs,
        "ambiguous_risk_refs": ambiguous_refs,
        "candidate_risk_refs": candidate_refs,
        "candidate_partition_hash": sha256_text(canonical_json(candidate_refs)),
        "numerator_plane_state": origin.get("plane_state", "single"),
        "binding_hash": "",
    }
    binding["source_provenance_hash"] = sha256_text(canonical_json({
        "measure_ref": binding["measure_ref"],
        "source_revisions": [{
            "revision_id": f"SRC-REV-{idx:03d}-001",
            "content_hash": sha256_text(canonical_json({
                "revision_id": f"SRC-REV-{idx:03d}-001",
                "source_locators": _locator_ids(idx, spec)}))}],
        "locator_ids": _locator_ids(idx, spec),
    }))
    binding["binding_hash"] = content_hash(binding, "binding_hash")
    return binding


def _denominator(idx: int, spec: dict[str, Any], *, alt: bool = False) -> dict[str, Any]:
    kind = spec.get("den_kind", "treated_subjects")
    value = spec.get("den_value", 126)
    state = spec.get("den_state", "closed_positive")
    excluded = spec.get("den_excl", [])
    if kind in ("subject_time", "exposure_time") and spec.get("segments", 0):
        # time-kind denominator value is the sum of the non-overlapping
        # normalized segment durations (independent recomputation anchor).
        value = spec.get("segments", 0) * 30
    # recomputed_value is the validator-rebuilt value from immutable source
    # anchors: any discrepancy (declared tamper fixtures only) is an integrity
    # failure. Exclusion refs live OUTSIDE the member subject range (offset
    # 999) except for the excluded-member-counted tamper fixture.
    recomputed = value - 1 if spec.get("den_tamper") else value
    excl_offset = 0 if spec.get("excluded_in_numerator") else 999
    unit = {"subject_time": "subject_day", "exposure_time": "subject_day",
            "expected_assessment_opportunities": "opportunity"}.get(kind, "subject")
    return {
        "denominator_kind": kind,
        "denominator_member_refs": _subject_ids(idx, max(value, 0), alt=alt),
        "denominator_value": value,
        "recomputed_value": recomputed,
        "denominator_unit": unit,
        "denominator_state": state,
        "exclusion_reason_codes": excluded,
        "excluded_member_refs": _subject_ids(idx, len(excluded), alt=alt,
                                             offset=excl_offset),
    }


def _time_segments(idx: int, spec: dict[str, Any], *, alt: bool = False) -> list[dict[str, Any]]:
    segs: list[dict[str, Any]] = []
    for n in range(1, spec.get("segments", 0) + 1):
        tamper = spec.get("seg_tamper", False)
        raw = 30
        norm = 31 if tamper else raw
        overlap_ref = None if not spec.get("seg_overlap") else f"SYN-D10-OVERLAP-{idx:03d}-{n}"
        segs.append({
            "segment_id": f"SYN-D10-SEG-{idx:03d}-{n}",
            "member_ref": f"SYN-D10-SUBJ-{idx:03d}-01-{n:02d}" if alt else
                          f"SYN-D10-SUBJ-{idx:03d}-01-{n:02d}",
            "segment_kind": "subject_time",
            "start_value": 1 + (n - 1) * 31,
            "end_value": 1 + (n - 1) * 31 + raw - 1,
            "raw_duration": raw,
            "normalized_duration": norm,
            "unit": "day",
            "inclusivity": "both_inclusive",
            "overlap_resolution_ref": overlap_ref,
        })
    return segs


def _opportunity(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    opp = spec.get("opp")
    if opp is None:
        return None
    expected = opp.get("expected", 42)
    observed = opp.get("observed", 9)
    provenance = opp.get("provenance", "accepted_d05_plan")
    missing = expected - observed if opp.get("complete", True) else expected
    return {
        "opportunity_definition_ref": f"SYN-D10-OPPDEF-{idx:03d}",
        "expected_opportunity_count": expected,
        "observed_opportunity_count": observed,
        "missing_opportunity_refs": _member_ids(idx, max(missing, 0), "OPP"),
        "opportunity_provenance": provenance,
        "opportunity_state": opp.get("state", "sufficient"),
        "complete": opp.get("complete", True),
    }


def _analysis_population(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_population_ref": f"SYN-D10-POP-{idx:03d}",
        "present": spec.get("pop_present", True),
        "analysis_population_contract_id": f"SYN-D10-POPC-{idx:03d}",
    }


def _coverage(idx: int, spec: dict[str, Any]) -> list[dict[str, Any]]:
    overrides = {row[0]: (row[1], row[2]) for row in spec.get("cov", [])}
    domains = ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09"]
    out = []
    for domain in domains:
        l0, l1 = overrides.get(domain, ("covered", "complete"))
        out.append({
            "producer_domain": domain,
            "l0_status": l0,
            "l1_medical_completeness_state": l1,
            "accepted_current": True,
            "coverage_locator_ids": [f"SYN-D10-LOC-CV-{idx:03d}"],
        })
    return out


def _cutoff_advance(idx: int, ch: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_state": ch.get("cutoff_state", "not_evaluable"),
        "strict_advance_predicate_passed": ch.get("cutoff_predicate", False),
        "policy_semantic_hash_equal": ch.get("cutoff_policy_equal", False),
        "prior_boundary_value": ch.get("prior_boundary", "2026-03-31"),
        "current_boundary_value": ch.get("current_boundary", "2026-06-30"),
    }


def _change_decision(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    ch = spec.get("change")
    if ch is None:
        return None
    def refs(key: str, n: int) -> list[str]:
        return [f"SYN-D10-{key}-{idx:03d}-{m:02d}" for m in range(1, n + 1)]
    prior = "SYN-D10-SNAP-PRIOR-001" if ch.get("prior") else None
    r2_prior = "SYN-D10-R2-PRIOR-001" if ch.get("r2_prior") else None
    return {
        "execution_basis": ch.get("basis", "full"),
        "comparison_state": ch.get("comparison_state", "initial_full"),
        "prior_snapshot_ref_or_none": prior,
        "data_change_refs": refs("DATACHG", ch.get("data_n", 0)),
        "denominator_change_refs": refs("DENCHG", ch.get("denom_n", 0)),
        "coverage_change_refs": refs("COVCHG", ch.get("coverage_n", 0)),
        "knowledge_change_refs": refs("KCHG", ch.get("knowledge_n", 0)),
        "rule_change_refs": refs("RULECHG", ch.get("rule_n", 0)),
        "mapping_change_refs": refs("MAPCHG", ch.get("mapping_n", 0)),
        "model_change_refs": refs("MODELCHG", ch.get("model_n", 0)),
        "method_change_refs": refs("METHCHG", ch.get("method_n", 0)),
        "population_change_refs": refs("POPCHG", ch.get("population_n", 0)),
        "visibility_change_refs": refs("VISCHG", ch.get("visibility_n", 0)),
        "mode_change_refs": refs("MODECHG", ch.get("mode_n", 0)),
        "cutoff_advance": _cutoff_advance(idx, ch),
        "r2_prior_ref_or_none": r2_prior,
        "r2_action": ch.get("r2_action"),
        "lineage_relation": ch.get("r2_lineage"),
        "carry_forward_state": "active" if ch.get("carry_forward") else "none",
        "claimed_clinical_change_kind": ch.get("claimed_kind"),
        "claimed_primary_change_cause": ch.get("claimed_cause"),
        "claimed_cutoff_state": ch.get("claimed_cutoff"),
        "data_change_kind": ch.get("data_kind"),
    }


def _visibility_decision(idx: int, spec: dict[str, Any],
                         member_refs: list[str],
                         members: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    member_by_ref = {m["member_ref"]: m for m in (members or [])}
    canonical_refs = (list(member_refs)
                      if len(set(member_refs)) != len(member_refs)
                      else sorted(set(member_refs)))
    hidden_members = spec.get("vis_hidden_members", 0)
    hidden_sites = spec.get("vis_hidden_sites", 0)
    evaluation = canonical_refs
    hidden = evaluation[:hidden_members]
    if spec.get("vis_hidden_dropped"):
        # hidden members dropped from evaluation instead of counted
        evaluation = evaluation[hidden_members:]
        projectable = evaluation
    elif spec.get("vis_hidden_omission"):
        # hidden refs omitted from the hidden set (no hidden list at all)
        projectable = evaluation[hidden_members:]
        hidden = []
    elif spec.get("vis_algebra_ok") is False:
        # declared algebra violation: hidden refs not a subset of evaluation
        projectable = evaluation[hidden_members:]
        hidden = evaluation[:hidden_members] + ["SYN-D10-RISK-EXTERNAL-001"]
    else:
        projectable = evaluation[hidden_members:]
    visible_n = len(projectable)
    eligible_n = len(evaluation)
    if spec.get("vis_algebra_ok") is False:
        visible_n = visible_n + 1
    dl_eligible = projectable[:spec.get("dl_n", 0)] if not spec.get("dl_violation") \
        else evaluation[:1]
    hidden_count = hidden_members
    if spec.get("vis_algebra_ok") is False and spec.get("vis_hidden_counts_bad"):
        hidden_count = hidden_count + 1
    projectable_sites = ([_site_ref(1)] if hidden_sites == 0 else [])
    projectable_pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in projectable if ref in member_by_ref
        and member_by_ref[ref]["subject_stable_id"]
        and member_by_ref[ref]["site_stable_id"] in projectable_sites
    })
    eligible_pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in dl_eligible if ref in member_by_ref
        and member_by_ref[ref]["subject_stable_id"]
        and member_by_ref[ref]["site_stable_id"] in projectable_sites
    })
    decision = {
        "blind_status": spec.get("blind_status", "blinded"),
        "audience_scope_id": f"SYN-D10-AUD-{idx:03d}",
        "evaluation_member_refs": evaluation,
        "projectable_member_refs": projectable,
        "hidden_member_refs": hidden,
        "hidden_reason_codes": ["visibility_restricted"] * len(hidden),
        "evaluation_site_refs": [_site_ref(1)],
        "projectable_site_refs": projectable_sites,
        "hidden_site_refs": [] if hidden_sites == 0 else [_site_ref(1)],
        "visible_n": visible_n,
        "eligible_n": eligible_n,
        "hidden_member_count": hidden_count,
        "hidden_site_count": hidden_sites,
        "rate_projection_state": spec.get("rate_state", "permitted"),
        "deep_link_eligible_member_refs": dl_eligible,
        "deep_link_eligible_site_refs": [] if spec.get("dl_violation") else
                                        [_site_ref(1)] * min(len(dl_eligible), 1),
        "hidden_set_omitted": spec.get("vis_hidden_omission", False),
        "deep_link_eligible_violation": spec.get("dl_violation", False),
        "treatment_inference_attempt": spec.get("blind_inference", False),
        "projectable_subject_site_pairs": [list(pair) for pair in projectable_pairs],
        "deep_link_eligible_subject_site_pairs": [list(pair)
                                                   for pair in eligible_pairs],
        "decision_id": "",
    }
    decision["decision_id"] = content_hash(decision, "decision_id")
    return decision


def _query_decision(idx: int, spec: dict[str, Any],
                    member_refs: list[str]) -> dict[str, Any]:
    q = spec.get("query", {})
    uncovered = q.get("uncovered", 7)
    covered = q.get("covered", 0)
    uncovered_explicit = "uncovered" in q
    member_refs = sorted(set(member_refs))
    covered_refs = member_refs[:covered]
    # Uncovered refs: the candidate member refs (generated by convention for
    # fanout-exceeded fixtures; real member refs otherwise).
    if uncovered == 0:
        uncovered_refs = []
    elif uncovered_explicit and uncovered > len(member_refs):
        uncovered_refs = [f"SYN-D10-RISK-{idx:03d}-{m:02d}"
                          for m in range(1, uncovered + 1)]
    elif covered > 0 and covered + uncovered < len(member_refs):
        # Deliberate Query redundancy attack fixture: preserve the truncated
        # submitted partition so the independent verifier can reject it.
        uncovered_refs = member_refs[covered:covered + uncovered]
    else:
        uncovered_refs = member_refs[covered:]
    covered_refs = sorted(set(covered_refs))
    uncovered_refs = sorted(set(uncovered_refs))
    member_query_ids = [sha256_text(canonical_json({"member_ref": ref}))
                        for ref in covered_refs]
    if spec.get("q_ids_mismatch"):
        # Keep the negative fixture structurally hash-shaped while breaking
        # the identity-to-member mapping; the verifier must reject it.
        member_query_ids = [sha256_text(canonical_json({
            "member_ref": f"SYN-D10-MQID-{idx:03d}-000"}))]
    # unit_member_set_hash must be the REAL recomputable hash over all unit
    # member refs (sorted-unique canonical encoding, contract section 11);
    # rehash-tamper fixtures carry a wrong hash instead.
    real_set_hash = sha256_text(canonical_json(sorted(member_refs)))
    if spec.get("rehash"):
        unit_hash = _content_sha(f"tampered-unitmembers:{idx:03d}")
    else:
        unit_hash = real_set_hash
    decision = {
        "decision": q.get("decision", "project_delta_present"),
        "covered_member_refs": covered_refs,
        "uncovered_member_refs": uncovered_refs,
        "member_query_content_identities": member_query_ids,
        "unit_member_set_hash": unit_hash,
        "coverage_proof_hash": "",
        "max_query_member_fanout": q.get("fanout", 100),
        "member_unlistable": q.get("unlistable", False),
        "pd_wording_state": q.get("pd", "not_pd"),
        "duplicate_query_attempt": spec.get("q_duplicate", False),
        "query_content_hash": "",
    }
    decision["coverage_proof_hash"] = sha256_text(canonical_json({
        "unit_member_refs": member_refs,
        "covered_member_refs": covered_refs,
        "uncovered_member_refs": uncovered_refs,
        "member_query_content_identities": member_query_ids,
    }))
    decision["query_content_hash"] = content_hash(decision, "query_content_hash")
    return decision


def _audience_text(idx: int, spec: dict[str, Any], *, alt: bool = False) -> dict[str, Any]:
    injection = spec.get("injection", False)
    finding_zh = ("发现 {n} 名已治疗受试者（同一口径）" if alt
                  else "发现 {n} 名受影响受试者（绝对量，分母口径见 denominator_context）")
    return {
        "audience_contract_id": f"SYN-D10-AC-{idx:03d}",
        "display_language": "zh-CN",
        "sentence_part_kind": "observed_finding",
        "basis_zh": "依据已接受的成员对象与可复算分母",
        "finding_zh": finding_zh,
        "action_zh": "建议结合中心/受试者记录核查（非正式结论）",
        "engineering_reference_attempt": injection,
        "injection_blocked": spec.get("injection_blocked", injection),
    }


def _deep_links(idx: int, spec: dict[str, Any],
                visibility: dict[str, Any],
                members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    kinds = spec.get("dl_kinds") or ["member"]
    member_by_ref = {m["member_ref"]: m for m in members}
    eligible_refs = list(visibility["deep_link_eligible_member_refs"])
    eligible_pairs = [tuple(pair) for pair in
                      visibility["deep_link_eligible_subject_site_pairs"]]
    for n in range(1, spec.get("dl_n", 0) + 1):
        kind = kinds[(n - 1) % len(kinds)]
        ref = eligible_refs[(n - 1) % len(eligible_refs)] if eligible_refs else None
        member = member_by_ref.get(ref) if ref else None
        if kind == "member":
            site_ref = member["site_stable_id"] if member else None
            subject_ref = member["subject_stable_id"] if member else None
            member_ref = ref
        elif kind == "site":
            site_ref = (visibility["deep_link_eligible_site_refs"] or
                        visibility["projectable_site_refs"] or [None])[0]
            subject_ref = None
            member_ref = None
        else:
            pair = eligible_pairs[(n - 1) % len(eligible_pairs)] \
                if eligible_pairs else (None, None)
            site_ref, subject_ref = pair[1], pair[0]
            member_ref = None
        out.append({"target_kind": kind, "site_ref": site_ref,
                    "subject_ref": subject_ref,
                    "member_object_ref": member_ref,
                    "visibility_decision_ref": visibility["decision_id"],
                    "return_state_key": f"SYN-D10-RET-{idx:03d}-{n}"})
    return out


def _model_evidence(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    model = spec.get("model")
    if model is None:
        return None
    role = model.get("role", "candidate_explanation")
    member_refs = sorted(set(m["member_ref"] for m in
                              _members(idx, spec)))
    source_refs = _locator_ids(idx, spec)
    source_pairs = [{
        "revision_id": f"SRC-REV-{idx:03d}-001",
        "content_hash": sha256_text(canonical_json({
            "revision_id": f"SRC-REV-{idx:03d}-001",
            "source_locators": source_refs})),
    }]
    permitted_leaf = ("model_candidate_only" if role == "candidate_explanation"
                      else "counterevidence_suggestion_only")
    core: dict[str, Any] = {
        "model_evidence_id": f"SYN-D10-MODEL-{idx:03d}",
        "role": role,
        "evaluation_content_identity": sha256_text(canonical_json({
            "project_ref": PROJECT_REF,
            "run_ref": RUN_REF,
            "snapshot_ref": SNAPSHOT_REF,
            "signal_kind": spec["kind"],
            "member_refs": member_refs,
            "source_revision_content_pairs": source_pairs,
        })),
        "input_content_hash": sha256_text(canonical_json({
            "input_schema": TYPED_INPUT_SCHEMA,
            "project_ref": PROJECT_REF,
            "member_refs": member_refs,
            "source_revision_content_pairs": source_pairs,
        })),
        "source_revision_content_pairs": source_pairs,
        "source_refs": source_refs,
        "model_id": f"SYN-D10-MODEL-ID-{idx:03d}",
        "model_version": "SYN-D10-MODEL-V1",
        "independent_context_hash": sha256_text(canonical_json({
            "project_ref": PROJECT_REF,
            "run_ref": RUN_REF,
            "snapshot_ref": SNAPSHOT_REF,
            "signal_kind": spec["kind"],
        })),
        "ensemble_id": f"SYN-D10-ENSEMBLE-{idx:03d}",
        "ensemble_size": model.get("ensemble_size", 1),
        "member_analysis_refs": sorted(set(_member_ids(idx, 2, "MA"))),
        "permitted_leaf": permitted_leaf,
        "member_analysis_ref_set_hash": sha256_text(canonical_json(
            sorted(set(_member_ids(idx, 2, "MA"))))),
        "output_identity": f"SYN-D10-MODEL-OUTPUT-{idx:03d}",
        "adjudication_state": "accepted",
    }
    core["model_binding_hash"] = sha256_text(canonical_json(core))
    core["output_hash"] = sha256_text(canonical_json({
        "output_identity": core["output_identity"],
        "model_binding_hash": core["model_binding_hash"],
        "permitted_leaf": permitted_leaf,
        "adjudication_state": "accepted",
    }))
    return core


def _safety_context(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    safety = spec.get("safety")
    if safety is None:
        return None
    missing = safety.get("missing", [])
    return {
        "context_id": f"SYN-D10-SAFEC-{idx:03d}",
        "context_complete": safety.get("complete", True),
        "exposure_definition_ref": None if "exposure" in missing else f"SYN-D10-EXPDEF-{idx:03d}",
        "coding_dictionary_ref": None if "coding" in missing else f"SYN-D10-MEDDRA-{idx:03d}",
        "severity_scale_ref": None if "severity" in missing else f"SYN-D10-CTCAE-{idx:03d}",
        "risk_window_ref": None if "risk_window" in missing else f"SYN-D10-RW-{idx:03d}",
        "descriptive_monitoring_only": True,
    }


def _efficacy_context(idx: int, spec: dict[str, Any], *, project_ref: str,
                      run_ref: str) -> dict[str, Any] | None:
    efficacy = spec.get("efficacy")
    if efficacy is None:
        return None
    missing = efficacy.get("missing", [])
    treatment_ok = not (spec.get("treatment_required", False)
                        and not spec.get("assignment_present", True))
    assignment_ref = None
    authority_ref = f"SYN-D10-TRAUTH-{idx:03d}" if treatment_ok else None
    mapping_hash = None
    if spec.get("assignment_present", False):
        mapping_hash = sha256_text(canonical_json({
            "authority": authority_ref, "project": project_ref, "run": run_ref,
        }))
        assignment_ref = mapping_hash
    return {
        "context_id": f"SYN-D10-EFFC-{idx:03d}",
        "context_complete": efficacy.get("complete", True),
        "endpoint_definition_ref": None if "endpoint" in missing else f"SYN-D10-ENDP-{idx:03d}",
        "estimand_ref": None if "estimand" in missing else f"SYN-D10-EST-{idx:03d}",
        "missing_data_rule_ref": None if "missing" in missing else f"SYN-D10-MDR-{idx:03d}",
        "intercurrent_event_rule_ref": None if "intercurrent" in missing else
                                       f"SYN-D10-ICR-{idx:03d}",
        "treatment_role_authority_ref": authority_ref,
        "treatment_assignment_exposure_identity_ref": assignment_ref,
        "treatment_role_required": spec.get("treatment_required", False),
        "blind_visibility_contract_ref": f"SYN-D10-BVC-{idx:03d}",
        "descriptive_monitoring_only": True,
        "estimate_kind": spec.get("estimate"),
        "treatment_assignment_mapping_hash": mapping_hash,
    }


def _rule_hit(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    sources = spec.get("sources", ["typed_member"])
    ce_matched = spec.get("ce_matched", 0)
    ce_declared = spec.get("ce_declared", 1)
    return {
        "positive_rule_ref": f"SYN-D10-RULE-POS-{idx:03d}",
        "hit_state": spec.get("hit", "hit"),
        "evidence_sources": sources,
        "counterevidence_matched_refs": _member_ids(idx, ce_matched, "CER"),
        "counterevidence_declared_refs": _member_ids(idx, ce_declared, "CER"),
    }


def _hotspot(idx: int, spec: dict[str, Any]) -> dict[str, Any] | None:
    if not spec.get("hotspot"):
        return None
    return {
        "hotspot_member_refs": [f"SYN-D10-RISK-{idx:03d}-01"],
        "hidden_in_display": spec.get("hotspot_hidden", False),
    }


def _count_layers(spec: dict[str, Any]) -> dict[str, Any]:
    layers = spec.get("count_layers", ["individual_risk"])
    return {
        "layers_in_common_numerator": layers,
        "mixed": len(set(layers)) > 1,
    }


def _numeric_policy(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    precision = 2 if spec.get("precision_alt") else 1
    return {
        "policy_id": f"SYN-D10-NUM-{idx:03d}",
        "allowed_estimate_kinds": list(ESTIMATE_KINDS),
        "decimal_context": "decimal(10,4)",
        "rounding_mode": "half_up",
        "display_precision": precision,
        "subject_time_unit": "day",
        "exposure_time_unit": "subject_day",
        "overlap_policy": "resolve_by_authority",
    }


def _mutation_context(spec: dict[str, Any], variant_id: str | None = None,
                      base_fixture_id: str | None = None) -> dict[str, Any]:
    return {
        "mutation_class": spec.get("mc", "none"),
        "desc": spec.get("desc", ""),
        "variant_id": variant_id,
        "base_fixture_id": base_fixture_id,
    }


def _anti_overfit_variant(spec: dict[str, Any], idx: int) -> dict[str, Any] | None:
    base = spec.get("anti_base")
    if base is None:
        return None
    variant = spec.get("variant", 1)
    changes = {
        "table_field_rename": ("evidence_refs", "synthetic_source/dataset_*.json",
                               "synthetic_source/alt_dataset_*.json"),
        "input_order_shuffle": ("members order", "ascending", "descending"),
        "version_field_change": ("mode_contract_version", "SYN-D10-MODE-001",
                                 "SYN-D10-MODE-001-ALT"),
        "zh_label_change": ("finding_zh", "发现 {n} 名受影响受试者",
                            "发现 {n} 名已治疗受试者（同一口径）"),
        "display_precision_change": ("numeric_policy display_precision", "1", "2"),
        "evidence_row_change": ("evidence_refs row_or_cell_ref", "sheet:1;row:N",
                                "sheet:2;row:N+1"),
        "audience_contract_id_change": ("audience_contract ids", "SYN-D10-AC-*",
                                        "SYN-D10-AC-*-ALT"),
        "envelope_id_change": ("envelope_id", "SYN-D10-ENV-*",
                               "SYN-D10-ENV-*-ALT"),
    }[base]
    base_fixture_id = f"D10-FIX-{idx - 1:03d}" if variant == 2 else None
    return {
        "base_fixture_id": base_fixture_id,
        "semantic_equivalence_ref": f"SYN-D10-SEMEQ-{base}-{idx:03d}",
        "surface_changes": [{
            "changed_token": changes[0],
            "from_value": changes[1],
            "to_value": changes[2],
        }],
        "variant_id": variant,
    }


def _evidence_refs(idx: int, n: int = 2, *, dup_locator: bool = False,
                   file_alt: bool = False, row_alt: bool = False) -> list[dict[str, Any]]:
    refs = []
    for m in range(1, n + 1):
        locator_id = f"SYN-D10-LOC-{idx:03d}-{m:02d}"
        if dup_locator and m == 2:
            locator_id = f"SYN-D10-LOC-{idx:03d}-01"
        source_file = (f"synthetic_source/alt_dataset_{idx:03d}.json"
                       if file_alt else
                       f"synthetic_source/dataset_{idx:03d}.json")
        row_ref = (f"sheet:2;row:{m + 1}" if row_alt else f"sheet:1;row:{m}")
        refs.append({
            "locator_id": locator_id,
            "locator_kind": "synthetic_file",
            "source_file": source_file,
            "row_or_cell_ref": row_ref,
            "lineage_ref": f"SYN-D10-LIN-{idx:03d}-{m:02d}",
        })
    return refs


def _audience_contract(idx: int, spec: dict[str, Any]) -> dict[str, Any]:
    suffix = "-ALT" if spec.get("audience_id_alt") else ""
    return {
        "audience_contract_id": f"SYN-D10-AC-{idx:03d}{suffix}",
        "audience_scope_id": f"SYN-D10-AUD-{idx:03d}{suffix}",
        "display_language": "zh-CN",
        "blind_status": spec.get("blind_status", "blinded"),
        "lexicon_ref": f"SYN-D10-LEX-{idx:03d}",
        "forbidden_internal_terms": ["正式安全性信号", "确证治疗效果", "优效",
                                     "非劣", "获益-风险裁决", "中心质量差",
                                     "中心质量好", "typed handoff", "candidate"],
        "injection_blocked": spec.get("injection_blocked", spec.get("injection", False)),
    }


def _source_revision_pairs(idx: int, spec: dict[str, Any]) -> list[dict[str, Any]]:
    def pair(rid: str) -> dict[str, Any]:
        # revision content hash is bound to the revision's typed content
        # anchors (the accepted source locator set), never to the id alone.
        return {"revision_id": rid,
                "content_hash": sha256_text(canonical_json({
                    "revision_id": rid,
                    "source_locators": _locator_ids(idx, spec)}))}
    pairs = [pair(f"SRC-REV-{idx:03d}-001")]
    if spec.get("envelope_ok", True) is False:
        pairs.append(pair("SRC-REV-EXTERNAL-001"))
    if spec.get("dup_revision"):
        # duplicate revision id (same recomputable content hash): the
        # duplicate-id violation is the tamper, not a hash mismatch.
        pairs.append(pair(f"SRC-REV-{idx:03d}-001"))
    return pairs


def _locator_ids(idx: int, spec: dict[str, Any]) -> list[str]:
    ids = sorted({f"SYN-D10-LOC-{idx:03d}-01", f"SYN-D10-LOC-{idx:03d}-02"})
    if spec.get("dup_locator"):
        ids = [f"SYN-D10-LOC-{idx:03d}-01"]
    return ids


# ---------------------------------------------------------------------------
# Case assembler: spec -> full typed_input (EXACT keys)
# ---------------------------------------------------------------------------
def build_typed_input(spec: dict[str, Any], idx: int, *, alt: bool = False) -> dict[str, Any]:
    # Identity base: anti-overfit pairs share one accepted identity; every
    # ref/identity-bearing value derives from it (never from the case index).
    ridx = int(spec.get("identity_idx") or idx)
    members = _members(ridx, spec, alt=alt)
    if spec.get("members_reversed"):
        members = list(reversed(members))
    member_refs = [m["member_ref"] for m in members]
    unique_member_count = len(set(member_refs))
    change = _change_decision(ridx, spec)
    visibility_decision = _visibility_decision(ridx, spec, member_refs, members)
    envelope_id = f"SYN-D10-ENV-{ridx:03d}"
    if spec.get("envelope_id_alt"):
        envelope_id = f"SYN-D10-ENV-{ridx:03d}-ALT"
    return {
        "input_schema": TYPED_INPUT_SCHEMA,
        "envelope_id": envelope_id,
        "project_ref": _project_ref(alt=alt),
        "run_ref": RUN_REF,
        "snapshot_ref": SNAPSHOT_REF,
        "source_revision_content_pairs": _source_revision_pairs(ridx, spec),
        "project_scope_binding": _scope_binding(ridx, spec, alt=alt),
        "mode_contract": _mode_contract(ridx, spec,
                                        alt=spec.get("mode_version_alt", False)),
        "signal_definition": _signal_definition(ridx, spec),
        "legal_matrix_row": _legal_matrix_row(ridx, spec),
        "expected_set": _expected_set(spec),
        "analysis_windows": _windows(ridx, spec),
        "stratum": _stratum(ridx, spec),
        "comparison_gate": _comparison_gate(ridx, spec),
        "window_pair_gate": _window_pair_gate(ridx, spec),
        "site_ledger": _site_ledger(ridx, spec, alt=alt),
        "members": members,
        "numerator_ledger": {
            "individual_risk_count": spec.get(
                "individual", spec.get("num", {}).get("subject", 7)),
            "center_pattern_count": spec.get("pattern", 0),
            "affected_subject_count": spec.get("num", {}).get("subject", 7),
            "event_or_outcome_count": spec.get("num", {}).get("event", 9),
            "affected_site_count": spec.get("num", {}).get("site", 3),
            "numerator_member_count": unique_member_count,
        },
        "measure_origin_binding": _measure_origin_binding(ridx, spec),
        "denominator": _denominator(ridx, spec, alt=alt),
        "time_segments": _time_segments(ridx, spec, alt=alt),
        "opportunity": _opportunity(ridx, spec),
        "analysis_population": _analysis_population(ridx, spec),
        "coverage": _coverage(ridx, spec),
        "change_decision": change,
        "visibility_decision": visibility_decision,
        "query_decision": _query_decision(ridx, spec, member_refs),
        "audience_text": _audience_text(ridx, spec,
                                        alt=spec.get("zh_label_alt", False)),
        "deep_links": _deep_links(ridx, spec, visibility_decision, members),
        "model_evidence": _model_evidence(ridx, spec),
        "safety_context": _safety_context(ridx, spec),
        "efficacy_context": _efficacy_context(
            ridx, spec, project_ref=_project_ref(alt=alt), run_ref=RUN_REF),
        "rule_hit": _rule_hit(ridx, spec),
        "hotspot": _hotspot(ridx, spec),
        "count_layers": _count_layers(spec),
        "evaluation_limits": {
            "small_sample": spec.get("small", False),
            "limited_evidence": spec.get("limited", False),
            "limited_reason": spec.get("limited_reason"),
        },
        "numeric_policy": _numeric_policy(ridx, spec),
        "mutation_context": _mutation_context(spec),
        "anti_overfit_variant": _anti_overfit_variant(spec, ridx),
        "evidence_refs": _evidence_refs(ridx,
                                        dup_locator=spec.get("dup_locator", False),
                                        file_alt=spec.get("evidence_file_alt", False),
                                        row_alt=spec.get("evidence_row_alt", False)),
    }


def build_case_row(typed: dict[str, Any], spec: dict[str, Any], idx: int) -> dict[str, Any]:
    fixture_id = f"D10-FIX-{idx:03d}"
    case: dict[str, Any] = {
        "case_id": f"D10-CASE-{idx:03d}",
        "primary_partition": spec["partition"],
        "family_id": spec["family"],
        "grain": spec.get("grain", "project"),
        "owner_route": spec["owner"],
        "clinical_claim_token": spec["token"],
        "disposition": spec["disposition"],
        "fixture_id": fixture_id,
        "fixture_hash": "",
        "oracle_case_id": f"D10-ORACLE-{idx:03d}",
        "manifest_case_id": f"D10-MANIFEST-{idx:03d}",
        "expected_leaf_set": None,
        "expected_trace_leaf_set": None,
        "expected_source_leaf_set": None,
        "mutation_class": spec.get("mc", "none"),
        "audience_contract": _audience_contract(idx, spec),
        "typed_input": typed,
    }
    core = {key: item for key, item in case.items() if key != "fixture_hash"}
    case["fixture_hash"] = content_hash(core, "fixture_hash")
    return case


# ---------------------------------------------------------------------------
# Partition builders (contract section 15 floors). Each spec is deterministic;
# ids are derived from the case index so two fresh generations are
# byte-identical. `disposition` is the DECLARED label; the independent oracle
# derives the expected outcome from typed facts (never from this field).
# ---------------------------------------------------------------------------
def _base_spec(partition: str, family: str, kind: str, token: str, owner: str,
               disposition: str, mc: str, desc: str, **kw: Any) -> dict[str, Any]:
    spec = {
        "partition": partition,
        "family": family,
        "kind": kind,
        "token": token,
        "owner": owner,
        "disposition": disposition,
        "mc": mc,
        "desc": desc,
        "attack_ids": [mc] if mc != "none" else [],
    }
    spec.update(kw)
    return spec


def _owned(partition: str, family: str, kind: str, disposition: str, mc: str,
           desc: str, **kw: Any) -> dict[str, Any]:
    token = kw.pop("token", "d10_" + kind)
    return _base_spec(partition, family, kind, token, "evaluate_and_own",
                      disposition, mc, desc, **kw)


def build_p01_specs() -> list[dict[str, Any]]:
    """5 signal kinds x 12: five dispositions, counterevidence, FP, FN,
    hidden, replay, comparison gate, window-pair gate."""
    rows: list[dict[str, Any]] = []
    for k, kind in enumerate(SIGNAL_KINDS):
        base = 1 + k * 12
        def make(idx: int, family: str, disposition: str, mc: str, desc: str,
                 **kw: Any) -> dict[str, Any]:
            return _owned("p01_signal_kind_disposition", family, kind, disposition,
                          mc, desc, **kw)
        rows.append(make(base, "d10_disposition_positive", "positive", "none",
                         "complete evaluation, rule hit, counterevidence insufficient",
                         hit="hit", ce_declared=1, ce_matched=0))
        rows.append(make(base + 1, "d10_disposition_negative", "negative", "none",
                         "complete evaluation, no rule hit",
                         hit="no_hit"))
        rows.append(make(base + 2, "d10_disposition_boundary", "boundary", "none",
                         "single subject / small sample -> boundary clue",
                         hit="hit", ce_declared=1, ce_matched=0, small=True,
                         num={"subject": 1, "event": 1, "member": 1, "site": 1},
                         pattern=0, individual=1))
        rows.append(make(base + 3, "d10_disposition_not_applicable", "not_applicable",
                         "none", "ModeContract design clause proves not applicable",
                         hit="hit", design_applicable="not_applicable"))
        rows.append(make(base + 4, "d10_disposition_not_evaluable", "not_evaluable",
                         "required_l1_hole",
                         "required L1 not_evaluable must not become zero/negative",
                         hit="no_hit",
                         cov=[[{
                             "project_risk_distribution": "D01",
                             "cross_site_pattern": "D09",
                             "project_time_trend": "D09",
                             "project_safety_trend": "D07",
                             "project_efficacy_trend": "D06",
                         }[kind], "covered", "not_evaluable"]],
                         attack_ids=["required_l1_hole"]))
        rows.append(make(base + 5, "d10_counterevidence_explains", "negative", "none",
                         "counterevidence fully explains -> negative",
                         hit="hit", ce_declared=2, ce_matched=2))
        rows.append(make(base + 6, "d10_false_positive_trap", "boundary", "none",
                         "p-value only cannot create positive",
                         hit="hit", sources=["pvalue"]))
        rows.append(make(base + 7, "d10_false_negative_trap", "not_evaluable",
                         "zero_event_empty_denominator_negative",
                         "zero events / closed-zero denominator cannot be negative",
                         hit="no_hit", den_state="closed_zero", den_value=0,
                         attack_ids=["zero_event_empty_denominator_negative"]))
        rows.append(make(base + 8, "d10_hidden_counted", "positive", "none",
                         "hidden members still count in evaluation; visibility qualified",
                         hit="hit", ce_declared=1, ce_matched=0,
                         vis_hidden_members=2, rate_state="qualified"))
        rows.append(make(base + 9, "d10_replay_stable", "positive", "none",
                         "same-window replay -> same identity, no change unit",
                         hit="hit", ce_declared=1, ce_matched=0,
                         change={"basis": "full", "comparison_state": "initial_full",
                                 "cutoff_state": "same_window",
                                 "cutoff_predicate": False,
                                 "cutoff_policy_equal": True}))
        rows.append(make(base + 10, "d10_comparison_gate", "comparison_set_gate", "none",
                         "insufficient eligible sites -> control-plane gate, zero units",
                         es_state="control_plane_gate", gate_kind="comparison_set_gate",
                         gate_reasons=["comparison_insufficient_sites"],
                         comp_state="insufficient_sites", eligible_sites=2,
                         required_sites=3))
        rows.append(make(base + 11, "d10_window_pair_gate", "window_pair_gate", "none",
                         "single window -> control-plane window-pair gate, zero units",
                         es_state="control_plane_gate", gate_kind="window_pair_gate",
                         gate_reasons=["window_pair_insufficient_windows"],
                         wins=1, pair_state="insufficient_windows", unique_windows=1))
    return rows


def build_p02_specs() -> list[dict[str, Any]]:
    """owner routing / 越权 / consume-only / handoff-only / zero medical output."""
    p = "p02_owner_routing_zero_medical"
    rows = [
        _base_spec(p, "d10_consume_d09_plain", "cross_site_pattern",
                   "d09_within_site_pattern", "consume_only", "routing_gate",
                   "none", "D09 pattern consume-only: zero D10 medical units",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_consume_only"]),
        _base_spec(p, "d10_consume_d09_descendants", "cross_site_pattern",
                   "d09_within_site_pattern", "consume_only", "routing_gate",
                   "d09_parent_descendant_duplication",
                   "D09 parent pattern with descendants must not form a D10 numerator",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_consume_only"],
                   pattern=1, descendants=2,
                   attack_ids=["d09_parent_descendant_duplication"]),
        _base_spec(p, "d10_consume_d09_recompute", "cross_site_pattern",
                   "d09_within_site_pattern", "consume_only", "routing_gate",
                   "d09_within_site_trend_recompute",
                   "D10 must never recompute a D09 single-site trend",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_consume_only"],
                   count_layers=["d09_within_site_trend", "center_pattern"],
                   attack_ids=["d09_within_site_trend_recompute"]),
        _base_spec(p, "d10_consume_d01_plain", "project_risk_distribution",
                   "d01_d08_individual_claim", "consume_only", "routing_gate",
                   "none", "individual claim consume-only: zero D10 units",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_consume_only"]),
        _base_spec(p, "d10_consume_d01_legal_row_mismatch",
                   "project_risk_distribution", "d10_project_risk_distribution",
                   "consume_only", "integrity_gate", "legal_row_mismatch",
                   "consume-only row on an ownable token -> legal-row mismatch",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["legal_row_consume_only_ownable"],
                   attack_ids=["legal_row_mismatch"]),
        _base_spec(p, "d10_consume_d01_scope_mismatch", "project_risk_distribution",
                   "d01_d08_individual_claim", "consume_only", "routing_gate",
                   "none", "wrong scope while consuming (consume-only gates first)",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_consume_only"], scope_eq="mismatch"),
        _base_spec(p, "d10_handoff_benefit_risk", "project_safety_trend",
                   "formal_benefit_risk_conclusion", "handoff_only", "handoff_gate",
                   "none", "formal benefit-risk is handoff-only, zero D10 units",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_handoff_only"]),
        _base_spec(p, "d10_handoff_confirmatory", "project_efficacy_trend",
                   "confirmatory_treatment_effect", "handoff_only", "handoff_gate",
                   "none", "confirmatory treatment effect is handoff-only",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_handoff_only"]),
        _base_spec(p, "d10_handoff_site_quality", "cross_site_pattern",
                   "site_quality_judgment", "handoff_only", "handoff_gate",
                   "none", "site quality judgment is handoff-only",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_handoff_only"]),
        _base_spec(p, "d10_handoff_ownable_attempt", "project_safety_trend",
                   "d10_project_safety_trend", "handoff_only", "integrity_gate",
                   "legal_row_mismatch",
                   "handoff-only row on ownable token -> legal-row mismatch",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["legal_row_handoff_only_ownable"],
                   attack_ids=["legal_row_mismatch"]),
        _base_spec(p, "d10_unresolved_token", "project_risk_distribution",
                   "unresolved", "routing_gate", "routing_gate", "none",
                   "unresolved claim token -> routing gate, zero medical units",
                   es_state="routing_gate_unresolved", gate_kind="routing_gate",
                   gate_reasons=["claim_token_unresolved"]),
        _base_spec(p, "d10_unresolved_injection", "project_risk_distribution",
                   "unresolved", "routing_gate", "routing_gate",
                   "audience_engineering_injection",
                   "unresolved + engineering reference attempt in audience text",
                   es_state="routing_gate_unresolved", gate_kind="routing_gate",
                   gate_reasons=["claim_token_unresolved"], injection=True,
                   injection_blocked=True,
                   attack_ids=["audience_engineering_injection"]),
        _owned(p, "d10_unauthorized_d09", "cross_site_pattern", "integrity_gate",
               "legal_row_mismatch",
               "evaluate_and_own on a consume-only token is unauthorized",
               es_state="admitted", gate_kind="integrity_gate",
               gate_reasons=["owner_route_unauthorized"], token="d09_within_site_pattern",
               attack_ids=["legal_row_mismatch"]),
        _owned(p, "d10_unauthorized_d01", "project_risk_distribution",
               "integrity_gate", "legal_row_mismatch",
               "evaluate_and_own on individual claim token is unauthorized",
               es_state="admitted", gate_kind="integrity_gate",
               gate_reasons=["owner_route_unauthorized"], token="d01_d08_individual_claim",
               attack_ids=["legal_row_mismatch"]),
        _owned(p, "d10_unauthorized_benefit_risk", "project_safety_trend",
               "integrity_gate", "legal_row_mismatch",
               "evaluate_and_own on formal benefit-risk is unauthorized",
               es_state="admitted", gate_kind="integrity_gate",
               gate_reasons=["owner_route_unauthorized"],
               token="formal_benefit_risk_conclusion",
               attack_ids=["legal_row_mismatch"]),
        _owned(p, "d10_unauthorized_confirmatory", "project_efficacy_trend",
               "integrity_gate", "legal_row_mismatch",
               "evaluate_and_own on confirmatory effect is unauthorized",
               es_state="admitted", gate_kind="integrity_gate",
               gate_reasons=["owner_route_unauthorized"],
               token="confirmatory_treatment_effect",
               attack_ids=["legal_row_mismatch"]),
        _owned(p, "d10_legal_row_kind_mismatch", "project_risk_distribution",
               "integrity_gate", "legal_row_mismatch",
               "signal definition kind disagrees with legal matrix row",
               legal_match=False, attack_ids=["legal_row_mismatch"]),
        _owned(p, "d10_envelope_revision_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "envelope source revision pairs not a closed subset",
               envelope_ok=False, gate_kind="global_gate",
               gate_reasons=["envelope_source_revision_not_closed"]),
        _owned(p, "d10_global_scope_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "project scope binding equality mismatch",
               scope_eq="mismatch", gate_kind="global_gate",
               gate_reasons=["scope_binding_mismatch"]),
        _owned(p, "d10_global_admission_failed", "project_risk_distribution",
               "global_gate", "none",
               "global admission gate failure -> zero medical units",
               es_state="global_admission_failed", gate_kind="global_gate",
               gate_reasons=["global_expected_set_failed"]),
        _owned(p, "d10_identity_unstable", "project_risk_distribution",
               "global_gate", "none",
               "site/subject identity state unstable -> global gate",
               identity_state="unstable", gate_kind="global_gate",
               gate_reasons=["identity_state_unstable"]),
        _owned(p, "d10_blind_authority_missing", "project_efficacy_trend",
               "global_gate", "none",
               "blind/visibility authority unresolved -> global gate",
               blind_status="blinded", es_state="global_admission_failed",
               gate_kind="global_gate",
               gate_reasons=["blind_authority_missing"]),
        _owned(p, "d10_zero_medical_routing", "project_risk_distribution",
               "routing_gate", "none",
               "expected-set routed consume-only -> routing gate, zero units",
               es_state="routed_consume_only", gate_kind="routing_gate",
               gate_reasons=["token_consume_only"]),
        _owned(p, "d10_zero_medical_unresolved", "project_risk_distribution",
               "routing_gate", "none",
               "expected-set unresolved -> routing gate, zero units",
               es_state="routing_gate_unresolved", gate_kind="routing_gate",
               gate_reasons=["claim_token_unresolved"]),
    ]
    return rows


def build_p03_specs() -> list[dict[str, Any]]:
    """project/site/subject/member identity, wrong scope, duplicate,
    same-origin ambiguity."""
    p = "p03_identity_scope_duplicate"
    rows = [
        _owned(p, "d10_member_wrong_project", "project_risk_distribution",
               "not_evaluable", "cross_project_scope",
               "member resolves to another project -> unit blocked",
               member_wrong_project=True, attack_ids=["cross_project_scope"]),
        _owned(p, "d10_member_wrong_site", "project_risk_distribution",
               "not_evaluable", "none",
               "member resolves to a site outside the project scope",
               member_wrong_site=True),
        _owned(p, "d10_member_wrong_subject", "project_risk_distribution",
               "not_evaluable", "none",
               "member resolves to a subject outside the project scope",
               member_wrong_subject=True),
        _owned(p, "d10_member_unresolvable", "project_risk_distribution",
               "not_evaluable", "none",
               "member identity unresolvable -> blocked before medical computation",
               member_unresolvable=True),
        _owned(p, "d10_duplicate_member_ref", "project_risk_distribution",
               "integrity_gate", "none",
               "duplicate member refs with conflicting content rejected",
               dup_member_ref=True, gate_kind="integrity_gate",
               gate_reasons=["duplicate_member_ref"]),
        _owned(p, "d10_scope_site_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "site-scope binding equality mismatch",
               scope_eq="mismatch", scope_type="site", gate_kind="global_gate",
               gate_reasons=["scope_binding_mismatch"]),
        _owned(p, "d10_scope_subject_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "subject-scope binding equality mismatch",
               scope_eq="mismatch", scope_type="subject", gate_kind="global_gate",
               gate_reasons=["scope_binding_mismatch"]),
        _owned(p, "d10_envelope_hash_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "envelope scope binding hash disagrees",
               scope_eq="mismatch", gate_kind="global_gate",
               gate_reasons=["envelope_scope_hash_mismatch"]),
        _owned(p, "d10_revision_pair_mispaired", "project_risk_distribution",
               "global_gate", "none",
               "revision/content pairs mispaired",
               envelope_ok=False, gate_kind="global_gate",
               gate_reasons=["revision_content_pair_mismatch"]),
        _owned(p, "d10_origin_verified_single_plane", "project_safety_trend",
               "positive", "none",
               "verified same-origin risk+measure -> ONE numerator plane",
               origin={"decision": "all_verified_same_origin", "verified": 3},
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}),
        _owned(p, "d10_origin_verified_double_count", "project_safety_trend",
               "integrity_gate", "d07_risk_safety_measure_same_origin",
               "verified same-origin counted on two planes -> integrity",
               origin={"decision": "all_verified_same_origin", "verified": 3,
                       "plane_state": "duplicate"},
               gate_kind="integrity_gate",
               gate_reasons=["same_origin_double_count"],
               safety={"complete": True},
               attack_ids=["d07_risk_safety_measure_same_origin"]),
        _owned(p, "d10_origin_ambiguous", "project_safety_trend",
               "not_evaluable", "none",
               "same-origin ambiguity -> never silently merged",
               origin={"decision": "ambiguous", "ambiguous": 2},
               safety={"complete": True}),
        _owned(p, "d10_origin_mixed_leaves", "project_safety_trend",
               "boundary", "none",
               "mixed verified+distinct -> separate leaves, limited",
               origin={"decision": "mixed_verified_and_distinct", "verified": 2,
                       "distinct": 2},
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}),
        _owned(p, "d10_origin_wrong_scope", "project_safety_trend",
               "not_evaluable", "none",
               "origin binding resolves outside scope",
               origin={"decision": "wrong_scope"},
               safety={"complete": True}),
        _owned(p, "d10_origin_not_evaluable", "project_safety_trend",
               "not_evaluable", "none",
               "origin not evaluable -> blocked",
               origin={"decision": "not_evaluable"},
               safety={"complete": True}),
        _owned(p, "d10_parent_descendant_common_numerator", "cross_site_pattern",
               "integrity_gate", "d09_parent_descendant_duplication",
               "D09 parent pattern + descendants in one common numerator",
               pattern=1, descendants=2, desc_in_numerator=True,
               gate_kind="integrity_gate",
               gate_reasons=["d09_parent_descendant_duplication"],
               attack_ids=["d09_parent_descendant_duplication"]),
        _owned(p, "d10_parent_descendant_separate_leaves", "cross_site_pattern",
               "positive", "none",
               "D09 parent and descendants in INDEPENDENT display leaves only",
               hit="hit", ce_declared=1, ce_matched=0,
               pattern=1, individual=5, descendants=5,
               num={"subject": 5, "event": 5, "member": 6, "site": 3}),
        _owned(p, "d10_origin_cross_envelope", "project_safety_trend",
               "not_evaluable", "measure_origin_cross_envelope_mixed",
               "origin binding references a member outside the envelope",
               origin={"decision": "wrong_scope"},
               safety={"complete": True},
               attack_ids=["measure_origin_cross_envelope_mixed"]),
        _owned(p, "d10_origin_mixed_with_ambiguous", "project_safety_trend",
               "not_evaluable", "measure_origin_cross_envelope_mixed",
               "mixed verified+distinct+ambiguous -> ambiguous forces not_evaluable",
               origin={"decision": "ambiguous", "verified": 1, "distinct": 1,
                       "ambiguous": 1},
               safety={"complete": True},
               attack_ids=["measure_origin_cross_envelope_mixed"]),
        _owned(p, "d10_same_origin_safety_d07", "project_safety_trend",
               "integrity_gate", "d07_risk_safety_measure_same_origin",
               "D07 risk and safety measure same origin double-counted",
               origin={"decision": "all_verified_same_origin", "verified": 2,
                       "plane_state": "duplicate"},
               gate_kind="integrity_gate",
               gate_reasons=["same_origin_double_count"],
               safety={"complete": True},
               attack_ids=["d07_risk_safety_measure_same_origin"]),
        _owned(p, "d10_site_identity_merged", "project_risk_distribution",
               "global_gate", "none",
               "site identity merged -> identity not stable",
               identity_state="unstable", gate_kind="global_gate",
               gate_reasons=["site_identity_merged"]),
        _owned(p, "d10_subject_identity_split", "project_risk_distribution",
               "global_gate", "none",
               "subject identity split -> identity not stable",
               identity_state="unstable", gate_kind="global_gate",
               gate_reasons=["subject_identity_split"]),
        _owned(p, "d10_site_ledger_wrong_project", "cross_site_pattern",
               "global_gate", "cross_project_scope",
               "site ledger bound to another project",
               envelope_ok=False, gate_kind="global_gate",
               gate_reasons=["site_ledger_wrong_project"],
               attack_ids=["cross_project_scope"]),
        _owned(p, "d10_member_identity_reuse", "project_risk_distribution",
               "integrity_gate", "none",
               "same member identity reused with different content",
               dup_member_ref=True, gate_kind="integrity_gate",
               gate_reasons=["duplicate_content_identity"]),
    ]
    return rows


def build_p04_specs() -> list[dict[str, Any]]:
    """numerator / denominator / subject-time / exposure-time / opportunity /
    analysis population."""
    p = "p04_numerator_denominator_time"
    rows = [
        _owned(p, "d10_subject_event_separate", "project_risk_distribution",
               "positive", "none",
               "subject count and event count reported separately",
               hit="hit", ce_declared=1, ce_matched=0,
               num={"subject": 5, "event": 9, "member": 5, "site": 2}),
        _owned(p, "d10_subject_event_mixed", "project_risk_distribution",
               "integrity_gate", "none",
               "subject and event counts merged into one numerator",
               count_layers=["individual_risk", "event_or_outcome"],
               gate_kind="integrity_gate", gate_reasons=["numerator_discipline"]),
        _owned(p, "d10_planes_separate", "project_risk_distribution",
               "positive", "none",
               "pattern and individual planes in independent display leaves",
               hit="hit", ce_declared=1, ce_matched=0,
               pattern=1, individual=5, descendants=5,
               num={"subject": 5, "event": 5, "member": 6, "site": 3}),
        _owned(p, "d10_planes_common_numerator", "project_risk_distribution",
               "integrity_gate", "cross_layer_count_mixing",
               "D09 pattern + individual risk + D10 signal summed as total risk",
               count_mixed=True, gate_kind="integrity_gate",
               gate_reasons=["cross_layer_count_mixing"],
               count_layers=["center_pattern", "individual_risk", "project_signal"],
               attack_ids=["cross_layer_count_mixing"]),
        _owned(p, "d10_den_enrolled", "project_risk_distribution",
               "positive", "none", "enrolled-subjects denominator",
               den_kind="enrolled_subjects", den_value=150,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_den_treated", "project_risk_distribution",
               "positive", "none", "treated-subjects denominator",
               den_kind="treated_subjects", den_value=126,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_den_safety_evaluable", "project_risk_distribution",
               "positive", "none", "safety-evaluable denominator",
               den_kind="safety_evaluable_subjects", den_value=120,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_den_efficacy_evaluable", "project_risk_distribution",
               "positive", "none", "efficacy-evaluable denominator",
               den_kind="efficacy_evaluable_subjects", den_value=118,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_den_subject_time", "project_safety_trend",
               "positive", "none", "subject-time denominator -> incidence rate",
               den_kind="subject_time", den_value=1200,
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}, estimate="incidence_rate",
               segments=2),
        _owned(p, "d10_den_exposure_time", "project_safety_trend",
               "positive", "none", "exposure-time denominator -> exposure-adjusted rate",
               den_kind="exposure_time", den_value=980,
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}, estimate="exposure_adjusted_rate",
               segments=2),
        _owned(p, "d10_den_opportunities", "project_risk_distribution",
               "positive", "none", "expected-assessment-opportunities denominator",
               den_kind="expected_assessment_opportunities", den_value=504,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_den_analysis_population", "project_efficacy_trend",
               "positive", "none", "analysis-population denominator",
               den_kind="analysis_population_members", den_value=112,
               hit="hit", ce_declared=1, ce_matched=0,
               efficacy={"complete": True}),
        _owned(p, "d10_closed_zero_design_na", "project_risk_distribution",
               "not_applicable", "none",
               "closed-zero denominator proven not applicable by design clause",
               den_state="closed_zero", den_value=0,
               design_applicable="not_applicable", hit="no_hit"),
        _owned(p, "d10_closed_zero_not_negative", "project_risk_distribution",
               "not_evaluable", "zero_event_empty_denominator_negative",
               "closed-zero denominator must not silently become negative",
               den_state="closed_zero", den_value=0, hit="no_hit",
               attack_ids=["zero_event_empty_denominator_negative"]),
        _owned(p, "d10_zero_events_complete_negative", "project_risk_distribution",
               "negative", "none",
               "zero events WITH complete checks and no hit -> negative",
               hit="no_hit", num={"subject": 0, "event": 0, "member": 0, "site": 0}),
        _owned(p, "d10_exclusions_applied", "project_risk_distribution",
               "positive", "none",
               "declared exclusions applied, denominator recomputed",
               den_excl=["not_in_analysis_set"], den_value=126,
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_exclusion_counted", "project_risk_distribution",
               "integrity_gate", "none",
               "excluded member still counted in numerator",
               excluded_in_numerator=True, den_excl=["not_in_analysis_set"],
               gate_kind="integrity_gate",
               gate_reasons=["excluded_member_counted"]),
        _owned(p, "d10_subject_time_overlap", "project_safety_trend",
               "integrity_gate", "none",
               "overlapping subject-time segments unresolved",
               gate_kind="integrity_gate", gate_reasons=["time_segment_overlap"],
               safety={"complete": True}, segments=2, seg_overlap=True),
        _owned(p, "d10_subject_time_valid", "project_safety_trend",
               "positive", "none",
               "valid non-overlapping subject-time segments",
               den_kind="subject_time", den_value=1200,
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}, estimate="incidence_rate",
               segments=2),
        _owned(p, "d10_exposure_time_tamper", "project_safety_trend",
               "integrity_gate", "denominator_time_segment_tamper",
               "normalized duration disagrees with source anchors",
               seg_tamper=True, gate_kind="integrity_gate",
               gate_reasons=["time_segment_tamper"],
               safety={"complete": True}, segments=2,
               attack_ids=["denominator_time_segment_tamper"]),
        _owned(p, "d10_exposure_time_valid", "project_safety_trend",
               "positive", "none",
               "valid exposure-time segments -> exposure-adjusted rate",
               den_kind="exposure_time", den_value=980,
               hit="hit", ce_declared=1, ce_matched=0,
               safety={"complete": True}, estimate="exposure_adjusted_rate",
               segments=2),
        _owned(p, "d10_opportunity_accepted", "project_risk_distribution",
               "positive", "none",
               "accepted gap opportunity ledger sufficient (9/42)",
               opp={"expected": 42, "observed": 9, "complete": True},
               hit="hit", ce_declared=1, ce_matched=0,
               num={"subject": 9, "event": 9, "member": 10, "site": 2},
               pattern=0, individual=9),
        _owned(p, "d10_opportunity_raw_only", "project_risk_distribution",
               "not_evaluable", "gap_only_provenance",
               "raw-only gap cannot enter admission",
               opp={"expected": 42, "observed": 9, "complete": True,
                    "provenance": "raw_only"},
               attack_ids=["gap_only_provenance"]),
        _owned(p, "d10_opportunity_incomplete", "project_risk_distribution",
               "not_evaluable", "gap_only_provenance",
               "gap opportunity ledger unclosed",
               opp={"expected": 42, "observed": 9, "complete": False,
                    "state": "insufficient"},
               attack_ids=["gap_only_provenance"]),
        _owned(p, "d10_population_missing", "project_efficacy_trend",
               "not_evaluable", "none",
               "analysis population absent -> not evaluable",
               pop_present=False, efficacy={"complete": True}),
        _owned(p, "d10_population_mismatch", "project_efficacy_trend",
               "not_evaluable", "none",
               "member outside the admitted analysis population",
               pop_present=False, efficacy={"complete": True}),
        _owned(p, "d10_denominator_tamper", "project_risk_distribution",
               "integrity_gate", "denominator_time_segment_tamper",
               "submitted denominator value differs from recomputed",
               den_tamper=True, gate_kind="integrity_gate",
               gate_reasons=["denominator_tamper"],
               attack_ids=["denominator_time_segment_tamper"]),
        _owned(p, "d10_segment_not_from_anchors", "project_safety_trend",
               "integrity_gate", "denominator_time_segment_tamper",
               "time segment not rebuilt from immutable source anchors",
               seg_tamper=True, gate_kind="integrity_gate",
               gate_reasons=["time_segment_tamper"],
               safety={"complete": True}, segments=1,
               attack_ids=["denominator_time_segment_tamper"]),
    ]
    return rows


def build_p05_specs() -> list[dict[str, Any]]:
    """cross-site comparability: small sites, late start, case mix,
    follow-up/exposure, coverage, method validity, gates, D06 boundary."""
    p = "p05_cross_site_comparability"
    rows = [
        _owned(p, "d10_small_site_boundary", "cross_site_pattern",
               "boundary", "small_site_stigma",
               "small eligible site -> boundary, never positive or stigmatized",
               hit="hit", ce_declared=1, ce_matched=0,
               comp_reasons=["site_small"],
               den_value=10, num={"subject": 1, "event": 1, "member": 1, "site": 1},
               attack_ids=["small_site_stigma"]),
        _owned(p, "d10_small_site_outlier_rate", "cross_site_pattern",
               "boundary", "small_site_stigma",
               "small site outlier rate must not be ranked or labeled bad",
               hit="hit", ce_declared=1, ce_matched=0,
               comp_reasons=["site_small_outlier"],
               den_value=8, num={"subject": 3, "event": 3, "member": 3, "site": 1},
               attack_ids=["small_site_stigma"]),
        _owned(p, "d10_small_site_heterogeneous", "cross_site_pattern",
               "boundary", "none",
               "two sites, one small -> heterogeneous, boundary",
               hit="hit", ce_declared=1, ce_matched=0,
               comp_reasons=["heterogeneous_sites"],
               eligible_sites=2, den_value=18,
               num={"subject": 4, "event": 4, "member": 4, "site": 2}),
        _owned(p, "d10_late_start_boundary", "cross_site_pattern",
               "boundary", "none",
               "late-start site with short follow-up -> boundary",
               comp_reasons=["site_late_start"],
               site_activation="late", hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_late_start_outlier", "cross_site_pattern",
               "boundary", "small_site_stigma",
               "late-start outlier must not be top-ranked",
               comp_reasons=["site_late_start_outlier"],
               site_activation="late", hit="hit", ce_declared=1, ce_matched=0,
               attack_ids=["small_site_stigma"]),
        _owned(p, "d10_late_start_incomparable", "cross_site_pattern",
               "comparison_set_gate", "none",
               "late-start site makes windows incomparable",
               comp_state="incomparable_sites", eligible_sites=2, required_sites=3,
               site_activation="late", es_state="control_plane_gate",
               gate_kind="comparison_set_gate", gate_reasons=["comparison_incomparable_sites"]),
        _owned(p, "d10_case_mix_mismatch", "cross_site_pattern",
               "boundary", "none",
               "case-mix covariate differences not explained",
               comp_reasons=["case_mix_mismatch"],
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_case_mix_missing", "cross_site_pattern",
               "not_evaluable", "none",
               "required case-mix covariates missing",
               comp_reasons=["case_mix_missing"]),
        _owned(p, "d10_followup_shortfall", "cross_site_pattern",
               "boundary", "none",
               "minimum follow-up not met across sites",
               comp_reasons=["followup_shortfall"],
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_exposure_shortfall", "cross_site_pattern",
               "boundary", "none",
               "minimum exposure not met",
               comp_reasons=["exposure_shortfall"],
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_site_coverage_hole", "cross_site_pattern",
               "not_evaluable", "required_l1_hole",
               "coverage hole in one required site",
               cov=[["D09", "covered", "not_evaluable"]],
               attack_ids=["required_l1_hole"]),
        _owned(p, "d10_site_coverage_truncated", "cross_site_pattern",
               "not_evaluable", "required_l1_hole",
               "truncated site coverage -> not evaluable",
               cov=[["D09", "truncated", "partial"]],
               attack_ids=["required_l1_hole"]),
        _owned(p, "d10_method_invalid", "cross_site_pattern",
               "not_evaluable", "none",
               "comparison method preconditions fail",
               comp_reasons=["method_validity_insufficient"]),
        _owned(p, "d10_method_insufficient", "cross_site_pattern",
               "not_evaluable", "none",
               "method validity insufficient",
               comp_reasons=["method_validity_insufficient"]),
        _owned(p, "d10_insufficient_sites_one", "cross_site_pattern",
               "comparison_set_gate", "none",
               "one eligible site < required three",
               es_state="control_plane_gate", gate_kind="comparison_set_gate",
               gate_reasons=["comparison_insufficient_sites"],
               comp_state="insufficient_sites", eligible_sites=1, required_sites=3),
        _owned(p, "d10_insufficient_sites_zero", "cross_site_pattern",
               "comparison_set_gate", "none",
               "zero eligible sites -> comparison gate",
               es_state="control_plane_gate", gate_kind="comparison_set_gate",
               gate_reasons=["comparison_insufficient_sites"],
               comp_state="insufficient_sites", eligible_sites=0, required_sites=3),
        _owned(p, "d10_incomparable_denominators", "cross_site_pattern",
               "comparison_set_gate", "none",
               "mixed denominator kinds across sites",
               es_state="control_plane_gate", gate_kind="comparison_set_gate",
               gate_reasons=["comparison_incomparable_sites"],
               comp_state="incomparable_sites", eligible_sites=2, required_sites=3),
        _owned(p, "d10_incomparable_windows", "cross_site_pattern",
               "comparison_set_gate", "none",
               "window definitions differ across sites",
               es_state="control_plane_gate", gate_kind="comparison_set_gate",
               gate_reasons=["comparison_incomparable_sites"],
               comp_state="incomparable_sites", eligible_sites=2, required_sites=3),
        _owned(p, "d10_cross_site_ready_positive", "cross_site_pattern",
               "positive", "none",
               "eligible sites ready with complete comparability evidence",
               hit="hit", ce_declared=1, ce_matched=0,
               eligible_sites=3, num={"subject": 7, "event": 9, "member": 7, "site": 3}),
        _owned(p, "d10_cross_site_counterevidence", "cross_site_pattern",
               "negative", "none",
               "case-mix difference fully explains cross-site difference",
               hit="hit", ce_declared=2, ce_matched=2),
        _owned(p, "d10_d06_efficacy_as_pattern", "cross_site_pattern",
               "integrity_gate", "none",
               "D06 site efficacy must not be treated as a D09 center pattern",
               pattern=1, descendants=2, member_producer_d06=True,
               gate_kind="integrity_gate",
               gate_reasons=["d06_efficacy_not_d09_pattern"]),
        _owned(p, "d10_d06_measure_authorized", "project_efficacy_trend",
               "positive", "none",
               "authorized D06 typed measure consumed as source measure",
               hit="hit", ce_declared=1, ce_matched=0,
               efficacy={"complete": True}, eligible_sites=3,
               num={"subject": 7, "event": 7, "member": 7, "site": 3}),
        _owned(p, "d10_site_quality_judgment_attempt", "cross_site_pattern",
               "not_evaluable", "none",
               "cross-site outlier converted into a site-quality verdict",
               comp_reasons=["site_quality_judgment"],
               gate_kind="integrity_gate", gate_reasons=["site_quality_judgment"]),
        _base_spec(p, "d10_site_quality_handoff", "cross_site_pattern",
                   "site_quality_judgment", "handoff_only", "handoff_gate",
                   "none", "site quality verdict stays handoff-only",
                   es_state="routed_consume_only", gate_kind="routing_gate",
                   gate_reasons=["token_handoff_only"]),
        _owned(p, "d10_small_site_excluded", "cross_site_pattern",
               "comparison_set_gate", "none",
               "small site excluded by eligibility rule -> gate",
               es_state="control_plane_gate", gate_kind="comparison_set_gate",
               gate_reasons=["comparison_insufficient_sites"],
               comp_state="insufficient_sites", eligible_sites=2, required_sites=3,
               excluded_sites=1),
        _owned(p, "d10_site_evidence_incomplete", "cross_site_pattern",
               "not_evaluable", "none",
               "per-site comparability evidence missing",
               comp_reasons=["site_evidence_incomplete"]),
        _owned(p, "d10_cross_site_positive_evidence", "cross_site_pattern",
               "positive", "none",
               "cross-site positive with full per-site evidence",
               hit="hit", ce_declared=1, ce_matched=0,
               eligible_sites=3, num={"subject": 12, "event": 15, "member": 12,
                                      "site": 3}),
        _owned(p, "d10_cross_site_heterogeneous_boundary", "cross_site_pattern",
               "boundary", "none",
               "heterogeneous case mix across eligible sites -> boundary",
               comp_reasons=["heterogeneous_sites"],
               hit="hit", ce_declared=1, ce_matched=0),
    ]
    return rows


def build_p06_specs() -> list[dict[str, Any]]:
    """safety: AE / severity / SAE / AESI / discontinuation / lab /
    exposure-adjusted / special population / singleton not hidden."""
    p = "p06_safety_trend"
    s = {"complete": True}
    rows = [
        _owned(p, "d10_safety_ae_proportion", "project_safety_trend",
               "positive", "none", "AE count + proportion with exposure context",
               safety=s, hit="hit", ce_declared=1, ce_matched=0,
               num={"subject": 7, "event": 9, "member": 7, "site": 3}),
        _owned(p, "d10_safety_no_hit", "project_safety_trend",
               "negative", "none", "complete safety evaluation, no hit",
               safety=s, hit="no_hit"),
        _owned(p, "d10_safety_severity", "project_safety_trend",
               "positive", "none", "grade 3+ severity distribution",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_severity_scale_missing", "project_safety_trend",
               "not_evaluable", "none", "severity scale missing from context",
               safety={"complete": False, "missing": ["severity"]}),
        _owned(p, "d10_safety_sae", "project_safety_trend",
               "positive", "none", "SAE events with seriousness rule",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_sae_singleton_hotspot", "project_safety_trend",
               "positive", "hotspot_singleton_not_hidden",
               "SAE singleton stays a hotspot, never hidden by low rate",
               safety=s, hit="hit", ce_declared=1, ce_matched=0,
               hotspot=True, num={"subject": 1, "event": 1, "member": 1, "site": 1},
               attack_ids=["hotspot_singleton_not_hidden"]),
        _owned(p, "d10_safety_aesi", "project_safety_trend",
               "positive", "none", "AESI events",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_aesi_context_missing", "project_safety_trend",
               "not_evaluable", "none", "AESI without risk-window context",
               safety={"complete": False, "missing": ["risk_window"]}),
        _owned(p, "d10_safety_discontinuation", "project_safety_trend",
               "positive", "none", "discontinuation / dose-adjustment events",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_discontinuation_small", "project_safety_trend",
               "boundary", "none", "small discontinuation count -> boundary",
               safety=s, hit="hit", ce_declared=1, ce_matched=0, small=True,
               num={"subject": 1, "event": 1, "member": 1, "site": 1}),
        _owned(p, "d10_safety_lab_trend", "project_safety_trend",
               "positive", "none", "lab shift trend",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_lab_no_hit", "project_safety_trend",
               "negative", "none", "lab trend with no rule hit",
               safety=s, hit="no_hit"),
        _owned(p, "d10_safety_exposure_adjusted", "project_safety_trend",
               "positive", "none", "exposure-adjusted rate",
               safety=s, hit="hit", ce_declared=1, ce_matched=0,
               den_kind="exposure_time", den_value=980, estimate="exposure_adjusted_rate",
               segments=2),
        _owned(p, "d10_safety_exposure_missing", "project_safety_trend",
               "not_evaluable", "none", "exposure definition missing",
               safety={"complete": False, "missing": ["exposure"]}),
        _owned(p, "d10_safety_special_population", "project_safety_trend",
               "positive", "none", "special-population risk distribution",
               safety=s, hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_safety_special_population_small", "project_safety_trend",
               "boundary", "none", "small special-population subset -> boundary",
               safety=s, hit="hit", ce_declared=1, ce_matched=0, small=True,
               num={"subject": 2, "event": 2, "member": 2, "site": 1}),
        _owned(p, "d10_safety_singleton_hidden_attempt", "project_safety_trend",
               "integrity_gate", "hotspot_singleton_not_hidden",
               "high-risk singleton hidden by project-low-rate display",
               safety=s, hotspot=True, hotspot_hidden=True, gate_kind="integrity_gate",
               gate_reasons=["hotspot_hidden"],
               attack_ids=["hotspot_singleton_not_hidden"]),
        _owned(p, "d10_safety_singleton_preserved", "project_safety_trend",
               "positive", "hotspot_singleton_not_hidden",
               "high-risk singleton preserved as hotspot with the unit",
               safety=s, hotspot=True, hit="hit", ce_declared=1, ce_matched=0,
               num={"subject": 1, "event": 1, "member": 1, "site": 1},
               attack_ids=["hotspot_singleton_not_hidden"]),
        _owned(p, "d10_safety_pvalue_only", "project_safety_trend",
               "boundary", "model_majority_ensemble1_positive",
               "p-value alone cannot create a positive",
               safety=s, hit="hit", sources=["pvalue"],
               attack_ids=["model_majority_ensemble1_positive"]),
        _owned(p, "d10_safety_model_majority", "project_safety_trend",
               "boundary", "model_majority_ensemble1_positive",
               "model majority vote cannot create a positive",
               safety=s, hit="hit", sources=["model_majority"],
               model={"role": "candidate_explanation", "ensemble_size": 1},
               attack_ids=["model_majority_ensemble1_positive"]),
        _owned(p, "d10_safety_context_incomplete", "project_safety_trend",
               "not_evaluable", "none", "safety context missing coding dictionary",
               safety={"complete": False, "missing": ["coding"]}),
        _owned(p, "d10_safety_context_no_window", "project_safety_trend",
               "not_evaluable", "none", "safety context missing risk window",
               safety={"complete": False, "missing": ["risk_window"]}),
        _owned(p, "d10_safety_formal_wording", "project_safety_trend",
               "integrity_gate", "formal_safety_efficacy_wording",
               "formal safety-signal wording must be rejected",
               gate_kind="integrity_gate", gate_reasons=["formal_safety_wording"],
               safety=s, injection=True, injection_blocked=False,
               attack_ids=["formal_safety_efficacy_wording"]),
        _owned(p, "d10_safety_event_double_count", "project_safety_trend",
               "integrity_gate", "none",
               "same AE+SAE event double-counted",
               gate_kind="integrity_gate", gate_reasons=["event_double_count"],
               safety=s, dup_member_ref=True),
    ]
    return rows


def build_p07_specs() -> list[dict[str, Any]]:
    """efficacy: endpoint / timepoint / baseline / missing / intercurrent /
    estimand / blind treatment role."""
    p = "p07_efficacy_trend"
    e = {"complete": True}
    rows = [
        _owned(p, "d10_efficacy_endpoint", "project_efficacy_trend",
               "positive", "none", "endpoint definition bound",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="responder_rate"),
        _owned(p, "d10_efficacy_endpoint_conflict", "project_efficacy_trend",
               "not_evaluable", "none", "endpoint definition hash conflict",
               efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned(p, "d10_efficacy_timepoint", "project_efficacy_trend",
               "positive", "none", "visit/timepoint window bound",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="summary_statistic"),
        _owned(p, "d10_efficacy_timepoint_missing", "project_efficacy_trend",
               "not_evaluable", "none", "timepoint window missing",
               efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned(p, "d10_efficacy_baseline", "project_efficacy_trend",
               "positive", "none", "baseline definition bound",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="summary_statistic"),
        _owned(p, "d10_efficacy_baseline_missing", "project_efficacy_trend",
               "not_evaluable", "none", "baseline definition missing",
               efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned(p, "d10_efficacy_missing_rule", "project_efficacy_trend",
               "positive", "none", "missing-data rule bound",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="responder_rate"),
        _owned(p, "d10_efficacy_missing_rule_absent", "project_efficacy_trend",
               "not_evaluable", "none", "missing-data rule absent",
               efficacy={"complete": False, "missing": ["missing"]}),
        _owned(p, "d10_efficacy_intercurrent", "project_efficacy_trend",
               "positive", "none", "intercurrent-event rule bound",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="responder_rate"),
        _owned(p, "d10_efficacy_intercurrent_absent", "project_efficacy_trend",
               "not_evaluable", "none", "intercurrent-event rule absent",
               efficacy={"complete": False, "missing": ["intercurrent"]}),
        _owned(p, "d10_efficacy_estimand_bound", "project_efficacy_trend",
               "positive", "none", "estimand bound with context",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="model_estimate"),
        _owned(p, "d10_efficacy_estimand_mismatch", "project_efficacy_trend",
               "not_evaluable", "efficacy_estimand_mismatch_forced_comparison",
               "estimand mismatch must not force a comparison",
               efficacy={"complete": False, "missing": ["estimand"]},
               estimand_bound=False,
               attack_ids=["efficacy_estimand_mismatch_forced_comparison"]),
        _owned(p, "d10_efficacy_unblinded_authorized", "project_efficacy_trend",
               "positive", "none", "authorized unblinded treatment role",
               efficacy=e, treatment_required=True, assignment_present=True,
               blind_status="unblinded_authorized",
               hit="hit", ce_declared=1, ce_matched=0, estimate="summary_statistic"),
        _owned(p, "d10_efficacy_assignment_missing", "project_efficacy_trend",
               "not_evaluable", "treatment_assignment_missing",
               "treatment assignment identity missing",
               efficacy=e, treatment_required=True, assignment_present=False,
               attack_ids=["treatment_assignment_missing"]),
        _owned(p, "d10_efficacy_unauthorized_unblinded", "project_efficacy_trend",
               "integrity_gate", "blind_treatment_inference",
               "unauthorized unblinded treatment-role read",
               efficacy=e, treatment_required=True, assignment_present=False,
               blind_inference=True, gate_kind="integrity_gate",
               gate_reasons=["unauthorized_unblinded"],
               attack_ids=["blind_treatment_inference", "treatment_assignment_missing"]),
        _owned(p, "d10_efficacy_blind_inference_counts", "project_efficacy_trend",
               "integrity_gate", "blind_treatment_inference",
               "blind inference through counts/denominators",
               efficacy=e, blind_inference=True, gate_kind="integrity_gate",
               gate_reasons=["blind_treatment_inference"],
               attack_ids=["blind_treatment_inference"]),
        _owned(p, "d10_efficacy_responder_rate", "project_efficacy_trend",
               "positive", "none", "responder rate with complete context",
               efficacy=e, hit="hit", ce_declared=1, ce_matched=0,
               estimate="responder_rate"),
        _owned(p, "d10_efficacy_responder_no_context", "project_efficacy_trend",
               "not_evaluable", "none", "responder rate without context",
               efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned(p, "d10_efficacy_model_no_estimand", "project_efficacy_trend",
               "not_evaluable", "none", "model estimate without estimand",
               efficacy={"complete": False, "missing": ["estimand"]}),
        _owned(p, "d10_efficacy_summary_no_population", "project_efficacy_trend",
               "not_evaluable", "none", "summary statistic without analysis set",
               pop_present=False, efficacy=e),
        _owned(p, "d10_efficacy_pvalue_only", "project_efficacy_trend",
               "boundary", "model_majority_ensemble1_positive",
               "efficacy p-value alone -> boundary",
               efficacy=e, hit="hit", sources=["pvalue"],
               attack_ids=["model_majority_ensemble1_positive"]),
        _owned(p, "d10_efficacy_model_majority", "project_efficacy_trend",
               "boundary", "model_majority_ensemble1_positive",
               "efficacy model majority alone -> boundary",
               efficacy=e, hit="hit", sources=["model_majority"],
               model={"role": "candidate_explanation", "ensemble_size": 1},
               attack_ids=["model_majority_ensemble1_positive"]),
        _owned(p, "d10_efficacy_confirmatory_attempt", "project_efficacy_trend",
               "integrity_gate", "formal_safety_efficacy_wording",
               "confirmatory treatment-effect conclusion attempt",
               efficacy=e, gate_kind="integrity_gate",
               gate_reasons=["confirmatory_conclusion_attempt"],
               injection=True, injection_blocked=False,
               attack_ids=["formal_safety_efficacy_wording"]),
        _owned(p, "d10_efficacy_window_incomparable", "project_efficacy_trend",
               "window_pair_gate", "none",
               "efficacy windows incomparable -> window-pair gate",
               es_state="control_plane_gate", gate_kind="window_pair_gate",
               gate_reasons=["window_pair_incomparable_windows"],
               pair_state="incomparable_windows", wins=2, unique_windows=2,
               efficacy=e),
    ]
    return rows


def build_p08_specs() -> list[dict[str, Any]]:
    """initial full / incremental / cutoff / rule/mapping/method/population/
    visibility/coverage change cause."""
    p = "p08_change_cause_lineage"

    def ch(**kw: Any) -> dict[str, Any]:
        base = {"basis": "full", "comparison_state": "initial_full",
                "prior": False, "data_n": 0, "denom_n": 0, "coverage_n": 0,
                "knowledge_n": 0, "rule_n": 0, "mapping_n": 0, "model_n": 0,
                "method_n": 0, "population_n": 0, "visibility_n": 0, "mode_n": 0,
                "cutoff_state": "not_evaluable", "cutoff_predicate": False,
                "cutoff_policy_equal": False}
        base.update(kw)
        return base

    rows = [
        _owned(p, "d10_initial_full_positive", "project_risk_distribution",
               "positive", "initial_full_fake_change",
               "first full snapshot: initial_current only, no change units",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(r2_action="create", r2_prior=False,
                         r2_lineage="initial_full_snapshot"),
               attack_ids=["initial_full_fake_change"]),
        _owned(p, "d10_initial_full_negative", "project_risk_distribution",
               "negative", "none",
               "first full snapshot, no hit",
               hit="no_hit", change=ch()),
        _owned(p, "d10_initial_full_fake_new", "project_risk_distribution",
               "integrity_gate", "initial_full_fake_change",
               "first full falsely labeled as new/closed",
               change=ch(claimed_kind="new", claimed_cause="data"),
               gate_kind="integrity_gate", gate_reasons=["fake_change_claim"],
               attack_ids=["initial_full_fake_change"]),
        _owned(p, "d10_incremental_new", "project_risk_distribution",
               "positive", "none",
               "incremental data change -> new",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=2, data_kind="new",
                         r2_action="create", r2_prior=False,
                         r2_lineage="continued_from_data_revision")),
        _owned(p, "d10_incremental_resolved", "project_risk_distribution",
               "positive", "none",
               "incremental data change -> resolved",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="resolved",
                         r2_action="propose_close", r2_prior=True,
                         r2_lineage="continued_from_data_revision")),
        _owned(p, "d10_incremental_continued", "project_risk_distribution",
               "positive", "none",
               "incremental data change -> continued",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="continued",
                         r2_action="continue", r2_prior=True,
                         r2_lineage="continued_from_data_revision")),
        _owned(p, "d10_incremental_downgraded", "project_risk_distribution",
               "positive", "none",
               "incremental data change -> downgraded",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="downgraded",
                         r2_action="update", r2_prior=True,
                         r2_lineage="continued_from_data_revision")),
        _owned(p, "d10_cutoff_strict_advance", "project_risk_distribution",
               "positive", "cutoff_first_positive_create",
               "strict cutoff advance first-positive create",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         cutoff_state="strict_advance", cutoff_predicate=True,
                         cutoff_policy_equal=True,
                         r2_action="create", r2_prior=False,
                         r2_lineage="continued_from_cutoff_advance"),
               attack_ids=["cutoff_first_positive_create"]),
        _owned(p, "d10_cutoff_first_positive_no_prior", "project_risk_distribution",
               "positive", "cutoff_first_positive_create",
               "cutoff advance create requires no prior R2 risk",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         cutoff_state="strict_advance", cutoff_predicate=True,
                         cutoff_policy_equal=True,
                         r2_action="create", r2_prior=False,
                         r2_lineage="continued_from_cutoff_advance"),
               attack_ids=["cutoff_first_positive_create"]),
        _owned(p, "d10_cutoff_predicate_tamper", "project_risk_distribution",
               "integrity_gate", "strict_cutoff_predicate_tamper_same_window_replay",
               "strict-advance predicate tampered",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         cutoff_state="same_window", cutoff_predicate=False,
                         cutoff_policy_equal=True, claimed_cutoff="strict_advance",
                         r2_action="create", r2_prior=False),
               gate_kind="integrity_gate", gate_reasons=["cutoff_advance_tamper"],
               attack_ids=["strict_cutoff_predicate_tamper_same_window_replay"]),
        _owned(p, "d10_same_window_replay", "project_risk_distribution",
               "integrity_gate", "strict_cutoff_predicate_tamper_same_window_replay",
               "same-window replay claimed as advance",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, data_kind="new",
                         cutoff_state="same_window", cutoff_predicate=False,
                         cutoff_policy_equal=True, claimed_cutoff="strict_advance",
                         r2_action="create", r2_prior=False),
               gate_kind="integrity_gate", gate_reasons=["same_window_replay"],
               attack_ids=["strict_cutoff_predicate_tamper_same_window_replay"]),
        _owned(p, "d10_cutoff_rule_mixed", "project_risk_distribution",
               "integrity_gate", "cutoff_rule_or_mode_mixed_first_positive",
               "cutoff advance mixed with rule change cannot first-positive create",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new", rule_n=1,
                         cutoff_state="strict_advance", cutoff_predicate=True,
                         cutoff_policy_equal=True,
                         r2_action="create", r2_prior=False,
                         r2_lineage="continued_from_cutoff_advance"),
               gate_kind="integrity_gate", gate_reasons=["cutoff_mixed_non_data"],
               attack_ids=["cutoff_rule_or_mode_mixed_first_positive"]),
        _owned(p, "d10_rule_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "rule change -> analysis-only change leaf, no clinical narrative",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, rule_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_rule_or_mapping_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_mapping_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "mapping change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, mapping_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_rule_or_mapping_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_method_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "method change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, method_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_method_or_population_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_population_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "population change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, population_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_method_or_population_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_visibility_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "visibility change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, visibility_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_visibility_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_coverage_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "coverage change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, coverage_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="coverage_regressed"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_mode_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "mode change -> analysis-only / supersession",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, mode_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_mode_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_mixed_non_data", "project_risk_distribution",
               "positive", "rule_method_visibility_mixed_change",
               "mixed rule+method change -> not_comparable, analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, rule_n=1, method_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_method_or_population_change"),
               attack_ids=["rule_method_visibility_mixed_change"]),
        _owned(p, "d10_r2_create_with_prior", "project_risk_distribution",
               "integrity_gate", "r2_wrong_prior_lineage_carry_forward",
               "create with an existing prior risk -> wrong prior",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         r2_action="create", r2_prior=True),
               gate_kind="integrity_gate", gate_reasons=["r2_wrong_prior"],
               attack_ids=["r2_wrong_prior_lineage_carry_forward"]),
        _owned(p, "d10_r2_carry_forward_broken_coverage", "project_risk_distribution",
               "not_evaluable", "r2_wrong_prior_lineage_carry_forward",
               "carry-forward on broken coverage -> not evaluable",
               cov=[["D01", "covered", "not_evaluable"]],
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="continued",
                         carry_forward=True,
                         r2_action="continue", r2_prior=True,
                         r2_lineage="continued_from_data_revision"),
               attack_ids=["r2_wrong_prior_lineage_carry_forward"]),
        _owned(p, "d10_r2_wrong_lineage", "project_risk_distribution",
               "integrity_gate", "r2_wrong_prior_lineage_carry_forward",
               "create with lineage not in the allowed closed set",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         r2_action="create", r2_prior=False,
                         r2_lineage="superseded_by_mode_change"),
               gate_kind="integrity_gate", gate_reasons=["r2_wrong_lineage"],
               attack_ids=["r2_wrong_prior_lineage_carry_forward"]),
        _owned(p, "d10_data_revision_continued", "project_risk_distribution",
               "positive", "none",
               "data revision continuation with prior risk",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=2, data_kind="continued",
                         r2_action="continue", r2_prior=True,
                         r2_lineage="continued_from_data_revision")),
        _owned(p, "d10_coverage_regression", "project_risk_distribution",
               "not_evaluable", "none",
               "coverage regression blocks evaluation",
               cov=[["D01", "missing", "missing"]],
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, coverage_n=1,
                         r2_lineage="coverage_regressed")),
        _owned(p, "d10_knowledge_change_analysis_only", "project_risk_distribution",
               "positive", "non_data_change_as_improvement",
               "knowledge change -> analysis-only",
               hit="hit", ce_declared=1, ce_matched=0,
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=0, knowledge_n=1,
                         r2_action="supersede", r2_prior=True,
                         r2_lineage="superseded_by_knowledge_change"),
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_fake_data_cause", "project_risk_distribution",
               "integrity_gate", "non_data_change_as_improvement",
               "claimed data cause while rule refs present",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, rule_n=1, data_kind="new",
                         claimed_kind="new", claimed_cause="data",
                         r2_action="continue", r2_prior=True),
               gate_kind="integrity_gate", gate_reasons=["fake_change_cause"],
               attack_ids=["non_data_change_as_improvement"]),
        _owned(p, "d10_cutoff_not_evaluable", "project_risk_distribution",
               "not_evaluable", "none",
               "cutoff boundary source missing -> not evaluable",
               change=ch(basis="incremental", comparison_state="comparable",
                         prior=True, data_n=1, data_kind="new",
                         cutoff_state="not_evaluable", cutoff_predicate=False,
                         cutoff_policy_equal=False,
                         r2_action="create", r2_prior=False,
                         r2_lineage="continued_from_cutoff_advance")),
    ]
    return rows


def build_p09_specs() -> list[dict[str, Any]]:
    """Query redundancy / fanout / PD wording / deep links."""
    p = "p09_query_deeplink"
    rows = [
        _owned(p, "d10_query_generated", "project_risk_distribution",
               "positive", "none",
               "positive with project delta -> one query draft",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 7}),
        _owned(p, "d10_query_within_fanout", "project_risk_distribution",
               "positive", "none",
               "positive, delta, within fanout -> one query",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 7,
                      "fanout": 100}),
        _owned(p, "d10_query_fully_covered", "project_risk_distribution",
               "positive", "none",
               "fully covered by member queries -> no D10 query",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "fully_covered_by_member_queries",
                      "uncovered": 0, "covered": 7}),
        _owned(p, "d10_query_unlistable", "project_risk_distribution",
               "positive", "none",
               "members unlistable -> no query",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "members_unlistable", "uncovered": 7,
                      "unlistable": True}),
        _owned(p, "d10_query_fanout_exceeded", "project_risk_distribution",
               "positive", "none",
               "fanout exceeded -> display-only, no query",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 101,
                      "fanout": 100}),
        _owned(p, "d10_query_pd_wording", "project_risk_distribution",
               "positive", "query_reorder_source_pd_redundancy_tamper",
               "PD-related query uses fixed verify wording",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 2,
                      "pd": "verify_whether_pd"},
               attack_ids=["query_reorder_source_pd_redundancy_tamper"]),
        _owned(p, "d10_query_non_pd", "project_risk_distribution",
               "positive", "none",
               "non-PD query wording",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 3}),
        _owned(p, "d10_query_three_part_sentences", "project_risk_distribution",
               "positive", "none",
               "basis/finding/action typed sentence parts",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 4}),
        _owned(p, "d10_deeplink_member", "project_risk_distribution",
               "positive", "none",
               "member-kind deep link",
               hit="hit", ce_declared=1, ce_matched=0, dl_n=1, dl_kinds=["member"]),
        _owned(p, "d10_deeplink_site", "project_risk_distribution",
               "positive", "none",
               "site-kind deep link",
               hit="hit", ce_declared=1, ce_matched=0, dl_n=1, dl_kinds=["site"]),
        _owned(p, "d10_deeplink_subject_site_pair", "project_risk_distribution",
               "positive", "none",
               "subject-site-pair deep link",
               hit="hit", ce_declared=1, ce_matched=0, dl_n=1,
               dl_kinds=["subject_site_pair"]),
        _owned(p, "d10_deeplink_deficient", "project_risk_distribution",
               "boundary", "none",
               "unresolvable member locator -> boundary, no fabricated jump",
               hit="hit", ce_declared=1, ce_matched=0, locator_missing=True),
        _owned(p, "d10_journey_one_hop", "project_risk_distribution",
               "positive", "none",
               "Project->Site->Subject->Journey/source one-hop chain",
               hit="hit", ce_declared=1, ce_matched=0, dl_n=3,
               dl_kinds=["member", "site", "subject_site_pair"]),
        _owned(p, "d10_source_locator_missing", "project_risk_distribution",
               "boundary", "none",
               "missing source locator -> boundary",
               hit="hit", ce_declared=1, ce_matched=0, locator_missing=True),
        _owned(p, "d10_query_reorder_invariant", "project_risk_distribution",
               "positive", "query_reorder_source_pd_redundancy_tamper",
               "member reorder must not change query identity",
               hit="hit", ce_declared=1, ce_matched=0,
               query={"decision": "project_delta_present", "uncovered": 7},
               attack_ids=["query_reorder_source_pd_redundancy_tamper"]),
        _owned(p, "d10_query_source_tamper", "project_risk_distribution",
               "integrity_gate", "query_reorder_source_pd_redundancy_tamper",
               "member-query content identity mismatch",
               gate_kind="integrity_gate", gate_reasons=["query_source_tamper"],
               q_ids_mismatch=True,
               query={"decision": "project_delta_present", "uncovered": 7},
               attack_ids=["query_reorder_source_pd_redundancy_tamper"]),
        _owned(p, "d10_query_redundancy_tamper", "project_risk_distribution",
               "integrity_gate", "query_reorder_source_pd_redundancy_tamper",
               "covered ∪ uncovered != unit members",
               gate_kind="integrity_gate", gate_reasons=["query_redundancy_tamper"],
               query={"decision": "project_delta_present", "uncovered": 3,
                      "covered": 2},
               attack_ids=["query_reorder_source_pd_redundancy_tamper"]),
        _owned(p, "d10_query_duplicate_per_unit", "project_risk_distribution",
               "integrity_gate", "query_reorder_source_pd_redundancy_tamper",
               "second query for the same evaluation unit",
               gate_kind="integrity_gate", gate_reasons=["duplicate_query_per_unit"],
               q_duplicate=True,
               query={"decision": "project_delta_present", "uncovered": 7},
               attack_ids=["query_reorder_source_pd_redundancy_tamper"]),
        _owned(p, "d10_deeplink_subject_only", "project_risk_distribution",
               "integrity_gate", "projection_deeplink_visibility_tamper",
               "subject-only deep link leaks scope",
               gate_kind="integrity_gate", gate_reasons=["deep_link_eligible_violation"],
               dl_violation=True, dl_n=1, dl_kinds=["subject_site_pair"],
               attack_ids=["projection_deeplink_visibility_tamper"]),
        _owned(p, "d10_audience_injection_blocked", "project_risk_distribution",
               "positive", "audience_engineering_injection",
               "engineering reference in zh audience text blocked -> no query",
               hit="hit", ce_declared=1, ce_matched=0, injection=True,
               injection_blocked=True,
               query={"decision": "project_delta_present", "uncovered": 7},
               attack_ids=["audience_engineering_injection"]),
    ]
    return rows


def build_p10_specs() -> list[dict[str, Any]]:
    """visibility / blindness / hidden denominators / non-disclosure."""
    p = "p10_visibility_blindness"
    rows = [
        _owned(p, "d10_vis_hidden_members", "project_risk_distribution",
               "positive", "none",
               "hidden members counted in evaluation, projection restricted",
               hit="hit", ce_declared=1, ce_matched=0,
               vis_hidden_members=2, rate_state="qualified"),
        _owned(p, "d10_vis_hidden_denominator", "project_risk_distribution",
               "positive", "none",
               "hidden-site denominator non-disclosure, counts shown",
               hit="hit", ce_declared=1, ce_matched=0,
               vis_hidden_sites=1, rate_state="suppressed"),
        _owned(p, "d10_vis_rate_suppressed", "project_risk_distribution",
               "positive", "none",
               "rate projection suppressed for hidden set",
               hit="hit", ce_declared=1, ce_matched=0,
               vis_hidden_members=3, rate_state="suppressed"),
        _owned(p, "d10_vis_rate_qualified", "project_risk_distribution",
               "positive", "none",
               "rate projection qualified on mixed visibility",
               hit="hit", ce_declared=1, ce_matched=0,
               vis_hidden_members=2, rate_state="qualified"),
        _owned(p, "d10_vis_hidden_site", "project_risk_distribution",
               "positive", "none",
               "hidden site set preserved",
               hit="hit", ce_declared=1, ce_matched=0,
               vis_hidden_sites=1, rate_state="qualified"),
        _owned(p, "d10_vis_hidden_omission", "project_risk_distribution",
               "integrity_gate", "blind_hidden_set_omission",
               "hidden refs omitted from the hidden set",
               vis_hidden_members=2, vis_hidden_omission=True,
               gate_kind="integrity_gate", gate_reasons=["hidden_set_omitted"],
               attack_ids=["blind_hidden_set_omission"]),
        _owned(p, "d10_vis_algebra_violation", "project_risk_distribution",
               "integrity_gate", "blind_hidden_set_omission",
               "projectable ∪ hidden != evaluation",
               vis_hidden_members=2, vis_algebra_ok=False,
               gate_kind="integrity_gate", gate_reasons=["visibility_algebra"],
               attack_ids=["blind_hidden_set_omission"]),
        _owned(p, "d10_vis_dl_eligible_valid", "project_risk_distribution",
               "positive", "none",
               "deep-link eligible subset of projectable (valid)",
               hit="hit", ce_declared=1, ce_matched=0, dl_n=2,
               dl_kinds=["member", "site"]),
        _owned(p, "d10_vis_dl_eligible_violation", "project_risk_distribution",
               "integrity_gate", "hidden_deeplink_eligible_subset_violation",
               "deep-link eligible member outside projectable set",
               dl_violation=True, gate_kind="integrity_gate",
               gate_reasons=["deep_link_eligible_violation"],
               attack_ids=["hidden_deeplink_eligible_subset_violation"]),
        _owned(p, "d10_vis_dl_hidden_site_pair", "project_risk_distribution",
               "integrity_gate", "hidden_deeplink_eligible_subset_violation",
               "subject-site pair deep link to a hidden site",
               dl_violation=True, gate_kind="integrity_gate",
               gate_reasons=["deep_link_eligible_violation"],
               attack_ids=["hidden_deeplink_eligible_subset_violation"]),
        _owned(p, "d10_vis_visible_n_algebra", "project_risk_distribution",
               "integrity_gate", "none",
               "visible_n != |projectable|",
               vis_algebra_ok=False, gate_kind="integrity_gate",
               gate_reasons=["visibility_algebra"]),
        _owned(p, "d10_vis_hidden_counts_algebra", "project_risk_distribution",
               "integrity_gate", "none",
               "hidden counts != set cardinality",
               vis_hidden_members=2, vis_algebra_ok=False,
               vis_hidden_counts_bad=True, gate_kind="integrity_gate",
               gate_reasons=["visibility_algebra"]),
        _owned(p, "d10_vis_blind_denominator_inference", "project_risk_distribution",
               "integrity_gate", "blind_treatment_inference",
               "blind inference through denominator counts",
               blind_inference=True, gate_kind="integrity_gate",
               gate_reasons=["blind_treatment_inference"],
               attack_ids=["blind_treatment_inference"]),
        _owned(p, "d10_vis_blind_label_inference", "project_risk_distribution",
               "integrity_gate", "blind_treatment_inference",
               "blind inference through labels/colors",
               blind_inference=True, gate_kind="integrity_gate",
               gate_reasons=["blind_treatment_inference"],
               attack_ids=["blind_treatment_inference"]),
        _owned(p, "d10_vis_unblinded_authorized", "project_efficacy_trend",
               "positive", "none",
               "authorized unblinded audience with visibility contract",
               blind_status="unblinded_authorized", efficacy={"complete": True},
               treatment_required=True, assignment_present=True,
               hit="hit", ce_declared=1, ce_matched=0,
               estimate="summary_statistic"),
        _owned(p, "d10_vis_hidden_dropped", "project_risk_distribution",
               "integrity_gate", "none",
               "hidden member dropped from evaluation instead of counted",
               vis_hidden_members=2, vis_hidden_dropped=True,
               gate_kind="integrity_gate",
               gate_reasons=["hidden_member_dropped"]),
    ]
    return rows


def build_p11_specs() -> list[dict[str, Any]]:
    """Unicode / key exactness / hash / tamper / bijection."""
    p = "p11_unicode_tamper_bijection"
    replay_change = {"basis": "full", "comparison_state": "initial_full",
                     "cutoff_state": "same_window", "cutoff_predicate": False,
                     "cutoff_policy_equal": True}
    rows = [
        _owned(p, "d10_nfc_normalized", "project_risk_distribution",
               "positive", "none",
               "NFC normalization keeps identity stable",
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_nfc_zh_text", "project_risk_distribution",
               "positive", "none",
               "decomposed Chinese input normalized to NFC",
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_confusable_fullwidth", "project_risk_distribution",
               "integrity_gate", "unicode_confusable_engineering_inject",
               "full-width engineering reference must be blocked",
               injection=True, injection_blocked=False, gate_kind="integrity_gate",
               gate_reasons=["audience_injection_blocked"],
               attack_ids=["unicode_confusable_engineering_inject"]),
        _owned(p, "d10_confusable_homoglyph", "project_risk_distribution",
               "integrity_gate", "unicode_confusable_engineering_inject",
               "homoglyph engineering reference must be blocked",
               injection=True, injection_blocked=False, gate_kind="integrity_gate",
               gate_reasons=["audience_injection_blocked"],
               attack_ids=["unicode_confusable_engineering_inject"]),
        _owned(p, "d10_inject_pattern_rule_token", "project_risk_distribution",
               "integrity_gate", "unicode_confusable_engineering_inject",
               "pattern/rule/mode/window/revision/scope/policy token in zh text",
               injection=True, injection_blocked=False, gate_kind="integrity_gate",
               gate_reasons=["audience_injection_blocked"],
               attack_ids=["unicode_confusable_engineering_inject"]),
        _owned(p, "d10_rehash_envelope", "project_risk_distribution",
               "integrity_gate", "rehash_bypass_evaluator_identity",
               "rehashed object cannot bypass evaluator identity",
               rehash=True, gate_kind="integrity_gate",
               gate_reasons=["rehash_bypass_evaluator_identity"],
               attack_ids=["rehash_bypass_evaluator_identity"]),
        _owned(p, "d10_rehash_query", "project_risk_distribution",
               "integrity_gate", "rehash_bypass_evaluator_identity",
               "rehashed query object with mismatched canonical hash",
               rehash=True, gate_kind="integrity_gate",
               gate_reasons=["rehash_bypass_evaluator_identity"],
               attack_ids=["rehash_bypass_evaluator_identity"]),
        _owned(p, "d10_rehash_projection", "project_risk_distribution",
               "integrity_gate", "rehash_bypass_evaluator_identity",
               "rehashed projection bypass attempt",
               rehash=True, gate_kind="integrity_gate",
               gate_reasons=["rehash_bypass_evaluator_identity"],
               attack_ids=["rehash_bypass_evaluator_identity"]),
        _owned(p, "d10_duplicate_id_rejected", "project_risk_distribution",
               "integrity_gate", "none",
               "duplicate stable id with different content rejected",
               dup_member_ref=True, gate_kind="integrity_gate",
               gate_reasons=["duplicate_content_identity"]),
        _owned(p, "d10_duplicate_locator", "project_risk_distribution",
               "integrity_gate", "none",
               "duplicate locator id with different content rejected",
               dup_locator=True, gate_kind="integrity_gate",
               gate_reasons=["duplicate_content_identity"]),
        _owned(p, "d10_nan_rejected", "project_risk_distribution",
               "integrity_gate", "none",
               "invalid non-finite numeric rejected from canonical hashing",
               den_value=-1, den_kind="treated_subjects", gate_kind="integrity_gate",
               gate_reasons=["invalid_numeric"]),
        _owned(p, "d10_id_reuse_across_revisions", "project_risk_distribution",
               "integrity_gate", "none",
               "same id across revisions with different content hash",
               dup_revision=True, gate_kind="integrity_gate",
               gate_reasons=["duplicate_content_identity"]),
        _owned(p, "d10_id_replay_same_content", "project_risk_distribution",
               "positive", "none",
               "same id + same content replay is idempotent",
               hit="hit", ce_declared=1, ce_matched=0, change=replay_change),
        _owned(p, "d10_order_permutation", "project_risk_distribution",
               "positive", "none",
               "input order permutation does not change identity",
               hit="hit", ce_declared=1, ce_matched=0, change=replay_change),
        _owned(p, "d10_ref_prefix_invariant", "project_risk_distribution",
               "positive", "none",
               "ref-prefix surface change keeps substantive identity",
               hit="hit", ce_declared=1, ce_matched=0, change=replay_change),
        _owned(p, "d10_canonical_byte_stable", "project_risk_distribution",
               "positive", "none",
               "canonical JSON byte stability across double-pass replay",
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_key_exactness", "project_risk_distribution",
               "positive", "none",
               "exact-key schema enforced on every typed object",
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_bijection_bijective", "project_risk_distribution",
               "positive", "none",
               "five-way case/fixture/oracle/manifest/test bijection holds",
               hit="hit", ce_declared=1, ce_matched=0),
        _owned(p, "d10_contract_hash_mismatch", "project_risk_distribution",
               "global_gate", "none",
               "mode content hash disagrees with authority",
               envelope_ok=False, gate_kind="global_gate",
               gate_reasons=["mode_content_hash_mismatch"]),
        _owned(p, "d10_authority_unresolved", "project_risk_distribution",
               "not_evaluable", "none",
               "authority content hash unresolvable",
               design_applicable="unresolved"),
    ]
    return rows


# anti-overfit bases (8) x 2 deterministic surface variants (16)
_ANTI_OVERFIT_BASES = ("table_field_rename", "input_order_shuffle",
                       "version_field_change", "zh_label_change",
                       "display_precision_change", "evidence_row_change",
                       "audience_contract_id_change", "envelope_id_change")


def build_p12_specs() -> list[dict[str, Any]]:
    """8 base pairs x 2 variants. Variant 2 differs ONLY in display/order/
    non-medical version fields (zh label, mode version, display precision,
    evidence file/row display names, audience/envelope ids, array order).
    Substantive identity (project/site/subject/member refs, signal/window/
    stratum/comparison, denominator, sets) is shared via identity_idx and is
    rebuilt from the accepted fixture authority."""
    p = "p12_anti_overfit"
    rows: list[dict[str, Any]] = []
    for n, base in enumerate(_ANTI_OVERFIT_BASES):
        for v in (1, 2):
            kw: dict[str, Any] = {"anti_base": base, "variant": v,
                                  "identity_idx": 297 + n * 2}
            if v == 2:
                if base == "table_field_rename":
                    kw["evidence_file_alt"] = True
                elif base == "input_order_shuffle":
                    kw["members_reversed"] = True
                elif base == "version_field_change":
                    kw["mode_version_alt"] = True
                elif base == "zh_label_change":
                    kw["zh_label_alt"] = True
                elif base == "display_precision_change":
                    kw["precision_alt"] = True
                elif base == "evidence_row_change":
                    kw["evidence_row_alt"] = True
                elif base == "audience_contract_id_change":
                    kw["audience_id_alt"] = True
                elif base == "envelope_id_change":
                    kw["envelope_id_alt"] = True
            rows.append(_owned(
                p, f"d10_anti_overfit_{base}_v{v}", "project_risk_distribution",
                "positive", "none",
                f"anti-overfit {base} variant {v}: same substantive identity",
                hit="hit", ce_declared=1, ce_matched=0, **kw))
    return rows


def all_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for builder in (build_p01_specs, build_p02_specs, build_p03_specs,
                    build_p04_specs, build_p05_specs, build_p06_specs,
                    build_p07_specs, build_p08_specs, build_p09_specs,
                    build_p10_specs, build_p11_specs, build_p12_specs):
        specs.extend(builder())
    return specs


def assemble_catalog() -> dict[str, Any]:
    specs = all_specs()
    cases = []
    for idx, spec in enumerate(specs, start=1):
        alt = bool(spec.get("surface_alt"))
        typed = build_typed_input(spec, idx, alt=alt)
        cases.append(build_case_row(typed, spec, idx))
    catalog: dict[str, Any] = {
        "catalog_id": CATALOG_ID,
        "version": SCHEMA_VERSION,
        "case_count": len(cases),
        "catalog_hash": "",
        "cases": cases,
    }
    catalog["catalog_hash"] = content_hash(catalog, "catalog_hash")
    return catalog


# ---------------------------------------------------------------------------
# Quota manifest + registry assembly
# ---------------------------------------------------------------------------
def _partition_counts(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_partition: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_partition.setdefault(case["primary_partition"], []).append(case)
    return by_partition


def _case_attack_index() -> dict[str, list[str]]:
    """case_id -> sorted unique attack ids (from the embedded spec table)."""
    out: dict[str, list[str]] = {}
    for idx, spec in enumerate(all_specs(), start=1):
        ids = sorted(set(spec.get("attack_ids", [])))
        if ids:
            out[f"D10-CASE-{idx:03d}"] = ids
    return out


def assemble_quota_manifest(catalog: dict[str, Any]) -> dict[str, Any]:
    cases = catalog["cases"]
    by_partition = _partition_counts(cases)
    partition_reqs = [{
        "partition_id": pid,
        "partition_label_zh": PARTITION_LABELS[pid],
        "required_minimum": minimum,
    } for pid, _, minimum in PARTITIONS]
    attack_reqs = [{
        "attack_id": aid,
        "attack_label_zh": ATTACK_LABELS_ZH[aid],
        "required_minimum": 1,
    } for aid in ATTACK_IDS]
    attack_index = _case_attack_index()
    case_attack_rows = [{
        "case_id": cid,
        "attack_ids": ids,
    } for cid, ids in sorted(attack_index.items())]
    actual_attack_counts = {aid: 0 for aid in ATTACK_IDS}
    for ids in attack_index.values():
        for aid in ids:
            actual_attack_counts[aid] += 1
    actual_partition_counts = {pid: len(members)
                               for pid, members in by_partition.items()}
    union_sorted = _sorted_unique([c["case_id"] for c in cases], "union case ids")
    catalog_ids_sorted = _sorted_unique([c["case_id"] for c in cases], "catalog ids")
    seen: set[str] = set()
    duplicates: list[str] = []
    for cid in union_sorted:
        if cid in seen:
            duplicates.append(cid)
        seen.add(cid)
    missing = [cid for cid in catalog_ids_sorted if cid not in seen]
    pairwise: dict[str, int] = {}
    partition_ids = [pid for pid, _, _ in PARTITIONS]
    for i, left in enumerate(partition_ids):
        for right in partition_ids[i + 1:]:
            left_ids = {c["case_id"] for c in by_partition.get(left, [])}
            right_ids = {c["case_id"] for c in by_partition.get(right, [])}
            pairwise[f"{left}∩{right}"] = len(left_ids & right_ids)
    manifest: dict[str, Any] = {
        "manifest_id": QUOTA_MANIFEST_ID,
        "required_total": REQUIRED_TOTAL,
        "primary_partition_requirements": partition_reqs,
        "mandatory_attack_requirements": attack_reqs,
        "actual_mandatory_attack_counts": actual_attack_counts,
        "case_to_mandatory_attack_rows": case_attack_rows,
        "actual_primary_partition_counts": actual_partition_counts,
        "case_id_union": union_sorted,
        "pairwise_intersection_counts": pairwise,
        "union_count": len(union_sorted),
        "duplicate_case_ids": duplicates,
        "missing_case_ids": missing,
        "catalog_hash": catalog["catalog_hash"],
        "oracle_hash": PROVISIONAL_HASH_SENTINEL,
        "registry_hash": PROVISIONAL_HASH_SENTINEL,
        "generator_hash": STAGE_A_GENERATOR_SHA256,
        "manifest_hash": "",
    }
    manifest["manifest_hash"] = content_hash(manifest, "manifest_hash")
    return manifest


def strip_substantive(value: Any) -> Any:
    """Remove run/snapshot/revision/version/wall-clock tokens and normalize
    documented surface tokens (SYN-D10-ALT-* renames and the case-index
    sequence in synthetic refs) before hashing, so anti-overfit variant pairs
    share one substantive identity."""
    if isinstance(value, str):
        return (re.sub(r"-\d{3}-", "-IDX-", value)
                .replace("SYN-D10-ALT-", "SYN-D10-")
                .replace("SYN-D10-MODE-001-ALT", "SYN-D10-MODE-001"))
    if isinstance(value, dict):
        return {key: strip_substantive(item) for key, item in value.items()
                if key not in STRIP_KEYS}
    if isinstance(value, list):
        return [strip_substantive(item) for item in value]
    return value


STRIP_KEYS = frozenset({
    "envelope_id", "run_ref", "snapshot_ref", "source_revision_content_pairs",
    "mode_contract_version", "audience_contract_id", "audience_scope_id",
    "mutation_context", "anti_overfit_variant", "evidence_refs",
    "locator_id", "source_file", "row_or_cell_ref", "lineage_ref",
    "surface_changes", "window_start", "window_end", "audience_text",
})


def assemble_registry(catalog: dict[str, Any], quota_manifest: dict[str, Any],
                      generator_source_hash: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in catalog["cases"]:
        number = case["case_id"].rsplit("-", 1)[-1]
        rows.append({
            "case_id": case["case_id"],
            "fixture_id": case["fixture_id"],
            "oracle_case_id": case["oracle_case_id"],
            "manifest_case_id": case["manifest_case_id"],
            "test_id": f"D10-TEST-{number}",
        })
    bijection_ok = all(
        len({row[col] for row in rows}) == len(rows) for col in BIJECTION_COLUMNS
    )
    audit = {
        "row_count": len(rows),
        "bijection_ok": bijection_ok,
        "sorted_case_ids": [row["case_id"] for row in rows],
        "duplicate_case_ids": [],
        "missing_case_ids": [],
    }
    oracle_reference_state = {
        "state": "unresolved",
        "reserved_for": "worker_02",
        "oracle_artifact_path": DECLARED_ORACLE_ARTIFACT_PATH,
        "expected_leaf_policy":
            "expected leaves exist only in the independent oracle artifact; "
            "catalog expected_* fields remain literal null; forbidden leaves "
            "per contract section 15",
        "catalog_expected_fields": "null",
    }
    registry: dict[str, Any] = {
        "artifact_kind": "d10_challenge_manifest_registry",
        "registry_id": REGISTRY_ID,
        "schema_version": SCHEMA_VERSION,
        "contract_semantic_hash": CONTRACT_SEMANTIC_HASH,
        "catalog_hash": catalog["catalog_hash"],
        "quota_manifest_hash": quota_manifest["manifest_hash"],
        "generator_hash": generator_source_hash,
        "oracle_reference_state": oracle_reference_state,
        "rows": rows,
        "bijection_audit": audit,
        "content_hash": "",
    }
    registry["content_hash"] = content_hash(registry, "content_hash")
    return registry


# ---------------------------------------------------------------------------
# Validation (schema-level; never derives expected outcomes)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Typed-input semantic audit (independent recomputation from typed facts;
# catches re-signed semantic tamper that schema checks alone accept).
# ---------------------------------------------------------------------------
AUDIT_CODES = frozenset({
    "legal_row_hash_bad", "legal_row_sd_mismatch", "scope_hash_bad",
    "mode_hash_bad",
    "source_hash_bad", "origin_hash_bad", "origin_refs_external",
    "origin_partition_bad", "origin_decision_bad",
    "den_refs_bad", "seg_recompute_bad", "ledger_bad",
    "cutoff_order_bad", "r2_prior_bad",
    "dl_eligible_bad", "dl_target_bad", "dl_pair_bad",
    "vis_decision_hash_bad", "vis_algebra_bad",
    "q_covered_bad", "q_identity_bad", "q_partition_bad", "q_content_bad",
    "assignment_bad", "desc_hash_bad", "model_hash_bad",
    "audience_scan_hit",
})
# Declared tamper fixtures legitimately carry exactly these audit codes
# (their mutation class is the declared attack); everything else must be
# absent from the fresh generation and rejected when present.
ALLOWED_AUDIT_BY_MUTATION: dict[str, frozenset[str]] = {
    "denominator_time_segment_tamper": frozenset({"seg_recompute_bad"}),
    "query_reorder_source_pd_redundancy_tamper": frozenset({
        "q_identity_bad", "q_partition_bad"}),
    "rehash_bypass_evaluator_identity": frozenset({"q_partition_bad"}),
    "legal_row_mismatch": frozenset({"legal_row_sd_mismatch"}),
    "blind_hidden_set_omission": frozenset({
        "vis_algebra_bad", "dl_pair_bad", "dl_eligible_bad"}),
    "hidden_deeplink_eligible_subset_violation": frozenset({
        "dl_pair_bad", "dl_eligible_bad", "dl_target_bad"}),
}
_ENGINEERING_KEY_RE = re.compile(
    r"(?:pattern|rule|mode|window|revision|scope|policy|hash|ref|key|id)"
    r"\s*[:=＝]")
_FULLWIDTH_LATIN = frozenset(
    list(range(0xFF10, 0xFF1A)) + list(range(0xFF21, 0xFF3B))
    + list(range(0xFF41, 0xFF5B)))
_INVISIBLE_CHARS = frozenset("\u200b\u200c\u200d\u2060\ufeff")


def _audience_scan_hit(audience_text: dict[str, Any],
                       audience_contract: dict[str, Any]) -> bool:
    """Independent audience-text audit: NFC, control/invisible chars,
    full-width confusable latin, closed engineering key/value patterns and
    the typed forbidden internal terms. Never trusts the submitted flag."""
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


def audit_case(case: dict[str, Any]) -> list[str]:
    """Recompute every cross-object hash/binding/set relation from the typed
    input alone. Returns violation codes (empty = internally consistent).
    Declared tamper fixtures still produce the codes their mutation class
    allows; everything else is rejected by validate_case."""
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
    locator_ids = _authority_locator_ids(typed)
    for pair in typed["source_revision_content_pairs"]:
        if pair["content_hash"] != sha256_text(canonical_json({
                "revision_id": pair["revision_id"],
                "source_locators": locator_ids})):
            out.append("source_hash_bad")
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
            derived_decision = "ambiguous"
        elif verified and distinct:
            derived_decision = "mixed_verified_and_distinct"
        elif verified:
            derived_decision = "all_verified_same_origin"
        elif distinct:
            derived_decision = "all_distinct"
        elif mob["origin_decision"] == "wrong_scope":
            derived_decision = "wrong_scope"
        else:
            derived_decision = "not_evaluable"
        if mob["origin_decision"] != derived_decision:
            out.append("origin_decision_bad")
        candidate_list = sorted(candidate)
        if mob["candidate_partition_hash"] != sha256_text(
                canonical_json(candidate_list)):
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
    projectable_refs_list = vis["projectable_member_refs"]
    hidden_refs = vis["hidden_member_refs"]
    declared_mutation = typed["mutation_context"]["mutation_class"]
    projectable = set(projectable_refs_list)
    if len(set(member_refs)) == len(member_refs) and any(
            values != sorted(set(values)) for values in
           (evaluation_refs, projectable_refs_list, hidden_refs,
            vis["deep_link_eligible_member_refs"],
            vis["evaluation_site_refs"], vis["projectable_site_refs"],
            vis["hidden_site_refs"], vis["deep_link_eligible_site_refs"])):
        out.append("vis_algebra_bad")
    if declared_mutation != "none" and (
            set(projectable_refs_list) | set(hidden_refs) != set(evaluation_refs) or
            set(projectable_refs_list) & set(hidden_refs)):
        out.append("vis_algebra_bad")
    if not set(vis["deep_link_eligible_member_refs"]) <= projectable:
        out.append("dl_eligible_bad")
    proj_sites = set(vis["projectable_site_refs"])
    member_by_ref = {m["member_ref"]: m for m in members}
    pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in projectable_refs_list if ref in member_by_ref
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
        out.append("vis_algebra_bad")
    if declared_mutation != "none" and submitted_pairs != pairs:
        out.append("vis_algebra_bad")
    if set(submitted_eligible_pairs) - set(pairs) or \
            set(submitted_eligible_pairs) != set(eligible_pairs):
        out.append("dl_pair_bad")
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
        else:  # subject_site_pair
            if (dl["subject_ref"], dl["site_ref"]) not in \
                    set(submitted_eligible_pairs):
                out.append("dl_target_bad")
            if dl["member_object_ref"] is not None:
                out.append("dl_target_bad")
    qd = typed["query_decision"]
    covered_refs = qd["covered_member_refs"]
    uncovered_refs = qd["uncovered_member_refs"]
    fanout_display_only = (len(uncovered_refs) > len(set(member_refs))
                           and qd["decision"] == "project_delta_present")
    if any(ref not in member_refs for ref in covered_refs):
        out.append("q_covered_bad")
    if any(ref not in member_refs for ref in uncovered_refs) and not fanout_display_only:
        out.append("q_covered_bad")
    if covered_refs != sorted(set(covered_refs)) or \
            uncovered_refs != sorted(set(uncovered_refs)):
        out.append("q_identity_bad")
    if not fanout_display_only and (set(covered_refs) & set(uncovered_refs) or \
            set(covered_refs) | set(uncovered_refs) != set(member_refs)):
        out.append("q_partition_bad")
    identities = qd["member_query_content_identities"]
    if len(identities) != len(covered_refs) or \
            len(set(identities)) != len(identities):
        out.append("q_identity_bad")
    elif any(identity != sha256_text(canonical_json({"member_ref": ref}))
             for identity, ref in zip(identities, covered_refs)):
        out.append("q_identity_bad")
    expected_unit_hash = sha256_text(canonical_json(sorted(set(member_refs))))
    if qd["unit_member_set_hash"] != expected_unit_hash:
        out.append("q_partition_bad")
    expected_proof = {
        "unit_member_refs": sorted(set(member_refs)),
        "covered_member_refs": covered_refs,
        "uncovered_member_refs": uncovered_refs,
        "member_query_content_identities": identities,
    }
    if qd["coverage_proof_hash"] != sha256_text(canonical_json(expected_proof)):
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
        if model["member_analysis_ref_set_hash"] != (sha256_text(
                canonical_json(sorted(set(model["member_analysis_refs"]))))) or \
                model["member_analysis_refs"] != sorted(set(model["member_analysis_refs"])):
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
# Fixture authority conformance: every decisive accepted value in the typed
# input must equal the fixed fixture authority registry entry. The authority
# is content-addressed and independently pinned; it is NEVER recomputed from
# the tested objects. Any mismatch (including fully re-signed artifacts)
# fails closed.
# ---------------------------------------------------------------------------
def _authority_member_tuples(members: list[dict[str, Any]]) -> list[tuple]:
    out = []
    for m in members:
        out.append((m["member_ref"], m["member_kind"], m["aggregation_plane"],
                    m["subject_stable_id"], m["site_stable_id"],
                    m["member_scope_state"], m["locator_resolution_state"],
                    m["monitoring_priority"], m["producer_domain"],
                    m["source_locator_refs"][0]
                    if m["source_locator_refs"] else None))
    return sorted(out)


def _authority_locator_ids(typed: dict[str, Any]) -> list[str]:
    ids = set()
    for m in typed["members"]:
        ids.update(m["source_locator_refs"])
    for ref in typed["evidence_refs"]:
        ids.add(ref["locator_id"])
    return sorted(ids)


def _authority_change_block(typed: dict[str, Any], cid: str) -> dict[str, Any] | None:
    """Rebuild the pinned change authority from the typed change decision."""
    ch = typed["change_decision"]
    if ch is None:
        return None
    def refs(key: str, refs_list: list[str]) -> list[str]:
        return sorted(refs_list)
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


def _authority_segment_hash(segments: list[dict[str, Any]]) -> str:
    ordered = sorted(segments, key=lambda s: s["segment_id"])
    return sha256_text(canonical_json(ordered))


def validate_authority_conformance(catalog: dict[str, Any],
                                   authority: dict[str, Any]) -> None:
    """Compare every case's typed_input against its fixed authority entry.
    Raises D10ArtifactError on the first mismatch."""
    entries = {e["case_id"]: e for e in authority["entries"]}
    if len(entries) != authority["case_count"]:
        raise D10ArtifactError("authority", "coverage",
                               "authority entry coverage mismatch")
    for case in catalog["cases"]:
        cid = case["case_id"]
        entry = entries.get(cid)
        if entry is None:
            raise D10ArtifactError("authority", "missing_entry",
                                   f"{cid} missing authority entry")
        typed = case["typed_input"]

        def check(label: str, expected: Any, got: Any) -> None:
            if expected != got:
                raise D10ArtifactError(
                    "authority", "mismatch",
                    f"{cid} authority mismatch {label}: "
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
        check("expected_set.expected_set_state",
              entry["expected_set"]["expected_set_state"],
              es["expected_set_state"])
        gate = es["admission_gate"]
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
                         "monitoring_priority", "producer_domain",
                         "locator_ref"), t))
               for t in _authority_member_tuples(typed["members"])])
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
              entry["denominator"]["denominator_value"],
              den["denominator_value"])
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
              _authority_segment_hash(segments))
        entry_patterns = {p["member_ref"]: p for p in entry["d09_patterns"]}
        for member in typed["members"]:
            if member["member_kind"] != "center_pattern":
                continue
            pinned = entry_patterns.get(member["member_ref"])
            if pinned is None:
                raise D10ArtifactError(
                    "authority", "mismatch",
                    f"{cid} d09 pattern {member['member_ref']} not pinned")
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
            check("measure_origin.numerator_plane_state",
                  pinned_mo["numerator_plane_state"],
                  mob["numerator_plane_state"])
            for key, pinned_key in (("verified_risk_refs", "verified_ref_set_hash"),
                                    ("distinct_risk_refs", "distinct_ref_set_hash"),
                                    ("ambiguous_risk_refs", "ambiguous_ref_set_hash")):
                check(f"measure_origin.{key}_set_hash",
                      pinned_mo[pinned_key],
                      sha256_text(canonical_json(sorted(mob[key]))))
            check("measure_origin.source_provenance_hash",
                  pinned_mo["source_provenance_hash"],
                  mob["source_provenance_hash"])
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
        check("visibility.eligible_n", pinned_vis["eligible_n"],
              vis["eligible_n"])
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
              pinned_q["max_query_member_fanout"],
              qd["max_query_member_fanout"])
        check("query.pd_wording_state", pinned_q["pd_wording_state"],
              qd["pd_wording_state"])
        check("query.member_unlistable", pinned_q["member_unlistable"],
              qd["member_unlistable"])
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
            check("model_evidence.role", pinned_me["role"], me["role"])
            check("model_evidence.ensemble_size",
                  pinned_me["ensemble_size"], me["ensemble_size"])
            check("model_evidence.permitted_leaf",
                  pinned_me["permitted_leaf"], me["permitted_leaf"])
            check("model_evidence.member_analysis_ref_set_hash",
                  pinned_me["member_analysis_ref_set_hash"],
                  sha256_text(canonical_json(sorted(me["member_analysis_refs"]))))
            check("model_evidence.model_evidence_id",
                  pinned_me["model_evidence_id"], me["model_evidence_id"])
            check("model_evidence.adjudication_state",
                  pinned_me["adjudication_state"], me["adjudication_state"])
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
            raise D10ArtifactError(
                "authority", "mismatch",
                f"{cid} authority mismatch source_revisions: accepted pair(s) "
                f"not present in submitted set {missing_source_pairs!r}")
        check("source_locator_set_hash", entry["source_locator_set_hash"],
              sha256_text(canonical_json(_authority_locator_ids(typed))))
        check("evidence_refs", entry["evidence_refs"], typed["evidence_refs"])
        check("change", entry["change"],
              _authority_change_block(typed, case["case_id"]))
        vis2 = typed["visibility_decision"]
        check("visibility.evaluation_site_set_hash",
              entry["visibility"]["evaluation_site_set_hash"],
              sha256_text(canonical_json(sorted(set(vis2["evaluation_site_refs"])))))
        check("visibility.projectable_site_set_hash",
              entry["visibility"]["projectable_site_set_hash"],
              sha256_text(canonical_json(sorted(set(vis2["projectable_site_refs"])))))
        check("visibility.hidden_site_set_hash",
              entry["visibility"]["hidden_site_set_hash"],
              sha256_text(canonical_json(sorted(set(vis2["hidden_site_refs"])))))
        check("visibility.deep_link_eligible_site_set_hash",
              entry["visibility"]["deep_link_eligible_site_set_hash"],
              sha256_text(canonical_json(
                  sorted(set(vis2["deep_link_eligible_site_refs"])))))
        projectable_refs = set(vis2["projectable_member_refs"])
        pair_list = sorted({
            (m["subject_stable_id"], m["site_stable_id"])
            for m in typed["members"]
            if m["member_ref"] in projectable_refs
            and m["subject_stable_id"]
            and m["site_stable_id"] in set(vis2["projectable_site_refs"])})
        check("visibility.projectable_subject_site_pair_set_hash",
              entry["visibility"]["projectable_subject_site_pair_set_hash"],
              sha256_text(canonical_json(pair_list)))
        hotspot = typed["hotspot"]
        check("hotspot_member_ref", entry["hotspot_member_ref"],
              hotspot["hotspot_member_refs"][0] if hotspot else None)


def load_authority() -> dict[str, Any]:
    if not AUTHORITY.exists():
        raise D10ArtifactError("authority", "missing",
                               f"fixture authority registry missing at {AUTHORITY}")
    return json.loads(AUTHORITY.read_text(encoding="utf-8"))


def validate_case(case: dict[str, Any], index: int) -> None:
    expect_exact_keys(case, CASE_KEYS, f"catalog case {index}")
    require_string(case["case_id"], "case_id")
    require_enum(case["primary_partition"], tuple(PARTITION_MINIMUMS), "primary_partition")
    require_string(case["family_id"], "family_id")
    require_enum(case["grain"], GRAINS, "grain")
    require_enum(case["owner_route"], OWNER_ROUTES, "owner_route")
    require_string(case["clinical_claim_token"], "clinical_claim_token")
    require_enum(case["disposition"], EXPECTED_DISPOSITION_OR_GATE, "disposition")
    require_enum(case["mutation_class"], MUTATION_CLASSES, "mutation_class")
    if case["expected_leaf_set"] is not None or \
            case["expected_trace_leaf_set"] is not None or \
            case["expected_source_leaf_set"] is not None:
        raise D10ArtifactError("schema_parse", "expected_leak",
                               f"{case['case_id']} expected_* fields must be null")
    expect_exact_keys(case["audience_contract"], AUDIENCE_CONTRACT_KEYS,
                      f"{case['case_id']} audience_contract")
    if case["fixture_id"] != f"D10-FIX-{index:03d}":
        raise D10ArtifactError("schema_parse", "id_mismatch",
                               f"{case['case_id']} fixture_id mismatch")
    if case["oracle_case_id"] != f"D10-ORACLE-{index:03d}":
        raise D10ArtifactError("schema_parse", "id_mismatch",
                               f"{case['case_id']} oracle_case_id mismatch")
    if case["manifest_case_id"] != f"D10-MANIFEST-{index:03d}":
        raise D10ArtifactError("schema_parse", "id_mismatch",
                               f"{case['case_id']} manifest_case_id mismatch")
    core = {key: item for key, item in case.items() if key != "fixture_hash"}
    if case["fixture_hash"] != content_hash(core, "fixture_hash"):
        raise D10ArtifactError("schema_parse", "fixture_hash_mismatch",
                               f"{case['case_id']} fixture_hash mismatch")
    validate_typed_input(case["typed_input"], case["case_id"])
    mutation_class = case["typed_input"]["mutation_context"]["mutation_class"]
    allowed = ALLOWED_AUDIT_BY_MUTATION.get(mutation_class, frozenset())
    violations = [code for code in audit_case(case) if code not in allowed]
    if violations:
        raise D10ArtifactError(
            "semantic_audit", "typed_input_tamper",
            f"{case['case_id']} typed-input semantic audit violations "
            f"(undeclared): {sorted(set(violations))}")


def validate_typed_input(typed: dict[str, Any], case_id: str) -> None:
    expect_exact_keys(typed, TYPED_INPUT_KEYS, f"{case_id} typed_input envelope")
    for key in ("envelope_id", "project_ref", "run_ref", "snapshot_ref"):
        require_string(typed[key], f"{case_id} {key}")
    expect_exact_keys(typed["project_scope_binding"], SCOPE_BINDING_KEYS,
                      f"{case_id} project_scope_binding")
    require_enum(typed["project_scope_binding"]["scope_equality_decision"],
                 SCOPE_EQUALITY_DECISIONS, "scope_equality_decision")
    if not sha256_hex(typed["project_scope_binding"]["scope_binding_hash"]):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} scope_binding_hash malformed")
    expect_exact_keys(typed["mode_contract"], MODE_CONTRACT_KEYS, f"{case_id} mode_contract")
    require_enum(typed["mode_contract"]["design_applicable_state"],
                 DESIGN_APPLICABLE_STATES, "design_applicable_state")
    if not sha256_hex(typed["mode_contract"]["mode_contract_content_hash"]):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} mode_contract_content_hash malformed")
    sd = typed["signal_definition"]
    expect_exact_keys(sd, SIGNAL_DEFINITION_KEYS, f"{case_id} signal_definition")
    require_enum(sd["signal_kind"], SIGNAL_KINDS, "signal_kind")
    require_enum(sd["d10_action"], OWNER_ROUTES, "d10_action")
    lr = typed["legal_matrix_row"]
    expect_exact_keys(lr, LEGAL_MATRIX_ROW_KEYS, f"{case_id} legal_matrix_row")
    es = typed["expected_set"]
    expect_exact_keys(es, EXPECTED_SET_KEYS, f"{case_id} expected_set")
    require_enum(es["expected_set_state"], EXPECTED_SET_STATES, "expected_set_state")
    if es["admission_gate"] is not None:
        expect_exact_keys(es["admission_gate"], ADMISSION_GATE_KEYS,
                          f"{case_id} admission_gate")
        require_string_list(es["admission_gate"]["reason_codes"],
                            f"{case_id} admission_gate reason_codes")
    for window in typed["analysis_windows"]:
        expect_exact_keys(window, WINDOW_KEYS, f"{case_id} window")
    expect_exact_keys(typed["stratum"], STRATUM_KEYS, f"{case_id} stratum")
    cg = typed["comparison_gate"]
    expect_exact_keys(cg, COMPARISON_GATE_KEYS, f"{case_id} comparison_gate")
    require_enum(cg["comparison_state"], COMPARISON_STATES, "comparison_state")
    require_string(cg["comparison_reference_stable_id"],
                   "comparison_reference_stable_id")
    wpg = typed["window_pair_gate"]
    expect_exact_keys(wpg, WINDOW_PAIR_GATE_KEYS, f"{case_id} window_pair_gate")
    require_enum(wpg["pair_state"], PAIR_STATES, "pair_state")
    expect_exact_keys(typed["site_ledger"], SITE_LEDGER_KEYS, f"{case_id} site_ledger")
    require_enum(typed["site_ledger"]["site_activation_state"],
                 SITE_ACTIVATION_STATES, "site_activation_state")
    for member in typed["members"]:
        expect_exact_keys(member, MEMBER_KEYS, f"{case_id} member")
        require_enum(member["member_kind"], MEMBER_KINDS, "member_kind")
        require_enum(member["aggregation_plane"], AGGREGATION_PLANES,
                     "aggregation_plane")
        require_enum(member["member_scope_state"], MEMBER_SCOPE_STATES,
                     "member_scope_state")
        require_enum(member["monitoring_priority"], ("high", "medium", "low"),
                     "monitoring_priority")
        require_enum(member["locator_resolution_state"],
                     ("locatable", "missing", "unresolvable"),
                     "locator_resolution_state")
        if member["member_kind"] == "center_pattern":
            if not member["descendant_member_refs"] or not member["descendant_set_hash"]:
                raise D10ArtifactError("schema_parse", "schema_error",
                                       f"{case_id} center_pattern member requires "
                                       "descendant refs + set hash")
        else:
            if member["descendant_member_refs"] or member["descendant_set_hash"]:
                raise D10ArtifactError("schema_parse", "schema_error",
                                       f"{case_id} non-pattern member must have "
                                       "empty descendant fields")
    nl = typed["numerator_ledger"]
    expect_exact_keys(nl, NUMERATOR_LEDGER_KEYS, f"{case_id} numerator_ledger")
    for key in NUMERATOR_LEDGER_KEYS:
        require_nonneg_int(nl[key], f"{case_id} numerator_ledger.{key}")
    mob = typed["measure_origin_binding"]
    if mob is not None:
        expect_exact_keys(mob, MEASURE_ORIGIN_BINDING_KEYS,
                          f"{case_id} measure_origin_binding")
        require_enum(mob["origin_decision"], ORIGIN_DECISIONS, "origin_decision")
        require_enum(mob["numerator_plane_state"], ("single", "duplicate"),
                     "numerator_plane_state")
    den = typed["denominator"]
    expect_exact_keys(den, DENOMINATOR_KEYS, f"{case_id} denominator")
    require_enum(den["denominator_kind"], DENOMINATOR_KINDS, "denominator_kind")
    require_enum(den["denominator_state"], DENOMINATOR_STATES, "denominator_state")
    if (den["denominator_value"] != den["recomputed_value"]
            and typed["mutation_context"]["mutation_class"]
            != "denominator_time_segment_tamper"):
        raise D10ArtifactError("schema_parse", "denominator_tamper",
                               f"{case_id} denominator_value != recomputed_value "
                               "without the declared tamper mutation class")
    for seg in typed["time_segments"]:
        expect_exact_keys(seg, TIME_SEGMENT_KEYS, f"{case_id} time_segment")
        require_enum(seg["segment_kind"], ("subject_time", "exposure_time"),
                     "segment_kind")
    opp = typed["opportunity"]
    if opp is not None:
        expect_exact_keys(opp, OPPORTUNITY_KEYS, f"{case_id} opportunity")
        require_enum(opp["opportunity_provenance"], OPPORTUNITY_PROVENANCES,
                     "opportunity_provenance")
        require_enum(opp["opportunity_state"], OPPORTUNITY_STATES,
                     "opportunity_state")
    pop = typed["analysis_population"]
    expect_exact_keys(pop, ANALYSIS_POPULATION_KEYS, f"{case_id} analysis_population")
    for cov in typed["coverage"]:
        expect_exact_keys(cov, COVERAGE_KEYS, f"{case_id} coverage")
        require_enum(cov["l0_status"], L0_STATUSES, "l0_status")
        require_enum(cov["l1_medical_completeness_state"], L1_STATES,
                     "l1_medical_completeness_state")
    ch = typed["change_decision"]
    if ch is not None:
        expect_exact_keys(ch, CHANGE_DECISION_KEYS, f"{case_id} change_decision")
        require_enum(ch["execution_basis"], ("full", "incremental"), "execution_basis")
        require_enum(ch["comparison_state"], ("initial_full", "comparable",
                                              "not_comparable"), "comparison_state")
        expect_exact_keys(ch["cutoff_advance"], CUTOFF_ADVANCE_KEYS,
                          f"{case_id} cutoff_advance")
        require_enum(ch["cutoff_advance"]["decision_state"], CUTOFF_DECISION_STATES,
                     "cutoff decision_state")
        if ch["claimed_clinical_change_kind"] is not None:
            require_enum(ch["claimed_clinical_change_kind"], CHANGE_KINDS,
                         "claimed_clinical_change_kind")
        if ch["claimed_primary_change_cause"] is not None:
            require_enum(ch["claimed_primary_change_cause"], CHANGE_CAUSES,
                         "claimed_primary_change_cause")
        if ch["claimed_cutoff_state"] is not None:
            require_enum(ch["claimed_cutoff_state"], CUTOFF_DECISION_STATES,
                         "claimed_cutoff_state")
        if ch["data_change_kind"] is not None:
            require_enum(ch["data_change_kind"],
                         ("new", "continued", "upgraded", "downgraded",
                          "resolved", "reopened"), "data_change_kind")
        if ch["r2_action"] is not None:
            require_enum(ch["r2_action"], HANDOFF_ACTIONS, "r2_action")
        if ch["lineage_relation"] is not None:
            require_enum(ch["lineage_relation"], LINEAGE_RELATIONS, "lineage_relation")
        require_enum(ch["carry_forward_state"], ("none", "active"),
                     "carry_forward_state")
    vis = typed["visibility_decision"]
    expect_exact_keys(vis, VISIBILITY_KEYS, f"{case_id} visibility_decision")
    require_enum(vis["blind_status"], BLIND_STATUSES, "blind_status")
    require_enum(vis["rate_projection_state"], RATE_PROJECTION_STATES,
                 "rate_projection_state")
    if not isinstance(vis["treatment_inference_attempt"], bool):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} treatment_inference_attempt must be bool")
    if not sha256_hex(vis["decision_id"]):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} visibility decision_id malformed")
    qd = typed["query_decision"]
    expect_exact_keys(qd, QUERY_DECISION_KEYS, f"{case_id} query_decision")
    require_enum(qd["decision"], QUERY_REDUNDANCY_DECISIONS, "query decision")
    require_enum(qd["pd_wording_state"], PD_WORDING_STATES, "pd_wording_state")
    if not isinstance(qd["duplicate_query_attempt"], bool):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} duplicate_query_attempt must be bool")
    if not sha256_hex(qd["query_content_hash"]):
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"{case_id} query_content_hash malformed")
    at = typed["audience_text"]
    expect_exact_keys(at, AUDIENCE_TEXT_KEYS, f"{case_id} audience_text")
    require_enum(at["sentence_part_kind"],
                 ("authority_basis", "observed_finding", "denominator_context",
                  "uncertainty", "counterevidence", "action_verify",
                  "action_reconcile", "action_pd_verify",
                  "source_business_identifier"), "sentence_part_kind")
    for dl in typed["deep_links"]:
        expect_exact_keys(dl, DEEP_LINK_KEYS, f"{case_id} deep_link")
        require_enum(dl["target_kind"], DEEP_LINK_TARGET_KINDS, "target_kind")
    me = typed["model_evidence"]
    if me is not None:
        expect_exact_keys(me, MODEL_EVIDENCE_KEYS, f"{case_id} model_evidence")
        require_enum(me["role"], MODEL_EVIDENCE_ROLES, "model role")
        require_enum(me["adjudication_state"], ADJUDICATION_STATES,
                     "adjudication_state")
        require_enum(me["permitted_leaf"],
                     ("model_candidate_only", "counterevidence_suggestion_only"),
                     "permitted_leaf")
        if not sha256_hex(me["model_binding_hash"]) or \
                not sha256_hex(me["output_hash"]):
            raise D10ArtifactError("schema_parse", "schema_error",
                                   f"{case_id} model evidence hashes malformed")
    sc = typed["safety_context"]
    if sc is not None:
        expect_exact_keys(sc, SAFETY_CONTEXT_KEYS, f"{case_id} safety_context")
    ec = typed["efficacy_context"]
    if ec is not None:
        expect_exact_keys(ec, EFFICACY_CONTEXT_KEYS, f"{case_id} efficacy_context")
        if ec["estimate_kind"] is not None:
            require_enum(ec["estimate_kind"],
                         ("summary_statistic", "responder_rate", "model_estimate"),
                         "efficacy estimate_kind")
        if ec["treatment_assignment_mapping_hash"] is not None and \
                not sha256_hex(ec["treatment_assignment_mapping_hash"]):
            raise D10ArtifactError("schema_parse", "schema_error",
                                   f"{case_id} assignment mapping hash malformed")
    rh = typed["rule_hit"]
    expect_exact_keys(rh, RULE_HIT_KEYS, f"{case_id} rule_hit")
    require_enum(rh["hit_state"], RULE_HIT_STATES, "hit_state")
    for source in rh["evidence_sources"]:
        require_enum(source, EVIDENCE_SOURCES, "evidence_sources")
    hp = typed["hotspot"]
    if hp is not None:
        expect_exact_keys(hp, HOTSPOT_KEYS, f"{case_id} hotspot")
    cl = typed["count_layers"]
    expect_exact_keys(cl, COUNT_LAYERS_KEYS, f"{case_id} count_layers")
    el = typed["evaluation_limits"]
    expect_exact_keys(el, EVALUATION_LIMITS_KEYS, f"{case_id} evaluation_limits")
    for key in ("small_sample", "limited_evidence"):
        if not isinstance(el[key], bool):
            raise D10ArtifactError("schema_parse", "schema_error",
                                   f"{case_id} evaluation_limits.{key} must be bool")
    if el["limited_reason"] is not None:
        require_string(el["limited_reason"], f"{case_id} limited_reason")
    expect_exact_keys(typed["numeric_policy"], NUMERIC_POLICY_KEYS,
                      f"{case_id} numeric_policy")
    expect_exact_keys(typed["mutation_context"], MUTATION_CONTEXT_KEYS,
                      f"{case_id} mutation_context")
    require_enum(typed["mutation_context"]["mutation_class"], MUTATION_CLASSES,
                 "mutation_class")
    aov = typed["anti_overfit_variant"]
    if aov is not None:
        expect_exact_keys(aov, ANTI_OVERFIT_KEYS, f"{case_id} anti_overfit_variant")
        for change in aov["surface_changes"]:
            expect_exact_keys(change, SURFACE_CHANGE_KEYS,
                              f"{case_id} surface_change")
    for ref in typed["evidence_refs"]:
        expect_exact_keys(ref, EVIDENCE_REF_KEYS, f"{case_id} evidence_ref")
    for pair in typed["source_revision_content_pairs"]:
        expect_exact_keys(pair, ["revision_id", "content_hash"],
                          f"{case_id} source revision pair")


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    expect_exact_keys(catalog, CATALOG_KEYS, "catalog top-level")
    if catalog["catalog_id"] != CATALOG_ID:
        raise D10ArtifactError("schema_parse", "schema_error",
                               "catalog_id mismatch")
    cases = catalog["cases"]
    if not isinstance(cases, list) or len(cases) != catalog["case_count"]:
        raise D10ArtifactError("schema_parse", "schema_error",
                               "case_count mismatch")
    if catalog["case_count"] < REQUIRED_TOTAL:
        raise D10ArtifactError("quota", "below_floor",
                               f"case_count {catalog['case_count']} < {REQUIRED_TOTAL}")
    for index, case in enumerate(cases, start=1):
        validate_case(case, index)
    if catalog["catalog_hash"] != content_hash(catalog, "catalog_hash"):
        raise D10ArtifactError("catalog_hash", "stale_hash",
                               "catalog content hash mismatch")
    return cases


def _mandatory_attack_mapping(cases: list[dict[str, Any]],
                              manifest: dict[str, Any]) -> None:
    """Verify mandatory-attack rows bidirectional consistency (oracle-blind)."""
    counts = {aid: 0 for aid in ATTACK_IDS}
    seen_cases: set[str] = set()
    for row in manifest["case_to_mandatory_attack_rows"]:
        expect_exact_keys(row, CASE_ATTACK_ROW_KEYS, "case_to_mandatory_attack_row")
        if row["case_id"] not in {c["case_id"] for c in cases}:
            raise D10ArtifactError("quota", "unknown_case",
                                   f"attack row references unknown case {row['case_id']}")
        if row["case_id"] in seen_cases:
            raise D10ArtifactError("quota", "duplicate_row",
                                   f"attack row duplicated for {row['case_id']}")
        seen_cases.add(row["case_id"])
        for aid in row["attack_ids"]:
            if aid not in ATTACK_IDS:
                raise D10ArtifactError("quota", "unknown_attack",
                                       f"unknown attack id {aid!r}")
            counts[aid] += 1
    for aid in ATTACK_IDS:
        if counts[aid] < 1:
            raise D10ArtifactError("quota", "attack_below_floor",
                                   f"mandatory attack {aid} has 0 cases")
        if counts[aid] != manifest["actual_mandatory_attack_counts"][aid]:
            raise D10ArtifactError("quota", "attack_count_mismatch",
                                   f"attack {aid} count mismatch")


def validate_quota_manifest(manifest: dict[str, Any],
                            catalog: dict[str, Any]) -> None:
    expect_exact_keys(manifest, QUOTA_TOP_KEYS, "quota manifest top-level")
    if manifest["manifest_id"] != QUOTA_MANIFEST_ID:
        raise D10ArtifactError("schema_parse", "schema_error",
                               "quota manifest_id mismatch")
    if manifest["required_total"] != REQUIRED_TOTAL:
        raise D10ArtifactError("schema_parse", "schema_error",
                               "required_total mismatch")
    if manifest["catalog_hash"] != catalog["catalog_hash"]:
        raise D10ArtifactError("catalog_hash", "stale_hash",
                               "quota catalog_hash mismatch")
    for entry in manifest["primary_partition_requirements"]:
        expect_exact_keys(entry, PARTITION_REQUIREMENT_KEYS,
                          "primary_partition_requirement")
    for entry in manifest["mandatory_attack_requirements"]:
        expect_exact_keys(entry, ATTACK_REQUIREMENT_KEYS, "mandatory_attack_requirement")
    cases = catalog["cases"]
    by_partition = _partition_counts(cases)
    for pid, _, minimum in PARTITIONS:
        actual = manifest["actual_primary_partition_counts"][pid]
        if actual != len(by_partition.get(pid, [])):
            raise D10ArtifactError("quota", "partition_count_mismatch",
                                   f"partition {pid} count mismatch")
        if actual < minimum:
            raise D10ArtifactError("quota", "below_floor",
                                   f"partition {pid} {actual} < {minimum}")
    total = sum(manifest["actual_primary_partition_counts"].values())
    if total != manifest["union_count"] or total != len(cases):
        raise D10ArtifactError("quota", "union_mismatch",
                               "partition totals != union count != case count")
    if manifest["duplicate_case_ids"] or manifest["missing_case_ids"]:
        raise D10ArtifactError("quota", "duplicate_or_missing",
                               "duplicate/missing case ids present")
    if any(v != 0 for v in manifest["pairwise_intersection_counts"].values()):
        raise D10ArtifactError("quota", "intersection_nonempty",
                               "primary partitions must be pairwise disjoint")
    if manifest["union_count"] != len(manifest["case_id_union"]):
        raise D10ArtifactError("quota", "union_mismatch", "union count mismatch")
    _mandatory_attack_mapping(cases, manifest)
    if manifest["manifest_hash"] != content_hash(manifest, "manifest_hash"):
        raise D10ArtifactError("quota", "stale_hash",
                               "quota manifest content hash mismatch")


def validate_registry(registry: dict[str, Any], catalog: dict[str, Any]) -> None:
    expect_exact_keys(registry, REGISTRY_TOP_KEYS, "registry top-level")
    if registry["registry_id"] != REGISTRY_ID:
        raise D10ArtifactError("schema_parse", "schema_error", "registry_id mismatch")
    if registry["catalog_hash"] != catalog["catalog_hash"]:
        raise D10ArtifactError("catalog_hash", "stale_hash",
                               "registry catalog_hash mismatch")
    expect_exact_keys(registry["oracle_reference_state"], ORACLE_REFERENCE_STATE_KEYS,
                      "registry oracle_reference_state")
    state = registry["oracle_reference_state"]["state"]
    if state not in REGISTRY_RESOLUTION_STATES:
        raise D10ArtifactError("schema_parse", "schema_error",
                               f"registry oracle state {state!r} not in "
                               f"{REGISTRY_RESOLUTION_STATES}")
    rows = registry["rows"]
    if len(rows) != catalog["case_count"]:
        raise D10ArtifactError("registry", "row_count_mismatch",
                               "registry row count != case count")
    seen: dict[str, set[str]] = {col: set() for col in BIJECTION_COLUMNS}
    for row in rows:
        expect_exact_keys(row, REGISTRY_ROW_KEYS, "registry row")
        for col in BIJECTION_COLUMNS:
            value = row[col]
            if value in seen[col]:
                raise D10ArtifactError("bijection", "duplicate",
                                       f"registry {col} duplicate {value}")
            seen[col].add(value)
    case_by_id = {c["case_id"]: c for c in catalog["cases"]}
    for row in rows:
        case = case_by_id.get(row["case_id"])
        if case is None:
            raise D10ArtifactError("bijection", "unknown_case",
                                   f"registry row unknown case {row['case_id']}")
        for col, key in (("fixture_id", "fixture_id"),
                         ("oracle_case_id", "oracle_case_id"),
                         ("manifest_case_id", "manifest_case_id")):
            if row[col] != case[key]:
                raise D10ArtifactError("bijection", "mismatch",
                                       f"registry {col} != catalog {key} for "
                                       f"{row['case_id']}")
    audit = registry["bijection_audit"]
    if audit["row_count"] != len(rows) or not audit["bijection_ok"]:
        raise D10ArtifactError("bijection", "audit_failed",
                               "registry bijection audit failed")
    if registry["content_hash"] != content_hash(registry, "content_hash"):
        raise D10ArtifactError("registry", "stale_hash",
                               "registry content hash mismatch")


def _registry_core(registry: dict[str, Any]) -> dict[str, Any]:
    """Projection of a registry onto its stage-A-owned fields: everything the
    provisional generation owns, minus the declared stage-B deltas."""
    core: dict[str, Any] = {key: item for key, item in registry.items()
                            if key not in RESOLVED_DELTA_TOP}
    reference = {key: item for key, item in
                 registry["oracle_reference_state"].items()
                 if key not in RESOLVED_DELTA_REFERENCE}
    core["oracle_reference_state"] = reference
    return core


def verify_resolved_registry(registry: dict[str, Any],
                             catalog: dict[str, Any]) -> None:
    """Stage-B declared verification of the worker_02 resolution linkage.
    Oracle-blind: never reads the oracle artifact or expected leaves."""
    validate_registry(registry, catalog)
    reference = registry["oracle_reference_state"]
    if reference["state"] != "resolved":
        raise D10ArtifactError("registry", "not_resolved",
                               "stage-B verification requires "
                               "oracle_reference_state state=resolved")
    if reference["reserved_for"] != "worker_02":
        raise D10ArtifactError("registry", "delta_mismatch",
                               f"reserved_for {reference['reserved_for']!r} "
                               "!= worker_02")
    if reference["oracle_artifact_path"] != DECLARED_ORACLE_ARTIFACT_PATH:
        raise D10ArtifactError("registry", "delta_mismatch",
                               "oracle_artifact_path != declared")
    if reference["catalog_expected_fields"] != "null":
        raise D10ArtifactError("registry", "delta_mismatch",
                               "catalog_expected_fields must remain 'null'")
    if registry["generator_hash"] != STAGE_A_GENERATOR_SHA256:
        raise D10ArtifactError("registry", "generator_hash",
                               "generator_hash != STAGE_A_GENERATOR_SHA256 pin")
    base_policy = (
        "expected leaves exist only in the independent oracle artifact; "
        "catalog expected_* fields remain literal null; forbidden leaves "
        "per contract section 15")
    policy = reference["expected_leaf_policy"]
    if not policy.startswith(base_policy):
        raise D10ArtifactError("registry", "delta_mismatch",
                               "expected_leaf_policy must extend the stage-A "
                               "policy verbatim")
    suffix = policy[len(base_policy):]
    if not suffix.startswith(RESOLVED_POLICY_SUFFIX_PREFIX):
        raise D10ArtifactError("registry", "delta_mismatch",
                               "expected_leaf_policy must gain the oracle "
                               "content_hash suffix")
    oracle_hash = suffix[len(RESOLVED_POLICY_SUFFIX_PREFIX):]
    if not sha256_hex(oracle_hash):
        raise D10ArtifactError("registry", "delta_mismatch",
                               "oracle content_hash suffix malformed")
    # The resolved registry must be exactly the fresh provisional registry
    # plus the declared delta (oracle-blind): rebuild the provisional core.
    provisional = dict(_registry_core(registry))
    provisional["oracle_reference_state"] = dict(
        registry["oracle_reference_state"])
    provisional["oracle_reference_state"]["state"] = "unresolved"
    provisional["oracle_reference_state"]["expected_leaf_policy"] = base_policy
    provisional["content_hash"] = ""
    provisional["content_hash"] = content_hash(provisional, "content_hash")
    # Rebuild what stage A would have produced for this catalog.
    quota_provisional = assemble_quota_manifest(catalog)
    fresh = assemble_registry(catalog, quota_provisional,
                              STAGE_A_GENERATOR_SHA256)
    if _registry_core(fresh) != _registry_core(provisional):
        raise D10ArtifactError("registry", "delta_mismatch",
                               "resolved registry core differs from a fresh "
                               "stage-A provisional registry (undeclared delta)")
    return oracle_hash


def distribution_check(catalog: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in catalog["cases"]:
        counts[case["primary_partition"]] = counts.get(case["primary_partition"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Stage-B resolution (deterministic, oracle-blind; worker_02 linkage)
# ---------------------------------------------------------------------------
def resolve_stage_b(registry: dict[str, Any], quota_manifest: dict[str, Any],
                    oracle_content_hash: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (resolved_registry, resolved_quota) applying exactly the
    declared stage-B delta. oracle_content_hash is passed in (never read from
    the oracle artifact). Deterministic: same inputs -> same outputs."""
    if not sha256_hex(oracle_content_hash):
        raise D10ArtifactError("registry", "delta_mismatch",
                               "oracle content hash must be 64 lowercase hex")
    if registry["oracle_reference_state"]["state"] != "unresolved":
        raise D10ArtifactError("registry", "refuse_clobber",
                               "registry is not provisional (cannot re-resolve)")
    resolved = json.loads(canonical_json(registry))
    base_policy = resolved["oracle_reference_state"]["expected_leaf_policy"]
    resolved["oracle_reference_state"]["state"] = "resolved"
    resolved["oracle_reference_state"]["expected_leaf_policy"] = (
        base_policy + RESOLVED_POLICY_SUFFIX_PREFIX + oracle_content_hash)
    resolved["content_hash"] = ""
    resolved["content_hash"] = content_hash(resolved, "content_hash")
    resolved_quota = json.loads(canonical_json(quota_manifest))
    resolved_quota["oracle_hash"] = oracle_content_hash
    resolved_quota["registry_hash"] = resolved["content_hash"]
    resolved_quota["manifest_hash"] = ""
    resolved_quota["manifest_hash"] = content_hash(resolved_quota, "manifest_hash")
    return resolved, resolved_quota


def _quota_is_resolved(manifest: dict[str, Any]) -> bool:
    return (manifest.get("oracle_hash") != PROVISIONAL_HASH_SENTINEL
            and manifest.get("registry_hash") != PROVISIONAL_HASH_SENTINEL)


def validate_resolved_quota(manifest: dict[str, Any],
                            registry: dict[str, Any]) -> None:
    """Oracle-blind verification of the resolved quota chain linkage."""
    if not _quota_is_resolved(manifest):
        raise D10ArtifactError("quota", "not_resolved",
                               "quota manifest is not resolved")
    if manifest["generator_hash"] != STAGE_A_GENERATOR_SHA256:
        raise D10ArtifactError("quota", "generator_hash",
                               "quota generator_hash != stage-A pin")
    reference = registry["oracle_reference_state"]
    if reference["state"] != "resolved":
        raise D10ArtifactError("quota", "not_resolved",
                               "registry must be resolved to validate quota")
    base_policy = (
        "expected leaves exist only in the independent oracle artifact; "
        "catalog expected_* fields remain literal null; forbidden leaves "
        "per contract section 15")
    suffix = reference["expected_leaf_policy"][len(base_policy):]
    oracle_hash = suffix[len(RESOLVED_POLICY_SUFFIX_PREFIX):]
    if manifest["oracle_hash"] != oracle_hash:
        raise D10ArtifactError("quota", "delta_mismatch",
                               "quota oracle_hash != registry oracle suffix")
    if manifest["registry_hash"] != content_hash(registry, "content_hash"):
        raise D10ArtifactError("quota", "delta_mismatch",
                               "quota registry_hash != registry content hash")
    if manifest["manifest_hash"] != content_hash(manifest, "manifest_hash"):
        raise D10ArtifactError("quota", "stale_hash",
                               "quota manifest content hash mismatch")


# ---------------------------------------------------------------------------
# Render pipeline + CLI
# ---------------------------------------------------------------------------
def _generate_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Assemble catalog, quota manifest, registry and validate everything,
    including conformance of every case against the fixed fixture authority."""
    validate_contract()
    catalog = assemble_catalog()
    validate_catalog(catalog)
    validate_authority_conformance(catalog, load_authority())
    quota_manifest = assemble_quota_manifest(catalog)
    validate_quota_manifest(quota_manifest, catalog)
    generator_hash = _generator_code_hash()
    registry = assemble_registry(catalog, quota_manifest, generator_hash)
    validate_registry(registry, catalog)
    return catalog, quota_manifest, registry, generator_hash


def _artifact_bytes(*artifacts: dict[str, Any]) -> list[bytes]:
    return [canonical_json(a).encode("utf-8") for a in artifacts]


def render_artifacts(verbose: bool = True, out_dir: Path | None = None) -> dict[str, Any]:
    def log(message: str) -> None:
        if verbose:
            print(message)

    log("D10 typed artifact generator (worker_01)")
    log("=" * 72)
    validate_contract()
    log(f"contract file/semantic SHA-256: {CONTRACT_FILE_SHA256}  OK (v0.6 frozen pin)")

    catalog_path = (out_dir / CATALOG.name) if out_dir else CATALOG
    quota_path = (out_dir / QUOTA.name) if out_dir else QUOTA
    registry_path = (out_dir / REGISTRY.name) if out_dir else REGISTRY

    catalog_a, quota_a, registry_a, generator_hash = _generate_all()
    catalog_b, quota_b, registry_b, _ = _generate_all()
    bytes_a = _artifact_bytes(catalog_a, quota_a, registry_a)
    bytes_b = _artifact_bytes(catalog_b, quota_b, registry_b)
    if bytes_a != bytes_b:
        raise D10ArtifactError("replay", "drift",
                               "double-pass byte mismatch (nondeterministic generator)")
    log(f"double-pass byte-identical: catalog {len(bytes_a[0])} B, "
        f"quota {len(bytes_a[1])} B, registry {len(bytes_a[2])} B  OK")

    for path, label in ((registry_path, "registry"), (quota_path, "quota manifest")):
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise D10ArtifactError(label, "unreadable",
                                       f"existing {label} {path} unreadable: {exc}")
            resolved = label == "registry" and existing.get(
                "oracle_reference_state", {}).get("state") == "resolved"
            if label == "quota manifest" and _quota_is_resolved(existing):
                resolved = True
            if resolved:
                raise D10ArtifactError(
                    label, "refuse_clobber",
                    f"{path} is a resolved stage-B artifact; stage-A render "
                    "must not overwrite the worker_02 resolution. Use --check "
                    "or --resolve-stage-b to verify/regenerate the resolution.")

    counts = distribution_check(catalog_a)
    log("\npartition distribution (required -> actual):")
    for partition, label, minimum in PARTITIONS:
        actual = counts.get(partition, 0)
        flag = "OK" if actual >= minimum else "BELOW FLOOR"
        log(f"  {partition:<42} {minimum:3d} -> {actual:3d}  {flag}")
    log(f"  {'TOTAL':<42} {MIN_CASE_COUNT:3d} -> {len(catalog_a['cases']):3d}  "
        f"({'OK' if len(catalog_a['cases']) >= MIN_CASE_COUNT else 'BELOW FLOOR'})")

    for path, payload, label in ((catalog_path, catalog_a, "catalog"),
                                 (quota_path, quota_a, "quota manifest"),
                                 (registry_path, registry_a, "registry")):
        payload_bytes = canonical_json(payload).encode("utf-8")
        path.write_bytes(payload_bytes)
        log(f"\nwrote {path} ({len(payload_bytes)} bytes)")
        reloaded = json.loads(path.read_text(encoding="utf-8"))
        if canonical_json(reloaded).encode("utf-8") != payload_bytes:
            raise D10ArtifactError("replay", "drift", f"{label} reload byte mismatch")
    validate_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    validate_quota_manifest(json.loads(quota_path.read_text(encoding="utf-8")),
                            json.loads(catalog_path.read_text(encoding="utf-8")))
    validate_registry(json.loads(registry_path.read_text(encoding="utf-8")),
                      json.loads(catalog_path.read_text(encoding="utf-8")))
    log("reload validation  OK")

    log(f"\ncatalog_id    : {catalog_a['catalog_id']}")
    log(f"case_count    : {catalog_a['case_count']}  "
        f"catalog_hash: {catalog_a['catalog_hash']}")
    log(f"quota manifest: {quota_a['manifest_id']}  "
        f"manifest_hash: {quota_a['manifest_hash']}")
    log(f"registry_id   : {registry_a['registry_id']}  "
        f"content_hash: {registry_a['content_hash']}")
    log(f"generator_hash: {generator_hash}")
    log("worker_01/worker_02 two-stage handoff (Codex):")
    log("  - expected_* fields are literal null in the catalog; no expected leaves exist")
    log("  - stage A provisional registry oracle_reference_state=unresolved; generator")
    log("    never reads the oracle for generation (import/read closure)")
    log("  - stage B: --resolve-stage-b finalizes registry + quota linkage, verified")
    log("    oracle-blind by verify_resolved_registry()/validate_resolved_quota()")
    return {"catalog": catalog_a, "quota_manifest": quota_a, "registry": registry_a}


def check_artifacts(verbose: bool = True) -> int:
    """--check mode (two-stage contract): regenerate twice, validate, compare
    catalog/quota bytes with on-disk artifacts (quota in provisional state),
    then run oracle-blind stage-B verification on the resolved artifacts.
    Never writes."""
    def log(message: str) -> None:
        if verbose:
            print(message)

    try:
        validate_contract()
        log("contract SHA-256 OK (v0.6 frozen pin)")
        catalog_a, quota_a, registry_a, generator_hash = _generate_all()
        catalog_b, quota_b, registry_b, _ = _generate_all()
        bytes_a = _artifact_bytes(catalog_a, quota_a, registry_a)
        bytes_b = _artifact_bytes(catalog_b, quota_b, registry_b)
        if bytes_a != bytes_b:
            raise D10ArtifactError("replay", "drift",
                                   "two fresh generations are NOT byte-identical")
        log("two fresh generations byte-identical  OK")
        if not CATALOG.exists() or not QUOTA.exists() or not REGISTRY.exists():
            raise D10ArtifactError("check", "missing",
                                   "--check: catalog/quota/registry must exist "
                                   "(run render without --check first)")
        on_disk_catalog = CATALOG.read_bytes()
        if on_disk_catalog != canonical_json(catalog_a).encode("utf-8"):
            raise D10ArtifactError("check", "drift",
                                   "--check: catalog differs from fresh generation")
        log(f"catalog matches fresh generation ({len(on_disk_catalog)} B)  OK")
        on_disk_quota = json.loads(QUOTA.read_text(encoding="utf-8"))
        if _quota_is_resolved(on_disk_quota):
            # Stage B: quota is the resolved chain-summary; verify oracle-blind
            # linkage against the resolved registry.
            on_disk_registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
            verify_resolved_registry(on_disk_registry, catalog_a)
            validate_resolved_quota(on_disk_quota, on_disk_registry)
            log("resolved quota oracle-blind chain verification OK")
        else:
            if canonical_json(on_disk_quota).encode("utf-8") != \
                    canonical_json(quota_a).encode("utf-8"):
                raise D10ArtifactError("check", "drift",
                                       "--check: provisional quota differs "
                                       "from fresh generation")
            log("provisional quota matches fresh generation  OK")
            on_disk_registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
            verify_resolved_registry(on_disk_registry, catalog_a)
        log(f"check passed: case_count={catalog_a['case_count']} "
            f"catalog_hash={catalog_a['catalog_hash']} "
            f"generator_hash={generator_hash}")
        return 0
    except D10ArtifactError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def resolve_stage_b_cli(oracle_hash: str, verbose: bool = True) -> int:
    """--resolve-stage-b: read provisional on-disk artifacts, apply the
    declared deterministic delta, write resolved registry + quota. Oracle-blind
    (the oracle hash is passed on the command line; the oracle artifact is
    never read)."""
    def log(message: str) -> None:
        if verbose:
            print(message)

    try:
        validate_contract()
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        validate_catalog(catalog)
        provisional_quota = json.loads(QUOTA.read_text(encoding="utf-8"))
        provisional_registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        resolved_registry, resolved_quota = resolve_stage_b(
            provisional_registry, provisional_quota, oracle_hash)
        verify_resolved_registry(resolved_registry, catalog)
        validate_resolved_quota(resolved_quota, resolved_registry)
        for path, payload, label in ((REGISTRY, resolved_registry, "registry"),
                                     (QUOTA, resolved_quota, "quota manifest")):
            payload_bytes = canonical_json(payload).encode("utf-8")
            path.write_bytes(payload_bytes)
            reloaded = json.loads(path.read_text(encoding="utf-8"))
            if canonical_json(reloaded).encode("utf-8") != payload_bytes:
                raise D10ArtifactError("replay", "drift",
                                       f"{label} reload byte mismatch")
            log(f"wrote resolved {label} -> {path} ({len(payload_bytes)} B)")
        log(f"stage-B resolution OK: oracle_hash={oracle_hash}")
        return 0
    except D10ArtifactError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="D10 typed artifact generator (worker_01)")
    parser.add_argument("--check", action="store_true",
                        help="regenerate twice, validate, compare with on-disk; no writes")
    parser.add_argument("--resolve-stage-b", metavar="ORACLE_HASH", default=None,
                        help="apply the declared worker_02 stage-B delta using the "
                             "given oracle content hash (oracle-blind)")
    parser.add_argument("--out", type=Path, default=None,
                        help="write artifacts to this directory instead of reviews/")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = parser.parse_args()
    try:
        if args.check:
            return check_artifacts(verbose=not args.quiet)
        if args.resolve_stage_b is not None:
            return resolve_stage_b_cli(args.resolve_stage_b, verbose=not args.quiet)
        render_artifacts(verbose=not args.quiet, out_dir=args.out)
        return 0
    except D10ArtifactError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
