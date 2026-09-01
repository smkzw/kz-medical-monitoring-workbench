"""R4-D02 CM slice deterministic tests (worker_02, round 2).

Proves the frozen D02 CM domain engine (``FROZEN_R4_D02_CONTRACT_V1``)
implements the mandatory contract with deterministic synthetic-only
assertions, covering all round-2 corrections:

* Versioned input dataclasses enforce their invariants.
* Expected-set expansion follows the compound ingredient x rule order,
  with mandatory ``ingredient_resolution`` units for unresolved slots.
* All five L1 dispositions are exercised: positive (six subtypes),
  negative (definitive identity non-match + outside window + conditions
  met), boundary (endpoint/partial date), not_evaluable (coverage gap,
  unresolved component, unconfirmed role/phase), and not_applicable
  (confirmed phase outside rule applicability).
* Stable classifier / stable-core vs versioned scope/lineage identity.
* Rule-target granularity: ingredient-exact > category > product-type.
* Indication sufficiency with explicit linkage-coverage gate, role
  confirmation gate, subject/temporal ownership, and both subtypes.
* Restricted-condition four-state (met/unmet/unevaluable/boundary).
* Rule-backed record-consistency and AE/MH/IP action-relationship paths.
* Query provenance includes CM source + identity evidence locators.
* Cross-domain evidence refs are canonical and carry no lifecycle state.
* CMUnitResult satisfies the neutral RiskDomainUnitResult protocol and
  materializes a full UnitEvaluation for the CoverageLedger.
* Episode L2 source count counts unique CM source records.
* User-visible result strings avoid prohibited research jargon.

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

from mm_r4.cm import (  # noqa: E402
    CMSliceError,
    CONFIRMATION_CONFIRMED,
    CONFIRMATION_UNRESOLVED,
    CMIntervalDescriptor,
    CMSemanticRecord,
    CMUnitResult,
    D02_DOMAIN,
    D02PriorityPolicy,
    IngredientBinding,
    MedicationEpisode,
    MedicationIdentityBinding,
    MedicationMatchStrategy,
    POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED,
    POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY,
    POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
    POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH,
    POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT,
    POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
    ProtocolMedicationRule,
    TreatmentInterpretationEvidence,
    expand_cm_expected_set,
    evaluate_cm_unit,
)
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    RiskDomainUnitResult,
    SourceLocator,
    UnitEvaluation,
    UnitJoinError,
    cross_domain_evidence_content_hash,
)
from mm_r2.identity import make_risk_identity  # noqa: E402


# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"


# ===========================================================================
# Fixtures / helpers
# ===========================================================================

def make_locator(
    record_id: str, table_semantic: str = "recorded_cm",
    snapshot_id: str = SNAPSHOT_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_strategy(version: str = "ms-v1",
                  chash: str = "sch1") -> MedicationMatchStrategy:
    return MedicationMatchStrategy(
        version=version, strategy_content_hash=chash)


def make_policy(version: str = "pp-v1") -> D02PriorityPolicy:
    return D02PriorityPolicy(
        version=version, policy_content_hash="pch1",
        rationale="synthetic default policy")


def make_binding(
    ingredients, original_name="合成药物A", normalized_name="synthetic_a",
    record_id="dict-1", confirmation=CONFIRMATION_CONFIRMED,
) -> MedicationIdentityBinding:
    return MedicationIdentityBinding(
        original_name=original_name, normalized_name=normalized_name,
        ingredients=tuple(ingredients),
        dictionary_name="DICT", dictionary_version="v1",
        dictionary_content_hash="dh1",
        evidence_locator=make_locator(record_id, "medication_identity"),
        confirmation_status=confirmation)


def make_episode(
    record_id="CM#9", subject="SYN-001", binding=None,
    cm_start="2026-01-03", cm_end="2026-01-05", ongoing=False,
    phase="treatment", treatment_role="treatment",
    treatment_role_confirmed=True, indication_text="", indication_concept="",
    indication_mappable=None, dose="100", dose_unit="mg", route="口服",
    frequency="每日一次",
    study_phase="treatment", study_phase_confirmed=True,
    indication_treatment_of_study_event=False,
    treatment_interpretation_evidence=(),
    stable_treatment_evidence_complete=False,
    stable_treatment_duration_confirmed=False,
    dose_frequency_unchanged=False,
) -> MedicationEpisode:
    if binding is None:
        binding = make_binding((IngredientBinding(ingredient="ingredientA"),))
    return MedicationEpisode(
        episode_id=f"ep-{record_id}", subject_ref=subject, site_ref=SITE_REF,
        stable_cm_source_event_key=f"recorded_cm:{record_id}",
        source_locator=make_locator(record_id),
        identity_binding=binding,
        interval=CMIntervalDescriptor(
            cm_start=cm_start, cm_end=cm_end, ongoing=ongoing,
            applicable_phase=phase),
        dose=dose, dose_unit=dose_unit, route=route, frequency=frequency,
        treatment_role=treatment_role,
        treatment_role_confirmed=treatment_role_confirmed,
        indication_text=indication_text,
        indication_concept=indication_concept,
        indication_mappable=indication_mappable,
        study_phase=study_phase,
        study_phase_confirmed=study_phase_confirmed,
        indication_treatment_of_study_event=indication_treatment_of_study_event,
        treatment_interpretation_evidence=tuple(
            treatment_interpretation_evidence),
        stable_treatment_evidence_complete=stable_treatment_evidence_complete,
        stable_treatment_duration_confirmed=stable_treatment_duration_confirmed,
        dose_frequency_unchanged=dose_frequency_unchanged)


def make_prohibited_rule(
    rule_id="R-CM-007", target_kind="ingredient", target_value="ingredientA",
    window_start="2026-01-01", window_end="2026-06-30",
    start_inc=True, end_inc=True, priority="high",
    applicable_phases=("treatment",),
) -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P12-4",
        rule_type="prohibited", target_kind=target_kind,
        target_value=target_value, applicable_phases=applicable_phases,
        window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        priority_on_hit=priority, priority_rationale="禁止成分",
        rule_content_hash="rc1", rule_lineage="rl1")


def make_restricted_rule(
    rule_id="R-CM-008", target_kind="ingredient", target_value="ingredientB",
    rescue_exception=True,
) -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id=rule_id, rule_version="v1", clause_locator="P12-5",
        rule_type="restricted", target_kind=target_kind,
        target_value=target_value, applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-06-30",
        window_start_inclusive=True, window_end_inclusive=True,
        rescue_exception=rescue_exception,
        priority_on_hit="medium", priority_rationale="限制成分",
        rule_content_hash="rc2", rule_lineage="rl2")


def make_record_consistency_rule(
    comparison_field="dose", expected_values=("50",),
) -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id="R-CM-REC-001", rule_version="v1",
        clause_locator="P12-6", rule_type="record_consistency",
        target_kind="ingredient", target_value="ingredientA",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-06-30",
        window_start_inclusive=True, window_end_inclusive=True,
        comparison_field=comparison_field,
        expected_values=expected_values,
        priority_on_hit="medium", priority_rationale="方案用药要求",
        rule_content_hash="rc-record-v1", rule_lineage="rl-record-v1")


def make_action_relationship_rule(
    expected_actions=("continue",), related_role="reported_ae",
    related_concept="headache",
) -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id="R-CM-ACT-001", rule_version="v1",
        clause_locator="P12-7", rule_type="action_relationship",
        target_kind="ingredient", target_value="ingredientA",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-06-30",
        window_start_inclusive=True, window_end_inclusive=True,
        related_role=related_role, related_concept=related_concept,
        expected_actions=expected_actions,
        priority_on_hit="high", priority_rationale="关键处置关系",
        rule_content_hash="rc-action-v1", rule_lineage="rl-action-v1")


_NO_POLICY = object()


def evaluate_one(episode, rules=(), strategy=None, policy=_NO_POLICY,
                 evidence_records=(), ip_records=(),
                 linkage_coverage_complete=False,
                 relationship_coverage_complete=False):
    if strategy is None:
        strategy = make_strategy()
    if policy is _NO_POLICY:
        policy = make_policy()
    expansion = expand_cm_expected_set(
        project_id=PROJECT_ID, episodes=(episode,),
        active_rules=rules, strategy=strategy)
    assert expansion.count > 0, "expected at least one expanded unit"
    results = []
    for eu in expansion.units:
        r = evaluate_cm_unit(
            project_id=PROJECT_ID, expanded=eu,
            evidence_records=evidence_records, strategy=strategy,
            priority_policy=policy, snapshot_id=SNAPSHOT_ID,
            ip_exposure_records=ip_records,
            linkage_coverage_complete=linkage_coverage_complete,
            relationship_coverage_complete=relationship_coverage_complete)
        results.append(r)
    return expansion, results


# ===========================================================================
# Input dataclass invariants
# ===========================================================================

class TestInputInvariants:
    def test_ingredient_binding_confirmed_requires_name(self):
        with pytest.raises(CMSliceError):
            IngredientBinding(ingredient="", confirmation=CONFIRMATION_CONFIRMED)

    def test_ingredient_binding_unresolved_requires_slot(self):
        with pytest.raises(CMSliceError):
            IngredientBinding(ingredient="", confirmation=CONFIRMATION_UNRESOLVED)

    def test_identity_binding_requires_dictionary_hash(self):
        with pytest.raises(CMSliceError):
            MedicationIdentityBinding(
                original_name="x", normalized_name="x",
                ingredients=(IngredientBinding(ingredient="i"),),
                dictionary_name="D", dictionary_version="v1",
                dictionary_content_hash="",
                evidence_locator=make_locator("d1"))

    def test_rule_requires_priority_rationale(self):
        with pytest.raises(CMSliceError):
            ProtocolMedicationRule(
                rule_id="r1", rule_version="v1", clause_locator="c",
                rule_type="prohibited", target_kind="ingredient",
                target_value="i", applicable_phases=("treatment",),
                priority_on_hit="high", priority_rationale="",
                rule_content_hash="h", rule_lineage="l")

    def test_strategy_requires_content_hash(self):
        with pytest.raises(CMSliceError):
            MedicationMatchStrategy(version="v1", strategy_content_hash="")


# ===========================================================================
# Expected-set expansion (frozen D02 §4.1)
# ===========================================================================

class TestExpectedSetExpansion:
    def test_single_ingredient_single_rule_two_units(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        exp = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule,), strategy=make_strategy())
        assert exp.count == 2
        assert not exp.has_not_evaluable()

    def test_compound_confirmed_plus_unresolved(self):
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="comp2",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule()
        exp = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule,), strategy=make_strategy())
        assert exp.count == 3
        assert exp.has_not_evaluable()

    def test_all_unresolved_compound_emits_resolution_units(self):
        binding = make_binding((
            IngredientBinding(component_slot="c1",
                              confirmation=CONFIRMATION_UNRESOLVED),
            IngredientBinding(component_slot="c2",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule()
        exp = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule,), strategy=make_strategy())
        assert exp.count == 2
        assert all(u.is_ingredient_resolution for u in exp.units)

    def test_expected_set_hash_stable(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        strat = make_strategy()
        exp1 = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule,), strategy=strat)
        exp2 = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule,), strategy=strat)
        assert exp1.expected_set_hash == exp2.expected_set_hash


# ===========================================================================
# Five L1 dispositions
# ===========================================================================

class TestFiveDispositions:
    def test_positive_prohibited_match(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].positive_subtype == POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH
        assert positives[0].monitoring_priority == "high"

    def test_negative_definitive_ingredient_exact_non_match(self):
        """Correction 2: confirmed ingredient-exact binding that differs
        from an ingredient-exact rule target is a deterministic negative."""
        binding = make_binding((IngredientBinding(ingredient="ingredientZ"),))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule(target_value="ingredientA")
        _, results = evaluate_one(ep, (rule,))
        rule_results = [r for r in results if r.unit_id != [
            eu.build_unit(PROJECT_ID, make_strategy()).unit_id
            for eu in expand_cm_expected_set(
                project_id=PROJECT_ID, episodes=(ep,),
                active_rules=(rule,), strategy=make_strategy()).units
            if eu.risk_family == "indication_check"][0]]
        negs = [r for r in rule_results
                if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(negs) == 1

    def test_negative_outside_window(self):
        ep = make_episode(cm_start="2026-07-10", cm_end="2026-07-12")
        rule = make_prohibited_rule(
            window_start="2026-01-01", window_end="2026-06-30")
        _, results = evaluate_one(ep, (rule,))
        negs = [r for r in results
                if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(negs) >= 1

    def test_not_evaluable_unresolved_component(self):
        binding = make_binding((
            IngredientBinding(component_slot="c1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "成分尚未确认" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert len(nes[0].r2_candidates) == 0

    def test_boundary_endpoint_inclusivity_unstated(self):
        ep = make_episode(cm_start="2026-01-01", cm_end="2026-01-02")
        rule = make_prohibited_rule(
            window_start="2026-01-01", window_end="2026-06-30",
            start_inc=None, end_inc=True)
        _, results = evaluate_one(ep, (rule,))
        boundaries = [r for r in results
                      if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(boundaries) == 1

    def test_boundary_partial_date_possibly_overlaps(self):
        ep = make_episode(cm_start="2026-01", cm_end="2026-02")
        rule = make_prohibited_rule(
            window_start="2026-01-15", window_end="2026-06-30")
        _, results = evaluate_one(ep, (rule,))
        boundaries = [r for r in results
                      if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(boundaries) == 1

    def test_not_applicable_confirmed_phase_outside(self):
        """Correction 1: confirmed study phase outside rule applicability
        -> not_applicable with no candidate/Query."""
        ep = make_episode(study_phase="followup", study_phase_confirmed=True)
        rule = make_prohibited_rule(applicable_phases=("treatment",))
        _, results = evaluate_one(ep, (rule,))
        nas = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_APPLICABLE]
        assert len(nas) == 1
        assert len(nas[0].r2_candidates) == 0
        assert len(nas[0].query_refs) == 0

    def test_not_evaluable_missing_phase(self):
        """Correction 1: missing/unconfirmed phase -> not_evaluable."""
        ep = make_episode(study_phase="", study_phase_confirmed=False)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "研究阶段" in r.not_evaluable_reason]
        assert len(nes) >= 1


# ===========================================================================
# Restricted-condition tri-state (correction 7)
# ===========================================================================

class TestRestrictedTriState:
    def test_restricted_unmet_rescue_positive(self):
        """Confirmed unmet rescue condition -> positive."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(binding=binding, treatment_role="treatment")
        rule = make_restricted_rule(rescue_exception=True)
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].positive_subtype == POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH

    def test_restricted_met_rescue_negative(self):
        """Confirmed met rescue condition -> negative."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(binding=binding, treatment_role="rescue")
        rule = make_restricted_rule(rescue_exception=True)
        _, results = evaluate_one(ep, (rule,))
        negs = [r for r in results
                if r.l1_disposition == L1Disposition.NEGATIVE
                and any(ev.evidence_role == "recorded_cm" for ev in r.evidence)]
        assert len(negs) >= 1

    def test_restricted_missing_role_not_evaluable(self):
        """Missing role -> not_evaluable."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(binding=binding, treatment_role="",
                          treatment_role_confirmed=False)
        rule = make_restricted_rule(rescue_exception=True)
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "角色" in r.not_evaluable_reason]
        assert len(nes) >= 1

    def test_restricted_stable_treatment_needs_full_evidence(self):
        """Stable treatment accepted only with duration + dose/frequency
        unchanged evidence; treatment_role_confirmed alone is not enough."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        # Without stable_treatment_duration_confirmed -> not_evaluable.
        ep = make_episode(binding=binding, treatment_role="treatment",
                          treatment_role_confirmed=True,
                          stable_treatment_duration_confirmed=False,
                          dose_frequency_unchanged=False)
        rule = ProtocolMedicationRule(
            rule_id="R-ST", rule_version="v1", clause_locator="P15",
            rule_type="restricted", target_kind="ingredient",
            target_value="ingredientB", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            stable_treatment_exception=True,
            priority_on_hit="medium", priority_rationale="限制稳定治疗",
            rule_content_hash="rc3", rule_lineage="rl3")
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert len(nes) >= 1
        # With full evidence -> negative.
        ep2 = make_episode(binding=binding, treatment_role="treatment",
                           treatment_role_confirmed=True,
                           stable_treatment_evidence_complete=True,
                           stable_treatment_duration_confirmed=True,
                           dose_frequency_unchanged=True)
        _, results2 = evaluate_one(ep2, (rule,))
        negs = [r for r in results2
                if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(negs) >= 1

    def test_restricted_stable_treatment_confirmed_unmet_is_positive(self):
        """A completed condition assessment may prove the stable-treatment
        exception unmet; missing assessment evidence may not."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(
            binding=binding, treatment_role="treatment",
            treatment_role_confirmed=True,
            stable_treatment_evidence_complete=True,
            stable_treatment_duration_confirmed=False,
            dose_frequency_unchanged=True)
        rule = ProtocolMedicationRule(
            rule_id="R-ST-UNMET", rule_version="v1", clause_locator="P15-2",
            rule_type="restricted", target_kind="ingredient",
            target_value="ingredientB", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            stable_treatment_exception=True,
            priority_on_hit="medium", priority_rationale="限制稳定治疗",
            rule_content_hash="rc3-unmet", rule_lineage="rl3-unmet")
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].positive_subtype == (
            POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH)

    def test_competing_stable_and_new_start_interpretations_are_boundary(self):
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        evidence = (
            TreatmentInterpretationEvidence(
                interpretation="stable_treatment",
                evidence_locator=make_locator("CM-history", "recorded_cm"),
                evidence_version="listing-v1",
                evidence_content_hash="stable-evidence-v1"),
            TreatmentInterpretationEvidence(
                interpretation="new_start",
                evidence_locator=make_locator("DOSE-change", "recorded_cm"),
                evidence_version="listing-v1",
                evidence_content_hash="new-start-evidence-v1"),
        )
        ep = make_episode(
            binding=binding, treatment_role="stable_treatment",
            treatment_role_confirmed=True,
            treatment_interpretation_evidence=evidence)
        rule = ProtocolMedicationRule(
            rule_id="R-ST-AMB", rule_version="v1", clause_locator="P15-4",
            rule_type="restricted", target_kind="ingredient",
            target_value="ingredientB", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            stable_treatment_exception=True, priority_on_hit="medium",
            priority_rationale="限制稳定治疗",
            rule_content_hash="rc-st-amb", rule_lineage="rl-st-amb")
        _, results = evaluate_one(ep, (rule,))
        boundaries = [r for r in results
                      if r.l1_disposition == L1Disposition.BOUNDARY]
        assert len(boundaries) == 1
        assert "两种解释均有来源支持" in boundaries[0].boundary_reason
        assert len(boundaries[0].r2_candidates) == 1

    def test_restricted_role_gap_outranks_endpoint_boundary(self):
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(
            binding=binding, cm_start="2026-01-01", cm_end="2026-06-30",
            treatment_role="", treatment_role_confirmed=False)
        rule = ProtocolMedicationRule(
            rule_id="R-BOUND-ROLE", rule_version="v1", clause_locator="P15-3",
            rule_type="restricted", target_kind="ingredient",
            target_value="ingredientB", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=None, window_end_inclusive=True,
            rescue_exception=True, priority_on_hit="medium",
            priority_rationale="限制抢救用药",
            rule_content_hash="rc-bound-role", rule_lineage="rl-bound-role")
        _, results = evaluate_one(ep, (rule,))
        rule_results = [r for r in results if "角色" in r.not_evaluable_reason]
        assert len(rule_results) == 1
        assert rule_results[0].l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_restricted_unknown_condition_token_fails_closed(self):
        """Unknown allowed-condition token -> not_evaluable."""
        binding = make_binding((IngredientBinding(ingredient="ingredientB"),))
        ep = make_episode(binding=binding, treatment_role="treatment")
        rule = ProtocolMedicationRule(
            rule_id="R-UNK", rule_version="v1", clause_locator="P16",
            rule_type="restricted", target_kind="ingredient",
            target_value="ingredientB", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            allowed_conditions=("bogus_condition",),
            priority_on_hit="medium", priority_rationale="未知条件",
            rule_content_hash="rc4", rule_lineage="rl4")
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "未知" in r.not_evaluable_reason]
        assert len(nes) >= 1


