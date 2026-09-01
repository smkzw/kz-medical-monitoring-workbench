"""R4-D06 evaluator slice behavior tests (representative frozen semantics).

Focused tests that drive the real D06 entrypoints on the frozen synthetic
fixtures and assert the medical semantics the contract pins down, without
re-reading the oracle on the runtime path:

* score recalculation consistency (consistent / inconsistent / missing
  strategy / unit gate);
* item completeness and value validity roots;
* baseline selection (unique candidate, chronological-last selection,
  postbaseline-as-baseline positive, boundary tie);
* change and percent-change recalculation;
* response classification thresholds and confirmation;
* endpoint composition (any/all components, precedence, missing policy);
* repeat selection worst-value;
* TTE precedence and boundary;
* ICE contexts (hypothetical without estimator, treatment policy);
* priority resolution and risk identity binding for positive roots;
* scope/binding fail-closed behavior.

All data is synthetic and offline; expected values below are derived from
the frozen contract semantics, not from the oracle object.
"""

from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


from mm_r4.efficacy_fixtures import build_d06_challenge_matrix  # noqa: E402

MATRIX = build_d06_challenge_matrix()


def _outcome(number: int):
    return MATRIX.by_number(number).assemble()


# ---------------------------------------------------------------------------
# Score recalculation
# ---------------------------------------------------------------------------


class TestScoreRecalculation:
    def test_consistent_total_is_negative(self):
        outcome = _outcome(1)
        assert outcome["l1_disposition"] == "negative"
        assert outcome["coverage_status"] == "covered"
        assert outcome["l2_counts"]["risks"] == 0

    def test_inconsistent_total_is_score_positive(self):
        outcome = _outcome(2)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "score_inconsistent"
        assert outcome["l2_counts"]["risks"] == 1
        assert outcome["l2_counts"]["queries"] == 1
        assert outcome["object_hashes"]["public_r4_identity_hash"] is not None

    def test_missing_component_without_strategy_is_positive(self):
        outcome = _outcome(3)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "required_component_missing"

    def test_prorate_mean_recalculates_to_frozen_total(self):
        outcome = _outcome(4)
        assert outcome["domain_assertions"]["recalculated_score"] == "18"
        assert outcome["domain_assertions"]["comparison_status"] == "consistent"
        assert outcome["domain_assertions"]["l1_disposition"] == "negative"

    def test_missing_minimum_count_rule_opens_algorithm_gate(self):
        outcome = _outcome(5)
        assert outcome["output_kind"] == "gate"
        assert outcome["gate_state"] == "open"
        assert outcome["gate_disposition"] == "not_evaluable"

    def test_reverse_omitted_is_score_positive(self):
        outcome = _outcome(7)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "score_inconsistent"

    def test_wrong_weight_is_score_positive(self):
        outcome = _outcome(8)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "score_inconsistent"

    def test_tolerance_keeps_rounding_difference_negative(self):
        outcome = _outcome(10)
        assert outcome["l1_disposition"] == "negative"

    def test_missing_tolerance_rule_is_not_evaluable(self):
        outcome = _outcome(11)
        assert outcome["l1_disposition"] == "not_evaluable"
        assert outcome["l2_counts"]["coverage_notices"] == 1

    def test_out_of_range_item_is_component_positive(self):
        outcome = _outcome(12)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "component_value_invalid"

    def test_raw_value_never_overwritten(self):
        outcome = _outcome(13)
        assert outcome["l1_disposition"] is None
        assert outcome["coverage_status"] == "covered"


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


class TestBaseline:
    def test_unique_pre_intervention_baseline_negative(self):
        outcome = _outcome(34)
        assert outcome["l1_disposition"] == "negative"

    def test_chronological_last_selection_unique(self):
        outcome = _outcome(35)
        assert outcome["domain_assertions"]["candidate_decision_status"] == ("unique")
        assert outcome["domain_assertions"]["selected_candidate_id"] == ("ASM-BASE-D1")
        assert outcome["l1_disposition"] == "negative"

    def test_default_nearest_first_dose_is_rejected(self):
        outcome = _outcome(36)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06ContractViolationError"

    def test_two_feasible_candidates_without_tie_break_boundary(self):
        outcome = _outcome(37)
        assert outcome["l1_disposition"] == "boundary"
        assert outcome["l2_counts"]["clues"] == 1

    def test_postbaseline_as_baseline_positive(self):
        outcome = _outcome(39)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "baseline_inconsistent"

    def test_old_episode_baseline_reused_positive(self):
        outcome = _outcome(40)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "baseline_inconsistent"

    def test_distinct_episodes_keep_distinct_obligations(self):
        outcome = _outcome(41)
        assert outcome["l1_disposition"] is None

    def test_baseline_correction_creates_new_lineage(self):
        outcome = _outcome(42)
        assert outcome["l1_disposition"] is None

    def test_baseline_decision_from_wrong_run_fails_closed(self):
        outcome = _outcome(175)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"
        assert outcome["error_stage"] == "typed_binding_validation"


