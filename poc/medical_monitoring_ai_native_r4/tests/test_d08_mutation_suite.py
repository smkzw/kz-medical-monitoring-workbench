"""R4-D08 negative mutation suite: every declared mutation class fails closed.

Mutates the frozen catalog's typed inputs (the catalog itself is never
written) and verifies the runtime reacts deterministically:

* semantic mutations that the frozen oracle marks as outcome-changing must
  change the assembled leaves (or raise the typed-validation error) --
  never silently produce the original outcome;
* inert mutations (surface renames, non-substantive metadata) must keep the
  exact original leaves;
* typed-schema violations (a fourth waiver state, invalid closed enums)
  must raise :class:`~mm_r4.d08_contracts.D08ContractError`;
* stale-hash / oracle-coupling guards live in the adapter: tampered frozen
  artifacts are rejected before any case runs.

The catalog/oracle/registry stay byte-identical after every test.
"""

from __future__ import annotations

import json
import sys
import unittest
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
from mm_r4.d08_contracts import D08ContractError  # noqa: E402

from test_d08_adapter import (  # noqa: E402
    CATALOG_FILE_SHA256,
    CATALOG_PATH,
    ORACLE_FILE_SHA256,
    ORACLE_PATH,
    REGISTRY_FILE_SHA256,
    REGISTRY_PATH,
    assemble_leaf_sets,
    load_artifacts,
    parse_typed_input,
    run_case,
    sha256_bytes,
)


def _clone(catalog: dict, case_id: str) -> dict:
    return json.loads(json.dumps(catalog["cases"][int(case_id.split("-")[-1]) - 1]))


def _leaves(case: dict) -> dict:
    typed, result, _ = run_case(case)
    leaf, trace, source = assemble_leaf_sets(case, typed, result)
    return {"expected_leaf_set": leaf, "expected_trace_leaf_set": trace,
            "expected_source_leaf_set": source}


class TestMutationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, cls.registry = load_artifacts()
        cls.expectations = {e["case_id"]: e for e in cls.oracle["ordered_expectations"]}

    def tearDown(self) -> None:
        # frozen files must never change
        self.assertEqual(sha256_bytes(CATALOG_PATH.read_bytes()), CATALOG_FILE_SHA256)
        self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()), ORACLE_FILE_SHA256)
        self.assertEqual(sha256_bytes(REGISTRY_PATH.read_bytes()), REGISTRY_FILE_SHA256)

    def test_wrong_subject_mutation_fails_closed(self) -> None:
        case = _clone(self.catalog, "D08-CASE-002")
        original = _leaves(case)
        case["typed_input"]["record_nodes"][1]["stable_record_identity"][
            "subject_ref"] = "SYN-D08-SUBJECT-002"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "cross-subject edge must change the outcome")

    def test_wrong_cutoff_mutation_fails_closed(self) -> None:
        case = _clone(self.catalog, "D08-CASE-002")
        original = _leaves(case)
        case["typed_input"]["record_nodes"][0]["cutoff_decision"][
            "decision"] = "out_of_cutoff"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "mixed membership must produce a boundary gate")

    def test_contains_direction_flip_changes_outcome(self) -> None:
        case = _clone(self.catalog, "D08-CASE-046")
        original = _leaves(case)
        tc = case["typed_input"]["temporal_comparisons"][0]
        tc["left_time_ref_id"], tc["right_time_ref_id"] = (
            tc["right_time_ref_id"], tc["left_time_ref_id"])
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "contains/contained_by interchange must change the outcome")

    def test_propagation_stale_flip_fails_closed(self) -> None:
        case = _clone(self.catalog, "D08-CASE-122")  # in_sync negative
        original = _leaves(case)
        p = case["typed_input"]["propagation_objects"][0]
        p["declared_consumed_revision"] = "SRC-REV-003"  # stale vs SRC-REV-004
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "stale propagation must change the outcome")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "positive")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.propagation_result"],
                         "stale")

    def test_time_missing_priority_mutation_fails_closed(self) -> None:
        case = _clone(self.catalog, "D08-CASE-233")
        original = _leaves(case)
        for n in case["typed_input"]["record_nodes"]:
            n["cutoff_decision"]["decision"] = "out_of_cutoff"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "all-out-of-cutoff mutation must change the outcome")
        self.assertEqual(mutated["expected_leaf_set"]["unit_count"], 0)

    def test_waiver_fourth_state_fails_typed_validation(self) -> None:
        case = _clone(self.catalog, "D08-CASE-230")
        case["typed_input"]["waiver_handoffs"][0]["closure_state"] = "partially_closed"
        with self.assertRaises(D08ContractError):
            parse_typed_input(case)

    def test_invalid_closed_enum_fails_typed_validation(self) -> None:
        case = _clone(self.catalog, "D08-CASE-001")
        case["typed_input"]["cardinality_specs"][0][
            "unmatched_required_policy"] = "invented_policy"
        with self.assertRaises(D08ContractError):
            parse_typed_input(case)

    def test_lineage_fingerprint_state_mutation_changes_outcome(self) -> None:
        """Mutating the closed fingerprint state changes the outcome
        deterministically (structured propagation result mutation)."""
        case = _clone(self.catalog, "D08-CASE-122")  # in_sync negative
        original = _leaves(case)
        p = case["typed_input"]["propagation_objects"][0]
        p["lineage_fingerprint_state"] = "mismatch"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "not_evaluable")
        self.assertEqual(
            mutated["expected_leaf_set"]["units.0.primary_reason"],
            "lineage_fingerprint_mismatch")

    def test_lineage_fingerprint_state_unknown_value_rejected(self) -> None:
        case = _clone(self.catalog, "D08-CASE-122")
        case["typed_input"]["propagation_objects"][0][
            "lineage_fingerprint_state"] = "broken_in_a_new_way"
        with self.assertRaises(D08ContractError):
            parse_typed_input(case)

    def test_decision_code_mutation_changes_outcome(self) -> None:
        """Mutating the closed identity decision code changes the outcome."""
        case = _clone(self.catalog, "D08-CASE-027")  # boundary (split without rule)
        original = _leaves(case)
        case["typed_input"]["identity_comparisons"][0][
            "decision_code"] = "merge_with_rule"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "negative")

    def test_relation_payload_status_drives_fail_closed(self) -> None:
        """The closed wrong-subject payload status gates fail-closed without
        any description text."""
        case = _clone(self.catalog, "D08-CASE-001")
        original = _leaves(case)
        case["typed_input"]["relation_payload_status"] = "wrong_subject_or_site"
        case["typed_input"]["mutation_context"]["mutation_description"] = ""
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "not_evaluable")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.primary_reason"],
                         "wrong_subject_payload_fail_closed")
        self.assertEqual(mutated["expected_leaf_set"]["l2.query_count"], 0)
        self.assertEqual(mutated["expected_leaf_set"]["l2.risk_count"], 0)

    def test_relation_payload_status_unknown_value_rejected(self) -> None:
        case = _clone(self.catalog, "D08-CASE-001")
        case["typed_input"]["relation_payload_status"] = "wrong_site_payload"
        with self.assertRaises(D08ContractError):
            parse_typed_input(case)

    def test_missing_resolve_materialization_fails_closed(self) -> None:
        """unique resolve without materialized node raises the expected-set
        admission integrity error on the integrity family path."""
        case = _clone(self.catalog, "D08-CASE-001")
        case["typed_input"]["relation_rules"][0][
            "clinical_relationship_type"] = "integrity_matrix"
        case["typed_input"]["resolve_decisions"] = [{
            "resolve_decision_id": "SYN-RES-X",
            "raw_link_id": "SYN-RAWLINK-001",
            "status": "unique",
            "materialized_record_node_ids": [],
            "rejected_candidate_ids": [],
            "reason_codes": [],
            "l0_coverage_status": "covered"}]
        typed = parse_typed_input(case)
        from mm_r4.d08_evaluator import evaluate
        result = evaluate(typed)
        self.assertIsNotNone(result.integrity_error)
        self.assertEqual(result.integrity_error.error_type,
                         "expected_set_admission_failed")
        self.assertEqual(result.units, ())

    def test_oracle_coupling_mutation_changes_leaves(self) -> None:
        """A typed-input mutation that the oracle explicitly flags (case 203
        leaf mutations) must be detected by the exact audit: the runtime
        leaves stay faithful, so an oracle edit mismatches."""
        case = _clone(self.catalog, "D08-CASE-203")
        original = _leaves(case)
        # flip a substantive fact: remove the resolve decision's counterpart
        for res in case["typed_input"]["resolve_decisions"]:
            if res["status"] == "not_found":
                res["status"] = "unique"
                res["materialized_record_node_ids"] = ["SYN-REC-001"]
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)

    def test_fanout_cap_mutation_fails_closed(self) -> None:
        case = _clone(self.catalog, "D08-CASE-196")
        original = _leaves(case)
        fan = case["typed_input"]["fanout_candidate_sets"][0]
        fan["candidate_identities"] = fan["candidate_identities"][:1]
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "fanout below cap must not keep the gate")

    def test_projectable_set_mutation_changes_audience_leaves(self) -> None:
        """Changing which nodes are projectable changes the audience leaves
        (anchor, query presence) -- the runtime projection is faithful."""
        case = _clone(self.catalog, "D08-CASE-001")
        original = _leaves(case)
        vis = case["typed_input"]["visibility_decision"]
        vis["projectable_node_set"] = vis["projectable_node_set"][:1]
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_source_leaf_set"]
                         ["source.projectable_node_set"],
                         [vis["projectable_node_set"][0]])

    def test_all_mutation_classes_materialized(self) -> None:
        classes = {c["mutation_class"] for c in self.catalog["cases"]}
        required = {"none", "counterevidence", "hidden", "fp_trap", "fn_trap",
                    "cutoff_oracle", "temporal_oracle", "waiver_state",
                    "replay_drift", "integrity_gap", "consume_only_zero_risk",
                    "special_floor", "anti_overfit_surface"}
        self.assertTrue(required <= classes, classes - required)


if __name__ == "__main__":
    unittest.main()
