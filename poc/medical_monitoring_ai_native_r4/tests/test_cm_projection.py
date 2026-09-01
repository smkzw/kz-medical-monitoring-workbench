"""R4-D02 CM journey/risk-marker projection deterministic tests (worker_03).

Proves the frozen D02 CM projection (``FROZEN_R4_D02_CONTRACT_V1`` §10)
implements the mandatory journey/event/risk-marker contract with
deterministic synthetic-only assertions:

* :class:`CMJourneyEvent` carries the §10 minimum fields:
  ``event_id/domain_track=cm/subject_ref/start/end/ongoing/
  date_precision/episode_id/display_label/source_locator_ids/unit_ids``.
* :class:`CMRiskMarker` carries the §10 minimum fields:
  ``marker_id/risk_family/audience_label/monitoring_priority/
  anchor_kind/anchor_start/anchor_end/unit_id/candidate_or_risk_id/
  source_locator_ids/rule_locator_ids/query_ids/coverage_gap``.
* Chinese typed event/risk labels are concrete medical wording; the
  six §9.2 positive subtype labels and the risk-family labels are used.
  Internal object names never leak.
* Visit/time-axis locators carry date precision.
* Source drill-back fields link CM source, identity evidence, rule
  clause, cross-domain evidence and Query ids.
* The episode rollup is view-only and preserves all child unit ids and
  ``has_positive/has_boundary/has_not_evaluable`` simultaneously.
* Bidirectional event-marker joins are verified by stable ids, not by
  prose.
* Simultaneous positive / boundary / not_evaluable states are never
  collapsed into a generic event or generic risk marker.

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
    CMIntervalDescriptor,
    CMSliceError,
    CMSemanticRecord,
    CONFIRMATION_CONFIRMED,
    CONFIRMATION_UNRESOLVED,
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
    expand_cm_expected_set,
    evaluate_cm_slice,
)
from mm_r4.cm_projection import (  # noqa: E402
    ANCHOR_KIND_INTERVAL,
    ANCHOR_KIND_OVERLAP,
    ANCHOR_KIND_UNRESOLVED,
    CMJourneyEvent,
    CMRiskMarker,
    CM_RISK_FAMILY_LABELS,
    project_cm_subject_journey,
)
from mm_r4.contracts import (  # noqa: E402
    L1Disposition,
    MONITORING_PRIORITY_HIGH,
    SourceLocator,
)


# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"


# ===========================================================================
# Helpers (mirror the engine test conventions)
# ===========================================================================

def make_locator(record_id: str, table_semantic: str = "recorded_cm",
                 snapshot_id: str = SNAPSHOT_ID) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_strategy(version: str = "ms-v1",
                  chash: str = "sch1") -> MedicationMatchStrategy:
    return MedicationMatchStrategy(version=version, strategy_content_hash=chash)


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
    cm_start="2026-01-03", cm_end="2026-01-05", ongoing=False, cutoff="",
    phase="treatment", treatment_role="treatment",
    treatment_role_confirmed=True, indication_text="", indication_concept="",
    indication_mappable=None, dose="100", dose_unit="mg", route="口服",
    frequency="每日一次",
    study_phase="treatment", study_phase_confirmed=True,
    indication_treatment_of_study_event=False,
) -> MedicationEpisode:
    if binding is None:
        binding = make_binding((IngredientBinding(ingredient="ingredientA"),))
    return MedicationEpisode(
        episode_id=f"ep-{record_id}", subject_ref=subject, site_ref=SITE_REF,
        stable_cm_source_event_key=f"recorded_cm:{record_id}",
        source_locator=make_locator(record_id),
        identity_binding=binding,
        interval=CMIntervalDescriptor(
            cm_start=cm_start, cm_end=cm_end, ongoing=ongoing, cutoff=cutoff,
            applicable_phase=phase),
        dose=dose, dose_unit=dose_unit, route=route, frequency=frequency,
        treatment_role=treatment_role,
        treatment_role_confirmed=treatment_role_confirmed,
        indication_text=indication_text,
        indication_concept=indication_concept,
        indication_mappable=indication_mappable,
        study_phase=study_phase,
        study_phase_confirmed=study_phase_confirmed,
        indication_treatment_of_study_event=indication_treatment_of_study_event)


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


def make_record_consistency_rule() -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id="R-CM-REC-001", rule_version="v1",
        clause_locator="P12-6", rule_type="record_consistency",
        target_kind="ingredient", target_value="ingredientA",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-06-30",
        window_start_inclusive=True, window_end_inclusive=True,
        comparison_field="dose", expected_values=("50",),
        priority_on_hit="medium", priority_rationale="方案用药要求",
        rule_content_hash="rc-record-v1", rule_lineage="rl-record-v1")


def make_action_relationship_rule() -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id="R-CM-ACT-001", rule_version="v1",
        clause_locator="P12-7", rule_type="action_relationship",
        target_kind="ingredient", target_value="ingredientA",
        applicable_phases=("treatment",),
        window_start="2026-01-01", window_end="2026-06-30",
        window_start_inclusive=True, window_end_inclusive=True,
        related_role="reported_ae", related_concept="headache",
        expected_actions=("continue",),
        priority_on_hit="high", priority_rationale="关键处置关系",
        rule_content_hash="rc-action-v1", rule_lineage="rl-action-v1")


def evaluate_and_project(episode, rules=(), strategy=None, policy=None,
                         evidence_records=(), ip_records=(),
                         linkage_coverage_complete=False,
                         relationship_coverage_complete=False):
    """Evaluate one episode and project its subject journey."""
    if strategy is None:
        strategy = make_strategy()
    if policy is None:
        policy = make_policy()
    slices = evaluate_cm_slice(
        project_id=PROJECT_ID, episodes=(episode,), active_rules=rules,
        strategy=strategy, evidence_records=evidence_records,
        priority_policy=policy, snapshot_id=SNAPSHOT_ID,
        ip_exposure_records=ip_records,
        linkage_coverage_complete=linkage_coverage_complete,
        relationship_coverage_complete=relationship_coverage_complete)
    exp = expand_cm_expected_set(
        project_id=PROJECT_ID, episodes=(episode,), active_rules=rules,
        strategy=strategy)
    subj = slices[episode.subject_ref]
    proj = project_cm_subject_journey(subj, expansions=exp)
    return subj, exp, proj


# ===========================================================================
# §10 minimum field presence: CMJourneyEvent
# ===========================================================================

class TestCMJourneyEventMinimumFields:
    """Frozen D02 §10: CMJourneyEvent minimum fields."""

    def test_prohibited_positive_projects_journey_event(self):
        ep = make_episode()
        subj, exp, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        assert proj.event_count >= 1
        ev = proj.events[0]
        # All §10 minimum fields present and non-empty.
        assert ev.event_id == ep.episode_id
        assert ev.domain_track == "cm"
        assert ev.subject_ref == "SYN-001"
        assert ev.start == "2026-01-03"
        assert ev.end == "2026-01-05"
        assert ev.ongoing is False
        assert ev.date_precision == "day"
        assert ev.episode_id == ep.episode_id
        assert ev.display_label == "合成药物A"
        assert len(ev.source_locator_ids) >= 1
        assert len(ev.unit_ids) >= 1

    def test_journey_event_domain_track_always_cm(self):
        """§10: CM events use a distinct track from AE/MH/IP."""
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        for ev in proj.events:
            assert ev.domain_track == "cm"

    def test_journey_event_requires_source_locator(self):
        with pytest.raises(CMSliceError, match="source locator"):
            CMJourneyEvent(
                event_id="ep-x", domain_track="cm", subject_ref="S1",
                start="", end="", ongoing=False, date_precision="none",
                episode_id="ep-x", display_label="x",
                source_locator_ids=(), unit_ids=("u1",))

    def test_journey_event_requires_cm_track(self):
        with pytest.raises(CMSliceError, match="domain_track"):
            CMJourneyEvent(
                event_id="ep-x", domain_track="ae", subject_ref="S1",
                start="", end="", ongoing=False, date_precision="none",
                episode_id="ep-x", display_label="x",
                source_locator_ids=("loc-1",), unit_ids=("u1",))


# ===========================================================================
# §10 minimum field presence: CMRiskMarker
# ===========================================================================

class TestCMRiskMarkerMinimumFields:
    """Frozen D02 §10: CMRiskMarker minimum fields."""

    def test_prohibited_positive_marker_has_all_minimum_fields(self):
        ep = make_episode()
        subj, exp, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        positive_markers = [m for m in proj.risk_markers
                            if m.l1_disposition == L1Disposition.POSITIVE]
        assert len(positive_markers) == 1
        m = positive_markers[0]
        # All §10 minimum fields.
        assert m.marker_id.startswith("cmm-")
        assert m.risk_family == "prohibited_medication"
        assert m.audience_label == "禁用药使用待核实"
        assert m.monitoring_priority == MONITORING_PRIORITY_HIGH
        assert m.anchor_kind == ANCHOR_KIND_OVERLAP
        assert m.anchor_start == "2026-01-03"
        assert m.anchor_end == "2026-01-05"
        assert m.unit_id.strip()
        assert m.candidate_or_risk_id.strip()
        assert len(m.source_locator_ids) >= 1
        assert len(m.rule_locator_ids) >= 1
        assert len(m.query_ids) >= 1
        assert m.coverage_gap is False

    def test_invalid_anchor_kind_rejected(self):
        with pytest.raises(CMSliceError, match="anchor_kind"):
            CMRiskMarker(
                marker_id="m1", risk_family="prohibited_medication",
                audience_label="x", monitoring_priority="high",
                anchor_kind="bogus", anchor_start="", anchor_end="",
                unit_id="u1", candidate_or_risk_id="c1",
                source_locator_ids=("loc-1",), rule_locator_ids=(),
                query_ids=(), coverage_gap=False)

    def test_invalid_priority_rejected(self):
        with pytest.raises(CMSliceError, match="monitoring_priority"):
            CMRiskMarker(
                marker_id="m1", risk_family="prohibited_medication",
                audience_label="x", monitoring_priority="bogus",
                anchor_kind=ANCHOR_KIND_OVERLAP, anchor_start="",
                anchor_end="", unit_id="u1", candidate_or_risk_id="c1",
                source_locator_ids=("loc-1",), rule_locator_ids=(),
                query_ids=(), coverage_gap=False)


# ===========================================================================
# §9.2 Chinese typed labels — no internal object names leak
# ===========================================================================

class TestChineseTypedLabels:
    """Frozen D02 §9.2: audience labels are concrete medical wording."""

    @pytest.mark.parametrize("subtype,expected", [
        (POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
         "禁用药使用待核实"),
        (POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH,
         "限制用药条件待核实"),
        (POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED,
         "用药依据待核实"),
        (POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
         "治疗用药与 AE/MH 记录待核实"),
        (POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY,
         "用药信息与方案要求不一致"),
        (POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT,
         "用药与处置记录关系待核实"),
    ])
    def test_positive_marker_uses_subtype_label(self, subtype, expected):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment",
            indication_treatment_of_study_event=(
                subtype == POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD))
        evidence_records = ()
        if subtype == POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH:
            rules = (make_prohibited_rule(),)
        elif subtype == POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH:
            ep2 = make_episode(
                binding=make_binding(
                    (IngredientBinding(ingredient="ingredientB"),)),
                indication_text="头痛", indication_concept="headache",
                indication_mappable=True, treatment_role_confirmed=True)
            ep = ep2
            rules = (make_restricted_rule(rescue_exception=True),)
        elif subtype == POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY:
            rules = (make_record_consistency_rule(),)
        elif subtype == POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT:
            rules = (make_action_relationship_rule(),)
            evidence_records = (CMSemanticRecord(
                role="reported_ae", concept="headache",
                locator=make_locator("AE#action", "reported_ae"),
                subject_ref=ep.subject_ref, site_ref=ep.site_ref,
                event_date_raw="2026-01-04",
                action_value="stop",
                linked_cm_source_event_key=ep.stable_cm_source_event_key,
                relationship_confirmation=CONFIRMATION_CONFIRMED),)
        else:
            rules = ()
        _, _, proj = evaluate_and_project(
            ep, rules=rules, linkage_coverage_complete=True,
            evidence_records=evidence_records,
            relationship_coverage_complete=(subtype == (
                POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT)))
        labels = {m.audience_label for m in proj.risk_markers}
        assert expected in labels, (
            f"expected label {expected!r} in {labels}")

    def test_no_internal_object_names_in_audience_labels(self):
        """§9.2/§3.9: no RiskCandidate/L1 positive/候选信号 etc."""
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        prohibited_terms = (
            "RiskCandidate", "L1 positive", "正式事实", "候选信号",
            "只读", "通用风险点", "已记录事项", "generic",
        )
        for m in proj.risk_markers:
            for term in prohibited_terms:
                assert term not in m.audience_label, (
                    f"prohibited term {term!r} in {m.audience_label!r}")

    def test_risk_family_label_map_has_concrete_wording(self):
        assert CM_RISK_FAMILY_LABELS["prohibited_medication"] == "禁用药使用待核实"
        assert CM_RISK_FAMILY_LABELS["restricted_medication"] == "限制用药条件待核实"
        assert CM_RISK_FAMILY_LABELS["medication_record_consistency"] == "用药信息与方案要求不一致"
        assert CM_RISK_FAMILY_LABELS["treatment_action_relationship"] == "用药与处置记录关系待核实"
        assert CM_RISK_FAMILY_LABELS["indication_check"] == "用药依据待核实"
        assert CM_RISK_FAMILY_LABELS["ingredient_resolution"] == "复方成分待确认"


# ===========================================================================
# §10 anchor kinds: overlap / interval / unresolved
# ===========================================================================

class TestAnchorKinds:
    """Frozen D02 §10: marker anchor kinds distinguish risk positions."""

    def test_prohibited_rule_marker_anchors_at_overlap(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert m.anchor_kind == ANCHOR_KIND_OVERLAP

    def test_indication_risk_anchors_at_interval_not_event(self):
        """§10 line 309: rationale risk with no event does not fabricate
        an event position; anchor on CM interval."""
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ind_markers = [x for x in proj.risk_markers
                       if x.risk_family == "indication_check"]
        assert len(ind_markers) == 1
        assert ind_markers[0].anchor_kind == ANCHOR_KIND_INTERVAL

    def test_unresolved_component_anchors_at_unresolved(self):
        """Compound with one unresolved component -> ingredient_resolution
        marker with unresolved anchor kind."""
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="unknown1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding, record_id="CM#10")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        unresolved_markers = [x for x in proj.risk_markers
                              if x.risk_family == "ingredient_resolution"]
        assert len(unresolved_markers) == 1
        assert unresolved_markers[0].anchor_kind == ANCHOR_KIND_UNRESOLVED
        assert unresolved_markers[0].coverage_gap is True


# ===========================================================================
# §10 source drill-back fields
# ===========================================================================

class TestSourceDrillBack:
    """Frozen D02 §10: one-click drill-back to CM source, identity evidence,
    rule clause, cross-domain evidence and Query."""

    def test_prohibited_marker_carries_rule_clause_locator(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert "P12-4" in m.rule_locator_ids

    def test_prohibited_marker_carries_query_id(self):
        ep = make_episode()
        subj, exp, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert len(m.query_ids) == 1
        assert m.query_ids[0].startswith("q-")

    def test_prohibited_marker_carries_identity_fields(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert m.risk_identity_id.startswith("risk-id-")
        assert m.stable_core.startswith("d02|prohibited_medication|")
        assert m.classifier == m.stable_core
        assert m.lineage_fingerprint.strip()

    def test_indication_marker_carries_cross_domain_evidence_ref(self):
        """§8/§10: indication positive emits a cm_indication cross-domain
        evidence ref; the marker carries its id for D01 drill-back."""
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ind_markers = [x for x in proj.risk_markers
                       if x.risk_family == "indication_check"]
        assert len(ind_markers) == 1
        m = ind_markers[0]
        assert len(m.cross_domain_evidence_ref_ids) == 1
        assert m.cross_domain_evidence_ref_ids[0].startswith("cer-")

    def test_journey_event_carries_cross_domain_evidence_ref_ids(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ev = proj.events[0]
        assert len(ev.cross_domain_evidence_ref_ids) >= 1


# ===========================================================================
# §10 view-only episode rollup preserves all child units + simultaneous flags
# ===========================================================================

class TestEpisodeRollup:
    """Frozen D02 §4.1 step 4, §11: read-only rollup preserves all child
    unit ids and has_positive/has_boundary/has_not_evaluable."""

    def test_rollup_preserves_child_unit_ids(self):
        ep = make_episode()
        subj, exp, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        assert len(proj.episode_rollups) == 1
        roll = proj.episode_rollups[0]
        assert roll.episode_id == ep.episode_id
        # Every evaluated unit id is in the rollup.
        evaluated_ids = {r.unit_id for r in subj.unit_results}
        assert set(roll.child_unit_ids) == evaluated_ids

    def test_rollup_simultaneous_positive_and_not_evaluable(self):
        """Compound with confirmed prohibited ingredient + unresolved
        component -> episode has both positive and not_evaluable."""
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="unknown1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding, record_id="CM#10")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        roll = proj.episode_rollups[0]
        assert roll.has_positive is True
        assert roll.has_not_evaluable is True
        assert roll.source_record_count == 1  # one unique CM source record

    def test_rollup_is_view_only_snapshot(self):
        """The rollup is a frozen dataclass; mutating raises."""
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        roll = proj.episode_rollups[0]
        with pytest.raises(Exception):
            roll.has_positive = False  # type: ignore[misc]


# ===========================================================================
# §10 bidirectional joins verified by stable ids
# ===========================================================================

class TestBidirectionalJoin:
    """Frozen D02 §10: all bidirectional joins use stable ids, not prose."""

    def test_marker_joins_to_event_via_episode_id(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        join = proj.join
        for m in proj.risk_markers:
            linked = join.events_for_marker(m.marker_id)
            assert len(linked) >= 1
            assert ep.episode_id in [e for e in linked] or any(
                proj_event.event_id in linked
                for proj_event in proj.events)

    def test_event_joins_to_all_its_markers(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        ev = proj.events[0]
        marker_ids = proj.join.markers_for_event(ev.event_id)
        # The episode has a prohibited positive + an indication-check
        # not_evaluable -> at least 2 markers.
        assert len(marker_ids) >= 2

    def test_join_source_locator_ids_match_marker(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        for m in proj.risk_markers:
            ids = proj.join.source_locator_ids_by_marker.get(m.marker_id, ())
            assert set(ids) == set(m.source_locator_ids)

    def test_join_rule_locator_ids_match_marker(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        prohibited = [x for x in proj.risk_markers
                      if x.risk_family == "prohibited_medication"][0]
        ids = proj.join.rule_locator_ids_by_marker[prohibited.marker_id]
        assert set(ids) == set(prohibited.rule_locator_ids)

    def test_join_query_ids_match_marker(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        for m in proj.risk_markers:
            ids = proj.join.query_ids_by_marker.get(m.marker_id, ())
            assert set(ids) == set(m.query_ids)

    def test_empty_projection_join_is_empty(self):
        """A fully-negative unit produces no markers; join is empty.

        A not_evaluable indication unit (no indication recorded) still
        emits a coverage-gap marker per §10 -- that is not 'empty'.  To
        get a truly marker-free projection we give the episode a mappable
        indication WITH a matching AE record and complete linkage, which
        makes the indication unit negative (no marker) and use a
        non-matching ingredient to make the rule unit negative too.
        """
        ae_rec = CMSemanticRecord(
            role="reported_ae", concept="headache",
            locator=make_locator("AE#1", "reported_ae"),
            subject_ref="SYN-001", event_date_raw="2026-01-04")
        ep = make_episode(
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientZ"),)),
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),),
            evidence_records=(ae_rec,), linkage_coverage_complete=True)
        assert len(proj.risk_markers) == 0
        assert proj.join.marker_ids_for_event == {}
# ===========================================================================
# §10 simultaneous states never collapse into a generic marker
# ===========================================================================

class TestNoStateCollapse:
    """Frozen D02 §10/§11: positive/boundary/not_evaluable states coexist;
    none is collapsed into a generic event or generic risk marker."""

    def test_compound_positive_and_not_evaluable_are_distinct_markers(self):
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="unknown1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding, record_id="CM#10")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        positive = [m for m in proj.risk_markers
                    if m.l1_disposition == L1Disposition.POSITIVE]
        not_evaluable = [m for m in proj.risk_markers
                         if m.l1_disposition == L1Disposition.NOT_EVALUABLE]
        assert len(positive) == 1
        assert len(not_evaluable) >= 1
        # Distinct marker ids, risk families, audience labels, anchor kinds.
        assert positive[0].marker_id != not_evaluable[0].marker_id
        assert positive[0].risk_family == "prohibited_medication"
        assert not_evaluable[0].risk_family == "ingredient_resolution"
        assert positive[0].audience_label == "禁用药使用待核实"
        assert not_evaluable[0].audience_label == "复方成分待确认"
        assert positive[0].anchor_kind == ANCHOR_KIND_OVERLAP
        assert not_evaluable[0].anchor_kind == ANCHOR_KIND_UNRESOLVED

    def test_positive_marker_is_risk_marker_not_evaluable_is_coverage_gap(self):
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="unknown1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding, record_id="CM#10")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        positive = [m for m in proj.risk_markers
                    if m.l1_disposition == L1Disposition.POSITIVE][0]
        ne = [m for m in proj.risk_markers
              if m.l1_disposition == L1Disposition.NOT_EVALUABLE][0]
        assert positive.is_risk_marker is True
        assert positive.coverage_gap is False
        assert ne.is_risk_marker is False
        assert ne.coverage_gap is True

    def test_subject_projection_reports_all_simultaneous_states(self):
        binding = make_binding((
            IngredientBinding(ingredient="ingredientA"),
            IngredientBinding(component_slot="unknown1",
                              confirmation=CONFIRMATION_UNRESOLVED),
        ))
        ep = make_episode(binding=binding, record_id="CM#10")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        assert proj.has_positive() is True
        assert proj.has_not_evaluable() is True
        assert proj.risk_marker_count >= 1
        assert proj.coverage_gap_marker_count >= 1


# ===========================================================================
# §7/§10 visit/time-axis locators carry date precision
# ===========================================================================

class TestTimeAxisLocators:
    """Frozen D02 §10/§7: journey events carry date precision on the
    visit/time axis."""

    def test_day_precision_full_dates(self):
        ep = make_episode(cm_start="2026-01-03", cm_end="2026-01-05")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        assert proj.events[0].date_precision == "day"

    def test_month_precision_partial_date(self):
        ep = make_episode(cm_start="2026-01", cm_end="2026-02")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        assert proj.events[0].date_precision == "month"

    def test_year_precision_partial_date(self):
        ep = make_episode(cm_start="2026", cm_end="2026")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        assert proj.events[0].date_precision == "year"

    def test_ongoing_end_shows_zhanchi(self):
        ep = make_episode(cm_start="2026-01-03", cm_end="", ongoing=True)
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        assert proj.events[0].ongoing is True
        assert proj.events[0].end == "持续中"


# ===========================================================================
# Determinism: repeated projection yields identical payloads
# ===========================================================================

class TestDeterminism:
    """Frozen D02: projection is deterministic for the same inputs."""

    def test_repeated_projection_is_identical(self):
        ep = make_episode()
        _, _, proj1 = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        _, _, proj2 = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        assert proj1.canonical_payload() == proj2.canonical_payload()

    def test_marker_ids_are_stable(self):
        ep = make_episode()
        _, _, proj1 = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        _, _, proj2 = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),))
        ids1 = [m.marker_id for m in proj1.risk_markers]
        ids2 = [m.marker_id for m in proj2.risk_markers]
        assert ids1 == ids2


# ===========================================================================
# Negative and not_applicable units produce no risk markers
# ===========================================================================

class TestNoMarkerForNegativeStates:
    """Frozen D02 §11: negative/not_applicable do not create risk markers."""

    def test_negative_unit_produces_no_markers(self):
        # Definitive ingredient-exact non-match rule unit + mappable
        # indication with matching AE -> both units negative, no marker.
        ae_rec = CMSemanticRecord(
            role="reported_ae", concept="headache",
            locator=make_locator("AE#1", "reported_ae"),
            subject_ref="SYN-001", event_date_raw="2026-01-04")
        ep = make_episode(
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientZ"),)),
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(make_prohibited_rule(),),
            evidence_records=(ae_rec,), linkage_coverage_complete=True)
        assert len(proj.risk_markers) == 0

    def test_not_applicable_unit_produces_no_applicable_marker(self):
        """Confirmed phase outside rule applicability -> not_applicable
        rule unit produces no marker.  The indication-check sibling may
        still be not_evaluable (coverage gap), but no marker carries
        ``l1_disposition=not_applicable``."""
        ep = make_episode(study_phase="followup", study_phase_confirmed=True)
        rule = make_prohibited_rule(applicable_phases=("treatment",))
        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        for m in proj.risk_markers:
            assert m.l1_disposition != L1Disposition.NOT_APPLICABLE


# ===========================================================================
# §10 indication-rationale risk: no fabricated event position
# ===========================================================================

class TestIndicationRationaleNoFabricatedEvent:
    """Frozen D02 §10 line 309: a rationale risk that holds because no
    corresponding AE/MH/diagnosis record exists does NOT fabricate an
    event position; the marker anchors on the CM interval."""

    def test_indication_positive_has_one_cm_event_not_two(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        # Exactly one CM journey event (the CM interval), not a fake
        # AE/MH event.
        assert proj.event_count == 1
        assert proj.events[0].domain_track == "cm"

    def test_indication_marker_anchor_is_interval(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ind = [x for x in proj.risk_markers
               if x.risk_family == "indication_check"][0]
        assert ind.anchor_kind == ANCHOR_KIND_INTERVAL


# ===========================================================================
# Cross-domain evidence ref projection integrity
# ===========================================================================

class TestCrossDomainEvidenceIntegrity:
    """Frozen D02 §3.3/§8/§10: the cm_indication cross-domain evidence ref
    is projected read-only; it carries no consumer lifecycle state."""

    def test_cross_domain_ref_ids_on_marker_and_event_match(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        marker_cer = [x.cross_domain_evidence_ref_ids
                      for x in proj.risk_markers
                      if x.risk_family == "indication_check"][0]
        event_cer = proj.events[0].cross_domain_evidence_ref_ids
        assert set(marker_cer) == set(event_cer)


# ===========================================================================
# Canonical payload serialization
# ===========================================================================

class TestCanonicalPayload:
    """The projection payloads serialize to deterministic canonical dicts."""

    def test_journey_event_canonical_payload_has_minimum_fields(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        payload = proj.events[0].canonical_payload()
        for key in ("event_id", "domain_track", "subject_ref", "start",
                    "end", "ongoing", "date_precision", "episode_id",
                    "display_label", "source_locator_ids", "unit_ids"):
            assert key in payload

    def test_risk_marker_canonical_payload_has_minimum_fields(self):
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.l1_disposition == L1Disposition.POSITIVE][0]
        payload = m.canonical_payload()
        for key in ("marker_id", "risk_family", "audience_label",
                    "monitoring_priority", "anchor_kind", "anchor_start",
                    "anchor_end", "unit_id", "candidate_or_risk_id",
                    "source_locator_ids", "rule_locator_ids", "query_ids",
                    "coverage_gap"):
            assert key in payload



# ===========================================================================
# Round-2 repair: Defect 1 -- real rule-overlap anchor
# ===========================================================================

class TestRealOverlapAnchor:
    """Defect 1: prohibited/restricted anchor must be the exact CM ∩ rule
    intersection when full-day endpoints are comparable."""

    def test_cm_wider_than_rule_window_exact_intersection(self):
        """CM spans 2026-01-01..2026-06-30; rule window is
        2026-02-01..2026-03-31.  The overlap anchor must be exactly
        2026-02-01..2026-03-31, not the full CM interval."""
        ep = make_episode(
            cm_start="2026-01-01", cm_end="2026-06-30",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),)))
        rule = make_prohibited_rule(
            window_start="2026-02-01", window_end="2026-03-31",
            start_inc=True, end_inc=True)
        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert m.anchor_kind == ANCHOR_KIND_OVERLAP
        assert m.anchor_start == "2026-02-01"
        assert m.anchor_end == "2026-03-31"

    def test_cm_inside_rule_window_anchor_is_cm(self):
        """CM fully inside rule window -> overlap equals CM interval."""
        ep = make_episode(
            cm_start="2026-02-15", cm_end="2026-02-20",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),)))
        rule = make_prohibited_rule(
            window_start="2026-01-01", window_end="2026-06-30")
        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        assert m.anchor_start == "2026-02-15"
        assert m.anchor_end == "2026-02-20"

    def test_partial_date_falls_back_to_cm_interval(self):
        """Partial-date CM interval -> fail-closed: anchor on full CM
        interval, consistent with engine boundary/not_evaluable."""
        ep = make_episode(
            cm_start="2026-01", cm_end="2026-06",
            binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),)))
        rule = make_prohibited_rule(
            window_start="2026-01-01", window_end="2026-06-30")
        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        # The rule unit will be boundary (partial date) -> check its marker.
        boundary_markers = [x for x in proj.risk_markers
                            if x.l1_disposition == L1Disposition.BOUNDARY]
        if boundary_markers:
            m = boundary_markers[0]
            # Fail-closed: full CM interval, not a fabricated intersection.
            assert m.anchor_start == "2026-01"
            assert m.anchor_end == "2026-06"


# ===========================================================================
# Round-2 repair: Defect 2 -- medication-identity drill-back
# ===========================================================================

class TestMedicationIdentityDrillBack:
    """Defect 2: every marker must include CM source locator AND
    identity-binding evidence locator when episode is available."""

    def test_prohibited_marker_includes_cm_source_and_identity_evidence(self):
        ep = make_episode(record_id="CM#42")
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        m = [x for x in proj.risk_markers
             if x.risk_family == "prohibited_medication"][0]
        cm_source = ep.source_locator.locator_id()
        identity_ev = ep.identity_binding.evidence_locator.locator_id()
        assert cm_source in m.source_locator_ids
        assert identity_ev in m.source_locator_ids

    def test_indication_marker_includes_cm_source_and_identity_evidence(self):
        ep = make_episode(
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment", record_id="CM#43")
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ind = [x for x in proj.risk_markers
               if x.risk_family == "indication_check"]
        # indication positive marker OR indication not_evaluable marker;
        # either way it must carry identity drill-back.
        assert len(ind) >= 1
        m = ind[0]
        cm_source = ep.source_locator.locator_id()
        identity_ev = ep.identity_binding.evidence_locator.locator_id()
        assert cm_source in m.source_locator_ids
        assert identity_ev in m.source_locator_ids

    def test_indication_locator_included_when_present(self):
        """When episode has a distinct indication_source_locator, it must
        appear in the marker source_locator_ids."""
        indication_loc = make_locator("IND#1", "diagnosis")
        ep = MedicationEpisode(
            episode_id="ep-CM44", subject_ref="SYN-001", site_ref=SITE_REF,
            stable_cm_source_event_key="recorded_cm:CM#44",
            source_locator=make_locator("CM#44"),
            identity_binding=make_binding(
                (IngredientBinding(ingredient="ingredientA"),)),
            interval=CMIntervalDescriptor(
                cm_start="2026-01-03", cm_end="2026-01-05",
                applicable_phase="treatment"),
            indication_text="头痛", indication_concept="headache",
            indication_mappable=True, treatment_role_confirmed=True,
            treatment_role="treatment",
            study_phase="treatment", study_phase_confirmed=True,
            indication_source_locator=indication_loc)
        _, _, proj = evaluate_and_project(
            ep, rules=(), linkage_coverage_complete=True)
        ind = [x for x in proj.risk_markers
               if x.risk_family == "indication_check"]
        assert len(ind) >= 1
        m = ind[0]
        assert indication_loc.locator_id() in m.source_locator_ids


# ===========================================================================
# Round-2 repair: Defect 3 -- episode + unit bound join
# ===========================================================================

class TestEpisodeUnitBoundJoin:
    """Defect 3: marker joins event only with same episode_id AND
    unit_id membership.  Episode alone is insufficient."""

    def test_adversarial_mismatched_unit_does_not_join(self):
        """Same episode_id but mismatched unit_id must NOT join in either
        direction."""
        from mm_r4.cm_projection import bidirectional_join
        ev = CMJourneyEvent(
            event_id="ep-A", domain_track="cm", subject_ref="S1",
            start="2026-01-01", end="2026-01-05", ongoing=False,
            date_precision="day", episode_id="ep-A",
            display_label="合成药物X",
            source_locator_ids=("loc-cm-1",), unit_ids=("unit-real",))
        # Marker shares episode_id but has a DIFFERENT unit_id.
        rogue = CMRiskMarker(
            marker_id="cmm-rogue", risk_family="prohibited_medication",
            audience_label="禁用药使用待核实",
            monitoring_priority="high",
            anchor_kind=ANCHOR_KIND_OVERLAP, anchor_start="2026-01-01",
            anchor_end="2026-01-05", unit_id="unit-fake",
            candidate_or_risk_id="cand-1",
            source_locator_ids=("loc-cm-1",), rule_locator_ids=("P12-4",),
            query_ids=("q-1",), coverage_gap=False, episode_id="ep-A")
        join = bidirectional_join((ev,), (rogue,))
        # No link in either direction.
        assert join.events_for_marker("cmm-rogue") == ()
        assert join.markers_for_event("ep-A") == ()

    def test_matching_unit_does_join(self):
        from mm_r4.cm_projection import bidirectional_join
        ev = CMJourneyEvent(
            event_id="ep-A", domain_track="cm", subject_ref="S1",
            start="2026-01-01", end="2026-01-05", ongoing=False,
            date_precision="day", episode_id="ep-A",
            display_label="合成药物X",
            source_locator_ids=("loc-cm-1",), unit_ids=("unit-real",))
        marker = CMRiskMarker(
            marker_id="cmm-real", risk_family="prohibited_medication",
            audience_label="禁用药使用待核实",
            monitoring_priority="high",
            anchor_kind=ANCHOR_KIND_OVERLAP, anchor_start="2026-01-01",
            anchor_end="2026-01-05", unit_id="unit-real",
            candidate_or_risk_id="cand-1",
            source_locator_ids=("loc-cm-1",), rule_locator_ids=("P12-4",),
            query_ids=("q-1",), coverage_gap=False, episode_id="ep-A")
        join = bidirectional_join((ev,), (marker,))
        assert "ep-A" in join.events_for_marker("cmm-real")
        assert "cmm-real" in join.markers_for_event("ep-A")

    def test_integrated_projection_join_is_unit_bound(self):
        """The full projection pipeline produces a unit-bound join."""
        ep = make_episode()
        _, _, proj = evaluate_and_project(ep, rules=(make_prohibited_rule(),))
        for m in proj.risk_markers:
            linked = proj.join.events_for_marker(m.marker_id)
            for eid in linked:
                ev = [e for e in proj.events if e.event_id == eid][0]
                assert m.unit_id in ev.unit_ids


# ===========================================================================
# Round-2 repair: Defect 4 -- no internal code as audience label
# ===========================================================================

class TestNoInternalCodeAsLabel:
    """Defect 4: an unknown risk family must fall back to natural Chinese,
    not its internal engineering code."""

    def test_unknown_family_falls_back_to_chinese(self):
        """Construct a marker with a synthetic unknown family and verify
        the audience label resolves via the public label helper."""
        from mm_r4.cm_projection import _risk_family_audience_label
        label = _risk_family_audience_label(
            "synthetic_unknown_xyz", "", "")
        assert label == "用药信息待核实"
        assert "synthetic_unknown_xyz" not in label

    def test_known_family_uses_family_label(self):
        from mm_r4.cm_projection import _risk_family_audience_label
        assert _risk_family_audience_label(
            "prohibited_medication", "", "") == "禁用药使用待核实"
        assert _risk_family_audience_label(
            "ingredient_resolution", "", "") == "复方成分待确认"

    def test_audience_labels_contain_no_backend_terms(self):
        """Scan all risk-family labels and the unknown fallback for
        prohibited internal/backend terms (frozen D02 §9.2/§3.9)."""
        from mm_r4.cm_projection import _UNKNOWN_FAMILY_LABEL
        prohibited = (
            "RiskCandidate", "risk_candidate", "L1_positive", "positive",
            "正式事实", "候选信号", "只读", "generic", "risk_family",
            "prohibited_medication", "restricted_medication",
            "indication_check", "ingredient_resolution",
            "risk_instance", "risk_identity", "signal_type",
        )
        all_labels = list(CM_RISK_FAMILY_LABELS.values()) + [_UNKNOWN_FAMILY_LABEL]
        for label in all_labels:
            for term in prohibited:
                assert term not in label, (
                    f"prohibited term {term!r} in label {label!r}")


# ===========================================================================
# Codex Gate-3 repair: exact full-day parsing and ongoing overlap anchors
# ===========================================================================

class TestExactTemporalAnchorParsing:
    """Only canonical full-day dates and explicit ongoing cutoffs may
    produce deterministic rule-overlap coordinates."""

    def test_full_day_parser_rejects_suffixes_and_timestamps(self):
        from mm_r4.cm_projection import _is_full_day

        assert _is_full_day("2026-01-03") is True
        assert _is_full_day(" 2026-01-03 ") is True
        assert _is_full_day("2026-01-03junk") is False
        assert _is_full_day("2026-01-03T12:30:00") is False
        assert _is_full_day("2026-1-3") is False

    def test_ongoing_with_cutoff_uses_real_rule_intersection(self):
        ep = make_episode(
            cm_start="2026-01-01", cm_end="", ongoing=True,
            cutoff="2026-06-30")
        rule = make_prohibited_rule(
            window_start="2026-02-01", window_end="2026-03-31")

        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        marker = next(
            item for item in proj.risk_markers
            if item.risk_family == "prohibited_medication")
        assert marker.anchor_kind == ANCHOR_KIND_OVERLAP
        assert marker.anchor_start == "2026-02-01"
        assert marker.anchor_end == "2026-03-31"

    def test_ongoing_without_cutoff_stays_fail_closed(self):
        ep = make_episode(
            cm_start="2026-01-01", cm_end="", ongoing=True, cutoff="")
        rule = make_prohibited_rule(
            window_start="2026-02-01", window_end="2026-03-31")

        _, _, proj = evaluate_and_project(ep, rules=(rule,))
        marker = next(
            item for item in proj.risk_markers
            if item.risk_family == "prohibited_medication")
        assert marker.l1_disposition == L1Disposition.BOUNDARY
        assert marker.anchor_start == "2026-01-01"
        assert marker.anchor_end == "持续中"
