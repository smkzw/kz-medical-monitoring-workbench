"""Runtime behavior tests for the shared offline ensemble closure.

Proves the decisive R4 closure behaviors (System Design v1.1 §9.2-9.4; plan
steps 9-10) without any real model, harness, service or port:

1. ``ensemble_size`` 0 / negative fails closed BEFORE side effects;
2. single-model runs expose no consensus/agreement leaf and keep residual
   conflicts at ``needs_user_attention`` while the analysis still completes;
3. N-way runs require the same ``input_content_hash`` plus distinct
   ``binding_id`` / ``session_id`` / ``independent_context_hash``; the same
   ``model_id`` on different bindings/sessions is valid;
4. a worker can never adjudicate itself (binding_id/session_id rejection);
5. deterministic evidence verification precedes adjudication: every claimed
   dimension (identity, version, date, unit, source, rule, artifact
   integrity) is compared against an independent typed authority context,
   the ACTUAL worker output digest is recomputed, and any failure blocks
   supporting outcomes;
6. gap search proposes candidates without creating lifecycle risk;
7. every baseline item is locatable to one of the six states with a source
   recheck locator;
8. high-risk or important disagreement stays visible and majority voting
   cannot hide or close it;
9. intake attribution and per-worker uniqueness are sealed before any
   analysis: ``worker_outputs`` keys must equal the output's own
   ``attempt_id`` and resolve to a declared ``AnalysisAttempt``, and each
   output may carry at most one assessment per baseline item plus unique
   finding and gap-proposal ids (cross-worker duplication stays legal).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r2.risk import AdjudicationOutcome  # noqa: E402
from mm_r4.ensemble import (  # noqa: E402
    Adjudicator,
    EnsembleError,
    EnsembleResult,
    EvidenceDigestContext,
    Finding,
    WorkerAnalysisOutput,
    require_positive_ensemble_size,
    run_ensemble,
    search_gaps,
    verify_attempt,
    worker_output_content_hash,
)
from mm_r4.ensemble_contracts import (  # noqa: E402
    VERIFICATION_DIMENSIONS,
    AnalysisAttempt,
    BaselineAssessment,
    GapCandidate,
    ReferenceBaselineItem,
)

_INPUT_HASH = "d" * 64
_ENSEMBLE_ID = "ens-001"


def _sha(char: str = "a") -> str:
    return char * 64


def _baseline(item_id: str = "baseline-001",
              identity: str = "ident-r1-safety-001",
              locator: str = "loc-orig-001") -> ReferenceBaselineItem:
    return ReferenceBaselineItem(
        item_id=item_id,
        source_kind="legacy_profile",
        source_locator_ids=(locator,),
        source_revision_id="rev-001",
        snapshot_id="snap-001",
        claimed_identity=identity,
        temporal_window="study-period-v1",
        claimed_content_hash="",
        origin_artifact_hash=_sha("b"),
    )


def _attempt(attempt_id: str = "worker-001",
             binding_id: str = "binding-001",
             session_id: str = "session-001",
             context_char: str = "c",
             input_hash: str = _INPUT_HASH,
             model_id: str = "model-alpha",
             ensemble_id: str = _ENSEMBLE_ID,
             output_ref: str = "artifact-out-001",
             output_hash: Optional[str] = None,
             claimed_date_window: str = "window-2026-01",
             claimed_unit_contract: str = "unit-mg",
             claimed_source_revision: str = "sr-001",
             claimed_rule_id: str = "rule-001",
             claimed_rule_version: str = "rule-v1",
             model_version: str = "v1.0") -> AnalysisAttempt:
    if output_hash is None:
        # Declared digest of the ACTUAL default output for this attempt.
        output_hash = worker_output_content_hash(_output(attempt_id))
    return AnalysisAttempt(
        attempt_id=attempt_id,
        ensemble_id=ensemble_id,
        binding_id=binding_id,
        session_id=session_id,
        model_id=model_id,
        model_version=model_version,
        role="worker",
        independent_context_hash=_sha(context_char),
        input_content_hash=input_hash,
        output_artifact_ref=output_ref,
        output_hash=output_hash,
        claimed_date_window=claimed_date_window,
        claimed_unit_contract=claimed_unit_contract,
        claimed_source_revision=claimed_source_revision,
        claimed_rule_id=claimed_rule_id,
        claimed_rule_version=claimed_rule_version,
    )


def _assessment(item_id: str = "baseline-001",
                state: str = "confirmed",
                attempt_id: str = "worker-001",
                recheck: Sequence[str] = ("loc-orig-001",),
                evidence_char: str = "f") -> BaselineAssessment:
    return BaselineAssessment(
        item_id=item_id,
        state=state,
        source_recheck_locator_ids=tuple(recheck),
        evidence_hashes=(_sha(evidence_char),),
        attempt_id=attempt_id,
        reason_codes=("source_rechecked", "content_match"),
    )


def _finding(finding_id: str = "finding-001",
             identity: str = "ident-current-001",
             priority: str = "low",
             supported: bool = True,
             locator: str = "loc-current-001") -> Finding:
    return Finding(
        finding_id=finding_id,
        proposed_identity=identity,
        monitoring_priority=priority,
        supported=supported,
        source_locator_ids=(locator,),
    )


def _gap(gap_id: str = "gap-001",
         kind: str = "baseline_missed_current",
         identity: str = "ident-gap-001",
         locator: str = "loc-orig-001",
         attempt_id: str = "worker-001") -> GapCandidate:
    return GapCandidate(
        gap_id=gap_id,
        gap_kind=kind,
        proposed_identity=identity,
        source_locator_ids=(locator,),
        originating_attempt_id=attempt_id,
    )


def _output(attempt_id: str = "worker-001",
            assessments: Sequence[BaselineAssessment] = (),
            findings: Sequence[Finding] = (),
            gap_candidates: Sequence = ()) -> WorkerAnalysisOutput:
    return WorkerAnalysisOutput(
        attempt_id=attempt_id,
        assessments=tuple(assessments),
        findings=tuple(findings),
        gap_candidates=tuple(gap_candidates),
    )


def _digest_for(artifact_ref: str, output: WorkerAnalysisOutput) -> Dict[str, str]:
    """Authority output digest that matches the ACTUAL output."""
    return {artifact_ref: worker_output_content_hash(output)}


def _artifact_defaults() -> Dict[str, str]:
    return {
        "artifact-out-001": worker_output_content_hash(_output("worker-001")),
        "artifact-out-002": worker_output_content_hash(_output("worker-002")),
        "artifact-out-003": worker_output_content_hash(_output("worker-003")),
    }


def _digest_context(input_hash: str = _INPUT_HASH,
                    output_digests: Optional[Dict[str, str]] = None,
                    evidence_digests: Optional[Sequence[str]] = None,
                    evidence_chars: Sequence[str] = ("f",),
                    date_windows: Optional[Dict[str, str]] = None,
                    unit_contracts: Optional[Dict[str, str]] = None,
                    source_versions: Optional[Dict[str, str]] = None,
                    model_versions: Optional[Dict[str, str]] = None,
                    rule_ids: Optional[Dict[str, str]] = None,
                    rule_versions: Optional[Dict[str, str]] = None,
                    finding_identities: Optional[
                        Dict[str, frozenset]] = None,
                    authorized_locators: Optional[
                        Dict[str, frozenset]] = None,
                    expected_ensemble_identity: str = _ENSEMBLE_ID) \
        -> EvidenceDigestContext:
    return EvidenceDigestContext(
        input_content_hash=input_hash,
        output_digests=(
            output_digests if output_digests is not None
            else _artifact_defaults()),
        evidence_digests=frozenset(
            evidence_digests if evidence_digests is not None
            else [_sha(char) for char in evidence_chars]),
        expected_ensemble_identity=expected_ensemble_identity,
        artifact_date_windows=(
            date_windows if date_windows is not None
            else {
                "artifact-out-001": "window-2026-01",
                "artifact-out-002": "window-2026-01",
                "artifact-out-003": "window-2026-01",
            }),
        artifact_unit_contracts=(
            unit_contracts if unit_contracts is not None
            else {
                "artifact-out-001": "unit-mg",
                "artifact-out-002": "unit-mg",
                "artifact-out-003": "unit-mg",
            }),
        artifact_source_versions=(
            source_versions if source_versions is not None
            else {
                "artifact-out-001": "sr-001",
                "artifact-out-002": "sr-001",
                "artifact-out-003": "sr-001",
            }),
        artifact_model_versions=(
            model_versions if model_versions is not None
            else {
                "artifact-out-001": "v1.0",
                "artifact-out-002": "v1.0",
                "artifact-out-003": "v1.0",
            }),
        artifact_rule_ids=(
            rule_ids if rule_ids is not None
            else {
                "artifact-out-001": "rule-001",
                "artifact-out-002": "rule-001",
                "artifact-out-003": "rule-001",
            }),
        artifact_rule_versions=(
            rule_versions if rule_versions is not None
            else {
                "artifact-out-001": "rule-v1",
                "artifact-out-002": "rule-v1",
                "artifact-out-003": "rule-v1",
            }),
        artifact_finding_identities=(
            finding_identities if finding_identities is not None
            else {
                "artifact-out-001": frozenset({"ident-current-001"}),
                "artifact-out-002": frozenset({"ident-current-001"}),
                "artifact-out-003": frozenset({"ident-current-001"}),
            }),
        artifact_authorized_source_locators=(
            authorized_locators if authorized_locators is not None
            else {
                "artifact-out-001": frozenset(
                    {"loc-current-001", "loc-orig-001"}),
                "artifact-out-002": frozenset(
                    {"loc-current-001", "loc-orig-001"}),
                "artifact-out-003": frozenset(
                    {"loc-current-001", "loc-orig-001"}),
            }),
    )


def _run(attempts: Sequence[AnalysisAttempt],
         outputs: Optional[Dict[str, WorkerAnalysisOutput]] = None,
         baseline_items: Sequence[ReferenceBaselineItem] = (),
         adjudicator: Optional[Adjudicator] = None,
         digest_context: Optional[EvidenceDigestContext] = None,
         current_source_locator_ids: Sequence[str] = ("loc-current-001",),
         verifier=None) -> EnsembleResult:
    output_map: Dict[str, WorkerAnalysisOutput] = (
        outputs if outputs is not None
        else {attempt.attempt_id: _output(attempt.attempt_id)
              for attempt in attempts})
    return run_ensemble(
        ensemble_id=_ENSEMBLE_ID,
        input_content_hash=_INPUT_HASH,
        attempts=attempts,
        worker_outputs=output_map,
        baseline_items=baseline_items,
        digest_context=(
            digest_context if digest_context is not None
            else _digest_context()),
        adjudicator=adjudicator,
        verifier=verifier,
        current_source_locator_ids=current_source_locator_ids,
    )


class TestEnsembleSizeGate(unittest.TestCase):
    def test_zero_fails_closed_before_side_effects(self) -> None:
        calls: List[str] = []

        def _verifier(*args):  # pragma: no cover - must never run
            calls.append("verifier")
            raise AssertionError("verifier must not run for size 0")

        def _adjudicate(*args):  # pragma: no cover - must never run
            calls.append("adjudicator")
            raise AssertionError("adjudicator must not run for size 0")

        with self.assertRaises(EnsembleError):
            run_ensemble(
                ensemble_id=_ENSEMBLE_ID,
                input_content_hash=_INPUT_HASH,
                attempts=[],
                worker_outputs={},
                baseline_items=(),
                digest_context=_digest_context(),
                verifier=_verifier,
                adjudicator=Adjudicator(
                    binding_id="adj-001", session_id="adj-session-001",
                    model_id="model-alpha", model_version="v1.0"),
            )
        self.assertEqual(calls, [])

    def test_negative_size_fails_closed(self) -> None:
        with self.assertRaises(EnsembleError):
            require_positive_ensemble_size(-1)
        with self.assertRaises(EnsembleError):
            require_positive_ensemble_size(0)
        with self.assertRaises(EnsembleError):
            require_positive_ensemble_size(True)  # bool is not a size

    def test_positive_size_passes(self) -> None:
        self.assertEqual(require_positive_ensemble_size(1), 1)
        self.assertEqual(require_positive_ensemble_size(3), 3)


class TestSingleModelEnsemble(unittest.TestCase):
    def test_no_consensus_or_agreement_leaf(self) -> None:
        attempt = _attempt()
        result = _run([attempt])
        self.assertEqual(result.ensemble_size, 1)
        self.assertIsNone(result.consensus_leaf)

    def test_residual_conflict_needs_user_attention(self) -> None:
        """A single model cannot adjudicate its own residual conflict: the
        main analysis completes but the outcome stays needs_user_attention
        and the conflict remains visible."""
        output = _output("worker-001",
                         assessments=(_assessment(),),
                         findings=(_finding(priority="high"),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        result = _run([attempt], baseline_items=(_baseline(),),
                      outputs={attempt.attempt_id: output},
                      digest_context=context)
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)
        self.assertEqual(len(result.conflicts), 1)
        conflict = result.conflicts[0]
        self.assertEqual(conflict.relation, "single_model_new")
        self.assertFalse(conflict.hidden)
        self.assertEqual(conflict.monitoring_priority, "high")
        # the analysis itself still completed
        self.assertEqual(len(result.verifications), 1)
        self.assertEqual(result.verifications[0].result, "passed")
        self.assertFalse(result.verification_blocked)

    def test_no_conflict_with_independent_adjudicator_supported(self) -> None:
        output = _output("worker-001", assessments=(_assessment(),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        result = _run([attempt], baseline_items=(_baseline(),),
                      outputs={attempt.attempt_id: output},
                      digest_context=context,
                      adjudicator=adjudicator)
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.DISTINCT_SUPPORTED)
        self.assertEqual(result.adjudication.reviewed_artifact_refs,
                         ("artifact-out-001",))

    def test_no_adjudicator_keeps_needs_user_attention(self) -> None:
        attempt = _attempt()
        result = _run([attempt])
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)


class TestNModelIsolation(unittest.TestCase):
    def _two_attempts(self):
        first = _attempt(attempt_id="worker-001", binding_id="binding-001",
                         session_id="session-001", context_char="c")
        second = _attempt(attempt_id="worker-002", binding_id="binding-002",
                          session_id="session-002", context_char="e",
                          output_ref="artifact-out-002")
        return first, second

    def test_same_model_different_binding_session_valid(self) -> None:
        first, second = self._two_attempts()
        self.assertEqual(first.model_id, second.model_id)
        result = _run([first, second])
        self.assertEqual(result.ensemble_size, 2)
        self.assertEqual(len(result.verifications), 2)

    def test_duplicate_worker_binding_rejected_before_verifier(self) -> None:
        """Reviewer probe: two workers with the SAME binding but different
        session/context must be rejected before the verifier, gap search,
        conflict merge or adjudication ever run."""
        first = _attempt(attempt_id="worker-001", binding_id="binding-001",
                         session_id="session-001", context_char="c")
        second = _attempt(attempt_id="worker-002", binding_id="binding-001",
                          session_id="session-002", context_char="e",
                          output_ref="artifact-out-002")
        calls: List[str] = []

        def _verifier(*args):  # pragma: no cover - must never run
            calls.append("verifier")
            raise AssertionError("verifier must not run for duplicate binding")

        with self.assertRaises(EnsembleError):
            _run([first, second], verifier=_verifier)
        self.assertEqual(calls, [])

    def test_requires_same_input_content_hash(self) -> None:
        first, _second = self._two_attempts()
        second = _attempt(attempt_id="worker-002", binding_id="binding-002",
                          session_id="session-002", context_char="e",
                          output_ref="artifact-out-002",
                          input_hash="9" * 64)
        with self.assertRaises(EnsembleError):
            _run([first, second])

    def test_requires_distinct_session_ids(self) -> None:
        first, _second = self._two_attempts()
        second = _attempt(attempt_id="worker-002", binding_id="binding-002",
                          session_id="session-001",  # collides
                          context_char="e", output_ref="artifact-out-002")
        with self.assertRaises(EnsembleError):
            _run([first, second])

    def test_requires_distinct_context_hashes(self) -> None:
        first, _second = self._two_attempts()
        second = _attempt(attempt_id="worker-002", binding_id="binding-002",
                          session_id="session-002",
                          context_char="c",  # collides with worker-001
                          output_ref="artifact-out-002")
        with self.assertRaises(EnsembleError):
            _run([first, second])

    def test_worker_output_must_match_attempt_ids(self) -> None:
        first, second = self._two_attempts()
        with self.assertRaises(EnsembleError):
            _run([first, second], outputs={
                "worker-001": _output("worker-001"),
                # missing worker-002, extra worker-999
                "worker-999": _output("worker-999"),
            })

    def test_worker_output_cannot_carry_another_attempts_assessment(self) -> None:
        first, second = self._two_attempts()
        foreign = _assessment(attempt_id="worker-002")
        with self.assertRaises(EnsembleError):
            _run([first, second], outputs={
                "worker-001": _output("worker-001", assessments=(foreign,)),
                "worker-002": _output("worker-002"),
            })

    def test_assessment_of_unknown_baseline_item_fails_closed(self) -> None:
        attempt = _attempt()
        with self.assertRaises(EnsembleError):
            _run([attempt], baseline_items=(),
                 outputs={
                     attempt.attempt_id: _output(
                         attempt.attempt_id,
                         assessments=(_assessment(item_id="baseline-999"),)),
                 })


class TestWorkerAdjudicatorSeparation(unittest.TestCase):
    def test_worker_cannot_adjudicate_itself_by_binding(self) -> None:
        attempt = _attempt(binding_id="binding-001")
        adjudicator = Adjudicator(
            binding_id="binding-001",  # collides with the worker
            session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        with self.assertRaises(EnsembleError):
            _run([attempt], adjudicator=adjudicator)

    def test_worker_cannot_adjudicate_itself_by_session(self) -> None:
        attempt = _attempt(session_id="session-001")
        adjudicator = Adjudicator(
            binding_id="adj-001",
            session_id="session-001",  # collides with the worker
            model_id="model-alpha", model_version="v1.0")
        with self.assertRaises(EnsembleError):
            _run([attempt], adjudicator=adjudicator)

    def test_independent_adjudicator_with_same_model_is_valid(self) -> None:
        attempt = _attempt(model_id="model-alpha")
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        result = _run([attempt], adjudicator=adjudicator)
        self.assertEqual(result.adjudication.binding_id, "adj-001")


class TestIntakeAttribution(unittest.TestCase):
    """Intake attribution is sealed BEFORE verifier, gap search, conflict
    merge and adjudication: every worker_outputs key must equal the output's
    own attempt_id and resolve to the declared AnalysisAttempt."""

    def _recording_verifier(self, calls: List[str]):
        def _verifier(*args):  # pragma: no cover - must never run
            calls.append("verifier")
            raise AssertionError("verifier must not run for bad intake")
        return _verifier

    def test_output_attempt_id_mismatch_rejected_before_verifier(self) -> None:
        """Reviewer probe: mapping key worker-001 carrying an output whose
        attempt_id is worker-999 must be rejected before the verifier, gap
        search, conflict merge or adjudication -- the forgery can never reach
        conflict attribution."""
        attempt = _attempt()  # declared attempt_id worker-001
        forged = _output(attempt_id="worker-999")  # mismatched attribution
        # give the forgery a matching digest + authority so only the
        # attribution check can catch it
        attempt = _attempt(output_hash=worker_output_content_hash(forged))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", forged))
        calls: List[str] = []
        with self.assertRaises(EnsembleError):
            _run([attempt], outputs={"worker-001": forged},
                 digest_context=context,
                 verifier=self._recording_verifier(calls))
        self.assertEqual(calls, [])
        self.assertEqual(len(calls), 0)

    def test_output_attempt_id_mismatch_rejected_directly(self) -> None:
        attempt = _attempt(output_ref="artifact-out-001")
        forged = _output(attempt_id="worker-999")
        with self.assertRaises(EnsembleError):
            _run([attempt], outputs={"worker-001": forged},
                 digest_context=_digest_context(
                     output_digests=_digest_for(
                         "artifact-out-001", forged)))

    def test_key_without_declared_attempt_rejected(self) -> None:
        """A mapping key that does not resolve to any declared
        AnalysisAttempt fails closed even though the key set matches the
        attempt ids (the check is per-key resolution, not set equality)."""
        attempt = _attempt(attempt_id="worker-001")
        with self.assertRaises(EnsembleError):
            _run([attempt], outputs={
                "worker-001": _output("worker-001"),
                # key matches no declared attempt; missing worker-001's
                # partner keeps the set comparison from firing first
                "worker-002": _output("worker-002"),
            })

    def test_valid_attribution_still_passes(self) -> None:
        attempt = _attempt()
        output = _output("worker-001")
        result = _run([attempt], outputs={"worker-001": output},
                      digest_context=_digest_context(
                          output_digests=_digest_for(
                              "artifact-out-001", output)))
        self.assertEqual(len(result.verifications), 1)
        self.assertEqual(result.verifications[0].result, "passed")


class TestIntakeUniqueness(unittest.TestCase):
    """Per-worker intake uniqueness fails closed at WorkerAnalysisOutput
    construction: at most one assessment per baseline item, unique finding
    ids, unique gap proposal ids.  Cross-worker duplication of item ids /
    finding identities / gap proposals stays legal."""

    def test_duplicate_assessment_item_rejected(self) -> None:
        """Reviewer probe: two BaselineAssessment objects for the same
        item_id with contradictory states must fail closed at intake (never
        reach verifier/gap/merge/adjudication)."""
        with self.assertRaises(EnsembleError):
            _output(
                "worker-001",
                assessments=(
                    _assessment("baseline-001", "confirmed"),
                    _assessment("baseline-001", "unsupported"),
                ))

    def test_duplicate_same_state_assessment_rejected(self) -> None:
        """Even same-state duplicates fail closed."""
        with self.assertRaises(EnsembleError):
            _output(
                "worker-001",
                assessments=(
                    _assessment("baseline-001", "confirmed"),
                    _assessment("baseline-001", "confirmed"),
                ))

    def test_duplicate_finding_id_rejected(self) -> None:
        with self.assertRaises(EnsembleError):
            _output(
                "worker-001",
                findings=(
                    _finding(finding_id="finding-001"),
                    _finding(finding_id="finding-001",
                             identity="ident-other"),
                ))

    def test_duplicate_gap_id_rejected(self) -> None:
        with self.assertRaises(EnsembleError):
            _output(
                "worker-001",
                gap_candidates=(
                    _gap(gap_id="gap-001"),
                    _gap(gap_id="gap-001", identity="ident-other"),
                ))

    def test_distinct_assessments_and_ids_remain_legal(self) -> None:
        output = _output(
            "worker-001",
            assessments=(
                _assessment("baseline-001", "confirmed"),
                _assessment("baseline-002", "outdated",
                            evidence_char="1"),
            ),
            findings=(_finding(finding_id="finding-001"),
                      _finding(finding_id="finding-002",
                               identity="ident-other")),
            gap_candidates=(_gap(gap_id="gap-001"),
                            _gap(gap_id="gap-002", identity="ident-other")),
        )
        self.assertEqual(len(output.assessments), 2)
        self.assertEqual(len(output.findings), 2)
        self.assertEqual(len(output.gap_candidates), 2)

    def test_cross_worker_duplicate_items_remain_legal(self) -> None:
        """Independent workers may legitimately address the same baseline
        item / finding identity: only per-output duplication is an intake
        defect."""
        outputs = {
            "worker-001": _output(
                "worker-001",
                assessments=(_assessment("baseline-001", "confirmed"),)),
            "worker-002": _output(
                "worker-002",
                assessments=(_assessment("baseline-001", "unsupported",
                                         attempt_id="worker-002",
                                         evidence_char="1"),)),
        }
        first = _attempt(attempt_id="worker-001", binding_id="binding-001",
                         session_id="session-001", context_char="c",
                         output_hash=worker_output_content_hash(
                             outputs["worker-001"]))
        second = _attempt(attempt_id="worker-002", binding_id="binding-002",
                          session_id="session-002", context_char="e",
                          output_ref="artifact-out-002",
                          output_hash=worker_output_content_hash(
                              outputs["worker-002"]))
        context = _digest_context(
            output_digests={
                "artifact-out-001": worker_output_content_hash(
                    outputs["worker-001"]),
                "artifact-out-002": worker_output_content_hash(
                    outputs["worker-002"]),
            },
            evidence_chars=("f", "1"),
        )
        result = _run([first, second], outputs=outputs,
                      baseline_items=(_baseline(),),
                      digest_context=context)
        self.assertTrue(all(v.result == "passed"
                            for v in result.verifications))
        # both workers assessed the same item: no baseline_miss conflict
        self.assertFalse([c for c in result.conflicts
                          if c.relation == "baseline_miss"])


class TestVerificationPrecedesAdjudication(unittest.TestCase):
    def test_failed_verification_blocks_supporting_outcome(self) -> None:
        attempt = _attempt(output_ref="artifact-out-001")
        # The authority digest for the artifact differs from the RECOMPUTED
        # canonical digest of the actual output -> artifact integrity fails.
        context = _digest_context(
            output_digests={"artifact-out-001": _sha("9")})
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        result = _run([attempt], adjudicator=adjudicator,
                      digest_context=context)
        self.assertTrue(result.verification_blocked)
        self.assertEqual(result.verifications[0].result, "failed")
        self.assertIn("artifact_hash_mismatch",
                      result.verifications[0].failure_reason_codes)
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)

    def test_input_version_mismatch_fails_verification(self) -> None:
        """The deterministic verifier itself rejects an attempt whose input
        hash diverges from the authority input hash (defense in depth; the
        ensemble gate already enforces the same-input rule)."""
        attempt = _attempt(input_hash="9" * 64)
        context = _digest_context(input_hash=_INPUT_HASH)
        record = verify_attempt(attempt, _output("worker-001"), context)
        self.assertEqual(record.result, "failed")
        self.assertIn("version_mismatch",
                      record.failure_reason_codes)

    def test_verifier_runs_for_every_attempt_before_result(self) -> None:
        seen: List[str] = []

        def _recording(attempt, output, context):
            seen.append(attempt.attempt_id)
            return verify_attempt(attempt, output, context)

        first, second = _attempt(attempt_id="worker-001",
                                 binding_id="binding-001",
                                 session_id="session-001",
                                 context_char="c"), \
            _attempt(attempt_id="worker-002", binding_id="binding-002",
                     session_id="session-002", context_char="e",
                     output_ref="artifact-out-002")
        result = _run([first, second], verifier=_recording)
        self.assertEqual(seen, ["worker-001", "worker-002"])
        self.assertEqual(len(result.verifications), 2)


class TestVerificationDimensionsAndAudit(unittest.TestCase):
    """The deterministic verifier compares every dimension against the typed
    authority context (identity, version, date, unit, source, rule, artifact
    integrity), emits the corresponding failure code per mutated dimension,
    and keeps ``checked_dimensions`` auditable even when every dimension
    fails."""

    def test_all_seven_dimensions_checked_on_pass(self) -> None:
        output = _output("worker-001", assessments=(_assessment(),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "passed")
        self.assertEqual(record.failure_reason_codes, ())
        self.assertEqual(set(record.checked_dimensions),
                         set(VERIFICATION_DIMENSIONS))
        self.assertEqual(len(record.checked_dimensions), 7)

    # -- identity dimension ------------------------------------------------

    def test_unregistered_ensemble_identity_fails(self) -> None:
        attempt = _attempt(ensemble_id="ens-forged")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("identity_mismatch", record.failure_reason_codes)
        self.assertIn("identity", record.checked_dimensions)

    def test_unregistered_finding_identity_fails(self) -> None:
        """Reviewer probe: an arbitrary unregistered finding identity must be
        rejected (identity_mismatch), not merely labeled as checked."""
        output = _output("worker-001",
                         findings=(_finding(identity="made-up-identity"),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("identity_mismatch", record.failure_reason_codes)

    # -- version dimension --------------------------------------------------

    def test_input_version_mismatch_fails(self) -> None:
        attempt = _attempt(input_hash="9" * 64)
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context(input_hash=_INPUT_HASH))
        self.assertEqual(record.result, "failed")
        self.assertIn("version_mismatch", record.failure_reason_codes)
        self.assertIn("version", record.checked_dimensions)

    def test_unregistered_model_version_fails(self) -> None:
        """Reviewer probe: an arbitrary unregistered model_version must be
        rejected (version_mismatch)."""
        attempt = _attempt(model_version="v9.9")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("version_mismatch", record.failure_reason_codes)

    def test_unregistered_source_revision_fails(self) -> None:
        attempt = _attempt(claimed_source_revision="sr-forged")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("version_mismatch", record.failure_reason_codes)

    # -- date / unit dimensions ---------------------------------------------

    def test_date_out_of_window_fails(self) -> None:
        attempt = _attempt(claimed_date_window="window-other")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("date_out_of_window",
                      record.failure_reason_codes)
        self.assertIn("date", record.checked_dimensions)

    def test_unit_mismatch_fails(self) -> None:
        attempt = _attempt(claimed_unit_contract="unit-ml")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("unit_mismatch", record.failure_reason_codes)
        self.assertIn("unit", record.checked_dimensions)

    def test_unresolved_date_window_fails_closed(self) -> None:
        """No authoritative date entry for the artifact -> unresolved ->
        date_out_of_window (fail closed)."""
        attempt = _attempt()
        context = _digest_context(date_windows={})
        record = verify_attempt(attempt, _output("worker-001"), context)
        self.assertEqual(record.result, "failed")
        self.assertIn("date_out_of_window",
                      record.failure_reason_codes)

    def test_unresolved_unit_contract_fails_closed(self) -> None:
        attempt = _attempt()
        context = _digest_context(unit_contracts={})
        record = verify_attempt(attempt, _output("worker-001"), context)
        self.assertEqual(record.result, "failed")
        self.assertIn("unit_mismatch", record.failure_reason_codes)

    # -- source dimension ---------------------------------------------------

    def test_unauthorized_recheck_locator_fails(self) -> None:
        output = _output(
            "worker-001",
            assessments=(_assessment(recheck=("loc-rogue-999",)),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("source_unresolvable", record.failure_reason_codes)
        self.assertIn("source", record.checked_dimensions)

    def test_unauthorized_finding_locator_fails(self) -> None:
        output = _output(
            "worker-001",
            findings=(_finding(locator="loc-rogue-999"),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("source_unresolvable", record.failure_reason_codes)

    def test_unregistered_evidence_hash_fails(self) -> None:
        output = _output("worker-001",
                         assessments=(_assessment(evidence_char="0"),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("source_unresolvable", record.failure_reason_codes)

    # -- rule dimension -----------------------------------------------------

    def test_unregistered_rule_id_fails(self) -> None:
        attempt = _attempt(claimed_rule_id="rule-forged")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("rule_version_mismatch", record.failure_reason_codes)
        self.assertIn("rule", record.checked_dimensions)

    def test_unregistered_rule_version_fails(self) -> None:
        attempt = _attempt(claimed_rule_version="rule-v9")
        record = verify_attempt(attempt, _output("worker-001"),
                                _digest_context())
        self.assertEqual(record.result, "failed")
        self.assertIn("rule_version_mismatch", record.failure_reason_codes)

    # -- artifact integrity dimension ---------------------------------------

    def test_mutated_output_with_unchanged_digests_fails(self) -> None:
        """Reviewer probe: changing the ACTUAL WorkerAnalysisOutput while
        leaving the attempt/output digest declarations unchanged must fail
        with artifact_hash_mismatch (the verifier recomputes the actual
        digest)."""
        output = _output("worker-001", assessments=(_assessment(),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests=_digest_for("artifact-out-001", output))
        # verifier passes against the true output
        self.assertEqual(verify_attempt(attempt, output, context).result,
                         "passed")
        # now mutate the ACTUAL output, keeping all declarations unchanged
        mutated = _output("worker-001",
                          assessments=(_assessment(evidence_char="0"),))
        record = verify_attempt(attempt, mutated, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("artifact_hash_mismatch",
                      record.failure_reason_codes)
        self.assertIn("artifact_integrity", record.checked_dimensions)

    def test_authority_digest_mismatch_fails(self) -> None:
        output = _output("worker-001")
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        context = _digest_context(
            output_digests={"artifact-out-001": _sha("9")})
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertIn("artifact_hash_mismatch",
                      record.failure_reason_codes)

    # -- full audit trail ---------------------------------------------------

    def test_all_dimensions_fail_keeps_full_audit_trail(self) -> None:
        """Every dimension fails at once: the record must still list all
        seven attempted dimensions, emit every corresponding failure code,
        and return one deterministic failed verification (no empty-dimension
        contract error)."""
        output = _output(
            "worker-001",
            assessments=(_assessment(
                recheck=("loc-rogue-999",), evidence_char="0"),),
            findings=(_finding(identity="ident-rogue-999",
                               locator="loc-rogue-999"),))
        attempt = _attempt(
            ensemble_id="ens-forged",
            input_hash="9" * 64,
            model_version="v9.9",
            claimed_source_revision="sr-forged",
            claimed_rule_id="rule-forged",
            claimed_rule_version="rule-v9",
            claimed_date_window="window-other",
            claimed_unit_contract="unit-ml",
            output_hash="1" * 64,
        )
        context = _digest_context(
            input_hash=_INPUT_HASH,
            output_digests={"artifact-out-001": _sha("9")},
            evidence_chars=("f",),
            date_windows={},
            unit_contracts={},
        )
        record = verify_attempt(attempt, output, context)
        self.assertEqual(record.result, "failed")
        self.assertEqual(set(record.checked_dimensions),
                         set(VERIFICATION_DIMENSIONS))
        self.assertEqual(len(record.checked_dimensions), 7)
        self.assertEqual(set(record.failure_reason_codes), {
            "identity_mismatch",
            "version_mismatch",
            "date_out_of_window",
            "unit_mismatch",
            "source_unresolvable",
            "rule_version_mismatch",
            "artifact_hash_mismatch",
        })

    def test_all_dimensions_fail_blocks_adjudication(self) -> None:
        """Verification-before-adjudication holds when every dimension
        fails: the run reports the block and keeps needs_user_attention."""
        output = _output(
            "worker-001",
            assessments=(_assessment(evidence_char="0"),))
        attempt = _attempt(output_hash=worker_output_content_hash(output))
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        context = _digest_context(
            input_hash="9" * 64,
            output_digests={"artifact-out-001": _sha("9")},
            evidence_chars=("f",),
            date_windows={},
            unit_contracts={},
        )
        result = _run([attempt], baseline_items=(_baseline(),),
                      outputs={attempt.attempt_id: output},
                      adjudicator=adjudicator,
                      digest_context=context)
        self.assertTrue(result.verification_blocked)
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)
        self.assertEqual(result.verifications[0].result, "failed")
        self.assertIn("date_out_of_window",
                      result.verifications[0].failure_reason_codes)
        self.assertIn("unit_mismatch",
                      result.verifications[0].failure_reason_codes)


class TestConflictVisibilityAndMajority(unittest.TestCase):
    def test_high_risk_disagreement_survives_majority(self) -> None:
        """Two workers support identity X while one negates it at high
        priority: the majority cannot hide or close the disagreement."""
        supporting = _finding(finding_id="f-1",
                              identity="ident-conflict-001",
                              priority="low", supported=True)
        negating = _finding(finding_id="f-2",
                            identity="ident-conflict-001",
                            priority="high", supported=False)
        outputs = {
            "worker-001": _output(
                "worker-001",
                assessments=(_assessment(attempt_id="worker-001"),),
                findings=(supporting,)),
            "worker-002": _output(
                "worker-002",
                assessments=(_assessment(attempt_id="worker-002"),),
                findings=(supporting,)),
            "worker-003": _output(
                "worker-003",
                assessments=(_assessment(attempt_id="worker-003"),),
                findings=(negating,)),
        }
        first = _attempt(
            attempt_id="worker-001", binding_id="binding-001",
            session_id="session-001", context_char="c",
            output_ref="artifact-out-001",
            output_hash=worker_output_content_hash(outputs["worker-001"]))
        second = _attempt(
            attempt_id="worker-002", binding_id="binding-002",
            session_id="session-002", context_char="e",
            output_ref="artifact-out-002",
            output_hash=worker_output_content_hash(outputs["worker-002"]))
        third = _attempt(
            attempt_id="worker-003", binding_id="binding-003",
            session_id="session-003", context_char="f",
            output_ref="artifact-out-003",
            output_hash=worker_output_content_hash(outputs["worker-003"]))
        context = _digest_context(
            output_digests={
                "artifact-out-001": worker_output_content_hash(
                    outputs["worker-001"]),
                "artifact-out-002": worker_output_content_hash(
                    outputs["worker-002"]),
                "artifact-out-003": worker_output_content_hash(
                    outputs["worker-003"]),
            },
            finding_identities={
                "artifact-out-001": frozenset({"ident-conflict-001"}),
                "artifact-out-002": frozenset({"ident-conflict-001"}),
                "artifact-out-003": frozenset({"ident-conflict-001"}),
            })
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        result = _run([first, second, third], outputs=outputs,
                      baseline_items=(_baseline(),),
                      digest_context=context,
                      adjudicator=adjudicator)
        conflict = next(c for c in result.conflicts
                        if c.relation == "mutual_negation")
        self.assertFalse(conflict.hidden)
        self.assertEqual(conflict.monitoring_priority, "high")
        self.assertEqual(conflict.display_state, "visible_conflict")
        self.assertEqual(set(conflict.member_attempt_ids),
                         {"worker-001", "worker-002", "worker-003"})
        # verification passed: the block comes from the conflict, not the
        # verifier
        self.assertTrue(all(v.result == "passed"
                            for v in result.verifications))
        # majority (2-1) cannot close it
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)
        self.assertIsNone(result.consensus_leaf)

    def test_shared_finding_conflict_visible_and_consensus_signal(self) -> None:
        finding = _finding(identity="ident-shared-001", priority="low")
        outputs = {
            "worker-001": _output(
                "worker-001",
                assessments=(_assessment(attempt_id="worker-001"),),
                findings=(finding,)),
            "worker-002": _output(
                "worker-002",
                assessments=(_assessment(attempt_id="worker-002"),),
                findings=(finding,)),
        }
        first = _attempt(
            attempt_id="worker-001", binding_id="binding-001",
            session_id="session-001", context_char="c",
            output_ref="artifact-out-001",
            output_hash=worker_output_content_hash(outputs["worker-001"]))
        second = _attempt(
            attempt_id="worker-002", binding_id="binding-002",
            session_id="session-002", context_char="e",
            output_ref="artifact-out-002",
            output_hash=worker_output_content_hash(outputs["worker-002"]))
        context = _digest_context(
            output_digests={
                "artifact-out-001": worker_output_content_hash(
                    outputs["worker-001"]),
                "artifact-out-002": worker_output_content_hash(
                    outputs["worker-002"]),
            },
            finding_identities={
                "artifact-out-001": frozenset({"ident-shared-001"}),
                "artifact-out-002": frozenset({"ident-shared-001"}),
            })
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        result = _run([first, second], outputs=outputs,
                      baseline_items=(_baseline(),),
                      digest_context=context,
                      adjudicator=adjudicator)
        self.assertEqual(result.consensus_leaf, "ident-shared-001")
        shared = next(c for c in result.conflicts
                      if c.relation == "shared_finding")
        self.assertFalse(shared.hidden)
        self.assertTrue(all(v.result == "passed"
                            for v in result.verifications))
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.MERGED_SUPPORTED)


class TestBaselineAssessmentCoverage(unittest.TestCase):
    def test_every_baseline_item_locatable_with_recheck_locators(self) -> None:
        """Each baseline item maps to exactly one of the six states and
        confirmed/unsupported carry source recheck locators."""
        items = (
            _baseline("baseline-001", "ident-001", "loc-orig-001"),
            _baseline("baseline-002", "ident-002", "loc-orig-002"),
            _baseline("baseline-003", "ident-003", "loc-orig-003"),
        )
        outputs = {
            "worker-001": _output(
                "worker-001",
                assessments=(
                    _assessment("baseline-001", "confirmed",
                                recheck=("loc-orig-001",)),
                    _assessment("baseline-002", "unsupported",
                                recheck=("loc-orig-002",),
                                evidence_char="1"),
                    _assessment("baseline-003", "insufficient_evidence",
                                recheck=(), evidence_char="2"),
                )),
        }
        attempt = _attempt(
            output_hash=worker_output_content_hash(outputs["worker-001"]))
        context = _digest_context(
            output_digests=_digest_for(
                "artifact-out-001", outputs["worker-001"]),
            evidence_chars=("f", "1", "2"),
            authorized_locators={
                "artifact-out-001": frozenset(
                    {"loc-orig-001", "loc-orig-002", "loc-orig-003"}),
            })
        result = _run([attempt], outputs=outputs, baseline_items=items,
                      digest_context=context)
        self.assertEqual(len(result.verifications), 1)
        self.assertEqual(result.verifications[0].result, "passed")
        # no baseline-miss conflicts and no gap candidates for covered items
        self.assertFalse([c for c in result.conflicts
                          if c.relation == "baseline_miss"])
        self.assertFalse([g for g in result.gap_candidates
                          if g.gap_kind == "baseline_missed_current"])
        for assessment in outputs[attempt.attempt_id].assessments:
            self.assertIn(assessment.state,
                          ("confirmed", "partially_supported",
                           "unsupported", "outdated",
                           "insufficient_evidence", "not_applicable"))
            if assessment.state in ("confirmed", "unsupported"):
                self.assertTrue(assessment.source_recheck_locator_ids)


class TestGapSearch(unittest.TestCase):
    def test_three_gap_kinds_proposed(self) -> None:
        items = (
            _baseline("baseline-001", "ident-baseline-001", "loc-orig-001"),
            _baseline("baseline-002", "ident-baseline-002", "loc-orig-002"),
            _baseline("baseline-003", "ident-baseline-003", "loc-orig-003"),
        )
        attempt = _attempt()
        # baseline-002 assessed; baseline-001 and baseline-003 unassessed.
        # baseline-003's locators are absent from the current source set.
        outputs = {
            attempt.attempt_id: _output(
                attempt.attempt_id,
                assessments=(
                    _assessment("baseline-002", "outdated",
                                recheck=("loc-orig-002",),
                                evidence_char="1"),
                ),
                findings=(_finding(identity="ident-current-new-001",
                                   locator="loc-current-001"),)),
        }
        gaps = search_gaps(
            baseline_items=items,
            worker_outputs=outputs,
            current_source_locator_ids=("loc-current-001",),
            originating_attempt_id=attempt.attempt_id,
        )
        kinds = {gap.gap_kind for gap in gaps}
        self.assertIn("baseline_missed_current", kinds)   # baseline-001/003
        self.assertIn("current_missed_baseline", kinds)   # new finding
        self.assertIn("source_unrepresented", kinds)      # baseline-003
        for gap in gaps:
            self.assertTrue(gap.source_locator_ids)
            self.assertEqual(gap.originating_attempt_id,
                             attempt.attempt_id)

    def test_gap_candidates_never_create_lifecycle_risk(self) -> None:
        attempt = _attempt()
        outputs = {attempt.attempt_id: _output(attempt.attempt_id)}
        gaps = search_gaps(
            baseline_items=(_baseline(),),
            worker_outputs=outputs,
            current_source_locator_ids=(),
            originating_attempt_id=attempt.attempt_id,
        )
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].gap_kind, "baseline_missed_current")
        # proposals only: no risk/promotion surface exists on a candidate
        for name in gaps[0].FORBIDDEN_PROMOTION_FIELDS:
            self.assertFalse(hasattr(gaps[0], name))

    def test_unassessed_baseline_yields_visible_conflict(self) -> None:
        attempt = _attempt()
        result = _run([attempt], baseline_items=(_baseline(),),
                      outputs={attempt.attempt_id: _output(
                          attempt.attempt_id)})
        miss = next(c for c in result.conflicts
                    if c.relation == "baseline_miss")
        self.assertFalse(miss.hidden)
        self.assertEqual(miss.monitoring_priority, "high")
        self.assertEqual(miss.display_state, "visible_baseline_miss")
        self.assertEqual(
            result.adjudication.outcome,
            AdjudicationOutcome.NEEDS_USER_ATTENTION)


class TestDeterminismAndIsolation(unittest.TestCase):
    def test_replay_is_byte_identical(self) -> None:
        finding = _finding(identity="ident-shared-001", priority="low")
        outputs = {
            "worker-001": _output("worker-001", findings=(finding,)),
            "worker-002": _output("worker-002", findings=(finding,)),
        }
        first = _attempt(
            attempt_id="worker-001", binding_id="binding-001",
            session_id="session-001", context_char="c",
            output_ref="artifact-out-001",
            output_hash=worker_output_content_hash(outputs["worker-001"]))
        second = _attempt(
            attempt_id="worker-002", binding_id="binding-002",
            session_id="session-002", context_char="e",
            output_ref="artifact-out-002",
            output_hash=worker_output_content_hash(outputs["worker-002"]))
        context = _digest_context(
            output_digests={
                "artifact-out-001": worker_output_content_hash(
                    outputs["worker-001"]),
                "artifact-out-002": worker_output_content_hash(
                    outputs["worker-002"]),
            },
            finding_identities={
                "artifact-out-001": frozenset({"ident-shared-001"}),
                "artifact-out-002": frozenset({"ident-shared-001"}),
            })
        adjudicator = Adjudicator(
            binding_id="adj-001", session_id="adj-session-001",
            model_id="model-alpha", model_version="v1.0")
        # reverse the input order: results must be identical
        first_result = _run([first, second], outputs=outputs,
                            digest_context=context,
                            adjudicator=adjudicator)
        second_result = _run([second, first], outputs=outputs,
                             digest_context=context,
                             adjudicator=adjudicator)
        self.assertEqual(first_result, second_result)
        self.assertEqual(
            first_result.verifications[0].attempt_id, "worker-001")
        self.assertEqual(first_result.conflicts, second_result.conflicts)
        self.assertEqual(first_result.gap_candidates,
                         second_result.gap_candidates)


if __name__ == "__main__":
    unittest.main()
