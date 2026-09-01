#!/usr/bin/env python3
"""D10 fixture authority registry generator (finite code executor).

Builds the immutable, content-addressed fixture authority registry that pins,
per case, the DECISIVE accepted upstream authority the catalog/oracle/verifier
must conform to: admitted project/run/snapshot/cutoff, scope binding, legal
matrix row, source revisions + locators, envelope member sets (refs/kinds/
planes/subjects/sites/scope/locator states/priorities), D09 owner +
descendants, assignment + mapping, mode contract, windows, stratum,
comparison reference, analysis population, denominator + subjects, time
segments, visibility partition (evaluation/projectable/hidden/deep-link
eligible sets), Query members + policy, ModelEvidence refs + permitted leaf,
measure-origin refs, audience contract forbidden terms and the expected-set
state.

Independence contract (REVISE_D10_ARTIFACTS round 2):
  * This module NEVER reads the typed catalog, the oracle, the challenge
    registry, the quota manifest or any runtime code. All authority values
    come from the embedded explicit case table below (an independent copy of
    the frozen D10 case plan) plus documented synthetic naming conventions.
  * The authority registry is the FIXED reference: it is content-addressed
    (per-entry authority_hash + top-level content_hash), self-pinned via the
    stage-A generator pin, and bijective over all 312 case ids. It must NOT
    be recomputed from the tested objects; the catalog generator, the oracle
    generator and the independent verifier each conformance-check the tested
    artifacts against this registry and fail closed on any mismatch.
  * Standard library only; no network, no wall-clock, no randomness, no
    runtime/UI/service code.
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
AUTHORITY = ROOT / "reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"

CONTRACT_FILE_SHA256 = "c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95"
CONTRACT_SEMANTIC_HASH = CONTRACT_FILE_SHA256
AUTHORITY_ID = "medical-monitoring-r4-d10-fixture-authority-registry-v1"
SCHEMA_VERSION = "1.0.0"
REQUIRED_TOTAL = 312

_PIN_SENTINEL = "0" * 64
STAGE_A_GENERATOR_SHA256 = "71c91c7d61baf48fa028ec3c95d1ab402b72bae4482314c9030ffa22b74a5fa2"


def _generator_code_hash() -> str:
    text = Path(__file__).read_text(encoding="utf-8")
    return sha256_text(text.replace(STAGE_A_GENERATOR_SHA256, _PIN_SENTINEL))


# ---------------------------------------------------------------------------
# Closed enums (independent copy of the frozen contract vocabulary)
# ---------------------------------------------------------------------------
SIGNAL_KINDS = ("project_risk_distribution", "cross_site_pattern",
                "project_time_trend", "project_safety_trend",
                "project_efficacy_trend")
OWNER_ROUTES = ("evaluate_and_own", "consume_only", "handoff_only",
                "context_only", "routing_gate")
MEMBER_KINDS = ("individual_risk", "center_pattern", "accepted_gap",
                "safety_measure", "efficacy_measure", "denominator_member")
AGGREGATION_PLANES = ("individual", "site_pattern", "project_measure")
DENOMINATOR_KINDS = ("enrolled_subjects", "treated_subjects",
                     "safety_evaluable_subjects", "efficacy_evaluable_subjects",
                     "subject_time", "exposure_time",
                     "expected_assessment_opportunities",
                     "analysis_population_members")
DENOMINATOR_STATES = ("closed_positive", "closed_zero", "unclosed")
MEMBER_SCOPE_STATES = ("in_scope", "wrong_project", "wrong_site",
                       "wrong_subject", "unresolvable")
LOCATOR_STATES = ("locatable", "missing", "unresolvable")
PRIORITIES = ("high", "medium", "low")
BLIND_STATUSES = ("blinded", "unblinded_authorized")
RATE_PROJECTION_STATES = ("permitted", "suppressed", "qualified")
QUERY_REDUNDANCY_DECISIONS = ("project_delta_present",
                              "fully_covered_by_member_queries",
                              "members_unlistable", "not_applicable")
PD_WORDING_STATES = ("not_pd", "verify_whether_pd")
ORIGIN_DECISIONS = ("all_verified_same_origin", "all_distinct",
                    "mixed_verified_and_distinct", "ambiguous", "wrong_scope",
                    "not_evaluable")
DEEP_LINK_TARGET_KINDS = ("member", "site", "subject_site_pair")
MODEL_EVIDENCE_ROLES = ("candidate_explanation", "counterevidence_suggestion")
EXPECTED_SET_STATES = ("admitted", "global_admission_failed",
                       "routed_consume_only", "routing_gate_unresolved",
                       "control_plane_gate")
DESIGN_APPLICABLE_STATES = ("applicable", "not_applicable", "unresolved")
WINDOW_KINDS = ("calendar_interval", "study_day_interval", "exposure_interval")
WINDOW_STATES = ("closed", "open")
STRATUM_STATES = ("closed", "open", "empty")
STRATUM_ADMISSIONS = ("admitted", "rejected_empty", "fanout_rejected", "not_required")
SITE_ACTIVATION_STATES = ("active", "late")
SCOPE_EQUALITY_DECISIONS = ("exact_match", "mismatch")
COMPARISON_STATES = ("insufficient_sites", "incomparable_sites", "ready")
PAIR_STATES = ("insufficient_windows", "incomparable_windows", "ready")
HANDOFF_ACTIONS = ("create", "continue", "update", "propose_close",
                   "reopen", "supersede")
CUTOFF_DECISION_STATES = ("strict_advance", "same_window", "policy_changed",
                          "not_evaluable")
LINEAGE_RELATIONS = ("initial_full_snapshot", "continued_from_data_revision",
                     "continued_from_cutoff_advance",
                     "superseded_by_knowledge_change",
                     "superseded_by_rule_or_mapping_change",
                     "superseded_by_method_or_population_change",
                     "superseded_by_mode_change",
                     "superseded_by_visibility_change",
                     "coverage_regressed", "not_comparable", "none")
CHANGE_CAUSES = ("data", "denominator", "coverage", "knowledge", "rule",
                 "mapping", "model", "method", "population", "visibility",
                 "mode", "mixed")
DATA_CHANGE_KINDS = ("new", "continued", "upgraded", "downgraded",
                     "resolved", "reopened")

PARTITIONS = (
    "p01_signal_kind_disposition", "p02_owner_routing_zero_medical",
    "p03_identity_scope_duplicate", "p04_numerator_denominator_time",
    "p05_cross_site_comparability", "p06_safety_trend",
    "p07_efficacy_trend", "p08_change_cause_lineage", "p09_query_deeplink",
    "p10_visibility_blindness", "p11_unicode_tamper_bijection",
    "p12_anti_overfit",
)

# ---------------------------------------------------------------------------
# Frozen schema: exact key sets of the authority registry
# ---------------------------------------------------------------------------
AUTHORITY_TOP_KEYS = ["authority_id", "schema_version", "contract_semantic_hash",
                      "case_count", "generator_hash", "entries",
                      "bijection_audit", "content_hash"]
ENTRY_KEYS = [
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
SIGNAL_DEFINITION_KEYS = ["signal_definition_id", "signal_kind",
                          "clinical_claim_token", "d10_action",
                          "required_producer_domains"]
LEGAL_MATRIX_ROW_KEYS = ["row_id", "signal_kind", "clinical_claim_token",
                         "d10_action"]
SCOPE_BINDING_KEYS = ["scope_binding_id", "scope_type",
                      "scope_equality_decision"]
MODE_CONTRACT_KEYS = ["mode_contract_version", "mode_contract_content_hash",
                       "design_clause_ref", "design_applicable_state"]
EXPECTED_SET_KEYS = ["expected_set_state", "admission_gate_kind",
                     "admission_gate_reasons"]
WINDOW_KEYS = ["analysis_window_stable_id", "window_instance_id",
               "window_definition_id", "window_kind", "window_state",
               "cutoff_ref"]
STRATUM_KEYS = ["stratum_contract_id", "stratum_key", "stratum_state",
                "stratum_admission"]
ANALYSIS_POPULATION_KEYS = ["analysis_population_ref",
                            "analysis_population_contract_id"]
MEMBER_KEYS = ["member_ref", "member_kind", "aggregation_plane",
               "subject_stable_id", "site_stable_id", "member_scope_state",
               "locator_resolution_state", "monitoring_priority",
               "producer_domain", "locator_ref"]
NUMERATOR_LEDGER_KEYS = ["individual_risk_count", "center_pattern_count",
                         "affected_subject_count", "event_or_outcome_count",
                         "affected_site_count", "numerator_member_count"]
DENOMINATOR_KEYS = ["denominator_kind", "denominator_value",
                    "denominator_unit", "denominator_state",
                    "exclusion_reason_codes"]
TIME_SEGMENTS_KEYS = ["count", "set_hash"]
D09_PATTERN_KEYS = ["member_ref", "owner_domain", "descendant_refs"]
MEASURE_ORIGIN_KEYS = ["binding_id", "measure_ref", "origin_decision",
                       "verified_risk_refs", "distinct_risk_refs",
                       "ambiguous_risk_refs", "candidate_risk_refs",
                       "numerator_plane_state", "verified_ref_set_hash",
                       "distinct_ref_set_hash", "ambiguous_ref_set_hash",
                       "candidate_ref_set_hash", "pairwise_disjoint",
                       "source_provenance_hash"]
TREATMENT_KEYS = ["treatment_role_required", "authority_ref",
                  "assignment_identity_ref", "mapping_hash"]
VISIBILITY_KEYS = ["blind_status", "hidden_member_count", "hidden_site_count",
                   "rate_projection_state", "evaluation_member_set_hash",
                   "projectable_member_set_hash", "hidden_member_set_hash",
                   "deep_link_eligible_member_set_hash",
                   "evaluation_site_set_hash", "projectable_site_set_hash",
                   "hidden_site_set_hash",
                   "deep_link_eligible_site_set_hash",
                   "projectable_subject_site_pair_set_hash",
                   "deep_link_eligible_subject_site_pair_set_hash",
                   "projectable_subject_site_pairs",
                   "deep_link_eligible_subject_site_pairs",
                   "eligible_n", "visible_n", "hidden_set_omitted",
                   "deep_link_eligible_violation",
                   "treatment_inference_attempt"]
DEEP_LINK_KEYS = ["target_kind", "site_ref", "subject_ref",
                  "member_object_ref"]
QUERY_KEYS = ["decision", "covered_member_refs", "uncovered_member_refs",
              "member_query_content_identities", "unit_member_set_hash",
              "coverage_proof_hash", "covered_member_set_hash",
              "uncovered_member_set_hash", "union_member_set_hash",
              "disjoint", "max_query_member_fanout",
              "pd_wording_state", "member_unlistable"]
MODEL_EVIDENCE_KEYS = ["model_evidence_id", "role",
                       "evaluation_content_identity", "input_content_hash",
                       "source_revision_content_pairs", "source_refs",
                       "model_id", "model_version", "independent_context_hash",
                       "ensemble_id", "ensemble_size", "member_analysis_refs",
                       "permitted_leaf", "member_analysis_ref_set_hash",
                       "output_identity", "output_hash", "adjudication_state",
                       "model_binding_hash"]
AUDIENCE_CONTRACT_KEYS = ["forbidden_internal_terms"]
EVIDENCE_REF_KEYS = ["locator_id", "locator_kind", "source_file",
                     "row_or_cell_ref", "lineage_ref"]
CHANGE_AUTHORITY_KEYS = ["execution_basis", "comparison_state", "prior_present",
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
SOURCE_REVISION_KEYS = ["revision_id", "content_hash"]
BIJECTION_AUDIT_KEYS = ["row_count", "bijection_ok", "sorted_case_ids",
                        "duplicate_case_ids", "missing_case_ids"]

# ---------------------------------------------------------------------------
# Canonical JSON and hashing (same infrastructure conventions as the chain)
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
    raw = CONTRACT.read_bytes()
    if sha256_bytes(raw) != CONTRACT_FILE_SHA256:
        raise AuthorityError("contract", "sha_mismatch",
                             "contract file SHA-256 mismatch")
    semantic = sha256_text(normalize_contract(raw.decode("utf-8")))
    if semantic != CONTRACT_SEMANTIC_HASH:
        raise AuthorityError("contract", "semantic_hash_mismatch",
                             "contract semantic hash mismatch")
    return semantic


def sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


class AuthorityError(Exception):
    def __init__(self, stage: str, error_class: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.error_class = error_class


def expect_exact_keys(obj: Any, keys: list[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise AuthorityError("schema_parse", "schema_error",
                             f"{label} must be an object")
    if sorted(obj.keys()) != sorted(keys):
        raise AuthorityError("schema_parse", "schema_error",
                             f"{label} exact-key mismatch: "
                             f"got {sorted(obj.keys())}, want {sorted(keys)}")


def require_enum(value: Any, closed: tuple[str, ...], label: str) -> str:
    if value not in closed:
        raise AuthorityError("schema_parse", "schema_error",
                             f"{label} {value!r} not in closed set")
    return value


def _sorted_unique(values: list[str], label: str) -> list[str]:
    if len(set(values)) != len(values):
        raise AuthorityError("schema_parse", "schema_error",
                             f"{label} contains duplicates")
    return sorted(values)


# ---------------------------------------------------------------------------
# Deterministic id/ref conventions (the authority FIXES these as accepted
# upstream values; consumers must conform, never re-derive from case ids).
# ---------------------------------------------------------------------------
def _subject_ids(idx: int, count: int, *, offset: int = 0, site: int = 1) -> list[str]:
    return [f"SYN-D10-SUBJ-{idx:03d}-{site:02d}-{offset + m:02d}"
            for m in range(1, count + 1)]


def _site_ref(site: int) -> str:
    return f"SYN-D10-SITE-{site:03d}"


def _member_ids(idx: int, count: int, prefix: str) -> list[str]:
    return [f"SYN-D10-{prefix}-{idx:03d}-{m:02d}" for m in range(1, count + 1)]


def _content_sha(label: str) -> str:
    return sha256_text(f"d10-content-v1:{label}")


# ---------------------------------------------------------------------------
# Row table (independent copy of the frozen case plan; same vocabulary as the
# catalog spec table). Only decisive authority fields are honoured.
# ---------------------------------------------------------------------------
DEFAULT_REQUIRED_DOMAINS = {
    "project_risk_distribution": ["D01", "D02", "D03", "D04"],
    "cross_site_pattern": ["D09", "D01"],
    "project_time_trend": ["D09", "D10"],
    "project_safety_trend": ["D07", "D01"],
    "project_efficacy_trend": ["D06", "D01"],
}
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
ROW_DEFAULTS: dict[str, Any] = {
    "owner": "evaluate_and_own", "es_state": "admitted",
    "gate_kind": None, "gate_reasons": [], "scope_eq": "exact_match",
    "scope_type": "project", "legal_match": True, "envelope_ok": True,
    "identity_ok": True, "den_kind": "treated_subjects", "den_value": 126,
    "den_state": "closed_positive", "den_excl": [], "den_tamper": False,
    "segments": 0, "seg_tamper": False, "seg_overlap": False,
    "pop_present": True, "opp": None, "num_subject": 7, "num_event": 9,
    "num_site": 3, "individual": 7, "pattern": 0, "descendants": 0,
    "desc_in_numerator": False, "dup_member_ref": False,
    "dup_locator": False, "dup_revision": False,
    "member_scope_bad": False, "member_scope_kind": None,
    "locator_missing": False, "member_producer_d06": False,
    "excluded_in_numerator": False, "origin": None, "safety": None,
    "efficacy": None, "treatment_required": False, "assignment_present": False,
    "model": None, "change": None, "vis_hidden_members": 0,
    "vis_hidden_sites": 0, "rate_state": "permitted",
    "blind_status": "blinded", "vis_algebra_ok": True,
    "vis_hidden_omission": False, "vis_hidden_dropped": False,
    "vis_hidden_counts_bad": False, "dl_violation": False, "dl_n": 0,
    "dl_kinds": ["member"], "blind_inference": False,
    "q_decision": "project_delta_present", "q_uncovered": 7, "q_fanout": 100,
    "q_unlistable": False, "q_pd": "not_pd", "q_covered": 0,
    "q_ids_mismatch": False, "q_duplicate": False, "rehash": False,
    "hotspot": False, "hotspot_hidden": False, "design_applicable": "applicable",
    "wins": 1, "unique_windows": None, "comp_state": "ready",
    "pair_state": "ready", "comp_reasons": [], "eligible_sites": 3,
    "required_sites": 3, "excluded_sites": 0, "site_activation": "active",
    "mode_version_alt": False, "envelope_id_alt": False,
    "audience_id_alt": False,
}


def _row(idx: int, partition: str, family: str, kind: str, token: str,
         owner: str, **kw: Any) -> dict[str, Any]:
    return {"idx": idx, "partition": partition, "family": family,
            "kind": kind, "token": token, "owner": owner, **kw}


def _owned_row(idx: int, partition: str, family: str, kind: str,
               **kw: Any) -> dict[str, Any]:
    token = kw.pop("token", "d10_" + kind)
    return _row(idx, partition, family, kind, token, "evaluate_and_own", **kw)


_P01 = "p01_signal_kind_disposition"


def _build_p01_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    replay_change = {"basis": "full", "comparison_state": "initial_full",
                     "cutoff_state": "same_window", "cutoff_predicate": False,
                     "cutoff_policy_equal": True}
    for k, kind in enumerate(SIGNAL_KINDS):
        base = 1 + k * 12
        def make(idx: int, family: str, **kw: Any) -> dict[str, Any]:
            return _owned_row(idx, _P01, family, kind, **kw)
        rows.append(make(base, "d10_disposition_positive"))
        rows.append(make(base + 1, "d10_disposition_negative", hit="no_hit"))
        rows.append(make(base + 2, "d10_disposition_boundary",
                         small=True, num_subject=1, num_event=1, num_site=1,
                         individual=1))
        rows.append(make(base + 3, "d10_disposition_not_applicable",
                         design_applicable="not_applicable"))
        rows.append(make(base + 4, "d10_disposition_not_evaluable",
                         hit="no_hit"))
        rows.append(make(base + 5, "d10_counterevidence_explains",
                         ce_declared=2, ce_matched=2))
        rows.append(make(base + 6, "d10_false_positive_trap",
                         sources=["pvalue"]))
        rows.append(make(base + 7, "d10_false_negative_trap", hit="no_hit",
                         den_state="closed_zero", den_value=0))
        rows.append(make(base + 8, "d10_hidden_counted",
                         vis_hidden_members=2, rate_state="qualified"))
        rows.append(make(base + 9, "d10_replay_stable", change=replay_change))
        rows.append(make(base + 10, "d10_comparison_gate",
                         es_state="control_plane_gate",
                         gate_kind="comparison_set_gate",
                         gate_reasons=["comparison_insufficient_sites"],
                         comp_state="insufficient_sites", eligible_sites=2,
                         required_sites=3))
        rows.append(make(base + 11, "d10_window_pair_gate",
                         es_state="control_plane_gate",
                         gate_kind="window_pair_gate",
                         gate_reasons=["window_pair_insufficient_windows"],
                         wins=1, pair_state="insufficient_windows",
                         unique_windows=1))
    return rows


_P02 = "p02_owner_routing_zero_medical"


def _build_p02_rows() -> list[dict[str, Any]]:
    return [
        _row(61, _P02, "d10_consume_d09_plain", "cross_site_pattern",
             "d09_within_site_pattern", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"]),
        _row(62, _P02, "d10_consume_d09_descendants", "cross_site_pattern",
             "d09_within_site_pattern", "consume_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_consume_only"],
             pattern=1, descendants=2),
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
             gate_kind="routing_gate",
             gate_reasons=["legal_row_consume_only_ownable"]),
        _row(66, _P02, "d10_consume_d01_scope_mismatch",
             "project_risk_distribution", "d01_d08_individual_claim",
             "consume_only", es_state="routed_consume_only",
             gate_kind="routing_gate", gate_reasons=["token_consume_only"],
             scope_eq="mismatch"),
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
        _owned_row(74, _P02, "d10_unauthorized_d01",
                   "project_risk_distribution",
                   token="d01_d08_individual_claim"),
        _owned_row(75, _P02, "d10_unauthorized_benefit_risk",
                   "project_safety_trend",
                   token="formal_benefit_risk_conclusion"),
        _owned_row(76, _P02, "d10_unauthorized_confirmatory",
                   "project_efficacy_trend",
                   token="confirmatory_treatment_effect"),
        _owned_row(77, _P02, "d10_legal_row_kind_mismatch",
                   "project_risk_distribution", legal_match=False),
        _owned_row(78, _P02, "d10_envelope_revision_mismatch",
                   "project_risk_distribution", envelope_ok=False,
                   gate_kind="global_gate",
                   gate_reasons=["envelope_source_revision_not_closed"]),
        _owned_row(79, _P02, "d10_global_scope_mismatch",
                   "project_risk_distribution", scope_eq="mismatch",
                   gate_kind="global_gate", gate_reasons=["scope_binding_mismatch"]),
        _owned_row(80, _P02, "d10_global_admission_failed",
                   "project_risk_distribution", es_state="global_admission_failed",
                   gate_kind="global_gate", gate_reasons=["global_expected_set_failed"]),
        _owned_row(81, _P02, "d10_identity_unstable",
                   "project_risk_distribution", identity_ok=False,
                   gate_kind="global_gate", gate_reasons=["identity_state_unstable"]),
        _owned_row(82, _P02, "d10_blind_authority_missing",
                   "project_efficacy_trend", blind_status="blinded",
                   es_state="global_admission_failed",
                   gate_kind="global_gate",
                   gate_reasons=["blind_authority_missing"]),
        _owned_row(83, _P02, "d10_zero_medical_routing",
                   "project_risk_distribution", es_state="routed_consume_only",
                   gate_kind="routing_gate", gate_reasons=["token_consume_only"]),
        _owned_row(84, _P02, "d10_zero_medical_unresolved",
                   "project_risk_distribution", es_state="routing_gate_unresolved",
                   gate_kind="routing_gate", gate_reasons=["claim_token_unresolved"]),
    ]


_P03 = "p03_identity_scope_duplicate"


def _build_p03_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(85, _P03, "d10_member_wrong_project",
                   "project_risk_distribution",
                   member_scope_kind="wrong_project"),
        _owned_row(86, _P03, "d10_member_wrong_site",
                   "project_risk_distribution", member_scope_kind="wrong_site"),
        _owned_row(87, _P03, "d10_member_wrong_subject",
                   "project_risk_distribution",
                   member_scope_kind="wrong_subject"),
        _owned_row(88, _P03, "d10_member_unresolvable",
                   "project_risk_distribution", member_scope_kind="unresolvable"),
        _owned_row(89, _P03, "d10_duplicate_member_ref",
                   "project_risk_distribution", dup_member_ref=True),
        _owned_row(90, _P03, "d10_scope_site_mismatch",
                   "project_risk_distribution", scope_eq="mismatch",
                   scope_type="site"),
        _owned_row(91, _P03, "d10_scope_subject_mismatch",
                   "project_risk_distribution", scope_eq="mismatch",
                   scope_type="subject"),
        _owned_row(92, _P03, "d10_envelope_hash_mismatch",
                   "project_risk_distribution", scope_eq="mismatch"),
        _owned_row(93, _P03, "d10_revision_pair_mispaired",
                   "project_risk_distribution", envelope_ok=False),
        _owned_row(94, _P03, "d10_origin_verified_single_plane",
                   "project_safety_trend",
                   origin={"decision": "all_verified_same_origin",
                           "verified": 3},
                   safety={"complete": True}),
        _owned_row(95, _P03, "d10_origin_verified_double_count",
                   "project_safety_trend",
                   origin={"decision": "all_verified_same_origin",
                           "verified": 3, "plane_state": "duplicate"},
                   safety={"complete": True}),
        _owned_row(96, _P03, "d10_origin_ambiguous", "project_safety_trend",
                   origin={"decision": "ambiguous", "ambiguous": 2},
                   safety={"complete": True}),
        _owned_row(97, _P03, "d10_origin_mixed_leaves", "project_safety_trend",
                   origin={"decision": "mixed_verified_and_distinct",
                           "verified": 2, "distinct": 2},
                   safety={"complete": True}),
        _owned_row(98, _P03, "d10_origin_wrong_scope", "project_safety_trend",
                   origin={"decision": "wrong_scope"},
                   safety={"complete": True}),
        _owned_row(99, _P03, "d10_origin_not_evaluable", "project_safety_trend",
                   origin={"decision": "not_evaluable"},
                   safety={"complete": True}),
        _owned_row(100, _P03, "d10_parent_descendant_common_numerator",
                   "cross_site_pattern", pattern=1, descendants=2,
                   desc_in_numerator=True),
        _owned_row(101, _P03, "d10_parent_descendant_separate_leaves",
                   "cross_site_pattern", pattern=1, descendants=5,
                   individual=5, num_subject=5, num_event=5, num_site=3),
        _owned_row(102, _P03, "d10_origin_cross_envelope",
                   "project_safety_trend",
                   origin={"decision": "wrong_scope"},
                   safety={"complete": True}),
        _owned_row(103, _P03, "d10_origin_mixed_with_ambiguous",
                   "project_safety_trend",
                   origin={"decision": "ambiguous", "verified": 1,
                           "distinct": 1, "ambiguous": 1},
                   safety={"complete": True}),
        _owned_row(104, _P03, "d10_same_origin_safety_d07",
                   "project_safety_trend",
                   origin={"decision": "all_verified_same_origin",
                           "verified": 2, "plane_state": "duplicate"},
                   safety={"complete": True}),
        _owned_row(105, _P03, "d10_site_identity_merged",
                   "project_risk_distribution", identity_ok=False),
        _owned_row(106, _P03, "d10_subject_identity_split",
                   "project_risk_distribution", identity_ok=False),
        _owned_row(107, _P03, "d10_site_ledger_wrong_project",
                   "cross_site_pattern", envelope_ok=False),
        _owned_row(108, _P03, "d10_member_identity_reuse",
                   "project_risk_distribution", dup_member_ref=True),
    ]


_P04 = "p04_numerator_denominator_time"


def _build_p04_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(109, _P04, "d10_subject_event_separate",
                   "project_risk_distribution", num_subject=5, num_event=9,
                   num_site=2, individual=5),
        _owned_row(110, _P04, "d10_subject_event_mixed",
                   "project_risk_distribution",
                   count_layers=["individual_risk", "event_or_outcome"]),
        _owned_row(111, _P04, "d10_planes_separate",
                   "project_risk_distribution", pattern=1, descendants=5,
                   individual=5, num_subject=5, num_event=5, num_site=3),
        _owned_row(112, _P04, "d10_planes_common_numerator",
                   "project_risk_distribution",
                   count_layers=["center_pattern", "individual_risk",
                                 "project_signal"]),
        _owned_row(113, _P04, "d10_den_enrolled",
                   "project_risk_distribution",
                   den_kind="enrolled_subjects", den_value=150),
        _owned_row(114, _P04, "d10_den_treated",
                   "project_risk_distribution"),
        _owned_row(115, _P04, "d10_den_safety_evaluable",
                   "project_risk_distribution",
                   den_kind="safety_evaluable_subjects", den_value=120),
        _owned_row(116, _P04, "d10_den_efficacy_evaluable",
                   "project_risk_distribution",
                   den_kind="efficacy_evaluable_subjects", den_value=118),
        _owned_row(117, _P04, "d10_den_subject_time", "project_safety_trend",
                   den_kind="subject_time", den_value=1200,
                   safety={"complete": True}, estimate="incidence_rate",
                   segments=2),
        _owned_row(118, _P04, "d10_den_exposure_time", "project_safety_trend",
                   den_kind="exposure_time", den_value=980,
                   safety={"complete": True},
                   estimate="exposure_adjusted_rate", segments=2),
        _owned_row(119, _P04, "d10_den_opportunities",
                   "project_risk_distribution",
                   den_kind="expected_assessment_opportunities",
                   den_value=504),
        _owned_row(120, _P04, "d10_den_analysis_population",
                   "project_efficacy_trend",
                   den_kind="analysis_population_members", den_value=112,
                   efficacy={"complete": True}),
        _owned_row(121, _P04, "d10_closed_zero_design_na",
                   "project_risk_distribution", den_state="closed_zero",
                   den_value=0, design_applicable="not_applicable",
                   hit="no_hit"),
        _owned_row(122, _P04, "d10_closed_zero_not_negative",
                   "project_risk_distribution", den_state="closed_zero",
                   den_value=0, hit="no_hit"),
        _owned_row(123, _P04, "d10_zero_events_complete_negative",
                   "project_risk_distribution", hit="no_hit",
                   num_subject=0, num_event=0, num_site=0, individual=0),
        _owned_row(124, _P04, "d10_exclusions_applied",
                   "project_risk_distribution", den_excl=["not_in_analysis_set"]),
        _owned_row(125, _P04, "d10_exclusion_counted",
                   "project_risk_distribution", excluded_in_numerator=True,
                   den_excl=["not_in_analysis_set"]),
        _owned_row(126, _P04, "d10_subject_time_overlap",
                   "project_safety_trend", safety={"complete": True},
                   segments=2, seg_overlap=True),
        _owned_row(127, _P04, "d10_subject_time_valid",
                   "project_safety_trend", den_kind="subject_time",
                   den_value=1200, safety={"complete": True},
                   estimate="incidence_rate", segments=2),
        _owned_row(128, _P04, "d10_exposure_time_tamper",
                   "project_safety_trend", safety={"complete": True},
                   segments=2, seg_tamper=True),
        _owned_row(129, _P04, "d10_exposure_time_valid",
                   "project_safety_trend", den_kind="exposure_time",
                   den_value=980, safety={"complete": True},
                   estimate="exposure_adjusted_rate", segments=2),
        _owned_row(130, _P04, "d10_opportunity_accepted",
                   "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": True},
                   individual=9, num_subject=9, num_event=9, num_site=2),
        _owned_row(131, _P04, "d10_opportunity_raw_only",
                   "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": True,
                        "provenance": "raw_only"}),
        _owned_row(132, _P04, "d10_opportunity_incomplete",
                   "project_risk_distribution",
                   opp={"expected": 42, "observed": 9, "complete": False,
                        "state": "insufficient"}),
        _owned_row(133, _P04, "d10_population_missing",
                   "project_efficacy_trend", pop_present=False,
                   efficacy={"complete": True}),
        _owned_row(134, _P04, "d10_population_mismatch",
                   "project_efficacy_trend", pop_present=False,
                   efficacy={"complete": True}),
        _owned_row(135, _P04, "d10_denominator_tamper",
                   "project_risk_distribution", den_tamper=True),
        _owned_row(136, _P04, "d10_segment_not_from_anchors",
                   "project_safety_trend", safety={"complete": True},
                   segments=1, seg_tamper=True),
    ]


_P05 = "p05_cross_site_comparability"


def _build_p05_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(137, _P05, "d10_small_site_boundary",
                   "cross_site_pattern", comp_reasons=["site_small"],
                   den_value=10, num_subject=1, num_event=1, num_site=1,
                   individual=1),
        _owned_row(138, _P05, "d10_small_site_outlier_rate",
                   "cross_site_pattern", comp_reasons=["site_small_outlier"],
                   den_value=8, num_subject=3, num_event=3, num_site=1,
                   individual=3),
        _owned_row(139, _P05, "d10_small_site_heterogeneous",
                   "cross_site_pattern", comp_reasons=["heterogeneous_sites"],
                   eligible_sites=2, den_value=18, num_subject=4,
                   num_event=4, num_site=2, individual=4),
        _owned_row(140, _P05, "d10_late_start_boundary",
                   "cross_site_pattern", comp_reasons=["site_late_start"],
                   site_activation="late"),
        _owned_row(141, _P05, "d10_late_start_outlier",
                   "cross_site_pattern", comp_reasons=["site_late_start_outlier"],
                   site_activation="late"),
        _owned_row(142, _P05, "d10_late_start_incomparable",
                   "cross_site_pattern", comp_state="incomparable_sites",
                   eligible_sites=2, required_sites=3, site_activation="late",
                   es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"]),
        _owned_row(143, _P05, "d10_case_mix_mismatch",
                   "cross_site_pattern", comp_reasons=["case_mix_mismatch"]),
        _owned_row(144, _P05, "d10_case_mix_missing",
                   "cross_site_pattern", comp_reasons=["case_mix_missing"]),
        _owned_row(145, _P05, "d10_followup_shortfall",
                   "cross_site_pattern", comp_reasons=["followup_shortfall"]),
        _owned_row(146, _P05, "d10_exposure_shortfall",
                   "cross_site_pattern", comp_reasons=["exposure_shortfall"]),
        _owned_row(147, _P05, "d10_site_coverage_hole",
                   "cross_site_pattern"),
        _owned_row(148, _P05, "d10_site_coverage_truncated",
                   "cross_site_pattern"),
        _owned_row(149, _P05, "d10_method_invalid", "cross_site_pattern",
                   comp_reasons=["method_validity_insufficient"]),
        _owned_row(150, _P05, "d10_method_insufficient", "cross_site_pattern",
                   comp_reasons=["method_validity_insufficient"]),
        _owned_row(151, _P05, "d10_insufficient_sites_one",
                   "cross_site_pattern", es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=1,
                   required_sites=3),
        _owned_row(152, _P05, "d10_insufficient_sites_zero",
                   "cross_site_pattern", es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=0,
                   required_sites=3),
        _owned_row(153, _P05, "d10_incomparable_denominators",
                   "cross_site_pattern", es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"],
                   comp_state="incomparable_sites", eligible_sites=2,
                   required_sites=3),
        _owned_row(154, _P05, "d10_incomparable_windows",
                   "cross_site_pattern", es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_incomparable_sites"],
                   comp_state="incomparable_sites", eligible_sites=2,
                   required_sites=3),
        _owned_row(155, _P05, "d10_cross_site_ready_positive",
                   "cross_site_pattern", eligible_sites=3, num_subject=7,
                   num_event=9, num_site=3),
        _owned_row(156, _P05, "d10_cross_site_counterevidence",
                   "cross_site_pattern", ce_declared=2, ce_matched=2),
        _owned_row(157, _P05, "d10_d06_efficacy_as_pattern",
                   "cross_site_pattern", member_producer_d06=True,
                   pattern=1, descendants=2),
        _owned_row(158, _P05, "d10_d06_measure_authorized",
                   "project_efficacy_trend", efficacy={"complete": True},
                   eligible_sites=3, num_subject=7, num_event=7, num_site=3),
        _owned_row(159, _P05, "d10_site_quality_judgment_attempt",
                   "cross_site_pattern"),
        _row(160, _P05, "d10_site_quality_handoff", "cross_site_pattern",
             "site_quality_judgment", "handoff_only",
             es_state="routed_consume_only", gate_kind="routing_gate",
             gate_reasons=["token_handoff_only"]),
        _owned_row(161, _P05, "d10_small_site_excluded",
                   "cross_site_pattern", es_state="control_plane_gate",
                   gate_kind="comparison_set_gate",
                   gate_reasons=["comparison_insufficient_sites"],
                   comp_state="insufficient_sites", eligible_sites=2,
                   required_sites=3, excluded_sites=1),
        _owned_row(162, _P05, "d10_site_evidence_incomplete",
                   "cross_site_pattern",
                   comp_reasons=["site_evidence_incomplete"]),
        _owned_row(163, _P05, "d10_cross_site_positive_evidence",
                   "cross_site_pattern", eligible_sites=3, num_subject=12,
                   num_event=15, num_site=3, individual=12),
        _owned_row(164, _P05, "d10_cross_site_heterogeneous_boundary",
                   "cross_site_pattern",
                   comp_reasons=["heterogeneous_sites"]),
    ]


_P06 = "p06_safety_trend"
_S = {"complete": True}


def _build_p06_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(165, _P06, "d10_safety_ae_proportion",
                   "project_safety_trend", safety=_S, num_subject=7,
                   num_event=9, num_site=3),
        _owned_row(166, _P06, "d10_safety_no_hit", "project_safety_trend",
                   safety=_S, hit="no_hit"),
        _owned_row(167, _P06, "d10_safety_severity", "project_safety_trend",
                   safety=_S),
        _owned_row(168, _P06, "d10_safety_severity_scale_missing",
                   "project_safety_trend",
                   safety={"complete": False, "missing": ["severity"]}),
        _owned_row(169, _P06, "d10_safety_sae", "project_safety_trend",
                   safety=_S),
        _owned_row(170, _P06, "d10_safety_sae_singleton_hotspot",
                   "project_safety_trend", safety=_S, hotspot=True,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(171, _P06, "d10_safety_aesi", "project_safety_trend",
                   safety=_S),
        _owned_row(172, _P06, "d10_safety_aesi_context_missing",
                   "project_safety_trend",
                   safety={"complete": False, "missing": ["risk_window"]}),
        _owned_row(173, _P06, "d10_safety_discontinuation",
                   "project_safety_trend", safety=_S),
        _owned_row(174, _P06, "d10_safety_discontinuation_small",
                   "project_safety_trend", safety=_S, small=True,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(175, _P06, "d10_safety_lab_trend", "project_safety_trend",
                   safety=_S),
        _owned_row(176, _P06, "d10_safety_lab_no_hit", "project_safety_trend",
                   safety=_S, hit="no_hit"),
        _owned_row(177, _P06, "d10_safety_exposure_adjusted",
                   "project_safety_trend", safety=_S,
                   den_kind="exposure_time", den_value=980,
                   estimate="exposure_adjusted_rate", segments=2),
        _owned_row(178, _P06, "d10_safety_exposure_missing",
                   "project_safety_trend",
                   safety={"complete": False, "missing": ["exposure"]}),
        _owned_row(179, _P06, "d10_safety_special_population",
                   "project_safety_trend", safety=_S),
        _owned_row(180, _P06, "d10_safety_special_population_small",
                   "project_safety_trend", safety=_S, small=True,
                   num_subject=2, num_event=2, num_site=1, individual=2),
        _owned_row(181, _P06, "d10_safety_singleton_hidden_attempt",
                   "project_safety_trend", safety=_S, hotspot=True,
                   hotspot_hidden=True),
        _owned_row(182, _P06, "d10_safety_singleton_preserved",
                   "project_safety_trend", safety=_S, hotspot=True,
                   num_subject=1, num_event=1, num_site=1, individual=1),
        _owned_row(183, _P06, "d10_safety_pvalue_only",
                   "project_safety_trend", safety=_S, sources=["pvalue"]),
        _owned_row(184, _P06, "d10_safety_model_majority",
                   "project_safety_trend", safety=_S,
                   sources=["model_majority"],
                   model={"role": "candidate_explanation",
                          "ensemble_size": 1}),
        _owned_row(185, _P06, "d10_safety_context_incomplete",
                   "project_safety_trend",
                   safety={"complete": False, "missing": ["coding"]}),
        _owned_row(186, _P06, "d10_safety_context_no_window",
                   "project_safety_trend",
                   safety={"complete": False, "missing": ["risk_window"]}),
        _owned_row(187, _P06, "d10_safety_formal_wording",
                   "project_safety_trend", safety=_S, injection=True,
                   injection_blocked=False),
        _owned_row(188, _P06, "d10_safety_event_double_count",
                   "project_safety_trend", safety=_S, dup_member_ref=True),
    ]


_P07 = "p07_efficacy_trend"
_E = {"complete": True}


def _build_p07_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(189, _P07, "d10_efficacy_endpoint",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="responder_rate"),
        _owned_row(190, _P07, "d10_efficacy_endpoint_conflict",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned_row(191, _P07, "d10_efficacy_timepoint",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="summary_statistic"),
        _owned_row(192, _P07, "d10_efficacy_timepoint_missing",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned_row(193, _P07, "d10_efficacy_baseline",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="summary_statistic"),
        _owned_row(194, _P07, "d10_efficacy_baseline_missing",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned_row(195, _P07, "d10_efficacy_missing_rule",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="responder_rate"),
        _owned_row(196, _P07, "d10_efficacy_missing_rule_absent",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["missing"]}),
        _owned_row(197, _P07, "d10_efficacy_intercurrent",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="responder_rate"),
        _owned_row(198, _P07, "d10_efficacy_intercurrent_absent",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["intercurrent"]}),
        _owned_row(199, _P07, "d10_efficacy_estimand_bound",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="model_estimate"),
        _owned_row(200, _P07, "d10_efficacy_estimand_mismatch",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["estimand"]}),
        _owned_row(201, _P07, "d10_efficacy_unblinded_authorized",
                   "project_efficacy_trend", efficacy=_E,
                   treatment_required=True, assignment_present=True,
                   blind_status="unblinded_authorized",
                   estimate="summary_statistic"),
        _owned_row(202, _P07, "d10_efficacy_assignment_missing",
                   "project_efficacy_trend", efficacy=_E,
                   treatment_required=True, assignment_present=False),
        _owned_row(203, _P07, "d10_efficacy_unauthorized_unblinded",
                   "project_efficacy_trend", efficacy=_E,
                   treatment_required=True, assignment_present=False,
                   blind_inference=True),
        _owned_row(204, _P07, "d10_efficacy_blind_inference_counts",
                   "project_efficacy_trend", efficacy=_E,
                   blind_inference=True),
        _owned_row(205, _P07, "d10_efficacy_responder_rate",
                   "project_efficacy_trend", efficacy=_E,
                   estimate="responder_rate"),
        _owned_row(206, _P07, "d10_efficacy_responder_no_context",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["endpoint"]}),
        _owned_row(207, _P07, "d10_efficacy_model_no_estimand",
                   "project_efficacy_trend",
                   efficacy={"complete": False, "missing": ["estimand"]}),
        _owned_row(208, _P07, "d10_efficacy_summary_no_population",
                   "project_efficacy_trend", pop_present=False,
                   efficacy=_E),
        _owned_row(209, _P07, "d10_efficacy_pvalue_only",
                   "project_efficacy_trend", efficacy=_E,
                   sources=["pvalue"]),
        _owned_row(210, _P07, "d10_efficacy_model_majority",
                   "project_efficacy_trend", efficacy=_E,
                   sources=["model_majority"],
                   model={"role": "candidate_explanation",
                          "ensemble_size": 1}),
        _owned_row(211, _P07, "d10_efficacy_confirmatory_attempt",
                   "project_efficacy_trend", efficacy=_E, injection=True,
                   injection_blocked=False),
        _owned_row(212, _P07, "d10_efficacy_window_incomparable",
                   "project_efficacy_trend", efficacy=_E,
                   es_state="control_plane_gate",
                   gate_kind="window_pair_gate",
                   gate_reasons=["window_pair_incomparable_windows"],
                   pair_state="incomparable_windows", wins=2,
                   unique_windows=2),
    ]


_P08 = "p08_change_cause_lineage"


def _build_p08_rows() -> list[dict[str, Any]]:
    def ch(**kw: Any) -> dict[str, Any]:
        base = dict(CHANGE_DEFAULTS)
        base.update(kw)
        return base
    return [
        _owned_row(213, _P08, "d10_initial_full_positive",
                   "project_risk_distribution",
                   change=ch(r2_action="create", r2_prior=False,
                             r2_lineage="initial_full_snapshot")),
        _owned_row(214, _P08, "d10_initial_full_negative",
                   "project_risk_distribution", hit="no_hit", change=ch()),
        _owned_row(215, _P08, "d10_initial_full_fake_new",
                   "project_risk_distribution",
                   change=ch(claimed_kind="new", claimed_cause="data")),
        _owned_row(216, _P08, "d10_incremental_new",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=2, data_kind="new",
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(217, _P08, "d10_incremental_resolved",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="resolved",
                             r2_action="propose_close", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(218, _P08, "d10_incremental_continued",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="continued",
                             r2_action="continue", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(219, _P08, "d10_incremental_downgraded",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="downgraded",
                             r2_action="update", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(220, _P08, "d10_cutoff_strict_advance",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(221, _P08, "d10_cutoff_first_positive_no_prior",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(222, _P08, "d10_cutoff_predicate_tamper",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="same_window",
                             cutoff_policy_equal=True,
                             claimed_cutoff="strict_advance",
                             r2_action="create", r2_prior=False)),
        _owned_row(223, _P08, "d10_same_window_replay",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_kind="new",
                             cutoff_state="same_window",
                             cutoff_policy_equal=True,
                             claimed_cutoff="strict_advance",
                             r2_action="create", r2_prior=False)),
        _owned_row(224, _P08, "d10_cutoff_rule_mixed",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new", rule_n=1,
                             cutoff_state="strict_advance",
                             cutoff_predicate=True, cutoff_policy_equal=True,
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
        _owned_row(225, _P08, "d10_rule_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, rule_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_rule_or_mapping_change")),
        _owned_row(226, _P08, "d10_mapping_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, mapping_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_rule_or_mapping_change")),
        _owned_row(227, _P08, "d10_method_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, method_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(228, _P08, "d10_population_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, population_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(229, _P08, "d10_visibility_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, visibility_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_visibility_change")),
        _owned_row(230, _P08, "d10_coverage_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, coverage_n=1, r2_action="supersede",
                             r2_prior=True, r2_lineage="coverage_regressed")),
        _owned_row(231, _P08, "d10_mode_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, mode_n=1, r2_action="supersede",
                             r2_prior=True, r2_lineage="superseded_by_mode_change")),
        _owned_row(232, _P08, "d10_mixed_non_data",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, rule_n=1, method_n=1,
                             r2_action="supersede", r2_prior=True,
                             r2_lineage="superseded_by_method_or_population_change")),
        _owned_row(233, _P08, "d10_r2_create_with_prior",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             r2_action="create", r2_prior=True)),
        _owned_row(234, _P08, "d10_r2_carry_forward_broken_coverage",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="continued",
                             carry_forward=True, r2_action="continue",
                             r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(235, _P08, "d10_r2_wrong_lineage",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             r2_action="create", r2_prior=False,
                             r2_lineage="superseded_by_mode_change")),
        _owned_row(236, _P08, "d10_data_revision_continued",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=2, data_kind="continued",
                             r2_action="continue", r2_prior=True,
                             r2_lineage="continued_from_data_revision")),
        _owned_row(237, _P08, "d10_coverage_regression",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, coverage_n=1,
                             r2_lineage="coverage_regressed")),
        _owned_row(238, _P08, "d10_knowledge_change_analysis_only",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, knowledge_n=1, r2_action="supersede",
                             r2_prior=True,
                             r2_lineage="superseded_by_knowledge_change")),
        _owned_row(239, _P08, "d10_fake_data_cause",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, rule_n=1, data_kind="new",
                             claimed_kind="new", claimed_cause="data",
                             r2_action="continue", r2_prior=True)),
        _owned_row(240, _P08, "d10_cutoff_not_evaluable",
                   "project_risk_distribution",
                   change=ch(basis="incremental", comparison_state="comparable",
                             prior=True, data_n=1, data_kind="new",
                             cutoff_state="not_evaluable",
                             r2_action="create", r2_prior=False,
                             r2_lineage="continued_from_cutoff_advance")),
    ]


_P09 = "p09_query_deeplink"


def _build_p09_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(241, _P09, "d10_query_generated",
                   "project_risk_distribution"),
        _owned_row(242, _P09, "d10_query_within_fanout",
                   "project_risk_distribution"),
        _owned_row(243, _P09, "d10_query_fully_covered",
                   "project_risk_distribution",
                   q_covered=7, q_uncovered=0,
                   q_decision="fully_covered_by_member_queries"),
        _owned_row(244, _P09, "d10_query_unlistable",
                   "project_risk_distribution",
                   q_decision="members_unlistable", q_unlistable=True),
        _owned_row(245, _P09, "d10_query_fanout_exceeded",
                   "project_risk_distribution", q_uncovered=101,
                   q_fanout=100),
        _owned_row(246, _P09, "d10_query_pd_wording",
                   "project_risk_distribution", q_pd="verify_whether_pd",
                   q_uncovered=2),
        _owned_row(247, _P09, "d10_query_non_pd",
                   "project_risk_distribution", q_uncovered=3),
        _owned_row(248, _P09, "d10_query_three_part_sentences",
                   "project_risk_distribution", q_uncovered=4),
        _owned_row(249, _P09, "d10_deeplink_member",
                   "project_risk_distribution", dl_n=1, dl_kinds=["member"]),
        _owned_row(250, _P09, "d10_deeplink_site",
                   "project_risk_distribution", dl_n=1, dl_kinds=["site"]),
        _owned_row(251, _P09, "d10_deeplink_subject_site_pair",
                   "project_risk_distribution", dl_n=1,
                   dl_kinds=["subject_site_pair"]),
        _owned_row(252, _P09, "d10_deeplink_deficient",
                   "project_risk_distribution", locator_missing=True),
        _owned_row(253, _P09, "d10_journey_one_hop",
                   "project_risk_distribution", dl_n=3,
                   dl_kinds=["member", "site", "subject_site_pair"]),
        _owned_row(254, _P09, "d10_source_locator_missing",
                   "project_risk_distribution", locator_missing=True),
        _owned_row(255, _P09, "d10_query_reorder_invariant",
                   "project_risk_distribution"),
        _owned_row(256, _P09, "d10_query_source_tamper",
                   "project_risk_distribution", q_ids_mismatch=True),
        _owned_row(257, _P09, "d10_query_redundancy_tamper",
                   "project_risk_distribution", q_covered=2, q_uncovered=3),
        _owned_row(258, _P09, "d10_query_duplicate_per_unit",
                   "project_risk_distribution", q_duplicate=True),
        _owned_row(259, _P09, "d10_deeplink_subject_only",
                   "project_risk_distribution", dl_violation=True, dl_n=1,
                   dl_kinds=["subject_site_pair"]),
        _owned_row(260, _P09, "d10_audience_injection_blocked",
                   "project_risk_distribution", injection=True,
                   injection_blocked=True),
    ]


_P10 = "p10_visibility_blindness"


def _build_p10_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(261, _P10, "d10_vis_hidden_members",
                   "project_risk_distribution", vis_hidden_members=2,
                   rate_state="qualified"),
        _owned_row(262, _P10, "d10_vis_hidden_denominator",
                   "project_risk_distribution", vis_hidden_sites=1,
                   rate_state="suppressed"),
        _owned_row(263, _P10, "d10_vis_rate_suppressed",
                   "project_risk_distribution", vis_hidden_members=3,
                   rate_state="suppressed"),
        _owned_row(264, _P10, "d10_vis_rate_qualified",
                   "project_risk_distribution", vis_hidden_members=2,
                   rate_state="qualified"),
        _owned_row(265, _P10, "d10_vis_hidden_site",
                   "project_risk_distribution", vis_hidden_sites=1,
                   rate_state="qualified"),
        _owned_row(266, _P10, "d10_vis_hidden_omission",
                   "project_risk_distribution", vis_hidden_members=2,
                   vis_hidden_omission=True),
        _owned_row(267, _P10, "d10_vis_algebra_violation",
                   "project_risk_distribution", vis_hidden_members=2,
                   vis_algebra_ok=False),
        _owned_row(268, _P10, "d10_vis_dl_eligible_valid",
                   "project_risk_distribution", dl_n=2,
                   dl_kinds=["member", "site"]),
        _owned_row(269, _P10, "d10_vis_dl_eligible_violation",
                   "project_risk_distribution", dl_violation=True),
        _owned_row(270, _P10, "d10_vis_dl_hidden_site_pair",
                   "project_risk_distribution", dl_violation=True),
        _owned_row(271, _P10, "d10_vis_visible_n_algebra",
                   "project_risk_distribution", vis_algebra_ok=False),
        _owned_row(272, _P10, "d10_vis_hidden_counts_algebra",
                   "project_risk_distribution", vis_hidden_members=2,
                   vis_algebra_ok=False, vis_hidden_counts_bad=True),
        _owned_row(273, _P10, "d10_vis_blind_denominator_inference",
                   "project_risk_distribution", blind_inference=True),
        _owned_row(274, _P10, "d10_vis_blind_label_inference",
                   "project_risk_distribution", blind_inference=True),
        _owned_row(275, _P10, "d10_vis_unblinded_authorized",
                   "project_efficacy_trend", efficacy=_E,
                   treatment_required=True, assignment_present=True,
                   blind_status="unblinded_authorized",
                   estimate="summary_statistic"),
        _owned_row(276, _P10, "d10_vis_hidden_dropped",
                   "project_risk_distribution", vis_hidden_members=2,
                   vis_hidden_dropped=True),
    ]


_P11 = "p11_unicode_tamper_bijection"
_REPLAY_CHANGE = {"basis": "full", "comparison_state": "initial_full",
                  "cutoff_state": "same_window", "cutoff_predicate": False,
                  "cutoff_policy_equal": True}


def _build_p11_rows() -> list[dict[str, Any]]:
    return [
        _owned_row(277, _P11, "d10_nfc_normalized",
                   "project_risk_distribution"),
        _owned_row(278, _P11, "d10_nfc_zh_text",
                   "project_risk_distribution"),
        _owned_row(279, _P11, "d10_confusable_fullwidth",
                   "project_risk_distribution", injection=True,
                   injection_blocked=False),
        _owned_row(280, _P11, "d10_confusable_homoglyph",
                   "project_risk_distribution", injection=True,
                   injection_blocked=False),
        _owned_row(281, _P11, "d10_inject_pattern_rule_token",
                   "project_risk_distribution", injection=True,
                   injection_blocked=False),
        _owned_row(282, _P11, "d10_rehash_envelope",
                   "project_risk_distribution", rehash=True),
        _owned_row(283, _P11, "d10_rehash_query",
                   "project_risk_distribution", rehash=True),
        _owned_row(284, _P11, "d10_rehash_projection",
                   "project_risk_distribution", rehash=True),
        _owned_row(285, _P11, "d10_duplicate_id_rejected",
                   "project_risk_distribution", dup_member_ref=True),
        _owned_row(286, _P11, "d10_duplicate_locator",
                   "project_risk_distribution", dup_locator=True),
        _owned_row(287, _P11, "d10_nan_rejected",
                   "project_risk_distribution", den_value=-1),
        _owned_row(288, _P11, "d10_id_reuse_across_revisions",
                   "project_risk_distribution", dup_revision=True),
        _owned_row(289, _P11, "d10_id_replay_same_content",
                   "project_risk_distribution", change=_REPLAY_CHANGE),
        _owned_row(290, _P11, "d10_order_permutation",
                   "project_risk_distribution", change=_REPLAY_CHANGE),
        _owned_row(291, _P11, "d10_ref_prefix_invariant",
                   "project_risk_distribution", change=_REPLAY_CHANGE),
        _owned_row(292, _P11, "d10_canonical_byte_stable",
                   "project_risk_distribution"),
        _owned_row(293, _P11, "d10_key_exactness",
                   "project_risk_distribution"),
        _owned_row(294, _P11, "d10_bijection_bijective",
                   "project_risk_distribution"),
        _owned_row(295, _P11, "d10_contract_hash_mismatch",
                   "project_risk_distribution", envelope_ok=False),
        _owned_row(296, _P11, "d10_authority_unresolved",
                   "project_risk_distribution",
                   design_applicable="unresolved"),
    ]


_P12 = "p12_anti_overfit"
_ANTI_BASE_NAMES = ("table_field_rename", "input_order_shuffle",
                    "version_field_change", "zh_label_change",
                    "display_precision_change", "evidence_row_change",
                    "audience_contract_id_change", "envelope_id_change")


def _build_p12_rows() -> list[dict[str, Any]]:
    rows = []
    for n, base in enumerate(_ANTI_BASE_NAMES):
        for v in (1, 2):
            idx = 297 + n * 2 + (v - 1)
            kw: dict[str, Any] = {"anti_base": base, "variant": v}
            if base == "version_field_change" and v == 2:
                kw["mode_version_alt"] = True
            if base == "envelope_id_change" and v == 2:
                kw["envelope_id_alt"] = True
            if base == "audience_contract_id_change" and v == 2:
                kw["audience_id_alt"] = True
            if base == "table_field_rename" and v == 2:
                kw["evidence_file_alt"] = True
            if base == "evidence_row_change" and v == 2:
                kw["evidence_row_alt"] = True
            rows.append(_owned_row(idx, _P12, f"d10_anti_overfit_{base}_v{v}",
                                   "project_risk_distribution",
                                   identity_idx=297 + n * 2, **kw))
    return rows


AUTHORITY_ROWS: list[dict[str, Any]] = (
    _build_p01_rows() + _build_p02_rows() + _build_p03_rows()
    + _build_p04_rows() + _build_p05_rows() + _build_p06_rows()
    + _build_p07_rows() + _build_p08_rows() + _build_p09_rows()
    + _build_p10_rows() + _build_p11_rows() + _build_p12_rows()
)

# ---------------------------------------------------------------------------
# Authority block builders (mirror the accepted catalog conventions; every
# value is FIXED here as accepted upstream authority)
# ---------------------------------------------------------------------------
def _derive_origin_decision(verified: list[str], distinct: list[str],
                            ambiguous: list[str]) -> str:
    """origin_decision derived ONLY from set membership (contract section 4):
    ambiguous non-empty -> ambiguous; verified only -> all_verified_same_origin;
    distinct only -> all_distinct; verified+distinct -> mixed; else not_evaluable."""
    if ambiguous:
        return "ambiguous"
    if verified and distinct:
        return "mixed_verified_and_distinct"
    if verified:
        return "all_verified_same_origin"
    if distinct:
        return "all_distinct"
    return "not_evaluable"


def _revision_content_hash(revision_id: str, locator_ids: list[str]) -> str:
    """Revision content hash bound to the revision's typed content anchors
    (the case's accepted source locator set), never to the id alone."""
    return sha256_text(canonical_json({
        "revision_id": revision_id,
        "source_locators": sorted(locator_ids),
    }))


def _locator_ids_for(ridx: int) -> list[str]:
    return sorted({f"SYN-D10-LOC-{ridx:03d}-01",
                   f"SYN-D10-LOC-{ridx:03d}-02"})


def _mode_contract_block(ridx: int, mode_version: str,
                         f: dict[str, Any]) -> dict[str, Any]:
    design_ref = None
    if f.get("design_applicable", "applicable") != "applicable":
        design_ref = f"SYN-D10-DESIGN-{ridx:03d}"
    mode = {
        "mode_contract_version": mode_version,
        "mode_contract_content_hash": "",
        "design_clause_ref": design_ref,
        "design_applicable_state": f.get("design_applicable", "applicable"),
    }
    core = {key: item for key, item in mode.items()
            if key != "mode_contract_content_hash"}
    mode["mode_contract_content_hash"] = sha256_text(canonical_json(core))
    return mode


def _visibility_block(f: dict[str, Any], members: list[dict[str, Any]],
                      evaluation: list[str], projectable: list[str],
                      hidden: list[str], dl_eligible: list[str],
                      visible_n: int, hidden_count: int) -> dict[str, Any]:
    vis_hidden_sites = int(f.get("vis_hidden_sites", 0))
    eval_sites = ["SYN-D10-SITE-001"]
    proj_sites = ["SYN-D10-SITE-001"] if vis_hidden_sites == 0 else []
    hidden_sites = [] if vis_hidden_sites == 0 else ["SYN-D10-SITE-001"]
    dl_sites = (["SYN-D10-SITE-001"]
                if dl_eligible and not f.get("dl_violation") else [])
    projectable_refs = set(projectable)
    projectable_members = [m for m in members if m["member_ref"] in projectable_refs]
    eligible_refs = set(dl_eligible)
    eligible_members = [m for m in members if m["member_ref"] in eligible_refs]
    pairs = sorted({(m["subject_stable_id"], m["site_stable_id"])
                    for m in projectable_members
                    if m["subject_stable_id"] and m["site_stable_id"]
                    and m["site_stable_id"] in proj_sites})
    eligible_pairs = sorted({(m["subject_stable_id"], m["site_stable_id"])
                             for m in eligible_members
                             if m["subject_stable_id"] and m["site_stable_id"]
                             and m["site_stable_id"] in proj_sites})
    return {
        "blind_status": f.get("blind_status", "blinded"),
        "hidden_member_count": hidden_count,
        "hidden_site_count": vis_hidden_sites,
        "rate_projection_state": f.get("rate_state", "permitted"),
        "evaluation_member_set_hash": sha256_text(
            canonical_json(sorted(set(evaluation)))),
        "projectable_member_set_hash": sha256_text(
            canonical_json(sorted(set(projectable)))),
        "hidden_member_set_hash": sha256_text(
            canonical_json(sorted(set(hidden)))),
        "deep_link_eligible_member_set_hash": sha256_text(
            canonical_json(sorted(set(dl_eligible)))),
        "evaluation_site_set_hash": sha256_text(
            canonical_json(sorted(set(eval_sites)))),
        "projectable_site_set_hash": sha256_text(
            canonical_json(sorted(set(proj_sites)))),
        "hidden_site_set_hash": sha256_text(
            canonical_json(sorted(set(hidden_sites)))),
        "deep_link_eligible_site_set_hash": sha256_text(
            canonical_json(sorted(set(dl_sites)))),
        "projectable_subject_site_pair_set_hash": sha256_text(
            canonical_json(pairs)),
        "deep_link_eligible_subject_site_pair_set_hash": sha256_text(
            canonical_json(eligible_pairs)),
        "projectable_subject_site_pairs": [list(pair) for pair in pairs],
        "deep_link_eligible_subject_site_pairs": [
            list(pair) for pair in eligible_pairs],
        "eligible_n": len(evaluation),
        "visible_n": visible_n,
        "hidden_set_omitted": bool(f.get("vis_hidden_omission")),
        "deep_link_eligible_violation": bool(f.get("dl_violation")),
        "treatment_inference_attempt": bool(f.get("blind_inference")),
    }


def _change_block(ridx: int, ch: dict[str, Any] | None) -> dict[str, Any] | None:
    if ch is None:
        return None
    def refs(key: str, n: int) -> list[str]:
        return [f"SYN-D10-{key}-{ridx:03d}-{m:02d}" for m in range(1, n + 1)]
    def set_hash(key: str, n: int) -> str:
        return sha256_text(canonical_json(sorted(refs(key, n))))
    return {
        "execution_basis": ch.get("basis", "full"),
        "comparison_state": ch.get("comparison_state", "initial_full"),
        "prior_present": bool(ch.get("prior")),
        "prior_evaluation_identity_ref": "SYN-D10-SNAP-PRIOR-001"
        if ch.get("prior") else None,
        "r2_prior_ref": "SYN-D10-R2-PRIOR-001" if ch.get("r2_prior") else None,
        "r2_action": ch.get("r2_action"),
        "r2_lineage": ch.get("r2_lineage"),
        "carry_forward": bool(ch.get("carry_forward")),
        "data_change_ref_set_hash": set_hash("DATACHG", ch.get("data_n", 0)),
        "denominator_change_ref_set_hash": set_hash("DENCHG", ch.get("denom_n", 0)),
        "coverage_change_ref_set_hash": set_hash("COVCHG", ch.get("coverage_n", 0)),
        "knowledge_change_ref_set_hash": set_hash("KCHG", ch.get("knowledge_n", 0)),
        "rule_change_ref_set_hash": set_hash("RULECHG", ch.get("rule_n", 0)),
        "mapping_change_ref_set_hash": set_hash("MAPCHG", ch.get("mapping_n", 0)),
        "model_change_ref_set_hash": set_hash("MODELCHG", ch.get("model_n", 0)),
        "method_change_ref_set_hash": set_hash("METHCHG", ch.get("method_n", 0)),
        "population_change_ref_set_hash": set_hash("POPCHG", ch.get("population_n", 0)),
        "visibility_change_ref_set_hash": set_hash("VISCHG", ch.get("visibility_n", 0)),
        "mode_change_ref_set_hash": set_hash("MODECHG", ch.get("mode_n", 0)),
        "cutoff_decision_state": ch.get("cutoff_state", "not_evaluable"),
        "cutoff_predicate": bool(ch.get("cutoff_predicate")),
        "cutoff_policy_equal": bool(ch.get("cutoff_policy_equal")),
        "prior_boundary_value": ch.get("prior_boundary", "2026-03-31"),
        "current_boundary_value": ch.get("current_boundary", "2026-06-30"),
    }


# ---------------------------------------------------------------------------
# Hydration: row -> full authority entry (accepted upstream values)
# ---------------------------------------------------------------------------
def _hydrate(row: dict[str, Any]) -> dict[str, Any]:
    idx = row["idx"]
    ridx = int(row.get("identity_idx") or idx)  # shared identity base for anti-overfit pairs
    kind = row["kind"]
    f = dict(ROW_DEFAULTS)
    f.update(row)
    n_subject = f.get("num_subject", 7)
    individual = f.get("individual", n_subject)
    pattern = f.get("pattern", 0)
    desc_in_num = bool(f.get("desc_in_numerator"))
    gap_present = f.get("opp") is not None
    safety_present = f.get("safety") is not None
    eff_present = f.get("efficacy") is not None
    dup = bool(f.get("dup_member_ref"))
    den_kind = f.get("den_kind", "treated_subjects")
    den_value = f.get("den_value", 126)
    if den_kind in ("subject_time", "exposure_time") and f.get("segments", 0):
        den_value = f["segments"] * 30
    scope_kind = f.get("member_scope_kind")

    members: list[dict[str, Any]] = []
    for m in range(1, individual + 1):
        scope_state = "in_scope" if scope_kind is None else scope_kind
        subject = (f"SYN-OTHER-SUBJECT-{ridx:03d}-{m:02d}"
                   if scope_kind == "wrong_subject"
                   else f"SYN-D10-SUBJ-{ridx:03d}-01-{m:02d}")
        site = {"wrong_project": "SYN-OTHER-PROJECT-SITE-001",
                "wrong_site": "SYN-OTHER-SITE-001"}.get(scope_kind,
                                                        "SYN-D10-SITE-001")
        loc_state = "missing" if (f.get("locator_missing") and m == 1) \
            else "locatable"
        priority = "high" if (f.get("hotspot") and m == 1) else "medium"
        members.append({
            "member_ref": f"SYN-D10-RISK-{ridx:03d}-{m:02d}",
            "member_kind": "individual_risk", "aggregation_plane": "individual",
            "subject_stable_id": subject, "site_stable_id": site,
            "member_scope_state": scope_state,
            "locator_resolution_state": loc_state,
            "monitoring_priority": priority, "producer_domain": "D01",
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
    pattern_members: list[dict[str, Any]] = []
    for m in range(1, pattern + 1):
        descendants = f.get("descendants", 0)
        pattern_members.append({
            "member_ref": f"SYN-D10-PAT-{ridx:03d}-{m:02d}",
            "member_kind": "center_pattern", "aggregation_plane": "site_pattern",
            "subject_stable_id": f"SYN-D10-SUBJ-{ridx:03d}-01-{m:02d}",
            "site_stable_id": "SYN-D10-SITE-001",
            "member_scope_state": "in_scope",
            "locator_resolution_state": "locatable",
            "monitoring_priority": "medium",
            "producer_domain": ("D06" if f.get("member_producer_d06") else "D09"),
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
        members.append(pattern_members[-1])
    if desc_in_num:
        members.append({
            "member_ref": f"SYN-D10-DESC-{ridx:03d}-01",
            "member_kind": "individual_risk", "aggregation_plane": "individual",
            "subject_stable_id": f"SYN-D10-SUBJ-{ridx:03d}-01-01",
            "site_stable_id": "SYN-D10-SITE-001",
            "member_scope_state": "in_scope",
            "locator_resolution_state": "locatable",
            "monitoring_priority": "medium", "producer_domain": "D01",
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
    if gap_present:
        members.append({
            "member_ref": f"SYN-D10-GAP-{ridx:03d}-01",
            "member_kind": "accepted_gap", "aggregation_plane": "individual",
            "subject_stable_id": f"SYN-D10-SUBJ-{ridx:03d}-01-01",
            "site_stable_id": "SYN-D10-SITE-001",
            "member_scope_state": "in_scope",
            "locator_resolution_state": "locatable",
            "monitoring_priority": "medium", "producer_domain": "D05",
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
    if safety_present:
        members.append({
            "member_ref": f"SYN-D10-SAFE-{ridx:03d}-01",
            "member_kind": "safety_measure", "aggregation_plane": "project_measure",
            "subject_stable_id": f"SYN-D10-SUBJ-{ridx:03d}-01-01",
            "site_stable_id": "SYN-D10-SITE-001",
            "member_scope_state": "in_scope",
            "locator_resolution_state": "locatable",
            "monitoring_priority": "medium", "producer_domain": "D07",
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
    if eff_present:
        members.append({
            "member_ref": f"SYN-D10-EFF-{ridx:03d}-01",
            "member_kind": "efficacy_measure",
            "aggregation_plane": "project_measure",
            "subject_stable_id": f"SYN-D10-SUBJ-{ridx:03d}-01-01",
            "site_stable_id": "SYN-D10-SITE-001",
            "member_scope_state": "in_scope",
            "locator_resolution_state": "locatable",
            "monitoring_priority": "medium", "producer_domain": "D06",
            "locator_ref": f"SYN-D10-LOC-{ridx:03d}-01",
        })
    if dup and members:
        members.append(dict(members[0]))
    member_refs = [m["member_ref"] for m in members]

    den_value_for_refs = max(den_value, 0)
    den_refs = _subject_ids(ridx, den_value_for_refs)
    excl_offset = 0 if f.get("excluded_in_numerator") else 999
    excl_refs = _subject_ids(ridx, len(f.get("den_excl", [])),
                             offset=excl_offset)

    segments: list[dict[str, Any]] = []
    for n in range(1, f.get("segments", 0) + 1):
        tamper = bool(f.get("seg_tamper"))
        raw = 30
        norm = 31 if tamper else raw
        segments.append({
            "segment_id": f"SYN-D10-SEG-{ridx:03d}-{n}",
            "member_ref": f"SYN-D10-SUBJ-{ridx:03d}-01-{n:02d}",
            "segment_kind": "subject_time",
            "start_value": 1 + (n - 1) * 31,
            "end_value": 1 + (n - 1) * 31 + raw - 1,
            "raw_duration": raw,
            "normalized_duration": norm,
            "unit": "day",
            "inclusivity": "both_inclusive",
            "overlap_resolution_ref": None if not f.get("seg_overlap")
            else f"SYN-D10-OVERLAP-{ridx:03d}-{n}",
        })

    vis_hidden = int(f.get("vis_hidden_members", 0))
    hidden = member_refs[:vis_hidden]
    if f.get("vis_hidden_omission"):
        hidden = []
    elif f.get("vis_algebra_ok") is False:
        hidden = member_refs[:vis_hidden] + ["SYN-D10-RISK-EXTERNAL-001"]
    evaluation = list(member_refs)
    if f.get("vis_hidden_dropped"):
        evaluation = evaluation[vis_hidden:]
        projectable = evaluation
    else:
        projectable = member_refs[vis_hidden:]
    dl_eligible = (projectable[:int(f.get("dl_n", 0))]
                   if not f.get("dl_violation") else evaluation[:1])
    visible_n = len(projectable)
    hidden_count = vis_hidden
    if f.get("vis_algebra_ok") is False:
        visible_n = visible_n + 1
        if f.get("vis_hidden_counts_bad"):
            hidden_count = hidden_count + 1

    q_covered = int(f.get("q_covered", 0))
    q_uncovered = int(f.get("q_uncovered", 7))
    q_uncovered_explicit = "q_uncovered" in row
    covered_refs = member_refs[:q_covered]
    if q_uncovered == 0:
        uncovered_refs = []
    elif q_uncovered_explicit and q_uncovered > len(member_refs):
        # Fanout-exceeded negative fixture: retain candidate refs outside the
        # accepted unit so membership validation has a concrete failure.
        uncovered_refs = [f"SYN-D10-RISK-{idx:03d}-{m:02d}"
                          for m in range(1, q_uncovered + 1)]
    elif q_covered > 0 and q_covered + q_uncovered < len(member_refs):
        # Deliberate Query redundancy attack fixture: retain the truncated
        # submitted partition so the independent verifier can fail it closed.
        uncovered_refs = member_refs[q_covered:q_covered + q_uncovered]
    else:
        # Ordinary cases use the full authoritative remainder.
        uncovered_refs = member_refs[q_covered:]

    canonical_query_ids = [
        sha256_text(canonical_json({"member_ref": ref}))
        for ref in sorted(set(covered_refs))]
    if f.get("q_ids_mismatch"):
        # Keep the negative fixture schema-valid while deliberately breaking
        # the identity-to-member mapping.  The verifier must reject it by
        # exact accepted-membership comparison.
        canonical_query_ids = [sha256_text(canonical_json({
            "member_ref": f"SYN-D10-MQID-{ridx:03d}-000"}))]
    unit_member_set_hash = (
        _content_sha(f"tampered-unitmembers:{ridx:03d}")
        if f.get("rehash") else
        sha256_text(canonical_json(sorted(set(member_refs)))))

    mode_version = "SYN-D10-MODE-001"
    if f.get("mode_version_alt"):
        mode_version = "SYN-D10-MODE-001-ALT"

    d09_patterns = [{
        "member_ref": pm["member_ref"],
        "owner_domain": pm["producer_domain"],
        "descendant_refs": _member_ids(idx, f.get("descendants", 0), "DESC"),
    } for pm in pattern_members]

    origin = f.get("origin")
    measure_origin = None
    if origin is not None:
        risk_refs = [m["member_ref"] for m in members
                     if m["member_kind"] == "individual_risk"]
        cursor = 0
        verified = sorted(set(risk_refs[cursor:cursor +
                                        int(origin.get("verified", 0))]))
        cursor += int(origin.get("verified", 0))
        distinct = sorted(set(risk_refs[cursor:cursor +
                                       int(origin.get("distinct", 0))]))
        cursor += int(origin.get("distinct", 0))
        ambiguous = sorted(set(risk_refs[cursor:cursor +
                                        int(origin.get("ambiguous", 0))]))
        candidate = sorted(set(verified) | set(distinct) | set(ambiguous))
        derived_origin_decision = _derive_origin_decision(verified, distinct,
                                                           ambiguous)
        if origin.get("decision") == "wrong_scope" and not candidate:
            derived_origin_decision = "wrong_scope"
        measure_origin = {
            "binding_id": f"SYN-D10-ORIGIN-{ridx:03d}",
            "measure_ref": f"SYN-D10-SAFE-{ridx:03d}-01",
            # The stored decision is only a cached, derived value.  Both the
            # catalog and the independent verifier recompute it from the
            # closed partition below and reject a submitted override.
            "origin_decision": derived_origin_decision,
            "verified_risk_refs": verified,
            "distinct_risk_refs": distinct,
            "ambiguous_risk_refs": ambiguous,
            "candidate_risk_refs": candidate,
            "numerator_plane_state": origin.get("plane_state", "single"),
            "verified_ref_set_hash": sha256_text(canonical_json(sorted(verified))),
            "distinct_ref_set_hash": sha256_text(canonical_json(sorted(distinct))),
            "ambiguous_ref_set_hash": sha256_text(canonical_json(sorted(ambiguous))),
            "candidate_ref_set_hash": sha256_text(canonical_json(candidate)),
            "pairwise_disjoint": not (set(verified) & set(distinct)
                                      or set(verified) & set(ambiguous)
                                      or set(distinct) & set(ambiguous)),
            "source_provenance_hash": sha256_text(canonical_json({
                "measure_ref": f"SYN-D10-SAFE-{ridx:03d}-01",
                "source_revisions": [{
                    "revision_id": f"SRC-REV-{ridx:03d}-001",
                    "content_hash": _revision_content_hash(
                        f"SRC-REV-{ridx:03d}-001", _locator_ids_for(ridx))}],
                "locator_ids": _locator_ids_for(ridx),
            })),
        }

    treatment_required = bool(f.get("treatment_required"))
    assignment_present = bool(f.get("assignment_present"))
    treatment_ok = not (treatment_required and not assignment_present)
    authority_ref = None
    if f.get("efficacy") is not None and treatment_ok:
        authority_ref = f"SYN-D10-TRAUTH-{ridx:03d}"
    assignment_ref = None
    mapping_hash = None
    if assignment_present:
        mapping_hash = sha256_text(canonical_json({
            "authority": authority_ref, "project": "SYN-D10-PROJECT-001",
            "run": "SYN-D10-RUN-001"}))
        assignment_ref = mapping_hash
    es_state = f.get("es_state", "admitted")
    if es_state != "admitted":
        if es_state == "control_plane_gate":
            gate_kind = f.get("gate_kind", "comparison_set_gate")
        elif es_state == "global_admission_failed":
            gate_kind = "global_gate"
        else:
            gate_kind = "routing_gate"
        gate_reasons = list(f.get("gate_reasons", []))
    else:
        gate_kind = None
        gate_reasons = []
    treatment = {
        "treatment_role_required": treatment_required,
        "authority_ref": authority_ref,
        "assignment_identity_ref": assignment_ref,
        "mapping_hash": mapping_hash,
    }

    model = f.get("model")
    model_evidence = None
    if model is not None:
        role = model.get("role", "candidate_explanation")
        analysis_refs = sorted(set(_member_ids(ridx, 2, "MA")))
        model_source_pairs = [{
            "revision_id": f"SRC-REV-{ridx:03d}-001",
            "content_hash": _revision_content_hash(
                f"SRC-REV-{ridx:03d}-001", _locator_ids_for(ridx)),
        }]
        permitted_leaf = ("model_candidate_only"
                          if role == "candidate_explanation"
                          else "counterevidence_suggestion_only")
        model_core = {
            "model_evidence_id": f"SYN-D10-MODEL-{ridx:03d}",
            "evaluation_content_identity": sha256_text(canonical_json({
                "project_ref": "SYN-D10-PROJECT-001",
                "run_ref": "SYN-D10-RUN-001",
                "snapshot_ref": "SYN-D10-SNAP-001",
                "signal_kind": kind,
                "member_refs": sorted(set(member_refs)),
                "source_revision_content_pairs": model_source_pairs,
            })),
            "input_content_hash": sha256_text(canonical_json({
                "input_schema": "d10-typed-input-v1",
                "project_ref": "SYN-D10-PROJECT-001",
                "member_refs": sorted(set(member_refs)),
                "source_revision_content_pairs": model_source_pairs,
            })),
            "source_revision_content_pairs": model_source_pairs,
            "source_refs": _locator_ids_for(ridx),
            "model_id": f"SYN-D10-MODEL-ID-{ridx:03d}",
            "model_version": "SYN-D10-MODEL-V1",
            "independent_context_hash": sha256_text(canonical_json({
                "project_ref": "SYN-D10-PROJECT-001",
                "run_ref": "SYN-D10-RUN-001",
                "snapshot_ref": "SYN-D10-SNAP-001",
                "signal_kind": kind,
            })),
            "ensemble_id": f"SYN-D10-ENSEMBLE-{ridx:03d}",
            "ensemble_size": model.get("ensemble_size", 1),
            "member_analysis_refs": analysis_refs,
            "permitted_leaf": permitted_leaf,
            "member_analysis_ref_set_hash": sha256_text(
                canonical_json(analysis_refs)),
            "output_identity": f"SYN-D10-MODEL-OUTPUT-{ridx:03d}",
            "adjudication_state": "accepted",
        }
        model_core["model_binding_hash"] = sha256_text(
            canonical_json({"role": role, **model_core}))
        model_core["output_hash"] = sha256_text(canonical_json({
            "output_identity": model_core["output_identity"],
            "model_binding_hash": model_core["model_binding_hash"],
            "permitted_leaf": permitted_leaf,
            "adjudication_state": "accepted",
        }))
        model_evidence = {"role": role, **model_core}

    locator_ids = sorted({f"SYN-D10-LOC-{ridx:03d}-01",
                          f"SYN-D10-LOC-{ridx:03d}-02"})
    if f.get("dup_locator"):
        locator_ids = [f"SYN-D10-LOC-{ridx:03d}-01"]
    revision = {"revision_id": f"SRC-REV-{ridx:03d}-001",
                "content_hash": _revision_content_hash(
                    f"SRC-REV-{ridx:03d}-001", locator_ids)}
    # The authority registry pins only genuinely accepted source
    # revision/content pairs.  Extra or duplicate submitted pairs are
    # intentional catalog attacks and belong to evaluation input, never to
    # accepted authority.  Downstream consumers must therefore prove that
    # these accepted pairs are present while retaining submitted extras for
    # semantic verification.
    source_revisions = [revision]

    deep_links = []
    dl_kinds = f.get("dl_kinds") or ["member"]
    member_by_ref = {m["member_ref"]: m for m in members}
    projectable_refs = set(projectable)
    eligible_refs = list(dl_eligible)
    eligible_pairs = sorted({
        (member_by_ref[ref]["subject_stable_id"],
         member_by_ref[ref]["site_stable_id"])
        for ref in eligible_refs if ref in member_by_ref
        and member_by_ref[ref]["subject_stable_id"]
        and member_by_ref[ref]["site_stable_id"]
    })
    for n in range(1, int(f.get("dl_n", 0)) + 1):
        tkind = dl_kinds[(n - 1) % len(dl_kinds)]
        if tkind == "member":
            ref = eligible_refs[(n - 1) % len(eligible_refs)] \
                if eligible_refs else None
            member = member_by_ref.get(ref) if ref else None
            deep_links.append({
                "target_kind": tkind,
                "site_ref": member["site_stable_id"] if member else
                "SYN-D10-SITE-001",
                "subject_ref": member["subject_stable_id"] if member else None,
                "member_object_ref": ref,
            })
        elif tkind == "site":
            deep_links.append({
                "target_kind": tkind,
                "site_ref": "SYN-D10-SITE-001" if projectable_refs else None,
                "subject_ref": None,
                "member_object_ref": None,
            })
        else:
            pair = eligible_pairs[(n - 1) % len(eligible_pairs)] \
                if eligible_pairs else (None, None)
            deep_links.append({
                "target_kind": "subject_site_pair",
                "site_ref": pair[1],
                "subject_ref": pair[0],
                "member_object_ref": None,
            })

    entry: dict[str, Any] = {
        "case_id": f"D10-CASE-{idx:03d}",
        "authority_id": f"D10-AUTH-{idx:03d}",
        "partition": f.get("partition"),
        "signal_definition": {
            "signal_definition_id": f"SYN-D10-DEF-{ridx:03d}",
            "signal_kind": kind,
            "clinical_claim_token": f.get("token"),
            "d10_action": f.get("owner"),
            "required_producer_domains": DEFAULT_REQUIRED_DOMAINS[kind],
        },
        "legal_matrix_row": {
            "row_id": f"SYN-D10-LEGAL-{ridx:03d}",
            "signal_kind": kind if f.get("legal_match", True) else "cross_site_pattern",
            "clinical_claim_token": (f.get("token") if f.get("legal_match", True)
                                     else "d10_cross_site_pattern"),
            "d10_action": (f.get("owner") if f.get("legal_match", True)
                           else "consume_only"),
        },
        "scope_binding": {
            "scope_binding_id": f"SYN-D10-SCOPE-{ridx:03d}",
            "scope_type": f.get("scope_type", "project"),
            "scope_equality_decision": f.get("scope_eq", "exact_match"),
        },
        "project_ref": "SYN-D10-PROJECT-001",
        "run_ref": "SYN-D10-RUN-001",
        "snapshot_ref": "SYN-D10-SNAP-001",
        "mode_contract": _mode_contract_block(ridx, mode_version, f),
        "expected_set": {
            "expected_set_state": es_state,
            "admission_gate_kind": gate_kind,
            "admission_gate_reasons": gate_reasons,
        },
        "analysis_windows": [{
            "analysis_window_stable_id": f"SYN-D10-WIN-{ridx:03d}-{w}",
            "window_instance_id": f"SYN-D10-WIN-{ridx:03d}-{w}-INST",
            "window_definition_id": f"SYN-D10-WD-{ridx:03d}-{w}",
            "window_kind": "calendar_interval",
            "window_state": "closed",
            "cutoff_ref": (f"SYN-D10-CUT-{ridx:03d}" if f.get("change")
                           else None),
        } for w in range(1, int(f.get("wins", 1)) + 1)],
        "stratum": {
            "stratum_contract_id": f"SYN-D10-SC-{ridx:03d}",
            "stratum_key": "overall",
            "stratum_state": "closed",
            "stratum_admission": "admitted",
        },
        "comparison_reference_stable_id": "SYN-D10-REF-OVERALL",
        "analysis_population": {
            "analysis_population_ref": f"SYN-D10-POP-{ridx:03d}",
            "analysis_population_contract_id": f"SYN-D10-POPC-{ridx:03d}",
        },
        "members": members,
        "numerator_ledger": {
            "individual_risk_count": individual,
            "center_pattern_count": pattern,
            "affected_subject_count": n_subject,
            "event_or_outcome_count": int(f.get("num_event", 9)),
            "affected_site_count": int(f.get("num_site", 3)),
            "numerator_member_count": len(set(member_refs)),
        },
        "denominator": {
            "denominator_kind": den_kind,
            "denominator_value": den_value,
            "denominator_unit": {"subject_time": "subject_day",
                                 "exposure_time": "subject_day",
                                 "expected_assessment_opportunities":
                                     "opportunity"}.get(den_kind, "subject"),
            "denominator_state": f.get("den_state", "closed_positive"),
            "exclusion_reason_codes": f.get("den_excl", []),
        },
        "denominator_member_set_hash": sha256_text(
            canonical_json(sorted(den_refs))),
        "time_segments": {
            "count": len(segments),
            "set_hash": sha256_text(canonical_json(sorted(
                segments, key=lambda s: s["segment_id"]))),
        },
        "d09_patterns": d09_patterns,
        "measure_origin": measure_origin,
        "treatment": treatment,
        "visibility": _visibility_block(
            f, members, evaluation, projectable, hidden, dl_eligible,
            visible_n, hidden_count),
        "deep_links": deep_links,
        "query": {
            "decision": f.get("q_decision", "project_delta_present"),
            "covered_member_refs": sorted(set(covered_refs)),
            "uncovered_member_refs": sorted(set(uncovered_refs)),
            "member_query_content_identities": canonical_query_ids,
            "unit_member_set_hash": unit_member_set_hash,
            "coverage_proof_hash": sha256_text(canonical_json({
                "unit_member_refs": sorted(set(member_refs)),
                "covered_member_refs": sorted(set(covered_refs)),
                "uncovered_member_refs": sorted(set(uncovered_refs)),
                "member_query_content_identities": canonical_query_ids,
            })),
            "covered_member_set_hash": sha256_text(
                canonical_json(sorted(set(covered_refs)))),
            "uncovered_member_set_hash": sha256_text(
                canonical_json(sorted(set(uncovered_refs)))),
            "union_member_set_hash": sha256_text(canonical_json(
                sorted(set(covered_refs) | set(uncovered_refs)))),
            "disjoint": not (set(covered_refs) & set(uncovered_refs)),
            "max_query_member_fanout": int(f.get("q_fanout", 100)),
            "pd_wording_state": f.get("q_pd", "not_pd"),
            "member_unlistable": bool(f.get("q_unlistable")),
        },
        "model_evidence": model_evidence,
        "audience_contract": {
            "forbidden_internal_terms": [
                "正式安全性信号", "确证治疗效果", "优效", "非劣",
                "获益-风险裁决", "中心质量差", "中心质量好",
                "typed handoff", "candidate"],
        },
        "source_revisions": source_revisions,
        "source_locator_set_hash": sha256_text(canonical_json(locator_ids)),
        "evidence_refs": [
            {
                "locator_id": locator_ids[0],
                "locator_kind": "synthetic_file",
                "source_file": ("synthetic_source/alt_dataset_%03d.json" % ridx
                                if f.get("evidence_file_alt") else
                                "synthetic_source/dataset_%03d.json" % ridx),
                "row_or_cell_ref": ("sheet:2;row:2" if f.get("evidence_row_alt")
                                    else "sheet:1;row:1"),
                "lineage_ref": f"SYN-D10-LIN-{ridx:03d}-01",
            },
            {
                "locator_id": locator_ids[1] if len(locator_ids) > 1
                else locator_ids[0],
                "locator_kind": "synthetic_file",
                "source_file": ("synthetic_source/alt_dataset_%03d.json" % ridx
                                if f.get("evidence_file_alt") else
                                "synthetic_source/dataset_%03d.json" % ridx),
                "row_or_cell_ref": ("sheet:2;row:3" if f.get("evidence_row_alt")
                                    else "sheet:1;row:2"),
                "lineage_ref": f"SYN-D10-LIN-{ridx:03d}-02",
            },
        ],
        "change": _change_block(ridx, f.get("change")),
        "hotspot_member_ref": (member_refs[0] if f.get("hotspot") else None),
        "authority_hash": "",
    }
    entry["authority_hash"] = content_hash(entry, "authority_hash")
    return entry


# ---------------------------------------------------------------------------
# Assembly / validation / CLI
# ---------------------------------------------------------------------------
def assemble_authority() -> dict[str, Any]:
    entries = [_hydrate(row) for row in AUTHORITY_ROWS]
    audit = {
        "row_count": len(entries),
        "bijection_ok": len({e["case_id"] for e in entries}) == len(entries)
        and len({e["authority_id"] for e in entries}) == len(entries),
        "sorted_case_ids": sorted(e["case_id"] for e in entries),
        "duplicate_case_ids": [],
        "missing_case_ids": [],
    }
    registry: dict[str, Any] = {
        "authority_id": AUTHORITY_ID,
        "schema_version": SCHEMA_VERSION,
        "contract_semantic_hash": CONTRACT_SEMANTIC_HASH,
        "case_count": len(entries),
        "generator_hash": _generator_code_hash(),
        "entries": entries,
        "bijection_audit": audit,
        "content_hash": "",
    }
    registry["content_hash"] = content_hash(registry, "content_hash")
    return registry


def validate_authority(registry: dict[str, Any]) -> None:
    expect_exact_keys(registry, AUTHORITY_TOP_KEYS, "authority top-level")
    if registry["authority_id"] != AUTHORITY_ID:
        raise AuthorityError("schema_parse", "schema_error",
                             "authority_id mismatch")
    if registry["case_count"] != REQUIRED_TOTAL:
        raise AuthorityError("schema_parse", "schema_error",
                             "authority case_count != 312")
    entries = registry["entries"]
    if len(entries) != registry["case_count"]:
        raise AuthorityError("schema_parse", "schema_error",
                             "authority entries count mismatch")
    seen: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        expect_exact_keys(entry, ENTRY_KEYS, f"authority entry {index}")
        if entry["case_id"] != f"D10-CASE-{index:03d}":
            raise AuthorityError("schema_parse", "id_mismatch",
                                 f"entry {index} case_id mismatch")
        if entry["case_id"] in seen:
            raise AuthorityError("schema_parse", "duplicate",
                                 f"duplicate entry {entry['case_id']}")
        seen.add(entry["case_id"])
        expect_exact_keys(entry["signal_definition"], SIGNAL_DEFINITION_KEYS,
                          f"{entry['case_id']} signal_definition")
        require_enum(entry["signal_definition"]["signal_kind"], SIGNAL_KINDS,
                     "signal_kind")
        expect_exact_keys(entry["legal_matrix_row"], LEGAL_MATRIX_ROW_KEYS,
                          f"{entry['case_id']} legal_matrix_row")
        expect_exact_keys(entry["scope_binding"], SCOPE_BINDING_KEYS,
                          f"{entry['case_id']} scope_binding")
        expect_exact_keys(entry["mode_contract"], MODE_CONTRACT_KEYS,
                          f"{entry['case_id']} mode_contract")
        if not sha256_hex(entry["mode_contract"]["mode_contract_content_hash"]):
            raise AuthorityError("schema_parse", "schema_error",
                                 f"{entry['case_id']} mode content hash malformed")
        expect_exact_keys(entry["expected_set"], EXPECTED_SET_KEYS,
                          f"{entry['case_id']} expected_set")
        for window in entry["analysis_windows"]:
            expect_exact_keys(window, WINDOW_KEYS,
                              f"{entry['case_id']} window")
        expect_exact_keys(entry["stratum"], STRATUM_KEYS,
                          f"{entry['case_id']} stratum")
        expect_exact_keys(entry["analysis_population"], ANALYSIS_POPULATION_KEYS,
                          f"{entry['case_id']} analysis_population")
        for member in entry["members"]:
            expect_exact_keys(member, MEMBER_KEYS, f"{entry['case_id']} member")
            require_enum(member["member_kind"], MEMBER_KINDS, "member_kind")
        expect_exact_keys(entry["numerator_ledger"], NUMERATOR_LEDGER_KEYS,
                          f"{entry['case_id']} numerator_ledger")
        expect_exact_keys(entry["denominator"], DENOMINATOR_KEYS,
                          f"{entry['case_id']} denominator")
        require_enum(entry["denominator"]["denominator_kind"],
                     DENOMINATOR_KINDS, "denominator_kind")
        expect_exact_keys(entry["time_segments"], TIME_SEGMENTS_KEYS,
                          f"{entry['case_id']} time_segments")
        for d09 in entry["d09_patterns"]:
            expect_exact_keys(d09, D09_PATTERN_KEYS, f"{entry['case_id']} d09_pattern")
        mo = entry["measure_origin"]
        if mo is not None:
            expect_exact_keys(mo, MEASURE_ORIGIN_KEYS,
                              f"{entry['case_id']} measure_origin")
            member_refs = [m["member_ref"] for m in entry["members"]]
            for key in ("verified_risk_refs", "distinct_risk_refs",
                        "ambiguous_risk_refs", "candidate_risk_refs"):
                refs = mo[key]
                if refs != sorted(set(refs)):
                    raise AuthorityError(
                        "schema_parse", "noncanonical_origin_partition",
                        f"{entry['case_id']} {key} is not sorted-unique")
                if any(ref not in member_refs for ref in refs):
                    raise AuthorityError(
                        "schema_parse", "origin_ref_external",
                        f"{entry['case_id']} {key} contains an unknown member")
            verified = set(mo["verified_risk_refs"])
            distinct = set(mo["distinct_risk_refs"])
            ambiguous = set(mo["ambiguous_risk_refs"])
            candidate = set(mo["candidate_risk_refs"])
            if candidate != verified | distinct | ambiguous or \
                    verified & distinct or verified & ambiguous or \
                    distinct & ambiguous:
                raise AuthorityError(
                    "schema_parse", "origin_partition_not_closed",
                    f"{entry['case_id']} origin partition is not closed/disjoint")
            expected_origin = _derive_origin_decision(
                sorted(verified), sorted(distinct), sorted(ambiguous))
            if mo["origin_decision"] == "wrong_scope" and not candidate:
                expected_origin = "wrong_scope"
            if mo["origin_decision"] != expected_origin:
                raise AuthorityError(
                    "schema_parse", "origin_decision_not_derived",
                    f"{entry['case_id']} origin_decision is not derived")
            for key, value in (
                    ("verified_ref_set_hash", sorted(verified)),
                    ("distinct_ref_set_hash", sorted(distinct)),
                    ("ambiguous_ref_set_hash", sorted(ambiguous)),
                    ("candidate_ref_set_hash", sorted(candidate))):
                if mo[key] != sha256_text(canonical_json(value)):
                    raise AuthorityError(
                        "schema_parse", "origin_hash_mismatch",
                        f"{entry['case_id']} {key} mismatch")
        expect_exact_keys(entry["treatment"], TREATMENT_KEYS,
                          f"{entry['case_id']} treatment")
        expect_exact_keys(entry["visibility"], VISIBILITY_KEYS,
                          f"{entry['case_id']} visibility")
        for dl in entry["deep_links"]:
            expect_exact_keys(dl, DEEP_LINK_KEYS, f"{entry['case_id']} deep_link")
        expect_exact_keys(entry["query"], QUERY_KEYS, f"{entry['case_id']} query")
        query = entry["query"]
        member_refs = sorted(set(m["member_ref"] for m in entry["members"]))
        covered = query["covered_member_refs"]
        uncovered = query["uncovered_member_refs"]
        if covered != sorted(set(covered)) or uncovered != sorted(set(uncovered)):
            raise AuthorityError("schema_parse", "query_noncanonical",
                                 f"{entry['case_id']} query refs are not sorted-unique")
        # Some catalog rows intentionally retain a truncated/overlapping
        # Query partition as a negative fixture.  The independent verifier
        # owns the closed-union decision; authority validation only checks
        # exact schema and canonical identity-bearing encodings here.
        identities = query["member_query_content_identities"]
        expected_ids = [sha256_text(canonical_json({"member_ref": ref}))
                        for ref in covered]
        # A negative fixture may intentionally carry an identity cardinality
        # mismatch.  Keep authority parsing structural here; the independent
        # verifier owns exact identity/membership acceptance.
        if len(identities) == len(covered) and identities != expected_ids:
            raise AuthorityError("schema_parse", "query_identity_mismatch",
                                 f"{entry['case_id']} query identities mismatch")
        expected_unit_hashes = {
            sha256_text(canonical_json(member_refs)),
            _content_sha(
                f"tampered-unitmembers:{entry['case_id'].split('-')[-1]}")}
        if query["unit_member_set_hash"] not in expected_unit_hashes:
            raise AuthorityError("schema_parse", "query_unit_hash_mismatch",
                                 f"{entry['case_id']} query unit hash mismatch")
        proof = {
            "unit_member_refs": member_refs,
            "covered_member_refs": covered,
            "uncovered_member_refs": uncovered,
            "member_query_content_identities": identities,
        }
        if query["coverage_proof_hash"] != sha256_text(canonical_json(proof)):
            raise AuthorityError("schema_parse", "query_proof_mismatch",
                                 f"{entry['case_id']} query coverage proof mismatch")
        me = entry["model_evidence"]
        if me is not None:
            expect_exact_keys(me, MODEL_EVIDENCE_KEYS,
                              f"{entry['case_id']} model_evidence")
            if me["ensemble_size"] == 1 and \
                    me["permitted_leaf"] != "model_candidate_only":
                raise AuthorityError(
                    "schema_parse", "ensemble1_consensus",
                    f"{entry['case_id']} ensemble=1 must never permit "
                    "consensus leaves")
            if me["source_revision_content_pairs"] != sorted(
                    me["source_revision_content_pairs"],
                    key=lambda pair: (pair["revision_id"], pair["content_hash"])):
                raise AuthorityError("schema_parse", "model_source_noncanonical",
                                     f"{entry['case_id']} model source pairs not canonical")
            if me["source_refs"] != sorted(set(me["source_refs"])):
                raise AuthorityError("schema_parse", "model_source_refs_noncanonical",
                                     f"{entry['case_id']} model source refs not canonical")
            if me["member_analysis_refs"] != sorted(set(me["member_analysis_refs"])):
                raise AuthorityError("schema_parse", "model_analysis_refs_noncanonical",
                                     f"{entry['case_id']} model analysis refs not canonical")
        expect_exact_keys(entry["audience_contract"], AUDIENCE_CONTRACT_KEYS,
                          f"{entry['case_id']} audience_contract")
        for rev in entry["source_revisions"]:
            expect_exact_keys(rev, SOURCE_REVISION_KEYS,
                              f"{entry['case_id']} source_revision")
        for ref in entry["evidence_refs"]:
            expect_exact_keys(ref, EVIDENCE_REF_KEYS,
                              f"{entry['case_id']} evidence_ref")
        ch = entry["change"]
        if ch is not None:
            expect_exact_keys(ch, CHANGE_AUTHORITY_KEYS,
                              f"{entry['case_id']} change authority")
        if not sha256_hex(entry["authority_hash"]):
            raise AuthorityError("schema_parse", "schema_error",
                                 f"{entry['case_id']} authority_hash malformed")
        if entry["authority_hash"] != content_hash(entry, "authority_hash"):
            raise AuthorityError("schema_parse", "stale_hash",
                                 f"{entry['case_id']} authority_hash mismatch")
    audit = registry["bijection_audit"]
    if audit["row_count"] != len(entries) or not audit["bijection_ok"]:
        raise AuthorityError("bijection", "audit_failed",
                             "authority bijection audit failed")
    if registry["content_hash"] != content_hash(registry, "content_hash"):
        raise AuthorityError("schema_parse", "stale_hash",
                             "authority content hash mismatch")


def render(verbose: bool = True) -> dict[str, Any]:
    def log(message: str) -> None:
        if verbose:
            print(message)

    validate_contract()
    first = assemble_authority()
    second = assemble_authority()
    if canonical_json(first) != canonical_json(second):
        raise AuthorityError("replay", "drift",
                             "double-pass byte mismatch (nondeterministic)")
    validate_authority(first)
    payload = canonical_json(first).encode("utf-8")
    AUTHORITY.write_bytes(payload)
    reloaded = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if canonical_json(reloaded).encode("utf-8") != payload:
        raise AuthorityError("replay", "drift", "reload byte mismatch")
    log(f"wrote {AUTHORITY} ({len(payload)} bytes, "
        f"content_hash {first['content_hash']}, "
        f"generator_hash {first['generator_hash']})")
    return first


def check(verbose: bool = True) -> int:
    def log(message: str) -> None:
        if verbose:
            print(message)

    try:
        validate_contract()
        first = assemble_authority()
        second = assemble_authority()
        if canonical_json(first) != canonical_json(second):
            log("FAIL: two fresh generations are NOT byte-identical")
            return 1
        log("OK: two fresh generations are byte-identical")
        if not AUTHORITY.exists():
            log(f"FAIL: authority artifact missing at {AUTHORITY}")
            return 1
        on_disk = AUTHORITY.read_bytes()
        if on_disk != canonical_json(first).encode("utf-8"):
            log("FAIL: on-disk authority differs from a fresh generation")
            return 1
        log("OK: on-disk authority matches a fresh generation")
        loaded = json.loads(on_disk.decode("utf-8"))
        validate_authority(loaded)
        log(f"OK: authority validates (schema, bijection, hash, "
            f"case coverage {loaded['case_count']})")
        return 0
    except AuthorityError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="D10 fixture authority registry generator")
    parser.add_argument("mode", nargs="?", default="check",
                        choices=("generate", "check"),
                        help="generate: write authority; check: verify determinism")
    parser.add_argument("--quiet", action="store_true", help="suppress output")
    args = parser.parse_args()
    try:
        if args.mode == "generate":
            render(verbose=not args.quiet)
            return 0
        return check(verbose=not args.quiet)
    except AuthorityError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
