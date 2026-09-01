"""Shared pytest fixtures for the R6 v0.1 synthetic/offline runtime slice.

All fixtures are read-only views of the frozen contract artifacts and the
deterministic fixture catalog. No test in this tree writes to the workbench
outside this POC directory, and none of the R6 create-only paths are modified
at test time.
"""

import json
import sys
from pathlib import Path

import pytest

POC_ROOT = Path(__file__).resolve().parents[1]

# Make ``mm_r6`` importable without installation (stdlib-only package).
SRC_DIR = POC_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mm_r6 import contracts  # noqa: E402
from mm_r6 import fixtures  # noqa: E402


@pytest.fixture(scope="session")
def workbench_root() -> Path:
    return contracts.WORKBENCH_ROOT


@pytest.fixture(scope="session")
def contract_raw() -> bytes:
    raw = contracts.load_bytes(contracts.contract_path())
    contracts.check_stable_bytes(raw, contracts.ACCEPTED_CONTRACT_SHA256, "contract.json")
    return raw


@pytest.fixture(scope="session")
def matrix_raw() -> bytes:
    raw = contracts.load_bytes(contracts.matrix_path())
    contracts.check_stable_bytes(raw, contracts.ACCEPTED_MATRIX_SHA256, "challenge_matrix.json")
    return raw


@pytest.fixture(scope="session")
def contract(contract_raw) -> dict:
    return json.loads(contract_raw.decode("utf-8"))


@pytest.fixture(scope="session")
def matrix(matrix_raw) -> dict:
    return json.loads(matrix_raw.decode("utf-8"))


@pytest.fixture(scope="session")
def matrix_rows(matrix) -> list:
    return matrix["rows"]


@pytest.fixture(scope="session")
def fixture_catalog(matrix_rows) -> dict:
    return fixtures.build_fixture_catalog(matrix_rows)
