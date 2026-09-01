"""IP window, assignment and exposure-day computation."""

from __future__ import annotations

from .ip_types import *
from .ip_types import (
    _prec_rank,
    _nv_precision,
    _to_day,
    _day_range,
)

# ---------------------------------------------------------------------------
# Window-overlap comparison (frozen D03 §7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _WindowOverlap:
    inside: bool
    outside: bool
    possibly_overlap: bool
    comparable: bool
    boundary_reason: str


def _compare_windows(
    interval: IPWindowDescriptor,
    win_start: str, win_end: str,
    start_inclusive: Optional[bool],
    end_inclusive: Optional[bool],
    *,
    containment: bool = True,
) -> _WindowOverlap:
    """Compare an episode/action window against a control window.

    ``containment=True`` (rule applicability): the episode/action must be
    fully inside the control window; a partial overlap is boundary.
    ``containment=False`` (algorithm computation window): any definite
    overlap evaluates; only a fully disjoint window is not_applicable.

    Full-day precision with explicit inclusivity determines overlap.
    Endpoint equality with unstated inclusivity is boundary.  Partial
    month/year dates that possibly overlap are boundary.  Incomparable
    anchors are not_evaluable.
    """
    span_start = interval.normalized_span_start()
    if span_start is None:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False, boundary_reason="开始日期缺失或无法解析")
    rw_start = (normalize_partial_date(win_start)
                if win_start.strip() else None)
    rw_end = (normalize_partial_date(win_end)
              if win_end.strip() else None)
    if rw_start is None and rw_end is None:
        return _WindowOverlap(
            inside=True, outside=False, possibly_overlap=False,
            comparable=True, boundary_reason="")
    span_end = interval.normalized_span_end()
    if span_end is None and not interval.span_ongoing:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="结束日期缺失；可能落入控制窗口")
    p_start = _nv_precision(span_start)
    p_end = _nv_precision(span_end)
    p_rw_start = _nv_precision(rw_start)
    p_rw_end = _nv_precision(rw_end)
    min_prec = min(_prec_rank(p_start), _prec_rank(p_end),
                   _prec_rank(p_rw_start), _prec_rank(p_rw_end))
    if min_prec < 3:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason=(
                f"部分日期精度（{p_start}/{p_end}/{p_rw_start}/{p_rw_end}）；"
                f"可能落入控制窗口"))
    cs = _to_day(span_start)
    ce = _to_day(span_end) if span_end else None
    rws = _to_day(rw_start) if rw_start else None
    rwe = _to_day(rw_end) if rw_end else None
    if cs is None or (span_end is not None and ce is None) or (
            rw_start is not None and rws is None) or (
            rw_end is not None and rwe is None):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False, boundary_reason="全日日期无法解析")
    # Endpoint equality with unstated inclusivity is ambiguous.
    if (start_inclusive is None and rws is not None and cs == rws
            and (containment or rwe is None or ce is None or ce <= rws)):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="开始日期恰在控制窗口起点；端点包含关系未声明")
    if (end_inclusive is None and rwe is not None and ce is not None
            and ce == rwe
            and (containment or rws is None or cs >= rwe)):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="结束日期恰在控制窗口终点；端点包含关系未声明")
    # Exclusive endpoints: contact at the excluded endpoint is disjoint.
    if (rws is not None and start_inclusive is False and cs == rws
            and ce == rws):
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    if (rwe is not None and end_inclusive is False and cs == rwe
            and ce == rwe):
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    # Definite disjointness.
    definitely_outside = False
    if rws is not None and ce is not None:
        definitely_outside = (ce < rws
                              or (ce == rws and start_inclusive is False))
    if rwe is not None:
        definitely_outside = definitely_outside or (
            cs > rwe or (cs == rwe and end_inclusive is False))
    if definitely_outside:
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    if containment:
        after_start = True
        if rws is not None:
            after_start = (cs >= rws if start_inclusive is not False
                           else cs > rws)
        before_end = True
        if rwe is not None and ce is not None:
            before_end = (ce <= rwe if end_inclusive is not False
                          else ce < rwe)
        if after_start and before_end:
            return _WindowOverlap(
                inside=True, outside=False, possibly_overlap=False,
                comparable=True, boundary_reason="")
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True, boundary_reason="区间部分落入控制窗口")
    # Overlap mode: any definite intersection evaluates.
    return _WindowOverlap(
        inside=True, outside=False, possibly_overlap=False,
        comparable=True, boundary_reason="")


