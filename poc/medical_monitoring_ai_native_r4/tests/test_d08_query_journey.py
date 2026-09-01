"""R4-D08 Query draft, risk marker and source-visibility tests.

Covers the renderer-neutral audience projection contract (v0.6 section 9)
over the frozen catalog through the typed runtime:

* D08-owned positives produce a three-part Chinese Query draft
  (``依据``/``发现``/``行动项``) referencing only projectable records and
  the relation rule; no PD wording (D04 owns PD);
* every positive Query draft passes the closed audience validation
  (lexicon patterns, no forbidden internal tokens, evidence within the
  projectable set, resolvable source locators, content hash);
* the risk marker carries the D08 public risk identity
  (``D08_cross_domain_logic`` / ``d08_public_v1``), stable source/event
  identity, affected domains and source locators;
* negative / boundary / not-applicable / not-evaluable / integrity and
  consume-only runs never emit a Query draft, risk marker or Journey
  marker;
* blinded/forbidden nodes never appear in any audience payload, Query
  evidence or Journey edge; the internal evaluation set may exceed the
  projectable set;
* source jumps resolve only to known record nodes / source locators.
"""

from __future__ import annotations

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
from mm_r4.d08_projection import (  # noqa: E402
    build_d08_query_draft,
    build_d08_risk_marker,
    validate_query_draft,
)

from test_d08_adapter import (  # noqa: E402
    load_artifacts,
    run_case,
)

POSITIVE_WITH_PAYLOAD_SAMPLES = (
    "D08-CASE-001", "D08-CASE-046", "D08-CASE-049", "D08-CASE-057",
    "D08-CASE-203", "D08-CASE-205",
)
NO_QUERY_SAMPLES = (
    "D08-CASE-002",   # negative
    "D08-CASE-082",   # boundary
    "D08-CASE-064",   # consume-only
    "D08-CASE-135",   # not_evaluable
)


class TestQueryDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()
        cls.cases = {c["case_id"]: c for c in cls.catalog["cases"]}

    def _run(self, cid: str):
        return run_case(self.cases[cid])

    def test_positive_cases_produce_three_part_query(self) -> None:
        for cid in POSITIVE_WITH_PAYLOAD_SAMPLES:
            typed, result, _ = self._run(cid)
            self.assertTrue(result.risk_candidate_present, cid)
            draft = build_d08_query_draft(typed, result)
            self.assertIsNotNone(draft, cid)
            assert draft is not None
            joined = "".join([draft["basis_sentence"], draft["finding_sentence"],
                              draft["action_sentence"]])
            for token in ("依据", "发现", "行动项"):
                self.assertIn(token, joined, cid)
            self.assertNotIn("PD", joined, cid)
            self.assertEqual(draft["query_owner"], "D08", cid)
            self.assertTrue(draft["evidence_refs"], cid)

    def test_query_draft_references_only_projectable_records(self) -> None:
        for cid in POSITIVE_WITH_PAYLOAD_SAMPLES:
            typed, result, _ = self._run(cid)
            draft = build_d08_query_draft(typed, result)
            assert draft is not None
            projectable = set(result.projectable_node_set)
            for ref in draft["evidence_refs"]:
                self.assertIn(ref, projectable, cid)

    def test_query_draft_passes_closed_audience_validation(self) -> None:
        for cid in POSITIVE_WITH_PAYLOAD_SAMPLES:
            typed, result, _ = self._run(cid)
            draft = build_d08_query_draft(typed, result)
            assert draft is not None
            validation = validate_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"], f"{cid}: {validation['reasons']}")

    def test_non_positive_runs_produce_no_query(self) -> None:
        for cid in NO_QUERY_SAMPLES:
            typed, result, _ = self._run(cid)
            self.assertFalse(result.risk_candidate_present, cid)
            self.assertIsNone(build_d08_query_draft(typed, result), cid)

    def test_integrity_failures_produce_no_query(self) -> None:
        for cid, case in self.cases.items():
            typed, result, _ = run_case(case)
            if result.integrity_error is None:
                continue
            self.assertIsNone(build_d08_query_draft(typed, result), cid)
            self.assertIsNone(build_d08_risk_marker(typed, result), cid)

    def test_all_query_drafts_validate_across_catalog(self) -> None:
        checked = 0
        for case in self.catalog["cases"]:
            typed, result, _ = run_case(case)
            draft = build_d08_query_draft(typed, result)
            if draft is None:
                self.assertFalse(result.risk_candidate_present
                                 and bool(result.projectable_node_set),
                                 case["case_id"])
                continue
            validation = validate_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"],
                            f"{case['case_id']}: {validation['reasons']}")
            checked += 1
        self.assertGreaterEqual(checked, 60)


