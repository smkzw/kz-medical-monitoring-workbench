"""R5 exact typed contract surface (``medical-monitoring-r5-exact-contract-v0.3.1``).

Implements, as immutable frozen dataclasses with fail-closed validation, every
object, field and closed enum declared by the frozen machine authority
``artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json``
(artifact SHA-256 ``3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949``,
embedded contract SHA-256 ``1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6``).

Scope
-----
* Typed public domain objects only.  No untyped dict/JSON public contract,
  no runtime schema generation from filenames, fixtures, case ids or test
  ids: the schema below is static code, cross-checked against the frozen
  JSON by ``tests/test_contracts.py`` (read-only test reads).
* Closed enums are exact tuples; every enum-typed field is validated
  fail-closed at construction.
* Canonical content hashes (see :mod:`mm_r5.canonical`) are computed from
  the object's non-hash fields with unordered reference collections sorted;
  a supplied mismatched hash is rejected at construction.
* Deferred leaves (``DEFERRED_CONTRACT_SPECS``) are fully typed and
  constructible as references/contracts, but their fields are honestly
  marked as having no upstream R4 authority yet: no later-stage data is
  pretended to exist.
* R4 is not imported here.  Read-only R4 authority adaptation is the W2
  adapter's responsibility.

Contract-constant provenance
----------------------------
Values of ``contract_constant``-kind fields are NOT emitted by the frozen
JSON (only their schema is).  They are derived here from the stage contract
v0.3 markdown (§8 domain encoding table, §10 audience lexicon, §14
elimination list, ``legacy_domain_policy``) and the frozen invariants.
``CONTRACT_CONSTANT_PIN_STATUS`` records which values are machine-pinned and
which are markdown-derived (reported to Codex as an explicit blocker: the
exact value lists of the audience encoding / lexicon / severity
line weights were never closed by an S0 SHA).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, fields as dataclass_fields
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from .canonical import (
    R5CanonicalError,
    canonical_object_hash,
    is_sha256_hex,
    register_object_fields,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class R5ContractError(Exception):
    """Closed-enum, required-field, shape or invariant violation of an R5
    typed object."""


class R5HashMismatchError(R5ContractError):
    """A supplied content hash does not match the deterministic canonical
    hash of the object's non-hash fields (tamper rejection)."""


# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

R5_CONTRACT_SCHEMA_ID = "medical-monitoring-r5-exact-contract-v0.3.1"
R5_CONTRACT_SHA256 = (
    "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6")
R5_EXACT_CONTRACT_ARTIFACT_SHA256 = (
    "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949")

RISK_OVERLAY_SHAPE = "double_chevron_badge"
EVENT_FORBIDDEN_SHAPES: Tuple[str, ...] = ("double_chevron_badge",)
UNKNOWN_DOMAIN_POLICY = "fail_closed_to_domain_confirmation_surface"
LEGACY_DOMAIN_POLICY: Dict[str, str] = {
    "OTHER": "forbidden",
    "background_treatment": "frozen_mapping_or_fail_closed",
    "non_drug_treatment": "frozen_mapping_or_fail_closed",
}


# ---------------------------------------------------------------------------
# Closed enumerations (exact vocabulary/order from exact_contract.json)
# ---------------------------------------------------------------------------

APPLICABILITY_STATES: Tuple[str, ...] = (
    "applicable", "not_applicable", "not_provided", "unknown")
AXIS_MODES: Tuple[str, ...] = ("calendar", "study_day")
CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "knowledge", "rule", "mapping", "model", "method", "coverage",
    "denominator", "population", "visibility", "mode", "user_decision")
CHANGE_KINDS: Tuple[str, ...] = (
    "initial_current", "new", "upgraded", "continued", "downgraded",
    "resolved", "reopened", "superseded", "not_evaluable", "not_comparable")
COVERAGE_STATES: Tuple[str, ...] = (
    "complete", "partial", "truncated", "unknown", "not_applicable")
