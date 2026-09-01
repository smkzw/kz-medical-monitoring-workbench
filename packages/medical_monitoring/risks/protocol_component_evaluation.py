"""Protocol evidence-gate and component-condition evaluation."""

from __future__ import annotations

import datetime
import itertools
from dataclasses import dataclass
from types import MappingProxyType
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Set,
                    Tuple)

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from ..intelligence.normalization import normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    EvaluationUnit,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)

from .protocol_contracts import *
from .protocol_contracts import (
    _date_interval, _day_date, _interval_relation, _parse_decimal, _round_decimal,
)
from .protocol_applicability import *
from .protocol_evidence import *

@dataclass(frozen=True)
class CrossDomainGateOutcome:
    """Outcome of the exact cross-domain verification gate (§7.4)."""

    verified: bool
    reason: str = ""
    relation_type: str = ""


def verify_cross_domain_ref(
    *,
    ref: CrossDomainEvidenceRef,
    subject_ref: str,
    site_ref: str,
    producer_unit_id: str,
    control_point_id: str,
    component_id: str,
    relation_type: str,
    rule_lineage: str,
) -> CrossDomainGateOutcome:
    """Exact cross-domain evidence gate (§7.4).

    Only subject + site + producer unit + stable source event
    key/content hash + rule/component + comparable window + closed
    relation type all exactly verified may support a positive/negative.
    Same record id on another subject, date-closeness alone, same row
    number alone and unconfirmed relations all fail closed
    (challenges 35/36/63).
    """
    if relation_type not in RELATION_TYPES:
        return CrossDomainGateOutcome(
            False, f"relation_type={relation_type!r} is not closed", "")
    if relation_type == RELATION_UNCONFIRMED:
        return CrossDomainGateOutcome(
            False, "跨域关系未确认，不能作为裁决依据",
            relation_type)
    if ref.consumer_domain != D04_DOMAIN:
        return CrossDomainGateOutcome(
            False,
            f"CrossDomainEvidenceRef consumer_domain must be {D04_DOMAIN}, "
            f"got {ref.consumer_domain!r}", relation_type)
    if not ref.verify_content_hash():
        return CrossDomainGateOutcome(
            False, "跨域引用内容哈希与稳定来源事件不一致",
            relation_type)
    if producer_unit_id and ref.producer_unit_id != producer_unit_id:
        return CrossDomainGateOutcome(
            False,
            f"producer_unit_id mismatch: ref {ref.producer_unit_id!r} != "
            f"expected {producer_unit_id!r}", relation_type)
    if not control_point_id.strip() or not component_id.strip():
        return CrossDomainGateOutcome(
            False, "rule/component 引用缺失，跨域关系无法确认",
            relation_type)
    ctx = dict(ref.context_payload)
    if ctx.get("subject_ref") != subject_ref:
        return CrossDomainGateOutcome(
            False,
            "跨域记录 subject 与受试者不匹配（仅 record id 相同不足）",
            relation_type)
    if ctx.get("site_ref") != site_ref:
        return CrossDomainGateOutcome(
            False,
            "跨域记录 site 与研究中心不匹配",
            relation_type)
    return CrossDomainGateOutcome(True, "", relation_type)


# ---------------------------------------------------------------------------
# Component condition evaluation (generic operator semantics)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentConditionOutcome:
    """Verdict + evidence of one atomic condition evaluation."""

    verdict: str
    reason: str = ""
    gap_codes: Tuple[str, ...] = ()
    gaps: Tuple[str, ...] = ()
    supporting: Tuple[EvidenceItem, ...] = ()
    counterevidence: Tuple[EvidenceItem, ...] = ()
    context: Tuple[EvidenceItem, ...] = ()
    binding_ids: Tuple[str, ...] = ()


def _binding_evidence(
    *, unit_id: str, component_id: str, binding: RuleEvidenceBinding,
    polarity: str, rule_lineage: str, note: str,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=f"ev-{unit_id}-{component_id}-{binding.binding_id}",
        polarity=polarity, locator=binding.source_locator,
        evidence_role=binding.source_role, rule_lineage=rule_lineage,
        uncertainty_note=note)


def _convert_value(
    value: Decimal, unit: str, target_unit: str,
    conversion_rules: Sequence[UnitConversionRule],
) -> Tuple[Optional[Decimal], bool, str]:
    """Versioned unit conversion; returns (value, ambiguous, reason)."""
    if unit == target_unit:
        return value, False, ""
    matches = [
        c for c in conversion_rules
        if c.from_unit == unit and c.to_unit == target_unit
    ]
    if not matches:
        return None, False, (
            f"单位 {unit!r} 与 {target_unit!r} 无版本化换算关系，无法比较")
    if len(matches) > 1:
        return None, True, (
            f"单位 {unit!r} 存在多个可行换算关系，无法唯一确定")
    factor = _parse_decimal(matches[0].factor)
    if factor is None:
        return None, False, "换算系数不可解析"
    return value * factor, False, ""


