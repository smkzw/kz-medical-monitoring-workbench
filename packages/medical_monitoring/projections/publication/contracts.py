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
# Typed objects (exact keys/cardinality/nullability from exact_contract.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceRevisionContentPair:
    """One source revision -> content hash binding (R4 authority value)."""

    revision_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id",
                           _check_str(self.revision_id,
                                      "SourceRevisionContentPair.revision_id"))
        # Opaque R4-derived hash: shape-checked, never recomputed locally.
        object.__setattr__(self, "content_hash",
                           _check_hash(self.content_hash,
                                       "SourceRevisionContentPair.content_hash"))


@dataclass(frozen=True)
class R5AEMHMatchHistory:
    """Append-only AE/MH later-recorded matching history (deferred leaf)."""

    candidate_ref: str
    from_snapshot_ref: str
    history_content_hash: str
    identity_evidence_refs: Tuple[str, ...]
    later_fact_ref: Optional[str]
    match_state: str
    to_snapshot_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_ref", _check_str(
            self.candidate_ref, "R5AEMHMatchHistory.candidate_ref"))
        object.__setattr__(self, "from_snapshot_ref", _check_str(
            self.from_snapshot_ref, "R5AEMHMatchHistory.from_snapshot_ref"))
        object.__setattr__(self, "to_snapshot_ref", _check_str(
            self.to_snapshot_ref, "R5AEMHMatchHistory.to_snapshot_ref"))
        object.__setattr__(self, "later_fact_ref", _check_optional_str(
            self.later_fact_ref, "R5AEMHMatchHistory.later_fact_ref"))
        object.__setattr__(self, "match_state", _check_closed(
            self.match_state, "R5AEMHMatchHistory.match_state", MATCH_STATES))
        object.__setattr__(self, "identity_evidence_refs", _freeze_str_tuple(
            self.identity_evidence_refs,
            "R5AEMHMatchHistory.identity_evidence_refs"))
        _verify_content_hash(self, "history_content_hash")


@dataclass(frozen=True)
class R5AudienceEncodingRegistry:
    """Frozen audience encoding: domain shapes/labels, severity lexicon,
    legacy-treatment mapping and the risk overlay shape."""

    domain_items: Tuple["R5DomainEncodingItem", ...]
    legacy_treatment_mapping: Tuple["R5LegacyTreatmentMappingItem", ...]
    risk_overlay_shape: str
    severity_items: Tuple["R5SeverityLexiconItem", ...]
    symptom_efficacy_subtypes: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_items", _freeze_obj_tuple(
            self.domain_items, "R5AudienceEncodingRegistry.domain_items",
            R5DomainEncodingItem))
        object.__setattr__(self, "legacy_treatment_mapping", _freeze_obj_tuple(
            self.legacy_treatment_mapping,
            "R5AudienceEncodingRegistry.legacy_treatment_mapping",
            R5LegacyTreatmentMappingItem))
        if self.risk_overlay_shape != RISK_OVERLAY_SHAPE:
            raise R5ContractError(
                "R5AudienceEncodingRegistry.risk_overlay_shape must be "
                f"{RISK_OVERLAY_SHAPE!r}, got {self.risk_overlay_shape!r}")
        object.__setattr__(self, "severity_items", _freeze_obj_tuple(
            self.severity_items,
            "R5AudienceEncodingRegistry.severity_items",
            R5SeverityLexiconItem))
        object.__setattr__(self, "symptom_efficacy_subtypes",
                           _freeze_closed_tuple(
                               self.symptom_efficacy_subtypes,
                               "R5AudienceEncodingRegistry."
                               "symptom_efficacy_subtypes",
                               SYMPTOM_EFFICACY_SUBTYPES))
        # Invariants ``severity_lexicon_bijection`` and ``risk_overlay_unique``.
        severities_seen: Dict[str, str] = {}
        for item in self.severity_items:
            expected_zh = severity_to_zh(item.severity)
            if item.label_zh != expected_zh:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.severity_items label "
                    f"{item.label_zh!r} for severity {item.severity!r} must "
                    f"be {expected_zh!r}")
            if item.severity in severities_seen:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.severity_items must contain "
                    f"severity {item.severity!r} exactly once")
            severities_seen[item.severity] = item.label_zh
        if set(severities_seen) != set(SEVERITIES):
            raise R5ContractError(
                "R5AudienceEncodingRegistry.severity_items must cover "
                f"exactly {SEVERITIES!r}, got {sorted(severities_seen)!r}")
        domains_seen: Dict[str, R5DomainEncodingItem] = {}
        for item in self.domain_items:
            if item.domain in domains_seen:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.domain_items must contain "
                    f"domain {item.domain!r} exactly once")
            domains_seen[item.domain] = item
            if item.event_shape in EVENT_FORBIDDEN_SHAPES:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry risk overlay shape "
                    f"{item.event_shape!r} is forbidden on events "
                    "(risk_overlay_unique)")
        if set(domains_seen) != set(DOMAINS):
            raise R5ContractError(
                "R5AudienceEncodingRegistry.domain_items must cover exactly "
                f"{DOMAINS!r}, got {sorted(domains_seen)!r}")
        symptom_encoding = domains_seen["symptom_efficacy"]
        if (symptom_encoding.event_shape, symptom_encoding.line_style) != (
                "circle", "trend"):
            raise R5ContractError(
                "symptom_efficacy encoding must be circle + trend")


