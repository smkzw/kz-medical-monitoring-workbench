"""R4-D04 protocol-compliance journey projection (frozen D04 §7.4, §9).

This module produces **renderer-neutral projection payload data** from
:class:`~mm_r4.protocol.ProtocolUnitResult` /
:class:`~mm_r4.protocol.ProtocolSliceResult` values produced by the D04
protocol domain engine (``protocol.py``).  It is data, not an R5 UI and
not a chart library (frozen D04 §9: "D04 只提供 renderer-neutral payload，
不宣称 R5 UI 已完成").

Three projection payloads (frozen D04 §9):

* :class:`ProtocolJourneyEvent` -- one protocol-compliance event anchored
  on the subject medical journey.  ``domain_track="protocol"`` keeps the
  protocol track distinct from the AE/MH/CM/IP/检查 tracks.  Events use
  the actual decision/anchor dates when available (screening, consent,
  randomization, first dose, treatment window, discontinuation), keep
  nominal/actual visit tokens separate, and events without any precise
  date go to the unresolved area (``anchor_kind=other`` with empty
  start/end) -- a time point is never fabricated.
* :class:`ProtocolRiskMarker` -- one typed D04 risk marker per
  positive/boundary unit carrying its candidate id, and one
  coverage-gap marker (no candidate) per not_evaluable unit so the view
  surfaces the gap without inventing a risk.  The marker's
  ``risk_family`` is the closed D04 signal type and its ``audience_label``
  is a concrete Chinese phrase; engineering codes never leak into the
  audience label.  Negative and not_applicable units project no marker.
* :class:`ProtocolEventMarkerJoin` -- the deterministic bidirectional
  event-marker join verified by stable ids and typed refs (frozen §7.4).
  ``join_reason`` is the closed enum ``unit_identity|anchor_event|
  source_locator|producer_reference``.  Producer-owned D02/D03/D05
  control points never create D04 units/risks/Queries: they surface only
  as typed :class:`ProtocolProducerReference` entries, and the join index
  records ``producer_reference`` edges carrying the producer's own ids.

Subject-level rollup: :class:`ProtocolSubjectJourneyProjection` carries
the typed events, the D04-native risk markers, the typed producer
references, the coverage-gap notice display payload and the deterministic
bidirectional join index.  The canonical payload is byte-deterministic.

All data is synthetic/offline.  No production UI, real project, provider,
dictionary, or product service is involved; port 8911 is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..risks.contracts import (
    L1Disposition,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidate,
    RiskCandidateRef,
)
from .aemh import monitoring_priority_audience_label
from ..risks.protocol import (
    ANCHOR_CONSENT,
    ANCHOR_DISCONTINUATION,
    ANCHOR_FIRST_DOSE,
    ANCHOR_KINDS,
    ANCHOR_ON_TREATMENT,
    ANCHOR_OTHER,
    ANCHOR_RANDOMIZATION,
    ANCHOR_SCREENING,
    D04_DOMAIN,
    JOIN_ANCHOR_EVENT,
    JOIN_PRODUCER_REFERENCE,
    JOIN_SOURCE_LOCATOR,
    JOIN_UNIT_IDENTITY,
    NODE_APPLICABILITY_GATE,
    NODE_ROUTING_GATE,
    ProtocolCoverageGapNotice,
    ProtocolEventMarkerJoin,
    ProtocolExpectedSetExpansion,
    ProtocolJourneyEvent,
    ProtocolProducerReference,
    ProtocolRiskMarker,
    ProtocolSliceError,
    ProtocolSliceResult,
    ProtocolUnitExpanded,
    ProtocolUnitResult,
)

__all__ = [
    "PROTOCOL_TRACK",
    "PROTOCOL_UNRESOLVED_LABEL",
    "EVENT_ANCHOR_LABELS",
    "DISPOSITION_EVENT_LABELS",
    "GAP_MARKER_AUDIENCE_LABEL",
    "ProtocolSubjectJourneyProjection",
    "ProtocolEventMarkerJoinIndex",
    "project_protocol_journey_events",
    "project_protocol_risk_markers",
    "bidirectional_join",
    "project_protocol_subject_journey",
]


# ---------------------------------------------------------------------------
# Constants and label maps (frozen D04 §8.2, §9)
# ---------------------------------------------------------------------------

#: The protocol-compliance journey track; AE/MH/CM/IP/检查 keep their own
#: tracks and are never merged into this one (§9).
PROTOCOL_TRACK = "protocol"

#: Chinese label for the unresolved area (§9: 不存在精确日期时进入独立待定
#: 区域，不伪造时间点).
PROTOCOL_UNRESOLVED_LABEL = "待定区·资料不足"

#: Evaluation anchor kind -> concrete Chinese anchor label (user-visible
#: journey labels; engineering codes never leak).
EVENT_ANCHOR_LABELS: Dict[str, str] = {
    ANCHOR_SCREENING: "筛选期",
    ANCHOR_CONSENT: "知情同意",
    ANCHOR_RANDOMIZATION: "随机化",
    ANCHOR_FIRST_DOSE: "首次给药",
    ANCHOR_ON_TREATMENT: "治疗期",
    ANCHOR_DISCONTINUATION: "退出/终止参与",
    ANCHOR_OTHER: "待定区",
}

#: L1 disposition -> concrete Chinese event label (§9: 方案符合性轨道保留
#: 具体中文标签; negative/not_applicable keep a non-risk wording).
DISPOSITION_EVENT_LABELS: Dict[str, str] = {
    L1Disposition.POSITIVE: "",
    L1Disposition.BOUNDARY: "",
    L1Disposition.NEGATIVE: "方案要求已核实一致",
    L1Disposition.NOT_EVALUABLE: "资料不足，暂无法核实",
    L1Disposition.NOT_APPLICABLE: "该标准不适用",
}

#: Coverage-gap marker audience label (not_evaluable units).
GAP_MARKER_AUDIENCE_LABEL = "资料不足，暂无法核实"

#: Point anchors that carry an actual event date from the applicability
#: decision anchor date (screening/consent/randomization/first dose/
#: discontinuation are distinct, never interchangeable, §7.2).
_POINT_ANCHORS: Tuple[str, ...] = (
    ANCHOR_SCREENING, ANCHOR_CONSENT, ANCHOR_RANDOMIZATION,
    ANCHOR_FIRST_DOSE, ANCHOR_DISCONTINUATION,
)

#: Priority ordering for the overall subject priority (high > medium >
#: low > unknown; unknown never defaults to low, §8.1).
_PRIORITY_RANK: Dict[str, int] = {
    MONITORING_PRIORITY_HIGH: 0,
    MONITORING_PRIORITY_MEDIUM: 1,
    MONITORING_PRIORITY_LOW: 2,
    MONITORING_PRIORITY_UNKNOWN: 3,
}


def _anchor_label(anchor_kind: str) -> str:
    return EVENT_ANCHOR_LABELS.get(anchor_kind, anchor_kind)


def _precision_of_date(s: str) -> str:
    """Derive a stable date-precision token for the visit/time axis."""
    if not s:
        return "none"
    value = s.strip()
    parts = value.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if parts and len(parts[0]) == 4:
        return "year"
    return "none"


def _candidate_id_of(unit: ProtocolUnitResult) -> str:
    """Primary candidate id from a unit's candidate refs, or ''."""
    for ref in unit.risk_candidate_refs:
        if isinstance(ref, RiskCandidateRef) and ref.candidate_id:
            return ref.candidate_id
    return ""


