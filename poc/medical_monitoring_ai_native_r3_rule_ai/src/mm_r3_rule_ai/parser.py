"""Strict single-object JSON parser with typed failure classification.

Discovery review §4.1-4.3:

* The model output MUST be a single JSON object.  We never strip Markdown code
  fences, never salvage a substring from prose, and never concatenate multiple
  JSON values.  Violations become typed, blocking parse failures.
* Every undeclared key at every schema level is rejected.
* Scalar / list types are validated without Python bool-as-int ambiguity, with
  finite numeric checks, allowed operators, logical combination, and
  field/operator/value compatibility from the frozen catalog.
* Each condition must bind to one frozen catalog field and carry a non-empty
  Chinese source phrase in ``extracted_from``.  Unknown fields are blocking;
  no implicit aliasing.

The parser is stdlib-only and **isomorphic** to :data:`RULE_CANDIDATE_SCHEMA`.
It does not call a model, never mutates R1/R3, and creates no transport.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .catalog import (
    CATALOG_OPERATORS,
    FieldCatalog,
    FieldSpec,
    ValueType,
)
from .schema import RULE_CANDIDATE_SCHEMA

__all__ = [
    "ParseStatus",
    "ParseFailureKind",
    "ConditionDraft",
    "RuleCandidateDraft",
    "ParseResult",
    "ParseError",
    "parse_rule_candidate",
    "canonical_candidate_payload",
    "candidate_content_hash",
]

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised for internal misuse (wrong argument types), not for bad model
    output.  Bad model output is returned as a :class:`ParseResult` with a
    blocking status."""


# ---------------------------------------------------------------------------
# Parse status / failure classification
# ---------------------------------------------------------------------------

class ParseStatus:
    """Outcome status of parsing one model output.

    * ``ok`` -- structurally valid AND no open questions.  Assumptions may be
      retained in the parsed candidate; the workflow conversion gate handles
      them separately and blocks RuleDraft construction while they remain.
    * ``blocked_open_questions`` -- structurally valid but the model declared
      unresolved open questions; cannot yield a RuleDraft.
    * Plus the blocking failure kinds below.
    """
    OK = "ok"
    BLOCKED_OPEN_QUESTIONS = "blocked_open_questions"
    # Structural / lexical failures:
    NOT_JSON = "not_json"
    MARKDOWN_FENCE = "markdown_fence"
    NOT_SINGLE_OBJECT = "not_single_object"
    MULTIPLE_JSON_VALUES = "multiple_json_values"
    EMPTY_OUTPUT = "empty_output"
    SCHEMA_VIOLATION = "schema_violation"
    UNKNOWN_FIELD = "unknown_field"
    INVALID_OPERATOR = "invalid_operator"
    INVALID_LOGICAL_COMBINATION = "invalid_logical_combination"
    TYPE_MISMATCH = "type_mismatch"
    EMPTY_CONDITIONS = "empty_conditions"
    MISSING_EXTRACTED_FROM = "missing_extracted_from"
    EMPTY_EXTRACTED_FROM = "empty_extracted_from"
    FIELD_NOT_IN_CATALOG = "field_not_in_catalog"
    OPERATOR_NOT_ALLOWED_FOR_FIELD = "operator_not_allowed_for_field"
    THRESHOLD_TYPE_MISMATCH = "threshold_type_mismatch"
    NON_FINITE_NUMBER = "non_finite_number"
    BOOL_AS_INT = "bool_as_int"
    DUPLICATE_KEY = "duplicate_key"


#: Failure kinds that are structurally fatal (no salvage).
FATAL_FAILURES: Tuple[str, ...] = (
    ParseStatus.NOT_JSON,
    ParseStatus.MARKDOWN_FENCE,
    ParseStatus.NOT_SINGLE_OBJECT,
    ParseStatus.MULTIPLE_JSON_VALUES,
    ParseStatus.EMPTY_OUTPUT,
    ParseStatus.SCHEMA_VIOLATION,
    ParseStatus.UNKNOWN_FIELD,
    ParseStatus.INVALID_OPERATOR,
    ParseStatus.INVALID_LOGICAL_COMBINATION,
    ParseStatus.TYPE_MISMATCH,
    ParseStatus.EMPTY_CONDITIONS,
    ParseStatus.MISSING_EXTRACTED_FROM,
    ParseStatus.EMPTY_EXTRACTED_FROM,
    ParseStatus.FIELD_NOT_IN_CATALOG,
    ParseStatus.OPERATOR_NOT_ALLOWED_FOR_FIELD,
    ParseStatus.THRESHOLD_TYPE_MISMATCH,
    ParseStatus.NON_FINITE_NUMBER,
    ParseStatus.BOOL_AS_INT,
    ParseStatus.DUPLICATE_KEY,
)

