"""R4-D08 independent verifier probe regressions (follow-up 2).

Each test reproduces one verifier finding against the typed runtime and
asserts the remediated behavior.  All inputs are self-contained synthetic
typed inputs (or catalog-derived via the adapter); the frozen catalog/
oracle/registry are read-only here.

Probes covered:

* P0 global ordered fail-closed: snapshot mismatch, single-subject spine
  mismatch, authority locator gap, node hash/locator/correction gaps,
  producer-binding scope gap and an empty bundle emit ONLY the first
  integrity error -- never a unit, never risk/Query/Journey; missing
  required producer coverage stays unit-level not_evaluable (frozen oracle
  cases 005/017/185/210/211 pin that shape);
* P1 propagation: actual_consumed_revision vs source vs declared;
  missing derived objects are detected by reference resolution (the
  verifier probe actual=REV5 / source=declared=REV4 / no derived object
  must NOT return in-sync negative);
* P1 temporal direction: point/interval is contained_by and interval/point
  is contains in temporal_matrix, without relying on the other family's
  flip;
* P1 reverse conservation: one forward + two duplicate reverse edges is
  NOT conserved; missing/extra/wrong-pair/equality cases;
* P1 visibility: projectable intersecting blinded/forbidden is a typed
  conflict -- disclosure_leak_present is true, hidden nodes are subtracted
  from every audience payload, and no hidden source/evidence/jump leaks;
* P2 sentinel-free runtime: the evaluator contains no synthetic sentinel
  values (``SRC-REV-000``, ``SYN-STABLE-MISSING-000``, all-zero hash);
* P2 anti-overfit: same substantive input executes the runtime with equal
  leaves; exhaustive strip-only surface renaming preserves exact leaves
  across all 233 cases.
"""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC,
             Path(__file__).resolve().parent):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d08_contracts import (  # noqa: E402
    D08TypedInput,
    INTEGRITY_ERROR_CLASSES,
    d08_content_hash,
)
from mm_r4.d08_evaluator import (  # noqa: E402
    D08IntegrityFailure,
    evaluate,
)
from mm_r4.d08_projection import (  # noqa: E402
    build_d08_query_draft,
    build_d08_risk_marker,
    project_d08_audience,
)

from test_d08_adapter import (  # noqa: E402
    assemble_leaf_sets,
    load_artifacts,
    run_case,
)
from test_d08_runtime_contract import (  # noqa: E402
    _node,
    _rule,
    _card,
    _typed,
)


def _leaves(case: dict) -> dict:
    typed, result, _ = run_case(case)
    leaf, trace, source = assemble_leaf_sets(case, typed, result)
    return {"expected_leaf_set": leaf, "expected_trace_leaf_set": trace,
            "expected_source_leaf_set": source}


