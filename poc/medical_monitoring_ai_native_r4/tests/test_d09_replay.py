"""R4-D09 deterministic replay, order-insensitivity, identity stability and
anti-overfit tests.

* double replay: every one of the 179 typed inputs evaluated twice yields
  byte-identical leaf sets (deterministic; no wall-clock/PID/mtime input);
* input ordering: shuffling the semantically inert collection sections
  (members, coverage, matched counterevidence refs, source verification
  records, evidence refs) never changes the outcome; ``analysis_windows``
  is excluded because the last window is identity-bearing;
* canonical permutations: members and source revisions (permuted together
  with their paired content hashes and verification records) keep the exact
  leaves, the evaluation-content identity, the Query draft identity and the
  R2 idempotency key;
* run/snapshot swaps: never change public/evaluation/R2 stable identities
  and never change any leaf (the handoff's audit refs update by design);
* surface renames: display labels, lexicon Chinese forms and envelope ids
  keep every leaf identical;
* versioned identity changes: meaningful authority/rule/window/source/
  stratum content changes change the appropriate versioned identity while
  surface ids stay out of every identity;
* anti-overfit variants: all 16 frozen variants are materialized with
  surface-only change records, and run/snapshot swaps on variants keep
  their pinned oracle leaves.

The catalog/oracle/registry are read-only here; nothing is written.
Runtime tests never branch on case identifiers for semantics; case ids are
test-side catalog fixture selection only.
"""

from __future__ import annotations

import json
import random
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d09_evaluator import evaluate  # noqa: E402
from mm_r4.d09_projection import (  # noqa: E402
    build_d09_query_draft,
    build_d09_r2_handoff,
    d09_evaluation_content_identity,
    d09_public_risk_identity,
)

from test_d09_adapter import (  # noqa: E402
    assemble_leaf_sets,
    case_index,
    load_artifacts,
    run_case,
)
from test_d09_runtime_contract import (  # noqa: E402
    _base_typed_input,
    _risk,
    _sha,
)

# Collections whose element order is semantically inert.  analysis_windows
# is excluded: the LAST window feeds the stable core / evaluation window
# identity, so its order is semantic.
_ORDER_INERT_COLLECTIONS = (
    "subject_risk_members", "gap_members", "change_ledger_members",
    "coverage", "matched_counterevidence_rule_refs",
    "source_verification_records", "evidence_refs",
)


def _leaves(case: dict) -> dict:
    typed, result = run_case(case)
    return _typed_leaves(typed, result, case_index(case))


def _typed_leaves(typed, result, idx: int) -> dict:
    leaf, trace, source = assemble_leaf_sets(typed, result, idx)
    return {"expected_leaf_set": leaf, "expected_trace_leaf_set": trace,
            "expected_source_leaf_set": source}


def _pair(**overrides: Any):
    """Locally constructed (typed, result); valid by construction."""
    typed = _base_typed_input(**overrides)
    return typed, evaluate(typed)


