"""R4-D08 renderer-neutral audience projection, risk marker and Query draft.

Consumes the accepted typed bundle and the evaluator's
:class:`~mm_r4.d08_evaluator.D08RunResult` (never the frozen oracle/registry/
manifest) and produces:

* :func:`project_d08_audience` -- the renderer-neutral audience projection:
  projectable/evaluation node sets, audience anchor, hidden-node count,
  Query/Journey/risk presence, resolvable source jumps and disclosure
  safety (blinded/forbidden nodes never leak into the audience payload);
* :func:`d08_unit_id_hash` -- the frozen unit identity (contract section
  4.3): stable core plus lineage/algorithm version, with run/snapshot/
  revision/computed dates excluded;
* :func:`build_d08_risk_marker` -- the D08 ``PublicR4RiskIdentity`` risk
  marker (domain ``D08_cross_domain_logic``, public identity version
  ``d08_public_v1``) with affected domains and source locators;
* :func:`build_d08_query_draft` -- a natural-Chinese three-part Query draft
  (``依据`` / ``发现`` / ``行动项``) for D08-owned positives that references
  only projectable records; PD wording is never produced (D04 owns it);
* :func:`validate_query_draft` -- closed audience validation: exact three
  patterns, no forbidden internal tokens, evidence/source locators within
  the projectable set, content hash and scope binding.

Boundaries honoured (v0.6 sections 4.3/9):

* Query drafts and risk markers exist only for D08-owned positive units
  (``query_owner/risk_owner = D08``); negative/boundary/not-applicable/
  not-evaluable/integrity and consume-only runs never get them;
* the audience payload only exposes projectable evidence; evaluation can
  exceed projection, and omission never changes the internal join result;
* no phantom nodes are ever created: a missing counterpart is phrased as
  "未见对应记录/数据更新待核实", never as a hidden record placeholder.

All data is synthetic and offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..risks.d08_contracts import (
    D08_DOMAIN_ID,
    D08_PUBLIC_IDENTITY_VERSION,
    D08TypedInput,
    d08_content_hash,
    d08_content_hash_prefixed,
)
from ..risks.d08_evaluator import (
    D08RunResult,
    D08SourceJumpTarget,
    D08UnitResult,
)


# ---------------------------------------------------------------------------
# Unit stable identity (contract section 4.3)
# ---------------------------------------------------------------------------


def _unit_stable_core(unit: D08UnitResult) -> str:
    """Version-independent unit stable core: classifier/grain/rule/slot/
    signal (excludes lineage, version, computed dates, run/snapshot/
    revision)."""
    return "|".join(filter(None, [
        unit.relation_rule_id,
        unit.unit_kind,
        unit.anchor_stable_identity or unit.slot_kind or unit.signal_type,
        unit.gate_signal_type or unit.signal_type,
    ]))


def d08_unit_id_hash(
    typed: D08TypedInput,
    unit: D08UnitResult,
    anchor_or_rel_instance: Optional[str] = None,
) -> str:
    """Frozen ``unit_id`` (contract section 4.3): stable core plus lineage
    and algorithm version; computed dates/intervals/precision never enter
    the temporal-window identity."""
    scope = typed.scope_binding
    rule = typed.relation_rules[0] if typed.relation_rules else None
    window = rule.applicability_window if rule else None
    return d08_content_hash({
        "project_id": scope.project_ref if scope else "",
        "domain_id": D08_DOMAIN_ID,
        "scope_type": "subject",
        "scope_key": scope.subject_ref if scope else "",
        "normalized_concept_or_rule_item": (
            unit.relation_rule_id,
            unit.unit_kind,
            anchor_or_rel_instance,
            unit.slot_kind,
            unit.signal_type,
        ),
        "temporal_window": (
            window.window_kind if window else None,
            rule.rule_id if window else None,
        ),
        "rule_or_knowledge_lineage": (
            rule.rule_hash if rule else "",
        ),
        "unit_algorithm_version": (
            rule.algorithm_version if rule else "d08_unit_v1"),
    })


# ---------------------------------------------------------------------------
# Audience projection (contract section 9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D08AudienceProjection:
    """Renderer-neutral audience projection for one run.

    ``audience_source_nodes`` are the projectable record node ids that the
    Query/Journey payload may reference; the projection never invents
    nodes.  ``relation_edges`` lists only edges whose both endpoints are
    projectable (each endpoint jumps to its source record).
    """

    projectable_node_set: Tuple[str, ...]
    evaluation_node_set: Tuple[str, ...]
    hidden_node_count: int
    audience_anchor: Optional[str]
    audience_payload_present: bool
    query_present: bool
    journey_marker_present: bool
    risk_present: bool
    audience_source_nodes: Tuple[str, ...]
    relation_edges: Tuple[Tuple[str, str, str], ...]
    source_jump_target_pairs: Tuple[D08SourceJumpTarget, ...]
    disclosure_leak_present: bool
    audience_lexicon_ref: Optional[str]


def project_d08_audience(
    typed: D08TypedInput,
    result: D08RunResult,
) -> D08AudienceProjection:
    """Project the evaluation onto the audience plane (contract section 9).

    Only both-endpoints-projectable observed edges become relation lines;
    hidden (blinded/forbidden) nodes are omitted from every payload but the
    internal evaluation/join result is untouched.  A single blocked edge
    never clears the Subject Journey's other visible markers.
    """
    projectable = set(result.projectable_node_set)
    edges: List[Tuple[str, str, str]] = []
    records_by_stable: Dict[str, List[str]] = {}
    for node in typed.record_nodes:
        records_by_stable.setdefault(
            node.stable_record_identity.stable_record_id, []).append(
                node.record_node_id)
    for e in typed.observed_edges:
        left, right = e.left_stable_identity, e.right_stable_identity
        left_matches = sorted(records_by_stable.get(left, ()))
        right_matches = sorted(records_by_stable.get(right, ()))
        # Duplicate stable identities are not resolved by iteration order.
        # An audience edge is emitted only when each endpoint maps uniquely.
        left_node = left_matches[0] if len(left_matches) == 1 else None
        right_node = right_matches[0] if len(right_matches) == 1 else None
        if left_node in projectable and right_node in projectable:
            edges.append((e.edge_id, left_node, right_node))
    jumps = tuple(
        D08SourceJumpTarget(j.jump_target_id, j.target_kind, j.target_object_id,
                            j.resolvable)
        for j in result.source_jump_target_pairs)
    anchor = result.audience_anchor
    source_nodes = result.projectable_node_set
    return D08AudienceProjection(
        projectable_node_set=result.projectable_node_set,
        evaluation_node_set=result.evaluation_node_set,
        hidden_node_count=result.hidden_node_count,
        audience_anchor=anchor,
        audience_payload_present=result.audience_payload_present,
        query_present=result.query_present,
        journey_marker_present=result.journey_marker_present,
        risk_present=result.risk_present,
        audience_source_nodes=source_nodes,
        relation_edges=tuple(edges),
        source_jump_target_pairs=jumps,
        disclosure_leak_present=result.disclosure_leak_present,
        audience_lexicon_ref=result.audience_lexicon_ref,
    )


# ---------------------------------------------------------------------------
# Risk marker (contract section 4.3 PublicR4RiskIdentity)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D08RiskMarker:
    marker_id: str
    unit_id: str
    risk_owner: str
    public_risk_identity: Dict[str, Any]
    affected_domains: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    content_hash: Optional[str] = None

    def with_hash(self) -> "D08RiskMarker":
        core = {
            "marker_id": self.marker_id,
            "unit_id": self.unit_id,
            "risk_owner": self.risk_owner,
            "public_risk_identity": self.public_risk_identity,
            "affected_domains": list(self.affected_domains),
            "source_locator_ids": list(self.source_locator_ids),
        }
        return D08RiskMarker(
            marker_id=self.marker_id,
            unit_id=self.unit_id,
            risk_owner=self.risk_owner,
            public_risk_identity=self.public_risk_identity,
            affected_domains=self.affected_domains,
            source_locator_ids=self.source_locator_ids,
            content_hash=d08_content_hash_prefixed(core),
        )


def _stable_event_identity(typed: D08TypedInput, unit: D08UnitResult) -> str:
    """Stable source/event identity: the explicit relation instance when the
    unit is per-instance, else the obligation-side stable identity."""
    if unit.unit_kind == "per_explicit_rel_instance":
        for mem in typed.rel_instance_memberships:
            return mem.rel_instance_id
    if typed.record_nodes:
        return typed.record_nodes[0].stable_record_identity.stable_record_id
    return unit.relation_rule_id


def _affected_domains(typed: D08TypedInput) -> Tuple[str, ...]:
    domains: List[str] = []
    for rule in typed.relation_rules:
        for dom in rule.required_producer_domains:
            if dom not in domains:
                domains.append(dom)
    for n in typed.record_nodes:
        dom = n.stable_record_identity.domain_id
        if dom not in domains:
            domains.append(dom)
    return tuple(domains)


def build_d08_risk_marker(
    typed: D08TypedInput,
    result: D08RunResult,
    unit: Optional[D08UnitResult] = None,
) -> Optional[D08RiskMarker]:
    """Build the D08 risk marker for the run's primary positive unit.

    Returns ``None`` when the run carries no D08-owned positive (no risk to
    mark).  The public risk identity keeps a stable classifier: it never
    merges with D01-D07 identities and never changes on data/date
    revision (rule lineage changes are handled by R2 supersession).
    """
    positives = result.positive_units
    if not positives:
        return None
    unit = unit if unit is not None else positives[0]
    stable_event = _stable_event_identity(typed, unit)
    unit_id = d08_unit_id_hash(typed, unit, stable_event)
    rule = typed.relation_rules[0] if typed.relation_rules else None
    window = rule.applicability_window if rule else None
    normalized_concept = _unit_stable_core(unit)
    public_identity = {
        "domain_id": D08_DOMAIN_ID,
        "public_identity_version": D08_PUBLIC_IDENTITY_VERSION,
        "stable_source_or_event_identity": stable_event,
        "normalized_concept": normalized_concept,
        "temporal_window": {
            "window_kind": window.window_kind if window else None,
            "rule_window_id": rule.rule_id if window else None,
        },
    }
    locators: List[str] = []
    for n in typed.record_nodes:
        if n.record_node_id not in result.projectable_node_set:
            continue
        for loc in n.source_locator_ids:
            if loc not in locators:
                locators.append(loc)
    marker = D08RiskMarker(
        marker_id=d08_content_hash_prefixed({
            "unit_id": unit_id,
            "stable_event_identity": stable_event,
            "normalized_concept": normalized_concept,
        }),
        unit_id=unit_id,
        risk_owner="D08",
        public_risk_identity=public_identity,
        affected_domains=_affected_domains(typed),
        source_locator_ids=tuple(sorted(locators)),
    )
    return marker.with_hash()


# ---------------------------------------------------------------------------
# Three-part Chinese Query draft (contract section 9)
# ---------------------------------------------------------------------------

_SHA256_PREFIX_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_DOMAIN_LABEL_FALLBACK = {
    "ae": "不良事件",
    "mh": "病史",
    "cm": "合并用药",
    "ip": "研究药物",
    "ex": "检查",
    "lb": "实验室检查",
}


def _domain_label(domain: str, typed: D08TypedInput) -> str:
    lexicon = typed.audience_lexicon
    if lexicon is not None and lexicon.allowed_domain_labels:
        for label in lexicon.allowed_domain_labels:
            if domain and domain in label:
                return label
    return _DOMAIN_LABEL_FALLBACK.get(domain, domain)


def _basis_sentence(typed: D08TypedInput, unit: D08UnitResult) -> str:
    rule = typed.relation_rules[0] if typed.relation_rules else None
    rule_ref = rule.rule_id if rule else unit.relation_rule_id
    if unit.signal_type == "propagation_lineage":
        return (
            f"依据：来源修订与派生对象声明消费修订一致性的规则 {rule_ref}，"
            "记录修订后派生结果必须同步更新或明确失效；")
    if unit.signal_type == "identity_collision":
        return (
            f"依据：跨表身份规则 {rule_ref}，同一稳定身份不得在受试者、"
            "中心或语义角色间冲突或重复；")
    if unit.signal_type == "temporal_impossibility":
        return (
            f"依据：时间逻辑规则 {rule_ref}，参与记录的时间关系必须满足"
            "已声明的先后/包含约束；")
    return (
        f"依据：跨表关系规则 {rule_ref} 与已接受数据快照，参与记录应保持"
        "双向可定位且关系守恒；")


def _finding_sentence(typed: D08TypedInput, unit: D08UnitResult) -> str:
    subject = typed.scope_binding.subject_ref if typed.scope_binding else ""
    subject_part = f"受试者 {subject} " if subject else ""
    anchor_node = None
    for n in typed.record_nodes:
        if n.record_node_id in (typed.visibility_decision.projectable_node_set
                                if typed.visibility_decision else ()):
            anchor_node = n
            break
    domain = _domain_label(anchor_node.stable_record_identity.domain_id
                           if anchor_node else "", typed)
    record_ref = anchor_node.record_node_id if anchor_node else ""
    if unit.signal_type == "propagation_lineage":
        return (
            f"发现：{subject_part}{domain} 记录（{record_ref}）修订后，"
            "派生结果声明消费修订与来源修订不一致，数据更新待核实；")
    if unit.signal_type == "identity_collision":
        return (
            f"发现：{subject_part}{domain} 记录（{record_ref}）的稳定身份"
            "在不同受试者/中心/语义角色间存在冲突；")
    if unit.signal_type == "temporal_impossibility":
        return (
            f"发现：{subject_part}{domain} 记录（{record_ref}）与对应记录的时间"
            "关系与规则声明不符；")
    return (
        f"发现：{subject_part}{domain} 记录（{record_ref}）存在跨表引用无法反向"
        "定位或关系未守恒的情形，未见对应记录；")


def _action_sentence() -> str:
    return (
        "行动项：请核实相关参与记录的关联关系与来源修订状态，"
        "并补充或更正对应记录。")


def build_d08_query_draft(
    typed: D08TypedInput,
    result: D08RunResult,
) -> Optional[Dict[str, Any]]:
    """Build the three-part Chinese Query draft for the primary D08-owned
    positive unit.

    Returns ``None`` when the run has no positive unit or no projectable
    audience payload (nothing to query about).  The draft is never sent:
    it is viewable/editable/exportable only.  PD wording is never produced
    here -- D04 owns PD phrasing.
    """
    positives = result.positive_units
    if not positives or not result.projectable_node_set:
        return None
    unit = positives[0]
    stable_event = _stable_event_identity(typed, unit)
    unit_id = d08_unit_id_hash(typed, unit, stable_event)
    risk_marker = build_d08_risk_marker(typed, result, unit)
    risk_id = risk_marker.marker_id if risk_marker else d08_content_hash_prefixed(
        {"unit_id": unit_id})
    basis = _basis_sentence(typed, unit)
    finding = _finding_sentence(typed, unit)
    action = _action_sentence()
    evidence_refs = sorted(result.projectable_node_set)
    locators: List[str] = []
    for n in typed.record_nodes:
        if n.record_node_id not in result.projectable_node_set:
            continue
        for loc in n.source_locator_ids:
            if loc not in locators:
                locators.append(loc)
    scope_binding_id = (
        typed.scope_binding.scope_binding_id if typed.scope_binding else "")
    draft_core = {
        "unit_id": unit_id,
        "risk_id": risk_id,
        "scope_binding_id": scope_binding_id,
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
    }
    audience_payload_hash = d08_content_hash_prefixed(draft_core)
    query_draft_id = d08_content_hash_prefixed({
        "audience_payload_hash": audience_payload_hash,
        "scope_binding_id": scope_binding_id,
    })
    draft: Dict[str, Any] = {
        "query_draft_id": query_draft_id,
        "unit_id": unit_id,
        "risk_id": risk_id,
        "owner_routing_decision_id": None,
        "query_owner": "D08",
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "evidence_refs": evidence_refs,
        "source_locator_ids": sorted(locators),
        "audience_payload_hash": audience_payload_hash,
        "content_hash": None,
    }
    draft["content_hash"] = d08_content_hash_prefixed({
        "query_draft_id": query_draft_id,
        "unit_id": unit_id,
        "risk_id": risk_id,
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "evidence_refs": evidence_refs,
        "source_locator_ids": sorted(locators),
    })
    return draft


def _forbidden_token_hit(lexicon: Any, sentences: Sequence[str]) -> Optional[str]:
    if lexicon is None:
        return None
    for token in lexicon.forbidden_internal_tokens or ():
        for sentence in sentences:
            if token and token in str(sentence):
                return token
    return None


def validate_query_draft(
    draft: Mapping[str, Any],
    typed: D08TypedInput,
    result: D08RunResult,
) -> Dict[str, Any]:
    """Closed audience validation of a D08 Query draft (contract section 9).

    Checks: the three required sentence patterns (``依据``/``发现``/
    ``行动项``), absence of forbidden internal tokens, evidence refs and
    source locators within the projectable node set, content-hash
    consistency and that no PD wording is present.
    """
    reasons: List[str] = []
    lexicon = typed.audience_lexicon
    required = tuple(lexicon.required_sentence_patterns
                     if lexicon and lexicon.required_sentence_patterns
                     else ("依据", "发现", "行动项"))
    sentences = [
        draft.get("basis_sentence"), draft.get("finding_sentence"),
        draft.get("action_sentence"),
    ]
    if len(sentences) != 3 or not all(
            isinstance(s, str) and bool(s) for s in sentences):
        reasons.append("three_sentence_contract")
    pattern_hit = all(
        any(pattern in str(s) for s in sentences if isinstance(s, str))
        for pattern in required)
    if not pattern_hit:
        reasons.append("required_sentence_patterns_missing")
    forbidden = _forbidden_token_hit(lexicon, [s for s in sentences if s])
    if forbidden is not None:
        reasons.append(f"forbidden_internal_token:{forbidden}")
    if "PD" in " ".join(str(s) for s in sentences if s):
        reasons.append("pd_wording_without_owner")
    projectable = set(result.projectable_node_set)
    evidence = draft.get("evidence_refs") or []
    if not all(isinstance(r, str) and r in projectable for r in evidence):
        reasons.append("evidence_not_projectable")
    locators = draft.get("source_locator_ids") or []
    known_locs = {loc.source_locator_id for loc in typed.source_locators}
    visible_locs = {
        locator_id
        for node in typed.record_nodes if node.record_node_id in projectable
        for locator_id in node.source_locator_ids
    }
    if not all(isinstance(loc, str) and loc in known_locs for loc in locators):
        reasons.append("source_locator_unresolved")
    elif not all(loc in visible_locs for loc in locators):
        reasons.append("source_locator_not_projectable")
    content_hash_valid = draft.get("content_hash") == d08_content_hash_prefixed({
        "query_draft_id": draft.get("query_draft_id"),
        "unit_id": draft.get("unit_id"),
        "risk_id": draft.get("risk_id"),
        "basis_sentence": draft.get("basis_sentence"),
        "finding_sentence": draft.get("finding_sentence"),
        "action_sentence": draft.get("action_sentence"),
        "evidence_refs": draft.get("evidence_refs"),
        "source_locator_ids": draft.get("source_locator_ids"),
    })
    if not content_hash_valid:
        reasons.append("content_hash_stale")
    return {"valid": not reasons, "reasons": reasons}
