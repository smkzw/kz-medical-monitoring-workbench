"""D03 investigational-product risk-domain compatibility facade."""

from .ip_types import *
from .ip_types import (
    _prec_rank,
    _nv_precision,
    _to_day,
    _day_range,
)
from .ip_resolution import *
from .ip_resolution import (
    _WindowOverlap,
    _compare_windows,
    _episode_window,
    _rule_window,
    _algorithm_window,
)
from .ip_results import *
from .ip_results import (
    _d03_risk_classifier,
    _d03_risk_scope,
    _build_d03_risk_identity,
    _d03_identity_detail,
    _build_d03_candidate,
    _expected_set_hash,
    _control_token_for,
    _make_evidence_item,
    _dedup_locator_ids,
    _make_source_record_ref,
    _canonical_text,
    _canonical_dose,
    _canonical_record_value,
    _journey_marker,
    _display_label,
    _query_text,
    _build_query_ref,
    _build_positive_result,
    _build_boundary_result,
    _not_evaluable_result,
    _negative_result,
)
from .ip_evaluation import *
from .ip_evaluation import (
    _required_roles_for,
    _audience_suffix_for,
    _binding_gate_result,
    _evaluate_role_phase_unit,
    _rule_phase_applicability,
    _evaluate_plan_actual_unit,
    _field_label,
    _occurrence_days_in_rule_window,
    _RatioOutcome,
    _round_ratio,
    _threshold_fraction,
    _check_ratio_against_thresholds,
    _window_day_count,
    _days_in_window,
    _planned_pause_day_count,
    _observation_for,
    _convert_unit,
    _evaluate_adherence_unit,
)
from .ip_actions import *
from .ip_actions import (
    _evaluate_allowed_action_unit,
    _evaluate_medical_action_unit,
    _amount_decimal,
    _record_totals,
    _evaluate_accountability_unit,
)
from .ip_orchestration import *

__all__ = ['REQUIRED_IP_ROLES', 'OPTIONAL_IP_ROLES', 'IP_ROLES', 'IPSliceError', 'PlannedTreatmentAssignment', 'IPExposureEpisode', 'ExposureOccurrence', 'ExposureAggregationPolicy', 'ProtocolExposureRule', 'AdherenceAlgorithm', 'AdherenceObservation', 'PlannedExposureAction', 'ActualIPAction', 'IPActionEvidence', 'AssignmentBindingMapping', 'D03PriorityPolicy', 'IPSemanticRecord', 'IPWindowDescriptor', 'AssignmentResolution', 'ExposureDayComputation', 'compute_actual_exposure_days', 'resolve_episode_assignment', 'IPUnitExpanded', 'IPExpectedSetExpansion', 'expand_ip_expected_set', 'IPUnitResult', 'IPSliceResult', 'IPEpisodeRollup', 'evaluate_ip_unit', 'evaluate_ip_slice', 'POSITIVE_SUBTYPE_LABELS', 'positive_subtype_audience_label', 'D03_DOMAIN', 'D03_UNIT_ALGO_VERSION', 'IP_RULE_TYPES', 'CONTROL_ITEMS', 'IP_ACTION_TYPES', 'METRIC_KINDS', 'CONFIRMATION_CONFIRMED', 'CONFIRMATION_UNRESOLVED']
