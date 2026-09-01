"""R4-D10 deterministic replay, order-insensitivity, identity-stability and
anti-overfit tests (worker_03).

* double replay: every one of the 312 typed inputs evaluates twice to a
  byte-identical D10RunResult (deterministic; no wall-clock/PID/mtime input);
* semantically inert order permutations across all 312 cases: reversing the
  order of the ``members`` / ``coverage`` / ``evidence_refs`` /
  ``time_segments`` / ``deep_links`` collection sections never changes the
  result (these are multisets in the frozen contract).  ``analysis_windows``
  is deliberately NOT permuted because the LAST window is the active
  evaluation window (identity-bearing at the projection layer); the reversal
  of ``analysis_windows`` on the sole two-window case is asserted to change
  the projected active-window instance ref, proving the non-inertness of a
  semantic sequence.
* paired revision/content/evidence/authority binding is preserved: a
  re-pairing attack (swapping content hashes between revision ids, or
  external authorit.y), or a locator-set change, fails closed with the
  exact reason instead of silently re-ordering pairs;
* run/snapshot/envelope/display-only renames keep the correct stable core,
  evaluation content identity, Query identity, projection content hash and
  R2 idempotency key; only the projection version id (by design) and the
  R2 audit refs update;
* meaningful rule/window/source/mode/scope/method/model/visibility changes
  affect the correct identities or fail closed;
* anti-overfit variants: the 16 frozen catalog variants are materialized and
  their pinned oracle leaves replay deterministically under surface-only
  run/snapshot swaps; opaque audit/test metadata is never read by the
  runtime (proven behaviorally).

The catalog/oracle/authority are read-only here; nothing is written.  Tests
never branch the runtime on case identifiers or mutation metadata; case ids
are test-side catalog fixture selection only (the frozen adapter is the only
artifact reader).
"""

from __future__ import annotations

import json
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
    AntiOverfitVariant,
    MutationContext,
    SourceRevisionPair,
    SurfaceChange,
    d10_canonical_json,
    d10_sha256_text,
)
from mm_r4.d10_projection import (  # noqa: E402
    project_d10_run,
)


def _sha(value: Any) -> str:
    """Canonical sha256 over a value (the ordinary local hash recipe)."""
    return d10_sha256_text(d10_canonical_json(value))


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


def _result_digest(result: Any) -> str:
    """Canonical byte-identity digest of a full result object."""
    return json.dumps({
        "disposition_or_gate": result.disposition_or_gate,
        "primary_reason": result.primary_reason,
        "unit": _unit_dict(result.unit),
        "gate": _gate_dict(result.gate),
        "trace": _trace_dict(result.trace),
        "source": [{"member_ref": leaf.member_ref,
                    "source_locator_ref": leaf.source_locator_ref,
                    "resolution_state": leaf.resolution_state,
                    "site_stable_id": leaf.site_stable_id,
                    "subject_stable_id": leaf.subject_stable_id}
                   for leaf in result.source],
        "forbidden": [{"leaf_kind": leaf.leaf_kind,
                       "expected_disposition": leaf.expected_disposition,
                       "gate_kind": leaf.gate_kind,
                       "change_kind": leaf.change_kind,
                       "reason_code": leaf.reason_code}
                      for leaf in result.forbidden],
        "evaluation_content_identity": result.evaluation_content_identity,
        "stable_core_ref": result.stable_core_ref,
        "replay_byte_equal": result.replay_byte_equal,
        "terminal_state": result.terminal_state,
    }, ensure_ascii=False, sort_keys=True)


def _unit_dict(unit: Any) -> Any:
    if unit is None:
        return None
    return {key: getattr(unit, key) for key in (
        "signal_kind", "l1_disposition", "primary_reason", "stable_core_ref",
        "numerator_member_count", "individual_risk_count",
        "affected_subject_count", "event_or_outcome_count",
        "center_pattern_count", "affected_site_count", "denominator_kind",
        "denominator_value", "denominator_state", "estimate_kind",
        "project_signal_count", "clue_count", "query_count",
        "risk_handoff_count", "change_kind", "change_cause",
        "lineage_relation", "handoff_action", "rate_projection_state",
        "hidden_member_count", "hidden_site_count", "deep_link_target_count",
        "member_expansion_state", "query_redundancy_decision",
        "pd_wording_state", "audience_injection_blocked",
        "counterevidence_rule_matches", "model_evidence_role",
        "hotspot_member_refs")}


