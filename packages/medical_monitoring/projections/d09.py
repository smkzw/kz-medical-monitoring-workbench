"""R4-D09 renderer-neutral projection layer (worker_02).

Consumes only a validated ``D09TypedInput`` bundle and the deterministic
evaluator's ``D09RunResult`` and produces immutable, renderer-neutral
projection objects:

* :func:`build_d09_audience_projection` -- audience visibility: projectable
  vs evaluation member sets, hidden-member count, risk/Query/Journey/hotspot
  presence, rate projection state and the frozen coverage phrase
  ``本次可评价范围/数据完整性``;
* :func:`build_d09_count_surface` -- the separated count surface
  (``individual_risk_count`` / ``affected_subject_count`` / ``event_count`` /
  ``gap_opportunity_count`` / ``center_pattern_count`` / ``clue_count`` /
  ``query_count``) with the frozen Chinese forms; the six mandated counts are
  never summed;
* :func:`build_d09_risk_marker` -- the D09 center-pattern risk marker
  (domain ``D09_center_pattern``, ``d09_public_v1``) with the stable public
  identity of contract section 5.1;
* :func:`build_d09_hotspots` -- hotspot subject rows; projections only,
  never L1 units or RiskInstances; high-priority members stay visible even
  on negative/boundary dispositions and the n=1 boundary case keeps its
  mandatory hotspot;
* :func:`build_d09_deep_links` -- verified one-hop deep-link targets with an
  explicit unavailable state (``来源暂无法定位``) and no fabricated jump;
* :func:`build_d09_query_draft` / :func:`validate_query_draft` -- at most
  one natural-Chinese three-sentence Query draft per positive unit
  (``依据`` / ``发现`` / ``行动项``), listing the complete uncovered
  projectable member set without truncation as a finite natural record list
  (no engineering ids in prose; definition/rule/window/mode/revision ids
  stay in the structured ``basis_refs`` / ``source_revision_refs`` trace
  fields), with the two-part PD wording gate (``请核实是否为 PD``) driven
  by the frozen Query policy and the exact structured ``pd_unreported``
  member fact; evidence completeness is mandatory (every listed member must
  contribute a locatable locator or the draft fails closed);
* :func:`d09_public_risk_identity` / :func:`d09_evaluation_content_identity`
  / :func:`build_d09_r2_handoff` / :func:`validate_d09_r2_handoff` --
  replay-stable R2 lifecycle handoff (contract section 10): create is the
  only action without a prior ref; continue/supersede require a compatible
  prior identity; broken coverage carries forward and never proposes
  closure; rule/method change supersedes.

Boundaries honoured (contract sections 1/10/11/12/14, worker_02 contract):

* the projection never reads the frozen catalog/oracle/registry/quota or any
  generator/test module, never branches on case/fixture/test identifiers and
  never interprets sentinels, display labels or hash recipes;
* global admission gates and admitted not-evaluable units emit no risk
  marker, Query draft, Journey payload, hotspot rows or R2 create/update
  handoff; a boundary may preserve visible hotspot context but never becomes
  a D09 risk or Query; gap-only positives keep zero individual risks while
  retaining affected-subject/gap-opportunity/center-pattern counts;
* the audience plane never leaks hidden members through rows, counts,
  ordering, rates, Query evidence, hotspot details, locators or tooltips;
  suppressed/qualified rate states never show a misleading precision rate;
  Query is a draft only (``draft_only=True``): never sent, never a task or
  workflow state; R2 lifecycle changes themselves are out of scope (handoff
  objects only).

All data is synthetic and offline.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..risks.d09_contracts import (
    D09_DOMAIN_ID,
    D09_PUBLIC_IDENTITY_VERSION,
    D09TypedInput,
    DENOMINATOR_UNITS,
    d09_content_hash,
    d09_unit_stable_core,
)
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


# ---------------------------------------------------------------------------
# Audience visibility projection (contract sections 7.3/11/14)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09AudienceProjection:
    """Renderer-neutral audience projection for one run.

    ``projectable_member_refs`` is the only member plane the audience may
    see; ``evaluation_member_refs`` may exceed it.  ``disclosure_leak_present``
    is always False because the projection layer fails closed whenever a
    hidden member would reach any audience payload.
    """

    audience_scope_id: str
    projectable_member_refs: Tuple[str, ...]
    evaluation_member_refs: Tuple[str, ...]
    hidden_member_refs: Tuple[str, ...]
    hidden_member_count: int
    audience_payload_present: bool
    risk_present: bool
    query_present: bool
    journey_marker_present: bool
    hotspot_present: bool
    rate_projection_state: str
    visible_n: Optional[int]
    eligible_n: Optional[int]
    coverage_state: str
    coverage_zh: str
    disposition_zh: str
    primary_reason: str
    disclosure_leak_present: bool


def build_d09_audience_projection(
    typed: D09TypedInput,
    result: D09RunResult,
) -> D09AudienceProjection:
    """Project the evaluation onto the audience plane (contract sections
    7.3/11/14)."""
    _assert_authoritative_result(typed, result)
    evaluation, projectable, hidden = _resolve_visibility_members(
        typed, result)
    if set(hidden) & set(projectable):
        raise D09ProjectionError(
            "hidden member leaked into the projectable set")
    unit = result.units[0] if result.unit_count else None
    disposition = result.disposition
    # Audience presence reflects the actual built audience-safe payloads, not
    # raw internal counts: a gate or an admitted not_evaluable unit carries
    # no audience payload; the independent count/status surface may still
    # explain 暂无法评价.
    # A positive/boundary unit whose entire evaluation member plane is hidden
    # has no audience-safe medical payload.  A closed negative may legitimately
    # have no members and still project its status/count surface.
    payload = (unit is not None and disposition != "not_evaluable"
               and (not evaluation or bool(projectable)))
    risk_present = build_d09_risk_marker(typed, result) is not None
    query_present = build_d09_query_draft(typed, result) is not None
    journey = bool(build_d09_deep_links(typed, result))
    coverage = _coverage_state(typed, result)
    coverage_zh = (typed.audience_lexicon.coverage_zh
                   or _FROZEN_COUNT_ZH["coverage_zh"])
    _assert_clean_zh(coverage_zh)
    disposition_zh = _disposition_zh(typed, disposition)
    _assert_clean_zh(disposition_zh)
    return D09AudienceProjection(
        audience_scope_id=typed.visibility_decision.audience_scope_id,
        projectable_member_refs=projectable,
        evaluation_member_refs=evaluation,
        hidden_member_refs=hidden,
        hidden_member_count=len(hidden),
        audience_payload_present=payload,
        risk_present=risk_present,
        query_present=query_present,
        journey_marker_present=journey,
        hotspot_present=bool(build_d09_hotspots(typed, result)),
        rate_projection_state=typed.visibility_decision.rate_projection_state,
        visible_n=typed.visibility_decision.visible_n,
        eligible_n=typed.visibility_decision.eligible_n,
        coverage_state=coverage,
        coverage_zh=coverage_zh,
        disposition_zh=disposition_zh,
        primary_reason=result.primary_reason,
        disclosure_leak_present=False,
    )


# ---------------------------------------------------------------------------
# Separated count surface (contract sections 10/14)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09ProjectionCountSurface:
    """Separated count surface.

    ``individual_risk_count`` / ``affected_subject_count`` / ``event_count`` /
    ``gap_opportunity_count`` / ``center_pattern_count`` / ``clue_count`` /
    ``query_count`` are kept strictly separate and are never summed.  Raw
    ``*_count`` and ``visible_*`` fields are audience-safe counts.  The raw
    evaluation-plane counts remain on ``D09RunResult`` and never cross this
    projection boundary.  Both sets are identical when no member is hidden.
    Chinese forms use the frozen contract section 14 wording; the rate is
    only present under ``permitted`` rate projection with no hidden members.
    """

    evaluation_window_instance_ref: str
    individual_risk_count: int
    affected_subject_count: int
    event_count: int
    gap_opportunity_count: int
    center_pattern_count: int
    clue_count: int
    query_count: int
    hidden_member_count: int
    visible_individual_risk_count: int
    visible_affected_subject_count: int
    visible_event_count: int
    visible_gap_opportunity_count: int
    visible_n: Optional[int]
    eligible_n: Optional[int]
    rate_projection_state: str
    individual_risk_zh: str
    affected_subjects_zh: str
    event_count_zh: str
    center_pattern_count_zh: str
    query_count_zh: Optional[str]
    clue_count_zh: Optional[str]
    coverage_zh: str
    coverage_state_zh: str
    denominator_zh: Optional[str]
    rate_zh: Optional[str]
    disposition_zh: str
    lifecycle_zh: Optional[str]


def _half_up(value: float, precision: int) -> float:
    factor = 10 ** precision
    return math.floor(value * factor + 0.5) / factor


def build_d09_count_surface(
    typed: D09TypedInput,
    result: D09RunResult,
) -> D09ProjectionCountSurface:
    """Build the separated count surface with frozen Chinese forms."""
    _assert_authoritative_result(typed, result)
    lexicon = typed.audience_lexicon
    evaluation, projectable, hidden = _resolve_visibility_members(
        typed, result)
    hidden_count = len(hidden)
    visible = _visible_counts(typed, result)
    coverage_state = _coverage_state(typed, result)
    coverage_zh = lexicon.coverage_zh or _FROZEN_COUNT_ZH["coverage_zh"]
    rate_state = typed.visibility_decision.rate_projection_state
    denominator_kind = result.denominator_kind
    unit_zh = _UNIT_LABELS_ZH.get(DENOMINATOR_UNITS.get(denominator_kind, ""),
                                  "")
    label_zh = _DENOMINATOR_LABELS_ZH.get(denominator_kind, denominator_kind)
    denominator_zh = (
        " ".join(part for part in
                 (label_zh, str(result.denominator_value), unit_zh) if part)
        if result.denominator_value > 0 or unit_zh else None)
    rate_zh: Optional[str] = None
    if (rate_state == "permitted" and hidden_count == 0
            and result.denominator_value > 0
            and denominator_kind in _DENOMINATOR_LABELS_ZH):
        numerator = result.affected_subject_count
        precision = max(0, typed.numeric_policy.display_precision)
        percent = _half_up(100.0 * numerator / result.denominator_value,
                           precision)
        rate_zh = f"{numerator}/{result.denominator_value}（{percent:.{precision}f}%）"

    individual_risk_zh = _fmt(
        lexicon.individual_risk_count_zh
        or _FROZEN_COUNT_ZH["individual_risk_count_zh"],
        visible[0])
    affected_subjects_zh = _fmt(
        lexicon.affected_subjects_zh or _FROZEN_COUNT_ZH["affected_subjects_zh"],
        visible[1])
    event_count_zh = _fmt(
        lexicon.event_count_zh or _FROZEN_COUNT_ZH["event_count_zh"],
        visible[2])
    audience_has_unit = not evaluation or bool(projectable)
    center_pattern_count = (
        result.center_pattern_count if audience_has_unit else 0)
    clue_count = result.clue_count if audience_has_unit else 0
    query_count = int(build_d09_query_draft(typed, result) is not None)
    center_pattern_count_zh = _fmt(
        lexicon.center_pattern_count_zh
        or _FROZEN_COUNT_ZH["center_pattern_count_zh"],
        center_pattern_count)
    query_count_zh = _fmt(_FROZEN_COUNT_ZH["query_count_zh"], query_count)
    coverage_state_zh = _COVERAGE_STATE_ZH.get(coverage_state, coverage_state)
    disposition_zh = _disposition_zh(typed, result.disposition)
    lifecycle_zh = _lifecycle_zh(typed, result)
    _assert_clean_zh(individual_risk_zh, affected_subjects_zh,
                     event_count_zh, center_pattern_count_zh,
                     query_count_zh, coverage_zh, coverage_state_zh,
                     denominator_zh or "", rate_zh or "",
                     disposition_zh, lifecycle_zh or "")
    return D09ProjectionCountSurface(
        evaluation_window_instance_ref=_evaluation_window_instance_ref(typed),
        individual_risk_count=visible[0],
        affected_subject_count=visible[1],
        event_count=visible[2],
        gap_opportunity_count=visible[3],
        center_pattern_count=center_pattern_count,
        clue_count=clue_count,
        query_count=query_count,
        hidden_member_count=hidden_count,
        visible_individual_risk_count=visible[0],
        visible_affected_subject_count=visible[1],
        visible_event_count=visible[2],
        visible_gap_opportunity_count=visible[3],
        visible_n=typed.visibility_decision.visible_n,
        eligible_n=typed.visibility_decision.eligible_n,
        rate_projection_state=rate_state,
        individual_risk_zh=individual_risk_zh,
        affected_subjects_zh=affected_subjects_zh,
        event_count_zh=event_count_zh,
        center_pattern_count_zh=center_pattern_count_zh,
        query_count_zh=query_count_zh,
        clue_count_zh=None,
        coverage_zh=coverage_zh,
        coverage_state_zh=coverage_state_zh,
        denominator_zh=denominator_zh,
        rate_zh=rate_zh,
        disposition_zh=disposition_zh,
        lifecycle_zh=lifecycle_zh,
    )


# ---------------------------------------------------------------------------
# D09 center-pattern risk marker (contract sections 5.1/10)
# ---------------------------------------------------------------------------


def d09_public_risk_identity(typed: D09TypedInput) -> Dict[str, Any]:
    """Stable public D09 risk identity (contract section 5.1 canonical
    tuple): excludes run/snapshot ids, computed dates, revisions and display
    text; never merges with D01-D08 public identities."""
    definition = typed.pattern_definition
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    return {
        "project_ref": typed.project_ref,
        "domain_id": D09_DOMAIN_ID,
        "scope_type": "site",
        "site_stable_id": typed.site_stable_id,
        "stable_source_or_event_identity": (
            definition.pattern_definition_id,
            window.analysis_window_stable_id if window else "",
            typed.stratum.stratum_key,
        ),
        "normalized_concept": (
            definition.pattern_kind,
            definition.pattern_definition_id,
        ),
        "temporal_window": (
            window.window_kind if window else None,
            window.window_definition_id if window else None,
        ),
        "public_identity_version": D09_PUBLIC_IDENTITY_VERSION,
        "scope_binding_id": typed.scope_binding.scope_binding_id,
    }


@dataclass(frozen=True)
class D09RiskMarker:
    """D09 center-pattern RiskInstance marker (contract sections 5.1/10).

    An audience projection: references only the resolved projectable
    member/locator set.  The public identity is revision-free and replay
    stable; run/snapshot ids never enter it.  The R2 lifecycle handoff
    carries the complete unit member set separately."""

    marker_id: str
    public_risk_identity: Dict[str, Any]
    stable_core: str
    risk_owner: str
    risk_kind: str
    aggregation_level: str
    member_refs: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    content_hash: str


def build_d09_risk_marker(
    typed: D09TypedInput,
    result: D09RunResult,
) -> Optional[D09RiskMarker]:
    """Build the center-pattern risk marker for the run's positive unit.

    Returns ``None`` unless the run carries exactly one D09 center-pattern
    risk (``risk_count == 1``) with at least one projectable member.
    Boundary/negative/not-applicable/not-evaluable and gate runs never get a
    marker.  The marker is an audience projection: it references only the
    resolved projectable member/locator set (the R2 lifecycle handoff may
    retain the complete unit member set separately).
    """
    _assert_authoritative_result(typed, result)
    if result.risk_count != 1 or result.unit_count != 1:
        return None
    public_identity = d09_public_risk_identity(typed)
    risks, gaps, changes = _projectable_members(typed, result)
    members = risks + gaps + changes
    if not members:
        return None
    member_refs = tuple(sorted(m.member_id for m in members))
    locators = tuple(sorted({locator
                             for m in members
                             for locator in m.source_locator_refs}))
    marker_id = d09_content_hash({
        "public_d09_risk_identity": public_identity,
        "stable_core": result.units[0].stable_core,
        "member_refs": list(member_refs),
    })
    core = {
        "marker_id": marker_id,
        "public_risk_identity": public_identity,
        "stable_core": result.units[0].stable_core,
        "risk_owner": "D09",
        "risk_kind": "center_pattern",
        "aggregation_level": "site_pattern",
        "member_refs": list(member_refs),
        "source_locator_ids": list(locators),
    }
    return D09RiskMarker(
        marker_id=marker_id,
        public_risk_identity=public_identity,
        stable_core=result.units[0].stable_core,
        risk_owner="D09",
        risk_kind="center_pattern",
        aggregation_level="site_pattern",
        member_refs=member_refs,
        source_locator_ids=locators,
        content_hash=d09_content_hash(core),
    )


# ---------------------------------------------------------------------------
# Hotspot subject rows (contract section 11)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09HotspotProjection:
    """One hotspot subject row.

    A projection only -- never an L1 unit and never a RiskInstance.  Only
    projectable members are referenced; hidden members never appear in rows,
    anchors, locators or ordering.
    """

    projection_id: str
    site_ref: str
    evaluation_window_instance_ref: str
    subject_ref: str
    member_risk_refs: Tuple[str, ...]
    gap_member_refs: Tuple[str, ...]
    monitoring_priority: Optional[str]
    priority_rule_ref: str
    visit_or_time_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    projectability_decision_ref: str


def _member_anchors(member: Any) -> Tuple[str, ...]:
    """Journey/Profile/Timeline anchors only when present and typed as
    resolved (contract section 11).

    A change-ledger member is anchored on its typed current window instance
    ref; both current and prior refs must be present, otherwise the member
    has no locatable anchor (the link becomes unavailable, never a locatable
    link without an anchor).
    """
    if member.member_kind == "subject_risk":
        return (member.event_time_ref,) if member.event_time_ref else ()
    if member.member_kind == "gap_opportunity":
        if member.anchor_resolution_state != "resolved":
            return ()
        return tuple(ref for ref in member.visit_or_time_anchor_refs if ref)
    if member.member_kind == "change_ledger":
        if member.current_window_instance_ref and member.prior_window_instance_ref:
            return (member.current_window_instance_ref,)
        return ()
    return ()


def _member_locator(member: Any) -> Optional[str]:
    """First source locator only when the member is typed locatable."""
    if not member.source_locator_refs:
        return None
    state = getattr(member, "source_locator_resolution_state", "locatable")
    if state != "locatable":
        return None
    return member.source_locator_refs[0]


def build_d09_hotspots(
    typed: D09TypedInput,
    result: D09RunResult,
) -> Tuple[D09HotspotProjection, ...]:
    """List hotspot subject rows (contract section 11).

    A subject row is projected when any of the following typed facts hold:

    * a projectable member carries ``monitoring_priority == high`` (visible
      even on negative/boundary dispositions);
    * the subject's projectable members span more than one producer domain;
    * the disposition is positive and the subject is a numerator subject;
    * the disposition is boundary, the pattern kind is
      ``repeated_subject_risk`` and exactly one subject is affected (the
      n=1 mandatory boundary hotspot).
    """
    _assert_authoritative_result(typed, result)
    if result.unit_count != 1 or result.disposition not in (
            "positive", "boundary", "negative"):
        return ()
    risks, gaps, changes = _projectable_members(typed, result)
    members_by_subject: Dict[str, List[Any]] = {}
    for member in risks + gaps + changes:
        members_by_subject.setdefault(member.subject_stable_id,
                                      []).append(member)
    numerator = _numerator_subjects(typed, result)
    n1_subject: Optional[str] = None
    if (result.disposition == "boundary"
            and typed.pattern_definition.pattern_kind == "repeated_subject_risk"
            and result.affected_subject_count == 1 and numerator):
        n1_subject = next(iter(numerator))
    window_instance = _evaluation_window_instance_ref(typed)
    rows: List[D09HotspotProjection] = []
    for subject in sorted(members_by_subject):
        members = members_by_subject[subject]
        priorities = [m.monitoring_priority for m in members
                      if getattr(m, "monitoring_priority", None)]
        domains = {m.producer_domain for m in members}
        high = any(p == "high" for p in priorities)
        multi_domain = len(domains) > 1
        eligible = (high or multi_domain
                    or (result.disposition == "positive"
                        and subject in numerator)
                    or subject == n1_subject)
        if not eligible:
            continue
        risk_refs = tuple(sorted(
            m.member_id for m in members if m.member_kind == "subject_risk"))
        gap_refs = tuple(sorted(
            m.member_id for m in members
            if m.member_kind == "gap_opportunity"))
        anchors = tuple(sorted({anchor
                                for m in members
                                for anchor in _member_anchors(m)}))
        locator_set: set = set()
        for m in members:
            locator = _member_locator(m)
            if locator is not None:
                locator_set.add(locator)
        locators = tuple(sorted(locator_set))
        priority = ("high" if high
                    else "medium" if any(p == "medium" for p in priorities)
                    else None)
        projection_id = d09_content_hash({
            "site_ref": typed.site_stable_id,
            "window_instance": window_instance,
            "subject_ref": subject,
            "member_refs": list(risk_refs + gap_refs),
            "monitoring_priority": priority,
        })
        rows.append(D09HotspotProjection(
            projection_id=projection_id,
            site_ref=typed.site_stable_id,
            evaluation_window_instance_ref=window_instance,
            subject_ref=subject,
            member_risk_refs=risk_refs,
            gap_member_refs=gap_refs,
            monitoring_priority=priority,
            priority_rule_ref=typed.pattern_definition.monitoring_priority_rule_ref,
            visit_or_time_anchor_refs=anchors,
            source_locator_refs=locators,
            projectability_decision_ref=typed.visibility_decision.audience_scope_id,
        ))
    rows.sort(key=lambda row: (_PRIORITY_RANK.get(row.monitoring_priority, 99),
                               row.subject_ref))
    return tuple(rows)


# ---------------------------------------------------------------------------
# Verified one-hop deep links (contract section 11)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09DeepLinkTarget:
    """One verified one-hop deep-link target.

    ``target_state`` is ``locatable`` only when the member's source locator
    resolves and no typed anchor is left unresolved; otherwise it is
    ``unavailable`` with ``unavailable_message == 来源暂无法定位`` and no
    fabricated jump target.  ``return_state_key`` is the member's stable
    public identity so the renderer can return to the same state.
    """

    link_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    site_ref: str
    subject_ref: str
    evaluation_window_instance_ref: str
    member_ref: str
    member_kind: str
    visit_or_time_anchor: Optional[str]
    anchor_resolution_state: str
    source_locator: Optional[str]
    locator_resolution_state: str
    target_state: str
    unavailable_message: Optional[str]
    return_state_key: str


def _build_link(typed: D09TypedInput, result: D09RunResult, member: Any,
                window_instance: str, return_state_key: str) -> D09DeepLinkTarget:
    locator = _member_locator(member)
    locator_state = getattr(member, "source_locator_resolution_state",
                            "locatable" if member.source_locator_refs
                            else "missing")
    anchors = _member_anchors(member)
    anchor = anchors[0] if anchors else None
    # every member kind requires a typed anchor for a locatable link: a
    # subject-risk member with an empty event time, a gap member with no
    # anchor (even when its state says resolved) and a trend member with a
    # missing window ref are all unavailable with 来源暂无法定位
    anchor_state = "resolved" if anchor is not None else "unresolved"
    if member.member_kind == "gap_opportunity" and (
            member.anchor_resolution_state == "unresolved"):
        anchor_state = "unresolved"
        anchor = None
    locatable = (locator is not None and anchor_state == "resolved")
    # An unavailable target never exposes a locator or anchor: no fabricated
    # jump and no half-open target (contract section 11).
    exposed_locator = locator if locatable else None
    exposed_anchor = anchor if locatable else None
    link_id = d09_content_hash({
        "site_ref": typed.site_stable_id,
        "subject_ref": member.subject_stable_id,
        "member_ref": member.member_id,
        "window_instance": window_instance,
        "locator": exposed_locator or "",
        "anchor": exposed_anchor or "",
    })
    return D09DeepLinkTarget(
        link_id=link_id,
        project_ref=typed.project_ref,
        run_ref=typed.run_ref,
        snapshot_ref=typed.snapshot_ref,
        site_ref=typed.site_stable_id,
        subject_ref=member.subject_stable_id,
        evaluation_window_instance_ref=window_instance,
        member_ref=member.member_id,
        member_kind=member.member_kind,
        visit_or_time_anchor=exposed_anchor,
        anchor_resolution_state=anchor_state,
        source_locator=exposed_locator,
        locator_resolution_state=locator_state,
        target_state="locatable" if locatable else "unavailable",
        unavailable_message=None if locatable else UNAVAILABLE_SOURCE_ZH,
        return_state_key=return_state_key,
    )


def build_d09_deep_links(
    typed: D09TypedInput,
    result: D09RunResult,
) -> Tuple[D09DeepLinkTarget, ...]:
    """Build the one-hop deep-link targets for projectable members.

    Gate and admitted not-evaluable runs emit none; positive/boundary/
    negative runs preserve the one-hop entry to individual risk.  Missing or
    unresolvable locators/anchors produce ``来源暂无法定位`` with no
    fabricated jump; hidden members never produce a link row.
    """
    _assert_authoritative_result(typed, result)
    if result.unit_count != 1 or result.disposition not in (
            "positive", "boundary", "negative"):
        return ()
    risks, gaps, changes = _projectable_members(typed, result)
    window_instance = _evaluation_window_instance_ref(typed)
    links: List[D09DeepLinkTarget] = []
    for member in risks:
        links.append(_build_link(typed, result, member, window_instance,
                                 member.public_r4_risk_identity))
    for member in gaps:
        links.append(_build_link(typed, result, member, window_instance,
                                 member.gap_opportunity_id))
    for member in changes:
        links.append(_build_link(
            typed, result, member, window_instance,
            "|".join((member.change_ledger_member_id,
                      member.current_window_instance_ref,
                      member.prior_window_instance_ref))))
    links.sort(key=lambda link: (link.member_ref, link.link_id))
    return tuple(links)


# ---------------------------------------------------------------------------
# Natural-Chinese three-sentence Query draft (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09QueryDraft:
    """The single center-level Query draft of a positive pattern unit.

    A draft only: never sent, never a task and never a workflow state
    (``draft_only`` is always True).  ``member_refs`` is the complete
    uncovered projectable member set in policy order -- never truncated.
    The three sentences are native Chinese without engineering ids; all
    definition/rule/window/mode ids live in the structured trace fields
    ``basis_refs`` and ``source_revision_refs`` (both hash-bound).
    """

    query_draft_id: str
    unit_stable_core: str
    query_owner: str
    basis_sentence: str
    finding_sentence: str
    action_sentence: str
    member_refs: Tuple[str, ...]
    member_count: int
    evidence_refs: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    scope_binding_id: str
    redundancy_decision: str
    max_query_member_fanout: int
    basis_refs: Tuple[str, ...]
    source_revision_refs: Tuple[str, ...]
    content_hash: str
    draft_only: bool = True


def _members_by_ref(typed: D09TypedInput) -> Dict[str, Any]:
    return {m.member_id: m for m in _all_members(typed)}


def _window_dates_zh(typed: D09TypedInput, window_instance_ref: str) -> str:
    """Human-readable computed dates of a typed window instance, resolved
    from the envelope; empty when the ref does not resolve."""
    for window in typed.analysis_windows:
        if window.window_instance_id == window_instance_ref:
            return f"{window.computed_window_start} 至 {window.computed_window_end}"
    return ""


def _record_entry_zh(member: Any, typed: D09TypedInput) -> str:
    """One finite natural record-list entry derived from exact typed member
    facts: subject id plus event date/risk category, gap category plus
    visit/time anchor, or trend current/prior window dates.  Never prints
    raw member refs, rule refs or engineering ids."""
    if member.member_kind == "subject_risk":
        category = _RISK_KIND_LABELS_ZH.get(member.risk_kind, "相关个体风险")
        event_part = f"{member.event_time_ref}，" if member.event_time_ref else ""
        return (f"受试者 {member.subject_stable_id}"
                f"（{event_part}{category}）")
    if member.member_kind == "gap_opportunity":
        category = _GAP_KIND_LABELS_ZH.get(member.gap_kind, "数据或流程缺口")
        anchor = (member.visit_or_time_anchor_refs[0]
                  if member.visit_or_time_anchor_refs else "")
        anchor_part = f"，{anchor}" if anchor else ""
        return f"受试者 {member.subject_stable_id}（{category}{anchor_part}）"
    current = _window_dates_zh(typed, member.current_window_instance_ref)
    prior = _window_dates_zh(typed, member.prior_window_instance_ref)
    current = current or "当前分析窗"
    prior = prior or "前一分析窗"
    return (f"受试者 {member.subject_stable_id}"
            f"（{current} 对比 {prior}）")


def _pd_fact_present(members: Sequence[Any]) -> bool:
    """Exact structured closed PD fact: a gap member whose typed
    ``gap_kind`` is exactly ``pd_unreported``.  No substring/prose/display-
    label/producer-domain inference and no invented risk-kind vocabulary."""
    return any(m.member_kind == "gap_opportunity"
               and m.gap_kind == "pd_unreported"
               for m in members)


def build_d09_query_draft(
    typed: D09TypedInput,
    result: D09RunResult,
) -> Optional[D09QueryDraft]:
    """Build the center-level Query draft.

    Returns ``None`` unless the evaluator granted exactly one Query
    (``query_count == 1``) for a positive unit.  The member list is the
    complete uncovered member set restricted to projectable members, ordered
    by the frozen member-order policy, never truncated.  Only locatable
    source evidence of the listed members is referenced.
    """
    _assert_authoritative_result(typed, result)
    if result.query_count != 1 or result.unit_count != 1:
        return None
    if result.disposition != "positive":
        return None
    decision = typed.query_redundancy_decision
    if decision.decision != "site_process_delta_present":
        return None
    _evaluation, projectable, _hidden = _resolve_visibility_members(
        typed, result)
    projectable_set = set(projectable)
    uncovered = [ref for ref in decision.uncovered_member_refs
                 if ref in projectable_set]
    if not uncovered:
        return None
    policy = typed.center_query_policy
    if policy.member_order_policy == "stable_member_ref_ascending":
        member_refs = tuple(sorted(uncovered))
    else:
        raise D09ProjectionError(
            f"unknown member_order_policy {policy.member_order_policy!r}")
    if len(member_refs) > decision.max_query_member_fanout:
        raise D09ProjectionError(
            "query member list exceeds the resolved fanout limit")
    by_ref = _members_by_ref(typed)
    visible = _visible_counts(typed, result)
    lexicon = typed.audience_lexicon
    definition = typed.pattern_definition
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    label_zh = lexicon.pattern_label_zh or definition.clinical_label_zh

    # Native-Chinese basis: clinical pattern label, current effective
    # project/protocol rule (no engineering ids), human-readable window.
    window_kind_zh = (_WINDOW_KIND_LABELS_ZH.get(window.window_kind, "分析窗")
                      if window else "分析窗")
    window_text = (f"{window.computed_window_start} 至 "
                   f"{window.computed_window_end}" if window else "本次")
    basis = (
        f"依据：{label_zh} 按本项目现行有效方案与监察规则，在{window_kind_zh}"
        f"（{window_text}）内需统一核实相关记录与判定；")

    parts: List[str] = []
    if visible[1]:
        parts.append(_fmt(lexicon.affected_subjects_zh
                          or _FROZEN_COUNT_ZH["affected_subjects_zh"],
                          visible[1]))
    if visible[2]:
        parts.append(_fmt(lexicon.event_count_zh
                          or _FROZEN_COUNT_ZH["event_count_zh"], visible[2]))
    if visible[3]:
        parts.append(f"缺口机会 {visible[3]} 项")
    count_text = "、".join(parts) if parts else "0"
    unit_zh = _UNIT_LABELS_ZH.get(DENOMINATOR_UNITS.get(
        result.denominator_kind, ""), "")
    denom_label = _DENOMINATOR_LABELS_ZH.get(result.denominator_kind,
                                             result.denominator_kind)
    denom_text = (
        " ".join(part for part in
                 (denom_label, str(result.denominator_value), unit_zh)
                 if part)
        if result.denominator_value > 0 or unit_zh else "—")
    coverage_state = _coverage_state(typed, result)
    coverage_state_zh = _COVERAGE_STATE_ZH.get(coverage_state, coverage_state)
    coverage_zh = lexicon.coverage_zh or _FROZEN_COUNT_ZH["coverage_zh"]
    record_text = "；".join(_record_entry_zh(by_ref[ref], typed)
                            for ref in member_refs)
    finding = (
        f"发现：本中心共 {count_text}，分母为{denom_text}，{coverage_zh}："
        f"{coverage_state_zh}；涉及记录（{len(member_refs)} 条）："
        f"{record_text}；")

    action = (
        f"行动项：请核实上述 {len(member_refs)} 条记录的具体字段与判定，"
        "并补充或更正对应记录；")
    # Two-part PD gate: the policy must allow verify_pd AND at least one
    # projectable uncovered member must carry the exact structured closed
    # PD fact (gap_kind == "pd_unreported").
    if ("verify_pd" in policy.allowed_action_kinds
            and _pd_fact_present([by_ref[ref] for ref in member_refs])):
        action += "请核实是否为 PD。"

    # Evidence completeness: every listed member must contribute a locatable
    # source locator; the evidence set is the full deterministic set and is
    # never silently partial or empty.
    evidence_refs: List[str] = []
    for ref in member_refs:
        member = by_ref.get(ref)
        if member is None:
            raise D09ProjectionError(
                f"uncovered member ref {ref!r} has no typed member object")
        locator = _member_locator(member)
        if locator is None:
            raise D09ProjectionError(
                f"query member {ref!r} has no locatable source locator")
        if locator not in evidence_refs:
            evidence_refs.append(locator)
    evidence_refs.sort()
    if not evidence_refs:
        raise D09ProjectionError(
            "query draft requires a non-empty locatable evidence set")
    scope_binding_id = typed.scope_binding.scope_binding_id
    unit_stable_core = d09_unit_stable_core(typed)
    basis_refs = (
        definition.pattern_definition_id,
        definition.positive_rule_ref,
        window.analysis_window_stable_id if window else "",
        typed.mode_contract_version,
    )
    # Revision refs are a semantic set in the frozen contract.  Canonicalize
    # their presentation/hash order so an equivalent input permutation cannot
    # change the draft identity.
    source_revision_refs = tuple(sorted(typed.source_revision_set))
    query_draft_id = d09_content_hash({
        "unit_stable_core": unit_stable_core,
        "member_refs": list(member_refs),
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "scope_binding_id": scope_binding_id,
        "basis_refs": list(basis_refs),
        "source_revision_refs": list(source_revision_refs),
    })
    draft_core = {
        "query_draft_id": query_draft_id,
        "unit_stable_core": unit_stable_core,
        "query_owner": "D09",
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "member_refs": list(member_refs),
        "evidence_refs": evidence_refs,
        "source_locator_ids": evidence_refs,
        "scope_binding_id": scope_binding_id,
        "redundancy_decision": decision.decision,
        "max_query_member_fanout": decision.max_query_member_fanout,
        "basis_refs": list(basis_refs),
        "source_revision_refs": list(source_revision_refs),
    }
    _assert_clean_zh(basis, finding, action)
    _assert_no_structured_ref_in_text(typed, basis, finding, action)
    return D09QueryDraft(
        query_draft_id=query_draft_id,
        unit_stable_core=unit_stable_core,
        query_owner="D09",
        basis_sentence=basis,
        finding_sentence=finding,
        action_sentence=action,
        member_refs=member_refs,
        member_count=len(member_refs),
        evidence_refs=tuple(evidence_refs),
        source_locator_ids=tuple(evidence_refs),
        scope_binding_id=scope_binding_id,
        redundancy_decision=decision.decision,
        max_query_member_fanout=decision.max_query_member_fanout,
        basis_refs=basis_refs,
        source_revision_refs=source_revision_refs,
        content_hash=d09_content_hash(draft_core),
    )


def validate_query_draft(
    draft: D09QueryDraft,
    typed: D09TypedInput,
    result: D09RunResult,
) -> Dict[str, Any]:
    """Closed audience validation of a D09 Query draft (contract section 12).

    Checks the exact three sentence patterns, absence of forbidden internal
    tokens, the complete (never truncated) uncovered projectable member set,
    projectable/locatable-only evidence, the frozen PD wording rule, and the
    content hash.
    """
    reasons: List[str] = []
    try:
        _assert_authoritative_result(typed, result)
    except D09ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    sentences = (draft.basis_sentence, draft.finding_sentence,
                 draft.action_sentence)
    if not all(isinstance(s, str) and bool(s) for s in sentences):
        reasons.append("three_sentence_contract")
    for prefix in ("依据：", "发现：", "行动项："):
        if not any(s.startswith(prefix) for s in sentences):
            reasons.append(f"required_sentence_pattern_missing:{prefix}")
    try:
        _assert_clean_zh(*sentences)
        _assert_no_structured_ref_in_text(typed, *sentences)
    except D09ProjectionError as error:
        reasons.append(str(error))
    _evaluation, projectable, hidden = _resolve_visibility_members(
        typed, result)
    projectable_set = set(projectable)
    projectable_uncovered = sorted(
        ref for ref in typed.query_redundancy_decision.uncovered_member_refs
        if ref in projectable_set)
    if list(draft.member_refs) != projectable_uncovered:
        reasons.append("member_set_not_complete_uncovered_projectable")
    if set(hidden) & set(draft.member_refs):
        reasons.append("hidden_member_in_query")
    if draft.member_count != len(draft.member_refs):
        reasons.append("member_count_mismatch")
    if draft.member_count > typed.center_query_policy.max_query_member_fanout:
        reasons.append("fanout_exceeded")
    by_ref = _members_by_ref(typed)
    locatable_evidence: List[str] = []
    for ref in draft.member_refs:
        member = by_ref.get(ref)
        if member is None:
            reasons.append(f"unresolved_member_ref:{ref}")
            continue
        locator = _member_locator(member)
        if locator is None:
            reasons.append(f"member_not_locatable:{ref}")
        elif locator not in locatable_evidence:
            locatable_evidence.append(locator)
    locatable_evidence.sort()
    if not draft.evidence_refs:
        reasons.append("evidence_must_be_non_empty")
    # the evidence set must equal the full deterministic locator set of the
    # complete member list; removing any locator is rejected
    if list(draft.evidence_refs) != locatable_evidence:
        reasons.append("evidence_not_locatable_projectable")
    if draft.source_locator_ids != draft.evidence_refs:
        reasons.append("source_locator_ids_mismatch")
    # Independent two-part PD gate: policy allows verify_pd AND the draft's
    # complete member list carries an exact structured closed PD fact.
    draft_members = [by_ref[ref] for ref in draft.member_refs
                     if ref in by_ref]
    pd_expected = ("verify_pd" in typed.center_query_policy.allowed_action_kinds
                   and _pd_fact_present(draft_members))
    pd_present = "请核实是否为 PD" in draft.action_sentence
    if pd_expected != pd_present:
        reasons.append("pd_wording_rule_mismatch")
    if not draft.draft_only:
        reasons.append("query_must_be_draft_only")
    if draft.query_owner != "D09":
        reasons.append("query_owner_not_d09")
    if draft.redundancy_decision != "site_process_delta_present":
        reasons.append("redundancy_decision_mismatch")
    if draft.max_query_member_fanout != typed.query_redundancy_decision.max_query_member_fanout:
        reasons.append("fanout_policy_mismatch")
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    expected_basis_refs = (
        typed.pattern_definition.pattern_definition_id,
        typed.pattern_definition.positive_rule_ref,
        window.analysis_window_stable_id if window else "",
        typed.mode_contract_version,
    )
    if draft.basis_refs != expected_basis_refs:
        reasons.append("basis_refs_mismatch")
    if draft.source_revision_refs != tuple(sorted(typed.source_revision_set)):
        reasons.append("source_revision_refs_mismatch")
    expected_hash = d09_content_hash({
        "query_draft_id": draft.query_draft_id,
        "unit_stable_core": draft.unit_stable_core,
        "query_owner": draft.query_owner,
        "basis_sentence": draft.basis_sentence,
        "finding_sentence": draft.finding_sentence,
        "action_sentence": draft.action_sentence,
        "member_refs": list(draft.member_refs),
        "evidence_refs": list(draft.evidence_refs),
        "source_locator_ids": list(draft.source_locator_ids),
        "scope_binding_id": draft.scope_binding_id,
        "redundancy_decision": draft.redundancy_decision,
        "max_query_member_fanout": draft.max_query_member_fanout,
        "basis_refs": list(draft.basis_refs),
        "source_revision_refs": list(draft.source_revision_refs),
    })
    if draft.content_hash != expected_hash:
        reasons.append("content_hash_stale")
    try:
        expected_draft = build_d09_query_draft(typed, result)
    except D09ProjectionError as error:
        reasons.append(f"authoritative_query_unavailable:{error}")
        expected_draft = None
    if expected_draft is None or draft != expected_draft:
        reasons.append("query_draft_not_exact_authoritative_projection")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Replay-stable R2 lifecycle handoff (contract section 10)
# ---------------------------------------------------------------------------


def d09_evaluation_content_identity(typed: D09TypedInput) -> str:
    """Evaluation-content identity (contract section 5.1): stable core plus
    the actual window instance, sorted source revisions/content hashes and
    all decisive authority/method hashes.  Opaque run/snapshot ids never
    enter it, so identical immutable content replays to the same identity
    and the same R2 idempotency key."""
    definition = typed.pattern_definition
    authority = typed.resolved_authority_decision
    method = typed.method_comparability_decision
    policy = typed.center_query_policy
    redundancy = typed.query_redundancy_decision
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    window_identity = d09_content_hash({
        "analysis_window_stable_id": window.analysis_window_stable_id
        if window else "",
        "computed_window_start": window.computed_window_start if window else "",
        "computed_window_end": window.computed_window_end if window else "",
        "cutoff_id": window.cutoff_id if window else "",
        "scope_binding_stable_id": window.scope_binding_stable_id
        if window else "",
    })
    return d09_content_hash({
        "unit_stable_core": d09_unit_stable_core(typed),
        "window_instance_identity": window_identity,
        "source_revision_set": sorted(typed.source_revision_set),
        "source_content_hashes": sorted(typed.source_content_hashes),
        "mode_contract_version": typed.mode_contract_version,
        "pattern_definition_content_hash": (
            definition.pattern_definition_content_hash),
        "window_definition_content_hash": (
            window.window_contract_content_hash if window else ""),
        "stratum_contract_content_hash": (
            typed.stratum.stratum_contract_content_hash),
        "legal_definition_matrix_content_hash": (
            definition.legal_definition_matrix_content_hash),
        "numeric_execution_policy_content_hash": (
            definition.numeric_execution_policy_content_hash),
        "resolved_authority": {
            "minimum_member_subject_count": authority.minimum_member_subject_count,
            "gap_positive_minimum_opportunity_count": (
                authority.gap_positive_minimum_opportunity_count),
            "trend_positive_minimum_subject_count": (
                authority.trend_positive_minimum_subject_count),
            "authority_validity_state": authority.authority_validity_state,
            "authority_ref": authority.authority_ref,
            "authority_locator_ref": authority.authority_locator_ref,
            "mode_contract_version": authority.mode_contract_version,
            "authority_content_hash": authority.authority_content_hash,
        },
        "method_comparability": {
            "method_validity_state": method.method_validity_state,
            "statistical_signal_role": method.statistical_signal_role,
            "member_expansion_state": method.member_expansion_state,
            "window_rule_version_refs": list(method.window_rule_version_refs),
            "stratum_method_version_refs": list(
                method.stratum_method_version_refs),
        },
        "center_query_policy": {
            "policy_id": policy.policy_id,
            "mode_contract_version": policy.mode_contract_version,
            "max_query_member_fanout": policy.max_query_member_fanout,
            "member_order_policy": policy.member_order_policy,
            "redundancy_rule_ref": policy.redundancy_rule_ref,
            "allowed_action_kinds": sorted(policy.allowed_action_kinds),
            "pd_wording_rule_ref": policy.pd_wording_rule_ref,
            "content_hash": policy.content_hash,
            "effective_interval": policy.effective_interval,
        },
        "query_redundancy_decision": {
            "decision": redundancy.decision,
            "max_query_member_fanout": redundancy.max_query_member_fanout,
            "unit_member_set_hash": redundancy.unit_member_set_hash,
            "covered_member_refs": sorted(redundancy.covered_member_refs),
            "uncovered_member_refs": sorted(redundancy.uncovered_member_refs),
            "member_query_refs": sorted(redundancy.member_query_refs),
            "coverage_proof_hash": redundancy.coverage_proof_hash,
        },
        "algorithm_version": _ALGORITHM_VERSION,
    })


@dataclass(frozen=True)
class D09R2RiskHandoff:
    """Replay-stable R2 lifecycle handoff (contract section 10).

    ``handoff_id`` and ``idempotency_key`` are equal and derive from the
    public D09 risk identity, the evaluation-content identity, the action,
    the prior instance ref and the prior public-identity ref -- never from
    opaque run/snapshot ids.  ``create`` is the only action that allows
    ``prior_risk_instance_ref is None``; every non-create action requires
    BOTH the prior instance ref and the prior public risk identity ref and
    fails closed when either is missing.  The handoff never proposes
    closure: broken coverage/not-evaluable carries forward and rule/method
    change supersedes.

    The projection only binds the typed prior refs; resolving them to the
    actual R2 instance and verifying that its public identity equals
    ``prior_public_risk_identity_ref`` is an R2 application gate, not a D09
    side effect.
    """

    handoff_id: str
    idempotency_key: str
    public_d09_risk_identity: Dict[str, Any]
    stable_core_ref: str
    current_evaluation_content_ref: str
    run_snapshot_audit_refs: Tuple[str, ...]
    prior_risk_instance_ref: Optional[str]
    prior_public_risk_identity_ref: Optional[str]
    action: str
    lineage_relation: str
    pattern_definition_hash: str
    mode_contract_version: str
    member_refs: Tuple[str, ...]
    measure_ledger_ref: str
    completeness_decision_ref: str
    monitoring_priority: Optional[str]
    no_auto_close_reasons: Tuple[str, ...]


def _measure_ledger_ref(typed: D09TypedInput, result: D09RunResult) -> str:
    return d09_content_hash({
        "denominator_kind": result.denominator_kind,
        "denominator_value": result.denominator_value,
        "denominator_state": result.denominator_state,
        "opportunity_expected": result.opportunity_expected,
        "opportunity_observed": result.opportunity_observed,
        "individual_risk_count": result.individual_risk_count,
        "affected_subject_count": result.affected_subject_count,
        "event_count": result.event_count,
        "gap_opportunity_count": result.gap_opportunity_count,
    })


def _completeness_decision_ref(typed: D09TypedInput,
                               result: D09RunResult) -> str:
    return d09_content_hash({
        "disposition": result.disposition,
        "primary_reason": result.primary_reason,
        "coverage_state": _coverage_state(typed, result),
    })


def _no_auto_close_reasons(typed: D09TypedInput,
                           result: D09RunResult) -> Tuple[str, ...]:
    reasons: List[str] = []
    members = _all_members(typed)
    if any(getattr(m, "monitoring_priority", None) == "high"
           for m in members):
        reasons.append("存在高监察优先级成员")
    if typed.lineage_context.carry_forward_state == "active":
        reasons.append("本次可评价范围不完整，需维持进行中")
    return tuple(reasons)


def _max_member_priority(typed: D09TypedInput) -> Optional[str]:
    priorities = [m.monitoring_priority for m in _all_members(typed)
                  if getattr(m, "monitoring_priority", None)]
    if "high" in priorities:
        return "high"
    if "medium" in priorities:
        return "medium"
    return None


def build_d09_r2_handoff(
    typed: D09TypedInput,
    result: D09RunResult,
) -> Optional[D09R2RiskHandoff]:
    """Build the R2 lifecycle handoff for the run.

    Action derivation (contract section 10, typed facts only):

    * no prior ref + positive -> ``create`` (lineage none/first_seen);
    * prior ref + superseded lineage -> ``supersede``;
    * prior ref + positive or carry-forward active -> ``continue``
      (lineage none/continued_from_data_revision/continued_from_cutoff_advance);
    * everything else emits no handoff.

    R2 action boundary: the contract's full R2 action vocabulary
    (create/continue/update/propose_close/reopen/supersede) is a downstream
    R2 lifecycle surface; this D09 projection may initiate only
    create/continue/supersede from current typed facts and never invents
    update/propose_close/reopen.

    Contradictory typed facts (e.g. create with a prior ref, carry-forward
    without a prior ref, continue/supersede without a prior ref or without
    the prior public risk identity ref) fail closed.  Resolving the prior
    refs to the actual R2 instance is an R2 application gate; no actual R2
    lifecycle change is performed here.
    """
    _assert_authoritative_result(typed, result)
    if result.unit_count != 1:
        return None
    lineage = typed.lineage_context
    prior = lineage.prior_risk_instance_ref
    prior_public = lineage.prior_public_risk_identity_ref
    disposition = result.disposition
    carry = lineage.carry_forward_state == "active"
    superseded = lineage.lineage_relation == (
        "superseded_by_rule_or_method_change")
    if prior is None:
        if carry:
            raise D09ProjectionError(
                "carry-forward without a prior risk instance ref")
        if disposition != "positive":
            return None
        if lineage.lineage_relation not in ("none", "first_seen"):
            raise D09ProjectionError(
                f"create action with lineage {lineage.lineage_relation!r}")
        if prior_public is not None:
            raise D09ProjectionError(
                "create action with a prior public risk identity ref")
        action = "create"
    else:
        if prior_public is None:
            raise D09ProjectionError(
                "non-create handoff requires prior_public_risk_identity_ref")
        if superseded:
            action = "supersede"
        elif disposition == "positive" or carry:
            if lineage.lineage_relation not in (
                    "none", "continued_from_data_revision",
                    "continued_from_cutoff_advance"):
                raise D09ProjectionError(
                    f"continue action with lineage "
                    f"{lineage.lineage_relation!r}")
            action = "continue"
        else:
            return None
    public_identity = d09_public_risk_identity(typed)
    evaluation_content = d09_evaluation_content_identity(typed)
    member_refs = tuple(sorted(m.member_id for m in _all_members(typed)))
    measure_ledger_ref = _measure_ledger_ref(typed, result)
    completeness_decision_ref = _completeness_decision_ref(typed, result)
    no_auto_close = _no_auto_close_reasons(typed, result)
    monitoring_priority = _max_member_priority(typed)
    handoff_id = d09_content_hash({
        "public_d09_risk_identity": public_identity,
        "evaluation_content_identity": evaluation_content,
        "action": action,
        "prior_risk_instance_ref": prior,
        "prior_public_risk_identity_ref": prior_public,
    })
    return D09R2RiskHandoff(
        handoff_id=handoff_id,
        idempotency_key=handoff_id,
        public_d09_risk_identity=public_identity,
        stable_core_ref=result.units[0].stable_core,
        current_evaluation_content_ref=evaluation_content,
        run_snapshot_audit_refs=(typed.run_ref, typed.snapshot_ref),
        prior_risk_instance_ref=prior,
        prior_public_risk_identity_ref=prior_public,
        action=action,
        lineage_relation=lineage.lineage_relation,
        pattern_definition_hash=(
            typed.pattern_definition.pattern_definition_content_hash),
        mode_contract_version=typed.mode_contract_version,
        member_refs=member_refs,
        measure_ledger_ref=measure_ledger_ref,
        completeness_decision_ref=completeness_decision_ref,
        monitoring_priority=monitoring_priority,
        no_auto_close_reasons=no_auto_close,
    )


def validate_d09_r2_handoff(
    handoff: D09R2RiskHandoff,
    typed: D09TypedInput,
    result: D09RunResult,
) -> Dict[str, Any]:
    """Closed validation of a D09 R2 handoff (contract section 10)."""
    reasons: List[str] = []
    try:
        _assert_authoritative_result(typed, result)
    except D09ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    expected_handoff_id = d09_content_hash({
        "public_d09_risk_identity": d09_public_risk_identity(typed),
        "evaluation_content_identity": d09_evaluation_content_identity(typed),
        "action": handoff.action,
        "prior_risk_instance_ref": (
            typed.lineage_context.prior_risk_instance_ref),
        "prior_public_risk_identity_ref": (
            typed.lineage_context.prior_public_risk_identity_ref),
    })
    if handoff.handoff_id != expected_handoff_id:
        reasons.append("handoff_id_stale")
    if handoff.idempotency_key != handoff.handoff_id:
        reasons.append("idempotency_key_mismatch")
    if handoff.action not in ("create", "continue", "supersede"):
        reasons.append(f"action_not_d09_initiated:{handoff.action}")
    if handoff.action == "create" and handoff.prior_risk_instance_ref is not None:
        reasons.append("create_with_prior_ref")
    if handoff.action == "create" and (
            handoff.prior_public_risk_identity_ref is not None):
        reasons.append("create_with_prior_public_ref")
    if handoff.action in ("continue", "supersede") and (
            handoff.prior_risk_instance_ref is None):
        reasons.append("non_create_without_prior_ref")
    if handoff.action in ("continue", "supersede") and (
            handoff.prior_public_risk_identity_ref is None):
        reasons.append("non_create_without_prior_public_ref")
    if handoff.action == "create" and result.disposition != "positive":
        reasons.append("create_without_positive")
    if handoff.action == "continue":
        carry = typed.lineage_context.carry_forward_state == "active"
        if result.disposition != "positive" and not carry:
            reasons.append("continue_without_positive_or_carry_forward")
    if handoff.action == "supersede" and typed.lineage_context.lineage_relation != (
            "superseded_by_rule_or_method_change"):
        reasons.append("supersede_without_rule_or_method_change")
    if handoff.current_evaluation_content_ref != d09_evaluation_content_identity(typed):
        reasons.append("evaluation_content_identity_stale")
    if handoff.public_d09_risk_identity != d09_public_risk_identity(typed):
        reasons.append("public_risk_identity_stale")
    if handoff.pattern_definition_hash != (
            typed.pattern_definition.pattern_definition_content_hash):
        reasons.append("pattern_definition_hash_stale")
    if handoff.stable_core_ref != result.units[0].stable_core:
        reasons.append("stable_core_stale")
    if handoff.mode_contract_version != typed.mode_contract_version:
        reasons.append("mode_contract_version_stale")
    if handoff.prior_risk_instance_ref != (
            typed.lineage_context.prior_risk_instance_ref):
        reasons.append("prior_ref_mismatch")
    if handoff.prior_public_risk_identity_ref != (
            typed.lineage_context.prior_public_risk_identity_ref):
        reasons.append("prior_public_ref_mismatch")
    if handoff.lineage_relation != typed.lineage_context.lineage_relation:
        reasons.append("lineage_relation_mismatch")
    if handoff.run_snapshot_audit_refs != (typed.run_ref, typed.snapshot_ref):
        reasons.append("run_snapshot_audit_refs_mismatch")
    # every identity-bearing field is bound: member refs, measure and
    # completeness refs, monitoring priority and no-auto-close reasons
    expected_member_refs = tuple(
        sorted(m.member_id for m in _all_members(typed)))
    if handoff.member_refs != expected_member_refs:
        reasons.append("member_refs_mismatch")
    if handoff.measure_ledger_ref != _measure_ledger_ref(typed, result):
        reasons.append("measure_ledger_ref_mismatch")
    if handoff.completeness_decision_ref != _completeness_decision_ref(
            typed, result):
        reasons.append("completeness_decision_ref_mismatch")
    if handoff.monitoring_priority != _max_member_priority(typed):
        reasons.append("monitoring_priority_mismatch")
    if handoff.no_auto_close_reasons != _no_auto_close_reasons(typed, result):
        reasons.append("no_auto_close_reasons_mismatch")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09ProjectionBundle:
    """Complete renderer-neutral projection of one run."""

    audience: D09AudienceProjection
    counts: D09ProjectionCountSurface
    risk_marker: Optional[D09RiskMarker]
    hotspots: Tuple[D09HotspotProjection, ...]
    deep_links: Tuple[D09DeepLinkTarget, ...]
    query_draft: Optional[D09QueryDraft]
    r2_handoff: Optional[D09R2RiskHandoff]


def project_d09_run(
    typed: D09TypedInput,
    result: D09RunResult,
) -> D09ProjectionBundle:
    """Project a validated typed run onto all renderer-neutral surfaces."""
    return D09ProjectionBundle(
        audience=build_d09_audience_projection(typed, result),
        counts=build_d09_count_surface(typed, result),
        risk_marker=build_d09_risk_marker(typed, result),
        hotspots=build_d09_hotspots(typed, result),
        deep_links=build_d09_deep_links(typed, result),
        query_draft=build_d09_query_draft(typed, result),
        r2_handoff=build_d09_r2_handoff(typed, result),
    )
