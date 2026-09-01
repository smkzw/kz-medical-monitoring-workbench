"""R4-D10 renderer-neutral projection layer (worker_02).

Consumes only an accepted ``D10TypedInput`` bundle and the deterministic
evaluator's authoritative ``D10RunResult`` and produces immutable,
renderer-neutral projection objects:

* :func:`build_d10_audience_projection` -- audience visibility: projectable
  vs evaluation member/site planes, hidden counts, payload presence, rate
  projection state, coverage and the frozen coverage phrase
  ``本次可评价范围/数据完整性``; every audience surface consumes the single
  resolved partition, so hidden members/sites never leak through rows,
  counts, ordering, rates, Query evidence, hotspot details, locators,
  tooltips or links;
* :func:`build_d10_count_surface` -- the separated count surface
  (``individual_risk_count`` / ``affected_subject_count`` /
  ``event_or_outcome_count`` / ``center_pattern_count`` /
  ``affected_site_count`` / ``project_signal_count`` / ``clue_count`` /
  ``query_count``) with frozen Chinese forms; the planes are never summed;
* :func:`build_d10_projection_version` / :func:`build_d10_project_projection`
  -- the versioned project projection (change section, center distribution,
  time/safety/efficacy trend surface, warnings, risk/clue markers, hotspot
  preservation, deep links, Query and R2 handoff refs) bound to the frozen
  audience contract;
* :func:`build_d10_risk_marker` -- the project-signal RiskInstance marker
  (``owner=D10``, ``aggregation_level=project_signal``) with the stable
  public identity of contract section 10; created only for positive units;
* :func:`build_d10_hotspots` -- hotspot subject rows; projections only;
  the typed high-risk hotspot members (including the single high-risk
  subject) are preserved on positive runs and never hidden behind a low
  project proportion or a small-sample note; rows are ordered by subject
  stable identity, never by a punitive risk ranking or black-box score;
* :func:`build_d10_deep_links` -- verified one-hop deep-link targets of the
  three closed kinds (member / site / subject_site_pair) with exact
  eligible-set, subject-site and return-state binding and an explicit
  unavailable state (``来源暂无法定位``) with no fabricated jump; no UI
  implementation, only the navigation contract;
* :func:`build_d10_query_draft` / :func:`validate_d10_query_draft` -- at
  most one natural-Chinese three-sentence Query draft per positive unit
  (``依据`` / ``发现`` / ``行动项``) over the complete uncovered projectable
  member set, the exact union/disjoint redundancy proof, draft-only status
  and the frozen Verify-PD template (``请核实是否为 PD``) exactly when the
  typed PD wording state is ``verify_whether_pd``; no task/submit/reply/
  close workflow;
* :func:`d10_public_risk_identity` / :func:`build_d10_r2_handoff` /
  :func:`validate_d10_r2_handoff` -- the
  replay-stable R2 lifecycle handoff contract (contract section 10) for
  positive units only: action x lineage/prior/carry-forward/idempotency
  constraints over the full closed action vocabulary
  (create/continue/update/propose_close/reopen/supersede), public identity,
  change/completeness hashes and no-auto-close reasons; R2 objects are
  emitted, never created or updated.

Boundaries honoured (contract sections 1/10/11/12/13/14, worker_02
contract):

* the projection is renderer-neutral: it never re-evaluates the medical
  disposition, never recomputes the numerator/denominator ledger, never
  reads artifact/oracle/registry/quota/generator/verifier/test files and
  never branches on case/fixture/test identifiers, mutation metadata,
  ``SYN-*`` strings or synthetic prefixes;
* the authoritative binding check binds the supplied result to the supplied
  typed bundle on the deterministic identity axes (stable core, signal
  kind); the projection never re-runs the evaluator;
* global/control-plane/routing/handoff gates and admitted not-evaluable
  units emit no risk marker, Query draft, hotspot rows, deep links or R2
  handoff; a boundary may preserve visible hotspot/center context but never
  becomes a project signal or Query;
* the audience plane never exposes hidden members/sites through counts,
  rates, labels, tooltips, Query or links; suppressed/qualified rate states
  never show a misleading precision rate; deep links are bound to the exact
  deep-link-eligible member/site/subject-site sets;
* the audience surface is native Chinese and never exposes internal
  disposition/state/enum/hash/id/ref/policy/mode/window/revision/scope
  tokens, ``正式事实`` / ``候选信号`` / ``只读`` or other backend labels;
  engineering references exist only in non-audience typed fields;
* Query is a draft only (``draft_only=True``): never sent, never a task and
  never a workflow state; the R2 handoff is a contract emission only --
  no R2 lifecycle object is created or updated here.

All data is synthetic and offline.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..risks.d10_contracts import (
    D10_DOMAIN_ID,
    D10TypedInput,
    D10_UNIT_ALGORITHM_VERSION,
    d10_content_hash,
    d10_normalize_nfc,
    d10_unit_stable_core,
)
from ..risks.d10_evaluator import D10RunResult

# ---------------------------------------------------------------------------
# Frozen Chinese forms (contract sections 10/11/12/14) and closed display
# vocabularies
# ---------------------------------------------------------------------------

_FROZEN_DISPOSITION_ZH = {
    "positive": "发现值得优先复核的项目信号",
    "negative": "在本次可评价范围内未发现该类项目信号（不代表无个体风险）",
    "boundary": "边界情况",
    "not_applicable": "不适用",
    "not_evaluable": "暂无法评价（附原因）",
    "global_gate": "本次未生成医学评价（项目级准入未通过）",
    "comparison_set_gate": "本次未生成医学评价（跨中心可比性尚未闭合）",
    "window_pair_gate": "本次未生成医学评价（可比分析窗不足）",
    "routing_gate": "本次未生成医学评价（归属路由未成立）",
    "handoff_gate": "本次未生成医学评价（仅外部处置边界）",
    "integrity_gate": "本次未生成医学评价（数据自洽性校验未通过）",
}

_FROZEN_COUNT_ZH = {
    "individual_risk_count_zh": "相关个体风险 {n} 条",
    "affected_subjects_zh": "受影响受试者 {n} 名",
    "event_or_outcome_count_zh": "事件或结局 {n} 起",
    "center_pattern_count_zh": "中心模式 {n} 项",
    "affected_site_count_zh": "受影响中心 {n} 个",
    "project_signal_count_zh": "项目信号 {n} 项",
    "clue_count_zh": "线索 {n} 项",
    "query_count_zh": "查询草稿 {n} 条",
    "coverage_zh": "本次可评价范围/数据完整性",
}

_DENOMINATOR_LABELS_ZH = {
    "enrolled_subjects": "入组受试者",
    "treated_subjects": "接受治疗受试者",
    "safety_evaluable_subjects": "安全性可评价受试者",
    "efficacy_evaluable_subjects": "疗效可评价受试者",
    "subject_time": "受试者时间",
    "exposure_time": "暴露时间",
    "expected_assessment_opportunities": "预期评估机会",
    "analysis_population_members": "分析人群成员",
}

_UNIT_LABELS_ZH = {
    "subject": "名", "day": "天", "subject_day": "人日", "opportunity": "次",
}

_DEN_UNIT_BY_KIND = {
    "enrolled_subjects": "subject",
    "treated_subjects": "subject",
    "safety_evaluable_subjects": "subject",
    "efficacy_evaluable_subjects": "subject",
    "subject_time": "subject_day",
    "exposure_time": "subject_day",
    "expected_assessment_opportunities": "opportunity",
    "analysis_population_members": "subject",
}

_COVERAGE_STATE_ZH = {
    "complete": "完整",
    "partial": "部分",
    "missing": "缺失",
    "not_evaluable": "暂无法评价",
}

_WINDOW_KIND_LABELS_ZH = {
    "calendar_interval": "日历区间",
    "study_day_interval": "研究日区间",
    "exposure_interval": "暴露区间",
}

_SIGNAL_KIND_LABELS_ZH = {
    "project_risk_distribution": "项目风险分布",
    "cross_site_pattern": "跨中心模式",
    "project_time_trend": "项目时间趋势",
    "project_safety_trend": "项目安全性趋势",
    "project_efficacy_trend": "项目疗效趋势",
}

_CHANGE_KIND_ZH = {
    "initial_current": "初始全量",
    "new": "新增",
    "continued": "持续",
    "upgraded": "升级",
    "downgraded": "降级",
    "resolved": "关闭",
    "reopened": "重开",
    "not_comparable": "不可直接比较",
}

_CHANGE_CAUSE_ZH = {
    "data": "数据变化",
    "denominator": "分母口径变化",
    "coverage": "覆盖变化",
    "knowledge": "知识库变化",
    "rule": "规则变化",
    "mapping": "映射变化",
    "model": "模型变化",
    "method": "方法变化",
    "population": "分析人群变化",
    "visibility": "可见性变化",
    "mode": "模式变化",
    "mixed": "多种原因",
}

_LINEAGE_ZH = {
    "initial_full_snapshot": "初始全量快照",
    "continued_from_data_revision": "随数据修订延续",
    "continued_from_cutoff_advance": "随数据截止推进延续",
    "superseded_by_knowledge_change": "因知识库变化取代",
    "superseded_by_rule_or_mapping_change": "因规则或映射变化取代",
    "superseded_by_method_or_population_change": "因方法或分析人群变化取代",
    "superseded_by_mode_change": "因模式变化取代",
    "superseded_by_visibility_change": "因可见性变化取代",
    "coverage_regressed": "覆盖回退",
    "not_comparable": "不可比较",
}

_ESTIMATE_KIND_ZH = {
    "count": "计数",
    "proportion": "比例",
    "incidence_rate": "发生率",
    "exposure_adjusted_rate": "暴露调整率",
    "summary_statistic": "汇总统计量",
    "responder_rate": "应答率",
    "model_estimate": "模型估计值",
}

_RATE_STATE_ZH = {
    "permitted": "比例可展示",
    "suppressed": "因可见性限制暂不展示比例",
    "qualified": "比例需限定口径后展示",
}

# Closed warning vocabulary keyed by typed facts (never a quality verdict).
_CODED_WARNING_ZH = {
    "site_small": (
        "个别中心样本量小，相关比例需谨慎比较，且不得据此对中心排序"),
    "site_small_outlier": (
        "个别中心样本量小且偏离明显，相关比例需谨慎比较，且不得据此"
        "对中心排序"),
    "site_late_start": (
        "个别中心启动晚，随访覆盖受限，相关比例需谨慎比较"),
    "site_late_start_outlier": (
        "个别中心启动晚且偏离明显，相关比例需谨慎比较，且不得据此"
        "对中心排序"),
    "case_mix_mismatch": "中心间病例构成存在差异，可比性受限",
    "case_mix_missing": "中心间病例构成信息缺失，可比性受限",
    "followup_shortfall": "部分中心随访不足，相关趋势需谨慎解读",
    "exposure_shortfall": "部分中心暴露不足，相关比例需谨慎解读",
    "heterogeneous_sites": "中心间存在异质性，分布需分中心复核",
    "method_validity_insufficient": "方法前提未充分满足，相关估计需谨慎解读",
    "site_evidence_incomplete": "个别中心证据不完整，相关计数需谨慎解读",
    "site_quality_judgment": (
        "涉及中心质量判定边界，仅提示复核，不作质量结论"),
}

_STIGMA_CODES = frozenset((
    "site_late_start_outlier", "site_small", "site_small_outlier",
))

# Forbidden internal labels and raw enum/status/backend tokens in any
# user-facing Chinese string (contract sections 12/14, worker_02 contract).
_FORBIDDEN_INTERNAL_TERMS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
    "正式安全性信号", "确证治疗效果", "优效", "非劣", "获益-风险裁决",
    "中心质量差", "中心质量好", "typed handoff", "candidate",
)

_FORBIDDEN_RAW_TOKENS = (
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "permitted", "suppressed", "qualified",
    "create", "continue", "update", "propose_close", "reopen", "supersede",
    "gate", "ledger", "handoff", "envelope", "payload", "evaluator",
    "projection", "hotspot", "deep_link", "signal_count", "clue_count",
    "center_pattern", "project_signal", "audience", "draft", "revision",
    "lineage", "stratum", "estimate_kind",
)

UNAVAILABLE_SOURCE_ZH = "来源暂无法定位"

_PRIORITY_RANK = {"high": 0, "medium": 1}

_ALGORITHM_VERSION = D10_UNIT_ALGORITHM_VERSION
_PUBLIC_IDENTITY_VERSION = "d10_public_v1"

_STRUCTURED_REF_KEY_RE = re.compile(
    r"(?i)(?:pattern(?:_definition)?_(?:id|ref)|"
    r"rule_(?:id|ref)|mode_contract_(?:version|id|ref)|"
    r"window(?:_instance|_definition)?_(?:id|ref)|"
    r"(?:source_)?revision(?:_(?:id|ref))?|"
    r"scope_binding_(?:id|ref)|policy_(?:id|ref)|"
    r"signal(?:_definition)?_(?:id|ref)|stratum_(?:id|ref)|"
    r"comparison_reference_(?:id|ref))\s*[:=：]"
)

_STRUCTURED_REF_COMPACT_RE = re.compile(
    r"(?i)(?:pattern(?:definition)?(?:id|ref)|rule(?:id|ref)|"
    r"modecontract(?:version|id|ref)|"
    r"window(?:instance|definition)?(?:id|ref)|"
    r"(?:source)?revision(?:id|ref)?|scopebinding(?:id|ref)|"
    r"policy(?:id|ref)|signaldefinition(?:id|ref)|stratum(?:id|ref)|"
    r"comparisonreference(?:id|ref))[:=]"
)

_NON_AUDIENCE_REF_KEYS = re.compile(
    r"(id|ref)(?:$|[A-Z_])", re.IGNORECASE)


class D10ProjectionError(Exception):
    """Integrity violation in the D10 projection layer (fail closed)."""


def _assert_authoritative_result(
    typed: D10TypedInput,
    result: D10RunResult,
) -> None:
    """Bind every projection to the authoritative deterministic result.

    The projection layer never re-runs the evaluator and never re-derives
    the medical disposition; it binds the supplied result to the supplied
    typed bundle on the deterministic identity axes.  A result that does
    not belong to the typed bundle fails closed:

    * unit/gate exclusivity: exactly one of the unit/gate leaves is
      present;
    * the top-level disposition agrees with the present leaf
      (``unit.l1_disposition`` / ``gate.gate_kind``);
    * the stable core is the typed stable core (unit) or ``None`` (gate);
    * the trace carries exactly one leaf whose content identity, stable
      core, replay flag and terminal state equal the result fields and
      whose kind matches the replay flag;
    * the evaluation content identity is a non-empty 64-hex digest equal
      to the trace leaf's content identity.
    """
    if not isinstance(result, D10RunResult):
        raise D10ProjectionError("result must be a D10RunResult")
    if (not result.evaluation_content_identity
            or len(result.evaluation_content_identity) != 64
            or any(c not in "0123456789abcdef"
                   for c in result.evaluation_content_identity)):
        raise D10ProjectionError(
            "result evaluation content identity is empty or malformed")
    unit = result.unit
    gate = result.gate
    if (unit is None) == (gate is None):
        raise D10ProjectionError(
            "result must carry exactly one of unit or gate leaf")
    if result.trace is None or len(result.trace) != 1:
        raise D10ProjectionError("result trace must carry exactly one leaf")
    trace_leaf = result.trace[0]
    if trace_leaf.content_identity != result.evaluation_content_identity:
        raise D10ProjectionError(
            "result trace content identity does not match the evaluation "
            "content identity")
    if trace_leaf.replay_byte_equal != result.replay_byte_equal:
        raise D10ProjectionError(
            "result trace replay flag does not match the result")
    if trace_leaf.terminal_state != result.terminal_state:
        raise D10ProjectionError(
            "result trace terminal state does not match the result")
    expected_trace_kind = ("admission_replay" if result.replay_byte_equal
                           else "evaluation_identity")
    if trace_leaf.trace_kind != expected_trace_kind:
        raise D10ProjectionError(
            f"result trace kind {trace_leaf.trace_kind!r} does not match "
            f"the replay state {result.replay_byte_equal!r}")
    if trace_leaf.stable_core_ref != result.stable_core_ref:
        raise D10ProjectionError(
            "result trace stable core does not match the result")
    expected_core = d10_unit_stable_core(typed)
    if unit is not None:
        if unit.signal_kind != typed.signal_definition.signal_kind:
            raise D10ProjectionError(
                "result unit signal kind does not match the typed bundle")
        if unit.l1_disposition != result.disposition_or_gate:
            raise D10ProjectionError(
                "result unit disposition does not match the top-level one")
        if unit.stable_core_ref != expected_core:
            raise D10ProjectionError(
                "result unit stable core does not match the typed bundle")
        if result.stable_core_ref != expected_core:
            raise D10ProjectionError(
                "result stable core does not match the typed bundle")
    else:
        if gate.signal_kind != typed.signal_definition.signal_kind:
            raise D10ProjectionError(
                "result gate signal kind does not match the typed bundle")
        if gate.gate_kind != result.disposition_or_gate:
            raise D10ProjectionError(
                "result gate kind does not match the top-level one")
        if result.stable_core_ref is not None:
            raise D10ProjectionError(
                "a gate result must not carry a stable core")


def _assert_clean_zh(*texts: str) -> None:
    """Reject forbidden internal labels and raw enum/status/backend tokens in
    user-facing Chinese strings."""
    for text in texts:
        for term in _FORBIDDEN_INTERNAL_TERMS:
            if term in text:
                raise D10ProjectionError(
                    f"forbidden internal label {term!r} in user-facing text")
        lowered = text.lower()
        for token in _FORBIDDEN_RAW_TOKENS:
            if token in lowered:
                raise D10ProjectionError(
                    f"raw internal token {token!r} in user-facing text")


def _assert_no_structured_ref_in_text(
    typed: D10TypedInput,
    *texts: str,
) -> None:
    """Prevent trace/contract identifiers from entering audience prose."""
    refs: set = set()
    refs.update((
        typed.envelope_id,
        typed.project_ref,
        typed.run_ref,
        typed.snapshot_ref,
        typed.mode_contract.mode_contract_version,
        typed.project_scope_binding.scope_binding_id,
        typed.signal_definition.signal_definition_id,
        typed.signal_definition.positive_rule_ref,
        typed.signal_definition.legal_matrix_row_ref,
        typed.legal_matrix_row.row_id,
        typed.stratum.stratum_contract_id,
        typed.comparison_gate.comparison_reference_stable_id,
        typed.comparison_gate.required_site_count_ref,
        typed.window_pair_gate.required_window_count_ref,
        typed.site_ledger.ledger_id,
        typed.audience_text.audience_contract_id,
        typed.visibility_decision.decision_id,
        typed.visibility_decision.audience_scope_id,
        typed.query_decision.unit_member_set_hash,
        typed.query_decision.coverage_proof_hash,
        typed.denominator.denominator_kind,
        typed.numeric_policy.policy_id,
    ))
    refs.update(tuple(p.revision_id for p in typed.source_revision_content_pairs))
    refs.update(tuple(p.content_hash for p in typed.source_revision_content_pairs))
    refs.update(tuple(m.member_ref for m in typed.members))
    refs.update(tuple(e.locator_id for e in typed.evidence_refs))
    for window in typed.analysis_windows:
        refs.update((
            window.analysis_window_stable_id,
            window.window_instance_id,
            window.window_definition_id,
            window.cutoff_ref or "",
        ))
    for member in typed.members:
        refs.update(
            tuple(member.source_locator_refs) + tuple(member.descendant_member_refs))
    if typed.measure_origin_binding is not None:
        refs.update((
            typed.measure_origin_binding.binding_id,
            typed.measure_origin_binding.measure_ref,
        ))
    if typed.change_decision is not None:
        ch = typed.change_decision
        refs.update((ch.execution_basis, ch.r2_action,
                     ch.r2_prior_ref_or_none or ""))
        refs.update(tuple(ch.data_change_refs))
        refs.update(tuple(ch.rule_change_refs))
        refs.update(tuple(ch.method_change_refs))
        refs.update(tuple(ch.mode_change_refs))
    if typed.model_evidence is not None:
        refs.update((typed.model_evidence.model_evidence_id,
                     typed.model_evidence.model_id,
                     typed.model_evidence.model_version))
    if typed.safety_context is not None:
        refs.update(tuple(ref for ref in (
            typed.safety_context.context_id,
            typed.safety_context.exposure_definition_ref or "",
            typed.safety_context.coding_dictionary_ref or "",
            typed.safety_context.severity_scale_ref or "",
            typed.safety_context.risk_window_ref or "") if ref))
    if typed.efficacy_context is not None:
        refs.update(tuple(ref for ref in (
            typed.efficacy_context.context_id,
            typed.efficacy_context.endpoint_definition_ref or "",
            typed.efficacy_context.estimand_ref or "",
            typed.efficacy_context.treatment_role_authority_ref or "") if ref))
    for text in texts:
        if not isinstance(text, str) or not text:
            raise D10ProjectionError("empty user-facing text")
        if any(unicodedata.category(character).startswith("C")
               for character in text):
            raise D10ProjectionError(
                "invisible format character in user-facing text")
        if d10_normalize_nfc(text) != text:
            raise D10ProjectionError(
                "user-facing text must be Unicode NFC")
        normalized_text = unicodedata.normalize("NFKC", text)
        compact_ascii = "".join(
            character for character in normalized_text
            if character.isascii()
            and (character.isalnum() or character in ":=")
        )
        if (_STRUCTURED_REF_KEY_RE.search(normalized_text)
                or _STRUCTURED_REF_COMPACT_RE.search(compact_ascii)):
            raise D10ProjectionError(
                "structured engineering reference syntax in user-facing text")
        for ref in sorted(refs):
            if not ref:
                continue
            normalized_ref = unicodedata.normalize("NFKC", ref)
            compact_ref = "".join(
                character for character in normalized_ref
                if character.isascii() and character.isalnum()
            )
            if (normalized_ref in normalized_text
                    or (compact_ref and compact_ref in compact_ascii)):
                raise D10ProjectionError(
                    "structured engineering reference in user-facing text")


def _fmt(template: str, value: int) -> str:
    return template.replace("{n}", str(value))


def _evaluation_window_instance_ref(typed: D10TypedInput) -> str:
    if typed.analysis_windows:
        return typed.analysis_windows[-1].window_instance_id
    return ""


def _window_text(typed: D10TypedInput) -> str:
    """Human-readable bounds of the current window instance."""
    if not typed.analysis_windows:
        return "本次"
    window = typed.analysis_windows[-1]
    if window.window_start and window.window_end:
        return f"{window.window_start} 至 {window.window_end}"
    return "本次"


def _window_kind_zh(typed: D10TypedInput) -> str:
    if not typed.analysis_windows:
        return "分析窗"
    return _WINDOW_KIND_LABELS_ZH.get(
        typed.analysis_windows[-1].window_kind, "分析窗")


# ---------------------------------------------------------------------------
# Visibility partition (contract section 13)
# ---------------------------------------------------------------------------


def _resolve_visibility_members(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """Closed resolution of the audience member partition.

    Returns ``(evaluation_refs, projectable_refs, hidden_refs)`` as sorted
    tuples.  For an admitted unit (the evaluator already validated the
    partition algebra and any violation is an integrity gate) the explicit
    typed sets are authoritative and every strict invariant is re-checked.
    For a gate run there is no audience payload and the resolution is a
    shape-safe view that never surfaces refs outside the member set.
    """
    all_refs = tuple(sorted(m.member_ref for m in typed.members))
    all_set = set(all_refs)
    visibility = typed.visibility_decision
    explicit_eval = set(visibility.evaluation_member_refs or ())
    explicit_proj = set(visibility.projectable_member_refs or ())
    explicit_hidden = set(visibility.hidden_member_refs or ())
    if result.unit is not None:
        explicit_all = explicit_eval | explicit_proj | explicit_hidden
        unknown = explicit_all - all_set
        if unknown:
            raise D10ProjectionError(
                "unknown member refs in visibility decision: "
                f"{sorted(unknown)!r}")
        evaluation = explicit_eval if explicit_eval else all_set
        projectable = explicit_proj if explicit_proj \
            else evaluation - explicit_hidden
        hidden = explicit_hidden if explicit_hidden \
            else (evaluation - projectable)
        if projectable - evaluation:
            raise D10ProjectionError(
                "projectable refs outside the evaluation set")
        if hidden - evaluation:
            raise D10ProjectionError("hidden refs outside the evaluation set")
        if projectable & hidden:
            raise D10ProjectionError("projectable/hidden member overlap")
        if explicit_proj and explicit_hidden and (
                projectable | hidden) != evaluation:
            raise D10ProjectionError(
                "explicit visibility partition does not reconcile with the "
                "evaluation set")
        return (tuple(sorted(evaluation)), tuple(sorted(projectable)),
                tuple(sorted(hidden)))
    # Gate run: no audience payload; resolve a shape-safe view over the
    # member set only (refs outside the member set cannot be projected).
    evaluation = explicit_eval if explicit_eval else all_set
    hidden = explicit_hidden & all_set
    projectable = (explicit_proj if explicit_proj else evaluation) - hidden
    projectable &= all_set
    evaluation |= projectable | hidden
    if projectable & hidden:
        raise D10ProjectionError("projectable/hidden member overlap")
    return (tuple(sorted(evaluation)), tuple(sorted(projectable)),
            tuple(sorted(hidden)))


def _resolve_visibility_sites(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """Closed resolution of the audience site partition.

    Returns ``(evaluation_sites, projectable_sites, hidden_sites)`` sorted
    from the typed site plane (the authoritative visibility input).  For an
    admitted unit the evaluator already validated the site algebra; this
    projection re-checks the projectable/hidden disjointness and
    evaluation containment invariants and fails closed on any
    contradiction.  Gate runs resolve a shape-safe view instead.
    """
    visibility = typed.visibility_decision
    evaluation = tuple(sorted(set(visibility.evaluation_site_refs or ())))
    projectable = tuple(sorted(set(visibility.projectable_site_refs or ())))
    hidden = tuple(sorted(set(visibility.hidden_site_refs or ())))
    if set(projectable) & set(hidden):
        raise D10ProjectionError("projectable/hidden site overlap")
    if result.unit is not None:
        if (set(projectable) | set(hidden)) - set(evaluation):
            # A site that is neither evaluated nor hidden is a projection
            # leak: it must fail closed rather than surface outside the
            # audience set.
            raise D10ProjectionError(
                "site partition refs outside the evaluation site set")
    return evaluation, projectable, hidden


def _pair_visible_members(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[Any, ...]:
    """Member-site pair visibility (contract sections 12/13).

    The single source of truth is the exact typed
    ``visibility_decision.projectable_subject_site_pairs`` authority (plus
    its projectable member and site planes), not a derived heuristic.  A
    member is audience-visible only when:

    * its ``member_ref`` is in ``projectable_member_refs``;
    * its ``site_stable_id`` is in ``projectable_site_refs``; and
    * its exact ``(subject_stable_id, site_stable_id)`` pair is in
      ``projectable_subject_site_pairs``.

    A member of a hidden site or a wrong-scope site (e.g. the evaluator's
    ``member_resolution_failed`` members at ``SYN-OTHER-*``) has no
    projectable pair and is excluded from counts, markers, hotspots, links
    and payloads.
    """
    visibility = typed.visibility_decision
    projectable_member_refs = set(visibility.projectable_member_refs or ())
    projectable_site_refs = set(visibility.projectable_site_refs or ())
    projectable_pairs = set(
        (pair[0], pair[1])
        for pair in visibility.projectable_subject_site_pairs)
    return tuple(sorted(
        (m for m in typed.members
         if m.member_ref in projectable_member_refs
         and m.site_stable_id in projectable_site_refs
         and (m.subject_stable_id, m.site_stable_id) in projectable_pairs),
        key=lambda m: m.member_ref))


# ---------------------------------------------------------------------------
# Coverage and disposition helpers
# ---------------------------------------------------------------------------


def _coverage_state(typed: D10TypedInput) -> str:
    """Closed L0/L1 coverage summary over the required producer domains."""
    required = set(typed.signal_definition.required_producer_domains)
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


def _coverage_state_zh(typed: D10TypedInput) -> str:
    state = _coverage_state(typed)
    return _COVERAGE_STATE_ZH.get(state, state)


def _disposition_zh(result: D10RunResult) -> str:
    disposition = result.disposition_or_gate
    label = _FROZEN_DISPOSITION_ZH.get(disposition, "")
    return label


# Closed mapping of every decisive primary-reason code (from the frozen
# oracle/verifier vocabulary) to native Chinese.  Unknown codes fall back to
# conservative disposition-specific wording; raw internal reason codes never
# reach the audience.
_DISPOSITION_REASON_FALLBACK_ZH = {
    "positive": "命中既定监测规则；",
    "negative": "在本次可评价范围内未发现该类项目信号；",
    "boundary": "存在可定位线索，但条件尚不足以下确定性判定；",
    "not_applicable": "本次不适用；",
    "not_evaluable": "本次暂无法评价；",
    "global_gate": "本次未生成医学评价；",
    "integrity_gate": "本次未生成医学评价（数据自洽性校验未通过）；",
    "comparison_set_gate": "本次未生成医学评价（跨中心可比性尚未闭合）；",
    "window_pair_gate": "本次未生成医学评价（可比分析窗不足）；",
    "routing_gate": "本次未生成医学评价（归属路由未成立）；",
    "handoff_gate": "本次未生成医学评价（仅外部处置边界）；",
}

_PRIMARY_REASON_ZH = {
    "rule_hit_counterevidence_insufficient": "命中既定监测规则且反证不足以解释；",
    "no_hit_complete": "未命中既定监测规则；",
    "counterevidence_explains": "既定反证已充分解释；",
    "small_sample": "样本量较小，尚不足以下确定性判定；",
    "limited_evidence": "证据有限，需结合更多信息复核；",
    "deep_link_deficient": "具备可定位线索但来源定位不完整；",
    "evidence_not_typed_positive_forbidden": "当前证据形态不足以直接判定为项目信号；",
    "mixed_origin_separate_leaves": "同源关系混合，需分叶计量；",
    "analysis_population_missing": "分析人群缺失，无法完成评价；",
    "audience_injection_blocked": "受众文本校验未通过；",
    "authority_unresolvable": "评价权威未能解析；",
    "blind_treatment_inference": "盲态边界被突破，禁止据此推断分组；",
    "case_mix_mismatch": "中心间病例构成存在差异，可比性受限；",
    "case_mix_missing": "中心间病例构成信息缺失，可比性受限；",
    "claim_token_unresolved": "归属路由未能解析；",
    "consume_only_no_medical_unit": "仅作消费引用的归属，不生成医学单元；",
    "control_plane_comparison_gate": "跨中心可比性尚未闭合；",
    "control_plane_window_pair_gate": "可比分析窗不足；",
    "cross_layer_count_mixing": "跨层计数混加校验未通过；",
    "cutoff_advance_tamper": "数据截止推进判定校验未通过；",
    "cutoff_not_evaluable": "数据截止推进无法评价；",
    "d06_efficacy_not_d09_pattern": "疗效测量不能充当中心模式；",
    "d09_parent_descendant_duplication": "中心模式与其成员重复计数；",
    "deep_link_eligible_violation": "深链可跳转集合校验未通过；",
    "denominator_tamper": "分母修订校验未通过；",
    "design_not_applicable": "当前阶段或分析集不适用；",
    "duplicate_content_identity": "存在重复内容身份；",
    "duplicate_query_per_unit": "每个单元只允许一条查询草稿；",
    "efficacy_context_incomplete": "疗效评价上下文不完整；",
    "excluded_member_counted": "排除成员被错误计入；",
    "expected_set_routed_consume_only": "期望集路由为消费引用；",
    "expected_set_routing_gate_unresolved": "期望集路由未解析；",
    "exposure_shortfall": "暴露不足，相关比例需谨慎解读；",
    "fake_change_claim": "变化判定与数据事实不一致；",
    "followup_shortfall": "随访不足，相关趋势需谨慎解读；",
    "gap_only_provenance": "缺口来源仅为原始记录，未获认可；",
    "global_admission_failed": "项目级准入未通过；",
    "handoff_only_no_medical_unit": "仅外部处置边界，不生成医学单元；",
    "heterogeneous_sites": "中心间存在异质性，分布需分中心复核；",
    "hidden_member_dropped": "隐藏成员集合校验未通过；",
    "hidden_set_omitted": "隐藏集合遗漏校验未通过；",
    "hotspot_hidden": "高风险热点被隐藏，须保持可见；",
    "identity_state_unstable": "成员身份状态不稳定；",
    "invalid_numeric": "数值校验未通过；",
    "legal_matrix_row_mismatch": "规则授权矩阵不一致；",
    "legal_row_mismatch": "规则授权矩阵不一致；",
    "member_resolution_failed": "成员解析失败；",
    "method_validity_insufficient": "方法前提未充分满足；",
    "origin_ambiguous": "同源关系不明确；",
    "origin_not_evaluable": "同源关系无法评价；",
    "origin_wrong_scope": "同源关系超出授权范围；",
    "opportunity_ledger_incomplete": "机会账本未闭合；",
    "owner_route_unauthorized": "归属路由未获授权；",
    "query_redundancy_tamper": "查询冗余判定校验未通过；",
    "query_source_tamper": "查询来源校验未通过；",
    "r2_create_non_data_mixed": "首建动作混入非数据变化；",
    "r2_wrong_lineage": "延续关系与动作不一致；",
    "r2_wrong_prior": "生命周期前序引用不正确；",
    "rehash_bypass_evaluator_identity": "内容重签名绕过评价身份校验；",
    "required_l1_hole": "必需医学记录存在缺口；",
    "safety_context_incomplete": "安全性评价上下文不完整；",
    "same_origin_double_count": "同源事件被重复计数；",
    "scope_binding_mismatch": "项目范围绑定不一致；",
    "site_evidence_incomplete": "个别中心证据不完整；",
    "site_late_start": "个别中心启动晚，随访覆盖受限；",
    "site_late_start_outlier": "个别中心启动晚且偏离明显；",
    "site_quality_judgment": "涉及中心质量判定边界，仅提示复核；",
    "site_small": "个别中心样本量小，相关比例需谨慎比较；",
    "site_small_outlier": "个别中心样本量小且偏离明显，相关比例需谨慎比较；",
    "source_authority_mismatch": "来源成员与评价权威不一致；",
    "time_segment_overlap": "时间段存在重叠；",
    "time_segment_tamper": "时间段数据校验未通过；",
    "treatment_assignment_missing": "治疗分配信息缺失；",
    "visibility_algebra": "可见性集合代数校验未通过；",
    "zero_denominator_not_negative": "零分母不作为阴性判定的依据；",
    "evaluation_authority_missing": "评价权威缺失；",
    "authority_identity_mismatch": "项目身份与评价权威不一致；",
    "model_authority_mismatch": "模型证据与评价权威不一致；",
    "envelope_source_revision_mismatch": "来源修订与封套不一致；",
    "mode_contract_tamper": "模式合同校验未通过；",
    "scope_binding_tamper": "项目范围绑定校验未通过；",
    "source_revision_hash_tamper": "来源修订哈希校验未通过；",
    "descendant_set_tamper": "成员继承集合校验未通过；",
    "query_identity_bad": "查询身份校验未通过；",
    "cutoff_advance_mixed": "数据截止推进混入非数据变化；",
    "nontyped_evidence_no_positive": "非类型化证据不足以判定为项目信号；",
}


def _primary_reason_zh(result: D10RunResult) -> str:
    """Native-Chinese primary reason for the authoritative disposition; raw
    internal reason codes never reach the audience."""
    reason = result.primary_reason
    label = _PRIMARY_REASON_ZH.get(reason)
    if label is None:
        label = _DISPOSITION_REASON_FALLBACK_ZH.get(
            result.disposition_or_gate, "本次未生成医学评价；")
    _assert_clean_zh(label)
    return label


def _denominator_zh(typed: D10TypedInput, result: D10RunResult) -> Optional[str]:
    unit_key = _DEN_UNIT_BY_KIND.get(typed.denominator.denominator_kind, "")
    unit_zh = _UNIT_LABELS_ZH.get(unit_key, "")
    label_zh = _DENOMINATOR_LABELS_ZH.get(
        typed.denominator.denominator_kind, typed.denominator.denominator_kind)
    value = result.unit.denominator_value if result.unit is not None else (
        result.gate.denominator_value if result.gate is not None else 0)
    if result.unit is None and value == 0 and unit_zh == "":
        return None
    parts = [label_zh, str(value)]
    if unit_zh:
        parts.append(unit_zh)
    return " ".join(parts)


def _half_up(value: float, precision: int) -> float:
    factor = 10 ** precision
    return math.floor(value * factor + 0.5) / factor


def _signal_label_zh(typed: D10TypedInput) -> str:
    return _SIGNAL_KIND_LABELS_ZH.get(
        typed.signal_definition.signal_kind,
        typed.signal_definition.signal_kind)


def _member_locator(member: Any) -> Optional[str]:
    """First source locator only when the member is typed locatable."""
    if not member.source_locator_refs:
        return None
    state = getattr(member, "locator_resolution_state", "locatable")
    if state != "locatable":
        return None
    return member.source_locator_refs[0]


# ---------------------------------------------------------------------------
# Audience visibility projection (contract sections 12/13)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10AudienceProjection:
    """Renderer-neutral audience projection for one run.

    ``projectable_member_refs`` / ``projectable_site_refs`` are the only
    planes the audience may see; the evaluation planes may exceed them.
    ``disclosure_leak_present`` is always False because the projection
    layer fails closed whenever a hidden member/site would reach any
    audience payload.
    """

    audience_scope_id: str
    projectable_member_refs: Tuple[str, ...]
    evaluation_member_refs: Tuple[str, ...]
    hidden_member_refs: Tuple[str, ...]
    projectable_site_refs: Tuple[str, ...]
    evaluation_site_refs: Tuple[str, ...]
    hidden_site_refs: Tuple[str, ...]
    hidden_member_count: int
    hidden_site_count: int
    audience_payload_present: bool
    risk_marker_present: bool
    query_present: bool
    hotspot_present: bool
    deep_link_present: bool
    rate_projection_state: str
    visible_n: Optional[int]
    eligible_n: Optional[int]
    coverage_state: str
    coverage_zh: str
    disposition_zh: str
    reason_zh: str
    disclosure_leak_present: bool


def build_d10_audience_projection(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10AudienceProjection:
    """Project the evaluation onto the audience plane (contract sections
    12/13)."""
    _assert_authoritative_result(typed, result)
    evaluation, projectable, hidden = _resolve_visibility_members(
        typed, result)
    eval_sites, proj_sites, hidden_sites = _resolve_visibility_sites(typed, result)
    pair_visible = _pair_visible_members(typed, result)
    pair_visible_refs = tuple(m.member_ref for m in pair_visible)
    visibility = typed.visibility_decision
    if set(hidden) & set(projectable):
        raise D10ProjectionError(
            "hidden member leaked into the projectable set")
    unit = result.unit
    # An admitted non-positive/not-evaluable unit or a gate carries no
    # audience payload; the independent count/status surface may still
    # explain 暂无法评价.  A member whose site is hidden is not part of the
    # audience boundary (the pair-visible set), so a run with no safe
    # member-site pair carries no audience payload.
    payload = (unit is not None
               and unit.l1_disposition not in ("not_evaluable",
                                               "not_applicable")
               and (not evaluation or bool(pair_visible)))
    risk_present = build_d10_risk_marker(typed, result) is not None
    query_present = build_d10_query_draft(typed, result) is not None
    deep_link = bool(build_d10_deep_links(typed, result))
    coverage_state = _coverage_state(typed)
    coverage_zh = _FROZEN_COUNT_ZH["coverage_zh"]
    disposition_zh = _disposition_zh(result)
    _assert_clean_zh(coverage_zh, disposition_zh)
    return D10AudienceProjection(
        audience_scope_id=visibility.audience_scope_id,
        projectable_member_refs=pair_visible_refs,
        evaluation_member_refs=evaluation,
        hidden_member_refs=hidden,
        projectable_site_refs=proj_sites,
        evaluation_site_refs=eval_sites,
        hidden_site_refs=hidden_sites,
        hidden_member_count=len(hidden),
        hidden_site_count=len(hidden_sites),
        audience_payload_present=payload,
        risk_marker_present=risk_present,
        query_present=query_present,
        hotspot_present=bool(build_d10_hotspots(typed, result)),
        deep_link_present=deep_link,
        rate_projection_state=visibility.rate_projection_state,
        visible_n=visibility.visible_n,
        eligible_n=visibility.eligible_n,
        coverage_state=coverage_state,
        coverage_zh=coverage_zh,
        disposition_zh=disposition_zh,
        reason_zh=_primary_reason_zh(result),
        disclosure_leak_present=False,
    )


# ---------------------------------------------------------------------------
# Separated count surface (contract section 10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectionCountSurface:
    """Separated count surface.

    ``individual_risk_count`` / ``affected_subject_count`` /
    ``event_or_outcome_count`` / ``center_pattern_count`` /
    ``affected_site_count`` / ``project_signal_count`` / ``clue_count`` /
    ``query_count`` are kept strictly separate and never summed.  All
    counts are computed over the projectable audience plane only (equal to
    the evaluator's evaluation-plane counts when nothing is hidden); the
    evaluation-plane raw counts never cross this projection boundary.
    Event/outcome and site counts that cannot be attributed to the visible
    plane without disclosure risk are suppressed to zero with the
    visibility state carried on ``rate_projection_state`` and ``disabled``
    flags.  Chinese forms use the frozen contract section 10 wording.
    """

    evaluation_window_instance_ref: str
    individual_risk_count: int
    affected_subject_count: int
    event_or_outcome_count: int
    center_pattern_count: int
    affected_site_count: int
    project_signal_count: int
    clue_count: int
    query_count: int
    numerator_member_count: int
    hidden_member_count: int
    hidden_site_count: int
    visible_individual_risk_count: int
    visible_affected_subject_count: int
    visible_event_or_outcome_count: int
    visible_center_pattern_count: int
    visible_affected_site_count: int
    event_count_disabled: bool
    site_count_disabled: bool
    visible_n: Optional[int]
    eligible_n: Optional[int]
    rate_projection_state: str
    individual_risk_zh: str
    affected_subjects_zh: str
    event_or_outcome_zh: str
    center_pattern_zh: str
    affected_site_zh: str
    project_signal_zh: str
    clue_zh: Optional[str]
    query_count_zh: str
    coverage_zh: str
    coverage_state_zh: str
    denominator_zh: Optional[str]
    rate_zh: Optional[str]
    disposition_zh: str


def build_d10_count_surface(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectionCountSurface:
    """Build the separated count surface with frozen Chinese forms."""
    _assert_authoritative_result(typed, result)
    _evaluation, _projectable, hidden = _resolve_visibility_members(
        typed, result)
    _eval_sites, _proj_sites, hidden_sites = _resolve_visibility_sites(typed, result)
    hidden_member_count = len(hidden)
    hidden_site_count = len(hidden_sites)
    unit = result.unit
    visibility = typed.visibility_decision
    rate_state = visibility.rate_projection_state
    coverage_zh = _FROZEN_COUNT_ZH["coverage_zh"]
    coverage_state_zh = _coverage_state_zh(typed)
    disposition_zh = _disposition_zh(result)
    window_instance = _evaluation_window_instance_ref(typed)

    if unit is None:
        base = D10ProjectionCountSurface(
            evaluation_window_instance_ref=window_instance,
            individual_risk_count=0, affected_subject_count=0,
            event_or_outcome_count=0, center_pattern_count=0,
            affected_site_count=0, project_signal_count=0, clue_count=0,
            query_count=0, numerator_member_count=0,
            hidden_member_count=hidden_member_count,
            hidden_site_count=hidden_site_count,
            visible_individual_risk_count=0,
            visible_affected_subject_count=0,
            visible_event_or_outcome_count=0,
            visible_center_pattern_count=0, visible_affected_site_count=0,
            event_count_disabled=False, site_count_disabled=False,
            visible_n=visibility.visible_n,
            eligible_n=visibility.eligible_n,
            rate_projection_state=rate_state,
            individual_risk_zh=_fmt(
                _FROZEN_COUNT_ZH["individual_risk_count_zh"], 0),
            affected_subjects_zh=_fmt(
                _FROZEN_COUNT_ZH["affected_subjects_zh"], 0),
            event_or_outcome_zh=_fmt(
                _FROZEN_COUNT_ZH["event_or_outcome_count_zh"], 0),
            center_pattern_zh=_fmt(
                _FROZEN_COUNT_ZH["center_pattern_count_zh"], 0),
            affected_site_zh=_fmt(
                _FROZEN_COUNT_ZH["affected_site_count_zh"], 0),
            project_signal_zh=_fmt(
                _FROZEN_COUNT_ZH["project_signal_count_zh"], 0),
            clue_zh=None,
            query_count_zh=_fmt(_FROZEN_COUNT_ZH["query_count_zh"], 0),
            coverage_zh=coverage_zh,
            coverage_state_zh=coverage_state_zh,
            denominator_zh=None,
            rate_zh=None,
            disposition_zh=disposition_zh,
        )
        _assert_clean_zh(
            base.individual_risk_zh, base.affected_subjects_zh,
            base.event_or_outcome_zh, base.center_pattern_zh,
            base.affected_site_zh, base.project_signal_zh,
            base.query_count_zh, coverage_zh, coverage_state_zh,
            disposition_zh)
        return base

    # All member-derived counts use the exact pair-visible member set (the
    # typed projectable_subject_site_pairs authority): a member whose exact
    # (subject, site) pair is not projectable -- hidden site or wrong-scope
    # site -- is never counted, so it cannot leak through individual/
    # subject/center-pattern or numerator-member counts.
    proj_members = _pair_visible_members(typed, result)
    projectable_set = {m.member_ref for m in proj_members}
    individual = len({m.member_ref for m in proj_members
                      if m.member_kind == "individual_risk"})
    subjects = len({m.subject_stable_id for m in proj_members
                    if m.subject_stable_id})
    patterns = len({m.member_ref for m in proj_members
                    if m.member_kind == "center_pattern"})
    # The affected-site and event/outcome counts are numerator-ledger facts
    # (never recomputed per member).  They are disclosed only when at least
    # one member-site pair is visible; with no visible pair (hidden site or
    # wrong-scope site) they are suppressed to zero because they would
    # confirm an excluded site or member.
    no_pair_visible = not proj_members
    site_count_disabled = hidden_site_count > 0 or no_pair_visible
    visible_sites = 0 if site_count_disabled else unit.affected_site_count
    withheld = hidden_member_count > 0 or hidden_site_count > 0 \
        or no_pair_visible
    event_count_disabled = withheld
    events = 0 if withheld else unit.event_or_outcome_count
    signal_count = unit.project_signal_count
    clue_count = unit.clue_count
    query_count = 1 if build_d10_query_draft(typed, result) is not None else 0
    numerator_members = len(projectable_set)

    denominator_zh: Optional[str] = None
    unit_key = _DEN_UNIT_BY_KIND.get(unit.denominator_kind, "")
    unit_zh = _UNIT_LABELS_ZH.get(unit_key, "")
    label_zh = _DENOMINATOR_LABELS_ZH.get(
        unit.denominator_kind, unit.denominator_kind)
    if unit.denominator_value > 0 or unit_zh:
        denominator_zh = " ".join(part for part in
                                  (label_zh, str(unit.denominator_value),
                                   unit_zh) if part)
    rate_zh: Optional[str] = None
    if (rate_state == "permitted" and hidden_member_count == 0
            and hidden_site_count == 0 and not no_pair_visible
            and unit.denominator_value > 0):
        precision = max(0, typed.numeric_policy.display_precision)
        percent = _half_up(100.0 * subjects / unit.denominator_value,
                           precision)
        rate_zh = f"{subjects}/{unit.denominator_value}（{percent:.{precision}f}%）"

    individual_risk_zh = _fmt(
        _FROZEN_COUNT_ZH["individual_risk_count_zh"], individual)
    affected_subjects_zh = _fmt(
        _FROZEN_COUNT_ZH["affected_subjects_zh"], subjects)
    event_or_outcome_zh = _fmt(
        _FROZEN_COUNT_ZH["event_or_outcome_count_zh"], events)
    center_pattern_zh = _fmt(
        _FROZEN_COUNT_ZH["center_pattern_count_zh"], patterns)
    affected_site_zh = _fmt(
        _FROZEN_COUNT_ZH["affected_site_count_zh"], visible_sites)
    project_signal_zh = _fmt(
        _FROZEN_COUNT_ZH["project_signal_count_zh"], signal_count)
    query_count_zh = _fmt(_FROZEN_COUNT_ZH["query_count_zh"], query_count)
    clue_zh = (_fmt(_FROZEN_COUNT_ZH["clue_count_zh"], clue_count)
               if clue_count else None)
    _assert_clean_zh(
        individual_risk_zh, affected_subjects_zh, event_or_outcome_zh,
        center_pattern_zh, affected_site_zh, project_signal_zh,
        query_count_zh, coverage_zh, coverage_state_zh,
        denominator_zh or "", rate_zh or "", clue_zh or "",
        disposition_zh)
    return D10ProjectionCountSurface(
        evaluation_window_instance_ref=window_instance,
        individual_risk_count=individual,
        affected_subject_count=subjects,
        event_or_outcome_count=events,
        center_pattern_count=patterns,
        affected_site_count=visible_sites,
        project_signal_count=signal_count,
        clue_count=clue_count,
        query_count=query_count,
        numerator_member_count=numerator_members,
        hidden_member_count=hidden_member_count,
        hidden_site_count=hidden_site_count,
        visible_individual_risk_count=individual,
        visible_affected_subject_count=subjects,
        visible_event_or_outcome_count=events,
        visible_center_pattern_count=patterns,
        visible_affected_site_count=visible_sites,
        event_count_disabled=event_count_disabled,
        site_count_disabled=site_count_disabled,
        visible_n=visibility.visible_n,
        eligible_n=visibility.eligible_n,
        rate_projection_state=rate_state,
        individual_risk_zh=individual_risk_zh,
        affected_subjects_zh=affected_subjects_zh,
        event_or_outcome_zh=event_or_outcome_zh,
        center_pattern_zh=center_pattern_zh,
        affected_site_zh=affected_site_zh,
        project_signal_zh=project_signal_zh,
        clue_zh=clue_zh,
        query_count_zh=query_count_zh,
        coverage_zh=coverage_zh,
        coverage_state_zh=coverage_state_zh,
        denominator_zh=denominator_zh,
        rate_zh=rate_zh,
        disposition_zh=disposition_zh,
    )


# ---------------------------------------------------------------------------
# Projection version (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectionVersion:
    """Versioned projection identity.

    Binds the projection to the authoritative evaluation content identity,
    the measure ledger, the stable risk core, the visibility decision set
    and the frozen audience contract.  Opaque run/snapshot ids are audit
    refs only and never enter the content hash.
    """

    projection_version_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    source_evaluation_content_identities: Tuple[str, ...]
    source_ledger_hashes: Tuple[str, ...]
    source_risk_refs: Tuple[str, ...]
    visibility_decision_refs: Tuple[str, ...]
    audience_contract_ref: str
    supersedes_projection_ref: Optional[str]
    projection_content_hash: str
    projection_version_content_hash: str


def build_d10_projection_version(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectionVersion:
    """Build the versioned projection identity for one run."""
    _assert_authoritative_result(typed, result)
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    content_identity = result.evaluation_content_identity
    # (the strengthened authoritative binding guarantees the result identity
    # is a non-empty 64-hex digest equal to its trace leaf content identity)
    stable_core = result.stable_core_ref or ""
    measure_ref = _measure_ledger_ref(typed, result)
    visibility = typed.visibility_decision
    supersedes = None
    if typed.change_decision is not None:
        supersedes = typed.change_decision.prior_snapshot_ref_or_none
    content_core = {
        "project_ref": typed.project_ref,
        "source_evaluation_content_identities": [content_identity],
        "source_ledger_hashes": [measure_ref],
        "source_risk_refs": [stable_core] if stable_core else [],
        "visibility_decision_refs": [visibility.decision_id],
        "audience_contract_ref": typed.audience_text.audience_contract_id,
        "supersedes_projection_ref": supersedes,
        "algorithm_version": _ALGORITHM_VERSION,
    }
    projection_content_hash = d10_content_hash(content_core)
    version_identity_content = {
        "project_ref": typed.project_ref,
        "run_ref": typed.run_ref,
        "snapshot_ref": typed.snapshot_ref,
        "cutoff_ref": window.cutoff_ref if window else None,
        "projection_content_hash": projection_content_hash,
    }
    projection_version_id = d10_content_hash(version_identity_content)
    return D10ProjectionVersion(
        projection_version_id=projection_version_id,
        project_ref=typed.project_ref,
        run_ref=typed.run_ref,
        snapshot_ref=typed.snapshot_ref,
        cutoff_ref=window.cutoff_ref if window else None,
        source_evaluation_content_identities=(content_identity,),
        source_ledger_hashes=(measure_ref,),
        source_risk_refs=(stable_core,) if stable_core else (),
        visibility_decision_refs=(visibility.decision_id,),
        audience_contract_ref=typed.audience_text.audience_contract_id,
        supersedes_projection_ref=supersedes,
        projection_content_hash=projection_content_hash,
        projection_version_content_hash=projection_version_id,
    )


# ---------------------------------------------------------------------------
# Project-signal risk marker (contract section 10)
# ---------------------------------------------------------------------------


def d10_public_risk_identity(typed: D10TypedInput) -> Dict[str, Any]:
    """Stable public D10 risk identity (contract section 10 canonical
    tuple): excludes run/snapshot ids, computed dates, revisions and display
    text; never merges with D01-D09 public identities."""
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    return {
        "project_ref": typed.project_ref,
        "domain_id": D10_DOMAIN_ID,
        "scope_type": "project",
        "stable_source_or_event_identity": (
            typed.signal_definition.signal_definition_id,
            window.analysis_window_stable_id if window else "",
            typed.stratum.stratum_key,
            typed.comparison_gate.comparison_reference_stable_id,
        ),
        "normalized_concept": (
            typed.signal_definition.signal_kind,
            typed.signal_definition.signal_definition_id,
        ),
        "temporal_window": (
            window.window_kind if window else None,
            window.window_definition_id if window else None,
        ),
        "public_identity_version": _PUBLIC_IDENTITY_VERSION,
        "scope_binding_id": typed.project_scope_binding.scope_binding_id,
    }


@dataclass(frozen=True)
class D10RiskMarker:
    """Project-signal RiskInstance marker (contract section 10).

    An audience projection: references only the resolved projectable
    member/locator set.  The public identity is revision-free and replay
    stable; run/snapshot ids never enter it."""

    marker_id: str
    public_risk_identity: Dict[str, Any]
    stable_core: str
    risk_owner: str
    risk_kind: str
    aggregation_level: str
    member_refs: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    content_hash: str


def build_d10_risk_marker(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Optional[D10RiskMarker]:
    """Build the project-signal risk marker for the run's positive unit.

    Returns ``None`` unless the run carries exactly one positive project
    signal with at least one projectable member.  Boundary/negative/
    not-applicable/not-evaluable and gate runs never get a marker.
    """
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return None
    public_identity = d10_public_risk_identity(typed)
    # The marker references only the pair-visible member set: members of a
    # hidden site are never exposed through the marker or its locators.
    members = _pair_visible_members(typed, result)
    if not members:
        return None
    member_refs = tuple(sorted(m.member_ref for m in members))
    locators = tuple(sorted({locator
                             for m in members
                             for locator in m.source_locator_refs
                             if _member_locator(m) is not None}))
    marker_id = d10_content_hash({
        "public_d10_risk_identity": public_identity,
        "stable_core": unit.stable_core_ref,
        "member_refs": list(member_refs),
    })
    core = {
        "marker_id": marker_id,
        "public_risk_identity": public_identity,
        "stable_core": unit.stable_core_ref,
        "risk_owner": "D10",
        "risk_kind": "project_signal",
        "aggregation_level": "project_signal",
        "member_refs": list(member_refs),
        "source_locator_ids": list(locators),
    }
    return D10RiskMarker(
        marker_id=marker_id,
        public_risk_identity=public_identity,
        stable_core=unit.stable_core_ref,
        risk_owner="D10",
        risk_kind="project_signal",
        aggregation_level="project_signal",
        member_refs=member_refs,
        source_locator_ids=locators,
        content_hash=d10_content_hash(core),
    )


# ---------------------------------------------------------------------------
# Hotspot subject rows (contract section 7/10/12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10HotspotProjection:
    """One hotspot subject row.

    A projection only -- never an L1 unit and never a RiskInstance.  Only
    pair-visible members are referenced; hidden members and members of
    hidden sites never appear in rows, anchors, locators or ordering.
    Order is subject stable identity ascending -- never a punitive risk
    ranking and never a black-box score.
    """

    projection_id: str
    site_ref: str
    evaluation_window_instance_ref: str
    subject_ref: str
    member_refs: Tuple[str, ...]
    monitoring_priority: Optional[str]
    source_locator_refs: Tuple[str, ...]
    projectability_decision_ref: str


def build_d10_hotspots(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10HotspotProjection, ...]:
    """List hotspot subject rows (contract sections 7/10/12).

    The typed ``Hotspot`` member set is the authoritative high-risk hotspot
    fact (the evaluator already fails closed when a hidden-in-display
    hotspot is submitted).  Rows are projected on positive runs only, over
    the pair-visible member plane: the single high-risk subject is always
    preserved and is never hidden behind a low project proportion or a
    small-sample note.
    """
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return ()
    hotspot = typed.hotspot
    if hotspot is None or not hotspot.hotspot_member_refs:
        return ()
    if hotspot.hidden_in_display:
        raise D10ProjectionError("hidden-in-display hotspot must fail closed")
    member_by_ref = {m.member_ref: m for m in typed.members}
    pair_visible = _pair_visible_members(typed, result)
    pair_visible_refs = {m.member_ref for m in pair_visible}
    window_instance = _evaluation_window_instance_ref(typed)
    rows_by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for ref in hotspot.hotspot_member_refs:
        member = member_by_ref.get(ref)
        if member is None:
            raise D10ProjectionError(
                f"hotspot member ref {ref!r} has no typed member object")
        if ref not in pair_visible_refs:
            # the evaluator already rejects hidden member leakage; a member
            # of a hidden site is not pair-visible and must not surface
            raise D10ProjectionError(
                f"hotspot member {ref!r} is not pair-visible")
        key = (member.subject_stable_id or "", member.site_stable_id or "")
        row = rows_by_pair.setdefault(key, {
            "members": [],
            "locators": [],
            "priorities": [],
        })
        row["members"].append(ref)
        locator = _member_locator(member)
        if locator is not None and locator not in row["locators"]:
            row["locators"].append(locator)
        row["priorities"].append(member.monitoring_priority)
    rows: List[D10HotspotProjection] = []
    for key in sorted(rows_by_pair):
        subject, site = key
        row = rows_by_pair[key]
        priorities = [p for p in row["priorities"] if p]
        priority = ("high" if "high" in priorities
                    else "medium" if "medium" in priorities else None)
        member_refs = tuple(sorted(row["members"]))
        projection_id = d10_content_hash({
            "site_ref": site,
            "window_instance": window_instance,
            "subject_ref": subject,
            "member_refs": list(member_refs),
            "monitoring_priority": priority,
        })
        rows.append(D10HotspotProjection(
            projection_id=projection_id,
            site_ref=site,
            evaluation_window_instance_ref=window_instance,
            subject_ref=subject,
            member_refs=member_refs,
            monitoring_priority=priority,
            source_locator_refs=tuple(sorted(row["locators"])),
            projectability_decision_ref=(
                typed.visibility_decision.audience_scope_id),
        ))
    rows.sort(key=lambda row: (_PRIORITY_RANK.get(row.monitoring_priority, 99),
                               row.subject_ref))
    return tuple(rows)


# ---------------------------------------------------------------------------
# Verified one-hop deep links (contract sections 11/12/13)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10DeepLinkTarget:
    """One verified one-hop deep-link target.

    ``target_kind`` is one of ``member`` / ``site`` / ``subject_site_pair``
    and the target is bound to the exact typed eligible set, subject-site
    pair and visibility decision of the envelope (the evaluator already
    rejected any violation).  ``target_state`` is ``locatable`` only when
    the source locator resolves; otherwise it is ``unavailable`` with
    ``unavailable_message == 来源暂无法定位`` and no fabricated jump.
    ``return_state_key`` restores the originating projection state.
    """

    link_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    signal_definition_ref: str
    evaluation_window_instance_ref: str
    target_kind: str
    site_ref: Optional[str]
    subject_ref: Optional[str]
    member_object_ref: Optional[str]
    source_locator: Optional[str]
    locator_resolution_state: str
    target_state: str
    unavailable_message: Optional[str]
    visibility_decision_ref: str
    visibility_decision_hash: str
    return_state_key: str


def _deep_link_eligible_members(typed: D10TypedInput) -> Tuple[str, ...]:
    return tuple(sorted(set(
        typed.visibility_decision.deep_link_eligible_member_refs or ())))


def _deep_link_eligible_sites(typed: D10TypedInput) -> Tuple[str, ...]:
    return tuple(sorted(set(
        typed.visibility_decision.deep_link_eligible_site_refs or ())))


def _deep_link_eligible_pairs(
    typed: D10TypedInput,
) -> Tuple[Tuple[str, str], ...]:
    return tuple(sorted(set(
        tuple(p) for p in
        typed.visibility_decision.deep_link_eligible_subject_site_pairs or ())))


def build_d10_deep_links(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10DeepLinkTarget, ...]:
    """Project the typed deep-link targets (contract sections 11/12/13).

    The envelope's ``deep_links`` are the authoritative link set already
    validated against the visibility algebra by the deterministic
    evaluator.  This projection re-verifies the exact eligible-set /
    subject-site / visibility binding and emits an immutable target per
    link; unresolvable locators produce ``来源暂无法定位`` with no
    fabricated jump.  A submitted link that violates the eligible sets or
    the pair binding fails closed.
    """
    _assert_authoritative_result(typed, result)
    if result.unit is None:
        return ()
    member_by_ref = {m.member_ref: m for m in typed.members}
    eligible_members = set(_deep_link_eligible_members(typed))
    eligible_sites = set(_deep_link_eligible_sites(typed))
    eligible_pairs = set(_deep_link_eligible_pairs(typed))
    _eval_sites, proj_sites, _hidden_sites = _resolve_visibility_sites(typed, result)
    proj_site_set = set(proj_sites)
    window_instance = _evaluation_window_instance_ref(typed)
    visibility = typed.visibility_decision
    links: List[D10DeepLinkTarget] = []
    for link in typed.deep_links:
        if link.visibility_decision_ref != visibility.decision_id:
            raise D10ProjectionError(
                "deep link not bound to the current visibility decision")
        site_ref = link.site_ref
        subject_ref = link.subject_ref
        member_ref = link.member_object_ref
        member = member_by_ref.get(member_ref) if member_ref else None
        if link.target_kind == "member":
            if member_ref not in eligible_members or member is None:
                raise D10ProjectionError(
                    "member deep link outside the eligible member set")
            if member.site_stable_id not in proj_site_set:
                raise D10ProjectionError(
                    "member deep link targets a hidden site")
            if link.subject_ref != member.subject_stable_id \
                    or link.site_ref != member.site_stable_id:
                raise D10ProjectionError(
                    "member deep link subject/site mismatch")
            locator_state = getattr(member, "locator_resolution_state",
                                    "locatable")
            locator = _member_locator(member)
        elif link.target_kind == "site":
            if site_ref not in eligible_sites or site_ref not in proj_site_set:
                raise D10ProjectionError(
                    "site deep link outside the eligible/projectable site set")
            if subject_ref is not None or member_ref is not None:
                raise D10ProjectionError("site deep link carries extra refs")
            locator_state = "locatable"
            locator = None
        else:
            if (
                    subject_ref is None or site_ref is None
                    or (subject_ref, site_ref) not in eligible_pairs):
                raise D10ProjectionError(
                    "subject-site deep link outside the eligible pair set")
            if member_ref is not None:
                raise D10ProjectionError(
                    "subject-site deep link carries a member ref")
            potential = [m for m in typed.members
                         if m.subject_stable_id == subject_ref
                         and m.site_stable_id == site_ref]
            if not potential:
                raise D10ProjectionError(
                    "subject-site deep link has no resolvable member")
            locator_state = getattr(potential[0], "locator_resolution_state",
                                    "locatable")
            locator = _member_locator(potential[0])
        locatable = locator is not None and locator_state == "locatable"
        exposed_locator = locator if locatable else None
        link_id = d10_content_hash({
            "target_kind": link.target_kind,
            "site_ref": site_ref or "",
            "subject_ref": subject_ref or "",
            "member_ref": member_ref or "",
            "window_instance": window_instance,
            "locator": exposed_locator or "",
            "return_state_key": link.return_state_key,
            "visibility_decision_ref": visibility.decision_id,
        })
        links.append(D10DeepLinkTarget(
            link_id=link_id,
            project_ref=typed.project_ref,
            run_ref=typed.run_ref,
            snapshot_ref=typed.snapshot_ref,
            signal_definition_ref=typed.signal_definition.signal_definition_id,
            evaluation_window_instance_ref=window_instance,
            target_kind=link.target_kind,
            site_ref=site_ref,
            subject_ref=subject_ref,
            member_object_ref=member_ref,
            source_locator=exposed_locator,
            locator_resolution_state=locator_state,
            target_state="locatable" if locatable else "unavailable",
            unavailable_message=None if locatable else UNAVAILABLE_SOURCE_ZH,
            visibility_decision_ref=visibility.decision_id,
            visibility_decision_hash=visibility.decision_id,
            return_state_key=link.return_state_key,
        ))
    links.sort(key=lambda item: (
        item.target_kind, item.link_id))
    return tuple(links)


# ---------------------------------------------------------------------------
# Natural-Chinese three-sentence Query draft (contract sections 11/12)
# ---------------------------------------------------------------------------

# Frozen closed sentence-part kinds of ``D10AudienceTextContract``
# (contract section 12).  Query drafts render their three Chinese sentences
# ONLY from these typed parts; freehand sentences are never emitted.
_SENTENCE_PART_KINDS = frozenset((
    "authority_basis", "observed_finding", "denominator_context",
    "uncertainty", "counterevidence", "action_verify", "action_reconcile",
    "action_pd_verify", "source_business_identifier",
))

# Part kinds that are allowed to carry business identifiers (center/subject/
# record business ids).  Every other part kind must be free of them.
_BUSINESS_IDENTIFIER_PART_KINDS = frozenset(("source_business_identifier",))


@dataclass(frozen=True)
class D10AudiencePart:
    """One typed audience sentence part (closed kind + rendered Chinese).

    ``part_kind`` must be one of the frozen closed kinds; ``text_zh`` is the
    native-Chinese rendering.  Business center/subject/record identifiers may
    only appear in ``source_business_identifier`` parts."""

    part_kind: str
    text_zh: str


@dataclass(frozen=True)
class D10QueryDraft:
    """The single project-level Query draft of a positive unit.

    A draft only: never sent, never a task and never a workflow state
    (``draft_only`` is always True).  ``member_refs`` is the complete
    uncovered projectable member set restricted by the frozen redundancy
    decision -- never truncated.  The three sentences are native Chinese
    without engineering ids; all definition/rule/window/mode ids live in
    the structured ``basis_refs`` / ``source_revision_refs`` trace fields
    and the redundancy proof fields.
    """

    query_draft_id: str
    unit_stable_core: str
    evaluation_content_identity: str
    query_owner: str
    basis_parts: Tuple[D10AudiencePart, ...]
    finding_parts: Tuple[D10AudiencePart, ...]
    action_parts: Tuple[D10AudiencePart, ...]
    basis_sentence: str
    finding_sentence: str
    action_sentence: str
    member_refs: Tuple[str, ...]
    member_count: int
    evidence_refs: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    scope_binding_id: str
    redundancy_decision: str
    redundancy_decision_hash: str
    unit_member_set_hash: str
    coverage_proof_hash: str
    covered_member_refs: Tuple[str, ...]
    uncovered_member_refs: Tuple[str, ...]
    max_query_member_fanout: int
    pd_wording_state: str
    basis_refs: Tuple[str, ...]
    source_revision_refs: Tuple[str, ...]
    content_hash: str
    draft_only: bool = True


def _query_evidence_refs(
    typed: D10TypedInput,
    member_refs: Sequence[str],
) -> Tuple[str, ...]:
    """Deterministic locatable evidence set of the complete member list;
    every listed member must contribute a locator or the draft fails
    closed."""
    member_by_ref = {m.member_ref: m for m in typed.members}
    evidence: List[str] = []
    for ref in member_refs:
        member = member_by_ref.get(ref)
        if member is None:
            raise D10ProjectionError(
                f"query member ref {ref!r} has no typed member object")
        locator = _member_locator(member)
        if locator is None:
            raise D10ProjectionError(
                f"query member {ref!r} has no locatable source locator")
        if locator not in evidence:
            evidence.append(locator)
    evidence.sort()
    if not evidence:
        raise D10ProjectionError(
            "query draft requires a non-empty locatable evidence set")
    return tuple(evidence)


def _record_entry_zh(member: Any, typed: D10TypedInput) -> str:
    """One finite natural record-list entry derived from exact typed member
    facts: subject id plus category/site context.  Never prints raw member
    refs, rule refs or engineering ids."""
    kind_label = _SIGNAL_KIND_LABELS_ZH.get(
        typed.signal_definition.signal_kind, "项目信号")
    subject = member.subject_stable_id
    if member.member_kind == "center_pattern":
        return f"中心模式相关成员（{kind_label}）"
    if subject:
        return f"受试者 {subject}（{kind_label}）"
    return f"已接受成员对象（{kind_label}）"


def build_d10_query_draft(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Optional[D10QueryDraft]:
    """Build the project-level Query draft.

    Returns ``None`` unless the evaluator granted exactly one Query
    (``query_count == 1``) for a positive unit whose typed redundancy
    decision is ``project_delta_present``, whose uncovered set is non-empty
    and whose audience boundary is free of hidden members/sites.  A draft is
    never partial: if any hidden member or hidden site intersects the unit
    audience boundary, no Query is emitted at all (the projected
    ``query_count`` drops to zero) and hidden refs never enter a Query
    object.

    The member list is the complete uncovered projectable member set in the
    decision's canonical order -- never truncated.  The three Chinese
    sentences are rendered ONLY from the frozen typed sentence parts
    (``basis_parts`` / ``finding_parts`` / ``action_parts``); business
    center/subject/record identifiers enter through
    ``source_business_identifier`` parts only.  The Verify-PD template
    (``请核实是否为 PD``) is a typed ``action_pd_verify`` part, shown
    exactly when the typed PD wording state is ``verify_whether_pd``.
    """
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return None
    if unit.query_count != 1:
        return None
    decision = typed.query_decision
    if decision.decision != "project_delta_present":
        return None
    # Hidden members/sites intersecting the unit audience boundary forbid a
    # draft entirely: no partial Query, no hidden refs, projected
    # query_count == 0 (contract sections 12/13, worker_02 contract).
    unit_member_refs = {m.member_ref for m in typed.members}
    unit_site_refs = {m.site_stable_id for m in typed.members
                      if m.site_stable_id}
    hidden_refs = set(typed.visibility_decision.hidden_member_refs)
    hidden_sites = set(typed.visibility_decision.hidden_site_refs)
    if (hidden_refs & unit_member_refs) or (hidden_sites & unit_site_refs):
        return None
    _evaluation, projectable, _hidden = _resolve_visibility_members(
        typed, result)
    if not decision.uncovered_member_refs:
        return None
    projectable_set = set(projectable)
    uncovered = [ref for ref in decision.uncovered_member_refs
                 if ref in projectable_set]
    if not uncovered:
        return None
    member_refs = tuple(uncovered)
    if len(member_refs) > decision.max_query_member_fanout:
        raise D10ProjectionError(
            "query member list exceeds the resolved fanout limit")
    evidence_refs = _query_evidence_refs(typed, member_refs)
    window_kind_zh = _window_kind_zh(typed)
    window_text = _window_text(typed)
    label_zh = _signal_label_zh(typed)

    # --- basis parts ----------------------------------------------------
    basis_parts = (D10AudiencePart(
        "authority_basis",
        f"依据：{label_zh} 按本项目现行有效方案与监察规则，在{window_kind_zh}"
        f"（{window_text}）内需统一核实相关记录与判定；"),)
    basis = "".join(part.text_zh for part in basis_parts)

    # --- finding parts --------------------------------------------------
    count_parts: List[str] = []
    subject_count = len({m.subject_stable_id for m in
                         (m for m in typed.members
                          if m.member_ref in projectable_set)
                         if m.subject_stable_id})
    if subject_count:
        count_parts.append(_fmt(_FROZEN_COUNT_ZH["affected_subjects_zh"],
                                subject_count))
    count_text = "、".join(count_parts) if count_parts else "0"
    unit_key = _DEN_UNIT_BY_KIND.get(typed.denominator.denominator_kind, "")
    unit_zh = _UNIT_LABELS_ZH.get(unit_key, "")
    denom_label = _DENOMINATOR_LABELS_ZH.get(
        typed.denominator.denominator_kind, typed.denominator.denominator_kind)
    denom_text = (
        " ".join(part for part in
                 (denom_label, str(typed.denominator.denominator_value),
                  unit_zh) if part)
        if typed.denominator.denominator_value > 0 or unit_zh else "—")
    coverage_state_zh = _coverage_state_zh(typed)
    coverage_zh = _FROZEN_COUNT_ZH["coverage_zh"]
    member_by_ref = {m.member_ref: m for m in typed.members}
    record_text = "；".join(
        _record_entry_zh(member_by_ref[ref], typed) for ref in member_refs)
    observed_part = D10AudiencePart(
        "observed_finding", f"发现：本项目共 {count_text}，")
    denominator_part = D10AudiencePart(
        "denominator_context",
        f"分母为{denom_text}，{coverage_zh}：{coverage_state_zh}；")
    business_part = D10AudiencePart(
        "source_business_identifier",
        f"涉及记录（{len(member_refs)} 条）：{record_text}；")
    finding_parts: List[D10AudiencePart] = [observed_part, denominator_part]
    if unit.counterevidence_rule_matches > 0:
        finding_parts.append(D10AudiencePart(
            "counterevidence", "存在反证线索，需一并核实；"))
    if typed.evaluation_limits.small_sample or typed.evaluation_limits.limited_evidence:
        finding_parts.append(D10AudiencePart(
            "uncertainty", "样本量或证据充分性受限，需谨慎解读；"))
    finding_parts.append(business_part)
    finding = "".join(part.text_zh for part in finding_parts)

    # --- action parts ---------------------------------------------------
    action_parts: List[D10AudiencePart] = [D10AudiencePart(
        "action_verify",
        f"行动项：请核实上述 {len(member_refs)} 条记录涉及的具体字段与判定，"
        "并补充或更正对应记录；")]
    if decision.pd_wording_state == "verify_whether_pd":
        action_parts.append(D10AudiencePart(
            "action_pd_verify", "请核实是否为 PD。"))
    action = "".join(part.text_zh for part in action_parts)

    basis_refs = (
        typed.signal_definition.signal_definition_id,
        typed.signal_definition.positive_rule_ref,
        typed.analysis_windows[-1].analysis_window_stable_id
        if typed.analysis_windows else "",
        typed.mode_contract.mode_contract_version,
    )
    source_revision_refs = tuple(sorted(
        p.revision_id for p in typed.source_revision_content_pairs))
    unit_stable_core = d10_unit_stable_core(typed)
    content_identity = result.evaluation_content_identity
    redundancy_hash = d10_content_hash({
        "decision": decision.decision,
        "unit_member_set_hash": decision.unit_member_set_hash,
        "coverage_proof_hash": decision.coverage_proof_hash,
        "covered_member_refs": list(decision.covered_member_refs),
        "uncovered_member_refs": list(decision.uncovered_member_refs),
        "max_query_member_fanout": decision.max_query_member_fanout,
        "pd_wording_state": decision.pd_wording_state,
    })

    def _parts_hash(parts: Tuple[D10AudiencePart, ...]) -> List[Dict[str, str]]:
        return [{"part_kind": part.part_kind, "text_zh": part.text_zh}
                for part in parts]

    query_draft_id = d10_content_hash({
        "unit_stable_core": unit_stable_core,
        "evaluation_content_identity": content_identity,
        "member_refs": list(member_refs),
        "basis_parts": _parts_hash(basis_parts),
        "finding_parts": _parts_hash(tuple(finding_parts)),
        "action_parts": _parts_hash(tuple(action_parts)),
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "scope_binding_id": typed.project_scope_binding.scope_binding_id,
        "redundancy_decision_hash": redundancy_hash,
        "pd_wording_state": decision.pd_wording_state,
        "basis_refs": list(basis_refs),
        "source_revision_refs": list(source_revision_refs),
    })
    draft_core = {
        "query_draft_id": query_draft_id,
        "unit_stable_core": unit_stable_core,
        "evaluation_content_identity": content_identity,
        "query_owner": "D10",
        "basis_parts": _parts_hash(basis_parts),
        "finding_parts": _parts_hash(tuple(finding_parts)),
        "action_parts": _parts_hash(tuple(action_parts)),
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "member_refs": list(member_refs),
        "evidence_refs": list(evidence_refs),
        "source_locator_ids": list(evidence_refs),
        "scope_binding_id": typed.project_scope_binding.scope_binding_id,
        "redundancy_decision": decision.decision,
        "redundancy_decision_hash": redundancy_hash,
        "unit_member_set_hash": decision.unit_member_set_hash,
        "coverage_proof_hash": decision.coverage_proof_hash,
        "covered_member_refs": list(decision.covered_member_refs),
        "uncovered_member_refs": list(decision.uncovered_member_refs),
        "max_query_member_fanout": decision.max_query_member_fanout,
        "pd_wording_state": decision.pd_wording_state,
        "basis_refs": list(basis_refs),
        "source_revision_refs": list(source_revision_refs),
    }
    _assert_clean_zh(basis, finding, action)
    _assert_no_structured_ref_in_text(typed, basis, finding, action)
    return D10QueryDraft(
        query_draft_id=query_draft_id,
        unit_stable_core=unit_stable_core,
        evaluation_content_identity=content_identity,
        query_owner="D10",
        basis_parts=basis_parts,
        finding_parts=tuple(finding_parts),
        action_parts=tuple(action_parts),
        basis_sentence=basis,
        finding_sentence=finding,
        action_sentence=action,
        member_refs=member_refs,
        member_count=len(member_refs),
        evidence_refs=evidence_refs,
        source_locator_ids=evidence_refs,
        scope_binding_id=typed.project_scope_binding.scope_binding_id,
        redundancy_decision=decision.decision,
        redundancy_decision_hash=redundancy_hash,
        unit_member_set_hash=decision.unit_member_set_hash,
        coverage_proof_hash=decision.coverage_proof_hash,
        covered_member_refs=decision.covered_member_refs,
        uncovered_member_refs=decision.uncovered_member_refs,
        max_query_member_fanout=decision.max_query_member_fanout,
        pd_wording_state=decision.pd_wording_state,
        basis_refs=basis_refs,
        source_revision_refs=source_revision_refs,
        content_hash=d10_content_hash(draft_core),
    )


def validate_d10_query_draft(
    draft: D10QueryDraft,
    typed: D10TypedInput,
    result: D10RunResult,
) -> Dict[str, Any]:
    """Closed audience validation of a D10 Query draft (contract section 11).

    Checks the exact three sentence patterns, absence of forbidden internal
    tokens, the complete (never truncated) uncovered projectable member
    set, the exact union/disjoint redundancy proof, the frozen PD wording
    rule, the evidence set and the content hash.  The draft must equal a
    fresh authoritative rebuild.
    """
    reasons: List[str] = []
    try:
        _assert_authoritative_result(typed, result)
    except D10ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    sentences = (draft.basis_sentence, draft.finding_sentence,
                 draft.action_sentence)
    if not all(isinstance(s, str) and bool(s) for s in sentences):
        reasons.append("three_sentence_contract")
    for prefix in ("依据：", "发现：", "行动项："):
        if not any(s.startswith(prefix) for s in sentences):
            reasons.append(f"required_sentence_pattern_missing:{prefix}")
    # structured sentence-part contract: closed kinds only, sentences
    # rendered exactly from the typed parts, business identifiers only in
    # the source_business_identifier part kind
    all_parts = list(draft.basis_parts) + list(draft.finding_parts) \
        + list(draft.action_parts)
    for part in all_parts:
        if not isinstance(part, D10AudiencePart):
            reasons.append("part_must_be_d10_audience_part")
            continue
        if part.part_kind not in _SENTENCE_PART_KINDS:
            reasons.append(f"unknown_sentence_part_kind:{part.part_kind}")
        if not isinstance(part.text_zh, str) or not part.text_zh:
            reasons.append("empty_sentence_part_text")
    if "".join(part.text_zh for part in draft.basis_parts) \
            != draft.basis_sentence:
        reasons.append("basis_sentence_not_rendered_from_parts")
    if "".join(part.text_zh for part in draft.finding_parts) \
            != draft.finding_sentence:
        reasons.append("finding_sentence_not_rendered_from_parts")
    if "".join(part.text_zh for part in draft.action_parts) \
            != draft.action_sentence:
        reasons.append("action_sentence_not_rendered_from_parts")
    _member_refs_for_business = {m.member_ref: m for m in typed.members}
    business_ids = set()
    for ref in draft.member_refs:
        member = _member_refs_for_business.get(ref)
        if member is not None and member.subject_stable_id:
            business_ids.add(member.subject_stable_id)
    for part in draft.basis_parts + draft.finding_parts + draft.action_parts:
        if part.part_kind in _BUSINESS_IDENTIFIER_PART_KINDS:
            continue
        if any(bid in part.text_zh for bid in business_ids if bid):
            reasons.append(
                "business_identifier_outside_identifier_part")
            break
    try:
        _assert_clean_zh(*sentences)
        _assert_no_structured_ref_in_text(typed, *sentences)
    except D10ProjectionError as error:
        reasons.append(str(error))
    _evaluation, projectable, hidden = _resolve_visibility_members(
        typed, result)
    projectable_set = set(projectable)
    projectable_uncovered = [
        ref for ref in typed.query_decision.uncovered_member_refs
        if ref in projectable_set]
    if list(draft.member_refs) != projectable_uncovered:
        reasons.append("member_set_not_complete_uncovered_projectable")
    if set(hidden) & set(draft.member_refs):
        reasons.append("hidden_member_in_query")
    if draft.member_count != len(draft.member_refs):
        reasons.append("member_count_mismatch")
    if draft.member_count > typed.query_decision.max_query_member_fanout:
        reasons.append("fanout_exceeded")
    try:
        locatable_evidence = _query_evidence_refs(typed, draft.member_refs)
    except D10ProjectionError as error:
        reasons.append(f"member_not_locatable:{error}")
        locatable_evidence = ()
    if not draft.evidence_refs:
        reasons.append("evidence_must_be_non_empty")
    if list(draft.evidence_refs) != list(locatable_evidence):
        reasons.append("evidence_not_locatable_projectable")
    if draft.source_locator_ids != draft.evidence_refs:
        reasons.append("source_locator_ids_mismatch")
    # exact union/disjoint proof of the redundancy decision
    unit_members = {m.member_ref for m in typed.members}
    covered_set = set(typed.query_decision.covered_member_refs)
    uncovered_set = set(typed.query_decision.uncovered_member_refs)
    if (covered_set | uncovered_set != unit_members
            or covered_set & uncovered_set):
        reasons.append("redundancy_union_disjoint_violation")
    if draft.unit_member_set_hash != typed.query_decision.unit_member_set_hash:
        reasons.append("unit_member_set_hash_mismatch")
    if draft.coverage_proof_hash != typed.query_decision.coverage_proof_hash:
        reasons.append("coverage_proof_hash_mismatch")
    if draft.redundancy_decision != typed.query_decision.decision:
        reasons.append("redundancy_decision_mismatch")
    if (draft.covered_member_refs != typed.query_decision.covered_member_refs
            or draft.uncovered_member_refs
            != typed.query_decision.uncovered_member_refs):
        reasons.append("redundancy_member_sets_mismatch")
    if draft.max_query_member_fanout \
            != typed.query_decision.max_query_member_fanout:
        reasons.append("fanout_policy_mismatch")
    # frozen Verify-PD wording
    pd_expected = typed.query_decision.pd_wording_state == "verify_whether_pd"
    pd_present = "请核实是否为 PD" in draft.action_sentence
    if pd_expected != pd_present:
        reasons.append("pd_wording_rule_mismatch")
    if draft.pd_wording_state != typed.query_decision.pd_wording_state:
        reasons.append("pd_wording_state_mismatch")
    if not draft.draft_only:
        reasons.append("query_must_be_draft_only")
    if draft.query_owner != "D10":
        reasons.append("query_owner_not_d10")
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    expected_basis_refs = (
        typed.signal_definition.signal_definition_id,
        typed.signal_definition.positive_rule_ref,
        window.analysis_window_stable_id if window else "",
        typed.mode_contract.mode_contract_version,
    )
    if draft.basis_refs != expected_basis_refs:
        reasons.append("basis_refs_mismatch")
    expected_revisions = tuple(sorted(
        p.revision_id for p in typed.source_revision_content_pairs))
    if draft.source_revision_refs != expected_revisions:
        reasons.append("source_revision_refs_mismatch")
    if draft.evaluation_content_identity != result.evaluation_content_identity:
        reasons.append("evaluation_content_identity_stale")
    expected_hash = d10_content_hash({
        "query_draft_id": draft.query_draft_id,
        "unit_stable_core": draft.unit_stable_core,
        "evaluation_content_identity": draft.evaluation_content_identity,
        "query_owner": draft.query_owner,
        "basis_parts": [{"part_kind": part.part_kind,
                         "text_zh": part.text_zh}
                        for part in draft.basis_parts],
        "finding_parts": [{"part_kind": part.part_kind,
                           "text_zh": part.text_zh}
                          for part in draft.finding_parts],
        "action_parts": [{"part_kind": part.part_kind,
                          "text_zh": part.text_zh}
                         for part in draft.action_parts],
        "basis_sentence": draft.basis_sentence,
        "finding_sentence": draft.finding_sentence,
        "action_sentence": draft.action_sentence,
        "member_refs": list(draft.member_refs),
        "evidence_refs": list(draft.evidence_refs),
        "source_locator_ids": list(draft.source_locator_ids),
        "scope_binding_id": draft.scope_binding_id,
        "redundancy_decision": draft.redundancy_decision,
        "redundancy_decision_hash": draft.redundancy_decision_hash,
        "unit_member_set_hash": draft.unit_member_set_hash,
        "coverage_proof_hash": draft.coverage_proof_hash,
        "covered_member_refs": list(draft.covered_member_refs),
        "uncovered_member_refs": list(draft.uncovered_member_refs),
        "max_query_member_fanout": draft.max_query_member_fanout,
        "pd_wording_state": draft.pd_wording_state,
        "basis_refs": list(draft.basis_refs),
        "source_revision_refs": list(draft.source_revision_refs),
    })
    if draft.content_hash != expected_hash:
        reasons.append("content_hash_stale")
    try:
        expected_draft = build_d10_query_draft(typed, result)
    except D10ProjectionError as error:
        reasons.append(f"authoritative_query_unavailable:{error}")
        expected_draft = None
    if expected_draft is None or draft != expected_draft:
        reasons.append("query_draft_not_exact_authoritative_projection")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Change section (contract section 14)
# ---------------------------------------------------------------------------


def _derive_clinical_change_kind(ch: Any, result: D10RunResult) -> str:
    """Deterministic clinical-change kind from the typed change decision.

    Mirrors the evaluator's derivation without re-running the evaluator:
    full initial runs and replay runs report ``initial_current``; non-data
    change reports ``not_comparable``; otherwise the typed
    ``data_change_kind`` (or ``continued``) is used.
    """
    if ch is None:
        return "initial_current"
    if ch.execution_basis == "full":
        if (ch.cutoff_advance is not None
                and ch.cutoff_advance.decision_state == "same_window"
                and ch.claimed_cutoff_state is None):
            return "initial_current"
        return ch.data_change_kind or "initial_current"
    if ch.comparison_state == "not_comparable":
        return "not_comparable"
    non_data = _non_data_change_ref_count(ch)
    if non_data > 0:
        return "not_comparable"
    return ch.data_change_kind or "continued"


def _non_data_change_ref_count(ch: Any) -> int:
    if ch is None:
        return 0
    return (len(ch.denominator_change_refs) + len(ch.coverage_change_refs)
            + len(ch.knowledge_change_refs) + len(ch.rule_change_refs)
            + len(ch.mapping_change_refs) + len(ch.model_change_refs)
            + len(ch.method_change_refs) + len(ch.population_change_refs)
            + len(ch.visibility_change_refs) + len(ch.mode_change_refs))


def _change_cause(ch: Any) -> Optional[str]:
    if ch is None:
        return None
    non_data = [key for key, count in (
        ("denominator", len(ch.denominator_change_refs)),
        ("coverage", len(ch.coverage_change_refs)),
        ("knowledge", len(ch.knowledge_change_refs)),
        ("rule", len(ch.rule_change_refs)),
        ("mapping", len(ch.mapping_change_refs)),
        ("model", len(ch.model_change_refs)),
        ("method", len(ch.method_change_refs)),
        ("population", len(ch.population_change_refs)),
        ("visibility", len(ch.visibility_change_refs)),
        ("mode", len(ch.mode_change_refs)),
    ) if count > 0]
    if non_data:
        return non_data[0] if len(non_data) == 1 else "mixed"
    if len(ch.data_change_refs) > 0:
        return "data"
    return None


@dataclass(frozen=True)
class D10ChangeSection:
    """Current/change section of the project projection (contract section
    14).

    ``fresh_full`` is True only for an initial/replay full run whose
    audience narrative is 初始全量 (no new/resolved/… claim); ``analysis
    only`` marks non-data changes whose narrative is 分析口径变化 and never
    a clinical improvement/worsening claim."""

    change_kind: str
    change_cause: Optional[str]
    lineage_relation: str
    analysis_only: bool
    fresh_full: bool
    replay: bool
    change_kind_zh: str
    change_cause_zh: Optional[str]
    lineage_zh: str
    narrative_zh: str


def build_d10_change_section(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ChangeSection:
    """Build the change section narrative from typed change facts."""
    _assert_authoritative_result(typed, result)
    ch = typed.change_decision
    if ch is None:
        return D10ChangeSection(
            change_kind="initial_current", change_cause=None,
            lineage_relation="initial_full_snapshot", analysis_only=False,
            fresh_full=True, replay=False,
            change_kind_zh=_CHANGE_KIND_ZH["initial_current"],
            change_cause_zh=None,
            lineage_zh=_LINEAGE_ZH["initial_full_snapshot"],
            narrative_zh="本次为首次全量快照，仅呈现当前状态，不产生新增或关闭等变化判定。")
    kind = _derive_clinical_change_kind(ch, result)
    cause = _change_cause(ch)
    lineage = ch.lineage_relation or ("initial_full_snapshot"
                                      if ch.execution_basis == "full"
                                      else "continued_from_data_revision")
    replay = bool(ch.execution_basis == "full"
                  and ch.cutoff_advance is not None
                  and ch.cutoff_advance.decision_state == "same_window"
                  and ch.claimed_cutoff_state is None)
    fresh_full = bool(ch.execution_basis == "full" and not replay)
    analysis_only = bool(_non_data_change_ref_count(ch) > 0
                         or ch.comparison_state == "not_comparable")
    kind_zh = _CHANGE_KIND_ZH.get(kind, kind)
    cause_zh = _CHANGE_CAUSE_ZH.get(cause, cause) if cause else None
    lineage_zh = _LINEAGE_ZH.get(lineage, lineage)
    if replay or fresh_full:
        narrative = "本次为初始或同窗全量快照，仅呈现当前状态，不产生新增或关闭等变化判定。"
    elif analysis_only:
        narrative = "分析口径变化，前后不可直接比较。"
    elif kind == "continued":
        narrative = ("本版相对上一可比版本为持续状态，变化原因为"
                     f"{cause_zh or '数据变化'}。")
    elif kind == "resolved":
        narrative = "本版相对上一可比版本为关闭状态，变化原因为数据变化。"
    elif kind == "reopened":
        narrative = "本版相对上一可比版本为重开状态，变化原因为数据变化。"
    elif kind == "new":
        narrative = f"本版相对上一可比版本为新增状态，变化原因为{cause_zh or '数据变化'}。"
    elif kind in ("upgraded", "downgraded"):
        narrative = (f"本版相对上一可比版本为{kind_zh}状态，变化原因为"
                     f"{cause_zh or '数据变化'}。")
    else:
        narrative = f"本版状态为{kind_zh}，变化原因为{cause_zh or '数据变化'}。"
    _assert_clean_zh(kind_zh, cause_zh or "", lineage_zh, narrative)
    _assert_no_structured_ref_in_text(typed, narrative)
    return D10ChangeSection(
        change_kind=kind,
        change_cause=cause,
        lineage_relation=lineage,
        analysis_only=analysis_only,
        fresh_full=fresh_full,
        replay=replay,
        change_kind_zh=kind_zh,
        change_cause_zh=cause_zh,
        lineage_zh=lineage_zh,
        narrative_zh=narrative,
    )


# ---------------------------------------------------------------------------
# Center distribution and trend/warning surfaces (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10CenterPatternRow:
    """One center column of the center distribution surface.

    Absolute counts and an explicit-denominator rate per projectable site;
    the rate column is present only under the permitted rate state with no
    hidden members/sites.  Small-sample / late-start / follow-up warnings
    are carried as typed warning codes, never as a quality verdict."""

    site_ref: str
    site_activation_state: str
    member_count: int
    affected_subject_count: int
    denominator_value: Optional[int]
    rate_zh: Optional[str]
    warning_codes: Tuple[str, ...]
    coverage_state: str


def _site_denominator_value(typed: D10TypedInput, site: str) -> Optional[int]:
    ledger = typed.site_ledger
    if ledger.site_ref != site:
        return None
    kind = typed.denominator.denominator_kind
    if kind == "treated_subjects":
        return len(ledger.treated_subject_refs)
    if kind == "enrolled_subjects":
        return len(ledger.eligible_subject_refs)
    if kind == "safety_evaluable_subjects":
        return len(ledger.evaluable_subject_refs)
    if kind == "efficacy_evaluable_subjects":
        return len(ledger.evaluable_subject_refs)
    return None


def build_d10_center_distribution(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10CenterPatternRow, ...]:
    """Center distribution surface: absolute counts and explicit
    denominator rates per projectable site.  No punitive ranking: rows are
    ordered by stable site identity."""
    _assert_authoritative_result(typed, result)
    _eval_sites, proj_sites, _hidden_sites = _resolve_visibility_sites(typed, result)
    if not proj_sites:
        return ()
    visibility = typed.visibility_decision
    withheld = (len(typed.visibility_decision.hidden_member_refs) > 0
                or len(typed.visibility_decision.hidden_site_refs) > 0)
    pair_visible = _pair_visible_members(typed, result)
    members_by_site: Dict[str, List[Any]] = {}
    for member in pair_visible:
        members_by_site.setdefault(member.site_stable_id, []).append(member)
    warning_codes = [code for code in typed.comparison_gate.reason_codes
                     if not code.startswith("comparison_")
                     and not code.startswith("window_pair_")]
    precision = max(0, typed.numeric_policy.display_precision)
    rows: List[D10CenterPatternRow] = []
    for site in sorted(proj_sites):
        members = members_by_site.get(site, [])
        subjects = len({m.subject_stable_id for m in members
                        if m.subject_stable_id})
        den_value = _site_denominator_value(typed, site)
        rate_zh: Optional[str] = None
        if (visibility.rate_projection_state == "permitted" and not withheld
                and den_value and den_value > 0):
            percent = _half_up(100.0 * subjects / den_value, precision)
            rate_zh = f"{subjects}/{den_value}（{percent:.{precision}f}%）"
        rows.append(D10CenterPatternRow(
            site_ref=site,
            site_activation_state=typed.site_ledger.site_activation_state
            if typed.site_ledger.site_ref == site else "active",
            member_count=len(members),
            affected_subject_count=subjects,
            denominator_value=den_value,
            rate_zh=rate_zh,
            warning_codes=tuple(warning_codes),
            coverage_state=_coverage_state(typed),
        ))
    return tuple(rows)


@dataclass(frozen=True)
class D10TrendSurface:
    """Time/safety/efficacy trend surface (contract sections 8/12).

    A descriptive-monitoring surface only: analysis set, window, denominator,
    method and uncertainty are carried in typed engineering fields; the
    audience narrative is the frozen descriptive-monitoring phrase and never
    a confirmatory or benefit-risk verdict."""

    trend_surface_present: bool
    signal_kind: str
    evaluation_window_instance_ref: str
    window_text_zh: str
    analysis_population_ref: Optional[str]
    denominator_kind: str
    denominator_value: int
    estimate_kind: Optional[str]
    exposure_definition_ref: Optional[str]
    coding_dictionary_ref: Optional[str]
    severity_scale_ref: Optional[str]
    endpoint_definition_ref: Optional[str]
    estimand_ref: Optional[str]
    missing_data_rule_ref: Optional[str]
    intercurrent_event_rule_ref: Optional[str]
    treatment_role_authority_ref: Optional[str]
    small_sample: bool
    limited_evidence: bool
    limited_reason: Optional[str]
    trend_note_zh: str


def build_d10_trend_surface(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10TrendSurface:
    """Build the time/safety/efficacy trend surface for trend signal
    kinds."""
    _assert_authoritative_result(typed, result)
    kind = typed.signal_definition.signal_kind
    safety = typed.safety_context
    efficacy = typed.efficacy_context
    limits = typed.evaluation_limits
    trend_present = kind in ("project_time_trend", "project_safety_trend",
                             "project_efficacy_trend")
    estimate = None
    if result.unit is not None:
        estimate = result.unit.estimate_kind
    elif efficacy is not None:
        estimate = efficacy.estimate_kind
    note = "描述性监测结果，仅供项目内复核；不构成正式确证或获益-风险结论。"
    if not trend_present:
        note = ""
    _assert_clean_zh(note)
    return D10TrendSurface(
        trend_surface_present=trend_present,
        signal_kind=kind,
        evaluation_window_instance_ref=_evaluation_window_instance_ref(typed),
        window_text_zh=_window_text(typed),
        analysis_population_ref=(typed.analysis_population.analysis_population_ref
                                 if typed.analysis_population.present else None),
        denominator_kind=typed.denominator.denominator_kind,
        denominator_value=typed.denominator.denominator_value,
        estimate_kind=estimate,
        exposure_definition_ref=safety.exposure_definition_ref if safety else None,
        coding_dictionary_ref=safety.coding_dictionary_ref if safety else None,
        severity_scale_ref=safety.severity_scale_ref if safety else None,
        endpoint_definition_ref=(efficacy.endpoint_definition_ref
                                 if efficacy else None),
        estimand_ref=efficacy.estimand_ref if efficacy else None,
        missing_data_rule_ref=efficacy.missing_data_rule_ref if efficacy else None,
        intercurrent_event_rule_ref=(efficacy.intercurrent_event_rule_ref
                                     if efficacy else None),
        treatment_role_authority_ref=(efficacy.treatment_role_authority_ref
                                      if efficacy else None),
        small_sample=limits.small_sample,
        limited_evidence=limits.limited_evidence,
        limited_reason=limits.limited_reason,
        trend_note_zh=note,
    )


@dataclass(frozen=True)
class D10WarningMarker:
    """One audience-safe warning marker.

    ``warning_zh`` is native Chinese; ``reason_code`` is a typed engineering
    field (never rendered to the audience)."""

    reason_code: str
    warning_zh: str


def build_d10_warnings(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10WarningMarker, ...]:
    """Audience-safe warning markers from typed facts (contract section 12).

    Small-sample / short-follow-up / case-mix / method warnings are
    descriptive and never a center quality verdict; no punitive ranking and
    no black-box score is produced."""
    _assert_authoritative_result(typed, result)
    warnings: List[D10WarningMarker] = []
    seen: set = set()
    for code in typed.comparison_gate.reason_codes:
        if code.startswith("comparison_") or code.startswith("window_pair_"):
            continue
        if code in seen:
            continue
        seen.add(code)
        text = _CODED_WARNING_ZH.get(code)
        if text is None:
            continue
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(reason_code=code, warning_zh=text))
    limits = typed.evaluation_limits
    if limits.small_sample:
        text = "样本量较小，相关比例需谨慎解读。"
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code="small_sample", warning_zh=text))
    if limits.limited_evidence:
        detail = limits.limited_reason or ""
        text = (f"证据有限（{detail}），需结合更多信息复核。"
                if detail else "证据有限，需结合更多信息复核。")
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code="limited_evidence", warning_zh=text))
    rate_state = typed.visibility_decision.rate_projection_state
    if rate_state in ("suppressed", "qualified"):
        text = _RATE_STATE_ZH[rate_state]
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code=rate_state, warning_zh=text))
    return tuple(warnings)


# ---------------------------------------------------------------------------
# Replay-stable R2 lifecycle handoff (contract section 10)
# ---------------------------------------------------------------------------


def _measure_ledger_ref(typed: D10TypedInput,
                        result: D10RunResult) -> str:
    unit = result.unit
    return d10_content_hash({
        "denominator_kind": typed.denominator.denominator_kind,
        "denominator_value": typed.denominator.denominator_value,
        "denominator_state": typed.denominator.denominator_state,
        "individual_risk_count": unit.individual_risk_count if unit else 0,
        "affected_subject_count": unit.affected_subject_count if unit else 0,
        "event_or_outcome_count": unit.event_or_outcome_count if unit else 0,
        "center_pattern_count": unit.center_pattern_count if unit else 0,
        "affected_site_count": unit.affected_site_count if unit else 0,
        "numerator_member_count": unit.numerator_member_count if unit else 0,
    })


def _completeness_decision_ref(typed: D10TypedInput,
                               result: D10RunResult) -> str:
    return d10_content_hash({
        "disposition_or_gate": result.disposition_or_gate,
        "primary_reason": result.primary_reason,
        "coverage_state": _coverage_state(typed),
        "denominator_state": typed.denominator.denominator_state,
    })


def _no_auto_close_reasons(typed: D10TypedInput,
                           result: D10RunResult) -> Tuple[str, ...]:
    """Closed no-auto-close reasons (contract section 10): high-priority
    members, carry-forward, broken coverage and hidden planes never propose
    closure."""
    reasons: List[str] = []
    members = typed.members
    if any(getattr(m, "monitoring_priority", None) == "high"
           for m in members):
        reasons.append("存在高监察优先级成员")
    if typed.change_decision is not None \
            and typed.change_decision.carry_forward_state == "active":
        reasons.append("本次可评价范围不完整，需维持进行中")
    if _coverage_state(typed) != "complete":
        reasons.append("覆盖不完整，需维持进行中")
    visibility = typed.visibility_decision
    if visibility.hidden_member_refs or visibility.hidden_site_refs:
        reasons.append("存在受限可见成员或中心，需维持进行中")
    return tuple(reasons)


def _max_member_priority(typed: D10TypedInput) -> Optional[str]:
    priorities = [m.monitoring_priority for m in typed.members
                  if getattr(m, "monitoring_priority", None)]
    if "high" in priorities:
        return "high"
    if "medium" in priorities:
        return "medium"
    return None


def _change_decision_hash(typed: D10TypedInput) -> str:
    ch = typed.change_decision
    if ch is None:
        return d10_content_hash({
            "execution_basis": "full", "comparison_state": "initial_full",
        })
    ca = ch.cutoff_advance
    return d10_content_hash({
        "execution_basis": ch.execution_basis,
        "comparison_state": ch.comparison_state,
        "prior_snapshot_ref_or_none": ch.prior_snapshot_ref_or_none,
        "data_change_refs": sorted(ch.data_change_refs),
        "denominator_change_refs": sorted(ch.denominator_change_refs),
        "coverage_change_refs": sorted(ch.coverage_change_refs),
        "knowledge_change_refs": sorted(ch.knowledge_change_refs),
        "rule_change_refs": sorted(ch.rule_change_refs),
        "mapping_change_refs": sorted(ch.mapping_change_refs),
        "model_change_refs": sorted(ch.model_change_refs),
        "method_change_refs": sorted(ch.method_change_refs),
        "population_change_refs": sorted(ch.population_change_refs),
        "visibility_change_refs": sorted(ch.visibility_change_refs),
        "mode_change_refs": sorted(ch.mode_change_refs),
        "data_change_kind": ch.data_change_kind,
        "lineage_relation": ch.lineage_relation,
        "r2_action": ch.r2_action,
        "r2_prior_ref_or_none": ch.r2_prior_ref_or_none,
        "carry_forward_state": ch.carry_forward_state,
        "cutoff_advance": {
            "decision_state": ca.decision_state if ca else None,
            "strict_advance_predicate_passed":
                ca.strict_advance_predicate_passed if ca else False,
            "policy_semantic_hash_equal":
                ca.policy_semantic_hash_equal if ca else False,
            "prior_boundary_value": ca.prior_boundary_value if ca else None,
            "current_boundary_value": ca.current_boundary_value if ca else None,
        },
    })


@dataclass(frozen=True)
class D10R2RiskHandoff:
    """Replay-stable R2 lifecycle handoff (contract section 10).

    ``handoff_id`` and ``idempotency_key`` are equal and derive from the
    public D10 risk identity, the current evaluation content identity, the
    action, the prior instance ref, the lineage relation and the change/
    completeness hashes -- never from opaque run/snapshot ids.

    Action constraints (closed): ``create`` is the only action without a
    prior ref and requires a create-legal lineage; every other action
    requires BOTH the prior instance ref and a compatible lineage.  The
    handoff is emitted for positive units only and never proposes closure
    for high-priority/carry-forward/coverage-restricted states.  No R2
    lifecycle object is created or updated -- the handoff is a contract
    emission only.
    """

    handoff_id: str
    idempotency_key: str
    public_d10_risk_identity: Dict[str, Any]
    stable_core_ref: str
    current_evaluation_content_ref: str
    run_snapshot_audit_refs: Tuple[str, ...]
    prior_risk_instance_ref: Optional[str]
    action: str
    lineage_relation: str
    change_decision_ref: str
    completeness_decision_ref: str
    member_refs: Tuple[str, ...]
    measure_ledger_ref: str
    monitoring_priority: Optional[str]
    no_auto_close_reasons: Tuple[str, ...]


def _derive_r2_handoff_action(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[Optional[str], str, Optional[str]]:
    """Derive ``(action, lineage_relation, prior_risk_instance_ref)`` for a
    positive unit (contract section 10).

    Every positive D10 unit emits an R2 handoff:

    * a declared ``r2_action`` on the typed change decision is authoritative
      (its consistency with the prior ref and lineage was already validated
      by the deterministic evaluator; any contradiction is an integrity
      gate);
    * an initial-full (or data-revision / strict cutoff-advance) positive
      with no prior R2 risk and no explicit transition derives ``create``
      with the create-legal lineage --- ``create`` is never mapped to a
      ``新增`` R5 display and never invents a prior;
    * a positive unit with a prior instance and no declared action derives
      ``continue`` (the signal persists on the same public identity).

    The derivation reads only the authoritative result and typed facts; it
    never re-runs the medical evaluator.
    """
    ch = typed.change_decision
    declared = ch.r2_action if ch else ""
    prior = ch.r2_prior_ref_or_none if ch else None
    lineage = ch.lineage_relation if ch else ""
    if declared:
        return declared, lineage, prior
    if ch is None or (prior is None
                      and _non_data_change_ref_count(ch) == 0
                      and ch.comparison_state != "not_comparable"):
        lineage = lineage or ("initial_full_snapshot"
                              if ch is None or ch.execution_basis == "full"
                              else "continued_from_data_revision")
        return "create", lineage, None
    lineage = lineage or "continued_from_data_revision"
    return "continue", lineage, prior


def build_d10_r2_handoff(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Optional[D10R2RiskHandoff]:
    """Build the R2 lifecycle handoff for a positive unit.

    Every positive D10 unit emits exactly one handoff (contract section 10).
    The action is derived deterministically: a declared ``r2_action`` is
    authoritative, otherwise an initial-full positive derives ``create``
    and a prior-bearing positive derives ``continue``.  The closed action
    x lineage x prior matrix is re-checked from the typed facts and fails
    closed on any contradiction (the evaluator already rejected them at
    evaluation time).  Non-positive runs and all gates emit no handoff."""
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return None
    action, lineage, prior = _derive_r2_handoff_action(typed, result)
    ch = typed.change_decision
    if action != "create":
        if prior is None:
            raise D10ProjectionError(
                f"non-create action {action!r} without a prior instance ref")
    else:
        if prior is not None:
            raise D10ProjectionError(
                "create action with a prior instance ref")
        if lineage not in (
                "initial_full_snapshot",
                "continued_from_data_revision",
                "continued_from_cutoff_advance"):
            raise D10ProjectionError(
                f"create action with create-illegal lineage {lineage!r}")
        if (ch is not None
                and (_non_data_change_ref_count(ch) > 0
                     or ch.comparison_state == "not_comparable")):
            raise D10ProjectionError(
                "create action with non-data change or non-comparable state")
        if lineage == "continued_from_cutoff_advance":
            ca = ch.cutoff_advance
            if ca is None or ca.decision_state != "strict_advance" \
                    or not ca.strict_advance_predicate_passed \
                    or not ca.policy_semantic_hash_equal:
                raise D10ProjectionError(
                    "cutoff-advance create without a strictly advanced "
                    "derived cutoff decision")
    if action == "supersede":
        if not (lineage.startswith("superseded_by_")
                or lineage == "coverage_regressed"):
            raise D10ProjectionError(
                f"supersede action with non-superseded lineage {lineage!r}")
    if action in ("continue", "update", "propose_close", "reopen"):
        if lineage not in ("continued_from_data_revision",
                           "continued_from_cutoff_advance", "none", ""):
            raise D10ProjectionError(
                f"{action} action with incompatible lineage {lineage!r}")
    public_identity = d10_public_risk_identity(typed)
    evaluation_content = result.evaluation_content_identity
    member_refs = tuple(sorted(
        set(m.member_ref for m in typed.members)))
    measure_ledger_ref = _measure_ledger_ref(typed, result)
    completeness_ref = _completeness_decision_ref(typed, result)
    change_ref = _change_decision_hash(typed)
    no_auto_close = _no_auto_close_reasons(typed, result)
    monitoring_priority = _max_member_priority(typed)
    handoff_id = d10_content_hash({
        "public_d10_risk_identity": public_identity,
        "evaluation_content_identity": evaluation_content,
        "action": action,
        "lineage_relation": lineage,
        "prior_risk_instance_ref": prior,
        "change_decision_hash": change_ref,
        "completeness_decision_hash": completeness_ref,
    })
    return D10R2RiskHandoff(
        handoff_id=handoff_id,
        idempotency_key=handoff_id,
        public_d10_risk_identity=public_identity,
        stable_core_ref=unit.stable_core_ref,
        current_evaluation_content_ref=evaluation_content,
        run_snapshot_audit_refs=(typed.run_ref, typed.snapshot_ref),
        prior_risk_instance_ref=prior,
        action=action,
        lineage_relation=lineage,
        change_decision_ref=change_ref,
        completeness_decision_ref=completeness_ref,
        member_refs=member_refs,
        measure_ledger_ref=measure_ledger_ref,
        monitoring_priority=monitoring_priority,
        no_auto_close_reasons=no_auto_close,
    )


def validate_d10_r2_handoff(
    handoff: D10R2RiskHandoff,
    typed: D10TypedInput,
    result: D10RunResult,
) -> Dict[str, Any]:
    """Closed validation of a D10 R2 handoff (contract section 10)."""
    reasons: List[str] = []
    try:
        _assert_authoritative_result(typed, result)
    except D10ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    if result.unit is None or result.unit.l1_disposition != "positive":
        reasons.append("handoff_requires_positive_unit")
    expected_action, expected_lineage, expected_prior = \
        _derive_r2_handoff_action(typed, result)
    if handoff.action != expected_action:
        reasons.append(f"action_mismatch:{handoff.action}")
    if handoff.lineage_relation != expected_lineage:
        reasons.append("lineage_relation_mismatch")
    if handoff.prior_risk_instance_ref != expected_prior:
        reasons.append("prior_ref_mismatch")
    if handoff.action not in (
            "create", "continue", "update", "propose_close", "reopen",
            "supersede"):
        reasons.append(f"action_not_d10_vocabulary:{handoff.action}")
    if handoff.action == "create":
        if handoff.prior_risk_instance_ref is not None:
            reasons.append("create_with_prior_ref")
        if expected_lineage not in (
                "initial_full_snapshot", "continued_from_data_revision",
                "continued_from_cutoff_advance"):
            reasons.append("create_with_illegal_lineage")
    else:
        if handoff.prior_risk_instance_ref is None:
            reasons.append("non_create_without_prior_ref")
        if handoff.action == "supersede":
            if not expected_lineage.startswith("superseded_by_") \
                    and expected_lineage != "coverage_regressed":
                reasons.append("supersede_without_superseded_lineage")
        if handoff.action in ("continue", "update", "propose_close",
                              "reopen"):
            if expected_lineage not in (
                    "continued_from_data_revision",
                    "continued_from_cutoff_advance", "none", ""):
                reasons.append("incompatible_continuation_lineage")
    expected_handoff_id = d10_content_hash({
        "public_d10_risk_identity": d10_public_risk_identity(typed),
        "evaluation_content_identity": result.evaluation_content_identity,
        "action": handoff.action,
        "lineage_relation": handoff.lineage_relation,
        "prior_risk_instance_ref": handoff.prior_risk_instance_ref,
        "change_decision_hash": _change_decision_hash(typed),
        "completeness_decision_hash": _completeness_decision_ref(typed, result),
    })
    if handoff.handoff_id != expected_handoff_id:
        reasons.append("handoff_id_stale")
    if handoff.idempotency_key != handoff.handoff_id:
        reasons.append("idempotency_key_mismatch")
    if handoff.current_evaluation_content_ref \
            != result.evaluation_content_identity:
        reasons.append("evaluation_content_identity_stale")
    if handoff.public_d10_risk_identity != d10_public_risk_identity(typed):
        reasons.append("public_risk_identity_stale")
    if handoff.stable_core_ref != (result.unit.stable_core_ref
                                   if result.unit is not None else ""):
        reasons.append("stable_core_stale")
    if handoff.change_decision_ref != _change_decision_hash(typed):
        reasons.append("change_decision_hash_stale")
    if handoff.completeness_decision_ref \
            != _completeness_decision_ref(typed, result):
        reasons.append("completeness_decision_hash_stale")
    if handoff.run_snapshot_audit_refs != (typed.run_ref, typed.snapshot_ref):
        reasons.append("run_snapshot_audit_refs_mismatch")
    expected_member_refs = tuple(sorted(
        set(m.member_ref for m in typed.members)))
    if handoff.member_refs != expected_member_refs:
        reasons.append("member_refs_mismatch")
    if handoff.measure_ledger_ref != _measure_ledger_ref(typed, result):
        reasons.append("measure_ledger_ref_mismatch")
    if handoff.monitoring_priority != _max_member_priority(typed):
        reasons.append("monitoring_priority_mismatch")
    if handoff.no_auto_close_reasons != _no_auto_close_reasons(typed, result):
        reasons.append("no_auto_close_reasons_mismatch")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Project projection and bundle (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectProjection:
    """The complete project projection for one run (contract section 12).

    Immutable and renderer-neutral: change section, center distribution,
    trend surface, warnings, hotspot refs, count-surface ref, deep links,
    Query draft and R2 handoff refs are bound to one projection version and
    content hash.  R5 may render this object; it must never recompute the
    underlying numbers."""

    projection_id: str
    projection_version_ref: str
    change_section: D10ChangeSection
    center_distribution: Tuple[D10CenterPatternRow, ...]
    trend_surface: D10TrendSurface
    warning_markers: Tuple[D10WarningMarker, ...]
    risk_marker_ref: Optional[str]
    hotspot_site_refs: Tuple[str, ...]
    hotspot_subject_refs: Tuple[str, ...]
    count_surface_ref: str
    coverage_refs: Tuple[str, ...]
    deep_link_target_refs: Tuple[str, ...]
    query_draft_ref: Optional[str]
    r2_handoff_ref: Optional[str]
    audience_text_ref: str
    projection_content_hash: str


def build_d10_project_projection(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectProjection:
    """Build the complete project projection (contract section 12)."""
    _assert_authoritative_result(typed, result)
    version = build_d10_projection_version(typed, result)
    counts = build_d10_count_surface(typed, result)
    change = build_d10_change_section(typed, result)
    centers = build_d10_center_distribution(typed, result)
    trend = build_d10_trend_surface(typed, result)
    warnings = build_d10_warnings(typed, result)
    hotspots = build_d10_hotspots(typed, result)
    links = build_d10_deep_links(typed, result)
    query = build_d10_query_draft(typed, result)
    handoff = build_d10_r2_handoff(typed, result)
    risk = build_d10_risk_marker(typed, result)
    coverage_refs = tuple(sorted(set(
        locator for c in typed.coverage for locator in c.coverage_locator_ids)))
    count_surface_ref = d10_content_hash({
        "evaluation_window_instance_ref": counts.evaluation_window_instance_ref,
        "individual_risk_count": counts.individual_risk_count,
        "affected_subject_count": counts.affected_subject_count,
        "event_or_outcome_count": counts.event_or_outcome_count,
        "center_pattern_count": counts.center_pattern_count,
        "affected_site_count": counts.affected_site_count,
        "project_signal_count": counts.project_signal_count,
        "clue_count": counts.clue_count,
        "query_count": counts.query_count,
        "hidden_member_count": counts.hidden_member_count,
        "hidden_site_count": counts.hidden_site_count,
    })
    projection_core = {
        "change_kind": change.change_kind,
        "center_site_refs": [row.site_ref for row in centers],
        "trend_surface_present": trend.trend_surface_present,
        "warning_refs": [w.reason_code for w in warnings],
        "risk_marker_ref": risk.marker_id if risk else None,
        "hotspot_refs": [h.projection_id for h in hotspots],
        "count_surface_ref": count_surface_ref,
        "coverage_refs": list(coverage_refs),
        "deep_link_refs": [link.link_id for link in links],
        "query_draft_id": query.query_draft_id if query else None,
        "r2_handoff_id": handoff.handoff_id if handoff else None,
        "audience_text_ref": typed.audience_text.audience_contract_id,
        "algorithm_version": _ALGORITHM_VERSION,
    }
    projection_content_hash = d10_content_hash(projection_core)
    projection_id = d10_content_hash({
        "projection_version_id": version.projection_version_id,
        "projection_content_hash": projection_content_hash,
    })
    return D10ProjectProjection(
        projection_id=projection_id,
        projection_version_ref=version.projection_version_id,
        change_section=change,
        center_distribution=centers,
        trend_surface=trend,
        warning_markers=warnings,
        risk_marker_ref=risk.marker_id if risk else None,
        hotspot_site_refs=tuple(sorted({
            h.site_ref for h in hotspots})),
        hotspot_subject_refs=tuple(sorted({
            h.subject_ref for h in hotspots})),
        count_surface_ref=count_surface_ref,
        coverage_refs=coverage_refs,
        deep_link_target_refs=tuple(link.link_id for link in links),
        query_draft_ref=query.query_draft_id if query else None,
        r2_handoff_ref=handoff.handoff_id if handoff else None,
        audience_text_ref=typed.audience_text.audience_contract_id,
        projection_content_hash=projection_content_hash,
    )


def validate_d10_project_projection(
    projection: D10ProjectProjection,
    typed: D10TypedInput,
    result: D10RunResult,
) -> Dict[str, Any]:
    """Closed authoritative rebuild of the project projection: the
    submitted object must equal a fresh rebuild of every leaf surface, so a
    re-signed tampered projection cannot pass."""
    reasons: List[str] = []
    try:
        expected = build_d10_project_projection(typed, result)
    except D10ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    if projection != expected:
        reasons.append("project_projection_not_exact_authoritative_rebuild")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectionBundle:
    """Complete renderer-neutral projection of one run."""

    audience: D10AudienceProjection
    counts: D10ProjectionCountSurface
    version: D10ProjectionVersion
    change_section: D10ChangeSection
    center_distribution: Tuple[D10CenterPatternRow, ...]
    trend_surface: D10TrendSurface
    warning_markers: Tuple[D10WarningMarker, ...]
    risk_marker: Optional[D10RiskMarker]
    hotspots: Tuple[D10HotspotProjection, ...]
    deep_links: Tuple[D10DeepLinkTarget, ...]
    query_draft: Optional[D10QueryDraft]
    r2_handoff: Optional[D10R2RiskHandoff]
    project_projection: D10ProjectProjection


def project_d10_run(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectionBundle:
    """Project a validated typed run onto all renderer-neutral surfaces."""
    return D10ProjectionBundle(
        audience=build_d10_audience_projection(typed, result),
        counts=build_d10_count_surface(typed, result),
        version=build_d10_projection_version(typed, result),
        change_section=build_d10_change_section(typed, result),
        center_distribution=build_d10_center_distribution(typed, result),
        trend_surface=build_d10_trend_surface(typed, result),
        warning_markers=build_d10_warnings(typed, result),
        risk_marker=build_d10_risk_marker(typed, result),
        hotspots=build_d10_hotspots(typed, result),
        deep_links=build_d10_deep_links(typed, result),
        query_draft=build_d10_query_draft(typed, result),
        r2_handoff=build_d10_r2_handoff(typed, result),
        project_projection=build_d10_project_projection(typed, result),
    )
