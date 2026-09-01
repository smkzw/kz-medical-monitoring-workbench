"""D10 runtime negative, static-closure and fail-closed contract tests.

These tests prove the clean-semantics boundary of the production runtime
(``d10_contracts.py`` / ``d10_evaluator.py``):

* static closure: the runtime never imports/reads artifact files, generators,
  the oracle, the registry, the quota manifest, the verifier or tests, and
  never branches on case/fixture/test ids, mutation metadata/class,
  descriptions, ``SYN-*`` strings or synthetic revision-hash conventions;
* the opaque ``mutation_context`` / ``anti_overfit_variant`` audit metadata is
  never read by the evaluator (proved statically and behaviorally);
* the accepted-membership authority boundary: the evaluator requires an
  immutable ``D10EvaluationAuthority`` (built by the test-only adapter from the
  independent fixture-authority registry) and fails closed before medical
  computation when the submitted project/run/snapshot identity, submitted
  source revision-content subset / locator set, or decisive ModelEvidence pin
  diverges from authority -- even for a fully self-consistent, locally
  re-signed substitution;
* the five final artifact semantic gates fail closed and report the exact
  fail-closed reason;
* the control-plane/routing/handoff gates emit zero medical units.

The test-only adapter reads the frozen catalog and fixture-authority registry
to obtain clean baseline envelopes and authorities; every tamper is applied to
the closed typed objects while the authority is held unchanged, so assertions
challenge semantic rebuilding rather than succeeding only because an obvious
hash was left stale.
"""

from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path
from typing import Any, Callable, List, Tuple
from unittest.mock import patch

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as adapter  # noqa: E402
from mm_r4 import d10_evaluator as evaluator  # noqa: E402
from mm_r4.d10_contracts import (  # noqa: E402
    AdmissionGate,
    D10ContractError,
    DeepLink,
    MutationContext,
    SourceRevisionPair,
    d10_canonical_json,
    d10_content_hash,
    d10_sha256_text,
    validate_typed_input,
)

_RUNTIME_FILES = (
    _R4_SRC / "mm_r4" / "d10_contracts.py",
    _R4_SRC / "mm_r4" / "d10_evaluator.py",
)

_FORBIDDEN_IMPORT_TOKENS = (
    "oracle", "registry", "quota", "verifier", "adapter", "generator",
    "fixture", "pytest", "unittest", "artifact",
)
_FORBIDDEN_FILE_READ_CALLS = (
    "open(", "json.load", "Path(", "read_text", "read_bytes", "load_json",
)
_MUTATION_METADATA_TOKENS = (
    "mutation_context", "anti_overfit_variant", "mutation_class",
    "variant_id", "base_fixture_id",
)


def _sha(value: Any) -> str:
    """Canonical sha256 over a value (the ordinary local hash recipe)."""
    return d10_sha256_text(d10_canonical_json(value))


def _content_hash(value: Any, own_key: str) -> str:
    return d10_content_hash(value, own_key)


def _case_typed(cid: str) -> Any:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    case = next(c for c in catalog["cases"] if c["case_id"] == cid)
    return adapter.build_typed_input(case["typed_input"])


def _authority_for(cid: str) -> Any:
    """Immutable evaluation authority for a case, built by the test-only
    adapter from the independent fixture-authority registry."""
    authority = adapter.load_authority()
    entry = next(e for e in authority["entries"] if e["case_id"] == cid)
    return adapter.build_authority(entry)


def _find_case(predicate: Callable[[Any], bool]) -> Tuple[str, Any]:
    """First catalog case whose built typed input satisfies ``predicate``.
    Selection is by explicit typed facts (never by case id), so the test stays
    robust to catalog renumbering."""
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    for case in catalog["cases"]:
        typed = adapter.build_typed_input(case["typed_input"])
        if predicate(typed):
            return case["case_id"], typed
    raise AssertionError("no catalog case satisfies the typed-fact predicate")


