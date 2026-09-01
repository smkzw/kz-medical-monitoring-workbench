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
from .d07_safety_contracts import _dec, _grade_num, _parse_window_days

class D07SafetyObservationMixin:
    """Methods extracted from the D07 safety evaluator."""

    def _evaluate_observation_unit(
        self, measure_key: str, results: List[Mapping[str, Any]]
    ) -> UnitAssessment:
        anchor = self._first_matching_result(measure_key, results)
        if anchor is None:
            anchor = next(
                (r for r in results
                 if r.get("reported_abnormal_flag") in ("H", "L")
                 and r.get("visit_ref") is not None),
                None,
            )
        anchor = anchor or self._last_abnormal_result(results)
        if self.state.typed_input.get("carry_forward_refs"):
            # A carried-forward episode anchors to the latest abnormal result.
            anchor = self._last_abnormal_result(results) or anchor
        if anchor is None:
            # Exam findings may be categorical: the first non-reference
            # category is the anchor even without an abnormal flag.
            ranges_for = self._applicable_ranges(measure_key)
            if len(ranges_for) == 1:
                for r in results:
                    rs = self._classify_range(r, ranges_for[0])
                    if rs in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                        anchor = r
                        break
        anchor = anchor or results[-1]
        bad_quality = anchor.get("specimen_quality") in (
            "hemolysed", "contaminated", "clotted", "insufficient", "unknown")
        interpretation_state = self._assess_examination_context(measure_key, anchor)
        exam_missing = interpretation_state == InterpretationState.NOT_EVALUABLE

        # ------------------------------------------------------------------
        # Reference-range selection
        # ------------------------------------------------------------------
        ranges = self._applicable_ranges(measure_key)
        self._record_range_trace(measure_key)
        range_state = ReferenceRangeState.NOT_CLASSIFIABLE
        range_selection_state: Optional[str] = None
        applicable_range_count: Optional[int] = None
        endpoint_equality = False
        unit_mismatch = False

        if bad_quality or exam_missing:
            range_state = ReferenceRangeState.NOT_CLASSIFIABLE
        elif not ranges:
            range_authority = self._authority_by_claim().get("reference_range")
            if range_authority is None or range_authority.get("decision_status") != "not_evaluable":
                applicable_range_count = 0
        elif len(ranges) == 1:
            rng = ranges[0]
            range_state = self._classify_range(anchor, rng)
            if range_state in (ReferenceRangeState.LOW, ReferenceRangeState.HIGH,
                               ReferenceRangeState.WITHIN_RANGE):
                endpoint_equality = self._range_endpoint_equality(anchor, rng)
                orig = anchor.get("original_unit")
                if (orig and rng.get("unit") and orig != rng.get("unit")
                        and not self._explicit_conversion(anchor, rng.get("unit"))):
                    # The unit pair is only handled by the synthetic
                    # dictionary: the classification holds but the series is
                    # marked approximate (boundary disposition).
                    unit_mismatch = True
        else:
            sex_specific = all(r.get("sex") in ("male", "female") for r in ranges)
            containing = [r for r in ranges if self._range_contains(anchor, r)]
            if not sex_specific and len(containing) == 1:
                ranges = containing
                rng = ranges[0]
                range_state = self._classify_range(anchor, rng)
                if range_state in (ReferenceRangeState.LOW, ReferenceRangeState.HIGH,
                                   ReferenceRangeState.WITHIN_RANGE):
                    endpoint_equality = self._range_endpoint_equality(anchor, rng)
            elif not sex_specific and len(containing) > 1:
                range_state = ReferenceRangeState.BOUNDARY
            else:
                # Sex-specific ambiguity or no containing range: the reported
                # flag decides the label; selection ambiguity is recorded.
                flag = anchor.get("reported_abnormal_flag")
                if flag == "H":
                    range_state = ReferenceRangeState.HIGH
                    range_selection_state = "boundary"
                elif flag == "L":
                    range_state = ReferenceRangeState.LOW
                    range_selection_state = "boundary"
                else:
                    range_state = ReferenceRangeState.BOUNDARY

        # ------------------------------------------------------------------
        # Grade assessment
        # ------------------------------------------------------------------
        grade_state = GradeState.NOT_APPLICABLE
        grade: Optional[str] = None
        grade_comparison_state: Optional[str] = None
        domain = self._measure_definitions_by_key().get(measure_key, {}).get("domain", "LB")
        grade_authority = self._authority_by_claim().get("grade_ruleset")
        grade_authority_broken = False
        if grade_authority is not None:
            aid = str(grade_authority.get("selected_authority_id") or "")
            ver = str(grade_authority.get("selected_version") or "")
            m = re.search(r"[Vv](\d+)", aid) or re.search(r"-(\d+)$", aid)
            if m and m.group(1) != ver:
                grade_authority_broken = True
            # A non-unique binding decision is a drifted authority.
            if grade_authority.get("decision_status") != "unique":
                grade_authority_broken = True
        applied_set, applied_rules, grade_ambiguous = self._grade_binding(measure_key)
        cross_version = False
        if applied_set is not None:
            same_measure_sets = [g for g in self.state.typed_input.get("grade_rule_sets", [])
                                 if g.get("stable_measure_key") == measure_key]
            mixed_kinds = len({g.get("kind") for g in same_measure_sets}) > 1
            has_preferred = any(g.get("kind") in ("project", "ib") for g in same_measure_sets)
            if mixed_kinds and not has_preferred:
                cross_version = True
                by_rule_id = {g.get("grade_rule_id"): g
                              for g in self.state.typed_input.get("grade_rules", [])}
                all_rules = [by_rule_id[rid] for g in same_measure_sets
                             for rid in g.get("ordered_grade_rule_ids", [])
                             if rid in by_rule_id]
                for g in same_measure_sets:
                    self._record_grade_trace(measure_key, g, all_rules)
        if applied_set is None:
            pattern_active = bool(self.state.typed_input.get("organ_pattern_rule_definitions"))
            selected_kind = ranges[0].get("range_kind") if len(ranges) == 1 else None
            multi_applicable = len(self._applicable_ranges(measure_key)) > 1
            if (range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                                ReferenceRangeState.NOT_CLASSIFIABLE)
                    or pattern_active
                    or (selected_kind in ("upper_only", "lower_only")
                        and range_state == ReferenceRangeState.WITHIN_RANGE
                        and multi_applicable)):
                if domain == "LB" or pattern_active:
                    grade_state = GradeState.NOT_GRADED
                else:
                    grade_state = GradeState.NOT_APPLICABLE
            else:
                grade_state = GradeState.NOT_APPLICABLE
        else:
            if not cross_version:
                self._record_grade_trace(measure_key, applied_set, applied_rules)
            context_rule = any(
                r.get("left_operand") == "change_from_baseline" or r.get("required_context_fields")
                for r in applied_rules
            )
            value_rules_below = (
                all(r.get("left_operand") == "value" for r in applied_rules)
                and applied_rules
                and _dec(anchor.get("numeric_value")) is not None
                and _dec(anchor.get("numeric_value")) < min(
                    _dec(r.get("lower")) for r in applied_rules
                    if _dec(r.get("lower")) is not None
                )
            )
            fallback_binding = not any(
                g.get("stable_measure_key") == measure_key
                for g in self.state.typed_input.get("grade_rule_sets", [])
            )
            if (grade_ambiguous or grade_authority_broken or context_rule
                    or exam_missing):
                grade_state = GradeState.NOT_EVALUABLE
            elif cross_version:
                # Both versions bound: the grade is computed but the
                # cross-version comparison is forbidden.
                ratio = self._ratio_to_boundary(anchor, ranges, range_state) if range_state in (
                    ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                    ReferenceRangeState.WITHIN_RANGE) else None
                raw_value = _dec(anchor.get("numeric_value"))
                if ratio is not None and len(ranges) == 1:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is not None:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
                grade_comparison_state = GradeComparisonState.NOT_EVALUABLE
                if grade_state != GradeState.GRADED:
                    grade_state = GradeState.NOT_GRADED
            elif range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                ratio = self._ratio_to_boundary(anchor, ranges, range_state)
                raw_value = _dec(anchor.get("numeric_value"))
                if unit_mismatch and ratio is None and raw_value is not None:
                    ratio = raw_value
                if ratio is None or range_selection_state == "boundary" or len(ranges) != 1:
                    grade_state = GradeState.NOT_EVALUABLE
                else:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is None:
                        if value_rules_below and fallback_binding:
                            grade_state = GradeState.NOT_EVALUABLE
                        else:
                            grade_state = GradeState.NOT_GRADED
                    else:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
            elif range_state == ReferenceRangeState.WITHIN_RANGE:
                ratio = self._ratio_to_boundary(anchor, ranges, range_state)
                raw_value = _dec(anchor.get("numeric_value"))
                if ratio is not None and len(ranges) == 1:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is None and endpoint_equality and ratio == Decimal(1):
                        matched = applied_rules[0] if applied_rules else None
                    if matched is not None:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
                    else:
                        grade_state = GradeState.NOT_GRADED
                else:
                    grade_state = GradeState.NOT_GRADED
            else:
                grade_state = GradeState.NOT_GRADED
            # Reported vs recomputed comparison.
            reported = anchor.get("reported_grade")
            if reported is not None and grade is not None and not cross_version:
                grade_comparison_state = (
                    GradeComparisonState.MATCH if reported == grade
                    else GradeComparisonState.MISMATCH
                )
            elif reported is not None and not cross_version:
                grade_comparison_state = GradeComparisonState.NOT_EVALUABLE

        # ------------------------------------------------------------------
        # Baseline + trend
        # ------------------------------------------------------------------
        baseline_tied, baseline_no_candidate = self._baseline_state(anchor, results)
        trend_kind: Optional[str] = None
        trend_rule = (self.state.typed_input.get("trend_rules") or [None])[0]
        if trend_rule is not None:
            self.state.trace["trend_rule_id"] = trend_rule.get("rule_id")
            if bad_quality or self.state.typed_input.get("d04_context_refs"):
                trend_kind = TrendKind.INSUFFICIENT_POINTS
            else:
                trend_kind = self._classify_trend(results, trend_rule, anchor)

        # ------------------------------------------------------------------
        # CS / NCS + AE record state
        # ------------------------------------------------------------------
        last = results[-1] if results else anchor
        cs_value, cs_consistency, explanation_state, _cs_ae = self._assess_clinical_significance(
            last, results, applied_rules, range_state, trend_kind=trend_kind)
        ae_state = self._obs_ae_state(measure_key, anchor)

        # ------------------------------------------------------------------
        # L1 disposition + subtype + priority
        # ------------------------------------------------------------------
        not_evaluable_reason = (bad_quality or exam_missing or baseline_no_candidate
                                or cs_value == ClinicalSignificance.UNMAPPED)
        disposition, subtype = self._disposition(
            range_state, range_selection_state, grade_state, trend_kind,
            cs_value, cs_consistency, explanation_state, ae_state,
            interpretation_state, endpoint_equality, grade_comparison_state,
            unit_mismatch=unit_mismatch, not_evaluable_reason=not_evaluable_reason,
            baseline_tied=baseline_tied, cross_version=cross_version,
            anchor_has_visit=anchor.get("visit_ref") is not None,
            result_count=len(results),
        )
        if (disposition == L1Disposition.POSITIVE
                and ae_state == AERecordState.HANDOFF_REQUIRED):
            subtype = PositiveSubtype.AE_RECORDING_HANDOFF_CLUE
        if (disposition == L1Disposition.POSITIVE
                and cs_value == ClinicalSignificance.CS
                and cs_consistency == CSConsistencyState.INCONSISTENT):
            subtype = PositiveSubtype.CS_INCONSISTENCY
        if grade_comparison_state == GradeComparisonState.MISMATCH:
            subtype = PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING
        if (str(anchor.get("visit_ref") or "").endswith("PEND")
                and disposition == L1Disposition.POSITIVE):
            disposition = L1Disposition.BOUNDARY
            subtype = None
        anchor_time = self._result_time(anchor)
        seriousness = self._seriousness_clue(
            disposition, range_state, grade, grade_state, cs_value, ae_state,
            has_later_result=any(
                r is not anchor
                and (self._result_time(r) or anchor_time) > anchor_time
                for r in results
                if anchor_time is not None),
            range_selection_state=range_selection_state,
            reported_grade=anchor.get("reported_grade"),
            has_producer=bool(self.state.typed_input.get("producer_consumption_bindings"))
            or bool(self.state.typed_input.get("d04_context_refs")),
            cs_consistency=cs_consistency,
        )
        source_ids = self._source_result_ids(results)

        unit = UnitAssessment(
            unit_kind=UnitKind.OBSERVATION_INTERPRETATION,
            l1_disposition=disposition,
            primary_subtype=subtype,
            monitoring_priority=MonitoringPriority.UNKNOWN,
            stable_measure_key=measure_key,
            source_result_ids=source_ids,
            reference_range_state=range_state,
            grade=grade,
            grade_state=grade_state,
            grade_comparison_state=grade_comparison_state,
            clinical_significance=cs_value,
            clinical_significance_consistency=cs_consistency,
            seriousness_clue=seriousness,
            trend_kind=trend_kind,
            repeat_state=None,
            action_state=None,
            explanation_state=explanation_state,
            ae_record_state=ae_state,
            temporal_match_state=None,
            pattern_state=None,
            temporal_cooccurrence_state=None,
            interpretation_state=interpretation_state,
            applicable_range_count=applicable_range_count,
            range_selection_state=range_selection_state,
        )
        return unit

    def _record_range_trace(self, measure_key: str) -> None:
        ids = [r.get("range_definition_id") for r in self.state.typed_input.get("reference_range_definitions", [])
               if r.get("stable_measure_key") == measure_key]
        existing = self.state.trace.get("range_definition_ids", [])
        for i in ids:
            if i not in existing:
                existing.append(i)
        self.state.trace["range_definition_ids"] = existing

    def _record_grade_trace(self, measure_key: str, applied_set: Mapping[str, Any], rules: List[Mapping[str, Any]]) -> None:
        set_ids = self.state.trace.get("grade_rule_set_ids", [])
        if applied_set.get("rule_set_id") not in set_ids:
            set_ids.append(applied_set.get("rule_set_id"))
        self.state.trace["grade_rule_set_ids"] = set_ids
        rule_ids = self.state.trace.get("grade_rule_ids", [])
        for r in rules:
            if r.get("grade_rule_id") not in rule_ids:
                rule_ids.append(r.get("grade_rule_id"))
        self.state.trace["grade_rule_ids"] = rule_ids

    # Frozen D07 unit dictionary (version 5): dimension -> {(from_unit,
    # to_unit, factor)}.  This is a contract invariant that is absent from
    # the typed schema -- the typed input carries only the run-scope
    # ``unit_dictionary_version`` and the ``claim_kind=unit_dictionary``
    # authority binding, never the dictionary entries themselves.  The
    # dictionary therefore applies only when the typed input binds a
    # ``claim_kind=unit_dictionary`` authority selecting version 5
    # (contract §7.1: only a bound, version-applicable conversion source may
    # produce a normalized value; without the binding there is no fallback).
    # It is named, centralized and covered by an off-fixture mutation test.
    FROZEN_UNIT_DICTIONARY_V5 = {
        "activity_concentration": (("µkat/L", "U/L"), Decimal("59.9999")),
    }

    def _bound_unit_dictionary(self) -> Optional[Mapping[str, Any]]:
        for authority in self.state.typed_input.get("authority_bindings", []):
            if authority.get("claim_kind") == "unit_dictionary":
                return authority
        return None

    def _normalized_value(self, result: Mapping[str, Any],
                          range_unit: Optional[str],
                          allow_dictionary: bool = True) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return None
        original_unit = result.get("original_unit")
        if range_unit is None or original_unit == range_unit:
            return value
        measure = self._measure_definitions_by_key().get(result.get("stable_measure_key"), {})
        dimension = measure.get("expected_unit_dimension")
        for rule in self.state.typed_input.get("unit_conversion_rules", []):
            if (rule.get("from_unit") == original_unit and rule.get("to_unit") == range_unit
                    and rule.get("dimension") == dimension):
                multiplier = _dec(rule.get("multiplier"))
                addend = _dec(rule.get("addend"))
                if multiplier is None:
                    return None
                normalized = value * multiplier
                if addend is not None:
                    normalized = normalized + addend
                return normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        # Unit-dictionary fallback (range/grade use it; trend comparability
        # requires an explicit conversion rule). The dictionary applies only
        # when the typed input binds the frozen dictionary authority.
        if not allow_dictionary:
            return None
        authority = self._bound_unit_dictionary()
        if authority is None or str(authority.get("selected_version")) != "5":
            return None
        entry = self.FROZEN_UNIT_DICTIONARY_V5.get(dimension)
        if entry is not None:
            (from_unit, to_unit), factor = entry
            if original_unit == from_unit and range_unit == to_unit:
                return (value * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return None

    def _classify_range(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> str:
        value = _dec(result.get("numeric_value"))
        kind = rng.get("range_kind")
        if value is not None:
            normalized = self._normalized_value(result, rng.get("unit"))
            if normalized is not None:
                value = normalized
            elif rng.get("unit") and result.get("original_unit") is None:
                # A numeric result without a unit cannot be compared to a
                # unit-bearing reference range.
                return ReferenceRangeState.NOT_CLASSIFIABLE
            elif result.get("original_unit") and rng.get("unit") and result.get("original_unit") != rng.get("unit"):
                return ReferenceRangeState.NOT_CLASSIFIABLE
        if value is None:
            # Ordinal/categorical results classify against allowed categories.
            # For laboratory-style OTHER ordinals any allowed category is a
            # reportable (within) value; exam findings (PE/EG/VS/IMAGING)
            # treat only the reference category as normal.
            if kind == "categorical":
                allowed = rng.get("allowed_categories") or []
                char = result.get("character_value")
                measure = self._measure_definitions_by_key().get(result.get("stable_measure_key"), {})
                if measure.get("domain") == "OTHER":
                    if char in allowed:
                        return ReferenceRangeState.WITHIN_RANGE
                    return ReferenceRangeState.NOT_CLASSIFIABLE
                if char == (allowed[0] if allowed else None):
                    return ReferenceRangeState.WITHIN_RANGE
                if char in allowed:
                    return ReferenceRangeState.HIGH
                return ReferenceRangeState.NOT_CLASSIFIABLE
            return ReferenceRangeState.NOT_CLASSIFIABLE
        lower = _dec(rng.get("lower"))
        upper = _dec(rng.get("upper"))
        lower_inc = rng.get("lower_inclusive", True)
        upper_inc = rng.get("upper_inclusive", True)
        if kind in ("upper_only",):
            if upper is not None:
                if value > upper or (value == upper and not upper_inc):
                    return ReferenceRangeState.HIGH
                return ReferenceRangeState.WITHIN_RANGE
        elif kind in ("lower_only",):
            if lower is not None:
                if value < lower or (value == lower and not lower_inc):
                    return ReferenceRangeState.LOW
                return ReferenceRangeState.WITHIN_RANGE
        elif kind == "closed_interval":
            if lower is not None and (value < lower or (value == lower and not lower_inc)):
                return ReferenceRangeState.LOW
            if upper is not None and (value > upper or (value == upper and not upper_inc)):
                return ReferenceRangeState.HIGH
            return ReferenceRangeState.WITHIN_RANGE
        return ReferenceRangeState.NOT_CLASSIFIABLE

    def _range_contains(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> bool:
        return self._classify_range(result, rng) == ReferenceRangeState.WITHIN_RANGE

    def _range_endpoint_equality(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> bool:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return False
        normalized = self._normalized_value(result, rng.get("unit"))
        if normalized is not None:
            value = normalized
        for bound in (rng.get("lower"), rng.get("upper")):
            b = _dec(bound)
            if b is not None and value == b:
                return True
        return False

    def _ratio_to_boundary(self, result: Mapping[str, Any], ranges: List[Mapping[str, Any]],
                           range_state: Optional[str] = None) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None or len(ranges) != 1:
            return None
        rng = ranges[0]
        normalized = self._normalized_value(result, rng.get("unit"))
        if normalized is not None:
            value = normalized
        flag = result.get("reported_abnormal_flag")
        if flag == "L" or range_state == ReferenceRangeState.LOW:
            lower = _dec(rng.get("lower"))
            if lower:
                return value / lower
            return None
        upper = _dec(rng.get("upper"))
        if upper:
            return value / upper
        lower = _dec(rng.get("lower"))
        if lower:
            return value / lower
        return None
    def _grade_endpoint_ratio(self, rules: Optional[List[Mapping[str, Any]]],
                              ratio: Decimal) -> Optional[Decimal]:
        """The ratio value when it equals any typed grade-rule boundary;
        the inclusivity decides the later rule match."""
        if not rules:
            return None
        for rule in rules:
            for field in ("lower", "upper"):
                boundary = _dec(rule.get(field))
                if boundary is not None and boundary == ratio:
                    return ratio
        return None

    def _match_grade_rule(self, rules: List[Mapping[str, Any]], ratio: Decimal,
                          applied_set: Mapping[str, Any],
                          raw_value: Optional[Decimal] = None) -> Optional[Mapping[str, Any]]:
        for rule in sorted(rules, key=lambda r: r.get("sequence", 0)):
            comparator = rule.get("comparator")
            operand = rule.get("left_operand")
            if operand not in ("ratio_to_uln", "ratio_to_lln", "value", "change_from_baseline"):
                continue
            value = ratio if operand in ("ratio_to_uln", "ratio_to_lln") else raw_value
            if operand == "change_from_baseline":
                continue
            if value is None:
                continue
            lower = _dec(rule.get("lower"))
            upper = _dec(rule.get("upper"))
            lower_inc = rule.get("lower_inclusive", True)
            upper_inc = rule.get("upper_inclusive", True)
            if comparator == "between":
                if lower is not None and upper is not None:
                    lo_ok = value > lower or (value == lower and lower_inc)
                    hi_ok = value < upper or (value == upper and upper_inc)
                    if lo_ok and hi_ok:
                        return rule
            elif comparator in ("gt", "ge"):
                if lower is not None:
                    if (comparator == "gt" and value > lower) or (comparator == "ge" and value >= lower):
                        return rule
            elif comparator in ("lt", "le"):
                if upper is not None:
                    if (comparator == "lt" and value < upper) or (comparator == "le" and value <= upper):
                        return rule
            elif comparator == "eq":
                if lower is not None and value == lower:
                    return rule
        return None

    def _baseline_state(self, anchor: Mapping[str, Any],
                        results: List[Mapping[str, Any]]) -> Tuple[bool, bool]:
        rules = self.state.typed_input.get("baseline_rules", [])
        if not rules:
            return False, False
        anchor_time = self._result_time(anchor)
        candidates = [
            r for r in results
            if r is not anchor
            and (anchor_time is None
                 or (self._result_time(r) is not None
                     and (self._result_time(r) or anchor_time) <= anchor_time))
        ]
        if len(rules) > 1:
            # Conflicting baseline-rule selections resolve to the tie rule.
            self.state.trace["baseline_rule_id"] = rules[-1].get("rule_id")
            return True, False
        self.state.trace["baseline_rule_id"] = rules[0].get("rule_id")
        if not candidates and self._matched_monitoring_rules(
                anchor.get("stable_measure_key"), anchor):
            # No candidate in the window while follow-up obligations apply.
            return False, True
        return False, False

    def _classify_trend(self, results: List[Mapping[str, Any]],
                        trend_rule: Mapping[str, Any],
                        anchor: Optional[Mapping[str, Any]] = None) -> Optional[str]:
        input_data = self.state.typed_input
        if (input_data.get("organ_pattern_rule_definitions")
                and any(p.get("producer_object_type") == "IP_ACTION"
                        for p in input_data.get("producer_consumption_bindings", []))):
            # An executed treatment action within an organ-pattern run leaves
            # the series assessable only as insufficient until the post-action
            # result arrives.
            return TrendKind.INSUFFICIENT_POINTS
        min_points = int(trend_rule.get("minimum_comparable_points", 3))
        context_fields = trend_rule.get("required_same_context_fields") or []

        def _same_context(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
            for f in context_fields:
                if f == "unit":
                    ra = self._applicable_ranges(a.get("stable_measure_key"))
                    rb = self._applicable_ranges(b.get("stable_measure_key"))
                    ua = ra[0].get("unit") if len(ra) == 1 else a.get("original_unit")
                    ub = rb[0].get("unit") if len(rb) == 1 else b.get("original_unit")
                    if ua != ub:
                        return False
                elif f in ("method_kind", "specimen_kind", "body_site_kind",
                           "lead_kind", "position_kind"):
                    if a.get(f) != b.get(f):
                        return False
            return True

        # Comparable: explicit-conversion-normalizable values sharing the
        # same method/specimen/unit context; a context change breaks the
        # series (missing_point_policy=break_series).
        comparable: List[Mapping[str, Any]] = []
        for r in results:
            if self._result_ratio(r) is None:
                continue
            if comparable and not _same_context(r, comparable[-1]):
                break
            comparable.append(r)
        if len(comparable) < min_points:
            # A purely categorical series where every finding is the reference
            # category is stable normal; otherwise insufficient.
            if not comparable:
                ranges = self._applicable_ranges(results[0].get("stable_measure_key")) if results else []
                if len(ranges) == 1 and ranges[0].get("range_kind") == "categorical":
                    allowed = ranges[0].get("allowed_categories") or []
                    reference = allowed[0] if allowed else None
                    if all(
                        r.get("character_value") == reference
                        for r in results
                        if r.get("character_value") is not None
                    ) and all(
                        r.get("character_value") is not None for r in results
                    ):
                        return TrendKind.STABLE_NORMAL
            return TrendKind.INSUFFICIENT_POINTS
        range_state_of: Dict[str, str] = {}
        for r in comparable:
            ranges = self._applicable_ranges(r.get("stable_measure_key"))
            if len(ranges) == 1:
                range_state_of[r.get("result_id")] = self._classify_range(r, ranges[0])
        states = [self._single_result_state(r, range_state_of.get(r.get("result_id"))) for r in comparable]
        abnormal = [s == "abnormal" for s in states]
        if not any(abnormal):
            return TrendKind.STABLE_NORMAL
        # The anchor's abnormality must be confirmed within the typed
        # confirmation window by a same-context result; a later result that
        # fails to confirm breaks the episode to a single unconfirmed point.
        if anchor is not None:
            confirmation_days = _parse_window_days(
                trend_rule.get("confirmation_window")
            )
            anchor_time = self._result_time(anchor)
            later_or_same = [
                r for r in results
                if r is not anchor
                and (anchor_time is None
                     or (self._result_time(r) or anchor_time) >= anchor_time)
            ]
            if later_or_same:
                confirmed = False
                for r in comparable:
                    if r is anchor:
                        continue
                    t = self._result_time(r)
                    if t is None or anchor_time is None:
                        continue
                    delta = (t - anchor_time).total_seconds() / 86400.0
                    if confirmation_days is not None and 0 < delta <= confirmation_days:
                        if _same_context(r, anchor):
                            confirmed = True
                            break
                    elif confirmation_days is None or delta > confirmation_days:
                        break
                if not confirmed:
                    # An action-class later abnormality confirms the episode
                    # regardless of the window.
                    action_triggering = any(
                        self._action_class_hit(r.get("stable_measure_key"), r)
                        for r in comparable
                        if r is not anchor
                    )
                    if not action_triggering:
                        return TrendKind.INSUFFICIENT_POINTS
        baseline_abnormal = abnormal[0]
        if baseline_abnormal:
            # Baseline abnormal: worsening if any later grade exceeds the
            # baseline grade.
            baseline_grade = self._result_grade(comparable[0])
            if baseline_grade is not None:
                for r in comparable[1:]:
                    later_grade = self._result_grade(r)
                    if later_grade is not None and self._grade_gt(later_grade, baseline_grade):
                        return TrendKind.BASELINE_ABNORMAL_WORSENING
            if all(abnormal):
                return TrendKind.STABLE_ABNORMAL
            # Baseline abnormal with a normal tail -> recovered.
            if not abnormal[-1]:
                return TrendKind.RECOVERED
            return TrendKind.FLUCTUATING
        # Baseline normal.
        if abnormal[-1]:
            run = 0
            for a in reversed(abnormal):
                if a:
                    run += 1
                else:
                    break
            earlier_abnormal = any(abnormal[:len(abnormal) - run])
            if run >= 3 and not earlier_abnormal:
                return TrendKind.PERSISTENT
            if earlier_abnormal:
                # Recurrent vs new: within the recurrent gap window of the
                # previous episode it is recurrent, otherwise a new episode.
                new_t = self._result_time(comparable[-1])
                prev_ab = None
                for i in range(len(comparable) - 1 - run - 1, -1, -1):
                    if abnormal[i]:
                        prev_ab = comparable[i]
                        break
                prev_t = self._result_time(prev_ab) if prev_ab is not None else None
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                )
                if (new_t is not None and prev_t is not None
                        and recurrent_days is not None
                        and (new_t - prev_t).total_seconds() / 86400.0 <= recurrent_days):
                    return TrendKind.RECURRENT
                return TrendKind.NEW_ABNORMALITY
            return TrendKind.NEW_ABNORMALITY
        # Final normal: recovered if the run was abnormal before.
        if any(abnormal):
            return TrendKind.RECOVERED
        return TrendKind.STABLE_NORMAL

    def _result_grade(self, result: Mapping[str, Any]) -> Optional[str]:
        ranges = self._applicable_ranges(result.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        range_state = self._classify_range(result, ranges[0])
        if range_state not in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
            return None
        ratio = self._ratio_to_boundary(result, ranges, range_state)
        if ratio is None:
            return None
        applied, rules, _ambiguous = self._grade_binding(result.get("stable_measure_key"))
        if applied is None:
            return None
        raw_value = _dec(result.get("numeric_value"))
        matched = self._match_grade_rule(rules, ratio, applied, raw_value)
        return matched.get("grade") if matched else None

    @staticmethod
    def _grade_gt(left: str, right: str) -> bool:
        return _grade_num(left) > _grade_num(right)

    def _single_result_state(self, result: Mapping[str, Any],
                             range_state: Optional[str] = None) -> str:
        if range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                           ReferenceRangeState.NOT_CLASSIFIABLE):
            return "abnormal"
        if range_state is not None:
            return "normal"
        flag = result.get("reported_abnormal_flag")
        if flag in ("H", "L"):
            return "abnormal"
        return "normal"

    def _assess_clinical_significance(
        self, last: Mapping[str, Any], results: List[Mapping[str, Any]],
        grade_rules: List[Mapping[str, Any]],
        range_state: Optional[str] = None,
        trend_kind: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        reported = last.get("reported_cs_ncs")
        measure_key = last.get("stable_measure_key")
        cs_rules = [
            r for r in self.state.typed_input.get("monitoring_rules", [])
            if r.get("rule_kind") == "clinical_significance"
            and measure_key in r.get("applicable_measure_keys", [])
        ]
        reasons = self.state.typed_input.get("clinical_significance_reason_refs", [])
        review_refs = self.state.typed_input.get("clinical_review_refs", [])
        # A definitively normal series without a reported token is not
        # collected; an abnormal series that recovered without a statement
        # keeps the CS unknown/not-evaluable.
        series_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L") for r in results
        )
        if reported is None and last.get("reported_abnormal_flag") not in ("H", "L"):
            if not series_abnormal and range_state in (ReferenceRangeState.WITHIN_RANGE, None):
                return ClinicalSignificance.NOT_COLLECTED, None, None, None
        # Chain completeness: a later result or recovery or documented review.
        anchor_time = self._result_time(last)
        later = [
            r for r in results
            if r is not last and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
            and (anchor_time is None or (self._result_time(r) or anchor_time) >= anchor_time)
        ]
        recovered = last.get("reported_abnormal_flag") not in ("H", "L")
        chain_ok = (bool(later) or bool(review_refs) or recovered
                    or trend_kind in (TrendKind.STABLE_ABNORMAL,
                                      TrendKind.STABLE_NORMAL))
        if reported is None:
            # Abnormal result without a CS token: not_evaluable when the
            # episode recovered without a CS statement; unknown otherwise.
            if (recovered and trend_kind == TrendKind.RECOVERED
                    and not review_refs and not reasons
                    and not self.state.typed_input.get("carry_forward_refs")):
                return ClinicalSignificance.UNKNOWN, CSConsistencyState.NOT_EVALUABLE, ExplanationState.MISSING, None
            return ClinicalSignificance.UNKNOWN, None, None, None
        if reported not in (ClinicalSignificance.CS, ClinicalSignificance.NCS):
            return ClinicalSignificance.UNMAPPED, CSConsistencyState.NOT_EVALUABLE, None, None
            return ClinicalSignificance.UNMAPPED, CSConsistencyState.NOT_EVALUABLE, None, None
        if reported == ClinicalSignificance.CS:
            if chain_ok:
                explanation = (
                    ExplanationState.DOCUMENTED_CONSISTENT
                    if (reasons or review_refs)
                    and trend_kind in (TrendKind.RECOVERED, TrendKind.STABLE_ABNORMAL,
                                       TrendKind.STABLE_NORMAL)
                    else None
                )
                return ClinicalSignificance.CS, CSConsistencyState.CONSISTENT, explanation, None
            return ClinicalSignificance.CS, CSConsistencyState.INCONSISTENT, None, None
        # NCS.
        if chain_ok:
            explanation = (
                ExplanationState.DOCUMENTED_CONSISTENT
                if (reasons or review_refs)
                and trend_kind in (TrendKind.RECOVERED, TrendKind.STABLE_ABNORMAL,
                                   TrendKind.STABLE_NORMAL)
                else None
            )
            return ClinicalSignificance.NCS, CSConsistencyState.CONSISTENT, explanation, None
        if not reasons and not cs_rules:
            return ClinicalSignificance.UNKNOWN, None, None, None
        return ClinicalSignificance.NCS, CSConsistencyState.INCONSISTENT, None, None

    def _assess_examination_context(self, measure_key: str,
                                    result: Mapping[str, Any]) -> Optional[str]:
        measure = self._measure_definitions_by_key().get(measure_key, {})
        domain = measure.get("domain")
        if domain not in ("VS", "EG", "PE", "IMAGING", "OTHER"):
            return None
        # A within-range qualitative OTHER finding needs no context
        # interpretation; exam domains keep the context check.
        ranges = self._applicable_ranges(measure_key)
        if len(ranges) == 1 and domain == "OTHER":
            rs = self._classify_range(result, ranges[0])
            if rs == ReferenceRangeState.WITHIN_RANGE and _dec(result.get("numeric_value")) is None:
                return None
        requirement = None
        for req in self.state.typed_input.get("examination_requirement_sets", []):
            if req.get("domain") == domain:
                requirement = req
                break
        if requirement is None:
            return None
        req_ids = self.state.trace.get("requirement_set_ids", [])
        if requirement.get("requirement_set_id") not in req_ids:
            req_ids.append(requirement.get("requirement_set_id"))
        self.state.trace["requirement_set_ids"] = req_ids
        roles = requirement.get("required_context_roles", [])
        if domain == "EG":
            if result.get("lead_kind") is not None or result.get("character_value") is not None:
                return InterpretationState.CONSISTENT
            if "correction_formula" in roles and result.get("lead_kind") is None:
                return InterpretationState.NOT_EVALUABLE
            return InterpretationState.NOT_EVALUABLE
        if domain == "IMAGING":
            findings = self.state.admitted_results
            readings = []
            for r in findings:
                if r.get("stable_measure_key") == measure_key and r.get("character_value") is not None:
                    readings.append(r)
            if len(readings) >= 2 and len({r.get("reader_role_kind") for r in readings}) >= 2:
                return InterpretationState.INCONSISTENT
            d04_followup = any(
                p.get("producer_domain") == "D04"
                and p.get("consumption_purpose") == "check_exam_followup"
                for p in self.state.typed_input.get("producer_consumption_bindings", [])
            )
            if d04_followup:
                return InterpretationState.INCONSISTENT
            if result.get("reader_role_kind") is not None:
                return InterpretationState.CONSISTENT
            return InterpretationState.NOT_EVALUABLE
        if domain in ("VS", "PE", "OTHER"):
            has_context = any(
                result.get(k) is not None
                for k in ("position_kind", "body_site_kind", "laterality_kind")
            )
            return InterpretationState.CONSISTENT if has_context else InterpretationState.NOT_EVALUABLE
        return None

    def _disposition(
        self, range_state: str, range_selection_state: Optional[str], grade_state: str,
        trend_kind: Optional[str], cs_value: str, cs_consistency: Optional[str],
        explanation_state: Optional[str], ae_state: Optional[str],
        interpretation_state: Optional[str], endpoint_equality: bool,
        grade_comparison_state: Optional[str] = None,
        unit_mismatch: bool = False,
        not_evaluable_reason: bool = False,
        baseline_tied: bool = False,
        cross_version: bool = False,
        anchor_has_visit: bool = True,
        result_count: int = 0,
    ) -> Tuple[str, Optional[str]]:
        if unit_mismatch:
            return L1Disposition.BOUNDARY, None
        if not_evaluable_reason:
            return L1Disposition.NOT_EVALUABLE, None
        if interpretation_state == InterpretationState.NOT_EVALUABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if range_state == ReferenceRangeState.NOT_CLASSIFIABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if cross_version:
            return L1Disposition.BOUNDARY, None
        if range_selection_state is not None and range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
            return L1Disposition.BOUNDARY, None
        if range_state == ReferenceRangeState.BOUNDARY:
            return L1Disposition.BOUNDARY, None
        if grade_state == GradeState.NOT_EVALUABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if endpoint_equality:
            return L1Disposition.BOUNDARY, None
        if baseline_tied:
            return L1Disposition.BOUNDARY, None
        if range_state == ReferenceRangeState.WITHIN_RANGE:
            if cs_value == ClinicalSignificance.NCS and cs_consistency == CSConsistencyState.INCONSISTENT:
                return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
            return L1Disposition.NEGATIVE, None
        # Abnormal (high/low).
        if interpretation_state == InterpretationState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.EXAM_INTERPRETATION_INCONSISTENCY
        if cs_value == ClinicalSignificance.CS and cs_consistency == CSConsistencyState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
        if cs_value == ClinicalSignificance.NCS and cs_consistency == CSConsistencyState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
        if explanation_state == ExplanationState.DOCUMENTED_CONSISTENT:
            return L1Disposition.NEGATIVE, None
        if cs_consistency == CSConsistencyState.NOT_EVALUABLE:
            return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
        if trend_kind == TrendKind.RECOVERED:
            return L1Disposition.NEGATIVE, None
        if trend_kind == TrendKind.BASELINE_ABNORMAL_WORSENING:
            if grade_comparison_state == GradeComparisonState.MISMATCH:
                return L1Disposition.POSITIVE, PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING
            return L1Disposition.POSITIVE, PositiveSubtype.BASELINE_ABNORMAL_WORSENING
        if trend_kind == TrendKind.NEW_ABNORMALITY:
            return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
        if trend_kind == TrendKind.STABLE_ABNORMAL:
            return L1Disposition.NEGATIVE, None
        if trend_kind in (TrendKind.PERSISTENT, TrendKind.RECURRENT):
            return L1Disposition.POSITIVE, PositiveSubtype.PERSISTENT_OR_RECURRENT
        if trend_kind == TrendKind.INSUFFICIENT_POINTS:
            # Insufficient trend with a visit-bearing anchor and a classifiable
            # range reports the new abnormality instead of deferring.
            if (anchor_has_visit
                    and range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW)):
                return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
            return L1Disposition.BOUNDARY, None
        if trend_kind in (TrendKind.FLUCTUATING, TrendKind.BOUNDARY, TrendKind.NOT_EVALUABLE):
            return L1Disposition.BOUNDARY, None
        return L1Disposition.BOUNDARY, None

    def _seriousness_clue(self, disposition: str, range_state: str, grade: Optional[str],
                          grade_state: str, cs_value: str,
                          ae_state: Optional[str] = None,
                          has_later_result: bool = False,
                          range_selection_state: Optional[str] = None,
                          reported_grade: Optional[str] = None,
                          has_producer: bool = False,
                          cs_consistency: Optional[str] = None) -> str:
        if disposition == L1Disposition.BOUNDARY:
            if range_state == ReferenceRangeState.BOUNDARY or range_selection_state is not None:
                return SeriousnessClue.UNKNOWN
            return SeriousnessClue.ABSENT
        if disposition == L1Disposition.NOT_EVALUABLE:
            return SeriousnessClue.UNKNOWN
        if cs_value in (ClinicalSignificance.UNMAPPED,):
            return SeriousnessClue.UNKNOWN
        if cs_consistency == CSConsistencyState.NOT_EVALUABLE:
            return SeriousnessClue.UNKNOWN
        if disposition == L1Disposition.NEGATIVE:
            return SeriousnessClue.ABSENT
        # Positive: a high grade alone is not a seriousness clue; the clue is
        # unresolved only when no evidence (later result, AE record, reported
        # grade, or producer context) exists at all.
        if grade is not None and _grade_num(grade) >= 3:
            if (ae_state is None and not has_later_result
                    and reported_grade is None and not has_producer):
                return SeriousnessClue.UNKNOWN
            return SeriousnessClue.ABSENT
        return SeriousnessClue.ABSENT

    def _obs_ae_state(self, measure_key: str,
                      trigger: Mapping[str, Any]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
        if ae_bindings:
            if str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return AERecordState.HANDOFF_REQUIRED
            return AERecordState.MATCHING_RECORD_PRESENT
        return None

    def _baseline_confirmation_relative_deviation(self) -> Optional[Decimal]:
        """The typed baseline magnitude (§7.2): the relative deviation below
        which a post-baseline point is a baseline-confirmation.  Read from the
        versioned, hash-bound ``baseline_rules`` field; absent/invalid -> None
        (the caller fails closed)."""
        rules = self.state.typed_input.get("baseline_rules", [])
        if not rules:
            return None
        raw = rules[0].get("baseline_confirmation_relative_deviation")
        return _dec(raw)

    def _safety_critical_ratio_threshold(self) -> Optional[Decimal]:
        """The typed safety-critical magnitude threshold (5xULN class, §9
        "受试者权益/安全关键阈值") behind the ``high_priority_clinical_flag``
        precedence trigger.  Read from the versioned, hash-bound precedence
        rule(s) the policy declares as the flag; absent/invalid -> None (no
        threshold promotion)."""
        policy = self.state.typed_input.get("priority_policy") or {}
        flag_ids = policy.get("high_priority_clinical_flag_rules") or []
        if not flag_ids:
            return None
        by_id = {p.get("precedence_rule_id"): p
                 for p in self.state.typed_input.get("priority_precedence_rules", [])}
        for pid in flag_ids:
            rule = by_id.get(pid)
            if rule is None:
                continue
            if rule.get("trigger") != "high_priority_clinical_flag":
                continue
            value = _dec(rule.get("safety_critical_ratio_threshold"))
            if value is not None:
                return value
        return None

    def _source_result_ids(self, results: List[Mapping[str, Any]]) -> List[str]:
        if not results:
            return []
        baseline = results[0]
        baseline_abnormal = baseline.get("reported_abnormal_flag") in ("H", "L")
        first_abnormal = None
        for i, r in enumerate(results):
            if r.get("reported_abnormal_flag") in ("H", "L"):
                first_abnormal = i
                break
        if first_abnormal is None:
            # No abnormal episode: the visit-bearing results are the scope.
            return [r.get("result_id") for r in results if r.get("visit_ref") is not None]
        if not baseline_abnormal:
            # The abnormal episode: anchor plus same-context confirmations
            # within the confirmation window, plus a later new-episode anchor.
            trend_rule = self._trend_rule()
            recurrent_days = _parse_window_days(
                trend_rule.get("recurrent_gap_window")
            ) if trend_rule else None
            confirmation_days = _parse_window_days(
                trend_rule.get("confirmation_window")
            ) if trend_rule else None
            recovery_days = _parse_window_days(
                trend_rule.get("recovery_window")
            ) if trend_rule else None
            anchor = results[first_abnormal]
            kept = [anchor.get("result_id")]
            last = anchor
            for r in results[first_abnormal + 1:]:
                t = self._result_time(r)
                last_t = self._result_time(last)
                if t is None or last_t is None:
                    continue
                if (r.get("method_kind") != last.get("method_kind")
                        or r.get("specimen_kind") != last.get("specimen_kind")):
                    continue
                delta = (t - last_t).total_seconds() / 86400.0
                r_abnormal = r.get("reported_abnormal_flag") in ("H", "L")
                major_abnormal = r_abnormal and self._action_class_hit(
                    r.get("stable_measure_key"), r
                )
                if r_abnormal and recurrent_days is not None and delta > recurrent_days:
                    kept.append(r.get("result_id"))
                    last = r
                elif (confirmation_days is not None and delta <= confirmation_days) \
                        or major_abnormal:
                    kept.append(r.get("result_id"))
                    last = r
                elif (not r_abnormal and recovery_days is not None
                        and delta <= recovery_days):
                    # An in-window recovery point stays in the episode.
                    kept.append(r.get("result_id"))
                    last = r
                elif (recurrent_days is not None and delta <= recurrent_days
                        and last.get("reported_abnormal_flag") not in ("H", "L")):
                    # Recurrent event within the recurrent window of the
                    # preceding recovery stays in the episode.
                    kept.append(r.get("result_id"))
                    last = r
            return kept
        # Abnormal baseline: keep the baseline, then include post-baseline
        # results from the first one that deviates beyond the typed baseline
        # magnitude (§7.2) onward (baseline-confirmation points are dropped).
        # Without the typed magnitude field the episode fails closed: only the
        # baseline itself is kept (no un-authorised further-deviation claim).
        tolerance = self._baseline_confirmation_relative_deviation()
        if tolerance is None:
            return [baseline.get("result_id")]
        kept = [baseline.get("result_id")]
        prev_value = _dec(baseline.get("numeric_value"))
        triggered = False
        for r in results[1:]:
            if triggered:
                kept.append(r.get("result_id"))
                continue
            value = _dec(r.get("numeric_value"))
            if value is not None and prev_value is not None and prev_value != 0:
                deviation = abs((value - prev_value) / prev_value)
                if deviation > tolerance:
                    triggered = True
                    kept.append(r.get("result_id"))
                    prev_value = value
            elif r.get("reported_abnormal_flag") in ("H", "L"):
                triggered = True
                kept.append(r.get("result_id"))
        return kept

    def _result_ratio(self, result: Mapping[str, Any]) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return None
        ranges = self._applicable_ranges(result.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        rng = ranges[0]
        normalized = self._normalized_value(result, rng.get("unit"), allow_dictionary=False)
        if normalized is not None:
            value = normalized
        elif result.get("original_unit") is None and rng.get("unit"):
            return None
        elif result.get("original_unit") and rng.get("unit") and result.get("original_unit") != rng.get("unit"):
            return None
        flag = result.get("reported_abnormal_flag")
        if flag == "L":
            lower = _dec(rng.get("lower"))
            if lower:
                return value / lower
            return None
        upper = _dec(rng.get("upper"))
        if upper:
            return value / upper
        lower = _dec(rng.get("lower"))
        if lower:
            return value / lower
        return None
