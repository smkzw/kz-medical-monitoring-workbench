"""Cohesive D05 visit-schedule evaluation authority."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, replace
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple)

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate

from .contracts import (
    CrossDomainEvidenceRef,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)
from .coverage import (
    CoverageLedger,
    CoverageSummary,
    ExpectedSet,
    is_domain_complete,
)
from .visit_schedule import (
    ACTIVITY_ASSESSMENT,
    ACTIVITY_CONTACT,
    ACTIVITY_PROCEDURE,
    ACTIVITY_SAMPLE,
    ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
    ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE,
    ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
    ACTIVITY_ASSIGNMENT_UNIQUE,
    ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED,
    ANCHOR_ROLE_OTHER,
    ANCHOR_ROLE_VISIT_SCHEDULE,
    APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
    APPLICABILITY_UNIQUE_ACTIVE,
    ASSIGNMENT_SCOPE_MULTI,
    ActualActivityConsumptionLedger,
    ActualActivityRecord,
    ActualEncounterBundle,
    ActualEncounterRecord,
    ActualRecordScopeDecision,
    ClinicalEventCutoff,
    D05_DOMAIN,
    D05_RULE_LINEAGE_DEFAULT,
    D05_UNIT_ALGO_VERSION,
    ENCOUNTER_HOSPITAL,
    ENCOUNTER_HOME,
    ENCOUNTER_ONSITE,
    ENCOUNTER_REMOTE,
    ENCOUNTER_UNKNOWN,
    ENCOUNTER_UNSCHEDULED,
    EvaluationMaturityRule,
    GATE_ANCHOR,
    GATE_APPLICABILITY,
    GATE_CUTOFF_SCOPE,
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_OPEN,
    GATE_ROUTING,
    INTERPRET_SCOPE_REPEAT,
    INTERPRET_SCOPE_WINDOW,
    MODALITY_HOME,
    MODALITY_HOSPITAL,
    MODALITY_ONSITE,
    MODALITY_REMOTE,
    OWNER_D05,
    OWNER_UNRESOLVED,
    PlannedActivityDefinition,
    PlannedVisitDefinition,
    PRECISION_DAY,
    PRECISION_MONTH,
    PRECISION_YEAR,
    PREDICATE_FALSE,
    PREDICATE_TRUE,
    PRODUCER_RELATION_TYPES,
    REASON_ANCHOR_MISSING,
    REASON_COVERAGE_INCOMPLETE,
    REASON_INTERVAL_STRADDLES,
    REASON_MAPPING_MISSING,
    REASON_MATURITY_RULE_MISSING,
    REASON_MULTIPLE_FEASIBLE,
    REASON_OTHER,
    REASON_PRECISION_INSUFFICIENT,
    REASON_ROUTING_COMPETITION,
    REASON_SCHEDULE_MISSING,
    REASON_TIME_ROLE_CONFLICT,
    REASON_TIME_ROLE_MISSING,
    REASON_TIMEZONE_MISSING,
    REASON_VERSION_MISSING,
    REASON_CODES,
    RELATION_FIXED_REFERENCE,
    RELATION_PRIOR_ACTUAL_VISIT,
    RELATION_TYPES,
    REVERSE_COVERAGE_CLOSED,
    REVERSE_COVERAGE_OPEN,
    SCOPE_BOUNDARY,
    SCOPE_IN_SCOPE,
    SCOPE_NOT_EVALUABLE,
    SCOPE_OUT_OF_CUTOFF,
    ScheduleEvaluationUnit,
    ScheduleGate,
    ScheduleInterpretationLedger,
    ScheduleSliceError,
    SnapshotAsOf,
    SUB_DAY_PRECISIONS,
    TypedScheduleAnchorRef,
    UNIT_ACTIVITY_OCCURRENCE,
    UNIT_ACTIVITY_TIMING,
    UNIT_ACTUAL_ASSIGNMENT,
    UNIT_SCHEDULE_CONSISTENCY,
    UNIT_VISIT_OCCURRENCE,
    UNIT_VISIT_ORDER,
    UNIT_VISIT_TIMING,
    VISIT_ASSIGNMENT_MULTI_FEASIBLE,
    VISIT_ASSIGNMENT_NOT_EVALUABLE,
    VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
    VISIT_ASSIGNMENT_UNIQUE,
    VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED,
    VISIT_SCHEDULED,
    ActivityAssignmentDecision,
    VisitAssignmentDecision,
    VisitCoverageGapNotice,
    VisitScheduleApplicabilityDecision,
    VisitWindowRule,
    bind_typed_schedule_anchor,
    resolve_actual_record_scope,
    schedule_evaluation_window_id,
    validate_gate_run_accounting,
)

from .visit_schedule_eval_contracts import *
from .visit_schedule_eval_contracts import (
    _PRIORITY_UNKNOWN, _bundle_interval_relation_to_day, _day_date,
    _day_interval_of,
)
from .visit_schedule_assignments import *
from .visit_schedule_expected import *
from .visit_schedule_expected import _predecessor_visit, _visit_key_of_activity
from .visit_schedule_results import *
from .visit_schedule_output_helpers import *
from .visit_schedule_output_helpers import (
    _anchor_day_of, _boundary_candidate_input, _bundle_end, _bundle_start,
    _candidate_input, _evidence_items, _missing_subtype, _mistimed_subtype,
    _not_applicable_result, _not_evaluable_result, _priority_or_unknown,
    _resolve_assignment_verdict, _result, _role_for_kind,
    _source_refs_for_activity, _source_refs_for_activity_id,
    _source_refs_for_bundle, _stable_key_of_activity,
    _timing_compare_instants,
)

def _link_unit(
    unit: ScheduleEvaluationUnit,
    visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    ledgers: Sequence[ActualActivityConsumptionLedger],
) -> ScheduleEvaluationUnit:
    """Attach the resolved assignment ids to a unit (unit_id unchanged)."""
    visit_assignment_id = ""
    activity_assignment_id = ""
    actual_bundle_id = ""
    actual_activity_id = ""
    for decision in visit_assignments:
        if decision.selected_planned_visit_id == unit.planned_visit_key \
                and unit.planned_visit_key \
                and decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            visit_assignment_id = decision.assignment_id
            actual_bundle_id = decision.actual_bundle_id
            break
    for decision in activity_assignments:
        if unit.planned_activity_key in decision.selected_planned_activity_ids:
            activity_assignment_id = decision.assignment_id
            actual_activity_id = decision.actual_activity_id
            break
    return replace(
        unit,
        visit_assignment_id=visit_assignment_id,
        activity_assignment_id=activity_assignment_id,
        actual_bundle_id=actual_bundle_id,
        actual_activity_id=actual_activity_id,
        lineage_hash="")


def _evaluate_unit(
    *, unit: ScheduleEvaluationUnit, expansion: ExpectedSetExpansion,
    visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    ledgers: Sequence[ActualActivityConsumptionLedger],
    reverse_index: Sequence[Tuple[str, str]],
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
    encounters: Sequence[ActualEncounterRecord],
    activities: Sequence[ActualActivityRecord],
    bundles: Sequence[ActualEncounterBundle],
    scope_decisions: Sequence[ActualRecordScopeDecision],
    applicability_decision: VisitScheduleApplicabilityDecision,
    maturity_rules: Mapping[str, EvaluationMaturityRule],
    activity_window_rules: Mapping[str, VisitWindowRule],
    obligation_applicability: Mapping[str, ObligationApplicability],
    source_coverage: Mapping[str, bool],
    cutoff_day: Optional[datetime.date],
    priority_policies: Mapping[str, D05PriorityPolicy],
    assignment_priority_policy: Optional[D05PriorityPolicy],
    enrollment_context: D05EnrollmentContext,
    record_locators: Mapping[str, SourceLocator],
    plan_locators: Sequence[SourceLocator],
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    """Evaluate one unit to an L1 disposition and build the candidate
    input for positive/boundary units."""
    kind = unit.unit_kind
    if kind == UNIT_VISIT_OCCURRENCE:
        return _eval_visit_occurrence(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_VISIT_TIMING:
        return _eval_visit_timing(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_VISIT_ORDER:
        return _eval_visit_order(
            unit=unit, visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind in (UNIT_ACTIVITY_OCCURRENCE, UNIT_ACTIVITY_TIMING):
        return _eval_activity(
            unit=unit, kind=kind, expansion=expansion,
            activity_assignments=activity_assignments,
            planned_visits=planned_visits,
            planned_activities=planned_activities,
            activities=activities,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            activity_window_rules=activity_window_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_ACTUAL_ASSIGNMENT:
        return _eval_actual_assignment(
            unit=unit, visit_assignments=visit_assignments,
            activity_assignments=activity_assignments,
            bundles=bundles, activities=activities,
            source_coverage=source_coverage,
            assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_SCHEDULE_CONSISTENCY:
        return _eval_schedule_consistency(
            unit=unit, assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            plan_locators=plan_locators)
    raise VisitScheduleEvaluatorError(f"unsupported unit kind {kind!r}")


def _find_visit(unit: ScheduleEvaluationUnit,
                planned_visits: Sequence[PlannedVisitDefinition],
                ) -> Optional[PlannedVisitDefinition]:
    for visit in planned_visits:
        if visit.planned_visit_key == unit.planned_visit_key:
            return visit
    return None


def _find_activity(unit: ScheduleEvaluationUnit,
                   planned_activities: Sequence[PlannedActivityDefinition],
                   ) -> Optional[PlannedActivityDefinition]:
    for activity in planned_activities:
        if activity.planned_activity_key == unit.planned_activity_key:
            return activity
    return None


def _unique_bundle_for_visit(
    visit_key: str, visit_assignments: Sequence[VisitAssignmentDecision],
    bundles: Sequence[ActualEncounterBundle],
) -> Optional[ActualEncounterBundle]:
    for decision in visit_assignments:
        if decision.selected_planned_visit_id == visit_key \
                and decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            for bundle in bundles:
                if bundle.bundle_id == decision.actual_bundle_id:
                    return bundle
    return None


def _assignment_for_bundle(
    bundle_id: str, visit_assignments: Sequence[VisitAssignmentDecision],
) -> Optional[VisitAssignmentDecision]:
    for decision in visit_assignments:
        if decision.actual_bundle_id == bundle_id:
            return decision
    return None
def _policy_verdict(
    key: str, priority_policies: Mapping[str, D05PriorityPolicy],
    kind: str,
) -> Optional[D05PriorityVerdict]:
    policy = priority_policies.get(key)
    if policy is None:
        if kind == L1Disposition.POSITIVE:
            raise VisitScheduleEvaluatorError(
                f"positive unit for obligation {key!r} requires a frozen "
                f"D05PriorityPolicy (priority inputs must be closed "
                f"enums, §9.1)")
        return None
    return resolve_d05_priority(policy)


def _first_locator(result: D05UnitResult) -> Optional[SourceLocator]:
    for item in result.evidence:
        return item.locator
    for ref in result.source_record_refs:
        return ref.locator
    return None


def _eval_visit_occurrence(
    *, unit, expansion, visit_assignments, planned_visits, bundles,
    applicability_decision, maturity_rules, obligation_applicability,
    source_coverage, priority_policies, enrollment_context, record_locators,
    plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    key = unit.planned_visit_key
    applicability = obligation_applicability.get(
        key, ObligationApplicability(obligation_key=key, applicable=True))
    if applicability.applicable is False:
        return _not_applicable_result(
            unit=unit, reason=applicability.reason_code,
            authority_locator_ids=applicability.authority_locator_ids,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if applicability.applicable is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("applicability",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if maturity_rules.get(UNIT_VISIT_OCCURRENCE) is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_MATURITY_RULE_MISSING,
            gap_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    maturity_rule = maturity_rules[UNIT_VISIT_OCCURRENCE]
    if maturity_day_for(maturity_rule=maturity_rule,
                        anchor_day=_anchor_day_of(unit, expansion),
                        window_rule=visit.window_rule) is None:
        # Maturity cannot be computed (missing anchor / unfrozen window):
        # the obligation stays not_evaluable, never a false missing-positive
        # (§4.2, challenge 113).
        return _not_evaluable_result(
            unit=unit, reason=REASON_MATURITY_RULE_MISSING,
            gap_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not source_coverage.get("encounter", True):
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("encounter",), l0_status=L0CoverageStatus.MISSING,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    bundle = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=([bundle.member_encounter_ids[0]] if bundle else []),
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_bundle(bundle, record_locators)
    if bundle is not None:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), None
    # A scope-gated record (boundary/not_evaluable scope) means "complete
    # absence" is not established: never a false visit_missing positive
    # (§4.2, §8.3; the cutoff-scope gate already blocks completeness).
    scope_gated = any(
        d.scope_status in (SCOPE_BOUNDARY, SCOPE_NOT_EVALUABLE)
        for d in expansion.scope_decisions)
    if scope_gated:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("encounter",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
    assert verdict is not None
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_VISIT_MISSING,
        audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_MISSING],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day=_anchor_day_of(unit, expansion),
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_VISIT_MISSING,
            audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_MISSING],
            priority=verdict.priority,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="missing visit with complete coverage")


def _eval_visit_timing(
    *, unit, expansion, visit_assignments, planned_visits, bundles,
    source_coverage, priority_policies, enrollment_context, record_locators,
    plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    bundle = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    if bundle is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    anchor_day = _anchor_day_of(unit, expansion)
    bounds = window_bounds(window_rule=visit.window_rule, anchor_day=anchor_day)
    lo_day, hi_day, complete = _bundle_interval_relation_to_day(bundle)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=([bundle.member_encounter_ids[0]] if bundle else []),
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_bundle(bundle, record_locators)
    # Sub-day window precision: instant-level compare (challenges 26/27/66).
    if visit.window_rule.date_precision in SUB_DAY_PRECISIONS:
        record_precision = bundle.date_precision
        if record_precision == PRECISION_DAY:
            # Hour-level window with complete day-only source -> boundary
            # (challenge 66: the source is complete but cannot discriminate).
            verdict = _policy_verdict(unit.planned_visit_key,
                                      priority_policies, L1Disposition.BOUNDARY)
            boundary_priority = _priority_or_unknown(verdict)
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="小时级窗口但来源仅按日采集且覆盖完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=visit.anchor_rule.anchor_kind,
                    window=visit.window_rule, anchor_day=anchor_day,
                    match_reason="sub-day window with day-only source")
        if record_precision not in SUB_DAY_PRECISIONS:
            return _not_evaluable_result(
                unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if not bundle.timezone.strip():
            return _not_evaluable_result(
                unit=unit, reason=REASON_TIMEZONE_MISSING,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        verdict, reason = _timing_compare_instants(
            window_rule=visit.window_rule, anchor_day=anchor_day,
            start=bundle.derived_start, end=bundle.derived_end,
            timezone=bundle.timezone)
        if verdict == L1Disposition.NEGATIVE:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    unit.planned_visit_key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), None
        if verdict == L1Disposition.POSITIVE:
            return _timing_positive(
                unit=unit, visit=visit, bundle=bundle, bounds=bounds,
                priority_policies=priority_policies, evidence=evidence,
                source_refs=source_refs, expansion=expansion,
                enrollment_context=enrollment_context)
        if verdict == L1Disposition.BOUNDARY:
            policy_verdict = _policy_verdict(unit.planned_visit_key,
                                             priority_policies,
                                             L1Disposition.BOUNDARY)
            boundary_priority = _priority_or_unknown(policy_verdict)
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="跨午夜区间边界无法在瞬时精度确定",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=visit.anchor_rule.anchor_kind,
                    window=visit.window_rule, anchor_day=anchor_day,
                    match_reason="sub-day interval straddles the window")
        return _not_evaluable_result(
            unit=unit, reason=reason or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not bounds.determinable:
        return _not_evaluable_result(
            unit=unit, reason=bounds.reason_code or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if lo_day is None or hi_day is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_bound = _day_date(bounds.lo_day)
    hi_bound = _day_date(bounds.hi_day)
    if lo_bound is None or hi_bound is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not complete:
        if hi_day < lo_bound or lo_day > hi_bound:
            return _timing_positive(
                unit=unit, visit=visit, bundle=bundle, bounds=bounds,
                priority_policies=priority_policies, evidence=evidence,
                source_refs=source_refs, expansion=expansion,
                enrollment_context=enrollment_context)
        if lo_day >= lo_bound and hi_day <= hi_bound:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    unit.planned_visit_key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day=_anchor_day_of(unit, expansion),
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), None
        verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                                  L1Disposition.BOUNDARY)
        boundary_priority = _priority_or_unknown(verdict)
        return _result(
            unit=unit, disposition=L1Disposition.BOUNDARY,
            boundary_reason="部分日期区间跨越窗口边界且来源完整",
            priority=boundary_priority,
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), _boundary_candidate_input(
                unit=unit, audience_label="访视时间边界待核实",
                priority=boundary_priority,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day=_anchor_day_of(unit, expansion),
                match_reason="partial date interval straddles the window")
    if lo_day >= lo_bound and hi_day <= hi_bound:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                unit.planned_visit_key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), None
    return _timing_positive(
        unit=unit, visit=visit, bundle=bundle, bounds=bounds,
        priority_policies=priority_policies, evidence=evidence,
        source_refs=source_refs, expansion=expansion,
        enrollment_context=enrollment_context)


def _timing_positive(
    *, unit, visit, bundle, bounds, priority_policies, evidence, source_refs,
    expansion, enrollment_context,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                              L1Disposition.POSITIVE)
    assert verdict is not None
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_VISIT_OVERWINDOW,
        audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_OVERWINDOW],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day=_anchor_day_of(unit, expansion),
        actual_start=_bundle_start(bundle),
        actual_end=_bundle_end(bundle),
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_VISIT_OVERWINDOW,
            audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_OVERWINDOW],
            priority=verdict.priority,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="actual visit outside the allowed window")


def _eval_visit_order(
    *, unit, visit_assignments, planned_visits, bundles, source_coverage,
    priority_policies, enrollment_context, record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    predecessor = _predecessor_visit(visit, planned_visits)
    if predecessor is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    current = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    prior = _unique_bundle_for_visit(
        predecessor.planned_visit_key, visit_assignments, bundles)
    if current is None or prior is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    current_lo, _, current_complete = _bundle_interval_relation_to_day(current)
    prior_lo, _, prior_complete = _bundle_interval_relation_to_day(prior)
    if not current_complete or not prior_complete \
            or current_lo is None or prior_lo is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=[current.member_encounter_ids[0],
                    prior.member_encounter_ids[0]],
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = tuple(
        _source_refs_for_bundle(current, record_locators)
        + _source_refs_for_bundle(prior, record_locators))
    if current_lo < prior_lo:
        verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                                  L1Disposition.POSITIVE)
        assert verdict is not None
        return _result(
            unit=unit, disposition=L1Disposition.POSITIVE,
            subtype=POSITIVE_VISIT_ORDER_INCONSISTENT,
            audience_label=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_VISIT_ORDER_INCONSISTENT],
            priority=verdict.priority,
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day="",
            actual_start=_bundle_start(current),
            actual_end=_bundle_end(current),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            priority_reason_codes=verdict.reason_codes,
            enrollment_context=enrollment_context), _candidate_input(
                unit=unit, subtype=POSITIVE_VISIT_ORDER_INCONSISTENT,
                audience_label=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_VISIT_ORDER_INCONSISTENT],
                priority=verdict.priority,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day="",
                rights_or_safety_critical=verdict.rights_or_safety_critical,
                machine_close_forbidden=verdict.machine_close_forbidden,
                match_reason="actual visit order contradicts planned_order")
    return _result(
        unit=unit, disposition=L1Disposition.NEGATIVE,
        priority=_priority_or_unknown(_policy_verdict(
            unit.planned_visit_key, priority_policies, "negative")),
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day="",
        actual_start=_bundle_start(current),
        actual_end=_bundle_end(current),
        enrollment_context=enrollment_context), None


def _eval_activity(
    *, unit, kind, expansion, activity_assignments,
    planned_visits, planned_activities, activities,
    applicability_decision, maturity_rules, activity_window_rules,
    obligation_applicability, source_coverage, priority_policies,
    enrollment_context, record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    activity_def = _find_activity(unit, planned_activities)
    assert activity_def is not None
    key = unit.planned_activity_key
    applicability = obligation_applicability.get(
        key, ObligationApplicability(obligation_key=key, applicable=True))
    if applicability.applicable is False:
        return _not_applicable_result(
            unit=unit, reason=applicability.reason_code,
            authority_locator_ids=applicability.authority_locator_ids,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if applicability.applicable is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("applicability",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    assigned: List[ActualActivityRecord] = []
    for decision in activity_assignments:
        if key in decision.selected_planned_activity_ids:
            for actual in activities:
                if actual.actual_activity_id == decision.actual_activity_id:
                    assigned.append(actual)
    role = _role_for_kind(activity_def.activity_kind)
    role_covered = source_coverage.get(role, True)
    visit_key = _visit_key_of_activity(activity_def, planned_visits) or ""
    anchor_day = ""
    for item in expansion.anchor_day_by_visit_key:
        if item[0] == visit_key:
            anchor_day = item[1]
            break
    window_rule = activity_window_rules.get(key)
    if kind == UNIT_ACTIVITY_OCCURRENCE:
        maturity_rule = maturity_rules.get(UNIT_ACTIVITY_OCCURRENCE)
        if maturity_rule is not None and maturity_day_for(
                maturity_rule=maturity_rule, anchor_day=anchor_day,
                window_rule=window_rule) is None:
            return _not_evaluable_result(
                unit=unit, reason=REASON_MATURITY_RULE_MISSING,
                gap_roles=("window",),
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if not role_covered:
            return _not_evaluable_result(
                unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
                gap_roles=(role,), l0_status=L0CoverageStatus.MISSING,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if assigned:
            actual = assigned[0]
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=_evidence_items(
                    record_locators=record_locators,
                    plan_locators=plan_locators,
                    record_ids=[actual.actual_activity_id],
                    plan_locator_ids=activity_def.source_locator_ids,
                    polarity=L1bEvidencePolarity.SUPPORTING),
                source_refs=_source_refs_for_activity(actual, record_locators),
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        subtype = _missing_subtype(activity_def.activity_kind)
        verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
        assert verdict is not None
        return _result(
            unit=unit, disposition=L1Disposition.POSITIVE,
            subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=verdict.priority,
            evidence=_evidence_items(
                record_locators=record_locators,
                plan_locators=plan_locators, record_ids=(),
                plan_locator_ids=activity_def.source_locator_ids,
                polarity=L1bEvidencePolarity.SUPPORTING),
            source_refs=(),
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            priority_reason_codes=verdict.reason_codes,
            enrollment_context=enrollment_context), _candidate_input(
                unit=unit, subtype=subtype,
                audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                priority=verdict.priority,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                rights_or_safety_critical=verdict.rights_or_safety_critical,
                machine_close_forbidden=verdict.machine_close_forbidden,
                match_reason="required activity missing with complete coverage")
    # Activity timing.
    if not assigned:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=(role,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    actual = assigned[0]
    bounds = window_bounds(window_rule=window_rule, anchor_day=anchor_day)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=[actual.actual_activity_id],
        plan_locator_ids=activity_def.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_activity(actual, record_locators)
    if window_rule is not None \
            and window_rule.date_precision in SUB_DAY_PRECISIONS:
        if actual.date_precision == PRECISION_DAY:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="小时级窗口但来源仅按日采集且覆盖完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="sub-day window with day-only source")
        if actual.date_precision not in SUB_DAY_PRECISIONS \
                or not actual.timezone.strip():
            return _not_evaluable_result(
                unit=unit, reason=REASON_TIMEZONE_MISSING,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        verdict, reason = _timing_compare_instants(
            window_rule=window_rule, anchor_day=anchor_day,
            start=actual.start, end=actual.end, timezone=actual.timezone)
        if verdict == L1Disposition.NEGATIVE:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        if verdict == L1Disposition.POSITIVE:
            verdict_policy = _policy_verdict(
                key, priority_policies, L1Disposition.POSITIVE)
            assert verdict_policy is not None
            subtype = _mistimed_subtype(activity_def.activity_kind)
            return _result(
                unit=unit, disposition=L1Disposition.POSITIVE,
                subtype=subtype,
                audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                priority=verdict_policy.priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                rights_or_safety_critical=verdict_policy.rights_or_safety_critical,
                machine_close_forbidden=verdict_policy.machine_close_forbidden,
                priority_reason_codes=verdict_policy.reason_codes,
                enrollment_context=enrollment_context), _candidate_input(
                    unit=unit, subtype=subtype,
                    audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                    priority=verdict_policy.priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    rights_or_safety_critical=verdict_policy.rights_or_safety_critical,
                    machine_close_forbidden=verdict_policy.machine_close_forbidden,
                    match_reason="required activity outside its independent window")
        if verdict == L1Disposition.BOUNDARY:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="跨午夜区间边界无法在瞬时精度确定",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="sub-day interval straddles the window")
        return _not_evaluable_result(
            unit=unit, reason=reason or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not bounds.determinable:
        return _not_evaluable_result(
            unit=unit, reason=bounds.reason_code or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_day, hi_day, complete = _day_interval_of(actual)
    if lo_day is None or hi_day is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=(role,),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_bound = _day_date(bounds.lo_day)
    hi_bound = _day_date(bounds.hi_day)
    if lo_bound is None or hi_bound is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not complete:
        # Partial-date interval: determinate only when fully in or out.
        if hi_day < lo_bound or lo_day > hi_bound:
            pass  # fall through to the mistimed positive below
        elif lo_day >= lo_bound and hi_day <= hi_bound:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        else:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="部分日期区间跨越窗口边界且来源完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="partial date interval straddles the window")
    if lo_day >= lo_bound and hi_day <= hi_bound:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            actual_start=actual.start, actual_end=actual.end,
            enrollment_context=enrollment_context), None
    verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
    assert verdict is not None
    subtype = _mistimed_subtype(activity_def.activity_kind)
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=subtype,
        audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=activity_def.applicability_expression or "",
        window=window_rule, anchor_day=anchor_day,
        actual_start=actual.start, actual_end=actual.end,
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=verdict.priority,
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="required activity outside its independent window")


def _eval_actual_assignment(
    *, unit, visit_assignments, activity_assignments, bundles, activities,
    source_coverage, assignment_priority_policy, enrollment_context,
    record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    """Actual-assignment unit for a problematic actual object (§5.1, §7.2)."""
    # Visit-level reverse check first.
    for bundle in bundles:
        if bundle.stable_actual_object_key != unit.stable_actual_object_key:
            continue
        decision = _assignment_for_bundle(bundle.bundle_id, visit_assignments)
        if decision is None:
            continue
        evidence = _evidence_items(
            record_locators=record_locators, plan_locators=plan_locators,
            record_ids=([bundle.member_encounter_ids[0]]
                        if bundle.member_encounter_ids else []),
            plan_locator_ids=(), polarity=L1bEvidencePolarity.SUPPORTING)
        source_refs = _source_refs_for_bundle(bundle, record_locators)
        if decision.decision_status == VISIT_ASSIGNMENT_MULTI_FEASIBLE:
            boundary_priority = _priority_or_unknown(
                _resolve_assignment_verdict(assignment_priority_policy))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="两个及以上计划访视均有完整可行依据",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视归属边界待核实",
                    priority=boundary_priority,
                    match_reason="multiple feasible planned visits")
        if decision.decision_status == VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT:
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        return _not_evaluable_result(
            unit=unit, reason=REASON_MAPPING_MISSING, gap_roles=("assignment",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    # Activity-level reverse check (mislabel / duplicate consumption).
    for decision in activity_assignments:
        if _stable_key_of_activity(decision.actual_activity_id, activities) \
                != unit.stable_actual_object_key:
            continue
        evidence = _evidence_items(
            record_locators=record_locators, plan_locators=plan_locators,
            record_ids=[decision.actual_activity_id],
            plan_locator_ids=(), polarity=L1bEvidencePolarity.SUPPORTING)
        source_refs = _source_refs_for_activity_id(
            decision.actual_activity_id, activities, record_locators)
        if decision.decision_status == ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION:
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_DUPLICATE,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        if decision.decision_status == ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE:
            boundary_priority = _priority_or_unknown(
                _resolve_assignment_verdict(assignment_priority_policy))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="活动归属存在多个可行解释",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="活动归属边界待核实",
                    priority=boundary_priority,
                    match_reason="multiple feasible planned activities")
        if decision.decision_status == ACTIVITY_ASSIGNMENT_NOT_EVALUABLE \
                and PRED_ACTIVITY_CLAIM in decision.evidence_predicate_ids:
            # Complete-evidence mislabel: positive under every feasible
            # interpretation (§5.1).
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("assignment",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    return _not_evaluable_result(
        unit=unit, reason=REASON_COVERAGE_INCOMPLETE, gap_roles=("assignment",),
        record_locators=record_locators, plan_locators=plan_locators,
        enrollment_context=enrollment_context), None


def _assignment_positive(
    *, unit, subtype, evidence, source_refs, policy, enrollment_context,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = policy and resolve_d05_priority(policy)
    priority = verdict.priority if verdict else _PRIORITY_UNKNOWN
    machine_close = verdict.machine_close_forbidden if verdict else False
    rights_safety = verdict.rights_or_safety_critical if verdict else False
    reason_codes = verdict.reason_codes if verdict else ()
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE, subtype=subtype,
        audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
        priority=priority, evidence=evidence, source_refs=source_refs,
        rights_or_safety_critical=rights_safety,
        machine_close_forbidden=machine_close,
        priority_reason_codes=reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=priority,
            rights_or_safety_critical=rights_safety,
            machine_close_forbidden=machine_close,
            match_reason="actual object mis-assigned or duplicate")


def _eval_schedule_consistency(
    *, unit, assignment_priority_policy, enrollment_context, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = assignment_priority_policy and resolve_d05_priority(
        assignment_priority_policy)
    priority = verdict.priority if verdict else _PRIORITY_UNKNOWN
    evidence = _evidence_items(
        record_locators={}, plan_locators=plan_locators,
        record_ids=(), plan_locator_ids=unit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_SCHEDULE_RULE_INCONSISTENT,
        audience_label=POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SCHEDULE_RULE_INCONSISTENT],
        priority=priority,
        evidence=evidence, source_refs=(),
        rights_or_safety_critical=(verdict.rights_or_safety_critical
                                   if verdict else False),
        machine_close_forbidden=(verdict.machine_close_forbidden
                                 if verdict else False),
        priority_reason_codes=verdict.reason_codes if verdict else (),
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_SCHEDULE_RULE_INCONSISTENT,
            audience_label=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SCHEDULE_RULE_INCONSISTENT],
            priority=priority,
            rights_or_safety_critical=(verdict.rights_or_safety_critical
                                       if verdict else False),
            machine_close_forbidden=(verdict.machine_close_forbidden
                                     if verdict else False),
            match_reason="plan rules cannot be simultaneously satisfied")