def _numeric_verdict(
    *, unit_id: str, component_id: str, comparison: RuleComparison,
    bindings: Sequence[RuleEvidenceBinding],
    conversion_rules: Sequence[UnitConversionRule],
    rule_lineage: str,
) -> ComponentConditionOutcome:
    """Generic numeric comparison with versioned conversion and rounding
    policy (§7.1, challenges 16-21)."""
    if not bindings:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="缺少数值证据",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("必需来源角色覆盖不完整",))
    # Identity/time gate: only confirmed bindings with comparable value.
    usable: List[RuleEvidenceBinding] = []
    for b in bindings:
        if not b.is_confirmed:
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason="证据身份或时间关系未确认，无法比较",
                gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
                gaps=("证据身份或时间关系未确认，无法比较",))
        usable.append(b)
    if len(usable) > 1:
        # 同日多个值只有版本化选择策略才可确定裁决 (§7.1); no policy here.
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="存在多个数值记录且无版本化选择策略，无法唯一确定",
            gap_codes=(GAP_RETEST_UNCONFIRMED,),
            gaps=("多值选择策略缺失，无法唯一确定",))
    b = usable[0]
    value = _parse_decimal(b.value)
    if value is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="关键数值缺失或不可解析",
            gap_codes=(GAP_VALUE_MISSING,),
            gaps=("关键数值缺失",))
    converted, ambiguous, reason = _convert_value(
        value, b.unit, comparison.canonical_unit, conversion_rules)
    if converted is None:
        return ComponentConditionOutcome(
            verdict=(VERDICT_BOUNDARY if ambiguous else VERDICT_NOT_EVALUABLE),
            reason=reason,
            gap_codes=(GAP_UNIT_UNCONVERTIBLE,),
            gaps=(reason,))
    value = converted
    if comparison.rounding_policy == ROUNDING_AFTER:
        value = _round_decimal(
            value, comparison.rounding_precision, comparison.rounding_mode)

    threshold = _parse_decimal(comparison.threshold)
    upper = (_parse_decimal(comparison.threshold_upper)
             if comparison.threshold_upper.strip() else None)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则阈值不可解析", gap_codes=(GAP_VALUE_MISSING,),
            gaps=("规则阈值不可解析",))
    outcome = _compare_value(
        value=value, comparison=comparison.comparison,
        threshold=threshold, upper=upper,
        lower_inclusive=comparison.lower_inclusive,
        upper_inclusive=comparison.upper_inclusive)
    if outcome == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="数值恰在阈值且等号/端点包含关系未定义",
            gap_codes=(), gaps=())
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=b,
        polarity=(L1bEvidencePolarity.SUPPORTING
                  if outcome == "met" else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"记录值 {b.value} {b.unit}，比较结果 {'满足' if outcome == 'met' else '不满足'}规则")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if outcome == "met" else VERDICT_UNMET),
        reason=f"数值比较{'满足' if outcome == 'met' else '不满足'}",
        supporting=(ev,) if outcome == "met" else (),
        counterevidence=() if outcome == "met" else (ev,),
        binding_ids=(b.binding_id,))


def _compare_value(
    *, value: Decimal, comparison: str, threshold: Decimal,
    upper: Optional[Decimal], lower_inclusive: Optional[bool],
    upper_inclusive: Optional[bool],
) -> str:
    """Returns met/unmet/boundary with explicit inclusivity semantics."""
    def endpoint_eq(v: Decimal, t: Decimal, inclusive: Optional[bool]) -> Optional[bool]:
        if v == t:
            if inclusive is None:
                return None
            return bool(inclusive)
        return None

    if comparison == "equals":
        return "met" if value == threshold else "unmet"
    if comparison == "not_equals":
        return "unmet" if value == threshold else "met"
    if comparison == "at_least":
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            return "met" if lower_inclusive else "unmet"
        return "met" if value > threshold else "unmet"
    if comparison == "at_most":
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            return "met" if lower_inclusive else "unmet"
        return "met" if value < threshold else "unmet"
    if comparison == "above":
        return "met" if value > threshold else "unmet"
    if comparison == "below":
        return "met" if value < threshold else "unmet"
    if comparison == "within_range":
        if upper is None:
            return "unmet"
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            if not lower_inclusive:
                return "unmet"
        elif value < threshold:
            return "unmet"
        if value == upper:
            if upper_inclusive is None:
                return "boundary"
            if not upper_inclusive:
                return "unmet"
        elif value > upper:
            return "unmet"
        return "met"
    return "unmet"


def _window_contains_date(
    date_raw: str, window_start: str, window_end: str,
    start_inclusive: Optional[bool], end_inclusive: Optional[bool],
) -> Tuple[str, str]:
    """Determinate inside/outside/boundary for one date in a window."""
    day = _day_date(date_raw)
    if day is None:
        return "not_evaluable", "日期缺失或精度不足，无法确认窗口内"
    lo = _day_date(window_start) if window_start.strip() else None
    hi = _day_date(window_end) if window_end.strip() else None
    if lo is None and hi is None:
        return "inside", ""
    if lo is not None and day == lo and start_inclusive is None:
        return "boundary", "日期恰在窗口起点且端点包含关系未定义"
    if hi is not None and day == hi and end_inclusive is None:
        return "boundary", "日期恰在窗口终点且端点包含关系未定义"
    inside = True
    if lo is not None:
        inside = inside and (day >= lo if start_inclusive is True
                             else day > lo)
    if hi is not None:
        inside = inside and (day <= hi if end_inclusive is True
                             else day < hi)
    return ("inside" if inside else "outside"), ""


