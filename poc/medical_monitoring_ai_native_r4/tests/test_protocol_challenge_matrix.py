"""R4-D04 protocol 83-case challenge matrix + golden hash tests (worker_03).

Drives the synthetic :func:`build_protocol_challenge_matrix` fixtures (all
83 frozen §12 challenge rows) through the real D04 engine
(``mm_r4.protocol``), the real projection (``mm_r4.protocol_projection``)
and the real R2 identity surface, proving every frozen challenge row
behaves as specified:

* all 83 numbered cases are present; every case is either an executable
  focused D04 assertion or carries an explicit named adjacent accepted
  test that resolves to a real test in the suite (§13: "所有 83 项合同
  挑战映射到聚焦的 D04 断言或命名相邻已接受测试");
* corrective 02: each adjacent mapping is exact-regression-locked to the
  frozen reference string and must resolve to the exact test method that
  exercises the full producer-side claim (high/user-confirmed/identity-
  ambiguous close refusal; reconcile-executed SUPERSEDED with closed==();
  medium -> persisted high -> machine-close refusal; resolver-driven
  next-visit/re-consent gate) -- a class-level smoke target or a
  reader-only flag test is never accepted as a producer mapping;
* the executable cases produce the expected per-unit L1 dispositions and
  candidate/Query/coverage-gap counts (core dispositions, applicability
  gates, numeric/unit/rounding/retest, exceptions, producer routing,
  evidence identity, sequence anchors, discontinuation, Query contexts,
  package expressions, cross-domain facts, age/retest/wording and
  order-independence rows);
* the frozen golden hashes (unit ids, component-assessment ids,
  expected-set hashes, candidate ids, projection payload hashes) are
  recomputed equal -- deterministic identities across reruns
  (challenges 48/59/60/68/83);
* deterministic replay of the same inputs yields identical unit ids,
  expected-set hashes and candidate ids;
* D01-D03 / R2 / R3 adjacent regressions stay green (challenge 55,
  verified by the full-suite verification stage) and port 8911 stays
  stopped.

All data is synthetic and offline.  No real project, provider,
dictionary, or product service; port 8911 is never touched.
"""

from __future__ import annotations

import importlib.util
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

import mm_r4.protocol as p  # noqa: E402
import mm_r4.protocol_projection as pp  # noqa: E402
from mm_r4.contracts import L1Disposition  # noqa: E402
from mm_r4.protocol_fixtures import (  # noqa: E402
    GOLDEN_CANDIDATE_IDS,
    GOLDEN_COMPONENT_ASSESSMENT_IDS,
    GOLDEN_EXPECTED_SET_HASH,
    GOLDEN_PROJECTION_PAYLOAD_HASH,
    GOLDEN_UNIT_IDS,
    PROJECT_ID,
    ProtocolChallengeCase,
    build_protocol_challenge_matrix,
    run_determinism_replay,
)

#: Challenge rows that are explicit mappings to a named adjacent accepted
#: test (lifecycle / shared flags / adjacent-slice regression rows).
ADJACENT_NUMBERS = (49, 50, 51, 52, 55, 61, 62, 64, 65, 66, 70, 78)

#: Exact frozen adjacent-test reference per mapped challenge row.  The
#: reference strings are the producer-side contract of each mapping: they
#: may only change with a recorded contract reason.  Each reference must
#: resolve to the exact test that exercises the full producer-side claim
#: (corrective 02), never a class-level smoke or reader-only test.
EXPECTED_ADJACENT_MAPPINGS = {
    49: ("test_protocol_slice.py::TestLifecycleIntegration::"
         "test_machine_close_requires_linked_negative_and_closed_ledger"),
    50: ("test_protocol_slice.py::TestLifecycleIntegration::"
         "test_high_user_confirmed_and_identity_ambiguous_never_"
         "machine_close"),
    51: ("test_protocol_slice.py::TestLifecycleIntegration::"
         "test_machine_close_requires_linked_negative_and_closed_ledger"),
    52: ("test_lifecycle_projection.py::TestSupersedeAndTerminate::"
         "test_supersede_on_lineage_change"),
    55: "test_ip_challenge_matrix.py::TestAdjacentRegression",
    61: ("test_protocol_slice.py::TestRetestAndExceptions::"
         "test_n1_pre_allowed_exception_reevaluates_negative"),
    62: ("test_lifecycle_projection.py::TestSupersedeAndTerminate::"
         "test_supersede_on_lineage_change"),
    64: ("test_protocol_slice.py::TestRemainingSemantics::"
         "test_site_ref_stays_in_lineage"),
    65: ("test_protocol_slice.py::TestApplicability::"
         "test_event_time_not_run_time_selects_version"),
    66: ("test_lifecycle_projection.py::TestCriticalityFlagNormalization::"
         "test_flagged_high_instance_refuses_machine_close"),
    70: ("test_protocol_slice.py::TestLifecycleIntegration::"
         "test_machine_close_forbidden_forces_high_and_blocks_close"),
    78: ("test_protocol_slice.py::TestApplicability::"
         "test_next_visit_or_reconsent_missing_trigger_one_gate"),
}


