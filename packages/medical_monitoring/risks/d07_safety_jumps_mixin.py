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
from .d07_safety_contracts import _dec

class D07SafetyJumpsMixin:
    """Methods extracted from the D07 safety evaluator."""

    def _range_lab_candidate(self, measure_key: str,
                             unit: UnitAssessment) -> Optional[str]:
        """The reference-range / conversion lab target for an observation
        without follow-up obligations (or None)."""
        input_data = self.state.typed_input
        results = [r for r in self.state.admitted_results
                   if r.get("stable_measure_key") == measure_key]
        if not results:
            return None
        anchor = self._last_abnormal_result(results) or results[-1]
        ranges = self._applicable_ranges(measure_key)
        declared = [r for r in input_data.get("reference_range_definitions", [])
                    if r.get("stable_measure_key") == measure_key]
        flag = anchor.get("reported_abnormal_flag")
        # Explicit conversion rule.
        if ranges and anchor.get("original_unit") and ranges[0].get("unit")                 and anchor.get("original_unit") != ranges[0].get("unit"):
            for rule in input_data.get("unit_conversion_rules", []):
                if (rule.get("from_unit") == anchor.get("original_unit")
                        and rule.get("to_unit") == ranges[0].get("unit")):
                    return rule.get("conversion_rule_id")
        # A sex/age selection that collapsed several declared ranges to one
        # applicable range is itself the lab target (also for within-range,
        # unflagged values).
        if len(declared) > 1 and len(ranges) == 1:
            return ranges[0].get("range_definition_id")
        # Generic multi-range with a single value-containing selection.
        if len(ranges) > 1 and not all(
                r.get("sex") in ("male", "female") for r in ranges):
            containing = [r for r in ranges if self._range_contains(anchor, r)]
            if len(containing) == 1:
                return containing[0].get("range_definition_id")
        if flag in ("H", "L"):
            same_unit = (
                not ranges
                or not anchor.get("original_unit")
                or not ranges[0].get("unit")
                or anchor.get("original_unit") == ranges[0].get("unit")
            )
            if same_unit and ranges:
                if len(ranges) > 1 and all(
                        r.get("sex") in ("male", "female") for r in ranges):
                    return ranges[0].get("range_definition_id")
                if self._range_endpoint_equality(anchor, ranges[0]):
                    return ranges[0].get("range_definition_id")
        if flag in ("H", "L") and not ranges and declared:
            range_authority = self._authority_by_claim().get("reference_range")
            if range_authority is None or range_authority.get("decision_status") != "not_evaluable":
                return declared[0].get("range_definition_id")
        return None

    def _append_risk_jumps(self, jumps: List[Dict[str, Any]], anchor: str,
                           unit: UnitAssessment) -> None:
        input_data = self.state.typed_input
        producer = input_data.get("producer_consumption_bindings") or []
        measures = {m.get("stable_measure_key"): m for m in input_data.get("measure_definitions", [])}
        measure = measures.get(unit.stable_measure_key, {})
        domain = measure.get("domain")

        def push(kind: str, target: str) -> None:
            jumps.append({
                "cardinality": "one", "source_object_id": anchor,
                "target_kind": kind, "target_object_id": target,
            })

        measure_keys = {r.get("stable_measure_key") for r in input_data.get("observed_results", [])}
        single_measure = len(measure_keys) == 1
        matched_rules = [
            r for r in input_data.get("monitoring_rules", [])
            if unit.stable_measure_key in r.get("applicable_measure_keys", [])
        ]
        pattern_defs = input_data.get("organ_pattern_rule_definitions") or []
        corrections = input_data.get("correction_chain_decisions") or []
        carry_refs = input_data.get("carry_forward_refs") or []
        reviews = input_data.get("clinical_review_refs") or []
        reasons = input_data.get("clinical_significance_reason_refs") or []
        d04_refs = input_data.get("d04_context_refs") or []
        handoff_producers = [p for p in producer
                             if p.get("producer_domain") in ("D01", "D02", "D03", "D04", "D06", "D10")]

        def push_producer(p: Mapping[str, Any]) -> None:
            pdom = p.get("producer_domain")
            if pdom == "D01":
                push("ae_record", p.get("producer_object_id"))
            elif pdom == "D02":
                push("cm_record", p.get("producer_object_id"))
            elif pdom == "D03" and not any(
                    j.get("target_kind") == "ip_action" for j in jumps):
                push("ip_action", p.get("producer_object_id"))
            elif pdom == "D04":
                push("protocol_clause", p.get("producer_object_id"))
            elif pdom in ("D06", "D10"):
                push("listing_row", p.get("producer_object_id"))

        if pattern_defs:
            # The pattern evaluation surfaces the typed handoff links then
            # its rule — once, from the first present component anchor.
            pat = next((u for u in self.state.units
                        if u.unit_kind == UnitKind.ORGAN_PATTERN), None)
            roles = pattern_defs[0].get("required_component_roles", [])
            role_keys = [r.get("stable_measure_key") for r in roles]
            first_component_anchor = None
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        first_component_anchor = r.get("result_id")
                        break
                if first_component_anchor:
                    break
            if anchor != first_component_anchor:
                return
            temporal = pat.temporal_cooccurrence_state if pat is not None else None
            present_count = 0
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        present_count += 1
                        break
            no_lab = (
                temporal in (TemporalCooccurrenceState.PRECISION_INSUFFICIENT,
                             TemporalCooccurrenceState.CONFLICTED)
                or (pat is not None and pat.l1_disposition == L1Disposition.NOT_EVALUABLE
                    and present_count < len(roles))
            )
            obligations = input_data.get("action_obligation_definitions") or []
            pure_exposure = bool(producer) and all(
                p.get("producer_object_type") == "IP_EXPOSURE" for p in producer)
            producers_first = bool(obligations) or not pure_exposure
            if producers_first:
                for p in producer:
                    push_producer(p)
            if not no_lab:
                push("lab_manual_rule", pattern_defs[0].get("pattern_rule_id"))
            if not producers_first:
                for p in producer:
                    push_producer(p)
            return

        for p in producer:
            push_producer(p)
        followup = next(
            (u for u in self.state.units
             if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
             and u.stable_measure_key == unit.stable_measure_key),
            None,
        )
        review_gate = (
            unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT
            or (followup is not None
                and followup.l1_disposition == L1Disposition.NEGATIVE)
        )
        if review_gate and reviews:
            push("listing_row", reviews[0].get("review_ref_id"))
        elif unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
            for ref in reasons:
                push("listing_row", ref.get("reason_ref_id"))
        for ref in d04_refs:
            clause = ref.get("protocol_clause_ref")
            if clause is not None:
                push("protocol_clause", clause)

        # A D04-deviation run, a handoff-linking run, or a correction chain
        # surfaces only the links above; the action-rule lab follows the
        # D04-context deviation.
        if d04_refs:
            if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
                action_rule = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
                if action_rule is not None:
                    push("lab_manual_rule", action_rule.get("rule_id"))
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                                   if o.get("obligation_kind") == "ae_assessment"), None)
                if obligation is not None:
                    push("protocol_clause", obligation.get("obligation_definition_id"))
            return
        if not single_measure:
            # Multi-measure runs surface only the listings.
            return

        # The examination-report link fires for the interpreted exam
        # findings, also alongside the handoff links.
        if domain in ("VS", "EG", "PE", "IMAGING", "OTHER"):
            if unit.interpretation_state in (
                    InterpretationState.CONSISTENT, InterpretationState.INCONSISTENT):
                req = next((r for r in input_data.get("examination_requirement_sets", [])
                            if r.get("domain") == domain), None)
                if req is not None:
                    series = next(
                        (r.get("repeat_series_ref")
                         for r in input_data.get("observed_results", [])
                         if r.get("stable_measure_key") == unit.stable_measure_key
                         and r.get("repeat_series_ref")),
                        None,
                    )
                    push("examination_report", series or req.get("requirement_set_id"))
            return

        if handoff_producers or corrections:
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                                   if o.get("obligation_kind") == "ae_assessment"), None)
                if obligation is not None:
                    push("protocol_clause", obligation.get("obligation_definition_id"))
            return
        if review_gate and reviews:
            return

        # The first abnormal result of the measure anchors the trend links.
        source = anchor
        for r in input_data.get("observed_results", []):
            if (r.get("stable_measure_key") == unit.stable_measure_key
                    and r.get("reported_abnormal_flag") in ("H", "L")):
                source = r.get("result_id")
                break
        by_result_id = {r.get("result_id"): r for r in input_data.get("observed_results", [])}
        anchor_r = by_result_id.get(anchor)
        src_r = by_result_id.get(source)

        def push_lab(kind: str, target: str) -> None:
            jumps.append({
                "cardinality": "one", "source_object_id": source,
                "target_kind": kind, "target_object_id": target,
            })

        endpoint_ratio = None
        if anchor_r is not None:
            ratio = self._result_ratio(anchor_r)
            if ratio is not None:
                applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                endpoint_ratio = self._grade_endpoint_ratio(app_rules, ratio)
        if unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
            cs_rule = next((r for r in matched_rules if r.get("rule_kind") == "clinical_significance"), None)
            if cs_rule is not None:
                push_lab("lab_manual_rule", cs_rule.get("rule_id"))
        elif unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
            action_rule = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
            if action_rule is not None:
                push_lab("lab_manual_rule", action_rule.get("rule_id"))
        elif unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
            obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                               if o.get("obligation_kind") == "ae_assessment"), None)
            if obligation is not None:
                push("protocol_clause", obligation.get("obligation_definition_id"))
        elif unit.primary_subtype == PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING:
            # A reported-vs-recomputed mismatch: the grade rule at the
            # endpoint or the applied set — and no follow-up clause.
            applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            if applied is not None and unit.grade_state == GradeState.GRADED:
                if endpoint_ratio is not None:
                    matched = self._match_grade_rule(
                        app_rules, endpoint_ratio, applied,
                        _dec(src_r.get("numeric_value")) if src_r is not None else None)
                    if matched is not None:
                        push("lab_manual_rule", matched.get("grade_rule_id"))
                else:
                    push("lab_manual_rule", applied.get("rule_set_id"))
            return
        elif unit.grade_comparison_state is not None:
            # A reported-grade comparison ran: the applied set is the lab
            # target; the comparison run carries no protocol clause.
            applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            if applied is not None and unit.grade_state == GradeState.GRADED:
                push("lab_manual_rule", applied.get("rule_set_id"))
            return
        elif followup is not None and followup.l1_disposition == L1Disposition.NEGATIVE:
            if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
                return
            if carry_refs:
                return
            repeat_candidate = self._repeat_candidate(unit.stable_measure_key, src_r)
            if (repeat_candidate is not None
                    and repeat_candidate.get("reported_abnormal_flag") not in ("H", "L")):
                # A met repeat that recovered to normal links the repeat rule.
                rep_rule = next((r for r in matched_rules if r.get("rule_kind") == "repeat"), None)
                if rep_rule is not None:
                    push("protocol_clause", rep_rule.get("rule_id"))
            elif repeat_candidate is not None:
                # A still-abnormal repeat: the trend rule when the series
                # resolved or persisted (stable/recovered/persistent/
                # recurrent) or the value kept rising.
                if unit.trend_kind in (TrendKind.STABLE_ABNORMAL, TrendKind.RECOVERED,
                                       TrendKind.PERSISTENT, TrendKind.RECURRENT):
                    trend_rule = (input_data.get("trend_rules") or [None])[0]
                    if trend_rule is not None:
                        push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                else:
                    last_val = _dec(repeat_candidate.get("numeric_value"))
                    trig_val = _dec(src_r.get("numeric_value")) if src_r is not None else None
                    if (last_val is not None and trig_val is not None
                            and last_val >= trig_val):
                        trend_rule = (input_data.get("trend_rules") or [None])[0]
                        if trend_rule is not None:
                            push_lab("lab_manual_rule", trend_rule.get("rule_id"))
        elif followup is not None:
            matches = [r for r in input_data.get("observed_results", [])
                       if self._matched_monitoring_rules(unit.stable_measure_key, r)]
            worsening = unit.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING
            missing_repeat = followup.repeat_state == RepeatState.REQUIRED_MISSING
            repeat_candidate = self._repeat_candidate(unit.stable_measure_key, src_r)
            first_visit_match = next(
                (m for m in matches if m.get("visit_ref") is not None),
                matches[0] if matches else None,
            )
            fu_triggers = [rid for rid in followup.source_result_ids
                           if by_result_id.get(rid) is not None]
            new_episode = bool(fu_triggers and first_visit_match
                               and fu_triggers[-1] != first_visit_match.get("result_id"))
            trend_rule = (input_data.get("trend_rules") or [None])[0]
            if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS and missing_repeat:
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if (unit.trend_kind == TrendKind.INSUFFICIENT_POINTS
                    and followup.repeat_state == RepeatState.WRONG_MEASURE_OR_METHOD
                    and repeat_candidate is not None
                    and repeat_candidate.get("reported_abnormal_flag") in ("H", "L")):
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if new_episode:
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if unit.primary_subtype == PositiveSubtype.NEW_ABNORMALITY \
                    and followup.action_state is not None \
                    and followup.repeat_state is None \
                    and len(matches) == 1:
                # An action-missing run with a single anchor links the
                # applied grade set and carries no follow-up clause.
                applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                if applied is not None and unit.grade_state == GradeState.GRADED:
                    push("lab_manual_rule", applied.get("rule_set_id"))
                return
            visited_baseline = False
            for r in input_data.get("observed_results", []):
                if r.get("stable_measure_key") != unit.stable_measure_key:
                    continue
                if r.get("reported_abnormal_flag") in ("H", "L"):
                    break
                if r.get("visit_ref") is not None:
                    visited_baseline = True
                    break
            baseline_time_producer = any(
                p.get("consumption_purpose") == "baseline_time_authority"
                for p in input_data.get("producer_consumption_bindings", [])
            )
            if (worsening or (len(matches) == 1 and missing_repeat)) and not visited_baseline:
                applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                if applied is not None and unit.grade_state == GradeState.GRADED:
                    if endpoint_ratio is not None:
                        matched = self._match_grade_rule(
                            app_rules, endpoint_ratio, applied,
                            _dec(src_r.get("numeric_value")) if src_r is not None else None)
                        if matched is not None:
                            push("lab_manual_rule", matched.get("grade_rule_id"))
                    else:
                        push("lab_manual_rule", applied.get("rule_set_id"))
            self._baseline_time_producer = baseline_time_producer
            self._visited_baseline = visited_baseline
        else:
            # No follow-up: the applied grade set when graded off the
            # endpoint, otherwise the conversion or reference range.
            applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            ranges = self._applicable_ranges(unit.stable_measure_key)
            range_unit = ranges[0].get("unit") if ranges else None
            converted = None
            if src_r is not None and range_unit:
                for rule in input_data.get("unit_conversion_rules", []):
                    if (rule.get("from_unit") == src_r.get("original_unit")
                            and rule.get("to_unit") == range_unit):
                        converted = rule
                        break
            if converted is not None:
                push("lab_manual_rule", converted.get("conversion_rule_id"))
            elif (applied is not None and unit.grade_state == GradeState.GRADED
                    and endpoint_ratio is None):
                push("lab_manual_rule", applied.get("rule_set_id"))
            else:
                candidate = self._range_lab_candidate(unit.stable_measure_key, unit)
                if candidate is not None:
                    push("lab_manual_rule", candidate)

        # Triggering monitoring rule as protocol clause (the action rule when
        # the follow-up obligation is a treatment/protocol action, otherwise
        # the repeat rule). Comparison runs, grade-mismatch runs, and
        # carried-forward runs carry no protocol clause.
        if (matched_rules and unit.grade_comparison_state is None
                and not carry_refs
                and unit.primary_subtype in (
                    PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP,
                    PositiveSubtype.NEW_ABNORMALITY,
                    PositiveSubtype.PERSISTENT_OR_RECURRENT,
                    PositiveSubtype.BASELINE_ABNORMAL_WORSENING)
                and endpoint_ratio is None):
            fu = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                 and u.stable_measure_key == unit.stable_measure_key),
                None,
            )
            if fu is not None and fu.l1_disposition == L1Disposition.POSITIVE:
                if (getattr(self, "_baseline_time_producer", False)
                        or not getattr(self, "_visited_baseline", False)):
                    if fu.action_state is not None:
                        trigger = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
                    else:
                        trigger = next((r for r in matched_rules if r.get("rule_kind") == "repeat"), None)
                    if trigger is not None:
                        push("protocol_clause", trigger.get("rule_id"))
