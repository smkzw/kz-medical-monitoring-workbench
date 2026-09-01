"""R4-D05 Patient Journey projection (renderer-neutral, worker_03).

Produces :class:`~mm_r4.visit_schedule.VisitJourneyProjection` from a
full :class:`~mm_r4.visit_schedule_evaluator.D05EvaluationOutcome`.

This is **projection data, not an R5 UI and not a chart library**
(frozen D05 §10: "D05 提供 renderer-neutral 的 VisitJourneyProjection，
不声称 R5 UI 已完成").  Shapes, domain short labels and text carry the
meaning; the payload is representable independently of color.

Contract §10 constraints enforced here:

* planned-visit markers and actual-encounter markers are separate objects
  joined by stable assignment edges -- never a single "已记录事项";
* AE / MH / CM / IP给药 / 检验·检查 / 住院·操作 / 症状·疗效 / 方案符合性
  keep their own domain lanes (``domain_code`` + Chinese short label +
  renderer-neutral shape/line semantics), never collapsed into one track;
* actual dates and raw/actual visit semantics are preserved; missing,
  conflicting or partial dates and pending assignment go to a pending area;
  cutoff-later records go to a separate out-of-cutoff area; a time point is
  never fabricated and a risk is never inferred from the display;
* risk markers bind stable unit / candidate-or-risk / query / source
  locators and preserve supporting / counterevidence / coverage-gap
  semantics;
* every stable join uses content-addressed ids, never same-date / text /
  visit-name substitution;
* audience payload QC rejects internal/log labels (``positive``,
  ``candidate``, ``正式事实``, ``候选信号``, ``只读``, ``规则引擎``,
  ``后端``, ``模型置信度``, ``已记录事项``, ``通用风险点``).

All data is synthetic/offline.  No real project, provider, dictionary or
product service; port 8911 is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple
from warnings import warn

from .contracts import L1Disposition, content_hash
from . import visit_schedule as vs
from . import visit_schedule_evaluator as vse


__all__ = [
    "DOMAIN_TRACKS",
    "DOMAIN_TRACK_LABELS",
    "ACTIVITY_KIND_LABELS",
    "PENDING_CONTEXT_TYPES",
    "OUT_OF_CUTOFF_OBJECT_TYPES",
    "FORBIDDEN_AUDIENCE_TOKENS",
    "VisitActivityMarker",
    "PendingContextMarker",
    "OutOfCutoffContextMarker",
    "RiskOverlapCluster",
    "project_visit_schedule_journey",
    "audience_payload_clean",
    "query_draft_parts_complete",
    "cluster_overlapping_risks",
    "brush_journey_display",
    "center_risk_join_qc",
    "reject_copied_center_risks",
    "reject_visitnum_as_time_order",
    "reject_collapsed_planned_actual",
]


# ---------------------------------------------------------------------------
# Audience domain tracks (§10: differentiated lanes, Chinese labels, and
# renderer-neutral shape/line semantics independent of color)
# ---------------------------------------------------------------------------

#: ``domain_code`` -> (Chinese short label, renderer-neutral line/shape
#: semantics token).  The ``shape_encoding`` is a color-independent
#: representation semantic (e.g. a line style or marker glyph base) that a
#: renderer may map to a visible encoding; it never relies on hue alone.
DOMAIN_TRACKS: Dict[str, Tuple[str, str]] = {
    "ae": ("AE·不良事件", "line-dashed"),
    "mh": ("MH·既往病史", "line-dotted"),
    "cm": ("CM·合并用药", "line-solid"),
    "ip": ("IP给药", "line-dashdot"),
    "lab": ("检验·检查", "glyph-triangle"),
    "proc": ("住院·操作", "glyph-square"),
    "sym": ("症状·疗效", "glyph-circle"),
    "comp": ("方案符合性", "glyph-diamond"),
}

DOMAIN_TRACK_LABELS: Dict[str, str] = {
    code: label for code, (label, _shape) in DOMAIN_TRACKS.items()}

#: activity_kind -> Chinese short label suffix.
ACTIVITY_KIND_LABELS: Dict[str, str] = {
    "assessment": "评估",
    "sample": "样本",
    "procedure": "操作",
    "contact": "联系",
}

#: Closed set of pending-context marker types.
PENDING_CONTEXT_TYPES: Tuple[str, ...] = (
    "missing_date", "partial_date", "conflicting_date",
    "pending_assignment",
)

#: Closed set of out-of-cutoff object types.
OUT_OF_CUTOFF_OBJECT_TYPES: Tuple[str, ...] = ("encounter", "activity")

#: Audience payload forbidden tokens (frozen §9.2 / §10: internal and log
#: vocabulary must never leak to the audience payload).
FORBIDDEN_AUDIENCE_TOKENS: Tuple[str, ...] = (
    "positive", "candidate", "formal fact",
    "正式事实", "候选信号", "只读", "规则引擎", "后端", "模型置信度",
    "已记录事项", "通用风险点",
)


def _domain_track(clinical_domain: str, activity_kind: str) -> str:
    """Map a clinical domain + activity kind to a closed-domain-code label.

    Recognised clinical domains map to the frozen lane vocabulary; any
    other domain is surfaced as ``comp`` (方案符合性) with a concrete
    Chinese suffix so no lane is ever invented and no engineering code
    leaks (§10: "不把任何固定疾病/复合/终点/项目/访视/表/字段写入内核").
    """
    suffix = ACTIVITY_KIND_LABELS.get(activity_kind, "")
    if clinical_domain in DOMAIN_TRACK_LABELS:
        base = DOMAIN_TRACK_LABELS[clinical_domain]
        return f"{base}·{suffix}" if suffix else base
    base = DOMAIN_TRACK_LABELS["comp"]
    if suffix:
        return f"{base}·{suffix}"
    return base


def audience_payload_clean(text: str) -> bool:
    """True when ``text`` carries no forbidden internal/log token."""
    lowered = text.lower()
    return not any(tok in lowered for tok in FORBIDDEN_AUDIENCE_TOKENS)


def query_draft_parts_complete(basis: str, finding: str, action: str) -> bool:
    """Challenge 87: a Query draft is complete only when all three Chinese
    parts are present and none leaks an internal token.  Incomplete drafts
    must not be emitted."""
    if not (basis.startswith("依据：") and finding.startswith("发现：")
            and action.startswith("行动项：")):
        return False
    return all(audience_payload_clean(part)
               for part in (basis, finding, action))


# ---------------------------------------------------------------------------
# New worker_03 marker value objects (immutable, content-addressed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VisitActivityMarker:
    """One activity on a differentiated domain lane of the shared visit
    axis (§10).

    ``domain_code`` is a closed lane code (ae/mh/cm/ip/lab/proc/sym/comp);
    ``audience_name`` is a concrete Chinese short label; ``shape_encoding``
    is a renderer-neutral color-independent representation semantic;
    ``source_locator_ids`` link the planned activity to its plan rows.
    """

    marker_id: str
    planned_activity_id: str
    planned_activity_key: str
    planned_visit_key: str
    domain_code: str
    domain_label: str
    shape_encoding: str
    audience_name: str
    status_hint: str
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        vs._validate_nonempty(
            self.planned_activity_id, "VisitActivityMarker.planned_activity_id")
        vs._validate_nonempty(
            self.planned_activity_key,
            "VisitActivityMarker.planned_activity_key")
        vs._validate_nonempty(
            self.planned_visit_key, "VisitActivityMarker.planned_visit_key")
        if self.domain_code not in DOMAIN_TRACKS:
            raise vs.ScheduleSliceError(
                f"VisitActivityMarker.domain_code {self.domain_code!r} "
                f"is not a closed lane code")
        vs._validate_nonempty(
            self.domain_label, "VisitActivityMarker.domain_label")
        vs._validate_nonempty(
            self.shape_encoding, "VisitActivityMarker.shape_encoding")
        vs._validate_nonempty(
            self.audience_name, "VisitActivityMarker.audience_name")
        vs._require_member(
            self.status_hint, vs.MARKER_STATUS_HINTS,
            "VisitActivityMarker.status_hint")
        if not audience_payload_clean(self.audience_name):
            raise vs.ScheduleSliceError(
                f"VisitActivityMarker audience label leaks an internal "
                f"token: {self.audience_name!r}")
        object.__setattr__(
            self, "source_locator_ids",
            vs._canonical_sorted(self.source_locator_ids))
        computed = "d05-avm-" + content_hash({
            "planned_activity_id": self.planned_activity_id,
            "planned_activity_key": self.planned_activity_key,
            "planned_visit_key": self.planned_visit_key,
            "domain_code": self.domain_code,
            "domain_label": self.domain_label,
            "shape_encoding": self.shape_encoding,
            "audience_name": self.audience_name,
            "status_hint": self.status_hint,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.marker_id and self.marker_id != computed:
            raise vs.ScheduleSliceError(
                f"VisitActivityMarker.marker_id {self.marker_id!r} does "
                f"not match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


@dataclass(frozen=True)
class PendingContextMarker:
    """A marker in the pending area of the journey axis (§10).

    Carries missing / partial / conflicting dates or a pending assignment;
    never a fabricated time point.  ``context_type`` is the closed set
    ``PENDING_CONTEXT_TYPES``.
    """

    marker_id: str
    context_type: str
    subject_ref: str
    reference_role: str           # "visit" | "activity" | "encounter"
    reference_key: str
    exhibit_label: str = ""
    reason: str = ""
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.context_type not in PENDING_CONTEXT_TYPES:
            raise vs.ScheduleSliceError(
                f"PendingContextMarker.context_type "
                f"{self.context_type!r} is not closed")
        vs._validate_nonempty(
            self.subject_ref, "PendingContextMarker.subject_ref")
        vs._validate_nonempty(
            self.reference_role, "PendingContextMarker.reference_role")
        vs._validate_nonempty(
            self.reference_key, "PendingContextMarker.reference_key")
        vs._validate_optional_str(
            self.exhibit_label, "PendingContextMarker.exhibit_label")
        vs._validate_optional_str(
            self.reason, "PendingContextMarker.reason")
        object.__setattr__(
            self, "source_locator_ids",
            vs._canonical_sorted(self.source_locator_ids))
        computed = "d05-pending-" + content_hash({
            "context_type": self.context_type,
            "subject_ref": self.subject_ref,
            "reference_role": self.reference_role,
            "reference_key": self.reference_key,
            "exhibit_label": self.exhibit_label,
            "reason": self.reason,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.marker_id and self.marker_id != computed:
            raise vs.ScheduleSliceError(
                f"PendingContextMarker.marker_id {self.marker_id!r} does "
                f"not match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


@dataclass(frozen=True)
class OutOfCutoffContextMarker:
    """A marker in the out-of-cutoff context area of the journey axis
    (§10).

    Cutoff-later records appear here only and never participate in the
    current-run expected-set / assignment / L1 / L2 / L3.
    """

    marker_id: str
    object_type: str              # "encounter" | "activity"
    object_id: str
    subject_ref: str
    recorded_start: str = ""
    recorded_end: str = ""
    date_precision: str = vs.PRECISION_UNKNOWN
    reason: str = ""
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.object_type not in OUT_OF_CUTOFF_OBJECT_TYPES:
            raise vs.ScheduleSliceError(
                f"OutOfCutoffContextMarker.object_type "
                f"{self.object_type!r} is not closed")
        vs._validate_nonempty(
            self.object_id, "OutOfCutoffContextMarker.object_id")
        vs._validate_nonempty(
            self.subject_ref, "OutOfCutoffContextMarker.subject_ref")
        vs._validate_optional_str(
            self.recorded_start, "OutOfCutoffContextMarker.recorded_start")
        vs._validate_optional_str(
            self.recorded_end, "OutOfCutoffContextMarker.recorded_end")
        vs._require_member(
            self.date_precision, vs.PRECISIONS,
            "OutOfCutoffContextMarker.date_precision")
        vs._validate_optional_str(
            self.reason, "OutOfCutoffContextMarker.reason")
        object.__setattr__(
            self, "source_locator_ids",
            vs._canonical_sorted(self.source_locator_ids))
        computed = "d05-ooc-" + content_hash({
            "object_type": self.object_type,
            "object_id": self.object_id,
            "subject_ref": self.subject_ref,
            "recorded_start": self.recorded_start,
            "recorded_end": self.recorded_end,
            "date_precision": self.date_precision,
            "reason": self.reason,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.marker_id and self.marker_id != computed:
            raise vs.ScheduleSliceError(
                f"OutOfCutoffContextMarker.marker_id {self.marker_id!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


# ---------------------------------------------------------------------------
# Marker builders (deterministic canonical order)
# ---------------------------------------------------------------------------

def _visit_results_by_key(
    unit_results: Sequence[vse.D05UnitResult],
) -> Dict[str, List[vse.D05UnitResult]]:
    out: Dict[str, List[vse.D05UnitResult]] = {}
    for r in unit_results:
        if r.planned_visit_key:
            out.setdefault(r.planned_visit_key, []).append(r)
    return out


def _activity_results_by_key(
    unit_results: Sequence[vse.D05UnitResult],
) -> Dict[str, List[vse.D05UnitResult]]:
    out: Dict[str, List[vse.D05UnitResult]] = {}
    for r in unit_results:
        if r.planned_activity_key:
            out.setdefault(r.planned_activity_key, []).append(r)
    return out


def _build_planned_visit_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
    planned_visits: Sequence[vs.PlannedVisitDefinition],
) -> Tuple[vs.PlannedVisitMarker, ...]:
    """One PlannedVisitMarker per planned visit that has an evaluation unit
    (matured, future or not_applicable) in the expected set."""
    expected_visit_keys: Set[str] = set()
    for unit in outcome.expected_units:
        if unit.planned_visit_key:
            expected_visit_keys.add(unit.planned_visit_key)
    results_by_key = _visit_results_by_key(outcome.unit_results)
    anchor_day_map = dict(outcome.anchor_day_by_visit_key)
    future_keys = set(outcome.future_obligation_keys)
    # Challenges 4/5/95: future / still-open visits stay visible on the
    # plan axis even though they are excluded from the medical expected-set.
    keys_to_show = expected_visit_keys | future_keys

    markers: List[vs.PlannedVisitMarker] = []
    for visit in planned_visits:
        if visit.planned_visit_key not in keys_to_show:
            continue
        anchor_day = anchor_day_map.get(visit.planned_visit_key, "")
        window_start = ""
        window_end = ""
        if anchor_day and visit.window_rule:
            try:
                wb = vse.window_bounds(
                    window_rule=visit.window_rule, anchor_day=anchor_day)
                if getattr(wb, "determinable", False):
                    window_start = wb.lo_day
                    window_end = wb.hi_day
            except Exception as exc:  # pragma: no cover - defensive
                warn(f"window_bounds failed for {visit.planned_visit_key}: "
                     f"{exc}", RuntimeWarning, stacklevel=2)
        results = results_by_key.get(visit.planned_visit_key, [])
        if visit.planned_visit_key in future_keys:
            status = vs.STATUS_UPCOMING
        elif results:
            status = vs.STATUS_EVALUATED
        else:
            status = vs.STATUS_DUE
        markers.append(vs.PlannedVisitMarker(
            marker_id="",
            planned_visit_id=visit.planned_visit_id,
            audience_name=visit.audience_visit_name,
            phase=visit.phase,
            nominal_anchor=anchor_day,
            window_start=window_start,
            window_end=window_end,
            date_precision=(
                visit.window_rule.date_precision
                if visit.window_rule else vs.PRECISION_UNKNOWN),
            status_hint=status,
            source_locator_ids=tuple(visit.source_locator_ids),
        ))
    # Deterministic canonical order: by window start then planned id.
    markers.sort(key=lambda m: (m.window_start or "z", m.planned_visit_id))
    return tuple(markers)


def _build_actual_encounter_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
    encounters: Sequence[vs.ActualEncounterRecord],
    bundles: Sequence[vs.ActualEncounterBundle],
    scope_decisions: Sequence[vs.ActualRecordScopeDecision],
    planned_visits: Sequence[vs.PlannedVisitDefinition],
) -> Tuple[vs.ActualEncounterMarker, ...]:
    """One ActualEncounterMarker per in-scope encounter, preserving the
    actual dates and raw/actual visit semantics.  Missing/partial dates map
    to ``pending_time``/``partial`` anchors; out-of-cutoff encounters are
    excluded here (they live in the out-of-cutoff area) and reported via
    :func:`_build_out_of_cutoff_markers`."""
    encounter_to_bundle: Dict[str, str] = {}
    for b in bundles:
        for mid in b.member_encounter_ids:
            encounter_to_bundle[mid] = b.bundle_id

    assignment_by_bundle: Dict[str, vs.VisitAssignmentDecision] = {}
    for a in outcome.visit_assignments:
        if a.decision_status == vs.VISIT_ASSIGNMENT_UNIQUE:
            assignment_by_bundle[a.actual_bundle_id] = a

    scope_by_object: Dict[str, vs.ActualRecordScopeDecision] = {}
    for d in scope_decisions:
        scope_by_object[d.actual_object_id] = d

    visit_by_id = {v.planned_visit_id: v for v in planned_visits}
    out_of_cutoff_ids = set(outcome.out_of_cutoff_object_ids)

    markers: List[vs.ActualEncounterMarker] = []
    for enc in encounters:
        if enc.encounter_id in out_of_cutoff_ids:
            continue  # out-of-cutoff area only
        bundle_id = encounter_to_bundle.get(enc.encounter_id, "")
        assignment = assignment_by_bundle.get(bundle_id)

        anchor_state = vs.ANCHOR_STATE_DATED
        if not enc.start or enc.start == "0001-01-01":
            anchor_state = vs.ANCHOR_STATE_PENDING_TIME
        elif enc.date_precision in (vs.PRECISION_MONTH, vs.PRECISION_YEAR):
            anchor_state = vs.ANCHOR_STATE_PARTIAL

        assignment_id = ""
        audience_name = ""
        if assignment:
            assignment_id = assignment.assignment_id
            visit = visit_by_id.get(assignment.selected_planned_visit_id)
            if visit:
                audience_name = visit.audience_visit_name

        markers.append(vs.ActualEncounterMarker(
            marker_id="",
            encounter_id=enc.encounter_id,
            encounter_kind=enc.encounter_kind,
            anchor_state=anchor_state,
            start=enc.start,
            end=enc.end,
            date_precision=enc.date_precision,
            assignment_id=assignment_id,
            audience_name=audience_name,
            source_locator_ids=tuple(enc.source_locator_ids),
        ))
    markers.sort(key=lambda m: (m.start or "z", m.encounter_id))
    return tuple(markers)


def _build_activity_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
    planned_activities: Sequence[vs.PlannedActivityDefinition],
    planned_visits: Sequence[vs.PlannedVisitDefinition],
) -> Tuple[VisitActivityMarker, ...]:
    """One VisitActivityMarker per planned activity in the expected set,
    on a differentiated domain lane.

    Each marker's ``planned_visit_key`` is the owning planned visit's
    cross-revision stable *logical* key (frozen §3.1: versioned definition
    ids live in lineage, never in the stable identity core).  The
    versioned ``PlannedActivityDefinition.planned_visit_id`` is resolved
    to its ``PlannedVisitDefinition.planned_visit_key``; an activity that
    references a visit id with no owning definition fails closed rather
    than writing a versioned id into a stable-key field.
    """
    visit_key_by_id = {v.planned_visit_id: v.planned_visit_key
                       for v in planned_visits}
    expected_activity_keys: Set[str] = set()
    for unit in outcome.expected_units:
        if unit.planned_activity_key:
            expected_activity_keys.add(unit.planned_activity_key)
    results_by_key = _activity_results_by_key(outcome.unit_results)

    markers: List[VisitActivityMarker] = []
    for activity in planned_activities:
        if activity.planned_activity_key not in expected_activity_keys:
            continue
        visit_key = visit_key_by_id.get(activity.planned_visit_id)
        if not visit_key:
            raise vs.ScheduleSliceError(
                f"planned activity {activity.planned_activity_id!r} "
                f"references planned visit id "
                f"{activity.planned_visit_id!r} that cannot be resolved "
                f"to a stable planned_visit_key")
        domain_code = activity.clinical_domain
        if domain_code not in DOMAIN_TRACKS:
            domain_code = "comp"
        domain_label, shape_encoding = DOMAIN_TRACKS[domain_code]
        suffix = ACTIVITY_KIND_LABELS.get(activity.activity_kind, "")
        track_label = f"{domain_label}·{suffix}" if suffix else domain_label
        results = results_by_key.get(activity.planned_activity_key, [])
        status = vs.STATUS_EVALUATED if results else vs.STATUS_DUE
        markers.append(VisitActivityMarker(
            marker_id="",
            planned_activity_id=activity.planned_activity_id,
            planned_activity_key=activity.planned_activity_key,
            planned_visit_key=visit_key,
            domain_code=domain_code,
            domain_label=track_label,
            shape_encoding=shape_encoding,
            audience_name=activity.audience_name,
            status_hint=status,
            source_locator_ids=tuple(activity.source_locator_ids),
        ))
    markers.sort(key=lambda m: (m.domain_code, m.planned_activity_key))
    return tuple(markers)


def _build_assignment_edges(
    outcome: vse.D05EvaluationOutcome,
    planned_visits: Sequence[vs.PlannedVisitDefinition],
) -> Tuple[Tuple[str, str], ...]:
    """Stable planned-visit -> actual-bundle assignment edges from unique
    assignments (§10: all joins use stable ids, never same-date/text)."""
    visit_id_by_key = {v.planned_visit_key: v.planned_visit_id
                       for v in planned_visits}
    edges: List[Tuple[str, str]] = []
    for a in outcome.visit_assignments:
        if a.decision_status != vs.VISIT_ASSIGNMENT_UNIQUE:
            continue
        planned_id = visit_id_by_key.get(a.selected_planned_visit_id, "")
        if planned_id and a.actual_bundle_id:
            edges.append((planned_id, a.actual_bundle_id))
    return tuple(sorted(edges))


def _build_risk_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
) -> Tuple[vs.VisitRiskMarker, ...]:
    """One VisitRiskMarker per positive / boundary / not_evaluable unit,
    binding unit, candidate-or-risk, query and source locators and
    preserving supporting / counterevidence / coverage-gap semantics.
    negative / not_applicable project no marker."""
    query_by_unit: Dict[str, List[str]] = {}
    for q in outcome.query_drafts:
        if q.unit_id and q.query_id:
            query_by_unit.setdefault(q.unit_id, []).append(q.query_id)

    markers: List[vs.VisitRiskMarker] = []
    for result in outcome.unit_results:
        disposition = result.l1_disposition
        if disposition in (L1Disposition.NEGATIVE,
                           L1Disposition.NOT_APPLICABLE,
                           L1Disposition.NOT_EVALUABLE):
            # risk markers require a candidate_or_risk_id; not_evaluable
            # units surface via coverage-gap notices, never a risk marker.
            continue

        candidate_id = ""
        for ref in result.risk_candidate_refs:
            candidate_id = (getattr(ref, "candidate_id", "") or "")
            if candidate_id:
                break

        anchor_kind = result.anchor_kind or vs.RELATION_FIXED_REFERENCE
        if anchor_kind not in vs.RELATION_TYPES:
            anchor_kind = vs.RELATION_FIXED_REFERENCE
        anchor_state = vs.ANCHOR_STATE_DATED
        if not result.anchor_start and not result.actual_start:
            anchor_state = vs.ANCHOR_STATE_PENDING_TIME
        elif result.precision in (vs.PRECISION_MONTH, vs.PRECISION_YEAR):
            anchor_state = vs.ANCHOR_STATE_PARTIAL

        supporting = tuple(result.source_locator_ids)
        counterevidence: List[str] = []
        for ev in result.evidence:
            if getattr(ev, "polarity", "") == "counterevidence":
                loc = getattr(ev, "locator", None)
                if loc is not None:
                    counterevidence.append(loc.locator_id())

        audience = result.audience_label or "资料不足，暂无法核实"
        if disposition == L1Disposition.BOUNDARY \
                and not audience.endswith("（边界）"):
            audience = f"{audience}（边界）"
        if not audience_payload_clean(audience):
            raise vs.ScheduleSliceError(
                f"risk marker audience label leaks an internal token: "
                f"{audience!r}")

        markers.append(vs.VisitRiskMarker(
            marker_id="",
            audience_label=audience,
            monitoring_priority=result.monitoring_priority,
            anchor_kind=anchor_kind,
            anchor_state=anchor_state,
            unit_id=result.unit_id,
            candidate_or_risk_id=candidate_id,
            anchor_start=result.anchor_start or result.window_start or "",
            anchor_end=result.anchor_end or result.window_end or "",
            date_precision=result.precision,
            supporting_locator_ids=supporting,
            counterevidence_locator_ids=tuple(sorted(set(counterevidence))),
            query_ids=tuple(sorted(query_by_unit.get(result.unit_id, []))),
            coverage_gap=bool(result.coverage_gap_notices),
        ))
    markers.sort(key=lambda m: (m.monitoring_priority, m.unit_id))
    return tuple(markers)


def _build_pending_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
    encounters: Sequence[vs.ActualEncounterRecord],
) -> Tuple[PendingContextMarker, ...]:
    """Pending-area markers for missing / partial / conflicting dates and
    pending assignment.  Never a fabricated time point."""
    markers: List[PendingContextMarker] = []
    out_of_cutoff_ids = set(outcome.out_of_cutoff_object_ids)

    for enc in encounters:
        if enc.encounter_id in out_of_cutoff_ids:
            continue
        if not enc.start or enc.start == "0001-01-01":
            markers.append(PendingContextMarker(
                marker_id="",
                context_type="missing_date",
                subject_ref=outcome.subject_ref,
                reference_role="encounter",
                reference_key=enc.encounter_id,
                exhibit_label="实际就诊日期缺失",
                reason="实际记录无可比较日期",
                source_locator_ids=tuple(enc.source_locator_ids),
            ))
        elif enc.date_precision in (vs.PRECISION_MONTH, vs.PRECISION_YEAR):
            markers.append(PendingContextMarker(
                marker_id="",
                context_type="partial_date",
                subject_ref=outcome.subject_ref,
                reference_role="encounter",
                reference_key=enc.encounter_id,
                exhibit_label="实际就诊日期精度不足",
                reason="部分日期未降至日级精度",
                source_locator_ids=tuple(enc.source_locator_ids),
            ))

    for result in outcome.unit_results:
        if result.l1_disposition != L1Disposition.NOT_EVALUABLE:
            continue
        if result.actual_start or result.anchor_start:
            continue
        role = "activity" if result.planned_activity_key else "visit"
        key = result.planned_activity_key or result.planned_visit_key
        if not key:
            continue
        markers.append(PendingContextMarker(
            marker_id="",
            context_type="missing_date",
            subject_ref=outcome.subject_ref,
            reference_role=role,
            reference_key=key,
            exhibit_label="资料不足，暂无法核实",
            reason=result.not_evaluable_reason or "关键日期缺失",
            source_locator_ids=tuple(result.source_locator_ids),
        ))

    markers.sort(key=lambda m: (m.context_type, m.reference_role,
                                m.reference_key))
    return tuple(markers)


def _build_out_of_cutoff_markers(
    *,
    outcome: vse.D05EvaluationOutcome,
    encounters: Sequence[vs.ActualEncounterRecord],
    activities: Sequence[vs.ActualActivityRecord],
) -> Tuple[OutOfCutoffContextMarker, ...]:
    """Out-of-cutoff context markers; these records never enter the
    current-run expected-set / assignment / L1 / L2 / L3."""
    encounter_by_id = {e.encounter_id: e for e in encounters}
    activity_by_id = {a.actual_activity_id: a for a in activities}

    markers: List[OutOfCutoffContextMarker] = []
    for oid in sorted(outcome.out_of_cutoff_object_ids):
        enc = encounter_by_id.get(oid)
        if enc is not None:
            markers.append(OutOfCutoffContextMarker(
                marker_id="",
                object_type="encounter",
                object_id=oid,
                subject_ref=outcome.subject_ref,
                recorded_start=enc.start,
                recorded_end=enc.end,
                date_precision=enc.date_precision,
                reason="cutoff 后实际就诊，不参与当前评价",
                source_locator_ids=tuple(enc.source_locator_ids),
            ))
            continue
        act = activity_by_id.get(oid)
        if act is not None:
            markers.append(OutOfCutoffContextMarker(
                marker_id="",
                object_type="activity",
                object_id=oid,
                subject_ref=outcome.subject_ref,
                recorded_start=act.start,
                recorded_end=act.end,
                date_precision=act.date_precision,
                reason="cutoff 后实际活动，不参与当前评价",
                source_locator_ids=tuple(act.source_locator_ids),
            ))
    markers.sort(key=lambda m: (m.object_type, m.object_id))
    return tuple(markers)


# ---------------------------------------------------------------------------
# Main projection entry point
# ---------------------------------------------------------------------------

def project_visit_schedule_journey(
    outcome: vse.D05EvaluationOutcome,
    *,
    planned_visits: Sequence[vs.PlannedVisitDefinition],
    planned_activities: Sequence[vs.PlannedActivityDefinition] = (),
    encounters: Sequence[vs.ActualEncounterRecord] = (),
    bundles: Sequence[vs.ActualEncounterBundle] = (),
    scope_decisions: Sequence[vs.ActualRecordScopeDecision] = (),
    activities: Sequence[vs.ActualActivityRecord] = (),
) -> vs.VisitJourneyProjection:
    """Build the renderer-neutral Patient Journey projection (§10).

    Assembles the separate planned-visit and actual-encounter markers,
    the differentiated activity domain-lane markers, the stable
    assignment edges, the risk markers, the pending-area markers and the
    out-of-cutoff context markers into the accepted
    :class:`~mm_r4.visit_schedule.VisitJourneyProjection` schema.

    The accepted projection identity (``projection_id`` / ``payload_hash``)
    covers the planned, actual, activity, risk, pending-time and
    out-of-cutoff marker ids together with assignment edges.  The payload
    hash additionally covers source locators.  Marker ids are sorted inside
    each collection, so input order cannot change the identity while marker
    removal or content changes remain detectable.
    """
    planned_markers = _build_planned_visit_markers(
        outcome=outcome, planned_visits=planned_visits)
    actual_markers = _build_actual_encounter_markers(
        outcome=outcome, encounters=encounters, bundles=bundles,
        scope_decisions=scope_decisions, planned_visits=planned_visits)
    activity_markers = _build_activity_markers(
        outcome=outcome, planned_activities=planned_activities,
        planned_visits=planned_visits)
    edges = _build_assignment_edges(outcome, planned_visits)
    risk_markers = _build_risk_markers(outcome=outcome)
    pending_markers = _build_pending_markers(
        outcome=outcome, encounters=encounters)
    out_markers = _build_out_of_cutoff_markers(
        outcome=outcome, encounters=encounters, activities=activities)

    all_loc_ids: Set[str] = set()
    for m in planned_markers:
        all_loc_ids.update(m.source_locator_ids)
    for m in actual_markers:
        all_loc_ids.update(m.source_locator_ids)
    for m in activity_markers:
        all_loc_ids.update(m.source_locator_ids)
    for m in risk_markers:
        all_loc_ids.update(m.supporting_locator_ids)
        all_loc_ids.update(m.counterevidence_locator_ids)
    for m in pending_markers:
        all_loc_ids.update(m.source_locator_ids)
    for m in out_markers:
        all_loc_ids.update(m.source_locator_ids)
    for n in outcome.coverage_gap_notices:
        all_loc_ids.update(n.reachable_source_locator_ids)

    return vs.VisitJourneyProjection(
        projection_id="",
        subject_ref=outcome.subject_ref,
        site_ref=outcome.site_ref,
        planned_visit_markers=planned_markers,
        actual_encounter_markers=actual_markers,
        activity_markers=activity_markers,
        assignment_edges=edges,
        risk_markers=risk_markers,
        pending_time_markers=pending_markers,
        out_of_cutoff_markers=out_markers,
        source_locator_ids=tuple(sorted(all_loc_ids)),
    )


# ---------------------------------------------------------------------------
# Projection QC helpers (challenges 87/90/91/93/94/96)
# Renderer-neutral: these never mutate L1/L3; they only filter or reject
# display payloads.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskOverlapCluster:
    """One overlap cluster of risk markers (challenge 93).

    Clustering is a display grouping: every member keeps its own
    ``marker_id`` / ``unit_id`` / priority, the cluster is expandable, and
    the member count equals the number of clustered markers.  High and
    medium risks that share a dated interval stay distinct identities.
    """

    cluster_id: str
    member_marker_ids: Tuple[str, ...]
    member_unit_ids: Tuple[str, ...]
    priorities: Tuple[str, ...]
    expandable: bool = True

    def __post_init__(self) -> None:
        if not self.member_marker_ids:
            raise vs.ScheduleSliceError(
                "RiskOverlapCluster requires at least one member marker")
        if len(set(self.member_marker_ids)) != len(self.member_marker_ids):
            raise vs.ScheduleSliceError(
                "RiskOverlapCluster dropped or duplicated a marker identity")
        if len(self.member_unit_ids) != len(self.member_marker_ids):
            raise vs.ScheduleSliceError(
                "RiskOverlapCluster unit ids must align 1:1 with markers")
        object.__setattr__(self, "expandable", True)


def _interval(marker: vs.VisitRiskMarker) -> Tuple[str, str]:
    start = marker.anchor_start or ""
    end = marker.anchor_end or start
    return start, end


def _intervals_overlap(a: Tuple[str, str], b: Tuple[str, str]) -> bool:
    a0, a1 = a
    b0, b1 = b
    if not a0 or not b0:
        return False
    return a0 <= b1 and b0 <= a1


def cluster_overlapping_risks(
    markers: Sequence[vs.VisitRiskMarker],
) -> Tuple[RiskOverlapCluster, ...]:
    """Group overlapping dated risk markers without dropping identity
    (challenge 93).  Non-overlapping markers form singleton clusters.
    Every input marker id appears in exactly one cluster."""
    remaining = list(markers)
    clusters: List[RiskOverlapCluster] = []
    seen: Set[str] = set()
    while remaining:
        seed = remaining.pop(0)
        if seed.marker_id in seen:
            continue
        group = [seed]
        seen.add(seed.marker_id)
        changed = True
        while changed:
            changed = False
            still: List[vs.VisitRiskMarker] = []
            for other in remaining:
                if other.marker_id in seen:
                    continue
                if any(_intervals_overlap(_interval(g), _interval(other))
                       for g in group):
                    group.append(other)
                    seen.add(other.marker_id)
                    changed = True
                else:
                    still.append(other)
            remaining = still
        group.sort(key=lambda m: (m.monitoring_priority, m.unit_id))
        clusters.append(RiskOverlapCluster(
            cluster_id="d05-cluster-" + content_hash(
                [m.marker_id for m in group]),
            member_marker_ids=tuple(m.marker_id for m in group),
            member_unit_ids=tuple(m.unit_id for m in group),
            priorities=tuple(m.monitoring_priority for m in group),
        ))
    clusters.sort(key=lambda c: c.cluster_id)
    clustered_ids = [mid for c in clusters for mid in c.member_marker_ids]
    if len(clustered_ids) != len(markers) \
            or set(clustered_ids) != {m.marker_id for m in markers}:
        raise vs.ScheduleSliceError(
            "cluster_overlapping_risks lost or duplicated a risk identity")
    return tuple(clusters)


def _day_token(value: str) -> str:
    return (value or "")[:10]


def brush_journey_display(
    projection: vs.VisitJourneyProjection,
    *,
    start: str,
    end: str,
) -> vs.VisitJourneyProjection:
    """Time-brush / zoom display filter (challenge 94).

    Returns a *new* projection whose markers are restricted to the
    ``[start, end]`` day window.  The source projection is not mutated;
    L1/L3 live on the evaluation outcome and cannot change here.
    """
    lo = _day_token(start)
    hi = _day_token(end)
    if not lo or not hi or lo > hi:
        raise vs.ScheduleSliceError(
            f"brush window {start!r}..{end!r} is not a closed day interval")

    def in_window(day: str) -> bool:
        token = _day_token(day)
        return bool(token) and lo <= token <= hi

    planned = tuple(
        m for m in projection.planned_visit_markers
        if in_window(m.window_start) or in_window(m.nominal_anchor)
        or in_window(m.window_end))
    actual = tuple(
        m for m in projection.actual_encounter_markers
        if in_window(m.start) or in_window(m.end))
    risks = tuple(
        m for m in projection.risk_markers
        if in_window(m.anchor_start) or in_window(m.anchor_end))
    pending = tuple(
        m for m in projection.pending_time_markers)
    # Pending-area markers have no fabricated date; they stay in the
    # pending area under any brush (challenge 92).
    out = tuple(
        m for m in projection.out_of_cutoff_markers
        if in_window(getattr(m, "recorded_start", "")))
    kept_planned = {m.planned_visit_id for m in planned}
    kept_actual = {m.encounter_id for m in actual}
    edges = tuple(
        e for e in projection.assignment_edges
        if e[0] in kept_planned or e[1] in kept_actual)
    return vs.VisitJourneyProjection(
        projection_id="",
        subject_ref=projection.subject_ref,
        site_ref=projection.site_ref,
        planned_visit_markers=planned,
        actual_encounter_markers=actual,
        activity_markers=projection.activity_markers,
        assignment_edges=edges,
        risk_markers=risks,
        pending_time_markers=pending,
        out_of_cutoff_markers=out,
        source_locator_ids=projection.source_locator_ids,
    )


def center_risk_join_qc(
    subject_projections: Sequence[vs.VisitJourneyProjection],
) -> Dict[str, object]:
    """Center aggregation may only carry counts, never cloned subject
    risk markers (challenge 96).  The returned payload has an empty
    ``copied_marker_ids`` tuple; any non-empty copy is a join/QC fail."""
    if not subject_projections:
        raise vs.ScheduleSliceError(
            "center_risk_join_qc requires at least one subject projection")
    marker_ids: List[str] = []
    candidate_ids: List[str] = []
    for proj in subject_projections:
        if not isinstance(proj, vs.VisitJourneyProjection):
            raise vs.ScheduleSliceError(
                "center_risk_join_qc requires VisitJourneyProjection inputs")
        for marker in proj.risk_markers:
            marker_ids.append(marker.marker_id)
            if marker.candidate_or_risk_id:
                candidate_ids.append(marker.candidate_or_risk_id)
    return {
        "subject_count": len(subject_projections),
        "risk_count": len(marker_ids),
        "copied_marker_ids": (),
        "copied_candidate_ids": (),
        "subject_marker_ids": tuple(marker_ids),
        "subject_candidate_ids": tuple(candidate_ids),
    }


def reject_copied_center_risks(
    center_marker_ids: Sequence[str],
    subject_marker_ids: Sequence[str],
) -> None:
    """Challenge 96 fail-closed path: a center payload that copies a
    subject-level risk marker identity is rejected."""
    overlap = set(center_marker_ids) & set(subject_marker_ids)
    if overlap:
        raise vs.ScheduleSliceError(
            "center aggregation copied subject risk marker(s): "
            + ", ".join(sorted(overlap)))


def reject_collapsed_planned_actual(
    projection: vs.VisitJourneyProjection,
) -> None:
    """Challenge 90: planned and actual markers must stay distinct objects
    joined by edges, never a single '已记录事项'."""
    planned_ids = {m.marker_id for m in projection.planned_visit_markers}
    actual_ids = {m.marker_id for m in projection.actual_encounter_markers}
    if not planned_ids or not actual_ids:
        raise vs.ScheduleSliceError(
            "planned/actual collapse QC requires both marker kinds")
    if planned_ids & actual_ids:
        raise vs.ScheduleSliceError(
            "Journey collapsed planned and actual into shared marker ids")
    for marker in projection.planned_visit_markers:
        if not audience_payload_clean(marker.audience_name) \
                or "已记录事项" in marker.audience_name:
            raise vs.ScheduleSliceError(
                "planned marker leaks collapsed-record vocabulary")
    for marker in projection.actual_encounter_markers:
        if marker.audience_name and (
                not audience_payload_clean(marker.audience_name)
                or "已记录事项" in marker.audience_name):
            raise vs.ScheduleSliceError(
                "actual marker leaks collapsed-record vocabulary")


def reject_visitnum_as_time_order(
    *,
    planned_visits: Sequence[vs.PlannedVisitDefinition],
    actual_markers: Sequence[vs.ActualEncounterMarker],
    proposed_encounter_order: Sequence[str],
) -> None:
    """Challenge 91: a display order that follows contingent VISITNUM /
    planned_order when recorded dates contradict that order is rejected.
    Time order is the recorded start, never VISITNUM."""
    if not proposed_encounter_order:
        raise vs.ScheduleSliceError(
            "reject_visitnum_as_time_order requires a proposed order")
    by_id = {m.encounter_id: m for m in actual_markers}
    dated = [m for m in actual_markers if m.start]
    time_order = tuple(
        m.encounter_id
        for m in sorted(dated, key=lambda m: (m.start, m.encounter_id)))
    proposed = tuple(proposed_encounter_order)
    if proposed == time_order:
        return
    audience_to_order = {
        v.audience_visit_name: v.planned_order for v in planned_visits}

    def _visitnum_rank(eid: str) -> str:
        marker = by_id.get(eid)
        if marker is None:
            return "zzz"
        return audience_to_order.get(marker.audience_name, "zzz")

    visitnum_sorted = tuple(sorted(proposed, key=_visitnum_rank))
    if proposed == visitnum_sorted:
        raise vs.ScheduleSliceError(
            "Journey used VISITNUM/planned_order as triggered-visit time "
            "order; recorded dates contradict that order")
    raise vs.ScheduleSliceError(
        "Journey display order is not the recorded-time order")
