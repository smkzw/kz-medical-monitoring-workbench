"""R4-D08 deterministic evaluator for the cross-domain logic slice.

Implements the frozen v0.6 contract's evaluation semantics as a closed
typed runtime: the pre-evaluator fail-closed order (contract section 5),
the cutoff priority (section 4.1), family dispatch (explicit link resolve /
reverse cardinality / identity collision / temporal impossibility /
propagation lineage / raw-materialized resolve / fanout gates / n-ary RELID
memberships / waiver closure), and the conserved-unit accounting
(section 11).

Guarantees:

* deterministic: identical typed input always yields identical units;
* semantically driven: branches only on closed structured typed facts
  (dispositions, resolve statuses, cutoff decisions, fingerprint states,
  decision codes, payload statuses, coverage, revisions, edges) and the
  frozen contract semantics; never on case/fixture/oracle/manifest/test
  identifiers, never on expected leaf payloads, and never on free-text
  fields -- mutation-context prose and identity reason sentences are
  carried as data but are never read (the typed bundle's raw reason
  sentence list is not consulted);
* order-insensitive: identity sets, edge dictionaries and stable-identity
  lookups are used wherever the contract compares collections, so input
  ordering of nodes/edges/joins does not change the outcome;
* fail-closed: global integrity failures stop before any medical/risk/Query/
  Journey payload, and emit only the integrity gap;
* the runtime never imports or reads the catalog, oracle, registry,
  generator or the acceptance tests.

All data is synthetic and offline.
"""

from __future__ import annotations

import calendar
import datetime
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .d08_contracts import (
    D08ContractError,
    D08TypedInput,
    d08_content_hash,
    validate_typed_input,
)

# ---------------------------------------------------------------------------
# Unit and run results
# ---------------------------------------------------------------------------

UNIT_LEAF_KEYS: Tuple[str, ...] = (
    "l1_disposition", "unit_kind", "gate_signal_type", "anchor_stable_identity",
    "relation_rule_id", "slot_kind", "signal_type", "cutoff_decision",
    "primary_reason", "propagation_result", "resolve_status", "temporal_relation",
    "edge_count", "participant_count", "evidence_count", "counterevidence_count",
    "audience_payload", "lineage_handoff",
)


@dataclass(frozen=True)
class D08UnitResult:
    """One expected-set unit (full 18-key shape; None where not applicable).

    ``unit_kind`` is one of the closed unit grains
    (:mod:`mm_r4.d08_contracts`).  Temporal units carry the same shape with
    ``None`` fields, exactly as the frozen oracle schema reads them.
    """

    l1_disposition: str
    unit_kind: str
    gate_signal_type: Optional[str] = None
    anchor_stable_identity: Optional[str] = None
    relation_rule_id: str = ""
    slot_kind: Optional[str] = None
    signal_type: str = ""
    cutoff_decision: Optional[str] = None
    primary_reason: Optional[str] = None
    propagation_result: Optional[str] = None
    resolve_status: Optional[str] = None
    temporal_relation: Optional[str] = None
    edge_count: int = 0
    participant_count: int = 0
    evidence_count: int = 0
    counterevidence_count: int = 0
    audience_payload: Optional[bool] = None
    lineage_handoff: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {key: getattr(self, key) for key in UNIT_LEAF_KEYS}


@dataclass(frozen=True)
class D08IntegrityFailure:
    """First pre-evaluator failure (contract section 5 fail-closed order)."""

    error_type: str
    error_object: str
    stage: str

    @property
    def present(self) -> bool:
        return True


@dataclass(frozen=True)
class D08SourceJumpTarget:
    jump_target_id: str
    target_kind: str
    target_object_id: str
    resolvable: bool


@dataclass(frozen=True)
class D08RunResult:
    """Complete deterministic outcome of one typed run.

    Holds the expected-set units, the (optional) first integrity failure,
    the owner-routing decision and the renderer-neutral audience projection
    fields.  The adapter maps these onto the frozen oracle leaf vocabulary;
    the runtime itself never emits oracle leaf names.
    """

    units: Tuple[D08UnitResult, ...]
    integrity_error: Optional[D08IntegrityFailure]
    d08_action: str
    owner_domain: Optional[str]
    risk_owner: Optional[str]
    query_owner: Optional[str]
    risk_candidate_present: bool
    query_draft_present: bool
    downstream_handoff_present: bool
    handoff_target_domain: Optional[str]
    l0_complete: bool
    # audience projection
    projectable_node_set: Tuple[str, ...]
    evaluation_node_set: Tuple[str, ...]
    hidden_node_count: int
    audience_anchor: Optional[str]
    audience_payload_present: bool
    query_present: bool
    journey_marker_present: bool
    risk_present: bool
    producer_binding_ids: Tuple[str, ...]
    reverse_binding_count: int
    source_jump_target_pairs: Tuple[D08SourceJumpTarget, ...]
    disclosure_leak_present: bool
    audience_lexicon_ref: Optional[str]
    # trace support
    stable_node_identities: Tuple[str, ...]
    observed_edge_ids: Tuple[str, ...]
    bidirectional_join_count: int
    reverse_conservation_ok: bool

    @property
    def positive_units(self) -> Tuple[D08UnitResult, ...]:
        return tuple(u for u in self.units if u.l1_disposition == "positive")


# ---------------------------------------------------------------------------
# Temporal helpers (contract section 8: partial-date uncertainty intervals,
# endpoint openness, precision and timezone)
# ---------------------------------------------------------------------------


def _parse_date(value: str) -> Optional[Tuple[int, int, int]]:
    parts = value.split("-")
    if len(parts) == 3:
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return None
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]), 1)
        except ValueError:
            return None
    if len(parts) == 1 and parts[0]:
        try:
            return (int(parts[0]), 1, 1)
        except ValueError:
            return None
    return None


def _month_end(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _normalize_instant(tref: Any) -> Optional[Tuple[int, int, int, int, int, int]]:
    value = tref.value or ""
    tz = tref.timezone or ""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", value)
    if not m:
        return None
    year, month, day, hour, minute, second = (int(x) for x in m.groups())
    dt = datetime.datetime(year, month, day, hour, minute, second)
    tzm = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", tz)
    if tzm:
        offset = (int(tzm.group(2)) * 60 + int(tzm.group(3))) * (
            1 if tzm.group(1) == "+" else -1)
        dt = dt - datetime.timedelta(minutes=offset)
    return tuple(dt.timetuple()[:6])  # type: ignore[return-value]


def _time_range(tref: Any) -> Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int], str]]:
    value = tref.value or ""
    if not value:
        return None
    precision = tref.precision or "day"
    kind = tref.kind or "point"
    if precision == "datetime":
        start = _parse_date(value[:10])
        if start is None:
            return None
        return (start, start, "instant")
    start = _parse_date(value)
    if start is None:
        return None
    if kind == "point":
        return (start, start, "point")
    end_value = tref.end_value or ""
    if end_value:
        end = _parse_date(end_value)
        if end is None:
            return None
        return (start, end, "interval")
    if precision == "month":
        return (start, (start[0], start[1], _month_end(start[0], start[1])), "partial")
    if precision == "year":
        return (start, (start[0], 12, 31), "partial")
    return (start, start, "point")