DATE_STATES: Tuple[str, ...] = ("exact", "partial", "conflicted", "missing")
DENOMINATOR_KINDS: Tuple[str, ...] = (
    "enrolled_subjects", "treated_subjects", "safety_evaluable_subjects",
    "efficacy_evaluable_subjects", "subject_time", "exposure_time")
DENOMINATOR_STATES: Tuple[str, ...] = (
    "closed_positive", "closed_zero", "unknown", "unclosed")
DOMAINS: Tuple[str, ...] = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance")
EVENT_SHAPES: Tuple[str, ...] = (
    "rounded_rect", "bookmark", "capsule", "hexagon", "square", "doorframe",
    "circle", "triangle", "single_flag")
JOURNEY_SUBTYPES: Tuple[str, ...] = (
    "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
    "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
    "scale", "outcome", "trend", "protocol_deviation")
LEGACY_MAPPING_STATES: Tuple[str, ...] = ("mapped", "unmapped_fail_closed")
LEGACY_TREATMENT_KINDS: Tuple[str, ...] = (
    "background_treatment", "non_drug_treatment")
LINE_STYLES: Tuple[str, ...] = (
    "solid", "dashed", "dot_dash", "step", "trend", "bracket")
MATCH_STATES: Tuple[str, ...] = ("exact", "ambiguous", "rejected")
MEASURE_UNITS: Tuple[str, ...] = (
    "subject", "event", "site", "day", "subject_day", "percent")
NUMERATOR_KINDS: Tuple[str, ...] = (
    "individual_risk", "center_pattern", "affected_subject", "event",
    "affected_site", "project_signal", "clue", "query")
PENDING_ITEM_KINDS: Tuple[str, ...] = ("event", "risk", "visit")
PROJECTION_KINDS: Tuple[str, ...] = (
    "d09_audience", "d10_project", "ensemble", "subject_temporal",
    "aemh_history")
RATE_STATES: Tuple[str, ...] = ("permitted", "qualified", "not_evaluable")
SEVERITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")
SEVERITY_ZH: Tuple[str, ...] = ("紧急", "高", "中", "低")
SORT_DIRECTIONS: Tuple[str, ...] = ("asc", "desc")
SORT_KEYS: Tuple[str, ...] = ("priority", "change", "evidence", "site_stable")
SYMPTOM_EFFICACY_SUBTYPES: Tuple[str, ...] = (
    "symptom", "efficacy", "scale", "outcome", "trend")
VISIBILITY_STATES: Tuple[str, ...] = ("projectable", "hidden", "not_evaluable")
VISIT_KINDS: Tuple[str, ...] = ("nominal", "actual", "unscheduled")
WORKSPACE_VIEWS: Tuple[str, ...] = ("journey", "trend", "events")

_ALL_ENUMS: Dict[str, Tuple[str, ...]] = {
    "applicability_state": APPLICABILITY_STATES,
    "axis_mode": AXIS_MODES,
    "change_cause": CHANGE_CAUSES,
    "change_kind": CHANGE_KINDS,
    "coverage_state": COVERAGE_STATES,
    "date_state": DATE_STATES,
    "denominator_kind": DENOMINATOR_KINDS,
    "denominator_state": DENOMINATOR_STATES,
    "domain": DOMAINS,
    "event_shape": EVENT_SHAPES,
    "journey_subtype": JOURNEY_SUBTYPES,
    "legacy_mapping_state": LEGACY_MAPPING_STATES,
    "legacy_treatment_kind": LEGACY_TREATMENT_KINDS,
    "line_style": LINE_STYLES,
    "match_state": MATCH_STATES,
    "measure_unit": MEASURE_UNITS,
    "numerator_kind": NUMERATOR_KINDS,
    "pending_item_kind": PENDING_ITEM_KINDS,
    "projection_kind": PROJECTION_KINDS,
    "rate_state": RATE_STATES,
    "severity": SEVERITIES,
    "severity_zh": SEVERITY_ZH,
    "sort_direction": SORT_DIRECTIONS,
    "sort_key": SORT_KEYS,
    "symptom_efficacy_subtype": SYMPTOM_EFFICACY_SUBTYPES,
    "visibility_state": VISIBILITY_STATES,
    "visit_kind": VISIT_KINDS,
    "workspace_view": WORKSPACE_VIEWS,
}


