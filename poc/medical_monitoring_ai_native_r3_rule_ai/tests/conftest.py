"""conftest for the R3 rule-AI adapter test suite (workers 01-03).

All tests run only inside the rule-AI package root; the frozen R1/R3 packages
are placed on sys.path read-only for cross-check tests.  No real-project paths,
credentials, or network are permitted.
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PKG_SRC) not in sys.path:
    sys.path.insert(0, str(PKG_SRC))

# Frozen R3 (read-only cross-checks only).
R3_SRC = Path(__file__).resolve().parents[2] / "medical_monitoring_ai_native_r3" / "src"
if str(R3_SRC) not in sys.path:
    sys.path.insert(0, str(R3_SRC))

# Frozen R1 (read-only: adapter/capability evidence for worker_02 bridge).
R1_SRC = Path(__file__).resolve().parents[2] / "medical_monitoring_ai_native_r1" / "src"
if str(R1_SRC) not in sys.path:
    sys.path.insert(0, str(R1_SRC))
