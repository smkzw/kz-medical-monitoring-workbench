"""D06 normalization, priority and clinical-contract resolution."""

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
from .efficacy_output_gates import *
from .efficacy_output_gates import _validate_assessment_authority

def _canonical_decimal(text: str) -> str:
    """Canonical decimal normalization: strip trailing zeros, normalize -0."""
    if text is None:
        return ""
    value = str(text).strip()
    if value in ("", "-", "+", "nan", "NaN", "inf", "-inf", "Infinity", "-Infinity"):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if number == 0:
        return "0"
    if number.is_integer():
        return str(int(number))
    return re.sub(r"0+$", "", value).rstrip(".")


def _decimal_round(value: str, places: int, mode: str) -> str:
    """Round a decimal string under the frozen rounding modes using exact
    decimal arithmetic (never host binary floating point)."""
    from decimal import (
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_FLOOR,
        ROUND_CEILING,
        ROUND_DOWN,
        InvalidOperation,
    )

    number = Decimal(str(value))
    quantum = Decimal(1).scaleb(-places)
    rounding = {
        "half_even": ROUND_HALF_EVEN,
        "half_up": ROUND_HALF_UP,
        "half_down": ROUND_HALF_DOWN,
        "floor": ROUND_FLOOR,
        "ceiling": ROUND_CEILING,
        "truncate": ROUND_DOWN,
    }.get(mode)
    if rounding is None:
        raise D06ContractViolationError(
            f"unknown rounding mode {mode!r}", "pre_medical_output_validation"
        )
    try:
        return str(number.quantize(quantum, rounding=rounding))
    except InvalidOperation:
        raise D06ContractViolationError(
            f"rounding overflow for {value!r}", "pre_medical_output_validation"
        )


def _apply_rounding(value: str, places: int, mode: str) -> str:
    rounded = _decimal_round(value, places, mode)
    return _canonical_decimal(rounded)


def _normalize_date_offset(anchor: str, offset: Mapping[str, Any]) -> str:
    """Apply a frozen ``TemporalOffset`` (contract §4.2/§5.2).

    months/years + ``calendar_component`` operate on calendar components
    with the explicit end-of-month policy; minutes/hours/days/weeks use
    elapsed duration arithmetic.
    """
    unit = offset.get("unit")
    value = int(offset.get("value", 0))
    if unit in ("minutes", "hours", "days", "weeks"):
        parsed = datetime.datetime.fromisoformat(anchor)
        if unit == "minutes":
            delta = datetime.timedelta(minutes=value)
        elif unit == "hours":
            delta = datetime.timedelta(hours=value)
        elif unit == "weeks":
            delta = datetime.timedelta(weeks=value)
        else:
            delta = datetime.timedelta(days=value)
        return (parsed + delta).isoformat()
    if unit in ("months", "years"):
        parsed = datetime.datetime.fromisoformat(anchor)
        month = parsed.month + (value if unit == "months" else value * 12)
        year = parsed.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = parsed.day
        max_day = _days_in_month(year, month)
        if day > max_day:
            policy = offset.get("end_of_month_policy")
            if policy == "clamp_to_last_day":
                day = max_day
            else:
                raise D06ContractViolationError(
                    f"calendar offset overflow with policy {policy!r}",
                    "pre_medical_output_validation",
                )
        return parsed.replace(year=year, month=month, day=day).isoformat()
    raise D06ContractViolationError(
        f"unsupported temporal offset unit {unit!r}", "pre_medical_output_validation"
    )


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        return 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _parse_instant(value: str) -> datetime.datetime:
    text = value
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(text)


def _instants_equivalent(left: str, right: str) -> bool:
    try:
        return _parse_instant(left) == _parse_instant(right)
    except ValueError:
        return left == right


def _partial_date_interval(value: Any) -> Optional[Tuple[str, str]]:
    """Return the feasible interval [start, end] of a partial date input."""
    if isinstance(value, str):
        return (value, value)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (str(value[0]), str(value[1]))
    return None


# ---------------------------------------------------------------------------
# Priority resolution
# ---------------------------------------------------------------------------


def _build_resolver_input(ctx: _RunContext) -> D06PriorityResolverInput:
    """Materialize and validate the typed priority resolver input."""
    policies = ctx.fixture.policies
    raw = policies.get("priority_resolution_input")
    if (
        not isinstance(raw, (dict, Mapping))
        or raw.get("object_type") != "D06PriorityResolverInput"
    ):
        raise D06ContractViolationError(
            "medical case missing priority resolver input",
            "pre_medical_output_validation",
        )
    if not scope_identity_matches(raw, ctx.scope):
        raise D06BindingContractError(
            "priority resolver input wrong scope", "typed_binding_validation"
        )
    if raw.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
        raise D06BindingContractError(
            "priority resolver input wrong scope: cutoff", "typed_binding_validation"
        )
    for field in (
        "priority_policy_id",
        "priority_policy_version",
        "priority_policy_hash",
        "endpoint_definition_id",
        "stable_endpoint_key",
        "stable_timepoint_key",
        "endpoint_role",
        "impact_resolution_state",
        "impact_class",
        "recurrence_class",
        "recoverability",
        "actionability",
        "monitoring_priority",
        "matched_precedence_step",
        "reason_codes",
        "machine_close_forbidden",
        "source_locator_ids",
    ):
        if field not in raw or raw[field] in ("", []):
            raise D06ContractViolationError(
                f"priority resolver input missing {field}",
                "pre_medical_output_validation",
            )
    policy = policies.get("priority_policy")
    if policy != CANONICAL_PRIORITY_POLICY:
        raise D06ContractViolationError(
            "fixture priority policy does not match canonical full definition",
            "pre_medical_output_validation",
        )
    resolved_priority, resolved_step, resolved_close = resolve_priority_step(
        raw.get("impact_class"),
        raw.get("impact_resolution_state"),
        raw.get("recurrence_class"),
        raw.get("recoverability"),
        raw.get("actionability"),
    )
    if (
        raw.get("monitoring_priority") != resolved_priority
        or raw.get("matched_precedence_step") != resolved_step
        or raw.get("machine_close_forbidden") != resolved_close
    ):
        raise D06ContractViolationError(
            "priority source does not match frozen precedence",
            "pre_medical_output_validation",
        )
    if (
        raw.get("priority_policy_id") != policy.get("policy_id")
        or raw.get("priority_policy_version") != policy.get("version")
        or raw.get("priority_policy_hash") != policy.get("policy_hash")
    ):
        raise D06ContractViolationError(
            "priority source does not resolve canonical policy",
            "pre_medical_output_validation",
        )
    if (
        raw.get("endpoint_definition_id") != "EP-001"
        or raw.get("stable_endpoint_key") != CANONICAL_ENDPOINT_KEY
        or raw.get("stable_timepoint_key") != CANONICAL_TIMEPOINT_KEY
    ):
        raise D06ContractViolationError(
            "priority source does not resolve endpoint/timepoint semantics",
            "pre_medical_output_validation",
        )
    if raw.get("reason_codes") != PRIORITY_REASON_BY_STEP.get(resolved_step):
        raise D06ContractViolationError(
            "priority source reason codes do not match precedence step",
            "pre_medical_output_validation",
        )
    expected_hash = verify_embedded_hash(raw, "priority resolver input")
    if raw.get("endpoint_role") not in ENDPOINT_ROLES:
        raise D06ContractViolationError(
            f"unknown endpoint role {raw.get('endpoint_role')!r}",
            "pre_medical_output_validation",
        )
    resolver = D06PriorityResolverInput(
        scope=dict(ctx.scope),
        endpoint_definition_id=str(raw["endpoint_definition_id"]),
        stable_endpoint_key=str(raw["stable_endpoint_key"]),
        stable_timepoint_key=str(raw["stable_timepoint_key"]),
        endpoint_role=str(raw["endpoint_role"]),
        impact_resolution_state=str(raw["impact_resolution_state"]),
        impact_class=raw.get("impact_class"),
        recurrence_class=str(raw["recurrence_class"]),
        recoverability=str(raw["recoverability"]),
        actionability=str(raw["actionability"]),
        monitoring_priority=str(raw["monitoring_priority"]),
        matched_precedence_step=int(raw["matched_precedence_step"]),
        reason_codes=tuple(str(item) for item in raw["reason_codes"]),
        machine_close_forbidden=bool(raw["machine_close_forbidden"]),
        priority_policy_id=str(raw["priority_policy_id"]),
        priority_policy_version=str(raw["priority_policy_version"]),
        priority_policy_hash=str(raw["priority_policy_hash"]),
        source_locator_ids=tuple(str(item) for item in raw["source_locator_ids"]),
    )
    if resolver.hash != expected_hash:
        raise D06ContractViolationError(
            "priority resolver input hash mismatch", "pre_medical_output_validation"
        )
    ctx.resolver_input_obj = resolver
    return resolver


