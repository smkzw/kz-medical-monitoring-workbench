"""R4-D03 IP journey and risk-marker projection (frozen D03 §9, §10).

This module produces **projection payload data** from
:class:`~mm_r4.ip.IPUnitResult` / :class:`~mm_r4.ip.IPSliceResult` values
produced by the D03 IP domain engine (``ip.py``).  It is data, not an R5
UI and not a chart library (frozen D03 §9: "D03 只提供 R5 可消费的
projection payload，不实现最终 UI" and the module boundary: "Do not
implement R5 UI or adopt a chart library").

Two projection payloads (frozen D03 §9):

* :class:`IPJourneyEvent` -- one typed event on the subject's visit/time
  axis.  ``event_kind`` distinguishes at least administration | dispense |
  return | pause | dose_reduce | dose_increase | resume | stop | ae | lab
  | exam | efficacy | visit; ``planned_or_actual`` carries planned |
  actual | context so the timeline never conflates intent with evidence.
* :class:`IPRiskMarker` -- one risk marker typed by the six frozen
  Chinese audience labels (frozen D03 §8).  Markers are never collapsed
  into a generic "记录事项" or "风险项"; a positive/boundary unit emits
  its own typed marker with its candidate identity, and a not_evaluable
  unit emits a coverage-gap marker (no candidate) so the view surfaces
  the gap without inventing a risk.

Deterministic bidirectional joins between journey events and risk markers
are verified by stable ids (``event_id + marker_id + unit_id +
risk_identity_id + join_reason + typed_ref_ids``), never by descriptive
text, nearest date, or episode alone (frozen D03 §9, §10).  A marker may
join many typed events; an event may join many markers from different
control units.

The module reuses the neutral identity accessors from ``contracts`` and
the Chinese audience labels from ``ip`` so the projection stays aligned
with the engine's identity and label decisions.  No production UI, real
project, provider, dictionary, or product service is involved.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..risks.ip import (
    ACCOUNTABILITY_PROXY_ANNOTATION,
    ACTION_DOSE_INCREASE,
    ACTION_DOSE_REDUCE,
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_STOP,
    ActualIPAction,
    IPActionEvidence,
    IPExposureEpisode,
    IPSemanticRecord,
    IPSliceError,
    IPSliceResult,
    IPUnitExpanded,
    IPUnitResult,
    IPExpectedSetExpansion,
    PlannedExposureAction,
    PlannedTreatmentAssignment,
    ExposureOccurrence,
    CONTROL_ACCOUNTABILITY,
    CONTROL_ADHERENCE,
    CONTROL_ALLOWED_ACTION,
    CONTROL_MEDICAL_ACTION,
    CONTROL_PLAN_ACTUAL,
    CONTROL_ROLE_PHASE,
    POSITIVE_SUBTYPE_LABELS,
)
from ..risks.contracts import (
    L1Disposition,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidate,
    RiskCandidateRef,
    candidate_identity_classifier,
    candidate_lineage_fingerprint,
    candidate_stable_core,
)
from .aemh import monitoring_priority_audience_label

__all__ = [
    "IPJourneyEvent",
    "IPRiskMarker",
    "IPJoinRecord",
    "IPEventMarkerJoin",
    "IPSubjectJourneyProjection",
    "IPTypedRef",
    "IP_RISK_FAMILY_LABELS",
    "EVENT_KIND_ADMINISTRATION",
    "EVENT_KIND_DISPENSE",
    "EVENT_KIND_RETURN",
    "EVENT_KIND_AE",
    "EVENT_KIND_LAB",
    "EVENT_KIND_EXAM",
    "EVENT_KIND_EFFICACY",
    "EVENT_KIND_VISIT",
    "IP_EVENT_KINDS",
    "PLANNED_OR_ACTUAL_PLANNED",
    "PLANNED_OR_ACTUAL_ACTUAL",
    "PLANNED_OR_ACTUAL_CONTEXT",
    "ANCHOR_KIND_EPISODE",
    "ANCHOR_KIND_OCCURRENCE",
    "ANCHOR_KIND_ACTION",
    "ANCHOR_KIND_MEDICAL_EVENT",
    "ANCHOR_KIND_UNRESOLVED",
    "JOIN_REASON_UNIT_IDENTITY",
    "JOIN_REASON_ANCHOR_EVENT",
    "JOIN_REASON_SOURCE_LOCATOR",
    "project_ip_journey_events",
    "project_ip_risk_markers",
    "project_ip_subject_journey",
    "bidirectional_join",
]


# ---------------------------------------------------------------------------
# Constants and label maps (frozen D03 §8, §9)
# ---------------------------------------------------------------------------

#: Typed visit-axis event kinds (frozen D03 §9 minimum set).
EVENT_KIND_ADMINISTRATION = "administration"
EVENT_KIND_DISPENSE = "dispense"
EVENT_KIND_RETURN = "return"
EVENT_KIND_PAUSE = "pause"
EVENT_KIND_DOSE_REDUCE = "dose_reduce"
EVENT_KIND_DOSE_INCREASE = "dose_increase"
EVENT_KIND_RESUME = "resume"
EVENT_KIND_STOP = "stop"
EVENT_KIND_AE = "ae"
EVENT_KIND_LAB = "lab"
EVENT_KIND_EXAM = "exam"
EVENT_KIND_EFFICACY = "efficacy"
EVENT_KIND_VISIT = "visit"

IP_EVENT_KINDS: Tuple[str, ...] = (
    EVENT_KIND_ADMINISTRATION, EVENT_KIND_DISPENSE, EVENT_KIND_RETURN,
    EVENT_KIND_PAUSE, EVENT_KIND_DOSE_REDUCE, EVENT_KIND_DOSE_INCREASE,
    EVENT_KIND_RESUME, EVENT_KIND_STOP, EVENT_KIND_AE, EVENT_KIND_LAB,
    EVENT_KIND_EXAM, EVENT_KIND_EFFICACY, EVENT_KIND_VISIT,
)

#: planned|actual|context tri-state for the visit axis.
PLANNED_OR_ACTUAL_PLANNED = "planned"
PLANNED_OR_ACTUAL_ACTUAL = "actual"
PLANNED_OR_ACTUAL_CONTEXT = "context"

#: Marker anchor kinds (frozen D03 §9 anchor_event_id_or_interval).
ANCHOR_KIND_EPISODE = "episode_interval"
ANCHOR_KIND_OCCURRENCE = "occurrence"
ANCHOR_KIND_ACTION = "action_interval"
ANCHOR_KIND_MEDICAL_EVENT = "medical_event"
ANCHOR_KIND_UNRESOLVED = "unresolved_component"

#: Join reasons (stable engineering codes, never audience text).
JOIN_REASON_UNIT_IDENTITY = "unit_identity"
JOIN_REASON_ANCHOR_EVENT = "anchor_event"
JOIN_REASON_SOURCE_LOCATOR = "shared_source_locator"

#: IP risk-family engineering code -> Chinese audience label.
#: Frozen D03 §8 audience labels are reused for positive subtypes; the six
#: risk families get concrete wording.  Engineering codes never appear in
#: the audience label.
IP_RISK_FAMILY_LABELS: Dict[str, str] = {
    "plan_actual_exposure": "研究药给药与方案不一致",
    "treatment_role_phase": "治疗分组或阶段待核实",
    "adherence": "研究药依从性待核实",
    "ip_action": "给药调整依据待核实",
    "medical_action": "给药处置与医学事件不一致",
    "ip_accountability": "研究药物核算待核实",
}
#: Fallback Chinese label for an unrecognized risk family.  This is a
#: concrete research-drug phrase, never an internal engineering code.
_UNKNOWN_FAMILY_LABEL = "研究药暴露信息待核实"

#: action_type -> event_kind mapping (stable engineering codes).
_ACTION_KIND_MAP: Dict[str, str] = {
    ACTION_PAUSE: EVENT_KIND_PAUSE,
    ACTION_DOSE_REDUCE: EVENT_KIND_DOSE_REDUCE,
    ACTION_DOSE_INCREASE: EVENT_KIND_DOSE_INCREASE,
    ACTION_RESUME: EVENT_KIND_RESUME,
    ACTION_STOP: EVENT_KIND_STOP,
}

#: medical-trigger source_role -> event_kind mapping.
_TRIGGER_KIND_MAP: Dict[str, str] = {
    "reported_ae": EVENT_KIND_AE,
    "lab_finding": EVENT_KIND_LAB,
    "exam_finding": EVENT_KIND_EXAM,
    "efficacy_assessment": EVENT_KIND_EFFICACY,
}


def _risk_family_audience_label(
    risk_family: str, positive_subtype: str, audience_label: str,
) -> str:
    """Resolve the Chinese audience label for a risk marker.

    A positive unit carries the engine's audience label already (one of
    the six frozen §8 subtype labels).  A boundary/not_evaluable marker
    that is not positive falls back to the risk-family label so the marker
    shows its concrete risk type without collapsing into a generic marker.
    An unknown risk family must NEVER leak its internal engineering code;
    it falls back to a natural Chinese phrase (frozen D03 §8/§9).
    """
    if audience_label.strip():
        return audience_label.strip()
    if positive_subtype.strip() and positive_subtype in POSITIVE_SUBTYPE_LABELS:
        return POSITIVE_SUBTYPE_LABELS[positive_subtype]
    return IP_RISK_FAMILY_LABELS.get(risk_family, _UNKNOWN_FAMILY_LABEL)


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


def _candidate_id_of(unit: IPUnitResult) -> str:
    """Return the primary candidate id from a unit's candidate refs, or ''."""
    for ref in unit.risk_candidate_refs:
        if isinstance(ref, RiskCandidateRef) and ref.candidate_id:
            return ref.candidate_id
    return ""


