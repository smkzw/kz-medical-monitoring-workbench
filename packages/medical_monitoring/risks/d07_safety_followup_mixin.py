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
from .d07_safety_contracts import _dec, _parse_window_days, _window_bounds

class D07SafetyFollowupMixin:
    """Methods extracted from the D07 safety evaluator."""

    def _evaluate_followup_obligations(self,
                                       obs_dispositions: Mapping[str, str],
                                       obs_subtypes: Mapping[str, Optional[str]]
                                       ) -> List[UnitAssessment]:
        units: List[UnitAssessment] = []
        results_by_measure = self._results_by_measure()
        for measure_key, results in results_by_measure.items():
            matches = [
                r for r in results
                if self._matched_monitoring_rules(measure_key, r)
            ]
            if not matches:
                continue
            # Predicate matches split into episodes only when a recovery
            # (normal result) between consecutive matches is followed by the
            # next match beyond the recurrent window; otherwise the matches
            # stay in one episode.
            episodes: List[List[Mapping[str, Any]]] = []
            current = [matches[0]]
            for m in matches[1:]:
                prev = current[-1]
                idx_prev = results.index(prev)
                idx_m = results.index(m)
                between = results[idx_prev + 1:idx_m]
                last_normal = None
                for r in between:
                    if r.get("reported_abnormal_flag") not in ("H", "L"):
                        last_normal = r
                t = self._result_time(m)
                nt = self._result_time(last_normal) if last_normal is not None else None
                trend_rule = self._trend_rule()
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                ) if trend_rule else None
                if (t is not None and nt is not None and recurrent_days is not None
                        and (t - nt).total_seconds() / 86400.0 > recurrent_days):
                    episodes.append(current)
                    current = [m]
                else:
                    current.append(m)
            episodes.append(current)
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            stable_abnormal = (
                obs is not None and obs.trend_kind == TrendKind.STABLE_ABNORMAL
            )
            if stable_abnormal:
                # A long-stable abnormal baseline: the follow-up anchors to
                # the first match (the baseline itself).
                trigger = matches[0]
            else:
                last_episode = episodes[-1]
                trigger = next(
                    (m for m in last_episode if m.get("visit_ref") is not None),
                    matches[0],
                )
            matched_rules = self._matched_monitoring_rules(measure_key, trigger)
            action_rule_fired = any(r.get("rule_kind") == "action" for r in matched_rules)
            obs_worsening = obs_subtypes.get(measure_key) == PositiveSubtype.BASELINE_ABNORMAL_WORSENING
            if action_rule_fired and obs_worsening:
                # Worsening baseline: the required clinical review dominates
                # and is not documented.
                repeat_state = None
                temporal = None
                obligation = None
            elif action_rule_fired and self._repeat_candidate(measure_key, trigger) is None:
                # Action-class abnormality without a repeat: the action
                # obligation dominates.
                repeat_state = None
                temporal = None
                obligation = self._select_obligation(matched_rules)
            else:
                obligation = self._select_obligation(matched_rules)
                repeat_state, temporal = self._repeat_state(measure_key, trigger, obligation)
            action_state = self._action_state(measure_key, trigger, matched_rules, obligation)
            explanation_state = self._explanation_state(measure_key)
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (explanation_state is not None
                    and (obs is None
                         or obs.clinical_significance_consistency != CSConsistencyState.CONSISTENT)):
                explanation_state = None
            cs_present = any(
                r.get("reported_cs_ncs") in (ClinicalSignificance.CS, ClinicalSignificance.NCS)
                for r in results
            )
            producer = self.state.typed_input.get("producer_consumption_bindings", [])
            ae_matching = any(
                p.get("producer_domain") == "D01"
                and p.get("permitted_outputs") == "evidence_only"
                and not str(p.get("producer_object_id", "")).endswith("NONE")
                for p in producer
            )
            ae_state = (
                AERecordState.MATCHING_RECORD_PRESENT
                if (cs_present and ae_matching) else None
            )
            subtype = self._followup_subtype(
                measure_key, results, matches, trigger, repeat_state, action_state,
                explanation_state, ae_state, matched_rules, obligation,
                obs_subtypes=obs_subtypes,
            )
            if subtype is None:
                disposition = L1Disposition.NEGATIVE
            else:
                disposition = L1Disposition.POSITIVE
            obs_disp = obs_dispositions.get(measure_key)
            if obs_disp not in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE):
                continue
            if (subtype is None and repeat_state == RepeatState.REQUIRED_MET):
                # A met repeat that recovered to normal closes the episode
                # without emitting a follow-up unit when the CS chain already
                # documented the closure.
                repeat_candidate = self._repeat_candidate(measure_key, trigger)
                obs_cs = obs.clinical_significance if obs is not None else None
                obs_csc = obs.clinical_significance_consistency if obs is not None else None
                if (repeat_candidate is not None
                        and repeat_candidate.get("reported_abnormal_flag") not in ("H", "L")
                        and obs_cs == ClinicalSignificance.CS
                        and obs_csc == CSConsistencyState.CONSISTENT):
                    continue
            unit = UnitAssessment(
                unit_kind=UnitKind.FOLLOWUP_OBLIGATION,
                l1_disposition=disposition,
                primary_subtype=subtype,
                monitoring_priority=MonitoringPriority.UNKNOWN,
                stable_measure_key=measure_key,
                source_result_ids=[trigger.get("result_id")],
                reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
                grade=None,
                grade_state=GradeState.NOT_APPLICABLE,
                grade_comparison_state=None,
                clinical_significance=ClinicalSignificance.NOT_COLLECTED,
                clinical_significance_consistency=None,
                seriousness_clue=SeriousnessClue.ABSENT,
                trend_kind=None,
                repeat_state=repeat_state,
                action_state=action_state,
                explanation_state=explanation_state,
                ae_record_state=ae_state,
                temporal_match_state=temporal,
                pattern_state=None,
                temporal_cooccurrence_state=None,
                interpretation_state=None,
            )
            units.append(unit)
        return units

    def _repeat_candidate(self, measure_key: str,
                          trigger: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        trigger_time = self._result_time(trigger)
        later = [
            r for r in self.state.admitted_results
            if r.get("stable_measure_key") == measure_key
            and r is not trigger
            and (trigger_time is None or (self._result_time(r) or trigger_time) >= trigger_time)
            and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
        ]
        return later[0] if later else None

    def _last_abnormal_result(self, results: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        for r in reversed(results):
            if r.get("reported_abnormal_flag") in ("H", "L"):
                return r
        return None

    def _first_matching_result(self, measure_key: str,
                               results: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        for r in results:
            if r.get("reported_abnormal_flag") not in ("H", "L"):
                continue
            if r.get("visit_ref") is None:
                continue
            if self._matched_monitoring_rules(measure_key, r):
                return r
        return None

    def _trend_rule(self) -> Optional[Mapping[str, Any]]:
        rules = self.state.typed_input.get("trend_rules", [])
        return rules[0] if rules else None

    def _action_rule_fired(self, measure_key: str,
                           trigger: Mapping[str, Any]) -> bool:
        """Whether a typed action-kind monitoring rule matches the result."""
        return any(
            r.get("rule_kind") == "action"
            for r in self._matched_monitoring_rules(measure_key, trigger)
        )

    def _high_grade_band_hit(self, measure_key: str,
                              trigger: Mapping[str, Any]) -> bool:
        """The ratio falls inside a G3+ rule band of any bound grade set of
        the measure (the typed high-grade magnitude class)."""
        ratio = self._result_ratio(trigger)
        if ratio is None:
            return False
        by_rule = {r.get("grade_rule_id"): r
                   for r in self.state.typed_input.get("grade_rules", [])}
        for grade_set in self.state.typed_input.get("grade_rule_sets", []):
            if grade_set.get("stable_measure_key") != measure_key:
                continue
            for rid in grade_set.get("ordered_grade_rule_ids", []):
                rule = by_rule.get(rid)
                if rule is None or rule.get("grade") not in ("G3", "G4", "G5"):
                    continue
                if self._ratio_in_grade_band(ratio, rule):
                    return True
        return False

    @staticmethod
    def _ratio_in_grade_band(ratio: Decimal, rule: Mapping[str, Any]) -> bool:
        comparator = rule.get("comparator")
        lower = _dec(rule.get("lower"))
        upper = _dec(rule.get("upper"))
        lower_inc = rule.get("lower_inclusive") is not False
        upper_inc = rule.get("upper_inclusive") is True
        if comparator == "between" and lower is not None and upper is not None:
            above = ratio > lower or (lower_inc and ratio == lower)
            below = ratio < upper or (upper_inc and ratio == upper)
            return bool(above and below)
        if comparator in ("ge", "gte"):
            return bool(ratio >= lower) if lower is not None else False
        if comparator == "gt":
            return bool(ratio > lower) if lower is not None else False
        if comparator in ("le", "lte"):
            return bool(ratio <= upper) if upper is not None else False
        if comparator == "lt":
            return bool(ratio < upper) if upper is not None else False
        if lower is not None and upper is None:
            return bool(ratio >= lower)
        if lower is None and upper is not None:
            return bool(ratio <= upper)
        return False

    def _action_class_hit(self, measure_key: str,
                          trigger: Mapping[str, Any]) -> bool:
        """The typed action class: an action-rule hit, or a ratio inside a
        high-grade band of any bound grade set."""
        if self._action_rule_fired(measure_key, trigger):
            return True
        return self._high_grade_band_hit(measure_key, trigger)

    def _matched_monitoring_rules(self, measure_key: str,
                                  trigger: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        matched: List[Mapping[str, Any]] = []
        for rule in self.state.typed_input.get("monitoring_rules", []):
            if measure_key not in rule.get("applicable_measure_keys", []):
                continue
            if rule.get("rule_kind") in ("organ_pattern", "other"):
                continue
            if self._predicates_match(rule, trigger):
                matched.append(rule)
        return matched

    def _predicates_match(self, rule: Mapping[str, Any], trigger: Mapping[str, Any]) -> bool:
        predicates = {
            p.get("predicate_id"): p
            for p in self.state.typed_input.get("monitoring_predicates", [])
        }
        ratio = self._trigger_ratio(trigger)
        if ratio is None:
            return False
        for pid in rule.get("ordered_predicate_ids", []):
            pred = predicates.get(pid)
            if pred is None:
                continue
            threshold = _dec(pred.get("right_typed_value"))
            comparator = pred.get("comparator")
            if threshold is None:
                continue
            if comparator == "ge" and ratio >= threshold:
                return True
            if comparator == "gt" and ratio > threshold:
                return True
            if comparator == "le" and ratio <= threshold:
                return True
            if comparator == "lt" and ratio < threshold:
                return True
            if comparator == "eq" and ratio == threshold:
                return True
            if comparator == "between":
                lo = _dec(pred.get("lower", pred.get("right_typed_value")))
                hi = _dec(pred.get("upper"))
                if lo is not None and hi is not None and lo <= ratio <= hi:
                    return True
        return False

    def _trigger_ratio(self, trigger: Mapping[str, Any]) -> Optional[Decimal]:
        value = _dec(trigger.get("numeric_value"))
        if value is None:
            return None
        ranges = self._applicable_ranges(trigger.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        upper = _dec(ranges[0].get("upper"))
        if upper:
            return value / upper
        return None

    def _record_monitoring_trace(self, measure_key: str) -> None:
        rules = self.state.trace.get("monitoring_rule_ids", [])
        preds = self.state.trace.get("monitoring_predicate_ids", [])
        for rule in self.state.typed_input.get("monitoring_rules", []):
            if measure_key not in rule.get("applicable_measure_keys", []):
                continue
            if rule.get("rule_id") not in rules:
                rules.append(rule.get("rule_id"))
            for pid in rule.get("ordered_predicate_ids", []):
                if pid not in preds:
                    preds.append(pid)
        self.state.trace["monitoring_rule_ids"] = rules
        self.state.trace["monitoring_predicate_ids"] = preds

    def _select_obligation(self, matched_rules: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        obligations = self.state.typed_input.get("action_obligation_definitions", [])
        trigger_ids = {r.get("rule_id") for r in matched_rules}
        candidates = [o for o in obligations if o.get("trigger_rule_id") in trigger_ids]
        if not candidates:
            return None
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        has_d04 = bool(self.state.typed_input.get("d04_context_refs")) or any(
            p.get("producer_domain") == "D04" for p in producer
        )
        has_d03 = any(
            p.get("producer_domain") == "D03"
            and p.get("permitted_outputs") == "handoff_only"
            for p in producer
        )

        def priority(o: Mapping[str, Any]) -> int:
            kind = o.get("obligation_kind")
            if kind == "protocol_execution_check" and (has_d04 or has_d03):
                return 0
            order = {"treatment_action": 1, "repeat": 2, "clinical_review": 3,
                     "ae_assessment": 4, "protocol_execution_check": 5}
            return order.get(kind, 6)
        return min(candidates, key=priority)

    def _repeat_state(self, measure_key: str, trigger: Mapping[str, Any],
                      obligation: Optional[Mapping[str, Any]] = None
                      ) -> Tuple[Optional[str], Optional[str]]:
        candidate = self._repeat_candidate(measure_key, trigger)
        if candidate is None:
            return RepeatState.REQUIRED_MISSING, None
        # The repeat window comes from the repeat-kind obligation when
        # present, regardless of the selected follow-up obligation.
        repeat_obligation = next(
            (o for o in self.state.typed_input.get("action_obligation_definitions", [])
             if o.get("obligation_kind") == "repeat"),
            obligation,
        )
        trigger_time = self._result_time(trigger)
        window = repeat_obligation.get("temporal_window") if repeat_obligation else None
        within = True
        if trigger_time is not None and window:
            lo, hi = _window_bounds(window, trigger_time)
            candidate_time = self._result_time(candidate)
            if candidate_time is not None and hi is not None and candidate_time > hi:
                within = False
        # The repeat must share the context of the episode baseline (first
        # result of the measure series).
        baseline = None
        for r in self.state.admitted_results:
            if r.get("stable_measure_key") == measure_key:
                baseline = r
                break
        context_mismatch = False
        if baseline is not None:
            for f in ("method_kind", "specimen_kind", "original_unit"):
                if (candidate.get(f) != baseline.get(f)
                        and (candidate.get(f) is not None or baseline.get(f) is not None)):
                    context_mismatch = True
                    break
        if context_mismatch:
            return RepeatState.WRONG_MEASURE_OR_METHOD, None
        if not within:
            return RepeatState.WRONG_WINDOW, TemporalMatchState.OUTSIDE_WINDOW
        return RepeatState.REQUIRED_MET, TemporalMatchState.MATCHED

    def _action_state(self, measure_key: str, trigger: Mapping[str, Any],
                      matched_rules: List[Mapping[str, Any]],
                      obligation: Optional[Mapping[str, Any]] = None) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        bindings = [p for p in producer if p.get("producer_domain") in ("D02", "D03", "D04")]
        for b in bindings:
            if (b.get("producer_domain") in ("D02", "D03")
                    and b.get("permitted_outputs") == "handoff_only"
                    and not str(b.get("producer_object_id", "")).endswith("NONE")):
                return ActionState.DISCORDANT
            if b.get("permitted_outputs") == "handoff_only":
                return ActionState.REQUIRED_MISSING
        evidence_only = [b for b in bindings if b.get("permitted_outputs") == "evidence_only"]
        if evidence_only:
            return ActionState.REQUIRED_MISSING
        cs_present = any(
            r.get("reported_cs_ncs") == ClinicalSignificance.CS
            for r in self.state.admitted_results
            if r.get("stable_measure_key") == measure_key
        )
        if cs_present:
            ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
            if ae_bindings and not str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return ActionState.REQUIRED_MET
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (obs is not None
                    and obs.clinical_significance_consistency == CSConsistencyState.INCONSISTENT):
                return ActionState.REQUIRED_MISSING
            return None
        action_rule_fired = any(r.get("rule_kind") == "action" for r in matched_rules)
        if action_rule_fired:
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (obs is not None
                    and obs.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING):
                # The required clinical review is not documented.
                return ActionState.REQUIRED_MISSING
            if self._repeat_candidate(measure_key, trigger) is not None:
                return ActionState.REQUIRED_MET
            return ActionState.REQUIRED_MISSING
        return None

    def _explanation_state(self, measure_key: str) -> Optional[str]:
        reasons = self.state.typed_input.get("clinical_significance_reason_refs", [])
        reviews = self.state.typed_input.get("clinical_review_refs", [])
        if reviews or reasons:
            return ExplanationState.DOCUMENTED_CONSISTENT
        return None

    def _ae_state(self, measure_key: str, trigger: Mapping[str, Any]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
        if ae_bindings:
            if str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return AERecordState.HANDOFF_REQUIRED
            return AERecordState.MATCHING_RECORD_PRESENT
        return None

    def _followup_subtype(
        self, measure_key: str, results: List[Mapping[str, Any]],
        matches: List[Mapping[str, Any]], trigger: Mapping[str, Any],
        repeat_state: Optional[str], action_state: Optional[str],
        explanation_state: Optional[str], ae_state: Optional[str],
        matched_rules: List[Mapping[str, Any]],
        obligation: Optional[Mapping[str, Any]] = None,
        obs_subtypes: Optional[Mapping[str, Optional[str]]] = None,
    ) -> Optional[str]:
        if action_state == ActionState.DISCORDANT:
            return PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY
        if action_state == ActionState.REQUIRED_MISSING:
            producer = self.state.typed_input.get("producer_consumption_bindings", [])
            has_handoff_none = any(
                p.get("permitted_outputs") == "handoff_only"
                and str(p.get("producer_object_id", "")).endswith("NONE")
                for p in producer
            )
            if (has_handoff_none
                    or (obligation is not None
                        and obligation.get("obligation_kind") == "protocol_execution_check")
                    or self.state.typed_input.get("d04_context_refs")):
                return PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        # The last predicate match must be satisfied: either it is itself a
        # valid repeat of an earlier trigger or it has a valid repeat after.
        last_match = matches[-1]
        last_satisfied = self._match_satisfied(last_match, trigger, matches)
        if repeat_state in (RepeatState.REQUIRED_MISSING, RepeatState.WRONG_WINDOW,
                            RepeatState.WRONG_MEASURE_OR_METHOD):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if (obs_subtypes is not None
                and obs_subtypes.get(measure_key) == PositiveSubtype.CS_INCONSISTENCY
                and not last_satisfied):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if (obs_subtypes is not None
                and obs_subtypes.get(measure_key) == PositiveSubtype.CS_INCONSISTENCY):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if ae_state == AERecordState.HANDOFF_REQUIRED:
            return PositiveSubtype.AE_RECORDING_HANDOFF_CLUE
        return None

    def _match_satisfied(self, last_match: Mapping[str, Any],
                         trigger: Mapping[str, Any],
                         matches: List[Mapping[str, Any]]) -> bool:
        # The last match satisfies the episode when it IS the trigger's
        # repeat (the follow-up was performed and closed the episode).
        candidate = self._repeat_candidate(
            trigger.get("stable_measure_key"), trigger)
        if candidate is last_match:
            return True
        # A recurrent event within the recurrent gap window of the previous
        # recovery is satisfied by the recovery itself.
        results = self.state.admitted_results
        if last_match in results:
            idx = results.index(last_match)
            last_normal = None
            for r in reversed(results[:idx]):
                if r.get("reported_abnormal_flag") not in ("H", "L"):
                    last_normal = r
                    break
            if last_normal is not None:
                lt, nt = self._result_time(last_match), self._result_time(last_normal)
                trend_rule = self._trend_rule()
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                ) if trend_rule else None
                if (lt is not None and nt is not None and recurrent_days is not None
                        and 0 < (lt - nt).total_seconds() / 86400.0 <= recurrent_days):
                    return True
        # Or the last match has its own valid repeat after it.
        own = self._repeat_candidate(
            trigger.get("stable_measure_key"), last_match)
        if own is not None:
            return self._repeat_relation_valid(last_match, own)
        return False

    def _repeat_relation_valid(
        self, trigger: Mapping[str, Any], candidate: Mapping[str, Any]
    ) -> bool:
        trigger_time = self._result_time(trigger)
        candidate_time = self._result_time(candidate)
        if trigger_time is None or candidate_time is None:
            return False
        repeat_obligation = next(
            (
                obligation
                for obligation in self.state.typed_input.get(
                    "action_obligation_definitions", []
                )
                if obligation.get("obligation_kind") == "repeat"
            ),
            None,
        )
        window = (
            repeat_obligation.get("temporal_window") if repeat_obligation else None
        )
        if trigger_time is not None and window:
            _lower, upper = _window_bounds(window, trigger_time)
            if candidate_time is not None and upper is not None and candidate_time > upper:
                return False
        delta = (candidate_time - trigger_time).total_seconds() / 86400.0
        if not 0 < delta:
            return False
        for field in ("method_kind", "specimen_kind", "original_unit"):
            if candidate.get(field) != trigger.get(field) and (
                candidate.get(field) is not None or trigger.get(field) is not None
            ):
                return False
        return True