#: Alias kept for clarity in reports.
ParseFailureKind = ParseStatus


def _is_blocking(status: str) -> bool:
    return status in FATAL_FAILURES or status == ParseStatus.BLOCKED_OPEN_QUESTIONS



def _deep_freeze(value: Any) -> Any:
    """Recursively freeze a JSON-able value so it cannot mutate after parse.

    Lists become tuples, dicts become frozen tuples of sorted items, scalars
    pass through.  Mirrors the frozen R3 ``deep_freeze_json`` semantics without
    importing frozen internals.
    """
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _deep_freeze(v)) for k, v in value.items()))
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _to_jsonable(value: Any) -> Any:
    """Inverse of :func:`_deep_freeze`: tuples -> lists for JSON payloads."""
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value

# ---------------------------------------------------------------------------
# Draft value objects (pure data; no R3 construction here)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConditionDraft:
    """One structured condition extracted from the model output.

    Field/operator/threshold compatibility has been validated against the
    catalog.  ``extracted_from`` is non-empty.  The ``threshold`` is
    deep-frozen so a candidate and its content hash cannot mutate after parse.
    """
    field: str
    operator: str
    threshold: Any
    extracted_from: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "threshold", _deep_freeze(self.threshold))

    def to_payload(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "threshold": _to_jsonable(self.threshold),
            "extracted_from": self.extracted_from,
        }


@dataclass(frozen=True)
class RuleCandidateDraft:
    """The structured candidate produced by a successful parse.

    This is a *candidate* only; it is never a frozen R3 ``RuleDraft``.  The
    workflow module decides whether to promote it.
    """
    rule_name: str
    conditions: Tuple[ConditionDraft, ...]
    logical_combination: str
    severity_hint: str
    domain_hint: str
    assumptions: Tuple[str, ...]
    open_questions: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", tuple(self.conditions))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(self, "open_questions", tuple(self.open_questions))

    def to_payload(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "conditions": [c.to_payload() for c in self.conditions],
            "logical_combination": self.logical_combination,
            "severity_hint": self.severity_hint,
            "domain_hint": self.domain_hint,
            "assumptions": list(self.assumptions),
            "open_questions": list(self.open_questions),
        }


@dataclass(frozen=True)
class ParseResult:
    """The outcome of parsing one model output.

    Exactly one of ``candidate`` (ok) or a blocking ``status`` is meaningful.
    ``errors`` carries one entry per violation for audit.
    """
    status: str
    candidate: Optional[RuleCandidateDraft] = None
    errors: Tuple[str, ...] = ()
    catalog_fingerprint: str = ""
    schema_hash: str = ""
    content_hash: str = ""

    @property
    def ok(self) -> bool:
        return self.status == ParseStatus.OK and self.candidate is not None

    @property
    def blocked(self) -> bool:
        return _is_blocking(self.status)

    def require_ok(self) -> RuleCandidateDraft:
        if not self.ok:
            raise ParseError(f"parse did not succeed: status={self.status} errors={list(self.errors)}")
        assert self.candidate is not None
        return self.candidate


# ---------------------------------------------------------------------------
# Canonical payload + hash
# ---------------------------------------------------------------------------

def canonical_candidate_payload(candidate: RuleCandidateDraft) -> Dict[str, Any]:
    return candidate.to_payload()


def candidate_content_hash(candidate: RuleCandidateDraft) -> str:
    import hashlib

    canon = json.dumps(
        canonical_candidate_payload(candidate),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Low-level JSON acceptance
# ---------------------------------------------------------------------------

def _looks_like_markdown_fence(text: str) -> bool:
    s = text.strip()
    return s.startswith("```")


class _DuplicateKeyError(ValueError):
    """Internal signal raised when a JSON object contains a repeated key."""


def _reject_duplicate_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """``object_pairs_hook`` that rejects duplicate object keys.

    Python's ``json`` silently keeps the last value for a repeated key; this
    hook makes the collision a blocking ``DUPLICATE_KEY`` parse failure so the
    model cannot mask an earlier condition with a later one.
    """
    seen: Dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKeyError(key)
        seen[key] = value
    return seen


def _strict_json_load(text: str) -> Tuple[Any, Optional[str]]:
    """Load exactly one JSON value; detect trailing data, fences and duplicate keys.

    Returns ``(value, error_kind)``.  On success ``error_kind`` is None.
    """
    if text is None or (isinstance(text, str) and text.strip() == ""):
        return None, ParseStatus.EMPTY_OUTPUT
    if not isinstance(text, str):
        return None, ParseStatus.NOT_JSON
    if _looks_like_markdown_fence(text):
        return None, ParseStatus.MARKDOWN_FENCE
    decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_pairs)
    stripped = text.strip()
    try:
        value, end = decoder.raw_decode(stripped)
    except _DuplicateKeyError:
        return None, ParseStatus.DUPLICATE_KEY
    except json.JSONDecodeError:
        return None, ParseStatus.NOT_JSON
    trailing = stripped[end:].strip()
    if trailing:
        return None, ParseStatus.MULTIPLE_JSON_VALUES
    return value, None


