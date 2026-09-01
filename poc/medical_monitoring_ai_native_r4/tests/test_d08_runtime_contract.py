"""R4-D08 focused runtime contract tests (self-contained synthetic inputs).

Covers the closed typed runtime contract WITHOUT reading the frozen
catalog/oracle/registry:

* typed validation: closed enums reject invalid values, waiver states are
  exactly three, bundles must be ``D08TypedInput``;
* deterministic evaluation: identical typed input yields identical units;
* pre-evaluator fail-closed order: every integrity stage stops before any
  medical/risk/Query/Journey payload and emits only the integrity gap;
* cutoff priority (section 4.1): time-missing / all-out / mixed-spans /
  propagation exemption;
* temporal relations (section 8): contains/contained_by direction,
  same-day indeterminacy, timezone and precision gaps;
* identity/duplicate semantics (section 6.1): cross-subject/site/role
  collisions, distinct/ambiguous, duplicate content, split/merge,
  mirror exemption, dedup-key mismatch;
* propagation lineage (section 10): stale/in-sync/derived-missing/
  no-obligation/intersection-empty/ambiguous-chain/producer-not-evaluable
  and the lineage-supersede handoff;
* explicit link resolve / reverse cardinality / n-ary RELID / fanout gate /
  waiver closure and consume-only zero-risk;
* runtime closure: the evaluator never imports the catalog, oracle,
  registry, generator or the acceptance tests, and never branches on
  case/test/fixture ids.

All inputs are self-contained synthetic typed inputs.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
from test_d08_adapter import parse_typed_input  # noqa: E402

from mm_r4.d08_contracts import (  # noqa: E402
    CLOSURE_STATES,
    CUTOFF_DECISIONS,
    D08ContractError,
    D08TypedInput,
    IDENTITY_DECISION_CODES,
    LINEAGE_FINGERPRINT_STATES,
    L0_STATUSES,
    RELATION_PAYLOAD_STATUSES,
    RESOLVE_STATUSES,
    TIME_PRECISIONS,
    UNIT_GRAINS,
    d08_content_hash,
    validate_typed_input,
)
from mm_r4.d08_evaluator import (  # noqa: E402
    D08IntegrityFailure,
    D08RunResult,
    evaluate,
)
from mm_r4.d08_projection import (  # noqa: E402
    build_d08_query_draft,
    build_d08_risk_marker,
    project_d08_audience,
)


def _node(node_id: str, stable_id: str, *, subject: str = "SYN-SUBJECT-1",
          site: str = "SYN-SITE-1", domain: str = "cm",
          role: str = "treatment_record", revision: str = "SRC-REV-3",
          snapshot: str = "SYN-SNAP-1", cutoff: str = "in_cutoff",
          chain: str = "SYN-CHAIN-1", locators: Tuple[str, ...] = ("SYN-LOC-1",),
          content_hash: Optional[str] = None) -> Dict[str, Any]:
    return {
        "record_node_id": node_id,
        "stable_record_identity": {
            "stable_record_id": stable_id,
            "project_ref": "SYN-PROJECT",
            "subject_ref": subject,
            "site_ref": site,
            "domain_id": domain,
            "semantic_role": role,
            "correction_chain_head": chain,
        },
        "accepted_snapshot_ref": snapshot,
        "source_revision": revision,
        "record_status": "accepted",
        "cutoff_decision": {"decision": cutoff, "reason_codes": []},
        "time_ref_ids": ["SYN-TIME-1"],
        "visit_ref_ids": [],
        "accepted_source_field_values": {},
        "unit_value_role": "record",
        "locator_ids": list(locators),
        "source_locator_ids": list(locators),
        "content_hash": content_hash or d08_content_hash(node_id),
    }


def _rule(rule_id: str = "SYN-RULE-1", rule_type: str = "explicit_link",
          owner: str = "D08", producers: Tuple[str, ...] = ("D02", "D01"),
          expected: Optional[str] = None, allowed: Tuple[str, ...] = (),
          directionality: str = "directed", version: str = "1") -> Dict[str, Any]:
    return {
        "rule_id": rule_id,
        "version": version,
        "rule_hash": d08_content_hash(rule_id),
        "owner_routing_ref": "SYN-ROUTE-1",
        "clinical_relationship_type": rule_type,
        "left_role_constraint": "obligation_side",
        "unit_anchor_role": "left",
        "evidence_set_role": "right",
        "unit_grain": "per_left_anchor_slot",
        "directionality": directionality,
        "identity_operand_ids": [],
        "time_operand_ids": [],
        "shared_precision": "day",
        "normalization_preconditions": [],
        "expected_relation": expected,
        "forbidden_relation": None,
        "allowed_relation_set": list(allowed),
        "required_relation": None,
        "required_producer_domains": list(producers),
        "applicability_window": {
            "window_kind": "rule_window", "start": "2026-01-01", "end": "2026-12-31"},
        "authority_locator_id": "SYN-AUTH-1",
        "max_unidentified_fanout": 5,
        "duplicate_policy_ref": "SYN-DUP-1",
        "cardinality_ref": "SYN-CARD-1",
        "owner_domain": owner,
        "algorithm_version": "d08_unit_v1",
    }


def _card(*, unmatched: str = "positive_missing_required",
          overmatch: str = "allowed", reverse: bool = False,
          bidirectional: bool = False) -> Dict[str, Any]:
    return {
        "cardinality_id": "SYN-CARD-1",
        "unit_grain": "per_left_anchor_slot",
        "left_min": 1, "left_max": 1, "right_min": 0, "right_max": 1,
        "unbounded": False,
        "bidirectional": bidirectional,
        "reverse_required": reverse,
        "unmatched_required_policy": unmatched,
        "overmatch_policy": overmatch,
    }


def _base_typed_input(**overrides: Any) -> Dict[str, Any]:
    """A minimal valid typed bundle (as JSON-able dict for the adapter-style
    parse, then converted)."""
    bundle: Dict[str, Any] = {
        "input_schema": "d08-typed-input-v1",
        "scope_binding": {
            "scope_binding_id": "SYN-SCOPE-1",
            "project_ref": "SYN-PROJECT",
            "run_ref": "SYN-RUN-1",
            "subject_ref": "SYN-SUBJECT-1",
            "site_ref": "SYN-SITE-1",
            "episode_key": "SYN-EPISODE-1",
            "monitoring_mode": "offline_synthetic",
            "accepted_snapshot_ref": "SYN-SNAP-1",
            "snapshot_as_of": "2026-07-01T00:00:00+00:00",
            "clinical_event_cutoff": "2026-06-30",
            "producer_version": "SYN-PV-1",
            "lineage_hash": d08_content_hash("SYN-SCOPE-1"),
        },
        "shared_spine_binding": {"shared_spine_ref": "SYN-SPINE-1",
                                 "scope_equality_decision": "equal"},
        "owner_route": {
            "candidate_problem_kind": "explicit_link_resolve",
            "clinical_claim_token": "d08_explicit_link_resolve",
            "owner_domain": "D08",
            "d08_action": "evaluate_and_own",
            "left_role": "obligation_side",
            "right_role": "counterpart_side",
            "source": "raw_link",
            "rule_refs": ["SYN-RULE-1"],
            "locator_ids": ["SYN-LOC-1"],
            "required_producer_domains": ["D02", "D01"],
        },
        "record_nodes": [
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-2"),
        ],
        "time_refs": [
            {
                "time_ref_id": "SYN-TIME-1", "value": "2026-03-01",
                "precision": "day", "kind": "point",
                "timezone_state": "present",
                "source_locator_ids": ["SYN-LOC-1"],
            },
        ],
        "temporal_comparisons": [],
        "identity_comparisons": [],
        "identity_operands": [],
        "relation_rules": [_rule()],
        "cardinality_specs": [_card()],
        "duplicate_policies": [],
        "raw_links": [],
        "resolve_decisions": [],
        "observed_edges": [
            {
                "edge_id": "SYN-EDGE-1", "relation_rule_id": "SYN-RULE-1",
                "direction": "forward", "edge_directionality": "directed",
                "left_stable_identity": "SYN-STABLE-1",
                "right_stable_identity": "SYN-STABLE-2",
                "explicit_rel_instance_id": "",
                "recorded_operands": [],
            },
        ],
        "bidirectional_joins": [
            {
                "join_id": "SYN-JOIN-1", "relation_rule_id": "SYN-RULE-1",
                "forward_edge_refs": ["SYN-EDGE-1"], "reverse_edge_refs": [],
                "forward_identity_set": ["SYN-STABLE-2"],
                "reverse_identity_set": [],
            },
        ],
        "rel_instance_memberships": [],
        "fanout_candidate_sets": [],
        "waiver_handoffs": [],
        "propagation_objects": [],
        "derived_objects": [],
        "producer_consumption_bindings": [],
        "authority_bindings": [
            {
                "authority_binding_id": "SYN-AUTH-1",
                "authority_kind": "synthetic_rule_package",
                "authority_version": "SYN-AV-1",
                "authority_hash": d08_content_hash("SYN-AUTH-1"),
                "applicability_window": {
                    "window_kind": "rule_window", "start": "2026-01-01",
                    "end": "2026-12-31"},
            },
        ],
        "coverage_status": [
            {"producer_domain": "D02", "l0_status": "covered",
             "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]},
            {"producer_domain": "D01", "l0_status": "covered",
             "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]},
        ],
        "visibility_decision": {
            "visibility_decision_id": "SYN-VIS-1",
            "audience_anchor_rule": "obligation_side",
            "audience_lexicon_ref": "SYN-LEX-1",
            "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "projectable_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "blinded_node_ids": [],
            "forbidden_node_ids": [],
        },
        "source_jump_registry": [],
        "source_locators": [
            {"source_locator_id": "SYN-LOC-1",
             "source_file_ref": "synthetic_source/dataset_a.json",
             "canonical_location": "synthetic_source/dataset_a.json#SYN-LOC-1",
             "locator_kind": "synthetic_file",
             "content_hash": d08_content_hash("SYN-LOC-1")},
        ],
        "audience_lexicon": {
            "lexicon_id": "SYN-LEX-1", "version": "1",
            "required_sentence_patterns": ["依据", "发现", "行动项"],
            "allowed_domain_labels": ["synthetic"],
            "forbidden_internal_tokens": ["internal_relationship_token"],
        },
        "visit_refs": [],
        "mutation_context": {
            "mutation_class": "none", "mutation_description": "",
            "substantive_input_hash": d08_content_hash("base"),
            "base_fixture_id": None, "variant_of": None,
        },
        "anti_overfit_variant": None,
    }
    bundle.update(overrides)
    return bundle


def _typed(**overrides: Any) -> D08TypedInput:
    """Build a typed bundle from JSON-able dict overrides."""
    case = {"owner_route": overrides.pop("owner_route", None),
            "typed_input": _base_typed_input(**overrides)}
    return parse_typed_input(case)


class TestTypedValidation(unittest.TestCase):
    def test_closed_enums_reject_invalid_values(self) -> None:
        with self.assertRaises(D08ContractError):
            _typed(cardinality_specs=[_card(unmatched="bogus_policy")])
        with self.assertRaises(D08ContractError):
            _typed(cardinality_specs=[_card(overmatch="bogus_overmatch")])
        with self.assertRaises(D08ContractError):
            _typed(record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1",
                      cutoff="out_of_range")])
        with self.assertRaises(D08ContractError):
            _typed(resolve_decisions=[{
                "resolve_decision_id": "SYN-RES-1", "raw_link_id": "SYN-RL-1",
                "status": "bogus_status",
                "materialized_record_node_ids": ["SYN-REC-1"],
                "rejected_candidate_ids": [], "reason_codes": [],
                "l0_coverage_status": "covered"}])
        with self.assertRaises(D08ContractError):
            _typed(coverage_status=[{
                "producer_domain": "D02", "l0_status": "bogus_l0",
                "accepted_current": True, "coverage_locator_ids": ["SYN-LOC-1"]}])

    def test_waiver_states_are_exactly_three(self) -> None:
        for state in CLOSURE_STATES:
            handoff = {
                "handoff_id": "SYN-H-1", "closure_state": state,
                "authorized_object_refs": (
                    ["SYN-STABLE-1"] if state == "full_set" else []),
                "anchor_stable_identity": "SYN-STABLE-1",
                "relation_rule_id": "SYN-RULE-1",
            }
            _typed(waiver_handoffs=[handoff])
        with self.assertRaises(D08ContractError):
            _typed(waiver_handoffs=[{
                "handoff_id": "SYN-H-1", "closure_state": "partially_closed",
                "authorized_object_refs": [], "anchor_stable_identity": "",
                "relation_rule_id": ""}])

    def test_enum_tuples_are_closed_and_consistent(self) -> None:
        self.assertIn("positive", ("positive", "negative", "boundary",
                                   "not_applicable", "not_evaluable"))
        self.assertEqual(set(CUTOFF_DECISIONS),
                         {"in_cutoff", "out_of_cutoff", "spans_cutoff",
                          "time_missing_not_evaluable"})
        self.assertEqual(set(RESOLVE_STATUSES),
                         {"unique", "ambiguous", "not_found",
                          "wrong_subject_or_site", "not_evaluable"})
        self.assertIn("covered", L0_STATUSES)
        self.assertIn("per_explicit_rel_instance", UNIT_GRAINS)
        self.assertIn("datetime", TIME_PRECISIONS)

    def test_new_decision_enums_are_closed(self) -> None:
        self.assertEqual(set(LINEAGE_FINGERPRINT_STATES),
                         {"intact", "broken_chain", "mismatch"})
        self.assertEqual(set(RELATION_PAYLOAD_STATUSES),
                         {"valid", "wrong_subject_or_site"})
        self.assertIn("unclassified", IDENTITY_DECISION_CODES)
        self.assertIn("merge_with_rule", IDENTITY_DECISION_CODES)
        # every closed identity code must have a defined effect in the
        # evaluator's closed table
        from mm_r4.d08_evaluator import _IDENTITY_CODE_EFFECT
        defined = set(_IDENTITY_CODE_EFFECT)
        self.assertEqual(
            set(IDENTITY_DECISION_CODES) - {"unclassified"},
            defined)

    def test_requires_typed_bundle(self) -> None:
        with self.assertRaises(D08ContractError):
            evaluate({"input_schema": "d08-typed-input-v1"})  # type: ignore[arg-type]
        with self.assertRaises(D08ContractError):
            validate_typed_input(None)  # type: ignore[arg-type]


class TestDeterminism(unittest.TestCase):
    def test_identical_input_yields_identical_units(self) -> None:
        a = evaluate(_typed())
        b = evaluate(_typed())
        self.assertEqual(
            [u.to_dict() for u in a.units],
            [u.to_dict() for u in b.units])
        self.assertEqual(a, b)

    def test_unit_leaf_keys_are_closed(self) -> None:
        from mm_r4.d08_evaluator import UNIT_LEAF_KEYS
        result = evaluate(_typed())
        self.assertEqual(len(UNIT_LEAF_KEYS), 18)
        for u in result.units:
            self.assertEqual(set(u.to_dict()), set(UNIT_LEAF_KEYS))


class TestIntegrityFailClosed(unittest.TestCase):
    """Every pre-evaluator stage stops before medical/risk/Query/Journey."""

    def _integrity_case(self, **overrides: Any) -> D08RunResult:
        overrides.setdefault("relation_rules", [
            _rule("SYN-RULE-INT-1", "integrity_matrix", producers=("D02",))])
        overrides.setdefault("coverage_status", [
            {"producer_domain": "D02", "l0_status": "covered",
             "accepted_current": True,
             "coverage_locator_ids": ["SYN-LOC-1"]}])
        return evaluate(_typed(**overrides))

    def test_snapshot_identity_mismatch(self) -> None:
        r = self._integrity_case(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-2", snapshot="SYN-SNAP-2")])
        self.assertEqual(r.integrity_error,
                         D08IntegrityFailure("snapshot_identity_mismatch",
                                             "SYN-REC-2",
                                             "run_snapshot_identity"))
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_candidate_present)
        self.assertFalse(r.query_draft_present)
        self.assertFalse(r.risk_present)

    def test_subject_spine_identity_mismatch(self) -> None:
        r = self._integrity_case(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-2", subject="SYN-SUBJECT-2")])
        self.assertEqual(r.integrity_error.error_type,
                         "subject_spine_identity_mismatch")
        self.assertEqual(r.units, ())
        self.assertFalse(r.query_present)

    def test_producer_l0_gap(self) -> None:
        r = self._integrity_case(coverage_status=[
            {"producer_domain": "D02", "l0_status": "missing",
             "accepted_current": False, "coverage_locator_ids": ["SYN-LOC-1"]},
        ])
        self.assertEqual(r.integrity_error,
                         D08IntegrityFailure("producer_l0_missing", "D02",
                                             "producer_coverage"))
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_candidate_present)

    def test_authority_locator_missing(self) -> None:
        r = self._integrity_case(relation_rules=[
            {**_rule("SYN-RULE-INT-1", "integrity_matrix",
                     producers=("D02",)),
             "authority_locator_id": "SYN-AUTH-MISSING"}])
        self.assertEqual(r.integrity_error.error_type,
                         "authority_locator_missing")
        self.assertEqual(r.integrity_error.error_object, "SYN-RULE-INT-1")
        self.assertEqual(r.units, ())

    def test_authority_window_excludes(self) -> None:
        """Rule window admits the event; the authority window excludes it."""
        r = self._integrity_case(
            time_refs=[{
                "time_ref_id": "SYN-TIME-1", "value": "2026-06-01",
                "precision": "day", "kind": "point",
                "timezone_state": "present",
                "source_locator_ids": ["SYN-LOC-1"]}],
            authority_bindings=[{
                "authority_binding_id": "SYN-AUTH-1",
                "authority_kind": "synthetic_rule_package",
                "authority_version": "SYN-AV-1",
                "authority_hash": d08_content_hash("SYN-AUTH-1"),
                "applicability_window": {
                    "window_kind": "rule_window", "start": "2026-01-01",
                    "end": "2026-01-31"}}])
        self.assertEqual(r.integrity_error.error_type,
                         "authority_window_excludes")

    def test_node_content_hash_and_locator_fail_closed(self) -> None:
        r = self._integrity_case(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", content_hash="0" * 64),
            _node("SYN-REC-2", "SYN-STABLE-2")])
        self.assertEqual(r.integrity_error.error_type,
                         "node_content_hash_mismatch")
        r2 = self._integrity_case(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", locators=()),
            _node("SYN-REC-2", "SYN-STABLE-2")])
        self.assertEqual(r2.integrity_error.error_type, "node_locator_missing")

    def test_correction_chain_incomplete(self) -> None:
        r = self._integrity_case(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1",
                  chain="SYN-STABLE-MISSING-000"),
            _node("SYN-REC-2", "SYN-STABLE-2")])
        self.assertEqual(r.integrity_error.error_type,
                         "correction_chain_incomplete")

    def test_obligation_identity_missing(self) -> None:
        # the expected-set admission check runs on the shared path (not the
        # integrity family) and keeps d08_action evaluate_and_own
        r = evaluate(_typed(observed_edges=[{
            "edge_id": "SYN-EDGE-1", "relation_rule_id": "SYN-RULE-1",
            "direction": "forward", "edge_directionality": "directed",
            "left_stable_identity": "SYN-STABLE-MISSING",
            "right_stable_identity": "SYN-STABLE-2",
            "explicit_rel_instance_id": "", "recorded_operands": []}]))
        self.assertEqual(r.integrity_error,
                         D08IntegrityFailure("obligation_identity_missing",
                                             "SYN-STABLE-MISSING",
                                             "expected_set_admission"))
        self.assertEqual(r.units, ())
        self.assertEqual(r.d08_action, "evaluate_and_own")

    def test_producer_binding_scope_mismatch(self) -> None:
        r = self._integrity_case(producer_consumption_bindings=[{
            "binding_id": "SYN-BIND-1", "producer_object_id": "SYN-PROD-1",
            "producer_object_hash": d08_content_hash("p"),
            "producer_version": "SYN-PV-1", "purpose": "derive",
            "permitted_outputs": ["derived_value"], "scope_equality": False}])
        self.assertEqual(r.integrity_error.error_type,
                         "producer_binding_scope_mismatch")
        self.assertEqual(r.integrity_error.error_object, "SYN-BIND-1")

    def test_integrity_failure_never_projects_payload(self) -> None:
        """Fail-closed guarantee: no Query/Journey marker and no risk on any
        integrity error."""
        cases = [
            dict(record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1"),
                _node("SYN-REC-2", "SYN-STABLE-2", snapshot="SYN-SNAP-2")]),
            dict(coverage_status=[
                {"producer_domain": "D02", "l0_status": "failed",
                 "accepted_current": False,
                 "coverage_locator_ids": ["SYN-LOC-1"]}]),
        ]
        for overrides in cases:
            r = self._integrity_case(**overrides)
            self.assertIsNotNone(r.integrity_error)
            self.assertEqual(r.units, ())
            self.assertFalse(r.risk_present)
            self.assertFalse(r.query_present)
            self.assertFalse(r.journey_marker_present)
            self.assertFalse(r.risk_candidate_present)


class TestCutoffPriority(unittest.TestCase):
    def test_time_missing_priority(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1",
                  cutoff="time_missing_not_evaluable"),
            _node("SYN-REC-2", "SYN-STABLE-2", cutoff="in_cutoff")]))
        self.assertEqual(len(r.units), 1)
        u = r.units[0]
        self.assertEqual(u.l1_disposition, "not_evaluable")
        self.assertEqual(u.cutoff_decision, "time_missing_not_evaluable")
        self.assertEqual(u.primary_reason, "time_missing_priority")
        self.assertEqual(r.units[0].unit_kind, "per_left_anchor_slot")

    def test_all_out_of_cutoff_zero_medical_units(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", cutoff="out_of_cutoff"),
            _node("SYN-REC-2", "SYN-STABLE-2", cutoff="out_of_cutoff")]))
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)

    def test_mixed_membership_single_boundary_gate(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", cutoff="in_cutoff"),
            _node("SYN-REC-2", "SYN-STABLE-2", cutoff="out_of_cutoff")]))
        self.assertEqual(len(r.units), 1)
        u = r.units[0]
        self.assertEqual(u.unit_kind, "routing_or_coverage_gate")
        self.assertEqual(u.gate_signal_type, "cutoff_boundary_gate")
        self.assertEqual(u.l1_disposition, "boundary")
        self.assertEqual(u.cutoff_decision, "mixed_or_spans")

    def test_spans_cutoff_single_boundary_gate(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1", cutoff="spans_cutoff"),
            _node("SYN-REC-2", "SYN-STABLE-2", cutoff="in_cutoff")]))
        self.assertEqual(len(r.units), 1)
        self.assertEqual(r.units[0].gate_signal_type, "cutoff_boundary_gate")

    def test_propagation_exempt_from_clinical_cutoff(self) -> None:
        """An accepted in-cutoff node revised after cutoff still propagates;
        cutoff constrains clinical events, not correction timing."""
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-PROP-1",
                                  "modification_propagation",
                                  producers=("D06",))],
            coverage_status=[{"producer_domain": "D06", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            record_nodes=[_node("SYN-REC-1", "SYN-STABLE-1",
                                revision="SRC-REV-4", cutoff="out_of_cutoff")],
            observed_edges=[],
            bidirectional_joins=[],
            propagation_objects=[{
                "propagation_id": "SYN-PROP-1",
                "source_record_node_id": "SYN-REC-1",
                "change_cause": "data",
                "source_revision": "SRC-REV-4",
                "declared_consumed_revision": "SRC-REV-3",
                "actual_consumed_revision": "",
                "changed_fields": ["dose_amount"],
                "consumed_field_intersection": ["dose_amount"],
                "derived_object_id": "SYN-DERIVED-1",
                "derived_object_type": "producer_declared_derived_value",
                "lineage_fingerprint": "lg-SYN-PROP-1",
                "old_derived_object_ref": "", "new_derived_object_ref": ""}],
            derived_objects=[{
                "derived_object_id": "SYN-DERIVED-1",
                "derived_object_type": "producer_declared_derived_value",
                "producer_object_id": "SYN-PROD-1",
                "producer_version": "SYN-PV-1",
                "producer_hash": d08_content_hash("d"),
                "declared_consumed_revision": "SRC-REV-3",
                "source_locator_ids": ["SYN-LOC-1"]}],
        ))
        self.assertEqual(len(r.units), 1)
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].propagation_result, "stale")


class TestTemporalSemantics(unittest.TestCase):
    def _temporal(self, comparisons: List[Dict[str, Any]], **rule_over: Any) -> D08RunResult:
        return evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-TEMP-1", "temporal_impossibility",
                                  producers=("D02",), **rule_over)],
            coverage_status=[{"producer_domain": "D02", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            observed_edges=[], bidirectional_joins=[],
            temporal_comparisons=comparisons,
            time_refs=[
                {"time_ref_id": "T-A", "value": "2026-03-01",
                 "precision": "day", "kind": "point",
                 "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
                {"time_ref_id": "T-B", "value": "2026-03-10",
                 "precision": "day", "kind": "point",
                 "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
                {"time_ref_id": "T-C", "value": "2026-03-05",
                 "precision": "day", "kind": "point",
                 "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
                {"time_ref_id": "T-I", "value": "2026-03-01",
                 "end_value": "2026-03-20", "precision": "day",
                 "kind": "interval", "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
            ]))

    def _cmp(self, left: str, right: str, **extra: Any) -> Dict[str, Any]:
        return {
            "comparison_id": "SYN-CMP-1", "left_time_ref_id": left,
            "right_time_ref_id": right, "expected_relation": None,
            "allowed_relation_set": [],
            "left_endpoint_openness": "closed",
            "right_endpoint_openness": "closed",
            "timezone_state": "present", "precision_level": "day",
            "relation_rule_id": "SYN-RULE-TEMP-1",
            **extra,
        }

    def test_contains_observed_contained_by_is_positive(self) -> None:
        r = self._temporal([self._cmp("T-I", "T-C", expected_relation="contains")])
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].temporal_relation, "contained_by")
        self.assertEqual(r.units[0].primary_reason, "observed_contained_by")

    def test_overlap_does_not_satisfy_containment(self) -> None:
        # two partially overlapping intervals -> feasible {overlap}; expected
        # contains -> positive (overlap never satisfies containment)
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-TEMP-1",
                                  "temporal_impossibility",
                                  producers=("D02",))],
            coverage_status=[{"producer_domain": "D02", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            observed_edges=[], bidirectional_joins=[],
            temporal_comparisons=[self._cmp("T-I", "T-I2",
                                            expected_relation="contains")],
            time_refs=[
                {"time_ref_id": "T-I", "value": "2026-03-01",
                 "end_value": "2026-03-20", "precision": "day",
                 "kind": "interval", "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
                {"time_ref_id": "T-I2", "value": "2026-03-10",
                 "end_value": "2026-03-30", "precision": "day",
                 "kind": "interval", "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
            ]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].temporal_relation, "overlap")
        self.assertEqual(r.units[0].primary_reason, "observed_overlap")

    def test_same_day_points_indeterminate_boundary(self) -> None:
        r = self._temporal([self._cmp("T-A", "T-A")])
        self.assertEqual(r.units[0].l1_disposition, "boundary")
        self.assertEqual(r.units[0].temporal_relation, "indeterminate")
        self.assertEqual(r.units[0].primary_reason, "indeterminate")

    def test_timezone_incomparable_primary_reason(self) -> None:
        r = self._temporal([self._cmp("T-A", "T-B", timezone_state="missing")])
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "timezone_incomparable")

    def test_precision_insufficient(self) -> None:
        # partial month ref vs day point -> precision_insufficient
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-TEMP-1", "temporal_impossibility",
                                  producers=("D02",))],
            coverage_status=[{"producer_domain": "D02", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            observed_edges=[], bidirectional_joins=[],
            temporal_comparisons=[self._cmp("T-M", "T-B")],
            time_refs=[
                {"time_ref_id": "T-M", "value": "2026-03",
                 "precision": "month", "kind": "interval",
                 "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
                {"time_ref_id": "T-B", "value": "2026-03-10",
                 "precision": "day", "kind": "point",
                 "timezone_state": "present",
                 "source_locator_ids": ["SYN-LOC-1"]},
            ]))
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "precision_insufficient")

    def test_before_observed_is_negative_when_expected(self) -> None:
        r = self._temporal([self._cmp("T-A", "T-B", expected_relation="before")])
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].temporal_relation, "before")


class TestIdentityAndDuplicate(unittest.TestCase):
    def _identity(self, final: str = "matched",
                  decision_code: Optional[str] = None,
                  reason_prose: Tuple[str, ...] = (),
                  nodes: Optional[List[Dict[str, Any]]] = None,
                  dup: Optional[Dict[str, Any]] = None) -> D08RunResult:
        comparison: Dict[str, Any] = {
            "comparison_id": "SYN-IDCMP-1",
            "relation_rule_id": "SYN-RULE-IDM-1",
            "final_result": final,
            "operand_equality_results": [],
        }
        if decision_code is not None:
            comparison["decision_code"] = decision_code
        if reason_prose:
            comparison["reason_codes"] = list(reason_prose)
        return evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-IDM-1", "identity_collision",
                                  producers=("D02",))],
            coverage_status=[{"producer_domain": "D02", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            observed_edges=[], bidirectional_joins=[],
            record_nodes=nodes or [
                _node("SYN-REC-1", "SYN-STABLE-1"),
                _node("SYN-REC-2", "SYN-STABLE-2")],
            identity_comparisons=[comparison],
            duplicate_policies=[dup] if dup else []))

    def test_cross_subject_collision_positive(self) -> None:
        r = self._identity(nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-1", subject="SYN-SUBJECT-2")])
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "cross_subject_collision")

    def test_cross_site_collision_positive(self) -> None:
        r = self._identity(nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-1", site="SYN-SITE-2")])
        self.assertEqual(r.units[0].primary_reason, "cross_site_collision")
        self.assertEqual(r.units[0].l1_disposition, "positive")

    def test_cross_role_collision_positive(self) -> None:
        r = self._identity(nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-1", role="other_role")])
        self.assertEqual(r.units[0].primary_reason, "cross_role_collision")

    def test_distinct_negative(self) -> None:
        r = self._identity(final="distinct")
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].primary_reason, "identity_distinct")

    def test_ambiguous_not_evaluable(self) -> None:
        r = self._identity(final="ambiguous")
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "identity_ambiguous")

    def test_decision_code_maps_disposition(self) -> None:
        """Closed decision codes drive the disposition deterministically."""
        r = self._identity(decision_code="split_without_rule")
        self.assertEqual(r.units[0].l1_disposition, "boundary")
        self.assertEqual(r.units[0].primary_reason, "identity_matched")
        r2 = self._identity(decision_code="merge_with_rule")
        self.assertEqual(r2.units[0].l1_disposition, "negative")
        self.assertEqual(r2.units[0].counterevidence_count, 1)
        r3 = self._identity(decision_code="operand_unknown")
        self.assertEqual(r3.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r3.units[0].primary_reason, "identity_matched")

    def test_arbitrary_reason_prose_cannot_change_disposition(self) -> None:
        """Natural-language reason sentences are never interpreted: with an
        explicit closed code, arbitrary prose leaves the outcome unchanged;
        with no code, unmatched prose falls back to the default negative."""
        prose = ("this is a completely unrelated English sentence about "
                 "duplicate events colliding across the trial",)
        r = self._identity(decision_code="duplicate_content_same_identity",
                           reason_prose=prose)
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "identity_matched")
        # same prose, no code -> unclassified -> default negative path
        r2 = self._identity(reason_prose=prose)
        self.assertEqual(r2.units[0].l1_disposition, "negative")
        self.assertEqual(r2.units[0].primary_reason, "identity_matched")
        # Chinese prose, no code -> still the default
        r3 = self._identity(reason_prose=("同一身份在不同受试者间冲突",))
        self.assertEqual(r3.units[0].l1_disposition, "negative")

    def test_unknown_decision_code_rejected(self) -> None:
        with self.assertRaises(D08ContractError):
            self._identity(decision_code="collision_by_english_prose")

    def test_duplicate_content_positive(self) -> None:
        r = self._identity(
            final="matched",
            dup={"policy_id": "SYN-DUP-1", "version": "1",
                 "dedup_keys": ["stable_record_id", "domain_id", "source_revision"],
                 "raw_materialized_mirror_exemption": False,
                 "stable_event_collision_semantics": "duplicate_content",
                 "modeling_rule_ref": ""})
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "duplicate_content")

    def test_split_without_rule_boundary(self) -> None:
        r = self._identity(
            dup={"policy_id": "SYN-DUP-1", "version": "1",
                 "dedup_keys": [], "raw_materialized_mirror_exemption": False,
                 "stable_event_collision_semantics": "split_records",
                 "modeling_rule_ref": ""})
        self.assertEqual(r.units[0].l1_disposition, "boundary")
        self.assertEqual(r.units[0].primary_reason, "unmodelled_split_records")

    def test_mirror_exemption_negative(self) -> None:
        r = self._identity(
            dup={"policy_id": "SYN-DUP-1", "version": "1",
                 "dedup_keys": [], "raw_materialized_mirror_exemption": True,
                 "stable_event_collision_semantics": "mirror_records",
                 "modeling_rule_ref": "SYN-MODEL-1"})
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].primary_reason, "mirror_exemption")

    def test_dedup_keys_mismatch_not_evaluable(self) -> None:
        r = self._identity(
            dup={"policy_id": "SYN-DUP-1", "version": "1",
                 "dedup_keys": ["non_observed_field"],
                 "raw_materialized_mirror_exemption": False,
                 "stable_event_collision_semantics": "independent_events",
                 "modeling_rule_ref": ""})
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "dedup_keys_mismatch")


class TestPropagationLineage(unittest.TestCase):
    def _prop(self, cause: str = "data", changed: Tuple[str, ...] = ("dose_amount",),
              intersection: Tuple[str, ...] = ("dose_amount",),
              declared: str = "SRC-REV-3", source: str = "SRC-REV-4",
              node_rev: str = "SRC-REV-4", derived_declared: str = "SRC-REV-3",
              fingerprint: str = "lg-SYN-PROP-1",
              fingerprint_state: Optional[str] = None,
              rule_version: str = "1",
              description: str = "") -> D08RunResult:
        propagation: Dict[str, Any] = {
            "propagation_id": "SYN-PROP-1",
            "source_record_node_id": "SYN-REC-1",
            "change_cause": cause,
            "source_revision": source,
            "declared_consumed_revision": declared,
            "actual_consumed_revision": "",
            "changed_fields": list(changed),
            "consumed_field_intersection": list(intersection),
            "derived_object_id": "SYN-DERIVED-1",
            "derived_object_type": "producer_declared_derived_value",
            "lineage_fingerprint": fingerprint,
            "old_derived_object_ref": "", "new_derived_object_ref": "",
        }
        if fingerprint_state is not None:
            propagation["lineage_fingerprint_state"] = fingerprint_state
        return evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-PROP-1", "modification_propagation",
                                  producers=("D06",), version=rule_version)],
            coverage_status=[{"producer_domain": "D06", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}],
            record_nodes=[_node("SYN-REC-1", "SYN-STABLE-1",
                                revision=node_rev)],
            observed_edges=[], bidirectional_joins=[],
            propagation_objects=[propagation],
            derived_objects=[{
                "derived_object_id": "SYN-DERIVED-1",
                "derived_object_type": "producer_declared_derived_value",
                "producer_object_id": "SYN-PROD-1",
                "producer_version": "SYN-PV-1",
                "producer_hash": d08_content_hash("d"),
                "declared_consumed_revision": derived_declared,
                "source_locator_ids": ["SYN-LOC-1"]}],
            mutation_context={
                "mutation_class": "none", "mutation_description": description,
                "substantive_input_hash": d08_content_hash("m"),
                "base_fixture_id": None, "variant_of": None}))

    def test_stale_positive(self) -> None:
        r = self._prop()
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].propagation_result, "stale")
        self.assertEqual(r.units[0].primary_reason, "consumed_revision_stale")
        self.assertTrue(r.risk_candidate_present)

    def test_in_sync_negative(self) -> None:
        r = self._prop(declared="SRC-REV-4", source="SRC-REV-4")
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].propagation_result, "in_sync")

    def test_intersection_empty_not_applicable(self) -> None:
        r = self._prop(intersection=())
        self.assertEqual(r.units[0].l1_disposition, "not_applicable")
        self.assertEqual(r.units[0].primary_reason, "intersection_empty")

    def test_derived_missing_positive(self) -> None:
        r = self._prop(derived_declared="SRC-REV-000")
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].propagation_result, "derived_missing")

    def test_no_obligation_negative(self) -> None:
        r = self._prop(declared="SRC-REV-4", source="SRC-REV-4",
                       node_rev="SRC-REV-4", derived_declared="SRC-REV-000")
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].propagation_result, "in_sync")
        self.assertEqual(r.units[0].primary_reason, "no_obligation")

    def test_lineage_supersede_handoff(self) -> None:
        r = self._prop(cause="rule_or_mapping")
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].propagation_result,
                         "lineage_supersede_handoff")
        self.assertTrue(r.units[0].lineage_handoff)
        self.assertTrue(r.downstream_handoff_present)
        self.assertEqual(r.handoff_target_domain, "D09")

    def test_ambiguous_chain_boundary(self) -> None:
        r = self._prop(fingerprint_state="broken_chain")
        self.assertEqual(r.units[0].l1_disposition, "boundary")
        self.assertEqual(r.units[0].propagation_result, "ambiguous_chain")

    def test_lineage_fingerprint_mismatch_not_evaluable(self) -> None:
        r = self._prop(fingerprint_state="mismatch")
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].propagation_result,
                         "producer_not_evaluable")
        self.assertEqual(r.units[0].primary_reason,
                         "lineage_fingerprint_mismatch")

    def test_producer_not_evaluable_no_changed_fields(self) -> None:
        r = self._prop(changed=())
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].propagation_result,
                         "producer_not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "producer_not_evaluable")

    def test_unknown_lineage_fingerprint_state_rejected(self) -> None:
        with self.assertRaises(D08ContractError):
            self._prop(fingerprint_state="fingerprint_does_not_match")

    def test_description_text_never_changes_propagation_outcome(self) -> None:
        """The runtime is invariant to arbitrary mutation_description text;
        only the closed structured fields decide."""
        base = self._prop()
        for prose in ("", "completely unrelated English prose about toxicity",
                      "完全无关的中文描述，不包含任何英文关键词"):
            r = self._prop(description=prose)
            self.assertEqual(
                [u.to_dict() for u in r.units],
                [u.to_dict() for u in base.units])

    def test_rule_version_change_splits_units(self) -> None:
        r = self._prop(rule_version="2")
        self.assertEqual(len(r.units), 2)
        self.assertEqual(r.units[0].propagation_result, "stale")
        self.assertEqual(r.units[1].propagation_result,
                         "lineage_supersede_handoff")
        self.assertTrue(r.units[1].lineage_handoff)
        self.assertEqual(r.units[0].unit_kind, "per_propagation_derived_object")


class TestLinkResolveAndCardinality(unittest.TestCase):
    def test_reverse_missing_positive(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-REV-1", "reverse_cardinality")],
            cardinality_specs=[_card(reverse=True)],
            observed_edges=[{
                "edge_id": "SYN-EDGE-1", "relation_rule_id": "SYN-RULE-REV-1",
                "direction": "forward", "edge_directionality": "directed",
                "left_stable_identity": "SYN-STABLE-1",
                "right_stable_identity": "SYN-STABLE-2",
                "explicit_rel_instance_id": "", "recorded_operands": []}],
            bidirectional_joins=[]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "reverse_missing")
        self.assertEqual(r.units[0].signal_type, "reverse_cardinality")

    def test_conserved_negative_with_reverse_edge(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-REV-1", "reverse_cardinality")],
            cardinality_specs=[_card(reverse=True)],
            observed_edges=[
                {"edge_id": "SYN-EDGE-1", "relation_rule_id": "SYN-RULE-REV-1",
                 "direction": "forward", "edge_directionality": "directed",
                 "left_stable_identity": "SYN-STABLE-1",
                 "right_stable_identity": "SYN-STABLE-2",
                 "explicit_rel_instance_id": "", "recorded_operands": []},
                {"edge_id": "SYN-EDGE-2", "relation_rule_id": "SYN-RULE-REV-1",
                 "direction": "reverse", "edge_directionality": "directed",
                 "left_stable_identity": "SYN-STABLE-2",
                 "right_stable_identity": "SYN-STABLE-1",
                 "explicit_rel_instance_id": "", "recorded_operands": []}],
            bidirectional_joins=[]))
        self.assertEqual(r.units[0].l1_disposition, "negative")
        self.assertEqual(r.units[0].primary_reason, "conserved")
        self.assertEqual(r.units[0].edge_count, 2)

    def test_not_found_positive_with_waiver_explicit_empty(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            resolve_decisions=[{
                "resolve_decision_id": "SYN-RES-1", "raw_link_id": "SYN-RL-1",
                "status": "not_found",
                "materialized_record_node_ids": [],
                "rejected_candidate_ids": [], "reason_codes": [],
                "l0_coverage_status": "covered"}],
            waiver_handoffs=[{
                "handoff_id": "SYN-H-1", "closure_state": "explicit_empty",
                "authorized_object_refs": [],
                "anchor_stable_identity": "SYN-STABLE-1",
                "relation_rule_id": "SYN-RULE-1"}]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "missing_required_link")
        self.assertEqual(r.units[0].resolve_status, "not_found")

    def test_waiver_missing_not_evaluable(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            resolve_decisions=[{
                "resolve_decision_id": "SYN-RES-1", "raw_link_id": "SYN-RL-1",
                "status": "not_found",
                "materialized_record_node_ids": [],
                "rejected_candidate_ids": [], "reason_codes": [],
                "l0_coverage_status": "covered"}],
            waiver_handoffs=[{
                "handoff_id": "SYN-H-1", "closure_state": "missing",
                "authorized_object_refs": [],
                "anchor_stable_identity": "SYN-STABLE-1",
                "relation_rule_id": "SYN-RULE-1"}]))
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "waiver_closure_missing")

    def test_waiver_full_set_unprovable_not_evaluable(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            waiver_handoffs=[{
                "handoff_id": "SYN-H-1", "closure_state": "full_set",
                "authorized_object_refs": ["SYN-STABLE-MISSING"],
                "anchor_stable_identity": "SYN-STABLE-1",
                "relation_rule_id": "SYN-RULE-1"}]))
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "waiver_closure_unprovable")

    def test_bijection_broken_no_raw_positive(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-RMB-1", "raw_materialized_resolve")],
            raw_links=[], resolve_decisions=[], observed_edges=[],
            bidirectional_joins=[]))
        self.assertEqual(r.units[0].l1_disposition, "positive")
        self.assertEqual(r.units[0].primary_reason, "bijection_broken_no_raw")

    def test_operands_identity_mismatch_boundary(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-RMB-1", "raw_materialized_resolve")],
            raw_links=[{
                "raw_link_id": "SYN-RL-1", "subject_ref": "SYN-SUBJECT-1",
                "domain_id": "cm", "idvar": "record_id",
                "idvarval": "SYN-REC-2", "relid": "REL-1",
                "reltype": "caused_by", "source_locator_ids": ["SYN-LOC-1"],
                "raw_content_hash": d08_content_hash("rl")}],
            resolve_decisions=[{
                "resolve_decision_id": "SYN-RES-1", "raw_link_id": "SYN-RL-1",
                "status": "unique",
                "materialized_record_node_ids": ["SYN-REC-1"],
                "rejected_candidate_ids": ["SYN-REC-2"],
                "reason_codes": [], "l0_coverage_status": "covered"}],
            observed_edges=[], bidirectional_joins=[]))
        self.assertEqual(r.units[0].l1_disposition, "boundary")
        self.assertEqual(r.units[0].primary_reason, "operands_identity_mismatch")

    def test_nary_relid_single_unit(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            rel_instance_memberships=[{
                "rel_instance_id": "REL-NARY-1",
                "relation_rule_id": "SYN-RULE-1",
                "unit_grain": "per_explicit_rel_instance",
                "member_ids": ["SYN-STABLE-1", "SYN-STABLE-2", "SYN-STABLE-3"],
                "raw_link_ids": ["SYN-RL-1", "SYN-RL-2", "SYN-RL-3"],
                "raw_link_bijection": {}}],
            record_nodes=[
                _node("SYN-REC-1", "SYN-STABLE-1"),
                _node("SYN-REC-2", "SYN-STABLE-2"),
                _node("SYN-REC-3", "SYN-STABLE-3")],
            observed_edges=[
                {"edge_id": f"SYN-EDGE-{i}",
                 "relation_rule_id": "SYN-RULE-1",
                 "direction": "forward",
                 "edge_directionality": "directed",
                 "left_stable_identity": f"SYN-STABLE-{i}",
                 "right_stable_identity": f"SYN-STABLE-{i + 1}",
                 "explicit_rel_instance_id": "REL-NARY-1",
                 "recorded_operands": []}
                for i in (1, 2)],
            bidirectional_joins=[]))
        self.assertEqual(len(r.units), 1)
        self.assertEqual(r.units[0].unit_kind, "per_explicit_rel_instance")
        self.assertEqual(r.units[0].primary_reason, "rel_instance_reverse_missing")
        self.assertEqual(r.units[0].participant_count, 3)

    def test_fanout_exceeded_gate(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            fanout_candidate_sets=[{
                "fanout_set_id": "SYN-FAN-1",
                "relation_rule_id": "SYN-RULE-1",
                "obligation_side_identity": "SYN-STABLE-1",
                "candidate_identities": [f"SYN-CAND-{i}" for i in range(6)],
                "max_unidentified_fanout": 5,
                "has_unique_identity_or_relid": False}]))
        self.assertEqual(r.units[0].unit_kind, "routing_or_coverage_gate")
        self.assertEqual(r.units[0].gate_signal_type, "identity_fanout_exceeded")
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "fanout_exceeded")

    def test_fanout_within_cap_evaluates(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-1", "explicit_link")],
            fanout_candidate_sets=[{
                "fanout_set_id": "SYN-FAN-1",
                "relation_rule_id": "SYN-RULE-1",
                "obligation_side_identity": "SYN-STABLE-1",
                "candidate_identities": ["SYN-CAND-1"],
                "max_unidentified_fanout": 5,
                "has_unique_identity_or_relid": True}]))
        self.assertEqual(r.units[0].unit_kind, "per_left_anchor_slot")

    def test_cross_scope_edge_not_evaluable(self) -> None:
        r = evaluate(_typed(record_nodes=[
            _node("SYN-REC-1", "SYN-STABLE-1"),
            _node("SYN-REC-2", "SYN-STABLE-2", subject="SYN-SUBJECT-2")]))
        self.assertEqual(r.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(r.units[0].primary_reason, "cross_scope_edge")

    def test_consume_only_zero_risk(self) -> None:
        r = evaluate(_typed(
            relation_rules=[_rule("SYN-RULE-CM-1", "explicit_link",
                                  owner="D02", producers=("D01",))],
            owner_route={
                "candidate_problem_kind": "consume_only_adjacency",
                "clinical_claim_token": "d02_cm_indication_match",
                "owner_domain": "D02",
                "d08_action": "consume_only",
                "left_role": "obligation_side", "right_role": "counterpart_side",
                "source": "raw_link", "rule_refs": ["SYN-RULE-CM-1"],
                "locator_ids": ["SYN-LOC-1"],
                "required_producer_domains": ["D01"]},
            coverage_status=[{"producer_domain": "D01", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}]))
        self.assertEqual(r.d08_action, "consume_only")
        self.assertEqual(r.owner_domain, "D02")
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)
        self.assertFalse(r.risk_candidate_present)

    def test_routing_ambiguity_gate(self) -> None:
        """A routing-ambiguity owner decision is a global pre-evaluator gap:
        it emits ONLY the integrity error (no unit, no risk), matching the
        frozen integrity-family routing case and the verifier's fail-closed
        order (contract section 5 step 9)."""
        r = evaluate(_typed(
            owner_route={
                "candidate_problem_kind": "routing_ambiguity",
                "clinical_claim_token": "d08_routing_or_coverage_gate",
                "owner_domain": "D08",
                "d08_action": "routing_gate",
                "left_role": "", "right_role": "", "source": "",
                "rule_refs": [], "locator_ids": [],
                "required_producer_domains": []}))
        self.assertIsNotNone(r.integrity_error)
        self.assertEqual(r.integrity_error.error_type, "routing_ambiguity_gate")
        self.assertEqual(r.integrity_error.stage, "owner_routing")
        self.assertEqual(r.units, ())
        self.assertFalse(r.risk_present)
        self.assertFalse(r.query_present)

    def test_wrong_subject_payload_status_fails_closed_without_prose(self) -> None:
        """The closed ``relation_payload_status`` drives fail-closed
        behaviour; no description text is involved."""
        typed = _typed(relation_payload_status="wrong_subject_or_site",
                       mutation_context={
                           "mutation_class": "none",
                           "mutation_description": "",
                           "substantive_input_hash": d08_content_hash("m"),
                           "base_fixture_id": None, "variant_of": None})
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason,
                         "wrong_subject_payload_fail_closed")
        self.assertEqual(result.units[0].signal_type, "explicit_link_resolve")
        self.assertFalse(result.risk_present)
        self.assertFalse(result.query_present)
        self.assertFalse(result.risk_candidate_present)

    def test_wrong_subject_payload_status_rejects_unknown_value(self) -> None:
        with self.assertRaises(D08ContractError):
            _typed(relation_payload_status="payload_refers_to_wrong_patient")

    def test_valid_payload_status_does_not_gate(self) -> None:
        typed = _typed(relation_payload_status="valid")
        result = evaluate(typed)
        self.assertNotEqual(result.units[0].primary_reason,
                            "wrong_subject_payload_fail_closed")


class TestAudienceProjection(unittest.TestCase):
    def test_projectable_and_evaluation_sets(self) -> None:
        typed = _typed()
        result = evaluate(typed)
        projection = project_d08_audience(typed, result)
        self.assertEqual(projection.projectable_node_set,
                         ("SYN-REC-1", "SYN-REC-2"))
        self.assertEqual(projection.audience_anchor, "SYN-REC-1")
        self.assertTrue(projection.audience_payload_present)

    def test_blinded_nodes_never_leak(self) -> None:
        typed = _typed(visibility_decision={
            "visibility_decision_id": "SYN-VIS-1",
            "audience_anchor_rule": "obligation_side",
            "audience_lexicon_ref": "SYN-LEX-1",
            "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "projectable_node_set": ["SYN-REC-1"],
            "blinded_node_ids": ["SYN-REC-2"],
            "forbidden_node_ids": []})
        result = evaluate(typed)
        projection = project_d08_audience(typed, result)
        self.assertEqual(projection.hidden_node_count, 1)
        self.assertNotIn("SYN-REC-2", projection.audience_source_nodes)
        # the internal join still sees both nodes
        self.assertTrue(result.reverse_conservation_ok
                        or result.units)

    def test_empty_projectable_no_query(self) -> None:
        typed = _typed(visibility_decision={
            "visibility_decision_id": "SYN-VIS-1",
            "audience_anchor_rule": "obligation_side",
            "audience_lexicon_ref": "SYN-LEX-1",
            "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "projectable_node_set": [],
            "blinded_node_ids": [], "forbidden_node_ids": []})
        result = evaluate(typed)
        self.assertFalse(result.query_present)
        self.assertFalse(result.audience_payload_present)
        self.assertIsNone(result.audience_anchor)
        self.assertFalse(result.query_draft_present)

    def test_audience_anchor_ambiguous_boundary(self) -> None:
        typed = _typed(visibility_decision={
            "visibility_decision_id": "SYN-VIS-1",
            "audience_anchor_rule": "ambiguous",
            "audience_lexicon_ref": "SYN-LEX-1",
            "evaluation_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "projectable_node_set": ["SYN-REC-1", "SYN-REC-2"],
            "blinded_node_ids": [], "forbidden_node_ids": []})
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason,
                         "audience_anchor_ambiguous")

    def test_source_jump_resolvability(self) -> None:
        typed = _typed(source_jump_registry=[
            {"jump_target_id": "SYN-JUMP-1", "target_kind": "record_node",
             "target_object_id": "SYN-REC-1",
             "source_locator_ids": ["SYN-LOC-1"]},
            {"jump_target_id": "SYN-JUMP-2", "target_kind": "source_locator",
             "target_object_id": "SYN-LOC-1",
             "source_locator_ids": ["SYN-LOC-1"]},
        ])
        result = evaluate(typed)
        pairs = {j.jump_target_id: j.resolvable
                 for j in result.source_jump_target_pairs}
        self.assertEqual(pairs, {"SYN-JUMP-1": True, "SYN-JUMP-2": True})

    def test_source_jump_target_missing_fail_closed(self) -> None:
        typed = _typed(source_jump_registry=[
            {"jump_target_id": "SYN-JUMP-1", "target_kind": "record_node",
             "target_object_id": "SYN-REC-MISSING",
             "source_locator_ids": ["SYN-LOC-1"]},
        ])
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason,
                         "source_jump_target_missing")


class TestQueryAndRiskProjection(unittest.TestCase):
    def test_positive_produces_query_and_risk(self) -> None:
        typed = _typed()
        result = evaluate(typed)
        # base bundle has forward edge without reverse under reverse_required
        # false -> conserved negative; force a positive link gap instead
        typed2 = _typed(
            relation_rules=[_rule("SYN-RULE-REV-1", "reverse_cardinality")],
            cardinality_specs=[_card(reverse=True)],
            observed_edges=[{
                "edge_id": "SYN-EDGE-1", "relation_rule_id": "SYN-RULE-REV-1",
                "direction": "forward", "edge_directionality": "directed",
                "left_stable_identity": "SYN-STABLE-1",
                "right_stable_identity": "SYN-STABLE-2",
                "explicit_rel_instance_id": "", "recorded_operands": []}],
            bidirectional_joins=[])
        result = evaluate(typed2)
        self.assertEqual(result.units[0].l1_disposition, "positive")
        draft = build_d08_query_draft(typed2, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        joined = "".join([draft["basis_sentence"], draft["finding_sentence"],
                          draft["action_sentence"]])
        self.assertIn("依据", joined)
        self.assertIn("发现", joined)
        self.assertIn("行动项", joined)
        self.assertNotIn("PD", joined)
        self.assertEqual(draft["query_owner"], "D08")
        marker = build_d08_risk_marker(typed2, result)
        self.assertIsNotNone(marker)
        assert marker is not None
        identity = marker.public_risk_identity
        self.assertEqual(identity["domain_id"], "D08_cross_domain_logic")
        self.assertEqual(identity["public_identity_version"], "d08_public_v1")
        self.assertTrue(marker.affected_domains)
        self.assertTrue(marker.content_hash)

    def test_negative_produces_no_query_or_risk(self) -> None:
        typed = _typed()  # conserved negative (reverse not required)
        result = evaluate(typed)
        self.assertEqual(result.units[0].l1_disposition, "negative")
        self.assertIsNone(build_d08_query_draft(typed, result))
        self.assertIsNone(build_d08_risk_marker(typed, result))

    def test_consume_only_no_query(self) -> None:
        typed = _typed(
            relation_rules=[_rule("SYN-RULE-CM-1", "explicit_link",
                                  owner="D02", producers=("D01",))],
            owner_route={
                "candidate_problem_kind": "consume_only_adjacency",
                "clinical_claim_token": "d02_cm_indication_match",
                "owner_domain": "D02", "d08_action": "consume_only",
                "left_role": "", "right_role": "", "source": "",
                "rule_refs": [], "locator_ids": [],
                "required_producer_domains": ["D01"]},
            coverage_status=[{"producer_domain": "D01", "l0_status": "covered",
                              "accepted_current": True,
                              "coverage_locator_ids": ["SYN-LOC-1"]}])
        result = evaluate(typed)
        self.assertIsNone(build_d08_query_draft(typed, result))
        self.assertIsNone(build_d08_risk_marker(typed, result))


# ---------------------------------------------------------------------------
# Runtime closure: static proof of independence from acceptance artifacts
# ---------------------------------------------------------------------------

_RUNTIME_MODULES = (
    Path(__file__).resolve().parents[1] / "src/mm_r4/d08_contracts.py",
    Path(__file__).resolve().parents[1] / "src/mm_r4/d08_evaluator.py",
    Path(__file__).resolve().parents[1] / "src/mm_r4/d08_projection.py",
)
# Semantic modules: evaluation must depend only on closed structured facts.
# The data-model module (d08_contracts) legitimately carries the free-text
# fields as schema, so the prose-coupling scan targets the two semantic
# modules only.
_SEMANTIC_MODULES = (
    Path(__file__).resolve().parents[1] / "src/mm_r4/d08_evaluator.py",
    Path(__file__).resolve().parents[1] / "src/mm_r4/d08_projection.py",
)
_FORBIDDEN_ID_RE = __import__("re").compile(
    r"D08-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+")
_FORBIDDEN_TOKENS = (
    "reviews", "typed_fixture_catalog", "expected_outcome_oracle",
    "challenge_manifest_registry", "test_d08_artifact_generator",
    "expected_leaf_set", "derive_expected_leaves",
)
# Free-text / prose-substring decision coupling must never exist in the
# semantic modules: no mutation-context text, no hint tables, no
# natural-language identity reason interpretation.
_FORBIDDEN_PROSE_TOKENS = (
    "mutation_description", "mutation_context", "_HINT", "reason_codes",
    "startswith", "SRC-REV-000", "SYN-STABLE-MISSING-000", '"0" * 64',
)


class TestRuntimeClosure(unittest.TestCase):
    def test_runtime_never_reads_acceptance_artifacts(self) -> None:
        for path in _RUNTIME_MODULES:
            src = path.read_text(encoding="utf-8")
            self.assertNotIn("reviews", src, path.name)
            self.assertNotIn("open(", src, path.name)
            self.assertNotIn("read_text", src, path.name)
            self.assertNotIn("read_bytes", src, path.name)

    def test_runtime_has_no_artifact_or_case_identifiers(self) -> None:
        for path in _RUNTIME_MODULES:
            src = path.read_text(encoding="utf-8")
            self.assertIsNone(_FORBIDDEN_ID_RE.search(src), path.name)
            for token in _FORBIDDEN_TOKENS:
                self.assertNotIn(token, src, f"{path.name} contains {token}")

    def test_runtime_imports_are_stdlib_or_package_only(self) -> None:
        allowed_roots = {
            "__future__", "calendar", "collections", "datetime", "hashlib",
            "json", "re", "dataclasses", "typing", "unicodedata", "mm_r4",
        }
        for path in _RUNTIME_MODULES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports: set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.level > 0:
                        imports.add("mm_r4")
                    else:
                        imports.add(node.module.split(".")[0])
            foreign = sorted(imports - allowed_roots)
            self.assertEqual(foreign, [], f"{path.name} foreign imports {foreign}")

    def test_runtime_has_no_hard_coded_expected_payloads(self) -> None:
        for path in _RUNTIME_MODULES:
            src = path.read_text(encoding="utf-8")
            for token in ("D08-CASE-001", "SYN-RULE-LINK-001",
                          "SYN-STABLE-001", "REL-001"):
                self.assertNotIn(token, src, path.name)

    def test_semantic_modules_have_no_text_driven_decision_tables(self) -> None:
        """Evaluation never references mutation-context prose, hint tables,
        identity reason prose, or substring matching: only closed structured
        facts decide."""
        for path in _SEMANTIC_MODULES:
            src = path.read_text(encoding="utf-8")
            for token in _FORBIDDEN_PROSE_TOKENS:
                self.assertNotIn(token, src, f"{path.name} contains {token}")


if __name__ == "__main__":
    unittest.main()
