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
    _bundle_interval_relation_to_day, _canonical_sorted, _day_date, _order_key,
)
from .visit_schedule_assignments import *
from .visit_schedule_assignments import _activity_candidate_keys

@dataclass(frozen=True)
class ExpectedSetExpansion:
    """Result of the gate + expected-set phase (§4.3 order)."""

    gates: Tuple[ScheduleGate, ...]
    gate_accounting: Any
    expected_units: Tuple[ScheduleEvaluationUnit, ...]
    expected_set: ExpectedSet
    anchor_refs: Tuple[TypedScheduleAnchorRef, ...]
    anchor_day_by_visit_key: Tuple[Tuple[str, str], ...]
    out_of_cutoff_object_ids: Tuple[str, ...]
    future_obligation_keys: Tuple[str, ...]
    excluded_obligation_keys: Tuple[str, ...]
    visit_assignment_prepass: Tuple[Tuple[str, str], ...]
    # (visit key, bundle id) unique pre-pass candidates used to decide
    # timing/order unit existence; deterministic.
    activity_assignment_prepass: Tuple[Tuple[str, str], ...]
    # (activity id, planned activity key) unique pre-pass candidates.
    scope_decisions: Tuple[ActualRecordScopeDecision, ...]
    cutoff: ClinicalEventCutoff


def _applicability_gate(
    *, decision: VisitScheduleApplicabilityDecision,
) -> ScheduleGate:
    status = decision.decision_status
    decision_status = (
        GATE_DECISION_BOUNDARY
        if status == APPLICABILITY_MULTI_FEASIBLE_BOUNDARY
        else GATE_DECISION_NOT_EVALUABLE)
    return ScheduleGate(
        gate_id="", gate_kind=GATE_APPLICABILITY,
        subject_ref=decision.subject_ref, site_ref=decision.site_ref,
        gate_state=GATE_OPEN, decision_status=decision_status,
        feasible_schedule_ids=decision.feasible_schedule_ids,
        reason_codes=decision.reason_codes or (REASON_VERSION_MISSING,),
        source_locator_ids=decision.source_locator_ids)


def _cutoff_scope_gates(
    *, scope_decisions: Sequence[ActualRecordScopeDecision],
    subject_ref: str, site_ref: str,
) -> Tuple[ScheduleGate, ...]:
    gates: List[ScheduleGate] = []
    seen: Set[str] = set()
    for decision in scope_decisions:
        if decision.scope_status not in (SCOPE_BOUNDARY, SCOPE_NOT_EVALUABLE):
            continue
        if decision.scope_decision_id in seen:
            continue  # one gate per stable decision per Run
        seen.add(decision.scope_decision_id)
        decision_status = (
            GATE_DECISION_BOUNDARY
            if decision.scope_status == SCOPE_BOUNDARY
            else GATE_DECISION_NOT_EVALUABLE)
        gates.append(ScheduleGate(
            gate_id="", gate_kind=GATE_CUTOFF_SCOPE,
            subject_ref=subject_ref, site_ref=site_ref,
            gate_state=GATE_OPEN, decision_status=decision_status,
            reason_codes=decision.reason_codes,
            source_locator_ids=decision.source_locator_ids))
    return tuple(gates)


def _visit_actual_day(bundle: ActualEncounterBundle) -> str:
    """The bundle's derived start day (chained-anchor propagation source);
    empty when the bundle is not day-dated."""
    lo, _, complete = _bundle_interval_relation_to_day(bundle)
    if not complete or lo is None:
        return ""
    return lo.isoformat()