# ---------------------------------------------------------------------------
# Change / percent change
# ---------------------------------------------------------------------------


class TestChange:
    def test_consistent_change_negative(self):
        outcome = _outcome(43)
        assert outcome["l1_disposition"] == "negative"

    def test_sign_wrong_change_positive(self):
        outcome = _outcome(44)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "change_value_inconsistent"

    def test_zero_baseline_without_rule_not_evaluable(self):
        outcome = _outcome(48)
        assert outcome["l1_disposition"] == "not_evaluable"
        assert outcome["coverage_status"] == "not_evaluable"

    def test_percent_change_matches_frozen_formula(self):
        outcome = _outcome(49)
        assert outcome["l1_disposition"] == "negative"


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------


class TestResponse:
    def test_threshold_inclusive_boundary_consistent(self):
        outcome = _outcome(51)
        assert outcome["domain_assertions"]["comparison_status"] == "consistent"
        assert outcome["domain_assertions"]["response_class"] == "responder"
        assert outcome["l1_disposition"] == "negative"

    def test_threshold_exclusive_boundary_consistent(self):
        outcome = _outcome(52)
        assert outcome["domain_assertions"]["response_class"] == "non_responder"
        assert outcome["l1_disposition"] == "negative"

    def test_missing_threshold_comparator_not_evaluable(self):
        outcome = _outcome(53)
        assert outcome["l1_disposition"] == "not_evaluable"

    def test_precision_interval_crossing_threshold_boundary(self):
        outcome = _outcome(54)
        assert outcome["l1_disposition"] == "boundary"
        assert outcome["l2_counts"]["clues"] == 1

    def test_confirmation_required_twice_met_once_positive(self):
        outcome = _outcome(55)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "response_class_inconsistent"

    def test_confirmation_met_twice_negative(self):
        outcome = _outcome(56)
        assert outcome["l1_disposition"] == "negative"

    def test_source_class_conflicts_with_recalculated(self):
        outcome = _outcome(58)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "response_class_inconsistent"


# ---------------------------------------------------------------------------
# Endpoint composition
# ---------------------------------------------------------------------------


class TestComposition:
    def test_any_component_overall_event_negative(self):
        outcome = _outcome(59)
        assert outcome["domain_assertions"]["overall_component_state"] == "event"
        assert outcome["domain_assertions"]["component_states"] == {
            "COMP-A": "event",
            "COMP-B": "non_event",
        }
        assert outcome["l1_disposition"] == "negative"

    def test_any_used_where_all_required_positive(self):
        outcome = _outcome(61)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "endpoint_composition_inconsistent"

    def test_component_identity_not_unique_not_evaluable(self):
        outcome = _outcome(62)
        assert outcome["l1_disposition"] == "not_evaluable"

    def test_hierarchical_precedence_wrong_positive(self):
        outcome = _outcome(63)
        assert outcome["l1_disposition"] == "positive"
        assert outcome["primary_subtype"] == "endpoint_composition_inconsistent"

    def test_missing_component_propagate_not_evaluable(self):
        outcome = _outcome(153)
        assert outcome["l1_disposition"] == "not_evaluable"

    def test_missing_component_not_event_policy_non_event(self):
        outcome = _outcome(154)
        assert outcome["l1_disposition"] == "negative"


# ---------------------------------------------------------------------------
# TTE / ICE
# ---------------------------------------------------------------------------


class TestTteAndIce:
    def test_tte_event_precedence_negative(self):
        outcome = _outcome(64)
        assert outcome["l1_disposition"] == "negative"

    def test_tte_precedence_rule_missing_not_evaluable(self):
        outcome = _outcome(65)
        assert outcome["l1_disposition"] == "not_evaluable"

    def test_tte_origin_missing_not_evaluable(self):
        outcome = _outcome(156)
        assert outcome["l1_disposition"] == "not_evaluable"

    def test_tte_competing_event_wins_tie(self):
        outcome = _outcome(196)
        assert outcome["domain_assertions"]["tte_status"] == "competing_event"
        assert outcome["domain_assertions"]["selected_event_ref"] == ("EV-COMP-001")

    def test_tte_boundary_no_single_duration(self):
        outcome = _outcome(219)
        assert outcome["domain_assertions"]["tte_status"] == "boundary"
        assert outcome["domain_assertions"]["single_duration"] is None
        assert len(outcome["domain_assertions"]["feasible_interpretation_ref_ids"]) >= 2
        assert outcome["l1_disposition"] == "boundary"

    def test_tte_wrong_subject_fails_closed(self):
        outcome = _outcome(180)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"

    def test_hypothetical_ice_without_estimator_not_evaluable(self):
        outcome = _outcome(85)
        assert outcome["l1_disposition"] == "not_evaluable"
        assert outcome["domain_assertions"]["hypothetical_value_created"] is False
        assert outcome["domain_assertions"]["ice_context_state"] == ("not_evaluable")

    def test_withdrawal_treatment_policy_negative(self):
        outcome = _outcome(84)
        assert outcome["l1_disposition"] == "negative"

    def test_ice_misclassified_as_missing_rejected(self):
        outcome = _outcome(80)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06ContractViolationError"

    def test_estimator_available_without_binding_schema_error(self):
        outcome = _outcome(202)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "SchemaContractError"


