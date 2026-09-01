"""R4-D07 clinical safety / laboratory / examination slice -- domain model.

Implements the frozen D07 typed contract (``medical_monitoring_r4_d07_
safety_laboratory_slice_contract_v1_20260813.md``, semantic hash
``6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a``) as a
closed typed-input runtime.  The module owns:

* the frozen typed enumerations (L1 dispositions, orthogonal semantics,
  positive subtypes, follow-up states, trend/pattern/examination states,
  integrity stages and closed error classes);
* deterministic canonical JSON and content addressing
  (``sha256(canonical_json(all typed fields except own hash))``);
* exact-key typed schema validation of every D07 typed object
  (``d07-typed-input-v1`` container and all section objects);
* the pre-evaluator integrity failure model.

The runtime never reads the challenge catalog, oracle, manifest or registry,
and never branches on case/test/fixture identifiers or expected text.  All
data is synthetic and offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any, Dict, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# Frozen contract identity (v0.4, accepted)
# ---------------------------------------------------------------------------

D07_SCHEMA_VERSION = "1.0.0"
D07_TYPED_INPUT_SCHEMA = "d07-typed-input-v1"

# Contract semantic hash (frozen; covers Status/Scope header through §15).
D07_CONTRACT_SEMANTIC_HASH = (
    "6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a"
)
D07_CONTRACT_STATUS = "REVISED_DRAFT_V0_4_FOR_INDEPENDENT_REVIEW"

# ---------------------------------------------------------------------------
# Canonical serialization and content addressing (v0.4 §5)
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


def d07_canonical_json(value: Any) -> str:
    """Deterministic D07 canonical JSON (NFC, sorted keys, compact)."""
    return json.dumps(
        _normalize_nfc(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def d07_sha256_text(text: str) -> str:
    """SHA-256 of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def d07_content_hash(value: Any) -> str:
    """Content address of any JSON-able value (hex sha256 of canonical JSON)."""
    return d07_sha256_text(d07_canonical_json(value))


def d07_content_hash_prefixed(value: Any) -> str:
    """Content address with the ``sha256:`` prefix (producer refs)."""
    return "sha256:" + d07_content_hash(value)


def is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


# ---------------------------------------------------------------------------
# Integrity failure model (v0.4 §14.1)
# ---------------------------------------------------------------------------

INTEGRITY_STAGES: Tuple[str, ...] = (
    "schema_parse",
    "canonical_hash",
    "artifact_hash",
    "contract_semantic_hash",
    "scope_cutoff",
    "authority_version",
    "correction_chain",
    "identity_duplicate",
    "foreign_key_bijection",
    "d05_gate_applicability",
    "evaluator_admission",
)

INTEGRITY_ERROR_CLASSES: Tuple[str, ...] = (
    "schema_error",
    "stale_hash",
    "artifact_mismatch",
    "semantic_hash_mismatch",
    "scope_mismatch",
    "out_of_cutoff",
    "authority_mismatch",
    "correction_ambiguous",
    "identity_ambiguous",
    "duplicate_identity",
    "foreign_key_error",
    "bijection_error",
    "open_d05_gate",
    "applicability_unresolved",
    "evaluator_not_admitted",
)


class D07IntegrityError(Exception):
    """Pre-evaluator integrity failure (first failure aborts the pipeline).

    ``stage`` is the frozen stage name, ``error_type`` the closed error class,
    ``error_object`` the exact typed-input locator (``section[index]``) that
    failed.  A failure must never produce medical/priority/risk/Query/Journey
    output.
    """

    def __init__(self, stage: str, error_type: str, error_object: str):
        if stage not in INTEGRITY_STAGES:
            raise ValueError(f"unknown integrity stage {stage!r}")
        if error_type not in INTEGRITY_ERROR_CLASSES:
            raise ValueError(f"unknown integrity error class {error_type!r}")
        super().__init__(f"{stage}:{error_type}:{error_object}")
        self.stage = stage
        self.error_type = error_type
        self.error_object = error_object


class D07ContractError(Exception):
    """Non-integrity contract violation inside the runtime (internal)."""


# ---------------------------------------------------------------------------
# Frozen typed enumerations (v0.4)
# ---------------------------------------------------------------------------


class L1Disposition:
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (POSITIVE, NEGATIVE, BOUNDARY, NOT_APPLICABLE, NOT_EVALUABLE)


class PositiveSubtype:
    NEW_ABNORMALITY = "new_abnormality"
    BASELINE_ABNORMAL_WORSENING = "baseline_abnormal_worsening"
    GRADE_OR_MAGNITUDE_WORSENING = "grade_or_magnitude_worsening"
    PERSISTENT_OR_RECURRENT = "persistent_or_recurrent_abnormality"
    CS_INCONSISTENCY = "clinical_significance_inconsistency"
    MISSING_REPEAT_OR_FOLLOWUP = "missing_repeat_or_followup"
    MEDICAL_ACTION_INCONSISTENCY = "medical_action_inconsistency"
    AE_RECORDING_HANDOFF_CLUE = "ae_recording_handoff_clue"
    PROTOCOL_OR_IB_ACTION_GAP = "protocol_or_ib_action_gap"
    ORGAN_PATTERN_CLUE = "organ_pattern_clue"
    EXAM_INTERPRETATION_INCONSISTENCY = "exam_interpretation_inconsistency"
    SOURCE_OR_CORRECTION_INCONSISTENCY = "source_or_correction_inconsistency"
    ALL: Tuple[str, ...] = (
        NEW_ABNORMALITY,
        BASELINE_ABNORMAL_WORSENING,
        GRADE_OR_MAGNITUDE_WORSENING,
        PERSISTENT_OR_RECURRENT,
        CS_INCONSISTENCY,
        MISSING_REPEAT_OR_FOLLOWUP,
        MEDICAL_ACTION_INCONSISTENCY,
        AE_RECORDING_HANDOFF_CLUE,
        PROTOCOL_OR_IB_ACTION_GAP,
        ORGAN_PATTERN_CLUE,
        EXAM_INTERPRETATION_INCONSISTENCY,
        SOURCE_OR_CORRECTION_INCONSISTENCY,
    )