def expand_expected_set(
    *,
    run_id: str,
    project_ref: str,
    subject_ref: str,
    site_ref: str,
    snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    applicability_decision: VisitScheduleApplicabilityDecision,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
    maturity_rules: Mapping[str, EvaluationMaturityRule],
    anchor_bindings: Sequence[AnchorBindingRequest],
    scope_decisions: Sequence[ActualRecordScopeDecision],
    obligation_applicability: Mapping[str, ObligationApplicability],
    schedule_consistency_issues: Sequence[ScheduleConsistencyIssue],
    activity_window_rules: Mapping[str, VisitWindowRule],
    visit_assignment_ctx: VisitAssignmentContext,
    activity_assignment_ctx: ActivityAssignmentContext,
    bundles: Sequence[ActualEncounterBundle],
    prior_resolved_gates: Sequence[ScheduleGate] = (),
    chained_anchor_prior_day_by_key: Optional[
        Mapping[str, str]] = None,
) -> ExpectedSetExpansion:
    """Gate + expected-set expansion in the frozen §4.3 order.

    ``chained_anchor_prior_day_by_key`` maps a planned_visit_key to its
    complete actual-visit day considering **all** bundles (in-scope and
    out-of-cutoff): an out-of-cutoff actual record still proves a prior
    visit occurred as a chained-anchor interpretation (§5.3), even though
    it never enters the L1 assignment (the two are orthogonal).  When two
    or more distinct prior visits at the immediately-preceding order level
    each carry a complete interpretation, the chained anchor is ambiguous
    and resolves to a single boundary ``GATE_ANCHOR`` (challenge 102),
    not a nearest-date winner.
    """
    gates: List[ScheduleGate] = list(prior_resolved_gates)
    cutoff_day = _day_date(clinical_event_cutoff.cutoff)

    # 1. Applicability gate (subject level).
    if applicability_decision.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
        gates.append(_applicability_gate(decision=applicability_decision))
        expected_set = ExpectedSet.from_units([], domain_id=D05_DOMAIN,
                                              run_id=run_id)
        accounting = validate_gate_run_accounting(gates=gates, run_id=run_id)
        return ExpectedSetExpansion(
            gates=tuple(gates), gate_accounting=accounting,
            expected_units=(), expected_set=expected_set, anchor_refs=(),
            anchor_day_by_visit_key=(), out_of_cutoff_object_ids=(),
            future_obligation_keys=(), excluded_obligation_keys=(),
            visit_assignment_prepass=(), activity_assignment_prepass=(),
            scope_decisions=tuple(scope_decisions),
            cutoff=clinical_event_cutoff)

    applicable_visit_keys = visit_assignment_ctx.applicable_visit_keys

    # 2. Owner routing: unresolved owner -> one routing gate; producer-owned
    # activities are excluded from the D05 expected-set (§2.3).
    routing_activity_keys: Set[str] = set()
    producer_owned_keys: Set[str] = set()
    for activity in planned_activities:
        if activity.owner_domain == OWNER_UNRESOLVED:
            routing_activity_keys.add(activity.planned_activity_key)
        elif activity.owner_domain != OWNER_D05:
            producer_owned_keys.add(activity.planned_activity_key)
    if routing_activity_keys:
        gates.append(ScheduleGate(
            gate_id="", gate_kind=GATE_ROUTING,
            subject_ref=subject_ref, site_ref=site_ref,
            gate_state=GATE_OPEN, decision_status=GATE_DECISION_NOT_EVALUABLE,
            feasible_owner_domains=(OWNER_UNRESOLVED,),
            affected_planned_activity_keys=_canonical_sorted(
                routing_activity_keys),
            reason_codes=(REASON_ROUTING_COMPETITION,),
            source_locator_ids=()))
    excluded_keys = set(routing_activity_keys) | set(producer_owned_keys)

    # 3. Cutoff-scope gates from the scope decisions.
    gates.extend(_cutoff_scope_gates(scope_decisions=scope_decisions,
                                     subject_ref=subject_ref,
                                     site_ref=site_ref))

    # 4. Anchor resolution (fixed / producer / chained) -- §4.3 order.
    # Chained anchors need the prior visit's unique *actual* date, so a
    # minimal bundle->visit pre-pass runs first (same assignment algorithm;
    # only fixed anchors are available at this stage, which is exactly the
    # §4.3 "unique resolve" requirement -- never a nearest-date shortcut).
    actual_day_by_visit_key: Dict[str, str] = {}
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            day = _visit_actual_day(bundle)
            if day:
                actual_day_by_visit_key.setdefault(
                    decision.selected_planned_visit_id, day)

    binding_by_key = {b.planned_visit_key: b for b in anchor_bindings}
    anchor_by_key: Dict[str, TypedScheduleAnchorRef] = {}
    anchor_day_by_key: Dict[str, str] = {}
    anchor_gate_keys: Set[str] = set()
    anchor_gates: List[ScheduleGate] = []
    ordered_keys = sorted(
        applicable_visit_keys,
        key=lambda k: _order_key(visit_assignment_ctx.visit_by_key(k).planned_order)
        if visit_assignment_ctx.visit_by_key(k) else (0,))
    resolved_anchor_refs: List[TypedScheduleAnchorRef] = []
    for visit_key in ordered_keys:
        visit = visit_assignment_ctx.visit_by_key(visit_key)
        if visit is None:
            continue
        binding = binding_by_key.get(visit_key)
        if binding is None:
            anchor_gate_keys.add(visit_key)
            continue
        relation = binding.relation_type
        if relation == RELATION_PRIOR_ACTUAL_VISIT:
            prior_level_keys = [
                k for k in ordered_keys
                if _order_key(
                    visit_assignment_ctx.visit_by_key(k).planned_order)
                < _order_key(visit.planned_order)]
            if prior_level_keys:
                max_prior_order = max(
                    _order_key(
                        visit_assignment_ctx.visit_by_key(k).planned_order)
                    for k in prior_level_keys)
                prior_level_keys = [
                    k for k in prior_level_keys
                    if _order_key(
                        visit_assignment_ctx.visit_by_key(k).planned_order)
                    == max_prior_order]
            # Complete feasible prior interpretations: each distinct prior
            # visit at the immediately-preceding order level with a
            # locatable actual-visit day (in-scope or out-of-cutoff).
            feasible_priors: List[str] = []
            for prior_key in prior_level_keys:
                day = actual_day_by_visit_key.get(prior_key, "")
                if not day:
                    day = (chained_anchor_prior_day_by_key or {}).get(
                        prior_key, "")
                if day:
                    feasible_priors.append(prior_key)
            if len(feasible_priors) >= 2:
                # Two+ complete feasible prior interpretations -> the
                # chained anchor is ambiguous: one boundary anchor gate
                # with the feasible anchor refs (challenge 102); never a
                # nearest-date / last-in-order winner.
                feasible_refs: List[TypedScheduleAnchorRef] = []
                for prior_key in sorted(feasible_priors):
                    prior_day = (actual_day_by_visit_key.get(prior_key, "")
                                 or (chained_anchor_prior_day_by_key or {}).get(
                                     prior_key, ""))
                    prior_binding = binding_by_key.get(prior_key)
                    # Each chained-anchor interpretation is one distinct
                    # prior visit occurrence; the episode discriminator
                    # keeps the two interpretations' stable anchor ids
                    # distinct (the anchor date is lineage-only, never a
                    # stable-id dimension, so the prior visit identity is
                    # carried here).
                    feasible_refs.append(TypedScheduleAnchorRef(
                        anchor_ref_id="", producer_domain="",
                        producer_unit_id="", stable_source_event_key="",
                        content_hash="", subject_ref=subject_ref,
                        site_ref=site_ref,
                        phase=prior_binding.phase if prior_binding else "",
                        episode_id=("prior:" + prior_key + ":" + prior_day),
                        anchor_start=prior_day, anchor_end=prior_day,
                        date_precision=PRECISION_DAY, timezone="",
                        relation_type=RELATION_PRIOR_ACTUAL_VISIT,
                        source_locator_ids=(
                            prior_binding.source_locator_ids
                            if prior_binding else ())))
                anchor_gate_keys.add(visit_key)
                anchor_gates.append(ScheduleGate(
                    gate_id="", gate_kind=GATE_ANCHOR,
                    subject_ref=subject_ref, site_ref=site_ref,
                    gate_state=GATE_OPEN,
                    decision_status=GATE_DECISION_BOUNDARY,
                    feasible_anchor_ref_ids=tuple(sorted(
                        r.anchor_ref_id for r in feasible_refs)),
                    affected_planned_visit_keys=(visit_key,),
                    affected_planned_activity_keys=_canonical_sorted(
                        binding.affected_planned_activity_keys),
                    missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
                    reason_codes=(REASON_MULTIPLE_FEASIBLE,),
                    source_locator_ids=binding.source_locator_ids))
                resolved_anchor_refs.extend(feasible_refs)
                continue
            prior_day = ""
            if len(feasible_priors) == 1:
                prior_key = feasible_priors[0]
                prior_day = (actual_day_by_visit_key.get(prior_key, "")
                             or (chained_anchor_prior_day_by_key or {}).get(
                                 prior_key, ""))
            if not prior_day:
                anchor_gate_keys.add(visit_key)
                anchor_gates.append(_chained_anchor_gate(
                    visit_key=visit_key, subject_ref=subject_ref,
                    site_ref=site_ref,
                    affected_activity_keys=binding.affected_planned_activity_keys))
                continue
            ref = TypedScheduleAnchorRef(
                anchor_ref_id="", producer_domain="", producer_unit_id="",
                stable_source_event_key="", content_hash="",
                subject_ref=subject_ref, site_ref=site_ref,
                phase=binding.phase, episode_id=binding.episode_id,
                anchor_start=prior_day, anchor_end=prior_day,
                date_precision=PRECISION_DAY, timezone="",
                relation_type=RELATION_PRIOR_ACTUAL_VISIT,
                source_locator_ids=binding.source_locator_ids)
            anchor_by_key[visit_key] = ref
            anchor_day_by_key[visit_key] = prior_day
            resolved_anchor_refs.append(ref)
            continue
        if relation == RELATION_FIXED_REFERENCE:
            outcome = bind_typed_schedule_anchor(
                relation_type=relation, subject_ref=subject_ref,
                site_ref=site_ref, anchor_start=binding.anchor_day,
                anchor_end=binding.anchor_day,
                date_precision=PRECISION_DAY, timezone="",
                phase=binding.phase, episode_id=binding.episode_id,
                affected_planned_visit_keys=(visit_key,),
                affected_planned_activity_keys=binding.affected_planned_activity_keys,
                source_locators=())
        else:
            outcome = bind_typed_schedule_anchor(
                relation_type=relation, subject_ref=subject_ref,
                site_ref=site_ref, producer_ref=binding.producer_ref,
                producer_domain=binding.producer_domain,
                producer_unit_id=binding.producer_unit_id,
                stable_source_event_key=binding.stable_source_event_key,
                content_hash=binding.content_hash, phase=binding.phase,
                episode_id=binding.episode_id,
                anchor_start=binding.anchor_start,
                anchor_end=binding.anchor_end,
                date_precision=binding.date_precision,
                timezone=binding.timezone,
                affected_planned_visit_keys=(visit_key,),
                affected_planned_activity_keys=binding.affected_planned_activity_keys,
                source_locators=())
        if outcome.is_bound:
            ref = outcome.anchor_ref
            assert ref is not None
            anchor_by_key[visit_key] = ref
            anchor_day_by_key[visit_key] = ref.anchor_start
            resolved_anchor_refs.append(ref)
        else:
            gate = outcome.gate
            assert gate is not None
            anchor_gate_keys.add(visit_key)
            anchor_gates.append(gate)
    gates.extend(anchor_gates)
    for key in anchor_gate_keys:
        binding = binding_by_key.get(key)
        if binding is not None:
            excluded_keys.update(binding.affected_planned_activity_keys)

    # 5. Expected-unit expansion over applicable, anchored, matured
    # obligations.  Out-of-cutoff records never enter the medical
    # denominator (§4.2); they are projected as Journey future context only.
    out_of_cutoff_ids = tuple(sorted(
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_OUT_OF_CUTOFF))

    units: List[ScheduleEvaluationUnit] = []
    future_keys: Set[str] = set()
    visit_prepass: List[Tuple[str, str]] = []

    # Pre-pass visit candidates: unique dated bundle -> visit key (also
    # decides timing/order unit existence; deterministic).
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            visit_prepass.append(
                (decision.selected_planned_visit_id, bundle.bundle_id))

    for visit in sorted(planned_visits, key=lambda v: v.planned_visit_key):
        key = visit.planned_visit_key
        if key not in applicable_visit_keys:
            continue
        if key in excluded_keys or key in anchor_gate_keys:
            continue
        anchor_day = anchor_day_by_key.get(key, "")
        occurrence_rule = maturity_rules.get(UNIT_VISIT_OCCURRENCE)
        occurrence_unit = _build_visit_unit(
            unit_kind=UNIT_VISIT_OCCURRENCE, visit=visit,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule=occurrence_rule,
            anchor_day=anchor_day, window_rule=visit.window_rule,
            anchor_episode_id=anchor_by_key.get(key, "").episode_id
            if key in anchor_by_key else "",
            cutoff_day=cutoff_day)
        if occurrence_unit is not None:
            units.append(occurrence_unit)
        else:
            future_keys.add(key)
        assigned_bundle = next(
            (bundle_id for vk, bundle_id in visit_prepass if vk == key), "")
        if assigned_bundle:
            timing_rule = maturity_rules.get(UNIT_VISIT_TIMING)
            timing_unit = _build_visit_unit(
                unit_kind=UNIT_VISIT_TIMING, visit=visit,
                project_ref=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, rule=timing_rule,
                anchor_day=anchor_day, window_rule=visit.window_rule,
                anchor_episode_id=anchor_by_key.get(key, "").episode_id
                if key in anchor_by_key else "",
                cutoff_day=cutoff_day)
            if timing_unit is not None:
                units.append(timing_unit)
        if visit.visit_kind == VISIT_SCHEDULED:
            predecessor = _predecessor_visit(visit, planned_visits)
            if predecessor is not None and any(
                    vk == predecessor.planned_visit_key
                    for vk, _ in visit_prepass):
                order_rule = maturity_rules.get(UNIT_VISIT_ORDER)
                order_unit = _build_visit_unit(
                    unit_kind=UNIT_VISIT_ORDER, visit=visit,
                    project_ref=project_ref, subject_ref=subject_ref,
                    site_ref=site_ref, rule=order_rule,
                    anchor_day=anchor_day, window_rule=visit.window_rule,
                    anchor_episode_id=anchor_by_key.get(key, "").episode_id
                    if key in anchor_by_key else "",
                    cutoff_day=cutoff_day)
                if order_unit is not None:
                    units.append(order_unit)

    # Activity units under anchored, applicable visits.
    visit_keys_set = set(applicable_visit_keys) - excluded_keys - anchor_gate_keys
    activity_prepass: List[Tuple[str, str]] = []
    for activity in planned_activities:
        if activity.owner_domain != OWNER_D05:
            continue
        if activity.planned_activity_key in excluded_keys:
            continue
        visit_key = _visit_key_of_activity(activity, planned_visits)
        if visit_key is None or visit_key not in visit_keys_set:
            continue
        anchor_day = anchor_day_by_key.get(visit_key, "")
        window_rule = activity_window_rules.get(activity.planned_activity_key)
        occurrence_rule = maturity_rules.get(UNIT_ACTIVITY_OCCURRENCE)
        occurrence_unit = _build_activity_unit(
            unit_kind=UNIT_ACTIVITY_OCCURRENCE, activity=activity,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule=occurrence_rule,
            anchor_day=anchor_day, window_rule=window_rule,
            anchor_episode_id=anchor_by_key.get(visit_key, "").episode_id
            if visit_key in anchor_by_key else "",
            cutoff_day=cutoff_day)
        if occurrence_unit is not None:
            units.append(occurrence_unit)
        else:
            future_keys.add(activity.planned_activity_key)
        timing_rule = maturity_rules.get(UNIT_ACTIVITY_TIMING)
        if timing_rule is not None and window_rule is not None \
                and _activity_prepass_unique(
                    activity=activity, visit_key=visit_key,
                    activity_assignment_ctx=activity_assignment_ctx):
            timing_unit = _build_activity_unit(
                unit_kind=UNIT_ACTIVITY_TIMING, activity=activity,
                project_ref=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, rule=timing_rule,
                anchor_day=anchor_day, window_rule=window_rule,
                anchor_episode_id=anchor_by_key.get(visit_key, "").episode_id
                if visit_key in anchor_by_key else "",
                cutoff_day=cutoff_day)
            if timing_unit is not None:
                units.append(timing_unit)
                for actual in activity_assignment_ctx.actual_activities:
                    planned_of_visit = [
                        a for a in activity_assignment_ctx.planned_activities
                        if activity_assignment_ctx.planned_activity_visit_key.get(
                            a.planned_activity_id, "") == visit_key]
                    cands, _ = _activity_candidate_keys(
                        activity=actual, visit_key=visit_key,
                        planned_activities=planned_of_visit,
                        code_aliases=activity_assignment_ctx.code_aliases)
                    if len(cands) == 1 \
                            and cands[0].planned_activity_key \
                            == activity.planned_activity_key:
                        activity_prepass.append(
                            (actual.actual_activity_id,
                             activity.planned_activity_key))
                        break

    # Actual-assignment units for problematic in-scope actual objects.
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status not in (
                VISIT_ASSIGNMENT_MULTI_FEASIBLE,
                VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
                VISIT_ASSIGNMENT_NOT_EVALUABLE):
            continue
        unit = _build_assignment_unit(
            unit_kind=UNIT_ACTUAL_ASSIGNMENT,
            stable_actual_object_key=bundle.stable_actual_object_key,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="d05-assignment-v1",
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    # Activity-level reverse check units (duplicate consumption /
    # complete-evidence mislabel; §7.2) -- decided by the same assignment
    # algorithm over the pre-pass visit context.
    bundle_by_encounter = {
        member_id: b.bundle_id
        for b in bundles for member_id in b.member_encounter_ids}
    visit_by_bundle = {
        d.actual_bundle_id: d.selected_planned_visit_id
        for d in (resolve_visit_assignment(bundle=b, ctx=visit_assignment_ctx)
                  for b in bundles)
        if d.decision_status == VISIT_ASSIGNMENT_UNIQUE}
    for actual in sorted(activity_assignment_ctx.actual_activities,
                         key=lambda a: a.actual_activity_id):
        visit_key = ""
        for encounter_id in actual.encounter_refs:
            bundle_id = bundle_by_encounter.get(encounter_id, "")
            if bundle_id and bundle_id in visit_by_bundle:
                visit_key = visit_by_bundle[bundle_id]
                break
        if not visit_key:
            continue
        planned_of_visit = [
            a for a in planned_activities
            if activity_assignment_ctx.planned_activity_visit_key.get(
                a.planned_activity_id, "") == visit_key]
        candidates, _ = _activity_candidate_keys(
            activity=actual, visit_key=visit_key,
            planned_activities=planned_of_visit,
            code_aliases=activity_assignment_ctx.code_aliases)
        problematic = (
            (len(candidates) >= 2
             and not all(bool(c.repeat_rule.strip()) for c in candidates))
            or (len(candidates) == 0
                and actual.recorded_activity_code.strip()
                and "UNSCHED" not in actual.recorded_activity_code.upper()
                and activity_assignment_ctx.activity_evidence_complete))
        if not problematic:
            continue
        unit = _build_assignment_unit(
            unit_kind=UNIT_ACTUAL_ASSIGNMENT,
            stable_actual_object_key=actual.stable_actual_object_key,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="d05-assignment-v1",
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    # Schedule-consistency units for declared plan self-inconsistencies.
    for issue in schedule_consistency_issues:
        unit = _build_assignment_unit(
            unit_kind=UNIT_SCHEDULE_CONSISTENCY,
            stable_actual_object_key="",
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="|".join(issue.rule_ids),
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    units = _dedupe_units(units)
    expected_set = ExpectedSet.from_units(units, domain_id=D05_DOMAIN,
                                          run_id=run_id)
    accounting = validate_gate_run_accounting(gates=gates, run_id=run_id)
    return ExpectedSetExpansion(
        gates=tuple(gates), gate_accounting=accounting,
        expected_units=tuple(units), expected_set=expected_set,
        anchor_refs=tuple(resolved_anchor_refs),
        anchor_day_by_visit_key=tuple(sorted(anchor_day_by_key.items())),
        out_of_cutoff_object_ids=out_of_cutoff_ids,
        future_obligation_keys=tuple(sorted(future_keys)),
        excluded_obligation_keys=tuple(sorted(excluded_keys)),
        visit_assignment_prepass=tuple(sorted(visit_prepass)),
        activity_assignment_prepass=tuple(sorted(activity_prepass)),
        scope_decisions=tuple(scope_decisions),
        cutoff=clinical_event_cutoff)


def _chained_anchor_gate(
    *, visit_key: str, subject_ref: str, site_ref: str,
    affected_activity_keys: Sequence[str],
) -> ScheduleGate:
    return ScheduleGate(
        gate_id="", gate_kind=GATE_ANCHOR, subject_ref=subject_ref,
        site_ref=site_ref, gate_state=GATE_OPEN,
        decision_status=GATE_DECISION_NOT_EVALUABLE,
        affected_planned_visit_keys=(visit_key,),
        affected_planned_activity_keys=_canonical_sorted(
            affected_activity_keys),
        missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
        reason_codes=(REASON_ANCHOR_MISSING,),
        source_locator_ids=())


def _predecessor_visit(
    visit: PlannedVisitDefinition,
    planned_visits: Sequence[PlannedVisitDefinition],
) -> Optional[PlannedVisitDefinition]:
    """The immediately previous scheduled visit by explicit planned_order
    (VISITNUM is never order authority)."""
    order = _order_key(visit.planned_order)
    candidates = [
        v for v in planned_visits
        if v.visit_kind == VISIT_SCHEDULED
        and v.planned_visit_key != visit.planned_visit_key
        and _order_key(v.planned_order) < order]
    if not candidates:
        return None
    return max(candidates, key=lambda v: _order_key(v.planned_order))


def _visit_key_of_activity(
    activity: PlannedActivityDefinition,
    planned_visits: Sequence[PlannedVisitDefinition],
) -> Optional[str]:
    for visit in planned_visits:
        if visit.planned_visit_id == activity.planned_visit_id:
            return visit.planned_visit_key
    return None


def _activity_prepass_unique(
    *, activity: PlannedActivityDefinition, visit_key: str,
    activity_assignment_ctx: ActivityAssignmentContext,
) -> bool:
    """True when any in-scope actual activity uniquely maps to this planned
    activity under the assignment algorithm (timing-unit existence)."""
    planned_of_visit = [
        a for a in activity_assignment_ctx.planned_activities
        if activity_assignment_ctx.planned_activity_visit_key.get(
            a.planned_activity_id, "") == visit_key]
    for actual in activity_assignment_ctx.actual_activities:
        if actual.activity_kind != activity.activity_kind:
            continue
        candidates, _ = _activity_candidate_keys(
            activity=actual, visit_key=visit_key,
            planned_activities=planned_of_visit,
            code_aliases=activity_assignment_ctx.code_aliases)
        if len(candidates) == 1 \
                and candidates[0].planned_activity_key \
                == activity.planned_activity_key:
            return True
    return False


def _build_visit_unit(
    *, unit_kind: str, visit: PlannedVisitDefinition,
    project_ref: str, subject_ref: str, site_ref: str,
    rule: Optional[EvaluationMaturityRule],
    anchor_day: str, window_rule: VisitWindowRule,
    anchor_episode_id: str, cutoff_day: Optional[datetime.date],
) -> Optional[ScheduleEvaluationUnit]:
    """One visit unit; None when the obligation is not matured at cutoff
    (future plan-axis only, §4.2)."""
    if rule is None:
        # Missing maturity rule: not_evaluable unit, never a default
        # window-latest endpoint (challenge 113).
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=visit, planned_activity=None,
            rule_id=visit.window_rule.window_rule_id,
            rule_version=visit.window_rule.rule_version,
            evaluation_window_id=_window_id(visit.window_rule,
                                            anchor_episode_id),
            anchor_episode_id=anchor_episode_id)
    if not anchor_day:
        return None  # anchor gate already accounts for the obligation
    window_id = _window_id(window_rule, anchor_episode_id)
    unit = _unit_for_kind(
        unit_kind=unit_kind, project_ref=project_ref,
        subject_ref=subject_ref, site_ref=site_ref,
        planned_visit=visit, planned_activity=None,
        rule_id=window_rule.window_rule_id,
        rule_version=window_rule.rule_version,
        evaluation_window_id=window_id,
        anchor_episode_id=anchor_episode_id)
    if unit is None:
        return None
    maturity_day = maturity_day_for(
        maturity_rule=rule, anchor_day=anchor_day,
        window_rule=window_rule)
    if maturity_day is None:
        return unit  # not_evaluable (maturity cannot be computed)
    maturity = _day_date(maturity_day)
    if maturity is None:
        return unit
    if cutoff_day is not None and maturity > cutoff_day:
        return None  # future obligation: plan axis only
    return unit


def _build_activity_unit(
    *, unit_kind: str, activity: PlannedActivityDefinition,
    project_ref: str, subject_ref: str, site_ref: str,
    rule: Optional[EvaluationMaturityRule],
    anchor_day: str, window_rule: Optional[VisitWindowRule],
    anchor_episode_id: str, cutoff_day: Optional[datetime.date],
) -> Optional[ScheduleEvaluationUnit]:
    rule_id = activity.timing_rule or activity.definition_hash
    if rule is None:
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=None, planned_activity=activity,
            rule_id=rule_id, rule_version=D05_RULE_LINEAGE_DEFAULT,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id)
    if not anchor_day or window_rule is None:
        # Anchor/activity window missing: keep a not_evaluable occurrence
        # unit (gap) instead of silently defaulting a window.
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=None, planned_activity=activity,
            rule_id=rule_id, rule_version=D05_RULE_LINEAGE_DEFAULT,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id)
    window_id = _window_id(window_rule, anchor_episode_id)
    unit = _unit_for_kind(
        unit_kind=unit_kind, project_ref=project_ref,
        subject_ref=subject_ref, site_ref=site_ref,
        planned_visit=None, planned_activity=activity,
        rule_id=window_rule.window_rule_id,
        rule_version=window_rule.rule_version,
        evaluation_window_id=window_id,
        anchor_episode_id=anchor_episode_id)
    if unit is None:
        return None
    maturity_day = maturity_day_for(
        maturity_rule=rule, anchor_day=anchor_day, window_rule=window_rule)
    if maturity_day is None:
        return unit
    maturity = _day_date(maturity_day)
    if maturity is None:
        return unit
    if cutoff_day is not None and maturity > cutoff_day:
        return None
    return unit


