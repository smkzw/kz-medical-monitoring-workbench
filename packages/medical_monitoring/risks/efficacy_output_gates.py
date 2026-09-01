"""D06 assessment-authority output gates."""

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
from .efficacy_contracts import _RunContext

def _validate_assessment_authority(
    ctx: _RunContext, assessment: Mapping[str, Any], label: str
) -> None:
    """Cross-resolve an accepted assessment against independent typed
    authorities (D05 binding refs / accepted inventory / foreign
    keys / instrument definition / item records).

    The assessment's lineage hash must be authenticated by the D05
    binding ref and inventory ``producer_payload_hash`` (never by
    recomputing the hash from the mutated object alone); its time
    must equal the ref/inventory ``actual_time_ref``; its binding
    ref must be in the foreign-key registry; its instrument, recall
    period, admin mode, item set/order, scope/cutoff, locators and
    accepted-current status must resolve the typed authorities.
    """
    aid = str(assessment.get("id", ""))
    if (
        assessment.get("object_type") != "ActualAssessmentRecord"
        or assessment.get("record_status") != "accepted_current"
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} is not an accepted-current "
            "ActualAssessmentRecord",
            "pre_medical_output_validation",
        )
    if not scope_identity_matches(assessment, ctx.scope):
        raise D06BindingContractError(
            f"accepted assessment {aid} wrong scope",
            "typed_binding_validation",
        )
    if assessment.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
        raise D06BindingContractError(
            f"accepted assessment {aid} wrong scope: cutoff",
            "typed_binding_validation",
        )
    inventory = {
        item.get("source_record_id"): item
        for item in ctx.fixture.source_registries.get(
            "accepted_d05_assessment_inventory", []
        )
    }
    refs = {
        item.get("source_record_id"): item
        for item in ctx.fixture.bindings.get("d05_refs", [])
    }
    foreign_keys = {
        item.get("source_record_id"): item
        for item in ctx.fixture.source_registries.get(
            "d05_assessment_foreign_keys", []
        )
    }
    inv_item = inventory.get(aid)
    ref = refs.get(aid)
    if not isinstance(inv_item, (dict, Mapping)) or not isinstance(
        ref, (dict, Mapping)
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks D05 inventory/binding authority",
            "pre_medical_output_validation",
        )
    foreign_key = foreign_keys.get(aid)
    if not isinstance(foreign_key, (dict, Mapping)):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks foreign-key authority",
            "pre_medical_output_validation",
        )
    # The accepted inventory item, the D05 binding ref and the
    # foreign-key registry entry are content-addressed authorities: their
    # embedded ``hash`` must match a recomputation over their own typed
    # fields before they are consumed.  A hash-only tamper on any one of
    # them fails closed instead of preserving the medical result.
    verify_embedded_hash(inv_item, f"accepted inventory item {aid}")
    verify_embedded_hash(ref, f"D05 binding ref {aid}")
    verify_embedded_hash(foreign_key, f"D05 foreign key {aid}")
    # Independent hash authentication: the accepted inventory and the
    # D05 binding ref carry the producer payload hash; a rehashed
    # assessment alone must not rewrite accepted truth.
    verify_lineage_hash(assessment, f"accepted assessment {aid}")
    if (
        assessment.get("lineage_hash")
        != inv_item.get("producer_payload_hash")
        or assessment.get("lineage_hash")
        != ref.get("producer_payload_hash")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lineage not authenticated by the "
            "accepted inventory/binding authority",
            "pre_medical_output_validation",
        )
    if (
        assessment.get("time") != inv_item.get("actual_time_ref")
        or assessment.get("time") != ref.get("actual_time_ref")
    ):
        raise D06BindingContractError(
            f"accepted assessment {aid} time not authenticated by the "
            "accepted inventory/binding authority",
            "typed_binding_validation",
        )
    if assessment.get("assessment_time_ref") not in (None, assessment.get("time")):
        raise D06BindingContractError(
            f"accepted assessment {aid} assessment time ref inconsistent",
            "typed_binding_validation",
        )
    foreign_key = foreign_keys.get(aid)
    if not isinstance(foreign_key, (dict, Mapping)) or foreign_key.get(
        "binding_ref_id"
    ) != ref.get("binding_ref_id"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} binding ref not in foreign keys",
            "pre_medical_output_validation",
        )
    # D05 semantic fields must agree bidirectionally across the accepted
    # assessment, the D05 binding ref, the accepted inventory and the
    # foreign-key registry; a partially synchronized rehash that drifts
    # any one of these fails closed.
    for field in (
        "d05_unit_id",
        "d05_planned_activity_key",
        "d05_actual_activity_key",
        "occurrence_disposition",
        "timing_disposition",
        "assignment_status",
    ):
        values = {
            assessment.get(field),
            ref.get(field),
            inv_item.get(field),
            foreign_key.get(field),
        }
        if len(values) != 1:
            raise D06ContractViolationError(
                f"accepted assessment {aid} {field} does not resolve the "
                "accepted D05 authority",
                "pre_medical_output_validation",
            )
    # Foreign-key producer payload/time authenticate the assessment
    # lineage and time independently.
    if (
        foreign_key.get("producer_payload_hash") != assessment.get("lineage_hash")
        or foreign_key.get("actual_time_ref") != assessment.get("time")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lineage/time not authenticated by the "
            "foreign-key registry",
            "pre_medical_output_validation",
        )
    if not ref.get("source_locator_ids"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} binding ref lacks source locators",
            "pre_medical_output_validation",
        )
    instrument = ctx.fixture.definitions.get("instrument", {})
    if (
        assessment.get("instrument_definition_id") != instrument.get("id")
        or assessment.get("actual_recall_period")
        != instrument.get("recall_period")
        or assessment.get("admin_mode") != instrument.get("admin_mode")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} instrument/recall/admin does not "
            "resolve the instrument definition",
            "pre_medical_output_validation",
        )
    if not assessment.get("stable_assessment_key"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} missing stable assessment key",
            "pre_medical_output_validation",
        )
    if not assessment.get("source_locator_ids"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks source locators",
            "pre_medical_output_validation",
        )
    # Item set/order: the assessment's item_record_ids must exactly
    # match the typed AssessmentItemRecords for that assessment.
    expected_items = list(assessment.get("item_record_ids", []))
    actual_items = [
        item.get("item_record_id")
        for item in ctx.fixture.records.get("assessment_items", [])
        if item.get("assessment_id") == aid
    ]
    if expected_items != actual_items:
        raise D06ContractViolationError(
            f"accepted assessment {aid} item set/order mismatch",
            "pre_medical_output_validation",
        )
    item_values = ctx.fixture.records.get("item_values") or {}
    for item in ctx.fixture.records.get("assessment_items", []):
        if item.get("assessment_id") == aid:
            if not isinstance(item, (dict, Mapping)) or not item.get(
                "item_record_id"
            ):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item record malformed",
                    "pre_medical_output_validation",
                )
            verify_content_hash(item, f"assessment item {aid}")
            if not item.get("source_locator_ids"):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item lacks source locators",
                    "pre_medical_output_validation",
                )
            # Item value/content authority: raw and normalized values
            # must agree with the typed item-values mapping keyed by
            # the item definition identity.
            definition_id = str(item.get("item_definition_id", ""))
            suffix = definition_id.rsplit("-", 1)[-1] if definition_id else ""
            expected_value = item_values.get(suffix)
            if (
                item.get("raw_value") != item.get("normalized_value")
                or item.get("raw_value") != expected_value
            ):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item "
                    f"{item.get('item_record_id')} value not authenticated "
                    "by the typed item-values authority",
                    "pre_medical_output_validation",
                )
