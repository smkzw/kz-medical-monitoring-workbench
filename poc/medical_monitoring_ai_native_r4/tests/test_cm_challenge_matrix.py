"""R4-D02 CM adversarial challenge-matrix + N-to-N+1 lifecycle tests (worker_04).

Drives the synthetic :func:`build_cm_challenge_matrix` fixtures (all 30
frozen §12 cases) through the real D02 engine (``mm_r4.cm``), the real
projection (``mm_r4.cm_projection``) and the real R2 lifecycle, proving
every frozen challenge case behaves as specified:

* all 30 numbered cases produce the expected per-unit L1 dispositions,
  candidate/Query/cross-domain counts and audience labels;
* identity is stable across locator/snapshot revision (case 25) and
  differs across drug/rule (case 14);
* compound episodes show simultaneous positive + not_evaluable with the
  L2 source record still counted once (cases 4, 22, 28);
* rule-target granularity (J07 super-type vs live vaccine) is enforced
  (cases 5, 23);
* Query drafts are three-part, carry minimum source locators and never
  carry a 'sent' flag (case 18);
* cross-domain evidence refs are canonical, exclude snapshot/revision
  from the content hash, and carry no lifecycle state (case 27);
* the N-to-N+1 lifecycle replay proves immutable historical completion,
  stable event identity, versioned lineage supersede (not
  resolved_by_data), identity_ambiguous rejection of auto-close, no
  duplicate D01/D02 candidates/risks/Queries, and deterministic replay.

All data is synthetic and offline.  No real project, provider, dictionary,
or product service; port 8911 is never touched.
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

from mm_r4.cm_fixtures import (  # noqa: E402
    DOMAIN_ID,
    PROJECT_ID,
    build_cm_challenge_matrix,
    evaluate,
    make_acceptance_service,
    make_baseline_snapshot,
    make_binding,
    make_closed_cm_ledger,
    make_episode,
    make_lifecycle,
    make_rule,
    make_strategy,
    make_strategy_v2,
    make_subsequent_snapshot,
    run_n_to_n1_replay,
)
from mm_r4.cm import (  # noqa: E402
    IngredientBinding,
    TreatmentInterpretationEvidence,
    TARGET_KIND_INGREDIENT,
)
from mm_r4.aemh import (  # noqa: E402
    SemanticRecord,
    consume_cross_domain_evidence_refs,
)
from mm_r4.cm_projection import (  # noqa: E402
    bidirectional_join,
    project_cm_journey_event,
    project_cm_risk_markers,
    ANCHOR_KIND_INTERVAL,
    ANCHOR_KIND_OVERLAP,
)
from mm_r4.contracts import (  # noqa: E402
    CoverageValidationError,
    CrossDomainEvidenceRef,
    L1Disposition,
    L2ObjectType,
    QueryDraftRef,
    RiskDomainUnitResult,
    SourceLocator,
    UnitEvaluation,
    cross_domain_evidence_content_hash,
)
from mm_r4.coverage import is_domain_complete  # noqa: E402
from mm_r4.lifecycle import R4LifecycleAdapter  # noqa: E402


# ===========================================================================
# Matrix integrity
# ===========================================================================

class TestMatrixIntegrity:
    """The matrix has exactly 30 cases numbered 1-30, all buildable."""

    def test_matrix_has_30_cases_numbered_1_to_30(self):
        m = build_cm_challenge_matrix()
        assert m.case_count == 30
        assert m.numbers == tuple(range(1, 31))

    def test_d02_public_root_exports_are_object_identical(self):
        import mm_r4
        from mm_r4 import aemh, cm, cm_projection

        assert mm_r4.MedicationEpisode is cm.MedicationEpisode
        assert (mm_r4.TreatmentInterpretationEvidence
                is cm.TreatmentInterpretationEvidence)
        assert mm_r4.evaluate_cm_slice is cm.evaluate_cm_slice
        assert (mm_r4.consume_cross_domain_evidence_refs
                is aemh.consume_cross_domain_evidence_refs)
        assert (mm_r4.CMSubjectJourneyProjection
                is cm_projection.CMSubjectJourneyProjection)
        assert (mm_r4.project_cm_subject_journey
                is cm_projection.project_cm_subject_journey)

    def test_every_case_builds_and_evaluates(self):
        m = build_cm_challenge_matrix()
        for c in m.cases:
            exp, results = c.build()
            assert exp.count == c.expected_count(), (
                f"case {c.number} ({c.name}) expected_set size "
                f"{c.expected_count()} != expansion {exp.count}")
            assert len(results) == exp.count, (
                f"case {c.number} result count != expansion count")

    def test_case_lookup_by_number_and_name(self):
        m = build_cm_challenge_matrix()
        assert m.by_number(1).number == 1
        assert m.by_name("prohibited_ingredient_in_window").number == 1
        with pytest.raises(KeyError):
            m.by_number(99)


# ===========================================================================
# Expected-unit matching helper
# ===========================================================================

def _match_expected(case, exp_unit, expansion, results):
    """Find the result unit matching an expected-unit spec and return it.

    Matching: by risk_family/rule_item substring (against the expansion
    unit), then verify the result's L1.
    """
    strategy = case.strategy_override or make_strategy()
    matched_result = None
    for i, eu in enumerate(expansion.units):
        uid = eu.build_unit(PROJECT_ID, strategy).unit_id
        if exp_unit.matches_unit(eu):
            for r in results:
                if r.unit_id == uid:
                    matched_result = r
                    break
            break
    if exp_unit.unit_index is not None:
        # index-based: pick the nth result in expansion order
        ordered_ids = [
            eu.build_unit(PROJECT_ID, strategy).unit_id
            for eu in expansion.units]
        id_to_result = {r.unit_id: r for r in results}
        idx = exp_unit.unit_index
        if 0 <= idx < len(ordered_ids):
            matched_result = id_to_result.get(ordered_ids[idx])
    assert matched_result is not None, (
        f"case {case.number}: no unit matched expected spec "
        f"(family={exp_unit.risk_family_contains!r}, "
        f"rule_item={exp_unit.rule_item_contains!r})")
    return matched_result


def _assert_expected_unit(case, exp_unit, expansion, results):
    r = _match_expected(case, exp_unit, expansion, results)
    assert r.l1_disposition == exp_unit.expected_l1, (
        f"case {case.number} ({case.name}): unit "
        f"family~{exp_unit.risk_family_contains!r} "
        f"rule~{exp_unit.rule_item_contains!r} expected L1 "
        f"{exp_unit.expected_l1!r}, got {r.l1_disposition!r}")
    if exp_unit.expected_candidate_count is not None:
        assert len(r.r2_candidates) == exp_unit.expected_candidate_count, (
            f"case {case.number}: expected "
            f"{exp_unit.expected_candidate_count} candidates, got "
            f"{len(r.r2_candidates)}")
    if exp_unit.expected_query_count is not None:
        assert len(r.query_refs) == exp_unit.expected_query_count, (
            f"case {case.number}: expected "
            f"{exp_unit.expected_query_count} queries, got "
            f"{len(r.query_refs)}")
    if exp_unit.expected_cross_domain_ref_count is not None:
        actual = sum(
            1 for ref in r.cross_domain_evidence_refs
            if isinstance(ref, CrossDomainEvidenceRef))
        assert actual == exp_unit.expected_cross_domain_ref_count, (
            f"case {case.number}: expected "
            f"{exp_unit.expected_cross_domain_ref_count} cross-domain refs, "
            f"got {actual}")
    if exp_unit.expected_positive_subtype:
        assert r.positive_subtype == exp_unit.expected_positive_subtype, (
            f"case {case.number}: expected subtype "
            f"{exp_unit.expected_positive_subtype!r}, got "
            f"{r.positive_subtype!r}")
    if exp_unit.expected_audience_label:
        assert r.audience_label == exp_unit.expected_audience_label, (
            f"case {case.number}: expected audience "
            f"{exp_unit.expected_audience_label!r}, got "
            f"{r.audience_label!r}")


# ===========================================================================
# Cases 1-12: core L1 dispositions and inputs
# ===========================================================================

class TestCases1to12CoreDispositions:

    def _run(self, number):
        c = build_cm_challenge_matrix().by_number(number)
        exp, results = c.build()
        for eu in c.expected_units:
            _assert_expected_unit(c, eu, exp, results)
        return c, exp, results

    def test_case1_prohibited_ingredient_in_window_positive(self):
        self._run(1)

    def test_case2_different_ingredient_negative(self):
        self._run(2)

    def test_case3_unresolved_ingredient_not_evaluable(self):
        self._run(3)

    def test_case4_compound_prohibited_plus_unresolved(self):
        self._run(4)

    def test_case5_j07_supertype_not_evaluable(self):
        self._run(5)

    def test_case6_endpoint_inclusivity_boundary(self):
        self._run(6)

    def test_case7_partial_date_boundary(self):
        self._run(7)

    def test_case8_stable_treatment_conditions_met_negative(self):
        c, exp, results = self._run(8)
        # §12 item 8: "明确稳定治疗满足条件，counterevidence/negative".
        # The restricted-rule unit must be negative AND carry counterevidence
        # polarity, not merely a bare negative disposition.
        from mm_r4.contracts import L1bEvidencePolarity
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE][0]
        polarities = {ev.polarity for ev in neg.evidence}
        assert L1bEvidencePolarity.COUNTEREVIDENCE in polarities, (
            "stable-treatment conditions met must carry counterevidence "
            "polarity, not a bare negative")

    def test_case9_stable_treatment_evidence_missing_not_evaluable(self):
        c, exp, results = self._run(9)
        episode = c.build_episodes()[0]
        assert episode.treatment_role_confirmed is True
        assert episode.stable_treatment_evidence_complete is False
        rule_result = next(
            r for r in results if "稳定治疗证据不完整" in r.not_evaluable_reason)
        assert rule_result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case9_branch_a_stable_new_start_is_boundary(self):
        """§12 item 9(a): independently sourced stable/new-start
        interpretations remain a visible boundary, never a forced choice."""
        interpretation_evidence = (
            TreatmentInterpretationEvidence(
                interpretation="stable_treatment",
                evidence_locator=SourceLocator(
                    snapshot_id="snapshot-N", source_revision_id="rev-N",
                    table_semantic="recorded_cm", record_id="CM#9-history",
                    column_or_anchor="历史用药起始日期"),
                evidence_version="listing-v1",
                evidence_content_hash="1" * 64),
            TreatmentInterpretationEvidence(
                interpretation="new_start",
                evidence_locator=SourceLocator(
                    snapshot_id="snapshot-N", source_revision_id="rev-N",
                    table_semantic="recorded_cm", record_id="CM#9-dose",
                    column_or_anchor="本期剂量变更"),
                evidence_version="listing-v1",
                evidence_content_hash="2" * 64),
        )
        ep = make_episode(
            record_id="CM#9b",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientB"),)),
            treatment_role="stable_treatment",
            treatment_role_confirmed=True,
            treatment_interpretation_evidence=interpretation_evidence)
        rule = make_rule(
            rule_id="R-REST-9b", rule_type="restricted",
            target_kind=TARGET_KIND_INGREDIENT, target_value="ingredientB",
            priority="medium", clause_locator="P9b",
            allowed_conditions=("stable_treatment",),
            priority_rationale="限制成分")
        _, by_subj = evaluate((ep,), (rule,))
        results = [r for urs in by_subj.values() for r in urs]
        boundaries = [
            r for r in results
            if r.l1_disposition == L1Disposition.BOUNDARY
        ]
        assert len(boundaries) == 1
        assert "两种解释均有来源支持" in boundaries[0].boundary_reason
        assert len(boundaries[0].r2_candidates) == 1
        assert len(boundaries[0].query_refs) == 0

    def test_case10_rescue_prophylaxis_no_auto_under_report(self):
        self._run(10)

    def test_case11_treatment_indication_no_event_positive(self):
        self._run(11)

    def test_case12_missing_indication_not_evaluable(self):
        self._run(12)


# ===========================================================================
# Cases 13-21: CM/IP separation, identity, lifecycle seeds, indication
# ===========================================================================

class TestCases13to21IdentityAndIndication:

    def _run(self, number):
        c = build_cm_challenge_matrix().by_number(number)
        exp, results = c.build()
        for eu in c.expected_units:
            _assert_expected_unit(c, eu, exp, results)
        return c, exp, results

    def test_case13_cm_ip_role_conflict_not_evaluable(self):
        self._run(13)

    def test_case14_different_drug_does_not_persist_old_risk(self):
        c, exp, results = self._run(14)
        # The two drugs for the same subject produce different risk
        # identities: the positive (14a) and the negative (14b) must not
        # share a risk_identity_id.
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE]
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert pos and neg
        pos_ids = {str(cand.detail.get("risk_identity_id", ""))
                   for r in pos for cand in r.r2_candidates}
        assert len(pos_ids) == 1, "exactly one positive identity expected"
        # The negative unit carries no candidate (identity non-match).
        assert all(not r.r2_candidates for r in neg)

    def test_case15_n_to_n1_linked_negative_close_seed(self):
        self._run(15)

    def test_case16_dictionary_lineage_change_seed(self):
        self._run(16)

    def test_case17_competing_identity_ambiguous_seed(self):
        self._run(17)

    def test_case18_query_three_part_journey_join(self):
        c, exp, results = self._run(18)
        # Query is three-part with minimum source locators.
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        q = pos.query_refs[0]
        assert isinstance(q, QueryDraftRef)
        assert q.basis.startswith("依据")
        assert q.finding.startswith("发现")
        assert q.action.startswith("行动项")
        assert q.source_locator_ids, "query must carry minimum source locators"
        # §12 item 18: "PD 仅核实" -- the action requests verification, it
        # never formally submits or adjudicates a protocol deviation.
        assert "请核实" in q.action, (
            "Query action must request verification, not formal PD submission")
        for forbidden in ("报送", "判定为PD", "判定为 PD", "正式判定"):
            assert forbidden not in q.action, (
                f"Query action must not contain formal PD language "
                f"{forbidden!r}")

    def test_case19_indication_subtype_precedence(self):
        self._run(19)

    def test_case20_restricted_rescue_role_unconfirmed_not_evaluable(self):
        self._run(20)

    def test_case21_vague_indication_not_evaluable(self):
        self._run(21)


# ===========================================================================
# Cases 22-30: compound flags, granularity, identity persistence, cross-domain
# ===========================================================================

class TestCases22to30CompoundAndIdentity:

    def _run(self, number):
        c = build_cm_challenge_matrix().by_number(number)
        exp, results = c.build()
        for eu in c.expected_units:
            _assert_expected_unit(c, eu, exp, results)
        return c, exp, results

    def test_case22_all_components_unresolved(self):
        c, exp, results = self._run(22)
        # Every unresolved component enters the expected-set; domain cannot
        # be complete while not_evaluable siblings exist.
        assert exp.count == 2
        assert all(r.l1_disposition == L1Disposition.NOT_EVALUABLE
                   for r in results)
        # §12 item 22: "域不得 complete" -- a closed ledger over the
        ledger = make_closed_cm_ledger(results)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete, (
            "domain with all-unresolved-component not_evaluable units "
            "must not be complete")
        assert any("not_evaluable" in r for r in reasons)

    def test_case23_j07_supertype_rule_matchable(self):
        self._run(23)

    def test_case24_boundary_plus_role_gap_not_evaluable(self):
        c, exp, results = self._run(24)
        # not_evaluable takes priority over the endpoint boundary because
        # the restricted rescue-role coverage gap is checked first.
        episode = c.build_episodes()[0]
        assert episode.study_phase_confirmed is True
        assert episode.treatment_role_confirmed is False
        for r in results:
            assert r.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case25_identity_persistence_on_data_correction(self):
        c, exp, results = self._run(25)
        # Identity is deterministic: re-evaluating the same inputs twice
        # yields the same identity_id (deterministic replay).
        exp2, results2 = c.build()
        ids1 = {str(cand.detail.get("risk_identity_id", ""))
                for r in results for cand in r.r2_candidates}
        ids2 = {str(cand.detail.get("risk_identity_id", ""))
                for r in results2 for cand in r.r2_candidates}
        assert ids1 == ids2, "identity must be deterministic across replays"

    def test_case26_competing_identity_rejects_auto_close_seed(self):
        self._run(26)

    def test_case27_cm_indication_handoff_dedup(self):
        c, exp, results = self._run(27)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        cer = pos.cross_domain_evidence_refs[0]
        assert isinstance(cer, CrossDomainEvidenceRef)
        assert cer.evidence_role == "cm_indication"
        assert cer.producer_domain == DOMAIN_ID
        assert cer.consumer_domain == "D01_aemh"
        # content_hash is canonical and excludes snapshot/revision.
        assert cer.content_hash == cer.compute_content_hash()
        # The content_hash does not embed the snapshot id: changing only
        # the snapshot must not change the hash.
        loc2 = SourceLocator(
            snapshot_id="snap-different", source_revision_id="rev-different",
            table_semantic=cer.source_locator.table_semantic,
            record_id=cer.source_locator.record_id,
            column_or_anchor=cer.source_locator.column_or_anchor)
        ctx = dict(cer.context_payload)
        h2 = cross_domain_evidence_content_hash(
            source_locator=loc2, evidence_role=cer.evidence_role,
            claim_scope=cer.claim_scope, context_payload=ctx)
        assert h2 == cer.content_hash, (
            "content_hash must exclude snapshot/revision id")
        # No lifecycle state is carried.
        for field in ("risk_state", "candidate_id", "risk_instance_id",
                      "l1_disposition", "query_id"):
            assert not hasattr(cer, field), (
                f"CrossDomainEvidenceRef must not carry {field}")
        # §12 item 27: "claim 变化产生新 hash" -- changing the clinical
        ctx_changed = dict(ctx)
        ctx_changed["indication_concept"] = "different_concept"
        h_changed = cross_domain_evidence_content_hash(
            source_locator=cer.source_locator, evidence_role=cer.evidence_role,
            claim_scope=cer.claim_scope, context_payload=ctx_changed)
        assert h_changed != cer.content_hash, (
            "a changed clinical claim must produce a new content_hash")
        changed_ref = CrossDomainEvidenceRef(
            evidence_ref_id=f"{cer.evidence_ref_id}-changed",
            producer_domain=cer.producer_domain,
            consumer_domain=cer.consumer_domain,
            evidence_role=cer.evidence_role,
            source_locator=cer.source_locator,
            producer_unit_id=cer.producer_unit_id,
            content_hash=h_changed,
            claim_scope=cer.claim_scope,
            context_payload=tuple(ctx_changed.items()),
        )
        # §12 item 27: dedup by (table_semantic, record_id, evidence_role,
        # content_hash).  Two refs with the same tuple are dedup-able;
        # a changed claim produces a new tuple (new content_hash).
        dedup_key = (
            cer.source_locator.table_semantic,
            cer.source_locator.record_id,
            cer.evidence_role,
            cer.content_hash,
        )
        # A second ref built from the same source event + same role +
        # same claim context must produce the same dedup key.
        h_same = cross_domain_evidence_content_hash(
            source_locator=cer.source_locator, evidence_role=cer.evidence_role,
            claim_scope=cer.claim_scope, context_payload=ctx)
        dedup_key_same = (
            cer.source_locator.table_semantic,
            cer.source_locator.record_id,
            cer.evidence_role,
            h_same,
        )
        assert dedup_key == dedup_key_same, (
            "unchanged claim must produce the same dedup tuple")
        # A changed claim produces a different content_hash -> different tuple.
        dedup_key_changed = (
            cer.source_locator.table_semantic,
            cer.source_locator.record_id,
            cer.evidence_role,
            h_changed,
        )
        assert dedup_key != dedup_key_changed, (
            "changed claim must produce a different dedup tuple")
        # D01/D02 risk identity, Query and lifecycle are never written into
        # the cross-domain ref (already checked above for field absence;
        # here we verify the context_payload carries no lifecycle ids).
        ctx_keys = set(dict(cer.context_payload).keys())
        for forbidden in ("risk_identity_id", "risk_instance_id",
                          "candidate_id", "query_id", "risk_state",
                          "l1_disposition"):
            assert forbidden not in ctx_keys, (
                f"context_payload must not carry {forbidden}")

        # The actual D01 consumer adapter, not a prose-only tuple check,
        # deduplicates a directly mapped record against the D02 handoff.
        active = SemanticRecord(
            role="cm_indication",
            concept=str(ctx["indication_concept"]),
            locator=cer.source_locator,
            subject_ref=str(ctx["subject_ref"]),
            site_ref=str(ctx["site_ref"]),
            note=str(ctx["indication_text"]),
            cross_domain_content_hash=cer.content_hash,
        )
        merged = consume_cross_domain_evidence_refs(
            (active,), (cer, cer))
        assert merged == (active,)

        # With no direct mapping, repeated identical refs materialize exactly
        # one D01 SemanticRecord with the source and subject identity intact.
        materialized = consume_cross_domain_evidence_refs((), (cer, cer))
        assert len(materialized) == 1
        assert materialized[0].role == "cm_indication"
        assert materialized[0].subject_ref == str(ctx["subject_ref"])
        assert materialized[0].cross_domain_content_hash == cer.content_hash

        # A changed clinical claim has a new canonical hash and survives as a
        # distinct D01 evidence record; it is not silently collapsed.
        changed = consume_cross_domain_evidence_refs(
            (active,), (changed_ref,))
        assert len(changed) == 2
        assert {r.cross_domain_content_hash for r in changed} == {
            cer.content_hash, h_changed,
        }

        # A direct cm_indication record without its canonical claim hash is
        # not safe to deduplicate and therefore fails closed.
        unhashed_active = SemanticRecord(
            role="cm_indication",
            concept=str(ctx["indication_concept"]),
            locator=cer.source_locator,
            subject_ref=str(ctx["subject_ref"]),
            site_ref=str(ctx["site_ref"]),
        )
        with pytest.raises(CoverageValidationError):
            consume_cross_domain_evidence_refs((unhashed_active,), (cer,))

    def test_case28_compound_flags_l2_source_one(self):
        c, exp, results = self._run(28)
        # positive + not_evaluable coexist; L2 source record counted once;
        # not_evaluable sibling produces no candidate/risk.
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE]
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert pos, "expected at least one positive unit"
        assert ne, "expected not_evaluable siblings"
        # L2 source record: all units derive from the single CM#28 record,
        # so the set of (table_semantic, record_id) pairs has size 1.
        all_src = set()
        for r in results:
            for sref in r.source_record_refs:
                all_src.add((sref.locator.table_semantic,
                             sref.locator.record_id))
        assert len(all_src) == 1, (
            f"expected exactly one CM source record, got {all_src}")
        assert all_src == {("recorded_cm", "CM#28")}, (
            f"source record must be CM#28, got {all_src}")
        # not_evaluable sibling carries no candidate.
        for r in ne:
            assert not r.r2_candidates, (
                "not_evaluable sibling must not produce a candidate")
            assert not r.query_refs, (
                "not_evaluable sibling must not produce a Query")

    def test_case29_ip_exposure_no_cm_unit(self):
        c, exp, results = self._run(29)
        assert exp.count == 0
        # §12 item 29: "仅映射为 ip_exposure 的 EX/IP 行不生成 D02 CM
        # episode/unit".  An ip_exposure record is never a MedicationEpisode;
        # it only enters the engine via ip_exposure_records and produces
        # zero D02 units on its own.  The CM/IP role-conflict path
        # (not_evaluable) is proven by case 13.
        from mm_r4.cm_fixtures import make_cm_record
        ip_only = make_cm_record("ip_exposure", "ip", record_id="EX#1")
        from mm_r4.cm_fixtures import evaluate
        exp_ip, by_subj = evaluate((), (), ip_exposure_records=(ip_only,))
        assert exp_ip.count == 0
        assert all(not v for v in by_subj.values())

    def test_case30_duck_type_lifecycle_no_medical_grading(self):
        c, exp, results = self._run(30)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        # D02 results satisfy the neutral RiskDomainUnitResult protocol
        # WITHOUT carrying a MedicalGrading attribute.
        assert isinstance(pos, RiskDomainUnitResult)
        assert not hasattr(pos, "medical_grading"), (
            "D02 result must not carry MedicalGrading")
        # It still materializes a UnitEvaluation for the ledger.
        ue = pos.to_unit_evaluation(
            l0_status="covered",
            provenance_snapshot_id="snap-x",
            provenance_rule_lineage="rl")
        assert isinstance(ue, UnitEvaluation)


# ===========================================================================
# Coverage ledger: count equation and L2 separation
# ===========================================================================

class TestCoverageLedgerInvariants:

    def test_closed_ledger_count_equation_holds(self):
        c = build_cm_challenge_matrix().by_number(1)
        exp, results = c.build()
        ledger = make_closed_cm_ledger(results)
        assert ledger.is_closed
        summary = ledger.close_and_summarize()
        total = sum(summary.l1_counts.get(d, 0)
                    for d in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE,
                              L1Disposition.BOUNDARY,
                              L1Disposition.NOT_APPLICABLE,
                              L1Disposition.NOT_EVALUABLE))
        assert total == summary.expected_units

    def test_l2_counts_never_contaminate(self):
        c = build_cm_challenge_matrix().by_number(1)
        exp, results = c.build()
        ledger = make_closed_cm_ledger(results)
        summary = ledger.close_and_summarize()
        l2 = summary.l2_counts
        # candidate, source_record, risk_instance, query_draft are separate.
        assert l2[L2ObjectType.RISK_CANDIDATE] >= 1
        assert l2[L2ObjectType.QUERY_DRAFT] >= 1
        # risk_instance is 0 until lifecycle establishes.
        assert l2[L2ObjectType.RISK_INSTANCE] == 0

    def test_domain_not_complete_with_not_evaluable(self):
        c = build_cm_challenge_matrix().by_number(1)
        exp, results = c.build()
        ledger = make_closed_cm_ledger(results)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete, (
            "domain with a not_evaluable unit must not be complete")
        assert any("not_evaluable" in r for r in reasons)


# ===========================================================================
# Query export != send (anti-invariant)
# ===========================================================================

class TestQueryExportNotSend:

    def test_query_draft_has_no_sent_flag(self):
        c = build_cm_challenge_matrix().by_number(18)
        exp, results = c.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        q = pos.query_refs[0]
        # QueryDraftRef is a draft; it carries basis/finding/action and
        # source locators, but never a 'sent'/'delivered'/'status' flag.
        assert not hasattr(q, "sent")
        assert not hasattr(q, "delivered")
        assert not hasattr(q, "status")
        assert q.basis and q.finding and q.action


# ===========================================================================
# Projection: journey event + risk marker + bidirectional join
# ===========================================================================

class TestProjectionJourneyAndJoin:

    def test_journey_event_and_risk_marker_join(self):
        c = build_cm_challenge_matrix().by_number(18)
        exp, results = c.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        # Need the episode for projection context.
        episodes = list(c.build_episodes())
        episode = episodes[0]
        ev = project_cm_journey_event(pos, episode=episode)
        assert ev is not None
        assert ev.domain_track == "cm"
        assert ev.episode_id == episode.episode_id
        assert pos.unit_id in ev.unit_ids
        markers = project_cm_risk_markers(
            pos, candidates=(), episode=episode,
            risk_family_hint="prohibited_medication")
        assert len(markers) >= 1
        mk = markers[0]
        assert mk.unit_id == pos.unit_id
        assert mk.anchor_kind == ANCHOR_KIND_OVERLAP
        # Bidirectional join: marker <-> event share episode AND unit.
        join = bidirectional_join((ev,), markers)
        assert mk.marker_id in join.marker_ids_for_event.get(ev.event_id, ())
        assert ev.event_id in join.event_ids_for_marker.get(mk.marker_id, ())

    def test_episode_only_marker_does_not_join(self):
        """Adversarial: a marker sharing episode_id but NOT unit_id must
        not join to the event (frozen D02 §10 dual-key join)."""
        c = build_cm_challenge_matrix().by_number(18)
        exp, results = c.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        episodes = list(c.build_episodes())
        episode = episodes[0]
        ev = project_cm_journey_event(pos, episode=episode)
        markers = project_cm_risk_markers(
            pos, candidates=(), episode=episode,
            risk_family_hint="prohibited_medication")
        mk = markers[0]
        # Forge a marker with the same episode but a wrong unit_id.
        import dataclasses
        forged = dataclasses.replace(mk, unit_id="unit-does-not-exist")
        join = bidirectional_join((ev,), (forged,))
        assert join.event_ids_for_marker.get(forged.marker_id, ()) == (), (
            "episode-only join must be rejected")

    def test_indication_risk_anchors_cm_interval_not_event(self):
        """A medication-rationale positive (no matching AE/MH) anchors on
        the CM interval, never fabricates an event position (§10)."""
        c = build_cm_challenge_matrix().by_number(11)
        exp, results = c.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        episode = list(c.build_episodes())[0]
        markers = project_cm_risk_markers(
            pos, candidates=(), episode=episode,
            risk_family_hint="indication_check")
        assert len(markers) == 1
        mk = markers[0]
        assert mk.anchor_kind == ANCHOR_KIND_INTERVAL
        assert mk.coverage_gap is False


# ===========================================================================
# Audience labels avoid research jargon
# ===========================================================================

class TestAudienceLabels:

    def test_positive_labels_are_chinese_not_research_jargon(self):
        m = build_cm_challenge_matrix()
        for c in m.cases:
            exp, results = c.build()
            for r in results:
                if r.l1_disposition == L1Disposition.POSITIVE:
                    assert r.audience_label, (
                        f"case {c.number}: positive must have audience label")
                    for token in ("RiskCandidate", "positive", "正式事实",
                                  "候选信号", "只读"):
                        assert token not in r.audience_label, (
                            f"case {c.number}: audience label "
                            f"{r.audience_label!r} contains jargon "
                            f"{token!r}")


# ===========================================================================
# N-to-N+1 lifecycle replay
# ===========================================================================

class TestNToN1Lifecycle:

    def _setup(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id="snap-d02-N",
                               revision_id="rev-N")
        make_subsequent_snapshot(svc, snapshot_id="snap-d02-N1",
                                 revision_id="rev-N1")
        # Also register the default fixture snapshot so case.build() results
        # (whose candidates carry source_snapshot_id=SNAPSHOT_ID) can be
        # promoted through the lifecycle in the same service.
        from mm_r4.cm_fixtures import SNAPSHOT_ID, SOURCE_REV_ID
        make_baseline_snapshot(svc, snapshot_id=SNAPSHOT_ID,
                               revision_id=SOURCE_REV_ID)
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy")
        return svc, lc, adapter

    def test_linked_negative_closes_medium_risk_and_preserves_history(self):
        """Case 15: N positive (medium) -> N+1 complete linked-negative ->
        machine close; historical record preserved (immutable)."""
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(15)
        replay = run_n_to_n1_replay(
            case=case, service=svc, lifecycle=lc, adapter=adapter)
        # Established exactly one risk at N.
        assert replay.established_instance.severity == "medium"
        assert replay.established_instance.current_state == "established"
        # N+1 linked negative closed it.
        assert len(replay.reconcile.closed) == 1
        closed = replay.reconcile.closed[0]
        assert closed.risk_instance_id == replay.n_instance_id
        assert closed.risk_identity_id == replay.n_identity_id
        # Historical completion preserved: the lifecycle chain is valid and
        # the closed instance retains its original identity.
        post = lc.get(replay.n_instance_id)
        assert post.current_state == "closed"
        assert post.risk_identity_id == replay.n_identity_id
        # §12 item 15: history immutability -- the transition chain is
        # preserved on the public RiskInstance.transitions attribute.
        # The close transition uses resolved_by_data; the establish
        # transition is preserved (not overwritten by the close).
        from mm_r4.lifecycle import CLOSE_REASON_RESOLVED_BY_DATA
        transitions = post.transitions
        close_ts = [t for t in transitions if t.to_state == "closed"]
        assert len(close_ts) == 1, "exactly one close transition"
        assert close_ts[0].reason == CLOSE_REASON_RESOLVED_BY_DATA
        est_ts = [t for t in transitions if t.to_state == "established"]
        assert len(est_ts) == 1, "establish transition preserved (immutable)"
        assert est_ts[0] is not close_ts[0], (
            "establish and close are distinct immutable transitions")

    def test_identity_stable_across_snapshot_revision(self):
        """Case 25: same inputs, same lineage -> same identity_id even
        though the snapshot/revision id changes between N and N+1."""
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(25)
        replay = run_n_to_n1_replay(
            case=case, service=svc, lifecycle=lc, adapter=adapter)
        # The N identity is deterministic; re-running the replay produces
        # the same identity_id (deterministic replay).
        svc2, lc2, adapter2 = self._setup()
        replay2 = run_n_to_n1_replay(
            case=case, service=svc2, lifecycle=lc2, adapter=adapter2)
        assert replay.n_identity_id == replay2.n_identity_id, (
            "identity must be stable across snapshot/revision ids")
        assert replay.n_candidate_id == replay2.n_candidate_id

    def test_lineage_change_supersedes_not_resolved_by_data(self):
        """Case 16: dictionary/strategy lineage change at N+1 -> supersede,
        never resolved_by_data."""
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(16)
        replay = run_n_to_n1_replay(
            case=case, service=svc, lifecycle=lc, adapter=adapter,
            n1_strategy_override=make_strategy_v2(),
            force_negative_n1=False)
        assert len(replay.reconcile.superseded) == 1
        assert len(replay.reconcile.closed) == 0, (
            "lineage change must not close by data")
        post = lc.get(replay.n_instance_id)
        assert post.current_state == "superseded"
        # §12 item 16: supersede must NOT use resolved_by_data.  Verify
        # through the public RiskInstance.transitions attribute.
        from mm_r4.lifecycle import CLOSE_REASON_RESOLVED_BY_DATA
        for t in post.transitions:
            assert t.reason != CLOSE_REASON_RESOLVED_BY_DATA, (
                "supersede must not use resolved_by_data close_reason")
        assert lc.verify_chain(PROJECT_ID)

    def test_case26_identity_ambiguous_lifecycle_guard_rejects_close(self):
        """Lifecycle guard (not competing-binding detection): once a risk is
        in ``identity_ambiguous`` state, any machine close is rejected
        (matrix §3.6: ambiguity blocks auto merge/close).  Genuine
        competing-binding detection from two versioned bindings is proven
        by ``test_case26_competing_identity_bindings_detected_by_reconcile``."""
        from mm_r4.lifecycle import LifecycleAdapterError
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case26 = m.by_number(26)
        # Establish the medium risk first.
        exp_n, res_n = case26.build()
        pos = [r for r in res_n
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        outcome = adapter.promote_unit_result(pos)
        inst_id, ident_id = outcome.established_risk_ids[0]
        established = lc.get(inst_id)
        assert established.severity == "medium"
        # Directly mark identity_ambiguous (lifecycle guard test only;
        # genuine competing-binding detection is proven by the reconcile
        # test above).
        ambiguous = adapter.mark_identity_ambiguous(established)
        assert ambiguous.current_state == "identity_ambiguous"
        # A machine close on an ambiguous risk must be rejected.
        with pytest.raises(LifecycleAdapterError):
            adapter.machine_close_by_data(
                ambiguous, coverage_snapshot_id="snap-d02-N1")
        # The risk stays identity_ambiguous (not closed).
        assert lc.get(inst_id).current_state == "identity_ambiguous"

    def test_no_duplicate_d01_d02_candidates_risks_queries(self):
        """D02 produces only D02 candidates/risks/Queries; D01 objects are
        never created in D02 (no duplicate across domains)."""
        m = build_cm_challenge_matrix()
        c = m.by_number(11)  # produces a cm_indication cross-domain ref
        exp, results = c.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        # All candidates carry domain = D02_cm.
        for cand in pos.r2_candidates:
            assert cand.domain == DOMAIN_ID, (
                "D02 candidate domain must be D02_cm")
        # All queries link the D02 candidate, not a D01 object.
        for q in pos.query_refs:
            assert q.linked_candidate_id in {
                c.candidate_id for c in pos.r2_candidates}
        # The cross-domain ref is NOT a candidate/risk/query -- it carries
        # only producer/consumer domain and content hash.
        cer = pos.cross_domain_evidence_refs[0]
        assert isinstance(cer, CrossDomainEvidenceRef)
        assert cer.producer_domain == DOMAIN_ID
        assert cer.consumer_domain == "D01_aemh"
        # No D01 candidate/risk/query id is embedded.
        for field in ("candidate_id", "risk_instance_id", "query_id"):
            assert not hasattr(cer, field)

    def test_deterministic_replay_same_inputs_same_outcome(self):
        """Running the same N->N+1 replay twice yields identical identity,
        candidate and reconcile outcomes."""
        m = build_cm_challenge_matrix()
        case = m.by_number(15)
        svc1, lc1, adapter1 = self._setup()
        r1 = run_n_to_n1_replay(
            case=case, service=svc1, lifecycle=lc1, adapter=adapter1)
        svc2, lc2, adapter2 = self._setup()
        r2 = run_n_to_n1_replay(
            case=case, service=svc2, lifecycle=lc2, adapter=adapter2)
        # identity_id + candidate_id are deterministic across lifecycles;
        # risk_instance_id is R2-assigned and need not be byte-identical.
        assert r1.n_identity_id == r2.n_identity_id
        assert r1.n_candidate_id == r2.n_candidate_id
        assert len(r1.reconcile.closed) == len(r2.reconcile.closed)

    def test_d02_result_duck_types_into_lifecycle_without_medical_grading(self):
        """Case 30: a D02 result without MedicalGrading is accepted by the
        lifecycle adapter's promote path (neutral protocol)."""
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(30)
        exp_n, res_n = case.build()
        pos = [r for r in res_n
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert not hasattr(pos, "medical_grading")
        outcome = adapter.promote_unit_result(pos)
        assert outcome.established_any
        assert len(outcome.established_risk_ids) == len(pos.r2_candidates)
        assert lc.verify_chain(PROJECT_ID)

    def test_identity_tamper_rejected_before_side_effect(self):
        """A tampered risk_candidate_ref (wrong risk_identity_id) is rejected
        before any lifecycle side effect (Codex round-3 finding 3)."""
        from dataclasses import replace as _replace
        from mm_r4.contracts import RiskCandidateRef
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(1)
        exp_n, res_n = case.build()
        pos = [r for r in res_n
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        # Tamper: replace the candidate ref's risk_identity_id with a wrong
        # value while keeping the real candidate.  The adapter verifies
        # that each ref's identity exactly matches its candidate's identity
        # BEFORE any registration/establishment side effect.
        real_ref = pos.risk_candidate_refs[0]
        tampered_ref = RiskCandidateRef(
            candidate_id=real_ref.candidate_id,
            risk_identity_id="risk-id-tampered",
            locator=real_ref.locator)
        tampered_pos = _replace(
            pos, risk_candidate_refs=(tampered_ref,))
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError):
            adapter.promote_unit_result(tampered_pos)
        # No side effect: no risk established.
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_case14_different_drug_neither_persists_nor_closes_old_risk(self):
        """§12 item 14: establish an old risk from drug A, then evaluate a
        different medication (drug B) for the same subject at N+1.  The
        old risk must neither persist (no exact identity match) nor close
        (no exact linked-negative); it carries forward stays active."""
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case14 = m.by_number(14)
        # N: establish the risk from drug A (14a positive).
        exp_n, res_n = case14.build()
        pos_a = [r for r in res_n
                 if r.l1_disposition == L1Disposition.POSITIVE][0]
        outcome = adapter.promote_unit_result(pos_a)
        inst_id, ident_id = outcome.established_risk_ids[0]
        established = lc.get(inst_id)
        assert established.current_state == "established"
        # N+1: ONLY drug B (14b) re-evaluated under the same rule (targets
        # ingredientA, not ingredientC).  Drug B produces a negative (no
        # match) and a not_evaluable indication -- no candidate carries the
        # old risk's identity.
        ep_b = make_episode(
            record_id="CM#14b", subject="SYN-014",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientC"),),
                original_name="合成药物C"))
        rule_a = make_rule(
            rule_id="R-PROH-14", target_kind=TARGET_KIND_INGREDIENT,
            target_value="ingredientA", priority="high",
            clause_locator="P14")
        _, by_n1 = evaluate(
            (ep_b,), (rule_a,), snapshot_id="snap-d02-N1")
        res_n1 = [r for urs in by_n1.values() for r in urs]
        # No N+1 candidate carries the old identity.
        n1_ids = {str(c.detail.get("risk_identity_id", ""))
                  for r in res_n1 for c in r.r2_candidates}
        assert ident_id not in n1_ids, (
            "drug B must not carry drug A's risk identity")
        ledger = make_closed_cm_ledger(res_n1, snapshot_id="snap-d02-N1")
        reconcile = adapter.reconcile_n_to_n1(
            previous_instances=[established],
            next_unit_results=res_n1,
            coverage_snapshot_id="snap-d02-N1",
            coverage_ledger=ledger)
        # The old risk is NOT persisted (no exact identity match).
        assert len(reconcile.persisted) == 0, (
            "different drug must not persist the old risk")
        # The old risk is NOT closed (no exact linked-negative).
        assert len(reconcile.closed) == 0, (
            "different drug must not close the old risk")
        # It carries forward (stays active, not closed).
        assert len(reconcile.carry_forward) == 1
        assert lc.get(inst_id).current_state == "established"
        assert lc.verify_chain(PROJECT_ID)

    def test_case25_identity_continuity_across_locator_change(self):
        """§12 item 25: same stable CM event, same ingredient/rule/lineage,
        but the full source locator (snapshot/revision) changes between N
        and N+1.  The risk_identity_id must stay continuous because the
        classifier excludes snapshot/revision and the scope lineage is
        unchanged."""
        from mm_r4.cm import CMIntervalDescriptor, MedicationEpisode
        m = build_cm_challenge_matrix()
        svc, lc, adapter = self._setup()
        case25 = m.by_number(25)
        # N: evaluate at the default snapshot.
        exp_n, res_n = case25.build()
        pos_n = [r for r in res_n
                 if r.l1_disposition == L1Disposition.POSITIVE][0]
        id_n = str(pos_n.r2_candidates[0].detail.get("risk_identity_id", ""))
        loc_n_id = pos_n.source_record_refs[0].locator.locator_id()
        outcome = adapter.promote_unit_result(pos_n)
        inst_id, ident_id = outcome.established_risk_ids[0]
        # N+1: rebuild the SAME episode but with a different source locator
        # (different snapshot_id + source_revision_id).  The
        # stable_cm_source_event_key, ingredient, rule, dictionary hash and
        # strategy are all unchanged.
        binding = make_binding((IngredientBinding(ingredient="ingredientA"),))
        rule = make_rule(
            rule_id="R-PROH-25", target_kind=TARGET_KIND_INGREDIENT,
            target_value="ingredientA", priority="medium",
            clause_locator="P25")
        loc_n1 = SourceLocator(
            snapshot_id="snap-d02-N1-25",
            source_revision_id="rev-d02-N1-25",
            table_semantic="recorded_cm", record_id="CM#25",
            column_or_anchor="row")
        ep_n1 = MedicationEpisode(
            episode_id="ep-CM#25", subject_ref="SYN-001", site_ref="SITE01",
            stable_cm_source_event_key="recorded_cm:CM#25",
            source_locator=loc_n1, identity_binding=binding,
            interval=CMIntervalDescriptor(
                cm_start="2026-01-03", cm_end="2026-01-05",
                applicable_phase="treatment"),
            study_phase="treatment", study_phase_confirmed=True)
        _, by_n1 = evaluate(
            (ep_n1,), (rule,), snapshot_id="snap-d02-N1-25")
        pos_n1 = [r for urs in by_n1.values() for r in urs
                  if r.l1_disposition == L1Disposition.POSITIVE][0]
        id_n1 = str(pos_n1.r2_candidates[0].detail.get("risk_identity_id", ""))
        loc_n1_id = pos_n1.source_record_refs[0].locator.locator_id()
        # The full locator changed (snapshot/revision differ).
        assert loc_n_id != loc_n1_id, (
            "the full source locator must change between N and N+1")
        # The identity is continuous: same stable_core, same identity_id.
        assert id_n == id_n1, (
            "identity must be continuous when only the locator changes")
        core_n = str(pos_n.r2_candidates[0].detail.get("stable_core", ""))
        core_n1 = str(pos_n1.r2_candidates[0].detail.get("stable_core", ""))
        assert core_n == core_n1
        # Reconcile: the N+1 positive matches the N identity exactly ->
        # the risk persists (identity continuity proven through lifecycle).
        established = lc.get(inst_id)
        ledger = make_closed_cm_ledger(
            [pos_n1] + [r for r in by_n1.get("SYN-001", [])
                        if r.unit_id != pos_n1.unit_id],
            snapshot_id="snap-d02-N1-25")
        reconcile = adapter.reconcile_n_to_n1(
            previous_instances=[established],
            next_unit_results=[pos_n1] + [
                r for r in by_n1.get("SYN-001", [])
                if r.unit_id != pos_n1.unit_id],
            coverage_snapshot_id="snap-d02-N1-25",
            coverage_ledger=ledger)
        assert len(reconcile.persisted) == 1, (
            "identity continuity must persist the risk across locator change")
        assert lc.get(inst_id).current_state == "established"

    def test_case26_competing_identity_bindings_detected_by_reconcile(self):
        """§12 item 26: N+1 carries two versioned identity bindings for the
        same stable_core (same source event, same ingredient/rule, but
        different dictionary content hash).  The reconcile must detect the
        competing identities and produce identity_ambiguous, rejecting any
        auto-close.  This is NOT a direct mark_identity_ambiguous call."""
        svc, lc, adapter = self._setup()
        rule = make_rule(
            rule_id="R-PROH-26", target_kind=TARGET_KIND_INGREDIENT,
            target_value="ingredientA", priority="medium",
            clause_locator="P26")
        strat = make_strategy()
        # N: establish risk with dictionary hash dh1.
        ep_n = make_episode(
            record_id="CM#26",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),),
                dictionary_content_hash="dh1"))
        _, by_n = evaluate((ep_n,), (rule,), strategy=strat,
                           snapshot_id="snap-d02-N")
        pos_n = [r for urs in by_n.values() for r in urs
                 if r.l1_disposition == L1Disposition.POSITIVE][0]
        outcome = adapter.promote_unit_result(pos_n)
        inst_id, ident_id = outcome.established_risk_ids[0]
        established = lc.get(inst_id)
        assert established.current_state == "established"
        # N+1: two episodes for the SAME source event but different
        # dictionary hashes (dh2, dh3).  Neither matches the N identity
        # (dh1).  Both produce the same stable_core but different
        # risk_identity_id -> competing identities.
        ep_n1a = make_episode(
            record_id="CM#26",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),),
                dictionary_content_hash="dh2"))
        ep_n1b = make_episode(
            record_id="CM#26",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),),
                dictionary_content_hash="dh3"))
        _, by_n1 = evaluate((ep_n1a, ep_n1b), (rule,), strategy=strat,
                            snapshot_id="snap-d02-N1")
        res_n1 = [r for urs in by_n1.values() for r in urs]
        pos_n1 = [r for r in res_n1
                  if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(pos_n1) == 2, "expected two competing positive units"
        cores = {str(c.detail.get("stable_core", ""))
                 for r in pos_n1 for c in r.r2_candidates}
        ids = {str(c.detail.get("risk_identity_id", ""))
               for r in pos_n1 for c in r.r2_candidates}
        assert len(cores) == 1, "competing bindings share the same stable_core"
        assert len(ids) == 2, "competing bindings have different identity ids"
        assert ident_id not in ids, "neither N+1 identity matches N"
        # Force non-positive units to negative for ledger completeness.
        from dataclasses import replace as _replace
        forced = []
        for r in res_n1:
            if r.l1_disposition == L1Disposition.POSITIVE:
                forced.append(r)
            else:
                forced.append(_replace(
                    r, l1_disposition=L1Disposition.NEGATIVE,
                    r2_candidates=(), risk_candidate_refs=(),
                    query_refs=(), cross_domain_evidence_refs=(),
                    positive_subtype="", audience_label="",
                    not_evaluable_reason="", boundary_reason=""))
        ledger = make_closed_cm_ledger(forced, snapshot_id="snap-d02-N1")
        reconcile = adapter.reconcile_n_to_n1(
            previous_instances=[established],
            next_unit_results=forced,
            coverage_snapshot_id="snap-d02-N1",
            coverage_ledger=ledger)
        assert len(reconcile.identity_ambiguous) == 1, (
            "competing identities must produce identity_ambiguous")
        assert len(reconcile.closed) == 0, (
            "identity_ambiguous must reject auto-close")
        assert len(reconcile.persisted) == 0
        assert lc.get(inst_id).current_state == "identity_ambiguous"
        assert lc.verify_chain(PROJECT_ID)


# ===========================================================================
# Compound episode rollup: simultaneous positive + not_evaluable flags
# ===========================================================================

class TestCompoundRollup:

    def test_compound_rollup_preserves_all_child_flags(self):
        from mm_r4.cm import evaluate_cm_slice
        m = build_cm_challenge_matrix()
        c = m.by_number(4)  # compound: positive + not_evaluable
        episodes = list(c.build_episodes())
        rules = list(c.build_rules())
        slice_results = evaluate_cm_slice(
            project_id=PROJECT_ID, episodes=episodes, active_rules=rules,
            strategy=make_strategy())
        subj = episodes[0].subject_ref
        sr = slice_results[subj]
        from mm_r4.cm import expand_cm_expected_set
        exp = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=episodes, active_rules=rules,
            strategy=make_strategy())
        rollups = sr.episode_rollups(exp)
        assert len(rollups) == 1
        rollup = rollups[0]
        assert rollup.has_positive
        assert rollup.has_not_evaluable
        # L2 source record count: the single CM#4 record.
        assert rollup.source_record_count == 1