def _check_scalar(value: Any, expected_type: str) -> Optional[str]:
    """Return an error kind if ``value`` does not match ``expected_type``."""
    if expected_type == ValueType.STRING:
        if not isinstance(value, str):
            return ParseStatus.TYPE_MISMATCH
        return None
    if expected_type == ValueType.INTEGER:
        # bool is a subclass of int in Python; reject with the declared status.
        if isinstance(value, bool):
            return ParseStatus.BOOL_AS_INT
        if not isinstance(value, int):
            return ParseStatus.TYPE_MISMATCH
        return None
    if expected_type == ValueType.NUMBER:
        if isinstance(value, bool):
            return ParseStatus.BOOL_AS_INT
        if not isinstance(value, (int, float)):
            return ParseStatus.TYPE_MISMATCH
        if isinstance(value, float) and not math.isfinite(value):
            return ParseStatus.NON_FINITE_NUMBER
        return None
    if expected_type == ValueType.BOOLEAN:
        if not isinstance(value, bool):
            return ParseStatus.TYPE_MISMATCH
        return None
    if expected_type == ValueType.STRING_LIST:
        if not isinstance(value, list) or not value:
            return ParseStatus.TYPE_MISMATCH
        if any(not isinstance(item, str) for item in value):
            return ParseStatus.TYPE_MISMATCH
        return None
    if expected_type == ValueType.NUMBER_LIST:
        if not isinstance(value, list) or not value:
            return ParseStatus.TYPE_MISMATCH
        for item in value:
            if isinstance(item, bool):
                return ParseStatus.BOOL_AS_INT
            if not isinstance(item, (int, float)):
                return ParseStatus.TYPE_MISMATCH
            if isinstance(item, float) and not math.isfinite(item):
                return ParseStatus.NON_FINITE_NUMBER
        return None
    return ParseStatus.TYPE_MISMATCH


def _expected_threshold_type(spec: FieldSpec, operator: str) -> str:
    """Map (field value_type, operator) -> expected threshold value-type tag."""
    # is_missing / is_present forbid a threshold entirely.
    if operator in ("is_missing", "is_present"):
        return ValueType.NONE
    if operator in ("in", "not_in"):
        if spec.value_type in (ValueType.NUMBER, ValueType.INTEGER):
            return ValueType.NUMBER_LIST
        return ValueType.STRING_LIST
    # eq/ne/contains/gt/ge/lt/le
    return spec.value_type


# ---------------------------------------------------------------------------
# Schema-level structural validation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Schema-derived constraints (single source of truth: RULE_CANDIDATE_SCHEMA)
# ---------------------------------------------------------------------------
# The parser derives required/allowed keys and enum values directly from
# RULE_CANDIDATE_SCHEMA so the JSON Schema document is the sole authority --
# no duplicated declarations that can drift.


def _schema_top_required() -> Tuple[str, ...]:
    return tuple(RULE_CANDIDATE_SCHEMA.get("required", ()))


def _schema_top_allowed() -> Tuple[str, ...]:
    props = RULE_CANDIDATE_SCHEMA.get("properties", {})
    return tuple(props.keys())


def _schema_condition_required() -> Tuple[str, ...]:
    items = RULE_CANDIDATE_SCHEMA["properties"]["conditions"]["items"]
    return tuple(items.get("required", ()))


def _schema_condition_allowed() -> Tuple[str, ...]:
    items = RULE_CANDIDATE_SCHEMA["properties"]["conditions"]["items"]
    return tuple(items.get("properties", {}).keys())


def _schema_enum(field_name: str) -> Tuple[str, ...]:
    """Extract an enum tuple for a top-level string field from the schema."""
    spec = RULE_CANDIDATE_SCHEMA["properties"][field_name]
    return tuple(spec.get("enum", ()))


def _schema_rule_name_max_length() -> int:
    """Extract rule_name.maxLength from the schema (default 200)."""
    return int(RULE_CANDIDATE_SCHEMA["properties"]["rule_name"].get("maxLength", 200))