def _run_case(number: int):
    case = build_protocol_challenge_matrix().by_number(number)
    exp, results = case.build()
    sr, _ = case.build_slice()
    return case, exp, results, sr


def _load_test_module(module_name: str):
    """Load a test module by file name from the R4 tests directory."""
    path = _TESTS_DIR / module_name
    spec = importlib.util.spec_from_file_location(
        module_name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None, \
        f"cannot load test module {module_name!r}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_adjacent(reference: str):
    """Split 'module::Class::test' or 'module::test' and load the target."""
    parts = reference.split("::")
    assert len(parts) in (2, 3), f"malformed adjacent ref {reference!r}"
    module = _load_test_module(parts[0])
    if len(parts) == 2:
        return getattr(module, parts[1])
    cls = getattr(module, parts[1])
    return getattr(cls, parts[2])


# ===========================================================================
# Matrix integrity
# ===========================================================================

class TestMatrixIntegrity:
    """The matrix has exactly 83 cases numbered 1-83; every challenge is
    executable or mapped to a resolvable adjacent accepted test."""

    def test_matrix_has_83_cases_numbered_1_to_83(self):
        m = build_protocol_challenge_matrix()
        assert m.case_count == 83
        assert m.numbers == tuple(range(1, 84))

    def test_case_lookup_by_number_and_name(self):
        m = build_protocol_challenge_matrix()
        assert m.by_number(1).number == 1
        assert m.by_name("inclusion_not_met_positive").number == 1
        with pytest.raises(KeyError):
            m.by_number(99)

    def test_every_case_builds_and_evaluates(self):
        m = build_protocol_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            exp, results = c.build()
            assert exp.count == c.expected_count(), (
                f"case {c.number} ({c.name}) expected_set size "
                f"{c.expected_count()} != expansion {exp.count}")
            assert len(results) == exp.count, (
                f"case {c.number} result count != expansion count")

    def test_every_challenge_has_executable_or_adjacent_mapping(self):
        m = build_protocol_challenge_matrix()
        for number in range(1, 84):
            c = m.by_number(number)
            assert c.adjacent_test or c.expected_units or \
                c.expected_set_size is not None, (
                f"case {number} has neither an executable assertion nor "
                f"an adjacent-test mapping")

    def test_adjacent_mappings_are_the_frozen_set(self):
        m = build_protocol_challenge_matrix()
        adjacent = {c.number for c in m.cases if c.adjacent_test}
        assert adjacent == set(ADJACENT_NUMBERS)

    def test_adjacent_mappings_are_exact_regression_locked(self):
        """Corrective 02: each mapped row carries the exact frozen
        adjacent-test reference.  A mapping drift (e.g. back to a
        reader-only flag test or a class-level smoke test) fails here even
        when the reference still resolves."""
        m = build_protocol_challenge_matrix()
        for number, frozen in EXPECTED_ADJACENT_MAPPINGS.items():
            case = m.by_number(number)
            assert case.adjacent_test == frozen, (
                f"case {number} adjacent mapping drifted:\n"
                f"  frozen: {frozen!r}\n"
                f"  actual: {case.adjacent_test!r}")

    def test_adjacent_references_resolve_to_exact_test_methods(self):
        """Every named adjacent accepted test exists and resolves to the
        exact test method (function), never a class-level smoke target.
        A 3-part reference must resolve to a function whose name and
        defining class match the reference; the individual lifecycle
        transition behavior itself is proven by running that mapped test
        green in the suite, which the resolution alone does not claim."""
        m = build_protocol_challenge_matrix()
        for c in m.cases:
            if not c.adjacent_test:
                continue
            parts = c.adjacent_test.split("::")
            target = _resolve_adjacent(c.adjacent_test)
            if len(parts) == 3:
                assert inspect.isfunction(target), (
                    f"case {c.number} adjacent ref {c.adjacent_test!r} "
                    f"must resolve to a test function, got "
                    f"{type(target).__name__} (class-level smoke targets "
                    f"do not prove the lifecycle transition)")
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

    def test_mapped_supersede_tests_are_not_class_smoke(self):
        """Challenges 52/62 map to the reconcile-executing supersede test,
        not the identity-only lineage test.  The mapped test asserts
        SUPERSEDED and closed == () after reconcile."""
        for number in (52, 62):
            ref = EXPECTED_ADJACENT_MAPPINGS[number]
            target = _resolve_adjacent(ref)
            assert target.__name__ == "test_supersede_on_lineage_change"
            src = inspect.getsource(target)
            assert "reconcile" in src or "machine_close" in src
            assert "SUPERSEDED" in src or "superseded" in src.lower()

    def test_mapped_flag_test_proves_medium_to_high_to_refusal(self):
        """Challenge 66 maps to the shared lifecycle test that proves
        medium -> persisted high -> refusal in one test; reader-only flag
        readers stay supporting coverage, not the producer mapping."""
        ref = EXPECTED_ADJACENT_MAPPINGS[66]
        target = _resolve_adjacent(ref)
        assert target.__name__ == (
            "test_flagged_high_instance_refuses_machine_close")
        src = inspect.getsource(target)
        assert 'severity == "high"' in src
        assert "machine_close_by_data" in src
        assert "must_carry_forward" in src
        # The caller-provided medium priority lives in the class helper
        # that this test drives; medium -> persisted high -> refusal is
        # one call path.
        module = _load_test_module("test_lifecycle_projection.py")
        helper_src = inspect.getsource(
            module.TestCriticalityFlagNormalization._establish_flagged)
        assert 'priority="medium"' in helper_src

    def test_mapped_reconsent_test_is_resolver_driven(self):
        """Challenge 78 maps to the resolver-driven next-visit/re-consent
        test, not a hand-constructed gate-only decision."""
        ref = EXPECTED_ADJACENT_MAPPINGS[78]
        target = _resolve_adjacent(ref)
        assert target.__name__ == (
            "test_next_visit_or_reconsent_missing_trigger_one_gate")
        src = inspect.getsource(target)
        assert "resolve_protocol_applicability" in src

    def test_all_adjacent_cases_are_numbered_53_and_55_mixed(self):
        """Cases 49-53/55 are lifecycle/regression rows; 53 also carries an
        executable lineage assertion (its adjacent ref is auxiliary)."""
        c = build_protocol_challenge_matrix().by_number(53)
        assert c.adjacent_test or c.check_fn is not None


# ===========================================================================
# Executable case assertions
# ===========================================================================

class TestCoreDispositions:
    """Challenges 1-6: inclusion/exclusion core dispositions."""

    def test_case1_inclusion_not_met_positive(self):
        c, exp, results, sr = _run_case(1)
        r = results[0]
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert r.positive_subtype == p.SUBTYPE_INCLUSION_NOT_MET
        assert r.audience_label == "入选条件待核实"
        assert len(r.r2_candidates) == 1
        assert len(r.query_refs) == 1

    def test_case2_inclusion_met_negative(self):
        c, exp, results, sr = _run_case(2)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE
        assert not results[0].r2_candidates

    def test_case3_exclusion_present_positive(self):
        c, exp, results, sr = _run_case(3)
        r = results[0]
        assert r.positive_subtype == p.SUBTYPE_EXCLUSION_PRESENT

    def test_case4_exclusion_absent_negative_with_coverage(self):
        c, exp, results, sr = _run_case(4)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE

    def test_case5_ie_summary_only_not_evaluable(self):
        c, exp, results, sr = _run_case(5)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_IE_SUMMARY_ONLY
                   for n in r.coverage_gap_notices)
        assert not r.r2_candidates and not r.query_refs

    def test_case6_zero_rows_never_negative(self):
        c, exp, results, sr = _run_case(6)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE


