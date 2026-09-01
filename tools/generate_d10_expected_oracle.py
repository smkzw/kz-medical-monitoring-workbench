#!/usr/bin/env python3
"""D10 expected-outcome oracle generator (worker_02, finite code executor).

Builds the independent R4-D10 v0.6 expected-outcome oracle: per-case
expected_leaf_set / expected_trace_leaf_set / expected_source_leaf_set,
expected_disposition_or_gate and forbidden_leaf_set, derived exclusively from
the embedded explicit case/family fact table (ORACLE_CASES) and the frozen
v0.6 contract. The catalog's expected_* fields are literal null; expected
leaves exist ONLY here.

Independence contract (task context + contract section 15/16):
  * This module NEVER reads the typed catalog, the challenge registry, the
    quota manifest, or any runtime code. All input facts come from the
    embedded explicit case/family specification table below (ORACLE_CASES),
    an independent copy of the frozen D10 family/partition fact
    specifications. No case-id -> disposition table exists: every expected
    outcome is DERIVED from typed facts by the contract rule engine below.
  * Standard library only; no network, no wall-clock, no randomness, no
    runtime/UI/service code. Two fresh generations are byte-identical.
  * The oracle content hash is the linkage value worker_02 declares in the
    registry's oracle_reference_state (stage-B) and the quota manifest's
    oracle_hash; this module never reads those artifacts.

Decision rules (contract sections 2.1/3.3/6/7/8/9/10/11/12/13/14):
  D1. Routing: unresolved token -> routing gate; consume_only / handoff_only
      rows -> routing / handoff gate with zero medical units; evaluate_and_own
      on a non-ownable token or a conflicting legal matrix row -> integrity
      gate; scope/envelope/identity failures -> global gate.
  D2. Expected-set: control-plane comparison/window gates produce
      control-plane gate leaves (zero medical units), never fake negatives.
  D3. Integrity (fail closed): denominator/time-segment tamper, cross-layer
      count mixing, D09 parent-descendant duplication, same-origin double
      counting, hidden-set algebra violations, blind treatment inference,
      rehash bypass, duplicate identities, audience engineering injection,
      hotspot hiding, query identity tamper -> integrity gate.
  D4. Completeness: required L1 holes, unclosed/zero denominators, missing
      analysis population, unclosed/raw-only opportunity ledgers, unresolved
      measure origin, incomplete safety/efficacy context, missing treatment
      assignment, invalid method evidence -> not_evaluable (zero events alone
      never negative); design non-applicability with authority -> not_applicable.
  D5. Gates: cross-site units admit only with a closed comparison set; trend
      units only with a closed window pair.
  D6. Evaluation: counterevidence fully explains -> negative; non-typed
      evidence (p-value/model majority) -> boundary; small sample / limited
      evidence / partial counterevidence / unresolved locators -> boundary;
      complete evaluation with rule hit -> positive; no hit -> negative.
  D7. Change: first full snapshot -> initial_current (no new/resolved/...);
      data-only revisions -> continued_from_data_revision / (proven)
      continued_from_cutoff_advance; any non-data cause -> not_comparable
      analysis-only leaf; claimed-vs-derived conflicts -> integrity gate.
  D8. Counts are stratified (individual risk / subject / event / pattern /
      site / signal / clue / query) and never mixed into one total.
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
ORACLE = ROOT / "reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"
AUTHORITY = ROOT / "reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"

CONTRACT_FILE_SHA256 = "c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95"
CONTRACT_SEMANTIC_HASH = CONTRACT_FILE_SHA256
ORACLE_ID = "medical-monitoring-r4-d10-expected-outcome-oracle"
SCHEMA_VERSION = "1.0.0"
ALGORITHM_VERSION = "d10_v1"
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
PROJECT_REF = "SYN-D10-PROJECT-001"

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
RATE_PROJECTION_STATES = ("permitted", "suppressed", "qualified")
QUERY_REDUNDANCY_DECISIONS = ("project_delta_present",
                              "fully_covered_by_member_queries",
                              "members_unlistable", "not_applicable")
PD_WORDING_STATES = ("not_pd", "verify_whether_pd")
MEMBER_EXPANSION_STATES = ("expanded", "unexpandable", "not_applicable")
MEMBER_SCOPE_STATES = ("in_scope", "wrong_project", "wrong_site", "wrong_subject",
                       "unresolvable")
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
TRACE_KINDS = ("evaluation_identity", "admission_replay")
TERMINAL_STATES = ("stable", "blocked")
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
CHANGE_DEFAULTS: dict[str, Any] = {
    "basis": "full", "comparison_state": "initial_full", "prior": False,
    "data_n": 0, "denom_n": 0, "coverage_n": 0, "knowledge_n": 0,
    "rule_n": 0, "mapping_n": 0, "model_n": 0, "method_n": 0,
    "population_n": 0, "visibility_n": 0, "mode_n": 0,
    "cutoff_state": "not_evaluable", "cutoff_predicate": False,
    "cutoff_policy_equal": False, "data_kind": None, "claimed_kind": None,
    "claimed_cause": None, "claimed_cutoff": None, "r2_action": None,
    "r2_prior": False, "r2_lineage": None, "carry_forward": False,
    "prior_boundary": "2026-03-31", "current_boundary": "2026-06-30",
}

# Oracle leaf schemas (uniform across all 312 entries; exact keys).
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

# ---------------------------------------------------------------------------
# Canonical JSON and hashing (proven D07/D08/D09 conventions)
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
        raise SystemExit("contract file SHA-256 mismatch (frozen v0.6 pin)")
    semantic = sha256_text(normalize_contract(raw.decode("utf-8")))
    if semantic != CONTRACT_SEMANTIC_HASH:
        raise SystemExit("contract semantic hash mismatch (frozen v0.6 pin)")
    return semantic


def sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


# ---------------------------------------------------------------------------
# Embedded explicit case/family fact table (independent copy of the frozen
# D10 family/partition fact specifications). Every row carries TYPED FACTS
# only: no disposition, no mutation/attack labels, no expected leaves. The
# rule engine below derives the expected outcome from these facts.
# Defaults (neutral synthetic base case) are applied in _hydrate.
# ---------------------------------------------------------------------------
DEFAULT_REQUIRED_DOMAINS = {
    "project_risk_distribution": ["D01", "D02", "D03", "D04"],
    "cross_site_pattern": ["D09", "D01"],
    "project_time_trend": ["D09", "D10"],
    "project_safety_trend": ["D07", "D01"],
    "project_efficacy_trend": ["D06", "D01"],
}
DEN_KIND_ESTIMATE = {
    "subject_time": "incidence_rate",
    "exposure_time": "exposure_adjusted_rate",
}


def _row(idx: int, partition: str, family: str, kind: str, token: str,
         owner: str, **kw: Any) -> dict[str, Any]:
    return {
        "idx": idx,
        "case_id": f"D10-CASE-{idx:03d}",
        "oracle_case_id": f"D10-ORACLE-{idx:03d}",
        "fixture_id": f"D10-FIX-{idx:03d}",
        "partition": partition,
        "family": family,
        "kind": kind,
        "token": token,
        "owner": owner,
        **kw,
    }


def _owned_row(idx: int, partition: str, family: str, kind: str,
               **kw: Any) -> dict[str, Any]:
    token = kw.pop("token", "d10_" + kind)
    return _row(idx, partition, family, kind, token, "evaluate_and_own", **kw)


# p01: 5 signal kinds x 12 (60)
def _build_p01_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = "p01_signal_kind_disposition"
    replay_change = {"basis": "full", "comparison_state": "initial_full",
                     "cutoff_state": "same_window", "cutoff_predicate": False,
                     "cutoff_policy_equal": True}
    for k, kind in enumerate(SIGNAL_KINDS):
        base = 1 + k * 12
        def r(idx: int, family: str, **kw: Any) -> dict[str, Any]:
            return _owned_row(idx, p, family, kind, **kw)
        rows.append(r(base, "d10_disposition_positive", hit="hit",
                      ce_declared=1, ce_matched=0))
        rows.append(r(base + 1, "d10_disposition_negative", hit="no_hit"))
        rows.append(r(base + 2, "d10_disposition_boundary", hit="hit",
                      ce_declared=1, ce_matched=0, small=True,
                      num_subject=1, num_event=1, num_site=1, individual=1))
        rows.append(r(base + 3, "d10_disposition_not_applicable", hit="hit",
                      design_applicable="not_applicable"))
        rows.append(r(base + 4, "d10_disposition_not_evaluable", hit="no_hit",
                      cov={DEFAULT_REQUIRED_DOMAINS[kind][0]:
                           ["covered", "not_evaluable"]}))
        rows.append(r(base + 5, "d10_counterevidence_explains", hit="hit",
                      ce_declared=2, ce_matched=2))
        rows.append(r(base + 6, "d10_false_positive_trap", hit="hit",
                      sources=["pvalue"]))
        rows.append(r(base + 7, "d10_false_negative_trap", hit="no_hit",
                      den_state="closed_zero", den_value=0))
        rows.append(r(base + 8, "d10_hidden_counted", hit="hit", ce_declared=1,
                      ce_matched=0, vis_hidden_members=2, rate_state="qualified"))
        rows.append(r(base + 9, "d10_replay_stable", hit="hit", ce_declared=1,
                      ce_matched=0, change=replay_change))
        rows.append(r(base + 10, "d10_comparison_gate",
                      es_state="control_plane_gate", gate_kind="comparison_set_gate",
                      gate_reasons=["comparison_insufficient_sites"],
                      comp_state="insufficient_sites", eligible_sites=2,
                      required_sites=3))
        rows.append(r(base + 11, "d10_window_pair_gate",
                      es_state="control_plane_gate", gate_kind="window_pair_gate",
                      gate_reasons=["window_pair_insufficient_windows"],
                      wins=1, pair_state="insufficient_windows",
                      unique_windows=1))
    return rows


# p02: owner routing (24)
_P02 = "p02_owner_routing_zero_medical"


def _build_p02_rows() -> list[dict[str, Any]]:
    rows = [
        _row(61, _P02, "d10_consume_d09_plain", "cross_site_pattern",
             "d09_within_site_pattern", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"]),
        _row(62, _P02, "d10_consume_d09_descendants", "cross_site_pattern",
             "d09_within_site_pattern", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"], pattern=1, descendants=2),
        _row(63, _P02, "d10_consume_d09_recompute", "cross_site_pattern",
             "d09_within_site_pattern", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"],
             count_layers=["d09_within_site_trend", "center_pattern"]),
        _row(64, _P02, "d10_consume_d01_plain", "project_risk_distribution",
             "d01_d08_individual_claim", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"]),
        _row(65, _P02, "d10_consume_d01_legal_row_mismatch",
             "project_risk_distribution", "d10_project_risk_distribution",
             "consume_only", es_state="routed_consume_only",
             gate_kind="routing_gate", gate_reasons=["legal_row_consume_only_ownable"]),
        _row(66, _P02, "d10_consume_d01_scope_mismatch", "project_risk_distribution",
             "d01_d08_individual_claim", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"], scope_eq="mismatch"),
        _row(67, _P02, "d10_handoff_benefit_risk", "project_safety_trend",
             "formal_benefit_risk_conclusion", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_handoff_only"]),
        _row(68, _P02, "d10_handoff_confirmatory", "project_efficacy_trend",
             "confirmatory_treatment_effect", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_handoff_only"]),
        _row(69, _P02, "d10_handoff_site_quality", "cross_site_pattern",
             "site_quality_judgment", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_handoff_only"]),
        _row(70, _P02, "d10_handoff_ownable_attempt", "project_safety_trend",
             "d10_project_safety_trend", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["legal_row_handoff_only_ownable"]),
        _row(71, _P02, "d10_unresolved_token", "project_risk_distribution",
             "unresolved", "routing_gate", es_state="routing_gate_unresolved",
             gate_kind="routing_gate", gate_reasons=["claim_token_unresolved"]),
        _row(72, _P02, "d10_unresolved_injection", "project_risk_distribution",
             "unresolved", "routing_gate", es_state="routing_gate_unresolved",
             gate_kind="routing_gate", gate_reasons=["claim_token_unresolved"],
             injection=True, injection_blocked=True),
        _owned_row(73, _P02, "d10_unauthorized_d09", "cross_site_pattern",
                   token="d09_within_site_pattern"),
        _owned_row(74, _P02, "d10_unauthorized_d01", "project_risk_distribution",
                   token="d01_d08_individual_claim"),
        _owned_row(75, _P02, "d10_unauthorized_benefit_risk",
                   "project_safety_trend", token="formal_benefit_risk_conclusion"),
        _owned_row(76, _P02, "d10_unauthorized_confirmatory",
                   "project_efficacy_trend", token="confirmatory_treatment_effect"),
        _owned_row(77, _P02, "d10_legal_row_kind_mismatch",
                   "project_risk_distribution", legal_match=False),
        _owned_row(78, _P02, "d10_envelope_revision_mismatch",
                   "project_risk_distribution", envelope_ok=False),
        _owned_row(79, _P02, "d10_global_scope_mismatch",
                   "project_risk_distribution", scope_eq="mismatch"),
        _owned_row(80, _P02, "d10_global_admission_failed",
                   "project_risk_distribution",
                   es_state="global_admission_failed", gate_kind="global_gate",
                   gate_reasons=["global_expected_set_failed"]),
        _owned_row(81, _P02, "d10_identity_unstable", "project_risk_distribution",
                   identity_ok=False),
        _owned_row(82, _P02, "d10_blind_authority_missing",
                   "project_efficacy_trend", blind_status="blinded",
                   es_state="global_admission_failed", gate_kind="global_gate",
                   gate_reasons=["blind_authority_missing"]),
        _owned_row(83, _P02, "d10_zero_medical_routing",
                   "project_risk_distribution", es_state="routed_consume_only",
                   gate_kind="routing_gate", gate_reasons=["token_consume_only"]),
        _owned_row(84, _P02, "d10_zero_medical_unresolved",
                   "project_risk_distribution", es_state="routing_gate_unresolved",
                   gate_kind="routing_gate", gate_reasons=["claim_token_unresolved"]),
    ]
    return rows


# p03: identity / scope / duplicate (24)
_P03 = "p03_identity_scope_duplicate"


def _build_p03_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(85, _P03, "d10_member_wrong_project", "project_risk_distribution",
                   member_scope_bad=True, member_scope_kind="wrong_project"),
        _owned_row(86, _P03, "d10_member_wrong_site", "project_risk_distribution",
                   member_scope_bad=True, member_scope_kind="wrong_site"),
        _owned_row(87, _P03, "d10_member_wrong_subject", "project_risk_distribution",
                   member_scope_bad=True, member_scope_kind="wrong_subject"),
        _owned_row(88, _P03, "d10_member_unresolvable", "project_risk_distribution",
                   member_scope_bad=True, member_scope_kind="unresolvable"),
        _owned_row(89, _P03, "d10_duplicate_member_ref", "project_risk_distribution",
                   dup_member_ref=True),
        _owned_row(90, _P03, "d10_scope_site_mismatch", "project_risk_distribution",
                   scope_eq="mismatch"),
        _owned_row(91, _P03, "d10_scope_subject_mismatch", "project_risk_distribution",
                   scope_eq="mismatch"),
        _owned_row(92, _P03, "d10_envelope_hash_mismatch", "project_risk_distribution",
                   scope_eq="mismatch"),
        _owned_row(93, _P03, "d10_revision_pair_mispaired", "project_risk_distribution",
                   envelope_ok=False),
        _owned_row(94, _P03, "d10_origin_verified_single_plane",
                   "project_safety_trend", hit="hit", ce_declared=1, ce_matched=0,
                   origin_decision="all_verified_same_origin",
                   origin_plane_duplicate=False, safety_missing=[]),
        _owned_row(95, _P03, "d10_origin_verified_double_count",
                   "project_safety_trend",
                   origin_decision="all_verified_same_origin",
                   origin_plane_duplicate=True, safety_missing=[]),
        _owned_row(96, _P03, "d10_origin_ambiguous", "project_safety_trend",
                   origin_decision="ambiguous", safety_missing=[]),
        _owned_row(97, _P03, "d10_origin_mixed_leaves", "project_safety_trend",
                   hit="hit", ce_declared=1, ce_matched=0,
                   origin_decision="mixed_verified_and_distinct",
                   safety_missing=[]),
        _owned_row(98, _P03, "d10_origin_wrong_scope", "project_safety_trend",
                   origin_decision="wrong_scope", safety_missing=[]),
        _owned_row(99, _P03, "d10_origin_not_evaluable", "project_safety_trend",
                   origin_decision="not_evaluable", safety_missing=[]),
        _owned_row(100, _P03, "d10_parent_descendant_common_numerator",
                   "cross_site_pattern", pattern=1, descendants=2,
                   desc_in_numerator=True),
        _owned_row(101, _P03, "d10_parent_descendant_separate_leaves",
                   "cross_site_pattern", hit="hit", ce_declared=1, ce_matched=0,
                   pattern=1, individual=5, descendants=5,
                   num_subject=5, num_event=5, num_site=3),
        _owned_row(102, _P03, "d10_origin_cross_envelope", "project_safety_trend",
                   origin_decision="wrong_scope", safety_missing=[]),
        _owned_row(103, _P03, "d10_origin_mixed_with_ambiguous",
                   "project_safety_trend", origin_decision="ambiguous",
                   safety_missing=[]),
        _owned_row(104, _P03, "d10_same_origin_safety_d07", "project_safety_trend",
                   origin_decision="all_verified_same_origin",
                   origin_plane_duplicate=True, safety_missing=[]),
        _owned_row(105, _P03, "d10_site_identity_merged", "project_risk_distribution",
                   identity_ok=False),
        _owned_row(106, _P03, "d10_subject_identity_split", "project_risk_distribution",
                   identity_ok=False),
        _owned_row(107, _P03, "d10_site_ledger_wrong_project", "cross_site_pattern",
                   envelope_ok=False),
        _owned_row(108, _P03, "d10_member_identity_reuse", "project_risk_distribution",
                   dup_member_ref=True),
    ]
    return rows


# p04: numerator / denominator / time (28)
_P04 = "p04_numerator_denominator_time"


def _build_p04_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(109, _P04, "d10_subject_event_separate", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   num_subject=5, num_event=9, num_site=2, individual=5),
        _owned_row(110, _P04, "d10_subject_event_mixed", "project_risk_distribution",
                   count_layers=["individual_risk", "event_or_outcome"]),
        _owned_row(111, _P04, "d10_planes_separate", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   pattern=1, individual=5, descendants=5,
                   num_subject=5, num_event=5, num_site=3),
        _owned_row(112, _P04, "d10_planes_common_numerator",
                   "project_risk_distribution",
                   count_layers=["center_pattern", "individual_risk",
                                 "project_signal"]),
        _owned_row(113, _P04, "d10_den_enrolled", "project_risk_distribution",
                   den_kind="enrolled_subjects", den_value=150,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(114, _P04, "d10_den_treated", "project_risk_distribution",
                   den_kind="treated_subjects", den_value=126,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(115, _P04, "d10_den_safety_evaluable", "project_risk_distribution",
                   den_kind="safety_evaluable_subjects", den_value=120,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(116, _P04, "d10_den_efficacy_evaluable", "project_risk_distribution",
                   den_kind="efficacy_evaluable_subjects", den_value=118,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(117, _P04, "d10_den_subject_time", "project_safety_trend",
                   den_kind="subject_time", den_value=1200, hit="hit",
                   ce_declared=1, ce_matched=0, safety_missing=[],
                   segments=2),
        _owned_row(118, _P04, "d10_den_exposure_time", "project_safety_trend",
                   den_kind="exposure_time", den_value=980, hit="hit",
                   ce_declared=1, ce_matched=0, safety_missing=[],
                   segments=2),
        _owned_row(119, _P04, "d10_den_opportunities", "project_risk_distribution",
                   den_kind="expected_assessment_opportunities", den_value=504,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(120, _P04, "d10_den_analysis_population", "project_efficacy_trend",
                   den_kind="analysis_population_members", den_value=112,
                   hit="hit", ce_declared=1, ce_matched=0, efficacy_missing=[]),
        _owned_row(121, _P04, "d10_closed_zero_design_na", "project_risk_distribution",
                   den_state="closed_zero", den_value=0, hit="no_hit",
                   design_applicable="not_applicable"),
        _owned_row(122, _P04, "d10_closed_zero_not_negative",
                   "project_risk_distribution", den_state="closed_zero",
                   den_value=0, hit="no_hit"),
        _owned_row(123, _P04, "d10_zero_events_complete_negative",
                   "project_risk_distribution", hit="no_hit",
                   num_subject=0, num_event=0, num_site=0, individual=0),
        _owned_row(124, _P04, "d10_exclusions_applied", "project_risk_distribution",
                   den_excl=["not_in_analysis_set"], den_value=126,
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(125, _P04, "d10_exclusion_counted", "project_risk_distribution",
                   excluded_in_numerator=True, den_excl=["not_in_analysis_set"]),
        _owned_row(126, _P04, "d10_subject_time_overlap", "project_safety_trend",
                   safety_missing=[], segments=2, seg_overlap=True),
        _owned_row(127, _P04, "d10_subject_time_valid", "project_safety_trend",
                   den_kind="subject_time", den_value=1200, hit="hit",
                   ce_declared=1, ce_matched=0, safety_missing=[],
                   segments=2),
        _owned_row(128, _P04, "d10_exposure_time_tamper", "project_safety_trend",
                   safety_missing=[], segments=2, seg_tamper=True),
        _owned_row(129, _P04, "d10_exposure_time_valid", "project_safety_trend",
                   den_kind="exposure_time", den_value=980, hit="hit",
                   ce_declared=1, ce_matched=0, safety_missing=[],
                   segments=2),
        _owned_row(130, _P04, "d10_opportunity_accepted", "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": True,
                        "provenance": "accepted_d05_plan"},
                   hit="hit", ce_declared=1, ce_matched=0,
                   num_subject=9, num_event=9, num_site=2, individual=9),
        _owned_row(131, _P04, "d10_opportunity_raw_only", "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": True,
                        "provenance": "raw_only"}),
        _owned_row(132, _P04, "d10_opportunity_incomplete", "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": False,
                        "provenance": "accepted_d05_plan"}),
        _owned_row(133, _P04, "d10_population_missing", "project_efficacy_trend",
                   pop_present=False, efficacy_missing=[]),
        _owned_row(134, _P04, "d10_population_mismatch", "project_efficacy_trend",
                   pop_present=False, efficacy_missing=[]),
        _owned_row(135, _P04, "d10_denominator_tamper", "project_risk_distribution",
                   den_tamper=True),
        _owned_row(136, _P04, "d10_segment_not_from_anchors", "project_safety_trend",
                   safety_missing=[], segments=1, seg_tamper=True),
    ]
    return rows


# p05: cross-site comparability (28)
_P05 = "p05_cross_site_comparability"


def _build_p05_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(137, _P05, "d10_small_site_boundary", "cross_site_pattern",
                   hit="hit", ce_declared=1, ce_matched=0,
                   comp_reasons=["site_small"], den_value=10,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(138, _P05, "d10_small_site_outlier_rate", "cross_site_pattern",
                   hit="hit", ce_declared=1, ce_matched=0,
                   comp_reasons=["site_small_outlier"], den_value=8,
                   num_subject=3, num_event=3, num_site=1, individual=3),
        _owned_row(139, _P05, "d10_small_site_heterogeneous", "cross_site_pattern",
                   hit="hit", ce_declared=1, ce_matched=0,
                   comp_reasons=["heterogeneous_sites"], eligible_sites=2,
                   den_value=18, num_subject=4, num_event=4, num_site=2,
                   individual=4),
        _owned_row(140, _P05, "d10_late_start_boundary", "cross_site_pattern",
                   comp_reasons=["site_late_start"], site_activation="late",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(141, _P05, "d10_late_start_outlier", "cross_site_pattern",
                   comp_reasons=["site_late_start_outlier"],
                   site_activation="late", hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(142, _P05, "d10_late_start_incomparable", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"],
                   comp_state="incomparable_sites", eligible_sites=2,
                   required_sites=3, site_activation="late"),
        _owned_row(143, _P05, "d10_case_mix_mismatch", "cross_site_pattern",
                   comp_reasons=["case_mix_mismatch"], hit="hit",
                   ce_declared=1, ce_matched=0),
        _owned_row(144, _P05, "d10_case_mix_missing", "cross_site_pattern",
                   comp_reasons=["case_mix_missing"]),
        _owned_row(145, _P05, "d10_followup_shortfall", "cross_site_pattern",
                   comp_reasons=["followup_shortfall"], hit="hit",
                   ce_declared=1, ce_matched=0),
        _owned_row(146, _P05, "d10_exposure_shortfall", "cross_site_pattern",
                   comp_reasons=["exposure_shortfall"], hit="hit",
                   ce_declared=1, ce_matched=0),
        _owned_row(147, _P05, "d10_site_coverage_hole", "cross_site_pattern",
                   cov={"D09": ["covered", "not_evaluable"]}),
        _owned_row(148, _P05, "d10_site_coverage_truncated", "cross_site_pattern",
                   cov={"D09": ["truncated", "partial"]}),
        _owned_row(149, _P05, "d10_method_invalid", "cross_site_pattern",
                   comp_reasons=["method_validity_insufficient"]),
        _owned_row(150, _P05, "d10_method_insufficient", "cross_site_pattern",
                   comp_reasons=["method_validity_insufficient"]),
        _owned_row(151, _P05, "d10_insufficient_sites_one", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=1,
                   required_sites=3),
        _owned_row(152, _P05, "d10_insufficient_sites_zero", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=0,
                   required_sites=3),
        _owned_row(153, _P05, "d10_incomparable_denominators", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"],
                   comp_state="incomparable_sites", eligible_sites=2,
                   required_sites=3),
        _owned_row(154, _P05, "d10_incomparable_windows", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"],
                   comp_state="incomparable_sites", eligible_sites=2,
                   required_sites=3),
        _owned_row(155, _P05, "d10_cross_site_ready_positive", "cross_site_pattern",
                   hit="hit", ce_declared=1, ce_matched=0, eligible_sites=3,
                   num_subject=7, num_event=9, num_site=3),
        _owned_row(156, _P05, "d10_cross_site_counterevidence", "cross_site_pattern",
                   hit="hit", ce_declared=2, ce_matched=2),
        _owned_row(157, _P05, "d10_d06_efficacy_as_pattern", "cross_site_pattern",
                   pattern=1, member_producer_d06=True),
        _owned_row(158, _P05, "d10_d06_measure_authorized", "project_efficacy_trend",
                   hit="hit", ce_declared=1, ce_matched=0, efficacy_missing=[],
                   eligible_sites=3, num_subject=7, num_event=7, num_site=3),
        _owned_row(159, _P05, "d10_site_quality_judgment_attempt",
                   "cross_site_pattern", comp_reasons=["site_quality_judgment"]),
        _row(160, _P05, "d10_site_quality_handoff", "cross_site_pattern",
             "site_quality_judgment", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_handoff_only"]),
        _owned_row(161, _P05, "d10_small_site_excluded", "cross_site_pattern",
                   es_state="control_plane_gate", gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=2,
                   required_sites=3, excluded_sites=1),
        _owned_row(162, _P05, "d10_site_evidence_incomplete", "cross_site_pattern",
                   comp_reasons=["site_evidence_incomplete"]),
        _owned_row(163, _P05, "d10_cross_site_positive_evidence", "cross_site_pattern",
                   hit="hit", ce_declared=1, ce_matched=0, eligible_sites=3,
                   num_subject=12, num_event=15, num_site=3, individual=12),
        _owned_row(164, _P05, "d10_cross_site_heterogeneous_boundary",
                   "cross_site_pattern", comp_reasons=["heterogeneous_sites"],
                   hit="hit", ce_declared=1, ce_matched=0),
    ]
    return rows


# p06: safety (24)
_P06 = "p06_safety_trend"


def _build_p06_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(165, _P06, "d10_safety_ae_proportion", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   num_subject=7, num_event=9, num_site=3),
        _owned_row(166, _P06, "d10_safety_no_hit", "project_safety_trend",
                   safety_missing=[], hit="no_hit"),
        _owned_row(167, _P06, "d10_safety_severity", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(168, _P06, "d10_safety_severity_scale_missing",
                   "project_safety_trend", safety_missing=["severity"]),
        _owned_row(169, _P06, "d10_safety_sae", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(170, _P06, "d10_safety_sae_singleton_hotspot",
                   "project_safety_trend", safety_missing=[], hit="hit",
                   ce_declared=1, ce_matched=0, hotspot=True,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(171, _P06, "d10_safety_aesi", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(172, _P06, "d10_safety_aesi_context_missing",
                   "project_safety_trend", safety_missing=["risk_window"]),
        _owned_row(173, _P06, "d10_safety_discontinuation", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(174, _P06, "d10_safety_discontinuation_small",
                   "project_safety_trend", safety_missing=[], hit="hit",
                   ce_declared=1, ce_matched=0, small=True,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(175, _P06, "d10_safety_lab_trend", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(176, _P06, "d10_safety_lab_no_hit", "project_safety_trend",
                   safety_missing=[], hit="no_hit"),
        _owned_row(177, _P06, "d10_safety_exposure_adjusted", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   den_kind="exposure_time", den_value=980, segments=2),
        _owned_row(178, _P06, "d10_safety_exposure_missing", "project_safety_trend",
                   safety_missing=["exposure"]),
        _owned_row(179, _P06, "d10_safety_special_population", "project_safety_trend",
                   safety_missing=[], hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(180, _P06, "d10_safety_special_population_small",
                   "project_safety_trend", safety_missing=[], hit="hit",
                   ce_declared=1, ce_matched=0, small=True,
                   num_subject=2, num_event=2, num_site=1, individual=2),
        _owned_row(181, _P06, "d10_safety_singleton_hidden_attempt",
                   "project_safety_trend", safety_missing=[], hotspot=True,
                   hotspot_hidden=True),
        _owned_row(182, _P06, "d10_safety_singleton_preserved",
                   "project_safety_trend", safety_missing=[], hotspot=True,
                   hit="hit", ce_declared=1, ce_matched=0,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(183, _P06, "d10_safety_pvalue_only", "project_safety_trend",
                   safety_missing=[], hit="hit", sources=["pvalue"]),
        _owned_row(184, _P06, "d10_safety_model_majority", "project_safety_trend",
                   safety_missing=[], hit="hit", sources=["model_majority"],
                   model_role="candidate_explanation", model_ensemble=1),
        _owned_row(185, _P06, "d10_safety_context_incomplete", "project_safety_trend",
                   safety_missing=["coding"]),
        _owned_row(186, _P06, "d10_safety_context_no_window", "project_safety_trend",
                   safety_missing=["risk_window"]),
        _owned_row(187, _P06, "d10_safety_formal_wording", "project_safety_trend",
                   safety_missing=[], injection=True, injection_blocked=False),
        _owned_row(188, _P06, "d10_safety_event_double_count", "project_safety_trend",
                   safety_missing=[], dup_member_ref=True),
    ]
    return rows


# p07: efficacy (24)
_P07 = "p07_efficacy_trend"


def _build_p07_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(189, _P07, "d10_efficacy_endpoint", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="responder_rate"),
        _owned_row(190, _P07, "d10_efficacy_endpoint_conflict",
                   "project_efficacy_trend", efficacy_missing=["endpoint"]),
        _owned_row(191, _P07, "d10_efficacy_timepoint", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="summary_statistic"),
        _owned_row(192, _P07, "d10_efficacy_timepoint_missing",
                   "project_efficacy_trend", efficacy_missing=["endpoint"]),
        _owned_row(193, _P07, "d10_efficacy_baseline", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="summary_statistic"),
        _owned_row(194, _P07, "d10_efficacy_baseline_missing",
                   "project_efficacy_trend", efficacy_missing=["endpoint"]),
        _owned_row(195, _P07, "d10_efficacy_missing_rule", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="responder_rate"),
        _owned_row(196, _P07, "d10_efficacy_missing_rule_absent",
                   "project_efficacy_trend", efficacy_missing=["missing"]),
        _owned_row(197, _P07, "d10_efficacy_intercurrent", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="responder_rate"),
        _owned_row(198, _P07, "d10_efficacy_intercurrent_absent",
                   "project_efficacy_trend", efficacy_missing=["intercurrent"]),
        _owned_row(199, _P07, "d10_efficacy_estimand_bound", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="model_estimate"),
        _owned_row(200, _P07, "d10_efficacy_estimand_mismatch",
                   "project_efficacy_trend", efficacy_missing=["estimand"]),
        _owned_row(201, _P07, "d10_efficacy_unblinded_authorized",
                   "project_efficacy_trend", efficacy_missing=[],
                   treatment_role_required=True, assignment_present=True,
                   blind_status="unblinded_authorized", hit="hit",
                   ce_declared=1, ce_matched=0, estimate="summary_statistic"),
        _owned_row(202, _P07, "d10_efficacy_assignment_missing",
                   "project_efficacy_trend", efficacy_missing=[],
                   treatment_role_required=True, assignment_present=False),
        _owned_row(203, _P07, "d10_efficacy_unauthorized_unblinded",
                   "project_efficacy_trend", efficacy_missing=[],
                   treatment_role_required=True, assignment_present=False,
                   blind_inference=True),
        _owned_row(204, _P07, "d10_efficacy_blind_inference_counts",
                   "project_efficacy_trend", efficacy_missing=[],
                   blind_inference=True),
        _owned_row(205, _P07, "d10_efficacy_responder_rate", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", ce_declared=1, ce_matched=0,
                   estimate="responder_rate"),
        _owned_row(206, _P07, "d10_efficacy_responder_no_context",
                   "project_efficacy_trend", efficacy_missing=["endpoint"]),
        _owned_row(207, _P07, "d10_efficacy_model_no_estimand",
                   "project_efficacy_trend", efficacy_missing=["estimand"]),
        _owned_row(208, _P07, "d10_efficacy_summary_no_population",
                   "project_efficacy_trend", pop_present=False,
                   efficacy_missing=[]),
        _owned_row(209, _P07, "d10_efficacy_pvalue_only", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", sources=["pvalue"]),
        _owned_row(210, _P07, "d10_efficacy_model_majority", "project_efficacy_trend",
                   efficacy_missing=[], hit="hit", sources=["model_majority"],
                   model_role="candidate_explanation", model_ensemble=1),
        _owned_row(211, _P07, "d10_efficacy_confirmatory_attempt",
                   "project_efficacy_trend", efficacy_missing=[],
                   injection=True, injection_blocked=False),
        _owned_row(212, _P07, "d10_efficacy_window_incomparable",
                   "project_efficacy_trend", es_state="control_plane_gate",
                   gate_kind="window_pair_gate",
                   gate_reasons=["window_pair_incomparable_windows"],
                   pair_state="incomparable_windows", wins=2, unique_windows=2,
                   efficacy_missing=[]),
    ]
    return rows


# p08: change cause / lineage (28)
_P08 = "p08_change_cause_lineage"


def _build_p08_rows() -> list[dict[str, Any]]:
    def ch(**kw: Any) -> dict[str, Any]:
        base = {"basis": "full", "comparison_state": "initial_full",
                "prior": False, "data_n": 0, "denom_n": 0, "coverage_n": 0,
                "knowledge_n": 0, "rule_n": 0, "mapping_n": 0, "model_n": 0,
                "method_n": 0, "population_n": 0, "visibility_n": 0, "mode_n": 0,
                "cutoff_state": "not_evaluable", "cutoff_predicate": False,
                "cutoff_policy_equal": False, "data_kind": None,
                "claimed_kind": None, "claimed_cause": None,
                "claimed_cutoff": None, "r2_action": None, "r2_prior": False,
                "r2_lineage": None, "carry_forward": False}
        base.update(kw)
        return base

    rows = [
        _owned_row(213, _P08, "d10_initial_full_positive", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(r2_action="create", r2_prior=False,
                             r2_lineage="initial_full_snapshot")),
        _owned_row(214, _P08, "d10_initial_full_negative", "project_risk_distribution",
                   hit="no_hit", change=ch()),
        _owned_row(215, _P08, "d10_initial_full_fake_new", "project_risk_distribution",
                   change=ch(claimed_kind="new", claimed_cause="data")),
        _owned_row(216, _P08, "d10_incremental_new", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=2, data_kind="new",
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(217, _P08, "d10_incremental_resolved", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="resolved",
                             r2_action="propose_close", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(218, _P08, "d10_incremental_continued", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="continued",
                             r2_action="continue", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(219, _P08, "d10_incremental_downgraded", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="downgraded",
                             r2_action="update", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(220, _P08, "d10_cutoff_strict_advance", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(221, _P08, "d10_cutoff_first_positive_no_prior",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(222, _P08, "d10_cutoff_predicate_tamper", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="same_window", cutoff_predicate=False,
                             cutoff_policy_equal=True, claimed_cutoff="strict_advance",
                             r2_action="create", r2_prior=False)),
        _owned_row(223, _P08, "d10_same_window_replay", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, data_kind="new",
                             cutoff_state="same_window", cutoff_predicate=False,
                             cutoff_policy_equal=True, claimed_cutoff="strict_advance",
                             r2_action="create", r2_prior=False)),
        _owned_row(224, _P08, "d10_cutoff_rule_mixed", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new", rule_n=1,
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(225, _P08, "d10_rule_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, rule_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_rule_or_mapping_change")),
        _owned_row(226, _P08, "d10_mapping_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, mapping_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_rule_or_mapping_change")),
        _owned_row(227, _P08, "d10_method_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, method_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(228, _P08, "d10_population_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, population_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(229, _P08, "d10_visibility_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, visibility_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_visibility_change")),
        _owned_row(230, _P08, "d10_coverage_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, coverage_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="coverage_regressed")),
        _owned_row(231, _P08, "d10_mode_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, mode_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_mode_change")),
        _owned_row(232, _P08, "d10_mixed_non_data", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, rule_n=1, method_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(233, _P08, "d10_r2_create_with_prior", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             r2_action="create", r2_prior=True)),
        _owned_row(234, _P08, "d10_r2_carry_forward_broken_coverage",
                   "project_risk_distribution",
                   cov={"D01": ["covered", "not_evaluable"]},
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="continued",
                             carry_forward=True, r2_action="continue",
                             r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(235, _P08, "d10_r2_wrong_lineage", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             r2_action="create", r2_prior=False,
                             r2_lineage="superseded_by_mode_change")),
        _owned_row(236, _P08, "d10_data_revision_continued", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=2, data_kind="continued",
                             r2_action="continue", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(237, _P08, "d10_coverage_regression", "project_risk_distribution",
                   cov={"D01": ["missing", "missing"]},
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, coverage_n=1,
                             r2_lineage="coverage_regressed")),
        _owned_row(238, _P08, "d10_knowledge_change_analysis_only",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0,
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=0, knowledge_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_knowledge_change")),
        _owned_row(239, _P08, "d10_fake_data_cause", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, rule_n=1, data_kind="new",
                             claimed_kind="new", claimed_cause="data",
                             r2_action="continue", r2_prior=True)),
        _owned_row(240, _P08, "d10_cutoff_not_evaluable", "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="not_evaluable", cutoff_predicate=False,
                             cutoff_policy_equal=False, r2_action="create",
                             r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
    ]
    return rows


# p09: query / deep link (20)
_P09 = "p09_query_deeplink"


def _build_p09_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(241, _P09, "d10_query_generated", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="project_delta_present", q_uncovered=7),
        _owned_row(242, _P09, "d10_query_within_fanout", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="project_delta_present", q_uncovered=7,
                   q_fanout=100),
        _owned_row(243, _P09, "d10_query_fully_covered", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="fully_covered_by_member_queries",
                   q_uncovered=0, q_covered=7),
        _owned_row(244, _P09, "d10_query_unlistable", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="members_unlistable", q_uncovered=7,
                   q_unlistable=True),
        _owned_row(245, _P09, "d10_query_fanout_exceeded", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="project_delta_present", q_uncovered=101,
                   q_fanout=100),
        _owned_row(246, _P09, "d10_query_pd_wording", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="project_delta_present", q_uncovered=2,
                   q_pd="verify_whether_pd"),
        _owned_row(247, _P09, "d10_query_non_pd", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   q_decision="project_delta_present", q_uncovered=3),
        _owned_row(248, _P09, "d10_query_three_part_sentences",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0, q_decision="project_delta_present",
                   q_uncovered=4),
        _owned_row(249, _P09, "d10_deeplink_member", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, dl_n=1),
        _owned_row(250, _P09, "d10_deeplink_site", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, dl_n=1),
        _owned_row(251, _P09, "d10_deeplink_subject_site_pair",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0, dl_n=1),
        _owned_row(252, _P09, "d10_deeplink_deficient", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, locator_missing=True),
        _owned_row(253, _P09, "d10_journey_one_hop", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, dl_n=3),
        _owned_row(254, _P09, "d10_source_locator_missing", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, locator_missing=True),
        _owned_row(255, _P09, "d10_query_reorder_invariant",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0, q_decision="project_delta_present",
                   q_uncovered=7),
        _owned_row(256, _P09, "d10_query_source_tamper", "project_risk_distribution",
                   q_ids_mismatch=True, q_decision="project_delta_present",
                   q_uncovered=7),
        _owned_row(257, _P09, "d10_query_redundancy_tamper",
                   "project_risk_distribution", q_decision="project_delta_present",
                   q_uncovered=3, q_covered=2),
        _owned_row(258, _P09, "d10_query_duplicate_per_unit",
                   "project_risk_distribution", q_duplicate=True,
                   q_decision="project_delta_present", q_uncovered=7),
        _owned_row(259, _P09, "d10_deeplink_subject_only", "project_risk_distribution",
                   dl_violation=True, dl_n=1),
        _owned_row(260, _P09, "d10_audience_injection_blocked",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0, injection=True, injection_blocked=True,
                   q_decision="project_delta_present", q_uncovered=7),
    ]
    return rows


# p10: visibility / blindness (16)
_P10 = "p10_visibility_blindness"


def _build_p10_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(261, _P10, "d10_vis_hidden_members", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   vis_hidden_members=2, rate_state="qualified"),
        _owned_row(262, _P10, "d10_vis_hidden_denominator", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   vis_hidden_sites=1, rate_state="suppressed"),
        _owned_row(263, _P10, "d10_vis_rate_suppressed", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   vis_hidden_members=3, rate_state="suppressed"),
        _owned_row(264, _P10, "d10_vis_rate_qualified", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   vis_hidden_members=2, rate_state="qualified"),
        _owned_row(265, _P10, "d10_vis_hidden_site", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0,
                   vis_hidden_sites=1, rate_state="qualified"),
        _owned_row(266, _P10, "d10_vis_hidden_omission", "project_risk_distribution",
                   vis_hidden_members=2, hidden_omission=True,
                   vis_algebra_ok=False),
        _owned_row(267, _P10, "d10_vis_algebra_violation", "project_risk_distribution",
                   vis_hidden_members=2, vis_algebra_ok=False),
        _owned_row(268, _P10, "d10_vis_dl_eligible_valid", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, dl_n=2),
        _owned_row(269, _P10, "d10_vis_dl_eligible_violation",
                   "project_risk_distribution", dl_violation=True),
        _owned_row(270, _P10, "d10_vis_dl_hidden_site_pair",
                   "project_risk_distribution", dl_violation=True),
        _owned_row(271, _P10, "d10_vis_visible_n_algebra", "project_risk_distribution",
                   vis_algebra_ok=False),
        _owned_row(272, _P10, "d10_vis_hidden_counts_algebra",
                   "project_risk_distribution", vis_hidden_members=2,
                   vis_algebra_ok=False, vis_hidden_counts_bad=True),
        _owned_row(273, _P10, "d10_vis_blind_denominator_inference",
                   "project_risk_distribution", blind_inference=True),
        _owned_row(274, _P10, "d10_vis_blind_label_inference",
                   "project_risk_distribution", blind_inference=True),
        _owned_row(275, _P10, "d10_vis_unblinded_authorized",
                   "project_efficacy_trend", efficacy_missing=[],
                   treatment_role_required=True, assignment_present=True,
                   blind_status="unblinded_authorized", hit="hit",
                   ce_declared=1, ce_matched=0, estimate="summary_statistic"),
        _owned_row(276, _P10, "d10_vis_hidden_dropped", "project_risk_distribution",
                   vis_hidden_members=2, vis_hidden_dropped=True,
                   vis_algebra_ok=False),
    ]
    return rows


# p11: unicode / tamper / bijection (20)
_P11 = "p11_unicode_tamper_bijection"
_REPLAY_CHANGE = {"basis": "full", "comparison_state": "initial_full",
                  "cutoff_state": "same_window", "cutoff_predicate": False,
                  "cutoff_policy_equal": True}


def _build_p11_rows() -> list[dict[str, Any]]:
    rows = [
        _owned_row(277, _P11, "d10_nfc_normalized", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(278, _P11, "d10_nfc_zh_text", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(279, _P11, "d10_confusable_fullwidth", "project_risk_distribution",
                   injection=True, injection_blocked=False),
        _owned_row(280, _P11, "d10_confusable_homoglyph", "project_risk_distribution",
                   injection=True, injection_blocked=False),
        _owned_row(281, _P11, "d10_inject_pattern_rule_token",
                   "project_risk_distribution", injection=True,
                   injection_blocked=False),
        _owned_row(282, _P11, "d10_rehash_envelope", "project_risk_distribution",
                   rehash=True),
        _owned_row(283, _P11, "d10_rehash_query", "project_risk_distribution",
                   rehash=True),
        _owned_row(284, _P11, "d10_rehash_projection", "project_risk_distribution",
                   rehash=True),
        _owned_row(285, _P11, "d10_duplicate_id_rejected", "project_risk_distribution",
                   dup_member_ref=True),
        _owned_row(286, _P11, "d10_duplicate_locator", "project_risk_distribution",
                   dup_locator=True),
        _owned_row(287, _P11, "d10_nan_rejected", "project_risk_distribution",
                   den_value=-1),
        _owned_row(288, _P11, "d10_id_reuse_across_revisions",
                   "project_risk_distribution", dup_revision=True),
        _owned_row(289, _P11, "d10_id_replay_same_content",
                   "project_risk_distribution", hit="hit", ce_declared=1,
                   ce_matched=0, change=_REPLAY_CHANGE),
        _owned_row(290, _P11, "d10_order_permutation", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, change=_REPLAY_CHANGE),
        _owned_row(291, _P11, "d10_ref_prefix_invariant", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0, change=_REPLAY_CHANGE),
        _owned_row(292, _P11, "d10_canonical_byte_stable", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(293, _P11, "d10_key_exactness", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(294, _P11, "d10_bijection_bijective", "project_risk_distribution",
                   hit="hit", ce_declared=1, ce_matched=0),
        _owned_row(295, _P11, "d10_contract_hash_mismatch", "project_risk_distribution",
                   envelope_ok=False),
        _owned_row(296, _P11, "d10_authority_unresolved", "project_risk_distribution",
                   design_applicable="unresolved"),
    ]
    return rows


# p12: anti-overfit (16) - identical substantive facts; surface variants only
_P12 = "p12_anti_overfit"
_ANTI_BASE_NAMES = ("project_rename", "site_rename", "subject_rename",
                    "table_field_rename", "input_order_shuffle",
                    "version_field_change", "zh_label_change",
                    "ref_prefix_change")


def _build_p12_rows() -> list[dict[str, Any]]:
    rows = []
    for n in range(8):
        for v in (1, 2):
            idx = 297 + n * 2 + (v - 1)
            rows.append(_owned_row(
                idx, _P12, f"d10_anti_overfit_{_ANTI_BASE_NAMES[n]}_v{v}",
                "project_risk_distribution", hit="hit", ce_declared=1,
                ce_matched=0))
    return rows


ORACLE_CASES: list[dict[str, Any]] = (
    _build_p01_rows() + _build_p02_rows() + _build_p03_rows()
    + _build_p04_rows() + _build_p05_rows() + _build_p06_rows()
    + _build_p07_rows() + _build_p08_rows() + _build_p09_rows()
    + _build_p10_rows() + _build_p11_rows() + _build_p12_rows()
)

# ---------------------------------------------------------------------------
# Hydration: spec row -> normalized fact dict (f). Every value below is a pure
# function of the row; the catalog-side typed_input carries the same facts.
# ---------------------------------------------------------------------------
FACT_DEFAULTS: dict[str, Any] = {
    "es_state": "admitted", "gate_kind": None, "gate_reasons": [],
    "legal_match": True, "scope_eq": "exact_match", "envelope_ok": True,
    "identity_ok": True, "cov": {}, "den_kind": "treated_subjects",
    "den_value": 126, "den_state": "closed_positive", "den_excl": [],
    "den_tamper": False, "seg_tamper": False, "seg_overlap": False,
    "pop_present": True, "opp": None, "num_subject": 7, "num_event": 9,
    "num_site": 3, "individual": 7, "pattern": 0, "hit": "hit",
    "sources": ["typed_member"], "ce_declared": 1, "ce_matched": 0,
    "comp_state": "ready", "pair_state": "ready", "comp_reasons": [],
    "eligible_sites": 3, "required_sites": 3, "site_activation": "active",
    "origin_decision": None, "origin_plane_duplicate": False,
    "safety_missing": None, "efficacy_missing": None,
    "treatment_role_required": False, "assignment_present": None,
    "model_role": None, "model_ensemble": None, "change": None,
    "vis_hidden_members": 0, "vis_hidden_sites": 0, "rate_state": "permitted",
    "blind_status": "blinded",
    "vis_algebra_ok": True, "hidden_omission": False, "dl_violation": False,
    "blind_inference": False, "vis_hidden_dropped": False,
    "vis_hidden_counts_bad": False, "dl_n": 0, "locator_missing": False,
    "q_decision": "project_delta_present", "q_uncovered": 7, "q_fanout": 100,
    "q_unlistable": False, "q_pd": "not_pd", "q_covered": 0,
    "q_ids_mismatch": False, "q_duplicate": False,
    "injection": False, "injection_blocked": False, "rehash": False,
    "hotspot": False, "hotspot_hidden": False,
    "count_layers": ["individual_risk"], "small": False, "limited": False,
    "limited_reason": None, "design_applicable": "applicable",
    "estimate": None, "member_scope_bad": False, "member_scope_kind": None,
    "dup_member_ref": False,
    "dup_locator": False, "dup_revision": False, "desc_in_numerator": False,
    "excluded_in_numerator": False, "member_producer_d06": False,
    # typed-input semantic audit flags (recomputation-based; all fixture data
    # is internally consistent so these stay False on the oracle side; the
    # independent verifier derives them from typed_input).
    "legal_row_hash_bad": False, "legal_row_sd_mismatch": False,
    "scope_hash_bad": False, "mode_hash_bad": False,
    "source_hash_bad": False, "source_authority_bad": False,
    "origin_hash_bad": False,
    "origin_refs_external": False, "den_refs_bad": False,
    "seg_recompute_bad": False, "ledger_bad": False, "cutoff_order_bad": False,
    "r2_prior_bad": False, "dl_eligible_bad": False, "dl_target_bad": False,
    "vis_decision_hash_bad": False, "q_covered_bad": False,
    "q_identity_bad": False, "q_content_bad": False, "assignment_bad": False,
    "desc_hash_bad": False, "model_hash_bad": False, "audience_scan_hit": False,
    "wins": 1, "unique_windows": None, "segments": 0, "den_excl": [],
}
IDENTITY_EXCLUDED_KEYS = frozenset({
    "idx", "case_id", "oracle_case_id", "fixture_id", "partition", "family",
    # builder-only / non-typed-derived bookkeeping (verifier cannot derive)
    "required_sites", "vis_hidden_counts_bad", "site_ref_for_members",
    # accepted-authority lookups (fixed reference, not evaluation content)
    "authority_entry", "surface_alt",
    # typed-input semantic audit flags (validation byproducts, not evaluation
    # content; the verifier derives them by recomputation)
    "legal_row_hash_bad", "legal_row_sd_mismatch", "scope_hash_bad",
    "mode_hash_bad", "source_hash_bad", "origin_hash_bad",
    "origin_refs_external", "source_authority_bad",
    "den_refs_bad", "seg_recompute_bad", "ledger_bad", "cutoff_order_bad",
    "r2_prior_bad", "dl_eligible_bad", "dl_target_bad",
    "vis_decision_hash_bad", "q_covered_bad", "q_identity_bad",
    "q_content_bad", "assignment_bad", "desc_hash_bad", "model_hash_bad",
    "audience_scan_hit",
})

# Accepted fixture authority (fixed reference; identity-bearing values are
# rebuilt from it, never from case-id conventions).
_AUTHORITY_INDEX: dict[str, dict[str, Any]] = {}
_AUTHORITY_HASH = ""


def _load_authority() -> tuple[dict[str, dict[str, Any]], str]:
    if not AUTHORITY.exists():
        raise SystemExit(f"fixture authority registry missing at {AUTHORITY}")
    data = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    index = {e["case_id"]: e for e in data["entries"]}
    if len(index) != data["case_count"]:
        raise SystemExit("fixture authority entry coverage mismatch")
    return index, data["content_hash"]


def _hydrate(spec: dict[str, Any]) -> dict[str, Any]:
    """Fill fields derived by documented synthetic naming conventions so the
    embedded table stays compact. Every value is a pure function of idx."""
    out: dict[str, Any] = dict(FACT_DEFAULTS)
    out.update(spec)
    idx = spec["idx"]
    kind = spec["kind"]
    out["required_domains"] = DEFAULT_REQUIRED_DOMAINS[kind]
    if out["unique_windows"] is None:
        out["unique_windows"] = 2 if out.get("wins", 1) >= 2 else 1
    cov: dict[str, list[str]] = {}
    overrides = spec.get("cov", {})
    for domain in ("D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09"):
        cov[domain] = list(overrides.get(domain, ("covered", "complete")))
    out["cov"] = cov
    if out["den_kind"] in ("subject_time", "exposure_time") and \
            out.get("segments", 0):
        # time-kind denominator value = sum of normalized segment durations
        out["den_value"] = out["segments"] * 30
    out["seg_recompute_bad"] = bool(out.get("seg_tamper", False))
    out["safety_present"] = "safety_missing" in spec
    out["safety_missing"] = list(spec.get("safety_missing", []))
    out["efficacy_present"] = "efficacy_missing" in spec
    out["efficacy_missing"] = list(spec.get("efficacy_missing", []))
    out["surface_alt"] = bool(spec.get("surface_alt", False))
    out["project_ref"] = PROJECT_REF
    cid = f"D10-CASE-{idx:03d}"
    entry = _AUTHORITY_INDEX.get(cid)
    if entry is None:
        raise SystemExit(f"oracle case {cid} missing fixture authority entry")
    out["authority_entry"] = entry
    out["project_ref"] = entry["project_ref"]
    # The four external-pair rows intentionally submit an extra pair.  Keep
    # that submitted attack visible to the source-authority semantic gate;
    # it is not accepted authority and must not collapse into an envelope
    # admission gate.
    out["source_authority_bad"] = bool(out.get("envelope_ok") is False)
    # Query identity and coverage facts are rebuilt from the fixed authority
    # payload, including explicit negative fixtures with external/truncated
    # submitted refs.  The row's compact q_uncovered value is only a fixture
    # hint and must not outrank the accepted typed object.
    authority_query = entry["query"]
    out["q_covered"] = len(authority_query["covered_member_refs"])
    out["q_uncovered"] = len(authority_query["uncovered_member_refs"])
    out["gap_present"] = out.get("opp") is not None
    if out["assignment_present"] is None:
        out["assignment_present"] = False
    out["replay"] = bool(
        out["change"] and out["change"].get("basis") == "full"
        and out["change"].get("cutoff_state") == "same_window"
        and out["change"].get("claimed_cutoff") is None)
    unit_members = (out["individual"] + out["pattern"]
                    + (1 if out.get("opp") else 0)
                    + (1 if out["safety_present"] else 0)
                    + (1 if out["efficacy_present"] else 0)
                    + (1 if out.get("desc_in_numerator") else 0))
    unit_member_refs = sorted({m["member_ref"] for m in entry["members"]})
    covered_refs = set(authority_query["covered_member_refs"])
    uncovered_refs = set(authority_query["uncovered_member_refs"])
    out["q_set_violation"] = bool(
        covered_refs | uncovered_refs != set(unit_member_refs)
        or covered_refs & uncovered_refs)
    # count_mixed: derived from the layers list.
    layers = out["count_layers"]
    out["count_mixed"] = len(set(layers)) > 1
    if out.get("change") is not None:
        change = dict(CHANGE_DEFAULTS)
        change.update(out["change"])
        out["change"] = change
    out.pop("descendants", None)
    out["excluded_sites"] = int(spec.get("excluded_sites", 0))
    if out.get("opp") is not None:
        out["opp"] = {key: out["opp"][key] for key in
                      ("expected", "observed", "complete", "provenance")}
    if out.get("vis_hidden_counts_bad"):
        out["vis_hidden_members"] = int(out["vis_hidden_members"]) + 1
    return out


def _content_sha(label: str) -> str:
    return sha256_text(f"d10-content-v1:{label}")


def _member_refs(f: dict[str, Any]) -> list[str]:
    idx = f["idx"]
    refs = [f"SYN-D10-RISK-{idx:03d}-{m:02d}"
            for m in range(1, f["individual"] + 1)]
    refs += [f"SYN-D10-PAT-{idx:03d}-{m:02d}"
             for m in range(1, f["pattern"] + 1)]
    if f.get("opp"):
        refs.append(f"SYN-D10-GAP-{idx:03d}-01")
    if f.get("safety_present"):
        refs.append(f"SYN-D10-SAFE-{idx:03d}-01")
    if f.get("efficacy_present"):
        refs.append(f"SYN-D10-EFF-{idx:03d}-01")
    if f.get("desc_in_numerator"):
        refs.append(f"SYN-D10-DESC-{idx:03d}-01")
    if f.get("dup_member_ref") and refs:
        refs.append(refs[0])
    return refs


def _unit_member_count(f: dict[str, Any]) -> int:
    return (f["individual"] + f["pattern"]
            + (1 if f.get("opp") else 0)
            + (1 if f.get("safety_present") else 0)
            + (1 if f.get("efficacy_present") else 0))


# ---------------------------------------------------------------------------
# Decision engine: disposition/gate from explicit spec facts + contract rules
# ---------------------------------------------------------------------------
def _derive_change(ch: dict[str, Any] | None) -> tuple[str, str | None, str, bool]:
    """Return (clinical_change_kind, primary_change_cause, lineage_relation,
    analysis_only) from the typed change facts (contract section 14)."""
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
            and ch.get("cutoff_predicate")
            and ch.get("cutoff_policy_equal") and ch.get("prior")):
        lineage = "continued_from_cutoff_advance"
    else:
        lineage = "continued_from_data_revision"
    return ch.get("data_kind") or "continued", "data", lineage, False


def derive_disposition(f: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Return (disposition_or_gate, primary_reason, extra) from contract
    sections 2.1/3.3/6/7/8/9/10/13/14. extra carries leaf-level facts."""
    token, owner = f["token"], f["owner"]
    kind = f["kind"]
    # D1 routing (contract section 2.1 legal rows)
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
    # owner == evaluate_and_own
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
        gate_kind = f["gate_kind"]
        if gate_kind == "comparison_set_gate":
            return "comparison_set_gate", "control_plane_comparison_gate", \
                {"zero_unit": True}
        return "window_pair_gate", "control_plane_window_pair_gate", \
            {"zero_unit": True}

    ch = f["change"]
    derived_change = _derive_change(ch) if ch else None
    derived_kind, derived_cause, derived_lineage, analysis_only = \
        (derived_change if derived_change else
         ("initial_current", None, "initial_full_snapshot", False))

    # D3 integrity group (fail closed; zero medical output)
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
    if ch and ch.get("r2_lineage") and derived_change and \
            ch.get("r2_lineage") != derived_lineage:
        return "integrity_gate", "r2_wrong_lineage", {"zero_unit": True}
    if ch and ch.get("claimed_kind") and derived_change and \
            ch["claimed_kind"] != derived_kind:
        return "integrity_gate", "fake_change_claim", {"zero_unit": True}
    if ch and ch.get("claimed_cause") and derived_change and \
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
    if f["origin_refs_external"] or f["origin_hash_bad"]:
        return "integrity_gate", "measure_origin_binding_tamper", {"zero_unit": True}
    if f["member_producer_d06"]:
        return "integrity_gate", "d06_efficacy_not_d09_pattern", {"zero_unit": True}
    if f["excluded_in_numerator"]:
        return "integrity_gate", "excluded_member_counted", {"zero_unit": True}
    if f["dup_member_ref"]:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f["dup_locator"]:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f["dup_revision"]:
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
    if f["dl_violation"] or f["dl_eligible_bad"]:
        return "integrity_gate", "deep_link_eligible_violation", {"zero_unit": True}
    if f["dl_target_bad"]:
        return "integrity_gate", "deep_link_target_tamper", {"zero_unit": True}
    if not f["vis_algebra_ok"] or f["vis_decision_hash_bad"]:
        return "integrity_gate", "visibility_algebra", {"zero_unit": True}
    if f["blind_inference"]:
        return "integrity_gate", "blind_treatment_inference", {"zero_unit": True}
    if not f["injection_blocked"] and \
            (f["injection"] or f["audience_scan_hit"]):
        return "integrity_gate", "audience_injection_blocked", {"zero_unit": True}
    if f["hotspot_hidden"]:
        return "integrity_gate", "hotspot_hidden", {"zero_unit": True}
    if f["q_set_violation"] or f["q_covered_bad"]:
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

    # D4 completeness (contract section 9.1 precedence)
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

    # D5 gates (contract section 3.3)
    if kind == "cross_site_pattern" and f["comp_state"] != "ready":
        return "comparison_set_gate", f"comparison_{f['comp_state']}", \
            {"zero_unit": True}
    if kind in ("project_time_trend", "project_safety_trend",
                "project_efficacy_trend") and f["pair_state"] != "ready":
        return "window_pair_gate", f"window_pair_{f['pair_state']}", \
            {"zero_unit": True}

    # D6 evaluation
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


