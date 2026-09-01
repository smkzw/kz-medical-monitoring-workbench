"""R4-D02 CM journey and risk-marker projection (frozen D02 §10).

This module produces **projection payload data** from
:class:`~mm_r4.cm.CMUnitResult` / :class:`~mm_r4.cm.CMSliceResult`
values produced by the D02 CM domain engine (``cm.py``).  It is data,
not an R5 UI (frozen D02 §10: "本切片只提供 projection payload，不宣称
R5 UI 已完成").

Two projection payloads (frozen D02 §10):

* :class:`CMJourneyEvent` -- one CM interval event on the subject medical
  journey, showing drug name, ingredient confirmation status,
  dose/route/frequency, indication, start/end/ongoing and source.
* :class:`CMRiskMarker` -- one risk marker anchored at the CM-interval ×
  rule-window overlap (for prohibited/restricted risks) or at the CM
  interval itself (for medication-rationale risks that hold *because* no
  corresponding AE/MH/diagnosis event exists).

Deterministic bidirectional joins between journey events and risk markers
are verified by stable ids, not by descriptive prose.  A marker never
collapses the simultaneous positive / boundary / not_evaluable states of
sibling units into a single generic marker -- each unit that carries a
candidate or a coverage gap emits its own typed marker with its own
``anchor_kind``, ``risk_family`` and ``monitoring_priority``.

The module reuses the neutral identity accessors from ``contracts`` and
the Chinese audience labels from ``cm`` so the projection stays aligned
with the engine's identity and label decisions.  No production UI,
real project, provider, dictionary, or product service is involved.
"""

from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..risks.cm import (
    CMSliceError,
    CMUnitResult,
    CMEpisodeRollup,
    CMSliceResult,
    CMExpectedSetExpansion,
    CMIntervalDescriptor,
    MedicationEpisode,
    POSITIVE_SUBTYPE_LABELS,
    ProtocolMedicationRule,
)
from ..risks.contracts import (
    CrossDomainEvidenceRef,
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
    "CMJourneyEvent",
    "CMRiskMarker",
    "CMSubjectJourneyProjection",
    "CM_RISK_FAMILY_LABELS",
    "ANCHOR_KIND_OVERLAP",
    "ANCHOR_KIND_INTERVAL",
    "ANCHOR_KIND_UNRESOLVED",
    "project_cm_journey_event",
    "project_cm_risk_markers",
    "project_cm_subject_journey",
    "bidirectional_join",
]


# ---------------------------------------------------------------------------
# Constants and label maps (frozen D02 §9.2, §10)
# ---------------------------------------------------------------------------

#: Anchor kinds for CM risk markers (frozen D02 §10).
ANCHOR_KIND_OVERLAP = "interval_rule_overlap"
ANCHOR_KIND_INTERVAL = "cm_interval"
ANCHOR_KIND_UNRESOLVED = "unresolved_component"

#: CM risk-family engineering code -> Chinese audience label.
#: Frozen D02 §9.2 audience labels are reused for positive subtypes; the
#: rule families and ingredient-resolution family get their own concrete
#: wording.  Engineering codes never appear in the audience label.
CM_RISK_FAMILY_LABELS: Dict[str, str] = {
    "prohibited_medication": "禁用药使用待核实",
    "restricted_medication": "限制用药条件待核实",
    "medication_record_consistency": "用药信息与方案要求不一致",
    "treatment_action_relationship": "用药与处置记录关系待核实",
    "indication_check": "用药依据待核实",
    "ingredient_resolution": "复方成分待确认",
}
#: Fallback Chinese label for an unrecognized risk family.  This is a
#: generic medication-check phrase, never an internal engineering code.
_UNKNOWN_FAMILY_LABEL = "用药信息待核实"


def _risk_family_audience_label(
    risk_family: str, positive_subtype: str, audience_label: str,
) -> str:
    """Resolve the Chinese audience label for a risk marker.

    A positive unit carries the engine's audience label already (one of
    the six frozen §9.2 subtype labels).  A boundary or not_evaluable
    marker that is not positive falls back to the risk-family label so
    the marker shows its concrete risk type without collapsing into a
    generic "risk point".  An unknown risk family must NEVER leak its
    internal engineering code as an audience label; it falls back to a
    natural Chinese phrase (frozen D02 §9.2/§3.9).
    """
    if audience_label.strip():
        return audience_label.strip()
    if positive_subtype.strip() and positive_subtype in POSITIVE_SUBTYPE_LABELS:
        return POSITIVE_SUBTYPE_LABELS[positive_subtype]
    return CM_RISK_FAMILY_LABELS.get(risk_family, _UNKNOWN_FAMILY_LABEL)


