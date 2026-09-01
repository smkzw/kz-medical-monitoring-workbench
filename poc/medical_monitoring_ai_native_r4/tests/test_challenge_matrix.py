"""R4 D01 AE/MH adversarial challenge-matrix tests (worker_03).

Drives the synthetic :func:`build_challenge_matrix` fixtures through the
real D01 engine and the real R2 lifecycle, proving every frozen-matrix §6
challenge category behaves as specified:

1. five exclusive L1 dispositions (one per unit, never multi-outcome);
2. hidden cross-role case (surface-normal, exposes under-reporting);
3. false-positive: NCS-only, confirmed alternative diagnosis,
   protocol-excluded concept;
4. false-negative: partial-date seriousness clue is not missed;
5. coverage: missing required role -> not_evaluable (fail-closed);
6. anti-invariant: Query export != send (no 'sent' flag), center pattern
   does not duplicate subject risks;
7. count/join: candidate, source-record, risk, query counts never
   contaminate each other;
8. L2 object-type counting through :class:`UnitEvaluation.count_l2`.

All data is synthetic and offline.
"""

from __future__ import annotations

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

from mm_r4.contracts import (  # noqa: E402
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    L2ObjectType,
    QueryDraftRef,
)
from mm_r4.fixtures import (  # noqa: E402
    PROJECT_ID,
    build_challenge_matrix,
    make_acceptance_service,
    make_baseline_snapshot,
    make_lifecycle,
    make_record,
    make_record_set,
    make_unit,
    evaluate,
)
from mm_r4.lifecycle import R4LifecycleAdapter  # noqa: E402


# ===========================================================================
# 1. Five exclusive L1 dispositions
# ===========================================================================

class TestFiveL1Dispositions:

    def setup_method(self):
        self.matrix = build_challenge_matrix()

    def test_positive_case(self):
        c = self.matrix.by_name("positive_suspected_under_report")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert len(r.risk_candidate_refs) >= 1
        assert len(r.query_refs) >= 1

    def test_negative_case(self):
        c = self.matrix.by_name("negative_reported_match")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert len(r.risk_candidate_refs) == 0

    def test_boundary_case(self):
        c = self.matrix.by_name("boundary_partial_date")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.BOUNDARY
        assert r.boundary_reason

    def test_not_applicable_case(self):
        c = self.matrix.by_name("not_applicable_protocol")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NOT_APPLICABLE

    def test_not_evaluable_case(self):
        c = self.matrix.by_name("coverage_missing_temporal_anchor")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "temporal_anchor" in r.not_evaluable_reason

    @pytest.mark.parametrize("name", [
        "positive_suspected_under_report",
        "negative_reported_match",
        "boundary_partial_date",
        "not_applicable_protocol",
        "coverage_missing_temporal_anchor",
    ])
    def test_each_unit_has_exactly_one_disposition(self, name):
        c = self.matrix.by_name(name)
        r = c.evaluate_case()
        # The disposition is always exactly one of the five.
        assert r.l1_disposition in L1Disposition.ALL
        # No multi-outcome: exactly one disposition field is set.
        count = sum(1 for d in L1Disposition.ALL if r.l1_disposition == d)
        assert count == 1


# ===========================================================================
# 2. Hidden cross-role case
# ===========================================================================

class TestHiddenCrossRole:

    def test_cm_indication_exposes_under_report(self):
        c = build_challenge_matrix().by_name("hidden_cross_role_cm_indication")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert len(r.risk_candidate_refs) >= 1
        # The clue comes from the CM indication role, not a reported AE.
        cand_roles = {
            ev.evidence_role for ev in r.evidence
            if ev.polarity == L1bEvidencePolarity.SUPPORTING}
        assert "cm_indication" in cand_roles


# ===========================================================================
# 3. False-positive challenges
# ===========================================================================

