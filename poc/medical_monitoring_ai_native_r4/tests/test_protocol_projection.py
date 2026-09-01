"""R4-D04 protocol-compliance journey projection tests (worker_03).

Proves the frozen D04 journey projection (``mm_r4.protocol_projection``)
implements the frozen §7.4/§9 contract:

* typed :class:`ProtocolJourneyEvent` payloads on the ``protocol`` track
  with actual/nominal visit-axis anchors, concrete Chinese labels and the
  unresolved area for events without any precise date (no fabricated time
  point, challenge 46);
* typed D04 risk markers: one per positive/boundary unit carrying its
  candidate id, one coverage-gap marker (no candidate) per not_evaluable
  unit, and zero markers for negative/not_applicable or producer-owned
  control points (challenges 29/45/47/56/57);
* the deterministic bidirectional :class:`ProtocolEventMarkerJoin` index
  verified by stable ids with the closed join reasons ``unit_identity |
  anchor_event | source_locator | producer_reference``; tamper (unknown
  event/marker id, mixed subject) fails **before** projection
  (challenges 47/63);
* the subject-level rollup carries the coverage-gap display payload,
  the typed producer references (never D04-created), the unresolved
  event ids and a byte-deterministic canonical payload (challenges
  46-48);
* public root exports are object-identical with the submodule symbols.

All data is synthetic and offline.  No real project, provider,
dictionary, or product service; port 8911 is never touched.
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

import mm_r4.protocol as p  # noqa: E402
import mm_r4.protocol_projection as pp  # noqa: E402
from mm_r4.contracts import (  # noqa: E402
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    QueryDraftRef,
)
from mm_r4.protocol_fixtures import (  # noqa: E402
    build_protocol_challenge_matrix,
    make_binding,
    make_enrollment,
    make_numeric_rule,
    make_control_point,
    make_producer_ref,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _run_case(number: int):
    """Build a matrix case and return (case, expansion, results, slice)."""
    case = build_protocol_challenge_matrix().by_number(number)
    exp, results = case.build()
    sr, _ = case.build_slice()
    return case, exp, results, sr


def _project(number: int, **kw):
    case, exp, results, sr = _run_case(number)
    proj = pp.project_protocol_subject_journey(
        sr, expansions=exp,
        producer_references=sr.producer_references, **kw)
    return case, exp, results, sr, proj


# ===========================================================================
# Journey events
# ===========================================================================

class TestJourneyEvents:
    """Frozen §9: typed protocol-track events with real anchors."""

    def test_positive_unit_projects_one_typed_event(self):
        _, exp, results, sr, proj = _project(
            1, nominal_visits={"CP01-INC": "筛选访视 V1"},
            actual_visits={"CP01-INC": "V1"})
        assert proj.event_count == 1
        ev = proj.events[0]
        assert ev.domain_track == pp.PROTOCOL_TRACK == "protocol"
        assert ev.subject_ref == "SYN-001"
        assert ev.site_ref == "SITE01"
        assert ev.control_point_id == "CP01-INC"
        assert ev.evaluation_node_id == p.NODE_ATOMIC
        assert ev.unit_ids == (results[0].unit_id,)
        # Anchor on the actual screening date.
        assert ev.anchor_kind == p.ANCHOR_SCREENING
        assert ev.start == "2026-03-01"
        assert not ev.end
        assert ev.date_precision == "day"
        # Nominal and actual visit tokens stay distinct.
        assert ev.nominal_visit == "筛选访视 V1"
        assert ev.actual_visit == "V1"
        assert ev.display_label == "筛选期·入选条件待核实"
        assert ev.source_locator_ids

    def test_event_labels_are_concrete_chinese(self):
        """Events keep concrete Chinese labels; engineering codes never
        appear in the display label."""
        _, _, _, _, proj = _project(1)
        ev = proj.events[0]
        assert "待核实" in ev.display_label
        for token in ("positive", "candidate", "formal", "候选信号",
                      "正式事实", "只读投影"):
            assert token not in ev.display_label

    def test_missing_date_goes_to_unresolved_area(self):
        """Challenge 46: an event without any precise date is placed in
        the unresolved area and never gets a fabricated time point."""
        case, exp, results, sr = _run_case(1)
        # Force an empty window: rebuild the unit with no anchor date.
        appl = p.ProtocolApplicabilityDecision(
            subject_ref="SYN-001", site_ref="SITE01",
            decision_time_anchor=p.ANCHOR_OTHER,
            decision_time_anchor_date="",
            decision_status=p.APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id="PROTO-1", protocol_version="V2.0",
            amendment_id_or_hash="am2",
            feasible_version_fingerprints=("fp-1",),
            stable_source_content_key="stable-key-1",
            source_locators=(make_binding("x").source_locator,))
        cp = make_control_point(
            control_point_id="CP-UNR-1",
            structured_rule=make_numeric_rule())
        from mm_r4.protocol_fixtures import evaluate_slice as _es
        sr2 = _es(
            applicability=appl, control_points=(cp,),
            plan=make_plan_root(cp.control_point_id),
            bindings=(make_binding(
                "bu", control_point_id="CP-UNR-1", value="8"),),
            coverage={"laboratory": True},
            enrollment=make_enrollment(p.QUERY_CONTEXT_NOT_OCCURRED))
        exp2 = p.expand_protocol_expected_set(
            project_id="proj-synthetic-001", applicability=appl,
            control_points=(cp,),
            plan=make_plan_root(cp.control_point_id))
        proj = pp.project_protocol_subject_journey(sr2, expansions=exp2)
        ev = proj.events[0]
        assert ev.anchor_kind == p.ANCHOR_OTHER
        assert not ev.start and not ev.end
        assert ev.event_id in proj.unresolved_event_ids
        assert "待定区" in ev.display_label

    def test_tracks_stay_distinct(self):
        """AE/MH/CM/IP/protocol keep distinct tracks and payload classes."""
        _, _, _, _, proj = _project(1)
        assert all(e.domain_track == "protocol" for e in proj.events)
        # The D04 event value object is not the D01/D03 event class.
        from mm_r4.projection import JourneyEvent as AEMHJourneyEvent
        from mm_r4.ip_projection import IPJourneyEvent
        assert pp.ProtocolJourneyEvent is not AEMHJourneyEvent
        assert pp.ProtocolJourneyEvent is not IPJourneyEvent

    def test_no_events_for_gate_units(self):
        """Applicability/routing gates are subject-level blockers; they
        project no journey event (their gap surfaces in the coverage-gap
        display payload instead)."""
        _, exp, results, sr = _run_case(13)  # applicability gate boundary
        proj = pp.project_protocol_subject_journey(sr, expansions=exp)
        assert proj.event_count == 0
        # The gate marker (if any) never carries a candidate: no D04 risk
        # identity exists for gates.
        assert proj.risk_marker_count == 0


# ===========================================================================
# Risk markers
# ===========================================================================

class TestRiskMarkers:
    """Frozen §9: typed D04 risk markers with candidate identity."""

    def test_positive_marker_carries_candidate_and_query(self):
        _, exp, results, sr, proj = _project(
            1, nominal_visits={"CP01-INC": "筛选访视 V1"})
        markers = [m for m in proj.risk_markers if m.candidate_or_risk_id]
        assert len(markers) == 1
        m = markers[0]
        assert m.marker_id == f"pm-{results[0].unit_id}"
        assert m.unit_id == results[0].unit_id
        assert m.risk_family == p.SIGNAL_INCLUSION
        assert m.audience_label == "入选条件待核实"
        assert m.monitoring_priority in (
            "high", "medium", "low", "unknown")
        assert m.query_ids
        assert not m.coverage_gap

    def test_boundary_marker_is_clue_not_query(self):
        _, _, _, _, proj = _project(18)  # unstated equality boundary
        markers = [m for m in proj.risk_markers if m.candidate_or_risk_id]
        assert markers
        assert all(m.audience_label.endswith("（边界）")
                   for m in markers)
        assert all(not m.query_ids for m in markers)

    def test_not_evaluable_projects_coverage_gap_marker_no_candidate(self):
        """Challenge 45: a not_evaluable unit surfaces as a coverage-gap
        marker with no candidate so the view shows the gap without
        inventing a risk."""
        _, _, _, _, proj = _project(45)
        gap_markers = [m for m in proj.risk_markers if m.coverage_gap]
        assert gap_markers
        for m in gap_markers:
            assert not m.candidate_or_risk_id
            assert not m.query_ids
            assert m.audience_label == "资料不足，暂无法核实"
        assert proj.coverage_gap_marker_count == len(gap_markers)

    def test_negative_unit_projects_no_marker(self):
        _, _, _, _, proj = _project(2)
        assert proj.risk_marker_count == 0
        assert proj.coverage_gap_marker_count == 0

    def test_producer_owned_never_create_d04_markers(self):
        """Challenges 29/56/57: D02/D03/D05 control points surface only as
        typed producer references; D04 creates no marker/risk for them."""
        _, _, _, _, proj = _project(29)
        assert proj.risk_marker_count == 0
        assert proj.producer_reference_count == 1
        ref = proj.producer_references[0]
        assert ref.owner_domain == p.OWNER_D02
        assert ref.producer_unit_id == "d02-unit-29"
        assert ref.producer_marker_or_query_id == "marker-d02-29"
        assert ref.producer_risk_identity_id == "rid-d02-29"
        assert ref.audience_label == "禁限用要求待核实"

    def test_marker_labels_never_leak_engineering_codes(self):
        for number in (1, 18, 45):
            _, _, _, _, proj = _project(number)
            for m in proj.risk_markers:
                for token in ("positive", "candidate", "formal",
                              "候选信号", "正式事实", "只读", "未知风险"):
                    assert token not in m.audience_label

    def test_positive_marker_query_reachable(self):
        """The marker's Query ids resolve to real QueryDraftRef objects on
        the unit."""
        case, exp, results, sr, proj = _project(1)
        unit = results[0]
        marker = [m for m in proj.risk_markers
                  if m.candidate_or_risk_id][0]
        assert set(marker.query_ids) == {q.query_id for q in unit.query_refs}
        assert all(isinstance(q, QueryDraftRef) for q in unit.query_refs)


# ===========================================================================
# Bidirectional join
# ===========================================================================

class TestBidirectionalJoin:
    """Frozen §7.4: verified bidirectional event-marker join."""

    def test_join_is_bidirectional_by_stable_ids(self):
        _, _, _, _, proj = _project(1)
        assert proj.join.records
        for rec in proj.join.records:
            assert rec.join_reason in p.JOIN_REASONS
            assert rec.event_id in {e.event_id for e in proj.events}
            assert rec.marker_id in {m.marker_id for m in proj.risk_markers}
            assert rec.unit_id == results_unit_for(proj, rec)
        # Index roundtrip.
        ev = proj.events[0]
        markers = proj.join.markers_for_event(ev.event_id)
        assert markers
        for mid in markers:
            assert ev.event_id in proj.join.events_for_marker(mid)

    def test_unit_identity_and_source_locator_reasons(self):
        _, _, _, _, proj = _project(1)
        reasons = {r.join_reason for r in proj.join.records}
        assert p.JOIN_UNIT_IDENTITY in reasons
        assert p.JOIN_SOURCE_LOCATOR in reasons

    def test_anchor_event_reason_on_shared_anchor(self):
        """Events and markers sharing the exact non-empty anchor triple
        join via ``anchor_event``."""
        from mm_r4.protocol import (ProtocolJourneyEvent, ProtocolRiskMarker,
                                    ANCHOR_SCREENING)
        ev = ProtocolJourneyEvent(
            event_id="ev-a", domain_track="protocol", subject_ref="S1",
            site_ref="SITE01", anchor_kind=ANCHOR_SCREENING,
            start="2026-03-01", end="",
            source_locator_ids=("L1",), unit_ids=("u1",))
        mk = ProtocolRiskMarker(
            marker_id="mk-a", risk_family=p.SIGNAL_INCLUSION,
            audience_label="入选条件待核实",
            monitoring_priority=MONITORING_PRIORITY_HIGH,
            anchor_kind=ANCHOR_SCREENING, anchor_start="2026-03-01",
            anchor_end="", unit_id="u1", candidate_or_risk_id="c1",
            protocol_locator_ids=("P1",),
            supporting_locator_ids=("L2",))
        join = pp.bidirectional_join((ev,), (mk,))
        reasons = {r.join_reason for r in join.records}
        assert p.JOIN_ANCHOR_EVENT in reasons
        assert p.JOIN_UNIT_IDENTITY in reasons

    def test_tamper_fails_before_projection(self):
        """The join builder only emits edges whose ids are reachable in
        the supplied collections; pathological inputs never produce an
        edge with an unknown event/marker id."""
        from mm_r4.protocol import (ProtocolJourneyEvent, ProtocolRiskMarker,
                                    ANCHOR_SCREENING)
        ev = ProtocolJourneyEvent(
            event_id="ev-1", domain_track="protocol", subject_ref="S1",
            site_ref="SITE01", anchor_kind=ANCHOR_SCREENING,
            start="2026-03-01", source_locator_ids=("L1",),
            unit_ids=("u1",))
        mk = ProtocolRiskMarker(
            marker_id="mk-1", risk_family=p.SIGNAL_INCLUSION,
            audience_label="入选条件待核实",
            monitoring_priority=MONITORING_PRIORITY_HIGH,
            anchor_kind=ANCHOR_SCREENING, unit_id="u1",
            candidate_or_risk_id="c1",
            protocol_locator_ids=("P1",),
            supporting_locator_ids=("L1",))
        join = pp.bidirectional_join((ev,), (mk,))
        assert all(r.event_id == "ev-1" for r in join.records)
        assert all(r.marker_id == "mk-1" for r in join.records)
        # Every edge stays inside the reachable id universe.
        event_ids = {e.event_id for e in (ev,)}
        marker_ids = {m.marker_id for m in (mk,)}
        for rec in join.records:
            assert rec.event_id in event_ids
            assert rec.marker_id in marker_ids

    def test_mixed_subject_fails_before_projection(self):
        from mm_r4.protocol import (ProtocolJourneyEvent, ANCHOR_SCREENING)
        ev1 = ProtocolJourneyEvent(
            event_id="ev-1", domain_track="protocol", subject_ref="S1",
            site_ref="SITE01", anchor_kind=ANCHOR_SCREENING,
            start="2026-03-01", source_locator_ids=("L1",),
            unit_ids=("u1",))
        ev2 = ProtocolJourneyEvent(
            event_id="ev-2", domain_track="protocol", subject_ref="S2",
            site_ref="SITE01", anchor_kind=ANCHOR_SCREENING,
            start="2026-03-01", source_locator_ids=("L2",),
            unit_ids=("u2",))
        with pytest.raises(p.ProtocolSliceError):
            pp.bidirectional_join((ev1, ev2), ())

    def test_producer_reference_edge_is_typed(self):
        """A producer edge joins a D04 event to the producer's own ids via
        ``producer_reference``; no D04 marker/unit/risk is created."""
        case, exp, results, sr = _run_case(1)
        # Attach a producer reference for the D02 unit consumed by the
        # same control point; D04 creates nothing for it.
        producer = make_producer_ref(
            "ref-x", p.OWNER_D02, "d02-unit-x",
            marker_or_query="marker-d02-x",
            risk_identity="rid-d02-x",
            audience_label="禁限用要求待核实",
            priority=MONITORING_PRIORITY_MEDIUM,
            control_point_id="CP01-INC")
        proj = pp.project_protocol_subject_journey(
            sr, expansions=exp, producer_references=(producer,))
        edges = [r for r in proj.join.records
                 if r.join_reason == p.JOIN_PRODUCER_REFERENCE]
        assert len(edges) == 1
        edge = edges[0]
        assert edge.event_id == proj.events[0].event_id
        assert edge.marker_id == "marker-d02-x"
        assert edge.unit_id == "d02-unit-x"
        assert edge.risk_identity_id == "rid-d02-x"
        assert ("producer_ref:ref-x") in edge.typed_ref_ids
        # No D04 marker/risk was created for the producer.
        assert proj.risk_marker_count == 1  # only the D04-native marker
        assert "marker-d02-x" not in {m.marker_id
                                      for m in proj.risk_markers}

    def test_join_is_deterministic(self):
        _, _, _, _, proj1 = _project(1)
        _, _, _, _, proj2 = _project(1)
        assert proj1.join.canonical_payload() == \
            proj2.join.canonical_payload()


# ===========================================================================
# Subject projection rollup
# ===========================================================================

class TestSubjectProjection:
    """Frozen §9/§11: rollup carries counts, gaps and deterministic
    payload."""

    def test_priority_aggregation(self):
        """Medium > unknown; the subject priority never defaults low."""
        case, exp, results, sr = _run_case(1)
        proj = pp.project_protocol_subject_journey(sr, expansions=exp)
        assert proj.monitoring_priority_code in (
            "high", "medium", "low", "unknown")

    def test_coverage_gap_display_payload(self):
        """Coverage-gap notices are aggregated as a display payload and
        counted separately from Query count."""
        _, _, _, sr, proj = _project(45)
        assert sr.coverage_gap_count == len(proj.coverage_gap_notices) >= 1
        for notice in proj.coverage_gap_notices:
            assert notice.notice_id
            assert notice.audience_text
        assert sr.query_draft_count == 0

    def test_canonical_payload_byte_deterministic(self):
        """Challenges 47/48: the canonical payload is byte-deterministic
        across reruns."""
        _, _, _, _, proj1 = _project(1)
        _, _, _, _, proj2 = _project(1)
        assert proj1.canonical_payload() == proj2.canonical_payload()
        # Frozen golden payload hash matches recomputation.
        from mm_r4.protocol_fixtures import (
            GOLDEN_PROJECTION_PAYLOAD_HASH, content_hash)
        assert GOLDEN_PROJECTION_PAYLOAD_HASH[1] == \
            content_hash(proj1.canonical_payload())

    def test_uncertainty_summary_aggregates_reasons(self):
        _, _, _, sr, proj = _project(45)
        assert proj.uncertainty_summary


# ===========================================================================
# Public exports
# ===========================================================================

class TestPublicExports:
    """Root package re-exports are object-identical with the submodules."""

    def test_root_projection_symbols_identical(self):
        import mm_r4
        assert (mm_r4.ProtocolJourneyEvent is
                pp.ProtocolJourneyEvent)
        assert (mm_r4.ProtocolRiskMarker is
                pp.ProtocolRiskMarker)
        assert (mm_r4.ProtocolEventMarkerJoin is
                p.ProtocolEventMarkerJoin)
        assert (mm_r4.ProtocolProducerReference is
                p.ProtocolProducerReference)
        assert (mm_r4.ProtocolEventMarkerJoinIndex is
                pp.ProtocolEventMarkerJoinIndex)
        assert mm_r4.project_protocol_subject_journey is \
            pp.project_protocol_subject_journey
        assert mm_r4.project_protocol_journey_events is \
            pp.project_protocol_journey_events
        assert mm_r4.project_protocol_risk_markers is \
            pp.project_protocol_risk_markers
        assert mm_r4.protocol_bidirectional_join is \
            pp.bidirectional_join

    def test_root_domain_symbols_identical(self):
        import mm_r4
        assert mm_r4.ProtocolSliceResult is p.ProtocolSliceResult
        assert mm_r4.ProtocolUnitResult is p.ProtocolUnitResult
        assert mm_r4.evaluate_protocol_slice is p.evaluate_protocol_slice
        assert mm_r4.D04_DOMAIN == p.D04_DOMAIN


# ===========================================================================
# Helpers used above (module-level so they can be referenced)
# ===========================================================================

def results_unit_for(proj, rec) -> str:
    for m in proj.risk_markers:
        if m.marker_id == rec.marker_id:
            return m.unit_id
    return ""


def make_plan_root(*root_ids: str):
    from mm_r4.protocol_fixtures import make_plan
    return make_plan(root_ids=root_ids)