class TestGlobalFailClosedProbes(unittest.TestCase):
    """P0: ordered pre-evaluator integrity checks for every family."""

    def test_snapshot_mismatch_on_explicit_link_fails_closed(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-2", snapshot="SYN-SNAP-2")]))
        self.assertEqual(
            r.integrity_error,
            D08IntegrityFailure("snapshot_identity_mismatch", "SYN-REC-2",
                                "run_snapshot_identity"))
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)
        self.assertFalse(r.risk_candidate_present)

    def test_single_subject_spine_mismatch_fails_closed(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", subject="SYN-SUBJECT-2")]))
        self.assertEqual(r.integrity_error.error_type,
                         "subject_spine_identity_mismatch")
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)

    def test_authority_locator_gap_fails_closed(self) -> None:
        r = evaluate(_typed(relation_rules=[
            {**_rule("SYN-RULE-1", "explicit_link", producers=("D02",)),
             "authority_locator_id": "SYN-AUTH-MISSING"}]))
        self.assertEqual(r.integrity_error.error_type,
                         "authority_locator_missing")
        self.assertEqual(r.units, ())

    def test_node_hash_locator_correction_gaps_fail_closed(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", content_hash="0" * 64),
            _node("SYN-REC-2", "SYN-STABLE-2")]))
        self.assertEqual(r.integrity_error.error_type,
                         "node_content_hash_mismatch")
        r2 = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", locators=()),
            _node("SYN-REC-2", "SYN-STABLE-2")]))
        self.assertEqual(r2.integrity_error.error_type, "node_locator_missing")
        # absent correction chain (structured None fact via the adapter's
        # sentinel translation) -> correction_chain_incomplete, fail-closed
        r3 = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1",
                  chain="SYN-STABLE-MISSING-000"),
            _node("SYN-REC-2", "SYN-STABLE-2")]))
        self.assertEqual(r3.integrity_error.error_type,
                         "correction_chain_incomplete")
        self.assertEqual(r3.units, ())

    def test_producer_binding_scope_gap_fails_closed(self) -> None:
        r = evaluate(_typed(producer_consumption_bindings=[{
            "binding_id": "SYN-BIND-1", "producer_object_id": "SYN-PROD-1",
            "producer_object_hash": d08_content_hash("p"),
            "producer_version": "SYN-PV-1", "purpose": "derive",
            "permitted_outputs": ["derived_value"], "scope_equality": False}]))
        self.assertEqual(r.integrity_error.error_type,
                         "producer_binding_scope_mismatch")
        self.assertEqual(r.units, ())

    def test_empty_bundle_never_becomes_positive(self) -> None:
        r = evaluate(D08TypedInput())
        self.assertIsNotNone(r.integrity_error)
        self.assertEqual(r.integrity_error.error_type,
                         "evaluator_admission_empty")
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)

    def test_missing_required_coverage_unit_level_not_evaluable(self) -> None:
        """Frozen oracle pins the coverage gap as unit-level not_evaluable in
        regular families (cases 005/017/185/210/211): admitted stage, one
        not_evaluable unit, no risk."""
        r = evaluate(_typed(coverage_status=[
            {"producer_domain": "D02", "l0_status": "covered",
             "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]},
            {"producer_domain": "D01", "l0_status": "missing",
             "accepted_current": False, "coverage_locator_ids": ["SYN-LOC-1"]},
        ]))
        self.assertIsNone(r.integrity_error)
        self.assertEqual(len(r.units), 1)
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "producer_l0_missing")
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)

    def test_no_units_and_no_risk_on_any_global_probe(self) -> None:
        probes = [
            _typed(record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1"),
                _node("SYN-REC-2", "SYN-STABLE-2", snapshot="SYN-SNAP-2")]),
            _typed(record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1", subject="SYN-SUBJECT-2")]),
            _typed(relation_rules=[
                {**_rule("SYN-RULE-1", "explicit_link", producers=("D02",)),
                 "authority_locator_id": "SYN-AUTH-MISSING"}]),
        ]
        for typed in probes:
            r = evaluate(typed)
            self.assertIsNotNone(r.integrity_error)
            self.assertEqual(r.units, ())
            self.assertFalse(r.risk_present)
            self.assertFalse(r.query_present)
            self.assertFalse(r.journey_marker_present)


class TestPropagationProbes(unittest.TestCase):
    """P1: declared/actual/source revision comparison; reference-resolved
    missing derived objects."""

    def _prop(self, *, actual: str = "SRC-REV-5",
              source: str = "SRC-REV-4", declared: str = "SRC-REV-4",
              source_node: str = "SYN-REC-1",
              derived: list | None = None) -> D08TypedInput:
        return _typed(
            relation_rules=[_rule("SYN-RULE-PROP-1", "modification_propagation",
                                  producers=("D06",))],
            coverage_status=[{"producer_domain": "D06", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            record_nodes=[_node("SYN-REC-1", "SYN-STABLE-1",
                                revision="SRC-REV-4")],
            observed_edges=[], bidirectional_joins=[],
            propagation_objects=[{
                "propagation_id": "SYN-PROP-1",
                "source_record_node_id": source_node,
                "change_cause": "data",
                "source_revision": source,
                "declared_consumed_revision": declared,
                "actual_consumed_revision": actual,
                "changed_fields": ["dose_amount"],
                "consumed_field_intersection": ["dose_amount"],
                "derived_object_id": "SYN-DERIVED-1",
                "derived_object_type": "producer_declared_derived_value",
                "lineage_fingerprint": "lg-SYN-PROP-1",
                "lineage_fingerprint_state": "intact",
                "old_derived_object_ref": "", "new_derived_object_ref": ""}],
            derived_objects=(
                derived if derived is not None else [{
                    "derived_object_id": "SYN-DERIVED-1",
                    "derived_object_type": "producer_declared_derived_value",
                    "producer_object_id": "SYN-PROD-1",
                    "producer_version": "SYN-PV-1",
                    "producer_hash": d08_content_hash("d"),
                    "declared_consumed_revision": declared,
                    "source_locator_ids": ["SYN-LOC-1"]}]))

    def test_actual_mismatch_with_present_derived_is_stale(self) -> None:
        """actual=REV5 while source=declared=REV4 and the derived object
        resolves: the propagation is stale, never in-sync."""
        r = evaluate(self._prop())
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].propagation_result, "stale")
        self.assertEqual(r.units[0].primary_reason,
                         "actual_consumed_revision_mismatch")

    def test_verifier_probe_missing_derived_not_in_sync(self) -> None:
        """Verifier probe: actual=REV5, source=declared=REV4, NO derived
        object -> must NOT return in-sync negative."""
        typed = self._prop(derived=[])
        r = evaluate(typed)
        self.assertNotEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].propagation_result, "derived_missing")
        self.assertEqual(r.units[0].primary_reason, "derived_missing")

    def test_missing_derived_without_obligation_is_no_obligation(self) -> None:
        """source == declared == actual and no derived object: no revision
        obligation -> in-sync no_obligation (frozen case 141 shape)."""
        typed = self._prop(actual="SRC-REV-4", derived=[])
        r = evaluate(typed)
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].propagation_result, "in_sync")
        self.assertEqual(r.units[0].primary_reason, "no_obligation")

    def test_source_record_node_reference_must_resolve(self) -> None:
        """source_record_node_id is a structured reference: an unresolvable
        reference makes the unit producer_not_evaluable (no silent pass)."""
        typed = self._prop(source_node="SYN-REC-MISSING")
        r = evaluate(typed)
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].propagation_result,
                         "producer_not_evaluable")
        self.assertEqual(r.units[0].primary_reason,
                         "source_record_node_missing")