class TestApplicabilityGates:
    """Challenges 11-15, 60, 71, 77, 83."""

    def test_case11_old_version_when_site_not_adopted(self):
        c, exp, results, sr = _run_case(11)
        assert exp.applicability.protocol_version == "V1.0"
        assert results[0].l1_disposition == L1Disposition.POSITIVE

    def test_case12_same_day_adoption_boundary(self):
        c, exp, results, sr = _run_case(12)
        assert sr.boundary_count == 1
        assert results[0].control_point_id == "protocol_applicability"

    def test_case13_two_feasible_versions_one_gate(self):
        c, exp, results, sr = _run_case(13)
        assert exp.count == 1
        assert results[0].l1_disposition == L1Disposition.BOUNDARY
        assert sr.positive_count == 0

    def test_case14_missing_dates_not_evaluable_gate(self):
        c, exp, results, sr = _run_case(14)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_APPLICABILITY_UNDETERMINED
                   for n in results[0].coverage_gap_notices)

    def test_case15_regulatory_guidance_data_driven(self):
        c, exp, results, sr = _run_case(15)
        # The engine itself holds no regulatory calendar; the switch is
        # data-driven (exercised by the case check_fn).
        assert results[0].l1_disposition == L1Disposition.NEGATIVE

    def test_case60_gate_input_order_independent(self):
        c, exp, results, sr = _run_case(60)
        assert exp.count == 1
        assert sr.boundary_count == 1

    def test_case71_many_control_points_still_one_gate(self):
        c, exp, results, sr = _run_case(71)
        assert exp.count == 1
        assert sr.boundary_count == 1
        sr.verify_count_invariants()

    def test_case77_new_enrollment_only_grandfathers_v1(self):
        c, exp, results, sr = _run_case(77)
        assert exp.applicability.protocol_version == "V1.0"

    def test_case83_reverse_order_same_hash(self):
        c, exp, results, sr = _run_case(83)
        assert exp.count == 1
        assert sr.boundary_count == 1