class TestFalsePositiveChallenges:

    def setup_method(self):
        self.matrix = build_challenge_matrix()

    def test_ncs_only_does_not_create_clue(self):
        c = self.matrix.by_name("fp_ncs_only_no_action")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert len(r.risk_candidate_refs) == 0

    def test_confirmed_alternative_diagnosis_excludes(self):
        c = self.matrix.by_name("fp_confirmed_alternative_diagnosis")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NEGATIVE
        # Counterevidence polarity must be present.
        assert any(
            ev.polarity == L1bEvidencePolarity.COUNTEREVIDENCE
            for ev in r.evidence)

    def test_protocol_excluded_concept_not_a_clue(self):
        c = self.matrix.by_name("fp_protocol_excluded_concept")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert len(r.risk_candidate_refs) == 0


# ===========================================================================
# 4. False-negative challenges
# ===========================================================================

class TestFalseNegativeChallenges:

    def test_partial_date_seriousness_not_missed(self):
        c = build_challenge_matrix().by_name("fn_partial_date_seriousness")
        r = c.evaluate_case()
        # The seriousness clue ensures the event is surfaced as a positive
        # clue, not silently dropped (false negative avoided).
        assert r.l1_disposition == L1Disposition.POSITIVE
        assert len(r.risk_candidate_refs) >= 1


# ===========================================================================
# 5. Coverage challenges (fail-closed)
# ===========================================================================

class TestCoverageChallenges:

    def test_missing_temporal_anchor_is_not_evaluable(self):
        c = build_challenge_matrix().by_name("coverage_missing_temporal_anchor")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_empty_record_collection_is_not_negative(self):
        """No records at all is NOT negative -- it is not_evaluable."""
        rs = make_record_set([])
        r = evaluate([], record_set=rs)
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE


# ===========================================================================
# 6. Anti-invariant: Query export != send
# ===========================================================================

class TestQueryExportNotSend:

    def test_query_draft_has_no_sent_attribute(self):
        c = build_challenge_matrix().by_name("anti_query_not_send")
        r = c.evaluate_case()
        assert r.query_refs
        for q in r.query_refs:
            assert isinstance(q, QueryDraftRef)
            assert not hasattr(q, "sent")
            assert not hasattr(q, "status")
            assert not hasattr(q, "is_sent")
            assert q.basis and q.finding and q.action

    def test_query_links_source_unit_and_candidate(self):
        c = build_challenge_matrix().by_name("anti_query_not_send")
        r = c.evaluate_case()
        q = r.query_refs[0]
        assert q.unit_id == r.unit_id
        assert q.linked_candidate_id
        assert q.source_locator_ids


# ===========================================================================
# 7. Count/join separation
# ===========================================================================

class TestCountJoinSeparation:

    def test_counts_never_contaminate(self):
        c = build_challenge_matrix().by_name("count_join_separation")
        r = c.evaluate_case()
        assert r.l1_disposition == L1Disposition.POSITIVE
        # 2 reported AE source records, 1 candidate, >=1 query.
        assert len(r.source_record_refs) == 2
        assert len(r.risk_candidate_refs) == 1
        assert len(r.query_refs) >= 1
        # Candidate count != source record count != query count.
        assert len(r.risk_candidate_refs) != len(r.source_record_refs)

    def test_unit_evaluation_count_l2_separates_types(self):
        c = build_challenge_matrix().by_name("count_join_separation")
        r = c.evaluate_case()
        ue = r.to_unit_evaluation(
            l0_status=L0CoverageStatus.COVERED,
            provenance_snapshot_id="snap-N",
            provenance_rule_lineage="d01-rule-v1")
        assert ue.count_l2(L2ObjectType.SOURCE_RECORD) == 2
        assert ue.count_l2(L2ObjectType.RISK_CANDIDATE) == 1
        assert ue.count_l2(L2ObjectType.QUERY_DRAFT) >= 1
        assert ue.count_l2(L2ObjectType.RISK_INSTANCE) == 0

    def test_positive_unit_join_invariant_enforced(self):
        """A positive UnitEvaluation must carry >=1 candidate (matrix §3.4)."""
        c = build_challenge_matrix().by_name("positive_suspected_under_report")
        r = c.evaluate_case()
        ue = r.to_unit_evaluation(
            l0_status=L0CoverageStatus.COVERED,
            provenance_snapshot_id="snap-N",
            provenance_rule_lineage="d01-rule-v1")
        assert ue.l1_disposition == L1Disposition.POSITIVE
        assert ue.count_l2(L2ObjectType.RISK_CANDIDATE) >= 1


    def test_query_count_not_added_to_risk_count(self):
        """Query drafts never inflate the risk-instance count."""
        c = build_challenge_matrix().by_name("anti_query_not_send")
        r = c.evaluate_case()
        ue = r.to_unit_evaluation(
            l0_status=L0CoverageStatus.COVERED,
            provenance_snapshot_id="snap-N",
            provenance_rule_lineage="d01-rule-v1")
        assert ue.count_l2(L2ObjectType.QUERY_DRAFT) >= 1
        assert ue.count_l2(L2ObjectType.RISK_INSTANCE) == 0


