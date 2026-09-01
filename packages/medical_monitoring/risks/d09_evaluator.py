"""R4-D09 deterministic center-pattern evaluator (worker_01).

Implements the frozen D09 v0.5 contract decision engine (contract sections
3.3/8/9) over the closed typed envelope of ``d09_contracts.py``:

* contract-ordered fail-closed: pre-admission identity/authority/expected-set
  failure emits only the global gate and zero medical units; post-admission
  required producer/denominator/opportunity/origin/window defects emit one
  ``not_evaluable`` unit and no risk/query payload;
* the three ownable token-kind bijections and all consume/handoff/context/
  routing owner paths (no D10/cross-site or efficacy-rate ownership);
* stable cores, exact member/origin dedup, separated subject/event/gap/
  individual/center/clue/query counts, coverage, counterevidence and the
  five L1 dispositions; n=1 repeated risk is boundary, closed-zero negative
  gates and design-clause not-applicable are exact;
* deterministic replay: same immutable typed content always yields the same
  result (no wall clock, no randomness, no ordering dependence).

Clean-semantics boundary (worker_01 corrective pass 2026-08-15): every
decisive branch consumes explicit closed typed facts of the envelope --
resolved authority decision, method/comparability decision, lineage context,
query redundancy decision, producer source-verification records and
per-member locator/anchor resolution states -- or existing typed facts
(coverage, blind status + stratum key, cutoff, origins, counterevidence
refs, windows, denominators, opportunities).  This module never reads the
envelope's opaque audit/test metadata, never branches on case/fixture/test
identifiers or expected leaves, and never interprets synthetic sentinels,
substrings, display labels, prose descriptions or content-hash conventions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from .d09_contracts import (
    D09ContractError,
    D09RunResult,
    D09TraceEdge,
    D09TypedInput,
    D09UnitResult,
    TREATMENT_STRATUM_KEYS,
    d09_unit_stable_core,
    validate_typed_input,
)


def _risk_facts(member: Any) -> Tuple[str, str, str, str, str, str, str, str, str]:
    """(member_id, subject, event, risk_kind, domain, origin, cutoff, locator,
    public_r4_risk_identity) for one accepted risk member."""
    locator = member.source_locator_refs[0] if member.source_locator_refs else ""
    return (member.member_id, member.subject_stable_id,
            member.source_event_identity, member.risk_kind,
            member.producer_domain, member.origin_decision,
            member.cutoff_relation, locator, member.public_r4_risk_identity)


def _counterevidence_level(typed: D09TypedInput) -> str:
    """Counterevidence explanation level from declared vs matched rule refs
    (contract section 3.2 input facts; both are typed reference sets)."""
    declared = set(typed.pattern_definition.counterevidence_rule_refs)
    matched = set(typed.matched_counterevidence_rule_refs)
    if not declared:
        return "condition_absent"
    if not matched:
        return "none"
    if matched == declared:
        return "full"
    return "partial"


def _journey_marker_present(typed: D09TypedInput) -> bool:
    """Journey/one-hop expansion marker (contract section 11): any risk
    member, any gap member with resolved visit/time anchors, or any
    change-ledger member."""
    if typed.subject_risk_members:
        return True
    if typed.change_ledger_members:
        return True
    return any(
        bool(member.visit_or_time_anchor_refs)
        and member.anchor_resolution_state == "resolved"
        for member in typed.gap_members)


def _deep_link_deficient(typed: D09TypedInput) -> bool:
    """No locatable one-hop source jump target (contract section 11): an
    unresolved member source locator or an unresolved gap visit/time anchor,
    both explicit closed typed facts."""
    for member in typed.subject_risk_members:
        if member.source_locator_resolution_state != "locatable":
            return True
    for member in typed.gap_members:
        if member.source_locator_resolution_state != "locatable":
            return True
        if member.anchor_resolution_state != "resolved":
            return True
    return False


def _all_members_locatable(typed: D09TypedInput) -> bool:
    """All member source locators resolve (contract section 10/14)."""
    for member in typed.subject_risk_members:
        if member.source_locator_resolution_state != "locatable":
            return False
    for member in typed.gap_members:
        if member.source_locator_resolution_state != "locatable":
            return False
    return True


# ---------------------------------------------------------------------------
# Numerator / count semantics (contract sections 5.2/6.2)
# ---------------------------------------------------------------------------


def _numerator(typed: D09TypedInput) -> Tuple[int, int, int, int]:
    """(individual_risk_count, affected_subjects, events, gap_opportunities).

    Members dedup by (public_r4_risk_identity, subject_stable_id) when any
    member carries ``verified_same_origin`` (the D08-verified same-origin
    binding is an input fact); the in-cutoff filter applies to the deduped
    member set.  Out-of-cutoff members stay in individual_risk_count as
    context but never count as affected/events.  Gap members count one
    missing opportunity each; trend members count unique change subjects.
    """
    kind = typed.pattern_definition.pattern_kind
    if kind == "repeated_subject_risk":
        rows = [_risk_facts(member) for member in typed.subject_risk_members]
        if any(r[5] == "verified_same_origin" for r in rows):
            seen: Dict[Tuple[str, str], List[str]] = {}
            for r in rows:
                seen.setdefault((r[8], r[1]), r)
            deduped = list(seen.values())
            in_members = [(r[1], r[2]) for r in deduped if r[6] == "in_cutoff"]
            return (len(deduped), len({m[0] for m in in_members}),
                    len({m[1] for m in in_members}), 0)
        in_members = [(r[1], r[2]) for r in rows if r[6] == "in_cutoff"]
        return len(rows), len({m[0] for m in in_members}), len({m[1] for m in in_members}), 0
    if kind == "systematic_data_or_process_gap":
        return 0, len({member.subject_stable_id
                       for member in typed.gap_members}), 0, len(typed.gap_members)
    if kind == "within_site_time_trend":
        return 0, len({member.subject_stable_id
                       for member in typed.change_ledger_members}), 0, 0
    return 0, 0, 0, 0


def _member_pairs(typed: D09TypedInput) -> Tuple[Tuple[str, str], ...]:
    """Sorted (member_ref, first_locator) pairs over all members with a
    locator (contract sections 5.2/10 evidence expansion)."""
    pairs: List[Tuple[str, str]] = []
    for member in typed.subject_risk_members:
        if member.source_locator_refs:
            pairs.append((member.member_id, member.source_locator_refs[0]))
    for member in typed.gap_members:
        if member.source_locator_refs:
            pairs.append((member.member_id, member.source_locator_refs[0]))
    for member in typed.change_ledger_members:
        if member.source_locator_refs:
            pairs.append((member.member_id, member.source_locator_refs[0]))
    return tuple(sorted(pairs, key=lambda pair: (pair[0], pair[1])))


def _evidence_locators(typed: D09TypedInput) -> Tuple[str, ...]:
    """Sorted unique member source locators (contract section 10 evidence
    node set)."""
    out: Set[str] = set()
    for member in typed.subject_risk_members:
        if member.source_locator_refs:
            out.add(member.source_locator_refs[0])
    for member in typed.gap_members:
        if member.source_locator_refs:
            out.add(member.source_locator_refs[0])
    for member in typed.change_ledger_members:
        if member.source_locator_refs:
            out.add(member.source_locator_refs[0])
    return tuple(sorted(out))


def _producer_binding_ids(typed: D09TypedInput) -> Tuple[str, ...]:
    """Sorted unique coverage locator ids (contract section 4 producer
    consumption bindings)."""
    out: Set[str] = set()
    for coverage in typed.coverage:
        out.update(coverage.coverage_locator_ids)
    return tuple(sorted(out))


def _owner_domain(typed: D09TypedInput) -> str:
    """Contract section 2.1 owner routing: only the three ownable tokens can
    evaluate and own; all other tokens route to their origin owner."""
    if typed.pattern_definition.d09_action == "evaluate_and_own":
        return "D09"
    token = typed.pattern_definition.clinical_claim_token
    if token.startswith("d06_"):
        return "D06"
    if token.startswith("d10_"):
        return "D10"
    if token == "d01_d08_individual_fact":
        return "D01-D08"
    return "unresolved"


def _query_generated(typed: D09TypedInput, disposition: str) -> bool:
    """Contract section 12: at most one Query draft per positive pattern unit,
    only when the resolved redundancy decision allows it and the resolvable
    member list stays within the resolved fanout limit."""
    if disposition != "positive":
        return False
    decision = typed.query_redundancy_decision
    if decision.decision != "site_process_delta_present":
        return False
    if not decision.uncovered_member_refs:
        return False
    kind = typed.pattern_definition.pattern_kind
    if kind == "repeated_subject_risk":
        member_count = len(typed.subject_risk_members)
    elif kind == "systematic_data_or_process_gap":
        member_count = len(typed.gap_members)
    else:
        member_count = len(typed.change_ledger_members)
    return member_count <= decision.max_query_member_fanout


# ---------------------------------------------------------------------------
# Disposition engine (contract sections 3.3/8/9, exact order)
# ---------------------------------------------------------------------------


def _derive_disposition(typed: D09TypedInput) -> Tuple[str, str, Dict[str, Any]]:
    """Return (disposition, primary_reason, extra).

    ``extra`` may carry ``zero_unit`` / ``gate`` / ``pair_state`` for
    control-plane (zero medical unit) outcomes.
    """
    kind = typed.pattern_definition.pattern_kind
    expected_set = typed.expected_set

    # -- zero-unit control-plane paths (contract sections 3.3/8.1/15) --
    if expected_set.expected_set_state != "admitted":
        gate = (expected_set.admission_gate.gate_kind
                if expected_set.admission_gate else None)
        return "not_applicable", "routed_or_gated", {
            "zero_unit": True, "gate": gate or expected_set.expected_set_state,
        }
    if kind == "within_site_time_trend":
        windows = typed.analysis_windows
        window_kinds = {window.window_kind for window in windows}
        if len(windows) < 2:
            return "not_applicable", "window_pair_gate", {
                "zero_unit": True, "gate": "window_pair_gate",
                "pair_state": "insufficient_windows",
            }
        if len(window_kinds) > 1:
            return "not_applicable", "window_pair_gate", {
                "zero_unit": True, "gate": "window_pair_gate",
                "pair_state": "incomparable_windows",
            }

    # -- admitted-unit integrity gates (contract section 8.2 order 1-6) --
    if typed.cutoff.cutoff_identity_state == "conflict":
        return "not_evaluable", "cutoff_conflict", {}
    required_domains = set(typed.pattern_definition.required_producer_domains)
    coverage_by_domain: Dict[str, Tuple[str, str, bool]] = {}
    for coverage in typed.coverage:
        coverage_by_domain[coverage.producer_domain] = (
            coverage.l0_status, coverage.l1_medical_completeness_state,
            coverage.accepted_current)
    for domain in sorted(required_domains):
        l0, l1, accepted = coverage_by_domain.get(
            domain, ("missing", "missing", True))
        if l0 != "covered" or l1 != "complete":
            return "not_evaluable", "coverage_hole", {"domain": domain}
        if not accepted:
            return "not_evaluable", "producer_ref_unresolvable", {}
    # Contract section 4: producer content verification (explicit records).
    if any(record.verification_state != "verified"
           for record in typed.source_verification_records):
        return "not_evaluable", "source_hash_mismatch", {}
    if typed.stratum.stratum_admission == "rejected_empty":
        return "not_evaluable", "stratum_required_empty", {}
    # Contract section 8.2 order 3 / section 9: resolved authority validity.
    if typed.resolved_authority_decision.authority_validity_state == "invalid":
        return "not_evaluable", "authority_fail", {}
    if typed.mode_contract_design_clause_ref:
        return "not_applicable", "design_not_applicable", {}
    if typed.denominator.denominator_state == "unclosed":
        return "not_evaluable", "denominator_unclosed", {}
    if typed.denominator.denominator_state == "closed_zero":
        return "not_evaluable", "denominator_closed_zero", {}
    if typed.opportunity.opportunity_provenance in (
            "raw_listing_only", "enumeration_conflict"):
        return "not_evaluable", "opportunity_provenance", {}
    if typed.opportunity.opportunity_state == "unknown":
        return "not_evaluable", "opportunity_unknown", {}
    origins = {member.origin_decision
               for member in typed.subject_risk_members}
    if "wrong_scope" in origins:
        return "not_evaluable", "origin_wrong_scope", {}
    if "not_evaluable" in origins:
        return "not_evaluable", "origin_not_evaluable", {}
    if "ambiguous" in origins:
        return "boundary", "origin_ambiguous", {}
    # Contract section 7.3: blinded projects must not use treatment-group /
    # treatment-role stratum keys (closed typed fact on the envelope).
    if (typed.visibility_decision.blind_status == "blinded"
            and typed.stratum.stratum_key in TREATMENT_STRATUM_KEYS):
        return "not_evaluable", "blinded_stratum_rejected", {}
    # Contract section 7.2: merged/split center identity is never comparable.
    if typed.lineage_context.site_identity_state in ("merged", "split"):
        return "not_evaluable", "site_merge_split", {}
    # Contract section 7.3: method validity preconditions not satisfied.
    if typed.method_comparability_decision.method_validity_state == "insufficient":
        return "not_evaluable", "validity_insufficient", {}
    # Contract section 11: unresolved locator/anchor -> no fabricated jump.
    if _deep_link_deficient(typed):
        return "boundary", "deep_link_deficient", {}
    # Contract section 7.3: hidden/visible rate mix -> qualified display.
    if typed.visibility_decision.rate_projection_state == "qualified":
        return "boundary", "visibility_qualified", {}

    # -- kind-specific medical rules (contract section 9) --
    if kind == "repeated_subject_risk":
        true_cutoffs = [member.cutoff_relation
                        for member in typed.subject_risk_members]
        if true_cutoffs and all(c == "out_of_cutoff" for c in true_cutoffs):
            return "not_evaluable", "cutoff_all_out", {}
        if any(c == "spans_cutoff" for c in true_cutoffs):
            return "boundary", "cutoff_spans", {}
        if any(c == "time_missing_not_evaluable" for c in true_cutoffs):
            return "not_evaluable", "time_missing", {}
        in_subjects = {member.subject_stable_id
                       for member, cutoff in zip(
                           typed.subject_risk_members, true_cutoffs)
                       if cutoff == "in_cutoff"}
        if len(in_subjects) == 0:
            return "negative", "closed_zero_no_members", {}
        # Contract section 9: resolved ModeContract minimum; never below 2.
        min_count = typed.resolved_authority_decision.minimum_member_subject_count
        if min_count is None:
            raise D09ContractError(
                "resolved minimum_member_subject_count is required")
        if len(in_subjects) < min_count:
            return "boundary", "n1_minimum", {}
        level = _counterevidence_level(typed)
        if level == "full":
            return "negative", "counterevidence_explains", {}
        if level == "partial":
            return "boundary", "counterevidence_partial", {}
        # Contract section 5.1/13: rule/method supersession lineage fact.
        if typed.lineage_context.lineage_relation == (
                "superseded_by_rule_or_method_change"):
            return "boundary", "rule_supersession", {}
        # Contract section 7.3: statistics alone cannot set L1; signals must
        # expand to member sources.
        if typed.method_comparability_decision.statistical_signal_role == (
                "sole_evidence"):
            return "boundary", "statistics_only", {}
        if typed.method_comparability_decision.member_expansion_state == (
                "unexpandable"):
            return "boundary", "signal_unexpandable", {}
        if typed.denominator.denominator_kind in ("subject_time", "exposure_time"):
            return "boundary", "short_exposure", {}
        if any(window.anchor_kind == "site_activation"
               for window in typed.analysis_windows):
            return "boundary", "late_activation", {}
        return "positive", "min_member_subject_count_satisfied", {}

    if kind == "systematic_data_or_process_gap":
        semantic_missing = (0 if _counterevidence_level(typed) == "full"
                            else len(typed.gap_members))
        if typed.opportunity.opportunity_state == "insufficient":
            if len(typed.gap_members) > 0:
                return "boundary", "opportunity_insufficient", {}
            return "not_evaluable", "opportunity_insufficient", {}
        if semantic_missing == 0:
            return "negative", "closed_zero_no_members", {}
        minimum = (typed.resolved_authority_decision
                   .gap_positive_minimum_opportunity_count)
        if minimum is None:
            raise D09ContractError(
                "resolved gap_positive_minimum_opportunity_count is required")
        if typed.opportunity.expected_opportunity_count < minimum:
            return "boundary", "small_sample", {}
        return "positive", "accepted_gap_opportunity_sufficient", {}

    if kind == "within_site_time_trend":
        if not typed.change_ledger_members:
            return "negative", "closed_zero_no_members", {}
        comparable_states = {member.comparable_state
                             for member in typed.change_ledger_members}
        change_kinds = {member.change_kind
                        for member in typed.change_ledger_members}
        if "not_evaluable" in comparable_states or "not_comparable" in change_kinds:
            # Contract section 7.2/7.3: incomparable windows never show a
            # false improvement/deterioration; the reason is a resolved fact.
            method = typed.method_comparability_decision
            if method.method_validity_state == "insufficient":
                return "not_evaluable", "validity_insufficient", {}
            if typed.lineage_context.carry_forward_state == "active":
                return "not_evaluable", "carry_forward", {}
            if len(set(method.window_rule_version_refs)) > 1:
                return "boundary", "window_definition_change", {}
            if typed.lineage_context.lineage_relation == (
                    "superseded_by_rule_or_method_change"):
                return "boundary", "rule_supersession", {}
            if len(set(method.stratum_method_version_refs)) > 1:
                return "not_evaluable", "stratum_change", {}
            return "boundary", "not_comparable", {}
        causes = {member.change_cause
                  for member in typed.change_ledger_members}
        if causes & {"coverage", "denominator", "method",
                     "rule_or_mapping", "mixed"}:
            return "boundary", "explained_change", {}
        subjects = {member.subject_stable_id
                    for member in typed.change_ledger_members}
        minimum = (typed.resolved_authority_decision
                   .trend_positive_minimum_subject_count)
        if minimum is None:
            raise D09ContractError(
                "resolved trend_positive_minimum_subject_count is required")
        if len(subjects) < minimum:
            return "boundary", "small_sample", {}
        return "positive", "comparable_windows_change_ledger", {}

    raise D09ContractError(f"unknown pattern kind {kind!r}")


# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------


def _l0_complete(typed: D09TypedInput) -> bool:
    required = set(typed.pattern_definition.required_producer_domains)
    return all(coverage.l0_status == "covered"
               for coverage in typed.coverage
               if coverage.producer_domain in required)


def _domain_complete(typed: D09TypedInput) -> bool:
    required = set(typed.pattern_definition.required_producer_domains)
    return all(coverage.l1_medical_completeness_state == "complete"
               for coverage in typed.coverage
               if coverage.producer_domain in required)


def _trace_edges(typed: D09TypedInput) -> Tuple[D09TraceEdge, ...]:
    return tuple(
        D09TraceEdge(edge_index=index, member_ref=pair[0], locator_ref=pair[1])
        for index, pair in enumerate(_member_pairs(typed), start=1))


def evaluate(typed: D09TypedInput) -> D09RunResult:
    """Evaluate one typed bundle to the complete deterministic run result.

    Validation is enforced at this public boundary.  The result is fully
    deterministic: same immutable typed content always produces the
    same run result.  Audit/test metadata on the envelope is never read.
    """
    validate_typed_input(typed)
    disposition, reason, extra = _derive_disposition(typed)
    zero_unit = bool(extra.get("zero_unit"))
    unit_count = 0 if zero_unit else 1
    kind = typed.pattern_definition.pattern_kind or ""
    individual_risk, affected, events, gap_opps = _numerator(typed)
    evidence = _evidence_locators(typed)
    source_record_count = len(evidence)
    risk_count = 1 if disposition == "positive" else 0
    clue_count = 1 if disposition == "boundary" else 0
    query_count = 1 if _query_generated(typed, disposition) else 0
    center_pattern_count = risk_count
    # Contract section 8.2/10: a prior D09 risk under a broken current run
    # carries forward (lineage handoff) instead of being closed; positives
    # hand off their new RiskInstance to R2.
    downstream_handoff = (disposition == "positive"
                          or typed.lineage_context.carry_forward_state == "active")
    # Contract section 5.1/13: supersession is an explicit lineage fact.
    superseded_count = 1 if typed.lineage_context.lineage_relation == (
        "superseded_by_rule_or_method_change") else 0
    gate = extra.get("gate")
    window_pair_state = extra.get("pair_state")
    admission_gate_kind = (typed.expected_set.admission_gate.gate_kind
                           if typed.expected_set.expected_set_state != "admitted"
                           and typed.expected_set.admission_gate else None)

    units: Tuple[D09UnitResult, ...] = ()
    if unit_count:
        units = (D09UnitResult(
            stable_core=d09_unit_stable_core(typed),
            l1_disposition=disposition,
            pattern_kind=kind,
            primary_reason=reason,
            participant_count=affected if disposition in ("positive", "boundary") else 0,
            event_count=events if disposition in ("positive", "boundary") else 0,
            gap_opportunity_count=gap_opps if disposition in ("positive", "boundary") else 0,
            individual_risk_count=individual_risk,
            risk_count=risk_count,
            clue_count=clue_count,
            query_count=query_count,
            evidence_count=source_record_count,
            counterevidence_count=len(typed.matched_counterevidence_rule_refs),
            lineage_handoff=downstream_handoff,
        ),)

    return D09RunResult(
        typed=typed,
        disposition=disposition,
        primary_reason=reason,
        integrity_stage=typed.expected_set.expected_set_state,
        admission_gate_kind=admission_gate_kind,
        window_pair_gate_present=(
            disposition == "not_applicable"
            and extra.get("gate") == "window_pair_gate"),
        window_pair_state=window_pair_state,
        gate_count=1 if (zero_unit and gate) else 0,
        open_gate_count=1 if (zero_unit and gate) else 0,
        owner_domain=_owner_domain(typed),
        d09_action=typed.pattern_definition.d09_action,
        l0_complete=_l0_complete(typed),
        domain_complete=_domain_complete(typed),
        unit_count=unit_count,
        positive_count=1 if disposition == "positive" else 0,
        negative_count=1 if disposition == "negative" else 0,
        boundary_count=1 if disposition == "boundary" else 0,
        not_applicable_count=1 if disposition == "not_applicable" else 0,
        not_evaluable_count=1 if disposition == "not_evaluable" else 0,
        individual_risk_count=individual_risk if unit_count else 0,
        affected_subject_count=affected if (
            unit_count and disposition in ("positive", "boundary")) else 0,
        event_count=events if (
            unit_count and disposition in ("positive", "boundary")) else 0,
        gap_opportunity_count=gap_opps if (
            unit_count and disposition in ("positive", "boundary")) else 0,
        center_pattern_count=center_pattern_count,
        clue_count=clue_count,
        query_count=query_count,
        risk_count=risk_count,
        source_record_count=source_record_count,
        denominator_kind=typed.denominator.denominator_kind,
        denominator_value=typed.denominator.denominator_value,
        denominator_state=typed.denominator.denominator_state,
        opportunity_expected=typed.opportunity.expected_opportunity_count,
        opportunity_observed=typed.opportunity.observed_opportunity_count,
        opportunity_missing=max(0, typed.opportunity.expected_opportunity_count
                                - typed.opportunity.observed_opportunity_count),
        opportunity_state=typed.opportunity.opportunity_state,
        downstream_handoff=downstream_handoff,
        handoff_target_domain="R2" if downstream_handoff else None,
        superseded_unit_count=superseded_count,
        journey_marker_present=_journey_marker_present(typed),
        all_members_locatable=_all_members_locatable(typed),
        units=units,
        trace_edges=_trace_edges(typed),
        evidence_locators=evidence,
        member_pairs=_member_pairs(typed),
        hidden_member_refs=tuple(sorted(set(
            typed.visibility_decision.hidden_member_refs))),
        producer_binding_ids=_producer_binding_ids(typed),
    )
