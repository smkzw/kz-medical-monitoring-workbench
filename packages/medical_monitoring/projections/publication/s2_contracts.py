"""R5 S2 authority-packet typed contracts, canonical identity and fail-closed
validator (``medical-monitoring-r5-s2-authority-packet-v0.1``).

Implements, as immutable frozen dataclasses with fail-closed validation, the
supplemental S2 authority packet declared by the frozen machine authority

* ``artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/
  authority_packet_schema.json``
  (artifact SHA-256 ``b44cb6c3c601dbb490557ab69c81d85060c1fe40bfc57c2ff5298cad8e0baa89``)
* ``.../exact_overlay.json`` (SHA-256
  ``6654dd89f0ca9efc088f1a58439cbaa8855f02e4f973c41325d6a923460d4a04``)
* human contract ``reviews/medical_monitoring_r5_s2_precondition_contract_v0_1_20260818.md``
  (SHA-256 ``1c91b27eadd778ebc0fdc5dd630d2342b22b02a8a4a212cbc621f6a62c8743b5``).

Scope
-----
* Typed packet objects only, exact keys/cardinality/nullability from the
  frozen schema.  Closed enums are exact tuples; every enum-typed field is
  validated fail-closed at construction.
* The packet embeds the frozen R4/R5 typed objects read-only (``Member``,
  ``EvidenceRef``, ``ModelEvidence``, ``D10DeepLinkTarget``,
  ``R5AuthorityReceipt``, ``AnalysisAttempt``, ``BaselineAssessment``,
  ``ReferenceBaselineItem``, ``ConflictVisibility``, ``EvidenceVerification``,
  ``AdjudicationBinding``, ``WorkerAnalysisOutput``): their exact key sets are
  re-verified against the frozen schema and any drift fails closed.
* Canonical identity is nonrecursive: ``packet_content_hash`` is the SHA-256
  of the canonical packet JSON excluding exactly ``packet_id`` and
  ``packet_content_hash``, and ``packet_id`` equals the literal
  ``r5-s2-auth:`` plus that hash (hash recipe
  ``utf8_nfc_sorted_keys_compact_json_newline``: NFC, sorted keys, compact
  separators, ``allow_nan=False``, trailing newline -- the same recipe the
  accepted S2 artifact family uses for ``manifest_content_sha256`` and the
  verifier's ``_packet_content_hash``).
* ``validate_s2_authority_packet`` is the fail-closed validator: it re-runs
  the 21 frozen cross-object invariants against the packet contents and
  returns ``{"valid": bool, "reasons": tuple of frozen error codes}`` without
  raising.  Construction itself is fail-closed too: every invariant runs at
  construction and a violation raises.
* Nothing here branches on project/case/fixture/test ids, filenames,
  synthetic sentinels, oracles, indexes, mutation classes or hash naming
  conventions (forbidden semantic branches of the frozen schema).  No ``assert``
  statement is used: every check raises or records explicitly.
* The packet never grants clinical truth, real-project, model, product,
  production or security eligibility; the only authority mode is the frozen
  literal ``synthetic_offline_test_only``.

S2 packet canonicalization is intentionally separate from :mod:`mm_r5.canonical`
(the R5 S0 objects' registered-object canonicalization): the packet recipe
excludes only the two root identity keys and serializes every nested object
with all of its fields, while the R5 object recipe excludes each object's own
hash fields.  Both conventions coexist; the S2 recipe is the one the frozen
``hash_recipes.packet_content_hash`` declares.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, fields as dataclass_fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Callable, Dict, Optional, Tuple

from ...risks.d10_contracts import EvidenceRef, Member, ModelEvidence
from ..d10 import D10DeepLinkTarget
from ...risks.ensemble import WorkerAnalysisOutput, worker_output_content_hash
from ...risks.ensemble_contracts import (
    AdjudicationBinding,
    AnalysisAttempt,
    BaselineAssessment,
    ConflictVisibility,
    EvidenceVerification,
    ReferenceBaselineItem,
)
from .contracts import R5AuthorityReceipt

# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

S2_PACKET_SCHEMA_ID = "medical-monitoring-r5-s2-authority-packet-v0.1"
S2_PACKET_SCHEMA_SHA256 = (
    "b44cb6c3c601dbb490557ab69c81d85060c1fe40bfc57c2ff5298cad8e0baa89")
S2_EXACT_OVERLAY_SHA256 = (
    "6654dd89f0ca9efc088f1a58439cbaa8855f02e4f973c41325d6a923460d4a04")
S2_MANIFEST_CONTENT_SHA256 = (
    "7901fa4084272314c08240284ce58ea540ddb7f74d2152e745850377720f46eb")
S2_HUMAN_CONTRACT_SHA256 = (
    "1c91b27eadd778ebc0fdc5dd630d2342b22b02a8a4a212cbc621f6a62c8743b5")

#: Planner-frozen authority mode (``authority_scope.mode``).
AUTHORITY_MODE_S2 = "synthetic_offline_test_only"
#: Frozen stage status of the accepted precondition artifacts.
STAGE_STATUS_S2 = "R5_S2_PRECONDITION_CONTRACT_READY"
#: Literal prefix of the nonrecursive packet identity.
PACKET_ID_PREFIX = "r5-s2-auth:"

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class S2ContractError(Exception):
    """Closed-enum, exact-key, cardinality, shape or invariant violation of an
    S2 authority-packet typed object."""


class S2HashMismatchError(S2ContractError):
    """A supplied content hash does not match the deterministic canonical hash
    of the object's non-hash fields (tamper rejection)."""