# ===========================================================================
# 8. Center pattern anti-invariant (matrix §3.4; bounded, not aggregation)
# ===========================================================================

class TestCenterPatternNotRisk:

    def test_center_aggregate_does_not_clone_subject_risk(self):
        """A center-level pattern observation must not create per-subject
        risk instances.  R4 D01 produces subject-scoped candidates only.

        Bounded anti-invariant (Codex finding 8): this test proves that
        two subject-scoped candidates remain disjoint and that no center
        aggregator exists in R4 that would clone or duplicate subject
        risks.  It is NOT a test of an implemented center aggregator --
        center aggregation is projection data only and is out of scope
        for this slice.
        """
        # Two subjects each with a positive clue.
        records_s1 = [
            make_record("reported_ae", "MedDRA:10019242", "ae-cp-s1",
                        event_date_raw="2026-03-01", subject_ref="S001"),
            make_record("symptom_event", "MedDRA:9999001", "sym-cp-s1",
                        event_date_raw="2026-03-15", subject_ref="S001",
                        intensity="moderate"),
        ]
        records_s2 = [
            make_record("reported_ae", "MedDRA:10019242", "ae-cp-s2",
                        event_date_raw="2026-03-01", subject_ref="S002",
                        site_ref="SITE02"),
            make_record("symptom_event", "MedDRA:9999001", "sym-cp-s2",
                        event_date_raw="2026-03-15", subject_ref="S002",
                        site_ref="SITE02", intensity="moderate"),
        ]
        r1 = evaluate(
            records_s1,
            record_set=make_record_set(records_s1, subject_ref="S001"),
            unit=make_unit(scope_key="S001"))
        r2 = evaluate(
            records_s2,
            record_set=make_record_set(
                records_s2, subject_ref="S002", site_ref="SITE02"),
            unit=make_unit(scope_key="S002"))
        # Each subject has its own candidate; no cross-subject cloning.
        cands_s1 = {c.candidate_id for c in r1.r2_candidates}
        cands_s2 = {c.candidate_id for c in r2.r2_candidates}
        assert cands_s1 and cands_s2
        assert cands_s1.isdisjoint(cands_s2)


# ===========================================================================
# 9. Lifecycle integration: positive case establishes exactly one risk
# ===========================================================================

class TestLifecycleIntegration:

    def test_positive_case_establishes_one_risk_per_candidate(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id="snap-N", revision_id="rev-N")
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy")
        c = build_challenge_matrix().by_name("positive_suspected_under_report")
        # Re-evaluate with the lifecycle's snapshot id.
        r = c.evaluate_case(snapshot_id="snap-N")
        outcome = adapter.promote_unit_result(r)
        assert outcome.established_any
        assert len(outcome.established_risk_ids) == len(r.r2_candidates)
        assert lc.verify_chain(PROJECT_ID)

    def test_negative_case_establishes_no_risk(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id="snap-N", revision_id="rev-N")
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy")
        c = build_challenge_matrix().by_name("negative_reported_match")
        r = c.evaluate_case(snapshot_id="snap-N")
        outcome = adapter.promote_unit_result(r)
        assert not outcome.established_any
        assert lc.instances_for_project(PROJECT_ID) == []