class TestTemporalDirectionProbes(unittest.TestCase):
    """P1: point/interval and interval/point directions in temporal_matrix
    (no reliance on the temporal_impossibility flip)."""

    def _matrix(self, comparisons: list, time_refs: list) -> D08TypedInput:
        return _typed(
            relation_rules=[_rule("SYN-RULE-TEMP-1", "temporal_matrix",
                                  producers=("D02",))],
            coverage_status=[{"producer_domain": "D02", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            observed_edges=[], bidirectional_joins=[],
            temporal_comparisons=comparisons,
            time_refs=time_refs)

    def _cmp(self, left: str, right: str, expected: str,
             allowed: tuple = ()) -> dict:
        return {
            "comparison_id": "SYN-CMP-1", "left_time_ref_id": left,
            "right_time_ref_id": right, "expected_relation": expected,
            "allowed_relation_set": list(allowed),
            "left_endpoint_openness": "closed",
            "right_endpoint_openness": "closed",
            "timezone_state": "present", "precision_level": "day",
            "relation_rule_id": "SYN-RULE-TEMP-1",
        }

    def _refs(self) -> list:
        return [
            {"time_ref_id": "T-INT", "value": "2026-03-01",
             "end_value": "2026-03-20", "precision": "day",
             "kind": "interval", "timezone_state": "present",
             "source_locator_ids": ["SYN-LOC-1"]},
            {"time_ref_id": "T-PT", "value": "2026-03-10",
             "precision": "day", "kind": "point",
             "timezone_state": "present",
             "source_locator_ids": ["SYN-LOC-1"]},
            {"time_ref_id": "T-BEFORE", "value": "2026-02-01",
             "precision": "day", "kind": "point",
             "timezone_state": "present",
             "source_locator_ids": ["SYN-LOC-1"]},
        ]

    def test_point_inside_interval_is_contained_by(self) -> None:
        """point/interval: the point inside the interval observes
        contained_by; expected contained_by is negative (no flip)."""
        r = evaluate(self._matrix(
            [self._cmp("T-PT", "T-INT", "contained_by")], self._refs()))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].temporal_relation, "contained_by")

    def test_point_inside_interval_expected_contains_is_positive(self) -> None:
        r = evaluate(self._matrix(
            [self._cmp("T-PT", "T-INT", "contains")], self._refs()))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].temporal_relation, "contained_by")
        self.assertEqual(r.units[0].primary_reason, "observed_contained_by")

    def test_interval_containing_point_is_contains(self) -> None:
        """interval/point: the interval containing the point observes
        contains; expected contains is negative."""
        r = evaluate(self._matrix(
            [self._cmp("T-INT", "T-PT", "contains")], self._refs()))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].temporal_relation, "contains")

    def test_interval_containing_point_expected_contained_by_positive(self) -> None:
        r = evaluate(self._matrix(
            [self._cmp("T-INT", "T-PT", "contained_by")], self._refs()))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].temporal_relation, "contains")

    def test_point_before_interval_is_before(self) -> None:
        r = evaluate(self._matrix(
            [self._cmp("T-BEFORE", "T-INT", "before")], self._refs()))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].temporal_relation, "before")

    def test_point_after_interval_is_after(self) -> None:
        refs = self._refs()
        refs.append({"time_ref_id": "T-AFTER", "value": "2026-04-01",
                     "precision": "day", "kind": "point",
                     "timezone_state": "present",
                     "source_locator_ids": ["SYN-LOC-1"]})
        r = evaluate(self._matrix(
            [self._cmp("T-AFTER", "T-INT", "after")], refs))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].temporal_relation, "after")


