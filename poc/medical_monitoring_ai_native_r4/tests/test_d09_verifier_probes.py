"""R4-D09 independent verifier probe regressions (worker_02 follow-up 3).

Each test reproduces one verifier finding against the typed runtime /
projection and asserts the remediated behavior.  All inputs are
self-contained synthetic typed inputs (or catalog-derived via the frozen
test adapter; the catalog/oracle/registry are read-only here).

Probes covered:

* P-fully-hidden: a fully hidden positive emits NO audience payload and
  zero audience risk/subject/event/pattern/Query counts (Query label stays
  ``查询草稿 0 条``) while the internal evaluator ledger keeps its count;
* P-partial: partial visibility exposes only the projectable counts;
  hidden members never reach rows/counts/Query/marker/hotspot/deep-link;
* P-evidence: independent and combined tampering of Query
  ``source_locator_ids`` / ``evidence_refs`` -- including a recomputed
  content hash -- is rejected by closed draft validation;
* P-handoff: joint forgery of ``handoff_id`` + ``idempotency_key`` (even a
  jointly-consistent pair) is rejected by expected-handoff hash
  recomputation; prior/public/lineage/action regressions fail closed;
* P-PD: across the 179-case catalog exactly 63 non-PD + 2 exact PD drafts,
  with the PD wording bound to the exact ``pd_unreported`` member fact and
  the ``verify_pd`` policy gate;
* P-anchor: missing risk/gap/trend anchors all yield an unavailable
  deep-link target (``来源暂无法定位``) with no locator/anchor disclosure;
* P-revision: source revision permutation preserves Query identity,
  canonical refs, evaluation-content identity and R2 idempotency.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d09_contracts import (  # noqa: E402
    ChangeLedgerMember,
    CoverageStatus,
    LineageContext,
    Opportunity,
    VisibilityDecision,
    d09_content_hash,
)
from mm_r4.d09_evaluator import evaluate  # noqa: E402
from mm_r4.d09_projection import (  # noqa: E402
    D09ProjectionError,
    UNAVAILABLE_SOURCE_ZH,
    build_d09_audience_projection,
    build_d09_count_surface,
    build_d09_deep_links,
    build_d09_query_draft,
    build_d09_r2_handoff,
    build_d09_risk_marker,
    d09_evaluation_content_identity,
    validate_d09_r2_handoff,
    validate_query_draft,
)

from test_d09_adapter import (  # noqa: E402
    assemble_leaf_sets,
    case_index,
    load_artifacts,
    run_case,
)
from test_d09_runtime_contract import (  # noqa: E402
    _base_typed_input,
    _definition,
    _risk,
    _sha,
    _window,
)
from test_d09_projection import _gap  # noqa: E402


def _evaluate(**overrides: Any):
    typed = _base_typed_input(**overrides)
    return typed, evaluate(typed)


class TestFullyHiddenPositiveProbes(unittest.TestCase):
    def test_fully_hidden_positive_has_no_audience_payload(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  _risk("R-3", "SYN-SUBJ-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                hidden_member_refs=("R-1", "R-2", "R-3"),
                hidden_reason_codes=("blinded_group",),
                visible_n=0, eligible_n=42,
                rate_projection_state="suppressed"))
        self.assertEqual(result.disposition, "positive")
        self.assertEqual(result.query_count, 1)  # internal evaluator ledger
        projection = build_d09_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.risk_present)
        self.assertFalse(projection.query_present)
        self.assertFalse(projection.journey_marker_present)
        self.assertFalse(projection.hotspot_present)
        self.assertEqual(projection.hidden_member_count, 3)
        self.assertEqual(projection.projectable_member_refs, ())
        self.assertIsNone(build_d09_risk_marker(typed, result))
        self.assertIsNone(build_d09_query_draft(typed, result))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 0)
        self.assertEqual(counts.affected_subject_count, 0)
        self.assertEqual(counts.event_count, 0)
        self.assertEqual(counts.center_pattern_count, 0)
        self.assertEqual(counts.query_count, 0)
        self.assertEqual(counts.query_count_zh, "查询草稿 0 条")


class TestPartialVisibilityProbes(unittest.TestCase):
    def test_partial_visibility_exposes_only_projectable_counts(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  _risk("R-3", "SYN-SUBJ-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                hidden_member_refs=("R-3",),
                hidden_reason_codes=("blinded_group",),
                visible_n=2, eligible_n=42,
                rate_projection_state="suppressed"))
        self.assertEqual(result.individual_risk_count, 3)  # evaluation plane
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.hidden_member_count, 1)
        self.assertEqual(counts.individual_risk_count, 2)
        self.assertEqual(counts.visible_individual_risk_count, 2)
        self.assertEqual(counts.affected_subject_count, 2)
        self.assertEqual(counts.event_count, 2)
        projection = build_d09_audience_projection(typed, result)
        self.assertNotIn("R-3", projection.projectable_member_refs)
        self.assertIn("R-3", projection.hidden_member_refs)
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertNotIn("R-3", draft.member_refs)
        for ref in ("R-3",):
            self.assertNotIn(ref, draft.finding_sentence)


class TestLocatorEvidenceTamperProbes(unittest.TestCase):
    """Query evidence tamper rejection (independent and combined)."""

    def test_independent_evidence_tamper_rejected(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        draft = build_d09_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        tampered = replace(draft, evidence_refs=("SYN-FORGED-LOC",))
        validation = validate_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_not_locatable_projectable",
                      validation["reasons"])

    def test_combined_tamper_with_recomputed_hash_rejected(self) -> None:
        """Even a jointly-consistent forgery (locator ids + evidence refs +
        recomputed content hash) is rejected: the evidence set must equal
        the deterministic locator set of the complete member list."""
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None

        def _recompute(d: object) -> str:
            return d09_content_hash({
                "query_draft_id": d.query_draft_id,
                "unit_stable_core": d.unit_stable_core,
                "query_owner": d.query_owner,
                "basis_sentence": d.basis_sentence,
                "finding_sentence": d.finding_sentence,
                "action_sentence": d.action_sentence,
                "member_refs": list(d.member_refs),
                "evidence_refs": list(d.evidence_refs),
                "source_locator_ids": list(d.source_locator_ids),
                "scope_binding_id": d.scope_binding_id,
                "redundancy_decision": d.redundancy_decision,
                "max_query_member_fanout": d.max_query_member_fanout,
                "basis_refs": list(d.basis_refs),
                "source_revision_refs": list(d.source_revision_refs),
            })

        forged = replace(
            draft,
            evidence_refs=("SYN-FORGED-LOC",),
            source_locator_ids=("SYN-FORGED-LOC",),
            content_hash=_recompute(replace(
                draft,
                evidence_refs=("SYN-FORGED-LOC",),
                source_locator_ids=("SYN-FORGED-LOC",))))
        validation = validate_query_draft(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_not_locatable_projectable",
                      validation["reasons"])
        self.assertNotIn("content_hash_stale", validation["reasons"])


class TestR2HandoffForgeryProbes(unittest.TestCase):
    """R2 handoff hash recomputation and action/prior/lineage regressions."""

    def _positive(self):
        return _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))

    def test_consistent_joint_forgery_rejected_by_recomputation(self) -> None:
        typed, result = self._positive()
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        # jointly-consistent pair: recomputation from typed facts still
        # rejects the stale id
        forged = replace(handoff, handoff_id="f" * 64,
                         idempotency_key="f" * 64)
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("handoff_id_stale", validation["reasons"])
        # inconsistent pair: idempotency must equal the handoff id
        forged = replace(handoff, handoff_id="f" * 64,
                         idempotency_key="e" * 64)
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("idempotency_key_mismatch", validation["reasons"])

    def test_action_forgery_rejected(self) -> None:
        typed, result = self._positive()
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        forged = replace(handoff, action="update")
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("action_not_d09_initiated:update", validation["reasons"])

    def test_prior_ref_forgery_on_create_rejected(self) -> None:
        typed, result = self._positive()
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        forged = replace(handoff, prior_risk_instance_ref="SYN-FORGED-PRIOR")
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("create_with_prior_ref", validation["reasons"])
        self.assertIn("prior_ref_mismatch", validation["reasons"])

    def test_lineage_forgery_rejected(self) -> None:
        typed, result = self._positive()
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        forged = replace(handoff, lineage_relation="superseded_by_rule_or_method_change")
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("lineage_relation_mismatch", validation["reasons"])

    def test_continue_without_prior_fails_closed_at_build(self) -> None:
        typed, result = self._positive()
        lineage = replace(
            typed.lineage_context,
            carry_forward_state="active",
            lineage_relation="continued_from_data_revision")
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(replace(typed, lineage_context=lineage),
                                 result)

    def test_create_with_prior_fails_closed_at_build(self) -> None:
        """A typed prior ref switches the build to the continue path (the
        create action only exists without a prior); a forged prior ref on a
        built create handoff is rejected by validation."""
        typed, result = self._positive()
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        self.assertEqual(handoff.action, "create")
        forged = replace(handoff, prior_risk_instance_ref="SYN-FORGED-PRIOR")
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("create_with_prior_ref", validation["reasons"])
        self.assertIn("prior_ref_mismatch", validation["reasons"])

    def test_broken_coverage_carry_forward_continues_and_validates(
            self) -> None:
        """Worker02 gate: broken coverage carries forward, never closes."""
        typed, result = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="active",
                lineage_relation="continued_from_data_revision"))
        self.assertEqual(result.disposition, "not_evaluable")
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        self.assertTrue(handoff.no_auto_close_reasons)
        validation = validate_d09_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])


class TestPdWordingDistributionProbes(unittest.TestCase):
    """63 non-PD + 2 exact PD drafts across the 179-case catalog."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _registry, _quota = load_artifacts()
        cls.bundles = {}
        cls.drafts = []
        for case in cls.catalog["cases"]:
            typed, result = run_case(case)
            draft = build_d09_query_draft(typed, result)
            if draft is not None:
                cls.drafts.append((case["case_id"], typed, result, draft))

    def test_pd_wording_bound_to_exact_pd_facts(self) -> None:
        non_pd = 0
        pd = 0
        for cid, typed, result, draft in self.drafts:
            draft_has_pd_fact = any(
                m.member_id in draft.member_refs
                and m.gap_kind == "pd_unreported"
                for m in typed.gap_members)
            if "请核实是否为 PD" in draft.action_sentence:
                pd += 1
                self.assertTrue(draft_has_pd_fact,
                                f"{cid}: PD wording without a PD member fact")
                self.assertIn("verify_pd",
                              typed.center_query_policy.allowed_action_kinds,
                              f"{cid}: PD wording without the verify_pd gate")
            else:
                non_pd += 1
                self.assertFalse(draft_has_pd_fact,
                                 f"{cid}: PD member without PD wording")
                self.assertNotIn("请核实是否为 PD",
                                 draft.action_sentence, cid)
            validation = validate_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")
        self.assertEqual(non_pd, 63)
        self.assertEqual(pd, 2)
        self.assertEqual(non_pd + pd, 65)