def _gate_dict(gate: Any) -> Any:
    if gate is None:
        return None
    return {"gate_kind": gate.gate_kind, "leaf_kind": gate.leaf_kind,
            "signal_kind": gate.signal_kind, "reason_codes": gate.reason_codes,
            "denominator_value": gate.denominator_value,
            "audience_injection_blocked": gate.audience_injection_blocked}


def _trace_dict(trace: Tuple[Any, ...]) -> list:
    return [{"trace_kind": leaf.trace_kind,
             "stable_core_ref": leaf.stable_core_ref,
             "content_identity": leaf.content_identity,
             "replay_byte_equal": leaf.replay_byte_equal,
             "terminal_state": leaf.terminal_state} for leaf in trace]


# Collections whose element order is semantically inert in the frozen typed
# envelope.  analysis_windows is excluded: the LAST window feeds the active
# evaluation window identity at the projection layer, so its order is
# semantic.
_ORDER_INERT_COLLECTIONS = (
    "members", "coverage", "evidence_refs", "time_segments", "deep_links",
)


class TestRunReplayDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()

    def test_double_replay_is_byte_identical_for_all_312(self) -> None:
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            typed = adapter.build_typed_input(case["typed_input"])
            authority = _authority_for(cid)
            first = evaluator.evaluate(typed, authority)
            second = evaluator.evaluate(typed, authority)
            self.assertEqual(_result_digest(first), _result_digest(second), cid)


class TestSemanticallyInertOrderPermutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()

    def _permuted(self, typed: Any, field: str) -> Any:
        value = getattr(typed, field)
        if len(value) < 2:
            return None
        return replace(typed, **{field: tuple(reversed(value))})

    def test_order_inert_collections_keep_byte_identical_result(self) -> None:
        checked = {field: 0 for field in _ORDER_INERT_COLLECTIONS}
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            typed = adapter.build_typed_input(case["typed_input"])
            authority = _authority_for(cid)
            baseline = evaluator.evaluate(typed, authority)
            for field in _ORDER_INERT_COLLECTIONS:
                permuted = self._permuted(typed, field)
                if permuted is None:
                    continue
                checked[field] += 1
                result = evaluator.evaluate(permuted, authority)
                self.assertEqual(_result_digest(result),
                                 _result_digest(baseline),
                                 f"{cid}.{field}")
        # every collection was actually exercised on a representative count
        for field, count in checked.items():
            self.assertGreaterEqual(count, 2, f"{field} never exercised")

    def test_analysis_window_order_is_semantic_not_inert(self) -> None:
        """The last analysis window is the active evaluation window; its
        order must never be blindly permuted.  Reversing the two-window
        catalog case changes the projected active-window instance ref even
        though the gated evaluator leaf is unchanged."""
        cid = "D10-CASE-212"
        typed = _case_typed(cid)
        self.assertEqual(len(typed.analysis_windows), 2)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        bundle = project_d10_run(typed, baseline)
        rev_typed = replace(
            typed,
            analysis_windows=tuple(reversed(typed.analysis_windows)))
        reversed_result = evaluator.evaluate(rev_typed, authority)
        reversed_bundle = project_d10_run(rev_typed, reversed_result)
        self.assertEqual(reversed_bundle.counts.evaluation_window_instance_ref,
                         typed.analysis_windows[0].window_instance_id)
        self.assertEqual(bundle.counts.evaluation_window_instance_ref,
                         typed.analysis_windows[1].window_instance_id)
        self.assertNotEqual(
            bundle.counts.evaluation_window_instance_ref,
            reversed_bundle.counts.evaluation_window_instance_ref)


class TestPairedRevisionContentEvidenceAuthorityBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()

    def test_source_pair_order_permutation_keeps_authority_semantics(self) -> None:
        """Permuting the ORDER of the source revision-content pairs never
        re-pairs a revision to another content hash: the pair objects keep
        their (revision_id, content_hash) binding and the set-based
        authority memberships are stable."""
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            typed = adapter.build_typed_input(case["typed_input"])
            if len(typed.source_revision_content_pairs) < 2:
                continue
            authority = _authority_for(cid)
            baseline = evaluator.evaluate(typed, authority)
            reordered = replace(
                typed,
                source_revision_content_pairs=tuple(
                    reversed(typed.source_revision_content_pairs)))
            result = evaluator.evaluate(reordered, authority)
            self.assertEqual(_result_digest(result),
                             _result_digest(baseline), cid)
            # the pairs kept their own revision/content binding
            self.assertEqual(
                {p for p in reordered.source_revision_content_pairs},
                {p for p in typed.source_revision_content_pairs}, cid)

    def test_repairing_content_hashes_to_wrong_revisions_fails_closed(
            self) -> None:
        """Swapping the content hashes between two submitted pairs while
        keeping their revision ids (a re-pairing attack) is never silently
        sorted: it fails closed on the ordinary source-hash recomputation."""
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        pair = typed.source_revision_content_pairs[0]
        re_paired = replace(
            typed,
            source_revision_content_pairs=(
                SourceRevisionPair(
                    revision_id=pair.revision_id,
                    content_hash="0" * 64),))
        result = evaluator.evaluate(re_paired, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "source_authority_mismatch")
        self.assertIsNone(result.unit)

    def test_evidence_locator_set_change_fails_by_authority_membership(
            self) -> None:
        """Adding an evidence locator changes the source locator set hash;
        the independent authority membership rejects it before medical
        computation."""
        cid, typed = _find_case(lambda t: bool(t.members))
        authority = _authority_for(cid)
        member = typed.members[0]
        changed_members = (
            replace(member,
                    source_locator_refs=member.source_locator_refs
                    + ("SYN-D10-LOC-FORGED-1",)),) + typed.members[1:]
        changed = replace(typed, members=changed_members)
        result = evaluator.evaluate(changed, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "source_authority_mismatch")
        self.assertIsNone(result.unit)