def _to_date(s: str) -> Optional[datetime.date]:
    """Parse a full-day ISO date string (YYYY-MM-DD) to a date, or None."""
    if not s:
        return None
    value = s.strip()
    if len(value) != 10:
        return None
    try:
        parsed = datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return parsed if parsed.isoformat() == value else None


def _is_full_day(s: str) -> bool:
    """True when *s* is a parseable full-day ISO date (YYYY-MM-DD)."""
    return _to_date(s) is not None


def _compute_overlap_anchor(
    interval: CMIntervalDescriptor,
    rule: ProtocolMedicationRule,
) -> Tuple[str, str, bool]:
    """Compute the real CM-interval ∩ rule-window overlap anchor.

    Returns ``(anchor_start, anchor_end, fabricated)``.  When all four
    endpoints are full-day dates and deterministically comparable, the
    anchor is the exact intersection of [cm_start, cm_end] and
    [rule.window_start, rule.window_end].  For partial/ambiguous
    endpoints or ongoing intervals without a cutoff, ``fabricated`` is
    True and the anchor falls back to the full CM interval -- this is a
    fail-closed non-fabricated position consistent with the engine
    disposition (the engine would have returned boundary/not_evaluable,
    never a positive on ambiguous endpoints).

    A positive marker only reaches this function when the engine already
    established a deterministic inside-window overlap, so the full-day
    path is the normal case.  The fallback handles boundary/not_evaluable
    markers that still carry an overlap anchor_kind.
    """
    cm_s = interval.cm_start.strip()
    if interval.ongoing:
        cm_end_raw = interval.cutoff.strip()
        if not _is_full_day(cm_end_raw):
            return cm_s, "持续中", True
    else:
        cm_end_raw = interval.cm_end.strip()
    rw_s = (rule.window_start or interval.rule_window_start).strip()
    rw_e = (rule.window_end or interval.rule_window_end).strip()
    # All four endpoints must be full-day dates for exact intersection.
    if not (_is_full_day(cm_s) and _is_full_day(cm_end_raw)
            and _is_full_day(rw_s) and _is_full_day(rw_e)):
        return cm_s, cm_end_raw, True
    cs = _to_date(cm_s)
    ce = _to_date(cm_end_raw)
    rws = _to_date(rw_s)
    rwe = _to_date(rw_e)
    assert cs is not None and ce is not None
    assert rws is not None and rwe is not None
    # Intersection: max(starts), min(ends).
    overlap_start = max(cs, rws)
    overlap_end = min(ce, rwe)
    if overlap_start > overlap_end:
        # No actual overlap (should not happen for a positive engine
        # result, but fail closed defensively).
        return cm_s, cm_end_raw, True
    return overlap_start.isoformat(), overlap_end.isoformat(), False




def _precision_of(interval: CMIntervalDescriptor) -> str:
    """Derive a stable date-precision token for the visit/time axis."""
    try:
        nv = interval.normalized_start()
    except Exception:
        nv = None
    if nv is None or not nv.normalized:
        return "none"
    s = str(nv.normalized)
    parts = s.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if parts and len(parts[0]) == 4:
        return "year"
    return "none"


def _candidate_id_of(unit: CMUnitResult) -> str:
    """Return the primary candidate id from a unit's candidate refs, or ''."""
    for ref in unit.risk_candidate_refs:
        if isinstance(ref, RiskCandidateRef) and ref.candidate_id:
            return ref.candidate_id
    return ""


def _candidate_detail(unit: CMUnitResult, candidates: Sequence[RiskCandidate],
                     ) -> Optional[RiskCandidate]:
    """Return the R2 candidate object matching the unit's primary candidate."""
    cid = _candidate_id_of(unit)
    if not cid:
        return None
    for cand in candidates:
        if cand.candidate_id == cid:
            return cand
    return None


