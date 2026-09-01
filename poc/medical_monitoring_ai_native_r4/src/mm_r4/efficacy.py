"""R4-D06 efficacy endpoint / scale / individual-trend slice -- domain model.

Frozen source of truth: ``FROZEN_R4_D06_CONTRACT_V1_16`` (§§1-15).  This
module owns the D06 **domain objects and stable identities**:

1. Canonical serialization and content addressing that reproduce the frozen
   generator's canonical JSON exactly (Unicode NFC on keys and strings,
   sorted keys, compact separators, ``ensure_ascii=False``, NaN/Infinity
   rejected).  Every D06 id/hash is a deterministic content address over a
   canonical payload; ``-0`` is normalized, ``1``/``1.0``/``1.00`` and
   Unicode-equivalent labels canonicalize identically.
2. Closed enumerations of the D06 slice: unit kinds, positive subtypes,
   gate kinds/states/decision statuses, TTE states, scope statuses,
   reporter types, D05 dispositions, enrollment query contexts, priority
   inputs, audience lexicon (frozen ``d06-audience-zh-v1``).
3. Fail-closed error types with the frozen ``error_type``/``error_stage``
   vocabulary (``SchemaContractError``, ``D06ContractViolationError``,
   ``D06BindingContractError``, ``OwnerScopeContractError``,
   ``ProjectionContractError``, ``AudiencePayloadValidationError``,
   ``ChallengeAssertionContractError``,
   ``ChallengeRegistryIntegrityError``).
4. Immutable typed objects for the computed identity/decision surface:
   the canonical ``D06PriorityPolicy``, ``D06PriorityResolverInput``,
   ``D06PriorityDecision``, ``D06UnitStableCore``,
   ``PublicR4RiskIdentity``, ``D06RiskBinding`` and the
   ``D06ChallengeOutcome`` object the entrypoints return.

The runtime never imports the frozen catalog/oracle/registry and never
branches on challenge number, fixture id, test id, expected text or
expected outcome.  All data is synthetic and offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Canonical serialization (frozen generator contract)
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _normalize_nfc(value: Any) -> Any:
    """Recursively Unicode-NFC-normalize strings and dict keys."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_nfc(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): _normalize_nfc(item)
            for key, item in value.items()
        }
    return value


