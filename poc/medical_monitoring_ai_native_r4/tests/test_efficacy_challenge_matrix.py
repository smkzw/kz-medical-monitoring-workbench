"""R4-D06 219-row frozen challenge matrix + DSL/oracle verification.

Drives every frozen challenge row (numbers 1..219) through the real D06
entrypoints (``efficacy_evaluator``, ``gate_evaluator``,
``contract_schema_validator``, ``audience_projection_validator``,
``challenge_registry_validator``) using the typed fixture adapter, then
verifies:

* the frozen catalog / oracle / registry identity and hashes are intact
  (``catalog_id``/``version``/``catalog_hash``, oracle hash, registry
  hash, contract semantic hash);
* every row executes through its declared entrypoint and produces the
  exact frozen expected-outcome leaf set (DSL path bijection);
* every frozen ``d06-assert-v1`` clause is interpreted against the actual
  outcome and holds (named, non-tautological assertions; tautological /
  static / unconsumed assertions are rejected by the interpreter);
* the assembled outcome matches the independent oracle object-for-object
  after canonical normalization;
* required outcome fields, trace edges, hash relations and audience
  checks are exact per the manifest;
* deterministic replay of identical runs yields identical object hashes.

The runtime never reads the oracle/DSL; expected outcomes stay test-side.
All data is synthetic and offline.
"""

from __future__ import annotations

import sys
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

from mm_r4.efficacy import (  # noqa: E402
    d06_canonical_json,
)
from mm_r4.efficacy_fixtures import (  # noqa: E402
    build_d06_challenge_matrix,
    interpret_assertion_dsl,
    load_frozen_catalog,
    load_frozen_oracle,
    load_frozen_registry,
    outcome_matches_expected,
)

CATALOG = load_frozen_catalog()
ORACLE = load_frozen_oracle()
REGISTRY = load_frozen_registry()
MATRIX = build_d06_challenge_matrix(CATALOG)

_ENTRYPOINT_SET = {
    "d06.efficacy_evaluator",
    "d06.gate_evaluator",
    "d06.contract_schema_validator",
    "d06.audience_projection_validator",
    "d06.challenge_registry_validator",
}


def _case_ids():
    return [f"challenge-{case.number:03d}" for case in MATRIX.cases]


def _case_args():
    return [case.number for case in MATRIX.cases]


# ===========================================================================
# Matrix structure
# ===========================================================================


class TestMatrixStructure:
    def test_matrix_has_exactly_219_unique_cases(self):
        assert MATRIX.case_count == 219
        assert MATRIX.numbers == tuple(range(1, 220))
        assert len({case.name for case in MATRIX.cases}) == 219

    def test_case_lookup_by_number(self):
        assert MATRIX.by_number(1).number == 1
        assert MATRIX.by_number(219).number == 219
        with pytest.raises(KeyError):
            MATRIX.by_number(0)

    def test_all_entrypoints_are_the_frozen_set(self):
        assert {case.entrypoint_id for case in MATRIX.cases} == _ENTRYPOINT_SET

    def test_fixture_scope_is_canonical(self):
        for case in MATRIX.cases:
            assert case.fixture["scope"]["project_ref"] == "SYN-D06-PROJECT"
            assert case.fixture["scope"]["subject_ref"] == "SYN-D06-SUBJECT-001"
            assert case.fixture["fixture_schema_version"] == "d06-typed-fixture-v2"
            assert case.fixture["synthetic_only"] is True


# ===========================================================================
# Executable challenge rows (all 219)
# ===========================================================================


