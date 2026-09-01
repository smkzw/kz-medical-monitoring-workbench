#!/usr/bin/env python3
"""D09 typed artifact generator (worker_01, finite code executor).

Builds the frozen R4-D09 v0.5 synthetic/offline typed-fixture catalog, the
challenge-manifest registry (identity rows + unresolved oracle reference state
only), and the partition quota manifest with a disjoint-union proof.

Contract source of truth (frozen, immutable SHA):
    reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md
    SHA-256 9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40

Hard boundaries (execution context + contract §16):
  * This module NEVER derives, infers, computes or writes expected outcomes.
    The catalog's three expected_* fields are literal JSON null; the registry
    holds deterministic identity rows with oracle_resolution="unresolved" for
    worker_02; expected leaves exist only in the independent oracle artifact.
  * This module NEVER reads the oracle or the registry (import/read closure).
  * Standard library only. No network, no wall-clock, no randomness.
  * Deterministic: two fresh generations are byte-identical (canonical UTF-8,
    NFC, no-whitespace JSON, sorted keys, stable array ordering, finite
    decimals only, SHA-256).

Design decisions (documented for the independent verifier):
  D1. Case-level `pattern_kind` is one of the three medical kinds for
      evaluate_and_own cases, the control-plane label "routing_gate" for
      unresolved-token routing cases, and null for known consume-only cases
      (no D09 pattern kind applies; zero D09 medical units).
  D2. Five L1 dispositions only (§9). Pre-admission gate / authority / routing
      cases (zero medical units) carry disposition "not_applicable" (design
      clause / legal matrix proves the evaluation does not apply); admitted
      units with L1 deficiencies carry "not_evaluable".
  D3. Per-case `fixture_hash` = SHA-256 of canonical JSON of typed_input.
      Registry rows additionally carry `substantive_input_hash` (typed_input
      with run/snapshot/revision/version/wall-clock tokens stripped).
  D4. pattern_definition carries the contract §3.2 field list plus two
      documented optional keys: `required_window_count_ref` (trend only) and
      `minimum_member_subject_count_ref` (null when not declared).
  D5. typed_input declares input-side authority/admission facts in the
      `expected_set` section (admitted | global_admission_failed |
      routed_consume_only | routing_gate_unresolved). This is input state,
      never an expected outcome; the oracle derives units/leaves from it.
  D6. TWO-STAGE REGISTRY CONTRACT (worker_03 bounded correction, 2026-08-15).
      Stage A is this module: it deterministically assembles catalog + quota
      manifest + a PROVISIONAL registry whose rows are oracle_resolution=
      "unresolved" and whose oracle_reference_state.state="unresolved".
      Stage B is worker_02's accepted resolution: the registry artifact was
      resolved in place (every row oracle_resolution="resolved",
      oracle_reference_state.state="resolved", and expected_leaf_policy gains
      the suffix '; oracle artifact content_hash=<sha256>'). This module never
      reads the oracle artifact and never derives expected leaves; the declared
      stage-B linkage is validated oracle-blind by verify_resolved_registry()
      (structural delta check) and, for the deep oracle linkage (suffix hash ==
      oracle content_hash, 179-row oracle bijection), by
      tests/test_d09_artifact_generator.py. --check therefore verifies catalog
      and quota byte-for-byte against disk and runs stage-B verification on the
      resolved registry; render refuses to overwrite a resolved registry
      (fail-closed) so stage A can never clobber worker_02 resolution.
  D7. Every decisive input fact is carried as a contract-authorized typed_input
      field (worker_03 follow-up, 2026-08-15; no oracle-side semantic tags):
      - `pattern_definition.counterevidence_rule_refs` declares the
        counterevidence rules; `matched_counterevidence_rule_refs` (typed_input
        envelope) declares which of them matched. Level is derived: declared
        empty -> condition_absent; matched empty -> none; matched == declared
        -> full; proper subset -> partial.
      - `mode_contract_design_clause_ref` (typed_input envelope, nullable)
        declares the locatable ModeContract design clause that makes a
        closed-zero denominator not_applicable (contract §6.3).
      - member `cutoff_relation` (D09InboundRiskMember) is the decisive cutoff
        fact; member `source_locator_resolution_state` and gap
        `anchor_resolution_state` carry the resolved deep-link
        deficiency; coverage `accepted_current=false` declares the
        producer-ref-unresolvable integrity block; a declared source content
        hash that differs from sha256("d09-rev:<revision>") declares the
        source-hash-mismatch integrity block; visibility
        `rate_projection_state="qualified"` declares the visibility boundary;
        `origin_decision=verified_same_origin` + shared
        `public_r4_risk_identity` declare the same-origin dedup groups.
  D8. The resolved registry's `generator_hash` is validated against the frozen
      STAGE_A_GENERATOR_SHA256 pin (never treated as an arbitrary delta);
      generator_hash is NOT part of the stage-B delta set.
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
CONTRACT = ROOT / "reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md"
CATALOG = ROOT / "reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json"
REGISTRY = ROOT / "reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json"
QUOTA = ROOT / "reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json"

# ---------------------------------------------------------------------------
# Two-stage registry contract (worker_03 documented decision, see docstring D6)
# ---------------------------------------------------------------------------
# Path of the independent oracle artifact. Declared for stage-B verification
# only; this module NEVER reads the file or its content.
DECLARED_ORACLE_ARTIFACT_PATH = "reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json"
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
RESOLVED_DELTA_ROW = frozenset({"oracle_resolution"})
# Frozen stage-A generator SHA: the exact catalog-generator revision that
# produced the catalog/quota/registry chain. The resolved registry's
# `generator_hash` field must equal this pin exactly; altered generator_hash
# (even with a consistent content_hash reseal) fails closed.
#
# The pin is self-referential by design: it hashes THIS generator file with
# the pin literal itself normalized to 64 zeros (_generator_code_hash), so the
# pin value does not feed back into the hash. Any other edit to the generator
# source changes the code hash and fails closed.
_PIN_SENTINEL = "0" * 64
STAGE_A_GENERATOR_SHA256 = (
    "ea5e56a9b5996003122149b7d12317e13a7ce16246c3090a2757cf89b42aee23"
)


def _generator_code_hash() -> str:
    """SHA-256 of this generator file with the self-referential pin literal
    normalized to the sentinel. Deterministic and immune to pin feedback."""
    text = Path(__file__).resolve().read_text(encoding="utf-8")
    return sha256_text(text.replace(STAGE_A_GENERATOR_SHA256, _PIN_SENTINEL))

# ---------------------------------------------------------------------------
# Frozen contract snapshot (accepted immutable SHA, acceptance record 2026-08-14)
# ---------------------------------------------------------------------------
CONTRACT_FILE_SHA256 = "9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40"
CONTRACT_SEMANTIC_HASH = CONTRACT_FILE_SHA256

# ---------------------------------------------------------------------------
# Artifact identity constants
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "1.0.0"
CATALOG_ID = "medical-monitoring-r4-d09-typed-fixture-catalog-v1"
REGISTRY_ID = "medical-monitoring-r4-d09-challenge-manifest-registry-v1"
QUOTA_MANIFEST_ID = "medical-monitoring-r4-d09-partition-quota-manifest-v1"
TYPED_INPUT_SCHEMA = "d09-typed-input-v1"
ALGORITHM_VERSION = "d09_v1"
PUBLIC_IDENTITY_VERSION = "d09_public_v1"

# Canonical synthetic scope (offline only; no real project/patient data).
PROJECT_REF = "SYN-D09-PROJECT-001"
SITE_REF = "SYN-D09-SITE-001"
SITE_REF_2 = "SYN-D09-SITE-002"
RUN_REF = "SYN-D09-RUN-001"
SNAPSHOT_REF = "SYN-D09-SNAP-001"
MONITORING_MODE = "offline_synthetic"

# ---------------------------------------------------------------------------
# Closed enums (frozen from contract v0.5 text)
# ---------------------------------------------------------------------------
DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")
PATTERN_KINDS = ("repeated_subject_risk", "systematic_data_or_process_gap", "within_site_time_trend")
OWNER_ROUTES = ("evaluate_and_own", "consume_only", "handoff_only", "context_only", "routing_gate")
OWNER_DOMAINS = ("D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10")

CLINICAL_CLAIM_TOKENS = (
    "d09_repeated_subject_risk", "d09_systematic_data_or_process_gap",
    "d09_within_site_time_trend", "d06_site_efficacy_rate", "d06_estimand",
    "d10_cross_site_outlier", "d10_treatment_arm_compare", "d10_project_trend",
    "d01_d08_individual_fact", "unresolved",
)
OWNED_TOKENS = frozenset({
    "d09_repeated_subject_risk", "d09_systematic_data_or_process_gap",
    "d09_within_site_time_trend",
})
TOKEN_KIND_BIJECTION = {
    "d09_repeated_subject_risk": "repeated_subject_risk",
    "d09_systematic_data_or_process_gap": "systematic_data_or_process_gap",
    "d09_within_site_time_trend": "within_site_time_trend",
}
CONSUME_ONLY_TOKENS = (
    "d06_site_efficacy_rate", "d06_estimand", "d10_cross_site_outlier",
    "d10_treatment_arm_compare", "d10_project_trend", "d01_d08_individual_fact",
)

RISK_KINDS = (
    "d01_seriousness_hospital_death", "d02_cm_indication_match",
    "d03_assignment_exposure", "d04_criterion_waiver_pd",
    "d05_planned_actual", "d06_score_timepoint",
    "d08_cross_domain_relation", "d07_coverage_or_gap",
)
GAP_KINDS = (
    "missing_required_field", "missing_required_assessment",
    "missing_required_lab", "missing_required_procedure",
    "unreported_ae", "pd_unreported",
)
MONITORING_PRIORITIES = ("high", "medium", "low")
CUTOFF_RELATIONS = ("in_cutoff", "out_of_cutoff", "spans_cutoff", "time_missing_not_evaluable")
ORIGIN_DECISIONS = ("verified_same_origin", "distinct", "ambiguous", "wrong_scope", "not_evaluable")
L0_STATUSES = ("covered", "missing", "partial", "truncated", "not_evaluable", "failed")
L1_STATES = ("complete", "partial", "not_evaluable", "missing")
DENOMINATOR_KINDS = (
    "enrolled_subjects", "treated_subjects", "evaluable_subjects",
    "subject_time", "exposure_time", "expected_assessment_opportunities",
)
DENOMINATOR_STATES = ("closed_positive", "closed_zero", "unclosed")
OPPORTUNITY_STATES = ("sufficient", "insufficient", "unknown")
OPPORTUNITY_PROVENANCES = (
    "accepted_d05_plan", "accepted_shared_plan", "accepted_producer_obligation",
    "raw_listing_only", "enumeration_conflict",
)
WINDOW_KINDS = (
    "calendar_interval", "study_day_interval", "subject_time_interval",
    "exposure_time_interval",
)
ANCHOR_KINDS = (
    "calendar_date", "site_activation", "consent", "randomization",
    "first_dose", "domain_event",
)
WINDOW_STATES = ("closed", "open")
STRATUM_STATES = ("closed", "open", "empty")
STRATUM_ADMISSIONS = ("admitted", "rejected_empty", "fanout_rejected", "not_required")
COMPARABLE_STATES = ("comparable", "boundary", "not_evaluable")
CHANGE_KINDS = ("increased", "decreased", "unchanged", "not_comparable")
CHANGE_CAUSES = ("data", "denominator", "coverage", "rule_or_mapping", "method", "mixed")
EXPECTED_SET_STATES = ("admitted", "global_admission_failed", "routed_consume_only",
                       "routing_gate_unresolved")
GATE_KINDS = ("cartesian_definition_fanout", "stratum_fanout", "legal_matrix_row_absent",
              "global_integrity", "cutoff_identity_conflict")
BLIND_STATUSES = ("blinded", "unblinded_authorized")
RATE_PROJECTION_STATES = ("permitted", "suppressed", "qualified")
MUTATION_CLASSES = (
    "none", "revision_repeat", "export_repeat", "order_shuffle", "display_rename",
    "same_origin_verified", "origin_ambiguous", "origin_wrong_scope", "origin_distinct",
    "coverage_missing", "coverage_partial", "coverage_truncated", "coverage_failed",
    "cutoff_all_out", "cutoff_mixed", "cutoff_spans", "time_missing", "cutoff_conflict",
    "revision_vs_event_time", "single_window", "window_shift", "window_definition_change",
    "stratum_change", "signal_unexpandable", "validity_insufficient", "statistics_only",
    "comparability_passes", "query_non_redundant", "query_fully_covered",
    "query_members_unlistable", "query_fanout_exceeded", "query_no_process_delta",
    "consume_only", "routing_gate", "l1_hole_zero_risk", "gap_only", "cartesian_rejected",
    "stratum_fanout_rejected", "stratum_required_empty", "visibility_hidden",
    "blinded_stratum_rejected", "authorized_unblinded", "carry_forward",
    "evidence_ref_shared", "n1_minimum", "authority_fail", "raw_only_provenance",
    "opportunity_conflict", "lifecycle_member_closed", "lifecycle_coverage_broken",
    "lifecycle_high_priority", "rule_supersession", "site_merge_split",
    "r5_side_by_side", "anti_overfit_rename", "anti_overfit_shuffle",
)

# ---------------------------------------------------------------------------
# Frozen schema: exact key sets
# ---------------------------------------------------------------------------
CATALOG_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
CASE_KEYS = [
    "case_id", "primary_partition_id", "family_id", "pattern_kind", "owner_route",
    "clinical_claim_token", "disposition", "fixture_id", "fixture_hash",
    "oracle_case_id", "manifest_case_id", "expected_leaf_set",
    "expected_trace_leaf_set", "expected_source_leaf_set", "mutation_class",
    "audience_contract", "typed_input",
]
AUDIENCE_CONTRACT_KEYS = [
    "audience_contract_id", "audience_scope_id", "blind_status",
    "authorized_unblinded_contract_ref", "display_language", "projection_contract_ref",
]

REGISTRY_TOP_KEYS = [
    "artifact_kind", "registry_id", "schema_version", "contract_semantic_hash",
    "catalog_hash", "quota_manifest_hash", "generator_hash",
    "oracle_reference_state", "rows", "bijection_audit", "content_hash",
]
REGISTRY_ROW_KEYS = [
    "case_id", "fixture_id", "oracle_case_id", "manifest_case_id", "test_id",
    "oracle_resolution", "substantive_input_hash",
]
BIJECTION_COLUMNS = ["case_id", "fixture_id", "oracle_case_id", "manifest_case_id", "test_id"]
ORACLE_REFERENCE_STATE_KEYS = [
    "state", "reserved_for", "oracle_artifact_path", "expected_leaf_policy",
    "catalog_expected_fields",
]

QUOTA_TOP_KEYS = [
    "artifact_kind", "manifest_id", "schema_version", "contract_semantic_hash",
    "catalog_hash", "total_case_count", "total_required_minimum", "partitions",
    "disjoint_union_proof", "content_hash",
]
PARTITION_ENTRY_KEYS = [
    "partition_id", "partition_label_zh", "required_minimum", "actual_count",
    "sorted_case_ids", "partition_hash",
]
DISJOINT_UNION_PROOF_KEYS = [
    "union_case_count", "union_sorted_case_ids", "catalog_case_id_set_equal",
    "pairwise_disjoint", "duplicate_case_ids", "missing_case_ids", "proof_hash",
]

# typed_input envelope (26 exact keys)
TYPED_INPUT_KEYS = [
    "input_schema", "envelope_id", "project_ref", "run_ref", "snapshot_ref",
    "source_revision_set", "source_content_hashes", "site_stable_id",
    "scope_binding", "pattern_definition", "mode_contract_version",
    "matched_counterevidence_rule_refs", "mode_contract_design_clause_ref",
    "analysis_windows", "stratum", "coverage", "subject_risk_members",
    "gap_members", "change_ledger_members", "denominator", "opportunity",
    "cutoff", "numeric_policy", "visibility_decision", "expected_set",
    "mutation_context", "anti_overfit_variant", "evidence_refs",
    "audience_lexicon",
    "resolved_authority_decision", "method_comparability_decision",
    "lineage_context", "center_query_policy", "query_redundancy_decision",
    "source_verification_records",
]
RESOLVED_AUTHORITY_KEYS = [
    "minimum_member_subject_count", "gap_positive_minimum_opportunity_count",
    "trend_positive_minimum_subject_count", "authority_validity_state",
    "authority_ref", "authority_locator_ref", "mode_contract_version",
    "authority_content_hash",
]
METHOD_COMPARABILITY_KEYS = [
    "method_validity_state", "statistical_signal_role",
    "member_expansion_state", "window_rule_version_refs",
    "stratum_method_version_refs",
]
LINEAGE_CONTEXT_KEYS = [
    "prior_risk_instance_ref", "prior_public_risk_identity_ref",
    "carry_forward_state", "lineage_relation", "site_identity_state",
]
CENTER_QUERY_POLICY_KEYS = [
    "policy_id", "mode_contract_version", "max_query_member_fanout",
    "member_order_policy", "redundancy_rule_ref", "allowed_action_kinds",
    "pd_wording_rule_ref", "content_hash", "effective_interval",
]
QUERY_REDUNDANCY_KEYS = [
    "decision", "max_query_member_fanout", "unit_member_set_hash",
    "covered_member_refs", "uncovered_member_refs", "member_query_refs",
    "coverage_proof_hash",
]
SOURCE_VERIFICATION_RECORD_KEYS = [
    "revision", "declared_content_hash", "verified_content_hash",
    "verification_state",
]
AUTHORITY_VALIDITY_STATES = ("valid", "invalid")
METHOD_VALIDITY_STATES = ("valid", "insufficient")
STATISTICAL_SIGNAL_ROLES = ("none", "supporting", "sole_evidence")
MEMBER_EXPANSION_STATES = ("expanded", "unexpandable", "not_applicable")
CARRY_FORWARD_STATES = ("none", "active")
LINEAGE_RELATIONS = (
    "none", "first_seen", "continued_from_data_revision",
    "continued_from_cutoff_advance", "superseded_by_rule_or_method_change",
)
SITE_IDENTITY_STATES = ("stable", "merged", "split")
QUERY_REDUNDANCY_DECISIONS = (
    "site_process_delta_present", "fully_covered_by_member_queries",
    "members_unlistable", "not_applicable",
)
SOURCE_VERIFICATION_STATES = ("verified", "mismatch", "unverifiable")
LOCATOR_RESOLUTION_STATES = ("locatable", "missing", "unresolvable")
ANCHOR_RESOLUTION_STATES = ("resolved", "unresolved")
SCOPE_BINDING_KEYS = ["scope_binding_id", "scope_type", "scope_equality_decision"]
PATTERN_DEFINITION_KEYS = [
    "pattern_definition_id", "pattern_kind", "clinical_label_zh", "risk_domain",
    "clinical_claim_token", "d09_action", "required_producer_domains",
    "accepted_member_risk_kinds", "numerator_contract_id",
    "allowed_denominator_kinds", "window_contract_id", "stratum_contract_id",
    "comparability_contract_id", "positive_rule_ref", "counterevidence_rule_refs",
    "monitoring_priority_rule_ref", "center_query_policy_id",
    "minimum_member_subject_count_ref", "required_window_count_ref",
    "opportunity_contract_id", "authority_version",
    "pattern_definition_content_hash", "legal_definition_matrix_content_hash",
    "numeric_execution_policy_content_hash",
]
WINDOW_KEYS = [
    "window_instance_id", "analysis_window_stable_id", "window_kind",
    "window_definition_id", "inclusivity", "anchor_kind", "computed_window_start",
    "computed_window_end", "cutoff_id", "scope_binding_stable_id",
    "window_state", "window_contract_content_hash",
]
STRATUM_KEYS = [
    "stratum_contract_id", "stratum_contract_content_hash", "stratum_key",
    "stratum_state", "stratum_admission",
]
COVERAGE_KEYS = [
    "producer_domain", "l0_status", "l1_medical_completeness_state",
    "accepted_current", "coverage_locator_ids",
]
RISK_MEMBER_KEYS = [
    "member_id", "member_kind", "subject_stable_id", "site_stable_id",
    "producer_domain", "risk_kind", "monitoring_priority",
    "public_r4_risk_identity", "source_event_identity", "event_time_ref",
    "cutoff_relation", "origin_decision", "source_locator_refs",
    "query_draft_refs", "source_locator_resolution_state",
]
GAP_MEMBER_KEYS = [
    "member_id", "member_kind", "subject_stable_id", "site_stable_id",
    "producer_domain", "gap_kind", "gap_opportunity_id", "gap_definition_id",
    "normalized_field_or_process_identity", "obligation_or_opportunity_ref",
    "visit_or_time_anchor_refs", "cutoff_relation", "source_locator_refs",
    "query_draft_refs", "source_locator_resolution_state",
    "anchor_resolution_state",
]
CHANGE_MEMBER_KEYS = [
    "member_id", "member_kind", "subject_stable_id", "site_stable_id",
    "producer_domain", "change_ledger_member_id", "current_window_instance_ref",
    "prior_window_instance_ref", "comparable_state", "change_kind",
    "absolute_delta", "rate_delta", "unit", "change_cause",
    "supporting_member_refs", "source_locator_refs",
]
DENOMINATOR_KEYS = [
    "denominator_kind", "denominator_member_refs", "denominator_eligibility_rule_ref",
    "denominator_excluded_member_refs", "exclusion_reason_codes",
    "denominator_value", "denominator_unit", "denominator_state",
]
OPPORTUNITY_KEYS = [
    "opportunity_definition_ref", "expected_opportunity_refs",
    "expected_opportunity_count", "observed_opportunity_refs",
    "observed_opportunity_count", "missing_opportunity_refs",
    "opportunity_value", "opportunity_unit", "opportunity_state",
    "opportunity_provenance",
]
CUTOFF_KEYS = [
    "cutoff_id", "cutoff_contract_id", "snapshot_as_of", "clinical_event_cutoff",
    "cutoff_identity_state", "cutoff_policy_ref",
]
NUMERIC_POLICY_KEYS = [
    "rate_numerator_kind", "rate_denominator_kind", "scale", "rounding_mode",
    "missing_zero_policy", "display_precision", "time_unit", "exposure_unit",
]
VISIBILITY_KEYS = [
    "audience_scope_id", "blind_status", "evaluation_member_refs",
    "projectable_member_refs", "hidden_member_refs", "hidden_reason_codes",
    "visible_n", "eligible_n", "rate_projection_state",
]
EXPECTED_SET_KEYS = ["expected_set_state", "admission_gate"]
ADMISSION_GATE_KEYS = ["gate_kind", "reason_codes"]
MUTATION_CONTEXT_KEYS = ["mutation_class", "desc", "variant_id", "base_fixture_id"]
ANTI_OVERFIT_KEYS = ["base_fixture_id", "semantic_equivalence_ref", "surface_changes", "variant_id"]
SURFACE_CHANGE_KEYS = ["changed_token", "from_value", "to_value"]
EVIDENCE_REF_KEYS = ["locator_id", "locator_kind", "source_file", "row_or_cell_ref", "lineage_ref"]
AUDIENCE_LEXICON_KEYS = [
    "pattern_label_zh", "disposition_zh", "lifecycle_zh",
    "individual_risk_count_zh", "affected_subjects_zh", "event_count_zh",
    "center_pattern_count_zh", "coverage_zh", "forbidden_internal_terms",
]

# ---------------------------------------------------------------------------
# Partition plan (contract §15 frozen floors; disjoint primary partitions)
# ---------------------------------------------------------------------------
PARTITIONS = [
    # (partition_id, label_zh, required_minimum)
    ("p01_covered_uncovered_zero", "covered zero / uncovered zero", 6),
    ("p02_small_sample_n1", "小样本与 n=1", 8),
    ("p03_short_exposure_late_start", "短暴露/随访与晚启动", 8),
    ("p04_case_mix_counterevidence", "病例组合/项目收集变更反证", 6),
    ("p05_numerator_denominator_opportunity", "分子/分母/机会量", 10),
    ("p06_revision_export_order", "重复 revision/导出/排序", 8),
    ("p07_same_origin_dedup", "同源与跨域去重", 8),
    ("p08_coverage_integrity", "coverage 与完整性优先", 10),
    ("p09_cutoff_window", "cutoff/窗口", 8),
    ("p10_method_statistical_preconditions", "方法与统计前提", 8),
    ("p11_center_query", "center Query", 10),
    ("p12_owner_lifecycle_counting", "owner/lifecycle/计数隔离", 8),
    ("p13_deeplink_chinese_projection", "深链与中文投影", 8),
    ("p14_hidden_anti_overfit", "hidden / anti-overfit", 16),
    ("p15_d06_d10_consume_only", "D06/D10 consume-only", 8),
    ("p16_l1_hole_zero_risk", "L1 hole as zero risk", 6),
    ("p17_gap_without_member_risk", "gap kind without member risk", 4),
    ("p18_first_window_trend", "first-window trend", 2),
    ("p19_cartesian_stratum_fanout", "Cartesian/stratum fanout", 4),
    ("p20_visibility_blinded_stratum", "visibility/blinded stratum", 6),
    ("p21_carry_forward_broken_coverage", "carry-forward on broken coverage", 4),
    ("p22_window_id_vs_computed_dates", "window id vs computed dates", 4),
    ("p23_evidence_ref_display_not_merge", "evidence_ref display not merge", 4),
    ("p24_query_fanout_redundancy", "Query fanout/redundancy", 4),
    ("p25_minimum_member_authority", "minimum member/authority", 2),
    ("p26_opportunity_provenance", "opportunity provenance", 2),
    ("p27_lifecycle_close", "lifecycle close", 3),
    ("p28_cross_window_site_identity", "cross-window/site identity", 3),
    ("p29_r5_no_cross_site_inference", "R5 no cross-site inference", 1),
]
MIN_CASE_COUNT = sum(entry[2] for entry in PARTITIONS)  # 179
PARTITION_MINIMUMS = {entry[0]: entry[2] for entry in PARTITIONS}
PARTITION_LABELS = {entry[0]: entry[1] for entry in PARTITIONS}

# ---------------------------------------------------------------------------
# Canonical JSON and hashing (proven D06/D07/D08 infrastructure conventions)
# ---------------------------------------------------------------------------
def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): normalize_value(item)
            for key, item in value.items()
        }
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        normalize_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


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
    """Verify the frozen contract file bytes and NFC/LF semantic hash."""
    raw = CONTRACT.read_bytes()
    digest = sha256_bytes(raw)
    if digest != CONTRACT_FILE_SHA256:
        raise D09ArtifactError("contract", "stale_hash",
                               f"contract file hash {digest} != pinned {CONTRACT_FILE_SHA256}")
    semantic = sha256_text(normalize_contract(raw.decode("utf-8")))
    if semantic != CONTRACT_SEMANTIC_HASH:
        raise D09ArtifactError("contract", "stale_hash",
                               f"contract semantic hash {semantic} != pinned {CONTRACT_SEMANTIC_HASH}")
    return semantic


# ---------------------------------------------------------------------------
# Validation primitives
# ---------------------------------------------------------------------------
class D09ArtifactError(Exception):
    def __init__(self, stage: str, error_class: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.error_class = error_class


def expect_exact_keys(obj: Any, keys: list[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise D09ArtifactError("schema_parse", "schema_error", f"{label} must be an object")
    actual = sorted(obj.keys())
    if actual != sorted(keys):
        raise D09ArtifactError(
            "schema_parse", "schema_error",
            f"{label} key mismatch: expected {sorted(keys)} got {actual}")
    for key in keys:
        if key not in obj:
            raise D09ArtifactError("schema_parse", "schema_error", f"{label} missing key {key}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise D09ArtifactError("schema_parse", "schema_error", f"{label} must be a non-empty string")
    return value


def require_enum(value: Any, closed: tuple[str, ...], label: str) -> str:
    if value not in closed:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{label} must be one of {closed}, got {value!r}")
    return value


def require_nonneg_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise D09ArtifactError("schema_parse", "schema_error", f"{label} must be a non-negative int")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{label} must be a list of non-empty strings")
    return value


def sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _sorted_unique(values: list[str], label: str) -> list[str]:
    if len(set(values)) != len(values):
        raise D09ArtifactError("schema_parse", "schema_error", f"{label} contains duplicates")
    return sorted(values)


# ---------------------------------------------------------------------------
# Object builders (every emitted object uses its EXACT frozen key set)
# ---------------------------------------------------------------------------
def _content_sha(label: str) -> str:
    """Deterministic synthetic authority/content hash derived from a stable label."""
    return sha256_text(f"d09-content-v1:{label}")


def _scope(idx: int) -> dict[str, Any]:
    return {
        "scope_binding_id": f"SYN-D09-SCOPE-{idx:03d}",
        "scope_type": "site",
        "scope_equality_decision": "exact_match",
    }


def _lexicon_label(kind: str | None) -> str:
    return {
        "repeated_subject_risk": "中心重复风险模式",
        "systematic_data_or_process_gap": "系统性数据或流程缺口",
        "within_site_time_trend": "同中心历时趋势",
    }.get(kind, "中心模式")


def _lexicon(kind: str | None) -> dict[str, Any]:
    return {
        "pattern_label_zh": _lexicon_label(kind),
        "disposition_zh": {
            "positive": "发现该类中心模式",
            "negative": "在本次可评价范围内未发现该类中心模式（不代表无个体风险）",
            "boundary": "边界情况",
            "not_applicable": "不适用",
            "not_evaluable": "暂无法评价（附原因）",
        },
        "lifecycle_zh": {
            "open": "进行中",
            "closed_verified": "已核实关闭",
            "superseded": "已由规则变更取代",
        },
        "individual_risk_count_zh": "相关个体风险 {n} 条",
        "affected_subjects_zh": "受影响受试者 {n} 名",
        "event_count_zh": "事件 {n} 起",
        "center_pattern_count_zh": "中心模式 {n} 项",
        "coverage_zh": "本次可评价范围/数据完整性",
        "forbidden_internal_terms": ["正式事实", "候选信号", "已记录事项", "只读", "通用风险点"],
    }


def _pattern_definition(spec: dict[str, Any], idx: int) -> dict[str, Any]:
    kind = spec.get("pattern_kind")
    token = spec["token"]
    definition_id = f"SYN-D09-DEF-{idx:03d}"
    return {
        "pattern_definition_id": definition_id,
        "pattern_kind": kind,
        "clinical_label_zh": spec.get("clinical_label_zh") or _lexicon_label(kind),
        "risk_domain": spec.get("risk_domain", "safety_quality"),
        "clinical_claim_token": token,
        "d09_action": spec["action"],
        "required_producer_domains": _sorted_unique(list(spec.get("domains", ["D01"])),
                                                    f"{definition_id} required_producer_domains"),
        "accepted_member_risk_kinds": _sorted_unique(
            list(spec.get("member_kinds", ["d01_seriousness_hospital_death"])),
            f"{definition_id} accepted_member_risk_kinds"),
        "numerator_contract_id": f"SYN-D09-NUM-{idx:03d}",
        "allowed_denominator_kinds": _sorted_unique(
            list(spec.get("denominator_kinds", ["evaluable_subjects"])),
            f"{definition_id} allowed_denominator_kinds"),
        "window_contract_id": spec.get("window_contract_id", f"SYN-D09-WC-{idx:03d}"),
        "stratum_contract_id": spec.get("stratum_contract_id", f"SYN-D09-SC-{idx:03d}"),
        "comparability_contract_id": spec.get("comparability_contract_id", f"SYN-D09-CC-{idx:03d}"),
        "positive_rule_ref": spec.get("positive_rule_ref", f"SYN-D09-RULE-POS-{idx:03d}"),
        "counterevidence_rule_refs": _sorted_unique(
            list(spec.get("counterevidence_refs", [])), f"{definition_id} counterevidence_rule_refs"),
        "monitoring_priority_rule_ref": f"SYN-D09-RULE-PRIO-{idx:03d}",
        "center_query_policy_id": spec.get("query_policy_id", f"SYN-D09-QP-{idx:03d}"),
        "minimum_member_subject_count_ref": spec.get("min_member_ref"),
        "required_window_count_ref": spec.get("required_window_count_ref"),
        "opportunity_contract_id": spec.get("opportunity_contract_id"),
        "authority_version": spec.get("authority_version", "SYN-D09-AUTH-001"),
        "pattern_definition_content_hash": _content_sha(f"def:{definition_id}"),
        "legal_definition_matrix_content_hash": _content_sha("legal-definition-matrix-d09-v1"),
        "numeric_execution_policy_content_hash": _content_sha("numeric-execution-policy-d09-v1"),
    }


def _window(idx: int, *, widx: int = 1, wstart: str = "2026-01-01", wend: str = "2026-03-31",
            wkind: str = "calendar_interval", anchor: str = "calendar_date",
            state: str = "closed", window_def_id: str | None = None,
            inclusivity: str = "both_inclusive", cutoff_id: str | None = None,
            window_contract_id: str | None = None) -> dict[str, Any]:
    stable_id = f"SYN-D09-WIN-{idx:03d}-{widx}"
    return {
        "window_instance_id": f"{stable_id}-INST",
        "analysis_window_stable_id": stable_id,
        "window_kind": wkind,
        "window_definition_id": window_def_id or f"SYN-D09-WD-{idx:03d}-{widx}",
        "inclusivity": inclusivity,
        "anchor_kind": anchor,
        "computed_window_start": wstart,
        "computed_window_end": wend,
        "cutoff_id": cutoff_id or f"SYN-D09-CUT-{idx:03d}",
        "scope_binding_stable_id": f"SYN-D09-SCOPE-{idx:03d}",
        "window_state": state,
        "window_contract_content_hash": _content_sha(
            f"window-contract:{window_contract_id or f'SYN-D09-WC-{idx:03d}'}"),
    }


def _stratum(idx: int, *, key: str = "overall", state: str = "closed",
             admission: str = "admitted", contract_id: str | None = None) -> dict[str, Any]:
    return {
        "stratum_contract_id": contract_id or f"SYN-D09-SC-{idx:03d}",
        "stratum_contract_content_hash": _content_sha(
            f"stratum-contract:{contract_id or f'SYN-D09-SC-{idx:03d}'}"),
        "stratum_key": key,
        "stratum_state": state,
        "stratum_admission": admission,
    }


def _coverage(domain: str, *, l0: str = "covered", l1: str = "complete",
              accepted: bool = True, loc: str | None = None) -> dict[str, Any]:
    return {
        "producer_domain": domain,
        "l0_status": l0,
        "l1_medical_completeness_state": l1,
        "accepted_current": accepted,
        "coverage_locator_ids": [loc or "SYN-D09-LOC-CV-001"],
    }


def _risk_member(idx: int, m: int, *, subject: str | None = None, domain: str = "D01",
                 risk_kind: str = "d01_seriousness_hospital_death",
                 priority: str = "medium", event_time: str = "2026-02-01",
                 cutoff: str = "in_cutoff", origin: str = "distinct",
                 risk_identity: str | None = None, event_identity: str | None = None,
                 loc: str | None = None, query_refs: list[str] | None = None,
                 loc_state: str = "locatable") -> dict[str, Any]:
    subj = subject or f"SYN-D09-SUBJ-{idx:03d}-{m:02d}"
    return {
        "member_id": f"SYN-D09-RISK-{idx:03d}-{m:02d}",
        "member_kind": "subject_risk",
        "subject_stable_id": subj,
        "site_stable_id": SITE_REF,
        "producer_domain": domain,
        "risk_kind": risk_kind,
        "monitoring_priority": priority,
        "public_r4_risk_identity": risk_identity or f"SYN-D09-RISKID-{idx:03d}-{m:02d}",
        "source_event_identity": event_identity or f"SYN-D09-EVT-{idx:03d}-{m:02d}",
        "event_time_ref": event_time,
        "cutoff_relation": cutoff,
        "origin_decision": origin,
        "source_locator_refs": [loc or f"SYN-D09-LOC-{idx:03d}-{m:02d}"],
        "query_draft_refs": _sorted_unique(list(query_refs or []), f"risk {idx}-{m} query_draft_refs"),
        "source_locator_resolution_state": loc_state,
    }


def _gap_member(idx: int, m: int, *, subject: str | None = None, domain: str = "D05",
                gap_kind: str = "missing_required_field",
                field: str = "lab_clinical_significance", anchor: str = "2026-02-01",
                cutoff: str = "in_cutoff", loc: str | None = None,
                loc_state: str = "locatable",
                anchor_state: str = "resolved") -> dict[str, Any]:
    subj = subject or f"SYN-D09-SUBJ-{idx:03d}-{m:02d}"
    return {
        "member_id": f"SYN-D09-GAP-{idx:03d}-{m:02d}",
        "member_kind": "gap_opportunity",
        "subject_stable_id": subj,
        "site_stable_id": SITE_REF,
        "producer_domain": domain,
        "gap_kind": gap_kind,
        "gap_opportunity_id": f"SYN-D09-GAPOPP-{idx:03d}-{m:02d}",
        "gap_definition_id": f"SYN-D09-GAPDEF-{idx:03d}",
        "normalized_field_or_process_identity": f"SYN-D09-FIELD-{idx:03d}:{field}",
        "obligation_or_opportunity_ref": f"SYN-D09-OBL-{idx:03d}-{m:02d}",
        "visit_or_time_anchor_refs": [anchor],
        "cutoff_relation": cutoff,
        "source_locator_refs": [loc or f"SYN-D09-LOC-{idx:03d}-{m:02d}"],
        "query_draft_refs": [],
        "source_locator_resolution_state": loc_state,
        "anchor_resolution_state": anchor_state,
    }


def _change_member(idx: int, m: int, *, subject: str | None = None,
                   current: str | None = None, prior: str | None = None,
                   comparable: str = "comparable", change_kind: str = "increased",
                   abs_delta: int | None = None, rate_delta: float | None = None,
                   unit: str = "rate_per_subject", cause: str = "data") -> dict[str, Any]:
    subj = subject or f"SYN-D09-SUBJ-{idx:03d}-{m:02d}"
    return {
        "member_id": f"SYN-D09-CHG-{idx:03d}-{m:02d}",
        "member_kind": "change_ledger",
        "subject_stable_id": subj,
        "site_stable_id": SITE_REF,
        "producer_domain": "D09",
        "change_ledger_member_id": f"SYN-D09-CHGID-{idx:03d}-{m:02d}",
        "current_window_instance_ref": current or f"SYN-D09-WIN-{idx:03d}-2-INST",
        "prior_window_instance_ref": prior or f"SYN-D09-WIN-{idx:03d}-1-INST",
        "comparable_state": comparable,
        "change_kind": change_kind,
        "absolute_delta": abs_delta,
        "rate_delta": rate_delta,
        "unit": unit,
        "change_cause": cause,
        "supporting_member_refs": _sorted_unique([f"SYN-D09-RISK-{idx:03d}-{m:02d}"],
                                                 f"change {idx}-{m} supporting_member_refs"),
        "source_locator_refs": [f"SYN-D09-LOC-{idx:03d}-{m:02d}"],
    }


def _denominator(idx: int, *, kind: str = "evaluable_subjects", members: list[str] | None = None,
                 value: int = 42, state: str = "closed_positive",
                 excluded: list[str] | None = None, reasons: list[str] | None = None,
                 eligibility_ref: str | None = None) -> dict[str, Any]:
    return {
        "denominator_kind": kind,
        "denominator_member_refs": _sorted_unique(
            members or [f"SYN-D09-SUBJ-{idx:03d}-{m:02d}" for m in range(1, value + 1)],
            f"denominator {idx} members"),
        "denominator_eligibility_rule_ref": eligibility_ref or f"SYN-D09-RULE-DEN-{idx:03d}",
        "denominator_excluded_member_refs": _sorted_unique(list(excluded or []),
                                                           f"denominator {idx} excluded"),
        "exclusion_reason_codes": _sorted_unique(list(reasons or []), f"denominator {idx} reasons"),
        "denominator_value": value,
        "denominator_unit": {"evaluable_subjects": "subject", "subject_time": "subject_day",
                             "exposure_time": "subject_day",
                             "expected_assessment_opportunities": "opportunity",
                             "enrolled_subjects": "subject", "treated_subjects": "subject"}[kind],
        "denominator_state": state,
    }


def _opportunity(idx: int, *, definition_ref: str | None = None,
                 expected: int = 42, observed: int = 0, missing: int = 42,
                 state: str = "sufficient", provenance: str = "accepted_d05_plan") -> dict[str, Any]:
    expected_refs = [f"SYN-D09-OPP-{idx:03d}-{i:02d}" for i in range(1, expected + 1)]
    observed_refs = [f"SYN-D09-OPP-{idx:03d}-{i:02d}" for i in range(1, observed + 1)]
    return {
        "opportunity_definition_ref": definition_ref or f"SYN-D09-OPPDEF-{idx:03d}",
        "expected_opportunity_refs": _sorted_unique(expected_refs, f"opportunity {idx} expected refs"),
        "expected_opportunity_count": expected,
        "observed_opportunity_refs": _sorted_unique(observed_refs, f"opportunity {idx} observed refs"),
        "observed_opportunity_count": observed,
        "missing_opportunity_refs": _sorted_unique(
            [f"SYN-D09-OPP-{idx:03d}-{i:02d}" for i in range(observed + 1, missing + 1)],
            f"opportunity {idx} missing refs"),
        "opportunity_value": f"{observed}/{expected}",
        "opportunity_unit": "opportunity",
        "opportunity_state": state,
        "opportunity_provenance": provenance,
    }


def _cutoff(idx: int, *, identity_state: str = "consistent",
            snapshot: str = "2026-07-01T00:00:00+00:00", event_cutoff: str = "2026-06-30",
            contract_id: str | None = None) -> dict[str, Any]:
    return {
        "cutoff_id": f"SYN-D09-CUT-{idx:03d}",
        "cutoff_contract_id": contract_id or f"SYN-D09-CUTC-{idx:03d}",
        "snapshot_as_of": snapshot,
        "clinical_event_cutoff": event_cutoff,
        "cutoff_identity_state": identity_state,
        "cutoff_policy_ref": f"SYN-D09-RULE-CUT-{idx:03d}",
    }


def _numeric_policy(idx: int) -> dict[str, Any]:
    return {
        "rate_numerator_kind": "unique_subject_count",
        "rate_denominator_kind": "evaluable_subjects",
        "scale": 3,
        "rounding_mode": "half_up",
        "missing_zero_policy": "zero_is_observation",
        "display_precision": 1,
        "time_unit": "day",
        "exposure_unit": "subject_day",
    }


def _visibility(idx: int, *, blind: str = "blinded", eval_refs: list[str] | None = None,
                projectable: list[str] | None = None, hidden: list[str] | None = None,
                hidden_reasons: list[str] | None = None, visible_n: int | None = None,
                eligible_n: int | None = None, rate_state: str = "permitted",
                scope_id: str | None = None) -> dict[str, Any]:
    return {
        "audience_scope_id": scope_id or f"SYN-D09-AUD-{idx:03d}",
        "blind_status": blind,
        "evaluation_member_refs": _sorted_unique(list(eval_refs or []), f"visibility {idx} eval refs"),
        "projectable_member_refs": _sorted_unique(list(projectable or []), f"visibility {idx} proj refs"),
        "hidden_member_refs": _sorted_unique(list(hidden or []), f"visibility {idx} hidden refs"),
        "hidden_reason_codes": _sorted_unique(list(hidden_reasons or []), f"visibility {idx} hidden reasons"),
        "visible_n": visible_n,
        "eligible_n": eligible_n,
        "rate_projection_state": rate_state,
    }


def _expected_set(state: str, gate_kind: str | None = None,
                  reason_codes: list[str] | None = None) -> dict[str, Any]:
    gate = None
    if gate_kind is not None:
        gate = {"gate_kind": gate_kind, "reason_codes": _sorted_unique(
            list(reason_codes or []), "admission gate reasons")}
    return {"expected_set_state": state, "admission_gate": gate}


def _mutation_context(spec: dict[str, Any], variant_id: str | None = None,
                      base_fixture_id: str | None = None) -> dict[str, Any]:
    return {
        "mutation_class": spec.get("mc", "none"),
        "desc": spec.get("desc", ""),
        "variant_id": variant_id,
        "base_fixture_id": base_fixture_id,
    }


def _evidence_ref(idx: int, n: int, *, file: str = "synthetic_source/dataset_a.json",
                  kind: str = "synthetic_file", row: str = "sheet:1;row:1") -> dict[str, Any]:
    return {
        "locator_id": f"SYN-D09-LOC-{idx:03d}-{n:02d}",
        "locator_kind": kind,
        "source_file": file,
        "row_or_cell_ref": row,
        "lineage_ref": f"SYN-D09-LIN-{idx:03d}-{n:02d}",
    }


def _audience_contract(idx: int, *, blind: str = "blinded",
                       unblinded_ref: str | None = None) -> dict[str, Any]:
    return {
        "audience_contract_id": f"SYN-D09-AC-{idx:03d}",
        "audience_scope_id": f"SYN-D09-AUD-{idx:03d}",
        "blind_status": blind,
        "authorized_unblinded_contract_ref": unblinded_ref,
        "display_language": "zh-CN",
        "projection_contract_ref": f"SYN-D09-PROJ-{idx:03d}",
    }


def _evidence_for_members(idx: int, member_loc_refs: list[str]) -> list[dict[str, Any]]:
    """Materialize evidence objects for the referenced member locators."""
    locs = sorted(set(member_loc_refs))
    out: list[dict[str, Any]] = []
    for n, loc in enumerate(locs, start=1):
        suffix = loc.rsplit("-", 1)[-1]
        out.append({
            "locator_id": loc,
            "locator_kind": "synthetic_file",
            "source_file": f"synthetic_source/dataset_{idx:03d}.json",
            "row_or_cell_ref": f"sheet:1;row:{n}",
            "lineage_ref": f"SYN-D09-LIN-{idx:03d}-{suffix}",
        })
    return out


# ---------------------------------------------------------------------------
# Case assembler: spec -> full case row (typed_input with EXACT keys)
# ---------------------------------------------------------------------------
def _subject_ids(idx: int, count: int, offset: int = 0) -> list[str]:
    return [f"SYN-D09-SUBJ-{idx:03d}-{offset + m:02d}" for m in range(1, count + 1)]


def _risk_ids(idx: int, count: int, offset: int = 0) -> list[str]:
    return [f"SYN-D09-RISK-{idx:03d}-{offset + m:02d}" for m in range(1, count + 1)]


def _gap_ids(idx: int, count: int, offset: int = 0) -> list[str]:
    return [f"SYN-D09-GAP-{idx:03d}-{offset + m:02d}" for m in range(1, count + 1)]


def _default_risk_members(idx: int, count: int, **kw: Any) -> list[dict[str, Any]]:
    """Build risk member rows.

    Supports two declarative shapes beyond the uniform default:
      * `cutoffs=[...]` (length == count): per-member cutoff_relation, used by
        the cutoff_mixed fixture (contract §7.1 mixed in/out membership).
      * `pair_domains=[...]`: verified same-origin pairs. count must be
        pairs * len(pair_domains); each pair shares subject_stable_id,
        source_event_identity and public_r4_risk_identity across the declared
        producer domains (contract §5.2 dedup groups).
    """
    cutoffs = kw.pop("cutoffs", None)
    pair_domains = kw.pop("pair_domains", None)
    if cutoffs is not None:
        if len(cutoffs) != count:
            raise D09ArtifactError("assembly", "schema_error",
                                   f"risk cutoffs length {len(cutoffs)} != count {count}")
        return [_risk_member(idx, m, cutoff=cutoffs[m - 1], **kw)
                for m in range(1, count + 1)]
    if pair_domains is not None:
        if count % len(pair_domains) != 0:
            raise D09ArtifactError("assembly", "schema_error",
                                   f"risk count {count} not a multiple of pair domains")
        pairs = count // len(pair_domains)
        rows: list[dict[str, Any]] = []
        for p in range(1, pairs + 1):
            for di, domain in enumerate(pair_domains):
                m = (p - 1) * len(pair_domains) + di + 1
                rows.append(_risk_member(
                    idx, m,
                    subject=f"SYN-D09-SUBJ-{idx:03d}-{p:02d}",
                    event_identity=f"SYN-D09-EVT-{idx:03d}-{p:02d}",
                    domain=domain,
                    risk_kind=("d08_cross_domain_relation" if domain == "D08"
                               else kw.get("risk_kind", "d01_seriousness_hospital_death")),
                    **kw))
        return rows
    return [_risk_member(idx, m, **kw) for m in range(1, count + 1)]


def _default_gap_members(idx: int, count: int, **kw: Any) -> list[dict[str, Any]]:
    return [_gap_member(idx, m, **kw) for m in range(1, count + 1)]


def _default_change_members(idx: int, count: int, **kw: Any) -> list[dict[str, Any]]:
    return [_change_member(idx, m, **kw) for m in range(1, count + 1)]


# ---------------------------------------------------------------------------
# Resolved domain facts (worker_01 corrective pass 2026-08-15).
# The typed envelope carries explicit resolved decisions (contract sections
# 6/7/9/10/12) instead of mutation-class metadata: resolved authority
# threshold and validity, method/comparability and statistical-signal facts,
# lineage context, Query redundancy decision and producer source-verification
# records.  Neutral defaults apply to all 179 cases; only the affected
# fixtures receive non-default facts.  The oracle generator and the runtime
# consume only these explicit facts.
# ---------------------------------------------------------------------------


def _resolved_authority_decision(spec: dict[str, Any], idx: int,
                                 kind: str | None) -> dict[str, Any]:
    invalid = spec.get("mc") == "authority_fail"
    min_count = (None if invalid or kind != "repeated_subject_risk"
                 else int(spec.get("minimum_member_subject_count", 2)))
    gap_minimum = (None if invalid or kind != "systematic_data_or_process_gap"
                   else int(spec.get("gap_positive_minimum_opportunity_count", 5)))
    trend_minimum = (None if invalid or kind != "within_site_time_trend"
                     else int(spec.get("trend_positive_minimum_subject_count", 3)))
    payload = {
        "authority_ref": f"SYN-D09-AUTH-{idx:03d}",
        "mode_contract_version": "SYN-D09-MODE-001",
        "minimum_member_subject_count": min_count,
        "gap_positive_minimum_opportunity_count": gap_minimum,
        "trend_positive_minimum_subject_count": trend_minimum,
    }
    return {
        **payload,
        "authority_validity_state": "invalid" if invalid else "valid",
        "authority_locator_ref": f"SYN-D09-AUTH-LOC-{idx:03d}",
        "authority_content_hash": sha256_text(canonical_json(payload)),
    }


def _method_comparability_decision(spec: dict[str, Any], idx: int,
                                   n_windows: int) -> dict[str, Any]:
    mc = spec.get("mc")
    rule_ref = f"SYN-D09-WRULE-{idx:03d}"
    method_ref = f"SYN-D09-SMVER-{idx:03d}"
    window_rule_version_refs = [rule_ref] * n_windows
    stratum_method_version_refs = [method_ref] * n_windows
    if mc == "window_definition_change":
        window_rule_version_refs = [f"{rule_ref}-{w}" for w in range(1, n_windows + 1)]
    if mc == "stratum_change":
        stratum_method_version_refs = [f"{method_ref}-{w}" for w in range(1, n_windows + 1)]
    return {
        "method_validity_state": (
            "insufficient" if mc == "validity_insufficient" else "valid"),
        "statistical_signal_role": (
            "sole_evidence" if mc == "statistics_only"
            else "supporting" if mc == "signal_unexpandable" else "none"),
        "member_expansion_state": (
            "unexpandable" if mc == "signal_unexpandable" else "not_applicable"),
        "window_rule_version_refs": window_rule_version_refs,
        "stratum_method_version_refs": stratum_method_version_refs,
    }


def _lineage_context(spec: dict[str, Any], idx: int) -> dict[str, Any]:
    mc = spec.get("mc")
    carry = mc == "carry_forward"
    if carry:
        lineage = "continued_from_data_revision"
    elif mc == "rule_supersession":
        lineage = "superseded_by_rule_or_method_change"
    else:
        lineage = "none"
    return {
        "prior_risk_instance_ref": f"SYN-D09-RISKINST-{idx:03d}" if carry else None,
        "prior_public_risk_identity_ref": (
            f"SYN-D09-PUBRISKID-{idx:03d}" if carry else None),
        "carry_forward_state": "active" if carry else "none",
        "lineage_relation": lineage,
        "site_identity_state": "split" if mc == "site_merge_split" else "stable",
    }


def _query_redundancy_decision(spec: dict[str, Any], idx: int,
                               members: list[dict[str, Any]]) -> dict[str, Any]:
    mc = spec.get("mc")
    member_ids = [m["member_id"] for m in members]
    member_query_refs: list[str] = []
    for member in members:
        member_query_refs.extend(member.get("query_draft_refs") or [])
    if mc == "query_fully_covered":
        decision = "fully_covered_by_member_queries"
        covered = member_ids
        uncovered: list[str] = []
    elif mc == "query_members_unlistable":
        decision = "members_unlistable"
        covered, uncovered = [], member_ids
    elif mc == "query_no_process_delta":
        decision = "not_applicable"
        covered, uncovered = [], member_ids
    else:
        decision = "site_process_delta_present"
        covered, uncovered = [], member_ids
    fanout = 10 if mc == "query_fanout_exceeded" else 100
    unit_hash = sha256_text(canonical_json(sorted(member_ids)))
    proof_hash = sha256_text(canonical_json({
        "decision": decision,
        "covered": sorted(set(covered)),
        "uncovered": sorted(set(uncovered)),
        "member_queries": sorted(set(member_query_refs)),
        "fanout": fanout,
    }))
    return {
        "decision": decision,
        "max_query_member_fanout": fanout,
        "unit_member_set_hash": unit_hash,
        "covered_member_refs": sorted(set(covered)),
        "uncovered_member_refs": sorted(set(uncovered)),
        "member_query_refs": sorted(set(member_query_refs)),
        "coverage_proof_hash": proof_hash,
    }


def _center_query_policy(spec: dict[str, Any], idx: int) -> dict[str, Any]:
    fanout = 10 if spec.get("mc") == "query_fanout_exceeded" else 100
    payload = {
        "policy_id": f"SYN-D09-QPOL-{idx:03d}",
        "mode_contract_version": "SYN-D09-MODE-001",
        "max_query_member_fanout": fanout,
        "member_order_policy": "stable_member_ref_ascending",
        "redundancy_rule_ref": f"SYN-D09-QRED-RULE-{idx:03d}",
        "allowed_action_kinds": ["request_record_verification", "verify_pd"],
        "pd_wording_rule_ref": f"SYN-D09-PD-WORDING-{idx:03d}",
        "effective_interval": "synthetic-open-interval",
    }
    return {**payload, "content_hash": sha256_text(canonical_json(payload))}


def _source_verification_records(spec: dict[str, Any],
                                 idx: int) -> list[dict[str, Any]]:
    revisions = sorted(set(spec.get("revision_set",
                                    [f"SRC-REV-{idx:03d}-001"])))
    broken = set(spec.get("broken_hash_revisions", []))
    records: list[dict[str, Any]] = []
    for revision in revisions:
        if revision in broken:
            records.append({
                "revision": revision,
                "declared_content_hash": sha256_text(f"d09-rev:{revision}-TAMPERED"),
                "verified_content_hash": sha256_text(f"d09-rev:{revision}"),
                "verification_state": "mismatch",
            })
        else:
            digest = sha256_text(f"d09-rev:{revision}")
            records.append({
                "revision": revision,
                "declared_content_hash": digest,
                "verified_content_hash": digest,
                "verification_state": "verified",
            })
    return records


def build_typed_input(spec: dict[str, Any], idx: int) -> dict[str, Any]:
    """Assemble the full typed_input envelope for a case spec."""
    parts = spec.get("parts") or {}
    site = spec.get("site", SITE_REF)
    risk_members = parts.get("risk_members") or _default_risk_members(
        idx, spec.get("risk_count", 0), **parts.get("risk_kwargs", {}))
    gap_members = parts.get("gap_members") or _default_gap_members(
        idx, spec.get("gap_count", 0), **parts.get("gap_kwargs", {}))
    change_members = parts.get("change_members") or _default_change_members(
        idx, spec.get("change_count", 0), **parts.get("change_kwargs", {}))
    windows = parts.get("windows") or [_window(idx)]
    coverage = parts.get("coverage") or [_coverage(domain) for domain in spec.get("domains", ["D01"])]
    denominator = parts.get("denominator") or _denominator(idx, **parts.get("denominator_kwargs", {}))
    opportunity = parts.get("opportunity") or _opportunity(idx, **parts.get("opportunity_kwargs", {}))
    cutoff = parts.get("cutoff") or _cutoff(idx, **parts.get("cutoff_kwargs", {}))
    visibility = parts.get("visibility") or _visibility(
        idx, blind=spec.get("blind", "blinded"), **parts.get("visibility_kwargs", {}))
    evidence = parts.get("evidence_refs") or _evidence_for_members(
        idx, [loc for member in risk_members + gap_members + change_members
              for loc in member["source_locator_refs"]])

    revision_set = sorted(set(spec.get("revision_set",
                                       [f"SRC-REV-{idx:03d}-001"])))
    source_hashes = [sha256_text(f"d09-rev:{rev}") for rev in revision_set]
    # Encode the source-hash-mismatch integrity fact (contract §4): a declared
    # hash that does not match its revision content. The producer declares the
    # TAMPERED label hash; the verifier recomputes sha256("d09-rev:<rev>") and
    # detects the mismatch.
    for rev in spec.get("broken_hash_revisions", []):
        if rev not in revision_set:
            raise D09ArtifactError("assembly", "schema_error",
                                   f"broken_hash_revision {rev} not in revision_set")
        pos = revision_set.index(rev)
        source_hashes[pos] = sha256_text(f"d09-rev:{rev}-TAMPERED")

    owning_members = risk_members
    if spec.get("pattern_kind") == "systematic_data_or_process_gap":
        owning_members = gap_members
    elif spec.get("pattern_kind") == "within_site_time_trend":
        owning_members = change_members
    if spec.get("mc") == "query_fully_covered":
        for position, member in enumerate(owning_members, start=1):
            if "query_draft_refs" in member and not member["query_draft_refs"]:
                member["query_draft_refs"] = [
                    f"SYN-D09-MEMBER-QUERY-{idx:03d}-{position:02d}"]

    typed: dict[str, Any] = {
        "input_schema": TYPED_INPUT_SCHEMA,
        "envelope_id": f"SYN-D09-ENV-{idx:03d}",
        "project_ref": spec.get("project_ref", PROJECT_REF),
        "run_ref": RUN_REF,
        "snapshot_ref": SNAPSHOT_REF,
        "source_revision_set": revision_set,
        "source_content_hashes": source_hashes,
        "site_stable_id": site,
        "scope_binding": _scope(idx),
        "pattern_definition": _pattern_definition(spec, idx),
        "mode_contract_version": "SYN-D09-MODE-001",
        "matched_counterevidence_rule_refs": _sorted_unique(
            list(spec.get("matched_ce_refs", [])),
            f"SYN-D09-ENV-{idx:03d} matched_counterevidence_rule_refs"),
        "mode_contract_design_clause_ref": spec.get("design_clause_ref"),
        "analysis_windows": windows,
        "stratum": _stratum(idx, **parts.get("stratum_kwargs", {})),
        "coverage": coverage,
        "subject_risk_members": risk_members,
        "gap_members": gap_members,
        "change_ledger_members": change_members,
        "denominator": denominator,
        "opportunity": opportunity,
        "cutoff": cutoff,
        "numeric_policy": _numeric_policy(idx),
        "visibility_decision": visibility,
        "expected_set": parts.get("expected_set") or _expected_set(
            spec.get("expected_set_state", "admitted"),
            gate_kind=spec.get("gate_kind"), reason_codes=spec.get("gate_reasons")),
        "mutation_context": _mutation_context(spec),
        "anti_overfit_variant": spec.get("anti_overfit_variant"),
        "evidence_refs": evidence,
        "audience_lexicon": _lexicon(spec.get("pattern_kind")),
        "resolved_authority_decision": _resolved_authority_decision(
            spec, idx, spec.get("pattern_kind")),
        "method_comparability_decision": _method_comparability_decision(
            spec, idx, len(windows)),
        "lineage_context": _lineage_context(spec, idx),
        "center_query_policy": _center_query_policy(spec, idx),
        "query_redundancy_decision": _query_redundancy_decision(
            spec, idx, owning_members),
        "source_verification_records": _source_verification_records(spec, idx),
    }
    return typed


def build_case_row(typed: dict[str, Any], spec: dict[str, Any], idx: int,
                   partition: str, family: str) -> dict[str, Any]:
    fixture_id = f"D09-FIX-{idx:03d}"
    case_id = f"D09-CASE-{idx:03d}"
    return {
        "case_id": case_id,
        "primary_partition_id": partition,
        "family_id": family,
        "pattern_kind": spec.get("pattern_kind"),
        "owner_route": spec["action"],
        "clinical_claim_token": spec["token"],
        "disposition": spec["disposition"],
        "fixture_id": fixture_id,
        "fixture_hash": sha256_text(canonical_json(typed)),
        "oracle_case_id": f"D09-ORACLE-{idx:03d}",
        "manifest_case_id": f"D09-MANIFEST-{idx:03d}",
        "expected_leaf_set": None,
        "expected_trace_leaf_set": None,
        "expected_source_leaf_set": None,
        "mutation_class": spec.get("mc", "none"),
        "audience_contract": _audience_contract(
            idx, blind=spec.get("blind", "blinded"),
            unblinded_ref=spec.get("unblinded_ref")),
        "typed_input": typed,
    }


# ---------------------------------------------------------------------------
# Partition builders (contract §15 floors). Each spec is deterministic; ids are
# derived from the case index so two fresh generations are byte-identical.
# ---------------------------------------------------------------------------
def _base_spec(partition: str, family: str, kind: str, token: str, action: str,
               disposition: str, mc: str, desc: str, **kw: Any) -> dict[str, Any]:
    spec = {
        "partition": partition,
        "family": family,
        "pattern_kind": kind,
        "token": token,
        "action": action,
        "disposition": disposition,
        "mc": mc,
        "desc": desc,
        "parts": {},
    }
    spec.update(kw)
    return spec


def build_p01_specs() -> list[dict[str, Any]]:
    """covered zero / uncovered zero (6): closed zero may be negative; any
    unclosed coverage/denominator/opportunity forbids negative."""
    return [
        # 001 covered zero -> negative (repeated risk)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "negative", "none",
                   "closed zero: coverage complete, denominator closed 42/42, "
                   "opportunity sufficient, zero members hit -> negative",
                   risk_count=0, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-001",
                   parts={"coverage": [_coverage("D01"), _coverage("D02")],
                          "denominator_kwargs": {"value": 42, "state": "closed_positive"}}),
        # 002 covered zero -> negative (systematic gap)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "negative", "none",
                   "closed zero gap: 42/42 expected opportunities observed, zero missing, "
                   "full coverage -> negative",
                   gap_count=0, domains=["D05", "D04"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 42, "missing": 0,
                                                 "state": "sufficient"},
                          "denominator_kwargs": {"kind": "expected_assessment_opportunities",
                                                 "value": 42}}),
        # 003 covered zero -> negative (within-site trend, two comparable windows)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "negative", "none",
                   "closed zero trend: two closed comparable windows both zero risk, "
                   "same denominator contract -> negative",
                   risk_count=0, domains=["D01"], change_count=0,
                   parts={"windows": [_window(3, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(3, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42}}),
        # 004 uncovered zero -> NOT negative (coverage missing)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "uncovered zero: required D01 L0 coverage missing; zero members must "
                   "NOT be treated as negative",
                   risk_count=0, domains=["D01", "D02"],
                   parts={"coverage": [_coverage("D01", l0="missing", l1="missing"),
                                       _coverage("D02")],
                          "denominator_kwargs": {"value": 42, "state": "unclosed"}}),
        # 005 uncovered zero -> NOT negative (denominator unclosed)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "uncovered zero: denominator unclosed; empty result cannot form a "
                   "negative",
                   risk_count=0, domains=["D01"],
                   parts={"denominator_kwargs": {"value": 0, "state": "unclosed"}}),
        # 006 uncovered zero -> NOT negative (opportunity insufficient)
        _base_spec("p01_covered_uncovered_zero", "d09_zero_closure",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "uncovered zero gap: opportunity_state insufficient; zero observations "
                   "cannot form a negative",
                   gap_count=0, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 0, "missing": 42,
                                                 "state": "insufficient"}}),
    ]


def build_p02_specs() -> list[dict[str, Any]]:
    """small sample / n=1 (8): n=1 forced boundary + hotspot, never positive;
    minimum member subject count for repeated risk is 2."""
    return [
        # 007 repeated n=1 -> boundary + hotspot
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "n=1: single subject hit; minimum_member_subject_count_ref=2 -> forced "
                   "boundary + hotspot, never positive",
                   risk_count=1, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high"},
                          "denominator_kwargs": {"value": 18}}),
        # 008 gap n=1 -> boundary
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "gap kind with single subject/opportunity -> small sample boundary",
                   gap_count=1, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 4, "observed": 1, "missing": 3}}),
        # 009 trend n=1 -> boundary
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "trend with one subject across two windows -> boundary (tiny sample)",
                   risk_count=1, domains=["D01"], change_count=1,
                   parts={"windows": [_window(9, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(9, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 1}}),
        # 010 repeated n=2 -> positive (minimum met)
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "n=2: minimum member subject count satisfied -> positive",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 18}}),
        # 011 repeated n=1 high priority SAE/AESI -> boundary + hotspot preserved
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "n=1 with high-priority member (SAE/AESI): boundary + hotspot retained; "
                   "single high-risk case never escalates to systematic",
                   risk_count=1, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high", "risk_kind": "d01_seriousness_hospital_death"},
                          "denominator_kwargs": {"value": 18}}),
        # 012 repeated n=3 small sample short followup -> boundary
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "n=3 with short follow-up -> small-sample boundary",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"kind": "subject_time", "value": 45}}),
        # 013 gap 2/4 small sample -> boundary
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "boundary", "none",
                   "gap 2/4 opportunities -> small sample boundary",
                   gap_count=2, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 4, "observed": 2, "missing": 2}}),
        # 014 trend two windows two subjects short exposure -> boundary
        _base_spec("p02_small_sample_n1", "d09_small_sample_n1",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "none",
                   "trend over two windows with only 2 subjects / short exposure -> boundary",
                   risk_count=2, domains=["D01"], change_count=2,
                   parts={"windows": [_window(14, widx=1, wstart="2026-01-01", wend="2026-02-28"),
                                      _window(14, widx=2, wstart="2026-03-01", wend="2026-04-30")],
                          "denominator_kwargs": {"kind": "exposure_time", "value": 40},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 1}}),
    ]


def build_p03_specs() -> list[dict[str, Any]]:
    """short exposure / follow-up / late activation (8): subject/exposure time,
    incomparable windows excluded, no false improvement."""
    return [
        # 015 repeated late site activation -> boundary
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "late site activation: window truncated vs protocol -> boundary",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"windows": [_window(15, anchor="site_activation",
                                              wstart="2026-03-01", wend="2026-03-31")],
                          "denominator_kwargs": {"value": 6}}),
        # 016 repeated short follow-up -> boundary
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "short follow-up: exposure too short for full comparability -> boundary",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"kind": "subject_time", "value": 30}}),
        # 017 trend incomparable windows -> window_pair_gate, zero trend units
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_applicable", "none",
                   "trend: window 1 short exposure vs window 2 full -> incomparable "
                   "windows, window_pair_gate, zero trend medical units",
                   risk_count=0, domains=["D01"], change_count=0,
                   required_window_count_ref="SYN-D09-WINREQ-001",
                   parts={"windows": [_window(17, widx=1, wstart="2026-01-01", wend="2026-01-31",
                                              wkind="exposure_time_interval"),
                                      _window(17, widx=2, wstart="2026-02-01", wend="2026-06-30")],
                          "denominator_kwargs": {"kind": "exposure_time", "value": 30}}),
        # 018 trend subject-time rate increase -> positive
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "none",
                   "trend with subject-time denominators (10 vs 12 subject-months): "
                   "rate 2/10 -> 3/12 increased, same method -> positive",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(18, widx=1, wstart="2026-01-01", wend="2026-03-31",
                                              wkind="subject_time_interval"),
                                      _window(18, widx=2, wstart="2026-04-01", wend="2026-06-30",
                                              wkind="subject_time_interval")],
                          "denominator_kwargs": {"kind": "subject_time", "value": 22},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 1,
                                            "rate_delta": 0.05, "unit": "rate_per_subject_month"}}),
        # 019 repeated short exposure -> boundary
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "short exposure: 5 subject-weeks exposure denominator -> boundary",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"kind": "exposure_time", "value": 5}}),
        # 020 gap late activation truncated window -> boundary
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "boundary", "none",
                   "gap with late-activated site: truncated opportunity window -> boundary",
                   gap_count=3, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 6, "observed": 3, "missing": 3,
                                                 "state": "insufficient"}}),
        # 021 trend coverage change explains difference -> no false improvement
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "none",
                   "trend rate 3/9 -> 1/9 but window 2 coverage degraded; change_cause=coverage "
                   "-> no false improvement, boundary",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(21, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(21, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 9},
                          "change_kwargs": {"change_kind": "decreased", "abs_delta": -2,
                                            "cause": "coverage"}}),
        # 022 repeated short exposure n=4 -> boundary
        _base_spec("p03_short_exposure_late_start", "d09_short_exposure_late_start",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "n=4 with short exposure (10 subject-days) -> boundary",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"kind": "exposure_time", "value": 10}}),
    ]


def build_p04_specs() -> list[dict[str, Any]]:
    """case-mix / collection-change counterevidence (6): explainable -> negative
    or boundary; unexplainable -> positive."""
    return [
        # 023 counterevidence explains -> negative
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "negative", "none",
                   "5/42 signal fully explained by case-mix change (L1b counterevidence "
                   "satisfied) -> negative; underlying individual risks retained",
                   risk_count=5, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   counterevidence_refs=["SYN-D09-RULE-CE-024"],
                   matched_ce_refs=["SYN-D09-RULE-CE-024"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 024 counterevidence partial -> boundary
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "case-mix change partially explains 4/42 -> boundary",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   counterevidence_refs=["SYN-D09-RULE-CE-025", "SYN-D09-RULE-CE-025B"],
                   matched_ce_refs=["SYN-D09-RULE-CE-025"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 025 counterevidence insufficient -> positive
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "5/42 with counterevidence preconditions unmet -> positive",
                   risk_count=5, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   counterevidence_refs=["SYN-D09-RULE-CE-025"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 026 collection change explains missing field -> negative (gap)
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "negative", "none",
                   "gap 6/42 explained by documented collection change (field added "
                   "mid-study) -> negative",
                   gap_count=6, domains=["D05"], counterevidence_refs=["SYN-D09-RULE-CE-027"],
                   matched_ce_refs=["SYN-D09-RULE-CE-027"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 42, "missing": 0}}),
        # 027 trend method change between windows -> not comparable -> boundary
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "none",
                   "trend windows use different method versions -> not comparable, "
                   "boundary, no false improvement/decline",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(27, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(27, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable", "cause": "method"}}),
        # 028 counterevidence condition missing -> positive
        _base_spec("p04_case_mix_counterevidence", "d09_case_mix_counterevidence",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "counterevidence rule condition data absent -> counterevidence cannot "
                   "explain -> positive",
                   risk_count=5, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
    ]


def build_p05_specs() -> list[dict[str, Any]]:
    """numerator/denominator/opportunity (10): subject vs event counts separated,
    denominator drift, empty denominator, wrong opportunity definition, explicit
    bucket mapping or fail closed."""
    return [
        # 029 positive: 4 subjects / 6 events separated
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "4 unique subjects, 6 distinct events: numerator subject count and "
                   "event count reported separately -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"event_identity": "SYN-D09-EVT-029-01"},
                          "denominator_kwargs": {"value": 42}}),
        # 030 denominator drift between windows -> not_evaluable
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "none",
                   "denominator 42 vs 37 across identical-content runs (drift) -> "
                   "not_evaluable; identical revision must not drift",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   revision_set=["SRC-REV-030-001", "SRC-REV-030-002"],
                   parts={"denominator_kwargs": {"value": 42, "state": "unclosed"}}),
        # 031 empty denominator closed_zero -> not_evaluable (no design clause)
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "none",
                   "denominator_state=closed_zero with no ModeContract design clause -> "
                   "default not_evaluable",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 0, "state": "closed_zero"}}),
        # 032 wrong opportunity definition -> fail closed not_evaluable
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "none",
                   "opportunity_definition_ref does not match pattern definition's "
                   "opportunity contract -> fail closed, not_evaluable",
                   gap_count=3, domains=["D05"],
                   parts={"opportunity_kwargs": {"definition_ref": "SYN-D09-OPPDEF-OTHER",
                                                 "state": "unknown"}}),
        # 033 subject not in any bucket but explicit mapping present -> positive
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "one member outside declared buckets with explicit mapping to "
                   "evaluable_subjects (exclusion reason documented) -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {
                       "value": 42,
                       "excluded": ["SYN-D09-SUBJ-033-03"],
                       "reasons": ["explicit_mapping_to_evaluable"]}}),
        # 034 subject in no bucket, no mapping -> fail closed
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "authority_fail",
                   "member subject belongs to no declared denominator bucket and no "
                   "explicit mapping -> fail closed, not_evaluable",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42, "state": "unclosed"}}),
        # 035 gap 9/42 -> positive
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "none",
                   "accepted gap 9/42 missing opportunities -> positive",
                   gap_count=9, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 036 opportunity unknown -> not_evaluable
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "none",
                   "opportunity_state=unknown -> not_evaluable",
                   gap_count=2, domains=["D05"],
                   parts={"opportunity_kwargs": {"state": "unknown"}}),
        # 037 positive: 3 subjects / 8 events separated
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "3 subjects with 8 events (multiple events per subject): counts "
                   "separated, no total-risk mixing -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"event_identity": "SYN-D09-EVT-037-01"},
                          "denominator_kwargs": {"value": 42}}),
        # 038 closed_zero with ModeContract design clause -> not_applicable
        _base_spec("p05_numerator_denominator_opportunity", "d09_numerator_denominator",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_applicable", "none",
                   "denominator closed_zero with locatable ModeContract design clause "
                   "proving the pattern is not applicable in this stage -> not_applicable",
                   risk_count=0, domains=["D01"], design_clause_ref="SYN-D09-DC-038",
                   parts={"denominator_kwargs": {"value": 0, "state": "closed_zero"},
                          "expected_set": _expected_set("admitted"),
                          "cutoff_kwargs": {}}),
    ]


def build_p06_specs() -> list[dict[str, Any]]:
    """revision / export / order (8): double-pass determinism; same revision not
    double-counted; canonical hashes stable."""
    return [
        # 039 repeated positive, duplicated revisions counted once
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "revision_repeat",
                   "same revision exported twice in source_revision_set: members counted "
                   "once; affected subjects 2, not 4 -> positive",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   revision_set=["SRC-REV-039-001", "SRC-REV-039-001"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 040 gap duplicated export rows counted once
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "export_repeat",
                   "duplicate export of same revision: 9/42 opportunities, no "
                   "double-counting -> positive",
                   gap_count=9, domains=["D05"], revision_set=["SRC-REV-040-001", "SRC-REV-040-001"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 041 reordered input -> same outcome
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "order_shuffle",
                   "member array order shuffled vs base semantics; outcome must not "
                   "change (stable identity ordering) -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 042 display-name change -> same disposition
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "display_rename",
                   "clinical_label_zh changed; display-only, evaluation unchanged -> "
                   "positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   clinical_label_zh="中心重复风险模式（显示名变体）",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 043 gap re-export same revision -> counts stable
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "export_repeat",
                   "re-export of the same accepted revision adds no new members; "
                   "9/42 stable -> positive",
                   gap_count=9, domains=["D05"], revision_set=["SRC-REV-043-001"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 044 trend double export no double count
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "export_repeat",
                   "same window pair exported twice: change ledger members counted once "
                   "-> positive",
                   risk_count=3, domains=["D01"], change_count=3,
                   revision_set=["SRC-REV-044-001", "SRC-REV-044-001"],
                   parts={"windows": [_window(44, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(44, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 2}}),
        # 045 canonical hash stability (revision repeat)
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "revision_repeat",
                   "identical content replayed under a new opaque run: content identity "
                   "and canonical hashes stable -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 046 same content different snapshot opaque id
        _base_spec("p06_revision_export_order", "d09_revision_export_order",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "revision_repeat",
                   "same immutable content with a different snapshot opaque id: same "
                   "evaluation content identity, R2 idempotent -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
    ]


def build_p07_specs() -> list[dict[str, Any]]:
    """same-origin / cross-domain dedup (8): D08 verified, ambiguous, wrong scope,
    distinct; no string merging."""
    return [
        # 047 verified same-origin pairs -> dedup to one member per subject
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "same_origin_verified",
                   "two D02+D08 pairs with D08-verified same-origin binding: each pair "
                   "counts one member -> positive, affected 2",
                   risk_count=4, domains=["D01", "D08"], min_member_ref="SYN-D09-MIN-002",
                   member_kinds=["d01_seriousness_hospital_death",
                                 "d08_cross_domain_relation"],
                   parts={"risk_kwargs": {"origin": "verified_same_origin",
                                          "risk_identity": "SYN-D09-RISKID-047-PAIR",
                                          "pair_domains": ["D01", "D08"]},
                          "denominator_kwargs": {"value": 42}}),
        # 048 ambiguous origin -> boundary
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "origin_ambiguous",
                   "same-origin claim ambiguous (no D08-verified binding) -> dedup_state "
                   "ambiguous -> boundary",
                   risk_count=2, domains=["D01", "D08"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "ambiguous"},
                          "denominator_kwargs": {"value": 42}}),
        # 049 wrong scope -> not_evaluable
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "origin_wrong_scope",
                   "member resolves to wrong subject/site scope -> wrong_scope -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "wrong_scope"},
                          "denominator_kwargs": {"value": 42}}),
        # 050 distinct cross-domain risks -> two members
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "origin_distinct",
                   "two distinct events (distinct origins) across domains -> two members, "
                   "no merge -> positive",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 051 shared evidence_ref but two identities -> NOT merged
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "evidence_ref_shared",
                   "shared evidence_ref_id with two distinct public risk identities and "
                   "no D08 binding: display cluster only, never merged -> positive, 2",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "distinct",
                                          "loc": "SYN-D09-LOC-SHARED-051"},
                          "denominator_kwargs": {"value": 42}}),
        # 052 gap members same field distinct subjects -> separate opportunities
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "origin_distinct",
                   "two gap members with the same normalized field but distinct subjects: "
                   "two separate opportunities, no string merge -> positive",
                   gap_count=2, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 40, "missing": 2}}),
        # 053 same-origin wrong scope on one member -> not_evaluable
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "origin_wrong_scope",
                   "one member of a claimed same-origin pair resolves to wrong scope -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01", "D08"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "wrong_scope"},
                          "denominator_kwargs": {"value": 42}}),
        # 054 origin not_evaluable -> not_evaluable
        _base_spec("p07_same_origin_dedup", "d09_same_origin_dedup",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "none",
                   "origin_decision=not_evaluable (resolution impossible) -> unit "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "not_evaluable"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p08_specs() -> list[dict[str, Any]]:
    """coverage & integrity priority (10): required partial/truncated/missing/failed;
    unrelated-domain gap does not implicate; medical output blocked."""
    return [
        # 055 required D02 L0 partial -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_partial",
                   "required D02 L0 partial -> not_evaluable (no medical output)",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01"), _coverage("D02", l0="partial",
                                                                   l1="partial")]}),
        # 056 required D03 L0 truncated -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_truncated",
                   "required D03 L0 truncated -> not_evaluable",
                   risk_count=2, domains=["D01", "D03"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01"), _coverage("D03", l0="truncated",
                                                                   l1="partial")]}),
        # 057 required D04 L0 missing -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "required D04 L0 missing -> not_evaluable",
                   gap_count=2, domains=["D05", "D04"],
                   parts={"coverage": [_coverage("D05"), _coverage("D04", l0="missing",
                                                                   l1="missing")]}),
        # 058 required D05 L0 failed -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_failed",
                   "required D05 L0 failed -> not_evaluable",
                   risk_count=2, domains=["D01", "D05"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01"), _coverage("D05", l0="failed",
                                                                   l1="missing")]}),
        # 059 unrelated non-required domain gap -> positive (no joint liability)
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "non-required D07 gap does not implicate the unit: required domains "
                   "complete -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01"), _coverage("D07", l0="missing",
                                                                   l1="missing")],
                          "denominator_kwargs": {"value": 42}}),
        # 060 required L0 complete but L1 not_evaluable -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "required domain L0 complete but L1 medical completeness "
                   "not_evaluable -> unit not_evaluable (L1 hole is not zero risk)",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01", l0="covered", l1="not_evaluable")]}),
        # 061 coverage complete -> positive
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "all required domains covered and L1 complete -> positive",
                   risk_count=4, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 062 producer ref unresolvable -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "producer object ref unresolvable / not accepted-current -> integrity "
                   "block, unit not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01", accepted=False)]}),
        # 063 source content hash mismatch -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "coverage_missing",
                   "declared source content hash does not match revision content -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   revision_set=["SRC-REV-063-001", "SRC-REV-063-BROKEN"],
                   broken_hash_revisions=["SRC-REV-063-BROKEN"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 064 scope binding mismatch -> not_evaluable
        _base_spec("p08_coverage_integrity", "d09_coverage_integrity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "origin_wrong_scope",
                   "member subject scope binding mismatches site scope -> wrong_scope -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "wrong_scope"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p09_specs() -> list[dict[str, Any]]:
    """cutoff / window (8): all-out, mixed, time missing, revision vs event time,
    single-window trend, cutoff identity conflict."""
    return [
        # 065 all members out of cutoff -> not_evaluable (context preserved)
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "cutoff_all_out",
                   "all members out_of_cutoff: no in-window medical numerator; context "
                   "preserved, unit not_evaluable (never negative)",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"cutoff": "out_of_cutoff"},
                          "denominator_kwargs": {"value": 42}}),
        # 066 single candidate spans cutoff -> cutoff boundary gate -> boundary
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "cutoff_spans",
                   "candidate spans cutoff (spans_cutoff): independent cutoff boundary "
                   "gate, no fabricated medical unit -> boundary",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"cutoff": "spans_cutoff"},
                          "denominator_kwargs": {"value": 42}}),
        # 067 mixed in/out cutoff -> positive on in-window members
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "cutoff_mixed",
                   "2 of 4 members in cutoff: out-of-cutoff members excluded from the "
                   "medical numerator but retained as context -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"cutoffs": ["in_cutoff", "in_cutoff",
                                                      "out_of_cutoff", "out_of_cutoff"]},
                          "denominator_kwargs": {"value": 42}}),
        # 068 time missing -> not_evaluable
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "time_missing",
                   "critical event time missing (time_missing_not_evaluable) -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"cutoff": "time_missing_not_evaluable"},
                          "denominator_kwargs": {"value": 42}}),
        # 069 revision after cutoff vs event in cutoff -> positive
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "revision_vs_event_time",
                   "member revised after cutoff but clinical event in cutoff: revision "
                   "time is not event time -> in_cutoff -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"cutoff": "in_cutoff",
                                          "event_time": "2026-05-15"},
                          "denominator_kwargs": {"value": 42}}),
        # 070 single open window trend -> window_pair_gate, zero trend units
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_applicable", "single_window",
                   "trend with a single open window: window_pair_gate, zero trend "
                   "medical units",
                   risk_count=0, domains=["D01"], required_window_count_ref="SYN-D09-WINREQ-002",
                   parts={"windows": [_window(70, widx=1, wstart="2026-01-01",
                                              wend="2026-06-30", state="open")]}),
        # 071 cutoff identity conflict -> fail closed
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "cutoff_conflict",
                   "cutoff identity / policy conflict: fail closed before any medical "
                   "computation -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"cutoff_kwargs": {"identity_state": "conflict"},
                          "denominator_kwargs": {"value": 42}}),
        # 072 subject-time window truncated -> boundary
        _base_spec("p09_cutoff_window", "d09_cutoff_window",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "subject-time window truncated for late-activated subjects -> "
                   "boundary, no negative",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"windows": [_window(72, wstart="2026-02-01", wend="2026-03-31",
                                              wkind="subject_time_interval")],
                          "denominator_kwargs": {"kind": "subject_time", "value": 20}}),
    ]


def build_p10_specs() -> list[dict[str, Any]]:
    """method & statistical preconditions (8): signal unexpandable, validity
    insufficient, comparability passes, statistics alone cannot classify."""
    return [
        # 073 signal not expandable to members -> boundary
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "signal_unexpandable",
                   "statistical signal exists but cannot be expanded to member sources "
                   "-> boundary (never positive)",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 074 method validity preconditions insufficient -> not_evaluable
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "validity_insufficient",
                   "method validity preconditions not satisfied -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 075 trend comparability passes -> positive
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "comparability_passes",
                   "two windows, same method/denominator/stratum, comparability "
                   "preconditions met -> positive",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(75, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(75, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 2}}),
        # 076 statistics alone cannot classify -> boundary
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "statistics_only",
                   "p-value/KRI alone cannot set L1; statistical signal is only L1b "
                   "evidence -> boundary",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 077 trend self-prior-window reference valid -> positive
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "comparability_passes",
                   "self_prior_window reference kind with valid method preconditions -> "
                   "positive",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(77, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(77, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 1}}),
        # 078 valid counterevidence -> negative
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "negative", "none",
                   "counterevidence rule fully satisfied with member-level expansion -> "
                   "negative",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   counterevidence_refs=["SYN-D09-RULE-CE-079"],
                   matched_ce_refs=["SYN-D09-RULE-CE-079"],
                   parts={"denominator_kwargs": {"value": 42}}),
        # 079 signal expandable + validity OK -> positive
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "signal expandable to members and method validity preconditions met "
                   "-> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 080 trend method validity fails -> not_evaluable
        _base_spec("p10_method_statistical_preconditions", "d09_method_preconditions",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_evaluable", "validity_insufficient",
                   "trend method validity precondition fails -> not_evaluable",
                   risk_count=2, domains=["D01"], change_count=2,
                   parts={"windows": [_window(80, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(80, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable"}}),
    ]


def build_p11_specs() -> list[dict[str, Any]]:
    """center Query (10): non-redundant, finite list, three-part sentence, PD
    wording, display-only boundary."""
    return [
        # 081 positive + non-redundant query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_non_redundant",
                   "site_process_delta present, members listable (4 <= fanout 10), no "
                   "member query fully covers -> one D09 center Query draft",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 082 gap positive + PD wording query
        _base_spec("p11_center_query", "d09_center_query",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "query_non_redundant",
                   "gap positive with PD-related wording: query asks to verify whether "
                   "PD, not an unbounded accusation",
                   gap_count=5, domains=["D05", "D04"], gap_kwargs={"gap_kind": "pd_unreported"},
                   parts={"gap_kwargs": {"gap_kind": "pd_unreported", "field": "pd_reported"},
                          "opportunity_kwargs": {"expected": 42, "observed": 37, "missing": 5}}),
        # 083 query fully covered by member queries -> no D09 query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_fully_covered",
                   "uncovered member set empty (fully covered by individual member "
                   "queries, set-equality proven) -> no D09 query, pattern displayed",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"query_refs": ["SYN-D09-Q-083-01", "SYN-D09-Q-083-02",
                                                         "SYN-D09-Q-083-03"]},
                          "denominator_kwargs": {"value": 42}}),
        # 084 boundary -> no query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "boundary pattern: display only, no Query draft",
                   risk_count=1, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 18}}),
        # 085 members unlistable -> no query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_members_unlistable",
                   "members cannot be bound to a finite record list -> no Query draft, "
                   "pattern displayed",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 086 trend positive + query
        _base_spec("p11_center_query", "d09_center_query",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "query_non_redundant",
                   "trend positive with process delta -> one center Query draft",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(86, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(86, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 2}}),
        # 087 fanout 12 > max 10 -> display only
        _base_spec("p11_center_query", "d09_center_query",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "query_fanout_exceeded",
                   "member fanout 12 exceeds max_query_member_fanout 10: query list "
                   "displayed only, no Query generated",
                   gap_count=12, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 30, "missing": 12}}),
        # 088 no site process delta -> no query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_no_process_delta",
                   "no site-process-level delta beyond member queries -> no D09 Query",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 089 redundancy not applicable -> no query
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_no_process_delta",
                   "redundancy decision not_applicable (pattern kind has no query "
                   "contract) -> no Query",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 090 positive with three-part sentence contract
        _base_spec("p11_center_query", "d09_center_query",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_non_redundant",
                   "positive with basis/finding/action all traceable -> one D09 Query "
                   "draft with the fixed three-part structure",
                   risk_count=5, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
    ]


def build_p12_specs() -> list[dict[str, Any]]:
    """owner / lifecycle / counting isolation (8): D09/D10/D01-D08/R2 boundaries;
    no total-risk mixing; rule supersession."""
    return [
        # 091 positive: counts separated
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "individual_risk_count 5, affected_subject_count 4, event_count 6, "
                   "center_pattern_count 1: four counts isolated, no total-risk sum",
                   risk_count=5, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 092 gap positive: individual_risk_count=0
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "gap_only",
                   "gap-only positive: individual_risk_count=0, affected_subject_count 9, "
                   "numerator_gap_opportunity_count 9 -> positive without fabricated risk",
                   gap_count=9, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 093 rule supersession -> boundary (not comparable)
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "rule_supersession",
                   "pattern definition content hash changed vs prior run: superseded "
                   "lineage, not comparable -> boundary",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 094 R2 idempotency: same content replayed
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "revision_repeat",
                   "same immutable content replayed under new opaque run id: same "
                   "evaluation content identity and R2 handoff idempotency key -> positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 095 prior D09 risk continues -> positive
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "prior D09 RiskInstance exists and current run still hits -> "
                   "action=continue, positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 096 member risks closed individually but pattern persists -> positive
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "lifecycle_member_closed",
                   "individual member risks closed but the center pattern still hits "
                   "(new members) -> center pattern persists, positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 097 coverage unclosed + prior risk -> carry-forward, not resolved
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "carry_forward",
                   "prior D09 risk with current coverage unclosed: carry-forward, never "
                   "resolved_by_data -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 0, "state": "unclosed"}}),
        # 098 high priority no auto-close -> positive continue
        _base_spec("p12_owner_lifecycle_counting", "d09_owner_lifecycle",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "lifecycle_high_priority",
                   "high monitoring priority with member SAE/AESI: machine auto-close "
                   "forbidden, R2 adjudication required -> positive continue",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p13_specs() -> list[dict[str, Any]]:
    """deep-link / Chinese projection (8): one-hop source, no locator, internal
    words forbidden, hotspot not hidden."""
    return [
        # 099 full one-hop chain -> positive
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "full one-hop chain present: pattern -> numerator list -> member risk "
                   "-> visit/time anchor -> source locator -> deep-link target -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 100 no source locator -> boundary, no fabricated jump
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "none",
                   "source locator missing: projection must show 来源暂无法定位, no "
                   "fabricated jump -> boundary",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"loc": "SYN-D09-LOC-MISSING",
                                     "loc_state": "missing"},
                          "denominator_kwargs": {"value": 42}}),
        # 101 gap member with visit anchor + locator -> positive
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "none",
                   "gap members carry visit anchors and source locators: deep-link "
                   "targets resolvable -> positive",
                   gap_count=9, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 102 internal words forbidden in display lexicon
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "none",
                   "audience lexicon uses only the fixed Chinese phrases; internal terms "
                   "(typed handoff / candidate / 正式事实 ...) never exposed -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        # 103 hotspot not hidden by low center ratio -> positive (rate suppressed)
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "visibility_hidden",
                   "hotspot subject retained even though center ratio is low; hidden "
                   "members suppress the rate, never hide the hotspot -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"visibility_kwargs": {"rate_state": "suppressed",
                                                "hidden": ["SYN-D09-RISK-103-04"],
                                                "hidden_reasons": ["blinded_group"],
                                                "visible_n": 3, "eligible_n": 42},
                          "denominator_kwargs": {"value": 42}}),
        # 104 trend positive with deep-link targets -> positive
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "none",
                   "trend change ledger members carry window instance refs and source "
                   "locators -> positive with deep links",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(104, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(104, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 2}}),
        # 105 boundary n=1 with hotspot projection
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "n=1 high-risk member: boundary + hotspot projection, single case "
                   "never escalated to systematic",
                   risk_count=1, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high"},
                          "denominator_kwargs": {"value": 18}}),
        # 106 gap member without anchor -> boundary
        _base_spec("p13_deeplink_chinese_projection", "d09_deeplink_projection",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "boundary", "none",
                   "gap member lacks visit/time anchor: no locatable deep-link target "
                   "-> boundary",
                   gap_count=2, domains=["D05"],
                   parts={"gap_kwargs": {"anchor": "UNKNOWN", "anchor_state": "unresolved"},
                          "opportunity_kwargs": {"expected": 42, "observed": 40, "missing": 2}}),
    ]


# ---------------------------------------------------------------------------
# p14 hidden / anti-overfit (16): 8 base fixtures x 2 deterministic surface
# variants. Semantic content identical; project/center/subject/field/table
# names and array order change; thresholds/rules stay in authority refs.
# ---------------------------------------------------------------------------
_ANTI_OVERFIT_BASES = [
    # (kind, token, disposition, mc, desc, extra_spec_fields)
    ("repeated_subject_risk", "d09_repeated_subject_risk", "positive", "none",
     "base: repeated risk positive 4/42",
     {"risk_count": 4, "domains": ["D01"], "min_member_ref": "SYN-D09-MIN-002"}),
    ("repeated_subject_risk", "d09_repeated_subject_risk", "negative", "none",
     "base: closed zero negative", {"risk_count": 0, "domains": ["D01"]}),
    ("repeated_subject_risk", "d09_repeated_subject_risk", "boundary", "n1_minimum",
     "base: n=1 boundary + hotspot",
     {"risk_count": 1, "domains": ["D01"], "min_member_ref": "SYN-D09-MIN-002"}),
    ("repeated_subject_risk", "d09_repeated_subject_risk", "not_evaluable", "coverage_missing",
     "base: required coverage missing",
     {"risk_count": 2, "domains": ["D01", "D02"], "min_member_ref": "SYN-D09-MIN-002",
      "parts_cov": "partial"}),
    ("systematic_data_or_process_gap", "d09_systematic_data_or_process_gap", "positive", "none",
     "base: gap 9/42 positive", {"gap_count": 9, "domains": ["D05"], "parts_gap": True}),
    ("systematic_data_or_process_gap", "d09_systematic_data_or_process_gap", "negative", "none",
     "base: gap closed zero negative",
     {"gap_count": 0, "domains": ["D05"], "parts_gap": True, "parts_opp_zero": True}),
    ("within_site_time_trend", "d09_within_site_time_trend", "positive", "none",
     "base: trend increase positive",
     {"risk_count": 3, "domains": ["D01"], "change_count": 3,
      "min_member_ref": "SYN-D09-MIN-002", "parts_trend": True}),
    ("within_site_time_trend", "d09_within_site_time_trend", "not_applicable", "single_window",
     "base: single-window trend gate",
     {"risk_count": 0, "domains": ["D01"], "parts_single_window": True}),
]


def _anti_overfit_parts(extra: dict[str, Any], idx: int) -> dict[str, Any]:
    parts: dict[str, Any] = {}
    if extra.get("parts_cov") == "partial":
        parts["coverage"] = [_coverage("D01"), _coverage("D02", l0="partial", l1="partial")]
    if extra.get("parts_gap"):
        parts["gap_kwargs"] = {"field": "lab_clinical_significance"}
        if extra.get("parts_opp_zero"):
            parts["opportunity_kwargs"] = {"expected": 42, "observed": 42, "missing": 0}
        else:
            parts["opportunity_kwargs"] = {"expected": 42, "observed": 33, "missing": 9}
    if extra.get("parts_trend"):
        parts["windows"] = [_window(idx, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                            _window(idx, widx=2, wstart="2026-04-01", wend="2026-06-30")]
        parts["change_kwargs"] = {"change_kind": "increased", "abs_delta": 2}
    if extra.get("parts_single_window"):
        parts["windows"] = [_window(idx, widx=1, wstart="2026-01-01", wend="2026-06-30",
                                    state="open")]
    return parts


def build_p14_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for bi, base in enumerate(_ANTI_OVERFIT_BASES):
        kind, token, disp, mc, desc, extra = base
        for vi, variant in enumerate(("rename", "shuffle")):
            spec = _base_spec(
                "p14_hidden_anti_overfit", "d09_hidden_anti_overfit",
                kind, token, "evaluate_and_own", disp,
                "anti_overfit_rename" if variant == "rename" else "anti_overfit_shuffle",
                f"anti-overfit {variant} variant of: {desc}", **extra)
            spec["parts"] = _anti_overfit_parts(extra, 0)  # index fixed below
            spec["anti_overfit_variant"] = {
                "base_fixture_id": f"D09-FIX-BASE-{bi + 1:02d}",
                "semantic_equivalence_ref": f"SYN-D09-SEMEQ-{bi + 1:02d}",
                "surface_changes": [
                    {"changed_token": "project_ref", "from_value": PROJECT_REF,
                     "to_value": f"SYN-D09-PROJECT-{bi + 1:02d}-{variant}"},
                    {"changed_token": "site_stable_id", "from_value": SITE_REF,
                     "to_value": f"SYN-D09-SITE-{bi + 1:02d}-{variant}"},
                    {"changed_token": "subject_id_prefix", "from_value": "SYN-D09-SUBJ",
                     "to_value": f"SYN-D09-SUBJ-{bi + 1:02d}-{variant}"},
                    {"changed_token": "source_file", "from_value": "synthetic_source/dataset_a.json",
                     "to_value": f"synthetic_source/dataset_{bi + 1:02d}_{variant}.json"},
                    {"changed_token": "array_order", "from_value": "stable_identity_order",
                     "to_value": "shuffled_deterministic_order"},
                ],
                "variant_id": f"d09-ao-{bi + 1:02d}-{variant}",
            }
            spec["_ao_bi"] = bi
            spec["_ao_variant"] = variant
            specs.append(spec)
    return specs


def build_p15_specs() -> list[dict[str, Any]]:
    """D06/D10 consume-only (8): non-ownable tokens -> owner fail, zero D09
    medical units; unresolved token -> routing gate."""
    rows: list[dict[str, Any]] = []
    for ci, token in enumerate(CONSUME_ONLY_TOKENS):
        rows.append(_base_spec(
            "p15_d06_d10_consume_only", "d09_consume_only",
            None, token, "consume_only", "not_applicable", "consume_only",
            f"claim token {token} is not D09-owned: routed to original owner, zero D09 "
            "medical units; consume-only case",
            risk_count=0, domains=[], gate_kind="legal_matrix_row_absent",
            gate_reasons=[f"token_not_ownable:{token}"],
            expected_set_state="routed_consume_only"))
    for ci in range(2):
        rows.append(_base_spec(
            "p15_d06_d10_consume_only", "d09_consume_only",
            "routing_gate", "unresolved", "routing_gate", "not_applicable",
            "routing_gate",
            "unresolved clinical claim token: routing gate produced, zero medical units",
            risk_count=0, domains=[], gate_kind="legal_matrix_row_absent",
            gate_reasons=["claim_token_unresolved"],
            expected_set_state="routing_gate_unresolved"))
    return rows


def build_p16_specs() -> list[dict[str, Any]]:
    """L1 hole as zero risk (6): required L0 complete but L1 not_evaluable with
    zero members must NOT become negative."""
    return [
        # 131 repeated kind
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "required D01 L0 complete but L1 not_evaluable; zero members -> "
                   "not_evaluable, never negative",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01", l0="covered", l1="not_evaluable")],
                          "denominator_kwargs": {"value": 42}}),
        # 132 gap kind
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "gap kind: required L1 not_evaluable, zero opportunities observed -> "
                   "not_evaluable",
                   gap_count=0, domains=["D05"],
                   parts={"coverage": [_coverage("D05", l0="covered", l1="not_evaluable")]}),
        # 133 trend kind
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "trend kind: required L1 not_evaluable -> not_evaluable",
                   risk_count=0, domains=["D01"], change_count=0,
                   parts={"coverage": [_coverage("D01", l0="covered", l1="not_evaluable")],
                          "windows": [_window(133, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(133, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42}}),
        # 134 L1 partial -> not_evaluable
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "required L1 partial: completeness hole, zero members -> "
                   "not_evaluable",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01", l0="covered", l1="partial")],
                          "denominator_kwargs": {"value": 42}}),
        # 135 L1 not_evaluable with zero observed opportunities
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "l1_hole_zero_risk",
                   "L1 not_evaluable and 0 observed opportunities: zero observation is "
                   "not a zero-risk negative",
                   gap_count=0, domains=["D05"],
                   parts={"coverage": [_coverage("D05", l0="covered", l1="not_evaluable")],
                          "opportunity_kwargs": {"expected": 42, "observed": 0, "missing": 42}}),
        # 136 control: L0+L1 complete zero members -> negative (contrast)
        _base_spec("p16_l1_hole_zero_risk", "d09_l1_hole_zero_risk",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "negative", "none",
                   "control contrast: L0 and L1 both complete, zero members -> negative "
                   "(this is what L1-hole must NOT claim)",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01", l0="covered", l1="complete")],
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p17_specs() -> list[dict[str, Any]]:
    """gap kind without member risk (4): accepted gap 9/42, no individual
    RiskInstance, still positive without fabricating risk."""
    return [
        # 137 the contract's 9/42 example
        _base_spec("p17_gap_without_member_risk", "d09_gap_without_member_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "gap_only",
                   "accepted gap 9/42 (laboratory clinical significance field): no "
                   "individual RiskInstance exists; positive without fabricating risk, "
                   "individual_risk_count=0",
                   gap_count=9, domains=["D05", "D04"],
                   parts={"gap_kwargs": {"field": "lab_clinical_significance"},
                          "opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 138 different gap kind
        _base_spec("p17_gap_without_member_risk", "d09_gap_without_member_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "gap_only",
                   "missing required assessment opportunity 6/18: positive via accepted "
                   "gap members only",
                   gap_count=6, domains=["D05"],
                   parts={"gap_kwargs": {"gap_kind": "missing_required_assessment",
                                         "field": "assessment_visit"},
                          "opportunity_kwargs": {"expected": 18, "observed": 12, "missing": 6}}),
        # 139 gap positive with query
        _base_spec("p17_gap_without_member_risk", "d09_gap_without_member_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "gap_only",
                   "gap positive with site-process delta and listable members -> one "
                   "center Query draft",
                   gap_count=9, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 33, "missing": 9}}),
        # 140 high-priority gap positive
        _base_spec("p17_gap_without_member_risk", "d09_gap_without_member_risk",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "gap_only",
                   "unreported PD gap 2/8 with high monitoring priority: positive without "
                   "individual RiskInstance",
                   gap_count=2, domains=["D05", "D04"],
                   parts={"gap_kwargs": {"gap_kind": "pd_unreported", "field": "pd_reported"},
                          "opportunity_kwargs": {"expected": 8, "observed": 6, "missing": 2}}),
    ]


def build_p18_specs() -> list[dict[str, Any]]:
    """first-window trend (2): single closed window -> zero trend units +
    window_pair_gate."""
    return [
        _base_spec("p18_first_window_trend", "d09_first_window_trend",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_applicable", "single_window",
                   "single closed window before any comparable second window: "
                   "window_pair_gate (insufficient_windows), zero trend medical units",
                   risk_count=0, domains=["D01"], required_window_count_ref="SYN-D09-WINREQ-001",
                   parts={"windows": [_window(141, widx=1, wstart="2026-01-01", wend="2026-03-31")],
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p18_first_window_trend", "d09_first_window_trend",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_applicable", "single_window",
                   "single closed window with required_window_count_ref=2: "
                   "window_pair_gate, not a silent absence and not a negative",
                   risk_count=0, domains=["D01"], required_window_count_ref="SYN-D09-WINREQ-002",
                   parts={"windows": [_window(142, widx=1, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p19_specs() -> list[dict[str, Any]]:
    """Cartesian / stratum fanout (4): kind x domain x definition rejected; empty
    stratum default no unit; excess stratum does not explode."""
    return [
        # 143 cartesian definition fanout rejected
        _base_spec("p19_cartesian_stratum_fanout", "d09_cartesian_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_applicable", "cartesian_rejected",
                   "expected-set generator rejects kind x domain x definition cartesian "
                   "fanout (two definitions for the same kind/domain): D09GlobalAdmissionGate, "
                   "zero medical units",
                   risk_count=0, domains=["D01"], gate_kind="cartesian_definition_fanout",
                   gate_reasons=["definition_axis_duplicated:repeated_subject_risk/D01"],
                   expected_set_state="global_admission_failed",
                   parts={"stratum_kwargs": {"admission": "fanout_rejected"}}),
        # 144 domain x definition cartesian rejected
        _base_spec("p19_cartesian_stratum_fanout", "d09_cartesian_fanout",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_applicable", "cartesian_rejected",
                   "domain x definition cartesian fanout rejected at authority: zero "
                   "medical units",
                   gap_count=0, domains=["D05", "D04"], gate_kind="cartesian_definition_fanout",
                   gate_reasons=["definition_axis_duplicated:systematic_data_or_process_gap"],
                   expected_set_state="global_admission_failed"),
        # 145 empty stratum cell, definition requires it -> not_evaluable
        _base_spec("p19_cartesian_stratum_fanout", "d09_cartesian_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "stratum_required_empty",
                   "empty stratum cell but the definition explicitly requires the "
                   "stratum: missing unit -> L1 not_evaluable (integrity), not silence",
                   risk_count=0, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"stratum_kwargs": {"key": "age_18_64", "state": "empty",
                                             "admission": "rejected_empty"}}),
        # 146 excess stratum cells do not explode -> positive on admitted cells
        _base_spec("p19_cartesian_stratum_fanout", "d09_cartesian_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "stratum_fanout_rejected",
                   "stratum contract admits 2 cells; input declares 10 cells: cells "
                   "outside the contract are not admitted, evaluation runs on admitted "
                   "cells only -> positive, no fanout explosion",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"stratum_kwargs": {"key": "overall", "admission": "admitted"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p20_specs() -> list[dict[str, Any]]:
    """visibility / blinded stratum (6): hidden members, audience rate fail-closed,
    blinded stratum key rejected, legal non-blinded positive."""
    return [
        # 147 hidden members; rate suppressed; evaluation complete -> positive
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "visibility_hidden",
                   "hidden members exist: evaluation set complete, projectable set "
                   "smaller; rate projection suppressed, never a misleading precise rate "
                   "-> positive",
                   risk_count=5, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"visibility_kwargs": {"rate_state": "suppressed",
                                                "hidden": ["SYN-D09-RISK-147-04",
                                                           "SYN-D09-RISK-147-05"],
                                                "hidden_reasons": ["blinded_group"],
                                                "visible_n": 3, "eligible_n": 42},
                          "denominator_kwargs": {"value": 42}}),
        # 148 hidden members make numerator incomplete -> boundary
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "visibility_hidden",
                   "2 of 3 members hidden: numerator completeness affected -> boundary",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"visibility_kwargs": {"rate_state": "qualified",
                                                "hidden": ["SYN-D09-RISK-148-02",
                                                           "SYN-D09-RISK-148-03"],
                                                "hidden_reasons": ["not_projectable"],
                                                "visible_n": 1, "eligible_n": 42},
                          "denominator_kwargs": {"value": 42}}),
        # 149 blinded stratum key in input -> rejected -> not_evaluable
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "blinded_stratum_rejected",
                   "blinded study, stratum key is a treatment/arm role: stratum key "
                   "rejected, fail closed -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"stratum_kwargs": {"key": "treatment_arm", "admission": "fanout_rejected"},
                          "denominator_kwargs": {"value": 42}}),
        # 150 legal non-blinded analysis -> positive
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "positive", "authorized_unblinded",
                   "project explicitly permits non-blinded analysis and run scope is "
                   "authorized: frozen non-blinded stratum contract used -> positive",
                   risk_count=3, domains=["D01"], change_count=3,
                   blind="unblinded_authorized",
                   unblinded_ref="SYN-D09-UNBLIND-001",
                   parts={"windows": [_window(150, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(150, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "denominator_kwargs": {"value": 42},
                          "change_kwargs": {"change_kind": "increased", "abs_delta": 2}}),
        # 151 gap audience rate fail-closed
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "visibility_hidden",
                   "visible 2 of eligible 5 with 3 hidden: rate fail-closed, "
                   "suppressed; evaluation still positive",
                   gap_count=5, domains=["D05"],
                   parts={"gap_kwargs": {"anchor": "2026-02-01"},
                          "visibility_kwargs": {"rate_state": "suppressed",
                                                "hidden": ["SYN-D09-GAP-151-03",
                                                           "SYN-D09-GAP-151-04",
                                                           "SYN-D09-GAP-151-05"],
                                                "hidden_reasons": ["blinded_group"],
                                                "visible_n": 2, "eligible_n": 5},
                          "opportunity_kwargs": {"expected": 42, "observed": 37, "missing": 5}}),
        # 152 rate qualified -> boundary
        _base_spec("p20_visibility_blinded_stratum", "d09_visibility_blinded",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "visibility_hidden",
                   "partial projectability: rate qualified with visible_n/eligible_n "
                   "explicit -> boundary",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"visibility_kwargs": {"rate_state": "qualified",
                                                "hidden": ["SYN-D09-RISK-152-03"],
                                                "hidden_reasons": ["not_projectable"],
                                                "visible_n": 2, "eligible_n": 42},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p21_specs() -> list[dict[str, Any]]:
    """carry-forward on broken coverage (4): prior D09 risk + current gap must
    carry forward, never resolved_by_data."""
    return [
        _base_spec("p21_carry_forward_broken_coverage", "d09_carry_forward",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "carry_forward",
                   "prior D09 risk instance exists; current coverage missing -> "
                   "carry-forward with gap, never resolved_by_data -> not_evaluable",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"coverage": [_coverage("D01"), _coverage("D02", l0="missing",
                                                                   l1="missing")]}),
        _base_spec("p21_carry_forward_broken_coverage", "d09_carry_forward",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "carry_forward",
                   "prior D09 risk; current denominator unclosed -> carry-forward, "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 0, "state": "unclosed"}}),
        _base_spec("p21_carry_forward_broken_coverage", "d09_carry_forward",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "carry_forward",
                   "prior gap risk; current opportunity_state unknown -> carry-forward, "
                   "not_evaluable",
                   gap_count=2, domains=["D05"],
                   parts={"opportunity_kwargs": {"state": "unknown"}}),
        _base_spec("p21_carry_forward_broken_coverage", "d09_carry_forward",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_evaluable", "carry_forward",
                   "prior trend risk; current windows incomparable -> carry-forward, "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], change_count=2,
                   parts={"windows": [_window(156, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(156, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable"}}),
    ]


def build_p22_specs() -> list[dict[str, Any]]:
    """window id vs computed dates (4): shifted endpoints same definition -> same
    stable core; version change -> incomparable."""
    return [
        _base_spec("p22_window_id_vs_computed_dates", "d09_window_identity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "window_shift",
                   "computed window endpoints shifted by cutoff advance under the same "
                   "window definition: same stable core, different window instance -> "
                   "positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"windows": [_window(157, wstart="2026-02-01", wend="2026-04-30")],
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p22_window_id_vs_computed_dates", "d09_window_identity",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "window_definition_change",
                   "window definition version changed between windows: not comparable, "
                   "boundary (superseded lineage), no false change",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(158, widx=1, wstart="2026-01-01", wend="2026-03-31",
                                              window_def_id="SYN-D09-WD-158-1"),
                                      _window(158, widx=2, wstart="2026-04-01", wend="2026-06-30",
                                              window_def_id="SYN-D09-WD-158-2")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable"}}),
        _base_spec("p22_window_id_vs_computed_dates", "d09_window_identity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "window_shift",
                   "same window definition, computed dates shifted: "
                   "continued_from_cutoff_advance, same stable core -> positive",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"windows": [_window(159, wstart="2026-01-15", wend="2026-04-15")],
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p22_window_id_vs_computed_dates", "d09_window_identity",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_evaluable", "stratum_change",
                   "stratum contract changed between windows: not comparable -> "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], change_count=2,
                   parts={"windows": [_window(160, widx=1, wstart="2026-01-01", wend="2026-03-31"),
                                      _window(160, widx=2, wstart="2026-04-01", wend="2026-06-30")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable",
                                            "cause": "method"}}),
    ]


def build_p23_specs() -> list[dict[str, Any]]:
    """evidence_ref display not merge (4): shared source but two risk ids stay
    separate unless D08 verified."""
    return [
        _base_spec("p23_evidence_ref_display_not_merge", "d09_evidence_ref_display",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "evidence_ref_shared",
                   "two risk identities share one evidence_ref_id without D08-verified "
                   "same-origin binding: display cluster only, two members -> positive",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "distinct",
                                          "loc": "SYN-D09-LOC-SHARED-161"},
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p23_evidence_ref_display_not_merge", "d09_evidence_ref_display",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "evidence_ref_shared",
                   "shared source file and locator, two public risk identities: never "
                   "merged by string/source similarity -> positive",
                   risk_count=2, domains=["D01", "D02"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "distinct",
                                          "loc": "SYN-D09-LOC-SHARED-162"},
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p23_evidence_ref_display_not_merge", "d09_evidence_ref_display",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "same_origin_verified",
                   "shared evidence_ref with D08-verified same-origin binding: merged "
                   "into one member per subject -> positive",
                   risk_count=2, domains=["D01", "D08"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"origin": "verified_same_origin",
                                          "risk_identity": "SYN-D09-RISKID-163-PAIR"},
                          "denominator_kwargs": {"value": 42}}),
        _base_spec("p23_evidence_ref_display_not_merge", "d09_evidence_ref_display",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "evidence_ref_shared",
                   "two gap members share a locator but distinct subjects: two "
                   "opportunities, no merge -> positive",
                   gap_count=2, domains=["D05"],
                   parts={"gap_kwargs": {"loc": "SYN-D09-LOC-SHARED-164"},
                          "opportunity_kwargs": {"expected": 42, "observed": 40, "missing": 2}}),
    ]


def build_p24_specs() -> list[dict[str, Any]]:
    """Query fanout / redundancy (4): over-limit display only; no process delta
    no query."""
    return [
        _base_spec("p24_query_fanout_redundancy", "d09_query_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_fanout_exceeded",
                   "member fanout 12 exceeds max_query_member_fanout 10: query list "
                   "displayed, no Query generated -> positive",
                   risk_count=12, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        _base_spec("p24_query_fanout_redundancy", "d09_query_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "query_no_process_delta",
                   "no site-process-level delta beyond member queries -> no D09 Query",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        _base_spec("p24_query_fanout_redundancy", "d09_query_fanout",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "positive", "query_fully_covered",
                   "gap members fully covered by existing individual queries (set "
                   "equality proven) -> no D09 Query",
                   gap_count=4, domains=["D05"],
                   parts={"opportunity_kwargs": {"expected": 42, "observed": 38, "missing": 4}}),
        _base_spec("p24_query_fanout_redundancy", "d09_query_fanout",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "query_members_unlistable",
                   "members unlistable: members cannot be bound to a finite record "
                   "list (source locators missing) -> no Query, boundary display only",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"loc": "SYN-D09-LOC-MISSING",
                                     "loc_state": "missing"},
                          "denominator_kwargs": {"value": 18}}),
    ]


def build_p25_specs() -> list[dict[str, Any]]:
    """minimum member / authority (2): n=1 forced boundary; min field illegal ->
    authority fail."""
    return [
        _base_spec("p25_minimum_member_authority", "d09_minimum_member_authority",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "boundary", "n1_minimum",
                   "n=1 with valid minimum_member_subject_count_ref=2: forced boundary "
                   "+ hotspot, never positive",
                   risk_count=1, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high"},
                          "denominator_kwargs": {"value": 18}}),
        _base_spec("p25_minimum_member_authority", "d09_minimum_member_authority",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_applicable", "authority_fail",
                   "minimum_member_subject_count_ref illegal (declared 0): authority "
                   "fail closed, zero medical units",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-ILLEGAL-000",
                   gate_kind="global_integrity", gate_reasons=["minimum_member_count_invalid"],
                   expected_set_state="global_admission_failed",
                   parts={"denominator_kwargs": {"value": 42}}),
    ]


def build_p26_specs() -> list[dict[str, Any]]:
    """opportunity provenance (2): raw-only gap not positive; D05 enumeration
    conflict fail closed."""
    return [
        _base_spec("p26_opportunity_provenance", "d09_opportunity_provenance",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "raw_only_provenance",
                   "gap opportunities resolvable only from raw listing (no accepted "
                   "D05/shared/producer obligation object): raw-only must NOT be "
                   "positive -> not_evaluable",
                   gap_count=3, domains=["D05"],
                   parts={"opportunity_kwargs": {"provenance": "raw_listing_only",
                                                 "state": "insufficient"}}),
        _base_spec("p26_opportunity_provenance", "d09_opportunity_provenance",
                   "systematic_data_or_process_gap", "d09_systematic_data_or_process_gap",
                   "evaluate_and_own", "not_evaluable", "opportunity_conflict",
                   "D05 accepted opportunity enumeration conflicts with producer "
                   "obligation objects: fail closed, not_evaluable",
                   gap_count=2, domains=["D05"],
                   parts={"opportunity_kwargs": {"provenance": "enumeration_conflict",
                                                 "state": "unknown"}}),
    ]


def build_p27_specs() -> list[dict[str, Any]]:
    """lifecycle close (3): member closed but pattern persists; coverage unclosed;
    high priority no auto-close."""
    return [
        _base_spec("p27_lifecycle_close", "d09_lifecycle_close",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "lifecycle_member_closed",
                   "old member risks closed individually but the pattern still hits "
                   "with new members: center pattern stays open, positive",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 42}}),
        _base_spec("p27_lifecycle_close", "d09_lifecycle_close",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "lifecycle_coverage_broken",
                   "coverage unclosed this run: prior D09 risk carried forward, no "
                   "auto-close -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"denominator_kwargs": {"value": 0, "state": "unclosed"}}),
        _base_spec("p27_lifecycle_close", "d09_lifecycle_close",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "lifecycle_high_priority",
                   "high-priority center pattern (SAE/AESI member): machine auto-close "
                   "forbidden; R2 adjudication required -> positive continue",
                   risk_count=3, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"risk_kwargs": {"priority": "high"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p28_specs() -> list[dict[str, Any]]:
    """cross-window / site identity (3): rule/method/stratum different; site
    merge/split not comparable."""
    return [
        _base_spec("p28_cross_window_site_identity", "d09_cross_window_identity",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "boundary", "rule_supersession",
                   "positive rule version differs between windows: supersession, not "
                   "comparable -> boundary",
                   risk_count=3, domains=["D01"], change_count=3,
                   parts={"windows": [_window(176, widx=1, wstart="2026-01-01", wend="2026-03-31",
                                              window_contract_id="SYN-D09-WC-176-A"),
                                      _window(176, widx=2, wstart="2026-04-01", wend="2026-06-30",
                                              window_contract_id="SYN-D09-WC-176-B")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable",
                                            "cause": "rule_or_mapping"}}),
        _base_spec("p28_cross_window_site_identity", "d09_cross_window_identity",
                   "within_site_time_trend", "d09_within_site_time_trend",
                   "evaluate_and_own", "not_evaluable", "stratum_change",
                   "stratum method contract differs between windows -> not comparable, "
                   "not_evaluable",
                   risk_count=2, domains=["D01"], change_count=2,
                   parts={"windows": [_window(177, widx=1, wstart="2026-01-01", wend="2026-03-31",
                                              window_contract_id="SYN-D09-WC-177-A"),
                                      _window(177, widx=2, wstart="2026-04-01", wend="2026-06-30",
                                              window_contract_id="SYN-D09-WC-177-B")],
                          "change_kwargs": {"comparable": "not_evaluable",
                                            "change_kind": "not_comparable",
                                            "cause": "method"}}),
        _base_spec("p28_cross_window_site_identity", "d09_cross_window_identity",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "not_evaluable", "site_merge_split",
                   "site identity merged/split between runs: unit not comparable across "
                   "identity change -> not_evaluable",
                   risk_count=2, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   parts={"stratum_kwargs": {"admission": "fanout_rejected"},
                          "denominator_kwargs": {"value": 42}}),
    ]


def build_p29_specs() -> list[dict[str, Any]]:
    """R5 no cross-site inference (1): two sites side by side, no comparison or
    ranking, no D10 wording."""
    return [
        _base_spec("p29_r5_no_cross_site_inference", "d09_r5_no_cross_site",
                   "repeated_subject_risk", "d09_repeated_subject_risk",
                   "evaluate_and_own", "positive", "r5_side_by_side",
                   "two sites displayed side by side: each site's own completed D09 "
                   "unit; no cross-site comparison, ranking, or D10 wording -> positive "
                   "for this site's unit",
                   risk_count=4, domains=["D01"], min_member_ref="SYN-D09-MIN-002",
                   site=SITE_REF,
                   parts={"denominator_kwargs": {"value": 42}}),
    ]


# ---------------------------------------------------------------------------
# Catalog assembly
# ---------------------------------------------------------------------------
def all_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for builder in (
        build_p01_specs, build_p02_specs, build_p03_specs, build_p04_specs,
        build_p05_specs, build_p06_specs, build_p07_specs, build_p08_specs,
        build_p09_specs, build_p10_specs, build_p11_specs, build_p12_specs,
        build_p13_specs, build_p14_specs, build_p15_specs, build_p16_specs,
        build_p17_specs, build_p18_specs, build_p19_specs, build_p20_specs,
        build_p21_specs, build_p22_specs, build_p23_specs, build_p24_specs,
        build_p25_specs, build_p26_specs, build_p27_specs, build_p28_specs,
        build_p29_specs,
    ):
        specs.extend(builder())
    return specs


def assemble_catalog() -> dict[str, Any]:
    specs = all_specs()
    cases: list[dict[str, Any]] = []
    partition_counts: dict[str, int] = {}
    for idx, spec in enumerate(specs, start=1):
        partition = spec["partition"]
        partition_counts[partition] = partition_counts.get(partition, 0) + 1
        # p14 anti-overfit parts depend on the real case index; rebuild them here.
        if spec.get("_ao_bi") is not None:
            spec["parts"] = _anti_overfit_parts(
                _ANTI_OVERFIT_BASES[spec["_ao_bi"]][5], idx)
        typed = build_typed_input(spec, idx)
        family = spec.get("family", spec["partition"])
        cases.append(build_case_row(typed, spec, idx, partition, family))
    if len(cases) != MIN_CASE_COUNT:
        raise D09ArtifactError("assembly", "case_count",
                               f"assembled {len(cases)} cases != frozen floor {MIN_CASE_COUNT}")
    for partition, minimum in PARTITION_MINIMUMS.items():
        if partition_counts.get(partition, 0) < minimum:
            raise D09ArtifactError("assembly", "quota",
                                   f"partition {partition} has {partition_counts.get(partition, 0)} "
                                   f"< minimum {minimum}")
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
def assemble_quota_manifest(catalog: dict[str, Any]) -> dict[str, Any]:
    cases = catalog["cases"]
    by_partition: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_partition.setdefault(case["primary_partition_id"], []).append(case)

    partitions: list[dict[str, Any]] = []
    for partition_id, label_zh, minimum in PARTITIONS:
        members = by_partition.get(partition_id, [])
        sorted_ids = _sorted_unique([c["case_id"] for c in members], f"{partition_id} case ids")
        entry = {
            "partition_id": partition_id,
            "partition_label_zh": label_zh,
            "required_minimum": minimum,
            "actual_count": len(members),
            "sorted_case_ids": sorted_ids,
            "partition_hash": sha256_text(canonical_json({
                "partition_id": partition_id,
                "required_minimum": minimum,
                "actual_count": len(members),
                "sorted_case_ids": sorted_ids,
            })),
        }
        partitions.append(entry)

    union_sorted = _sorted_unique([c["case_id"] for c in cases], "union case ids")
    catalog_ids_sorted = _sorted_unique([c["case_id"] for c in cases], "catalog case ids")
    seen: set[str] = set()
    duplicates: list[str] = []
    for case_id in union_sorted:
        if case_id in seen:
            duplicates.append(case_id)
        seen.add(case_id)
    missing = [cid for cid in catalog_ids_sorted if cid not in seen]
    disjoint = len(duplicates) == 0 and len(missing) == 0 and len(seen) == len(catalog_ids_sorted)
    proof_core = {
        "union_sorted_case_ids": union_sorted,
        "catalog_sorted_case_ids": catalog_ids_sorted,
    }
    disjoint_union_proof = {
        "union_case_count": len(union_sorted),
        "union_sorted_case_ids": union_sorted,
        "catalog_case_id_set_equal": len(seen) == len(catalog_ids_sorted) and not missing,
        "pairwise_disjoint": disjoint,
        "duplicate_case_ids": duplicates,
        "missing_case_ids": missing,
        "proof_hash": sha256_text(canonical_json(proof_core)),
    }

    manifest: dict[str, Any] = {
        "artifact_kind": "d09_partition_quota_manifest",
        "manifest_id": QUOTA_MANIFEST_ID,
        "schema_version": SCHEMA_VERSION,
        "contract_semantic_hash": CONTRACT_SEMANTIC_HASH,
        "catalog_hash": catalog["catalog_hash"],
        "total_case_count": len(cases),
        "total_required_minimum": MIN_CASE_COUNT,
        "partitions": partitions,
        "disjoint_union_proof": disjoint_union_proof,
        "content_hash": "",
    }
    manifest["content_hash"] = content_hash(manifest, "content_hash")
    return manifest


def strip_substantive(value: Any) -> Any:
    """Remove run/snapshot/revision/version/wall-clock tokens before hashing."""
    if isinstance(value, dict):
        return {key: strip_substantive(item) for key, item in value.items()
                if key not in STRIP_KEYS}
    if isinstance(value, list):
        return [strip_substantive(item) for item in value]
    return value


STRIP_KEYS = frozenset({
    "envelope_id", "run_ref", "snapshot_ref", "source_revision_set",
    "source_content_hashes", "mode_contract_version", "authority_version",
})


def assemble_registry(catalog: dict[str, Any], quota_manifest: dict[str, Any],
                      generator_source_hash: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in catalog["cases"]:
        typed = case["typed_input"]
        rows.append({
            "case_id": case["case_id"],
            "fixture_id": case["fixture_id"],
            "oracle_case_id": case["oracle_case_id"],
            "manifest_case_id": case["manifest_case_id"],
            "test_id": f"D09-TEST-{case['case_id'].rsplit('-', 1)[-1]}",
            "oracle_resolution": "unresolved",
            "substantive_input_hash": sha256_text(canonical_json(strip_substantive(typed))),
        })
    bijection_ok = all(
        len({row[col] for row in rows}) == len(rows) for col in BIJECTION_COLUMNS)
    audit = {
        "row_count": len(rows),
        "columns": {col: len({row[col] for row in rows}) for col in BIJECTION_COLUMNS},
        "bijection_ok": bijection_ok,
    }
    oracle_reference_state = {
        "state": "unresolved",
        "reserved_for": "worker_02",
        "oracle_artifact_path": "reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json",
        "expected_leaf_policy": (
            "expected leaves exist only in the independent oracle artifact; the catalog "
            "expected_* fields are literal null; this registry holds identity rows only "
            "and never infers expected outcomes"),
        "catalog_expected_fields": "null",
    }
    registry: dict[str, Any] = {
        "artifact_kind": "d09_challenge_registry",
        "registry_id": REGISTRY_ID,
        "schema_version": SCHEMA_VERSION,
        "contract_semantic_hash": CONTRACT_SEMANTIC_HASH,
        "catalog_hash": catalog["catalog_hash"],
        "quota_manifest_hash": quota_manifest["content_hash"],
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
def validate_case(case: dict[str, Any], index: int) -> None:
    expect_exact_keys(case, CASE_KEYS, f"catalog case {index}")
    case_id = require_string(case["case_id"], "case_id")
    partition = require_string(case["primary_partition_id"], "primary_partition_id")
    if partition not in PARTITION_MINIMUMS:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{case_id} unknown partition {partition}")
    require_enum(case["disposition"], DISPOSITIONS, f"{case_id} disposition")
    require_string(case["family_id"], f"{case_id} family_id")
    require_string(case["fixture_id"], f"{case_id} fixture_id")
    if not sha256_hex(require_string(case["fixture_hash"], f"{case_id} fixture_hash")):
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{case_id} fixture_hash not a SHA-256 hex string")
    require_string(case["oracle_case_id"], f"{case_id} oracle_case_id")
    require_string(case["manifest_case_id"], f"{case_id} manifest_case_id")
    if case["expected_leaf_set"] is not None or case["expected_trace_leaf_set"] is not None \
            or case["expected_source_leaf_set"] is not None:
        raise D09ArtifactError("schema_parse", "expected_leak",
                               f"{case_id} expected_* must be literal null in the catalog")
    require_enum(case["mutation_class"], MUTATION_CLASSES, f"{case_id} mutation_class")
    expect_exact_keys(case["audience_contract"], AUDIENCE_CONTRACT_KEYS,
                      f"{case_id} audience_contract")

    token = require_enum(case["clinical_claim_token"], CLINICAL_CLAIM_TOKENS,
                         f"{case_id} clinical_claim_token")
    action = require_enum(case["owner_route"], OWNER_ROUTES, f"{case_id} owner_route")
    kind = case["pattern_kind"]
    if action == "evaluate_and_own":
        if token not in OWNED_TOKENS:
            raise D09ArtifactError("schema_parse", "token_mismatch",
                                   f"{case_id} evaluate_and_own with non-ownable token {token}")
        if kind != TOKEN_KIND_BIJECTION[token]:
            raise D09ArtifactError("schema_parse", "token_mismatch",
                                   f"{case_id} kind {kind} != token bijection "
                                   f"{TOKEN_KIND_BIJECTION[token]}")
    elif action == "consume_only":
        if token not in CONSUME_ONLY_TOKENS or kind is not None \
                or case["disposition"] != "not_applicable":
            raise D09ArtifactError("schema_parse", "token_mismatch",
                                   f"{case_id} consume_only requires non-ownable token, "
                                   "null kind, disposition not_applicable")
    elif action == "routing_gate":
        if token != "unresolved" or kind != "routing_gate" \
                or case["disposition"] != "not_applicable":
            raise D09ArtifactError("schema_parse", "token_mismatch",
                                   f"{case_id} routing_gate requires unresolved token, "
                                   "kind routing_gate, disposition not_applicable")
    else:
        raise D09ArtifactError("schema_parse", "token_mismatch",
                               f"{case_id} unsupported owner_route {action}")

    validate_typed_input(case["typed_input"], case_id)
    _validate_case_member_sanity(case, case_id)


def _validate_case_member_sanity(case: dict[str, Any], case_id: str) -> None:
    typed = case["typed_input"]
    total_members = (len(typed["subject_risk_members"]) + len(typed["gap_members"])
                     + len(typed["change_ledger_members"]))
    if case["disposition"] == "positive" and total_members == 0:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{case_id} positive requires at least one current member "
                               "risk / accepted gap member / change-ledger member")


def validate_typed_input(typed: dict[str, Any], case_id: str) -> None:
    expect_exact_keys(typed, TYPED_INPUT_KEYS, f"{case_id} typed_input envelope")
    if typed["input_schema"] != TYPED_INPUT_SCHEMA:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"{case_id} input_schema mismatch")
    expect_exact_keys(typed["scope_binding"], SCOPE_BINDING_KEYS, f"{case_id} scope_binding")
    expect_exact_keys(typed["pattern_definition"], PATTERN_DEFINITION_KEYS,
                      f"{case_id} pattern_definition")
    expect_exact_keys(typed["stratum"], STRATUM_KEYS, f"{case_id} stratum")
    expect_exact_keys(typed["denominator"], DENOMINATOR_KEYS, f"{case_id} denominator")
    expect_exact_keys(typed["opportunity"], OPPORTUNITY_KEYS, f"{case_id} opportunity")
    expect_exact_keys(typed["cutoff"], CUTOFF_KEYS, f"{case_id} cutoff")
    expect_exact_keys(typed["numeric_policy"], NUMERIC_POLICY_KEYS, f"{case_id} numeric_policy")
    expect_exact_keys(typed["visibility_decision"], VISIBILITY_KEYS,
                      f"{case_id} visibility_decision")
    expect_exact_keys(typed["expected_set"], EXPECTED_SET_KEYS, f"{case_id} expected_set")
    if typed["expected_set"]["admission_gate"] is not None:
        expect_exact_keys(typed["expected_set"]["admission_gate"], ADMISSION_GATE_KEYS,
                          f"{case_id} admission_gate")
    expect_exact_keys(typed["mutation_context"], MUTATION_CONTEXT_KEYS,
                      f"{case_id} mutation_context")
    authority = typed["resolved_authority_decision"]
    expect_exact_keys(authority, RESOLVED_AUTHORITY_KEYS,
                      f"{case_id} resolved_authority_decision")
    require_enum(authority["authority_validity_state"], AUTHORITY_VALIDITY_STATES,
                 f"{case_id} authority_validity_state")
    if authority["minimum_member_subject_count"] is not None:
        require_nonneg_int(authority["minimum_member_subject_count"],
                           f"{case_id} minimum_member_subject_count")
    for key in ("gap_positive_minimum_opportunity_count",
                "trend_positive_minimum_subject_count"):
        if authority[key] is not None:
            require_nonneg_int(authority[key], f"{case_id} {key}")
            if authority[key] < 1:
                raise D09ArtifactError("assembly", "schema_error",
                                       f"{case_id} {key} must be positive")
    authority_payload = {
        "authority_ref": authority["authority_ref"],
        "mode_contract_version": authority["mode_contract_version"],
        "minimum_member_subject_count": authority["minimum_member_subject_count"],
        "gap_positive_minimum_opportunity_count": (
            authority["gap_positive_minimum_opportunity_count"]),
        "trend_positive_minimum_subject_count": (
            authority["trend_positive_minimum_subject_count"]),
    }
    if authority["authority_content_hash"] != sha256_text(canonical_json(authority_payload)):
        raise D09ArtifactError("assembly", "hash_mismatch",
                               f"{case_id} authority_content_hash mismatch")
    if authority["mode_contract_version"] != typed["mode_contract_version"]:
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} authority ModeContract mismatch")
    kind = typed["pattern_definition"]["pattern_kind"]
    if authority["authority_validity_state"] == "valid":
        if (kind == "repeated_subject_risk"
                and (authority["minimum_member_subject_count"] is None
                     or authority["minimum_member_subject_count"] < 2)):
            raise D09ArtifactError("assembly", "schema_error",
                                   f"{case_id} repeated minimum authority invalid")
        if (kind == "systematic_data_or_process_gap"
                and authority["gap_positive_minimum_opportunity_count"] is None):
            raise D09ArtifactError("assembly", "schema_error",
                                   f"{case_id} gap minimum authority missing")
        if (kind == "within_site_time_trend"
                and authority["trend_positive_minimum_subject_count"] is None):
            raise D09ArtifactError("assembly", "schema_error",
                                   f"{case_id} trend minimum authority missing")
    method = typed["method_comparability_decision"]
    expect_exact_keys(method, METHOD_COMPARABILITY_KEYS,
                      f"{case_id} method_comparability_decision")
    require_enum(method["method_validity_state"], METHOD_VALIDITY_STATES,
                 f"{case_id} method_validity_state")
    require_enum(method["statistical_signal_role"], STATISTICAL_SIGNAL_ROLES,
                 f"{case_id} statistical_signal_role")
    require_enum(method["member_expansion_state"], MEMBER_EXPANSION_STATES,
                 f"{case_id} member_expansion_state")
    lineage = typed["lineage_context"]
    expect_exact_keys(lineage, LINEAGE_CONTEXT_KEYS, f"{case_id} lineage_context")
    require_enum(lineage["carry_forward_state"], CARRY_FORWARD_STATES,
                 f"{case_id} carry_forward_state")
    require_enum(lineage["lineage_relation"], LINEAGE_RELATIONS,
                 f"{case_id} lineage_relation")
    require_enum(lineage["site_identity_state"], SITE_IDENTITY_STATES,
                 f"{case_id} site_identity_state")
    policy = typed["center_query_policy"]
    expect_exact_keys(policy, CENTER_QUERY_POLICY_KEYS,
                      f"{case_id} center_query_policy")
    require_nonneg_int(policy["max_query_member_fanout"],
                       f"{case_id} policy max_query_member_fanout")
    if policy["max_query_member_fanout"] < 1:
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} policy fanout must be positive")
    policy_payload = {key: value for key, value in policy.items()
                      if key != "content_hash"}
    if policy["content_hash"] != sha256_text(canonical_json(policy_payload)):
        raise D09ArtifactError("assembly", "hash_mismatch",
                               f"{case_id} center_query_policy content_hash mismatch")
    if policy["mode_contract_version"] != typed["mode_contract_version"]:
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} Query policy ModeContract mismatch")
    query = typed["query_redundancy_decision"]
    expect_exact_keys(query, QUERY_REDUNDANCY_KEYS,
                      f"{case_id} query_redundancy_decision")
    require_enum(query["decision"], QUERY_REDUNDANCY_DECISIONS,
                 f"{case_id} query decision")
    require_nonneg_int(query["max_query_member_fanout"],
                       f"{case_id} max_query_member_fanout")
    if query["max_query_member_fanout"] != policy["max_query_member_fanout"]:
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} Query/policy fanout mismatch")
    if typed["pattern_definition"]["pattern_kind"] == "repeated_subject_risk":
        members = typed["subject_risk_members"]
    elif typed["pattern_definition"]["pattern_kind"] == "systematic_data_or_process_gap":
        members = typed["gap_members"]
    else:
        members = typed["change_ledger_members"]
    member_ids = sorted(member["member_id"] for member in members)
    if len(member_ids) != len(set(member_ids)):
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} duplicate member ids")
    if query["unit_member_set_hash"] != sha256_text(canonical_json(member_ids)):
        raise D09ArtifactError("assembly", "hash_mismatch",
                               f"{case_id} unit_member_set_hash mismatch")
    covered = set(query["covered_member_refs"])
    uncovered = set(query["uncovered_member_refs"])
    if (covered & uncovered or covered | uncovered != set(member_ids)
            or len(covered) != len(query["covered_member_refs"])
            or len(uncovered) != len(query["uncovered_member_refs"])):
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} Query member partition mismatch")
    member_queries = sorted(set(
        ref for member in members
        for ref in member["query_draft_refs"]
    )) if typed["pattern_definition"]["pattern_kind"] != "within_site_time_trend" else []
    if sorted(query["member_query_refs"]) != member_queries:
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} member_query_refs mismatch")
    proof_payload = {
        "decision": query["decision"],
        "covered": sorted(covered),
        "uncovered": sorted(uncovered),
        "member_queries": member_queries,
        "fanout": query["max_query_member_fanout"],
    }
    if query["coverage_proof_hash"] != sha256_text(canonical_json(proof_payload)):
        raise D09ArtifactError("assembly", "hash_mismatch",
                               f"{case_id} Query coverage proof mismatch")
    if (query["decision"] == "fully_covered_by_member_queries"
            and (uncovered or covered != set(member_ids)
                 or (member_ids and not query["member_query_refs"]))):
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} fully covered Query proof incomplete")
    if (query["decision"] == "site_process_delta_present" and member_ids
            and not uncovered):
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} site process delta lacks uncovered members")
    revisions = dict(zip(typed["source_revision_set"],
                         typed["source_content_hashes"]))
    if (not revisions or len(revisions) != len(typed["source_revision_set"])
            or len(typed["source_verification_records"]) != len(revisions)):
        raise D09ArtifactError("assembly", "schema_error",
                               f"{case_id} source verification coverage mismatch")
    seen_revisions: set[str] = set()
    for record in typed["source_verification_records"]:
        expect_exact_keys(record, SOURCE_VERIFICATION_RECORD_KEYS,
                          f"{case_id} source_verification_record")
        require_enum(record["verification_state"], SOURCE_VERIFICATION_STATES,
                     f"{case_id} verification_state")
        revision = record["revision"]
        if revision in seen_revisions or revision not in revisions:
            raise D09ArtifactError("assembly", "schema_error",
                                   f"{case_id} source revision mismatch")
        seen_revisions.add(revision)
        if record["declared_content_hash"] != revisions[revision]:
            raise D09ArtifactError("assembly", "hash_mismatch",
                                   f"{case_id} declared source hash mismatch")
        if (record["verification_state"] == "verified"
                and record["declared_content_hash"] != record["verified_content_hash"]):
            raise D09ArtifactError("assembly", "hash_mismatch",
                                   f"{case_id} verified source hash mismatch")
        if (record["verification_state"] == "mismatch"
                and record["declared_content_hash"] == record["verified_content_hash"]):
            raise D09ArtifactError("assembly", "hash_mismatch",
                                   f"{case_id} mismatch source hashes equal")
    variant = typed["anti_overfit_variant"]
    if variant is not None:
        expect_exact_keys(variant, ANTI_OVERFIT_KEYS, f"{case_id} anti_overfit_variant")
        for change in variant["surface_changes"]:
            expect_exact_keys(change, SURFACE_CHANGE_KEYS, f"{case_id} surface_change")
    expect_exact_keys(typed["audience_lexicon"], AUDIENCE_LEXICON_KEYS,
                      f"{case_id} audience_lexicon")
    for window in typed["analysis_windows"]:
        expect_exact_keys(window, WINDOW_KEYS, f"{case_id} analysis_window")
    for cov in typed["coverage"]:
        expect_exact_keys(cov, COVERAGE_KEYS, f"{case_id} coverage")
    accepted_risk_kinds = set(
        typed["pattern_definition"]["accepted_member_risk_kinds"])
    for member in typed["subject_risk_members"]:
        expect_exact_keys(member, RISK_MEMBER_KEYS, f"{case_id} risk member")
        require_enum(member["source_locator_resolution_state"],
                     LOCATOR_RESOLUTION_STATES,
                     f"{case_id} risk member {member['member_id']} locator state")
        if member["risk_kind"] not in accepted_risk_kinds:
            raise D09ArtifactError(
                "schema_parse", "schema_error",
                f"{case_id} risk member {member['member_id']} risk_kind "
                f"{member['risk_kind']!r} is not admitted by "
                "pattern_definition.accepted_member_risk_kinds")
    for member in typed["gap_members"]:
        expect_exact_keys(member, GAP_MEMBER_KEYS, f"{case_id} gap member")
        require_enum(member["source_locator_resolution_state"],
                     LOCATOR_RESOLUTION_STATES,
                     f"{case_id} gap member {member['member_id']} locator state")
        require_enum(member["anchor_resolution_state"], ANCHOR_RESOLUTION_STATES,
                     f"{case_id} gap member {member['member_id']} anchor state")
    for member in typed["change_ledger_members"]:
        expect_exact_keys(member, CHANGE_MEMBER_KEYS, f"{case_id} change member")
    for ref in typed["evidence_refs"]:
        expect_exact_keys(ref, EVIDENCE_REF_KEYS, f"{case_id} evidence_ref")


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    expect_exact_keys(catalog, CATALOG_KEYS, "catalog top-level")
    if catalog["catalog_id"] != CATALOG_ID:
        raise D09ArtifactError("schema_parse", "schema_error", "catalog_id mismatch")
    if catalog["version"] != SCHEMA_VERSION:
        raise D09ArtifactError("schema_parse", "schema_error", "catalog version mismatch")
    cases = catalog["cases"]
    if not isinstance(cases, list) or len(cases) != catalog["case_count"]:
        raise D09ArtifactError("schema_parse", "schema_error",
                               "case_count mismatch with cases list")
    if len(cases) < MIN_CASE_COUNT:
        raise D09ArtifactError("quota", "below_floor",
                               f"case_count {len(cases)} < {MIN_CASE_COUNT}")
    for col in ("case_id", "fixture_id", "oracle_case_id", "manifest_case_id"):
        ids = [case[col] for case in cases]
        if len(set(ids)) != len(ids):
            raise D09ArtifactError("bijection", "duplicate",
                                   f"duplicate {col} in catalog cases")
    seen_partitions: dict[str, list[str]] = {}
    for index, case in enumerate(cases, start=1):
        validate_case(case, index)
        seen_partitions.setdefault(case["primary_partition_id"], []).append(case["case_id"])
    for partition, minimum in PARTITION_MINIMUMS.items():
        count = len(seen_partitions.get(partition, []))
        if count < minimum:
            raise D09ArtifactError("quota", "below_floor",
                                   f"partition {partition}: {count} < {minimum}")
        if len(set(seen_partitions.get(partition, []))) != count:
            raise D09ArtifactError("quota", "duplicate",
                                   f"partition {partition} contains duplicate case ids")
    # disjoint union of partitions == full catalog case set
    union: set[str] = set()
    for ids in seen_partitions.values():
        union |= set(ids)
    if union != {case["case_id"] for case in cases}:
        raise D09ArtifactError("quota", "not_disjoint_union",
                               "partition union != complete catalog case set")
    if catalog["catalog_hash"] != content_hash(catalog, "catalog_hash"):
        raise D09ArtifactError("catalog_hash", "stale_hash", "catalog_hash mismatch")
    return cases


def validate_quota_manifest(manifest: dict[str, Any], catalog: dict[str, Any]) -> None:
    expect_exact_keys(manifest, QUOTA_TOP_KEYS, "quota manifest top-level")
    if manifest["manifest_id"] != QUOTA_MANIFEST_ID:
        raise D09ArtifactError("schema_parse", "schema_error", "quota manifest_id mismatch")
    if manifest["catalog_hash"] != catalog["catalog_hash"]:
        raise D09ArtifactError("catalog_hash", "stale_hash",
                               "quota manifest catalog_hash mismatch")
    if manifest["total_case_count"] != len(catalog["cases"]):
        raise D09ArtifactError("schema_parse", "schema_error", "quota total_case_count mismatch")
    if manifest["total_required_minimum"] != MIN_CASE_COUNT:
        raise D09ArtifactError("schema_parse", "schema_error", "quota minimum mismatch")
    all_ids: list[str] = []
    for entry in manifest["partitions"]:
        expect_exact_keys(entry, PARTITION_ENTRY_KEYS, "quota partition entry")
        partition = entry["partition_id"]
        if partition not in PARTITION_MINIMUMS:
            raise D09ArtifactError("schema_parse", "schema_error",
                                   f"quota unknown partition {partition}")
        if entry["required_minimum"] != PARTITION_MINIMUMS[partition]:
            raise D09ArtifactError("schema_parse", "schema_error",
                                   f"quota {partition} required_minimum mismatch")
        actual = [case["case_id"] for case in catalog["cases"]
                  if case["primary_partition_id"] == partition]
        if entry["actual_count"] != len(actual) or entry["sorted_case_ids"] != sorted(actual):
            raise D09ArtifactError("schema_parse", "schema_error",
                                   f"quota {partition} actual_count/sorted ids mismatch")
        if entry["partition_hash"] != sha256_text(canonical_json({
                "partition_id": partition,
                "required_minimum": entry["required_minimum"],
                "actual_count": entry["actual_count"],
                "sorted_case_ids": entry["sorted_case_ids"]})):
            raise D09ArtifactError("schema_parse", "schema_error",
                                   f"quota {partition} partition_hash mismatch")
        all_ids.extend(entry["sorted_case_ids"])
    proof = manifest["disjoint_union_proof"]
    expect_exact_keys(proof, DISJOINT_UNION_PROOF_KEYS, "quota disjoint_union_proof")
    if proof["union_sorted_case_ids"] != sorted(all_ids):
        raise D09ArtifactError("quota", "not_disjoint_union", "quota union mismatch")
    if not proof["catalog_case_id_set_equal"] or not proof["pairwise_disjoint"] \
            or proof["duplicate_case_ids"] or proof["missing_case_ids"]:
        raise D09ArtifactError("quota", "not_disjoint_union",
                               "quota disjoint union proof failed")
    if manifest["content_hash"] != content_hash(manifest, "content_hash"):
        raise D09ArtifactError("catalog_hash", "stale_hash", "quota content_hash mismatch")


def validate_registry(registry: dict[str, Any], catalog: dict[str, Any]) -> None:
    """Schema-level registry validation, independent of resolution state.

    Accepts both stage-A provisional (unresolved) and stage-B resolved
    registries; enforces that the oracle reference state and every row share
    one uniform resolution state (mixed/tampered states fail closed).
    """
    expect_exact_keys(registry, REGISTRY_TOP_KEYS, "registry top-level")
    if registry["registry_id"] != REGISTRY_ID:
        raise D09ArtifactError("schema_parse", "schema_error", "registry_id mismatch")
    if registry["catalog_hash"] != catalog["catalog_hash"]:
        raise D09ArtifactError("catalog_hash", "stale_hash", "registry catalog_hash mismatch")
    expect_exact_keys(registry["oracle_reference_state"], ORACLE_REFERENCE_STATE_KEYS,
                      "registry oracle_reference_state")
    state = registry["oracle_reference_state"]["state"]
    if state not in REGISTRY_RESOLUTION_STATES:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"registry oracle state {state!r} not in "
                               f"{REGISTRY_RESOLUTION_STATES}")
    rows = registry["rows"]
    if len(rows) != len(catalog["cases"]):
        raise D09ArtifactError("bijection", "row_count", "registry row count mismatch")
    resolutions: set[str] = set()
    for row in rows:
        expect_exact_keys(row, REGISTRY_ROW_KEYS, "registry row")
        resolutions.add(row["oracle_resolution"])
        for col in ("case_id", "fixture_id", "oracle_case_id", "manifest_case_id"):
            if row[col] != next(c[col] for c in catalog["cases"]
                                if c["case_id"] == row["case_id"]):
                raise D09ArtifactError("bijection", "mismatch",
                                       f"registry row {row['case_id']} {col} mismatch")
        if not sha256_hex(row["substantive_input_hash"]):
            raise D09ArtifactError("schema_parse", "schema_error",
                                   f"registry row {row['case_id']} substantive hash invalid")
    if len(resolutions) != 1:
        raise D09ArtifactError("schema_parse", "mixed_resolution",
                               f"registry rows must share one oracle_resolution, got "
                               f"{sorted(resolutions)}")
    resolution = resolutions.pop()
    if resolution not in REGISTRY_RESOLUTION_STATES:
        raise D09ArtifactError("schema_parse", "schema_error",
                               f"registry row oracle_resolution {resolution!r} not in "
                               f"{REGISTRY_RESOLUTION_STATES}")
    if resolution != state:
        raise D09ArtifactError("schema_parse", "resolution_mismatch",
                               f"oracle_reference_state.state {state!r} != row "
                               f"oracle_resolution {resolution!r}")
    audit = registry["bijection_audit"]
    if audit["row_count"] != len(rows) or not audit["bijection_ok"]:
        raise D09ArtifactError("bijection", "audit_failed", "registry bijection audit failed")
    if registry["content_hash"] != content_hash(registry, "content_hash"):
        raise D09ArtifactError("catalog_hash", "stale_hash", "registry content_hash mismatch")


def _registry_core(registry: dict[str, Any]) -> dict[str, Any]:
    """Projection of a registry onto its stage-A-owned fields: everything the
    catalog generator produces, excluding the declared stage-B delta fields."""
    core: dict[str, Any] = {key: item for key, item in registry.items()
                            if key not in RESOLVED_DELTA_TOP}
    reference = {key: item for key, item in registry["oracle_reference_state"].items()
                 if key not in RESOLVED_DELTA_REFERENCE}
    core["oracle_reference_state"] = reference
    core["rows"] = [{key: item for key, item in row.items() if key not in RESOLVED_DELTA_ROW}
                    for row in registry["rows"]]
    return core


def verify_resolved_registry(registry: dict[str, Any], catalog: dict[str, Any]) -> None:
    """Stage-B declared verification of the worker_02 resolution linkage.

    Oracle-blind: never reads the oracle artifact or expected leaves. Proves
    the resolved registry is EXACTLY a fresh provisional registry plus the
    declared resolution delta (state/resolution flips + policy content_hash
    suffix + recomputed content_hash; generator_hash must equal the frozen
    stage-A generator pin). Any other
    deviation -- tampered identity rows, altered substantive hashes, corrupted
    policy suffix, mixed resolution states -- fails closed.
    """
    validate_registry(registry, catalog)
    reference = registry["oracle_reference_state"]
    if reference["state"] != "resolved":
        raise D09ArtifactError("registry", "not_resolved",
                               "stage-B verification requires oracle_reference_state "
                               "state=resolved (stage A provisional registry is not a "
                               "complete chain)")
    if reference["reserved_for"] != "worker_02":
        raise D09ArtifactError("registry", "delta_mismatch",
                               f"reserved_for {reference['reserved_for']!r} != worker_02")
    if reference["oracle_artifact_path"] != DECLARED_ORACLE_ARTIFACT_PATH:
        raise D09ArtifactError("registry", "delta_mismatch",
                               f"oracle_artifact_path {reference['oracle_artifact_path']!r} "
                               f"!= declared {DECLARED_ORACLE_ARTIFACT_PATH}")
    if reference["catalog_expected_fields"] != "null":
        raise D09ArtifactError("registry", "delta_mismatch",
                               "catalog_expected_fields must remain literal 'null'")
    if any(row["oracle_resolution"] != "resolved" for row in registry["rows"]):
        raise D09ArtifactError("registry", "delta_mismatch",
                               "every registry row must be oracle_resolution=resolved")
    # generator_hash is pinned to the frozen stage-A generator revision; an
    # altered generator_hash fails closed even with a consistent reseal.
    if registry["generator_hash"] != STAGE_A_GENERATOR_SHA256:
        raise D09ArtifactError("registry", "generator_hash_mismatch",
                               f"resolved registry generator_hash "
                               f"{registry['generator_hash']} != frozen stage-A pin "
                               f"{STAGE_A_GENERATOR_SHA256}")
    # fresh provisional registry (oracle-blind): the stage-A source of truth.
    # quota manifest is computed exactly once per verification.
    quota_manifest = assemble_quota_manifest(catalog)
    provisional = assemble_registry(
        catalog, quota_manifest, _generator_code_hash())
    if provisional["generator_hash"] != STAGE_A_GENERATOR_SHA256:
        raise D09ArtifactError("registry", "generator_hash_mismatch",
                               "current generator code hash does not match the frozen "
                               "STAGE_A_GENERATOR_SHA256 pin")
    base_policy = provisional["oracle_reference_state"]["expected_leaf_policy"]
    policy = reference["expected_leaf_policy"]
    if not policy.startswith(base_policy):
        raise D09ArtifactError("registry", "delta_mismatch",
                               "resolved expected_leaf_policy base text deviates from "
                               "the provisional policy")
    tail = policy[len(base_policy):]
    if not re.fullmatch(re.escape(RESOLVED_POLICY_SUFFIX_PREFIX) + r"[0-9a-f]{64}", tail):
        raise D09ArtifactError("registry", "delta_mismatch",
                               "resolved expected_leaf_policy must end with "
                               "'; oracle artifact content_hash=<sha256 hex>'")
    if canonical_json(_registry_core(registry)) != canonical_json(_registry_core(provisional)):
        raise D09ArtifactError("registry", "tampered",
                               "resolved registry deviates from provisional registry + "
                               "declared stage-B delta")


def distribution_check(catalog: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in catalog["cases"]:
        counts[case["primary_partition_id"]] = counts.get(case["primary_partition_id"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Render pipeline + CLI
# ---------------------------------------------------------------------------
def _generate_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Assemble catalog, quota manifest, registry and validate everything."""
    validate_contract()
    catalog = assemble_catalog()
    cases = validate_catalog(catalog)
    quota_manifest = assemble_quota_manifest(catalog)
    validate_quota_manifest(quota_manifest, catalog)
    generator_hash = _generator_code_hash()
    registry = assemble_registry(catalog, quota_manifest, generator_hash)
    validate_registry(registry, catalog)
    if len(cases) != MIN_CASE_COUNT:
        raise D09ArtifactError("assembly", "case_count",
                               f"{len(cases)} cases != {MIN_CASE_COUNT}")
    return catalog, quota_manifest, registry, generator_hash


