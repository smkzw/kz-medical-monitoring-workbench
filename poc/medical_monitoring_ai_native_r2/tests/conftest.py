"""Shared pytest fixtures for the R2 POC test suite (worker_01-owned, Batch A).

All tests run only inside the R2 POC root; runtime artifacts go to pytest
tmp dirs.  No real-project paths, credentials, or network are permitted.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from mm_r2.artifacts import ArtifactStore  # noqa: E402
from mm_r2.acceptance import AcceptanceService  # noqa: E402

LOCAL_TEST_USER = "local_test_user"


@pytest.fixture
def r2_artifact_store(tmp_path):
    """Fresh content-addressed artifact store under the pytest tmp dir."""
    store = ArtifactStore(tmp_path / "artifacts")
    yield store


@pytest.fixture
def r2_acceptance_service():
    """Fresh in-memory acceptance service initialized with the current local
    OS user (synthetic fixture name in tests)."""
    return AcceptanceService(local_user=LOCAL_TEST_USER)