class TestReverseConservationProbes(unittest.TestCase):
    """P1: exact bidirectional identity-set and cardinality constraints."""

    def _link(self, edges: list, card: dict | None = None) -> D08TypedInput:
        return _typed(
            relation_rules=[_rule("SYN-RULE-REV-1", "reverse_cardinality")],
            cardinality_specs=[card] if card else [_card(reverse=True)],
            observed_edges=edges,
            bidirectional_joins=[])

    def _edge(self, eid: str, left: str, right: str,
              direction: str = "forward") -> dict:
        return {"edge_id": eid, "relation_rule_id": "SYN-RULE-REV-1",
                "direction": direction, "edge_directionality": "directed",
                "left_stable_identity": left, "right_stable_identity": right,
                "explicit_rel_instance_id": "", "recorded_operands": []}

    _S1 = "SYN-STABLE-1"
    _S2 = "SYN-STABLE-2"

    def test_one_forward_two_duplicate_reverse_not_conserved(self) -> None:
        """Verifier probe: one forward + two duplicate reverse edges cannot
        be conserved negative."""
        r = evaluate(self._link([
            self._edge("E1", self._S1, self._S2),
            self._edge("E2", self._S2, self._S1, direction="reverse"),
            self._edge("E3", self._S2, self._S1, direction="reverse"),
        ]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "reverse_missing")
        self.assertFalse(r.reverse_conservation_ok)

    def test_missing_reverse_not_conserved(self) -> None:
        r = evaluate(self._link([self._edge("E1", self._S1, self._S2)]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "reverse_missing")

    def test_extra_reverse_not_conserved(self) -> None:
        r = evaluate(self._link([
            self._edge("E1", self._S1, self._S2),
            self._edge("E2", self._S2, self._S1, direction="reverse"),
            self._edge("E3", self._S1, self._S2, direction="reverse"),
        ]))
        self.assertEqual(r.units[0].l1_disposition, "positive")

    def test_wrong_pair_not_conserved(self) -> None:
        r = evaluate(self._link([
            self._edge("E1", self._S1, self._S2),
            self._edge("E2", self._S1, self._S2, direction="reverse"),
        ]))
        self.assertEqual(r.units[0].l1_disposition, "positive")

    def test_equal_conserved_negative(self) -> None:
        r = evaluate(self._link([
            self._edge("E1", self._S1, self._S2),
            self._edge("E2", self._S2, self._S1, direction="reverse"),
        ]))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].primary_reason, "conserved")
        self.assertTrue(r.reverse_conservation_ok)

    def test_join_identity_set_mismatch_not_conserved(self) -> None:
        typed = _typed(
            relation_rules=[_rule("SYN-RULE-REV-1", "reverse_cardinality")],
            cardinality_specs=[_card(reverse=True)],
            observed_edges=[
                self._edge("E1", self._S1, self._S2),
                self._edge("E2", self._S2, self._S1, direction="reverse"),
            ],
            bidirectional_joins=[{
                "join_id": "SYN-JOIN-1", "relation_rule_id": "SYN-RULE-REV-1",
                "forward_edge_refs": ["E1"], "reverse_edge_refs": ["E2"],
                "forward_identity_set": ["SYN-STABLE-WRONG"],
                "reverse_identity_set": [self._S1]}])
        r = evaluate(typed)
        self.assertEqual(r.units[0].l1_disposition, "positive")