def enum_values(name: str) -> Tuple[str, ...]:
    """Exact closed-enum vocabulary by contract enum name (fail closed)."""
    try:
        return _ALL_ENUMS[name]
    except KeyError:
        raise R5ContractError(f"unknown R5 enum {name!r}") from None


# ---------------------------------------------------------------------------
# Derived frozen vocabulary (provenance in module docstring / pin status)
# ---------------------------------------------------------------------------

#: journey_subtype -> the single frozen owning domain (invariant
#: ``domain_subtype_matrix``).  Derived from the journey_subtype enum and
#: stage contract v0.3 §7/§8 track decomposition.
DOMAIN_SUBTYPE_MATRIX: Dict[str, Tuple[str, ...]] = {
    "ae": ("ae",),
    "mh": ("mh",),
    "cm": ("concomitant_medication",),
    "ip": ("ip_dose", "ip_pause", "ip_resume"),
    "lab_exam": ("lab", "exam"),
    "hospital_procedure": ("hospitalization", "procedure"),
    "symptom_efficacy": ("symptom", "efficacy", "scale", "outcome", "trend"),
    "protocol_compliance": ("protocol_deviation",),
}

#: severity -> fixed audience label (invariant ``severity_lexicon_bijection``).
SEVERITY_TO_ZH: Dict[str, str] = {
    "critical": "紧急", "high": "高", "medium": "中", "low": "低",
}
ZH_TO_SEVERITY: Dict[str, str] = {v: k for k, v in SEVERITY_TO_ZH.items()}

#: legacy severity -> R5 severity (invariant ``legacy_severity_mapping``);
#: any unmapped legacy value fails closed.
LEGACY_SEVERITY_MAPPING: Dict[str, str] = {
    "severe": "high", "moderate": "medium", "mild": "low",
}

#: upstream R4 authority severity vocabulary for
#: ``severity_authority_no_promotion`` (R4 today emits high/medium/low/
#: unknown; an explicit critical authority token is the only way R5 may
#: project critical).
R4_AUTHORITY_SEVERITY_VOCABULARY: Tuple[str, ...] = (
    "critical", "high", "medium", "low", "unknown")
_SEVERITY_RANK: Dict[str, int] = {
    "critical": 3, "high": 2, "medium": 1, "low": 0,
}


def severity_to_zh(severity: str) -> str:
    """Fixed audience label of one closed severity (fail closed)."""
    if severity not in SEVERITY_TO_ZH:
        raise R5ContractError(
            f"severity must be one of {SEVERITIES!r}, got {severity!r}")
    return SEVERITY_TO_ZH[severity]


def zh_to_severity(label_zh: str) -> str:
    """Inverse of :func:`severity_to_zh` (fail closed)."""
    if label_zh not in ZH_TO_SEVERITY:
        raise R5ContractError(
            f"severity label must be one of {SEVERITY_ZH!r}, got {label_zh!r}")
    return ZH_TO_SEVERITY[label_zh]


def legacy_severity_to_r5(legacy: str) -> str:
    """Frozen legacy severity mapping (fail closed on unmapped values)."""
    if legacy not in LEGACY_SEVERITY_MAPPING:
        raise R5ContractError(
            f"unmapped legacy severity {legacy!r} fails closed; "
            f"known mapping: {LEGACY_SEVERITY_MAPPING!r}")
    return LEGACY_SEVERITY_MAPPING[legacy]


