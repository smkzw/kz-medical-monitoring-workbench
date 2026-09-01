"""R4-D07 mutation suite (worker-02 slice).

Executes every mutation id *declared* on the frozen catalog (195 negative
declarations across 58 closed ids, 145 positive declarations) against the real
D07 runtime:

* negative mutations: each declared (case, id) is applied to the frozen typed
  input and must fail closed -- a pre-evaluator integrity error with no
  medical/priority/risk/Query/Journey output (v0.4 §14.2 / §15: stale/rehash,
  wrong scope/site/run/subject/cutoff, authority version, correction fork,
  identity/duplicate, unit/range/grade/CS-NCS, owner/query, priority,
  lifecycle, Journey marker/jump/payload, applicability, open D05 gate, and
  synchronized rewrite without independent authority);
* pinned integrity classes: on the 11 deliberately defective cases, a
  hash-consistent mutation of the defect dimension must reproduce the exact
  oracle-pinned error class (scope_mismatch, out_of_cutoff, stale_hash,
  correction_ambiguous, duplicate_identity, authority_mismatch,
  foreign_key_error, bijection_error);
* positive mutations: each declared positive mutation is a provably inert
  change -- the raw runtime output must stay byte-identical.

The runtime never reads the oracle / manifest / registry; expected outcomes
stay strictly test-side.  All data is synthetic and offline.
"""

from __future__ import annotations

import copy
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
    NEGATIVE_OPERATORS,
    POSITIVE_OPERATORS,
    SECTION_HASH_FIELD,
    apply_mutation,
    build_indexes,
    canonical_json,
    content_hash,
    declared_mutation_pairs,
    fail_closed_root,
    flatten_root,
    rehash_object,
)
from mm_r4.d07_safety_evaluator import evaluate_safety  # noqa: E402

IDX = build_indexes()
CATALOG = IDX["frozen_catalog"]
CASES = IDX["overlay_cases_by_id"]
EXPECTATIONS = IDX["expectations_by_id"]
NEGATIVE_PAIRS, POSITIVE_PAIRS = declared_mutation_pairs(CATALOG)

