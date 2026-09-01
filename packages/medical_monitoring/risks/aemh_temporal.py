"""Protocol-boundary and partial-date evaluation for AE/MH."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..intelligence.normalization import NormalizedValue
from .aemh_types import (
    ProtocolAEMHBoundary, SemanticRecordSet, TemporalTolerance,
)

# ---------------------------------------------------------------------------
# Resolved protocol anchors + boundary classification (finding 2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolAnchorDates:
    """Resolved actual anchor dates for one subject under a
    :class:`ProtocolAEMHBoundary`.

    ``start_norm`` and ``end_norm`` are R3-normalized partial dates
    resolved by matching the boundary's anchor descriptors to the
    subject's ``temporal_anchor`` records.  ``resolved`` is ``True`` only
    when both anchors are available and normalizable.
    """

    start_descriptor: str
    end_descriptor: str
    start_norm: Optional[NormalizedValue]
    end_norm: Optional[NormalizedValue]
    start_raw: str = ""
    end_raw: str = ""

    @property
    def resolved(self) -> bool:
        return (
            self.start_norm is not None
            and self.end_norm is not None
            and self.start_norm.quality not in ("unsupported", "missing")
            and self.end_norm.quality not in ("unsupported", "missing")
            and bool(self.start_norm.normalized)
            and bool(self.end_norm.normalized)
        )

    def unresolved_reason(self) -> str:
        if self.start_norm is None or not self.start_norm.normalized or \
                self.start_norm.quality in ("unsupported", "missing"):
            return (
                f"报告起始锚点 {self.start_descriptor!r} 未解析到有效日期")
        if self.end_norm is None or not self.end_norm.normalized or \
                self.end_norm.quality in ("unsupported", "missing"):
            return (
                f"报告截止锚点 {self.end_descriptor!r} 未解析到有效日期")
        return ""


@dataclass(frozen=True)
class BoundaryClassification:
    """Outcome of classifying an event date against the resolved protocol
    boundary (finding 2).

    * ``inside``: event is strictly inside the reporting window.
    * ``outside``: event is strictly outside at shared precision.
    * ``boundary``: event date precision is insufficient or crosses a
      boundary edge (e.g., month-only date that could be inside or outside).
    * ``not_evaluable``: anchors missing/invalid or comparison impossible.
    """

    classification: str  # "inside" | "outside" | "boundary" | "not_evaluable"
    reason: str = ""
    shared_precision: str = "none"

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "reason": self.reason,
            "shared_precision": self.shared_precision,
        }


_PREC_ORDER = {"day": 3, "month": 2, "year": 1, "none": 0}
_ORDER_PREC = {0: "none", 1: "year", 2: "month", 3: "day"}


def _resolve_protocol_anchors(
    record_set: "SemanticRecordSet",
    boundary: ProtocolAEMHBoundary,
) -> ProtocolAnchorDates:
    """Resolve the boundary's anchor descriptors to actual subject dates
    by matching ``anchor_descriptor`` on ``temporal_anchor`` records
    (finding 2)."""
    start_norm: Optional[NormalizedValue] = None
    end_norm: Optional[NormalizedValue] = None
    start_raw = ""
    end_raw = ""
    for rec in record_set.temporal_anchor_records:
        desc = rec.anchor_descriptor.strip()
        if not desc:
            continue
        if desc == boundary.reporting_start_anchor and not start_norm:
            start_raw = rec.event_date_raw
            start_norm = rec.normalized_date()
        elif desc == boundary.reporting_end_anchor and not end_norm:
            end_raw = rec.event_date_raw
            end_norm = rec.normalized_date()
    return ProtocolAnchorDates(
        start_descriptor=boundary.reporting_start_anchor,
        end_descriptor=boundary.reporting_end_anchor,
        start_norm=start_norm,
        end_norm=end_norm,
        start_raw=start_raw,
        end_raw=end_raw,
    )


def classify_event_against_boundary(
    event_date: Optional[NormalizedValue],
    anchors: ProtocolAnchorDates,
) -> BoundaryClassification:
    """Classify an event date against the resolved protocol boundary.

    Exact inside/outside comparisons affect applicability; partial dates
    crossing a boundary yield ``boundary``; missing/invalid/incomparable
    anchors yield ``not_evaluable``; no silent first/last-day imputation
    (finding 2).
    """
    if not anchors.resolved:
        return BoundaryClassification(
            classification="not_evaluable",
            reason=anchors.unresolved_reason(),
            shared_precision="none")

    if event_date is None or not event_date.normalized:
        return BoundaryClassification(
            classification="not_evaluable",
            reason="事件日期缺失，无法与方案报告窗口比较",
            shared_precision="none")
    if event_date.quality in ("unsupported", "missing"):
        return BoundaryClassification(
            classification="not_evaluable",
            reason=f"事件日期质量不足 (quality={event_date.quality})",
            shared_precision="none")

    start = anchors.start_norm  # type: ignore[union-attr]
    end = anchors.end_norm      # type: ignore[union-attr]
    ev_norm = str(event_date.normalized)
    start_norm = str(start.normalized)
    end_norm = str(end.normalized)

    ev_prec = _precision_level(event_date)
    start_prec = _precision_level(start)
    end_prec = _precision_level(end)

    min_prec_order = min(
        _PREC_ORDER[ev_prec],
        _PREC_ORDER[start_prec],
        _PREC_ORDER[end_prec],
    )
    if min_prec_order == 0:
        return BoundaryClassification(
            classification="not_evaluable",
            reason="无共享精度，无法比较事件与方案报告窗口",
            shared_precision="none")
    min_prec = _ORDER_PREC[min_prec_order]

    def _cmp(a: str, b: str, prec: str) -> int:
        n = {"year": 4, "month": 7, "day": 10}.get(prec, 0)
        sa, sb = a[:n], b[:n]
        if sa < sb:
            return -1
        if sa > sb:
            return 1
        return 0

    cmp_start = _cmp(ev_norm, start_norm, min_prec)
    cmp_end = _cmp(ev_norm, end_norm, min_prec)

    # Strictly inside at shared precision.  A first occurrence exactly on
    # the study/reporting start cannot be ordered relative to the anchor
    # without time-of-day or explicit pre-existing/worsening context, so it
    # is a boundary even when both values are day precision (matrix §4 D01).
    if cmp_start >= 0 and cmp_end <= 0:
        if cmp_start == 0:
            return BoundaryClassification(
                classification="boundary",
                reason=(
                    "事件恰位于方案研究起点，缺少日内先后或既往存在/"
                    "新发恶化信息，暂无法确定是否属于研究期事件"),
                shared_precision=min_prec)
        # End-edge ambiguity remains precision-dependent: a day-precision
        # reporting cutoff is inclusive unless the protocol says otherwise,
        # while a month/year value cannot prove window membership.
        if min_prec in ("year", "month") and cmp_end == 0:
            return BoundaryClassification(
                classification="boundary",
                reason=(
                    f"事件在 {min_prec} 精度上恰位于方案报告窗口边界，"
                    f"无法确定是否在窗口内"),
                shared_precision=min_prec)
        return BoundaryClassification(
            classification="inside",
            reason="事件在方案报告窗口内",
            shared_precision=min_prec)

    # Strictly outside at shared precision.
    if cmp_start < 0 or cmp_end > 0:
        # If the event is coarser than the boundary and same year as the
        # edge, it could cross -> boundary.
        if ev_prec in ("year", "month") and (
                start_prec == "day" or end_prec == "day"):
            edge_same = False
            if cmp_start < 0 and ev_norm[:4] == start_norm[:4]:
                edge_same = True
            if cmp_end > 0 and ev_norm[:4] == end_norm[:4]:
                edge_same = True
            if edge_same:
                return BoundaryClassification(
                    classification="boundary",
                    reason=(
                        f"事件精度 ({ev_prec}) 不足以确定是否跨过"
                        f"方案报告窗口边界"),
                    shared_precision=min_prec)
        return BoundaryClassification(
            classification="outside",
            reason="事件在方案报告窗口外",
            shared_precision=min_prec)

    # Should not reach here, but fail safe.
    return BoundaryClassification(
        classification="boundary",
        reason="无法确定事件是否在方案报告窗口内",
        shared_precision=min_prec)


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TemporalComparison:
    """Outcome of comparing two R3-normalized partial dates.

    Comparison is only valid on the **shared precision** of both dates.
    If shared precision is insufficient to determine ordering or window
    membership, ``comparable`` is ``False`` and the caller must fall back
    to ``boundary`` or ``not_evaluable`` (matrix §3.8).
    """

    comparable: bool
    same_period: bool
    within_tolerance: bool
    shared_precision: str  # "day" | "month" | "year" | "none"
    uncertainty: str

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "comparable": self.comparable,
            "same_period": self.same_period,
            "within_tolerance": self.within_tolerance,
            "shared_precision": self.shared_precision,
            "uncertainty": self.uncertainty,
        }


def _precision_level(norm: Optional[NormalizedValue]) -> str:
    """Return the precision level of a normalized date: day/month/year/none."""
    if norm is None or not norm.normalized:
        return "none"
    normalized = str(norm.normalized)
    parts = normalized.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if len(parts) >= 1 and len(parts[0]) == 4:
        return "year"
    return "none"


def _shared_precision(a: str, b: str) -> str:
    """Return the finest precision shared by two precision levels."""
    order = {"day": 3, "month": 2, "year": 1, "none": 0}
    return a if order[a] <= order[b] else b


def compare_partial_dates(
    date_a: Optional[NormalizedValue],
    date_b: Optional[NormalizedValue],
    tolerance: TemporalTolerance,
) -> TemporalComparison:
    """Compare two R3-normalized partial dates on their shared precision.

    Fails closed: if either date is missing/unsupported, or if the shared
    precision is insufficient to determine whether the dates are within
    tolerance, ``comparable`` is ``False``.
    """
    if date_a is None or date_b is None:
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="one or both dates missing")
    if date_a.quality in ("unsupported", "missing"):
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty=f"date_a quality={date_a.quality}")
    if date_b.quality in ("unsupported", "missing"):
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty=f"date_b quality={date_b.quality}")

    norm_a = str(date_a.normalized) if date_a.normalized else ""
    norm_b = str(date_b.normalized) if date_b.normalized else ""
    if not norm_a or not norm_b:
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="one or both normalized values empty")

    prec_a = _precision_level(date_a)
    prec_b = _precision_level(date_b)
    shared = _shared_precision(prec_a, prec_b)

    if shared == "none":
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="no shared date precision")

    # Compare at the shared precision level.
    if shared == "year":
        same = norm_a[:4] == norm_b[:4]
        return TemporalComparison(
            comparable=True, same_period=same, within_tolerance=same,
            shared_precision="year",
            uncertainty="compared at year precision only")

    if shared == "month":
        same = norm_a[:7] == norm_b[:7]
        return TemporalComparison(
            comparable=True, same_period=same, within_tolerance=same,
            shared_precision="month",
            uncertainty="compared at month precision only")

    # shared == "day": full comparison possible.
    if norm_a[:10] == norm_b[:10]:
        if not tolerance.same_day:
            return TemporalComparison(
                comparable=True, same_period=True, within_tolerance=False,
                shared_precision="day",
                uncertainty="same-day matching disabled by strategy")
        return TemporalComparison(
            comparable=True, same_period=True, within_tolerance=True,
            shared_precision="day", uncertainty="")

    # Different days: apply tolerance if provided.
    if tolerance.tolerance_days is not None:
        import datetime
        try:
            da = datetime.date.fromisoformat(norm_a[:10])
            db = datetime.date.fromisoformat(norm_b[:10])
            delta = abs((da - db).days)
            within = delta <= tolerance.tolerance_days
            return TemporalComparison(
                comparable=True, same_period=False,
                within_tolerance=within,
                shared_precision="day",
                uncertainty=f"day delta={delta}, "
                            f"tolerance={tolerance.tolerance_days}")
        except (ValueError, TypeError):
            return TemporalComparison(
                comparable=False, same_period=False, within_tolerance=False,
                shared_precision="day",
                uncertainty="could not parse day-precision dates for delta")
    # No tolerance: different days are not within tolerance.
    return TemporalComparison(
        comparable=True, same_period=False, within_tolerance=False,
        shared_precision="day",
        uncertainty="different days, no tolerance applied")