def _unit_for_kind(
    *, unit_kind: str, project_ref: str, subject_ref: str, site_ref: str,
    planned_visit: Optional[PlannedVisitDefinition],
    planned_activity: Optional[PlannedActivityDefinition],
    rule_id: str, rule_version: str, evaluation_window_id: str,
    anchor_episode_id: str,
) -> Optional[ScheduleEvaluationUnit]:
    try:
        return ScheduleEvaluationUnit(
            unit_id="", project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, unit_kind=unit_kind,
            planned_visit_key=planned_visit.planned_visit_key
            if planned_visit else "",
            planned_activity_key=planned_activity.planned_activity_key
            if planned_activity else "",
            evaluation_window_id=evaluation_window_id,
            anchor_episode_id=anchor_episode_id,
            rule_id=rule_id, rule_version=rule_version,
            planned_visit_id=planned_visit.planned_visit_id
            if planned_visit else "",
            planned_activity_id=planned_activity.planned_activity_id
            if planned_activity else "")
    except ScheduleSliceError:
        return None


def _build_assignment_unit(
    *, unit_kind: str, stable_actual_object_key: str,
    project_ref: str, subject_ref: str, site_ref: str,
    rule_id: str, anchor_episode_id: str,
) -> Optional[ScheduleEvaluationUnit]:
    try:
        return ScheduleEvaluationUnit(
            unit_id="", project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, unit_kind=unit_kind,
            stable_actual_object_key=stable_actual_object_key,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id,
            rule_id=rule_id, rule_version=D05_UNIT_ALGO_VERSION)
    except ScheduleSliceError:
        return None


def _window_id(window_rule: VisitWindowRule, anchor_episode_id: str) -> str:
    return schedule_evaluation_window_id(
        anchor_kind=window_rule.anchor_kind,
        anchor_source_role=window_rule.anchor_source_role,
        calendar_semantics=window_rule.calendar_semantics,
        study_day_zero_exists=window_rule.study_day_zero_exists,
        lower_offset=window_rule.lower_offset,
        upper_offset=window_rule.upper_offset,
        lower_endpoint_inclusive=window_rule.lower_endpoint_inclusive,
        upper_endpoint_inclusive=window_rule.upper_endpoint_inclusive,
        grace_period=window_rule.grace_period,
        date_precision=window_rule.date_precision,
        timezone=window_rule.timezone,
        propagation_rule=window_rule.propagation_rule,
        anchor_episode_id=anchor_episode_id)


def _dedupe_units(
    units: Sequence[ScheduleEvaluationUnit],
) -> List[ScheduleEvaluationUnit]:
    seen: Set[str] = set()
    result: List[ScheduleEvaluationUnit] = []
    for unit in units:
        if unit.unit_id in seen:
            continue
        seen.add(unit.unit_id)
        result.append(unit)
    return result
