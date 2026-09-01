"""IP role, plan/actual and adherence unit evaluation."""

from __future__ import annotations

from .ip_types import *
from .ip_types import (
    _prec_rank,
    _nv_precision,
    _to_day,
    _day_range,
)
from .ip_resolution import *
from .ip_resolution import (
    _WindowOverlap,
    _compare_windows,
    _episode_window,
    _rule_window,
    _algorithm_window,
)
from .ip_results import *
from .ip_results import (
    _d03_risk_classifier,
    _d03_risk_scope,
    _build_d03_risk_identity,
    _d03_identity_detail,
    _build_d03_candidate,
    _expected_set_hash,
    _control_token_for,
    _make_evidence_item,
    _dedup_locator_ids,
    _make_source_record_ref,
    _canonical_text,
    _canonical_dose,
    _canonical_record_value,
    _journey_marker,
    _display_label,
    _query_text,
    _build_query_ref,
    _build_positive_result,
    _build_boundary_result,
    _not_evaluable_result,
    _negative_result,
)

# ---------------------------------------------------------------------------
# Role coverage gate (frozen D03 §3.1)
# ---------------------------------------------------------------------------

def _required_roles_for(
    expanded: IPUnitExpanded,
    role_coverage: Mapping[str, bool],
) -> Optional[str]:
    """Return a Chinese gap reason when a required semantic role is not
    covered, else None.  Fail-closed: roles absent from ``role_coverage``
    are not covered."""
    required: Set[str] = set(REQUIRED_IP_ROLES)
    control = expanded.control_item
    if control == CONTROL_PLAN_ACTUAL:
        required.add("planned_treatment")
    elif control == CONTROL_ROLE_PHASE:
        required.add("planned_treatment")
        required.add("study_phase")
        if (expanded.assignment is not None
                and expanded.assignment.randomization_token.strip()):
            required.add("randomization")
    elif control == CONTROL_ADHERENCE:
        required.add("planned_treatment")
        required.add("study_phase")
    elif control == CONTROL_ALLOWED_ACTION:
        required.add("planned_treatment")
        required.add("ip_action_reason")
    elif control == CONTROL_MEDICAL_ACTION:
        required.add("planned_treatment")
        required.add("ip_action_reason")
    elif control == CONTROL_ACCOUNTABILITY:
        required.add("ip_dispense")
        required.add("ip_return")
    missing = sorted(role for role in required
                     if not role_coverage.get(role, False))
    if not missing:
        return None
    labels = "、".join(IP_ROLE_LABELS.get(role, role) for role in missing)
    return f"必需来源角色覆盖不完整（{labels}），无法评价"


def _audience_suffix_for(expanded: "IPUnitExpanded") -> str:
    control = expanded.control_item
    return {
        CONTROL_PLAN_ACTUAL: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH],
        CONTROL_ROLE_PHASE: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH],
        CONTROL_ADHERENCE: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
        CONTROL_ALLOWED_ACTION: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
        CONTROL_MEDICAL_ACTION: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
        CONTROL_ACCOUNTABILITY: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
    }[control]


def _binding_gate_result(
    *, project_id: str, expanded: "IPUnitExpanded", unit_id: str,
    snapshot_id: str, rule_lineage: str,
) -> Optional[IPUnitResult]:
    """Terminal result when the assignment binding failed.

    Zero candidates -> not_evaluable; two or more feasible candidates ->
    boundary (both have source support; the kernel must not choose).
    """
    episode = expanded.episode
    if expanded.resolution.status == RESOLUTION_MISSING:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=expanded.resolution.reason, rule_lineage=rule_lineage)
    if expanded.resolution.status == RESOLUTION_AMBIGUOUS:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=expanded.resolution.reason,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=_audience_suffix_for(expanded))
    return None


# ---------------------------------------------------------------------------
# Unit-level evaluation: role_phase
# ---------------------------------------------------------------------------

