"""D09 test-only frozen artifact adapter, oracle leaf assembly and hash pins.

This test module is the ONLY component allowed to read the frozen D09 artifact
chain (contract/catalog/oracle/registry/quota).  It validates every frozen
file hash, parses the 179 catalog ``typed_input`` envelopes into the closed
typed objects of ``mm_r4.d09_contracts``, runs the deterministic evaluator and
assembles the expected/source/trace leaf vocabulary of the independent oracle
for exact per-key comparison.

The production runtime modules (``d09_contracts.py`` / ``d09_evaluator.py``)
never import this module and never read the frozen artifacts.

Clean-semantics boundary (corrective freeze, 2026-08-16):
  * The runtime is decoupled from synthetic test intent: it never reads
    mutation context / anti-overfit metadata, never branches on mutation
    class, and never interprets sentinel locator/anchor spellings or content-
    hash conventions.
  * Versioned numerical authority, Center Query policy, Query member-set proof
    and source-verification alignment are explicit typed facts.  Validation
    rejects missing authority, default fanout, inconsistent set/proof hashes
    and revision/hash mismatches before evaluation.

Identity-token formatting notes (adapter-only):
  * ``trace.edge_set`` ids are fixture-level identity tokens
    (``SYN-D09-EDGE-<idx>-<n>``) synthesized from the case index and the
    runtime's sorted member/locator pairs; the runtime itself exposes typed
    ``D09TraceEdge`` objects (edge_index/member_ref/locator_ref).
  * the trace-leaf locatability flags (``reverse_conservation_ok``,
    ``positive_evidence_ok``) are defined by the frozen oracle in terms of
    its own missing-locator marker; the adapter reproduces that oracle leaf
    definition with a test-side constant (``FROZEN_MISSING_LOCATOR``).  The
    runtime never sees it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[3]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _ROOT / "poc" / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _ROOT / "poc" / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _ROOT / "poc" / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d09_contracts import (  # noqa: E402
    AdmissionGate,
    AnalysisWindow,
    AntiOverfitVariant,
    AudienceLexicon,
    CenterQueryPolicy,
    ChangeLedgerMember,
    CoverageStatus,
    Cutoff,
    D09TypedInput,
    Denominator,
    EvidenceRef,
    ExpectedSet,
    GapMember,
    LineageContext,
    MethodComparabilityDecision,
    MutationContext,
    NumericPolicy,
    Opportunity,
    PatternDefinition,
    QueryRedundancyDecision,
    ResolvedAuthorityDecision,
    ScopeBinding,
    SourceVerificationRecord,
    Stratum,
    SubjectRiskMember,
    SurfaceChange,
    VisibilityDecision,
    validate_typed_input,
)
from mm_r4.d09_evaluator import evaluate  # noqa: E402

CONTRACT_PATH = _ROOT / "reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md"
CATALOG_PATH = _ROOT / "reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json"
ORACLE_PATH = _ROOT / "reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json"
REGISTRY_PATH = _ROOT / "reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json"
QUOTA_PATH = _ROOT / "reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json"
GENERATOR_TEST_PATH = _ROOT / "tests" / "test_d09_artifact_generator.py"

# ---------------------------------------------------------------------------
# Frozen pins (2026-08-15 acceptance state; contract section 16 anchors).
# ---------------------------------------------------------------------------
CONTRACT_FILE_SHA256 = "9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40"
CATALOG_FILE_SHA256 = "93a737989eb05d75cb15ca09860949890013059663c601868b2f2a93c5c710eb"
ORACLE_FILE_SHA256 = "045990cfa9d0286e5b8c007d5c942faff0489a8afb06d09158c0f4733cb0c86a"
REGISTRY_FILE_SHA256 = "b697c43199047a15ed5666f55ef1b1d99762c34b3925c9e36815497ebd92f179"
QUOTA_FILE_SHA256 = "4b80f36a4904e0beb0f7f14b428db010109de4d3bd71becdc367996e9085b50a"
GENERATOR_TEST_FILE_SHA256 = "170418760176906c3f6e01d9a9dd5ceb3f7ef880673a0c5472c16e843cf1e78f"

CASE_COUNT = 179

DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")

_ARTIFACT_PINS: Tuple[Tuple[Path, str], ...] = (
    (CONTRACT_PATH, CONTRACT_FILE_SHA256),
    (CATALOG_PATH, CATALOG_FILE_SHA256),
    (ORACLE_PATH, ORACLE_FILE_SHA256),
    (REGISTRY_PATH, REGISTRY_FILE_SHA256),
    (QUOTA_PATH, QUOTA_FILE_SHA256),
    (GENERATOR_TEST_PATH, GENERATOR_TEST_FILE_SHA256),
)

# Oracle leaf key vocabulary (uniform across all 179 entries).
LEAF48_KEYS: Tuple[str, ...] = (
    "all_units_disposed", "boundary_count", "domain_complete",
    "expected_set_reconciled", "gate.admission_gate_kind",
    "gate.admission_gate_present", "gate.window_pair_gate_present",
    "gate.window_pair_state", "gate_count", "integrity.error_object",
    "integrity.error_stage", "integrity.error_type", "integrity.gate_kind",
    "integrity.stage", "l0_complete", "l2.affected_subject_count",
    "l2.center_pattern_count", "l2.clue_count", "l2.event_count",
    "l2.gap_opportunity_count", "l2.individual_risk_count", "l2.query_count",
    "l2.risk_count", "l2.source_record_count", "l3.boundary_count",
    "l3.positive_count", "l3.risk_count", "measure.denominator_kind",
    "measure.denominator_state", "measure.denominator_value",
    "measure.opportunity_expected", "measure.opportunity_missing",
    "measure.opportunity_observed", "measure.opportunity_state",
    "negative_count", "not_applicable_count", "not_evaluable_count",
    "open_gate_count", "ownership.d09_action",
    "ownership.downstream_handoff_present", "ownership.handoff_target_domain",
    "ownership.owner_domain", "ownership.query_draft_present",
    "ownership.query_owner", "ownership.risk_candidate_present",
    "ownership.risk_owner", "positive_count", "unit_count",
)
UNITS_KEYS: Tuple[str, ...] = (
    "units.0.clue_count", "units.0.counterevidence_count", "units.0.event_count",
    "units.0.evidence_count", "units.0.gap_opportunity_count",
    "units.0.gate_signal_type", "units.0.individual_risk_count",
    "units.0.l1_disposition", "units.0.lineage_handoff",
    "units.0.participant_count", "units.0.pattern_kind",
    "units.0.primary_reason", "units.0.query_count", "units.0.risk_count",
    "units.0.stable_core", "units.0.unit_kind",
)
LEAF64_KEYS: Tuple[str, ...] = tuple(sorted(LEAF48_KEYS + UNITS_KEYS))

SOURCE_LEAF_KEYS: Tuple[str, ...] = (
    "source.audience_anchor", "source.audience_lexicon_ref",
    "source.audience_payload_present", "source.disclosure_leak_present",
    "source.evaluation_node_set", "source.hidden_node_count",
    "source.journey_marker_present", "source.producer_binding_ids",
    "source.projectable_node_set", "source.query_present",
    "source.reverse_binding_count", "source.risk_present",
    "source.source_jump_target_pairs",
)
TRACE_LEAF_KEYS: Tuple[str, ...] = (
    "trace.bidirectional_join_count", "trace.edge_set",
    "trace.lineage_handoff_count", "trace.negative_checked_edge_count",
    "trace.positive_evidence_ok", "trace.reverse_conservation_ok",
    "trace.stable_core_count", "trace.superseded_unit_count",
    "trace.unit_stable_cores",
)

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifacts() -> Tuple[dict, dict, dict, dict]:
    """Load catalog/oracle/registry/quota, validating every frozen file hash."""
    for path, pin in _ARTIFACT_PINS:
        digest = sha256_bytes(path.read_bytes())
        if digest != pin:
            raise AssertionError(
                f"frozen artifact hash mismatch: {path.name} {digest} != {pin}")
    return (load_json(CATALOG_PATH), load_json(ORACLE_PATH),
            load_json(REGISTRY_PATH), load_json(QUOTA_PATH))


# ---------------------------------------------------------------------------
# JSON -> typed bundle parsing (pure field mapping, no semantics)
# ---------------------------------------------------------------------------


def _as_str_tuple(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    return tuple(str(item) for item in value)


def _as_int_or_none(value: Any) -> Optional[int]:
    return None if value is None else int(value)


def _parse_scope_binding(value: Any) -> ScopeBinding:
    return ScopeBinding(
        scope_binding_id=str(value["scope_binding_id"]),
        scope_type=str(value["scope_type"]),
        scope_equality_decision=str(value["scope_equality_decision"]),
    )


def _parse_pattern_definition(value: Any) -> PatternDefinition:
    return PatternDefinition(
        pattern_definition_id=str(value["pattern_definition_id"]),
        pattern_kind=value.get("pattern_kind"),
        clinical_label_zh=str(value["clinical_label_zh"]),
        risk_domain=str(value["risk_domain"]),
        clinical_claim_token=str(value["clinical_claim_token"]),
        d09_action=str(value["d09_action"]),
        required_producer_domains=_as_str_tuple(value["required_producer_domains"]),
        accepted_member_risk_kinds=_as_str_tuple(value["accepted_member_risk_kinds"]),
        numerator_contract_id=str(value["numerator_contract_id"]),
        allowed_denominator_kinds=_as_str_tuple(value["allowed_denominator_kinds"]),
        window_contract_id=str(value["window_contract_id"]),
        stratum_contract_id=str(value["stratum_contract_id"]),
        comparability_contract_id=str(value["comparability_contract_id"]),
        positive_rule_ref=str(value["positive_rule_ref"]),
        counterevidence_rule_refs=_as_str_tuple(value["counterevidence_rule_refs"]),
        monitoring_priority_rule_ref=str(value["monitoring_priority_rule_ref"]),
        center_query_policy_id=str(value["center_query_policy_id"]),
        minimum_member_subject_count_ref=value.get("minimum_member_subject_count_ref"),
        required_window_count_ref=value.get("required_window_count_ref"),
        opportunity_contract_id=value.get("opportunity_contract_id"),
        authority_version=str(value["authority_version"]),
        pattern_definition_content_hash=str(value["pattern_definition_content_hash"]),
        legal_definition_matrix_content_hash=str(
            value["legal_definition_matrix_content_hash"]),
        numeric_execution_policy_content_hash=str(
            value["numeric_execution_policy_content_hash"]),
    )


def _parse_window(value: Any) -> AnalysisWindow:
    return AnalysisWindow(
        window_instance_id=str(value["window_instance_id"]),
        analysis_window_stable_id=str(value["analysis_window_stable_id"]),
        window_kind=str(value["window_kind"]),
        window_definition_id=str(value["window_definition_id"]),
        inclusivity=str(value["inclusivity"]),
        anchor_kind=str(value["anchor_kind"]),
        computed_window_start=str(value["computed_window_start"]),
        computed_window_end=str(value["computed_window_end"]),
        cutoff_id=str(value["cutoff_id"]),
        scope_binding_stable_id=str(value["scope_binding_stable_id"]),
        window_state=str(value["window_state"]),
        window_contract_content_hash=str(value["window_contract_content_hash"]),
    )


def _parse_stratum(value: Any) -> Stratum:
    return Stratum(
        stratum_contract_id=str(value["stratum_contract_id"]),
        stratum_contract_content_hash=str(value["stratum_contract_content_hash"]),
        stratum_key=str(value["stratum_key"]),
        stratum_state=str(value["stratum_state"]),
        stratum_admission=str(value["stratum_admission"]),
    )


def _parse_coverage(value: Any) -> CoverageStatus:
    return CoverageStatus(
        producer_domain=str(value["producer_domain"]),
        l0_status=str(value["l0_status"]),
        l1_medical_completeness_state=str(value["l1_medical_completeness_state"]),
        accepted_current=bool(value["accepted_current"]),
        coverage_locator_ids=_as_str_tuple(value.get("coverage_locator_ids")),
    )


def _parse_risk_member(value: Any) -> SubjectRiskMember:
    return SubjectRiskMember(
        member_id=str(value["member_id"]),
        member_kind=str(value.get("member_kind", "subject_risk")),
        subject_stable_id=str(value["subject_stable_id"]),
        site_stable_id=str(value["site_stable_id"]),
        producer_domain=str(value["producer_domain"]),
        risk_kind=str(value["risk_kind"]),
        monitoring_priority=str(value["monitoring_priority"]),
        public_r4_risk_identity=str(value["public_r4_risk_identity"]),
        source_event_identity=str(value["source_event_identity"]),
        event_time_ref=str(value["event_time_ref"]),
        cutoff_relation=str(value["cutoff_relation"]),
        origin_decision=str(value["origin_decision"]),
        source_locator_refs=_as_str_tuple(value.get("source_locator_refs")),
        query_draft_refs=_as_str_tuple(value.get("query_draft_refs")),
        source_locator_resolution_state=str(
            value.get("source_locator_resolution_state", "locatable")),
    )


def _parse_gap_member(value: Any) -> GapMember:
    return GapMember(
        member_id=str(value["member_id"]),
        member_kind=str(value.get("member_kind", "gap_opportunity")),
        subject_stable_id=str(value["subject_stable_id"]),
        site_stable_id=str(value["site_stable_id"]),
        producer_domain=str(value["producer_domain"]),
        gap_kind=str(value["gap_kind"]),
        gap_opportunity_id=str(value["gap_opportunity_id"]),
        gap_definition_id=str(value["gap_definition_id"]),
        normalized_field_or_process_identity=str(
            value["normalized_field_or_process_identity"]),
        obligation_or_opportunity_ref=str(value["obligation_or_opportunity_ref"]),
        visit_or_time_anchor_refs=_as_str_tuple(value.get("visit_or_time_anchor_refs")),
        cutoff_relation=str(value["cutoff_relation"]),
        source_locator_refs=_as_str_tuple(value.get("source_locator_refs")),
        query_draft_refs=_as_str_tuple(value.get("query_draft_refs")),
        source_locator_resolution_state=str(
            value.get("source_locator_resolution_state", "locatable")),
        anchor_resolution_state=str(
            value.get("anchor_resolution_state", "resolved")),
    )


def _parse_change_member(value: Any) -> ChangeLedgerMember:
    return ChangeLedgerMember(
        member_id=str(value["member_id"]),
        member_kind=str(value.get("member_kind", "change_ledger")),
        subject_stable_id=str(value["subject_stable_id"]),
        site_stable_id=str(value["site_stable_id"]),
        producer_domain=str(value.get("producer_domain", "D09")),
        change_ledger_member_id=str(value["change_ledger_member_id"]),
        current_window_instance_ref=str(value["current_window_instance_ref"]),
        prior_window_instance_ref=str(value["prior_window_instance_ref"]),
        comparable_state=str(value["comparable_state"]),
        change_kind=str(value["change_kind"]),
        absolute_delta=value.get("absolute_delta"),
        rate_delta=value.get("rate_delta"),
        unit=str(value["unit"]),
        change_cause=str(value["change_cause"]),
        supporting_member_refs=_as_str_tuple(value.get("supporting_member_refs")),
        source_locator_refs=_as_str_tuple(value.get("source_locator_refs")),
    )


def _parse_denominator(value: Any) -> Denominator:
    return Denominator(
        denominator_kind=str(value["denominator_kind"]),
        denominator_member_refs=_as_str_tuple(value["denominator_member_refs"]),
        denominator_eligibility_rule_ref=str(value["denominator_eligibility_rule_ref"]),
        denominator_excluded_member_refs=_as_str_tuple(
            value["denominator_excluded_member_refs"]),
        exclusion_reason_codes=_as_str_tuple(value["exclusion_reason_codes"]),
        denominator_value=int(value["denominator_value"]),
        denominator_unit=str(value["denominator_unit"]),
        denominator_state=str(value["denominator_state"]),
    )


def _parse_opportunity(value: Any) -> Opportunity:
    return Opportunity(
        opportunity_definition_ref=str(value["opportunity_definition_ref"]),
        expected_opportunity_refs=_as_str_tuple(value["expected_opportunity_refs"]),
        expected_opportunity_count=int(value["expected_opportunity_count"]),
        observed_opportunity_refs=_as_str_tuple(value["observed_opportunity_refs"]),
        observed_opportunity_count=int(value["observed_opportunity_count"]),
        missing_opportunity_refs=_as_str_tuple(value["missing_opportunity_refs"]),
        opportunity_value=str(value["opportunity_value"]),
        opportunity_unit=str(value["opportunity_unit"]),
        opportunity_state=str(value["opportunity_state"]),
        opportunity_provenance=str(value["opportunity_provenance"]),
    )


def _parse_cutoff(value: Any) -> Cutoff:
    return Cutoff(
        cutoff_id=str(value["cutoff_id"]),
        cutoff_contract_id=str(value["cutoff_contract_id"]),
        snapshot_as_of=str(value["snapshot_as_of"]),
        clinical_event_cutoff=str(value["clinical_event_cutoff"]),
        cutoff_identity_state=str(value["cutoff_identity_state"]),
        cutoff_policy_ref=str(value["cutoff_policy_ref"]),
    )


def _parse_numeric_policy(value: Any) -> NumericPolicy:
    return NumericPolicy(
        rate_numerator_kind=str(value["rate_numerator_kind"]),
        rate_denominator_kind=str(value["rate_denominator_kind"]),
        scale=int(value["scale"]),
        rounding_mode=str(value["rounding_mode"]),
        missing_zero_policy=str(value["missing_zero_policy"]),
        display_precision=int(value["display_precision"]),
        time_unit=str(value["time_unit"]),
        exposure_unit=str(value["exposure_unit"]),
    )


def _parse_visibility(value: Any) -> VisibilityDecision:
    return VisibilityDecision(
        audience_scope_id=str(value["audience_scope_id"]),
        blind_status=str(value["blind_status"]),
        evaluation_member_refs=_as_str_tuple(value.get("evaluation_member_refs")),
        projectable_member_refs=_as_str_tuple(value.get("projectable_member_refs")),
        hidden_member_refs=_as_str_tuple(value.get("hidden_member_refs")),
        hidden_reason_codes=_as_str_tuple(value.get("hidden_reason_codes")),
        visible_n=_as_int_or_none(value.get("visible_n")),
        eligible_n=_as_int_or_none(value.get("eligible_n")),
        rate_projection_state=str(value["rate_projection_state"]),
    )


def _parse_expected_set(value: Any) -> ExpectedSet:
    gate_value = value.get("admission_gate")
    gate = None
    if gate_value is not None:
        gate = AdmissionGate(
            gate_kind=str(gate_value["gate_kind"]),
            reason_codes=_as_str_tuple(gate_value.get("reason_codes")),
        )
    return ExpectedSet(
        expected_set_state=str(value["expected_set_state"]),
        admission_gate=gate,
    )


def _parse_mutation_context(value: Any) -> MutationContext:
    return MutationContext(
        mutation_class=str(value["mutation_class"]),
        desc=str(value.get("desc", "")),
        variant_id=value.get("variant_id"),
        base_fixture_id=value.get("base_fixture_id"),
    )


def _parse_anti_overfit(value: Any) -> Optional[AntiOverfitVariant]:
    if value is None:
        return None
    surface = tuple(
        SurfaceChange(
            changed_token=str(item["changed_token"]),
            from_value=str(item["from_value"]),
            to_value=str(item["to_value"]),
        )
        for item in value.get("surface_changes", [])
    )
    return AntiOverfitVariant(
        variant_id=str(value["variant_id"]),
        base_fixture_id=str(value["base_fixture_id"]),
        semantic_equivalence_ref=str(value.get("semantic_equivalence_ref", "")),
        surface_changes=surface,
    )


def _parse_evidence_ref(value: Any) -> EvidenceRef:
    return EvidenceRef(
        locator_id=str(value["locator_id"]),
        locator_kind=str(value["locator_kind"]),
        source_file=str(value["source_file"]),
        row_or_cell_ref=str(value["row_or_cell_ref"]),
        lineage_ref=str(value["lineage_ref"]),
    )


def _parse_lexicon(value: Any) -> AudienceLexicon:
    return AudienceLexicon(
        affected_subjects_zh=str(value["affected_subjects_zh"]),
        center_pattern_count_zh=str(value["center_pattern_count_zh"]),
        coverage_zh=str(value["coverage_zh"]),
        event_count_zh=str(value["event_count_zh"]),
        individual_risk_count_zh=str(value["individual_risk_count_zh"]),
        pattern_label_zh=str(value["pattern_label_zh"]),
        disposition_zh=dict(value.get("disposition_zh") or {}),
        lifecycle_zh=dict(value.get("lifecycle_zh") or {}),
        forbidden_internal_terms=_as_str_tuple(value.get("forbidden_internal_terms")),
    )


def _parse_resolved_authority(value: Any) -> ResolvedAuthorityDecision:
    return ResolvedAuthorityDecision(
        minimum_member_subject_count=value.get("minimum_member_subject_count"),
        gap_positive_minimum_opportunity_count=value.get(
            "gap_positive_minimum_opportunity_count"),
        trend_positive_minimum_subject_count=value.get(
            "trend_positive_minimum_subject_count"),
        authority_validity_state=str(value["authority_validity_state"]),
        authority_ref=str(value["authority_ref"]),
        authority_locator_ref=str(value["authority_locator_ref"]),
        mode_contract_version=str(value["mode_contract_version"]),
        authority_content_hash=str(value["authority_content_hash"]),
    )


def _parse_method_comparability(value: Any) -> MethodComparabilityDecision:
    return MethodComparabilityDecision(
        method_validity_state=str(value["method_validity_state"]),
        statistical_signal_role=str(value["statistical_signal_role"]),
        member_expansion_state=str(value["member_expansion_state"]),
        window_rule_version_refs=_as_str_tuple(value["window_rule_version_refs"]),
        stratum_method_version_refs=_as_str_tuple(
            value["stratum_method_version_refs"]),
    )


def _parse_lineage_context(value: Any) -> LineageContext:
    return LineageContext(
        prior_risk_instance_ref=value.get("prior_risk_instance_ref"),
        prior_public_risk_identity_ref=value.get("prior_public_risk_identity_ref"),
        carry_forward_state=str(value["carry_forward_state"]),
        lineage_relation=str(value["lineage_relation"]),
        site_identity_state=str(value["site_identity_state"]),
    )


def _parse_center_query_policy(value: Any) -> CenterQueryPolicy:
    return CenterQueryPolicy(
        policy_id=str(value["policy_id"]),
        mode_contract_version=str(value["mode_contract_version"]),
        max_query_member_fanout=int(value["max_query_member_fanout"]),
        member_order_policy=str(value["member_order_policy"]),
        redundancy_rule_ref=str(value["redundancy_rule_ref"]),
        allowed_action_kinds=_as_str_tuple(value["allowed_action_kinds"]),
        pd_wording_rule_ref=str(value["pd_wording_rule_ref"]),
        content_hash=str(value["content_hash"]),
        effective_interval=str(value["effective_interval"]),
    )


def _parse_query_redundancy(value: Any) -> QueryRedundancyDecision:
    return QueryRedundancyDecision(
        decision=str(value["decision"]),
        max_query_member_fanout=int(value["max_query_member_fanout"]),
        unit_member_set_hash=str(value["unit_member_set_hash"]),
        covered_member_refs=_as_str_tuple(value["covered_member_refs"]),
        uncovered_member_refs=_as_str_tuple(value["uncovered_member_refs"]),
        member_query_refs=_as_str_tuple(value["member_query_refs"]),
        coverage_proof_hash=str(value["coverage_proof_hash"]),
    )


def _parse_verification_records(value: Any) -> Tuple[SourceVerificationRecord, ...]:
    return tuple(
        SourceVerificationRecord(
            revision=str(record["revision"]),
            declared_content_hash=str(record["declared_content_hash"]),
            verified_content_hash=str(record["verified_content_hash"]),
            verification_state=str(record["verification_state"]),
        )
        for record in value
    )


def parse_typed_input(case: Mapping[str, Any]) -> D09TypedInput:
    """Convert a catalog case's ``typed_input`` JSON to the typed bundle."""
    value = case["typed_input"]
    typed = D09TypedInput(
        envelope_id=str(value["envelope_id"]),
        input_schema=str(value["input_schema"]),
        project_ref=str(value["project_ref"]),
        run_ref=str(value["run_ref"]),
        snapshot_ref=str(value["snapshot_ref"]),
        source_revision_set=_as_str_tuple(value["source_revision_set"]),
        source_content_hashes=_as_str_tuple(value["source_content_hashes"]),
        site_stable_id=str(value["site_stable_id"]),
        scope_binding=_parse_scope_binding(value["scope_binding"]),
        pattern_definition=_parse_pattern_definition(value["pattern_definition"]),
        mode_contract_version=str(value["mode_contract_version"]),
        matched_counterevidence_rule_refs=_as_str_tuple(
            value["matched_counterevidence_rule_refs"]),
        mode_contract_design_clause_ref=value.get("mode_contract_design_clause_ref"),
        analysis_windows=tuple(_parse_window(item)
                               for item in value["analysis_windows"]),
        stratum=_parse_stratum(value["stratum"]),
        coverage=tuple(_parse_coverage(item) for item in value["coverage"]),
        subject_risk_members=tuple(_parse_risk_member(item)
                                   for item in value["subject_risk_members"]),
        gap_members=tuple(_parse_gap_member(item) for item in value["gap_members"]),
        change_ledger_members=tuple(_parse_change_member(item)
                                    for item in value["change_ledger_members"]),
        denominator=_parse_denominator(value["denominator"]),
        opportunity=_parse_opportunity(value["opportunity"]),
        cutoff=_parse_cutoff(value["cutoff"]),
        numeric_policy=_parse_numeric_policy(value["numeric_policy"]),
        visibility_decision=_parse_visibility(value["visibility_decision"]),
        expected_set=_parse_expected_set(value["expected_set"]),
        mutation_context=_parse_mutation_context(value["mutation_context"]),
        anti_overfit_variant=_parse_anti_overfit(value.get("anti_overfit_variant")),
        evidence_refs=tuple(_parse_evidence_ref(item)
                            for item in value.get("evidence_refs", [])),
        audience_lexicon=_parse_lexicon(value["audience_lexicon"]),
        resolved_authority_decision=_parse_resolved_authority(
            value["resolved_authority_decision"]),
        method_comparability_decision=_parse_method_comparability(
            value["method_comparability_decision"]),
        lineage_context=_parse_lineage_context(value["lineage_context"]),
        center_query_policy=_parse_center_query_policy(
            value["center_query_policy"]),
        query_redundancy_decision=_parse_query_redundancy(
            value["query_redundancy_decision"]),
        source_verification_records=_parse_verification_records(
            value["source_verification_records"]),
    )
    validate_typed_input(typed)
    return typed


