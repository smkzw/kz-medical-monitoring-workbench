"""Tests for the R6 v0.1 11-validator dispatcher and one-replace-per-row executor.

Work item 2 coverage only. Full reproducibility / boundary / receipt checks belong
to work item 3 (``test_challenge_matrix.py``). These tests prove:

* all 11 validators are registered;
* the non-normative category map cannot narrow validation coverage;
* exactly one RFC 6902 ``replace`` is applied per row;
* canonical outcome / error / projection / blocking match the metadata oracle
  for all 86 rows;
* undeclared diagnostics cannot be emitted;
* non-replace mutations are rejected;
* positive rows have no blocking findings.
"""

from __future__ import annotations

import copy

import pytest

from mm_r6 import contracts, fixtures, validator


def test_eleven_validators_registered(contract):
    ids = [v["id"] for v in contract["deterministic_validators"]]
    assert len(ids) == 11
    assert set(ids) == set(validator.VALIDATORS)
    assert tuple(ids) == validator.VALIDATOR_ORDER or set(ids) == set(validator.VALIDATOR_ORDER)


def test_category_validator_map_is_not_a_dispatch_filter(contract):
    mapping = contract["challenge_matrix_binding"]["category_validator_map"]
    assert len(mapping) == 12
    assert contract["challenge_matrix_binding"]["category_validator_map_normative"] is False
    expected_content_validators = [
        vid for vid in validator.VALIDATOR_ORDER if vid != "R6-C-BOUNDARY-001"
    ]
    for category, documented_ids in mapping.items():
        assert validator.validators_for_category(contract, category) == expected_content_validators
        for vid in documented_ids:
            assert vid in validator.VALIDATORS
    # Boundary validator is intentionally outside content categories.
    assert "R6-C-BOUNDARY-001" in validator.VALIDATORS
    for expected_ids in mapping.values():
        assert "R6-C-BOUNDARY-001" not in expected_ids


def test_unknown_category_rejected(contract):
    with pytest.raises(validator.ValidatorError):
        validator.validators_for_category(contract, "not-a-contract-category")


def test_apply_one_replace_only(matrix_rows):
    row = matrix_rows[0]
    doc = fixtures.build_fixture(row["challenge_id"], row)
    mutated = validator.apply_one_replace(doc, row["single_mutation"])
    assert fixtures.get_pointer(mutated, row["single_mutation"]["path"]) == row["single_mutation"]["value"]
    # Original fixture must remain at baseline (deep-copy semantics).
    assert fixtures.get_pointer(doc, row["single_mutation"]["path"]) == row["baseline_value"]
    with pytest.raises(validator.ValidatorError):
        validator.apply_one_replace(doc, {**row["single_mutation"], "op": "add"})
    with pytest.raises(validator.ValidatorError):
        validator.apply_one_replace(doc, {**row["single_mutation"], "op": "remove"})


def test_undeclared_diagnostic_rejected(matrix):
    index = validator.build_diagnostic_index(matrix)
    assert len(index) == 49
    with pytest.raises(validator.ValidatorError):
        validator.finding_for("NOT_A_REAL_DIAGNOSTIC", index)


def test_diagnostic_index_matches_error_code_map(matrix, contract):
    index = validator.build_diagnostic_index(matrix)
    validator_failure_codes = {
        v["id"]: set(v["failure_codes"]) for v in contract["deterministic_validators"]
    }
    for code, (vid, failure, blocking) in index.items():
        assert code in matrix["error_semantics"]
        assert failure in validator_failure_codes[vid]
        assert blocking is True


def _rows():
    return contracts.matrix_obj(contracts.matrix_raw())["rows"]