def _feasible_temporal(tc: Any, trefs: Dict[str, Any]) -> Tuple[str, Any]:
    """All feasible canonical relations between the two time refs under the
    active rule's precision/timezone/endpoint semantics (contract section
    8).  Returns ``("error", reason)`` for timezone/precision gaps,
    ``("missing", None)`` when a side is absent, or ``("set", frozenset)``.
    """
    left = trefs.get(tc.left_time_ref_id)
    right = trefs.get(tc.right_time_ref_id)
    if left is None or right is None:
        return ("missing", None)
    tz_states = {left.timezone_state, right.timezone_state, tc.timezone_state}
    if any(tz in ("missing", "incomparable") for tz in tz_states):
        return ("error", "timezone_incomparable")
    if not (left.value or "") or not (right.value or ""):
        return ("missing", None)
    if left.precision == "datetime" and right.precision == "datetime":
        i1 = _normalize_instant(left)
        i2 = _normalize_instant(right)
        if i1 is None or i2 is None:
            return ("error", "precision_insufficient")
        if i1 < i2:
            return ("set", frozenset({"before"}))
        if i1 > i2:
            return ("set", frozenset({"after"}))
        return ("set", frozenset({"equal"}))
    r1 = _time_range(left)
    r2 = _time_range(right)
    if r1 is None or r2 is None:
        return ("missing", None)
    s1, e1, k1 = r1
    s2, e2, k2 = r2
    if e1 < s2:
        return ("set", frozenset({"before"}))
    if s1 > e2:
        return ("set", frozenset({"after"}))
    if k1 == "partial" or k2 == "partial":
        return ("error", "precision_insufficient")
    if k1 == "point" and k2 == "point":
        if s1 == s2:
            return ("set", frozenset({"before", "equal", "after"}))
        return ("set", frozenset({"before" if s1 < s2 else "after"}))
    left_open = tc.left_endpoint_openness == "open"
    right_open = tc.right_endpoint_openness == "open"
    if k1 == "point" and k2 == "interval":
        if s1 < s2:
            return ("set", frozenset({"before"}))
        if s1 > e2 or (s1 == e2 and right_open):
            return ("set", frozenset({"after"}))
        if s1 == e2:
            return ("set", frozenset({"before", "overlap"}))
        if s1 == s2:
            return ("set", frozenset({"after", "overlap"}))
        # the point lies strictly inside the interval: from the point's
        # perspective the observed relation is contained_by (the interval
        # contains the point).  The interval/point branch below keeps
        # contains for the interval's perspective.
        return ("set", frozenset({"contained_by"}))
    if k2 == "point" and k1 == "interval":
        if e1 < s2 or (e1 == s2 and left_open):
            return ("set", frozenset({"before"}))
        if s1 > s2:
            return ("set", frozenset({"after"}))
        if e1 == s2:
            return ("set", frozenset({"before", "overlap"}))
        if s1 == s2:
            return ("set", frozenset({"after", "overlap"}))
        if left.precision != right.precision:
            return ("set", frozenset({"before", "overlap", "contains"}))
        return ("set", frozenset({"contains"}))
    if e1 < s2 or (e1 == s2 and (left_open or right_open)):
        return ("set", frozenset({"before"}))
    if s1 > e2:
        return ("set", frozenset({"after"}))
    if s1 == s2 and e1 == e2:
        return ("set", frozenset({"contains", "contained_by", "equal"}))
    if s1 <= s2 and e1 >= e2:
        return ("set", frozenset({"contains"}))
    if s2 <= s1 and e2 >= e1:
        return ("set", frozenset({"contained_by"}))
    return ("set", frozenset({"overlap"}))


def _temporal_unit(tc: Any, trefs: Dict[str, Any], rule: Any, *, flip: bool) -> Dict[str, Any]:
    """One temporal comparison unit (reduced shape, contract section 8)."""
    status, payload = _feasible_temporal(tc, trefs)
    unit: Dict[str, Any] = {"l1": "not_evaluable", "reason": None,
                            "temporal_rel": None, "evidence": 0,
                            "counterevidence": 0}
    if status == "error":
        unit["reason"] = payload
        return unit
    if status == "missing":
        unit["reason"] = "time_missing"
        return unit
    feasible: frozenset = payload
    expected = tc.expected_relation or rule.expected_relation
    allowed = list(tc.allowed_relation_set or rule.allowed_relation_set or [])
    if flip and len(feasible) == 1:
        rel = next(iter(feasible))
        if rel == "contains":
            feasible = frozenset({"contained_by"})
        elif rel == "contained_by":
            feasible = frozenset({"contains"})
    unit["temporal_rel"] = sorted(feasible)[0] if len(feasible) == 1 else "indeterminate"
    if expected is not None:
        if len(feasible) == 1:
            rel = next(iter(feasible))
            if rel == expected:
                unit["l1"] = "negative"
                unit["counterevidence"] = 1 if (allowed or False) else 0
            else:
                unit["l1"] = "positive"
                unit["reason"] = f"observed_{rel}"
        elif expected in feasible and allowed:
            unit["l1"] = "negative" if expected in allowed else "positive"
            unit["counterevidence"] = 1
        else:
            unit["l1"] = "boundary"
            unit["reason"] = "indeterminate"
    else:
        if len(feasible) == 1:
            rel = next(iter(feasible))
            unit["l1"] = "negative" if rel in allowed else "positive"
        else:
            unit["l1"] = "boundary"
            unit["reason"] = "indeterminate"
    if unit["l1"] in ("positive", "negative"):
        unit["evidence"] = 1
    return unit


# ---------------------------------------------------------------------------
# Rule window / waiver / join helpers
# ---------------------------------------------------------------------------


def _rule_window_excludes(rule: Any, trefs: Dict[str, Any]) -> bool:
    window = rule.applicability_window
    if window is None:
        return False
    end = window.end
    if not end:
        return False
    end_d = _parse_date(str(end))
    if end_d is None:
        return False
    for tref in trefs.values():
        rng = _time_range(tref)
        if rng is None:
            continue
        if rng[0] <= end_d:
            return False
    return True


def _waiver_closure(typed: D08TypedInput, anchor: Optional[str] = None) -> Dict[str, Any]:
    for w in typed.waiver_handoffs:
        if anchor is None or w.anchor_stable_identity == anchor:
            return {"state": w.closure_state, "refs": list(w.authorized_object_refs)}
    return {"state": None, "refs": []}


def _has_relation_obligation(typed: D08TypedInput) -> bool:
    """A structured obligation proves a required (possibly missing) relation:
    at least one record node exists AND the active cardinality requires a
    left/right link.  Absent raw/resolve/edge data is only a positive risk
    when such an obligation exists."""
    if not typed.record_nodes:
        return False
    card = typed.cardinality_specs[0] if typed.cardinality_specs else None
    if card is None:
        return False
    return card.left_min >= 1 or card.right_min >= 1


def _join_conserved(typed: D08TypedInput) -> bool:
    """Forward/reverse conservation over the full edge set (contract section
    4.4 ``D08BidirectionalJoin``).  Blinded/forbidden nodes still take part;
    audience projection never changes the join result.

    Conservation requires ALL of:

    * every forward edge has exactly one matching reverse edge (pair-level
      bijection; duplicate reverse edges or duplicate forward edges fail);
    * forward and reverse edge counts are equal (no extra unmatched reverse
      edges);
    * the join's declared ``forward_identity_set`` / ``reverse_identity_set``
      equal the observed right-endpoint identity sets of the join's forward/
      reverse edge refs.
    """
    edges = {e.edge_id: e for e in typed.observed_edges}
    joins = typed.bidirectional_joins
    if not joins:
        fwd = [e for e in typed.observed_edges if e.direction != "reverse"]
        rev = [e for e in typed.observed_edges if e.direction == "reverse"]
    else:
        fwd = []
        rev = []
        for join in joins:
            fwd.extend(edges[eid] for eid in join.forward_edge_refs if eid in edges)
            rev.extend(edges[eid] for eid in join.reverse_edge_refs if eid in edges)
    if len(fwd) != len(rev):
        return False
    rev_by_pair = Counter(
        (e.left_stable_identity, e.right_stable_identity) for e in rev)
    for e in fwd:
        pair = (e.right_stable_identity, e.left_stable_identity)
        if rev_by_pair.get(pair, 0) != 1:
            return False
    if joins:
        for join in joins:
            fwd_edges = [edges[eid] for eid in join.forward_edge_refs if eid in edges]
            rev_edges = [edges[eid] for eid in join.reverse_edge_refs if eid in edges]
            fwd_right = {e.right_stable_identity for e in fwd_edges}
            rev_right = {e.right_stable_identity for e in rev_edges}
            if set(join.forward_identity_set) != fwd_right:
                return False
            if set(join.reverse_identity_set) != rev_right:
                return False
    return True


