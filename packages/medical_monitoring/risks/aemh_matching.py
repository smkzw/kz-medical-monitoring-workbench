"""Reported-event matching, journey markers, and Query text for AE/MH."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

from .aemh_temporal import compare_partial_dates, _precision_level
from .aemh_results import _concept
from .aemh_types import (
    EventMatchStrategy, MedicalGrading, ProtocolAEMHBoundary, SemanticRecord,
)
from .contracts import MONITORING_PRIORITY_HIGH

# ---------------------------------------------------------------------------
# Reported-match logic (matrix §4 D01 "误报控制")
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ReportedMatchOutcome:
    """Result of matching an evidence record against reported AE/MH."""

    matched: bool
    boundary: bool
    not_evaluable: bool
    reason: str
    matched_record: Optional[SemanticRecord] = None


def _match_evidence_to_reported(
    evidence: SemanticRecord,
    reported: Sequence[SemanticRecord],
    strategy: EventMatchStrategy,
    boundary: ProtocolAEMHBoundary,
) -> _ReportedMatchOutcome:
    """Match one evidence record against reported AE/MH source records.

    Returns a match outcome with boundary/not_evaluable flags for partial-
    date or precision-insufficient cases.
    """
    any_boundary = False
    any_not_evaluable = False
    boundary_reason = ""
    ne_reason = ""

    ev_date = evidence.normalized_date()
    ev_concept = _concept(evidence)

    for rep in reported:
        # Concept match (caller-supplied equivalence, no project aliases).
        if not strategy.concepts_match(ev_concept, _concept(rep)):
            continue

        rep_date = rep.normalized_date()
        temporal = compare_partial_dates(ev_date, rep_date,
                                         strategy.temporal_tolerance)

        if not temporal.comparable:
            any_not_evaluable = True
            ne_reason = (
                f"concept matched but dates incomparable: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r} "
                f"at {temporal.shared_precision} precision "
                f"({temporal.uncertainty})")
            continue

        if temporal.within_tolerance and temporal.shared_precision == "day":
            return _ReportedMatchOutcome(
                matched=True, boundary=False, not_evaluable=False,
                reason=f"evidence matches reported {rep.role} "
                       f"at day precision",
                matched_record=rep)

        # Month/year precision within_tolerance means same period but
        # insufficient day-level detail to confirm the same event ->
        # boundary, not a clean match (matrix §3.8, §4 D01 "误报控制").
        if temporal.within_tolerance and temporal.shared_precision in (
                "month", "year"):
            any_boundary = True
            boundary_reason = (
                f"concept matched and same {temporal.shared_precision} "
                f"but insufficient day precision to confirm same event: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r}")
            continue

        # Comparable but not within tolerance -> could be a different event
        # or a boundary if precision is coarse.
        if temporal.shared_precision in ("year", "month"):
            any_boundary = True
            boundary_reason = (
                f"concept matched but dates only comparable at "
                f"{temporal.shared_precision} precision: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r}")
        # If day-precision and outside tolerance, it's a distinct event
        # (not a match, not a boundary) -- continue searching.

    if any_not_evaluable:
        return _ReportedMatchOutcome(
            matched=False, boundary=False, not_evaluable=True,
            reason=ne_reason)
    if any_boundary:
        return _ReportedMatchOutcome(
            matched=False, boundary=True, not_evaluable=False,
            reason=boundary_reason)
    return _ReportedMatchOutcome(
        matched=False, boundary=False, not_evaluable=False,
        reason="no concept-and-temporal match found among reported records")


# ---------------------------------------------------------------------------
# Journey marker construction
# ---------------------------------------------------------------------------

#: Mapping from semantic role to journey event category.
#: Categories are kept distinct (matrix §3.9, §4 D01 "输出"):
#: AE/MH/CM/IP/检查/住院/操作/症状 etc. are never conflated.
_ROLE_TO_JOURNEY_CATEGORY: Dict[str, str] = {
    "reported_ae": "ae",
    "reported_mh": "mh",
    "symptom_event": "symptom",
    "cm_indication": "cm",
    "lab_finding": "lab",
    "exam_finding": "exam",
    "healthcare_encounter": "hospitalization",
    "procedure": "procedure",
    "ip_action": "ip",
    "seriousness_clue": "seriousness",
    "death_event": "death",
    "visit": "visit",
}


def _journey_category(role: str) -> str:
    return _ROLE_TO_JOURNEY_CATEGORY.get(role, "other")


def _build_journey_marker(
    record: SemanticRecord,
    grading: MedicalGrading,
    unit_id: str,
    uncertainty: str = "",
    *,
    is_candidate: bool = False,
    is_boundary_support: bool = False,
) -> Dict[str, Any]:
    """Build one journey projection marker from a semantic record.

    This is projection *data*, not a UI.  The category is a stable
    engineering code; audience labels are produced in ``projection.py``.
    Risk-marker scoping flags (finding 8) are carried so the projection
    layer can mark only candidate, boundary-supporting or serious locators.
    Every marker carries the source ``unit_id`` (finding 6).
    """
    norm = record.normalized_date()
    is_serious = bool(
        grading.has_seriousness_clue
        or grading.monitoring_priority == MONITORING_PRIORITY_HIGH)
    return {
        "unit_id": unit_id,
        "category": _journey_category(record.role),
        "concept": record.concept,
        "role": record.role,
        "source_locator_id": record.locator.locator_id(),
        "record_id": record.locator.record_id,
        "temporal_anchor_raw": record.event_date_raw,
        "temporal_anchor_normalized": str(norm.normalized) if norm and norm.normalized else "",
        "temporal_precision": _precision_level(norm) if norm else "none",
        "visit_label": record.visit_label,
        "phase": record.phase,
        "intensity": grading.intensity,
        "intensity_scale": grading.intensity_scale,
        "seriousness_criteria": list(grading.seriousness_criteria),
        "monitoring_priority": grading.monitoring_priority,
        "ai_assertion": record.ai_assertion,
        "uncertainty": uncertainty or (norm.uncertainty if norm else ""),
        "is_candidate_locator": is_candidate,
        "is_boundary_support_locator": is_boundary_support,
        "is_serious_locator": is_serious,
    }

# ---------------------------------------------------------------------------
# NCS / alternative-diagnosis counterevidence (finding 6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _CounterevidenceAssessment:
    """Assessment of whether an evidence record is explained away by NCS
    or a confirmed alternative diagnosis (finding 6)."""

    is_combination_counterevidence: bool
    reason: str


def _assess_counterevidence(
    evidence: SemanticRecord,
    grading: MedicalGrading,
) -> _CounterevidenceAssessment:
    """Determine whether NCS or a confirmed alternative diagnosis explains
    away an evidence clue (finding 6).

    NCS is only combination counterevidence when there is no associated
    symptom, medical action/treatment, seriousness clue, or repeat
    worsening.  NCS alone must not become an absolute exclusion.  A
    confirmed alternative diagnosis may be counterevidence but must remain
    source-linked.
    """
    if evidence.has_alternative_diagnosis:
        return _CounterevidenceAssessment(
            is_combination_counterevidence=True,
            reason=(
                f"确认的替代诊断 {evidence.alternative_diagnosis!r} 可作为"
                f"排除依据，但须保留来源链接，不绝对排除"),
        )

    if evidence.is_ncs:
        has_confounder = (
            evidence.role == "symptom_event"
            or evidence.has_medical_action
            or grading.has_seriousness_clue
            or grading.monitoring_priority == MONITORING_PRIORITY_HIGH
            or evidence.intensity.strip().lower() in (
                "severe", "grade 3", "grade4", "grade5",
                "grade 3", "grade 4", "grade 5")
        )
        if has_confounder:
            return _CounterevidenceAssessment(
                is_combination_counterevidence=False,
                reason=(
                    "NCS 不能单独作为排除依据：存在相关症状、医学处置、"
                    "严重性线索或恶化"),
            )
        return _CounterevidenceAssessment(
            is_combination_counterevidence=True,
            reason="明确 NCS 且无相关症状/处置/严重性/恶化，可作为组合反证",
        )

    return _CounterevidenceAssessment(
        is_combination_counterevidence=False, reason="")


# ---------------------------------------------------------------------------
# Query construction helpers (finding 9)
# ---------------------------------------------------------------------------
def _query_basis_text(
    boundary: ProtocolAEMHBoundary,
    strategy: EventMatchStrategy,
) -> str:
    """Audience-readable Query basis identifying the versioned protocol
    boundary and match strategy (finding 9).

    Returns the basis text WITHOUT the ``依据：`` prefix; the projection
    layer adds exactly one ``依据：`` prefix (finding 5)."""
    return (
        f"方案 AE/MH 报告边界 {boundary.boundary_id} "
        f"(v{boundary.version})，事件匹配策略 {strategy.strategy_id} "
        f"(v{strategy.version})")


def _query_finding_text(
    subject_ref: str,
    concept: str,
) -> str:
    """Query finding uses concrete medical wording (finding 9)."""
    return (
        f"受试者 {subject_ref} 的 {concept} 在当前 AE/MH 中未发现对应记录，"
        f"可能为 AE/MH 漏报")


def _query_action_text() -> str:
    return "请核实是否为 AE/MH 漏报，并补充或说明原始记录"