class TestD10RuntimeStaticClosure(unittest.TestCase):
    """The runtime source carries no forbidden imports, file reads, or
    test-intent branches."""

    def test_no_forbidden_imports(self) -> None:
        problems: List[str] = []
        for path in _RUNTIME_FILES:
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped.startswith(("import ", "from ")):
                    continue
                low = stripped.lower()
                if any(token in low for token in _FORBIDDEN_IMPORT_TOKENS):
                    problems.append(f"{path.name}: {stripped}")
        self.assertEqual(problems, [], f"forbidden imports: {problems}")

    def test_no_file_reading_in_runtime(self) -> None:
        problems: List[str] = []
        for path in _RUNTIME_FILES:
            text = path.read_text(encoding="utf-8")
            for call in _FORBIDDEN_FILE_READ_CALLS:
                if call in text:
                    problems.append(f"{path.name}: {call}")
        self.assertEqual(problems, [], f"file reads: {problems}")

    def test_no_mutation_metadata_in_evaluator(self) -> None:
        """The evaluator never references the opaque audit metadata."""
        text = (_R4_SRC / "mm_r4" / "d10_evaluator.py").read_text(
            encoding="utf-8")
        problems = [token for token in _MUTATION_METADATA_TOKENS
                    if token in text]
        self.assertEqual(problems, [],
                         f"evaluator references audit metadata: {problems}")


class TestD10MutationContextIsOpaque(unittest.TestCase):
    """The opaque audit metadata never changes a deterministic outcome."""

    def test_mutation_context_does_not_change_result(self) -> None:
        typed = _case_typed("D10-CASE-001")
        authority = _authority_for("D10-CASE-001")
        baseline = evaluator.evaluate(typed, authority)

        tampered = dataclasses.replace(
            typed,
            mutation_context=MutationContext(
                mutation_class="adversarial_probe",
                desc="not a real clinical fact",
                variant_id=999,
                base_fixture_id="FAKE"),
            anti_overfit_variant=None,
        )
        probed = evaluator.evaluate(tampered, authority)

        self.assertEqual(probed.disposition_or_gate,
                         baseline.disposition_or_gate)
        self.assertEqual(probed.evaluation_content_identity,
                         baseline.evaluation_content_identity)
        self.assertEqual(probed.trace, baseline.trace)
        self.assertEqual(probed.source, baseline.source)