class ReferenceRangeState:
    LOW = "low"
    WITHIN_RANGE = "within_range"
    HIGH = "high"
    NOT_CLASSIFIABLE = "not_classifiable"
    BOUNDARY = "boundary"
    ALL: Tuple[str, ...] = (LOW, WITHIN_RANGE, HIGH, NOT_CLASSIFIABLE, BOUNDARY)


class GradeState:
    GRADED = "graded"
    NOT_GRADED = "not_graded"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (GRADED, NOT_GRADED, NOT_APPLICABLE, NOT_EVALUABLE)


class ClinicalSignificance:
    CS = "CS"
    NCS = "NCS"
    UNKNOWN = "unknown"
    NOT_COLLECTED = "not_collected"
    UNMAPPED = "unmapped"
    ALL: Tuple[str, ...] = (CS, NCS, UNKNOWN, NOT_COLLECTED, UNMAPPED)


class SeriousnessClue:
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    ALL: Tuple[str, ...] = (PRESENT, ABSENT, UNKNOWN)


class MonitoringPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"
    ALL: Tuple[str, ...] = (LOW, MEDIUM, HIGH, UNKNOWN)


class UnitKind:
    OBSERVATION_INTERPRETATION = "observation_interpretation"
    FOLLOWUP_OBLIGATION = "followup_obligation"
    ORGAN_PATTERN = "organ_pattern"
    ALL: Tuple[str, ...] = (OBSERVATION_INTERPRETATION, FOLLOWUP_OBLIGATION, ORGAN_PATTERN)


class TrendKind:
    NEW_ABNORMALITY = "new_abnormality"
    BASELINE_ABNORMAL_WORSENING = "baseline_abnormal_worsening"
    PERSISTENT = "persistent"
    RECURRENT = "recurrent"
    RECOVERED = "recovered"
    STABLE_ABNORMAL = "stable_abnormal"
    STABLE_NORMAL = "stable_normal"
    FLUCTUATING = "fluctuating"
    INSUFFICIENT_POINTS = "insufficient_points"
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        NEW_ABNORMALITY,
        BASELINE_ABNORMAL_WORSENING,
        PERSISTENT,
        RECURRENT,
        RECOVERED,
        STABLE_ABNORMAL,
        STABLE_NORMAL,
        FLUCTUATING,
        INSUFFICIENT_POINTS,
        BOUNDARY,
        NOT_EVALUABLE,
    )


class RepeatState:
    NOT_REQUIRED = "not_required"
    REQUIRED_MET = "required_met"
    REQUIRED_MISSING = "required_missing"
    WRONG_WINDOW = "wrong_window"
    WRONG_MEASURE_OR_METHOD = "wrong_measure_or_method"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        NOT_REQUIRED,
        REQUIRED_MET,
        REQUIRED_MISSING,
        WRONG_WINDOW,
        WRONG_MEASURE_OR_METHOD,
        NOT_EVALUABLE,
    )


class ActionState:
    NOT_REQUIRED = "not_required"
    REQUIRED_MET = "required_met"
    REQUIRED_MISSING = "required_missing"
    DISCORDANT = "discordant"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        NOT_REQUIRED,
        REQUIRED_MET,
        REQUIRED_MISSING,
        DISCORDANT,
        NOT_EVALUABLE,
    )


class ExplanationState:
    NOT_REQUIRED = "not_required"
    DOCUMENTED_CONSISTENT = "documented_consistent"
    DOCUMENTED_INCONSISTENT = "documented_inconsistent"
    MISSING = "missing"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        NOT_REQUIRED,
        DOCUMENTED_CONSISTENT,
        DOCUMENTED_INCONSISTENT,
        MISSING,
        NOT_EVALUABLE,
    )


class AERecordState:
    NOT_EXPECTED = "not_expected"
    MATCHING_RECORD_PRESENT = "matching_record_present"
    HANDOFF_REQUIRED = "handoff_required"
    AMBIGUOUS = "ambiguous"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        NOT_EXPECTED,
        MATCHING_RECORD_PRESENT,
        HANDOFF_REQUIRED,
        AMBIGUOUS,
        NOT_EVALUABLE,
    )


class TemporalMatchState:
    MATCHED = "matched"
    OUTSIDE_WINDOW = "outside_window"
    PRECISION_INSUFFICIENT = "precision_insufficient"
    CONFLICTED = "conflicted"
    ALL: Tuple[str, ...] = (MATCHED, OUTSIDE_WINDOW, PRECISION_INSUFFICIENT, CONFLICTED)


class InterpretationState:
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (CONSISTENT, INCONSISTENT, BOUNDARY, NOT_EVALUABLE)


class CSConsistencyState:
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (CONSISTENT, INCONSISTENT, BOUNDARY, NOT_EVALUABLE)


class PatternState:
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (MATCHED, NOT_MATCHED, BOUNDARY, NOT_EVALUABLE)


class TemporalCooccurrenceState:
    MATCHED = "matched"
    OUTSIDE_WINDOW = "outside_window"
    PRECISION_INSUFFICIENT = "precision_insufficient"
    CONFLICTED = "conflicted"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (MATCHED, OUTSIDE_WINDOW, PRECISION_INSUFFICIENT, CONFLICTED, NOT_EVALUABLE)


class D07Action:
    EVALUATE_AND_OWN = "evaluate_and_own"
    HANDOFF_ONLY = "handoff_only"
    CONTEXT_ONLY = "context_only"
    NOT_APPLICABLE = "not_applicable"
    ALL: Tuple[str, ...] = (EVALUATE_AND_OWN, HANDOFF_ONLY, CONTEXT_ONLY, NOT_APPLICABLE)


