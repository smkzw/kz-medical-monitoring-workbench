"""Shared fixtures for R7 slice-01 ExecutionProfile / Run binding tests.

Stdlib + pytest only. Makes ``mm_r7`` importable from the POC ``src/`` tree
and pins adjacent workbench roots for boundary checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

POC_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = POC_ROOT / "src"
WORKBENCH_ROOT = POC_ROOT.parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Adjacent R1-R6 import paths (read-only for R7 bridge).
for _r in ("r6", "r5", "r4", "r3", "r3_rule_ai", "r2", "r1"):
    _r_src = WORKBENCH_ROOT / "poc" / f"medical_monitoring_ai_native_{_r}" / "src"
    if _r_src.exists() and str(_r_src) not in sys.path:
        sys.path.insert(0, str(_r_src))
_r5_tests = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r5" / "tests"
if _r5_tests.exists() and str(_r5_tests) not in sys.path:
    sys.path.insert(0, str(_r5_tests))

@pytest.fixture(scope="session")
def poc_root() -> Path:
    return POC_ROOT


@pytest.fixture(scope="session")
def workbench_root() -> Path:
    return WORKBENCH_ROOT


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "r7_profile_run.sqlite3"
