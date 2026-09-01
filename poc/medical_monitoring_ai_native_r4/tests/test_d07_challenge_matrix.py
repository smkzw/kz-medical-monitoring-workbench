"""R4-D07 frozen 144-case challenge matrix runner (worker-02 slice).

Drives every frozen case (001..144) through the real D07 runtime entrypoint
``mm_r4.d07_safety_evaluator.evaluate_safety`` using the frozen typed inputs,
then verifies, per case:

* frozen artifact identity: catalog / oracle / registry schema, contract
  semantic hash, registry cross hashes, five-way bijection columns, and the
  per-case ``substantive_input_hash`` equality chain
  (runtime canonical JSON == catalog == registry);
* exact leaf bijection against the independent oracle: the flattened runtime
  raw root must equal ``expected_leaf_set`` + ``expected_trace_leaf_set`` +
  ``expected_source_leaf_set`` with no extra (beyond the documented root
  synthetic leaves) and no missing leaves, and every value must be equal
  (v0.4 §14.1: 额外或缺失均失败);
* the frozen closed-DSL assertion program: re-compiled from oracle leaves via
  the frozen generator, its hash must reproduce the registry
  ``assertion_program_hash``, and every clause must hold against the runtime
  output (including the ``error_equals`` pin on the 11 integrity cases);
* fail-closed guarantee on the 11 integrity-error cases: a pre-evaluator
  integrity error is emitted and no medical/priority/risk/Query/Journey
  leaves exist;
* runtime closure: the runtime source never reads the frozen artifacts and
  never branches on case/test/fixture identifiers (static AST audit).

The runtime never reads the oracle / manifest / registry; expected outcomes
stay strictly test-side.  All data is synthetic and offline.
"""

from __future__ import annotations

import ast
import sys
from functools import lru_cache
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.d07_fixtures import (  # noqa: E402
    ENTRYPOINT,
    EXPECTED_CASE_COUNT,
    ROOT_SYNTHETIC_LEAVES,
    build_indexes,
    compile_frozen_program,
    content_hash,
    exact_leaf_check,
    fail_closed_root,
    flatten_root,
    interpret_program,
    validate_program_structure,
)
from mm_r4.d07_safety_evaluator import evaluate_safety  # noqa: E402

IDX = build_indexes()
CATALOG = IDX["frozen_catalog"]
OVERLAY_CATALOG = IDX["overlay_catalog"]
ORACLE = IDX["oracle"]
REGISTRY = IDX["registry"]
CASES = IDX["overlay_cases_by_id"]
FROZEN_CASES = IDX["frozen_cases_by_id"]
EXPECTATIONS = IDX["expectations_by_id"]
REGISTRY_CORE = IDX["registry_core"]
FROZEN_SUBSTANTIVE_HASHES = IDX["frozen_substantive_hashes"]
OVERLAY_SUBSTANTIVE_HASHES = IDX["overlay_substantive_hashes"]

# Frozen row distribution (v0.4 §14 table).
EXPECTED_DISTRIBUTION = {
    "disposition_applicability": 12,
    "unit_and_range": 16,
    "baseline_and_trend": 16,
    "grade": 16,
    "cs_ncs_and_sample_quality": 14,
    "followup_and_handoff": 18,
    "organ_pattern": 14,
    "examination": 12,
    "identity_version_hash": 10,
    "query_journey": 8,
    "lifecycle_aggregation": 8,
}