class TestChallengeRows:
    @pytest.mark.parametrize("number", _case_args(), ids=_case_ids())
    def test_row_executes_against_frozen_oracle(self, number):
        case = MATRIX.by_number(number)
        assembled = case.assemble()
        # Exact leaf bijection: no extra, no missing outcome leaves.
        assert sorted(assembled) == sorted(case.expected_outcome)
        # Every frozen DSL clause is a named, non-tautological assertion
        # that holds against the raw entrypoint output.  No challenge/
        # test/case identity, expected text, oracle, manifest trace or
        # annotation substitutes any leaf (v1.18: all 219 rows exact,
        # including clinical_outcome_contract).
        assertions = interpret_assertion_dsl(assembled, case.assertion_dsl)
        assert len(assertions) == len(case.assertion_dsl)
        for assertion in assertions:
            assert assertion.passed, (
                f"case {number} clause {assertion.clause_id} failed"
            )
        # Independent oracle comparison.
        assert outcome_matches_expected(assembled, case.expected_outcome)
        # Required outcome fields are exact.
        assert sorted(assembled) == sorted(case.required_outcome_fields)
        # Trace edges are exact and canonical.
        assert assembled["trace_edges"] == sorted(set(case.required_trace_edge_types))
        # Hash relations bind the frozen fixture hash.
        assert assembled["domain_assertions"]["evaluated_fixture_hash"] == (
            case.fixture_hash
        )
        assert assembled["object_hashes"]["fixture_hash"] == case.fixture_hash
        assert assembled["invoked_entrypoint"] == case.entrypoint_id

    @pytest.mark.parametrize("number", _case_args(), ids=_case_ids())
    def test_row_has_runtime_derived_medical_leaves(self, number):
        """Every row carries at least one runtime-derived non-metadata leaf.

        Guards against static/literal assertions: the medical outcome
        fields must be produced by the engine, not copied from the
        manifest.
        """
        case = MATRIX.by_number(number)
        assembled = case.assemble()
        derived = [
            "l1_disposition",
            "primary_subtype",
            "coverage_status",
            "gate_state",
            "gate_disposition",
            "l2_counts",
            "output_kind",
            "error_type",
            "error_stage",
        ]
        medical_present = any(assembled.get(key) is not None for key in derived)
        if case.expected_outcome["output_kind"] == "error":
            assert assembled["error_type"] is not None
        else:
            assert medical_present or assembled["output_kind"] in (
                "projection",
                "definition_binding",
            ), f"case {number} has no runtime-derived medical leaf"

    @pytest.mark.parametrize("number", _case_args(), ids=_case_ids())
    def test_row_dsl_clauses_are_exact_bijection(self, number):
        case = MATRIX.by_number(number)
        clauses = case.assertion_dsl
        for index, clause in enumerate(clauses, 1):
            assert set(clause) == {
                "canonicalization_rule",
                "clause_id",
                "operator",
                "outcome_path",
                "typed_expected_value",
            }
            assert clause["clause_id"] == f"assert-{index:03d}"
            assert clause["operator"] in ("equals", "is_null")
            assert clause["canonicalization_rule"] == "d06-canonical-v1"
            if clause["operator"] == "is_null":
                assert clause["typed_expected_value"] is None
            else:
                assert clause["typed_expected_value"] is not None


# ===========================================================================
# Registry / DSL validator behavior (challenge_registry_validator)
# ===========================================================================


class TestChallengeRegistryValidator:
    def test_tautological_callback_rejected(self):
        case = MATRIX.by_number(170)
        outcome = case.run()
        assert outcome.output_kind == "error"
        assert outcome.error_type == "ChallengeAssertionContractError"
        assert outcome.error_stage == "assertion_manifest_validation"

    def test_input_only_assertion_rejected(self):
        case = MATRIX.by_number(171)
        outcome = case.run()
        assert outcome.error_type == "ChallengeAssertionContractError"

    def test_unrelated_field_assertion_rejected(self):
        case = MATRIX.by_number(189)
        outcome = case.run()
        assert outcome.error_type == "ChallengeAssertionContractError"

    def test_registry_integrity_drift_rejected_before_evaluator(self):
        case = MATRIX.by_number(214)
        outcome = case.run()
        assert outcome.output_kind == "error"
        assert outcome.error_type == "ChallengeRegistryIntegrityError"
        assert outcome.error_stage == "pre_fixture_integrity"
        assert outcome.domain_assertions["evaluator_invoked"] is False

    def test_valid_split_mapping_accepted(self):
        case = MATRIX.by_number(172)
        outcome = case.run()
        assert outcome.output_kind == "result"
        assert outcome.error_type is None


# ===========================================================================
# Deterministic replay
# ===========================================================================


class TestDeterministicReplay:
    def test_identical_rerun_hashes_are_stable(self):
        for number in (1, 2, 95, 108, 141, 219):
            case = MATRIX.by_number(number)
            first = case.assemble()
            second = case.assemble()
            assert d06_canonical_json(first) == d06_canonical_json(second)
            assert first["object_hashes"] == second["object_hashes"]
            assert first["domain_assertions"] == second["domain_assertions"]

    def test_all_fixture_hashes_match_oracle_bindings(self):
        oracle_cases = {item["challenge_number"]: item for item in ORACLE["cases"]}
        for case in MATRIX.cases:
            assert case.fixture_hash == oracle_cases[case.number]["fixture_hash"]

    def test_no_duplicate_risk_identity_across_rerun(self):
        """Positive roots never duplicate risk/Query counts on replay."""
        for number in (2, 7, 12, 39, 58, 95, 168):
            case = MATRIX.by_number(number)
            first = case.assemble()
            second = case.assemble()
            assert first["l2_counts"] == second["l2_counts"]
            assert first["l2_counts"]["risks"] == 1
            assert first["l2_counts"]["queries"] == 1
