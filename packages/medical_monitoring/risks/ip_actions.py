"""IP action, medical-trigger and accountability evaluation."""

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
from .ip_evaluation import *
from .ip_evaluation import (
    _required_roles_for,
    _audience_suffix_for,
    _binding_gate_result,
    _evaluate_role_phase_unit,
    _rule_phase_applicability,
    _evaluate_plan_actual_unit,
    _field_label,
    _occurrence_days_in_rule_window,
    _RatioOutcome,
    _round_ratio,
    _threshold_fraction,
    _check_ratio_against_thresholds,
    _window_day_count,
    _days_in_window,
    _planned_pause_day_count,
    _observation_for,
    _convert_unit,
    _evaluate_adherence_unit,
)

# ---------------------------------------------------------------------------
# Unit-level evaluation: allowed_action
# ---------------------------------------------------------------------------

def _evaluate_allowed_action_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    planned_actions: Sequence[PlannedExposureAction],
    actual_actions: Sequence[ActualIPAction],
    action_coverage_complete: bool,
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
    if not action_coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际给药动作来源覆盖不完整，无法核对允许条件",
            rule_lineage=rule_lineage)
    assignment_id = expanded.assignment.assignment_id
    actuals = [
        a for a in actual_actions
        if (a.episode_key == episode.episode_key
            and a.assignment_id == assignment_id
            and a.action_type == expanded.action_type)]
    if not actuals:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=(f"未找到该类型（{expanded.action_type}）的实际给药动作；"
                    f"动作记录缺失且无法证明其本应存在，不自动判为允许"),
            rule_lineage=rule_lineage)
    if len(actuals) > 1:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="同一类型存在多个实际动作记录，且无唯一版本化优先级可解析重叠",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
            source_locators=tuple(a.source_locator for a in actuals
                                  if a.source_locator))
    action = actuals[0]
    if action.confirmation_status != CONFIRMATION_CONFIRMED:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际给药动作未获确认，无法核对允许条件",
            rule_lineage=rule_lineage,
            extra_locators=(action.source_locator,) if action.source_locator
            else ())
    # Rule window applicability for the action.
    overlap = _compare_windows(
        expanded.window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive)
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
                POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
            source_locators=(action.source_locator,) if action.source_locator
            else ())
    problems: List[str] = []
    # Dose constraint (50 mg vs 25 mg case).
    if rule.allowed_dose_after_values:
        if not episode.dose_disclosed:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="需要核对调整后剂量但该身份在当前披露范围不可用",
                rule_lineage=rule_lineage)
        actual_after = _canonical_record_value("dose_after", action.dose_after)
        if actual_after is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="实际动作调整后剂量缺失或精度不足，无法核对允许值",
                rule_lineage=rule_lineage,
                extra_locators=(action.source_locator,) if action.source_locator
                else ())
        allowed = {
            _canonical_record_value("dose_after", v)
            for v in rule.allowed_dose_after_values}
        if actual_after not in allowed:
            problems.append(
                f"调整后剂量 {action.dose_after} 不在方案允许值 "
                f"{sorted(rule.allowed_dose_after_values)} 内")
    # Reason requirement.
    if rule.allowed_reasons:
        if not action.reason.strip():
            problems.append("给药调整缺少已记录原因")
        elif _canonical_text(action.reason) not in {
                _canonical_text(r) for r in rule.allowed_reasons}:
            problems.append(
                f"给药调整原因 {action.reason!r} 不在方案允许原因"
                f" {list(rule.allowed_reasons)} 内")
    # Planned-action closure (§6.3).
    if rule.planned_action_required:
        planned_matches = [
            p for p in planned_actions
            if (p.episode_key == episode.episode_key
                and p.assignment_id == expanded.assignment.assignment_id
                and p.action_type == expanded.action_type
                and p.confirmation_status == CONFIRMATION_CONFIRMED)]
        if not planned_matches:
            problems.append(
                "实际给药调整缺少对应的已确认计划动作，闭环不完整")
        elif len(planned_matches) > 1:
            return _build_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                boundary_reason="实际动作对应多个计划动作，动作重叠无唯一版本化优先级可解析",
                snapshot_id=snapshot_id, rule_lineage=rule_lineage,
                audience_suffix=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
                source_locators=tuple(p.source_locator for p in planned_matches
                                      if p.source_locator))
    if not problems:
        locs = [locator for locator in (action.source_locator,) if locator]
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason=("实际给药调整的类型、原因、前后剂量与方案允许条件及计划"
                    "动作闭环一致"),
            extra_locators=locs)
    match_reason = "；".join(problems)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    locs = [locator for locator in (action.source_locator,) if locator]
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=locs)


# ---------------------------------------------------------------------------
# Unit-level evaluation: medical_action
# ---------------------------------------------------------------------------

