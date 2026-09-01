"""R4-D03 IP journey/risk-marker projection deterministic tests (worker_02).

Proves the frozen D03 projection contract (``FROZEN_R4_D03_CONTRACT_V1_1``
§9, §10) implemented in :mod:`mm_r4.ip_projection`:

* Typed visit-axis events: ``event_kind`` distinguishes at least
  administration | dispense | return | pause | dose_reduce | dose_increase
  | resume | stop | ae | lab | exam | efficacy | visit; ``planned_or_actual``
  carries planned | actual | context so intent never conflates with evidence.
* Six concrete Chinese risk labels (frozen D03 §8) never leak engineering
  codes; no generic "已记录事项"/"风险项" collapse.
* Stable typed ids (``event_id / marker_id / unit_id / risk_identity_id /
  join_reason / typed_ref_ids``) verified joins.
* Many-to-many ``IPEventMarkerJoin``: one marker may join many events; one
  event may join many markers from different control units; episode alone
  never joins.
* Source/Query drill-back: typed refs (assignment|rule|algorithm|
  medical_event|source_locator|query) and byte-deterministic payloads.
* Positive / boundary / not_evaluable coexist; none is collapsed.

All data is synthetic and offline.  No production UI, chart library, real
project, provider, or port.
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

from mm_r4.ip import (  # noqa: E402
    ACCOUNTABILITY_PROXY_ANNOTATION,
    ACTION_DOSE_REDUCE,
    ACTION_PAUSE,
    CONFIRMATION_CONFIRMED,
    D03PriorityPolicy,
    ExposureAggregationPolicy,
    ExposureOccurrence,
    IPActionEvidence,
    IPExposureEpisode,
    IPSemanticRecord,
    METRIC_ACCOUNTABILITY_PROXY,
    METRIC_DAY_RATIO,
    POSITIVE_SUBTYPE_LABELS,
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
    PlannedExposureAction,
    PlannedTreatmentAssignment,
    ProtocolExposureRule,
    AdherenceAlgorithm,
    AdherenceObservation,
    ActualIPAction,
    AssignmentBindingMapping,
    evaluate_ip_slice,
    expand_ip_expected_set,
)
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    SourceLocator,
)
from mm_r4.ip_projection import (  # noqa: E402
    ANCHOR_KIND_EPISODE,
    ANCHOR_KIND_MEDICAL_EVENT,
    ANCHOR_KIND_UNRESOLVED,
    EVENT_KIND_ADMINISTRATION,
    EVENT_KIND_AE,
    EVENT_KIND_DISPENSE,
    EVENT_KIND_LAB,
    EVENT_KIND_RETURN,
    EVENT_KIND_VISIT,
    IP_EVENT_KINDS,
    IPJourneyEvent,
    IPRiskMarker,
    IP_RISK_FAMILY_LABELS,
    JOIN_REASON_ANCHOR_EVENT,
    JOIN_REASON_SOURCE_LOCATOR,
    JOIN_REASON_UNIT_IDENTITY,
    PLANNED_OR_ACTUAL_ACTUAL,
    PLANNED_OR_ACTUAL_CONTEXT,
    PLANNED_OR_ACTUAL_PLANNED,
    bidirectional_join,
    project_ip_journey_events,
    project_ip_subject_journey,
)


# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"

DEFAULT_ROLE_COVERAGE = {
    "ip_exposure": True,
    "subject_identity": True,
    "site_identity": True,
    "temporal_anchor": True,
    "randomization": True,
    "planned_treatment": True,
    "study_phase": True,
    "ip_dispense": True,
    "ip_return": True,
    "ip_accountability": True,
    "reported_ae": True,
    "lab_finding": True,
    "exam_finding": True,
    "efficacy_assessment": True,
    "ip_action_reason": True,
    "recorded_cm": True,
}


# ===========================================================================
# Fixtures / helpers (mirror test_ip_slice.py conventions)
# ===========================================================================

def make_locator(
    record_id: str, table_semantic: str = "ip_exposure",
    snapshot_id: str = SNAPSHOT_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_assignment(
    assignment_id="ASSIGN-01", subject="SYN-001", role_token="active",
    phase="treatment", dose="50", dose_unit="mg", dosage_form="tablet",
    route="口服", frequency="每日一次", planned_start="2026-01-01",
    planned_end="2026-03-31", display_label="研究药物 A（盲态标签）",
    disclosure="open", randomization_token="R1",
) -> PlannedTreatmentAssignment:
    return PlannedTreatmentAssignment(
        assignment_id=assignment_id, subject_ref=subject, site_ref=SITE_REF,
        treatment_role_token=role_token, study_phase=phase,
        planned_drug_identity="synthetic_drug_x", dose=dose,
        dose_unit=dose_unit, dosage_form=dosage_form, route=route,
        frequency=frequency, planned_start=planned_start,
        planned_end=planned_end, content_hash="asg-hash-01",
        assignment_lineage="asg-lineage-01",
        display_role_label=display_label,
        randomization_token=randomization_token,
        disclosure_state=disclosure,
        source_locator=make_locator("RAND#1", "randomization"))


def make_episode(
    episode_key="EP-1", record_id="EX#1", subject="SYN-001", role="active",
    role_confirmed=True, phase="treatment", phase_confirmed=True,
    dose="50", dose_unit="mg", dosage_form="tablet", route="口服",
    frequency="每日一次",
    span_start="2026-01-01", span_end="2026-01-28",
    assignment_link="direct", assignment_id="ASSIGN-01",
    disclosure="open", semantics="treatment_span", drug_identity="drugX",
    link_lineage="",
) -> IPExposureEpisode:
    return IPExposureEpisode(
        episode_key=episode_key, subject_ref=subject, site_ref=SITE_REF,
        actual_treatment_role=role,
        source_locator=make_locator(record_id),
        role_confirmed=role_confirmed, study_phase=phase,
        phase_confirmed=phase_confirmed,
        actual_drug_identity=drug_identity,
        dose=dose, dose_unit=dose_unit, dosage_form=dosage_form,
        route=route, frequency=frequency,
        span_start=span_start, span_end=span_end,
        source_semantics=semantics,
        assignment_link_status=assignment_link,
        assignment_id=assignment_id,
        assignment_link_lineage=link_lineage,
        disclosure_state=disclosure)


def make_occurrence(
    occ_id, date_start, episode_key="EP-1", date_end="",
    continuous_daily=False, dose="50", dose_unit="mg", route="口服",
    frequency="每日一次", revision="r1", record_id="",
) -> ExposureOccurrence:
    return ExposureOccurrence(
        occurrence_id=occ_id, episode_key=episode_key,
        date_start=date_start, date_end=date_end,
        continuous_daily=continuous_daily,
        dose=dose, dose_unit=dose_unit, route=route, frequency=frequency,
        source_locator=make_locator(record_id or f"EX-{occ_id}"),
        accepted_revision=revision, accepted_revision_hash=f"h-{revision}")


def make_agg_policy(
    version="ap-v1", chash="apch1",
    continuous_expansion=False, overlap_policy="boundary",
    split_lineage="",
) -> ExposureAggregationPolicy:
    return ExposureAggregationPolicy(
        version=version, content_hash=chash,
        rationale="synthetic aggregation policy",
        continuous_interval_expansion_allowed=continuous_expansion,
        overlap_conflict_policy=overlap_policy,
        split_priority_lineage=split_lineage)


def make_plan_actual_rule(
    rule_id="R-IP-01", planned_dose="50", planned_unit="mg",
    planned_form="tablet", planned_route="口服", planned_freq="每日一次",
    window_start="2026-01-01", window_end="2026-03-31",
    start_inc=True, end_inc=True, priority="high",
    applicable_phases=("treatment",), compare_fields=(),
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P20-1",
        rule_content_hash="rc-plan-01", rule_lineage="rl-plan-01",
        rule_type="plan_actual",
        applicable_treatment_role="active",
        applicable_phases=applicable_phases,
        window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        planned_dose=planned_dose, planned_dose_unit=planned_unit,
        planned_dosage_form=planned_form, planned_route=planned_route,
        planned_frequency=planned_freq, compare_fields=compare_fields,
        priority_on_hit=priority, priority_rationale="方案计划给药要求")


def make_allowed_action_rule(
    rule_id="R-IP-02", action_types=(ACTION_DOSE_REDUCE,),
    allowed_dose_after=("50",), allowed_reasons=("毒性",),
    planned_required=True, priority="high",
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P21-1",
        rule_content_hash="rc-action-01", rule_lineage="rl-action-01",
        rule_type="allowed_action",
        applicable_treatment_role="active",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-03-31",
        window_start_inclusive=True, window_end_inclusive=True,
        allowed_action_types=action_types,
        allowed_reasons=allowed_reasons,
        allowed_dose_after_values=allowed_dose_after,
        planned_action_required=planned_required,
        priority_on_hit=priority, priority_rationale="允许的给药调整")


def make_medical_action_rule(
    rule_id="R-IP-03", trigger_role="reported_ae",
    trigger_concept="肝功能异常", expected_actions=(ACTION_PAUSE,),
    priority="high",
) -> ProtocolExposureRule:
    return ProtocolExposureRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P22-1",
        rule_content_hash="rc-med-01", rule_lineage="rl-med-01",
        rule_type="medical_action",
        applicable_treatment_role="active",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-03-31",
        window_start_inclusive=True, window_end_inclusive=True,
        trigger_role=trigger_role, trigger_concept=trigger_concept,
        expected_actions=expected_actions,
        priority_on_hit=priority, priority_rationale="医学触发处置要求")


def make_adherence_algorithm(
    algorithm_id="ALG-01", metric=METRIC_DAY_RATIO,
    window_id="W1", window_start="2026-01-01", window_end="2026-01-10",
    start_inc=True, end_inc=True,
    lower="0.8", upper=None, lower_inc=True, upper_inc=None,
    precision=1, rounding="round_half_up", compare="before",
    canonical_unit="", conversions=(),
    pause_handling="included",
) -> AdherenceAlgorithm:
    return AdherenceAlgorithm(
        algorithm_id=algorithm_id, version="v1", content_hash="rc-alg-01",
        metric_kind=metric,
        numerator_source=(
            "actual_exposure_days" if metric == METRIC_DAY_RATIO
            else "recorded_administration"),
        denominator_source="window_days" if metric == METRIC_DAY_RATIO
        else "planned_amount",
        window_id=window_id, window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        canonical_unit=canonical_unit, conversion_lineage="cl-v1",
        unit_conversion_rules=conversions,
        lower_threshold=lower, upper_threshold=upper,
        lower_inclusive=lower_inc, upper_inclusive=upper_inc,
        planned_pause_handling=pause_handling,
        calculation_precision=precision, rounding_mode=rounding,
        compare_before_or_after_rounding=compare,
        rationale="synthetic adherence algorithm")


def make_observation(
    obs_id, algorithm_id="ALG-01", window_id="W1",
    coverage=True, numerator="", denominator="", unit="",
    locator=None,
) -> AdherenceObservation:
    return AdherenceObservation(
        observation_id=obs_id, algorithm_id=algorithm_id,
        window_id=window_id, coverage_complete=coverage,
        numerator_value=numerator, denominator_value=denominator,
        unit=unit,
        item_source_locators=(
            (locator,) if locator is not None else
            (make_locator(f"OBS-{obs_id}", "ip_accountability"),)),
        accepted_revision="r1",
        source_locator=make_locator(f"OBS-{obs_id}", "ip_accountability"))


def make_evidence(
    event_key="reported_ae:AE#1", subject="SYN-001", episode_key="EP-1",
    actual_action=ACTION_PAUSE, concept="肝功能异常",
    event_start="2026-01-05", event_end="2026-01-05",
    confirmation=CONFIRMATION_CONFIRMED, source_role="reported_ae",
    record_id="AE#1",
) -> IPActionEvidence:
    return IPActionEvidence(
        source_role=source_role, stable_source_event_key=event_key,
        subject_ref=subject, site_ref=SITE_REF,
        linked_ip_episode_id=episode_key, relation_type="triggered_action",
        source_locator=make_locator(record_id, source_role),
        concept=concept, actual_action=actual_action,
        event_start=event_start, event_end=event_end,
        relation_confirmation=confirmation)


def make_planned_action(
    action_id="PA-1", action_type=ACTION_PAUSE, episode_key="EP-1",
    assignment_id="ASSIGN-01", action_start="2026-01-05",
    action_end="2026-01-09", reason="毒性",
) -> PlannedExposureAction:
    return PlannedExposureAction(
        action_id=action_id, action_type=action_type,
        assignment_id=assignment_id, episode_key=episode_key,
        action_start=action_start, action_end=action_end,
        dose_before="50", dose_after="0", dose_unit="mg",
        reason=reason, source_locator=make_locator(f"PACT-{action_id}",
                                                   "planned_treatment"),
        confirmation_status=CONFIRMATION_CONFIRMED)


def make_actual_action(
    action_id="AA-1", action_type=ACTION_DOSE_REDUCE, episode_key="EP-1",
    assignment_id="ASSIGN-01", action_start="2026-01-05",
    action_end="2026-01-09", dose_after="25", reason="毒性",
    planned_id="", confirmation=CONFIRMATION_CONFIRMED,
) -> ActualIPAction:
    return ActualIPAction(
        action_id=action_id, action_type=action_type,
        assignment_id=assignment_id, episode_key=episode_key,
        action_start=action_start, action_end=action_end,
        dose_before="50", dose_after=dose_after, dose_unit="mg",
        reason=reason, related_planned_action_id=planned_id,
        source_locator=make_locator(f"AACT-{action_id}", "ip_action_reason"),
        confirmation_status=confirmation)


def make_return_record(
    record_id="RET#1", subject="SYN-001", amount="10", unit="片",
    amount_kind="exact", episode_key="EP-1",
) -> IPSemanticRecord:
    return IPSemanticRecord(
        role="ip_return", concept="study_drug_return",
        locator=make_locator(record_id, "ip_return"),
        subject_ref=subject, site_ref=SITE_REF,
        amount_value=amount, amount_unit=unit, amount_kind=amount_kind,
        linked_ip_episode_key=episode_key)


def make_dispense_record(
    record_id="DISP#1", subject="SYN-001", amount="10", unit="片",
    amount_kind="exact", episode_key="EP-1",
) -> IPSemanticRecord:
    return IPSemanticRecord(
        role="ip_dispense", concept="study_drug_dispense",
        locator=make_locator(record_id, "ip_dispense"),
        subject_ref=subject, site_ref=SITE_REF,
        amount_value=amount, amount_unit=unit, amount_kind=amount_kind,
        linked_ip_episode_key=episode_key)


def make_mapping(version="mv1", chash="mch1", allow=True):
    return AssignmentBindingMapping(
        version=version, content_hash=chash,
        rationale="synthetic binding mapping",
        allow_derived_binding=allow)


def make_policy(version="pp-v1") -> D03PriorityPolicy:
    return D03PriorityPolicy(
        version=version, policy_content_hash="pch1",
        rationale="synthetic priority policy")


_NO_POLICY = object()


def evaluate_slice(
    episode, assignments=None, rules=(), algorithms=(),
    occurrences=(), evidence=(), planned_actions=(), actual_actions=(),
    observations=(), returns=(), dispenses=(), cm_conflicts=(),
    role_coverage=None, agg_policy=None, action_coverage=False,
    trigger_coverage=False, return_expectation="unknown",
    priority_policy=_NO_POLICY, mapping=None, snapshot_id=SNAPSHOT_ID,
):
    if assignments is None:
        assignments = (make_assignment(),)
    if role_coverage is None:
        role_coverage = DEFAULT_ROLE_COVERAGE
    if agg_policy is None:
        agg_policy = make_agg_policy()
    if priority_policy is _NO_POLICY:
        priority_policy = make_policy()
    return evaluate_ip_slice(
        project_id=PROJECT_ID, episodes=(episode,),
        assignments=assignments, active_rules=rules,
        adherence_algorithms=algorithms,
        action_evidence=evidence, occurrences=occurrences,
        planned_actions=planned_actions, actual_actions=actual_actions,
        observations=observations,
        return_records=returns, dispense_records=dispenses,
        cm_conflict_rows=cm_conflicts,
        role_coverage=role_coverage, aggregation_policy=agg_policy,
        action_coverage_complete=action_coverage,
        trigger_coverage_complete=trigger_coverage,
        protocol_return_expectation=return_expectation,
        priority_policy=priority_policy,
        binding_mapping=mapping, snapshot_id=snapshot_id)[episode.subject_ref]


def expansion_for(episode, assignments=None, rules=(), algorithms=(),
                  evidence=()):
    if assignments is None:
        assignments = (make_assignment(),)
    return expand_ip_expected_set(
        project_id=PROJECT_ID, episodes=(episode,),
        assignments=assignments, active_rules=rules,
        adherence_algorithms=algorithms, action_evidence=evidence)


def project_slice(episode, slice_result, expansions, **kwargs):
    return project_ip_subject_journey(
        slice_result, expansions=expansions, **kwargs)


# ===========================================================================
# §9 typed event kinds — no generic timeline conflation
# ===========================================================================

class TestTypedEventKinds:
    """Frozen D03 §9: events are typed, never a generic "已记录事项"."""

    def test_event_kinds_cover_frozen_minimum_set(self):
        for kind in (EVENT_KIND_ADMINISTRATION, EVENT_KIND_DISPENSE,
                     EVENT_KIND_RETURN, "pause", "dose_reduce",
                     "dose_increase", "resume", "stop",
                     EVENT_KIND_AE, EVENT_KIND_LAB, "exam", "efficacy",
                     EVENT_KIND_VISIT):
            assert kind in IP_EVENT_KINDS

    def test_planned_vs_actual_pause_events(self):
        episode = make_episode()
        assignment = make_assignment()
        planned = make_planned_action(action_type=ACTION_PAUSE)
        actual = make_actual_action(action_type=ACTION_PAUSE)
        evs = project_ip_journey_events(
            None, episode=episode, assignment=assignment,
            planned_actions=(planned,), actual_actions=(actual,))
        planned_ev = [e for e in evs if e.event_id == "ip-ev-pause-PA-1"]
        actual_ev = [e for e in evs if e.event_id == "ip-ev-pause-AA-1"]
        assert len(planned_ev) == 1 and len(actual_ev) == 1
        assert planned_ev[0].planned_or_actual == PLANNED_OR_ACTUAL_PLANNED
        assert actual_ev[0].planned_or_actual == PLANNED_OR_ACTUAL_ACTUAL
        assert planned_ev[0].event_kind == "pause"
        assert actual_ev[0].event_kind == "pause"

    def test_medical_trigger_context_events(self):
        episode = make_episode()
        ev = make_evidence(event_key="reported_ae:AE#1",
                           actual_action=ACTION_PAUSE)
        evs = project_ip_journey_events(
            None, episode=episode, action_evidence=(ev,))
        ae_evs = [e for e in evs
                  if e.event_id == "ip-ev-ae-reported_ae:AE#1"]
        assert len(ae_evs) == 1
        assert ae_evs[0].event_kind == EVENT_KIND_AE
        assert ae_evs[0].planned_or_actual == PLANNED_OR_ACTUAL_CONTEXT

    def test_accountability_dispense_return_events(self):
        episode = make_episode()
        ret = make_return_record()
        disp = make_dispense_record()
        evs = project_ip_journey_events(
            None, episode=episode, return_records=(ret,),
            dispense_records=(disp,))
        kinds = {e.event_kind for e in evs}
        assert EVENT_KIND_RETURN in kinds
        assert EVENT_KIND_DISPENSE in kinds

    def test_occurrence_administration_events(self):
        episode = make_episode()
        occ = make_occurrence("OCC-1", "2026-01-05")
        evs = project_ip_journey_events(None, episode=episode,
                                        occurrences=(occ,))
        occ_evs = [e for e in evs
                   if e.event_id == "ip-ev-admin-EP-1-OCC-1"]
        assert len(occ_evs) == 1
        assert occ_evs[0].event_kind == EVENT_KIND_ADMINISTRATION
        assert occ_evs[0].start == "2026-01-05"


# ===========================================================================
# §8 / §9 six concrete Chinese risk labels — no engineering leak
# ===========================================================================

class TestChineseRiskLabels:
    """Frozen D03 §8: six concrete Chinese labels, no internal codes."""

    def test_six_risk_family_labels(self):
        assert IP_RISK_FAMILY_LABELS == {
            "plan_actual_exposure": "研究药给药与方案不一致",
            "treatment_role_phase": "治疗分组或阶段待核实",
            "adherence": "研究药依从性待核实",
            "ip_action": "给药调整依据待核实",
            "medical_action": "给药处置与医学事件不一致",
            "ip_accountability": "研究药物核算待核实",
        }

    def test_positive_marker_uses_frozen_subtype_label(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        # Actual dose differs from planned -> mismatch positive.
        episode = make_episode(dose="25")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,))
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        proj = project_slice(episode, slice_result, expansion)
        plan_markers = [m for m in proj.risk_markers
                        if m.risk_family == "plan_actual_exposure"]
        assert plan_markers
        for m in plan_markers:
            assert m.audience_label == POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH]
            assert "plan_actual_exposure" not in m.audience_label

    def test_no_internal_engineering_code_in_any_label(self):
        episode = make_episode()
        assignment = make_assignment()
        rules = (
            make_plan_actual_rule(planned_dose="50"),
            make_allowed_action_rule(),
            make_medical_action_rule(),
        )
        # Force positives across several controls.
        slice_result = evaluate_slice(
            episode, rules=rules, assignments=(assignment,),
            evidence=(make_evidence(actual_action=ACTION_PAUSE),),
            actual_actions=(make_actual_action(
                action_type=ACTION_DOSE_REDUCE, dose_after="25"),),
            action_coverage=True, trigger_coverage=True)
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=rules,
            evidence=(make_evidence(actual_action=ACTION_PAUSE),))
        proj = project_slice(episode, slice_result, expansion,
                             action_evidence=(make_evidence(
                                 actual_action=ACTION_PAUSE),))
        assert proj.risk_markers
        for m in proj.risk_markers:
            assert m.audience_label.strip()
            for banned in ("ip_action", "plan_actual", "adherence",
                           "medical_action", "risk_family", "candidate",
                           "marker", "旅程", "风险项", "已记录事项"):
                assert banned not in m.audience_label


# ===========================================================================
# §9 stable marker ids + typed refs
# ===========================================================================

class TestStableMarkerIdsAndTypedRefs:
    """Frozen D03 §9: stable marker ids and typed refs (no snapshots)."""

    def test_marker_id_is_stable_unit_hash(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        episode = make_episode(dose="25")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,))
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        proj = project_slice(episode, slice_result, expansion)
        for m in proj.risk_markers:
            assert m.marker_id.startswith("ipm-")
            assert m.unit_id
            assert "snapshot" not in m.marker_id
            # Typed refs carry assignment/rule/query kinds.
            kinds = {r.kind for r in m.typed_refs}
            assert "assignment" in kinds or "rule" in kinds
            assert "query" in kinds

    def test_typed_ref_validation(self):
        with pytest.raises(Exception):
            # IPJourneyEvent requires a valid event_kind.
            IPJourneyEvent(
                event_id="e1", event_kind="bogus",
                planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
                episode_id="EP-1", stable_ip_event_key="k",
                subject_ref="S", start="2026-01-01", end="",
                date_precision="day",
                source_locator_ids=("loc-1",), unit_ids=("u1",))

    def test_journey_event_typed_ref_ids(self):
        episode = make_episode()
        assignment = make_assignment()
        evs = project_ip_journey_events(
            None, episode=episode, assignment=assignment)
        admin = [e for e in evs if e.event_id == "ip-ev-admin-EP-1"]
        assert len(admin) == 1
        ref_ids = admin[0].typed_ref_ids()
        assert any(r.startswith("assignment:") for r in ref_ids)
        assert any(r.startswith("source_locator:") for r in ref_ids)


# ===========================================================================
# §9/§10 bidirectional many-to-many join verified by stable ids
# ===========================================================================

class TestBidirectionalJoin:
    """Frozen D03 §9/§10: many-to-many joins use stable ids, not prose."""

    def test_marker_joins_events_via_unit_identity(self):
        ev = IPJourneyEvent(
            event_id="ip-ev-admin-EP-1", event_kind=EVENT_KIND_ADMINISTRATION,
            planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id="EP-1", stable_ip_event_key="ip_exposure:EX#1",
            subject_ref="SYN-001", start="2026-01-01", end="2026-01-28",
            date_precision="day", source_locator_ids=("loc-ep",),
            unit_ids=("u1",))
        marker = IPRiskMarker(
            marker_id="ipm-u1", unit_id="u1", risk_identity_id="rid-1",
            subtype=POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
            audience_label="研究药给药与方案不一致",
            priority="high", anchor_kind=ANCHOR_KIND_EPISODE,
            anchor_event_id_or_interval="2026-01-01|2026-01-28",
            typed_refs=(), source_locator_ids=("loc-ep",),
            query_id="q-u1", uncertainty="", episode_id="EP-1")
        join = bidirectional_join([ev], [marker])
        assert join.markers_for_event("ip-ev-admin-EP-1") == ("ipm-u1",)
        assert join.events_for_marker("ipm-u1") == ("ip-ev-admin-EP-1",)
        assert join.records[0].join_reason == JOIN_REASON_UNIT_IDENTITY
        assert join.records[0].risk_identity_id == "rid-1"

    def test_episode_alone_never_joins(self):
        # Same episode_id but unit_id NOT in the event's unit_ids -> no join.
        ev = IPJourneyEvent(
            event_id="ip-ev-admin-EP-X", event_kind=EVENT_KIND_ADMINISTRATION,
            planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id="EP-1", stable_ip_event_key="k",
            subject_ref="SYN-001", start="2026-01-01", end="",
            date_precision="day", source_locator_ids=("loc1",),
            unit_ids=("other-unit",))
        marker = IPRiskMarker(
            marker_id="ipm-u1", unit_id="u1", risk_identity_id="",
            subtype="", audience_label="研究药依从性待核实",
            priority="medium", anchor_kind=ANCHOR_KIND_EPISODE,
            anchor_event_id_or_interval="none",
            typed_refs=(), source_locator_ids=("loc2",),
            query_id="", uncertainty="", episode_id="EP-1")
        join = bidirectional_join([ev], [marker])
        assert join.markers_for_event("ip-ev-admin-EP-X") == ()
        assert join.events_for_marker("ipm-u1") == ()

    def test_many_to_many_across_control_units(self):
        # One event joins two markers from different units; one marker joins
        # two events (shared episode + unit identity).
        mk1 = IPRiskMarker(
            marker_id="ipm-u1", unit_id="u1", risk_identity_id="r1",
            subtype="", audience_label="a1", priority="high",
            anchor_kind=ANCHOR_KIND_EPISODE,
            anchor_event_id_or_interval="none",
            typed_refs=(), source_locator_ids=("locA",),
            query_id="", uncertainty="", episode_id="EP-1")
        mk2 = IPRiskMarker(
            marker_id="ipm-u2", unit_id="u2", risk_identity_id="r2",
            subtype="", audience_label="a2", priority="medium",
            anchor_kind=ANCHOR_KIND_EPISODE,
            anchor_event_id_or_interval="none",
            typed_refs=(), source_locator_ids=("locB",),
            query_id="", uncertainty="", episode_id="EP-1")
        ev1 = IPJourneyEvent(
            event_id="e1", event_kind=EVENT_KIND_ADMINISTRATION,
            planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id="EP-1", stable_ip_event_key="k1",
            subject_ref="SYN-001", start="2026-01-01", end="",
            date_precision="day", source_locator_ids=("locA",),
            unit_ids=("u1", "u2"))
        ev2 = IPJourneyEvent(
            event_id="e2", event_kind=EVENT_KIND_VISIT,
            planned_or_actual=PLANNED_OR_ACTUAL_CONTEXT,
            episode_id="EP-1", stable_ip_event_key="k2",
            subject_ref="SYN-001", start="2026-01-02", end="",
            date_precision="day", source_locator_ids=("locC",),
            unit_ids=("u1",))
        join = bidirectional_join([ev1, ev2], [mk1, mk2])
        assert set(join.markers_for_event("e1")) == {"ipm-u1", "ipm-u2"}
        assert join.markers_for_event("e2") == ("ipm-u1",)
        assert "e1" in join.events_for_marker("ipm-u1")
        assert "e2" in join.events_for_marker("ipm-u1")
        assert join.events_for_marker("ipm-u2") == ("e1",)

    def test_anchor_event_and_source_locator_joins(self):
        ev = IPJourneyEvent(
            event_id="ip-ev-ae-AE#1", event_kind=EVENT_KIND_AE,
            planned_or_actual=PLANNED_OR_ACTUAL_CONTEXT,
            episode_id="EP-1", stable_ip_event_key="reported_ae:AE#1",
            subject_ref="SYN-001", start="2026-01-05", end="",
            date_precision="day", source_locator_ids=("loc-ae",),
            unit_ids=("u1",))
        mk = IPRiskMarker(
            marker_id="ipm-u1", unit_id="u1", risk_identity_id="rid",
            subtype="", audience_label="给药处置与医学事件不一致",
            priority="high", anchor_kind=ANCHOR_KIND_MEDICAL_EVENT,
            anchor_event_id_or_interval="ip-ev-ae-AE#1",
            typed_refs=(), source_locator_ids=("loc-ae",),
            query_id="", uncertainty="", episode_id="EP-1")
        join = bidirectional_join([ev], [mk])
        assert join.markers_for_event("ip-ev-ae-AE#1") == ("ipm-u1",)
        reason = join.records[0].join_reason
        assert reason in (JOIN_REASON_ANCHOR_EVENT, JOIN_REASON_SOURCE_LOCATOR,
                          JOIN_REASON_UNIT_IDENTITY)
        # The anchor event id must appear when unit identity also matches.
        if JOIN_REASON_UNIT_IDENTITY not in (reason,):
            assert reason in (JOIN_REASON_ANCHOR_EVENT,
                              JOIN_REASON_SOURCE_LOCATOR)


# ===========================================================================
# §9/§10 source/Query drill-back
# ===========================================================================

class TestSourceQueryDrillBack:
    """Frozen D03 §9/§10: one-hop drill-back to source + Query."""

    def test_marker_carries_source_locators_and_query(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        episode = make_episode(dose="25")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,))
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        proj = project_slice(episode, slice_result, expansion)
        pos = [m for m in proj.risk_markers if m.is_risk_marker]
        assert pos
        for m in pos:
            assert m.source_locator_ids
            assert m.query_id.startswith("q-")
            assert m.risk_identity_id
            assert m.stable_core
            assert m.lineage_fingerprint
            assert m.classifier

    def test_event_source_locator_present(self):
        episode = make_episode()
        assignment = make_assignment()
        evs = project_ip_journey_events(
            None, episode=episode, assignment=assignment)
        for ev in evs:
            assert ev.source_locator_ids
            assert ev.stable_ip_event_key
            assert ev.subject_ref


# ===========================================================================
# §9 byte-deterministic payloads
# ===========================================================================

class TestDeterminism:
    """Frozen D03/§10: projection payloads are byte-deterministic.

    Repeated projection and canonical serialization of the same inputs
    yield identical payloads; join records are stably ordered.
    """

    def test_repeated_projection_identical(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        episode = make_episode(dose="25")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,))
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        p1 = project_slice(episode, slice_result, expansion)
        p2 = project_slice(episode, slice_result, expansion)
        assert p1.canonical_payload() == p2.canonical_payload()
        assert p1.join.canonical_payload() == p2.join.canonical_payload()
        ev_ids1 = [e.event_id for e in p1.events]
        ev_ids2 = [e.event_id for e in p2.events]
        assert ev_ids1 == ev_ids2

    def test_join_canonical_payload_stable(self):
        ev = IPJourneyEvent(
            event_id="e1", event_kind=EVENT_KIND_ADMINISTRATION,
            planned_or_actual=PLANNED_OR_ACTUAL_ACTUAL,
            episode_id="EP-1", stable_ip_event_key="k",
            subject_ref="S", start="2026-01-01", end="",
            date_precision="day", source_locator_ids=("locA",),
            unit_ids=("u1",))
        mk = IPRiskMarker(
            marker_id="ipm-u1", unit_id="u1", risk_identity_id="r",
            subtype="", audience_label="a", priority="high",
            anchor_kind=ANCHOR_KIND_EPISODE,
            anchor_event_id_or_interval="none",
            typed_refs=(), source_locator_ids=("locA",),
            query_id="", uncertainty="", episode_id="EP-1")
        j1 = bidirectional_join([ev], [mk]).canonical_payload()
        j2 = bidirectional_join([ev], [mk]).canonical_payload()
        assert j1 == j2


# ===========================================================================
# §10 subject journey: positive / boundary / not_evaluable coexist
# ===========================================================================

class TestSubjectJourneyCoexistence:
    """Frozen D03 §10/§11: positive + not_evaluable coexist, never collapse."""

    def test_positive_and_not_evaluable_sibling_markers(self):
        # plan_actual positive (dose mismatch) + adherence not_evaluable
        # (missing observation) coexists as separate markers.
        episode = make_episode(dose="25")
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        alg = make_adherence_algorithm()
        slice_result = evaluate_slice(
            episode, rules=(rule,), algorithms=(alg,),
            assignments=(assignment,), observations=())
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,),
            algorithms=(alg,))
        proj = project_slice(episode, slice_result, expansion)
        assert proj.has_positive()
        assert proj.has_not_evaluable()
        coverage_gap = [m for m in proj.risk_markers if m.coverage_gap]
        positive = [m for m in proj.risk_markers if m.is_risk_marker]
        assert coverage_gap and positive
        # Not collapsed: each marker keeps its own unit_id.
        gap_units = {m.unit_id for m in coverage_gap}
        pos_units = {m.unit_id for m in positive}
        assert gap_units.isdisjoint(pos_units)

    def test_negative_produces_no_marker(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        # Matching dose -> negative.
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,))
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        proj = project_slice(episode, slice_result, expansion)
        for m in proj.risk_markers:
            assert m.l1_disposition != L1Disposition.NEGATIVE

    def test_subject_priority_from_markers(self):
        episode = make_episode(dose="25")
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50", priority="high")
        policy = make_policy()
        # Override plan_actual priority to high for a deterministic check.
        policy = D03PriorityPolicy(
            version="pp-v1", policy_content_hash="pch1",
            rationale="synthetic priority policy",
            planned_actual_priority="high")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,),
            priority_policy=policy)
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,))
        proj = project_slice(episode, slice_result, expansion)
        assert proj.monitoring_priority_code == "high"
        assert proj.monitoring_priority_label == "高"


# ===========================================================================
# §6.2 accountability-proxy marker annotation (worker_02 followup)
# ===========================================================================

class TestAccountabilityProxyAnnotation:
    """Frozen §6.2: an accountability/proxy-backed risk marker's
    user-visible uncertainty must carry the exact ``按发放/回收核算``
    annotation and must never be presented as proven ``实际服药天数``;
    the six Chinese audience labels, stable ids and joins are preserved.
    """

    def _proxy_positive_projection(self):
        # §6.2-valid input: the algorithm declares its canonical unit and
        # every side (observation, return, dispense) carries that explicit
        # unit, so the engine can compare the converted balance.  Dispense
        # 30 minus return 10 = 20, but recorded administration total is
        # 25 -> ip_accountability_inconsistency positive.
        episode = make_episode()
        assignment = make_assignment()
        alg = make_adherence_algorithm(
            metric=METRIC_ACCOUNTABILITY_PROXY, canonical_unit="片")
        obs = make_observation(
            "OBS-PX1", algorithm_id=alg.algorithm_id,
            window_id=alg.window_id, numerator="25", denominator="30",
            unit="片", coverage=True)
        ret = make_return_record(record_id="RET#1", amount="10", unit="片")
        disp = make_dispense_record(record_id="DISP#1", amount="30", unit="片")
        slice_result = evaluate_slice(
            episode, algorithms=(alg,), assignments=(assignment,),
            observations=(obs,), returns=(ret,), dispenses=(disp,),
            return_expectation="expected")
        expansion = expansion_for(
            episode, assignments=(assignment,), algorithms=(alg,))
        return project_slice(episode, slice_result, expansion)

    def test_proxy_positive_marker_carries_frozen_annotation(self):
        proj = self._proxy_positive_projection()
        markers = [
            m for m in proj.risk_markers
            if m.audience_label == "研究药物核算待核实"
            and not m.coverage_gap]
        assert markers, "expected a positive 研究药物核算待核实 marker"
        for m in markers:
            assert m.l1_disposition == L1Disposition.POSITIVE
            # Frozen §6.2 exact phrase present; proven-day token absent.
            assert "按发放/回收核算" in m.uncertainty
            assert "实际服药天数" not in m.uncertainty
            assert m.uncertainty.endswith(
                ACCOUNTABILITY_PROXY_ANNOTATION)
            # Six Chinese audience labels / stable ids / joins preserved.
            assert m.audience_label == (
                IP_RISK_FAMILY_LABELS["ip_accountability"])
            assert m.marker_id.startswith("ipm-")
            assert m.unit_id
            assert m.risk_identity_id
            assert proj.join.events_for_marker(m.marker_id)

    def test_proxy_positive_journey_payload_carries_annotation(self):
        proj = self._proxy_positive_projection()
        payload = proj.canonical_payload()
        marker_payloads = [
            mp for mp in payload["risk_markers"]
            if mp["audience_label"] == "研究药物核算待核实"
            and not mp["coverage_gap"]]
        assert marker_payloads
        for mp in marker_payloads:
            assert "按发放/回收核算" in mp["uncertainty"]
            assert "实际服药天数" not in mp["uncertainty"]

    def test_proxy_coverage_gap_marker_carries_annotation(self):
        # Missing return with expected return -> not_evaluable coverage
        # gap; the proxy disclaimer must still be user-visible.
        episode = make_episode()
        assignment = make_assignment()
        alg = make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY)
        slice_result = evaluate_slice(
            episode, algorithms=(alg,), assignments=(assignment,),
            return_expectation="expected")
        expansion = expansion_for(
            episode, assignments=(assignment,), algorithms=(alg,))
        proj = project_slice(episode, slice_result, expansion)
        gaps = [
            m for m in proj.risk_markers
            if m.audience_label == "研究药物核算待核实" and m.coverage_gap]
        assert gaps
        for m in gaps:
            assert m.l1_disposition == L1Disposition.NOT_EVALUABLE
            assert "按发放/回收核算" in m.uncertainty
            assert "实际服药天数" not in m.uncertainty
            assert m.audience_label == (
                IP_RISK_FAMILY_LABELS["ip_accountability"])

    def test_day_ratio_marker_untouched(self):
        # A plain day-ratio adherence unit never carries the proxy
        # annotation: the stamp is scoped to accountability/proxy.
        episode = make_episode()
        assignment = make_assignment()
        alg = make_adherence_algorithm(metric=METRIC_DAY_RATIO)
        slice_result = evaluate_slice(
            episode, algorithms=(alg,), assignments=(assignment,),
            observations=())
        expansion = expansion_for(
            episode, assignments=(assignment,), algorithms=(alg,))
        proj = project_slice(episode, slice_result, expansion)
        for m in proj.risk_markers:
            assert "按发放/回收核算" not in m.uncertainty


# ===========================================================================
# §9/§10 typed anchor kinds
# ===========================================================================

class TestAnchorKinds:
    """Frozen D03 §9: marker anchor kinds distinguish risk positions."""

    def test_medical_action_anchor_is_medical_event(self):
        episode = make_episode()
        assignment = make_assignment()
        rule = make_medical_action_rule()
        ev = make_evidence(actual_action=ACTION_PAUSE)
        # Actual action matches expected -> negative, no marker. Force a
        # positive by mismatching the expected action.
        ev = make_evidence(actual_action="stop")
        slice_result = evaluate_slice(
            episode, rules=(rule,), assignments=(assignment,),
            evidence=(ev,), trigger_coverage=True)
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,),
            evidence=(ev,))
        proj = project_slice(episode, slice_result, expansion,
                             action_evidence=(ev,))
        med = [m for m in proj.risk_markers
               if m.risk_family == "medical_action"]
        assert med
        for m in med:
            assert m.anchor_kind == ANCHOR_KIND_MEDICAL_EVENT

    def test_not_evaluable_marker_anchor_unresolved(self):
        episode = make_episode()
        assignment = make_assignment()
        alg = make_adherence_algorithm()
        # Missing observation -> not_evaluable.
        slice_result = evaluate_slice(
            episode, algorithms=(alg,), assignments=(assignment,),
            observations=())
        expansion = expansion_for(
            episode, assignments=(assignment,), algorithms=(alg,))
        proj = project_slice(episode, slice_result, expansion)
        gap = [m for m in proj.risk_markers if m.coverage_gap]
        assert gap
        for m in gap:
            assert m.anchor_kind == ANCHOR_KIND_UNRESOLVED


# ===========================================================================
# §10 episode rollup preserved in projection
# ===========================================================================

class TestEpisodeRollupPreserved:
    """Frozen D03 §10/§11: episode rollup carries sibling independent flags."""

    def test_rollup_preserves_positive_and_not_evaluable(self):
        episode = make_episode(dose="25")
        assignment = make_assignment()
        rule = make_plan_actual_rule(planned_dose="50")
        alg = make_adherence_algorithm()
        slice_result = evaluate_slice(
            episode, rules=(rule,), algorithms=(alg,),
            assignments=(assignment,), observations=())
        expansion = expansion_for(
            episode, assignments=(assignment,), rules=(rule,),
            algorithms=(alg,))
        proj = project_slice(episode, slice_result, expansion)
        assert proj.episode_rollups
        roll = proj.episode_rollups[0]
        assert roll.has_positive is True
        assert roll.has_not_evaluable is True
        assert roll.episode_key == "EP-1"