"""Cohesive D07 safety evaluator methods."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .d07_safety import (
    AERecordState,
    ActionState,
    ApplicabilityValue,
    CSConsistencyState,
    ClinicalSignificance,
    D07Action,
    D07IntegrityError,
    ExplanationState,
    GradeComparisonState,
    GradeState,
    InterpretationState,
    L1Disposition,
    LifecycleTransition,
    MonitoringPriority,
    PatternState,
    PositiveSubtype,
    RecordStatus,
    ReferenceRangeState,
    RepeatState,
    SeriousnessClue,
    TemporalCooccurrenceState,
    TemporalMatchState,
    TrendKind,
    UnitKind,
    UNIT_ALGORITHM_VERSIONS,
    is_sha256_hex,
    validate_typed_input,
    verify_object_self_hash,
)
from ..projections.d07_journey import build_d07_journey_summary

from .d07_safety_contracts import *
from .d07_safety_contracts import _parse_instant

class D07SafetyPriorityMixin:
    """Methods extracted from the D07 safety evaluator."""

    def _evaluate_organ_patterns(self) -> List[UnitAssessment]:
        units: List[UnitAssessment] = []
        results_by_measure = self._results_by_measure()
        pattern_rules = self.state.typed_input.get("organ_pattern_rule_definitions", [])
        for pattern in pattern_rules:
            monitoring = [m for m in self.state.typed_input.get("monitoring_rules", [])
                          if m.get("rule_kind") == "organ_pattern"]
            if not monitoring:
                continue
            self._record_pattern_trace(pattern)
            roles = pattern.get("required_component_roles", [])
            anchors: List[Mapping[str, Any]] = []
            missing_roles = 0
            for role in roles:
                measure_key = role.get("stable_measure_key")
                results = results_by_measure.get(measure_key, [])
                abnormal = [r for r in results if r.get("reported_abnormal_flag") in ("H", "L")]
                if abnormal:
                    anchors.append(abnormal[-1])
                else:
                    missing_roles += 1
            # 1. Temporal precision of the present anchors.
            times = [self._result_time(r) for r in anchors]
            if any(t is None for t in times):
                state = PatternState.BOUNDARY
                temporal = TemporalCooccurrenceState.PRECISION_INSUFFICIENT
                disposition = L1Disposition.BOUNDARY
                subtype = None
            elif len(anchors) >= 2:
                # 2. Temporal window spread (conflicted beyond the window).
                window_days = self._pattern_window_days(pattern, monitoring)
                spread = (max(times) - min(times)).total_seconds() / 86400.0
                if window_days is not None and spread > window_days:
                    state = PatternState.BOUNDARY
                    temporal = TemporalCooccurrenceState.CONFLICTED
                    disposition = L1Disposition.BOUNDARY
                    subtype = None
                elif missing_roles:
                    state = PatternState.NOT_EVALUABLE
                    temporal = TemporalCooccurrenceState.NOT_EVALUABLE
                    disposition = L1Disposition.NOT_EVALUABLE
                    subtype = None
                else:
                    temporal = TemporalCooccurrenceState.MATCHED
                    # 3. Exposure / alternative-explanation context for
                    # full multi-component patterns.
                    if len(roles) >= 3:
                        bindings = self.state.typed_input.get("producer_consumption_bindings", [])
                        exposure = [b for b in bindings
                                    if b.get("consumption_purpose") == "organ_pattern_exposure_context"]
                        alternative = [b for b in bindings
                                       if b.get("consumption_purpose") == "organ_pattern_alternative_explanation"]
                        if exposure:
                            state = PatternState.MATCHED
                            disposition = L1Disposition.POSITIVE
                            subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
                        elif alternative:
                            state = PatternState.BOUNDARY
                            disposition = L1Disposition.BOUNDARY
                            subtype = None
                        else:
                            state = PatternState.NOT_EVALUABLE
                            disposition = L1Disposition.NOT_EVALUABLE
                            subtype = None
                    else:
                        state = PatternState.MATCHED
                        disposition = L1Disposition.POSITIVE
                        subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
            else:
                # 2b. Single present anchor: a missing role is not evaluable.
                if missing_roles:
                    state = PatternState.NOT_EVALUABLE
                    temporal = TemporalCooccurrenceState.NOT_EVALUABLE
                    disposition = L1Disposition.NOT_EVALUABLE
                    subtype = None
                else:
                    temporal = TemporalCooccurrenceState.MATCHED
                    state = PatternState.MATCHED
                    disposition = L1Disposition.POSITIVE
                    subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
            priority = MonitoringPriority.UNKNOWN
            seriousness = SeriousnessClue.UNKNOWN
            if disposition == L1Disposition.POSITIVE:
                priority = MonitoringPriority.HIGH
                seriousness = SeriousnessClue.PRESENT
            elif disposition == L1Disposition.BOUNDARY:
                priority = MonitoringPriority.MEDIUM
            unit = UnitAssessment(
                unit_kind=UnitKind.ORGAN_PATTERN,
                l1_disposition=disposition,
                primary_subtype=subtype,
                monitoring_priority=priority,
                stable_measure_key=pattern.get("pattern_rule_id"),
                source_result_ids=[a.get("result_id") for a in anchors],
                reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
                grade=None,
                grade_state=GradeState.NOT_APPLICABLE,
                grade_comparison_state=None,
                clinical_significance=ClinicalSignificance.NOT_COLLECTED,
                clinical_significance_consistency=None,
                seriousness_clue=seriousness,
                trend_kind=None,
                repeat_state=None,
                action_state=None,
                explanation_state=None,
                ae_record_state=None,
                temporal_match_state=None,
                pattern_state=state,
                temporal_cooccurrence_state=temporal,
                interpretation_state=None,
            )
            units.append(unit)
        return units

    def _pattern_window_days(self, pattern: Mapping[str, Any],
                             monitoring: List[Mapping[str, Any]]) -> Optional[float]:
        window = pattern.get("temporal_window") or (
            monitoring[0].get("temporal_window") if monitoring else None)
        if not window or len(window) != 2:
            return None
        m = re.match(r"^(\d+(?:\.\d+)?)(h|d)$", str(window[1]).strip())
        if not m:
            return None
        value = float(m.group(1))
        return value / 24.0 if m.group(2) == "h" else value

    def _record_pattern_trace(self, pattern: Mapping[str, Any]) -> None:
        ids = self.state.trace.get("pattern_rule_ids", [])
        if pattern.get("pattern_rule_id") not in ids:
            ids.append(pattern.get("pattern_rule_id"))
        self.state.trace["pattern_rule_ids"] = ids

    def _result_time(self, result: Mapping[str, Any]) -> Optional[datetime]:
        time_refs = {t.get("time_ref_id"): t for t in self.state.typed_input.get("time_refs", [])}
        ref = time_refs.get(result.get("collection_or_exam_time"))
        if ref is None:
            return None
        return _parse_instant(ref.get("value"))

    # ------------------------------------------------------------------
    # Not-applicable unit
    # ------------------------------------------------------------------

    def _build_not_applicable_unit(self, measure: Mapping[str, Any],
                                   evidence: Mapping[str, Any]) -> UnitAssessment:
        authority = {
            b.get("authority_binding_id"): b
            for b in self.state.typed_input.get("authority_bindings", [])
        }.get(evidence.get("authority_binding_id"))
        return UnitAssessment(
            unit_kind=UnitKind.OBSERVATION_INTERPRETATION,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            primary_subtype=None,
            monitoring_priority=MonitoringPriority.LOW,
            stable_measure_key=measure.get("stable_measure_key"),
            source_result_ids=[],
            reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
            grade=None,
            grade_state=GradeState.NOT_APPLICABLE,
            grade_comparison_state=None,
            clinical_significance=ClinicalSignificance.NOT_COLLECTED,
            clinical_significance_consistency=None,
            seriousness_clue=SeriousnessClue.UNKNOWN,
            trend_kind=None,
            repeat_state=None,
            action_state=None,
            explanation_state=None,
            ae_record_state=None,
            temporal_match_state=None,
            pattern_state=None,
            temporal_cooccurrence_state=None,
            interpretation_state=None,
            applicability=evidence.get("applicability"),
            applicability_authority_id=evidence.get("authority_binding_id"),
            applicability_authority_version=authority.get("selected_version") if authority else None,
            applicability_evidence_id=evidence.get("applicability_evidence_id"),
            control_plane_no_match=evidence.get("control_plane_no_match"),
        )

    # ------------------------------------------------------------------
    # Ownership / priority / lifecycle / coverage
    # ------------------------------------------------------------------

    def _resolve_ownership_priority_lifecycle(self) -> None:
        # Priorities per unit.
        for unit in self.state.units:
            unit.monitoring_priority = self._resolve_priority(unit)
        self._resolve_lifecycle()
        self._resolve_ownership()

    def _resolve_priority(self, unit: UnitAssessment) -> str:
        if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
            if unit.l1_disposition != L1Disposition.POSITIVE:
                return MonitoringPriority.LOW
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == unit.stable_measure_key),
                None,
            )
            if obs is not None and obs.monitoring_priority == MonitoringPriority.UNKNOWN:
                return MonitoringPriority.UNKNOWN
            trigger = None
            if obs is not None and obs.source_result_ids:
                by_id = {r.get("result_id"): r
                         for r in self.state.typed_input.get("observed_results", [])}
                trigger = by_id.get(obs.source_result_ids[-1])
            if trigger is not None:
                rules = self._matched_monitoring_rules(unit.stable_measure_key, trigger)
                floors = [r.get("priority_floor") for r in rules if r.get("priority_floor")]
                if MonitoringPriority.HIGH in floors:
                    return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        if unit.l1_disposition == L1Disposition.NOT_APPLICABLE:
            return MonitoringPriority.LOW
        if unit.l1_disposition == L1Disposition.NOT_EVALUABLE:
            return MonitoringPriority.UNKNOWN
        if unit.l1_disposition == L1Disposition.NEGATIVE:
            return MonitoringPriority.LOW
        if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
            return MonitoringPriority.UNKNOWN
        if unit.l1_disposition == L1Disposition.BOUNDARY:
            if unit.range_selection_state is not None or unit.reference_range_state == ReferenceRangeState.BOUNDARY:
                return MonitoringPriority.UNKNOWN
            if unit.grade_state == GradeState.NOT_EVALUABLE:
                return MonitoringPriority.UNKNOWN
            if unit.reference_range_state == ReferenceRangeState.WITHIN_RANGE:
                return MonitoringPriority.LOW
            if unit.grade == "G1":
                return MonitoringPriority.LOW
            if unit.grade == "G2" or unit.reference_range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                return MonitoringPriority.MEDIUM
            return MonitoringPriority.MEDIUM
        # Positive disposition.
        if unit.pattern_elevated:
            pattern_units = [u for u in self.state.units
                             if u.unit_kind == UnitKind.ORGAN_PATTERN]
            pattern_roles = [
                len(p.get("required_component_roles", []))
                for p in self.state.typed_input.get("organ_pattern_rule_definitions", [])
            ]
            all_not_evaluable = bool(pattern_units) and all(
                u.l1_disposition == L1Disposition.NOT_EVALUABLE for u in pattern_units
            )
            conflicted = bool(pattern_units) and any(
                u.temporal_cooccurrence_state == TemporalCooccurrenceState.CONFLICTED
                for u in pattern_units
            )
            if (all_not_evaluable and max(pattern_roles or [0]) < 3
                    and unit.grade not in ("G3", "G4")):
                return MonitoringPriority.MEDIUM
            if conflicted and unit.grade not in ("G3", "G4"):
                return MonitoringPriority.MEDIUM
            return MonitoringPriority.HIGH
        if (self.state.typed_input.get("carry_forward_refs")
                and self.state.typed_input.get("correction_chain_decisions")):
            return MonitoringPriority.LOW
        measure = self._measure_definitions_by_key().get(unit.stable_measure_key, {})
        if measure.get("domain") in ("EG", "VS", "PE", "IMAGING"):
            if unit.grade in ("G3", "G4"):
                return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        if (unit.primary_subtype in (PositiveSubtype.BASELINE_ABNORMAL_WORSENING,
                                     PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING)
                and (unit.grade == "G3" or unit.grade == "G4")):
            return MonitoringPriority.HIGH
        floors = self._unit_rule_floors(unit)
        if floors and MonitoringPriority.HIGH in floors:
            return MonitoringPriority.HIGH
        if unit.grade == "G3" or unit.grade == "G4":
            return MonitoringPriority.HIGH
        if unit.primary_subtype in (PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP,
                                    PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY):
            if unit.grade == "G3":
                return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        # The high-priority clinical flag (a typed action-rule hit, a typed
        # high-grade band hit, or a ratio reaching the typed safety-critical
        # threshold) takes the declared high precedence regardless of the
        # grade-set outcome.  The flag only fires when the frozen precedence
        # policy declares the trigger; every magnitude threshold comes from
        # typed rules (monitoring predicates / grade rules / the precedence
        # rule's typed safety threshold), never an evaluator-internal constant.
        policy = self.state.typed_input.get("priority_policy") or {}
        flag_declared = bool(policy.get("high_priority_clinical_flag_rules"))
        if flag_declared and unit.source_result_ids:
            by_id = {r.get("result_id"): r
                     for r in self.state.typed_input.get("observed_results", [])}
            anchor = by_id.get(unit.source_result_ids[-1])
            if anchor is not None:
                if self._action_class_hit(unit.stable_measure_key, anchor):
                    return MonitoringPriority.HIGH
                threshold = self._safety_critical_ratio_threshold()
                if threshold is not None:
                    ratio = self._result_ratio(anchor)
                    if ratio is not None and ratio >= threshold:
                        return MonitoringPriority.HIGH
        if unit.primary_subtype == PositiveSubtype.ORGAN_PATTERN_CLUE:
            return MonitoringPriority.HIGH
        if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
            return MonitoringPriority.MEDIUM
        if unit.grade == "G2":
            return MonitoringPriority.MEDIUM
        if unit.grade == "G1":
            return MonitoringPriority.LOW
        if unit.grade_state == GradeState.NOT_GRADED:
            return MonitoringPriority.MEDIUM
        return MonitoringPriority.MEDIUM

    def _unit_rule_floors(self, unit: UnitAssessment) -> List[str]:
        if not unit.source_result_ids:
            return []
        by_id = {r.get("result_id"): r
                 for r in self.state.typed_input.get("observed_results", [])}
        anchor = by_id.get(unit.source_result_ids[-1])
        if anchor is None:
            return []
        rules = self._matched_monitoring_rules(unit.stable_measure_key, anchor)
        return [r.get("priority_floor") for r in rules if r.get("priority_floor")]

    def _resolve_ownership(self) -> None:
        units = self.state.units
        blocked = self.state.blocked
        applicability_evidence = self.state.typed_input.get("applicability_evidence", [])
        if blocked:
            self.state.ownership = {
                "d07_action": D07Action.HANDOFF_ONLY,
                "owner_domain": "D05",
                "handoff_target_domain": "D05",
                "downstream_handoff_present": True,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        if applicability_evidence:
            self.state.ownership = {
                "d07_action": D07Action.NOT_APPLICABLE,
                "owner_domain": "D07",
                "handoff_target_domain": None,
                "downstream_handoff_present": False,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        if not units and not self.state.admitted_results:
            self.state.ownership = {
                "d07_action": D07Action.HANDOFF_ONLY,
                "owner_domain": "D05",
                "handoff_target_domain": "D05",
                "downstream_handoff_present": True,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        risk_present = any(
            u.l1_disposition == L1Disposition.POSITIVE for u in units
        )
        lifecycle = self.state.lifecycle
        blocked_lifecycle = bool(lifecycle) and (
            lifecycle.get("transition") == LifecycleTransition.CLOSED
            or lifecycle.get("transition") == LifecycleTransition.NONE
            or (lifecycle.get("transition") == LifecycleTransition.CARRY_FORWARD and not risk_present)
        )
        risk_candidate = risk_present if blocked_lifecycle else True
        handoff_domain = self._downstream_handoff_domain(units)
        pd_permitted = self._pd_wording_permitted(units)
        self.state.ownership = {
            "d07_action": D07Action.EVALUATE_AND_OWN,
            "owner_domain": "D07",
            "handoff_target_domain": handoff_domain,
            "downstream_handoff_present": handoff_domain is not None,
            "risk_owner": "D07",
            "query_owner": "D07",
            "risk_candidate_present": risk_candidate,
            "query_draft_present": risk_candidate,
            "pd_wording_permitted": pd_permitted,
        }

    def _downstream_handoff_domain(self, units: List[UnitAssessment]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        for unit in units:
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                return "D01"
            if unit.primary_subtype == PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY:
                for p in producer:
                    if p.get("producer_domain") in ("D02", "D03"):
                        return p.get("producer_domain")
                return "D02"
            if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
                if self.state.typed_input.get("d04_context_refs"):
                    return "D04"
                for p in producer:
                    if p.get("producer_domain") == "D03":
                        return "D03"
                return "D04"
        for p in producer:
            if p.get("permitted_outputs") == "handoff_only" and p.get("producer_domain") != "D10":
                return p.get("producer_domain")
        return None

    def _pd_wording_permitted(self, units: List[UnitAssessment]) -> Optional[bool]:
        d04 = self.state.typed_input.get("d04_context_refs", [])
        if d04 and any(u.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP for u in units):
            return True
        return None

    def _resolve_lifecycle(self) -> None:
        carry = self.state.typed_input.get("carry_forward_refs", [])
        previous_scope = self.state.typed_input.get("previous_run_scope_binding")
        has_out_of_cutoff = any(
            r.get("record_status") == RecordStatus.OUT_OF_CUTOFF
            for r in self.state.typed_input.get("observed_results", [])
        )
        if not carry and previous_scope is None and not has_out_of_cutoff:
            self.state.lifecycle = {}
            return
        risk_present = any(
            u.l1_disposition == L1Disposition.POSITIVE for u in self.state.units
        )
        if not carry and previous_scope is None:
            self.state.lifecycle = {
                "transition": LifecycleTransition.NONE,
                "carry_forward_source_risk_id": None,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": False,
                "machine_close_forbidden": False,
            }
            return
        ref = carry[0] if carry else {}
        source_risk = ref.get("source_risk_id")
        rule_version_changed = self._rule_version_changed(previous_scope)
        prev_results = self.state.typed_input.get("previous_observed_results", [])
        prev_had_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L") for r in prev_results
        )
        if risk_present:
            if source_risk is not None and prev_results and not prev_had_abnormal:
                # The previous run's risk was closed (recovery); a new
                # abnormal hit reopens it.
                self.state.lifecycle = {
                    "transition": LifecycleTransition.REOPENED,
                    "carry_forward_source_risk_id": source_risk,
                    "close_reason": None,
                    "reopen_trigger_present": True,
                    "rule_version_changed": rule_version_changed,
                    "machine_close_forbidden": False,
                }
                return
            transition = LifecycleTransition.CARRY_FORWARD if source_risk else LifecycleTransition.NEW_RISK
            self.state.lifecycle = {
                "transition": transition,
                "carry_forward_source_risk_id": source_risk,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": rule_version_changed,
                "machine_close_forbidden": False,
            }
            return
        withdrawn = self._abnormal_withdrawn()
        current_has_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L")
            and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
            for r in self.state.typed_input.get("observed_results", [])
        )
        if withdrawn:
            close_reason = "withdrawn_by_source"
        elif current_has_abnormal:
            close_reason = "explained_by_verified_repeat"
        else:
            # No risk in the current run and nothing withdrawn: the prior
            # risk record carries forward unchanged (rule-set version changes
            # are marked separately).
            self.state.lifecycle = {
                "transition": LifecycleTransition.CARRY_FORWARD,
                "carry_forward_source_risk_id": source_risk,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": rule_version_changed,
                "machine_close_forbidden": False,
            }
            return
        self.state.lifecycle = {
            "transition": LifecycleTransition.CLOSED,
            "carry_forward_source_risk_id": source_risk,
            "close_reason": close_reason,
            "reopen_trigger_present": False,
            "rule_version_changed": rule_version_changed,
            "machine_close_forbidden": False,
        }

    def _rule_version_changed(self, previous_scope: Optional[Mapping[str, Any]]) -> bool:
        if not previous_scope:
            return False
        current = (self.state.scope.get("rule_set_versions") or {})
        prev = (previous_scope.get("rule_set_versions") or {})
        return current != prev

    def _abnormal_withdrawn(self) -> bool:
        for result in self.state.typed_input.get("observed_results", []):
            if (result.get("record_status") == RecordStatus.WITHDRAWN
                    and result.get("reported_abnormal_flag") in ("H", "L")):
                return True
        return False