def _evaluate_medical_action_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    action_evidence: Sequence[IPActionEvidence],
    trigger_coverage_complete: bool,
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
    if not trigger_coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="医学触发来源覆盖不完整，无法核对处置关系",
            rule_lineage=rule_lineage)
    if expanded.trigger_key == "none":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("未找到该规则对应的医学触发记录；来源行缺失且无法证明"
                    "其本应存在，不自动判为处置关系成立"),
            rule_lineage=rule_lineage)
    matching = [ev for ev in action_evidence
                if ev.stable_source_event_key == expanded.trigger_key]
    if not matching:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="触发事件定位不到对应来源证据",
            rule_lineage=rule_lineage)
    # Dedup by verified link key.
    by_key: Dict[str, IPActionEvidence] = {}
    for ev in matching:
        by_key.setdefault(ev.verified_link_key, ev)
    evidence_rows = [by_key[k] for k in sorted(by_key)]
    if len(evidence_rows) > 1:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="同一触发事件存在多条不同关联键的证据，关系无法唯一确定",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
            source_locators=tuple(ev.source_locator for ev in evidence_rows))
    ev = evidence_rows[0]
    # Subject/site/episode identity (wrong subject/site/episode never forms
    # a positive/negative; it is not_evaluable context, §7).
    if (ev.subject_ref != episode.subject_ref
            or ev.site_ref != episode.site_ref
            or ev.linked_ip_episode_id != episode.episode_key):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("处置关系需要精确的 episode/来源链接；链接缺失或跨受试者"
                    "/中心，无法评价"),
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    if ev.relation_confirmation != CONFIRMATION_CONFIRMED:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="医学触发事件与给药处置的关系尚未确认，无法评价",
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    if rule.trigger_concept and (
            _canonical_text(ev.concept) != _canonical_text(rule.trigger_concept)):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("触发事件概念与规则要求不一致，且该记录不能作为处置关系"
                    "裁决依据"),
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    # Time-window comparability.
    ev_window = IPWindowDescriptor(
        span_start=ev.event_start, span_end=ev.event_end,
        applicable_phase=episode.study_phase)
    overlap = _compare_windows(
        ev_window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
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
                POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
            source_locators=(ev.source_locator,))
    expected = {_canonical_text(a) for a in rule.expected_actions}
    actual_action = _canonical_text(ev.actual_action)
    if actual_action in expected:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason=(f"医学触发事件 {ev.stable_source_event_key} 对应的实际处置"
                    f" {ev.actual_action} 与规则预期一致"),
            extra_locators=(ev.source_locator,))
    if not ev.actual_action.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="触发事件的处置动作记录缺失，无法核对预期处置",
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    match_reason = (
        f"触发事件 {ev.stable_source_event_key} 的实际处置 {ev.actual_action}"
        f" 与规则 {rule.rule_id} 预期 {sorted(rule.expected_actions)} 冲突")
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=(ev.source_locator,))


# ---------------------------------------------------------------------------
# Unit-level evaluation: accountability (frozen D03 §5.4 decision table)
# ---------------------------------------------------------------------------

def _amount_decimal(value: str) -> Optional[Decimal]:
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _record_totals(
    records: Sequence[IPSemanticRecord],
) -> Tuple[Optional[Decimal], str, Optional[str], List[SourceLocator]]:
    """Sum exact/zero amounts of records sharing one unit.

    Returns (total, unit, gap_reason, locators).  ``unit`` is the single
    canonical source unit of the side ("" when the side does not sum
    cleanly); it is preserved so the accountability balance can convert
    every side to the algorithm's canonical unit before comparison
    (frozen §6.2 rules 1/3).  Range/partial -> boundary via gap_reason
    marker; conflicting or missing units/fields -> not_evaluable reason
    markers.
    """
    total = Decimal(0)
    units: Set[str] = set()
    locators: List[SourceLocator] = []
    for rec in records:
        locators.append(rec.locator)
        if rec.amount_kind in (AMOUNT_KIND_RANGE, AMOUNT_KIND_PARTIAL):
            return None, "", "range", locators
        if rec.amount_kind == AMOUNT_KIND_MISSING \
                or not rec.amount_value.strip() or not rec.amount_unit.strip():
            return None, "", "missing", locators
        if rec.amount_kind not in (AMOUNT_KIND_EXACT, AMOUNT_KIND_ZERO):
            return None, "", "missing", locators
        value = _amount_decimal(rec.amount_value)
        if value is None:
            return None, "", "missing", locators
        units.add(_canonical_text(rec.amount_unit))
        total += value
    if len(units) > 1:
        return None, "", "units", locators
    unit = next(iter(units)) if units else ""
    return total, unit, "", locators


