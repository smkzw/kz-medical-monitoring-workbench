"""Native-Chinese three-sentence Query draft projection."""

from .d10_core import *
from .d10_identity import *

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


__all__ = [name for name in globals() if not name.startswith("__")]
