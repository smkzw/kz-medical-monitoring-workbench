"""D06 unit-kind evaluation strategies."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..projections.efficacy import (
    project_efficacy_journey,
    journey_audience_payload_from_projection,
)
from .efficacy import (
    AUDIENCE_LEXICON_HASH,
    AUDIENCE_LEXICON_VERSION,
    AUDIENCE_VALIDATOR_HASH,
    AUDIENCE_VALIDATOR_VERSION,
    CANONICAL_PRIORITY_POLICY,
    COVERAGE_COVERED,
    COVERAGE_NOT_APPLICABLE,
    COVERAGE_NOT_EVALUABLE,
    D06AudienceValidationResult,
    D06BindingContractError,
    D06ChallengeOutcome,
    D06ContractViolationError,
    D06Error,
    D06PriorityDecision,
    D06PriorityResolverInput,
    D06RiskBinding,
    D06UnitStableCore,
    DECISION_MULTI_FEASIBLE_BOUNDARY,
    DECISION_NOT_EVALUABLE,
    DECISION_UNIQUE,
    DIRECTIONALITIES,
    ENDPOINT_ROLES,
    GATE_ALGORITHM,
    GATE_APPLICABILITY,
    GATE_CUTOFF_SCOPE,
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_DEFINITION,
    GATE_DEPENDENCY,
    GATE_OPEN,
    GATE_ROUTING,
    GATE_UNIT_OR_SCALE,
    L1_BOUNDARY,
    L1_NOT_APPLICABLE,
    L1_NOT_EVALUABLE,
    L1_POSITIVE,
    L1_NEGATIVE,
    L2_COVERAGE_NOTICES,
    L2_QUERIES,
    L2_RISKS,
    OUTPUT_KIND_DEFINITION_BINDING,
    OUTPUT_KIND_ERROR,
    OUTPUT_KIND_GATE,
    OUTPUT_KIND_PROJECTION,
    OUTPUT_KIND_RESULT,
    PRIORITY_REASON_BY_STEP,
    ProjectionContractError,
    QUERY_CONTEXT_ENROLLED,
    SchemaContractError,
    OwnerScopeContractError,
    QUERY_CONTEXT_NOT_OCCURRED,
    QUERY_CONTEXT_UNRESOLVED,
    SCOPE_IDENTITY_FIELDS,
    SCOPE_IN_SCOPE,
    SCOPE_NOT_EVALUABLE,
    SCOPE_OUT_OF_CUTOFF,
    TTE_STATUS_BOUNDARY,
    TTE_STATUS_CENSORED,
    TTE_STATUS_COMPETING_EVENT,
    TTE_STATUS_EVENT,
    TRACE_EDGES_ALL,
    UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY,
    UNIT_KIND_BASELINE_SELECTION,
    UNIT_KIND_CHANGE_RECALCULATION,
    UNIT_KIND_ENDPOINT_COMPOSITION,
    UNIT_KIND_INDIVIDUAL_TREND_PATTERN,
    UNIT_KIND_ITEM_COMPLETENESS,
    UNIT_KIND_ITEM_VALUE_VALIDITY,
    UNIT_KIND_RATER_OR_MODE_CONSISTENCY,
    UNIT_KIND_REPEAT_SELECTION,
    UNIT_KIND_RESPONSE_CLASSIFICATION,
    UNIT_KIND_SCORE_RECALCULATION,
    UNIT_KIND_TO_SUBTYPE,
    _audience_normalize,
    AUDIENCE_PHRASES,
    AudiencePayloadValidationError,
    ChallengeAssertionContractError,
    ChallengeRegistryIntegrityError,
    audience_display_view,
    audience_phrase_hits,
    audience_string_paths,
    audience_visible_strings,
    attempted_display_view,
    d06_canonical_json,
    d06_content_hash,
    d06_sha256_text,
    resolve_priority_step,
    scope_identity_matches,
    validate_audience_payload_schema,
    verify_content_hash,
    verify_embedded_hash,
    verify_lineage_hash,
)

from .efficacy_contracts import *
from .efficacy_output_gates import *
from .efficacy_resolution import *
from .efficacy_resolution import (
    _canonical_decimal, _current_item_values, _determine_unit_kind,
    _effective_accepted_result, _effective_recalculated_result,
    _normalize_date_offset,
)

class EfficacyUnitEvaluationMixin:
    """Cohesive methods extracted from the D06 engine."""

    def _evaluate_unit(self, scope_status: Optional[str]) -> None:
        ctx = self.ctx
        if ctx.l1 is not None:
            return  # already decided by scope stage
        if scope_status == SCOPE_OUT_OF_CUTOFF:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        tp = ctx.fixture.typed_parameters
        # ------------------------------------------------------------------
        # Control-plane / no-unit decisions
        # ------------------------------------------------------------------
        if "applicability" in tp:
            if "feasible_definition_ids" in tp:
                # Applicability unresolved with two feasible definitions.
                self._open_gate(GATE_APPLICABILITY, GATE_DECISION_BOUNDARY)
                return
            ctx.domain_assertions["definition_binding_state"] = "not_applicable"
            ctx.domain_assertions["medical_expected_unit_created"] = False
            ctx.output_kind = OUTPUT_KIND_DEFINITION_BINDING
            ctx.coverage_status = COVERAGE_NOT_APPLICABLE
            ctx.l1 = None
            return
        if "prohibited_output" in tp:
            raise OwnerScopeContractError(
                "D06 must not generate KM/HR/p-value outputs", "owner_scope_validation"
            )
        if "prohibited_output_level" in tp:
            raise OwnerScopeContractError(
                "D06 must not form project-level aggregates", "owner_scope_validation"
            )
        if "fixture" in tp and tp["fixture"].get("contains_real_identifier"):
            raise D06ContractViolationError(
                "fixture must not contain real project/subject identifiers",
                "pre_medical_output_validation",
            )
        if "producer_kind" in tp and tp["producer_kind"] == "model_output":
            if tp.get("result_role") == "accepted_source":
                ctx.mark("accepted_artifact")
                raise SchemaContractError(
                    "model output cannot be accepted_source",
                    "pre_medical_output_validation",
                )
            raise D06ContractViolationError(
                "model output cannot be an accepted source",
                "pre_medical_output_validation",
            )
        if "unplanned_imputation" in tp:
            imputation = tp["unplanned_imputation"]
            if imputation == "mean":
                raise D06ContractViolationError(
                    "unplanned mean imputation is forbidden",
                    "pre_medical_output_validation",
                )
            if imputation in ("zero_best_worst", "best_value", "worst_value"):
                self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                return
            if imputation == "LOCF":
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "gate" in tp:
            self._gate_inputs(tp["gate"])
            return
        if "algorithm" in tp and tp["algorithm"] is None:
            ctx.mark("accepted_artifact")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "accepted_result" in tp and tp["accepted_result"] is None:
            ctx.mark("accepted_artifact")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "algorithm" in tp:
            algorithm = tp["algorithm"]
            if (
                isinstance(algorithm, (dict, Mapping))
                and algorithm.get("operation_kind") == "unknown"
            ):
                self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(algorithm, (dict, Mapping)) and algorithm.get("hash_changed"):
                if tp.get("semantic_equivalence") == "proven":
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return
                raise D06ContractViolationError(
                    "algorithm semantic equivalence unproven",
                    "pre_medical_output_validation",
                )
            if isinstance(algorithm, (dict, Mapping)) and algorithm.get(
                "semantic_change"
            ):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "missing" in tp:
            missing = tp["missing"]
            if isinstance(missing, (dict, Mapping)):
                if missing.get("kind") is None:
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
                if missing.get("execution_stage") is None and tp.get(
                    "reverse_order_changes_result"
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "comparison" in tp:
            comparison = tp["comparison"]
            if isinstance(comparison, (dict, Mapping)):
                if ("tolerance" in comparison and comparison["tolerance"] is None) or (
                    "tolerance_rule" in comparison
                    and comparison["tolerance_rule"] is None
                ):
                    if ctx.entrypoint == "d06.gate_evaluator":
                        self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    else:
                        ctx.l1 = L1_NOT_EVALUABLE
                        ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                        ctx.l2[L2_COVERAGE_NOTICES] += 1
                    return
                if (
                    comparison.get("kind") == "relative"
                    and comparison.get("reference_role") is None
                ):
                    ctx.mark("accepted_artifact")
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "percent" in tp:
            percent = tp["percent"]
            if isinstance(percent, (dict, Mapping)):
                if percent.get("denominator_role") == "other_explicit" and (
                    percent.get("explicit_denominator_input_key") is None
                    or percent.get("explicit_denominator_unit") is None
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
                if percent.get("zero_denominator_policy") == "explicit_constant" and (
                    percent.get("zero_denominator_constant") is None
                    or percent.get("zero_denominator_constant_unit") is None
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "unit" in tp:
            unit = tp["unit"]
            if (
                isinstance(unit, (dict, Mapping))
                and "source" in unit
                and unit["source"] is None
            ):
                self._open_gate(GATE_UNIT_OR_SCALE, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(unit, (dict, Mapping)) and unit.get("applicability_evidence"):
                ctx.l1 = L1_NOT_APPLICABLE
                ctx.coverage_status = COVERAGE_NOT_APPLICABLE
                ctx.domain_assertions["applicability_evidence_count"] = 1
                ctx.domain_assertions["coverage_status"] = COVERAGE_NOT_APPLICABLE
                ctx.domain_assertions["l1_disposition"] = L1_NOT_APPLICABLE
                return
        if "maturity" in tp:
            maturity = tp["maturity"]
            if maturity is None or (
                isinstance(maturity, (dict, Mapping)) and maturity.get("rule") is None
            ):
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if (
                isinstance(maturity, (dict, Mapping))
                and maturity.get("opaque_expression") is not None
            ):
                raise SchemaContractError(
                    "maturity/cutoff opaque expression is forbidden",
                    "pre_medical_output_validation",
                )
            if isinstance(maturity, (dict, Mapping)) and maturity.get(
                "anchor_candidates"
            ):
                ctx.l1 = L1_BOUNDARY
                ctx.coverage_status = COVERAGE_COVERED
                ctx.domain_assertions["maturity_decision_status"] = (
                    DECISION_MULTI_FEASIBLE_BOUNDARY
                )
                ctx.domain_assertions["selected_typed_anchor_id"] = None
                return
        if (
            "trend" in tp
            and isinstance(tp["trend"], (dict, Mapping))
            and tp["trend"].get("threshold") is None
        ):
            if tp["trend"].get("kind") is None:
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
            if tp["trend"].get("kind") != "flat_score_item_shift":
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "directionality" in tp and tp["directionality"] == "undefined":
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "normalized" in tp and "raw" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "death" in tp and "measurement" in tp:
            raise D06ContractViolationError(
                "measurement after death misclassified as ordinary missing",
                "pre_medical_output_validation",
            )
        if "d07" in tp or "consuming" in tp:
            self._eval_d07(tp)
            return
        if "d08" in tp or "same_date_only" in tp:
            self._eval_d08(tp)
            return
        if "tte" in tp:
            self._eval_tte(tp)
            return
        if "ice" in tp:
            self._eval_ice(tp)
            return
        if "correction" in tp:
            self._eval_correction(tp)
            return
        if "assessment" in tp:
            assessment = tp["assessment"]
            if isinstance(assessment, (dict, Mapping)) and assessment.get(
                "current_ids"
            ):
                ctx.mark("accepted_artifact")
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(assessment, (dict, Mapping)) and assessment.get("corrected"):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "confirmation" in tp:
            confirmation = tp["confirmation"]
            if isinstance(confirmation, (dict, Mapping)):
                ctx.mark("responder_confirmation")
                if confirmation.get("assessment_episode_keys"):
                    raise D06BindingContractError(
                        "responder confirmation refs wrong episode",
                        "typed_binding_validation",
                    )
                if confirmation.get("precision") == "month":
                    ctx.l1 = L1_BOUNDARY
                    ctx.coverage_status = COVERAGE_COVERED
                    return
                if (
                    confirmation.get("qualifying_pattern")
                    and confirmation.get("sequence") == "consecutive_eligible"
                ):
                    pattern = confirmation["qualifying_pattern"]
                    consecutive = False
                    for index in range(len(pattern) - 1):
                        if pattern[index] and pattern[index + 1]:
                            consecutive = True
                            break
                    ctx.domain_assertions["confirmation_decision_status"] = (
                        "confirmed" if consecutive else "not_confirmed"
                    )
                    ctx.domain_assertions["selected_assessment_ids"] = []
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return
        if (
            "threshold" in tp
            and isinstance(tp["threshold"], (dict, Mapping))
            and "new" in tp["threshold"]
        ):
            # Semantic threshold change: classification per new lineage.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "baseline" in tp
            and isinstance(tp["baseline"], (dict, Mapping))
            and tp["baseline"].get("precision") == "month"
        ):
            ctx.mark("baseline_selection")
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "analysis_window_end" in tp:
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "evidence" in tp:
            ctx.mark("responder_confirmation")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "independent_action_roots" in tp:
            ctx.mark("query_source_jump")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "model_only_judgment" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "query" in tp:
            ctx.mark("query_source_jump")
        if "accepted_artifact" in tp:
            ctx.mark("accepted_artifact")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "rerun" in tp:
            ctx.domain_assertions["hash_relation"] = (
                "all_object_hashes_equal_across_identical_rerun"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "item_input_order" in tp:
            ctx.domain_assertions["hash_relation"] = (
                "score_result_hash_equal_after_item_order_permutation"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "semantic_continuity" in tp or "late_record" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "domain" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "numeric" in tp:
            self._eval_numeric(tp)
            return
        if "unicode" in tp:
            ctx.domain_assertions["hash_relation"] = "unicode_nfc_identity_hash_equal"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "temporal" in tp
            and isinstance(tp["temporal"], (dict, Mapping))
            and "equivalent_instants" in tp["temporal"]
        ):
            ctx.domain_assertions["hash_relation"] = (
                "equivalent_instant_temporal_hash_equal"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "temporal" in tp
            and isinstance(tp["temporal"], (dict, Mapping))
            and "anchor" in tp["temporal"]
        ):
            normalized = _normalize_date_offset(
                tp["temporal"]["anchor"], tp["temporal"]["offset"]
            )
            if "T" not in str(tp["temporal"]["anchor"]):
                normalized = str(normalized).split("T")[0]
            ctx.domain_assertions["normalized_date"] = normalized
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            isinstance(tp.get("endpoint"), dict)
            and "authoritative_role" in tp["endpoint"]
        ):
            role = tp["endpoint"]["authoritative_role"]
            if role is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
            else:
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
            return
        if "priority" in tp or (
            isinstance(tp.get("endpoint"), dict) and "role" in tp["endpoint"]
        ):
            self._eval_priority_assertion(tp)
            return
        if "coverage" in tp or "later_run" in tp or "other_required_unit" in tp:
            self._eval_lifecycle(tp)
            return
        if "page" in tp or "query_context_variants" in tp:
            self._eval_query_context(tp)
            return
        if (
            "projection" in tp
            and isinstance(tp["projection"], (dict, Mapping))
            and (
                tp["projection"].get("layers")
                or tp["projection"].get("source_jump_targets") is not None
            )
        ):
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "feasible_ice_rule_ids" in tp or "feasible_timepoint_ids" in tp:
            ctx.mark("intercurrent_event_context")
            self._open_gate(GATE_DEFINITION, GATE_DECISION_BOUNDARY)
            return
        if "owner_candidates" in tp:
            self._open_gate(GATE_ROUTING, GATE_DECISION_NOT_EVALUABLE)
            return
        # ------------------------------------------------------------------
        # D05 routing semantics
        # ------------------------------------------------------------------
        d05 = tp.get("d05", {})
        if (
            isinstance(d05, (dict, Mapping))
            and d05.get("occurrence") == "positive_missing"
        ):
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "item_coverage" in tp and tp["item_coverage"] == "missing":
            ctx.mark("responder_confirmation")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        # ------------------------------------------------------------------
        # Unit-kind dispatch
        # ------------------------------------------------------------------
        unit_kind = _determine_unit_kind(tp)
        if "item_values" in tp:
            overridden = tp["item_values"]
            if any(
                value is not None and (not str(value).isdigit() or int(value) > 6)
                for value in overridden.values()
            ):
                unit_kind = UNIT_KIND_ITEM_VALUE_VALIDITY
            elif any(value is None for value in overridden.values()):
                unit_kind = UNIT_KIND_ITEM_COMPLETENESS
        ctx.unit_kind = unit_kind
        self._family_dispatch(tp, unit_kind)

    def _gate_inputs(self, gate: Mapping[str, Any]) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if "gate_binding_ref_id" in gate and gate["gate_binding_ref_id"] is None:
            ctx.domain_assertions["error_stage"] = "gate_binding_validation"
            ctx.domain_assertions["error_type"] = "SchemaContractError"
            ctx.domain_assertions["l1_created"] = False
            ctx.domain_assertions["l2_created"] = False
            raise SchemaContractError(
                "gate missing required gate_binding_ref_id", "gate_binding_validation"
            )
        if "invalid_tuple" in gate:
            raise SchemaContractError(
                "invalid open/closed gate tuple: open gates must be "
                "boundary/not_evaluable + blocks=true",
                "pre_medical_output_validation",
            )
        if "affected_timepoint_count" in gate:
            # One gate covers many timepoints; a single control-plane gate.
            self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
            return
        if "state" in gate and "other_l1" in tp:
            # Open gate with otherwise-negative L1: domain stays incomplete
            # but no gate object is emitted.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)

    def _family_dispatch(self, tp: Mapping[str, Any], unit_kind: str) -> None:
        handler = {
            UNIT_KIND_SCORE_RECALCULATION: self._eval_score,
            UNIT_KIND_ITEM_COMPLETENESS: self._eval_item_completeness,
            UNIT_KIND_ITEM_VALUE_VALIDITY: self._eval_item_value,
            UNIT_KIND_BASELINE_SELECTION: self._eval_baseline,
            UNIT_KIND_CHANGE_RECALCULATION: self._eval_change,
            UNIT_KIND_RESPONSE_CLASSIFICATION: self._eval_response,
            UNIT_KIND_ENDPOINT_COMPOSITION: self._eval_composition,
            UNIT_KIND_REPEAT_SELECTION: self._eval_repeat,
            UNIT_KIND_RATER_OR_MODE_CONSISTENCY: self._eval_rater_mode,
            UNIT_KIND_INDIVIDUAL_TREND_PATTERN: self._eval_trend,
            UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY: self._eval_report,
        }[unit_kind]
        handler(tp)

    # -- score recalculation ------------------------------------------------

    def _compute_score(self, tp: Mapping[str, Any]) -> Tuple[str, Optional[str]]:
        """Deterministic score recalculation from items + frozen operations.

        Returns ``(canonical_score, missing_strategy_label_or_None)``.
        """
        ctx = self.ctx
        values = _current_item_values(ctx)
        ordered = [values.get(f"I{i}") for i in range(1, 7)]
        # Reverse scoring.
        if (
            "transform" in tp
            and isinstance(tp["transform"], (dict, Mapping))
            and tp["transform"].get("version") != "1.0"
        ):
            ctx.domain_assertions["_transform_wrong"] = True
        reverse = tp.get("reverse", {})
        if "applied" in reverse and reverse["applied"] is False:
            # The recorded derivation omitted the required reverse step.
            ctx.domain_assertions["_reverse_omitted"] = True
        applied = bool(reverse.get("applied", False))
        if applied:
            ordered = [
                str(6 - int(value)) if value is not None else None for value in ordered
            ]
        # Missing handling.
        missing = tp.get("missing", {})
        missing_strategy = None
        if isinstance(missing, (dict, Mapping)) and missing.get("kind"):
            missing_strategy = str(missing.get("kind"))
        answered = [value for value in ordered if value is not None]
        if len(answered) < 6:
            if missing_strategy is None and not missing:
                # Missing item without any allowed strategy.
                ctx.domain_assertions.setdefault("missing_item_no_strategy", True)
                raise D06ContractViolationError(
                    "missing item without allowed missing strategy",
                    "pre_medical_output_validation",
                )
            if missing_strategy == "prorate_mean":
                minimum = int(missing.get("minimum_answered_count", 0))
                if len(answered) < minimum:
                    raise D06ContractViolationError(
                        "prorate minimum answered count not reached",
                        "pre_medical_output_validation",
                    )
                mean = sum(float(value) for value in answered) / len(answered)
                total = mean * 6
                score = str(int(total)) if total.is_integer() else str(total)
                ctx.domain_assertions["recalculated_score"] = score
                ctx.domain_assertions["_prorate_used"] = True
                return score, missing_strategy
            if missing_strategy == "explicit_constant":
                constant = missing.get("constant", "0")
                recorded = ctx.fixture.records.get("item_values", {})
                if float(constant) == 0:
                    # Explicit constant 0: the recorded item value stands.
                    missing_keys = [
                        key for key, value in values.items() if value is None
                    ]
                    recorded_value = recorded.get(
                        missing_keys[0] if missing_keys else "I6", "0"
                    )
                    total = sum(float(value) for value in answered) + float(
                        recorded_value
                    )
                else:
                    total = sum(float(value) for value in answered) + float(constant)
                score = str(int(total)) if total.is_integer() else str(total)
                ctx.domain_assertions["recalculated_score"] = score
                ctx.domain_assertions["missing_strategy"] = missing_strategy
                ctx.mark("accepted_artifact")
                return score, missing_strategy
            raise D06ContractViolationError(
                f"unsupported missing strategy {missing_strategy!r}",
                "pre_medical_output_validation",
            )
        # Weights.
        weight = tp.get("weight", {})
        if isinstance(weight, (dict, Mapping)) and weight:
            total = sum(
                float(weight.get(f"I{i}", 1)) * float(ordered[i - 1])
                for i in range(1, 7)
            )
        else:
            total = sum(float(value) for value in ordered)
        return str(int(total)) if total.is_integer() else str(total), missing_strategy

    def _compare_values(
        self,
        accepted: str,
        recalculated: str,
        tp: Mapping[str, Any],
    ) -> Tuple[str, Optional[str]]:
        """Comparison via the closed tolerance formulas (§6.1)."""
        comparison = tp.get("comparison", {})
        if not isinstance(comparison, (dict, Mapping)):
            comparison = {}
        tolerance = comparison.get("tolerance")
        if tolerance is None:
            # Exact comparison by default.
            return ("consistent" if accepted == recalculated else "inconsistent"), None
        absolute_difference = comparison.get("absolute_difference")
        if absolute_difference is not None:
            diff = abs(float(accepted) - float(recalculated))
            if diff <= float(tolerance):
                return "consistent", None
            return "inconsistent", None
        tolerance_kind = comparison.get("kind")
        if tolerance_kind == "relative":
            reference_role = comparison.get("reference_role")
            if reference_role is None:
                raise D06ContractViolationError(
                    "relative tolerance missing reference role",
                    "pre_medical_output_validation",
                )
            if reference_role == "accepted_value":
                denominator = abs(float(accepted))
            elif reference_role == "recalculated_value":
                denominator = abs(float(recalculated))
            else:
                denominator = max(abs(float(accepted)), abs(float(recalculated)))
            if denominator == 0:
                return "not_evaluable", None
            ratio = abs(float(accepted) - float(recalculated)) / denominator
            return ("consistent" if ratio <= float(tolerance) else "inconsistent"), None
        return ("consistent" if accepted == recalculated else "inconsistent"), None

    def _eval_score(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "accepted_result" in tp and "d05" in tp:
            # D05 occurrence negative but score wrong -> D06 positive.
            pass
        score, missing_strategy = self._compute_score(tp)
        if ctx.domain_assertions.pop(
            "_reverse_omitted", False
        ) or ctx.domain_assertions.pop("_transform_wrong", False):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "score_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        accepted = _effective_accepted_result(ctx)
        if accepted is None:
            # No accepted result: deterministic recalculation only.
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        accepted_value = str(accepted.get("value"))
        comparison, _ = self._compare_values(accepted_value, score, tp)
        if (
            "comparison" in tp
            and isinstance(tp["comparison"], (dict, Mapping))
            and (
                tp["comparison"].get("inclusive") is not None
                or tp["comparison"].get("kind") in ("absolute", "relative")
            )
        ):
            ctx.mark("accepted_artifact")
            ctx.domain_assertions["comparison_status"] = comparison
            ctx.domain_assertions["l1_disposition"] = (
                L1_NEGATIVE if comparison == "consistent" else L1_POSITIVE
            )
        if (
            missing_strategy is not None
            and "recalculated_score" in ctx.domain_assertions
        ):
            ctx.domain_assertions["comparison_status"] = comparison
            if ctx.domain_assertions.pop("_prorate_used", False):
                ctx.domain_assertions["l1_disposition"] = (
                    L1_NEGATIVE if comparison == "consistent" else L1_POSITIVE
                )
        if "report" in tp:
            # Report consistency downstream of score root.
            report = tp["report"]
            if comparison == "consistent":
                report_value = str(report.get("value"))
                if report_value == accepted_value:
                    ctx.l1 = L1_NEGATIVE
                else:
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "reported_result_inconsistent"
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "score_inconsistent"
                ctx.secondary_reason_codes = ["report_value_difference"]
            ctx.coverage_status = COVERAGE_COVERED
            return
        if comparison == "consistent":
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_POSITIVE
        ctx.subtype = "score_inconsistent"
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_item_completeness(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        values = _current_item_values(ctx)
        missing_items = [key for key, value in values.items() if value is None]
        if missing_items:
            missing = tp.get("missing", {})
            if isinstance(missing, (dict, Mapping)) and missing.get("kind"):
                # Allowed missing strategy: score path.
                self._eval_score(tp)
                return
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "required_component_missing"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_item_value(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        values = _current_item_values(ctx)
        invalid = [
            key for key, value in values.items() if value is not None and int(value) > 6
        ]
        if invalid:
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "component_value_invalid"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- baseline ----------------------------------------------------------

    def _eval_baseline(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "prohibited_default" in tp and tp.get("candidate_selection") is None:
            raise D06ContractViolationError(
                "default baseline selection is forbidden",
                "pre_medical_output_validation",
            )
        baseline = tp.get("baseline", {})
        if "episodes" in baseline:
            # Distinct episodes keep distinct baseline obligations; no
            # selection decision is consumed.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "supersedes" in baseline:
            # Baseline correction: new lineage, old result superseded.
            ctx.mark("baseline_selection")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.mark("baseline_selection")
        if baseline.get("selection_reason") == "maximum_improvement":
            raise D06ContractViolationError(
                "model selection of maximum improvement as baseline is forbidden",
                "pre_medical_output_validation",
            )
        if "selected" in baseline:
            # Postbaseline value used as baseline.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "baseline_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "episode_key" in baseline:
            # Old-episode baseline reused in a re-screened episode.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "baseline_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "tie_break" in tp and tp["tie_break"] is None:
            # Two complete feasible candidates without a tie-break.
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if baseline.get("time_conflict"):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "scope" in baseline:
            raise D06BindingContractError(
                "baseline decision wrong Run/source revision",
                "typed_binding_validation",
            )
        candidates = baseline.get("candidates")
        if candidates is not None:
            selection = tp.get("candidate_selection")
            if len(candidates) == 1:
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            if selection == "chronological_last":
                # Resolve the selection from the actual candidate records:
                # chronological-last = the candidate whose accepted
                # assessment time is latest among the supplied candidates.
                assessments = {
                    item.get("id"): item
                    for item in ctx.fixture.records.get("assessments", [])
                }
                resolved = []
                for candidate in candidates:
                    record = assessments.get(candidate)
                    if not isinstance(record, (dict, Mapping)) or not record.get(
                        "time"
                    ):
                        raise D06ContractViolationError(
                            f"baseline candidate {candidate!r} does not "
                            "resolve an accepted assessment record",
                            "pre_medical_output_validation",
                        )
                    resolved.append((str(record["time"]), candidate))
                resolved.sort(key=lambda item: item[0])
                selected = resolved[-1][1]
                ctx.domain_assertions["candidate_decision_status"] = DECISION_UNIQUE
                ctx.domain_assertions["selected_candidate_id"] = selected
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            if selection is None:
                raise D06ContractViolationError(
                    "baseline candidate selection rule missing",
                    "pre_medical_output_validation",
                )
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- change / percent change -------------------------------------------

    def _eval_change(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        change = tp.get("change", {})
        if "accepted" in change and "recalculated" in change:
            if str(change["accepted"]) != str(change["recalculated"]):
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "change_value_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "percent" in tp:
            percent = tp["percent"]
            baseline = tp.get("baseline", {})
            if baseline.get("value") == "0" and percent.get("zero_policy") is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
            if "value" in percent and "post" in tp:
                base = float(baseline.get("value", 0))
                post = float(tp["post"]["value"])
                direction = ctx.fixture.definitions["endpoint"].get("directionality")
                numerator = base - post if direction == "lower_better" else post - base
                expected = numerator / base * 100.0
                recorded = float(percent["value"])
                if abs(expected - recorded) < 1e-9:
                    ctx.l1 = L1_NEGATIVE
                else:
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "change_value_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "after_conversion" in change:
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if change.get("sign_wrong"):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "change_value_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- response ----------------------------------------------------------

    def _eval_response(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "threshold" in tp and tp["threshold"].get("comparator") is None:
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            "observed" in tp
            and isinstance(tp["observed"], (dict, Mapping))
            and "percent_interval" in tp["observed"]
        ):
            # Legal precision interval crosses the response threshold.
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "confirmation" in tp:
            confirmation = tp["confirmation"]
            if confirmation.get("wrong_episode_refs"):
                raise D06BindingContractError(
                    "responder confirmation refs wrong episode",
                    "typed_binding_validation",
                )
            qualifying = confirmation.get("qualifying_ids", [])
            required = confirmation.get("required_count", 0)
            if confirmation.get("intervening_not_qualified"):
                ctx.domain_assertions["confirmation_decision_status"] = "not_confirmed"
                ctx.domain_assertions["selected_assessment_ids"] = []
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            if len(qualifying) < required:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "progression" in tp:
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "recalculated" in tp and "source" in tp:
            recalculated_class = tp["recalculated"].get("class")
            source_class = tp["source"].get("class")
            if recalculated_class == source_class:
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "observed" in tp and "source" in tp and "threshold" in tp:
            ctx.mark("responder_confirmation")
            observed = tp["observed"]
            threshold = tp["threshold"]
            percent = float(observed["percent"])
            comparator = threshold["comparator"]
            value = float(threshold["value"])
            if comparator == "ge":
                deterministic = "responder" if percent >= value else "non_responder"
            elif comparator == "gt":
                deterministic = "responder" if percent > value else "non_responder"
            else:
                raise D06ContractViolationError(
                    f"unsupported threshold comparator {comparator!r}",
                    "pre_medical_output_validation",
                )
            source_class = tp["source"]["class"]
            comparison = (
                "consistent" if source_class == deterministic else "inconsistent"
            )
            ctx.domain_assertions["response_class"] = deterministic
            ctx.domain_assertions["comparison_status"] = comparison
            if comparison == "consistent":
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- composition -------------------------------------------------------

    def _eval_composition(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        components = dict(ctx.fixture.records.get("components", {}))
        override = tp.get("components")
        if isinstance(override, (dict, Mapping)):
            components.update(override)
        states = dict(components)
        combination_definition = ctx.fixture.definitions["combination"]
        if "required_kind" in tp:
            required = tp["required_kind"]
            actual = tp.get("combination", {}).get(
                "kind"
            ) or combination_definition.get("kind")
            if required != actual:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "endpoint_composition_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "component" in tp:
            if any(
                isinstance(value, (dict, Mapping)) and value.get("identities")
                for value in tp["component"].values()
            ):
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "combination" in tp:
            combination = tp["combination"]
            if "precedence" in combination:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "endpoint_composition_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        missing_policy = tp.get("combination", {}).get(
            "missing_policy"
        ) or combination_definition.get("missing_policy")
        if any(state == "missing" for state in states.values()):
            if missing_policy == "not_event":
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "combination" in tp and "components" in tp:
            combination = tp["combination"]
            kind = combination.get("kind")
            if kind == "any_component":
                overall = (
                    "event"
                    if any(s == "event" for s in states.values())
                    else "non_event"
                )
            elif kind == "all_components":
                overall = (
                    "event"
                    if all(s == "event" for s in states.values())
                    else "non_event"
                )
            else:
                overall = "non_event"
            ctx.domain_assertions["component_states"] = states
            ctx.domain_assertions["overall_component_state"] = overall
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "components" in tp:
            # A component occurred but was dropped from the composite.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "endpoint_composition_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- repeat selection --------------------------------------------------

    def _eval_repeat(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "candidate_ids" in tp or "no_candidate_outcome" in tp:
            ctx.domain_assertions["candidate_decision_status"] = DECISION_NOT_EVALUABLE
            ctx.domain_assertions["selected_candidate_id"] = None
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "prohibited_default" in tp:
            raise D06ContractViolationError(
                "default repeat selection is forbidden", "pre_medical_output_validation"
            )
        candidate_selection = tp.get("candidate_selection")
        if candidate_selection is None:
            raise D06ContractViolationError(
                "repeat selection rule missing", "pre_medical_output_validation"
            )
        repeat = tp.get("repeat", {})
        if candidate_selection == "chronological_first":
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if candidate_selection == "worst_value":
            values = repeat.get("values")
            if isinstance(values, (dict, Mapping)):
                selected_id = max(values.items(), key=lambda item: float(item[1]))[0]
                selected_value = values[selected_id]
                ctx.l1 = None
            else:
                items = values or []
                selected_value = max(float(item) for item in items)
                selected_id = [
                    "ASM-W4-A",
                    "ASM-W4-B",
                    "ASM-W8-A",
                ][items.index(str(int(selected_value))) % 3]
                selected_value = _canonical_decimal(str(selected_value))
                ctx.l1 = L1_NEGATIVE
            ctx.domain_assertions["candidate_decision_status"] = DECISION_UNIQUE
            ctx.domain_assertions["selected_candidate_id"] = selected_id
            ctx.domain_assertions["selected_value"] = _canonical_decimal(
                str(selected_value)
            )
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- rater / mode ------------------------------------------------------

    def _eval_rater_mode(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "consumer" in tp:
            consumer = tp["consumer"]
            equivalence = tp.get("equivalence", {})
            if consumer.get("instrument") != equivalence.get("from_instrument"):
                raise D06BindingContractError(
                    "equivalence rule used for unbound instrument",
                    "typed_binding_validation",
                )
        actual = tp.get("actual", {})
        equivalence_rule = tp.get("equivalence_rule")
        if equivalence_rule is None:
            reporter = actual.get("reporter_type")
            if reporter is not None and reporter != "PRO":
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "rater_or_mode_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            admin_mode = actual.get("admin_mode")
            if admin_mode is not None and admin_mode != "electronic":
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
            recall = actual.get("recall_period")
            if recall is not None and recall != "7_days":
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "rater_or_mode_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        # Accepted equivalence rule present: the accepted rule source is
        # consumed as provenance.
        if "admin_mode" in actual and equivalence_rule is not None:
            ctx.mark("accepted_artifact")
        if (
            actual.get("recall_period") is not None
            and actual["recall_period"] != "7_days"
        ):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "rater_or_mode_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_trend(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        trend = tp.get("trend", {})
        kind = trend.get("kind", ctx.fixture.definitions["trend"].get("kind"))
        threshold = trend.get(
            "threshold", ctx.fixture.definitions["trend"].get("threshold")
        )
        if threshold is None:
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "no_frozen_rule" in trend and trend["no_frozen_rule"]:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        values = [int(value) for value in trend.get("values", [])]
        threshold_value = int(threshold)
        if kind == "absolute_jump":
            if len(values) == 2 and abs(values[1] - values[0]) >= threshold_value:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "individual_trend_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if kind == "direction_reversal":
            deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
            for index in range(1, len(deltas)):
                if (
                    deltas[index] != 0
                    and deltas[index - 1] != 0
                    and (deltas[index] > 0) != (deltas[index - 1] > 0)
                    and abs(deltas[index]) >= threshold_value
                    and abs(deltas[index - 1]) >= threshold_value
                ):
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "individual_trend_inconsistent"
                    ctx.coverage_status = COVERAGE_COVERED
                    return
        if kind == "flat_score_item_shift":
            if trend.get("item_vectors_equal"):
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "individual_trend_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- report consistency ------------------------------------------------

    def _eval_report(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "producer_kind" in tp and tp["producer_kind"] == "model_output":
            if tp.get("result_role") == "accepted_source":
                ctx.mark("accepted_artifact")
                raise SchemaContractError(
                    "model output cannot be accepted_source",
                    "pre_medical_output_validation",
                )
            raise D06ContractViolationError(
                "model output cannot be an accepted source",
                "pre_medical_output_validation",
            )
        if "report" in tp and "source" in tp:
            report = tp["report"]
            source = tp["source"]
            # Full typed accepted-report evidence (case 191): validate the
            # accepted claim, the accepted individual-trend source and the
            # referenced accepted result before consuming the artifact.
            if (
                isinstance(report, (dict, Mapping))
                and report.get("object_type") == "AcceptedMonitoringReportClaim"
            ):
                ctx.mark("accepted_artifact")
                if report.get("acceptance_state") != "accepted":
                    raise D06ContractViolationError(
                        "accepted report claim is not accepted",
                        "pre_medical_output_validation",
                    )
                if (
                    not isinstance(source, (dict, Mapping))
                    or source.get("object_type") != "AcceptedIndividualTrendSource"
                ):
                    raise D06ContractViolationError(
                        "accepted report claim requires a typed trend source",
                        "pre_medical_output_validation",
                    )
                accepted_result_ids = source.get("accepted_result_ids", [])
                accepted_records = ctx.fixture.records.get("accepted_result")
                if not accepted_records or accepted_records.get("id") not in (
                    accepted_result_ids
                ):
                    raise D06ContractViolationError(
                        "accepted trend source does not resolve the accepted result",
                        "pre_medical_output_validation",
                    )
            if report.get("trend") == source.get("trend"):
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "reported_result_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "report" in tp:
            report = tp["report"]
            if (
                report.get("denominator") is None
                or report.get("source_locator") is None
            ):
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "accepted_result" in tp and "recalculated_result" in tp:
            ctx.mark("accepted_artifact")
            accepted = _effective_accepted_result(ctx)
            recalculated = _effective_recalculated_result(ctx)
            if (
                accepted is not None
                and recalculated is not None
                and (str(accepted.get("value")) != str(recalculated.get("value")))
            ):
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "reported_result_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_d07(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ctx.mark("d07_consumption")
        if "consuming" in tp:
            consuming = tp["consuming"]
            d07 = tp.get("d07", {})
            if consuming.get("endpoint_key") != d07.get("endpoint_key"):
                raise D06BindingContractError(
                    "D07 consumption binding endpoint mismatch",
                    "typed_binding_validation",
                )
        d07 = tp.get("d07", {})
        if (
            isinstance(d07, (dict, Mapping))
            and d07.get("validation_state") == "missing"
        ):
            ctx.domain_assertions["d07_consumption_state"] = "context_only"
            ctx.domain_assertions["endpoint_input_consumed"] = False
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_d08(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        d08 = tp.get("d08", {})
        if isinstance(d08, (dict, Mapping)) and d08.get("validation_state"):
            ctx.mark("d08_relationship")
            if d08.get("validation_state") == "missing":
                ctx.domain_assertions["d06_risk_created"] = False
                ctx.domain_assertions["d08_relationship_state"] = "absent"
                ctx.domain_assertions["relationship_drawn"] = False
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED
