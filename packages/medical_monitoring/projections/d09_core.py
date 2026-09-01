"""Shared audience vocabulary and visibility helpers for D09 projections."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional, Tuple

from ..risks.d09_contracts import D09TypedInput
from ..risks.d09_evaluator import D09RunResult, evaluate

# ---------------------------------------------------------------------------
# Frozen Chinese forms (contract section 14) and closed display vocabularies
# ---------------------------------------------------------------------------

_FROZEN_DISPOSITION_ZH = {
    "positive": "发现该类中心模式",
    "negative": "在本次可评价范围内未发现该类中心模式（不代表无个体风险）",
    "boundary": "边界情况",
    "not_applicable": "不适用",
    "not_evaluable": "暂无法评价（附原因）",
}

_FROZEN_LIFECYCLE_ZH = {
    "open": "进行中",
    "superseded": "已由规则变更取代",
    "closed_verified": "已核实关闭",
}

_FROZEN_COUNT_ZH = {
    "individual_risk_count_zh": "相关个体风险 {n} 条",
    "affected_subjects_zh": "受影响受试者 {n} 名",
    "event_count_zh": "事件 {n} 起",
    "center_pattern_count_zh": "中心模式 {n} 项",
    "coverage_zh": "本次可评价范围/数据完整性",
    "query_count_zh": "查询草稿 {n} 条",
}

_DENOMINATOR_LABELS_ZH = {
    "enrolled_subjects": "入组受试者",
    "treated_subjects": "接受治疗受试者",
    "evaluable_subjects": "可评价受试者",
    "subject_time": "受试者时间",
    "exposure_time": "暴露时间",
    "expected_assessment_opportunities": "预期评估机会",
}

_UNIT_LABELS_ZH = {"subject": "名", "subject_day": "天", "opportunity": "次"}

_COVERAGE_STATE_ZH = {
    "complete": "完整",
    "partial": "部分",
    "missing": "缺失",
    "not_evaluable": "暂无法评价",
}

_WINDOW_KIND_LABELS_ZH = {
    "calendar_interval": "日历区间",
    "study_day_interval": "研究日区间",
    "subject_time_interval": "受试者时间区间",
    "exposure_time_interval": "暴露时间区间",
}

# Closed Chinese display labels for the frozen catalog vocabularies; unknown
# kinds fall back to a generic natural phrase (never the raw token).
_RISK_KIND_LABELS_ZH = {
    "d01_seriousness_hospital_death": "严重性（住院或死亡）相关个体风险",
    "d08_cross_domain_relation": "跨域关系风险",
}

_GAP_KIND_LABELS_ZH = {
    "missing_required_field": "缺失必填字段",
    "pd_unreported": "疑似未上报 PD",
    "missing_required_assessment": "缺失必做评估",
}

# Forbidden internal labels and raw enum/status/backend tokens in any
# user-facing Chinese string (contract section 14, worker_02 contract).
_FORBIDDEN_INTERNAL_TERMS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
)

_FORBIDDEN_RAW_TOKENS = (
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "permitted", "suppressed", "qualified",
    "create", "continue", "update", "propose_close", "reopen", "supersede",
    "open", "superseded", "closed_verified", "first_seen",
    "gate", "ledger", "handoff", "envelope", "payload", "evaluator",
    "projection", "hotspot", "deep_link", "risk_count", "query_count",
    "clue_count", "center_pattern", "site_pattern",
)

UNAVAILABLE_SOURCE_ZH = "来源暂无法定位"

_PRIORITY_RANK = {"high": 0, "medium": 1}

_ALGORITHM_VERSION = "d09_v1"

_STRUCTURED_REF_KEY_RE = re.compile(
    r"(?i)(?:pattern(?:_definition)?_(?:id|ref)|"
    r"rule_(?:id|ref)|mode_contract_(?:version|id|ref)|"
    r"window(?:_instance|_definition)?_(?:id|ref)|"
    r"(?:source_)?revision(?:_(?:id|ref))?|"
    r"scope_binding_(?:id|ref)|policy_(?:id|ref))\s*[:=：]"
)

_STRUCTURED_REF_COMPACT_RE = re.compile(
    r"(?i)(?:pattern(?:definition)?(?:id|ref)|rule(?:id|ref)|"
    r"modecontract(?:version|id|ref)|"
    r"window(?:instance|definition)?(?:id|ref)|"
    r"(?:source)?revision(?:id|ref)?|"
    r"scopebinding(?:id|ref)|policy(?:id|ref))[:=]"
)


class D09ProjectionError(Exception):
    """Integrity violation in the D09 projection layer (fail closed)."""


def _assert_authoritative_result(
    typed: D09TypedInput,
    result: D09RunResult,
) -> None:
    """Bind every projection to the evaluator's deterministic current result."""
    if not isinstance(result, D09RunResult) or result.typed != typed:
        raise D09ProjectionError("result is not bound to the supplied typed input")
    if result != evaluate(typed):
        raise D09ProjectionError("result is not the authoritative evaluation")


def _assert_clean_zh(*texts: str) -> None:
    """Reject forbidden internal labels and raw enum/status/backend tokens in
    user-facing Chinese strings."""
    for text in texts:
        for term in _FORBIDDEN_INTERNAL_TERMS:
            if term in text:
                raise D09ProjectionError(
                    f"forbidden internal label {term!r} in user-facing text")
        lowered = text.lower()
        for token in _FORBIDDEN_RAW_TOKENS:
            if token in lowered:
                raise D09ProjectionError(
                    f"raw internal token {token!r} in user-facing text")


def _assert_no_structured_ref_in_text(
    typed: D09TypedInput,
    *texts: str,
) -> None:
    """Prevent trace/contract identifiers from entering audience prose."""
    definition = typed.pattern_definition
    policy = typed.center_query_policy
    refs = {
        typed.mode_contract_version,
        typed.scope_binding.scope_binding_id,
        definition.pattern_definition_id,
        definition.positive_rule_ref,
        definition.monitoring_priority_rule_ref,
        definition.center_query_policy_id,
        definition.minimum_member_subject_count_ref,
        definition.required_window_count_ref,
        definition.opportunity_contract_id,
        definition.authority_version,
        policy.policy_id,
        policy.redundancy_rule_ref,
        policy.pd_wording_rule_ref,
        *typed.source_revision_set,
        *definition.counterevidence_rule_refs,
    }
    for window in typed.analysis_windows:
        refs.update((
            window.window_instance_id,
            window.analysis_window_stable_id,
            window.window_definition_id,
            window.cutoff_id,
            window.scope_binding_stable_id,
        ))
    for text in texts:
        if any(unicodedata.category(character).startswith("C")
               for character in text):
            raise D09ProjectionError(
                "invisible format character in user-facing text")
        normalized_text = unicodedata.normalize("NFKC", text)
        compact_ascii = "".join(
            character for character in normalized_text
            if character.isascii()
            and (character.isalnum() or character in ":=")
        )
        if (_STRUCTURED_REF_KEY_RE.search(normalized_text)
                or _STRUCTURED_REF_COMPACT_RE.search(compact_ascii)):
            raise D09ProjectionError(
                "structured engineering reference syntax in user-facing text")
        for ref in refs:
            if not ref:
                continue
            normalized_ref = unicodedata.normalize("NFKC", ref)
            compact_ref = "".join(
                character for character in normalized_ref
                if character.isascii() and character.isalnum()
            )
            if (normalized_ref in normalized_text
                    or (compact_ref and compact_ref in compact_ascii)):
                raise D09ProjectionError(
                    "structured engineering reference in user-facing text")


def _fmt(template: str, value: int) -> str:
    return template.replace("{n}", str(value))


def _coverage_state(typed: D09TypedInput, result: D09RunResult) -> str:
    """Closed L0/L1 coverage summary over the required producer domains."""
    required = set(typed.pattern_definition.required_producer_domains)
    relevant = [c for c in typed.coverage if c.producer_domain in required]
    if not relevant:
        return "missing"
    if any(c.l0_status != "covered" for c in relevant):
        return "missing"
    if any(c.l1_medical_completeness_state == "not_evaluable"
           for c in relevant):
        return "not_evaluable"
    if any(c.l1_medical_completeness_state == "missing" for c in relevant):
        return "missing"
    if any(c.l1_medical_completeness_state == "partial" for c in relevant):
        return "partial"
    return "complete"


def _disposition_zh(typed: D09TypedInput, disposition: str) -> str:
    lexicon = typed.audience_lexicon
    if lexicon.disposition_zh:
        label = lexicon.disposition_zh.get(disposition)
        if label:
            return label
    return _FROZEN_DISPOSITION_ZH.get(disposition, "")


def _lifecycle_zh(typed: D09TypedInput, result: D09RunResult) -> Optional[str]:
    """Lifecycle display label: superseded lineage wins; otherwise an open
    (in-progress) pattern when a handoff is live."""
    lineage = typed.lineage_context
    key: Optional[str] = None
    if lineage.lineage_relation == "superseded_by_rule_or_method_change":
        key = "superseded"
    elif result.downstream_handoff and result.unit_count == 1:
        key = "open"
    if key is None:
        return None
    lexicon = typed.audience_lexicon
    if lexicon.lifecycle_zh:
        label = lexicon.lifecycle_zh.get(key)
        if label:
            return label
    return _FROZEN_LIFECYCLE_ZH.get(key)


def _all_members(typed: D09TypedInput):
    return list(typed.subject_risk_members) + list(typed.gap_members) + list(
        typed.change_ledger_members)


