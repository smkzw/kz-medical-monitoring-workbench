"""Tests for R6 v0.1 contract verification and the baseline fixture catalog.

All tests are read-only: frozen artifacts are loaded from disk, tamper
scenarios run on in-memory copies, and nothing outside this POC tree is
written. The suite must pass under normal, ``-O``, and ``-OO`` execution and
any ``PYTHONHASHSEED``.
"""

import copy
import json

import pytest

from mm_r6 import contracts as C
from mm_r6 import fixtures as F


# ---------------------------------------------------------------------------
# stable-byte identity
# ---------------------------------------------------------------------------

class TestStableBytes:
    def test_contract_sha_matches_accepted(self, contract_raw):
        assert C.sha256_hex(contract_raw) == C.ACCEPTED_CONTRACT_SHA256

    def test_matrix_sha_matches_accepted(self, matrix_raw):
        assert C.sha256_hex(matrix_raw) == C.ACCEPTED_MATRIX_SHA256

    def test_prose_sha_matches_accepted(self, workbench_root):
        raw = C.load_bytes(C.prose_path())
        C.check_stable_bytes(raw, C.ACCEPTED_PROSE_SHA256, "prose contract")

    def test_tampered_contract_byte_fails(self, contract_raw):
        tampered = bytearray(contract_raw)
        tampered[0] ^= 0x01
        with pytest.raises(C.ContractVerificationError, match="stable_bytes"):
            C.check_stable_bytes(bytes(tampered), C.ACCEPTED_CONTRACT_SHA256, "contract.json")

    def test_tampered_matrix_byte_fails(self, matrix_raw):
        tampered = bytearray(matrix_raw)
        tampered[-1] ^= 0x01
        with pytest.raises(C.ContractVerificationError, match="stable_bytes"):
            C.check_stable_bytes(bytes(tampered), C.ACCEPTED_MATRIX_SHA256, "challenge_matrix.json")


# ---------------------------------------------------------------------------
# identity and structure
# ---------------------------------------------------------------------------

class TestIdentityAndStructure:
    def test_verify_all_passes(self, contract, matrix):
        report = C.verify_all(contract, matrix)
        assert report["row_count"] == 86
        assert report["diagnostic_code_count"] == 49
        assert len(report["validator_ids"]) == 11
        assert report["checks"] == {
            "contract_object": True,
            "matrix_object": True,
            "identity_bindings": True,
        }

    def test_contract_counts(self, contract):
        counts = contract["contract_counts"]
        assert counts["mode_count"] == 3
        assert counts["three_piece_count"] == 3
        assert counts["report_unit_type_count"] == 9
        assert counts["claim_status_count"] == 8
        assert counts["coverage_status_count"] == 5
        assert counts["output_kind_count"] == 16
        assert counts["deterministic_validator_count"] == 11
        assert counts["prohibition_count"] == 16

    def test_matrix_identity_fields(self, matrix, contract):
        C.verify_identity(contract, matrix)
        assert matrix["contract_id"] == contract["contract_id"]
        assert matrix["contract_version"] == contract["contract_version"] == "0.1"

    def test_matrix_identity_mismatch_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        tampered["contract_id"] = "other_contract"
        with pytest.raises(C.ContractVerificationError, match="matrix_identity"):
            C.verify_matrix_object(tampered, contract)

    def test_contract_validator_count_mismatch_rejected(self, contract):
        tampered = copy.deepcopy(contract)
        tampered["contract_counts"]["deterministic_validator_count"] = 12
        with pytest.raises(C.ContractVerificationError, match="deterministic_validator_count"):
            C.verify_contract_object(tampered)

    def test_row_drop_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        tampered["rows"] = tampered["rows"][:85]
        with pytest.raises(C.ContractVerificationError, match="row_count"):
            C.verify_matrix_object(tampered, contract)

    def test_non_replace_op_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        tampered["rows"][0]["single_mutation"]["op"] = "add"
        with pytest.raises(C.ContractVerificationError, match="mutation_op_replace_only"):
            C.verify_matrix_object(tampered, contract)

    def test_placeholder_mutation_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        tampered["rows"][0]["single_mutation"]["value"] = "TODO"
        with pytest.raises(C.ContractVerificationError, match="placeholder_mutations_forbidden"):
            C.verify_matrix_object(tampered, contract)

    def test_undeclared_diagnostic_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        row = tampered["rows"][1]  # R6C-002, reject row
        row["expected_outcome"] = "reject:NOT_A_REAL_CODE"
        row["expected_error"] = "NOT_A_REAL_CODE"
        with pytest.raises(C.ContractVerificationError, match="declared_diagnostic_only"):
            C.verify_matrix_object(tampered, contract)

    def test_accept_row_with_error_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        row = tampered["rows"][0]  # R6C-001, accept row
        row["expected_error"] = "REPORT_CLAIM_EVIDENCE_MISSING"
        with pytest.raises(C.ContractVerificationError, match="error_rule"):
            C.verify_matrix_object(tampered, contract)

    def test_bad_projection_rejected(self, contract, matrix):
        tampered = copy.deepcopy(matrix)
        tampered["rows"][0]["expected_projection"] = "not_a_projection"
        with pytest.raises(C.ContractVerificationError, match="projection_values"):
            C.verify_matrix_object(tampered, contract)


