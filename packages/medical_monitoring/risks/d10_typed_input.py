"""Pure structural D10 mapping converter (mapping -> immutable typed objects).

Migrated from the frozen R4 test-only ``d10_adapter`` (B6 dependency closure):
this module carries only the exact-key ``mapping -> typed-object`` conversion
used to build a :class:`~medical_monitoring.risks.d10_contracts.D10TypedInput`
from a catalog/synthetic ``typed_input`` dict.  The conversion is purely
structural -- it copies exact-key JSON onto the closed dataclasses and never
infers identity, treatment group, endpoint, severity or same-origin
relationships from Chinese titles, free text, display order, center names or
model summaries.  ``mutation_context`` / ``anti_overfit_variant`` are carried
as opaque shape-only audit metadata and are never read by the evaluator's
decision path.

Deliberately NOT migrated from the frozen adapter: frozen-artifact SHA pins,
catalog/oracle/registry/quota loading, and the oracle leaf-vocabulary mapping.
"""

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Tuple

from .d10_contracts import (
    AdmissionGate,
    AnalysisPopulation,
    AnalysisWindow,
    AntiOverfitVariant,
    AudienceText,
    ChangeDecision,
    ComparisonGate,
    CountLayers,
    CoverageStatus,
    CutoffAdvance,
    D10TypedInput,
    DeepLink,
    Denominator,
    EfficacyContext,
    EvaluationLimits,
    EvidenceRef,
    ExpectedSet,
    Hotspot,
    LegalMatrixRow,
    MeasureOriginBinding,
    Member,
    ModeContract,
    ModelEvidence,
    MutationContext,
    NumeratorLedger,
    NumericPolicy,
    Opportunity,
    QueryDecision,
    RuleHit,
    SafetyContext,
    ScopeBinding,
    SignalDefinition,
    SiteLedger,
    SourceRevisionPair,
    Stratum,
    SurfaceChange,
    TimeSegment,
    VisibilityDecision,
    WindowPairGate,
)


# Structural helpers
# ---------------------------------------------------------------------------


def _as_tuple(value: Any) -> Any:
    """Recursively freeze lists to tuples (keeps ``None`` and scalars)."""
    if isinstance(value, list):
        return tuple(_as_tuple(item) for item in value)
    return value


# ---------------------------------------------------------------------------
# Typed catalog -> immutable typed objects
# ---------------------------------------------------------------------------


def _parse_source_pairs(value: List[Mapping[str, Any]]) -> Tuple[SourceRevisionPair, ...]:
    return tuple(SourceRevisionPair(
        revision_id=str(pair["revision_id"]),
        content_hash=str(pair["content_hash"]),
    ) for pair in value)


def _parse_scope(value: Mapping[str, Any]) -> ScopeBinding:
    return ScopeBinding(
        scope_binding_id=str(value["scope_binding_id"]),
        scope_type=str(value["scope_type"]),
        scope_equality_decision=str(value["scope_equality_decision"]),
        scope_binding_hash=str(value["scope_binding_hash"]),
    )


def _parse_mode(value: Mapping[str, Any]) -> ModeContract:
    return ModeContract(
        mode_contract_version=str(value["mode_contract_version"]),
        mode_contract_content_hash=str(value["mode_contract_content_hash"]),
        design_applicable_state=str(value["design_applicable_state"]),
        design_clause_ref=value.get("design_clause_ref"),
    )


def _parse_signal(value: Mapping[str, Any]) -> SignalDefinition:
    return SignalDefinition(
        signal_definition_id=str(value["signal_definition_id"]),
        signal_kind=str(value["signal_kind"]),
        clinical_claim_token=str(value["clinical_claim_token"]),
        d10_action=str(value["d10_action"]),
        risk_or_outcome_domain=str(value["risk_or_outcome_domain"]),
        required_producer_domains=_as_tuple(value["required_producer_domains"]),
        positive_rule_ref=str(value.get("positive_rule_ref", "")),
        counterevidence_rule_refs=_as_tuple(value.get("counterevidence_rule_refs", [])),
        legal_matrix_row_ref=str(value.get("legal_matrix_row_ref", "")),
        authority_locator=str(value.get("authority_locator", "")),
    )