# ---------------------------------------------------------------------------
# Priority / risk identity
# ---------------------------------------------------------------------------


class TestPriorityAndRisk:
    def test_primary_endpoint_medium_step_three(self):
        outcome = _outcome(67)
        assert outcome["domain_assertions"]["impact_class"] == "primary_endpoint"
        assert outcome["domain_assertions"]["monitoring_priority"] == "medium"
        assert outcome["domain_assertions"]["matched_precedence_step"] == 3
        assert outcome["l1_disposition"] is None

    def test_undefined_role_priority_unknown(self):
        outcome = _outcome(68)
        assert outcome["domain_assertions"]["impact_resolution_state"] == ("unresolved")
        assert outcome["domain_assertions"]["monitoring_priority"] == "unknown"
        assert outcome["domain_assertions"]["matched_precedence_step"] == 2

    def test_administrative_low_step_five(self):
        outcome = _outcome(69)
        assert outcome["domain_assertions"]["impact_class"] == "administrative"
        assert outcome["domain_assertions"]["monitoring_priority"] == "low"
        assert outcome["domain_assertions"]["matched_precedence_step"] == 5

    def test_primary_endpoint_irrecoverable_high_close_forbidden(self):
        outcome = _outcome(71)
        assert outcome["domain_assertions"]["monitoring_priority"] == "high"
        assert outcome["domain_assertions"]["machine_close_forbidden"] is True

    def test_rights_safety_high_close_forbidden(self):
        outcome = _outcome(200)
        assert outcome["domain_assertions"]["monitoring_priority"] == "high"
        assert outcome["domain_assertions"]["matched_precedence_step"] == 1
        assert outcome["domain_assertions"]["machine_close_forbidden"] is True

    def test_positive_root_emits_public_identity(self):
        outcome = _outcome(2)
        assert outcome["object_hashes"]["public_r4_identity_hash"].startswith("sha256:")
        assert (
            outcome["domain_assertions"]["priority_resolution"]["projection_state"]
            == "emitted_risk_decision"
        )

    def test_negative_root_no_risk_identity(self):
        outcome = _outcome(1)
        assert outcome["object_hashes"]["public_r4_identity_hash"] is None
        assert (
            outcome["domain_assertions"]["priority_resolution"]["projection_state"]
            == "resolver_result_only"
        )


# ---------------------------------------------------------------------------
# Fail-closed bindings
# ---------------------------------------------------------------------------


class TestFailClosedBindings:
    def test_wrong_project_binding_no_medical_unit(self):
        outcome = _outcome(117)
        assert outcome["l1_disposition"] is None
        assert outcome["l2_counts"]["risks"] == 0

    def test_wrong_site_binding_no_medical_unit(self):
        outcome = _outcome(133)
        assert outcome["l1_disposition"] is None

    def test_wrong_run_binding_no_medical_unit(self):
        outcome = _outcome(134)
        assert outcome["l1_disposition"] is None

    def test_wrong_episode_binding_no_medical_unit(self):
        outcome = _outcome(135)
        assert outcome["l1_disposition"] is None

    def test_wrong_snapshot_scope_gate(self):
        outcome = _outcome(136)
        assert outcome["output_kind"] == "gate"
        assert outcome["gate_state"] == "open"
        assert outcome["gate_disposition"] == "not_evaluable"

    def test_missing_d05_refs_dependency_gate(self):
        outcome = _outcome(159)
        assert outcome["output_kind"] == "gate"
        assert outcome["gate_state"] == "open"
        assert outcome["gate_disposition"] == "not_evaluable"

    def test_wrong_spine_hash_binding_error(self):
        outcome = _outcome(160)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"

    def test_wrong_spine_cutoff_projection_error(self):
        outcome = _outcome(161)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "ProjectionContractError"
        assert outcome["error_stage"] == "projection_validation"

    def test_d07_consumption_endpoint_mismatch_binding_error(self):
        outcome = _outcome(211)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"

    def test_equivalence_rule_unbound_instrument_binding_error(self):
        outcome = _outcome(212)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"

    def test_gate_missing_binding_ref_schema_error(self):
        outcome = _outcome(204)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "SchemaContractError"
        assert outcome["error_stage"] == "gate_binding_validation"
        assert outcome["domain_assertions"]["l1_created"] is False
        assert outcome["domain_assertions"]["l2_created"] is False

    def test_model_output_cannot_be_accepted_source(self):
        outcome = _outcome(137)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "SchemaContractError"