# ---------------------------------------------------------------------------
# 86 rows: shape and the 49-diagnostic-code map
# ---------------------------------------------------------------------------

class TestChallengeMatrixShape:
    def test_86_unique_ids_in_order(self, matrix):
        ids = [r["challenge_id"] for r in matrix["rows"]]
        assert len(ids) == 86
        assert len(set(ids)) == 86
        assert ids == [f"R6C-{i:03d}" for i in range(1, 87)]

    def test_category_and_severity_counts(self, matrix):
        from collections import Counter

        assert Counter(r["category"] for r in matrix["rows"]) == Counter(
            matrix["category_counts"]
        )
        assert Counter(r["severity"] for r in matrix["rows"]) == Counter(
            matrix["severity_counts"]
        )
        assert len(set(matrix["category_counts"])) == 12
        assert matrix["severity_counts"] == {"P0": 2, "P1": 69, "P2": 15}

    def test_all_paths_under_candidate_root_and_well_formed(self, matrix):
        for row in matrix["rows"]:
            path = row["single_mutation"]["path"]
            assert path.startswith("/candidate/")
            assert not path.endswith("/")
            assert "//" not in path

    def test_diagnostic_map_bidirectional_49(self, contract, matrix):
        semantics = set(matrix["error_semantics"].keys())
        mapped = {
            code
            for entry in matrix["error_code_map"]
            for code in entry["diagnostic_codes"]
        }
        assert semantics == mapped
        assert len(semantics) == 49
        validators = {v["id"]: set(v["failure_codes"]) for v in contract["deterministic_validators"]}
        for entry in matrix["error_code_map"]:
            assert entry["validator_id"] in validators
            assert entry["failure_code"] in validators[entry["validator_id"]]
            assert entry["blocking"] is True

    def test_every_expected_error_declared(self, matrix):
        semantics = set(matrix["error_semantics"].keys())
        for row in matrix["rows"]:
            if row["expected_error"] is not None:
                assert row["expected_error"] in semantics

    def test_positive_rows_have_null_error(self, matrix):
        for row in matrix["rows"]:
            if row["case_class"] == "positive":
                assert row["expected_error"] is None


# ---------------------------------------------------------------------------
# pointer helpers
# ---------------------------------------------------------------------------

class TestPointerHelpers:
    def test_strict_eq_type_aware(self):
        assert F.strict_eq(True, True)
        assert not F.strict_eq(True, 1)
        assert not F.strict_eq(False, 0)
        assert F.strict_eq(1, 1.0)
        assert F.strict_eq([1, {"a": None}], [1, {"a": None}])
        assert not F.strict_eq([1], [1.0, 2])

    def test_set_pointer_fail_closed(self):
        doc = {"candidate": {"body": {}}}
        with pytest.raises(F.FixtureError, match="pointer path missing"):
            F.set_pointer(doc, "/candidate/body/paragraph/claim", "x")
        with pytest.raises(F.FixtureError, match="pointer path missing"):
            F.set_pointer(doc, "/candidate/body/missing/claim", "x")
        # template itself is not mutated by failed or successful sets
        assert doc == {"candidate": {"body": {}}}
    def test_pointer_escaping_roundtrip(self):
        # key "a/b" is written as "a~1b" in a pointer; "c~d" as "c~0d"
        doc = {"a/b": {"c~d": [10, 20]}}
        assert F.get_pointer(doc, "/a~1b/c~0d/1") == 20
        out = F.set_pointer(doc, "/a~1b/c~0d/0", 99)
        assert out == {"a/b": {"c~d": [99, 20]}}
        stripped, found = F.strip_pointer(doc, "/a~1b/c~0d")
        assert found and stripped == {"a/b": {}}

    def test_pointer_exists_distinguishes_null(self):
        doc = {"candidate": {"x": None}}
        assert F.pointer_exists(doc, "/candidate/x")
        assert F.get_pointer(doc, "/candidate/x") is None
        assert not F.pointer_exists(doc, "/candidate/y")