def _artifact_bytes(*artifacts: dict[str, Any]) -> list[bytes]:
    return [canonical_json(a).encode("utf-8") for a in artifacts]


def render_artifacts(verbose: bool = True, out_dir: Path | None = None) -> dict[str, Any]:
    def log(message: str) -> None:
        if verbose:
            print(message)

    log("D09 typed artifact generator (worker_01)")
    log("=" * 72)
    validate_contract()
    log(f"contract file/semantic SHA-256: {CONTRACT_SEMANTIC_HASH}  OK (v0.5 frozen pin)")

    catalog_path = (out_dir / CATALOG.name) if out_dir else CATALOG
    quota_path = (out_dir / QUOTA.name) if out_dir else QUOTA
    registry_path = (out_dir / REGISTRY.name) if out_dir else REGISTRY

    catalog_a, quota_a, registry_a, generator_hash = _generate_all()
    # pass B: two fresh generations must be byte-identical for every artifact
    catalog_b, quota_b, registry_b, _ = _generate_all()
    bytes_a = _artifact_bytes(catalog_a, quota_a, registry_a)
    bytes_b = _artifact_bytes(catalog_b, quota_b, registry_b)
    if bytes_a != bytes_b:
        raise D09ArtifactError("replay", "drift", "double-pass byte mismatch (nondeterministic generator)")
    log(f"double-pass byte-identical: catalog {len(bytes_a[0])} B, quota {len(bytes_a[1])} B, "
        f"registry {len(bytes_a[2])} B  OK")

    # Two-stage contract (docstring D6): stage A must never clobber the
    # worker_02 stage-B resolution. A resolved on-disk registry is protected.
    if registry_path.exists():
        try:
            existing = json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise D09ArtifactError("registry", "unreadable",
                                   f"existing registry {registry_path} unreadable: {exc}")
        if existing.get("oracle_reference_state", {}).get("state") == "resolved":
            raise D09ArtifactError(
                "registry", "refuse_clobber",
                f"{registry_path} is a resolved stage-B registry; stage-A render "
                "must not overwrite the worker_02 oracle resolution. Use --check "
                "(two-stage contract) to verify, or re-run the worker_02 resolution "
                "path to regenerate a resolved registry.")

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
            raise D09ArtifactError("replay", "drift", f"{label} reload byte mismatch")
    validate_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    validate_quota_manifest(json.loads(quota_path.read_text(encoding="utf-8")),
                            json.loads(catalog_path.read_text(encoding="utf-8")))
    validate_registry(json.loads(registry_path.read_text(encoding="utf-8")),
                      json.loads(catalog_path.read_text(encoding="utf-8")))
    log("reload validation  OK")

    log(f"\ncatalog_id    : {catalog_a['catalog_id']}")
    log(f"case_count    : {catalog_a['case_count']}  catalog_hash: {catalog_a['catalog_hash']}")
    log(f"quota manifest: {quota_a['manifest_id']}  content_hash: {quota_a['content_hash']}")
    log(f"registry_id   : {registry_a['registry_id']}  content_hash: {registry_a['content_hash']}")
    log(f"generator_hash: {generator_hash}")
    log("worker_01/worker_03 two-stage handoff (Codex):")
    log("  - expected_* fields are literal null in the catalog; no expected leaves exist")
    log("  - stage A provisional registry oracle_reference_state=unresolved; generator")
    log("    never reads the oracle or registry for generation (import/read closure)")
    log("  - stage B: the accepted resolved registry is verified by")
    log("    verify_resolved_registry() (oracle-blind delta check) and by")
    log("    tests/test_d09_artifact_generator.py (deep oracle linkage)")
    return {"catalog": catalog_a, "quota_manifest": quota_a, "registry": registry_a}