class TestNumericUnitRoundingRetest:
    """Challenges 16-24, 81."""

    def test_case16_below_lower_bound_positive(self):
        c, exp, results, sr = _run_case(16)
        assert results[0].l1_disposition == L1Disposition.POSITIVE

    def test_case17_exact_threshold_inclusive_determinate(self):
        c, exp, results, sr = _run_case(17)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE

    def test_case18_unstated_equality_boundary_no_query(self):
        c, exp, results, sr = _run_case(18)
        assert results[0].l1_disposition == L1Disposition.BOUNDARY
        assert len(results[0].r2_candidates) == 1
        assert not results[0].query_refs

    def test_case19_unit_conversion_determinate(self):
        c, exp, results, sr = _run_case(19)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE

    def test_case20_unknown_unit_not_evaluable(self):
        c, exp, results, sr = _run_case(20)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_UNIT_UNCONVERTIBLE
                   for n in r.coverage_gap_notices)

    def test_case21_rounding_before_after_differ(self):
        c, exp, results, sr = _run_case(21)
        by_id = {r.control_point_id: r for r in results}
        assert by_id["CP21-BEFORE"].l1_disposition == L1Disposition.POSITIVE
        assert by_id["CP21-AFTER"].l1_disposition == L1Disposition.NEGATIVE

    def test_case22_retest_in_window_negative_counterevidence(self):
        c, exp, results, sr = _run_case(22)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE
        assert any(ev.polarity == "counterevidence"
                   for ev in results[0].evidence)

    def test_case23_retest_not_satisfied_positive(self):
        c, exp, results, sr = _run_case(23)
        assert results[0].l1_disposition == L1Disposition.POSITIVE

    def test_case24_conflicting_retests_boundary(self):
        c, exp, results, sr = _run_case(24)
        assert results[0].l1_disposition == L1Disposition.BOUNDARY

    def test_case81_retest_outside_window_keeps_positive(self):
        c, exp, results, sr = _run_case(81)
        assert results[0].l1_disposition == L1Disposition.POSITIVE


class TestExceptions:
    """Challenges 25-28."""

    def test_case25_protocol_defined_exception_negative(self):
        c, exp, results, sr = _run_case(25)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE
        assert any(ev.polarity == "counterevidence"
                   for ev in results[0].evidence)

    def test_case26_waiver_wording_not_enough(self):
        c, exp, results, sr = _run_case(26)
        assert results[0].l1_disposition == L1Disposition.POSITIVE

    def test_case27_investigator_judgment_missing_not_evaluable(self):
        c, exp, results, sr = _run_case(27)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_INVESTIGATOR_JUDGMENT_MISSING
                   for n in r.coverage_gap_notices)

    def test_case28_urgent_hazard_context_not_negative(self):
        c, exp, results, sr = _run_case(28)
        assert results[0].l1_disposition == L1Disposition.POSITIVE