# ---------------------------------------------------------------------------
# baseline fixture catalog
# ---------------------------------------------------------------------------

EXPECTED_CONTESTED_PATHS = [
    "/candidate/body/paragraph/claim/evidence_refs",
    "/candidate/cross_page/anchor_state",
    "/candidate/cutoff/ref",
    "/candidate/daily/output_scope",
    "/candidate/denominator/ref",
    "/candidate/output/claim_status",
    "/candidate/publication/analysis_state",
    "/candidate/revision_issue/diff_state",
    "/candidate/table/row/claim/locator_ref",
]


class TestFixtureCatalog:
    def test_catalog_builds_86_sorted(self, fixture_catalog, matrix_rows):
        assert fixture_catalog["fixture_count"] == 86
        entries = fixture_catalog["fixtures"]
        assert [e["fixture_id"] for e in entries] == [
            row["challenge_id"] for row in sorted(matrix_rows, key=lambda r: r["challenge_id"])
        ]
        assert all(e["fixture_id"] == e["challenge_id"] for e in entries)

    def test_pointer_preconditions_all_rows(self, matrix_rows):
        for row in matrix_rows:
            doc = F.build_fixture(row["challenge_id"], row)
            assert F.verify_pointer_preconditions(doc, row) == [], row["challenge_id"]
            assert F.verify_freeze(doc, F.CANONICAL_TEMPLATE, row) == [], row["challenge_id"]

    def test_contested_paths_exact(self, fixture_catalog, matrix_rows):
        assert fixture_catalog["contested_paths"] == EXPECTED_CONTESTED_PATHS
        assert C.contested_paths(matrix_rows) == EXPECTED_CONTESTED_PATHS

    def test_catalog_two_pass_byte_identical(self, matrix_rows):
        b1 = F.canonical_catalog_bytes(F.build_fixture_catalog(matrix_rows))
        b2 = F.canonical_catalog_bytes(F.build_fixture_catalog(matrix_rows))
        assert b1 == b2

    def test_catalog_verify_independent(self, fixture_catalog, matrix_rows):
        assert F.verify_fixture_catalog(fixture_catalog, matrix_rows) == []

    def test_template_not_mutated_by_builds(self, matrix_rows):
        before = copy.deepcopy(F.CANONICAL_TEMPLATE)
        for row in matrix_rows:
            F.build_fixture(row["challenge_id"], row)
        assert F.strict_eq(before, F.CANONICAL_TEMPLATE)

    def test_null_baseline_pointers_exist(self, matrix_rows):
        null_rows = [r for r in matrix_rows if r["baseline_value"] is None]
        assert len(null_rows) >= 5
        for row in null_rows:
            doc = F.build_fixture(row["challenge_id"], row)
            pointer = row["single_mutation"]["path"]
            assert F.pointer_exists(doc, pointer), row["challenge_id"]
            assert F.get_pointer(doc, pointer) is None, row["challenge_id"]

    def test_contested_fixture_uses_row_baseline(self, matrix_rows):
        by_id = {r["challenge_id"]: r for r in matrix_rows}
        for cid, expected_baseline in (
            ("R6C-001", []),
            ("R6C-004", ["fact-body-001"]),
            ("R6C-032", None),
            ("R6C-033", "cutoff-2026-08-01"),
            ("R6C-048", None),
            ("R6C-049", "unresolved"),
            ("R6C-053", "delta_only"),
            ("R6C-058", "change_summary_plus_current_full_risk"),
            ("R6C-065", "unsupported"),
            ("R6C-066", "outdated_wrong_cutoff"),
            ("R6C-083", "complete"),
            ("R6C-086", "running"),
            ("R6C-007", None),
            ("R6C-010", "table-1/r-2/c-3"),
            ("R6C-039", "unlinked"),
            ("R6C-041", "unique"),
            ("R6C-024", None),
            ("R6C-025", "denom-001"),
        ):
            row = by_id[cid]
            doc = F.build_fixture(cid, row)
            assert F.get_pointer(doc, row["single_mutation"]["path"]) == expected_baseline
            assert F.verify_pointer_preconditions(doc, row) == []

    def test_catalog_payload_is_json_serializable(self, fixture_catalog):
        text = json.dumps(fixture_catalog, sort_keys=True, ensure_ascii=False)
        assert json.loads(text)["catalog_id"] == "mm_r6_baseline_fixture_catalog"