def _parse_legal_row(value: Mapping[str, Any]) -> LegalMatrixRow:
    return LegalMatrixRow(
        row_id=str(value["row_id"]),
        signal_kind=str(value["signal_kind"]),
        clinical_claim_token=str(value["clinical_claim_token"]),
        d10_action=str(value["d10_action"]),
        row_hash=str(value["row_hash"]),
    )


def _parse_expected_set(value: Mapping[str, Any]) -> ExpectedSet:
    gate = value.get("admission_gate")
    admission_gate = None
    if gate is not None:
        admission_gate = AdmissionGate(
            gate_kind=str(gate["gate_kind"]),
            reason_codes=_as_tuple(gate.get("reason_codes", [])),
        )
    return ExpectedSet(
        expected_set_state=str(value["expected_set_state"]),
        admission_gate=admission_gate,
    )


def _parse_window(value: Mapping[str, Any]) -> AnalysisWindow:
    return AnalysisWindow(
        analysis_window_stable_id=str(value["analysis_window_stable_id"]),
        window_instance_id=str(value["window_instance_id"]),
        window_definition_id=str(value["window_definition_id"]),
        window_definition_hash=str(value["window_definition_hash"]),
        window_kind=str(value["window_kind"]),
        window_state=str(value["window_state"]),
        window_start=value.get("window_start"),
        window_end=value.get("window_end"),
        cutoff_ref=value.get("cutoff_ref"),
    )


def _parse_stratum(value: Mapping[str, Any]) -> Stratum:
    return Stratum(
        stratum_contract_id=str(value["stratum_contract_id"]),
        stratum_key=str(value["stratum_key"]),
        stratum_state=str(value["stratum_state"]),
        stratum_admission=str(value["stratum_admission"]),
    )


def _parse_comparison(value: Mapping[str, Any]) -> ComparisonGate:
    return ComparisonGate(
        comparison_state=str(value["comparison_state"]),
        comparison_reference_stable_id=str(value["comparison_reference_stable_id"]),
        required_site_count_ref=str(value.get("required_site_count_ref", "")),
        observed_eligible_site_count=int(value["observed_eligible_site_count"]),
        eligible_site_refs=_as_tuple(value.get("eligible_site_refs", [])),
        excluded_site_refs=_as_tuple(value.get("excluded_site_refs", [])),
        reason_codes=_as_tuple(value.get("reason_codes", [])),
        permitted_output=str(value.get("permitted_output", "")),
    )


def _parse_window_pair(value: Mapping[str, Any]) -> WindowPairGate:
    return WindowPairGate(
        pair_state=str(value["pair_state"]),
        required_window_count_ref=str(value.get("required_window_count_ref", "")),
        observed_unique_window_count=int(value["observed_unique_window_count"]),
        reason_codes=_as_tuple(value.get("reason_codes", [])),
        permitted_output=str(value.get("permitted_output", "")),
    )


def _parse_site_ledger(value: Mapping[str, Any]) -> SiteLedger:
    return SiteLedger(
        ledger_id=str(value["ledger_id"]),
        site_ref=str(value["site_ref"]),
        site_activation_state=str(value.get("site_activation_state", "active")),
        identity_state=str(value.get("identity_state", "stable")),
        eligible_subject_refs=_as_tuple(value.get("eligible_subject_refs", [])),
        treated_subject_refs=_as_tuple(value.get("treated_subject_refs", [])),
        evaluable_subject_refs=_as_tuple(value.get("evaluable_subject_refs", [])),
        d09_pattern_refs=_as_tuple(value.get("d09_pattern_refs", [])),
        coverage_refs=_as_tuple(value.get("coverage_refs", [])),
        site_activation_ref=str(value.get("site_activation_ref", "")),
    )


