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
    _PRIORITY_UNKNOWN, _day_date, _day_instant_interval, _offset_days,
)
from .visit_schedule_assignments import *
from .visit_schedule_expected import *
from .visit_schedule_results import *

def _evidence_items(
    *, record_locators: Mapping[str, SourceLocator],
    plan_locators: Sequence[SourceLocator],
    record_ids: Sequence[str], plan_locator_ids: Sequence[str],
    polarity: str,
) -> Tuple[EvidenceItem, ...]:
    items: List[EvidenceItem] = []
    seen: Set[str] = set()
    for record_id in record_ids:
        locator = record_locators.get(record_id)
        if locator is None:
            continue
        key = locator.locator_id()
        if key in seen:
            continue
        seen.add(key)
        items.append(EvidenceItem(
            evidence_id="d05-ev-" + content_hash({
                "locator": key, "polarity": polarity,
                "role": locator.table_semantic}),
            polarity=polarity, locator=locator,
            evidence_role=locator.table_semantic,
            rule_lineage=D05_RULE_LINEAGE_DEFAULT))
    for locator in plan_locators:
        key = locator.locator_id()
        if key in seen:
            continue
        if plan_locator_ids and key not in plan_locator_ids:
            continue
        seen.add(key)
        items.append(EvidenceItem(
            evidence_id="d05-ev-" + content_hash({
                "locator": key, "polarity": polarity, "role": "plan"}),
            polarity=polarity, locator=locator,
            evidence_role="plan", rule_lineage=D05_RULE_LINEAGE_DEFAULT))
    return tuple(items)
def _result(
    *, unit, disposition, priority, evidence, source_refs,
    enrollment_context, subtype="", audience_label="",
    boundary_reason="", not_evaluable_reason="", l0_status=None,
    anchor_kind="", window=None, anchor_day="",
    actual_start="", actual_end="",
    rights_or_safety_critical=False, machine_close_forbidden=False,
    priority_reason_codes=(),
) -> D05UnitResult:
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return D05UnitResult(
        unit_id=unit.unit_id, subject_ref=unit.subject_ref,
        site_ref=unit.site_ref, unit_kind=unit.unit_kind,
        planned_visit_key=unit.planned_visit_key,
        planned_activity_key=unit.planned_activity_key,
        stable_actual_object_key=unit.stable_actual_object_key,
        l1_disposition=disposition, monitoring_priority=priority,
        l0_status=l0_status or L0CoverageStatus.COVERED,
        positive_subtype=subtype, audience_label=audience_label,
        query_context=enrollment_context.query_context,
        not_evaluable_reason=not_evaluable_reason,
        boundary_reason=boundary_reason,
        evaluation_window_id=unit.evaluation_window_id,
        rule_id=unit.rule_id, rule_version=unit.rule_version,
        anchor_kind=anchor_kind,
        window_start=window_start, window_end=window_end,
        precision=precision,
        actual_start=actual_start, actual_end=actual_end,
        evidence=evidence, source_record_refs=source_refs,
        classifier=unit.classifier, stable_core=unit.stable_core,
        rights_or_safety_critical=rights_or_safety_critical,
        machine_close_forbidden=machine_close_forbidden,
        priority_reason_codes=priority_reason_codes,
        source_locator_ids=tuple(sorted(
            {item.locator.locator_id() for item in evidence})))


def _not_evaluable_result(
    *, unit, reason, gap_roles, record_locators, plan_locators,
    enrollment_context, evidence=(), source_refs=(),
    l0_status=L0CoverageStatus.COVERED,
) -> D05UnitResult:
    return _result(
        unit=unit, disposition=L1Disposition.NOT_EVALUABLE,
        priority=_PRIORITY_UNKNOWN,
        evidence=evidence, source_refs=source_refs,
        enrollment_context=enrollment_context,
        not_evaluable_reason=reason, l0_status=l0_status)


def _not_applicable_result(
    *, unit, reason, authority_locator_ids, record_locators, plan_locators,
    enrollment_context,
) -> D05UnitResult:
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=(), plan_locator_ids=authority_locator_ids,
        polarity=L1bEvidencePolarity.CONTEXT)
    return _result(
        unit=unit, disposition=L1Disposition.NOT_APPLICABLE,
        priority=_PRIORITY_UNKNOWN,
        evidence=evidence, source_refs=(),
        enrollment_context=enrollment_context)


def _candidate_input(
    *, unit, subtype, audience_label, priority,
    anchor_kind="", window=None, anchor_day="",
    rights_or_safety_critical=False, machine_close_forbidden=False,
    match_reason="",
) -> Dict[str, Any]:
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return {
        "positive_subtype": subtype, "audience_label": audience_label,
        "monitoring_priority": priority,
        "rule_lineage": unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        "anchor_kind": anchor_kind, "anchor_start": "",
        "anchor_end": "", "window_start": window_start,
        "window_end": window_end, "precision": precision,
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
        "match_reason": match_reason,
    }