def _estimate_kind(f: dict[str, Any]) -> str:
    if f.get("estimate"):
        return f["estimate"]
    return DEN_KIND_ESTIMATE.get(f["den_kind"], "proportion")


def _query_count(f: dict[str, Any], disposition: str) -> int:
    if disposition != "positive":
        return 0
    if f["q_decision"] != "project_delta_present":
        return 0
    if f["q_uncovered"] <= 0:
        return 0
    if f["q_unlistable"]:
        return 0
    if f["q_uncovered"] > f["q_fanout"]:
        return 0
    if (f["injection"] or f["audience_scan_hit"]) and f["injection_blocked"]:
        return 0
    return 1


# ---------------------------------------------------------------------------
# Leaf builders
# ---------------------------------------------------------------------------
def _gate_leaf_kind(disposition_or_gate: str) -> str:
    return {
        "comparison_set_gate": "control_plane_comparison_gate",
        "window_pair_gate": "control_plane_window_pair_gate",
        "global_gate": "global_integrity_gate",
        "integrity_gate": "global_integrity_gate",
        "routing_gate": "routing_gate",
        "handoff_gate": "handoff_gate",
    }[disposition_or_gate]


def build_expected_leaf_set(f: dict[str, Any], disposition_or_gate: str,
                            reason: str, extra: dict[str, Any]) -> list[dict[str, Any]]:
    idx = f["idx"]
    if extra.get("zero_unit") or disposition_or_gate in GATE_DISPOSITIONS:
        leaf: dict[str, Any] = {key: None for key in LEAF_KEYS}
        leaf["leaf_kind"] = _gate_leaf_kind(disposition_or_gate)
        leaf["signal_kind"] = f["kind"]
        leaf["gate_kind"] = disposition_or_gate
        leaf["reason_codes"] = sorted(set(f["gate_reasons"] or [reason]))
        leaf["expected_disposition"] = None
        for key in ("numerator_member_count", "numerator_individual_risk_count",
                    "numerator_affected_subject_count",
                    "numerator_event_or_outcome_count",
                    "numerator_center_pattern_count",
                    "numerator_affected_site_count", "project_signal_count",
                    "clue_count", "query_count", "risk_handoff_count",
                    "hidden_member_count", "hidden_site_count",
                    "deep_link_target_count", "counterevidence_rule_matches"):
            leaf[key] = 0
        leaf["denominator_value"] = f["den_value"] if f["den_value"] >= 0 else 0
        leaf["member_expansion_state"] = "not_applicable"
        leaf["audience_injection_blocked"] = bool(f["injection"])
        return [leaf]

    derived_change = _derive_change(f["change"]) if f["change"] else \
        ("initial_current", None, "initial_full_snapshot", False)
    derived_kind, derived_cause, derived_lineage, analysis_only = derived_change
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
        for key in ("numerator_member_count", "numerator_individual_risk_count",
                    "numerator_affected_subject_count",
                    "numerator_event_or_outcome_count",
                    "numerator_center_pattern_count",
                    "numerator_affected_site_count", "project_signal_count",
                    "clue_count", "query_count", "risk_handoff_count",
                    "hidden_member_count", "hidden_site_count",
                    "deep_link_target_count", "counterevidence_rule_matches"):
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
        for key in ("numerator_member_count", "numerator_individual_risk_count",
                    "numerator_affected_subject_count",
                    "numerator_event_or_outcome_count",
                    "numerator_center_pattern_count",
                    "numerator_affected_site_count", "project_signal_count",
                    "clue_count", "query_count", "risk_handoff_count",
                    "hidden_member_count", "hidden_site_count",
                    "deep_link_target_count", "counterevidence_rule_matches"):
            analysis[key] = 0
        analysis["denominator_value"] = f["den_value"] if f["den_value"] >= 0 else 0
        analysis["member_expansion_state"] = "not_applicable"
        analysis["audience_injection_blocked"] = bool(f["injection"])
        leaves.append(analysis)
    return leaves


