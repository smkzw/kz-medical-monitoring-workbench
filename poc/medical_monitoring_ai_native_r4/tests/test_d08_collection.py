"""R4-D08 collection/import robustness from both run directories.

The required root command

    python3 -m pytest -q -p no:cacheprovider \
        poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py

must collect from the workbench root exactly as it does from the R4 POC
directory.  This test re-runs pytest in collect-only mode as a subprocess
from both directories and asserts the D08 modules import and collect
cleanly in each.

No frozen artifact is read or written here; the catalog/oracle/registry
stay untouched.
"""

from __future__ import annotations

import glob
import re
import subprocess
import sys
import unittest
from pathlib import Path

_R4_ROOT = Path(__file__).resolve().parents[1]
_WORKBENCH_ROOT = _R4_ROOT.parent.parent


def _collect(cwd: Path, targets: list) -> tuple:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--co", *targets],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=240,
    )
    combined = proc.stdout + "\n" + proc.stderr
    collected = 0
    match = re.search(r"(\d+)\s+tests? collected", combined)
    if match:
        collected = int(match.group(1))
    return proc.returncode, collected, combined[-3000:]


class TestCollectionRobustness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.d08_files = sorted(glob.glob(str(_R4_ROOT / "tests" / "test_d08_*.py")))
        cls.r4_relative = [
            str(Path("tests") / Path(f).name) for f in cls.d08_files]
        cls.root_relative = [
            str(Path("poc/medical_monitoring_ai_native_r4/tests")
                / Path(f).name)
            for f in cls.d08_files]

    def test_r4_directory_collection(self) -> None:
        code, count, tail = _collect(_R4_ROOT, self.r4_relative)
        self.assertEqual(code, 0, tail)
        self.assertGreaterEqual(count, 121, tail)

    def test_workbench_root_collection(self) -> None:
        code, count, tail = _collect(_WORKBENCH_ROOT, self.root_relative)
        self.assertEqual(code, 0, tail)
        self.assertGreaterEqual(count, 121, tail)

    def test_both_directories_collect_identical_sets(self) -> None:
        code_r4, count_r4, tail_r4 = _collect(_R4_ROOT, self.r4_relative)
        code_root, count_root, tail_root = _collect(
            _WORKBENCH_ROOT, self.root_relative)
        self.assertEqual(code_r4, 0, tail_r4)
        self.assertEqual(code_root, 0, tail_root)
        self.assertEqual(count_root, count_r4,
                         f"root {count_root} != r4 {count_r4}\n{tail_root}")


if __name__ == "__main__":
    unittest.main()