def _parse_member(value: Mapping[str, Any]) -> Member:
    return Member(
        member_ref=str(value["member_ref"]),
        member_kind=str(value["member_kind"]),
        aggregation_plane=str(value["aggregation_plane"]),
        producer_domain=str(value["producer_domain"]),
        member_scope_state=str(value.get("member_scope_state", "in_scope")),
        site_stable_id=str(value.get("site_stable_id", "")),
        subject_stable_id=value.get("subject_stable_id"),
        monitoring_priority=str(value.get("monitoring_priority", "medium")),
        accepted_current_state=str(value.get("accepted_current_state", "accepted_current")),
        locator_resolution_state=str(value.get("locator_resolution_state", "locatable")),
        source_locator_refs=_as_tuple(value.get("source_locator_refs", [])),
        descendant_member_refs=_as_tuple(value.get("descendant_member_refs", [])),
        descendant_set_hash=value.get("descendant_set_hash"),
        treatment_role_ref=value.get("treatment_role_ref"),
    )


def _parse_numerator(value: Mapping[str, Any]) -> NumeratorLedger:
    return NumeratorLedger(
        individual_risk_count=int(value["individual_risk_count"]),
        center_pattern_count=int(value["center_pattern_count"]),
        affected_subject_count=int(value["affected_subject_count"]),
        event_or_outcome_count=int(value["event_or_outcome_count"]),
        affected_site_count=int(value["affected_site_count"]),
        numerator_member_count=int(value["numerator_member_count"]),
    )


def _parse_measure_origin(value: Optional[Mapping[str, Any]]) -> Optional[MeasureOriginBinding]:
    if value is None:
        return None
    return MeasureOriginBinding(
        binding_id=str(value["binding_id"]),
        measure_ref=str(value["measure_ref"]),
        origin_decision=str(value["origin_decision"]),
        verified_risk_refs=_as_tuple(value.get("verified_risk_refs", [])),
        distinct_risk_refs=_as_tuple(value.get("distinct_risk_refs", [])),
        ambiguous_risk_refs=_as_tuple(value.get("ambiguous_risk_refs", [])),
        candidate_risk_refs=_as_tuple(value.get("candidate_risk_refs", [])),
        candidate_partition_hash=str(value.get("candidate_partition_hash", "")),
        numerator_plane_state=str(value.get("numerator_plane_state", "single")),
        binding_hash=str(value.get("binding_hash", "")),
        source_provenance_hash=str(value.get("source_provenance_hash", "")),
    )


def _parse_denominator(value: Mapping[str, Any]) -> Denominator:
    return Denominator(
        denominator_kind=str(value["denominator_kind"]),
        denominator_value=int(value["denominator_value"]),
        recomputed_value=int(value["recomputed_value"]),
        denominator_unit=str(value.get("denominator_unit", "subject")),
        denominator_state=str(value.get("denominator_state", "closed_positive")),
        denominator_member_refs=_as_tuple(value.get("denominator_member_refs", [])),
        excluded_member_refs=_as_tuple(value.get("excluded_member_refs", [])),
        exclusion_reason_codes=_as_tuple(value.get("exclusion_reason_codes", [])),
    )


def _parse_time_segment(value: Mapping[str, Any]) -> TimeSegment:
    return TimeSegment(
        segment_id=str(value["segment_id"]),
        member_ref=str(value["member_ref"]),
        segment_kind=str(value.get("segment_kind", "subject_time")),
        start_value=int(value.get("start_value", 0)),
        end_value=int(value.get("end_value", 0)),
        raw_duration=int(value.get("raw_duration", 0)),
        normalized_duration=int(value.get("normalized_duration", 0)),
        unit=str(value.get("unit", "day")),
        inclusivity=str(value.get("inclusivity", "both_inclusive")),
        overlap_resolution_ref=value.get("overlap_resolution_ref"),
    )


def _parse_opportunity(value: Optional[Mapping[str, Any]]) -> Optional[Opportunity]:
    if value is None:
        return None
    return Opportunity(
        opportunity_definition_ref=str(value.get("opportunity_definition_ref", "")),
        expected_opportunity_count=int(value.get("expected_opportunity_count", 0)),
        observed_opportunity_count=int(value.get("observed_opportunity_count", 0)),
        missing_opportunity_refs=_as_tuple(value.get("missing_opportunity_refs", [])),
        opportunity_provenance=str(value.get("opportunity_provenance", "accepted_d05_plan")),
        opportunity_state=str(value.get("opportunity_state", "unknown")),
        complete=bool(value.get("complete", False)),
    )