# ===========================================================================
# J07 super-class granularity (frozen D02 §6)
# ===========================================================================

class TestRecordConsistencyAndActionRelationship:
    """Executable coverage for frozen positive subtypes 5 and 6."""

    def test_specialized_rule_invariants_fail_closed(self):
        base = dict(
            rule_id="R-BAD", rule_version="v1", clause_locator="P1",
            target_kind="ingredient", target_value="ingredientA",
            applicable_phases=("treatment",),
            priority_on_hit="medium", priority_rationale="synthetic",
            rule_content_hash="bad-hash", rule_lineage="bad-lineage")
        with pytest.raises(CMSliceError, match="comparison_field"):
            ProtocolMedicationRule(
                **base, rule_type="record_consistency",
                expected_values=("50",))
        with pytest.raises(CMSliceError, match="related_role"):
            ProtocolMedicationRule(
                **base, rule_type="action_relationship",
                expected_actions=("continue",))
        with pytest.raises(CMSliceError, match="confirmed treatment"):
            CMSemanticRecord(
                role="reported_ae", concept="headache",
                locator=make_locator("AE#bad", "reported_ae"),
                subject_ref="SYN-001",
                relationship_confirmation=CONFIRMATION_CONFIRMED)

    def test_record_inconsistency_positive_and_matching_negative(self):
        rule = make_record_consistency_rule()
        ep = make_episode(dose="100")
        expansion, results = evaluate_one(ep, (rule,))
        record_units = [unit for unit in expansion.units
                        if unit.risk_family
                        == "medication_record_consistency"]
        assert len(record_units) == 1
        positives = [result for result in results
                     if result.positive_subtype
                     == POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY]
        assert len(positives) == 1
        positive = positives[0]
        assert positive.l1_disposition == L1Disposition.POSITIVE
        assert positive.monitoring_priority == "medium"
        assert len(positive.r2_candidates) == 1
        assert len(positive.query_refs) == 1
        query = positive.query_refs[0]
        assert "方案规则 R-CM-REC-001" in query.basis
        assert "剂量记录为 100" in query.finding
        assert set(query.source_locator_ids) == {
            ep.source_locator.locator_id(),
            ep.identity_binding.evidence_locator.locator_id(),
        }

        _, matching_results = evaluate_one(
            make_episode(dose="50"), (rule,))
        record_results = [result for result in matching_results
                          if "剂量与方案规则" in
                          " ".join(ev.uncertainty_note
                                   for ev in result.evidence)]
        assert len(record_results) == 1
        assert record_results[0].l1_disposition == L1Disposition.NEGATIVE
        assert not record_results[0].r2_candidates
        assert not record_results[0].query_refs

    def test_record_inconsistency_missing_actual_is_not_evaluable(self):
        _, results = evaluate_one(
            make_episode(route=""),
            (make_record_consistency_rule(
                comparison_field="route", expected_values=("口服",)),))
        relevant = [result for result in results
                    if "给药途径缺失" in result.not_evaluable_reason]
        assert len(relevant) == 1
        assert relevant[0].l1_disposition == L1Disposition.NOT_EVALUABLE
        assert not relevant[0].r2_candidates
        assert not relevant[0].query_refs

    def test_action_relationship_positive_has_exact_link_and_provenance(self):
        ep = make_episode()
        record = CMSemanticRecord(
            role="reported_ae", concept="headache",
            locator=make_locator("AE#1", "reported_ae"),
            subject_ref=ep.subject_ref, site_ref=ep.site_ref,
            event_date_raw="2026-01-04",
            action_value="stop",
            linked_cm_source_event_key=ep.stable_cm_source_event_key,
            relationship_confirmation=CONFIRMATION_CONFIRMED)
        _, results = evaluate_one(
            ep, (make_action_relationship_rule(),),
            evidence_records=(record,),
            relationship_coverage_complete=True)
        positives = [result for result in results
                     if result.positive_subtype == (
                         POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT)]
        assert len(positives) == 1
        positive = positives[0]
        assert positive.monitoring_priority == "high"
        assert any(ev.evidence_role == "reported_ae"
                   and ev.locator == record.locator
                   for ev in positive.evidence)
        query = positive.query_refs[0]
        assert "处置记录为 stop" in query.finding
        assert set(query.source_locator_ids) == {
            ep.source_locator.locator_id(),
            ep.identity_binding.evidence_locator.locator_id(),
            record.locator.locator_id(),
        }

    def test_action_relationship_match_negative_and_incomplete_fail_closed(self):
        ep = make_episode()
        matching = CMSemanticRecord(
            role="reported_ae", concept="headache",
            locator=make_locator("AE#2", "reported_ae"),
            subject_ref=ep.subject_ref, site_ref=ep.site_ref,
            event_date_raw="2026-01-04",
            action_value="continue",
            linked_cm_source_event_key=ep.stable_cm_source_event_key,
            relationship_confirmation=CONFIRMATION_CONFIRMED)
        rule = make_action_relationship_rule()
        _, incomplete_results = evaluate_one(
            ep, (rule,), evidence_records=(matching,))
        incomplete = [result for result in incomplete_results
                      if "来源覆盖不完整" in result.not_evaluable_reason]
        assert len(incomplete) == 1
        assert not incomplete[0].r2_candidates

        _, complete_results = evaluate_one(
            ep, (rule,), evidence_records=(matching,),
            relationship_coverage_complete=True)
        negatives = [result for result in complete_results
                     if result.l1_disposition == L1Disposition.NEGATIVE
                     and any(ev.evidence_role == "reported_ae"
                             for ev in result.evidence)]
        assert len(negatives) == 1
        assert not negatives[0].query_refs

    def test_action_relationship_competing_records_are_boundary(self):
        ep = make_episode()
        records = (
            CMSemanticRecord(
                role="reported_ae", concept="headache",
                locator=make_locator("AE#3", "reported_ae"),
                subject_ref=ep.subject_ref, site_ref=ep.site_ref,
                event_date_raw="2026-01-04",
                action_value="continue",
                linked_cm_source_event_key=ep.stable_cm_source_event_key,
                relationship_confirmation=CONFIRMATION_CONFIRMED),
            CMSemanticRecord(
                role="reported_ae", concept="headache",
                locator=make_locator("AE#4", "reported_ae"),
                subject_ref=ep.subject_ref, site_ref=ep.site_ref,
                event_date_raw="2026-01-04",
                action_value="stop",
                linked_cm_source_event_key=ep.stable_cm_source_event_key,
                relationship_confirmation=CONFIRMATION_CONFIRMED),
        )
        _, results = evaluate_one(
            ep, (make_action_relationship_rule(),),
            evidence_records=records,
            relationship_coverage_complete=True)
        boundaries = [result for result in results
                      if result.l1_disposition == L1Disposition.BOUNDARY]
        assert len(boundaries) == 1
        assert "同时存在一致与冲突" in boundaries[0].boundary_reason
        assert boundaries[0].audience_label == (
            "用药与处置记录关系待核实（边界）")
        assert not boundaries[0].query_refs

    def test_action_relationship_accepts_separate_ip_evidence_channel(self):
        ep = make_episode()
        ip_record = CMSemanticRecord(
            role="ip_exposure", concept="study_drug",
            locator=make_locator("EX#2", "ip_exposure"),
            subject_ref=ep.subject_ref, site_ref=ep.site_ref,
            event_date_raw="2026-01-04", action_value="dose_interrupted",
            linked_cm_source_event_key=ep.stable_cm_source_event_key,
            relationship_confirmation=CONFIRMATION_CONFIRMED)
        rule = make_action_relationship_rule(
            expected_actions=("dose_continued",),
            related_role="ip_exposure", related_concept="study_drug")
        _, results = evaluate_one(
            ep, (rule,), ip_records=(ip_record,),
            relationship_coverage_complete=True)
        positives = [result for result in results
                     if result.positive_subtype == (
                         POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT)]
        assert len(positives) == 1
        assert any(ev.evidence_role == "ip_exposure"
                   for ev in positives[0].evidence)

    def test_specialized_expected_set_units_are_distinct(self):
        ep = make_episode()
        expansion = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(make_record_consistency_rule(),
                          make_action_relationship_rule()),
            strategy=make_strategy())
        assert expansion.count == 3
        assert len(set(expansion.unit_ids)) == 3
        assert {unit.risk_family for unit in expansion.units} == {
            "medication_record_consistency",
            "treatment_action_relationship",
            "indication_check",
        }


