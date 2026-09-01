"""R4-D09 renderer-neutral projection, Query, hotspot, deep-link, count and
R2 handoff tests (worker_02).

Covers the projection layer over locally constructed typed inputs (semantic
negatives) plus the test-only frozen artifact adapter (broad 179-case
projection invariants):

* audience visibility: projectable vs evaluation member planes, hidden
  members never leak through rows/counts/ordering/rates/Query evidence/
  hotspot details/locators/tooltips; suppressed/qualified rates never show
  a misleading precision rate;
* separated count surface with the frozen Chinese forms (contract section
  14); the six mandated counts are never summed; gap-only positives keep
  zero individual risks with retained affected/gap/center counts;
* D09 center-pattern risk marker (``D09_center_pattern`` / ``d09_public_v1``)
  only for positives; replay stable across run/snapshot swaps;
* hotspot subject rows: projections only; n=1 boundary keeps its mandatory
  hotspot; high-priority members stay visible on boundary/negative;
* verified one-hop deep links: missing/unresolvable locator or anchor yields
  ``来源暂无法定位`` with no fabricated jump; anchors only when present and
  typed resolved;
* at most one Query draft per positive unit (``依据``/``发现``/``行动项``),
  complete uncovered projectable member set without truncation, PD wording
  ``请核实是否为 PD`` driven by the frozen Query policy;
* replay-stable R2 handoff: create/continue/supersede/carry-forward with
  strict prior-ref rules and no proposed closure.

All data is synthetic and offline.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict

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
    CenterQueryPolicy,
    ChangeLedgerMember,
    CoverageStatus,
    Denominator,
    ExpectedSet,
    GapMember,
    LineageContext,
    Opportunity,
    VisibilityDecision,
    d09_content_hash,
    d09_unit_stable_core,
)
from mm_r4.d09_evaluator import evaluate  # noqa: E402
from mm_r4.d09_projection import (  # noqa: E402
    D09ProjectionError,
    build_d09_audience_projection,
    build_d09_count_surface,
    build_d09_deep_links,
    build_d09_hotspots,
    build_d09_query_draft,
    build_d09_r2_handoff,
    build_d09_risk_marker,
    d09_evaluation_content_identity,
    d09_public_risk_identity,
    project_d09_run,
    validate_d09_r2_handoff,
    validate_query_draft,
)

from test_d09_runtime_contract import (  # noqa: E402
    _sha,
    _authority,
    _base_typed_input,
    _definition,
    _query_decision,
    _query_policy,
    _risk,
    _window,
)
from test_d09_adapter import load_artifacts, run_case  # noqa: E402


def _evaluate(**overrides: Any):
    typed = _base_typed_input(**overrides)
    return typed, evaluate(typed)


def _policy_without_pd(fanout: int = 100) -> CenterQueryPolicy:
    payload = {
        "policy_id": "SYN-QPOL-NOPD-1",
        "mode_contract_version": "SYN-D09-MODE-001",
        "max_query_member_fanout": fanout,
        "member_order_policy": "stable_member_ref_ascending",
        "redundancy_rule_ref": "SYN-QRED-RULE-1",
        "allowed_action_kinds": ["request_record_verification"],
        "pd_wording_rule_ref": "SYN-PD-WORDING-1",
        "effective_interval": "synthetic-open-interval",
    }
    return CenterQueryPolicy(
        policy_id=payload["policy_id"],
        mode_contract_version=payload["mode_contract_version"],
        max_query_member_fanout=payload["max_query_member_fanout"],
        member_order_policy=payload["member_order_policy"],
        redundancy_rule_ref=payload["redundancy_rule_ref"],
        allowed_action_kinds=tuple(payload["allowed_action_kinds"]),
        pd_wording_rule_ref=payload["pd_wording_rule_ref"],
        content_hash=d09_content_hash(payload),
        effective_interval=payload["effective_interval"],
    )


def _query_content_hash(draft: Any) -> str:
    return d09_content_hash({
        "query_draft_id": draft.query_draft_id,
        "unit_stable_core": draft.unit_stable_core,
        "query_owner": draft.query_owner,
        "basis_sentence": draft.basis_sentence,
        "finding_sentence": draft.finding_sentence,
        "action_sentence": draft.action_sentence,
        "member_refs": list(draft.member_refs),
        "evidence_refs": list(draft.evidence_refs),
        "source_locator_ids": list(draft.source_locator_ids),
        "scope_binding_id": draft.scope_binding_id,
        "redundancy_decision": draft.redundancy_decision,
        "max_query_member_fanout": draft.max_query_member_fanout,
        "basis_refs": list(draft.basis_refs),
        "source_revision_refs": list(draft.source_revision_refs),
    })


def _gap(member_id: str, subject: str, *, locator: str = "SYN-LOC-G",
         anchor: str = "2026-02-01", anchor_state: str = "resolved",
         loc_state: str = "locatable",
         gap_kind: str = "missing_required_field") -> GapMember:
    return GapMember(
        member_id=member_id,
        subject_stable_id=subject,
        site_stable_id="SYN-SITE-1",
        producer_domain="D05",
        gap_kind=gap_kind,
        gap_opportunity_id=f"SYN-GAPOPP-{member_id}",
        gap_definition_id="SYN-GAPDEF-1",
        normalized_field_or_process_identity="SYN-FIELD-1",
        obligation_or_opportunity_ref=f"SYN-OBL-{member_id}",
        visit_or_time_anchor_refs=(anchor,) if anchor else (),
        cutoff_relation="in_cutoff",
        source_locator_refs=(locator,),
        source_locator_resolution_state=loc_state,
        anchor_resolution_state=anchor_state,
    )


def _gap_positive_args(gap_count: int = 9) -> Dict[str, Any]:
    gaps = tuple(_gap(f"GAP-{n}", f"SYN-SUBJ-{n}") for n in range(1, gap_count + 1))
    return dict(
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
            expected_opportunity_count=42, observed_opportunity_count=33,
            opportunity_state="sufficient"),
    )


# ---------------------------------------------------------------------------
# Audience visibility
# ---------------------------------------------------------------------------


class TestAudienceProjection(unittest.TestCase):
    def test_positive_payload_present_with_risk_and_query(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        projection = build_d09_audience_projection(typed, result)
        self.assertTrue(projection.audience_payload_present)
        self.assertTrue(projection.risk_present)
        self.assertTrue(projection.query_present)
        self.assertTrue(projection.journey_marker_present)
        self.assertEqual(projection.hidden_member_count, 0)
        self.assertEqual(projection.projectable_member_refs,
                         ("R-1", "R-2"))
        self.assertFalse(projection.disclosure_leak_present)

    def test_global_gate_emits_no_payload(self) -> None:
        typed, result = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        self.assertEqual(result.unit_count, 0)
        projection = build_d09_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.risk_present)
        self.assertFalse(projection.query_present)
        self.assertFalse(projection.journey_marker_present)
        self.assertFalse(projection.hotspot_present)

    def test_admitted_not_evaluable_has_no_payload_but_count_surface(self) -> None:
        typed, result = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.disposition, "not_evaluable")
        projection = build_d09_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.risk_present)
        self.assertFalse(projection.query_present)
        self.assertFalse(projection.journey_marker_present)
        self.assertFalse(projection.hotspot_present)
        self.assertEqual(projection.coverage_state, "missing")
        self.assertEqual(projection.coverage_zh, "本次可评价范围/数据完整性")
        # the independent count/status surface still explains the state
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.disposition_zh, "暂无法评价（附原因）")
        self.assertEqual(counts.coverage_state_zh, "缺失")

    def test_all_uncovered_hidden_suppresses_built_query(self) -> None:
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
        self.assertEqual(result.query_count, 1)  # internal ledger
        self.assertIsNone(build_d09_query_draft(typed, result))
        projection = build_d09_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.query_present)
        self.assertFalse(projection.risk_present)
        self.assertFalse(projection.journey_marker_present)
        self.assertFalse(projection.hotspot_present)
        self.assertIsNone(build_d09_risk_marker(typed, result))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 0)
        self.assertEqual(counts.affected_subject_count, 0)
        self.assertEqual(counts.event_count, 0)
        self.assertEqual(counts.center_pattern_count, 0)
        self.assertEqual(counts.query_count, 0)
        self.assertEqual(counts.query_count_zh, "查询草稿 0 条")

    def test_hidden_members_never_reach_any_audience_payload(self) -> None:
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
        self.assertEqual(result.disposition, "positive")
        bundle = project_d09_run(typed, result)
        self.assertNotIn("R-3", bundle.audience.projectable_member_refs)
        self.assertEqual(bundle.audience.hidden_member_count, 1)
        for hotspot in bundle.hotspots:
            self.assertNotIn("R-3", hotspot.member_risk_refs)
        for link in bundle.deep_links:
            self.assertNotEqual(link.member_ref, "R-3")
        assert bundle.query_draft is not None
        self.assertNotIn("R-3", bundle.query_draft.member_refs)
        self.assertNotIn("R-3", bundle.query_draft.basis_sentence
                         + bundle.query_draft.finding_sentence
                         + bundle.query_draft.action_sentence)
        self.assertNotIn("R-3", bundle.counts.individual_risk_zh
                         + bundle.counts.affected_subjects_zh
                         + bundle.counts.event_count_zh)
        self.assertEqual(bundle.counts.visible_individual_risk_count, 2)
        self.assertEqual(bundle.counts.rate_zh, None)


# ---------------------------------------------------------------------------
# Authoritative typed visibility partition
# ---------------------------------------------------------------------------


class TestVisibilityPartition(unittest.TestCase):
    def test_unknown_ref_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1", "R-2", "R-BOGUS")))
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_projectable_outside_evaluation_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1",),
                projectable_member_refs=("R-1", "R-2")))
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_hidden_outside_evaluation_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1",),
                hidden_member_refs=("R-2",),
                hidden_reason_codes=("blinded_group",)))
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_projectable_hidden_overlap_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                projectable_member_refs=("R-1", "R-2"),
                hidden_member_refs=("R-2",),
                hidden_reason_codes=("blinded_group",)))
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_non_reconciling_explicit_partition_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  _risk("R-3", "SYN-SUBJ-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1", "R-2", "R-3"),
                projectable_member_refs=("R-1",),
                hidden_member_refs=("R-2",),
                hidden_reason_codes=("blinded_group",)))
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_explicit_partition_is_authoritative(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  _risk("R-3", "SYN-SUBJ-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1", "R-2", "R-3"),
                projectable_member_refs=("R-1", "R-2"),
                hidden_member_refs=("R-3",),
                hidden_reason_codes=("blinded_group",),
                visible_n=2, eligible_n=42,
                rate_projection_state="suppressed"))
        bundle = project_d09_run(typed, result)
        self.assertEqual(bundle.audience.evaluation_member_refs,
                         ("R-1", "R-2", "R-3"))
        self.assertEqual(bundle.audience.projectable_member_refs,
                         ("R-1", "R-2"))
        self.assertEqual(bundle.audience.hidden_member_refs, ("R-3",))
        self.assertEqual(bundle.audience.hidden_member_count, 1)
        self.assertEqual(bundle.counts.visible_individual_risk_count, 2)
        self.assertEqual(bundle.counts.visible_affected_subject_count, 2)
        assert bundle.query_draft is not None
        self.assertEqual(bundle.query_draft.member_refs, ("R-1", "R-2"))
        for link in bundle.deep_links:
            self.assertNotEqual(link.member_ref, "R-3")
        for hotspot in bundle.hotspots:
            self.assertNotIn("R-3", hotspot.member_risk_refs)
        validation = validate_query_draft(bundle.query_draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_explicit_evaluation_only_derives_projectable(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  _risk("R-3", "SYN-SUBJ-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                evaluation_member_refs=("R-1", "R-2")))
        projection = build_d09_audience_projection(typed, result)
        self.assertEqual(projection.evaluation_member_refs, ("R-1", "R-2"))
        self.assertEqual(projection.projectable_member_refs, ("R-1", "R-2"))
        self.assertEqual(projection.hidden_member_count, 0)


# ---------------------------------------------------------------------------
# Separated count surface
# ---------------------------------------------------------------------------


class TestCountSurface(unittest.TestCase):
    def test_frozen_chinese_forms_and_separation(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", event="SYN-EVT-1"),
            _risk("R-2", "SYN-SUBJ-2", event="SYN-EVT-2"),
            _risk("R-3", "SYN-SUBJ-2", event="SYN-EVT-2")))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 3)
        self.assertEqual(counts.affected_subject_count, 2)
        self.assertEqual(counts.event_count, 2)
        self.assertEqual(counts.center_pattern_count, 1)
        self.assertEqual(counts.clue_count, 0)
        self.assertEqual(counts.query_count, 1)
        self.assertEqual(counts.individual_risk_zh, "相关个体风险 3 条")
        self.assertEqual(counts.affected_subjects_zh, "受影响受试者 2 名")
        self.assertEqual(counts.event_count_zh, "事件 2 起")
        self.assertEqual(counts.center_pattern_count_zh, "中心模式 1 项")
        self.assertEqual(counts.coverage_zh, "本次可评价范围/数据完整性")
        self.assertEqual(counts.coverage_state_zh, "完整")
        self.assertEqual(counts.rate_zh, "2/42（4.8%）")
        self.assertEqual(counts.lifecycle_zh, "进行中")
        self.assertEqual(counts.disposition_zh, "发现该类中心模式")

    def test_counts_are_never_summed(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2"),
            _risk("R-3", "SYN-SUBJ-2", event="SYN-EVT-2")))
        counts = build_d09_count_surface(typed, result)
        # The six mandated counts are individually exposed; the surface
        # carries no aggregate "total" field and no summing method.
        fields = (counts.individual_risk_count, counts.affected_subject_count,
                  counts.event_count, counts.center_pattern_count,
                  counts.clue_count, counts.query_count)
        self.assertEqual(counts.individual_risk_count, 3)
        self.assertEqual(counts.affected_subject_count, 2)
        self.assertEqual(counts.center_pattern_count, 1)
        self.assertNotEqual(counts.individual_risk_count,
                            counts.affected_subject_count)
        self.assertFalse(hasattr(counts, "total_risk_count"))
        self.assertNotEqual(sum(fields), 2 * counts.individual_risk_count)

    def test_visible_counts_equal_raw_when_no_hidden(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.visible_individual_risk_count,
                         counts.individual_risk_count)
        self.assertEqual(counts.visible_affected_subject_count,
                         counts.affected_subject_count)
        self.assertEqual(counts.visible_event_count, counts.event_count)

    def test_gap_only_positive_keeps_counts_separate(self) -> None:
        typed, result = _evaluate(**_gap_positive_args(9))
        self.assertEqual(result.disposition, "positive")
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 0)
        self.assertEqual(counts.affected_subject_count, 9)
        self.assertEqual(counts.gap_opportunity_count, 9)
        self.assertEqual(counts.center_pattern_count, 1)
        self.assertEqual(counts.individual_risk_zh, "相关个体风险 0 条")
        self.assertEqual(counts.affected_subjects_zh, "受影响受试者 9 名")

    def test_suppressed_rate_never_shows_precision(self) -> None:
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
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.rate_projection_state, "suppressed")
        self.assertIsNone(counts.rate_zh)
        self.assertEqual(counts.visible_n, 2)
        self.assertEqual(counts.eligible_n, 42)
        self.assertEqual(counts.hidden_member_count, 1)
        self.assertEqual(counts.visible_affected_subject_count, 2)

    def test_boundary_clue_count_never_becomes_query(self) -> None:
        typed, result = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(result.disposition, "boundary")
        self.assertEqual(counts.clue_count, 1)
        self.assertEqual(counts.query_count, 0)
        self.assertIsNone(counts.clue_count_zh)
        self.assertEqual(counts.disposition_zh, "边界情况")

    def test_gate_surface_zero_counts(self) -> None:
        typed, result = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        counts = build_d09_count_surface(typed, result)
        self.assertEqual(counts.center_pattern_count, 0)
        self.assertEqual(counts.clue_count, 0)
        self.assertEqual(counts.query_count, 0)


# ---------------------------------------------------------------------------
# D09 center-pattern risk marker
# ---------------------------------------------------------------------------


class TestRiskMarker(unittest.TestCase):
    def test_positive_marker_public_identity(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        marker = build_d09_risk_marker(typed, result)
        self.assertIsNotNone(marker)
        assert marker is not None
        identity = marker.public_risk_identity
        self.assertEqual(identity["domain_id"], "D09_center_pattern")
        self.assertEqual(identity["public_identity_version"], "d09_public_v1")
        self.assertEqual(identity["scope_type"], "site")
        self.assertEqual(identity["site_stable_id"], "SYN-SITE-1")
        self.assertEqual(identity["stable_source_or_event_identity"][0],
                         "SYN-DEF-1")
        self.assertEqual(identity["normalized_concept"][0],
                         "repeated_subject_risk")
        self.assertEqual(marker.risk_owner, "D09")
        self.assertEqual(marker.risk_kind, "center_pattern")
        self.assertEqual(marker.aggregation_level, "site_pattern")
        self.assertEqual(marker.member_refs, ("R-1", "R-2"))
        self.assertTrue(marker.content_hash)

    def test_marker_identity_excludes_run_and_snapshot(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        marker_a = build_d09_risk_marker(typed, result)
        swapped = replace(typed, run_ref="SYN-RUN-OTHER",
                          snapshot_ref="SYN-SNAP-OTHER")
        marker_b = build_d09_risk_marker(swapped, evaluate(swapped))
        assert marker_a is not None and marker_b is not None
        self.assertEqual(marker_a.marker_id, marker_b.marker_id)
        self.assertEqual(marker_a.public_risk_identity,
                         marker_b.public_risk_identity)
        self.assertEqual(marker_a.content_hash, marker_b.content_hash)

    def test_projection_rejects_forged_evaluator_result(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),))
        self.assertEqual(result.disposition, "boundary")
        forged = replace(result, disposition="positive")
        with self.assertRaises(D09ProjectionError):
            build_d09_risk_marker(typed, forged)
        with self.assertRaises(D09ProjectionError):
            build_d09_query_draft(typed, forged)
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, forged)

    def test_marker_excludes_hidden_members_and_locators(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1", locator="SYN-LOC-1"),
                                  _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2"),
                                  _risk("R-3", "SYN-SUBJ-3", locator="SYN-LOC-3")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                hidden_member_refs=("R-3",),
                hidden_reason_codes=("blinded_group",),
                visible_n=2, eligible_n=42,
                rate_projection_state="suppressed"))
        marker = build_d09_risk_marker(typed, result)
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker.member_refs, ("R-1", "R-2"))
        self.assertNotIn("SYN-LOC-3", marker.source_locator_ids)
        # the R2 lifecycle handoff keeps the complete unit member set
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        self.assertEqual(handoff.member_refs, ("R-1", "R-2", "R-3"))

    def test_replay_stable_marker(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        first = build_d09_risk_marker(typed, result)
        second = build_d09_risk_marker(typed, result)
        self.assertEqual(first, second)

    def test_non_positive_runs_never_get_marker(self) -> None:
        boundary = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertIsNone(build_d09_risk_marker(boundary[0], boundary[1]))
        negative = _evaluate(subject_risk_members=())
        self.assertIsNone(build_d09_risk_marker(negative[0], negative[1]))
        not_evaluable = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),))
        self.assertIsNone(build_d09_risk_marker(not_evaluable[0],
                                                not_evaluable[1]))
        gate = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        self.assertIsNone(build_d09_risk_marker(gate[0], gate[1]))


# ---------------------------------------------------------------------------
# Hotspot subject rows
# ---------------------------------------------------------------------------


class TestHotspots(unittest.TestCase):
    def test_n1_boundary_keeps_mandatory_hotspot(self) -> None:
        typed, result = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertEqual(result.disposition, "boundary")
        self.assertEqual(result.affected_subject_count, 1)
        hotspots = build_d09_hotspots(typed, result)
        self.assertEqual(len(hotspots), 1)
        self.assertEqual(hotspots[0].subject_ref, "SYN-SUBJ-1")
        self.assertEqual(hotspots[0].member_risk_refs, ("R-1",))
        self.assertEqual(hotspots[0].monitoring_priority, "medium")
        self.assertEqual(hotspots[0].priority_rule_ref, "SYN-RULE-PRIO-1")
        self.assertEqual(hotspots[0].source_locator_refs, ("SYN-LOC-1",))
        self.assertIsNone(build_d09_risk_marker(typed, result),
                          "hotspot is a projection, never a risk")

    def test_hotspot_replay_stable(self) -> None:
        typed, result = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        first = build_d09_hotspots(typed, result)
        second = build_d09_hotspots(typed, result)
        self.assertEqual(first, second)

    def test_subthreshold_boundary_without_high_priority_no_hotspot(self) -> None:
        typed, result = _evaluate(
            resolved_authority_decision=_authority(repeated_minimum=3),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.disposition, "boundary")
        self.assertEqual(result.affected_subject_count, 2)
        self.assertEqual(build_d09_hotspots(typed, result), ())

    def test_high_priority_member_hotspot_on_boundary(self) -> None:
        typed, result = _evaluate(
            resolved_authority_decision=_authority(repeated_minimum=3),
            subject_risk_members=(
                _risk("R-1", "SYN-SUBJ-1"),
                _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        high = replace(typed.subject_risk_members[0],
                       monitoring_priority="high")
        typed_high = replace(typed, subject_risk_members=(high, typed.subject_risk_members[1]))
        result_high = evaluate(typed_high)
        self.assertEqual(result_high.disposition, "boundary")
        hotspots = build_d09_hotspots(typed_high, result_high)
        self.assertEqual([h.subject_ref for h in hotspots], ["SYN-SUBJ-1"])
        self.assertEqual(hotspots[0].monitoring_priority, "high")

    def test_multi_domain_member_hotspot_on_boundary(self) -> None:
        from mm_r4.d09_contracts import SubjectRiskMember
        d08_member = SubjectRiskMember(
            member_id="R-3", subject_stable_id="SYN-SUBJ-2",
            site_stable_id="SYN-SITE-1", producer_domain="D08",
            risk_kind="d08_cross_domain_relation",
            monitoring_priority="medium",
            public_r4_risk_identity="SYN-RID-R-3",
            source_event_identity="SYN-EVT-3", event_time_ref="2026-02-01",
            cutoff_relation="in_cutoff", origin_decision="distinct",
            source_locator_refs=("SYN-LOC-3",))
        typed, result = _evaluate(
            resolved_authority_decision=_authority(repeated_minimum=3),
            pattern_definition=_definition(accepted_member_risk_kinds=(
                "d01_seriousness_hospital_death", "d08_cross_domain_relation")),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2"),
                                  d08_member))
        self.assertEqual(result.disposition, "boundary")
        self.assertEqual(result.affected_subject_count, 2)
        hotspots = build_d09_hotspots(typed, result)
        # SYN-SUBJ-2 carries members from D01 and D08 -> multi-domain hotspot
        self.assertEqual([h.subject_ref for h in hotspots], ["SYN-SUBJ-2"])
        self.assertEqual(len(hotspots[0].member_risk_refs), 2)

    def test_positive_lists_every_affected_subject(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        hotspots = build_d09_hotspots(typed, result)
        self.assertEqual({h.subject_ref for h in hotspots},
                         {"SYN-SUBJ-1", "SYN-SUBJ-2"})

    def test_hidden_high_priority_member_never_hotspot(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                hidden_member_refs=("R-2",),
                hidden_reason_codes=("blinded_group",),
                visible_n=1, eligible_n=42,
                rate_projection_state="suppressed"))
        hidden_high = replace(typed.subject_risk_members[1],
                              monitoring_priority="high")
        typed_high = replace(typed, subject_risk_members=(
            typed.subject_risk_members[0], hidden_high))
        result_high = evaluate(typed_high)
        hotspots = build_d09_hotspots(typed_high, result_high)
        for hotspot in hotspots:
            self.assertNotIn("R-2", hotspot.member_risk_refs)

    def test_gate_and_not_evaluable_emit_no_hotspots(self) -> None:
        gate = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        self.assertEqual(build_d09_hotspots(gate[0], gate[1]), ())
        not_evaluable = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1",
                                        loc_state="missing"),))
        self.assertEqual(build_d09_hotspots(not_evaluable[0],
                                            not_evaluable[1]), ())


# ---------------------------------------------------------------------------
# Deep links
# ---------------------------------------------------------------------------


class TestDeepLinks(unittest.TestCase):
    def test_locatable_member_gets_resolved_target(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        links = build_d09_deep_links(typed, result)
        self.assertEqual(len(links), 2)
        link = links[0]
        self.assertEqual(link.target_state, "locatable")
        self.assertEqual(link.source_locator, "SYN-LOC-1")
        self.assertEqual(link.locator_resolution_state, "locatable")
        self.assertEqual(link.visit_or_time_anchor, "2026-02-01")
        self.assertEqual(link.anchor_resolution_state, "resolved")
        self.assertIsNone(link.unavailable_message)
        self.assertEqual(link.return_state_key, "SYN-RID-R-1")
        self.assertEqual(link.project_ref, "SYN-PROJECT-1")
        self.assertEqual(link.run_ref, "SYN-RUN-1")
        self.assertEqual(link.snapshot_ref, "SYN-SNAP-1")
        self.assertEqual(link.site_ref, "SYN-SITE-1")
        self.assertEqual(link.subject_ref, "SYN-SUBJ-1")

    def test_missing_locator_yields_unavailable_no_fabricated_jump(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", loc_state="missing"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        self.assertEqual(result.disposition, "boundary")
        links = {link.member_ref: link for link in build_d09_deep_links(typed, result)}
        missing = links["R-1"]
        self.assertEqual(missing.target_state, "unavailable")
        self.assertIsNone(missing.source_locator)
        self.assertEqual(missing.unavailable_message, "来源暂无法定位")
        self.assertEqual(missing.locator_resolution_state, "missing")
        resolved = links["R-2"]
        self.assertEqual(resolved.target_state, "locatable")
        self.assertEqual(resolved.source_locator, "SYN-LOC-2")

    def test_unresolved_gap_anchor_yields_unavailable(self) -> None:
        typed, result = _evaluate(**_gap_positive_args(2))
        self.assertEqual(result.disposition, "positive")
        unresolved = replace(typed.gap_members[0],
                             anchor_resolution_state="unresolved")
        typed_u = replace(typed, gap_members=(
            unresolved, typed.gap_members[1]))
        result_u = evaluate(typed_u)
        self.assertEqual(result_u.disposition, "boundary")
        links = {link.member_ref: link
                 for link in build_d09_deep_links(typed_u, result_u)}
        self.assertEqual(links["GAP-1"].target_state, "unavailable")
        self.assertEqual(links["GAP-1"].unavailable_message, "来源暂无法定位")
        self.assertIsNone(links["GAP-1"].visit_or_time_anchor)
        self.assertEqual(links["GAP-1"].anchor_resolution_state, "unresolved")
        self.assertEqual(links["GAP-2"].target_state, "locatable")
        self.assertEqual(links["GAP-2"].visit_or_time_anchor, "2026-02-01")

    def test_change_member_without_locator_unavailable(self) -> None:
        from mm_r4.d09_contracts import ChangeLedgerMember
        changes = tuple(ChangeLedgerMember(
            member_id=f"CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1",
            change_ledger_member_id=f"SYN-CHGID-{n}",
            current_window_instance_ref="SYN-WIN-2-INST",
            prior_window_instance_ref="SYN-WIN-1-INST",
            comparable_state="comparable", change_kind="increased",
            change_cause="data", unit="rate_per_subject",
            supporting_member_refs=("SYN-RISK-1",))
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
        self.assertEqual(links[0].target_state, "unavailable")
        self.assertEqual(links[0].unavailable_message, "来源暂无法定位")

    def _trend_args(self, *, with_locators: bool,
                    prior_ref: str = "SYN-WIN-1-INST") -> Dict[str, Any]:
        changes = tuple(ChangeLedgerMember(
            member_id=f"CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1",
            change_ledger_member_id=f"SYN-CHGID-{n}",
            current_window_instance_ref="SYN-WIN-2-INST",
            prior_window_instance_ref=prior_ref,
            comparable_state="comparable", change_kind="increased",
            change_cause="data", unit="rate_per_subject",
            supporting_member_refs=("SYN-RISK-1",),
            source_locator_refs=(f"SYN-LOC-CHG-{n}",) if with_locators else ())
            for n in range(1, 4))
        return dict(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window(stable_id="SYN-WIN-1"),
                              _window(stable_id="SYN-WIN-2")),
            subject_risk_members=(),
            change_ledger_members=changes,
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))

    def test_change_member_locatable_with_current_window_anchor(self) -> None:
        typed, result = _evaluate(**self._trend_args(with_locators=True))
        self.assertEqual(result.disposition, "positive")
        links = build_d09_deep_links(typed, result)
        self.assertEqual(len(links), 3)
        link = links[0]
        self.assertEqual(link.target_state, "locatable")
        self.assertEqual(link.visit_or_time_anchor, "SYN-WIN-2-INST")
        self.assertEqual(link.anchor_resolution_state, "resolved")
        self.assertEqual(link.source_locator, "SYN-LOC-CHG-1")
        self.assertEqual(link.member_kind, "change_ledger")
        self.assertIn("SYN-WIN-2-INST", link.return_state_key)
        self.assertIn("SYN-WIN-1-INST", link.return_state_key)
        self.assertIn("SYN-CHGID-1", link.return_state_key)

    def test_change_member_missing_prior_ref_unavailable(self) -> None:
        typed, result = _evaluate(
            **self._trend_args(with_locators=True, prior_ref=""))
        self.assertEqual(result.disposition, "positive")
        links = build_d09_deep_links(typed, result)
        self.assertEqual(links[0].target_state, "unavailable")
        self.assertEqual(links[0].unavailable_message, "来源暂无法定位")
        self.assertIsNone(links[0].source_locator)
        self.assertIsNone(links[0].visit_or_time_anchor)
        self.assertEqual(links[0].anchor_resolution_state, "unresolved")

    def test_risk_member_without_event_time_anchor_unavailable(self) -> None:
        no_event = replace(_risk("R-1", "SYN-SUBJ-1"), event_time_ref="")
        typed, result = _evaluate(subject_risk_members=(
            no_event, _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        self.assertEqual(result.disposition, "positive")
        links = {link.member_ref: link
                 for link in build_d09_deep_links(typed, result)}
        self.assertEqual(links["R-1"].target_state, "unavailable")
        self.assertEqual(links["R-1"].unavailable_message, "来源暂无法定位")
        self.assertIsNone(links["R-1"].source_locator)
        self.assertIsNone(links["R-1"].visit_or_time_anchor)
        self.assertEqual(links["R-1"].anchor_resolution_state, "unresolved")
        self.assertEqual(links["R-2"].target_state, "locatable")

    def test_gap_member_without_anchor_unavailable_even_if_resolved(self) -> None:
        no_anchor = _gap("GAP-1", "SYN-SUBJ-1", anchor="",
                         anchor_state="resolved")
        typed, result = _evaluate(**_gap_positive_args(2))
        typed = replace(typed, gap_members=(
            no_anchor, typed.gap_members[1]))
        result = evaluate(typed)
        self.assertEqual(result.disposition, "positive")
        links = {link.member_ref: link
                 for link in build_d09_deep_links(typed, result)}
        self.assertEqual(links["GAP-1"].target_state, "unavailable")
        self.assertEqual(links["GAP-1"].unavailable_message, "来源暂无法定位")
        self.assertIsNone(links["GAP-1"].source_locator)
        self.assertEqual(links["GAP-2"].target_state, "locatable")

    def test_trend_member_missing_current_ref_unavailable(self) -> None:
        typed, result = _evaluate(
            **self._trend_args(with_locators=True, prior_ref="SYN-WIN-1-INST"))
        current = replace(typed.change_ledger_members[0],
                          current_window_instance_ref="")
        typed_c = replace(typed, change_ledger_members=(
            current, typed.change_ledger_members[1],
            typed.change_ledger_members[2]))
        result_c = evaluate(typed_c)
        self.assertEqual(result_c.disposition, "positive")
        links = {link.member_ref: link
                 for link in build_d09_deep_links(typed_c, result_c)}
        self.assertEqual(links["CHG-1"].target_state, "unavailable")
        self.assertEqual(links["CHG-1"].unavailable_message, "来源暂无法定位")
        self.assertIsNone(links["CHG-1"].source_locator)
        self.assertEqual(links["CHG-1"].anchor_resolution_state, "unresolved")
        self.assertEqual(links["CHG-2"].target_state, "locatable")

    def test_gate_and_not_evaluable_emit_no_deep_links(self) -> None:
        gate = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        self.assertEqual(build_d09_deep_links(gate[0], gate[1]), ())
        not_evaluable = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertEqual(build_d09_deep_links(not_evaluable[0],
                                              not_evaluable[1]), ())

    def test_hidden_member_never_has_a_link(self) -> None:
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
        links = build_d09_deep_links(typed, result)
        self.assertEqual({link.member_ref for link in links},
                         {"R-1", "R-2"})


# ---------------------------------------------------------------------------
# Query draft
# ---------------------------------------------------------------------------


class TestQueryDraft(unittest.TestCase):
    def test_positive_delta_query_three_sentences(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        draft = build_d09_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        self.assertTrue(draft.basis_sentence.startswith("依据："))
        self.assertTrue(draft.finding_sentence.startswith("发现："))
        self.assertTrue(draft.action_sentence.startswith("行动项："))
        self.assertEqual(draft.query_owner, "D09")
        self.assertTrue(draft.draft_only)
        self.assertEqual(draft.member_refs, ("R-1", "R-2"))
        self.assertEqual(draft.member_count, 2)
        self.assertEqual(draft.evidence_refs, ("SYN-LOC-1", "SYN-LOC-2"))
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])
        # native Chinese, no engineering ids in the prose
        self.assertIn("中心重复风险模式", draft.basis_sentence)
        self.assertIn("2026-01-01 至 2026-03-31", draft.basis_sentence)
        self.assertIn("本中心", draft.finding_sentence)
        self.assertIn("本次可评价范围/数据完整性", draft.finding_sentence)
        self.assertIn("涉及记录（2 条）", draft.finding_sentence)
        self.assertIn("受试者 SYN-SUBJ-1", draft.finding_sentence)
        self.assertIn("受试者 SYN-SUBJ-2", draft.finding_sentence)
        joined = draft.basis_sentence + draft.finding_sentence + draft.action_sentence
        for token in ("SYN-DEF-1", "SYN-RULE-POS-1", "SYN-WIN-1",
                      "SYN-D09-MODE-001", "R-1、R-2", "SYN-REV-1", "SYN-SITE-1"):
            self.assertNotIn(token, joined)
        # structured trace fields carry the engineering refs
        self.assertEqual(draft.basis_refs[0], "SYN-DEF-1")
        self.assertEqual(draft.basis_refs[1], "SYN-RULE-POS-1")
        self.assertEqual(draft.basis_refs[2], "SYN-WIN-1")
        self.assertEqual(draft.basis_refs[3], "SYN-D09-MODE-001")
        self.assertEqual(draft.source_revision_refs, ("SYN-REV-1",))

    def test_query_validator_rejects_rehashed_identity_and_sentence_tampering(
            self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        mutations = (
            {"query_draft_id": _sha("forged-query")},
            {"unit_stable_core": "forged-stable-core"},
            {"scope_binding_id": "forged-scope"},
            {"finding_sentence": draft.finding_sentence.replace(
                "本中心", "其他中心", 1)},
        )
        for mutation in mutations:
            tampered = replace(draft, **mutation)
            tampered = replace(tampered, content_hash=_query_content_hash(tampered))
            validation = validate_query_draft(tampered, typed, result)
            with self.subTest(mutation=mutation):
                self.assertFalse(validation["valid"])
                self.assertIn(
                    "query_draft_not_exact_authoritative_projection",
                    validation["reasons"])

    def test_query_rejects_structured_refs_in_clinical_label(self) -> None:
        members = (_risk("R-1", "SYN-SUBJ-1"),
                   _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2"))
        for injected in (
                "SYN-DEF-1", "SYN-RULE-POS-1", "SYN-D09-MODE-001",
                "SYN-WIN-1", "SYN-REV-1", "rule_ref=FORGED",
                "pattern_id=FORGED", "pattern_definition_id=FORGED",
                "mode_contract_version=FORGED", "window_ref=FORGED",
                "revision=FORGED", "scope_binding_id=FORGED",
                "policy_ref=FORGED", "rule_ref\u200b=FORGED",
                "rule_ref＝FORGED", "ｒｕｌｅ＿ｒｅｆ＝FORGED",
                "rule_ref\u034f=FORGED", "rule_ref\ufe0f=FORGED",
                "rule_ref\u17b4=FORGED", "rule - ref = FORGED"):
            typed = _base_typed_input(
                subject_risk_members=members,
                audience_lexicon=replace(
                    _base_typed_input().audience_lexicon,
                    pattern_label_zh=f"中心模式 {injected}"))
            result = evaluate(typed)
            with self.subTest(injected=injected):
                with self.assertRaises(D09ProjectionError):
                    build_d09_query_draft(typed, result)

    def test_source_revision_set_order_does_not_change_query_identity(self) -> None:
        revisions_a = ("SYN-REV-B", "SYN-REV-A")
        revisions_b = tuple(reversed(revisions_a))
        hashes_a = tuple(_sha(f"d09-rev:{revision}") for revision in revisions_a)
        hashes_b = tuple(_sha(f"d09-rev:{revision}") for revision in revisions_b)
        members = (
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2"),
        )

        typed_a, result_a = _evaluate(
            source_revision_set=revisions_a,
            source_content_hashes=hashes_a,
            subject_risk_members=members,
        )
        typed_b, result_b = _evaluate(
            source_revision_set=revisions_b,
            source_content_hashes=hashes_b,
            subject_risk_members=members,
        )
        draft_a = build_d09_query_draft(typed_a, result_a)
        draft_b = build_d09_query_draft(typed_b, result_b)
        assert draft_a is not None and draft_b is not None

        self.assertEqual(draft_a.source_revision_refs,
                         ("SYN-REV-A", "SYN-REV-B"))
        self.assertEqual(draft_a, draft_b)
        self.assertTrue(validate_query_draft(
            draft_a, typed_a, result_a)["valid"])
        self.assertTrue(validate_query_draft(
            draft_b, typed_b, result_b)["valid"])

    def test_pd_wording_requires_exact_pd_member_fact(self) -> None:
        # verify_pd is an allowlist, not proof: no member carries the exact
        # structured PD fact -> no PD wording (fixes the 63 false positives)
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertNotIn("请核实是否为 PD", draft.action_sentence)
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_pd_wording_present_for_pd_unreported_gap_member(self) -> None:
        args = _gap_positive_args(2)
        args["gap_members"] = (
            _gap("GAP-1", "SYN-SUBJ-1", gap_kind="pd_unreported"),
            _gap("GAP-2", "SYN-SUBJ-2", locator="SYN-LOC-G2"))
        typed, result = _evaluate(**args)
        self.assertEqual(result.disposition, "positive")
        self.assertEqual(result.query_count, 1)
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertIn("请核实是否为 PD", draft.action_sentence)
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_pd_wording_requires_policy_allowlist_too(self) -> None:
        args = _gap_positive_args(2)
        args["gap_members"] = (
            _gap("GAP-1", "SYN-SUBJ-1", gap_kind="pd_unreported"),
            _gap("GAP-2", "SYN-SUBJ-2", locator="SYN-LOC-G2"))
        args["center_query_policy"] = _policy_without_pd()
        args["query_redundancy_decision"] = _query_decision(
            args["gap_members"], fanout=100)
        typed, result = _evaluate(**args)
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertNotIn("请核实是否为 PD", draft.action_sentence)
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_hidden_pd_member_never_triggers_pd_wording(self) -> None:
        args = _gap_positive_args(2)
        args["gap_members"] = (
            _gap("GAP-1", "SYN-SUBJ-1", gap_kind="pd_unreported"),
            _gap("GAP-2", "SYN-SUBJ-2", locator="SYN-LOC-G2"))
        args["visibility_decision"] = VisibilityDecision(
            audience_scope_id="SYN-AUD-1",
            hidden_member_refs=("GAP-1",),
            hidden_reason_codes=("blinded_group",),
            visible_n=1, eligible_n=5,
            rate_projection_state="suppressed")
        typed, result = _evaluate(**args)
        self.assertEqual(result.disposition, "positive")
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertEqual(draft.member_refs, ("GAP-2",))
        self.assertNotIn("请核实是否为 PD", draft.action_sentence)
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_fully_covered_suppresses_query(self) -> None:
        members = (_risk("R-1", "SYN-SUBJ-1", query_refs=("SYN-Q-1",)),
                   _risk("R-2", "SYN-SUBJ-2", query_refs=("SYN-Q-2",)))
        typed, result = _evaluate(
            subject_risk_members=members,
            query_redundancy_decision=_query_decision(
                members, decision="fully_covered_by_member_queries"))
        self.assertEqual(result.query_count, 0)
        self.assertIsNone(build_d09_query_draft(typed, result))

    def test_fanout_exceeded_suppresses_query(self) -> None:
        members = tuple(_risk(f"R-{n}", f"SYN-SUBJ-{n}")
                        for n in range(1, 13))
        typed, result = _evaluate(
            subject_risk_members=members,
            query_redundancy_decision=_query_decision(members, fanout=10))
        self.assertEqual(result.query_count, 0)
        self.assertIsNone(build_d09_query_draft(typed, result))

    def test_boundary_never_queries(self) -> None:
        typed, result = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertIsNone(build_d09_query_draft(typed, result))

    def test_query_lists_complete_projectable_uncovered_set(self) -> None:
        members = tuple(_risk(f"R-{n}", f"SYN-SUBJ-{n}")
                        for n in range(1, 9))
        typed, result = _evaluate(
            subject_risk_members=members,
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                hidden_member_refs=("R-8",),
                hidden_reason_codes=("blinded_group",),
                visible_n=7, eligible_n=42,
                rate_projection_state="suppressed"))
        self.assertEqual(result.query_count, 1)
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertEqual(draft.member_refs, tuple(f"R-{n}" for n in range(1, 8)))
        self.assertEqual(draft.member_count, 7)
        self.assertNotIn("R-8", draft.finding_sentence)
        validation = validate_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_validation_rejects_tampered_hash_and_tokens(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        tampered = replace(draft, content_hash="0" * 64)
        validation = validate_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("content_hash_stale", validation["reasons"])
        bad_token = replace(draft, action_sentence="行动项：请核实正式事实。")
        validation = validate_query_draft(bad_token, typed, result)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("forbidden" in reason
                            for reason in validation["reasons"]))
        hidden_leak = replace(draft, member_refs=("R-1", "R-2", "R-HIDDEN"))
        validation = validate_query_draft(hidden_leak, typed, result)
        self.assertFalse(validation["valid"])

    def test_unlocatable_query_member_fails_closed(self) -> None:
        # trend positives are not covered by the evaluator's locatability
        # gate for change members: a projectable uncovered member without a
        # locator must raise, never produce a partial-evidence draft
        changes = tuple(ChangeLedgerMember(
            member_id=f"CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1",
            change_ledger_member_id=f"SYN-CHGID-{n}",
            current_window_instance_ref="SYN-WIN-2-INST",
            prior_window_instance_ref="SYN-WIN-1-INST",
            comparable_state="comparable", change_kind="increased",
            change_cause="data", unit="rate_per_subject",
            supporting_member_refs=("SYN-RISK-1",),
            source_locator_refs=(f"SYN-LOC-CHG-{n}",) if n != 2 else ())
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
        self.assertEqual(result.query_count, 1)
        with self.assertRaises(D09ProjectionError):
            build_d09_query_draft(typed, result)

    def test_validation_rejects_removed_evidence_locator(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertEqual(draft.evidence_refs, ("SYN-LOC-1", "SYN-LOC-2"))
        removed = replace(draft, evidence_refs=("SYN-LOC-1",))
        validation = validate_query_draft(removed, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_not_locatable_projectable",
                      validation["reasons"])

    def test_validation_rejects_source_locator_alias_tamper(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        tampered = replace(draft, source_locator_ids=("SYN-LOC-1",))
        validation = validate_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("source_locator_ids_mismatch", validation["reasons"])
        self.assertIn("content_hash_stale", validation["reasons"])
        empty = replace(draft, evidence_refs=())
        validation = validate_query_draft(empty, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_must_be_non_empty", validation["reasons"])

    def test_query_never_treated_as_workflow_state(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        draft = build_d09_query_draft(typed, result)
        assert draft is not None
        self.assertTrue(draft.draft_only)
        self.assertFalse(hasattr(draft, "status"))
        self.assertFalse(hasattr(draft, "state"))


# ---------------------------------------------------------------------------
# R2 lifecycle handoff
# ---------------------------------------------------------------------------


class TestR2Handoff(unittest.TestCase):
    def test_create_without_prior(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "create")
        self.assertIsNone(handoff.prior_risk_instance_ref)
        self.assertEqual(handoff.idempotency_key, handoff.handoff_id)
        self.assertEqual(handoff.lineage_relation, "none")
        self.assertEqual(handoff.pattern_definition_hash,
                         typed.pattern_definition.pattern_definition_content_hash)
        self.assertEqual(handoff.member_refs, ("R-1", "R-2"))
        self.assertEqual(handoff.monitoring_priority, "medium")
        validation = validate_d09_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_evaluation_identity_binds_decisive_authority_method_and_query_policy(
            self) -> None:
        members = (_risk("R-1", "SYN-SUBJ-1"),
                   _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2"))
        typed = _base_typed_input(subject_risk_members=members)
        base_identity = d09_evaluation_content_identity(typed)
        variants = (
            replace(typed, resolved_authority_decision=replace(
                typed.resolved_authority_decision,
                minimum_member_subject_count=3)),
            replace(typed, method_comparability_decision=replace(
                typed.method_comparability_decision,
                statistical_signal_role="supporting")),
            replace(
                typed,
                center_query_policy=_query_policy(1),
                query_redundancy_decision=_query_decision(
                    members, fanout=1)),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(
                    base_identity, d09_evaluation_content_identity(variant))

    def test_continue_with_prior_data_revision(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="continued_from_data_revision"))
        self.assertEqual(result.disposition, "positive")
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        self.assertEqual(handoff.prior_risk_instance_ref, "SYN-PRIOR-1")
        validation = validate_d09_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_carry_forward_never_proposes_closure(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="active",
                lineage_relation="continued_from_data_revision"),
            denominator=Denominator(
                denominator_kind="evaluable_subjects", denominator_value=0,
                denominator_state="unclosed"))
        self.assertEqual(result.disposition, "not_evaluable")
        self.assertTrue(result.downstream_handoff)
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        self.assertTrue(handoff.no_auto_close_reasons)
        validation = validate_d09_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_rule_or_method_change_supersedes(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="superseded_by_rule_or_method_change"))
        self.assertEqual(result.disposition, "boundary")
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "supersede")
        self.assertEqual(handoff.lineage_relation,
                         "superseded_by_rule_or_method_change")
        validation = validate_d09_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_continue_requires_prior_public_identity_ref(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref=None,
                carry_forward_state="none",
                lineage_relation="continued_from_data_revision"))
        self.assertEqual(result.disposition, "positive")
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, result)

    def test_supersede_requires_prior_public_identity_ref(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref=None,
                carry_forward_state="none",
                lineage_relation="superseded_by_rule_or_method_change"))
        self.assertEqual(result.disposition, "boundary")
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, result)

    def test_create_with_prior_public_ref_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref=None,
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="none"))
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, result)

    def test_prior_public_ref_tamper_rejected_by_validation(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="continued_from_data_revision"))
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        self.assertEqual(handoff.prior_public_risk_identity_ref,
                         "SYN-PRIOR-ID-1")
        tampered = replace(handoff,
                           prior_public_risk_identity_ref="SYN-TAMPERED-ID")
        validation = validate_d09_r2_handoff(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("prior_public_ref_mismatch", validation["reasons"])
        dropped = replace(handoff, prior_public_risk_identity_ref=None)
        validation = validate_d09_r2_handoff(dropped, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("non_create_without_prior_public_ref",
                      validation["reasons"])

    def test_r2_action_vocabulary_boundary(self) -> None:
        # the contract's full R2 vocabulary (update/propose_close/reopen) is
        # a downstream R2 lifecycle surface; this projection initiates only
        # create/continue/supersede and the validator rejects the rest
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        self.assertEqual(handoff.action, "create")
        for action in ("update", "propose_close", "reopen"):
            tampered = replace(handoff, action=action)
            validation = validate_d09_r2_handoff(tampered, typed, result)
            self.assertFalse(validation["valid"], action)
            self.assertTrue(any("action_not_d09_initiated" in reason
                                for reason in validation["reasons"]), action)

    def test_identity_bearing_field_tamper_probes(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="continued_from_data_revision"))
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        probes = (
            ("member_refs", ("R-1",), "member_refs_mismatch"),
            ("measure_ledger_ref", "0" * 64, "measure_ledger_ref_mismatch"),
            ("completeness_decision_ref", "0" * 64,
             "completeness_decision_ref_mismatch"),
            ("monitoring_priority", "high", "monitoring_priority_mismatch"),
            ("no_auto_close_reasons", ("存在高监察优先级成员",),
             "no_auto_close_reasons_mismatch"),
            ("stable_core_ref", "0" * 64, "stable_core_stale"),
            ("pattern_definition_hash", "0" * 64,
             "pattern_definition_hash_stale"),
        )
        for field, value, reason in probes:
            tampered = replace(handoff, **{field: value})
            validation = validate_d09_r2_handoff(tampered, typed, result)
            self.assertFalse(validation["valid"], field)
            self.assertIn(reason, validation["reasons"], field)

    def test_handoff_and_idempotency_key_cannot_be_jointly_forged(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        forged = replace(handoff, handoff_id="0" * 64,
                         idempotency_key="0" * 64)
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("handoff_id_stale", validation["reasons"])

    def test_create_with_prior_contradiction_fails_closed(self) -> None:
        typed, result = _evaluate(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="none",
                lineage_relation="first_seen"))
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, result)

    def test_carry_forward_without_prior_fails_closed(self) -> None:
        typed, result = _evaluate(
            lineage_context=LineageContext(
                carry_forward_state="active",
                lineage_relation="continued_from_data_revision"),
            denominator=Denominator(
                denominator_kind="evaluable_subjects", denominator_value=0,
                denominator_state="unclosed"))
        self.assertEqual(result.disposition, "not_evaluable")
        with self.assertRaises(D09ProjectionError):
            build_d09_r2_handoff(typed, result)

    def test_no_handoff_on_gate_boundary_or_plain_not_evaluable(self) -> None:
        gate = _evaluate(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed"))
        self.assertIsNone(build_d09_r2_handoff(gate[0], gate[1]))
        boundary = _evaluate(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertIsNone(build_d09_r2_handoff(boundary[0], boundary[1]))
        not_evaluable = _evaluate(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),))
        self.assertIsNone(build_d09_r2_handoff(not_evaluable[0],
                                               not_evaluable[1]))

    def test_handoff_replay_stable_across_run_snapshot_swap(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        first = build_d09_r2_handoff(typed, result)
        second = build_d09_r2_handoff(typed, result)
        self.assertEqual(first, second)
        swapped = replace(typed, run_ref="SYN-RUN-OTHER",
                          snapshot_ref="SYN-SNAP-OTHER")
        swapped_result = evaluate(swapped)
        swapped_handoff = build_d09_r2_handoff(swapped, swapped_result)
        assert first is not None and swapped_handoff is not None
        self.assertEqual(first.handoff_id, swapped_handoff.handoff_id)
        self.assertEqual(first.idempotency_key, swapped_handoff.idempotency_key)
        self.assertEqual(first.current_evaluation_content_ref,
                         swapped_handoff.current_evaluation_content_ref)
        self.assertEqual(first.public_d09_risk_identity,
                         swapped_handoff.public_d09_risk_identity)
        self.assertEqual(swapped_handoff.run_snapshot_audit_refs,
                         ("SYN-RUN-OTHER", "SYN-SNAP-OTHER"))

    def test_validation_rejects_closure_and_identity_break(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        closed = replace(handoff, action="propose_close")
        validation = validate_d09_r2_handoff(closed, typed, result)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("action" in reason for reason in validation["reasons"]))
        broken = replace(handoff,
                         current_evaluation_content_ref="0" * 64)
        validation = validate_d09_r2_handoff(broken, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evaluation_content_identity_stale",
                      validation["reasons"])
        non_create = replace(handoff, action="continue")
        validation = validate_d09_r2_handoff(non_create, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("non_create_without_prior_ref", validation["reasons"])

    def test_evaluation_content_identity_uses_frozen_algorithm_version(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        identity = d09_evaluation_content_identity(typed)
        # independent re-derivation with the frozen contract literal
        window = typed.analysis_windows[-1]
        definition = typed.pattern_definition
        window_identity = d09_content_hash({
            "analysis_window_stable_id": window.analysis_window_stable_id,
            "computed_window_start": window.computed_window_start,
            "computed_window_end": window.computed_window_end,
            "cutoff_id": window.cutoff_id,
            "scope_binding_stable_id": window.scope_binding_stable_id,
        })
        expected = d09_content_hash({
            "unit_stable_core": d09_unit_stable_core(typed),
            "window_instance_identity": window_identity,
            "source_revision_set": sorted(typed.source_revision_set),
            "source_content_hashes": sorted(typed.source_content_hashes),
            "mode_contract_version": typed.mode_contract_version,
            "pattern_definition_content_hash": (
                definition.pattern_definition_content_hash),
            "window_definition_content_hash": (
                window.window_contract_content_hash),
            "stratum_contract_content_hash": (
                typed.stratum.stratum_contract_content_hash),
            "legal_definition_matrix_content_hash": (
                definition.legal_definition_matrix_content_hash),
            "numeric_execution_policy_content_hash": (
                definition.numeric_execution_policy_content_hash),
            "resolved_authority": {
                "minimum_member_subject_count": (
                    typed.resolved_authority_decision.minimum_member_subject_count),
                "gap_positive_minimum_opportunity_count": (
                    typed.resolved_authority_decision
                    .gap_positive_minimum_opportunity_count),
                "trend_positive_minimum_subject_count": (
                    typed.resolved_authority_decision
                    .trend_positive_minimum_subject_count),
                "authority_validity_state": (
                    typed.resolved_authority_decision.authority_validity_state),
                "authority_ref": typed.resolved_authority_decision.authority_ref,
                "authority_locator_ref": (
                    typed.resolved_authority_decision.authority_locator_ref),
                "mode_contract_version": (
                    typed.resolved_authority_decision.mode_contract_version),
                "authority_content_hash": (
                    typed.resolved_authority_decision.authority_content_hash),
            },
            "method_comparability": {
                "method_validity_state": (
                    typed.method_comparability_decision.method_validity_state),
                "statistical_signal_role": (
                    typed.method_comparability_decision.statistical_signal_role),
                "member_expansion_state": (
                    typed.method_comparability_decision.member_expansion_state),
                "window_rule_version_refs": list(
                    typed.method_comparability_decision.window_rule_version_refs),
                "stratum_method_version_refs": list(
                    typed.method_comparability_decision
                    .stratum_method_version_refs),
            },
            "center_query_policy": {
                "policy_id": typed.center_query_policy.policy_id,
                "mode_contract_version": (
                    typed.center_query_policy.mode_contract_version),
                "max_query_member_fanout": (
                    typed.center_query_policy.max_query_member_fanout),
                "member_order_policy": (
                    typed.center_query_policy.member_order_policy),
                "redundancy_rule_ref": (
                    typed.center_query_policy.redundancy_rule_ref),
                "allowed_action_kinds": sorted(
                    typed.center_query_policy.allowed_action_kinds),
                "pd_wording_rule_ref": (
                    typed.center_query_policy.pd_wording_rule_ref),
                "content_hash": typed.center_query_policy.content_hash,
                "effective_interval": (
                    typed.center_query_policy.effective_interval),
            },
            "query_redundancy_decision": {
                "decision": typed.query_redundancy_decision.decision,
                "max_query_member_fanout": (
                    typed.query_redundancy_decision.max_query_member_fanout),
                "unit_member_set_hash": (
                    typed.query_redundancy_decision.unit_member_set_hash),
                "covered_member_refs": sorted(
                    typed.query_redundancy_decision.covered_member_refs),
                "uncovered_member_refs": sorted(
                    typed.query_redundancy_decision.uncovered_member_refs),
                "member_query_refs": sorted(
                    typed.query_redundancy_decision.member_query_refs),
                "coverage_proof_hash": (
                    typed.query_redundancy_decision.coverage_proof_hash),
            },
            "algorithm_version": "d09_v1",
        })
        self.assertEqual(identity, expected)
        self.assertNotIn("d09_unit_v1", identity)

    def test_identity_functions_exclude_opaque_ids(self) -> None:
        typed, result = _evaluate(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        identity_a = d09_evaluation_content_identity(typed)
        identity_b = d09_evaluation_content_identity(replace(
            typed, run_ref="SYN-RUN-X", snapshot_ref="SYN-SNAP-X"))
        self.assertEqual(identity_a, identity_b)
        public_a = d09_public_risk_identity(typed)
        public_b = d09_public_risk_identity(replace(
            typed, run_ref="SYN-RUN-X", snapshot_ref="SYN-SNAP-X"))
        self.assertEqual(public_a, public_b)


# ---------------------------------------------------------------------------
# Broad 179-case projection invariants (test-only adapter)
# ---------------------------------------------------------------------------


class TestBroadCatalogProjectionInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _, _, _ = load_artifacts()
        cls.bundles: Dict[str, Any] = {}
        for case in cls.catalog["cases"]:
            typed, result = run_case(case)
            cls.bundles[case["case_id"]] = (typed, result,
                                            project_d09_run(typed, result))

    def test_gate_runs_emit_no_projection_payload(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.unit_count:
                continue
            self.assertIsNone(bundle.risk_marker, cid)
            self.assertIsNone(bundle.query_draft, cid)
            self.assertIsNone(bundle.r2_handoff, cid)
            self.assertEqual(bundle.hotspots, (), cid)
            self.assertEqual(bundle.deep_links, (), cid)
            self.assertFalse(bundle.audience.audience_payload_present, cid)
            self.assertFalse(bundle.audience.journey_marker_present, cid)

    def test_not_evaluable_runs_emit_no_medical_payload(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition != "not_evaluable":
                continue
            self.assertIsNone(bundle.risk_marker, cid)
            self.assertIsNone(bundle.query_draft, cid)
            self.assertEqual(bundle.hotspots, (), cid)
            self.assertEqual(bundle.deep_links, (), cid)
            self.assertFalse(bundle.audience.journey_marker_present, cid)
            self.assertFalse(bundle.audience.audience_payload_present, cid)
            self.assertEqual(bundle.counts.disposition_zh, "暂无法评价（附原因）",
                             cid)
            if result.downstream_handoff:
                self.assertIsNotNone(bundle.r2_handoff, cid)
                assert bundle.r2_handoff is not None
                self.assertEqual(bundle.r2_handoff.action, "continue", cid)
                self.assertTrue(bundle.r2_handoff.no_auto_close_reasons, cid)
                validation = validate_d09_r2_handoff(
                    bundle.r2_handoff, typed, result)
                self.assertTrue(validation["valid"],
                                f"{cid}: {validation['reasons']}")
            else:
                self.assertIsNone(bundle.r2_handoff, cid)

    def test_positives_have_marker_hotspots_links_and_handoff(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition != "positive":
                continue
            self.assertIsNotNone(bundle.risk_marker, cid)
            self.assertTrue(bundle.hotspots, cid)
            self.assertTrue(bundle.deep_links, cid)
            assert bundle.r2_handoff is not None
            self.assertEqual(bundle.r2_handoff.action, "create", cid)
            validation = validate_d09_r2_handoff(bundle.r2_handoff,
                                                 typed, result)
            self.assertTrue(validation["valid"], f"{cid}: {validation['reasons']}")
            marker = bundle.risk_marker
            assert marker is not None
            self.assertEqual(marker.risk_owner, "D09", cid)
            self.assertEqual(marker.public_risk_identity["domain_id"],
                             "D09_center_pattern", cid)

    def test_query_draft_presence_matches_evaluator(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.query_count == 1:
                self.assertIsNotNone(bundle.query_draft, cid)
                assert bundle.query_draft is not None
                validation = validate_query_draft(bundle.query_draft,
                                                  typed, result)
                self.assertTrue(validation["valid"],
                                f"{cid}: {validation['reasons']}")
            else:
                self.assertIsNone(bundle.query_draft, cid)

    def test_query_sentences_free_of_engineering_ids(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            draft = bundle.query_draft
            if draft is None:
                continue
            joined = (draft.basis_sentence + draft.finding_sentence
                      + draft.action_sentence)
            definition = typed.pattern_definition
            # engineering id classes never enter the prose
            for ref in (definition.pattern_definition_id,
                        definition.positive_rule_ref,
                        definition.center_query_policy_id,
                        typed.mode_contract_version):
                self.assertNotIn(ref, joined, cid)
            for window in typed.analysis_windows:
                self.assertNotIn(window.analysis_window_stable_id, joined, cid)
                self.assertNotIn(window.window_instance_id, joined, cid)
            for member in (typed.subject_risk_members + typed.gap_members
                           + typed.change_ledger_members):
                self.assertNotIn(member.member_id, joined, cid)
            for revision in typed.source_revision_set:
                self.assertNotIn(revision, joined, cid)
            # finite natural record list is retained
            self.assertIn("涉及记录", draft.finding_sentence, cid)
            self.assertIn("受试者", draft.finding_sentence, cid)
            self.assertIn("本中心", draft.finding_sentence, cid)
            # structured trace fields carry the refs
            self.assertEqual(draft.basis_refs[0],
                             definition.pattern_definition_id, cid)
            self.assertEqual(draft.basis_refs[1],
                             definition.positive_rule_ref, cid)
            self.assertEqual(draft.basis_refs[3],
                             typed.mode_contract_version, cid)
            self.assertEqual(draft.source_revision_refs,
                             tuple(typed.source_revision_set), cid)

    def test_handoff_actions_stay_within_d09_initiated_set(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if bundle.r2_handoff is None:
                continue
            self.assertIn(bundle.r2_handoff.action,
                          ("create", "continue", "supersede"), cid)
            validation = validate_d09_r2_handoff(bundle.r2_handoff,
                                                 typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")

    def test_pd_wording_matches_exact_pd_facts_across_catalog(self) -> None:
        pd_drafts = 0
        non_pd_drafts = 0
        for cid, (typed, result, bundle) in self.bundles.items():
            draft = bundle.query_draft
            if draft is None:
                continue
            draft_has_pd_fact = any(
                m.member_id in draft.member_refs
                and m.gap_kind == "pd_unreported"
                for m in typed.gap_members)
            if "请核实是否为 PD" in draft.action_sentence:
                pd_drafts += 1
                self.assertTrue(draft_has_pd_fact,
                                f"{cid}: PD wording without a PD member fact")
            else:
                non_pd_drafts += 1
                self.assertFalse(draft_has_pd_fact,
                                 f"{cid}: PD member without PD wording")
                self.assertNotIn("请核实是否为 PD",
                                 draft.action_sentence, cid)
            validation = validate_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")
        # frozen distribution: 63 non-PD drafts + 2 exact PD drafts
        self.assertEqual(non_pd_drafts, 63)
        self.assertEqual(pd_drafts, 2)
        self.assertEqual(non_pd_drafts + pd_drafts, 65)

    def test_boundaries_never_become_risk_or_query(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition != "boundary":
                continue
            self.assertIsNone(bundle.risk_marker, cid)
            self.assertIsNone(bundle.query_draft, cid)
            self.assertTrue(bundle.deep_links, cid)

    def test_not_applicable_units_emit_no_medical_payload(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition != "not_applicable":
                continue
            self.assertIsNone(bundle.risk_marker, cid)
            self.assertIsNone(bundle.query_draft, cid)
            self.assertIsNone(bundle.r2_handoff, cid)
            self.assertEqual(bundle.hotspots, (), cid)
            self.assertEqual(bundle.deep_links, (), cid)

    def test_hidden_members_never_reach_any_payload(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            hidden = set(result.hidden_member_refs)
            if not hidden:
                continue
            self.assertFalse(hidden & set(bundle.audience.projectable_member_refs),
                             cid)
            for hotspot in bundle.hotspots:
                refs = set(hotspot.member_risk_refs) | set(hotspot.gap_member_refs)
                self.assertFalse(hidden & refs, cid)
            for link in bundle.deep_links:
                self.assertNotIn(link.member_ref, hidden, cid)
            if bundle.query_draft is not None:
                self.assertFalse(hidden & set(bundle.query_draft.member_refs), cid)
                joined = "".join((bundle.query_draft.basis_sentence,
                                  bundle.query_draft.finding_sentence,
                                  bundle.query_draft.action_sentence))
                for ref in hidden:
                    self.assertNotIn(ref, joined, cid)
            if bundle.risk_marker is not None:
                self.assertFalse(hidden & set(bundle.risk_marker.member_refs),
                                 cid)
                for locator in bundle.risk_marker.source_locator_ids:
                    self.assertNotIn(locator, hidden, cid)
            joined_counts = "".join((
                bundle.counts.individual_risk_zh,
                bundle.counts.affected_subjects_zh,
                bundle.counts.event_count_zh,
                bundle.counts.center_pattern_count_zh))
            for ref in hidden:
                self.assertNotIn(ref, joined_counts, cid)

    def test_rate_never_shown_when_not_permitted(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            state = typed.visibility_decision.rate_projection_state
            if state != "permitted":
                self.assertIsNone(bundle.counts.rate_zh, cid)
            elif bundle.counts.hidden_member_count == 0:
                if result.denominator_value > 0:
                    self.assertIsNotNone(bundle.counts.rate_zh, cid)

    def test_visible_counts_equal_raw_when_nothing_hidden(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if bundle.counts.hidden_member_count:
                continue
            if result.unit_count == 0:
                # gate runs zero every raw count at the evaluation plane
                self.assertEqual(bundle.counts.visible_individual_risk_count,
                                 0, cid)
                continue
            self.assertEqual(bundle.counts.visible_individual_risk_count,
                             bundle.counts.individual_risk_count, cid)
            self.assertEqual(bundle.counts.visible_affected_subject_count,
                             bundle.counts.affected_subject_count, cid)
            self.assertEqual(bundle.counts.visible_event_count,
                             bundle.counts.event_count, cid)
            self.assertEqual(bundle.counts.visible_gap_opportunity_count,
                             bundle.counts.gap_opportunity_count, cid)

    def test_counts_never_mixed_across_catalog(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            counts = bundle.counts
            self.assertEqual(counts.individual_risk_count,
                             counts.visible_individual_risk_count, cid)
            self.assertEqual(counts.affected_subject_count,
                             counts.visible_affected_subject_count, cid)
            self.assertEqual(counts.event_count,
                             counts.visible_event_count, cid)
            self.assertEqual(counts.gap_opportunity_count,
                             counts.visible_gap_opportunity_count, cid)
            self.assertEqual(counts.query_count,
                             int(bundle.query_draft is not None), cid)
            self.assertEqual(counts.evaluation_window_instance_ref,
                             typed.analysis_windows[-1].window_instance_id
                             if typed.analysis_windows else "", cid)
            # boundary clue is never a Query count and a Query is never a
            # risk count
            if result.disposition == "boundary":
                self.assertEqual(counts.clue_count, 1, cid)
                self.assertEqual(counts.query_count, 0, cid)

    def test_hotspot_subjects_within_numerator_or_priority_rules(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition == "positive":
                # every affected subject of a positive unit is projected
                self.assertGreaterEqual(len(bundle.hotspots), 1, cid)
                hotspot_subjects = {h.subject_ref for h in bundle.hotspots}
                self.assertEqual(len(hotspot_subjects), len(bundle.hotspots),
                                 cid)
            for hotspot in bundle.hotspots:
                self.assertEqual(hotspot.site_ref, typed.site_stable_id, cid)
                self.assertTrue(hotspot.subject_ref, cid)
                self.assertTrue(hotspot.priority_rule_ref, cid)
                self.assertTrue(hotspot.projectability_decision_ref, cid)

    def test_deep_link_unavailable_state_never_fabricates(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            for link in bundle.deep_links:
                if link.target_state == "unavailable":
                    self.assertIsNone(link.source_locator, cid)
                    self.assertEqual(link.unavailable_message,
                                     "来源暂无法定位", cid)
                else:
                    self.assertIsNotNone(link.source_locator, cid)
                    self.assertIsNone(link.unavailable_message, cid)
                    self.assertEqual(link.locator_resolution_state,
                                     "locatable", cid)

    def test_marker_and_handoff_replay_stable(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            if result.disposition != "positive":
                continue
            marker = build_d09_risk_marker(typed, result)
            handoff = build_d09_r2_handoff(typed, result)
            self.assertEqual(marker, bundle.risk_marker, cid)
            self.assertEqual(handoff, bundle.r2_handoff, cid)
            assert marker is not None and handoff is not None
            self.assertEqual(marker.content_hash, marker.content_hash, cid)
            self.assertEqual(handoff.idempotency_key, handoff.handoff_id, cid)

    def test_no_cross_site_ranking_or_comparison_in_payloads(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            # every payload is scoped to the single evaluated site; no
            # ordering field carries a cross-site rank
            for hotspot in bundle.hotspots:
                self.assertEqual(hotspot.site_ref, typed.site_stable_id, cid)
            for link in bundle.deep_links:
                self.assertEqual(link.site_ref, typed.site_stable_id, cid)
                self.assertEqual(link.project_ref, typed.project_ref, cid)
                self.assertTrue(link.subject_ref, cid)
            self.assertFalse(hasattr(bundle.counts, "rank"), cid)
            self.assertFalse(hasattr(bundle.counts, "comparison"), cid)

    def test_all_user_facing_strings_are_clean_chinese(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            texts = [
                bundle.counts.individual_risk_zh,
                bundle.counts.affected_subjects_zh,
                bundle.counts.event_count_zh,
                bundle.counts.center_pattern_count_zh,
                bundle.counts.coverage_zh,
                bundle.counts.coverage_state_zh,
                bundle.counts.disposition_zh,
                bundle.counts.denominator_zh or "",
                bundle.counts.rate_zh or "",
                bundle.audience.disposition_zh,
            ]
            if bundle.counts.lifecycle_zh:
                texts.append(bundle.counts.lifecycle_zh)
            if bundle.query_draft is not None:
                texts.extend((bundle.query_draft.basis_sentence,
                              bundle.query_draft.finding_sentence,
                              bundle.query_draft.action_sentence))
            for link in bundle.deep_links:
                if link.unavailable_message:
                    texts.append(link.unavailable_message)
            joined = "".join(texts)
            for token in ("正式事实", "候选信号", "已记录事项", "只读",
                          "通用风险点"):
                self.assertNotIn(token, joined, cid)
            for token in ("positive", "negative", "boundary", "not_evaluable",
                          "permitted", "suppressed", "qualified", "gate",
                          "ledger", "handoff", "hotspot", "deep_link"):
                self.assertNotIn(token, joined, cid)


if __name__ == "__main__":
    unittest.main()