@dataclass(frozen=True)
class R5AudienceLexicon:
    """Frozen audience lexicon: allowed/forbidden terms and their fixed
    audience labels."""

    content_hash: str
    forbidden_terms: Tuple[str, ...]
    items: Tuple["R5LexiconItem", ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "forbidden_terms", _freeze_str_tuple(
            self.forbidden_terms, "R5AudienceLexicon.forbidden_terms"))
        object.__setattr__(self, "items", _freeze_obj_tuple(
            self.items, "R5AudienceLexicon.items", R5LexiconItem))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5AuthorityReceipt:
    """Per-leaf authority receipt: every binding identity, evaluation
    content identity, visibility decision and source revision-content pair
    of one public projection.  Hash fields are R4-authoritative values
    (shape-checked here, verified against R4 by the W2 adapter)."""

    audience_contract_id: str
    cutoff_ref: Optional[str]
    evaluation_content_identities: Tuple[str, ...]
    project_ref: str
    public_projection_content_hash: str
    public_projection_id: str
    public_projection_kind: str
    run_ref: str
    snapshot_ref: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    visibility_decision_hash: str
    visibility_decision_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "audience_contract_id", _check_str(
            self.audience_contract_id,
            "R5AuthorityReceipt.audience_contract_id"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "R5AuthorityReceipt.cutoff_ref"))
        object.__setattr__(self, "project_ref", _check_str(
            self.project_ref, "R5AuthorityReceipt.project_ref"))
        object.__setattr__(self, "run_ref", _check_str(
            self.run_ref, "R5AuthorityReceipt.run_ref"))
        object.__setattr__(self, "snapshot_ref", _check_str(
            self.snapshot_ref, "R5AuthorityReceipt.snapshot_ref"))
        object.__setattr__(self, "public_projection_id", _check_str(
            self.public_projection_id,
            "R5AuthorityReceipt.public_projection_id"))
        object.__setattr__(self, "public_projection_kind", _check_closed(
            self.public_projection_kind,
            "R5AuthorityReceipt.public_projection_kind", PROJECTION_KINDS))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5AuthorityReceipt.visibility_decision_id"))
        object.__setattr__(self, "public_projection_content_hash",
                           _check_hash(
                               self.public_projection_content_hash,
                               "R5AuthorityReceipt."
                               "public_projection_content_hash"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5AuthorityReceipt.visibility_decision_hash"))
        object.__setattr__(self, "evaluation_content_identities",
                           _freeze_hash_tuple(
                               self.evaluation_content_identities,
                               "R5AuthorityReceipt."
                               "evaluation_content_identities"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "R5AuthorityReceipt."
                               "source_revision_content_pairs",
                               SourceRevisionContentPair))


@dataclass(frozen=True)
class R5CenterMapCell:
    """One center x domain cell of the center risk map."""

    domain: str
    individual_risk_refs: Tuple[str, ...]
    measure_refs: Tuple[str, ...]
    pattern_refs: Tuple[str, ...]
    severity: str
    site_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5CenterMapCell.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5CenterMapCell.severity", SEVERITIES))
        object.__setattr__(self, "site_ref", _check_str(
            self.site_ref, "R5CenterMapCell.site_ref"))
        object.__setattr__(self, "individual_risk_refs", _freeze_str_tuple(
            self.individual_risk_refs,
            "R5CenterMapCell.individual_risk_refs"))
        object.__setattr__(self, "measure_refs", _freeze_str_tuple(
            self.measure_refs, "R5CenterMapCell.measure_refs"))
        object.__setattr__(self, "pattern_refs", _freeze_str_tuple(
            self.pattern_refs, "R5CenterMapCell.pattern_refs"))


@dataclass(frozen=True)
class R5CenterMapProjection:
    """Center risk map projection: cells, replay instance and the stable
    (non-punitive) site ordering."""

    cells: Tuple[R5CenterMapCell, ...]
    content_hash: str
    projection_instance: "R5ProjectionInstance"
    stable_site_order: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", _freeze_obj_tuple(
            self.cells, "R5CenterMapProjection.cells", R5CenterMapCell))
        if not isinstance(self.projection_instance, R5ProjectionInstance):
            raise R5ContractError(
                "R5CenterMapProjection.projection_instance must be an "
                f"R5ProjectionInstance, got {type(self.projection_instance).__name__}")
        if not isinstance(self.stable_site_order, (list, tuple)):
            raise R5ContractError(
                "R5CenterMapProjection.stable_site_order must be a "
                f"list/tuple, got {type(self.stable_site_order).__name__}")
        # Stable ordering is ORDER-SIGNIFICANT: preserved verbatim, unique.
        object.__setattr__(self, "stable_site_order", tuple(
            _check_str(site, "R5CenterMapProjection.stable_site_order[]")
            for site in self.stable_site_order))
        _check_no_duplicates(
            self.stable_site_order,
            "R5CenterMapProjection.stable_site_order")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5ChangeBand:
    """One risk's change band: closed kind plus the cause plane."""

    authority_receipt_ref: str
    change_cause: Optional[str]
    change_kind: str
    current_snapshot_ref: str
    prior_snapshot_ref: Optional[str]
    risk_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5ChangeBand.authority_receipt_ref"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5ChangeBand.risk_ref"))
        object.__setattr__(self, "current_snapshot_ref", _check_str(
            self.current_snapshot_ref,
            "R5ChangeBand.current_snapshot_ref"))
        object.__setattr__(self, "prior_snapshot_ref", _check_optional_str(
            self.prior_snapshot_ref, "R5ChangeBand.prior_snapshot_ref"))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "R5ChangeBand.change_kind", CHANGE_KINDS))
        if self.change_cause is not None:
            object.__setattr__(self, "change_cause", _check_closed(
                self.change_cause, "R5ChangeBand.change_cause", CHANGE_CAUSES))


@dataclass(frozen=True)
class R5CurrentRiskSet:
    """Current high/medium full set, low-risk cluster and resolved history
    refs.  Planes are mutually exclusive (invariant
    ``unique_reference_sets``)."""

    authority_receipt_ref: str
    high_risk_refs: Tuple[str, ...]
    low_risk_cluster_refs: Tuple[str, ...]
    medium_risk_refs: Tuple[str, ...]
    resolved_history_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5CurrentRiskSet.authority_receipt_ref"))
        object.__setattr__(self, "high_risk_refs", _freeze_str_tuple(
            self.high_risk_refs, "R5CurrentRiskSet.high_risk_refs"))
        object.__setattr__(self, "medium_risk_refs", _freeze_str_tuple(
            self.medium_risk_refs, "R5CurrentRiskSet.medium_risk_refs"))
        object.__setattr__(self, "low_risk_cluster_refs", _freeze_str_tuple(
            self.low_risk_cluster_refs,
            "R5CurrentRiskSet.low_risk_cluster_refs"))
        object.__setattr__(self, "resolved_history_refs", _freeze_str_tuple(
            self.resolved_history_refs,
            "R5CurrentRiskSet.resolved_history_refs"))
        _require_disjoint("R5CurrentRiskSet", (
            ("high_risk", self.high_risk_refs),
            ("medium_risk", self.medium_risk_refs),
            ("low_risk_cluster", self.low_risk_cluster_refs),
            ("resolved_history", self.resolved_history_refs),
        ))


@dataclass(frozen=True)
class R5DeepLinkState:
    """Canonical deep-link state: authoritative identities plus the
    canonical view/axis/window."""

    axis_mode: str
    cutoff_ref: str
    event_ref: Optional[str]
    project_ref: str
    return_context_key: str
    risk_anchor_ref: str
    risk_ref: str
    run_ref: str
    site_ref: Optional[str]
    snapshot_ref: str
    source_locator_ref: Optional[str]
    spine_ref: str
    subject_ref: str
    view: str
    visit_ref: Optional[str]
    window_end: Optional[date]
    window_start: Optional[date]

    def __post_init__(self) -> None:
        object.__setattr__(self, "axis_mode", _check_closed(
            self.axis_mode, "R5DeepLinkState.axis_mode", AXIS_MODES))
        object.__setattr__(self, "view", _check_closed(
            self.view, "R5DeepLinkState.view", WORKSPACE_VIEWS))
        for name in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                     "return_context_key", "risk_anchor_ref", "risk_ref",
                     "spine_ref", "subject_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5DeepLinkState.{name}"))
        for name in ("event_ref", "site_ref", "source_locator_ref",
                     "visit_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5DeepLinkState.{name}"))
        object.__setattr__(self, "window_start", _check_optional_date(
            self.window_start, "R5DeepLinkState.window_start"))
        object.__setattr__(self, "window_end", _check_optional_date(
            self.window_end, "R5DeepLinkState.window_end"))
        _check_window_order(self.window_start, self.window_end,
                            "R5DeepLinkState")


