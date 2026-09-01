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
from .visit_schedule_eval_contracts import _PRIORITY_UNKNOWN, _canonical_sorted

@dataclass(frozen=True)
class D05UnitResult:
    """The evaluation outcome of one D05 unit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol (contracts.py)
    and materializes a full :class:`UnitEvaluation` for the shared
    ``CoverageLedger``.
    """

    unit_id: str
    subject_ref: str
    site_ref: str
    unit_kind: str
    planned_visit_key: str = ""
    planned_activity_key: str = ""
    stable_actual_object_key: str = ""
    l1_disposition: str = L1Disposition.NOT_EVALUABLE
    monitoring_priority: str = _PRIORITY_UNKNOWN
    l0_status: str = L0CoverageStatus.COVERED
    positive_subtype: str = ""
    audience_label: str = ""
    query_context: str = ""
    not_evaluable_reason: str = ""
    boundary_reason: str = ""
    evaluation_window_id: str = ""
    rule_id: str = ""
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    anchor_kind: str = ""
    anchor_start: str = ""
    anchor_end: str = ""
    window_start: str = ""
    window_end: str = ""
    precision: str = PRECISION_DAY
    actual_start: str = ""
    actual_end: str = ""
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    coverage_gap_notices: Tuple[VisitCoverageGapNotice, ...] = ()
    classifier: str = ""
    stable_core: str = ""
    rights_or_safety_critical: bool = False
    machine_close_forbidden: bool = False
    priority_reason_codes: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.l1_disposition={self.l1_disposition!r} "
                f"invalid")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.monitoring_priority="
                f"{self.monitoring_priority!r} invalid")
        if self.l0_status not in L0CoverageStatus.ALL_STATUSES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.l0_status={self.l0_status!r} invalid")
        if self.positive_subtype and \
                self.positive_subtype not in POSITIVE_SUBTYPES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.positive_subtype="
                f"{self.positive_subtype!r} invalid")
        if self.query_context and self.query_context not in QUERY_CONTEXTS:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.query_context={self.query_context!r} invalid")
        if self.l1_disposition == L1Disposition.POSITIVE:
            if not self.positive_subtype:
                raise VisitScheduleEvaluatorError(
                    "positive unit requires a positive subtype")
            if not self.audience_label:
                raise VisitScheduleEvaluatorError(
                    "positive unit requires an audience label")
        if self.l1_disposition == L1Disposition.NOT_EVALUABLE:
            if not self.not_evaluable_reason:
                raise VisitScheduleEvaluatorError(
                    "not_evaluable unit requires not_evaluable_reason")
        for name in ("r2_candidates", "risk_candidate_refs",
                     "risk_instance_refs", "evidence", "source_record_refs",
                     "query_refs", "coverage_gap_notices"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "priority_reason_codes",
                           _canonical_sorted(self.priority_reason_codes))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))

    def all_source_locator_ids(self) -> Tuple[str, ...]:
        ids: List[str] = []
        for ref in self.source_record_refs:
            ids.append(ref.locator.locator_id())
        for item in self.evidence:
            ids.append(item.locator.locator_id())
        for ref in self.risk_candidate_refs:
            if ref.locator is not None:
                ids.append(ref.locator.locator_id())
        return tuple(sorted(set(ids)))

    def to_unit_evaluation(
        self, *, provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity not in polarities:
                polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=self.l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(sorted(polarities)),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Candidates, Query drafts, gap notices (§9, §12)
# ---------------------------------------------------------------------------

def _risk_scope(
    *, site_ref: str, protocol_version: str, arm: str, cohort: str,
    phase: str, rule_content_hash: str, evaluation_window_id: str,
) -> Tuple[str, ...]:
    parts: Set[str] = {
        f"site:{site_ref}" if site_ref else "site:",
        f"protocol:{protocol_version}" if protocol_version else "protocol:",
        f"arm:{arm}" if arm else "arm:",
        f"cohort:{cohort}" if cohort else "cohort:",
        f"phase:{phase}" if phase else "phase:",
        f"rule:{rule_content_hash}",
        f"window:{evaluation_window_id}" if evaluation_window_id else "window:",
        f"ua:{D05_EVAL_ALGO_VERSION}",
    }
    return tuple(sorted(parts))


def build_d05_candidate(
    *, project_id: str, subject_ref: str, site_ref: str,
    unit: ScheduleEvaluationUnit, positive_subtype: str,
    audience_label: str, monitoring_priority: str,
    snapshot_id: str, rule_lineage: str,
    anchor_kind: str = "", anchor_start: str = "", anchor_end: str = "",
    window_start: str = "", window_end: str = "", precision: str = "",
    protocol_version: str = "", arm: str = "", cohort: str = "",
    phase: str = "", rights_or_safety_critical: bool = False,
    machine_close_forbidden: bool = False,
    source_locator_ids: Sequence[str] = (),
    full_locator_id: str = "",
    match_reason: str = "",
) -> RiskCandidate:
    """Build the R2 candidate for one positive/boundary D05 unit (public
    ``make_risk_identity`` only; identity detail mirrors D04 conventions)."""
    scope = _risk_scope(
        site_ref=site_ref, protocol_version=protocol_version, arm=arm,
        cohort=cohort, phase=phase,
        rule_content_hash=unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        evaluation_window_id=unit.evaluation_window_id)
    classifier = unit.classifier or unit.stable_core
    identity = make_risk_identity(
        project_id=project_id, subject_ref=subject_ref,
        domain=D05_DOMAIN, scope=list(scope),
        classifier=classifier)
    if unit.planned_activity_key:
        stable_event_key = (
            f"activity:{unit.planned_activity_key}:"
            f"{unit.evaluation_window_id}")
    else:
        stable_event_key = (
            f"visit:{unit.planned_visit_key}:{unit.evaluation_window_id}")
    sorted_locators = tuple(sorted(source_locator_ids))
    first_locator = sorted_locators[0] if sorted_locators else ""
    detail: Dict[str, Any] = {
        "risk_identity_id": identity.risk_identity_id,
        # The shared lifecycle adapter requires stable_core to exactly equal
        # the identity classifier (D04 convention).
        "stable_core": classifier,
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": stable_event_key,
        "risk_family": unit.unit_kind,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "evaluation_window_id": unit.evaluation_window_id,
        "monitoring_priority": monitoring_priority,
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
        "match_reason": match_reason or positive_subtype,
        "protocol_version": protocol_version,
        "locator_id": first_locator,
        "full_locator_id": full_locator_id or first_locator,
    }
    return RiskCandidate.from_signal(
        project_id=project_id, subject_ref=subject_ref,
        domain=D05_DOMAIN, signal_type=positive_subtype,
        source_snapshot_id=snapshot_id,
        rule_activation_id=rule_lineage or D05_RULE_LINEAGE_DEFAULT,
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)


_ANCHOR_LABELS: Mapping[str, str] = {
    RELATION_FIXED_REFERENCE: "固定基准日",
    RELATION_PRIOR_ACTUAL_VISIT: "前次实际访视",
    "first_ip_dose": "首次给药",
    "randomization": "随机化",
    "consent": "知情同意",
    "other_verified_protocol_anchor": "其他已验证方案锚点",
}


def _action_suffix(query_context: str) -> str:
    if query_context == QUERY_CONTEXT_NOT_OCCURRED:
        return ("请核实访视、评估或样本完成情况、筛选结论或数据记录，"
                "并补充或更正相应记录。")
    if query_context == QUERY_CONTEXT_ENROLLED:
        return ("请核实、说明、补充或更正相应记录；如确认不符合方案，"
                "请评估是否构成方案偏离并按相应流程处理。")
    return ("请先核实是否已随机/入组/接受研究干预及事件时序；"
            "当前资料不足，暂无法确认是否符合方案。")


def build_d05_query_draft(
    *, unit_id: str, subject_ref: str, protocol_version: str,
    plan_target: str, anchor_label: str, window_start: str, window_end: str,
    finding: str, query_context: str, candidate_id: str,
    source_locator_ids: Sequence[str],
) -> QueryDraftRef:
    """Three-part Chinese Query draft (§9.2) -- fixed format, enrollment-
    aware action; only ``enrolled_or_post_enrollment`` appends PD wording."""
    window_txt = ""
    if window_start and window_end:
        window_txt = f"；允许窗口 {window_start} 至 {window_end}"
    anchor_txt = _ANCHOR_LABELS.get(anchor_label, anchor_label or "计划锚点")
    basis = (
        f"依据：方案 {protocol_version} 规定{plan_target}；"
        f"计划锚点 {anchor_txt}{window_txt}。")
    finding_txt = (
        f"发现：参与者 {subject_ref} {finding}。"
        f"支持依据定位 {', '.join(sorted(set(source_locator_ids)))}。")
    action = f"行动项：{_action_suffix(query_context)}"
    return QueryDraftRef(
        query_id="d05-query-" + content_hash({
            "unit_id": unit_id,
            "basis": basis, "finding": finding_txt, "action": action,
            "source_locator_ids": sorted(set(source_locator_ids)),
        }),
        unit_id=unit_id, basis=basis, finding=finding_txt, action=action,
        source_locator_ids=tuple(sorted(set(source_locator_ids))),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Run orchestration (§4.3 order)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class D05EvaluationOutcome:
    """One subject's D05 Run evaluation result."""

    run_id: str
    project_ref: str
    subject_ref: str
    site_ref: str
    snapshot_as_of: SnapshotAsOf
    clinical_event_cutoff: ClinicalEventCutoff
    applicability_decision: VisitScheduleApplicabilityDecision
    gates: Tuple[ScheduleGate, ...]
    gate_accounting: Any
    expected_units: Tuple[ScheduleEvaluationUnit, ...]
    expected_set: ExpectedSet
    visit_assignments: Tuple[VisitAssignmentDecision, ...]
    activity_assignments: Tuple[ActivityAssignmentDecision, ...]
    consumption_ledgers: Tuple[ActualActivityConsumptionLedger, ...]
    reverse_consumption_index: Tuple[Tuple[str, str], ...]
    unit_results: Tuple[D05UnitResult, ...]
    coverage_ledger: CoverageLedger
    coverage_summary: CoverageSummary
    domain_complete: Tuple[bool, List[str]]
    candidates: Tuple[RiskCandidate, ...]
    query_drafts: Tuple[QueryDraftRef, ...]
    coverage_gap_notices: Tuple[VisitCoverageGapNotice, ...]
    interpretation_ledgers: Tuple[ScheduleInterpretationLedger, ...]
    anchor_refs: Tuple[TypedScheduleAnchorRef, ...]
    anchor_day_by_visit_key: Tuple[Tuple[str, str], ...]
    out_of_cutoff_object_ids: Tuple[str, ...]
    future_obligation_keys: Tuple[str, ...]
    excluded_obligation_keys: Tuple[str, ...]
    enrollment_context: D05EnrollmentContext

    def l1_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {d: 0 for d in L1Disposition.ALL}
        for result in self.unit_results:
            counts[result.l1_disposition] += 1
        return counts

    def gates_block_domain(self) -> bool:
        return self.gate_accounting.blocks_domain_complete


def combine_domain_complete(
    *,
    coverage_complete: Tuple[bool, List[str]],
    gate_accounting: Any,
    gates: Sequence[Any] = (),
) -> Tuple[bool, List[str]]:
    """The authoritative D05 medical-completeness verdict.

    Domain completeness is the AND of the closed coverage-ledger verdict
    (:func:`is_domain_complete`) and the D05 control-plane gate accounting
    (§3.3, §12): any open applicability / routing / anchor / cutoff-scope
    gate blocks the medical domain, independently of whether the L1 units
    happened to evaluate closed.  Returns ``(True, [])`` only when both hold;
    otherwise ``(False, deterministic reasons)`` with the gate block listed
    first.
    """
    reasons: List[str] = []
    open_kinds = tuple(
        sorted({var.gate_kind for var in gates
                if getattr(var, "gate_state", "") == GATE_OPEN}))
    blocks = bool(gate_accounting.blocks_domain_complete) or bool(open_kinds)
    if blocks:
        kind_txt = (", ".join(open_kinds) if open_kinds else "unclassified")
        reasons.append(
            f"open ScheduleGate(s) block domain completeness: {kind_txt}")
    coverage_ok, coverage_reasons = coverage_complete
    reasons.extend(coverage_reasons)
    return (True, []) if (coverage_ok and not blocks) else (False, reasons)


def _resolve_scope_decisions(
    *, records: Sequence[Any], snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    record_locators: Mapping[str, SourceLocator],
    provided: Sequence[ActualRecordScopeDecision],
) -> Tuple[ActualRecordScopeDecision, ...]:
    if provided:
        return tuple(provided)
    decisions: List[ActualRecordScopeDecision] = []
    for record in records:
        object_id = getattr(record, "encounter_id", "") or getattr(
            record, "actual_activity_id", "")
        locator = record_locators.get(object_id)
        if locator is None:
            raise VisitScheduleEvaluatorError(
                f"record {object_id!r} has no source locator; cannot "
                f"resolve its scope (fail closed)")
        decisions.append(resolve_actual_record_scope(
            record=record, snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            source_locators=(locator,)))
    return tuple(decisions)

