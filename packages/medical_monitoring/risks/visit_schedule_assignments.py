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
    _bundle_interval_relation_to_day, _canonical_sorted, _day_date,
    _modality_for_encounter_kind, _repeat_multiplicity,
)

def _is_claim_code(code: str) -> bool:
    """True when a recorded visit code claims a planned visit; unscheduled
    tokens are explicit non-claims (§5.1 unplanned_supported path)."""
    code = (code or "").strip().upper()
    return bool(code) and code not in ("UNSCHEDULED", "UNPLANNED", "N/A")


def _visit_candidate_keys(
    *, bundle: ActualEncounterBundle, ctx: VisitAssignmentContext,
) -> Tuple[List[str], Dict[str, str], Set[str], bool]:
    """Candidate planned-visit keys for one bundle, per-candidate rejected
    reasons, applied predicate ids and a claim-complete flag.

    Never selects a winner by nearest date / VISITNUM / row order; the time
    window only excludes candidates that are determinately impossible
    (bundle entirely before the candidate's window start).
    """
    candidates: List[str] = []
    rejected: Dict[str, str] = {}
    applied: Set[str] = set()
    claim_complete = True

    # Predicate 1 -- verified explicit stable mapping / source parent key.
    explicit_keys: Set[str] = set()
    for mapping in ctx.explicit_mappings:
        if mapping.stable_actual_object_key == bundle.stable_actual_object_key \
                or (mapping.encounter_id
                    and mapping.encounter_id in bundle.member_encounter_ids):
            explicit_keys.add(mapping.planned_visit_key)
    if explicit_keys:
        applied.add(PRED_EXPLICIT_MAPPING)
        if len(explicit_keys) > 1:
            # Conflicting verified mappings: never choose by order/date.
            return [], {}, applied, True
        mapped_key = next(iter(explicit_keys))
        if mapped_key not in ctx.applicable_visit_keys:
            # The record claims a planned visit outside the unique
            # applicable plan: unassigned_inconsistent, never absorbed.
            return [], {mapped_key: REASON_SCHEDULE_MISSING}, applied, True
        return [mapped_key], {}, applied, True

    # Predicate 2 -- official visit code + verified alias mapping.
    codes: Set[str] = set()
    for member_id in bundle.member_encounter_ids:
        encounter = ctx.encounter_by_id.get(member_id)
        code = encounter.recorded_visit_code if encounter else ""
        if _is_claim_code(code):
            codes.add(code)
    official_keys: Set[str] = set()
    code_incomplete = False
    for code in sorted(codes):
        mapped_official: Set[str] = set()
        for mapping in ctx.code_mappings:
            if mapping.recorded_visit_code == code \
                    and mapping.protocol_version == ctx.protocol_version:
                mapped_official.add(mapping.official_visit_code)
        if not mapped_official:
            code_incomplete = True
            continue
        for official in mapped_official:
            for visit in ctx.planned_visits:
                if visit.official_visit_code == official \
                        and visit.planned_visit_key in ctx.applicable_visit_keys:
                    official_keys.add(visit.planned_visit_key)
    if codes and not code_incomplete:
        applied.add(PRED_OFFICIAL_CODE)
        if len(official_keys) > 1:
            # Two planned visits share the official code with equal other
            # evidence -> multi-feasible boundary, never nearest date.
            return sorted(official_keys), {}, applied, True
        if len(official_keys) == 1:
            return [next(iter(official_keys))], {}, applied, True
        # Codes mapped but no applicable visit carries the official code.
        return [], {c: REASON_SCHEDULE_MISSING for c in codes}, applied, \
            ctx.code_coverage_complete
    if codes and code_incomplete:
        applied.add(PRED_OFFICIAL_CODE)
        claim_complete = False
        candidates = sorted(official_keys)

    # No claim (no recorded claim code): every applicable visit is
    # possible under the remaining predicates; the caller decides
    # unplanned/not_evaluable.
    if not codes:
        candidates = sorted(ctx.applicable_visit_keys)

    # Predicate 3 -- phase/episode/modality compatibility.
    applied.add(PRED_PHASE_EPISODE_MODALITY)
    modality = _modality_for_encounter_kind(ctx.bundle_encounter_kind(bundle))
    surviving: List[str] = []
    for key in candidates:
        visit = ctx.visit_by_key(key)
        if visit is None:
            rejected[key] = REASON_SCHEDULE_MISSING
            continue
        reason = ""
        if modality and visit.allowed_modalities \
                and modality not in visit.allowed_modalities:
            reason = REASON_OTHER
        if not reason and bundle.assignment_scope == ASSIGNMENT_SCOPE_MULTI \
                and not visit.merge_or_split_rule.strip():
            reason = REASON_OTHER
        if reason:
            rejected[key] = reason
            continue
        surviving.append(key)
    candidates = surviving

    # Predicate 4 -- composition/scope rules (bundle membership authority
    # already validated by worker_01; nothing further to exclude here).

    # Predicate 5 -- window exclusion (only determinately impossible
    # candidates; never a nearest-date winner).
    if candidates:
        applied.add(PRED_WINDOW_EXCLUSION)
        lo_day, hi_day, complete = _bundle_interval_relation_to_day(bundle)
        if complete and lo_day is not None and hi_day is not None:
            surviving = []
            for key in candidates:
                visit = ctx.visit_by_key(key)
                anchor_day = ctx.anchor_day(key)
                if visit is None or not anchor_day:
                    surviving.append(key)
                    continue
                bounds = window_bounds(window_rule=visit.window_rule,
                                       anchor_day=anchor_day)
                if bounds.determinable and bounds.lo_day:
                    lo_bound = _day_date(bounds.lo_day)
                    if lo_bound is not None and hi_day < lo_bound:
                        # The whole encounter interval precedes the visit's
                        # earliest possible date: impossible candidate.
                        rejected[key] = REASON_TIME_ROLE_MISSING
                        continue
                surviving.append(key)
            candidates = surviving
    return candidates, rejected, applied, claim_complete


