"""R4-D01 AE/MH projection: Chinese Query drafts and journey projection.

This module produces **projection data** from :class:`AEMHUnitResult` /
:class:`AEMHSliceResult` values:

* :func:`project_query_drafts` -- structured Chinese three-part Query
  projection (``basis`` + ``finding`` + ``action``) with source links.
* :func:`project_journey` -- a journey projection payload with distinct
  medical event categories, temporal/visit anchors, risk markers and
  uncertainty.

This is **data**, not an R5 UI (matrix §3.9, §5.1).  Engineering codes
are kept stable and separate from audience-facing Chinese labels.  The
audience text uses concrete medical wording and never exposes research
jargon (matrix §3.9 prohibited terms).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple

from .aemh import (
    AEMHSliceResult,
    AEMHUnitResult,
    CLINICAL_FLAG_TOKENS,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_UNKNOWN,
)
from .contracts import QueryDraftRef

__all__ = [
    "QueryProjection",
    "JourneyProjection",
    "JourneyEvent",
    "project_query_drafts",
    "project_journey",
    "project_subject_journey",
    "query_to_text",
    # Audience label helpers
    "disposition_audience_label",
    "category_audience_label",
    "monitoring_priority_audience_label",
    "seriousness_audience_label",
]


# ---------------------------------------------------------------------------
# Audience label maps (stable engineering code -> Chinese audience label)
# ---------------------------------------------------------------------------

#: L1 disposition -> audience label.  Uses concrete medical wording.
#: Finding 9: negative uses a clear non-risk conclusion, not the semantically
#: inverted "当前 AE/MH 中未发现对应记录" (that phrase belongs in the Query
#: finding text where it is a positive finding).
_DISPOSITION_LABELS: Dict[str, str] = {
    "positive": "疑似 AE 漏报",
    "negative": "当前证据范围内未发现需核实的 AE/MH 问题",
    "boundary": "日期或归类边界，需进一步核实",
    "not_applicable": "该评价单元在当前方案版本下不适用",
    "not_evaluable": "信息不足，暂无法评价",
}

#: Journey category -> audience label (matrix §3.9).
#: AE/MH/CM/IP/检查/住院/操作/症状 are distinct.
_CATEGORY_LABELS: Dict[str, str] = {
    "ae": "不良事件",
    "mh": "既往病史",
    "cm": "合并用药",
    "ip": "研究药物处置",
    "lab": "实验室检查",
    "exam": "体格/辅助检查",
    "hospitalization": "住院/就医",
    "procedure": "医学操作",
    "symptom": "症状",
    "seriousness": "严重性线索",
    "death": "死亡事件",
    "visit": "访视",
    "other": "其他医学事件",
}

#: Monitoring priority -> audience label (matrix §3.5).
_PRIORITY_LABELS: Dict[str, str] = {
    "high": "高",
    "medium": "中",
    "low": "低",
    "unknown": "未知",
}

#: Seriousness criterion token -> audience label.
_SERIOUSNESS_LABELS: Dict[str, str] = {
    "sae": "严重不良事件 (SAE)",
    "aesi": "特别关注不良事件 (AESI)",
    "death": "死亡",
    "life_threatening": "危及生命",
    "hospitalization": "住院或延长住院",
    "disability": "显著功能障碍",
    "congenital_anomaly": "先天异常",
    "other_important_medical_event": "其他重要医学事件",
}


def disposition_audience_label(disposition: str) -> str:
    """L1 disposition engineering code -> Chinese audience label."""
    return _DISPOSITION_LABELS.get(disposition, disposition)


def category_audience_label(category: str) -> str:
    """Journey category engineering code -> Chinese audience label."""
    return _CATEGORY_LABELS.get(category, category)


def monitoring_priority_audience_label(priority: str) -> str:
    """Monitoring priority engineering code -> Chinese audience label."""
    return _PRIORITY_LABELS.get(priority, priority)


def seriousness_audience_label(criterion: str) -> str:
    """Seriousness criterion token -> Chinese audience label."""
    return _SERIOUSNESS_LABELS.get(criterion, criterion)


# ---------------------------------------------------------------------------
# Query projection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QueryProjection:
    """One projected Query draft with Chinese audience text.

    Engineering fields (``query_id``, ``unit_id``, ``engineering_disposition``)
    are stable codes; ``basis`` / ``finding`` / ``action`` carry the
    Chinese three-part Query text.  ``source_locator_ids`` link to the
    row-level source records (matrix §5.1).
    """

    query_id: str
    unit_id: str
    basis: str
    finding: str
    action: str
    source_locator_ids: Tuple[str, ...]
    linked_candidate_id: str = ""
    linked_risk_instance_id: str = ""
    engineering_disposition: str = ""
    subject_ref: str = ""
    audience_label: str = ""

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValueError("QueryProjection.query_id is required")
        if not self.unit_id.strip():
            raise ValueError("QueryProjection.unit_id is required")
        loc_ids = tuple(sorted(set(self.source_locator_ids)))
        if not loc_ids:
            raise ValueError(
                "QueryProjection must link at least one source locator")
        object.__setattr__(self, "source_locator_ids", loc_ids)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "unit_id": self.unit_id,
            "basis": self.basis,
            "finding": self.finding,
            "action": self.action,
            "source_locator_ids": list(self.source_locator_ids),
            "linked_candidate_id": self.linked_candidate_id,
            "linked_risk_instance_id": self.linked_risk_instance_id,
            "engineering_disposition": self.engineering_disposition,
            "subject_ref": self.subject_ref,
            "audience_label": self.audience_label,
        }


def project_query_drafts(
    unit_result: AEMHUnitResult,
) -> Tuple[QueryProjection, ...]:
    """Project Query drafts from one :class:`AEMHUnitResult`.

    Each Query is ``basis + finding + action`` with source links.  Only
    positive and boundary units produce Query projections (matrix §5.1).
    """
    projections: List[QueryProjection] = []
    for q in unit_result.query_refs:
        if not isinstance(q, QueryDraftRef):
            continue
        audience = disposition_audience_label(unit_result.l1_disposition)
        projections.append(QueryProjection(
            query_id=q.query_id,
            unit_id=q.unit_id,
            basis=f"依据：{q.basis}",
            finding=q.finding,
            action=q.action,
            source_locator_ids=q.source_locator_ids,
            linked_candidate_id=q.linked_candidate_id,
            linked_risk_instance_id=q.linked_risk_instance_id,
            engineering_disposition=unit_result.l1_disposition,
            subject_ref=unit_result.subject_ref,
            audience_label=audience,
        ))
    return tuple(projections)


def query_to_text(projection: QueryProjection) -> str:
    """Render a Query projection as the exact three-part Chinese text."""
    return f"{projection.basis}\n发现：{projection.finding}\n行动项：{projection.action}"


# ---------------------------------------------------------------------------
# Journey projection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class JourneyEvent:
    """One event on the medical journey projection.

    Engineering fields (``category``, ``monitoring_priority_code``) are
    stable codes; ``category_label`` carries the Chinese audience label.
    Temporal/visit anchor, risk marker and uncertainty are explicit
    (matrix §3.9).
    """

    category: str
    unit_id: str
    category_label: str
    concept: str
    source_locator_id: str
    record_id: str
    temporal_anchor_raw: str
    temporal_anchor_normalized: str
    temporal_precision: str
    visit_label: str
    phase: str
    intensity: str
    intensity_scale: str
    seriousness_criteria: Tuple[str, ...]
    seriousness_labels: Tuple[str, ...]
    monitoring_priority_code: str
    monitoring_priority_label: str
    is_risk_marker: bool
    ai_assertion: bool
    uncertainty: str

    def __post_init__(self) -> None:
        if not isinstance(self.unit_id, str) or not self.unit_id.strip():
            raise ValueError(
                "JourneyEvent.unit_id is required and must be non-empty "
                "(finding 6)")
        object.__setattr__(
            self, "seriousness_criteria", tuple(self.seriousness_criteria))
        object.__setattr__(
            self, "seriousness_labels", tuple(self.seriousness_labels))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "unit_id": self.unit_id,
            "category_label": self.category_label,
            "concept": self.concept,
            "source_locator_id": self.source_locator_id,
            "record_id": self.record_id,
            "temporal_anchor_raw": self.temporal_anchor_raw,
            "temporal_anchor_normalized": self.temporal_anchor_normalized,
            "temporal_precision": self.temporal_precision,
            "visit_label": self.visit_label,
            "phase": self.phase,
            "intensity": self.intensity,
            "intensity_scale": self.intensity_scale,
            "seriousness_criteria": list(self.seriousness_criteria),
            "seriousness_labels": list(self.seriousness_labels),
            "monitoring_priority_code": self.monitoring_priority_code,
            "monitoring_priority_label": self.monitoring_priority_label,
            "is_risk_marker": self.is_risk_marker,
            "ai_assertion": self.ai_assertion,
            "uncertainty": self.uncertainty,
        }


@dataclass(frozen=True)
class JourneyProjection:
    """Journey projection for one subject across one or more units.

    This is **projection data** (matrix §3.9): visit/temporal anchors,
    distinct event categories, risk markers, source links and uncertainty.
    It is NOT a rendered UI component.
    """

    subject_ref: str
    events: Tuple[JourneyEvent, ...]
    disposition_code: str
    disposition_label: str
    has_risk_marker: bool
    monitoring_priority_code: str
    monitoring_priority_label: str
    uncertainty_summary: str = ""
    unit_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "unit_ids", tuple(self.unit_ids))

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def risk_marker_count(self) -> int:
        return sum(1 for e in self.events if e.is_risk_marker)

    def categories_present(self) -> Tuple[str, ...]:
        return tuple(sorted(set(e.category for e in self.events)))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "subject_ref": self.subject_ref,
            "events": [e.canonical_payload() for e in self.events],
            "disposition_code": self.disposition_code,
            "disposition_label": self.disposition_label,
            "has_risk_marker": self.has_risk_marker,
            "monitoring_priority_code": self.monitoring_priority_code,
            "monitoring_priority_label": self.monitoring_priority_label,
            "uncertainty_summary": self.uncertainty_summary,
            "unit_ids": list(self.unit_ids),
        }


def _is_risk_marker(marker: Mapping[str, Any], disposition: str) -> bool:
    """A journey marker is a risk marker only when its locator is the
    actual candidate locator, a boundary-supporting locator, or a high-
    priority/SAE/AESI/death locator (finding 8).  An unrelated recorded
    AE on a positive/boundary unit is NOT a risk marker."""
    if marker.get("is_candidate_locator"):
        return True
    if marker.get("is_boundary_support_locator"):
        return True
    if marker.get("is_serious_locator"):
        return True
    pri = marker.get("monitoring_priority", MONITORING_PRIORITY_UNKNOWN)
    if pri == MONITORING_PRIORITY_HIGH:
        return True
    seriousness = marker.get("seriousness_criteria", [])
    if any(s in CLINICAL_FLAG_TOKENS for s in seriousness):
        return True
    return False


def project_journey(
    unit_result: AEMHUnitResult,
) -> JourneyProjection:
    """Project the medical journey for one :class:`AEMHUnitResult`.

    Each journey marker from the unit result becomes a
    :class:`JourneyEvent` with distinct categories, temporal/visit anchors,
    risk markers and uncertainty.
    """
    events: List[JourneyEvent] = []
    for marker in unit_result.journey_markers:
        marker_unit_id = marker.get("unit_id", "")
        if marker_unit_id != unit_result.unit_id:
            raise ValueError(
                "Journey marker unit_id must exactly match its source "
                "AEMHUnitResult.unit_id")
        category = marker.get("category", "other")
        seriousness = marker.get("seriousness_criteria", [])
        seriousness_labels = tuple(
            seriousness_audience_label(s) for s in seriousness)
        pri_code = marker.get(
            "monitoring_priority", MONITORING_PRIORITY_UNKNOWN)
        events.append(JourneyEvent(
            category=category,
            unit_id=marker_unit_id,
            category_label=category_audience_label(category),
            concept=marker.get("concept", ""),
            source_locator_id=marker.get("source_locator_id", ""),
            record_id=marker.get("record_id", ""),
            temporal_anchor_raw=marker.get("temporal_anchor_raw", ""),
            temporal_anchor_normalized=marker.get(
                "temporal_anchor_normalized", ""),
            temporal_precision=marker.get("temporal_precision", "none"),
            visit_label=marker.get("visit_label", ""),
            phase=marker.get("phase", ""),
            intensity=marker.get("intensity", ""),
            intensity_scale=marker.get("intensity_scale", ""),
            seriousness_criteria=tuple(seriousness),
            seriousness_labels=seriousness_labels,
            monitoring_priority_code=pri_code,
            monitoring_priority_label=monitoring_priority_audience_label(
                pri_code),
            is_risk_marker=_is_risk_marker(
                marker, unit_result.l1_disposition),
            ai_assertion=marker.get("ai_assertion", False),
            uncertainty=marker.get("uncertainty", ""),
        ))

    # Sort events by normalized temporal anchor (stable).
    events.sort(key=lambda e: (
        not e.temporal_anchor_normalized,
        e.temporal_anchor_normalized,
        e.source_locator_id))

    has_risk = any(e.is_risk_marker for e in events)
    pri_code = unit_result.medical_grading.monitoring_priority
    uncertainty_parts = [
        e.uncertainty for e in events if e.uncertainty]
    uncertainty_summary = "；".join(dict.fromkeys(uncertainty_parts))

    return JourneyProjection(
        subject_ref=unit_result.subject_ref,
        events=tuple(events),
        disposition_code=unit_result.l1_disposition,
        disposition_label=disposition_audience_label(
            unit_result.l1_disposition),
        has_risk_marker=has_risk,
        monitoring_priority_code=pri_code,
        monitoring_priority_label=monitoring_priority_audience_label(pri_code),
        uncertainty_summary=uncertainty_summary,
        unit_ids=(unit_result.unit_id,),
    )


def project_subject_journey(
    slice_result: AEMHSliceResult,
) -> JourneyProjection:
    """Project the combined journey for one subject across all their units.

    Merges events from multiple unit results, preserving the per-unit
    disposition in each event's risk-marker flag.  The overall disposition
    is the most severe across units.
    """
    all_events: List[JourneyEvent] = []
    unit_ids: List[str] = []
    # Overall disposition: positive > boundary > not_evaluable > negative >
    # not_applicable.
    priority_order = {
        "positive": 0,
        "boundary": 1,
        "not_evaluable": 2,
        "negative": 3,
        "not_applicable": 4,
    }
    best_disposition = "not_applicable"
    best_priority_code = MONITORING_PRIORITY_UNKNOWN
    all_uncertainty: List[str] = []

    for ur in slice_result.unit_results:
        unit_journey = project_journey(ur)
        all_events.extend(unit_journey.events)
        unit_ids.append(ur.unit_id)
        if priority_order.get(ur.l1_disposition, 99) < priority_order.get(
                best_disposition, 99):
            best_disposition = ur.l1_disposition
        ur_pri = ur.medical_grading.monitoring_priority
        if ur_pri == MONITORING_PRIORITY_HIGH:
            best_priority_code = MONITORING_PRIORITY_HIGH
        elif (ur_pri == MONITORING_PRIORITY_MEDIUM
              and best_priority_code != MONITORING_PRIORITY_HIGH):
            best_priority_code = MONITORING_PRIORITY_MEDIUM
        elif (ur_pri == MONITORING_PRIORITY_LOW
              and best_priority_code not in (
                  MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_MEDIUM)):
            best_priority_code = MONITORING_PRIORITY_LOW
        if unit_journey.uncertainty_summary:
            all_uncertainty.append(unit_journey.uncertainty_summary)

    all_events.sort(key=lambda e: (
        not e.temporal_anchor_normalized,
        e.temporal_anchor_normalized,
        e.source_locator_id))

    has_risk = any(e.is_risk_marker for e in all_events)

    return JourneyProjection(
        subject_ref=slice_result.subject_ref,
        events=tuple(all_events),
        disposition_code=best_disposition,
        disposition_label=disposition_audience_label(best_disposition),
        has_risk_marker=has_risk,
        monitoring_priority_code=best_priority_code,
        monitoring_priority_label=monitoring_priority_audience_label(
            best_priority_code),
        uncertainty_summary="；".join(dict.fromkeys(all_uncertainty)),
        unit_ids=tuple(sorted(set(unit_ids))),
    )