class TestD10EvaluationAuthorityBoundary(unittest.TestCase):
    """The evaluator requires the immutable authority and fails closed on any
    accepted-membership divergence, before medical computation."""

    def test_authority_missing_fails_closed(self) -> None:
        typed = _case_typed("D10-CASE-001")
        with patch.object(evaluator, "project_facts",
                          side_effect=AssertionError(
                              "authority gate must precede project_facts")):
            result = evaluator.evaluate(typed, None)
        self.assertEqual(result.disposition_or_gate, "global_gate")
        self.assertEqual(result.primary_reason, "evaluation_authority_missing")
        self.assertIsNone(result.unit)

    def test_authority_identity_mismatch_fails_closed(self) -> None:
        typed = _case_typed("D10-CASE-001")
        authority = _authority_for("D10-CASE-001")
        tampered = dataclasses.replace(typed, snapshot_ref="SYN-D10-SNAP-999")
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "global_gate")
        self.assertEqual(result.primary_reason, "authority_identity_mismatch")
        self.assertIsNone(result.unit)

    def test_valid_source_subset_matches_baseline(self) -> None:
        """A legal submitted subset remains equivalent to the baseline."""
        cid, typed = _find_case(
            lambda t: len(t.source_revision_content_pairs) == 1)
        authority = _authority_for(cid)
        baseline = evaluator.evaluate(typed, authority)

        current = typed.source_revision_content_pairs[0]
        locator_ids = sorted({locator
                              for member in typed.members
                              for locator in member.source_locator_refs}
                             | {ref.locator_id for ref in typed.evidence_refs})
        alternate_revision = f"{current.revision_id}-alternate"
        alternate = SourceRevisionPair(
            revision_id=alternate_revision,
            content_hash=d10_sha256_text(d10_canonical_json({
                "revision_id": alternate_revision,
                "source_locators": locator_ids,
            })),
        )
        expanded_authority = dataclasses.replace(
            authority,
            accepted_source_revision_content_pairs=(
                *authority.accepted_source_revision_content_pairs,
                alternate,
            ),
        )
        subset_result = evaluator.evaluate(typed, expanded_authority)
        self.assertNotEqual(subset_result.primary_reason,
                            "source_authority_mismatch")
        self.assertEqual(subset_result, baseline)

    def test_external_pair_catalog_cases_fail_by_source_authority(self) -> None:
        """External submitted pairs are evaluation attacks, never authority."""
        for cid in ("D10-CASE-078", "D10-CASE-093",
                    "D10-CASE-107", "D10-CASE-295"):
            typed = _case_typed(cid)
            authority = _authority_for(cid)
            self.assertGreaterEqual(len(typed.source_revision_content_pairs), 2,
                                    cid)
            with patch.object(evaluator, "project_facts",
                              side_effect=AssertionError(
                                  "source authority gate must precede project_facts")):
                result = evaluator.evaluate(typed, authority)
            self.assertEqual(result.disposition_or_gate, "integrity_gate", cid)
            self.assertEqual(result.primary_reason,
                             "source_authority_mismatch", cid)
            self.assertIsNone(result.unit, cid)
            self.assertEqual(result.source, (), cid)

            # The unaccepted pair alone must still fail specifically by
            # authority membership, rather than falling through to medical
            # computation or an envelope-prefix convention.
            only_unaccepted = dataclasses.replace(
                typed,
                source_revision_content_pairs=(
                    typed.source_revision_content_pairs[-1],))
            with patch.object(evaluator, "project_facts",
                              side_effect=AssertionError(
                                  "source authority gate must precede project_facts")):
                rejected = evaluator.evaluate(only_unaccepted, authority)
            self.assertEqual(rejected.disposition_or_gate, "integrity_gate", cid)
            self.assertEqual(rejected.primary_reason,
                             "source_authority_mismatch", cid)
            self.assertIsNone(rejected.unit, cid)

    def test_model_evidence_removal_fails_by_model_authority(self) -> None:
        cid, typed = _find_case(lambda t: t.model_evidence is not None)
        authority = _authority_for(cid)
        removed = dataclasses.replace(typed, model_evidence=None)
        with patch.object(evaluator, "project_facts",
                          side_effect=AssertionError(
                              "model authority gate must precede project_facts")):
            result = evaluator.evaluate(removed, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "model_authority_mismatch")
        self.assertIsNone(result.unit)
        self.assertEqual(result.source, ())


class TestD10EnsembleSizePinFailClosed(unittest.TestCase):
    """The D10 ``ModelEvidence`` pin requires ``ensemble_size >= 1`` (R4
    plan: 0 / negative fail closed at the pin, before any medical
    computation)."""

    def _model_case(self) -> Tuple[Any, Any]:
        cid, typed = _find_case(lambda t: t.model_evidence is not None)
        return cid, typed

    def test_ensemble_size_zero_rejected_at_pin(self) -> None:
        cid, typed = self._model_case()
        model = dataclasses.replace(typed.model_evidence, ensemble_size=0)
        tampered = dataclasses.replace(typed, model_evidence=model)
        with self.assertRaises(D10ContractError):
            validate_typed_input(tampered)

    def test_ensemble_size_zero_fails_closed_before_medical_computation(
            self) -> None:
        cid, typed = self._model_case()
        authority = _authority_for(cid)
        model = dataclasses.replace(typed.model_evidence, ensemble_size=0)
        tampered = dataclasses.replace(typed, model_evidence=model)
        with self.assertRaises(D10ContractError):
            evaluator.evaluate(tampered, authority)

    def test_ensemble_size_negative_rejected_at_pin(self) -> None:
        cid, typed = self._model_case()
        model = dataclasses.replace(typed.model_evidence, ensemble_size=-1)
        tampered = dataclasses.replace(typed, model_evidence=model)
        with self.assertRaises(D10ContractError):
            validate_typed_input(tampered)

    def test_ensemble_size_one_remains_valid_at_pin(self) -> None:
        cid, typed = self._model_case()
        model = dataclasses.replace(typed.model_evidence, ensemble_size=1)
        valid = dataclasses.replace(typed, model_evidence=model)
        validate_typed_input(valid)  # must not raise