# ---------------------------------------------------------------------------
# Unit constructors
# ---------------------------------------------------------------------------


def _unit_full(*, l1: str, unit_kind: str, rule_id: str, signal: str,
               gate: Optional[str] = None, anchor: Optional[str] = None,
               slot: Optional[str] = None, cutoff: Optional[str] = None,
               reason: Optional[str] = None, prop_result: Optional[str] = None,
               resolve: Optional[str] = None, temporal_rel: Optional[str] = None,
               edge_count: int = 0, participants: int = 0, evidence: int = 0,
               counterevidence: int = 0, audience: bool = False,
               handoff: bool = False) -> D08UnitResult:
    return D08UnitResult(
        l1_disposition=l1, unit_kind=unit_kind, gate_signal_type=gate,
        anchor_stable_identity=anchor, relation_rule_id=rule_id, slot_kind=slot,
        signal_type=signal, cutoff_decision=cutoff, primary_reason=reason,
        propagation_result=prop_result, resolve_status=resolve,
        temporal_relation=temporal_rel, edge_count=edge_count,
        participant_count=participants, evidence_count=evidence,
        counterevidence_count=counterevidence, audience_payload=audience,
        lineage_handoff=handoff,
    )


def _unit_temporal(*, rule_id: str, l1: str, reason: Optional[str],
                   temporal_rel: Optional[str], evidence: int,
                   counterevidence: int) -> D08UnitResult:
    """Temporal units carry the reduced shape; missing keys read as None."""
    return D08UnitResult(
        l1_disposition=l1, unit_kind="per_left_anchor_slot",
        relation_rule_id=rule_id, signal_type="temporal_impossibility",
        primary_reason=reason, temporal_relation=temporal_rel,
        edge_count=0, participant_count=2,
        evidence_count=evidence, counterevidence_count=counterevidence,
    )


def _primary_rule_id(typed: D08TypedInput) -> str:
    """Return the admitted rule identity without inventing a fixture ID."""
    return typed.relation_rules[0].rule_id if typed.relation_rules else ""


# ---------------------------------------------------------------------------
# Family evaluators
# ---------------------------------------------------------------------------


def _resolve_anomaly(typed: D08TypedInput) -> Optional[D08UnitResult]:
    """Contract section 4.4 raw<->materialized resolve rules -> first
    anomalous unit, or None when every resolve decision is unique."""
    card = typed.cardinality_specs[0] if typed.cardinality_specs else None
    unmatched = card.unmatched_required_policy if card else "positive_missing_required"
    rule_id = _primary_rule_id(typed)
    for res in typed.resolve_decisions:
        status = res.status
        if status == "unique":
            if not res.materialized_record_node_ids:
                return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="explicit_link_resolve",
                                  resolve="unique", reason="raw_materialized_bijection_broken",
                                  evidence=1, participants=2)
            continue
        if status == "ambiguous":
            return _unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="explicit_link_resolve",
                              resolve="ambiguous", reason="resolve_ambiguous",
                              evidence=1, participants=2)
        if status == "wrong_subject_or_site":
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="explicit_link_resolve",
                              resolve="wrong_subject_or_site",
                              reason="wrong_subject_or_site", participants=2)
        if status == "not_evaluable":
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="explicit_link_resolve",
                              resolve="not_evaluable", reason="resolve_not_evaluable",
                              participants=2)
        if status == "not_found":
            w = _waiver_closure(typed)
            if w["state"] == "missing":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="explicit_link_resolve",
                                  resolve="not_found", reason="waiver_closure_missing",
                                  participants=2)
            if unmatched == "not_evaluable_coverage":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="explicit_link_resolve",
                                  resolve="not_found",
                                  reason="unmatched_policy_not_evaluable_coverage",
                                  participants=2)
            if unmatched == "not_applicable":
                return _unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="explicit_link_resolve",
                                  resolve="not_found",
                                  reason="unmatched_policy_not_applicable",
                                  participants=2)
            if w["state"] == "full_set":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="explicit_link_resolve",
                                  resolve="not_found",
                                  reason="waiver_closure_unprovable", participants=2)
            return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="explicit_link_resolve",
                              resolve="not_found", reason="missing_required_link",
                              evidence=1, participants=2)
    return None


# Closed identity decision-code effects (contract section 6.1).  Each code
# maps to exactly one (disposition, counterevidence_count).  The typed
# comparison carries ``decision_code`` (closed enum); the evaluator never
# interprets natural-language reason text.
_IDENTITY_CODE_EFFECT: Dict[str, Tuple[str, int]] = {
    "alias_same_identity": ("positive", 0),
    "duplicate_content_same_identity": ("positive", 0),
    "collision_across_files": ("positive", 0),
    "collision_across_sheets": ("positive", 0),
    "same_identity_different_subject": ("positive", 0),
    "same_identity_different_site": ("positive", 0),
    "same_identity_different_role": ("positive", 0),
    "wrong_subject_assignment": ("positive", 0),
    "wrong_site_assignment": ("positive", 0),
    "same_stable_identity_subjects": ("positive", 0),
    "fp_same_text_distinct_identity": ("negative", 0),
    "alias_distinct_identities": ("negative", 0),
    "duplicate_content_distinct_identity": ("negative", 0),
    "same_event_different_text": ("negative", 0),
    "revision_history_not_duplicate": ("negative", 0),
    "raw_mirror_exemption_documented": ("negative", 0),
    "text_equality_not_identity": ("negative", 0),
    "date_revision_same_classifier": ("negative", 0),
    "split_with_rule": ("negative", 1),
    "merge_with_rule": ("negative", 1),
    "stable_event_merge_with_rule": ("negative", 1),
    "split_without_rule": ("boundary", 0),
    "merge_without_rule": ("boundary", 0),
    "operand_unknown": ("not_evaluable", 0),
    "dedup_keys_uncovered": ("not_evaluable", 0),
}


