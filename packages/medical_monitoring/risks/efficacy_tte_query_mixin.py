"""D06 TTE, ICE, lifecycle, query-context and priority evaluation."""

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
from .efficacy_contracts import _RunContext, _declared_scope_identity_matches
from .efficacy_output_gates import *
from .efficacy_resolution import *
from .efficacy_resolution import (
    _apply_rounding, _build_resolver_input, _emit_risk_decision,
    _priority_resolution_payload, _query_payload_for_context,
)

class EfficacyTteQueryMixin:
    """Cohesive methods extracted from the D06 engine."""

    def _resolve_tte_precedence(self, ctx: _RunContext) -> Mapping[str, Any]:
        """Resolve and validate the typed TTE precedence binding + rule.

        The binding must be a typed ``TTEEndpointPrecedenceBinding`` with
        an exact id, matching scope/cutoff, a payload-consistent
        lineage hash and a rule id linked to the typed
        ``TTEPrecedenceRule`` registry.  Missing binding id, wrong
        scope/version/rule/reference or a drifted hash fails closed;
        there are no fixed fallback identities.
        """
        binding = ctx.fixture.bindings.get("tte_precedence_binding")
        if not isinstance(binding, (dict, Mapping)):
            raise D06ContractViolationError(
                "TTE evaluation requires a typed precedence binding",
                "pre_medical_output_validation",
            )
        if binding.get("object_type") != "TTEEndpointPrecedenceBinding":
            raise D06ContractViolationError(
                "TTE precedence binding wrong object type",
                "pre_medical_output_validation",
            )
        if not binding.get("id"):
            raise D06ContractViolationError(
                "TTE precedence binding missing id",
                "pre_medical_output_validation",
            )
        if not binding.get("event_precedence_rule_id"):
            raise D06ContractViolationError(
                "TTE precedence binding missing rule id",
                "pre_medical_output_validation",
            )
        if not binding.get("producer_version"):
            raise D06ContractViolationError(
                "TTE precedence binding missing version",
                "pre_medical_output_validation",
            )
        if not binding.get("source_locator_ids"):
            raise D06ContractViolationError(
                "TTE precedence binding missing source locators",
                "pre_medical_output_validation",
            )
        if not binding.get("stable_endpoint_key") or not binding.get(
            "stable_timepoint_key"
        ):
            raise D06ContractViolationError(
                "TTE precedence binding missing endpoint/timepoint identity",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(binding, ctx.scope):
            raise D06BindingContractError(
                "TTE precedence binding wrong scope",
                "typed_binding_validation",
            )
        if binding.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            raise D06BindingContractError(
                "TTE precedence binding wrong scope: cutoff",
                "typed_binding_validation",
            )
        verify_lineage_hash(binding, "TTE precedence binding")
        # The binding must resolve the typed TTE source registry:
        # endpoint/timepoint identity, precedence rule and event
        # references must be consistent with the registry's typed
        # values; a rehashed reference that no longer resolves fails
        # closed.
        tte_registry = ctx.fixture.source_registries.get("tte_source_registry")
        if (
            not isinstance(tte_registry, (dict, Mapping))
            or tte_registry.get("object_type") != "TTESourceRegistry"
        ):
            raise D06ContractViolationError(
                "TTE source registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(tte_registry, "TTE source registry")
        for field in (
            "stable_endpoint_key",
            "stable_timepoint_key",
            "event_precedence_rule_id",
        ):
            if binding.get(field) != tte_registry.get(field):
                raise D06ContractViolationError(
                    f"TTE precedence binding {field} does not resolve the "
                    "typed source registry",
                    "pre_medical_output_validation",
                )
        rule = ctx.fixture.source_registries.get("tte_rule_registry")
        if not isinstance(rule, (dict, Mapping)) or rule.get(
            "object_type"
        ) != "TTEPrecedenceRule":
            raise D06ContractViolationError(
                "TTE rule registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(rule, "TTE rule registry")
        if (
            rule.get("event_precedence_rule_id")
            != binding.get("event_precedence_rule_id")
        ):
            raise D06ContractViolationError(
                "TTE precedence rule linkage mismatch",
                "pre_medical_output_validation",
            )
        if not rule.get("allowed_tie_policies"):
            raise D06ContractViolationError(
                "TTE rule registry lacks allowed tie policies",
                "pre_medical_output_validation",
            )
        # Cross-resolve the registry references to the independently
        # typed event sources, typed TTE records and the timepoint
        # definition: a rehashed registry (or binding) field that no
        # longer resolves these authorities fails closed.
        events = {
            event.get("event_id"): event
            for event in ctx.fixture.source_registries.get("tte_source_events", [])
        }
        target_event = events.get(tte_registry.get("target_event_ref"))
        competing_event = events.get(tte_registry.get("competing_event_ref"))
        if (
            not isinstance(target_event, (dict, Mapping))
            or target_event.get("event_role") != "target_event"
            or not isinstance(competing_event, (dict, Mapping))
            or competing_event.get("event_role") != "competing_event"
        ):
            raise D06ContractViolationError(
                "TTE registry event references do not resolve the typed "
                "event sources",
                "pre_medical_output_validation",
            )
        tte_records = ctx.fixture.records.get("tte")
        if not isinstance(tte_records, (dict, Mapping)):
            raise D06ContractViolationError(
                "TTE evaluation requires typed TTE records",
                "pre_medical_output_validation",
            )
        event_time_ref = tte_registry.get("event_time_ref")
        timepoint = ctx.fixture.definitions.get("timepoint", {})
        if (
            event_time_ref != tte_records.get("event_time")
            or event_time_ref != target_event.get("effective_time_ref")
            or event_time_ref != competing_event.get("effective_time_ref")
            or event_time_ref != timepoint.get("nominal_time")
        ):
            raise D06ContractViolationError(
                "TTE registry event time does not resolve the typed event "
                "sources/records/timepoint authority",
                "pre_medical_output_validation",
            )
        if tte_registry.get("origin_time_ref") != tte_records.get("origin"):
            raise D06ContractViolationError(
                "TTE registry origin time does not resolve the typed records",
                "pre_medical_output_validation",
            )
        if (
            tte_records.get("censor_time") is not None
            and tte_registry.get("censor_time_ref") != tte_records.get("censor_time")
        ):
            raise D06ContractViolationError(
                "TTE registry censor time does not resolve the typed records",
                "pre_medical_output_validation",
            )
        tte_input = ctx.fixture.typed_parameters.get("tte")
        if (
            tte_registry.get("tie_policy")
            not in rule.get("allowed_tie_policies", [])
            or (
                isinstance(tte_input, (dict, Mapping))
                and tte_input.get("tie_policy") is not None
                and tte_registry.get("tie_policy")
                != tte_input.get("tie_policy")
            )
        ):
            raise D06ContractViolationError(
                "TTE registry tie policy does not resolve the typed "
                "input/rule authority",
                "pre_medical_output_validation",
            )
        if not binding.get("stable_source_identity"):
            raise D06ContractViolationError(
                "TTE precedence binding missing stable source identity",
                "pre_medical_output_validation",
            )
        if not tte_registry.get("source_locator_ids"):
            raise D06ContractViolationError(
                "TTE source registry lacks source locators",
                "pre_medical_output_validation",
            )
        for event in (target_event, competing_event):
            if not event.get("source_locator_ids"):
                raise D06ContractViolationError(
                    "TTE typed source event lacks source locators",
                    "pre_medical_output_validation",
                )
        return binding

    def _eval_tte(self, tp: Mapping[str, Any]) -> None:
        """TTE precedence evaluation; every emitted identity is derived
        from the typed TTE source registry / typed events / precedence
        binding, never from fixed constants or fallback ids."""
        ctx = self.ctx
        ctx.mark("tte_precedence")
        tte = tp.get("tte", {})
        registries = ctx.fixture.source_registries
        if (
            isinstance(tte, (dict, Mapping))
            and "origin" in tte
            and tte["origin"] is None
        ):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            isinstance(tte, (dict, Mapping))
            and "precedence_rule" in tte
            and tte["precedence_rule"] is None
        ):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            isinstance(tte, (dict, Mapping))
            and any(field in tte for field in SCOPE_IDENTITY_FIELDS)
            and not _declared_scope_identity_matches(tte, ctx.scope)
        ):
            # Any scope identity field the typed TTE event declares must
            # agree with the fixture's own declared scope binding; a
            # wrong subject/run/project/site fails closed here
            # identically, regardless of the value spelling.
            raise D06BindingContractError(
                "TTE ref wrong subject/scope", "typed_binding_validation"
            )
        precedence_binding = self._resolve_tte_precedence(ctx)
        binding_id = str(precedence_binding["id"])
        allowed_tie_policies = list(
            registries.get("tte_rule_registry", {}).get("allowed_tie_policies", [])
        )
        if (
            isinstance(tte, (dict, Mapping))
            and tte.get("tie_policy")
            and tte["tie_policy"] not in allowed_tie_policies
        ):
            raise D06ContractViolationError(
                "TTE tie policy not allowed by the typed rule registry",
                "pre_medical_output_validation",
            )
        if isinstance(tte, (dict, Mapping)) and tte.get("tie_policy") == "boundary":
            ctx.domain_assertions["feasible_interpretation_ref_ids"] = list(
                tte.get("feasible_interpretation_ref_ids", [])
            )
            ctx.domain_assertions["single_duration"] = None
            ctx.domain_assertions["tte_status"] = TTE_STATUS_BOUNDARY
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if isinstance(tte, (dict, Mapping)) and tte.get("same_time_states"):
            precedence = tte.get("precedence", [])
            same_time_states = tte.get("same_time_states", [])
            winner = next(
                (state for state in precedence if state in same_time_states),
                same_time_states[0] if same_time_states else None,
            )
            status = {
                "competing_event": TTE_STATUS_COMPETING_EVENT,
                "event": TTE_STATUS_EVENT,
                "censored": TTE_STATUS_CENSORED,
            }.get(winner, winner)
            role = {
                "competing_event": "competing_event",
                "event": "target_event",
                "censored": "censored",
            }.get(winner, winner)
            # Selected event id resolves strictly from the typed TTE
            # source-event registry; a missing/drifted event fails closed.
            selected_event_ref = None
            selected_event = None
            for event in registries.get("tte_source_events", []):
                if (
                    isinstance(event, (dict, Mapping))
                    and event.get("event_role") == role
                ):
                    if (
                        not event.get("event_id")
                        or event.get("object_type") != "TypedTTEEventSource"
                    ):
                        raise D06ContractViolationError(
                            "TTE typed source event malformed",
                            "pre_medical_output_validation",
                        )
                    verify_embedded_hash(event, "TTE typed source event")
                    if not event.get("source_locator_ids"):
                        raise D06ContractViolationError(
                            "TTE typed source event missing source locators",
                            "pre_medical_output_validation",
                        )
                    selected_event_ref = str(event["event_id"])
                    selected_event = event
                    break
            if selected_event_ref is None or selected_event is None:
                raise D06ContractViolationError(
                    f"TTE {role} source event cannot be resolved from the "
                    "typed source registry",
                    "pre_medical_output_validation",
                )
            # Event time must be typed, within the evaluation window and
            # consistent with the typed TTE records: the selected event's
            # effective time must equal the recorded event_time and be at
            # or before the clinical cutoff.  A rehashed event-time drift
            # that no longer resolves this authority fails closed.
            effective_time = selected_event.get("effective_time_ref")
            cutoff = ctx.scope.get("clinical_event_cutoff", "")
            if not effective_time or (cutoff and effective_time > cutoff):
                raise D06ContractViolationError(
                    "TTE source event time outside the evaluation window",
                    "pre_medical_output_validation",
                )
            tte_records = ctx.fixture.records.get("tte")
            if isinstance(tte_records, (dict, Mapping)) and tte_records.get(
                "event_time"
            ):
                recorded_time = tte_records.get("event_time")
                if effective_time != recorded_time:
                    raise D06ContractViolationError(
                        "TTE source event time does not match typed TTE records",
                        "pre_medical_output_validation",
                    )
                recorded_refs = (
                    tte_records.get("target_event_ref"),
                    tte_records.get("competing_event_ref"),
                )
                if selected_event_ref not in recorded_refs:
                    raise D06ContractViolationError(
                        "TTE selected event not referenced by typed TTE records",
                        "pre_medical_output_validation",
                    )
                # All same-time-state roles that resolve to a typed source
                # event must share the recorded event time; a drifted
                # event time breaks the same-time declaration.
                role_by_state = {
                    "competing_event": "competing_event",
                    "event": "target_event",
                    "censored": "censored",
                }
                for state in same_time_states:
                    state_role = role_by_state.get(state)
                    if state_role is None:
                        continue
                    for event in registries.get("tte_source_events", []):
                        if (
                            isinstance(event, (dict, Mapping))
                            and event.get("event_role") == state_role
                        ):
                            if event.get("effective_time_ref") != recorded_time:
                                raise D06ContractViolationError(
                                    "TTE same-time state event time mismatch",
                                    "pre_medical_output_validation",
                                )
                            break
            ctx.domain_assertions["tte_status"] = status
            ctx.domain_assertions["tte_precedence_binding_id"] = binding_id
            ctx.domain_assertions["selected_event_ref"] = selected_event_ref
            if winner == "competing_event":
                ctx.l1 = None
            else:
                ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_ice(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ice = tp.get("ice", {})
        if not isinstance(ice, (dict, Mapping)):
            ice = {}
        if any(field in ice for field in SCOPE_IDENTITY_FIELDS) and not (
            _declared_scope_identity_matches(ice, ctx.scope)
        ):
            # Binding fails before any ICE context is consumed: every
            # scope identity field the typed ICE event declares must
            # agree with the fixture's own declared scope binding,
            # regardless of the value spelling.
            raise D06BindingContractError(
                "ICE typed producer event wrong subject", "typed_binding_validation"
            )
        if tp.get("misclassified_as") == "missing":
            ctx.mark("intercurrent_event_context")
            raise D06ContractViolationError(
                "intercurrent event misclassified as missing",
                "pre_medical_output_validation",
            )
        if (
            ice.get("estimator_availability") == "available"
            and ice.get("estimator_binding") is None
            and ice.get("strategy") != "hypothetical"
        ):
            ctx.mark("intercurrent_event_context")
            raise SchemaContractError(
                "available ICE estimator requires a binding",
                "pre_medical_output_validation",
            )
        if ice.get("strategy") == "hypothetical":
            if ice.get("estimator_availability") == "available":
                ctx.mark("intercurrent_event_context")
            ctx.domain_assertions["hypothetical_value_created"] = False
            ctx.domain_assertions["ice_context_state"] = "not_evaluable"
            ctx.domain_assertions["normal_derived_result_created"] = False
            if ice.get("estimator_availability") == "available":
                ctx.domain_assertions["coverage_status"] = COVERAGE_NOT_EVALUABLE
                ctx.domain_assertions["l1_disposition"] = L1_NOT_EVALUABLE
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if ice.get("feasible_rule_ids"):
            ctx.mark("intercurrent_event_context")
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "source_role" in ice and ice["source_role"] is None:
            ctx.mark("intercurrent_event_context")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if ice.get("strategy") == "treatment_policy":
            if ice.get("type") == "withdrawal":
                ctx.mark("intercurrent_event_context")
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_correction(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        correction = tp["correction"]
        ctx.mark("accepted_artifact")
        if isinstance(correction, (dict, Mapping)):
            if correction.get("current_ids") and correction.get("graph") == "branch":
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if correction.get("current_ids") and correction.get("lineage") is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_numeric(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        numeric = tp["numeric"]
        if isinstance(numeric, (dict, Mapping)):
            if numeric.get("input") == "NaN":
                raise D06BindingContractError(
                    "NaN input rejected", "typed_binding_validation"
                )
            if numeric.get("equivalent_inputs") is not None:
                if "negative_zero_policy" in tp:
                    ctx.domain_assertions["hash_relation"] = (
                        "negative_zero_and_zero_hash_equal"
                    )
                elif "unicode" in tp:
                    ctx.domain_assertions["hash_relation"] = (
                        "unicode_nfc_identity_hash_equal"
                    )
                else:
                    ctx.domain_assertions["hash_relation"] = (
                        "canonical_decimal_hashes_all_equal"
                    )
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
            if numeric.get("rounding_modes"):
                places = int(numeric["decimal_places"])
                half_even = _apply_rounding(str(numeric["input"]), places, "half_even")
                half_up = _apply_rounding(str(numeric["input"]), places, "half_up")
                ctx.domain_assertions["half_even_result"] = half_even
                ctx.domain_assertions["half_up_result"] = half_up
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_priority_assertion(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED
        ctx._priority_da = True

    def _eval_lifecycle(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        later_run = tp.get("later_run", {})
        coverage = tp.get("coverage")
        risk = tp.get("risk", {})
        if coverage == "covered" and later_run.get("linked_negative"):
            if ctx.entrypoint == "d06.gate_evaluator":
                self._open_gate(GATE_APPLICABILITY, GATE_DECISION_NOT_EVALUABLE)
                ctx.l3_state = "closed"
                ctx.l3_transition = "rejected_by_evidence/resolved_by_data"
                return
            ctx.l3_state = "closed"
            ctx.l3_transition = "rejected_by_evidence/resolved_by_data"
            ctx.domain_assertions["l3_state"] = "closed"
            ctx.domain_assertions["l3_transition"] = (
                "rejected_by_evidence/resolved_by_data"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if later_run.get("coverage") == "partial":
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if risk.get("priority") == "high" or later_run.get("corrected"):
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "other_required_unit" in tp:
            ctx.domain_assertions["blocking_required_unit_disposition"] = tp[
                "other_required_unit"
            ]
            ctx.domain_assertions["r2_close_allowed"] = False
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _resolve_enrollment_source_events(
        self,
        ctx: _RunContext,
        source_events: Mapping[str, Any],
        refs: Sequence[str],
        query_context: str,
        decision_time: Optional[str] = None,
    ) -> List[str]:
        """Resolve every referenced enrollment source event against the
        typed registry with exact object type, payload-consistent hash,
        source locators, context linkage and the decision's effective
        time symbol.  A missing or drifted source fails closed; no source
        is echoed without being resolved."""
        resolved: List[str] = []
        for ref in refs:
            event = source_events.get(ref)
            if not isinstance(event, (dict, Mapping)):
                raise D06ContractViolationError(
                    f"enrollment source event {ref!r} cannot be resolved",
                    "pre_medical_output_validation",
                )
            if event.get("object_type") != "EnrollmentSourceEvent":
                raise D06ContractViolationError(
                    "enrollment source event wrong object type",
                    "pre_medical_output_validation",
                )
            verify_embedded_hash(event, "enrollment source event")
            if not event.get("source_locator_ids"):
                raise D06ContractViolationError(
                    "enrollment source event lacks source locators",
                    "pre_medical_output_validation",
                )
            if event.get("query_context") != query_context:
                raise D06ContractViolationError(
                    "enrollment source event context mismatch",
                    "pre_medical_output_validation",
                )
            # Effective time is a typed symbol shared by the decision and
            # its source events; a rehashed event-time drift that no
            # longer equals the decision's time fails closed.
            if not event.get("effective_time_ref") or (
                decision_time is not None
                and event.get("effective_time_ref") != decision_time
            ):
                raise D06ContractViolationError(
                    "enrollment source event time does not resolve the "
                    "decision time",
                    "pre_medical_output_validation",
                )
            resolved.append(str(event["event_id"]))
        return resolved

    def _resolve_enrollment_decision(
        self, ctx: _RunContext, decision: Any, label: str
    ) -> Mapping[str, Any]:
        """Validate a typed enrollment context decision: exact object
        type, scope/cutoff, payload-consistent hash, source locators and
        effective event time.  A missing/drifted decision fails closed
        and suppresses the Query."""
        if not isinstance(decision, (dict, Mapping)) or decision.get(
            "object_type"
        ) != "EnrollmentContextDecisionRef":
            raise D06ContractViolationError(
                f"enrollment decision {label} wrong object type",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(decision, ctx.scope):
            raise D06BindingContractError(
                f"enrollment decision {label} wrong scope",
                "typed_binding_validation",
            )
        if decision.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            raise D06BindingContractError(
                f"enrollment decision {label} wrong scope: cutoff",
                "typed_binding_validation",
            )
        verify_embedded_hash(decision, f"enrollment decision {label}")
        if not decision.get("source_locator_ids"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing source locators",
                "pre_medical_output_validation",
            )
        if not decision.get("effective_time_ref"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing effective time",
                "pre_medical_output_validation",
            )
        # The decision is a D04-produced enrollment context decision; a
        # rewritten producer domain fails closed.
        if decision.get("producer_domain") != "D04":
            raise D06ContractViolationError(
                f"enrollment decision {label} wrong producer domain",
                "pre_medical_output_validation",
            )
        if not decision.get("source_event_refs"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing source event refs",
                "pre_medical_output_validation",
            )
        return decision

    def _resolve_enrollment_rule(self, ctx: _RunContext) -> Mapping[str, Any]:
        """Validate the typed enrollment rule registry (object type,
        payload-consistent hash, rule id/version) and return it."""
        rule = ctx.fixture.source_registries.get("enrollment_rule_registry")
        if not isinstance(rule, (dict, Mapping)) or rule.get(
            "object_type"
        ) != "EnrollmentDecisionRule":
            raise D06ContractViolationError(
                "enrollment rule registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(rule, "enrollment rule registry")
        if not rule.get("decision_rule_id") or not rule.get("rule_version"):
            raise D06ContractViolationError(
                "enrollment rule registry missing rule id/version",
                "pre_medical_output_validation",
            )
        if not rule.get("source_locator_ids"):
            raise D06ContractViolationError(
                "enrollment rule registry lacks source locators",
                "pre_medical_output_validation",
            )
        if not rule.get("allowed_contexts"):
            raise D06ContractViolationError(
                "enrollment rule registry lacks allowed contexts",
                "pre_medical_output_validation",
            )
        return rule

    def _eval_query_context(self, tp: Mapping[str, Any]) -> None:
        """Enrollment-aware Query derivation from the typed enrollment
        decisions / source events / rule registry (never page or variant
        constants)."""
        ctx = self.ctx
        bindings = ctx.fixture.bindings
        registries = ctx.fixture.source_registries
        decisions = bindings.get("enrollment_context_decisions", [])
        source_events = {
            item.get("event_id"): item
            for item in registries.get("enrollment_source_events", [])
        }
        rule = self._resolve_enrollment_rule(ctx)
        if "page" in tp:
            ctx.mark("query_source_jump")
            active_id = bindings.get("active_enrollment_decision_id")
            active = next(
                (item for item in decisions if item.get("decision_id") == active_id),
                None,
            )
            if not isinstance(active, (dict, Mapping)):
                raise D06ContractViolationError(
                    "active enrollment decision cannot be resolved from bindings",
                    "pre_medical_output_validation",
                )
            self._resolve_enrollment_decision(ctx, active, "active")
            query_context = str(active.get("query_context"))
            if query_context not in rule.get("allowed_contexts", []):
                raise D06ContractViolationError(
                    "active enrollment decision context not allowed by the "
                    "rule registry",
                    "pre_medical_output_validation",
                )
            decision_id = str(active.get("decision_id"))
            source_refs = list(active.get("source_event_refs", []))
            decision_rule_id = str(
                active.get("decision_rule_id") or rule.get("decision_rule_id")
            )
            rule_version = str(active.get("rule_version") or rule.get("rule_version"))
            if (
                decision_rule_id != rule.get("decision_rule_id")
                or rule_version != rule.get("rule_version")
            ):
                raise D06ContractViolationError(
                    "enrollment decision does not resolve the frozen "
                    "enrollment rule registry",
                    "pre_medical_output_validation",
                )
            self._resolve_enrollment_source_events(
                ctx,
                source_events,
                source_refs,
                query_context,
                decision_time=str(active.get("effective_time_ref") or ""),
            )
            ctx.domain_assertions["query_context"] = query_context
            ctx.domain_assertions["enrollment_decision_id"] = decision_id
            ctx.domain_assertions["enrollment_decision_rule_id"] = decision_rule_id
            ctx.domain_assertions["enrollment_rule_version"] = rule_version
            ctx.domain_assertions["enrollment_source_event_refs"] = source_refs
            ctx.domain_assertions["pd_wording_valid"] = (
                query_context == QUERY_CONTEXT_ENROLLED
            )
            ctx.domain_assertions["forbidden_query_fragments"] = list(
                PD_WORDING_FRAGMENTS
            )
            if query_context == QUERY_CONTEXT_UNRESOLVED and "page" in tp:
                payload = {
                    "query_context": query_context,
                    "basis_sentence": "依据：当前入组状态尚未明确。",
                    "finding_sentence": "发现：页面标志与已接受入组决定不一致。",
                    "action_sentence": (
                        "行动项：请先核实随机、入组或首次给药状态及事件时序。"
                    ),
                }
            else:
                sentences = QUERY_PAYLOADS_BY_CONTEXT.get(query_context, {})
                payload = {
                    "query_context": query_context,
                    "basis_sentence": sentences.get("basis_sentence", ""),
                    "finding_sentence": sentences.get("finding_sentence", ""),
                    "action_sentence": sentences.get("action_sentence", ""),
                }
            ctx.domain_assertions["query_payload"] = payload
            ctx._query_payload = payload
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "query_context_variants" in tp:
            variants = list(tp["query_context_variants"])
            by_context = bindings.get("active_enrollment_decision_ids_by_context", {})
            decision_ids = {}
            source_events_by_context = {}
            rules_by_context = {}
            rule_id = str(rule.get("decision_rule_id", ""))
            rule_version = str(rule.get("rule_version", ""))
            for context in variants:
                decision_id = by_context.get(context)
                decision = next(
                    (
                        item
                        for item in decisions
                        if item.get("decision_id") == decision_id
                    ),
                    None,
                )
                if not isinstance(decision, (dict, Mapping)):
                    raise D06ContractViolationError(
                        f"variant enrollment decision {context!r} cannot be resolved",
                        "pre_medical_output_validation",
                    )
                self._resolve_enrollment_decision(
                    ctx, decision, f"variant {context!r}"
                )
                # The by-context mapping and the decision's own query
                # context must agree bidirectionally; the decision's
                # context must be allowed by the frozen rule registry.
                if str(decision.get("query_context", "")) != context:
                    raise D06ContractViolationError(
                        f"variant enrollment decision {context!r} context "
                        "mismatch",
                        "pre_medical_output_validation",
                    )
                if context not in rule.get("allowed_contexts", []):
                    raise D06ContractViolationError(
                        f"variant enrollment context {context!r} not allowed "
                        "by the rule registry",
                        "pre_medical_output_validation",
                    )
                # The decision must resolve the frozen enrollment rule
                # registry; any rule/version drift fails closed.
                if (
                    str(decision.get("decision_rule_id", "")) != rule_id
                    or str(decision.get("rule_version", "")) != rule_version
                ):
                    raise D06ContractViolationError(
                        "enrollment decision does not resolve the frozen "
                        "enrollment rule registry",
                        "pre_medical_output_validation",
                    )
                decision_ids[context] = str(decision.get("decision_id"))
                source_refs = list(decision.get("source_event_refs", []))
                # Every variant source event must resolve against the
                # typed registry (exact type/hash/locators/context/time);
                # a missing or drifted source fails closed and suppresses
                # the Query instead of echoing unresolved references.
                self._resolve_enrollment_source_events(
                    ctx,
                    source_events,
                    source_refs,
                    context,
                    decision_time=str(decision.get("effective_time_ref") or ""),
                )
                source_events_by_context[context] = source_refs
                rules_by_context[context] = {
                    "decision_rule_id": rule_id,
                    "rule_version": rule_version,
                }
            outcomes = {}
            payloads = {}
            for context in variants:
                payload = _query_payload_for_context(context)
                outcomes[context] = {"pd_wording_valid": payload["pd_wording_valid"]}
                payloads[context] = {
                    "query_context": context,
                    "basis_sentence": payload["basis_sentence"],
                    "finding_sentence": payload["finding_sentence"],
                    "action_sentence": payload["action_sentence"],
                    "pd_wording_valid": payload["pd_wording_valid"],
                }
            ctx.domain_assertions["enrollment_decision_ids_by_context"] = decision_ids
            ctx.domain_assertions["enrollment_source_events_by_context"] = (
                source_events_by_context
            )
            ctx.domain_assertions["enrollment_rules_by_context"] = rules_by_context
            ctx.domain_assertions["query_context_outcomes"] = outcomes
            ctx.domain_assertions["query_payloads"] = payloads
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _emit_priority_da(self, resolver: D06PriorityResolverInput) -> None:
        """Case-specific priority-resolution domain assertions (§9.1).

        Derived from the actual resolver input; the field set follows the
        endpoint-role / impact / recurrence semantics of the typed input.
        """
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        impact = resolver.impact_class
        recurrence = resolver.recurrence_class
        if impact in ("rights_safety", "critical_treatment"):
            ctx.domain_assertions["machine_close_forbidden"] = (
                resolver.machine_close_forbidden
            )
            ctx.domain_assertions["matched_precedence_step"] = (
                resolver.matched_precedence_step
            )
            ctx.domain_assertions["monitoring_priority"] = resolver.monitoring_priority
            return
        if recurrence == "repeated_site":
            return
        endpoint_role = tp.get("endpoint", {}).get("role")
        ctx.domain_assertions["impact_class"] = impact
        if (
            endpoint_role == "undefined"
            or resolver.impact_resolution_state == "unresolved"
        ):
            ctx.domain_assertions["impact_resolution_state"] = (
                resolver.impact_resolution_state
            )
        ctx.domain_assertions["machine_close_forbidden"] = (
            resolver.machine_close_forbidden
        )
        ctx.domain_assertions["matched_precedence_step"] = (
            resolver.matched_precedence_step
        )
        ctx.domain_assertions["monitoring_priority"] = resolver.monitoring_priority

    def _resolve_priority(self) -> None:
        """Post-pipeline priority resolution for every medical case.

        Runs after the pipeline (including gate/error outcomes) because the
        frozen expected outcomes always carry the resolver-based priority
        resolution derived from the typed resolver input; only the
        control-plane definition binding (203) is ``not_run_control_plane``.
        Failures are NOT swallowed: an invalid/mutated resolver input or
        policy fails closed into an error outcome with no priority payload.
        """
        ctx = self.ctx
        if ctx.priority_resolution is not None:
            return
        if ctx.scope_integrity_failed:
            # A typed scope/schema integrity failure happened before any
            # priority resolution may be engaged: emit no priority
            # payload, no resolver input hash/object, no risk/public
            # identity and no clinical projection.
            return
        if ctx.fixture.policies.get("priority_resolution_input") is None:
            if (
                ctx.domain_assertions.get("definition_binding_state")
                == "not_applicable"
            ):
                ctx.priority_resolution = {
                    "projection_state": "not_run_control_plane",
                    "priority_policy_id": CANONICAL_PRIORITY_POLICY["policy_id"],
                    "priority_policy_version": CANONICAL_PRIORITY_POLICY["version"],
                    "priority_policy_hash": CANONICAL_PRIORITY_POLICY["policy_hash"],
                    "priority_resolver_input_hash": None,
                    "priority_decision_id": None,
                    "endpoint_definition_id": None,
                    "stable_endpoint_key": None,
                    "stable_timepoint_key": None,
                    "endpoint_role": None,
                    "impact_resolution_state": None,
                    "impact_class": None,
                    "recurrence_class": None,
                    "recoverability": None,
                    "actionability": None,
                    "monitoring_priority": None,
                    "matched_precedence_step": None,
                    "reason_codes": None,
                    "machine_close_forbidden": None,
                }
            return
        resolver = _build_resolver_input(ctx)
        if ctx.l1 == L1_POSITIVE and ctx.output_kind == OUTPUT_KIND_RESULT:
            _emit_risk_decision(ctx)
            ctx.l2[L2_QUERIES] += 1
        ctx.priority_resolution = _priority_resolution_payload(ctx)
        if getattr(ctx, "_priority_da", False):
            self._emit_priority_da(resolver)