def _candidate_detail(
    unit: ProtocolUnitResult,
    candidates: Sequence[RiskCandidate],
) -> Optional[RiskCandidate]:
    """The R2 candidate matching the unit's primary candidate, or None."""
    cid = _candidate_id_of(unit)
    if not cid:
        return None
    for cand in candidates:
        if cand.candidate_id == cid:
            return cand
    return None


def _expanded_by_unit(
    expansions: Optional[ProtocolExpectedSetExpansion],
) -> Dict[str, ProtocolUnitExpanded]:
    """Map unit_id -> expanded seed (for site/phase/applicability context)."""
    if expansions is None:
        return {}
    out: Dict[str, ProtocolUnitExpanded] = {}
    for eu in expansions.units:
        out[eu.build_unit(expansions.project_id).unit_id] = eu
    return out


def _source_locator_ids(unit: ProtocolUnitResult) -> Tuple[str, ...]:
    """Deterministically deduplicated reachable source locator ids."""
    ids: List[str] = []
    for sref in unit.source_record_refs:
        ids.append(sref.locator.locator_id())
    for ev in unit.evidence:
        ids.append(ev.locator.locator_id())
    for ref in unit.risk_candidate_refs:
        if ref.locator is not None:
            ids.append(ref.locator.locator_id())
    ids.extend(unit.protocol_locator_ids)
    return tuple(sorted(set(x for x in ids if x)))