class TestProducerRouting:
    """Challenges 29-33, 56, 57, 67, 69."""

    def test_case29_d02_cm_routed_out_zero_d04_units(self):
        c, exp, results, sr = _run_case(29)
        assert exp.count == 0
        assert sr.expected_units == 0
        assert sr.candidate_count == 0 and sr.query_draft_count == 0
        assert len(sr.delegated_control_points) == 1
        assert len(sr.producer_references) == 1

    def test_case30_d02_ambiguous_no_escalation(self):
        c, exp, results, sr = _run_case(30)
        assert sr.expected_units == 0
        assert sr.positive_count == 0

    def test_case31_d03_action_routed_out(self):
        c, exp, results, sr = _run_case(31)
        assert sr.expected_units == 0
        assert sr.candidate_count == 0

    def test_case32_d03_dependency_blocks_d04_unit(self):
        c, exp, results, sr = _run_case(32)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_PRODUCER_DEPENDENCY
                   for n in r.coverage_gap_notices)

    def test_case33_d05_stub_routed(self):
        c, exp, results, sr = _run_case(33)
        assert sr.expected_units == 0
        delegated = sr.delegated_control_points[0]
        assert delegated.owner_domain == p.OWNER_D05
        assert delegated.routing_gap == "d05_stub_not_frozen"

    def test_case56_d02_single_producer_risk(self):
        c, exp, results, sr = _run_case(56)
        assert sr.expected_units == 0
        assert sr.candidate_count == 0 and sr.query_draft_count == 0
        assert len(sr.producer_references) == 1

    def test_case57_d03_single_producer_risk(self):
        c, exp, results, sr = _run_case(57)
        assert sr.expected_units == 0
        assert sr.candidate_count == 0

    def test_case67_owner_competition_single_routing_gate(self):
        c, exp, results, sr = _run_case(67)
        assert exp.count == 1
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert r.evaluation_node_id == p.NODE_ROUTING_GATE
        assert r.signal_type == p.SIGNAL_PROTOCOL_ROUTING

    def test_case69_split_failure_single_routing_gate(self):
        c, exp, results, sr = _run_case(69)
        assert exp.count == 1
        assert results[0].evaluation_node_id == p.NODE_ROUTING_GATE


class TestPackageExpressions:
    """Challenges 8, 9, 58, 72-74, 82."""

    def test_case8_any_and_all_one_unit_each(self):
        c, exp, results, sr = _run_case(8)
        assert exp.count == 2
        by_id = {r.control_point_id: r for r in results}
        assert by_id["CP08-ANY"].l1_disposition == L1Disposition.NEGATIVE
        assert by_id["CP08-ALL"].l1_disposition == L1Disposition.POSITIVE

    def test_case9_component_assessments_outside_expected_set(self):
        c, exp, results, sr = _run_case(9)
        r = results[0]
        assert len(r.component_assessments) == 2
        assert all(a.assessment_id not in exp.unit_ids
                   for a in r.component_assessments)

    def test_case58_determinate_positive_with_gap(self):
        c, exp, results, sr = _run_case(58)
        r = results[0]
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert len(r.r2_candidates) == 1
        assert len(r.query_refs) == 1
        assert r.l0_status == "partial"

    def test_case72_any_one_met_one_ne_negative(self):
        c, exp, results, sr = _run_case(72)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert not r.r2_candidates and not r.query_refs
        assert r.l0_status == "partial"

    def test_case73_all_one_unmet_one_ne_positive(self):
        c, exp, results, sr = _run_case(73)
        r = results[0]
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert len(r.r2_candidates) == 1
        assert "C73a" in r.decisive_component_ids

    def test_case74_at_least_n_three_variants(self):
        c, exp, results, sr = _run_case(74)
        by_id = {r.control_point_id: r for r in results}
        assert by_id["CP74-TRUE"].l1_disposition == L1Disposition.POSITIVE
        assert by_id["CP74-FALSE"].l1_disposition == L1Disposition.NEGATIVE
        assert by_id["CP74-VAR"].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case82_ambiguous_any_all_not_evaluable(self):
        c, exp, results, sr = _run_case(82)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RULE_NOT_VERIFIED
                   for n in r.coverage_gap_notices)


class TestQueryAndGaps:
    """Challenges 43-45, 75, 76."""

    def test_case43_three_part_query_enrolled(self):
        c, exp, results, sr = _run_case(43)
        r = results[0]
        q = r.query_refs[0]
        assert q.basis and q.finding and q.action
        assert "评估是否构成方案偏离" in q.action
        assert q.source_locator_ids

    def test_case44_query_forbids_confirmed_pd(self):
        c, exp, results, sr = _run_case(44)
        for r in results:
            for q in r.query_refs:
                text = q.basis + q.finding + q.action
                for token in ("已确认PD", "重大PD", "已报送", "已关闭"):
                    assert token not in text

    def test_case45_gap_notice_no_query(self):
        c, exp, results, sr = _run_case(45)
        r = results[0]
        assert len(r.coverage_gap_notices) == 1
        assert not r.r2_candidates and not r.query_refs
        assert r.coverage_gap_notices[0].audience_text

    def test_case75_not_enrolled_no_pd_direction(self):
        c, exp, results, sr = _run_case(75)
        q = results[0].query_refs[0]
        assert "评估是否构成方案偏离" not in q.action
        assert "筛选" in (q.action + q.basis)

    def test_case76_unresolved_state_first(self):
        c, exp, results, sr = _run_case(76)
        q = results[0].query_refs[0]
        assert "评估是否构成方案偏离" not in q.action
        assert "资料不足" in (q.basis + q.finding + q.action)