class RecordStatus:
    ACCEPTED_CURRENT = "accepted_current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    OUT_OF_CUTOFF = "out_of_cutoff"
    ALL: Tuple[str, ...] = (ACCEPTED_CURRENT, SUPERSEDED, WITHDRAWN, PENDING, OUT_OF_CUTOFF)


class RangeKind:
    LOWER_ONLY = "lower_only"
    UPPER_ONLY = "upper_only"
    CLOSED_INTERVAL = "closed_interval"
    CATEGORICAL = "categorical"
    ALL: Tuple[str, ...] = (LOWER_ONLY, UPPER_ONLY, CLOSED_INTERVAL, CATEGORICAL)


class ResultKind:
    NUMERIC = "numeric"
    ORDINAL = "ordinal"
    CATEGORICAL = "categorical"
    TEXT = "text"
    INTERVAL = "interval"
    ALL: Tuple[str, ...] = (NUMERIC, ORDINAL, CATEGORICAL, TEXT, INTERVAL)


class TimePrecision:
    DATETIME = "datetime"
    DATE = "date"
    MONTH = "month"
    YEAR = "year"
    UNKNOWN = "unknown"
    ALL: Tuple[str, ...] = (DATETIME, DATE, MONTH, YEAR, UNKNOWN)


class TimezoneState:
    PROVIDED = "provided"
    REQUIRED_MISSING = "required_missing"
    NOT_APPLICABLE = "not_applicable"
    ALL: Tuple[str, ...] = (PROVIDED, REQUIRED_MISSING, NOT_APPLICABLE)


class RangeSelectionState:
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (BOUNDARY, NOT_EVALUABLE)


class GradeComparisonState:
    MATCH = "match"
    MISMATCH = "mismatch"
    REPORTED_ONLY = "reported_only"
    RECOMPUTED_ONLY = "recomputed_only"
    BOTH_NOT_APPLICABLE = "both_not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (
        MATCH,
        MISMATCH,
        REPORTED_ONLY,
        RECOMPUTED_ONLY,
        BOTH_NOT_APPLICABLE,
        NOT_EVALUABLE,
    )


class ApplicabilityValue:
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    BOUNDARY = "boundary"
    NOT_EVALUABLE = "not_evaluable"
    ALL: Tuple[str, ...] = (APPLICABLE, NOT_APPLICABLE, BOUNDARY, NOT_EVALUABLE)


class LifecycleTransition:
    NEW_RISK = "new_risk"
    CARRY_FORWARD = "carry_forward"
    CLOSED = "closed"
    REOPENED = "reopened"
    NONE = "none"
    ALL: Tuple[str, ...] = (NEW_RISK, CARRY_FORWARD, CLOSED, REOPENED, NONE)


# Unit algorithm versions (stable identity dimension).
UNIT_ALGORITHM_VERSIONS = {
    UnitKind.OBSERVATION_INTERPRETATION: "d07-observation-interpretation-v1",
    UnitKind.FOLLOWUP_OBLIGATION: "d07-followup-obligation-v1",
    UnitKind.ORGAN_PATTERN: "d07-organ-pattern-v1",
}

# ---------------------------------------------------------------------------
# Exact-key typed schemas (v0.4 §5: unknown key, missing required key,
# out-of-enum value, wrong object type or embedded hash mismatch fail closed
# before medical evaluation)
# ---------------------------------------------------------------------------
#
# Every section object is validated against an exact key set.  ``required``
# keys must be present; ``optional`` keys may be present; any other key fails.
# Type/constraint checks are applied per key via ``_check_object``.

_STR = "str"
_STR_OR_NULL = "str|null"
_STR_LIST = "str_list"
_INT = "int"
_BOOL = "bool"
_BOOL_LIST = "bool_list"
_STR_LIST_LIST = "str_list_list"
_DEC = "decimal"  # canonical decimal string
_DEC_LIST = "decimal_list"
_DEC_OR_NULL = "decimal|null"
_BOOL_OR_NULL = "bool|null"


# key -> (kind, enum-or-None)
# Each spec entry: key -> (kind, enum).  ``_SPEC_REQUIRED`` holds the required
# key specs, ``_SPEC_OPTIONAL`` the optional key specs for each object type.
_SPEC_REQUIRED: Dict[str, Dict[str, Tuple[str, Optional[Tuple[str, ...]]]]] = {}
_SPEC_OPTIONAL: Dict[str, Dict[str, Tuple[str, Optional[Tuple[str, ...]]]]] = {}


def _spec(name: str, required: Mapping[str, Tuple[str, Optional[Tuple[str, ...]]]],
          optional: Optional[Mapping[str, Tuple[str, Optional[Tuple[str, ...]]]]] = None) -> None:
    _SPEC_REQUIRED[name] = dict(required)
    _SPEC_OPTIONAL[name] = dict(optional or {})


def _spec_merged(name: str) -> Dict[str, Tuple[str, Optional[Tuple[str, ...]]]]:
    merged = dict(_SPEC_REQUIRED.get(name, {}))
    merged.update(_SPEC_OPTIONAL.get(name, {}))
    return merged


def _enum(*values: str) -> Tuple[str, ...]:
    return values


# --- run scope binding / previous run scope binding ---
_RUN_SCOPE_REQ = {
    "scope_binding_id": (_STR, None),
    "project_ref": (_STR, None),
    "run_ref": (_STR, None),
    "monitoring_mode": (_STR, _enum("full", "focused")),
    "source_revision": (_STR, None),
    "accepted_snapshot_ref": (_STR, None),
    "snapshot_as_of": (_STR, None),
    "clinical_event_cutoff": (_STR, None),
    "protocol_version": (_STR, None),
    "ib_rsi_version": (_STR, None),
    "lab_manual_version": (_STR, None),
    "mapping_version": (_STR, None),
    "unit_dictionary_version": (_STR, None),
    "rule_set_versions": ("dict", None),
    "source_locator_ids": (_STR_LIST, None),
    "lineage_hash": (_STR, None),
}
_spec("run_scope_binding", _RUN_SCOPE_REQ)
_spec("previous_run_scope_binding", _RUN_SCOPE_REQ)

