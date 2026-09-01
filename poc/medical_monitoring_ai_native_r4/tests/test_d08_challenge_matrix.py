"""R4-D08 233-case frozen oracle challenge matrix through the runtime.

Every catalog case is parsed by the test-only adapter into typed objects,
evaluated by the runtime, projected, and the assembled leaves are compared
EXACTLY (per key, all three leaf sets) against the pinned oracle entry.
No oracle leaf can escape: missing, extra and unequal keys are all
discrepancies.

Also covers:

* family floors (>= 200 cases, every owned family covers all five
  dispositions, consume-only zero-risk);
* the cutoff oracle essentials (zero medical units for all-out-of-cutoff,
  exactly one boundary gate for mixed/spans, not-found positive,
  time-missing priority, propagation retention);
* temporal oracle essentials (contains x contained_by -> positive,
  overlap never satisfies containment, timezone_incomparable primary
  reason);
* n-ary RELID single unit and fanout gate;
* every runtime-produced Query draft validates against the audience
  lexicon.
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
from test_d08_adapter import (  # noqa: E402
    audit_case,
    load_artifacts,
    run_case,
)
from mm_r4.d08_projection import (  # noqa: E402
    build_d08_query_draft,
    validate_query_draft,
)

DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")

FAMILY_FLOORS = {
    "anti_overfit": 12,
    "consume_only_adjacency": 16,
    "correction_propagation_matrix": 24,
    "cutoff_matrix": 9,
    "d08_explicit_link_resolve": 12,
    "d08_identity_collision": 12,
    "d08_propagation_lineage": 15,
    "d08_reverse_cardinality": 12,
    "d08_unowned_temporal_impossibility": 12,
    "fanout_gate": 4,
    "identity_duplicate_matrix": 20,
    "integrity_coverage": 20,
    "query_journey_audience": 16,
    "raw_materialized_bijection": 12,
    "replay_drift": 4,
    "special_floors": 13,
    "temporal_matrix": 20,
}


def _indexed() -> tuple:
    catalog, oracle, registry = load_artifacts()
    cases = {c["case_id"]: c for c in catalog["cases"]}
    expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
    return catalog, oracle, registry, cases, expectations


class TestChallengeMatrix(unittest.TestCase):
    """Exact 233-case oracle match through the typed runtime."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._catalog, cls._oracle, cls._registry, cls._cases, cls._exps = _indexed()

    def test_all_233_cases_match_exact_oracle_leaves(self) -> None:
        failures: dict = {}
        for cid in sorted(self._cases):
            problems = audit_case(self._cases[cid], self._exps[cid])
            if problems:
                failures[cid] = problems
        self.assertEqual(
            failures, {},
            f"runtime diverged from the pinned oracle on {len(failures)} cases: "
            f"{list(failures)[:5]}")

    def test_leaf_coverage_floor(self) -> None:
        """The oracle covers every leaf class with materialized cases."""
        counts = Counter()
        for e in self._oracle["ordered_expectations"]:
            counts["expected_leaf_set"] += len(e["expected_leaf_set"])
            counts["expected_trace_leaf_set"] += len(e["expected_trace_leaf_set"])
            counts["expected_source_leaf_set"] += len(e["expected_source_leaf_set"])
        self.assertEqual(sum(counts.values()), 16881)
        self.assertGreaterEqual(counts["expected_leaf_set"], 233 * 30)
        self.assertGreaterEqual(counts["expected_trace_leaf_set"], 233 * 10)
        self.assertGreaterEqual(counts["expected_source_leaf_set"], 233 * 13)

    def test_family_floors_and_disposition_coverage(self) -> None:
        by_family = Counter(c["family_id"] for c in self._catalog["cases"])
        self.assertEqual(sum(by_family.values()), 233)
        for family, floor in FAMILY_FLOORS.items():
            self.assertGreaterEqual(by_family.get(family, 0), floor, family)
        for family in ("d08_explicit_link_resolve", "d08_reverse_cardinality",
                       "d08_identity_collision", "d08_unowned_temporal_impossibility",
                       "d08_propagation_lineage"):
            disps = {c["disposition"] for c in self._catalog["cases"]
                     if c["family_id"] == family}
            self.assertEqual(disps, set(DISPOSITIONS), family)

    def test_consume_only_zero_risk(self) -> None:
        count = 0
        for cid, case in self._cases.items():
            if case["family_id"] != "consume_only_adjacency":
                continue
            count += 1
            ls = self._exps[cid]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 0)
            self.assertEqual(ls["l2.risk_count"], 0)
            self.assertEqual(ls["l2.query_count"], 0)
            self.assertEqual(ls["l2.clue_count"], 0)
            self.assertEqual(ls["ownership.d08_action"], "consume_only")
        self.assertGreaterEqual(count, 14)

    def test_cutoff_oracle_essentials(self) -> None:
        # all-out-of-cutoff -> zero medical units
        self.assertEqual(self._exps["D08-CASE-200"]["expected_leaf_set"]["unit_count"], 0)
        # mixed membership -> exactly one cutoff boundary gate
        for cid in ("D08-CASE-201", "D08-CASE-202"):
            ls = self._exps[cid]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 1)
            self.assertEqual(ls["gate_count"], 1)
            self.assertEqual(ls["units.0.gate_signal_type"], "cutoff_boundary_gate")
            self.assertEqual(ls["units.0.l1_disposition"], "boundary")
            self.assertEqual(ls["units.0.unit_kind"], "routing_or_coverage_gate")
        # in-cutoff / covered / zero-match -> not-found positive
        ls = self._exps["D08-CASE-203"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        self.assertEqual(ls["units.0.resolve_status"], "not_found")
        # time-missing + mixed -> exactly one not_evaluable, no gate
        ls = self._exps["D08-CASE-204"]["expected_leaf_set"]
        self.assertEqual(ls["unit_count"], 1)
        self.assertEqual(ls["gate_count"], 0)
        self.assertEqual(ls["units.0.l1_disposition"], "not_evaluable")
        # propagation retained after in->out correction (positive) and
        # in-cutoff event with post-cutoff source revision (negative)
        self.assertEqual(
            self._exps["D08-CASE-205"]["expected_leaf_set"]["units.0.l1_disposition"],
            "positive")
        self.assertEqual(
            self._exps["D08-CASE-206"]["expected_leaf_set"]["units.0.l1_disposition"],
            "negative")

    def test_temporal_oracle_essentials(self) -> None:
        # expected contains, observed contained_by -> positive
        ls = self._exps["D08-CASE-046"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        self.assertEqual(ls["units.0.temporal_relation"], "contained_by")
        self.assertEqual(ls["units.0.primary_reason"], "observed_contained_by")
        # expected contains, observed contains -> negative (allowed)
        ls = self._exps["D08-CASE-092"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "negative")
        # expected before, observed after -> positive
        ls = self._exps["D08-CASE-081"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        # same-day points without time -> indeterminate boundary
        ls = self._exps["D08-CASE-082"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "boundary")
        self.assertEqual(ls["units.0.temporal_relation"], "indeterminate")
        # timezone + precision both missing -> timezone_incomparable primary
        tz_cases = [e for e in self._oracle["ordered_expectations"]
                    if e["expected_leaf_set"].get("units.0.primary_reason")
                    == "timezone_incomparable"]
        self.assertTrue(tz_cases)
        for e in tz_cases:
            self.assertEqual(e["expected_leaf_set"]["units.0.l1_disposition"],
                             "not_evaluable")

    def test_fanout_gate(self) -> None:
        ls = self._exps["D08-CASE-196"]["expected_leaf_set"]
        self.assertEqual(ls["unit_count"], 1)
        self.assertEqual(ls["units.0.gate_signal_type"], "identity_fanout_exceeded")
        self.assertEqual(ls["units.0.l1_disposition"], "not_evaluable")
        self.assertEqual(ls["units.0.unit_kind"], "routing_or_coverage_gate")

    def test_nary_relid_single_unit(self) -> None:
        nary = [c for c in self._catalog["cases"]
                if any(len(m.get("member_ids") or []) >= 3
                       for m in c["typed_input"]["rel_instance_memberships"])]
        self.assertTrue(nary, "no N-ary RELID case materialized")
        for case in nary:
            ls = self._exps[case["case_id"]]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 1)
            self.assertEqual(ls["units.0.unit_kind"], "per_explicit_rel_instance")

    def test_runtime_query_drafts_all_validate(self) -> None:
        """Every D08-owned positive with a projectable payload yields a
        lexicon-valid three-part Query draft (依据/发现/行动项, no PD)."""
        checked = 0
        for cid in sorted(self._cases):
            case = self._cases[cid]
            typed, result, _ = run_case(case)
            ls = self._exps[cid]["expected_leaf_set"]
            if not (result.risk_candidate_present and result.projectable_node_set):
                self.assertIsNone(build_d08_query_draft(typed, result),
                                  f"{cid} must not project a query")
                continue
            draft = build_d08_query_draft(typed, result)
            self.assertIsNotNone(draft, cid)
            assert draft is not None
            validation = validate_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"], f"{cid}: {validation['reasons']}")
            self.assertEqual(ls["ownership.query_draft_present"], True)
            self.assertEqual(ls["l2.query_count"], 1)
            checked += 1
        self.assertGreaterEqual(checked, 60)

    def test_integrity_failures_project_no_risk_or_query(self) -> None:
        for cid in sorted(self._cases):
            ls = self._exps[cid]["expected_leaf_set"]
            if ls["integrity.stage"] != "integrity_error":
                continue
            self.assertEqual(ls["unit_count"], 0)
            self.assertEqual(ls["l2.risk_count"], 0)
            self.assertEqual(ls["l2.query_count"], 0)
            self.assertEqual(ls["l2.clue_count"], 0)


if __name__ == "__main__":
    unittest.main()
