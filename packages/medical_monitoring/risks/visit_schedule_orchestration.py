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
    _day_date, _order_key, _validate_nonempty,
)
from .visit_schedule_assignments import *
from .visit_schedule_expected import *
from .visit_schedule_expected import _visit_actual_day, _visit_key_of_activity
from .visit_schedule_results import *
from .visit_schedule_results import _resolve_scope_decisions
from .visit_schedule_output_helpers import *
from .visit_schedule_output_helpers import (
    _build_gap_notice, _build_interpretation_ledgers, _build_query_for_result,
    _plan_target_for,
)
from .visit_schedule_unit_evaluation import *
from .visit_schedule_unit_evaluation import _evaluate_unit, _first_locator, _link_unit

def evaluate_visit_schedule_run(
    *,
    run_id: str,
    project_ref: str,
    subject_ref: str,
    site_ref: str,
    snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    applicability_decision: VisitScheduleApplicabilityDecision,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition] = (),
    maturity_rules: Optional[Mapping[str, EvaluationMaturityRule]] = None,
    anchor_bindings: Sequence[AnchorBindingRequest] = (),
    encounters: Sequence[ActualEncounterRecord] = (),
    activities: Sequence[ActualActivityRecord] = (),
    bundles: Sequence[ActualEncounterBundle] = (),
    scope_decisions: Sequence[ActualRecordScopeDecision] = (),
    record_locators: Optional[Mapping[str, SourceLocator]] = None,
    plan_locators: Sequence[SourceLocator] = (),
    explicit_visit_mappings: Sequence[StableVisitMapping] = (),
    official_code_mappings: Sequence[OfficialCodeMapping] = (),
    activity_code_aliases: Sequence[OfficialActivityCodeAlias] = (),
    activity_window_rules: Optional[Mapping[str, VisitWindowRule]] = None,
    obligation_applicability: Optional[Mapping[str, ObligationApplicability]] = None,
    priority_policies: Optional[Mapping[str, D05PriorityPolicy]] = None,
    assignment_priority_policy: Optional[D05PriorityPolicy] = None,
    source_coverage: Optional[Mapping[str, bool]] = None,
    enrollment: Optional[EnrollmentEvidence] = None,
    schedule_consistency_issues: Sequence[ScheduleConsistencyIssue] = (),
    allow_unscheduled_visits: bool = False,
    allow_unscheduled_activities: bool = False,
    mapping_coverage_complete: bool = True,
    code_coverage_complete: bool = True,
    prior_resolved_gates: Sequence[ScheduleGate] = (),
    interpretation_rule_ids: Sequence[str] = (),
) -> D05EvaluationOutcome:
    """Run the frozen §4.3 pipeline for one subject: gates -> expected-set
    -> bidirectional assignment + ledger -> per-unit evaluation -> L2/L3
    (candidates, Query drafts, coverage-gap notices) -> closed coverage
    ledger."""
    _validate_nonempty(run_id, "run_id")
    _validate_nonempty(project_ref, "project_ref")
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    if not isinstance(snapshot_as_of, SnapshotAsOf):
        raise VisitScheduleEvaluatorError("snapshot_as_of must be SnapshotAsOf")
    if not isinstance(clinical_event_cutoff, ClinicalEventCutoff):
        raise VisitScheduleEvaluatorError(
            "clinical_event_cutoff must be ClinicalEventCutoff")
    maturity_rules = maturity_rules or {}
    activity_window_rules = activity_window_rules or {}
    obligation_applicability = obligation_applicability or {}
    priority_policies = priority_policies or {}
    source_coverage = source_coverage or {}
    record_locators = record_locators or {}

    # --- scope decisions (dual cutoff; worker_01 authority) ---------------
    scope_decisions = _resolve_scope_decisions(
        records=list(encounters) + list(activities),
        snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        record_locators=record_locators,
        provided=scope_decisions)
    encounter_ids = {e.encounter_id for e in encounters}
    in_scope_encounter_ids = {
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_IN_SCOPE and d.actual_object_id
        in encounter_ids}
    in_scope_bundles = tuple(
        b for b in bundles
        if all(member in in_scope_encounter_ids
               for member in b.member_encounter_ids))
    in_scope_activity_ids = {
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_IN_SCOPE
        and d.actual_object_id in {a.actual_activity_id for a in activities}}
    in_scope_activities = tuple(
        a for a in activities if a.actual_activity_id in in_scope_activity_ids)

    # --- enrollment context (§9.2) ----------------------------------------
    enrollment_evidence = enrollment or EnrollmentEvidence(
        subject_ref=subject_ref)
    enrollment_context = resolve_d05_enrollment_context(
        evidence=enrollment_evidence)

    # --- assignment contexts ----------------------------------------------
    applicable_visit_keys = tuple(
        sorted((v.planned_visit_key for v in planned_visits),
               key=lambda k: _order_key(
                   next(v.planned_order for v in planned_visits
                        if v.planned_visit_key == k))))
    anchor_day_by_key: Dict[str, str] = {}
    for binding in anchor_bindings:
        if binding.relation_type == RELATION_FIXED_REFERENCE:
            anchor_day_by_key[binding.planned_visit_key] = binding.anchor_day
    encounter_by_id = {e.encounter_id: e for e in encounters}
    visit_ctx = VisitAssignmentContext(
        project_ref=project_ref, subject_ref=subject_ref, site_ref=site_ref,
        applicable_visit_keys=applicable_visit_keys,
        planned_visits=tuple(planned_visits),
        explicit_mappings=tuple(explicit_visit_mappings),
        code_mappings=tuple(official_code_mappings),
        anchor_day_by_visit_key=tuple(sorted(anchor_day_by_key.items())),
        encounter_by_id=encounter_by_id,
        protocol_version=applicability_decision.protocol_version,
        allow_unscheduled_visits=allow_unscheduled_visits,
        mapping_coverage_complete=mapping_coverage_complete,
        code_coverage_complete=code_coverage_complete)

    # Chained-anchor feasibility considers ALL bundles (in-scope and
    # out-of-cutoff): an out-of-cutoff actual visit still proves the visit
    # occurred as a chained-anchor interpretation (§5.3), orthogonally to
    # its L1 evaluability.  Only the unique assignment is authoritative;
    # never a nearest-date / row-order shortcut.
    chained_anchor_prior_day_by_key: Dict[str, str] = {}
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(
            bundle=bundle, ctx=visit_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            day = _visit_actual_day(bundle)
            if day:
                chained_anchor_prior_day_by_key.setdefault(
                    decision.selected_planned_visit_id, day)

    activity_visit_key_by_id: Dict[str, str] = {}
    for activity in planned_activities:
        visit_key = _visit_key_of_activity(activity, planned_visits)
        if visit_key:
            activity_visit_key_by_id[activity.planned_activity_id] = visit_key
    activity_ctx = ActivityAssignmentContext(
        subject_ref=subject_ref, site_ref=site_ref,
        planned_activities=tuple(planned_activities),
        code_aliases=tuple(activity_code_aliases),
        planned_activity_visit_key=activity_visit_key_by_id,
        actual_activities=in_scope_activities,
        allow_unscheduled_activities=allow_unscheduled_activities,
        activity_evidence_complete=mapping_coverage_complete
        and code_coverage_complete)

    # --- gate + expected-set expansion ------------------------------------
    expansion = expand_expected_set(
        run_id=run_id, project_ref=project_ref, subject_ref=subject_ref,
        site_ref=site_ref, snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        applicability_decision=applicability_decision,
        planned_visits=planned_visits,
        planned_activities=planned_activities,
        maturity_rules=maturity_rules,
        anchor_bindings=anchor_bindings,
        scope_decisions=scope_decisions,
        obligation_applicability=obligation_applicability,
        schedule_consistency_issues=schedule_consistency_issues,
        activity_window_rules=activity_window_rules,
        visit_assignment_ctx=visit_ctx,
        activity_assignment_ctx=activity_ctx,
        bundles=in_scope_bundles,
        prior_resolved_gates=prior_resolved_gates,
        chained_anchor_prior_day_by_key=chained_anchor_prior_day_by_key)

    # --- real assignment passes -------------------------------------------
    visit_assignments = resolve_visit_assignments(
        bundles=in_scope_bundles, ctx=visit_ctx)
    visit_by_bundle = {
        d.actual_bundle_id: d.selected_planned_visit_id
        for d in visit_assignments
        if d.decision_status == VISIT_ASSIGNMENT_UNIQUE}
    bundle_by_encounter = {
        member_id: b.bundle_id
        for b in in_scope_bundles for member_id in b.member_encounter_ids}
    visit_key_by_activity: Dict[str, str] = {}
    for activity in in_scope_activities:
        visit_key = ""
        for encounter_id in activity.encounter_refs:
            bundle_id = bundle_by_encounter.get(encounter_id, "")
            if bundle_id and bundle_id in visit_by_bundle:
                visit_key = visit_by_bundle[bundle_id]
                break
        visit_key_by_activity[activity.actual_activity_id] = visit_key
    activity_assignments = resolve_activity_assignments(
        activities=in_scope_activities,
        visit_key_by_activity=visit_key_by_activity,
        ctx=activity_ctx)
    ledgers = build_consumption_ledgers(
        assignments=activity_assignments,
        planned_activities=planned_activities,
        site_ref=site_ref)
    reverse_index = tuple(sorted(
        (pid, d.actual_activity_id)
        for d in activity_assignments for pid in d.selected_planned_activity_ids))

    # --- final units with assignment links --------------------------------
    final_units: List[ScheduleEvaluationUnit] = []
    for unit in expansion.expected_units:
        final_units.append(_link_unit(unit, visit_assignments,
                                      activity_assignments, ledgers))

    # --- per-unit evaluation ----------------------------------------------
    cutoff_day = _day_date(clinical_event_cutoff.cutoff)
    results: List[D05UnitResult] = []
    candidate_inputs: List[Optional[Dict[str, Any]]] = []
    for unit in final_units:
        result, candidate_input = _evaluate_unit(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            activity_assignments=activity_assignments,
            ledgers=ledgers, reverse_index=reverse_index,
            planned_visits=planned_visits,
            planned_activities=planned_activities,
            encounters=encounters, activities=activities,
            bundles=in_scope_bundles,
            scope_decisions=scope_decisions,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            activity_window_rules=activity_window_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            cutoff_day=cutoff_day,
            priority_policies=priority_policies,
            assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            record_locators=record_locators,
            plan_locators=plan_locators)
        results.append(result)
        candidate_inputs.append(candidate_input)

    # --- L2/L3: candidates, queries, gap notices --------------------------
    candidates: List[RiskCandidate] = []
    queries: List[QueryDraftRef] = []
    gap_notices: List[VisitCoverageGapNotice] = []
    for index, (unit, candidate_input) in enumerate(
            zip(final_units, candidate_inputs)):
        result = results[index]
        if candidate_input is not None:
            first_loc = _first_locator(result)
            candidate = build_d05_candidate(
                project_id=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, unit=unit,
                positive_subtype=candidate_input["positive_subtype"],
                audience_label=candidate_input["audience_label"],
                monitoring_priority=candidate_input["monitoring_priority"],
                snapshot_id=snapshot_as_of.snapshot_id,
                rule_lineage=candidate_input["rule_lineage"],
                anchor_kind=candidate_input["anchor_kind"],
                anchor_start=candidate_input["anchor_start"],
                anchor_end=candidate_input["anchor_end"],
                window_start=candidate_input["window_start"],
                window_end=candidate_input["window_end"],
                precision=candidate_input["precision"],
                protocol_version=applicability_decision.protocol_version,
                arm=applicability_decision.arm,
                cohort=applicability_decision.cohort,
                phase=applicability_decision.phase,
                rights_or_safety_critical=candidate_input[
                    "rights_or_safety_critical"],
                machine_close_forbidden=candidate_input[
                    "machine_close_forbidden"],
                source_locator_ids=result.all_source_locator_ids(),
                full_locator_id=first_loc.locator_id() if first_loc else "",
                match_reason=candidate_input["match_reason"])
            candidates.append(candidate)
            cand_ref = RiskCandidateRef(
                candidate_id=candidate.candidate_id,
                risk_identity_id=str(candidate.detail.get(
                    "risk_identity_id", "")),
                locator=first_loc)
            result = replace(
                result, r2_candidates=(candidate,),
                risk_candidate_refs=(cand_ref,))
            if result.l1_disposition == L1Disposition.POSITIVE:
                query = _build_query_for_result(
                    result=result, unit=unit,
                    protocol_version=applicability_decision.protocol_version,
                    enrollment_context=enrollment_context,
                    candidate_id=cand_ref.candidate_id,
                    plan_target=_plan_target_for(unit, planned_visits,
                                                 planned_activities))
                if query is not None:
                    queries.append(query)
                    result = replace(result, query_refs=(query,))
        if result.l1_disposition == L1Disposition.NOT_EVALUABLE:
            notice = _build_gap_notice(result)
            if notice is not None:
                gap_notices.append(notice)
                result = replace(result, coverage_gap_notices=(notice,))
        results[final_units.index(unit)] = result

    # --- closed coverage ledger -------------------------------------------
    expected = ExpectedSet.from_units(
        final_units, domain_id=D05_DOMAIN, run_id=run_id)
    ledger = CoverageLedger(expected_set=expected)
    for unit, result in zip(final_units, results):
        maturity_rule = maturity_rules.get(unit.unit_kind)
        provenance_rule = (maturity_rule.rule_version if maturity_rule
                           else D05_RULE_LINEAGE_DEFAULT)
        ledger.assign(result.to_unit_evaluation(
            provenance_snapshot_id=snapshot_as_of.snapshot_id,
            provenance_rule_lineage=provenance_rule))
    ledger.close()
    summary = ledger.close_and_summarize()
    coverage_complete = is_domain_complete(summary)
    domain_complete = combine_domain_complete(
        coverage_complete=coverage_complete,
        gate_accounting=expansion.gate_accounting,
        gates=expansion.gates)

    interp_ledgers = _build_interpretation_ledgers(
        visit_assignments=visit_assignments,
        activity_assignments=activity_assignments,
        rule_ids=interpretation_rule_ids)

    return D05EvaluationOutcome(
        run_id=run_id, project_ref=project_ref, subject_ref=subject_ref,
        site_ref=site_ref, snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        applicability_decision=applicability_decision,
        gates=expansion.gates, gate_accounting=expansion.gate_accounting,
        expected_units=tuple(final_units), expected_set=expected,
        visit_assignments=visit_assignments,
        activity_assignments=activity_assignments,
        consumption_ledgers=ledgers,
        reverse_consumption_index=reverse_index,
        unit_results=tuple(results), coverage_ledger=ledger,
        coverage_summary=summary, domain_complete=domain_complete,
        candidates=tuple(candidates), query_drafts=tuple(queries),
        coverage_gap_notices=tuple(gap_notices),
        interpretation_ledgers=interp_ledgers,
        anchor_refs=expansion.anchor_refs,
        anchor_day_by_visit_key=expansion.anchor_day_by_visit_key,
        out_of_cutoff_object_ids=expansion.out_of_cutoff_object_ids,
        future_obligation_keys=expansion.future_obligation_keys,
        excluded_obligation_keys=expansion.excluded_obligation_keys,
        enrollment_context=enrollment_context)