class TestIdentityAndDeterminism:
    """Challenges 46-48, 53, 59, 68."""

    def test_case46_projection_anchors_and_unresolved(self):
        c, exp, results, sr = _run_case(46)
        proj = pp.project_protocol_subject_journey(
            sr, expansions=exp,
            nominal_visits={"CP46-INC": "筛选访视 V1"},
            actual_visits={"CP46-INC": "V1"})
        assert proj.event_count == 1
        ev = proj.events[0]
        assert ev.start == "2026-03-01"
        assert ev.display_label == "筛选期·入选条件待核实"

    def test_case47_join_labels_reachable(self):
        c, exp, results, sr = _run_case(47)
        proj = pp.project_protocol_subject_journey(
            sr, expansions=exp,
            nominal_visits={"CP47-INC": "筛选访视 V1"},
            actual_visits={"CP47-INC": "V1"})
        assert proj.risk_marker_count == 1
        m = proj.risk_markers[0]
        assert m.audience_label == "入选条件待核实"
        assert m.query_ids
        for rec in proj.join.records:
            assert rec.join_reason in p.JOIN_REASONS

    def test_case48_deterministic_rerun(self):
        exp1, results1, exp2, results2 = run_determinism_replay(1)
        assert exp1.unit_ids == exp2.unit_ids
        assert exp1.expected_set_hash == exp2.expected_set_hash
        cand1 = sorted(c.candidate_id
                       for r in results1 for c in r.r2_candidates)
        cand2 = sorted(c.candidate_id
                       for r in results2 for c in r.r2_candidates)
        assert cand1 == cand2

    def test_case53_new_lineage_only_future_runs(self):
        c, exp, results, sr = _run_case(53)
        # check_fn already asserts the lineage isolation; here we assert
        # the identity is stable within the run.
        assert len(set(exp.unit_ids)) == 1

    def test_case59_pipe_ids_distinct(self):
        c, exp, results, sr = _run_case(59)
        r = results[0]
        assert "|" in r.control_point_id
        assert len(set(exp.unit_ids)) == 1
        assert all(a.assessment_id != r.unit_id
                   for a in r.component_assessments)

    def test_case68_two_windows_distinct_identity(self):
        c, exp, results, sr = _run_case(68)
        assert len(exp.unit_ids) == 2
        assert len(set(exp.unit_ids)) == 2
        windows = {r.evaluation_window_id for r in results}
        assert len(windows) == 2


class TestCrossDomainAndRemaining:
    """Challenges 34-42, 63, 79, 80."""

    def test_case34_alternate_source_allowed(self):
        c, exp, results, sr = _run_case(34)
        assert results[0].l1_disposition == L1Disposition.NEGATIVE

    def test_case35_wrong_identity_fails_closed(self):
        c, exp, results, sr = _run_case(35)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case36_cross_domain_wrong_subject_refused(self):
        c, exp, results, sr = _run_case(36)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RELATION_UNCONFIRMED
                   for n in r.coverage_gap_notices)

    def test_case37_partial_date_boundary(self):
        c, exp, results, sr = _run_case(37)
        assert results[0].l1_disposition == L1Disposition.BOUNDARY

    def test_case38_consent_after_procedure_positive(self):
        c, exp, results, sr = _run_case(38)
        r = results[0]
        assert r.positive_subtype == p.SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT

    def test_case39_anchors_not_interchangeable(self):
        c, exp, results, sr = _run_case(39)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case40_ie_dv_semantics_separate(self):
        c, exp, results, sr = _run_case(40)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_FREE_TEXT_ONLY
                   for n in r.coverage_gap_notices)

    def test_case41_discontinuation_inconsistent_positive(self):
        c, exp, results, sr = _run_case(41)
        r = results[0]
        assert r.positive_subtype == \
            p.SUBTYPE_DISCONTINUATION_INCONSISTENT
        assert r.audience_label == "退出或终止参与标准待核实"

    def test_case42_discontinuation_missing_input_not_evaluable(self):
        c, exp, results, sr = _run_case(42)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case63_unconfirmed_relation_refused(self):
        c, exp, results, sr = _run_case(63)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_EVIDENCE_IDENTITY_UNCONFIRMED
                   for n in r.coverage_gap_notices)

    def test_case79_cm_fact_d04_risk_domain(self):
        c, exp, results, sr = _run_case(79)
        r = results[0]
        assert r.positive_subtype == p.SUBTYPE_EXCLUSION_PRESENT
        assert all(cand.detail.get("domain") == p.D04_DOMAIN
                   for cand in r.r2_candidates)
        assert sr.candidate_count == 1

    def test_case80_age_algorithm_unfrozen_not_evaluable(self):
        c, exp, results, sr = _run_case(80)
        r = results[0]
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_AGE_ALGORITHM_UNFROZEN
                   for n in r.coverage_gap_notices)


