"""R4-D05 visit-schedule domain-object contract tests (worker_01).

Focused tests for the frozen D05 contract (§§3.1-3.4, §4.2, §5.3, §12)
domain objects implemented in :mod:`mm_r4.visit_schedule`: immutable
planned/actual objects, the dual time boundaries (snapshot_as_of vs
clinical_event_cutoff), ScheduleGate state truth table, encounter bundles
with merge/split rules and exact typed anchors with deterministic hashes
and fail-closed validation.

Evaluation, expected-set expansion, Query wording, journey projection
functions and challenge-matrix fixtures are worker_02/03 territory and are
not exercised here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.contracts import (  # noqa: E402
    SourceLocator,
    cross_domain_evidence_content_hash,
)
from mm_r4 import visit_schedule as vs  # noqa: E402

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"
SUBJECT = "SYN-001"


# ===========================================================================
# Synthetic helpers
# ===========================================================================

def make_locator(
    record_id: str, table_semantic: str = "encounter",
    snapshot_id: str = SNAPSHOT_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_snapshot() -> vs.SnapshotAsOf:
    return vs.SnapshotAsOf(
        snapshot_id=SNAPSHOT_ID, accepted_at="2026-08-12T06:00:00Z",
        source_revision_id=SOURCE_REV_ID)


def make_cutoff(
    cutoff: str = "2026-08-10",
    precision: str = vs.PRECISION_DAY,
    timezone: str = "",
) -> vs.ClinicalEventCutoff:
    return vs.ClinicalEventCutoff(
        cutoff=cutoff, precision=precision, timezone=timezone)


def make_encounter(
    encounter_id: str = "enc-1",
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    start: str = "2026-08-01", end: str = "2026-08-01",
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
    recorded_visit_code: str = "V1",
    encounter_kind: str = vs.ENCOUNTER_ONSITE,
    source_locator: Optional[SourceLocator] = None,
    source_record_key: Optional[str] = None,
) -> vs.ActualEncounterRecord:
    loc = source_locator or make_locator(encounter_id)
    return vs.ActualEncounterRecord(
        encounter_id=encounter_id, stable_actual_object_key="",
        subject_ref=subject_ref, site_ref=site_ref,
        source_record_keys=(source_record_key or "encounter:" + encounter_id,),
        encounter_kind=encounter_kind,
        recorded_visit_code=recorded_visit_code,
        start=start, end=end, date_precision=date_precision,
        timezone=timezone,
        source_locator_ids=("loc-" + loc.content_digest(),))


def make_activity(
    activity_id: str = "act-1",
    start: str = "2026-08-01", end: str = "2026-08-01",
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
    source_locator: Optional[SourceLocator] = None,
) -> vs.ActualActivityRecord:
    loc = source_locator or make_locator(activity_id, "assessment")
    return vs.ActualActivityRecord(
        actual_activity_id=activity_id, stable_actual_object_key="",
        subject_ref=SUBJECT, site_ref=SITE_REF,
        source_record_keys=("assessment:" + activity_id,),
        activity_kind=vs.ACTIVITY_ASSESSMENT,
        clinical_domain="efficacy", recorded_activity_code="ASSESS-1",
        start=start, end=end, date_precision=date_precision,
        timezone=timezone,
        source_locator_ids=("loc-" + loc.content_digest(),))


def make_window(
    window_rule_id: str = "wr-1",
    anchor_kind: str = vs.RELATION_FIXED_REFERENCE,
    calendar_semantics: str = vs.STUDY_DAY,
    propagation_rule: str = vs.PROPAGATION_FIXED_ANCHOR,
    lower_offset: str = "-3", upper_offset: str = "+3",
    study_day_zero_exists: Optional[bool] = True,
    lower_endpoint_inclusive: Optional[bool] = True,
    upper_endpoint_inclusive: Optional[bool] = False,
    date_precision: str = vs.PRECISION_DAY,
) -> vs.VisitWindowRule:
    return vs.VisitWindowRule(
        window_rule_id=window_rule_id, anchor_kind=anchor_kind,
        anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
        calendar_semantics=calendar_semantics,
        propagation_rule=propagation_rule,
        lower_offset=lower_offset, upper_offset=upper_offset,
        study_day_zero_exists=study_day_zero_exists,
        lower_endpoint_inclusive=lower_endpoint_inclusive,
        upper_endpoint_inclusive=upper_endpoint_inclusive,
        date_precision=date_precision)


def make_anchor_rule(
    anchor_kind: str = vs.RELATION_FIXED_REFERENCE,
) -> vs.VisitAnchorRule:
    return vs.VisitAnchorRule(
        anchor_kind=anchor_kind,
        anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE)


def make_planned_visit(
    visit_id: str = "pv-v2-1", visit_key: str = "PV-KEY-1",
    official_code: str = "V4", audience_name: str = "第 4 周访视",
    planned_order: str = "4", visit_kind: str = vs.VISIT_SCHEDULED,
    window: Optional[vs.VisitWindowRule] = None,
) -> vs.PlannedVisitDefinition:
    return vs.PlannedVisitDefinition(
        planned_visit_id=visit_id, planned_visit_key=visit_key,
        schedule_id="sched-1", protocol_version="V2.0",
        official_visit_code=official_code, audience_visit_name=audience_name,
        planned_order=planned_order, visit_kind=visit_kind,
        phase="treatment", applicability_expression="expr-1",
        anchor_rule=make_anchor_rule(),
        window_rule=window or make_window())


def make_applicability(
    status: str = vs.APPLICABILITY_UNIQUE_ACTIVE,
    protocol_version: str = "V2.0",
    feasible: Sequence[str] = ("sched-1",),
    reasons: Sequence[str] = (),
    cutoff: Optional[vs.ClinicalEventCutoff] = None,
    transition_rule: str = vs.TRANSITION_ALL_SWITCH,
) -> vs.VisitScheduleApplicabilityDecision:
    return vs.VisitScheduleApplicabilityDecision(
        decision_id="", project_ref=PROJECT_ID, subject_ref=SUBJECT,
        site_ref=SITE_REF, protocol_version=protocol_version,
        arm="A", cohort="C1", phase="treatment",
        transition_rule=transition_rule,
        cutoff=cutoff or make_cutoff(),
        decision_status=status, feasible_schedule_ids=feasible,
        reason_codes=reasons)


def make_gate(
    gate_kind: str = vs.GATE_APPLICABILITY,
    gate_state: str = vs.GATE_OPEN,
    decision_status: str = vs.GATE_DECISION_BOUNDARY,
    feasible: Sequence[str] = ("sched-1", "sched-2"),
    reasons: Sequence[str] = (vs.REASON_MULTIPLE_FEASIBLE,),
    prior_gate_id: str = "", resolved_by_decision_id: str = "",
    counts_in_medical_expected_set: bool = False,
    blocks_domain_complete: Optional[bool] = None,
) -> vs.ScheduleGate:
    return vs.ScheduleGate(
        gate_id="", gate_kind=gate_kind, subject_ref=SUBJECT, site_ref=SITE_REF,
        gate_state=gate_state, decision_status=decision_status,
        feasible_schedule_ids=feasible, reason_codes=reasons,
        prior_gate_id=prior_gate_id,
        resolved_by_decision_id=resolved_by_decision_id,
        counts_in_medical_expected_set=counts_in_medical_expected_set,
        blocks_domain_complete=blocks_domain_complete)


def make_producer_anchor_ref(
    *,
    producer_domain: str = vs.OWNER_D03,
    evidence_role: str = "first_dose",
    producer_unit_id: str = "ip-unit-1",
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    phase: str = "phase-1", episode_id: str = "ep-1",
    anchor_start: str = "2026-01-05", anchor_end: str = "2026-01-05",
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
    record_id: str = "cd-1",
    relation_type: str = vs.RELATION_FIRST_IP_DOSE,
    ctx_extra: Sequence[Tuple[str, str]] = (),
    source_locator: Optional[SourceLocator] = None,
) -> vs.CrossDomainEvidenceRef:
    loc = source_locator or make_locator(record_id, "ip_exposure")
    ctx_items: list = [
        ("subject_ref", subject_ref), ("site_ref", site_ref),
        ("phase", phase), ("episode_id", episode_id),
        ("anchor_start", anchor_start), ("anchor_end", anchor_end),
        ("date_precision", date_precision), ("timezone", timezone),
    ]
    if relation_type:
        ctx_items.append(("relation_type", relation_type))
    ctx_items.extend(ctx_extra)
    ctx = tuple(ctx_items)
    return vs.CrossDomainEvidenceRef(
        evidence_ref_id="cd-ref-1", producer_domain=producer_domain,
        consumer_domain=vs.D05_DOMAIN, evidence_role=evidence_role,
        source_locator=loc, producer_unit_id=producer_unit_id,
        content_hash=cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role=evidence_role,
            claim_scope="", context_payload=dict(ctx)),
        claim_scope="", context_payload=ctx)


FULL_CTX_KEYS = ("subject_ref", "site_ref", "phase", "episode_id",
                 "anchor_start", "anchor_end", "date_precision",
                 "timezone", "relation_type")


def make_anchor_ref_with_ctx(
    ctx: Sequence[Tuple[str, str]],
    *,
    producer_domain: str = vs.OWNER_D03,
    evidence_role: str = "first_dose",
    producer_unit_id: str = "ip-unit-1",
    record_id: str = "cd-1",
) -> vs.CrossDomainEvidenceRef:
    """Build a producer ref from an explicit context tuple (used to prove
    every missing producer-context dimension fails closed)."""
    loc = make_locator(record_id, "ip_exposure")
    ctx_t = tuple(ctx)
    return vs.CrossDomainEvidenceRef(
        evidence_ref_id="cd-ref-ctx", producer_domain=producer_domain,
        consumer_domain=vs.D05_DOMAIN, evidence_role=evidence_role,
        source_locator=loc, producer_unit_id=producer_unit_id,
        content_hash=cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role=evidence_role,
            claim_scope="", context_payload=dict(ctx_t)),
        claim_scope="", context_payload=ctx_t)


def make_anchor_ref_missing_ctx(*missing: str) -> vs.CrossDomainEvidenceRef:
    """Full-context producer ref with the named context keys omitted."""
    items = [("subject_ref", SUBJECT), ("site_ref", SITE_REF),
             ("phase", "phase-1"), ("episode_id", "ep-1"),
             ("anchor_start", "2026-01-05"), ("anchor_end", "2026-01-05"),
             ("date_precision", vs.PRECISION_DAY), ("timezone", ""),
             ("relation_type", vs.RELATION_FIRST_IP_DOSE)]
    omitted = set(missing)
    kept = [item for item in items if item[0] not in omitted]
    return make_anchor_ref_with_ctx(kept)


def full_anchor_expected(
    ref: Optional[vs.CrossDomainEvidenceRef] = None,
    *,
    relation_type: str = vs.RELATION_FIRST_IP_DOSE,
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    producer_domain: str = vs.OWNER_D03,
    producer_unit_id: str = "ip-unit-1",
    stable_source_event_key: Optional[str] = None,
    content_hash: Optional[str] = None,
    phase: str = "phase-1", episode_id: str = "ep-1",
    anchor_start: str = "2026-01-05", anchor_end: str = "2026-01-05",
    date_precision: str = vs.PRECISION_DAY, timezone: str = "",
) -> dict:
    """Full explicit expected-dimension kwargs for a producer binding
    (§5.3): no dimension may be omitted.  Ref-derived values are filled
    from the ref when not overridden."""
    ref = ref or make_producer_anchor_ref(relation_type=relation_type)
    key = stable_source_event_key if stable_source_event_key is not None \
        else (f"{ref.source_locator.table_semantic}:"
              f"{ref.source_locator.record_id}")
    return dict(
        relation_type=relation_type, subject_ref=subject_ref,
        site_ref=site_ref, producer_ref=ref,
        producer_domain=producer_domain, producer_unit_id=producer_unit_id,
        stable_source_event_key=key,
        content_hash=content_hash if content_hash is not None
        else ref.content_hash,
        phase=phase, episode_id=episode_id,
        anchor_start=anchor_start, anchor_end=anchor_end,
        date_precision=date_precision, timezone=timezone)


def bind_full(kw: dict) -> vs.AnchorBindingOutcome:
    """Bind a full expected-dimension kwarg dict through the public
    binder (used by the missing/wrong-dimension challenge tests)."""
    return vs.bind_typed_schedule_anchor(
        relation_type=kw["relation_type"], subject_ref=kw["subject_ref"],
        site_ref=kw["site_ref"], producer_ref=kw["producer_ref"],
        producer_domain=kw["producer_domain"],
        producer_unit_id=kw["producer_unit_id"],
        stable_source_event_key=kw["stable_source_event_key"],
        content_hash=kw["content_hash"], phase=kw["phase"],
        episode_id=kw["episode_id"], anchor_start=kw["anchor_start"],
        anchor_end=kw["anchor_end"], date_precision=kw["date_precision"],
        timezone=kw["timezone"])


# ===========================================================================
# 1. Closed enums and input invariants
# ===========================================================================

class TestClosedEnums:
    def test_visit_kind_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_planned_visit(visit_kind="unplanned_extra")
        assert vs.VISIT_TRIGGERED in vs.VISIT_KINDS
        assert vs.VISIT_REPEAT_ALLOWED in vs.VISIT_KINDS

    def test_activity_kind_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_encounter(encounter_kind="teleport")
        assert vs.ENCOUNTER_REMOTE in vs.ENCOUNTER_KINDS

    def test_precision_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_encounter(date_precision="nanosecond")
        assert vs.PRECISION_MONTH in vs.PRECISIONS

    def test_gate_kind_and_state_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_kind="decision")
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_state="ajar")

    def test_relation_type_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitAnchorRule(anchor_kind="closest_visit",
                               anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE)

    def test_unit_kind_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.EvaluationMaturityRule(
                maturity_rule_id="mr-1", unit_kind="visit_score",
                anchor_kind=vs.RELATION_FIXED_REFERENCE,
                anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                maturity_expression="window_end", cutoff_precision=vs.PRECISION_DAY)

    def test_immutability(self):
        gate = make_gate()
        with pytest.raises(Exception):
            gate.gate_state = vs.GATE_CLOSED  # type: ignore[misc]
        visit = make_planned_visit()
        with pytest.raises(Exception):
            visit.planned_order = "99"  # type: ignore[misc]

    def test_tuple_fields_canonically_sorted(self):
        gate = make_gate(feasible=("sched-2", "sched-1"))
        assert gate.feasible_schedule_ids == ("sched-1", "sched-2")


# ===========================================================================
# 2. Planned objects (§3.1)
# ===========================================================================

class TestPlannedDefinitions:
    def test_definition_hash_deterministic(self):
        a = make_planned_visit()
        b = make_planned_visit()
        assert a.definition_hash == b.definition_hash

    def test_stable_key_unchanged_when_display_text_changes(self):
        a = make_planned_visit(audience_name="第 4 周访视")
        b = make_planned_visit(audience_name="第 4 周随访")
        assert a.planned_visit_key == b.planned_visit_key
        assert a.definition_hash != b.definition_hash

    def test_definition_hash_changes_on_semantic_change(self):
        a = make_planned_visit(official_code="V4")
        b = make_planned_visit(official_code="V4X")
        assert a.definition_hash != b.definition_hash

    def test_sample_activity_requires_specimen_role(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.PlannedActivityDefinition(
                planned_activity_id="pa-1", planned_activity_key="PA-1",
                planned_visit_id="pv-1", activity_kind=vs.ACTIVITY_SAMPLE,
                clinical_domain="laboratory", official_activity_code="SX",
                audience_name="样本 X", applicability_expression="expr-1",
                occurrence_rule="occ-1", timing_rule="tim-1")

    def test_window_rule_no_default_inclusivity(self):
        rule = vs.VisitWindowRule(
            window_rule_id="wr-1", anchor_kind=vs.RELATION_FIXED_REFERENCE,
            anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
            calendar_semantics=vs.STUDY_DAY,
            propagation_rule=vs.PROPAGATION_FIXED_ANCHOR,
            lower_offset="-3", upper_offset="+3",
            lower_endpoint_inclusive=None, upper_endpoint_inclusive=None,
            study_day_zero_exists=None, date_precision=vs.PRECISION_DAY)
        assert rule.lower_endpoint_inclusive is None
        assert rule.study_day_zero_exists is None  # explicitly unfrozen

    def test_window_rule_sub_day_requires_timezone(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitWindowRule(
                window_rule_id="wr-1", anchor_kind=vs.RELATION_FIXED_REFERENCE,
                anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                calendar_semantics=vs.ELAPSED_DURATION,
                propagation_rule=vs.PROPAGATION_FIXED_ANCHOR,
                lower_offset="-3", upper_offset="+3",
                date_precision=vs.PRECISION_HOUR)

    def test_window_rule_offset_free_text_rejected(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitWindowRule(
                window_rule_id="wr-1", anchor_kind=vs.RELATION_FIXED_REFERENCE,
                anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                calendar_semantics=vs.CALENDAR_DATE,
                propagation_rule=vs.PROPAGATION_FIXED_ANCHOR,
                lower_offset="around day 3", upper_offset="+3",
                date_precision=vs.PRECISION_DAY)

    def test_maturity_rule_missing_anchor_effect_gate_only(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.EvaluationMaturityRule(
                maturity_rule_id="mr-1", unit_kind=vs.UNIT_VISIT_OCCURRENCE,
                anchor_kind=vs.RELATION_FIXED_REFERENCE,
                anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                maturity_expression="window_end",
                cutoff_precision=vs.PRECISION_DAY,
                missing_anchor_effect="skip")

    def test_episode_scoped_window_ids_differ(self):
        spec = dict(anchor_kind=vs.RELATION_FIXED_REFERENCE,
                    anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                    calendar_semantics=vs.STUDY_DAY,
                    study_day_zero_exists=True, lower_offset="-3",
                    upper_offset="+3", lower_endpoint_inclusive=True,
                    upper_endpoint_inclusive=False, grace_period="",
                    date_precision=vs.PRECISION_DAY, timezone="",
                    propagation_rule=vs.PROPAGATION_FIXED_ANCHOR)
        base = vs.schedule_evaluation_window_id(**spec)
        ep1 = vs.schedule_evaluation_window_id(**spec,
                                                anchor_episode_id="ep-1")
        ep2 = vs.schedule_evaluation_window_id(**spec,
                                                anchor_episode_id="ep-2")
        assert base == vs.schedule_evaluation_window_id(**spec)
        assert ep1 != ep2  # episodes never close each other (§3.4)
        assert ep1 != base


# ===========================================================================
# 3. Applicability decision (§4.1)
# ===========================================================================

class TestApplicabilityDecision:
    def test_unique_active_requires_version_and_schedule(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_applicability(status=vs.APPLICABILITY_UNIQUE_ACTIVE,
                               protocol_version="", feasible=())
        assert make_applicability().decision_id.startswith("d05-appl-")

    def test_boundary_requires_two_feasible(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_applicability(status=vs.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
                               feasible=("sched-1",))
        d = make_applicability(status=vs.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
                               feasible=("sched-1", "sched-2"),
                               reasons=(vs.REASON_MULTIPLE_FEASIBLE,))
        assert d.decision_status == vs.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY

    def test_not_evaluable_requires_reason(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_applicability(status=vs.APPLICABILITY_NOT_EVALUABLE,
                               feasible=(), reasons=())
        d = make_applicability(status=vs.APPLICABILITY_NOT_EVALUABLE,
                               feasible=(), reasons=(vs.REASON_VERSION_MISSING,))
        assert d.reason_codes == (vs.REASON_VERSION_MISSING,)

    def test_decision_id_stable_across_cutoff_change(self):
        a = make_applicability(cutoff=make_cutoff("2026-08-10"))
        b = make_applicability(cutoff=make_cutoff("2026-09-01"))
        assert a.decision_id == b.decision_id  # clinical identity stable
        assert a.hash != b.hash  # run-scoped lineage differs

    def test_transition_rule_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_applicability(transition_rule="grandfather_everything")
        assert vs.TRANSITION_NEXT_VISIT_SWITCH in vs.TRANSITION_RULES

    def test_no_default_latest_version(self):
        d = make_applicability(protocol_version="V1.0",
                               feasible=("sched-old",))
        assert d.protocol_version == "V1.0"  # never auto-selected to latest


# ===========================================================================
# 4. Actual records and stable identity (§3.2, §3.4)
# ===========================================================================

class TestActualRecordsAndIdentity:
    def test_content_hash_deterministic(self):
        a = make_encounter()
        b = make_encounter()
        assert a.content_hash == b.content_hash

    def test_stable_key_excludes_dates(self):
        a = make_encounter(start="2026-08-01", end="2026-08-01")
        b = make_encounter(start="2026-08-05", end="2026-08-05")
        assert a.stable_actual_object_key == b.stable_actual_object_key
        assert a.content_hash != b.content_hash

    def test_stable_key_excludes_visit_name_free_text(self):
        a = make_encounter()
        b = make_encounter()
        # same source record keys => same identity even though the record
        # id string appears in the recorded visit code is not in the key:
        assert a.stable_actual_object_key == b.stable_actual_object_key
        assert "enc-1" not in a.stable_actual_object_key.replace("key", "")

    def test_stable_key_mismatch_fails_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActualEncounterRecord(
                encounter_id="enc-1", stable_actual_object_key="forged",
                subject_ref=SUBJECT, site_ref=SITE_REF,
                source_record_keys=("encounter:enc-1",),
                encounter_kind=vs.ENCOUNTER_ONSITE,
                recorded_visit_code="V1")

    def test_stable_key_order_independent(self):
        a = vs.encounter_stable_object_key(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            source_record_keys=("t1:r1", "t2:r2"))
        b = vs.encounter_stable_object_key(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            source_record_keys=("t2:r2", "t1:r1"))
        assert a == b

    def test_derived_date_requires_algorithm_and_inputs(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_encounter().__class__(
                encounter_id="enc-1", stable_actual_object_key="",
                subject_ref=SUBJECT, site_ref=SITE_REF,
                source_record_keys=("encounter:enc-1",),
                encounter_kind=vs.ENCOUNTER_ONSITE,
                recorded_visit_code="V1", start="2026-08-01", end="2026-08-01",
                date_precision=vs.PRECISION_DAY,
                date_origin=vs.DATE_ORIGIN_DERIVED,
                derivation_algorithm_id="", input_locator_ids=())
        enc = vs.ActualEncounterRecord(
            encounter_id="enc-2", stable_actual_object_key="",
            subject_ref=SUBJECT, site_ref=SITE_REF,
            source_record_keys=("encounter:enc-2",),
            encounter_kind=vs.ENCOUNTER_ONSITE,
            recorded_visit_code="V1", start="2026-08-01", end="2026-08-01",
            date_precision=vs.PRECISION_DAY,
            date_origin=vs.DATE_ORIGIN_DERIVED,
            derivation_algorithm_id="sv-derive-v1",
            input_locator_ids=("loc-x",))
        assert enc.date_origin == vs.DATE_ORIGIN_DERIVED

    def test_recorded_date_forbids_derivation_ids(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActualEncounterRecord(
                encounter_id="enc-1", stable_actual_object_key="",
                subject_ref=SUBJECT, site_ref=SITE_REF,
                source_record_keys=("encounter:enc-1",),
                encounter_kind=vs.ENCOUNTER_ONSITE,
                recorded_visit_code="V1", start="2026-08-01", end="2026-08-01",
                date_precision=vs.PRECISION_DAY,
                derivation_algorithm_id="fake-algo",
                input_locator_ids=("loc-x",))

    def test_date_without_precision_fails_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_encounter(start="2026-08-01", end="2026-08-01",
                           date_precision=vs.PRECISION_UNKNOWN)

    def test_sub_day_record_requires_timezone(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_encounter(start="2026-08-01T10:00", end="2026-08-01T10:30",
                           date_precision=vs.PRECISION_MINUTE)
        rec = make_encounter(start="2026-08-01T10:00", end="2026-08-01T10:30",
                             date_precision=vs.PRECISION_MINUTE,
                             timezone="UTC")
        assert rec.timezone == "UTC"


# ===========================================================================
# 5. Dual time boundaries (§4.2) -- snapshot_as_of vs clinical_event_cutoff
# ===========================================================================

class TestDualCutoffScope:
    def _scope(self, record, snapshot=None, cutoff=None,
               locators=None, **kw):
        return vs.resolve_actual_record_scope(
            record=record,
            snapshot_as_of=snapshot or make_snapshot(),
            clinical_event_cutoff=cutoff or make_cutoff(),
            source_locators=locators or (make_locator("loc-1"),),
            **kw)

    def test_in_scope_before_cutoff(self):
        rec = make_encounter(start="2026-08-01", end="2026-08-01")
        d = self._scope(rec)
        assert d.scope_status == vs.SCOPE_IN_SCOPE
        assert d.reason_codes == ()

    def test_cutoff_day_inclusive(self):
        rec = make_encounter(start="2026-08-10", end="2026-08-10")
        assert self._scope(rec).scope_status == vs.SCOPE_IN_SCOPE

    def test_out_of_cutoff_after(self):
        rec = make_encounter(start="2026-08-12", end="2026-08-12")
        d = self._scope(rec)
        assert d.scope_status == vs.SCOPE_OUT_OF_CUTOFF
        assert d.reason_codes == ()

    def test_partial_month_straddle_boundary(self):
        rec = make_encounter(start="2026-08", end="2026-08",
                             date_precision=vs.PRECISION_MONTH)
        d = self._scope(rec)
        assert d.scope_status == vs.SCOPE_BOUNDARY
        assert vs.REASON_INTERVAL_STRADDLES in d.reason_codes

    def test_partial_month_entirely_before_cutoff_in_scope(self):
        rec = make_encounter(start="2026-07", end="2026-07",
                             date_precision=vs.PRECISION_MONTH)
        assert self._scope(rec).scope_status == vs.SCOPE_IN_SCOPE

    def test_partial_month_entirely_after_cutoff_out(self):
        rec = make_encounter(start="2026-09", end="2026-09",
                             date_precision=vs.PRECISION_MONTH)
        assert self._scope(rec).scope_status == vs.SCOPE_OUT_OF_CUTOFF

    def test_missing_time_role_not_evaluable(self):
        rec = make_encounter(start="", end="")
        d = self._scope(rec)
        assert d.scope_status == vs.SCOPE_NOT_EVALUABLE
        assert vs.REASON_TIME_ROLE_MISSING in d.reason_codes

    def test_conflicting_day_interval_not_evaluable(self):
        rec = make_encounter(start="2026-08-05", end="2026-08-01")
        d = self._scope(rec)
        assert d.scope_status == vs.SCOPE_NOT_EVALUABLE
        assert vs.REASON_TIME_ROLE_CONFLICT in d.reason_codes

    def test_explicit_conflicting_roles_not_evaluable(self):
        rec = make_encounter(start="2026-08-01", end="2026-08-01")
        d = self._scope(rec, conflicting_time_roles=("svstdt", "svendt"))
        assert d.scope_status == vs.SCOPE_NOT_EVALUABLE
        assert vs.REASON_TIME_ROLE_CONFLICT in d.reason_codes

    def test_sub_day_without_timezone_not_evaluable(self):
        # Construction rejects sub-day without tz; use a duck record to
        # exercise the resolver's fail-closed guard (challenge 27).
        class Duck:
            actual_object_id = "enc-duck"
            start = "2026-08-01T22:00"
            end = "2026-08-02T02:00"
            date_precision = vs.PRECISION_HOUR
            timezone = ""
        d = self._scope(Duck())
        assert d.scope_status == vs.SCOPE_NOT_EVALUABLE
        assert vs.REASON_TIMEZONE_MISSING in d.reason_codes

    def test_cross_midnight_with_tz_evaluated(self):
        cut = vs.ClinicalEventCutoff(cutoff="2026-08-02T12:00",
                                     precision=vs.PRECISION_HOUR,
                                     timezone="UTC")
        rec = make_encounter(start="2026-08-01T22:00", end="2026-08-02T02:00",
                             date_precision=vs.PRECISION_HOUR, timezone="UTC")
        d = self._scope(rec, cutoff=cut)
        assert d.scope_status == vs.SCOPE_IN_SCOPE

    def test_event_on_subday_cutoff_day_boundary(self):
        cut = vs.ClinicalEventCutoff(cutoff="2026-08-01T12:00",
                                     precision=vs.PRECISION_HOUR,
                                     timezone="UTC")
        rec = make_encounter(start="2026-08-01", end="2026-08-01")
        assert self._scope(rec, cutoff=cut).scope_status == vs.SCOPE_BOUNDARY

    def test_wrong_snapshot_fails_closed(self):
        rec = make_encounter()
        other_snapshot = vs.SnapshotAsOf(
            snapshot_id="snap-other", accepted_at="2026-08-13T06:00:00Z",
            source_revision_id="rev-2")
        with pytest.raises(vs.ScheduleSliceError):
            self._scope(rec, snapshot=other_snapshot)

    def test_missing_locators_fails_closed(self):
        rec = make_encounter()
        with pytest.raises(vs.ScheduleSliceError):
            vs.resolve_actual_record_scope(
                record=rec, snapshot_as_of=make_snapshot(),
                clinical_event_cutoff=make_cutoff(), source_locators=())

    def test_scope_deterministic_rerun(self):
        rec = make_encounter()
        a = self._scope(rec)
        b = self._scope(rec)
        assert a.scope_decision_id == b.scope_decision_id
        assert a.lineage_hash == b.lineage_hash

    def test_late_arriving_new_snapshot_new_decision(self):
        rec = make_encounter(start="2026-08-05", end="2026-08-05")
        d1 = self._scope(rec)
        late_snapshot = vs.SnapshotAsOf(
            snapshot_id="snap-accepted-002", accepted_at="2026-08-20T06:00:00Z",
            source_revision_id="sr-2")
        late_loc = make_locator("enc-1", snapshot_id="snap-accepted-002")
        d2 = vs.resolve_actual_record_scope(
            record=rec, snapshot_as_of=late_snapshot,
            clinical_event_cutoff=make_cutoff(),
            source_locators=(late_loc,))
        assert d1.scope_status == vs.SCOPE_IN_SCOPE
        assert d2.scope_status == vs.SCOPE_IN_SCOPE
        assert d1.scope_decision_id != d2.scope_decision_id  # new Run

    def test_activity_record_scoped_too(self):
        act = make_activity(start="2026-08-12", end="2026-08-12")
        d = self._scope(act)
        assert d.scope_status == vs.SCOPE_OUT_OF_CUTOFF


# ===========================================================================
# 6. Encounter bundles (§3.2, §5.2)
# ===========================================================================

class TestEncounterBundle:
    def test_single_contact_single_member_bundle(self):
        rec = make_encounter()
        b = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        assert b.member_encounter_ids == ("enc-1",)
        assert b.derived_start == "2026-08-01"
        assert b.bundle_id.startswith("d05-bundle-id-")

    def test_two_contacts_merge_rule_derived_interval(self):
        a = make_encounter("enc-a", start="2026-08-01", end="2026-08-01")
        b = make_encounter("enc-b", start="2026-08-02", end="2026-08-02")
        bundle = vs.build_actual_encounter_bundle(
            member_encounters=(a, b), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_MULTI_CONTACT,
            merge_or_split_rule_id="mr-1")
        assert bundle.derived_start == "2026-08-01"
        assert bundle.derived_end == "2026-08-02"

    def test_member_order_swap_same_bundle_identity(self):
        a = make_encounter("enc-a")
        b = make_encounter("enc-b")
        x = vs.build_actual_encounter_bundle(
            member_encounters=(a, b), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_MULTI_CONTACT,
            merge_or_split_rule_id="mr-1")
        y = vs.build_actual_encounter_bundle(
            member_encounters=(b, a), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_MULTI_CONTACT,
            merge_or_split_rule_id="mr-1")
        assert x.bundle_id == y.bundle_id
        assert x.lineage_hash == y.lineage_hash
        assert x.stable_actual_object_key == y.stable_actual_object_key

    def test_multi_contact_without_merge_rule_fails(self):
        a = make_encounter("enc-a")
        b = make_encounter("enc-b")
        with pytest.raises(vs.ScheduleSliceError):
            vs.build_actual_encounter_bundle(
                member_encounters=(a, b), subject_ref=SUBJECT,
                site_ref=SITE_REF, episode_kind=vs.EPISODE_MULTI_CONTACT)

    def test_wrong_subject_site_fails_closed(self):
        rec = make_encounter(subject_ref="SYN-OTHER")
        with pytest.raises(vs.ScheduleSliceError):
            vs.build_actual_encounter_bundle(
                member_encounters=(rec,), subject_ref=SUBJECT,
                site_ref=SITE_REF, episode_kind=vs.EPISODE_SINGLE_CONTACT)

    def test_unsplit_multi_bundle_membership_fails(self):
        a = make_encounter("enc-a")
        b = make_encounter("enc-b")
        b1 = vs.build_actual_encounter_bundle(
            member_encounters=(a,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        b2 = vs.build_actual_encounter_bundle(
            member_encounters=(a, b), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_MULTI_CONTACT,
            merge_or_split_rule_id="mr-1")
        with pytest.raises(vs.ScheduleSliceError):
            vs.validate_bundle_membership(bundles=(b1, b2))

    def test_split_rule_allows_multi_bundle(self):
        a = make_encounter("enc-a")
        b = make_encounter("enc-b")
        b1 = vs.build_actual_encounter_bundle(
            member_encounters=(a,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        b2 = vs.build_actual_encounter_bundle(
            member_encounters=(a, b), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_MULTI_CONTACT,
            merge_or_split_rule_id="mr-1")
        vs.validate_bundle_membership(
            bundles=(b1, b2), split_allowed_encounter_ids=("enc-a",))

    def test_duplicate_bundle_rejected(self):
        rec = make_encounter()
        b1 = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        with pytest.raises(vs.ScheduleSliceError):
            vs.validate_bundle_membership(bundles=(b1, b1))

    def test_bundle_stable_key_mismatch_fails(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActualEncounterBundle(
                bundle_id="", stable_actual_object_key="forged",
                subject_ref=SUBJECT, site_ref=SITE_REF,
                member_encounter_ids=("enc-1",),
                episode_kind=vs.EPISODE_SINGLE_CONTACT,
                assignment_scope=vs.ASSIGNMENT_SCOPE_SINGLE)

    def test_bundle_stable_key_declarable_and_verified(self):
        # Declaring the exact canonical key is accepted and preserved.
        rec = make_encounter()
        declared = vs.bundle_stable_object_key(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            member_encounter_ids=("enc-1",))
        b = vs.ActualEncounterBundle(
            bundle_id="", stable_actual_object_key=declared,
            subject_ref=SUBJECT, site_ref=SITE_REF,
            member_encounter_ids=("enc-1",),
            episode_kind=vs.EPISODE_SINGLE_CONTACT,
            assignment_scope=vs.ASSIGNMENT_SCOPE_SINGLE)
        assert b.stable_actual_object_key == declared
        auto = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        assert auto.stable_actual_object_key == declared

    def test_bundle_stable_key_cross_run_stable(self):
        # Same member episode in a later snapshot/revision keeps the same
        # stable key and bundle id; only the lineage (locators) differs.
        rec = make_encounter()
        loc1 = make_locator("enc-1", snapshot_id="snap-accepted-001")
        loc2 = make_locator("enc-1", snapshot_id="snap-accepted-002")
        b1 = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT,
            source_locators=(loc1,))
        b2 = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT,
            source_locators=(loc2,))
        assert b1.stable_actual_object_key == b2.stable_actual_object_key
        assert b1.bundle_id == b2.bundle_id
        assert b1.lineage_hash != b2.lineage_hash
        assert b1.stable_actual_object_key == vs.bundle_stable_object_key(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            member_encounter_ids=("enc-1",))

    def test_member_timezone_conflict_fails(self):
        a = make_encounter("enc-a", timezone="UTC")
        b = make_encounter("enc-b", timezone="+08:00")
        with pytest.raises(vs.ScheduleSliceError):
            vs.build_actual_encounter_bundle(
                member_encounters=(a, b), subject_ref=SUBJECT,
                site_ref=SITE_REF, episode_kind=vs.EPISODE_MULTI_CONTACT,
                merge_or_split_rule_id="mr-1")

    def test_multi_visit_scope_requires_merge_rule(self):
        rec = make_encounter()
        with pytest.raises(vs.ScheduleSliceError):
            vs.build_actual_encounter_bundle(
                member_encounters=(rec,), subject_ref=SUBJECT,
                site_ref=SITE_REF, episode_kind=vs.EPISODE_SINGLE_CONTACT,
                assignment_scope=vs.ASSIGNMENT_SCOPE_MULTI)


# ===========================================================================
# 7. ScheduleGate (§3.3, §12) -- closed truth table (challenge 116)
# ===========================================================================

class TestScheduleGate:
    def test_open_boundary_legal(self):
        gate = make_gate(gate_state=vs.GATE_OPEN,
                         decision_status=vs.GATE_DECISION_BOUNDARY)
        assert gate.blocks_domain_complete is True

    def test_open_not_evaluable_legal(self):
        gate = make_gate(gate_state=vs.GATE_OPEN,
                         decision_status=vs.GATE_DECISION_NOT_EVALUABLE)
        assert gate.blocks_domain_complete is True

    def test_closed_resolved_legal(self):
        prior = make_gate()
        gate = make_gate(gate_state=vs.GATE_CLOSED,
                         decision_status=vs.GATE_DECISION_RESOLVED,
                         prior_gate_id=prior.gate_id,
                         resolved_by_decision_id="dec-1")
        assert gate.blocks_domain_complete is False
        assert gate.lineage_hash.startswith("d05-gate-")

    @pytest.mark.parametrize("state,status", [
        (vs.GATE_OPEN, vs.GATE_DECISION_RESOLVED),
        (vs.GATE_CLOSED, vs.GATE_DECISION_BOUNDARY),
        (vs.GATE_CLOSED, vs.GATE_DECISION_NOT_EVALUABLE),
    ])
    def test_illegal_state_combos_fail(self, state, status):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_state=state, decision_status=status)

    def test_open_gate_forbids_prior_and_resolved(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_state=vs.GATE_OPEN,
                      decision_status=vs.GATE_DECISION_BOUNDARY,
                      prior_gate_id="g-old")

    def test_closed_gate_requires_prior_and_resolved(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_state=vs.GATE_CLOSED,
                      decision_status=vs.GATE_DECISION_RESOLVED,
                      prior_gate_id="", resolved_by_decision_id="")

    def test_counts_in_medical_expected_set_always_false(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(counts_in_medical_expected_set=True)

    def test_blocks_domain_complete_mismatch_fails(self):
        with pytest.raises(vs.ScheduleSliceError):
            make_gate(gate_state=vs.GATE_OPEN,
                      decision_status=vs.GATE_DECISION_BOUNDARY,
                      blocks_domain_complete=False)

    def test_gate_id_deterministic_and_order_independent(self):
        a = make_gate(feasible=("s1", "s2"))
        b = make_gate(feasible=("s2", "s1"))
        assert a.gate_id == b.gate_id

    def test_run_accounting_equation(self):
        open_boundary = make_gate(
            gate_kind=vs.GATE_APPLICABILITY,
            decision_status=vs.GATE_DECISION_BOUNDARY)
        open_ne = make_gate(
            gate_kind=vs.GATE_ANCHOR,
            decision_status=vs.GATE_DECISION_NOT_EVALUABLE,
            reasons=(vs.REASON_ANCHOR_MISSING,))
        closed = make_gate(
            gate_kind=vs.GATE_ROUTING,
            gate_state=vs.GATE_CLOSED,
            decision_status=vs.GATE_DECISION_RESOLVED,
            prior_gate_id=open_ne.gate_id, resolved_by_decision_id="d-1")
        acc = vs.validate_gate_run_accounting(gates=(open_boundary, open_ne,
                                                     closed), run_id="r-1")
        assert acc.total == 3
        assert acc.closed_resolved == 1
        assert acc.open_boundary == 1
        assert acc.open_not_evaluable == 1
        assert acc.blocks_domain_complete is True

    def test_duplicate_gate_rejected_per_run(self):
        gate = make_gate()
        with pytest.raises(vs.ScheduleSliceError):
            vs.validate_gate_run_accounting(gates=(gate, gate))

    def test_all_closed_does_not_block(self):
        prior = make_gate()
        closed = make_gate(gate_state=vs.GATE_CLOSED,
                           decision_status=vs.GATE_DECISION_RESOLVED,
                           prior_gate_id=prior.gate_id,
                           resolved_by_decision_id="d-1")
        acc = vs.validate_gate_run_accounting(gates=(closed,))
        assert acc.blocks_domain_complete is False
        assert vs.all_gates_closed((closed,)) is True

    def test_cutoff_scope_gate_kind_closed_set(self):
        gate = make_gate(gate_kind=vs.GATE_CUTOFF_SCOPE,
                         decision_status=vs.GATE_DECISION_BOUNDARY)
        assert gate.gate_kind == vs.GATE_CUTOFF_SCOPE


# ===========================================================================
# 8. Typed schedule anchors (§5.3)
# ===========================================================================

class TestTypedAnchors:
    def test_producer_anchor_bound_full_dimensions(self):
        ref = make_producer_anchor_ref()
        out = vs.bind_typed_schedule_anchor(
            relation_type=vs.RELATION_FIRST_IP_DOSE, subject_ref=SUBJECT,
            site_ref=SITE_REF, producer_ref=ref,
            producer_domain=vs.OWNER_D03, producer_unit_id="ip-unit-1",
            stable_source_event_key="ip_exposure:cd-1",
            content_hash=ref.content_hash,
            phase="phase-1", episode_id="ep-1",
            anchor_start="2026-01-05", anchor_end="2026-01-05",
            date_precision=vs.PRECISION_DAY, timezone="")
        assert out.is_bound
        assert out.anchor_ref.producer_domain == vs.OWNER_D03
        assert out.anchor_ref.anchor_ref_id.startswith("d05-anchor-")
        assert out.anchor_ref.anchor_start == "2026-01-05"
        assert out.anchor_ref.stable_source_event_key == "ip_exposure:cd-1"

    def test_wrong_phase_fails_closed(self):
        ref = make_producer_anchor_ref(phase="phase-1")
        out = bind_full(full_anchor_expected(ref, phase="phase-2"))
        assert not out.is_bound
        assert vs.REASON_PHASE_OR_EPISODE_MISMATCH in out.gate.reason_codes

    def test_wrong_episode_fails_closed(self):
        ref = make_producer_anchor_ref(producer_domain=vs.OWNER_D04,
                                       episode_id="ep-1",
                                       relation_type=vs.RELATION_RANDOMIZATION)
        out = bind_full(full_anchor_expected(
            ref, relation_type=vs.RELATION_RANDOMIZATION,
            producer_domain=vs.OWNER_D04, episode_id="ep-2"))
        assert not out.is_bound
        assert vs.REASON_PHASE_OR_EPISODE_MISMATCH in out.gate.reason_codes

    def test_wrong_subject_fails_closed(self):
        ref = make_producer_anchor_ref(subject_ref="SYN-OTHER")
        out = bind_full(full_anchor_expected(ref))
        assert not out.is_bound
        assert vs.REASON_SUBJECT_SITE_MISMATCH in out.gate.reason_codes

    def test_wrong_producer_domain_fails_closed(self):
        ref = make_producer_anchor_ref(producer_domain=vs.OWNER_D04)
        out = bind_full(full_anchor_expected(
            ref, producer_domain=vs.OWNER_D03))
        assert not out.is_bound
        assert vs.REASON_WRONG_PRODUCER_DOMAIN in out.gate.reason_codes

    def test_wrong_consumer_domain_fails_closed(self):
        ref = make_producer_anchor_ref()
        other = vs.CrossDomainEvidenceRef(
            evidence_ref_id="x", producer_domain=vs.OWNER_D03,
            consumer_domain=vs.OWNER_D04, evidence_role="first_dose",
            source_locator=ref.source_locator,
            producer_unit_id=ref.producer_unit_id,
            content_hash=ref.content_hash,
            context_payload=ref.context_payload)
        out = bind_full(full_anchor_expected(other))
        assert not out.is_bound
        assert vs.REASON_WRONG_CONSUMER_DOMAIN in out.gate.reason_codes

    def test_content_hash_mismatch_fails_closed(self):
        ref = make_producer_anchor_ref()

        class StaleRef(vs.CrossDomainEvidenceRef):
            """Simulate a corrupted/stale producer ref whose stored hash no
            longer verifies against its payload (shared contracts reject
            non-canonical hashes at construction, so this is the only way a
            mismatched ref can reach the binder)."""

            def verify_content_hash(self) -> bool:
                return False

        stale = StaleRef(
            evidence_ref_id="x", producer_domain=vs.OWNER_D03,
            consumer_domain=vs.D05_DOMAIN, evidence_role="first_dose",
            source_locator=ref.source_locator, producer_unit_id="u",
            content_hash=ref.content_hash, context_payload=ref.context_payload)
        out = bind_full(full_anchor_expected(stale))
        assert not out.is_bound
        assert vs.REASON_ANCHOR_CONFLICT in out.gate.reason_codes

    def test_missing_producer_ref_gate(self):
        kw = full_anchor_expected()
        kw["producer_ref"] = None
        out = bind_full(kw)
        assert not out.is_bound
        assert vs.REASON_ANCHOR_MISSING in out.gate.reason_codes

    def test_missing_time_interval_gate(self):
        # Context interval keys present but empty while the expected
        # interval is non-empty: missing evidence, never a substitute.
        ref = make_producer_anchor_ref(anchor_start="", anchor_end="")
        out = bind_full(full_anchor_expected(ref))
        assert not out.is_bound
        assert vs.REASON_ANCHOR_MISSING in out.gate.reason_codes

    def test_fixed_reference_anchor(self):
        out = vs.bind_typed_schedule_anchor(
            relation_type=vs.RELATION_FIXED_REFERENCE, subject_ref=SUBJECT,
            site_ref=SITE_REF, anchor_start="2026-01-05",
            anchor_end="2026-01-05")
        assert out.is_bound
        assert out.anchor_ref.producer_domain == ""
        assert out.anchor_ref.relation_type == vs.RELATION_FIXED_REFERENCE

    def test_fixed_anchor_without_time_gate(self):
        out = vs.bind_typed_schedule_anchor(
            relation_type=vs.RELATION_FIXED_REFERENCE, subject_ref=SUBJECT,
            site_ref=SITE_REF)
        assert not out.is_bound
        assert vs.REASON_ANCHOR_MISSING in out.gate.reason_codes

    def test_internal_anchor_with_producer_ref_raises(self):
        ref = make_producer_anchor_ref()
        with pytest.raises(vs.ScheduleSliceError):
            vs.bind_typed_schedule_anchor(
                relation_type=vs.RELATION_FIXED_REFERENCE,
                subject_ref=SUBJECT, site_ref=SITE_REF,
                producer_ref=ref, anchor_start="2026-01-05",
                anchor_end="2026-01-05")

    def test_anchor_ref_id_stable_across_snapshot_revisions(self):
        # Same producer event (same table_semantic:record_id) in a later
        # snapshot/revision -> identical anchor identity, different lineage.
        loc_a = make_locator("cd-1", "ip_exposure",
                             snapshot_id="snap-accepted-001")
        loc_b = make_locator("cd-1", "ip_exposure",
                             snapshot_id="snap-accepted-002")
        ref_a = make_producer_anchor_ref(source_locator=loc_a)
        ref_b = make_producer_anchor_ref(source_locator=loc_b)
        kw_a = full_anchor_expected(ref_a)
        kw_b = full_anchor_expected(ref_b)
        a = vs.bind_typed_schedule_anchor(
            relation_type=kw_a["relation_type"],
            subject_ref=kw_a["subject_ref"], site_ref=kw_a["site_ref"],
            producer_ref=kw_a["producer_ref"],
            producer_domain=kw_a["producer_domain"],
            producer_unit_id=kw_a["producer_unit_id"],
            stable_source_event_key=kw_a["stable_source_event_key"],
            content_hash=kw_a["content_hash"], phase=kw_a["phase"],
            episode_id=kw_a["episode_id"], anchor_start=kw_a["anchor_start"],
            anchor_end=kw_a["anchor_end"],
            date_precision=kw_a["date_precision"], timezone=kw_a["timezone"],
            source_locators=(loc_a,))
        b = vs.bind_typed_schedule_anchor(
            relation_type=kw_b["relation_type"],
            subject_ref=kw_b["subject_ref"], site_ref=kw_b["site_ref"],
            producer_ref=kw_b["producer_ref"],
            producer_domain=kw_b["producer_domain"],
            producer_unit_id=kw_b["producer_unit_id"],
            stable_source_event_key=kw_b["stable_source_event_key"],
            content_hash=kw_b["content_hash"], phase=kw_b["phase"],
            episode_id=kw_b["episode_id"], anchor_start=kw_b["anchor_start"],
            anchor_end=kw_b["anchor_end"],
            date_precision=kw_b["date_precision"], timezone=kw_b["timezone"],
            source_locators=(loc_b,))
        assert a.anchor_ref.anchor_ref_id == b.anchor_ref.anchor_ref_id
        assert a.anchor_ref.lineage_hash != b.anchor_ref.lineage_hash

    def test_producer_anchor_requires_hex_content_hash(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.TypedScheduleAnchorRef(
                anchor_ref_id="", producer_domain=vs.OWNER_D03,
                producer_unit_id="u", stable_source_event_key="k",
                content_hash="not-hex", subject_ref=SUBJECT, site_ref=SITE_REF,
                phase="p", episode_id="e", anchor_start="2026-01-05",
                anchor_end="2026-01-05", date_precision=vs.PRECISION_DAY,
                timezone="", relation_type=vs.RELATION_FIRST_IP_DOSE)

    def test_sub_day_anchor_requires_timezone(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.TypedScheduleAnchorRef(
                anchor_ref_id="", producer_domain="", producer_unit_id="",
                stable_source_event_key="", content_hash="",
                subject_ref=SUBJECT, site_ref=SITE_REF, phase="", episode_id="",
                anchor_start="2026-01-05T10:00", anchor_end="2026-01-05T10:00",
                date_precision=vs.PRECISION_HOUR, timezone="",
                relation_type=vs.RELATION_FIXED_REFERENCE)


# ===========================================================================
# 8b. Full-dimension anchor matching (§5.3) -- every declared dimension
# must match exactly; same-day dates or a plain locator can never
# substitute.
# ===========================================================================

class TestAnchorFullDimensionMatching:
    def _full_expected(self, ref=None, **overrides):
        kw = full_anchor_expected(ref, **overrides)
        return kw

    def test_all_dimensions_match_true(self):
        assert vs.anchor_binding_matches(**self._full_expected()) is True

    def test_missing_producer_ref_false(self):
        kw = self._full_expected()
        kw["producer_ref"] = None
        assert vs.anchor_binding_matches(**kw) is False

    def test_producer_domain_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            producer_domain="D04_protocol_compliance")) is False

    def test_producer_unit_id_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            producer_unit_id="ip-unit-999")) is False

    def test_stable_source_event_key_wrong_false(self):
        # Same day, wrong source record: a plain locator cannot substitute.
        assert vs.anchor_binding_matches(**self._full_expected(
            stable_source_event_key="ip_exposure:cd-999")) is False

    def test_content_hash_wrong_false(self):
        other = make_producer_anchor_ref(record_id="cd-2")
        assert vs.anchor_binding_matches(**self._full_expected(
            content_hash=other.content_hash)) is False

    def test_subject_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            subject_ref="SYN-OTHER")) is False

    def test_site_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            site_ref="SITE02")) is False

    def test_phase_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            phase="phase-9")) is False

    def test_phase_missing_on_ref_false(self):
        ref = make_producer_anchor_ref(phase="")
        assert vs.anchor_binding_matches(**self._full_expected(
            ref, phase="phase-1")) is False

    def test_episode_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            episode_id="ep-9")) is False

    def test_anchor_start_wrong_false(self):
        # Same end date, different start: same-day proximity cannot
        # substitute for an exact interval endpoint.
        assert vs.anchor_binding_matches(**self._full_expected(
            anchor_start="2026-01-06")) is False

    def test_anchor_end_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            anchor_end="2026-01-06")) is False

    def test_date_precision_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            date_precision=vs.PRECISION_MONTH)) is False

    def test_timezone_wrong_false(self):
        assert vs.anchor_binding_matches(**self._full_expected(
            timezone="+08:00")) is False

    def test_relation_type_conflict_via_ref_context_false(self):
        ref = make_producer_anchor_ref(relation_type="randomization")
        assert vs.anchor_binding_matches(**self._full_expected(ref)) is False

    def test_binder_gate_for_each_wrong_dimension(self):
        cases = [
            (None, dict(producer_domain="D04_protocol_compliance"),
             vs.REASON_WRONG_PRODUCER_DOMAIN),
            (None, dict(producer_unit_id="ip-unit-999"),
             vs.REASON_ANCHOR_CONFLICT),
            (None, dict(stable_source_event_key="ip_exposure:cd-999"),
             vs.REASON_ANCHOR_CONFLICT),
            (None, dict(phase="phase-9"),
             vs.REASON_PHASE_OR_EPISODE_MISMATCH),
            (None, dict(episode_id="ep-9"),
             vs.REASON_PHASE_OR_EPISODE_MISMATCH),
            (None, dict(anchor_start="2026-01-06"),
             vs.REASON_INTERVAL_MISMATCH),
            (None, dict(anchor_end="2026-01-06"),
             vs.REASON_INTERVAL_MISMATCH),
            (None, dict(date_precision=vs.PRECISION_MONTH),
             vs.REASON_PRECISION_OR_TIMEZONE_MISMATCH),
            (make_producer_anchor_ref(timezone="UTC"),
             dict(timezone="+08:00"),
             vs.REASON_PRECISION_OR_TIMEZONE_MISMATCH),
        ]
        for ref, overrides, expected_reason in cases:
            kw = self._full_expected(ref, **overrides)
            out = bind_full(kw)
            assert not out.is_bound, overrides
            assert expected_reason in out.gate.reason_codes, overrides
            assert out.gate.gate_kind == vs.GATE_ANCHOR

    def test_same_day_cannot_substitute_wrong_unit_id(self):
        # Date identical to the ref, only the producer unit differs:
        # must fail closed -- no nearest-date absorption.
        ref = make_producer_anchor_ref(producer_unit_id="ip-unit-1")
        kw = self._full_expected(ref, producer_unit_id="ip-unit-2")
        assert vs.anchor_binding_matches(**kw) is False
        out = bind_full(kw)
        assert not out.is_bound
        assert vs.REASON_ANCHOR_CONFLICT in out.gate.reason_codes

    def test_ref_claimed_relation_type_conflict_gate(self):
        ref = make_producer_anchor_ref(relation_type="randomization")
        out = bind_full(full_anchor_expected(ref))
        assert not out.is_bound
        assert vs.REASON_INVALID_RELATION_TYPE in out.gate.reason_codes


# ===========================================================================
# 8c. Missing dimensions fail closed (§5.3) -- omission never behaves as
# a wildcard: every missing expected dimension and every missing
# producer-context dimension is rejected.
# ===========================================================================

class TestAnchorMissingDimensionsFailClosed:
    REQUIRED_EXPECTED = [
        "producer_domain", "producer_unit_id", "stable_source_event_key",
        "content_hash", "phase", "anchor_start", "anchor_end",
        "date_precision",
    ]

    REQUIRED_CONTEXT = [
        "subject_ref", "site_ref", "phase", "episode_id", "anchor_start",
        "anchor_end", "date_precision", "timezone", "relation_type",
    ]

    @pytest.mark.parametrize("dim", REQUIRED_EXPECTED)
    def test_missing_expected_dimension_fails_closed(self, dim):
        ref = make_producer_anchor_ref()
        kw = full_anchor_expected(ref)
        kw[dim] = ""  # an omitted expected value must not act as a wildcard
        assert vs.anchor_binding_matches(**kw) is False
        out = bind_full(kw)
        assert not out.is_bound
        assert vs.REASON_ANCHOR_MISSING in out.gate.reason_codes

    @pytest.mark.parametrize("dim", REQUIRED_CONTEXT)
    def test_missing_producer_context_dimension_fails_closed(self, dim):
        ref = make_anchor_ref_missing_ctx(dim)
        kw = full_anchor_expected(ref)
        assert vs.anchor_binding_matches(**kw) is False
        out = bind_full(kw)
        assert not out.is_bound
        if dim in ("subject_ref", "site_ref"):
            assert vs.REASON_SUBJECT_SITE_MISMATCH in out.gate.reason_codes
        else:
            assert vs.REASON_ANCHOR_MISSING in out.gate.reason_codes

    def test_episode_id_empty_requires_context_key_and_empty_expected(self):
        # ``episode_id`` may be the explicit empty value only when the
        # context contains the key and the expected value is likewise
        # empty; missing context key or non-empty expected fails closed.
        ref = make_anchor_ref_missing_ctx("episode_id")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref, episode_id="")) is False  # context key absent
        ref2 = make_producer_anchor_ref(episode_id="")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref2, episode_id="")) is True  # explicit empty on both sides
        ref3 = make_producer_anchor_ref(episode_id="")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref3, episode_id="ep-1")) is False  # context empty vs expected

    def test_timezone_empty_requires_context_key_and_empty_expected(self):
        ref = make_anchor_ref_missing_ctx("timezone")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref, timezone="")) is False  # context key absent
        ref2 = make_producer_anchor_ref(timezone="")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref2, timezone="")) is True  # explicit empty on both sides
        ref3 = make_producer_anchor_ref(timezone="+08:00")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref3, timezone="+08:00")) is True  # explicit equal non-empty
        ref4 = make_producer_anchor_ref(timezone="+08:00")
        assert vs.anchor_binding_matches(**full_anchor_expected(
            ref4, timezone="")) is False  # context non-empty vs expected


# ===========================================================================
# 9. Assignment and consumption ledger objects (§5.1, §7.2)
# ===========================================================================

class TestAssignmentsAndLedger:
    def test_visit_assignment_unique_requires_selected_candidate(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT,
                actual_bundle_id="b-1",
                candidate_planned_visit_ids=("v1",),
                decision_status=vs.VISIT_ASSIGNMENT_UNIQUE,
                selected_planned_visit_id="")
        d = vs.VisitAssignmentDecision(
            assignment_id="", subject_ref=SUBJECT, actual_bundle_id="b-1",
            candidate_planned_visit_ids=("v1", "v2"),
            decision_status=vs.VISIT_ASSIGNMENT_UNIQUE,
            selected_planned_visit_id="v2")
        assert d.assignment_id.startswith("d05-va-")

    def test_visit_assignment_non_unique_forbids_selected(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT, actual_bundle_id="b-1",
                candidate_planned_visit_ids=("v1",),
                decision_status=vs.VISIT_ASSIGNMENT_NOT_EVALUABLE,
                selected_planned_visit_id="v1")

    def test_visit_assignment_multi_feasible_requires_two(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT, actual_bundle_id="b-1",
                candidate_planned_visit_ids=("v1",),
                decision_status=vs.VISIT_ASSIGNMENT_MULTI_FEASIBLE)

    def test_activity_assignment_unique_exactly_one_selected(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActivityAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT,
                actual_activity_id="a-1",
                candidate_planned_activity_ids=("p1",),
                decision_status=vs.ACTIVITY_ASSIGNMENT_UNIQUE)
        d = vs.ActivityAssignmentDecision(
            assignment_id="", subject_ref=SUBJECT, actual_activity_id="a-1",
            candidate_planned_activity_ids=("p1", "p2"),
            decision_status=vs.ACTIVITY_ASSIGNMENT_UNIQUE,
            selected_planned_activity_ids=("p2",))
        assert d.assignment_id.startswith("d05-aa-")

    def test_activity_assignment_duplicate_consumption(self):
        d = vs.ActivityAssignmentDecision(
            assignment_id="", subject_ref=SUBJECT, actual_activity_id="a-1",
            candidate_planned_activity_ids=("p1", "p2"),
            decision_status=vs.ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
            selected_planned_activity_ids=("p1", "p2"))
        assert d.decision_status == vs.ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActivityAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT,
                actual_activity_id="a-1",
                candidate_planned_activity_ids=("p1", "p2"),
                decision_status=vs.ACTIVITY_ASSIGNMENT_UNIQUE,
                selected_planned_activity_ids=("p1", "p2"))

    def test_selected_must_be_in_candidates(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActivityAssignmentDecision(
                assignment_id="", subject_ref=SUBJECT, actual_activity_id="a-1",
                candidate_planned_activity_ids=("p1",),
                decision_status=vs.ACTIVITY_ASSIGNMENT_UNIQUE,
                selected_planned_activity_ids=("p9",))

    def test_ledger_single_consumption_closed(self):
        led = vs.ActualActivityConsumptionLedger(
            ledger_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            actual_activity_id="a-1",
            consuming_planned_activity_ids=("p1",),
            allowed_multiplicity=1, assignment_ids=("aa-1",),
            reverse_coverage_status=vs.REVERSE_COVERAGE_CLOSED)
        assert led.ledger_id.startswith("d05-aa-ledger-")
        assert led.reverse_coverage_status == vs.REVERSE_COVERAGE_CLOSED

    def test_ledger_multi_consumption_without_rule_not_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ActualActivityConsumptionLedger(
                ledger_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
                actual_activity_id="a-1",
                consuming_planned_activity_ids=("p1", "p2"),
                allowed_multiplicity=1, assignment_ids=("aa-1",),
                reverse_coverage_status=vs.REVERSE_COVERAGE_CLOSED)
        led = vs.ActualActivityConsumptionLedger(
            ledger_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            actual_activity_id="a-1",
            consuming_planned_activity_ids=("p1", "p2"),
            allowed_multiplicity=1, assignment_ids=("aa-1",),
            reverse_coverage_status=vs.REVERSE_COVERAGE_OPEN)
        assert led.reverse_coverage_status == vs.REVERSE_COVERAGE_OPEN

    def test_ledger_multi_consumption_with_rule_closed(self):
        led = vs.ActualActivityConsumptionLedger(
            ledger_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            actual_activity_id="a-1",
            consuming_planned_activity_ids=("p1", "p2"),
            allowed_multiplicity=2, repeat_rule_id="rr-1",
            assignment_ids=("aa-1", "aa-2"),
            reverse_coverage_status=vs.REVERSE_COVERAGE_CLOSED)
        assert led.repeat_rule_id == "rr-1"

    def test_ledger_deterministic(self):
        kw = dict(subject_ref=SUBJECT, site_ref=SITE_REF,
                  actual_activity_id="a-1",
                  consuming_planned_activity_ids=("p1",),
                  allowed_multiplicity=1, assignment_ids=("aa-1",))
        a = vs.ActualActivityConsumptionLedger(ledger_id="", **kw)
        b = vs.ActualActivityConsumptionLedger(ledger_id="", **kw)
        assert a.ledger_id == b.ledger_id


# ===========================================================================
# 10. Interpretation ledger and evaluation unit (§3.3, §3.4, §6)
# ===========================================================================

class TestInterpretationLedgerAndUnits:
    def test_ledger_partition_and_disjoint(self):
        led = vs.ScheduleInterpretationLedger(
            ledger_id="", decision_scope=vs.INTERPRET_SCOPE_MERGE,
            interpretation_ids=("i1", "i2"),
            accepted_interpretation_ids=("i1",),
            rejected_interpretation_ids=("i2",),
            predicate_results=(("i1", vs.PREDICATE_FALSE),
                               ("i2", vs.PREDICATE_TRUE)),
            rejection_reason_codes=(vs.REASON_INTERVAL_MISMATCH,))
        assert led.ledger_id.startswith("d05-interp-")

    def test_ledger_accepted_rejected_overlap_fails(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ScheduleInterpretationLedger(
                ledger_id="", decision_scope=vs.INTERPRET_SCOPE_MERGE,
                interpretation_ids=("i1",),
                accepted_interpretation_ids=("i1",),
                rejected_interpretation_ids=("i1",),
                predicate_results=(("i1", vs.PREDICATE_FALSE),),
                rejection_reason_codes=(vs.REASON_INTERVAL_MISMATCH,))

    def test_ledger_missing_coverage_fails(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ScheduleInterpretationLedger(
                ledger_id="", decision_scope=vs.INTERPRET_SCOPE_MERGE,
                interpretation_ids=("i1", "i2"),
                accepted_interpretation_ids=("i1",),
                rejected_interpretation_ids=("i2",),
                predicate_results=(("i1", vs.PREDICATE_FALSE),),
                rejection_reason_codes=(vs.REASON_INTERVAL_MISMATCH,))

    def test_ledger_rejected_without_reason_fails(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.ScheduleInterpretationLedger(
                ledger_id="", decision_scope=vs.INTERPRET_SCOPE_MERGE,
                interpretation_ids=("i1", "i2"),
                accepted_interpretation_ids=("i1",),
                rejected_interpretation_ids=("i2",),
                predicate_results=(("i1", vs.PREDICATE_FALSE),
                                   ("i2", vs.PREDICATE_TRUE)),
                rejection_reason_codes=())

    def _unit(self, **kw):
        base = dict(
            unit_id="", project_ref=PROJECT_ID, subject_ref=SUBJECT,
            site_ref=SITE_REF, unit_kind=vs.UNIT_VISIT_OCCURRENCE,
            planned_visit_key="PV-KEY-1",
            evaluation_window_id=vs.schedule_evaluation_window_id(
                anchor_kind=vs.RELATION_FIXED_REFERENCE,
                anchor_source_role=vs.ANCHOR_ROLE_VISIT_SCHEDULE,
                calendar_semantics=vs.STUDY_DAY, study_day_zero_exists=True,
                lower_offset="-3", upper_offset="+3",
                lower_endpoint_inclusive=True,
                upper_endpoint_inclusive=False, grace_period="",
                date_precision=vs.PRECISION_DAY, timezone="",
                propagation_rule=vs.PROPAGATION_FIXED_ANCHOR),
            rule_id="rule-1")
        base.update(kw)
        return vs.ScheduleEvaluationUnit(**base)

    def test_unit_id_stable_across_locator_lineage(self):
        a = self._unit(source_locator_ids=("loc-a",))
        b = self._unit(source_locator_ids=("loc-b",))
        assert a.unit_id == b.unit_id
        assert a.lineage_hash != b.lineage_hash

    def test_unit_kind_requires_visit_key(self):
        with pytest.raises(vs.ScheduleSliceError):
            self._unit(unit_kind=vs.UNIT_VISIT_OCCURRENCE,
                       planned_visit_key="")

    def test_activity_unit_requires_activity_key(self):
        with pytest.raises(vs.ScheduleSliceError):
            self._unit(unit_kind=vs.UNIT_ACTIVITY_OCCURRENCE,
                       planned_visit_key="", planned_activity_key="")

    def test_actual_assignment_unit_requires_actual_key(self):
        with pytest.raises(vs.ScheduleSliceError):
            self._unit(unit_kind=vs.UNIT_ACTUAL_ASSIGNMENT,
                       planned_visit_key="")

    def test_stable_core_content_addressed_and_identity_sensitive(self):
        u = self._unit()
        for token in ("run-", "snap-", "revision", "rev-"):
            assert token not in u.stable_core  # hash core never embeds run ids
        # Same obligation reruns to the same core.
        assert u.stable_core == self._unit().stable_core
        # A different obligation key changes the core.
        assert u.stable_core != self._unit(planned_visit_key="PV-KEY-2").stable_core
        # Locators never enter the stable core (lineage only).
        assert u.stable_core == self._unit(source_locator_ids=("loc-b",)).stable_core

    def test_unit_and_classifier_stable_across_reruns(self):
        a = self._unit()
        b = self._unit()
        assert a.unit_id == b.unit_id
        assert a.classifier == b.classifier

    def test_unit_kind_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            self._unit(unit_kind="visit_scoring")


# ===========================================================================
# 11. Coverage-gap notice and journey schemas (§3.3, §8.5, §10)
# ===========================================================================

class TestGapNoticeAndJourney:
    def test_gap_notice_deterministic(self):
        kw = dict(unit_id="u-1", reason_code=vs.REASON_TIME_ROLE_MISSING,
                  missing_evidence_roles=("visit_date",),
                  audience_text="访视日期缺失，暂无法核实")
        a = vs.VisitCoverageGapNotice(notice_id="", **kw)
        b = vs.VisitCoverageGapNotice(notice_id="", **kw)
        assert a.notice_id == b.notice_id
        assert a.notice_id.startswith("d05-gap-")

    def test_gap_notice_reason_closed(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitCoverageGapNotice(
                notice_id="", unit_id="u-1", reason_code="missing_data",
                audience_text="资料不足")

    def test_gap_notice_requires_audience_text(self):
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitCoverageGapNotice(
                notice_id="", unit_id="u-1",
                reason_code=vs.REASON_TIME_ROLE_MISSING, audience_text="")

    def test_planned_visit_marker(self):
        m = vs.PlannedVisitMarker(
            marker_id="", planned_visit_id="pv-1", audience_name="第 4 周访视",
            phase="treatment", nominal_anchor="2026-03-01",
            window_start="2026-02-26", window_end="2026-03-04",
            date_precision=vs.PRECISION_DAY, status_hint=vs.STATUS_DUE)
        assert m.marker_id.startswith("d05-pvm-")
        with pytest.raises(vs.ScheduleSliceError):
            vs.PlannedVisitMarker(
                marker_id="", planned_visit_id="pv-1",
                audience_name="第 4 周访视", phase="treatment",
                nominal_anchor="2026-03-01", window_start="2026-02-26",
                window_end="2026-03-04", date_precision=vs.PRECISION_DAY,
                status_hint="occurred")

    def test_actual_encounter_marker_anchor_states(self):
        for state in (vs.ANCHOR_STATE_DATED, vs.ANCHOR_STATE_PARTIAL,
                      vs.ANCHOR_STATE_PENDING_TIME,
                      vs.ANCHOR_STATE_OUT_OF_CUTOFF):
            m = vs.ActualEncounterMarker(
                marker_id="", encounter_id="enc-1",
                encounter_kind=vs.ENCOUNTER_ONSITE, anchor_state=state,
                start="2026-03-05", end="2026-03-05",
                date_precision=vs.PRECISION_DAY, assignment_id="va-1")
            assert m.marker_id.startswith("d05-aem-")

    def test_risk_marker_priority_closed(self):
        kw = dict(marker_id="", audience_label="访视时间待核实",
                  monitoring_priority="high", anchor_kind=vs.RELATION_FIXED_REFERENCE,
                  anchor_state=vs.ANCHOR_STATE_DATED, unit_id="u-1",
                  candidate_or_risk_id="c-1", anchor_start="2026-03-05",
                  date_precision=vs.PRECISION_DAY)
        m = vs.VisitRiskMarker(**kw)
        assert m.marker_id.startswith("d05-risk-marker-")
        with pytest.raises(vs.ScheduleSliceError):
            vs.VisitRiskMarker(**{**kw, "monitoring_priority": "critical"})

    def test_projection_payload_hash_deterministic(self):
        pm = vs.PlannedVisitMarker(
            marker_id="", planned_visit_id="pv-1", audience_name="第 4 周访视",
            phase="treatment", nominal_anchor="2026-03-01",
            window_start="2026-02-26", window_end="2026-03-04",
            date_precision=vs.PRECISION_DAY, status_hint=vs.STATUS_EVALUATED)
        ae = vs.ActualEncounterMarker(
            marker_id="", encounter_id="enc-1",
            encounter_kind=vs.ENCOUNTER_ONSITE, anchor_state=vs.ANCHOR_STATE_DATED,
            start="2026-03-05", end="2026-03-05",
            date_precision=vs.PRECISION_DAY, assignment_id="va-1")
        kw = dict(projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
                  planned_visit_markers=(pm,),
                  actual_encounter_markers=(ae,),
                  assignment_edges=(("pv-1", "enc-1"),))
        a = vs.VisitJourneyProjection(**kw)
        b = vs.VisitJourneyProjection(**{**kw, "assignment_edges": (
            ("pv-1", "enc-1"),)})
        assert a.projection_id == b.projection_id
        assert a.payload_hash == b.payload_hash
        assert a.projection_id.startswith("d05-proj-")

    def test_projection_edges_canonical_sorted(self):
        pm = vs.PlannedVisitMarker(
            marker_id="", planned_visit_id="pv-1", audience_name="第 4 周访视",
            phase="treatment", nominal_anchor="2026-03-01",
            window_start="2026-02-26", window_end="2026-03-04",
            date_precision=vs.PRECISION_DAY, status_hint=vs.STATUS_EVALUATED)
        proj = vs.VisitJourneyProjection(
            projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            planned_visit_markers=(pm,),
            assignment_edges=(("pv-2", "enc-2"), ("pv-1", "enc-1")))
        assert proj.assignment_edges == (("pv-1", "enc-1"),
                                         ("pv-2", "enc-2"))

    # -- JOURney root identity covers the auxiliary marker collections
    # (worker_03 repair: activity/pending/out-of-cutoff marker ids are part
    # of ``projection_id`` / ``payload_hash``; removing or changing any
    # marker in a collection changes the root identity, fail-closed).

    def _base_auxiliary_projection(self):
        """A projection carrying one marker in each of the three auxiliary
        collections plus a planned marker, so each collection is
        non-empty and mutatable in isolation."""
        from mm_r4.visit_schedule_projection import (
            VisitActivityMarker, PendingContextMarker,
            OutOfCutoffContextMarker,
        )
        pm = vs.PlannedVisitMarker(
            marker_id="", planned_visit_id="pv-1", audience_name="第 4 周访视",
            phase="treatment", nominal_anchor="2026-03-01",
            window_start="2026-02-26", window_end="2026-03-04",
            date_precision=vs.PRECISION_DAY, status_hint=vs.STATUS_DUE)
        am = VisitActivityMarker(
            marker_id="", planned_activity_id="pa-1",
            planned_activity_key="PA-A", planned_visit_key="PV-A",
            domain_code="ae", domain_label="AE·不良事件",
            shape_encoding="line-dashed", audience_name="AE 评估",
            status_hint=vs.STATUS_DUE)
        pend = PendingContextMarker(
            marker_id="", context_type="missing_date",
            subject_ref=SUBJECT, reference_role="encounter",
            reference_key="enc-1")
        ooc = OutOfCutoffContextMarker(
            marker_id="", object_type="encounter", object_id="enc-9",
            subject_ref=SUBJECT)
        return vs.VisitJourneyProjection(
            projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            planned_visit_markers=(pm,),
            activity_markers=(am,),
            pending_time_markers=(pend,),
            out_of_cutoff_markers=(ooc,))

    def test_auxiliary_marker_removal_changes_root_identity(self):
        """Removing any marker from activity/pending/out-of-cutoff changes
        ``projection_id`` and ``payload_hash`` (tamper-sensitive)."""
        base = self._base_auxiliary_projection()
        for field in ("activity_markers", "pending_time_markers",
                      "out_of_cutoff_markers"):
            kw = dict(
                projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
                planned_visit_markers=base.planned_visit_markers,
                assignment_edges=base.assignment_edges,
                risk_markers=base.risk_markers,
                activity_markers=base.activity_markers,
                pending_time_markers=base.pending_time_markers,
                out_of_cutoff_markers=base.out_of_cutoff_markers,
            )
            kw[field] = ()
            removed = vs.VisitJourneyProjection(**kw)
            assert removed.projection_id != base.projection_id, (
                f"removing {field} must not preserve projection_id")
            assert removed.payload_hash != base.payload_hash, (
                f"removing {field} must not preserve payload_hash")

    def test_auxiliary_marker_change_changes_root_identity(self):
        """Changing any marker's content in activity/pending/out-of-cutoff
        changes ``projection_id`` and ``payload_hash`` (a changed marker
        id is content-addressed, so the root identity must follow)."""
        base = self._base_auxiliary_projection()
        from mm_r4.visit_schedule_projection import (
            VisitActivityMarker, PendingContextMarker,
            OutOfCutoffContextMarker,
        )
        changed_activity = VisitActivityMarker(
            marker_id="", planned_activity_id="pa-1",
            planned_activity_key="PA-A", planned_visit_key="PV-A",
            domain_code="ae", domain_label="AE·不良事件",
            shape_encoding="line-dashed", audience_name="AE 评估",
            status_hint=vs.STATUS_EVALUATED)  # changed status_hint
        changed_pending = PendingContextMarker(
            marker_id="", context_type="partial_date",
            subject_ref=SUBJECT, reference_role="encounter",
            reference_key="enc-1")  # changed context_type
        changed_ooc = OutOfCutoffContextMarker(
            marker_id="", object_type="activity", object_id="enc-9",
            subject_ref=SUBJECT)  # changed object_type
        variants = {
            "activity_markers": (changed_activity,),
            "pending_time_markers": (changed_pending,),
            "out_of_cutoff_markers": (changed_ooc,),
        }
        for field, repl in variants.items():
            kw = dict(
                projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
                planned_visit_markers=base.planned_visit_markers,
                assignment_edges=base.assignment_edges,
                risk_markers=base.risk_markers,
                activity_markers=base.activity_markers,
                pending_time_markers=base.pending_time_markers,
                out_of_cutoff_markers=base.out_of_cutoff_markers,
            )
            kw[field] = repl
            changed = vs.VisitJourneyProjection(**kw)
            assert changed.projection_id != base.projection_id, (
                f"changing {field} must not preserve projection_id")
            assert changed.payload_hash != base.payload_hash, (
                f"changing {field} must not preserve payload_hash")

    def test_auxiliary_marker_order_independent_identity(self):
        """Reordering markers within an auxiliary collection preserves the
        root identity (canonical sorted marker-id coverage, not input
        order)."""
        base = self._base_auxiliary_projection()
        from mm_r4.visit_schedule_projection import (
            VisitActivityMarker, PendingContextMarker,
            OutOfCutoffContextMarker,
        )
        am_a = VisitActivityMarker(
            marker_id="", planned_activity_id="pa-a",
            planned_activity_key="PA-A", planned_visit_key="PV-A",
            domain_code="ae", domain_label="AE·不良事件",
            shape_encoding="line-dashed", audience_name="AE 评估",
            status_hint=vs.STATUS_DUE)
        am_b = VisitActivityMarker(
            marker_id="", planned_activity_id="pa-b",
            planned_activity_key="PA-B", planned_visit_key="PV-B",
            domain_code="lab", domain_label="检验·检查",
            shape_encoding="glyph-triangle", audience_name="检验评估",
            status_hint=vs.STATUS_UPCOMING)
        pend_a = PendingContextMarker(
            marker_id="", context_type="missing_date",
            subject_ref=SUBJECT, reference_role="encounter",
            reference_key="enc-1")
        pend_b = PendingContextMarker(
            marker_id="", context_type="pending_assignment",
            subject_ref=SUBJECT, reference_role="visit",
            reference_key="pv-1")
        ooc_a = OutOfCutoffContextMarker(
            marker_id="", object_type="encounter", object_id="enc-9",
            subject_ref=SUBJECT)
        ooc_b = OutOfCutoffContextMarker(
            marker_id="", object_type="activity", object_id="act-9",
            subject_ref=SUBJECT)
        kw = dict(
            projection_id="", subject_ref=SUBJECT, site_ref=SITE_REF,
            planned_visit_markers=base.planned_visit_markers,
            assignment_edges=base.assignment_edges,
            risk_markers=base.risk_markers,
        )
        forward = vs.VisitJourneyProjection(
            **kw, activity_markers=(am_a, am_b),
            pending_time_markers=(pend_a, pend_b),
            out_of_cutoff_markers=(ooc_a, ooc_b))
        reversed_ids = vs.VisitJourneyProjection(
            **kw, activity_markers=(am_b, am_a),
            pending_time_markers=(pend_b, pend_a),
            out_of_cutoff_markers=(ooc_b, ooc_a))
        assert forward.projection_id == reversed_ids.projection_id
        assert forward.payload_hash == reversed_ids.payload_hash

    def test_auxiliary_marker_without_id_fails_closed(self):
        """A marker lacking a content-addressed ``marker_id`` cannot be
        part of the projection identity: the projection construction must
        reject it (fail-closed) rather than silently exclude it from the
        root hash."""
        class NoIdMarker:
            pass
        for field in ("activity_markers", "pending_time_markers",
                      "out_of_cutoff_markers"):
            with pytest.raises(vs.ScheduleSliceError):
                vs.VisitJourneyProjection(
                    projection_id="", subject_ref=SUBJECT,
                    site_ref=SITE_REF,
                    **{field: (NoIdMarker(),)})

    def test_auxiliary_marker_requires_formal_typed_value(self):
        """A forged object with an arbitrary non-empty marker id must not
        enter any auxiliary collection."""
        class ForgedMarker:
            marker_id = "d05-forged-nonempty"
            content = "arbitrary"

        for field in ("activity_markers", "pending_time_markers",
                      "out_of_cutoff_markers"):
            with pytest.raises(vs.ScheduleSliceError, match="requires"):
                vs.VisitJourneyProjection(
                    projection_id="", subject_ref=SUBJECT,
                    site_ref=SITE_REF,
                    **{field: (ForgedMarker(),)})

    def test_auxiliary_marker_content_must_match_its_id(self):
        """Even a formal frozen marker fails closed if its payload is
        tampered while retaining the original content-addressed id."""
        cases = (
            ("activity_markers", "audience_name", "被篡改的评估"),
            ("pending_time_markers", "reason", "被篡改的原因"),
            ("out_of_cutoff_markers", "reason", "被篡改的原因"),
        )
        for field, attribute, changed_value in cases:
            base = self._base_auxiliary_projection()
            marker = getattr(base, field)[0]
            object.__setattr__(marker, attribute, changed_value)
            with pytest.raises(vs.ScheduleSliceError, match="current content"):
                vs.VisitJourneyProjection(
                    projection_id="", subject_ref=SUBJECT,
                    site_ref=SITE_REF,
                    activity_markers=base.activity_markers,
                    pending_time_markers=base.pending_time_markers,
                    out_of_cutoff_markers=base.out_of_cutoff_markers)


# ===========================================================================
# 12. Determinism replay (challenges 35/36/106/107/114)
# ===========================================================================

class TestDeterminismReplay:
    def test_reversed_gate_feasible_order_same_hash(self):
        a = make_gate(feasible=("s1", "s2"))
        b = make_gate(feasible=("s2", "s1"))
        assert a.lineage_hash == b.lineage_hash

    def test_reversed_ledger_input_order_same_hash(self):
        def build(predicate_results):
            return vs.ScheduleInterpretationLedger(
                ledger_id="", decision_scope=vs.INTERPRET_SCOPE_MERGE,
                interpretation_ids=("i1", "i2"),
                accepted_interpretation_ids=("i1",),
                rejected_interpretation_ids=("i2",),
                predicate_results=predicate_results,
                rejection_reason_codes=(vs.REASON_INTERVAL_MISMATCH,))
        a = build((("i1", vs.PREDICATE_FALSE), ("i2", vs.PREDICATE_TRUE)))
        b = build((("i2", vs.PREDICATE_TRUE), ("i1", vs.PREDICATE_FALSE)))
        assert a.ledger_id == b.ledger_id

    def test_reversed_candidate_order_same_assignment_id(self):
        kw = dict(subject_ref=SUBJECT, actual_bundle_id="b-1",
                  decision_status=vs.VISIT_ASSIGNMENT_UNIQUE,
                  selected_planned_visit_id="v2")
        a = vs.VisitAssignmentDecision(
            assignment_id="", candidate_planned_visit_ids=("v1", "v2"), **kw)
        b = vs.VisitAssignmentDecision(
            assignment_id="", candidate_planned_visit_ids=("v2", "v1"), **kw)
        assert a.assignment_id == b.assignment_id

    def test_rerun_identical_hashes(self):
        rec = make_encounter()
        cut = make_cutoff()
        snap = make_snapshot()
        loc = make_locator("enc-1")
        dec1 = vs.resolve_actual_record_scope(
            record=rec, snapshot_as_of=snap, clinical_event_cutoff=cut,
            source_locators=(loc,))
        dec2 = vs.resolve_actual_record_scope(
            record=rec, snapshot_as_of=snap, clinical_event_cutoff=cut,
            source_locators=(loc,))
        assert dec1.scope_decision_id == dec2.scope_decision_id
        b1 = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        b2 = vs.build_actual_encounter_bundle(
            member_encounters=(rec,), subject_ref=SUBJECT, site_ref=SITE_REF,
            episode_kind=vs.EPISODE_SINGLE_CONTACT)
        assert b1.bundle_id == b2.bundle_id
        assert b1.lineage_hash == b2.lineage_hash
