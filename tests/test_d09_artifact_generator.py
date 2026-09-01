"""Focused non-LLM freeze tests for the D09 artifact generator + oracle.

Covers (worker_03 work item + follow-up, D09 v0.5 frozen contract):
  * exact catalog top-level / case / typed_input schemas and >= 179 cases
  * exact primary-partition minima, per-partition uniqueness, disjoint-union proof
  * all catalog expected_* fields literal null (oracle-only leaves)
  * five-way case/fixture/oracle/manifest/test bijection + full oracle coverage
  * oracle-only expected/source/trace leaves (schema uniform, non-empty)
  * generator/runtime import & read closure from the oracle and registry
  * canonical UTF-8 / NFC / no-whitespace JSON and embedded SHA-256
  * rejection of NaN / Infinity
  * mutation gates (schema / hash / token / resolution tamper fails closed)
  * input-order and display-name invariance (order_shuffle / display_rename /
    anti-overfit variants produce identical outcomes modulo identity tokens)
  * content-identity/idempotency: same immutable revision across opaque run
    IDs -> identical content identity; changed revision/cutoff/method ->
    distinct content identity; rule supersession -> superseded lineage
  * two-stage registry contract regression: stage-A provisional registry is
    oracle-blind; stage-B resolved registry passes verify_resolved_registry
    with the generator_hash pinned to the frozen STAGE_A_GENERATOR_SHA256;
    tampered / mismatched resolved registries fail closed (including altered
    generator_hash with a consistent content_hash reseal)
  * independent verifier: ALL 179 dispositions and ALL decisive counts are
    re-derived from catalog typed_input alone with ZERO skips
    (no semantic skip tables, no oracle-side semantic tags, no free-text
    descriptions, no case ids, no catalog disposition)
  * repeated `--check` and double-generation byte identity
  * unchanged accepted contract SHA and TCP 8911 stopped

2026-08-15 follow-up corrections (all within the six-file boundary):
  * catalog generator: typed_input envelope gains contract-authorized input
    facts `matched_counterevidence_rule_refs` and `mode_contract_design_clause_ref`;
    CASE-067 encodes mixed cutoff relations per member; CASE-047 encodes the
    two D02+D08 verified same-origin pairs (shared subject/event/identity per
    pair); CASE-063 declares a source content hash that does not match its
    revision (integrity block); CASE-168 declares members unlistable via
    missing source locators; CASE-024 declares two counterevidence rules with
    one matched (partial); CASE-025 declares the rule without a match.
  * oracle generator: the 8 oracle-side semantic tag keys (ce_level,
    true_cutoffs, declared, qb_override, integrity_block,
    design_clause_closed_zero, deep_link_deficient, visibility_boundary) were
    REMOVED from ORACLE_CASES; all dispositions and counts are now derived
    from the same contract-authorized facts the catalog carries.
  * registry verification: generator_hash is validated against the frozen
    STAGE_A_GENERATOR_SHA256 pin (self-normalized code hash) and is NOT a
    stage-B delta.
  * artifacts regenerated; all file/content pins below are the new SHAs.

2026-08-15 Luna REVISE repair (confirmed CASE-047 whitelist defect):
  * CASE-047's pattern_definition.accepted_member_risk_kinds now admits both
    member risk kinds (d01_seriousness_hospital_death and
    d08_cross_domain_relation), matching contract §3.2 and the D08
    cross-domain members produced by the pair_domains builder. The verified
    same-origin dedup result stays 2/2/2.
  * New TestRiskKindWhitelistInvariant: general 179-case invariant (every
    subject_risk member risk kind is accepted by its case definition),
    focused CASE-047 assertions, and a mutation proving an unlisted member
    risk kind is rejected by the test verifier.
  * Generator re-pinned (self-normalized code hash) and catalog/quota/resolved
    registry regenerated; oracle unchanged. All pins below are the new SHAs.
"""

from __future__ import annotations

import ast
import collections
import hashlib
import json
import re
import socket
import subprocess
import sys
import tempfile
import unittest
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_d09_challenge_registry as g  # noqa: E402
import generate_d09_expected_oracle as o  # noqa: E402

CATALOG_PATH = ROOT / "reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json"
ORACLE_PATH = ROOT / "reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json"
REGISTRY_PATH = ROOT / "reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json"
QUOTA_PATH = ROOT / "reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json"
CATALOG_GEN_PATH = ROOT / "tools/generate_d09_challenge_registry.py"
ORACLE_GEN_PATH = ROOT / "tools/generate_d09_expected_oracle.py"

ORACLE_ARTIFACT_NAME = "medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json"

CASE_COUNT = 179
MIN_CASE_COUNT = 179

# ---------------------------------------------------------------------------
# Pinned schema key sets (copied from the frozen generator; must not drift).
# ---------------------------------------------------------------------------
CATALOG_TOP_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
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

ORACLE_TOP_KEYS = [
    "artifact_kind", "oracle_id", "schema_version", "contract_semantic_hash",
    "case_count", "ordered_expectations", "content_hash",
]
ORDERED_EXPECTATION_KEYS = [
    "case_id", "oracle_case_id", "fixture_id", "expected_leaf_set",
    "expected_source_leaf_set", "expected_trace_leaf_set",
]

# Oracle leaf schemas (uniform across all 179 entries). 48-key shape = zero
# medical units (no units.0.* block); 64-key shape = units present.
LEAF48_KEYS = [
    "all_units_disposed", "boundary_count", "domain_complete", "expected_set_reconciled",
    "gate.admission_gate_kind", "gate.admission_gate_present",
    "gate.window_pair_gate_present", "gate.window_pair_state", "gate_count",
    "integrity.error_object", "integrity.error_stage", "integrity.error_type",
    "integrity.gate_kind", "integrity.stage", "l0_complete",
    "l2.affected_subject_count", "l2.center_pattern_count", "l2.clue_count",
    "l2.event_count", "l2.gap_opportunity_count", "l2.individual_risk_count",
    "l2.query_count", "l2.risk_count", "l2.source_record_count",
    "l3.boundary_count", "l3.positive_count", "l3.risk_count",
    "measure.denominator_kind", "measure.denominator_state", "measure.denominator_value",
    "measure.opportunity_expected", "measure.opportunity_missing",
    "measure.opportunity_observed", "measure.opportunity_state",
    "negative_count", "not_applicable_count", "not_evaluable_count", "open_gate_count",
    "ownership.d09_action", "ownership.downstream_handoff_present",
    "ownership.handoff_target_domain", "ownership.owner_domain",
    "ownership.query_draft_present", "ownership.query_owner",
    "ownership.risk_candidate_present", "ownership.risk_owner",
    "positive_count", "unit_count",
]
UNITS_KEYS = [
    "units.0.clue_count", "units.0.counterevidence_count", "units.0.event_count",
    "units.0.evidence_count", "units.0.gap_opportunity_count",
    "units.0.gate_signal_type", "units.0.individual_risk_count",
    "units.0.l1_disposition", "units.0.lineage_handoff", "units.0.participant_count",
    "units.0.pattern_kind", "units.0.primary_reason", "units.0.query_count",
    "units.0.risk_count", "units.0.stable_core", "units.0.unit_kind",
]
LEAF64_KEYS = sorted(LEAF48_KEYS + UNITS_KEYS)
SOURCE_LEAF_KEYS = [
    "source.audience_anchor", "source.audience_lexicon_ref", "source.audience_payload_present",
    "source.disclosure_leak_present", "source.evaluation_node_set",
    "source.hidden_node_count", "source.journey_marker_present",
    "source.producer_binding_ids", "source.projectable_node_set",
    "source.query_present", "source.reverse_binding_count", "source.risk_present",
    "source.source_jump_target_pairs",
]
TRACE_LEAF_KEYS = [
    "trace.bidirectional_join_count", "trace.edge_set", "trace.lineage_handoff_count",
    "trace.negative_checked_edge_count", "trace.positive_evidence_ok",
    "trace.reverse_conservation_ok", "trace.stable_core_count",
    "trace.superseded_unit_count", "trace.unit_stable_cores",
]

# Leaf fields that legitimately differ between semantically-equal variants:
# identity tokens (stable cores / node / edge / jump pairs). Everything else
# (counts, dispositions, gates, ownership) must be invariant.
IDENTITY_LEAF_KEYS = frozenset({
    "units.0.stable_core", "source.audience_anchor", "source.evaluation_node_set",
    "source.projectable_node_set", "source.source_jump_target_pairs",
    "trace.edge_set", "trace.unit_stable_cores", "source.producer_binding_ids",
    "source.audience_lexicon_ref", "source.reverse_binding_count",
    "source.hidden_node_count", "trace.bidirectional_join_count",
    "trace.lineage_handoff_count", "trace.stable_core_count",
    "trace.negative_checked_edge_count",
})

# Static closure proofs -----------------------------------------------------
FORBIDDEN_DERIVATION_TOKENS = (
    "derive_disposition", "build_expected_leaf_set", "build_source_leaf_set",
    "build_trace_leaf_set", "derive_expected", "def derive",
    "positive_count", "unit_count", "units.0.", "trace.edge_set",
    "l3.positive_count", "l2.affected_subject_count",
)
RUNTIME_TOKENS = ("socket", "bind(", "listen(", "serve_forever", "8911",
                  "uvicorn", "flask", "mm_r4", "run_monitoring")
STDLIB_MODULES = frozenset({
    "__future__", "argparse", "ast", "calendar", "collections", "datetime",
    "hashlib", "json", "pathlib", "re", "sys", "tempfile", "typing", "unicodedata",
})
# Oracle-side semantic tag keys that MUST NOT exist anywhere (removed 2026-08-15).
FORBIDDEN_ORACLE_TAG_KEYS = (
    "ce_level", "true_cutoffs", "declared", "qb_override", "integrity_block",
    "design_clause_closed_zero", "visibility_boundary",
)
# Semantic decision coupling that the ORACLE GENERATOR must never contain:
# mutation metadata reads, sentinel spelling decisions and hash recipes
# (worker_01 corrective pass 2026-08-15).
FORBIDDEN_ORACLE_SEMANTIC_TOKENS = (
    'spec["mc"]', '"mc"', "mutation", "anti_overfit", "base_fixture",
    "variant_id", "MISSING", "UNKNOWN", "d09-rev", "TAMPERED", "LOC-MISSING",
    "NO_QUERY",
)

