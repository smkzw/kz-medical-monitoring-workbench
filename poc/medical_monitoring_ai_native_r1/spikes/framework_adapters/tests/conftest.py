"""Shared pytest fixtures for the framework-adapter spike test suite.

Worker_01-owned.  Resolves both the accepted slice1 ``mm_r1`` src and the
spike ``mm_r1_spike`` src onto sys.path, and provides fresh tmp-dir-backed
stores/harnesses.  All runtime products land in pytest tmp dirs only.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve src roots: slice1 src (read-only import) + spike src (owned).
_POC_ROOT = Path(__file__).resolve().parents[3]  # .../poc/medical_monitoring_ai_native_r1
_SLICE1_SRC = _POC_ROOT / "src"
_SPIKE_SRC = _POC_ROOT / "spikes" / "framework_adapters" / "src"
for _p in (_SLICE1_SRC, _SPIKE_SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest  # noqa: E402

from mm_r1.store import Store  # noqa: E402
from mm_r1_spike.contract import ConformanceContract  # noqa: E402
from mm_r1_spike.work_events import WorkEventStore  # noqa: E402


@pytest.fixture
def slice1_src_path() -> Path:
    return _SLICE1_SRC


@pytest.fixture
def spike_src_path() -> Path:
    return _SPIKE_SRC


@pytest.fixture
def src_paths(slice1_src_path, spike_src_path):
    """PYTHONPATH prefixes for the subprocess harness (slice1 + spike src)."""
    return [slice1_src_path, spike_src_path]


@pytest.fixture
def r1_store(tmp_path):
    """Fresh authoritative slice1 SQLite Store under the pytest tmp dir."""
    store = Store(tmp_path / "authoritative.sqlite3", tmp_path / "artifacts")
    yield store
    store.close()


@pytest.fixture
def work_events(tmp_path):
    """Fresh work-event store under the pytest tmp dir."""
    store = WorkEventStore(tmp_path / "work_events.sqlite3")
    yield store
    store.close()


@pytest.fixture
def work_dir(tmp_path):
    """Fresh working directory for restart-harness persistence (DB/files)."""
    d = tmp_path / "restart_work"
    d.mkdir(parents=True, exist_ok=True)
    return d