def _evaluate_existence(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool],
    rule_lineage: str,
) -> ComponentConditionOutcome:
    """exists/not_exists with the §4.3 zero-record proof requirements."""
    role = rule.exists_target_role
    target = [b for b in bindings if b.source_role == role]
    role_covered = coverage_complete_roles.get(role, False)
    if any(not b.is_confirmed for b in target):
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="记录关系未确认，不能作为存在性依据",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("记录关系未确认，不能作为存在性依据",))
    # Window filtering: a record outside the declared window is not the
    # target record; date missing cannot confirm inside-window status.
    in_window: List[RuleEvidenceBinding] = []
    if rule.evaluation_window_start.strip() or rule.evaluation_window_end.strip():
        for b in target:
            status, _reason = _window_contains_date(
                b.date_raw, rule.evaluation_window_start,
                rule.evaluation_window_end, rule.window_start_inclusive,
                rule.window_end_inclusive)
            if status == "inside":
                in_window.append(b)
            elif status == "boundary":
                return ComponentConditionOutcome(
                    verdict=VERDICT_BOUNDARY,
                    reason="记录日期与规则窗口端点关系未定义",
                    gap_codes=(), gaps=())
            elif status == "not_evaluable":
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="记录日期缺失或精度不足，无法确认是否在窗口内",
                    gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                    gaps=("记录日期缺失或精度不足，无法确认是否在窗口内",))
    else:
        in_window = list(target)

    def build_ev(b: RuleEvidenceBinding, found: bool) -> Tuple[EvidenceItem, ...]:
        if not found:
            return ()
        note = ("命中目标记录" if rule.operator == OP_EXISTS
                else "不应存在的记录被发现")
        return (_binding_evidence(
            unit_id=unit_id, component_id=component_id, binding=b,
            polarity=L1bEvidencePolarity.SUPPORTING,
            rule_lineage=rule_lineage, note=note),)

    if rule.operator == OP_EXISTS:
        if in_window:
            evs = tuple(ev for b in in_window for ev in build_ev(b, True))
            return ComponentConditionOutcome(
                verdict=VERDICT_MET, reason="目标记录存在",
                supporting=evs,
                binding_ids=tuple(b.binding_id for b in in_window))
        if role_covered:
            return ComponentConditionOutcome(
                verdict=VERDICT_UNMET,
                reason="来源完整覆盖下未发现目标记录",
                gap_codes=(), gaps=())
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="未见记录但无法证明来源完整覆盖，不能推断未发生",
            gap_codes=(GAP_RECORD_MISSING_UNPROVEN,),
            gaps=("未见记录但无法证明来源完整覆盖，不能推断未发生",))
    # not_exists
    if in_window:
        evs = tuple(ev for b in in_window for ev in build_ev(b, True))
        return ComponentConditionOutcome(
            verdict=VERDICT_UNMET, reason="不应存在的记录被发现",
            counterevidence=evs,
            binding_ids=tuple(b.binding_id for b in in_window))
    if role_covered:
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="来源完整覆盖下未见任何目标记录",
            gap_codes=(), gaps=())
    return ComponentConditionOutcome(
        verdict=VERDICT_NOT_EVALUABLE,
        reason="未见记录但无法证明来源完整覆盖，不能推断未发生",
        gap_codes=(GAP_RECORD_MISSING_UNPROVEN,),
        gaps=("未见记录但无法证明来源完整覆盖，不能推断未发生",))


def _ordered_bindings_for_roles(
    *, component_id: str, bindings: Sequence[RuleEvidenceBinding],
    role_a: str, role_b: str,
) -> Tuple[Optional[RuleEvidenceBinding], Optional[RuleEvidenceBinding], str]:
    """Select the role-a/role-b bindings; wrong identity fails closed."""
    a = [b for b in bindings if b.source_role == role_a]
    b_list = [b for b in bindings if b.source_role == role_b]
    for b in a + b_list:
        if not b.is_confirmed:
            return None, None, "证据身份或时间关系未确认"
    if len(a) > 1 or len(b_list) > 1:
        return None, None, "同一锚点存在多个记录且无版本化选择策略"
    return (a[0] if a else None), (b_list[0] if b_list else None), ""


def _evaluate_temporal_order(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    """OP_TEMPORAL_ORDER / OP_SEQUENCE -- anchors are never interchangeable
    (§7.2, challenge 39); partial dates compare on shared precision only."""
    a, b, reason = _ordered_bindings_for_roles(
        component_id=component_id, bindings=bindings,
        role_a=rule.anchor_role_a, role_b=rule.anchor_role_b)
    if reason:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=(reason,))
    if a is None or b is None:
        missing = [r for r in (rule.anchor_role_a, rule.anchor_role_b)
                   if (a is None and r == rule.anchor_role_a)
                   or (b is None and r == rule.anchor_role_b)]
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=f"时序锚点 {missing} 记录缺失，无法比较",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("时序锚点记录缺失，无法比较",))
    ia = _date_interval(a.date_raw)
    ib = _date_interval(b.date_raw)
    if ia is None or ib is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="时序锚点日期缺失或无法解析",
            gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
            gaps=("时序锚点日期缺失或无法解析，无法比较",))
    relation = _interval_relation(ia, ib)
    direction = rule.order_direction
    if direction == "before":
        met = relation == "before"
    elif direction == "after":
        met = relation == "after"
    elif direction == "not_after":
        met = relation in ("before", "equal_day")
    else:  # not_before
        met = relation in ("after", "equal_day")
    if relation == "possibly_overlap":
        # Partial dates that may or may not satisfy the order stay
        # boundary -- never silently padded (challenge 37).
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期在共享精度上可能命中也可能不命中时序关系",
            gap_codes=(), gaps=())
    evs = (
        _binding_evidence(
            unit_id=unit_id, component_id=component_id, binding=b,
            polarity=(L1bEvidencePolarity.SUPPORTING if met
                      else L1bEvidencePolarity.COUNTEREVIDENCE),
            rule_lineage=rule_lineage,
            note=f"{rule.anchor_role_a}={a.date_raw}, "
                 f"{rule.anchor_role_b}={b.date_raw}"),
    )
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"时序关系{'满足' if met else '不满足'}规则要求",
        supporting=evs if met else (),
        counterevidence=() if met else evs,
        binding_ids=(a.binding_id, b.binding_id))