def _query_ids(unit: ProtocolUnitResult) -> Tuple[str, ...]:
    return tuple(
        sorted({q.query_id for q in unit.query_refs
                if isinstance(q, QueryDraftRef) and q.query_id}))


def _event_display_label(unit: ProtocolUnitResult) -> str:
    """Concrete Chinese event label: anchor + disposition wording."""
    anchor = _anchor_label(unit.eval_anchor_kind or ANCHOR_OTHER)
    if unit.l1_disposition in (L1Disposition.POSITIVE,
                               L1Disposition.BOUNDARY):
        base = unit.audience_label or "方案符合性待核实"
        if unit.l1_disposition == L1Disposition.BOUNDARY:
            base = f"{base}（边界）"
        return f"{anchor}·{base}"
    label = DISPOSITION_EVENT_LABELS.get(
        unit.l1_disposition, "方案符合性待核实")
    return f"{anchor}·{label}"


# ---------------------------------------------------------------------------
# Per-unit event projection (frozen D04 §9)
# ---------------------------------------------------------------------------

def project_protocol_journey_events(
    unit_result: ProtocolUnitResult,
    *,
    expansions: Optional[ProtocolExpectedSetExpansion] = None,
    site_ref: str = "",
    nominal_visits: Optional[Mapping[str, str]] = None,
    actual_visits: Optional[Mapping[str, str]] = None,
) -> Tuple[ProtocolJourneyEvent, ...]:
    """Project one typed protocol-compliance journey event per evaluated
    unit (atomic/package roots only; applicability/routing gates are
    subject-level blockers surfaced through the coverage-gap display, not
    journey events).

    Anchoring rules (§9, §7.2):

    * the evaluation window dates are the primary anchors (the window of
      an inclusion rule is anchored to the actual screening period, the
      sequence window to the actual consent/randomization events, the
      discontinuation window to the trigger/disposition interval);
    * when the window carries no dates but the applicability decision
      anchor kind equals the unit's evaluation anchor kind, the actual
      decision anchor date is used (screening date, consent date, ...);
    * ``nominal_visit`` / ``actual_visit`` stay separate tokens (a nominal
      visit is only used when the rule is explicitly nominal-visit
      anchored; actual events keep their real dates, §7.2);
    * no precise date at all -> an unresolved event (``anchor_kind=other``,
      empty start/end) that is never assigned a fabricated time point.
    """
    if unit_result.evaluation_node_id in (NODE_APPLICABILITY_GATE,
                                          NODE_ROUTING_GATE):
        return ()

    anchor_kind = unit_result.eval_anchor_kind or ANCHOR_OTHER
    if anchor_kind not in ANCHOR_KINDS:
        raise ProtocolSliceError(
            f"unit {unit_result.unit_id!r} eval_anchor_kind "
            f"{anchor_kind!r} invalid for journey projection")

    expanded = None
    if expansions is not None:
        expanded = _expanded_by_unit(expansions).get(unit_result.unit_id)
    applicability = expanded.applicability if expanded is not None else None

    start = unit_result.window_start or ""
    end = unit_result.window_end or ""
    if not start and applicability is not None:
        if (applicability.decision_time_anchor == anchor_kind
                and applicability.decision_time_anchor_date.strip()):
            start = applicability.decision_time_anchor_date
            end = ""
    if start and not end and anchor_kind == ANCHOR_ON_TREATMENT:
        end = start
    if not start:
        anchor_kind = ANCHOR_OTHER

    nominal = ""
    actual = ""
    cp_id = unit_result.control_point_id
    if nominal_visits is not None and cp_id in nominal_visits:
        nominal = nominal_visits[cp_id]
    if actual_visits is not None and cp_id in actual_visits:
        actual = actual_visits[cp_id]

    phase = ""
    if expanded is not None:
        phase = expanded.applicability.phase

    if not site_ref:
        if expanded is not None:
            site_ref = expanded.site_ref
        elif unit_result.risk_candidate_refs:
            ref0 = unit_result.risk_candidate_refs[0]
            if ref0.locator is not None:
                site_ref = ref0.locator.site_ref if hasattr(
                    ref0.locator, "site_ref") else ""

    return (ProtocolJourneyEvent(
        event_id=f"pev-{unit_result.unit_id}",
        domain_track=PROTOCOL_TRACK,
        subject_ref=unit_result.subject_ref,
        site_ref=site_ref,
        anchor_kind=anchor_kind,
        start=start,
        end=end,
        date_precision=(
            unit_result.precision
            if unit_result.precision in ("day", "month", "year", "unknown")
            else _precision_of_date(start)),
        nominal_visit=nominal,
        actual_visit=actual,
        phase=phase,
        protocol_version=unit_result.protocol_version,
        control_point_id=unit_result.control_point_id,
        evaluation_node_id=unit_result.evaluation_node_id,
        decisive_component_ids=unit_result.decisive_component_ids,
        display_label=_event_display_label(unit_result),
        source_locator_ids=_source_locator_ids(unit_result),
        unit_ids=(unit_result.unit_id,),
    ),)