def _candidate_detail(unit: IPUnitResult,
                      candidates: Sequence[RiskCandidate],
                      ) -> Optional[RiskCandidate]:
    """Return the R2 candidate object matching the unit's primary candidate."""
    cid = _candidate_id_of(unit)
    if not cid:
        return None
    for cand in candidates:
        if cand.candidate_id == cid:
            return cand
    return None


def _display_role_label(assignment: Optional[PlannedTreatmentAssignment]) -> str:
    """Disclosure-safe display label; never leaks masked identity."""
    if assignment is not None and assignment.display_role_label.strip():
        return assignment.display_role_label.strip()
    return "研究药物"


# ---------------------------------------------------------------------------
# IPTypedRef -- stable typed reference (frozen D03 §9 typed_refs)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPTypedRef:
    """One stable typed reference on an event or risk marker.

    ``kind`` is a stable engineering code: ``assignment`` | ``rule`` |
    ``algorithm`` | ``medical_event`` | ``source_locator`` | ``query``.
    ``ref_id`` is the stable id (never a snapshot/revision).  ``role`` is a
    short semantic role for the reference (e.g. the medical-trigger source
    role).  Typed refs make one-hop drill-back explicit and stable without
    relying on descriptive text.
    """

    kind: str
    ref_id: str
    role: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.ref_id, str) or not self.ref_id.strip():
            raise IPSliceError("IPTypedRef.ref_id is required")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise IPSliceError("IPTypedRef.kind is required")

    def typed_ref_id(self) -> str:
        return f"{self.kind}:{self.ref_id}"


def _typed_ref_ids(refs: Sequence[IPTypedRef]) -> Tuple[str, ...]:
    return tuple(sorted(set(r.typed_ref_id() for r in refs)))


# ---------------------------------------------------------------------------
# IPJourneyEvent (frozen D03 §9 minimum fields)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPJourneyEvent:
    """One typed event on the subject medical journey visit/time axis.

    Minimum fields (frozen D03 §9): ``event_id / event_kind /
    planned_or_actual / episode_id / stable_ip_event_key / assignment_id /
    treatment_role_token / display_role_label / disclosure_state / start /
    end / date_precision / visit / phase / dose / unit / route /
    frequency / typed_refs / source_locator_ids / uncertainty``.

    ``event_kind`` is one of the typed visit-axis kinds (administration,
    dispense, return, pause, dose_reduce, dose_increase, resume, stop, ae,
    lab, exam, efficacy, visit).  ``planned_or_actual`` distinguishes
    planned intent from confirmed actual evidence from context.  The
    display role label is disclosure-safe; masked identity never leaks.
    """

    event_id: str
    event_kind: str
    planned_or_actual: str
    episode_id: str
    stable_ip_event_key: str
    subject_ref: str
    start: str
    end: str
    date_precision: str
    source_locator_ids: Tuple[str, ...]
    unit_ids: Tuple[str, ...]
    typed_refs: Tuple[IPTypedRef, ...] = ()
    assignment_id: str = ""
    treatment_role_token: str = ""
    display_role_label: str = ""
    disclosure_state: str = ""
    dose: str = ""
    unit: str = ""
    route: str = ""
    frequency: str = ""
    visit: str = ""
    phase: str = ""
    uncertainty: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise IPSliceError("IPJourneyEvent.event_id is required")
        if self.event_kind not in IP_EVENT_KINDS:
            raise IPSliceError(
                f"IPJourneyEvent.event_kind={self.event_kind!r} invalid")
        if self.planned_or_actual not in (
                PLANNED_OR_ACTUAL_PLANNED, PLANNED_OR_ACTUAL_ACTUAL,
                PLANNED_OR_ACTUAL_CONTEXT):
            raise IPSliceError(
                f"IPJourneyEvent.planned_or_actual="
                f"{self.planned_or_actual!r} invalid")
        if not self.episode_id.strip():
            raise IPSliceError("IPJourneyEvent.episode_id is required")
        if not self.stable_ip_event_key.strip():
            raise IPSliceError("IPJourneyEvent.stable_ip_event_key is required")
        if not self.subject_ref.strip():
            raise IPSliceError("IPJourneyEvent.subject_ref is required")
        loc = tuple(sorted(set(self.source_locator_ids)))
        if not loc:
            raise IPSliceError(
                "IPJourneyEvent must carry at least one source locator id")
        object.__setattr__(self, "source_locator_ids", loc)
        object.__setattr__(self, "unit_ids", tuple(self.unit_ids))
        object.__setattr__(self, "typed_refs", tuple(self.typed_refs))

    def typed_ref_ids(self) -> Tuple[str, ...]:
        return _typed_ref_ids(self.typed_refs)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "planned_or_actual": self.planned_or_actual,
            "episode_id": self.episode_id,
            "stable_ip_event_key": self.stable_ip_event_key,
            "subject_ref": self.subject_ref,
            "start": self.start,
            "end": self.end,
            "date_precision": self.date_precision,
            "source_locator_ids": list(self.source_locator_ids),
            "unit_ids": list(self.unit_ids),
            "typed_refs": [
                {"kind": r.kind, "ref_id": r.ref_id, "role": r.role}
                for r in self.typed_refs],
            "assignment_id": self.assignment_id,
            "treatment_role_token": self.treatment_role_token,
            "display_role_label": self.display_role_label,
            "disclosure_state": self.disclosure_state,
            "dose": self.dose,
            "unit": self.unit,
            "route": self.route,
            "frequency": self.frequency,
            "visit": self.visit,
            "phase": self.phase,
            "uncertainty": self.uncertainty,
        }