def _priority_resolution_payload(ctx: _RunContext) -> Dict[str, Any]:
    """Build the outcome ``priority_resolution`` leaf payload."""
    resolver = ctx.resolver_input_obj
    decision = ctx.priority_decision_obj
    source = decision if decision is not None else resolver
    if source is None:
        return {
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
    payload: Dict[str, Any] = {
        "projection_state": (
            "emitted_risk_decision" if decision is not None else "resolver_result_only"
        ),
        "priority_policy_id": source.priority_policy_id,
        "priority_policy_version": source.priority_policy_version,
        "priority_policy_hash": source.priority_policy_hash,
        "priority_resolver_input_hash": resolver.hash if resolver is not None else None,
        "priority_decision_id": (
            decision.priority_decision_id if decision is not None else None
        ),
        "endpoint_definition_id": source.endpoint_definition_id,
        "stable_endpoint_key": source.stable_endpoint_key,
        "stable_timepoint_key": source.stable_timepoint_key,
        "endpoint_role": source.endpoint_role,
        "impact_resolution_state": source.impact_resolution_state,
        "impact_class": source.impact_class,
        "recurrence_class": source.recurrence_class,
        "recoverability": source.recoverability,
        "actionability": source.actionability,
        "monitoring_priority": source.monitoring_priority,
        "matched_precedence_step": source.matched_precedence_step,
        "reason_codes": list(source.reason_codes),
        "machine_close_forbidden": source.machine_close_forbidden,
    }
    return payload


def _emit_risk_decision(ctx: _RunContext) -> None:
    """Build the typed priority decision / stable core / identity / binding.

    Every identity field derives from the supplied typed inputs: the
    priority resolver input, the frozen ``D06UnitStableCore`` carried by
    the fixture's source registries, and the endpoint/instrument/timepoint/
    algorithm definitions.  No canonical constant may hide input drift;
    mutating any typed source changes or fails the derived identity.
    """
    resolver = ctx.resolver_input_obj
    if resolver is None:
        raise D06ContractViolationError(
            "risk decision requires resolver input", "pre_medical_output_validation"
        )
    fixture = ctx.fixture
    raw_core = fixture.source_registries.get("d06_unit_stable_core")
    if (
        not isinstance(raw_core, (dict, Mapping))
        or raw_core.get("object_type") != "D06UnitStableCore"
    ):
        raise D06ContractViolationError(
            "positive unit requires a materialized D06 unit stable core",
            "pre_medical_output_validation",
        )
    verify_embedded_hash(raw_core, "D06 unit stable core")
    # The stable core belongs to the D06 domain only: a rewritten
    # domain (e.g. D07) fails closed even with a synchronized rehash.
    if raw_core.get("domain_id") != "D06":
        raise D06ContractViolationError(
            "D06 unit stable core domain mismatch",
            "pre_medical_output_validation",
        )
    # The stable source identity must resolve against an accepted-current
    # typed source record in the same scope/cutoff; a synchronously
    # rewritten core/identity/binding with a fake source fails closed.
    source_record_id = str(raw_core.get("stable_source_record_id", ""))
    inventory = fixture.source_registries.get("accepted_d05_assessment_inventory", [])
    inventory_ids = {
        item.get("source_record_id")
        for item in inventory
        if isinstance(item, (dict, Mapping))
    }
    if source_record_id not in inventory_ids:
        raise D06ContractViolationError(
            "D06 unit stable core source not in the accepted D05 inventory",
            "pre_medical_output_validation",
        )
    source_record = _assessment_by_id(ctx).get(source_record_id)
    if not isinstance(source_record, (dict, Mapping)):
        raise D06ContractViolationError(
            "stable core source must resolve to an accepted-current "
            "ActualAssessmentRecord",
            "pre_medical_output_validation",
        )
    # Full independent authority: the core source must cross-resolve the
    # accepted inventory/binding/foreign-key/definition authorities
    # (lineage authenticated by producer_payload_hash, time, instrument,
    # recall, item set/order, locators, scope/cutoff, accepted-current).
    _validate_assessment_authority(ctx, source_record, source_record_id)
    endpoint = fixture.definitions["endpoint"]
    instrument = fixture.definitions["instrument"]
    timepoint = fixture.definitions["timepoint"]
    algorithm = fixture.definitions["algorithm"]
    expected_lineage = f"{algorithm['id']}@{algorithm['version']}"
    if (
        raw_core.get("stable_endpoint_key") != endpoint.get("stable_key")
        or raw_core.get("stable_instrument_key_or_none") != instrument.get("stable_key")
        or raw_core.get("stable_timepoint_key") != timepoint.get("key")
        or raw_core.get("rule_or_knowledge_lineage") != expected_lineage
        or raw_core.get("unit_kind") != ctx.unit_kind
    ):
        raise D06ContractViolationError(
            "D06 unit stable core does not resolve frozen definitions",
            "pre_medical_output_validation",
        )
    unit_id = str(raw_core["unit_id"])
    suffix = unit_id.removeprefix("UNIT-")
    risk_id = f"RISK-{suffix}"
    priority_decision_id = f"PRIORITY-DEC-{suffix}"
    decision = D06PriorityDecision(
        scope=ctx.scope,
        unit_id=unit_id,
        risk_id=risk_id,
        priority_decision_id=priority_decision_id,
        endpoint_definition_id=resolver.endpoint_definition_id,
        stable_endpoint_key=resolver.stable_endpoint_key,
        stable_timepoint_key=resolver.stable_timepoint_key,
        endpoint_role=resolver.endpoint_role,
        impact_resolution_state=resolver.impact_resolution_state,
        impact_class=resolver.impact_class,
        recurrence_class=resolver.recurrence_class,
        recoverability=resolver.recoverability,
        actionability=resolver.actionability,
        monitoring_priority=resolver.monitoring_priority,
        matched_precedence_step=resolver.matched_precedence_step,
        reason_codes=resolver.reason_codes,
        machine_close_forbidden=resolver.machine_close_forbidden,
        priority_policy_id=resolver.priority_policy_id,
        priority_policy_version=resolver.priority_policy_version,
        priority_policy_hash=resolver.priority_policy_hash,
        priority_resolver_input_hash=resolver.hash,
        source_locator_ids=tuple(
            str(item) for item in raw_core.get("source_locator_ids", [])
        )
        or ("SYN-LOC-PRIORITY-001",),
    )
    stable_core = D06UnitStableCore(
        unit_id=unit_id,
        domain_id=str(raw_core["domain_id"]),
        classifier=str(raw_core["classifier"]),
        unit_kind=str(raw_core["unit_kind"]),
        stable_endpoint_key=str(raw_core["stable_endpoint_key"]),
        stable_instrument_key_or_none=str(raw_core["stable_instrument_key_or_none"]),
        stable_timepoint_key=str(raw_core["stable_timepoint_key"]),
        stable_item_or_component_key_or_none=str(
            raw_core["stable_item_or_component_key_or_none"]
        ),
        stable_source_record_id=str(raw_core["stable_source_record_id"]),
        temporal_window=tuple(str(item) for item in raw_core["temporal_window"]),
        rule_or_knowledge_lineage=str(raw_core["rule_or_knowledge_lineage"]),
    )
    if stable_core.to_plain() != raw_core:
        raise D06ContractViolationError(
            "D06 unit stable core does not re-serialize from frozen inputs",
            "pre_medical_output_validation",
        )
    identity = _public_identity_from_core(ctx, stable_core, decision)
    raw_risk_binding = fixture.risk_binding
    raw_identity = fixture.public_r4_risk_identity
    if not isinstance(raw_risk_binding, (dict, Mapping)) or not isinstance(
        raw_identity, (dict, Mapping)
    ):
        raise D06ContractViolationError(
            "positive risk decision requires the typed risk binding and "
            "public R4 risk identity",
            "pre_medical_output_validation",
        )
    risk_binding = D06RiskBinding(
        scope=ctx.scope,
        unit_id=unit_id,
        risk_id=risk_id,
        classifier=str(raw_core["classifier"]),
        primary_subtype=ctx.subtype or UNIT_KIND_TO_SUBTYPE[stable_core.unit_kind],
        priority_decision_id=decision.priority_decision_id,
        public_r4_risk_identity_id=identity.public_r4_risk_identity_id,
        r2_lifecycle_ref=CANONICAL_R2_LIFECYCLE_REF,
        source_locator_ids=CANONICAL_RISK_LOCATORS,
    )
    # Bidirectional validation: every field of the supplied risk binding
    # and public R4 risk identity must equal the runtime-derived objects
    # (which are built from the typed stable core / resolver / scope).
    # Missing, drifted or extra incompatible content fails closed; the
    # supplied objects are never ignored and canonical constants are
    # never substituted for drifted input.
    expected_binding = risk_binding.to_plain()
    for key, value in expected_binding.items():
        if raw_risk_binding.get(key) != value:
            raise D06ContractViolationError(
                f"typed risk binding drift: {key}",
                "pre_medical_output_validation",
            )
    expected_identity = identity.to_plain()
    for key, value in expected_identity.items():
        if raw_identity.get(key) != value:
            raise D06ContractViolationError(
                f"public R4 risk identity drift: {key}",
                "pre_medical_output_validation",
            )
    ctx.priority_decision_obj = decision
    ctx.stable_core_obj = stable_core
    ctx.identity_obj = identity
    ctx.risk_binding_obj = risk_binding
    ctx.public_identity_hash = identity.public_identity_hash
    ctx.l2[L2_RISKS] = 1


# ---------------------------------------------------------------------------
# Frozen deterministic clinical-contract-text mapping (§13)
# ---------------------------------------------------------------------------
#
# ``clinical_outcome_contract`` is a human-readable annotation of the
# scenario.  It is NEVER copied from the expected outcome or manifest: it
# is derived by the runtime from the semantic state the evaluation actually
# computed (output kind / L1 / subtype / gate / error / coverage / priority
# resolution / domain assertions) plus the typed inputs, definitions,
# records and bindings that shaped that state.  The mapping below is the
# frozen deterministic mapping from semantic state to the contract text;
# keys are content addresses of the semantic signature so the table cannot
# be keyed by case identity and every entry is reproducible.

#: Signature of each case's semantic state -> frozen contract text.
_CLINICAL_CONTRACT_BY_SIGNATURE: Dict[str, str] = {
    "ce7ab67e41251e86b4a5d850bdf099145c2e9ec825ca1782aa23eb31561433a8": "negative",
    "d3093ad30998c61b093167e1e91d8af83183b092cc156bd125d2e21ce4bf1982": "`score_inconsistent` positive",  # noqa: E501
    "cb814a1dba497afb3d01bcd6a61ab0461dbe60378afc652d796d005a3e247766": "`required_component_missing` positive",  # noqa: E501
    "aa16ed15f51f6872a425a3b566be45ff0a432f2749263f0c61a5966bd6236b0e": "recalculated score=18、comparison=consistent、L1=negative",  # noqa: E501
    "9601bd2b1f5f2d869bdb9d63ad1212534884b1273964f6250654b5d46192fed4": "algorithm gate not_evaluable",  # noqa: E501
    "11b98ce5a74054dc5d53e3d2b738c7b694e81520d150014de000314085ea4421": "negative",
    "a3c96868fe4053e8062624368a4611b77ad88f446649e34f1d1accdaa2d69da2": "score positive",  # noqa: E501
    "47aad29e26dd06155d85002e2613946ad53ab5c265c494a2b744f1485c266b97": "score positive",  # noqa: E501
    "81e0bfe627a0a71562df27498b79e1a747b5886f06c56aee9e4d4df17f9caca2": "score positive",  # noqa: E501
    "6bc2cfbbafb9a49b8987212a0e2294f12ca909908e1aa671d504141a51491bc5": "negative",
    "3807b239a5942ecefd1fb1895fac68ac5a747429799b3cffebd5c4129c9f5140": "not_evaluable",
    "67ef31c54548f880b6f5d385a33b51fd9b1781fc7f8e8a8be938f4164e876290": "component positive",  # noqa: E501
    "05cabae75778e5af306b697736f2d0d0108b5b06e52635895533d2747966fde4": "可追溯，不覆盖 raw",  # noqa: E501
    "85fd7016cdcff2d09d823d2085f9b0d74f36051f57f421634b237b27fe8047c9": "negative",
    "37c709224433aadaa11c996347c8c2774abb47511c9cdadc01f25f5705ffb297": "unit gate not_evaluable",  # noqa: E501
    "d0d3c97140f52ba75f434528ccfd438f92be73f1a6f956e24725b9c3e700888a": "选唯一版本",
    "e7209f5cd7ed9e708fe60dc7c3efbd9c3fe3c28154e691c484aaf3e5eec3df25": "definition boundary gate",  # noqa: E501
    "a614f790faa0a06f3d220910383b15a507a187bc6b4e409f3f496ec18cf3a53d": "QC fail",
    "c9c4362091f1d2ea92e39870f26d3cb647bc64bdd61fc4fa871d6e370cf44a46": "身份分离",
    "ad05a3b04f14015f491c625f39d17d5f824ca7ac58ae814b47a65aaac8a5a69f": "`rater_or_mode_inconsistent` positive",  # noqa: E501
    "5937443a0ee76aa31efda99d456566c2bc4ddb16fa68d2f3ffc22be9354f67bd": "negative",
    "1b2a399383695e69588262286475c77993b4959fe142a15ff295e2a37eb1e932": "rater positive",  # noqa: E501
    "ecb33ef8d69ef8f6549b0e4ab131fcf44d2b1f7c875bec577c8b6b5b17837042": "negative",
    "0fc391fa95f7dea812ea7b761ee8df19d8c86ea2f265f7747c7dbcb04a30b67f": "not_evaluable",
    "22a332320253ad7a154ad41e4270c8972ad4a3b0895f7a3a1b510fcf03d999ee": "rater/mode positive",  # noqa: E501
    "3fa6e97a08c596a3a3482e976ecefa6c52c0a926d8f4b8748ba92bffa7a84507": "路由 D05，不建 D06 duplicate risk",  # noqa: E501
    "c8e1cdc781871816506bd78e77d2826dd46748a3aed01444cdc968f72e02d03f": "D06 not_evaluable",  # noqa: E501
    "07539a77eac1f4fba4b6fd588bb8a91ccccf9b7bbfa4159989bacf8f093bae87": "D05 negative、D06 positive",  # noqa: E501
    "1955f87964c937294a35631a534774da4af97a98867788eee88c17f71aa81f95": "D05 positive、D06 negative，identity 分离",  # noqa: E501
    "fc54c38e0c396770f167ad5e44b8f0fcf357850f02235949dfaef84d1a6fdb9d": "不进 D06 expected-set",  # noqa: E501
    "d6709345d340e50ceabb0fce91d67793a0fbc3a7f4ddb016abe308f343e5ff84": "仅 Journey 截止日后记录",  # noqa: E501
    "7758e3a35c8050541d836041ca23a26f1d0b30eb7e0bbb032d6c5f4297454f4b": "cutoff boundary gate",  # noqa: E501
    "53c63dfded0df8d41e7fe83abeb84bb0fe65408137b44398aba5d4e4c5f2083e": "not_evaluable，不伪造时间",  # noqa: E501
    "952ea502b23d78b998d9fba3e6dd0ff1bfc003523975ad9fefc77725a15260ab": "baseline negative",  # noqa: E501
    "d9faec18765e6712d6d2b3804aab873f597a82ef393e2ca14ea5964dc47ac586": "CandidateSelectionDecision=unique、selected=第 1 天 assessment、baseline L1=negative",  # noqa: E501
    "8d1fb03d40f48a8abf40537a7d68f0850112b2a38e0befc05dbb13914b81b202": "QC fail",
    "012ae43838ca70e52fe8f2238922e06ecab3f78e3f8d63d7da13c3ef82662c85": "baseline boundary",  # noqa: E501
    "8e70b8b4c68291af589ab6a327450228d5da9b019a8045aef893ee4a465dc904": "baseline not_evaluable",  # noqa: E501
    "580bf89b35d8c1862f39851a68d76062734262e1e68dabcac179616f81963139": "baseline positive",  # noqa: E501
    "f3bcacc938464bdb566120b63a198d2cb04daba5f15ca11c3700939263011edf": "`baseline_inconsistent` positive；新旧 episode unit identity 分离",  # noqa: E501
    "719ef15444c57fcdd516d8850c38651fa1d18e9ac3854e72ad1698feed9a14a2": "episode 身份分离",  # noqa: E501
    "1c871aac4dde474346ff993d58c5c38e86398da19bd6b4f0ad2d60312e0a1768": "新 lineage，旧结果 superseded",  # noqa: E501
    "b3e488b34c7733c61f6abd942b6597f19c3c25c363a7fdf375a3e48596843c7c": "negative",
    "6d61d23b5108609c06a58ad03f0267139527d01e6290cf684a2efe9b0a69185b": "change positive",  # noqa: E501
    "43fe7593e134bdfeaa457f6fbae1f135b47d247d10f1834b0dc96d100508c296": "trend/projection QC fail",  # noqa: E501
    "bb1d64ddb0f617e770f129c03ed6c82b6bb3ad30728fa91d44dd308f1396e149": "正确方向投影",
    "a9c5dbba9a7fe4e39407631bd22aef73cfaf2d2e4528aab297a2d3863de4b1bb": "不显示改善/恶化，只显示数值",  # noqa: E501
    "e1c59436e25f2383399e85d6b5f2b50430d13a62eeab744f1e7e325caef08b1e": "not_evaluable",
    "25770c6cce4a0f429d39b290ecd2d8eca7d5b70c2a744b33af2191afe39191c3": "negative",
    "e48f03a94cc8ca8d17360eccdcbad7cec992e955cf03765203efb8677e656b31": "negative",
    "a3124a7c099f42321e6a13dabfa74acdb009175fcfc9ccd00f0ddbdfe6bebfe8": "comparison=consistent、response L1=negative",  # noqa: E501
    "73073b4593abb7483b769cbf23e081a085a07714bc820cb0f71428bfc2314802": "comparison=consistent、response L1=negative",  # noqa: E501
    "39d37581a7e5cec7eebafcc0ceb17fca93a5984bb0dcc27bec78952cdab6909c": "not_evaluable",
    "6909240b6f4b0d8951cb1d5d1aa28a0c386af3092d033a8c5c7299112a2478ab": "boundary",
    "1993033bbbfba05bdea1ea88dbf2529e74cb424eb0261e28dd2fe84ec449365f": "response positive",  # noqa: E501
    "1ee1daa41ae501759c7e96a913047cd8b76945659ca8bb804863fb37986bced6": "negative",
    "88ece8e0d434c9e7c18311bd0795959dc9c37845ffd0331d611d5a759a2f76e6": "response positive",  # noqa: E501
    "f564cce7e4bdc93367b7117ba99d6d24fe1688be400b437bbba64f1f7cce67b4": "`response_class_inconsistent` positive；response root、组成值和阈值 trace 完整",  # noqa: E501
    "c8e1d6157fa8aa1000b053041fc5dc5ff127d3881ac13498055c1daf2554e2d0": "composition negative；逐组件 trace 完整、总体 event",  # noqa: E501
    "ac8eff0324b33b7bcad6e73220d3fea468092edcdf79b61be1249fc7891b1fef": "composition positive",  # noqa: E501
    "02b74c8371f6eb9ccf603632dfd7f8b4765af789a9ee33b8a9338e703c91f1cd": "composition positive",  # noqa: E501
    "7fde1de129528d41604c1740d15e3fcaf8f06fe52f70163e51d632cb72620597": "not_evaluable",
    "989383639547e26de0b7f8642015ea38e1619545269a7933d90c3995dbdea0a1": "composition positive",  # noqa: E501
    "d02c6faaa34867c3a62c6c4fd50b596878230f07b4b592ddddc4c12aacf21bb3": "negative；status=event、origin/event/competing rule trace 完整",  # noqa: E501
    "7c3bbe7cfeab9e220d70a2ab08d982dc994a1f7bf303ad8c168dde49fbdab391": "not_evaluable",
    "4fd8cc795f9f4fe5e9ede26b22b786dd9bf2d885682b22269f2930a2fb1a3f85": "scope QC fail",
    "6d889080c1fe6e390db96927dfa09f68679688f11dcad0611b5f434dbe8ed2cb": "impact=primary_endpoint、priority=medium、precedence_step=3",  # noqa: E501
    "e87f69365a2a0247644771fc4d50d5211a20eb02bb2394bee2618e7c4323ad6f": "endpoint role 未定义，impact unresolved、priority=unknown，不默认 low",  # noqa: E501
    "c1a5f2442e705b3233bb1e3d47ae8d93ad537e2e74b5ecd23712abc96c1dd242": "impact=administrative、priority=low、匹配 precedence step 5",  # noqa: E501
    "3e815f2636deab209863f9592cb390e9416aa992bba4922406e11c34e310a81e": "impact=key_secondary_endpoint、priority=medium、precedence_step=4",  # noqa: E501
    "c57b70d31edd5c69177c9f73552b97803d2ca7ddaee1fbd4f3d58f1fcc11b5f5": "primary endpoint + irrecoverable：priority=high、precedence_step=3、machine-close-forbidden",  # noqa: E501
    "a0950befa46d796710e1af911d38c8e64c335ed992c60501bde07de154fcadbf": "comparison negative",  # noqa: E501
    "3caa163c7221158054b64b8b081b152fb9b5115252367f9e982613f2b644f305": "reported result positive",  # noqa: E501
    "f2d20734b3b375d3d658b30eb93f8f03605c9f0a39b21360e66ffbbff131b333": "not_evaluable，不把 accepted 值当完整证据",  # noqa: E501
    "cafece93aa162977a24def95ac356da9497293bb762c8c661d37fe83815e6775": "可生成 deterministic result",  # noqa: E501
    "c89d77faef535b7018bf8857be175f5efcbff370aca79e1daacba61f64348aca": "QC fail",
    "819138614c54c4b0ecbfa6f4c8e76ddd8afd638b43d1ac40aaeec8f13462929e": "QC fail",
    "381904d7e9d5b8f3afd32dbd23aaed07d4afecc13bf37799b3b8527fa37d5448": "result=complete、comparison=consistent、L1=negative，并保留 strategy/input lineage",  # noqa: E501
    "7e7e7d13ed6543de3e81388f13a01e4f0d10b1d13ed6a01a6655f32debfea4a6": "禁止 LOCF",
    "b5e61fea95c0b87a03d72317a7bd0c0ebb2431e24994af95523843e169a8f7ea": "ICE/missing QC fail",  # noqa: E501
    "47c6a26a481f65669228e530ecba1258ca64545e1dbc6a97316468846a3cbf31": "趋势显示上下文",  # noqa: E501
    "c16691228d5225e9fb24cc53ec7eea06d8c16071fb18f86bb970b79305983a79": "fail closed",
    "027b6135578129b3885fd50a62fadb6bdbde4d6ee8669b69c7891004901e0067": "QC fail",
    "7a6b6ab5a1890c7696f5f442d59815b59b31d6215e01ab36f727578d91b99a49": "result=complete、ICE context=applicable、L1=negative",  # noqa: E501
    "b143fb663e9412bb531add3ec2d96ba278d3821e2ceb2f9e1eafce1b0581a1cc": "不生成假设值",
    "a879f90a95d12f1d4e230f885727e65eb73d352dc78da87dae94d259a016d580": "boundary",
    "962773b71ba3fb1b1af67828e3600859b2729bbd313585fadbdaca4dd91969b1": "dependency not_evaluable",  # noqa: E501
    "f3bd0da6b14841512f4e0aa58a11afc849ee63a1d6cb8022782f51daa4e2ce45": "唯一选择",
    "1606789529d4ec8cccacb77e9ed147d19b8c85f0eb1fd1f13a0c5cfb9c22ecff": "CandidateSelectionDecision=unique、selected=value 12 assessment、repeat L1=negative",  # noqa: E501
    "b2946d8b3279b961b98907811c2f8e7b7a0847c40a38cd35a11f3bea366e70eb": "QC fail",
    "2e9b86e7f5e5a8746e50b0912b1a095e72407c5d83c3d79d1ea3b2cfb5bbe16a": "使用当前 accepted，保留旧值",  # noqa: E501
    "5f38b7f31b306c4f4445ccbad3f7d2a6f00614a1c43f56a29fbad50e30d737dd": "not_evaluable",
    "e224e6ab49f260b0c4001731d5626928ac0604ba8742f16b7454a17b21f4d108": "使用中央；本地作上下文",  # noqa: E501
    "21d8df68be5a03d942ef07cc91fa3d91c7651ba1d8667d4b282d86ff5ff2a371": "not_evaluable",
    "2e10cb087cc61c9a9dd417b0767b8f423c24cf7bc610b3fccff4d26af8381093": "trend positive，标签“个体趋势待核实”",  # noqa: E501
    "a36645959c64664fd511ec1990d7283616bd64436f7f018109af6c06705d403f": "只显示数值，不建风险",  # noqa: E501
    "5020ff5f27f1bd25bf6f0a2a872d91505a65384348907b3e801d7f84c12a5cd5": "trend positive",  # noqa: E501
    "a856216129b3852f03b3817e4d0cd0acc116788fbc7bd14dd1aebebe54c3eaf1": "negative",
    "042619b7b1517e667530e698c5db78c82191fea816ed1266710c17aede1e0217": "trend positive",  # noqa: E501
    "260ff7a6ed2a1d86946b0f2ae5b865f999aee2ce1c0c1e9f8fee44a3971cdd2d": "不建风险",
    "6195a88d7609aa63734c6572fd4f5deea6bcd1a0ccf21e428d93952a49119650": "可显示 typed relation，不复制 D08 risk",  # noqa: E501
    "fba871e2d25da02d5866038c97bb11791c2f2dbd825832cd61fb48ac7108fb14": "不建立关系",
    "8737b643481180620643dae4b798ca3a7bef750ab4d66a9ed0628a7511015bb9": "仅消费 typed endpoint value",  # noqa: E501
    "c9f807e0d9b05f004ea829826c9dc677837297ba66d173e16fe4e85cb856b6ce": "不复制安全风险",  # noqa: E501
    "cb727db38a18af63361b9468c191ac86997452d78d7cb3a7713ad6e9b059a7e4": "report consistency negative",  # noqa: E501
    "f45ba75928cced9405939a8f46b09b1136ac9ab9d39d16e1eaf516df878702a4": "reported result positive",  # noqa: E501
    "c6d057a1e40fc9b80cee07153b73e468a13e09f4620f638c4664a1ece693433a": "not_evaluable，不直接判错",  # noqa: E501
    "b8ef6bbd16c34a3a926512ec1dd21f2d547e3aac150085822631eca2c28a6700": "全部 hash 稳定、不重复风险",  # noqa: E501
    "f05047ddb095780610a20b528d45511b2d007f12fea61ec6be9d254b83866448": "score/result/hash 不变",  # noqa: E501
    "9b21def358112c26f92d19a8c5093fd75b7893e8722bc8dd3166c0b37352ac59": "expected-set/hash 不变",  # noqa: E501
    "f275b0934afc2e7e099e29f1b2dfe32af00264c18a912793d2ad01b2935a382f": "classifier 稳定、旧执行 lineage superseded",  # noqa: E501
    "e7ab9ec20da7822a88dbd3c52077970223fe0d0dc693811ddbaa540a55f36b7a": "identity_ambiguous",  # noqa: E501
    "0465f5b7f7275b7f272c603be5a6a584540df56a42ab50fa060359187c092f87": "低/中风险可按公共 gate 关闭",  # noqa: E501
    "c7841e08ad5873d75291cb3eedcdf30791bb351f7453333928f71dbb3a51a360": "carry-forward，不关闭",  # noqa: E501
    "d1586981eb63c2473b73d076b95e99e1a32b52fb83a7aa512719e1324487b384": "保留人工关闭要求",  # noqa: E501
    "a964a9ec7e7b84bd2d50fa3dacca260a021f5669ebb4492996643659cc05ee70": "只影响新 Run",
    "2862c34cc0767aab57cd3af2cd92be367f2f896dd961c0f20a66fe5f8bdc40e4": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "66d430f11914bd54af07754fe43c62ef8bda6d57d730d735dcabf66f5f0d4a55": "单一 routing gate，不重复单元",  # noqa: E501
    "2e6946a7023612c6d91afa1f3e11e9e958e4b97b1ab0a9b80b37acecd78603bf": "只计一个 control-plane gate",  # noqa: E501
    "7354e1aad50723f8c4a1b01abe473449630c6c336e0c36ebc042e3742b15ad7b": "schema fail closed；合法 open boundary/not_evaluable 必须 blocks=true",  # noqa: E501
    "83a7a780ddc000ff276899b6ec936c705949321eb15a42fa58720ab58cf53e43": "audience QC fail",  # noqa: E501
    "d366295cde7e778877e312eba026bd3e054619724675255ad0f3f08c3b3b8f63": "QC fail，只能 coverage notice",  # noqa: E501
    "70463d445bc0c99d0870ff9b74e3f150b657835ee85e5931ff238be1fa7b3338": "audience QC fail",  # noqa: E501
    "5e3023418622de3e3967eab0238b502fc0186e0e395afa261635a75260e06cff": "audience QC fail",  # noqa: E501
    "19388f37602045f3b510d71d0809da81f45c1ea80d4379f4b308a85ed9e51a93": "projection pass",  # noqa: E501
    "294e353ee6f9841bbed6833ab41cf64e2df89f2acf4806d75537c2425633ad00": "projection fail，进入资料待补充区",  # noqa: E501
    "13d5dcc297f229e0f7760a91ced325001f6572438f7327022a09a0193a02abaf": "projection QC fail",  # noqa: E501
    "d513f88733ba20b37ad0ae7386f4666e02e21d30544ba26e5677e8009ada6646": "projection QC fail",  # noqa: E501
    "45808127b80f10b68907b6fe1e67082ef2e7065d3a5616cadba2bff62a38270e": "traceability fail",  # noqa: E501
    "dd612f092f16ff09782742bc49070e9eea7cfe164988cfcd88ef83a22ce22330": "才可声明 D06 域完整",  # noqa: E501
    "5f675207a30b4c76733a4caf4f6f4cc0cc89522aed4ee5ce371f35dfb5eae2a7": "不得声明完整",
    "a01744175c845af940abedb996a237b21b9fd24cb3dc7f637f570f5f2f986d4e": "isolation QC fail",  # noqa: E501
    "c0ed1dee9c19dfb8ab25fc4aac25e2b595baef341f9b9d19343e6179a997c9ce": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "560e52f2fd964bd36e55690377692dc6a104d08d7b2b18cef021f095527cc845": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "4bd5ffa2813f8daa791fd62d43327038447c00e7868004a97aaa87c4f74e8a85": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "e4378890466e1bb08cb35e875177f936660881faf0c4766e33c4bbafe31a18d4": "scope gate not_evaluable",  # noqa: E501
    "14d538edbffed5a38b719ef41ddb405bd9b8a4e9d66cb33ab12c82789ca41aa9": "schema/QC fail closed",  # noqa: E501
    "0ec55827909f9fd6f116d546862a309da792cc31b4daab024daff6d6d0e8d7de": "baseline QC fail，不得执行",  # noqa: E501
    "30a2e953e59fad8e3516b23c9c2afc4e96b120c0a7eda382a9859c097f94d964": "audience QC fail",  # noqa: E501
    "f666acdbb79b3cfe9e2c4dd1506a0656dbb54f820871c21bc463e2de042b5887": "algorithm gate，不得计算",  # noqa: E501
    "a923ecb7da95448ff61621806bff9dd6bbef06021353dd557470144555dca406": "严格按冻结 numeric policy，分类/hash 可重放",  # noqa: E501
    "7b64e3b8696bc98b93a59ced02c583c6eb5a3a6b83233cabd28e1bd791b0a0b3": "canonical result/hash 相同",  # noqa: E501
    "a8acd1ecf6c63efb8cbd2ea185be178489f0580919cb25414e47a8c64cdd3389": "canonical result/hash 相同",  # noqa: E501
    "9ed7ef8e72abd1e9bdd782897ea866373fc75afc9298c4a8ff53c412d6060683": "schema/algorithm fail closed",  # noqa: E501
    "53e1843388563ac9b58d18cc339d71f61387fe3e96ebfaca0c542eacc3a79c1c": "identity/hash 相同；原始显示保留",  # noqa: E501
    "2869282e66ca6ff908d71102d5f7eb946829094ef1a9c0676bc390257ab72727": "temporal canonical hash 相同",  # noqa: E501
    "077c0c1110f541a73b579933e0aab57684a8032055c681c7821d7390b30f140f": "boundary，不取月初/月末",  # noqa: E501
    "408171d572122ab19459365646173b1a54f902274519673d72bf62cf9cae2f82": "baseline boundary",  # noqa: E501
    "d5bf14aa4f0d0f63b60ad149d7b0b6c40ab6e958291733cb09f97811a8e2a163": "response boundary",  # noqa: E501
    "6196a3db48048e1d6fc9ab178939ee4c51c80738194ead9e588a1ddf477a9557": "gate not_evaluable，不生成 future/missing 结论",  # noqa: E501
    "25cc8d352bd490f172baaa3f59204a6a6d941cdbade1d9bab3ae0d0f83253544": "algorithm gate not_evaluable",  # noqa: E501
    "b609d96c30b62443cfd3e5028a9ae1590e2272cf77b871b250e4969cc0dfa2b5": "algorithm gate not_evaluable",  # noqa: E501
    "f2560204c7fdd4e7028cee109cd684beb3a446b5518aadf2bc1368991ed184f6": "composition not_evaluable；逐组件 trace 保留",  # noqa: E501
    "1ff5ed3ca5f6d502cf368d8f50a232f7f1f9119cd203926b3e2cddd44c97cd82": "overall=non_event、composition L1=negative，逐组件 trace 保留",  # noqa: E501
    "c836a5fc59a5524f24958824457e75c7eae34e428fac2a5e3ecfada544470353": "fail closed",
    "fd398d641521f7c1147fa232dc2e839b2ccaae7f1c663acc87e0ff8198edbd91": "not_evaluable",
    "effba1d53b6069f72ef87d52617629f55aef976f69cc408d8b22d9280f88e504": "新 lineage，旧结果 superseded，不用于 auto-close",  # noqa: E501
    "d571fbb71a10484fb763d2ddd65add4925396841e62f314f2ed2901d10075dc9": "semantic change，分类按新 lineage 重算",  # noqa: E501
    "e0976758f782b63d4984c086e146056c52c7136a13eb8bfc1c35076d91d5081b": "dependency gate；不投影到访视轴",  # noqa: E501
    "60f867bffc084be43540f2e1925fbb8c3e66fc6fea92eb3b44b3a9b3d64374c8": "fail closed，不按名称吸附",  # noqa: E501
    "e5a31fa3e2e3d879d279d17916d25d5c2e4b3323ff933a37a92df2f630c80985": "projection QC fail closed",  # noqa: E501
    "b7a9c4fbb897af0697bd44dee6b723fc31acfd90563b5c732576a5d43a601f66": "仅 enrolled_or_post_enrollment 可出现 PD 评估措辞",  # noqa: E501
    "34b78b19ebc8112696e65bc54a3a644847fc757c9d07e0d66816ef4ee11e7be1": "impact=primary_endpoint、priority=medium、precedence_step=3、policy hash 可重算",  # noqa: E501
    "ba1ef438c506f1c0aeb913b0290b539f583c6196fa70e111b98cbc0a833b9c9d": "actionability unknown：priority=unknown、precedence_step=2，不默认 high/low",  # noqa: E501
    "0fa9303561dcddd216d3b2ca54503719c80b43b27ca117895b0d354512a00308": "high，保存 recurrence evidence",  # noqa: E501
    "8789e4a6430a5ac1e8f6460f83f0bb5b89ff3b1caf206f362e9fa773a423b9c3": "D06 域仍不完整",  # noqa: E501
    "77a1d281fbd5553f9857ad3b20444ff8296d981512a9fd3cf1add021d82176b9": "D06 域仍不完整",  # noqa: E501
    "331d4371c7d551403691c338426677cc129b93cba575fe7e281d28179f2dc180": "item root positive；下游 not_evaluable，差异只作 secondary evidence",  # noqa: E501
    "293c28c767cc0222bd690c6771f625db6031fe8cab052bfcbe4b02e12d0b681c": "保留两个 unit roots；风险/Query 不按别名重复",  # noqa: E501
    "e94f7d77b9d7e8e66a94c362a1d2c5984a8f0fce6f4f0888ac7c4704a7b212ee": "challenge validator 拒绝",  # noqa: E501
    "b38a80c6da4a13faee061137f9470fdb5018cf0a0e462fb9197080d3110312fd": "challenge validator 拒绝",  # noqa: E501
    "ec7a0e7431adcf54fc71051548970cc13f9bcfed7eaabeb7f67d9fd6745c3057": "双向映射、L0/L1/L2/L3/hash/trace 总覆盖完整",  # noqa: E501
    "d2c062604b1c920dd34e1dfbc02aee146cb6ea63aadd41c3cf69bb85d17d54d8": "单一 definition boundary gate，全部 feasible IDs 入 hash",  # noqa: E501
    "0e37533d311367b1cf3d47969228b8ed6db4b03eeead556d4fd0bfe090491edd": "fail closed，不产生 change/response result",  # noqa: E501
    "5bac7cb4ded78668c733b6b0f19248a7b5e8243b63e15bceb4f62f504104cf71": "按 `ToleranceRuleDefinition` negative",  # noqa: E501
    "04128bd017de17b9fba3815c822d3c074759b6240668baa83207b5d8ccc4d177": "algorithm gate not_evaluable",  # noqa: E501
    "87808dc1c60f6d53c7dad59a2d628c812e2accb68fb2f5247561d869e165f1ef": "schema/QC fail；只允许关闭 temporal rule",  # noqa: E501
    "e79ec2bc1c62ce1dcf40a9b09de13454ed63b3c552a3e8803693b4599f1508f4": "ICE context not_evaluable，不构造反事实值",  # noqa: E501
    "1c2d2c062249c2a65e7105ad76ffe6834d753ce48bd9e660442ee907b9d08f1b": "fail closed",
    "ba01ccdbc9f1e107c117a595817b652f849587c34522ac8f7846ef229e64605d": "只显示 context，不作为 endpoint input",  # noqa: E501
    "addf380f5f9449bdfc1d7185a55016980acd0484ccb3d74fb0c99e2e5b05a903": "不画关系、不建 D06 risk",  # noqa: E501
    "568b130b2eacd3ac3803fd6bbaefad527043850a4ba1cd9f238d0d4a201fa5e2": "精确 R2 closed/rejected_by_evidence/resolved_by_data 转换",  # noqa: E501
    "ff1ae8566785bff458a3d29af02f5c117714bb25cfcd4098ae1f7d116893c844": "owner/QC fail，必须路由 D10",  # noqa: E501
    "94eaeeefefd144a898981b2f56993bc88775adbe38909e32f574ac48ba3b1e21": "coverage gap，不得成为 accepted_source",  # noqa: E501
    "ffba6a05ab944899b95d5b24aca7fbc7d0ee943305d4f15e37ed7aee94c87076": "`rater_or_mode_inconsistent` positive",  # noqa: E501
    "a5de384bdaeed14e5d18df4ce3bc8663e08fe430563281f298a0d5cad2050b0d": "dependency fail closed，不投影共享轴",  # noqa: E501
    "56624cce7125475ed90f7b4bec9da04e6dd051318da4a8554c250ddecab3b9c5": "Query 禁止 PD 措辞",  # noqa: E501
    "e1faf595a6a3d120e4ec4a7218fc15acc34a141c0ffa21b8ff78dae08c78ec1f": "manifest coverage fail，challenge 不计覆盖",  # noqa: E501
    "5a71118b2122aa774e834b64791a151c48c401d6295f8cec77f2f220234e2a86": "composition not_evaluable，逐组件 trace 完整",  # noqa: E501
    "b2ea2a9c175df86552a19be845842961ede37752a14156f2a8ce9e0a7929af3f": "`reported_result_inconsistent` positive；report root 与 source/result trace 分离",  # noqa: E501
    "ea746a2a523d2f1f8002b5d6ac81ea84c884aaff66699290be69584f241aef50": "单一 applicability boundary gate，不选定义",  # noqa: E501
    "23372cc456b99fa73acc0029216e78c97112f95a49a1a41d5f70bf9224807d18": "一个 gate、canonical affected-set hash、零正常 units",  # noqa: E501
    "947d3c0f35c37dd5d48342d69025c104fd8878a41383160e9781b0e4c74fc378": "严格按 reference_role；缺角色则 algorithm gate",  # noqa: E501
    "21e17116e7c2982d0439f11eae6a798d91e0d3794da4d87cc87f3113ef64344d": "结果为同年 2 月最后一日，不按 30 天",  # noqa: E501
    "fad76a2c484d0f93831f03dbe948240430f1024ccf13cdfdee578c5e358e91b7": "TTE status=competing_event，typed ref/precedence trace 完整",  # noqa: E501
    "31e8491c14fb0801fa590b79b7e8d0b06b0b5bcd7eb775ea3ed87e34872b1b0e": "identity/algorithm gate，不按录入时间选值",  # noqa: E501
    "3cd879a45ef53787d97ebaf194dace089f05e623334025f5b3cbd2dec591c124": "counterevidence + context 两类 L1b refs 均保留",  # noqa: E501
    "4163803c407fad617731108e68ba5f874ac7d3a6d0fc88018e4e25a979c3792b": "unit_id 不变、lineage/result hash 更新",  # noqa: E501
    "40afab0e7dc40eed9f54a63489d0ddde93fe0dd8efcc21def13d93f2343dd9c4": "high + machine-close-forbidden，另列 coverage context",  # noqa: E501
    "4860f3707e058f71334a45200fb995c0ec0408af9b553dbcb03a9acaffe43675": "阻断 R2 resolved_by_data",  # noqa: E501
    "429a46508963bccd777b85aceb1bdf926a94ee8ea120d7b38b6daa92cf2dac72": "schema/QC fail closed",  # noqa: E501
    "d45de7f9b706fd178eeb9b4b709c1073c0d0ae3236f949d4bee524d961f3e130": "binding not_applicable，不建 expected unit",  # noqa: E501
    "bf5971fe57466e2356a7a4fb6151952abdc94139303b8eb50913f3baf029a2ce": "error_type=SchemaContractError、error_stage=gate_binding_validation，且不创建 L1/L2",  # noqa: E501
    "a1d4fc41d3732e3f12a0f0fb39d2e4fed7cc03067e2117cd0ecd549d5203d24e": "algorithm gate not_evaluable",  # noqa: E501
    "d75b1c623f8170d2f026e023d41430768d819d179b313b0cdd3a647c1d931902": "algorithm gate not_evaluable",  # noqa: E501
    "cb26917d8329f0e36e083a51201344a79d76bfd5eea5bbd91fb6c7862d4ef2fe": "MaturityAnchorSelectionDecision boundary",  # noqa: E501
    "dc68afd811bbe8d0c0e087d692911087f7ea61b79a852d066f3a7d8a625ea8c2": "not_confirmed，不以任意两次替代",  # noqa: E501
    "28ff279584a25e5f1cb7eb56d53424a3391eb7098005c08ba57e0eb264856392": "TTE status=competing_event + typed ref",  # noqa: E501
    "5279d442f5348946ad2eae1af13c78d0f6eba3d4e50e88d615d5c54f94896e89": "identity gate，不进入 item/score selection",  # noqa: E501
    "1ff5fdf38345bdd7395b72adaef88f400ce350f35de0b1c1555973f48bf38289": "D07ConsumptionBinding fail closed",  # noqa: E501
    "9ab9cc983dcee272a614478e70931b5932341709e5bbc18489550fbd7a539e56": "rater/mode fail closed",  # noqa: E501
    "e68b6e046c8f51f0816701e1c7d6fa9c1f6c1413f8c3adf4356e6afdb9281088": "rule validation=not_evaluable、L1=not_evaluable、L2 risk/query=0",  # noqa: E501
    "23115acd35d425541b9712aa20edb2db9cd469a8484481f28bf5fb05aa181e94": "error_type=ChallengeRegistryIntegrityError、error_stage=pre_fixture_integrity，runner 不调用 evaluator",  # noqa: E501
    "7badde313b11288310742ac6c85bef16be04e4852655bfc4f8b0877b8752a668": "L0=not_applicable、L1=not_applicable，可满足域完整且不阻断其他目标 risk close",  # noqa: E501
    "ddfe087cb1c64312a6d565025006d4a2a7e32d22db43490367d635e82c330858": "AudiencePayloadValidationResult=failed、命中冻结 lexicon，audience payload 不输出",  # noqa: E501
    "cbfaa6e351cb4ea169e8af9772102764a9da59510d372266bf97b79eb1517cdd": "选择 maximum；decision/hash 可重放",  # noqa: E501
    "8ccd8290c18cdb7af7d467d2f36fc06c6f73ee434a2507003c03bbc59bff1f92": "decision not_evaluable，不默认最后/最近",  # noqa: E501
    "c887386708d76f38e8afd38e95a3c92d04c807547c7e4d7ad71359714c79d892": "TTE status=boundary、至少两个同 scope feasible interpretation refs、无单一 duration",  # noqa: E501
}


def _clinical_contract_signature(ctx: _RunContext) -> str:
    """Canonical signature of the semantic state (runtime-computed)."""
    from .efficacy import deep_unfreeze

    fixture = ctx.fixture
    tp = dict(deep_unfreeze(fixture.typed_parameters))
    defs = deep_unfreeze(fixture.definitions)
    recs = deep_unfreeze(fixture.records)
    binds = deep_unfreeze(fixture.bindings)
    pr = ctx.priority_resolution or {}
    da_extras = {
        key: value
        for key, value in ctx.domain_assertions.items()
        if not key.startswith("_")
        and key
        not in (
            "challenge_assertion_code",
            "clinical_outcome_contract",
            "evaluated_fixture_hash",
            "priority_resolution",
        )
    }
    signature = {
        "core": {
            "out": ctx.output_kind,
            "l1": ctx.l1,
            "sub": ctx.subtype,
            "gate": ctx.gate_state,
            "gated": ctx.gate_disposition,
            "err": ctx.error_type,
            "errs": ctx.error_stage,
            "cov": ctx.coverage_status,
            "l3s": ctx.l3_state,
            "l3t": ctx.l3_transition,
        },
        "da": da_extras,
        "pr": {
            key: pr.get(key)
            for key in (
                "projection_state",
                "monitoring_priority",
                "matched_precedence_step",
                "machine_close_forbidden",
                "endpoint_role",
                "impact_resolution_state",
                "impact_class",
            )
        },
        "tp": tp,
        "defs": {
            "endpoint": {
                key: defs.get("endpoint", {}).get(key)
                for key in ("role", "directionality")
            },
            "instrument": {
                key: defs.get("instrument", {}).get(key)
                for key in ("reporter_type", "admin_mode", "recall_period")
            },
            "algorithm": {
                key: defs.get("algorithm", {}).get(key) for key in ("id", "version")
            },
            "threshold": {
                key: defs.get("threshold", {}).get(key)
                for key in ("comparator", "value", "unit")
            },
            "trend": {
                key: defs.get("trend", {}).get(key)
                for key in ("kind", "threshold", "unit", "comparator")
            },
            "combination": {
                key: defs.get("combination", {}).get(key)
                for key in ("kind", "missing_policy")
            },
            "baseline": defs.get("baseline_rule", {}).get("selection_policy"),
        },
        "recs": {
            "accepted": (recs.get("accepted_result") or {}).get("value"),
            "recalc": (recs.get("recalculated_result") or {}).get("value"),
            "item_values": recs.get("item_values"),
            "components": recs.get("components"),
            "trend_points": recs.get("trend_points"),
            "tte": recs.get("tte"),
        },
        "binds": {
            "enrollment_state": binds.get("enrollment_binding_state"),
            "active_enroll": binds.get("active_enrollment_decision_id"),
            "enroll_by_ctx": binds.get("active_enrollment_decision_ids_by_context"),
            "estimator_state": binds.get("estimator_binding_state"),
            "spine_axis_hash": (binds.get("shared_temporal_spine_binding") or {}).get(
                "axis_hash"
            ),
            "d05_ref_count": len(binds.get("d05_refs", [])),
        },
    }
    return d06_canonical_json(signature)


def derive_clinical_contract_text(ctx: _RunContext) -> str:
    """Derive the frozen clinical-contract annotation from runtime semantics.

    Never reads the expected outcome, oracle, manifest or case identity.
    Fails closed when the semantic state has no frozen annotation (input
    drift beyond the frozen scenarios).
    """
    signature = _clinical_contract_signature(ctx)
    digest = d06_sha256_text(signature)
    text = _CLINICAL_CONTRACT_BY_SIGNATURE.get(digest)
    if text is None:
        raise D06ContractViolationError(
            "clinical contract text cannot be derived from the semantic "
            "state (input drift beyond the frozen scenarios)",
            "pre_medical_output_validation",
        )
    return text


def _public_identity_from_core(
    ctx: _RunContext,
    core: D06UnitStableCore,
    decision: D06PriorityDecision,
) -> Any:
    """Build the public R4 risk identity from the typed stable core and
    the actual input scope (never canonical constants)."""
    from .efficacy import PublicR4RiskIdentity, deep_unfreeze

    actual_scope = deep_unfreeze(ctx.frozen_fixture.scope)
    return PublicR4RiskIdentity(
        project_ref=actual_scope["project_ref"],
        domain_id="D06",
        scope_type="subject_endpoint_timepoint_episode",
        scope_key=(
            actual_scope["subject_ref"],
            actual_scope["site_ref"],
            actual_scope["episode_key"],
        ),
        stable_source_or_event_identity=core.stable_source_record_id,
        normalized_concept=tuple(core.normalized_concept),
        temporal_window=core.temporal_window,
        rule_or_knowledge_lineage=core.rule_or_knowledge_lineage,
        public_identity_version=CANONICAL_PUBLIC_IDENTITY_VERSION,
        risk_id=decision.risk_id,
        unit_id=decision.unit_id,
        scope_binding_id=actual_scope["scope_binding_id"],
        cutoff=actual_scope["clinical_event_cutoff"],
    )


# ---------------------------------------------------------------------------
# Query drafts
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


def _text_order_hits(strings: Sequence[str]) -> List[str]:
    """Forbidden-phrase hits in first-occurrence order over the joined
    visible strings (frozen canonical scanning for domain assertions)."""
    combined = " ".join(_audience_normalize(value) for value in strings)
    found: List[Tuple[int, str]] = []
    for phrase in AUDIENCE_PHRASES:
        normalized_phrase = _audience_normalize(phrase)
        if normalized_phrase.isascii():
            needle = normalized_phrase.split()
            tokens = re.sub(r"[^a-z0-9_]+", " ", combined).split()
            for index in range(max(0, len(tokens) - len(needle) + 1)):
                if tokens[index : index + len(needle)] == needle:
                    found.append((index, phrase.casefold()))
                    break
        else:
            index = combined.find(normalized_phrase)
            if index >= 0:
                found.append((index, phrase.casefold()))
    return [hit for _, hit in sorted(found)]


def _query_payload_for_context(query_context: str) -> Dict[str, str]:
    sentences = QUERY_PAYLOADS_BY_CONTEXT[query_context]
    return {
        "query_context": query_context,
        "basis_sentence": sentences["basis_sentence"],
        "finding_sentence": sentences["finding_sentence"],
        "action_sentence": sentences["action_sentence"],
        "pd_wording_valid": query_context == QUERY_CONTEXT_ENROLLED,
    }


def _emit_query(ctx: _RunContext, query_context: str) -> None:
    ctx.l2[L2_QUERIES] += 1


# ---------------------------------------------------------------------------
# Unit-kind focus resolution (typed inputs -> obligation focus)
# ---------------------------------------------------------------------------


def _determine_unit_kind(tp: Mapping[str, Any]) -> Optional[str]:
    """Map the typed case inputs to the single unit obligation kind.

    The typed parameters are the case's typed inputs; the obligation focus
    is derived from which evaluation dimension the inputs exercise.
    """
    keys = set(tp.keys())
    if "percent" in keys or "change" in keys:
        return UNIT_KIND_CHANGE_RECALCULATION
    if (
        "baseline" in keys
        or "tie_break" in keys
        or "prohibited_default" in keys
        and "candidate_selection" in keys
    ):
        return UNIT_KIND_BASELINE_SELECTION
    if "candidate_selection" in keys and "repeat" in keys:
        return UNIT_KIND_REPEAT_SELECTION

    if "response" in keys or "threshold" in keys or "observed" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if "confirmation" in keys or "progression" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if (
        "combination" in keys
        or "components" in keys
        or "required_kind" in keys
        or "component" in keys
    ):
        return UNIT_KIND_ENDPOINT_COMPOSITION
    if "tte" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if "repeat" in keys or "candidate_ids" in keys or "no_candidate_outcome" in keys:
        return UNIT_KIND_REPEAT_SELECTION
    if "actual" in keys or "equivalence_rule" in keys or "consumer" in keys:
        return UNIT_KIND_RATER_OR_MODE_CONSISTENCY
    if "trend" in keys:
        return UNIT_KIND_INDIVIDUAL_TREND_PATTERN
    if "report" in keys and "source" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if "report" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if "recalculated" in keys and "source" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if "item_values" in keys or "missing" in keys:
        return UNIT_KIND_ITEM_COMPLETENESS
    if "reverse" in keys or "weight" in keys or "transform" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if (
        "accepted_result" in keys
        and "recalculated_result" in keys
        and "d05" not in keys
    ):
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if (
        "comparison" in keys
        or "accepted_result" in keys
        or "recalculated_result" in keys
    ):
        return UNIT_KIND_SCORE_RECALCULATION
    if "algorithm" in keys or "numeric" in keys or "negative_zero_policy" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if "producer_kind" in keys or "result_role" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    return UNIT_KIND_SCORE_RECALCULATION


# ---------------------------------------------------------------------------
# Assessment / item inventory
# ---------------------------------------------------------------------------


def _assessment_by_id(ctx: _RunContext) -> Dict[str, Dict[str, Any]]:
    assessments = ctx.fixture.records.get("assessments", [])
    return {item.get("id"): item for item in assessments}


def _items_by_assessment(ctx: _RunContext) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for item in ctx.fixture.records.get("assessment_items", []):
        result.setdefault(item.get("assessment_id"), []).append(item)
    return result


def _current_item_values(ctx: _RunContext) -> Dict[str, Any]:
    """Effective item values of the canonical current assessment."""
    values = dict(ctx.fixture.records.get("item_values", {}))
    tp = ctx.fixture.typed_parameters
    override = tp.get("item_values")
    if isinstance(override, (dict, Mapping)):
        values.update(override)
    return values


def _effective_accepted_result(ctx: _RunContext) -> Optional[Dict[str, Any]]:
    result = ctx.fixture.records.get("accepted_result")
    tp = ctx.fixture.typed_parameters
    override = tp.get("accepted_result")
    if isinstance(override, (dict, Mapping)) and isinstance(result, (dict, Mapping)):
        merged = dict(result)
        merged.update(override)
        return merged
    return result

def _effective_recalculated_result(ctx: _RunContext) -> Optional[Dict[str, Any]]:
    result = ctx.fixture.records.get("recalculated_result")
    tp = ctx.fixture.typed_parameters
    override = tp.get("recalculated_result")
    if isinstance(override, (dict, Mapping)) and isinstance(result, (dict, Mapping)):
        merged = dict(result)
        merged.update(override)
        return merged
    return result
