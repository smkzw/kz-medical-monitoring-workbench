"""R5 S1 W3 -- immutable R4 public-source SHA gate.

Freezes the five R4 public source files the read-only authority adapter
imports (``mm_r4.d10_contracts``, ``mm_r4.d10_projection``,
``mm_r4.ensemble_contracts``, ``mm_r4.ensemble``, ``mm_r4/__init__.py``)
and enforces byte-identical sources across the whole R5 S1 test session:
ANY byte drift in R4 fails S1.

* a session-scoped autouse fixture snapshots the five SHA-256 values at
  session start (before ANY R5 test runs), fails the session if they do not
  match the freeze, and re-checks them at session end (after the whole test
  suite) -- verifying the sources before AND after the suite;
* a parametrized gate test asserts every file hash equals the frozen value;
* the evidence record ``evidence/r4_readonly_sha256.json`` (W3 artifact)
  must match the frozen values exactly.

Frozen values: ``context/medical_monitoring_r5_contract_acceptance_record_
20260818.md`` (seven-SHA freeze, R4 public source set).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

import pytest

#: R4 public source file -> frozen SHA-256 (acceptance-record freeze).
R4_SOURCE_SHA256: Dict[str, str] = {
    "d10_contracts.py": (
        "a1f7550b6f836141168d0d123fd86416a5e9e600585af8f657a43dc40b6ebfdb"),
    "d10_projection.py": (
        "14af6237f2052ff323cc12cb9760aad8ab91c93b594d89d04e1b88fd5e43e017"),
    "ensemble_contracts.py": (
        "fb429ea3c854291eb2a120bd3a745eef155370bd79932c91e4fcab212ce84c40"),
    "ensemble.py": (
        "beb5c1ab8f3db5c42e780e31312e057e1fe95298ee351e28b0602fb8dffa608a"),
    "__init__.py": (
        "deeae440d6a75ce0a6c519c9ec79539b3a4225fffe9b234ecc58443beb7b3f7d"),
}

_POC_ROOT = Path(__file__).resolve().parents[2]
R4_MMR4_DIR = (
    _POC_ROOT / "medical_monitoring_ai_native_r4" / "src" / "mm_r4")
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence" / "r4_readonly_sha256.json")


def _source_hashes() -> Dict[str, str]:
    return {
        name: hashlib.sha256(
            (R4_MMR4_DIR / name).read_bytes()).hexdigest()
        for name in R4_SOURCE_SHA256
    }


@pytest.fixture(scope="session", autouse=True)
def _r4_sha_before_and_after() -> None:
    """Fail the session if the five R4 sources drift from the freeze,
    checked before the suite runs and again after the suite finishes."""
    before = _source_hashes()
    assert before == R4_SOURCE_SHA256, (
        "R4 public source drifted from the S0 freeze BEFORE the R5 suite: "
        f"{before}")
    yield
    after = _source_hashes()
    assert after == R4_SOURCE_SHA256, (
        "R4 public source drifted from the S0 freeze AFTER the R5 suite: "
        f"{after}")
    assert after == before, "R4 sources changed during the R5 suite run"


@pytest.mark.parametrize("name", sorted(R4_SOURCE_SHA256))
def test_r4_public_source_matches_frozen_sha256(name: str) -> None:
    path = R4_MMR4_DIR / name
    assert path.is_file(), f"missing R4 public source: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == R4_SOURCE_SHA256[name], (
        f"R4 public source {name} drifted from the freeze: {actual}")


def test_r4_evidence_record_matches_frozen_values() -> None:
    """The W3 evidence record must pin exactly the frozen five SHAs."""
    assert EVIDENCE_PATH.is_file(), f"missing evidence record: {EVIDENCE_PATH}"
    data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert data["files"] == R4_SOURCE_SHA256, (
        "evidence record drifted from the frozen values")
    assert data["schema"] == (
        "medical-monitoring-r5-r4-readonly-sha256-evidence-v1")