def _parse_population(value: Mapping[str, Any]) -> AnalysisPopulation:
    return AnalysisPopulation(
        analysis_population_ref=str(value["analysis_population_ref"]),
        present=bool(value.get("present", True)),
        analysis_population_contract_id=str(value.get("analysis_population_contract_id", "")),
    )


def _parse_coverage(value: Mapping[str, Any]) -> CoverageStatus:
    return CoverageStatus(
        producer_domain=str(value["producer_domain"]),
        l0_status=str(value.get("l0_status", "covered")),
        l1_medical_completeness_state=str(
            value.get("l1_medical_completeness_state", "complete")),
        accepted_current=bool(value.get("accepted_current", True)),
        coverage_locator_ids=_as_tuple(value.get("coverage_locator_ids", [])),
    )


def _parse_change(value: Optional[Mapping[str, Any]]) -> Optional[ChangeDecision]:
    if value is None:
        return None
    cutoff = value.get("cutoff_advance")
    cutoff_advance = None
    if cutoff is not None:
        cutoff_advance = CutoffAdvance(
            decision_state=str(cutoff["decision_state"]),
            strict_advance_predicate_passed=bool(cutoff["strict_advance_predicate_passed"]),
            policy_semantic_hash_equal=bool(cutoff["policy_semantic_hash_equal"]),
            prior_boundary_value=cutoff.get("prior_boundary_value"),
            current_boundary_value=cutoff.get("current_boundary_value"),
        )
    return ChangeDecision(
        execution_basis=str(value["execution_basis"]),
        comparison_state=str(value["comparison_state"]),
        prior_snapshot_ref_or_none=value.get("prior_snapshot_ref_or_none"),
        data_change_refs=_as_tuple(value.get("data_change_refs", [])),
        denominator_change_refs=_as_tuple(value.get("denominator_change_refs", [])),
        coverage_change_refs=_as_tuple(value.get("coverage_change_refs", [])),
        knowledge_change_refs=_as_tuple(value.get("knowledge_change_refs", [])),
        rule_change_refs=_as_tuple(value.get("rule_change_refs", [])),
        mapping_change_refs=_as_tuple(value.get("mapping_change_refs", [])),
        model_change_refs=_as_tuple(value.get("model_change_refs", [])),
        method_change_refs=_as_tuple(value.get("method_change_refs", [])),
        population_change_refs=_as_tuple(value.get("population_change_refs", [])),
        visibility_change_refs=_as_tuple(value.get("visibility_change_refs", [])),
        mode_change_refs=_as_tuple(value.get("mode_change_refs", [])),
        cutoff_advance=cutoff_advance,
        r2_prior_ref_or_none=value.get("r2_prior_ref_or_none"),
        r2_action=value.get("r2_action") or "",
        lineage_relation=value.get("lineage_relation") or "",
        carry_forward_state=value.get("carry_forward_state") or "none",
        claimed_clinical_change_kind=value.get("claimed_clinical_change_kind"),
        claimed_primary_change_cause=value.get("claimed_primary_change_cause"),
        claimed_cutoff_state=value.get("claimed_cutoff_state"),
        data_change_kind=value.get("data_change_kind"),
    )


def _parse_visibility(value: Mapping[str, Any]) -> VisibilityDecision:
    return VisibilityDecision(
        decision_id=str(value["decision_id"]),
        blind_status=str(value.get("blind_status", "blinded")),
        audience_scope_id=str(value.get("audience_scope_id", "")),
        evaluation_member_refs=_as_tuple(value.get("evaluation_member_refs", [])),
        projectable_member_refs=_as_tuple(value.get("projectable_member_refs", [])),
        hidden_member_refs=_as_tuple(value.get("hidden_member_refs", [])),
        hidden_reason_codes=_as_tuple(value.get("hidden_reason_codes", [])),
        evaluation_site_refs=_as_tuple(value.get("evaluation_site_refs", [])),
        projectable_site_refs=_as_tuple(value.get("projectable_site_refs", [])),
        hidden_site_refs=_as_tuple(value.get("hidden_site_refs", [])),
        visible_n=int(value.get("visible_n", 0)),
        eligible_n=int(value.get("eligible_n", 0)),
        hidden_member_count=int(value.get("hidden_member_count", 0)),
        hidden_site_count=int(value.get("hidden_site_count", 0)),
        rate_projection_state=str(value.get("rate_projection_state", "permitted")),
        deep_link_eligible_member_refs=_as_tuple(
            value.get("deep_link_eligible_member_refs", [])),
        deep_link_eligible_site_refs=_as_tuple(value.get("deep_link_eligible_site_refs", [])),
        hidden_set_omitted=bool(value.get("hidden_set_omitted", False)),
        deep_link_eligible_violation=bool(value.get("deep_link_eligible_violation", False)),
        treatment_inference_attempt=bool(value.get("treatment_inference_attempt", False)),
        projectable_subject_site_pairs=_as_tuple(
            value.get("projectable_subject_site_pairs", [])),
        deep_link_eligible_subject_site_pairs=_as_tuple(
            value.get("deep_link_eligible_subject_site_pairs", [])),
    )