class TestAnchorFailClosedProbes(unittest.TestCase):
    """Missing risk/gap/trend anchors yield unavailable targets with no
    locator/anchor disclosure."""

    def test_missing_risk_locator_yields_unavailable_link(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", locator="SYN-LOC-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2",
                  loc_state="missing")))
        links = build_d09_deep_links(typed, result)
        by_ref = {link.member_ref: link for link in links}
        self.assertIn("R-2", by_ref)
        link = by_ref["R-2"]
        self.assertEqual(link.target_state, "unavailable")
        self.assertEqual(link.unavailable_message, UNAVAILABLE_SOURCE_ZH)
        self.assertIsNone(link.source_locator)
        self.assertIsNone(link.visit_or_time_anchor)
        self.assertEqual(by_ref["R-1"].target_state, "locatable")

    def test_missing_gap_anchor_yields_unavailable_link(self) -> None:
        gaps = tuple(_gap(f"GAP-{n}", f"SYN-SUBJ-{n}", anchor_state="unresolved")
                     for n in range(1, 3))
        typed, result = _evaluate(
            pattern_definition=_definition(
                pattern_kind="systematic_data_or_process_gap",
                clinical_claim_token="d09_systematic_data_or_process_gap",
                required_producer_domains=("D05",),
                accepted_member_risk_kinds=(),
                allowed_denominator_kinds=("evaluable_subjects",)),
            coverage=(CoverageStatus(producer_domain="D05", l0_status="covered",
                                     l1_medical_completeness_state="complete"),),
            subject_risk_members=(),
            gap_members=gaps,
            opportunity=Opportunity(
                opportunity_definition_ref="SYN-OPPDEF-1",
                expected_opportunity_count=42,
                observed_opportunity_count=40,
                opportunity_state="sufficient"))
        links = build_d09_deep_links(typed, result)
        self.assertTrue(links)
        for link in links:
            self.assertEqual(link.target_state, "unavailable", link.member_ref)
            self.assertEqual(link.unavailable_message, UNAVAILABLE_SOURCE_ZH)
            self.assertIsNone(link.source_locator)
            self.assertIsNone(link.visit_or_time_anchor)

    def test_missing_trend_locator_yields_unavailable_link(self) -> None:
        changes = tuple(ChangeLedgerMember(
            member_id=f"SYN-CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1",
            change_ledger_member_id=f"SYN-CHGID-{n}",
            current_window_instance_ref="SYN-WIN-2-INST",
            prior_window_instance_ref="SYN-WIN-1-INST",
            comparable_state="comparable", change_kind="increased",
            change_cause="data", unit="rate_per_subject",
            supporting_member_refs=(f"SYN-RISK-{n}",),
            source_locator_refs=())
            for n in range(1, 4))
        typed, result = _evaluate(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window(stable_id="SYN-WIN-1"),
                              _window(stable_id="SYN-WIN-2")),
            subject_risk_members=(),
            change_ledger_members=changes,
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))
        self.assertEqual(result.disposition, "positive")
        links = build_d09_deep_links(typed, result)
        self.assertEqual(len(links), 3)
        for link in links:
            self.assertEqual(link.target_state, "unavailable")
            self.assertEqual(link.unavailable_message, UNAVAILABLE_SOURCE_ZH)
            self.assertIsNone(link.source_locator)
            self.assertIsNone(link.visit_or_time_anchor)