# ---------------------------------------------------------------------------
# IPRiskMarker (frozen D03 §9 minimum fields)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPRiskMarker:
    """One risk marker anchored on the IP journey.

    Minimum fields (frozen D03 §9): ``marker_id / unit_id /
    risk_identity_id / subtype / audience_label / priority / anchor_kind /
    anchor_event_id_or_interval / typed_refs / source_locator_ids /
    query_id / uncertainty``.

    A positive or boundary unit produces one risk marker carrying its
    candidate id; a not_evaluable unit produces a coverage-gap marker (no
    candidate) so the view surfaces the gap without inventing a risk.
    ``anchor_event_id_or_interval`` is a stable event id or a stable
    interval descriptor; the join uses it via ``JOIN_REASON_ANCHOR_EVENT``.
    """

    marker_id: str
    unit_id: str
    risk_identity_id: str
    subtype: str
    audience_label: str
    priority: str
    anchor_kind: str
    anchor_event_id_or_interval: str
    typed_refs: Tuple[IPTypedRef, ...]
    source_locator_ids: Tuple[str, ...]
    query_id: str
    uncertainty: str
    risk_family: str = ""
    l1_disposition: str = ""
    candidate_or_risk_id: str = ""
    coverage_gap: bool = False
    episode_id: str = ""
    stable_core: str = ""
    lineage_fingerprint: str = ""
    classifier: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.marker_id, str) or not self.marker_id.strip():
            raise IPSliceError("IPRiskMarker.marker_id is required")
        if not self.unit_id.strip():
            raise IPSliceError("IPRiskMarker.unit_id is required")
        if not self.audience_label.strip():
            raise IPSliceError("IPRiskMarker.audience_label is required")
        if self.priority not in (
                MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_MEDIUM,
                MONITORING_PRIORITY_LOW, MONITORING_PRIORITY_UNKNOWN):
            raise IPSliceError(
                f"IPRiskMarker.priority={self.priority!r} invalid")
        if self.anchor_kind not in (ANCHOR_KIND_EPISODE, ANCHOR_KIND_OCCURRENCE,
                                    ANCHOR_KIND_ACTION,
                                    ANCHOR_KIND_MEDICAL_EVENT,
                                    ANCHOR_KIND_UNRESOLVED):
            raise IPSliceError(
                f"IPRiskMarker.anchor_kind={self.anchor_kind!r} invalid")
        if not self.anchor_event_id_or_interval.strip():
            raise IPSliceError("IPRiskMarker.anchor_event_id_or_interval required")
        object.__setattr__(self, "typed_refs", tuple(self.typed_refs))
        loc = tuple(sorted(set(self.source_locator_ids)))
        if not loc:
            raise IPSliceError(
                "IPRiskMarker must carry at least one source locator id")
        object.__setattr__(self, "source_locator_ids", loc)

    @property
    def is_risk_marker(self) -> bool:
        """A marker is a genuine risk marker when it carries a candidate or
        risk id (positive/boundary).  A pure coverage-gap marker without a
        candidate is a not_evaluable marker, not an established risk."""
        return bool(self.candidate_or_risk_id.strip())

    def typed_ref_ids(self) -> Tuple[str, ...]:
        return _typed_ref_ids(self.typed_refs)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "marker_id": self.marker_id,
            "unit_id": self.unit_id,
            "risk_identity_id": self.risk_identity_id,
            "subtype": self.subtype,
            "audience_label": self.audience_label,
            "priority": self.priority,
            "anchor_kind": self.anchor_kind,
            "anchor_event_id_or_interval": self.anchor_event_id_or_interval,
            "typed_refs": [
                {"kind": r.kind, "ref_id": r.ref_id, "role": r.role}
                for r in self.typed_refs],
            "source_locator_ids": list(self.source_locator_ids),
            "query_id": self.query_id,
            "uncertainty": self.uncertainty,
            "risk_family": self.risk_family,
            "l1_disposition": self.l1_disposition,
            "candidate_or_risk_id": self.candidate_or_risk_id,
            "coverage_gap": self.coverage_gap,
            "episode_id": self.episode_id,
            "stable_core": self.stable_core,
            "lineage_fingerprint": self.lineage_fingerprint,
            "classifier": self.classifier,
        }


# ---------------------------------------------------------------------------
# IPJoinRecord + IPEventMarkerJoin (frozen D03 §9, §10)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPJoinRecord:
    """One deterministic bidirectional join edge.

    Frozen D03 §9: ``event_id + marker_id + unit_id + risk_identity_id +
    join_reason + typed_ref_ids``.  Every edge is verified by stable ids
    and typed refs; descriptive text, nearest date, or episode alone is
    never a join key.
    """

    event_id: str
    marker_id: str
    unit_id: str
    risk_identity_id: str
    join_reason: str
    typed_ref_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise IPSliceError("IPJoinRecord.event_id is required")
        if not self.marker_id.strip():
            raise IPSliceError("IPJoinRecord.marker_id is required")
        if not self.unit_id.strip():
            raise IPSliceError("IPJoinRecord.unit_id is required")
        if not self.join_reason.strip():
            raise IPSliceError("IPJoinRecord.join_reason is required")
        object.__setattr__(self, "typed_ref_ids",
                           tuple(sorted(set(self.typed_ref_ids))))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "marker_id": self.marker_id,
            "unit_id": self.unit_id,
            "risk_identity_id": self.risk_identity_id,
            "join_reason": self.join_reason,
            "typed_ref_ids": list(self.typed_ref_ids),
        }