class TestD10FailClosedGates(unittest.TestCase):
    """Each gate fails closed with zero medical output on tampering."""

    def _base(self) -> Tuple[Any, Any]:
        cid = "D10-CASE-001"
        return _case_typed(cid), _authority_for(cid)

    def test_integrity_gate_on_decision_id_tamper(self) -> None:
        typed, authority = self._base()
        vis = typed.visibility_decision
        tampered_vis = dataclasses.replace(vis, decision_id="0" * 64)
        tampered = dataclasses.replace(typed, visibility_decision=tampered_vis)
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertIsNone(result.unit)
        self.assertIsNotNone(result.gate)

    def test_integrity_gate_on_denominator_tamper(self) -> None:
        typed, authority = self._base()
        den = typed.denominator
        tampered_den = dataclasses.replace(
            den, denominator_value=den.denominator_value + 1)
        tampered = dataclasses.replace(typed, denominator=tampered_den)
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")

    def test_integrity_gate_on_negative_denominator(self) -> None:
        typed, authority = self._base()
        den = typed.denominator
        tampered_den = dataclasses.replace(
            den, denominator_value=-1, recomputed_value=-1)
        tampered = dataclasses.replace(typed, denominator=tampered_den)
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "invalid_numeric")

    def test_integrity_gate_on_duplicate_source_revision(self) -> None:
        typed, authority = self._base()
        pair = typed.source_revision_content_pairs[0]
        tampered = dataclasses.replace(
            typed, source_revision_content_pairs=(pair, pair))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "duplicate_content_identity")

    def test_integrity_gate_on_audience_injection(self) -> None:
        typed, authority = self._base()
        audience = typed.audience_text
        tampered_audience = dataclasses.replace(
            audience, engineering_reference_attempt=True, injection_blocked=False)
        tampered = dataclasses.replace(typed, audience_text=tampered_audience)
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "audience_injection_blocked")

    def test_global_gate_on_scope_mismatch(self) -> None:
        typed, authority = self._base()
        sb = typed.project_scope_binding
        tampered_sb = dataclasses.replace(sb, scope_equality_decision="mismatch")
        tampered = dataclasses.replace(typed, project_scope_binding=tampered_sb)
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "global_gate")


