"""R4-D03 IP synthetic fixtures, challenge matrix and N-to-N+1 lifecycle
harness (worker_03).

Every fixture in this module is **deterministic, synthetic and offline**.
No real-project data, table names, drug names, fixed dosing thresholds or
30-day rules are encoded.  The fixtures build the same frozen public value
objects the D03 IP engine (``mm_r4.ip``) and the D03 projection
(``mm_r4.ip_projection``) use, so the tests exercise the real engine
evaluation, the real projection join invariants, the real R2 identity/
lifecycle public API and the real ``CoverageLedger`` rather than mocks.

The module delivers the three things required by the frozen D03 contract
``FROZEN_R4_D03_CONTRACT_V1_1`` §11 (synthetic challenge matrix) and
§4/§10 (identity persistence, supersede, identity ambiguity, sibling
rollup coexistence, deterministic replay):

1. Thin primitive builders (:func:`make_locator`, :func:`make_assignment`,
   :func:`make_episode`, :func:`make_occurrence`, :func:`make_agg_policy`,
   :func:`make_plan_actual_rule`, :func:`make_allowed_action_rule`,
   :func:`make_medical_action_rule`, :func:`make_adherence_algorithm`,
   :func:`make_observation`, :func:`make_evidence`,
   :func:`make_planned_action`, :func:`make_actual_action`,
   :func:`make_return_record`, :func:`make_dispense_record`,
   :func:`make_cm_conflict_record`, :func:`make_mapping`,
   :func:`make_policy`) that construct the frozen versioned inputs with
   stable hashes.
2. :func:`build_ip_challenge_matrix` -- executable reference cases for
   every frozen §11 challenge row (six positives + six negatives,
   boundary cases, fail-closed not_evaluable cases, exposure-day
   semantics, medical-trigger linkage, binding/disclosure, the §5.4
   return decision table, planned/actual actions, adherence arithmetic,
   determinism, lifecycle seeds and sibling coexistence), each carrying
   its expected per-unit L1 dispositions and candidate/Query counts.
3. An N-to-N+1 lifecycle harness (:func:`make_acceptance_service`,
   :func:`make_baseline_snapshot`, :func:`make_subsequent_snapshot`,
   :func:`make_closed_ip_ledger`, :func:`run_n_to_n1_replay`) that proves
   immutable historical completion, stable event identity, versioned
   lineage supersede (never ``resolved_by_data``), identity ambiguity
   guards, no duplicate D01/D02/D03 candidates/risks/Queries, and
   deterministic replay.

All data is synthetic.  No production UI, real project, provider,
dictionary, or product service is involved; port 8911 is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as _replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY,
    AcceptanceService,
    SnapshotAcceptanceState,
    SnapshotBinding,
)
from mm_r2.domain import (
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    SourceRevision,
)
from mm_r2.identity import IdentityResolution, make_record_identity
from mm_r2.risk import RiskLifecycle

from .ip import (
    ACTION_DOSE_REDUCE,
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_STOP,
    CONFIRMATION_CONFIRMED,
    CONFIRMATION_UNRESOLVED,
    CONTROL_ACCOUNTABILITY,
    CONTROL_ADHERENCE,
    CONTROL_PLAN_ACTUAL,
    CONTROL_ROLE_PHASE,
    D03_DOMAIN,
    D03_RULE_LINEAGE_DEFAULT,
    D03PriorityPolicy,
    ExposureAggregationPolicy,
    ExposureDayComputation,
    ExposureOccurrence,
    IPActionEvidence,
    IPExposureEpisode,
    IPExpectedSetExpansion,
    IPSemanticRecord,
    IPSliceResult,
    IPUnitExpanded,
    IPUnitResult,
    METRIC_ACCOUNTABILITY_PROXY,
    METRIC_AMOUNT_RATIO,
    METRIC_DAY_RATIO,
    METRIC_DOSE_COUNT_RATIO,
    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
    POSITIVE_SUBTYPE_LABELS,
    POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
    RETURN_EXPECTED,
    RETURN_NOT_REQUIRED,
    RETURN_UNKNOWN,
    RESOLUTION_BOUND,
    RULE_TYPE_ALLOWED_ACTION,
    RULE_TYPE_MEDICAL_ACTION,
    RULE_TYPE_PLAN_ACTUAL,
    AssignmentResolution,
    ActualIPAction,
    AdherenceAlgorithm,
    AdherenceObservation,
    AssignmentBindingMapping,
    PlannedExposureAction,
    PlannedTreatmentAssignment,
    ProtocolExposureRule,
    compute_actual_exposure_days,
    evaluate_ip_slice,
    evaluate_ip_unit,
    expand_ip_expected_set,
)
from .contracts import L1Disposition, SourceLocator, UnitEvaluation
from .coverage import CoverageLedger, ExpectedSet, expected_set_hash

__all__ = [
    # constants
    "PROJECT_ID",
    "DOMAIN_ID",
    "RUN_ID",
    "RULE_LINEAGE",
    "SNAPSHOT_ID",
    "SOURCE_REV_ID",
    "SITE_REF",
    "DEFAULT_ROLE_COVERAGE",
    # primitive builders
    "make_locator",
    "make_assignment",
    "make_episode",
    "make_occurrence",
    "make_agg_policy",
    "make_plan_actual_rule",
    "make_allowed_action_rule",
    "make_medical_action_rule",
    "make_adherence_algorithm",
    "make_observation",
    "make_evidence",
    "make_planned_action",
    "make_actual_action",
    "make_return_record",
    "make_dispense_record",
    "make_cm_conflict_record",
    "make_mapping",
    "make_policy",
    "evaluate",
    "evaluate_one",
    "evaluate_slice",
    # challenge matrix
    "IPExpectedUnit",
    "IPChallengeCase",
    "IPChallengeMatrix",
    "build_ip_challenge_matrix",
    # lifecycle harness
    "make_unit_evaluation",
    "make_closed_ip_ledger",
    "attach_risk_ref",
    "make_acceptance_service",
    "make_baseline_snapshot",
    "make_subsequent_snapshot",
    "make_lifecycle",
    "NToN1Replay",
    "run_n_to_n1_replay",
]


# ---------------------------------------------------------------------------
# Stable synthetic constants (no project specifics, no fixed table names)
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = D03_DOMAIN
RUN_ID = "run-synthetic-d03-001"
RULE_LINEAGE = D03_RULE_LINEAGE_DEFAULT
SNAPSHOT_ID = "snap-d03-accepted-001"
SOURCE_REV_ID = "sr-d03-listing-001"
SITE_REF = "SITE01"

#: Default role coverage: every semantic role covered.  Challenge cases
#: that probe coverage gaps override individual roles.
DEFAULT_ROLE_COVERAGE: Dict[str, bool] = {
    "ip_exposure": True,
    "subject_identity": True,
    "site_identity": True,
    "temporal_anchor": True,
    "randomization": True,
    "planned_treatment": True,
    "study_phase": True,
    "ip_dispense": True,
    "ip_return": True,
    "ip_accountability": True,
    "reported_ae": True,
    "lab_finding": True,
    "exam_finding": True,
    "efficacy_assessment": True,
    "ip_action_reason": True,
    "recorded_cm": True,
}


# ---------------------------------------------------------------------------
# Primitive builders (mirror the worker_01/worker_02 test conventions)
# ---------------------------------------------------------------------------

def make_locator(
    record_id: str, table_semantic: str = "ip_exposure",
    snapshot_id: str = SNAPSHOT_ID,
    source_revision_id: str = SOURCE_REV_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=source_revision_id,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_assignment(
    assignment_id: str = "ASSIGN-01", subject: str = "SYN-001",
    role_token: str = "active", phase: str = "treatment",
    dose: str = "50", dose_unit: str = "mg", dosage_form: str = "tablet",
    route: str = "口服", frequency: str = "每日一次",
    planned_start: str = "2026-01-01", planned_end: str = "2026-03-31",
    display_label: str = "研究药物 A（盲态标签）",
    disclosure: str = "open", randomization_token: str = "R1",
    planned_drug_identity: str = "synthetic_drug_x",
    content_hash: str = "asg-hash-01",
    assignment_lineage: str = "asg-lineage-01",
) -> PlannedTreatmentAssignment:
    return PlannedTreatmentAssignment(
        assignment_id=assignment_id, subject_ref=subject, site_ref=SITE_REF,
        treatment_role_token=role_token, study_phase=phase,
        planned_drug_identity=planned_drug_identity, dose=dose,
        dose_unit=dose_unit, dosage_form=dosage_form, route=route,
        frequency=frequency, planned_start=planned_start,
        planned_end=planned_end, content_hash=content_hash,
        assignment_lineage=assignment_lineage,
        display_role_label=display_label,
        randomization_token=randomization_token,
        disclosure_state=disclosure,
        source_locator=make_locator("RAND#1", "randomization"))


def make_episode(
    episode_key: str = "EP-1", record_id: str = "EX#1",
    subject: str = "SYN-001", role: str = "active",
    role_confirmed: bool = True, phase: str = "treatment",
    phase_confirmed: bool = True,
    dose: str = "50", dose_unit: str = "mg", dosage_form: str = "tablet",
    route: str = "口服", frequency: str = "每日一次",
    span_start: str = "2026-01-01", span_end: str = "2026-01-28",
    assignment_link: str = "direct", assignment_id: str = "ASSIGN-01",
    disclosure: str = "open", semantics: str = "treatment_span",
    drug_identity: str = "drugX", link_lineage: str = "",
) -> IPExposureEpisode:
    return IPExposureEpisode(
        episode_key=episode_key, subject_ref=subject, site_ref=SITE_REF,
        actual_treatment_role=role,
        source_locator=make_locator(record_id),
        role_confirmed=role_confirmed, study_phase=phase,
        phase_confirmed=phase_confirmed,
        actual_drug_identity=drug_identity,
        dose=dose, dose_unit=dose_unit, dosage_form=dosage_form,
        route=route, frequency=frequency,
        span_start=span_start, span_end=span_end,
        source_semantics=semantics,
        assignment_link_status=assignment_link,
        assignment_id=assignment_id,
        assignment_link_lineage=link_lineage,
        disclosure_state=disclosure)


def make_occurrence(
    occ_id: str, date_start: str, episode_key: str = "EP-1",
    date_end: str = "", continuous_daily: bool = False,
    dose: str = "50", dose_unit: str = "mg", route: str = "口服",
    frequency: str = "每日一次", revision: str = "r1",
    record_id: str = "", snapshot_id: str = SNAPSHOT_ID,
) -> ExposureOccurrence:
    return ExposureOccurrence(
        occurrence_id=occ_id, episode_key=episode_key,
        date_start=date_start, date_end=date_end,
        continuous_daily=continuous_daily,
        dose=dose, dose_unit=dose_unit, route=route, frequency=frequency,
        source_locator=make_locator(
            record_id or f"EX-{occ_id}", snapshot_id=snapshot_id),
        accepted_revision=revision, accepted_revision_hash=f"h-{revision}")


def make_agg_policy(
    version: str = "ap-v1", chash: str = "apch1",
    continuous_expansion: bool = False,
    overlap_policy: str = "boundary", split_lineage: str = "",
) -> ExposureAggregationPolicy:
    return ExposureAggregationPolicy(
        version=version, content_hash=chash,
        rationale="synthetic aggregation policy",
        continuous_interval_expansion_allowed=continuous_expansion,
        overlap_conflict_policy=overlap_policy,
        split_priority_lineage=split_lineage)


def make_plan_actual_rule(
    rule_id: str = "R-IP-01", planned_dose: str = "50",
    planned_unit: str = "mg", planned_form: str = "tablet",
    planned_route: str = "口服", planned_freq: str = "每日一次",
    window_start: str = "2026-01-01", window_end: str = "2026-03-31",
    start_inc: Optional[bool] = True, end_inc: Optional[bool] = True,
    priority: str = "high",
    applicable_phases: Sequence[str] = ("treatment",),
    compare_fields: Sequence[str] = (),
    rule_version: str = "v1", rule_content_hash: str = "rc-plan-01",
    rule_lineage: str = "rl-plan-01",
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version=rule_version,
        clause_locator="P20-1", rule_content_hash=rule_content_hash,
        rule_lineage=rule_lineage, rule_type=RULE_TYPE_PLAN_ACTUAL,
        applicable_treatment_role="active",
        applicable_phases=tuple(applicable_phases),
        window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        planned_dose=planned_dose, planned_dose_unit=planned_unit,
        planned_dosage_form=planned_form, planned_route=planned_route,
        planned_frequency=planned_freq, compare_fields=tuple(compare_fields),
        priority_on_hit=priority, priority_rationale="方案计划给药要求")


def make_allowed_action_rule(
    rule_id: str = "R-IP-02",
    action_types: Sequence[str] = (ACTION_DOSE_REDUCE,),
    allowed_dose_after: Sequence[str] = ("50",),
    allowed_reasons: Sequence[str] = ("毒性",),
    planned_required: bool = True, priority: str = "high",
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P21-1",
        rule_content_hash="rc-action-01", rule_lineage="rl-action-01",
        rule_type=RULE_TYPE_ALLOWED_ACTION,
        applicable_treatment_role="active",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-03-31",
        window_start_inclusive=True, window_end_inclusive=True,
        allowed_action_types=tuple(action_types),
        allowed_reasons=tuple(allowed_reasons),
        allowed_dose_after_values=tuple(allowed_dose_after),
        planned_action_required=planned_required,
        priority_on_hit=priority, priority_rationale="允许的给药调整")


def make_medical_action_rule(
    rule_id: str = "R-IP-03", trigger_role: str = "reported_ae",
    trigger_concept: str = "肝功能异常",
    expected_actions: Sequence[str] = (ACTION_PAUSE,),
    priority: str = "high",
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P22-1",
        rule_content_hash="rc-med-01", rule_lineage="rl-med-01",
        rule_type=RULE_TYPE_MEDICAL_ACTION,
        applicable_treatment_role="active",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-03-31",
        window_start_inclusive=True, window_end_inclusive=True,
        trigger_role=trigger_role, trigger_concept=trigger_concept,
        expected_actions=tuple(expected_actions),
        priority_on_hit=priority, priority_rationale="医学触发处置要求")


def make_adherence_algorithm(
    algorithm_id: str = "ALG-01", metric: str = METRIC_DAY_RATIO,
    window_id: str = "W1", window_start: str = "2026-01-01",
    window_end: str = "2026-01-10",
    start_inc: Optional[bool] = True, end_inc: Optional[bool] = True,
    lower: Optional[str] = "0.8", upper: Optional[str] = None,
    lower_inc: Optional[bool] = True, upper_inc: Optional[bool] = None,
    precision: int = 1, rounding: str = "round_half_up",
    compare: str = "before",
    canonical_unit: str = "", conversions: Sequence[Tuple[str, str, str]] = (),
    pause_handling: str = "included",
) -> AdherenceAlgorithm:
    return AdherenceAlgorithm(
        algorithm_id=algorithm_id, version="v1", content_hash="rc-alg-01",
        metric_kind=metric,
        numerator_source=(
            "actual_exposure_days" if metric == METRIC_DAY_RATIO
            else "recorded_administration"),
        denominator_source=(
            "window_days" if metric == METRIC_DAY_RATIO
            else "planned_amount"),
        window_id=window_id, window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        canonical_unit=canonical_unit, conversion_lineage="cl-v1",
        unit_conversion_rules=tuple(conversions),
        lower_threshold=lower, upper_threshold=upper,
        lower_inclusive=lower_inc, upper_inclusive=upper_inc,
        planned_pause_handling=pause_handling,
        calculation_precision=precision, rounding_mode=rounding,
        compare_before_or_after_rounding=compare,
        rationale="synthetic adherence algorithm")


def make_observation(
    obs_id: str, algorithm_id: str = "ALG-01", window_id: str = "W1",
    coverage: bool = True, numerator: str = "", denominator: str = "",
    unit: str = "", locator: Optional[SourceLocator] = None,
) -> AdherenceObservation:
    return AdherenceObservation(
        observation_id=obs_id, algorithm_id=algorithm_id,
        window_id=window_id, coverage_complete=coverage,
        numerator_value=numerator, denominator_value=denominator,
        unit=unit,
        item_source_locators=(
            (locator,) if locator is not None else
            (make_locator(f"OBS-{obs_id}", "ip_accountability"),)),
        accepted_revision="r1",
        source_locator=make_locator(f"OBS-{obs_id}", "ip_accountability"))


def make_evidence(
    event_key: str = "reported_ae:AE#1", subject: str = "SYN-001",
    episode_key: str = "EP-1", actual_action: str = ACTION_PAUSE,
    concept: str = "肝功能异常",
    event_start: str = "2026-01-05", event_end: str = "2026-01-05",
    confirmation: str = CONFIRMATION_CONFIRMED,
    source_role: str = "reported_ae", record_id: str = "AE#1",
    site_ref: str = SITE_REF,
) -> IPActionEvidence:
    return IPActionEvidence(
        source_role=source_role, stable_source_event_key=event_key,
        subject_ref=subject, site_ref=site_ref,
        linked_ip_episode_id=episode_key, relation_type="triggered_action",
        source_locator=make_locator(record_id, source_role),
        concept=concept, actual_action=actual_action,
        event_start=event_start, event_end=event_end,
        relation_confirmation=confirmation)


def make_planned_action(
    action_id: str = "PA-1", action_type: str = ACTION_PAUSE,
    episode_key: str = "EP-1", assignment_id: str = "ASSIGN-01",
    action_start: str = "2026-01-05", action_end: str = "2026-01-09",
    reason: str = "毒性",
) -> PlannedExposureAction:
    return PlannedExposureAction(
        action_id=action_id, action_type=action_type,
        assignment_id=assignment_id, episode_key=episode_key,
        action_start=action_start, action_end=action_end,
        dose_before="50", dose_after="0", dose_unit="mg",
        reason=reason, source_locator=make_locator(
            f"PACT-{action_id}", "planned_treatment"),
        confirmation_status=CONFIRMATION_CONFIRMED)


def make_actual_action(
    action_id: str = "AA-1", action_type: str = ACTION_DOSE_REDUCE,
    episode_key: str = "EP-1", assignment_id: str = "ASSIGN-01",
    action_start: str = "2026-01-05", action_end: str = "2026-01-09",
    dose_after: str = "25", reason: str = "毒性",
    planned_id: str = "", confirmation: str = CONFIRMATION_CONFIRMED,
) -> ActualIPAction:
    return ActualIPAction(
        action_id=action_id, action_type=action_type,
        assignment_id=assignment_id, episode_key=episode_key,
        action_start=action_start, action_end=action_end,
        dose_before="50", dose_after=dose_after, dose_unit="mg",
        reason=reason, related_planned_action_id=planned_id,
        source_locator=make_locator(
            f"AACT-{action_id}", "ip_action_reason"),
        confirmation_status=confirmation)


def make_return_record(
    record_id: str = "RET#1", subject: str = "SYN-001",
    amount: str = "10", unit: str = "片",
    amount_kind: str = "exact", episode_key: str = "EP-1",
) -> IPSemanticRecord:
    return IPSemanticRecord(
        role="ip_return", concept="study_drug_return",
        locator=make_locator(record_id, "ip_return"),
        subject_ref=subject, site_ref=SITE_REF,
        amount_value=amount, amount_unit=unit, amount_kind=amount_kind,
        linked_ip_episode_key=episode_key)


def make_dispense_record(
    record_id: str = "DISP#1", subject: str = "SYN-001",
    amount: str = "10", unit: str = "片",
    amount_kind: str = "exact", episode_key: str = "EP-1",
) -> IPSemanticRecord:
    return IPSemanticRecord(
        role="ip_dispense", concept="study_drug_dispense",
        locator=make_locator(record_id, "ip_dispense"),
        subject_ref=subject, site_ref=SITE_REF,
        amount_value=amount, amount_unit=unit, amount_kind=amount_kind,
        linked_ip_episode_key=episode_key)


def make_cm_conflict_record(
    record_id: str = "EX#1", subject: str = "SYN-001",
) -> IPSemanticRecord:
    """A recorded_cm row sharing the episode's record id: the same source
    row is mutually exclusively mapped as CM and IP (§3.1)."""
    return IPSemanticRecord(
        role="recorded_cm", concept="concomitant_medication",
        locator=make_locator(record_id, "recorded_cm"),
        subject_ref=subject, site_ref=SITE_REF,
        relationship_confirmation=CONFIRMATION_CONFIRMED)


def make_mapping(version: str = "mv1", chash: str = "mch1",
                 allow: bool = True) -> AssignmentBindingMapping:
    return AssignmentBindingMapping(
        version=version, content_hash=chash,
        rationale="synthetic binding mapping",
        allow_derived_binding=allow)


def make_policy(version: str = "pp-v1") -> D03PriorityPolicy:
    return D03PriorityPolicy(
        version=version, policy_content_hash="pch1",
        rationale="synthetic priority policy")


_NO_POLICY = object()


# ---------------------------------------------------------------------------
# Evaluation entry points
# ---------------------------------------------------------------------------

def evaluate(
    episodes: Sequence[IPExposureEpisode],
    *,
    assignments: Optional[Sequence[PlannedTreatmentAssignment]] = None,
    rules: Sequence[ProtocolExposureRule] = (),
    algorithms: Sequence[AdherenceAlgorithm] = (),
    occurrences: Sequence[ExposureOccurrence] = (),
    evidence: Sequence[IPActionEvidence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    returns: Sequence[IPSemanticRecord] = (),
    dispenses: Sequence[IPSemanticRecord] = (),
    cm_conflicts: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    agg_policy: Any = _NO_POLICY,
    action_coverage: bool = False,
    trigger_coverage: bool = False,
    return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Any = _NO_POLICY,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = SNAPSHOT_ID,
) -> Tuple[IPExpectedSetExpansion, Dict[str, List[IPUnitResult]]]:
    """Expand + evaluate a synthetic D03 collection through the engine.

    Returns ``(expansion, results_by_subject)`` where each expanded unit
    receives exactly one L1 disposition.  Every collection defaults to
    empty; nothing is invented.
    """
    _assignments = list(assignments) if assignments is not None \
        else [make_assignment()]
    _coverage = (dict(role_coverage) if role_coverage is not None
                 else dict(DEFAULT_ROLE_COVERAGE))
    _agg = agg_policy if agg_policy is not _NO_POLICY else make_agg_policy()
    _prio = (priority_policy if priority_policy is not _NO_POLICY
             else make_policy())
    expansion = expand_ip_expected_set(
        project_id=PROJECT_ID, episodes=episodes,
        assignments=_assignments, active_rules=rules,
        adherence_algorithms=algorithms, action_evidence=evidence,
        binding_mapping=binding_mapping)
    by_subject: Dict[str, List[IPUnitResult]] = {}
    for eu in expansion.units:
        r = evaluate_ip_unit(
            project_id=PROJECT_ID, expanded=eu,
            occurrences=occurrences, action_evidence=evidence,
            planned_actions=planned_actions, actual_actions=actual_actions,
            observations=observations, return_records=returns,
            dispense_records=dispenses, cm_conflict_rows=cm_conflicts,
            role_coverage=_coverage, aggregation_policy=_agg,
            action_coverage_complete=action_coverage,
            trigger_coverage_complete=trigger_coverage,
            protocol_return_expectation=return_expectation,
            priority_policy=_prio, binding_mapping=binding_mapping,
            snapshot_id=snapshot_id)
        by_subject.setdefault(r.subject_ref, []).append(r)
    return expansion, by_subject


def evaluate_one(
    episode: IPExposureEpisode,
    *,
    assignments: Optional[Sequence[PlannedTreatmentAssignment]] = None,
    rules: Sequence[ProtocolExposureRule] = (),
    algorithms: Sequence[AdherenceAlgorithm] = (),
    occurrences: Sequence[ExposureOccurrence] = (),
    evidence: Sequence[IPActionEvidence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    returns: Sequence[IPSemanticRecord] = (),
    dispenses: Sequence[IPSemanticRecord] = (),
    cm_conflicts: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    agg_policy: Any = _NO_POLICY,
    action_coverage: bool = False,
    trigger_coverage: bool = False,
    return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Any = _NO_POLICY,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = SNAPSHOT_ID,
) -> Tuple[IPExpectedSetExpansion, List[IPUnitResult]]:
    """Evaluate one episode and return ``(expansion, [results])``.

    The list is ordered as the expansion produced the units.
    """
    expansion, by_subject = evaluate(
        (episode,), assignments=assignments, rules=rules,
        algorithms=algorithms, occurrences=occurrences, evidence=evidence,
        planned_actions=planned_actions, actual_actions=actual_actions,
        observations=observations, returns=returns, dispenses=dispenses,
        cm_conflicts=cm_conflicts, role_coverage=role_coverage,
        agg_policy=agg_policy, action_coverage=action_coverage,
        trigger_coverage=trigger_coverage,
        return_expectation=return_expectation,
        priority_policy=priority_policy, binding_mapping=binding_mapping,
        snapshot_id=snapshot_id)
    subj = episode.subject_ref
    return expansion, by_subject.get(subj, [])


def evaluate_slice(
    episodes: Sequence[IPExposureEpisode],
    *,
    assignments: Optional[Sequence[PlannedTreatmentAssignment]] = None,
    rules: Sequence[ProtocolExposureRule] = (),
    algorithms: Sequence[AdherenceAlgorithm] = (),
    occurrences: Sequence[ExposureOccurrence] = (),
    evidence: Sequence[IPActionEvidence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    returns: Sequence[IPSemanticRecord] = (),
    dispenses: Sequence[IPSemanticRecord] = (),
    cm_conflicts: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    agg_policy: Any = _NO_POLICY,
    action_coverage: bool = False,
    trigger_coverage: bool = False,
    return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Any = _NO_POLICY,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = SNAPSHOT_ID,
) -> Dict[str, IPSliceResult]:
    """Evaluate a synthetic D03 collection through the slice entry point.

    Returns ``subject_ref -> IPSliceResult`` so callers can project the
    journey and read episode rollups.
    """
    _assignments = list(assignments) if assignments is not None \
        else [make_assignment()]
    _coverage = (dict(role_coverage) if role_coverage is not None
                 else dict(DEFAULT_ROLE_COVERAGE))
    _agg = agg_policy if agg_policy is not _NO_POLICY else make_agg_policy()
    _prio = (priority_policy if priority_policy is not _NO_POLICY
             else make_policy())
    return evaluate_ip_slice(
        project_id=PROJECT_ID, episodes=episodes,
        assignments=_assignments, active_rules=rules,
        adherence_algorithms=algorithms, action_evidence=evidence,
        occurrences=occurrences, planned_actions=planned_actions,
        actual_actions=actual_actions, observations=observations,
        return_records=returns, dispense_records=dispenses,
        cm_conflict_rows=cm_conflicts, role_coverage=_coverage,
        aggregation_policy=_agg, action_coverage_complete=action_coverage,
        trigger_coverage_complete=trigger_coverage,
        protocol_return_expectation=return_expectation,
        priority_policy=_prio, binding_mapping=binding_mapping,
        snapshot_id=snapshot_id)


# ---------------------------------------------------------------------------
# Challenge matrix
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPExpectedUnit:
    """Expected outcome for one expanded unit identified by substrings of
    its ``control_item`` / ``control_token``, or by ``unit_index``.

    Exactly one of ``control_item_contains`` / ``control_token_contains`` /
    ``unit_index`` should identify the unit.  ``expected_l1`` is the L1
    disposition that unit must receive.  Optional count fields default to
    ``None`` (don't assert) so each case asserts only what the contract
    requires.
    """

    expected_l1: str
    control_item_contains: str = ""
    control_token_contains: str = ""
    unit_index: Optional[int] = None
    expected_candidate_count: Optional[int] = None
    expected_query_count: Optional[int] = None
    expected_positive_subtype: str = ""
    expected_audience_label: str = ""

    def matches_unit(self, expanded_unit: Any) -> bool:
        if self.unit_index is not None:
            return False  # index match handled by caller
        if self.control_item_contains and (
                self.control_item_contains not in expanded_unit.control_item):
            return False
        if self.control_token_contains and (
                self.control_token_contains not in expanded_unit.control_token):
            return False
        return bool(self.control_item_contains or self.control_token_contains)


@dataclass(frozen=True)
class IPChallengeCase:
    """One numbered frozen §11 challenge case.

    ``build_*`` are zero-arg factories returning the synthetic inputs
    (rebuilt fresh so cases are independent and deterministic).
    ``direct_seeds`` carries pre-built :class:`IPUnitExpanded` seeds for
    the engine-edge fail-closed rows (missing algorithm / missing rule)
    that the slice expansion cannot express.  ``expected_units`` lists the
    expected per-unit outcomes; ``expected_set_size`` is the expected
    number of expanded units (defaults to ``len(expected_units)`` when not
    set, or ``len(direct_seeds)`` for direct cases).
    """

    number: int
    name: str
    category: str
    description: str
    build_episodes: Any = field(default=tuple, repr=False)
    build_assignments: Any = field(default=tuple, repr=False)
    build_rules: Any = field(default=tuple, repr=False)
    build_algorithms: Any = field(default=tuple, repr=False)
    build_occurrences: Any = field(default=tuple, repr=False)
    build_evidence: Any = field(default=tuple, repr=False)
    build_planned_actions: Any = field(default=tuple, repr=False)
    build_actual_actions: Any = field(default=tuple, repr=False)
    build_observations: Any = field(default=tuple, repr=False)
    build_returns: Any = field(default=tuple, repr=False)
    build_dispenses: Any = field(default=tuple, repr=False)
    build_cm_conflicts: Any = field(default=tuple, repr=False)
    direct_seeds: Tuple[Any, ...] = ()
    expected_units: Tuple[IPExpectedUnit, ...] = ()
    expected_set_size: Optional[int] = None
    role_coverage_override: Optional[Mapping[str, bool]] = None
    agg_policy_override: Any = _NO_POLICY
    action_coverage: bool = False
    trigger_coverage: bool = False
    return_expectation: str = RETURN_UNKNOWN
    priority_policy_override: Any = _NO_POLICY
    binding_mapping_override: Optional[AssignmentBindingMapping] = None

    # -- input collection helpers ----------------------------------------

    def _assignments(self) -> List[PlannedTreatmentAssignment]:
        out = list(self.build_assignments())
        return out or [make_assignment()]

    def _role_coverage(self) -> Dict[str, bool]:
        cov = dict(DEFAULT_ROLE_COVERAGE)
        if self.role_coverage_override is not None:
            cov.update(self.role_coverage_override)
        return cov

    def _agg_policy(self) -> ExposureAggregationPolicy:
        if self.agg_policy_override is not _NO_POLICY:
            return self.agg_policy_override
        return make_agg_policy()

    def _priority_policy(self) -> D03PriorityPolicy:
        if self.priority_policy_override is not _NO_POLICY:
            return self.priority_policy_override
        return make_policy()

    # -- evaluation ------------------------------------------------------

    def build(
        self, **overrides: Any,
    ) -> Tuple[IPExpectedSetExpansion, List[IPUnitResult]]:
        """Build inputs, run the engine, return (expansion, results).

        ``overrides`` may set ``snapshot_id``, ``rules`` and
        ``algorithms`` (used by the N->N+1 replay); nothing else is
        forwarded.
        """
        snapshot_id = overrides.pop("snapshot_id", SNAPSHOT_ID)
        rules = overrides.pop("rules", None)
        algorithms = overrides.pop("algorithms", None)
        if overrides:
            raise TypeError(f"unexpected build overrides {sorted(overrides)}")
        _rules = list(rules) if rules is not None else list(self.build_rules())
        _algorithms = (
            list(algorithms) if algorithms is not None
            else list(self.build_algorithms()))
        if self.direct_seeds:
            return self._build_direct(snapshot_id=snapshot_id)
        episodes = list(self.build_episodes())
        assignments = self._assignments()
        exp, by_subject = evaluate(
            episodes, assignments=assignments, rules=_rules,
            algorithms=_algorithms,
            occurrences=list(self.build_occurrences()),
            evidence=list(self.build_evidence()),
            planned_actions=list(self.build_planned_actions()),
            actual_actions=list(self.build_actual_actions()),
            observations=list(self.build_observations()),
            returns=list(self.build_returns()),
            dispenses=list(self.build_dispenses()),
            cm_conflicts=list(self.build_cm_conflicts()),
            role_coverage=self._role_coverage(),
            agg_policy=self._agg_policy(),
            action_coverage=self.action_coverage,
            trigger_coverage=self.trigger_coverage,
            return_expectation=self.return_expectation,
            priority_policy=self._priority_policy(),
            binding_mapping=self.binding_mapping_override,
            snapshot_id=snapshot_id)
        return exp, self._ordered(exp, by_subject)

    def _build_direct(
        self, *, snapshot_id: str,
    ) -> Tuple[IPExpectedSetExpansion, List[IPUnitResult]]:
        """Evaluate pre-built :class:`IPUnitExpanded` seeds (engine-edge
        fail-closed rows: missing algorithm / missing rule)."""
        seeds = list(self.direct_seeds)
        expansion = IPExpectedSetExpansion(
            units=tuple(seeds), project_id=PROJECT_ID,
            binding_mapping=self.binding_mapping_override)
        results: List[IPUnitResult] = []
        for eu in seeds:
            results.append(evaluate_ip_unit(
                project_id=PROJECT_ID, expanded=eu,
                occurrences=list(self.build_occurrences()),
                action_evidence=list(self.build_evidence()),
                planned_actions=list(self.build_planned_actions()),
                actual_actions=list(self.build_actual_actions()),
                observations=list(self.build_observations()),
                return_records=list(self.build_returns()),
                dispense_records=list(self.build_dispenses()),
                cm_conflict_rows=list(self.build_cm_conflicts()),
                role_coverage=self._role_coverage(),
                aggregation_policy=self._agg_policy(),
                action_coverage_complete=self.action_coverage,
                trigger_coverage_complete=self.trigger_coverage,
                protocol_return_expectation=self.return_expectation,
                priority_policy=self._priority_policy(),
                binding_mapping=self.binding_mapping_override,
                snapshot_id=snapshot_id))
        return expansion, results

    @staticmethod
    def _ordered(
        exp: IPExpectedSetExpansion,
        by_subject: Dict[str, List[IPUnitResult]],
    ) -> List[IPUnitResult]:
        """Order results by expansion unit order for index matching."""
        id_to_result: Dict[str, IPUnitResult] = {}
        for urs in by_subject.values():
            for r in urs:
                id_to_result[r.unit_id] = r
        ordered: List[IPUnitResult] = []
        for eu in exp.units:
            uid = eu.build_unit(PROJECT_ID).unit_id
            r = id_to_result.get(uid)
            if r is not None:
                ordered.append(r)
        return ordered

    def build_slice(self) -> Tuple[IPSliceResult, IPExpectedSetExpansion]:
        """Run the slice entry point (subject -> IPSliceResult) plus the
        expansion, so callers can project the journey and read rollups."""
        if self.direct_seeds:
            exp, results = self.build()
            all_results = list(results)
            sr = IPSliceResult(
                subject_ref=all_results[0].subject_ref if all_results else "",
                unit_results=tuple(all_results),
                r2_candidates=tuple(
                    c for r in all_results for c in r.r2_candidates),
                expected_set_hash=exp.expected_set_hash,
                rule_lineage=RULE_LINEAGE)
            return sr, exp
        episodes = list(self.build_episodes())
        rules = list(self.build_rules())
        algorithms = list(self.build_algorithms())
        assignments = self._assignments()
        by_subj = evaluate_slice(
            episodes, assignments=assignments, rules=rules,
            algorithms=algorithms,
            occurrences=list(self.build_occurrences()),
            evidence=list(self.build_evidence()),
            planned_actions=list(self.build_planned_actions()),
            actual_actions=list(self.build_actual_actions()),
            observations=list(self.build_observations()),
            returns=list(self.build_returns()),
            dispenses=list(self.build_dispenses()),
            cm_conflicts=list(self.build_cm_conflicts()),
            role_coverage=self._role_coverage(),
            agg_policy=self._agg_policy(),
            action_coverage=self.action_coverage,
            trigger_coverage=self.trigger_coverage,
            return_expectation=self.return_expectation,
            priority_policy=self._priority_policy(),
            binding_mapping=self.binding_mapping_override)
        exp = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=episodes,
            assignments=assignments, active_rules=rules,
            adherence_algorithms=algorithms,
            action_evidence=list(self.build_evidence()),
            binding_mapping=self.binding_mapping_override)
        subj = episodes[0].subject_ref if episodes else ""
        return by_subj[subj], exp

    def day_computation(self) -> ExposureDayComputation:
        """Actual-exposure-day computation for single-episode cases."""
        episodes = list(self.build_episodes())
        if len(episodes) != 1:
            raise AssertionError("day_computation requires exactly one episode")
        return compute_actual_exposure_days(
            episode=episodes[0],
            occurrences=list(self.build_occurrences()),
            policy=self._agg_policy())

    def expected_count(self) -> int:
        if self.expected_set_size is not None:
            return self.expected_set_size
        if self.direct_seeds:
            return len(self.direct_seeds)
        return len(self.expected_units)


@dataclass(frozen=True)
class IPChallengeMatrix:
    """The full numbered frozen §11 challenge matrix for D03."""

    cases: Tuple[IPChallengeCase, ...]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def numbers(self) -> Tuple[int, ...]:
        return tuple(c.number for c in self.cases)

    def by_number(self, number: int) -> IPChallengeCase:
        for c in self.cases:
            if c.number == number:
                return c
        raise KeyError(f"no challenge case #{number}")

    def by_name(self, name: str) -> IPChallengeCase:
        for c in self.cases:
            if c.name == name:
                return c
        raise KeyError(f"no challenge case named {name!r}")


# -- helpers for building the cases ----------------------------------------

def _ev(
    l1: str, *, control_item: str = "", control_token: str = "",
    index: Optional[int] = None, cand: Optional[int] = None,
    query: Optional[int] = None, subtype: str = "",
    audience: str = "",
) -> IPExpectedUnit:
    return IPExpectedUnit(
        expected_l1=l1, control_item_contains=control_item,
        control_token_contains=control_token, unit_index=index,
        expected_candidate_count=cand, expected_query_count=query,
        expected_positive_subtype=subtype, expected_audience_label=audience)


def _role_negative() -> IPExpectedUnit:
    return _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ROLE_PHASE)


def _role_boundary() -> IPExpectedUnit:
    return _ev(L1Disposition.BOUNDARY, control_item=CONTROL_ROLE_PHASE,
               cand=1, query=0)


def build_ip_challenge_matrix() -> IPChallengeMatrix:
    """Build the frozen §11 51-case synthetic challenge matrix.

    Every frozen challenge row is represented as an executable case with
    explicit expected per-unit L1 assertions:

    1. six positive subtypes each with a corresponding negative (1-12);
    2. boundary: threshold equality, window endpoints, partial dates,
       action overlap, blinded ambiguous background role (13-17);
    3. fail-closed not_evaluable: missing algorithm, missing denominator,
       unit conflict, unconfirmed role, CM/IP mutual exclusion, single
       missing occurrence never implies missed dose (18-23);
    4. exposure-day semantics: span != actual days, sparse dosing, daily
       multi-dose, continuous interval, same-role union, different-dose
       overlap never silently merged (24-27);
    5. medical-trigger linkage: wrong subject/site/episode, unconfirmed
       relation (28);
    6. binding/disclosure: missing link, ambiguous assignment, blinded
       match/conflict/masking (29-31);
    7. return decision table §5.4: uncovered, zero rows, empty field,
       explicit zero, partial value, not-applicable (32-37);
    8. planned/actual actions: pause denominator effect, resume/stop
       closure (38-39);
    9. adherence arithmetic: 79.95 rounding, zero denominator, duplicate
       observation, unit conversion, window endpoint exclusivity (40-44);
    10. determinism: locator dedup + revision conflict, out-of-order
        input (45-46);
    11. lifecycle seeds: linked-negative close, rule supersede, positive +
        not_evaluable sibling rollup (47-49);
    12. accountability unit conversion (§6.2 rules 1/3): a versioned
        conversion that closes the balance is negative; the same
        cross-unit inputs without a conversion basis fail closed to
        not_evaluable with no candidate/Query (50-51).
    """
    cases: List[IPChallengeCase] = []

    # -- 1. Six positives + six negatives ---------------------------------

    cases.append(IPChallengeCase(
        number=1, name="plan_actual_dose_mismatch_positive",
        category="positive",
        description="actual 25 mg vs planned 50 mg -> plan_actual positive",
        build_episodes=lambda: (make_episode(dose="25"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        build_occurrences=lambda: (make_occurrence("OC-1", "2026-01-01",
                                                   dose="25"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_PLAN_ACTUAL,
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH]),
        )))

    cases.append(IPChallengeCase(
        number=2, name="plan_actual_consistent_negative",
        category="negative",
        description="actual 50 mg matches plan -> plan_actual negative",
        build_episodes=lambda: (make_episode(dose="50"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        build_occurrences=lambda: (make_occurrence("OC-1", "2026-01-01",
                                                   dose="50"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_PLAN_ACTUAL),
        )))

    cases.append(IPChallengeCase(
        number=3, name="role_phase_mismatch_positive",
        category="positive",
        description=(
            "actual role placebo vs assigned active -> role_phase positive"),
        build_episodes=lambda: (make_episode(role="placebo"),),
        expected_set_size=1,
        expected_units=(
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ROLE_PHASE,
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH]),
        )))

    cases.append(IPChallengeCase(
        number=4, name="role_phase_consistent_negative",
        category="negative",
        description="role and phase match the confirmed assignment",
        build_episodes=lambda: (make_episode(),),
        expected_set_size=1,
        expected_units=(_role_negative(),)))

    cases.append(IPChallengeCase(
        number=5, name="adherence_day_ratio_low_positive",
        category="positive",
        description="2 of 10 window days -> adherence out of range",
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01"),
            make_occurrence("OC-2", "2026-01-05"),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ADHERENCE,
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]),
        )))

    cases.append(IPChallengeCase(
        number=6, name="adherence_day_ratio_in_range_negative",
        category="negative",
        description="8 of 10 window days == lower threshold inclusive -> ok",
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in range(1, 9)),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    cases.append(IPChallengeCase(
        number=7, name="unsupported_dose_reduce_25_vs_50_positive",
        category="positive",
        description=(
            "actual reduce to 25 mg not in allowed 50 mg -> unsupported"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_allowed_action_rule(),),
        build_planned_actions=lambda: (
            make_planned_action("PA-1", ACTION_DOSE_REDUCE,
                                action_start="2026-01-05",
                                action_end="2026-01-09"),),
        build_actual_actions=lambda: (
            make_actual_action("AA-1", ACTION_DOSE_REDUCE,
                               action_start="2026-01-05",
                               action_end="2026-01-09", dose_after="25"),),
        action_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE,
                control_token="allowed_action:R-IP-02:dose_reduce",
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION]),
        )))

    cases.append(IPChallengeCase(
        number=8, name="supported_dose_reduce_negative",
        category="negative",
        description=(
            "actual reduce to 50 mg with reason and planned action -> ok"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_allowed_action_rule(),),
        build_planned_actions=lambda: (
            make_planned_action("PA-1", ACTION_DOSE_REDUCE,
                                action_start="2026-01-05",
                                action_end="2026-01-09"),),
        build_actual_actions=lambda: (
            make_actual_action("AA-1", ACTION_DOSE_REDUCE,
                               action_start="2026-01-05",
                               action_end="2026-01-09", dose_after="50"),),
        action_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE,
                control_token="allowed_action:R-IP-02:dose_reduce"),
        )))

    cases.append(IPChallengeCase(
        number=9, name="medical_trigger_action_conflict_positive",
        category="positive",
        description=(
            "AE trigger expects pause but actual resume -> inconsistent"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_medical_action_rule(),),
        build_evidence=lambda: (
            make_evidence(actual_action=ACTION_RESUME),),
        trigger_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE,
                control_token="medical_action:R-IP-03:reported_ae:AE#1",
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT]),
        )))

    cases.append(IPChallengeCase(
        number=10, name="medical_trigger_action_consistent_negative",
        category="negative",
        description="AE trigger pause matches actual pause -> negative",
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_medical_action_rule(),),
        build_evidence=lambda: (
            make_evidence(actual_action=ACTION_PAUSE),),
        trigger_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE,
                control_token="medical_action:R-IP-03:reported_ae:AE#1"),
        )))

    cases.append(IPChallengeCase(
        number=11, name="accountability_balance_mismatch_positive",
        category="positive",
        description=(
            "dispense 20 - return 10 = 10 != recorded 5 -> inconsistency"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY,
                canonical_unit="片"),),
        build_dispenses=lambda: (
            make_dispense_record("DISP#1", amount="20"),),
        build_returns=lambda: (make_return_record("RET#1", amount="10"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="5", unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ACCOUNTABILITY,
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
                audience=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY]),
        )))

    cases.append(IPChallengeCase(
        number=12, name="accountability_balance_closed_negative",
        category="negative",
        description="dispense 20 - return 10 == recorded 10 -> closed",
        build_episodes=lambda: (make_episode(),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY,
                canonical_unit="片"),),
        build_dispenses=lambda: (
            make_dispense_record("DISP#1", amount="20"),),
        build_returns=lambda: (make_return_record("RET#1", amount="10"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="10", unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ACCOUNTABILITY),
        )))

    # -- 2. Boundary rows -------------------------------------------------

    cases.append(IPChallengeCase(
        number=13, name="adherence_threshold_equality_boundary",
        category="boundary",
        description=(
            "9/10 == upper threshold with unstated inclusivity -> boundary"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(lower=None, upper="0.9",
                                     lower_inc=None, upper_inc=None),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in range(1, 10)),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.BOUNDARY, control_item=CONTROL_ADHERENCE,
                cand=1, query=0),
        )))

    cases.append(IPChallengeCase(
        number=14, name="window_endpoint_inclusivity_boundary",
        category="boundary",
        description=(
            "episode ends exactly at rule window end, inclusivity unstated "
            "-> boundary"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-10", span_end="2026-01-10"),),
        build_rules=lambda: (
            make_plan_actual_rule(window_start="2026-01-01",
                                  window_end="2026-01-10",
                                  end_inc=None),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.BOUNDARY, control_item=CONTROL_PLAN_ACTUAL,
                cand=1, query=0),
        )))

    cases.append(IPChallengeCase(
        number=15, name="partial_date_boundary",
        category="boundary",
        description=(
            "month-precision span start cannot resolve window overlap -> "
            "boundary"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01", span_end="2026-01-28"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.BOUNDARY, control_item=CONTROL_PLAN_ACTUAL,
                cand=1, query=0),
        )))

    cases.append(IPChallengeCase(
        number=16, name="action_overlap_boundary",
        category="boundary",
        description=(
            "one actual action maps to two confirmed planned actions -> "
            "boundary"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_allowed_action_rule(),),
        build_planned_actions=lambda: (
            make_planned_action("PA-1", ACTION_DOSE_REDUCE,
                                action_start="2026-01-05",
                                action_end="2026-01-09"),
            make_planned_action("PA-2", ACTION_DOSE_REDUCE,
                                action_start="2026-01-11",
                                action_end="2026-01-13"),
        ),
        build_actual_actions=lambda: (
            make_actual_action("AA-1", ACTION_DOSE_REDUCE,
                               action_start="2026-01-05",
                               action_end="2026-01-09", dose_after="50"),),
        action_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.BOUNDARY,
                control_token="allowed_action:R-IP-02:dose_reduce",
                cand=1, query=0),
        )))

    cases.append(IPChallengeCase(
        number=17, name="blinded_ambiguous_assignment_boundary",
        category="boundary",
        description=(
            "two blinded assignments both fit; ambiguous binding is "
            "boundary and never leaks drug identity"),
        build_episodes=lambda: (
            make_episode(assignment_link="none", assignment_id="",
                         disclosure="masked_identity"),),
        build_assignments=lambda: (
            make_assignment(
                assignment_id="ASSIGN-A",
                display_label="研究药物（盲态标签）",
                disclosure="masked_identity",
                planned_drug_identity="synthetic_drug_x",
                content_hash="asg-hash-a", assignment_lineage="asg-a"),
            make_assignment(
                assignment_id="ASSIGN-B",
                display_label="研究药物（盲态标签）",
                disclosure="masked_identity",
                planned_drug_identity="synthetic_drug_y",
                content_hash="asg-hash-b", assignment_lineage="asg-b"),
        ),
        binding_mapping_override=make_mapping(),
        expected_set_size=1,
        expected_units=(_role_boundary(),)))

    # -- 3. Fail-closed not_evaluable rows --------------------------------

    def _missing_algorithm_seed() -> Tuple[Any, ...]:
        episode = make_episode(span_start="2026-01-01",
                               span_end="2026-01-10")
        assignment = make_assignment()
        resolution = AssignmentResolution(
            status=RESOLUTION_BOUND, assignment=assignment)
        seed = IPUnitExpanded(
            episode=episode, control_item=CONTROL_ADHERENCE,
            control_token="adherence:none:none",
            risk_family="adherence",
            resolution=resolution, assignment=assignment)
        return (seed,)

    cases.append(IPChallengeCase(
        number=18, name="missing_algorithm_not_evaluable",
        category="not_evaluable",
        description=(
            "adherence unit without an algorithm fails closed (row 3)"),
        direct_seeds=_missing_algorithm_seed(),
        expected_set_size=1,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                control_item=CONTROL_ADHERENCE, cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=19, name="missing_denominator_not_evaluable",
        category="not_evaluable",
        description=(
            "day-ratio algorithm with unstated window endpoint inclusivity "
            "-> denominator uncomputable (row 3)"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(window_start="2026-01-02",
                                     window_end="2026-01-10",
                                     start_inc=None, end_inc=True),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in range(1, 6)),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=20, name="unit_conflict_not_evaluable",
        category="not_evaluable",
        description=(
            "observation unit 'mg' vs canonical '片' without conversion -> "
            "not_evaluable (row 3)"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                metric=METRIC_DOSE_COUNT_RATIO, canonical_unit="片",
                conversions=()),),
        build_observations=lambda: (
            make_observation("OBS-1", numerator="10", denominator="10",
                             unit="mg"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=21, name="role_unconfirmed_not_evaluable",
        category="not_evaluable",
        description="unconfirmed treatment role -> role_phase not_evaluable",
        build_episodes=lambda: (make_episode(role_confirmed=False),),
        expected_set_size=1,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ROLE_PHASE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=22, name="cm_ip_mutual_exclusion_not_evaluable",
        category="not_evaluable",
        description=(
            "same source row mapped as both recorded_cm and ip_exposure -> "
            "not_evaluable (row 3)"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_plan_actual_rule(),),
        build_cm_conflicts=lambda: (make_cm_conflict_record("EX#1"),),
        expected_set_size=2,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ROLE_PHASE,
                cand=0, query=0),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_PLAN_ACTUAL,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=23, name="missing_occurrence_no_missed_dose",
        category="not_evaluable",
        description=(
            "no occurrence rows -> never infer missed dose (row 3)"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    # -- 4. Exposure-day semantics (row 4) --------------------------------

    cases.append(IPChallengeCase(
        number=24, name="span_vs_actual_days",
        category="exposure_days",
        description=(
            "28-day span with only D1 + D15 occurrences -> 2 actual days; "
            "adherence uses 2, never the span"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-28"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(window_start="2026-01-01",
                                     window_end="2026-01-28"),),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01"),
            make_occurrence("OC-2", "2026-01-15"),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ADHERENCE,
                cand=1, query=1),
        )))

    cases.append(IPChallengeCase(
        number=25, name="multi_dose_and_interval_days",
        category="exposure_days",
        description=(
            "two doses on one day count once; explicit continuous interval "
            "expands to its day set"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01", dose="50"),
            make_occurrence("OC-2", "2026-01-01", dose="25"),
            make_occurrence("OC-3", "2026-01-05", date_end="2026-01-07",
                            continuous_daily=True),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        agg_policy_override=make_agg_policy(continuous_expansion=True),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ADHERENCE,
                cand=1, query=1),
        )))

    cases.append(IPChallengeCase(
        number=26, name="same_role_overlap_union",
        category="exposure_days",
        description=(
            "same-role same-dose overlapping intervals union their day set, "
            "never sum interval lengths"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01", date_end="2026-01-03",
                            continuous_daily=True),
            make_occurrence("OC-2", "2026-01-03", date_end="2026-01-05",
                            continuous_daily=True),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        agg_policy_override=make_agg_policy(continuous_expansion=True),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ADHERENCE,
                cand=1, query=1),
        )))

    cases.append(IPChallengeCase(
        number=27, name="different_dose_overlap_no_merge",
        category="exposure_days",
        description=(
            "different-dose overlapping intervals never silently merge; "
            "union_fail policy -> ambiguous -> not_evaluable"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01", date_end="2026-01-05",
                            continuous_daily=True, dose="50"),
            make_occurrence("OC-2", "2026-01-03", date_end="2026-01-07",
                            continuous_daily=True, dose="25"),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        agg_policy_override=make_agg_policy(
            continuous_expansion=True, overlap_policy="union_fail"),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    # -- 5. Medical-trigger linkage (row 5) -------------------------------

    cases.append(IPChallengeCase(
        number=28, name="wrong_subject_site_episode_unconfirmed",
        category="medical_linkage",
        description=(
            "wrong subject / wrong site / wrong episode / unconfirmed "
            "relation never form a positive or negative"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (make_medical_action_rule(),),
        build_evidence=lambda: (
            make_evidence(event_key="reported_ae:AE-WS",
                          subject="SYN-OTHER", record_id="AE-WS"),
            make_evidence(event_key="reported_ae:AE-WSITE",
                          site_ref="SITE99", record_id="AE-WSITE"),
            make_evidence(event_key="reported_ae:AE-WEP",
                          episode_key="EP-9", record_id="AE-WEP"),
            make_evidence(event_key="reported_ae:AE-UNC",
                          confirmation=CONFIRMATION_UNRESOLVED,
                          record_id="AE-UNC"),
        ),
        trigger_coverage=True,
        expected_set_size=5,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_token="medical_action:R-IP-03:reported_ae:AE-WS",
                cand=0, query=0),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_token="medical_action:R-IP-03:reported_ae:AE-WSITE",
                cand=0, query=0),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_token="medical_action:R-IP-03:reported_ae:AE-WEP",
                cand=0, query=0),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_token="medical_action:R-IP-03:reported_ae:AE-UNC",
                cand=0, query=0),
        )))

    # -- 6. Binding / disclosure (row 6) ----------------------------------

    cases.append(IPChallengeCase(
        number=29, name="missing_assignment_link_not_evaluable",
        category="binding",
        description=(
            "no direct link and no derived mapping -> binding missing -> "
            "not_evaluable"),
        build_episodes=lambda: (
            make_episode(assignment_link="none", assignment_id=""),),
        expected_set_size=1,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ROLE_PHASE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=30, name="ambiguous_assignment_boundary",
        category="binding",
        description=(
            "two feasible assignments -> ambiguous binding is boundary; "
            "kernel never picks by drug name or order"),
        build_episodes=lambda: (
            make_episode(assignment_link="none", assignment_id=""),),
        build_assignments=lambda: (
            make_assignment(assignment_id="ASSIGN-A",
                            content_hash="asg-hash-a",
                            assignment_lineage="asg-a"),
            make_assignment(assignment_id="ASSIGN-B",
                            content_hash="asg-hash-b",
                            assignment_lineage="asg-b"),
        ),
        binding_mapping_override=make_mapping(),
        expected_set_size=1,
        expected_units=(_role_boundary(),)))

    cases.append(IPChallengeCase(
        number=31, name="masked_identity_no_leak",
        category="blinding",
        description=(
            "masked identity: role/phase verifiable without drug identity; "
            "masked dose makes dose compare not_evaluable"),
        build_episodes=lambda: (
            make_episode(disclosure="masked_identity_and_dose"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        expected_set_size=2,
        expected_units=(
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ROLE_PHASE),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_PLAN_ACTUAL,
                cand=0, query=0),
        )))

    # -- 7. Return decision table §5.4 (row 7) ----------------------------

    def _accountability_algorithm():
        return (make_adherence_algorithm(
            algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY,
            canonical_unit="片"),)

    cases.append(IPChallengeCase(
        number=32, name="return_uncovered_not_evaluable",
        category="accountability",
        description="ip_return role uncovered -> not_evaluable, never zero",
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        role_coverage_override={"ip_return": False},
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ACCOUNTABILITY,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=33, name="return_expected_no_rows_not_evaluable",
        category="accountability",
        description=(
            "protocol expects return but no locatable return rows -> "
            "not_evaluable, no inference of non-return"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        return_expectation=RETURN_EXPECTED,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ACCOUNTABILITY,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=34, name="return_empty_field_not_evaluable",
        category="accountability",
        description="return row with empty amount/unit -> not_evaluable",
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        build_returns=lambda: (
            make_return_record("RET#1", amount="", amount_kind="missing"),),
        build_dispenses=lambda: (make_dispense_record("DISP#1", amount="10"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="10", unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ACCOUNTABILITY,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=35, name="return_explicit_zero_enters_algorithm",
        category="accountability",
        description=(
            "explicit zero return is a known value, not missing: balance "
            "10 - 0 == recorded 10 -> negative"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        build_returns=lambda: (
            make_return_record("RET#1", amount="0", amount_kind="zero"),),
        build_dispenses=lambda: (make_dispense_record("DISP#1", amount="10"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="10", unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ACCOUNTABILITY),
        )))

    cases.append(IPChallengeCase(
        number=36, name="return_partial_boundary",
        category="accountability",
        description="range/partial return amount -> boundary",
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        build_returns=lambda: (
            make_return_record("RET#1", amount="5-10", amount_kind="range"),),
        build_dispenses=lambda: (make_dispense_record("DISP#1", amount="10"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.BOUNDARY, control_item=CONTROL_ACCOUNTABILITY,
                cand=1, query=0),
        )))

    cases.append(IPChallengeCase(
        number=37, name="return_not_required_not_applicable",
        category="accountability",
        description=(
            "protocol declares no return required in window -> "
            "not_applicable"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=_accountability_algorithm,
        return_expectation=RETURN_NOT_REQUIRED,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_APPLICABLE,
                control_item=CONTROL_ACCOUNTABILITY),
        )))

    # -- 8. Planned/actual actions (row 8) --------------------------------

    cases.append(IPChallengeCase(
        number=38, name="planned_pause_denominator_effect",
        category="actions",
        description=(
            "planned pause excluded from denominator: 5 actual days / "
            "(10 - 5 pause days) = 1.0 in range -> negative"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(pause_handling="excluded_from_denominator"),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in range(1, 6)),
        build_planned_actions=lambda: (
            make_planned_action("PA-1", ACTION_PAUSE,
                                action_start="2026-01-05",
                                action_end="2026-01-09"),),
        build_observations=lambda: (make_observation("OBS-1"),),
        action_coverage=True,
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    cases.append(IPChallengeCase(
        number=39, name="planned_actual_resume_stop",
        category="actions",
        description=(
            "resume with planned closure -> negative; stop without any "
            "actual action record -> not_evaluable (fail closed)"),
        build_episodes=lambda: (make_episode(),),
        build_rules=lambda: (
            make_allowed_action_rule(
                action_types=(ACTION_RESUME, ACTION_STOP),
                allowed_dose_after=(), allowed_reasons=()),),
        build_planned_actions=lambda: (
            make_planned_action("PA-R", ACTION_RESUME,
                                action_start="2026-01-11",
                                action_end="2026-01-13"),),
        build_actual_actions=lambda: (
            make_actual_action("AA-R", ACTION_RESUME,
                               action_start="2026-01-11",
                               action_end="2026-01-13"),),
        action_coverage=True,
        expected_set_size=3,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE,
                control_token="allowed_action:R-IP-02:resume"),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_token="allowed_action:R-IP-02:stop",
                cand=0, query=0),
        )))

    # -- 9. Adherence arithmetic (row 9) ----------------------------------

    cases.append(IPChallengeCase(
        number=40, name="rounding_79_95_after_rounding_negative",
        category="adherence_arithmetic",
        description=(
            "79.95/100 displayed as 80.0 and compared after rounding at "
            "threshold 0.8 -> negative"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                metric=METRIC_AMOUNT_RATIO, lower="0.8", upper=None,
                lower_inc=True, upper_inc=None, precision=2,
                compare="after", canonical_unit="", conversions=()),),
        build_observations=lambda: (
            make_observation("OBS-1", numerator="79.95",
                             denominator="100", unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    cases.append(IPChallengeCase(
        number=41, name="zero_denominator_not_evaluable",
        category="adherence_arithmetic",
        description="zero denominator fails closed (row 9)",
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(metric=METRIC_AMOUNT_RATIO),),
        build_observations=lambda: (
            make_observation("OBS-1", numerator="10", denominator="0",
                             unit="片"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=42, name="duplicate_observation_not_evaluable",
        category="adherence_arithmetic",
        description=(
            "two different observations for one algorithm+window -> "
            "not_evaluable (row 9)"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(metric=METRIC_AMOUNT_RATIO),),
        build_observations=lambda: (
            make_observation("OBS-1", numerator="9", denominator="10",
                             unit="片"),
            make_observation("OBS-2", numerator="8", denominator="10",
                             unit="片"),
        ),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=43, name="unit_conversion_ok_negative",
        category="adherence_arithmetic",
        description=(
            "versioned conversion g->mg: 0.05g/0.1g = 50mg/100mg = 0.5 in "
            "range -> negative"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                metric=METRIC_DOSE_COUNT_RATIO, canonical_unit="mg",
                conversions=(("g", "mg", "1000"),),
                lower="0.4", upper="0.9", lower_inc=True, upper_inc=True),),
        build_observations=lambda: (
            make_observation("OBS-1", numerator="0.05", denominator="0.1",
                             unit="g"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    cases.append(IPChallengeCase(
        number=44, name="window_endpoint_exclusive_negative",
        category="adherence_arithmetic",
        description=(
            "inclusive window: 9/10 = 0.9 at inclusive lower -> negative; "
            "the test flips start inclusivity to prove the endpoint rule"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(lower="0.9", upper=None,
                                     lower_inc=True, upper_inc=None),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in range(1, 10)),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    # -- 10. Determinism (row 10) -----------------------------------------

    cases.append(IPChallengeCase(
        number=45, name="locator_dedup_revision_ambiguous",
        category="determinism",
        description=(
            "identical rows under one locator dedup; a stable event with "
            "two accepted revisions is ambiguous -> not_evaluable"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: (
            make_occurrence("OC-A1", "2026-01-01", record_id="EX-DUP"),
            make_occurrence("OC-A2", "2026-01-01", record_id="EX-DUP"),
            make_occurrence("OC-B1", "2026-01-05", record_id="EX-REV",
                            revision="r1", snapshot_id="snap-r1"),
            make_occurrence("OC-B2", "2026-01-05", record_id="EX-REV",
                            revision="r2", snapshot_id="snap-r2"),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE, control_item=CONTROL_ADHERENCE,
                cand=0, query=0),
        )))

    cases.append(IPChallengeCase(
        number=46, name="out_of_order_deterministic",
        category="determinism",
        description=(
            "occurrences supplied in reverse order produce the same day set "
            "and the same evaluation"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (make_adherence_algorithm(),),
        build_occurrences=lambda: tuple(
            make_occurrence(f"OC-{d}", f"2026-01-{d:02d}")
            for d in (8, 3, 1, 6, 2, 7, 5, 4)),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ADHERENCE),
        )))

    # -- 11. Lifecycle seeds + sibling rollup (row 11) --------------------

    cases.append(IPChallengeCase(
        number=47, name="n_to_n1_linked_negative_seed",
        category="lifecycle",
        description=(
            "plan_actual positive seed for the N->N+1 linked-negative "
            "machine close"),
        build_episodes=lambda: (make_episode(dose="25"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        build_occurrences=lambda: (make_occurrence("OC-1", "2026-01-01",
                                                   dose="25"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_PLAN_ACTUAL,
                cand=1, query=1),
        )))

    cases.append(IPChallengeCase(
        number=48, name="rule_version_supersede_seed",
        category="lifecycle",
        description=(
            "same stable event under a changed rule version -> supersede, "
            "never resolved_by_data"),
        build_episodes=lambda: (make_episode(dose="25"),),
        build_rules=lambda: (make_plan_actual_rule(),),
        build_occurrences=lambda: (make_occurrence("OC-1", "2026-01-01",
                                                   dose="25"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_PLAN_ACTUAL,
                cand=1, query=1),
        )))

    cases.append(IPChallengeCase(
        number=49, name="positive_ne_sibling_rollup",
        category="lifecycle",
        description=(
            "one episode with a positive adherence unit AND a "
            "not_evaluable accountability unit; rollup keeps both flags and "
            "domain is not complete"),
        build_episodes=lambda: (
            make_episode(span_start="2026-01-01", span_end="2026-01-10"),),
        build_algorithms=lambda: (
            make_adherence_algorithm(),
            make_adherence_algorithm(
                algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY),
        ),
        build_occurrences=lambda: (
            make_occurrence("OC-1", "2026-01-01"),
            make_occurrence("OC-2", "2026-01-05"),
        ),
        build_observations=lambda: (make_observation("OBS-1"),),
        expected_set_size=3,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.POSITIVE, control_item=CONTROL_ADHERENCE,
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_item=CONTROL_ACCOUNTABILITY, cand=0, query=0),
        )))

    # -- 12. Accountability unit conversion (§6.2 rules 1/3, cases 50-51)

    cases.append(IPChallengeCase(
        number=50, name="accountability_unit_conversion_negative",
        category="accountability_conversion",
        description=(
            "accountability_proxy cross-unit: dispense 20 片 - return 10 片 "
            "= 50 mg under 1 片=5 mg == recorded 50 mg -> converted "
            "negative"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY,
                canonical_unit="mg", conversions=(("片", "mg", "5"),)),),
        build_dispenses=lambda: (
            make_dispense_record("DISP#1", amount="20", unit="片"),),
        build_returns=lambda: (
            make_return_record("RET#1", amount="10", unit="片"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="50", unit="mg"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NEGATIVE, control_item=CONTROL_ACCOUNTABILITY),
        )))

    cases.append(IPChallengeCase(
        number=51, name="accountability_unit_no_conversion_not_evaluable",
        category="accountability_conversion",
        description=(
            "same cross-unit inputs without any versioned conversion rule "
            "-> fail closed to not_evaluable with no candidate/Query"),
        build_episodes=lambda: (make_episode(),),
        build_algorithms=lambda: (
            make_adherence_algorithm(
                algorithm_id="ACC-01", metric=METRIC_ACCOUNTABILITY_PROXY,
                canonical_unit="mg"),),
        build_dispenses=lambda: (
            make_dispense_record("DISP#1", amount="20", unit="片"),),
        build_returns=lambda: (
            make_return_record("RET#1", amount="10", unit="片"),),
        build_observations=lambda: (
            make_observation("OBS-1", algorithm_id="ACC-01",
                             numerator="50", unit="mg"),),
        expected_set_size=2,
        expected_units=(
            _role_negative(),
            _ev(L1Disposition.NOT_EVALUABLE,
                control_item=CONTROL_ACCOUNTABILITY, cand=0, query=0),
        )))

    return IPChallengeMatrix(cases=tuple(cases))


# ---------------------------------------------------------------------------
# Ledger + lifecycle harness
# ---------------------------------------------------------------------------

def make_unit_evaluation(
    unit_result: IPUnitResult,
    *,
    snapshot_id: str = SNAPSHOT_ID,
    rule_lineage: str = RULE_LINEAGE,
    l0_status: str = "covered",
) -> UnitEvaluation:
    """Build a :class:`UnitEvaluation` from a D03 unit result with
    caller-supplied L0/provenance."""
    return unit_result.to_unit_evaluation(
        l0_status=l0_status,
        provenance_snapshot_id=snapshot_id,
        provenance_rule_lineage=rule_lineage)


def make_closed_ip_ledger(
    unit_results: Sequence[IPUnitResult],
    *,
    snapshot_id: str = SNAPSHOT_ID,
    rule_lineage: str = RULE_LINEAGE,
    domain_id: str = DOMAIN_ID,
    run_id: str = RUN_ID,
) -> CoverageLedger:
    """Build a *closed* R4 :class:`CoverageLedger` whose expected unit ids
    exactly equal the supplied unit results' unit ids.

    Each unit result is converted to a :class:`UnitEvaluation` with the
    given provenance snapshot/rule lineage.  The ledger is closed so
    ``is_domain_complete`` is meaningful.
    """
    unit_ids = [ur.unit_id for ur in unit_results]
    eset = ExpectedSet(
        expected_set_hash_value=expected_set_hash(unit_ids),
        unit_ids=tuple(unit_ids),
        domain_id=domain_id, run_id=run_id,
        expected_count=len(unit_ids))
    ledger = CoverageLedger(expected_set=eset)
    for ur in unit_results:
        ue = make_unit_evaluation(
            ur, snapshot_id=snapshot_id, rule_lineage=rule_lineage)
        ledger.assign(ue)
    ledger.close()
    return ledger


def attach_risk_ref(
    unit_result: IPUnitResult,
    *,
    risk_instance_id: str,
    risk_identity_id: str,
    risk_state: str = "established",
) -> IPUnitResult:
    """Return a copy of ``unit_result`` with a historical risk-instance
    ref attached, so a NEGATIVE N+1 unit explicitly links the prior risk
    (frozen D03 §10 exact linked-negative close)."""
    from .contracts import RiskInstanceRef
    ref = RiskInstanceRef(
        risk_instance_id=risk_instance_id,
        risk_identity_id=risk_identity_id,
        risk_state=risk_state)
    return _replace(
        unit_result,
        risk_instance_refs=unit_result.risk_instance_refs + (ref,))


def make_acceptance_service(local_user: str = "test") -> AcceptanceService:
    """A fresh real :class:`AcceptanceService` for synthetic snapshots."""
    return AcceptanceService(local_user=local_user)


def _make_accepted_snapshot(
    service: AcceptanceService,
    *,
    pid: str, rid: str, sid: str,
    rows: Optional[List[Dict[str, Any]]] = None,
    eligible: bool = True,
) -> Any:
    """Build a synthetic accepted snapshot via public R2 APIs only."""
    _rows = rows if rows is not None else [{"subject": "S001", "ip": "drugX"}]
    source = SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="v1", source_bytes=b"synthetic-d03")
    snap = ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version=f"cutoff-{sid}", rows=_rows)
    algo = IdentityAlgorithm(
        algorithm_id="alg-d03-1", name="record-id", version="1")
    mapping = MappingDefinition(
        mapping_id="m-d03-1", project_id=pid, source_revision_id=rid,
        identity_algorithm_id="alg-d03-1", source_field="EXTRT",
        canonical_field="ip_term", version="1", confidence=1.0,
        is_critical=True)
    result = MappingResult.from_verified(
        result_id="mr-d03-1", project_id=pid, snapshot=snap,
        mapping=mapping, identity_algorithm=algo, record_count=len(_rows))
    subjects = [r.get("subject", "S001") for r in _rows]
    rec_ids = [make_record_identity(pid, algo, {"subject": s}) for s in subjects]
    resolution = IdentityResolution(algorithm=algo, resolved=tuple(rec_ids))
    binding = SnapshotBinding(
        project_id=pid, snapshot=snap, source=source,
        identity_algorithm=algo, mapping_definitions=(mapping,),
        mapping_results=(result,), identity_resolution=resolution)
    actor = ACCEPTED_BY_SYSTEM_POLICY
    service.register(binding, actor)
    service.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                    evidence=service.evidence(
                        sid, actor, structural_validation_complete=True))
    service.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                    evidence=service.evidence(sid, actor))
    service.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                    evidence=service.evidence(sid, actor, approved_scope=True))
    if eligible:
        service.advance(sid, SnapshotAcceptanceState.BASELINE_ELIGIBLE, actor,
                        evidence=service.evidence(
                            sid, actor, source_coverage_complete=True,
                            approved_scope=True))
    return snap


def make_baseline_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str = SNAPSHOT_ID,
    revision_id: str = SOURCE_REV_ID,
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a baseline-eligible full snapshot and return its id."""
    if rows is None:
        rows = [{"subject": "S001", "ip": "drugX"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_subsequent_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str,
    revision_id: str,
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a *subsequent* baseline-eligible full snapshot for close."""
    if rows is None:
        rows = [{"subject": "S001", "ip": "drugX"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_lifecycle(local_user: str = "test") -> RiskLifecycle:
    return RiskLifecycle(local_user=local_user)


# ---------------------------------------------------------------------------
# N-to-N+1 deterministic replay harness
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NToN1Replay:
    """Result of one N-to-N+1 deterministic replay.

    Captures the N positive unit/candidate/identity, the N+1 unit (with
    the historical risk link attached for the linked-negative path), the
    :class:`ReconcileResult` and the post-replay lifecycle state.
    """

    n_unit: IPUnitResult
    n_candidate_id: str
    n_identity_id: str
    n_instance_id: str
    n1_unit: IPUnitResult
    established_instance: Any
    reconcile: Any
    lifecycle: RiskLifecycle

    @property
    def closed(self) -> bool:
        return self.reconcile.closed != ()


def run_n_to_n1_replay(
    *,
    case: IPChallengeCase,
    service: AcceptanceService,
    lifecycle: RiskLifecycle,
    adapter: Any,
    n_snapshot_id: str = "snap-d03-N",
    n1_snapshot_id: str = "snap-d03-N1",
    rules_override_n1: Optional[Sequence[ProtocolExposureRule]] = None,
    force_negative_n1: bool = True,
) -> NToN1Replay:
    """Run a deterministic N->N+1 replay for one challenge case.

    1. Evaluate the case at snapshot N (baseline-eligible).
    2. Promote the single positive unit through the adapter, establishing
       exactly one risk.
    3. Re-evaluate the *same* synthetic inputs at snapshot N+1.  By
       default (``force_negative_n1=True``) every N+1 unit is forced to
       NEGATIVE and the unit carrying the N positive's control token is
       given the exact historical risk-instance link (exact
       linked-negative, §10), so a low/medium risk machine-closes and the
       historical record is preserved.
    4. Build a closed, complete CoverageLedger over the N+1 units and
       call ``reconcile_n_to_n1``.

    Set ``force_negative_n1=False`` with ``rules_override_n1`` for the
    lineage-change path: the same stable event re-evaluates POSITIVE under
    a changed rule version/lineage; the reconcile then supersedes the risk
    rather than closing it (§10: ``superseded``, never
    ``resolved_by_data``).
    """
    # -- N evaluation ----------------------------------------------------
    exp_n, results_n = _evaluate_case_at(case, snapshot_id=n_snapshot_id)
    positive_n = _pick_positive(results_n)
    if positive_n is None:
        raise ValueError(
            f"case {case.number} ({case.name}) produced no positive N unit; "
            f"cannot run N->N+1 replay")
    outcome = adapter.promote_unit_result(positive_n)
    if not outcome.established_risk_ids:
        raise ValueError(
            f"case {case.number} N promotion established no risk")
    instance_id, identity_id = outcome.established_risk_ids[0]
    established = lifecycle.get(instance_id)

    # -- N+1 evaluation --------------------------------------------------
    _, results_n1_raw = _evaluate_case_at(
        case, snapshot_id=n1_snapshot_id,
        rules_override=rules_override_n1)
    if force_negative_n1:
        n1_results, n1_unit, found = _link_negative_n1(
            results_n1_raw, positive_n, established)
        if not found:
            raise ValueError(
                f"case {case.number} produced no corresponding N+1 "
                f"negative unit")
    else:
        n1_unit = _pick_positive(results_n1_raw)
        if n1_unit is None:
            raise ValueError(
                f"case {case.number} produced no positive N+1 unit for "
                f"the supersede path")
        n1_results = [
            r if r.unit_id == n1_unit.unit_id else _force_negative(r)
            for r in results_n1_raw]

    ledger = make_closed_ip_ledger(
        n1_results, snapshot_id=n1_snapshot_id)

    reconcile = adapter.reconcile_n_to_n1(
        previous_instances=[established],
        next_unit_results=n1_results,
        coverage_snapshot_id=n1_snapshot_id,
        coverage_ledger=ledger)

    return NToN1Replay(
        n_unit=positive_n,
        n_candidate_id=(positive_n.r2_candidates[0].candidate_id
                        if positive_n.r2_candidates else ""),
        n_identity_id=identity_id,
        n_instance_id=instance_id,
        n1_unit=n1_unit,
        established_instance=established,
        reconcile=reconcile,
        lifecycle=lifecycle)


def _evaluate_case_at(
    case: IPChallengeCase,
    *,
    snapshot_id: str,
    rules_override: Optional[Sequence[ProtocolExposureRule]] = None,
) -> Tuple[IPExpectedSetExpansion, List[IPUnitResult]]:
    """Re-evaluate a case's synthetic inputs at a given snapshot, with an
    optional rule-version override (the supersede path)."""
    return case.build(snapshot_id=snapshot_id, rules=rules_override)


def _pick_positive(
    results: Sequence[IPUnitResult],
) -> Optional[IPUnitResult]:
    for r in results:
        if r.l1_disposition == L1Disposition.POSITIVE and r.r2_candidates:
            return r
    return None


def _link_negative_n1(
    n1_results: Sequence[IPUnitResult],
    n_positive: IPUnitResult,
    established: Any,
) -> Tuple[List[IPUnitResult], IPUnitResult, bool]:
    """Force every N+1 unit to NEGATIVE (the corrected snapshot state) and
    attach the exact historical risk link to the unit that carried the N
    positive's control token.

    Matching: the N positive's candidate stores ``control_token``; we find
    the N+1 unit whose re-evaluated candidate carries the same token, or
    fall back to identical ``unit_id`` (identity-persistence path where
    the N+1 inputs equal the N inputs).
    """
    target_token = ""
    for cand in n_positive.r2_candidates:
        target_token = str(cand.detail.get("control_token", ""))
        if target_token:
            break
    linked_unit: Optional[IPUnitResult] = None
    forced: List[IPUnitResult] = []
    found = False
    for r in n1_results:
        cand_token = ""
        for cand in r.r2_candidates:
            cand_token = str(cand.detail.get("control_token", ""))
            break
        same_token = (target_token and cand_token
                      and cand_token == target_token)
        if (same_token or r.unit_id == n_positive.unit_id) and not found:
            forced.append(attach_risk_ref(
                _force_negative(r),
                risk_instance_id=established.risk_instance_id,
                risk_identity_id=established.risk_identity_id,
                risk_state=established.current_state))
            linked_unit = forced[-1]
            found = True
        else:
            forced.append(_force_negative(r))
    return forced, linked_unit, found


def _force_negative(unit: IPUnitResult) -> IPUnitResult:
    """Return a copy of ``unit`` forced to NEGATIVE with no candidates.

    Used only to model the linked-negative N+1 outcome for the replay
    harness: the N+1 snapshot has resolved the discrepancy, so the same
    control unit becomes a clean negative that explicitly links the prior
    risk.  The unit_id and identity dimensions are preserved so the ledger
    expected-set still matches.
    """
    return _replace(
        unit,
        l1_disposition=L1Disposition.NEGATIVE,
        r2_candidates=(),
        risk_candidate_refs=(),
        query_refs=(),
        positive_subtype="",
        audience_label="",
        not_evaluable_reason="",
        boundary_reason="",
        journey_markers=())
