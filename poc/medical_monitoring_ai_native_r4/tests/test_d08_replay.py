"""R4-D08 deterministic replay, order-insensitivity and anti-overfit tests.

* double replay: every one of the 233 typed inputs evaluated twice yields
  byte-identical leaf sets (deterministic, no wall-clock/PID/mtime input);
* input ordering: shuffling the collection-type sections (observed edges,
  joins, coverage, authority, raw links, record nodes, memberships,
  temporal/identity comparisons, ...) never changes the outcome -- the
  runtime compares identity sets and dictionaries, not list positions;
  the source-jump registry keeps its frozen list order, so its shuffled
  pair SET is asserted equal;
* surface renames: renaming projects/sites/runs/snapshots/versions/tables/
  file refs/field keys (the exact tokens the frozen anti-overfit variants
  change) leaves every leaf identical;
* anti-overfit variants: all 12 frozen variants evaluate to exactly the
  same leaves as their base fixtures (semantic preservation), and the
  same substantive input never maps to different medical outcomes.

The catalog/oracle/registry are read-only here; nothing is written.
"""

from __future__ import annotations

import dataclasses
import json
import random
import sys
import unittest
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
from mm_r4.d08_evaluator import evaluate  # noqa: E402

from test_d08_adapter import (  # noqa: E402
    assemble_leaf_sets,
    load_artifacts,
    run_case,
)

# Collections whose element order is semantically inert (the runtime
# compares identity sets / id-keyed dictionaries).  source_jump_registry is
# excluded: the frozen source leaf preserves its list order.
_ORDER_INERT_COLLECTIONS = (
    "record_nodes", "observed_edges", "bidirectional_joins", "coverage_status",
    "authority_bindings", "raw_links", "resolve_decisions",
    "temporal_comparisons", "identity_comparisons", "rel_instance_memberships",
    "fanout_candidate_sets", "derived_objects", "producer_consumption_bindings",
    "source_locators", "propagation_objects", "duplicate_policies",
    "identity_operands", "waiver_handoffs", "time_refs", "cardinality_specs",
    "relation_rules",
)


def _leaves(case: dict) -> dict:
    typed, result, _ = run_case(case)
    leaf, trace, source = assemble_leaf_sets(case, typed, result)
    return {"expected_leaf_set": leaf, "expected_trace_leaf_set": trace,
            "expected_source_leaf_set": source}


class TestRunReplayDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()

    def test_double_replay_is_byte_identical(self) -> None:
        for case in self.catalog["cases"]:
            first = _leaves(case)
            second = _leaves(case)
            self.assertEqual(
                json.dumps(first, ensure_ascii=False, sort_keys=True),
                json.dumps(second, ensure_ascii=False, sort_keys=True),
                case["case_id"])

    def test_replay_drift_family_materialized(self) -> None:
        drift = [c for c in self.catalog["cases"] if c["family_id"] == "replay_drift"]
        self.assertGreaterEqual(len(drift), 4)

    def test_mutation_description_invariance(self) -> None:
        """The runtime is invariant to arbitrary edits/removal/translation of
        the free-text mutation description: once the test-only adapter has
        parsed the structured facts, replacing the description with unrelated
        English prose, unrelated Chinese prose, or an empty string leaves
        every leaf identical."""
        substitutions = (
            "",
            "completely unrelated English prose describing an AE review step",
            "完全无关的中文描述，与跨表关系或修订传播没有任何关联",
        )
        for case in self.catalog["cases"]:
            typed, result, _ = run_case(case)
            base = assemble_leaf_sets(case, typed, result)
            mc = typed.mutation_context
            for prose in substitutions:
                new_mc = (dataclasses.replace(mc, mutation_description=prose)
                          if mc is not None else None)
                mutated = dataclasses.replace(typed, mutation_context=new_mc)
                re_run = evaluate(mutated)
                leaves = assemble_leaf_sets(case, mutated, re_run)
                self.assertEqual(leaves, base, case["case_id"])


class TestOrderInsensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()
        cls._rng = random.Random(20260814)

    def test_shuffled_collections_keep_exact_leaves(self) -> None:
        for case in self.catalog["cases"]:
            base = _leaves(case)
            for coll in _ORDER_INERT_COLLECTIONS:
                items = case["typed_input"].get(coll)
                if not items or len(items) < 2:
                    continue
                shuffled = json.loads(json.dumps(case))
                self._rng.shuffle(shuffled["typed_input"][coll])
                self.assertEqual(
                    _leaves(shuffled), base,
                    f"{case['case_id']} changed when {coll} order was shuffled")

    def test_source_jump_pairs_are_order_invariant_as_sets(self) -> None:
        for case in self.catalog["cases"]:
            items = case["typed_input"].get("source_jump_registry")
            if not items or len(items) < 2:
                continue
            base = _leaves(case)
            shuffled = json.loads(json.dumps(case))
            self._rng.shuffle(shuffled["typed_input"]["source_jump_registry"])
            moved = _leaves(shuffled)
            self.assertEqual(
                {json.dumps(p, ensure_ascii=False, sort_keys=True)
                 for p in moved["expected_source_leaf_set"]
                 ["source.source_jump_target_pairs"]},
                {json.dumps(p, ensure_ascii=False, sort_keys=True)
                 for p in base["expected_source_leaf_set"]
                 ["source.source_jump_target_pairs"]},
                case["case_id"])


class TestSurfaceRenameInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()

    def _rename(self, case: dict) -> dict:
        """Apply the exact token classes the frozen anti-overfit surface
        variants change (project/site/run/snapshot/versions/table/file refs/
        field keys), keeping substantive semantics."""
        renamed = json.loads(json.dumps(case))
        ti = renamed["typed_input"]

        def rename_refs(obj: dict, field: str, prefix: str) -> None:
            if field in obj and isinstance(obj[field], str) and obj[field]:
                obj[field] = prefix + obj[field]

        scope = ti.get("scope_binding") or {}
        for f in ("project_ref", "run_ref", "site_ref", "episode_key"):
            rename_refs(scope, f, "RENAMED-")
        if "snapshot_as_of" in scope:
            scope["snapshot_as_of"] = "2026-08-01T00:00:00+00:00"
        if "clinical_event_cutoff" in scope:
            scope["clinical_event_cutoff"] = "2026-07-31"
        for n in ti.get("record_nodes") or []:
            rename_refs(n["stable_record_identity"], "project_ref", "RENAMED-")
            rename_refs(n["stable_record_identity"], "site_ref", "RENAMED-")
            n["accepted_source_field_values"] = {
                ("renamed_" + k): v for k, v in
                (n.get("accepted_source_field_values") or {}).items()}
        for w in ti.get("waiver_handoffs") or []:
            for f in ("project_ref", "run_ref", "subject_ref", "site_ref"):
                rename_refs(w, f, "RENAMED-")
        for r in ti.get("raw_links") or []:
            rename_refs(r, "subject_ref", "RENAMED-")
        for loc in ti.get("source_locators") or []:
            for f in ("source_file_ref", "canonical_location"):
                rename_refs(loc, f, "renamed/")
            rename_refs(loc, "locator_kind", "renamed_")
        for a in ti.get("authority_bindings") or []:
            rename_refs(a, "authority_version", "RENAMED-")
        return renamed

    def test_surface_renames_keep_exact_leaves(self) -> None:
        samples = ("D08-CASE-001", "D08-CASE-049", "D08-CASE-203")
        cases = {c["case_id"]: c for c in self.catalog["cases"]}
        for cid in samples:
            base = _leaves(cases[cid])
            renamed = self._rename(cases[cid])
            self.assertEqual(_leaves(renamed), base, cid)


class TestAntiOverfitSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _ = load_artifacts()
        cls.by_fixture = {c["fixture_id"]: c for c in cls.catalog["cases"]}

    def test_variants_keep_base_disposition(self) -> None:
        variants = [c for c in self.catalog["cases"]
                    if c["typed_input"].get("anti_overfit_variant")]
        self.assertGreaterEqual(len(variants), 12)
        for case in variants:
            variant = case["typed_input"]["anti_overfit_variant"]
            base = self.by_fixture[variant["base_fixture_id"]]
            self.assertEqual(case["disposition"], base["disposition"],
                             f"{case['case_id']} anti-overfit changed disposition")

    def test_variants_evaluate_to_exact_base_leaves(self) -> None:
        """Same substantive semantics: the variant produces exactly the base
        fixture's leaves (surface renames and strip-only metadata never
        change the medical outcome)."""
        for case in self.catalog["cases"]:
            variant = case["typed_input"].get("anti_overfit_variant")
            if variant is None:
                continue
            base = self.by_fixture[variant["base_fixture_id"]]
            self.assertEqual(_leaves(case), _leaves(base),
                             f"{case['case_id']} diverged from its base")

    def test_same_substantive_input_same_outcome(self) -> None:
        """The frozen duplicate-substantive guarantee holds through the
        runtime: same substantive hash -> identical runtime leaves (the
        runtime executes, not just catalog dispositions)."""
        by_hash: dict = {}
        for case in self.catalog["cases"]:
            h = case["typed_input"]["mutation_context"]["substantive_input_hash"]
            by_hash.setdefault(h, set()).add(case["case_id"])
        groups = [ids for ids in by_hash.values() if len(ids) > 1]
        self.assertTrue(groups, "no duplicate-substantive groups materialized")
        by_id = {c["case_id"]: c for c in self.catalog["cases"]}
        for ids in groups:
            base = _leaves(by_id[sorted(ids)[0]])
            for cid in sorted(ids)[1:]:
                self.assertEqual(_leaves(by_id[cid]), base,
                                 f"substantive group {sorted(ids)} diverged")

    def test_variant_oracle_leaves_match(self) -> None:
        """The 233-case audit already proves this; a focused spot check keeps
        the guarantee visible here."""
        exps = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}
        for cid in ("D08-CASE-218", "D08-CASE-226", "D08-CASE-229"):
            case = next(c for c in self.catalog["cases"] if c["case_id"] == cid)
            self.assertEqual(_leaves(case)["expected_leaf_set"],
                             exps[cid]["expected_leaf_set"], cid)


if __name__ == "__main__":
    unittest.main()