def _evaluate_role_phase_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    assignment = expanded.assignment
    if not episode.role_confirmed:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际治疗角色未确认，无法核对治疗分组或阶段",
            rule_lineage=rule_lineage)
    if not episode.phase_confirmed or not episode.study_phase.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="研究阶段缺失或未确认，无法核对治疗分组或阶段",
            rule_lineage=rule_lineage)
    mismatches: List[str] = []
    if (episode.actual_treatment_role.strip()
            != assignment.treatment_role_token.strip()):
        mismatches.append(
            f"实际治疗角色 {episode.actual_treatment_role} 与分组角色 "
            f"{assignment.treatment_role_token} 不一致")
    if episode.study_phase.strip() != assignment.study_phase.strip():
        mismatches.append(
            f"实际研究阶段 {episode.study_phase} 与分组阶段 "
            f"{assignment.study_phase} 不一致")
    if not mismatches:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason="实际治疗角色与研究阶段与已确认分组一致")
    match_reason = "；".join(mismatches)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=(
            (assignment.source_locator,) if assignment.source_locator else ()))


# ---------------------------------------------------------------------------
# Unit-level evaluation: plan_actual
# ---------------------------------------------------------------------------

def _rule_phase_applicability(
    *, episode: IPExposureEpisode, rule: ProtocolExposureRule,
    unit_id: str, rule_lineage: str,
) -> Optional[IPUnitResult]:
    """Return a terminal NA/NE result when the rule does not apply, else
    None.  Confirmed phase outside applicability is not_applicable; every
    unconfirmed/missing phase state is not_evaluable."""
    if rule.applicable_phases:
        if not episode.phase_confirmed or not episode.study_phase.strip():
            note = ("研究阶段缺失或为空，无法判定方案规则适用性"
                    if not episode.study_phase.strip()
                    else f"研究阶段 {episode.study_phase!r} 未获确认，"
                         f"无法判定方案规则适用性")
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=note,
                rule_lineage=rule_lineage)
        if episode.study_phase.strip() not in rule.applicable_phases:
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
    if rule.applicable_treatment_role:
        if not episode.role_confirmed:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="实际治疗角色未确认，无法判定方案规则适用性",
                rule_lineage=rule_lineage)
        if (episode.actual_treatment_role.strip()
                != rule.applicable_treatment_role.strip()):
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
    return None


def _evaluate_plan_actual_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    occurrences: Sequence[ExposureOccurrence],
    aggregation_policy: Optional[ExposureAggregationPolicy],
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    rule = expanded.rule
    gate = _rule_phase_applicability(
        episode=episode, rule=rule, unit_id=unit_id,
        rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    # Window applicability: a determinate overlap evaluates; a fully
    # disjoint episode is not_applicable; possible overlap is boundary
    # (frozen D03 §7).  Out-of-window dosing surfaces via occurrence days.
    overlap = _compare_windows(
        expanded.window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive,
        containment=False)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage)
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH])
    # Disclosure gate: dose/form comparison needs dose disclosure (F-07).
    compares_dose = any(f in ("dose", "dosage_form")
                        for f in rule.compare_fields)
    if compares_dose and not episode.dose_disclosed:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="需要核对剂量/剂型身份但该身份在当前披露范围不可用",
            rule_lineage=rule_lineage)
    # Field comparison.
    mismatches: List[str] = []
    for fname in rule.compare_fields:
        actual = _canonical_record_value(fname, getattr(episode, fname))
        planned = _canonical_record_value(
            fname, getattr(rule, f"planned_{fname}"))
        if actual is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=f"实际{_field_label(fname)}缺失或精度不足，无法与方案"
                       f"计划可靠比较",
                rule_lineage=rule_lineage)
        if planned is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=f"方案计划{_field_label(fname)}缺失，无法可靠比较",
                rule_lineage=rule_lineage)
        if actual != planned:
            mismatches.append(
                f"实际{_field_label(fname)} {getattr(episode, fname)} 与计划"
                f" {getattr(rule, f'planned_{fname}')} 不一致")
    # Window mismatch via occurrence days outside the planned dosing window.
    window_violations: List[str] = []
    if aggregation_policy is not None and rule.window_start.strip():
        occ_days = _occurrence_days_in_rule_window(
            episode=episode, occurrences=occurrences,
            rule=rule, policy=aggregation_policy)
        if occ_days is not None:
            window_violations = occ_days
    if window_violations:
        mismatches.append(
            "存在给药日落在方案计划给药窗口之外："
            + "、".join(sorted(window_violations)[:3]))
    if not mismatches:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason="实际给药与方案计划在剂量、剂型、途径、频次和窗口上一致")
    match_reason = "；".join(mismatches)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=())


