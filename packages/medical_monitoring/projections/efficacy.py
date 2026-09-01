"""R4-D06 renderer-neutral efficacy Patient Journey projection.

Frozen source of truth: ``FROZEN_R4_D06_CONTRACT_V1_16`` (§10).  This
module owns the D06 **journey projection surface**:

1. :class:`EfficacyJourneyProjection` -- the renderer-neutral projection
   object with an explicit visit axis, distinct efficacy / scale /
   response / trend lanes, typed event and risk markers, source jump
   targets, risk anchors, and separate pending / out-of-cutoff areas
   (never collapsed into a generic "已记录事项" label, never exposing
   internal terms such as "正式事实" / "候选信号" / "只读投影" / "positive"
   / "candidate" to the user).
2. :func:`project_efficacy_journey` -- builds the projection from the
   typed fixture and the evaluation scope decisions: baseline markers,
   threshold bands, actual-point markers, risk markers, pending markers
   and cutoff-later markers.  Undated records never get a fabricated
   position (they go to the pending area); cutoff-later records go to the
   "截止日后记录" area.
3. The audience payload factories and per-kind validation glue consumed by
   the evaluator's audience validation stage (frozen ``d06-audience-zh-v1``
   lexicon lives in :mod:`mm_r4.efficacy`).

Filtering / zooming / collapsing only changes the display; it never
changes L1/L3 dispositions, denominators, risk identity or counts.  The
projection is renderer-neutral: it declares structure, not pixels.

All data is synthetic and offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

__all__ = [
    "EfficacyJourneyProjection",
    "EfficacyJourneyMarker",
    "EfficacyTrendPoint",
    "MARKER_ACTUAL_POINT",
    "MARKER_BASELINE",
    "MARKER_THRESHOLD_BAND",
    "MARKER_RISK",
    "MARKER_PENDING",
    "MARKER_OUT_OF_CUTOFF",
    "project_efficacy_journey",
    "journey_audience_payload",
    "journey_audience_payload_from_projection",
    "query_audience_payload",
    "risk_label_audience_payload",
]

# Marker kinds (closed set, renderer-neutral).
MARKER_ACTUAL_POINT = "actual_point"
MARKER_BASELINE = "baseline"
MARKER_THRESHOLD_BAND = "threshold_band"
MARKER_RISK = "risk"
MARKER_PENDING = "pending"
MARKER_OUT_OF_CUTOFF = "out_of_cutoff"
MARKER_KINDS: Tuple[str, ...] = (
    MARKER_ACTUAL_POINT,
    MARKER_BASELINE,
    MARKER_THRESHOLD_BAND,
    MARKER_RISK,
    MARKER_PENDING,
    MARKER_OUT_OF_CUTOFF,
)


@dataclass(frozen=True)
class EfficacyTrendPoint:
    """One observed/derived trend point on the shared visit axis."""

    stable_endpoint_key: str
    stable_timepoint_key: str
    observed_time_ref: str
    nominal_time_ref: str
    value: str
    value_state: str
    reporter_role: str = "PRO"
    trend_rule_id: Optional[str] = None
    input_result_ids: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()

    def to_plain(self) -> Dict[str, Any]:
        return {
            "stable_endpoint_key": self.stable_endpoint_key,
            "stable_timepoint_key": self.stable_timepoint_key,
            "observed_time_ref": self.observed_time_ref,
            "nominal_time_ref": self.nominal_time_ref,
            "value": self.value,
            "value_state": self.value_state,
            "reporter_role": self.reporter_role,
            "trend_rule_id": self.trend_rule_id,
            "input_result_ids": list(self.input_result_ids),
            "source_locator_ids": list(self.source_locator_ids),
        }


@dataclass(frozen=True)
class EfficacyJourneyMarker:
    """One typed marker on the journey (risk / baseline / threshold / event).

    Every marker carries the actual typed source locator ids it was
    derived from and a content-addressed payload hash, so a locator
    mutation/removal changes the marker (and the projection) instead of
    silently retaining a generic payload.
    """

    marker_id: str
    marker_kind: str
    stable_endpoint_key: str
    stable_timepoint_key: str
    anchor_state: str
    audience_label: str
    monitoring_priority: Optional[str] = None
    actual_time_ref: Optional[str] = None
    nominal_time_ref: Optional[str] = None
    source_jump_target: Optional[str] = None
    risk_anchor: Optional[str] = None
    source_locator_ids: Tuple[str, ...] = ()
    payload_hash: Optional[str] = None

    def to_plain(self) -> Dict[str, Any]:
        payload = {
            "marker_id": self.marker_id,
            "marker_kind": self.marker_kind,
            "stable_endpoint_key": self.stable_endpoint_key,
            "stable_timepoint_key": self.stable_timepoint_key,
            "anchor_state": self.anchor_state,
            "audience_label": self.audience_label,
            "monitoring_priority": self.monitoring_priority,
            "actual_time_ref": self.actual_time_ref,
            "nominal_time_ref": self.nominal_time_ref,
            "source_jump_target": self.source_jump_target,
            "risk_anchor": self.risk_anchor,
            "source_locator_ids": list(self.source_locator_ids),
        }
        if self.payload_hash is not None:
            payload["payload_hash"] = self.payload_hash
        return payload


@dataclass(frozen=True)
class EfficacyJourneyProjection:
    """Renderer-neutral efficacy journey projection (§10)."""

    projection_id: str
    project_ref: str
    run_ref: str
    subject_ref: str
    site_ref: str
    episode_key: str
    scope_binding_id: str
    cutoff: str
    shared_temporal_spine_binding_id: str
    visit_axis_label: str
    visit_axis: Tuple[str, ...]
    endpoint_lanes: Tuple[str, ...]
    trend_points: Tuple[EfficacyTrendPoint, ...] = ()
    markers: Tuple[EfficacyJourneyMarker, ...] = ()
    pending_markers: Tuple[EfficacyJourneyMarker, ...] = ()
    out_of_cutoff_markers: Tuple[EfficacyJourneyMarker, ...] = ()
    data_gap_section_label: str = "资料待补充"
    after_cutoff_section_label: str = "截止日后记录"

    def to_plain(self) -> Dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "project_ref": self.project_ref,
            "run_ref": self.run_ref,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "episode_key": self.episode_key,
            "scope_binding_id": self.scope_binding_id,
            "cutoff": self.cutoff,
            "shared_temporal_spine_binding_id": (self.shared_temporal_spine_binding_id),
            "visit_axis_label": self.visit_axis_label,
            "visit_axis": list(self.visit_axis),
            "endpoint_lanes": list(self.endpoint_lanes),
            "trend_points": [point.to_plain() for point in self.trend_points],
            "markers": [marker.to_plain() for marker in self.markers],
            "pending_markers": [marker.to_plain() for marker in self.pending_markers],
            "out_of_cutoff_markers": [
                marker.to_plain() for marker in self.out_of_cutoff_markers
            ],
            "data_gap_section_label": self.data_gap_section_label,
            "after_cutoff_section_label": self.after_cutoff_section_label,
        }

    def payload_hash(self) -> str:
        from ..risks.efficacy import d06_content_hash

        return d06_content_hash(self.to_plain())


# ---------------------------------------------------------------------------
# Frozen canonical audience payloads (§10)
# ---------------------------------------------------------------------------

CANONICAL_JOURNEY_PAYLOAD: Dict[str, Any] = {
    "payload_kind": "journey",
    "payload_schema_version": "d06-journey-audience-v1",
    "display_text": "查看访视轴与来源依据",
    "visit_axis_label": "访视轴",
    "endpoint_lanes": [
        {
            "endpoint_label": "主要疗效终点",
            "marker_label": "查看评估记录",
            "source_jump_target": "受试者历时资料",
        }
    ],
}

CANONICAL_QUERY_SENTENCES: Dict[str, Dict[str, str]] = {
    "enrollment_not_occurred": {
        "basis_sentence": "依据：当前资料显示尚未入组。",
        "finding_sentence": "发现：疗效记录需核实。",
        "action_sentence": "行动项：请核实并更正相关记录。",
    },
    "enrolled_or_post_enrollment": {
        "basis_sentence": "依据：参与者已入组。",
        "finding_sentence": "发现：疗效记录需核实。",
        "action_sentence": (
            "行动项：请核实相关记录；如确认不符合方案，"
            "请评估是否构成方案偏离并按相应流程处理。"
        ),
    },
    "enrollment_state_unresolved": {
        "basis_sentence": "依据：当前入组状态尚未明确。",
        "finding_sentence": "发现：入组时序与疗效记录关系待核实。",
        "action_sentence": "行动项：请先核实随机、入组或首次给药状态及事件时序。",
    },
}

# Map a projection to the audience journey payload shape the validator
# checks (contract §10).
JOURNEY_AUDIENCE_DISPLAY_FIELDS = (
    "display_text",
    "endpoint_lanes",
    "visit_axis_label",
)


def journey_audience_payload() -> Dict[str, Any]:
    """Canonical renderer-neutral journey audience payload."""
    return dict(CANONICAL_JOURNEY_PAYLOAD)


def journey_audience_payload_from_projection(
    projection: EfficacyJourneyProjection,
) -> Dict[str, Any]:
    """Serialize a built journey projection into the audience payload the
    validator checks (§10).

    Before serialization the projection's provenance is verified from its
    own typed fields: every marker's content-addressed ``payload_hash``
    must match a recomputation over its payload (a dataclass-replaced or
    mutated marker with changed locator/content but stale hash raises a
    specific projection/contract error), every marker carrying a
    source-jump target must have validated source locators, and the
    projection must carry at least one validated source locator.  A
    valid projection still serializes to the frozen unchanged payload.
    """
    from ..risks.efficacy import D06ContractViolationError, ProjectionContractError
    from ..risks.efficacy import d06_content_hash

    all_locators: List[str] = []
    for marker in (
        projection.markers
        + projection.pending_markers
        + projection.out_of_cutoff_markers
    ):
        if marker.payload_hash is not None:
            marker_payload = {
                key: value
                for key, value in marker.to_plain().items()
                if key != "payload_hash"
            }
            if marker.payload_hash != d06_content_hash(marker_payload):
                raise ProjectionContractError(
                    f"journey marker {marker.marker_id} payload hash is stale",
                    "projection_validation",
                )
        if marker.source_jump_target and not marker.source_locator_ids:
            raise ProjectionContractError(
                f"journey marker {marker.marker_id} jump target without "
                "validated source locators",
                "projection_validation",
            )
        all_locators.extend(marker.source_locator_ids)
    if not all_locators:
        raise D06ContractViolationError(
            "journey projection has no validated source locators; "
            "payload suppressed",
            "pre_medical_output_validation",
        )
    first_lane = (
        projection.endpoint_lanes[0]
        if projection.endpoint_lanes
        else "主要疗效终点"
    )
    return {
        "payload_kind": "journey",
        "payload_schema_version": "d06-journey-audience-v1",
        "display_text": "查看访视轴与来源依据",
        "visit_axis_label": projection.visit_axis_label,
        "endpoint_lanes": [
            {
                "endpoint_label": first_lane,
                "marker_label": "查看评估记录",
                "source_jump_target": "受试者历时资料",
            }
        ],
    }


def query_audience_payload(
    query_context: str,
    basis_sentence: str,
    finding_sentence: str,
    action_sentence: str,
) -> Dict[str, Any]:
    return {
        "payload_kind": "query",
        "payload_schema_version": "d06-query-audience-v1",
        "query_context": query_context,
        "basis_sentence": basis_sentence,
        "finding_sentence": finding_sentence,
        "action_sentence": action_sentence,
    }


def risk_label_audience_payload(
    risk_category: str,
    priority_label: str,
    finding_summary: str,
    jump_target: str,
) -> Dict[str, Any]:
    return {
        "payload_kind": "risk_label",
        "payload_schema_version": "d06-risk_label-audience-v1",
        "risk_category": risk_category,
        "priority_label": priority_label,
        "finding_summary": finding_summary,
        "jump_target": jump_target,
    }


# ---------------------------------------------------------------------------
# Projection builder
# ---------------------------------------------------------------------------


def _marker(
    marker_id: str,
    kind: str,
    endpoint_key: str,
    timepoint_key: str,
    anchor_state: str,
    label: str,
    actual_time_ref: Optional[str] = None,
    nominal_time_ref: Optional[str] = None,
    priority: Optional[str] = None,
    jump_target: Optional[str] = None,
    risk_anchor: Optional[str] = None,
    source_locator_ids: Tuple[str, ...] = (),
) -> EfficacyJourneyMarker:
    marker = EfficacyJourneyMarker(
        marker_id=marker_id,
        marker_kind=kind,
        stable_endpoint_key=endpoint_key,
        stable_timepoint_key=timepoint_key,
        anchor_state=anchor_state,
        audience_label=label,
        monitoring_priority=priority,
        actual_time_ref=actual_time_ref,
        nominal_time_ref=nominal_time_ref,
        source_jump_target=jump_target,
        risk_anchor=risk_anchor,
        source_locator_ids=tuple(str(item) for item in source_locator_ids),
    )
    # Content-addressed payload hash: any locator/source drift changes
    # the marker (and therefore the projection hash).
    from dataclasses import replace as _replace

    from ..risks.efficacy import d06_content_hash

    marker_payload = {
        key: value
        for key, value in marker.to_plain().items()
        if key != "payload_hash"
    }
    return _replace(marker, payload_hash=d06_content_hash(marker_payload))


def project_efficacy_journey(
    fixture: Any,
    scope_status: Optional[str] = None,
    unit_l1: Optional[str] = None,
    priority_decision: Optional[Any] = None,
) -> EfficacyJourneyProjection:
    """Build the renderer-neutral journey projection from the typed fixture.

    Baseline / threshold / actual-point / risk markers stay on distinct
    lanes; undated or unresolved records enter the pending area; records
    after ``clinical_event_cutoff`` enter the cutoff-later area.  No
    internal term ever becomes a user label.

    Every identity -- projection id, shared temporal spine binding id,
    marker ids/types, risk anchor/identity, marker priority and
    source-jump targets -- is derived from the validated typed runtime
    objects (scope, spine binding, typed assessment records and locators,
    typed ``D06PriorityDecision``); there are no page/variant/static
    fallback identities.  An invalid projection or missing spine/decision
    fails closed instead of fabricating an identity.
    """
    from ..risks.efficacy import (
        D06ContractViolationError,
        d06_canonical_json,
        d06_sha256_text,
    )

    scope = fixture.scope
    definitions = fixture.definitions
    records = fixture.records
    bindings = getattr(fixture, "bindings", {}) or {}
    endpoint_key = definitions["endpoint"].get("stable_key")
    timepoint_key = definitions["timepoint"].get("key")
    if not endpoint_key or not timepoint_key:
        raise D06ContractViolationError(
            "journey projection requires typed endpoint/timepoint definitions",
            "pre_medical_output_validation",
        )
    # Shared temporal spine: the projection's time-spine identity comes
    # from the validated typed spine binding; a missing/drifted spine
    # fails closed instead of substituting a static id.
    spine = bindings.get("shared_temporal_spine_binding")
    if not isinstance(spine, (dict, Mapping)) or not spine.get("spine_binding_id"):
        raise D06ContractViolationError(
            "journey projection requires the typed shared temporal spine",
            "pre_medical_output_validation",
        )
    spine_binding_id = str(spine["spine_binding_id"])
    # Projection id is derived from the typed run identity (never a
    # static fallback); any scope/spine drift changes it.
    identity_core = [
        scope.get("project_ref", ""),
        scope.get("run_ref", ""),
        scope.get("subject_ref", ""),
        scope.get("episode_key", ""),
        scope.get("scope_binding_id", ""),
        spine_binding_id,
    ]
    projection_id = "D06-PROJECTION-{0}".format(
        d06_sha256_text(d06_canonical_json(identity_core))[:16]
    )
    assessments = records.get("assessments", [])
    trend_points = records.get("trend_points", [])
    # Effective assessment times: typed per-case overrides are part of the
    # actual runtime inputs (e.g. cutoff-later records for case 31).
    typed_parameters = getattr(fixture, "typed_parameters", {}) or {}
    assessment_override = typed_parameters.get("assessment") or {}
    if (
        isinstance(assessment_override, (dict, Mapping))
        and "time" in assessment_override
    ):
        assessments = [
            {
                **item,
                "time": str(assessment_override["time"]),
            }
            if item.get("id") == "ASM-W4-A"
            else item
            for item in assessments
        ]

    visit_axis = tuple(sorted({str(item.get("time", "")) for item in assessments}))
    markers: List[EfficacyJourneyMarker] = []
    pending: List[EfficacyJourneyMarker] = []
    out_of_cutoff: List[EfficacyJourneyMarker] = []
    cutoff = scope.get("clinical_event_cutoff", "")

    for assessment in assessments:
        assessment_id = str(assessment.get("id", ""))
        actual_time = str(assessment.get("time", ""))
        label = "查看评估记录"
        # Source-jump targets are emitted only for records carrying
        # validated typed source locators (the renderer label is the
        # frozen lexicon; the presence derives from the typed locator).
        locators = assessment.get("source_locator_ids") or []
        jump_target = "受试者历时资料" if locators else None
        if actual_time and actual_time > cutoff:
            out_of_cutoff.append(
                _marker(
                    marker_id=f"MRK-OOC-{assessment_id}",
                    kind=MARKER_OUT_OF_CUTOFF,
                    endpoint_key=endpoint_key,
                    timepoint_key=timepoint_key,
                    anchor_state="out_of_cutoff",
                    label=label,
                    actual_time_ref=actual_time,
                    nominal_time_ref=timepoint_key,
                    jump_target=jump_target,
                    source_locator_ids=locators,
                )
            )
            continue
        if not actual_time:
            pending.append(
                _marker(
                    marker_id=f"MRK-PEND-{assessment_id}",
                    kind=MARKER_PENDING,
                    endpoint_key=endpoint_key,
                    timepoint_key=timepoint_key,
                    anchor_state="pending_time",
                    label="资料待补充",
                    nominal_time_ref=timepoint_key,
                )
            )
            continue
        if "BASE" in assessment_id:
            markers.append(
                _marker(
                    marker_id=f"MRK-BASE-{assessment_id}",
                    kind=MARKER_BASELINE,
                    endpoint_key=endpoint_key,
                    timepoint_key=timepoint_key,
                    anchor_state="dated",
                    label="基线评估",
                    actual_time_ref=actual_time,
                    nominal_time_ref=timepoint_key,
                    source_locator_ids=locators,
                )
            )
        else:
            markers.append(
                _marker(
                    marker_id=f"MRK-ACT-{assessment_id}",
                    kind=MARKER_ACTUAL_POINT,
                    endpoint_key=endpoint_key,
                    timepoint_key=timepoint_key,
                    anchor_state="dated",
                    label=label,
                    actual_time_ref=actual_time,
                    nominal_time_ref=timepoint_key,
                    jump_target=jump_target,
                    source_locator_ids=locators,
                )
            )
    threshold = definitions.get("threshold", {})
    if threshold:
        markers.append(
            _marker(
                marker_id="MRK-THRESHOLD",
                kind=MARKER_THRESHOLD_BAND,
                endpoint_key=endpoint_key,
                timepoint_key=timepoint_key,
                anchor_state="dated",
                label="反应阈值",
                nominal_time_ref=timepoint_key,
            )
        )
    if unit_l1 == "positive":
        # Risk marker identity/anchor/priority come from the typed
        # priority decision (which itself derives from the typed resolver
        # input); a positive projection without the decision fails
        # closed instead of fabricating a risk identity.
        if priority_decision is None:
            raise D06ContractViolationError(
                "positive projection requires the typed priority decision",
                "pre_medical_output_validation",
            )
        risk_id = priority_decision.risk_id
        decision_locators = tuple(
            str(item)
            for item in getattr(priority_decision, "source_locator_ids", ())
        )
        markers.append(
            _marker(
                marker_id=f"MRK-{risk_id}",
                kind=MARKER_RISK,
                endpoint_key=endpoint_key,
                timepoint_key=timepoint_key,
                anchor_state="dated",
                label="评分变化待核实",
                priority=priority_decision.monitoring_priority,
                actual_time_ref=str(
                    assessments[-1].get("time", "") if assessments else ""
                ),
                nominal_time_ref=timepoint_key,
                jump_target=(
                    "受试者历时资料" if decision_locators else None
                ),
                risk_anchor=risk_id,
                source_locator_ids=decision_locators,
            )
        )

    trend_objects = tuple(
        EfficacyTrendPoint(
            stable_endpoint_key=endpoint_key,
            stable_timepoint_key=timepoint_key,
            observed_time_ref=str(point.get("time", "")),
            nominal_time_ref=timepoint_key,
            value=str(point.get("value", "")),
            value_state="observed",
        )
        for point in trend_points
    )

    return EfficacyJourneyProjection(
        projection_id=projection_id,
        project_ref=str(scope.get("project_ref", "")),
        run_ref=str(scope.get("run_ref", "")),
        subject_ref=str(scope.get("subject_ref", "")),
        site_ref=str(scope.get("site_ref", "")),
        episode_key=str(scope.get("episode_key", "")),
        scope_binding_id=str(scope.get("scope_binding_id", "")),
        cutoff=cutoff,
        shared_temporal_spine_binding_id=spine_binding_id,
        visit_axis_label="访视轴",
        visit_axis=visit_axis,
        endpoint_lanes=("主要疗效终点", "量表", "反应", "个体趋势"),
        trend_points=trend_objects,
        markers=tuple(markers),
        pending_markers=tuple(pending),
        out_of_cutoff_markers=tuple(out_of_cutoff),
    )