class TestRiskMarker(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _ = load_artifacts()
        cls.cases = {c["case_id"]: c for c in cls.catalog["cases"]}

    def test_risk_marker_public_identity(self) -> None:
        for cid in POSITIVE_WITH_PAYLOAD_SAMPLES:
            typed, result, _ = run_case(self.cases[cid])
            marker = build_d08_risk_marker(typed, result)
            self.assertIsNotNone(marker, cid)
            assert marker is not None
            identity = marker.public_risk_identity
            self.assertEqual(identity["domain_id"], "D08_cross_domain_logic", cid)
            self.assertEqual(identity["public_identity_version"], "d08_public_v1", cid)
            self.assertTrue(identity["stable_source_or_event_identity"], cid)
            self.assertTrue(identity["normalized_concept"], cid)
            self.assertTrue(marker.affected_domains, cid)
            self.assertTrue(marker.content_hash, cid)
            self.assertEqual(marker.risk_owner, "D08", cid)

    def test_risk_marker_affected_domains_cover_producers_and_nodes(self) -> None:
        for cid in POSITIVE_WITH_PAYLOAD_SAMPLES:
            typed, result, _ = run_case(self.cases[cid])
            marker = build_d08_risk_marker(typed, result)
            assert marker is not None
            node_domains = {n.stable_record_identity.domain_id
                            for n in typed.record_nodes}
            producer_domains = {
                d for r in typed.relation_rules
                for d in r.required_producer_domains}
            self.assertTrue((node_domains | producer_domains)
                            <= set(marker.affected_domains), cid)

    def test_risk_marker_stable_identity_survives_data_revision(self) -> None:
        """A source-revision edit keeps the public classifier (stable
        identity + normalized concept) identical."""
        import json as _json
        case = _json.loads(_json.dumps(self.cases["D08-CASE-049"]))
        typed, result, _ = run_case(case)
        marker_a = build_d08_risk_marker(typed, result)
        assert marker_a is not None
        for n in case["typed_input"]["record_nodes"]:
            n["source_revision"] = "SRC-REV-EDITED"
        typed_b, result_b, _ = run_case(case)
        marker_b = build_d08_risk_marker(typed_b, result_b)
        assert marker_b is not None
        self.assertEqual(
            marker_a.public_risk_identity["stable_source_or_event_identity"],
            marker_b.public_risk_identity["stable_source_or_event_identity"])
        self.assertEqual(marker_a.public_risk_identity["normalized_concept"],
                         marker_b.public_risk_identity["normalized_concept"])


class TestAudienceVisibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _ = load_artifacts()
        cls.cases = {c["case_id"]: c for c in cls.catalog["cases"]}
        cls.expectations = {e["case_id"]: e for e in cls.oracle["ordered_expectations"]}

    def test_hidden_nodes_never_appear_in_any_payload(self) -> None:
        """blinded/forbidden nodes stay out of every audience payload across
        the whole catalog; evaluation may still exceed projection."""
        for cid, case in self.cases.items():
            vis = case["typed_input"].get("visibility_decision") or {}
            hidden = set(vis.get("blinded_node_ids") or []) | set(
                vis.get("forbidden_node_ids") or [])
            if not hidden:
                continue
            typed, result, projection = run_case(case)
            self.assertFalse(
                hidden & set(projection.audience_source_nodes), cid)
            self.assertEqual(projection.hidden_node_count, len(hidden), cid)
            self.assertFalse(hidden & set(projection.projectable_node_set), cid)
            draft = build_d08_query_draft(typed, result)
            if draft is not None:
                self.assertFalse(
                    hidden & set(draft["evidence_refs"]), cid)

    def test_evaluation_set_may_exceed_projectable_set(self) -> None:
        for cid, case in self.cases.items():
            vis = case["typed_input"].get("visibility_decision") or {}
            evaluation = set(vis.get("evaluation_node_set") or [])
            projectable = set(vis.get("projectable_node_set") or [])
            if projectable < evaluation:
                typed, result, projection = run_case(case)
                self.assertGreaterEqual(len(projection.evaluation_node_set),
                                        len(projection.projectable_node_set), cid)

    def test_journey_marker_only_for_query_present(self) -> None:
        for cid, case in self.cases.items():
            typed, result, projection = run_case(case)
            self.assertEqual(projection.journey_marker_present,
                             projection.query_present, cid)
            self.assertEqual(projection.risk_present,
                             bool(result.positive_units), cid)
            self.assertFalse(projection.disclosure_leak_present, cid)

    def test_audience_anchor_is_first_projectable(self) -> None:
        for cid, case in self.cases.items():
            vis = case["typed_input"].get("visibility_decision") or {}
            projectable = vis.get("projectable_node_set") or []
            typed, result, projection = run_case(case)
            expected = projectable[0] if projectable else None
            self.assertEqual(projection.audience_anchor, expected, cid)

    def test_relation_edges_require_both_endpoints_projectable(self) -> None:
        for cid, case in self.cases.items():
            vis = case["typed_input"].get("visibility_decision") or {}
            projectable = set(vis.get("projectable_node_set") or [])
            edges = case["typed_input"].get("observed_edges") or []
            if not edges:
                continue
            typed, result, projection = run_case(case)
            for edge_id, left, right in projection.relation_edges:
                self.assertIn(left, projectable, cid)
                self.assertIn(right, projectable, cid)

    def test_source_jumps_resolve_within_scope(self) -> None:
        for cid, case in self.cases.items():
            typed, result, projection = run_case(case)
            node_ids = {n.record_node_id for n in typed.record_nodes}
            loc_ids = {loc.source_locator_id for loc in typed.source_locators}
            for jump in projection.source_jump_target_pairs:
                universe = node_ids if jump.target_kind == "record_node" else loc_ids
                self.assertEqual(jump.resolvable,
                                 jump.target_object_id in universe, cid)


if __name__ == "__main__":
    unittest.main()