def _build_query_for_result(
    *, result: D05UnitResult, unit: ScheduleEvaluationUnit,
    protocol_version: str, enrollment_context: D05EnrollmentContext,
    candidate_id: str, plan_target: str = "",
) -> Optional[QueryDraftRef]:
    if result.l1_disposition != L1Disposition.POSITIVE:
        return None
    locator_ids = result.all_source_locator_ids()
    if not locator_ids:
        # No locatable supporting evidence (e.g. missing visit without
        # supplied plan locators): no Query can be bound; the positive unit
        # and its candidate still stand (§9.2 requires locatable evidence).
        return None
    if not plan_target:
        plan_target = "访视"
    if result.positive_subtype in (POSITIVE_VISIT_MISSING,
                                   POSITIVE_ASSESSMENT_MISSING,
                                   POSITIVE_SAMPLE_MISSING):
        finding = f"{result.audience_label}：截止数据截止日未见相应记录"
    elif result.positive_subtype in (POSITIVE_VISIT_OVERWINDOW,
                                     POSITIVE_ASSESSMENT_MISTIMED,
                                     POSITIVE_SAMPLE_MISTIMED):
        finding = (f"{result.audience_label}：实际记录时间 "
                   f"{result.actual_start or '未知'}，需与允许窗口核对")
    elif result.positive_subtype == POSITIVE_VISIT_ORDER_INCONSISTENT:
        finding = "访视先后顺序与方案计划次序不一致，需核实"
    elif result.positive_subtype == POSITIVE_VISIT_DUPLICATE:
        finding = "同一实际记录被重复计入多个计划单元，需核实归属"
    elif result.positive_subtype == POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT:
        finding = "实际记录归属与唯一可适用计划不一致，需核实访视归属"
    else:
        finding = "方案时序要求存在不一致，需核实"
    return build_d05_query_draft(
        unit_id=result.unit_id, subject_ref=result.subject_ref,
        protocol_version=protocol_version, plan_target=plan_target,
        anchor_label=result.anchor_kind or "计划锚点",
        window_start=result.window_start, window_end=result.window_end,
        finding=finding, query_context=enrollment_context.query_context,
        candidate_id=candidate_id,
        source_locator_ids=result.all_source_locator_ids())


def _plan_target_for(
    unit: ScheduleEvaluationUnit,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
) -> str:
    if unit.planned_activity_key:
        for activity in planned_activities:
            if activity.planned_activity_key == unit.planned_activity_key:
                return f"评估/样本 {activity.audience_name}"
    if unit.planned_visit_key:
        for visit in planned_visits:
            if visit.planned_visit_key == unit.planned_visit_key:
                return f"访视 {visit.audience_visit_name}"
    return "访视"


def _boundary_candidate_input(
    *, unit: ScheduleEvaluationUnit, audience_label: str,
    priority: str, anchor_kind: str = "", window: Optional[VisitWindowRule] = None,
    anchor_day: str = "", match_reason: str = "",
) -> Dict[str, Any]:
    """Candidate input for a boundary unit: one clue with preserved
    uncertainty (§8.4); signal type is the closed unit kind, never a
    fabricated positive subtype."""
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return {
        "positive_subtype": unit.unit_kind,
        "audience_label": audience_label,
        "monitoring_priority": priority,
        "rule_lineage": unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        "anchor_kind": anchor_kind, "anchor_start": "",
        "anchor_end": "", "window_start": window_start,
        "window_end": window_end, "precision": precision,
        "rights_or_safety_critical": False,
        "machine_close_forbidden": False,
        "match_reason": match_reason,
    }


def _build_gap_notice(result: D05UnitResult) -> Optional[VisitCoverageGapNotice]:
    if result.l1_disposition != L1Disposition.NOT_EVALUABLE:
        return None
    labels = {
        REASON_MATURITY_RULE_MISSING: "评价成熟规则未冻结，暂无法判断是否到计划时间",
        REASON_TIME_ROLE_MISSING: "实际日期或时间角色缺失，暂无法核对时间",
        REASON_COVERAGE_INCOMPLETE: "所需来源资料不完整，暂无法完成评价",
        REASON_PRECISION_INSUFFICIENT: "日期精度或窗口端点规则不足，暂无法完成评价",
        REASON_TIME_ROLE_CONFLICT: "实际日期角色冲突，暂无法完成评价",
        REASON_ANCHOR_MISSING: "计划锚点缺失，暂无法完成评价",
        REASON_MAPPING_MISSING: "访视/活动映射不足，暂无法确定归属",
    }
    reason = result.not_evaluable_reason or REASON_COVERAGE_INCOMPLETE
    audience_text = labels.get(reason, "资料不足，暂无法完成评价")
    return VisitCoverageGapNotice(
        notice_id="", unit_id=result.unit_id, reason_code=reason,
        missing_evidence_roles=(ANCHOR_ROLE_OTHER,),
        plan_locator_ids=(),
        reachable_source_locator_ids=result.all_source_locator_ids(),
        audience_text=audience_text)


