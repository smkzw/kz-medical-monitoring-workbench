"""Shared pytest fixtures for the R1 POC test suite (worker_01-owned).

All tests run only inside the POC root; runtime products go to pytest tmp dirs.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from mm_r1.store import Store  # noqa: E402


@pytest.fixture
def r1_store(tmp_path):
    """Fresh SQLite authoritative store under the pytest tmp dir."""
    store = Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts")
    yield store
    store.close()
