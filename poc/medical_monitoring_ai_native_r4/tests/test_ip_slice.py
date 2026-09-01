"""R4-D03 IP exposure slice deterministic tests (worker_01).

Proves the frozen D03 IP domain engine (``FROZEN_R4_D03_CONTRACT_V1_1``)
implements the mandatory contract with deterministic synthetic-only
assertions, covering the §11 minimum acceptance matrix for the engine:

* Versioned input dataclasses enforce their invariants (§3.2).
* Expected-set expansion follows the six control items per episode, with
  deterministic hashes (§4).
* Assignment/episode binding: direct link, derived unique, zero candidates
  (not_evaluable), two or more candidates (boundary), subject mismatch.
* Actual exposure days vs treatment span; sparse dosing; daily multi-dose
  counts a day once; continuous intervals expand only with explicit
  semantics + policy; same-role same-dose union; different-dose interval
  overlaps never silently merge; zero occurrences never imply missed dose.
* Six positive subtypes each with a corresponding negative.
* Boundary: threshold equality with unstated inclusivity, window endpoints,
  partial dates, ambiguous assignment, return partial/range values.
* not_evaluable: missing algorithm, zero denominator, unit conflict, role
  conflict, CM/IP mutual exclusion, missing occurrence rows.
* Adherence arithmetic: threshold equality, 79.95 rounding flip, zero
  denominator, duplicate observation, unit conversion, window endpoints,
  planned-pause denominator effect.
* Medical-trigger linkage: wrong subject/site/episode or unconfirmed
  relation never forms a positive/negative.
* Accountability §5.4 decision table: uncovered roles, zero rows, empty
  fields, explicit zero, partial values, not-applicable windows.
* Blinding: role/phase verifiable without identity; masked dose makes the
  dose-dependent control not_evaluable; no unapproved identity leaks into
  Query/Journey text.
* Query: three-part Chinese text, versioned basis, user Chinese labels,
  no confirmed-PD language; unit join provenance.
* Identity: stable classifier, versioned scope/lineage, supersede on rule
  version change.
* Ledger: RiskDomainUnitResult protocol, UnitEvaluation materialization,
  sibling positive + not_evaluable rollup coexistence.

All data is synthetic and offline.  No real project, provider, or port.
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
    ACTION_DOSE_REDUCE,
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_STOP,
    CONFIRMATION_CONFIRMED,
    CONFIRMATION_UNRESOLVED,
    D03_DOMAIN,
    D03PriorityPolicy,
    ExposureAggregationPolicy,
    ExposureOccurrence,
    IPActionEvidence,
    IPExposureEpisode,
    IPSemanticRecord,
    IPSliceError,
    IPUnitExpanded,
    METRIC_ACCOUNTABILITY_PROXY,
    METRIC_AMOUNT_RATIO,
    METRIC_DAY_RATIO,
    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
    POSITIVE_SUBTYPE_LABELS,
    POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
    PlannedExposureAction,
    PlannedTreatmentAssignment,
    ProtocolExposureRule,
    AdherenceAlgorithm,
    AdherenceObservation,
    ActualIPAction,
    AssignmentBindingMapping,
    AssignmentResolution,
    compute_actual_exposure_days,
    evaluate_ip_slice,
    evaluate_ip_unit,
    expand_ip_expected_set,
    resolve_episode_assignment,
)
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    RiskDomainUnitResult,
    SourceLocator,
    UnitEvaluation,
    UnitJoinError,
)
from mm_r2.identity import make_risk_identity  # noqa: E402


# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"

#: Default role coverage: every semantic role covered.  Tests that probe
#: coverage gaps override this.
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
# Fixtures / helpers
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


def evaluate_one(
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
    expansion = expand_ip_expected_set(
        project_id=PROJECT_ID, episodes=(episode,),
        assignments=assignments, active_rules=rules,
        adherence_algorithms=algorithms,
        action_evidence=evidence, binding_mapping=mapping)
    assert expansion.count > 0, "expected at least one expanded unit"
    results = []
    for eu in expansion.units:
        r = evaluate_ip_unit(
            project_id=PROJECT_ID, expanded=eu,
            occurrences=occurrences, action_evidence=evidence,
            planned_actions=planned_actions, actual_actions=actual_actions,
            observations=observations,
            return_records=returns, dispense_records=dispenses,
            cm_conflict_rows=cm_conflicts,
            role_coverage=role_coverage, aggregation_policy=agg_policy,
            action_coverage_complete=action_coverage,
            trigger_coverage_complete=trigger_coverage,
            protocol_return_expectation=return_expectation,
            priority_policy=priority_policy,
            binding_mapping=mapping, snapshot_id=snapshot_id)
        results.append(r)
    return expansion, results


def result_by_control(expansion, results, control_item):
    """Return the unit results belonging to one control item."""
    targets = [eu.build_unit(PROJECT_ID).unit_id
               for eu in expansion.units
               if eu.control_item == control_item]
    assert len(targets) == 1, f"expected exactly one {control_item} unit"
    return [r for r in results if r.unit_id == targets[0]]


# ===========================================================================
# Input dataclass invariants
# ===========================================================================

class TestInputInvariants:
    def test_assignment_requires_content_hash(self):
        with pytest.raises(IPSliceError):
            PlannedTreatmentAssignment(
                assignment_id="A1", subject_ref="S1", site_ref="SITE01",
                treatment_role_token="active", study_phase="treatment",
                planned_drug_identity="x", dose="50", dose_unit="mg",
                dosage_form="tablet", route="口服", frequency="每日一次",
                planned_start="2026-01-01", planned_end="2026-03-31",
                content_hash="", assignment_lineage="l",
                display_role_label="L")

    def test_episode_direct_link_requires_assignment_id(self):
        with pytest.raises(IPSliceError, match="assignment_id"):
            make_episode(assignment_link="direct", assignment_id="")

    def test_episode_derived_link_requires_lineage(self):
        with pytest.raises(IPSliceError, match="lineage"):
            make_episode(assignment_link="derived", assignment_id="A1",
                         link_lineage="")

    def test_plan_rule_requires_planned_dose(self):
        with pytest.raises(IPSliceError, match="planned_dose"):
            ProtocolExposureRule(
                rule_id="r1", rule_version="v1", clause_locator="c",
                rule_content_hash="h", rule_lineage="l",
                rule_type="plan_actual", applicable_phases=("treatment",),
                planned_dose="", planned_dose_unit="mg",
                planned_dosage_form="tablet", planned_route="口服",
                planned_frequency="每日一次",
                priority_on_hit="high", priority_rationale="r")

    def test_allowed_action_rule_requires_action_types(self):
        with pytest.raises(IPSliceError, match="allowed_action_types"):
            ProtocolExposureRule(
                rule_id="r2", rule_version="v1", clause_locator="c",
                rule_content_hash="h", rule_lineage="l",
                rule_type="allowed_action", applicable_phases=("treatment",),
                priority_on_hit="high", priority_rationale="r")

    def test_medical_action_rule_requires_trigger_role(self):
        with pytest.raises(IPSliceError, match="trigger_role"):
            ProtocolExposureRule(
                rule_id="r3", rule_version="v1", clause_locator="c",
                rule_content_hash="h", rule_lineage="l",
                rule_type="medical_action", applicable_phases=("treatment",),
                expected_actions=(ACTION_PAUSE,),
                priority_on_hit="high", priority_rationale="r")

    def test_algorithm_requires_threshold(self):
        with pytest.raises(IPSliceError, match="threshold"):
            AdherenceAlgorithm(
                algorithm_id="a1", version="v1", content_hash="h",
                metric_kind=METRIC_DAY_RATIO,
                numerator_source="actual_exposure_days",
                denominator_source="window_days",
                lower_threshold=None, upper_threshold=None)

    def test_algorithm_window_requires_dates(self):
        with pytest.raises(IPSliceError, match="window"):
            AdherenceAlgorithm(
                algorithm_id="a2", version="v1", content_hash="h",
                metric_kind=METRIC_DAY_RATIO,
                numerator_source="actual_exposure_days",
                denominator_source="window_days",
                window_id="W1", window_start="", window_end="",
                lower_threshold="0.8")

    def test_evidence_requires_linked_episode(self):
        with pytest.raises(IPSliceError, match="linked_ip_episode_id"):
            IPActionEvidence(
                source_role="reported_ae",
                stable_source_event_key="reported_ae:AE#1",
                subject_ref="S1", site_ref="SITE01",
                linked_ip_episode_id="", relation_type="t",
                source_locator=make_locator("AE#1", "reported_ae"))

    def test_split_policy_requires_priority_lineage(self):
        with pytest.raises(IPSliceError, match="split_priority_lineage"):
            make_agg_policy(overlap_policy="split_at_change", split_lineage="")


# ===========================================================================
# Expected-set expansion (frozen D03 §4)
# ===========================================================================

class TestExpectedSetExpansion:
    def test_six_control_items_expand_independently(self):
        ep = make_episode()
        rules = (
            make_plan_actual_rule(),
            make_allowed_action_rule(action_types=(ACTION_DOSE_REDUCE,
                                                   ACTION_RESUME)),
            make_medical_action_rule(),
        )
        evidence = (
            make_evidence(event_key="reported_ae:AE#1", record_id="AE#1"),
            make_evidence(event_key="reported_ae:AE#2", record_id="AE#2",
                          concept="头痛"),
        )
        exp = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            assignments=(make_assignment(),), active_rules=rules,
            adherence_algorithms=(make_adherence_algorithm(),),
            action_evidence=evidence)
        # role_phase(1) + plan_actual(1) + allowed_action(2) +
        # medical_action(2) + adherence(1) = 7
        assert exp.count == 7
        assert len(set(exp.unit_ids)) == 7
        controls = {u.control_item for u in exp.units}
        assert controls == {"role_phase", "plan_actual", "allowed_action",
                            "adherence", "medical_action"}

    def test_accountability_proxy_algorithm_emits_accountability_unit(self):
        ep = make_episode()
        alg = make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY)
        exp = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            assignments=(make_assignment(),),
            adherence_algorithms=(alg,))
        assert exp.count == 2
        assert {u.control_item for u in exp.units} == {
            "role_phase", "accountability"}

    def test_medical_rule_without_evidence_emits_none_trigger(self):
        ep = make_episode()
        exp = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            assignments=(make_assignment(),),
            active_rules=(make_medical_action_rule(),))
        med = [u for u in exp.units if u.control_item == "medical_action"]
        assert len(med) == 1
        assert med[0].trigger_key == "none"

    def test_expected_set_hash_stable_and_order_independent(self):
        ep1 = make_episode()
        ep2 = make_episode(episode_key="EP-2", record_id="EX#2")
        rules = (make_plan_actual_rule(), make_allowed_action_rule())
        ex1 = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=(ep1, ep2),
            assignments=(make_assignment(),), active_rules=rules)
        ex2 = expand_ip_expected_set(
            project_id=PROJECT_ID, episodes=(ep2, ep1),
            assignments=(make_assignment(),), active_rules=rules)
        assert ex1.expected_set_hash == ex2.expected_set_hash
        assert ex1.expected_set_hash.startswith("d03-eset-")


# ===========================================================================
# Assignment binding (frozen D03 §4 steps 1-3)
# ===========================================================================

class TestAssignmentBinding:
    def test_direct_link_bound(self):
        ep = make_episode()
        res = resolve_episode_assignment(
            episode=ep, assignments=(make_assignment(),))
        assert res.is_bound
        assert res.assignment.assignment_id == "ASSIGN-01"

    def test_direct_link_missing_assignment(self):
        ep = make_episode(assignment_id="MISSING-99")
        res = resolve_episode_assignment(
            episode=ep, assignments=(make_assignment(),))
        assert res.status == "missing"

    def test_direct_link_subject_mismatch(self):
        ep = make_episode(subject="SYN-999")
        res = resolve_episode_assignment(
            episode=ep, assignments=(make_assignment(),))
        assert res.status == "missing"
        assert "不一致" in res.reason

    def test_no_link_without_mapping_is_missing(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(episode=ep, assignments=())
        assert res.status == "missing"

    def test_derived_unique_candidate_bound(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep, assignments=(make_assignment(),),
            binding_mapping=make_mapping())
        assert res.is_bound

    def test_derived_candidate_must_overlap_episode_window(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep,
            assignments=(make_assignment(
                planned_start="2025-01-01", planned_end="2025-03-31"),),
            binding_mapping=make_mapping())
        assert res.status == "missing"
        assert "时间窗明确不相交" in res.reason

    def test_derived_binding_uses_unique_window_candidate(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep,
            assignments=(
                make_assignment(
                    assignment_id="ASSIGN-OLD", planned_start="2025-01-01",
                    planned_end="2025-03-31"),
                make_assignment(
                    assignment_id="ASSIGN-CURRENT",
                    planned_start="2026-01-01",
                    planned_end="2026-03-31"),
            ),
            binding_mapping=make_mapping())
        assert res.is_bound
        assert res.assignment.assignment_id == "ASSIGN-CURRENT"

    def test_derived_partial_window_candidate_is_ambiguous(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep,
            assignments=(make_assignment(
                planned_start="2026-01", planned_end="2026-03"),),
            binding_mapping=make_mapping())
        assert res.status == "ambiguous"
        assert "无法证明唯一适用窗口" in res.reason

    def test_derived_exact_and_unresolved_windows_are_ambiguous(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep,
            assignments=(
                make_assignment(
                    assignment_id="ASSIGN-CURRENT",
                    planned_start="2026-01-01",
                    planned_end="2026-03-31"),
                make_assignment(
                    assignment_id="ASSIGN-PARTIAL",
                    planned_start="2026-01", planned_end="2026-03"),
            ),
            binding_mapping=make_mapping())
        assert res.status == "ambiguous"
        assert "ASSIGN-CURRENT" in res.reason
        assert "ASSIGN-PARTIAL" in res.reason

    def test_derived_two_candidates_ambiguous(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        res = resolve_episode_assignment(
            episode=ep,
            assignments=(make_assignment(assignment_id="ASSIGN-01"),
                         make_assignment(assignment_id="ASSIGN-02")),
            binding_mapping=make_mapping())
        assert res.status == "ambiguous"
        assert "不得按药名" in res.reason

    def test_role_phase_missing_binding_is_not_evaluable(self):
        ep = make_episode(assignment_id="MISSING-99")
        _, results = evaluate_one(ep)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "无法唯一绑定" in r.not_evaluable_reason]
        assert len(nes) >= 1

    def test_role_phase_ambiguous_binding_is_boundary(self):
        ep = make_episode(assignment_link="none", assignment_id="")
        _, results = evaluate_one(
            ep,
            assignments=(make_assignment(assignment_id="ASSIGN-01"),
                         make_assignment(assignment_id="ASSIGN-02")),
            mapping=make_mapping())
        boundaries = [r for r in results
                      if r.l1_disposition == L1Disposition.BOUNDARY
                      and "候选" in r.boundary_reason]
        assert len(boundaries) >= 1
        assert len(boundaries[0].r2_candidates) == 1


# ===========================================================================
# Actual exposure days (frozen D03 §6.1)
# ===========================================================================

class TestActualExposureDays:
    def test_span_never_proves_days_sparse_dosing(self):
        ep = make_episode(span_start="2026-01-01", span_end="2026-01-28")
        occs = (
            make_occurrence("O1", "2026-01-01"),
            make_occurrence("O2", "2026-01-15"),
        )
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=occs, policy=make_agg_policy())
        assert dc.status == "complete"
        assert dc.actual_exposure_days == 2
        assert dc.day_set == ("2026-01-01", "2026-01-15")

    def test_no_occurrence_never_implies_28_days(self):
        ep = make_episode(span_start="2026-01-01", span_end="2026-01-28")
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=(), policy=make_agg_policy())
        assert dc.status == "no_occurrence"
        assert dc.actual_exposure_days == 0

    def test_daily_multi_dose_counts_day_once(self):
        ep = make_episode()
        occs = (
            make_occurrence("O1", "2026-01-05", dose="50"),
            make_occurrence("O2", "2026-01-05", dose="25"),
        )
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=occs, policy=make_agg_policy())
        assert dc.status == "complete"
        assert dc.actual_exposure_days == 1

    def test_continuous_interval_expands_only_with_policy_and_semantics(self):
        ep = make_episode()
        occ = make_occurrence("O1", "2026-01-05", date_end="2026-01-07",
                              continuous_daily=True)
        # Policy forbids expansion -> endpoints only.
        dc1 = compute_actual_exposure_days(
            episode=ep, occurrences=(occ,),
            policy=make_agg_policy(continuous_expansion=False))
        assert dc1.actual_exposure_days == 2
        # Policy allows expansion -> full inclusive day set.
        dc2 = compute_actual_exposure_days(
            episode=ep, occurrences=(occ,),
            policy=make_agg_policy(continuous_expansion=True))
        assert dc2.actual_exposure_days == 3
        assert dc2.day_set == ("2026-01-05", "2026-01-06", "2026-01-07")

    def test_interval_without_daily_semantics_never_expands(self):
        ep = make_episode()
        occ = make_occurrence("O1", "2026-01-05", date_end="2026-01-07",
                              continuous_daily=False)
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=(occ,),
            policy=make_agg_policy(continuous_expansion=True))
        # No continuous-daily declaration: endpoints only.
        assert dc.actual_exposure_days == 2

    def test_same_role_same_dose_overlap_unions(self):
        ep = make_episode()
        occs = (
            make_occurrence("O1", "2026-01-05", date_end="2026-01-10",
                            continuous_daily=True),
            make_occurrence("O2", "2026-01-08", date_end="2026-01-12",
                            continuous_daily=True),
        )
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=occs,
            policy=make_agg_policy(continuous_expansion=True))
        assert dc.status == "complete"
        assert dc.actual_exposure_days == 8  # 01-05..01-12 inclusive

    def test_different_dose_overlap_is_boundary_not_silent_union(self):
        ep = make_episode()
        occs = (
            make_occurrence("O1", "2026-01-05", date_end="2026-01-10",
                            continuous_daily=True, dose="50"),
            make_occurrence("O2", "2026-01-08", date_end="2026-01-12",
                            continuous_daily=True, dose="25"),
        )
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=occs,
            policy=make_agg_policy(continuous_expansion=True,
                                   overlap_policy="boundary"))
        assert dc.status == "boundary"
        assert "重叠" in dc.reason

    def test_different_dose_overlap_union_fail_is_ambiguous(self):
        ep = make_episode()
        occs = (
            make_occurrence("O1", "2026-01-05", date_end="2026-01-10",
                            continuous_daily=True, dose="50"),
            make_occurrence("O2", "2026-01-08", date_end="2026-01-12",
                            continuous_daily=True, dose="25"),
        )
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=occs,
            policy=make_agg_policy(continuous_expansion=True,
                                   overlap_policy="union_fail"))
        assert dc.status == "ambiguous"

    def test_duplicate_locator_rows_dedup(self):
        ep = make_episode()
        occ1 = make_occurrence("O1", "2026-01-05", record_id="EX-DUP")
        occ2 = make_occurrence("O1b", "2026-01-05", record_id="EX-DUP")
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=(occ1, occ2), policy=make_agg_policy())
        assert dc.status == "complete"
        assert dc.actual_exposure_days == 1

    def test_conflicting_revision_same_event_is_ambiguous(self):
        ep = make_episode()
        occ1 = make_occurrence("O1", "2026-01-05", revision="r1",
                               record_id="EX-REV")
        # Same stable event key (table_semantic:record_id) but a different
        # locator/snapshot: the kernel cannot select the current accepted
        # revision and must fail closed.
        occ2 = ExposureOccurrence(
            occurrence_id="O2", episode_key="EP-1", date_start="2026-01-06",
            dose="50", dose_unit="mg",
            source_locator=make_locator("EX-REV", snapshot_id="snap-v2"),
            accepted_revision="r2", accepted_revision_hash="h-r2")
        dc = compute_actual_exposure_days(
            episode=ep, occurrences=(occ1, occ2), policy=make_agg_policy())
        assert dc.status == "ambiguous"
        assert "accepted revision" in dc.reason


# ===========================================================================
# Six positives and negatives (frozen D03 §5.1)
# ===========================================================================

class TestSixPositivesAndNegatives:
    def test_plan_actual_mismatch_positive_and_negative(self):
        pos_ep = make_episode(dose="100")
        _, pos_results = evaluate_one(pos_ep, rules=(make_plan_actual_rule(),))
        pos = [r for r in pos_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH]
        assert len(pos) == 1
        assert pos[0].l1_disposition == L1Disposition.POSITIVE
        assert "剂量" in pos[0].query_refs[0].finding

        neg_ep = make_episode(dose="50")
        neg_exp, neg_results = evaluate_one(
            neg_ep, rules=(make_plan_actual_rule(),))
        neg_pa = result_by_control(neg_exp, neg_results, "plan_actual")
        assert len(neg_pa) == 1
        assert neg_pa[0].l1_disposition == L1Disposition.NEGATIVE
        assert not neg_pa[0].r2_candidates
        assert not neg_pa[0].query_refs

    def test_role_phase_mismatch_positive_and_negative(self):
        mis_ep = make_episode(role="control")
        _, mis_results = evaluate_one(mis_ep)
        pos = [r for r in mis_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH]
        assert len(pos) == 1
        assert pos[0].monitoring_priority == "high"

        ok_ep = make_episode(role="active")
        _, ok_results = evaluate_one(ok_ep)
        neg = [r for r in ok_results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(neg) == 1

    def test_phase_mismatch_positive(self):
        mis_ep = make_episode(phase="followup")
        _, mis_results = evaluate_one(mis_ep)
        pos = [r for r in mis_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH]
        assert len(pos) == 1
        assert "阶段" in pos[0].query_refs[0].finding

    def test_adherence_out_of_range_positive_and_negative(self):
        alg = make_adherence_algorithm()
        pos_ep = make_episode()
        pos_occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                         for i in range(1, 6))  # 5 days -> 0.5 < 0.8
        _, pos_results = evaluate_one(
            pos_ep, algorithms=(alg,), occurrences=pos_occs,
            observations=(make_observation("OB1"),))
        pos = [r for r in pos_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(pos) == 1
        assert "0.5" in pos[0].query_refs[0].finding

        neg_ep = make_episode()
        neg_occs = tuple(make_occurrence(f"N{i}", f"2026-01-0{i}")
                         for i in range(1, 10))  # 9 days -> 0.9
        neg_exp, neg_results = evaluate_one(
            neg_ep, algorithms=(alg,), occurrences=neg_occs,
            observations=(make_observation("OB2"),))
        neg = result_by_control(neg_exp, neg_results, "adherence")
        assert len(neg) == 1
        assert neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_unsupported_action_positive_and_negative(self):
        rule = make_allowed_action_rule()
        # 25 mg is not allowed when the protocol only permits 50 mg.
        pos_ep = make_episode()
        pos_action = make_actual_action(dose_after="25")
        _, pos_results = evaluate_one(
            pos_ep, rules=(rule,), actual_actions=(pos_action,),
            action_coverage=True)
        pos = [r for r in pos_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION]
        assert len(pos) == 1
        assert "25" in pos[0].query_refs[0].finding

        neg_ep = make_episode()
        neg_action = make_actual_action(dose_after="50")
        planned = make_planned_action(action_type=ACTION_DOSE_REDUCE)
        neg_exp, neg_results = evaluate_one(
            neg_ep, rules=(rule,),
            actual_actions=(neg_action,), planned_actions=(planned,),
            action_coverage=True)
        neg = result_by_control(neg_exp, neg_results, "allowed_action")
        assert len(neg) == 1
        assert neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_medical_trigger_action_positive_and_negative(self):
        rule = make_medical_action_rule()
        pos_ep = make_episode()
        pos_ev = make_evidence(actual_action=ACTION_RESUME)
        _, pos_results = evaluate_one(
            pos_ep, rules=(rule,), evidence=(pos_ev,),
            trigger_coverage=True)
        pos = [r for r in pos_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT]
        assert len(pos) == 1
        assert "resume" in pos[0].query_refs[0].finding

        neg_ep = make_episode()
        neg_ev = make_evidence(actual_action=ACTION_PAUSE)
        neg_exp, neg_results = evaluate_one(
            neg_ep, rules=(rule,), evidence=(neg_ev,),
            trigger_coverage=True)
        neg = result_by_control(neg_exp, neg_results, "medical_action")
        assert len(neg) == 1
        assert neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_accountability_inconsistency_positive_and_negative(self):
        alg = make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY,
                                       canonical_unit="片")
        ret = make_return_record(amount="0", amount_kind="zero")
        dis = make_dispense_record()
        pos_ep = make_episode()
        pos_obs = make_observation("OB1", numerator="5", denominator="10",
                                   unit="片")
        _, pos_results = evaluate_one(
            pos_ep, algorithms=(alg,), returns=(ret,), dispenses=(dis,),
            observations=(pos_obs,), return_expectation="expected")
        pos = [r for r in pos_results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY]
        assert len(pos) == 1

        neg_ep = make_episode()
        neg_obs = make_observation("OB2", numerator="10", denominator="10",
                                   unit="片")
        neg_exp, neg_results = evaluate_one(
            neg_ep, algorithms=(alg,), returns=(ret,), dispenses=(dis,),
            observations=(neg_obs,), return_expectation="expected")
        neg = result_by_control(neg_exp, neg_results, "accountability")
        assert len(neg) == 1
        assert neg[0].l1_disposition == L1Disposition.NEGATIVE


# ===========================================================================
# Boundary cases (frozen D03 §5.3)
# ===========================================================================

class TestBoundaryCases:
    def test_threshold_equality_inclusivity_unstated_is_boundary(self):
        alg = make_adherence_algorithm(lower="0.8", lower_inc=None)
        ep = make_episode()
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 9))  # 8 days -> exactly 0.8
        _, results = evaluate_one(
            ep, algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB1"),))
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY
               and "阈值等号" in r.boundary_reason]
        assert len(bnd) == 1

    def test_window_violation_occurrence_outside_plan_window_positive(self):
        ep = make_episode(span_start="2026-01-01", span_end="2026-01-28")
        rule = make_plan_actual_rule(window_end="2026-01-10")
        occs = (make_occurrence("O1", "2026-01-12"),)
        _, results = evaluate_one(
            ep, rules=(rule,), occurrences=occs)
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH
               and "给药窗口之外" in r.query_refs[0].finding]
        assert len(pos) == 1

    def test_episode_fully_outside_rule_window_is_not_applicable(self):
        ep = make_episode(span_start="2026-07-01", span_end="2026-07-28")
        rule = make_plan_actual_rule()
        _, results = evaluate_one(ep, rules=(rule,))
        nas = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_APPLICABLE]
        assert len(nas) == 1
        assert len(nas[0].r2_candidates) == 0
        assert len(nas[0].query_refs) == 0

    def test_partial_date_possibly_overlaps_is_boundary(self):
        ep = make_episode(span_start="2026-01", span_end="2026-02")
        rule = make_plan_actual_rule(window_start="2026-01-15",
                                     window_end="2026-06-30")
        _, results = evaluate_one(ep, rules=(rule,))
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(bnd) == 1

    def test_return_partial_value_is_boundary(self):
        alg = make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY,
                                       canonical_unit="片")
        ret = make_return_record(amount="5-10", amount_kind="range")
        dis = make_dispense_record()
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(
                make_observation("OB1", numerator="10", denominator="10",
                                 unit="片"),),
            return_expectation="expected")
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY
               and "范围值" in r.boundary_reason]
        assert len(bnd) == 1

    def test_multiple_actual_actions_same_type_are_boundary(self):
        rule = make_allowed_action_rule()
        actions = (
            make_actual_action("AA-1", dose_after="50"),
            make_actual_action("AA-2", dose_after="50"),
        )
        _, results = evaluate_one(
            make_episode(), rules=(rule,), actual_actions=actions,
            action_coverage=True)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(bnd) == 1


# ===========================================================================
# not_evaluable cases (frozen D03 §5.4)
# ===========================================================================

class TestNotEvaluableCases:
    def test_missing_algorithm_guard(self):
        ep = make_episode()
        eu = IPUnitExpanded(
            episode=ep, control_item="adherence",
            control_token="adherence:ALG-X:W1", risk_family="adherence",
            resolution=AssignmentResolution(
                status="bound", assignment=make_assignment()),
            assignment=make_assignment())
        r = evaluate_ip_unit(
            project_id=PROJECT_ID, expanded=eu,
            role_coverage=DEFAULT_ROLE_COVERAGE)
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "缺少适用的依从性算法" in r.not_evaluable_reason

    def test_missing_role_coverage_is_not_evaluable(self):
        ep = make_episode()
        coverage = dict(DEFAULT_ROLE_COVERAGE)
        coverage["planned_treatment"] = False
        _, results = evaluate_one(ep, rules=(make_plan_actual_rule(),),
                                  role_coverage=coverage)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "覆盖不完整" in r.not_evaluable_reason]
        assert len(nes) >= 1

    def test_zero_denominator_is_not_evaluable(self):
        alg = make_adherence_algorithm(metric=METRIC_AMOUNT_RATIO,
                                       canonical_unit="")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,),
            observations=(make_observation(
                "OB1", numerator="10", denominator="0"),))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "分母为零" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_unit_conflict_without_conversion_is_not_evaluable(self):
        alg = make_adherence_algorithm(metric=METRIC_AMOUNT_RATIO,
                                       canonical_unit="g")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,),
            observations=(make_observation(
                "OB1", numerator="500", denominator="1", unit="mg"),))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "换算依据" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_single_missing_occurrence_does_not_imply_missed_dose(self):
        alg = make_adherence_algorithm()
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), occurrences=(),
            observations=(make_observation("OB1"),))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "不得推断漏服" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_cm_ip_mutual_exclusion_is_not_evaluable(self):
        cm_row = IPSemanticRecord(
            role="recorded_cm", concept="synthetic_cm",
            locator=make_locator("EX#1", "recorded_cm"),
            subject_ref="SYN-001", site_ref=SITE_REF)
        _, results = evaluate_one(
            make_episode(record_id="EX#1"), cm_conflicts=(cm_row,))
        nes = [r for r in results
               if "角色互斥冲突" in r.not_evaluable_reason]
        assert len(nes) >= 1

    def test_medical_wrong_subject_never_positive(self):
        rule = make_medical_action_rule()
        wrong = make_evidence(subject="SYN-999")
        _, results = evaluate_one(
            make_episode(), rules=(rule,), evidence=(wrong,),
            trigger_coverage=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "跨受试者" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert not any(r.l1_disposition == L1Disposition.POSITIVE
                       for r in results)

    def test_medical_wrong_episode_never_positive(self):
        rule = make_medical_action_rule()
        wrong = make_evidence(episode_key="EP-OTHER")
        _, results = evaluate_one(
            make_episode(), rules=(rule,), evidence=(wrong,),
            trigger_coverage=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "跨受试者" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_medical_unconfirmed_relation_is_not_evaluable(self):
        rule = make_medical_action_rule()
        ev = make_evidence(confirmation=CONFIRMATION_UNRESOLVED)
        _, results = evaluate_one(
            make_episode(), rules=(rule,), evidence=(ev,),
            trigger_coverage=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "尚未确认" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_medical_trigger_coverage_incomplete_is_not_evaluable(self):
        rule = make_medical_action_rule()
        ev = make_evidence(actual_action=ACTION_RESUME)
        _, results = evaluate_one(
            make_episode(), rules=(rule,), evidence=(ev,),
            trigger_coverage=False)
        nes = [r for r in results
               if "触发来源覆盖不完整" in r.not_evaluable_reason]
        assert len(nes) >= 1


# ===========================================================================
# Adherence arithmetic (frozen D03 §6.2, §11 item 9)
# ===========================================================================

class TestAdherenceNumbers:
    def test_threshold_equality_inclusive_is_negative(self):
        alg = make_adherence_algorithm(lower="0.8", lower_inc=True)
        ep = make_episode()
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 9))  # exactly 0.8
        _, results = evaluate_one(
            ep, algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB1"),))
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE
               and "恰在阈值等号且该侧包含" in
               " ".join(ev.uncertainty_note for ev in r.evidence)]
        assert len(neg) == 1

    def test_threshold_equality_exclusive_is_positive(self):
        alg = make_adherence_algorithm(lower="0.8", lower_inc=False)
        ep = make_episode()
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 9))  # exactly 0.8
        _, results = evaluate_one(
            ep, algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB1"),))
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(pos) == 1

    def test_7995_rounding_flip_before_after(self):
        before_alg = make_adherence_algorithm(
            metric=METRIC_AMOUNT_RATIO, lower="80", lower_inc=True,
            compare="before", canonical_unit="")
        after_alg = make_adherence_algorithm(
            metric=METRIC_AMOUNT_RATIO, lower="80", lower_inc=True,
            compare="after", canonical_unit="")
        ep = make_episode()
        obs = make_observation("OB1", numerator="79.95", denominator="1")
        _, before_results = evaluate_one(
            ep, algorithms=(before_alg,), observations=(obs,))
        _, after_results = evaluate_one(
            ep, algorithms=(after_alg,), observations=(obs,))
        before_pos = [r for r in before_results
                      if r.positive_subtype
                      == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        after_pos = [r for r in after_results
                     if r.positive_subtype
                     == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(before_pos) == 1   # 79.95 < 80 -> positive
        assert len(after_pos) == 0    # rounds to 80.0 >= 80 -> negative

    def test_duplicate_observation_is_not_evaluable(self):
        alg = make_adherence_algorithm(metric=METRIC_AMOUNT_RATIO,
                                       canonical_unit="")
        obs1 = make_observation("OB1", numerator="10", denominator="10")
        obs2 = make_observation("OB2", numerator="11", denominator="10")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), observations=(obs1, obs2))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "重复 observation" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_unit_conversion_applies_to_ratio(self):
        alg = make_adherence_algorithm(
            metric=METRIC_AMOUNT_RATIO, canonical_unit="g",
            conversions=(("mg", "g", "0.001"),), lower="0.8")
        # Both raw values share the source unit "mg": 500 mg vs 1000 mg
        # (= 1 g) converts to 0.5 g / 1 g = 0.5 < 0.8 -> positive.
        obs = make_observation("OB1", numerator="500", denominator="1000",
                               unit="mg")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), observations=(obs,))
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(pos) == 1
        assert "0.5" in pos[0].query_refs[0].finding

    def test_window_endpoint_inclusivity_changes_denominator(self):
        inc_alg = make_adherence_algorithm(
            lower="0.55", end_inc=True, window_end="2026-01-10")
        exc_alg = make_adherence_algorithm(
            lower="0.55", end_inc=False, window_end="2026-01-10")
        ep = make_episode()
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 6))  # 5 dosing days
        _, inc_results = evaluate_one(
            ep, algorithms=(inc_alg,), occurrences=occs,
            observations=(make_observation("OB1"),))
        exc_exp, exc_results = evaluate_one(
            ep, algorithms=(exc_alg,), occurrences=occs,
            observations=(make_observation("OB2"),))
        # inclusive end: 5/10 = 0.5 < 0.55 -> positive
        inc_pos = [r for r in inc_results
                   if r.positive_subtype
                   == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(inc_pos) == 1
        # exclusive end: 5/9 = 0.5556 >= 0.55 -> negative
        exc_neg = result_by_control(exc_exp, exc_results, "adherence")
        assert len(exc_neg) == 1
        assert exc_neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_planned_pause_denominator_effect(self):
        window = "2026-01-15"
        included_alg = make_adherence_algorithm(
            window_end=window, lower="0.8", pause_handling="included")
        excluded_alg = make_adherence_algorithm(
            window_end=window, lower="0.8",
            pause_handling="excluded_from_denominator")
        pause = make_planned_action(action_type=ACTION_PAUSE)
        occs = tuple(
            make_occurrence(f"O{i}", f"2026-01-{i:02d}")
            for i in (1, 2, 3, 4, 10, 11, 12, 13, 14, 15))
        # 10 dosing days in a 15-day window; 5 planned pause days (01-05..09)
        _, inc_results = evaluate_one(
            make_episode(), algorithms=(included_alg,), occurrences=occs,
            observations=(make_observation("OB1"),),
            planned_actions=(pause,), action_coverage=True)
        exc_exp, exc_results = evaluate_one(
            make_episode(), algorithms=(excluded_alg,), occurrences=occs,
            observations=(make_observation("OB2"),),
            planned_actions=(pause,), action_coverage=True)
        inc_pos = [r for r in inc_results
                   if r.positive_subtype
                   == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        exc_neg = result_by_control(exc_exp, exc_results, "adherence")
        # included: 10/15 = 0.667 < 0.8 -> positive
        assert len(inc_pos) == 1
        # excluded: 10/(15-5) = 1.0 -> negative
        assert len(exc_neg) == 1
        assert exc_neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_pause_exclusion_requires_action_coverage(self):
        alg = make_adherence_algorithm(
            window_end="2026-01-15", pause_handling="excluded_from_denominator")
        occs = tuple(
            make_occurrence(f"O{i}", f"2026-01-{i:02d}")
            for i in (1, 2, 3, 4, 10, 11, 12, 13, 14, 15))
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB1"),),
            action_coverage=False)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "计划动作来源覆盖不完整" in r.not_evaluable_reason]
        assert len(nes) == 1


# ===========================================================================
# Allowed actions (frozen D03 §6.3, §11 item 8)
# ===========================================================================

class TestAllowedActions:
    def test_stop_with_allowed_reason_negative(self):
        rule = make_allowed_action_rule(
            action_types=(ACTION_STOP,), allowed_dose_after=(),
            allowed_reasons=("完成治疗",))
        planned = make_planned_action(action_type=ACTION_STOP,
                                      reason="完成治疗")
        actual = make_actual_action(action_type=ACTION_STOP,
                                    reason="完成治疗", dose_after="0")
        stop_exp, results = evaluate_one(
            make_episode(), rules=(rule,),
            planned_actions=(planned,), actual_actions=(actual,),
            action_coverage=True)
        neg = result_by_control(stop_exp, results, "allowed_action")
        assert len(neg) == 1
        assert neg[0].l1_disposition == L1Disposition.NEGATIVE

    def test_stop_with_disallowed_reason_positive(self):
        rule = make_allowed_action_rule(
            action_types=(ACTION_STOP,), allowed_dose_after=(),
            allowed_reasons=("完成治疗",))
        actual = make_actual_action(action_type=ACTION_STOP,
                                    reason="个人意愿", dose_after="0")
        _, results = evaluate_one(
            make_episode(), rules=(rule,), actual_actions=(actual,),
            action_coverage=True)
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION]
        assert len(pos) == 1
        assert "个人意愿" in pos[0].query_refs[0].finding

    def test_action_without_planned_counterpart_positive_when_required(self):
        rule = make_allowed_action_rule()
        actual = make_actual_action(dose_after="50")
        _, results = evaluate_one(
            make_episode(), rules=(rule,), actual_actions=(actual,),
            action_coverage=True)
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION
               and "计划动作" in r.query_refs[0].finding]
        assert len(pos) == 1

    def test_no_actual_action_is_not_evaluable_not_false_negative(self):
        rule = make_allowed_action_rule()
        aa_exp, results = evaluate_one(
            make_episode(), rules=(rule,), action_coverage=True)
        aa = result_by_control(aa_exp, results, "allowed_action")
        assert len(aa) == 1
        assert aa[0].l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "未找到该类型" in aa[0].not_evaluable_reason
        assert not aa[0].r2_candidates

    def test_planned_action_overlap_is_boundary(self):
        rule = make_allowed_action_rule()
        planned = (
            make_planned_action("PA-1", action_type=ACTION_DOSE_REDUCE),
            make_planned_action("PA-2", action_type=ACTION_DOSE_REDUCE),
        )
        actual = make_actual_action(dose_after="50")
        _, results = evaluate_one(
            make_episode(), rules=(rule,),
            planned_actions=planned, actual_actions=(actual,),
            action_coverage=True)
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY
               and "多个计划动作" in r.boundary_reason]
        assert len(bnd) == 1


# ===========================================================================
# Accountability decision table (frozen D03 §5.4)
# ===========================================================================

class TestAccountabilityDecisionTable:
    def _alg(self):
        return make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY,
                                        canonical_unit="片")

    def test_uncovered_return_role_is_not_evaluable(self):
        coverage = dict(DEFAULT_ROLE_COVERAGE)
        coverage["ip_return"] = False
        _, results = evaluate_one(
            make_episode(), algorithms=(self._alg(),),
            role_coverage=coverage, return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "回收记录" in r.not_evaluable_reason]
        assert len(nes) >= 1

    def test_expected_return_zero_rows_is_not_evaluable_with_gap(self):
        _, results = evaluate_one(
            make_episode(), algorithms=(self._alg(),),
            returns=(), return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "研究药物核算信息待核实" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_return_fields_empty_is_not_evaluable(self):
        ret = make_return_record(amount="", amount_kind="missing")
        dis = make_dispense_record()
        _, results = evaluate_one(
            make_episode(), algorithms=(self._alg(),), returns=(ret,),
            dispenses=(dis,),
            observations=(make_observation(
                "OB1", numerator="10", denominator="10", unit="片"),),
            return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "必需字段" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_not_required_window_is_not_applicable(self):
        _, results = evaluate_one(
            make_episode(), algorithms=(self._alg(),),
            return_expectation="not_required")
        nas = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_APPLICABLE]
        assert len(nas) == 1
        assert len(nas[0].r2_candidates) == 0

    def test_missing_dispense_rows_is_not_evaluable(self):
        ret = make_return_record(amount="0", amount_kind="zero")
        _, results = evaluate_one(
            make_episode(), algorithms=(self._alg(),), returns=(ret,),
            dispenses=(),
            observations=(make_observation(
                "OB1", numerator="0", denominator="10", unit="片"),),
            return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "发放记录缺失" in r.not_evaluable_reason]
        assert len(nes) == 1


# ===========================================================================
# Accountability unit conversion (frozen D03 §6.2 rules 1/3, §11 item 9)
# ===========================================================================

class TestAccountabilityUnitConversion:
    """Dispense/return/recorded sides are each converted to the algorithm's
    canonical unit via the versioned conversion rules before the balance
    comparison.  A missing or unverifiable conversion basis fails closed to
    not_evaluable; raw values are never compared across units."""

    def _alg(self, canonical_unit="mg", conversions=()):
        return make_adherence_algorithm(
            metric=METRIC_ACCOUNTABILITY_PROXY,
            canonical_unit=canonical_unit, conversions=conversions)

    def test_conversion_present_converted_balance_closes_negative(self):
        """20 片 dispense - 10 片 return = 50 mg after 片->mg x5, equal to
        recorded 50 mg -> negative."""
        alg = self._alg(canonical_unit="mg",
                        conversions=(("片", "mg", "5"),))
        ret = make_return_record(amount="10", unit="片")
        dis = make_dispense_record(amount="20", unit="片")
        obs = make_observation("OB-C1", numerator="50", denominator="50",
                               unit="mg")
        exp, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(obs,),
            return_expectation="expected")
        acc = result_by_control(exp, results, "accountability")
        assert len(acc) == 1
        assert acc[0].l1_disposition == L1Disposition.NEGATIVE
        assert not acc[0].r2_candidates

    def test_conversion_missing_is_not_evaluable(self):
        """片 sides cannot be converted to canonical mg without a rule ->
        not_evaluable, never a negative on raw values."""
        alg = self._alg(canonical_unit="mg", conversions=())
        ret = make_return_record(amount="10", unit="片")
        dis = make_dispense_record(amount="20", unit="片")
        obs = make_observation("OB-C2", numerator="50", denominator="50",
                               unit="mg")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(obs,),
            return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "换算依据" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert not nes[0].r2_candidates

    def test_cross_side_unit_mismatch_without_basis_is_not_evaluable(self):
        """Return side 片 vs dispense side mg: each side single-unit, but no
        versioned basis converts the return side -> not_evaluable."""
        alg = self._alg(canonical_unit="mg", conversions=())
        ret = make_return_record(amount="10", unit="片")
        dis = make_dispense_record(amount="50", unit="mg")
        obs = make_observation("OB-C3", numerator="40", denominator="50",
                               unit="mg")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(obs,),
            return_expectation="expected")
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "换算依据" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_converted_mismatch_is_positive(self):
        """Converted balance 50 mg != recorded 40 mg -> positive with the
        canonical-unit wording."""
        alg = self._alg(canonical_unit="mg",
                        conversions=(("片", "mg", "5"),))
        ret = make_return_record(amount="10", unit="片")
        dis = make_dispense_record(amount="20", unit="片")
        obs = make_observation("OB-C4", numerator="40", denominator="50",
                               unit="mg")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(obs,),
            return_expectation="expected")
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY]
        assert len(pos) == 1
        assert pos[0].l1_disposition == L1Disposition.POSITIVE
        query = pos[0].query_refs[0]
        assert "50" in query.finding
        assert "mg" in query.finding

    def test_identical_units_still_pass_through(self):
        """Same-unit sides (no conversion needed) keep the original
        positive/negative behavior."""
        alg = self._alg(canonical_unit="片", conversions=())
        ret = make_return_record(amount="0", amount_kind="zero")
        dis = make_dispense_record(amount="10", unit="片")
        obs = make_observation("OB-C5", numerator="5", denominator="10",
                               unit="片")
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(obs,),
            return_expectation="expected")
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY]
        assert len(pos) == 1
        assert pos[0].l1_disposition == L1Disposition.POSITIVE


# ===========================================================================
# accountability_proxy user language (frozen D03 §6.2)
# ===========================================================================

class TestAccountabilityProxyUserLanguage:
    """Frozen §6.2: ``accountability_proxy`` results must annotate
    ``按发放/回收核算`` in user-visible Query/evidence text for positive
    AND negative outcomes, and must never be presented as proven actual
    dosing days."""

    PROXY_PHRASE = "按发放/回收核算"
    # The forbidden claim token never appears anywhere in proxy text.
    PROVEN_DAYS_TOKEN = "实际服药天数"

    def _proxy_case(self, observation):
        alg = make_adherence_algorithm(metric=METRIC_ACCOUNTABILITY_PROXY,
                                       canonical_unit="片")
        ret = make_return_record(amount="0", amount_kind="zero")
        dis = make_dispense_record()
        expansion, results = evaluate_one(
            make_episode(), algorithms=(alg,), returns=(ret,),
            dispenses=(dis,), observations=(observation,),
            return_expectation="expected")
        return result_by_control(expansion, results, "accountability")

    def _user_texts(self, result):
        texts = [ev.uncertainty_note for ev in result.evidence]
        texts.extend(r.boundary_reason for r in (result,))
        texts.extend(r.not_evaluable_reason for r in (result,))
        texts.append(result.audience_label)
        for q in result.query_refs:
            texts.extend((q.basis, q.finding, q.action))
        return [t for t in texts if t]

    def test_proxy_positive_query_and_evidence_stamp_phrase(self):
        result = self._proxy_case(
            make_observation("OB-P1", numerator="5", denominator="10",
                             unit="片"))
        assert len(result) == 1
        positive = result[0]
        assert positive.l1_disposition == L1Disposition.POSITIVE
        assert positive.positive_subtype == (
            POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY)
        assert len(positive.query_refs) == 1
        query = positive.query_refs[0]
        assert self.PROXY_PHRASE in query.basis
        assert self.PROXY_PHRASE in query.finding
        assert any(self.PROXY_PHRASE in ev.uncertainty_note
                   for ev in positive.evidence)

    def test_proxy_negative_evidence_stamps_phrase(self):
        result = self._proxy_case(
            make_observation("OB-N1", numerator="10", denominator="10",
                             unit="片"))
        assert len(result) == 1
        negative = result[0]
        assert negative.l1_disposition == L1Disposition.NEGATIVE
        assert any(self.PROXY_PHRASE in ev.uncertainty_note
                   for ev in negative.evidence)

    def test_proxy_never_presented_as_proven_dosing_days(self):
        positive = self._proxy_case(
            make_observation("OB-P2", numerator="5", denominator="10",
                             unit="片"))[0]
        negative = self._proxy_case(
            make_observation("OB-N2", numerator="10", denominator="10",
                             unit="片"))[0]
        for text in self._user_texts(positive) + self._user_texts(negative):
            assert self.PROVEN_DAYS_TOKEN not in text, (
                f"proxy result presented as proven dosing days: {text!r}")

    def test_non_proxy_adherence_not_stamped_as_proxy(self):
        """The 按发放/回收核算 annotation applies only to
        accountability_proxy metrics, never to day-ratio adherence."""
        alg = make_adherence_algorithm()  # day_ratio
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 6))
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB-D1"),))
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE]
        assert len(pos) == 1
        for ev in pos[0].evidence:
            assert self.PROXY_PHRASE not in ev.uncertainty_note
        for query in pos[0].query_refs:
            assert self.PROXY_PHRASE not in query.basis
            assert self.PROXY_PHRASE not in query.finding


# ===========================================================================
# Blinding / disclosure (frozen D03 §3.3, F-07)
# ===========================================================================

class TestBlindingAndDisclosure:
    def test_masked_identity_role_phase_still_evaluates(self):
        ep = make_episode(disclosure="masked_identity",
                          drug_identity="SECRET-DRUG")
        assignment = make_assignment(disclosure="masked_identity",
                                     display_label="盲态研究药物 B")
        _, results = evaluate_one(ep, assignments=(assignment,))
        neg = [r for r in results
               if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(neg) == 1

    def test_masked_identity_mismatch_positive_uses_display_label_only(self):
        ep = make_episode(disclosure="masked_identity", role="control",
                          drug_identity="SECRET-DRUG")
        assignment = make_assignment(disclosure="masked_identity",
                                     display_label="盲态研究药物 B")
        _, results = evaluate_one(ep, assignments=(assignment,))
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH]
        assert len(pos) == 1
        text = (pos[0].query_refs[0].basis + pos[0].query_refs[0].finding
                + pos[0].query_refs[0].action)
        assert "SECRET-DRUG" not in text
        assert "盲态研究药物 B" in text
        for marker in pos[0].journey_markers:
            assert "SECRET-DRUG" not in str(marker)

    def test_masked_dose_plan_actual_is_not_evaluable(self):
        ep = make_episode(disclosure="masked_identity_and_dose")
        _, results = evaluate_one(ep, rules=(make_plan_actual_rule(),))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "披露范围不可用" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_masked_dose_allowed_action_dose_check_not_evaluable(self):
        ep = make_episode(disclosure="masked_identity_and_dose")
        actual = make_actual_action(dose_after="25")
        _, results = evaluate_one(
            ep, rules=(make_allowed_action_rule(),),
            actual_actions=(actual,), action_coverage=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "披露范围不可用" in r.not_evaluable_reason]
        assert len(nes) == 1


# ===========================================================================
# Query and user language (frozen D03 §8)
# ===========================================================================

class TestQueryAndUserLanguage:
    PROHIBITED = ("正式事实", "候选信号", "只读", "未知风险", "已构成PD",
                  "构成PD", "已构成方案偏离")

    def _all_user_strings(self, results):
        strs = []
        for r in results:
            strs.append(r.not_evaluable_reason)
            strs.append(r.boundary_reason)
            strs.append(r.audience_label)
            for q in r.query_refs:
                strs.append(q.basis)
                strs.append(q.finding)
                strs.append(q.action)
        return [s for s in strs if s]

    def test_positive_has_three_part_query_with_provenance(self):
        ep = make_episode(dose="100")
        rule = make_plan_actual_rule()
        _, results = evaluate_one(ep, rules=(rule,))
        pos = [r for r in results
               if r.positive_subtype
               == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH][0]
        assert len(pos.query_refs) == 1
        q = pos.query_refs[0]
        assert q.basis.startswith("依据")
        assert q.finding.startswith("发现")
        assert q.action.startswith("行动项")
        assert q.linked_candidate_id == pos.r2_candidates[0].candidate_id
        assert "R-IP-01" in q.basis
        assert "P20-1" in q.basis
        assert "SYN-001" in q.finding
        assert len(set(q.source_locator_ids)) == len(q.source_locator_ids)
        # Query locators must be reachable on the materialized evaluation.
        ue = pos.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rl-plan-01")
        assert isinstance(ue, UnitEvaluation)

    def test_all_positive_subtypes_have_native_labels(self):
        subtypes = {
            POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH:
                "研究药给药与方案不一致",
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH:
                "治疗分组或阶段待核实",
            POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE: "研究药依从性待核实",
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION: "给药调整依据待核实",
            POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT:
                "给药处置与医学事件不一致",
            POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY:
                "研究药物核算待核实",
        }
        for subtype, label in subtypes.items():
            assert label in POSITIVE_SUBTYPE_LABELS[subtype]
            from mm_r4.ip import positive_subtype_audience_label
            assert positive_subtype_audience_label(subtype) == label

    def test_no_prohibited_jargon_in_rule_results(self):
        ep = make_episode(dose="100")
        _, results = evaluate_one(ep, rules=(make_plan_actual_rule(),))
        for s in self._all_user_strings(results):
            for token in self.PROHIBITED:
                assert token not in s, f"prohibited {token!r} in {s!r}"

    def test_no_prohibited_jargon_in_adherence_results(self):
        alg = make_adherence_algorithm()
        occs = tuple(make_occurrence(f"O{i}", f"2026-01-0{i}")
                     for i in range(1, 6))
        _, results = evaluate_one(
            make_episode(), algorithms=(alg,), occurrences=occs,
            observations=(make_observation("OB1"),))
        for s in self._all_user_strings(results):
            for token in self.PROHIBITED:
                assert token not in s, f"prohibited {token!r} in {s!r}"

    def test_query_never_states_confirmed_pd(self):
        ep = make_episode(dose="100")
        _, results = evaluate_one(ep, rules=(make_plan_actual_rule(),))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        for part in (pos.query_refs[0].basis, pos.query_refs[0].finding,
                     pos.query_refs[0].action):
            assert "已构成" not in part
            assert "PD" not in part


# ===========================================================================
# Identity (frozen D03 §4)
# ===========================================================================

class TestIdentity:
    def test_same_input_same_identity(self):
        ep = make_episode(dose="100")
        rule = make_plan_actual_rule()
        _, res1 = evaluate_one(ep, rules=(rule,))
        _, res2 = evaluate_one(ep, rules=(rule,))
        id1 = [r for r in res1 if r.l1_disposition == L1Disposition.POSITIVE][0]
        id2 = [r for r in res2 if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert (id1.r2_candidates[0].detail["risk_identity_id"]
                == id2.r2_candidates[0].detail["risk_identity_id"])

    def test_rule_version_change_different_identity(self):
        ep = make_episode(dose="100")
        r1 = make_plan_actual_rule(rule_id="R-IP-V")
        r2 = ProtocolExposureRule(
            rule_id="R-IP-V", rule_version="v2", clause_locator="P20-2",
            rule_content_hash="rc-plan-02", rule_lineage="rl-plan-02",
            rule_type="plan_actual", applicable_treatment_role="active",
            applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-03-31",
            window_start_inclusive=True, window_end_inclusive=True,
            planned_dose="50", planned_dose_unit="mg",
            planned_dosage_form="tablet", planned_route="口服",
            planned_frequency="每日一次",
            priority_on_hit="high", priority_rationale="r")
        _, res1 = evaluate_one(ep, rules=(r1,))
        _, res2 = evaluate_one(ep, rules=(r2,))
        id1 = [r for r in res1 if r.l1_disposition == L1Disposition.POSITIVE][0]
        id2 = [r for r in res2 if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert (id1.r2_candidates[0].detail["risk_identity_id"]
                != id2.r2_candidates[0].detail["risk_identity_id"])
        # Stable cores stay equal (classifier excludes versions).
        assert (id1.r2_candidates[0].detail["stable_core"]
                == id2.r2_candidates[0].detail["stable_core"])

    def test_classifier_excludes_versions_and_hashes(self):
        ep = make_episode(dose="100")
        rule = make_plan_actual_rule()
        _, results = evaluate_one(ep, rules=(rule,))
        pos = [r for r in results if r.l1_disposition == L1Disposition.POSITIVE][0]
        cand = pos.r2_candidates[0]
        assert "rc-plan-01" not in cand.detail["classifier"]
        assert "rl-plan-01" not in cand.detail["classifier"]
        assert "asg-hash-01" not in cand.detail["classifier"]

    def test_identity_uses_make_risk_identity(self):
        ep = make_episode(dose="100")
        rule = make_plan_actual_rule()
        _, results = evaluate_one(ep, rules=(rule,))
        pos = [r for r in results if r.l1_disposition == L1Disposition.POSITIVE][0]
        cand = pos.r2_candidates[0]
        expected = make_risk_identity(
            project_id=PROJECT_ID, subject_ref="SYN-001",
            domain=D03_DOMAIN, scope=cand.detail["scope"],
            classifier=cand.detail["classifier"])
        assert expected.risk_identity_id == cand.detail["risk_identity_id"]

    def test_scope_includes_site_precision_role_and_lineage(self):
        ep = make_episode(dose="100")
        rule = make_plan_actual_rule()
        _, results = evaluate_one(ep, rules=(rule,))
        pos = [r for r in results if r.l1_disposition == L1Disposition.POSITIVE][0]
        cand = pos.r2_candidates[0]
        scope = cand.detail["scope"]
        assert any("site:SITE01" in s for s in scope)
        assert any("role:active" in s for s in scope)
        assert any("ph:treatment" in s for s in scope)
        assert any("rule:R-IP-01/" in s for s in scope)
        assert any("asg:ASSIGN-01/" in s for s in scope)
        assert any("dp:" in s for s in scope)


# ===========================================================================
# Protocol + ledger materialization
# ===========================================================================

class TestProtocolAndLedger:
    def test_satisfies_risk_domain_unit_result(self):
        r = evaluate_ip_unit(
            project_id=PROJECT_ID,
            expanded=IPUnitExpanded(
                episode=make_episode(),
                control_item="role_phase", control_token="role_phase:none",
                risk_family="treatment_role_phase",
                resolution=AssignmentResolution(status="missing",
                                                reason="gap")))
        assert isinstance(r, RiskDomainUnitResult)

    def test_to_unit_evaluation_not_evaluable(self):
        r = evaluate_ip_unit(
            project_id=PROJECT_ID,
            expanded=IPUnitExpanded(
                episode=make_episode(),
                control_item="role_phase", control_token="role_phase:none",
                risk_family="treatment_role_phase",
                resolution=AssignmentResolution(status="missing",
                                                reason="gap")))
        ue = r.to_unit_evaluation()
        assert isinstance(ue, UnitEvaluation)
        assert ue.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_to_unit_evaluation_positive_requires_provenance(self):
        ep = make_episode(dose="100")
        _, results = evaluate_one(ep, rules=(make_plan_actual_rule(),))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        ue = pos.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rl-plan-01")
        assert ue.l1_disposition == L1Disposition.POSITIVE
        with pytest.raises(UnitJoinError):
            pos.to_unit_evaluation()

    def test_ledger_counts_expected_units_exactly_once(self):
        from mm_r4.coverage import CoverageLedger, ExpectedSet
        ep = make_episode(dose="100")
        rules = (make_plan_actual_rule(),)
        expansion, results = evaluate_one(ep, rules=rules)
        units = tuple(eu.build_unit(PROJECT_ID) for eu in expansion.units)
        expected = ExpectedSet.from_units(
            units, domain_id=D03_DOMAIN, run_id="run-synthetic-001")
        ledger = CoverageLedger(expected_set=expected)
        by_id = {r.unit_id: r for r in results}
        for eu in expansion.units:
            unit = eu.build_unit(PROJECT_ID)
            ledger.assign(by_id[unit.unit_id].to_unit_evaluation(
                provenance_snapshot_id=SNAPSHOT_ID,
                provenance_rule_lineage="rl-plan-01"))
        summary = ledger.close_and_summarize()
        assert summary.expected_units == len(units)
        assert summary.assigned_units == len(units)


# ===========================================================================
# Slice rollup + sibling coexistence (frozen D03 §10, §11 item 11)
# ===========================================================================

class TestSliceRollupAndCoexistence:
    def test_positive_and_not_evaluable_siblings_coexist(self):
        ep = make_episode(dose="100")
        alg = make_adherence_algorithm()
        rules = (make_plan_actual_rule(),)
        expansion, results = evaluate_one(
            ep, rules=rules, algorithms=(alg,),
            observations=(make_observation("OB1"),))
        assert any(r.l1_disposition == L1Disposition.POSITIVE
                   for r in results)
        assert any(r.l1_disposition == L1Disposition.NOT_EVALUABLE
                   and "不得推断漏服" in r.not_evaluable_reason
                   for r in results)

    def test_episode_rollup_preserves_sibling_flags(self):
        from mm_r4.ip import IPSliceResult
        ep = make_episode(dose="100")
        alg = make_adherence_algorithm()
        rules = (make_plan_actual_rule(),)
        expansion, results = evaluate_one(
            ep, rules=rules, algorithms=(alg,),
            observations=(make_observation("OB1"),))
        sr = IPSliceResult(
            subject_ref="SYN-001", unit_results=tuple(results),
            expected_set_hash=expansion.expected_set_hash)
        rollups = sr.episode_rollups(expansion)
        assert len(rollups) == 1
        rollup = rollups[0]
        assert rollup.has_positive
        assert rollup.has_not_evaluable
        assert rollup.has_negative      # role_phase unit evaluates negative
        assert len(rollup.child_unit_ids) == len(expansion.unit_ids)

    def test_slice_result_counts_and_grouping(self):
        ep1 = make_episode(dose="100")
        ep2 = make_episode(episode_key="EP-2", record_id="EX#2",
                           subject="SYN-002", assignment_id="ASSIGN-02")
        rules = (make_plan_actual_rule(),)
        out = evaluate_ip_slice(
            project_id=PROJECT_ID, episodes=(ep1, ep2),
            assignments=(make_assignment(),
                         make_assignment(assignment_id="ASSIGN-02",
                                         subject="SYN-002")),
            active_rules=rules, role_coverage=DEFAULT_ROLE_COVERAGE,
            snapshot_id=SNAPSHOT_ID)
        assert set(out) == {"SYN-001", "SYN-002"}
        sr1 = out["SYN-001"]
        assert sr1.positive_count >= 1
        assert sr1.negative_count >= 1
        assert sr1.not_evaluable_count == 0
        # Episodes without rules still carry the role_phase unit.
        sr2 = out["SYN-002"]
        assert sr2.positive_count == 0
        assert sr2.negative_count >= 1

    def test_identity_ambiguous_scope_for_ambiguous_binding(self):
        # A rule/algo version supersede carries a distinct lineage; the
        # ambiguous binding itself stays boundary with a candidate.
        ep = make_episode(assignment_link="none", assignment_id="")
        _, results = evaluate_one(
            ep,
            assignments=(make_assignment(assignment_id="ASSIGN-01"),
                         make_assignment(assignment_id="ASSIGN-02")),
            mapping=make_mapping())
        bnd = [r for r in results
               if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(bnd) >= 1
        assert len(bnd[0].r2_candidates) == 1