# ---------------------------------------------------------------------------
# Per-unit marker projection (frozen D04 §9)
# ---------------------------------------------------------------------------

def project_protocol_risk_markers(
    unit_result: ProtocolUnitResult,
    *,
    candidates: Sequence[RiskCandidate] = (),
    expansions: Optional[ProtocolExpectedSetExpansion] = None,
) -> Tuple[ProtocolRiskMarker, ...]:
    """Project D04 risk markers for one unit result.

    * positive / boundary -> one typed risk marker carrying the candidate
      id, the concrete Chinese audience label and the closed
      ``risk_family`` (D04 signal type);
    * not_evaluable (including applicability/routing gates) -> one
      coverage-gap marker with **no** candidate id so the view surfaces
      the gap without inventing a risk;
    * negative / not_applicable -> no marker.

    Producer-owned control points never reach this function as D04 units
    (they are routed out of the expected-set); they surface only as typed
    :class:`ProtocolProducerReference` entries on the overview.
    """
    disposition = unit_result.l1_disposition
    if disposition in (L1Disposition.NEGATIVE, L1Disposition.NOT_APPLICABLE):
        return ()

    engine_marker = (
        unit_result.journey_markers[0]
        if unit_result.journey_markers else None)
    risk_family = ""
    if engine_marker is not None:
        risk_family = engine_marker.risk_family
    if not risk_family:
        risk_family = unit_result.signal_type or D04_DOMAIN

    anchor_kind = unit_result.eval_anchor_kind or ANCHOR_OTHER
    anchor_start = unit_result.window_start or ""
    anchor_end = unit_result.window_end or ""
    precision = unit_result.precision or _precision_of_date(anchor_start)

    if disposition == L1Disposition.NOT_EVALUABLE:
        return (ProtocolRiskMarker(
            marker_id=f"pm-{unit_result.unit_id}",
            risk_family=risk_family,
            audience_label=GAP_MARKER_AUDIENCE_LABEL,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            anchor_kind=ANCHOR_OTHER,
            anchor_start="",
            anchor_end="",
            date_precision="unknown",
            unit_id=unit_result.unit_id,
            candidate_or_risk_id="",
            protocol_locator_ids=unit_result.protocol_locator_ids,
            supporting_locator_ids=_source_locator_ids(unit_result),
            counterevidence_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in unit_result.evidence
                if ev.polarity == "counterevidence"})),
            query_ids=(),
            coverage_gap=True,
        ),)

    cand = _candidate_detail(unit_result, candidates)
    candidate_id = _candidate_id_of(unit_result)
    if cand is not None:
        candidate_id = candidate_id or str(
            cand.detail.get("candidate_id", "")) or str(
            cand.candidate_id)
    priority = unit_result.monitoring_priority
    audience = unit_result.audience_label or GAP_MARKER_AUDIENCE_LABEL
    if disposition == L1Disposition.BOUNDARY and not audience.endswith("（边界）"):
        audience = f"{audience}（边界）"

    return (ProtocolRiskMarker(
        marker_id=f"pm-{unit_result.unit_id}",
        risk_family=risk_family,
        audience_label=audience,
        monitoring_priority=priority,
        anchor_kind=anchor_kind,
        anchor_start=anchor_start,
        anchor_end=anchor_end,
        date_precision=precision,
        unit_id=unit_result.unit_id,
        candidate_or_risk_id=candidate_id,
        protocol_locator_ids=unit_result.protocol_locator_ids,
        supporting_locator_ids=_source_locator_ids(unit_result),
        counterevidence_locator_ids=tuple(sorted({
            ev.locator.locator_id() for ev in unit_result.evidence
            if ev.polarity == "counterevidence"})),
        query_ids=_query_ids(unit_result),
        coverage_gap=bool(unit_result.unresolved_component_ids),
    ),)