class TestJ07Granularity:
    def test_j07_superclass_rule_can_match_j07_target(self):
        binding = make_binding((
            IngredientBinding(ingredient="vaccineX", categories=("J07",)),
        ))
        ep = make_episode(binding=binding)
        rule = ProtocolMedicationRule(
            rule_id="R-CM-VAC", rule_version="v1", clause_locator="P13",
            rule_type="prohibited", target_kind="category",
            target_value="J07", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            priority_on_hit="high", priority_rationale="禁用疫苗类",
            rule_content_hash="rcv", rule_lineage="rlv")
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1

    def test_j07_only_not_enough_for_live_vaccine_rule(self):
        binding = make_binding((
            IngredientBinding(ingredient="vaccineX", categories=("J07",)),
        ))
        ep = make_episode(binding=binding)
        rule = ProtocolMedicationRule(
            rule_id="R-CM-LV", rule_version="v1", clause_locator="P14",
            rule_type="prohibited", target_kind="product_type",
            target_value="live_attenuated", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            priority_on_hit="high", priority_rationale="禁用活疫苗",
            rule_content_hash="rcl", rule_lineage="rll")
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "product_type" in r.not_evaluable_reason]
        assert len(nes) == 1


# ===========================================================================
# Indication / AE-MH linkage with coverage gate (corrections 3, 4, 5, 6)
# ===========================================================================

