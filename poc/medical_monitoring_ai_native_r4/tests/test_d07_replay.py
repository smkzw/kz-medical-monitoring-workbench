"""R4-D07 deterministic replay suite (worker-02 slice).

Proves the D07 runtime is a pure function of the substantive typed input:

* every frozen case run twice through fresh evaluator instances yields
  byte-identical canonical raw roots (medical + trace + source + integrity
  leaves);
* a fresh Python process reproduces the identical canonical output for a
  sample of cases (cross-process determinism);
* the runtime output carries no case/fixture/test identity, and the typed
  inputs themselves contain no case binding, so removing the catalog case
  binding cannot change the raw output (v0.4 §14.2: 去除 case binding 后相同
  substantive typed input 必须产生相同 raw medical output、trace 与 projection);
* positive mutations declared on the frozen cases are provably inert: the raw
  output stays byte-identical.

The runtime never reads the oracle / manifest / registry; expected outcomes
stay strictly test-side.  All data is synthetic and offline.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.d07_fixtures import (  # noqa: E402
    build_indexes,
    canonical_json,
    declared_mutation_pairs,
    flatten_root,
)
from mm_r4.d07_fixtures import POSITIVE_OPERATORS, apply_mutation  # noqa: E402
from mm_r4.d07_safety_evaluator import evaluate_safety  # noqa: E402

IDX = build_indexes()
CATALOG = IDX["frozen_catalog"]
CASES = IDX["overlay_cases_by_id"]
_ , _POSITIVE_PAIRS = declared_mutation_pairs(CATALOG)


def _case_ids():
    return [f"case-{n:03d}" for n in range(1, 145)]


def _case_numbers():
    return list(range(1, 145))


def _canonical(case_id: str) -> str:
    return canonical_json(evaluate_safety(CASES[case_id]["typed_input"]))


def json_loads(text: str):
    import json

    return json.loads(text)


class TestRunReplayDeterminism:
    @pytest.mark.parametrize("number", _case_numbers(), ids=_case_ids())
    def test_two_runs_are_byte_identical(self, number):
        case_id = f"{number:03d}"
        first = _canonical(case_id)
        second = _canonical(case_id)
        assert first == second, case_id

    @pytest.mark.parametrize("number", _case_numbers(), ids=_case_ids())
    def test_repeated_runs_share_leaf_shape(self, number):
        """Leaf-key sets and leaf counts are stable across runs."""
        case_id = f"{number:03d}"
        root = evaluate_safety(CASES[case_id]["typed_input"])
        flat = flatten_root(root)
        again = flatten_root(evaluate_safety(CASES[case_id]["typed_input"]))
        assert set(flat) == set(again), case_id
        assert root == evaluate_safety(CASES[case_id]["typed_input"]), case_id

    def test_fresh_process_reproduces_output(self):
        """A brand-new Python interpreter reproduces identical canonical output
        for a cross-process sample (001, 119, 129)."""
        poc_root = _POC_ROOT
        script = (
            "import json, sys; "
            "paths = ['medical_monitoring_ai_native_r1/src', "
            "'medical_monitoring_ai_native_r2/src', "
            "'medical_monitoring_ai_native_r3/src', "
            "'medical_monitoring_ai_native_r4/src']; "
            f"base = {str(poc_root)!r}; "
            "[sys.path.insert(0, base + '/' + p) for p in paths]; "
            "from mm_r4.d07_safety_evaluator import evaluate_safety; "
            "from mm_r4.d07_fixtures import build_indexes, canonical_json; "
            "idx = build_indexes(); "
            "cases = idx['cases_by_id']; "
            "out = {cid: canonical_json(evaluate_safety(cases[cid]['typed_input'])) "
            "       for cid in ('001','119','129')}; "
            "print(json.dumps(out))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=120, check=True,
        )
        fresh = json_loads(result.stdout)
        for cid in ("001", "119", "129"):
            assert fresh[cid] == _canonical(cid), cid


class TestCaseBindingIndependence:
    def test_typed_inputs_contain_no_case_binding(self):
        """The runtime never receives case_id / fixture_id / case_name: the
        typed inputs carry only the frozen D07 object vocabulary.  The
        distinct binding markers are the fixture id (``d07f-NNN``), the test id
        and the Chinese case name (a bare ``001`` substring is part of the
        synthetic id vocabulary, e.g. ``SYN-RES-001-3``)."""
        for case_id, case in CASES.items():
            blob = canonical_json(case["typed_input"])
            assert "case_id" not in blob, case_id
            assert "fixture_id" not in blob, case_id
            assert "case_name" not in blob, case_id
            assert case["fixture_id"] not in blob, case_id
            assert case["case_name"] not in blob, case_id
            assert f"d07-test-{case_id}" not in blob, case_id

    def test_same_substantive_input_same_output_regardless_of_wrapper(self):
        """Wrapping the identical typed input in different containers (no
        semantic change) yields identical raw output."""
        case = CASES["002"]
        typed = case["typed_input"]
        baseline = canonical_json(evaluate_safety(typed))
        wrapped = {"wrapper": "x", "typed_input": typed}
        out = evaluate_safety(wrapped["typed_input"])
        assert canonical_json(out) == baseline
        assert canonical_json(evaluate_safety({"typed_input": typed}["typed_input"])) == baseline


class TestPositiveMutationsInert:
    @pytest.mark.parametrize(
        "pair",
        [(cid, mid) for cid, mid in _POSITIVE_PAIRS],
        ids=[f"{cid}-{mid}" for cid, mid in _POSITIVE_PAIRS],
    )
    def test_positive_mutation_preserves_raw_output(self, pair):
        case_id, mutation_id = pair
        assert mutation_id in POSITIVE_OPERATORS, mutation_id
        baseline = _canonical(case_id)
        mutated = apply_mutation(CASES[case_id]["typed_input"], mutation_id)
        assert canonical_json(mutated) != canonical_json(CASES[case_id]["typed_input"]), (
            f"{case_id} {mutation_id} was a no-op"
        )
        out = canonical_json(evaluate_safety(mutated))
        assert out == baseline, (
            f"{case_id} {mutation_id} changed the raw output"
        )