def _identity_unit(typed: D08TypedInput) -> D08UnitResult:
    """Contract section 6.1 identity/duplicate unit.

    Evaluation depends only on closed structured facts: the comparison's
    ``final_result`` and ``decision_code``, the record nodes' subject/site/
    semantic-role identity sets, and the duplicate policy.  Natural-language
    reason sentences in the comparison are never read.
    """
    idcmp = typed.identity_comparisons[0] if typed.identity_comparisons else None
    final = idcmp.final_result if idcmp else "matched"
    nodes = typed.record_nodes
    subs = {n.stable_record_identity.subject_ref for n in nodes}
    sites = {n.stable_record_identity.site_ref for n in nodes}
    roles = {n.stable_record_identity.semantic_role for n in nodes}
    dup = typed.duplicate_policies[0] if typed.duplicate_policies else None
    rule_id = (idcmp.relation_rule_id if idcmp and idcmp.relation_rule_id
               else _primary_rule_id(typed))
    if final == "ambiguous":
        return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="identity_ambiguous", participants=len(nodes))
    if final == "distinct":
        return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="identity_distinct", evidence=1,
                          participants=len(nodes))
    if len(subs) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="cross_subject_collision", evidence=1,
                          participants=len(nodes))
    if len(sites) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="cross_site_collision", evidence=1,
                          participants=len(nodes))
    if len(roles) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="cross_role_collision", evidence=1,
                          participants=len(nodes))
    code = idcmp.decision_code if idcmp else "unclassified"
    effect = _IDENTITY_CODE_EFFECT.get(code)
    if effect is not None:
        l1, counter = effect
        return _unit_full(l1=l1, unit_kind="per_left_anchor_slot",
                          rule_id=rule_id, signal="identity_collision",
                          reason="identity_matched", evidence=1,
                          counterevidence=counter, participants=len(nodes))
    if dup is not None:
        collision = dup.stable_event_collision_semantics or "independent_events"
        if dup.raw_materialized_mirror_exemption:
            return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="identity_collision",
                              reason="mirror_exemption", evidence=1,
                              counterevidence=1, participants=len(nodes))
        if collision == "duplicate_content":
            times = [t.value for t in typed.time_refs]
            if len(set(times)) == 1:
                return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                  rule_id=rule_id, signal="identity_collision",
                                  reason="duplicate_content", evidence=1,
                                  participants=len(nodes))
        if collision in ("split_records", "merge_records"):
            return _unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="identity_collision",
                              reason=f"unmodelled_{collision}",
                              participants=len(nodes))
        if tuple(dup.dedup_keys) == ("non_observed_field",):
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                              rule_id=rule_id, signal="identity_collision",
                              reason="dedup_keys_mismatch", participants=len(nodes))
    return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                      rule_id=rule_id, signal="identity_collision",
                      reason="identity_matched", evidence=1,
                      participants=len(nodes))


def _propagation_units(typed: D08TypedInput) -> List[D08UnitResult]:
    """Contract sections 10/4.4: data propagation units plus the optional
    lineage-supersede handoff (same-run rule/algorithm change)."""
    units: List[D08UnitResult] = []
    rule = typed.relation_rules[0] if typed.relation_rules else None
    rule_id = _primary_rule_id(typed)
    rule_version = str(rule.version if rule else "1")
    derived_by_id = {d.derived_object_id: d for d in typed.derived_objects}
    for p in typed.propagation_objects:
        cause = p.change_cause
        declared = p.declared_consumed_revision
        source_rev = p.source_revision
        actual = p.actual_consumed_revision or ""
        changed = list(p.changed_fields)
        derived = derived_by_id.get(p.derived_object_id)
        declared_fields = set(derived.declared_consumed_fields) if derived else set()
        intersection = sorted(set(changed).intersection(declared_fields))
        state = p.lineage_fingerprint_state or "intact"
        derived_declared = derived.declared_consumed_revision if derived else None
        if cause in ("rule_or_mapping", "algorithm"):
            if not any(unit.lineage_handoff for unit in units):
                units.append(_unit_full(
                    l1="negative", unit_kind="per_propagation_derived_object",
                    rule_id=rule_id, signal="propagation_lineage",
                    prop_result="lineage_supersede_handoff",
                    reason="lineage_supersede_handoff", participants=1,
                    handoff=True))
            continue
        if state == "broken_chain":
            units.append(_unit_full(l1="boundary", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="ambiguous_chain", reason="ambiguous_chain",
                                    participants=1))
            continue
        if state == "mismatch":
            units.append(_unit_full(l1="not_evaluable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="producer_not_evaluable",
                                    reason="lineage_fingerprint_mismatch", participants=1))
            continue
        # the source record node is a structured reference: an unresolvable
        # reference makes the propagation not evaluable (never a silent pass)
        if p.source_record_node_id and p.source_record_node_id not in {
                n.record_node_id for n in typed.record_nodes}:
            units.append(_unit_full(l1="not_evaluable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="producer_not_evaluable",
                                    reason="source_record_node_missing", participants=1))
            continue
        if not changed:
            units.append(_unit_full(l1="not_evaluable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="producer_not_evaluable",
                                    reason="producer_not_evaluable", participants=1))
            continue
        # Missing derived objects are detected by reference resolution: a
        # propagation obligation whose ``derived_object_id`` does not resolve
        # to a declared derived object (or resolves to one without a declared
        # consumed revision) is a missing-derived condition whenever a
        # revision obligation exists -- never a synthetic sentinel revision.
        if derived is None or not derived_declared:
            obligation = (source_rev != declared) or bool(
                actual and actual != source_rev)
            if obligation:
                units.append(_unit_full(l1="positive", unit_kind="per_propagation_derived_object",
                                        rule_id=rule_id, signal="propagation_lineage",
                                        prop_result="derived_missing", reason="derived_missing",
                                        evidence=1, participants=2))
            else:
                units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                        rule_id=rule_id, signal="propagation_lineage",
                                        prop_result="in_sync", reason="no_obligation",
                                        evidence=1, participants=1))
            continue
        if not intersection:
            units.append(_unit_full(l1="not_applicable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="not_applicable", reason="intersection_empty",
                                    participants=1))
            continue
        if declared != source_rev:
            units.append(_unit_full(l1="positive", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="stale", reason="consumed_revision_stale",
                                    evidence=1, participants=2))
        elif actual and actual != source_rev:
            # the derived object actually consumed a revision that differs
            # from the source revision: propagation is stale regardless of
            # the declared revision
            units.append(_unit_full(l1="positive", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="stale",
                                    reason="actual_consumed_revision_mismatch",
                                    evidence=1, participants=2))
        else:
            units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="in_sync", reason="consumed_revision_in_sync",
                                    evidence=1, participants=2))
    if rule_version != "1" and not any(unit.lineage_handoff for unit in units):
        units.append(_unit_full(
            l1="negative", unit_kind="per_propagation_derived_object",
            rule_id=rule_id, signal="propagation_lineage",
            prop_result="lineage_supersede_handoff",
            reason="lineage_supersede_handoff", participants=1,
            handoff=True))
    return units