def resolve_visit_assignment(
    *, bundle: ActualEncounterBundle, ctx: VisitAssignmentContext,
) -> VisitAssignmentDecision:
    """One bundle -> planned visit assignment decision (§5.1)."""
    claims_visit = any(
        (ctx.encounter_by_id.get(mid) is not None
         and _is_claim_code(ctx.encounter_by_id[mid].recorded_visit_code))
        for mid in bundle.member_encounter_ids)
    # An explicitly unscheduled contact allowed by the plan is decided
    # before candidate resolution (§5.1 unplanned_supported): it never
    # competes with planned visits.
    explicitly_unscheduled = (
        ctx.allow_unscheduled_visits and not claims_visit and any(
            ctx.encounter_by_id.get(mid) is not None
            and (ctx.encounter_by_id[mid].encounter_kind
                 == ENCOUNTER_UNSCHEDULED
                 or not _is_claim_code(
                     ctx.encounter_by_id[mid].recorded_visit_code))
            for mid in bundle.member_encounter_ids))
    candidates, rejected, applied, claim_complete = _visit_candidate_keys(
        bundle=bundle, ctx=ctx)
    evidence_predicates = _canonical_sorted(applied)
    rejected_reasons = _canonical_sorted(rejected.values())

    if explicitly_unscheduled:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=(),
            decision_status=VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)

    if len(candidates) == 1:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=tuple(candidates),
            decision_status=VISIT_ASSIGNMENT_UNIQUE,
            selected_planned_visit_id=candidates[0],
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)
    if len(candidates) >= 2:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=tuple(candidates),
            decision_status=VISIT_ASSIGNMENT_MULTI_FEASIBLE,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)

    # Zero feasible candidates.
    evidence_complete = (
        ctx.mapping_coverage_complete and ctx.code_coverage_complete
        and claim_complete)
    if claims_visit and evidence_complete:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=(),
            decision_status=VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)
    return VisitAssignmentDecision(
        assignment_id="", subject_ref=ctx.subject_ref,
        actual_bundle_id=bundle.bundle_id,
        candidate_planned_visit_ids=(),
        decision_status=VISIT_ASSIGNMENT_NOT_EVALUABLE,
        evidence_predicate_ids=evidence_predicates,
        rejected_candidate_reasons=rejected_reasons,
        algorithm_version=D05_UNIT_ALGO_VERSION,
        source_locator_ids=bundle.source_locator_ids)