class TestIndicationLinkage:
    def test_treatment_without_event_positive_needs_coverage_and_token(self):
        """Correction 3+5: subtype 2 requires linkage_coverage_complete AND
        indication_treatment_of_study_event=True."""
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].positive_subtype == POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD

    def test_indication_without_coverage_is_not_evaluable(self):
        """Correction 3: incomplete coverage -> not_evaluable, never positive."""
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=False)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "覆盖" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_indication_unexplained_subtype_1(self):
        """Correction 5: mappable role-confirmed but unexplained (no
        treatment-of-study-event token) -> subtype 1."""
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=False)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].positive_subtype == POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED

    def test_indication_priority_unknown_without_policy(self):
        """Correction 6: non-rule positive without D02PriorityPolicy ->
        unknown, not medium."""
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=False)
        _, results = evaluate_one(ep, (), policy=None,
                                  linkage_coverage_complete=True)
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1
        assert positives[0].monitoring_priority == "unknown"

    def test_treatment_with_matching_event_negative(self):
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment")
        ae_rec = CMSemanticRecord(
            role="reported_ae", concept="hypertension",
            locator=make_locator("AE#1", "reported_ae"),
            subject_ref="SYN-001", event_date_raw="2026-01-02")
        _, results = evaluate_one(ep, (), evidence_records=(ae_rec,),
                                  linkage_coverage_complete=True)
        negs = [r for r in results
                if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(negs) == 1

    def test_vague_indication_not_evaluable(self):
        ep = make_episode(
            indication_text="对症治疗", indication_concept="",
            indication_mappable=False, treatment_role="treatment")
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert len(nes) == 1

    def test_missing_indication_not_evaluable(self):
        ep = make_episode(indication_text="", indication_concept="",
                          indication_mappable=None)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "缺失" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_prophylaxis_confirmed_role_negative(self):
        """Correction 3/5: prophylaxis with confirmed role -> negative."""
        ep = make_episode(
            indication_text="预防接种", indication_concept="prophylaxis_vaccine",
            indication_mappable=True, treatment_role="prophylaxis")
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        negs = [r for r in results
                if r.l1_disposition == L1Disposition.NEGATIVE]
        assert len(negs) == 1

    def test_prophylaxis_unconfirmed_role_not_evaluable(self):
        """Correction 3: unconfirmed treatment role -> not_evaluable."""
        ep = make_episode(
            indication_text="预防接种", indication_concept="prophylaxis_vaccine",
            indication_mappable=True, treatment_role="prophylaxis",
            treatment_role_confirmed=False)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "角色" in r.not_evaluable_reason]
        assert len(nes) == 1

    def test_cross_subject_record_not_used_as_counterevidence(self):
        """Correction 4: another participant's record must not prove a
        matching event."""
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        ae_rec = CMSemanticRecord(
            role="reported_ae", concept="hypertension",
            locator=make_locator("AE#2", "reported_ae"),
            subject_ref="SYN-002", event_date_raw="2026-01-02")
        _, results = evaluate_one(ep, (), evidence_records=(ae_rec,),
                                  linkage_coverage_complete=True)
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1

    def test_temporally_uninterpretable_record_fails_closed(self):
        """Correction 4: a same-concept record with an unparseable date
        fails closed instead of silently matching."""
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        ae_rec = CMSemanticRecord(
            role="reported_ae", concept="hypertension",
            locator=make_locator("AE#3", "reported_ae"),
            subject_ref="SYN-001", event_date_raw="garbage_date")
        _, results = evaluate_one(ep, (), evidence_records=(ae_rec,),
                                  linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "日期" in r.not_evaluable_reason]
        assert len(nes) == 1