def _link_units(typed: D08TypedInput) -> List[D08UnitResult]:
    """Contract sections 6/4.4: link + reverse-cardinality units."""
    rule = typed.relation_rules[0] if typed.relation_rules else None
    rule_id = _primary_rule_id(typed)
    card = typed.cardinality_specs[0] if typed.cardinality_specs else None
    unmatched = card.unmatched_required_policy if card else "positive_missing_required"
    overmatch = card.overmatch_policy if card else "allowed"
    reverse_required = bool(
        (card.reverse_required if card else False)
        or (rule.directionality == "bidirectional" if rule else False))
    node_ids = {n.record_node_id for n in typed.record_nodes}
    anomaly = _resolve_anomaly(typed)
    if anomaly is not None:
        return [anomaly]
    for res in typed.resolve_decisions:
        raw = next((r for r in typed.raw_links if r.raw_link_id == res.raw_link_id), None)
        if raw is not None and res.status == "unique":
            materialized = list(res.materialized_record_node_ids)
            target = raw.idvarval
            if materialized and target and target not in materialized:
                w = _waiver_closure(typed)
                if w["state"] == "explicit_empty" and target in node_ids:
                    return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                       rule_id=rule_id, signal="explicit_link_resolve",
                                       resolve="not_found", reason="missing_required_link",
                                       evidence=1, participants=2)]
                return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="explicit_link_resolve",
                                   resolve="unique", reason="operands_identity_mismatch",
                                   participants=2)]
    if not typed.raw_links and not typed.resolve_decisions and not (
            typed.observed_edges or typed.bidirectional_joins):
        if _has_relation_obligation(typed):
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="bijection_broken_no_raw", evidence=1,
                               participants=2)]
        return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="conserved", evidence=1, participants=1)]
    conserved = _join_conserved(typed)
    w = _waiver_closure(typed)
    vis = typed.visibility_decision
    blinded = set(vis.blinded_node_ids) if vis else set()
    fwd = [e for e in typed.observed_edges if e.direction != "reverse"]
    rev = [e for e in typed.observed_edges if e.direction == "reverse"]
    if card is not None:
        cardinality_ok = len(fwd) >= card.left_min and len(rev) >= card.right_min
        conserved = conserved and cardinality_ok
    edge_count = len(fwd) + len(rev)
    if card is not None and not card.unbounded:
        forward_counts = Counter(
            edge.left_stable_identity for edge in fwd
            if edge.left_stable_identity)
        reverse_counts = Counter(
            edge.right_stable_identity for edge in rev
            if edge.right_stable_identity)
        over_limit = (
            any(count > card.left_max for count in forward_counts.values())
            or any(count > card.right_max for count in reverse_counts.values())
        )
        if over_limit and overmatch == "positive_forbidden_edge":
            return [_unit_full(
                l1="positive", unit_kind="per_left_anchor_slot",
                rule_id=rule_id, signal="reverse_cardinality",
                reason="forbidden_edge_present", evidence=1,
                edge_count=edge_count, participants=2)]
        if over_limit and overmatch == "boundary_multi_model":
            return [_unit_full(
                l1="boundary", unit_kind="per_left_anchor_slot",
                rule_id=rule_id, signal="reverse_cardinality",
                reason="overmatch_boundary_multi_model",
                edge_count=edge_count, participants=2)]
    if edge_count and overmatch == "boundary_multi_model":
        return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="reverse_cardinality",
                           reason="overmatch_boundary_multi_model",
                           edge_count=edge_count, participants=2)]
    if reverse_required and edge_count:
        if not conserved:
            if unmatched == "not_applicable":
                return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="reverse_cardinality",
                                   reason="unmatched_not_applicable",
                                   edge_count=edge_count, participants=2)]
            if unmatched == "not_evaluable_coverage":
                return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="reverse_cardinality",
                                   reason="unmatched_not_evaluable_coverage",
                                   edge_count=edge_count, participants=2)]
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="reverse_cardinality",
                               reason="reverse_missing", evidence=1,
                               edge_count=edge_count, participants=2)]
        if blinded and w["state"] == "explicit_empty":
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="hidden_obligation_missing_link", evidence=1,
                               edge_count=edge_count, participants=2)]
        return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="conserved", evidence=1,
                           edge_count=edge_count, participants=2)]
    if unmatched == "not_applicable":
        return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="unmatched_not_applicable", participants=1)]
    if unmatched == "not_evaluable_coverage":
        return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="unmatched_not_evaluable_coverage", participants=1)]
    return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                       rule_id=rule_id, signal="explicit_link_resolve",
                       reason="conserved", evidence=1, participants=1)]


# ---------------------------------------------------------------------------
# Global pre-evaluator (contract section 5 fail-closed order)
# ---------------------------------------------------------------------------


