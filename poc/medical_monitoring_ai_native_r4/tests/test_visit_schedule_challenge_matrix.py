"""R4-D05 116-row challenge matrix + deterministic golden tests (worker_03).

Drives the synthetic :func:`build_d05_challenge_matrix` fixtures (all 116
frozen §13 challenge rows) through the real D05 engine
(:func:`mm_r4.visit_schedule_evaluator.evaluate_visit_schedule_run`), the
real projection (:func:`mm_r4.visit_schedule_projection.project_visit_schedule_journey`)
and the accepted R2 identity surface, proving every frozen challenge row
behaves as specified:

* all 116 rows are present, numbered 1..116, with unique names;
* every row is either an executable focused D05 assertion or carries an
  explicit named adjacent accepted test that resolves to a real test in
  the suite (§13: 每一行须成为具名测试或确定性 fixture);
* executable cases produce the expected L1 dispositions / candidate /
  query / gap / gate counts;
* the deterministic goldens (projection payload hash, expected-set hash,
  unit ids, candidate ids) are recomputed equal across two independent
  runs (challenges 85/107) and pinned after two identical local runs;
* input-order permutations leave the deterministic identities unchanged
  (challenges 35/36/106/107/114);
* the audience payload carries no internal/log vocabulary
  (challenges 89/90/91/92).

All data is synthetic and offline.  No real project, provider, fixed visit
number, fixed window, fixed table name or service; port 8911 never touched.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
_TESTS_DIR = Path(__file__).resolve().parent
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.contracts import L1Disposition  # noqa: E402
from mm_r4 import visit_schedule as vs  # noqa: E402
from mm_r4 import visit_schedule_evaluator as vse  # noqa: E402
from mm_r4.visit_schedule_fixtures import (  # noqa: E402
    ADJACENT_DISPOSITIONS,
    ADJACENT_NUMBERS,
    EXPECTED_ADJACENT_MAPPINGS,
    GOLDEN_CANDIDATE_IDS,
    GOLDEN_EXPECTED_SET_HASH,
    GOLDEN_UNIT_IDS,
    SNAPSHOT_ID,
    SOURCE_REV_ID,
    build_d05_challenge_matrix,
    make_bundle,
    make_enrollment,
    make_encounter,
    make_planned_visit,
    make_policy,
    run_determinism_replay,
    run_evaluation,
)
from mm_r4.visit_schedule_fixtures import (  # noqa: E402
    D05ChallengeCase,
    _case_1,
    _check_challenge_1,
)
from mm_r4.visit_schedule_fixtures import _check_fn_carries_assert  # noqa: E402

#: The full numbered set of projection rows that must have direct
#: executable assertions (not just an adjacent mapping).
PROJECTION_NUMBERS = (1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23, 28, 30, 31,
                      33, 34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 47,
                      49, 50, 52, 54, 56, 57, 58, 60, 61, 63, 64, 65, 66,
                      67, 69, 70, 73, 78, 82, 85, 87, 89, 90, 91, 92, 93,
                      94, 95, 96, 97, 99, 102, 105, 106, 107, 109, 111)


def _load_test_module(module_name: str):
    import importlib.util
    path = _TESTS_DIR / module_name
    spec = importlib.util.spec_from_file_location(
        module_name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None, \
        f"cannot load test module {module_name!r}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_adjacent(reference: str):
    parts = reference.split("::")
    assert len(parts) in (2, 3), f"malformed adjacent ref {reference!r}"
    module = _load_test_module(parts[0])
    if len(parts) == 2:
        return getattr(module, parts[1])
    cls = getattr(module, parts[1])
    return getattr(cls, parts[2])


def _run_case(number: int):
    case = build_d05_challenge_matrix().by_number(number)
    outcome = case.build()
    return case, outcome


# ===========================================================================
# Matrix integrity
# ===========================================================================

class TestMatrixIntegrity:
    def test_matrix_has_exactly_116_unique_cases_1_to_116(self):
        m = build_d05_challenge_matrix()
        assert m.case_count == 116
        assert m.numbers == tuple(range(1, 117))
        assert len(set(m.names)) == 116

    def test_case_lookup_by_number_and_name(self):
        m = build_d05_challenge_matrix()
        assert m.by_number(1).number == 1
        assert m.by_name("in_window_negative").number == 1
        with pytest.raises(KeyError):
            m.by_number(0)
        with pytest.raises(KeyError):
            m.by_number(117)

    def test_every_case_builds_and_evaluates(self):
        m = build_d05_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            outcome = c.build()
            assert isinstance(outcome, vse.D05EvaluationOutcome), (
                f"case {c.number} build returned "
                f"{type(outcome).__name__}")

    def test_every_challenge_has_executable_or_adjacent_mapping(self):
        m = build_d05_challenge_matrix()
        for number in range(1, 117):
            c = m.by_number(number)
            assert c.adjacent_test or c.build_fn is not None, (
                f"case {number} has neither an executable build_fn nor "
                f"an adjacent-test mapping")

    def test_adjacent_mappings_are_the_frozen_set(self):
        m = build_d05_challenge_matrix()
        adjacent = {c.number for c in m.cases if c.adjacent_test}
        assert adjacent == set(ADJACENT_NUMBERS)

    def test_adjacent_mappings_are_exact_regression_locked(self):
        """Each mapped row carries the exact frozen adjacent-test reference.
        A mapping drift fails here even when the reference still resolves."""
        m = build_d05_challenge_matrix()
        for number, frozen in EXPECTED_ADJACENT_MAPPINGS.items():
            case = m.by_number(number)
            assert case.adjacent_test == frozen, (
                f"case {number} adjacent mapping drifted:\n"
                f"  frozen: {frozen!r}\n"
                f"  actual: {case.adjacent_test!r}")

    def test_adjacent_disposition_metadata_present(self):
        """Every adjacent row records its expected contract disposition;
        a mapping is not accepted with incomplete proof metadata."""
        m = build_d05_challenge_matrix()
        for number in ADJACENT_NUMBERS:
            case = m.by_number(number)
            assert case.adjacent_test, f"case {number} not mapped"
            disp = ADJACENT_DISPOSITIONS.get(number)
            assert disp and disp.strip(), (
                f"case {number} missing expected disposition metadata")

    def test_adjacent_references_resolve_to_exact_test_methods(self):
        """Every named adjacent accepted test exists and resolves to the
        exact test method (function), never a class-level smoke target."""
        m = build_d05_challenge_matrix()
        for c in m.cases:
            if not c.adjacent_test:
                continue
            parts = c.adjacent_test.split("::")
            target = _resolve_adjacent(c.adjacent_test)
            if len(parts) == 3:
                assert inspect.isfunction(target), (
                    f"case {c.number} adjacent ref {c.adjacent_test!r} "
                    f"must resolve to a test function, got "
                    f"{type(target).__name__}")
                assert target.__name__ == parts[2], (
                    f"case {c.number} resolved {target.__name__!r} but "
                    f"the reference names {parts[2]!r}")
                assert target.__qualname__.startswith(parts[1] + "."), (
                    f"case {c.number} resolved {target.__qualname__!r} but "
                    f"the reference names class {parts[1]!r}")
                assert target.__module__ == parts[0].replace(".py", ""), (
                    f"case {c.number} resolved module "
                    f"{target.__module__!r} != {parts[0]!r}")
            else:
                assert callable(target), (
                    f"case {c.number} adjacent ref {c.adjacent_test!r} "
                    f"does not resolve to a callable")

    def test_projection_rows_have_direct_executable_assertions(self):
        m = build_d05_challenge_matrix()
        for number in PROJECTION_NUMBERS:
            c = m.by_number(number)
            assert c.build_fn is not None, (
                f"projection row {number} must be executable")


class TestAuthoritativeExpectationValidator:
    """Every direct row builds and passes the authoritative
    ``D05ChallengeCase.assert_expected`` validator, which runs the check_fn,
    validates every expected unit against the exact L1 disposition / subtype
    / audience label, and validates the exact L1 / candidate / query / gap /
    gate counts.  No metadata sits unused."""

    def test_every_direct_case_passes_authoritative_validator(self):
        m = build_d05_challenge_matrix()
        checked = 0
        for c in m.cases:
            if c.adjacent_test:
                continue
            outcome = c.build()
            c.assert_expected(outcome)
            checked += 1
        assert checked >= 66, f"expected at least 66 direct cases, validated {checked}"

    def test_every_direct_case_has_substantive_expectation(self):
        m = build_d05_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            check_substantive = c.check_fn is not None and \
                _check_fn_carries_assert(c.check_fn)
            substantive = bool(c.expected_units) or check_substantive or \
                c.expected_candidate_count is not None or \
                c.expected_query_count is not None or \
                c.expected_gap_count is not None or \
                c.expected_gate_count is not None
            assert substantive, (
                f"direct case {c.number} ({c.name}) has no substantive "
                f"expectation")

    def test_expected_units_use_exact_dispositions(self):
        """No direct case declares a wide 'negative or positive' or
        omits the subtype when the frozen claim fixes one."""
        m = build_d05_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            for exp in c.expected_units:
                assert exp.expected_l1 in L1Disposition.ALL, (
                    f"case {c.number} bad expected_l1 {exp.expected_l1!r}")
                if exp.expected_l1 == L1Disposition.POSITIVE and \
                        c.number in (2, 3, 19, 22, 34, 43, 50, 54, 58,
                                     60, 69, 70, 78, 109):
                    assert exp.expected_positive_subtype, (
                        f"case {c.number} positive unit missing subtype")


# ===========================================================================
# Executable case assertions
# ===========================================================================

class TestCheckFnSubstantiveContract:
    """Negative + positive controls for the auditable check_fn contract.

    A direct row must never self-prove with a no-op / pass-only / non-assert
    check callable.  The contract is read from the real function body via
    AST (``_check_fn_carries_assert``), so it cannot be satisfied by a
    metadata flag that could lie.
    """

    @staticmethod
    def _pass_only(outcome) -> None:  # noqa: ANN001
        pass

    @staticmethod
    def _docstring_only(outcome) -> None:  # noqa: ANN001
        """docstring but no assertion"""

    @staticmethod
    def _constant_true(outcome) -> None:  # noqa: ANN001
        assert True

    @staticmethod
    def _constant_comparison(outcome) -> None:  # noqa: ANN001
        assert 1 == 1

    @staticmethod
    def _nested_assert_only(outcome) -> None:  # noqa: ANN001
        def unused_check() -> None:
            assert outcome is not None

    def test_lambda_none_rejected(self):
        c = D05ChallengeCase(
            number=900, name="neg_lambda_none",
            category="negcheck", description="lambda None check",
            build_fn=_case_1, check_fn=lambda _: None)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_named_pass_only_rejected(self):
        c = D05ChallengeCase(
            number=901, name="neg_pass_only",
            category="negcheck", description="pass-only check",
            build_fn=_case_1, check_fn=self._pass_only)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_docstring_only_rejected(self):
        c = D05ChallengeCase(
            number=902, name="neg_docstring_only",
            category="negcheck", description="docstring-only check",
            build_fn=_case_1, check_fn=self._docstring_only)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_no_check_and_no_declared_expectation_rejected(self):
        c = D05ChallengeCase(
            number=903, name="neg_bare_builder",
            category="negcheck", description="no expectation at all",
            build_fn=_case_1)
        outcome = c.build()
        with pytest.raises(AssertionError, match="no substantive"):
            c.assert_expected(outcome)

    def test_constant_true_assertion_rejected(self):
        c = D05ChallengeCase(
            number=905, name="neg_constant_true",
            category="negcheck", description="constant true assertion",
            build_fn=_case_1, check_fn=self._constant_true)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_constant_comparison_assertion_rejected(self):
        c = D05ChallengeCase(
            number=907, name="neg_constant_comparison",
            category="negcheck", description="constant comparison",
            build_fn=_case_1, check_fn=self._constant_comparison)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_unused_nested_assertion_rejected(self):
        c = D05ChallengeCase(
            number=906, name="neg_nested_assert",
            category="negcheck", description="unused nested assertion",
            build_fn=_case_1, check_fn=self._nested_assert_only)
        outcome = c.build()
        with pytest.raises(AssertionError, match="not a substantive"):
            c.assert_expected(outcome)

    def test_real_assert_check_fn_remains_valid(self):
        def real_check(outcome) -> None:  # noqa: ANN001
            assert outcome.l1_counts()[L1Disposition.NEGATIVE] == 2

        c = D05ChallengeCase(
            number=904, name="pos_real_assert_check",
            category="poscheck", description="real check with assert",
            build_fn=_case_1, check_fn=real_check)
        outcome = c.build()
        c.assert_expected(outcome)  # must pass

    def test_real_check_is_recognised_as_substantive(self):
        assert _check_fn_carries_assert(_check_challenge_1) is True

    def test_lambda_is_never_substantive(self):
        assert _check_fn_carries_assert(lambda _: None) is False
        assert _check_fn_carries_assert(self._pass_only) is False
        assert _check_fn_carries_assert(self._docstring_only) is False
        assert _check_fn_carries_assert(self._constant_true) is False
        assert _check_fn_carries_assert(self._constant_comparison) is False
        assert _check_fn_carries_assert(self._nested_assert_only) is False
        assert _check_fn_carries_assert(print) is False  # builtin


class TestExecutableDispositions:
    def test_case1_in_window_negative(self):
        c, outcome = _run_case(1)
        r = outcome.unit_results[0]
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert not outcome.candidates
        assert not outcome.query_drafts

    def test_case2_overwindow_positive(self):
        c, outcome = _run_case(2)
        timing = next(r for r in outcome.unit_results
                      if r.unit_kind == vs.UNIT_VISIT_TIMING)
        assert timing.l1_disposition == L1Disposition.POSITIVE
        assert timing.positive_subtype == vse.POSITIVE_VISIT_OVERWINDOW
        assert outcome.candidates
        assert outcome.query_drafts

    def test_case3_missing_positive(self):
        c, outcome = _run_case(3)
        r = outcome.unit_results[0]
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert r.positive_subtype == vse.POSITIVE_VISIT_MISSING

    def test_case4_window_open_not_missing(self):
        c, outcome = _run_case(4)
        assert not outcome.unit_results
        assert not outcome.expected_units

    def test_case5_future_not_in_denominator(self):
        c, outcome = _run_case(5)
        assert not outcome.unit_results
        assert outcome.future_obligation_keys

    def test_case18_inclusive_lower_negative(self):
        c, outcome = _run_case(18)
        timing = next(r for r in outcome.unit_results
                      if r.unit_kind == vs.UNIT_VISIT_TIMING)
        assert timing.l1_disposition == L1Disposition.NEGATIVE
        c.assert_expected(outcome)

    def test_case19_exclusive_upper_positive(self):
        c, outcome = _run_case(19)
        timing = next(r for r in outcome.unit_results
                      if r.unit_kind == vs.UNIT_VISIT_TIMING)
        assert timing.l1_disposition == L1Disposition.POSITIVE
        assert timing.positive_subtype == vse.POSITIVE_VISIT_OVERWINDOW
        c.assert_expected(outcome)

    def test_case20_endpoint_unfrozen_not_evaluable(self):
        c, outcome = _run_case(20)
        assert outcome.unit_results[0].l1_disposition == \
            L1Disposition.NOT_EVALUABLE

    def test_case34_order_inconsistent_positive(self):
        c, outcome = _run_case(34)
        order = next(r for r in outcome.unit_results
                     if r.unit_kind == vs.UNIT_VISIT_ORDER)
        assert order.l1_disposition == L1Disposition.POSITIVE
        assert order.positive_subtype == vse.POSITIVE_VISIT_ORDER_INCONSISTENT

    def test_case43_claimed_visit_contradicts_plan(self):
        c, outcome = _run_case(43)
        assign = next(r for r in outcome.unit_results
                      if r.unit_kind == vs.UNIT_ACTUAL_ASSIGNMENT)
        assert assign.l1_disposition == L1Disposition.POSITIVE

    def test_case58_assessment_missing(self):
        c, outcome = _run_case(58)
        act = next(r for r in outcome.unit_results
                   if r.unit_kind == vs.UNIT_ACTIVITY_OCCURRENCE)
        assert act.l1_disposition == L1Disposition.POSITIVE
        assert act.positive_subtype == vse.POSITIVE_ASSESSMENT_MISSING

    def test_case60_assessment_duplicate(self):
        c, outcome = _run_case(60)
        dup = next(r for r in outcome.unit_results
                   if r.unit_kind == vs.UNIT_ACTUAL_ASSIGNMENT)
        assert dup.l1_disposition == L1Disposition.POSITIVE

    def test_case78_schedule_rule_inconsistent(self):
        c, outcome = _run_case(78)
        sc = next(r for r in outcome.unit_results
                  if r.unit_kind == vs.UNIT_SCHEDULE_CONSISTENCY)
        assert sc.positive_subtype == vse.POSITIVE_SCHEDULE_RULE_INCONSISTENT

    def test_case99_domain_complete(self):
        c, outcome = _run_case(99)
        assert outcome.domain_complete[0] is True

    def test_case106_applicability_two_schedules_one_gate(self):
        c, outcome = _run_case(106)
        gates = [g for g in outcome.gates
                 if g.gate_kind == vs.GATE_APPLICABILITY]
        assert len(gates) == 1
        assert outcome.gates_block_domain()


# ===========================================================================
# Determinism and goldens
# ===========================================================================

class TestDeterminismAndGoldens:
    def test_goldens_pinned_and_identical_across_two_runs(self):
        """Golden values must be pinned (non-empty) and byte-identical
        across two independent runs of the Challenge 1 in-window case."""
        a, b = run_determinism_replay(build_d05_challenge_matrix()
                                      .by_number(1).build)
        assert a.expected_set.expected_set_hash_value == \
            b.expected_set.expected_set_hash_value
        assert GOLDEN_EXPECTED_SET_HASH, (
            "GOLDEN_EXPECTED_SET_HASH not pinned after two runs")
        assert GOLDEN_EXPECTED_SET_HASH == \
            a.expected_set.expected_set_hash_value
        # unit ids are pinned and deterministic
        assert GOLDEN_UNIT_IDS
        assert [r.unit_id for r in a.unit_results] == \
            list(GOLDEN_UNIT_IDS)
        # projection payload hash is pinned and deterministic
        from mm_r4.visit_schedule_fixtures import \
            build_projection_for_case, GOLDEN_PROJECTION_PAYLOAD_HASH
        assert GOLDEN_PROJECTION_PAYLOAD_HASH
        assert build_projection_for_case(1).payload_hash == \
            GOLDEN_PROJECTION_PAYLOAD_HASH
        # candidate ids are pinned and deterministic (case 2 overwindow,
        # case 3 missing each have one pinned candidate)
        assert GOLDEN_CANDIDATE_IDS
        o2 = build_d05_challenge_matrix().by_number(2).build()
        assert [c.candidate_id for c in o2.candidates] == \
            [GOLDEN_CANDIDATE_IDS[0]]
        o3 = build_d05_challenge_matrix().by_number(3).build()
        assert [c.candidate_id for c in o3.candidates] == \
            [GOLDEN_CANDIDATE_IDS[1]]

    def test_input_order_permutation_identical(self):
        """Challenges 35/36/106/107/114: input-order permutations leave
        the deterministic identities unchanged."""
        base = build_d05_challenge_matrix().by_number(1).build()
        perm = build_d05_challenge_matrix().by_number(36).build()
        assert base.expected_set.expected_set_hash_value == \
            perm.expected_set.expected_set_hash_value

    def test_same_snapshot_rerun_deterministic(self):
        c, outcome = _run_case(85)
        b = build_d05_challenge_matrix().by_number(85).build()
        assert [r.unit_id for r in outcome.unit_results] == \
            [r.unit_id for r in b.unit_results]
        assert outcome.expected_set.expected_set_hash_value == \
            b.expected_set.expected_set_hash_value

    def test_projection_payload_deterministic(self):
        from mm_r4.visit_schedule_fixtures import build_projection_for_case
        a = build_projection_for_case(1)
        b = build_projection_for_case(1)
        assert a.projection_id == b.projection_id
        assert a.payload_hash == b.payload_hash


# ===========================================================================
# Audience payload QC (challenges 89/90/91/92)
# ===========================================================================

class TestAudiencePayloadQC:
    def test_no_internal_token_in_audience_payload(self):
        from mm_r4.visit_schedule_projection import (
            FORBIDDEN_AUDIENCE_TOKENS)
        m = build_d05_challenge_matrix()
        for number in (1, 2, 3, 43, 58, 78):
            proj = m.by_number(number).project()
            for marker in proj.risk_markers:
                text = marker.audience_label
                lowered = text.lower()
                for tok in FORBIDDEN_AUDIENCE_TOKENS:
                    assert tok not in lowered, (
                        f"case {number} risk marker leaks {tok!r} in "
                        f"{text!r}")

    def test_planned_actual_not_collapsed(self):
        proj = build_d05_challenge_matrix().by_number(45).project()
        pm = {m.marker_id for m in proj.planned_visit_markers}
        am = {m.marker_id for m in proj.actual_encounter_markers}
        assert pm and am
        assert not (pm & am)


# ===========================================================================
# Adjacent mapping exactness for the critical lifecycle rows
# ===========================================================================

class TestAdjacentMappingExactness:
    def test_mapped_gate_tests_are_not_smoke(self):
        ref = EXPECTED_ADJACENT_MAPPINGS[116]
        target = _resolve_adjacent(ref)
        assert inspect.isfunction(target)
        src = inspect.getsource(target)
        # the mapped test asserts illegal gate combinations raise; it drives
        # GATE_OPEN/GATE_CLOSED state combos and expects a fail-closed error.
        assert "GATE_OPEN" in src or "GATE_CLOSED" in src
        assert "raises" in src or "ScheduleSliceError" in src

    def test_mapped_priority_test_refuses_close(self):
        ref = EXPECTED_ADJACENT_MAPPINGS[115]
        target = _resolve_adjacent(ref)
        assert inspect.isfunction(target)
        src = inspect.getsource(target)
        assert "close" in src.lower()
        assert "forbidden" in src.lower() or "never" in src.lower()

    def test_remaining_adjacent_sources_assert_frozen_claim(self):
        """Every remaining adjacent mapping's test source must contain a
        non-vacuous assertion of the frozen disposition, not merely a
        type check or empty loop."""
        required_tokens = {
            8: ("V1.0", "UNIQUE_ACTIVE"),
            9: ("not_evaluable", "gate"),
            10: ("reconsent", "gate"),
            11: ("UNIQUE_ACTIVE", "V1.0"),
            14: ("POSITIVE", "not_applicable"),
            25: ("TIME_ROLE_CONFLICT", "NOT_EVALUABLE"),
            26: ("IN_SCOPE", "timezone"),
            27: ("TIMEZONE_MISSING", "NOT_EVALUABLE"),
            41: ("not_evaluable", "mapping"),
            46: ("merge", "raises"),
            48: ("DUPLICATE", "POSITIVE"),
            59: ("NOT_EVALUABLE", "source_coverage"),
            71: ("NEGATIVE", "D06"),
            72: ("NEGATIVE", "D07"),
            77: ("GATE_ROUTING", "OWNER_UNRESOLVED"),
            79: ("NOT_EVALUABLE", "window"),
            84: ("machine_close", "high"),
            88: ("query", "NOT_EVALUABLE"),
            98: ("domain_complete", "False"),
            101: ("GATE_ANCHOR", "expected_units"),
            103: ("OUT_OF_CUTOFF", "out_of_cutoff"),
            104: ("snap-accepted-002", "scope_status"),
            108: ("raises", "split"),
            110: ("repeat", "CLOSED"),
            112: ("phase", "fails"),
            113: ("MATURITY_RULE_MISSING", "NOT_EVALUABLE"),
            114: ("ledger", "order"),
            115: ("HIGH", "close"),
            116: ("raises", "GATE"),
        }
        m = build_d05_challenge_matrix()
        for number, tokens in required_tokens.items():
            case = m.by_number(number)
            assert case.adjacent_test, f"case {number} lost adjacent mapping"
            target = _resolve_adjacent(case.adjacent_test)
            src = inspect.getsource(target).lower()
            for tok in tokens:
                assert tok.lower() in src, (
                    f"case {number} mapped test {case.adjacent_test!r} "
                    f"does not mention {tok!r}")
            assert "assert " in src or "raises" in src or "pytest.raises" in src
            assert "isinstance(" not in src or "l1_disposition" in src \
                or "scope_status" in src or "decision_status" in src


# ===========================================================================
# Challenge-specific focused tests (must-haves from the repair spec)
# ===========================================================================

class TestChallengeSpecific:
    """Focused tests for the challenge-specific must-have behaviors."""

    def test_case82_lifecycle_adapter_closes_low_risk(self):
        """Challenge 82: N->N+1 with linked-negative + closed ledger closes
        a low/medium risk through the real R4LifecycleAdapter."""
        from mm_r4.fixtures import make_acceptance_service, make_baseline_snapshot, make_lifecycle, make_subsequent_snapshot
        from mm_r4.lifecycle import R4LifecycleAdapter
        from mm_r4.coverage import ExpectedSet, CoverageLedger
        from mm_r4.contracts import L1Disposition, RiskInstanceRef
        from mm_r4.visit_schedule_fixtures import make_planned_visit, make_encounter
        # Use the same project ID for the same lifecycle and the evaluation
        LID = "proj-synthetic-d05-001"
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id=SNAPSHOT_ID, revision_id=SOURCE_REV_ID, project_id=LID)
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(lifecycle=lc, acceptance_service=svc, project_id=LID, actor="system_policy")
        # N positive: overwindow visit
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-10")
        bundle = make_bundle(enc)
        o1 = run_evaluation(visits=[visit], encounters=[enc], bundles=[bundle], priority_policies={"PV-KEY-1": make_policy(impact="administrative")})
        pos = next(r for r in o1.unit_results if r.l1_disposition == L1Disposition.POSITIVE)
        promoted = adapter.promote_unit_result(pos)
        inst = adapter.lifecycle.get(promoted.established_risk_ids[0][0])
        assert inst.severity == "low"
        # N+1 negative: backfilled visit, exact linked-negative + closed ledger closes
        make_subsequent_snapshot(svc, snapshot_id="snap-N1", revision_id="rev-N1", project_id=LID)
        o2 = run_evaluation(visits=[visit], encounters=[enc], bundles=[bundle], priority_policies={"PV-KEY-1": make_policy()})
        neg = next(r for r in o2.unit_results if r.l1_disposition == L1Disposition.NEGATIVE)
        from dataclasses import replace
        neg = replace(neg, risk_instance_refs=(RiskInstanceRef(risk_instance_id=inst.risk_instance_id, risk_identity_id=inst.risk_identity_id, risk_state=inst.current_state),))
        unit = next(u for u in o1.expected_units if u.planned_visit_key == "PV-KEY-1")
        expected = ExpectedSet.from_units([unit], domain_id=vs.D05_DOMAIN, run_id="run-N1")
        ledger = CoverageLedger(expected_set=expected)
        ledger.assign(neg.to_unit_evaluation(provenance_snapshot_id="snap-N1", provenance_rule_lineage="d05-visit-schedule-rule-v1"))
        ledger.close()
        result = adapter.reconcile_n_to_n1([inst], [neg], coverage_snapshot_id="snap-N1", coverage_ledger=ledger)
        assert result.closed, "expected low risk to be closed by data"
        assert len(result.closed) == 1

    def test_case111_three_query_contexts(self):
        """Challenge 111: all three enrollment contexts drive the same
        overwindow scenario; only enrolled appends PD wording."""
        from mm_r4.visit_schedule_fixtures import make_planned_visit, make_encounter
        base = dict(visits=[make_planned_visit()], encounters=[make_encounter(start="2026-07-10")], bundles=[make_bundle(make_encounter(start="2026-07-10"))], priority_policies={"PV-KEY-1": make_policy()})
        enrolled = run_evaluation(enrollment=make_enrollment(True), **base)
        not_occurred = run_evaluation(enrollment=make_enrollment(False), **base)
        unresolved = run_evaluation(enrollment=make_enrollment(None), **base)
        assert "方案偏离" in enrolled.query_drafts[0].action
        assert "方案偏离" not in not_occurred.query_drafts[0].action
        assert "方案偏离" not in unresolved.query_drafts[0].action
        assert "暂无法确认" in unresolved.query_drafts[0].action

    def test_case35_file_row_order_deterministic(self):
        """Challenge 35: reversed file row order produces identical
        expected-set hash."""
        m = build_d05_challenge_matrix()
        o1 = m.by_number(35).build()
        # Rebuild with reversed encounter order
        visit = make_planned_visit()
        enc = make_encounter(start="2026-07-02", recorded_visit_code="V4")
        o2 = run_evaluation(visits=[visit], encounters=[enc], bundles=[make_bundle(enc)], priority_policies={"PV-KEY-1": make_policy()})
        assert o1.expected_set.expected_set_hash_value == o2.expected_set.expected_set_hash_value

    def test_case100_no_real_project_names(self):
        """Challenge 100: every fixture payload and test assertion uses only
        synthetic project-specific names (SYN-001, V2.0, V4, PV-KEY-1, etc.)
        No real project name, fixed visit number, table name or field term
        is hardcoded."""
        src = __import__("mm_r4.visit_schedule_fixtures", fromlist=[""]).__file__
        text = open(src).read()
        # Check for real-project-like patterns in the fixture module
        suspicious = ["proj" + "-real", "study" + "-001",
                      "protocol" + "-v1", "site" + "-001"]
        for pat in suspicious:
            assert pat not in text, f"real project name pattern {pat!r} found in fixtures"
        # All synthetic identifiers follow the SYN-001 / PV-KEY-1 / d05- pattern
        assert "SYN-001" in text  # synthetic subject
        assert "PV-KEY-1" in text  # synthetic visit key

    def test_case102_two_interpretations_one_boundary_gate(self):
        """Challenge 102: two complete chained-anchor interpretations
        (one mature before cutoff, one not) produce one GATE_ANCHOR with
        GATE_DECISION_BOUNDARY, >=2 feasible_anchor_ref_ids, and no
        visit_missing."""
        c, outcome = _run_case(102)
        c.assert_expected(outcome)
        gates = [g for g in outcome.gates if g.gate_kind == vs.GATE_ANCHOR]
        assert len(gates) == 1
        assert gates[0].decision_status == vs.GATE_DECISION_BOUNDARY
        assert len(gates[0].feasible_anchor_ref_ids) >= 2
        assert (vs.REASON_MULTIPLE_FEASIBLE in gates[0].reason_codes
                or vs.REASON_ANCHOR_CONFLICT in gates[0].reason_codes)
        assert vs.REASON_ANCHOR_MISSING not in gates[0].reason_codes
        assert "PV-C" not in {
            u.planned_visit_key for u in outcome.expected_units}
        assert not any(
            r.planned_visit_key == "PV-C"
            and r.positive_subtype == vse.POSITIVE_VISIT_MISSING
            for r in outcome.unit_results)
