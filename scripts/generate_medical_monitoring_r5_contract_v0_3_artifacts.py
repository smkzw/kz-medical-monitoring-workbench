#!/usr/bin/env python3
"""Generate the deterministic R5 v0.3 contract package.

Every quota instance owns one distinct case, one JSON-Patch mutation and one
contract-rule oracle. Semantic selection never branches on case/fixture/project
identity; it uses the declared category and mutated leaf.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md"
OUT = ROOT / "artifacts/medical_monitoring_r5_contract_v0_3"

CATEGORY_SLOTS = {
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

CATEGORY_SEVERITY = {
    "authority_identity": "P1", "authority_visibility": "P1", "change_comparability": "P1", "change_cause_plane": "P1",
    "count_layer_conservation": "P1", "numerator_denominator_rate": "P1", "coverage_cutoff_limits": "P1",
    "center_pattern_individual": "P2", "center_stable_order": "P3", "inspector_evidence_order": "P2",
    "ensemble_visibility": "P1", "deep_link_identity": "P1", "return_context": "P2", "visit_semantics": "P1",
    "axis_conversion": "P1", "uncertain_dates": "P1", "eight_domain_adaptation": "P2", "encoding_registry": "P3",
    "aemh_projection": "P2", "aemh_match_history": "P2", "source_one_hop": "P1", "audience_lexicon": "P4",
    "interaction_no_mutation": "P0", "deterministic_replay": "P3", "high_density_performance": "P3",
}

ACCEPT_SLOTS = {
    *(('change_comparability', x) for x in CATEGORY_SLOTS['change_comparability']),
    ('numerator_denominator_rate', 'denominator_zero'), ('numerator_denominator_rate', 'denominator_unclosed'),
    ('coverage_cutoff_limits', 'coverage_partial'), ('coverage_cutoff_limits', 'coverage_truncated'),
    ('coverage_cutoff_limits', 'small_sample'), ('coverage_cutoff_limits', 'short_followup'),
    ('center_stable_order', 'input_permutation'), ('center_stable_order', 'stable_site_id'),
    ('ensemble_visibility', 'zero_worker'), ('ensemble_visibility', 'single_worker'),
    ('ensemble_visibility', 'unique_finding'), ('ensemble_visibility', 'graded_conflict'),
    ('ensemble_visibility', 'mutual_negation'), ('ensemble_visibility', 'baseline_miss'),
    *(('return_context', x) for x in CATEGORY_SLOTS['return_context']),
    ('axis_conversion', 'calendar_default'), ('axis_conversion', 'study_day_valid'), ('axis_conversion', 'conversion_replay'),
    *(('aemh_match_history', x) for x in CATEGORY_SLOTS['aemh_match_history'] if x != 'no_auto_close'),
    *(('deterministic_replay', x) for x in CATEGORY_SLOTS['deterministic_replay']),
}

ENUMS = {
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

def f(t: str, c: str = "one", n: bool = False) -> dict[str, object]:
    return {"type": t, "cardinality": c, "nullable": n}

OBJECTS = {
    "SourceRevisionContentPair": {"revision_id": f("str"), "content_hash": f("sha256")},
    "R5FilterState": {"severity": f("enum:severity", "many"), "domain": f("enum:domain", "many"), "site_refs": f("str", "many"), "change_kind": f("enum:change_kind", "many"), "include_low": f("bool")},
    "R5SortState": {"key": f("enum:sort_key"), "direction": f("enum:sort_direction")},
    "R5PageState": {"page_index": f("int"), "page_size": f("int")},
    "R5ScrollState": {"project_list_y": f("int"), "center_map_y": f("int"), "workspace_y": f("int")},
    "R5DomainEncodingItem": {"domain": f("enum:domain"), "event_shape": f("enum:event_shape"), "short_label_zh": f("str"), "line_style": f("enum:line_style")},
    "R5SeverityLexiconItem": {"severity": f("enum:severity"), "label_zh": f("str"), "line_weight": f("int")},
    "R5LegacyTreatmentMappingItem": {"legacy_kind": f("enum:legacy_treatment_kind"), "target_domain": f("enum:domain", n=True), "target_subtype": f("enum:journey_subtype", n=True), "mapping_authority_ref": f("str", n=True), "mapping_state": f("enum:legacy_mapping_state")},
    "R5LexiconItem": {"token": f("str"), "label_zh": f("str"), "audience_allowed": f("bool")},
    "R5AuthorityReceipt": {"public_projection_kind": f("enum:projection_kind"), "public_projection_id": f("str"), "public_projection_content_hash": f("sha256"), "evaluation_content_identities": f("sha256", "many"), "visibility_decision_id": f("str"), "visibility_decision_hash": f("sha256"), "project_ref": f("str"), "run_ref": f("str"), "snapshot_ref": f("str"), "cutoff_ref": f("str", n=True), "source_revision_content_pairs": f("SourceRevisionContentPair", "many"), "audience_contract_id": f("str")},
    "R5ProjectionInstance": {"opaque_run_ref": f("str"), "opaque_snapshot_ref": f("str"), "replay_content_identity": f("sha256"), "authority_receipt_ref": f("str"), "content_hash": f("sha256")},
    "R5ChangeBand": {"risk_ref": f("str"), "change_kind": f("enum:change_kind"), "change_cause": f("enum:change_cause", n=True), "prior_snapshot_ref": f("str", n=True), "current_snapshot_ref": f("str"), "authority_receipt_ref": f("str")},
    "R5CurrentRiskSet": {"high_risk_refs": f("str", "many"), "medium_risk_refs": f("str", "many"), "low_risk_cluster_refs": f("str", "many"), "resolved_history_refs": f("str", "many"), "authority_receipt_ref": f("str")},
    "R5QuantitativeMeasure": {"authoritative_value_ref": f("str"), "numerator_kind": f("enum:numerator_kind"), "numerator_member_refs": f("str", "many"), "numerator_value": f("decimal"), "denominator_kind": f("enum:denominator_kind"), "denominator_member_refs": f("str", "many"), "denominator_exclusion_refs": f("str", "many"), "denominator_value": f("decimal", n=True), "denominator_state": f("enum:denominator_state"), "unit": f("enum:measure_unit"), "rate_state": f("enum:rate_state"), "coverage_state": f("enum:coverage_state"), "cutoff_ref": f("str"), "evaluation_limit_refs": f("str", "many"), "authority_receipt_ref": f("str")},
    "R5ProjectCockpitProjection": {"projection_instance": f("R5ProjectionInstance"), "change_band_refs": f("str", "many"), "current_risk_set_ref": f("str"), "measure_refs": f("str", "many"), "center_map_ref": f("str"), "selected_risk_ref": f("str", n=True), "content_hash": f("sha256")},
    "R5CenterMapCell": {"site_ref": f("str"), "domain": f("enum:domain"), "severity": f("enum:severity"), "pattern_refs": f("str", "many"), "individual_risk_refs": f("str", "many"), "measure_refs": f("str", "many")},
    "R5CenterMapProjection": {"projection_instance": f("R5ProjectionInstance"), "stable_site_order": f("str", "many"), "cells": f("R5CenterMapCell", "many"), "content_hash": f("sha256")},
    "R5RiskInspectorProjection": {"risk_ref": f("str"), "severity": f("enum:severity"), "domain": f("enum:domain"), "baseline_item_refs": f("str", "many"), "baseline_assessment_refs": f("str", "many"), "analysis_attempt_refs": f("str", "many"), "worker_output_refs": f("str", "many"), "verification_refs": f("str", "many"), "conflict_refs": f("str", "many"), "adjudication_ref": f("str", n=True), "support_evidence_refs": f("str", "many"), "counterevidence_refs": f("str", "many"), "source_locator_refs": f("str", "many"), "query_draft_ref": f("str", n=True), "authority_receipt_ref": f("str")},
    "R5DeepLinkState": {"project_ref": f("str"), "run_ref": f("str"), "snapshot_ref": f("str"), "cutoff_ref": f("str"), "site_ref": f("str", n=True), "subject_ref": f("str"), "risk_ref": f("str"), "view": f("enum:workspace_view"), "spine_ref": f("str"), "axis_mode": f("enum:axis_mode"), "window_start": f("date", n=True), "window_end": f("date", n=True), "visit_ref": f("str", n=True), "event_ref": f("str", n=True), "risk_anchor_ref": f("str"), "source_locator_ref": f("str", n=True), "return_context_key": f("str")},
    "R5ReturnContext": {"canonical_state_hash": f("sha256"), "deep_link_state": f("R5DeepLinkState"), "filter_state": f("R5FilterState"), "sort_state": f("R5SortState"), "page_state": f("R5PageState"), "scroll_state": f("R5ScrollState"), "inspector_width": f("int"), "temporary_expansion_refs": f("str", "many")},
    "R5SubjectWorkspaceState": {"subject_ref": f("str"), "spine_ref": f("str"), "axis_mode": f("enum:axis_mode"), "window_start": f("date", n=True), "window_end": f("date", n=True), "selected_visit_ref": f("str", n=True), "selected_event_ref": f("str", n=True), "selected_risk_ref": f("str", n=True), "active_view": f("enum:workspace_view"), "content_hash": f("sha256")},
    "R5TemporalSpineProjection": {"spine_ref": f("str"), "subject_ref": f("str"), "visit_refs": f("str", "many"), "event_refs": f("str", "many"), "pending_date_refs": f("str", "many"), "phase_band_refs": f("str", "many"), "cutoff_ref": f("str"), "content_hash": f("sha256")},
    "R5VisitNode": {"visit_ref": f("str"), "visit_kind": f("enum:visit_kind"), "nominal_date": f("date", n=True), "actual_date": f("date", n=True), "date_state": f("enum:date_state"), "phase_ref": f("str", n=True), "source_locator_refs": f("str", "many")},
    "R5JourneyTrack": {"domain": f("enum:domain"), "applicability_state": f("enum:applicability_state"), "event_refs": f("str", "many"), "risk_anchor_refs": f("str", "many"), "content_hash": f("sha256")},
    "R5JourneyEvent": {"event_ref": f("str"), "domain": f("enum:domain"), "subtype": f("enum:journey_subtype"), "date_state": f("enum:date_state"), "start": f("date", n=True), "end": f("date", n=True), "source_locator_refs": f("str", "many"), "risk_anchor_refs": f("str", "many")},
    "R5RiskAnchor": {"risk_ref": f("str"), "domain": f("enum:domain"), "severity": f("enum:severity"), "risk_type_zh": f("str"), "event_ref": f("str", n=True), "visit_ref": f("str", n=True), "date_state": f("enum:date_state")},
    "R5PendingDateItem": {"item_ref": f("str"), "item_kind": f("enum:pending_item_kind"), "domain": f("enum:domain"), "date_state": f("enum:date_state"), "candidate_date_refs": f("str", "many"), "source_locator_refs": f("str", "many")},
    "R5AEMHMatchHistory": {"candidate_ref": f("str"), "later_fact_ref": f("str", n=True), "match_state": f("enum:match_state"), "identity_evidence_refs": f("str", "many"), "from_snapshot_ref": f("str"), "to_snapshot_ref": f("str"), "history_content_hash": f("sha256")},
    "R5AudienceEncodingRegistry": {"domain_items": f("R5DomainEncodingItem", "many"), "risk_overlay_shape": f("str"), "severity_items": f("R5SeverityLexiconItem", "many"), "symptom_efficacy_subtypes": f("enum:symptom_efficacy_subtype", "many"), "legacy_treatment_mapping": f("R5LegacyTreatmentMappingItem", "many")},
    "R5AudienceLexicon": {"items": f("R5LexiconItem", "many"), "forbidden_terms": f("str", "many"), "content_hash": f("sha256")},
}

def build_field_mappings() -> list[dict[str, str]]:
    d10_version = "mm_r4.d10_projection:D10ProjectionVersion"
    d10_project = "mm_r4.d10_projection:D10ProjectProjection"
    d10_counts = "mm_r4.d10_projection:D10ProjectionCountSurface"
    d10_change = "mm_r4.d10_projection:D10ChangeSection"
    d10_center = "mm_r4.d10_projection:D10CenterPatternRow"
    d10_risk = "mm_r4.d10_projection:D10RiskMarker"
    d10_link = "mm_r4.d10_projection:D10DeepLinkTarget"
    d10_input = "mm_r4.d10_contracts:D10TypedInput"
    ensemble = "mm_r4.ensemble_contracts"
    direct = {
        "R5AuthorityReceipt.public_projection_id": [f"{d10_project}.projection_id"],
        "R5AuthorityReceipt.public_projection_content_hash": [f"{d10_project}.projection_content_hash"],
        "R5AuthorityReceipt.evaluation_content_identities": [f"{d10_version}.source_evaluation_content_identities"],
        "R5AuthorityReceipt.visibility_decision_id": [f"{d10_input}.visibility_decision.decision_id"],
        "R5AuthorityReceipt.project_ref": [f"{d10_version}.project_ref"],
        "R5AuthorityReceipt.run_ref": [f"{d10_version}.run_ref"],
        "R5AuthorityReceipt.snapshot_ref": [f"{d10_version}.snapshot_ref"],
        "R5AuthorityReceipt.cutoff_ref": [f"{d10_version}.cutoff_ref"],
        "R5AuthorityReceipt.source_revision_content_pairs": [f"{d10_input}.source_revision_content_pairs"],
        "R5AuthorityReceipt.audience_contract_id": [f"{d10_version}.audience_contract_ref"],
        "R5ChangeBand.change_kind": [f"{d10_change}.change_kind"],
        "R5ChangeBand.change_cause": [f"{d10_change}.change_cause"],
        "R5QuantitativeMeasure.numerator_value": [f"{d10_counts}.visible_individual_risk_count"],
        "R5QuantitativeMeasure.denominator_value": [f"{d10_center}.denominator_value"],
        "R5CenterMapCell.site_ref": [f"{d10_center}.site_ref"],
        "R5DeepLinkState.project_ref": [f"{d10_link}.project_ref"],
        "R5DeepLinkState.run_ref": [f"{d10_link}.run_ref"],
        "R5DeepLinkState.snapshot_ref": [f"{d10_link}.snapshot_ref"],
        "R5DeepLinkState.cutoff_ref": [f"{d10_version}.cutoff_ref"],
        "R5DeepLinkState.site_ref": [f"{d10_link}.site_ref"],
        "R5DeepLinkState.subject_ref": [f"{d10_link}.subject_ref"],
        "R5DeepLinkState.source_locator_ref": [f"{d10_link}.source_locator"],
        "R5DeepLinkState.return_context_key": [f"{d10_link}.return_state_key"],
        "R5RiskInspectorProjection.analysis_attempt_refs": [f"{ensemble}:AnalysisAttempt.attempt_id"],
        "R5RiskInspectorProjection.baseline_item_refs": [f"{ensemble}:ReferenceBaselineItem.item_id"],
        "R5RiskInspectorProjection.baseline_assessment_refs": [f"{ensemble}:BaselineAssessment.item_id"],
        "R5RiskInspectorProjection.verification_refs": [f"{ensemble}:EvidenceVerification.verification_id"],
        "R5RiskInspectorProjection.conflict_refs": [f"{ensemble}:ConflictVisibility.conflict_id"],
        "R5RiskInspectorProjection.adjudication_ref": [f"{ensemble}:AdjudicationBinding.binding_id"],
        "R5RiskInspectorProjection.risk_ref": [f"{d10_risk}.marker_id"],
    }
    ui_objects = {"R5FilterState", "R5SortState", "R5PageState", "R5ScrollState", "R5ReturnContext", "R5SubjectWorkspaceState"}
    contract_objects = {"R5DomainEncodingItem", "R5SeverityLexiconItem", "R5LegacyTreatmentMappingItem", "R5LexiconItem", "R5AudienceEncodingRegistry", "R5AudienceLexicon"}
    deferred_temporal = {"R5TemporalSpineProjection", "R5VisitNode", "R5JourneyTrack", "R5JourneyEvent", "R5RiskAnchor", "R5PendingDateItem"}
    derived_sources = {
        "R5AuthorityReceipt": [f"{d10_version}.projection_version_id", f"{d10_version}.source_evaluation_content_identities", f"{d10_input}.visibility_decision", f"{d10_input}.source_revision_content_pairs"],
        "R5ProjectionInstance": [f"{d10_version}.projection_version_id", f"{d10_version}.projection_content_hash"],
        "R5ChangeBand": [f"{d10_change}.change_kind", f"{d10_change}.change_cause", f"{d10_version}.snapshot_ref"],
        "R5CurrentRiskSet": [f"{d10_risk}.marker_id", f"{d10_risk}.risk_kind", f"{d10_risk}.member_refs", f"{d10_project}.risk_marker_ref"],
        "R5QuantitativeMeasure": [f"{d10_counts}.visible_individual_risk_count", f"{d10_counts}.rate_projection_state", f"{d10_counts}.coverage_state_zh", f"{d10_input}.denominator"],
        "R5ProjectCockpitProjection": [f"{d10_project}.projection_id", f"{d10_project}.change_section", f"{d10_project}.center_distribution", f"{d10_project}.count_surface_ref"],
        "R5CenterMapCell": [f"{d10_center}.site_ref", f"{d10_center}.member_count", f"{d10_center}.affected_subject_count", f"{d10_center}.denominator_value"],
        "R5CenterMapProjection": [f"{d10_project}.center_distribution", f"{d10_project}.projection_content_hash"],
        "R5RiskInspectorProjection": [f"{d10_risk}.marker_id", f"{ensemble}:ReferenceBaselineItem.item_id", f"{ensemble}:BaselineAssessment.item_id", f"{ensemble}:AnalysisAttempt.attempt_id", f"{ensemble}:EvidenceVerification.verification_id", f"{ensemble}:ConflictVisibility.conflict_id"],
        "R5DeepLinkState": [f"{d10_link}.link_id", f"{d10_link}.visibility_decision_ref", f"{d10_link}.source_locator"],
        "SourceRevisionContentPair": [f"{d10_input}.source_revision_content_pairs"],
    }
    deferred_targets = {
        # D10's center row is a count/coverage surface.  It does not carry the
        # domain, severity or member identities required by these R5 leaves.
        **{f"R5CenterMapCell.{name}": "r5-center-map-cell-semantic-adapter-v1" for name in (
            "domain", "severity", "pattern_refs", "individual_risk_refs", "measure_refs"
        )},
        # R4 currently has no single public current/resolved risk-set contract.
        **{f"R5CurrentRiskSet.{name}": "r5-current-risk-set-public-v1" for name in OBJECTS["R5CurrentRiskSet"]},
        # The count surface alone cannot supply traceable numerator/denominator
        # members, cutoff or evaluation limits.  S1 must bind the full typed
        # authority before any quantitative measure can be emitted.
        **{f"R5QuantitativeMeasure.{name}": "r5-quantitative-measure-authority-v1" for name in OBJECTS["R5QuantitativeMeasure"]},
        # These Inspector leaves have no complete public R4/ensemble projection
        # yet.  Existing identifier-only leaves remain direct mappings below.
        **{f"R5RiskInspectorProjection.{name}": "r5-risk-inspector-evidence-adapter-v1" for name in (
            "severity", "domain", "worker_output_refs", "support_evidence_refs",
            "counterevidence_refs", "source_locator_refs", "query_draft_ref",
            "authority_receipt_ref",
        )},
        # Projection kind is selected by the concrete adapter variant; it is
        # not globally d10_project for D09/ensemble/temporal/history receipts.
        "R5AuthorityReceipt.public_projection_kind": "r5-authority-receipt-kind-v1",
    }
    canonical_hash_targets = {
        "R5SubjectWorkspaceState.content_hash": "canonical_sha256.R5SubjectWorkspaceState.non_hash_fields",
        "R5ReturnContext.canonical_state_hash": "canonical_sha256.R5ReturnContext.non_hash_fields",
    }
    mappings = []
    for object_name, fields in sorted(OBJECTS.items()):
        for field_name in sorted(fields):
            target = f"{object_name}.{field_name}"
            if target in canonical_hash_targets:
                kind, paths, recipe, deferred = "canonical_derived", [], canonical_hash_targets[target], None
            elif target in deferred_targets:
                kind, paths, recipe, deferred = "deferred", [], "identity_preserving_adapter", deferred_targets[target]
            elif target in direct:
                kind, paths, recipe, deferred = "r4_direct", direct[target], "copy_or_closed_map", None
            elif target in {"R5DeepLinkState.axis_mode", "R5DeepLinkState.view", "R5DeepLinkState.window_start", "R5DeepLinkState.window_end"}:
                kind, paths, recipe, deferred = "ui_state", [], f"view_state.{object_name}.{field_name}", None
            elif target in {"R5DeepLinkState.spine_ref", "R5DeepLinkState.visit_ref", "R5DeepLinkState.event_ref", "R5DeepLinkState.risk_anchor_ref"}:
                kind, paths, recipe, deferred = "deferred", [], "subject_temporal_identity_lookup", "subject-temporal-public-v1"
            elif target == "R5DeepLinkState.risk_ref":
                kind, paths, recipe, deferred = "derived", [f"{d10_risk}.marker_id", f"{d10_link}.member_object_ref"], "verified_risk_member_join", None
            elif object_name in ui_objects:
                kind, paths, recipe, deferred = "ui_state", [], f"view_state.{object_name}.{field_name}", None
            elif object_name in contract_objects:
                kind, paths, recipe, deferred = "contract_constant", [], f"exact_contract.{object_name}.{field_name}", None
            elif object_name in deferred_temporal:
                kind, paths, recipe, deferred = "deferred", [], "identity_preserving_adapter", "subject-temporal-public-v1"
            elif object_name == "R5AEMHMatchHistory":
                kind, paths, recipe, deferred = "deferred", [], "append_only_history_adapter", "aemh-match-history-public-v1"
            else:
                kind, paths, recipe, deferred = "derived", derived_sources[object_name], f"derive.{object_name}.{field_name}", None
            validation = direct.get(target, derived_sources.get(object_name, [])) if object_name == "R5DeepLinkState" and field_name in {"risk_ref", "spine_ref", "cutoff_ref"} else []
            mappings.append({"target": target, "source_kind": kind, "source_paths": paths, "recipe_id": recipe, "validation_paths": validation, "deferred_contract": deferred})
    return mappings

PERFORMANCE_PROFILE = {
    "browser": "Chromium bundled with pinned Playwright in frontend lockfile", "build_mode": "frontend production build; local 8911 only in S7",
    "viewport": [1440, 900], "dataset": {"events": 1000, "metrics": 40, "risk_anchors": 300},
    "machine_record": ["hardware_model", "os_version", "cpu_logical_count", "memory_gib", "playwright_version", "chromium_version", "commit_sha"],
    "cache_modes": ["cold_new_context_no_http_cache", "warm_same_context_second_navigation"], "samples_per_mode": 7,
    "summary_statistic": "p95_nearest_rank",
    "marks": {"interactive_start": "navigationStart", "interactive_end": "risk-list, center-map, inspector and journey controls enabled", "response_start": "trusted pointer or keyboard event", "response_end": "next painted frame with updated canonical selection"},
    "thresholds": {"cold_interactive_ms_p95": 2500, "warm_interactive_ms_p95": 1500, "brush_zoom_select_ms_p95": 100, "pan_fps_p05": 30},
}

INVARIANTS = [
    {"invariant_id": "receipt_identity_exact", "objects": ["R5AuthorityReceipt", "R5ProjectionInstance"], "predicate": "project/run/snapshot/cutoff/public projection identities equal the bound R4 projection version and receipt", "error_code": "authority_identity_mismatch"},
    {"invariant_id": "deep_link_identity_exact", "objects": ["R5DeepLinkState", "R5AuthorityReceipt"], "predicate": "project/run/snapshot/cutoff/site/subject are verified against the target projection; risk and spine belong to that subject", "error_code": "deep_link_identity_mismatch"},
    {"invariant_id": "canonical_content_hash", "objects": ["R5ProjectionInstance", "R5ProjectCockpitProjection", "R5CenterMapProjection", "R5SubjectWorkspaceState", "R5ReturnContext"], "predicate": "content_hash or canonical_state_hash equals sha256 canonical JSON of all non-hash fields with sorted unordered refs", "error_code": "content_hash_mismatch"},
    {"invariant_id": "unique_reference_sets", "objects": ["R5CurrentRiskSet", "R5QuantitativeMeasure", "R5RiskInspectorProjection"], "predicate": "every many-ref field is duplicate-free and mutually exclusive where planes differ", "error_code": "duplicate_or_cross_plane_ref"},
    {"invariant_id": "denominator_rate_consistency", "objects": ["R5QuantitativeMeasure"], "predicate": "closed_positive requires value>0; closed_zero requires value=0 and rate_state=not_evaluable; unknown/unclosed require null value and rate_state=not_evaluable", "error_code": "denominator_rate_inconsistent"},
    {"invariant_id": "date_geometry_consistency", "objects": ["R5VisitNode", "R5JourneyEvent", "R5PendingDateItem"], "predicate": "exact requires precise date; partial/conflicted preserve ranges; missing has no fabricated main-axis date", "error_code": "date_geometry_inconsistent"},
    {"invariant_id": "domain_subtype_matrix", "objects": ["R5JourneyEvent"], "predicate": "subtype belongs to its frozen domain; symptom/efficacy/scale/outcome/trend belong only to symptom_efficacy", "error_code": "domain_subtype_mismatch"},
    {"invariant_id": "aemh_append_only_transition", "objects": ["R5AEMHMatchHistory"], "predicate": "snapshot transitions append; exact/ambiguous/rejected never delete prior candidate or auto-close risk", "error_code": "aemh_history_rewrite"},
    {"invariant_id": "severity_lexicon_bijection", "objects": ["R5SeverityLexiconItem"], "predicate": "critical=紧急, high=高, medium=中, low=低 exactly once", "error_code": "severity_lexicon_mismatch"},
    {"invariant_id": "severity_authority_no_promotion", "objects": ["R5RiskAnchor", "R5RiskInspectorProjection"], "predicate": "critical may appear only when upstream R4 authority is critical; high never promotes to critical", "error_code": "severity_unauthorized_promotion"},
    {"invariant_id": "legacy_severity_mapping", "objects": ["R5SeverityLexiconItem"], "predicate": "legacy severe->high, moderate->medium, mild->low; unmapped legacy value fails closed", "error_code": "legacy_severity_mapping_mismatch"},
    {"invariant_id": "risk_overlay_unique", "objects": ["R5AudienceEncodingRegistry"], "predicate": "risk_overlay_shape=double_chevron_badge and no event_shape uses it", "error_code": "risk_event_shape_collision"},
    {"invariant_id": "domain_encoding_complete_unique", "objects": ["R5AudienceEncodingRegistry", "R5DomainEncodingItem"], "predicate": "domain_items contains each of the eight closed domains exactly once; symptom_efficacy event_shape=circle and line_style=trend", "error_code": "domain_encoding_incomplete_or_ambiguous"},
    {"invariant_id": "legacy_treatment_fail_closed", "objects": ["R5LegacyTreatmentMappingItem"], "predicate": "mapped requires authority ref,target domain,target subtype; unmapped_fail_closed requires all targets null and enters domain-confirmation surface", "error_code": "legacy_treatment_mapping_invalid"},
]

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def canonical(v: object) -> bytes: return (json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()

def severity_for(category: str, slot: str) -> str:
    if (category, slot) in {
        ("authority_identity", "project_ref"),
        ("authority_visibility", "hidden_member"), ("authority_visibility", "hidden_site"),
        ("deep_link_identity", "project"), ("deep_link_identity", "site"), ("deep_link_identity", "subject"),
        ("source_one_hop", "listing_row"), ("source_one_hop", "listing_cell"), ("source_one_hop", "nearest_fallback"),
    }:
        return "P0"
    return CATEGORY_SEVERITY[category]

def build_rules() -> list[dict[str, str]]:
    rules = []
    for category, slots in CATEGORY_SLOTS.items():
        for slot in slots:
            rule_id = f"{category}.{slot}"
            accepted = (category, slot) in ACCEPT_SLOTS
            valid_value = f"valid::{category}::{slot}"
            mutated_value = f"mutated::{category}::{slot}"
            rules.append({"rule_id": rule_id, "category": category, "slot": slot, "valid_value": valid_value, "mutated_value": mutated_value, "expected_outcome": ("accept:" if accepted else "reject:") + rule_id, "expected_projection": "emitted" if accepted else "not_emitted"})
    return rules

def stage_for(category: str) -> str:
    if category.startswith("authority_"):
        return "S1"
    if category in {"change_comparability", "change_cause_plane", "deep_link_identity", "return_context"}:
        return "S2"
    if category.startswith("count_") or category.startswith("numerator_") or category.startswith("coverage_") or category.startswith("center_"):
        return "S3"
    if category in {"inspector_evidence_order", "ensemble_visibility", "source_one_hop"}:
        return "S4"
    if category in {"visit_semantics", "axis_conversion", "uncertain_dates", "eight_domain_adaptation", "encoding_registry", "aemh_projection", "aemh_match_history"}:
        return "S5"
    if category in {"interaction_no_mutation", "deterministic_replay"}:
        return "S6"
    return "S7"

def build_registry(rules: list[dict[str, str]]) -> list[dict[str, object]]:
    rows, ordinal = [], 0
    for rule in rules:
            category, slot = rule["category"], rule["slot"]
            ordinal += 1
            expected, projection = rule["expected_outcome"], rule["expected_projection"]
            mutation = {"op": "replace", "path": f"/input/{category}/{slot}", "value": rule["mutated_value"]}
            rows.append({
                "case_id": f"R5C-{ordinal:03d}", "category": category,
                "precondition": f"valid embedded input with leaf /input/{category}/{slot}", "single_mutation": mutation,
                "expected_typed_outcome_or_error": expected,
                "forbidden_audience_output": "no stale, cross-identity, fabricated, hidden or task-state audience output",
                "stage_oracle_contract": {"kind": "planned_pytest", "planned_stage": stage_for(category), "rule_id": rule["rule_id"], "test_locator": f"poc/medical_monitoring_ai_native_r5/tests/challenges/test_{category}.py::test_{slot}", "expected_outcome": expected, "expected_projection": projection, "required_non_llm_anchor": "typed validator result plus canonical projection hash or measured browser trace"},
                "severity": severity_for(category, slot),
            })
    return rows

def main() -> None:
    rules = build_rules()
    contract_sha = sha(CONTRACT.read_bytes())
    registry = build_registry(rules)
    if len(registry) != 204:
        raise RuntimeError(f"expected 204 cases, got {len(registry)}")
    ledger = [{"quota_instance_id": f"R5Q-{r['category']}-{i+1:03d}", "category": r["category"], "case_id": r["case_id"]} for i, r in enumerate(registry)]
    exact = {"schema": "medical-monitoring-r5-exact-contract-v0.3.1", "contract_sha256": contract_sha, "enums": ENUMS, "objects": OBJECTS, "field_mappings": build_field_mappings(), "invariants": INVARIANTS, "challenge_rules": rules, "risk_overlay_shape": "double_chevron_badge", "event_forbidden_shapes": ["double_chevron_badge"], "unknown_domain_policy": "fail_closed_to_domain_confirmation_surface", "legacy_domain_policy": {"background_treatment": "frozen_mapping_or_fail_closed", "non_drug_treatment": "frozen_mapping_or_fail_closed", "OTHER": "forbidden"}, "performance_profile": PERFORMANCE_PROFILE}
    payloads = {
        "exact_contract.json": exact,
        "challenge_registry.json": {"schema": "medical-monitoring-r5-challenge-registry-v0.3.1", "contract_sha256": contract_sha, "row_count": len(registry), "rows": registry},
        "quota_ledger.json": {"schema": "medical-monitoring-r5-quota-ledger-v0.3.1", "contract_sha256": contract_sha, "category_quotas": {k: len(v) for k, v in CATEGORY_SLOTS.items()}, "expected_total": 204, "instance_count": len(ledger), "instances": ledger},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (OUT / name).write_bytes(canonical(payload))
    names = sorted(payloads)
    manifest = {"schema": "medical-monitoring-r5-contract-artifact-manifest-v0.3.1", "contract_sha256": contract_sha, "artifact_names": names, "artifacts": {n: sha((OUT / n).read_bytes()) for n in names}, "generator_sha256": sha(Path(__file__).read_bytes())}
    (OUT / "manifest.json").write_bytes(canonical(manifest))

if __name__ == "__main__":
    main()