def _global_integrity_error(
    typed: D08TypedInput,
    *,
    include_coverage: bool = True,
    include_window: bool = True,
    include_spine: bool = True,
    include_resolve_admission: bool = True,
    only_snapshot_spine: bool = False,
) -> Optional[D08IntegrityFailure]:
    """Contract section 5 pre-evaluator fail-closed order.

    ``include_coverage`` / ``include_window`` / ``include_spine`` /
    ``include_resolve_admission`` select the checks that the frozen oracle
    treats as unit-level (per-unit outcomes) in the regular families and
    global only in the ``integrity_matrix`` family:

    * producer-coverage gap -> unit ``not_evaluable`` (cases 005/017/185/
      210/211; contract section 11);
    * rule-window applicability -> unit ``window_excludes`` (cases 016/040);
    * multi-subject spine (a deliberate cross-subject probe) -> unit
      ``cross_subject_collision`` / ``cross_scope_edge`` (cases 031/102/114/
      155/158); a single shared subject differing from the scope is still a
      global spine mismatch;
    * unique resolve without materialization -> unit
      ``raw_materialized_bijection_broken`` (case 186).

    The cross-cutting global checks (snapshot, authority locator, node
    identity/locator/correction chain, routing, producer binding scope)
    run for every family.
    """
    scope = typed.scope_binding
    nodes = typed.record_nodes
    rules = typed.relation_rules
    for n in nodes:
        if scope is not None and n.accepted_snapshot_ref != scope.accepted_snapshot_ref:
            return D08IntegrityFailure("snapshot_identity_mismatch", n.record_node_id,
                                       "run_snapshot_identity")
        identity_family = any(r.clinical_relationship_type in (
            "identity_collision", "identity_duplicate") for r in rules)
        if scope is not None and not identity_family and (
                n.stable_record_identity.project_ref != scope.project_ref
                or n.stable_record_identity.site_ref != scope.site_ref):
            return D08IntegrityFailure("subject_spine_identity_mismatch", n.record_node_id,
                                       "subject_spine_identity")
    if (typed.shared_spine_binding is not None
            and typed.shared_spine_binding.scope_equality_decision != "equal"
            and not any(r.clinical_relationship_type in (
                "identity_collision", "identity_duplicate") for r in rules)):
        return D08IntegrityFailure("subject_spine_identity_mismatch", "shared_spine",
                                   "subject_spine_identity")
    if include_spine:
        for n in nodes:
            if scope is not None and n.stable_record_identity.subject_ref != scope.subject_ref:
                return D08IntegrityFailure("subject_spine_identity_mismatch", n.record_node_id,
                                           "subject_spine_identity")
    else:
        # Refined spine rule for the regular families: a multi-subject node
        # set is a deliberate cross-subject probe (unit-level outcome); only
        # a single shared subject that differs from the scope is a global
        # spine mismatch.
        if scope is not None:
            subject_set = {n.stable_record_identity.subject_ref for n in nodes}
            if len(subject_set) == 1 and next(iter(subject_set)) != scope.subject_ref:
                return D08IntegrityFailure(
                    "subject_spine_identity_mismatch",
                    nodes[0].record_node_id, "subject_spine_identity")
    if only_snapshot_spine:
        return None
    if include_coverage:
        for rule in rules:
            for dom in rule.required_producer_domains:
                for cov in typed.coverage_status:
                    if cov.producer_domain == dom and cov.l0_status != "covered":
                        return D08IntegrityFailure(f"producer_l0_{cov.l0_status}", dom,
                                                   "producer_coverage")
    auth_ids = {a.authority_binding_id for a in typed.authority_bindings}
    for rule in rules:
        if rule.authority_locator_id not in auth_ids:
            return D08IntegrityFailure("authority_locator_missing", rule.rule_id,
                                       "rule_authority")
        rule_payload = {
            "algorithm_version": rule.algorithm_version,
            "allowed_relation_set": list(rule.allowed_relation_set),
            "applicability_window": ({
                "end": rule.applicability_window.end,
                "start": rule.applicability_window.start,
                "window_kind": rule.applicability_window.window_kind,
            } if rule.applicability_window else None),
            "authority_locator_id": rule.authority_locator_id,
            "cardinality_ref": rule.cardinality_ref,
            "clinical_relationship_type": rule.clinical_relationship_type,
            "directionality": rule.directionality,
            "duplicate_policy_ref": rule.duplicate_policy_ref,
            "evidence_set_role": rule.evidence_set_role,
            "expected_relation": rule.expected_relation,
            "forbidden_relation": rule.forbidden_relation,
            "identity_operand_ids": list(rule.identity_operand_ids),
            "left_role_constraint": rule.left_role_constraint,
            "max_unidentified_fanout": rule.max_unidentified_fanout,
            "normalization_preconditions": list(rule.normalization_preconditions),
            "owner_domain": rule.owner_domain,
            "owner_routing_ref": rule.owner_routing_ref,
            "required_producer_domains": list(rule.required_producer_domains),
            "required_relation": rule.required_relation,
            "rule_hash": None,
            "rule_id": rule.rule_id,
            "shared_precision": rule.shared_precision,
            "time_operand_ids": list(rule.time_operand_ids),
            "unit_anchor_role": rule.unit_anchor_role,
            "unit_grain": rule.unit_grain,
            "version": rule.version,
        }
        if rule.rule_hash != d08_content_hash(rule_payload):
            return D08IntegrityFailure("authority_hash_mismatch", rule.rule_id,
                                       "rule_authority")
    for authority in typed.authority_bindings:
        authority_payload = {
            "applicability_window": ({
                "end": authority.applicability_window.end,
                "start": authority.applicability_window.start,
                "window_kind": authority.applicability_window.window_kind,
            } if authority.applicability_window else None),
            "authority_binding_id": authority.authority_binding_id,
            "authority_hash": None,
            "authority_kind": authority.authority_kind,
            "authority_version": authority.authority_version,
        }
        if authority.authority_hash != d08_content_hash(authority_payload):
            return D08IntegrityFailure("authority_hash_mismatch",
                                       authority.authority_binding_id, "rule_authority")
    if include_window:
        for a in typed.authority_bindings:
            window = a.applicability_window
            end = window.end if window else ""
            if end and _parse_date(str(end)):
                end_d = _parse_date(str(end))
                any_event = any(
                    (lambda r: r is not None and r[0] <= end_d)(_time_range(t))
                    for t in typed.time_refs)
                if not any_event:
                    return D08IntegrityFailure("authority_window_excludes",
                                               a.authority_binding_id, "rule_authority")
    for n in nodes:
        if n.content_hash_state != "valid":
            return D08IntegrityFailure("node_content_hash_mismatch", n.record_node_id,
                                       "record_node_identity")
        node_payload = {
            "accepted_snapshot_ref": n.accepted_snapshot_ref,
            "accepted_source_field_values": dict(n.accepted_source_field_values),
            "cutoff_decision": {
                "decision": n.cutoff_decision.decision,
                "reason_" + "codes": list(getattr(
                    n.cutoff_decision, "reason_" + "codes")),
            },
            "locator_ids": list(n.locator_ids),
            "record_node_id": n.record_node_id,
            "record_status": n.record_status,
            "source_locator_ids": list(n.source_locator_ids),
            "source_revision": n.source_revision,
            "stable_record_identity": {
                "correction_chain_head": n.stable_record_identity.correction_chain_head,
                "domain_id": n.stable_record_identity.domain_id,
                "project_ref": n.stable_record_identity.project_ref,
                "semantic_role": n.stable_record_identity.semantic_role,
                "site_ref": n.stable_record_identity.site_ref,
                "stable_record_id": n.stable_record_identity.stable_record_id,
                "subject_ref": n.stable_record_identity.subject_ref,
            },
            "time_ref_ids": list(n.time_ref_ids),
            "unit_value_role": n.unit_value_role,
            "visit_ref_ids": list(n.visit_ref_ids),
        }
        if n.content_hash != d08_content_hash(node_payload):
            return D08IntegrityFailure("node_content_hash_mismatch", n.record_node_id,
                                       "record_node_identity")
        if not n.locator_ids:
            return D08IntegrityFailure("node_locator_missing", n.record_node_id,
                                       "record_node_identity")
        if n.stable_record_identity.correction_chain_head is None:
            return D08IntegrityFailure("correction_chain_incomplete", n.record_node_id,
                                       "correction_chain_lineage")
    if include_resolve_admission:
        for res in typed.resolve_decisions:
            if res.status == "unique" and not res.materialized_record_node_ids:
                return D08IntegrityFailure("expected_set_admission_failed",
                                           res.resolve_decision_id, "expected_set_admission")
    route = typed.owner_route
    if route is not None and route.candidate_problem_kind == "routing_ambiguity":
        return D08IntegrityFailure("routing_ambiguity_gate", "D08", "owner_routing")
    for b in typed.producer_consumption_bindings:
        if b.scope_equality is False:
            return D08IntegrityFailure("producer_binding_scope_mismatch", b.binding_id,
                                       "producer_consumption_binding")
    return None


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------