class S2CanonicalError(Exception):
    """A value cannot be canonicalized (unknown type, non-finite decimal) or
    is not a valid sha256 hex string."""


class S2InvariantError(S2ContractError):
    """One frozen cross-object invariant failed.  ``args[0]`` carries the
    invariant context; ``error_code`` is the frozen schema error code."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


# ---------------------------------------------------------------------------
# Closed enumerations (exact vocabulary from authority_packet_schema.json)
# ---------------------------------------------------------------------------

AUTHORITY_MODES: Tuple[str, ...] = (AUTHORITY_MODE_S2,)
S2_DATE_STATES: Tuple[str, ...] = ("exact",)
S2_DOMAINS: Tuple[str, ...] = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance")
FALLBACK_POLICIES: Tuple[str, ...] = ("none",)
S2_JOURNEY_SUBTYPES: Tuple[str, ...] = (
    "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
    "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
    "scale", "outcome", "trend", "protocol_deviation")
MODEL_EVIDENCE_VISIBILITIES: Tuple[str, ...] = ("packet_only",)
RESOLUTION_STATES: Tuple[str, ...] = ("locatable",)
#: S2 packet severity is high > medium > low; ``critical``/``unknown`` fail
#: closed (schema ``enums.severity`` -- narrower than the S0 R5 SEVERITIES).
S2_SEVERITIES: Tuple[str, ...] = ("high", "medium", "low")
S2_SOURCE_LOCATOR_KINDS: Tuple[str, ...] = (
    "listing_row", "listing_cell", "protocol_clause", "ib_clause",
    "synthetic_file")
S2_STAGE_STATUSES: Tuple[str, ...] = (STAGE_STATUS_S2,)
S2_VERIFICATION_DIMENSIONS: Tuple[str, ...] = (
    "identity", "version", "date", "unit", "source", "rule",
    "artifact_integrity")
S2_VISIT_KINDS: Tuple[str, ...] = ("actual", "unscheduled")

_SEVERITY_RANK: Dict[str, int] = {"high": 2, "medium": 1, "low": 0}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Validation helpers (fail closed, never ``assert``)
# ---------------------------------------------------------------------------


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise S2ContractError(f"{name} must be a non-empty str, got {value!r}")
    return unicodedata.normalize("NFC", value)


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_str(value, name)


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise S2ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise S2ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_date(value: Any, name: str) -> date:
    # Exact ``datetime.date`` only: ``datetime.datetime`` carries time/tz
    # semantics the packet does not define for a date field.
    if type(value) is not date:
        raise S2ContractError(
            f"{name} must be a datetime.date, got {type(value).__name__}: "
            f"{value!r}")
    return value


def _check_optional_date(value: Any, name: str) -> Optional[date]:
    if value is None:
        return None
    return _check_date(value, name)


def _check_hash(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise S2ContractError(
            f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_optional_hash(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_hash(value, name)


def _check_closed(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise S2ContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_optional_closed(
    value: Any, name: str, allowed: Tuple[str, ...],
) -> Optional[str]:
    if value is None:
        return None
    return _check_closed(value, name, allowed)


def _check_synthetic_relative_path(value: Any, name: str) -> str:
    """``synthetic_relative_path_only``: a non-empty relative path with no
    absolute root, drive, backslash or ``..`` climb (synthetic offline
    sources only)."""
    result = _check_str(value, name)
    if result.startswith("/") or result.startswith("\\"):
        raise S2ContractError(
            f"{name} must be a relative path, got {result!r}")
    if "\\" in result:
        raise S2ContractError(
            f"{name} must use forward slashes, got {result!r}")
    if re.match(r"^[A-Za-z]:", result):
        raise S2ContractError(
            f"{name} must not carry a drive prefix, got {result!r}")
    if any(part == ".." for part in result.split("/")):
        raise S2ContractError(
            f"{name} must not climb directories, got {result!r}")
    return result


def _freeze_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    """Normalize a many-str reference collection: list/tuple input, every
    member a non-empty NFC str, sorted (unordered set) and duplicate-free."""
    if not isinstance(value, (list, tuple)):
        raise S2ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_str(item, f"{name}[]") for item in value)
    if len(set(result)) != len(result):
        raise S2ContractError(
            f"{name} must be duplicate-free, got {sorted(result)!r}")
    return tuple(sorted(result))


def _freeze_hash_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise S2ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_hash(item, f"{name}[]") for item in value)
    if len(set(result)) != len(result):
        raise S2ContractError(
            f"{name} must be duplicate-free, got {sorted(result)!r}")
    return tuple(sorted(result))


def _freeze_sorted_objects(
    value: Any, name: str, cls: type, key_name: str,
) -> Tuple[Any, ...]:
    """Many-cardinality object collection: every item is a ``cls`` instance,
    sorted by the schema-declared ``sorted_unique_by`` key and
    duplicate-free."""
    if not isinstance(value, (list, tuple)):
        raise S2ContractError(f"{name} must be a list/tuple, got {value!r}")
    items = []
    for item in value:
        if not isinstance(item, cls):
            raise S2ContractError(
                f"{name}[] must be a {cls.__name__}, got "
                f"{type(item).__name__}")
        key = _check_str(getattr(item, key_name), f"{name}[].{key_name}")
        items.append((key, item))
    keys = [key for key, _ in items]
    if len(set(keys)) != len(keys):
        raise S2ContractError(
            f"{name} must be sorted-unique by {key_name}, got "
            f"{sorted(keys)!r}")
    return tuple(item for _, item in sorted(items, key=lambda pair: pair[0]))


def _require_exact_count(
    items: Tuple[Any, ...], expected: int, name: str,
) -> None:
    if len(items) != expected:
        raise S2ContractError(
            f"{name} must have exactly {expected} items, got {len(items)}")


def _require_min_count(items: Tuple[Any, ...], minimum: int, name: str) -> None:
    if len(items) < minimum:
        raise S2ContractError(
            f"{name} must have at least {minimum} items, got {len(items)}")


def _require_empty(items: Tuple[Any, ...], name: str) -> None:
    if items:
        raise S2ContractError(f"{name} must be exactly empty, got {items!r}")


def _require_nfc(value: str, name: str) -> None:
    if not unicodedata.is_normalized("NFC", value):
        raise S2ContractError(
            f"{name} must be Unicode NFC, got {value!r}")


def _check_obj_type(value: Any, cls: type, name: str) -> None:
    if not isinstance(value, cls):
        raise S2ContractError(
            f"{name} must be a {cls.__name__}, got {type(value).__name__}")


# ---------------------------------------------------------------------------
# Canonical serialization (frozen hash_recipes.packet_content_hash)
# ---------------------------------------------------------------------------


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise S2CanonicalError(
            f"non-finite decimal cannot be canonicalized: {value!r}")
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    return format(normalized, "f")


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _to_plain(value: Any) -> Any:
    """Recursively convert a packet value to a plain JSON-able structure.

    Strings are NFC-normalized, unordered collections are sorted by their own
    canonical JSON (so input ordering can never change a hash), and every
    dataclass is serialized with ALL of its fields (the packet recipe only
    excludes the two root identity keys, never nested hash fields)."""
    if value is None:
        return None
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return _canonical_decimal(value)
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        items = [_to_plain(item) for item in value]
        items.sort(key=_sort_key)
        return items
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): _to_plain(v)
                for key, v in value.items()}
    if _is_frozen_dataclass_instance(value):
        return {field.name: _to_plain(getattr(value, field.name))
                for field in dataclass_fields(value)}
    raise S2CanonicalError(
        f"unsupported packet leaf type {type(value).__name__}: {value!r}")


def _is_frozen_dataclass_instance(value: Any) -> bool:
    return is_dataclass(value) and not isinstance(value, type)


def s2_canonical_bytes(value: Any) -> bytes:
    """Deterministic canonical bytes of any packet value (NFC, sorted keys,
    compact separators, no NaN, trailing newline -- the frozen
    ``utf8_nfc_sorted_keys_compact_json_newline`` recipe)."""
    return (json.dumps(_to_plain(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n"
            ).encode("utf-8")


def s2_canonical_json(value: Any) -> str:
    """Deterministic canonical JSON text of any packet value (recipe above)."""
    return s2_canonical_bytes(value).decode("utf-8")


def s2_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def s2_object_content_hash(obj: Any) -> str:
    """Content address of one packet object over ALL of its fields (used for
    ``authority_receipt_ref`` and ``member_analysis_ref_set_hash``)."""
    return s2_sha256(s2_canonical_bytes(obj))


def s2_content_hash_excluding(obj: Any, excluded: Tuple[str, ...]) -> str:
    """Content address of one packet object excluding the named root fields
    (used for the five bindings' ``content_hash``:
    ``canonical_sha256_of_non_hash_fields``)."""
    if not _is_frozen_dataclass_instance(obj):
        raise S2CanonicalError(
            f"s2_content_hash_excluding expects a dataclass, got "
            f"{type(obj).__name__}")
    core = {field.name: getattr(obj, field.name)
            for field in dataclass_fields(obj)
            if field.name not in excluded}
    return s2_sha256(s2_canonical_bytes(core))


def binding_content_hash(binding: Any) -> str:
    """The canonical content hash of one S2 binding (non-hash fields; the
    binding's own ``content_hash`` field is excluded)."""
    return s2_content_hash_excluding(binding, ("content_hash",))


def packet_core_dict(packet: Any) -> Dict[str, Any]:
    """Plain-dict projection of the packet excluding exactly ``packet_id`` and
    ``packet_content_hash`` (the frozen identity-exclusion set)."""
    if not _is_frozen_dataclass_instance(packet):
        raise S2CanonicalError(
            f"packet_core_dict expects a dataclass, got "
            f"{type(packet).__name__}")
    return {field.name: getattr(packet, field.name)
            for field in dataclass_fields(packet)
            if field.name not in ("packet_id", "packet_content_hash")}


def compute_packet_content_hash(packet: Any) -> str:
    """Nonrecursive packet content hash: SHA-256 of the canonical packet JSON
    excluding exactly ``packet_id`` and ``packet_content_hash``."""
    return s2_sha256(s2_canonical_bytes(packet_core_dict(packet)))


def compute_packet_id(packet: Any) -> str:
    """Nonrecursive packet identity: literal prefix plus the content hash."""
    return PACKET_ID_PREFIX + compute_packet_content_hash(packet)


def _verify_content_hash(obj: Any, hash_field: str) -> None:
    """Canonical content-hash verification (tamper rejection): a supplied
    non-empty hash must equal the deterministic canonical hash of all
    non-hash fields (else S2HashMismatchError); an empty supplied hash is
    computed and stored."""
    expected = binding_content_hash(obj)
    supplied = getattr(obj, hash_field)
    if supplied and supplied != expected:
        raise S2HashMismatchError(
            f"{type(obj).__name__}.{hash_field} {supplied!r} does not match "
            f"the deterministic canonical hash {expected!r}")
    object.__setattr__(obj, hash_field, expected)


# ---------------------------------------------------------------------------
# Imported-object exact key sets (frozen schema ``imported_objects``)
# ---------------------------------------------------------------------------

IMPORTED_EXACT_KEYS: Dict[str, Tuple[str, ...]] = {
    "AdjudicationBinding": (
        "binding_id", "session_id", "model_id", "model_version", "outcome",
        "reviewed_artifact_refs"),
    "AnalysisAttempt": (
        "attempt_id", "ensemble_id", "binding_id", "session_id", "model_id",
        "model_version", "role", "independent_context_hash",
        "input_content_hash", "output_artifact_ref", "output_hash",
        "claimed_date_window", "claimed_unit_contract",
        "claimed_source_revision", "claimed_rule_id", "claimed_rule_version"),
    "BaselineAssessment": (
        "item_id", "state", "source_recheck_locator_ids", "evidence_hashes",
        "attempt_id", "reason_codes"),
    "ConflictVisibility": (
        "conflict_id", "member_attempt_ids", "monitoring_priority",
        "relation", "display_state", "hidden"),
    "D10DeepLinkTarget": (
        "link_id", "project_ref", "run_ref", "snapshot_ref",
        "signal_definition_ref", "evaluation_window_instance_ref",
        "target_kind", "site_ref", "subject_ref", "member_object_ref",
        "source_locator", "locator_resolution_state", "target_state",
        "unavailable_message", "visibility_decision_ref",
        "visibility_decision_hash", "return_state_key"),
    "EvidenceRef": (
        "locator_id", "locator_kind", "source_file", "row_or_cell_ref",
        "lineage_ref"),
    "EvidenceVerification": (
        "verification_id", "attempt_id", "checked_dimensions", "result",
        "failure_reason_codes"),
    "Member": (
        "member_ref", "member_kind", "aggregation_plane", "producer_domain",
        "member_scope_state", "site_stable_id", "subject_stable_id",
        "monitoring_priority", "accepted_current_state",
        "locator_resolution_state", "source_locator_refs",
        "descendant_member_refs", "descendant_set_hash",
        "treatment_role_ref"),
    "ModelEvidence": (
        "model_evidence_id", "role", "permitted_leaf", "model_id",
        "model_version", "evaluation_content_identity",
        "input_content_hash", "source_revision_content_pairs", "source_refs",
        "independent_context_hash", "ensemble_id", "ensemble_size",
        "member_analysis_refs", "member_analysis_ref_set_hash",
        "output_identity", "output_hash", "adjudication_state",
        "model_binding_hash"),
    "R5AuthorityReceipt": (
        "audience_contract_id", "cutoff_ref", "evaluation_content_identities",
        "project_ref", "public_projection_content_hash",
        "public_projection_id", "public_projection_kind", "run_ref",
        "snapshot_ref", "source_revision_content_pairs",
        "visibility_decision_hash", "visibility_decision_id"),
    "ReferenceBaselineItem": (
        "item_id", "source_kind", "source_locator_ids", "source_revision_id",
        "snapshot_id", "claimed_identity", "temporal_window",
        "claimed_content_hash", "origin_artifact_hash",
        "FORBIDDEN_AUTHORITY_FIELDS"),
    "WorkerAnalysisOutput": (
        "attempt_id", "assessments", "findings", "gap_candidates"),
}


def check_imported_object_exact_keys(obj: Any, object_name: str) -> None:
    """Exact-key gate for one imported object: the frozen schema declares the
    only permitted field set; ANY extra or missing key fails closed (guards
    against upstream R4/R5 source drift)."""
    spec = IMPORTED_EXACT_KEYS.get(object_name)
    if spec is None:
        raise S2ContractError(
            f"unknown imported object name {object_name!r}")
    actual = tuple(field.name for field in dataclass_fields(obj))
    if actual != spec:
        raise S2ContractError(
            f"{object_name} exact keys mismatch: expected {spec!r}, got "
            f"{actual!r} (extra/missing keys fail closed)")


# ---------------------------------------------------------------------------
# Typed binding objects (exact keys from authority_packet_schema.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S2CenterBinding:
    """Center-cell binding: pattern member relation, typed domain and the
    closed severity precedence over the actual pattern/individual members."""

    content_hash: str
    individual_risk_refs: Tuple[str, ...]
    measure_refs: Tuple[str, ...]
    member_priorities: Tuple[str, ...]
    member_producer_domains: Tuple[str, ...]
    pattern_descendant_member_refs: Tuple[str, ...]
    pattern_ref: str
    r4_risk_or_outcome_domain: str
    r5_domain: str
    r5_severity: str
    site_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_ref", _check_str(
            self.pattern_ref, "R5S2CenterBinding.pattern_ref"))
        object.__setattr__(self, "site_ref", _check_str(
            self.site_ref, "R5S2CenterBinding.site_ref"))
        object.__setattr__(self, "r4_risk_or_outcome_domain", _check_closed(
            self.r4_risk_or_outcome_domain,
            "R5S2CenterBinding.r4_risk_or_outcome_domain", S2_DOMAINS))
        object.__setattr__(self, "r5_domain", _check_closed(
            self.r5_domain, "R5S2CenterBinding.r5_domain", S2_DOMAINS))
        object.__setattr__(self, "r5_severity", _check_closed(
            self.r5_severity, "R5S2CenterBinding.r5_severity",
            S2_SEVERITIES))
        object.__setattr__(self, "individual_risk_refs", _freeze_str_tuple(
            self.individual_risk_refs,
            "R5S2CenterBinding.individual_risk_refs"))
        _require_min_count(self.individual_risk_refs, 2,
                           "R5S2CenterBinding.individual_risk_refs")
        object.__setattr__(self, "pattern_descendant_member_refs",
                           _freeze_str_tuple(
                               self.pattern_descendant_member_refs,
                               "R5S2CenterBinding."
                               "pattern_descendant_member_refs"))
        _require_min_count(self.pattern_descendant_member_refs, 2,
                           "R5S2CenterBinding.pattern_descendant_member_refs")
        object.__setattr__(self, "measure_refs", _freeze_str_tuple(
            self.measure_refs, "R5S2CenterBinding.measure_refs"))
        _require_empty(self.measure_refs,
                       "R5S2CenterBinding.measure_refs (deferred to S3)")
        object.__setattr__(self, "member_priorities",
                           _freeze_str_tuple(
                               self.member_priorities,
                               "R5S2CenterBinding.member_priorities"))
        _require_min_count(self.member_priorities, 1,
                           "R5S2CenterBinding.member_priorities")
        for priority in self.member_priorities:
            _check_closed(priority, "R5S2CenterBinding.member_priorities[]",
                          S2_SEVERITIES)
        object.__setattr__(self, "member_producer_domains",
                           _freeze_str_tuple(
                               self.member_producer_domains,
                               "R5S2CenterBinding.member_producer_domains"))
        _require_min_count(self.member_producer_domains, 1,
                           "R5S2CenterBinding.member_producer_domains")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S2ProjectRiskBinding:
    """Project-risk binding: the accepted D10 risk marker identity, its
    projection version and the S1 receipt projection identity."""

    authority_receipt_ref: str
    content_hash: str
    cutoff_ref: str
    member_refs: Tuple[str, ...]
    project_ref: str
    projection_version_ref: str
    public_projection_content_hash: str
    public_projection_id: str
    risk_marker_content_hash: str
    risk_ref: str
    run_ref: str
    snapshot_ref: str
    source_locator_refs: Tuple[str, ...]
    stable_core_ref: str

    def __post_init__(self) -> None:
        for name in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                     "projection_version_ref", "risk_ref", "stable_core_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S2ProjectRiskBinding.{name}"))
        for name in ("authority_receipt_ref", "risk_marker_content_hash",
                     "public_projection_id", "public_projection_content_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"R5S2ProjectRiskBinding.{name}"))
        object.__setattr__(self, "member_refs", _freeze_str_tuple(
            self.member_refs, "R5S2ProjectRiskBinding.member_refs"))
        _require_min_count(self.member_refs, 1,
                           "R5S2ProjectRiskBinding.member_refs")
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "R5S2ProjectRiskBinding.source_locator_refs"))
        _require_min_count(self.source_locator_refs, 1,
                           "R5S2ProjectRiskBinding.source_locator_refs")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S2SourceBinding:
    """One-hop source binding: a locatable synthetic deep-link locator with
    its exact revision-content pair and ``fallback_policy=none``."""

    content_hash: str
    fallback_policy: str
    lineage_ref: str
    locator_id: str
    locator_kind: str
    resolution_state: str
    revision_content_hash: str
    revision_id: str
    row_or_cell_ref: str
    source_file: str

    def __post_init__(self) -> None:
        for name in ("lineage_ref", "locator_id", "revision_id",
                     "row_or_cell_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S2SourceBinding.{name}"))
        object.__setattr__(self, "fallback_policy", _check_closed(
            self.fallback_policy, "R5S2SourceBinding.fallback_policy",
            FALLBACK_POLICIES))
        object.__setattr__(self, "locator_kind", _check_closed(
            self.locator_kind, "R5S2SourceBinding.locator_kind",
            S2_SOURCE_LOCATOR_KINDS))
        object.__setattr__(self, "resolution_state", _check_closed(
            self.resolution_state, "R5S2SourceBinding.resolution_state",
            RESOLUTION_STATES))
        object.__setattr__(self, "revision_content_hash", _check_hash(
            self.revision_content_hash,
            "R5S2SourceBinding.revision_content_hash"))
        object.__setattr__(self, "source_file",
                           _check_synthetic_relative_path(
                               self.source_file,
                               "R5S2SourceBinding.source_file"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S2TemporalBinding:
    """Single synthetic/offline temporal chain: one exact-date visit, one
    event and one risk anchor sharing subject/spine/domain/severity/source."""

    actual_date: date
    content_hash: str
    cutoff_ref: str
    date_state: str
    domain: str
    event_end: Optional[date]
    event_ref: str
    event_start: date
    event_subtype: str
    nominal_date: Optional[date]
    pending_date_refs: Tuple[str, ...]
    phase_band_refs: Tuple[str, ...]
    phase_ref: Optional[str]
    risk_anchor_ref: str
    risk_ref: str
    risk_type_zh: str
    severity: str
    source_locator_ref: str
    spine_ref: str
    subject_ref: str
    visit_kind: str
    visit_ref: str

    def __post_init__(self) -> None:
        for name in ("cutoff_ref", "event_ref", "risk_anchor_ref", "risk_ref",
                     "source_locator_ref", "spine_ref", "subject_ref",
                     "visit_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S2TemporalBinding.{name}"))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5S2TemporalBinding.date_state",
            S2_DATE_STATES))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5S2TemporalBinding.domain", S2_DOMAINS))
        object.__setattr__(self, "event_subtype", _check_closed(
            self.event_subtype, "R5S2TemporalBinding.event_subtype",
            S2_JOURNEY_SUBTYPES))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5S2TemporalBinding.severity", S2_SEVERITIES))
        object.__setattr__(self, "visit_kind", _check_closed(
            self.visit_kind, "R5S2TemporalBinding.visit_kind",
            S2_VISIT_KINDS))
        object.__setattr__(self, "risk_type_zh", _check_str(
            self.risk_type_zh, "R5S2TemporalBinding.risk_type_zh"))
        _require_nfc(self.risk_type_zh, "R5S2TemporalBinding.risk_type_zh")
        object.__setattr__(self, "actual_date", _check_date(
            self.actual_date, "R5S2TemporalBinding.actual_date"))
        object.__setattr__(self, "event_start", _check_date(
            self.event_start, "R5S2TemporalBinding.event_start"))
        object.__setattr__(self, "event_end", _check_optional_date(
            self.event_end, "R5S2TemporalBinding.event_end"))
        object.__setattr__(self, "nominal_date", _check_optional_date(
            self.nominal_date, "R5S2TemporalBinding.nominal_date"))
        object.__setattr__(self, "phase_ref", _check_optional_str(
            self.phase_ref, "R5S2TemporalBinding.phase_ref"))
        object.__setattr__(self, "pending_date_refs", _freeze_str_tuple(
            self.pending_date_refs, "R5S2TemporalBinding.pending_date_refs"))
        _require_empty(self.pending_date_refs,
                       "R5S2TemporalBinding.pending_date_refs "
                       "(deferred to S5)")
        object.__setattr__(self, "phase_band_refs", _freeze_str_tuple(
            self.phase_band_refs, "R5S2TemporalBinding.phase_band_refs"))
        _require_empty(self.phase_band_refs,
                       "R5S2TemporalBinding.phase_band_refs "
                       "(deferred to S5)")
        if self.event_end is not None and self.event_end < self.event_start:
            raise S2ContractError(
                "R5S2TemporalBinding.event_end must not precede event_start "
                f"({self.event_end.isoformat()} < "
                f"{self.event_start.isoformat()})")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S2InspectorBinding:
    """Risk Inspector binding: every public ref mechanically derived from the
    actual packet objects; S4-deferred leaves stay exactly empty/null."""

    adjudication_ref: str
    analysis_attempt_refs: Tuple[str, ...]
    authority_receipt_ref: str
    baseline_assessment_refs: Tuple[str, ...]
    baseline_item_refs: Tuple[str, ...]
    conflict_refs: Tuple[str, ...]
    content_hash: str
    counterevidence_refs: Tuple[str, ...]
    domain: str
    model_evidence_visibility: str
    query_draft_ref: Optional[str]
    risk_ref: str
    severity: str
    source_locator_refs: Tuple[str, ...]
    support_evidence_refs: Tuple[str, ...]
    verification_refs: Tuple[str, ...]
    worker_output_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("adjudication_ref", "risk_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S2InspectorBinding.{name}"))
        object.__setattr__(self, "authority_receipt_ref", _check_hash(
            self.authority_receipt_ref,
            "R5S2InspectorBinding.authority_receipt_ref"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5S2InspectorBinding.domain", S2_DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5S2InspectorBinding.severity", S2_SEVERITIES))
        object.__setattr__(self, "model_evidence_visibility", _check_closed(
            self.model_evidence_visibility,
            "R5S2InspectorBinding.model_evidence_visibility",
            MODEL_EVIDENCE_VISIBILITIES))
        object.__setattr__(self, "query_draft_ref", _check_optional_str(
            self.query_draft_ref, "R5S2InspectorBinding.query_draft_ref"))
        if self.query_draft_ref is not None:
            raise S2ContractError(
                "R5S2InspectorBinding.query_draft_ref must be exactly null "
                "(deferred to S4)")
        for name in ("analysis_attempt_refs", "baseline_assessment_refs",
                     "baseline_item_refs", "conflict_refs",
                     "counterevidence_refs", "source_locator_refs",
                     "support_evidence_refs", "verification_refs",
                     "worker_output_refs"):
            object.__setattr__(self, name, _freeze_str_tuple(
                getattr(self, name), f"R5S2InspectorBinding.{name}"))
        _require_exact_count(self.analysis_attempt_refs, 2,
                             "R5S2InspectorBinding.analysis_attempt_refs")
        _require_exact_count(self.baseline_assessment_refs, 1,
                             "R5S2InspectorBinding.baseline_assessment_refs")
        _require_exact_count(self.baseline_item_refs, 1,
                             "R5S2InspectorBinding.baseline_item_refs")
        _require_exact_count(self.conflict_refs, 1,
                             "R5S2InspectorBinding.conflict_refs")
        _require_exact_count(self.source_locator_refs, 1,
                             "R5S2InspectorBinding.source_locator_refs")
        _require_exact_count(self.verification_refs, 2,
                             "R5S2InspectorBinding.verification_refs")
        _require_empty(self.counterevidence_refs,
                       "R5S2InspectorBinding.counterevidence_refs "
                       "(deferred to S4)")
        _require_empty(self.support_evidence_refs,
                       "R5S2InspectorBinding.support_evidence_refs "
                       "(deferred to S4)")
        _require_empty(self.worker_output_refs,
                       "R5S2InspectorBinding.worker_output_refs "
                       "(deferred to S4)")
        _verify_content_hash(self, "content_hash")