# ===========================================================================
# Identity (frozen D02 §4.2)
# ===========================================================================

class TestIdentity:
    def test_same_event_same_lineage_same_identity(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        strat = make_strategy()
        _, results1 = evaluate_one(ep, (rule,), strategy=strat)
        _, results2 = evaluate_one(ep, (rule,), strategy=strat)
        pos1 = [r for r in results1
                if r.l1_disposition == L1Disposition.POSITIVE][0]
        pos2 = [r for r in results2
                if r.l1_disposition == L1Disposition.POSITIVE][0]
        id1 = pos1.r2_candidates[0].detail["risk_identity_id"]
        id2 = pos2.r2_candidates[0].detail["risk_identity_id"]
        assert id1 == id2

    def test_lineage_change_different_identity(self):
        ep = make_episode()
        r1 = ProtocolMedicationRule(
            rule_id="R-CM-007", rule_version="v1", clause_locator="P12-4",
            rule_type="prohibited", target_kind="ingredient",
            target_value="ingredientA", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            priority_on_hit="high", priority_rationale="r",
            rule_content_hash="rcA", rule_lineage="llA")
        r2 = ProtocolMedicationRule(
            rule_id="R-CM-007", rule_version="v2", clause_locator="P12-4",
            rule_type="prohibited", target_kind="ingredient",
            target_value="ingredientA", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            priority_on_hit="high", priority_rationale="r",
            rule_content_hash="rcB", rule_lineage="llB")
        _, res1 = evaluate_one(ep, (r1,))
        _, res2 = evaluate_one(ep, (r2,))
        id1 = [r for r in res1
               if r.l1_disposition == L1Disposition.POSITIVE][0].r2_candidates[0].detail["risk_identity_id"]
        id2 = [r for r in res2
               if r.l1_disposition == L1Disposition.POSITIVE][0].r2_candidates[0].detail["risk_identity_id"]
        assert id1 != id2

    def test_classifier_excludes_lineage(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        classifier = pos.r2_candidates[0].detail["classifier"]
        assert "rl1" not in classifier
        assert "rc1" not in classifier

    def test_identity_uses_make_risk_identity(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        strat = make_strategy()
        _, results = evaluate_one(ep, (rule,), strategy=strat)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        cand = pos.r2_candidates[0]
        expected = make_risk_identity(
            project_id=PROJECT_ID, subject_ref="SYN-001",
            domain=D02_DOMAIN, scope=cand.detail["scope"],
            classifier=cand.detail["classifier"])
        assert expected.risk_identity_id == cand.detail["risk_identity_id"]


# ===========================================================================
# CMUnitResult protocol + ledger materialization
# ===========================================================================

class TestProtocolAndLedger:
    def test_satisfies_risk_domain_unit_result(self):
        r = CMUnitResult(
            unit_id="u1", subject_ref="S1",
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority="unknown")
        assert isinstance(r, RiskDomainUnitResult)

    def test_to_unit_evaluation_not_evaluable(self):
        r = CMUnitResult(
            unit_id="u1", subject_ref="S1",
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority="unknown",
            not_evaluable_reason="gap")
        ue = r.to_unit_evaluation()
        assert isinstance(ue, UnitEvaluation)

    def test_to_unit_evaluation_positive_requires_provenance(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        ue = pos.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rl1")
        assert ue.l1_disposition == L1Disposition.POSITIVE
        with pytest.raises(UnitJoinError):
            pos.to_unit_evaluation()


# ===========================================================================
# Query drafts (frozen D02 §9.3, correction 8)
# ===========================================================================

class TestQueryDrafts:
    def test_positive_has_three_part_query(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        assert len(pos.query_refs) == 1
        q = pos.query_refs[0]
        assert q.basis.startswith("依据")
        assert q.finding.startswith("发现")
        assert q.action.startswith("行动项")
        assert q.linked_candidate_id == pos.r2_candidates[0].candidate_id

    def test_query_contains_subject_and_dates(self):
        ep = make_episode(cm_start="2026-01-03", cm_end="2026-01-05")
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        q = pos.query_refs[0]
        assert "SYN-001" in q.finding
        assert "2026-01-03" in q.finding

    def test_query_provenance_includes_cm_source_and_identity(self):
        """Correction 8: every Query must include CM source locator AND
        medication-identity evidence locator, deduplicated."""
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        q = pos.query_refs[0]
        cm_loc_id = ep.source_locator.locator_id()
        id_loc_id = ep.identity_binding.evidence_locator.locator_id()
        assert cm_loc_id in q.source_locator_ids
        assert id_loc_id in q.source_locator_ids
        # Deduplicated: no duplicate ids.
        assert len(set(q.source_locator_ids)) == len(q.source_locator_ids)

    def test_query_rule_id_in_basis(self):
        """Correction 8: rule id/clause locator instantiated in text."""
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        q = pos.query_refs[0]
        assert "R-CM-007" in q.basis
        assert "P12-4" in q.basis


# ===========================================================================
# Cross-domain evidence (frozen D02 §3.3, §8)
# ===========================================================================

class TestCrossDomainEvidence:
    def test_cm_indication_ref_is_canonical(self):
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        ref = pos.cross_domain_evidence_refs[0]
        assert ref.verify_content_hash()
        expected = cross_domain_evidence_content_hash(
            source_locator=ref.source_locator,
            evidence_role="cm_indication",
            claim_scope="treatment",
            context_payload=dict(ref.context_payload))
        assert ref.content_hash == expected

    def test_ref_producer_ne_consumer_domain(self):
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        pos = [r for r in results
               if r.l1_disposition == L1Disposition.POSITIVE][0]
        ref = pos.cross_domain_evidence_refs[0]
        assert ref.producer_domain == D02_DOMAIN
        assert ref.consumer_domain == "D01_aemh"

    def test_snapshot_change_same_claim_same_hash(self):
        ep = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        ep2 = make_episode(
            indication_text="高血压", indication_concept="hypertension",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        ep2_alt = MedicationEpisode(
            episode_id=ep2.episode_id, subject_ref=ep2.subject_ref,
            site_ref=ep2.site_ref,
            stable_cm_source_event_key=ep2.stable_cm_source_event_key,
            source_locator=SourceLocator(
                snapshot_id="snap-different", source_revision_id="rev-diff",
                table_semantic="recorded_cm", record_id="CM#9"),
            identity_binding=ep2.identity_binding,
            interval=ep2.interval,
            treatment_role=ep2.treatment_role,
            treatment_role_confirmed=ep2.treatment_role_confirmed,
            indication_text=ep2.indication_text,
            indication_concept=ep2.indication_concept,
            indication_mappable=ep2.indication_mappable,
            study_phase=ep2.study_phase,
            study_phase_confirmed=ep2.study_phase_confirmed,
            indication_treatment_of_study_event=ep2.indication_treatment_of_study_event)
        _, res1 = evaluate_one(ep, (), linkage_coverage_complete=True)
        _, res2 = evaluate_one(ep2_alt, (), linkage_coverage_complete=True)
        ref1 = [r for r in res1
                if r.l1_disposition == L1Disposition.POSITIVE][0].cross_domain_evidence_refs[0]
        ref2 = [r for r in res2
                if r.l1_disposition == L1Disposition.POSITIVE][0].cross_domain_evidence_refs[0]
        assert ref1.content_hash == ref2.content_hash


# ===========================================================================
# CM/IP separation (frozen D02 §3.1)
# ===========================================================================

class TestCMIPSeparation:
    def test_ip_role_conflict_not_evaluable(self):
        ep = make_episode(record_id="EX#1")
        ip_rec = CMSemanticRecord(
            role="ip_exposure", concept="study_drug",
            locator=make_locator("EX#1", "ip_exposure"),
            subject_ref="SYN-001")
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,), ip_records=(ip_rec,))
        nes = [r for r in results
               if "角色互斥冲突" in r.not_evaluable_reason]
        assert len(nes) >= 1


# ===========================================================================
# Compound positive + not_evaluable coexistence + source count (correction 9)
# ===========================================================================

class TestCompoundCoexistence:
    def test_compound_positive_and_not_evaluable_separate_units(self):
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="comp2",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "成分尚未确认" in r.not_evaluable_reason]
        assert len(positives) == 1
        assert len(nes) == 1
        assert len(nes[0].r2_candidates) == 0

    def test_episode_source_count_counts_unique_records(self):
        """Correction 9: one CM row counts once even with multiple child
        units (compound + multi-rule)."""
        from mm_r4.cm import CMSliceResult
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="comp2",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule1 = make_prohibited_rule()
        rule2 = ProtocolMedicationRule(
            rule_id="R-CM-009", rule_version="v1", clause_locator="P17",
            rule_type="prohibited", target_kind="ingredient",
            target_value="ingredientA", applicable_phases=("treatment",),
            window_start="2026-01-01", window_end="2026-06-30",
            window_start_inclusive=True, window_end_inclusive=True,
            priority_on_hit="high", priority_rationale="r",
            rule_content_hash="rc5", rule_lineage="rl5")
        strat = make_strategy()
        exp = expand_cm_expected_set(
            project_id=PROJECT_ID, episodes=(ep,),
            active_rules=(rule1, rule2), strategy=strat)
        unit_results = []
        for eu in exp.units:
            r = evaluate_cm_unit(
                project_id=PROJECT_ID, expanded=eu,
                strategy=strat, priority_policy=make_policy(),
                snapshot_id=SNAPSHOT_ID)
            unit_results.append(r)
        sr = CMSliceResult(
            subject_ref="SYN-001", unit_results=tuple(unit_results),
            expected_set_hash=exp.expected_set_hash)
        rollups = sr.episode_rollups(exp)
        assert len(rollups) == 1
        # One CM source row -> source_record_count == 1 despite 4 child units.
        assert rollups[0].source_record_count == 1
        assert len(rollups[0].child_unit_ids) >= 3
        assert rollups[0].has_positive
        assert rollups[0].has_not_evaluable


# ===========================================================================
# User language (correction 10)
# ===========================================================================

class TestUserLanguage:
    """Scan all user-visible result strings for prohibited jargon."""

    PROHIBITED = ("正式事实", "候选信号", "只读", "未知风险")

    def _all_result_strings(self, results):
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

    def test_no_prohibited_jargon_in_rule_results(self):
        ep = make_episode()
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        for s in self._all_result_strings(results):
            for token in self.PROHIBITED:
                assert token not in s, f"prohibited {token!r} in {s!r}"

    def test_no_prohibited_jargon_in_indication_results(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment")
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        for s in self._all_result_strings(results):
            for token in self.PROHIBITED:
                assert token not in s, f"prohibited {token!r} in {s!r}"

    def test_no_prohibited_jargon_in_not_evaluable_results(self):
        ep = make_episode(study_phase="", study_phase_confirmed=False)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        for s in self._all_result_strings(results):
            for token in self.PROHIBITED:
                assert token not in s, f"prohibited {token!r} in {s!r}"

    def test_unreachable_branch_uses_native_phrase(self):
        """Correction 10: unreachable evaluator branch says native Chinese
        coverage-gap phrase, not '未知风险族'."""
        from mm_r4.cm import CMUnitExpanded
        ep = make_episode()
        strat = make_strategy()
        # Manually build an expanded unit with an unrecognized risk family.
        bogus = CMUnitExpanded(
            episode=ep, ingredient_token="ingredientA",
            rule_item_or_concept="bogus", risk_family="bogus_family",
            is_ingredient_resolution=False, rule=None)
        r = evaluate_cm_unit(
            project_id=PROJECT_ID, expanded=bogus,
            strategy=strat, priority_policy=make_policy(),
            snapshot_id=SNAPSHOT_ID)
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "未识别的用药核查类型" in r.not_evaluable_reason
        assert "未知风险" not in r.not_evaluable_reason


# ===========================================================================
# Phase-gate corrections (round-3 corrections 1-4)
# ===========================================================================

class TestPhaseGateRuleUnit:
    """Correction 1: rule-unit phase gate must fail closed for every
    inconsistent or unconfirmed phase state."""

    def test_confirmed_false_phase_nonempty_is_not_evaluable(self):
        """(confirmed=False, phase non-empty) must be not_evaluable,
        not evaluation."""
        ep = make_episode(study_phase="treatment", study_phase_confirmed=False)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "未获确认" in r.not_evaluable_reason]
        assert len(nes) >= 1
        # No positive produced despite a definitive match.
        assert not any(r.l1_disposition == L1Disposition.POSITIVE
                       for r in results)

    def test_confirmed_true_phase_empty_is_not_evaluable(self):
        """(confirmed=True, phase empty) must be not_evaluable."""
        ep = make_episode(study_phase="", study_phase_confirmed=True)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "缺失或为空" in r.not_evaluable_reason]
        assert len(nes) >= 1
        assert not any(r.l1_disposition == L1Disposition.POSITIVE
                       for r in results)

    def test_confirmed_true_phase_outside_applicable_is_not_applicable(self):
        """Confirmed phase outside applicable_phases is not_applicable."""
        ep = make_episode(study_phase="followup", study_phase_confirmed=True)
        rule = make_prohibited_rule(applicable_phases=("treatment",))
        _, results = evaluate_one(ep, (rule,))
        nas = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_APPLICABLE]
        assert len(nas) == 1
        assert len(nas[0].r2_candidates) == 0
        assert len(nas[0].query_refs) == 0

    def test_confirmed_true_phase_inside_proceeds_to_evaluation(self):
        """Confirmed phase inside applicable_phases proceeds normally."""
        ep = make_episode(study_phase="treatment", study_phase_confirmed=True)
        rule = make_prohibited_rule(applicable_phases=("treatment",))
        _, results = evaluate_one(ep, (rule,))
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1


class TestPhaseGateIndicationUnit:
    """Correction 2: indication-check units must apply the required-phase
    gate before becoming positive or negative."""

    def test_missing_phase_indication_not_evaluable_no_candidate(self):
        """Missing phase on indication unit -> not_evaluable, zero
        candidate/Query/ref."""
        ep = make_episode(
            study_phase="", study_phase_confirmed=False,
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "研究阶段缺失或为空" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert len(nes[0].r2_candidates) == 0
        assert len(nes[0].query_refs) == 0
        assert len(nes[0].cross_domain_evidence_refs) == 0

    def test_unconfirmed_phase_indication_not_evaluable_no_candidate(self):
        """Unconfirmed phase (confirmed=False, phase non-empty) on
        indication unit -> not_evaluable, zero candidate/Query/ref."""
        ep = make_episode(
            study_phase="treatment", study_phase_confirmed=False,
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "未获确认" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert len(nes[0].r2_candidates) == 0
        assert len(nes[0].query_refs) == 0
        assert len(nes[0].cross_domain_evidence_refs) == 0

    def test_confirmed_empty_phase_indication_not_evaluable(self):
        """(confirmed=True, phase empty) on indication unit ->
        not_evaluable."""
        ep = make_episode(
            study_phase="", study_phase_confirmed=True,
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "缺失或为空" in r.not_evaluable_reason]
        assert len(nes) == 1
        assert len(nes[0].r2_candidates) == 0

    def test_confirmed_phase_indication_can_proceed(self):
        """Confirmed phase on indication unit with complete coverage ->
        positive is possible."""
        ep = make_episode(
            study_phase="treatment", study_phase_confirmed=True,
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role="treatment",
            indication_treatment_of_study_event=True)
        _, results = evaluate_one(ep, (), linkage_coverage_complete=True)
        positives = [r for r in results
                     if r.l1_disposition == L1Disposition.POSITIVE]
        assert len(positives) == 1


class TestUnresolvedIngredientUserLanguage:
    """Correction 3: unresolved-ingredient reason must be natural Chinese,
    free of backend tokens."""

    BACKEND_TOKENS = (
        "ingredient_resolution", "RiskCandidate", "L1",
        "formal fact", "正式事实", "候选信号", "只读", "未知风险")

    def test_unresolved_reason_is_natural_chinese(self):
        binding = make_binding((
            IngredientBinding(component_slot="c1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding)
        rule = make_prohibited_rule()
        _, results = evaluate_one(ep, (rule,))
        nes = [r for r in results
               if r.l1_disposition == L1Disposition.NOT_EVALUABLE
               and "成分尚未确认" in r.not_evaluable_reason]
        assert len(nes) == 1
        reason = nes[0].not_evaluable_reason
        for token in self.BACKEND_TOKENS:
            assert token not in reason, (
                f"backend token {token!r} leaked into reason {reason!r}")