# ---------------------------------------------------------------------------
# CMJourneyEvent (frozen D02 §10 minimum fields)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMJourneyEvent:
    """One CM interval event on the subject medical journey projection.

    Minimum fields (frozen D02 §10):
    ``event_id / domain_track=cm / subject_ref / start / end / ongoing /
    date_precision / episode_id / display_label / source_locator_ids /
    unit_ids``.

    The display label carries the original drug name and ingredient
    confirmation status; dose/route/frequency and indication are
    projection context for drill-back.  ``domain_track`` is always
    ``"cm"`` so CM events use a distinct track/shape from AE/MH/IP.
    """

    event_id: str
    domain_track: str
    subject_ref: str
    start: str
    end: str
    ongoing: bool
    date_precision: str
    episode_id: str
    display_label: str
    source_locator_ids: Tuple[str, ...]
    unit_ids: Tuple[str, ...]
    ingredient_status: str = ""
    dose: str = ""
    dose_unit: str = ""
    route: str = ""
    frequency: str = ""
    indication_text: str = ""
    treatment_role: str = ""
    normalized_name: str = ""
    cross_domain_evidence_ref_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise CMSliceError("CMJourneyEvent.event_id is required")
        if self.domain_track != "cm":
            raise CMSliceError(
                "CMJourneyEvent.domain_track must be 'cm'")
        if not self.subject_ref.strip():
            raise CMSliceError("CMJourneyEvent.subject_ref is required")
        if not self.episode_id.strip():
            raise CMSliceError("CMJourneyEvent.episode_id is required")
        loc = tuple(sorted(set(self.source_locator_ids)))
        if not loc:
            raise CMSliceError(
                "CMJourneyEvent must carry at least one source locator id")
        object.__setattr__(self, "source_locator_ids", loc)
        object.__setattr__(self, "unit_ids", tuple(self.unit_ids))
        object.__setattr__(
            self, "cross_domain_evidence_ref_ids",
            tuple(self.cross_domain_evidence_ref_ids))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "domain_track": self.domain_track,
            "subject_ref": self.subject_ref,
            "start": self.start,
            "end": self.end,
            "ongoing": self.ongoing,
            "date_precision": self.date_precision,
            "episode_id": self.episode_id,
            "display_label": self.display_label,
            "source_locator_ids": list(self.source_locator_ids),
            "unit_ids": list(self.unit_ids),
            "ingredient_status": self.ingredient_status,
            "dose": self.dose,
            "dose_unit": self.dose_unit,
            "route": self.route,
            "frequency": self.frequency,
            "indication_text": self.indication_text,
            "treatment_role": self.treatment_role,
            "normalized_name": self.normalized_name,
            "cross_domain_evidence_ref_ids": list(
                self.cross_domain_evidence_ref_ids),
        }


# ---------------------------------------------------------------------------
# CMRiskMarker (frozen D02 §10 minimum fields)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMRiskMarker:
    """One risk marker anchored on the CM journey.

    Minimum fields (frozen D02 §10):
    ``marker_id / risk_family / audience_label / monitoring_priority /
    anchor_kind / anchor_start / anchor_end / unit_id /
    candidate_or_risk_id / source_locator_ids / rule_locator_ids /
    query_ids / coverage_gap``.

    ``anchor_kind`` distinguishes:

    * ``interval_rule_overlap`` -- the marker sits at the CM interval ×
      rule window overlap (prohibited/restricted risks, §10 line 308).
    * ``cm_interval`` -- the marker sits on the CM interval itself because
      the rationale risk holds *because no corresponding AE/MH/diagnosis
      event was found*; no fake event position is created (§10 line 309).
    * ``unresolved_component`` -- the marker marks an unresolved compound
      component that blocks domain medical completeness.

    ``coverage_gap`` is True for not_evaluable markers so the view can
    surface coverage gaps even when a positive sibling exists.
    """

    marker_id: str
    risk_family: str
    audience_label: str
    monitoring_priority: str
    anchor_kind: str
    anchor_start: str
    anchor_end: str
    unit_id: str
    candidate_or_risk_id: str
    source_locator_ids: Tuple[str, ...]
    rule_locator_ids: Tuple[str, ...]
    query_ids: Tuple[str, ...]
    coverage_gap: bool
    episode_id: str = ""
    l1_disposition: str = ""
    positive_subtype: str = ""
    risk_identity_id: str = ""
    stable_core: str = ""
    lineage_fingerprint: str = ""
    classifier: str = ""
    cross_domain_evidence_ref_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.marker_id, str) or not self.marker_id.strip():
            raise CMSliceError("CMRiskMarker.marker_id is required")
        if not self.risk_family.strip():
            raise CMSliceError("CMRiskMarker.risk_family is required")
        if not self.audience_label.strip():
            raise CMSliceError("CMRiskMarker.audience_label is required")
        if self.monitoring_priority not in (
                MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_MEDIUM,
                MONITORING_PRIORITY_LOW, MONITORING_PRIORITY_UNKNOWN):
            raise CMSliceError(
                f"CMRiskMarker.monitoring_priority="
                f"{self.monitoring_priority!r} invalid")
        if self.anchor_kind not in (ANCHOR_KIND_OVERLAP, ANCHOR_KIND_INTERVAL,
                                    ANCHOR_KIND_UNRESOLVED):
            raise CMSliceError(
                f"CMRiskMarker.anchor_kind={self.anchor_kind!r} invalid")
        if not self.unit_id.strip():
            raise CMSliceError("CMRiskMarker.unit_id is required")
        loc = tuple(sorted(set(self.source_locator_ids)))
        object.__setattr__(self, "source_locator_ids", loc)
        object.__setattr__(self, "rule_locator_ids",
                           tuple(sorted(set(self.rule_locator_ids))))
        object.__setattr__(self, "query_ids",
                           tuple(sorted(set(self.query_ids))))
        object.__setattr__(
            self, "cross_domain_evidence_ref_ids",
            tuple(self.cross_domain_evidence_ref_ids))

    @property
    def is_risk_marker(self) -> bool:
        """A marker is a genuine risk marker when it carries a candidate or
        risk id (positive/boundary).  A pure coverage-gap marker without a
        candidate is a not_evaluable marker, not an established risk."""
        return bool(self.candidate_or_risk_id.strip())

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "marker_id": self.marker_id,
            "risk_family": self.risk_family,
            "audience_label": self.audience_label,
            "monitoring_priority": self.monitoring_priority,
            "anchor_kind": self.anchor_kind,
            "anchor_start": self.anchor_start,
            "anchor_end": self.anchor_end,
            "unit_id": self.unit_id,
            "candidate_or_risk_id": self.candidate_or_risk_id,
            "source_locator_ids": list(self.source_locator_ids),
            "rule_locator_ids": list(self.rule_locator_ids),
            "query_ids": list(self.query_ids),
            "coverage_gap": self.coverage_gap,
            "episode_id": self.episode_id,
            "l1_disposition": self.l1_disposition,
            "positive_subtype": self.positive_subtype,
            "risk_identity_id": self.risk_identity_id,
            "stable_core": self.stable_core,
            "lineage_fingerprint": self.lineage_fingerprint,
            "classifier": self.classifier,
            "cross_domain_evidence_ref_ids": list(
                self.cross_domain_evidence_ref_ids),
        }