# ---------------------------------------------------------------------------
# Deterministic bidirectional join (frozen D04 §7.4)
# ---------------------------------------------------------------------------

def bidirectional_join(
    events: Sequence[ProtocolJourneyEvent],
    markers: Sequence[ProtocolRiskMarker],
    producer_references: Sequence[ProtocolProducerReference] = (),
) -> ProtocolEventMarkerJoinIndex:
    """Build the deterministic bidirectional event-marker join index.

    Join rules (all by stable ids / typed refs; descriptive text, nearest
    date or same-number is never a join key, §7.4/§9):

    * ``unit_identity`` -- the event's ``unit_ids`` contains the marker's
      ``unit_id`` (primary stable unit-identity join);
    * ``anchor_event`` -- the event and the marker share the exact same
      non-empty ``(anchor_kind, start, end)`` anchor (the anchor triple is
      the stable anchor key of the D04 payload);
    * ``source_locator`` -- they share at least one source locator id
      (verified drill-back to the same accepted row);
    * ``producer_reference`` -- a D04 event whose ``control_point_id``
      equals the producer reference's ``control_point_id`` joins to the
      producer's own ids (``producer_unit_id`` / marker / risk identity)
      with the producer's ``ref_id`` as a typed ref.  No D04 unit/risk/
      Query is created; the producer keeps its own identity.

    Tamper fails **before** projection: every record's event/marker ids
    must be reachable in the supplied collections and every event/marker
    must share the same subject (a mixed-subject or unreachable id raises
    :class:`ProtocolSliceError`).
    """
    event_by_id: Dict[str, ProtocolJourneyEvent] = {
        ev.event_id: ev for ev in events}
    marker_by_id: Dict[str, ProtocolRiskMarker] = {
        m.marker_id: m for m in markers}

    subject = ""
    site = ""
    for ev in events:
        if not subject:
            subject = ev.subject_ref
            site = ev.site_ref
        elif ev.subject_ref != subject or ev.site_ref != site:
            raise ProtocolSliceError(
                "bidirectional join refuses mixed subject/site events "
                "(tamper before projection)")

    records: List[ProtocolEventMarkerJoin] = []
    seen: Set[Tuple[str, str, str]] = set()

    def add(
        event_id: str, marker_id: str, unit_id: str,
        risk_identity_id: str, join_reason: str,
        typed_ref_ids: Tuple[str, ...],
        *,
        producer_edge: bool = False,
    ) -> None:
        if event_id not in event_by_id:
            raise ProtocolSliceError(
                f"bidirectional join references unknown event {event_id!r} "
                "(tamper before projection)")
        if not producer_edge and marker_id not in marker_by_id:
            raise ProtocolSliceError(
                f"bidirectional join references unknown marker "
                f"{marker_id!r} (tamper before projection)")
        key = (event_id, marker_id, join_reason)
        if key in seen:
            return
        seen.add(key)
        records.append(ProtocolEventMarkerJoin(
            event_id=event_id, marker_id=marker_id, unit_id=unit_id,
            risk_identity_id=risk_identity_id, join_reason=join_reason,
            typed_ref_ids=tuple(sorted(set(typed_ref_ids)))))

    # -- D04-native edges ------------------------------------------------
    for m in markers:
        for ev in events:
            reasons: List[str] = []
            if m.unit_id in ev.unit_ids:
                reasons.append(JOIN_UNIT_IDENTITY)
            if (ev.anchor_kind == m.anchor_kind
                    and ev.start and m.anchor_start
                    and ev.start == m.anchor_start
                    and (ev.end or "") == (m.anchor_end or "")):
                reasons.append(JOIN_ANCHOR_EVENT)
            if set(ev.source_locator_ids) & set(m.supporting_locator_ids):
                reasons.append(JOIN_SOURCE_LOCATOR)
            for reason in reasons:
                add(ev.event_id, m.marker_id, m.unit_id, "",
                    reason, ())

    # -- producer-reference edges (typed, producer identity preserved) ---
    # Producer markers are NOT D04 markers: the edge carries the
    # producer's own stable ids (producer_unit_id / marker / risk
    # identity) and the producer's ref_id as a typed ref.  Reachability
    # of the producer's ids is established through the typed
    # ProtocolProducerReference object itself -- the edge never creates a
    # D04 unit/risk/Query (§7.4, §9).
    for ref in producer_references:
        if not ref.control_point_id:
            continue
        for ev in events:
            if ev.control_point_id != ref.control_point_id:
                continue
            if subject and ev.subject_ref != subject:
                continue
            marker_key = ref.producer_marker_or_query_id or (
                f"{ref.owner_domain}:{ref.producer_unit_id}")
            add(
                ev.event_id, marker_key, ref.producer_unit_id,
                ref.producer_risk_identity_id, JOIN_PRODUCER_REFERENCE,
                (f"producer_ref:{ref.ref_id}",),
                producer_edge=True)

    ordered = sorted(records,
                     key=lambda r: (r.event_id, r.marker_id, r.join_reason))
    return ProtocolEventMarkerJoinIndex(records=tuple(ordered))