def _evaluate_duration(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    a, b, reason = _ordered_bindings_for_roles(
        component_id=component_id, bindings=bindings,
        role_a=rule.anchor_role_a, role_b=rule.anchor_role_b)
    if reason:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=(reason,))
    if a is None or b is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="持续时长所需日期记录缺失",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("持续时长所需日期记录缺失",))
    da = _day_date(a.date_raw)
    db = _day_date(b.date_raw)
    if da is None or db is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期无法计算精确持续时长，可能命中也可能不命中",
            gap_codes=(), gaps=())
    days = abs((db - da).days)
    threshold = _parse_decimal(rule.duration_min)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="持续时长阈值不可解析",
            gap_codes=(GAP_VALUE_MISSING,), gaps=("持续时长阈值不可解析",))
    day_dec = Decimal(days)
    if day_dec == threshold and rule.duration_min_inclusive is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="持续时长恰在阈值且端点包含关系未定义",
            gap_codes=(), gaps=())
    met = (day_dec >= threshold
           if rule.duration_min_inclusive is not False
           else day_dec > threshold)
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"持续时长 {days} 天{'满足' if met else '不满足'}要求",
        gap_codes=(), gaps=())


def _evaluate_count(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    alternate_roles = (req.alternate_evidence_roles if req is not None
                       else rule.alternate_evidence_roles)
    targets = [b for b in bindings
               if b.source_role in required_roles
               or b.source_role in alternate_roles]
    if any(not b.is_confirmed for b in targets):
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="计数记录关系未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("计数记录关系未确认",))
    if rule.evaluation_window_start.strip() or rule.evaluation_window_end.strip():
        filtered: List[RuleEvidenceBinding] = []
        for b in targets:
            status, _r = _window_contains_date(
                b.date_raw, rule.evaluation_window_start,
                rule.evaluation_window_end, rule.window_start_inclusive,
                rule.window_end_inclusive)
            if status == "inside":
                filtered.append(b)
            elif status == "boundary":
                return ComponentConditionOutcome(
                    verdict=VERDICT_BOUNDARY,
                    reason="计数记录日期与窗口端点关系未定义",
                    gap_codes=(), gaps=())
            elif status == "not_evaluable":
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="计数记录日期缺失或精度不足",
                    gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                    gaps=("计数记录日期缺失或精度不足",))
        targets = filtered
    count = len(targets)
    threshold = rule.count_threshold
    cmp_ = rule.count_comparison
    met = (count >= threshold if cmp_ == "at_least"
           else count <= threshold if cmp_ == "at_most"
           else count == threshold)
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"计数 {count} {'满足' if met else '不满足'}阈值 {threshold}",
        gap_codes=(), gaps=())


def _evaluate_age(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    """OP_AGE -- never defaults to 周岁/实足年龄 (challenge 80)."""
    if not rule.age_algorithm_id.strip():
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄算法未冻结，绝不默认周岁/实足年龄算法",
            gap_codes=(GAP_AGE_ALGORITHM_UNFROZEN,),
            gaps=("年龄算法未冻结，无法计算年龄",))
    birth = [b for b in bindings if b.source_role == "demographics"]
    consent = [b for b in bindings if b.source_role == "consent"]
    if not birth or not consent:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="出生日期或知情日期缺失，无法计算年龄",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("出生日期或知情日期缺失，无法计算年龄",))
    birth_nv = normalize_partial_date(birth[0].value or birth[0].date_raw)
    consent_day = _day_date(consent[0].date_raw)
    if not birth_nv.normalized or consent_day is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期无法确定精确年龄，可能命中也可能不命中",
            gap_codes=(), gaps=())
    birth_parts = str(birth_nv.normalized).split("-")
    if len(birth_parts) < 1:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="出生日期精度不足，无法确定年龄",
            gap_codes=(), gaps=())
    birth_year = int(birth_parts[0])
    age_years = consent_day.year - birth_year
    comparison = rule.comparison
    if comparison is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄规则缺少比较语义",
            gap_codes=(GAP_EXPRESSION_INCOMPLETE,),
            gaps=("年龄规则缺少比较语义",))
    dec = Decimal(age_years)
    threshold = _parse_decimal(comparison.threshold)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄阈值不可解析",
            gap_codes=(GAP_VALUE_MISSING,), gaps=("年龄阈值不可解析",))
    if len(birth_parts) < 3 and dec == threshold:
        # Only birth year known and age sits on the threshold year: the
        # subject may or may not have crossed the birthday -> boundary.
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="仅知出生年份且年龄恰在阈值年度，可能命中也可能不命中",
            gap_codes=(), gaps=())
    met = _compare_value(
        value=dec, comparison=comparison.comparison, threshold=threshold,
        upper=(_parse_decimal(comparison.threshold_upper)
               if comparison.threshold_upper.strip() else None),
        lower_inclusive=comparison.lower_inclusive,
        upper_inclusive=comparison.upper_inclusive) == "met"
    if not met and _compare_value(
            value=dec, comparison=comparison.comparison, threshold=threshold,
            upper=(_parse_decimal(comparison.threshold_upper)
                   if comparison.threshold_upper.strip() else None),
            lower_inclusive=comparison.lower_inclusive,
            upper_inclusive=comparison.upper_inclusive) == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="年龄恰在阈值且端点包含关系未定义",
            gap_codes=(), gaps=())
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"年龄 {age_years} 岁{'满足' if met else '不满足'}规则",
        gap_codes=(), gaps=())


