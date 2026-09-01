"""Independent verification suite for the R6 v0.1 challenge-matrix slice.

Work item 3 only. Proves (without claiming product/runtime acceptance):

* 86/86 one-replace oracle parity (outcome / error / projection / only-once);
* 49 diagnostic codes map to the 11 validators; undeclared diagnostics rejected;
* positive (accept/record) rows emit no blocking findings;
* fixture catalog two-pass canonical bytes are identical;
* frozen contract/matrix/prose SHA-256 immutability;
* protected medical-writing aggregate (542 files) is unchanged;
* ports 8911 and 5174 remain stopped;
* create-only allowlist under this POC is exact;
* subprocess reproducibility under normal / ``-O`` / ``-OO`` × ≥3
  ``PYTHONHASHSEED`` values (raise-based, not assert-based, so optimizer
  stripping cannot vacate the check).

This module never writes outside the declared R6 create-only paths and never
starts services, browsers, OCR, models, or real-project workflows.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from mm_r6 import contracts, fixtures, validator

POC_ROOT = Path(__file__).resolve().parents[1]
WORKBENCH_ROOT = contracts.WORKBENCH_ROOT

CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "evidence/r6_contract_runtime_receipt.json",
        "src/mm_r6/report_review.py",
        "tests/test_report_review.py",
        "evidence/r6_report_review_runtime_receipt.json",
        "src/mm_r6/report_bundle.py",
        "tests/test_report_bundle.py",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "src/mm_r6/mode_output.py",
        "src/mm_r6/agent_harness.py",
        "tests/test_mode_output.py",
        "tests/test_agent_harness.py",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
        "README.md",
    }
)

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 542
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
)
EXPECTED_CATALOG_SHA256 = (
    "76b43076d896001fb4b393f43329a194b32d9091625101d8eed2ba2ece940b53"
)
EXPECTED_TEMPLATE_SHA256 = (
    "8474742023eb192df8e332c6e20a0c9f89ea06292f68e9005a41e195967daf0e"
)

PROTECTED_PORTS = (8911, 5174)


def _rows():
    return contracts.matrix_obj(contracts.matrix_raw())["rows"]


def _medical_writing_boundary(root: Path) -> dict:
    """Recompute the frozen medical-writing inventory (read-only).

    Algorithm matches
    ``scripts/verify_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py``
    / the R5-S5 public-authority protected-inventory contract: walk the five
    protected roots, keep regular files whose relative path matches
    ``medical[-_]writing``, hash each file, then aggregate
    ``relative\\0file_sha\\n`` over UTF-8-sorted relatives.
    """
    matched: dict = {}
    errors = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        base = root / root_relative
        if not base.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, dirnames, filenames in os.walk(
            base, topdown=True, followlinks=False
        ):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(directory) / filename
                relative = path.relative_to(root).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(
                        f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}"
                    )
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched[relative] = hashlib.sha256(path.read_bytes()).hexdigest().lower()
                except (OSError, UnicodeError) as exc:
                    errors.append(
                        f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}"
                    )
    aggregate = hashlib.sha256()
    for relative in sorted(matched, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "file_count": len(matched),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


# ---------------------------------------------------------------------------
# 86/86 oracle parity + only-once
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", _rows(), ids=lambda r: r["challenge_id"])
def test_independent_oracle_parity_per_row(row, contract, matrix):
    result = validator.execute_challenge(row, contract, matrix)
    assert result.mutations_applied == 1
    assert result.outcome == row["expected_outcome"]
    assert result.error == row["expected_error"]
    assert result.projection == row["expected_projection"]
    assert row["test_metadata_only"] is True


def test_oracle_parity_report_zero_mismatches(contract, matrix):
    report = validator.oracle_parity_report(matrix["rows"], contract, matrix)
    assert report["row_count"] == 86
    assert report["mismatch_count"] == 0
    assert report["mismatches"] == []
    assert len(report["results"]) == 86


def test_execute_all_only_once_ordered(matrix_rows, contract, matrix):
    results = validator.execute_all(matrix_rows, contract, matrix)
    assert len(results) == 86
    assert [r.challenge_id for r in results] == [f"R6C-{i:03d}" for i in range(1, 87)]
    assert all(r.mutations_applied == 1 for r in results)
    # Second call is independent; still one mutation per row (no shared state).
    again = validator.execute_all(matrix_rows, contract, matrix)
    assert [r.as_dict() for r in again] == [r.as_dict() for r in results]


# ---------------------------------------------------------------------------
# 49 diagnostic mappings + undeclared rejection
# ---------------------------------------------------------------------------


def test_forty_nine_diagnostic_mappings(matrix, contract):
    index = validator.build_diagnostic_index(matrix)
    assert len(index) == 49
    assert set(index) == set(matrix["error_semantics"])
    map_codes = [
        code
        for entry in matrix["error_code_map"]
        for code in entry["diagnostic_codes"]
    ]
    assert len(map_codes) == 49
    assert len(set(map_codes)) == 49
    assert set(map_codes) == set(matrix["error_semantics"])
    validator_failure_codes = {
        v["id"]: set(v["failure_codes"]) for v in contract["deterministic_validators"]
    }
    assert len(validator_failure_codes) == 11
    for code, (vid, failure, blocking) in index.items():
        assert blocking is True
        assert vid in validator_failure_codes
        assert failure in validator_failure_codes[vid]
    # Every row's expected_error (when set) is declared.
    for row in matrix["rows"]:
        err = row["expected_error"]
        if err is not None:
            assert err in index


def test_undeclared_diagnostic_rejected(matrix):
    with pytest.raises(validator.ValidatorError):
        validator.finding_for("NOT_A_DECLARED_DIAGNOSTIC_CODE", validator.build_diagnostic_index(matrix))


def test_sixteen_prohibitions_and_eleven_validators(contract):
    assert len(contract["prohibitions"]) == 16
    assert len(set(contract["prohibitions"])) == 16
    ids = [v["id"] for v in contract["deterministic_validators"]]
    assert len(ids) == 11
    assert set(ids) == set(validator.VALIDATORS)
    assert "R6-C-BOUNDARY-001" in ids


# ---------------------------------------------------------------------------
# positive rows: no blocking
# ---------------------------------------------------------------------------


def test_positive_rows_have_no_blocking(matrix_rows, contract, matrix):
    positives = [
        r
        for r in matrix_rows
        if r["expected_error"] is None
        and (
            r["expected_outcome"].startswith("accept:")
            or r["expected_outcome"].startswith("record:")
        )
    ]
    assert len(positives) >= 1
    for row in positives:
        result = validator.execute_challenge(row, contract, matrix)
        assert result.blocking is False
        assert result.error is None
        assert all(not f.blocking for f in result.findings)


# ---------------------------------------------------------------------------
# deterministic bytes (catalog two-pass + template digest)
# ---------------------------------------------------------------------------


def test_fixture_catalog_two_pass_bytes_identical(matrix_rows):
    c1 = fixtures.build_fixture_catalog(matrix_rows)
    c2 = fixtures.build_fixture_catalog(matrix_rows)
    b1 = fixtures.canonical_catalog_bytes(c1)
    b2 = fixtures.canonical_catalog_bytes(c2)
    assert b1 == b2
    assert c1["catalog_sha256"] == c2["catalog_sha256"] == EXPECTED_CATALOG_SHA256
    assert fixtures.template_sha256() == EXPECTED_TEMPLATE_SHA256
    assert fixtures.verify_fixture_catalog(c1, matrix_rows) == []


def test_per_row_fixture_bytes_stable(matrix_rows):
    for row in matrix_rows:
        a = fixtures.build_fixture(row["challenge_id"], row)
        b = fixtures.build_fixture(row["challenge_id"], row)
        assert fixtures.canonical_bytes(a) == fixtures.canonical_bytes(b)
        assert fixtures.verify_pointer_preconditions(a, row) == []


# ---------------------------------------------------------------------------
# source immutability (frozen stable bytes)
# ---------------------------------------------------------------------------


def test_frozen_source_sha_immutability(contract_raw, matrix_raw, workbench_root):
    assert contracts.sha256_hex(contract_raw) == contracts.ACCEPTED_CONTRACT_SHA256
    assert contracts.sha256_hex(matrix_raw) == contracts.ACCEPTED_MATRIX_SHA256
    prose = contracts.load_bytes(contracts.prose_path())
    assert contracts.sha256_hex(prose) == contracts.ACCEPTED_PROSE_SHA256
    # Re-read from disk independently of fixtures (immutability under this run).
    disk_c = (workbench_root / contracts.CONTRACT_REL_PATH).read_bytes()
    disk_m = (workbench_root / contracts.MATRIX_REL_PATH).read_bytes()
    disk_p = (workbench_root / contracts.PROSE_REL_PATH).read_bytes()
    assert contracts.sha256_hex(disk_c) == contracts.ACCEPTED_CONTRACT_SHA256
    assert contracts.sha256_hex(disk_m) == contracts.ACCEPTED_MATRIX_SHA256
    assert contracts.sha256_hex(disk_p) == contracts.ACCEPTED_PROSE_SHA256


# ---------------------------------------------------------------------------
# medical-writing boundary + ports stopped
# ---------------------------------------------------------------------------


def test_medical_writing_aggregate_unchanged(workbench_root):
    boundary = _medical_writing_boundary(workbench_root)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


# ---------------------------------------------------------------------------
# create-only allowlist (exact file set under POC, ignoring caches)
# ---------------------------------------------------------------------------


def test_create_only_allowlist_exact():
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        if "__pycache__" in rel.split("/") or ".pytest_cache" in rel.split("/"):
            continue
        if rel.endswith(".pyc"):
            continue
        found.add(rel)
    # Evidence receipts may be absent until the final verifier write. The
    # create-only surface otherwise must match exactly (no extras).
    optional_receipts = {
        "evidence/r6_contract_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
    }
    extras = found - CREATE_ONLY_RELATIVE
    missing_required = (CREATE_ONLY_RELATIVE - optional_receipts) - found
    assert extras == set()
    assert missing_required == set()
    assert found <= CREATE_ONLY_RELATIVE


# ---------------------------------------------------------------------------
# reproducibility: normal / -O / -OO × hash seeds (subprocess, raise-based)
# ---------------------------------------------------------------------------

_REPRO_PROBE = r"""
import os, sys
sys.path.insert(0, os.environ["MM_R6_SRC"])
from mm_r6 import contracts, fixtures, validator
c = contracts.contract_obj(contracts.contract_raw())
m = contracts.matrix_obj(contracts.matrix_raw())
rows = m["rows"]
report = validator.oracle_parity_report(rows, c, m)
if report["mismatch_count"] != 0 or report["row_count"] != 86:
    raise SystemExit("parity_fail:%s" % report["mismatch_count"])