def _parse_query(value: Mapping[str, Any]) -> QueryDecision:
    return QueryDecision(
        decision=str(value["decision"]),
        covered_member_refs=_as_tuple(value.get("covered_member_refs", [])),
        uncovered_member_refs=_as_tuple(value.get("uncovered_member_refs", [])),
        member_query_content_identities=_as_tuple(
            value.get("member_query_content_identities", [])),
        unit_member_set_hash=str(value.get("unit_member_set_hash", "")),
        coverage_proof_hash=str(value.get("coverage_proof_hash", "")),
        max_query_member_fanout=int(value.get("max_query_member_fanout", 100)),
        member_unlistable=bool(value.get("member_unlistable", False)),
        pd_wording_state=str(value.get("pd_wording_state", "not_pd")),
        duplicate_query_attempt=bool(value.get("duplicate_query_attempt", False)),
        query_content_hash=str(value.get("query_content_hash", "")),
    )


def _parse_audience(value: Mapping[str, Any]) -> AudienceText:
    return AudienceText(
        audience_contract_id=str(value["audience_contract_id"]),
        display_language=str(value.get("display_language", "zh-CN")),
        sentence_part_kind=str(value.get("sentence_part_kind", "observed_finding")),
        basis_zh=str(value.get("basis_zh", "")),
        finding_zh=str(value.get("finding_zh", "")),
        action_zh=str(value.get("action_zh", "")),
        engineering_reference_attempt=bool(value.get("engineering_reference_attempt", False)),
        injection_blocked=bool(value.get("injection_blocked", False)),
    )


def _parse_deep_link(value: Mapping[str, Any]) -> DeepLink:
    return DeepLink(
        target_kind=str(value["target_kind"]),
        site_ref=value.get("site_ref"),
        subject_ref=value.get("subject_ref"),
        member_object_ref=value.get("member_object_ref"),
        visibility_decision_ref=str(value.get("visibility_decision_ref", "")),
        return_state_key=str(value.get("return_state_key", "")),
    )


def _parse_model(value: Optional[Mapping[str, Any]]) -> Optional[ModelEvidence]:
    if value is None:
        return None
    return ModelEvidence(
        model_evidence_id=str(value["model_evidence_id"]),
        role=str(value["role"]),
        permitted_leaf=str(value["permitted_leaf"]),
        model_id=str(value["model_id"]),
        model_version=str(value["model_version"]),
        evaluation_content_identity=str(value.get("evaluation_content_identity", "")),
        input_content_hash=str(value.get("input_content_hash", "")),
        source_revision_content_pairs=_parse_source_pairs(
            value.get("source_revision_content_pairs", [])),
        source_refs=_as_tuple(value.get("source_refs", [])),
        independent_context_hash=str(value.get("independent_context_hash", "")),
        ensemble_id=str(value.get("ensemble_id", "")),
        ensemble_size=int(value.get("ensemble_size", 1)),
        member_analysis_refs=_as_tuple(value.get("member_analysis_refs", [])),
        member_analysis_ref_set_hash=str(value.get("member_analysis_ref_set_hash", "")),
        output_identity=str(value.get("output_identity", "")),
        output_hash=str(value.get("output_hash", "")),
        adjudication_state=str(value.get("adjudication_state", "pending")),
        model_binding_hash=str(value.get("model_binding_hash", "")),
    )