def validate_severity_authority(projected: str, upstream_authority: str) -> str:
    """Invariant ``severity_authority_no_promotion``.

    ``critical`` may appear only when the upstream R4 authority explicitly
    declares ``critical``; ``high`` never promotes to ``critical`` and no
    severity projects above its upstream authority.  An ``unknown`` upstream
    cannot authorize any severity (fail closed).
    """
    projected = _check_closed(projected, "severity", SEVERITIES)
    if upstream_authority not in R4_AUTHORITY_SEVERITY_VOCABULARY:
        raise R5ContractError(
            f"unknown upstream severity authority {upstream_authority!r}; "
            f"expected one of {R4_AUTHORITY_SEVERITY_VOCABULARY!r}")
    if upstream_authority == "unknown":
        raise R5ContractError(
            "unknown upstream authority cannot authorize any severity")
    if _SEVERITY_RANK[projected] > _SEVERITY_RANK[upstream_authority]:
        raise R5ContractError(
            f"severity promotion rejected: projected {projected!r} exceeds "
            f"upstream authority {upstream_authority!r}")
    return projected


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise R5ContractError(f"{name} must be a non-empty str, got {value!r}")
    return unicodedata.normalize("NFC", value)


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_str(value, name)


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise R5ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise R5ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_nonneg_int(value: Any, name: str) -> int:
    value = _check_int(value, name)
    if value < 0:
        raise R5ContractError(f"{name} must be a non-negative int, got {value!r}")
    return value


def _check_date(value: Any, name: str) -> date:
    # Exact ``datetime.date`` only: ``datetime.datetime`` carries time/tz
    # semantics the spine contract does not define for a main-axis date.
    if type(value) is not date:
        raise R5ContractError(
            f"{name} must be a datetime.date, got {type(value).__name__}: "
            f"{value!r}")
    return value


def _check_optional_date(value: Any, name: str) -> Optional[date]:
    if value is None:
        return None
    return _check_date(value, name)


def _check_decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise R5ContractError(
            f"{name} must be an int/Decimal, got {type(value).__name__}: "
            f"{value!r}")
    result = value if isinstance(value, Decimal) else Decimal(value)
    if not result.is_finite():
        raise R5ContractError(f"{name} must be finite, got {value!r}")
    return result


def _check_optional_decimal(value: Any, name: str) -> Optional[Decimal]:
    if value is None:
        return None
    return _check_decimal(value, name)