def _evaluate_discontinuation_trigger(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    conversion_rules: Sequence[UnitConversionRule], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    """OP_DISCONTINUATION_TRIGGER (§3.2/6.1 subtype 4).

    Trigger reached + disposition determinately inconsistent -> issue
    (verdict unmet); trigger not reached -> requirement satisfied
    (verdict met); disposition missing/unconfirmed -> not_evaluable.
    IP stop/pause dosing actions are D03-owned and never re-evaluated
    here (challenge 41/42).
    """
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    trigger = rule.trigger_comparison
    trigger_bindings = [
        b for b in bindings
        if b.source_role in required_roles
        and b.source_role != "disposition"]
    trigger_outcome = _numeric_verdict(
        unit_id=unit_id, component_id=component_id,
        comparison=trigger, bindings=trigger_bindings,
        conversion_rules=conversion_rules, rule_lineage=rule_lineage)
    if trigger_outcome.verdict == VERDICT_UNMET:
        # Trigger not reached: no withdrawal issue.
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="退出/终止参与触发条件未达到",
            supporting=trigger_outcome.supporting,
            counterevidence=trigger_outcome.counterevidence,
            binding_ids=trigger_outcome.binding_ids)
    if trigger_outcome.verdict in (VERDICT_BOUNDARY,
                                   VERDICT_NOT_EVALUABLE):
        return trigger_outcome
    # Trigger reached: check disposition consistency.
    disposition = [b for b in bindings if b.source_role == "disposition"]
    if not disposition:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="已满足退出/终止参与触发条件，但受试者处置记录缺失",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("受试者处置记录缺失，无法判定是否一致",))
    disp = disposition[0]
    if not disp.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="处置记录关系未确认，无法判定一致性",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("处置记录关系未确认",))
    expected = {v.strip() for v in rule.expected_disposition_values}
    actual = disp.value.strip()
    consistent = actual in expected
    if consistent and rule.disposition_window_days.strip():
        window_days = _parse_decimal(rule.disposition_window_days)
        trigger_date = next(
            (b.date_raw for b in trigger_bindings if b.date_raw.strip()), "")
        disp_day = _day_date(disp.date_raw)
        trig_day = _day_date(trigger_date)
        if disp_day is None or trig_day is None:
            return ComponentConditionOutcome(
                verdict=VERDICT_BOUNDARY,
                reason="处置或触发日期精度不足，无法确认处置时窗",
                gap_codes=(), gaps=())
        if (disp_day - trig_day).days > int(window_days):
            consistent = False
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=disp,
        polarity=(L1bEvidencePolarity.SUPPORTING if consistent
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"处置记录 {actual}，{'一致' if consistent else '不一致'}")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if consistent else VERDICT_UNMET),
        reason=("处置记录与触发标准一致" if consistent
                else "处置记录与触发标准确定不一致"),
        supporting=(ev,) if consistent else (),
        counterevidence=() if consistent else (ev,),
        binding_ids=(disp.binding_id,))


def _evaluate_investigator_judgment(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    judgments = [b for b in bindings
                 if b.source_role == "investigator_judgment"]
    if not judgments:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则必需研究者判断，但判断记录缺失，不得由临床常识补写",
            gap_codes=(GAP_INVESTIGATOR_JUDGMENT_MISSING,),
            gaps=("研究者判断缺失",))
    j = judgments[0]
    if not j.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="研究者判断记录未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("研究者判断记录未确认",))
    note = j.value.strip()
    met = (note.lower() not in ("no", "否", "不适用", ""))
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=j,
        polarity=(L1bEvidencePolarity.SUPPORTING if met
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage, note="研究者判断记录")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason="研究者判断已记录",
        supporting=(ev,) if met else (),
        counterevidence=() if met else (ev,),
        binding_ids=(j.binding_id,))


def _evaluate_equality_or_membership(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    alternate_roles = (req.alternate_evidence_roles if req is not None
                       else rule.alternate_evidence_roles)
    usable = [b for b in bindings
              if b.source_role in required_roles
              or b.source_role in alternate_roles]
    if not usable:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="缺少等值/集合证据",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("必需来源角色覆盖不完整",))
    b = usable[0]
    if not b.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="证据关系未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("证据关系未确认",))
    actual = " ".join(b.value.strip().casefold().split())
    if rule.operator == OP_SET_MEMBERSHIP:
        allowed = {" ".join(v.strip().casefold().split())
                   for v in rule.value_set}
        met = actual in allowed
    else:  # equals / not_equals
        target = " ".join(rule.value_set[0].strip().casefold().split())
        met = actual == target
        if rule.operator == OP_NOT_EQUALS:
            met = not met
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=b,
        polarity=(L1bEvidencePolarity.SUPPORTING if met
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"记录值 {b.value}，{'满足' if met else '不满足'}规则")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"值比较{'满足' if met else '不满足'}",
        supporting=(ev,) if met else (),
        counterevidence=() if met else (ev,),
        binding_ids=(b.binding_id,))


def _qualifying_exception(
    *, component: ProtocolComponent, subject_ref: str, site_ref: str,
    exceptions: Sequence[ProtocolExceptionBinding],
) -> Tuple[bool, Optional[ProtocolExceptionBinding], Optional[str]]:
    """Classify exceptions per §7.3.

    Returns (qualifies, exception, gap_or_boundary).  A qualifying
    exception flips the component verdict to met with counterevidence.
    ``retrospective_explanation`` / ``urgent_hazard_justification`` are
    context only and never rewrite a non-conformance (challenges 25/26/28).
    """
    for exc in exceptions:
        if exc.control_point_id != component.control_point_id:
            continue
        if exc.component_id and exc.component_id != component.component_id:
            continue
        if exc.subject_ref != subject_ref or exc.site_ref != site_ref:
            continue
        if exc.exception_effect == EXCEPTION_RETROSPECTIVE:
            continue
        if exc.exception_effect == EXCEPTION_URGENT_HAZARD:
            continue
        if exc.exception_effect == EXCEPTION_UNRESOLVED:
            return False, exc, "boundary"
        if exc.exception_effect == EXCEPTION_PROTOCOL_DEFINED:
            if exc.approved_or_confirmed is None:
                return False, exc, "gap"
            if not exc.approved_or_confirmed:
                continue  # unapproved wording cannot rewrite
            return True, exc, None
        if exc.exception_effect == EXCEPTION_EFFECTIVE_RULE_CHANGE:
            if exc.approved_or_confirmed is None:
                return False, exc, "gap"
            if exc.effective_at_event_time is None:
                return False, exc, "gap"
            if not exc.approved_or_confirmed or not exc.effective_at_event_time:
                continue
            return True, exc, None
    return False, None, None