@dataclass(frozen=True)
class R5DomainEncodingItem:
    """One domain's audience encoding: event shape, line style and the
    fixed Chinese short label (stage contract v0.3 §8)."""

    domain: str
    event_shape: str
    line_style: str
    short_label_zh: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5DomainEncodingItem.domain", DOMAINS))
        object.__setattr__(self, "event_shape", _check_closed(
            self.event_shape, "R5DomainEncodingItem.event_shape",
            EVENT_SHAPES))
        object.__setattr__(self, "line_style", _check_closed(
            self.line_style, "R5DomainEncodingItem.line_style", LINE_STYLES))
        object.__setattr__(self, "short_label_zh", _check_str(
            self.short_label_zh, "R5DomainEncodingItem.short_label_zh"))
        if self.event_shape in EVENT_FORBIDDEN_SHAPES:
            raise R5ContractError(
                "R5DomainEncodingItem.event_shape "
                f"{self.event_shape!r} is forbidden on events "
                "(risk_overlay_unique)")


@dataclass(frozen=True)
class R5FilterState:
    """Ephemeral filter state of one view."""

    change_kind: Tuple[str, ...]
    domain: Tuple[str, ...]
    include_low: bool
    severity: Tuple[str, ...]
    site_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "change_kind", _freeze_closed_tuple(
            self.change_kind, "R5FilterState.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "domain", _freeze_closed_tuple(
            self.domain, "R5FilterState.domain", DOMAINS))
        object.__setattr__(self, "severity", _freeze_closed_tuple(
            self.severity, "R5FilterState.severity", SEVERITIES))
        object.__setattr__(self, "site_refs", _freeze_str_tuple(
            self.site_refs, "R5FilterState.site_refs"))
        object.__setattr__(self, "include_low", _check_bool(
            self.include_low, "R5FilterState.include_low"))


@dataclass(frozen=True)
class R5JourneyEvent:
    """One journey event on its owning domain track (deferred leaf)."""

    date_state: str
    domain: str
    end: Optional[date]
    event_ref: str
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    start: Optional[date]
    subtype: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5JourneyEvent.domain", DOMAINS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5JourneyEvent.date_state", DATE_STATES))
        object.__setattr__(self, "subtype", _check_closed(
            self.subtype, "R5JourneyEvent.subtype", JOURNEY_SUBTYPES))
        if self.subtype not in DOMAIN_SUBTYPE_MATRIX[self.domain]:
            raise R5ContractError(
                "R5JourneyEvent.domain_subtype_matrix violation: subtype "
                f"{self.subtype!r} does not belong to domain "
                f"{self.domain!r}")
        object.__setattr__(self, "event_ref", _check_str(
            self.event_ref, "R5JourneyEvent.event_ref"))
        object.__setattr__(self, "risk_anchor_refs", _freeze_str_tuple(
            self.risk_anchor_refs, "R5JourneyEvent.risk_anchor_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5JourneyEvent.source_locator_refs"))
        object.__setattr__(self, "start", _check_optional_date(
            self.start, "R5JourneyEvent.start"))
        object.__setattr__(self, "end", _check_optional_date(
            self.end, "R5JourneyEvent.end"))
        _check_date_geometry(self.date_state, self.start, self.end,
                             "R5JourneyEvent")
        _check_window_order(self.start, self.end, "R5JourneyEvent")


@dataclass(frozen=True)
class R5JourneyTrack:
    """One domain track of the subject journey (deferred leaf)."""

    applicability_state: str
    content_hash: str
    domain: str
    event_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "applicability_state", _check_closed(
            self.applicability_state, "R5JourneyTrack.applicability_state",
            APPLICABILITY_STATES))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5JourneyTrack.domain", DOMAINS))
        object.__setattr__(self, "event_refs", _freeze_str_tuple(
            self.event_refs, "R5JourneyTrack.event_refs"))
        object.__setattr__(self, "risk_anchor_refs", _freeze_str_tuple(
            self.risk_anchor_refs, "R5JourneyTrack.risk_anchor_refs"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5LegacyTreatmentMappingItem:
    """Frozen legacy treatment domain mapping item.  Without a frozen
    project mapping the item stays ``unmapped_fail_closed`` with all
    targets null (invariant ``legacy_treatment_fail_closed``)."""

    legacy_kind: str
    mapping_authority_ref: Optional[str]
    mapping_state: str
    target_domain: Optional[str]
    target_subtype: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "legacy_kind", _check_closed(
            self.legacy_kind, "R5LegacyTreatmentMappingItem.legacy_kind",
            LEGACY_TREATMENT_KINDS))
        object.__setattr__(self, "mapping_state", _check_closed(
            self.mapping_state, "R5LegacyTreatmentMappingItem.mapping_state",
            LEGACY_MAPPING_STATES))
        object.__setattr__(self, "mapping_authority_ref", _check_optional_str(
            self.mapping_authority_ref,
            "R5LegacyTreatmentMappingItem.mapping_authority_ref"))
        if self.target_domain is not None:
            object.__setattr__(self, "target_domain", _check_closed(
                self.target_domain,
                "R5LegacyTreatmentMappingItem.target_domain", DOMAINS))
        if self.target_subtype is not None:
            object.__setattr__(self, "target_subtype", _check_closed(
                self.target_subtype,
                "R5LegacyTreatmentMappingItem.target_subtype",
                JOURNEY_SUBTYPES))
        if self.mapping_state == "mapped":
            if (self.mapping_authority_ref is None
                    or self.target_domain is None
                    or self.target_subtype is None):
                raise R5ContractError(
                    "R5LegacyTreatmentMappingItem mapped requires "
                    "mapping_authority_ref, target_domain and "
                    "target_subtype")
        else:  # unmapped_fail_closed
            if (self.mapping_authority_ref is not None
                    or self.target_domain is not None
                    or self.target_subtype is not None):
                raise R5ContractError(
                    "R5LegacyTreatmentMappingItem unmapped_fail_closed "
                    "requires all targets null (enters domain-confirmation "
                    "surface)")


@dataclass(frozen=True)
class R5LexiconItem:
    """One lexicon token with its audience label and allow flag."""

    audience_allowed: bool
    label_zh: str
    token: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "token", _check_str(
            self.token, "R5LexiconItem.token"))
        object.__setattr__(self, "label_zh", _check_str(
            self.label_zh, "R5LexiconItem.label_zh"))
        object.__setattr__(self, "audience_allowed", _check_bool(
            self.audience_allowed, "R5LexiconItem.audience_allowed"))