# The 11 deliberately defective cases (their oracle pins the exact class).
INTEGRITY_CASES = frozenset(
    {"028", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128"}
)


def _case_ids():
    return [f"case-{n:03d}" for n in range(1, EXPECTED_CASE_COUNT + 1)]


def _case_numbers():
    return list(range(1, EXPECTED_CASE_COUNT + 1))


def _case_id(number: int) -> str:
    return f"{number:03d}"


# ===========================================================================
# Frozen artifact identity and matrix structure
# ===========================================================================


class TestMatrixStructure:
    def test_matrix_has_exactly_144_contiguous_cases(self):
        assert CATALOG["case_count"] == EXPECTED_CASE_COUNT
        assert len(CATALOG["ordered_cases"]) == EXPECTED_CASE_COUNT
        assert list(CASES) == [f"{n:03d}" for n in range(1, 145)]
        assert list(EXPECTATIONS) == list(CASES)

    def test_all_entrypoints_are_the_frozen_single_entrypoint(self):
        assert {case["entrypoint"] for case in CATALOG["ordered_cases"]} == {ENTRYPOINT}
        assert {row["entrypoint"] for row in REGISTRY["ordered_registry_core"]} == {ENTRYPOINT}

    def test_row_distribution_matches_frozen_contract(self):
        distribution = REGISTRY["bijection_audit"]["row_distribution"]
        assert distribution == EXPECTED_DISTRIBUTION
        assert sum(distribution.values()) == EXPECTED_CASE_COUNT

    def test_registry_bijection_audit_flags(self):
        audit = REGISTRY["bijection_audit"]
        assert audit["five_way_bijection_passed"] is True
        assert audit["row_distribution_passed"] is True
        assert audit["case_count"] == EXPECTED_CASE_COUNT
        assert audit["integrity_error_case_count"] == len(INTEGRITY_CASES)
        assert audit["duplicate_substantive_input_groups"] == 0
        for column, unique in audit["column_uniqueness"].items():
            assert unique is True, column

    def test_integrity_error_cases_are_exactly_the_frozen_11(self):
        pinned = {
            e["case_id"]
            for e in ORACLE["ordered_expectations"]
            if e.get("expected_integrity_error") is not None
        }
        assert pinned == INTEGRITY_CASES

    def test_static_vocabulary_independence(self):
        """Catalog typed inputs carry no outcome-vocabulary keys and the oracle
        leaf paths never address typed-input sections (disjoint vocabulary)."""
        typed_sections = set(CATALOG["ordered_cases"][0]["typed_input"])
        outcome_prefixes = {
            "integrity.", "units.", "ownership.", "lifecycle.", "trace.",
            "source.", "coverage.", "journey.", "query.",
        }
        for case in CATALOG["ordered_cases"]:
            assert set(case["typed_input"]) == typed_sections
            for section in typed_sections:
                assert section not in outcome_prefixes, section
        for expectation in ORACLE["ordered_expectations"]:
            for leaf_set in ("expected_leaf_set", "expected_trace_leaf_set",
                             "expected_source_leaf_set"):
                for path in expectation[leaf_set]:
                    head = path.split(".", 1)[0]
                    assert head not in typed_sections, (
                        f"{expectation['case_id']} oracle path {path!r} addresses "
                        f"typed-input section {head!r}"
                    )


class TestArtifactIdentity:
    def test_all_cases_carry_frozen_mutation_ids(self):
        for case in CATALOG["ordered_cases"]:
            assert case["positive_mutation_ids"], case["case_id"]
            assert case["negative_mutation_ids"], case["case_id"]
            for mid in case["positive_mutation_ids"] + case["negative_mutation_ids"]:
                assert mid.startswith(("P-", "N-")), (case["case_id"], mid)

    def test_per_case_expected_leaf_set_hash_matches_registry(self):
        for case_id in CASES:
            expectation = EXPECTATIONS[case_id]
            leaf_hash = content_hash(expectation["expected_leaf_set"])
            assert leaf_hash == REGISTRY_CORE[case_id]["expected_leaf_set_hash"], case_id

    @pytest.mark.parametrize("number", _case_numbers(), ids=_case_ids())
    def test_frozen_program_hash_matches_registry(self, number):
        case_id = _case_id(number)
        program, program_hash = compile_frozen_program(EXPECTATIONS[case_id], ORACLE)
        assert program_hash == REGISTRY_CORE[case_id]["assertion_program_hash"], case_id
        assert program, case_id


class TestFrozenOverlaySeparation:
    """The frozen catalog view stays immutable; the synthetic overlay is a
    deep copy with its own substantive hashes (never masquerading as frozen)."""

    def test_catalog_key_is_frozen_not_overlay(self):
        assert IDX["catalog"] is IDX["frozen_catalog"]
        assert IDX["catalog"] is not IDX["overlay_catalog"]
        assert IDX["cases_by_id"] is IDX["overlay_cases_by_id"]
        assert IDX["cases_by_id"] is not IDX["frozen_cases_by_id"]

    def test_frozen_catalog_carries_no_injected_fields(self):
        for case in CATALOG["ordered_cases"]:
            for rule in case["typed_input"].get("baseline_rules", []):
                assert "baseline_confirmation_relative_deviation" not in rule
            for rule in case["typed_input"].get("priority_precedence_rules", []):
                assert "safety_critical_ratio_threshold" not in rule

    def test_overlay_carries_injected_fields(self):
        for case_id, case in CASES.items():
            for rule in case["typed_input"].get("baseline_rules", []):
                assert rule.get("baseline_confirmation_relative_deviation") == "0.02"
            flag = (case["typed_input"].get("priority_policy") or {}).get(
                "high_priority_clinical_flag_rules") or []
            for rule in case["typed_input"].get("priority_precedence_rules", []):
                if rule.get("trigger") == "high_priority_clinical_flag" \
                        and rule.get("precedence_rule_id") in flag:
                    assert rule.get("safety_critical_ratio_threshold") == "5"

    def test_frozen_and_overlay_substantive_hashes_are_separate(self):
        for case_id in CASES:
            frozen = FROZEN_SUBSTANTIVE_HASHES[case_id]
            overlay = OVERLAY_SUBSTANTIVE_HASHES[case_id]
            assert frozen == FROZEN_CASES[case_id]["substantive_input_hash"]
            assert overlay == CASES[case_id]["substantive_input_hash"]
            assert overlay != frozen
            assert overlay == content_hash(CASES[case_id]["typed_input"])
            assert frozen == content_hash(FROZEN_CASES[case_id]["typed_input"])

    def test_overlay_top_level_hash_is_explicit_and_self_consistent(self):
        assert "content_hash" not in OVERLAY_CATALOG
        assert OVERLAY_CATALOG["frozen_content_hash"] == CATALOG["content_hash"]
        overlay_without_own_hash = {
            key: value for key, value in OVERLAY_CATALOG.items()
            if key != "overlay_content_hash"
        }
        assert OVERLAY_CATALOG["overlay_content_hash"] == content_hash(
            overlay_without_own_hash
        )
        assert OVERLAY_CATALOG["overlay_content_hash"] != CATALOG["content_hash"]


# ===========================================================================
# Executable challenge rows (all 144) -- oracle / DSL exact match
# ===========================================================================


@lru_cache(maxsize=EXPECTED_CASE_COUNT)
def _compiled(case_id: str):
    return compile_frozen_program(EXPECTATIONS[case_id], ORACLE)


class TestChallengeRows:
    @pytest.mark.parametrize("number", _case_numbers(), ids=_case_ids())
    def test_row_exact_matches_oracle_and_dsl(self, number):
        case_id = _case_id(number)
        case = CASES[case_id]
        expectation = EXPECTATIONS[case_id]
        root = evaluate_safety(case["typed_input"])
        flat = flatten_root(root)

        # 1. Exact leaf bijection vs the independent oracle.
        missing, extra, mismatches, integrity_ok = exact_leaf_check(flat, expectation)
        assert not missing, f"case {case_id} missing oracle leaves: {missing}"
        assert not extra, f"case {case_id} extra runtime leaves: {extra}"
        assert not mismatches, f"case {case_id} value mismatches: {mismatches}"
        assert integrity_ok, (
            f"case {case_id} integrity error mismatch: "
            f"expected {expectation.get('expected_integrity_error')} "
            f"got {flat.get('integrity_error')}"
        )

        # 2. Root synthetic leaves (documented runtime-output contract).
        assert flat.get("integrity_error") == root.get("integrity_error")
        medical_keys = [
            k for k in flat
            if not k.startswith(("trace.", "source.", "integrity."))
            and k not in ROOT_SYNTHETIC_LEAVES
        ]
        assert root.get("medical_leaf_count") == len(medical_keys), case_id
        assert root.get("trace_leaf_count") == len([
            k for k in flat if k.startswith("trace.")
        ]), case_id
        assert root.get("source_leaf_count") == len([
            k for k in flat if k.startswith("source.")
        ]), case_id

        # 3. Integrity cases fail closed: no medical/priority/risk/Query/Journey.
        if case_id in INTEGRITY_CASES:
            assert fail_closed_root(root), (
                f"case {case_id} did not fail closed: "
                f"err={root.get('integrity_error')} unit_count={root.get('unit_count')}"
            )

        # 4. Frozen closed-DSL program: hash fidelity + every clause holds.
        program, program_hash = _compiled(case_id)
        assert program_hash == REGISTRY_CORE[case_id]["assertion_program_hash"], case_id
        validate_program_structure(program)
        assertions = interpret_program(program, flat)
        assert len(assertions) == len(program), case_id
        failed = [a for a in assertions if not a["passed"]]
        assert not failed, (
            f"case {case_id} DSL clauses failed: "
            + "; ".join(
                f"{a['clause_id']} {a['operator']} {a['actual_path']} "
                f"expected={a['expected']!r} actual={a['actual']!r}"
                for a in failed[:5]
            )
        )


# ===========================================================================
# Runtime closure: the runtime never reads the frozen artifacts
# ===========================================================================


class TestRuntimeClosure:
    _RUNTIME_FILES = (
        _R4_SRC / "mm_r4" / "d07_safety.py",
        _R4_SRC / "mm_r4" / "d07_safety_evaluator.py",
        _R4_SRC / "mm_r4" / "d07_journey.py",
        _R4_SRC / "mm_r4" / "d07_query.py",
    )

    def test_runtime_never_reads_frozen_artifacts(self):
        artifact_basename_fragments = (
            "typed_fixture_catalog", "expected_outcome_oracle",
            "challenge_manifest_registry", "reviews/",
        )
        for path in self._RUNTIME_FILES:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                # No file IO.
                if isinstance(node, ast.Call):
                    func = node.func
                    name = (
                        func.id if isinstance(func, ast.Name)
                        else func.attr if isinstance(func, ast.Attribute) else ""
                    )
                    assert name not in ("open", "read_text", "write_text",
                                        "load", "loads"), (path.name, node.lineno)
                # No imports of artifact modules / test adapters.
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in node.names]
                    for name in names:
                        assert "generate_d07" not in name, (path.name, node.lineno)
                        assert "fixtures" not in name, (path.name, node.lineno)
                        assert "reviews" not in name, (path.name, node.lineno)
                # No string literal references the frozen artifact files.
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for fragment in artifact_basename_fragments:
                        assert fragment not in node.value, (
                            path.name, node.lineno, fragment
                        )

    def test_runtime_output_carries_no_case_binding(self):
        """The raw output never contains the fixture/test identifiers or the
        Chinese case names (the runtime only sees the typed input; a bare
        ``001`` substring is part of the synthetic id vocabulary)."""
        for case_id in ("001", "129", "137"):
            case = CASES[case_id]
            root = evaluate_safety(case["typed_input"])
            flat = flatten_root(root)
            joined = "".join(
                str(v) for v in flat.values() if isinstance(v, (str, list))
            )
            assert case["fixture_id"] not in joined
            assert case["case_name"] not in joined
            assert f"d07-test-{case_id}" not in joined