# ===========================================================================
# Golden hashes
# ===========================================================================

class TestGoldenHashes:
    """Frozen golden unit/component/expected-set/candidate/payload hashes
    recompute equal (deterministic identities, challenges 48/59/60/68/83)."""

    def test_golden_hashes_are_frozen_and_nonempty(self):
        assert GOLDEN_EXPECTED_SET_HASH
        assert GOLDEN_UNIT_IDS
        assert GOLDEN_PROJECTION_PAYLOAD_HASH
        for number, unit_ids in GOLDEN_UNIT_IDS.items():
            assert unit_ids
            assert len(set(unit_ids)) == len(unit_ids)

    def test_golden_expected_set_hashes_recompute(self):
        m = build_protocol_challenge_matrix()
        for number, frozen in GOLDEN_EXPECTED_SET_HASH.items():
            case = m.by_number(number)
            exp, _ = case.build()
            assert exp.expected_set_hash == frozen, (
                f"case {number} expected-set hash drifted")

    def test_golden_unit_ids_recompute(self):
        m = build_protocol_challenge_matrix()
        for number, frozen in GOLDEN_UNIT_IDS.items():
            case = m.by_number(number)
            exp, _ = case.build()
            assert tuple(exp.unit_ids) == frozen, (
                f"case {number} unit ids drifted")

    def test_golden_component_assessment_ids_recompute(self):
        m = build_protocol_challenge_matrix()
        for number, frozen in GOLDEN_COMPONENT_ASSESSMENT_IDS.items():
            case = m.by_number(number)
            _, results = case.build()
            actual = sorted({
                a.assessment_id
                for r in results for a in r.component_assessments})
            assert tuple(actual) == frozen, (
                f"case {number} component assessment ids drifted")

    def test_golden_candidate_ids_recompute(self):
        m = build_protocol_challenge_matrix()
        for number, frozen in GOLDEN_CANDIDATE_IDS.items():
            case = m.by_number(number)
            _, results = case.build()
            actual = sorted({
                c.candidate_id for r in results for c in r.r2_candidates})
            assert tuple(actual) == frozen, (
                f"case {number} candidate ids drifted")

    def test_golden_projection_payload_hashes_recompute(self):
        from mm_r4.contracts import content_hash
        m = build_protocol_challenge_matrix()
        for number, frozen in GOLDEN_PROJECTION_PAYLOAD_HASH.items():
            case = m.by_number(number)
            sr, exp = case.build_slice()
            proj = pp.project_protocol_subject_journey(
                sr, expansions=exp,
                producer_references=sr.producer_references)
            actual = content_hash(proj.canonical_payload())
            assert actual == frozen, (
                f"case {number} projection payload hash drifted")

    def test_gate_hash_order_independent(self):
        """Challenges 60/83: applicability-gate expected-set hashes and
        unit ids are identical for reversed feasible fingerprints."""
        c60 = build_protocol_challenge_matrix().by_number(60)
        c83 = build_protocol_challenge_matrix().by_number(83)
        for c in (c60, c83):
            exp1, _ = c.build()
            # Reversed fingerprint order.
            rev = _reversed_applicability(c)
            exp_rev = p.expand_protocol_expected_set(
                project_id=PROJECT_ID, applicability=rev,
                control_points=tuple(c.build_control_points()),
                plan=_case_plan(c))
            assert exp1.unit_ids == exp_rev.unit_ids
            assert exp1.expected_set_hash == exp_rev.expected_set_hash


# ===========================================================================
# Count invariants
# ===========================================================================