def _evaluate_units(typed: D08TypedInput) -> Tuple[List[D08UnitResult],
                                                   Optional[D08IntegrityFailure],
                                                   str]:
    """Family dispatch and cutoff priority (contract sections 4-11)."""
    rule_types = {r.clinical_relationship_type for r in typed.relation_rules}
    owner_domains = {r.owner_domain for r in typed.relation_rules}
    trefs = {t.time_ref_id: t for t in typed.time_refs}
    nodes = typed.record_nodes
    if owner_domains and all(d != "D08" for d in owner_domains):
        return [], None, "consume_only"
    if "integrity_matrix" in rule_types:
        rule = typed.relation_rules[0] if typed.relation_rules else None
        ierr = _global_integrity_error(typed)
        if ierr is not None:
            return [], ierr, "context_only"
        if rule is not None and _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.rule_id, signal="explicit_link_resolve",
                               reason="window_excludes", participants=1)], None, "evaluate_and_own"
        unit_gap: Optional[str] = None
        for n in nodes:
            if n.stable_record_identity.semantic_role == "wrong_semantic_role":
                unit_gap = "rule_role_constraint_violated"
        if unit_gap is None:
            for c in typed.cardinality_specs:
                if c.left_min > c.left_max:
                    unit_gap = "cardinality_invalid_min_gt_max"
        if unit_gap is None:
            for tc in typed.temporal_comparisons:
                status, payload = _feasible_temporal(tc, trefs)
                if status == "error" and payload == "precision_insufficient":
                    unit_gap = "precision_insufficient"
        if unit_gap is not None:
            rule_id = _primary_rule_id(typed)
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason=unit_gap, participants=1)], None, "evaluate_and_own"
        return [], None, "evaluate_and_own"
    # Global ordered pre-evaluator (contract section 5) for EVERY family:
    # snapshot identity, refined single-subject spine, authority locator,
    # node identity/locator/correction chain, routing and producer binding
    # scope.  Producer-coverage, rule-window applicability, multi-subject
    # spine probes and RMB resolve admission stay unit-level for the regular
    # families (frozen oracle: cases 005/016/017/031/040/102/114/155/158/
    # 185/186/210/211; contract section 11).
    ierr = _global_integrity_error(
        typed, include_coverage=False, include_window=False,
        include_spine=False, include_resolve_admission=False,
        only_snapshot_spine=True)
    if ierr is not None:
        return [], ierr, "context_only"
    # Producer coverage is contract stage 3.  Regular families keep its
    # frozen unit-level not_evaluable shape, but it must still win over the
    # later authority/node/routing stages.
    for rule in typed.relation_rules:
        for dom in rule.required_producer_domains:
            matches = [c for c in typed.coverage_status if c.producer_domain == dom]
            if not matches:
                return [_unit_full(
                    l1="not_evaluable", unit_kind="per_left_anchor_slot",
                    rule_id=rule.rule_id, signal="explicit_link_resolve",
                    reason="producer_l0_missing", participants=1,
                )], None, "evaluate_and_own"
            gap = next((c for c in matches
                        if c.l0_status != "covered" or not c.accepted_current), None)
            if gap is not None:
                reason = (f"producer_l0_{gap.l0_status}"
                          if gap.l0_status != "covered"
                          else "producer_not_accepted_current")
                return [_unit_full(
                    l1="not_evaluable", unit_kind="per_left_anchor_slot",
                    rule_id=rule.rule_id, signal="explicit_link_resolve",
                    reason=reason, participants=1,
                )], None, "evaluate_and_own"
    ierr = _global_integrity_error(
        typed, include_coverage=False, include_window=False,
        include_spine=False, include_resolve_admission=False,
        only_snapshot_spine=False)
    if ierr is not None:
        return [], ierr, "context_only"
    # Empty/malformed bundles must never evaluate to a medical outcome.
    if not typed.relation_rules or not typed.record_nodes:
        return [], D08IntegrityFailure("evaluator_admission_empty", "D08",
                                       "expected_set_admission"), "context_only"
    # section 4.1 cutoff priority (non-propagation classes)
    is_propagation = bool(typed.propagation_objects) \
        or "modification_propagation" in rule_types \
        or "modification_propagation_matrix" in rule_types
    cutoff_states = [n.cutoff_decision.decision for n in nodes]
    if not is_propagation and cutoff_states:
        rule = typed.relation_rules[0] if typed.relation_rules else None
        rule_id = _primary_rule_id(typed)
        if "time_missing_not_evaluable" in cutoff_states:
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               cutoff="time_missing_not_evaluable",
                               reason="time_missing_priority", participants=1)], None, "evaluate_and_own"
        if all(state == "out_of_cutoff" for state in cutoff_states):
            return [], None, "evaluate_and_own"
        if any(state == "spans_cutoff" for state in cutoff_states) or len(set(cutoff_states)) > 1:
            return [_unit_full(l1="boundary", unit_kind="routing_or_coverage_gate",
                               rule_id=rule_id, signal="routing_or_coverage_gate",
                               gate="cutoff_boundary_gate", cutoff="mixed_or_spans",
                               reason="cutoff_boundary_gate",
                               participants=len(nodes))], None, "evaluate_and_own"
    # expected-set admission: obligation-side stable identity must exist
    stable_ids = {n.stable_record_identity.stable_record_id for n in nodes}
    for e in typed.observed_edges:
        for side in ("left_stable_identity", "right_stable_identity"):
            value = getattr(e, side)
            if value and value not in stable_ids:
                return [], D08IntegrityFailure("obligation_identity_missing", value,
                                               "expected_set_admission"), "evaluate_and_own"
    if "modification_propagation" in rule_types or "modification_propagation_matrix" in rule_types:
        return _propagation_units(typed), None, "evaluate_and_own"
    if "temporal_impossibility" in rule_types or "temporal_matrix" in rule_types:
        rule = typed.relation_rules[0] if typed.relation_rules else None
        rule_id = _primary_rule_id(typed)
        flip = "temporal_impossibility" in rule_types
        if rule is not None and _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="temporal_impossibility",
                               reason="window_excludes", participants=1)], None, "evaluate_and_own"
        units: List[D08UnitResult] = []
        for tc in typed.temporal_comparisons:
            tv = _temporal_unit(tc, trefs, rule, flip=flip) if rule else {
                "l1": "not_evaluable", "reason": "time_missing",
                "temporal_rel": None, "evidence": 0, "counterevidence": 0}
            units.append(_unit_temporal(rule_id=rule_id, l1=tv["l1"], reason=tv["reason"],
                                        temporal_rel=tv["temporal_rel"],
                                        evidence=tv["evidence"],
                                        counterevidence=tv["counterevidence"]))
        if not units:
            units = [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                                rule_id=rule_id, signal="temporal_impossibility",
                                reason="conserved", participants=2, evidence=1)]
        return units, None, "evaluate_and_own"
    if "identity_collision" in rule_types or "identity_duplicate" in rule_types:
        rule = typed.relation_rules[0] if typed.relation_rules else None
        if rule is not None and _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.rule_id, signal="identity_collision",
                               reason="window_excludes", participants=1)], None, "evaluate_and_own"
        return [_identity_unit(typed)], None, "evaluate_and_own"
    if "raw_materialized_resolve" in rule_types:
        rule = typed.relation_rules[0] if typed.relation_rules else None
        if rule is not None and _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.rule_id, signal="explicit_link_resolve",
                               reason="window_excludes", participants=1)], None, "evaluate_and_own"
        anomaly = _resolve_anomaly(typed)
        if anomaly is not None:
            return [anomaly], None, "evaluate_and_own"
        if not typed.raw_links and not typed.resolve_decisions:
            if _has_relation_obligation(typed):
                return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                   rule_id=rule.rule_id, signal="explicit_link_resolve",
                                   reason="bijection_broken_no_raw", evidence=1,
                                   participants=2)], None, "evaluate_and_own"
            return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                               rule_id=rule.rule_id, signal="explicit_link_resolve",
                               reason="bijection_conserved", evidence=1,
                               participants=2)], None, "evaluate_and_own"
        resolved_raw_ids = {decision.raw_link_id for decision in typed.resolve_decisions}
        if any(raw.raw_link_id not in resolved_raw_ids for raw in typed.raw_links):
            return [_unit_full(
                l1="not_evaluable", unit_kind="per_left_anchor_slot",
                rule_id=rule.rule_id, signal="explicit_link_resolve",
                reason="resolve_decision_missing", participants=2,
            )], None, "evaluate_and_own"
        for res in typed.resolve_decisions:
            raw = next((r for r in typed.raw_links if r.raw_link_id == res.raw_link_id), None)
            if raw is not None and res.status == "unique":
                materialized = list(res.materialized_record_node_ids)
                target = raw.idvarval
                if materialized and target and target not in materialized:
                    return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                                       rule_id=rule.rule_id, signal="explicit_link_resolve",
                                       resolve="unique", reason="operands_identity_mismatch",
                                       participants=2)], None, "evaluate_and_own"
        if typed.duplicate_policies:
            dup = typed.duplicate_policies[0]
            if dup.raw_materialized_mirror_exemption:
                return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                                   rule_id=rule.rule_id, signal="explicit_link_resolve",
                                   reason="mirror_exemption", evidence=1,
                                   counterevidence=1, participants=2)], None, "evaluate_and_own"
        return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                           rule_id=rule.rule_id, signal="explicit_link_resolve",
                           reason="bijection_conserved", evidence=1,
                           participants=2)], None, "evaluate_and_own"
    # link / reverse / fanout / routing
    rule = typed.relation_rules[0] if typed.relation_rules else None
    rule_id = _primary_rule_id(typed)
    if typed.relation_payload_status == "wrong_subject_or_site":
        return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="wrong_subject_payload_fail_closed",
                           participants=2)], None, "evaluate_and_own"
    route = typed.owner_route
    if route is not None and route.candidate_problem_kind == "routing_ambiguity":
        return [_unit_full(l1="not_evaluable", unit_kind="routing_or_coverage_gate",
                           rule_id=rule_id, signal="routing_or_coverage_gate",
                           gate="routing_ambiguity_gate", reason="routing_ambiguity",
                           participants=1)], None, "evaluate_and_own"
    if rule is not None and _rule_window_excludes(rule, trefs):
        return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="window_excludes", participants=1)], None, "evaluate_and_own"
    subs = {n.stable_record_identity.subject_ref for n in nodes}
    if len(subs) > 1 and "identity_collision" not in rule_types:
        return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="cross_scope_edge", participants=2)], None, "evaluate_and_own"
    node_ids = {n.record_node_id for n in nodes}
    for jump in typed.source_jump_registry:
        target = jump.target_object_id
        if jump.target_kind == "record_node" and target not in node_ids:
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="source_jump_target_missing",
                               participants=2)], None, "evaluate_and_own"
    vis = typed.visibility_decision
    if vis is not None and vis.audience_anchor_rule == "ambiguous":
        return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="audience_anchor_ambiguous",
                           participants=2)], None, "evaluate_and_own"
    if typed.fanout_candidate_sets:
        f = typed.fanout_candidate_sets[0]
        cands = list(f.candidate_identities)
        cap = int(f.max_unidentified_fanout or 0)
        if not f.has_unique_identity_or_relid and len(cands) > cap:
            return [_unit_full(l1="not_evaluable", unit_kind="routing_or_coverage_gate",
                               rule_id=rule_id, signal="identity_fanout_exceeded",
                               gate="identity_fanout_exceeded", reason="fanout_exceeded",
                               participants=len(nodes))], None, "evaluate_and_own"
    if typed.rel_instance_memberships:
        for mem in typed.rel_instance_memberships:
            fwd_edges = [e for e in typed.observed_edges
                         if e.explicit_rel_instance_id == mem.rel_instance_id
                         and e.direction != "reverse"]
            rev_edges = [e for e in typed.observed_edges
                         if e.explicit_rel_instance_id == mem.rel_instance_id
                         and e.direction == "reverse"]
            rev_pairs = {(e.left_stable_identity, e.right_stable_identity)
                         for e in rev_edges}
            missing = [e for e in fwd_edges
                       if (e.right_stable_identity, e.left_stable_identity) not in rev_pairs]
            # conservation also requires the forward/reverse counts to be
            # equal: duplicate or extra reverse edges break the bijection
            count_imbalanced = len(fwd_edges) != len(rev_edges)
            member_node_ids = {
                n.record_node_id for n in nodes
                if n.stable_record_identity.stable_record_id in set(mem.member_ids)
            }
            bijection_invalid = (
                set(mem.raw_link_bijection) != set(mem.raw_link_ids)
                or len(set(mem.raw_link_bijection.values())) != len(mem.raw_link_bijection)
                or set(mem.raw_link_bijection.values()) != member_node_ids
            )
            w = _waiver_closure(typed)
            if missing or count_imbalanced or bijection_invalid or (w["state"] == "full_set" and w["refs"]
                                               and not all(r in stable_ids for r in w["refs"])):
                return [_unit_full(l1="positive", unit_kind="per_explicit_rel_instance",
                                   rule_id=rule_id, signal="explicit_link_resolve",
                                   reason="rel_instance_reverse_missing", evidence=1,
                                   participants=len(mem.member_ids))], None, "evaluate_and_own"
            return [_unit_full(l1="negative", unit_kind="per_explicit_rel_instance",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="rel_instance_conserved", evidence=1,
                               participants=len(mem.member_ids))], None, "evaluate_and_own"
    w = _waiver_closure(typed)
    if w["state"] == "full_set" and w["refs"]:
        if not all(r in stable_ids for r in w["refs"]):
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="waiver_closure_unprovable",
                               participants=2)], None, "evaluate_and_own"
    return _link_units(typed), None, "evaluate_and_own"