def _build_interpretation_ledgers(
    *, visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    rule_ids: Sequence[str],
) -> Tuple[ScheduleInterpretationLedger, ...]:
    ledgers: List[ScheduleInterpretationLedger] = []
    for decision in visit_assignments:
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE \
                and not decision.rejected_candidate_reasons:
            continue
        interpretations = tuple(decision.candidate_planned_visit_ids)
        accepted = (decision.selected_planned_visit_id,) \
            if decision.selected_planned_visit_id else ()
        rejected = tuple(
            c for c in interpretations if c not in accepted)
        predicates = tuple(
            (i, PREDICATE_TRUE if i in accepted else PREDICATE_FALSE)
            for i in interpretations)
        if not interpretations:
            continue
        try:
            ledgers.append(ScheduleInterpretationLedger(
                ledger_id="", decision_scope=INTERPRET_SCOPE_WINDOW,
                interpretation_ids=interpretations,
                accepted_interpretation_ids=accepted,
                rejected_interpretation_ids=rejected,
                predicate_results=predicates,
                rejection_reason_codes=tuple(
                    r for r in decision.rejected_candidate_reasons
                    if r in REASON_CODES) or (REASON_MULTIPLE_FEASIBLE,),
                merge_split_repeat_reschedule_trigger_rule_ids=rule_ids,
                algorithm_version=D05_UNIT_ALGO_VERSION,
                source_locator_ids=decision.source_locator_ids))
        except ScheduleSliceError:
            continue
    for decision in activity_assignments:
        if decision.decision_status == ACTIVITY_ASSIGNMENT_UNIQUE:
            continue
        interpretations = tuple(decision.candidate_planned_activity_ids)
        accepted = tuple(decision.selected_planned_activity_ids)
        rejected = tuple(
            c for c in interpretations if c not in accepted)
        predicates = tuple(
            (i, PREDICATE_TRUE if i in accepted else PREDICATE_FALSE)
            for i in interpretations)
        if not interpretations:
            continue
        try:
            ledgers.append(ScheduleInterpretationLedger(
                ledger_id="", decision_scope=INTERPRET_SCOPE_REPEAT,
                interpretation_ids=interpretations,
                accepted_interpretation_ids=accepted,
                rejected_interpretation_ids=rejected,
                predicate_results=predicates,
                rejection_reason_codes=(REASON_MULTIPLE_FEASIBLE,),
                merge_split_repeat_reschedule_trigger_rule_ids=rule_ids,
                algorithm_version=D05_UNIT_ALGO_VERSION,
                source_locator_ids=decision.source_locator_ids))
        except ScheduleSliceError:
            continue
    return tuple(ledgers)


# ---------------------------------------------------------------------------
# Small helpers used across evaluation
# ---------------------------------------------------------------------------

def _timing_compare_instants(
    *, window_rule: VisitWindowRule, anchor_day: str,
    start: str, end: str, timezone: str,
) -> Tuple[str, str]:
    """Sub-day window verdict at instant level (challenges 26/27).

    Returns (disposition_token, reason) where disposition_token is one of
    NEGATIVE / POSITIVE / BOUNDARY / NOT_EVALUABLE.  Cross-midnight events
    require a frozen timezone (challenge 26); a missing timezone that can
    change the conclusion is not_evaluable (challenge 27).
    """
    lo_i = _parse_instant(start, timezone)
    hi_i = _parse_instant(end, timezone)
    if lo_i is None and hi_i is None:
        return L1Disposition.NOT_EVALUABLE, REASON_TIME_ROLE_MISSING
    if hi_i is None:
        hi_i = lo_i
    if lo_i is None:
        lo_i = hi_i
    if hi_i < lo_i:  # cross-midnight with complete timezone
        hi_i = hi_i + datetime.timedelta(days=1)
    anchor = _day_date(anchor_day)
    if anchor is None:
        return L1Disposition.NOT_EVALUABLE, REASON_TIME_ROLE_MISSING
    if window_rule.lower_endpoint_inclusive is None \
            or window_rule.upper_endpoint_inclusive is None:
        return L1Disposition.NOT_EVALUABLE, REASON_PRECISION_INSUFFICIENT
    lower = _offset_days(window_rule.lower_offset)
    upper = _offset_days(window_rule.upper_offset)
    grace = _offset_days(window_rule.grace_period)
    if lower is None or upper is None or grace is None:
        return L1Disposition.NOT_EVALUABLE, REASON_PRECISION_INSUFFICIENT

    def _apply(offset: int) -> datetime.date:
        if window_rule.calendar_semantics == "study_day":
            if window_rule.study_day_zero_exists is False:
                offset = offset - 1
        return anchor + datetime.timedelta(days=offset)

    lo_start, _ = _day_instant_interval(_apply(lower), _apply(lower))
    _, hi_end = _day_instant_interval(
        _apply(upper) + datetime.timedelta(days=grace),
        _apply(upper) + datetime.timedelta(days=grace))
    if not window_rule.lower_endpoint_inclusive:
        lo_start = lo_start + datetime.timedelta(days=1)
    if not window_rule.upper_endpoint_inclusive:
        hi_end = hi_end - datetime.timedelta(days=1)
    if hi_i < lo_start or lo_i > hi_end:
        return L1Disposition.POSITIVE, ""
    if lo_i >= lo_start and hi_i <= hi_end:
        return L1Disposition.NEGATIVE, ""
    return L1Disposition.BOUNDARY, REASON_INTERVAL_STRADDLES