# ---------------------------------------------------------------------------
# The root authority packet (exact keys from authority_packet_schema.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S2AuthorityPacket:
    """The frozen S2 authority packet: one receipt, one project-risk binding,
    one center binding, one temporal binding, one source binding, one
    reference-baseline item, exactly two assessments, two isolated worker
    attempts/outputs, two passed verifications, one visible conflict, one
    independent adjudicator and one packet-only D10 ModelEvidence."""

    adjudication: AdjudicationBinding
    analysis_attempts: Tuple[AnalysisAttempt, ...]
    authority_mode: str
    authority_receipt: R5AuthorityReceipt
    baseline_assessments: Tuple[BaselineAssessment, ...]
    center_binding: R5S2CenterBinding
    center_pattern_member: Member
    conflict: ConflictVisibility
    deep_link_target: D10DeepLinkTarget
    individual_members: Tuple[Member, ...]
    inspector_binding: R5S2InspectorBinding
    model_evidence: ModelEvidence
    packet_content_hash: str
    packet_id: str
    project_risk_binding: R5S2ProjectRiskBinding
    reference_baseline_items: Tuple[ReferenceBaselineItem, ...]
    source_binding: R5S2SourceBinding
    source_evidence: EvidenceRef
    stage_status: str
    temporal_binding: R5S2TemporalBinding
    verifications: Tuple[EvidenceVerification, ...]
    worker_outputs: Tuple[WorkerAnalysisOutput, ...]

    def __post_init__(self) -> None:
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "packet.authority_receipt")
        _check_obj_type(self.project_risk_binding, R5S2ProjectRiskBinding,
                        "packet.project_risk_binding")
        _check_obj_type(self.center_binding, R5S2CenterBinding,
                        "packet.center_binding")
        _check_obj_type(self.center_pattern_member, Member,
                        "packet.center_pattern_member")
        _check_obj_type(self.temporal_binding, R5S2TemporalBinding,
                        "packet.temporal_binding")
        _check_obj_type(self.deep_link_target, D10DeepLinkTarget,
                        "packet.deep_link_target")
        _check_obj_type(self.source_binding, R5S2SourceBinding,
                        "packet.source_binding")
        _check_obj_type(self.source_evidence, EvidenceRef,
                        "packet.source_evidence")
        _check_obj_type(self.inspector_binding, R5S2InspectorBinding,
                        "packet.inspector_binding")
        _check_obj_type(self.conflict, ConflictVisibility,
                        "packet.conflict")
        _check_obj_type(self.adjudication, AdjudicationBinding,
                        "packet.adjudication")
        _check_obj_type(self.model_evidence, ModelEvidence,
                        "packet.model_evidence")

        object.__setattr__(self, "authority_mode", _check_closed(
            self.authority_mode, "packet.authority_mode", AUTHORITY_MODES))
        object.__setattr__(self, "stage_status", _check_closed(
            self.stage_status, "packet.stage_status", S2_STAGE_STATUSES))
        # packet_content_hash / packet_id are nonrecursive identities: an
        # empty placeholder is recomputed; a supplied value is verified.
        if self.packet_content_hash:
            object.__setattr__(self, "packet_content_hash", _check_hash(
                self.packet_content_hash, "packet.packet_content_hash"))
        else:
            object.__setattr__(self, "packet_content_hash", "")
        if self.packet_id:
            object.__setattr__(self, "packet_id", _check_str(
                self.packet_id, "packet.packet_id"))
        else:
            object.__setattr__(self, "packet_id", "")

        object.__setattr__(self, "individual_members", _freeze_sorted_objects(
            self.individual_members, "packet.individual_members", Member,
            "member_ref"))
        _require_min_count(self.individual_members, 2,
                           "packet.individual_members")
        object.__setattr__(self, "reference_baseline_items",
                           _freeze_sorted_objects(
                               self.reference_baseline_items,
                               "packet.reference_baseline_items",
                               ReferenceBaselineItem, "item_id"))
        _require_exact_count(self.reference_baseline_items, 1,
                             "packet.reference_baseline_items")
        object.__setattr__(self, "analysis_attempts", _freeze_sorted_objects(
            self.analysis_attempts, "packet.analysis_attempts",
            AnalysisAttempt, "attempt_id"))
        _require_exact_count(self.analysis_attempts, 2,
                             "packet.analysis_attempts")
        object.__setattr__(self, "baseline_assessments",
                           _freeze_sorted_objects(
                               self.baseline_assessments,
                               "packet.baseline_assessments",
                               BaselineAssessment, "attempt_id"))
        _require_exact_count(self.baseline_assessments, 2,
                             "packet.baseline_assessments")
        object.__setattr__(self, "verifications", _freeze_sorted_objects(
            self.verifications, "packet.verifications",
            EvidenceVerification, "verification_id"))
        _require_exact_count(self.verifications, 2, "packet.verifications")
        object.__setattr__(self, "worker_outputs", _freeze_sorted_objects(
            self.worker_outputs, "packet.worker_outputs",
            WorkerAnalysisOutput, "attempt_id"))
        _require_exact_count(self.worker_outputs, 2, "packet.worker_outputs")

        # Nonrecursive identity: exclude exactly the two root identity keys.
        expected_hash = compute_packet_content_hash(self)
        if self.packet_content_hash and \
                self.packet_content_hash != expected_hash:
            raise S2HashMismatchError(
                "packet.packet_content_hash "
                f"{self.packet_content_hash!r} does not match the canonical "
                f"packet hash {expected_hash!r}")
        object.__setattr__(self, "packet_content_hash", expected_hash)
        expected_id = PACKET_ID_PREFIX + expected_hash
        if self.packet_id and self.packet_id != expected_id:
            raise S2HashMismatchError(
                "packet.packet_id must equal the literal prefix plus the "
                f"content hash, got {self.packet_id!r}, expected "
                f"{expected_id!r}")
        object.__setattr__(self, "packet_id", expected_id)

        # Fail-closed construction: every frozen invariant runs here.
        _validate_packet_invariants(self)


# Cross-object invariants load after the packet type is defined.
from . import s2_invariants as _invariants

_validate_packet_invariants = _invariants._validate_packet_invariants

from .s2_invariants import *  # noqa: F401,F403,E402

__all__ = _invariants.__all__
