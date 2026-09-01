"""R4-D10 negative mutation suite (worker_03): independently re-sealed
semantic mutations fail closed; outcome-changing mutations change the exact
disposition; surface-only metadata stays inert.

All tampering is applied to the closed typed objects of accepted catalog
envelopes while the independent evaluation Authority is held unchanged, and
every local hash/binding that the runtime would recompute is re-sealed
coherently (using the runtime's binding recipes) so the assertion challenges
semantic rebuilding -- never a stale hash.  The catalog/oracle/registry/
quota/authority are read-only; nothing is written.

* five Worker-01 final semantic gates, each with an independent reseal:
  measure-origin partition, Query partition, hidden subject-site pair,
  exact source-authority membership and complete ModelEvidence provenance
  -- asserting the exact fail-closed disposition/reason and zero medical
  unit (unit None + empty source + no stable core);
* outcome-changing mutations across coverage / denominator / comparison /
  window pair / cutoff / change / R2 / visibility / evidence / locator /
  numerical boundaries;
* surface-only metadata (audit prose, variant records, display text) stays
  byte-inert.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as adapter  # noqa: E402
from mm_r4 import d10_evaluator as evaluator  # noqa: E402
from mm_r4.d10_contracts import (  # noqa: E402
    MutationContext,
    d10_canonical_json,
    d10_content_hash,
    d10_sha256_text,
)

_ZERO_MEDICAL_GATES = (
    "global_gate", "integrity_gate", "comparison_set_gate",
    "window_pair_gate", "routing_gate", "handoff_gate",
)


def _sha(value: Any) -> str:
    """Canonical sha256 over a value (the ordinary local hash recipe)."""
    return d10_sha256_text(d10_canonical_json(value))


def _content_hash(value: Any, own_key: str) -> str:
    return d10_content_hash(value, own_key)


def _authority_for(cid: str) -> Any:
    authority = adapter.load_authority()
    entry = next(e for e in authority["entries"] if e["case_id"] == cid)
    return adapter.build_authority(entry)


def _case_typed(cid: str) -> Any:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    case = next(c for c in catalog["cases"] if c["case_id"] == cid)
    return adapter.build_typed_input(case["typed_input"])


def _find_case(predicate: Callable[[Any], bool]) -> Tuple[str, Any]:
    """First catalog case whose built typed input satisfies ``predicate``.
    Selection is by explicit typed facts only (never by case id)."""
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    for case in catalog["cases"]:
        typed = adapter.build_typed_input(case["typed_input"])
        if predicate(typed):
            return case["case_id"], typed
    raise AssertionError("no catalog case satisfies the typed-fact predicate")


def _assert_zero_medical(self: unittest.TestCase, result: Any,
                         cid: str = "") -> None:
    self.assertIsNone(result.unit, f"{cid}: gate must emit zero medical units")
    self.assertEqual(result.source, (), f"{cid}: gate carries no source leaves")
    self.assertIsNone(result.stable_core_ref, f"{cid}: gate has no stable core")


class TestFiveWorker01GatesFailClosed(unittest.TestCase):
    """Independently re-sealed semantic mutations for the five accepted
    Worker-01 final gates; each asserts the exact fail-closed reason and a
    zero medical unit."""

    def test_measure_origin_partition_resealed_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.measure_origin_binding is not None
            and t.measure_origin_binding.origin_decision
            == "all_verified_same_origin"
            and len(t.measure_origin_binding.verified_risk_refs) >= 2)
        authority = _authority_for(cid)
        mob = typed.measure_origin_binding
        moved = mob.verified_risk_refs[-1]
        verified = tuple(ref for ref in mob.verified_risk_refs
                         if ref != moved)
        ambiguous = (moved,)
        candidate = tuple(sorted(set(mob.candidate_risk_refs)))
        base = replace(
            mob, verified_risk_refs=verified, ambiguous_risk_refs=ambiguous,
            candidate_risk_refs=candidate,
            candidate_partition_hash=_sha(sorted(set(candidate))))
        re_sealed = replace(
            base, binding_hash=_content_hash(
                evaluator._origin_binding_dict(base), "binding_hash"))
        result = evaluator.evaluate(
            replace(typed, measure_origin_binding=re_sealed), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason,
                         "measure_origin_binding_tamper", cid)
        _assert_zero_medical(self, result, cid)

    def test_query_partition_resealed_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.query_decision.decision == "project_delta_present"
            and t.query_decision.uncovered_member_refs)
        authority = _authority_for(cid)
        qd = typed.query_decision
        members = [m.member_ref for m in typed.members]
        overlap = members[0]
        new_covered = (overlap,)
        new_uncovered = tuple(members)  # overlap appears in BOTH sets
        identity = _sha({"member_ref": overlap})
        unit_hash = _sha(sorted(set(members)))
        proof = {
            "unit_member_refs": sorted(set(members)),
            "covered_member_refs": list(new_covered),
            "uncovered_member_refs": list(new_uncovered),
            "member_query_content_identities": [identity],
        }
        base = replace(
            qd, covered_member_refs=new_covered,
            uncovered_member_refs=new_uncovered,
            member_query_content_identities=(identity,),
            unit_member_set_hash=unit_hash,
            coverage_proof_hash=_sha(proof))
        re_sealed = replace(
            base, query_content_hash=_content_hash(
                evaluator._query_decision_dict(base), "query_content_hash"))
        result = evaluator.evaluate(
            replace(typed, query_decision=re_sealed), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "query_redundancy_tamper", cid)
        _assert_zero_medical(self, result, cid)

    def test_hidden_subject_site_pair_resealed_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.visibility_decision.hidden_member_refs)
        authority = _authority_for(cid)
        vis = typed.visibility_decision
        member_by_ref = {m.member_ref: m for m in typed.members}
        hidden_ref = vis.hidden_member_refs[0]
        hidden = member_by_ref[hidden_ref]
        hidden_pair = (hidden.subject_stable_id, hidden.site_stable_id)
        # re-seal the visibility decision as if the hidden (subject,site)
        # pair were projectable -- the typed algebra stays internally
        # consistent (decision_id re-signed) but the rebuilt projectable
        # pair set cannot contain a hidden member's pair.
        re_sealed_vis = replace(
            vis,
            projectable_subject_site_pairs=(
                tuple(vis.projectable_subject_site_pairs) + (hidden_pair,)))
        re_sealed_vis = replace(
            re_sealed_vis,
            decision_id=_content_hash(
                evaluator._vis_decision_dict(re_sealed_vis), "decision_id"))
        result = evaluator.evaluate(
            replace(typed, visibility_decision=re_sealed_vis), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "visibility_algebra", cid)
        _assert_zero_medical(self, result, cid)

    def test_external_source_pair_fails_by_exact_authority_membership(
            self) -> None:
        """The four corrected-external-pair integrity cases fail by exact
        source-authority membership (never a prefix convention or a stale
        hash) with zero medical output."""
        for cid in ("D10-CASE-078", "D10-CASE-093",
                    "D10-CASE-107", "D10-CASE-295"):
            typed = _case_typed(cid)
            self.assertGreaterEqual(len(typed.source_revision_content_pairs), 2,
                                    cid)
            authority = _authority_for(cid)
            result = evaluator.evaluate(typed, authority)
            self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
            self.assertEqual(result.primary_reason,
                             "source_authority_mismatch", cid)
            _assert_zero_medical(self, result, cid)

    def test_substituted_source_revision_fails_exact_membership(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        pair = typed.source_revision_content_pairs[0]
        locator_ids = evaluator._locator_ids(typed)
        new_revision = "SRC-REV-001-001-copy"
        re_sealed = replace(
            typed,
            source_revision_content_pairs=(
                replace(
                    pair, revision_id=new_revision,
                    content_hash=_sha({"revision_id": new_revision,
                                       "source_locators": locator_ids})),))
        result = evaluator.evaluate(re_sealed, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason,
                         "source_authority_mismatch", cid)
        _assert_zero_medical(self, result, cid)

    def test_model_evidence_removal_fails_complete_provenance(self) -> None:
        cid, typed = _find_case(lambda t: t.model_evidence is not None)
        authority = _authority_for(cid)
        result = evaluator.evaluate(replace(typed, model_evidence=None),
                                    authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason,
                         "model_authority_mismatch", cid)
        _assert_zero_medical(self, result, cid)

    def test_model_source_provenance_substitution_fails_pin(self) -> None:
        cid, typed = _find_case(
            lambda t: t.model_evidence is not None
            and t.model_evidence.source_revision_content_pairs)
        authority = _authority_for(cid)
        model = typed.model_evidence
        pair = model.source_revision_content_pairs[0]
        swapped = replace(
            model,
            source_revision_content_pairs=(
                replace(pair, revision_id=pair.revision_id + "-forged"),))
        binding = _sha(evaluator._model_binding_dict(swapped))
        re_sealed = replace(
            swapped, model_binding_hash=binding,
            output_hash=_sha({
                "output_identity": swapped.output_identity,
                "model_binding_hash": binding,
                "permitted_leaf": swapped.permitted_leaf,
                "adjudication_state": swapped.adjudication_state}))
        result = evaluator.evaluate(
            replace(typed, model_evidence=re_sealed), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason,
                         "model_authority_mismatch", cid)
        _assert_zero_medical(self, result, cid)


class TestOutcomeChangingMutations(unittest.TestCase):
    """Coverage / denominator / comparison / window pair / cutoff / change /
    R2 / visibility / evidence / locator / numerical-boundary mutations all
    change the exact disposition or fail closed (never silent)."""

    def test_coverage_gap_flips_to_required_l1_hole(self) -> None:
        cid = "D10-CASE-001"  # positive project_risk_distribution
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        self.assertEqual(baseline.disposition_or_gate, "positive")
        domain = typed.signal_definition.required_producer_domains[0]
        coverage = tuple(
            replace(c, l0_status="missing")
            if c.producer_domain == domain else c
            for c in typed.coverage)
        result = evaluator.evaluate(
            replace(typed, coverage=coverage), authority)
        self.assertEqual(result.disposition_or_gate, "not_evaluable", cid)
        self.assertEqual(result.primary_reason, "required_l1_hole", cid)
        self.assertIsNotNone(result.unit)

    def test_denominator_recompute_flips_to_integrity_gate(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        den = typed.denominator
        result = evaluator.evaluate(
            replace(typed, denominator=replace(
                den, denominator_value=den.denominator_value + 1)),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "denominator_tamper", cid)
        _assert_zero_medical(self, result, cid)

    def test_zero_denominator_is_not_negative(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        den = typed.denominator
        result = evaluator.evaluate(
            replace(typed, denominator=replace(
                den, denominator_value=0, recomputed_value=0,
                denominator_member_refs=(),
                denominator_state="closed_zero")),
            authority)
        self.assertEqual(result.disposition_or_gate, "not_evaluable", cid)
        self.assertEqual(result.primary_reason,
                         "zero_denominator_not_negative", cid)

    def test_negative_denominator_invalid_numeric_gate(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        den = typed.denominator
        result = evaluator.evaluate(
            replace(typed, denominator=replace(
                den, denominator_value=-1, recomputed_value=-1)),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "invalid_numeric", cid)
        _assert_zero_medical(self, result, cid)

    def test_comparison_gate_flips_to_comparison_set_gate(self) -> None:
        cid, typed = _find_case(
            lambda t: t.signal_definition.signal_kind == "cross_site_pattern"
            and t.comparison_gate.comparison_state == "ready")
        authority = _authority_for(cid)
        result = evaluator.evaluate(
            replace(typed, comparison_gate=replace(
                typed.comparison_gate, comparison_state="insufficient_sites")),
            authority)
        self.assertEqual(result.disposition_or_gate, "comparison_set_gate", cid)
        self.assertEqual(result.primary_reason, "comparison_insufficient_sites",
                         cid)
        _assert_zero_medical(self, result, cid)

    def test_window_pair_gate_flips_to_window_pair_gate(self) -> None:
        cid, typed = _find_case(
            lambda t: t.signal_definition.signal_kind == "project_time_trend"
            and t.window_pair_gate.pair_state == "ready")
        authority = _authority_for(cid)
        result = evaluator.evaluate(
            replace(typed, window_pair_gate=replace(
                typed.window_pair_gate, pair_state="insufficient_windows")),
            authority)
        self.assertEqual(result.disposition_or_gate, "window_pair_gate", cid)
        self.assertEqual(result.primary_reason, "window_pair_insufficient_windows",
                         cid)
        _assert_zero_medical(self, result, cid)

    def test_cutoff_advance_contradiction_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.change_decision is not None
            and t.change_decision.cutoff_advance is not None)
        authority = _authority_for(cid)
        ch = typed.change_decision
        ca = ch.cutoff_advance
        # declare strict_advance while the typed predicates contradict it
        impossible = replace(
            ca, decision_state="strict_advance",
            strict_advance_predicate_passed=False)
        result = evaluator.evaluate(
            replace(typed, change_decision=replace(
                ch, cutoff_advance=impossible)), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "cutoff_advance_tamper", cid)
        _assert_zero_medical(self, result, cid)

    def test_fake_change_claim_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.change_decision is not None
            and t.change_decision.execution_basis != "full"
            and t.change_decision.claimed_clinical_change_kind
            in (None, "continued", "new", "upgraded")
            and t.change_decision.data_change_kind != "resolved")
        authority = _authority_for(cid)
        ch = typed.change_decision
        # claim a resolved kind that the typed change facts cannot produce
        result = evaluator.evaluate(
            replace(typed, change_decision=replace(
                ch, claimed_clinical_change_kind="resolved")), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "fake_change_claim", cid)
        _assert_zero_medical(self, result, cid)

    def test_r2_create_with_prior_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.change_decision is not None
            and t.change_decision.r2_action == "create")
        authority = _authority_for(cid)
        ch = typed.change_decision
        result = evaluator.evaluate(
            replace(typed, change_decision=replace(
                ch, r2_action="create",
                r2_prior_ref_or_none="SYN-D10-R2-PRIOR-FORGED")), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "r2_wrong_prior", cid)
        _assert_zero_medical(self, result, cid)

    def test_visibility_algebra_break_fails_closed(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        vis = typed.visibility_decision
        # projectable and hidden overlap the same member -> algebra break
        member = typed.members[0].member_ref
        overlapping = replace(
            vis,
            projectable_member_refs=vis.projectable_member_refs + (member,),
            hidden_member_refs=vis.hidden_member_refs + (member,),
            visible_n=vis.visible_n + 1)
        re_sealed = replace(
            overlapping,
            decision_id=_content_hash(
                evaluator._vis_decision_dict(overlapping), "decision_id"))
        result = evaluator.evaluate(
            replace(typed, visibility_decision=re_sealed), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "visibility_algebra", cid)
        _assert_zero_medical(self, result, cid)

    def test_locator_unresolvable_flips_to_deep_link_deficient(self) -> None:
        cid, typed = _find_case(
            lambda t: t.rule_hit.hit_state == "hit"
            and any(m.locator_resolution_state == "locatable"
                    for m in t.members)
            and t.denominator.denominator_value > 0)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        self.assertEqual(baseline.disposition_or_gate, "positive", cid)
        member = typed.members[0]
        members = tuple(
            replace(m, locator_resolution_state="unresolvable")
            if m.member_ref == member.member_ref else m
            for m in typed.members)
        result = evaluator.evaluate(replace(typed, members=members), authority)
        self.assertEqual(result.disposition_or_gate, "boundary", cid)
        self.assertEqual(result.primary_reason, "deep_link_deficient", cid)

    def test_counterevidence_partial_flips_to_boundary(self) -> None:
        cid, typed = _find_case(
            lambda t: t.rule_hit.hit_state == "hit"
            and sum(1 for src in t.rule_hit.evidence_sources
                    if src in ("typed_member", "verified_measure")) > 0
            and len(t.rule_hit.counterevidence_declared_refs) >= 2)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        # the frozen candidate is a counterevidence-explained negative
        # (2 declared / 2 matched); leaving one declared ref unmatched flips
        # it to the boundary ``counterevidence_partial``.
        self.assertEqual(baseline.disposition_or_gate, "negative", cid)
        declared = typed.rule_hit.counterevidence_declared_refs
        result = evaluator.evaluate(
            replace(typed, rule_hit=replace(
                typed.rule_hit,
                counterevidence_matched_refs=declared[:1])), authority)
        self.assertEqual(result.disposition_or_gate, "boundary", cid)
        self.assertEqual(result.primary_reason,
                         "counterevidence_partial", cid)

    def test_time_segment_tamper_fails_closed(self) -> None:
        # pick a non-time denominator so the segment tamper does not also
        # trip the denominator recompute gate first
        cid, typed = _find_case(
            lambda t: len(t.time_segments) >= 1
            and t.denominator.denominator_kind
            not in ("subject_time", "exposure_time"))
        authority = _authority_for(cid)
        seg = typed.time_segments[0]
        segments = (replace(
            seg, normalized_duration=seg.normalized_duration + 1),) \
            + typed.time_segments[1:]
        result = evaluator.evaluate(
            replace(typed, time_segments=segments), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason, "time_segment_tamper", cid)
        _assert_zero_medical(self, result, cid)

    def test_numerator_ledger_mismatch_fails_closed(self) -> None:
        cid, typed = _find_case(
            lambda t: t.numerator_ledger.individual_risk_count >= 1)
        authority = _authority_for(cid)
        nl = typed.numerator_ledger
        result = evaluator.evaluate(
            replace(typed, numerator_ledger=replace(
                nl, individual_risk_count=nl.individual_risk_count + 1)),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
        self.assertEqual(result.primary_reason,
                         "numerator_ledger_mismatch", cid)
        _assert_zero_medical(self, result, cid)


class TestSurfaceOnlyMetadataIsInert(unittest.TestCase):
    def test_audit_metadata_and_display_text_never_change_outcome(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        tampered = replace(
            typed,
            mutation_context=MutationContext(
                mutation_class="inert_probe",
                desc="surface-only metadata, no clinical fact",
                variant_id="77",
                base_fixture_id="FAKE"),
            anti_overfit_variant=None)
        probed = evaluator.evaluate(tampered, authority)
        self.assertEqual(probed.disposition_or_gate,
                         baseline.disposition_or_gate)
        self.assertEqual(probed.evaluation_content_identity,
                         baseline.evaluation_content_identity)
        self.assertEqual(probed.trace, baseline.trace)
        self.assertEqual(probed.source, baseline.source)


if __name__ == "__main__":
    unittest.main()