def _episode_window(episode: IPExposureEpisode) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        applicable_phase=episode.study_phase)


def _rule_window(episode: IPExposureEpisode,
                 rule: ProtocolExposureRule) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        window_start=rule.window_start, window_end=rule.window_end,
        window_start_inclusive=rule.window_start_inclusive,
        window_end_inclusive=rule.window_end_inclusive,
        applicable_phase=episode.study_phase)


def _algorithm_window(episode: IPExposureEpisode,
                      algorithm: AdherenceAlgorithm) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        window_start=algorithm.window_start,
        window_end=algorithm.window_end,
        window_start_inclusive=algorithm.window_start_inclusive,
        window_end_inclusive=algorithm.window_end_inclusive,
        applicable_phase=episode.study_phase)


# ---------------------------------------------------------------------------
# Assignment binding (frozen D03 §4 steps 1-3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssignmentResolution:
    """Outcome of binding one episode to a planned treatment assignment."""

    status: str                       # bound | missing | ambiguous
    assignment: Optional[PlannedTreatmentAssignment] = None
    reason: str = ""

    @property
    def is_bound(self) -> bool:
        return self.status == RESOLUTION_BOUND


def resolve_episode_assignment(
    *,
    episode: IPExposureEpisode,
    assignments: Sequence[PlannedTreatmentAssignment],
    binding_mapping: Optional[AssignmentBindingMapping] = None,
) -> AssignmentResolution:
    """Bind an episode to a unique assignment (frozen D03 §4 steps 1-3).

    1. A stable accepted direct/derived link is preferred; the linked
       assignment must exist and share subject + site.
    2. Without a link, only an active mapping that deterministically
       yields exactly one subject+site+role+phase+window candidate may
       derive a binding.
    3. Zero candidates -> missing (not_evaluable); two or more feasible
       candidates -> ambiguous (boundary/not_evaluable).  The kernel never
       picks by drug name, nearest date or input order.
    """
    if not isinstance(episode, IPExposureEpisode):
        raise IPSliceError("episode must be an IPExposureEpisode")
    if episode.assignment_link_status in (ASSIGNMENT_LINK_DIRECT,
                                          ASSIGNMENT_LINK_DERIVED):
        if not episode.assignment_id.strip():
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason="episode 声称存在 assignment 链接但缺少 assignment_id")
        linked = [a for a in assignments
                  if a.assignment_id == episode.assignment_id]
        if not linked:
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason=(f"assignment 链接 {episode.assignment_id!r} 未找到，"
                        f"无法唯一绑定"))
        if len(linked) > 1:
            return AssignmentResolution(
                status=RESOLUTION_AMBIGUOUS,
                reason=(f"assignment 链接 {episode.assignment_id!r} 存在多条"
                        f"记录，无法唯一绑定"))
        candidate = linked[0]
        if (candidate.subject_ref != episode.subject_ref
                or candidate.site_ref != episode.site_ref):
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason=("assignment 链接与 episode 的受试者/中心不一致，"
                        "无法绑定"))
        return AssignmentResolution(
            status=RESOLUTION_BOUND, assignment=candidate)
    # No direct link: derived binding only under an active mapping.
    if binding_mapping is None or not binding_mapping.allow_derived_binding:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason="episode 无直接 assignment 链接且无允许派生的版本化映射")
    keyed_candidates = [
        a for a in assignments
        if (a.subject_ref == episode.subject_ref
            and a.site_ref == episode.site_ref
            and a.treatment_role_token == episode.actual_treatment_role
            and a.study_phase == episode.study_phase)]
    if not keyed_candidates:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason=("没有满足 subject+site+role+phase 的 assignment 候选，"
                    "无法确定性绑定"))

    candidates: List[PlannedTreatmentAssignment] = []
    unresolved_ids: List[str] = []
    episode_window = _episode_window(episode)
    for candidate in keyed_candidates:
        overlap = _compare_windows(
            episode_window,
            candidate.planned_start,
            candidate.planned_end,
            True,
            True,
            containment=True,
        )
        if overlap.inside:
            candidates.append(candidate)
        elif not overlap.outside:
            unresolved_ids.append(candidate.assignment_id)

    if unresolved_ids:
        ids = sorted(a.assignment_id for a in candidates) + sorted(
            unresolved_ids)
        return AssignmentResolution(
            status=RESOLUTION_AMBIGUOUS,
            reason=(f"assignment 候选 {ids} 的时间窗存在部分日期、缺失或"
                    "边界重叠，无法证明唯一适用窗口"))
    if not candidates:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason=("满足 subject+site+role+phase 的 assignment 均与"
                    "episode 时间窗明确不相交，无法确定性绑定"))
    if len(candidates) > 1:
        ids = sorted(a.assignment_id for a in candidates)
        return AssignmentResolution(
            status=RESOLUTION_AMBIGUOUS,
            reason=(f"存在多个可适用 assignment 候选 {ids}，不得按药名、"
                    f"最近日期或输入顺序选择"))
    return AssignmentResolution(status=RESOLUTION_BOUND, assignment=candidates[0])