class TestVisibilityConflictProbes(unittest.TestCase):
    """P1: projectable intersecting blinded/forbidden is a typed conflict."""

    def _conflicted(self) -> D08TypedInput:
        return _typed(visibility_decision={
            "visibility_decision_id": "SYN-VIS-1",
            "audience_anchor_rule": "obligation_side",
            "audience_lexicon_ref": "SYN-LEX-1",
            "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "projectable_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "blinded_node_ids": ["SYN-REC-2"],
            "forbidden_node_ids": []})

    def test_conflict_sets_disclosure_leak_and_subtracts(self) -> None:
        typed = self._conflicted()
        r = evaluate(typed)
        self.assertTrue(r.disclosure_leak_present)
        self.assertNotIn("SYN-REC-2", r.projectable_node_set)
        self.assertEqual(r.hidden_node_count, 1)
        projection = project_d08_audience(typed, r)
        self.assertNotIn("SYN-REC-2", projection.audience_source_nodes)
        for _, left, right in projection.relation_edges:
            self.assertNotIn("SYN-REC-2", (left, right))

    def test_no_hidden_in_query_evidence_or_jumps(self) -> None:
        typed = self._conflicted()
        r = evaluate(typed)
        draft = build_d08_query_draft(typed, r)
        if draft is not None:
            self.assertNotIn("SYN-REC-2", draft["evidence_refs"])
        marker = build_d08_risk_marker(typed, r)
        if marker is not None:
            locators = marker.source_locator_ids
            self.assertNotIn("SYN-REC-2", str(locators))

    def test_consistent_input_no_leak(self) -> None:
        typed = _typed()  # projectable == evaluation, no hidden
        r = evaluate(typed)
        self.assertFalse(r.disclosure_leak_present)
        self.assertEqual(r.projectable_node_set, ("SYN-REC-1", "SYN-REC-2"))


class TestSentinelFreeRuntime(unittest.TestCase):
    """P2: no synthetic sentinel coupling in the runtime."""

    def test_evaluator_has_no_synthetic_sentinels(self) -> None:
        path = Path(__file__).resolve().parents[1] / "src/mm_r4/d08_evaluator.py"
        src = path.read_text(encoding="utf-8")
        for token in ("SRC-REV-000", "SYN-STABLE-MISSING-000", '"0" * 64'):
            self.assertNotIn(token, src, token)

    def test_invariant_to_value_renames(self) -> None:
        """The runtime branches only on revision equality/inequality, never on
        literal values: renaming every revision token consistently preserves
        the outcome (no sentinel literals in decision logic)."""
        case = json.loads(json.dumps(next(
            c for c in load_artifacts()[0]["cases"]
            if c["case_id"] == "D08-CASE-049")))
        original = _leaves(case)

        def rename_revs(obj):
            if isinstance(obj, dict):
                for k, v in list(obj.items()):
                    if k in ("source_revision", "declared_consumed_revision",
                             "actual_consumed_revision") and isinstance(v, str):
                        obj[k] = "REV-" + v
                    else:
                        rename_revs(v)
            elif isinstance(obj, list):
                for item in obj:
                    rename_revs(item)

        rename_revs(case["typed_input"])
        self.assertEqual(_leaves(case), original)