# --- authority bindings ---
_spec("authority_bindings", {
    "authority_binding_id": (_STR, None),
    "claim_kind": (_STR, _enum("lab_manual", "reference_range", "grade_ruleset",
                               "unit_dictionary", "collection_scope")),
    "candidate_authority_ids": (_STR_LIST, None),
    "selected_authority_id": (_STR_OR_NULL, None),
    "selected_version": (_STR_OR_NULL, None),
    "decision_status": (_STR, _enum("unique", "boundary", "not_evaluable")),
    "effective_interval": (_STR_LIST, None),
    "scope_predicate_results": (_BOOL_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- cutoff decisions ---
_spec("cutoff_decisions", {
    "cutoff_decision_id": (_STR, None),
    "record_time_ref_id": (_STR, None),
    "run_cutoff_time_ref_id": (_STR, None),
    "d05_cutoff_policy_id": (_STR, None),
    "d05_cutoff_policy_version": (_STR, None),
    "d05_cutoff_policy_hash": (_STR, None),
    "normalized_record_interval": (_STR_LIST, None),
    "normalized_cutoff_instant": (_STR, None),
    "comparison": (_STR, _enum("before", "at", "after", "overlaps", "precision_insufficient")),
    "admitted": (_BOOL, None),
    "decision": (_STR, _enum("within_cutoff", "out_of_cutoff", "boundary", "not_evaluable")),
    "reason_codes": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- time refs ---
_spec("time_refs", {
    "time_ref_id": (_STR, None),
    "precision": (_STR, TimePrecision.ALL),
    "timezone_state": (_STR, TimezoneState.ALL),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "value": (_STR_OR_NULL, None),
    "timezone": (_STR_OR_NULL, None),
})
_spec("previous_time_refs", _spec_merged("time_refs"))

# --- scope envelopes ---
_spec("scope_envelopes", {
    "envelope_id": (_STR, None),
    "record_id": (_STR, None),
    "record_status": (_STR, RecordStatus.ALL),
    "project_ref": (_STR, None),
    "run_ref": (_STR, None),
    "monitoring_mode": (_STR, _enum("full", "focused")),
    "scope_type": (_STR, _enum("subject")),
    "scope_key": (_STR, None),
    "subject_ref": (_STR, None),
    "site_ref": (_STR, None),
    "domain_id": (_STR, None),
    "episode_key": (_STR, None),
    "source_revision": (_STR, None),
    "accepted_snapshot_ref": (_STR, None),
    "cutoff": (_STR, None),
    "observed_time_ref": (_STR, None),
    "scope_binding_id": (_STR, None),
    "authority_binding_id": (_STR, None),
    "record_content_hash": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
}, optional={
    "supersedes_record_id": (_STR_OR_NULL, None),
    "correction_reason": (_STR_OR_NULL, None),
})
_spec("previous_scope_envelopes", _SPEC_REQUIRED["scope_envelopes"],
      _SPEC_OPTIONAL["scope_envelopes"])

# --- correction chain decisions ---
_spec("correction_chain_decisions", {
    "decision_id": (_STR, None),
    "stable_source_record_id": (_STR, None),
    "candidate_record_ids": (_STR_LIST, None),
    "accepted_current_record_id": (_STR_OR_NULL, None),
    "branch_state": (_STR, _enum("linear", "forked", "broken", "ambiguous")),
    "supersession_edges": ("str_2d_list", None),
    "cutoff_decision": ("dict|null", None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- measure definitions ---
_spec("measure_definitions", {
    "definition_id": (_STR, None),
    "stable_measure_key": (_STR, None),
    "version": (_STR, None),
    "domain": (_STR, _enum("LB", "VS", "EG", "PE", "IMAGING", "OTHER")),
    "audience_name": (_STR, None),
    "result_kind": (_STR, ResultKind.ALL),
    "allowed_result_kinds": (_STR_LIST, None),
    "applicability_rule_id": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "definition_hash": (_STR, None),
}, optional={
    "expected_unit_dimension": (_STR_OR_NULL, None),
})

# --- reference range definitions ---
_spec("reference_range_definitions", {
    "range_definition_id": (_STR, None),
    "stable_measure_key": (_STR, None),
    "version": (_STR, None),
    "range_kind": (_STR, RangeKind.ALL),
    "sex": (_STR, _enum("male", "female", "intersex", "unknown", "not_applicable")),
    "effective_interval": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "lower": (_DEC_OR_NULL, None),
    "upper": (_DEC_OR_NULL, None),
    "lower_inclusive": (_BOOL_OR_NULL, None),
    "upper_inclusive": (_BOOL_OR_NULL, None),
    "allowed_categories": (_STR_LIST, None),
    "age_interval": (_STR_LIST, None),
    "unit": (_STR_OR_NULL, None),
})

# --- unit conversion rules ---
_spec("unit_conversion_rules", {
    "conversion_rule_id": (_STR, None),
    "version": (_STR, None),
    "from_unit": (_STR, None),
    "to_unit": (_STR, None),
    "dimension": (_STR, None),
    "formula": (_STR, _enum("factor", "affine")),
    "multiplier": (_DEC, None),
    "numeric_policy_id": (_STR_OR_NULL, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "addend": (_DEC_OR_NULL, None),
    "applicability": (_STR_OR_NULL, None),
})

# --- grade rule sets + grade rules ---
_spec("grade_rule_sets", {
    "rule_set_id": (_STR, None),
    "name": (_STR, None),
    "version": (_STR, None),
    "kind": (_STR, _enum("CTCAE", "protocol", "ib", "project")),
    "ordered_grade_rule_ids": (_STR_LIST, None),
    "grade_domain": (_STR, None),
    "endpoint_inclusivity": (_STR, _enum("documented", "boundary")),
    "missing_input_outcome": (_STR, _enum("not_evaluable", "not_graded", "not_applicable")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "stable_measure_key": (_STR_OR_NULL, None),
    "term_code": (_STR_OR_NULL, None),
})
_spec("grade_rules", {
    "grade_rule_id": (_STR, None),
    "sequence": (_INT, None),
    "grade": (_STR, None),
    "comparator": (_STR, _enum("lt", "le", "eq", "ge", "gt", "between", "outside",
                              "categorical_equals")),
    "left_operand": (_STR, _enum("value", "ratio_to_uln", "ratio_to_lln",
                                 "change_from_baseline", "category")),
    "required_context_fields": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "lower": (_DEC_OR_NULL, None),
    "upper": (_DEC_OR_NULL, None),
    "lower_inclusive": (_BOOL_OR_NULL, None),
    "upper_inclusive": (_BOOL_OR_NULL, None),
    "categorical_value": (_STR_OR_NULL, None),
})

# --- monitoring rules + predicates ---
_spec("monitoring_rules", {
    "rule_id": (_STR, None),
    "version": (_STR, None),
    "rule_kind": (_STR, _enum("repeat", "action", "organ_pattern",
                              "clinical_significance", "other")),
    "applicable_measure_keys": (_STR_LIST, None),
    "ordered_predicate_ids": (_STR_LIST, None),
    "temporal_window": (_STR_LIST, None),
    "required_followup_roles": (_STR_LIST, None),
    "owner_route": (_STR, D07Action.ALL),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "priority_floor": (_STR_OR_NULL, MonitoringPriority.ALL),
})
_spec("monitoring_predicates", {
    "predicate_id": (_STR, None),
    "sequence": (_INT, None),
    "left_operand": (_STR, None),
    "comparator": (_STR, _enum("lt", "le", "eq", "ne", "ge", "gt", "between", "outside",
                              "in_enum", "not_in_enum", "exists", "absent", "before",
                              "after", "overlaps", "within_window", "same_interval")),
    "missing_outcome": (_STR, _enum("not_evaluable", "boundary", "no_match")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    "right_typed_value": (_STR_OR_NULL, None),
    "right_ref_id": (_STR_OR_NULL, None),
    "temporal_relation": (_STR_OR_NULL, None),
})

# --- baseline + trend rules ---
_spec("baseline_rules", {
    "rule_id": (_STR, None),
    "version": (_STR, None),
    "candidate_window": (_STR_LIST, None),
    "allowed_record_statuses": (_STR_LIST, None),
    "ordering_fields": (_STR_LIST, None),
    "tie_break_fields": (_STR_LIST, None),
    "minimum_required_candidates": (_INT, None),
    "no_candidate_outcome": (_STR, _enum("not_evaluable", "not_applicable")),
    "tie_outcome": (_STR, _enum("boundary", "not_evaluable")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    # Typed baseline magnitude (§7.2 "基线异常进一步升/降级"): the relative
    # deviation below which a post-baseline point is a baseline-confirmation
    # (not a further deviation).  Absent -> the runtime fails closed (no
    # magnitude-based episode dropping).
    "baseline_confirmation_relative_deviation": (_DEC_OR_NULL, None),
})
_spec("trend_rules", {
    "rule_id": (_STR, None),
    "version": (_STR, None),
    "minimum_comparable_points": (_INT, None),
    "confirmation_point_count": (_INT, None),
    "confirmation_window": (_STR, None),
    "recovery_window": (_STR, None),
    "recurrent_gap_window": (_STR, None),
    "required_same_context_fields": (_STR_LIST, None),
    "missing_point_policy": (_STR, _enum("break_series", "boundary", "not_evaluable")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- action obligation definitions ---
_spec("action_obligation_definitions", {
    "obligation_definition_id": (_STR, None),
    "version": (_STR, None),
    "obligation_kind": (_STR, _enum("repeat", "clinical_review", "treatment_action",
                                   "ae_assessment", "protocol_execution_check")),
    "trigger_rule_id": (_STR, None),
    "required_action_role": (_STR, None),
    "temporal_window": (_STR_LIST, None),
    "owner_domain": (_STR, None),
    "query_owner": (_STR, None),
    "merge_key_fields": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- organ pattern rule definitions ---
_spec("organ_pattern_rule_definitions", {
    "pattern_rule_id": (_STR, None),
    "name": (_STR, None),
    "version": (_STR, None),
    "required_component_roles": (_STR_LIST_LIST, None),
    "temporal_window": (_STR_LIST, None),
    "alternative_explanation_required": (_BOOL, None),
    "exposure_context_required": (_BOOL, None),
    "seriousness_clue_permitted": (_BOOL, None),
    "owner_route": (_STR, D07Action.ALL),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- examination requirement sets ---
_spec("examination_requirement_sets", {
    "requirement_set_id": (_STR, None),
    "version": (_STR, None),
    "domain": (_STR, _enum("LB", "VS", "EG", "PE", "IMAGING", "OTHER")),
    "required_context_roles": (_STR_LIST, None),
    "conditional_requirement_predicates": (_STR_LIST, None),
    "allowed_interpretation_states": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- priority policy + precedence rules ---
_spec("priority_policy", {
    "policy_id": (_STR, None),
    "version": (_STR, None),
    "ordered_precedence_rule_ids": (_STR_LIST, None),
    "high_priority_clinical_flag_rules": (_STR_LIST, None),
    "machine_close_forbidden_rules": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "policy_hash": (_STR, None),
})
_spec("priority_precedence_rules", {
    "precedence_rule_id": (_STR, None),
    "step": (_INT, None),
    "trigger": (_STR, _enum("high_priority_clinical_flag", "identity_or_evidence_unresolved",
                           "significant_safety_concern", "mild_or_explained",
                           "negative_or_not_applicable")),
    "monitoring_priority": (_STR, MonitoringPriority.ALL),
    "machine_close_forbidden": (_BOOL, None),
    "reason_codes": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
}, optional={
    # Typed safety-critical magnitude threshold (5xULN class, §9 "受试者权益/
    # 安全关键阈值") for the ``high_priority_clinical_flag`` trigger.  Absent
    # -> the runtime fails closed (no threshold promotion).
    "safety_critical_ratio_threshold": (_DEC_OR_NULL, None),
})

# --- observed results ---
_spec("observed_results", {
    "result_id": (_STR, None),
    "stable_source_record_id": (_STR, None),
    "subject_ref": (_STR, None),
    "site_ref": (_STR, None),
    "stable_measure_key": (_STR, None),
    "domain": (_STR, _enum("LB", "VS", "EG", "PE", "IMAGING", "OTHER")),
    "raw_value": (_STR, None),
    "collection_or_exam_time": (_STR, None),
    "specimen_quality": (_STR, _enum("acceptable", "hemolysed", "contaminated", "clotted",
                                     "insufficient", "unknown", "not_applicable")),
    "correction_status": (_STR, _enum("original", "corrected", "reported_again")),
    "record_status": (_STR, RecordStatus.ALL),
    "accepted_snapshot_ref": (_STR, None),
    "scope_envelope_id": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "lineage_hash": (_STR, None),
}, optional={
    "numeric_value": (_DEC_OR_NULL, None),
    "character_value": (_STR_OR_NULL, None),
    "original_unit": (_STR_OR_NULL, None),
    "reported_range_low": (_DEC_OR_NULL, None),
    "reported_range_high": (_DEC_OR_NULL, None),
    "reported_abnormal_flag": (_STR_OR_NULL, None),
    "reported_cs_ncs": (_STR_OR_NULL, _enum("CS", "NCS", "borderline")),
    "reported_grade": (_STR_OR_NULL, None),
    "visit_ref": (_STR_OR_NULL, None),
    "method_kind": (_STR_OR_NULL, None),
    "specimen_kind": (_STR_OR_NULL, None),
    "body_site_kind": (_STR_OR_NULL, None),
    "lead_kind": (_STR_OR_NULL, None),
    "position_kind": (_STR_OR_NULL, None),
    "laterality_kind": (_STR_OR_NULL, None),
    "reader_role_kind": (_STR_OR_NULL, None),
    "lab_or_reader": (_STR_OR_NULL, None),
    "repeat_series_ref": (_STR_OR_NULL, None),
})
_spec("previous_observed_results", _SPEC_REQUIRED["observed_results"],
      _SPEC_OPTIONAL["observed_results"])

# --- subject demographics ---
_spec("subject_demographics", {
    "subject_ref": (_STR, None),
    "sex": (_STR, _enum("male", "female", "intersex", "unknown", "not_applicable")),
    "age_years": (_STR, None),
    "pregnancy_state": (_STR, _enum("pregnant", "not_pregnant", "unknown", "not_applicable")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- visit refs ---
_spec("visit_refs", {
    "visit_ref_id": (_STR, None),
    "visit_label": (_STR, None),
    "status": (_STR, None),
    "planned_date": (_STR_OR_NULL, None),
    "actual_date": (_STR_OR_NULL, None),
    "window": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- producer consumption bindings ---
_spec("producer_consumption_bindings", {
    "binding_id": (_STR, None),
    "scope_binding_id": (_STR, None),
    "producer_domain": (_STR, None),
    "producer_object_type": (_STR, None),
    "producer_object_id": (_STR, None),
    "producer_content_hash": (_STR, None),
    "producer_version": (_STR, None),
    "consumer_domain": (_STR, None),
    "consumption_purpose": (_STR, None),
    "permitted_outputs": (_STR, _enum("evidence_only", "handoff_only", "risk_and_query")),
    "source_locator_ids": (_STR_LIST, None),
    "lineage_hash": (_STR, None),
})

# --- D05 gate bindings ---
_spec("d05_gate_bindings", {
    "d05_gate_binding_id": (_STR, None),
    "source_record_id": (_STR, None),
    "blocked_observation_id": (_STR, None),
    "blocked_stage": (_STR, _enum("expected_set_expansion", "evaluation_admission",
                                  "obligation_assessment", "pattern_assessment")),
    "control_plane_state": (_STR, _enum("boundary", "not_evaluable")),
    "reason_codes": (_STR_LIST, None),
    "project_ref": (_STR, None),
    "run_ref": (_STR, None),
    "scope_binding_id": (_STR, None),
    "subject_ref": (_STR, None),
    "site_ref": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- applicability evidence ---
_spec("applicability_evidence", {
    "applicability_evidence_id": (_STR, None),
    "scope_binding_id": (_STR, None),
    "unit_candidate_key": (_STR, None),
    "authority_binding_id": (_STR, None),
    "applicability_rule_id": (_STR, None),
    "applicability": (_STR, ApplicabilityValue.ALL),
    "control_plane_no_match": (_BOOL, None),
    "predicate_results": (_BOOL_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- clinical review refs + CS reason refs + d04 context refs + carry-forward ---
_spec("clinical_review_refs", {
    "review_ref_id": (_STR, None),
    "review_role": (_STR, None),
    "review_outcome": (_STR, None),
    "review_time": (_STR_OR_NULL, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})
_spec("clinical_significance_reason_refs", {
    "reason_ref_id": (_STR, None),
    "reason_text": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})
_spec("d04_context_refs", {
    "d04_context_ref_id": (_STR, None),
    "context_kind": (_STR, _enum("protocol_deviation_candidate", "eligibility_context",
                                 "protocol_action_context")),
    "protocol_clause_ref": (_STR, None),
    "context_accepted": (_BOOL, None),
    "context_scope_equal": (_BOOL, None),
    "accepted_content_hash": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})
_spec("carry_forward_refs", {
    "carry_forward_ref_id": (_STR, None),
    "previous_run_ref": (_STR, None),
    "previous_scope_binding_id": (_STR, None),
    "source_risk_id": (_STR_OR_NULL, None),
    "identity_resolution_state": (_STR, _enum("resolved", "ambiguous", "not_resolved")),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- audience lexicon ---
_spec("audience_lexicon", {
    "lexicon_id": (_STR, None),
    "version": (_STR, None),
    "allowed_domain_labels": (_STR_LIST, None),
    "allowed_risk_type_labels": (_STR_LIST, None),
    "forbidden_internal_tokens": (_STR_LIST, None),
    "required_sentence_patterns": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "content_hash": (_STR, None),
})

# --- shared spine binding + equality decision ---
_spec("shared_spine_binding", {
    "binding_id": (_STR, None),
    "project_ref": (_STR, None),
    "run_ref": (_STR, None),
    "monitoring_mode": (_STR, None),
    "scope_type": (_STR, None),
    "scope_key": (_STR, None),
    "subject_ref": (_STR, None),
    "site_ref": (_STR, None),
    "accepted_snapshot_ref": (_STR, None),
    "source_revision": (_STR, None),
    "episode_key": (_STR, None),
    "d05_projection_id": (_STR, None),
    "spine_binding_id": (_STR, None),
    "axis_version": (_STR, None),
    "axis_hash": (_STR, None),
    "cutoff": (_STR, None),
    "scope_binding_id": (_STR, None),
    "scope_equality_decision_id": (_STR, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})
_spec("shared_spine_scope_equality_decision", {
    "decision_id": (_STR, None),
    "binding_id": (_STR, None),
    "d05_projection_id": (_STR, None),
    "project_equal": (_BOOL, None),
    "run_equal": (_BOOL, None),
    "mode_equal": (_BOOL, None),
    "scope_type_equal": (_BOOL, None),
    "scope_key_equal": (_BOOL, None),
    "subject_equal": (_BOOL, None),
    "site_equal": (_BOOL, None),
    "snapshot_equal": (_BOOL, None),
    "source_revision_equal": (_BOOL, None),
    "episode_equal": (_BOOL, None),
    "cutoff_equal": (_BOOL, None),
    "axis_hash_valid": (_BOOL, None),
    "all_equal": (_BOOL, None),
    "reason_codes": (_STR_LIST, None),
    "source_locator_ids": (_STR_LIST, None),
    "hash": (_STR, None),
})

# --- typed input container (v0.4 §14.1 flat container) ---
TYPED_INPUT_SECTION_KEYS: Tuple[str, ...] = (
    "input_schema",
    "run_scope_binding",
    "previous_run_scope_binding",
    "authority_bindings",
    "measure_definitions",
    "reference_range_definitions",
    "unit_conversion_rules",
    "grade_rule_sets",
    "grade_rules",
    "monitoring_rules",
    "monitoring_predicates",
    "baseline_rules",
    "trend_rules",
    "action_obligation_definitions",
    "organ_pattern_rule_definitions",
    "examination_requirement_sets",
    "priority_policy",
    "priority_precedence_rules",
    "producer_consumption_bindings",
    "clinical_review_refs",
    "clinical_significance_reason_refs",
    "d04_context_refs",
    "correction_chain_decisions",
    "cutoff_decisions",
    "d05_gate_bindings",
    "applicability_evidence",
    "observed_results",
    "previous_observed_results",
    "scope_envelopes",
    "previous_scope_envelopes",
    "time_refs",
    "previous_time_refs",
    "subject_demographics",
    "visit_refs",
    "carry_forward_refs",
    "shared_spine_binding",
    "shared_spine_scope_equality_decision",
    "audience_lexicon",
)

LIST_SECTIONS: Tuple[str, ...] = (
    "authority_bindings",
    "measure_definitions",
    "reference_range_definitions",
    "unit_conversion_rules",
    "grade_rule_sets",
    "grade_rules",
    "monitoring_rules",
    "monitoring_predicates",
    "baseline_rules",
    "trend_rules",
    "action_obligation_definitions",
    "organ_pattern_rule_definitions",
    "examination_requirement_sets",
    "priority_precedence_rules",
    "producer_consumption_bindings",
    "clinical_review_refs",
    "clinical_significance_reason_refs",
    "d04_context_refs",
    "correction_chain_decisions",
    "cutoff_decisions",
    "d05_gate_bindings",
    "applicability_evidence",
    "observed_results",
    "previous_observed_results",
    "scope_envelopes",
    "previous_scope_envelopes",
    "time_refs",
    "previous_time_refs",
    "subject_demographics",
    "visit_refs",
    "carry_forward_refs",
)

DICT_SECTIONS: Tuple[str, ...] = (
    "run_scope_binding",
    "previous_run_scope_binding",
    "priority_policy",
    "shared_spine_binding",
    "shared_spine_scope_equality_decision",
    "audience_lexicon",
)

_DECIMAL_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
_INT_RE = re.compile(r"^[+-]?\d+$")


def _check_scalar(value: Any, kind: str, label: str) -> None:
    if kind == _STR:
        if not isinstance(value, str):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _STR_OR_NULL:
        if value is not None and not isinstance(value, str):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _STR_LIST:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _BOOL:
        if not isinstance(value, bool):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _BOOL_LIST:
        if not isinstance(value, list) or not all(isinstance(v, bool) for v in value):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _INT:
        if not isinstance(value, int) or isinstance(value, bool):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _DEC:
        if not isinstance(value, str) or not _DECIMAL_RE.match(value):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _DEC_OR_NULL:
        if value is not None and (not isinstance(value, str) or not _DECIMAL_RE.match(value)):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == "dict":
        if not isinstance(value, dict):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == "dict|null":
        if value is not None and not isinstance(value, dict):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == _STR_LIST_LIST:
        if not isinstance(value, list) or not all(
            isinstance(v, dict) for v in value
        ):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == "str_2d_list":
        if not isinstance(value, list) or not all(
            isinstance(v, list) and all(isinstance(s, str) for s in v)
            for v in value
        ):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    elif kind == "bool|null":
        if value is not None and not isinstance(value, bool):
            raise D07IntegrityError("schema_parse", "schema_error", label)
    else:
        raise AssertionError(f"unhandled schema kind {kind!r}")


def validate_typed_object(
    obj: Mapping[str, Any], spec_name: str, locator: str
) -> None:
    """Exact-key validation of one typed object (fail-closed schema_parse)."""
    required = _SPEC_REQUIRED.get(spec_name)
    if required is None:
        raise D07IntegrityError("schema_parse", "schema_error", locator)
    optional = _SPEC_OPTIONAL.get(spec_name, {})
    spec = dict(required)
    spec.update(optional)
    unknown = [k for k in obj.keys() if k not in spec]
    if unknown:
        raise D07IntegrityError("schema_parse", "schema_error",
                                f"{locator}:unknown_key:{unknown[0]}")
    for key, (kind, enum_values) in required.items():
        if key not in obj:
            raise D07IntegrityError("schema_parse", "schema_error",
                                    f"{locator}:missing_key:{key}")
        value = obj[key]
        _check_scalar(value, kind, f"{locator}.{key}")
        if enum_values is not None and value not in enum_values:
            raise D07IntegrityError("schema_parse", "schema_error",
                                    f"{locator}.{key}:enum:{value}")
    for key, (kind, enum_values) in optional.items():
        if key not in obj:
            continue
        value = obj[key]
        _check_scalar(value, kind, f"{locator}.{key}")
        if enum_values is not None and value not in enum_values:
            raise D07IntegrityError("schema_parse", "schema_error",
                                    f"{locator}.{key}:enum:{value}")
    # Nested component-role objects inside organ pattern definitions.
    if spec_name == "organ_pattern_rule_definitions":
        for idx, role in enumerate(obj.get("required_component_roles", [])):
            unknown_role = [k for k in role.keys() if k not in ("component_role", "stable_measure_key")]
            if unknown_role or "component_role" not in role or "stable_measure_key" not in role:
                raise D07IntegrityError("schema_parse", "schema_error",
                                        f"{locator}.required_component_roles[{idx}]")
    if spec_name == "run_scope_binding":
        rule_set_versions = obj.get("rule_set_versions")
        if not isinstance(rule_set_versions, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in rule_set_versions.items()
        ):
            raise D07IntegrityError("schema_parse", "schema_error",
                                    f"{locator}.rule_set_versions")


def validate_typed_input(typed_input: Mapping[str, Any]) -> None:
    """Validate the flat typed-input container (exact key set)."""
    unknown = [k for k in typed_input.keys() if k not in TYPED_INPUT_SECTION_KEYS]
    if unknown:
        raise D07IntegrityError("schema_parse", "schema_error",
                                f"typed_input:unknown_key:{unknown[0]}")
    missing = [k for k in TYPED_INPUT_SECTION_KEYS if k not in typed_input]
    if missing:
        raise D07IntegrityError("schema_parse", "schema_error",
                                f"typed_input:missing_key:{missing[0]}")
    if typed_input.get("input_schema") != D07_TYPED_INPUT_SCHEMA:
        raise D07IntegrityError("schema_parse", "schema_error", "typed_input.input_schema")
    for section in LIST_SECTIONS:
        value = typed_input.get(section)
        if not isinstance(value, list):
            raise D07IntegrityError("schema_parse", "schema_error", f"typed_input.{section}")
        spec_name = section if section in _SPEC_REQUIRED else None
        if spec_name is None:
            continue
        for idx, obj in enumerate(value):
            if not isinstance(obj, dict):
                raise D07IntegrityError("schema_parse", "schema_error",
                                        f"{section}[{idx}]")
            validate_typed_object(obj, spec_name, f"{section}[{idx}]")
    for section in DICT_SECTIONS:
        value = typed_input.get(section)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise D07IntegrityError("schema_parse", "schema_error", f"typed_input.{section}")
        validate_typed_object(value, section, section)


def verify_object_self_hash(obj: Mapping[str, Any], hash_field: str, locator: str) -> None:
    """canonical_hash: recompute the object hash from typed fields."""
    supplied = obj.get(hash_field)
    if not is_sha256_hex(supplied):
        raise D07IntegrityError("canonical_hash", "stale_hash", locator)
    core = {key: value for key, value in obj.items() if key != hash_field}
    expected = d07_content_hash(core)
    if supplied != expected:
        raise D07IntegrityError("canonical_hash", "stale_hash", locator)


# Hash field per section (object self-hash fields verified in canonical_hash).
SECTION_HASH_FIELDS: Dict[str, str] = {
    "authority_bindings": "hash",
    "cutoff_decisions": "hash",
    "time_refs": "hash",
    "previous_time_refs": "hash",
    "scope_envelopes": "record_content_hash",
    "previous_scope_envelopes": "record_content_hash",
    "correction_chain_decisions": "hash",
    "measure_definitions": "definition_hash",
    "reference_range_definitions": "hash",
    "unit_conversion_rules": "hash",
    "grade_rule_sets": "hash",
    "grade_rules": "hash",
    "monitoring_rules": "hash",
    "monitoring_predicates": "hash",
    "baseline_rules": "hash",
    "trend_rules": "hash",
    "action_obligation_definitions": "hash",
    "organ_pattern_rule_definitions": "hash",
    "examination_requirement_sets": "hash",
    "priority_precedence_rules": "hash",
    "producer_consumption_bindings": "lineage_hash",
    "clinical_review_refs": "hash",
    "clinical_significance_reason_refs": "hash",
    "d04_context_refs": "hash",
    "d05_gate_bindings": "hash",
    "applicability_evidence": "hash",
    "observed_results": "lineage_hash",
    "previous_observed_results": "lineage_hash",
    "subject_demographics": "hash",
    "visit_refs": "hash",
    "carry_forward_refs": "hash",
}

SINGLETON_HASH_FIELDS: Dict[str, str] = {
    "run_scope_binding": "lineage_hash",
    "previous_run_scope_binding": "lineage_hash",
    "priority_policy": "policy_hash",
    "audience_lexicon": "content_hash",
    "shared_spine_binding": "hash",
    "shared_spine_scope_equality_decision": "hash",
}