@dataclass(frozen=True)
class IPEventMarkerJoin:
    """Deterministic many-to-many bidirectional join index.

    Defines the many-to-many relation between IP journey events and risk
    markers (frozen D03 §9: "一个 marker 可关联多个有明确角色的 event，一个
    event 可关联多个不同控制单元 marker；每一条边都必须由稳定 id 和 typed
    ref 校验").  ``records`` is the canonical edge list; ``markers_by_event``
    and ``events_by_marker`` are the deduplicated bidirectional index.
    """

    records: Tuple[IPJoinRecord, ...] = ()
    markers_by_event: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    events_by_marker: Dict[str, Tuple[str, ...]] = field(default_factory=dict)

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
            "records": [r.canonical_payload() for r in self.records],
            "markers_by_event": {
                k: list(v) for k, v in sorted(self.markers_by_event.items())},
            "events_by_marker": {
                k: list(v) for k, v in sorted(self.events_by_marker.items())},
        }


def bidirectional_join(
    events: Sequence[IPJourneyEvent],
    markers: Sequence[IPRiskMarker],
) -> IPEventMarkerJoin:
    """Build the deterministic bidirectional event-marker join index.

    A marker joins to a journey event when EITHER:

    * they share the same ``episode_id`` AND the event's ``unit_ids``
      contains the marker's ``unit_id`` (``JOIN_REASON_UNIT_IDENTITY``) --
      the primary stable unit-identity join; episode alone is never
      sufficient (frozen D03 §9);
    * the event's ``event_id`` equals the marker's
      ``anchor_event_id_or_interval`` (``JOIN_REASON_ANCHOR_EVENT``) for
      markers that anchor on a specific occurrence/action/medical event;
    * they share at least one source locator id
      (``JOIN_REASON_SOURCE_LOCATOR``) -- verified drill-back to the same
      original EX/EC/DA/IP row.

    Every edge carries the marker's risk identity and the union of the
    two nodes' typed ref ids.  Joining is by stable ids only; descriptive
    text and nearest date are never used.
    """
    records: List[IPJoinRecord] = []
    marker_by_id: Dict[str, IPRiskMarker] = {}
    event_by_id: Dict[str, IPJourneyEvent] = {}
    events_by_episode: Dict[str, List[str]] = {}
    for ev in events:
        event_by_id[ev.event_id] = ev
        events_by_episode.setdefault(ev.episode_id, []).append(ev.event_id)

    for m in markers:
        marker_by_id[m.marker_id] = m
        linked_event_ids: Set[str] = set()
        reasons: Dict[str, str] = {}
        # Primary: episode + unit identity.
        for eid in events_by_episode.get(m.episode_id, []):
            ev = event_by_id.get(eid)
            if ev is not None and m.unit_id in ev.unit_ids:
                linked_event_ids.add(eid)
                reasons[eid] = JOIN_REASON_UNIT_IDENTITY
        # Anchor event.
        if m.anchor_event_id_or_interval in event_by_id:
            linked_event_ids.add(m.anchor_event_id_or_interval)
            reasons.setdefault(m.anchor_event_id_or_interval,
                               JOIN_REASON_ANCHOR_EVENT)
        # Shared source locator (drill-back to same original row).
        marker_locs = set(m.source_locator_ids)
        for ev in events:
            if ev.event_id in linked_event_ids:
                continue
            if marker_locs & set(ev.source_locator_ids):
                linked_event_ids.add(ev.event_id)
                reasons[ev.event_id] = JOIN_REASON_SOURCE_LOCATOR
        for eid in sorted(linked_event_ids):
            ev = event_by_id.get(eid)
            typed_ids = _typed_ref_ids(m.typed_refs)
            if ev is not None:
                typed_ids = tuple(sorted(set(
                    typed_ids + ev.typed_ref_ids())))
            records.append(IPJoinRecord(
                event_id=eid, marker_id=m.marker_id, unit_id=m.unit_id,
                risk_identity_id=m.risk_identity_id,
                join_reason=reasons[eid], typed_ref_ids=typed_ids))
    return IPEventMarkerJoin(records=tuple(records))


# ---------------------------------------------------------------------------
# Per-unit projection helpers
# ---------------------------------------------------------------------------

def _assignments_by_episode(
    expansions: Optional[IPExpectedSetExpansion],
) -> Dict[str, PlannedTreatmentAssignment]:
    if expansions is None:
        return {}
    out: Dict[str, PlannedTreatmentAssignment] = {}
    for eu in expansions.units:
        if eu.assignment is not None:
            out.setdefault(eu.episode.episode_key, eu.assignment)
    return out


def _expanded_by_unit(
    expansions: Optional[IPExpectedSetExpansion],
) -> Dict[str, IPUnitExpanded]:
    if expansions is None:
        return {}
    out: Dict[str, IPUnitExpanded] = {}
    for eu in expansions.units:
        out[eu.build_unit(expansions.project_id).unit_id] = eu
    return out


def _unit_ids_for_episode(
    expansions: Optional[IPExpectedSetExpansion], episode_key: str,
) -> Tuple[str, ...]:
    if expansions is None:
        return ()
    ids: List[str] = []
    for eu in expansions.units:
        if eu.episode.episode_key == episode_key:
            ids.append(eu.build_unit(expansions.project_id).unit_id)
    return tuple(sorted(set(ids)))


def _episode_assignment_ref(
    assignment: Optional[PlannedTreatmentAssignment],
) -> Optional[IPTypedRef]:
    if assignment is None:
        return None
    return IPTypedRef(kind="assignment", ref_id=assignment.assignment_id,
                      role="planned_assignment")


def _source_ref(locator_id_role: str, locator_id: str) -> IPTypedRef:
    return IPTypedRef(kind="source_locator", ref_id=locator_id,
                      role=locator_id_role)


def _anchor_interval(episode: Optional[IPExposureEpisode],
                     start: str, end: str, ongoing: bool) -> str:
    """Stable anchor interval string for markers."""
    end_token = "持续中" if ongoing else (end or start or "none")
    return f"{start or 'none'}|{end_token}"


# ---------------------------------------------------------------------------
# Event construction (frozen D03 §9 typed visit-axis events)
# ---------------------------------------------------------------------------