def _check_hash(value: Any, name: str) -> str:
    if not is_sha256_hex(value):
        raise R5ContractError(
            f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_closed(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise R5ContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_no_duplicates(values: Tuple[str, ...], name: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise R5ContractError(
                f"{name} must be duplicate-free, repeated {value!r}")
        seen.add(value)


def _freeze_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    """Normalize a many-str reference collection: list/tuple input, every
    member a non-empty NFC str, sorted (unordered set) and duplicate-free
    (invariant ``unique_reference_sets``)."""
    if not isinstance(value, (list, tuple)):
        raise R5ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_str(item, f"{name}[]") for item in value)
    _check_no_duplicates(result, name)
    return tuple(sorted(result))


def _freeze_closed_tuple(
    value: Any, name: str, allowed: Tuple[str, ...],
) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise R5ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(
        _check_closed(item, f"{name}[]", allowed) for item in value)
    _check_no_duplicates(result, name)
    return tuple(sorted(result))


def _freeze_hash_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise R5ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_hash(item, f"{name}[]") for item in value)
    _check_no_duplicates(result, name)
    return tuple(sorted(result))


def _freeze_obj_tuple(value: Any, name: str, cls: type) -> Tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise R5ContractError(f"{name} must be a list/tuple, got {value!r}")
    for item in value:
        if not isinstance(item, cls):
            raise R5ContractError(
                f"{name}[] must be {cls.__name__}, got "
                f"{type(item).__name__}")
    return tuple(value)


def _require_disjoint(
    name: str, planes: Tuple[Tuple[str, Tuple[str, ...]], ...],
) -> None:
    """Cross-plane exclusivity (invariant ``unique_reference_sets``): a ref
    may appear in at most one declared plane."""
    seen: Dict[str, str] = {}
    for plane_name, members in planes:
        for item in members:
            if item in seen:
                raise R5ContractError(
                    f"{name} planes overlap: {item!r} appears in both "
                    f"{seen[item]!r} and {plane_name!r}")
            seen[item] = plane_name


# ---------------------------------------------------------------------------
# Deferred leaf registry (honest representation of not-yet-derived leaves)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5DeferredContract:
    """One named deferred contract: a typed leaf whose fields have no
    upstream R4 public authority yet.  The fields are fully typed and
    constructible as references/contracts, but no later-stage data is
    pretended to exist (exact_contract.json ``field_mappings``,
    ``source_kind == deferred``)."""

    contract_id: str
    adapter_recipe: str
    deferred_fields: Tuple[str, ...]


DEFERRED_CONTRACT_SPECS: Tuple[R5DeferredContract, ...] = (
    R5DeferredContract(
        contract_id="aemh-match-history-public-v1",
        adapter_recipe="append_only_history_adapter",
        deferred_fields=(
            "R5AEMHMatchHistory.candidate_ref",
            "R5AEMHMatchHistory.from_snapshot_ref",
            "R5AEMHMatchHistory.history_content_hash",
            "R5AEMHMatchHistory.identity_evidence_refs",
            "R5AEMHMatchHistory.later_fact_ref",
            "R5AEMHMatchHistory.match_state",
            "R5AEMHMatchHistory.to_snapshot_ref",
        ),
    ),
    R5DeferredContract(
        contract_id="r5-authority-receipt-kind-v1",
        adapter_recipe="identity_preserving_adapter",
        deferred_fields=(
            "R5AuthorityReceipt.public_projection_kind",
        ),
    ),
    R5DeferredContract(
        contract_id="r5-center-map-cell-semantic-adapter-v1",
        adapter_recipe="identity_preserving_adapter",
        deferred_fields=(
            "R5CenterMapCell.domain",
            "R5CenterMapCell.individual_risk_refs",
            "R5CenterMapCell.measure_refs",
            "R5CenterMapCell.pattern_refs",
            "R5CenterMapCell.severity",
        ),
    ),
    R5DeferredContract(
        contract_id="r5-current-risk-set-public-v1",
        adapter_recipe="identity_preserving_adapter",
        deferred_fields=(
            "R5CurrentRiskSet.authority_receipt_ref",
            "R5CurrentRiskSet.high_risk_refs",
            "R5CurrentRiskSet.low_risk_cluster_refs",
            "R5CurrentRiskSet.medium_risk_refs",
            "R5CurrentRiskSet.resolved_history_refs",
        ),
    ),
    R5DeferredContract(
        contract_id="subject-temporal-public-v1",
        adapter_recipe="subject_temporal_identity_lookup",
        deferred_fields=(
            "R5DeepLinkState.event_ref",
            "R5DeepLinkState.risk_anchor_ref",
            "R5DeepLinkState.spine_ref",
            "R5DeepLinkState.visit_ref",
            "R5JourneyEvent.date_state",
            "R5JourneyEvent.domain",
            "R5JourneyEvent.end",
            "R5JourneyEvent.event_ref",
            "R5JourneyEvent.risk_anchor_refs",
            "R5JourneyEvent.source_locator_refs",
            "R5JourneyEvent.start",
            "R5JourneyEvent.subtype",
            "R5JourneyTrack.applicability_state",
            "R5JourneyTrack.content_hash",
            "R5JourneyTrack.domain",
            "R5JourneyTrack.event_refs",
            "R5JourneyTrack.risk_anchor_refs",
            "R5PendingDateItem.candidate_date_refs",
            "R5PendingDateItem.date_state",
            "R5PendingDateItem.domain",
            "R5PendingDateItem.item_kind",
            "R5PendingDateItem.item_ref",
            "R5PendingDateItem.source_locator_refs",
            "R5RiskAnchor.date_state",
            "R5RiskAnchor.domain",
            "R5RiskAnchor.event_ref",
            "R5RiskAnchor.risk_ref",
            "R5RiskAnchor.risk_type_zh",
            "R5RiskAnchor.severity",
            "R5RiskAnchor.visit_ref",
            "R5TemporalSpineProjection.content_hash",
            "R5TemporalSpineProjection.cutoff_ref",
            "R5TemporalSpineProjection.event_refs",
            "R5TemporalSpineProjection.pending_date_refs",
            "R5TemporalSpineProjection.phase_band_refs",
            "R5TemporalSpineProjection.spine_ref",
            "R5TemporalSpineProjection.subject_ref",
            "R5TemporalSpineProjection.visit_refs",
            "R5VisitNode.actual_date",
            "R5VisitNode.date_state",
            "R5VisitNode.nominal_date",
            "R5VisitNode.phase_ref",
            "R5VisitNode.source_locator_refs",
            "R5VisitNode.visit_kind",
            "R5VisitNode.visit_ref",
        ),
    ),
    R5DeferredContract(
        contract_id="r5-quantitative-measure-authority-v1",
        adapter_recipe="identity_preserving_adapter",
        deferred_fields=(
            "R5QuantitativeMeasure.authoritative_value_ref",
            "R5QuantitativeMeasure.authority_receipt_ref",
            "R5QuantitativeMeasure.coverage_state",
            "R5QuantitativeMeasure.cutoff_ref",
            "R5QuantitativeMeasure.denominator_exclusion_refs",
            "R5QuantitativeMeasure.denominator_kind",
            "R5QuantitativeMeasure.denominator_member_refs",
            "R5QuantitativeMeasure.denominator_state",
            "R5QuantitativeMeasure.denominator_value",
            "R5QuantitativeMeasure.evaluation_limit_refs",
            "R5QuantitativeMeasure.numerator_kind",
            "R5QuantitativeMeasure.numerator_member_refs",
            "R5QuantitativeMeasure.numerator_value",
            "R5QuantitativeMeasure.rate_state",
            "R5QuantitativeMeasure.unit",
        ),
    ),
    R5DeferredContract(
        contract_id="r5-risk-inspector-evidence-adapter-v1",
        adapter_recipe="identity_preserving_adapter",
        deferred_fields=(
            "R5RiskInspectorProjection.authority_receipt_ref",
            "R5RiskInspectorProjection.counterevidence_refs",
            "R5RiskInspectorProjection.domain",
            "R5RiskInspectorProjection.query_draft_ref",
            "R5RiskInspectorProjection.severity",
            "R5RiskInspectorProjection.source_locator_refs",
            "R5RiskInspectorProjection.support_evidence_refs",
            "R5RiskInspectorProjection.worker_output_refs",
        ),
    ),
)

DEFERRED_CONTRACT_BY_ID: Dict[str, R5DeferredContract] = {
    spec.contract_id: spec for spec in DEFERRED_CONTRACT_SPECS}

#: object name -> deferred field names (computed statically once).
_DEFERRED_FIELD_BY_OBJECT: Dict[str, Tuple[str, ...]] = {}
for _spec in DEFERRED_CONTRACT_SPECS:
    for _target in _spec.deferred_fields:
        _object_name, _field_name = _target.split(".", 1)
        _DEFERRED_FIELD_BY_OBJECT[_object_name] = (
            _DEFERRED_FIELD_BY_OBJECT.get(_object_name, ()) + (_field_name,))
_DEFERRED_FIELD_BY_OBJECT = {
    name: tuple(dict.fromkeys(fields))
    for name, fields in _DEFERRED_FIELD_BY_OBJECT.items()}


def deferred_contract(contract_id: str) -> R5DeferredContract:
    """One named deferred contract (fail closed on unknown ids)."""
    try:
        return DEFERRED_CONTRACT_BY_ID[contract_id]
    except KeyError:
        raise R5ContractError(
            f"unknown deferred contract {contract_id!r}; known: "
            f"{sorted(DEFERRED_CONTRACT_BY_ID)!r}") from None


def deferred_fields_for(object_name: str) -> Tuple[str, ...]:
    """Field names of one R5 object that are deferred (no upstream R4
    authority yet).  Known objects with no deferred fields return ().
    Unknown object names fail closed."""
    if object_name not in _CLASS_BY_NAME:
        raise R5ContractError(f"unknown R5 object {object_name!r}")
    return _DEFERRED_FIELD_BY_OBJECT.get(object_name, ())


def is_deferred_field(object_name: str, field_name: str) -> bool:
    return field_name in deferred_fields_for(object_name)


def deferred_leaf_objects() -> Tuple[str, ...]:
    """Objects whose EVERY field is deferred (fully constructible as
    references/contracts only)."""
    leaves: list[str] = []
    for class_name in sorted(_DEFERRED_FIELD_BY_OBJECT):
        cls = _CLASS_BY_NAME.get(class_name)
        if cls is None:
            raise R5ContractError(
                f"deferred object {class_name!r} has no typed class")
        field_names = tuple(f.name for f in dataclass_fields(cls))
        if set(field_names) == set(_DEFERRED_FIELD_BY_OBJECT[class_name]):
            leaves.append(class_name)
    return tuple(leaves)



# ---------------------------------------------------------------------------
# Cross-field invariant helpers
# ---------------------------------------------------------------------------


def _verify_content_hash(obj: Any, hash_field: str) -> None:
    """Canonical content-hash verification (tamper rejection): a supplied
    non-empty hash must equal sha256 of the canonical JSON of all non-hash
    fields with sorted unordered refs (else R5HashMismatchError); the field
    is then pinned to the computed value.  The empty string is the builder
    "unset" sentinel and is filled with the computed hash."""
    try:
        expected = canonical_object_hash(obj)
    except R5CanonicalError as error:
        raise R5ContractError(
            f"{type(obj).__name__} cannot be canonicalized: {error}") from error
    supplied = getattr(obj, hash_field)
    if supplied and supplied != expected:
        raise R5HashMismatchError(
            f"{type(obj).__name__}.{hash_field} {supplied!r} does not match "
            f"the deterministic canonical hash {expected!r}")
    object.__setattr__(obj, hash_field, expected)


def _check_window_order(
    start: Optional[date], end: Optional[date], owner: str,
) -> None:
    if start is not None and end is not None and end < start:
        raise R5ContractError(
            f"{owner} window_end precedes window_start "
            f"({start.isoformat()} > {end.isoformat()})")


def _check_date_geometry(
    date_state: str, start: Optional[date], end: Optional[date], owner: str,
) -> None:
    """Invariant ``date_geometry_consistency``: exact requires a precise
    main-axis date; missing never fabricates one; partial/conflicted keep
    ranges."""
    if date_state == "missing" and (start is not None or end is not None):
        raise R5ContractError(
            f"{owner} date_state=missing must carry no fabricated main-axis "
            "date (date_geometry_consistency)")
    if date_state == "exact" and start is None:
        raise R5ContractError(
            f"{owner} date_state=exact requires a precise start date "
            "(date_geometry_consistency)")


def _check_denominator_rate(measure: "R5QuantitativeMeasure") -> None:
    """Invariant ``denominator_rate_consistency``: closed_positive requires
    value > 0; closed_zero requires value == 0 and rate_state
    not_evaluable; unknown/unclosed require null value and rate_state
    not_evaluable.  R5 never recomputes the value."""
    state = measure.denominator_state
    value = measure.denominator_value
    if state == "closed_positive":
        if value is None or value <= 0:
            raise R5ContractError(
                "R5QuantitativeMeasure closed_positive requires "
                f"denominator_value > 0, got {value!r}")
    elif state == "closed_zero":
        if value is None or value != 0:
            raise R5ContractError(
                "R5QuantitativeMeasure closed_zero requires "
                f"denominator_value == 0, got {value!r}")
        if measure.rate_state != "not_evaluable":
            raise R5ContractError(
                "R5QuantitativeMeasure closed_zero requires "
                f"rate_state=not_evaluable, got {measure.rate_state!r}")
    else:  # unknown / unclosed
        if value is not None:
            raise R5ContractError(
                f"R5QuantitativeMeasure denominator_state={state!r} requires "
                f"null denominator_value, got {value!r}")
        if measure.rate_state != "not_evaluable":
            raise R5ContractError(
                f"R5QuantitativeMeasure denominator_state={state!r} requires "
                f"rate_state=not_evaluable, got {measure.rate_state!r}")