# ---------------------------------------------------------------------------
# Subject journey projection (view-only rollup)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMSubjectJourneyProjection:
    """View-only journey projection for one subject across CM units.

    Carries the CM journey events, risk markers, the read-only episode
    rollups, and the bidirectional join index.  It is projection data,
    not a rendered UI.
    """

    subject_ref: str
    events: Tuple[CMJourneyEvent, ...]
    risk_markers: Tuple[CMRiskMarker, ...]
    episode_rollups: Tuple[CMEpisodeRollup, ...]
    join: "CMEventMarkerJoin"
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
                    "episode_id": r.episode_id,
                    "child_unit_ids": list(r.child_unit_ids),
                    "has_positive": r.has_positive,
                    "has_boundary": r.has_boundary,
                    "has_not_evaluable": r.has_not_evaluable,
                    "has_negative": r.has_negative,
                    "source_record_count": r.source_record_count,
                }
                for r in self.episode_rollups],
            "join": self.join.canonical_payload(),
            "monitoring_priority_code": self.monitoring_priority_code,
            "monitoring_priority_label": self.monitoring_priority_label,
            "uncertainty_summary": self.uncertainty_summary,
        }


# ---------------------------------------------------------------------------
# Bidirectional join index (frozen D02 §10: stable-id verified joins)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMEventMarkerJoin:
    """Deterministic bidirectional join between CM journey events and risk
    markers, keyed by ``episode_id`` and ``unit_id``.

    Frozen D02 §10 requires "点击风险可双向到 CM 原始记录、药物身份依据、
    方案条款、关联 AE/MH/诊断和 Query；所有双向 join 用稳定 id 验证，不以
    说明文字代替".  This index provides:

    * ``markers_by_episode`` -- episode_id -> sorted marker ids.
    * ``markers_by_unit`` -- unit_id -> sorted marker ids.
    * ``events_by_episode`` -- episode_id -> sorted event ids.
    * ``event_ids_for_marker`` / ``marker_ids_for_event`` -- the
      bidirectional pairs, joined via episode_id and unit_id.
    """

    markers_by_episode: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    markers_by_unit: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    events_by_episode: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    event_ids_for_marker: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    marker_ids_for_event: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    source_locator_ids_by_marker: Dict[str, Tuple[str, ...]] = field(
        default_factory=dict)
    rule_locator_ids_by_marker: Dict[str, Tuple[str, ...]] = field(
        default_factory=dict)
    query_ids_by_marker: Dict[str, Tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("markers_by_episode", "markers_by_unit",
                     "events_by_episode", "event_ids_for_marker",
                     "marker_ids_for_event", "source_locator_ids_by_marker",
                     "rule_locator_ids_by_marker", "query_ids_by_marker"):
            frozen = {
                k: tuple(sorted(set(v)))
                for k, v in getattr(self, name).items()
            }
            object.__setattr__(self, name, frozen)

    def markers_for_event(self, event_id: str) -> Tuple[str, ...]:
        return self.marker_ids_for_event.get(event_id, ())

    def events_for_marker(self, marker_id: str) -> Tuple[str, ...]:
        return self.event_ids_for_marker.get(marker_id, ())

    def canonical_payload(self) -> Dict[str, Any]:
        def _ser(d: Dict[str, Tuple[str, ...]]) -> Dict[str, List[str]]:
            return {k: list(v) for k, v in sorted(d.items())}
        return {
            "markers_by_episode": _ser(self.markers_by_episode),
            "markers_by_unit": _ser(self.markers_by_unit),
            "events_by_episode": _ser(self.events_by_episode),
            "event_ids_for_marker": _ser(self.event_ids_for_marker),
            "marker_ids_for_event": _ser(self.marker_ids_for_event),
            "source_locator_ids_by_marker": _ser(
                self.source_locator_ids_by_marker),
            "rule_locator_ids_by_marker": _ser(
                self.rule_locator_ids_by_marker),
            "query_ids_by_marker": _ser(self.query_ids_by_marker),
        }


def bidirectional_join(
    events: Sequence[CMJourneyEvent],
    markers: Sequence[CMRiskMarker],
) -> CMEventMarkerJoin:
    """Build the deterministic bidirectional event-marker join index.

    A marker joins to a journey event only when they share the same
    ``episode_id`` **and** the event's ``unit_ids`` contains the marker's
    ``unit_id`` (frozen D02 §10).  Joining by episode alone is
    prohibited: an adversarial marker with the same episode id but a
    mismatched unit id must never link in either direction.  The join is
    by stable ids only; descriptive text is never used as a join key.
    """
    markers_by_episode: Dict[str, List[str]] = {}
    markers_by_unit: Dict[str, List[str]] = {}
    events_by_episode: Dict[str, List[str]] = {}
    event_ids_for_marker: Dict[str, List[str]] = {}
    marker_ids_for_event: Dict[str, List[str]] = {}
    source_locator_ids_by_marker: Dict[str, List[str]] = {}
    rule_locator_ids_by_marker: Dict[str, List[str]] = {}
    query_ids_by_marker: Dict[str, List[str]] = {}

    # Index events by episode_id and by event_id for the dual-key lookup.
    event_by_id: Dict[str, CMJourneyEvent] = {}
    for ev in events:
        events_by_episode.setdefault(ev.episode_id, []).append(ev.event_id)
        event_by_id[ev.event_id] = ev

    for m in markers:
        markers_by_episode.setdefault(m.episode_id, []).append(m.marker_id)
        markers_by_unit.setdefault(m.unit_id, []).append(m.marker_id)
        source_locator_ids_by_marker[m.marker_id] = list(
            m.source_locator_ids)
        rule_locator_ids_by_marker[m.marker_id] = list(m.rule_locator_ids)
        query_ids_by_marker[m.marker_id] = list(m.query_ids)
        # Bidirectional link: marker -> events sharing BOTH its episode_id
        # AND whose unit_ids contains the marker's unit_id.  Episode alone
        # is insufficient (Defect 3).
        candidate_event_ids = events_by_episode.get(m.episode_id, [])
        linked_events: List[str] = []
        for eid in candidate_event_ids:
            ev = event_by_id.get(eid)
            if ev is not None and m.unit_id in ev.unit_ids:
                linked_events.append(eid)
        event_ids_for_marker[m.marker_id] = linked_events
        for eid in linked_events:
            marker_ids_for_event.setdefault(eid, []).append(m.marker_id)

    return CMEventMarkerJoin(
        markers_by_episode=markers_by_episode,
        markers_by_unit=markers_by_unit,
        events_by_episode=events_by_episode,
        event_ids_for_marker=event_ids_for_marker,
        marker_ids_for_event=marker_ids_for_event,
        source_locator_ids_by_marker=source_locator_ids_by_marker,
        rule_locator_ids_by_marker=rule_locator_ids_by_marker,
        query_ids_by_marker=query_ids_by_marker,
    )


# ---------------------------------------------------------------------------
# Per-unit projection (read-only views over CMUnitResult)
# ---------------------------------------------------------------------------

def _episode_lookup(
    expansions: Optional[CMExpectedSetExpansion],
) -> Dict[str, MedicationEpisode]:
    """Map unit_id -> episode for source-drill-back context."""
    if expansions is None:
        return {}
    out: Dict[str, MedicationEpisode] = {}
    for eu in expansions.units:
        unit = eu.build_unit(expansions.project_id, expansions.strategy)
        out[unit.unit_id] = eu.episode
    return out


def project_cm_journey_event(
    unit_result: CMUnitResult,
    *,
    episode: Optional[MedicationEpisode] = None,
) -> Optional[CMJourneyEvent]:
    """Project one CM journey interval event from a unit result.

    Returns None when the unit result has no episode context (no
    ``journey_markers`` and no episode supplied).  A unit with markers
    always has episode context because ``cm.py`` attaches a journey marker
    to every positive/boundary unit; not_evaluable ingredient-resolution
    and coverage-gap units are projected as journey events too so the
    view shows the CM interval with its coverage gap.
    """
    markers = unit_result.journey_markers
    # Source locator ids: prefer the journey marker source locator, fall
    # back to the unit's source record refs.
    marker = markers[0] if markers else None
    source_ids: List[str] = []
    if marker is not None:
        sid = marker.get("source_locator_id", "")
        if sid:
            source_ids.append(sid)
    if not source_ids:
        for sref in unit_result.source_record_refs:
            source_ids.append(sref.locator.locator_id())
    if not source_ids:
        return None

    interval: Optional[CMIntervalDescriptor] = None
    binding_name = ""
    normalized_name = ""
    ingredient_status = ""
    dose = ""
    dose_unit = ""
    route = ""
    frequency = ""
    indication_text = ""
    treatment_role = ""
    if episode is not None:
        interval = episode.interval
        binding_name = episode.identity_binding.original_name
        normalized_name = episode.identity_binding.normalized_name
        if episode.identity_binding.has_unresolved:
            ingredient_status = "unresolved"
        elif episode.identity_binding.confirmed_ingredients:
            ingredient_status = "confirmed"
        dose = episode.dose
        dose_unit = episode.dose_unit
        route = episode.route
        frequency = episode.frequency
        indication_text = episode.indication_text
        treatment_role = episode.treatment_role
    elif marker is not None:
        # Fall back to marker display fields.
        binding_name = marker.get("display_label", "")
        start = marker.get("start", "")
        end = marker.get("end", "")
        ongoing = bool(marker.get("ongoing", False))
        interval = CMIntervalDescriptor(
            cm_start=start, cm_end=end, ongoing=ongoing)

    if interval is None:
        return None

    display_label = binding_name or marker.get("display_label", "") if marker else binding_name
    episode_id = (marker.get("episode_id", "") if marker else
                  (episode.episode_id if episode else ""))
    if not episode_id:
        return None

    cer_ids = tuple(
        ref.evidence_ref_id for ref in unit_result.cross_domain_evidence_refs
        if isinstance(ref, CrossDomainEvidenceRef))

    return CMJourneyEvent(
        event_id=episode_id,
        domain_track="cm",
        subject_ref=unit_result.subject_ref,
        start=interval.cm_start,
        end=("持续中" if interval.ongoing else interval.cm_end),
        ongoing=interval.ongoing,
        date_precision=_precision_of(interval),
        episode_id=episode_id,
        display_label=display_label,
        source_locator_ids=tuple(source_ids),
        unit_ids=(unit_result.unit_id,),
        ingredient_status=ingredient_status,
        dose=dose,
        dose_unit=dose_unit,
        route=route,
        frequency=frequency,
        indication_text=indication_text,
        treatment_role=treatment_role,
        normalized_name=normalized_name,
        cross_domain_evidence_ref_ids=cer_ids,
    )


def project_cm_risk_markers(
    unit_result: CMUnitResult,
    *,
    candidates: Sequence[RiskCandidate] = (),
    rules_by_unit: Optional[Mapping[str, ProtocolMedicationRule]] = None,
    episode: Optional[MedicationEpisode] = None,
    risk_family_hint: str = "",
) -> Tuple[CMRiskMarker, ...]:
    """Project risk markers for one unit result.

    A positive or boundary unit produces one risk marker carrying its
    candidate id, rule/identity/query drill-back and the appropriate
    anchor kind.  A not_evaluable unit produces a coverage-gap marker
    (no candidate) so the view surfaces the gap without inventing a risk.
    A negative or not_applicable unit produces no marker.

    ``risk_family_hint`` carries the expanded unit's risk family (from
    ``CMUnitExpanded.risk_family``) so ingredient-resolution and other
    families are correctly typed even when the engine attaches no journey
    marker to a not_evaluable unit.

    Simultaneous positive / boundary / not_evaluable states are never
    collapsed: each unit emits its own marker with its own typed
    ``risk_family``, ``audience_label`` and ``l1_disposition``.
    """
    disposition = unit_result.l1_disposition
    if disposition in (L1Disposition.NEGATIVE, L1Disposition.NOT_APPLICABLE):
        return ()

    markers: List[CMRiskMarker] = []
    marker_base = unit_result.journey_markers[0] if unit_result.journey_markers else None

    risk_family = ""
    if marker_base is not None:
        risk_family = marker_base.get("risk_family", "")
    if not risk_family:
        risk_family = risk_family_hint or "indication_check"

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
    # Defect 2: whenever the episode is available, guarantee medication-
    # identity drill-back by including the CM source locator, the
    # identity-binding evidence locator, and the distinct indication
    # locator (frozen D02 §10: one-click to CM source, identity evidence,
    # rule clause, related AE/MH/diagnosis and Query).
    if episode is not None:
        source_ids.append(episode.source_locator.locator_id())
        source_ids.append(
            episode.identity_binding.evidence_locator.locator_id())
        if episode.indication_source_locator is not None:
            source_ids.append(
                episode.indication_source_locator.locator_id())
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

    # Rule drill-back.
    rule_locator_ids: List[str] = []
    rule = rules_by_unit.get(unit_result.unit_id) if rules_by_unit else None
    if rule is not None:
        rule_locator_ids.append(rule.clause_locator)
    # Query ids.
    query_ids = [q.query_id for q in unit_result.query_refs
                 if isinstance(q, QueryDraftRef)]

    # Cross-domain evidence ref ids (D01 drill-back).
    cer_ids = tuple(
        ref.evidence_ref_id for ref in unit_result.cross_domain_evidence_refs
        if isinstance(ref, CrossDomainEvidenceRef))
    # Anchor kind + interval resolution.
    anchor_kind = ANCHOR_KIND_INTERVAL
    anchor_start = ""
    anchor_end = ""
    interval: Optional[CMIntervalDescriptor] = None
    if episode is not None:
        interval = episode.interval
        anchor_start = interval.cm_start
        anchor_end = ("持续中" if interval.ongoing else interval.cm_end)
    elif marker_base is not None:
        anchor_start = marker_base.get("start", "")
        anchor_end = marker_base.get("end", "")
        ongoing = bool(marker_base.get("ongoing", False))
        interval = CMIntervalDescriptor(
            cm_start=anchor_start,
            cm_end="" if ongoing else anchor_end,
            ongoing=ongoing)

    if risk_family in ("prohibited_medication", "restricted_medication"):
        anchor_kind = ANCHOR_KIND_OVERLAP
        # Defect 1: compute the real CM-interval ∩ rule-window overlap
        # when full-day endpoints are deterministically comparable; fail
        # closed (full CM interval) for partial/ambiguous endpoints.
        if rule is not None and interval is not None:
            anchor_start, anchor_end, _fabricated = _compute_overlap_anchor(
                interval, rule)
    elif risk_family == "ingredient_resolution":
        anchor_kind = ANCHOR_KIND_UNRESOLVED
    else:
        # indication_check rationale risk: §10 line 309 -- do NOT fabricate
        # an event position; anchor on the CM interval and mark that no
        # corresponding AE/MH/diagnosis record was found.
        anchor_kind = ANCHOR_KIND_INTERVAL

    audience_label = _risk_family_audience_label(
        risk_family, unit_result.positive_subtype,
        unit_result.audience_label)
    priority = unit_result.monitoring_priority

    coverage_gap = disposition == L1Disposition.NOT_EVALUABLE

    episode_id = ""
    if episode is not None:
        episode_id = episode.episode_id
    elif marker_base is not None:
        episode_id = marker_base.get("episode_id", "")

    marker_id = f"cmm-{unit_result.unit_id}"

    markers.append(CMRiskMarker(
        marker_id=marker_id,
        risk_family=risk_family,
        audience_label=audience_label,
        monitoring_priority=priority,
        anchor_kind=anchor_kind,
        anchor_start=anchor_start,
        anchor_end=anchor_end,
        unit_id=unit_result.unit_id,
        candidate_or_risk_id=candidate_id,
        source_locator_ids=tuple(source_ids),
        rule_locator_ids=tuple(rule_locator_ids),
        query_ids=tuple(query_ids),
        coverage_gap=coverage_gap,
        episode_id=episode_id,
        l1_disposition=disposition,
        positive_subtype=unit_result.positive_subtype,
        risk_identity_id=risk_identity_id,
        stable_core=stable_core,
        lineage_fingerprint=lineage_fingerprint,
        classifier=classifier,
        cross_domain_evidence_ref_ids=cer_ids,
    ))
    return tuple(markers)


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


def project_cm_subject_journey(
    slice_result: CMSliceResult,
    *,
    expansions: Optional[CMExpectedSetExpansion] = None,
    rules: Sequence[ProtocolMedicationRule] = (),
) -> CMSubjectJourneyProjection:
    """Project the view-only CM journey for one subject across all units.

    Builds one journey event per episode (deduplicated), one risk marker
    per positive/boundary/not_evaluable unit, the read-only episode
    rollups, and the deterministic bidirectional join index.  Positive,
    boundary and not_evaluable states coexist; none is collapsed.
    """
    episode_by_unit = _episode_lookup(expansions)
    # Build a unit_id -> rule map from expansions when available so rule
    # clause locators are available for drill-back without re-deriving the
    # rule assignment.
    rules_by_unit: Dict[str, ProtocolMedicationRule] = {}
    risk_family_by_unit: Dict[str, str] = {}
    if expansions is not None:
        for eu in expansions.units:
            unit = eu.build_unit(expansions.project_id,
                                 expansions.strategy)
            if eu.rule is not None:
                rules_by_unit[unit.unit_id] = eu.rule
            risk_family_by_unit[unit.unit_id] = eu.risk_family
    for r in rules:
        # Rules supplied directly are indexed by their clause locator for
        # tests that pass rules without expansions; unit-level resolution
        # via expansions takes precedence.
        rules_by_unit.setdefault(r.clause_locator, r)

    all_events: List[CMJourneyEvent] = []
    all_markers: List[CMRiskMarker] = []
    events_by_episode: Dict[str, CMJourneyEvent] = {}
    best_priority = MONITORING_PRIORITY_UNKNOWN
    uncertainty_parts: List[str] = []

    for ur in slice_result.unit_results:
        ep = episode_by_unit.get(ur.unit_id)
        ev = project_cm_journey_event(ur, episode=ep)
        if ev is not None:
            if ev.episode_id not in events_by_episode:
                events_by_episode[ev.episode_id] = ev
                all_events.append(ev)
            else:
                # Merge unit_ids into the existing episode event.
                base = events_by_episode[ev.episode_id]
                merged_units = tuple(sorted(set(base.unit_ids + ev.unit_ids)))
                merged = CMJourneyEvent(
                    event_id=base.event_id,
                    domain_track=base.domain_track,
                    subject_ref=base.subject_ref,
                    start=base.start,
                    end=base.end,
                    ongoing=base.ongoing,
                    date_precision=base.date_precision,
                    episode_id=base.episode_id,
                    display_label=base.display_label,
                    source_locator_ids=tuple(sorted(set(
                        base.source_locator_ids + ev.source_locator_ids))),
                    unit_ids=merged_units,
                    ingredient_status=base.ingredient_status,
                    dose=base.dose,
                    dose_unit=base.dose_unit,
                    route=base.route,
                    frequency=base.frequency,
                    indication_text=base.indication_text,
                    treatment_role=base.treatment_role,
                    normalized_name=base.normalized_name,
                    cross_domain_evidence_ref_ids=tuple(sorted(set(
                        base.cross_domain_evidence_ref_ids
                        + ev.cross_domain_evidence_ref_ids))),
                )
                events_by_episode[base.episode_id] = merged
                # Replace in all_events list.
                for i, e in enumerate(all_events):
                    if e.episode_id == base.episode_id:
                        all_events[i] = merged
                        break

        unit_rules = {ur.unit_id: rules_by_unit.get(ur.unit_id)} if (
            ur.unit_id in rules_by_unit) else None
        mk = project_cm_risk_markers(
            ur, candidates=slice_result.r2_candidates,
            rules_by_unit=unit_rules, episode=ep,
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

    rollups: Tuple[CMEpisodeRollup, ...] = ()
    if expansions is not None:
        rollups = slice_result.episode_rollups(expansions)

    join = bidirectional_join(all_events, all_markers)

    return CMSubjectJourneyProjection(
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