INTEGRITY_CASES = frozenset(
    {"028", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128"}
)


def _run(case_id: str, typed_input) -> dict:
    return evaluate_safety(typed_input)


def _mutated_pairs(pairs):
    return pairs


class TestNegativeMutationsFailClosed:
    @pytest.mark.parametrize(
        "pair",
        _mutated_pairs(NEGATIVE_PAIRS),
        ids=[f"{cid}-{mid}" for cid, mid in NEGATIVE_PAIRS],
    )
    def test_declared_negative_mutation_fails_closed(self, pair):
        case_id, mutation_id = pair
        assert mutation_id in NEGATIVE_OPERATORS, f"unimplemented mutation {mutation_id}"
        baseline_input = CASES[case_id]["typed_input"]
        mutated = apply_mutation(baseline_input, mutation_id)
        # The mutation must be substantive (never a no-op).
        assert content_hash(mutated) != content_hash(baseline_input), (
            f"{case_id} {mutation_id} was a no-op"
        )
        root = _run(case_id, mutated)
        assert fail_closed_root(root), (
            f"{case_id} {mutation_id} did not fail closed: "
            f"integrity_error={root.get('integrity_error')!r} "
            f"unit_count={root.get('unit_count')} "
            f"medical_leaf_count={root.get('medical_leaf_count')} "
            f"ownership={'ownership' in root} query={'query' in root} "
            f"journey={'journey' in root}"
        )

    @pytest.mark.parametrize(
        "pair",
        _mutated_pairs(NEGATIVE_PAIRS),
        ids=[f"{cid}-{mid}" for cid, mid in NEGATIVE_PAIRS],
    )
    def test_negative_mutation_emits_no_medical_units(self, pair):
        case_id, mutation_id = pair
        mutated = apply_mutation(CASES[case_id]["typed_input"], mutation_id)
        root = _run(case_id, mutated)
        flat = flatten_root(root)
        medical = [
            k for k in flat
            if not k.startswith(("trace.", "source.", "integrity."))
            and k not in {"integrity_error", "medical_leaf_count",
                          "trace_leaf_count", "source_leaf_count"}
        ]
        assert not medical or all(
            k in {"all_units_disposed", "domain_complete", "expected_set_reconciled",
                  "l0_complete", "not_evaluable_count", "open_d05_gate_count",
                  "unit_count", "unresolved_identity_count"}
            for k in medical
        ), f"{case_id} {mutation_id} leaked medical leaves: {sorted(medical)}"


# ---------------------------------------------------------------------------
# Pinned integrity classes: hash-consistent mutation of the defect dimension
# must reproduce the oracle-pinned error class on the 11 defect cases.
# ---------------------------------------------------------------------------

def _mutate_rehash(ti, section, field, value, selector=0):
    objs = ti[section] if isinstance(ti[section], list) else [ti[section]]
    obj = objs[selector]
    obj[field] = value
    rehash_object(obj, SECTION_HASH_FIELD[section])


def _probe_authority_mismatch(ti):
    _mutate_rehash(ti, "authority_bindings", "selected_version", "999")


def _probe_scope_mismatch_project(ti):
    # Case 119's envelopes already carry a wrong project ref; a *third* value
    # on the run scope keeps the cross-object inconsistency (rehash-consistent
    # mutation of the scope dimension).
    _mutate_rehash(ti, "run_scope_binding", "project_ref", "SYN-TAMPER-PROJECT")


def _probe_out_of_cutoff(ti):
    _mutate_rehash(ti, "cutoff_decisions", "admitted", False)


def _probe_stale_hash(ti):
    obj = CASES["121"]["typed_input"]["observed_results"][0]
    # Tamper without rehash: canonical-hash stage must fire stale_hash.
    ti["observed_results"][0]["result_id"] = obj["result_id"] + "-TAMPER"


def _probe_scope_mismatch_revision(ti):
    _mutate_rehash(ti, "scope_envelopes", "source_revision", "SYN-WRONG-REV")


def _probe_correction_ambiguous(ti, selector=1):
    _mutate_rehash(ti, "observed_results", "correction_status", "corrected", selector)


def _probe_duplicate_identity(ti):
    objs = ti["observed_results"]
    objs[1]["stable_source_record_id"] = objs[0]["stable_source_record_id"]
    rehash_object(objs[1], SECTION_HASH_FIELD["observed_results"])


def _probe_foreign_key_error(ti):
    _mutate_rehash(ti, "observed_results", "scope_envelope_id", "SYN-NO-SUCH-ENVELOPE")


def _probe_bijection_error(ti):
    _mutate_rehash(ti, "scope_envelopes", "record_id", "SYN-WRONG-REC-ID")


PINNED_PROBES = {
    "028": ("authority_mismatch", _probe_authority_mismatch),
    "119": ("scope_mismatch", _probe_scope_mismatch_project),
    "120": ("out_of_cutoff", _probe_out_of_cutoff),
    "121": ("stale_hash", _probe_stale_hash),
    "122": ("scope_mismatch", _probe_scope_mismatch_revision),
    "123": ("correction_ambiguous", _probe_correction_ambiguous),
    "124": ("duplicate_identity", _probe_duplicate_identity),
    "125": ("correction_ambiguous", _probe_correction_ambiguous),
    "126": ("authority_mismatch", _probe_authority_mismatch),
    "127": ("foreign_key_error", _probe_foreign_key_error),
    "128": ("bijection_error", _probe_bijection_error),
}


class TestPinnedIntegrityClasses:
    @pytest.mark.parametrize(
        "case_id",
        sorted(INTEGRITY_CASES),
        ids=[f"case-{cid}" for cid in sorted(INTEGRITY_CASES)],
    )
    def test_hash_consistent_defect_mutation_reproduces_pinned_class(self, case_id):
        pinned_class, probe = PINNED_PROBES[case_id]
        ti = copy.deepcopy(CASES[case_id]["typed_input"])
        probe(ti)
        root = _run(case_id, ti)
        assert fail_closed_root(root), (
            f"case {case_id} probe did not fail closed: "
            f"integrity_error={root.get('integrity_error')!r}"
        )
        assert root.get("integrity_error") == pinned_class, (
            f"case {case_id} expected pinned class {pinned_class!r}, "
            f"got {root.get('integrity_error')!r} at stage "
            f"{root.get('integrity', {}).get('stage')}"
        )

    def test_frozen_fixtures_themselves_pin_exact_classes(self):
        """The frozen 11 defect fixtures pin the exact class (oracle error_equals
        is exercised by the 144-case runner; here we re-assert the pins)."""
        for case_id in sorted(INTEGRITY_CASES):
            pinned = EXPECTATIONS[case_id].get("expected_integrity_error")
            assert pinned is not None, case_id
            root = _run(case_id, CASES[case_id]["typed_input"])
            assert root.get("integrity_error") == pinned["error_type"], case_id
            assert root.get("integrity", {}).get("stage") == pinned["stage"], case_id


class TestPositiveMutationsInert:
    @pytest.mark.parametrize(
        "pair",
        [(cid, mid) for cid, mid in POSITIVE_PAIRS],
        ids=[f"{cid}-{mid}" for cid, mid in POSITIVE_PAIRS],
    )
    def test_positive_mutation_preserves_raw_output(self, pair):
        case_id, mutation_id = pair
        assert mutation_id in POSITIVE_OPERATORS, mutation_id
        baseline_input = CASES[case_id]["typed_input"]
        baseline = canonical_json(_run(case_id, baseline_input))
        mutated = apply_mutation(baseline_input, mutation_id)
        assert content_hash(mutated) != content_hash(baseline_input), (
            f"{case_id} {mutation_id} was a no-op"
        )
        assert canonical_json(_run(case_id, mutated)) == baseline, (
            f"{case_id} {mutation_id} changed the raw output"
        )


class TestMutationOperatorCoverage:
    def test_every_declared_negative_id_has_an_operator(self):
        declared = {mid for _, mid in NEGATIVE_PAIRS}
        assert declared <= set(NEGATIVE_OPERATORS)
        missing = declared - set(NEGATIVE_OPERATORS)
        assert not missing, sorted(missing)

    def test_every_declared_positive_id_has_an_operator(self):
        declared = {mid for _, mid in POSITIVE_PAIRS}
        assert declared <= set(POSITIVE_OPERATORS)

    def test_closed_negative_vocabulary_matches_frozen_registry(self):
        declared = sorted({mid for _, mid in NEGATIVE_PAIRS})
        # Every declared negative id must be class-annotated in the operator
        # table.  The table additionally carries the two contract §14.2 wrong
        # scope/run classes the frozen catalog does not declare
        # (N-WRONG-RUN, N-WRONG-EPISODE), kept as documented operators.
        assert set(declared) <= set(NEGATIVE_OPERATORS)
        assert set(NEGATIVE_OPERATORS) - set(declared) == {
            "N-WRONG-EPISODE", "N-WRONG-RUN"
        }