_FIELD_LABELS: Dict[str, str] = {
    "dose": "剂量", "dose_unit": "剂量单位", "dosage_form": "剂型",
    "route": "给药途径", "frequency": "给药频次",
}


def _field_label(field_name: str) -> str:
    return _FIELD_LABELS.get(field_name, field_name)


def _occurrence_days_in_rule_window(
    *, episode: IPExposureEpisode,
    occurrences: Sequence[ExposureOccurrence],
    rule: ProtocolExposureRule,
    policy: ExposureAggregationPolicy,
) -> Optional[List[str]]:
    """Return occurrence day tokens determinately OUTSIDE the rule window,
    or None when the check cannot be proven (no occurrences / ambiguous /
    insufficient precision)."""
    daycomp = compute_actual_exposure_days(
        episode=episode, occurrences=occurrences, policy=policy)
    if daycomp.status != DAY_STATUS_COMPLETE or not daycomp.day_set:
        return None
    rw_start = (normalize_partial_date(rule.window_start)
                if rule.window_start.strip() else None)
    rw_end = (normalize_partial_date(rule.window_end)
              if rule.window_end.strip() else None)
    if rw_start is None and rw_end is None:
        return None
    days_parsed: List[Any] = []
    for day_txt in daycomp.day_set:
        day_nv = normalize_partial_date(day_txt)
        day = _to_day(day_nv)
        if day is None:
            return None
        days_parsed.append(day)
    d_rws = _to_day(rw_start) if rw_start is not None else None
    d_rwe = _to_day(rw_end) if rw_end is not None else None
    # Unstated endpoint inclusivity on an occurrence day is not provable.
    if (rule.window_start_inclusive is None and d_rws is not None
            and any(day == d_rws for day in days_parsed)):
        return None
    if (rule.window_end_inclusive is None and d_rwe is not None
            and any(day == d_rwe for day in days_parsed)):
        return None
    outside: List[str] = []
    for day_txt, day in zip(daycomp.day_set, days_parsed):
        if d_rws is not None:
            if (day < d_rws
                    if rule.window_start_inclusive is not False
                    else day <= d_rws):
                outside.append(day_txt)
                continue
        if d_rwe is not None:
            if (day > d_rwe
                    if rule.window_end_inclusive is not False
                    else day >= d_rwe):
                outside.append(day_txt)
    return sorted(set(outside))


# ---------------------------------------------------------------------------
# Unit-level evaluation: adherence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _RatioOutcome:
    out_of_range: bool
    equality: bool
    value_desc: str
    reason: str


def _round_ratio(frac: Fraction, precision: int, mode: str) -> Decimal:
    dec = Decimal(frac.numerator) / Decimal(frac.denominator)
    quantum = Decimal(1).scaleb(-precision)
    rounding = {
        ROUNDING_ROUND_HALF_UP: ROUND_HALF_UP,
        ROUNDING_FLOOR: ROUND_FLOOR,
        ROUNDING_CEILING: ROUND_CEILING,
    }[mode]
    return dec.quantize(quantum, rounding=rounding)


def _threshold_fraction(value: str) -> Optional[Fraction]:
    try:
        return Fraction(Decimal(str(value)))
    except Exception:
        return None