@dataclass(frozen=True)
class R5PageState:
    """Ephemeral pagination state."""

    page_index: int
    page_size: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "page_index", _check_nonneg_int(
            self.page_index, "R5PageState.page_index"))
        object.__setattr__(self, "page_size", _check_int(
            self.page_size, "R5PageState.page_size"))
        if self.page_size < 1:
            raise R5ContractError(
                f"R5PageState.page_size must be >= 1, got {self.page_size!r}")


@dataclass(frozen=True)
class R5PendingDateItem:
    """One item parked in the date-confirmation area: its date is never
    exact and never fabricated on the main axis (deferred leaf)."""

    candidate_date_refs: Tuple[str, ...]
    date_state: str
    domain: str
    item_kind: str
    item_ref: str
    source_locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_kind", _check_closed(
            self.item_kind, "R5PendingDateItem.item_kind",
            PENDING_ITEM_KINDS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5PendingDateItem.date_state", DATE_STATES))
        if self.date_state == "exact":
            raise R5ContractError(
                "R5PendingDateItem.date_state must not be exact: a pending "
                "item never carries a precise main-axis date "
                "(date_geometry_consistency)")
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5PendingDateItem.domain", DOMAINS))
        object.__setattr__(self, "item_ref", _check_str(
            self.item_ref, "R5PendingDateItem.item_ref"))
        object.__setattr__(self, "candidate_date_refs", _freeze_str_tuple(
            self.candidate_date_refs,
            "R5PendingDateItem.candidate_date_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "R5PendingDateItem.source_locator_refs"))


@dataclass(frozen=True)
class R5ProjectCockpitProjection:
    """Project risk cockpit projection: current risk set, change bands,
    measures and center map bound to one replay instance."""

    center_map_ref: str
    change_band_refs: Tuple[str, ...]
    content_hash: str
    current_risk_set_ref: str
    measure_refs: Tuple[str, ...]
    projection_instance: R5ProjectionInstance
    selected_risk_ref: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "center_map_ref", _check_str(
            self.center_map_ref, "R5ProjectCockpitProjection.center_map_ref"))
        object.__setattr__(self, "current_risk_set_ref", _check_str(
            self.current_risk_set_ref,
            "R5ProjectCockpitProjection.current_risk_set_ref"))
        object.__setattr__(self, "selected_risk_ref", _check_optional_str(
            self.selected_risk_ref,
            "R5ProjectCockpitProjection.selected_risk_ref"))
        object.__setattr__(self, "change_band_refs", _freeze_str_tuple(
            self.change_band_refs,
            "R5ProjectCockpitProjection.change_band_refs"))
        object.__setattr__(self, "measure_refs", _freeze_str_tuple(
            self.measure_refs, "R5ProjectCockpitProjection.measure_refs"))
        if not isinstance(self.projection_instance, R5ProjectionInstance):
            raise R5ContractError(
                "R5ProjectCockpitProjection.projection_instance must be an "
                "R5ProjectionInstance, got "
                f"{type(self.projection_instance).__name__}")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5ProjectionInstance:
    """Separate opaque run/snapshot audit identity and replay-stable
    content identity.  ``content_hash`` covers the non-hash fields
    (invariant ``canonical_content_hash``); ``replay_content_identity`` is
    an R4-derived opaque value (shape-checked, not recomputed)."""

    authority_receipt_ref: str
    content_hash: str
    opaque_run_ref: str
    opaque_snapshot_ref: str
    replay_content_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5ProjectionInstance.authority_receipt_ref"))
        object.__setattr__(self, "opaque_run_ref", _check_str(
            self.opaque_run_ref, "R5ProjectionInstance.opaque_run_ref"))
        object.__setattr__(self, "opaque_snapshot_ref", _check_str(
            self.opaque_snapshot_ref,
            "R5ProjectionInstance.opaque_snapshot_ref"))
        object.__setattr__(self, "replay_content_identity", _check_hash(
            self.replay_content_identity,
            "R5ProjectionInstance.replay_content_identity"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5QuantitativeMeasure:
    """One quantitative measure projected verbatim from R4 authority:
    numerator/denominator member refs, value, unit, rate state, coverage,
    cutoff and evaluation limits.  R5 never recomputes (deferred leaf)."""

    authoritative_value_ref: str
    authority_receipt_ref: str
    coverage_state: str
    cutoff_ref: str
    denominator_exclusion_refs: Tuple[str, ...]
    denominator_kind: str
    denominator_member_refs: Tuple[str, ...]
    denominator_state: str
    denominator_value: Optional[Decimal]
    evaluation_limit_refs: Tuple[str, ...]
    numerator_kind: str
    numerator_member_refs: Tuple[str, ...]
    numerator_value: Decimal
    rate_state: str
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authoritative_value_ref", _check_str(
            self.authoritative_value_ref,
            "R5QuantitativeMeasure.authoritative_value_ref"))
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5QuantitativeMeasure.authority_receipt_ref"))
        object.__setattr__(self, "cutoff_ref", _check_str(
            self.cutoff_ref, "R5QuantitativeMeasure.cutoff_ref"))
        object.__setattr__(self, "coverage_state", _check_closed(
            self.coverage_state, "R5QuantitativeMeasure.coverage_state",
            COVERAGE_STATES))
        object.__setattr__(self, "denominator_kind", _check_closed(
            self.denominator_kind,
            "R5QuantitativeMeasure.denominator_kind", DENOMINATOR_KINDS))
        object.__setattr__(self, "denominator_state", _check_closed(
            self.denominator_state,
            "R5QuantitativeMeasure.denominator_state", DENOMINATOR_STATES))
        object.__setattr__(self, "numerator_kind", _check_closed(
            self.numerator_kind, "R5QuantitativeMeasure.numerator_kind",
            NUMERATOR_KINDS))
        object.__setattr__(self, "rate_state", _check_closed(
            self.rate_state, "R5QuantitativeMeasure.rate_state", RATE_STATES))
        object.__setattr__(self, "unit", _check_closed(
            self.unit, "R5QuantitativeMeasure.unit", MEASURE_UNITS))
        object.__setattr__(self, "numerator_value", _check_decimal(
            self.numerator_value, "R5QuantitativeMeasure.numerator_value"))
        object.__setattr__(self, "denominator_value", _check_optional_decimal(
            self.denominator_value,
            "R5QuantitativeMeasure.denominator_value"))
        object.__setattr__(self, "numerator_member_refs", _freeze_str_tuple(
            self.numerator_member_refs,
            "R5QuantitativeMeasure.numerator_member_refs"))
        object.__setattr__(self, "denominator_member_refs", _freeze_str_tuple(
            self.denominator_member_refs,
            "R5QuantitativeMeasure.denominator_member_refs"))
        object.__setattr__(self, "denominator_exclusion_refs",
                           _freeze_str_tuple(
                               self.denominator_exclusion_refs,
                               "R5QuantitativeMeasure."
                               "denominator_exclusion_refs"))
        object.__setattr__(self, "evaluation_limit_refs", _freeze_str_tuple(
            self.evaluation_limit_refs,
            "R5QuantitativeMeasure.evaluation_limit_refs"))
        _check_denominator_rate(self)


@dataclass(frozen=True)
class R5ReturnContext:
    """Return context: canonical URL state plus ephemeral client state.
    ``canonical_state_hash`` covers the non-hash fields (invariant
    ``canonical_content_hash``)."""

    canonical_state_hash: str
    deep_link_state: R5DeepLinkState
    filter_state: R5FilterState
    inspector_width: int
    page_state: R5PageState
    scroll_state: "R5ScrollState"
    sort_state: "R5SortState"
    temporary_expansion_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name, cls in (
                ("deep_link_state", R5DeepLinkState),
                ("filter_state", R5FilterState),
                ("page_state", R5PageState),
                ("scroll_state", R5ScrollState),
                ("sort_state", R5SortState)):
            value = getattr(self, name)
            if not isinstance(value, cls):
                raise R5ContractError(
                    f"R5ReturnContext.{name} must be a {cls.__name__}, got "
                    f"{type(value).__name__}")
        object.__setattr__(self, "inspector_width", _check_nonneg_int(
            self.inspector_width, "R5ReturnContext.inspector_width"))
        object.__setattr__(self, "temporary_expansion_refs",
                           _freeze_str_tuple(
                               self.temporary_expansion_refs,
                               "R5ReturnContext.temporary_expansion_refs"))
        _verify_content_hash(self, "canonical_state_hash")


@dataclass(frozen=True)
class R5RiskAnchor:
    """One risk anchor on the temporal spine (deferred leaf)."""

    date_state: str
    domain: str
    event_ref: Optional[str]
    risk_ref: str
    risk_type_zh: str
    severity: str
    visit_ref: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5RiskAnchor.date_state", DATE_STATES))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5RiskAnchor.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5RiskAnchor.severity", SEVERITIES))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5RiskAnchor.risk_ref"))
        object.__setattr__(self, "risk_type_zh", _check_str(
            self.risk_type_zh, "R5RiskAnchor.risk_type_zh"))
        object.__setattr__(self, "event_ref", _check_optional_str(
            self.event_ref, "R5RiskAnchor.event_ref"))
        object.__setattr__(self, "visit_ref", _check_optional_str(
            self.visit_ref, "R5RiskAnchor.visit_ref"))