def _collect_errors_for_object(
    obj: Mapping[str, Any],
    allowed: Sequence[str],
    required: Sequence[str],
) -> List[str]:
    """Return list of error strings for unknown/missing keys."""
    errs: List[str] = []
    keys = set(obj.keys())
    unknown = keys - set(allowed)
    for k in sorted(unknown):
        errs.append(f"unknown_property:{k}")
    missing = set(required) - keys
    for k in sorted(missing):
        errs.append(f"missing_property:{k}")
    return errs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_rule_candidate(
    raw_output: str,
    catalog: FieldCatalog,
) -> ParseResult:
    """Parse one model output into a :class:`RuleCandidateDraft`.

    Strict, fail-closed, catalog-bound.  The caller MUST supply an explicit
    :class:`FieldCatalog`; there is no built-in default.  Returns a
    :class:`ParseResult`; never raises for bad model output (only for
    programmer misuse via :class:`ParseError`).
    """
    if not isinstance(catalog, FieldCatalog):
        raise ParseError("catalog must be a FieldCatalog")
    from .schema import schema_content_hash

    sch_hash = schema_content_hash()

    # --- 1. Accept exactly one JSON object -------------------------------
    value, err = _strict_json_load(raw_output)
    if err is not None:
        return ParseResult(
            status=err,
            errors=(f"json:{err}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if not isinstance(value, dict):
        return ParseResult(
            status=ParseStatus.NOT_SINGLE_OBJECT,
            errors=(f"not_object:{type(value).__name__}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )

    # --- 2. Top-level structural keys ------------------------------------
    errs: List[str] = list(_collect_errors_for_object(value, _schema_top_allowed(), _schema_top_required()))
    if errs:
        kind = (
            ParseStatus.UNKNOWN_FIELD
            if any(e.startswith("unknown_property") for e in errs)
            else ParseStatus.SCHEMA_VIOLATION
        )
        return ParseResult(
            status=kind,
            errors=tuple(errs),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )

    rule_name = value["rule_name"]
    conditions_raw = value["conditions"]
    logical_combination = value["logical_combination"]
    severity_hint = value["severity_hint"]
    domain_hint = value["domain_hint"]
    assumptions_raw = value["assumptions"]
    open_questions_raw = value["open_questions"]

    # --- 3. Top-level scalar / enum validation ---------------------------
    rule_name_max = _schema_rule_name_max_length()
    if not isinstance(rule_name, str) or not rule_name.strip():
        return ParseResult(
            status=ParseStatus.SCHEMA_VIOLATION,
            errors=("rule_name:nonempty_string_required",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if len(rule_name) > rule_name_max:
        return ParseResult(
            status=ParseStatus.SCHEMA_VIOLATION,
            errors=(f"rule_name:exceeds_maxLength_{rule_name_max}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if logical_combination not in _schema_enum("logical_combination"):
        return ParseResult(
            status=ParseStatus.INVALID_LOGICAL_COMBINATION,
            errors=(f"logical_combination:{logical_combination!r}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if severity_hint not in _schema_enum("severity_hint"):
        return ParseResult(
            status=ParseStatus.SCHEMA_VIOLATION,
            errors=(f"severity_hint:{severity_hint!r}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if domain_hint not in _schema_enum("domain_hint"):
        return ParseResult(
            status=ParseStatus.SCHEMA_VIOLATION,
            errors=(f"domain_hint:{domain_hint!r}",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    if not isinstance(conditions_raw, list) or not conditions_raw:
        return ParseResult(
            status=ParseStatus.EMPTY_CONDITIONS,
            errors=("conditions:nonempty_list_required",),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
        )
    # assumptions / open_questions must be arrays of non-empty strings
    for label, arr in (("assumptions", assumptions_raw), ("open_questions", open_questions_raw)):
        if not isinstance(arr, list):
            return ParseResult(
                status=ParseStatus.SCHEMA_VIOLATION,
                errors=(f"{label}:array_required",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )
        for item in arr:
            if not isinstance(item, str) or not item.strip():
                return ParseResult(
                    status=ParseStatus.SCHEMA_VIOLATION,
                    errors=(f"{label}:nonempty_string_required",),
                    catalog_fingerprint=catalog.fingerprint,
                    schema_hash=sch_hash,
                )

    # --- 4. Per-condition validation -------------------------------------
    parsed_conditions: List[ConditionDraft] = []
    for i, cond in enumerate(conditions_raw):
        if not isinstance(cond, dict):
            return ParseResult(
                status=ParseStatus.SCHEMA_VIOLATION,
                errors=(f"conditions[{i}]:object_required",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )
        cerrs = _collect_errors_for_object(cond, _schema_condition_allowed(), _schema_condition_required())
        if cerrs:
            kind = (
                ParseStatus.UNKNOWN_FIELD
                if any(e.startswith("unknown_property") for e in cerrs)
                else ParseStatus.SCHEMA_VIOLATION
            )
            return ParseResult(
                status=kind,
                errors=tuple(f"conditions[{i}].{e}" for e in cerrs),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )

        c_field = cond["field"]
        c_operator = cond["operator"]
        c_threshold = cond["threshold"]
        c_extracted = cond["extracted_from"]

        if not isinstance(c_field, str) or not c_field.strip():
            return ParseResult(
                status=ParseStatus.SCHEMA_VIOLATION,
                errors=(f"conditions[{i}].field:nonempty_string_required",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )
        if c_operator not in CATALOG_OPERATORS:
            return ParseResult(
                status=ParseStatus.INVALID_OPERATOR,
                errors=(f"conditions[{i}].operator:{c_operator!r}",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )
        if not isinstance(c_extracted, str) or not c_extracted.strip():
            return ParseResult(
                status=ParseStatus.EMPTY_EXTRACTED_FROM,
                errors=(f"conditions[{i}].extracted_from:nonempty_required",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )

        # --- catalog binding --------------------------------------------
        spec = catalog.get(c_field)
        if spec is None:
            return ParseResult(
                status=ParseStatus.FIELD_NOT_IN_CATALOG,
                errors=(f"conditions[{i}].field:{c_field!r}_not_in_catalog",),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )
        if not spec.allows_operator(c_operator):
            return ParseResult(
                status=ParseStatus.OPERATOR_NOT_ALLOWED_FOR_FIELD,
                errors=(
                    f"conditions[{i}]:operator {c_operator!r} not allowed for "
                    f"field {c_field!r}",
                ),
                catalog_fingerprint=catalog.fingerprint,
                schema_hash=sch_hash,
            )

        expected_t = _expected_threshold_type(spec, c_operator)
        if expected_t == ValueType.NONE:
            # is_missing / is_present must have null threshold.
            if c_threshold is not None:
                return ParseResult(
                    status=ParseStatus.THRESHOLD_TYPE_MISMATCH,
                    errors=(
                        f"conditions[{i}]:operator {c_operator!r} requires "
                        f"null threshold",
                    ),
                    catalog_fingerprint=catalog.fingerprint,
                    schema_hash=sch_hash,
                )
        else:
            terr = _check_scalar(c_threshold, expected_t)
            if terr is not None:
                # Preserve declared typed statuses; ordinary type failures stay
                # under THRESHOLD_TYPE_MISMATCH so callers can distinguish them.
                if terr == ParseStatus.BOOL_AS_INT:
                    status = ParseStatus.BOOL_AS_INT
                elif terr == ParseStatus.NON_FINITE_NUMBER:
                    status = ParseStatus.NON_FINITE_NUMBER
                else:
                    status = ParseStatus.THRESHOLD_TYPE_MISMATCH
                return ParseResult(
                    status=status,
                    errors=(
                        f"conditions[{i}].threshold:{terr} expected "
                        f"{expected_t} for field {c_field!r} operator "
                        f"{c_operator!r}",
                    ),
                    catalog_fingerprint=catalog.fingerprint,
                    schema_hash=sch_hash,
                )

        parsed_conditions.append(
            ConditionDraft(
                field=c_field,
                operator=c_operator,
                threshold=c_threshold,
                extracted_from=c_extracted,
            )
        )

    candidate = RuleCandidateDraft(
        rule_name=rule_name,
        conditions=tuple(parsed_conditions),
        logical_combination=logical_combination,
        severity_hint=severity_hint,
        domain_hint=domain_hint,
        assumptions=tuple(assumptions_raw),
        open_questions=tuple(open_questions_raw),
    )

    content_h = candidate_content_hash(candidate)

    # --- 5. Open questions block (but are NOT structural failures) -------
    if candidate.open_questions:
        return ParseResult(
            status=ParseStatus.BLOCKED_OPEN_QUESTIONS,
            candidate=candidate,
            errors=tuple(f"open_question:{q}" for q in candidate.open_questions),
            catalog_fingerprint=catalog.fingerprint,
            schema_hash=sch_hash,
            content_hash=content_h,
        )

    return ParseResult(
        status=ParseStatus.OK,
        candidate=candidate,
        catalog_fingerprint=catalog.fingerprint,
        schema_hash=sch_hash,
        content_hash=content_h,
    )