def _positive_pair(**overrides: Any):
    return _pair(subject_risk_members=(
        _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")),
        **overrides)


class TestRunReplayDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()

    def test_double_replay_is_byte_identical(self) -> None:
        for case in self.catalog["cases"]:
            first = _leaves(case)
            second = _leaves(case)
            self.assertEqual(
                json.dumps(first, ensure_ascii=False, sort_keys=True),
                json.dumps(second, ensure_ascii=False, sort_keys=True),
                case["case_id"])

    def test_revision_export_order_family_materialized(self) -> None:
        family = [c for c in self.catalog["cases"]
                  if c.get("family_id") == "d09_revision_export_order"]
        self.assertGreaterEqual(len(family), 8)
        classes = {c["typed_input"]["mutation_context"]["mutation_class"]
                   for c in family}
        self.assertTrue({"revision_repeat", "export_repeat", "order_shuffle",
                         "display_rename"} <= classes, classes)


class TestOrderInsensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()
        cls._rng = random.Random(20260815)

    def test_shuffled_collections_keep_exact_leaves(self) -> None:
        for case in self.catalog["cases"]:
            base = _leaves(case)
            for collection in _ORDER_INERT_COLLECTIONS:
                items = case["typed_input"].get(collection)
                if not items or len(items) < 2:
                    continue
                shuffled = json.loads(json.dumps(case))
                self._rng.shuffle(shuffled["typed_input"][collection])
                self.assertEqual(
                    _leaves(shuffled), base,
                    f"{case['case_id']} changed when {collection} "
                    f"order was shuffled")

    def test_paired_revision_permutation_keeps_leaves_and_identities(
            self) -> None:
        """Source revisions are permuted together with their paired content
        hashes and verification records (canonical order-insensitivity)."""
        catalog_cases = [c for c in self.catalog["cases"]
                         if len(c["typed_input"]["source_revision_set"]) > 1]
        self.assertGreaterEqual(len(catalog_cases), 2)
        for case in catalog_cases:
            base = _leaves(case)
            typed, result = run_case(case)
            base_eval_id = d09_evaluation_content_identity(typed)
            revisions = list(typed.source_revision_set)
            hashes = list(typed.source_content_hashes)
            records = list(typed.source_verification_records)
            permuted = revisions[::-1]
            order = [revisions.index(revision) for revision in permuted]
            re_typed = replace(
                typed,
                source_revision_set=tuple(permuted),
                source_content_hashes=tuple(hashes[i] for i in order),
                source_verification_records=tuple(records[i] for i in order))
            re_result = evaluate(re_typed)
            leaves = _typed_leaves(re_typed, re_result, case_index(case))
            self.assertEqual(leaves, base, case["case_id"])
            self.assertEqual(d09_evaluation_content_identity(re_typed),
                             base_eval_id, case["case_id"])

        # locally constructed 3-revision positive: leaves, Query draft
        # identity and R2 idempotency all stay stable
        base_typed, base_result = _positive_pair(
            source_revision_set=("SYN-REV-A", "SYN-REV-B", "SYN-REV-C"),
            source_content_hashes=(_sha("d09-rev:A"), _sha("d09-rev:B"),
                                   _sha("d09-rev:C")))
        permuted_typed, permuted_result = _positive_pair(
            source_revision_set=("SYN-REV-C", "SYN-REV-A", "SYN-REV-B"),
            source_content_hashes=(_sha("d09-rev:C"), _sha("d09-rev:A"),
                                   _sha("d09-rev:B")))
        self.assertEqual(
            d09_evaluation_content_identity(permuted_typed),
            d09_evaluation_content_identity(base_typed))
        base_draft = build_d09_query_draft(base_typed, base_result)
        permuted_draft = build_d09_query_draft(permuted_typed,
                                               permuted_result)
        self.assertIsNotNone(base_draft)
        self.assertIsNotNone(permuted_draft)
        assert base_draft is not None and permuted_draft is not None
        self.assertEqual(permuted_draft.query_draft_id,
                         base_draft.query_draft_id)
        self.assertEqual(permuted_draft.source_revision_refs,
                         base_draft.source_revision_refs)
        self.assertEqual(permuted_draft.content_hash, base_draft.content_hash)
        base_handoff = build_d09_r2_handoff(base_typed, base_result)
        permuted_handoff = build_d09_r2_handoff(permuted_typed,
                                                permuted_result)
        self.assertIsNotNone(base_handoff)
        self.assertIsNotNone(permuted_handoff)
        assert base_handoff is not None and permuted_handoff is not None
        self.assertEqual(permuted_handoff.idempotency_key,
                         base_handoff.idempotency_key)

    def test_member_order_shuffle_keeps_leaves_and_identities(self) -> None:
        members = (_risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2"),
                   _risk("R-3", "SYN-SUBJ-3"))
        base_typed, base_result = _pair(subject_risk_members=members)
        shuffled_typed, shuffled_result = _pair(
            subject_risk_members=(members[2], members[0], members[1]))
        base_snapshot = (_semantic_snapshot(base_result),
                         d09_evaluation_content_identity(base_typed))
        shuffled_snapshot = (_semantic_snapshot(shuffled_result),
                             d09_evaluation_content_identity(shuffled_typed))
        self.assertEqual(shuffled_snapshot, base_snapshot)
        base_draft = build_d09_query_draft(base_typed, base_result)
        shuffled_draft = build_d09_query_draft(shuffled_typed,
                                               shuffled_result)
        assert base_draft is not None and shuffled_draft is not None
        self.assertEqual(shuffled_draft.query_draft_id,
                         base_draft.query_draft_id)


class TestRunSnapshotIdentityStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()

    def test_run_snapshot_swap_keeps_leaves_and_stable_identities(self) -> None:
        typed, result = _positive_pair()
        public = d09_public_risk_identity(typed)
        evaluation = d09_evaluation_content_identity(typed)
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        swapped = replace(typed, run_ref="SYN-RUN-2",
                          snapshot_ref="SYN-SNAP-2")
        swapped_result = evaluate(swapped)
        self.assertEqual(d09_public_risk_identity(swapped), public)
        self.assertEqual(d09_evaluation_content_identity(swapped), evaluation)
        swapped_handoff = build_d09_r2_handoff(swapped, swapped_result)
        assert swapped_handoff is not None
        self.assertEqual(swapped_handoff.idempotency_key,
                         handoff.idempotency_key)
        self.assertEqual(swapped_handoff.handoff_id, handoff.handoff_id)
        # audit refs are the only handoff fields that may track the run
        self.assertEqual(swapped_handoff.run_snapshot_audit_refs,
                         ("SYN-RUN-2", "SYN-SNAP-2"))

    def test_run_snapshot_swap_keeps_exact_leaves_across_catalog(self) -> None:
        for case in self.catalog["cases"]:
            base = _leaves(case)
            typed, _ = run_case(case)
            swapped = replace(typed, run_ref=typed.run_ref + "-swapped",
                              snapshot_ref=typed.snapshot_ref + "-swapped")
            result = evaluate(swapped)
            leaves = _typed_leaves(swapped, result, case_index(case))
            self.assertEqual(leaves, base, case["case_id"])

    def test_envelope_id_swap_inert(self) -> None:
        typed, result = _positive_pair()
        swapped = replace(typed, envelope_id="SYN-ENV-OTHER")
        self.assertEqual(_semantic_snapshot(evaluate(swapped)),
                         _semantic_snapshot(result))


class TestSurfaceRenameInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()

    def test_display_labels_and_lexicon_renames_keep_exact_leaves(
            self) -> None:
        samples = ("D09-CASE-001", "D09-CASE-047", "D09-CASE-081",
                   "D09-CASE-147")
        cases = {c["case_id"]: c for c in self.catalog["cases"]}
        for cid in samples:
            case = cases[cid]
            base = _leaves(case)
            typed, _ = run_case(case)
            renamed = replace(
                typed,
                pattern_definition=replace(
                    typed.pattern_definition,
                    clinical_label_zh="renamed clinical label"),
                audience_lexicon=replace(
                    typed.audience_lexicon,
                    affected_subjects_zh="重命名受影响受试者 {n} 名",
                    center_pattern_count_zh="重命名中心模式 {n} 项",
                    coverage_zh="重命名本次可评价范围",
                    event_count_zh="重命名事件 {n} 起",
                    individual_risk_count_zh="重命名相关个体风险 {n} 条",
                    pattern_label_zh="重命名模式标签",
                    disposition_zh={"positive": "重命名发现", "negative": "重命名未发现"},
                    lifecycle_zh={"open": "重命名进行中"}),
            )
            result = evaluate(renamed)
            leaves = _typed_leaves(renamed, result, case_index(case))
            self.assertEqual(leaves, base, cid)


class TestVersionedIdentityChanges(unittest.TestCase):
    """Meaningful content changes change the appropriate versioned identity;
    surface ids never enter any identity."""

    def _identities(self, typed, result) -> Tuple[Any, ...]:
        return (d09_public_risk_identity(typed),
                d09_evaluation_content_identity(typed),
                typed.pattern_definition.pattern_definition_id,
                typed.stratum.stratum_key)

    def test_authority_definition_change_changes_evaluation_identity(
            self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        changed = replace(
            typed,
            pattern_definition=replace(
                typed.pattern_definition,
                pattern_definition_content_hash=_sha("d09-content-v1:def:other")))
        changed_evaluation = d09_evaluation_content_identity(changed)
        self.assertNotEqual(changed_evaluation, evaluation,
                            "authority/rule content change must change the "
                            "evaluation-content identity")
        self.assertEqual(d09_public_risk_identity(changed), public,
                         "public identity is revision/content-hash free")

    def test_window_content_change_changes_evaluation_identity(self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        window = typed.analysis_windows[0]
        changed = replace(
            typed,
            analysis_windows=(replace(
                window, window_contract_content_hash=_sha("other-window-contract")),))
        self.assertNotEqual(d09_evaluation_content_identity(changed),
                            evaluation)
        self.assertEqual(d09_public_risk_identity(changed), public)

    def test_window_dates_change_changes_evaluation_identity(self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        window = typed.analysis_windows[0]
        changed = replace(
            typed,
            analysis_windows=(replace(
                window, computed_window_start="2026-02-01",
                computed_window_end="2026-04-30"),))
        self.assertNotEqual(d09_evaluation_content_identity(changed),
                            evaluation)
        self.assertEqual(d09_public_risk_identity(changed), public,
                         "computed dates never enter the public identity")

    def test_source_content_change_changes_evaluation_identity(self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        changed, changed_result = _positive_pair(
            source_revision_set=("SYN-REV-1",),
            source_content_hashes=(_sha("d09-rev:SYN-REV-1-CHANGED"),))
        self.assertNotEqual(d09_evaluation_content_identity(changed),
                            evaluation)
        self.assertEqual(d09_public_risk_identity(changed), public)
        handoff = build_d09_r2_handoff(typed, result)
        changed_handoff = build_d09_r2_handoff(changed, changed_result)
        assert handoff is not None and changed_handoff is not None
        self.assertNotEqual(changed_handoff.idempotency_key,
                            handoff.idempotency_key)

    def test_stratum_hash_change_changes_evaluation_identity(self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        changed = replace(
            typed,
            stratum=replace(typed.stratum,
                            stratum_contract_content_hash=_sha("other-stratum")))
        self.assertNotEqual(d09_evaluation_content_identity(changed),
                            evaluation)
        self.assertEqual(d09_public_risk_identity(changed), public)

    def test_stratum_key_change_changes_core_and_public_identity(self) -> None:
        typed, result = _positive_pair()
        public, evaluation, _def_id, _stratum = self._identities(typed, result)
        changed = replace(typed, stratum=replace(typed.stratum,
                                                 stratum_key="site_a"))
        self.assertNotEqual(d09_evaluation_content_identity(changed),
                            evaluation)
        self.assertNotEqual(d09_public_risk_identity(changed), public)
        self.assertEqual(result.units[0].stable_core,
                         "SYN-PROJECT-1|SYN-SITE-1|SYN-DEF-1|SYN-WIN-1|"
                         "SYN-SC-1|overall")
        self.assertEqual(evaluate(changed).units[0].stable_core,
                         "SYN-PROJECT-1|SYN-SITE-1|SYN-DEF-1|SYN-WIN-1|"
                         "SYN-SC-1|site_a")


class TestAntiOverfitVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()

    def test_variants_materialized_with_surface_change_records(self) -> None:
        variants = [c for c in self.catalog["cases"]
                    if c["typed_input"].get("anti_overfit_variant")]
        self.assertGreaterEqual(len(variants), 16)
        classes = {c["typed_input"]["mutation_context"]["mutation_class"]
                   for c in variants}
        self.assertTrue({"anti_overfit_rename", "anti_overfit_shuffle"}
                        <= classes, classes)
        for case in variants:
            variant = case["typed_input"]["anti_overfit_variant"]
            self.assertTrue(variant["surface_changes"],
                            case["case_id"])

    def test_run_snapshot_swap_on_variants_keeps_oracle_leaves(self) -> None:
        """A variant's pinned leaves are immune to run/snapshot swaps (the
        anti-overfit surface plane stays replay-stable)."""
        for case in self.catalog["cases"]:
            if not case["typed_input"].get("anti_overfit_variant"):
                continue
            base = _leaves(case)
            typed, _ = run_case(case)
            swapped = replace(typed, run_ref=typed.run_ref + "-swapped",
                              snapshot_ref=typed.snapshot_ref + "-swapped")
            result = evaluate(swapped)
            leaves = _typed_leaves(swapped, result, case_index(case))
            self.assertEqual(leaves, base, case["case_id"])


def _semantic_snapshot(result: Any) -> Tuple[Any, ...]:
    """Deterministic view of a run result excluding the typed envelope ref."""
    excluded = {"typed"}
    return tuple((name, getattr(result, name))
                 for name in sorted(vars(result))
                 if name not in excluded and not name.startswith("_"))


if __name__ == "__main__":
    unittest.main()