def _resolve_visibility_members(
    typed: D09TypedInput,
    result: D09RunResult,
):
    """Closed resolution of the audience member partition (contract section
    7.3): (evaluation_refs, projectable_refs, hidden_refs) as sorted tuples.

    A non-empty explicit ``VisibilityDecision`` set is authoritative for its
    plane; an empty set keeps the schema's backward-compatible implicit
    plane (evaluation = all envelope members, hidden = the typed hidden
    refs, projectable = evaluation minus hidden).  Fails closed on unknown
    refs, projectable/hidden overlap, projectable outside evaluation, hidden
    outside evaluation, or an explicit partition that does not reconcile
    with the evaluation set.  Every audience surface consumes this single
    resolved partition.
    """
    all_refs = tuple(sorted(m.member_id for m in _all_members(typed)))
    all_set = set(all_refs)
    visibility = typed.visibility_decision
    explicit_eval = set(visibility.evaluation_member_refs or ())
    explicit_proj = set(visibility.projectable_member_refs or ())
    explicit_hidden = set(visibility.hidden_member_refs or ())
    implicit_hidden = set(result.hidden_member_refs or ())
    explicit_all = explicit_eval | explicit_proj | explicit_hidden
    unknown = explicit_all - all_set
    if unknown:
        raise D09ProjectionError(
            "unknown member refs in visibility decision: "
            f"{sorted(unknown)!r}")
    hidden = explicit_hidden if explicit_hidden else implicit_hidden
    evaluation = explicit_eval if explicit_eval else all_set
    projectable = explicit_proj if explicit_proj else evaluation - hidden
    if projectable - evaluation:
        raise D09ProjectionError(
            "projectable refs outside the evaluation set")
    if hidden - evaluation:
        raise D09ProjectionError("hidden refs outside the evaluation set")
    if projectable & hidden:
        raise D09ProjectionError("projectable/hidden member overlap")
    if explicit_proj and explicit_hidden and (
            projectable | hidden) != evaluation:
        raise D09ProjectionError(
            "explicit visibility partition does not reconcile with the "
            "evaluation set")
    return (tuple(sorted(evaluation)), tuple(sorted(projectable)),
            tuple(sorted(hidden)))


def _projectable_members(typed: D09TypedInput, result: D09RunResult):
    """(risks, gaps, changes) restricted to the resolved projectable
    member plane of the authoritative visibility partition."""
    _evaluation, projectable, _hidden = _resolve_visibility_members(
        typed, result)
    projectable_set = set(projectable)
    risks = [m for m in typed.subject_risk_members
             if m.member_id in projectable_set]
    gaps = [m for m in typed.gap_members if m.member_id in projectable_set]
    changes = [m for m in typed.change_ledger_members
               if m.member_id in projectable_set]
    return risks, gaps, changes


def _visible_counts(typed: D09TypedInput, result: D09RunResult):
    """(individual_risk, affected_subjects, events, gap_opportunities)
    computed over the projectable member plane only; identical to the
    evaluation counts when no member is hidden.  Affected/event/gap counts
    mirror the evaluator's disposition gating (positive/boundary only)."""
    if result.unit_count == 0:
        return 0, 0, 0, 0
    risks, gaps, changes = _projectable_members(typed, result)
    kind = typed.pattern_definition.pattern_kind
    counted = result.disposition in ("positive", "boundary")
    if kind == "repeated_subject_risk":
        # Dedup trigger mirrors the evaluator: any verified same-origin
        # member dedups the (public identity, subject) pairs.
        if any(m.origin_decision == "verified_same_origin"
               for m in typed.subject_risk_members):
            seen: Dict[Tuple[str, str], Any] = {}
            for m in risks:
                seen.setdefault((m.public_r4_risk_identity,
                                 m.subject_stable_id), m)
            deduped = list(seen.values())
        else:
            deduped = list(risks)
        in_cutoff = [m for m in deduped
                     if m.cutoff_relation == "in_cutoff"]
        if not counted:
            return len(deduped), 0, 0, 0
        return (len(deduped),
                len({m.subject_stable_id for m in in_cutoff}),
                len({m.source_event_identity for m in in_cutoff}), 0)
    if kind == "systematic_data_or_process_gap":
        if not counted:
            return 0, 0, 0, 0
        return 0, len({m.subject_stable_id for m in gaps}), 0, len(gaps)
    if kind == "within_site_time_trend":
        if not counted:
            return 0, 0, 0, 0
        return 0, len({m.subject_stable_id for m in changes}), 0, 0
    return 0, 0, 0, 0


def _numerator_subjects(typed: D09TypedInput, result: D09RunResult):
    """Unique numerator subjects over the projectable member plane."""
    risks, gaps, changes = _projectable_members(typed, result)
    kind = typed.pattern_definition.pattern_kind
    if kind == "repeated_subject_risk":
        if any(m.origin_decision == "verified_same_origin"
               for m in typed.subject_risk_members):
            seen: Dict[Tuple[str, str], Any] = {}
            for m in risks:
                seen.setdefault((m.public_r4_risk_identity,
                                 m.subject_stable_id), m)
            deduped = list(seen.values())
        else:
            deduped = list(risks)
        return {m.subject_stable_id for m in deduped
                if m.cutoff_relation == "in_cutoff"}
    if kind == "systematic_data_or_process_gap":
        return {m.subject_stable_id for m in gaps}
    if kind == "within_site_time_trend":
        return {m.subject_stable_id for m in changes}
    return set()


def _evaluation_window_instance_ref(typed: D09TypedInput) -> str:
    if typed.analysis_windows:
        return typed.analysis_windows[-1].window_instance_id
    return ""