# ---------------------------------------------------------------------------
# Bidirectional join index (frozen D04 §7.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolEventMarkerJoinIndex:
    """Deterministic many-to-many bidirectional join index.

    ``records`` is the canonical edge list of fixed
    :class:`~mm_r4.protocol.ProtocolEventMarkerJoin` edges (each edge is
    ``event_id + marker_id + unit_id + risk_identity_id + join_reason +
    typed_ref_ids``, frozen §7.4); ``markers_by_event`` and
    ``events_by_marker`` are the deduplicated bidirectional index built
    from the verified records.
    """

    records: Tuple[ProtocolEventMarkerJoin, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
        by_event: Dict[str, Set[str]] = {}
        by_marker: Dict[str, Set[str]] = {}
        for rec in self.records:
            by_event.setdefault(rec.event_id, set()).add(rec.marker_id)
            by_marker.setdefault(rec.marker_id, set()).add(rec.event_id)
        object.__setattr__(self, "markers_by_event", {
            k: tuple(sorted(v)) for k, v in by_event.items()})
        object.__setattr__(self, "events_by_marker", {
            k: tuple(sorted(v)) for k, v in by_marker.items()})

    def markers_for_event(self, event_id: str) -> Tuple[str, ...]:
        return self.markers_by_event.get(event_id, ())

    def events_for_marker(self, marker_id: str) -> Tuple[str, ...]:
        return self.events_by_marker.get(marker_id, ())

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "records": [
                {
                    "event_id": r.event_id, "marker_id": r.marker_id,
                    "unit_id": r.unit_id,
                    "risk_identity_id": r.risk_identity_id,
                    "join_reason": r.join_reason,
                    "typed_ref_ids": list(r.typed_ref_ids),
                }
                for r in self.records],
            "markers_by_event": {
                k: list(v)
                for k, v in sorted(self.markers_by_event.items())},
            "events_by_marker": {
                k: list(v)
                for k, v in sorted(self.events_by_marker.items())},
        }