def _stable_core_ref(f: dict[str, Any]) -> str:
    entry = f["authority_entry"]
    first_window = entry["analysis_windows"][0]["analysis_window_stable_id"]
    return "|".join([entry["project_ref"],
                     entry["signal_definition"]["signal_definition_id"],
                     first_window,
                     entry["stratum"]["stratum_contract_id"],
                     entry["stratum"]["stratum_key"],
                     entry["comparison_reference_stable_id"]])


def build_source_leaf_set(f: dict[str, Any], disposition_or_gate: str) -> list[dict[str, Any]]:
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
    """Derived from typed facts + contract rules; never from catalog labels."""
    out: list[dict[str, Any]] = []
    if disposition_or_gate in GATE_DISPOSITIONS:
        out.append({"leaf_kind": "medical_unit", "expected_disposition": None,
                    "gate_kind": None, "change_kind": None,
                    "reason_code": f"zero_medical_output:{reason}"})
        return out
    ch = f["change"]
    derived = _derive_change(ch) if ch else None
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
            source in ("typed_member", "verified_measure") for source in f["sources"]):
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


def build_expectation(spec: dict[str, Any]) -> dict[str, Any]:
    f = _hydrate(spec)
    disposition_or_gate, reason, extra = derive_disposition(f)
    expected_leaf_set = build_expected_leaf_set(f, disposition_or_gate, reason,
                                                extra)
    expected_trace_leaf_set = build_trace_leaf_set(f, disposition_or_gate, reason)
    expected_source_leaf_set = build_source_leaf_set(f, disposition_or_gate)
    forbidden_leaf_set = build_forbidden_leaf_set(f, disposition_or_gate, reason)
    expectation: dict[str, Any] = {
        "case_id": spec["case_id"],
        "oracle_case_id": spec["oracle_case_id"],
        "fixture_id": spec["fixture_id"],
        "expected_leaf_set": expected_leaf_set,
        "expected_trace_leaf_set": expected_trace_leaf_set,
        "expected_source_leaf_set": expected_source_leaf_set,
        "expected_disposition_or_gate": disposition_or_gate,
        "forbidden_leaf_set": forbidden_leaf_set,
        "oracle_hash": "",
    }
    core = {key: item for key, item in expectation.items()
            if key != "oracle_hash"}
    expectation["oracle_hash"] = content_hash(core, "oracle_hash")
    return expectation