def resolve_visit_assignments(
    *, bundles: Sequence[ActualEncounterBundle],
    ctx: VisitAssignmentContext,
) -> Tuple[VisitAssignmentDecision, ...]:
    """All bundle -> visit assignment decisions (canonical order)."""
    return tuple(
        resolve_visit_assignment(bundle=bundle, ctx=ctx)
        for bundle in sorted(bundles, key=lambda b: b.bundle_id))


# ---------------------------------------------------------------------------
# Activity assignment (§7) + consumption ledger
# ---------------------------------------------------------------------------

def _activity_candidate_keys(
    *, activity: ActualActivityRecord, visit_key: str,
    planned_activities: Sequence[PlannedActivityDefinition],
    code_aliases: Sequence[OfficialActivityCodeAlias],
) -> Tuple[List[PlannedActivityDefinition], Dict[str, str]]:
    """Candidate planned activities already scoped to the assigned visit."""
    candidates: List[PlannedActivityDefinition] = []
    rejected: Dict[str, str] = {}
    for planned in planned_activities:
        if planned.owner_domain != OWNER_D05:
            continue
        if planned.activity_kind != activity.activity_kind:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        if planned.clinical_domain and activity.clinical_domain \
                and planned.clinical_domain != activity.clinical_domain:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        code_ok = (activity.recorded_activity_code
                   == planned.official_activity_code)
        if not code_ok:
            for alias in code_aliases:
                if alias.recorded_activity_code \
                        == activity.recorded_activity_code \
                        and alias.official_activity_code \
                        == planned.official_activity_code \
                        and alias.clinical_domain == planned.clinical_domain:
                    code_ok = True
                    break
        if not code_ok:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        candidates.append(planned)
    return candidates, rejected


def resolve_activity_assignment(
    *, activity: ActualActivityRecord, visit_key: str,
    ctx: ActivityAssignmentContext,
) -> Tuple[ActivityAssignmentDecision, ...]:
    """One actual activity -> planned activity assignment (§7.1/§7.2).

    Returns one decision for a single obligation and one decision per
    obligation for allowed repeat/resample multi-consumption (the closed
    ``unique`` status carries exactly one selected id; the consumption
    ledger aggregates the shared row, §7.2)."""
    if not visit_key:
        # No determinately assigned visit context for this activity.
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
            evidence_predicate_ids=(),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    planned_of_visit = [
        a for a in ctx.planned_activities
        if ctx.planned_activity_visit_key.get(a.planned_activity_id, "")
        == visit_key]
    candidates, _ = _activity_candidate_keys(
        activity=activity, visit_key=visit_key,
        planned_activities=planned_of_visit,
        code_aliases=ctx.code_aliases)
    if len(candidates) == 1:
        planned = candidates[0]
        repeat_ok = bool(planned.repeat_rule.strip())
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(planned.planned_activity_key,),
            decision_status=ACTIVITY_ASSIGNMENT_UNIQUE,
            selected_planned_activity_ids=(planned.planned_activity_key,),
            repeat_or_resample_parent_id=(
                planned.planned_activity_key if repeat_ok else ""),
            repeat_rule_id=(planned.repeat_rule if repeat_ok else ""),
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    if len(candidates) >= 2:
        all_repeat = all(bool(c.repeat_rule.strip()) for c in candidates)
        if all_repeat:
            # Allowed repeat/resample multi-consumption: one unique
            # decision per obligation; the ledger row aggregates them with
            # an explicit repeat rule (§7.2, challenges 61/110).
            decisions = []
            for planned in sorted(candidates,
                                  key=lambda c: c.planned_activity_key):
                decisions.append(ActivityAssignmentDecision(
                    assignment_id="", subject_ref=ctx.subject_ref,
                    actual_activity_id=activity.actual_activity_id,
                    candidate_planned_activity_ids=(
                        planned.planned_activity_key,),
                    decision_status=ACTIVITY_ASSIGNMENT_UNIQUE,
                    selected_planned_activity_ids=(
                        planned.planned_activity_key,),
                    repeat_or_resample_parent_id=planned.planned_activity_key,
                    repeat_rule_id=planned.repeat_rule,
                    evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
                    algorithm_version=D05_UNIT_ALGO_VERSION,
                    source_locator_ids=activity.source_locator_ids))
            return tuple(decisions)
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=tuple(
                sorted(c.planned_activity_key for c in candidates)),
            decision_status=ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
            selected_planned_activity_ids=tuple(
                sorted(c.planned_activity_key for c in candidates)),
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    # Zero candidates.
    unscheduled = ctx.allow_unscheduled_activities and (
        not activity.recorded_activity_code.strip()
        or "UNSCHED" in activity.recorded_activity_code.upper())
    if unscheduled:
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED,
            evidence_predicate_ids=(),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    if ctx.activity_evidence_complete \
            and activity.recorded_activity_code.strip():
        # Complete-evidence mislabel: the record claims a planned activity
        # that no applicable obligation matches.  Status is not_evaluable
        # (the closed activity-status set has no unassigned token) but the
        # reverse-coverage ledger stays open and the actual_assignment unit
        # evaluates positive (the issue predicate is true under every
        # feasible interpretation, §5.1).
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    return (ActivityAssignmentDecision(
        assignment_id="", subject_ref=ctx.subject_ref,
        actual_activity_id=activity.actual_activity_id,
        candidate_planned_activity_ids=(),
        decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
        evidence_predicate_ids=(),
        algorithm_version=D05_UNIT_ALGO_VERSION,
        source_locator_ids=activity.source_locator_ids),)


