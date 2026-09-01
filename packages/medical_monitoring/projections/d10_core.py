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


__all__ = [name for name in globals() if not name.startswith("__")]