def check_artifacts(verbose: bool = True) -> int:
    """--check mode (two-stage contract, docstring D6): regenerate twice,
    validate, and compare catalog + quota manifest bytes with the on-disk
    artifacts; then run oracle-blind stage-B verification on the on-disk
    resolved registry. Never writes."""
    def log(message: str) -> None:
        if verbose:
            print(message)

    try:
        validate_contract()
        log("contract SHA-256 OK (v0.5 frozen pin)")
        catalog_a, quota_a, registry_a, generator_hash = _generate_all()
        catalog_b, quota_b, registry_b, _ = _generate_all()
        bytes_a = _artifact_bytes(catalog_a, quota_a, registry_a)
        bytes_b = _artifact_bytes(catalog_b, quota_b, registry_b)
        if bytes_a != bytes_b:
            raise D09ArtifactError("replay", "drift",
                                   "two fresh generations are NOT byte-identical")
        log("two fresh generations byte-identical  OK")
        for path, payload, label in ((CATALOG, catalog_a, "catalog"),
                                     (QUOTA, quota_a, "quota manifest")):
            if not path.exists():
                raise D09ArtifactError("check", "missing",
                                       f"--check: {path} does not exist (run without --check first)")
            on_disk = path.read_bytes()
            if on_disk != canonical_json(payload).encode("utf-8"):
                raise D09ArtifactError("check", "drift",
                                       f"--check: {path} differs from a fresh generation")
            log(f"{path} matches fresh generation ({len(on_disk)} B)  OK")
        # Stage B: the registry on disk is the accepted resolved registry; a
        # fresh generation of the registry is deliberately NOT byte-compared
        # (the fresh artifact is the provisional stage-A form). Instead the
        # declared stage-B resolution is verified oracle-blind: the on-disk
        # registry must be exactly the provisional registry plus the declared
        # worker_02 delta.
        if not REGISTRY.exists():
            raise D09ArtifactError("check", "missing",
                                   f"--check: {REGISTRY} does not exist (run without --check first)")
        on_disk_registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        verify_resolved_registry(on_disk_registry, catalog_a)
        log(f"{REGISTRY} resolved registry stage-B verification OK "
            f"({len(on_disk_registry['rows'])} rows, all resolved)")
        log(f"check passed: case_count={catalog_a['case_count']} catalog_hash="
            f"{catalog_a['catalog_hash']} generator_hash={generator_hash}")
        return 0
    except D09ArtifactError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="D09 typed artifact generator (worker_01)")
    parser.add_argument("--check", action="store_true",
                        help="regenerate twice, validate, compare with on-disk artifacts; no writes")
    parser.add_argument("--out", type=Path, default=None,
                        help="write artifacts to this directory instead of reviews/")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = parser.parse_args()
    try:
        if args.check:
            return check_artifacts(verbose=not args.quiet)
        render_artifacts(verbose=not args.quiet, out_dir=args.out)
        return 0
    except D09ArtifactError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