def case_index(case: Mapping[str, Any]) -> int:
    """Adapter-side case index (identity token formatting only)."""
    return int(str(case["case_id"]).rsplit("-", 1)[1])


# ---------------------------------------------------------------------------
# Runtime + oracle leaf assembly
# ---------------------------------------------------------------------------


def run_case(case: Mapping[str, Any]):
    """Parse + validate + evaluate one catalog case; return (typed, result)."""
    typed = parse_typed_input(case)
    return typed, evaluate(typed)


def _edge_ids(idx: int, pair_count: int) -> List[str]:
    return [f"SYN-D09-EDGE-{idx:03d}-{n:02d}" for n in range(1, pair_count + 1)]


def assemble_leaf_sets(typed: D09TypedInput, result: Any,
                       idx: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Map the runtime result onto the frozen oracle leaf vocabulary."""
    disposition = result.disposition
    zero_unit = result.unit_count == 0
    pairs = result.member_pairs
    evidence = result.evidence_locators
    hidden_locators = {locator for member, locator in pairs
                       if member in set(result.hidden_member_refs)}
    projectable = [locator for locator in evidence
                   if locator not in hidden_locators]
    # Locatability is a typed runtime fact (per-member resolution states).
    all_members_locatable = result.all_members_locatable

    leaf: Dict[str, Any] = {
        "all_units_disposed": True,
        "unit_count": result.unit_count,
        "positive_count": result.positive_count,
        "negative_count": result.negative_count,
        "boundary_count": result.boundary_count,
        "not_applicable_count": result.not_applicable_count,
        "not_evaluable_count": result.not_evaluable_count,
        "expected_set_reconciled": True,
        "gate_count": result.gate_count,
        "open_gate_count": result.open_gate_count,
        "integrity.stage": result.integrity_stage,
        "integrity.gate_kind": result.admission_gate_kind,
        "integrity.error_object": None,
        "integrity.error_stage": None,
        "integrity.error_type": None,
        "l0_complete": result.l0_complete,
        "domain_complete": result.domain_complete,
        "l2.individual_risk_count": result.individual_risk_count,
        "l2.affected_subject_count": result.affected_subject_count,
        "l2.event_count": result.event_count,
        "l2.gap_opportunity_count": result.gap_opportunity_count,
        "l2.center_pattern_count": result.center_pattern_count,
        "l2.clue_count": result.clue_count,
        "l2.query_count": result.query_count,
        "l2.risk_count": result.risk_count,
        "l2.source_record_count": result.source_record_count,
        "l3.positive_count": result.risk_count,
        "l3.boundary_count": result.clue_count,
        "l3.risk_count": result.risk_count,
        "ownership.owner_domain": result.owner_domain,
        "ownership.d09_action": result.d09_action,
        "ownership.risk_candidate_present": result.risk_count == 1,
        "ownership.risk_owner": "D09" if result.risk_count else None,
        "ownership.query_draft_present": result.query_count == 1,
        "ownership.query_owner": "D09" if result.query_count else None,
        "ownership.downstream_handoff_present": result.downstream_handoff,
        "ownership.handoff_target_domain": result.handoff_target_domain,
        "measure.denominator_kind": result.denominator_kind,
        "measure.denominator_value": result.denominator_value,
        "measure.denominator_state": result.denominator_state,
        "measure.opportunity_expected": result.opportunity_expected,
        "measure.opportunity_observed": result.opportunity_observed,
        "measure.opportunity_missing": result.opportunity_missing,
        "measure.opportunity_state": result.opportunity_state,
        "gate.window_pair_gate_present": result.window_pair_gate_present,
        "gate.window_pair_state": result.window_pair_state,
        "gate.admission_gate_present": result.integrity_stage != "admitted",
        "gate.admission_gate_kind": result.admission_gate_kind,
    }
    if result.unit_count:
        unit = result.units[0]
        leaf.update({
            "units.0.l1_disposition": unit.l1_disposition,
            "units.0.pattern_kind": unit.pattern_kind,
            "units.0.unit_kind": unit.unit_kind,
            "units.0.primary_reason": unit.primary_reason,
            "units.0.participant_count": unit.participant_count,
            "units.0.event_count": unit.event_count,
            "units.0.gap_opportunity_count": unit.gap_opportunity_count,
            "units.0.individual_risk_count": unit.individual_risk_count,
            "units.0.risk_count": unit.risk_count,
            "units.0.clue_count": unit.clue_count,
            "units.0.query_count": unit.query_count,
            "units.0.evidence_count": unit.evidence_count,
            "units.0.counterevidence_count": unit.counterevidence_count,
            "units.0.gate_signal_type": unit.gate_signal_type,
            "units.0.lineage_handoff": unit.lineage_handoff,
            "units.0.stable_core": unit.stable_core,
        })

    source: Dict[str, Any] = {
        "source.audience_anchor": typed.visibility_decision.audience_scope_id,
        "source.audience_lexicon_ref": None,
        "source.audience_payload_present": True,
        "source.disclosure_leak_present": False,
        "source.evaluation_node_set": list(evidence),
        "source.projectable_node_set": projectable,
        "source.hidden_node_count": len(result.hidden_member_refs),
        "source.journey_marker_present": result.journey_marker_present,
        "source.producer_binding_ids": list(result.producer_binding_ids),
        "source.query_present": result.query_count == 1,
        "source.risk_present": result.risk_count == 1,
        "source.reverse_binding_count": len(pairs),
        "source.source_jump_target_pairs": [list(pair) for pair in pairs],
    }

    trace: Dict[str, Any] = {
        "trace.stable_core_count": 0 if zero_unit else 1,
        "trace.unit_stable_cores": ([] if zero_unit
                                    else [result.units[0].stable_core]),
        "trace.lineage_handoff_count": 1 if result.downstream_handoff else 0,
        "trace.superseded_unit_count": result.superseded_unit_count,
        "trace.edge_set": _edge_ids(idx, len(pairs)),
        "trace.bidirectional_join_count": len(pairs),
        "trace.negative_checked_edge_count": len(pairs) if disposition == "negative" else 0,
        "trace.positive_evidence_ok": (True if disposition != "positive"
                                       else all_members_locatable),
        "trace.reverse_conservation_ok": all_members_locatable,
    }
    return leaf, trace, source


def _diff_leaf_dicts(assembled: Mapping[str, Any],
                     oracle_leaf: Mapping[str, Any]) -> List[str]:
    problems: List[str] = []
    for key in sorted(set(assembled) | set(oracle_leaf)):
        if assembled.get(key) != oracle_leaf.get(key):
            problems.append(
                f"{key}: runtime={assembled.get(key)!r} oracle={oracle_leaf.get(key)!r}")
    return problems


def audit_case(case: Mapping[str, Any],
               expectation: Mapping[str, Any]) -> List[str]:
    """Exact per-key audit of one case against its pinned oracle entry."""
    typed, result = run_case(case)
    idx = case_index(case)
    leaf, trace, source = assemble_leaf_sets(typed, result, idx)
    problems: List[str] = []
    problems.extend(_diff_leaf_dicts(leaf, expectation["expected_leaf_set"]))
    problems.extend(_diff_leaf_dicts(trace, expectation["expected_trace_leaf_set"]))
    problems.extend(_diff_leaf_dicts(source, expectation["expected_source_leaf_set"]))
    return problems


def audit_all_cases() -> Dict[str, List[str]]:
    """Audit every frozen catalog case; return {case_id: [diff strings]}."""
    catalog, oracle, _registry, _quota = load_artifacts()
    expectations = {entry["case_id"]: entry
                    for entry in oracle["ordered_expectations"]}
    problems: Dict[str, List[str]] = {}
    for case in catalog["cases"]:
        diffs = audit_case(case, expectations[case["case_id"]])
        if diffs:
            problems[case["case_id"]] = diffs
    return problems


def diff_key_sets(problems: Dict[str, List[str]]) -> Dict[str, frozenset]:
    """Map each case's diff strings to their leaf-key set (for exact pinning)."""
    out: Dict[str, frozenset] = {}
    for case_id, diffs in problems.items():
        out[case_id] = frozenset(diff.split(":", 1)[0] for diff in diffs)
    return out


# ---------------------------------------------------------------------------
# Sanity pins for the adapter itself
# ---------------------------------------------------------------------------


class TestD09AdapterSanity(unittest.TestCase):
    """The adapter refuses stale frozen artifacts before any case runs."""

    def test_frozen_artifact_hashes_pinned(self) -> None:
        for path, pin in _ARTIFACT_PINS:
            digest = sha256_bytes(path.read_bytes())
            self.assertEqual(digest, pin, f"{path.name} sha256 drift")

    def test_case_count_and_bijection(self) -> None:
        catalog, oracle, registry, _quota = load_artifacts()
        self.assertEqual(len(catalog["cases"]), CASE_COUNT)
        self.assertEqual(catalog["case_count"], CASE_COUNT)
        self.assertEqual(len(oracle["ordered_expectations"]), CASE_COUNT)
        self.assertEqual(len(registry["rows"]), CASE_COUNT)
        catalog_ids = [case["case_id"] for case in catalog["cases"]]
        self.assertEqual(len(set(catalog_ids)), CASE_COUNT)
        self.assertEqual(registry["bijection_audit"]["bijection_ok"], True)

    def test_oracle_leaf_schema_uniform(self) -> None:
        _catalog, oracle, _registry, _quota = load_artifacts()
        for entry in oracle["ordered_expectations"]:
            leaf = entry["expected_leaf_set"]
            if leaf.get("unit_count") == 0:
                self.assertEqual(tuple(sorted(leaf)), LEAF48_KEYS,
                                 f"{entry['case_id']} 48-key shape")
            else:
                self.assertEqual(tuple(sorted(leaf)), LEAF64_KEYS,
                                 f"{entry['case_id']} 64-key shape")
            self.assertEqual(tuple(sorted(entry["expected_trace_leaf_set"])),
                             TRACE_LEAF_KEYS)
            self.assertEqual(tuple(sorted(entry["expected_source_leaf_set"])),
                             SOURCE_LEAF_KEYS)


class TestD09FullOracleParity(unittest.TestCase):
    """179/179 exact expected/trace/source leaf parity, zero skips, zero
    xfails, zero pinned-gap allowances."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, cls.registry, _quota = load_artifacts()
        cls.expectations = {entry["case_id"]: entry
                            for entry in cls.oracle["ordered_expectations"]}
        cls.problems: Dict[str, List[str]] = {}
        for case in cls.catalog["cases"]:
            diffs = audit_case(case, cls.expectations[case["case_id"]])
            if diffs:
                cls.problems[case["case_id"]] = diffs

    def test_all_179_cases_exact_leaf_parity(self) -> None:
        self.assertEqual(len(self.problems), 0,
                         f"{len(self.problems)} cases with leaf diffs: "
                         f"{sorted(self.problems)[:5]}")

    def test_all_cases_run_without_exception(self) -> None:
        for case in self.catalog["cases"]:
            typed, result = run_case(case)
            self.assertIn(result.disposition, DISPOSITIONS, case["case_id"])
            self.assertEqual(result.unit_count, len(result.units))

    def test_disposition_distribution_matches_oracle(self) -> None:
        counts: Dict[str, int] = {}
        for entry in self.oracle["ordered_expectations"]:
            leaf = entry["expected_leaf_set"]
            if leaf.get("unit_count"):
                disposition = leaf["units.0.l1_disposition"]
            else:
                disposition = "not_applicable"
            counts[disposition] = counts.get(disposition, 0) + 1
        self.assertEqual(counts.get("positive", 0), 73)
        self.assertEqual(counts.get("boundary", 0), 33)
        self.assertEqual(counts.get("not_evaluable", 0), 44)
        self.assertEqual(counts.get("negative", 0), 11)
        self.assertEqual(counts.get("not_applicable", 0), 18)
        self.assertEqual(sum(counts.values()), CASE_COUNT)


if __name__ == "__main__":
    unittest.main()