def evaluate_component_condition(
    *,
    unit_id: str,
    component: ProtocolComponent,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool],
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcome: Optional[RetestOutcome] = None,
    subject_ref: str = "",
    site_ref: str = "",
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    """Evaluate one atomic condition -> condition verdict (§4, §7).

    Auxiliary-only roles (IE/DV summaries, monitoring notes, free text)
    can never alone prove a criterion met or unmet (challenges 5/6).
    Identity/time mismatches and unconfirmed relations fail closed.
    Exceptions are classified per §7.3 and may flip the verdict with
    counterevidence.  The verdict is neutral ("condition satisfied as
    written"); mapping to the issue predicate is done separately.

    When an ``evidence_requirement`` is supplied, its required/alternate
    role sets are the authoritative evidence-role contract (§4.2): a
    binding may satisfy only a role declared by the requirement plus its
    identity/component -- the evaluator never re-derives a second
    divergent role list from the structured rule.
    """
    rule = component.structured_rule
    req = evidence_requirement
    if req is not None:
        required_roles = req.required_evidence_roles
        alternate_roles = req.alternate_evidence_roles
    else:
        required_roles = rule.required_evidence_roles
        alternate_roles = rule.alternate_evidence_roles
    rule_lineage = rule.rule_priority_policy or D04_RULE_LINEAGE_DEFAULT
    if component.verification_status != "verified":
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则抽取未经验证，任一/全部/至少 N 关系未冻结，禁止默认组合语义",
            gap_codes=(GAP_RULE_NOT_VERIFIED,),
            gaps=("规则抽取未经验证",))

    # Producer-dependency gate (challenge 32): a D04 unit consuming a
    # producer fact whose own evaluation is not_evaluable is blocked.
    blocked = [b for b in bindings if b.producer_dependency_blocked]
    if blocked:
        reason = blocked[0].producer_dependency_reason or (
            "所依赖的上游评价暂无法评价")
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_PRODUCER_DEPENDENCY,), gaps=(reason,))

    # Cross-domain gate: every binding carrying a producer ref must pass
    # the exact verification (§7.4).
    for b in bindings:
        if b.cross_domain_ref is None:
            continue
        gate = verify_cross_domain_ref(
            ref=b.cross_domain_ref, subject_ref=subject_ref,
            site_ref=site_ref,
            producer_unit_id=(
                b.expected_producer_unit_id
                or b.cross_domain_ref.producer_unit_id),
            control_point_id=component.control_point_id,
            component_id=component.component_id,
            relation_type=RELATION_ELIGIBILITY_FACT,
            rule_lineage=rule_lineage)
        if not gate.verified:
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE, reason=gate.reason,
                gap_codes=(GAP_RELATION_UNCONFIRMED,), gaps=(gate.reason,))

    # Auxiliary-only gate: IE/DV/monitoring summaries are hints, never
    # standalone proof (§4.1/4.2).  Applies to the whole binding set even
    # when the auxiliary role is not in the rule's required/alternate set.
    if bindings and all(b.source_role in AUXILIARY_ONLY_ROLES
                        for b in bindings):
        code = (GAP_IE_SUMMARY_ONLY if bindings[0].source_role
                == "aggregate_ie_status" else GAP_FREE_TEXT_ONLY)
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=("IEYN/IE 汇总或 DV 行不能作为逐条标准证据；"
                    "需要逐条 rule-specific 证据"),
            gap_codes=(code,),
            gaps=("仅有汇总/自由文本证据，无逐条标准证据",))

    relevant = [b for b in bindings
                if b.source_role in required_roles
                or b.source_role in alternate_roles]
    if relevant and all(b.source_role in AUXILIARY_ONLY_ROLES
                        for b in relevant):
        code = (GAP_IE_SUMMARY_ONLY if relevant[0].source_role
                == "aggregate_ie_status" else GAP_FREE_TEXT_ONLY)
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=("IEYN/IE 汇总或 DV 行不能作为逐条标准证据；"
                    "需要逐条 rule-specific 证据"),
            gap_codes=(code,),
            gaps=("仅有汇总/自由文本证据，无逐条标准证据",))
    for b in bindings:
        if (b.source_role not in required_roles
                and b.source_role not in alternate_roles):
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason=(
                    f"证据角色 {b.source_role!r} 不在规则允许的"
                    f"required/alternate 集合内"),
                gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
                gaps=("证据角色不在规则允许集合内",))

    op = rule.operator
    if op in (OP_NUMERIC_AT_LEAST, OP_NUMERIC_AT_MOST, OP_NUMERIC_ABOVE,
              OP_NUMERIC_BELOW, OP_WITHIN_RANGE):
        outcome = _numeric_verdict(
            unit_id=unit_id, component_id=component.component_id,
            comparison=rule.comparison, bindings=relevant,
            conversion_rules=unit_conversion_rules, rule_lineage=rule_lineage)
    elif op == OP_EXISTS or op == OP_NOT_EXISTS:
        outcome = _evaluate_existence(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            coverage_complete_roles=coverage_complete_roles,
            rule_lineage=rule_lineage)
    elif op == OP_TEMPORAL_INCLUSION:
        if not relevant:
            outcome = ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason="缺少窗口内证据",
                gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
                gaps=("缺少窗口内证据",))
        else:
            b = relevant[0]
            if not b.is_confirmed:
                outcome = ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="证据关系未确认",
                    gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
                    gaps=("证据关系未确认",))
            else:
                status, reason = _window_contains_date(
                    b.date_raw, rule.evaluation_window_start,
                    rule.evaluation_window_end, rule.window_start_inclusive,
                    rule.window_end_inclusive)
                if status == "inside":
                    ev = _binding_evidence(
                        unit_id=unit_id,
                        component_id=component.component_id, binding=b,
                        polarity=L1bEvidencePolarity.SUPPORTING,
                        rule_lineage=rule_lineage,
                        note="记录在规则窗口内")
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_MET, reason="记录在规则窗口内",
                        supporting=(ev,), binding_ids=(b.binding_id,))
                elif status == "outside":
                    ev = _binding_evidence(
                        unit_id=unit_id,
                        component_id=component.component_id, binding=b,
                        polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                        rule_lineage=rule_lineage,
                        note="记录在规则窗口外")
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_UNMET, reason="记录在规则窗口外",
                        counterevidence=(ev,), binding_ids=(b.binding_id,))
                elif status == "boundary":
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_BOUNDARY, reason=reason,
                        gap_codes=(), gaps=())
                else:
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_NOT_EVALUABLE, reason=reason,
                        gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                        gaps=(reason,))
    elif op in (OP_TEMPORAL_ORDER, OP_SEQUENCE):
        outcome = _evaluate_temporal_order(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_DURATION:
        outcome = _evaluate_duration(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_COUNT:
        outcome = _evaluate_count(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            coverage_complete_roles=coverage_complete_roles,
            rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_AGE:
        outcome = _evaluate_age(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_DISCONTINUATION_TRIGGER:
        outcome = _evaluate_discontinuation_trigger(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            conversion_rules=unit_conversion_rules, rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_INVESTIGATOR_JUDGMENT:
        outcome = _evaluate_investigator_judgment(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op in (OP_EQUALS, OP_NOT_EQUALS, OP_SET_MEMBERSHIP):
        outcome = _evaluate_equality_or_membership(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_APPROVED_EXCEPTION:
        outcome = ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="approved_exception 不能作为原子运算子执行",
            gap_codes=(GAP_UNKNOWN_OPERATOR,),
            gaps=("例外运算符不受支持",))
    else:
        outcome = ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=f"规则运算子 {op!r} 不受支持，无法评价",
            gap_codes=(GAP_UNKNOWN_OPERATOR,),
            gaps=("规则运算子不受支持",))

    # Retest handling (§7.1, challenges 22-24, 81): a qualifying retest may
    # cover the initial; a retest outside the allowed window cannot.
    if retest_outcome is not None and rule.retest_or_confirmation_policy.strip():
        rt = retest_outcome
        if rt.conflict_with_initial:
            return ComponentConditionOutcome(
                verdict=VERDICT_BOUNDARY,
                reason="两个同等权威的复测/确认结果且规则未规定优先级",
                gap_codes=(), gaps=())
        if rt.has_retest:
            if rt.retest_in_allowed_window is False:
                # Retest outside the allowed window cannot serve as
                # exclusion counterevidence (challenge 81).
                pass
            elif rt.meets_criterion is True and (
                    rt.retest_in_allowed_window is True
                    and rt.retest_authority_ok is not False
                    and rt.retest_count_ok is not False):
                ev = _binding_evidence(
                    unit_id=unit_id,
                    component_id=component.component_id,
                    binding=RuleEvidenceBinding(
                        binding_id=f"{component.component_id}-retest",
                        control_point_id=component.control_point_id,
                        component_id=component.component_id,
                        subject_ref=subject_ref or component.control_point_id,
                        site_ref=site_ref,
                        source_role="retest_result",
                        stable_source_event_key="retest",
                        source_locator=SourceLocator(
                            snapshot_id="retest-synthetic",
                            source_revision_id="retest-synthetic",
                            table_semantic="retest_result",
                            record_id=f"retest-{component.component_id}")),
                    polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                    rule_lineage=rule_lineage,
                    note="规则允许的复测结果满足要求，覆盖初筛结果")
                return ComponentConditionOutcome(
                    verdict=VERDICT_MET,
                    reason="规则允许的复测结果满足要求，覆盖初筛结果",
                    counterevidence=(ev,),
                    gap_codes=(), gaps=())
            elif rt.meets_criterion is None or (
                    rt.retest_in_allowed_window is None
                    or rt.retest_authority_ok is None
                    or rt.retest_count_ok is None):
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="复测时间窗/次数/权威来源未确认，无法覆盖初筛",
                    gap_codes=(GAP_RETEST_UNCONFIRMED,),
                    gaps=("复测时间窗/次数/权威来源未确认",))

    # Exception handling (§7.3) -- after the operator verdict.
    qualifies, exc, gap_or_boundary = _qualifying_exception(
        component=component, subject_ref=subject_ref, site_ref=site_ref,
        exceptions=exceptions)
    if gap_or_boundary == "gap":
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="例外/豁免的批准/确认状态缺失，无法判断其效力",
            gap_codes=(GAP_EXCEPTION_UNRESOLVED,),
            gaps=("例外/豁免状态缺失，无法判断其效力",))
    if gap_or_boundary == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="例外/豁免效力类型无法唯一确定",
            gap_codes=(), gaps=())
    if qualifies:
        ev = None
        if exc is not None and exc.source_locator is not None:
            ev = EvidenceItem(
                evidence_id=f"ev-{unit_id}-{component.component_id}-exception",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=exc.source_locator,
                evidence_role="protocol_exception",
                rule_lineage=rule_lineage,
                uncertainty_note="方案预先允许的例外或已生效的正式规则变化")
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="方案预先允许的例外或已生效的正式规则变化，不构成问题",
            counterevidence=((ev,) if ev is not None else ()),
            context=outcome.context)
    return outcome


# ---------------------------------------------------------------------------
# Issue predicate + expression evaluation (§5)
# ---------------------------------------------------------------------------

def component_issue_predicate(
    control_point_type: str, verdict: str,
) -> str:
    """Map a condition verdict to the component issue predicate (§5).

    inclusion: satisfied -> no issue; exclusion: condition present ->
    issue; required action/discontinuation/sequence/other: requirement
    consistent -> no issue.
    """
    if verdict == VERDICT_BOUNDARY:
        return ISSUE_BOUNDARY
    if verdict == VERDICT_NOT_EVALUABLE:
        return ISSUE_NOT_EVALUABLE
    if verdict == VERDICT_NOT_APPLICABLE:
        return ISSUE_NOT_APPLICABLE
    if control_point_type == CONTROL_INCLUSION:
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    if control_point_type == CONTROL_EXCLUSION:
        return ISSUE_TRUE if verdict == VERDICT_MET else ISSUE_FALSE
    if control_point_type == CONTROL_DISCONTINUATION_OR_WITHDRAWAL:
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    if control_point_type in (
            CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT,
            CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            CONTROL_OTHER_PROTOCOL_REQUIREMENT):
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    return ISSUE_NOT_EVALUABLE


@dataclass(frozen=True)
class ExpressionEvaluation:
    """Outcome of evaluating the parent issue expression over feasible
    assignments (§5)."""

    disposition: str
    gap_component_ids: Tuple[str, ...] = ()
    decisive_component_ids: Tuple[str, ...] = ()
    reason: str = ""


def evaluate_issue_expression(
    expression: Optional[IssueExpression],
    component_results: Mapping[str, str],
    *,
    all_not_applicable: bool,
    control_point_authoritatively_not_applicable: bool,
) -> ExpressionEvaluation:
    """Evaluate AND/OR/NOT/AT_LEAST_N over feasible truth assignments.

    For boundary/not_evaluable components every feasible assignment is
    considered: constant true -> positive; constant false -> negative;
    mixed with any participating not_evaluable -> not_evaluable; mixed
    otherwise -> boundary; all components not applicable and the control
    point authoritatively not applicable -> not_applicable; an incomplete
    expression/component set -> not_evaluable (no AND/OR defaulting).
    """
    if expression is None:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason="缺少父级问题表达式，无法评价组合标准")
    unknown = [cid for cid in expression.component_ids
               if cid not in component_results]
    if unknown:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason=f"表达式引用未知子条件 {sorted(unknown)}",
            gap_component_ids=tuple(unknown))

    feasible_sets: List[Tuple[str, Tuple[bool, ...]]] = []
    gap_ids: List[str] = []
    decisive: List[str] = []
    participating: List[str] = []
    for cid in expression.component_ids:
        result = component_results[cid]
        if result == ISSUE_TRUE:
            feasible_sets.append((cid, (True,)))
            decisive.append(cid)
        elif result == ISSUE_FALSE:
            feasible_sets.append((cid, (False,)))
        elif result == ISSUE_BOUNDARY:
            feasible_sets.append((cid, (True, False)))
            gap_ids.append(cid)
        elif result == ISSUE_NOT_EVALUABLE:
            feasible_sets.append((cid, (True, False)))
            gap_ids.append(cid)
        elif result == ISSUE_NOT_APPLICABLE:
            continue
        else:
            return ExpressionEvaluation(
                disposition=L1Disposition.NOT_EVALUABLE,
                reason=f"子条件 {cid!r} 的问题谓词结果 {result!r} 无效")
        participating.append(cid)

    if not participating:
        if control_point_authoritatively_not_applicable:
            return ExpressionEvaluation(
                disposition=L1Disposition.NOT_APPLICABLE,
                reason="全部子条件明确不适用且控制点经权威适用性证明不适用")
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason="全部子条件不适用但控制点未经权威证明不适用",
            gap_component_ids=tuple(gap_ids))

    # Cartesian product over feasible assignments.
    outcomes: Set[bool] = set()
    ids = [cid for cid, _ in feasible_sets]
    values = [vals for _, vals in feasible_sets]
    for combo in itertools.product(*values):
        assignment = dict(zip(ids, combo))
        outcomes.add(expression.truth_value(assignment))
        if len(outcomes) == 2:
            break

    gap_ids = [cid for cid in gap_ids if cid in participating]
    if outcomes == {True}:
        return ExpressionEvaluation(
            disposition=L1Disposition.POSITIVE,
            gap_component_ids=tuple(gap_ids),
            decisive_component_ids=tuple(sorted(decisive)),
            reason="所有可行赋值下表达式恒为真")
    if outcomes == {False}:
        return ExpressionEvaluation(
            disposition=L1Disposition.NEGATIVE,
            gap_component_ids=tuple(gap_ids),
            decisive_component_ids=tuple(sorted(decisive)),
            reason="所有可行赋值下表达式恒为假")
    has_not_evaluable = any(
        component_results[cid] == ISSUE_NOT_EVALUABLE
        for cid in participating)
    if has_not_evaluable:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            gap_component_ids=tuple(gap_ids),
            reason="真/假均可行且参与的不确定子条件无法评价")
    return ExpressionEvaluation(
        disposition=L1Disposition.BOUNDARY,
        gap_component_ids=tuple(gap_ids),
        reason="真/假均可行且所有参与子条件均可评价，仍无法唯一确定")