def resolve_activity_assignments(
    *, activities: Sequence[ActualActivityRecord],
    visit_key_by_activity: Mapping[str, str],
    ctx: ActivityAssignmentContext,
) -> Tuple[ActivityAssignmentDecision, ...]:
    """All actual-activity assignments (canonical order)."""
    decisions: List[ActivityAssignmentDecision] = []
    for activity in sorted(activities, key=lambda a: a.actual_activity_id):
        visit_key = visit_key_by_activity.get(activity.actual_activity_id, "")
        decisions.extend(resolve_activity_assignment(
            activity=activity, visit_key=visit_key, ctx=ctx))
    return tuple(decisions)


def build_consumption_ledgers(
    *,
    assignments: Sequence[ActivityAssignmentDecision],
    planned_activities: Sequence[PlannedActivityDefinition],
    site_ref: str,
) -> Tuple[ActualActivityConsumptionLedger, ...]:
    """Consumption ledgers (actual -> planned index) with reverse coverage
    status; the planned -> actual index is derived by the caller from these
    rows (§7.2)."""
    by_activity: Dict[str, List[ActivityAssignmentDecision]] = {}
    for decision in assignments:
        by_activity.setdefault(decision.actual_activity_id, []).append(decision)
    ledgers: List[ActualActivityConsumptionLedger] = []
    for actual_activity_id in sorted(by_activity):
        decisions = sorted(by_activity[actual_activity_id],
                           key=lambda d: d.assignment_id)
        consuming: Set[str] = set()
        repeat_rules: Set[str] = set()
        for decision in decisions:
            consuming.update(decision.selected_planned_activity_ids)
            if decision.repeat_rule_id:
                repeat_rules.update(decision.repeat_rule_id.split("|"))
        consuming_ids = _canonical_sorted(consuming)
        if not consuming_ids:
            continue  # unplanned/not_evaluable with no consumer
        multiplicity = max(
            1, max((_repeat_multiplicity(r) for r in repeat_rules),
                   default=1))
        if len(consuming_ids) > multiplicity:
            multiplicity = len(consuming_ids)
        repeat_rule_id = "|".join(sorted(repeat_rules))
        closed = len(consuming_ids) <= multiplicity and (
            len(consuming_ids) == 1 or bool(repeat_rule_id))
        ledgers.append(ActualActivityConsumptionLedger(
            ledger_id="", subject_ref=decisions[0].subject_ref,
            site_ref=site_ref, actual_activity_id=actual_activity_id,
            consuming_planned_activity_ids=consuming_ids,
            allowed_multiplicity=multiplicity,
            repeat_rule_id=repeat_rule_id,
            assignment_ids=tuple(sorted(
                d.assignment_id for d in decisions)),
            reverse_coverage_status=(
                REVERSE_COVERAGE_CLOSED if closed else REVERSE_COVERAGE_OPEN),
            source_locator_ids=_canonical_sorted(
                loc for d in decisions for loc in d.source_locator_ids)))
    return tuple(ledgers)