def _evaluate_accountability_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    return_records: Sequence[IPSemanticRecord],
    dispense_records: Sequence[IPSemanticRecord],
    observations: Sequence[AdherenceObservation],
    protocol_return_expectation: str,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    algorithm = expanded.algorithm
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    if protocol_return_expectation not in RETURN_EXPECTATIONS:
        raise IPSliceError(
            f"protocol_return_expectation={protocol_return_expectation!r} "
            f"invalid")
    # §5.4 decision table.
    episode_returns = [
        r for r in return_records
        if (r.subject_ref == episode.subject_ref
            and r.site_ref == episode.site_ref
            and (not r.linked_ip_episode_key
                 or r.linked_ip_episode_key == episode.episode_key))]
    episode_dispenses = [
        r for r in dispense_records
        if (r.subject_ref == episode.subject_ref
            and r.site_ref == episode.site_ref
            and (not r.linked_ip_episode_key
                 or r.linked_ip_episode_key == episode.episode_key))]
    if not episode_returns:
        if protocol_return_expectation == RETURN_NOT_REQUIRED:
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
        if protocol_return_expectation == RETURN_EXPECTED:
            reason = ("方案明确期望回收，但完整覆盖中没有可定位的回收记录；"
                      "研究药物核算信息待核实，不得推断未归还或未服药")
        else:
            reason = ("回收记录缺失且无法证明其本应存在；研究药物核算信息"
                      "待核实")
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=reason,
            rule_lineage=rule_lineage)
    return_total, return_unit, return_gap, return_locs = _record_totals(
        episode_returns)
    if return_gap == "range":
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=("已确认发生回收，但回收量为部分值/范围值，或存在"
                             "多个有版本化依据的换算结果"),
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
            source_locators=return_locs)
    if return_gap == "missing":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="回收记录必需字段（数量或单位）为空，无法核算",
            rule_lineage=rule_lineage, extra_locators=return_locs)
    if return_gap == "units":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="回收记录单位不一致且无版本化换算依据，无法核算",
            rule_lineage=rule_lineage, extra_locators=return_locs)
    if not episode_dispenses:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录缺失，无法完成发放回收核算",
            rule_lineage=rule_lineage)
    dispense_total, dispense_unit, dispense_gap, dispense_locs = _record_totals(
        episode_dispenses)
    if dispense_gap == "range":
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="发放量为部分值/范围值，核算存在两个可行解释",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
            source_locators=dispense_locs)
    if dispense_gap == "missing":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录必需字段（数量或单位）为空，无法核算",
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    if dispense_gap == "units":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录单位不一致且无版本化换算依据，无法核算",
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    # Recorded-administered total from the window observation.
    observation, obs_gap = _observation_for(algorithm, observations)
    if observation is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=obs_gap,
            rule_lineage=rule_lineage)
    if not observation.coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药核算覆盖不完整，无法完成发放回收核算",
            rule_lineage=rule_lineage)
    recorded = _amount_decimal(observation.numerator_value)
    if recorded is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药总量缺失或无法解析，无法核算",
            rule_lineage=rule_lineage)
    # Frozen §6.2 rules 1/3: convert every side to the algorithm's
    # canonical unit before balance comparison.  Raw values are never
    # compared across units; a missing/conflicting unit or a missing
    # versioned conversion basis fails closed to not_evaluable.
    if not algorithm.canonical_unit.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="算法未声明规范单位，无法完成发放回收核算",
            rule_lineage=rule_lineage,
            extra_locators=return_locs + dispense_locs)
    converted_return, return_gap = _convert_unit(
        return_total, return_unit, algorithm)
    if converted_return is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=return_gap,
            rule_lineage=rule_lineage, extra_locators=return_locs)
    converted_dispense, dispense_gap = _convert_unit(
        dispense_total, dispense_unit, algorithm)
    if converted_dispense is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=dispense_gap,
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    if not observation.unit.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药核算缺少单位，无法完成发放回收核算",
            rule_lineage=rule_lineage,
            extra_locators=tuple(loc for loc in observation.item_source_locators))
    converted_recorded, recorded_gap = _convert_unit(
        recorded, observation.unit, algorithm)
    if converted_recorded is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=recorded_gap,
            rule_lineage=rule_lineage,
            extra_locators=tuple(loc for loc in observation.item_source_locators))
    balance = converted_dispense - converted_return
    if balance != converted_recorded:
        match_reason = (
            f"发放 {converted_dispense} 减回收 {converted_return} 为 "
            f"{balance}，与记录给药总量 {converted_recorded} 不一致（规范"
            f"单位 {algorithm.canonical_unit}）")
        # Frozen §6.2: an accountability_proxy positive must carry the exact
        # 按发放/回收核算 annotation on its user-visible evidence and must
        # never be presented as proven actual dosing days.
        extra_evidence: Tuple[EvidenceItem, ...] = ()
        if algorithm.is_accountability_proxy:
            extra_evidence = (_make_evidence_item(
                evidence_id=f"ev-{unit_id}-proxy",
                polarity=L1bEvidencePolarity.SUPPORTING,
                locator=episode.source_locator,
                evidence_role="ip_accountability",
                rule_lineage=rule_lineage,
                uncertainty_note=ACCOUNTABILITY_PROXY_ANNOTATION),)
        if priority_policy is not None:
            priority = priority_policy.priority_for_subtype(
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY)
        else:
            priority = MONITORING_PRIORITY_UNKNOWN
        return _build_positive_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            subtype=POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
            match_reason=match_reason, snapshot_id=snapshot_id,
            monitoring_priority=priority, rule_lineage=rule_lineage,
            source_locators=return_locs + dispense_locs
            + list(observation.item_source_locators),
            extra_evidence=extra_evidence)
    return _negative_result(
        unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
        reason=("发放减回收与记录给药总量一致，核算闭环成立（按发放/回收"
                "核算口径）"),
        extra_locators=return_locs + dispense_locs)