def _check_ratio_against_thresholds(
    frac: Fraction, algorithm: AdherenceAlgorithm,
) -> _RatioOutcome:
    """Compare a ratio against the algorithm thresholds (§6.2).

    Threshold equality is decisive only when the side's inclusivity is
    explicit; otherwise boundary.
    """
    compare_after = (
        algorithm.compare_before_or_after_rounding == COMPARE_AFTER_ROUNDING)
    if compare_after:
        rounded = _round_ratio(frac, algorithm.calculation_precision,
                               algorithm.rounding_mode)
        value_desc = str(rounded)
        val: Optional[Fraction] = None
    else:
        value_desc = (f"{frac.numerator}/{frac.denominator}="
                      f"{float(frac):.6g}")
        val = frac
    out_of_range = False
    equality_thresholds: List[str] = []
    if algorithm.upper_threshold is not None:
        thr = _threshold_fraction(algorithm.upper_threshold)
        if thr is None:
            return _RatioOutcome(False, False, value_desc,
                                 "上限阈值无法解析")
        if compare_after:
            if rounded > Decimal(algorithm.upper_threshold):
                out_of_range = True
            elif rounded == Decimal(algorithm.upper_threshold):
                equality_thresholds.append("upper")
        else:
            if val > thr:
                out_of_range = True
            elif val == thr:
                equality_thresholds.append("upper")
    if algorithm.lower_threshold is not None:
        thr = _threshold_fraction(algorithm.lower_threshold)
        if thr is None:
            return _RatioOutcome(False, False, value_desc,
                                 "下限阈值无法解析")
        if compare_after:
            if rounded < Decimal(algorithm.lower_threshold):
                out_of_range = True
            elif rounded == Decimal(algorithm.lower_threshold):
                equality_thresholds.append("lower")
        else:
            if val < thr:
                out_of_range = True
            elif val == thr:
                equality_thresholds.append("lower")
    if out_of_range:
        return _RatioOutcome(True, False, value_desc, "超出允许范围")
    if equality_thresholds:
        inclusive_flags = {
            "upper": algorithm.upper_inclusive,
            "lower": algorithm.lower_inclusive,
        }
        if any(inclusive_flags[t] is None for t in equality_thresholds):
            return _RatioOutcome(
                False, True, value_desc,
                "计算值恰在阈值等号边界，算法未声明该侧包含关系")
        if all(inclusive_flags[t] for t in equality_thresholds):
            return _RatioOutcome(
                False, False, value_desc, "恰在阈值等号且该侧包含，处于允许范围")
        return _RatioOutcome(
            True, False, value_desc, "恰在阈值等号且该侧不包含，超出允许范围")
    return _RatioOutcome(False, False, value_desc, "")


def _window_day_count(
    algorithm: AdherenceAlgorithm,
) -> Tuple[Optional[int], str]:
    """Expected day count of the algorithm window per endpoint rules."""
    start = (normalize_partial_date(algorithm.window_start)
             if algorithm.window_start.strip() else None)
    end = (normalize_partial_date(algorithm.window_end)
           if algorithm.window_end.strip() else None)
    if start is None or end is None:
        return None, "算法窗口起止日期缺失"
    if _nv_precision(start) != "day" or _nv_precision(end) != "day":
        return None, "算法窗口日期精度不足（需全日精度）"
    if (algorithm.window_start_inclusive is None
            or algorithm.window_end_inclusive is None):
        return None, "算法窗口端点包含关系未声明，无法确定分母"
    d_start = _to_day(start)
    d_end = _to_day(end)
    if d_start is None or d_end is None or d_end < d_start:
        return None, "算法窗口日期无法解析或起止颠倒"
    if algorithm.window_start_inclusive is False:
        d_start += datetime.timedelta(days=1)
    if algorithm.window_end_inclusive is False:
        d_end -= datetime.timedelta(days=1)
    if d_end < d_start:
        return None, "算法窗口端点包含关系导致窗口为空"
    return (d_end - d_start).days + 1, ""


def _days_in_window(
    day_set: Sequence[str], algorithm: AdherenceAlgorithm,
) -> Tuple[Optional[int], str]:
    """Count exposure days inside the algorithm window per endpoints."""
    start = (normalize_partial_date(algorithm.window_start)
             if algorithm.window_start.strip() else None)
    end = (normalize_partial_date(algorithm.window_end)
           if algorithm.window_end.strip() else None)
    if start is None or end is None:
        return None, "算法窗口起止日期缺失"
    if (algorithm.window_start_inclusive is None
            or algorithm.window_end_inclusive is None):
        return None, "算法窗口端点包含关系未声明，无法确定窗口内给药日"
    d_start = _to_day(start)
    d_end = _to_day(end)
    if d_start is None or d_end is None:
        return None, "算法窗口日期无法解析"
    count = 0
    for day_txt in day_set:
        day = _to_day(normalize_partial_date(day_txt))
        if day is None:
            return None, "实际给药日精度不足，无法与算法窗口比较"
        if algorithm.window_start_inclusive is False and day == d_start:
            continue
        if algorithm.window_end_inclusive is False and day == d_end:
            continue
        if d_start <= day <= d_end:
            count += 1
    return count, ""