class TestCountInvariants:
    """Frozen §11: expected = five L1 buckets; counts stay separate."""

    def test_slice_count_equation_holds_for_every_executable_case(self):
        m = build_protocol_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            sr, _ = c.build_slice()
            sr.verify_count_invariants()
            total = (sr.positive_count + sr.negative_count
                     + sr.boundary_count + sr.not_applicable_count
                     + sr.not_evaluable_count)
            assert total == sr.expected_units == len(sr.unit_results)

    def test_query_count_never_feeds_risk_count(self):
        for number in (1, 3, 16, 38, 41):
            _, _, results, sr = _run_case(number)
            assert sr.candidate_count >= sr.query_draft_count
            for r in results:
                if r.l1_disposition == L1Disposition.NOT_EVALUABLE:
                    assert not r.r2_candidates and not r.query_refs

    def test_positive_units_each_carry_at_most_one_candidate_query(self):
        m = build_protocol_challenge_matrix()
        for c in m.cases:
            if c.adjacent_test:
                continue
            _, results = c.build()
            for r in results:
                if r.l1_disposition == L1Disposition.POSITIVE:
                    assert len(r.r2_candidates) <= 1
                    assert len(r.query_refs) <= 1
                if r.l1_disposition == L1Disposition.NEGATIVE:
                    assert not r.r2_candidates


# ===========================================================================
# Adjacent regression surface
# ===========================================================================

class TestAdjacentRegressionSurface:
    """Challenge 55: the adjacent suites stay green; the D01-D03 fixtures
    still evaluate (the shared root package stays regression-free)."""

    def test_d01_fixture_still_evaluates(self):
        from mm_r4.fixtures import (
            evaluate as d01_evaluate, build_challenge_matrix,
        )
        case = next(
            c for c in build_challenge_matrix().cases
            if c.name == "positive_suspected_under_report")
        ur = d01_evaluate(list(case.records))
        assert ur.l1_disposition == L1Disposition.POSITIVE

    def test_d02_matrix_still_builds(self):
        from mm_r4.cm_fixtures import build_cm_challenge_matrix
        m = build_cm_challenge_matrix()
        assert m.case_count >= 1

    def test_d03_matrix_still_builds(self):
        from mm_r4.ip_fixtures import build_ip_challenge_matrix
        m = build_ip_challenge_matrix()
        assert m.case_count == 51

    def test_protocol_root_exports_object_identical(self):
        import mm_r4
        from mm_r4 import contracts, protocol, protocol_fixtures, \
            protocol_projection
        assert mm_r4.ProtocolSliceResult is protocol.ProtocolSliceResult
        assert (mm_r4.ProtocolJourneyEvent is
                protocol.ProtocolJourneyEvent)
        assert (mm_r4.ProtocolEventMarkerJoinIndex is
                protocol_projection.ProtocolEventMarkerJoinIndex)
        assert (mm_r4.ProtocolChallengeMatrix is
                protocol_fixtures.ProtocolChallengeMatrix)
        assert mm_r4.build_protocol_challenge_matrix is \
            protocol_fixtures.build_protocol_challenge_matrix
        assert mm_r4.evaluate_protocol_slice is protocol.evaluate_protocol_slice
        # Corrective 01: frozen shared candidate flag readers + D04
        # evidence-requirement builders reach the root un-aliased.
        assert (mm_r4.candidate_rights_or_safety_critical is
                contracts.candidate_rights_or_safety_critical)
        assert (mm_r4.candidate_machine_close_forbidden is
                contracts.candidate_machine_close_forbidden)
        assert (mm_r4.build_rule_evidence_requirement is
                protocol.build_rule_evidence_requirement)
        assert (mm_r4.expand_rule_evidence_requirements is
                protocol.expand_rule_evidence_requirements)
        assert mm_r4.policy_content_hash_value is \
            protocol.policy_content_hash_value

    def test_protocol_public_all_declares_d04_surface(self):
        import mm_r4
        for name in (
            "candidate_rights_or_safety_critical",
            "candidate_machine_close_forbidden",
            "build_rule_evidence_requirement",
            "expand_rule_evidence_requirements",
            "policy_content_hash_value",
        ):
            assert name in mm_r4.__all__, name
            assert getattr(mm_r4, name) is not None, name


# ===========================================================================
# Helpers
# ===========================================================================

def _reversed_applicability(case: ProtocolChallengeCase):
    from mm_r4.protocol_fixtures import make_applicability
    appl = case.build_applicability()
    fps = tuple(reversed(appl.feasible_version_fingerprints))
    return make_applicability(
        status=appl.decision_status, fingerprints=fps)


def _case_plan(case: ProtocolChallengeCase):
    plan = case.build_plan()
    if not plan:
        from mm_r4.protocol_fixtures import make_plan
        plan = make_plan(
            root_ids=tuple(cp.control_point_id
                           for cp in case.build_control_points()))
    return plan