def _build_episode_event(
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    unit_ids: Sequence[str],
) -> IPJourneyEvent:
    """One administration event for the episode's study-drug span."""
    refs: List[IPTypedRef] = []
    asg_ref = _episode_assignment_ref(assignment)
    if asg_ref is not None:
        refs.append(asg_ref)
    refs.append(_source_ref(
        episode.source_locator.table_semantic,
        episode.source_locator.locator_id()))
    end = ("持续中" if episode.span_ongoing else episode.span_end)
    return IPJourneyEvent(
        event_id=f"ip-ev-admin-{episode.episode_key}",
        event_kind=EVENT_KIND_ADMINISTRATION,
        planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
        episode_id=episode.episode_key,
        stable_ip_event_key=episode.stable_ip_event_key,
        subject_ref=episode.subject_ref,
        start=episode.span_start,
        end=end,
        date_precision=_precision_of_date(episode.span_start),
        source_locator_ids=(episode.source_locator.locator_id(),),
        unit_ids=tuple(unit_ids),
        typed_refs=tuple(refs),
        assignment_id=(assignment.assignment_id if assignment else ""),
        treatment_role_token=episode.actual_treatment_role,
        display_role_label=_display_role_label(assignment),
        disclosure_state=episode.disclosure_state,
        dose=episode.dose, unit=episode.dose_unit,
        route=episode.route, frequency=episode.frequency,
        phase=episode.study_phase, visit=episode.study_phase)


def _build_occurrence_events(
    episode: IPExposureEpisode, occurrences: Sequence[ExposureOccurrence],
    unit_ids: Sequence[str],
) -> Tuple[IPJourneyEvent, ...]:
    """One administration event per accepted occurrence (actual dosing)."""
    events: List[IPJourneyEvent] = []
    ep_occs = [o for o in occurrences
               if o.episode_key == episode.episode_key]
    for occ in ep_occs:
        end = occ.date_end or occ.date_start
        events.append(IPJourneyEvent(
            event_id=f"ip-ev-admin-{episode.episode_key}-{occ.occurrence_id}",
            event_kind=EVENT_KIND_ADMINISTRATION,
            planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id=episode.episode_key,
            stable_ip_event_key=(
                f"{occ.source_locator.table_semantic}:"
                f"{occ.source_locator.record_id}"),
            subject_ref=episode.subject_ref,
            start=occ.date_start, end=end,
            date_precision=_precision_of_date(occ.date_start),
            source_locator_ids=(occ.source_locator.locator_id(),),
            unit_ids=tuple(unit_ids),
            typed_refs=(_source_ref(occ.source_locator.table_semantic,
                                    occ.source_locator.locator_id()),),
            assignment_id=occ.assignment_id,
            treatment_role_token=episode.actual_treatment_role,
            display_role_label="研究药物",
            disclosure_state=episode.disclosure_state,
            dose=occ.dose, unit=occ.dose_unit, route=occ.route,
            frequency=occ.frequency, phase=episode.study_phase))
    return tuple(events)


def _build_action_events(
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    planned_actions: Sequence[PlannedExposureAction],
    actual_actions: Sequence[ActualIPAction],
    unit_ids: Sequence[str],
) -> Tuple[IPJourneyEvent, ...]:
    """Typed pause/reduce/increase/resume/stop events (planned vs actual)."""
    events: List[IPJourneyEvent] = []
    asg_ref = _episode_assignment_ref(assignment)
    for action in planned_actions:
        if action.episode_key != episode.episode_key:
            continue
        kind = _ACTION_KIND_MAP.get(action.action_type)
        if kind is None:
            continue
        refs: List[IPTypedRef] = []
        if asg_ref is not None:
            refs.append(asg_ref)
        if action.source_locator is not None:
            refs.append(_source_ref(action.source_locator.table_semantic,
                                    action.source_locator.locator_id()))
        end = action.action_end or action.action_start
        events.append(IPJourneyEvent(
            event_id=f"ip-ev-{kind}-{action.action_id}",
            event_kind=kind, planned_or_actual=PLANNED_OR_ACTUAL_PLANNED,
            episode_id=episode.episode_key,
            stable_ip_event_key=(
                f"{action.source_locator.table_semantic}:"
                f"{action.source_locator.record_id}" if action.source_locator
                else f"planned_action:{action.action_id}"),
            subject_ref=episode.subject_ref,
            start=action.action_start, end=end,
            date_precision=_precision_of_date(action.action_start),
            source_locator_ids=(
                (action.source_locator.locator_id(),)
                if action.source_locator else (episode.source_locator.locator_id(),)),
            unit_ids=tuple(unit_ids), typed_refs=tuple(refs),
            assignment_id=action.assignment_id,
            treatment_role_token=episode.actual_treatment_role,
            display_role_label=_display_role_label(assignment),
            disclosure_state=episode.disclosure_state,
            dose=action.dose_after, unit=action.dose_unit,
            phase=episode.study_phase, uncertainty=action.reason))
    for action in actual_actions:
        if action.episode_key != episode.episode_key:
            continue
        kind = _ACTION_KIND_MAP.get(action.action_type)
        if kind is None:
            continue
        refs = []
        if asg_ref is not None:
            refs.append(asg_ref)
        if action.source_locator is not None:
            refs.append(_source_ref(action.source_locator.table_semantic,
                                    action.source_locator.locator_id()))
        end = action.action_end or action.action_start
        events.append(IPJourneyEvent(
            event_id=f"ip-ev-{kind}-{action.action_id}",
            event_kind=kind, planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id=episode.episode_key,
            stable_ip_event_key=(
                f"{action.source_locator.table_semantic}:"
                f"{action.source_locator.record_id}" if action.source_locator
                else f"actual_action:{action.action_id}"),
            subject_ref=episode.subject_ref,
            start=action.action_start, end=end,
            date_precision=_precision_of_date(action.action_start),
            source_locator_ids=(
                (action.source_locator.locator_id(),)
                if action.source_locator else (episode.source_locator.locator_id(),)),
            unit_ids=tuple(unit_ids), typed_refs=tuple(refs),
            assignment_id=action.assignment_id,
            treatment_role_token=episode.actual_treatment_role,
            display_role_label=_display_role_label(assignment),
            disclosure_state=episode.disclosure_state,
            dose=action.dose_after, unit=action.dose_unit,
            phase=episode.study_phase, uncertainty=action.reason))
    return tuple(events)