# ---------------------------------------------------------------------------
# Subject-level projection (frozen D04 §9, §11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolSubjectJourneyProjection:
    """View-only protocol-compliance journey for one subject across all
    D04 units.

    Carries the typed protocol journey events, the D04-native risk
    markers, the typed producer references (D02/D03/D05/D08, never
    D04-created), the coverage-gap notice display payload, the
    deterministic bidirectional join index and the aggregated monitoring
    priority.  It is projection data, not a rendered UI.
    """

    subject_ref: str
    events: Tuple[ProtocolJourneyEvent, ...]
    risk_markers: Tuple[ProtocolRiskMarker, ...]
    producer_references: Tuple[ProtocolProducerReference, ...]
    join: ProtocolEventMarkerJoinIndex
    coverage_gap_notices: Tuple[ProtocolCoverageGapNotice, ...] = ()
    unresolved_event_ids: Tuple[str, ...] = ()
    monitoring_priority_code: str = MONITORING_PRIORITY_UNKNOWN
    monitoring_priority_label: str = ""
    uncertainty_summary: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "risk_markers", tuple(self.risk_markers))
        object.__setattr__(self, "producer_references",
                           tuple(self.producer_references))
        object.__setattr__(self, "coverage_gap_notices",
                           tuple(self.coverage_gap_notices))
        object.__setattr__(self, "unresolved_event_ids",
                           tuple(self.unresolved_event_ids))

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def risk_marker_count(self) -> int:
        """D04-native risk markers with a candidate (positive/boundary)."""
        return sum(1 for m in self.risk_markers
                   if m.candidate_or_risk_id.strip())

    @property
    def coverage_gap_marker_count(self) -> int:
        """Coverage-gap markers (not_evaluable units, no candidate)."""
        return sum(1 for m in self.risk_markers if m.coverage_gap)

    @property
    def producer_reference_count(self) -> int:
        return len(self.producer_references)

    def has_risk_marker(self) -> bool:
        """Any D04-native risk marker with a candidate (positive/boundary)."""
        return any(m.candidate_or_risk_id.strip()
                   for m in self.risk_markers)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "subject_ref": self.subject_ref,
            "events": [_event_payload(e) for e in self.events],
            "risk_markers": [_marker_payload(m) for m in self.risk_markers],
            "producer_references": [
                {
                    "ref_id": r.ref_id, "owner_domain": r.owner_domain,
                    "producer_unit_id": r.producer_unit_id,
                    "producer_marker_or_query_id":
                        r.producer_marker_or_query_id,
                    "producer_risk_identity_id": r.producer_risk_identity_id,
                    "audience_label": r.audience_label,
                    "monitoring_priority": r.monitoring_priority,
                    "control_point_id": r.control_point_id,
                }
                for r in self.producer_references],
            "join": self.join.canonical_payload(),
            "coverage_gap_notices": [
                {
                    "notice_id": n.notice_id, "unit_id": n.unit_id,
                    "reason_code": n.reason_code,
                    "missing_evidence_roles": list(n.missing_evidence_roles),
                    "protocol_locator_ids": list(n.protocol_locator_ids),
                    "reachable_source_locator_ids":
                        list(n.reachable_source_locator_ids),
                    "audience_text": n.audience_text,
                }
                for n in self.coverage_gap_notices],
            "unresolved_event_ids": list(self.unresolved_event_ids),
            "monitoring_priority_code": self.monitoring_priority_code,
            "monitoring_priority_label": self.monitoring_priority_label,
            "uncertainty_summary": self.uncertainty_summary,
        }


def _event_payload(e: ProtocolJourneyEvent) -> Dict[str, Any]:
    return {
        "event_id": e.event_id, "domain_track": e.domain_track,
        "subject_ref": e.subject_ref, "site_ref": e.site_ref,
        "anchor_kind": e.anchor_kind, "start": e.start, "end": e.end,
        "date_precision": e.date_precision,
        "nominal_visit": e.nominal_visit, "actual_visit": e.actual_visit,
        "phase": e.phase, "protocol_version": e.protocol_version,
        "control_point_id": e.control_point_id,
        "evaluation_node_id": e.evaluation_node_id,
        "decisive_component_ids": list(e.decisive_component_ids),
        "display_label": e.display_label,
        "source_locator_ids": list(e.source_locator_ids),
        "unit_ids": list(e.unit_ids),
    }