def _parse_instant(raw: str, tz_token: str) -> Optional[datetime.datetime]:
    """Parse a sub-day datetime instant, normalized to UTC when a timezone
    is provided; None when unparseable."""
    raw = (raw or "").strip()
    if not raw:
        return None
    tz: Optional[datetime.tzinfo] = None
    token = (tz_token or "").strip()
    if token in ("UTC", "utc"):
        tz = datetime.timezone.utc
    else:
        m = re.match(r"^([+-])(\d{2}):(\d{2})$", token)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            tz = datetime.timezone(
                sign * datetime.timedelta(hours=int(m.group(2)),
                                          minutes=int(m.group(3))))
    try:
        parsed = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        if tz is None:
            return None
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(datetime.timezone.utc)


def _anchor_day_of(
    unit: ScheduleEvaluationUnit,
    expansion: ExpectedSetExpansion,
) -> str:
    for item in expansion.anchor_day_by_visit_key:
        if item[0] == unit.planned_visit_key:
            return item[1]
    return ""


def _source_refs_for_bundle(
    bundle: Optional[ActualEncounterBundle],
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    if bundle is None:
        return ()
    refs: List[SourceRecordRef] = []
    seen: Set[str] = set()
    for member_id in bundle.member_encounter_ids:
        locator = record_locators.get(member_id)
        if locator is None or locator.locator_id() in seen:
            continue
        seen.add(locator.locator_id())
        refs.append(SourceRecordRef(record_id=locator.record_id,
                                    locator=locator))
    return tuple(refs)


def _source_refs_for_activity(
    activity: ActualActivityRecord,
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    locator = record_locators.get(activity.actual_activity_id)
    if locator is None:
        return ()
    return (SourceRecordRef(record_id=locator.record_id, locator=locator),)


def _source_refs_for_activity_id(
    activity_id: str, activities: Sequence[ActualActivityRecord],
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    for activity in activities:
        if activity.actual_activity_id == activity_id:
            return _source_refs_for_activity(activity, record_locators)
    return ()


def _stable_key_of_activity(
    activity_id: str, activities: Sequence[ActualActivityRecord],
) -> str:
    for activity in activities:
        if activity.actual_activity_id == activity_id:
            return activity.stable_actual_object_key
    return ""


def _bundle_start(bundle: Optional[ActualEncounterBundle]) -> str:
    return (bundle.derived_start if bundle else "") or ""


def _bundle_end(bundle: Optional[ActualEncounterBundle]) -> str:
    return (bundle.derived_end if bundle else "") or ""


def _role_for_kind(activity_kind: str) -> str:
    return {
        ACTIVITY_ASSESSMENT: "assessment",
        ACTIVITY_SAMPLE: "sample",
        ACTIVITY_PROCEDURE: "procedure",
        ACTIVITY_CONTACT: "contact",
    }.get(activity_kind, "assessment")


def _missing_subtype(activity_kind: str) -> str:
    if activity_kind == ACTIVITY_SAMPLE:
        return POSITIVE_SAMPLE_MISSING
    return POSITIVE_ASSESSMENT_MISSING


def _mistimed_subtype(activity_kind: str) -> str:
    if activity_kind == ACTIVITY_SAMPLE:
        return POSITIVE_SAMPLE_MISTIMED
    return POSITIVE_ASSESSMENT_MISTIMED


def _resolve_assignment_verdict(
    policy: Optional[D05PriorityPolicy],
) -> Optional[D05PriorityVerdict]:
    if policy is None:
        return None
    return resolve_d05_priority(policy)


def _priority_or_unknown(verdict: Optional[D05PriorityVerdict]) -> str:
    if verdict is None:
        return _PRIORITY_UNKNOWN
    return verdict.priority