# ---------------------------------------------------------------------------
# Assembly / validation / CLI
# ---------------------------------------------------------------------------
def assemble_oracle() -> dict[str, Any]:
    global _AUTHORITY_INDEX, _AUTHORITY_HASH
    _AUTHORITY_INDEX, _AUTHORITY_HASH = _load_authority()
    expectations = [build_expectation(spec) for spec in ORACLE_CASES]
    oracle: dict[str, Any] = {
        "artifact_kind": "independent_expected_outcome_oracle",
        "oracle_id": ORACLE_ID,
        "schema_version": SCHEMA_VERSION,
        "contract_semantic_hash": CONTRACT_SEMANTIC_HASH,
        "case_count": len(expectations),
        "ordered_expectations": expectations,
        "fixture_authority_registry_hash": _AUTHORITY_HASH,
        "content_hash": "",
    }
    oracle["content_hash"] = content_hash(oracle, "content_hash")
    return oracle


def validate_oracle(oracle: dict[str, Any]) -> None:
    if sorted(oracle.keys()) != sorted(ORACLE_TOP_KEYS):
        raise SystemExit(f"oracle top-level key mismatch: {sorted(oracle.keys())}")
    if oracle["oracle_id"] != ORACLE_ID:
        raise SystemExit("oracle_id mismatch")
    if oracle["case_count"] != len(ORACLE_CASES):
        raise SystemExit("case_count vs spec table mismatch")
    seen: set[str] = set()
    for entry in oracle["ordered_expectations"]:
        if sorted(entry.keys()) != sorted(ORDERED_EXPECTATION_KEYS):
            raise SystemExit(f"expectation key mismatch for {entry.get('case_id')}")
        if entry["case_id"] in seen:
            raise SystemExit(f"duplicate case_id {entry['case_id']}")
        seen.add(entry["case_id"])
        if entry["expected_disposition_or_gate"] not in \
                EXPECTED_DISPOSITION_OR_GATE:
            raise SystemExit(f"bad disposition {entry['case_id']}: "
                             f"{entry['expected_disposition_or_gate']}")
        for leaf in entry["expected_leaf_set"]:
            if sorted(leaf.keys()) != sorted(LEAF_KEYS):
                raise SystemExit(f"leaf key mismatch {entry['case_id']}")
            if leaf["leaf_kind"] not in LEAF_KINDS:
                raise SystemExit(f"bad leaf_kind {entry['case_id']}: "
                                 f"{leaf['leaf_kind']}")
        for leaf in entry["expected_trace_leaf_set"]:
            if sorted(leaf.keys()) != sorted(TRACE_LEAF_KEYS):
                raise SystemExit(f"trace leaf key mismatch {entry['case_id']}")
        for leaf in entry["expected_source_leaf_set"]:
            if sorted(leaf.keys()) != sorted(SOURCE_LEAF_KEYS):
                raise SystemExit(f"source leaf key mismatch {entry['case_id']}")
        for leaf in entry["forbidden_leaf_set"]:
            if sorted(leaf.keys()) != sorted(FORBIDDEN_LEAF_KEYS):
                raise SystemExit(f"forbidden leaf key mismatch {entry['case_id']}")
        core = {key: item for key, item in entry.items() if key != "oracle_hash"}
        if entry["oracle_hash"] != content_hash(core, "oracle_hash"):
            raise SystemExit(f"oracle_hash mismatch {entry['case_id']}")
    if len(seen) != oracle["case_count"]:
        raise SystemExit("case_id coverage mismatch")
    if oracle["content_hash"] != content_hash(oracle, "content_hash"):
        raise SystemExit("oracle content hash mismatch")
    if not sha256_hex(oracle["content_hash"]):
        raise SystemExit("oracle content hash malformed")
    if canonical_json(oracle) != canonical_json(json.loads(canonical_json(oracle))):
        raise SystemExit("oracle JSON not canonical")


