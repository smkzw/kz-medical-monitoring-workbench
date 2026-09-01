"""R4-D05 visit-schedule evaluator slice tests (worker_02).

Focused deterministic tests for the D05 evaluation pipeline
(``FROZEN_R4_D05_CONTRACT_V1_2``) implemented in
:mod:`mm_r4.visit_schedule_evaluator`, consuming worker_01's immutable
domain surface (:mod:`mm_r4.visit_schedule`):

* Gate phase: applicability / routing / typed-anchor / cutoff-scope gates;
  an open gate never enters the medical expected-set and blocks domain
  completeness (challenges 6/7/74/77/101/102/105/106/112/116).
* Applicable expected-set: dual cutoff, maturity (window-latest endpoint
  vs future), not_applicable audit units, owner routing (challenges
  3/4/5/13/14/15/17/95/103/113).
* Bidirectional assignment: closed evidence-predicate order, never
  nearest-date / VISITNUM / row order (challenges 37-48); consumption
  ledgers with reverse coverage both directions (60/61/62/109/110).
* Five L1 dispositions with closed positive subtypes and Chinese audience
  labels (challenges 1/2/18-27/33/34/56-59/63-66/71/72/78).
* First-match priority policy: rights/safety hard-high and
  machine-close-forbidden (challenge 115); unknown never defaults low.
* Enrollment-aware three-part Chinese Query drafts (87/88/89/111).
* Shared lifecycle adapter integration (82/83/84/85): severity projection,
  machine-close proof, carry-forward.
* Determinism and accounting (35/36/85/97/98/99/107/114).

All data is synthetic and offline.  No real project, provider, fixed visit
number, fixed window, fixed table name, medication rule or service.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4 import visit_schedule as vs  # noqa: E402
from mm_r4 import visit_schedule_evaluator as vse  # noqa: E402
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    RiskInstanceRef,
    SourceLocator,
    cross_domain_evidence_content_hash,
)
from mm_r4.coverage import CoverageLedger, ExpectedSet  # noqa: E402
from mm_r4.fixtures import (  # noqa: E402
    make_acceptance_service,
    make_baseline_snapshot,
    make_lifecycle,
    make_subsequent_snapshot,
)
from mm_r4.lifecycle import R4LifecycleAdapter  # noqa: E402

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"
SUBJECT = "SYN-001"
ANCHOR_DAY = "2026-07-01"
CUTOFF = "2026-08-10"


# ===========================================================================
# Synthetic helpers
# ===========================================================================

def make_locator(
    record_id: str, table_semantic: str = "encounter",
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=SNAPSHOT_ID, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_snapshot() -> vs.SnapshotAsOf:
    return vs.SnapshotAsOf(
        snapshot_id=SNAPSHOT_ID, accepted_at="2026-08-12T06:00:00Z",
        source_revision_id=SOURCE_REV_ID)


def make_cutoff(cutoff: str = CUTOFF) -> vs.ClinicalEventCutoff:
    return vs.ClinicalEventCutoff(cutoff=cutoff, precision=vs.PRECISION_DAY)


def make_encounter(
    encounter_id: str = "enc-1", start: str = "2026-07-02",
    recorded_visit_code: str = "V4",
    encounter_kind: str = vs.ENCOUNTER_ONSITE,
    end: str = "", date_precision: str = vs.PRECISION_DAY,
    timezone: str = "",
) -> vs.ActualEncounterRecord:
    loc = make_locator(encounter_id)
    return vs.ActualEncounterRecord(
        encounter_id=encounter_id, stable_actual_object_key="",
        subject_ref=SUBJECT, site_ref=SITE_REF,
        source_record_keys=("encounter:" + encounter_id,),
        encounter_kind=encounter_kind,
        recorded_visit_code=recorded_visit_code,
        start=start, end=end or start, date_precision=date_precision,
        timezone=timezone, source_locator_ids=(loc.locator_id(),))


def make_activity(
    activity_id: str = "act-1", start: str = "2026-07-02",
    recorded_code: str = "ASSESS-1", activity_kind: str = vs.ACTIVITY_ASSESSMENT,
    clinical_domain: str = "efficacy", encounter_refs: Sequence[str] = (),
    end: str = "", date_precision: str = vs.PRECISION_DAY,
    timezone: str = "",
) -> vs.ActualActivityRecord:
    loc = make_locator(activity_id, "assessment")
    return vs.ActualActivityRecord(
        actual_activity_id=activity_id, stable_actual_object_key="",
        subject_ref=SUBJECT, site_ref=SITE_REF,
        source_record_keys=("assessment:" + activity_id,),
        activity_kind=activity_kind, clinical_domain=clinical_domain,
        recorded_activity_code=recorded_code,
        start=start, end=end or start, date_precision=date_precision,
        timezone=timezone, encounter_refs=encounter_refs,
        source_locator_ids=(loc.locator_id(),))


def make_window(
    lower: str = "-3", upper: str = "+3",
    study_day_zero_exists: Optional[bool] = True,
    lower_endpoint_inclusive: Optional[bool] = True,
    upper_endpoint_inclusive: Optional[bool] = False,
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
    window_rule_id: str = "wr-1",
) -> vs.VisitWindowRule:
    return vs.VisitWindowRule(
        window_rule_id=window_rule_id,
        anchor_kind=vs.RELATION_FIXED_REFERENCE,
        anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
        calendar_semantics=vs.STUDY_DAY,
        propagation_rule=vs.PROPAGATION_FIXED_ANCHOR,
        lower_offset=lower, upper_offset=upper,
        study_day_zero_exists=study_day_zero_exists,
        lower_endpoint_inclusive=lower_endpoint_inclusive,
        upper_endpoint_inclusive=upper_endpoint_inclusive,
        date_precision=date_precision, timezone=timezone)


def make_planned_visit(
    visit_id: str = "pv-v2-1", visit_key: str = "PV-KEY-1",
    official_code: str = "V4", audience_name: str = "第 4 周访视",
    planned_order: str = "4", visit_kind: str = vs.VISIT_SCHEDULED,
    window: Optional[vs.VisitWindowRule] = None,
    allowed_modalities: Sequence[str] = (vs.MODALITY_ONSITE,),
    merge_or_split_rule: str = "",
    plan_locator: Optional[SourceLocator] = None,
) -> vs.PlannedVisitDefinition:
    loc = plan_locator or make_locator("plan-" + visit_id, "plan_text")
    return vs.PlannedVisitDefinition(
        planned_visit_id=visit_id, planned_visit_key=visit_key,
        schedule_id="sched-1", protocol_version="V2.0",
        official_visit_code=official_code,
        audience_visit_name=audience_name, planned_order=planned_order,
        visit_kind=visit_kind, phase="treatment",
        applicability_expression="expr-1",
        anchor_rule=vs.VisitAnchorRule(
            anchor_kind=vs.RELATION_FIXED_REFERENCE,
            anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE),
        window_rule=window or make_window(),
        allowed_modalities=tuple(allowed_modalities),
        merge_or_split_rule=merge_or_split_rule,
        source_locator_ids=(loc.locator_id(),))


def make_planned_activity(
    activity_id: str = "pa-1", activity_key: str = "PA-KEY-1",
    visit_id: str = "pv-v2-1", activity_kind: str = vs.ACTIVITY_ASSESSMENT,
    clinical_domain: str = "efficacy", official_code: str = "ASSESS-1",
    audience_name: str = "疗效评估", repeat_rule: str = "",
    owner_domain: str = vs.OWNER_D05,
    timing_rule: str = "wr-1",
    specimen_or_method_role: str = "",
    plan_locator: Optional[SourceLocator] = None,
) -> vs.PlannedActivityDefinition:
    loc = plan_locator or make_locator("plan-" + activity_id, "plan_text")
    return vs.PlannedActivityDefinition(
        planned_activity_id=activity_id,
        planned_activity_key=activity_key, planned_visit_id=visit_id,
        activity_kind=activity_kind, clinical_domain=clinical_domain,
        official_activity_code=official_code, audience_name=audience_name,
        applicability_expression="expr-1", occurrence_rule="once",
        timing_rule=timing_rule, repeat_rule=repeat_rule,
        specimen_or_method_role=specimen_or_method_role,
        owner_domain=owner_domain,
        source_locator_ids=(loc.locator_id(),))


def make_applicability(
    status: str = vs.APPLICABILITY_UNIQUE_ACTIVE,
    protocol_version: str = "V2.0",
    feasible: Sequence[str] = ("sched-1",),
    reasons: Sequence[str] = (),
    cutoff: Optional[vs.ClinicalEventCutoff] = None,
) -> vs.VisitScheduleApplicabilityDecision:
    return vs.VisitScheduleApplicabilityDecision(
        decision_id="", project_ref=PROJECT_ID, subject_ref=SUBJECT,
        site_ref=SITE_REF, protocol_version=protocol_version,
        arm="A", cohort="C1", phase="treatment",
        transition_rule=vs.TRANSITION_ALL_SWITCH,
        cutoff=cutoff or make_cutoff(),
        decision_status=status, feasible_schedule_ids=feasible,
        reason_codes=reasons)


def make_maturity(
    unit_kind: str, expression: str = "window_latest_endpoint",
) -> vs.EvaluationMaturityRule:
    return vs.EvaluationMaturityRule(
        maturity_rule_id="mr-" + unit_kind, unit_kind=unit_kind,
        anchor_kind=vs.RELATION_FIXED_REFERENCE,
        anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
        maturity_expression=expression, cutoff_precision=vs.PRECISION_DAY)


def make_policy(
    impact: str = vse.IMPACT_OTHER_REQUIRED,
    recurrence: str = vse.RECURRENCE_SINGLE,
    recoverability: str = vse.RECOVERABILITY_RECOVERABLE,
    actionability: str = vse.ACTIONABILITY_ACTIONABLE,
) -> vse.D05PriorityPolicy:
    return vse.D05PriorityPolicy(
        policy_id="", impact_class=impact, recurrence_class=recurrence,
        recoverability=recoverability, actionability=actionability)


def make_enrollment(
    enrolled: Optional[bool] = True,
) -> vse.EnrollmentEvidence:
    if enrolled is True:
        return vse.EnrollmentEvidence(
            subject_ref=SUBJECT, randomized_or_enrolled=True,
            received_study_intervention=True, coverage_complete=True)
    if enrolled is False:
        return vse.EnrollmentEvidence(
            subject_ref=SUBJECT, randomized_or_enrolled=False,
            received_study_intervention=False, coverage_complete=True)
    return vse.EnrollmentEvidence(subject_ref=SUBJECT)


def make_bundle(
    *encounters: vs.ActualEncounterRecord,
    episode_kind: Optional[str] = None,
    assignment_scope: str = vs.ASSIGNMENT_SCOPE_SINGLE,
    merge_or_split_rule_id: str = "",
) -> vs.ActualEncounterBundle:
    return vs.build_actual_encounter_bundle(
        member_encounters=tuple(encounters), subject_ref=SUBJECT,
        site_ref=SITE_REF,
        episode_kind=episode_kind or (
            vs.EPISODE_MULTI_CONTACT if len(encounters) > 1
            else vs.EPISODE_SINGLE_CONTACT),
        assignment_scope=assignment_scope,
        merge_or_split_rule_id=merge_or_split_rule_id)


def make_anchor_binding(
    visit_key: str = "PV-KEY-1",
    relation_type: str = vs.RELATION_FIXED_REFERENCE,
    anchor_day: str = ANCHOR_DAY,
    producer_ref: Optional[vs.CrossDomainEvidenceRef] = None,
    **kw: Any,
) -> vse.AnchorBindingRequest:
    if relation_type != vs.RELATION_FIXED_REFERENCE:
        anchor_day = ""
    return vse.AnchorBindingRequest(
        planned_visit_key=visit_key, relation_type=relation_type,
        producer_ref=producer_ref, anchor_day=anchor_day,
        phase=kw.get("phase", "treatment"),
        episode_id=kw.get("episode_id", "ep-1"),
        producer_domain=kw.get("producer_domain", ""),
        producer_unit_id=kw.get("producer_unit_id", ""),
        stable_source_event_key=kw.get("stable_source_event_key", ""),
        content_hash=kw.get("content_hash", ""),
        anchor_start=kw.get("anchor_start", ""),
        anchor_end=kw.get("anchor_end", ""),
        date_precision=kw.get("date_precision", vs.PRECISION_DAY),
        timezone=kw.get("timezone", ""),
        affected_planned_activity_keys=kw.get(
            "affected_planned_activity_keys", ()))


def make_producer_ref(
    *,
    producer_domain: str = vs.OWNER_D03,
    evidence_role: str = "first_dose",
    producer_unit_id: str = "ip-unit-1",
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    phase: str = "treatment", episode_id: str = "ep-1",
    anchor_start: str = "2026-06-30", anchor_end: str = "2026-06-30",
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
    record_id: str = "cd-1",
    relation_type: str = vs.RELATION_FIRST_IP_DOSE,
) -> vs.CrossDomainEvidenceRef:
    loc = make_locator(record_id, "ip_exposure")
    ctx = (
        ("subject_ref", subject_ref), ("site_ref", site_ref),
        ("phase", phase), ("episode_id", episode_id),
        ("anchor_start", anchor_start), ("anchor_end", anchor_end),
        ("date_precision", date_precision), ("timezone", timezone),
        ("relation_type", relation_type),
    )
    return vs.CrossDomainEvidenceRef(
        evidence_ref_id="cd-ref-1", producer_domain=producer_domain,
        consumer_domain=vs.D05_DOMAIN, evidence_role=evidence_role,
        source_locator=loc, producer_unit_id=producer_unit_id,
        content_hash=cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role=evidence_role,
            claim_scope="", context_payload=dict(ctx)),
        claim_scope="", context_payload=ctx)


def record_locators(*records: Any) -> Mapping[str, SourceLocator]:
    locs: dict = {}
    for record in records:
        object_id = getattr(record, "encounter_id", "") or getattr(
            record, "actual_activity_id", "")
        if object_id:
            locs[object_id] = make_locator(object_id)
    return locs


def run_evaluation(
    visits: Sequence[vs.PlannedVisitDefinition] = (),
    activities: Sequence[vs.PlannedActivityDefinition] = (),
    encounters: Sequence[vs.ActualEncounterRecord] = (),
    actual_activities: Sequence[vs.ActualActivityRecord] = (),
    bundles: Sequence[vs.ActualEncounterBundle] = (),
    anchor_bindings: Optional[Sequence[vse.AnchorBindingRequest]] = None,
    maturity_rules: Optional[Mapping[str, vs.EvaluationMaturityRule]] = None,
    priority_policies: Optional[Mapping[str, vse.D05PriorityPolicy]] = None,
    assignment_priority_policy: Optional[vse.D05PriorityPolicy] = None,
    applicability: Optional[vs.VisitScheduleApplicabilityDecision] = None,
    cutoff: Optional[vs.ClinicalEventCutoff] = None,
    code_mappings: Optional[Sequence[vse.OfficialCodeMapping]] = None,
    explicit_mappings: Sequence[vse.StableVisitMapping] = (),
    activity_window_rules: Optional[Mapping[str, vs.VisitWindowRule]] = None,
    obligation_applicability: Optional[
        Mapping[str, vse.ObligationApplicability]] = None,
    source_coverage: Optional[Mapping[str, bool]] = None,
    enrollment: Optional[vse.EnrollmentEvidence] = None,
    schedule_consistency_issues: Sequence[vse.ScheduleConsistencyIssue] = (),
    plan_locators: Sequence[SourceLocator] = (),
    allow_unscheduled_visits: bool = False,
    allow_unscheduled_activities: bool = False,
    mapping_coverage_complete: bool = True,
    code_coverage_complete: bool = True,
    prior_resolved_gates: Sequence[vs.ScheduleGate] = (),
    **kw: Any,
) -> vse.D05EvaluationOutcome:
    visits = tuple(visits)
    if anchor_bindings is None:
        anchor_bindings = tuple(
            vse.AnchorBindingRequest(
                planned_visit_key=v.planned_visit_key,
                relation_type=vs.RELATION_FIXED_REFERENCE,
                anchor_day=ANCHOR_DAY)
            for v in visits)
    if maturity_rules is None:
        maturity_rules = {
            k: make_maturity(k)
            for k in (vs.UNIT_VISIT_OCCURRENCE, vs.UNIT_VISIT_TIMING,
                      vs.UNIT_VISIT_ORDER, vs.UNIT_ACTIVITY_OCCURRENCE,
                      vs.UNIT_ACTIVITY_TIMING)}
    if priority_policies is None:
        priority_policies = {
            v.planned_visit_key: make_policy() for v in visits}
    if code_mappings is None:
        code_mappings = tuple(
            vse.OfficialCodeMapping(
                recorded_visit_code=v.official_visit_code,
                official_visit_code=v.official_visit_code,
                protocol_version=v.protocol_version)
            for v in visits)
    locs = record_locators(*encounters, *actual_activities)
    if not plan_locators:
        plan_locators = tuple(
            make_locator("plan-" + v.planned_visit_id, "plan_text")
            for v in visits)
    return vse.evaluate_visit_schedule_run(
        run_id="run-1", project_ref=PROJECT_ID, subject_ref=SUBJECT,
        site_ref=SITE_REF, snapshot_as_of=make_snapshot(),
        clinical_event_cutoff=cutoff or make_cutoff(),
        applicability_decision=applicability or make_applicability(),
        planned_visits=visits, planned_activities=tuple(activities),
        maturity_rules=maturity_rules, anchor_bindings=anchor_bindings,
        encounters=tuple(encounters), activities=tuple(actual_activities),
        bundles=tuple(bundles), record_locators=locs,
        plan_locators=plan_locators,
        explicit_visit_mappings=explicit_mappings,
        official_code_mappings=code_mappings,
        activity_window_rules=activity_window_rules or {},
        obligation_applicability=obligation_applicability or {},
        priority_policies=priority_policies,
        assignment_priority_policy=assignment_priority_policy,
        source_coverage=source_coverage or {},
        enrollment=enrollment or make_enrollment(True),
        schedule_consistency_issues=schedule_consistency_issues,
        allow_unscheduled_visits=allow_unscheduled_visits,
        allow_unscheduled_activities=allow_unscheduled_activities,
        mapping_coverage_complete=mapping_coverage_complete,
        code_coverage_complete=code_coverage_complete,
        prior_resolved_gates=prior_resolved_gates,
        **kw)


def result_for(outcome: vse.D05EvaluationOutcome, unit_kind: str,
               key: str = "") -> vse.D05UnitResult:
    for result in outcome.unit_results:
        if result.unit_kind != unit_kind:
            continue
        if key and result.planned_visit_key != key \
                and result.planned_activity_key != key:
            continue
        return result
    raise AssertionError(
        f"no unit result kind={unit_kind!r} key={key!r}; "
        f"kinds={[r.unit_kind for r in outcome.unit_results]}")


def result_by_key(outcome: vse.D05EvaluationOutcome,
                  key: str) -> vse.D05UnitResult:
    for result in outcome.unit_results:
        if result.planned_visit_key == key \
                or result.planned_activity_key == key:
            return result
    raise AssertionError(f"no result for key {key!r}")


# ===========================================================================
# 1. Priority policy (§9.1)
# ===========================================================================

class TestPriorityPolicy:
    def test_step1_rights_safety_always_high_and_close_forbidden(self):
        verdict = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_RIGHTS_SAFETY))
        assert verdict.priority == "high"
        assert verdict.machine_close_forbidden is True
        assert verdict.rights_or_safety_critical is True
        assert verdict.precedence_step == 1

    def test_step1_critical_treatment_high_close_forbidden(self):
        verdict = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_CRITICAL_TREATMENT))
        assert verdict.priority == "high"
        assert verdict.machine_close_forbidden is True
        assert verdict.rights_or_safety_critical is False
        assert verdict.precedence_step == 1

    def test_step1_unknown_actionability_keeps_high_with_note(self):
        """Challenge 115: unknown actionability/recoverability must not
        downgrade a determined safety priority; it only adds a coverage
        note."""
        verdict = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_RIGHTS_SAFETY,
            actionability=vse.ACTIONABILITY_UNKNOWN,
            recoverability=vse.RECOVERABILITY_UNKNOWN))
        assert verdict.priority == "high"
        assert verdict.machine_close_forbidden is True
        assert verdict.coverage_note  # coverage/context prompt kept

    def test_step2_unknown_never_defaults_low(self):
        for impact in (vse.IMPACT_PRIMARY_ENDPOINT,
                       vse.IMPACT_ADMINISTRATIVE):
            verdict = vse.resolve_d05_priority(make_policy(
                impact=impact, recoverability=vse.RECOVERABILITY_UNKNOWN))
            assert verdict.priority == "unknown"
            assert verdict.precedence_step == 2
            assert not verdict.machine_close_forbidden
            verdict2 = vse.resolve_d05_priority(make_policy(
                impact=impact, actionability=vse.ACTIONABILITY_CONTEXT_ONLY))
            assert verdict2.priority == "unknown"

    def test_step3_primary_endpoint(self):
        medium = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_PRIMARY_ENDPOINT,
            recoverability=vse.RECOVERABILITY_RECOVERABLE))
        assert medium.priority == "medium"
        high = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_PRIMARY_ENDPOINT,
            recoverability=vse.RECOVERABILITY_IRRECOVERABLE))
        assert high.priority == "high"

    def test_step4_other_required_escalations(self):
        base = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_OTHER_REQUIRED))
        assert base.priority == "medium"
        site = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_OTHER_REQUIRED,
            recurrence=vse.RECURRENCE_REPEATED_SITE))
        assert site.priority == "high"
        irrecoverable = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_KEY_SECONDARY_ENDPOINT,
            recoverability=vse.RECOVERABILITY_IRRECOVERABLE))
        assert irrecoverable.priority == "high"

    def test_step5_administrative_low_only_single_recoverable_actionable(self):
        low = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_ADMINISTRATIVE))
        assert low.priority == "low"
        subject = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_ADMINISTRATIVE,
            recurrence=vse.RECURRENCE_REPEATED_SUBJECT))
        assert subject.priority == "medium"
        site = vse.resolve_d05_priority(make_policy(
            impact=vse.IMPACT_ADMINISTRATIVE,
            recurrence=vse.RECURRENCE_REPEATED_SITE))
        assert site.priority == "high"

    def test_closed_enum_fails_at_construction(self):
        with pytest.raises(vse.VisitScheduleEvaluatorError):
            make_policy(impact="free_text_grade")
        with pytest.raises(vse.VisitScheduleEvaluatorError):
            make_policy(recoverability="maybe")

    def test_policy_and_verdict_content_addressed(self):
        p1 = make_policy()
        p2 = make_policy()
        assert p1.policy_id == p2.policy_id
        assert p1.hash == p2.hash
        v1 = vse.resolve_d05_priority(p1)
        v2 = vse.resolve_d05_priority(p2)
        assert v1.hash == v2.hash


# ===========================================================================
# 2. Enrollment-aware Query context (§9.2)
# ===========================================================================

class TestEnrollmentContext:
    def test_enrolled(self):
        ctx = vse.resolve_d05_enrollment_context(evidence=make_enrollment(True))
        assert ctx.query_context == vse.QUERY_CONTEXT_ENROLLED

    def test_not_occurred(self):
        ctx = vse.resolve_d05_enrollment_context(evidence=make_enrollment(False))
        assert ctx.query_context == vse.QUERY_CONTEXT_NOT_OCCURRED

    def test_unresolved(self):
        ctx = vse.resolve_d05_enrollment_context(
            evidence=vse.EnrollmentEvidence(subject_ref=SUBJECT))
        assert ctx.query_context == vse.QUERY_CONTEXT_UNRESOLVED

    def test_incomplete_coverage_never_enrolled(self):
        evidence = vse.EnrollmentEvidence(
            subject_ref=SUBJECT, randomized_or_enrolled=True,
            received_study_intervention=True, coverage_complete=False)
        ctx = vse.resolve_d05_enrollment_context(evidence=evidence)
        assert ctx.query_context == vse.QUERY_CONTEXT_UNRESOLVED

    def test_disposition_only_never_implies_enrolled(self):
        """Corrective §9.2: a generic disposition record alone does not
        prove enrollment -- even with complete coverage, disposition-only
        evidence is unresolved (never enrolled PD wording)."""
        evidence = vse.EnrollmentEvidence(
            subject_ref=SUBJECT, disposition_recorded=True,
            coverage_complete=True)
        ctx = vse.resolve_d05_enrollment_context(evidence=evidence)
        assert ctx.query_context == vse.QUERY_CONTEXT_UNRESOLVED
        assert "方案偏离" not in vse._action_suffix(ctx.query_context)

    def test_screen_failure_disposition_with_both_false_is_not_occurred(self):
        """Corrective §9.2: a screen-failure-like disposition with both
        randomization/enrollment and study intervention explicitly false
        and complete coverage -> enrollment_not_occurred."""
        evidence = vse.EnrollmentEvidence(
            subject_ref=SUBJECT, randomized_or_enrolled=False,
            received_study_intervention=False, disposition_recorded=True,
            coverage_complete=True)
        ctx = vse.resolve_d05_enrollment_context(evidence=evidence)
        assert ctx.query_context == vse.QUERY_CONTEXT_NOT_OCCURRED

    def test_disposition_only_incomplete_coverage_unresolved(self):
        """Corrective §9.2: disposition-only with incomplete coverage is
        unresolved, never enrolled and never not_occurred."""
        evidence = vse.EnrollmentEvidence(
            subject_ref=SUBJECT, disposition_recorded=True,
            coverage_complete=False)
        ctx = vse.resolve_d05_enrollment_context(evidence=evidence)
        assert ctx.query_context == vse.QUERY_CONTEXT_UNRESOLVED

    def test_disposition_only_with_randomization_false_is_unresolved(self):
        """Corrective §9.2: randomization explicitly false but intervention
        unknown and a disposition present -> not determinate -> unresolved
        (only both-false + complete coverage means not_occurred)."""
        evidence = vse.EnrollmentEvidence(
            subject_ref=SUBJECT, randomized_or_enrolled=False,
            disposition_recorded=True, coverage_complete=True)
        ctx = vse.resolve_d05_enrollment_context(evidence=evidence)
        assert ctx.query_context == vse.QUERY_CONTEXT_UNRESOLVED


# ===========================================================================
# 3. Expected-set, gates and dual cutoff (§4, §3.3)
# ===========================================================================

class TestExpectedSetAndGates:
    def _visit(self):
        return make_planned_visit()

    def test_applicability_gate_only_when_not_unique(self):
        """Challenges 6/7/106: non-unique applicability -> exactly one
        subject-level gate, zero expected units, domain blocked."""
        for status, feasible, reasons in (
            (vs.APPLICABILITY_NOT_EVALUABLE, (), (vs.REASON_VERSION_MISSING,)),
            (vs.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY, ("sched-1", "sched-2"),
             (vs.REASON_MULTIPLE_FEASIBLE,)),
        ):
            appl = make_applicability(status=status, feasible=feasible,
                                      reasons=reasons)
            outcome = run_evaluation(visits=[self._visit()],
                                     applicability=appl)
            assert len(outcome.gates) == 1
            assert outcome.gates[0].gate_kind == vs.GATE_APPLICABILITY
            assert outcome.gates[0].gate_state == vs.GATE_OPEN
            assert len(outcome.expected_units) == 0
            assert outcome.gates_block_domain()
            # Corrective: an open applicability gate must also make the
            # authoritative domain_complete verdict incomplete.
            assert outcome.domain_complete[0] is False
            assert any("open ScheduleGate" in r
                       for r in outcome.domain_complete[1])

    def test_routing_gate_blocks_owner_unresolved_activities(self):
        """Challenge 105: one control-plane routing gate, no medical
        expected-set for the affected activities."""
        visit = self._visit()
        routed = make_planned_activity(
            activity_key="PA-ROUTE", owner_domain=vs.OWNER_UNRESOLVED)
        outcome = run_evaluation(
            visits=[visit], activities=[routed],
            anchor_bindings=[make_anchor_binding(visit_key="PV-KEY-1")],
            activity_window_rules={"PA-ROUTE": make_window()})
        gate = next(g for g in outcome.gates
                    if g.gate_kind == vs.GATE_ROUTING)
        assert gate.gate_state == vs.GATE_OPEN
        assert "PA-ROUTE" in gate.affected_planned_activity_keys
        assert outcome.excluded_obligation_keys == ("PA-ROUTE",)
        assert "PA-ROUTE" not in {
            u.planned_activity_key for u in outcome.expected_units}
        # Corrective: an open routing gate blocks the medical domain.
        assert outcome.gates_block_domain()
        assert outcome.domain_complete[0] is False
        assert any("open ScheduleGate" in r
                   for r in outcome.domain_complete[1])

    def test_producer_owned_activity_excluded_not_routed(self):
        visit = self._visit()
        owned = make_planned_activity(
            activity_key="PA-D06", owner_domain=vs.OWNER_D06)
        outcome = run_evaluation(
            visits=[visit], activities=[owned],
            anchor_bindings=[make_anchor_binding(visit_key="PV-KEY-1")])
        assert not any(g.gate_kind == vs.GATE_ROUTING for g in outcome.gates)
        assert "PA-D06" in outcome.excluded_obligation_keys

    def test_missing_anchor_gate_no_downstream_units(self):
        """Challenges 101: missing chained anchor -> single anchor gate;
        dependent obligations never enter the normal expected-set."""
        first = make_planned_visit(
            visit_id="pv-a", visit_key="PV-A", official_code="V1",
            audience_name="第 1 周访视", planned_order="1")
        second = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2")
        bindings = [
            make_anchor_binding(visit_key="PV-A"),
            make_anchor_binding(visit_key="PV-B",
                                relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
        ]
        outcome = run_evaluation(
            visits=[first, second], anchor_bindings=bindings,
            priority_policies={"PV-A": make_policy(), "PV-B": make_policy()})
        anchor_gates = [g for g in outcome.gates
                        if g.gate_kind == vs.GATE_ANCHOR]
        assert len(anchor_gates) == 1
        assert anchor_gates[0].decision_status == vs.GATE_DECISION_NOT_EVALUABLE
        assert vs.REASON_ANCHOR_MISSING in anchor_gates[0].reason_codes
        assert anchor_gates[0].feasible_anchor_ref_ids == ()
        assert "PV-B" in anchor_gates[0].affected_planned_visit_keys
        assert "PV-B" not in {u.planned_visit_key
                              for u in outcome.expected_units}
        assert "PV-A" in {u.planned_visit_key
                          for u in outcome.expected_units}
        # Corrective: an open anchor gate blocks the medical domain even
        # though the unaffected visit evaluated.
        assert outcome.gates_block_domain()
        assert outcome.domain_complete[0] is False
        assert any("open ScheduleGate" in r
                   for r in outcome.domain_complete[1])

    def test_exact_producer_anchor_binding_and_wrong_phase_gate(self):
        """Challenges 73/112: exact typed producer binding works; a
        same-day ref with wrong phase/episode fails closed to an anchor
        gate (never a date-neighbour substitution)."""
        ref = make_producer_ref()
        binding_ok = vse.AnchorBindingRequest(
            planned_visit_key="PV-KEY-1", relation_type=vs.RELATION_FIRST_IP_DOSE,
            producer_ref=ref, producer_domain=vs.OWNER_D03,
            producer_unit_id="ip-unit-1",
            stable_source_event_key="ip_exposure:cd-1",
            content_hash=ref.content_hash, phase="treatment",
            episode_id="ep-1", anchor_start="2026-06-30",
            anchor_end="2026-06-30", date_precision=vs.PRECISION_DAY)
        outcome = run_evaluation(
            visits=[self._visit()], anchor_bindings=[binding_ok])
        assert not any(g.gate_kind == vs.GATE_ANCHOR for g in outcome.gates)
        assert outcome.anchor_day_by_visit_key == (
            ("PV-KEY-1", "2026-06-30"),)
        # Wrong phase on a same-day ref -> anchor gate (never a
        # date-neighbour substitution).
        ref_wrong = make_producer_ref(phase="screening")
        binding_bad = vse.AnchorBindingRequest(
            planned_visit_key="PV-KEY-1", relation_type=vs.RELATION_FIRST_IP_DOSE,
            producer_ref=ref_wrong, producer_domain=vs.OWNER_D03,
            producer_unit_id="ip-unit-1",
            stable_source_event_key="ip_exposure:cd-1",
            content_hash=ref_wrong.content_hash, phase="treatment",
            episode_id="ep-1", anchor_start="2026-06-30",
            anchor_end="2026-06-30", date_precision=vs.PRECISION_DAY)
        outcome_bad = run_evaluation(
            visits=[self._visit()], anchor_bindings=[binding_bad])
        assert any(g.gate_kind == vs.GATE_ANCHOR for g in outcome_bad.gates)
        assert len(outcome_bad.expected_units) == 0

    def test_future_obligation_not_in_expected_set(self):
        """Challenges 4/5: window still open or planned date after cutoff
        -> plan axis only, never an L1 denominator."""
        visit = self._visit()
        outcome = run_evaluation(visits=[visit], cutoff=make_cutoff("2026-07-02"))
        assert len(outcome.expected_units) == 0
        assert outcome.future_obligation_keys == ("PV-KEY-1",)

    def test_not_applicable_audit_unit_with_authority(self):
        """Challenges 13/15: locatable phase end / death -> not_applicable
        audit unit, no occurrence/timing medical units."""
        appl = vse.ObligationApplicability(
            obligation_key="PV-KEY-1", applicable=False,
            reason_code=vs.REASON_SCHEDULE_MISSING)
        outcome = run_evaluation(
            visits=[self._visit()],
            obligation_applicability={"PV-KEY-1": appl})
        results = [r for r in outcome.unit_results
                   if r.planned_visit_key == "PV-KEY-1"]
        assert results and all(
            r.l1_disposition == L1Disposition.NOT_APPLICABLE
            for r in results)
        assert outcome.candidates == ()

    def test_missing_data_never_infers_not_applicable(self):
        """Challenge 14: no further data is not early termination."""
        outcome = run_evaluation(visits=[self._visit()])
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE)
        assert occ.l1_disposition == L1Disposition.POSITIVE  # missing, not N/A

    def test_missing_maturity_rule_not_evaluable_not_default(self):
        """Challenge 113: missing occurrence maturity rule -> not_evaluable
        with gap, never a default window-latest endpoint."""
        outcome = run_evaluation(
            visits=[self._visit()], maturity_rules={
                vs.UNIT_VISIT_TIMING: make_maturity(vs.UNIT_VISIT_TIMING),
                vs.UNIT_VISIT_ORDER: make_maturity(vs.UNIT_VISIT_ORDER)})
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE)
        assert occ.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert occ.not_evaluable_reason == vs.REASON_MATURITY_RULE_MISSING
        assert len(outcome.coverage_gap_notices) == 1

    def test_out_of_cutoff_encounter_excluded_from_assignment(self):
        """Challenge 103: accepted-snapshot record after cutoff only goes
        to Journey future context; never assignment/L1."""
        encounter = make_encounter(start="2026-09-01")
        scope = vs.resolve_actual_record_scope(
            record=encounter, snapshot_as_of=make_snapshot(),
            clinical_event_cutoff=make_cutoff(),
            source_locators=(make_locator("enc-1"),))
        assert scope.scope_status == vs.SCOPE_OUT_OF_CUTOFF
        bundle = make_bundle(encounter)
        outcome = run_evaluation(
            visits=[self._visit()], encounters=[encounter],
            bundles=[bundle], code_mappings=())
        assert outcome.out_of_cutoff_object_ids == ("enc-1",)
        assert not any(a.actual_bundle_id == bundle.bundle_id
                       for a in outcome.visit_assignments)
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE)
        assert occ.l1_disposition == L1Disposition.POSITIVE  # still missing

    def test_scope_gate_blocks_false_missing_positive(self):
        """A boundary/not_evaluable scope record means 'complete absence'
        is not established: occurrence must not claim visit_missing."""
        encounter = make_encounter(
            start="2026-07-02", date_precision=vs.PRECISION_MONTH,
            end="2026-08")
        scope = vs.resolve_actual_record_scope(
            record=encounter, snapshot_as_of=make_snapshot(),
            clinical_event_cutoff=make_cutoff(),
            source_locators=(make_locator("enc-1"),))
        assert scope.scope_status == vs.SCOPE_BOUNDARY
        outcome = run_evaluation(
            visits=[self._visit()], encounters=[encounter],
            code_mappings=())
        assert any(g.gate_kind == vs.GATE_CUTOFF_SCOPE for g in outcome.gates)
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE)
        assert occ.l1_disposition == L1Disposition.NOT_EVALUABLE
        # Corrective: an open cutoff-scope gate blocks the medical domain.
        assert outcome.gates_block_domain()
        assert outcome.domain_complete[0] is False
        assert any("open ScheduleGate" in r
                   for r in outcome.domain_complete[1])

    def test_prior_resolved_gate_accounting(self):
        """Challenge 116 (closed branch): a prior closed/resolved gate is
        counted but does not block."""
        prior = vs.ScheduleGate(
            gate_id="", gate_kind=vs.GATE_ANCHOR, subject_ref=SUBJECT,
            site_ref=SITE_REF, gate_state=vs.GATE_CLOSED,
            decision_status=vs.GATE_DECISION_RESOLVED,
            prior_gate_id="d05-gate-old", resolved_by_decision_id="d05-dec-1",
            source_locator_ids=())
        outcome = run_evaluation(
            visits=[self._visit()], prior_resolved_gates=[prior])
        assert outcome.gate_accounting.closed_resolved == 1
        assert not outcome.gates_block_domain()
        # Corrective: a closed/resolved gate does NOT block completeness.
        assert outcome.domain_complete == (True, [])


# ===========================================================================
# 4. Visit assignment (§5.1)
# ===========================================================================

class TestVisitAssignment:
    def _two_visits(self):
        return (
            make_planned_visit(
                visit_id="pv-v2-0", visit_key="PV-KEY-0", official_code="V3",
                audience_name="第 3 周访视", planned_order="3"),
            make_planned_visit(
                visit_id="pv-v2-1", visit_key="PV-KEY-1", official_code="V4",
                audience_name="第 4 周访视", planned_order="4"),
        )

    def test_explicit_mapping_unique(self):
        """Challenge 37: verified stable explicit mapping wins."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-02", recorded_visit_code="V3")
        bundle = make_bundle(enc)
        mapping = vse.StableVisitMapping(
            planned_visit_key="PV-KEY-1",
            stable_actual_object_key=bundle.stable_actual_object_key)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            explicit_mappings=[mapping],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        decision = outcome.visit_assignments[0]
        assert decision.decision_status == vs.VISIT_ASSIGNMENT_UNIQUE
        assert decision.selected_planned_visit_id == "PV-KEY-1"
        assert vse.PRED_EXPLICIT_MAPPING in decision.evidence_predicate_ids

    def test_official_code_unique(self):
        """Challenge 38: official code + version/phase consistent -> unique."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-02", recorded_visit_code="V4")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        decision = outcome.visit_assignments[0]
        assert decision.decision_status == vs.VISIT_ASSIGNMENT_UNIQUE
        assert decision.selected_planned_visit_id == "PV-KEY-1"

    def test_nearest_date_never_absorbs(self):
        """Challenge 39: date nearest to V3 but code V4 -> assigned to V4,
        never absorbed by the closer date."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-01", recorded_visit_code="V4")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        assert outcome.visit_assignments[0].selected_planned_visit_id \
            == "PV-KEY-1"

    def test_multi_feasible_boundary(self):
        """Challenge 40: two planned visits both feasible with equal
        evidence -> multi_feasible_boundary, never a date pick."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-02",
                             recorded_visit_code="UNSCHEDULED")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=(),
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        decision = outcome.visit_assignments[0]
        assert decision.decision_status == vs.VISIT_ASSIGNMENT_MULTI_FEASIBLE
        assert len(decision.candidate_planned_visit_ids) == 2
        # The actual_assignment unit for this bundle is boundary.
        assign_unit = result_for(outcome, vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign_unit.l1_disposition == L1Disposition.BOUNDARY

    def test_mapping_missing_not_evaluable(self):
        """Challenge 41: mapping table absent and only a similar name ->
        not_evaluable, no nearest-date fallback."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-02", recorded_visit_code="VX")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=(),
            mapping_coverage_complete=False, code_coverage_complete=False,
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        decision = outcome.visit_assignments[0]
        assert decision.decision_status == vs.VISIT_ASSIGNMENT_NOT_EVALUABLE
        assign_unit = result_for(outcome, vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign_unit.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_unplanned_supported(self):
        """Challenge 42: explicitly unscheduled contact allowed by the plan
        -> unplanned_supported, no positive."""
        v0, v1 = self._two_visits()
        enc = make_encounter(
            start="2026-07-02", recorded_visit_code="UNSCHEDULED",
            encounter_kind=vs.ENCOUNTER_UNSCHEDULED)
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=(), allow_unscheduled_visits=True,
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        assert outcome.visit_assignments[0].decision_status \
            == vs.VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED
        assert not any(r.unit_kind == vs.UNIT_ACTUAL_ASSIGNMENT
                       for r in outcome.unit_results)

    def test_unassigned_inconsistent_positive(self):
        """Challenge 43: record claims a planned visit that contradicts the
        unique applicable plan -> assignment positive."""
        v0, v1 = self._two_visits()
        enc = make_encounter(start="2026-07-02", recorded_visit_code="V9")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=[
                vse.OfficialCodeMapping(recorded_visit_code="V3",
                                        official_visit_code="V3",
                                        protocol_version="V2.0"),
                vse.OfficialCodeMapping(recorded_visit_code="V4",
                                        official_visit_code="V4",
                                        protocol_version="V2.0"),
                vse.OfficialCodeMapping(recorded_visit_code="V9",
                                        official_visit_code="V9",
                                        protocol_version="V2.0"),
            ],
            assignment_priority_policy=make_policy(),
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        decision = outcome.visit_assignments[0]
        assert decision.decision_status \
            == vs.VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT
        assign_unit = result_for(outcome, vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign_unit.l1_disposition == L1Disposition.POSITIVE
        assert assign_unit.positive_subtype \
            == vse.POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT

    def test_window_exclusion_only_impossible_candidates(self):
        """Predicate 5: a bundle determinately before a candidate's window
        start is excluded; a late bundle is not (mistiming, not
        misassignment)."""
        v0 = make_planned_visit(
            visit_id="pv-w1", visit_key="PV-W1", official_code="W1",
            audience_name="第 1 周访视", planned_order="1")
        v1 = make_planned_visit(
            visit_id="pv-w2", visit_key="PV-W2", official_code="W2",
            audience_name="第 2 周访视", planned_order="2")
        enc = make_encounter(start="2026-07-01",
                             recorded_visit_code="UNSCHEDULED")
        bundle = make_bundle(enc)
        # V1 window [06-28, 07-03]; V2 same. Encounter 07-01 is in both
        # windows -> with no claim both are feasible -> boundary.
        outcome = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=(),
            priority_policies={"PV-W1": make_policy(), "PV-W2": make_policy()})
        assert outcome.visit_assignments[0].decision_status \
            == vs.VISIT_ASSIGNMENT_MULTI_FEASIBLE
        # A visit whose window opens later (anchor +21 days = 07-22) cannot
        # host an encounter on 07-01: excluded as impossible.
        late = make_planned_visit(
            visit_id="pv-late", visit_key="PV-LATE", official_code="WL",
            audience_name="第 5 周访视", planned_order="5",
            window=make_window(lower="-3", upper="+3",
                               study_day_zero_exists=False))
        bindings = [
            make_anchor_binding(visit_key="PV-LATE", anchor_day="2026-07-22")]
        outcome2 = run_evaluation(
            visits=[late], encounters=[enc], bundles=[bundle],
            code_mappings=(), anchor_bindings=bindings,
            priority_policies={"PV-LATE": make_policy()})
        # The encounter is before PV-LATE's window start (07-22 + offsets):
        # excluded -> not_evaluable (no claim, complete evidence).
        assert outcome2.visit_assignments[0].decision_status \
            == vs.VISIT_ASSIGNMENT_NOT_EVALUABLE

    def test_multi_contact_bundle_unique_negative(self):
        """Challenge 45: one planned visit across two contacts with an
        explicit merge rule -> one planned node, negative occurrence."""
        e1 = make_encounter("enc-a", "2026-07-01", "V4")
        e2 = make_encounter("enc-b", "2026-07-02", "V4")
        bundle = make_bundle(e1, e2, merge_or_split_rule_id="merge-1")
        outcome = run_evaluation(
            visits=self._two_visits(), encounters=[e1, e2],
            bundles=[bundle],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        assert outcome.visit_assignments[0].decision_status \
            == vs.VISIT_ASSIGNMENT_UNIQUE
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        assert occ.l1_disposition == L1Disposition.NEGATIVE

    def test_bundle_input_order_does_not_change_result(self):
        """Challenge 107: swapping the two encounter rows (and bundle member
        order) leaves the assignment and hashes identical."""
        e1 = make_encounter("enc-a", "2026-07-01", "V4")
        e2 = make_encounter("enc-b", "2026-07-02", "V4")
        b1 = make_bundle(e1, e2, merge_or_split_rule_id="merge-1")
        b2 = make_bundle(e2, e1, merge_or_split_rule_id="merge-1")
        assert b1.bundle_id == b2.bundle_id
        o1 = run_evaluation(
            visits=self._two_visits(), encounters=[e1, e2],
            bundles=[b1],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        o2 = run_evaluation(
            visits=self._two_visits(), encounters=[e2, e1],
            bundles=[b2],
            priority_policies={"PV-KEY-0": make_policy(),
                               "PV-KEY-1": make_policy()})
        assert o1.expected_set.expected_set_hash_value \
            == o2.expected_set.expected_set_hash_value
        assert o1.visit_assignments[0].hash == o2.visit_assignments[0].hash


# ===========================================================================
# 5. Activity assignment + consumption ledger (§7)
# ===========================================================================

class TestActivityAssignmentAndLedger:
    def _setup(self, repeat_rule: str = ""):
        visit = make_planned_visit()
        activity = make_planned_activity(repeat_rule=repeat_rule)
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(encounter_refs=(enc.encounter_id,))
        return visit, activity, enc, bundle, actual

    def test_unique_activity_assignment_and_closed_ledger(self):
        visit, activity, enc, bundle, actual = self._setup()
        outcome = run_evaluation(
            visits=[visit], activities=[activity],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-KEY-1": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        decision = next(d for d in outcome.activity_assignments
                        if d.actual_activity_id == "act-1")
        assert decision.decision_status == vs.ACTIVITY_ASSIGNMENT_UNIQUE
        assert decision.selected_planned_activity_ids == ("PA-KEY-1",)
        ledger = outcome.consumption_ledgers[0]
        assert ledger.consuming_planned_activity_ids == ("PA-KEY-1",)
        assert ledger.reverse_coverage_status == vs.REVERSE_COVERAGE_CLOSED
        assert ("PA-KEY-1", "act-1") in outcome.reverse_consumption_index
        occ = result_for(outcome, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-KEY-1")
        assert occ.l1_disposition == L1Disposition.NEGATIVE

    def test_duplicate_consumption_positive(self):
        """Challenges 60/109: one actual assessment consumed by two planned
        obligations without a repeat rule -> duplicate_consumption positive
        and the ledger reverse coverage is open."""
        visit = make_planned_visit()
        a1 = make_planned_activity(activity_id="pa-1", activity_key="PA-1")
        a2 = make_planned_activity(activity_id="pa-2", activity_key="PA-2")
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[a1, a2],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-1": make_window(),
                                   "PA-2": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-1": make_policy(), "PA-2": make_policy()},
            assignment_priority_policy=make_policy())
        decision = next(d for d in outcome.activity_assignments
                        if d.actual_activity_id == "act-1")
        assert decision.decision_status \
            == vs.ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION
        ledger = outcome.consumption_ledgers[0]
        assert ledger.reverse_coverage_status == vs.REVERSE_COVERAGE_OPEN
        assign_unit = result_for(outcome, vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign_unit.l1_disposition == L1Disposition.POSITIVE
        assert assign_unit.positive_subtype == vse.POSITIVE_VISIT_DUPLICATE

    def test_repeat_allowed_multi_consumption_closed(self):
        """Challenges 61/110: repeat rule + parent binding + allowed
        multiplicity -> ledger allows multi-consumption and reverse coverage
        closes; both directions reconcile."""
        visit = make_planned_visit()
        a1 = make_planned_activity(activity_id="pa-1", activity_key="PA-1",
                                   repeat_rule="repeat:unlimited")
        a2 = make_planned_activity(activity_id="pa-2", activity_key="PA-2",
                                   repeat_rule="repeat:unlimited")
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[a1, a2],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-1": make_window(),
                                   "PA-2": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-1": make_policy(), "PA-2": make_policy()})
        ledger = outcome.consumption_ledgers[0]
        assert ledger.consuming_planned_activity_ids == ("PA-1", "PA-2")
        assert ledger.allowed_multiplicity == 2
        assert ledger.repeat_rule_id
        assert ledger.reverse_coverage_status == vs.REVERSE_COVERAGE_CLOSED
        assert ("PA-1", "act-1") in outcome.reverse_consumption_index
        assert ("PA-2", "act-1") in outcome.reverse_consumption_index

    def test_mislabeled_activity_positive(self):
        """Complete-evidence mislabel: an activity claiming a planned code
        that no obligation matches -> actual_assignment positive."""
        visit = make_planned_visit()
        activity = make_planned_activity()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(
            recorded_code="WRONG-CODE", encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[activity],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-KEY-1": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()},
            assignment_priority_policy=make_policy())
        assign_unit = result_for(outcome, vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign_unit.l1_disposition == L1Disposition.POSITIVE
        assert assign_unit.positive_subtype \
            == vse.POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT

    def test_unplanned_activity_supported(self):
        """Challenge 44: an extra unplanned assessment inside a visit is not
        forced into a planned obligation."""
        visit = make_planned_visit()
        activity = make_planned_activity()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(
            recorded_code="UNSCHED-1", encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[activity],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-KEY-1": make_window()},
            allow_unscheduled_activities=True,
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        decision = next(d for d in outcome.activity_assignments
                        if d.actual_activity_id == "act-1")
        assert decision.decision_status \
            == vs.ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED
        assert not any(r.unit_kind == vs.UNIT_ACTUAL_ASSIGNMENT
                       for r in outcome.unit_results)


# ===========================================================================
# 6. Unit evaluation -- five L1 dispositions (§8)
# ===========================================================================

class TestUnitEvaluation:
    def test_in_window_visit_negative(self):
        """Challenge 1: unique schedule, fixed anchor, in-window visit ->
        occurrence negative + timing negative."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert occ.l1_disposition == L1Disposition.NEGATIVE
        assert timing.l1_disposition == L1Disposition.NEGATIVE

    def test_overwindow_positive(self):
        """Challenge 2: determinate late visit -> visit_overwindow."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing.l1_disposition == L1Disposition.POSITIVE
        assert timing.positive_subtype == vse.POSITIVE_VISIT_OVERWINDOW
        assert timing.audience_label == "访视时间待核实"
        assert len(outcome.candidates) == 1
        assert len(outcome.query_drafts) == 1

    def test_missing_visit_positive(self):
        """Challenge 3: window latest endpoint before cutoff with complete
        coverage and no visit -> visit_missing."""
        visit = make_planned_visit()
        outcome = run_evaluation(visits=[visit],
                                 priority_policies={"PV-KEY-1": make_policy()})
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        assert occ.l1_disposition == L1Disposition.POSITIVE
        assert occ.positive_subtype == vse.POSITIVE_VISIT_MISSING

    def test_endpoint_inclusivity(self):
        """Challenges 18/19: exact date on inclusive lower endpoint is
        negative; on exclusive upper endpoint it is positive."""
        lower_inc = make_planned_visit(
            window=make_window(lower_endpoint_inclusive=True,
                               upper_endpoint_inclusive=True))
        enc = make_encounter(start="2026-06-28")  # lower bound -3
        bundle = make_bundle(enc)
        o1 = run_evaluation(
            visits=[lower_inc], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        timing = result_for(o1, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing.l1_disposition == L1Disposition.NEGATIVE
        upper_excl = make_planned_visit(
            window=make_window(upper_endpoint_inclusive=False))
        enc2 = make_encounter("enc-2", "2026-07-04")  # upper bound +3 excl
        bundle2 = make_bundle(enc2)
        o2 = run_evaluation(
            visits=[upper_excl], encounters=[enc2], bundles=[bundle2],
            priority_policies={"PV-KEY-1": make_policy()})
        timing2 = result_for(o2, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing2.l1_disposition == L1Disposition.POSITIVE

    def test_unfrozen_endpoint_not_evaluable(self):
        """Challenge 20: endpoint inclusivity undefined -> not_evaluable,
        never defaulted inclusive."""
        visit = make_planned_visit(
            window=make_window(lower_endpoint_inclusive=None,
                               upper_endpoint_inclusive=None))
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert occ.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert timing.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert not outcome.candidates
        assert not outcome.query_drafts
        # Occurrence (maturity not computable) + timing (window not
        # determinable): both are coverage gaps, never Queries.
        assert len(outcome.coverage_gap_notices) == 2

    def test_partial_month_in_window_negative(self):
        """Challenge 21: partial month entirely inside the window ->
        negative."""
        visit = make_planned_visit(
            window=make_window(lower="-35", upper="+35"))
        enc = make_encounter("enc-1", "2026-07", "V4",
                             date_precision=vs.PRECISION_MONTH)
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing.l1_disposition == L1Disposition.NEGATIVE

    def test_partial_month_out_of_window_positive(self):
        """Challenge 22: partial month entirely outside the window ->
        positive."""
        visit = make_planned_visit(
            window=make_window(lower="+1", upper="+30"))
        enc = make_encounter("enc-1", "2026-06", "V4",
                             date_precision=vs.PRECISION_MONTH)
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing.l1_disposition == L1Disposition.POSITIVE

    def test_partial_date_straddling_boundary(self):
        """Challenge 23: partial interval crossing the window bound with
        complete source -> boundary, preserved uncertainty."""
        visit = make_planned_visit()
        enc = make_encounter("enc-1", "2026-07", "V4",
                             date_precision=vs.PRECISION_MONTH,
                             end="2026-07")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        timing = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert timing.l1_disposition == L1Disposition.BOUNDARY
        assert len(outcome.candidates) == 1  # one clue with uncertainty
        assert not outcome.query_drafts  # boundary never drafts a Query

    def test_missing_dates_not_evaluable(self):
        """Challenge 24: missing date role -> not_evaluable (cutoff-scope
        gate), no silent day padding, no false missing-positive."""
        visit = make_planned_visit()
        enc = make_encounter("enc-1", "", "V4")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        assert any(g.gate_kind == vs.GATE_CUTOFF_SCOPE for g in outcome.gates)
        occ = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        assert occ.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert occ.not_evaluable_reason == vs.REASON_COVERAGE_INCOMPLETE
        # The date-less record never enters the timing evaluation.
        assert not any(r.unit_kind == vs.UNIT_VISIT_TIMING
                       for r in outcome.unit_results)

    def test_contingent_visit_not_judged_by_visitnum(self):
        """Challenge 33: contingent visit with a lower VISITNUM but legal
        timing is never an order violation."""
        base = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2")
        contingent = make_planned_visit(
            visit_id="pv-c", visit_key="PV-C", official_code="V1T",
            audience_name="触发访视", planned_order="1",
            visit_kind=vs.VISIT_CONTINGENT)
        e_b = make_encounter("enc-b", "2026-07-02", "V2")
        e_c = make_encounter("enc-c", "2026-07-03", "V1T")
        outcome = run_evaluation(
            visits=[base, contingent],
            encounters=[e_b, e_c], bundles=[make_bundle(e_b),
                                            make_bundle(e_c)],
            priority_policies={"PV-B": make_policy(),
                               "PV-C": make_policy()})
        assert not any(r.unit_kind == vs.UNIT_VISIT_ORDER
                       for r in outcome.unit_results)

    def test_order_inconsistent_positive(self):
        """Challenge 34: explicit planned_order contradicted by actual
        order -> visit_order_inconsistent."""
        first = make_planned_visit(
            visit_id="pv-a", visit_key="PV-A", official_code="V1",
            audience_name="第 1 周访视", planned_order="1")
        second = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2")
        e_a = make_encounter("enc-a", "2026-07-10", "V1")
        e_b = make_encounter("enc-b", "2026-07-02", "V2")
        outcome = run_evaluation(
            visits=[first, second],
            encounters=[e_a, e_b], bundles=[make_bundle(e_a),
                                            make_bundle(e_b)],
            priority_policies={"PV-A": make_policy(),
                               "PV-B": make_policy()})
        order = result_for(outcome, vs.UNIT_VISIT_ORDER, "PV-B")
        assert order.l1_disposition == L1Disposition.POSITIVE
        assert order.positive_subtype == vse.POSITIVE_VISIT_ORDER_INCONSISTENT

    def test_assessment_occurrence_and_timing_separate(self):
        """Challenges 56/57: assessment completed in the wrong visit window
        -> occurrence negative, timing positive (two atomic roots)."""
        visit = make_planned_visit()
        activity = make_planned_activity()
        enc = make_encounter(start="2026-07-10")  # visit overwindow too
        bundle = make_bundle(enc)
        actual = make_activity(start="2026-07-10",
                               encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[activity],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-KEY-1": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        occ = result_for(outcome, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-KEY-1")
        timing = result_for(outcome, vs.UNIT_ACTIVITY_TIMING, "PA-KEY-1")
        assert occ.l1_disposition == L1Disposition.NEGATIVE
        assert timing.l1_disposition == L1Disposition.POSITIVE
        assert timing.positive_subtype == vse.POSITIVE_ASSESSMENT_MISTIMED

    def test_missing_assessment_positive_and_table_gap(self):
        """Challenges 58/59: missing with complete coverage -> positive;
        table not provided -> not_evaluable, never judged missing."""
        visit = make_planned_visit()
        activity = make_planned_activity()
        o1 = run_evaluation(
            visits=[visit], activities=[activity],
            anchor_bindings=[make_anchor_binding()],
            activity_window_rules={"PA-KEY-1": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        occ = result_for(o1, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-KEY-1")
        assert occ.l1_disposition == L1Disposition.POSITIVE
        assert occ.positive_subtype == vse.POSITIVE_ASSESSMENT_MISSING
        o2 = run_evaluation(
            visits=[visit], activities=[activity],
            anchor_bindings=[make_anchor_binding()],
            activity_window_rules={"PA-KEY-1": make_window()},
            source_coverage={"assessment": False},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        occ2 = result_for(o2, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-KEY-1")
        assert occ2.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert occ2.l0_status == "missing"

    def test_sample_timing_day_precision_ok_and_hour_window_boundary(self):
        """Challenges 63/65/66: sample in window negative; day precision
        suffices for a day window; hour-level window with complete day-only
        source -> boundary."""
        visit = make_planned_visit()
        sample = make_planned_activity(
            activity_id="pa-s", activity_key="PA-S",
            activity_kind=vs.ACTIVITY_SAMPLE, clinical_domain="lab",
            official_code="SAMP-1", audience_name="样本采集",
            specimen_or_method_role="blood")
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(
            activity_id="act-s", start="2026-07-02",
            recorded_code="SAMP-1", activity_kind=vs.ACTIVITY_SAMPLE,
            clinical_domain="lab", encounter_refs=(enc.encounter_id,))
        o1 = run_evaluation(
            visits=[visit], activities=[sample],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-S": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-S": make_policy()})
        timing = result_for(o1, vs.UNIT_ACTIVITY_TIMING, "PA-S")
        assert timing.l1_disposition == L1Disposition.NEGATIVE
        hour_window = make_window(date_precision=vs.PRECISION_HOUR,
                                  timezone="UTC")
        o2 = run_evaluation(
            visits=[visit], activities=[sample],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-S": hour_window},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-S": make_policy()})
        timing2 = result_for(o2, vs.UNIT_ACTIVITY_TIMING, "PA-S")
        assert timing2.l1_disposition == L1Disposition.BOUNDARY

    def test_d06_d07_anomalies_do_not_create_d05_risks(self):
        """Challenges 71/72: D06 efficacy / D07 lab anomalies never create
        D05 risks; a timely sample stays negative."""
        visit = make_planned_visit()
        sample = make_planned_activity(
            activity_id="pa-s", activity_key="PA-S",
            activity_kind=vs.ACTIVITY_SAMPLE, clinical_domain="lab",
            official_code="SAMP-1", audience_name="样本采集",
            specimen_or_method_role="blood")
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        actual = make_activity(
            activity_id="act-s", start="2026-07-02",
            recorded_code="SAMP-1", activity_kind=vs.ACTIVITY_SAMPLE,
            clinical_domain="lab", encounter_refs=(enc.encounter_id,))
        outcome = run_evaluation(
            visits=[visit], activities=[sample],
            encounters=[enc], actual_activities=[actual], bundles=[bundle],
            activity_window_rules={"PA-S": make_window()},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-S": make_policy()})
        occ = result_for(outcome, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-S")
        assert occ.l1_disposition == L1Disposition.NEGATIVE
        assert not any(r.positive_subtype for r in outcome.unit_results)

    def test_missing_activity_window_rule_not_evaluable(self):
        """Challenge 79-adjacent: an activity whose timing window rule is
        not frozen cannot be judged missing -- occurrence stays
        not_evaluable (no default window-latest endpoint)."""
        visit = make_planned_visit()
        activity = make_planned_activity()
        outcome = run_evaluation(
            visits=[visit], activities=[activity],
            anchor_bindings=[make_anchor_binding()],
            activity_window_rules={},
            priority_policies={"PV-KEY-1": make_policy(),
                               "PA-KEY-1": make_policy()})
        occ = result_for(outcome, vs.UNIT_ACTIVITY_OCCURRENCE, "PA-KEY-1")
        assert occ.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert occ.r2_candidates == ()
        assert occ.query_refs == ()
        assert len(occ.coverage_gap_notices) == 1

    def test_schedule_consistency_positive(self):
        """Challenge 78: plan rules that cannot be simultaneously satisfied
        -> schedule_rule_inconsistent positive."""
        issue = vse.ScheduleConsistencyIssue(
            issue_id="sc-1", rule_ids=("wr-1", "wr-2"))
        visit = make_planned_visit()
        outcome = run_evaluation(
            visits=[visit], schedule_consistency_issues=[issue],
            assignment_priority_policy=make_policy(),
            priority_policies={"PV-KEY-1": make_policy()})
        unit = result_for(outcome, vs.UNIT_SCHEDULE_CONSISTENCY)
        assert unit.l1_disposition == L1Disposition.POSITIVE
        assert unit.positive_subtype == vse.POSITIVE_SCHEDULE_RULE_INCONSISTENT


# ===========================================================================
# 7. Query drafts (§9.2)
# ===========================================================================

class TestQueryDraft:
    def _overwindow(self, enrollment=None):
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        return run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()},
            enrollment=enrollment or make_enrollment(True))

    def test_three_parts_and_no_engineering_jargon(self):
        """Challenges 87/89: every Query has 依据/发现/行动项 and no
        engineering tokens leak to audience text."""
        outcome = self._overwindow()
        assert len(outcome.query_drafts) == 1
        query = outcome.query_drafts[0]
        assert query.basis.startswith("依据：")
        assert query.finding.startswith("发现：")
        assert query.action.startswith("行动项：")
        for text in (query.basis, query.finding, query.action):
            assert vse.audience_tokens_clean(text), text

    def test_context_conditional_pd_wording(self):
        """Challenge 111: only enrolled_or_post_enrollment appends the PD
        evaluation clause."""
        enrolled = self._overwindow(make_enrollment(True)).query_drafts[0]
        assert "方案偏离" in enrolled.action
        not_occurred = self._overwindow(make_enrollment(False)).query_drafts[0]
        assert "方案偏离" not in not_occurred.action
        unresolved = self._overwindow(make_enrollment(None)).query_drafts[0]
        assert "方案偏离" not in unresolved.action
        assert "暂无法确认是否符合方案" in unresolved.action

    def test_not_evaluable_never_queries(self):
        """Challenge 88: not_evaluable only shows a coverage gap, never a
        Query."""
        visit = make_planned_visit(
            window=make_window(lower_endpoint_inclusive=None,
                               upper_endpoint_inclusive=None))
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        assert not outcome.query_drafts
        assert not outcome.candidates
        assert len(outcome.coverage_gap_notices) == 2

    def test_missing_visit_query_links_plan_locator(self):
        """A missing visit's Query binds the plan locator as its locatable
        evidence."""
        visit = make_planned_visit()
        plan_loc = make_locator("plan-pv-v2-1", "plan_text")
        visit = make_planned_visit(plan_locator=plan_loc)
        outcome = run_evaluation(
            visits=[visit], plan_locators=[plan_loc],
            priority_policies={"PV-KEY-1": make_policy()})
        assert len(outcome.query_drafts) == 1
        query = outcome.query_drafts[0]
        assert plan_loc.locator_id() in query.source_locator_ids


# ===========================================================================
# 8. Lifecycle adapter integration (§9.1, §11)
# ===========================================================================

class TestLifecycleIntegration:
    def _adapter(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id=SNAPSHOT_ID,
                               revision_id=SOURCE_REV_ID)
        lc = make_lifecycle()
        return R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy"), svc, lc

    def _positive_outcome(self, policy=None, encounters=()):
        visit = make_planned_visit()
        encs = list(encounters)
        bundles = [make_bundle(e) for e in encs]
        return run_evaluation(
            visits=[visit], encounters=encs, bundles=bundles,
            priority_policies={"PV-KEY-1": policy or make_policy()})

    def _positive_result(self, policy=None):
        outcome = self._positive_outcome(policy)
        return next(r for r in outcome.unit_results
                    if r.l1_disposition == L1Disposition.POSITIVE)

    def _negative_result(self, instance) -> vse.D05UnitResult:
        """An N+1 negative unit explicitly linking the prior risk
        (RiskInstanceRef) -- the exact linked-negative proof."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        result = result_for(outcome, vs.UNIT_VISIT_OCCURRENCE, "PV-KEY-1")
        from dataclasses import replace
        return replace(
            result,
            risk_instance_refs=(
                RiskInstanceRef(
                    risk_instance_id=instance.risk_instance_id,
                    risk_identity_id=instance.risk_identity_id,
                    risk_state=instance.current_state),))

    def _closed_ledger_for(
        self, result: vse.D05UnitResult, snapshot_id: str,
    ) -> CoverageLedger:
        unit = next(u for u in self._positive_outcome().expected_units
                    if u.planned_visit_key == "PV-KEY-1")
        expected = ExpectedSet.from_units(
            [unit], domain_id=vs.D05_DOMAIN, run_id="run-N1")
        ledger = CoverageLedger(expected_set=expected)
        ledger.assign(result.to_unit_evaluation(
            provenance_snapshot_id=snapshot_id,
            provenance_rule_lineage="d05-visit-schedule-rule-v1"))
        ledger.close()
        return ledger

    def test_positive_promotes_and_establishes_with_priority(self):
        outcome = self._positive_outcome(make_policy(impact=vse.IMPACT_PRIMARY_ENDPOINT))
        result = next(r for r in outcome.unit_results
                      if r.l1_disposition == L1Disposition.POSITIVE)
        assert result.monitoring_priority == "medium"
        adapter, _, lc = self._adapter()
        promoted = adapter.promote_unit_result(result)
        assert len(promoted.registered_candidate_ids) == 1
        assert len(promoted.established_risk_ids) == 1
        inst = lc.instances_for_project(PROJECT_ID)[0]
        assert inst.severity == "medium"

    def test_rights_safety_high_and_machine_close_forbidden(self):
        """Challenge 115: rights/safety -> candidate flagged; the shared
        adapter forces severity=high and refuses machine close."""
        policy = make_policy(impact=vse.IMPACT_RIGHTS_SAFETY)
        result = self._positive_result(policy)
        assert result.monitoring_priority == "high"
        cand = result.r2_candidates[0]
        assert cand.detail["rights_or_safety_critical"] is True
        assert cand.detail["machine_close_forbidden"] is True
        adapter, _, _ = self._adapter()
        promoted = adapter.promote_unit_result(result)
        inst = adapter.lifecycle.get(promoted.established_risk_ids[0][0])
        assert inst.severity == "high"
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id=SNAPSHOT_ID)

    def test_machine_close_requires_linked_negative_and_closed_ledger(self):
        """Challenges 82/83: low/medium machine close requires a subsequent
        accepted snapshot + exact linked negative + closed complete ledger;
        without the proof the risk carries forward."""
        policy = make_policy(impact=vse.IMPACT_ADMINISTRATIVE)
        result = self._positive_result(policy)
        assert result.monitoring_priority == "low"
        adapter, svc, _ = self._adapter()
        promoted = adapter.promote_unit_result(result)
        inst = adapter.lifecycle.get(promoted.established_risk_ids[0][0])
        assert inst.severity == "low"
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id=SNAPSHOT_ID)
        # N+1 with a linked negative + closed ledger closes it.
        make_subsequent_snapshot(svc, snapshot_id="snap-N1",
                                 revision_id="rev-N1")
        neg = self._negative_result(inst)
        ledger = self._closed_ledger_for(neg, snapshot_id="snap-N1")
        result = adapter.reconcile_n_to_n1(
            [inst], [neg], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert len(result.closed) == 1
        assert result.closed[0].current_state == "closed"

    def test_high_risk_never_machine_closed(self):
        """Challenge 84: a high risk carries forward even with a full
        linked-negative proof; machine close refuses it."""
        high = self._positive_result(make_policy(
            impact=vse.IMPACT_MANDATORY_CRITICAL_SAMPLE,
            recoverability=vse.RECOVERABILITY_TIME_CRITICAL))
        assert high.monitoring_priority == "high"
        adapter, svc, _ = self._adapter()
        promoted = adapter.promote_unit_result(high)
        inst = adapter.lifecycle.get(promoted.established_risk_ids[0][0])
        make_subsequent_snapshot(svc, snapshot_id="snap-N1",
                                 revision_id="rev-N1")
        neg = self._negative_result(inst)
        ledger = self._closed_ledger_for(neg, snapshot_id="snap-N1")
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id="snap-N1",
                next_unit_results=[neg], coverage_ledger=ledger)
        reconciled = adapter.reconcile_n_to_n1(
            [inst], [neg], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert reconciled.closed == ()
        assert len(reconciled.carry_forward) == 1

    def test_boundary_registers_candidates_only(self):
        """Boundary units register candidates but are never established by
        machine adjudication."""
        visit = make_planned_visit()
        enc = make_encounter("enc-1", "2026-07", "V4",
                             date_precision=vs.PRECISION_MONTH,
                             end="2026-07")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        result = next(r for r in outcome.unit_results
                      if r.l1_disposition == L1Disposition.BOUNDARY)
        assert result.r2_candidates
        adapter, _, lc = self._adapter()
        promoted = adapter.promote_unit_result(result)
        assert promoted.registered_candidate_ids
        assert not promoted.established_risk_ids
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_not_evaluable_registers_nothing(self):
        visit = make_planned_visit(
            window=make_window(lower_endpoint_inclusive=None,
                               upper_endpoint_inclusive=None))
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        result = result_for(outcome, vs.UNIT_VISIT_TIMING, "PV-KEY-1")
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        adapter, _, lc = self._adapter()
        promoted = adapter.promote_unit_result(result)
        assert promoted.registered_candidate_ids == ()
        assert not promoted.established_risk_ids
        assert lc.instances_for_project(PROJECT_ID) == []


# ===========================================================================
# 9. Determinism and accounting (§12)
# ===========================================================================

class TestDeterminismAndAccounting:
    def test_rerun_identical_hashes(self):
        """Challenge 85: same snapshot rerun -> identical expected-set,
        unit, candidate and Query hashes; no duplicated risks."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        kwargs = dict(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        o1 = run_evaluation(**kwargs)
        o2 = run_evaluation(**kwargs)
        assert o1.expected_set.expected_set_hash_value \
            == o2.expected_set.expected_set_hash_value
        assert [u.unit_id for u in o1.expected_units] \
            == [u.unit_id for u in o2.expected_units]
        assert [c.candidate_id for c in o1.candidates] \
            == [c.candidate_id for c in o2.candidates]
        assert [q.query_id for q in o1.query_drafts] \
            == [q.query_id for q in o2.query_drafts]

    def test_input_order_never_changes_hashes(self):
        """Challenges 35/36/114: only row/dict order differs -> expected-set
        and assignment hashes identical."""
        v0 = make_planned_visit(
            visit_id="pv-v2-0", visit_key="PV-KEY-0", official_code="V3",
            audience_name="第 3 周访视", planned_order="3")
        v1 = make_planned_visit(
            visit_id="pv-v2-1", visit_key="PV-KEY-1", official_code="V4",
            audience_name="第 4 周访视", planned_order="4")
        e1 = make_encounter("enc-1", "2026-07-02", "V4")
        e2 = make_encounter("enc-2", "2026-07-02", "V3")
        b1 = make_bundle(e1)
        b2 = make_bundle(e2)
        policies = {"PV-KEY-0": make_policy(), "PV-KEY-1": make_policy()}
        o1 = run_evaluation(
            visits=[v0, v1], encounters=[e1, e2],
            bundles=[b1, b2], priority_policies=policies)
        o2 = run_evaluation(
            visits=[v1, v0], encounters=[e2, e1], bundles=[b2, b1],
            priority_policies=policies)
        assert o1.expected_set.expected_set_hash_value \
            == o2.expected_set.expected_set_hash_value
        assert sorted(a.hash for a in o1.visit_assignments) \
            == sorted(a.hash for a in o2.visit_assignments)
        assert [r.unit_id for r in o1.unit_results] \
            == [r.unit_id for r in o2.unit_results]

    def test_count_equation_and_l2_separation(self):
        """Challenges 97/99: expected_units = sum of five L1; L2 counts are
        separate and never inter-derived."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        assert len(outcome.expected_units) == len(outcome.unit_results)
        assert sum(outcome.l1_counts().values()) == len(outcome.expected_units)
        assert outcome.coverage_summary.expected_units \
            == len(outcome.expected_units)
        assert outcome.coverage_summary.query_draft_count() \
            == len(outcome.query_drafts)
        assert outcome.coverage_summary.risk_candidate_count() \
            == len(outcome.candidates)
        assert outcome.coverage_summary.source_record_count() >= 1

    def test_l0_gap_blocks_domain_complete(self):
        """Challenge 98: L0 missing but all L1 negative -> domain still not
        complete."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            source_coverage={"encounter": False},
            priority_policies={"PV-KEY-1": make_policy()})
        assert outcome.domain_complete[0] is False
        assert outcome.domain_complete[1]

    def test_all_closed_negative_domain_complete(self):
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        assert outcome.domain_complete == (True, [])
        assert not outcome.gates_block_domain()

    def test_each_positive_has_candidate_and_query(self):
        """Every positive unit associates with one candidate and at most one
        Query; accounting is not inter-derived."""
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        positives = [r for r in outcome.unit_results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert positives
        for result in positives:
            assert len(result.risk_candidate_refs) == 1
            assert len(result.query_refs) <= 1
            assert result.audience_label
            assert vse.audience_tokens_clean(result.audience_label)

    def test_interpretation_ledger_replay_input_order(self):
        """Challenge 114: interpretation ledger hash is input-order
        independent (canonicalized)."""
        v0 = make_planned_visit(
            visit_id="pv-v2-0", visit_key="PV-KEY-0", official_code="V3",
            audience_name="第 3 周访视", planned_order="3")
        v1 = make_planned_visit(
            visit_id="pv-v2-1", visit_key="PV-KEY-1", official_code="V4",
            audience_name="第 4 周访视", planned_order="4")
        enc = make_encounter(start="2026-07-02",
                             recorded_visit_code="UNSCHEDULED")
        bundle = make_bundle(enc)
        policies = {"PV-KEY-0": make_policy(), "PV-KEY-1": make_policy()}
        o1 = run_evaluation(
            visits=[v0, v1], encounters=[enc], bundles=[bundle],
            code_mappings=(), priority_policies=policies)
        o2 = run_evaluation(
            visits=[v1, v0], encounters=[enc], bundles=[bundle],
            code_mappings=(), priority_policies=policies)
        assert o1.interpretation_ledgers
        assert [led.ledger_id for led in o1.interpretation_ledgers] \
            == [led.ledger_id for led in o2.interpretation_ledgers]


# ===========================================================================
# 10. Open gate blocks domain completeness (corrective pass)
# ===========================================================================

class TestGateBlocksDomainComplete:
    """Corrective: the authoritative ``domain_complete`` verdict must AND
    the coverage-ledger completeness with the control-plane gate accounting.
    Any open applicability/routing/anchor/cutoff gate returns incomplete
    with a deterministic reason, even when the (possibly empty) L1 units
    all evaluated closed."""

    def _visit(self):
        return make_planned_visit()

    def test_zero_unit_applicability_gate_blocks_domain(self):
        """An applicability not_evaluable run with zero expected units must
        report domain_complete == False (previously leaked as True)."""
        appl = make_applicability(
            status=vs.APPLICABILITY_NOT_EVALUABLE, feasible=(),
            reasons=(vs.REASON_VERSION_MISSING,))
        outcome = run_evaluation(visits=[self._visit()], applicability=appl)
        assert len(outcome.expected_units) == 0
        assert outcome.gates_block_domain()
        assert outcome.domain_complete[0] is False
        # The gate block is the deterministic reason, listed first.
        assert outcome.domain_complete[1][0].startswith(
            "open ScheduleGate(s) block domain completeness")
        assert "applicability" in outcome.domain_complete[1][0]

    def test_routing_gate_blocks_domain(self):
        visit = self._visit()
        routed = make_planned_activity(
            activity_key="PA-ROUTE", owner_domain=vs.OWNER_UNRESOLVED)
        outcome = run_evaluation(
            visits=[visit], activities=[routed],
            anchor_bindings=[make_anchor_binding(visit_key="PV-KEY-1")],
            activity_window_rules={"PA-ROUTE": make_window()})
        assert any(g.gate_kind == vs.GATE_ROUTING for g in outcome.gates)
        assert outcome.domain_complete[0] is False
        assert "routing" in outcome.domain_complete[1][0]

    def test_anchor_gate_blocks_domain(self):
        first = make_planned_visit(
            visit_id="pv-a", visit_key="PV-A", official_code="V1",
            audience_name="第 1 周访视", planned_order="1")
        second = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2")
        bindings = [
            make_anchor_binding(visit_key="PV-A"),
            make_anchor_binding(visit_key="PV-B",
                                relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
        ]
        outcome = run_evaluation(
            visits=[first, second], anchor_bindings=bindings,
            priority_policies={"PV-A": make_policy(), "PV-B": make_policy()})
        assert any(g.gate_kind == vs.GATE_ANCHOR for g in outcome.gates)
        assert outcome.domain_complete[0] is False
        assert "anchor" in outcome.domain_complete[1][0]

    def test_cutoff_scope_gate_blocks_domain(self):
        encounter = make_encounter(
            start="2026-07-02", date_precision=vs.PRECISION_MONTH,
            end="2026-08")
        outcome = run_evaluation(
            visits=[self._visit()], encounters=[encounter],
            code_mappings=())
        assert any(g.gate_kind == vs.GATE_CUTOFF_SCOPE for g in outcome.gates)
        assert outcome.domain_complete[0] is False
        assert "cutoff_scope" in outcome.domain_complete[1][0]

    def test_all_closed_negative_path_still_complete(self):
        """The existing all-closed negative path must remain complete:
        no open gate, no L0 blocker, no L1 not_evaluable."""
        visit = self._visit()
        enc = make_encounter(start="2026-07-02")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle],
            priority_policies={"PV-KEY-1": make_policy()})
        assert outcome.domain_complete == (True, [])
        assert not outcome.gates_block_domain()

    def test_combine_domain_complete_direct(self):
        """Direct unit check of the combining function: gate block wins even
        when coverage is complete; clean coverage + no block is complete."""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class _Acct:
            blocks_domain_complete: bool

        gate = vs.ScheduleGate(
            gate_id="", gate_kind=vs.GATE_ANCHOR, subject_ref=SUBJECT,
            site_ref=SITE_REF, gate_state=vs.GATE_OPEN,
            decision_status=vs.GATE_DECISION_NOT_EVALUABLE,
            reason_codes=(vs.REASON_ANCHOR_MISSING,), source_locator_ids=())
        blocked = vse.combine_domain_complete(
            coverage_complete=(True, []),
            gate_accounting=_Acct(True), gates=(gate,))
        assert blocked == (False, ["open ScheduleGate(s) block domain "
                                   "completeness: anchor"])
        clean = vse.combine_domain_complete(
            coverage_complete=(True, []),
            gate_accounting=_Acct(False), gates=())
        assert clean == (True, [])

    def test_chained_anchor_two_feasible_interpretations_boundary(self):
        """Challenge 102: two complete feasible chained-anchor
        interpretations (one mature before cutoff, one not) -> boundary
        anchor gate with >=2 feasible anchor ref ids, not visit_missing."""
        v1a = make_planned_visit(
            visit_id="pv-1a", visit_key="PV-1A", official_code="V1A",
            audience_name="第 1 周访视 A", planned_order="1")
        v1b = make_planned_visit(
            visit_id="pv-1b", visit_key="PV-1B", official_code="V1B",
            audience_name="第 1 周访视 B", planned_order="1")
        vc = make_planned_visit(
            visit_id="pv-c", visit_key="PV-C", official_code="V2",
            audience_name="第 2 周访视", planned_order="2",
            window=make_window(lower="+7", upper="+13"))
        enc_early = make_encounter(
            encounter_id="enc-early", start="2026-07-02",
            recorded_visit_code="V1A")
        enc_late = make_encounter(
            encounter_id="enc-late", start="2026-08-20",
            recorded_visit_code="V1B")
        b_early = make_bundle(enc_early)
        b_late = make_bundle(enc_late)
        policies = {"PV-1A": make_policy(), "PV-1B": make_policy(),
                    "PV-C": make_policy()}
        bindings = [
            make_anchor_binding("PV-1A"),
            make_anchor_binding("PV-1B"),
            make_anchor_binding(
                "PV-C", relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
        ]
        outcome = run_evaluation(
            visits=[v1a, v1b, vc], encounters=[enc_early, enc_late],
            bundles=[b_early, b_late], cutoff=make_cutoff("2026-08-10"),
            anchor_bindings=bindings, priority_policies=policies)
        anchor_gates = [g for g in outcome.gates
                        if g.gate_kind == vs.GATE_ANCHOR]
        assert len(anchor_gates) == 1
        assert anchor_gates[0].decision_status == vs.GATE_DECISION_BOUNDARY
        assert len(anchor_gates[0].feasible_anchor_ref_ids) >= 2
        assert "PV-C" not in {
            u.planned_visit_key for u in outcome.expected_units}
        assert not any(
            r.planned_visit_key == "PV-C"
            and r.positive_subtype == vse.POSITIVE_VISIT_MISSING
            for r in outcome.unit_results)
        assert anchor_gates[0].gate_state == vs.GATE_OPEN
        assert outcome.gates_block_domain()

    def test_chained_anchor_zero_complete_missing_gate(self):
        """Chained anchor with no complete feasible predecessor -> exactly
        one not_evaluable missing-anchor gate (never a boundary / never a
        nearest-date winner)."""
        first = make_planned_visit(
            visit_id="pv-a", visit_key="PV-A", official_code="V1",
            audience_name="第 1 周访视", planned_order="1")
        second = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2")
        bindings = [
            make_anchor_binding(visit_key="PV-A"),
            make_anchor_binding(
                visit_key="PV-B",
                relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
        ]
        # No encounters/bundles at all -> zero complete predecessor
        # interpretations -> one not_evaluable missing-anchor gate.
        outcome = run_evaluation(
            visits=[first, second], anchor_bindings=bindings,
            priority_policies={"PV-A": make_policy(),
                               "PV-B": make_policy()})
        anchor_gates = [g for g in outcome.gates
                        if g.gate_kind == vs.GATE_ANCHOR]
        assert len(anchor_gates) == 1
        assert anchor_gates[0].decision_status == vs.GATE_DECISION_NOT_EVALUABLE
        assert anchor_gates[0].gate_state == vs.GATE_OPEN
        assert vs.REASON_ANCHOR_MISSING in anchor_gates[0].reason_codes
        assert anchor_gates[0].feasible_anchor_ref_ids == ()
        assert "PV-B" not in {
            u.planned_visit_key for u in outcome.expected_units}
        assert "PV-A" in {u.planned_visit_key
                          for u in outcome.expected_units}
        assert outcome.gates_block_domain()

    def test_chained_anchor_one_complete_bound(self):
        """Chained anchor with exactly one complete feasible predecessor ->
        bound (resolved), no anchor gate, and the dependent visit is
        evaluated normally."""
        first = make_planned_visit(
            visit_id="pv-a", visit_key="PV-A", official_code="V1",
            audience_name="第 1 周访视", planned_order="1")
        second = make_planned_visit(
            visit_id="pv-b", visit_key="PV-B", official_code="V2",
            audience_name="第 2 周访视", planned_order="2",
            window=make_window(lower="+7", upper="+13"))
        enc = make_encounter(
            encounter_id="enc-1", start="2026-07-02",
            recorded_visit_code="V1")
        bundle = make_bundle(enc)
        bindings = [
            make_anchor_binding(visit_key="PV-A"),
            make_anchor_binding(
                visit_key="PV-B",
                relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
        ]
        outcome = run_evaluation(
            visits=[first, second], encounters=[enc], bundles=[bundle],
            anchor_bindings=bindings,
            priority_policies={"PV-A": make_policy(),
                               "PV-B": make_policy()})
        assert not any(g.gate_kind == vs.GATE_ANCHOR for g in outcome.gates)
        # PV-B is anchored from PV-A's actual day (2026-07-02) and evaluated.
        assert "PV-B" in {u.planned_visit_key
                          for u in outcome.expected_units}
        assert not outcome.gates_block_domain()

    def test_chained_anchor_input_order_reversal_stable(self):
        """Input-order reversal of the two feasible prior visits leaves the
        boundary gate id and the feasible anchor ref ids unchanged
        (deterministic, content-addressed; never row-order)."""
        def _build(visits_in_order):
            v1a, v1b, vc = visits_in_order
            enc_early = make_encounter(
                encounter_id="enc-early", start="2026-07-02",
                recorded_visit_code="V1A")
            enc_late = make_encounter(
                encounter_id="enc-late", start="2026-08-20",
                recorded_visit_code="V1B")
            b_early = make_bundle(enc_early)
            b_late = make_bundle(enc_late)
            bindings = [
                make_anchor_binding("PV-1A"),
                make_anchor_binding("PV-1B"),
                make_anchor_binding(
                    "PV-C", relation_type=vs.RELATION_PRIOR_ACTUAL_VISIT),
            ]
            return run_evaluation(
                visits=[v1a, v1b, vc], encounters=[enc_early, enc_late],
                bundles=[b_early, b_late],
                cutoff=make_cutoff("2026-08-10"),
                anchor_bindings=bindings,
                priority_policies={
                    "PV-1A": make_policy(), "PV-1B": make_policy(),
                    "PV-C": make_policy()})

        v1a = make_planned_visit(
            visit_id="pv-1a", visit_key="PV-1A", official_code="V1A",
            audience_name="第 1 周访视 A", planned_order="1")
        v1b = make_planned_visit(
            visit_id="pv-1b", visit_key="PV-1B", official_code="V1B",
            audience_name="第 1 周访视 B", planned_order="1")
        vc = make_planned_visit(
            visit_id="pv-c", visit_key="PV-C", official_code="V2",
            audience_name="第 2 周访视", planned_order="2",
            window=make_window(lower="+7", upper="+13"))
        o1 = _build([v1a, v1b, vc])
        o2 = _build([v1b, v1a, vc])  # reversed prior-visit input order
        def _anchor_gate(outcome):
            gates = [g for g in outcome.gates
                     if g.gate_kind == vs.GATE_ANCHOR]
            assert len(gates) == 1
            return gates[0]
        g1, g2 = _anchor_gate(o1), _anchor_gate(o2)
        assert g1.gate_id == g2.gate_id
        assert g1.feasible_anchor_ref_ids == g2.feasible_anchor_ref_ids
        assert len(g1.feasible_anchor_ref_ids) >= 2
        assert g1.decision_status == vs.GATE_DECISION_BOUNDARY
        assert g1.decision_status == g2.decision_status
