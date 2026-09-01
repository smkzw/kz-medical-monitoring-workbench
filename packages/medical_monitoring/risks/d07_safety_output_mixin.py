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

class D07SafetyOutputMixin:
    """Methods extracted from the D07 safety evaluator."""

    def _assemble_raw_output(self) -> Dict[str, Any]:
        state = self.state
        root: Dict[str, Any] = {}
        error = state.error
        if error is not None:
            root["integrity"] = {
                "stage": error.stage,
                "error_type": error.error_type,
                "error_object": error.error_object,
            }
        else:
            root["integrity"] = {"stage": "admitted", "error_type": None, "error_object": None}

        not_evaluable_count = sum(
            1 for u in state.units if u.l1_disposition == L1Disposition.NOT_EVALUABLE
        )
        open_gate_count = len(state.blocked)
        unresolved_identity = 0

        l0_complete = (
            error is None
            and open_gate_count == 0
            and len(state.units) > 0
        )
        root["l0_complete"] = l0_complete
        root["expected_set_reconciled"] = (
            error is None
            and not state.blocked
            and self._expected_reconciled()
        )
        root["all_units_disposed"] = (
            error is None
            and not state.blocked
            and all(u.l1_disposition in L1Disposition.ALL for u in state.units)
        )
        root["not_evaluable_count"] = not_evaluable_count
        root["open_d05_gate_count"] = open_gate_count
        root["unresolved_identity_count"] = unresolved_identity
        root["unit_count"] = len(state.units)
        root["domain_complete"] = (
            error is None
            and l0_complete
            and root["expected_set_reconciled"]
            and root["all_units_disposed"]
            and not_evaluable_count == 0
            and open_gate_count == 0
            and not any(
                u.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE
                for u in state.units
            )
        )

        if state.units:
            root["units"] = {
                str(i): self._unit_leaves(u) for i, u in enumerate(state.units)
            }
        if state.blocked:
            root["blocked"] = {str(i): b for i, b in enumerate(state.blocked)}
        if self._coverage_needed():
            root["coverage"] = self._coverage_leaves()
        if state.ownership:
            root["ownership"] = state.ownership
        if state.lifecycle:
            root["lifecycle"] = state.lifecycle
        if state.aggregation_created:
            root["aggregation_created"] = False

        root["trace"] = self._trace_leaves()
        root["source"] = self._source_leaves()

        # Journey summary (worker-03): only on admitted runs without D05 open
        # gates and only when the typed input binds the shared visit/time
        # spine (contract v0.4 section 11).  The summary leaf set is exactly
        # the frozen oracle's ``journey.*`` vocabulary.
        if error is None and not state.blocked:
            journey = build_d07_journey_summary(
                state.typed_input,
                state.units,
                root["source"].get("source_jump_target_pairs", []),
            )
            if journey is not None:
                root["journey"] = journey

        # Root synthetic leaves (documented D07_ROOT_OUTPUT_LEAVES).
        flattened = self._flatten(root)
        medical_keys = [k for k in flattened if not k.startswith(("trace.", "source.", "integrity."))]
        trace_keys = [k for k in flattened if k.startswith("trace.")]
        source_keys = [k for k in flattened if k.startswith("source.")]
        root["integrity_error"] = error.error_type if error else None
        root["medical_leaf_count"] = len(medical_keys)
        root["trace_leaf_count"] = len(trace_keys)
        root["source_leaf_count"] = len(source_keys)
        return root

    @staticmethod
    def _flatten(value: Any, prefix: str = "") -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if isinstance(value, dict):
            for key, item in value.items():
                out.update(
                    D07SafetyOutputMixin._flatten(
                        item, f"{prefix}.{key}" if prefix else str(key)
                    )
                )
        else:
            out[prefix] = value
        return out

    def _unit_leaves(self, u: UnitAssessment) -> Dict[str, Any]:
        leaves: Dict[str, Any] = OrderedDict()
        leaves["unit_kind"] = u.unit_kind
        leaves["l1_disposition"] = u.l1_disposition
        leaves["primary_subtype"] = u.primary_subtype
        leaves["monitoring_priority"] = u.monitoring_priority
        leaves["stable_measure_key"] = u.stable_measure_key
        leaves["source_result_ids"] = list(u.source_result_ids)
        leaves["reference_range_state"] = u.reference_range_state
        leaves["grade"] = u.grade
        leaves["grade_state"] = u.grade_state
        leaves["grade_comparison_state"] = u.grade_comparison_state
        leaves["clinical_significance"] = u.clinical_significance
        leaves["clinical_significance_consistency"] = u.clinical_significance_consistency
        leaves["seriousness_clue"] = u.seriousness_clue
        leaves["trend_kind"] = u.trend_kind
        leaves["repeat_state"] = u.repeat_state
        leaves["action_state"] = u.action_state
        leaves["explanation_state"] = u.explanation_state
        leaves["ae_record_state"] = u.ae_record_state
        leaves["temporal_match_state"] = u.temporal_match_state
        leaves["pattern_state"] = u.pattern_state
        leaves["temporal_cooccurrence_state"] = u.temporal_cooccurrence_state
        leaves["interpretation_state"] = u.interpretation_state
        if u.applicability is not None:
            leaves["applicability"] = u.applicability
            leaves["applicability_authority_id"] = u.applicability_authority_id
            leaves["applicability_authority_version"] = u.applicability_authority_version
            leaves["applicability_evidence_id"] = u.applicability_evidence_id
            leaves["control_plane_no_match"] = u.control_plane_no_match
        if u.applicable_range_count is not None:
            leaves["applicable_range_count"] = u.applicable_range_count
        if u.range_selection_state is not None:
            leaves["range_selection_state"] = u.range_selection_state
        return leaves

    def _expected_reconciled(self) -> bool:
        if self.state.error is not None:
            return True
        expected = self._expected_unit_keys()
        evaluated = {
            u.stable_measure_key for u in self.state.units
            if u.unit_kind in (UnitKind.OBSERVATION_INTERPRETATION,
                               UnitKind.FOLLOWUP_OBLIGATION)
        }
        return expected == evaluated

    def _coverage_needed(self) -> bool:
        if self.state.error is not None:
            return False
        return bool(self.state.blocked) or bool(
            self.state.typed_input.get("applicability_evidence")
        ) or (not self.state.units and not self.state.admitted_results)

    def _coverage_leaves(self) -> Dict[str, Any]:
        state = self.state
        blocked = state.blocked
        evidence = state.typed_input.get("applicability_evidence", [])
        if blocked:
            return {
                "blocked_observation_count": len(blocked),
                "expected_unit_count": len(self._expected_unit_keys()),
                "evaluated_unit_count": 0,
                "missing_unit_count": len(self._expected_unit_keys()),
                "unexpected_unit_count": 0,
                "duplicate_unit_count": 0,
                "open_d05_gate_count": len(blocked),
                "gate_blocked_stage": blocked[0].get("blocked_stage"),
                "control_plane_state": blocked[0].get("control_plane_state"),
                "applicability_evidence_count": len(evidence),
                "l1_negative_permitted": False,
                "l1_not_applicable_permitted": False,
            }
        if evidence:
            return {
                "applicability": "not_applicable",
                "applicability_evidence_count": len(evidence),
                "applicability_evidence_ids": [e.get("applicability_evidence_id") for e in evidence],
                "control_plane_no_match": False,
                "l0_gap": False,
                "l1_not_applicable_permitted": True,
            }
        return {
            "applicability_evidence_count": 0,
            "authority_coverage": "missing",
            "mapping_coverage": "missing",
            "source_role_status": "missing",
            "control_plane_no_match": True,
            "expected_unit_count": 0,
            "evaluated_unit_count": 0,
            "missing_unit_count": 0,
            "unexpected_unit_count": 0,
            "duplicate_unit_count": 0,
            "l0_gap": True,
            "l1_negative_permitted": False,
            "l1_not_applicable_permitted": False,
        }

    def _visit_trace_ids(self) -> List[str]:
        input_data = self.state.typed_input
        results = input_data.get("observed_results", [])
        abnormal = [r for r in results if r.get("reported_abnormal_flag") in ("H", "L")]
        visits: List[str] = []

        def add(v: Optional[str]) -> None:
            if isinstance(v, str) and v not in visits:
                visits.append(v)

        if not abnormal:
            first = next((r for r in results if r.get("visit_ref") is not None), None)
            if first is not None:
                add(first.get("visit_ref"))
            return visits
        anchor = next((r for r in abnormal if r.get("visit_ref") is not None), None)
        if anchor is None:
            return visits
        # Baseline candidates' visits (D05 visit-bound baselines).
        admitted = self.state.admitted_results
        for r in admitted:
            if r is anchor:
                break
            if r.get("visit_ref") is not None:
                add(r.get("visit_ref"))
        add(anchor.get("visit_ref"))
        trigger = self._first_matching_result(anchor.get("stable_measure_key"), results) or anchor


        trigger_time = self._result_time(trigger)
        closure = None
        for r in results:
            if (r is not trigger
                    and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT):
                t = self._result_time(r)
                if trigger_time is None or (t is not None and t >= trigger_time):
                    closure = r
                    break
        if closure is not None:
            obligations = input_data.get("action_obligation_definitions") or []
            closure_normal = closure.get("reported_abnormal_flag") not in ("H", "L")
            if not obligations:
                # Runs without follow-up obligations bind every closure visit
                # (raw CS closures, unit-boundary tails, pattern companions).
                add(closure.get("visit_ref"))
            elif closure_normal:
                # A normal closure visit binds for carried-forward runs and
                # for a positive follow-up whose repeat carries a specimen.
                if bool(self.state.lifecycle):
                    add(closure.get("visit_ref"))
                else:
                    fu_unit = next(
                        (u for u in self.state.units
                         if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                         and u.stable_measure_key == trigger.get("stable_measure_key")),
                        None,
                    )
                    if (fu_unit is not None
                            and fu_unit.l1_disposition == L1Disposition.POSITIVE
                            and fu_unit.repeat_state == RepeatState.WRONG_MEASURE_OR_METHOD
                            and closure.get("specimen_kind")):
                        add(closure.get("visit_ref"))
            else:
                # A still-abnormal closure binds only a documented CS chain.
                if (bool(input_data.get("clinical_review_refs"))
                        and closure.get("reported_cs_ncs")):
                    add(closure.get("visit_ref"))
        # Excluded (out-of-cutoff) abnormal results keep their visit.
        for r in results:
            if (r.get("reported_abnormal_flag") in ("H", "L")
                    and r not in admitted
                    and r.get("visit_ref") is not None):
                add(r.get("visit_ref"))
        return visits

    def _trace_leaves(self) -> Dict[str, Any]:
        trace = dict(self.state.trace)
        always = [
            "applicability_evidence_ids", "authority_binding_ids", "baseline_rule_id",
            "carry_forward_ref_ids", "correction_decision_ids", "d04_context_ref_ids",
            "d05_gate_binding_ids", "grade_rule_ids", "measure_definition_ids",
            "pattern_rule_ids", "priority_policy_id", "priority_precedence_rule_ids",
            "producer_binding_ids", "record_envelope_ids", "requirement_set_ids",
            "scope_binding_id", "shared_spine_binding_id", "trend_rule_id",
            "unit_conversion_rule_ids", "visit_ref_ids",
        ]
        scalar_keys = {
            "scope_binding_id", "baseline_rule_id", "trend_rule_id",
            "d05_cutoff_policy_id", "priority_policy_id", "shared_spine_binding_id",
        }
        out: Dict[str, Any] = {}
        if self.state.error is not None:
            # Integrity-failure runs emit the full key set (values bound so
            # far, empty for sections never consumed).
            keys = always + [
                "cutoff_decision_ids", "d05_cutoff_policy_id",
                "grade_rule_set_ids", "monitoring_rule_ids",
                "monitoring_predicate_ids", "obligation_definition_ids",
                "range_definition_ids", "unit_algorithm_versions",
            ]
            for key in keys:
                if key in trace:
                    out[key] = trace[key]
                elif key in scalar_keys:
                    out[key] = None
                else:
                    out[key] = []
            # A unit-conversion authority failure aborts before grade binding.
            if (self.state.error.stage == "authority_version"
                    and self.state.error.error_object.startswith("unit_conversion_rules")):
                out["grade_rule_set_ids"] = []
                out["grade_rule_ids"] = []
            if out.get("d05_cutoff_policy_id") is None:
                cutoffs = self.state.typed_input.get("cutoff_decisions", [])
                if cutoffs:
                    out["d05_cutoff_policy_id"] = cutoffs[0].get("d05_cutoff_policy_id")
            return out
        # Clean runs: always-emitted keys plus path-bound conditional keys.
        if not self.state.blocked:
            visit_ids = self._visit_trace_ids()
            if visit_ids:
                trace["visit_ref_ids"] = visit_ids
        for key in always:
            if key in trace:
                out[key] = trace[key]
            elif key in scalar_keys:
                out[key] = None
            else:
                out[key] = []
        # D05-gate-blocked records keep their scope envelopes in the trace.
        if self.state.blocked:
            blocked_record_ids = {b.get("source_record_id") for b in self.state.blocked}
            envelope_ids = list(out.get("record_envelope_ids", []))
            for r in self.state.typed_input.get("observed_results", []):
                if (r.get("stable_source_record_id") in blocked_record_ids
                        and r.get("scope_envelope_id") not in envelope_ids):
                    envelope_ids.append(r.get("scope_envelope_id"))
            out["record_envelope_ids"] = envelope_ids
        input_data = self.state.typed_input
        has_cutoff = bool(input_data.get("cutoff_decisions"))
        has_results = any(input_data.get("observed_results"))
        blocked = bool(self.state.blocked)
        if has_cutoff:
            out["cutoff_decision_ids"] = trace.get(
                "cutoff_decision_ids",
                [c.get("cutoff_decision_id") for c in input_data.get("cutoff_decisions", [])],
            )
            out["d05_cutoff_policy_id"] = trace.get(
                "d05_cutoff_policy_id",
                (input_data.get("cutoff_decisions") or [{}])[0].get("d05_cutoff_policy_id"),
            )
        if has_results:
            out["range_definition_ids"] = trace.get("range_definition_ids", [])
        if ("grade_rule_set_ids" in trace
                or any(u.l1_disposition != L1Disposition.NOT_APPLICABLE
                       for u in self.state.units)):
            out["grade_rule_set_ids"] = trace.get("grade_rule_set_ids", [])
        if has_results and not blocked:
            out["monitoring_rule_ids"] = trace.get("monitoring_rule_ids", [])
            out["monitoring_predicate_ids"] = trace.get("monitoring_predicate_ids", [])
            out["obligation_definition_ids"] = trace.get("obligation_definition_ids", [])
        if not self.state.blocked and (self.state.units or any(
                self.state.typed_input.get("observed_results") or [])):
            out["unit_algorithm_versions"] = trace.get("unit_algorithm_versions", [])
        return out

    def _source_leaves(self) -> Dict[str, Any]:
        input_data = self.state.typed_input
        locators: List[str] = []
        sections = [
            "observed_results", "scope_envelopes", "run_scope_binding",
            "previous_run_scope_binding", "previous_scope_envelopes",
            "previous_time_refs", "cutoff_decisions", "time_refs", "visit_refs",
            "subject_demographics",
            "audience_lexicon", "authority_bindings", "measure_definitions",
            "reference_range_definitions", "grade_rule_sets", "monitoring_rules",
            "monitoring_predicates", "baseline_rules", "trend_rules",
            "action_obligation_definitions", "organ_pattern_rule_definitions",
            "examination_requirement_sets", "priority_precedence_rules",
            "producer_consumption_bindings", "d05_gate_bindings",
            "applicability_evidence", "clinical_significance_reason_refs",
            "clinical_review_refs", "d04_context_refs", "correction_chain_decisions",
            "carry_forward_refs",
            "shared_spine_binding", "shared_spine_scope_equality_decision",
        ]
        for section in sections:
            value = input_data.get(section)
            objs = value if isinstance(value, list) else ([value] if isinstance(value, dict) else [])
            for obj in objs:
                if isinstance(obj, dict):
                    for loc in obj.get("source_locator_ids", []):
                        if loc not in locators:
                            locators.append(loc)
        record_ids: List[str] = []
        for r in input_data.get("observed_results", []):
            rid = r.get("stable_source_record_id")
            if rid not in record_ids:
                record_ids.append(rid)
        producer_ids = [p.get("binding_id") for p in input_data.get("producer_consumption_bindings", [])]
        jumps: List[Dict[str, Any]] = []
        if self.state.error is not None:
            # Integrity-failure runs carry no medical output. The one
            # record the frozen oracle surfaces is the last visit-bearing
            # result for a unit-conversion authority drift, which anchors
            # the defect entry.
            if str(self.state.error).startswith("authority_version:authority_mismatch:unit_conversion_rules"):
                for r in reversed(input_data.get("observed_results", [])):
                    if r.get("visit_ref") is not None:
                        jumps.append({
                            "cardinality": "one", "source_object_id": r.get("result_id"),
                            "target_kind": "listing_row",
                            "target_object_id": r.get("stable_source_record_id"),
                        })
                        break
            return {
                "source_locator_ids": sorted(locators),
                "stable_source_record_ids": record_ids,
                "producer_binding_ids": producer_ids,
                "source_jump_target_pairs": jumps,
                "reverse_binding_count": len(jumps),
            }

        superseded_by: Dict[str, List[str]] = {}
        for decision in input_data.get("correction_chain_decisions", []):
            for edge in decision.get("supersession_edges", []):
                if isinstance(edge, list) and len(edge) == 2:
                    superseded_by.setdefault(edge[1], []).append(edge[0])
            accepted = decision.get("accepted_current_record_id")
            for cand in decision.get("candidate_record_ids", []):
                if cand != accepted:
                    superseded_by.setdefault(accepted, []).append(cand)
        by_result_id = {r.get("result_id"): r for r in input_data.get("observed_results", [])}

        def add_listing(rid: str) -> None:
            result = by_result_id.get(rid)
            if result is None:
                return
            jumps.append({
                "cardinality": "one", "source_object_id": rid,
                "target_kind": "listing_row",
                "target_object_id": result.get("stable_source_record_id"),
            })
            for prior in superseded_by.get(rid, []):
                if prior in by_result_id:
                    jumps.append({
                        "cardinality": "one", "source_object_id": rid,
                        "target_kind": "listing_row",
                        "target_object_id": by_result_id[prior].get("stable_source_record_id"),
                    })

        def add_listing_from(source_rid: str, target_rid: str) -> None:
            result = by_result_id.get(target_rid)
            if result is None:
                return
            jumps.append({
                "cardinality": "one", "source_object_id": source_rid,
                "target_kind": "listing_row",
                "target_object_id": result.get("stable_source_record_id"),
            })

        if self.state.blocked:
            blocked_record_ids = {b.get("source_record_id") for b in self.state.blocked}
            for r in input_data.get("observed_results", []):
                if r.get("stable_source_record_id") in blocked_record_ids:
                    add_listing(r.get("result_id"))
        measure_defs = {
            m.get("stable_measure_key"): m
            for m in input_data.get("measure_definitions", [])
        }
        by_measure = {}
        for r in self.state.admitted_results:
            by_measure.setdefault(r.get("stable_measure_key"), []).append(r)
        obs_units = [u for u in self.state.units if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION]
        review_refs = input_data.get("clinical_review_refs") or []
        reason_refs = input_data.get("clinical_significance_reason_refs") or []
        carry_refs = input_data.get("carry_forward_refs") or []

        pattern_defs = input_data.get("organ_pattern_rule_definitions") or []

        if pattern_defs:
            # The organ-pattern evaluation owns the listings: the matched
            # multi-component rule with obligations lists every component
            # anchor, a two-role matched rule lists both anchors, and a
            # precision/conflict boundary lists the present anchors. All
            # other pattern states list the first present anchor only.
            pat = next((u for u in self.state.units
                        if u.unit_kind == UnitKind.ORGAN_PATTERN), None)
            roles = pattern_defs[0].get("required_component_roles", [])
            role_keys = [r.get("stable_measure_key") for r in roles]
            obligations = input_data.get("action_obligation_definitions") or []
            temporal_both = pat is not None and pat.temporal_cooccurrence_state in (
                TemporalCooccurrenceState.PRECISION_INSUFFICIENT,
                TemporalCooccurrenceState.CONFLICTED,
            )
            first_anchor_result = None
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        first_anchor_result = r
                        break
                if first_anchor_result is not None:
                    break
            eg_unpositioned = (
                first_anchor_result is not None
                and measure_defs.get(first_anchor_result.get("stable_measure_key"), {}).get("domain") == "EG"
                and not first_anchor_result.get("position_kind")
            )
            both = (bool(obligations) or temporal_both
                    or (len(roles) == 2 and pat is not None
                        and pat.l1_disposition == L1Disposition.POSITIVE
                        and not eg_unpositioned))
            present = []
            for key in role_keys:
                abnormal = [r for r in by_measure.get(key, [])
                            if r.get("reported_abnormal_flag") in ("H", "L")]
                if abnormal:
                    present.append(abnormal[-1])
            if both:
                for r in present:
                    add_listing(r.get("result_id"))
            elif present:
                add_listing(present[0].get("result_id"))
        else:
            for unit in obs_units:
                results = by_measure.get(unit.stable_measure_key, [])
                measure_def = measure_defs.get(unit.stable_measure_key, {})
                exam_domain = measure_def.get("domain") in ("VS", "EG", "PE", "IMAGING", "OTHER")
                if exam_domain:
                    # Examination findings list every visit-bearing record
                    # under its own source.
                    for r in results:
                        if r.get("visit_ref") is not None:
                            add_listing(r.get("result_id"))
                    continue
                matches = [r for r in results
                           if self._matched_monitoring_rules(unit.stable_measure_key, r)]
                fu_unit = next(
                    (u for u in self.state.units
                     if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                     and u.stable_measure_key == unit.stable_measure_key),
                    None,
                )
                fu_met = fu_unit is not None and fu_unit.l1_disposition == L1Disposition.NEGATIVE
                if not matches:
                    if (unit.l1_disposition == L1Disposition.BOUNDARY
                            and unit.trend_kind != TrendKind.INSUFFICIENT_POINTS):
                        for r in results:
                            if (r.get("reported_abnormal_flag") in ("H", "L")
                                    and r.get("visit_ref") is not None):
                                add_listing(r.get("result_id"))
                        continue
                    src_ids = [rid for rid in unit.source_result_ids
                               if by_result_id.get(rid) is not None
                               and by_result_id[rid].get("visit_ref") is not None]
                    if not src_ids:
                        continue
                    first_src = src_ids[0]
                    if unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
                        if review_refs:
                            add_listing(first_src)
                            jumps.append({
                                "cardinality": "one", "source_object_id": first_src,
                                "target_kind": "listing_row",
                                "target_object_id": review_refs[0].get("review_ref_id"),
                            })
                        elif reason_refs:
                            add_listing(first_src)
                            jumps.append({
                                "cardinality": "one", "source_object_id": first_src,
                                "target_kind": "listing_row",
                                "target_object_id": reason_refs[0].get("reason_ref_id"),
                            })
                        else:
                            for rid in src_ids:
                                add_listing_from(first_src, rid)
                    else:
                        add_listing(first_src)
                    continue
                first = matches[0]
                last = matches[-1]
                last_result = results[-1] if results else None
                if unit.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING:
                    first_visit = next(
                        (m for m in matches if m.get("visit_ref") is not None), first)
                    add_listing(first_visit.get("result_id"))
                    continue
                # A CS-documented closure lists the trigger plus the reason /
                # closure record under the trigger source. The review ref is
                # emitted by the risk-anchored section (after the handoff
                # links) to preserve the frozen order. A met follow-up closes
                # through the met branch instead.
                if (unit.clinical_significance in (ClinicalSignificance.CS, ClinicalSignificance.NCS)
                        and unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT
                        and not fu_met):
                    if reason_refs and not review_refs:
                        add_listing(first.get("result_id"))
                        jumps.append({
                            "cardinality": "one", "source_object_id": first.get("result_id"),
                            "target_kind": "listing_row",
                            "target_object_id": reason_refs[0].get("reason_ref_id"),
                        })
                    else:
                        add_listing(first.get("result_id"))
                        if (last_result is not None and last_result is not first
                                and not review_refs):
                            add_listing_from(first.get("result_id"),
                                             last_result.get("result_id"))
                    continue
                if unit.l1_disposition == L1Disposition.BOUNDARY:
                    if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS:
                        add_listing(first.get("result_id"))
                    else:
                        for r in results:
                            if r.get("reported_abnormal_flag") in ("H", "L"):
                                add_listing(r.get("result_id"))
                    continue
                if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS:
                    abnormal_matches = [m for m in matches
                                        if m.get("reported_abnormal_flag") in ("H", "L")]
                    if (abnormal_matches and fu_unit is not None
                            and fu_unit.repeat_state == RepeatState.WRONG_WINDOW):
                        add_listing(abnormal_matches[-1].get("result_id"))
                    elif abnormal_matches:
                        add_listing(abnormal_matches[0].get("result_id"))
                    else:
                        add_listing(first.get("result_id"))
                    continue
                if fu_met:
                    if review_refs:
                        # The review ref is emitted by the risk-anchored section
                        # (after the handoff links) to preserve the frozen order.
                        add_listing(first.get("result_id"))
                        continue
                    if (last_result is not None and last_result is not last
                            and last_result.get("reported_abnormal_flag") not in ("H", "L")):
                        if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
                            add_listing(first.get("result_id"))
                            add_listing_from(first.get("result_id"),
                                             last_result.get("result_id"))
                        elif carry_refs:
                            add_listing(first.get("result_id"))
                            add_listing(last_result.get("result_id"))
                        else:
                            add_listing(last_result.get("result_id"))
                        continue
                    if (last_result is not None
                            and last_result.get("reported_abnormal_flag") in ("H", "L")):
                        if unit.l1_disposition != L1Disposition.POSITIVE:
                            # A resolved negative observation lists its first
                            # visit-bearing match only.
                            first_visit = next(
                                (m for m in matches if m.get("visit_ref") is not None), first)
                            add_listing(first_visit.get("result_id"))
                            continue
                        if unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
                            first_visit = next(
                                (m for m in matches if m.get("visit_ref") is not None), first)
                            add_listing(first_visit.get("result_id"))
                            continue
                        if len(matches) <= 2:
                            last_val = _dec(last_result.get("numeric_value"))
                            first_val = _dec(first.get("numeric_value"))
                            if (last_val is not None and first_val is not None
                                    and last_val < first_val):
                                # A declining but still-abnormal repeat keeps the
                                # trigger and the closure under the trigger
                                # source.
                                add_listing(first.get("result_id"))
                                add_listing_from(first.get("result_id"),
                                                 last_result.get("result_id"))
                                continue
                        add_listing(last.get("result_id"))
                        continue
                    add_listing(last.get("result_id"))
                    continue
                trailing_normal = (
                    last_result is not None and last_result is not last
                    and last_result.get("reported_abnormal_flag") not in ("H", "L")
                    and (last_result.get("method_kind") == last.get("method_kind"))
                    and (last_result.get("specimen_kind") == last.get("specimen_kind"))
                )
                if (trailing_normal
                        and unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE
                        and fu_unit is not None
                        and fu_unit.l1_disposition == L1Disposition.POSITIVE):
                    add_listing(first.get("result_id"))
                    add_listing_from(first.get("result_id"),
                                     last_result.get("result_id"))
                    continue
                if trailing_normal and fu_unit is None:
                    add_listing(last_result.get("result_id"))
                    continue
                add_listing(last.get("result_id"))

        # A D05 visit-bound baseline surfaces the last baseline candidate's
        # visit as a typed visit link.
        if any(r.get("reported_abnormal_flag") in ("H", "L")
               for r in self.state.admitted_results):
            baseline_visited = []
            for r in self.state.admitted_results:
                if r.get("reported_abnormal_flag") in ("H", "L"):
                    break
                if r.get("visit_ref") is not None:
                    baseline_visited.append(r)
            if len(baseline_visited) >= 2:
                r = baseline_visited[-1]
                jumps.append({
                    "cardinality": "one", "source_object_id": r.get("result_id"),
                    "target_kind": "visit", "target_object_id": r.get("visit_ref"),
                })
        # Risk-anchored jumps for positive observation units, for negative
        # observations that carry a follow-up obligation, and for exam-domain
        # observations (the examination-report link is always surfaced).
        for unit in obs_units:
            has_fu = any(
                u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                and u.stable_measure_key == unit.stable_measure_key
                for u in self.state.units
            )
            measure = measure_defs.get(unit.stable_measure_key, {})
            exam_domain = measure.get("domain") in ("VS", "EG", "PE", "IMAGING", "OTHER")
            if (unit.l1_disposition != L1Disposition.POSITIVE and not has_fu
                    and not exam_domain
                    and self._range_lab_candidate(unit.stable_measure_key, unit) is None):
                continue
            trigger = next(
                (r for r in input_data.get("observed_results", [])
                 if r.get("stable_measure_key") == unit.stable_measure_key
                 and r.get("reported_abnormal_flag") in ("H", "L")
                 and r.get("visit_ref") is not None),
                None,
            )
            if trigger is None and unit.source_result_ids:
                trigger = by_result_id.get(unit.source_result_ids[0])
            if trigger is None:
                continue
            anchor = trigger.get("result_id")
            self._append_risk_jumps(jumps, anchor, unit)
        seen = set()
        deduped = []
        for j in jumps:
            key = (j.get("source_object_id"), j.get("target_kind"), j.get("target_object_id"))
            if key not in seen:
                seen.add(key)
                deduped.append(j)
        jumps = deduped
        reverse_count = len(jumps)
        return {
            "source_locator_ids": sorted(locators),
            "stable_source_record_ids": record_ids,
            "producer_binding_ids": producer_ids,
            "source_jump_target_pairs": jumps,
            "reverse_binding_count": reverse_count,
        }