def d06_canonical_json(value: Any) -> str:
    """Deterministic D06 canonical JSON (NFC, sorted keys, compact)."""
    return json.dumps(
        _normalize_nfc(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def d06_sha256_text(text: str) -> str:
    """SHA-256 of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def d06_content_hash(value: Any) -> str:
    """Content address of any JSON-able value (sha256 of canonical JSON)."""
    return d06_sha256_text(d06_canonical_json(value))


def d06_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def d06_hash_hex(value: Any) -> str:
    """Hex sha256 of a canonical payload (no ``sha256:`` prefix)."""
    return d06_content_hash(value)


def verify_embedded_hash(obj: Mapping[str, Any], label: str) -> str:
    """Verify an object's embedded ``hash`` field against its payload.

    Returns the expected ``sha256:...`` string; raises
    :class:`D06ContractViolationError` on mismatch.
    """
    supplied = obj.get("hash")
    core = {key: value for key, value in obj.items() if key != "hash"}
    expected = f"sha256:{d06_sha256_text(d06_canonical_json(core))}"
    if supplied != expected:
        raise D06ContractViolationError(
            f"{label} hash mismatch", "pre_medical_output_validation"
        )
    return expected


def verify_lineage_hash(obj: Mapping[str, Any], label: str) -> str:
    """Verify an object's embedded ``lineage_hash`` field."""
    supplied = obj.get("lineage_hash")
    core = {key: value for key, value in obj.items() if key != "lineage_hash"}
    expected = f"sha256:{d06_sha256_text(d06_canonical_json(core))}"
    if supplied != expected:
        raise D06ContractViolationError(
            f"{label} lineage hash mismatch", "pre_medical_output_validation"
        )
    return expected


def verify_content_hash(obj: Mapping[str, Any], label: str) -> str:
    """Verify an object's embedded ``content_hash`` field."""
    supplied = obj.get("content_hash")
    core = {key: value for key, value in obj.items() if key != "content_hash"}
    expected = f"sha256:{d06_sha256_text(d06_canonical_json(core))}"
    if supplied != expected:
        raise D06ContractViolationError(
            f"{label} content hash mismatch", "pre_medical_output_validation"
        )
    return expected


# ---------------------------------------------------------------------------
# Fail-closed error vocabulary (frozen §12.1 / §13)
# ---------------------------------------------------------------------------


class D06Error(Exception):
    """Base D06 fail-closed error carrying the frozen type/stage pair."""

    error_type = "D06Error"
    error_stage = "pre_medical_output_validation"

    def __init__(self, message: str, error_stage: Optional[str] = None):
        super().__init__(message)
        if error_stage is not None:
            self.error_stage = error_stage


class SchemaContractError(D06Error):
    error_type = "SchemaContractError"


class D06ContractViolationError(D06Error):
    error_type = "D06ContractViolationError"


class D06BindingContractError(D06Error):
    error_type = "D06BindingContractError"
    error_stage = "typed_binding_validation"


class OwnerScopeContractError(D06Error):
    error_type = "OwnerScopeContractError"
    error_stage = "owner_scope_validation"


class ProjectionContractError(D06Error):
    error_type = "ProjectionContractError"
    error_stage = "projection_validation"


class AudiencePayloadValidationError(D06Error):
    error_type = "AudiencePayloadValidationError"
    error_stage = "audience_payload_validation"


class ChallengeAssertionContractError(D06Error):
    error_type = "ChallengeAssertionContractError"
    error_stage = "assertion_manifest_validation"


class ChallengeRegistryIntegrityError(D06Error):
    error_type = "ChallengeRegistryIntegrityError"
    error_stage = "pre_fixture_integrity"


# ---------------------------------------------------------------------------
# Closed enumerations
# ---------------------------------------------------------------------------

# Unit kinds (contract §4.3 closed set).
UNIT_KIND_ITEM_COMPLETENESS = "item_completeness"
UNIT_KIND_ITEM_VALUE_VALIDITY = "item_value_validity"
UNIT_KIND_SCORE_RECALCULATION = "score_recalculation"
UNIT_KIND_BASELINE_SELECTION = "baseline_selection"
UNIT_KIND_CHANGE_RECALCULATION = "change_recalculation"
UNIT_KIND_RESPONSE_CLASSIFICATION = "response_classification"
UNIT_KIND_ENDPOINT_COMPOSITION = "endpoint_composition"
UNIT_KIND_REPEAT_SELECTION = "repeat_selection"
UNIT_KIND_RATER_OR_MODE_CONSISTENCY = "rater_or_mode_consistency"
UNIT_KIND_INDIVIDUAL_TREND_PATTERN = "individual_trend_pattern"
UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY = "accepted_report_consistency"

UNIT_KINDS: Tuple[str, ...] = (
    UNIT_KIND_ITEM_COMPLETENESS,
    UNIT_KIND_ITEM_VALUE_VALIDITY,
    UNIT_KIND_SCORE_RECALCULATION,
    UNIT_KIND_BASELINE_SELECTION,
    UNIT_KIND_CHANGE_RECALCULATION,
    UNIT_KIND_RESPONSE_CLASSIFICATION,
    UNIT_KIND_ENDPOINT_COMPOSITION,
    UNIT_KIND_REPEAT_SELECTION,
    UNIT_KIND_RATER_OR_MODE_CONSISTENCY,
    UNIT_KIND_INDIVIDUAL_TREND_PATTERN,
    UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY,
)

# Positive primary subtypes (contract §8.1) and their fixed unit-kind map.
SUBTYPE_REQUIRED_COMPONENT_MISSING = "required_component_missing"
SUBTYPE_COMPONENT_VALUE_INVALID = "component_value_invalid"
SUBTYPE_SCORE_INCONSISTENT = "score_inconsistent"
SUBTYPE_BASELINE_INCONSISTENT = "baseline_inconsistent"
SUBTYPE_CHANGE_VALUE_INCONSISTENT = "change_value_inconsistent"
SUBTYPE_RESPONSE_CLASS_INCONSISTENT = "response_class_inconsistent"
SUBTYPE_ENDPOINT_COMPOSITION_INCONSISTENT = "endpoint_composition_inconsistent"
SUBTYPE_REPEAT_SELECTION_INCONSISTENT = "repeat_selection_inconsistent"
SUBTYPE_RATER_OR_MODE_INCONSISTENT = "rater_or_mode_inconsistent"
SUBTYPE_INDIVIDUAL_TREND_INCONSISTENT = "individual_trend_inconsistent"
SUBTYPE_REPORTED_RESULT_INCONSISTENT = "reported_result_inconsistent"

POSITIVE_SUBTYPES: Tuple[str, ...] = (
    SUBTYPE_REQUIRED_COMPONENT_MISSING,
    SUBTYPE_COMPONENT_VALUE_INVALID,
    SUBTYPE_SCORE_INCONSISTENT,
    SUBTYPE_BASELINE_INCONSISTENT,
    SUBTYPE_CHANGE_VALUE_INCONSISTENT,
    SUBTYPE_RESPONSE_CLASS_INCONSISTENT,
    SUBTYPE_ENDPOINT_COMPOSITION_INCONSISTENT,
    SUBTYPE_REPEAT_SELECTION_INCONSISTENT,
    SUBTYPE_RATER_OR_MODE_INCONSISTENT,
    SUBTYPE_INDIVIDUAL_TREND_INCONSISTENT,
    SUBTYPE_REPORTED_RESULT_INCONSISTENT,
)

SUBTYPE_TO_UNIT_KIND: Dict[str, str] = {
    SUBTYPE_REQUIRED_COMPONENT_MISSING: UNIT_KIND_ITEM_COMPLETENESS,
    SUBTYPE_COMPONENT_VALUE_INVALID: UNIT_KIND_ITEM_VALUE_VALIDITY,
    SUBTYPE_SCORE_INCONSISTENT: UNIT_KIND_SCORE_RECALCULATION,
    SUBTYPE_BASELINE_INCONSISTENT: UNIT_KIND_BASELINE_SELECTION,
    SUBTYPE_CHANGE_VALUE_INCONSISTENT: UNIT_KIND_CHANGE_RECALCULATION,
    SUBTYPE_RESPONSE_CLASS_INCONSISTENT: UNIT_KIND_RESPONSE_CLASSIFICATION,
    SUBTYPE_ENDPOINT_COMPOSITION_INCONSISTENT: UNIT_KIND_ENDPOINT_COMPOSITION,
    SUBTYPE_REPEAT_SELECTION_INCONSISTENT: UNIT_KIND_REPEAT_SELECTION,
    SUBTYPE_RATER_OR_MODE_INCONSISTENT: UNIT_KIND_RATER_OR_MODE_CONSISTENCY,
    SUBTYPE_INDIVIDUAL_TREND_INCONSISTENT: UNIT_KIND_INDIVIDUAL_TREND_PATTERN,
    SUBTYPE_REPORTED_RESULT_INCONSISTENT: UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY,
}

UNIT_KIND_TO_SUBTYPE: Dict[str, str] = {
    value: key for key, value in SUBTYPE_TO_UNIT_KIND.items()
}

# Gate kinds / states / decision statuses (contract §4.3 closed truth table).
GATE_APPLICABILITY = "applicability"
GATE_ROUTING = "routing"
GATE_DEFINITION = "definition"
GATE_ALGORITHM = "algorithm"
GATE_BASELINE = "baseline"
GATE_UNIT_OR_SCALE = "unit_or_scale"
GATE_DEPENDENCY = "dependency"
GATE_CUTOFF_SCOPE = "cutoff_scope"

GATE_KINDS: Tuple[str, ...] = (
    GATE_APPLICABILITY,
    GATE_ROUTING,
    GATE_DEFINITION,
    GATE_ALGORITHM,
    GATE_BASELINE,
    GATE_UNIT_OR_SCALE,
    GATE_DEPENDENCY,
    GATE_CUTOFF_SCOPE,
)

GATE_OPEN = "open"
GATE_CLOSED = "closed"
GATE_STATES: Tuple[str, ...] = (GATE_OPEN, GATE_CLOSED)

GATE_DECISION_BOUNDARY = "boundary"
GATE_DECISION_NOT_EVALUABLE = "not_evaluable"
GATE_DECISION_RESOLVED = "resolved"
GATE_DECISION_STATUSES: Tuple[str, ...] = (
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_DECISION_RESOLVED,
)

# Scope statuses (contract §4.2).
SCOPE_IN_SCOPE = "in_scope"
SCOPE_OUT_OF_CUTOFF = "out_of_cutoff"
SCOPE_BOUNDARY = "boundary"
SCOPE_NOT_EVALUABLE = "not_evaluable"
SCOPE_STATUSES: Tuple[str, ...] = (
    SCOPE_IN_SCOPE,
    SCOPE_OUT_OF_CUTOFF,
    SCOPE_BOUNDARY,
    SCOPE_NOT_EVALUABLE,
)

# TTE statuses (contract §4.2).
TTE_STATUS_EVENT = "event"
TTE_STATUS_COMPETING_EVENT = "competing_event"
TTE_STATUS_CENSORED = "censored"
TTE_STATUS_BOUNDARY = "boundary"
TTE_STATUS_NOT_EVALUABLE = "not_evaluable"
TTE_STATUSES: Tuple[str, ...] = (
    TTE_STATUS_EVENT,
    TTE_STATUS_COMPETING_EVENT,
    TTE_STATUS_CENSORED,
    TTE_STATUS_BOUNDARY,
    TTE_STATUS_NOT_EVALUABLE,
)

# D05 dispositions reused verbatim.
D05_OCCURRENCE_NEGATIVE = "negative"
D05_OCCURRENCE_POSITIVE = "positive"
D05_TIMING_NEGATIVE = "negative"
D05_TIMING_POSITIVE = "positive"
D05_ASSIGNMENT_UNIQUE = "unique"

# Enrollment query contexts (contract §9.2).
QUERY_CONTEXT_NOT_OCCURRED = "enrollment_not_occurred"
QUERY_CONTEXT_ENROLLED = "enrolled_or_post_enrollment"
QUERY_CONTEXT_UNRESOLVED = "enrollment_state_unresolved"
QUERY_CONTEXTS: Tuple[str, ...] = (
    QUERY_CONTEXT_NOT_OCCURRED,
    QUERY_CONTEXT_ENROLLED,
    QUERY_CONTEXT_UNRESOLVED,
)

# Endpoint roles (contract §4.1 closed set).
ENDPOINT_ROLE_PRIMARY = "primary"
ENDPOINT_ROLE_CO_PRIMARY = "co_primary"
ENDPOINT_ROLE_MULTIPLE_PRIMARY = "multiple_primary"
ENDPOINT_ROLE_KEY_SECONDARY = "key_secondary"
ENDPOINT_ROLE_SECONDARY = "secondary"
ENDPOINT_ROLE_EXPLORATORY = "exploratory"
ENDPOINT_ROLE_SUPPORTIVE = "supportive"
ENDPOINT_ROLE_UNDEFINED = "undefined"
ENDPOINT_ROLES: Tuple[str, ...] = (
    ENDPOINT_ROLE_PRIMARY,
    ENDPOINT_ROLE_CO_PRIMARY,
    ENDPOINT_ROLE_MULTIPLE_PRIMARY,
    ENDPOINT_ROLE_KEY_SECONDARY,
    ENDPOINT_ROLE_SECONDARY,
    ENDPOINT_ROLE_EXPLORATORY,
    ENDPOINT_ROLE_SUPPORTIVE,
    ENDPOINT_ROLE_UNDEFINED,
)

# Directionality (contract §4.1).
DIRECTION_HIGHER_BETTER = "higher_better"
DIRECTION_LOWER_BETTER = "lower_better"
DIRECTION_BIDIRECTIONAL = "bidirectional"
DIRECTION_EVENT_BASED = "event_based"
DIRECTION_UNDEFINED = "undefined"
DIRECTIONALITIES: Tuple[str, ...] = (
    DIRECTION_HIGHER_BETTER,
    DIRECTION_LOWER_BETTER,
    DIRECTION_BIDIRECTIONAL,
    DIRECTION_EVENT_BASED,
    DIRECTION_UNDEFINED,
)

# Reporter types (contract §4.1).
REPORTER_PRO = "PRO"
REPORTER_OBSRO = "ObsRO"
REPORTER_CLINRO = "ClinRO"
REPORTER_PERFO = "PerfO"
REPORTER_OBJECTIVE = "objective_measure"
REPORTER_TYPES: Tuple[str, ...] = (
    REPORTER_PRO,
    REPORTER_OBSRO,
    REPORTER_CLINRO,
    REPORTER_PERFO,
    REPORTER_OBJECTIVE,
)

# Impact / recurrence / recoverability / actionability (contract §9.1).
IMPACT_RIGHTS_SAFETY = "rights_safety"
IMPACT_CRITICAL_TREATMENT = "critical_treatment"
IMPACT_PRIMARY_ENDPOINT = "primary_endpoint"
IMPACT_KEY_SECONDARY_ENDPOINT = "key_secondary_endpoint"
IMPACT_MANDATORY_CRITICAL_SAMPLE = "mandatory_critical_sample"
IMPACT_OTHER_REQUIRED = "other_required"
IMPACT_ADMINISTRATIVE = "administrative"
IMPACT_CLASSES: Tuple[str, ...] = (
    IMPACT_RIGHTS_SAFETY,
    IMPACT_CRITICAL_TREATMENT,
    IMPACT_PRIMARY_ENDPOINT,
    IMPACT_KEY_SECONDARY_ENDPOINT,
    IMPACT_MANDATORY_CRITICAL_SAMPLE,
    IMPACT_OTHER_REQUIRED,
    IMPACT_ADMINISTRATIVE,
)

RECURRENCE_SINGLE = "single"
RECURRENCE_REPEATED_SUBJECT = "repeated_subject"
RECURRENCE_REPEATED_SITE = "repeated_site"
RECURRENCE_CLASSES: Tuple[str, ...] = (
    RECURRENCE_SINGLE,
    RECURRENCE_REPEATED_SUBJECT,
    RECURRENCE_REPEATED_SITE,
)

RECOVERABLE = "recoverable"
TIME_CRITICAL = "time_critical"
IRRECOVERABLE = "irrecoverable"
RECOVERABILITY_UNKNOWN = "unknown"
RECOVERABILITY_CLASSES: Tuple[str, ...] = (
    RECOVERABLE,
    TIME_CRITICAL,
    IRRECOVERABLE,
    RECOVERABILITY_UNKNOWN,
)

ACTIONABLE = "actionable"
CONTEXT_ONLY = "context_only"
ACTIONABILITY_UNKNOWN = "unknown"
ACTIONABILITY_CLASSES: Tuple[str, ...] = (
    ACTIONABLE,
    CONTEXT_ONLY,
    ACTIONABILITY_UNKNOWN,
)

# Monitoring priorities (shared vocabulary).
PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"
PRIORITY_UNKNOWN = "unknown"
PRIORITIES: Tuple[str, ...] = (
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    PRIORITY_UNKNOWN,
)

# Output kinds of the challenge outcome.
OUTPUT_KIND_RESULT = "result"
OUTPUT_KIND_GATE = "gate"
OUTPUT_KIND_PROJECTION = "projection"
OUTPUT_KIND_DEFINITION_BINDING = "definition_binding"
OUTPUT_KIND_ERROR = "error"
OUTPUT_KINDS: Tuple[str, ...] = (
    OUTPUT_KIND_RESULT,
    OUTPUT_KIND_GATE,
    OUTPUT_KIND_PROJECTION,
    OUTPUT_KIND_DEFINITION_BINDING,
    OUTPUT_KIND_ERROR,
)

# Decision statuses used by selection decisions.
DECISION_UNIQUE = "unique"
DECISION_TIE_BOUNDARY = "tie_boundary"
DECISION_MULTI_FEASIBLE_BOUNDARY = "multi_feasible_boundary"
DECISION_NOT_EVALUABLE = "not_evaluable"
DECISION_NOT_APPLICABLE = "not_applicable"
DECISION_BOUNDARY = "boundary"
DECISION_CONFIRMED = "confirmed"
DECISION_NOT_CONFIRMED = "not_confirmed"

# L0 coverage statuses (reused from the frozen R1 vocabulary, mirrored here
# as constants so the engine never depends on catalog metadata).
COVERAGE_COVERED = "covered"
COVERAGE_PARTIAL = "partial"
COVERAGE_TRUNCATED = "truncated"
COVERAGE_NOT_APPLICABLE = "not_applicable"
COVERAGE_NOT_EVALUABLE = "not_evaluable"
COVERAGE_FAILED = "failed"
COVERAGE_MISSING = "missing"

# L1 dispositions (frozen shared vocabulary).
L1_POSITIVE = "positive"
L1_NEGATIVE = "negative"
L1_BOUNDARY = "boundary"
L1_NOT_APPLICABLE = "not_applicable"
L1_NOT_EVALUABLE = "not_evaluable"
L1_DISPOSITIONS: Tuple[str, ...] = (
    L1_POSITIVE,
    L1_NEGATIVE,
    L1_BOUNDARY,
    L1_NOT_APPLICABLE,
    L1_NOT_EVALUABLE,
)

# ---------------------------------------------------------------------------
# Frozen audience lexicon (d06-audience-zh-v1, contract §10)
# ---------------------------------------------------------------------------

AUDIENCE_PHRASES: Tuple[str, ...] = (
    "positive",
    "negative",
    "boundary",
    "not_applicable",
    "not_evaluable",
    "candidate",
    "formal fact",
    "model confidence",
    "backend",
    "debug",
    "log",
    "classifier",
    "payload",
    "lineage",
    "hash",
    "QC",
    "正式事实",
    "候选信号",
    "只读投影",
    "规则命中",
    "后端",
    "模型置信度",
    "算法异常",
    "模型判断",
)
AUDIENCE_DISPLAY_KEYS: Tuple[str, ...] = (
    "id",
    "*_id",
    "hash",
    "*_hash",
    "ref",
    "*_ref",
    "classifier",
    "payload",
    "lineage",
    "backend",
    "debug",
    "log",
    "confidence",
)
AUDIENCE_LEXICON_HASH = (
    "d73a3da6fb9e5643c17673273bff042af5df75259979dcc59cb8adff917e5a75"
)
AUDIENCE_VALIDATOR_VERSION = "d06-audience-validator-v1"
AUDIENCE_LEXICON_VERSION = "d06-audience-zh-v1"
AUDIENCE_VALIDATOR_DEFINITION: Dict[str, Any] = {
    "payload_schemas": {
        "journey": [
            "display_text",
            "endpoint_lanes",
            "payload_kind",
            "payload_schema_version",
            "visit_axis_label",
        ],
        "query": [
            "action_sentence",
            "basis_sentence",
            "finding_sentence",
            "payload_kind",
            "payload_schema_version",
            "query_context",
        ],
        "risk_label": [
            "finding_summary",
            "jump_target",
            "payload_kind",
            "payload_schema_version",
            "priority_label",
            "risk_category",
        ],
    },
    "validator_version": AUDIENCE_VALIDATOR_VERSION,
}
AUDIENCE_VALIDATOR_HASH = d06_sha256_text(
    d06_canonical_json(AUDIENCE_VALIDATOR_DEFINITION)
)

# Frozen canonical synthetic scope (contract §15).
CANONICAL_SYNTHETIC_SCOPE: Dict[str, str] = {
    "accepted_snapshot_ref": "SYN-SNAPSHOT-001",
    "clinical_event_cutoff": "2026-01-31T23:59:59+08:00",
    "episode_key": "EPISODE-001",
    "monitoring_mode": "full",
    "project_ref": "SYN-D06-PROJECT",
    "run_ref": "SYN-D06-RUN-001",
    "scope_binding_id": "SYN-D06-SCOPE-001",
    "site_ref": "SYN-D06-SITE-001",
    "snapshot_as_of": "2026-01-31T23:59:59+08:00",
    "source_revision": "SYN-REV-001",
    "subject_ref": "SYN-D06-SUBJECT-001",
}

SCOPE_IDENTITY_FIELDS: Tuple[str, ...] = (
    "project_ref",
    "run_ref",
    "monitoring_mode",
    "subject_ref",
    "site_ref",
    "episode_key",
    "source_revision",
    "accepted_snapshot_ref",
    "scope_binding_id",
)
SCOPE_ALL_FIELDS: Tuple[str, ...] = SCOPE_IDENTITY_FIELDS + ("clinical_event_cutoff",)

# ---------------------------------------------------------------------------
# Priority policy (frozen canonical definition, contract §9.1)
# ---------------------------------------------------------------------------


def _canonical_priority_policy_payload() -> Dict[str, Any]:
    policy = {
        "object_type": "D06PriorityPolicy",
        "policy_id": "D06-PRIORITY-V1",
        "version": "1.0",
        "ordered_precedence_rules": [
            {
                "step": 1,
                "impact_classes": ["rights_safety", "critical_treatment"],
                "monitoring_priority": "high",
                "machine_close_forbidden": True,
                "reason_codes": ["rights_or_critical_treatment"],
            },
            {
                "step": 2,
                "trigger_any": [
                    "impact_unresolved",
                    "recoverability_unknown",
                    "actionability_context_only_or_unknown",
                ],
                "monitoring_priority": "unknown",
                "machine_close_forbidden": False,
                "reason_codes": ["priority_input_unresolved"],
            },
            {
                "step": 3,
                "impact_classes": ["primary_endpoint", "mandatory_critical_sample"],
                "high_if_recoverability": ["time_critical", "irrecoverable"],
                "otherwise_priority": "medium",
                "high_machine_close_forbidden": True,
                "reason_codes": ["primary_or_mandatory_critical"],
            },
            {
                "step": 4,
                "impact_classes": ["key_secondary_endpoint", "other_required"],
                "high_if_recurrence": ["repeated_site"],
                "high_if_recoverability": ["irrecoverable"],
                "otherwise_priority": "medium",
                "high_machine_close_forbidden": True,
                "reason_codes": ["key_secondary_or_other_required"],
            },
            {
                "step": 5,
                "impact_classes": ["administrative"],
                "high_if_recurrence": ["repeated_site"],
                "high_if_recoverability": ["irrecoverable", "time_critical"],
                "medium_if_recurrence": ["repeated_subject"],
                "otherwise_priority": "low",
                "high_machine_close_forbidden": True,
                "reason_codes": ["administrative_precedence"],
            },
        ],
        "source_locator_ids": ["SYN-LOC-D06-PRIORITY-POLICY-001"],
    }
    policy["policy_hash"] = f"sha256:{d06_sha256_text(d06_canonical_json(policy))}"
    return policy


CANONICAL_PRIORITY_POLICY: Dict[str, Any] = _canonical_priority_policy_payload()

PRIORITY_REASON_BY_STEP: Dict[int, List[str]] = {
    1: ["rights_or_critical_treatment"],
    2: ["priority_input_unresolved"],
    3: ["primary_or_mandatory_critical"],
    4: ["key_secondary_or_other_required"],
    5: ["administrative_precedence"],
}


def resolve_priority_step(
    impact_class: Optional[str],
    impact_resolution_state: str,
    recurrence_class: str,
    recoverability: str,
    actionability: str,
) -> Tuple[str, int, bool]:
    """Frozen five-step first-match priority policy (§9.1).

    Returns ``(monitoring_priority, matched_precedence_step,
    machine_close_forbidden)``.  First match wins; never falls through to
    low when inputs are unresolved.
    """
    if impact_class in (IMPACT_RIGHTS_SAFETY, IMPACT_CRITICAL_TREATMENT):
        return PRIORITY_HIGH, 1, True
    if (
        impact_resolution_state == "unresolved"
        or recoverability == RECOVERABILITY_UNKNOWN
        or actionability in (CONTEXT_ONLY, ACTIONABILITY_UNKNOWN)
    ):
        return PRIORITY_UNKNOWN, 2, False
    if impact_class in (IMPACT_PRIMARY_ENDPOINT, IMPACT_MANDATORY_CRITICAL_SAMPLE):
        priority = (
            PRIORITY_HIGH
            if recoverability in (TIME_CRITICAL, IRRECOVERABLE)
            else PRIORITY_MEDIUM
        )
        return priority, 3, priority == PRIORITY_HIGH
    if impact_class in (IMPACT_KEY_SECONDARY_ENDPOINT, IMPACT_OTHER_REQUIRED):
        priority = (
            PRIORITY_HIGH
            if recurrence_class == RECURRENCE_REPEATED_SITE
            or recoverability == IRRECOVERABLE
            else PRIORITY_MEDIUM
        )
        return priority, 4, priority == PRIORITY_HIGH
    if impact_class == IMPACT_ADMINISTRATIVE:
        if recurrence_class == RECURRENCE_REPEATED_SITE or recoverability in (
            IRRECOVERABLE,
            TIME_CRITICAL,
        ):
            priority = PRIORITY_HIGH
        elif recurrence_class == RECURRENCE_REPEATED_SUBJECT:
            priority = PRIORITY_MEDIUM
        else:
            priority = PRIORITY_LOW
        return priority, 5, priority == PRIORITY_HIGH
    raise D06ContractViolationError(
        f"unsupported resolved priority impact class: {impact_class!r}",
        "pre_medical_output_validation",
    )


# ---------------------------------------------------------------------------
# Audience validation primitives (frozen §10 matching algorithm)
# ---------------------------------------------------------------------------


def _audience_normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def audience_phrase_hits(strings: Sequence[str]) -> List[str]:
    """Forbidden phrase hits in frozen lexicon order."""
    normalized = [_audience_normalize(value) for value in strings]
    hits: List[str] = []
    for phrase in AUDIENCE_PHRASES:
        normalized_phrase = _audience_normalize(phrase)
        if normalized_phrase.isascii():
            needle = normalized_phrase.split()
            matched = False
            for text in normalized:
                tokens = re.sub(r"[^a-z0-9_]+", " ", text).split()
                if any(
                    tokens[index : index + len(needle)] == needle
                    for index in range(max(0, len(tokens) - len(needle) + 1))
                ):
                    matched = True
                    break
        else:
            matched = any(normalized_phrase in text for text in normalized)
        if matched:
            hits.append(phrase.casefold())
    return hits


def audience_visible_strings(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            result.extend(audience_visible_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(audience_visible_strings(item))
        return result
    return []


def audience_string_paths(value: Any, prefix: Tuple[str, ...] = ()) -> List[str]:
    if isinstance(value, str):
        return [".".join(prefix)]
    if isinstance(value, list):
        result: List[str] = []
        for index, item in enumerate(value):
            result.extend(audience_string_paths(item, prefix + (str(index),)))
        return result
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            result.extend(audience_string_paths(item, prefix + (str(key),)))
        return result
    return []


def audience_display_view(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Canonical display view of an audience payload (frozen §10)."""
    kind = payload.get("payload_kind")
    if kind == "journey":
        return {
            "display_text": payload.get("display_text"),
            "endpoint_lanes": payload.get("endpoint_lanes"),
            "visit_axis_label": payload.get("visit_axis_label"),
        }
    if kind == "query":
        return {
            "action_sentence": payload.get("action_sentence"),
            "basis_sentence": payload.get("basis_sentence"),
            "finding_sentence": payload.get("finding_sentence"),
        }
    if kind == "risk_label":
        return {
            "finding_summary": payload.get("finding_summary"),
            "jump_target": payload.get("jump_target"),
            "priority_label": payload.get("priority_label"),
            "risk_category": payload.get("risk_category"),
        }
    return dict(payload)


def attempted_display_view(value: Any) -> Any:
    """Recursive visible-string view used when no payload was emitted."""
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFKC", str(key)).casefold()
            if any(token in normalized_key for token in ("text", "label", "sentence")):
                result[str(key)] = item
            elif isinstance(item, (dict, list)):
                nested = attempted_display_view(item)
                if nested not in ({}, []):
                    result[str(key)] = nested
        return result
    if isinstance(value, list):
        result = [attempted_display_view(item) for item in value]
        return [item for item in result if item not in ({}, [])]
    return {}


def forbidden_audience_keys(value: Any) -> List[str]:
    """Forbidden display-key hits (``id``/``*_id``/``hash``/... rules)."""
    hits: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFKC", str(key)).casefold()
            if (
                normalized_key
                in {
                    "id",
                    "hash",
                    "ref",
                    "classifier",
                    "payload",
                    "lineage",
                    "backend",
                    "debug",
                    "log",
                    "confidence",
                }
                or normalized_key.endswith("_id")
                or normalized_key.endswith("_hash")
                or normalized_key.endswith("_ref")
            ):
                hits.append(str(key))
            hits.extend(forbidden_audience_keys(item))
    elif isinstance(value, list):
        for item in value:
            hits.extend(forbidden_audience_keys(item))
    return hits


def has_chinese(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(re.search(r"[\u3400-\u9fff]", value))


def validate_audience_payload_schema(payload: Mapping[str, Any]) -> str:
    """Validate a payload against the frozen per-kind schema.

    Returns the expected ``payload_schema_version``; raises
    :class:`AudiencePayloadValidationError` on any schema/content failure.
    """
    kind = payload.get("payload_kind")
    required = AUDIENCE_VALIDATOR_DEFINITION["payload_schemas"].get(kind)
    if required is None or sorted(payload) != required:
        raise AudiencePayloadValidationError(
            "audience payload schema/unknown fields mismatch"
        )
    expected_version = f"d06-{kind}-audience-v1"
    if payload.get("payload_schema_version") != expected_version:
        raise AudiencePayloadValidationError("audience payload schema version mismatch")
    if kind == "journey":
        if not has_chinese(payload.get("display_text", "")) or not has_chinese(
            payload.get("visit_axis_label", "")
        ):
            raise AudiencePayloadValidationError(
                "journey audience text must be nonempty Chinese"
            )
        lanes = payload.get("endpoint_lanes")
        if not isinstance(lanes, list) or not lanes:
            raise AudiencePayloadValidationError(
                "journey audience payload needs endpoint lane"
            )
        required_lane = ["endpoint_label", "marker_label", "source_jump_target"]
        for lane in lanes:
            if (
                not isinstance(lane, dict)
                or sorted(lane) != required_lane
                or any(
                    not isinstance(lane[field], str)
                    or not lane[field].strip()
                    or not has_chinese(lane[field])
                    for field in required_lane
                )
            ):
                raise AudiencePayloadValidationError(
                    "journey audience lane schema/content mismatch"
                )
    elif kind == "query":
        if payload.get("query_context") not in QUERY_CONTEXTS:
            raise AudiencePayloadValidationError("query audience context mismatch")
        for field, prefix in (
            ("basis_sentence", "依据："),
            ("finding_sentence", "发现："),
            ("action_sentence", "行动项："),
        ):
            value = payload.get(field)
            if (
                not isinstance(value, str)
                or not value.startswith(prefix)
                or not has_chinese(value)
            ):
                raise AudiencePayloadValidationError(
                    "query audience three-sentence schema/content mismatch"
                )
    else:
        for field in (
            "finding_summary",
            "jump_target",
            "priority_label",
            "risk_category",
        ):
            value = payload.get(field)
            if (
                not isinstance(value, str)
                or not value.strip()
                or not has_chinese(value)
            ):
                raise AudiencePayloadValidationError(
                    "risk-label audience schema/content mismatch"
                )
    return expected_version


# ---------------------------------------------------------------------------
# Immutable typed outcome surface
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D06PriorityResolverInput:
    """Content-addressed priority resolution input (contract §9.1)."""

    scope: Mapping[str, str]
    endpoint_definition_id: str
    stable_endpoint_key: str
    stable_timepoint_key: str
    endpoint_role: str
    impact_resolution_state: str
    impact_class: Optional[str]
    recurrence_class: str
    recoverability: str
    actionability: str
    monitoring_priority: str
    matched_precedence_step: int
    reason_codes: Tuple[str, ...]
    machine_close_forbidden: bool
    priority_policy_id: str
    priority_policy_version: str
    priority_policy_hash: str
    source_locator_ids: Tuple[str, ...]

    def to_plain(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = object_scope_fields(self.scope)
        payload.update(
            {
                "object_type": "D06PriorityResolverInput",
                "endpoint_definition_id": self.endpoint_definition_id,
                "stable_endpoint_key": self.stable_endpoint_key,
                "stable_timepoint_key": self.stable_timepoint_key,
                "endpoint_role": self.endpoint_role,
                "impact_resolution_state": self.impact_resolution_state,
                "impact_class": self.impact_class,
                "recurrence_class": self.recurrence_class,
                "recoverability": self.recoverability,
                "actionability": self.actionability,
                "monitoring_priority": self.monitoring_priority,
                "matched_precedence_step": self.matched_precedence_step,
                "reason_codes": list(self.reason_codes),
                "machine_close_forbidden": self.machine_close_forbidden,
                "priority_policy_id": self.priority_policy_id,
                "priority_policy_version": self.priority_policy_version,
                "priority_policy_hash": self.priority_policy_hash,
                "source_locator_ids": list(self.source_locator_ids),
            }
        )
        payload["hash"] = f"sha256:{d06_sha256_text(d06_canonical_json(payload))}"
        return payload

    @property
    def hash(self) -> str:  # noqa: A003 - domain field name
        return self.to_plain()["hash"]


@dataclass(frozen=True)
class D06PriorityDecision:
    """Emitted priority decision; only instantiated for risk units (§9.1)."""

    scope: Mapping[str, str]
    unit_id: str
    risk_id: str
    priority_decision_id: str
    endpoint_definition_id: str
    stable_endpoint_key: str
    stable_timepoint_key: str
    endpoint_role: str
    impact_resolution_state: str
    impact_class: Optional[str]
    recurrence_class: str
    recoverability: str
    actionability: str
    monitoring_priority: str
    matched_precedence_step: int
    reason_codes: Tuple[str, ...]
    machine_close_forbidden: bool
    priority_policy_id: str
    priority_policy_version: str
    priority_policy_hash: str
    priority_resolver_input_hash: str
    source_locator_ids: Tuple[str, ...]

    def to_plain(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = object_scope_fields(self.scope)
        payload.update(
            {
                "object_type": "D06PriorityDecision",
                "unit_id": self.unit_id,
                "risk_id": self.risk_id,
                "priority_decision_id": self.priority_decision_id,
                "endpoint_definition_id": self.endpoint_definition_id,
                "stable_endpoint_key": self.stable_endpoint_key,
                "stable_timepoint_key": self.stable_timepoint_key,
                "endpoint_role": self.endpoint_role,
                "impact_resolution_state": self.impact_resolution_state,
                "impact_class": self.impact_class,
                "recurrence_class": self.recurrence_class,
                "recoverability": self.recoverability,
                "actionability": self.actionability,
                "monitoring_priority": self.monitoring_priority,
                "matched_precedence_step": self.matched_precedence_step,
                "reason_codes": list(self.reason_codes),
                "machine_close_forbidden": self.machine_close_forbidden,
                "priority_policy_id": self.priority_policy_id,
                "priority_policy_version": self.priority_policy_version,
                "priority_policy_hash": self.priority_policy_hash,
                "priority_resolver_input_hash": self.priority_resolver_input_hash,
                "source_locator_ids": list(self.source_locator_ids),
            }
        )
        payload["lineage_hash"] = (
            f"sha256:{d06_sha256_text(d06_canonical_json(payload))}"
        )
        return payload

    @property
    def lineage_hash(self) -> str:  # noqa: A003 - domain field name
        return self.to_plain()["lineage_hash"]


@dataclass(frozen=True)
class D06UnitStableCore:
    """Materialized stable-core tuple of a D06 obligation (§4.4)."""

    unit_id: str
    domain_id: str
    classifier: str
    unit_kind: str
    stable_endpoint_key: str
    stable_instrument_key_or_none: str
    stable_timepoint_key: str
    stable_item_or_component_key_or_none: str
    stable_source_record_id: str
    temporal_window: Tuple[str, str]
    rule_or_knowledge_lineage: str

    def to_plain(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "object_type": "D06UnitStableCore",
            "unit_id": self.unit_id,
            "domain_id": self.domain_id,
            "classifier": self.classifier,
            "unit_kind": self.unit_kind,
            "stable_endpoint_key": self.stable_endpoint_key,
            "stable_instrument_key_or_none": self.stable_instrument_key_or_none,
            "stable_timepoint_key": self.stable_timepoint_key,
            "stable_item_or_component_key_or_none": (
                self.stable_item_or_component_key_or_none
            ),
            "stable_source_record_id": self.stable_source_record_id,
            "temporal_window": list(self.temporal_window),
            "rule_or_knowledge_lineage": self.rule_or_knowledge_lineage,
        }
        payload["hash"] = f"sha256:{d06_sha256_text(d06_canonical_json(payload))}"
        return payload

    @property
    def hash(self) -> str:  # noqa: A003 - domain field name
        return self.to_plain()["hash"]

    @property
    def normalized_concept(self) -> List[str]:
        return [
            self.classifier,
            self.unit_kind,
            self.stable_endpoint_key,
            self.stable_instrument_key_or_none,
            self.stable_timepoint_key,
            self.stable_item_or_component_key_or_none,
        ]


@dataclass(frozen=True)
class PublicR4RiskIdentity:
    """Public R4 risk identity for a positive D06 root (§4.4)."""

    project_ref: str
    domain_id: str
    scope_type: str
    scope_key: Tuple[str, str, str]
    stable_source_or_event_identity: str
    normalized_concept: Tuple[str, ...]
    temporal_window: Tuple[str, str]
    rule_or_knowledge_lineage: str
    public_identity_version: str
    risk_id: str
    unit_id: str
    scope_binding_id: str
    cutoff: str

    def canonical_tuple(self) -> List[Any]:
        return [
            self.project_ref,
            self.domain_id,
            self.scope_type,
            list(self.scope_key),
            self.stable_source_or_event_identity,
            list(self.normalized_concept),
            list(self.temporal_window),
            self.rule_or_knowledge_lineage,
            self.public_identity_version,
            self.risk_id,
            self.unit_id,
            self.scope_binding_id,
            self.cutoff,
        ]

    @property
    def public_identity_hash(self) -> str:
        return f"sha256:{d06_sha256_text(d06_canonical_json(self.canonical_tuple()))}"

    @property
    def public_r4_risk_identity_id(self) -> str:
        digest = self.public_identity_hash[-16:]
        return f"R4ID-{digest}"

    def to_plain(self) -> Dict[str, Any]:
        return {
            "object_type": "PublicR4RiskIdentity",
            "project_ref": self.project_ref,
            "domain_id": self.domain_id,
            "scope_type": self.scope_type,
            "scope_key": list(self.scope_key),
            "stable_source_or_event_identity": self.stable_source_or_event_identity,
            "normalized_concept": list(self.normalized_concept),
            "temporal_window": list(self.temporal_window),
            "rule_or_knowledge_lineage": self.rule_or_knowledge_lineage,
            "public_identity_version": self.public_identity_version,
            "risk_id": self.risk_id,
            "unit_id": self.unit_id,
            "scope_binding_id": self.scope_binding_id,
            "cutoff": self.cutoff,
            "subject_ref": self.scope_key[0],
            "site_ref": self.scope_key[1],
            "episode_key": self.scope_key[2],
            "stable_endpoint_key": self.normalized_concept[2],
            "stable_timepoint_key": self.normalized_concept[4],
            "canonical_tuple": self.canonical_tuple(),
            "public_identity_hash": self.public_identity_hash,
            "public_r4_risk_identity_id": self.public_r4_risk_identity_id,
        }


@dataclass(frozen=True)
class D06RiskBinding:
    """Bidirectional risk binding for a positive D06 root (§4.4)."""

    scope: Mapping[str, str]
    unit_id: str
    risk_id: str
    classifier: str
    primary_subtype: str
    priority_decision_id: str
    public_r4_risk_identity_id: str
    r2_lifecycle_ref: str
    source_locator_ids: Tuple[str, ...]

    def to_plain(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = object_scope_fields(self.scope)
        payload.update(
            {
                "object_type": "D06RiskBinding",
                "unit_id": self.unit_id,
                "risk_id": self.risk_id,
                "classifier": self.classifier,
                "primary_subtype": self.primary_subtype,
                "priority_decision_id": self.priority_decision_id,
                "public_r4_risk_identity_id": self.public_r4_risk_identity_id,
                "R2_lifecycle_ref": self.r2_lifecycle_ref,
                "source_locator_ids": list(self.source_locator_ids),
            }
        )
        payload["lineage_hash"] = (
            f"sha256:{d06_sha256_text(d06_canonical_json(payload))}"
        )
        return payload

    @property
    def lineage_hash(self) -> str:  # noqa: A003 - domain field name
        return self.to_plain()["lineage_hash"]


@dataclass(frozen=True)
class D06AudienceValidationResult:
    """Audience payload validation result (contract §10)."""

    payload_schema: bool
    payload_schema_version: str
    validator_version: str
    validator_hash: str
    lexicon_version: str
    forbidden_lexicon_hash: str
    forbidden_fragment_hits: Tuple[str, ...]
    validated_display_string_paths: Tuple[str, ...]
    validation_state: str
    audience_payload_absent: bool

    def to_plain(self) -> Dict[str, Any]:
        return {
            "payload_schema": self.payload_schema,
            "payload_schema_version": self.payload_schema_version,
            "validator_version": self.validator_version,
            "validator_hash": self.validator_hash,
            "lexicon_version": self.lexicon_version,
            "forbidden_lexicon_hash": self.forbidden_lexicon_hash,
            "forbidden_fragment_hits": list(self.forbidden_fragment_hits),
            "validated_display_string_paths": list(self.validated_display_string_paths),
            "validation_state": self.validation_state,
            "audience_payload_absent": self.audience_payload_absent,
        }


# L2 counted object types (contract §12).
L2_CLUES = "clues"
L2_COVERAGE_NOTICES = "coverage_notices"
L2_QUERIES = "queries"
L2_RISKS = "risks"
L2_COUNT_KEYS: Tuple[str, ...] = (
    L2_CLUES,
    L2_COVERAGE_NOTICES,
    L2_QUERIES,
    L2_RISKS,
)

# Required trace edges (contract §12.1 / manifest contract).
TRACE_RULE_LINEAGE = "rule_lineage"
TRACE_SCOPE_BINDING = "scope_binding"
TRACE_SOURCE_LOCATOR = "source_locator"
TRACE_EDGES_ALL: Tuple[str, ...] = (
    TRACE_RULE_LINEAGE,
    TRACE_SCOPE_BINDING,
    TRACE_SOURCE_LOCATOR,
)


@dataclass(frozen=True)
class D06ChallengeOutcome:
    """Typed outcome produced by every D06 entrypoint (§12.1).

    The plain serialization carries the exact frozen expected-outcome
    shape so the challenge DSL can assert every leaf.
    """

    invoked_entrypoint: str
    input_scope_hash: str
    output_kind: str
    coverage_status: Optional[str]
    gate_state: Optional[str]
    gate_disposition: Optional[str]
    l1_disposition: Optional[str]
    primary_subtype: Optional[str]
    secondary_reason_codes: Tuple[str, ...] = ()
    l2_counts: Mapping[str, int] = field(
        default_factory=lambda: {key: 0 for key in L2_COUNT_KEYS}
    )
    l3_state: Optional[str] = None
    l3_transition: Optional[str] = None
    object_ids: Mapping[str, str] = field(default_factory=dict)
    object_hashes: Mapping[str, Any] = field(default_factory=dict)
    trace_edges: Tuple[str, ...] = ()
    audience_payload: Optional[Mapping[str, Any]] = None
    audience_payload_absent: bool = False
    audience_validation_result: Optional[D06AudienceValidationResult] = None
    audience_validation_state: Optional[str] = None
    domain_assertions: Mapping[str, Any] = field(default_factory=dict)
    error_type: Optional[str] = None
    error_stage: Optional[str] = None
    payload_hash: Optional[str] = None

    def to_plain(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "invoked_entrypoint": self.invoked_entrypoint,
            "input_scope_hash": self.input_scope_hash,
            "output_kind": self.output_kind,
            "coverage_status": self.coverage_status,
            "gate_state": self.gate_state,
            "gate_disposition": self.gate_disposition,
            "l1_disposition": self.l1_disposition,
            "primary_subtype": self.primary_subtype,
            "l2_counts": (
                {key: self.l2_counts.get(key, 0) for key in L2_COUNT_KEYS}
                if self.output_kind != OUTPUT_KIND_ERROR
                else None
            ),
            "l3_state": self.l3_state,
            "l3_transition": self.l3_transition,
            "object_hashes": dict(self.object_hashes),
            "trace_edges": sorted(self.trace_edges),
            "domain_assertions": dict(self.domain_assertions),
            "error_type": self.error_type,
            "error_stage": self.error_stage,
        }
        if self.audience_validation_result is not None:
            payload["audience_validation_result"] = (
                self.audience_validation_result.to_plain()
            )
            payload["audience_payload_absent"] = self.audience_payload_absent
        payload["audience_validation_state"] = self.audience_validation_state
        if self.audience_payload is not None:
            payload["audience_payload"] = dict(self.audience_payload)
        if self.secondary_reason_codes:
            payload["secondary_reason_codes"] = list(self.secondary_reason_codes)
        if self.object_ids:
            payload["object_ids"] = dict(self.object_ids)
        if self.payload_hash is not None:
            payload["payload_hash"] = self.payload_hash
        return payload


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------


def scope_identity_matches(obj: Mapping[str, Any], scope: Mapping[str, Any]) -> bool:
    """Exact identity match on the frozen scope identity fields."""
    for identity_field in SCOPE_IDENTITY_FIELDS:
        if obj.get(identity_field) != scope.get(identity_field):
            return False
    return True


def scope_all_matches(obj: Mapping[str, Any], scope: Mapping[str, Any]) -> bool:
    for identity_field in SCOPE_ALL_FIELDS:
        if obj.get(identity_field) != scope.get(identity_field):
            return False
    return True


def plain_value_hash(value: Any) -> str:
    """Hex sha256 of a canonical payload."""
    return d06_content_hash(value)


def deep_freeze(value: Any) -> Any:
    """Recursively freeze mappings and sequences into immutable structures.

    Dicts become ``MappingProxyType`` wrappers, lists/tuples become tuples,
    so post-construction mutation of any nested source (scope, definitions,
    records, bindings, policies, registries, raw fixture) can never change
    a runtime input or its derived outcome.
    """
    if isinstance(value, Mapping):
        return MappingProxyType({key: deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(deep_freeze(item) for item in value)
    return value


def deep_unfreeze(value: Any) -> Any:
    """Convert a deep-frozen structure back to plain JSON-able values."""
    if isinstance(value, Mapping):
        return {str(key): deep_unfreeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [deep_unfreeze(item) for item in value]
    return value


def object_scope_fields(scope: Mapping[str, str]) -> Dict[str, str]:
    """Scope subset carried by D06 identity/decision objects.

    Matches the frozen objects: the identity fields plus ``cutoff``; the
    run-level ``snapshot_as_of`` never enters these objects.
    """
    payload: Dict[str, str] = {
        field: scope[field] for field in SCOPE_IDENTITY_FIELDS if field in scope
    }
    payload["cutoff"] = scope["clinical_event_cutoff"]
    return payload