def validate_oracle_authority() -> None:
    """The oracle's embedded decisive facts must equal the fixed fixture
    authority entry for every case (authority conformance, fail closed)."""
    for spec in ORACLE_CASES:
        f = _hydrate(spec)
        entry = f["authority_entry"]
        cid = f"case_id"
        def check(label: str, expected: Any, got: Any) -> None:
            if expected != got:
                raise SystemExit(
                    f"oracle authority mismatch {entry['case_id']} {label}: "
                    f"authority={expected!r} oracle={got!r}")
        sd = entry["signal_definition"]
        check("signal_kind", sd["signal_kind"], f["kind"])
        check("clinical_claim_token", sd["clinical_claim_token"], f["token"])
        check("d10_action", sd["d10_action"], f["owner"])
        es = entry["expected_set"]
        check("expected_set_state", es["expected_set_state"], f["es_state"])
        if es["admission_gate_kind"] is not None:
            check("admission_gate_kind", es["admission_gate_kind"],
                  f["gate_kind"])
            check("admission_gate_reasons", es["admission_gate_reasons"],
                  f["gate_reasons"])
        den = entry["denominator"]
        check("denominator_kind", den["denominator_kind"], f["den_kind"])
        check("denominator_value", den["denominator_value"], f["den_value"])
        check("denominator_state", den["denominator_state"], f["den_state"])
        ledger = entry["numerator_ledger"]
        check("individual_risk_count", ledger["individual_risk_count"],
              f["individual"])
        check("center_pattern_count", ledger["center_pattern_count"],
              f["pattern"])
        check("affected_subject_count", ledger["affected_subject_count"],
              f["num_subject"])
        check("event_or_outcome_count", ledger["event_or_outcome_count"],
              f["num_event"])
        check("affected_site_count", ledger["affected_site_count"],
              f["num_site"])
        vis = entry["visibility"]
        check("blind_status", vis["blind_status"], f["blind_status"])
        check("hidden_member_count", vis["hidden_member_count"],
              f["vis_hidden_members"])
        check("hidden_site_count", vis["hidden_site_count"],
              f["vis_hidden_sites"])
        check("rate_projection_state", vis["rate_projection_state"],
              f["rate_state"])
        q = entry["query"]
        check("query.decision", q["decision"], f["q_decision"])
        check("query.max_query_member_fanout", q["max_query_member_fanout"],
              f["q_fanout"])
        check("query.pd_wording_state", q["pd_wording_state"], f["q_pd"])
        check("query.member_unlistable", q["member_unlistable"],
              f["q_unlistable"])
        me = entry["model_evidence"]
        if me is None:
            check("model_evidence", None, f["model_role"])
        else:
            check("model_evidence.role", me["role"], f["model_role"])
            check("model_evidence.ensemble_size", me["ensemble_size"],
                  f["model_ensemble"])
        mo = entry["measure_origin"]
        if mo is None:
            check("measure_origin", None, f["origin_decision"])
        else:
            check("measure_origin.origin_decision", mo["origin_decision"],
                  f["origin_decision"])
        treatment = entry["treatment"]
        check("treatment.treatment_role_required",
              treatment["treatment_role_required"],
              f["treatment_role_required"])
        check("treatment.assignment_present",
              treatment["assignment_identity_ref"] is not None,
              bool(f["assignment_present"]))
        check("analysis_windows count", len(entry["analysis_windows"]),
              f["wins"])
        check("design_applicable_state",
              entry["mode_contract"]["design_applicable_state"],
              f["design_applicable"])