def _marker_payload(m: ProtocolRiskMarker) -> Dict[str, Any]:
    return {
        "marker_id": m.marker_id, "risk_family": m.risk_family,
        "audience_label": m.audience_label,
        "monitoring_priority": m.monitoring_priority,
        "anchor_kind": m.anchor_kind,
        "anchor_start": m.anchor_start, "anchor_end": m.anchor_end,
        "date_precision": m.date_precision, "unit_id": m.unit_id,
        "candidate_or_risk_id": m.candidate_or_risk_id,
        "protocol_locator_ids": list(m.protocol_locator_ids),
        "supporting_locator_ids": list(m.supporting_locator_ids),
        "counterevidence_locator_ids": list(m.counterevidence_locator_ids),
        "query_ids": list(m.query_ids), "coverage_gap": m.coverage_gap,
    }


def project_protocol_subject_journey(
    slice_result: ProtocolSliceResult,
    *,
    expansions: Optional[ProtocolExpectedSetExpansion] = None,
    nominal_visits: Optional[Mapping[str, str]] = None,
    actual_visits: Optional[Mapping[str, str]] = None,
    producer_references: Optional[Sequence[ProtocolProducerReference]] = None,
) -> ProtocolSubjectJourneyProjection:
    """Project the view-only protocol-compliance journey for one subject
    across all D04 units (§9).

    Builds the typed protocol-track events, one risk marker per
    positive/boundary/not_evaluable unit, passes the producer references
    through as typed entries (their identity is preserved, never copied
    into D04), aggregates the coverage-gap display payload, computes the
    unresolved area (events without any precise date) and builds the
    deterministic bidirectional join index.  Positive, boundary and
    not_evaluable states coexist; none is collapsed.
    """
    expanded_by_unit = _expanded_by_unit(expansions)

    all_events: List[ProtocolJourneyEvent] = []
    all_markers: List[ProtocolRiskMarker] = []
    notices: List[ProtocolCoverageGapNotice] = []
    best_priority = MONITORING_PRIORITY_UNKNOWN
    uncertainty_parts: List[str] = []

    for ur in slice_result.unit_results:
        expanded = expanded_by_unit.get(ur.unit_id)
        site_ref = expanded.site_ref if expanded is not None else ""
        events = project_protocol_journey_events(
            ur, expansions=expansions, site_ref=site_ref,
            nominal_visits=nominal_visits, actual_visits=actual_visits)
        all_events.extend(events)
        markers = project_protocol_risk_markers(
            ur, candidates=slice_result.r2_candidates,
            expansions=expansions)
        all_markers.extend(markers)
        notices.extend(ur.coverage_gap_notices)
        rank = _PRIORITY_RANK.get(ur.monitoring_priority, 99)
        if rank < _PRIORITY_RANK.get(best_priority, 99):
            best_priority = ur.monitoring_priority
        for note in (ur.not_evaluable_reason, ur.boundary_reason):
            if note.strip() and note not in uncertainty_parts:
                uncertainty_parts.append(note)

    all_events.sort(key=lambda e: (not bool(e.start), e.start, e.event_id))
    all_markers.sort(key=lambda m: (m.unit_id, m.marker_id))
    notices.sort(key=lambda n: (n.unit_id, n.notice_id))
    unresolved = tuple(
        e.event_id for e in all_events
        if not e.start and not e.end)

    refs = tuple(producer_references) if producer_references is not None \
        else slice_result.producer_references
    join = bidirectional_join(all_events, all_markers, refs)

    return ProtocolSubjectJourneyProjection(
        subject_ref=slice_result.subject_ref,
        events=tuple(all_events),
        risk_markers=tuple(all_markers),
        producer_references=refs,
        join=join,
        coverage_gap_notices=tuple(notices),
        unresolved_event_ids=unresolved,
        monitoring_priority_code=best_priority,
        monitoring_priority_label=monitoring_priority_audience_label(
            best_priority),
        uncertainty_summary="；".join(uncertainty_parts),
    )