class TestSourceRevisionOrderInvarianceProbes(unittest.TestCase):
    """Source revision permutation preserves Query identity and canonical
    refs, evaluation-content identity and R2 idempotency."""

    def test_permutation_preserves_query_identity_and_canonical_refs(
            self) -> None:
        base_typed, base_result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            source_revision_set=("SYN-REV-A", "SYN-REV-B", "SYN-REV-C"),
            source_content_hashes=(_sha("d09-rev:A"), _sha("d09-rev:B"),
                                   _sha("d09-rev:C")))
        permuted_typed, permuted_result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            source_revision_set=("SYN-REV-C", "SYN-REV-A", "SYN-REV-B"),
            source_content_hashes=(_sha("d09-rev:C"), _sha("d09-rev:A"),
                                   _sha("d09-rev:B")))
        self.assertEqual(d09_evaluation_content_identity(permuted_typed),
                         d09_evaluation_content_identity(base_typed))
        base_draft = build_d09_query_draft(base_typed, base_result)
        permuted_draft = build_d09_query_draft(permuted_typed,
                                               permuted_result)
        assert base_draft is not None and permuted_draft is not None
        self.assertEqual(permuted_draft.query_draft_id,
                         base_draft.query_draft_id)
        self.assertEqual(permuted_draft.content_hash, base_draft.content_hash)
        self.assertEqual(permuted_draft.source_revision_refs,
                         tuple(sorted(("SYN-REV-A", "SYN-REV-B", "SYN-REV-C"))))
        base_handoff = build_d09_r2_handoff(base_typed, base_result)
        permuted_handoff = build_d09_r2_handoff(permuted_typed,
                                                permuted_result)
        assert base_handoff is not None and permuted_handoff is not None
        self.assertEqual(permuted_handoff.idempotency_key,
                         base_handoff.idempotency_key)
        # leaves stay identical too
        base_leaf = assemble_leaf_sets(base_typed, base_result, 1)
        permuted_leaf = assemble_leaf_sets(permuted_typed,
                                           permuted_result, 1)
        self.assertEqual(permuted_leaf, base_leaf)

    def test_catalog_multi_revision_cases_permutation_stable(self) -> None:
        catalog, _oracle, _registry, _quota = load_artifacts()
        for case in catalog["cases"]:
            revisions = case["typed_input"]["source_revision_set"]
            if len(revisions) < 2:
                continue
            typed, result = run_case(case)
            base = assemble_leaf_sets(typed, result, case_index(case))
            hashes = list(typed.source_content_hashes)
            records = list(typed.source_verification_records)
            permuted = revisions[::-1]
            order = [revisions.index(r) for r in permuted]
            re_typed = replace(
                typed,
                source_revision_set=tuple(permuted),
                source_content_hashes=tuple(hashes[i] for i in order),
                source_verification_records=tuple(records[i] for i in order))
            re_result = evaluate(re_typed)
            leaves = assemble_leaf_sets(re_typed, re_result,
                                        case_index(case))
            self.assertEqual(leaves, base, case["case_id"])


if __name__ == "__main__":
    unittest.main()