class TestD10FiveFinalArtifactGates(unittest.TestCase):
    """One strong, independently named re-sign/tamper test per final artifact
    semantic gate, each asserting the exact fail-closed reason."""

    def test_measure_origin_partition_disjointness_reject(self) -> None:
        cid, typed = _find_case(
            lambda t: t.measure_origin_binding is not None
            and t.measure_origin_binding.origin_decision
            == "all_verified_same_origin"
            and t.measure_origin_binding.verified_risk_refs)
        authority = _authority_for(cid)
        mob = typed.measure_origin_binding
        new_distinct = (mob.verified_risk_refs[0],)
        new_candidate = tuple(sorted(
            set(mob.candidate_risk_refs) | set(new_distinct)))
        base = dataclasses.replace(
            mob, distinct_risk_refs=new_distinct,
            candidate_risk_refs=new_candidate)
        tampered = dataclasses.replace(
            base,
            candidate_partition_hash=_sha(sorted(set(new_candidate))),
            binding_hash=_content_hash(
                evaluator._origin_binding_dict(base), "binding_hash"))
        result = evaluator.evaluate(
            dataclasses.replace(typed, measure_origin_binding=tampered),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "measure_origin_binding_tamper")
        self.assertIsNone(result.unit)

    def test_query_partition_disjoint_closed_union_reject(self) -> None:
        cid, typed = _find_case(
            lambda t: t.query_decision.decision == "project_delta_present"
            and not t.query_decision.covered_member_refs
            and t.query_decision.uncovered_member_refs)
        authority = _authority_for(cid)
        qd = typed.query_decision
        members = [m.member_ref for m in typed.members]
        overlap_ref = members[0]
        new_covered = (overlap_ref,)
        new_uncovered = tuple(members)  # overlap_ref appears in both
        unit_hash = _sha(sorted(set(members)))
        identity = _sha({"member_ref": overlap_ref})
        proof = {
            "unit_member_refs": sorted(set(members)),
            "covered_member_refs": list(new_covered),
            "uncovered_member_refs": list(new_uncovered),
            "member_query_content_identities": [identity],
        }
        base = dataclasses.replace(
            qd, covered_member_refs=new_covered,
            uncovered_member_refs=new_uncovered,
            member_query_content_identities=(identity,),
            unit_member_set_hash=unit_hash,
            coverage_proof_hash=_sha(proof))
        tampered = dataclasses.replace(
            base, query_content_hash=_content_hash(
                evaluator._query_decision_dict(base), "query_content_hash"))
        result = evaluator.evaluate(
            dataclasses.replace(typed, query_decision=tampered), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "query_redundancy_tamper")
        self.assertIsNone(result.unit)

    def test_hidden_member_pair_never_in_deep_link_target(self) -> None:
        cid, typed = _find_case(
            lambda t: t.visibility_decision.hidden_member_refs)
        authority = _authority_for(cid)
        vis = typed.visibility_decision
        member_by_ref = {m.member_ref: m for m in typed.members}
        hidden_ref = vis.hidden_member_refs[0]
        hidden = member_by_ref[hidden_ref]
        leak = DeepLink(
            target_kind="subject_site_pair",
            subject_ref=hidden.subject_stable_id,
            site_ref=hidden.site_stable_id,
            member_object_ref=None,
            visibility_decision_ref=vis.decision_id,
            return_state_key="SYN-D10-RET-LEAK-001",
        )
        result = evaluator.evaluate(
            dataclasses.replace(typed, deep_links=typed.deep_links + (leak,)),
            authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "deep_link_target_tamper")
        self.assertIsNone(result.unit)

    def test_source_authority_rejects_self_consistent_substitution(self) -> None:
        # A fully self-consistent revision/content/locator substitution: the
        # revision id is swapped (plausible prefix) and the content hash is
        # re-signed over the FULL rebuilt locator set, so the internal hash
        # recomputation (source_hash_bad) is satisfied.  The independent
        # authority is held unchanged, so only accepted source membership can
        # reject it.
        cid = "D10-CASE-001"
        typed = _case_typed(cid)
        authority = _authority_for(cid)
        pair = typed.source_revision_content_pairs[0]
        new_revision = "SRC-REV-001-001-copy"  # preserves the accepted prefix
        locator_ids = evaluator._locator_ids(typed)
        tampered = dataclasses.replace(
            typed,
            source_revision_content_pairs=(
                dataclasses.replace(
                    pair, revision_id=new_revision,
                    content_hash=_sha({
                        "revision_id": new_revision,
                        "source_locators": locator_ids})),))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "source_authority_mismatch")
        self.assertIsNone(result.unit)

    def test_model_authority_rejects_self_consistent_substitution(self) -> None:
        # A fully self-consistent model substitution: model_version changed and
        # binding/output re-signed so the internal recomputation (model_hash_bad)
        # is satisfied.  The independent authority pin is held unchanged, so only
        # the accepted ModelEvidence pin can reject it.
        cid, typed = _find_case(
            lambda t: t.model_evidence is not None
            and t.model_evidence.role == "candidate_explanation")
        authority = _authority_for(cid)
        model = typed.model_evidence
        swapped = dataclasses.replace(model, model_version="SYN-D10-MODEL-V2")
        binding = _sha(evaluator._model_binding_dict(swapped))
        tampered = dataclasses.replace(
            swapped, model_binding_hash=binding,
            output_hash=_sha({
                "output_identity": swapped.output_identity,
                "model_binding_hash": binding,
                "permitted_leaf": swapped.permitted_leaf,
                "adjudication_state": swapped.adjudication_state}))
        result = evaluator.evaluate(
            dataclasses.replace(typed, model_evidence=tampered), authority)
        self.assertEqual(result.disposition_or_gate, "integrity_gate")
        self.assertEqual(result.primary_reason, "model_authority_mismatch")
        self.assertIsNone(result.unit)


