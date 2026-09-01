"""D10 test-only frozen artifact adapter and oracle parity.

This test module is the ONLY component allowed to read the frozen D10 artifact
chain (contract / catalog / oracle / registry / quota).  It:

* pins the frozen file SHA-256 digests and refuses a stale artifact before any
  case runs;
* parses all 312 catalog ``typed_input`` envelopes into the closed typed
  objects of ``mm_r4.d10_contracts`` (via ``mm_r4.d10_adapter``);
* runs the deterministic evaluator and demands exact per-case parity against
  the independent oracle on four dimensions required by the worker_01 slice:
  disposition/gate, stable-core, trace leaf (including content identity) and
  source leaf set.

The production runtime modules (``d10_contracts.py`` / ``d10_evaluator.py``)
never import this module and never read the frozen artifacts.  The adapter is
imported by this test module only.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as adapter  # noqa: E402
from mm_r4 import d10_evaluator as evaluator  # noqa: E402


def _run_case(case: Dict[str, Any], authority: Any) -> Tuple[Any, Any]:
    typed = adapter.build_typed_input(case["typed_input"])
    return typed, evaluator.evaluate(typed, authority)


def _trace_leaf_dict(result: Any) -> Dict[str, Any]:
    leaf = result.trace[0] if result.trace else None
    return {
        "trace_kind": leaf.trace_kind if leaf else None,
        "stable_core_ref": leaf.stable_core_ref if leaf else None,
        "content_identity": leaf.content_identity if leaf else None,
        "replay_byte_equal": leaf.replay_byte_equal if leaf else None,
        "terminal_state": leaf.terminal_state if leaf else None,
    }


class TestD10FrozenArtifacts(unittest.TestCase):
    """The adapter refuses stale frozen artifacts before any case runs."""

    def test_frozen_artifact_hashes_pinned(self) -> None:
        self.assertEqual(adapter.verify_frozen_hashes(), [])

    def test_case_count_and_bijection(self) -> None:
        catalog, oracle, registry, quota = adapter.load_artifacts()
        self.assertEqual(len(catalog["cases"]), adapter.CASE_COUNT)
        self.assertEqual(catalog["case_count"], adapter.CASE_COUNT)
        self.assertEqual(len(oracle["ordered_expectations"]), adapter.CASE_COUNT)
        catalog_ids = [case["case_id"] for case in catalog["cases"]]
        oracle_ids = [entry["case_id"]
                      for entry in oracle["ordered_expectations"]]
        self.assertEqual(len(set(catalog_ids)), adapter.CASE_COUNT)
        self.assertEqual(sorted(catalog_ids), sorted(oracle_ids))

    def test_all_cases_parse_and_validate(self) -> None:
        catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        for case in catalog["cases"]:
            typed = adapter.build_typed_input(case["typed_input"])
            # validate_typed_input is invoked inside evaluate(); call it here
            # to prove the closed schema accepts every frozen envelope.
            from mm_r4.d10_contracts import validate_typed_input
            validate_typed_input(typed)


class TestD10FullOracleParity(unittest.TestCase):
    """312/312 exact disposition/gate + core/trace/source parity, zero skips,
    zero xfails, zero pinned-gap allowances."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _registry, _quota = adapter.load_artifacts()
        cls.authority_index = {
            entry["case_id"]: adapter.build_authority(entry)
            for entry in adapter.load_authority()["entries"]
        }
        cls.expectations = {
            entry["case_id"]: entry
            for entry in cls.oracle["ordered_expectations"]
        }

    def test_312_cases_exact_parity(self) -> None:
        disposition_problems: List[str] = []
        core_problems: List[str] = []
        trace_problems: List[str] = []
        source_problems: List[str] = []
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            expectation = self.expectations[cid]
            authority = self.authority_index[cid]
            _typed, result = _run_case(case, authority)

            if result.disposition_or_gate != \
                    expectation["expected_disposition_or_gate"]:
                disposition_problems.append(
                    f"{cid}: runtime={result.disposition_or_gate} "
                    f"oracle={expectation['expected_disposition_or_gate']}")

            oracle_trace = expectation["expected_trace_leaf_set"]
            runtime_trace = _trace_leaf_dict(result)
            if len(result.trace) != len(oracle_trace):
                trace_problems.append(f"{cid}: trace count {len(result.trace)} "
                                      f"!= {len(oracle_trace)}")
                continue
            for key in ("trace_kind", "stable_core_ref", "content_identity",
                        "replay_byte_equal", "terminal_state"):
                if runtime_trace[key] != oracle_trace[0][key]:
                    if key == "stable_core_ref":
                        core_problems.append(
                            f"{cid}: {runtime_trace[key]!r} != "
                            f"{oracle_trace[0][key]!r}")
                    else:
                        trace_problems.append(
                            f"{cid}.{key}: {runtime_trace[key]!r} != "
                            f"{oracle_trace[0][key]!r}")

            if adapter.result_source_leaves(result) != \
                    expectation["expected_source_leaf_set"]:
                source_problems.append(f"{cid}: source leaf set mismatch")

        self.assertEqual(disposition_problems, [],
                         f"{len(disposition_problems)} disposition diffs: "
                         f"{disposition_problems[:10]}")
        self.assertEqual(core_problems, [],
                         f"{len(core_problems)} stable-core diffs: "
                         f"{core_problems[:10]}")
        self.assertEqual(trace_problems, [],
                         f"{len(trace_problems)} trace diffs: "
                         f"{trace_problems[:10]}")
        self.assertEqual(source_problems, [],
                         f"{len(source_problems)} source diffs: "
                         f"{source_problems[:10]}")

    def test_disposition_distribution_matches_oracle(self) -> None:
        """The closed disposition/gate vocabulary is exactly covered."""
        runtime_counts: Dict[str, int] = {}
        oracle_counts: Dict[str, int] = {}
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            authority = self.authority_index[cid]
            _typed, result = _run_case(case, authority)
            runtime_counts[result.disposition_or_gate] = \
                runtime_counts.get(result.disposition_or_gate, 0) + 1
            oracle_counts[self.expectations[cid]
                          ["expected_disposition_or_gate"]] = \
                oracle_counts.get(
                    self.expectations[cid]["expected_disposition_or_gate"],
                    0) + 1
        self.assertEqual(runtime_counts, oracle_counts)


if __name__ == "__main__":
    unittest.main()
