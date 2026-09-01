"""R4-D05 Patient Journey projection tests (worker_03).

Focused deterministic tests for :mod:`mm_r4.visit_schedule_projection`,
which builds the renderer-neutral Chinese Patient Journey projection from
:class:`mm_r4.visit_schedule_evaluator.D05EvaluationOutcome` (frozen §10):

* planned-visit and actual-encounter markers are separate objects joined
  by stable assignment edges (never a single "已记录事项");
* AE / MH / CM / IP给药 / 检验·检查 / 住院·操作 / 症状·疗效 / 方案符合性
  keep differentiated domain lanes with domain code + Chinese short label
  + renderer-neutral shape/line semantics;
* actual dates and raw/actual visit semantics are preserved; missing /
  partial / conflicting dates and pending assignment go to a pending area;
  cutoff-later records go to a separate out-of-cutoff area; a time point
  is never fabricated;
* risk markers bind stable unit / candidate-or-risk / query / source
  locators and preserve supporting / counterevidence / coverage-gap
  semantics;
* audience payload QC rejects internal/log vocabulary.

All data is synthetic/offline.  No real project, provider, dictionary or
product service; port 8911 is never touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
from mm_r4.visit_schedule_projection import (  # noqa: E402
    DOMAIN_TRACKS,
    FORBIDDEN_AUDIENCE_TOKENS,
    OutOfCutoffContextMarker,
    PendingContextMarker,
    VisitActivityMarker,
    audience_payload_clean,
    brush_journey_display,
    center_risk_join_qc,
    cluster_overlapping_risks,
    project_visit_schedule_journey,
    query_draft_parts_complete,
    reject_collapsed_planned_actual,
    reject_copied_center_risks,
    reject_visitnum_as_time_order,
)
from mm_r4.visit_schedule_fixtures import (  # noqa: E402
    build_projection_for_case,
    make_activity,
    make_bundle,
    make_encounter,
    make_planned_activity,
    make_planned_visit,
    make_policy,
    run_evaluation,
)


def _project_case(number: int) -> vs.VisitJourneyProjection:
    return build_projection_for_case(number)


# ===========================================================================
# Marker value objects
# ===========================================================================

class TestVisitActivityMarker:
    def test_content_addressed_and_immutable(self):
        m = VisitActivityMarker(
            marker_id="", planned_activity_id="pa-1",
            planned_activity_key="PA-KEY-1", planned_visit_key="PV-KEY-1",
            domain_code="ae", domain_label="AE·不良事件",
            shape_encoding="line-dashed", audience_name="不良事件评估",
            status_hint=vs.STATUS_EVALUATED)
        assert m.marker_id.startswith("d05-avm-")
        with pytest.raises(Exception):
            m.marker_id = "x"

    def test_closed_domain_code(self):
        with pytest.raises(vs.ScheduleSliceError):
            VisitActivityMarker(
                marker_id="", planned_activity_id="pa-1",
                planned_activity_key="PA-KEY-1",
                planned_visit_key="PV-KEY-1",
                domain_code="not-a-lane",
                domain_label="x", shape_encoding="x",
                audience_name="x", status_hint=vs.STATUS_EVALUATED)

    def test_forbidden_token_rejected(self):
        with pytest.raises(vs.ScheduleSliceError):
            VisitActivityMarker(
                marker_id="", planned_activity_id="pa-1",
                planned_activity_key="PA-KEY-1",
                planned_visit_key="PV-KEY-1",
                domain_code="ae", domain_label="AE",
                shape_encoding="line-dashed",
                audience_name="候选信号", status_hint=vs.STATUS_EVALUATED)


class TestPendingAndOutOfCutoffMarkers:
    def test_pending_context_closed_type(self):
        with pytest.raises(vs.ScheduleSliceError):
            PendingContextMarker(
                marker_id="", context_type="bogus",
                subject_ref="SYN-001", reference_role="visit",
                reference_key="PV-1")

    def test_out_of_cutoff_closed_type(self):
        with pytest.raises(vs.ScheduleSliceError):
            OutOfCutoffContextMarker(
                marker_id="", object_type="bogus", object_id="enc-1",
                subject_ref="SYN-001")

    def test_markers_content_addressed(self):
        p = PendingContextMarker(
            marker_id="", context_type="missing_date",
            subject_ref="SYN-001", reference_role="encounter",
            reference_key="enc-1")
        o = OutOfCutoffContextMarker(
            marker_id="", object_type="encounter", object_id="enc-1",
            subject_ref="SYN-001")
        assert p.marker_id.startswith("d05-pending-")
        assert o.marker_id.startswith("d05-ooc-")


# ===========================================================================
# Audience token QC
# ===========================================================================

class TestAudienceTokenQC:
    def test_clean_text_passes(self):
        assert audience_payload_clean("访视时间待核实")
        assert audience_payload_clean("样本采集时间待核实")

    @pytest.mark.parametrize("token", FORBIDDEN_AUDIENCE_TOKENS)
    def test_forbidden_token_detected(self, token):
        assert audience_payload_clean(token) is False


# ===========================================================================
# Projection structure (challenges 90/91/92/93/94/95/96)
# ===========================================================================

class TestProjectionStructure:
    def test_planned_and_actual_markers_separate(self):
        """Challenge 90: planned and actual are never collapsed into a
        single '已记录事项'."""
        proj = _project_case(45)  # multi-contact merge
        assert proj.planned_visit_markers
        assert proj.actual_encounter_markers
        pm_ids = {m.marker_id for m in proj.planned_visit_markers}
        am_ids = {m.marker_id for m in proj.actual_encounter_markers}
        assert not (pm_ids & am_ids)
        reject_collapsed_planned_actual(proj)
        for edge in proj.assignment_edges:
            assert len(edge) == 2
            assert edge[0] and edge[1]
        assert len(proj.actual_encounter_markers) == 2

    def test_domain_lanes_present(self):
        """AE/MH/CM/IP/检验/住院/症状/方案符合性 keep distinct lanes with
        Chinese labels and non-color shape semantics."""
        assert set(DOMAIN_TRACKS) == {
            "ae", "mh", "cm", "ip", "lab", "proc", "sym", "comp"}
        for code, (label, shape) in DOMAIN_TRACKS.items():
            assert label
            assert shape
            assert shape.startswith("line-") or shape.startswith("glyph-")

    def test_contingent_visitnum_not_time_order(self):
        """Challenge 91: triggered-visit VISITNUM is not used as the real
        time order."""
        from mm_r4.visit_schedule_fixtures import (
            make_bundle, make_encounter, make_planned_visit, run_evaluation)
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
            encounters=[e_b, e_c],
            bundles=[make_bundle(e_b), make_bundle(e_c)],
            priority_policies={"PV-B": make_policy(), "PV-C": make_policy()})
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[base, contingent],
            encounters=[e_b, e_c],
            bundles=[make_bundle(e_b), make_bundle(e_c)])
        dated = [m for m in proj.actual_encounter_markers if m.start]
        time_order = tuple(
            m.encounter_id
            for m in sorted(dated, key=lambda m: (m.start, m.encounter_id)))
        assert time_order == ("enc-b", "enc-c")
        reject_visitnum_as_time_order(
            planned_visits=[base, contingent],
            actual_markers=proj.actual_encounter_markers,
            proposed_encounter_order=time_order)
        with pytest.raises(vs.ScheduleSliceError):
            reject_visitnum_as_time_order(
                planned_visits=[base, contingent],
                actual_markers=proj.actual_encounter_markers,
                proposed_encounter_order=("enc-c", "enc-b"))
        assert not any(r.unit_kind == vs.UNIT_VISIT_ORDER
                       for r in outcome.unit_results)

    def test_missing_date_goes_to_pending_area(self):
        """Challenge 92: a date-missing event lives in the pending area,
        never a fabricated date."""
        enc = make_encounter(encounter_id="enc-1", start="",
                             recorded_visit_code="V4")
        visit = make_planned_visit()
        bundle = make_bundle(enc)
        outcome = run_evaluation(visits=[visit], bundles=[bundle])
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[visit], encounters=[enc],
            bundles=[bundle])
        assert proj.pending_time_markers
        for m in proj.pending_time_markers:
            assert m.context_type == "missing_date"
        for m in proj.actual_encounter_markers:
            assert m.anchor_state in (vs.ANCHOR_STATE_PENDING_TIME,
                                      vs.ANCHOR_STATE_PARTIAL)
            if m.anchor_state == vs.ANCHOR_STATE_PENDING_TIME:
                assert not m.start or m.start == "0001-01-01"

    def test_overlap_cluster_preserves_identity(self):
        """Challenge 93: overlapping high and medium risks keep identity
        and remain expandable."""
        from mm_r4.visit_schedule_fixtures import (
            make_bundle, make_encounter, make_planned_visit, make_policy,
            run_evaluation)
        from mm_r4 import visit_schedule_evaluator as vse
        v_high = make_planned_visit(
            visit_id="pv-h", visit_key="PV-HIGH", official_code="V4",
            audience_name="第 4 周访视", planned_order="4")
        v_med = make_planned_visit(
            visit_id="pv-m", visit_key="PV-MED", official_code="V5",
            audience_name="第 5 周访视", planned_order="5")
        enc_h = make_encounter(encounter_id="enc-h", start="2026-07-10",
                               recorded_visit_code="V4")
        enc_m = make_encounter(encounter_id="enc-m", start="2026-07-10",
                               recorded_visit_code="V5")
        outcome = run_evaluation(
            visits=[v_high, v_med], encounters=[enc_h, enc_m],
            bundles=[make_bundle(enc_h), make_bundle(enc_m)],
            priority_policies={
                "PV-HIGH": make_policy(impact=vse.IMPACT_RIGHTS_SAFETY),
                "PV-MED": make_policy(impact=vse.IMPACT_OTHER_REQUIRED)})
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[v_high, v_med],
            encounters=[enc_h, enc_m],
            bundles=[make_bundle(enc_h), make_bundle(enc_m)])
        highs = [m for m in proj.risk_markers if m.monitoring_priority == "high"]
        meds = [m for m in proj.risk_markers if m.monitoring_priority == "medium"]
        assert highs and meds
        clusters = cluster_overlapping_risks(proj.risk_markers)
        member_ids = [mid for c in clusters for mid in c.member_marker_ids]
        assert len(member_ids) == len(proj.risk_markers)
        assert set(member_ids) == {m.marker_id for m in proj.risk_markers}
        overlap = [c for c in clusters if len(c.member_marker_ids) >= 2]
        assert overlap
        assert all(c.expandable for c in overlap)

    def test_time_brush_does_not_change_l1(self):
        """Challenge 94: filtering/zoom only changes display, not L1/L3."""
        from mm_r4.contracts import L1Disposition
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        outcome = run_evaluation(
            visits=[visit], encounters=[enc], bundles=[bundle])
        timing = next(r for r in outcome.unit_results
                      if r.unit_kind == vs.UNIT_VISIT_TIMING)
        assert timing.l1_disposition == L1Disposition.POSITIVE
        l1_before = dict(outcome.l1_counts())
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[visit], encounters=[enc],
            bundles=[bundle])
        source_hash = proj.payload_hash
        source_risks = tuple(m.marker_id for m in proj.risk_markers)
        assert source_risks
        brushed = brush_journey_display(
            proj, start="2026-06-01", end="2026-06-15")
        assert not brushed.risk_markers
        assert tuple(m.marker_id for m in proj.risk_markers) == source_risks
        assert proj.payload_hash == source_hash
        assert dict(outcome.l1_counts()) == l1_before
        assert timing.l1_disposition == L1Disposition.POSITIVE

    def test_future_visit_visible_not_in_denominator(self):
        """Challenge 95: future visits show on the plan axis without
        entering the expected-set / risk denominator."""
        proj = _project_case(5)
        from mm_r4.visit_schedule_fixtures import build_d05_challenge_matrix
        outcome = build_d05_challenge_matrix().by_number(5).build()
        assert not outcome.expected_units
        assert "PV-FUTURE" in outcome.future_obligation_keys
        future = [m for m in proj.planned_visit_markers
                  if m.planned_visit_id == "pv-future"]
        assert len(future) == 1
        assert future[0].status_hint == vs.STATUS_UPCOMING
        assert not proj.risk_markers

    def test_center_aggregation_does_not_copy_risk(self):
        """Challenge 96: aggregation never copies individual risk."""
        from mm_r4.visit_schedule_fixtures import build_d05_challenge_matrix
        proj = build_d05_challenge_matrix().by_number(93).project()
        assert proj.risk_markers
        summary = center_risk_join_qc((proj,))
        assert summary["copied_marker_ids"] == ()
        assert summary["risk_count"] == len(proj.risk_markers)
        subject_ids = tuple(m.marker_id for m in proj.risk_markers)
        with pytest.raises(vs.ScheduleSliceError):
            reject_copied_center_risks(subject_ids, subject_ids)

    def test_query_draft_missing_part_rejected(self):
        """Challenge 87: a Query missing 依据/发现/行动项 is not complete."""
        assert query_draft_parts_complete(
            "依据：方案 V2.0 规定访视。",
            "发现：参与者 SYN-001 超窗。",
            "行动项：请核实。")
        assert not query_draft_parts_complete(
            "", "发现：x", "行动项：y")
        assert not query_draft_parts_complete(
            "依据：x", "", "行动项：y")
        assert not query_draft_parts_complete(
            "依据：x", "发现：y", "")
        from mm_r4.contracts import CoverageValidationError, QueryDraftRef
        with pytest.raises(CoverageValidationError):
            QueryDraftRef(
                query_id="q-bad", unit_id="u-1", basis="",
                finding="发现：x", action="行动项：y",
                source_locator_ids=("loc-1",))

    def test_projection_deterministic_rerun(self):
        """Challenges 85/107: same inputs -> identical projection hash."""
        a = _project_case(1)
        b = _project_case(1)
        assert a.projection_id == b.projection_id
        assert a.payload_hash == b.payload_hash

    def test_activity_markers_use_domain_lanes(self):
        act = make_planned_activity(
            activity_id="pa-1", activity_key="PA-KEY-1",
            visit_id="pv-v2-1", clinical_domain="efficacy",
            audience_name="疗效评估")
        visit = make_planned_visit()
        enc = make_encounter()
        bundle = make_bundle(enc)
        actual = make_activity(
            activity_id="act-1", start="2026-07-02",
            recorded_code="ASSESS-1", encounter_refs=[enc.encounter_id])
        outcome = run_evaluation(
            visits=[visit], activities=[act], bundles=[bundle],
            actual_activities=[actual])
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[visit], planned_activities=[act],
            encounters=[enc], bundles=[bundle], activities=[actual])
        assert proj.activity_markers
        for m in proj.activity_markers:
            assert m.domain_code in DOMAIN_TRACKS
            assert m.audience_name
            assert m.shape_encoding
            assert m.source_locator_ids

    def test_activity_marker_planned_visit_key_is_logical(self):
        """P1: the versioned planned_visit_id must resolve to the owning
        visit's cross-revision stable logical key, never leak into
        planned_visit_key."""
        visit = make_planned_visit(
            visit_id="pv-versioned", visit_key="PV-LOGICAL",
            official_code="V4", audience_name="第 4 周访视")
        act = make_planned_activity(
            activity_id="pa-1", activity_key="PA-KEY-1",
            visit_id="pv-versioned", clinical_domain="efficacy",
            audience_name="疗效评估")
        enc = make_encounter()
        bundle = make_bundle(enc)
        actual = make_activity(
            activity_id="act-1", recorded_code="ASSESS-1",
            encounter_refs=[enc.encounter_id])
        outcome = run_evaluation(
            visits=[visit], activities=[act], bundles=[bundle],
            actual_activities=[actual])
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[visit], planned_activities=[act],
            encounters=[enc], bundles=[bundle], activities=[actual])
        assert proj.activity_markers
        for m in proj.activity_markers:
            assert m.planned_visit_key == "PV-LOGICAL"
            assert m.planned_visit_key != "pv-versioned"

    def test_activity_marker_unresolved_visit_fails_closed(self):
        """P1: an activity whose planned_visit_id cannot be resolved to an
        owning planned visit must fail closed rather than write a versioned
        id into a stable-key field."""
        visit = make_planned_visit(
            visit_id="pv-v2-1", visit_key="PV-KEY-1")
        act = make_planned_activity(
            activity_id="pa-1", activity_key="PA-KEY-1",
            visit_id="pv-v2-1", clinical_domain="efficacy",
            audience_name="疗效评估")
        enc = make_encounter()
        bundle = make_bundle(enc)
        actual = make_activity(
            activity_id="act-1", recorded_code="ASSESS-1",
            encounter_refs=[enc.encounter_id])
        outcome = run_evaluation(
            visits=[visit], activities=[act], bundles=[bundle],
            actual_activities=[actual])
        # Projection omits the owning visit -> the activity's visit id is
        # unresolvable and the projection must fail closed.
        with pytest.raises(vs.ScheduleSliceError):
            project_visit_schedule_journey(
                outcome, planned_visits=[], planned_activities=[act],
                encounters=[enc], bundles=[bundle], activities=[actual])

    def test_activity_marker_input_order_independent(self):
        """Challenge 36-style: input order of planned activities / visits
        must not change the resolved logical visit key or marker set."""
        v_a = make_planned_visit(
            visit_id="pv-a-v2", visit_key="PV-A",
            official_code="V4", audience_name="访视 A")
        v_b = make_planned_visit(
            visit_id="pv-b-v2", visit_key="PV-B",
            official_code="V5", audience_name="访视 B")
        act_a = make_planned_activity(
            activity_id="pa-a", activity_key="PA-A",
            visit_id="pv-a-v2", clinical_domain="efficacy",
            audience_name="评估 A")
        act_b = make_planned_activity(
            activity_id="pa-b", activity_key="PA-B",
            visit_id="pv-b-v2", clinical_domain="lab",
            audience_name="检验 B")
        enc = make_encounter()
        bundle = make_bundle(enc)
        actual_a = make_activity(
            activity_id="act-a", recorded_code="ASSESS-1",
            encounter_refs=[enc.encounter_id])
        actual_b = make_activity(
            activity_id="act-b", recorded_code="LAB-1",
            encounter_refs=[enc.encounter_id])

        def project(acts, actuals):
            outcome = run_evaluation(
                visits=[v_a, v_b], activities=acts, bundles=[bundle],
                actual_activities=actuals)
            return project_visit_schedule_journey(
                outcome, planned_visits=[v_a, v_b],
                planned_activities=acts, encounters=[enc],
                bundles=[bundle], activities=actuals)

        p1 = project([act_a, act_b], [actual_a, actual_b])
        p2 = project([act_b, act_a], [actual_b, actual_a])
        keys1 = tuple((m.planned_activity_key, m.planned_visit_key)
                      for m in p1.activity_markers)
        keys2 = tuple((m.planned_activity_key, m.planned_visit_key)
                      for m in p2.activity_markers)
        assert keys1 == keys2
        assert set(keys1) == {("PA-A", "PV-A"), ("PA-B", "PV-B")}

    def test_risk_markers_bind_ids_and_locators(self):
        proj = _project_case(2)
        for m in proj.risk_markers:
            assert m.unit_id
            assert m.audience_label
            assert m.supporting_locator_ids or m.counterevidence_locator_ids
            assert m.candidate_or_risk_id or m.coverage_gap

    def test_out_of_cutoff_separate_area(self):
        """Challenge 103: cutoff-later records go to the out-of-cutoff
        area, not the assignment/L1 axis."""
        from datetime import date
        late = (date(2026, 8, 20)).isoformat()
        enc_late = make_encounter(encounter_id="enc-late",
                                  start=late, recorded_visit_code="V4")
        visit = make_planned_visit()
        from mm_r4.visit_schedule_fixtures import make_cutoff
        cutoff = make_cutoff("2026-08-10")
        outcome = run_evaluation(
            visits=[visit], encounters=[enc_late], cutoff=cutoff,
            bundles=[make_bundle(enc_late)])
        proj = project_visit_schedule_journey(
            outcome, planned_visits=[visit], encounters=[enc_late],
            bundles=[make_bundle(enc_late)])
        assert proj.out_of_cutoff_markers
        for m in proj.out_of_cutoff_markers:
            assert m.object_type in ("encounter", "activity")