def render(verbose: bool = True) -> dict[str, Any]:
    def log(message: str) -> None:
        if verbose:
            print(message)

    validate_contract()
    oracle = assemble_oracle()
    validate_oracle(oracle)
    validate_oracle_authority()
    payload = canonical_json(oracle).encode("utf-8")
    ORACLE.write_bytes(payload)
    log(f"wrote {ORACLE} ({len(payload)} bytes, sha256 {oracle['content_hash']})")
    return oracle


def check(verbose: bool = True) -> int:
    def log(message: str) -> None:
        if verbose:
            print(message)

    try:
        validate_contract()
        first = assemble_oracle()
        validate_oracle(first)
        second = assemble_oracle()
        validate_oracle(second)
        a_bytes = canonical_json(first).encode("utf-8")
        b_bytes = canonical_json(second).encode("utf-8")
        if a_bytes != b_bytes:
            log("FAIL: two fresh generations are NOT byte-identical")
            return 1
        log("OK: two fresh generations are byte-identical")
        log(f"    sha256 {first['content_hash']}")
        if not ORACLE.exists():
            log(f"FAIL: oracle artifact missing at {ORACLE}")
            return 1
        on_disk = ORACLE.read_bytes()
        if on_disk != a_bytes:
            log("FAIL: on-disk oracle bytes differ from a fresh generation")
            return 1
        log("OK: on-disk oracle matches a fresh generation")
        loaded = json.loads(on_disk.decode("utf-8"))
        validate_oracle(loaded)
        log("OK: on-disk oracle validates (schema, closed enums, canonical, hash)")
        return 0
    except SystemExit as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="D10 expected-outcome oracle generator")
    parser.add_argument("mode", nargs="?", default="check",
                        choices=("generate", "check"),
                        help="generate: write oracle artifact; check: verify determinism")
    args = parser.parse_args()
    if args.mode == "generate":
        render(verbose=True)
        return 0
    return check(verbose=True)


if __name__ == "__main__":
    sys.exit(main())
