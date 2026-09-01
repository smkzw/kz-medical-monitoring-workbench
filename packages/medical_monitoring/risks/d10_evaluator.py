"""R4-D10 deterministic project/cross-site signal evaluator (worker_01).

Implements the frozen D10 v0.6 contract decision engine (contract sections
2.1/3.3/6/7/8/9/10/13/14) over the closed typed envelope of
``d10_contracts.py``:

* contract-ordered fail-closed: routing/owner/legal-matrix/identity/expected-
  set failure emits only the corresponding gate and zero medical units;
  integrity failures (tamper, algebra, set violations) emit the global
  integrity gate; admitted units with required completeness defects emit one
  ``not_evaluable`` unit; comparison/window admission failures emit their
  control-plane gates;
* the five ownable token/kind routes and all consume/handoff/routing paths;
* exact numerator layer separation, denominator recompute, change-cause
  derivation, visibility algebra, query redundancy, and the five L1
  dispositions with fixed precedence;
* deterministic replay: same immutable typed content always yields the same
  result (no wall clock, no randomness, no ordering dependence).

Clean-semantics boundary (worker_01): every decisive branch consumes explicit
closed typed fields of the envelope -- signal definition/legal row, scope
binding, expected set, source revision pairs, rule hit state and evidence
sources, counterevidence refs, coverage, denominator + recomputed value, time
segments, opportunity, analysis population, change decision + cutoff advance,
visibility decision, query decision, safety/efficacy contexts, measure-origin
binding, model evidence, evaluation limits, comparison/window gates, hotspot.
This module never reads the envelope's opaque audit/test metadata, never
branches on case/fixture/test identifiers, never interprets ``SYN-*`` strings,
descriptions, display labels or synthetic revision-hash conventions, and never
imports/reads artifact files, generators, the oracle, the registry, the quota
manifest, the verifier or tests.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple

from .d10_contracts import (
    ALLOWED_CREATE_LINEAGES,
    BOUNDARY_COMP_CODES,
    CHANGE_KIND_FORBIDDEN_FOR_NON_DATA,
    CONSUME_ONLY_TOKENS,
    D10EvaluationAuthority,
    D10TypedInput,
    DEN_KIND_ESTIMATE,
    GATE_DISPOSITIONS,
    HANDOFF_ONLY_TOKENS,
    NOT_EVALUABLE_COMP_CODES,
    NON_DATA_CAUSE_KEYS,
    OWNED_TOKENS,
    STIGMA_CODES,
    UNRESOLVED_TOKEN,
    d10_canonical_json,
    d10_content_hash,
    d10_normalize_nfc,
    d10_sha256_text,
    d10_unit_stable_core,
    validate_typed_input,
)
from .d10_results import (
    D10ForbiddenLeaf,
    D10GateResult,
    D10RunResult,
    D10SourceLeaf,
    D10TraceLeaf,
    D10UnitResult,
)

# Frozen audience contract forbidden internal terms (contract section 12);
# carried here as the closed typed template vocabulary of the frozen contract.
_FORBIDDEN_AUDIENCE_TERMS = (
    "正式安全性信号", "确证治疗效果", "优效", "非劣", "获益-风险裁决",
    "中心质量差", "中心质量好", "typed handoff", "candidate",
)
_FULLWIDTH_LATIN = frozenset(
    list(range(0xFF10, 0xFF1A)) + list(range(0xFF21, 0xFF3B))
    + list(range(0xFF41, 0xFF5B)))
_INVISIBLE_CHARS = frozenset("\u200b\u200c\u200d\u2060\ufeff")
_ENGINEERING_KEY_RE = re.compile(
    r"(pattern|rule|mode|window|revision|scope|policy|hash|id|ref)"
    r"([a-z0-9_-]*)", re.IGNORECASE)

# Cause names keyed by the non-data change ref-set counters (contract 14).
_CAUSE_BY_KEY = {
    "denom_n": "denominator",
    "coverage_n": "coverage",
    "knowledge_n": "knowledge",
    "rule_n": "rule",
    "mapping_n": "mapping",
    "model_n": "model",
    "method_n": "method",
    "population_n": "population",
    "visibility_n": "visibility",
    "mode_n": "mode",
}


class D10Facts:
    """Resolved typed facts for one envelope (mirrors the frozen verifier's
    fact projection; every field derives from explicit typed fields)."""

    __slots__ = (
        "kind", "token", "owner", "legal_match", "scope_eq", "envelope_ok",
        "identity_ok", "es_state", "gate_kind", "gate_reasons", "cov",
        "required_domains", "den_kind", "den_value", "den_state", "den_excl",
        "den_tamper", "seg_tamper", "seg_overlap", "pop_present", "opp",
        "num_subject", "num_event", "num_site", "individual", "pattern",
        "safety_present", "efficacy_present", "gap_present",
        "member_scope_bad", "member_scope_kind", "dup_member_ref",
        "desc_in_numerator",
        "dup_locator", "dup_revision", "origin_decision",
        "origin_plane_duplicate", "excluded_in_numerator",
        "member_producer_d06", "safety_missing", "efficacy_missing",
        "treatment_role_required", "assignment_present", "model_role",
        "model_ensemble", "comp_state", "comp_reasons", "eligible_sites",
        "excluded_sites", "site_activation", "pair_state", "wins",
        "unique_windows", "segments", "change", "vis_hidden_members",
        "vis_hidden_sites", "rate_state", "blind_status", "hidden_omission",
        "dl_violation", "blind_inference", "dl_n", "locator_missing",
        "q_decision", "q_uncovered", "q_covered", "q_fanout", "q_unlistable",
        "q_pd", "q_ids_mismatch", "q_duplicate", "injection",
        "injection_blocked", "rehash", "hotspot", "hotspot_hidden",
        "count_layers", "count_mixed", "small", "limited", "limited_reason",
        "design_applicable", "estimate", "hit", "sources", "ce_declared",
        "ce_matched", "project_ref", "replay", "vis_algebra_ok",
        "vis_decision_hash_bad", "vis_hidden_dropped", "q_set_violation",
        # typed-input audit flags (recomputation; all explicit typed facts)
        "legal_row_hash_bad", "legal_row_sd_mismatch", "scope_hash_bad",
        "mode_hash_bad", "source_hash_bad", "source_pair_duplicate",
        "origin_hash_bad", "origin_refs_external", "origin_partition_bad",
        "origin_decision_bad",
        "den_refs_bad", "seg_recompute_bad", "ledger_bad", "cutoff_order_bad",
        "r2_prior_bad", "dl_eligible_bad", "dl_target_bad",
        "visibility_noncanonical", "visibility_algebra_bad",
        "visibility_pair_rebuild_bad", "visibility_pair_eligible_bad",
        "q_covered_bad", "q_identity_bad", "q_partition_bad", "q_content_bad",
        "assignment_bad", "desc_hash_bad", "model_hash_bad",
        "audience_scan_hit",
        # independent evaluation-authority flags (accepted identity/source
        # membership/model pin; authority is an explicit runtime input)
        "authority_missing", "authority_identity_bad",
        "source_authority_bad", "model_authority_bad",
    )


def _locator_ids(typed: D10TypedInput) -> List[str]:
    """Accepted source locator set rebuilt from typed members + evidence refs
    (never from id conventions)."""
    ids: Set[str] = set()
    for member in typed.members:
        ids.update(member.source_locator_refs)
    for ref in typed.evidence_refs:
        ids.add(ref.locator_id)
    return sorted(ids)


def _audience_scan_hit(typed: D10TypedInput) -> bool:
    """Rendered-audience engineering-reference audit: any non-empty
    non-NFC text, control/invisible characters, fullwidth Latin, engineering
    key/reference tokens, or forbidden internal terms fail closed.  All typed
    fields of the audience text and its contract are explicit facts."""
    texts = (typed.audience_text.basis_zh, typed.audience_text.finding_zh,
             typed.audience_text.action_zh)
    forbidden = tuple(term.lower() for term in _FORBIDDEN_AUDIENCE_TERMS)
    for text in texts:
        if not isinstance(text, str) or not text:
            return True
        if d10_normalize_nfc(text) != text:
            return True
        if any(unicodedata.category(ch).startswith("C")
               or ch in _INVISIBLE_CHARS for ch in text):
            return True
        if any(ord(ch) in _FULLWIDTH_LATIN for ch in text):
            return True
        if _ENGINEERING_KEY_RE.search(text):
            return True
        low = text.lower()
        if any(term in low for term in forbidden):
            return True
    return False


def project_facts(typed: D10TypedInput,
                  authority: Optional[D10EvaluationAuthority] = None,
                  ) -> D10Facts:
    """Project every decisive typed fact from the closed envelope."""
    sd = typed.signal_definition
    lr = typed.legal_matrix_row
    es = typed.expected_set
    den = typed.denominator
    vis = typed.visibility_decision
    qd = typed.query_decision
    rh = typed.rule_hit
    el = typed.evaluation_limits
    nl = typed.numerator_ledger
    members = typed.members
    member_refs = [m.member_ref for m in members]
    kinds = [m.member_kind for m in members]

    pairs = typed.source_revision_content_pairs
    # Keep envelope shape separate from accepted authority membership.  The
    # authority preflight handles accepted-pair presence and submitted extras;
    # duplicate revision ids remain a downstream content-identity attack.
    envelope_ok = bool(pairs) and all(p == pairs[0] for p in pairs)
    dup_revision = len({p.revision_id for p in pairs}) != len(pairs)

    f = D10Facts()
    f.kind = sd.signal_kind
    f.token = sd.clinical_claim_token
    f.owner = sd.d10_action
    f.legal_match = (
        lr.signal_kind == sd.signal_kind
        and lr.clinical_claim_token == sd.clinical_claim_token
        and lr.d10_action == sd.d10_action)
    f.scope_eq = typed.project_scope_binding.scope_equality_decision
    f.envelope_ok = envelope_ok
    f.identity_ok = typed.site_ledger.identity_state == "stable"
    f.es_state = es.expected_set_state
    f.gate_kind = es.admission_gate.gate_kind if es.admission_gate else None
    f.gate_reasons = list(es.admission_gate.reason_codes) if es.admission_gate else []
    f.cov = {c.producer_domain: (c.l0_status, c.l1_medical_completeness_state)
             for c in typed.coverage}
    f.required_domains = list(sd.required_producer_domains)
    f.den_kind = den.denominator_kind
    f.den_value = den.denominator_value
    f.den_state = den.denominator_state
    f.den_excl = list(den.exclusion_reason_codes)
    f.den_tamper = den.denominator_value != den.recomputed_value
    f.seg_tamper = any(s.normalized_duration != s.raw_duration
                       for s in typed.time_segments)
    f.seg_overlap = any(s.overlap_resolution_ref is not None
                        for s in typed.time_segments)
    f.pop_present = typed.analysis_population.present
    f.opp = None
    if typed.opportunity is not None:
        f.opp = {
            "expected": typed.opportunity.expected_opportunity_count,
            "observed": typed.opportunity.observed_opportunity_count,
            "provenance": typed.opportunity.opportunity_provenance,
            "complete": typed.opportunity.complete,
        }
    f.num_subject = nl.affected_subject_count
    f.num_event = nl.event_or_outcome_count
    f.num_site = nl.affected_site_count
    f.individual = nl.individual_risk_count
    f.pattern = nl.center_pattern_count
    f.safety_present = "safety_measure" in kinds
    f.efficacy_present = "efficacy_measure" in kinds
    f.gap_present = "accepted_gap" in kinds
    f.member_scope_bad = any(m.member_scope_state != "in_scope" for m in members)
    f.member_scope_kind = next(
        (m.member_scope_state for m in members
         if m.member_scope_state != "in_scope"), None)
    f.dup_member_ref = len(set(member_refs)) != len(member_refs)
    pattern_descendants = [d for m in members
                           if m.member_kind == "center_pattern"
                           for d in m.descendant_member_refs]
    f.desc_in_numerator = any(ref in pattern_descendants for ref in member_refs)
    f.dup_locator = len({e.locator_id for e in typed.evidence_refs}) != \
        len(typed.evidence_refs)
    f.dup_revision = dup_revision
    f.origin_decision = None
    f.origin_plane_duplicate = False
    if typed.measure_origin_binding is not None:
        f.origin_decision = typed.measure_origin_binding.origin_decision
        f.origin_plane_duplicate = (
            typed.measure_origin_binding.numerator_plane_state == "duplicate")
    excluded_subjects = set(den.excluded_member_refs)
    member_subjects = {m.subject_stable_id for m in members
                       if m.subject_stable_id}
    f.excluded_in_numerator = bool(excluded_subjects & member_subjects)
    f.member_producer_d06 = any(
        m.member_kind == "center_pattern" and m.producer_domain == "D06"
        for m in members)
    f.safety_missing = []
    if typed.safety_context is not None:
        f.safety_missing = sorted(
            key for key, ref in (
                ("exposure", typed.safety_context.exposure_definition_ref),
                ("coding", typed.safety_context.coding_dictionary_ref),
                ("severity", typed.safety_context.severity_scale_ref),
                ("risk_window", typed.safety_context.risk_window_ref))
            if ref is None)
    f.efficacy_missing = []
    f.treatment_role_required = False
    f.assignment_present = False
    f.estimate = None
    if typed.efficacy_context is not None:
        f.efficacy_missing = sorted(
            key for key, ref in (
                ("endpoint", typed.efficacy_context.endpoint_definition_ref),
                ("estimand", typed.efficacy_context.estimand_ref),
                ("missing", typed.efficacy_context.missing_data_rule_ref),
                ("intercurrent",
                 typed.efficacy_context.intercurrent_event_rule_ref))
            if ref is None)
        f.treatment_role_required = typed.efficacy_context.treatment_role_required
        f.assignment_present = (
            typed.efficacy_context.treatment_assignment_exposure_identity_ref
            is not None)
        f.estimate = typed.efficacy_context.estimate_kind
    f.model_role = None
    f.model_ensemble = None
    if typed.model_evidence is not None:
        f.model_role = typed.model_evidence.role
        f.model_ensemble = typed.model_evidence.ensemble_size
    f.comp_state = typed.comparison_gate.comparison_state
    f.comp_reasons = [code for code in typed.comparison_gate.reason_codes
                      if not code.startswith("comparison_")
                      and not code.startswith("window_pair_")]
    f.eligible_sites = typed.comparison_gate.observed_eligible_site_count
    f.excluded_sites = len(typed.comparison_gate.excluded_site_refs)
    f.site_activation = typed.site_ledger.site_activation_state
    f.pair_state = typed.window_pair_gate.pair_state
    f.wins = len(typed.analysis_windows)
    f.unique_windows = len({w.analysis_window_stable_id
                            for w in typed.analysis_windows})
    f.segments = len(typed.time_segments)
    f.change = None
    if typed.change_decision is not None:
        ch = typed.change_decision
        ca = ch.cutoff_advance
        f.change = {
            "basis": ch.execution_basis,
            "comparison_state": ch.comparison_state,
            "prior": ch.prior_snapshot_ref_or_none is not None,
            "data_n": len(ch.data_change_refs),
            "denom_n": len(ch.denominator_change_refs),
            "coverage_n": len(ch.coverage_change_refs),
            "knowledge_n": len(ch.knowledge_change_refs),
            "rule_n": len(ch.rule_change_refs),
            "mapping_n": len(ch.mapping_change_refs),
            "model_n": len(ch.model_change_refs),
            "method_n": len(ch.method_change_refs),
            "population_n": len(ch.population_change_refs),
            "visibility_n": len(ch.visibility_change_refs),
            "mode_n": len(ch.mode_change_refs),
            "cutoff_state": ca.decision_state if ca else None,
            "cutoff_predicate": ca.strict_advance_predicate_passed if ca else False,
            "cutoff_policy_equal": ca.policy_semantic_hash_equal if ca else False,
            "prior_boundary": ca.prior_boundary_value if ca else None,
            "current_boundary": ca.current_boundary_value if ca else None,
            "data_kind": ch.data_change_kind,
            "claimed_kind": ch.claimed_clinical_change_kind,
            "claimed_cause": ch.claimed_primary_change_cause,
            "claimed_cutoff": ch.claimed_cutoff_state,
            "r2_action": ch.r2_action or None,
            "r2_prior": ch.r2_prior_ref_or_none is not None,
            "r2_lineage": ch.lineage_relation or None,
            "carry_forward": ch.carry_forward_state == "active",
        }
    f.vis_hidden_members = vis.hidden_member_count
    f.vis_hidden_sites = vis.hidden_site_count
    f.rate_state = vis.rate_projection_state
    f.blind_status = vis.blind_status
    f.hidden_omission = vis.hidden_set_omitted
    f.dl_violation = vis.deep_link_eligible_violation
    f.blind_inference = vis.treatment_inference_attempt
    f.dl_n = len(typed.deep_links)
    f.locator_missing = any(m.locator_resolution_state != "locatable"
                            for m in members)
    f.q_decision = qd.decision
    f.q_uncovered = len(qd.uncovered_member_refs)
    f.q_covered = len(qd.covered_member_refs)
    f.q_fanout = qd.max_query_member_fanout
    f.q_unlistable = qd.member_unlistable
    f.q_pd = qd.pd_wording_state
    f.q_ids_mismatch = (len(qd.member_query_content_identities)
                        != len(qd.covered_member_refs))
    f.q_duplicate = qd.duplicate_query_attempt
    f.injection = typed.audience_text.engineering_reference_attempt
    f.injection_blocked = typed.audience_text.injection_blocked
    f.rehash = qd.unit_member_set_hash != d10_sha256_text(
        d10_canonical_json(sorted(set(member_refs))))
    f.hotspot = typed.hotspot is not None
    f.hotspot_hidden = bool(typed.hotspot and typed.hotspot.hidden_in_display)
    f.count_layers = list(typed.count_layers.layers_in_common_numerator)
    f.count_mixed = len(set(f.count_layers)) > 1
    f.small = el.small_sample
    f.limited = el.limited_evidence
    f.limited_reason = el.limited_reason
    f.design_applicable = typed.mode_contract.design_applicable_state
    f.hit = rh.hit_state
    f.sources = list(rh.evidence_sources)
    f.ce_declared = len(rh.counterevidence_declared_refs)
    f.ce_matched = len(rh.counterevidence_matched_refs)
    f.project_ref = typed.project_ref

    evaluation = set(vis.evaluation_member_refs)
    projectable = set(vis.projectable_member_refs)
    hidden = set(vis.hidden_member_refs)
    f.vis_algebra_ok = bool(
        projectable | hidden == evaluation
        and not (projectable & hidden)
        and hidden <= evaluation
        and vis.visible_n == len(vis.projectable_member_refs)
        and vis.hidden_member_count == len(vis.hidden_member_refs)
        and vis.hidden_site_count == len(vis.hidden_site_refs)
        and vis.decision_id == d10_content_hash(
            _vis_decision_dict(vis), "decision_id"))
    f.vis_decision_hash_bad = vis.decision_id != d10_content_hash(
        _vis_decision_dict(vis), "decision_id")
    f.vis_hidden_dropped = set(vis.evaluation_member_refs) != set(member_refs)
    unit_member_refs = set(member_refs)
    f.q_set_violation = bool(
        set(qd.covered_member_refs) | set(qd.uncovered_member_refs)
        != unit_member_refs
        or set(qd.covered_member_refs) & set(qd.uncovered_member_refs)
        or any(ref not in unit_member_refs
               for ref in list(qd.covered_member_refs)
               + list(qd.uncovered_member_refs)))
    f.replay = bool(
        f.change and f.change["basis"] == "full"
        and f.change["cutoff_state"] == "same_window"
        and f.change["claimed_cutoff"] is None)

    audit = _typed_audit_codes(typed) | _authority_audit_codes(typed, authority)
    for code in _AUDIT_CODES:
        setattr(f, code, code in audit)
    return f


def _vis_decision_dict(vis: Any) -> Dict[str, Any]:
    """Visibility decision canonical dict (exact keys, submitted list order
    preserved -- mirrors the frozen verifier's raw-dict content hash)."""
    return {
        "blind_status": vis.blind_status,
        "audience_scope_id": vis.audience_scope_id,
        "evaluation_member_refs": list(vis.evaluation_member_refs),
        "projectable_member_refs": list(vis.projectable_member_refs),
        "hidden_member_refs": list(vis.hidden_member_refs),
        "hidden_reason_codes": list(vis.hidden_reason_codes),
        "evaluation_site_refs": list(vis.evaluation_site_refs),
        "projectable_site_refs": list(vis.projectable_site_refs),
        "hidden_site_refs": list(vis.hidden_site_refs),
        "visible_n": vis.visible_n,
        "eligible_n": vis.eligible_n,
        "hidden_member_count": vis.hidden_member_count,
        "hidden_site_count": vis.hidden_site_count,
        "rate_projection_state": vis.rate_projection_state,
        "deep_link_eligible_member_refs": list(vis.deep_link_eligible_member_refs),
        "deep_link_eligible_site_refs": list(vis.deep_link_eligible_site_refs),
        "hidden_set_omitted": vis.hidden_set_omitted,
        "deep_link_eligible_violation": vis.deep_link_eligible_violation,
        "treatment_inference_attempt": vis.treatment_inference_attempt,
        "projectable_subject_site_pairs": [
            list(p) for p in vis.projectable_subject_site_pairs],
        "deep_link_eligible_subject_site_pairs": [
            list(p) for p in vis.deep_link_eligible_subject_site_pairs],
    }


_AUDIT_CODES = frozenset({
    "legal_row_hash_bad", "legal_row_sd_mismatch", "scope_hash_bad",
    "mode_hash_bad", "source_hash_bad", "origin_hash_bad",
    "origin_refs_external", "origin_partition_bad", "origin_decision_bad",
    "source_pair_duplicate", "den_refs_bad", "seg_recompute_bad",
    "ledger_bad", "cutoff_order_bad", "r2_prior_bad", "dl_eligible_bad",
    "dl_target_bad", "visibility_noncanonical", "visibility_algebra_bad",
    "visibility_pair_rebuild_bad", "visibility_pair_eligible_bad",
    "vis_decision_hash_bad", "q_covered_bad", "q_identity_bad",
    "q_partition_bad", "q_content_bad", "assignment_bad", "desc_hash_bad",
    "model_hash_bad", "audience_scan_hit",
    "authority_missing", "authority_identity_bad",
    "source_authority_bad", "model_authority_bad",
})


def _typed_audit_codes(typed: D10TypedInput) -> Set[str]:
    """Independent recomputation of every cross-object hash/binding/set
    relation from explicit typed facts (contract section 16 non-LLM
    anchors).  Fails closed on any inconsistency."""
    out: Set[str] = set()
    lr = typed.legal_matrix_row
    sd = typed.signal_definition
    if lr.row_hash != d10_content_hash({
            "row_id": lr.row_id, "signal_kind": lr.signal_kind,
            "clinical_claim_token": lr.clinical_claim_token,
            "d10_action": lr.d10_action}, "row_hash"):
        out.add("legal_row_hash_bad")
    if (lr.signal_kind != sd.signal_kind
            or lr.clinical_claim_token != sd.clinical_claim_token
            or lr.d10_action != sd.d10_action):
        out.add("legal_row_sd_mismatch")
    sb = typed.project_scope_binding
    if sb.scope_binding_hash != d10_content_hash(
            {"scope_binding_id": sb.scope_binding_id,
             "scope_type": sb.scope_type,
             "scope_equality_decision": sb.scope_equality_decision},
            "scope_binding_hash"):
        out.add("scope_hash_bad")
    mode = typed.mode_contract
    if mode.mode_contract_content_hash != d10_content_hash(
            {"mode_contract_version": mode.mode_contract_version,
             "design_applicable_state": mode.design_applicable_state,
             "design_clause_ref": mode.design_clause_ref},
            "mode_contract_content_hash"):
        out.add("mode_hash_bad")
    locator_ids = _locator_ids(typed)
    seen_pairs: Set[Tuple[str, str]] = set()
    for pair in typed.source_revision_content_pairs:
        if pair.content_hash != d10_sha256_text(d10_canonical_json({
                "revision_id": pair.revision_id,
                "source_locators": locator_ids})):
            out.add("source_hash_bad")
        pair_key = (pair.revision_id, pair.content_hash)
        if pair_key in seen_pairs:
            out.add("source_pair_duplicate")
        seen_pairs.add(pair_key)
    members = typed.members
    member_refs = [m.member_ref for m in members]
    mob = typed.measure_origin_binding
    if mob is not None:
        for key in ("verified_risk_refs", "distinct_risk_refs",
                    "ambiguous_risk_refs", "candidate_risk_refs"):
            for ref in getattr(mob, key):
                if ref not in member_refs:
                    out.add("origin_refs_external")
            if list(getattr(mob, key)) != sorted(set(getattr(mob, key))):
                out.add("origin_partition_bad")
        verified = set(mob.verified_risk_refs)
        distinct = set(mob.distinct_risk_refs)
        ambiguous = set(mob.ambiguous_risk_refs)
        candidate = set(mob.candidate_risk_refs)
        if candidate != verified | distinct | ambiguous \
                or verified & distinct or verified & ambiguous \
                or distinct & ambiguous:
            out.add("origin_partition_bad")
        if ambiguous:
            derived_origin = "ambiguous"
        elif verified and distinct:
            derived_origin = "mixed_verified_and_distinct"
        elif verified:
            derived_origin = "all_verified_same_origin"
        elif distinct:
            derived_origin = "all_distinct"
        elif mob.origin_decision == "wrong_scope":
            derived_origin = "wrong_scope"
        else:
            derived_origin = "not_evaluable"
        if mob.origin_decision != derived_origin:
            out.add("origin_decision_bad")
        if mob.candidate_partition_hash != d10_sha256_text(
                d10_canonical_json(sorted(candidate))):
            out.add("origin_hash_bad")
        if mob.binding_hash != d10_content_hash(
                _origin_binding_dict(mob), "binding_hash"):
            out.add("origin_hash_bad")
    den = typed.denominator
    segments = typed.time_segments
    time_kind = den.denominator_kind in ("subject_time", "exposure_time")
    if not time_kind:
        if den.denominator_value >= 0 and \
                len(den.denominator_member_refs) != den.denominator_value:
            out.add("den_refs_bad")
    else:
        total = sum(s.normalized_duration for s in segments)
        if total != den.denominator_value or \
                len(den.denominator_member_refs) != den.denominator_value:
            out.add("den_refs_bad")
        if not {s.member_ref for s in segments} <= \
                set(den.denominator_member_refs):
            out.add("den_refs_bad")
    for seg in segments:
        if seg.raw_duration != seg.end_value - seg.start_value + 1 \
                or seg.normalized_duration != seg.raw_duration:
            out.add("seg_recompute_bad")
    nl = typed.numerator_ledger
    pattern_descendants = [d for m in members
                           if m.member_kind == "center_pattern"
                           for d in m.descendant_member_refs]
    indiv_refs = [m.member_ref for m in members
                  if m.member_kind == "individual_risk"
                  and m.member_ref not in pattern_descendants]
    indiv_subjects = {m.subject_stable_id for m in members
                      if m.member_kind == "individual_risk"
                      and m.subject_stable_id}
    if nl.individual_risk_count != len(set(indiv_refs)):
        out.add("ledger_bad")
    if nl.center_pattern_count != len({m.member_ref for m in members
                                       if m.member_kind == "center_pattern"}):
        out.add("ledger_bad")
    if nl.affected_subject_count != len(indiv_subjects):
        out.add("ledger_bad")
    if nl.numerator_member_count != len(set(member_refs)):
        out.add("ledger_bad")
    for m in members:
        if m.member_kind == "center_pattern" and \
                m.descendant_set_hash != d10_sha256_text(
                    d10_canonical_json(sorted(m.descendant_member_refs))):
            out.add("desc_hash_bad")
    ch = typed.change_decision
    if ch is not None and ch.cutoff_advance is not None:
        ca = ch.cutoff_advance
        derived_strict = bool(ca.strict_advance_predicate_passed
                              and ca.policy_semantic_hash_equal
                              and str(ca.current_boundary_value)
                              > str(ca.prior_boundary_value))
        if ca.decision_state == "strict_advance" and not derived_strict:
            out.add("cutoff_order_bad")
        if ch.r2_action in ("continue", "update", "propose_close",
                            "reopen", "supersede") and \
                ch.r2_prior_ref_or_none is None:
            out.add("r2_prior_bad")
        if ch.carry_forward_state == "active" and \
                ch.r2_prior_ref_or_none is None:
            out.add("r2_prior_bad")
    vis = typed.visibility_decision
    if vis.decision_id != d10_content_hash(_vis_decision_dict(vis),
                                           "decision_id"):
        out.add("vis_decision_hash_bad")
    evaluation_refs = vis.evaluation_member_refs
    projectable_refs = vis.projectable_member_refs
    hidden_refs = vis.hidden_member_refs
    if any(list(values) != sorted(set(values)) for values in (
            evaluation_refs, projectable_refs, hidden_refs,
            vis.deep_link_eligible_member_refs, vis.evaluation_site_refs,
            vis.projectable_site_refs, vis.hidden_site_refs,
            vis.deep_link_eligible_site_refs)):
        out.add("visibility_noncanonical")
    if set(projectable_refs) | set(hidden_refs) != set(evaluation_refs) or \
            set(projectable_refs) & set(hidden_refs):
        out.add("visibility_algebra_bad")
    if vis.visible_n != len(set(projectable_refs)) or \
            vis.eligible_n != len(set(evaluation_refs)) or \
            vis.hidden_member_count != len(set(hidden_refs)) or \
            vis.hidden_site_count != len(set(vis.hidden_site_refs)):
        out.add("visibility_algebra_bad")
    if not set(vis.deep_link_eligible_member_refs) <= set(projectable_refs):
        out.add("dl_eligible_bad")
    proj_sites = set(vis.projectable_site_refs)
    member_by_ref = {m.member_ref: m for m in members}
    pairs = sorted({
        (member_by_ref[ref].subject_stable_id,
         member_by_ref[ref].site_stable_id)
        for ref in projectable_refs if ref in member_by_ref
        and member_by_ref[ref].subject_stable_id
        and member_by_ref[ref].site_stable_id in proj_sites})
    if [tuple(p) for p in vis.projectable_subject_site_pairs] != pairs:
        out.add("visibility_pair_rebuild_bad")
    eligible_pairs = sorted({
        (member_by_ref[ref].subject_stable_id,
         member_by_ref[ref].site_stable_id)
        for ref in vis.deep_link_eligible_member_refs
        if ref in member_by_ref and member_by_ref[ref].subject_stable_id
        and member_by_ref[ref].site_stable_id in proj_sites})
    if set(vis.deep_link_eligible_subject_site_pairs) != set(eligible_pairs):
        out.add("visibility_pair_eligible_bad")
    if not set(vis.deep_link_eligible_site_refs) <= proj_sites:
        out.add("dl_eligible_bad")
    for dl in typed.deep_links:
        if dl.visibility_decision_ref != vis.decision_id:
            out.add("dl_target_bad")
        if dl.target_kind == "member":
            ref = dl.member_object_ref
            member = member_by_ref.get(ref) if ref else None
            if ref not in set(vis.deep_link_eligible_member_refs) \
                    or member is None \
                    or dl.subject_ref != member.subject_stable_id \
                    or dl.site_ref != member.site_stable_id:
                out.add("dl_target_bad")
        elif dl.target_kind == "site":
            if dl.site_ref not in proj_sites:
                out.add("dl_target_bad")
            if dl.subject_ref is not None or dl.member_object_ref is not None:
                out.add("dl_target_bad")
        else:
            if (dl.subject_ref, dl.site_ref) not in set(pairs):
                out.add("dl_target_bad")
            if dl.member_object_ref is not None:
                out.add("dl_target_bad")
    qd = typed.query_decision
    covered_refs = qd.covered_member_refs
    uncovered_refs = qd.uncovered_member_refs
    if any(ref not in member_refs for ref in covered_refs):
        out.add("q_covered_bad")
    if any(ref not in member_refs for ref in uncovered_refs):
        out.add("q_covered_bad")
    if list(covered_refs) != sorted(set(covered_refs)) or \
            list(uncovered_refs) != sorted(set(uncovered_refs)):
        out.add("q_identity_bad")
    if (set(covered_refs) & set(uncovered_refs)
            or set(covered_refs) | set(uncovered_refs) != set(member_refs)):
        out.add("q_partition_bad")
    identities = qd.member_query_content_identities
    if len(identities) != len(covered_refs) or \
            len(set(identities)) != len(identities):
        out.add("q_identity_bad")
    elif any(identity != d10_sha256_text(d10_canonical_json(
            {"member_ref": ref}))
             for identity, ref in zip(identities, covered_refs)):
        out.add("q_identity_bad")
    if qd.unit_member_set_hash != d10_sha256_text(
            d10_canonical_json(sorted(set(member_refs)))):
        out.add("q_partition_bad")
    proof = {
        "unit_member_refs": sorted(set(member_refs)),
        "covered_member_refs": list(covered_refs),
        "uncovered_member_refs": list(uncovered_refs),
        "member_query_content_identities": list(identities),
    }
    if qd.coverage_proof_hash != d10_sha256_text(d10_canonical_json(proof)):
        out.add("q_partition_bad")
    if qd.query_content_hash != d10_content_hash(
            _query_decision_dict(qd), "query_content_hash"):
        out.add("q_content_bad")
    model = typed.model_evidence
    if model is not None:
        expected_leaf = ("model_candidate_only"
                         if model.role == "candidate_explanation"
                         else "counterevidence_suggestion_only")
        if model.permitted_leaf != expected_leaf or \
                (model.ensemble_size == 1
                 and model.permitted_leaf != "model_candidate_only"):
            out.add("model_hash_bad")
        binding_core = _model_binding_dict(model)
        if model.model_binding_hash != d10_sha256_text(
                d10_canonical_json(binding_core)):
            out.add("model_hash_bad")
        if list(model.member_analysis_refs) != sorted(set(model.member_analysis_refs)) \
                or model.member_analysis_ref_set_hash != d10_sha256_text(
                    d10_canonical_json(sorted(set(model.member_analysis_refs)))):
            out.add("model_hash_bad")
        if model.output_hash != d10_sha256_text(d10_canonical_json({
                "output_identity": model.output_identity,
                "model_binding_hash": model.model_binding_hash,
                "permitted_leaf": model.permitted_leaf,
                "adjudication_state": model.adjudication_state})):
            out.add("model_hash_bad")
    ec = typed.efficacy_context
    if ec is not None and \
            ec.treatment_assignment_exposure_identity_ref is not None:
        authority = ec.treatment_role_authority_ref
        if authority is None:
            out.add("assignment_bad")
        recomputed = d10_sha256_text(d10_canonical_json({
            "authority": authority, "project": typed.project_ref,
            "run": typed.run_ref}))
        if ec.treatment_assignment_exposure_identity_ref != recomputed:
            out.add("assignment_bad")
        if ec.treatment_assignment_mapping_hash != recomputed:
            out.add("assignment_bad")
    if _audience_scan_hit(typed):
        out.add("audience_scan_hit")
    return out


def _authority_audit_codes(typed: D10TypedInput,
                           authority: Optional[D10EvaluationAuthority],
                           ) -> Set[str]:
    """Accepted-membership audit against the independent evaluation authority
    (contract section 4).  The authority is an explicit immutable runtime
    input; the runtime never reads the registry that produced it.  Fails
    closed before medical computation when the submitted envelope identity,
    submitted source revision-content subset / locator set, or decisive
    ModelEvidence pin diverges from authority.  No case/fixture/test id,
    mutation metadata, description or synthetic convention is consulted."""
    out: Set[str] = set()
    if authority is None:
        out.add("authority_missing")
        return out
    if (typed.project_ref != authority.project_ref
            or typed.run_ref != authority.run_ref
            or typed.snapshot_ref != authority.snapshot_ref):
        out.add("authority_identity_bad")
    accepted = {
        (pair.revision_id, pair.content_hash)
        for pair in authority.accepted_source_revision_content_pairs
    }
    submitted = {
        (pair.revision_id, pair.content_hash)
        for pair in typed.source_revision_content_pairs
    }
    # A unit may submit any non-empty, internally valid subset of the
    # authority's accepted pairs.  Extras are authority failures; missing
    # accepted pairs are allowed because authority is a superset of the
    # envelope's admitted source membership for this unit.
    if any(pair_key not in accepted for pair_key in submitted):
        out.add("source_authority_bad")
    locator_set_hash = d10_sha256_text(
        d10_canonical_json(_locator_ids(typed)))
    if locator_set_hash != authority.accepted_source_locator_set_hash:
        out.add("source_authority_bad")
    if authority.model_binding_hash is None:
        if typed.model_evidence is not None:
            out.add("model_authority_bad")
    elif (typed.model_evidence is None
          or typed.model_evidence.model_binding_hash
          != authority.model_binding_hash
          or typed.model_evidence.output_hash != authority.model_output_hash):
        out.add("model_authority_bad")
    return out


def _origin_binding_dict(mob: Any) -> Dict[str, Any]:
    return {
        "binding_id": mob.binding_id,
        "measure_ref": mob.measure_ref,
        "origin_decision": mob.origin_decision,
        "verified_risk_refs": sorted(mob.verified_risk_refs),
        "distinct_risk_refs": sorted(mob.distinct_risk_refs),
        "ambiguous_risk_refs": sorted(mob.ambiguous_risk_refs),
        "candidate_risk_refs": sorted(mob.candidate_risk_refs),
        "candidate_partition_hash": mob.candidate_partition_hash,
        "numerator_plane_state": mob.numerator_plane_state,
        "source_provenance_hash": mob.source_provenance_hash,
    }


def _query_decision_dict(qd: Any) -> Dict[str, Any]:
    return {
        "decision": qd.decision,
        "covered_member_refs": list(qd.covered_member_refs),
        "uncovered_member_refs": list(qd.uncovered_member_refs),
        "member_query_content_identities": list(
            qd.member_query_content_identities),
        "unit_member_set_hash": qd.unit_member_set_hash,
        "coverage_proof_hash": qd.coverage_proof_hash,
        "max_query_member_fanout": qd.max_query_member_fanout,
        "member_unlistable": qd.member_unlistable,
        "pd_wording_state": qd.pd_wording_state,
        "duplicate_query_attempt": qd.duplicate_query_attempt,
    }


def _model_binding_dict(model: Any) -> Dict[str, Any]:
    return {
        "model_evidence_id": model.model_evidence_id,
        "role": model.role,
        "evaluation_content_identity": model.evaluation_content_identity,
        "input_content_hash": model.input_content_hash,
        "source_revision_content_pairs": [
            {"revision_id": pair.revision_id, "content_hash": pair.content_hash}
            for pair in model.source_revision_content_pairs],
        "source_refs": sorted(model.source_refs),
        "model_id": model.model_id,
        "model_version": model.model_version,
        "independent_context_hash": model.independent_context_hash,
        "ensemble_id": model.ensemble_id,
        "ensemble_size": model.ensemble_size,
        "member_analysis_refs": sorted(model.member_analysis_refs),
        "permitted_leaf": model.permitted_leaf,
        "member_analysis_ref_set_hash": model.member_analysis_ref_set_hash,
        "output_identity": model.output_identity,
        "adjudication_state": model.adjudication_state,
    }


# ---------------------------------------------------------------------------
# Change derivation (contract section 14)
# ---------------------------------------------------------------------------


def derive_change(ch: Optional[Dict[str, Any]]) -> Tuple[str, Optional[str], str, bool]:
    """Return (clinical_change_kind, primary_change_cause, lineage_relation,
    analysis_only) from the typed change facts."""
    if ch is None or ch.get("basis") == "full":
        return "initial_current", None, "initial_full_snapshot", False
    if ch.get("comparison_state") == "not_comparable":
        return "not_comparable", None, "not_comparable", True
    non_data = [key for key in NON_DATA_CAUSE_KEYS if ch.get(key, 0) > 0]
    if non_data:
        causes = [_CAUSE_BY_KEY[key] for key in non_data]
        cause = causes[0] if len(causes) == 1 else "mixed"
        if "method" in causes or "population" in causes:
            lineage = "superseded_by_method_or_population_change"
        elif "rule" in causes or "mapping" in causes or "model" in causes:
            lineage = "superseded_by_rule_or_mapping_change"
        elif "knowledge" in causes:
            lineage = "superseded_by_knowledge_change"
        elif "mode" in causes:
            lineage = "superseded_by_mode_change"
        elif "visibility" in causes:
            lineage = "superseded_by_visibility_change"
        elif "coverage" in causes:
            lineage = "coverage_regressed"
        else:
            lineage = "not_comparable"
        return "not_comparable", cause, lineage, True
    if (ch.get("cutoff_state") == "strict_advance"
            and ch.get("cutoff_predicate")
            and ch.get("cutoff_policy_equal") and ch.get("prior")):
        lineage = "continued_from_cutoff_advance"
    else:
        lineage = "continued_from_data_revision"
    return ch.get("data_kind") or "continued", "data", lineage, False


# ---------------------------------------------------------------------------
# Decision rule table (contract sections 2.1/3.3/6/7/8/9/10/13/14)
# ---------------------------------------------------------------------------


def derive_disposition(f: D10Facts) -> Tuple[str, str, Dict[str, Any]]:
    """Return (disposition_or_gate, primary_reason, extra).  extra carries
    leaf-level facts (e.g. zero_unit)."""
    token, owner, kind = f.token, f.owner, f.kind
    if f.authority_missing:
        return "global_gate", "evaluation_authority_missing", {"zero_unit": True}
    if f.authority_identity_bad:
        return "global_gate", "authority_identity_mismatch", {"zero_unit": True}
    if token == UNRESOLVED_TOKEN:
        return "routing_gate", "claim_token_unresolved", {"zero_unit": True}
    if owner == "consume_only":
        if token not in CONSUME_ONLY_TOKENS:
            return "integrity_gate", "legal_row_mismatch", {"zero_unit": True}
        return "routing_gate", "consume_only_no_medical_unit", {"zero_unit": True}
    if owner == "handoff_only":
        if token not in HANDOFF_ONLY_TOKENS:
            return "integrity_gate", "legal_row_mismatch", {"zero_unit": True}
        return "handoff_gate", "handoff_only_no_medical_unit", {"zero_unit": True}
    if owner == "routing_gate":
        return "routing_gate", "routing_gate_no_medical_unit", {"zero_unit": True}
    if token not in OWNED_TOKENS:
        return "integrity_gate", "owner_route_unauthorized", {"zero_unit": True}
    if not f.legal_match:
        return "integrity_gate", "legal_matrix_row_mismatch", {"zero_unit": True}
    if f.legal_row_hash_bad:
        return "integrity_gate", "legal_matrix_row_tamper", {"zero_unit": True}
    if f.scope_eq != "exact_match":
        return "global_gate", "scope_binding_mismatch", {"zero_unit": True}
    if f.scope_hash_bad:
        return "integrity_gate", "scope_binding_tamper", {"zero_unit": True}
    if f.source_authority_bad:
        return "integrity_gate", "source_authority_mismatch", {"zero_unit": True}
    if not f.envelope_ok:
        return "global_gate", "envelope_source_revision_mismatch", {"zero_unit": True}
    if not f.identity_ok:
        return "global_gate", "identity_state_unstable", {"zero_unit": True}
    if f.mode_hash_bad:
        return "integrity_gate", "mode_contract_tamper", {"zero_unit": True}
    if f.es_state == "global_admission_failed":
        return "global_gate", "global_admission_failed", {"zero_unit": True}
    if f.es_state in ("routed_consume_only", "routing_gate_unresolved"):
        return "routing_gate", f"expected_set_{f.es_state}", {"zero_unit": True}
    if f.es_state == "control_plane_gate":
        if f.gate_kind == "comparison_set_gate":
            return "comparison_set_gate", "control_plane_comparison_gate", \
                {"zero_unit": True}
        return "window_pair_gate", "control_plane_window_pair_gate", \
            {"zero_unit": True}

    ch = f.change
    derived = derive_change(ch) if ch else None
    derived_kind = derived[0] if derived else "initial_current"
    derived_cause = derived[1] if derived else None
    derived_lineage = derived[2] if derived else "initial_full_snapshot"
    analysis_only = derived[3] if derived else False

    if (ch and ch.get("claimed_cutoff") == "strict_advance"
            and ch.get("cutoff_state") in ("same_window", "policy_changed")) \
            or f.cutoff_order_bad:
        return "integrity_gate", "cutoff_advance_tamper", {"zero_unit": True}
    if ch and ch.get("r2_lineage") == "continued_from_cutoff_advance" \
            and ch.get("cutoff_state") == "not_evaluable":
        return "not_evaluable", "cutoff_not_evaluable", {}
    if (ch and ch.get("r2_action") == "create" and ch.get("r2_prior")) \
            or f.r2_prior_bad:
        return "integrity_gate", "r2_wrong_prior", {"zero_unit": True}
    if ch and ch.get("r2_action") == "create" \
            and ch.get("r2_lineage") not in ALLOWED_CREATE_LINEAGES:
        return "integrity_gate", "r2_wrong_lineage", {"zero_unit": True}
    if ch and ch.get("r2_action") == "create" and analysis_only:
        return "integrity_gate", "r2_create_non_data_mixed", {"zero_unit": True}
    if ch and ch.get("r2_lineage") and derived \
            and ch.get("r2_lineage") != derived_lineage:
        return "integrity_gate", "r2_wrong_lineage", {"zero_unit": True}
    if ch and ch.get("claimed_kind") and derived \
            and ch["claimed_kind"] != derived_kind:
        return "integrity_gate", "fake_change_claim", {"zero_unit": True}
    if ch and ch.get("claimed_cause") and derived \
            and ch["claimed_cause"] != derived_cause:
        return "integrity_gate", "fake_change_cause", {"zero_unit": True}
    if f.den_tamper:
        return "integrity_gate", "denominator_tamper", {"zero_unit": True}
    if f.den_refs_bad:
        return "integrity_gate", "denominator_recompute_mismatch", {"zero_unit": True}
    if f.seg_tamper or f.seg_recompute_bad:
        return "integrity_gate", "time_segment_tamper", {"zero_unit": True}
    if f.seg_overlap:
        return "integrity_gate", "time_segment_overlap", {"zero_unit": True}
    if f.count_mixed:
        return "integrity_gate", "cross_layer_count_mixing", {"zero_unit": True}
    if f.desc_in_numerator:
        return "integrity_gate", "d09_parent_descendant_duplication", \
            {"zero_unit": True}
    if f.ledger_bad:
        return "integrity_gate", "numerator_ledger_mismatch", {"zero_unit": True}
    if f.origin_decision == "all_verified_same_origin" \
            and f.origin_plane_duplicate:
        return "integrity_gate", "same_origin_double_count", {"zero_unit": True}
    if f.origin_refs_external or f.origin_hash_bad or f.origin_partition_bad \
            or f.origin_decision_bad:
        return "integrity_gate", "measure_origin_binding_tamper", \
            {"zero_unit": True}
    if f.member_producer_d06:
        return "integrity_gate", "d06_efficacy_not_d09_pattern", {"zero_unit": True}
    if f.excluded_in_numerator:
        return "integrity_gate", "excluded_member_counted", {"zero_unit": True}
    if f.dup_member_ref:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f.dup_locator:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f.dup_revision or f.source_pair_duplicate:
        return "integrity_gate", "duplicate_content_identity", {"zero_unit": True}
    if f.source_hash_bad:
        return "integrity_gate", "source_revision_hash_tamper", {"zero_unit": True}
    if f.source_authority_bad:
        return "integrity_gate", "source_authority_mismatch", {"zero_unit": True}
    if f.desc_hash_bad:
        return "integrity_gate", "descendant_set_tamper", {"zero_unit": True}
    if f.den_value < 0:
        return "integrity_gate", "invalid_numeric", {"zero_unit": True}
    if f.rehash:
        return "integrity_gate", "rehash_bypass_evaluator_identity", \
            {"zero_unit": True}
    if f.vis_hidden_dropped:
        return "integrity_gate", "hidden_member_dropped", {"zero_unit": True}
    if f.hidden_omission:
        return "integrity_gate", "hidden_set_omitted", {"zero_unit": True}
    if f.dl_violation or f.dl_eligible_bad or f.visibility_pair_eligible_bad:
        return "integrity_gate", "deep_link_eligible_violation", {"zero_unit": True}
    if f.dl_target_bad:
        return "integrity_gate", "deep_link_target_tamper", {"zero_unit": True}
    if not f.vis_algebra_ok or f.vis_decision_hash_bad \
            or f.visibility_noncanonical or f.visibility_algebra_bad \
            or f.visibility_pair_rebuild_bad:
        return "integrity_gate", "visibility_algebra", {"zero_unit": True}
    if f.blind_inference:
        return "integrity_gate", "blind_treatment_inference", {"zero_unit": True}
    if not f.injection_blocked and (f.injection or f.audience_scan_hit):
        return "integrity_gate", "audience_injection_blocked", {"zero_unit": True}
    if f.hotspot_hidden:
        return "integrity_gate", "hotspot_hidden", {"zero_unit": True}
    if f.q_set_violation or f.q_covered_bad or f.q_partition_bad:
        return "integrity_gate", "query_redundancy_tamper", {"zero_unit": True}
    if f.q_ids_mismatch or f.q_identity_bad:
        return "integrity_gate", "query_source_tamper", {"zero_unit": True}
    if f.q_content_bad:
        return "integrity_gate", "query_source_tamper", {"zero_unit": True}
    if f.q_duplicate:
        return "integrity_gate", "duplicate_query_per_unit", {"zero_unit": True}
    if f.assignment_bad:
        return "integrity_gate", "treatment_assignment_tamper", {"zero_unit": True}
    if f.model_hash_bad:
        return "integrity_gate", "model_evidence_tamper", {"zero_unit": True}
    if f.model_authority_bad:
        return "integrity_gate", "model_authority_mismatch", {"zero_unit": True}
    if f.member_scope_bad:
        return "not_evaluable", "member_resolution_failed", {}

    # D4 completeness (contract section 9.1 precedence)
    for domain in f.required_domains:
        l0, l1 = f.cov.get(domain, ("covered", "complete"))
        if l0 != "covered" or l1 != "complete":
            return "not_evaluable", "required_l1_hole", {}
    if f.den_state == "unclosed":
        return "not_evaluable", "denominator_unclosed", {}
    if f.den_state == "closed_zero":
        if f.design_applicable == "not_applicable":
            return "not_applicable", "design_not_applicable", {}
        return "not_evaluable", "zero_denominator_not_negative", {}
    if not f.pop_present:
        return "not_evaluable", "analysis_population_missing", {}
    if f.opp and not f.opp["complete"]:
        return "not_evaluable", "opportunity_ledger_incomplete", {}
    if f.opp and f.opp["provenance"] == "raw_only":
        return "not_evaluable", "gap_only_provenance", {}
    if f.origin_decision in ("ambiguous", "wrong_scope", "not_evaluable"):
        return "not_evaluable", f"origin_{f.origin_decision}", {}
    if kind == "project_safety_trend" and f.safety_missing:
        return "not_evaluable", "safety_context_incomplete", {}
    if kind == "project_efficacy_trend":
        if f.efficacy_missing:
            return "not_evaluable", "efficacy_context_incomplete", {}
        if f.treatment_role_required and not f.assignment_present:
            return "not_evaluable", "treatment_assignment_missing", {}
    for code in f.comp_reasons:
        if code in NOT_EVALUABLE_COMP_CODES:
            return "not_evaluable", code, {}
    if f.design_applicable == "unresolved":
        return "not_evaluable", "authority_unresolvable", {}
    if f.design_applicable == "not_applicable":
        return "not_applicable", "design_not_applicable", {}

    # D5 gates (contract section 3.3)
    if kind == "cross_site_pattern" and f.comp_state != "ready":
        return "comparison_set_gate", f"comparison_{f.comp_state}", \
            {"zero_unit": True}
    if kind in ("project_time_trend", "project_safety_trend",
                "project_efficacy_trend") and f.pair_state != "ready":
        return "window_pair_gate", f"window_pair_{f.pair_state}", \
            {"zero_unit": True}

    # D6 evaluation
    for code in f.comp_reasons:
        if code in BOUNDARY_COMP_CODES:
            return "boundary", code, {}
    if f.origin_decision == "mixed_verified_and_distinct":
        return "boundary", "mixed_origin_separate_leaves", {}
    typed_evidence = any(source in ("typed_member", "verified_measure")
                         for source in f.sources)
    if f.hit != "not_applicable" and not typed_evidence:
        return "boundary", "evidence_not_typed_positive_forbidden", {}
    if f.ce_declared > 0 and f.ce_matched >= f.ce_declared:
        return "negative", "counterevidence_explains", {}
    if f.small:
        return "boundary", "small_sample", {}
    if f.limited:
        return "boundary", f.limited_reason or "limited_evidence", {}
    if 0 < f.ce_matched < f.ce_declared:
        return "boundary", "counterevidence_partial", {}
    if f.locator_missing:
        return "boundary", "deep_link_deficient", {}
    if f.hit == "no_hit":
        return "negative", "no_hit_complete", {}
    if f.hit == "not_applicable":
        return "not_applicable", "rule_not_applicable", {}
    return "positive", "rule_hit_counterevidence_insufficient", {}


def _estimate_kind(f: D10Facts) -> str:
    if f.estimate:
        return f.estimate
    return DEN_KIND_ESTIMATE.get(f.den_kind, "proportion")


def _query_count(f: D10Facts, disposition: str) -> int:
    if disposition != "positive":
        return 0
    if f.q_decision != "project_delta_present":
        return 0
    if f.q_uncovered <= 0:
        return 0
    if f.q_unlistable:
        return 0
    if f.q_uncovered > f.q_fanout:
        return 0
    if (f.injection or f.audience_scan_hit) and f.injection_blocked:
        return 0
    return 1


# ---------------------------------------------------------------------------
# Evaluation identity (contract section 5) and leaf builders
# ---------------------------------------------------------------------------

# Keys that are NOT evaluation content (test/audit bookkeeping, authority
# lookup results, or validation byproducts); excluded from content identity.
_IDENTITY_EXCLUDED_KEYS = frozenset({
    "idx", "case_id", "oracle_case_id", "fixture_id", "partition", "family",
    "required_sites", "vis_hidden_counts_bad", "site_ref_for_members",
    "authority_entry", "surface_alt",
} | _AUDIT_CODES)


def _facts_dict(f: D10Facts) -> Dict[str, Any]:
    return {key: getattr(f, key) for key in D10Facts.__slots__}


def evaluation_content_identity(f: D10Facts) -> str:
    """Deterministic content identity of one evaluation: canonical NFC JSON
    of every decisive typed fact (audit/test bookkeeping excluded), sha256."""
    core = {key: value for key, value in _facts_dict(f).items()
            if key not in _IDENTITY_EXCLUDED_KEYS}
    return d10_sha256_text(d10_canonical_json(core))


def _gate_leaf_kind(disposition_or_gate: str) -> str:
    return {
        "comparison_set_gate": "control_plane_comparison_gate",
        "window_pair_gate": "control_plane_window_pair_gate",
        "global_gate": "global_integrity_gate",
        "integrity_gate": "global_integrity_gate",
        "routing_gate": "routing_gate",
        "handoff_gate": "handoff_gate",
    }[disposition_or_gate]


def _unit_member_count(f: D10Facts) -> int:
    return (f.individual + f.pattern
            + (1 if f.opp else 0)
            + (1 if f.safety_present else 0)
            + (1 if f.efficacy_present else 0))


def _authority_preflight_result(
        typed: D10TypedInput, codes: Set[str]) -> D10RunResult:
    """Build an authority gate without projecting project medical facts."""
    if "authority_missing" in codes:
        disposition = "global_gate"
        reason = "evaluation_authority_missing"
    elif "authority_identity_bad" in codes:
        disposition = "global_gate"
        reason = "authority_identity_mismatch"
    elif "source_authority_bad" in codes:
        disposition = "integrity_gate"
        reason = "source_authority_mismatch"
    else:
        disposition = "integrity_gate"
        reason = "model_authority_mismatch"
    identity = d10_sha256_text(d10_canonical_json({
        "authority_gate": reason,
        "signal_kind": typed.signal_definition.signal_kind,
    }))
    terminal = "blocked" if disposition == "integrity_gate" else "stable"
    return D10RunResult(
        disposition_or_gate=disposition,
        primary_reason=reason,
        unit=None,
        gate=D10GateResult(
            gate_kind=disposition,
            leaf_kind=_gate_leaf_kind(disposition),
            signal_kind=typed.signal_definition.signal_kind,
            reason_codes=(reason,),
            denominator_value=0,
            audience_injection_blocked=False,
        ),
        trace=(D10TraceLeaf(
            trace_kind="evaluation_identity",
            stable_core_ref=None,
            content_identity=identity,
            replay_byte_equal=False,
            terminal_state=terminal,
        ),),
        source=(),
        forbidden=(D10ForbiddenLeaf(
            leaf_kind="medical_unit",
            expected_disposition=None,
            gate_kind=None,
            change_kind=None,
            reason_code=f"zero_medical_output:{reason}",
        ),),
        evaluation_content_identity=identity,
        stable_core_ref=None,
        replay_byte_equal=False,
        terminal_state=terminal,
    )


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def evaluate(typed: D10TypedInput,
             authority: Optional[D10EvaluationAuthority] = None,
             ) -> D10RunResult:
    """Deterministically evaluate one typed D10 envelope against the accepted
    evaluation authority (contract section 4).  ``authority`` is a required
    immutable runtime input; when absent the run fails closed as a global
    authority-missing gate before any medical computation."""
    validate_typed_input(typed)
    authority_codes = _authority_audit_codes(typed, authority)
    if authority_codes:
        return _authority_preflight_result(typed, authority_codes)
    f = project_facts(typed, authority)
    disposition_or_gate, reason, extra = derive_disposition(f)
    identity = evaluation_content_identity(f)
    stable_core = None if disposition_or_gate in GATE_DISPOSITIONS \
        else d10_unit_stable_core(typed)
    replay = bool(f.replay)
    terminal = "blocked" if disposition_or_gate == "integrity_gate" \
        else "stable"

    unit: Optional[D10UnitResult] = None
    gate: Optional[D10GateResult] = None
    if extra.get("zero_unit") or disposition_or_gate in GATE_DISPOSITIONS:
        gate = D10GateResult(
            gate_kind=disposition_or_gate,
            leaf_kind=_gate_leaf_kind(disposition_or_gate),
            signal_kind=f.kind,
            reason_codes=tuple(sorted(set(f.gate_reasons or [reason]))),
            denominator_value=f.den_value if f.den_value >= 0 else 0,
            audience_injection_blocked=bool(f.injection),
        )
    else:
        positive = disposition_or_gate == "positive"
        boundary = disposition_or_gate == "boundary"
        derived = derive_change(f.change) if f.change else None
        derived_kind = derived[0] if derived else "initial_current"
        derived_cause = derived[1] if derived else None
        derived_lineage = derived[2] if derived else "initial_full_snapshot"
        unit = D10UnitResult(
            signal_kind=f.kind,
            l1_disposition=disposition_or_gate,
            primary_reason=reason,
            stable_core_ref=stable_core or "",
            numerator_member_count=_unit_member_count(f),
            individual_risk_count=f.individual,
            affected_subject_count=f.num_subject,
            event_or_outcome_count=f.num_event,
            center_pattern_count=f.pattern,
            affected_site_count=f.num_site,
            denominator_kind=f.den_kind,
            denominator_value=f.den_value if f.den_value >= 0 else 0,
            denominator_state=f.den_state,
            estimate_kind=_estimate_kind(f),
            project_signal_count=1 if positive else 0,
            clue_count=1 if boundary else 0,
            query_count=_query_count(f, disposition_or_gate),
            risk_handoff_count=1 if positive else 0,
            change_kind=derived_kind,
            change_cause=derived_cause,
            lineage_relation=derived_lineage,
            handoff_action=f.change.get("r2_action") if (f.change and positive)
            else None,
            rate_projection_state=f.rate_state,
            hidden_member_count=f.vis_hidden_members,
            hidden_site_count=f.vis_hidden_sites,
            deep_link_target_count=0 if f.locator_missing else f.dl_n,
            member_expansion_state="unexpandable" if f.q_unlistable
            else "expanded",
            query_redundancy_decision=f.q_decision,
            pd_wording_state=f.q_pd,
            audience_injection_blocked=bool(f.injection and f.injection_blocked),
            counterevidence_rule_matches=f.ce_matched,
            model_evidence_role=f.model_role,
        )

    trace = (D10TraceLeaf(
        trace_kind="admission_replay" if replay else "evaluation_identity",
        stable_core_ref=stable_core,
        content_identity=identity,
        replay_byte_equal=replay,
        terminal_state=terminal,
    ),)

    source: List[D10SourceLeaf] = []
    if disposition_or_gate not in GATE_DISPOSITIONS:
        for member in sorted(typed.members, key=lambda m: m.member_ref):
            source.append(D10SourceLeaf(
                member_ref=member.member_ref,
                source_locator_ref=member.source_locator_refs[0]
                if member.source_locator_refs else None,
                resolution_state=member.locator_resolution_state,
                site_stable_id=member.site_stable_id,
                subject_stable_id=member.subject_stable_id,
            ))

    forbidden = _build_forbidden(f, disposition_or_gate, reason)
    return D10RunResult(
        disposition_or_gate=disposition_or_gate,
        primary_reason=reason,
        unit=unit,
        gate=gate,
        trace=tuple(trace),
        source=tuple(source),
        forbidden=tuple(forbidden),
        evaluation_content_identity=identity,
        stable_core_ref=stable_core,
        replay_byte_equal=replay,
        terminal_state=terminal,
    )


def _build_forbidden(f: D10Facts, disposition_or_gate: str,
                     reason: str) -> List[D10ForbiddenLeaf]:
    """Forbidden-leaf set derived from typed facts + contract rules; never
    from catalog labels."""
    out: List[D10ForbiddenLeaf] = []
    if disposition_or_gate in GATE_DISPOSITIONS:
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition=None,
            gate_kind=None, change_kind=None,
            reason_code=f"zero_medical_output:{reason}"))
        return out
    ch = f.change
    derived = derive_change(ch) if ch else None
    if ch is None or ch.get("basis") == "full" or f.replay:
        for kind_name in CHANGE_KIND_FORBIDDEN_FOR_NON_DATA:
            out.append(D10ForbiddenLeaf(
                leaf_kind="medical_unit", expected_disposition=None,
                gate_kind=None, change_kind=kind_name,
                reason_code="initial_full_or_replay_no_change_unit"))
    if derived and derived[3]:
        for kind_name in CHANGE_KIND_FORBIDDEN_FOR_NON_DATA:
            out.append(D10ForbiddenLeaf(
                leaf_kind="medical_unit", expected_disposition=None,
                gate_kind=None, change_kind=kind_name,
                reason_code="non_data_change_analysis_only"))
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition=None,
            gate_kind=None, change_kind=None,
            reason_code="non_data_change_not_clinical"))
    if f.den_state == "closed_zero" or f.den_value == 0:
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition="negative",
            gate_kind=None, change_kind=None,
            reason_code="zero_event_not_negative"))
    if any(code in STIGMA_CODES for code in f.comp_reasons):
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition="positive",
            gate_kind=None, change_kind=None,
            reason_code="small_site_no_stigma"))
    if f.hit != "not_applicable" and not any(
            source in ("typed_member", "verified_measure")
            for source in f.sources):
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition="positive",
            gate_kind=None, change_kind=None,
            reason_code="nontyped_evidence_no_positive"))
    if f.kind == "project_efficacy_trend" and (
            f.efficacy_missing
            or (f.treatment_role_required and not f.assignment_present)):
        out.append(D10ForbiddenLeaf(
            leaf_kind="medical_unit", expected_disposition="positive",
            gate_kind=None, change_kind=None,
            reason_code="efficacy_gate_no_positive"))
    return out