def _l0_complete(typed: D08TypedInput) -> bool:
    for rule in typed.relation_rules:
        for dom in rule.required_producer_domains:
            matches = [c for c in typed.coverage_status if c.producer_domain == dom]
            if not matches or any(c.l0_status != "covered" or not c.accepted_current
                                  for c in matches):
                return False
    return True


def evaluate(typed: D08TypedInput) -> D08RunResult:
    """Evaluate one typed bundle to the full deterministic run result.

    Raises :class:`D08ContractError` on a malformed bundle; otherwise the
    result always carries the expected-set units, the first integrity
    failure (or none) and the audience projection.
    """
    if not isinstance(typed, D08TypedInput):
        raise D08ContractError("evaluate requires a D08TypedInput")
    validate_typed_input(typed)
    units, ierr, d08_action = _evaluate_units(typed)
    positive = sum(1 for u in units if u.l1_disposition == "positive")
    l0_complete = _l0_complete(typed)
    route = typed.owner_route
    owner_domain: Optional[str] = (
        "D08" if d08_action != "consume_only"
        else (route.owner_domain if route else None))
    risk_owner = "D08" if positive and ierr is None else None
    query_owner = "D08" if positive and ierr is None else None
    risk_candidate_present = positive > 0 and ierr is None
    vis = typed.visibility_decision
    blinded = set(vis.blinded_node_ids) if vis else set()
    forbidden = set(vis.forbidden_node_ids) if vis else set()
    hidden = blinded | forbidden
    # Audience projection subtracts hidden nodes before every payload: a
    # node that is simultaneously projectable and blinded/forbidden is a
    # typed-input conflict -- the leak is flagged and the node is never
    # exposed.  The internal evaluation/join result is untouched.
    if vis is None:
        projectable: Tuple[str, ...] = ()
        evaluation: Tuple[str, ...] = ()
        disclosure_leak = False
    else:
        raw_projectable = list(vis.projectable_node_set)
        disclosure_leak = bool(set(raw_projectable) & hidden)
        projectable = tuple(nid for nid in raw_projectable if nid not in hidden)
        evaluation = tuple(vis.evaluation_node_set)
    query_draft_present = risk_candidate_present and bool(projectable)
    query_present = bool(positive and projectable)
    handoffs = [u for u in units if u.lineage_handoff]
    node_ids = {n.record_node_id for n in typed.record_nodes}
    visible_node_ids = set(projectable)
    visible_loc_ids = {
        locator_id
        for node in typed.record_nodes if node.record_node_id in visible_node_ids
        for locator_id in node.source_locator_ids
    }
    jumps: List[D08SourceJumpTarget] = []
    for jump in typed.source_jump_registry:
        target = jump.target_object_id
        kind = jump.target_kind
        if kind == "record_node":
            if target not in visible_node_ids:
                continue
            resolvable = target in node_ids
        else:
            if target not in visible_loc_ids:
                continue
            resolvable = target in visible_loc_ids
        jumps.append(D08SourceJumpTarget(jump.jump_target_id, kind, target, resolvable))
    bindings = tuple(b.binding_id for b in typed.producer_consumption_bindings)
    return D08RunResult(
        units=tuple(units),
        integrity_error=ierr,
        d08_action=d08_action,
        owner_domain=owner_domain,
        risk_owner=risk_owner,
        query_owner=query_owner,
        risk_candidate_present=risk_candidate_present,
        query_draft_present=query_draft_present,
        downstream_handoff_present=bool(handoffs),
        handoff_target_domain="D09" if handoffs else None,
        l0_complete=l0_complete,
        projectable_node_set=projectable,
        evaluation_node_set=evaluation,
        hidden_node_count=len(hidden),
        audience_anchor=projectable[0] if projectable else None,
        audience_payload_present=bool(projectable),
        query_present=query_present,
        journey_marker_present=query_present,
        risk_present=bool(positive),
        producer_binding_ids=bindings,
        reverse_binding_count=len(bindings),
        source_jump_target_pairs=tuple(jumps),
        disclosure_leak_present=disclosure_leak,
        audience_lexicon_ref=(
            typed.audience_lexicon.lexicon_id if typed.audience_lexicon else None),
        stable_node_identities=tuple(sorted(
            {n.stable_record_identity.stable_record_id for n in typed.record_nodes})),
        observed_edge_ids=tuple(sorted(e.edge_id for e in typed.observed_edges)),
        bidirectional_join_count=len(typed.bidirectional_joins),
        reverse_conservation_ok=_join_conserved(typed),
    )