def _parse_safety(value: Optional[Mapping[str, Any]]) -> Optional[SafetyContext]:
    if value is None:
        return None
    return SafetyContext(
        context_id=str(value["context_id"]),
        context_complete=bool(value.get("context_complete", False)),
        exposure_definition_ref=value.get("exposure_definition_ref"),
        coding_dictionary_ref=value.get("coding_dictionary_ref"),
        severity_scale_ref=value.get("severity_scale_ref"),
        risk_window_ref=value.get("risk_window_ref"),
        descriptive_monitoring_only=bool(value.get("descriptive_monitoring_only", True)),
    )


def _parse_efficacy(value: Optional[Mapping[str, Any]]) -> Optional[EfficacyContext]:
    if value is None:
        return None
    return EfficacyContext(
        context_id=str(value["context_id"]),
        context_complete=bool(value.get("context_complete", False)),
        endpoint_definition_ref=value.get("endpoint_definition_ref"),
        estimand_ref=value.get("estimand_ref"),
        missing_data_rule_ref=value.get("missing_data_rule_ref"),
        intercurrent_event_rule_ref=value.get("intercurrent_event_rule_ref"),
        treatment_role_authority_ref=value.get("treatment_role_authority_ref"),
        treatment_assignment_exposure_identity_ref=value.get(
            "treatment_assignment_exposure_identity_ref"),
        treatment_role_required=bool(value.get("treatment_role_required", False)),
        blind_visibility_contract_ref=value.get("blind_visibility_contract_ref"),
        descriptive_monitoring_only=bool(value.get("descriptive_monitoring_only", True)),
        estimate_kind=value.get("estimate_kind"),
        treatment_assignment_mapping_hash=value.get("treatment_assignment_mapping_hash"),
    )


def _parse_rule_hit(value: Mapping[str, Any]) -> RuleHit:
    return RuleHit(
        positive_rule_ref=str(value.get("positive_rule_ref", "")),
        hit_state=str(value.get("hit_state", "no_hit")),
        evidence_sources=_as_tuple(value.get("evidence_sources", [])),
        counterevidence_matched_refs=_as_tuple(value.get("counterevidence_matched_refs", [])),
        counterevidence_declared_refs=_as_tuple(value.get("counterevidence_declared_refs", [])),
    )


def _parse_hotspot(value: Optional[Mapping[str, Any]]) -> Optional[Hotspot]:
    if value is None:
        return None
    return Hotspot(
        hotspot_member_refs=_as_tuple(value.get("hotspot_member_refs", [])),
        hidden_in_display=bool(value.get("hidden_in_display", False)),
    )


def _parse_count_layers(value: Mapping[str, Any]) -> CountLayers:
    return CountLayers(
        layers_in_common_numerator=_as_tuple(value.get("layers_in_common_numerator", [])),
        mixed=bool(value.get("mixed", False)),
    )


def _parse_limits(value: Mapping[str, Any]) -> EvaluationLimits:
    return EvaluationLimits(
        small_sample=bool(value.get("small_sample", False)),
        limited_evidence=bool(value.get("limited_evidence", False)),
        limited_reason=value.get("limited_reason"),
    )


def _parse_numeric_policy(value: Mapping[str, Any]) -> NumericPolicy:
    return NumericPolicy(
        policy_id=str(value.get("policy_id", "")),
        allowed_estimate_kinds=_as_tuple(value.get("allowed_estimate_kinds", [])),
        decimal_context=str(value.get("decimal_context", "decimal(10,4)")),
        rounding_mode=str(value.get("rounding_mode", "half_up")),
        display_precision=int(value.get("display_precision", 1)),
        subject_time_unit=str(value.get("subject_time_unit", "day")),
        exposure_time_unit=str(value.get("exposure_time_unit", "subject_day")),
        overlap_policy=str(value.get("overlap_policy", "resolve_by_authority")),
    )


def _parse_mutation(value: Mapping[str, Any]) -> MutationContext:
    return MutationContext(
        mutation_class=value.get("mutation_class"),
        desc=value.get("desc"),
        variant_id=value.get("variant_id"),
        base_fixture_id=value.get("base_fixture_id"),
    )