class TestFinalVerifierGapProbes(unittest.TestCase):
    """Regression probes from the verifier's second REVISE pass."""

    def test_missing_and_not_current_required_coverage_block(self) -> None:
        for coverage in (
            [{"producer_domain": "D02", "l0_status": "covered",
              "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]}],
            [{"producer_domain": "D02", "l0_status": "covered",
              "accepted_current": False, "coverage_locator_ids": ["SYN-LOC-1"]},
             {"producer_domain": "D01", "l0_status": "covered",
              "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]}],
        ):
            result = evaluate(_typed(coverage_status=coverage))
            self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
            self.assertFalse(result.risk_present)
            self.assertFalse(result.query_present)

    def test_project_site_and_shared_spine_mismatch_fail_closed(self) -> None:
        site_result = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", site="OTHER-SITE")]))
        self.assertEqual(site_result.integrity_error.error_type,
                         "subject_spine_identity_mismatch")
        spine_result = evaluate(_typed(shared_spine_binding={
            "shared_spine_ref": "SYN-SPINE-1",
            "scope_equality_decision": "not_equal"}))
        self.assertEqual(spine_result.integrity_error.error_type,
                         "subject_spine_identity_mismatch")

    def test_authority_and_record_hash_binding_are_verified(self) -> None:
        typed = _typed()
        bad_authority = replace(typed.authority_bindings[0],
                                authority_hash=d08_content_hash("wrong"))
        result = evaluate(replace(typed, authority_bindings=(bad_authority,)))
        self.assertEqual(result.integrity_error.error_type, "authority_hash_mismatch")
        bad_node = replace(typed.record_nodes[0], content_hash=d08_content_hash("wrong"))
        result = evaluate(replace(typed, record_nodes=(bad_node,) + typed.record_nodes[1:]))
        self.assertEqual(result.integrity_error.error_type, "node_content_hash_mismatch")

    def test_right_min_and_nary_bijection_are_enforced(self) -> None:
        typed = _typed(cardinality_specs=[{
            **_card(reverse=True, bidirectional=True), "right_min": 2,
        }], observed_edges=[
            {"edge_id": "E1", "relation_rule_id": "SYN-RULE-1",
             "direction": "forward", "edge_directionality": "directed",
             "left_stable_identity": "SYN-STABLE-1",
             "right_stable_identity": "SYN-STABLE-2",
             "explicit_rel_instance_id": "", "recorded_operands": []},
            {"edge_id": "E2", "relation_rule_id": "SYN-RULE-1",
             "direction": "reverse", "edge_directionality": "directed",
             "left_stable_identity": "SYN-STABLE-2",
             "right_stable_identity": "SYN-STABLE-1",
             "explicit_rel_instance_id": "", "recorded_operands": []},
        ], bidirectional_joins=[])
        self.assertEqual(evaluate(typed).units[0].l1_disposition, "positive")

        catalog = load_artifacts()[0]
        case = next(c for c in catalog["cases"] if c["case_id"] == "D08-CASE-012")
        nary = run_case(case)[0]
        membership = nary.rel_instance_memberships[0]
        broken = replace(membership, raw_link_bijection=dict(
            list(membership.raw_link_bijection.items())[:-1]))
        result = evaluate(replace(nary, rel_instance_memberships=(broken,)))
        self.assertEqual(result.units[0].l1_disposition, "positive")

    def test_rmb_window_exclusion_is_not_applicable(self) -> None:
        rule = _rule("SYN-RULE-RMB-1", "raw_materialized_resolve")
        rule["applicability_window"] = {
            "window_kind": "rule_window", "start": "2025-01-01",
            "end": "2025-12-31"}
        result = evaluate(_typed(relation_rules=[rule]))
        self.assertEqual(result.units[0].l1_disposition, "not_applicable")
        self.assertEqual(result.units[0].primary_reason, "window_excludes")

    def test_hidden_jump_and_locator_do_not_project(self) -> None:
        typed = _typed(
            cardinality_specs=[_card(reverse=True, bidirectional=True)],
            record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1", locators=("SYN-LOC-1",)),
                _node("SYN-REC-2", "SYN-STABLE-2", locators=("SYN-LOC-2",)),
            ],
            visibility_decision={
                "visibility_decision_id": "SYN-VIS-1",
                "audience_anchor_rule": "obligation_side",
                "audience_lexicon_ref": "SYN-LEX-1",
                "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
                "projectable_node_set": ["SYN-REC-1"],
                "blinded_node_ids": ["SYN-REC-2"], "forbidden_node_ids": []},
            source_jump_registry=[{
                "jump_target_id": "J-HIDDEN", "target_kind": "record_node",
                "target_object_id": "SYN-REC-2", "source_locator_ids": ["SYN-LOC-2"]}],
            source_locators=[
                {"source_locator_id": "SYN-LOC-1", "source_file_ref": "a",
                 "canonical_location": "a#1", "locator_kind": "synthetic_file",
                 "content_hash": d08_content_hash("1")},
                {"source_locator_id": "SYN-LOC-2", "source_file_ref": "a",
                 "canonical_location": "a#2", "locator_kind": "synthetic_file",
                 "content_hash": d08_content_hash("2")},
            ])
        result = evaluate(typed)
        self.assertEqual(result.source_jump_target_pairs, ())
        draft = build_d08_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        draft["source_locator_ids"] = ["SYN-LOC-2"]
        validation = __import__(
            "mm_r4.d08_projection", fromlist=["validate_query_draft"]
        ).validate_query_draft(draft, typed, result)
        self.assertIn("source_locator_not_projectable", validation["reasons"])

    def test_over_limit_positive_forbidden_edge_is_positive(self) -> None:
        typed = _typed(
            relation_rules=[_rule("CUSTOM-RULE-OVER", "reverse_cardinality")],
            cardinality_specs=[_card(overmatch="positive_forbidden_edge")],
            observed_edges=[
                {"edge_id": "E1", "relation_rule_id": "CUSTOM-RULE-OVER",
                 "direction": "forward", "edge_directionality": "directed",
                 "left_stable_identity": "SYN-STABLE-1",
                 "right_stable_identity": "SYN-STABLE-2",
                 "explicit_rel_instance_id": "", "recorded_operands": []},
                {"edge_id": "E2", "relation_rule_id": "CUSTOM-RULE-OVER",
                 "direction": "forward", "edge_directionality": "directed",
                 "left_stable_identity": "SYN-STABLE-1",
                 "right_stable_identity": "SYN-STABLE-2",
                 "explicit_rel_instance_id": "", "recorded_operands": []},
            ], bidirectional_joins=[])
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.units[0].primary_reason,
                         "forbidden_edge_present")

    def test_coverage_stage_precedes_bad_authority(self) -> None:
        typed = _typed(coverage_status=[
            {"producer_domain": "D02", "l0_status": "covered",
             "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]},
        ])
        bad_authority = replace(
            typed.authority_bindings[0], authority_hash=d08_content_hash("bad"))
        result = evaluate(replace(
            typed, authority_bindings=(bad_authority,)))
        self.assertIsNone(result.integrity_error)
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "producer_l0_missing")

    def test_mixed_propagation_has_one_handoff(self) -> None:
        base = TestPropagationProbes()._prop()
        rule_change = replace(
            base.propagation_objects[0], propagation_id="SYN-PROP-RULE",
            change_cause="rule_or_mapping")
        rule = replace(base.relation_rules[0], version="2")
        # Keep the signed typed rule internally consistent after changing its
        # structured version.
        rule = replace(rule, rule_hash=d08_content_hash({
            "algorithm_version": rule.algorithm_version,
            "allowed_relation_set": list(rule.allowed_relation_set),
            "applicability_window": {
                "end": rule.applicability_window.end,
                "start": rule.applicability_window.start,
                "window_kind": rule.applicability_window.window_kind,
            },
            "authority_locator_id": rule.authority_locator_id,
            "cardinality_ref": rule.cardinality_ref,
            "clinical_relationship_type": rule.clinical_relationship_type,
            "directionality": rule.directionality,
            "duplicate_policy_ref": rule.duplicate_policy_ref,
            "evidence_set_role": rule.evidence_set_role,
            "expected_relation": rule.expected_relation,
            "forbidden_relation": rule.forbidden_relation,
            "identity_operand_ids": list(rule.identity_operand_ids),
            "left_role_constraint": rule.left_role_constraint,
            "max_unidentified_fanout": rule.max_unidentified_fanout,
            "normalization_preconditions": list(rule.normalization_preconditions),
            "owner_domain": rule.owner_domain,
            "owner_routing_ref": rule.owner_routing_ref,
            "required_producer_domains": list(rule.required_producer_domains),
            "required_relation": rule.required_relation,
            "rule_hash": None,
            "rule_id": rule.rule_id,
            "shared_precision": rule.shared_precision,
            "time_operand_ids": list(rule.time_operand_ids),
            "unit_anchor_role": rule.unit_anchor_role,
            "unit_grain": rule.unit_grain,
            "version": rule.version,
        }))
        result = evaluate(replace(
            base, relation_rules=(rule,),
            propagation_objects=(base.propagation_objects[0], rule_change)))
        self.assertEqual(len(result.units), 2)
        self.assertEqual(sum(u.lineage_handoff for u in result.units), 1)

    def test_custom_rmb_rule_identity_is_retained(self) -> None:
        result = evaluate(_typed(relation_rules=[
            _rule("CUSTOM-RMB-RULE", "raw_materialized_resolve")]))
        self.assertEqual(result.units[0].relation_rule_id, "CUSTOM-RMB-RULE")

    def test_integrity_enum_and_runtime_have_no_synthetic_rule_fallbacks(self) -> None:
        self.assertIn("authority_hash_mismatch", INTEGRITY_ERROR_CLASSES)
        path = Path(__file__).resolve().parents[1] / "src/mm_r4/d08_evaluator.py"
        source = path.read_text(encoding="utf-8")
        for token in ("SYN-RULE-001", "SYN-RULE-IDM-001", "SYN-RULE-RMB-001"):
            self.assertNotIn(token, source)

    def test_integrity_matrix_global_integrity_precedes_window(self) -> None:
        rule = _rule("CUSTOM-INTEGRITY", "integrity_matrix", producers=("D02",))
        rule["applicability_window"] = {
            "window_kind": "rule_window", "start": "2025-01-01",
            "end": "2025-12-31"}
        typed = _typed(
            relation_rules=[rule],
            coverage_status=[{
                "producer_domain": "D02", "l0_status": "covered",
                "accepted_current": True,
                "coverage_locator_ids": ["SYN-LOC-1"],
            }])
        bad_node = replace(
            typed.record_nodes[0], content_hash=d08_content_hash("bad-node"))
        result = evaluate(replace(
            typed, record_nodes=(bad_node,) + typed.record_nodes[1:]))
        self.assertEqual(result.integrity_error.error_type,
                         "node_content_hash_mismatch")
        self.assertEqual(result.units, ())

    def test_projection_duplicate_stable_identity_is_deterministic_fail_closed(self) -> None:
        nodes = [
            _node("REC-A", "DUP-STABLE"),
            _node("REC-B", "DUP-STABLE"),
            _node("REC-C", "SYN-STABLE-2"),
        ]
        typed = _typed(
            relation_rules=[_rule("CUSTOM-ID", "identity_collision")],
            record_nodes=nodes,
            observed_edges=[{
                "edge_id": "EDGE-DUP", "relation_rule_id": "CUSTOM-ID",
                "direction": "forward", "edge_directionality": "directed",
                "left_stable_identity": "DUP-STABLE",
                "right_stable_identity": "SYN-STABLE-2",
                "explicit_rel_instance_id": "", "recorded_operands": [],
            }], bidirectional_joins=[])
        first = project_d08_audience(typed, evaluate(typed))
        reversed_typed = replace(typed, record_nodes=tuple(reversed(typed.record_nodes)))
        second = project_d08_audience(reversed_typed, evaluate(reversed_typed))
        self.assertEqual(first.relation_edges, ())
        self.assertEqual(first.relation_edges, second.relation_edges)

    def test_propagation_recomputes_intersection_from_derived_declaration(self) -> None:
        typed = TestPropagationProbes()._prop(actual="SRC-REV-4")
        derived = replace(typed.derived_objects[0], declared_consumed_fields=())
        claimed = replace(
            typed, derived_objects=(derived,),
            propagation_objects=(replace(
                typed.propagation_objects[0],
                consumed_field_intersection=("dose_amount",)),))
        unclaimed = replace(
            claimed, propagation_objects=(replace(
                claimed.propagation_objects[0], consumed_field_intersection=()),))
        for bundle in (claimed, unclaimed):
            result = evaluate(bundle)
            self.assertEqual(result.units[0].l1_disposition, "not_applicable")
            self.assertEqual(result.units[0].primary_reason, "intersection_empty")

    def test_rmb_raw_link_without_resolve_decision_is_not_evaluable(self) -> None:
        typed = _typed(
            relation_rules=[_rule("CUSTOM-RMB", "raw_materialized_resolve")],
            raw_links=[{
                "raw_link_id": "RAW-UNRESOLVED", "source_locator_ids": ["SYN-LOC-1"],
                "domain_id": "cm", "subject_ref": "SYN-SUBJECT",
                "idvar": "record_id", "idvarval": "SYN-REC-1",
                "reltype": "caused_by", "relid": "REL-1",
                "raw_content_hash": d08_content_hash("raw"),
            }],
            resolve_decisions=[])
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason,
                         "resolve_decision_missing")


class TestAntiOverfitStrengthened(unittest.TestCase):
    """P2: runtime-executing substantive-hash groups and exhaustive rename."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()

    def test_same_substantive_input_executes_runtime_with_equal_leaves(self) -> None:
        """Same substantive hash -> identical runtime leaves (executes the
        runtime, not just catalog dispositions)."""
        by_hash: dict = {}
        for case in self.catalog["cases"]:
            h = case["typed_input"]["mutation_context"]["substantive_input_hash"]
            by_hash.setdefault(h, []).append(case["case_id"])
        groups = [ids for ids in by_hash.values() if len(ids) > 1]
        self.assertTrue(groups, "no duplicate-substantive groups materialized")
        by_id = {c["case_id"]: c for c in self.catalog["cases"]}
        for ids in groups:
            base = _leaves(by_id[ids[0]])
            for cid in ids[1:]:
                self.assertEqual(_leaves(by_id[cid]), base, f"group {ids}")

    def test_strip_only_surface_rename_all_233_cases(self) -> None:
        """Renaming the non-substantive versioning envelope (run/snapshot/
        producer-version/authority-version/snapshot-as-of) preserves exact
        leaves across ALL 233 cases."""
        for case in self.catalog["cases"]:
            base = _leaves(case)
            renamed = json.loads(json.dumps(case))
            scope = renamed["typed_input"].get("scope_binding") or {}
            for f in ("run_ref", "accepted_snapshot_ref", "producer_version"):
                if f in scope:
                    scope[f] = "RENAMED-" + str(scope[f])
            if "snapshot_as_of" in scope:
                scope["snapshot_as_of"] = "2026-08-01T00:00:00+00:00"
            # node envelope refs must stay consistent with the scope snapshot
            for n in renamed["typed_input"].get("record_nodes") or []:
                if "accepted_snapshot_ref" in n:
                    n["accepted_snapshot_ref"] = "RENAMED-" + str(
                        n["accepted_snapshot_ref"])
            for a in renamed["typed_input"].get("authority_bindings") or []:
                if "authority_version" in a:
                    a["authority_version"] = "RENAMED-" + str(a["authority_version"])
            self.assertEqual(_leaves(renamed), base, case["case_id"])


if __name__ == "__main__":
    unittest.main()
