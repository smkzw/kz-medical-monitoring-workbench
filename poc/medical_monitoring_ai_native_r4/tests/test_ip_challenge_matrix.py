"""R4-D03 IP adversarial challenge-matrix + N-to-N+1 lifecycle tests
(worker_03).

Drives the synthetic :func:`build_ip_challenge_matrix` fixtures (all 51
frozen §11 cases) through the real D03 engine (``mm_r4.ip``), the real
projection (``mm_r4.ip_projection``) and the real R2 lifecycle, proving
every frozen challenge row behaves as specified:

* all 51 numbered cases produce the expected per-unit L1 dispositions and
  candidate/Query counts (rows 1-10: six positives + six negatives,
  boundary, fail-closed not_evaluable, exposure-day semantics,
  medical-trigger linkage, binding/disclosure, §5.4 return decision
  table, planned/actual actions, adherence arithmetic, determinism);
* actual exposure days never equal treatment span; multi-dose days count
  once; continuous intervals expand only with explicit semantics +
  policy; same-role overlaps union; different-dose overlaps never merge
  (row 4, cases 24-27);
* wrong subject/site/episode and unconfirmed relations never form a
  positive/negative (row 5, case 28);
* blinded/masked disclosure never leaks drug identity into any
  evaluation text or marker (rows 2/6, cases 17/31);
* N-to-N+1 lifecycle replay proves immutable historical completion,
  stable event identity, versioned lineage supersede (never
  resolved_by_data), positive + not_evaluable sibling rollup coexistence,
  and deterministic replay (row 11, cases 47-49);
* Query drafts are three-part Chinese, ask to verify (never state
  confirmed PD), and carry no 'sent' flag (row 12);
* ``accountability_proxy`` user-visible Query/evidence/projection
  carries ``按发放/回收核算`` and never presents proven
  ``实际服药天数`` (§6.2, cases 11/12);
* accountability balances are only compared in the algorithm's canonical
  unit: a versioned 片->mg conversion that closes the balance is
  negative, and the same cross-unit inputs without a conversion basis
  fail closed to not_evaluable with no candidate/Query (§6.2 rules 1/3,
  cases 50-51);
* the projection emits typed events/risk markers/joins with stable ids
  and one-hop source drill-back, and the canonical payload is
  byte-deterministic (rows 10/12);
* D01/D02 stay regression-free through the shared root package (row 13).

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

from mm_r4.ip_fixtures import (  # noqa: E402
    PROJECT_ID,
    SNAPSHOT_ID,
    SOURCE_REV_ID,
    build_ip_challenge_matrix,
    evaluate_one,
    make_acceptance_service,
    make_adherence_algorithm,
    make_baseline_snapshot,
    make_closed_ip_ledger,
    make_lifecycle,
    make_plan_actual_rule,
    make_subsequent_snapshot,
    run_n_to_n1_replay,
)
from mm_r4.ip import (  # noqa: E402
    CONTROL_ACCOUNTABILITY,
    METRIC_AMOUNT_RATIO,
    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
    POSITIVE_SUBTYPE_LABELS,
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
    D03_DOMAIN,
)
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    L2ObjectType,
    QueryDraftRef,
    RiskDomainUnitResult,
    canonical_json,
    content_hash,
)
from mm_r4.coverage import is_domain_complete  # noqa: E402
from mm_r4.ip_projection import (  # noqa: E402
    EVENT_KIND_ADMINISTRATION,
    EVENT_KIND_AE,
    EVENT_KIND_DISPENSE,
    EVENT_KIND_RETURN,
    EVENT_KIND_VISIT,
    IP_EVENT_KINDS,
    JOIN_REASON_UNIT_IDENTITY,
    PLANNED_OR_ACTUAL_ACTUAL,
    PLANNED_OR_ACTUAL_CONTEXT,
    PLANNED_OR_ACTUAL_PLANNED,
    project_ip_subject_journey,
)
from mm_r4.lifecycle import (  # noqa: E402
    CLOSE_REASON_RESOLVED_BY_DATA,
    R4LifecycleAdapter,
)


# ===========================================================================
# Matrix integrity
# ===========================================================================

class TestMatrixIntegrity:
    """The matrix has exactly 51 cases numbered 1-51, all buildable."""

    def test_matrix_has_51_cases_numbered_1_to_51(self):
        m = build_ip_challenge_matrix()
        assert m.case_count == 51
        assert m.numbers == tuple(range(1, 52))

    def test_case_lookup_by_number_and_name(self):
        m = build_ip_challenge_matrix()
        assert m.by_number(1).number == 1
        assert m.by_name("plan_actual_dose_mismatch_positive").number == 1
        with pytest.raises(KeyError):
            m.by_number(99)

    def test_every_case_builds_and_evaluates(self):
        m = build_ip_challenge_matrix()
        for c in m.cases:
            exp, results = c.build()
            assert exp.count == c.expected_count(), (
                f"case {c.number} ({c.name}) expected_set size "
                f"{c.expected_count()} != expansion {exp.count}")
            assert len(results) == exp.count, (
                f"case {c.number} result count != expansion count")

    def test_ip_public_root_exports_are_object_identical(self):
        import mm_r4
        from mm_r4 import ip, ip_projection, ip_fixtures

        assert mm_r4.IPExposureEpisode is ip.IPExposureEpisode
        assert mm_r4.IPUnitResult is ip.IPUnitResult
        assert mm_r4.evaluate_ip_slice is ip.evaluate_ip_slice
        assert (mm_r4.IPSubjectJourneyProjection
                is ip_projection.IPSubjectJourneyProjection)
        assert (mm_r4.project_ip_subject_journey
                is ip_projection.project_ip_subject_journey)
        assert mm_r4.IPJourneyEvent is ip_projection.IPJourneyEvent
        assert (mm_r4.build_ip_challenge_matrix
                is ip_fixtures.build_ip_challenge_matrix)
        assert mm_r4.IPChallengeCase is ip_fixtures.IPChallengeCase


# ===========================================================================
# Expected-unit matching helper
# ===========================================================================

def _match_expected(case, exp_unit, expansion, results):
    """Find the result unit matching an expected-unit spec and return it.

    Matching: by control_item / control_token substring (against the
    expansion unit), then verify the result's L1.
    """
    matched_result = None
    for i, eu in enumerate(expansion.units):
        uid = eu.build_unit(PROJECT_ID).unit_id
        if exp_unit.matches_unit(eu):
            for r in results:
                if r.unit_id == uid:
                    matched_result = r
                    break
            break
    if exp_unit.unit_index is not None:
        # index-based: pick the nth result in expansion order
        ordered_ids = [eu.build_unit(PROJECT_ID).unit_id
                       for eu in expansion.units]
        id_to_result = {r.unit_id: r for r in results}
        idx = exp_unit.unit_index
        if 0 <= idx < len(ordered_ids):
            matched_result = id_to_result.get(ordered_ids[idx])
    assert matched_result is not None, (
        f"case {case.number}: no unit matched expected spec "
        f"(item={exp_unit.control_item_contains!r}, "
        f"token={exp_unit.control_token_contains!r})")
    return matched_result


def _assert_expected_unit(case, exp_unit, expansion, results):
    r = _match_expected(case, exp_unit, expansion, results)
    assert r.l1_disposition == exp_unit.expected_l1, (
        f"case {case.number} ({case.name}): unit "
        f"item~{exp_unit.control_item_contains!r} "
        f"token~{exp_unit.control_token_contains!r} expected L1 "
        f"{exp_unit.expected_l1!r}, got {r.l1_disposition!r}")
    if exp_unit.expected_candidate_count is not None:
        assert len(r.r2_candidates) == exp_unit.expected_candidate_count, (
            f"case {case.number}: expected "
            f"{exp_unit.expected_candidate_count} candidates, got "
            f"{len(r.r2_candidates)}")
    if exp_unit.expected_query_count is not None:
        assert len(r.query_refs) == exp_unit.expected_query_count, (
            f"case {case.number}: expected {exp_unit.expected_query_count} "
            f"queries, got {len(r.query_refs)}")
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


def _run_case(number):
    c = build_ip_challenge_matrix().by_number(number)
    exp, results = c.build()
    for eu in c.expected_units:
        _assert_expected_unit(c, eu, exp, results)
    return c, exp, results


# ===========================================================================
# Cases 1-12: six positives + six negatives
# ===========================================================================

class TestCases1to12CoreDispositions:

    def test_case1_plan_actual_dose_mismatch_positive(self):
        c, exp, results = _run_case(1)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        # Query basis cites the versioned rule, never a confirmed PD.
        q = pos.query_refs[0]
        assert "R-IP-01" in q.basis
        assert "请核实" in q.action

    def test_case2_plan_actual_consistent_negative(self):
        _run_case(2)

    def test_case3_role_phase_mismatch_positive(self):
        c, exp, results = _run_case(3)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert pos.positive_subtype == \
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH

    def test_case4_role_phase_consistent_negative(self):
        _run_case(4)

    def test_case5_adherence_day_ratio_low_positive(self):
        _run_case(5)

    def test_case6_adherence_day_ratio_in_range_negative(self):
        _run_case(6)

    def test_case7_unsupported_dose_reduce_25_vs_50_positive(self):
        c, exp, results = _run_case(7)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert "25" in pos.evidence[0].uncertainty_note
        assert pos.positive_subtype == \
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION

    def test_case8_supported_dose_reduce_negative(self):
        _run_case(8)

    def test_case9_medical_trigger_action_conflict_positive(self):
        _run_case(9)

    def test_case10_medical_trigger_action_consistent_negative(self):
        _run_case(10)

    def test_case11_accountability_balance_mismatch_positive(self):
        c, exp, results = _run_case(11)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert pos.positive_subtype == \
            POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY

    def test_case12_accountability_balance_closed_negative(self):
        _run_case(12)

    def test_six_positives_carry_distinct_subtypes_and_labels(self):
        """Row 1: each positive carries its own subtype + §8 Chinese label,
        and no engineering code leaks into the audience label."""
        for number in (1, 3, 5, 7, 9, 11):
            c, exp, results = _run_case(number)
            pos = [r for r in results
                   if r.l1_disposition == L1Disposition.POSITIVE]
            assert pos, f"case {number} expected a positive"
            for r in pos:
                assert r.positive_subtype in POSITIVE_SUBTYPE_LABELS
                assert r.audience_label == POSITIVE_SUBTYPE_LABELS[
                    r.positive_subtype]
                for token in ("RiskCandidate", "positive", "候选信号",
                              "正式事实", "只读"):
                    assert token not in r.audience_label, (
                        f"case {number}: audience label "
                        f"{r.audience_label!r} contains jargon {token!r}")


# ===========================================================================
# Proxy user language (§6.2, cases 11/12)
# ===========================================================================

class TestAccountabilityProxyUserLanguage:
    """FROZEN §6.2 (cases 11/12): ``accountability_proxy`` user-visible
    Query/evidence/projection must carry ``按发放/回收核算`` and must
    never present proven ``实际服药天数``."""

    PROXY_PHRASE = "按发放/回收核算"
    PROVEN_DAYS_TOKEN = "实际服药天数"

    def _accountability_unit(self, case, exp, results):
        item_by_uid = {eu.build_unit(PROJECT_ID).unit_id: eu.control_item
                       for eu in exp.units}
        for r in results:
            if item_by_uid.get(r.unit_id, "") == CONTROL_ACCOUNTABILITY:
                return r
        raise AssertionError(
            f"case {case.number}: no accountability unit in results")

    def test_cases_11_and_12_are_proxy_backed(self):
        """The user-language invariant applies to real proxy metrics."""
        for number in (11, 12):
            c = build_ip_challenge_matrix().by_number(number)
            algs = list(c.build_algorithms())
            assert len(algs) == 1
            assert algs[0].is_accountability_proxy, (
                f"case {number} must be accountability_proxy")

    def test_case11_positive_query_and_evidence_annotated(self):
        c, exp, results = _run_case(11)
        r = self._accountability_unit(c, exp, results)
        assert r.l1_disposition == L1Disposition.POSITIVE
        q_txt = " ".join(q.basis + q.finding + q.action
                         for q in r.query_refs)
        ev_txt = " ".join(e.uncertainty_note for e in r.evidence)
        assert self.PROXY_PHRASE in q_txt, "proxy positive Query text"
        assert self.PROXY_PHRASE in ev_txt, "proxy positive evidence"
        assert self.PROVEN_DAYS_TOKEN not in q_txt
        assert self.PROVEN_DAYS_TOKEN not in ev_txt

    def test_case12_negative_evidence_annotated_no_query(self):
        c, exp, results = _run_case(12)
        r = self._accountability_unit(c, exp, results)
        assert r.l1_disposition == L1Disposition.NEGATIVE
        ev_txt = " ".join(e.uncertainty_note for e in r.evidence)
        assert self.PROXY_PHRASE in ev_txt, "proxy negative evidence"
        assert self.PROVEN_DAYS_TOKEN not in ev_txt
        assert not r.query_refs, "negative proxy must not draft a Query"

    def test_case11_projection_payload_annotated(self):
        c = build_ip_challenge_matrix().by_number(11)
        sr, exp = c.build_slice()
        proj = project_ip_subject_journey(
            sr, expansions=exp,
            occurrences=list(c.build_occurrences()),
            action_evidence=list(c.build_evidence()),
            planned_actions=list(c.build_planned_actions()),
            actual_actions=list(c.build_actual_actions()),
            return_records=list(c.build_returns()),
            dispense_records=list(c.build_dispenses()))
        payload = canonical_json(proj.canonical_payload())
        assert self.PROXY_PHRASE in payload, (
            "case 11 projection payload must annotate the proxy")
        assert self.PROVEN_DAYS_TOKEN not in payload
        markers = [mk for mk in proj.risk_markers if mk.is_risk_marker]
        acc = [mk for mk in markers
               if mk.audience_label == POSITIVE_SUBTYPE_LABELS[
                   POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY]]
        assert acc, "case 11 must project the accountability risk marker"
        assert all(self.PROXY_PHRASE in mk.uncertainty for mk in acc)

    def test_case12_projection_payload_never_claims_proven_days(self):
        c = build_ip_challenge_matrix().by_number(12)
        sr, exp = c.build_slice()
        proj = project_ip_subject_journey(
            sr, expansions=exp,
            occurrences=list(c.build_occurrences()),
            action_evidence=list(c.build_evidence()),
            planned_actions=list(c.build_planned_actions()),
            actual_actions=list(c.build_actual_actions()),
            return_records=list(c.build_returns()),
            dispense_records=list(c.build_dispenses()))
        payload = canonical_json(proj.canonical_payload())
        assert self.PROVEN_DAYS_TOKEN not in payload

    def test_proxy_phrase_stays_scoped_to_accountability_unit(self):
        """No blanket stamping: the sibling role_phase unit of the proxy
        cases never carries the proxy annotation."""
        for number in (11, 12):
            c, exp, results = _run_case(number)
            item_by_uid = {eu.build_unit(PROJECT_ID).unit_id: eu.control_item
                           for eu in exp.units}
            for r in results:
                if item_by_uid.get(r.unit_id, "") == CONTROL_ACCOUNTABILITY:
                    continue
                text = " ".join(e.uncertainty_note for e in r.evidence)
                assert self.PROXY_PHRASE not in text, (
                    f"case {number}: proxy phrase leaked into a "
                    f"non-accountability unit {r.unit_id!r}")


# ===========================================================================
# Accountability unit conversion (§6.2 rules 1/3, cases 50-51)
# ===========================================================================

class TestAccountabilityUnitConversion:
    """FROZEN §6.2 rules 1/3: ``accountability_proxy`` balances are only
    compared in the algorithm's canonical unit.  A versioned conversion
    that closes the balance is negative; the same cross-unit inputs
    without a conversion basis fail closed to not_evaluable with no
    candidate/Query (cases 50-51)."""

    PROXY_PHRASE = "按发放/回收核算"
    PROVEN_DAYS_TOKEN = "实际服药天数"

    def _accountability_unit(self, case, exp, results):
        item_by_uid = {eu.build_unit(PROJECT_ID).unit_id: eu.control_item
                       for eu in exp.units}
        for r in results:
            if item_by_uid.get(r.unit_id, "") == CONTROL_ACCOUNTABILITY:
                return r
        raise AssertionError(
            f"case {case.number}: no accountability unit in results")

    def test_cases_50_and_51_are_cross_unit_proxy_inputs(self):
        """Both cases carry 片 dispense/return rows, an mg recorded value,
        an accountability_proxy algorithm and mg canonical unit."""
        for number in (50, 51):
            c = build_ip_challenge_matrix().by_number(number)
            algs = list(c.build_algorithms())
            assert len(algs) == 1
            assert algs[0].is_accountability_proxy, (
                f"case {number} must be accountability_proxy")
            assert algs[0].canonical_unit == "mg"
            assert all(d.amount_unit == "片"
                       for d in c.build_dispenses())
            assert all(r.amount_unit == "片" for r in c.build_returns())
            assert all(o.unit == "mg" for o in c.build_observations())

    def test_case50_converted_balance_closes_negative(self):
        """20 片 - 10 片 converts to 100 - 50 = 50 mg == recorded 50 mg."""
        c, exp, results = _run_case(50)
        r = self._accountability_unit(c, exp, results)
        assert r.l1_disposition == L1Disposition.NEGATIVE
        assert not r.r2_candidates, \
            "converted negative must carry no candidate"
        assert not r.query_refs, "converted negative must not draft a Query"

    def test_case50_negative_evidence_keeps_proxy_annotation(self):
        """The converted-negative evidence retains 按发放/回收核算 and
        never claims proven 实际服药天数."""
        c, exp, results = _run_case(50)
        r = self._accountability_unit(c, exp, results)
        ev_txt = " ".join(e.uncertainty_note for e in r.evidence)
        assert self.PROXY_PHRASE in ev_txt, "proxy negative evidence"
        assert "核算闭环成立" in ev_txt, "negative closure reason"
        assert self.PROVEN_DAYS_TOKEN not in ev_txt

    def test_case51_no_conversion_fails_closed(self):
        """Same cross-unit inputs without a versioned conversion basis are
        not_evaluable with no candidate and no Query."""
        c, exp, results = _run_case(51)
        r = self._accountability_unit(c, exp, results)
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "换算依据" in r.not_evaluable_reason
        assert not r.r2_candidates, \
            "fail-closed not_evaluable must carry no candidate"
        assert not r.query_refs, \
            "fail-closed not_evaluable must not draft a Query"

    def test_proxy_phrase_stays_scoped_in_conversion_cases(self):
        """The sibling role_phase units of cases 50/51 never carry the
        proxy annotation."""
        for number in (50, 51):
            c, exp, results = _run_case(number)
            item_by_uid = {eu.build_unit(PROJECT_ID).unit_id: eu.control_item
                           for eu in exp.units}
            for r in results:
                if item_by_uid.get(r.unit_id, "") == CONTROL_ACCOUNTABILITY:
                    continue
                text = " ".join(e.uncertainty_note for e in r.evidence)
                assert self.PROXY_PHRASE not in text, (
                    f"case {number}: proxy phrase leaked into a "
                    f"non-accountability unit {r.unit_id!r}")


# ===========================================================================
# Cases 13-17: boundary
# ===========================================================================

class TestCases13to17Boundary:

    def test_case13_threshold_equality_boundary(self):
        c, exp, results = _run_case(13)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        # Boundary carries a candidate but never a Query.
        assert len(bnd.r2_candidates) == 1
        assert not bnd.query_refs

    def test_case14_window_endpoint_inclusivity_boundary(self):
        c, exp, results = _run_case(14)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert "端点包含关系未声明" in bnd.boundary_reason

    def test_case15_partial_date_boundary(self):
        c, exp, results = _run_case(15)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert "部分日期" in bnd.boundary_reason

    def test_case16_action_overlap_boundary(self):
        c, exp, results = _run_case(16)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert "多个计划动作" in bnd.boundary_reason

    def test_case17_blinded_ambiguous_assignment_boundary(self):
        c, exp, results = _run_case(17)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert len(bnd.r2_candidates) == 1
        # Blinded: no drug identity leaks into any evaluation text.
        for r in results:
            text = " ".join((
                r.boundary_reason, r.audience_label,
                r.not_evaluable_reason,
                " ".join(e.uncertainty_note for e in r.evidence)))
            for token in ("synthetic_drug_x", "synthetic_drug_y",
                          "drugX", "drugY"):
                assert token not in text, (
                    f"case 17 leaked {token!r}: {text!r}")


# ===========================================================================
# Cases 18-23: fail-closed not_evaluable
# ===========================================================================

class TestCases18to23NotEvaluable:

    def test_case18_missing_algorithm_not_evaluable(self):
        c, exp, results = _run_case(18)
        ne = results[0]
        assert "缺少适用的依从性算法" in ne.not_evaluable_reason
        assert not ne.r2_candidates

    def test_case19_missing_denominator_not_evaluable(self):
        c, exp, results = _run_case(19)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert ("端点包含关系未声明" in ne.not_evaluable_reason
                or "窗口" in ne.not_evaluable_reason)

    def test_case20_unit_conflict_not_evaluable(self):
        c, exp, results = _run_case(20)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "无版本化换算依据" in ne.not_evaluable_reason

    def test_case21_role_unconfirmed_not_evaluable(self):
        c, exp, results = _run_case(21)
        ne = results[0]
        assert "角色" in ne.not_evaluable_reason

    def test_case22_cm_ip_mutual_exclusion_not_evaluable(self):
        c, exp, results = _run_case(22)
        # Both sibling units fail closed on the role-conflict row.
        assert all(r.l1_disposition == L1Disposition.NOT_EVALUABLE
                   for r in results)
        assert "互斥" in results[0].not_evaluable_reason

    def test_case23_missing_occurrence_no_missed_dose(self):
        c, exp, results = _run_case(23)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "不得推断漏服" in ne.not_evaluable_reason
        # No candidate/Query is invented from the gap.
        assert not ne.r2_candidates
        assert not ne.query_refs


# ===========================================================================
# Cases 24-27: exposure-day semantics (row 4)
# ===========================================================================

class TestCases24to27ExposureDays:

    def test_case24_span_never_equals_actual_days(self):
        c, exp, results = _run_case(24)
        dc = c.day_computation()
        # 28-day span, D1 + D15 only -> exactly 2 actual exposure days.
        assert dc.actual_exposure_days == 2
        assert dc.day_set == ("2026-01-01", "2026-01-15")
        assert dc.span_start == "2026-01-01"
        assert dc.span_end == "2026-01-28"
        # The adherence unit went POSITIVE with the 2-day numerator: if the
        # engine had used the 28-day span as actual days the ratio would be
        # 28/28 = 1.0 and negative.  POSITIVE proves span is never dosing.
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE]
        assert pos, "2/28 must be out of range (span not used as dosing)"

    def test_case25_multi_dose_day_counts_once_and_interval_expands(self):
        c, exp, results = _run_case(25)
        dc = c.day_computation()
        # Two doses on 2026-01-01 count one day; the explicitly declared
        # continuous interval 01-05..01-07 expands to 3 days.
        assert dc.day_set == (
            "2026-01-01", "2026-01-05", "2026-01-06", "2026-01-07")
        assert dc.actual_exposure_days == 4

    def test_case26_same_role_overlap_unions_days(self):
        c, exp, results = _run_case(26)
        dc = c.day_computation()
        # 01-01..01-03 and 01-03..01-05 union to five days; interval lengths
        # are never summed (3 + 3 != 5 proves union semantics).
        assert dc.actual_exposure_days == 5
        assert dc.day_set == tuple(
            f"2026-01-{d:02d}" for d in range(1, 6))

    def test_case27_different_dose_overlap_never_merged(self):
        c, exp, results = _run_case(27)
        dc = c.day_computation()
        # Different-dose overlapping continuous intervals with union_fail
        # policy are ambiguous, never silently merged.
        assert dc.status == "ambiguous"
        assert dc.actual_exposure_days == 0
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert ne, "ambiguous day computation must be not_evaluable"


# ===========================================================================
# Case 28: medical-trigger linkage (row 5)
# ===========================================================================

class TestCase28MedicalLinkage:

    def test_wrong_identity_never_forms_positive_negative(self):
        c, exp, results = _run_case(28)
        # Exactly one role_phase negative; four medical units all
        # not_evaluable with the fail-closed reasons.
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert len(neg) == 1 and len(ne) == 4
        assert not any(r.l1_disposition == L1Disposition.POSITIVE
                       for r in results)
        reasons = " ".join(r.not_evaluable_reason for r in ne)
        assert "跨受试者" in reasons or "无法评价" in reasons
        assert "尚未确认" in reasons
        # None of the not_evaluable units carries a candidate or Query.
        for r in ne:
            assert not r.r2_candidates
            assert not r.query_refs


# ===========================================================================
# Cases 29-31: binding / blinding (row 6)
# ===========================================================================

class TestCases29to31BindingAndBlinding:

    def test_case29_missing_assignment_link_not_evaluable(self):
        c, exp, results = _run_case(29)
        assert results[0].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_case30_ambiguous_assignment_boundary_no_pick(self):
        c, exp, results = _run_case(30)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert len(bnd.r2_candidates) == 1
        # The kernel never picks an assignment: the reason names both
        # candidates without choosing by name/date/order.
        assert "多个可适用" in bnd.boundary_reason or \
            "候选" in bnd.boundary_reason

    def test_case31_masked_identity_no_leak(self):
        c, exp, results = _run_case(31)
        by_item = {r.l1_disposition: r for r in results}
        # Role/phase verifiable without product identity -> negative.
        assert L1Disposition.NEGATIVE in by_item
        # Masked dose makes the dose-dependent control not_evaluable.
        assert L1Disposition.NOT_EVALUABLE in by_item
        ne = by_item[L1Disposition.NOT_EVALUABLE]
        assert "披露" in ne.not_evaluable_reason
        # No unapproved identity leaks into any text.
        for r in results:
            text = " ".join((
                r.not_evaluable_reason, r.boundary_reason,
                " ".join(e.uncertainty_note for e in r.evidence)))
            for token in ("synthetic_drug_x", "drugX"):
                assert token not in text, (
                    f"case 31 leaked {token!r}: {text!r}")


# ===========================================================================
# Cases 32-37: return decision table §5.4 (row 7)
# ===========================================================================

class TestCases32to37ReturnDecisionTable:

    def test_case32_return_role_uncovered_not_evaluable(self):
        c, exp, results = _run_case(32)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "必需来源角色覆盖不完整" in ne.not_evaluable_reason

    def test_case33_return_expected_no_rows_not_evaluable(self):
        c, exp, results = _run_case(33)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "期望回收" in ne.not_evaluable_reason
        assert "不得推断未归还或未服药" in ne.not_evaluable_reason

    def test_case34_return_empty_field_not_evaluable(self):
        c, exp, results = _run_case(34)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "必需字段" in ne.not_evaluable_reason

    def test_case35_return_explicit_zero_enters_algorithm(self):
        c, exp, results = _run_case(35)
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert neg, "explicit zero return is a known value, not missing"

    def test_case36_return_partial_boundary(self):
        c, exp, results = _run_case(36)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY][0]
        assert "部分值/范围值" in bnd.boundary_reason

    def test_case37_return_not_required_not_applicable(self):
        c, exp, results = _run_case(37)
        na = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_APPLICABLE]
        assert na, "protocol-declared no-return window is not_applicable"


# ===========================================================================
# Cases 38-39: planned/actual actions (row 8)
# ===========================================================================

class TestCases38to39Actions:

    def test_case38_planned_pause_denominator_effect(self):
        c, exp, results = _run_case(38)
        # No positive: with the pause excluded, 5 actual days over
        # (10 - 5 pause days) = 1.0 is in range.
        assert not any(r.l1_disposition == L1Disposition.POSITIVE
                       for r in results)
        assert any(r.l1_disposition == L1Disposition.NEGATIVE for r in results)
        # Counter-prove the effect: the SAME inputs with the pause included
        # in the denominator yield 5/10 = 0.5 -> positive.
        alg_included = make_adherence_algorithm(
            pause_handling="included")
        exp2, results2 = evaluate_one(
            list(c.build_episodes())[0], rules=list(c.build_rules()),
            algorithms=(alg_included,),
            occurrences=list(c.build_occurrences()),
            observations=list(c.build_observations()),
            planned_actions=list(c.build_planned_actions()),
            action_coverage=True)
        pos2 = [r for r in results2
                if r.l1_disposition == L1Disposition.POSITIVE]
        assert pos2, "pause included in denominator -> 0.5 out of range"

    def test_case39_resume_closed_stop_fail_closed(self):
        c, exp, results = _run_case(39)
        disps = {r.l1_disposition: r for r in results}
        assert L1Disposition.NEGATIVE in disps
        assert L1Disposition.NOT_EVALUABLE in disps
        ne = disps[L1Disposition.NOT_EVALUABLE]
        assert "实际给药动作" in ne.not_evaluable_reason


# ===========================================================================
# Cases 40-44: adherence arithmetic (row 9)
# ===========================================================================

class TestCases40to44AdherenceArithmetic:

    def test_case40_rounding_79_95_after_rounding_negative(self):
        c, exp, results = _run_case(40)
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert neg, "79.95/100 compared AFTER rounding at 0.8 is in range"
        # The flip: compared BEFORE rounding the same inputs are positive.
        alg_before = make_adherence_algorithm(
            metric=METRIC_AMOUNT_RATIO, lower="0.8", upper=None,
            lower_inc=True, upper_inc=None, precision=2,
            compare="before", canonical_unit="", conversions=())
        exp2, results2 = evaluate_one(
            list(c.build_episodes())[0], rules=list(c.build_rules()),
            algorithms=(alg_before,),
            observations=list(c.build_observations()))
        pos2 = [r for r in results2
                if r.l1_disposition == L1Disposition.POSITIVE]
        assert pos2, "0.7995 < 0.8 before rounding must be out of range"

    def test_case41_zero_denominator_not_evaluable(self):
        c, exp, results = _run_case(41)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "分母为零" in ne.not_evaluable_reason

    def test_case42_duplicate_observation_not_evaluable(self):
        c, exp, results = _run_case(42)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "重复 observation" in ne.not_evaluable_reason

    def test_case43_unit_conversion_ok_negative(self):
        c, exp, results = _run_case(43)
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert neg, "0.05g/0.1g converts to 50mg/100mg = 0.5 in range"

    def test_case44_window_endpoint_exclusivity_flip(self):
        c, exp, results = _run_case(44)
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert neg, "9/10 at inclusive lower 0.9 is in range"
        # Exclusive window start: D1 falls out, 8/9 = 0.889 < 0.9 -> positive.
        alg_exclusive = make_adherence_algorithm(
            lower="0.9", upper=None, lower_inc=True, upper_inc=None,
            start_inc=False, end_inc=True)
        exp2, results2 = evaluate_one(
            list(c.build_episodes())[0], rules=list(c.build_rules()),
            algorithms=(alg_exclusive,),
            occurrences=list(c.build_occurrences()),
            observations=list(c.build_observations()))
        pos2 = [r for r in results2
                if r.l1_disposition == L1Disposition.POSITIVE]
        assert pos2, (
            "exclusive start: 8 in-window days / 9 window days < 0.9 must "
            "be out of range")


# ===========================================================================
# Cases 45-46: determinism (row 10)
# ===========================================================================

class TestCases45to46Determinism:

    def test_case45_locator_dedup_and_revision_conflict(self):
        c, exp, results = _run_case(45)
        ne = [r for r in results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert "accepted revision" in ne.not_evaluable_reason or \
            "重复" in ne.not_evaluable_reason
        # Deterministic: re-running yields identical unit ids and reason.
        exp2, results2 = c.build()
        assert [r.unit_id for r in results] == [r.unit_id for r in results2]
        assert ne.not_evaluable_reason == \
            [r for r in results2
             if r.l1_disposition == L1Disposition.NOT_EVALUABLE][
                 0].not_evaluable_reason

    def test_case46_out_of_order_input_same_result(self):
        c, exp, results = _run_case(46)
        # Same inputs in sorted order produce the identical result set.
        from mm_r4.ip_fixtures import evaluate_one as _eval
        ep = list(c.build_episodes())[0]
        occurrences = list(c.build_occurrences())
        exp_sorted, results_sorted = _eval(
            ep, rules=list(c.build_rules()),
            algorithms=list(c.build_algorithms()),
            occurrences=sorted(occurrences, key=lambda o: o.date_start),
            observations=list(c.build_observations()))
        assert [r.unit_id for r in results] == \
            [r.unit_id for r in results_sorted]
        assert [r.l1_disposition for r in results] == \
            [r.l1_disposition for r in results_sorted]

    def test_byte_deterministic_projection_payload(self):
        """Row 10: the projected journey payload is byte-deterministic."""
        c = build_ip_challenge_matrix().by_number(5)
        sr1, exp1 = c.build_slice()
        proj1 = project_ip_subject_journey(
            sr1, expansions=exp1, occurrences=list(c.build_occurrences()))
        sr2, exp2 = c.build_slice()
        proj2 = project_ip_subject_journey(
            sr2, expansions=exp2, occurrences=list(c.build_occurrences()))
        h1 = content_hash(canonical_json(proj1.canonical_payload()))
        h2 = content_hash(canonical_json(proj2.canonical_payload()))
        assert h1 == h2
        assert proj1.canonical_payload() == proj2.canonical_payload()


# ===========================================================================
# N-to-N+1 lifecycle replay (row 11)
# ===========================================================================

class TestNToN1Lifecycle:

    def _setup(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id="snap-d03-N",
                               revision_id="rev-N")
        make_subsequent_snapshot(svc, snapshot_id="snap-d03-N1",
                                 revision_id="rev-N1")
        # Also register the default fixture snapshot so case.build() results
        # (whose candidates carry source_snapshot_id=SNAPSHOT_ID) can be
        # promoted in the same service.
        make_baseline_snapshot(svc, snapshot_id=SNAPSHOT_ID,
                               revision_id=SOURCE_REV_ID)
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy")
        return svc, lc, adapter

    def test_linked_negative_closes_medium_risk_and_preserves_history(self):
        """Case 47: N positive (medium) -> N+1 complete linked-negative ->
        machine close; historical record preserved (immutable)."""
        m = build_ip_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(47)
        replay = run_n_to_n1_replay(
            case=case, service=svc, lifecycle=lc, adapter=adapter)
        assert replay.established_instance.severity == "medium"
        assert replay.established_instance.current_state == "established"
        assert len(replay.reconcile.closed) == 1
        closed = replay.reconcile.closed[0]
        assert closed.risk_instance_id == replay.n_instance_id
        assert closed.risk_identity_id == replay.n_identity_id
        post = lc.get(replay.n_instance_id)
        assert post.current_state == "closed"
        assert post.risk_identity_id == replay.n_identity_id
        transitions = post.transitions
        close_ts = [t for t in transitions if t.to_state == "closed"]
        assert len(close_ts) == 1, "exactly one close transition"
        assert close_ts[0].reason == CLOSE_REASON_RESOLVED_BY_DATA
        est_ts = [t for t in transitions if t.to_state == "established"]
        assert len(est_ts) == 1, "establish transition preserved (immutable)"
        assert est_ts[0] is not close_ts[0]

    def test_rule_version_change_supersedes_not_resolved_by_data(self):
        """Case 48: rule version/lineage change at N+1 -> supersede, never
        resolved_by_data."""
        m = build_ip_challenge_matrix()
        svc, lc, adapter = self._setup()
        case = m.by_number(48)
        replay = run_n_to_n1_replay(
            case=case, service=svc, lifecycle=lc, adapter=adapter,
            rules_override_n1=(make_plan_actual_rule(
                rule_version="v2", rule_content_hash="rc-plan-02",
                rule_lineage="rl-plan-02"),),
            force_negative_n1=False)
        assert len(replay.reconcile.superseded) == 1
        assert len(replay.reconcile.closed) == 0, (
            "lineage change must not close by data")
        post = lc.get(replay.n_instance_id)
        assert post.current_state == "superseded"
        for t in post.transitions:
            assert t.reason != CLOSE_REASON_RESOLVED_BY_DATA, (
                "supersede must not use resolved_by_data close_reason")
        assert lc.verify_chain(PROJECT_ID)

    def test_deterministic_replay_same_inputs_same_outcome(self):
        m = build_ip_challenge_matrix()
        case = m.by_number(47)
        svc1, lc1, adapter1 = self._setup()
        r1 = run_n_to_n1_replay(
            case=case, service=svc1, lifecycle=lc1, adapter=adapter1)
        svc2, lc2, adapter2 = self._setup()
        r2 = run_n_to_n1_replay(
            case=case, service=svc2, lifecycle=lc2, adapter=adapter2)
        assert r1.n_identity_id == r2.n_identity_id
        assert r1.n_candidate_id == r2.n_candidate_id
        assert len(r1.reconcile.closed) == len(r2.reconcile.closed)

    def test_positive_ne_sibling_rollup_coexistence(self):
        """Case 49: positive + not_evaluable sibling units coexist; the
        episode rollup keeps both flags and the domain is not complete."""
        c = build_ip_challenge_matrix().by_number(49)
        sr, exp = c.build_slice()
        rollups = sr.episode_rollups(exp)
        assert len(rollups) == 1
        rollup = rollups[0]
        assert rollup.has_positive
        assert rollup.has_not_evaluable
        assert rollup.has_negative
        # Any not_evaluable blocks domain completeness.
        ledger = make_closed_ip_ledger(list(sr.unit_results))
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete, (
            "domain with a not_evaluable sibling must not be complete")
        assert any("not_evaluable" in r for r in reasons)
        # The not_evaluable sibling produced no candidate/Query.
        ne = [r for r in sr.unit_results
              if r.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert not ne.r2_candidates
        assert not ne.query_refs

    def test_d03_candidates_carry_only_d03_domain(self):
        """D03 never creates D01/D02 candidates: every candidate/Query is
        D03-domain and linked to a D03 candidate."""
        for number in (1, 5, 7, 9, 11):
            c, exp, results = _run_case(number)
            for r in results:
                for cand in r.r2_candidates:
                    assert cand.domain == D03_DOMAIN, (
                        f"case {number}: D03 candidate domain must be "
                        f"{D03_DOMAIN}")
                for q in r.query_refs:
                    if q.linked_candidate_id:
                        assert q.linked_candidate_id in {
                            cand.candidate_id for cand in r.r2_candidates}


# ===========================================================================
# Coverage ledger invariants
# ===========================================================================

class TestCoverageLedgerInvariants:

    def test_closed_ledger_count_equation_holds(self):
        c = build_ip_challenge_matrix().by_number(1)
        exp, results = c.build()
        ledger = make_closed_ip_ledger(results)
        assert ledger.is_closed
        summary = ledger.close_and_summarize()
        total = sum(summary.l1_counts.get(d, 0)
                    for d in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE,
                              L1Disposition.BOUNDARY,
                              L1Disposition.NOT_APPLICABLE,
                              L1Disposition.NOT_EVALUABLE))
        assert total == summary.expected_units

    def test_l2_counts_never_contaminate(self):
        c = build_ip_challenge_matrix().by_number(1)
        exp, results = c.build()
        ledger = make_closed_ip_ledger(results)
        summary = ledger.close_and_summarize()
        l2 = summary.l2_counts
        assert l2[L2ObjectType.RISK_CANDIDATE] >= 1
        assert l2[L2ObjectType.QUERY_DRAFT] >= 1
        # risk_instance is 0 until lifecycle establishes.
        assert l2[L2ObjectType.RISK_INSTANCE] == 0

    def test_ip_unit_result_satisfies_neutral_protocol(self):
        c = build_ip_challenge_matrix().by_number(1)
        exp, results = c.build()
        for r in results:
            assert isinstance(r, RiskDomainUnitResult)
        # It materializes a full UnitEvaluation for the ledger.
        from mm_r4.contracts import UnitEvaluation
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        ue = pos.to_unit_evaluation(
            l0_status="covered",
            provenance_snapshot_id="snap-x",
            provenance_rule_lineage="rl")
        assert isinstance(ue, UnitEvaluation)


# ===========================================================================
# Query export != send (anti-invariant, row 12)
# ===========================================================================

class TestQueryExportNotSend:

    def test_query_draft_three_part_and_no_sent_flag(self):
        for number in (1, 3, 5, 7, 9, 11):
            c, exp, results = _run_case(number)
            for r in results:
                for q in r.query_refs:
                    assert isinstance(q, QueryDraftRef)
                    assert q.basis.startswith("依据")
                    assert q.finding.startswith("发现")
                    assert q.action.startswith("行动项")
                    assert q.source_locator_ids, (
                        f"case {number}: query must carry minimum source "
                        f"locators")
                    assert "请核实" in q.action, (
                        f"case {number}: action must request verification")
                    # Never a 'sent'/'delivered'/'status' flag.
                    for forbidden_attr in ("sent", "delivered", "status"):
                        assert not hasattr(q, forbidden_attr)
                    # Never states confirmed PD.
                    for token in ("报送", "已构成 PD", "已构成PD",
                                  "判定为PD", "判定为 PD", "正式判定"):
                        assert token not in q.action and token not in \
                            q.finding and token not in q.basis, (
                            f"case {number}: query contains confirmed-PD "
                            f"language {token!r}")


# ===========================================================================
# Projection: typed events, Chinese labels, join, drill-back (row 12)
# ===========================================================================

class TestProjectionJourneyAndJoin:

    def test_typed_event_kinds_and_planned_actual(self):
        # Case 9 has an AE trigger context event; case 11 has dispense +
        # return events; case 7 has planned/actual action events.
        for number, expected_kinds in (
                (1, {EVENT_KIND_ADMINISTRATION, EVENT_KIND_VISIT}),
                (9, {EVENT_KIND_ADMINISTRATION, EVENT_KIND_AE,
                     EVENT_KIND_VISIT}),
                (11, {EVENT_KIND_ADMINISTRATION, EVENT_KIND_DISPENSE,
                      EVENT_KIND_RETURN, EVENT_KIND_VISIT}),
        ):
            c = build_ip_challenge_matrix().by_number(number)
            sr, exp = c.build_slice()
            proj = project_ip_subject_journey(
                sr, expansions=exp,
                occurrences=list(c.build_occurrences()),
                action_evidence=list(c.build_evidence()),
                planned_actions=list(c.build_planned_actions()),
                actual_actions=list(c.build_actual_actions()),
                return_records=list(c.build_returns()),
                dispense_records=list(c.build_dispenses()))
            kinds = {e.event_kind for e in proj.events}
            assert expected_kinds <= kinds, (
                f"case {number}: expected kinds {expected_kinds} in {kinds}")
            for e in proj.events:
                assert e.event_kind in IP_EVENT_KINDS
                assert e.planned_or_actual in (
                    PLANNED_OR_ACTUAL_PLANNED, PLANNED_OR_ACTUAL_ACTUAL,
                    PLANNED_OR_ACTUAL_CONTEXT)
                assert e.source_locator_ids, "event must carry locators"

    def test_risk_marker_subtype_and_chinese_label(self):
        c = build_ip_challenge_matrix().by_number(1)
        sr, exp = c.build_slice()
        proj = project_ip_subject_journey(
            sr, expansions=exp, occurrences=list(c.build_occurrences()))
        risk_markers = [m for m in proj.risk_markers if m.is_risk_marker]
        assert risk_markers, "expected at least one risk marker"
        for m in risk_markers:
            assert m.subtype == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH
            assert m.audience_label == POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH]
            assert m.priority in ("high", "medium", "low", "unknown")
            assert m.typed_refs, "marker must carry typed refs"
            for ref in m.typed_refs:
                assert ref.kind in (
                    "assignment", "rule", "algorithm", "medical_event",
                    "source_locator", "query")
                assert ref.ref_id, "typed ref id is required"

    def test_bidirectional_join_by_stable_ids(self):
        c = build_ip_challenge_matrix().by_number(1)
        sr, exp = c.build_slice()
        proj = project_ip_subject_journey(
            sr, expansions=exp, occurrences=list(c.build_occurrences()))
        markers = [m for m in proj.risk_markers if m.is_risk_marker]
        assert markers
        marker = markers[0]
        joined = proj.join.events_for_marker(marker.marker_id)
        assert joined, "marker must join at least one typed event"
        event_ids = set(proj.join.events_for_marker(marker.marker_id))
        for ev in proj.events:
            if ev.event_id in event_ids:
                # Join edge carries the marker's unit + risk identity.
                recs = [rec for rec in proj.join.records
                        if rec.event_id == ev.event_id
                        and rec.marker_id == marker.marker_id]
                assert recs
                assert recs[0].unit_id == marker.unit_id
                assert recs[0].risk_identity_id == marker.risk_identity_id
                assert recs[0].join_reason == JOIN_REASON_UNIT_IDENTITY
                # One-hop drill-back: the typed refs carry the assignment
                # and the query ids.
                typed = set(recs[0].typed_ref_ids)
                assert any(r.startswith("assignment:") for r in typed)
                assert any(r.startswith("query:") for r in typed)

    def test_no_generic_risk_collapse(self):
        """All positive subtypes across the matrix keep their distinct
        §8 audience labels in the projected markers."""
        m = build_ip_challenge_matrix()
        labels_seen = set()
        for number in (1, 3, 5, 7, 9, 11):
            c = m.by_number(number)
            sr, exp = c.build_slice()
            proj = project_ip_subject_journey(
                sr, expansions=exp,
                occurrences=list(c.build_occurrences()),
                action_evidence=list(c.build_evidence()),
                planned_actions=list(c.build_planned_actions()),
                actual_actions=list(c.build_actual_actions()),
                return_records=list(c.build_returns()),
                dispense_records=list(c.build_dispenses()))
            for mk in proj.risk_markers:
                if mk.is_risk_marker:
                    labels_seen.add(mk.audience_label)
        assert labels_seen == set(POSITIVE_SUBTYPE_LABELS.values()), (
            f"expected all six frozen labels, got {labels_seen}")

    def test_coverage_gap_marker_for_not_evaluable(self):
        """A not_evaluable unit projects a coverage-gap marker (no
        candidate) so the view surfaces the gap without inventing a risk."""
        c = build_ip_challenge_matrix().by_number(23)
        sr, exp = c.build_slice()
        proj = project_ip_subject_journey(sr, expansions=exp)
        gap = [m for m in proj.risk_markers if m.coverage_gap]
        assert gap, "case 23 must project a coverage-gap marker"
        assert all(not m.is_risk_marker for m in gap)
        assert proj.coverage_gap_marker_count >= 1


# ===========================================================================
# Adjacent regression: D01/D02 stay green through the shared root (row 13)
# ===========================================================================

class TestAdjacentRegression:

    def test_d01_fixture_still_evaluates_positive(self):
        from mm_r4.fixtures import (
            evaluate as d01_evaluate, build_challenge_matrix,
        )
        case = next(
            c for c in build_challenge_matrix().cases
            if c.name == "positive_suspected_under_report")
        ur = d01_evaluate(list(case.records))
        assert ur.l1_disposition == L1Disposition.POSITIVE

    def test_d02_fixture_still_evaluates_positive(self):
        from mm_r4.cm_fixtures import (
            build_cm_challenge_matrix, DOMAIN_ID as D02_DOMAIN_ID,
        )
        case = build_cm_challenge_matrix().by_number(1)
        exp, results = case.build()
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE]
        assert pos, "D02 prohibited-ingredient case must stay positive"
        for r in results:
            for cand in r.r2_candidates:
                assert cand.domain == D02_DOMAIN_ID

    def test_d03_units_never_collide_with_d01_d02_unit_ids(self):
        """D03 expected-set hashes and unit ids are domain-scoped and never
        duplicate D01/D02 unit ids for the same project."""
        from mm_r4.fixtures import build_challenge_matrix as d01_matrix
        from mm_r4.cm_fixtures import build_cm_challenge_matrix as d02_matrix
        d01_ids = set()
        for c in d01_matrix().cases:
            from mm_r4.fixtures import evaluate as _eval
            ur = _eval(list(c.records))
            d01_ids.add(ur.unit_id)
        from mm_r4.cm_fixtures import make_strategy as cm_strategy
        d02_ids = set()
        for number in (1, 2, 3):
            exp, _ = d02_matrix().by_number(number).build()
            for eu in exp.units:
                d02_ids.add(eu.build_unit(PROJECT_ID, cm_strategy()).unit_id)
        d03_ids = set()
        for number in (1, 5, 9, 11, 24, 49):
            exp, _ = build_ip_challenge_matrix().by_number(number).build()
            for eu in exp.units:
                d03_ids.add(eu.build_unit(PROJECT_ID).unit_id)
        assert not (d03_ids & d01_ids), "D03 unit ids must not collide with D01"
        assert not (d03_ids & d02_ids), "D03 unit ids must not collide with D02"