def _build_accountability_events(
    episode: IPExposureEpisode, records: Sequence[IPSemanticRecord],
    kind: str, unit_ids: Sequence[str],
) -> Tuple[IPJourneyEvent, ...]:
    """Typed dispense/return events from semantic accountability rows."""
    events: List[IPJourneyEvent] = []
    for rec in records:
        if rec.linked_ip_episode_key and \
                rec.linked_ip_episode_key != episode.episode_key:
            continue
        if rec.subject_ref and rec.subject_ref != episode.subject_ref:
            continue
        start = rec.event_start_raw or episode.span_start
        end = rec.event_end_raw or start
        amount = rec.amount_value or ""
        unit = rec.amount_unit or ""
        events.append(IPJourneyEvent(
            event_id=f"ip-ev-{kind}-{rec.stable_source_event_key}",
            event_kind=kind, planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id=episode.episode_key,
            stable_ip_event_key=rec.stable_source_event_key,
            subject_ref=episode.subject_ref,
            start=start, end=end,
            date_precision=_precision_of_date(start),
            source_locator_ids=(rec.locator.locator_id(),),
            unit_ids=tuple(unit_ids),
            typed_refs=(_source_ref(rec.locator.table_semantic,
                                    rec.locator.locator_id()),),
            treatment_role_token=episode.actual_treatment_role,
            display_role_label="研究药物",
            disclosure_state=episode.disclosure_state,
            dose=amount, unit=unit, phase=episode.study_phase))
    return tuple(events)


def _build_evidence_events(
    episode: IPExposureEpisode, evidence: Sequence[IPActionEvidence],
    unit_ids: Sequence[str],
) -> Tuple[IPJourneyEvent, ...]:
    """Typed ae/lab/exam/efficacy medical-trigger context events."""
    events: List[IPJourneyEvent] = []
    for ev in evidence:
        if ev.subject_ref != episode.subject_ref:
            continue
        if ev.linked_ip_episode_id and \
                ev.linked_ip_episode_id != episode.episode_key:
            continue
        kind = _TRIGGER_KIND_MAP.get(ev.source_role)
        if kind is None:
            continue
        start = ev.event_start or episode.span_start
        end = ev.event_end or start
        events.append(IPJourneyEvent(
            event_id=f"ip-ev-{kind}-{ev.stable_source_event_key}",
            event_kind=kind, planned_or_actual=PLANNED_OR_ACTUAL_CONTEXT,
            episode_id=ev.linked_ip_episode_id or episode.episode_key,
            stable_ip_event_key=ev.stable_source_event_key,
            subject_ref=episode.subject_ref,
            start=start, end=end,
            date_precision=_precision_of_date(start),
            source_locator_ids=(ev.source_locator.locator_id(),),
            unit_ids=tuple(unit_ids),
            typed_refs=(
                IPTypedRef(kind="medical_event",
                           ref_id=ev.stable_source_event_key,
                           role=ev.source_role),
                _source_ref(ev.source_locator.table_semantic,
                            ev.source_locator.locator_id()),
            ),
            treatment_role_token=episode.actual_treatment_role,
            display_role_label="研究药物",
            disclosure_state=episode.disclosure_state,
            phase=episode.study_phase, uncertainty=ev.concept))
    return tuple(events)


def _build_visit_event(
    episode: IPExposureEpisode, unit_ids: Sequence[str],
) -> IPJourneyEvent:
    """One visit-axis anchor event for the episode's phase."""
    return IPJourneyEvent(
        event_id=f"ip-ev-visit-{episode.episode_key}",
        event_kind=EVENT_KIND_VISIT, planned_or_actual=PLANNED_OR_ACTUAL_CONTEXT,
        episode_id=episode.episode_key,
        stable_ip_event_key=episode.stable_ip_event_key,
        subject_ref=episode.subject_ref,
        start=episode.span_start,
        end=("持续中" if episode.span_ongoing else
             (episode.span_end or episode.span_start)),
        date_precision=_precision_of_date(episode.span_start),
        source_locator_ids=(episode.source_locator.locator_id(),),
        unit_ids=tuple(unit_ids),
        typed_refs=(_source_ref(episode.source_locator.table_semantic,
                                episode.source_locator.locator_id()),),
        treatment_role_token=episode.actual_treatment_role,
        display_role_label="研究药物",
        disclosure_state=episode.disclosure_state,
        phase=episode.study_phase, visit=episode.study_phase)


# ---------------------------------------------------------------------------
# Per-unit projection
# ---------------------------------------------------------------------------