class TestD10ZeroMedicalUnitGates(unittest.TestCase):
    """control-plane / routing / handoff gates emit zero medical units."""

    def _base(self) -> Tuple[Any, Any]:
        cid = "D10-CASE-001"
        return _case_typed(cid), _authority_for(cid)

    def _assert_zero_medical(self, result: Any) -> None:
        self.assertIsNone(result.unit, "gate must emit zero medical units")
        self.assertIsNotNone(result.gate)
        self.assertEqual(result.source, ())
        self.assertIsNone(result.stable_core_ref)

    def test_comparison_set_gate_zero_medical_units(self) -> None:
        typed, authority = self._base()
        es = typed.expected_set
        tampered = dataclasses.replace(
            typed,
            expected_set=dataclasses.replace(
                es, expected_set_state="control_plane_gate",
                admission_gate=AdmissionGate(
                    gate_kind="comparison_set_gate", reason_codes=())))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "comparison_set_gate")
        self.assertEqual(result.primary_reason, "control_plane_comparison_gate")
        self._assert_zero_medical(result)

    def test_window_pair_gate_zero_medical_units(self) -> None:
        typed, authority = self._base()
        es = typed.expected_set
        tampered = dataclasses.replace(
            typed,
            expected_set=dataclasses.replace(
                es, expected_set_state="control_plane_gate",
                admission_gate=AdmissionGate(
                    gate_kind="window_pair_gate", reason_codes=())))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "window_pair_gate")
        self.assertEqual(result.primary_reason, "control_plane_window_pair_gate")
        self._assert_zero_medical(result)

    def test_routing_gate_zero_medical_units(self) -> None:
        typed, authority = self._base()
        sd = typed.signal_definition
        tampered = dataclasses.replace(
            typed, signal_definition=dataclasses.replace(
                sd, clinical_claim_token="unresolved"))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "routing_gate")
        self.assertEqual(result.primary_reason, "claim_token_unresolved")
        self._assert_zero_medical(result)

    def test_handoff_gate_zero_medical_units(self) -> None:
        typed, authority = self._base()
        sd = typed.signal_definition
        tampered = dataclasses.replace(
            typed, signal_definition=dataclasses.replace(
                sd, clinical_claim_token="formal_benefit_risk_conclusion",
                d10_action="handoff_only"))
        result = evaluator.evaluate(tampered, authority)
        self.assertEqual(result.disposition_or_gate, "handoff_gate")
        self.assertEqual(result.primary_reason, "handoff_only_no_medical_unit")
        self._assert_zero_medical(result)


class TestD10Determinism(unittest.TestCase):
    """Same immutable typed content yields byte-identical results."""

    def test_replay_byte_equal(self) -> None:
        typed = _case_typed("D10-CASE-001")
        authority = _authority_for("D10-CASE-001")
        first = evaluator.evaluate(typed, authority)
        second = evaluator.evaluate(typed, authority)
        self.assertEqual(first.disposition_or_gate, second.disposition_or_gate)
        self.assertEqual(first.evaluation_content_identity,
                         second.evaluation_content_identity)
        self.assertEqual(first.trace, second.trace)
        self.assertEqual(first.source, second.source)


if __name__ == "__main__":
    unittest.main()