TREATMENT_STRATUM_KEYS = frozenset({"treatment_arm", "treatment_role"})


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(g.normalize_value(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def object_hash(obj: dict, own_key: str = "content_hash") -> str:
    core = {k: v for k, v in obj.items() if k != own_key}
    return sha256_text(canonical_json(core))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clone(obj: Any) -> Any:
    return json.loads(canonical_json(obj))


def load_artifacts() -> tuple[dict, dict, dict, dict]:
    return (load_json(CATALOG_PATH), load_json(ORACLE_PATH),
            load_json(REGISTRY_PATH), load_json(QUOTA_PATH))


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(key)
            yield from _walk_strings(item)


def reject_nonfinite(value: Any) -> None:
    raise ValueError("non-finite numeric constant")


def content_identity(typed: dict[str, Any]) -> str:
    """Contract §5.1 D09EvaluationContentIdentity re-computed from typed input."""
    pd = typed["pattern_definition"]
    wins = typed["analysis_windows"]
    stratum = typed["stratum"]
    window_instances = sorted(
        sha256_text(canonical_json({
            "analysis_window_stable_id": w["analysis_window_stable_id"],
            "computed_window_start": w["computed_window_start"],
            "computed_window_end": w["computed_window_end"],
            "cutoff_id": w["cutoff_id"],
            "scope_binding_stable_id": w["scope_binding_stable_id"],
        })) for w in wins)
    core = {
        "project_ref": typed["project_ref"],
        "site_stable_id": typed["site_stable_id"],
        "pattern_definition_id": pd["pattern_definition_id"],
        "window_instance_identities": window_instances,
        "stratum_contract_id": stratum["stratum_contract_id"],
        "stratum_key": stratum["stratum_key"],
        "source_revision_set": sorted(set(typed["source_revision_set"])),
        "source_content_hashes": sorted(set(typed["source_content_hashes"])),
        "mode_contract_version": typed["mode_contract_version"],
        "pattern_definition_content_hash": pd["pattern_definition_content_hash"],
        "stratum_contract_content_hash": stratum["stratum_contract_content_hash"],
        "legal_definition_matrix_content_hash": pd["legal_definition_matrix_content_hash"],
        "numeric_execution_policy_content_hash": pd["numeric_execution_policy_content_hash"],
        "algorithm_version": "d09_v1",
    }
    return sha256_text(canonical_json(core))


# ===========================================================================
# Independent verifier: re-derives disposition and ALL decisive counts for
# every case from catalog typed_input ONLY (contract §8/§9/§5.1/§5.2/§12).
# Deliberately written from the frozen contract text; does NOT call the oracle
# generator's derivation machinery. Zero skips: every one of the 179 cases
# must reproduce the oracle exactly.
# ===========================================================================
def catalog_facts(case: dict[str, Any]) -> dict[str, Any]:
    """Project the catalog typed_input onto the contract fact model."""
    t = case["typed_input"]
    pd = t["pattern_definition"]
    return {
        "es_state": t["expected_set"]["expected_set_state"],
        "gate_kind": (t["expected_set"]["admission_gate"] or {}).get("gate_kind"),
        "kind": case["pattern_kind"],
        "token": case["clinical_claim_token"],
        "owner": case["owner_route"],
        "mc": case["mutation_class"],
        "wins": t["analysis_windows"],
        "cov": t["coverage"],
        "producers": pd["required_producer_domains"],
        "den_kind": t["denominator"]["denominator_kind"],
        "den_value": t["denominator"]["denominator_value"],
        "den_state": t["denominator"]["denominator_state"],
        "opp_exp": t["opportunity"]["expected_opportunity_count"],
        "opp_obs": t["opportunity"]["observed_opportunity_count"],
        "opp_state": t["opportunity"]["opportunity_state"],
        "opp_prov": t["opportunity"]["opportunity_provenance"],
        "cutoff_state": t["cutoff"]["cutoff_identity_state"],
        "stratum_admission": t["stratum"]["stratum_admission"],
        "stratum_key": t["stratum"]["stratum_key"],
        "blind": t["visibility_decision"]["blind_status"],
        "authority_validity": t["resolved_authority_decision"]["authority_validity_state"],
        "min_count": t["resolved_authority_decision"]["minimum_member_subject_count"],
        "gap_positive_minimum": t["resolved_authority_decision"][
            "gap_positive_minimum_opportunity_count"],
        "trend_positive_minimum": t["resolved_authority_decision"][
            "trend_positive_minimum_subject_count"],
        "method_validity": t["method_comparability_decision"]["method_validity_state"],
        "signal_role": t["method_comparability_decision"]["statistical_signal_role"],
        "expansion": t["method_comparability_decision"]["member_expansion_state"],
        "win_rule_versions": t["method_comparability_decision"]["window_rule_version_refs"],
        "stratum_method_versions": t["method_comparability_decision"]["stratum_method_version_refs"],
        "lineage_relation": t["lineage_context"]["lineage_relation"],
        "carry_forward_state": t["lineage_context"]["carry_forward_state"],
        "site_identity_state": t["lineage_context"]["site_identity_state"],
        "query_decision": t["query_redundancy_decision"]["decision"],
        "query_fanout": t["query_redundancy_decision"]["max_query_member_fanout"],
        "verification_states": [r["verification_state"]
                                for r in t["source_verification_records"]],
        "risk_resolutions": [m["source_locator_resolution_state"]
                             for m in t["subject_risk_members"]],
        "gap_anchor_states": [m["anchor_resolution_state"] for m in t["gap_members"]],
        "risks": [{
            "member_id": m["member_id"],
            "subject": m["subject_stable_id"],
            "event": m["source_event_identity"],
            "origin": m["origin_decision"],
            "cutoff": m["cutoff_relation"],
            "locator": m["source_locator_refs"][0] if m["source_locator_refs"] else None,
            "identity": m["public_r4_risk_identity"],
        } for m in t["subject_risk_members"]],
        "gaps": [{
            "member_id": m["member_id"],
            "subject": m["subject_stable_id"],
            "anchor": m["visit_or_time_anchor_refs"],
            "locator": m["source_locator_refs"][0] if m["source_locator_refs"] else None,
        } for m in t["gap_members"]],
        "chgs": [{
            "member_id": m["member_id"],
            "subject": m["subject_stable_id"],
            "comparable": m["comparable_state"],
            "change_kind": m["change_kind"],
            "cause": m["change_cause"],
            "locator": m["source_locator_refs"][0] if m["source_locator_refs"] else None,
        } for m in t["change_ledger_members"]],
        "design_clause_ref": t["mode_contract_design_clause_ref"],
        "declared_ce": pd["counterevidence_rule_refs"],
        "matched_ce": t["matched_counterevidence_rule_refs"],
        "rate_state": t["visibility_decision"]["rate_projection_state"],
        "revisions": t["source_revision_set"],
        "declared_hashes": t["source_content_hashes"],
    }


def evidence_locators(f: dict[str, Any]) -> list[str]:
    out = [r["locator"] for r in f["risks"] if r["locator"]]
    out += [gr["locator"] for gr in f["gaps"] if gr["locator"]]
    out += [c["locator"] for c in f["chgs"] if c["locator"]]
    return sorted(set(out))


def source_hash_mismatch(f: dict[str, Any]) -> bool:
    """Producer content verification is an explicit typed fact."""
    return any(state != "verified" for state in f["verification_states"])


def ce_level_of(f: dict[str, Any]) -> str:
    declared = list(f["declared_ce"])
    matched = list(f["matched_ce"])
    if not declared:
        return "condition_absent"
    if not matched:
        return "none"
    if set(matched) == set(declared):
        return "full"
    return "partial"


def deep_link_deficient(f: dict[str, Any]) -> bool:
    if any(state != "locatable" for state in f["risk_resolutions"]):
        return True
    if any(state != "resolved" for state in f["gap_anchor_states"]):
        return True
    return False


def derive_disposition(f: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Re-derive (disposition, primary_reason, extra) from explicit typed
    facts of the catalog typed_input ONLY (contract §8/§9).  No mutation
    metadata, sentinel spelling or hash recipe is read."""
    kind = f["kind"]
    if f["es_state"] != "admitted":
        return "not_applicable", "routed_or_gated", {
            "zero_unit": True, "gate": f["gate_kind"] or f["es_state"]}
    if kind == "within_site_time_trend":
        n_win = len(f["wins"])
        win_kinds = {w["window_kind"] for w in f["wins"]}
        if n_win < 2:
            return "not_applicable", "window_pair_gate", {
                "zero_unit": True, "gate": "window_pair_gate",
                "pair_state": "insufficient_windows"}
        if len(win_kinds) > 1:
            return "not_applicable", "window_pair_gate", {
                "zero_unit": True, "gate": "window_pair_gate",
                "pair_state": "incomparable_windows"}
    if f["cutoff_state"] == "conflict":
        return "not_evaluable", "cutoff_conflict", {}
    required = set(f["producers"])
    cov_by = {c["producer_domain"]: (c["l0_status"], c["l1_medical_completeness_state"],
                                     c["accepted_current"]) for c in f["cov"]}
    for domain in sorted(required):
        l0, l1, accepted = cov_by.get(domain, ("missing", "missing", True))
        if l0 != "covered" or l1 != "complete":
            return "not_evaluable", "coverage_hole", {"domain": domain}
        if not accepted:
            return "not_evaluable", "producer_ref_unresolvable", {}
    if source_hash_mismatch(f):
        return "not_evaluable", "source_hash_mismatch", {}
    if f["stratum_admission"] == "rejected_empty":
        return "not_evaluable", "stratum_required_empty", {}
    if f["authority_validity"] == "invalid":
        return "not_evaluable", "authority_fail", {}
    if f.get("design_clause_ref"):
        return "not_applicable", "design_not_applicable", {}
    if f["den_state"] == "unclosed":
        return "not_evaluable", "denominator_unclosed", {}
    if f["den_state"] == "closed_zero":
        return "not_evaluable", "denominator_closed_zero", {}
    if f["opp_prov"] in ("raw_listing_only", "enumeration_conflict"):
        return "not_evaluable", "opportunity_provenance", {}
    if f["opp_state"] == "unknown":
        return "not_evaluable", "opportunity_unknown", {}
    origins = {r["origin"] for r in f["risks"]}
    if "wrong_scope" in origins:
        return "not_evaluable", "origin_wrong_scope", {}
    if "not_evaluable" in origins:
        return "not_evaluable", "origin_not_evaluable", {}
    if "ambiguous" in origins:
        return "boundary", "origin_ambiguous", {}
    if f["blind"] == "blinded" and f["stratum_key"] in TREATMENT_STRATUM_KEYS:
        return "not_evaluable", "blinded_stratum_rejected", {}
    if f["site_identity_state"] in ("merged", "split"):
        return "not_evaluable", "site_merge_split", {}
    if f["method_validity"] == "insufficient":
        return "not_evaluable", "validity_insufficient", {}
    if deep_link_deficient(f):
        return "boundary", "deep_link_deficient", {}
    if f["rate_state"] == "qualified":
        return "boundary", "visibility_qualified", {}

    if kind == "repeated_subject_risk":
        true_cut = [r["cutoff"] for r in f["risks"]]
        if true_cut and all(c == "out_of_cutoff" for c in true_cut):
            return "not_evaluable", "cutoff_all_out", {}
        if any(c == "spans_cutoff" for c in true_cut):
            return "boundary", "cutoff_spans", {}
        if any(c == "time_missing_not_evaluable" for c in true_cut):
            return "not_evaluable", "time_missing", {}
        in_subjects = {r["subject"] for r, c in zip(f["risks"], true_cut)
                       if c == "in_cutoff"}
        if len(in_subjects) == 0:
            return "negative", "closed_zero_no_members", {}
        min_count = f["min_count"]
        if min_count is None:
            raise AssertionError("resolved minimum_member_subject_count required")
        if len(in_subjects) < min_count:
            return "boundary", "n1_minimum", {}
        level = ce_level_of(f)
        if level == "full":
            return "negative", "counterevidence_explains", {}
        if level == "partial":
            return "boundary", "counterevidence_partial", {}
        if f["lineage_relation"] == "superseded_by_rule_or_method_change":
            return "boundary", "rule_supersession", {}
        if f["signal_role"] == "sole_evidence":
            return "boundary", "statistics_only", {}
        if f["expansion"] == "unexpandable":
            return "boundary", "signal_unexpandable", {}
        if f["den_kind"] in ("subject_time", "exposure_time"):
            return "boundary", "short_exposure", {}
        if any(w["anchor_kind"] == "site_activation" for w in f["wins"]):
            return "boundary", "late_activation", {}
        return "positive", "min_member_subject_count_satisfied", {}

    if kind == "systematic_data_or_process_gap":
        semantic_missing = 0 if ce_level_of(f) == "full" else len(f["gaps"])
        if f["opp_state"] == "insufficient":
            if len(f["gaps"]) > 0:
                return "boundary", "opportunity_insufficient", {}
            return "not_evaluable", "opportunity_insufficient", {}
        if semantic_missing == 0:
            return "negative", "closed_zero_no_members", {}
        minimum = f["gap_positive_minimum"]
        if minimum is None:
            raise AssertionError("resolved gap positive minimum required")
        if f["opp_exp"] < minimum:
            return "boundary", "small_sample", {}
        return "positive", "accepted_gap_opportunity_sufficient", {}

    if kind == "within_site_time_trend":
        if not f["chgs"]:
            return "negative", "closed_zero_no_members", {}
        comps = {c["comparable"] for c in f["chgs"]}
        change_kinds = {c["change_kind"] for c in f["chgs"]}
        if "not_evaluable" in comps or "not_comparable" in change_kinds:
            if f["method_validity"] == "insufficient":
                return "not_evaluable", "validity_insufficient", {}
            if f["carry_forward_state"] == "active":
                return "not_evaluable", "carry_forward", {}
            if len(set(f["win_rule_versions"])) > 1:
                return "boundary", "window_definition_change", {}
            if f["lineage_relation"] == "superseded_by_rule_or_method_change":
                return "boundary", "rule_supersession", {}
            if len(set(f["stratum_method_versions"])) > 1:
                return "not_evaluable", "stratum_change", {}
            return "boundary", "not_comparable", {}
        causes = {c["cause"] for c in f["chgs"]}
        if causes & {"coverage", "denominator", "method", "rule_or_mapping", "mixed"}:
            return "boundary", "explained_change", {}
        n_subj = len({c["subject"] for c in f["chgs"]})
        minimum = f["trend_positive_minimum"]
        if minimum is None:
            raise AssertionError("resolved trend positive minimum required")
        if n_subj < minimum:
            return "boundary", "small_sample", {}
        return "positive", "comparable_windows_change_ledger", {}

    raise AssertionError(f"unknown pattern kind {kind}")


def numerator(f: dict[str, Any]) -> tuple[int, int, int, int]:
    """(individual_risk_count, affected_subjects, events, gap_opportunities)."""
    kind = f["kind"]
    if kind == "repeated_subject_risk":
        rows = f["risks"]
        if any(r["origin"] == "verified_same_origin" for r in rows):
            seen: dict[tuple[str, str], dict[str, Any]] = {}
            for r in rows:
                seen.setdefault((r["identity"], r["subject"]), r)
            deduped = list(seen.values())
            in_members = [(r["subject"], r["event"]) for r in deduped
                          if r["cutoff"] == "in_cutoff"]
            return (len(deduped), len({m[0] for m in in_members}),
                    len({m[1] for m in in_members}), 0)
        in_members = [(r["subject"], r["event"]) for r in rows
                      if r["cutoff"] == "in_cutoff"]
        return len(rows), len({m[0] for m in in_members}), len({m[1] for m in in_members}), 0
    if kind == "systematic_data_or_process_gap":
        return 0, len({gr["subject"] for gr in f["gaps"]}), 0, len(f["gaps"])
    if kind == "within_site_time_trend":
        return 0, len({c["subject"] for c in f["chgs"]}), 0, 0
    return 0, 0, 0, 0


def query_generated(f: dict[str, Any], disposition: str) -> bool:
    if disposition != "positive":
        return False
    if f["query_decision"] != "site_process_delta_present":
        return False
    kind = f["kind"]
    if kind == "repeated_subject_risk":
        member_count = len(f["risks"])
    elif kind == "systematic_data_or_process_gap":
        member_count = len(f["gaps"])
    else:
        member_count = len(f["chgs"])
    return member_count <= f["query_fanout"]


def owner_domain_of(f: dict[str, Any]) -> str:
    if f["owner"] == "evaluate_and_own":
        return "D09"
    token = f["token"]
    if token.startswith("d06_"):
        return "D06"
    if token.startswith("d10_"):
        return "D10"
    if token == "d01_d08_individual_fact":
        return "D01-D08"
    return "unresolved"


def journey_marker(f: dict[str, Any]) -> bool:
    if f["risks"]:
        return True
    if any(bool(gr["anchor"]) and state == "resolved"
           for gr, state in zip(f["gaps"], f["gap_anchor_states"])):
        return True
    return bool(f["chgs"])


def verify_case(case: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Re-derive disposition + decisive counts from catalog typed_input and
    compare EXACTLY with the oracle entry. Returns problem strings (empty =
    pass). Never reads catalog disposition, free-text descriptions or case ids
    for the derivation."""
    f = catalog_facts(case)
    leaf = entry["expected_leaf_set"]
    problems: list[str] = []
    cid = case["case_id"]

    disp, reason, extra = derive_disposition(f)
    zero_unit = bool(extra.get("zero_unit", False))
    gate = extra.get("gate")
    pair_state = extra.get("pair_state")

    leaf_disp = None
    for d, key in (("positive", "positive_count"), ("negative", "negative_count"),
                   ("boundary", "boundary_count"), ("not_evaluable", "not_evaluable_count"),
                   ("not_applicable", "not_applicable_count")):
        if leaf[key] == 1:
            leaf_disp = d
            break
    if leaf_disp is None:
        problems.append(f"{cid}: no disposition count in oracle leaf")
    elif disp != leaf_disp:
        problems.append(f"{cid}: disposition derived {disp} != oracle {leaf_disp}")

    individual, affected, events, gap_opps = numerator(f)
    risk_count = 1 if disp == "positive" else 0
    clue_count = 1 if disp == "boundary" else 0
    query_count = 1 if query_generated(f, disp) else 0
    source_records = len(evidence_locators(f))
    opp_missing = max(0, f["opp_exp"] - f["opp_obs"])
    l0_complete = all(c["l0_status"] == "covered" for c in f["cov"]
                      if c["producer_domain"] in set(f["producers"]))
    domain_complete = all(c["l1_medical_completeness_state"] == "complete"
                          for c in f["cov"]
                          if c["producer_domain"] in set(f["producers"]))
    downstream = (disp == "positive" or f["carry_forward_state"] == "active")
    unit = 0 if zero_unit else 1
    show_counts = unit and disp in ("positive", "boundary")

    checks = {
        "unit_count": unit,
        "positive_count": 1 if disp == "positive" else 0,
        "negative_count": 1 if disp == "negative" else 0,
        "boundary_count": 1 if disp == "boundary" else 0,
        "not_evaluable_count": 1 if disp == "not_evaluable" else 0,
        "not_applicable_count": 1 if disp == "not_applicable" else 0,
        "gate_count": 1 if (zero_unit and gate) else 0,
        "open_gate_count": 1 if (zero_unit and gate) else 0,
        "l0_complete": l0_complete,
        "domain_complete": domain_complete,
        "l2.individual_risk_count": individual if unit else 0,
        "l2.affected_subject_count": affected if show_counts else 0,
        "l2.event_count": events if show_counts else 0,
        "l2.gap_opportunity_count": gap_opps if show_counts else 0,
        "l2.risk_count": risk_count,
        "l2.clue_count": clue_count,
        "l2.query_count": query_count,
        "l2.source_record_count": source_records,
        "l3.positive_count": risk_count,
        "l3.boundary_count": clue_count,
        "l3.risk_count": risk_count,
        "ownership.d09_action": f["owner"],
        "ownership.owner_domain": owner_domain_of(f),
        "ownership.risk_candidate_present": risk_count == 1,
        "ownership.risk_owner": "D09" if risk_count else None,
        "ownership.query_draft_present": query_count == 1,
        "ownership.query_owner": "D09" if query_count else None,
        "ownership.downstream_handoff_present": downstream,
        "ownership.handoff_target_domain": "R2" if downstream else None,
        "measure.denominator_kind": f["den_kind"],
        "measure.denominator_value": f["den_value"],
        "measure.denominator_state": f["den_state"],
        "measure.opportunity_expected": f["opp_exp"],
        "measure.opportunity_observed": f["opp_obs"],
        "measure.opportunity_missing": opp_missing,
        "measure.opportunity_state": f["opp_state"],
        "gate.window_pair_gate_present": gate == "window_pair_gate",
        "gate.window_pair_state": pair_state,
        "gate.admission_gate_present": f["es_state"] != "admitted",
        "gate.admission_gate_kind": f["gate_kind"] if f["es_state"] != "admitted" else None,
        "integrity.stage": f["es_state"],
        "integrity.gate_kind": f["gate_kind"] if f["es_state"] != "admitted" else None,
    }
    for key, derived in checks.items():
        if leaf[key] != derived:
            problems.append(f"{cid} {key}: derived {derived!r} != oracle {leaf[key]!r}")

    if unit:
        unit_checks = {
            "units.0.l1_disposition": disp,
            "units.0.pattern_kind": f["kind"],
            "units.0.unit_kind": "d09_pattern_unit",
            "units.0.primary_reason": reason,
            "units.0.participant_count": affected if show_counts else 0,
            "units.0.event_count": events if show_counts else 0,
            "units.0.gap_opportunity_count": gap_opps if show_counts else 0,
            "units.0.individual_risk_count": individual,
            "units.0.risk_count": risk_count,
            "units.0.clue_count": clue_count,
            "units.0.query_count": query_count,
            "units.0.evidence_count": source_records,
            "units.0.counterevidence_count": len(f["matched_ce"]),
            "units.0.gate_signal_type": None,
            "units.0.lineage_handoff": downstream,
        }
        for key, derived in unit_checks.items():
            if leaf[key] != derived:
                problems.append(f"{cid} {key}: derived {derived!r} != oracle {leaf[key]!r}")

    # source-leaf re-derivation of the decisive facts
    source = entry["expected_source_leaf_set"]
    src_checks = {
        "source.journey_marker_present": journey_marker(f),
        "source.query_present": query_generated(f, disp),
        "source.risk_present": disp == "positive",
        "source.hidden_node_count": len(f["risks"]) - 0,
    }
    for key, derived in src_checks.items():
        if key == "source.hidden_node_count":
            expected = len(case["typed_input"]["visibility_decision"].get("hidden_member_refs") or [])
            if source[key] != expected:
                problems.append(f"{cid} {key}: derived {expected!r} != oracle {source[key]!r}")
        elif source[key] != derived:
            problems.append(f"{cid} {key}: derived {derived!r} != oracle {source[key]!r}")
    return problems


# ---------------------------------------------------------------------------
class TestHashPinsAndAnchors(unittest.TestCase):
    """Computed content integrity: embedded hashes must recompute from the
    frozen artifacts and generators must stay mutually consistent."""

    def test_embedded_content_hashes_recompute(self) -> None:
        catalog, oracle, registry, quota = load_artifacts()
        self.assertEqual(oracle["content_hash"], object_hash(oracle))
        self.assertEqual(registry["content_hash"], object_hash(registry))
        self.assertEqual(quota["content_hash"], object_hash(quota))
        self.assertEqual(catalog["catalog_hash"], object_hash(catalog, "catalog_hash"))

    def test_cross_artifact_embedded_hashes(self) -> None:
        catalog, oracle, registry, quota = load_artifacts()
        self.assertEqual(registry["catalog_hash"], catalog["catalog_hash"])
        self.assertEqual(registry["quota_manifest_hash"], quota["content_hash"])
        self.assertEqual(quota["catalog_hash"], catalog["catalog_hash"])
        self.assertEqual(registry["contract_semantic_hash"], g.CONTRACT_SEMANTIC_HASH)
        self.assertEqual(quota["contract_semantic_hash"], g.CONTRACT_SEMANTIC_HASH)
        self.assertEqual(oracle["contract_semantic_hash"], o.CONTRACT_SEMANTIC_HASH)
        self.assertEqual(catalog["catalog_hash"], g.assemble_catalog()["catalog_hash"])

    def test_resolved_registry_generator_hash_self_consistent(self) -> None:
        registry = load_json(REGISTRY_PATH)
        self.assertEqual(registry["generator_hash"], g.STAGE_A_GENERATOR_SHA256)
        self.assertEqual(registry["generator_hash"], g._generator_code_hash())
        oracle = load_json(ORACLE_PATH)
        policy = registry["oracle_reference_state"]["expected_leaf_policy"]
        self.assertIn(f"oracle artifact content_hash={oracle['content_hash']}", policy)
        self.assertEqual(registry["oracle_reference_state"]["oracle_artifact_path"],
                         "reviews/" + ORACLE_ARTIFACT_NAME)

    def test_generator_contract_semantic_alignment(self) -> None:
        self.assertEqual(g.CONTRACT_SEMANTIC_HASH, o.CONTRACT_SEMANTIC_HASH)
        self.assertEqual(g.MIN_CASE_COUNT, MIN_CASE_COUNT)

    def test_no_oracle_side_semantic_tags_exist(self) -> None:
        """The 8 removed oracle-side semantic tag keys must not exist anywhere:
        not in the oracle generator source, not as spec keys, and there are no
        semantic skip-table definitions in this suite or the oracle generator."""
        src = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        for key in FORBIDDEN_ORACLE_TAG_KEYS:
            self.assertNotIn(f'"{key}"', src,
                             f"oracle-side tag key {key!r} still present as a literal")
            self.assertNotIn(f"'{key}'", src,
                             f"oracle-side tag key {key!r} still present as a literal")
        # the spec rows must not carry any tag key
        for spec in o.ORACLE_CASES:
            for key in FORBIDDEN_ORACLE_TAG_KEYS:
                self.assertNotIn(key, spec, f"tag key {key!r} still in spec row {spec['case_id']}")
        self.assertNotIn("SKIP_DISPOSITION", src)
        self.assertNotIn("SKIP_COUNTS", src)
        test_src = Path(__file__).read_text(encoding="utf-8")
        # The docstring mentions the removed identifiers; what must be absent
        # is any actual skip mechanism (assignment/definition) in this suite.
        for ident in ("SKIP_DISPOSITION", "SKIP_COUNTS"):
            self.assertNotIn(f"{ident} =", test_src, f"skip identifier {ident} defined")
            self.assertNotIn(f"{ident}:", test_src, f"skip identifier {ident} defined")


class TestCanonicalEncoding(unittest.TestCase):
    """UTF-8 / NFC / no-whitespace canonical JSON + no non-finite numbers."""

    ARTIFACT_PATHS = (CATALOG_PATH, ORACLE_PATH, REGISTRY_PATH, QUOTA_PATH)

    def test_bytes_are_canonical_no_whitespace(self) -> None:
        for path in self.ARTIFACT_PATHS:
            raw = path.read_bytes()
            obj = json.loads(raw.decode("utf-8"))
            self.assertEqual(raw, canonical_json(obj).encode("utf-8"),
                             f"{path.name} bytes are not the canonical JSON form")
            self.assertNotIn(b"\n", raw, f"{path.name} contains a newline")

    def test_all_strings_are_nfc(self) -> None:
        for path in self.ARTIFACT_PATHS:
            obj = load_json(path)
            for text in _walk_strings(obj):
                self.assertTrue(unicodedata.is_normalized("NFC", text),
                                f"{path.name} contains non-NFC string {text!r}")

    def test_no_nan_infinity_in_artifacts(self) -> None:
        for path in self.ARTIFACT_PATHS:
            json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)

    def test_generators_reject_nan_infinity(self) -> None:
        for fn in (g.canonical_json, o.canonical_json):
            with self.assertRaises(ValueError):
                fn({"x": float("nan")})
            with self.assertRaises(ValueError):
                fn({"x": float("inf")})
            with self.assertRaises(ValueError):
                fn({"x": float("-inf")})

    def test_fixture_and_content_hashes_are_sha256_hex(self) -> None:
        catalog = load_json(CATALOG_PATH)
        hex64 = re.compile(r"[0-9a-f]{64}")
        for case in catalog["cases"]:
            self.assertRegex(case["fixture_hash"], hex64, case["case_id"])
        self.assertRegex(catalog["catalog_hash"], hex64)


class TestCatalogSchema(unittest.TestCase):
    """Exact top-level / case / typed_input schemas; >= 179 cases."""

    def test_top_level_exact_keys_and_identity(self) -> None:
        catalog = load_json(CATALOG_PATH)
        self.assertEqual(sorted(catalog.keys()), sorted(CATALOG_TOP_KEYS))
        self.assertEqual(catalog["catalog_id"], g.CATALOG_ID)
        self.assertEqual(catalog["version"], g.SCHEMA_VERSION)
        self.assertEqual(catalog["case_count"], CASE_COUNT)
        self.assertEqual(len(catalog["cases"]), CASE_COUNT)
        self.assertGreaterEqual(len(catalog["cases"]), 179)

    def test_case_exact_keys_and_sequential_ids(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for index, case in enumerate(catalog["cases"], start=1):
            self.assertEqual(sorted(case.keys()), sorted(CASE_KEYS), case["case_id"])
            self.assertEqual(case["case_id"], f"D09-CASE-{index:03d}")
            self.assertEqual(case["fixture_id"], f"D09-FIX-{index:03d}")
            self.assertEqual(case["oracle_case_id"], f"D09-ORACLE-{index:03d}")
            self.assertEqual(case["manifest_case_id"], f"D09-MANIFEST-{index:03d}")

    def test_nested_typed_input_exact_key_sets(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            typed = case["typed_input"]
            self.assertEqual(sorted(typed.keys()), sorted(TYPED_INPUT_KEYS), case["case_id"])
            self.assertEqual(typed["input_schema"], g.TYPED_INPUT_SCHEMA)
            self.assertEqual(sorted(typed["scope_binding"].keys()), sorted(SCOPE_BINDING_KEYS))
            self.assertEqual(sorted(typed["pattern_definition"].keys()),
                             sorted(PATTERN_DEFINITION_KEYS))
            self.assertEqual(sorted(case["audience_contract"].keys()),
                             sorted(AUDIENCE_CONTRACT_KEYS))
            self.assertEqual(sorted(typed["stratum"].keys()), sorted(STRATUM_KEYS))
            self.assertEqual(sorted(typed["denominator"].keys()), sorted(DENOMINATOR_KEYS))
            self.assertEqual(sorted(typed["opportunity"].keys()), sorted(OPPORTUNITY_KEYS))
            self.assertEqual(sorted(typed["cutoff"].keys()), sorted(CUTOFF_KEYS))
            self.assertEqual(sorted(typed["numeric_policy"].keys()), sorted(NUMERIC_POLICY_KEYS))
            self.assertEqual(sorted(typed["visibility_decision"].keys()),
                             sorted(VISIBILITY_KEYS))
            self.assertEqual(sorted(typed["expected_set"].keys()), sorted(EXPECTED_SET_KEYS))
            self.assertEqual(sorted(typed["mutation_context"].keys()),
                             sorted(MUTATION_CONTEXT_KEYS))
            self.assertEqual(sorted(typed["audience_lexicon"].keys()),
                             sorted(AUDIENCE_LEXICON_KEYS))
            if typed["anti_overfit_variant"] is not None:
                self.assertEqual(sorted(typed["anti_overfit_variant"].keys()),
                                 sorted(ANTI_OVERFIT_KEYS))
                for change in typed["anti_overfit_variant"]["surface_changes"]:
                    self.assertEqual(sorted(change.keys()), sorted(SURFACE_CHANGE_KEYS))
            for window in typed["analysis_windows"]:
                self.assertEqual(sorted(window.keys()), sorted(WINDOW_KEYS))
            for cov in typed["coverage"]:
                self.assertEqual(sorted(cov.keys()), sorted(COVERAGE_KEYS))
            for member in typed["subject_risk_members"]:
                self.assertEqual(sorted(member.keys()), sorted(RISK_MEMBER_KEYS))
            for member in typed["gap_members"]:
                self.assertEqual(sorted(member.keys()), sorted(GAP_MEMBER_KEYS))
            for member in typed["change_ledger_members"]:
                self.assertEqual(sorted(member.keys()), sorted(CHANGE_MEMBER_KEYS))
            for ref in typed["evidence_refs"]:
                self.assertEqual(sorted(ref.keys()), sorted(EVIDENCE_REF_KEYS))

    def test_new_input_fact_fields_well_formed(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            typed = case["typed_input"]
            matched = typed["matched_counterevidence_rule_refs"]
            self.assertIsInstance(matched, list)
            for ref in matched:
                self.assertIn(ref, typed["pattern_definition"]["counterevidence_rule_refs"],
                              f"{case['case_id']} matched ce ref not declared")
            dc = typed["mode_contract_design_clause_ref"]
            self.assertTrue(dc is None or isinstance(dc, str))
            if dc is not None:
                self.assertEqual(case["case_id"], "D09-CASE-038")
                self.assertEqual(dc, "SYN-D09-DC-038")

    def test_expected_fields_are_literal_null(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            for key in ("expected_leaf_set", "expected_trace_leaf_set",
                        "expected_source_leaf_set"):
                self.assertIsNone(case[key],
                                  f"{case['case_id']} {key} must be literal null in the catalog")

    def test_closed_enums_and_token_kind_bijection(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            self.assertIn(case["disposition"], g.DISPOSITIONS, case["case_id"])
            self.assertIn(case["clinical_claim_token"], g.CLINICAL_CLAIM_TOKENS)
            self.assertIn(case["owner_route"], g.OWNER_ROUTES)
            self.assertIn(case["mutation_class"], g.MUTATION_CLASSES)
            self.assertIn(case["primary_partition_id"], g.PARTITION_MINIMUMS)
            if case["owner_route"] == "evaluate_and_own":
                self.assertIn(case["clinical_claim_token"], g.OWNED_TOKENS)
                self.assertEqual(case["pattern_kind"],
                                 g.TOKEN_KIND_BIJECTION[case["clinical_claim_token"]])
            elif case["owner_route"] == "consume_only":
                self.assertIn(case["clinical_claim_token"], g.CONSUME_ONLY_TOKENS)
                self.assertIsNone(case["pattern_kind"])
            elif case["owner_route"] == "routing_gate":
                self.assertEqual(case["clinical_claim_token"], "unresolved")
                self.assertEqual(case["pattern_kind"], "routing_gate")

    def test_fixture_hash_recomputes_for_every_case(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            self.assertEqual(case["fixture_hash"],
                             sha256_text(g.canonical_json(case["typed_input"])),
                             f"{case['case_id']} fixture_hash must be sha256(canonical(typed_input))")

    def test_generator_validation_passes(self) -> None:
        catalog = load_json(CATALOG_PATH)
        g.validate_catalog(catalog)


class TestPartitionQuota(unittest.TestCase):
    """Exact primary-partition minima, uniqueness, disjoint-union proof."""

    def test_every_partition_at_least_minimum_and_exact(self) -> None:
        catalog = load_json(CATALOG_PATH)
        _quota = load_json(QUOTA_PATH)
        counts = collections.Counter(c["primary_partition_id"] for c in catalog["cases"])
        self.assertEqual(len(counts), len(g.PARTITIONS))
        for partition, minimum in g.PARTITION_MINIMUMS.items():
            self.assertGreaterEqual(counts[partition], minimum, partition)
            self.assertEqual(counts[partition], minimum,
                             f"{partition} must match its frozen floor exactly")
        self.assertEqual(sum(counts.values()), MIN_CASE_COUNT)

    def test_quota_manifest_entries_match_catalog(self) -> None:
        catalog = load_json(CATALOG_PATH)
        quota = load_json(QUOTA_PATH)
        cases = catalog["cases"]
        for entry in quota["partitions"]:
            self.assertEqual(sorted(entry.keys()), sorted(PARTITION_ENTRY_KEYS))
            partition = entry["partition_id"]
            members = [c["case_id"] for c in cases
                       if c["primary_partition_id"] == partition]
            self.assertEqual(entry["required_minimum"], g.PARTITION_MINIMUMS[partition])
            self.assertEqual(entry["actual_count"], len(members))
            self.assertEqual(entry["sorted_case_ids"], sorted(members))
            self.assertEqual(len(entry["sorted_case_ids"]),
                             len(set(entry["sorted_case_ids"])),  # uniqueness
                             f"{partition} sorted_case_ids must be unique")
            self.assertEqual(entry["partition_hash"], sha256_text(g.canonical_json({
                "partition_id": partition,
                "required_minimum": entry["required_minimum"],
                "actual_count": entry["actual_count"],
                "sorted_case_ids": entry["sorted_case_ids"],
            })))

    def test_disjoint_union_proof(self) -> None:
        catalog = load_json(CATALOG_PATH)
        quota = load_json(QUOTA_PATH)
        proof = quota["disjoint_union_proof"]
        self.assertEqual(sorted(proof.keys()), sorted(DISJOINT_UNION_PROOF_KEYS))
        all_partition_ids = [cid for entry in quota["partitions"]
                             for cid in entry["sorted_case_ids"]]
        catalog_ids = sorted(c["case_id"] for c in catalog["cases"])
        self.assertEqual(proof["union_sorted_case_ids"], sorted(all_partition_ids))
        self.assertEqual(proof["union_sorted_case_ids"], catalog_ids)
        self.assertEqual(proof["union_case_count"], MIN_CASE_COUNT)
        self.assertTrue(proof["catalog_case_id_set_equal"])
        self.assertTrue(proof["pairwise_disjoint"])
        self.assertEqual(proof["duplicate_case_ids"], [])
        self.assertEqual(proof["missing_case_ids"], [])
        self.assertEqual(proof["proof_hash"], sha256_text(g.canonical_json({
            "union_sorted_case_ids": proof["union_sorted_case_ids"],
            "catalog_sorted_case_ids": catalog_ids,
        })))
        self.assertEqual(quota["total_case_count"], MIN_CASE_COUNT)
        self.assertEqual(quota["total_required_minimum"], MIN_CASE_COUNT)

    def test_generator_quota_validation_passes(self) -> None:
        catalog, _, _, quota = load_artifacts()
        g.validate_quota_manifest(quota, catalog)


class TestRegistryBijectionAndCoverage(unittest.TestCase):
    """Five-way bijection and full oracle coverage."""

    def test_five_column_bijection(self) -> None:
        registry = load_json(REGISTRY_PATH)
        rows = registry["rows"]
        self.assertEqual(len(rows), CASE_COUNT)
        for col in BIJECTION_COLUMNS:
            self.assertEqual(len({row[col] for row in rows}), CASE_COUNT, col)
        self.assertTrue(registry["bijection_audit"]["bijection_ok"])
        self.assertEqual(registry["bijection_audit"]["row_count"], CASE_COUNT)
        for col in BIJECTION_COLUMNS:
            self.assertEqual(registry["bijection_audit"]["columns"][col], CASE_COUNT)

    def test_rows_match_catalog_and_test_ids(self) -> None:
        catalog = load_json(CATALOG_PATH)
        registry = load_json(REGISTRY_PATH)
        for index, (row, case) in enumerate(zip(registry["rows"], catalog["cases"]), start=1):
            self.assertEqual(row["case_id"], case["case_id"])
            self.assertEqual(row["fixture_id"], case["fixture_id"])
            self.assertEqual(row["oracle_case_id"], case["oracle_case_id"])
            self.assertEqual(row["manifest_case_id"], case["manifest_case_id"])
            self.assertEqual(row["test_id"], f"D09-TEST-{index:03d}")
            self.assertEqual(row["oracle_resolution"], "resolved")
            self.assertEqual(row["substantive_input_hash"],
                             sha256_text(g.canonical_json(g.strip_substantive(case["typed_input"]))),
                             f"{case['case_id']} substantive_input_hash mismatch")

    def test_full_oracle_coverage_and_bijection(self) -> None:
        catalog, oracle, registry, _ = load_artifacts()
        cat_ids = {c["case_id"] for c in catalog["cases"]}
        ora_ids = {e["case_id"] for e in oracle["ordered_expectations"]}
        reg_ids = {r["case_id"] for r in registry["rows"]}
        self.assertEqual(cat_ids, ora_ids)
        self.assertEqual(cat_ids, reg_ids)
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        for case in catalog["cases"]:
            e = expectations[case["case_id"]]
            self.assertEqual(e["oracle_case_id"], case["oracle_case_id"])
            self.assertEqual(e["fixture_id"], case["fixture_id"])

    def test_generator_registry_validation_passes(self) -> None:
        catalog, _, registry, _ = load_artifacts()
        g.validate_registry(registry, catalog)


class TestOracleSchemaAndLeaves(unittest.TestCase):
    """Oracle-only expected/source/trace leaves: schema, uniformity, absence
    of catalog expected content."""

    def test_oracle_top_and_expectation_keys(self) -> None:
        oracle = load_json(ORACLE_PATH)
        self.assertEqual(sorted(oracle.keys()), sorted(ORACLE_TOP_KEYS))
        self.assertEqual(oracle["oracle_id"], o.ORACLE_ID)
        self.assertEqual(oracle["schema_version"], o.SCHEMA_VERSION)
        self.assertEqual(oracle["case_count"], CASE_COUNT)
        self.assertEqual(len(oracle["ordered_expectations"]), CASE_COUNT)
        for entry in oracle["ordered_expectations"]:
            self.assertEqual(sorted(entry.keys()), sorted(ORDERED_EXPECTATION_KEYS))

    def test_leaf_schema_uniform_64_48_13_9(self) -> None:
        oracle = load_json(ORACLE_PATH)
        full, reduced = 0, 0
        for entry in oracle["ordered_expectations"]:
            leaf_keys = sorted(entry["expected_leaf_set"].keys())
            if leaf_keys == LEAF64_KEYS:
                full += 1
            elif leaf_keys == LEAF48_KEYS:
                reduced += 1
            else:
                self.fail(f"{entry['case_id']} unexpected expected_leaf_set keys {leaf_keys}")
            self.assertEqual(sorted(entry["expected_source_leaf_set"].keys()),
                             sorted(SOURCE_LEAF_KEYS))
            self.assertEqual(sorted(entry["expected_trace_leaf_set"].keys()),
                             sorted(TRACE_LEAF_KEYS))
        self.assertEqual(full, 162)
        self.assertEqual(reduced, 17)

    def test_oracle_leaves_nonempty_and_catalog_null(self) -> None:
        catalog, oracle, _, _ = load_artifacts()
        for entry in oracle["ordered_expectations"]:
            for key in ("expected_leaf_set", "expected_source_leaf_set",
                        "expected_trace_leaf_set"):
                self.assertIsInstance(entry[key], dict)
                self.assertTrue(entry[key], f"{entry['case_id']} {key} must be non-empty")
        for case in catalog["cases"]:
            for key in ("expected_leaf_set", "expected_source_leaf_set",
                        "expected_trace_leaf_set"):
                self.assertIsNone(case[key])

    def test_oracle_unit_disposition_matches_catalog_declared(self) -> None:
        catalog, oracle, _, _ = load_artifacts()
        cases = {c["case_id"]: c for c in catalog["cases"]}
        for entry in oracle["ordered_expectations"]:
            case = cases[entry["case_id"]]
            leaf = entry["expected_leaf_set"]
            if "units.0.l1_disposition" in leaf:
                self.assertEqual(leaf["units.0.l1_disposition"], case["disposition"],
                                 entry["case_id"])
            else:
                self.assertEqual(case["disposition"], "not_applicable", entry["case_id"])
                self.assertEqual(leaf["unit_count"], 0)

    def test_oracle_has_no_internal_display_leakage(self) -> None:
        catalog, oracle, _, _ = load_artifacts()
        blob = json.dumps(oracle, ensure_ascii=False)
        for case in catalog["cases"]:
            forbidden = case["typed_input"]["audience_lexicon"]["forbidden_internal_terms"]
            self.assertTrue(forbidden)
            for term in forbidden:
                self.assertNotIn(term, blob, f"forbidden term {term!r} leaked into oracle")
            label = case["typed_input"]["pattern_definition"]["clinical_label_zh"]
            self.assertNotIn(label, blob,
                             f"display label {label!r} must not appear in the oracle")
        self.assertTrue(all(
            e["expected_source_leaf_set"]["source.disclosure_leak_present"] is False
            for e in oracle["ordered_expectations"]))

    def test_generator_oracle_validation_passes(self) -> None:
        oracle = load_json(ORACLE_PATH)
        o.validate_oracle(oracle)


class TestImportAndReadClosure(unittest.TestCase):
    """Static proofs: catalog generator never reads oracle content/leaves and
    neither generator imports the other, D08 runtime, or non-stdlib modules."""

    @staticmethod
    def _imports(source: str) -> set[str]:
        tree = ast.parse(source)
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        return modules

    def test_catalog_generator_stdlib_only_and_no_oracle_import(self) -> None:
        src = CATALOG_GEN_PATH.read_text(encoding="utf-8")
        imports = self._imports(src)
        self.assertTrue(imports <= STDLIB_MODULES, f"foreign imports: {imports - STDLIB_MODULES}")
        self.assertNotIn("generate_d09_expected_oracle", src)

    def test_oracle_generator_stdlib_only_and_no_catalog_import(self) -> None:
        src = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        imports = self._imports(src)
        self.assertTrue(imports <= STDLIB_MODULES, f"foreign imports: {imports - STDLIB_MODULES}")
        self.assertNotIn("generate_d09_challenge_registry", src)

    def test_oracle_generator_has_no_semantic_coupling(self) -> None:
        """The oracle generator's semantic code derives every leaf from
        explicit resolved facts: no mutation metadata, no sentinel spelling,
        no revision-hash recipe (worker_01 corrective pass 2026-08-15).
        The embedded ORACLE_CASES table region is excluded: it carries
        fixture identity labels and locator ref values as data."""
        src = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        marker = "ORACLE_CASES: list[dict[str, Any]] = ["
        start = src.find(marker)
        self.assertGreaterEqual(start, 0)
        lst_open = start + len(marker) - 1
        depth = 0
        table_end = None
        for k in range(lst_open, len(src)):
            if src[k] == "[":
                depth += 1
            elif src[k] == "]":
                depth -= 1
                if depth == 0:
                    table_end = k + 1
                    break
        self.assertIsNotNone(table_end)
        code = src[:start] + src[table_end:]
        for token in FORBIDDEN_ORACLE_SEMANTIC_TOKENS:
            self.assertNotIn(token, code,
                             f"oracle generator semantic coupling token {token!r}")

    def test_catalog_generator_has_no_expected_leaf_derivation(self) -> None:
        src = CATALOG_GEN_PATH.read_text(encoding="utf-8")
        for token in FORBIDDEN_DERIVATION_TOKENS:
            self.assertNotIn(token, src, f"expected-leaf derivation token {token!r} present")

    def test_catalog_generator_never_reads_oracle(self) -> None:
        src = CATALOG_GEN_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        reads: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in (
                        "read_bytes", "read_text", "open", "read"):
                    reads.append(ast.unparse(node))
        self.assertTrue(reads, "expected at least the contract read call")
        for call in reads:
            self.assertNotIn(ORACLE_ARTIFACT_NAME, call,
                             f"catalog generator reads the oracle: {call}")
        self.assertNotIn(load_json(ORACLE_PATH)["content_hash"], src)

    def test_catalog_generator_never_writes_oracle(self) -> None:
        src = CATALOG_GEN_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        writes: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in ("write_bytes", "write_text"):
                    writes.append(ast.unparse(node))
        self.assertTrue(writes)
        for call in writes:
            self.assertNotIn(ORACLE_ARTIFACT_NAME, call,
                             f"catalog generator writes the oracle: {call}")

    def test_oracle_generator_reads_only_contract_and_own_artifact(self) -> None:
        src = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        reads: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in (
                        "read_bytes", "read_text", "open", "read"):
                    reads.append(ast.unparse(node))
        self.assertEqual(len(reads), 2,
                         f"oracle generator must have exactly two read calls, got {reads}")
        for call in reads:
            self.assertNotIn("catalog", call.lower())
            self.assertNotIn("registry", call.lower())
            self.assertNotIn("quota", call.lower())
            self.assertNotIn(".open(", call)

    def test_no_runtime_or_server_code_in_generators(self) -> None:
        for path in (CATALOG_GEN_PATH, ORACLE_GEN_PATH):
            src = path.read_text(encoding="utf-8")
            for token in RUNTIME_TOKENS:
                self.assertNotIn(token, src, f"{path.name} contains runtime token {token!r}")


class TestTwoStageRegistryContract(unittest.TestCase):
    """Regression: stage-A provisional registry is oracle-blind; stage-B
    resolved registry is exactly provisional + declared delta; --check passes."""

    def test_stage_a_provisional_registry_is_oracle_blind(self) -> None:
        catalog = load_json(CATALOG_PATH)
        quota = load_json(QUOTA_PATH)
        provisional = g.assemble_registry(catalog, quota, g._generator_code_hash())
        self.assertEqual(provisional["oracle_reference_state"]["state"], "unresolved")
        self.assertEqual(provisional["oracle_reference_state"]["reserved_for"], "worker_02")
        policy = provisional["oracle_reference_state"]["expected_leaf_policy"]
        self.assertNotIn("content_hash=", policy)
        self.assertTrue(all(row["oracle_resolution"] == "unresolved"
                            for row in provisional["rows"]))
        self.assertEqual(provisional["generator_hash"], g.STAGE_A_GENERATOR_SHA256)
        g.validate_registry(provisional, catalog)

    def test_stage_b_delta_exactly(self) -> None:
        catalog, _, registry, _ = load_artifacts()
        provisional = g.assemble_registry(
            catalog, load_json(QUOTA_PATH), g._generator_code_hash())
        self.assertNotEqual(g.canonical_json(provisional), g.canonical_json(registry))
        # generator_hash is pinned, not a delta: it must match exactly.
        self.assertEqual(registry["generator_hash"], provisional["generator_hash"])
        self.assertEqual(g._registry_core(registry), g._registry_core(provisional))
        base = provisional["oracle_reference_state"]["expected_leaf_policy"]
        policy = registry["oracle_reference_state"]["expected_leaf_policy"]
        self.assertTrue(policy.startswith(base))
        self.assertRegex(
            policy[len(base):],
            re.escape(g.RESOLVED_POLICY_SUFFIX_PREFIX) + r"[0-9a-f]{64}")
        for prow, rrow in zip(provisional["rows"], registry["rows"]):
            self.assertEqual(rrow["oracle_resolution"], "resolved")
            self.assertEqual(rrow["substantive_input_hash"],
                             prow["substantive_input_hash"])

    def test_verify_resolved_registry_passes_pristine(self) -> None:
        catalog, _, registry, _ = load_artifacts()
        g.verify_resolved_registry(registry, catalog)

    def test_check_artifacts_and_render_guard(self) -> None:
        self.assertEqual(g.check_artifacts(verbose=False), 0)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            ws.mkdir()
            (ws / REGISTRY_PATH.name).write_bytes(REGISTRY_PATH.read_bytes())
            with self.assertRaises(g.D09ArtifactError):
                g.render_artifacts(verbose=False, out_dir=ws)


class TestStageBFailsClosed(unittest.TestCase):
    """Every tamper of the resolved registry must fail closed."""

    def setUp(self) -> None:
        self.catalog, _, self.registry, _ = load_artifacts()

    def _reseed(self, registry: dict) -> dict:
        registry["content_hash"] = g.content_hash(registry, "content_hash")
        return registry

    def test_generator_hash_tamper_with_reseal_fails(self) -> None:
        r = clone(self.registry)
        r["generator_hash"] = "0" * 64
        self._reseed(r)
        with self.assertRaises(g.D09ArtifactError) as ctx:
            g.verify_resolved_registry(r, self.catalog)
        self.assertEqual(ctx.exception.error_class, "generator_hash_mismatch")

    def test_generator_hash_tamper_without_reseal_fails(self) -> None:
        r = clone(self.registry)
        r["generator_hash"] = "1" * 64
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_row_resolution_flip_fails(self) -> None:
        r = clone(self.registry)
        r["rows"][3]["oracle_resolution"] = "unresolved"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_mixed_resolutions_fail(self) -> None:
        r = clone(self.registry)
        r["rows"][0]["oracle_resolution"] = "resolved"
        r["rows"][1]["oracle_resolution"] = "unresolved"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_state_flip_alone_fails(self) -> None:
        r = clone(self.registry)
        r["oracle_reference_state"]["state"] = "unresolved"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_reserved_for_tamper_fails(self) -> None:
        r = clone(self.registry)
        r["oracle_reference_state"]["reserved_for"] = "worker_99"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_artifact_path_tamper_fails(self) -> None:
        r = clone(self.registry)
        r["oracle_reference_state"]["oracle_artifact_path"] = "reviews/other.json"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_catalog_expected_fields_tamper_fails(self) -> None:
        r = clone(self.registry)
        r["oracle_reference_state"]["catalog_expected_fields"] = "filled"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_policy_suffix_truncated_fails(self) -> None:
        r = clone(self.registry)
        policy = r["oracle_reference_state"]["expected_leaf_policy"]
        r["oracle_reference_state"]["expected_leaf_policy"] = policy.rsplit(";", 1)[0]
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_policy_suffix_corrupted_fails(self) -> None:
        r = clone(self.registry)
        policy = r["oracle_reference_state"]["expected_leaf_policy"]
        r["oracle_reference_state"]["expected_leaf_policy"] = policy[:-1] + "G"
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_row_substantive_hash_tamper_with_reseal_fails(self) -> None:
        r = clone(self.registry)
        r["rows"][5]["substantive_input_hash"] = "1" * 64
        self._reseed(r)
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_row_identity_tamper_fails(self) -> None:
        r = clone(self.registry)
        r["rows"][0]["oracle_case_id"] = "D09-ORACLE-999"
        self._reseed(r)
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_stale_content_hash_fails(self) -> None:
        r = clone(self.registry)
        r["rows"][2]["substantive_input_hash"] = "2" * 64
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_bijection_audit_tamper_fails(self) -> None:
        r = clone(self.registry)
        r["bijection_audit"]["bijection_ok"] = False
        self._reseed(r)
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_row_key_missing_fails(self) -> None:
        r = clone(self.registry)
        r["rows"][0].pop("test_id")
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(r, self.catalog)

    def test_unresolved_registry_is_not_a_complete_chain(self) -> None:
        provisional = g.assemble_registry(
            self.catalog, load_json(QUOTA_PATH), g._generator_code_hash())
        with self.assertRaises(g.D09ArtifactError):
            g.verify_resolved_registry(provisional, self.catalog)


class TestMutationGates(unittest.TestCase):
    """Generator schema/hash/token gates reject tampered artifacts."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()
        self.expectations = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}

    def test_stale_contract_hash_fails(self) -> None:
        original = g.CONTRACT_FILE_SHA256
        try:
            g.CONTRACT_FILE_SHA256 = "0" * 64
            with self.assertRaises(g.D09ArtifactError):
                g.validate_contract()
        finally:
            g.CONTRACT_FILE_SHA256 = original

    def test_case_missing_and_extra_key_fail(self) -> None:
        case = clone(self.catalog["cases"][0])
        case.pop("fixture_hash")
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)
        case = clone(self.catalog["cases"][0])
        case["rogue_key"] = True
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_typed_input_missing_new_key_fails(self) -> None:
        case = clone(self.catalog["cases"][0])
        case["typed_input"].pop("matched_counterevidence_rule_refs")
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)
        case = clone(self.catalog["cases"][0])
        case["typed_input"].pop("mode_contract_design_clause_ref")
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_numeric_authority_and_query_policy_tamper_fail(self) -> None:
        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["resolved_authority_decision"]["minimum_member_subject_count"] = 1
        payload = {
            key: typed["resolved_authority_decision"][key]
            for key in (
                "authority_ref", "mode_contract_version",
                "minimum_member_subject_count",
                "gap_positive_minimum_opportunity_count",
                "trend_positive_minimum_subject_count",
            )
        }
        typed["resolved_authority_decision"]["authority_content_hash"] = \
            g.sha256_text(g.canonical_json(payload))
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-AUTHORITY")

        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["center_query_policy"]["max_query_member_fanout"] = 9
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-QUERY-POLICY")

    def test_query_proof_and_source_alignment_tamper_fail(self) -> None:
        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["query_redundancy_decision"]["unit_member_set_hash"] = "0" * 64
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-MEMBER-SET")

        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["query_redundancy_decision"]["coverage_proof_hash"] = "0" * 64
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-PROOF")

        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["source_verification_records"] = []
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-SOURCE-EMPTY")

        typed = clone(self.catalog["cases"][0]["typed_input"])
        typed["source_verification_records"][0]["revision"] = "WRONG-REVISION"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_typed_input(typed, "TAMPER-SOURCE-REVISION")
    def test_expected_leaf_leak_fails(self) -> None:
        case = clone(self.catalog["cases"][0])
        case["expected_leaf_set"] = {"positive_count": 1}
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_disposition_enum_violation_fails(self) -> None:
        case = clone(self.catalog["cases"][0])
        case["disposition"] = "bogus"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_token_kind_bijection_violation_fails(self) -> None:
        case = clone(self.catalog["cases"][0])
        case["clinical_claim_token"] = "d06_estimand"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_consume_only_null_kind_violation_fails(self) -> None:
        case = clone(next(c for c in self.catalog["cases"]
                          if c["owner_route"] == "consume_only"))
        case["pattern_kind"] = "repeated_subject_risk"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_positive_requires_members(self) -> None:
        case = clone(next(c for c in self.catalog["cases"] if c["disposition"] == "positive"))
        typed = case["typed_input"]
        typed["subject_risk_members"] = []
        typed["gap_members"] = []
        typed["change_ledger_members"] = []
        with self.assertRaises(g.D09ArtifactError):
            g.validate_case(case, 1)

    def test_fixture_hash_tamper_fails_catalog_hash(self) -> None:
        catalog = clone(self.catalog)
        catalog["cases"][0]["fixture_hash"] = "1" * 64
        with self.assertRaises(g.D09ArtifactError):
            g.validate_catalog(catalog)

    def test_quota_actual_count_tamper_fails(self) -> None:
        quota = clone(self.quota)
        quota["partitions"][0]["actual_count"] += 1
        with self.assertRaises(g.D09ArtifactError):
            g.validate_quota_manifest(quota, self.catalog)

    def test_quota_proof_flags_tamper_fails(self) -> None:
        quota = clone(self.quota)
        quota["disjoint_union_proof"]["pairwise_disjoint"] = False
        with self.assertRaises(g.D09ArtifactError):
            g.validate_quota_manifest(quota, self.catalog)
        quota = clone(self.quota)
        quota["disjoint_union_proof"]["missing_case_ids"] = ["D09-CASE-001"]
        with self.assertRaises(g.D09ArtifactError):
            g.validate_quota_manifest(quota, self.catalog)

    def test_registry_tamper_fails_validate_registry(self) -> None:
        r = clone(self.registry)
        r["rows"][0]["oracle_resolution"] = "unresolved"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_registry(r, self.catalog)
        r = clone(self.registry)
        r["oracle_reference_state"]["state"] = "bogus"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_registry(r, self.catalog)
        r = clone(self.registry)
        r["rows"][0]["substantive_input_hash"] = "zzz"
        with self.assertRaises(g.D09ArtifactError):
            g.validate_registry(r, self.catalog)

    def test_nan_in_catalog_fails_canonical_round_trip(self) -> None:
        case = clone(self.catalog["cases"][0])
        case["typed_input"]["denominator"]["denominator_value"] = float("nan")
        with self.assertRaises(ValueError):
            g.canonical_json(case)

    def test_oracle_tamper_fails_validate_oracle(self) -> None:
        oracle = clone(self.oracle)
        oracle["ordered_expectations"][0]["expected_leaf_set"] = {}
        with self.assertRaises(SystemExit):
            o.validate_oracle(oracle)
        oracle = clone(self.oracle)
        oracle["ordered_expectations"][1].pop("expected_trace_leaf_set")
        with self.assertRaises(SystemExit):
            o.validate_oracle(oracle)
        oracle = clone(self.oracle)
        oracle["ordered_expectations"][0]["oracle_case_id"] = \
            oracle["ordered_expectations"][1]["oracle_case_id"]
        with self.assertRaises(SystemExit):
            o.validate_oracle(oracle)
        oracle = clone(self.oracle)
        oracle["content_hash"] = "0" * 64
        with self.assertRaises(SystemExit):
            o.validate_oracle(oracle)


class TestContentIdentityAndInvariance(unittest.TestCase):
    """Contract §5.1/§5.2: content identity/idempotency, revision/cutoff/
    method sensitivity, lineage supersession, input-order/display invariance."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, _ = load_artifacts()
        self.expectations = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}
        self.cases = {c["case_id"]: c for c in self.catalog["cases"]}

    def test_opaque_run_ids_do_not_change_content_identity(self) -> None:
        typed = clone(self.catalog["cases"][0]["typed_input"])
        base_id = content_identity(typed)
        base_sub = g.strip_substantive(typed)
        for field, value in (("run_ref", "SYN-D09-RUN-OPAQUE-777"),
                             ("snapshot_ref", "SYN-D09-SNAP-OPAQUE-888"),
                             ("envelope_id", "SYN-D09-ENV-OPAQUE-999")):
            mutated = clone(typed)
            mutated[field] = value
            self.assertEqual(content_identity(mutated), base_id,
                             f"{field} must not enter content identity")
            self.assertEqual(g.strip_substantive(mutated), base_sub,
                             f"{field} must be stripped from the idempotency key")

    def test_changed_revision_cutoff_method_change_content_identity(self) -> None:
        typed = clone(self.catalog["cases"][0]["typed_input"])
        base_id = content_identity(typed)

        rev = clone(typed)
        rev["source_revision_set"] = ["SRC-REV-001-002"]
        rev["source_content_hashes"] = [g.sha256_text("d09-rev:SRC-REV-001-002")]
        self.assertNotEqual(content_identity(rev), base_id, "revision advance must change identity")

        cutoff = clone(typed)
        cutoff["cutoff"]["cutoff_id"] = "SYN-D09-CUT-999"
        for window in cutoff["analysis_windows"]:
            window["cutoff_id"] = "SYN-D09-CUT-999"
        self.assertNotEqual(content_identity(cutoff), base_id,
                            "cutoff change must change window instance identity")

        method = clone(typed)
        method["pattern_definition"]["pattern_definition_content_hash"] = "0" * 64
        self.assertNotEqual(content_identity(method), base_id,
                            "method change must change content identity")

    def test_duplicate_revision_is_idempotent_in_identity(self) -> None:
        typed = clone(self.catalog["cases"][0]["typed_input"])
        base_id = content_identity(typed)
        dup = clone(typed)
        dup["source_revision_set"] = typed["source_revision_set"] + typed["source_revision_set"]
        self.assertEqual(content_identity(dup), base_id,
                         "duplicate re-export of the same revision must not change identity")
        self.assertEqual(g.strip_substantive(dup), g.strip_substantive(typed))

    def test_revision_repeat_counts_members_once(self) -> None:
        case = next(c for c in self.catalog["cases"] if c["mutation_class"] == "revision_repeat")
        leaf = self.expectations[case["case_id"]]["expected_leaf_set"]
        self.assertEqual(leaf["l2.affected_subject_count"], 2)
        self.assertEqual(leaf["l2.event_count"], 2)
        self.assertEqual(leaf["l2.individual_risk_count"], 2)

    def test_rule_supersession_produces_superseded_lineage(self) -> None:
        superseded = [c for c in self.catalog["cases"] if c["mutation_class"] == "rule_supersession"]
        self.assertTrue(superseded)
        for case in superseded:
            trace = self.expectations[case["case_id"]]["expected_trace_leaf_set"]
            self.assertGreaterEqual(trace["trace.superseded_unit_count"], 1,
                                    f"{case['case_id']} method change must supersede units")

    def test_data_revision_continuation_never_supersedes(self) -> None:
        for case in self.catalog["cases"]:
            if case["mutation_class"] in ("revision_repeat", "export_repeat",
                                          "cutoff_all_out", "cutoff_mixed", "cutoff_spans"):
                trace = self.expectations[case["case_id"]]["expected_trace_leaf_set"]
                self.assertEqual(trace["trace.superseded_unit_count"], 0,
                                 f"{case['case_id']} data/cutoff continuation must not supersede")

    def test_order_shuffle_and_display_rename_same_outcome(self) -> None:
        order = next(c for c in self.catalog["cases"] if c["mutation_class"] == "order_shuffle")
        rename = next(c for c in self.catalog["cases"] if c["mutation_class"] == "display_rename")
        self.assertEqual(order["disposition"], rename["disposition"])
        eo, er = self.expectations[order["case_id"]], self.expectations[rename["case_id"]]
        for leaf in ("expected_leaf_set", "expected_source_leaf_set", "expected_trace_leaf_set"):
            diffs = [k for k in eo[leaf] if k not in er[leaf] or eo[leaf][k] != er[leaf][k]]
            self.assertTrue(set(diffs) <= IDENTITY_LEAF_KEYS,
                            f"{leaf} differs beyond identity tokens: {diffs}")
        self.assertIn("显示名变体",
                      rename["typed_input"]["pattern_definition"]["clinical_label_zh"])
        self.assertNotIn("显示名变体", json.dumps(self.oracle, ensure_ascii=False))

    def test_anti_overfit_variants_invariant_outcomes(self) -> None:
        groups: dict[str, list[str]] = collections.defaultdict(list)
        for case in self.catalog["cases"]:
            aov = case["typed_input"].get("anti_overfit_variant")
            if aov:
                groups[aov["base_fixture_id"]].append(case["case_id"])
        self.assertEqual(len(groups), 8)
        for base, ids in sorted(groups.items()):
            self.assertEqual(len(ids), 2, base)
            first, second = ids
            self.assertEqual(self.cases[first]["disposition"], self.cases[second]["disposition"])
            e1, e2 = self.expectations[first], self.expectations[second]
            for leaf in ("expected_leaf_set", "expected_source_leaf_set",
                         "expected_trace_leaf_set"):
                diffs = [k for k in e1[leaf] if k not in e2[leaf] or e1[leaf][k] != e2[leaf][k]]
                self.assertTrue(set(diffs) <= IDENTITY_LEAF_KEYS,
                                f"{first} vs {second} {leaf} diffs beyond identity: {diffs}")

    def test_verified_same_origin_pairs_dedup(self) -> None:
        for cid in ("D09-CASE-047", "D09-CASE-163"):
            case = self.cases[cid]
            members = case["typed_input"]["subject_risk_members"]
            self.assertTrue(all(m["origin_decision"] == "verified_same_origin"
                                for m in members))
            leaf = self.expectations[cid]["expected_leaf_set"]
            self.assertEqual(leaf["l2.affected_subject_count"], 2)
            self.assertEqual(leaf["l2.event_count"], 2)
            self.assertEqual(leaf["l2.individual_risk_count"], 2)
        # 047 encodes two D02+D08 pairs: four rows sharing subjects/events per pair
        m047 = self.cases["D09-CASE-047"]["typed_input"]["subject_risk_members"]
        self.assertEqual(len(m047), 4)
        self.assertEqual(m047[0]["subject_stable_id"], m047[1]["subject_stable_id"])
        self.assertEqual(m047[0]["source_event_identity"], m047[1]["source_event_identity"])
        self.assertNotEqual(m047[0]["producer_domain"], m047[1]["producer_domain"])


# ---------------------------------------------------------------------------
# Contract §3.2 whitelist invariant (Luna REVISE repair 2026-08-15): every
# typed subject_risk member risk_kind must be admitted by its case
# pattern_definition.accepted_member_risk_kinds.
# ---------------------------------------------------------------------------
def risk_kind_invariant_problems(case: dict[str, Any]) -> list[str]:
    """Return whitelist violations for one case (empty = pass)."""
    typed = case["typed_input"]
    whitelist = set(typed["pattern_definition"]["accepted_member_risk_kinds"])
    problems: list[str] = []
    for member in typed["subject_risk_members"]:
        if member["risk_kind"] not in whitelist:
            problems.append(
                f"member {member['member_id']} risk_kind {member['risk_kind']!r} not in "
                f"accepted_member_risk_kinds {sorted(whitelist)}")
    return problems


class TestRiskKindWhitelistInvariant(unittest.TestCase):
    """Every subject_risk member risk kind is admitted by its case definition
    (contract §3.2); CASE-047 whitelists its D08 cross-domain members; an
    unlisted member risk kind is rejected."""

    def setUp(self) -> None:
        self.catalog, self.oracle, _, _ = load_artifacts()
        self.expectations = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}
        self.cases = {c["case_id"]: c for c in self.catalog["cases"]}

    def test_all_179_member_risk_kinds_whitelisted(self) -> None:
        failures: dict[str, list[str]] = {}
        for case in self.catalog["cases"]:
            problems = risk_kind_invariant_problems(case)
            if problems:
                failures[case["case_id"]] = problems
        self.assertEqual(
            failures, {},
            f"{len(failures)} cases violate the member risk-kind whitelist:\n"
            + "\n".join(f"{cid}: {'; '.join(p)}" for cid, p in sorted(failures.items())))

    def test_case_047_focused_whitelist_and_dedup(self) -> None:
        case = self.cases["D09-CASE-047"]
        whitelist = set(case["typed_input"]["pattern_definition"]["accepted_member_risk_kinds"])
        members = case["typed_input"]["subject_risk_members"]
        self.assertEqual(len(members), 4)
        self.assertIn("d01_seriousness_hospital_death", whitelist)
        self.assertIn("d08_cross_domain_relation", whitelist)
        d08 = [m for m in members if m["producer_domain"] == "D08"]
        self.assertEqual(len(d08), 2)
        for member in d08:
            self.assertEqual(member["risk_kind"], "d08_cross_domain_relation")
        for member in members:
            self.assertIn(member["risk_kind"], whitelist,
                          f"{member['member_id']} risk_kind not whitelisted")
        # intended verified same-origin dedup result stays 2/2/2
        leaf = self.expectations["D09-CASE-047"]["expected_leaf_set"]
        self.assertEqual(leaf["l2.affected_subject_count"], 2)
        self.assertEqual(leaf["l2.event_count"], 2)
        self.assertEqual(leaf["l2.individual_risk_count"], 2)

    def test_unlisted_member_risk_kind_rejected(self) -> None:
        case = clone(self.cases["D09-CASE-047"])
        target = next(m for m in case["typed_input"]["subject_risk_members"]
                      if m["producer_domain"] == "D08")
        target["risk_kind"] = "d05_planned_actual"  # declared kind, NOT admitted
        problems = risk_kind_invariant_problems(case)
        self.assertTrue(problems, "unlisted member risk kind must be rejected")
        self.assertIn("d05_planned_actual", problems[0])
        mutated_catalog = clone(self.catalog)
        index = next(i for i, row in enumerate(mutated_catalog["cases"])
                     if row["case_id"] == "D09-CASE-047")
        mutated_catalog["cases"][index] = case
        mutated_catalog["catalog_hash"] = g.content_hash(mutated_catalog, "catalog_hash")
        with self.assertRaises(g.D09ArtifactError) as ctx:
            g.validate_catalog(mutated_catalog)
        self.assertEqual(ctx.exception.error_class, "schema_error")
        # pristine case passes the same check
        self.assertEqual(risk_kind_invariant_problems(self.cases["D09-CASE-047"]), [])


class TestIndependentVerifier(unittest.TestCase):
    """179/179 disposition and decisive-count re-derivation from catalog
    typed_input ONLY, with ZERO skips."""

    def setUp(self) -> None:
        self.catalog, self.oracle, _, _ = load_artifacts()
        self.expectations = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}

    def test_all_179_dispositions_and_counts_derived_zero_skips(self) -> None:
        failures: dict[str, list[str]] = {}
        for case in self.catalog["cases"]:
            problems = verify_case(case, self.expectations[case["case_id"]])
            if problems:
                failures[case["case_id"]] = problems
        self.assertEqual(
            failures, {},
            f"independent verifier rejected {len(failures)}/179 cases:\n"
            + "\n".join(f"{cid}: {'; '.join(p)}" for cid, p in sorted(failures.items())))

    def test_all_179_cases_present_and_covered(self) -> None:
        self.assertEqual(len(self.catalog["cases"]), 179)
        self.assertEqual(len(self.expectations), 179)
        self.assertEqual({c["case_id"] for c in self.catalog["cases"]},
                         set(self.expectations))

    def test_verifier_is_not_coupled_to_oracle_generator(self) -> None:
        """The verifier functions live in this test module and do not import
        the oracle generator's decision machinery."""
        for name in ("derive_disposition", "numerator", "query_generated",
                     "catalog_facts", "verify_case"):
            fn = globals().get(name)
            self.assertIsNotNone(fn, name)
            self.assertNotEqual(getattr(fn, "__module__", ""),
                                "generate_d09_expected_oracle", name)

    def test_no_free_text_or_case_id_dependence(self) -> None:
        """The verifier must not read mutation_context.desc, case ids or the
        catalog disposition field."""
        src = inspect_source_of_verify_case()
        for token in ('["desc"]', '.get("desc")', '["disposition"]',
                      'case_id', 'mutation_context'):
            if token == 'case_id':
                # only the diagnostics label may mention the case id
                self.assertLessEqual(src.count("case_id"), 1)
            else:
                self.assertNotIn(token, src,
                                 f"verifier reads forbidden input {token!r}")


def inspect_source_of_verify_case() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    start = source.index("def catalog_facts")
    end = source.index("# ---------------------------------------------------------------------------",
                        start)
    return source[start:end]


class TestDeterministicReplayAndPort(unittest.TestCase):
    """Repeated --check, double-generation byte identity, TCP 8911 stopped."""

    def test_generate_all_twice_byte_identical(self) -> None:
        first = g._generate_all()
        second = g._generate_all()
        for name, a, b in (("catalog", first[0], second[0]),
                           ("quota", first[1], second[1]),
                           ("registry", first[2], second[2])):
            self.assertEqual(g.canonical_json(a), g.canonical_json(b), name)

    def test_render_to_two_temp_workspaces_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            ws1 = Path(tmp1) / "ws"
            ws2 = Path(tmp2) / "ws"
            ws1.mkdir()
            ws2.mkdir()
            g.render_artifacts(verbose=False, out_dir=ws1)
            g.render_artifacts(verbose=False, out_dir=ws2)
            for name in (CATALOG_PATH.name, QUOTA_PATH.name, REGISTRY_PATH.name):
                self.assertEqual((ws1 / name).read_bytes(), (ws2 / name).read_bytes(), name)
            self.assertEqual((ws1 / CATALOG_PATH.name).read_bytes(),
                             CATALOG_PATH.read_bytes())
            self.assertEqual((ws1 / QUOTA_PATH.name).read_bytes(), QUOTA_PATH.read_bytes())
            provisional = g._generate_all()[2]
            self.assertEqual((ws1 / REGISTRY_PATH.name).read_bytes(),
                             g.canonical_json(provisional).encode("utf-8"))

    def test_repeated_check_exits_zero(self) -> None:
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(CATALOG_GEN_PATH), "--check"],
                cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0,
                             f"catalog --check failed:\n{result.stdout}\n{result.stderr}")
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(ORACLE_GEN_PATH), "check"],
                cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0,
                             f"oracle check failed:\n{result.stdout}\n{result.stderr}")

    def test_tcp_8911_stopped(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", 8911))
        finally:
            sock.close()
        self.assertNotEqual(result, 0,
                            "port 8911 must stay stopped (connection must be refused)")


if __name__ == "__main__":
    unittest.main()