def project_ip_journey_events(
    unit_result: IPUnitResult,
    *,
    episode: Optional[IPExposureEpisode] = None,
    assignment: Optional[PlannedTreatmentAssignment] = None,
    expansions: Optional[IPExpectedSetExpansion] = None,
    occurrences: Sequence[ExposureOccurrence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
) -> Tuple[IPJourneyEvent, ...]:
    """Project the typed visit-axis events for one unit's episode.

    Returns the full typed event set for the episode: the episode
    administration event, per-occurrence administration events, typed
    planned/actual action events, dispense/return events, medical-trigger
    context events, and one visit anchor.  Returns () when no episode
    context is available (no episode supplied and no journey marker).
    """
    if episode is None:
        marker = unit_result.journey_markers[0] if unit_result.journey_markers else None
        if marker is None:
            return ()
    if episode is None:
        return ()
    unit_ids = _unit_ids_for_episode(expansions, episode.episode_key)
    if not unit_ids and unit_result is not None:
        unit_ids = (unit_result.unit_id,)
    events: List[IPJourneyEvent] = []
    events.append(_build_episode_event(episode, assignment, unit_ids))
    events.extend(_build_occurrence_events(episode, occurrences, unit_ids))
    events.extend(_build_action_events(
        episode, assignment, planned_actions, actual_actions, unit_ids))
    events.extend(_build_accountability_events(episode, return_records,
                                               EVENT_KIND_RETURN, unit_ids))
    events.extend(_build_accountability_events(episode, dispense_records,
                                               EVENT_KIND_DISPENSE, unit_ids))
    events.extend(_build_evidence_events(episode, action_evidence, unit_ids))
    events.append(_build_visit_event(episode, unit_ids))
    return tuple(events)


def _marker_typed_refs(
    expanded: Optional[IPUnitExpanded],
    query_id: str,
) -> Tuple[IPTypedRef, ...]:
    """Typed refs for a marker: assignment/rule/algorithm + query."""
    refs: List[IPTypedRef] = []
    if expanded is not None:
        if expanded.assignment is not None:
            refs.append(IPTypedRef(kind="assignment",
                                   ref_id=expanded.assignment.assignment_id,
                                   role="planned_assignment"))
        if expanded.rule is not None:
            refs.append(IPTypedRef(kind="rule", ref_id=expanded.rule.rule_id,
                                   role="protocol_rule"))
        if expanded.algorithm is not None:
            refs.append(IPTypedRef(kind="algorithm",
                                   ref_id=expanded.algorithm.algorithm_id,
                                   role="adherence_algorithm"))
    if query_id:
        refs.append(IPTypedRef(kind="query", ref_id=query_id,
                               role="query_draft"))
    return tuple(refs)


def _is_proxy_backed(expanded: Optional[IPUnitExpanded]) -> bool:
    """True for an accountability control, or an adherence control whose
    metric is the dispense/return ``accountability_proxy`` (frozen
    D03 §3.2, §6.2)."""
    if expanded is None:
        return False
    if expanded.control_item == CONTROL_ACCOUNTABILITY:
        return True
    return (expanded.control_item == CONTROL_ADHERENCE
            and expanded.algorithm is not None
            and expanded.algorithm.is_accountability_proxy)


def _proxy_backed_uncertainty(text: str) -> str:
    """Frozen §6.2: a proxy-backed marker's user-visible uncertainty must
    carry the exact ``按发放/回收核算`` annotation and must never be
    presented as proven actual dosing days (the disclaimer deliberately
    omits the token ``实际服药天数``)."""
    parts = [p for p in (text, ACCOUNTABILITY_PROXY_ANNOTATION)
             if p and p.strip()]
    return "；".join(parts)


def project_ip_risk_markers(
    unit_result: IPUnitResult,
    *,
    candidates: Sequence[RiskCandidate] = (),
    expanded: Optional[IPUnitExpanded] = None,
    episode: Optional[IPExposureEpisode] = None,
    risk_family_hint: str = "",
) -> Tuple[IPRiskMarker, ...]:
    """Project risk markers for one unit result.

    A positive or boundary unit produces one risk marker carrying its
    candidate id and the six-subtype Chinese audience label.  A
    not_evaluable unit produces a coverage-gap marker (no candidate) so
    the view surfaces the gap without inventing a risk.  A negative or
    not_applicable unit produces no marker.

    ``risk_family_hint`` carries the expanded unit's risk family so the
    marker is correctly typed even when the engine attaches no journey
    marker to a not_evaluable unit.
    """
    disposition = unit_result.l1_disposition
    if disposition in (L1Disposition.NEGATIVE, L1Disposition.NOT_APPLICABLE):
        return ()

    marker_base = (unit_result.journey_markers[0]
                   if unit_result.journey_markers else None)
    risk_family = ""
    if marker_base is not None:
        risk_family = marker_base.get("risk_family", "")
    if not risk_family:
        risk_family = risk_family_hint or "ip_action"

    # Source locator ids for drill-back.
    source_ids: List[str] = []
    for sref in unit_result.source_record_refs:
        source_ids.append(sref.locator.locator_id())
    for ev in unit_result.evidence:
        source_ids.append(ev.locator.locator_id())
    for ref in unit_result.risk_candidate_refs:
        if ref.locator is not None:
            source_ids.append(ref.locator.locator_id())
    source_ids = sorted(set(x for x in source_ids if x))
    if not source_ids and marker_base is not None:
        sid = marker_base.get("source_locator_id", "")
        if sid:
            source_ids.append(sid)
    if episode is not None:
        source_ids.append(episode.source_locator.locator_id())
        source_ids = sorted(set(source_ids))

    # Candidate / identity detail via neutral accessors.
    cand = _candidate_detail(unit_result, candidates)
    candidate_id = _candidate_id_of(unit_result)
    risk_identity_id = ""
    stable_core = ""
    lineage_fingerprint = ""
    classifier = ""
    if cand is not None:
        risk_identity_id = str(cand.detail.get("risk_identity_id", ""))
        stable_core = candidate_stable_core(cand)
        lineage_fingerprint = candidate_lineage_fingerprint(cand)
        classifier = candidate_identity_classifier(cand)
    elif unit_result.risk_candidate_refs:
        ref0 = unit_result.risk_candidate_refs[0]
        risk_identity_id = ref0.risk_identity_id

    # Query ids.
    query_ids = [q.query_id for q in unit_result.query_refs
                 if isinstance(q, QueryDraftRef)]
    query_id = query_ids[0] if query_ids else ""

    audience_label = _risk_family_audience_label(
        risk_family, unit_result.positive_subtype,
        unit_result.audience_label)
    priority = unit_result.monitoring_priority
    coverage_gap = disposition == L1Disposition.NOT_EVALUABLE

    episode_id = ""
    if episode is not None:
        episode_id = episode.episode_key
    elif marker_base is not None:
        episode_id = marker_base.get("episode_id", "")

    # Anchor: episode interval for most controls; occurrence/action/medical
    # events anchor on their specific event id when available.
    anchor_kind = ANCHOR_KIND_EPISODE
    anchor_event_id_or_interval = ""
    if episode is not None:
        anchor_event_id_or_interval = _anchor_interval(
            episode, episode.span_start, episode.span_end,
            episode.span_ongoing)
    elif marker_base is not None:
        anchor_event_id_or_interval = _anchor_interval(
            None, marker_base.get("start", ""), marker_base.get("end", ""),
            False)
    control = ""
    if expanded is not None:
        control = expanded.control_item
    if disposition == L1Disposition.NOT_EVALUABLE:
        # A coverage gap has no determinable risk position; anchor it as
        # unresolved (frozen D03 §9) regardless of control item.
        anchor_kind = ANCHOR_KIND_UNRESOLVED
    elif control == CONTROL_MEDICAL_ACTION:
        anchor_kind = ANCHOR_KIND_MEDICAL_EVENT
    elif control == CONTROL_ALLOWED_ACTION:
        anchor_kind = ANCHOR_KIND_ACTION
    elif control in (CONTROL_ADHERENCE, CONTROL_ACCOUNTABILITY,
                     CONTROL_PLAN_ACTUAL, CONTROL_ROLE_PHASE):
        anchor_kind = ANCHOR_KIND_EPISODE

    marker_typed_refs = _marker_typed_refs(expanded, query_id)
    marker_id = f"ipm-{unit_result.unit_id}"

    uncertainty = (unit_result.not_evaluable_reason
                   if disposition == L1Disposition.NOT_EVALUABLE
                   else unit_result.boundary_reason)
    if _is_proxy_backed(expanded):
        uncertainty = _proxy_backed_uncertainty(uncertainty)

    return (IPRiskMarker(
        marker_id=marker_id, unit_id=unit_result.unit_id,
        risk_identity_id=risk_identity_id,
        subtype=unit_result.positive_subtype,
        audience_label=audience_label, priority=priority,
        anchor_kind=anchor_kind,
        anchor_event_id_or_interval=anchor_event_id_or_interval,
        typed_refs=marker_typed_refs,
        source_locator_ids=tuple(source_ids), query_id=query_id,
        uncertainty=uncertainty,
        risk_family=risk_family, l1_disposition=disposition,
        candidate_or_risk_id=candidate_id, coverage_gap=coverage_gap,
        episode_id=episode_id, stable_core=stable_core,
        lineage_fingerprint=lineage_fingerprint, classifier=classifier,
    ),)


# ---------------------------------------------------------------------------
# Subject-level projection
# ---------------------------------------------------------------------------

# Priority ordering for the overall subject priority (high > medium > low).
_PRIORITY_RANK = {
    MONITORING_PRIORITY_HIGH: 0,
    MONITORING_PRIORITY_MEDIUM: 1,
    MONITORING_PRIORITY_LOW: 2,
    MONITORING_PRIORITY_UNKNOWN: 3,
}


def project_ip_subject_journey(
    slice_result: IPSliceResult,
    *,
    occurrences: Sequence[ExposureOccurrence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
    episodes: Sequence[IPExposureEpisode] = (),
    expansions: Optional[IPExpectedSetExpansion] = None,
) -> "IPSubjectJourneyProjection":
    """Project the view-only IP journey for one subject across all units.

    Builds the typed visit-axis events (from episodes + occurrences +
    actions + accountability rows + medical-trigger evidence), one risk
    marker per positive/boundary/not_evaluable unit, the read-only episode
    rollups, and the deterministic bidirectional join index.  Positive,
    boundary and not_evaluable states coexist; none is collapsed.
    """
    assignments_by_episode = _assignments_by_episode(expansions)
    expanded_by_unit = _expanded_by_unit(expansions)
    risk_family_by_unit: Dict[str, str] = {}
    if expansions is not None:
        for eu in expansions.units:
            unit = eu.build_unit(expansions.project_id)
            risk_family_by_unit[unit.unit_id] = eu.risk_family

    # Episode set: from expansions if available, else explicit episodes.
    episode_map: Dict[str, IPExposureEpisode] = {}
    if expansions is not None:
        for eu in expansions.units:
            episode_map.setdefault(eu.episode.episode_key, eu.episode)
    for ep in episodes:
        episode_map.setdefault(ep.episode_key, ep)

    all_events: List[IPJourneyEvent] = []
    all_markers: List[IPRiskMarker] = []
    event_by_id: Dict[str, IPJourneyEvent] = {}
    best_priority = MONITORING_PRIORITY_UNKNOWN
    uncertainty_parts: List[str] = []

    for episode in episode_map.values():
        assignment = assignments_by_episode.get(episode.episode_key)
        prj_events = project_ip_journey_events(
            None, episode=episode, assignment=assignment,
            expansions=expansions, occurrences=occurrences,
            planned_actions=planned_actions, actual_actions=actual_actions,
            action_evidence=action_evidence, return_records=return_records,
            dispense_records=dispense_records)
        for ev in prj_events:
            if ev.event_id not in event_by_id:
                event_by_id[ev.event_id] = ev
                all_events.append(ev)

    for ur in slice_result.unit_results:
        ep = episode_map.get(_episode_key_for_unit(ur, expansions))
        expanded = expanded_by_unit.get(ur.unit_id)
        mk = project_ip_risk_markers(
            ur, candidates=slice_result.r2_candidates,
            expanded=expanded, episode=ep,
            risk_family_hint=risk_family_by_unit.get(ur.unit_id, ""))
        all_markers.extend(mk)
        rank = _PRIORITY_RANK.get(ur.monitoring_priority, 99)
        if rank < _PRIORITY_RANK.get(best_priority, 99):
            best_priority = ur.monitoring_priority
        for note in (ur.not_evaluable_reason, ur.boundary_reason):
            if note.strip() and note not in uncertainty_parts:
                uncertainty_parts.append(note)

    # Sort events by start for stable ordering.
    all_events.sort(key=lambda e: (not bool(e.start), e.start, e.event_id))
    # Sort markers by unit_id for stable ordering.
    all_markers.sort(key=lambda m: (m.unit_id, m.marker_id))

    rollups: Tuple[Any, ...] = ()
    if expansions is not None:
        rollups = slice_result.episode_rollups(expansions)

    join = bidirectional_join(all_events, all_markers)

    return IPSubjectJourneyProjection(
        subject_ref=slice_result.subject_ref,
        events=tuple(all_events),
        risk_markers=tuple(all_markers),
        episode_rollups=rollups,
        join=join,
        monitoring_priority_code=best_priority,
        monitoring_priority_label=monitoring_priority_audience_label(
            best_priority),
        uncertainty_summary="；".join(uncertainty_parts),
    )


def _episode_key_for_unit(
    unit_result: IPUnitResult,
    expansions: Optional[IPExpectedSetExpansion],
) -> str:
    """Derive the episode key for a unit from its journey marker or
    expansion contribution."""
    if unit_result.journey_markers:
        key = unit_result.journey_markers[0].get("episode_id", "")
        if key:
            return key
    if expansions is not None:
        for eu in expansions.units:
            if eu.build_unit(expansions.project_id).unit_id == unit_result.unit_id:
                return eu.episode.episode_key
    return ""


# ---------------------------------------------------------------------------
# Subject journey projection (view-only rollup)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPSubjectJourneyProjection:
    """View-only journey projection for one subject across IP units.

    Carries the typed IP journey events, risk markers, the read-only
    episode rollups, and the deterministic bidirectional join index.  It
    is projection data, not a rendered UI.
    """

    subject_ref: str
    events: Tuple[IPJourneyEvent, ...]
    risk_markers: Tuple[IPRiskMarker, ...]
    episode_rollups: Tuple[Any, ...]
    join: IPEventMarkerJoin
    monitoring_priority_code: str = MONITORING_PRIORITY_UNKNOWN
    monitoring_priority_label: str = ""
    uncertainty_summary: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "risk_markers", tuple(self.risk_markers))
        object.__setattr__(self, "episode_rollups",
                           tuple(self.episode_rollups))

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def risk_marker_count(self) -> int:
        return sum(1 for m in self.risk_markers if m.is_risk_marker)

    @property
    def coverage_gap_marker_count(self) -> int:
        return sum(1 for m in self.risk_markers if m.coverage_gap)

    def has_positive(self) -> bool:
        return any(m.l1_disposition == L1Disposition.POSITIVE
                   for m in self.risk_markers)

    def has_boundary(self) -> bool:
        return any(m.l1_disposition == L1Disposition.BOUNDARY
                   for m in self.risk_markers)

    def has_not_evaluable(self) -> bool:
        return any(m.l1_disposition == L1Disposition.NOT_EVALUABLE
                   for m in self.risk_markers)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "subject_ref": self.subject_ref,
            "events": [e.canonical_payload() for e in self.events],
            "risk_markers": [m.canonical_payload()
                             for m in self.risk_markers],
            "episode_rollups": [
                {
                    "episode_key": getattr(r, "episode_key"),
                    "child_unit_ids": list(getattr(r, "child_unit_ids")),
                    "has_positive": getattr(r, "has_positive"),
                    "has_boundary": getattr(r, "has_boundary"),
                    "has_not_evaluable": getattr(r, "has_not_evaluable"),
                    "has_negative": getattr(r, "has_negative"),
                    "source_record_count": getattr(r, "source_record_count"),
                }
                for r in self.episode_rollups],
            "join": self.join.canonical_payload(),
            "monitoring_priority_code": self.monitoring_priority_code,
            "monitoring_priority_label": self.monitoring_priority_label,
            "uncertainty_summary": self.uncertainty_summary,
        }