def _planned_pause_day_count(
    *, algorithm: AdherenceAlgorithm,
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    planned_actions: Sequence[PlannedExposureAction],
    action_coverage_complete: bool,
) -> Tuple[Optional[int], str]:
    """Planned-pause day count subtracted from the denominator when the
    algorithm excludes planned pauses (§6.2/§6.3)."""
    if algorithm.planned_pause_handling == PLANNED_PAUSE_INCLUDED:
        return 0, ""
    if not action_coverage_complete:
        return None, "计划动作来源覆盖不完整，无法按排除计划暂停计算分母"
    total = 0
    assignment_id = assignment.assignment_id if assignment is not None else ""
    for action in planned_actions:
        if (action.action_type != ACTION_PAUSE
                or action.episode_key != episode.episode_key
                or action.assignment_id != assignment_id
                or action.confirmation_status != CONFIRMATION_CONFIRMED):
            continue
        start = (normalize_partial_date(action.action_start)
                 if action.action_start.strip() else None)
        end = (normalize_partial_date(action.action_end)
               if action.action_end.strip() else None)
        if start is None or end is None or _nv_precision(start) != "day" \
                or _nv_precision(end) != "day":
            return None, "计划暂停起止日期缺失或精度不足，无法计算分母"
        d_start = _to_day(start)
        d_end = _to_day(end)
        if d_start is None or d_end is None:
            return None, "计划暂停日期无法解析"
        total += (d_end - d_start).days + 1
    return total, ""


def _observation_for(
    algorithm: AdherenceAlgorithm,
    observations: Sequence[AdherenceObservation],
) -> Tuple[Optional[AdherenceObservation], Optional[str]]:
    """Select the unique observation for this algorithm+window, deduping
    identical rows; conflicting duplicates fail closed."""
    matching = [o for o in observations
                if (o.algorithm_id == algorithm.algorithm_id
                    and o.window_id == algorithm.window_id)]
    if not matching:
        return None, "缺少该窗口的依从性 observation"
    unique: List[AdherenceObservation] = []
    seen_hashes: Set[str] = set()
    for obs in matching:
        h = content_hash((
            obs.numerator_value, obs.denominator_value, obs.unit,
            obs.numerator_source, obs.denominator_source,
            obs.coverage_complete,
            tuple(loc.locator_id() for loc in obs.item_source_locators),
            obs.accepted_revision))
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        unique.append(obs)
    if len(unique) > 1:
        return None, "存在多个内容不同的重复 observation，无法唯一确定"
    return unique[0], ""


def _convert_unit(value: Decimal, unit: str, algorithm: AdherenceAlgorithm,
                  ) -> Tuple[Optional[Decimal], str]:
    """Convert a value to the algorithm's canonical unit when a versioned
    conversion rule exists; identical units pass through."""
    if _canonical_text(unit) == _canonical_text(algorithm.canonical_unit):
        return value, ""
    for from_unit, to_unit, factor in algorithm.unit_conversion_rules:
        if (_canonical_text(unit) == _canonical_text(from_unit)
                and _canonical_text(to_unit)
                == _canonical_text(algorithm.canonical_unit)):
            try:
                factor_dec = Decimal(str(factor))
            except Exception:
                return None, f"换算系数 {factor!r} 无法解析"
            return value * factor_dec, ""
    return None, (
        f"观察单位 {unit!r} 与算法规范单位 {algorithm.canonical_unit!r} "
        f"不一致且无版本化换算依据")