def _parse_anti_overfit(value: Optional[Mapping[str, Any]]) -> Optional[AntiOverfitVariant]:
    if value is None:
        return None
    surface = tuple(SurfaceChange(
        changed_token=str(item["changed_token"]),
        from_value=str(item["from_value"]),
        to_value=str(item["to_value"]),
    ) for item in value.get("surface_changes", []))
    return AntiOverfitVariant(
        base_fixture_id=value.get("base_fixture_id"),
        semantic_equivalence_ref=value.get("semantic_equivalence_ref"),
        surface_changes=surface,
        variant_id=value.get("variant_id"),
    )


def _parse_evidence_ref(value: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        locator_id=str(value["locator_id"]),
        locator_kind=str(value.get("locator_kind", "synthetic_file")),
        source_file=str(value.get("source_file", "")),
        row_or_cell_ref=str(value.get("row_or_cell_ref", "")),
        lineage_ref=str(value.get("lineage_ref", "")),
    )


def build_typed_input(value: Mapping[str, Any]) -> D10TypedInput:
    """Convert a catalog ``typed_input`` dict into the immutable typed bundle.

    The mapping is structural only: it copies exact-key JSON onto the closed
    dataclasses and never infers semantics from free text, ids, or metadata.
    """
    typed = D10TypedInput(
        input_schema=str(value["input_schema"]),
        envelope_id=str(value["envelope_id"]),
        project_ref=str(value["project_ref"]),
        run_ref=str(value["run_ref"]),
        snapshot_ref=str(value["snapshot_ref"]),
        source_revision_content_pairs=_parse_source_pairs(
            value["source_revision_content_pairs"]),
        project_scope_binding=_parse_scope(value["project_scope_binding"]),
        mode_contract=_parse_mode(value["mode_contract"]),
        signal_definition=_parse_signal(value["signal_definition"]),
        legal_matrix_row=_parse_legal_row(value["legal_matrix_row"]),
        expected_set=_parse_expected_set(value["expected_set"]),
        analysis_windows=tuple(_parse_window(item)
                               for item in value["analysis_windows"]),
        stratum=_parse_stratum(value["stratum"]),
        comparison_gate=_parse_comparison(value["comparison_gate"]),
        window_pair_gate=_parse_window_pair(value["window_pair_gate"]),
        site_ledger=_parse_site_ledger(value["site_ledger"]),
        members=tuple(_parse_member(item) for item in value["members"]),
        numerator_ledger=_parse_numerator(value["numerator_ledger"]),
        measure_origin_binding=_parse_measure_origin(value.get("measure_origin_binding")),
        denominator=_parse_denominator(value["denominator"]),
        time_segments=tuple(_parse_time_segment(item)
                            for item in value["time_segments"]),
        opportunity=_parse_opportunity(value.get("opportunity")),
        analysis_population=_parse_population(value["analysis_population"]),
        coverage=tuple(_parse_coverage(item) for item in value["coverage"]),
        change_decision=_parse_change(value.get("change_decision")),
        visibility_decision=_parse_visibility(value["visibility_decision"]),
        query_decision=_parse_query(value["query_decision"]),
        audience_text=_parse_audience(value["audience_text"]),
        deep_links=tuple(_parse_deep_link(item) for item in value["deep_links"]),
        model_evidence=_parse_model(value.get("model_evidence")),
        safety_context=_parse_safety(value.get("safety_context")),
        efficacy_context=_parse_efficacy(value.get("efficacy_context")),
        rule_hit=_parse_rule_hit(value["rule_hit"]),
        hotspot=_parse_hotspot(value.get("hotspot")),
        count_layers=_parse_count_layers(value["count_layers"]),
        evaluation_limits=_parse_limits(value["evaluation_limits"]),
        numeric_policy=_parse_numeric_policy(value["numeric_policy"]),
        mutation_context=_parse_mutation(value["mutation_context"]),
        anti_overfit_variant=_parse_anti_overfit(value.get("anti_overfit_variant")),
        evidence_refs=tuple(_parse_evidence_ref(item)
                            for item in value.get("evidence_refs", [])),
    )
    return typed


__all__ = ["build_typed_input"]