@dataclass(frozen=True)
class R5RiskInspectorProjection:
    """Risk Inspector evidence binding: baseline, attempts, verification,
    conflict, adjudication and source refs.  Support and counterevidence
    are exclusive planes (invariant ``unique_reference_sets``)."""

    adjudication_ref: Optional[str]
    analysis_attempt_refs: Tuple[str, ...]
    authority_receipt_ref: str
    baseline_assessment_refs: Tuple[str, ...]
    baseline_item_refs: Tuple[str, ...]
    conflict_refs: Tuple[str, ...]
    counterevidence_refs: Tuple[str, ...]
    domain: str
    query_draft_ref: Optional[str]
    risk_ref: str
    severity: str
    source_locator_refs: Tuple[str, ...]
    support_evidence_refs: Tuple[str, ...]
    verification_refs: Tuple[str, ...]
    worker_output_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5RiskInspectorProjection.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5RiskInspectorProjection.severity", SEVERITIES))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5RiskInspectorProjection.risk_ref"))
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5RiskInspectorProjection.authority_receipt_ref"))
        object.__setattr__(self, "adjudication_ref", _check_optional_str(
            self.adjudication_ref,
            "R5RiskInspectorProjection.adjudication_ref"))
        object.__setattr__(self, "query_draft_ref", _check_optional_str(
            self.query_draft_ref,
            "R5RiskInspectorProjection.query_draft_ref"))
        object.__setattr__(self, "analysis_attempt_refs", _freeze_str_tuple(
            self.analysis_attempt_refs,
            "R5RiskInspectorProjection.analysis_attempt_refs"))
        object.__setattr__(self, "baseline_assessment_refs",
                           _freeze_str_tuple(
                               self.baseline_assessment_refs,
                               "R5RiskInspectorProjection."
                               "baseline_assessment_refs"))
        object.__setattr__(self, "baseline_item_refs", _freeze_str_tuple(
            self.baseline_item_refs,
            "R5RiskInspectorProjection.baseline_item_refs"))
        object.__setattr__(self, "conflict_refs", _freeze_str_tuple(
            self.conflict_refs, "R5RiskInspectorProjection.conflict_refs"))
        object.__setattr__(self, "counterevidence_refs", _freeze_str_tuple(
            self.counterevidence_refs,
            "R5RiskInspectorProjection.counterevidence_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "R5RiskInspectorProjection.source_locator_refs"))
        object.__setattr__(self, "support_evidence_refs", _freeze_str_tuple(
            self.support_evidence_refs,
            "R5RiskInspectorProjection.support_evidence_refs"))
        object.__setattr__(self, "verification_refs", _freeze_str_tuple(
            self.verification_refs,
            "R5RiskInspectorProjection.verification_refs"))
        object.__setattr__(self, "worker_output_refs", _freeze_str_tuple(
            self.worker_output_refs,
            "R5RiskInspectorProjection.worker_output_refs"))
        overlap = set(self.support_evidence_refs) & set(
            self.counterevidence_refs)
        if overlap:
            raise R5ContractError(
                "R5RiskInspectorProjection support/counterevidence planes "
                f"overlap: {sorted(overlap)!r}")


@dataclass(frozen=True)
class R5ScrollState:
    """Ephemeral scroll offsets of the three surfaces."""

    center_map_y: int
    project_list_y: int
    workspace_y: int

    def __post_init__(self) -> None:
        for name in ("center_map_y", "project_list_y", "workspace_y"):
            object.__setattr__(self, name, _check_nonneg_int(
                getattr(self, name), f"R5ScrollState.{name}"))


@dataclass(frozen=True)
class R5SeverityLexiconItem:
    """One severity's fixed audience label and line weight."""

    label_zh: str
    line_weight: int
    severity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5SeverityLexiconItem.severity", SEVERITIES))
        object.__setattr__(self, "label_zh", _check_str(
            self.label_zh, "R5SeverityLexiconItem.label_zh"))
        object.__setattr__(self, "line_weight", _check_nonneg_int(
            self.line_weight, "R5SeverityLexiconItem.line_weight"))


@dataclass(frozen=True)
class R5SortState:
    """Ephemeral sort state of one view."""

    direction: str
    key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _check_closed(
            self.key, "R5SortState.key", SORT_KEYS))
        object.__setattr__(self, "direction", _check_closed(
            self.direction, "R5SortState.direction", SORT_DIRECTIONS))


@dataclass(frozen=True)
class R5SubjectWorkspaceState:
    """Subject Workspace shared state: one temporal spine, one window and
    one selection across the three views."""

    active_view: str
    axis_mode: str
    content_hash: str
    selected_event_ref: Optional[str]
    selected_risk_ref: Optional[str]
    selected_visit_ref: Optional[str]
    spine_ref: str
    subject_ref: str
    window_end: Optional[date]
    window_start: Optional[date]

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_view", _check_closed(
            self.active_view, "R5SubjectWorkspaceState.active_view",
            WORKSPACE_VIEWS))
        object.__setattr__(self, "axis_mode", _check_closed(
            self.axis_mode, "R5SubjectWorkspaceState.axis_mode", AXIS_MODES))
        object.__setattr__(self, "subject_ref", _check_str(
            self.subject_ref, "R5SubjectWorkspaceState.subject_ref"))
        object.__setattr__(self, "spine_ref", _check_str(
            self.spine_ref, "R5SubjectWorkspaceState.spine_ref"))
        object.__setattr__(self, "selected_event_ref", _check_optional_str(
            self.selected_event_ref,
            "R5SubjectWorkspaceState.selected_event_ref"))
        object.__setattr__(self, "selected_risk_ref", _check_optional_str(
            self.selected_risk_ref,
            "R5SubjectWorkspaceState.selected_risk_ref"))
        object.__setattr__(self, "selected_visit_ref", _check_optional_str(
            self.selected_visit_ref,
            "R5SubjectWorkspaceState.selected_visit_ref"))
        object.__setattr__(self, "window_start", _check_optional_date(
            self.window_start, "R5SubjectWorkspaceState.window_start"))
        object.__setattr__(self, "window_end", _check_optional_date(
            self.window_end, "R5SubjectWorkspaceState.window_end"))
        _check_window_order(self.window_start, self.window_end,
                            "R5SubjectWorkspaceState")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5TemporalSpineProjection:
    """Temporal spine: visits, events and pending-date refs on one shared
    spine (deferred leaf)."""

    content_hash: str
    cutoff_ref: str
    event_refs: Tuple[str, ...]
    pending_date_refs: Tuple[str, ...]
    phase_band_refs: Tuple[str, ...]
    spine_ref: str
    subject_ref: str
    visit_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "spine_ref", _check_str(
            self.spine_ref, "R5TemporalSpineProjection.spine_ref"))
        object.__setattr__(self, "subject_ref", _check_str(
            self.subject_ref, "R5TemporalSpineProjection.subject_ref"))
        object.__setattr__(self, "cutoff_ref", _check_str(
            self.cutoff_ref, "R5TemporalSpineProjection.cutoff_ref"))
        object.__setattr__(self, "event_refs", _freeze_str_tuple(
            self.event_refs, "R5TemporalSpineProjection.event_refs"))
        object.__setattr__(self, "pending_date_refs", _freeze_str_tuple(
            self.pending_date_refs,
            "R5TemporalSpineProjection.pending_date_refs"))
        object.__setattr__(self, "phase_band_refs", _freeze_str_tuple(
            self.phase_band_refs,
            "R5TemporalSpineProjection.phase_band_refs"))
        object.__setattr__(self, "visit_refs", _freeze_str_tuple(
            self.visit_refs, "R5TemporalSpineProjection.visit_refs"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5VisitNode:
    """One visit node on the temporal spine (deferred leaf)."""

    actual_date: Optional[date]
    date_state: str
    nominal_date: Optional[date]
    phase_ref: Optional[str]
    source_locator_refs: Tuple[str, ...]
    visit_kind: str
    visit_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "visit_ref", _check_str(
            self.visit_ref, "R5VisitNode.visit_ref"))
        object.__setattr__(self, "visit_kind", _check_closed(
            self.visit_kind, "R5VisitNode.visit_kind", VISIT_KINDS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5VisitNode.date_state", DATE_STATES))
        object.__setattr__(self, "actual_date", _check_optional_date(
            self.actual_date, "R5VisitNode.actual_date"))
        object.__setattr__(self, "nominal_date", _check_optional_date(
            self.nominal_date, "R5VisitNode.nominal_date"))
        object.__setattr__(self, "phase_ref", _check_optional_str(
            self.phase_ref, "R5VisitNode.phase_ref"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5VisitNode.source_locator_refs"))
        if self.date_state == "missing" and (
                self.actual_date is not None or self.nominal_date is not None):
            raise R5ContractError(
                "R5VisitNode date_state=missing must carry no fabricated "
                "main-axis date (date_geometry_consistency)")
        if self.date_state == "exact" and (
                self.actual_date is None and self.nominal_date is None):
            raise R5ContractError(
                "R5VisitNode date_state=exact requires a precise date "
                "(date_geometry_consistency)")


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


# ---------------------------------------------------------------------------
# Canonical field registration (static; verified against the JSON by tests)
# ---------------------------------------------------------------------------

register_object_fields(
    "SourceRevisionContentPair",
    hash_fields=("content_hash",))
register_object_fields(
    "R5AEMHMatchHistory",
    hash_fields=("history_content_hash",))
register_object_fields(
    "R5AudienceEncodingRegistry")
register_object_fields(
    "R5AudienceLexicon",
    hash_fields=("content_hash",))
register_object_fields(
    "R5AuthorityReceipt",
    hash_fields=(
        "public_projection_content_hash",
        "visibility_decision_hash",
        "evaluation_content_identities",
    ))
register_object_fields(
    "R5CenterMapCell")
register_object_fields(
    "R5CenterMapProjection",
    hash_fields=("content_hash",),
    ordered_fields=("stable_site_order",))
register_object_fields(
    "R5ChangeBand")
register_object_fields(
    "R5CurrentRiskSet")
register_object_fields(
    "R5DeepLinkState")
register_object_fields(
    "R5DomainEncodingItem")
register_object_fields(
    "R5FilterState")
register_object_fields(
    "R5JourneyEvent")
register_object_fields(
    "R5JourneyTrack",
    hash_fields=("content_hash",))
register_object_fields(
    "R5LegacyTreatmentMappingItem")
register_object_fields(
    "R5LexiconItem")
register_object_fields(
    "R5PageState")
register_object_fields(
    "R5PendingDateItem")
register_object_fields(
    "R5ProjectCockpitProjection",
    hash_fields=("content_hash",))
register_object_fields(
    "R5ProjectionInstance",
    hash_fields=("content_hash", "replay_content_identity"))
register_object_fields(
    "R5QuantitativeMeasure")
register_object_fields(
    "R5ReturnContext",
    hash_fields=("canonical_state_hash",))
register_object_fields(
    "R5RiskAnchor")
register_object_fields(
    "R5RiskInspectorProjection")
register_object_fields(
    "R5ScrollState")
register_object_fields(
    "R5SeverityLexiconItem")
register_object_fields(
    "R5SortState")
register_object_fields(
    "R5SubjectWorkspaceState",
    hash_fields=("content_hash",))
register_object_fields(
    "R5TemporalSpineProjection",
    hash_fields=("content_hash",))
register_object_fields(
    "R5VisitNode")

#: class name -> typed class (used by deferred_leaf_objects and validation).
_CLASS_BY_NAME: Dict[str, type] = {
    cls.__name__: cls for cls in (
        SourceRevisionContentPair,
        R5AEMHMatchHistory,
        R5AudienceEncodingRegistry,
        R5AudienceLexicon,
        R5AuthorityReceipt,
        R5CenterMapCell,
        R5CenterMapProjection,
        R5ChangeBand,
        R5CurrentRiskSet,
        R5DeepLinkState,
        R5DomainEncodingItem,
        R5FilterState,
        R5JourneyEvent,
        R5JourneyTrack,
        R5LegacyTreatmentMappingItem,
        R5LexiconItem,
        R5PageState,
        R5PendingDateItem,
        R5ProjectCockpitProjection,
        R5ProjectionInstance,
        R5QuantitativeMeasure,
        R5ReturnContext,
        R5RiskAnchor,
        R5RiskInspectorProjection,
        R5ScrollState,
        R5SeverityLexiconItem,
        R5SortState,
        R5SubjectWorkspaceState,
        R5TemporalSpineProjection,
        R5VisitNode,
    )
}


def known_object_names() -> Tuple[str, ...]:
    """Every R5 object class name declared by the typed surface."""
    return tuple(sorted(_CLASS_BY_NAME))


def is_r5_object(obj: Any) -> bool:
    return type(obj) in _CLASS_BY_NAME.values()


def validate_object(obj: Any) -> bool:
    """Fail-closed check that ``obj`` is a known R5 typed object whose
    canonical core is serializable (construction already enforced all
    invariants; this re-proves the canonical path for the W2 adapter)."""
    if not is_r5_object(obj):
        raise R5ContractError(
            f"not an R5 typed object: {type(obj).__name__}")
    canonical_object_hash(obj)  # raises R5CanonicalError on any defect
    return True


# ---------------------------------------------------------------------------
# Frozen contract constants (values NOT pinned by the S0 SHAs; see
# CONTRACT_CONSTANT_PIN_STATUS and the W1 report)
# ---------------------------------------------------------------------------

#: 8-domain audience encoding (stage contract v0.3 §8 table).  §8 lists
#: symptom_efficacy uses one event shape (circle); longitudinal change is
#: expressed only by the trend line style, so the registry has no second
#: shape convention.
DOMAIN_ENCODING_ITEMS: Tuple[R5DomainEncodingItem, ...] = (
    R5DomainEncodingItem(domain="ae", short_label_zh="AE",
                         event_shape="rounded_rect", line_style="solid"),
    R5DomainEncodingItem(domain="mh", short_label_zh="MH",
                         event_shape="bookmark", line_style="dot_dash"),
    R5DomainEncodingItem(domain="cm", short_label_zh="合并用药",
                         event_shape="capsule", line_style="solid"),
    R5DomainEncodingItem(domain="ip", short_label_zh="试验药",
                         event_shape="hexagon", line_style="step"),
    R5DomainEncodingItem(domain="lab_exam", short_label_zh="检验/检查",
                         event_shape="square", line_style="trend"),
    R5DomainEncodingItem(domain="hospital_procedure",
                         short_label_zh="住院/操作",
                         event_shape="doorframe", line_style="solid"),
    R5DomainEncodingItem(domain="symptom_efficacy",
                         short_label_zh="症状/疗效",
                         event_shape="circle", line_style="trend"),
    R5DomainEncodingItem(domain="protocol_compliance",
                         short_label_zh="方案符合",
                         event_shape="single_flag", line_style="bracket"),
)

#: 4 severity lexicon items.  Labels are pinned (§10 紧急/高/中/低 and the
#: severity_lexicon_bijection invariant); line weights 4/3/2/1 are an
#: unpinned choice (flagged in CONTRACT_CONSTANT_PIN_STATUS).
SEVERITY_LEXICON_ITEMS: Tuple[R5SeverityLexiconItem, ...] = (
    R5SeverityLexiconItem(severity="critical", label_zh="紧急", line_weight=4),
    R5SeverityLexiconItem(severity="high", label_zh="高", line_weight=3),
    R5SeverityLexiconItem(severity="medium", label_zh="中", line_weight=2),
    R5SeverityLexiconItem(severity="low", label_zh="低", line_weight=1),
)

#: Legacy treatment mapping: no frozen project mapping exists in the frozen
#: contract, so both legacy kinds stay unmapped_fail_closed (legacy_domain_
#: policy: frozen_mapping_or_fail_closed) and enter the domain-confirmation
#: surface.
LEGACY_TREATMENT_MAPPING_ITEMS: Tuple[R5LegacyTreatmentMappingItem, ...] = (
    R5LegacyTreatmentMappingItem(
        legacy_kind="background_treatment", mapping_state="unmapped_fail_closed",
        mapping_authority_ref=None, target_domain=None, target_subtype=None),
    R5LegacyTreatmentMappingItem(
        legacy_kind="non_drug_treatment", mapping_state="unmapped_fail_closed",
        mapping_authority_ref=None, target_domain=None, target_subtype=None),
)

#: Forbidden audience structure labels (stage contract v0.3 §8 / §14
#: elimination lists).  Exact token set is NOT closed by an S0 SHA (flagged).
FORBIDDEN_TERMS: Tuple[str, ...] = (
    "已记录事项", "正式事实", "候选信号", "通用风险点", "只读", "只读来源原文片段",
    "Checklist", "项目医学风险 Checklist", "待行动", "未读", "个例优先队列",
    "Safety/PV",
)

#: Audience lexicon items: 8 domain tokens + 4 severity tokens + PV-context
#: 信号 (allowed only for 药物警戒/安全性信号, §8) + the forbidden terms
#: (audience_allowed=False).  Exact token list is NOT closed by an S0 SHA.
LEXICON_ITEMS: Tuple[R5LexiconItem, ...] = (
    R5LexiconItem(token="ae", label_zh="AE", audience_allowed=True),
    R5LexiconItem(token="mh", label_zh="MH", audience_allowed=True),
    R5LexiconItem(token="cm", label_zh="合并用药", audience_allowed=True),
    R5LexiconItem(token="ip", label_zh="试验药", audience_allowed=True),
    R5LexiconItem(token="lab_exam", label_zh="检验/检查",
                  audience_allowed=True),
    R5LexiconItem(token="hospital_procedure", label_zh="住院/操作",
                  audience_allowed=True),
    R5LexiconItem(token="symptom_efficacy", label_zh="症状/疗效",
                  audience_allowed=True),
    R5LexiconItem(token="protocol_compliance", label_zh="方案符合",
                  audience_allowed=True),
    R5LexiconItem(token="critical", label_zh="紧急", audience_allowed=True),
    R5LexiconItem(token="high", label_zh="高", audience_allowed=True),
    R5LexiconItem(token="medium", label_zh="中", audience_allowed=True),
    R5LexiconItem(token="low", label_zh="低", audience_allowed=True),
    R5LexiconItem(token="signal", label_zh="信号", audience_allowed=True),
    *(
        R5LexiconItem(token=term, label_zh=term, audience_allowed=False)
        for term in FORBIDDEN_TERMS
    ),
)


def build_audience_encoding_registry() -> R5AudienceEncodingRegistry:
    """The frozen audience encoding registry (contract constants)."""
    return R5AudienceEncodingRegistry(
        domain_items=DOMAIN_ENCODING_ITEMS,
        legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
        risk_overlay_shape=RISK_OVERLAY_SHAPE,
        severity_items=SEVERITY_LEXICON_ITEMS,
        symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES,
    )


def build_audience_lexicon() -> R5AudienceLexicon:
    """The frozen audience lexicon (contract constants); ``content_hash``
    is the deterministic canonical hash of its non-hash fields."""
    return R5AudienceLexicon(
        content_hash="",
        forbidden_terms=FORBIDDEN_TERMS,
        items=LEXICON_ITEMS,
    )


#: Pin status of every contract-constant value group.  ``PINNED_*`` values
#: trace to a frozen SHA or exact_contract.json; ``PARTIAL`` values are
#: markdown-derived with at least one unpinned choice (see W1 report).
CONTRACT_CONSTANT_PIN_STATUS: Dict[str, Tuple[str, str]] = {
    "DOMAIN_ENCODING_ITEMS": (
        "PINNED_POLICY",
        "labels/shapes/line styles from stage contract v0.3 §8; "
        "domain_encoding_complete_unique freezes eight unique domains and "
        "symptom_efficacy circle + trend"),
    "SEVERITY_LEXICON_ITEMS": (
        "PARTIAL",
        "labels pinned (§10 + severity_lexicon_bijection invariant); "
        "line_weight 4/3/2/1 unpinned by any SHA"),
    "SYMPTOM_EFFICACY_SUBTYPES": (
        "PINNED_EXACT_CONTRACT",
        "exact_contract.json enums.symptom_efficacy_subtype"),
    "LEGACY_TREATMENT_MAPPING_ITEMS": (
        "PINNED_POLICY",
        "legacy_domain_policy frozen_mapping_or_fail_closed; no frozen "
        "project mapping exists -> unmapped_fail_closed"),
    "LEXICON_ITEMS": (
        "PARTIAL",
        "tokens/labels derived from §8/§10/§14; exact token list unpinned "
        "by any SHA"),
    "FORBIDDEN_TERMS": (
        "PARTIAL",
        "derived from §8/§14 forbidden lists; exact set unpinned by any SHA"),
    "RISK_OVERLAY_SHAPE": (
        "PINNED_EXACT_CONTRACT",
        "exact_contract.json risk_overlay_shape"),
    "DOMAIN_SUBTYPE_MATRIX": (
        "PARTIAL",
        "derived from journey_subtype enum + §7/§8; literal matrix unpinned"),
    "LEGACY_SEVERITY_MAPPING": (
        "PINNED_INVARIANT",
        "invariants.legacy_severity_mapping"),
}

__all__ = [
    "APPLICABILITY_STATES",
    "AXIS_MODES",
    "CHANGE_CAUSES",
    "CHANGE_KINDS",
    "CONTRACT_CONSTANT_PIN_STATUS",
    "COVERAGE_STATES",
    "DATE_STATES",
    "DEFERRED_CONTRACT_BY_ID",
    "DEFERRED_CONTRACT_SPECS",
    "DENOMINATOR_KINDS",
    "DENOMINATOR_STATES",
    "DOMAIN_ENCODING_ITEMS",
    "DOMAIN_SUBTYPE_MATRIX",
    "DOMAINS",
    "EVENT_FORBIDDEN_SHAPES",
    "EVENT_SHAPES",
    "FORBIDDEN_TERMS",
    "JOURNEY_SUBTYPES",
    "LEGACY_DOMAIN_POLICY",
    "LEGACY_MAPPING_STATES",
    "LEGACY_SEVERITY_MAPPING",
    "LEGACY_TREATMENT_KINDS",
    "LEGACY_TREATMENT_MAPPING_ITEMS",
    "LEXICON_ITEMS",
    "LINE_STYLES",
    "MATCH_STATES",
    "MEASURE_UNITS",
    "NUMERATOR_KINDS",
    "PENDING_ITEM_KINDS",
    "PROJECTION_KINDS",
    "R4_AUTHORITY_SEVERITY_VOCABULARY",
    "R5AEMHMatchHistory",
    "R5AudienceEncodingRegistry",
    "R5AudienceLexicon",
    "R5AuthorityReceipt",
    "R5CanonicalError",
    "R5CenterMapCell",
    "R5CenterMapProjection",
    "R5ChangeBand",
    "R5ContractError",
    "R5CurrentRiskSet",
    "R5DeepLinkState",
    "R5DeferredContract",
    "R5DomainEncodingItem",
    "R5FilterState",
    "R5HashMismatchError",
    "R5JourneyEvent",
    "R5JourneyTrack",
    "R5LegacyTreatmentMappingItem",
    "R5LexiconItem",
    "R5PageState",
    "R5PendingDateItem",
    "R5ProjectCockpitProjection",
    "R5ProjectionInstance",
    "R5QuantitativeMeasure",
    "R5ReturnContext",
    "R5RiskAnchor",
    "R5RiskInspectorProjection",
    "R5ScrollState",
    "R5SeverityLexiconItem",
    "R5SortState",
    "R5SubjectWorkspaceState",
    "R5TemporalSpineProjection",
    "R5VisitNode",
    "R5_CONTRACT_SHA256",
    "R5_CONTRACT_SCHEMA_ID",
    "R5_EXACT_CONTRACT_ARTIFACT_SHA256",
    "RATE_STATES",
    "RISK_OVERLAY_SHAPE",
    "SEVERITIES",
    "SEVERITY_LEXICON_ITEMS",
    "SEVERITY_TO_ZH",
    "SEVERITY_ZH",
    "SORT_DIRECTIONS",
    "SORT_KEYS",
    "SYMPTOM_EFFICACY_SUBTYPES",
    "UNKNOWN_DOMAIN_POLICY",
    "VISIBILITY_STATES",
    "VISIT_KINDS",
    "WORKSPACE_VIEWS",
    "ZH_TO_SEVERITY",
    "build_audience_encoding_registry",
    "build_audience_lexicon",
    "deferred_contract",
    "deferred_fields_for",
    "deferred_leaf_objects",
    "enum_values",
    "is_deferred_field",
    "is_r5_object",
    "known_object_names",
    "legacy_severity_to_r5",
    "severity_to_zh",
    "validate_object",
    "validate_severity_authority",
    "zh_to_severity",
]
