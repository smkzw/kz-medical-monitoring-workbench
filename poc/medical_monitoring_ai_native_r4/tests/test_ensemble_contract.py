"""Typed-contract tests for the shared ensemble / reference-baseline closure.

Covers the closed vocabularies and value-object invariants of
:mod:`mm_r4.ensemble_contracts` (System Design v1.1 §9.2-9.4; R4 plan steps
9-10):

* exactly six baseline assessment states, never an L1 disposition set and
  never an L3 lifecycle state set;
* reference-baseline items are challengeable (no gold/authoritative/
  accepted-as-truth field) and carry deterministic content hashes plus
  origin source locators;
* ``confirmed`` / ``unsupported`` require source recheck locators; the other
  states stop at insufficient evidence / not applicable when the original
  source cannot be rechecked;
* gap candidates are proposals with closed kinds and no risk-promotion field;
* analysis attempts carry isolation identity (binding/session/context hash);
* deterministic evidence verification records have closed results and reason
  codes;
* adjudication outcomes reuse the R2 five-state vocabulary (never the D10 pin
  states accepted/divergent/pending);
* high-risk or important disagreement cannot be constructed hidden.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r2.risk import AdjudicationOutcome  # noqa: E402
from mm_r4 import contracts  # noqa: E402
from mm_r4.ensemble_contracts import (  # noqa: E402
    ASSESSMENT_REASON_CODES,
    ATTEMPT_ROLES,
    BASELINE_STATES,
    AdjudicationBinding,
    AnalysisAttempt,
    BaselineAssessment,
    CONFLICT_DISPLAY_STATES,
    CONFLICT_RELATIONS,
    ConflictVisibility,
    EnsembleContractError,
    EvidenceVerification,
    GAP_KINDS,
    GapCandidate,
    NON_HIDEABLE_RELATIONS,
    RECHECK_REQUIRED_STATES,
    ReferenceBaselineItem,
    SOURCE_KINDS,
    VERIFICATION_DIMENSIONS,
    VERIFICATION_FAILURE_CODES,
    VERIFICATION_RESULTS,
)

_SRC_FILES = (
    _R4_SRC / "mm_r4" / "ensemble_contracts.py",
    _R4_SRC / "mm_r4" / "ensemble.py",
)

_FORBIDDEN_DECISION_TOKENS = (
    "oracle", "SYN-", "case_id", "mutation", "fixture",
)


def _sha() -> str:
    """A structurally valid (but arbitrary) 64-hex sha256 value."""
    return "a" * 64


def _make_item(**overrides) -> ReferenceBaselineItem:
    fields = dict(
        item_id="baseline-001",
        source_kind="legacy_profile",
        source_locator_ids=("loc-orig-001",),
        source_revision_id="rev-001",
        snapshot_id="snap-001",
        claimed_identity="ident-r1-safety-001",
        temporal_window="study-period-v1",
        claimed_content_hash="",
        origin_artifact_hash=_sha(),
    )
    fields.update(overrides)
    return ReferenceBaselineItem(**fields)


def _make_assessment(**overrides) -> BaselineAssessment:
    fields = dict(
        item_id="baseline-001",
        state="confirmed",
        source_recheck_locator_ids=("loc-orig-001",),
        evidence_hashes=(_sha(),),
        attempt_id="worker-001",
        reason_codes=("source_rechecked", "content_match"),
    )
    fields.update(overrides)
    return BaselineAssessment(**fields)


def _make_gap(**overrides) -> GapCandidate:
    fields = dict(
        gap_id="gap-001",
        gap_kind="baseline_missed_current",
        proposed_identity="ident-r1-safety-001",
        source_locator_ids=("loc-orig-001",),
        originating_attempt_id="worker-001",
    )
    fields.update(overrides)
    return GapCandidate(**fields)


def _make_attempt(**overrides) -> AnalysisAttempt:
    fields = dict(
        attempt_id="worker-001",
        ensemble_id="ens-001",
        binding_id="binding-001",
        session_id="session-001",
        model_id="model-alpha",
        model_version="v1.0",
        role="worker",
        independent_context_hash="c" * 64,
        input_content_hash="d" * 64,
        output_artifact_ref="artifact-out-001",
        output_hash="e" * 64,
        claimed_date_window="window-2026-01",
        claimed_unit_contract="unit-mg",
        claimed_source_revision="sr-001",
        claimed_rule_id="rule-001",
        claimed_rule_version="rule-v1",
    )
    fields.update(overrides)
    return AnalysisAttempt(**fields)


def _make_verification(**overrides) -> EvidenceVerification:
    fields = dict(
        verification_id="verify-001",
        attempt_id="worker-001",
        checked_dimensions=("identity", "version", "artifact_integrity"),
        result="passed",
        failure_reason_codes=(),
    )
    fields.update(overrides)
    return EvidenceVerification(**fields)


def _make_conflict(**overrides) -> ConflictVisibility:
    fields = dict(
        conflict_id="conflict-001",
        member_attempt_ids=("worker-001",),
        monitoring_priority="medium",
        relation="single_model_new",
        display_state="needs_attention",
        hidden=False,
    )
    fields.update(overrides)
    return ConflictVisibility(**fields)


class TestBaselineStateVocabulary(unittest.TestCase):
    def test_exactly_six_assessment_states(self) -> None:
        self.assertEqual(BASELINE_STATES, (
            "confirmed",
            "partially_supported",
            "unsupported",
            "outdated",
            "insufficient_evidence",
            "not_applicable",
        ))
        self.assertEqual(len(BASELINE_STATES), 6)
        self.assertEqual(len(set(BASELINE_STATES)), 6)

    def test_states_are_not_l1_dispositions(self) -> None:
        """Six-state assessment is NOT the L1 disposition vocabulary: only
        the spelling ``not_applicable`` is shared; the five L1 dispositions
        (positive/negative/boundary/not_applicable/not_evaluable) never
        appear as assessment states, and confirmed/unsupported never map to
        negative/positive."""
        l1 = set(contracts.L1Disposition.ALL)
        self.assertEqual(set(BASELINE_STATES) & l1, {"not_applicable"})
        self.assertNotIn("confirmed", l1)
        self.assertNotIn("unsupported", l1)
        self.assertNotIn("positive", BASELINE_STATES)
        self.assertNotIn("negative", BASELINE_STATES)
        self.assertNotIn("boundary", BASELINE_STATES)
        self.assertNotIn("not_evaluable", BASELINE_STATES)

    def test_states_are_not_l3_lifecycle_states(self) -> None:
        l3 = set(contracts.L3RiskStateRef.all_states())
        self.assertTrue(l3.isdisjoint(set(BASELINE_STATES)))

    def test_recheck_required_states_subset(self) -> None:
        self.assertEqual(set(RECHECK_REQUIRED_STATES),
                         {"confirmed", "unsupported"})
        self.assertTrue(set(RECHECK_REQUIRED_STATES)
                        .issubset(set(BASELINE_STATES)))

    def test_closed_vocabularies_unique(self) -> None:
        for vocabulary in (SOURCE_KINDS, BASELINE_STATES, GAP_KINDS,
                           ATTEMPT_ROLES, VERIFICATION_RESULTS,
                           VERIFICATION_DIMENSIONS,
                           VERIFICATION_FAILURE_CODES,
                           ASSESSMENT_REASON_CODES, CONFLICT_RELATIONS,
                           CONFLICT_DISPLAY_STATES):
            self.assertEqual(len(set(vocabulary)), len(vocabulary),
                             vocabulary)


class TestReferenceBaselineItem(unittest.TestCase):
    def test_valid_item(self) -> None:
        item = _make_item()
        self.assertEqual(item.source_kind, "legacy_profile")
        self.assertTrue(item.claimed_content_hash)

    def test_rejects_unknown_source_kind(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_item(source_kind="current_export")

    def test_rejects_empty_source_locators(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_item(source_locator_ids=())

    def test_rejects_blank_identity(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_item(claimed_identity="  ")

    def test_rejects_bad_origin_artifact_hash(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_item(origin_artifact_hash="not-a-hash")

    def test_rejects_stale_claimed_content_hash(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_item(claimed_content_hash="f" * 64)

    def test_content_hash_is_deterministic(self) -> None:
        first = _make_item()
        second = _make_item()
        self.assertEqual(first.claimed_content_hash,
                         second.claimed_content_hash)
        changed = _make_item(temporal_window="other-window")
        self.assertNotEqual(first.claimed_content_hash,
                            changed.claimed_content_hash)

    def test_forbids_authority_fields(self) -> None:
        item = _make_item()
        for name in item.FORBIDDEN_AUTHORITY_FIELDS:
            self.assertFalse(hasattr(item, name),
                             f"{name} must not exist on the baseline item")
        for name in item.FORBIDDEN_AUTHORITY_FIELDS:
            with self.assertRaises(TypeError):
                ReferenceBaselineItem(
                    item_id="b", source_kind="legacy_profile",
                    source_locator_ids=("loc",), source_revision_id="r",
                    snapshot_id="s", claimed_identity="i",
                    temporal_window="w", claimed_content_hash="",
                    origin_artifact_hash=_sha(), **{name: True})

    def test_locators_are_sorted_deterministically(self) -> None:
        item = _make_item(source_locator_ids=("z-loc", "a-loc"))
        self.assertEqual(item.source_locator_ids, ("a-loc", "z-loc"))


class TestBaselineAssessment(unittest.TestCase):
    def test_valid_assessment(self) -> None:
        assessment = _make_assessment()
        self.assertEqual(assessment.state, "confirmed")

    def test_confirmed_requires_source_recheck(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(state="confirmed",
                             source_recheck_locator_ids=())

    def test_unsupported_requires_source_recheck(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(state="unsupported",
                             source_recheck_locator_ids=())

    def test_insufficient_evidence_allows_empty_recheck(self) -> None:
        assessment = _make_assessment(
            state="insufficient_evidence",
            source_recheck_locator_ids=(),
            reason_codes=("evidence_insufficient",))
        self.assertEqual(assessment.state, "insufficient_evidence")

    def test_not_applicable_allows_empty_recheck(self) -> None:
        assessment = _make_assessment(
            state="not_applicable",
            source_recheck_locator_ids=(),
            reason_codes=("outside_assessment_scope",))
        self.assertEqual(assessment.state, "not_applicable")

    def test_rejects_unknown_state(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(state="confirmed_extra")

    def test_rejects_prose_reason_codes(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(reason_codes=("free prose is not a state",))

    def test_rejects_empty_reason_codes(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(reason_codes=())

    def test_rejects_empty_evidence_hashes(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(evidence_hashes=())

    def test_rejects_non_sha_evidence_hash(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_assessment(evidence_hashes=("zzz",))


class TestGapCandidate(unittest.TestCase):
    def test_valid_gap(self) -> None:
        gap = _make_gap()
        self.assertEqual(gap.gap_kind, "baseline_missed_current")

    def test_rejects_unknown_kind(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_gap(gap_kind="auto_escalated")

    def test_rejects_empty_locators(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_gap(source_locator_ids=())

    def test_forbids_promotion_fields(self) -> None:
        gap = _make_gap()
        for name in gap.FORBIDDEN_PROMOTION_FIELDS:
            self.assertFalse(hasattr(gap, name),
                             f"{name} must not exist on a gap candidate")


class TestAnalysisAttempt(unittest.TestCase):
    def test_valid_attempt(self) -> None:
        attempt = _make_attempt()
        self.assertEqual(attempt.role, "worker")

    def test_rejects_unknown_role(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(role="supervisor")

    def test_rejects_blank_session(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(session_id="")

    def test_rejects_bad_context_hash(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(independent_context_hash="short")

    def test_rejects_empty_claimed_date_window(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(claimed_date_window="")

    def test_rejects_empty_claimed_unit_contract(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(claimed_unit_contract="")

    def test_rejects_empty_claimed_source_revision(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(claimed_source_revision="")

    def test_rejects_empty_claimed_rule_id(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(claimed_rule_id="")

    def test_rejects_empty_claimed_rule_version(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_attempt(claimed_rule_version="")

    def test_same_model_different_binding_session_is_valid(self) -> None:
        first = _make_attempt()
        second = _make_attempt(
            attempt_id="worker-002",
            binding_id="binding-002",
            session_id="session-002",
            independent_context_hash="f" * 64,
        )
        self.assertEqual(first.model_id, second.model_id)
        self.assertNotEqual(first.binding_id, second.binding_id)
        self.assertNotEqual(first.session_id, second.session_id)


class TestEvidenceVerification(unittest.TestCase):
    def test_passed_must_carry_no_failure_codes(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_verification(result="passed",
                               failure_reason_codes=("identity_mismatch",))

    def test_failed_must_carry_failure_code(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_verification(result="failed", failure_reason_codes=())

    def test_failed_with_closed_code(self) -> None:
        verification = _make_verification(
            result="failed",
            failure_reason_codes=("artifact_hash_mismatch",))
        self.assertEqual(verification.result, "failed")

    def test_rejects_unknown_dimension(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_verification(checked_dimensions=("telepathy",))

    def test_rejects_unknown_result(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_verification(result="maybe")

    def test_rejects_empty_dimensions(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_verification(checked_dimensions=())

    def test_failed_record_keeps_full_seven_dimension_audit(self) -> None:
        """A failed verification must still be constructible with ALL seven
        attempted dimensions recorded (auditability is never lost to the
        non-empty-dimension invariant)."""
        verification = _make_verification(
            checked_dimensions=VERIFICATION_DIMENSIONS,
            result="failed",
            failure_reason_codes=(
                "input_content_mismatch",
                "artifact_hash_mismatch",
                "source_unresolvable",
                "date_out_of_window",
                "unit_mismatch",
            ))
        self.assertEqual(set(verification.checked_dimensions),
                         set(VERIFICATION_DIMENSIONS))
        self.assertEqual(len(verification.checked_dimensions), 7)
        self.assertIn("date_out_of_window",
                      verification.failure_reason_codes)
        self.assertIn("unit_mismatch", verification.failure_reason_codes)


class TestAdjudicationBinding(unittest.TestCase):
    def test_outcome_reuses_r2_vocabulary(self) -> None:
        self.assertEqual(tuple(AdjudicationOutcome.all_outcomes()), (
            "merged_supported",
            "distinct_supported",
            "rejected_by_evidence",
            "version_mismatch",
            "needs_user_attention",
        ))

    def test_d10_pin_states_are_not_adjudication_outcomes(self) -> None:
        """D10 ``ADJUDICATION_STATES`` (accepted/divergent/pending) are pin
        states, never §9.4 adjudication outcomes."""
        for pin_state in ("accepted", "divergent", "pending"):
            with self.assertRaises(EnsembleContractError):
                AdjudicationBinding(
                    binding_id="adj-001",
                    session_id="adj-session-001",
                    model_id="model-alpha",
                    model_version="v1.0",
                    outcome=pin_state,
                    reviewed_artifact_refs=("artifact-out-001",))

    def test_rejects_empty_reviewed_artifact_refs(self) -> None:
        with self.assertRaises(EnsembleContractError):
            AdjudicationBinding(
                binding_id="adj-001",
                session_id="adj-session-001",
                model_id="model-alpha",
                model_version="v1.0",
                outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                reviewed_artifact_refs=())


class TestConflictVisibility(unittest.TestCase):
    def test_high_priority_cannot_be_hidden(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_conflict(monitoring_priority="high", hidden=True)

    def test_mutual_negation_cannot_be_hidden(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_conflict(relation="mutual_negation",
                           display_state="visible_conflict", hidden=True)

    def test_baseline_miss_cannot_be_hidden(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_conflict(relation="baseline_miss",
                           display_state="visible_baseline_miss", hidden=True)

    def test_low_priority_shared_finding_may_be_hidden(self) -> None:
        conflict = _make_conflict(
            monitoring_priority="low",
            relation="shared_finding",
            display_state="visible_conflict",
            hidden=True)
        self.assertTrue(conflict.hidden)

    def test_baseline_miss_requires_matching_display_state(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_conflict(relation="baseline_miss",
                           display_state="visible_conflict")

    def test_mutual_negation_requires_matching_display_state(self) -> None:
        with self.assertRaises(EnsembleContractError):
            _make_conflict(relation="mutual_negation",
                           display_state="needs_attention")

    def test_high_priority_visible_conflict_valid(self) -> None:
        conflict = _make_conflict(
            monitoring_priority="high",
            relation="mutual_negation",
            display_state="visible_conflict",
            hidden=False)
        self.assertFalse(conflict.hidden)

    def test_non_hideable_relations_constant(self) -> None:
        self.assertEqual(NON_HIDEABLE_RELATIONS,
                         ("mutual_negation", "baseline_miss"))


class TestStaticClosure(unittest.TestCase):
    def test_no_forbidden_decision_tokens_in_source(self) -> None:
        """The shared closure never branches on external evaluation-service
        outputs, synthetic sentinel strings, test identifiers, case indexes
        or opaque audit identifiers."""
        for path in _SRC_FILES:
            text = path.read_text(encoding="utf-8")
            hits = [token for token in _FORBIDDEN_DECISION_TOKENS
                    if token in text]
            self.assertEqual(hits, [],
                             f"{path.name} carries decision tokens: {hits}")

    def test_runtime_never_imports_forbidden_sources(self) -> None:
        text = (_R4_SRC / "mm_r4" / "ensemble.py").read_text(
            encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            low = stripped.lower()
            for token in ("oracle", "fixture", "mutation", "registry",
                          "adapter", "generator", "pytest", "unittest"):
                self.assertNotIn(token, low,
                                 f"forbidden import: {stripped}")

    def test_contracts_never_import_d10(self) -> None:
        text = (_R4_SRC / "mm_r4" / "ensemble_contracts.py").read_text(
            encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            self.assertNotIn("d10", stripped.lower(),
                             f"contracts must not couple to D10: {stripped}")


if __name__ == "__main__":
    unittest.main()