def _evaluate_adherence_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    occurrences: Sequence[ExposureOccurrence],
    aggregation_policy: Optional[ExposureAggregationPolicy],
    observations: Sequence[AdherenceObservation],
    planned_actions: Sequence[PlannedExposureAction],
    action_coverage_complete: bool,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    algorithm = expanded.algorithm
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    # Window applicability (algorithm window defines the computation scope).
    overlap = _compare_windows(
        expanded.window, algorithm.window_start, algorithm.window_end,
        algorithm.window_start_inclusive, algorithm.window_end_inclusive,
        containment=False)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage)
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE])

    if aggregation_policy is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少版本化暴露聚合策略，无法计算实际给药日",
            rule_lineage=rule_lineage)
    observation, obs_gap = _observation_for(algorithm, observations)
    if observation is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=obs_gap,
            rule_lineage=rule_lineage)
    if not observation.coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="依从性 observation 覆盖不完整，无法确认分子分母完整",
            rule_lineage=rule_lineage)

    numerator: Optional[int] = None
    denominator: Optional[int] = None
    num_desc = ""
    if algorithm.is_day_ratio:
        daycomp = compute_actual_exposure_days(
            episode=episode, occurrences=occurrences,
            policy=aggregation_policy)
        if daycomp.status == DAY_STATUS_NO_OCCURRENCE:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=("未找到该 episode 的给药记录；单条缺失不得推断漏服，"
                        "实际给药日不能从治疗跨度推导"),
                rule_lineage=rule_lineage,
                extra_locators=tuple(o.source_locator for o in occurrences))
        if daycomp.status == DAY_STATUS_AMBIGUOUS:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=daycomp.reason, rule_lineage=rule_lineage)
        if daycomp.status == DAY_STATUS_BOUNDARY:
            return _build_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                boundary_reason=daycomp.reason, snapshot_id=snapshot_id,
                rule_lineage=rule_lineage,
                audience_suffix=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
                source_locators=tuple(o.source_locator for o in occurrences))
        in_window, gap = _days_in_window(daycomp.day_set, algorithm)
        if in_window is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=gap,
                rule_lineage=rule_lineage)
        numerator = in_window
        num_desc = f"实际给药日 {in_window} 天"
        expected, wgap = _window_day_count(algorithm)
        if expected is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=wgap,
                rule_lineage=rule_lineage)
        denominator = expected
        pause_days, pgap = _planned_pause_day_count(
            algorithm=algorithm, episode=episode,
            assignment=expanded.assignment,
            planned_actions=planned_actions,
            action_coverage_complete=action_coverage_complete)
        if pause_days is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=pgap,
                rule_lineage=rule_lineage)
        denominator -= pause_days
        if denominator < 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="计划暂停日数超过算法窗口日数，分母计算冲突",
                rule_lineage=rule_lineage)
        if denominator == 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分母为零（零分母按算法策略不可评价）",
                rule_lineage=rule_lineage)
        frac = Fraction(numerator, denominator)
        denominator_desc = str(denominator)
    else:
        if not observation.numerator_value.strip() \
                or not observation.denominator_value.strip():
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性 observation 缺少原始分子或分母值",
                rule_lineage=rule_lineage)
        try:
            num_frac = Fraction(Decimal(observation.numerator_value))
            den_frac = Fraction(Decimal(observation.denominator_value))
        except Exception:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分子或分母无法解析", rule_lineage=rule_lineage)
        if den_frac == 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分母为零（零分母按算法策略不可评价）",
                rule_lineage=rule_lineage)
        if algorithm.canonical_unit:
            num_converted, cgap = _convert_unit(
                Decimal(observation.numerator_value), observation.unit,
                algorithm)
            if num_converted is None:
                return _not_evaluable_result(
                    unit_id=unit_id, episode=episode, reason=cgap,
                    rule_lineage=rule_lineage)
            num_frac = Fraction(num_converted)
            den_converted, dgap = _convert_unit(
                Decimal(observation.denominator_value), observation.unit,
                algorithm)
            if den_converted is None:
                return _not_evaluable_result(
                    unit_id=unit_id, episode=episode, reason=dgap,
                    rule_lineage=rule_lineage)
            den_frac = Fraction(den_converted)
        num_desc = (f"分子 {observation.numerator_value}{observation.unit}，"
                    f"分母 {observation.denominator_value}{observation.unit}")
        frac = num_frac / den_frac
        denominator_desc = str(den_frac)
    # -- ratio + threshold check -------------------------------------------
    outcome = _check_ratio_against_thresholds(frac, algorithm)
    reason = (
        f"{num_desc}，分母 {denominator_desc}，比值 {outcome.value_desc}"
        f"（算法 {algorithm.algorithm_id} v{algorithm.version}）"
        + (f"；{outcome.reason}" if outcome.reason else ""))
    if outcome.out_of_range:
        if priority_policy is not None:
            priority = priority_policy.priority_for_subtype(
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE)
        else:
            priority = MONITORING_PRIORITY_UNKNOWN
        obs_locators = tuple(
            loc for loc in observation.item_source_locators)
        return _build_positive_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            subtype=POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
            match_reason=reason, snapshot_id=snapshot_id,
            monitoring_priority=priority, rule_lineage=rule_lineage,
            source_locators=obs_locators)
    if outcome.equality:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
            source_locators=tuple(
                loc for loc in observation.item_source_locators))
    return _negative_result(
        unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
        reason=reason,
        extra_locators=tuple(loc for loc in observation.item_source_locators))