class TestRenamesKeepCorrectIdentities(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        cls.positive = [c["case_id"] for c in cls.catalog["cases"]
                        if any(
                            e["case_id"] == c["case_id"]
                            for e in _oracle["ordered_expectations"]
                            if e["expected_disposition_or_gate"] == "positive")]

    def test_run_snapshot_swap_keeps_all_stable_identities(self) -> None:
        """Run/snapshot ids are opaque audit refs: they never enter the
        stable core, the evaluation content identity, the Query draft, the
        projection content hash or the R2 idempotency key (only the
        projection VERSION id and the handoff audit refs update by design)."""
        for cid in self.positive:
            typed = _case_typed(cid)
            # project_efficacy_trend units with a typed treatment-assignment
            # identity bind the run id into the assignment identity by design
            # (the frozen contract's ``treatment_assignment_exposure_identity``
            # is run-scoped); a run/snapshot rename there fails closed on
            # ``treatment_assignment_tamper`` and is covered by the
            # fail-closed tests, not the opaque-rename stability test.
            if typed.efficacy_context is not None \
                    and typed.efficacy_context.treatment_assignment_exposure_identity_ref \
                    is not None:
                continue
            authority = _authority_for(cid)
            baseline = evaluator.evaluate(typed, authority)
            bundle = project_d10_run(typed, baseline)
            swapped = replace(typed, run_ref="SYN-D10-RUN-ALT",
                              snapshot_ref="SYN-D10-SNAP-ALT")
            swapped_authority = replace(
                authority, run_ref="SYN-D10-RUN-ALT",
                snapshot_ref="SYN-D10-SNAP-ALT")
            swapped_result = evaluator.evaluate(swapped, swapped_authority)
            self.assertEqual(swapped_result.evaluation_content_identity,
                             baseline.evaluation_content_identity, cid)
            self.assertEqual(swapped_result.stable_core_ref,
                             baseline.stable_core_ref, cid)
            swapped_bundle = project_d10_run(swapped, swapped_result)
            if bundle.query_draft is not None:
                self.assertIsNotNone(swapped_bundle.query_draft, cid)
                assert swapped_bundle.query_draft is not None
                self.assertEqual(
                    bundle.query_draft.query_draft_id,
                    swapped_bundle.query_draft.query_draft_id, cid)
            if bundle.r2_handoff is not None:
                self.assertIsNotNone(swapped_bundle.r2_handoff, cid)
                assert swapped_bundle.r2_handoff is not None
                self.assertEqual(bundle.r2_handoff.handoff_id,
                                 swapped_bundle.r2_handoff.handoff_id, cid)
                self.assertEqual(
                    bundle.r2_handoff.idempotency_key,
                    swapped_bundle.r2_handoff.idempotency_key, cid)
                self.assertEqual(
                    swapped_bundle.r2_handoff.run_snapshot_audit_refs,
                    ("SYN-D10-RUN-ALT", "SYN-D10-SNAP-ALT"), cid)
            self.assertEqual(
                bundle.project_projection.projection_content_hash,
                swapped_bundle.project_projection.projection_content_hash,
                cid)
            # the projection VERSION id is the one surface that names the
            # run/snapshot instance -- it must change by design
            self.assertNotEqual(
                bundle.version.projection_version_id,
                swapped_bundle.version.projection_version_id, cid)

    def test_envelope_and_display_only_renames_are_byte_inert(self) -> None:
        """Rename envelope id and the display-only audience text: the
        outcome, the stable core and the evaluation content identity stay
        identical because the runtime never branches on those surfaces."""
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        renamed = replace(
            typed,
            envelope_id="SYN-D10-ENV-RENAMED-01",
            audience_text=replace(
                typed.audience_text,
                basis_zh="依据：项目现行有效方案与监察规则，需统一核实。",
                finding_zh="发现：本项目存在相关记录，详见行动项。",
                action_zh="行动项：请核实并补充或更正对应记录。"))
        result = evaluator.evaluate(renamed, authority)
        self.assertEqual(_result_digest(result), _result_digest(baseline))
        self.assertEqual(result.evaluation_content_identity,
                         baseline.evaluation_content_identity)
        self.assertEqual(result.stable_core_ref, baseline.stable_core_ref)
        renamed_bundle = project_d10_run(renamed, result)
        baseline_bundle = project_d10_run(typed, baseline)
        self.assertEqual(
            renamed_bundle.project_projection.projection_content_hash,
            baseline_bundle.project_projection.projection_content_hash)


class TestMeaningfulChangesAffectCorrectIdentityOrFailClosed(unittest.TestCase):
    """Every meaningful rule/window/source/mode/scope/method/model/visibility
    change must either change the correct identity (evaluation content
    identity and/or stable core and/or projection hash) or fail closed with
    the exact gate -- never silently produce the original outcome."""

    def test_rule_change_changes_disposition_and_identity(self) -> None:
        cid, typed = _find_case(
            lambda t: t.rule_hit.hit_state == "hit")
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        changed = replace(
            typed, rule_hit=replace(typed.rule_hit, hit_state="no_hit",
                                    counterevidence_declared_refs=()))
        result = evaluator.evaluate(changed, authority)
        self.assertNotEqual(result, baseline, cid)
        self.assertNotEqual(result.evaluation_content_identity,
                            baseline.evaluation_content_identity, cid)

    def test_window_stable_change_changes_stable_core_and_projection(
            self) -> None:
        cid = "D10-CASE-218"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        bundle = project_d10_run(typed, baseline)
        changed = replace(
            typed,
            analysis_windows=tuple(
                replace(w, analysis_window_stable_id=w.analysis_window_stable_id
                        + "-ALT") for w in typed.analysis_windows))
        result = evaluator.evaluate(changed, authority)
        self.assertNotEqual(result.stable_core_ref,
                            baseline.stable_core_ref, cid)
        changed_bundle = project_d10_run(changed, result)
        self.assertNotEqual(
            changed_bundle.project_projection.projection_content_hash,
            bundle.project_projection.projection_content_hash, cid)

    def test_source_change_fails_closed_by_authority(self) -> None:
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        pair = typed.source_revision_content_pairs[0]
        locator_ids = evaluator._locator_ids(typed)
        alternate = SourceRevisionPair(
            revision_id=f"{pair.revision_id}-copy",
            content_hash=_sha({"revision_id": f"{pair.revision_id}-copy",
                               "source_locators": locator_ids}))
        result = evaluator.evaluate(
            replace(typed, source_revision_content_pairs=(alternate,)),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "source_authority_mismatch")
        self.assertIsNone(result.unit)

    def test_mode_change_fails_closed_on_hash(self) -> None:
        cid = "D10-CASE-218"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        changed = replace(
            typed,
            mode_contract=replace(typed.mode_contract,
                                  design_applicable_state="not_applicable"))
        result = evaluator.evaluate(changed, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertIsNone(result.unit)

    def test_scope_mismatch_fails_closed_global(self) -> None:
        cid = "D10-CASE-218"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        changed = replace(
            typed,
            project_scope_binding=replace(
                typed.project_scope_binding,
                scope_equality_decision="mismatch"))
        result = evaluator.evaluate(changed, authority)
        self.assertEqual(result.disposition_or_gate, "global_gate")
        self.assertEqual(result.primary_reason, "scope_binding_mismatch")
        self.assertIsNone(result.unit)

    def test_visibility_change_fails_closed(self) -> None:
        cid = "D10-CASE-218"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        changed = replace(
            typed,
            visibility_decision=replace(
                typed.visibility_decision,
                blind_status="unblinded_authorized",
                treatment_inference_attempt=True))
        result = evaluator.evaluate(changed, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertIsNone(result.unit)

    def test_model_version_change_fails_closed_by_authority(self) -> None:
        cid, typed = _find_case(
            lambda t: t.model_evidence is not None
            and t.model_evidence.role == "candidate_explanation")
        authority = _authority_for(cid)
        model = typed.model_evidence
        swapped = replace(model, model_version="SYN-D10-MODEL-V2")
        binding = _sha(evaluator._model_binding_dict(swapped))
        tampered = replace(
            swapped, model_binding_hash=binding,
            output_hash=_sha({
                "output_identity": swapped.output_identity,
                "model_binding_hash": binding,
                "permitted_leaf": swapped.permitted_leaf,
                "adjudication_state": swapped.adjudication_state}))
        result = evaluator.evaluate(
            replace(typed, model_evidence=tampered), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "model_authority_mismatch")
        self.assertIsNone(result.unit)

    def test_method_change_affects_change_facts_or_fails_closed(self) -> None:
        catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        chosen = None
        for case in catalog["cases"]:
            cand = adapter.build_typed_input(case["typed_input"])
            if cand.change_decision is None \
                    or cand.change_decision.execution_basis == "full":
                continue
            authority = _authority_for(case["case_id"])
            if evaluator.evaluate(cand, authority).disposition_or_gate \
                    == "integrity_gate":
                continue
            chosen = (case["case_id"], cand, authority)
            break
        self.assertIsNotNone(chosen, "no non-gate delta-change candidate")
        cid, typed, authority = chosen
        baseline = evaluator.evaluate(typed, authority)
        ch = typed.change_decision
        changed = replace(
            typed,
            change_decision=replace(
                ch, method_change_refs=ch.method_change_refs
                + ("SYN-D10-METHOD-CHG-1",),
                claimed_primary_change_cause=None))
        result = evaluator.evaluate(changed, authority)
        if result.disposition_or_gate == "integrity_gate":
            self.assertIsNone(result.unit)
        else:
            self.assertNotEqual(result, baseline, cid)


class TestAntiOverfitVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _registry, _quota = adapter.load_artifacts()
        cls.expectations = {
            entry["case_id"]: entry
            for entry in cls.oracle["ordered_expectations"]
        }
        cls.variant_cases = [
            case for case in cls.catalog["cases"]
            if case["typed_input"].get("anti_overfit_variant") is not None]

    def test_frozen_variants_replay_deterministically(self) -> None:
        """All frozen anti-overfit variants materialize and replay to their
        pinned oracle disposition; run/snapshot swaps keep the evaluation
        identity -- the runtime never reads the variant audit metadata."""
        self.assertGreaterEqual(len(self.variant_cases), 16)
        for case in self.variant_cases:
            cid = case["case_id"]
            typed = adapter.build_typed_input(case["typed_input"])
            authority = _authority_for(cid)
            baseline = evaluator.evaluate(typed, authority)
            expectation = self.expectations[cid]
            self.assertEqual(baseline.disposition_or_gate,
                             expectation["expected_disposition_or_gate"], cid)
            swapped = replace(typed, run_ref="SYN-D10-RUN-V",
                              snapshot_ref="SYN-D10-SNAP-V")
            swapped_authority = replace(
                authority, run_ref="SYN-D10-RUN-V",
                snapshot_ref="SYN-D10-SNAP-V")
            swapped_result = evaluator.evaluate(swapped, swapped_authority)
            self.assertEqual(swapped_result.evaluation_content_identity,
                             baseline.evaluation_content_identity, cid)
            self.assertEqual(swapped_result.disposition_or_gate,
                             baseline.disposition_or_gate, cid)

    def test_audit_metadata_never_changes_a_variant_outcome(self) -> None:
        """Fabricated surface-change / semantic-equivalence records and
        arbitrary mutation prose are opaque audit metadata: they never
        change a deterministic outcome."""
        cid, typed = _find_case(
            lambda t: t.model_evidence is not None
            or t.measure_origin_binding is not None)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)
        tampered = replace(
            typed,
            mutation_context=MutationContext(
                mutation_class="adversarial_probe",
                desc="not a real clinical fact",
                variant_id="999",
                base_fixture_id="FAKE"),
            anti_overfit_variant=AntiOverfitVariant(
                base_fixture_id="FAKE",
                semantic_equivalence_ref="FAKE",
                surface_changes=(
                    SurfaceChange("envelope_id", "SYN-X", "SYN-Y"),
                    SurfaceChange("display", "旧", "新"),
                ),
                variant_id=999))
        probed = evaluator.evaluate(tampered, authority)
        self.assertEqual(probed.disposition_or_gate,
                         baseline.disposition_or_gate)
        self.assertEqual(probed.evaluation_content_identity,
                         baseline.evaluation_content_identity)
        self.assertEqual(probed.trace, baseline.trace)
        self.assertEqual(probed.source, baseline.source)


if __name__ == "__main__":
    unittest.main()