@pytest.mark.parametrize("row", _rows(), ids=lambda r: r["challenge_id"])
def test_each_row_oracle_parity(row, contract, matrix):
    result = validator.execute_challenge(row, contract, matrix)
    assert result.mutations_applied == 1
    assert result.outcome == row["expected_outcome"]
    assert result.error == row["expected_error"]
    assert result.projection == row["expected_projection"]
    if row["expected_error"] is None:
        assert result.blocking is False
        assert all(not f.blocking for f in result.findings)
    else:
        assert result.blocking is True
        assert any(f.diagnostic_code == row["expected_error"] for f in result.findings)
        primary = [f for f in result.findings if f.diagnostic_code == row["expected_error"]][0]
        assert primary.blocking is True
        # Canonical failure_code must be one declared by the mapped validator.
        mapped = validator.build_diagnostic_index(matrix)[row["expected_error"]]
        assert primary.validator_id == mapped[0]
        assert primary.failure_code == mapped[1]


def test_execute_all_only_once(matrix_rows, contract, matrix):
    results = validator.execute_all(matrix_rows, contract, matrix)
    assert len(results) == 86
    assert [r.challenge_id for r in results] == [f"R6C-{i:03d}" for i in range(1, 87)]
    assert all(r.mutations_applied == 1 for r in results)


def test_oracle_parity_report_clean(contract, matrix):
    report = validator.oracle_parity_report(matrix["rows"], contract, matrix)
    assert report["row_count"] == 86
    assert report["mismatch_count"] == 0
    assert report["mismatches"] == []


def test_category_relabel_cannot_suppress_any_expected_diagnostic(matrix_rows, contract, matrix):
    categories = tuple(contract["challenge_matrix_binding"]["category_validator_map"])
    for row in matrix_rows:
        expected = row["expected_error"]
        if expected is None:
            continue
        for category in categories:
            relabeled = copy.deepcopy(row)
            relabeled["category"] = category
            result = validator.execute_challenge(relabeled, contract, matrix)
            assert expected in {finding.diagnostic_code for finding in result.findings}, (
                row["challenge_id"],
                category,
                expected,
            )


def test_positive_rows_identity_preserved(matrix_rows, contract, matrix):
    positives = [r for r in matrix_rows if r["expected_error"] is None and r["expected_outcome"].startswith("accept:")]
    assert len(positives) >= 1
    for row in positives:
        result = validator.execute_challenge(row, contract, matrix)
        assert result.blocking is False
        assert result.error is None
        assert result.outcome.startswith("accept:")


def test_r6c_065_066_share_post_mutation_doc_but_differ_by_baseline(matrix_rows, contract, matrix):
    r65 = next(r for r in matrix_rows if r["challenge_id"] == "R6C-065")
    r66 = next(r for r in matrix_rows if r["challenge_id"] == "R6C-066")
    d65 = fixtures.set_pointer(
        fixtures.build_fixture(r65["challenge_id"], r65),
        r65["single_mutation"]["path"],
        r65["single_mutation"]["value"],
    )
    d66 = fixtures.set_pointer(
        fixtures.build_fixture(r66["challenge_id"], r66),
        r66["single_mutation"]["path"],
        r66["single_mutation"]["value"],
    )
    assert fixtures.strict_eq(d65, d66)
    a65 = validator.execute_challenge(r65, contract, matrix)
    a66 = validator.execute_challenge(r66, contract, matrix)
    assert a65.error == "REPORT_STATUS_EVIDENCE_MISMATCH"
    assert a66.error == "REPORT_CUTOFF_MISMATCH"


def test_challenge_result_as_dict_is_json_serializable(matrix_rows, contract, matrix):
    import json

    result = validator.execute_challenge(matrix_rows[0], contract, matrix)
    raw = json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True)
    assert "challenge_id" in raw


def test_fixture_not_mutated_by_executor(matrix_rows, contract, matrix):
    row = next(r for r in matrix_rows if r["challenge_id"] == "R6C-002")
    doc = fixtures.build_fixture(row["challenge_id"], row)
    before = fixtures.canonical_bytes(doc)
    validator.execute_challenge(row, contract, matrix, fixture_doc=copy.deepcopy(doc))
    assert fixtures.canonical_bytes(doc) == before