c1 = fixtures.build_fixture_catalog(rows)
c2 = fixtures.build_fixture_catalog(rows)
if fixtures.canonical_catalog_bytes(c1) != fixtures.canonical_catalog_bytes(c2):
    raise SystemExit("catalog_bytes_diverge")
if c1["catalog_sha256"] != os.environ["MM_R6_EXPECTED_CATALOG_SHA"]:
    raise SystemExit("catalog_sha_mismatch")
print("ok")
"""


@pytest.mark.parametrize("opt_flag", ["", "-O", "-OO"])
@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
def test_repro_matrix_oracle_and_catalog(opt_flag, hash_seed):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MM_R6_SRC"] = str(POC_ROOT / "src")
    env["MM_R6_EXPECTED_CATALOG_SHA"] = EXPECTED_CATALOG_SHA256
    cmd = [sys.executable]
    if opt_flag:
        cmd.append(opt_flag)
    cmd.extend(["-c", _REPRO_PROBE])
    proc = subprocess.run(
        cmd,
        cwd=str(WORKBENCH_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"opt={opt_flag!r} seed={hash_seed} rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "ok" in proc.stdout


def test_verify_all_structural_gate(contract, matrix):
    report = contracts.verify_all(contract, matrix)
    assert report["row_count"] == 86
    assert report["diagnostic_code_count"] == 49
    assert len(report["validator_ids"]) == 11
    assert report["checks"]["contract_object"] is True
    assert report["checks"]["matrix_object"] is True
    assert report["checks"]["identity_bindings"] is True