# ---------------------------------------------------------------------------
# Actual exposure days (frozen D03 §6.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExposureDayComputation:
    """Actual exposure day set derived ONLY from accepted occurrences.

    ``day_set`` holds the unique full-day dates with proven dosing;
    ``status`` is ``complete``/``no_occurrence``/``ambiguous``/``boundary``.
    The episode span is carried for display but never used as dosing proof.
    """

    day_set: Tuple[str, ...]
    status: str
    span_start: str = ""
    span_end: str = ""
    reason: str = ""

    @property
    def actual_exposure_days(self) -> int:
        return len(self.day_set)


def compute_actual_exposure_days(
    *,
    episode: IPExposureEpisode,
    occurrences: Sequence[ExposureOccurrence],
    policy: ExposureAggregationPolicy,
) -> ExposureDayComputation:
    """Compute the actual exposure day set for one episode (§6.1).

    * Dedup by full locator; identical rows collapse, conflicting content
      under one locator or one stable event key with different accepted
      revisions is ambiguous (fail-closed).
    * Single occurrences contribute their explicit date; intervals expand
      to a day set only with explicit continuous-daily semantics AND
      policy permission; otherwise they contribute only their explicit
      endpoints.
    * Same-role same-dose same-semantics overlapping intervals union their
      day sets (never sum interval lengths); different dose/role overlaps
      follow the policy (union_fail -> ambiguous, boundary -> boundary,
      split_at_change -> counted once with the versioned priority rule).
    * Zero occurrences is ``no_occurrence``; the span never implies days.
    """
    episode_occs = [o for o in occurrences
                    if o.episode_key == episode.episode_key]
    # -- dedup / revision selection --------------------------------------
    by_locator: Dict[str, List[ExposureOccurrence]] = {}
    for occ in episode_occs:
        by_locator.setdefault(occ.source_locator.locator_id(), []).append(occ)
    chosen: List[ExposureOccurrence] = []
    for loc_id, rows in by_locator.items():
        payloads = {content_hash((
            occ.date_start, occ.date_end, occ.continuous_daily, occ.dose,
            occ.dose_unit, occ.route, occ.frequency, occ.accepted_revision,
            occ.accepted_revision_hash)) for occ in rows}
        if len(payloads) > 1:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一来源定位出现内容不同的记录，无法确定当前 "
                        "accepted 行"))
        chosen.append(rows[0])
    # Stable event key (table_semantic:record_id) revision conflicts.
    by_event: Dict[str, List[ExposureOccurrence]] = {}
    for occ in chosen:
        by_event.setdefault(
            f"{occ.source_locator.table_semantic}:{occ.source_locator.record_id}",
            []).append(occ)
    accepted: List[ExposureOccurrence] = []
    for key, rows in by_event.items():
        revisions = {r.accepted_revision for r in rows}
        if len(revisions) > 1:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一稳定来源事件存在多个不同 accepted revision，"
                        "无法确定当前 accepted 行"))
        accepted.append(rows[0])
    if not accepted:
        return ExposureDayComputation(
            day_set=(), status=DAY_STATUS_NO_OCCURRENCE,
            span_start=episode.span_start, span_end=episode.span_end,
            reason=("未找到该 episode 的给药记录；不得从治疗跨度推导实际"
                    "给药日，也不得推断漏服"))

    days: Set[Any] = set()
    day_fingerprint: Dict[Any, Set[str]] = {}
    day_interval_covered: Set[Any] = set()
    conflict_reason = ""
    for occ in accepted:
        start = normalize_partial_date(occ.date_start)
        if start is None or _nv_precision(start) != "day":
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=(f"给药记录 {occ.occurrence_id!r} 日期缺失或精度不足，"
                        f"无法确定实际给药日"))
        d_start = _to_day(start)
        d_end = d_start
        if occ.date_end.strip() and occ.date_end != occ.date_start:
            end = normalize_partial_date(occ.date_end)
            if end is None or _nv_precision(end) != "day":
                return ExposureDayComputation(
                    day_set=(), status=DAY_STATUS_AMBIGUOUS,
                    span_start=episode.span_start, span_end=episode.span_end,
                    reason=(f"给药记录 {occ.occurrence_id!r} 区间终点缺失或"
                            f"精度不足"))
            d_end = _to_day(end)
        # A true continuous-dosing interval expands to its full day set;
        # every other occurrence contributes only its explicit dates.
        is_expanded_interval = (
            d_end != d_start and occ.continuous_daily
            and policy.continuous_interval_expansion_allowed)
        if d_end == d_start:
            explicit_days = [d_start]
        elif is_expanded_interval:
            explicit_days = _day_range(d_start, d_end)
        else:
            # Interval without continuous-daily declaration contributes
            # only its explicit endpoints (§6.1).
            explicit_days = [d_start, d_end]
        fingerprint = "|".join((
            occ.dose or "-", occ.dose_unit or "-", occ.route or "-",
            occ.frequency or "-", episode.source_semantics,
        ))
        for day in explicit_days:
            days.add(day)
            day_fingerprint.setdefault(day, set()).add(fingerprint)
            if is_expanded_interval:
                day_interval_covered.add(day)
    # -- overlap conflict handling ----------------------------------------
    # Different-dose/role overlaps matter only when a continuous interval
    # covers the day; several single-dose occurrences on the same day are a
    # legitimate multi-dose day (counted once for day purposes, §6.1).
    policy_conflict = False
    for day, fps in day_fingerprint.items():
        if len(fps) > 1 and day in day_interval_covered:
            policy_conflict = True
            break
    if policy_conflict:
        if policy.overlap_conflict_policy == OVERLAP_POLICY_UNION_FAIL:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一日存在不同剂量/单位/途径/频次或来源语义的重叠"
                        "连续给药区间，聚合策略不允许合并"))
        if policy.overlap_conflict_policy == OVERLAP_POLICY_BOUNDARY:
            return ExposureDayComputation(
                day_set=tuple(sorted(day.isoformat() for day in days)),
                status=DAY_STATUS_BOUNDARY,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一日存在不同剂量/角色重叠的连续给药区间，两个可行"
                        "解释均有来源支持"))
        # split_at_change: day counted once; the versioned priority rule
        # (policy.split_priority_lineage) resolves dose identity at change
        # points.  The day set itself is the union.
        conflict_reason = (
            "重叠给药日按版本化优先级规则在变化点拆分，实际给药日按日去重")
    return ExposureDayComputation(
        day_set=tuple(sorted(day.isoformat() for day in days)),
        status=DAY_STATUS_COMPLETE,
        span_start=episode.span_start, span_end=episode.span_end,
        reason=conflict_reason)
