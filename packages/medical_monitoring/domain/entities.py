"""Framework-neutral R2 domain kernel: immutable source/snapshot/knowledge/
rule/mapping/fact entities with schema+version provenance (Design v1.1
sections 5-7; implementation plan R2 steps 1-2).

Conventions
-----------

* Every entity is a frozen dataclass with an explicit
  ``(schema_name, schema_version)`` pair validated against the
  :mod:`schema_registry` at construction time.
* Content-addressed hashes are SHA-256 over canonical JSON
  (:func:`canonical_json`).  ``content_hash`` is recomputed from the
  declared canonical fields (never from a caller-supplied field), so a
  hash/identity mismatch is a hard error.
* Provenance (``project_id`` / ``source_revision_id`` / ``schema_*``) is
  mandatory wherever the design binds it; ``IdentityAlgorithm`` records are
  bound to entities that need record-identity reproducibility.
* The codec (:func:`to_dictable` / :func:`from_dictable`) is deterministic
  so that hashes survive a serialize/deserialize round trip.

This module declares **no** mutable state machine: the snapshot acceptance
chain lives in :mod:`acceptance`.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import re as _re
import uuid
from collections.abc import Mapping
from dataclasses import InitVar, dataclass, field, fields
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from .schema_registry import default_registry

__all__ = [
    "MmR2Error",
    "DomainValidationError",
    "ProvenanceError",
    "HashMismatchError",
    "now_iso",
    "new_id",
    "canonical_json",
    "sha256_hex",
    "content_hash",
    "validate_sha256_hex",
    "deep_freeze_json",
    "to_dictable",
    "from_dictable",
    "StudyProject",
    "SourceRevision",
    "ListingSnapshot",
    "StudyKnowledgePack",
    "RuleActivation",
    "MappingDefinition",
    "MappingResult",
    "CanonicalFact",
    "IdentityAlgorithm",
    "Provenance",
]


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """UTC ISO-8601 timestamp, lexicographically sortable, microsecond precision."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def new_id(prefix: str = "") -> str:
    """Short random identifier; optional prefix for debuggability (<=64 chars)."""
    return (prefix + uuid.uuid4().hex)[:64]


class ImmutableDict(Mapping):
    """A genuinely immutable mapping with no reachable mutable backing.

    It is backed by :class:`types.MappingProxyType` (a read-only view of a
    dict).  Because the only stored attribute ``_m`` is itself a `mappingproxy`
    (which has no item-assignment and exposes no writable backing), there is
    no ``dict.__setitem__`` base-class backdoor and **no mutable backing
    object reachable through ordinary attribute access** -- ``frozen._m["x"]=2``
    raises :class:`TypeError`.  Item assignment and deletion raise
    :class:`TypeError`.

    It is used as the leaf container for deeply-frozen object graphs so that
    a caller cannot mutate a nested mapping reachable from a frozen dataclass
    and thereby change the recomputed identity/hash.  The backing dict is
    built once from the fully materialized source data and never exposed.
    """

    __slots__ = ("_m",)

    def __init__(self, *args, **kwargs) -> None:
        object.__setattr__(self, "_m", MappingProxyType(dict(*args, **kwargs)))

    def __setattr__(self, name, value) -> None:
        raise TypeError("ImmutableDict attributes cannot be reassigned")

    def __delattr__(self, name) -> None:
        raise TypeError("ImmutableDict attributes cannot be deleted")

    def __getitem__(self, key):
        return self._m[key]

    def __iter__(self):
        return iter(self._m)

    def __len__(self):
        return len(self._m)

    def __contains__(self, key):
        return key in self._m

    def get(self, key, default=None):
        return self._m.get(key, default)

    def keys(self):
        return self._m.keys()

    def items(self):
        return self._m.items()

    def values(self):
        return self._m.values()

    def __eq__(self, other):
        if isinstance(other, Mapping):
            return dict(self._m) == dict(other)
        return NotImplemented

    def __hash__(self):
        return hash(frozenset(self._m.items()))

    def __repr__(self):
        return f"ImmutableDict({dict(self._m)!r})"

    # -- mutation interfaces all raise ------------------------------------

    def _immutable(self, *args, **kwargs):
        raise TypeError("ImmutableDict is immutable after construction")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable


def _freeze_scalar(value: Any) -> Any:
    """Freeze one JSON scalar; reject non-finite numbers and non-JSON types.

    Returns the value unchanged (str/int/bool/None) or raises
    :class:`DomainValidationError` for values that cannot be part of a
    canonical JSON content address.
    """
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DomainValidationError(
                f"non-finite number {value!r} cannot be part of a canonical "
                f"JSON content address"
            )
        return value
    raise DomainValidationError(
        f"unsupported JSON leaf type {type(value).__name__} ({value!r}) in "
        f"canonical content; only str/int/float/bool/None/list/dict allowed"
    )


def deep_freeze_json(value: Any) -> Any:
    """Deep-copy and freeze an arbitrary JSON-like structure.

    * mappings become :class:`ImmutableDict` (sorted for determinism);
    * sequences become tuples;
    * scalars are validated (:func:`_freeze_scalar`) and non-finite numbers /
      unsupported leaf types are rejected.

    The returned structure is a private copy: mutating the caller's original
    input can never change it, and mutating any value reachable inside the
    frozen object raises :class:`TypeError`.  This is the single primitive
    used to freeze every JSON-like field of Batch A entities.
    """
    if isinstance(value, Mapping):
        return ImmutableDict(
            (str(k), deep_freeze_json(v)) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))
        )
    if isinstance(value, (tuple, list)):
        return tuple(deep_freeze_json(v) for v in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _freeze_scalar(value)
    # dataclasses/enums are not raw JSON; reject rather than silently coerce.
    raise DomainValidationError(
        f"unsupported JSON container type {type(value).__name__} in canonical "
        f"content; only dict/list/tuple/scalars allowed"
    )


def _json_plain(obj: Any) -> Any:
    """Recursively convert Mapping/tuple/list to plain JSON-able structures.

    ``ImmutableDict`` (a Mapping) is normalized to a plain dict so that
    :func:`json.dumps` can serialize it deterministically.  Any other
    non-JSON leaf type is surfaced (so non-finite numbers and unsupported
    values still fail closed via ``allow_nan=False``).
    """
    if isinstance(obj, Mapping):
        return {str(k): _json_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_plain(v) for v in obj]
    return obj


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8, no NaN.

    This is the single canonicalization primitive used for every content
    hash in R2.  Changing it invalidates every stored hash.

    Non-finite numbers (NaN/Infinity/-Infinity) and unsupported leaf types
    are rejected explicitly rather than being silently coerced, so no two
    distinct values can ever produce the same content address.
    """
    return json.dumps(_json_plain(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(obj: Any) -> str:
    """Content address of any JSON-able object (sha256 of canonical JSON).

    Non-finite numbers and unsupported leaf types fail closed via
    :func:`canonical_json` (``allow_nan=False``).
    """
    return sha256_hex(canonical_json(obj).encode("utf-8"))

_SHA256_RE = _re.compile(r"^[0-9a-f]{64}$")


def validate_sha256_hex(value: str, field_name: str = "content_digest") -> str:
    """Validate that *value* is a canonical 64-char lowercase hex SHA-256 digest.

    Returns the value if valid; raises :class:`DomainValidationError` otherwise.
    """
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise DomainValidationError(
            f"{field_name} must be a 64-character lowercase hex SHA-256 "
            f"digest; got {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class MmR2Error(Exception):
    """Base class for all R2 POC errors."""


class DomainValidationError(MmR2Error):
    """An entity failed invariant validation."""


class ProvenanceError(MmR2Error):
    """Missing or inconsistent provenance binding."""


class HashMismatchError(MmR2Error):
    """A content hash did not match the recomputed canonical hash."""


# ---------------------------------------------------------------------------
# Authority capability (private, never exported)
# ---------------------------------------------------------------------------

# A construction token captured into the authoritative validators/factories
# below and deleted from the module namespace after class creation.  It is
# therefore not an addressable module attribute that a caller can pass to a
# direct dataclass constructor.  There is deliberately **no** digest-only
# rehydration path in Batch A: Batch C must verify stored bytes before it may
# recreate an authoritative object.
_VERIFIED = object()


# ---------------------------------------------------------------------------
# Schema validation helper (shared by every entity)
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    """Validate the entity's (schema_name, schema_version) against the registry.

    New objects must be written at the current (non-deprecated) version.
    """
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Codec
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, type] = {}


def _register_dataclass(cls: type) -> type:
    _REGISTRY[cls.__name__] = cls
    return cls


def to_dictable(obj: Any) -> Any:
    """Convert dataclasses/enums/primitives to plain JSON-able structures."""
    import dataclasses as _dc
    import enum as _enum
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        d: Dict[str, Any] = {}
        for f in fields(obj):
            d[f.name] = to_dictable(getattr(obj, f.name))
        return {"__r2_dataclass__": obj.__class__.__name__, "fields": d}
    if isinstance(obj, _enum.Enum):
        return {"__r2_enum__": type(obj).__name__, "value": obj.value}
    if isinstance(obj, (list, tuple)):
        return [to_dictable(x) for x in obj]
    if isinstance(obj, dict) or isinstance(obj, Mapping):
        return {str(k): to_dictable(v) for k, v in obj.items()}
    return obj


def from_dictable(data: Any, _context: Optional[Dict[str, Any]] = None) -> Any:
    """Inverse of :func:`to_dictable` for **non-authoritative** entities only.

    Generic deserialization **fails closed** for content-addressed /
    authoritative entities (those declared with a ``_verified`` InitVar):
    reconstructing one from arbitrary serialized bytes would trust a
    caller-chosen digest or reference, which is a public trust-escalation
    hole.  There is deliberately **no** digest-only rehydration path in Batch
    A.  Batch C must add a verified rehydration adapter that verifies the
    actual stored bytes/hash (against the artifact store) before recreating
    an authoritative object from untrusted/migrated data.

    Non-authoritative entities (plain dataclasses without a ``_verified``
    InitVar) round-trip normally.
    """
    if isinstance(data, dict):
        if "__r2_enum__" in data:
            raise MmR2Error(
                f"enum reconstruction for {data['__r2_enum__']!r} is not "
                f"supported via the generic codec; use the owning module"
            )
        if "__r2_dataclass__" in data:
            cls_name = data["__r2_dataclass__"]
            cls = _REGISTRY.get(cls_name)
            if cls is None:
                raise MmR2Error(f"unknown dataclass in payload: {cls_name!r}")
            if "_verified" in getattr(cls, "__dataclass_fields__", {}):
                raise MmR2Error(
                    f"generic rehydration of authoritative entity "
                    f"{cls_name!r} is not permitted; there is no digest-only "
                    f"rehydration in Batch A (Batch C must add a verified "
                    f"adapter after artifact byte/hash verification)"
                )
            kwargs = {k: from_dictable(v) for k, v in data["fields"].items()}
            return cls(**kwargs)
        return {k: from_dictable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [from_dictable(x) for x in data]
    return data


# ---------------------------------------------------------------------------
# Source / project / snapshot entities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
@_register_dataclass
class StudyProject:
    """Research project identity and isolation boundary (Design 5).

    Different studies must never reuse business primary keys or silently
    cross-talk. ``is_synthetic`` records source provenance; both real projects
    and explicit test fixtures use the same identity contract.
    """

    schema_name: str = "study_project"
    schema_version: str = "1"
    project_id: str = ""
    name: str = ""
    is_synthetic: bool = True
    created_at: str = ""
    config: Tuple[Tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.project_id:
            raise DomainValidationError("StudyProject.project_id is required")
        if not self.name:
            raise DomainValidationError("StudyProject.name is required")
        if not isinstance(self.is_synthetic, bool):
            raise DomainValidationError("StudyProject.is_synthetic must be bool")
        # VETO2: deep-freeze the JSON-like config so a nested value reachable
        # from the frozen project cannot be mutated after construction and
        # change serialized/hash-relevant state.
        object.__setattr__(self, "config", deep_freeze_json(self.config))


@dataclass(frozen=True)
@_register_dataclass
class SourceRevision:
    """Immutable source revision: protocol/IB/listing/report/other (Design 5).

    ``content_digest`` is a real SHA-256 over the actual immutable source
    bytes (produced by the caller from synthetic content).  ``content_hash``
    is the full identity binding (metadata fingerprint + content_digest);
    a different file with the same IDs/version/scope but different bytes
    produces a different ``content_hash``.
    """

    schema_name: str = "source_revision"
    schema_version: str = "1"
    revision_id: str = ""
    project_id: str = ""
    source_type: str = ""           # protocol | ib | listing | report | other
    version: str = ""
    content_digest: str = ""        # SHA-256 of actual source bytes (required)
    content_hash: str = ""          # full identity binding (auto-computed)
    valid_from: Optional[str] = None
    scope: Tuple[Tuple[str, Any], ...] = ()
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _VERIFIED,
    ) -> None:
        _validate_schema(self)
        if not self.revision_id:
            raise DomainValidationError("SourceRevision.revision_id is required")
        if not self.project_id:
            raise DomainValidationError("SourceRevision.project_id is required")
        if self.source_type not in ("protocol", "ib", "listing", "report", "other"):
            raise DomainValidationError(
                f"unknown source_type {self.source_type!r}"
            )
        if not self.version:
            raise DomainValidationError("SourceRevision.version is required")
        validate_sha256_hex(self.content_digest, "SourceRevision.content_digest")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "SourceRevision requires verified source bytes; use "
                "SourceRevision.from_bytes(...) to construct an authoritative "
                "revision (digest-only construction is unavailable to public "
                "callers)"
            )
        object.__setattr__(self, "scope", deep_freeze_json(self.scope))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"SourceRevision.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    @classmethod
    def from_bytes(
        cls,
        revision_id: str,
        project_id: str,
        source_type: str,
        version: str,
        source_bytes: bytes,
        *,
        scope: Tuple[Tuple[str, Any], ...] = (),
        valid_from: Optional[str] = None,
        created_at: str = "",
        _authority_token: Any = _VERIFIED,
    ) -> "SourceRevision":
        """Authoritative constructor that receives the actual immutable source
        bytes, computes ``content_digest`` internally and verifies the full
        identity binding.  Digest-only construction is unavailable to public
        callers.
        """
        if not isinstance(source_bytes, bytes) or len(source_bytes) == 0:
            raise DomainValidationError(
                "SourceRevision.from_bytes requires non-empty source bytes"
            )
        return cls(
            revision_id=revision_id,
            project_id=project_id,
            source_type=source_type,
            version=version,
            content_digest=sha256_hex(source_bytes),
            scope=deep_freeze_json(scope),
            valid_from=valid_from,
            created_at=created_at,
            _verified=_authority_token,
        )

    def metadata_payload(self) -> Dict[str, Any]:
        """Metadata-only fingerprint (excludes the content bytes/digest)."""
        return {
            "revision_id": self.revision_id,
            "project_id": self.project_id,
            "source_type": self.source_type,
            "version": self.version,
            "valid_from": self.valid_from,
            "scope": dict(self.scope),
        }

    @property
    def metadata_fingerprint(self) -> str:
        return content_hash(self.metadata_payload())

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "metadata_fingerprint": self.metadata_fingerprint,
            "content_digest": self.content_digest,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())

@dataclass(frozen=True)
@_register_dataclass
class ListingSnapshot:
    """Full data listing for one cutoff; immutable; records structure (Design 5).

    Every input is a full snapshot (Design 6.2): R2 never accepts a "diff
    file" as a fact substitute.  ``content_digest`` is a real SHA-256 over
    the canonical full-listing content (produced by the caller from synthetic
    rows).  ``content_hash`` is the full identity binding (metadata
    fingerprint + content_digest); two listings with the same IDs/version/
    shape/row_count but different row content produce different hashes.
    """

    schema_name: str = "listing_snapshot"
    schema_version: str = "1"
    snapshot_id: str = ""
    project_id: str = ""
    revision_id: str = ""
    snapshot_version: str = ""
    content_digest: str = ""        # SHA-256 of canonical full-listing content (required)
    content_hash: str = ""          # full identity binding (auto-computed)
    row_count: int = 0
    structure: Tuple[Tuple[str, Any], ...] = ()
    is_synthetic: bool = True
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _VERIFIED,
    ) -> None:
        _validate_schema(self)
        if not self.snapshot_id:
            raise DomainValidationError("ListingSnapshot.snapshot_id is required")
        if not self.project_id:
            raise DomainValidationError("ListingSnapshot.project_id is required")
        if not self.revision_id:
            raise DomainValidationError("ListingSnapshot.revision_id is required")
        if not self.snapshot_version:
            raise DomainValidationError("ListingSnapshot.snapshot_version is required")
        if not isinstance(self.is_synthetic, bool):
            raise DomainValidationError("ListingSnapshot.is_synthetic must be bool")
        if self.row_count < 0:
            raise DomainValidationError("ListingSnapshot.row_count must be >= 0")
        validate_sha256_hex(self.content_digest, "ListingSnapshot.content_digest")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "ListingSnapshot requires verified canonical full-listing "
                "content; use ListingSnapshot.from_content(...) to construct "
                "an authoritative snapshot (digest-only construction is "
                "unavailable to public callers)"
            )
        object.__setattr__(self, "structure", deep_freeze_json(self.structure))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"ListingSnapshot.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    @classmethod
    def from_content(
        cls,
        snapshot_id: str,
        project_id: str,
        revision_id: str,
        snapshot_version: str,
        rows: Any,
        *,
        structure: Tuple[Tuple[str, Any], ...] = (),
        is_synthetic: bool = True,
        created_at: str = "",
        _authority_token: Any = _VERIFIED,
    ) -> "ListingSnapshot":
        """Authoritative constructor that receives the actual canonical
        full-listing content (``rows``), computes ``content_digest`` from it
        internally and verifies row/shape metadata where feasible.
        Digest-only construction is unavailable to public callers.
        """
        if not isinstance(is_synthetic, bool):
            raise DomainValidationError("ListingSnapshot.is_synthetic must be bool")
        # Canonicalize + validate the full content up front (rejects
        # non-finite numbers and unsupported leaf types).
        frozen_rows = deep_freeze_json(rows)
        if isinstance(frozen_rows, tuple) and len(frozen_rows) > 0:
            if not all(isinstance(r, Mapping) for r in frozen_rows):
                raise DomainValidationError(
                    "ListingSnapshot.from_content rows must be a list of row "
                    "dicts"
                )
            row_count = len(frozen_rows)
        elif frozen_rows == ():
            row_count = 0
        else:
            raise DomainValidationError(
                "ListingSnapshot.from_content rows must be a list of row dicts"
            )
        return cls(
            snapshot_id=snapshot_id,
            project_id=project_id,
            revision_id=revision_id,
            snapshot_version=snapshot_version,
            content_digest=content_hash(frozen_rows),
            row_count=row_count,
            structure=deep_freeze_json(structure),
            is_synthetic=is_synthetic,
            created_at=created_at,
            _verified=_authority_token,
        )

    def metadata_payload(self) -> Dict[str, Any]:
        """Metadata-only fingerprint (excludes the content bytes/digest)."""
        return {
            "snapshot_id": self.snapshot_id,
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "snapshot_version": self.snapshot_version,
            "row_count": self.row_count,
            "structure": dict(self.structure),
        }

    @property
    def metadata_fingerprint(self) -> str:
        return content_hash(self.metadata_payload())

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "metadata_fingerprint": self.metadata_fingerprint,
            "content_digest": self.content_digest,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Knowledge / rule / mapping
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
@_register_dataclass
class Provenance:
    """Reusable provenance binding: project + source revision + identity alg.

    Knowledge packs, rule activations, mappings and facts all reference one of
    these to bind their authority.  Carrying it as a first-class frozen value
    keeps the schema-registry check centralized.
    """

    schema_name: str = "provenance"
    schema_version: str = "1"
    project_id: str = ""
    source_revision_id: str = ""
    identity_algorithm_id: str = ""
    knowledge_pack_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.project_id:
            raise DomainValidationError("Provenance.project_id is required")


@dataclass(frozen=True)
@_register_dataclass
class IdentityAlgorithm:
    """Frozen record/risk identity algorithm descriptor.

    The Run manifest freezes the identity algorithm (Design 6.2).  Its
    ``digest`` is the content hash of the descriptor so that two runs with
    the same digest are guaranteed to use the same identity semantics.
    """

    schema_name: str = "identity_algorithm"
    schema_version: str = "1"
    algorithm_id: str = ""
    name: str = ""
    version: str = ""
    params: Tuple[Tuple[str, Any], ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.algorithm_id:
            raise DomainValidationError("IdentityAlgorithm.algorithm_id is required")
        if not self.name:
            raise DomainValidationError("IdentityAlgorithm.name is required")
        if not self.version:
            raise DomainValidationError("IdentityAlgorithm.version is required")
        object.__setattr__(self, "params", deep_freeze_json(self.params))

    @property
    def digest(self) -> str:
        return content_hash({
            "algorithm_id": self.algorithm_id,
            "name": self.name,
            "version": self.version,
            "params": dict(self.params),
        })


@dataclass(frozen=True)
@_register_dataclass
class StudyKnowledgePack:
    """Project requirements/endpoints/dosing/visits/control-points (Design 5,7).

    Versioned; project files take precedence within their claim scope.  The
    pack binds the project + source revision + identity algorithm so the
    knowledge layer is reproducible.
    """

    schema_name: str = "study_knowledge_pack"
    schema_version: str = "1"
    pack_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    identity_algorithm_id: str = ""
    version: str = ""
    content_hash: str = ""
    layers: Tuple[Tuple[str, Any], ...] = ()   # four-layer knowledge
    claim_scope: Tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.pack_id:
            raise DomainValidationError("StudyKnowledgePack.pack_id is required")
        if not self.project_id:
            raise DomainValidationError("StudyKnowledgePack.project_id is required")
        if not self.version:
            raise DomainValidationError("StudyKnowledgePack.version is required")
        if not self.source_revision_id:
            raise ProvenanceError(
                "StudyKnowledgePack must bind a source_revision_id"
            )
        if not self.identity_algorithm_id:
            raise ProvenanceError(
                "StudyKnowledgePack must bind an identity_algorithm_id"
            )
        object.__setattr__(self, "layers", deep_freeze_json(self.layers))
        object.__setattr__(self, "claim_scope", deep_freeze_json(self.claim_scope))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"StudyKnowledgePack.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "identity_algorithm_id": self.identity_algorithm_id,
            "version": self.version,
            "layers": dict(self.layers),
            "claim_scope": list(self.claim_scope),
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
@_register_dataclass
class RuleActivation:
    """Approved activation of a decomposed natural-language rule (Design 5,7).

    Freezes scope, version, retroactivity and impact analysis.  Binds
    project + source revision so reactivation is reproducible.
    """

    schema_name: str = "rule_activation"
    schema_version: str = "1"
    activation_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    knowledge_pack_id: str = ""
    rule_text: str = ""
    activated_version: str = ""
    activated_by: str = ""
    scope: Tuple[str, ...] = ()
    retroactive_from: Optional[str] = None
    impact_analysis: Tuple[Tuple[str, Any], ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.activation_id:
            raise DomainValidationError("RuleActivation.activation_id is required")
        if not self.project_id:
            raise DomainValidationError("RuleActivation.project_id is required")
        if not self.source_revision_id:
            raise ProvenanceError("RuleActivation must bind a source_revision_id")
        if not self.knowledge_pack_id:
            raise ProvenanceError("RuleActivation must bind a knowledge_pack_id")
        if not self.rule_text:
            raise DomainValidationError("RuleActivation.rule_text is required")
        if not self.activated_version:
            raise DomainValidationError("RuleActivation.activated_version is required")
        if not self.activated_by:
            raise DomainValidationError("RuleActivation.activated_by is required")
        object.__setattr__(self, "scope", deep_freeze_json(self.scope))
        object.__setattr__(self, "impact_analysis", deep_freeze_json(self.impact_analysis))


@dataclass(frozen=True)
@_register_dataclass
class MappingDefinition:
    """Semantic mapping definition: source field -> canonical field (Design 5).

    Versioned; binds project + source revision + identity algorithm so the
    same listing maps reproducibly.  ``confidence`` in [0,1]; ``is_critical``
    flags mappings whose ambiguity blocks baseline eligibility.
    """

    schema_name: str = "mapping_definition"
    schema_version: str = "1"
    mapping_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    identity_algorithm_id: str = ""
    source_field: str = ""
    canonical_field: str = ""
    fact_type: str = ""
    version: str = ""
    confidence: float = 1.0
    is_critical: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        if not self.mapping_id:
            raise DomainValidationError("MappingDefinition.mapping_id is required")
        if not self.project_id:
            raise DomainValidationError("MappingDefinition.project_id is required")
        if not self.source_revision_id:
            raise ProvenanceError("MappingDefinition must bind a source_revision_id")
        if not self.identity_algorithm_id:
            raise ProvenanceError(
                "MappingDefinition must bind an identity_algorithm_id"
            )
        if not self.source_field or not self.canonical_field:
            raise DomainValidationError(
                "MappingDefinition.source_field and canonical_field are required"
            )
        if not self.version:
            raise DomainValidationError("MappingDefinition.version is required")
        if not (0.0 <= self.confidence <= 1.0):
            raise DomainValidationError(
                f"MappingDefinition.confidence must be in [0,1], got {self.confidence}"
            )

    def canonical_payload(self) -> Dict[str, Any]:
        """Full semantic mapping contract, excluding operational timestamp."""
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "mapping_id": self.mapping_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "identity_algorithm_id": self.identity_algorithm_id,
            "source_field": self.source_field,
            "canonical_field": self.canonical_field,
            "fact_type": self.fact_type,
            "version": self.version,
            "confidence": self.confidence,
            "is_critical": self.is_critical,
        }

    @property
    def digest(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
@_register_dataclass
class MappingResult:
    """A materialized mapping result against one snapshot (Design 5).

    Binds the mapping definition, the snapshot it was produced against, and
    the identity algorithm used.  ``is_ambiguous`` flags results whose
    identity/scope ambiguity blocks baseline eligibility.
    """

    schema_name: str = "mapping_result"
    schema_version: str = "1"
    result_id: str = ""
    project_id: str = ""
    snapshot_id: str = ""
    mapping_id: str = ""
    mapping_definition_digest: str = ""
    identity_algorithm_id: str = ""
    record_count: int = 0
    identity_digest: str = ""
    is_ambiguous: bool = False
    ambiguity_reason: str = ""
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _VERIFIED,
    ) -> None:
        _validate_schema(self)
        if not self.result_id:
            raise DomainValidationError("MappingResult.result_id is required")
        if not self.project_id:
            raise DomainValidationError("MappingResult.project_id is required")
        if not self.snapshot_id:
            raise DomainValidationError("MappingResult.snapshot_id is required")
        if not self.mapping_id:
            raise DomainValidationError("MappingResult.mapping_id is required")
        validate_sha256_hex(
            self.mapping_definition_digest,
            "MappingResult.mapping_definition_digest",
        )
        if not self.identity_algorithm_id:
            raise ProvenanceError("MappingResult must bind an identity_algorithm_id")
        if self.record_count < 0:
            raise DomainValidationError("MappingResult.record_count must be >= 0")
        if self.is_ambiguous and not self.ambiguity_reason:
            raise DomainValidationError(
                "MappingResult.is_ambiguous requires ambiguity_reason"
            )
        if _verified is not _authority_token:
            raise DomainValidationError(
                "MappingResult requires verified mapping/snapshot/identity "
                "binding; use MappingResult.from_verified(...) to construct "
                "an authoritative result"
            )

    @classmethod
    def from_verified(
        cls,
        result_id: str,
        project_id: str,
        snapshot: "ListingSnapshot",
        mapping: "MappingDefinition",
        identity_algorithm: "IdentityAlgorithm",
        *,
        record_count: int = 0,
        identity_digest: str = "",
        is_ambiguous: bool = False,
        ambiguity_reason: str = "",
        created_at: str = "",
        _authority_token: Any = _VERIFIED,
    ) -> "MappingResult":
        """Authoritative mapping result bound to real, verified objects.

        Validates cross-project/snapshot/source consistency: the snapshot and
        mapping must belong to the same project/source revision, and the
        identity algorithm reference must match the mapping's own binding.
        ``identity_digest`` is validated as a canonical SHA-256 when supplied.
        """
        if snapshot.project_id != project_id or mapping.project_id != project_id:
            raise ProvenanceError(
                "MappingResult project_id must match both snapshot and "
                "mapping project_id"
            )
        if mapping.source_revision_id != snapshot.revision_id:
            raise ProvenanceError(
                "MappingResult mapping.source_revision_id must match "
                "snapshot.revision_id"
            )
        if mapping.identity_algorithm_id != identity_algorithm.algorithm_id:
            raise ProvenanceError(
                "MappingResult identity_algorithm must match the mapping's "
                "identity_algorithm_id"
            )
        if record_count != snapshot.row_count:
            raise ProvenanceError(
                "MappingResult record_count must cover the complete snapshot: "
                f"got {record_count}, expected {snapshot.row_count}"
            )
        if identity_digest:
            validate_sha256_hex(identity_digest, "MappingResult.identity_digest")
        return cls(
            result_id=result_id,
            project_id=project_id,
            snapshot_id=snapshot.snapshot_id,
            mapping_id=mapping.mapping_id,
            mapping_definition_digest=mapping.digest,
            identity_algorithm_id=identity_algorithm.algorithm_id,
            record_count=record_count,
            identity_digest=identity_digest,
            is_ambiguous=is_ambiguous,
            ambiguity_reason=ambiguity_reason,
            created_at=created_at,
            _verified=_authority_token,
        )


@dataclass(frozen=True)
@_register_dataclass
class CanonicalFact:
    """Normalized clinical fact bound to source, record identity and mapping.

    Facts-only (``role`` is always ``facts``); candidate/inference/suggestion
    payloads must use :class:`ArtifactEnvelope` payload roles.  The fact binds
    project + source revision + snapshot + the stable record identity digest +
    the identity algorithm digest + the accepted mapping result so provenance
    is one-hop-traceable and the fact cannot drift from its producing mapping.

    The public ``fact_id`` is deterministic: derived from the identity payload
    (project/source/snapshot/type/record/mapping/location/payload).  A supplied
    ``fact_id`` must match exactly.
    """

    schema_name: str = "canonical_fact"
    schema_version: str = "1"
    fact_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    snapshot_id: str = ""
    fact_type: str = ""
    record_identity_digest: str = ""
    identity_algorithm_digest: str = ""
    mapping_result_id: str = ""
    mapping_definition_digest: str = ""
    role: str = "facts"             # ALWAYS facts; validated below
    payload: Tuple[Tuple[str, Any], ...] = ()
    source_location: Tuple[Tuple[str, Any], ...] = ()
    content_hash: str = ""
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _VERIFIED,
    ) -> None:
        _validate_schema(self)
        if not self.project_id:
            raise DomainValidationError("CanonicalFact.project_id is required")
        if not self.source_revision_id:
            raise ProvenanceError("CanonicalFact must bind a source_revision_id")
        if not self.snapshot_id:
            raise ProvenanceError("CanonicalFact must bind a snapshot_id")
        if not self.fact_type:
            raise DomainValidationError("CanonicalFact.fact_type is required")
        validate_sha256_hex(
            self.record_identity_digest, "CanonicalFact.record_identity_digest"
        )
        validate_sha256_hex(
            self.identity_algorithm_digest, "CanonicalFact.identity_algorithm_digest"
        )
        if not self.mapping_result_id:
            raise ProvenanceError(
                "CanonicalFact must bind a mapping_result_id"
            )
        validate_sha256_hex(
            self.mapping_definition_digest,
            "CanonicalFact.mapping_definition_digest",
        )
        if self.role != "facts":
            raise DomainValidationError(
                f"CanonicalFact.role must be 'facts'; got {self.role!r}. "
                f"Candidate/inference/suggestion payloads must use "
                f"ArtifactEnvelope payload roles, not CanonicalFact."
            )
        if _verified is not _authority_token:
            raise DomainValidationError(
                "CanonicalFact requires verified record identity, identity "
                "algorithm and mapping binding; use CanonicalFact.from_bundle(...)"
            )
        object.__setattr__(self, "payload", deep_freeze_json(self.payload))
        object.__setattr__(self, "source_location", deep_freeze_json(self.source_location))
        # Deterministic fact_id from identity payload.
        derived = self._derive_fact_id()
        if not self.fact_id:
            object.__setattr__(self, "fact_id", derived)
        elif self.fact_id != derived:
            raise DomainValidationError(
                f"CanonicalFact.fact_id {self.fact_id!r} does not match the "
                f"deterministic identity-derived id {derived!r}"
            )
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"CanonicalFact.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    @classmethod
    def from_bundle(
        cls,
        project: "StudyProject",
        source: "SourceRevision",
        snapshot: "ListingSnapshot",
        record_identity: "RecordIdentity",
        identity_algorithm: "IdentityAlgorithm",
        mapping_definition: "MappingDefinition",
        mapping_result: "MappingResult",
        fact_type: str,
        *,
        payload: Tuple[Tuple[str, Any], ...] = (),
        source_location: Tuple[Tuple[str, Any], ...] = (),
        created_at: str = "",
        _authority_token: Any = _VERIFIED,
    ) -> "CanonicalFact":
        """Authoritative fact constructed from a verified reference bundle.

        Validates cross-project/snapshot/source consistency across every
        bound object and rejects fabricated/unresolved references.  The
        record identity and mapping result must reference the same project /
        snapshot / source revision / identity algorithm as the fact being
        built.
        """
        from .identity import RecordIdentity  # local import to avoid cycle
        pid = project.project_id
        if source.project_id != pid:
            raise ProvenanceError("CanonicalFact source project_id mismatch")
        if snapshot.project_id != pid or snapshot.revision_id != source.revision_id:
            raise ProvenanceError(
                "CanonicalFact snapshot must match project and source revision"
            )
        if record_identity.project_id != pid:
            raise ProvenanceError("CanonicalFact record identity project_id mismatch")
        if record_identity.algorithm_digest != identity_algorithm.digest:
            raise ProvenanceError(
                "CanonicalFact record identity algorithm_digest must match the "
                "identity algorithm"
            )
        if mapping_result.project_id != pid:
            raise ProvenanceError("CanonicalFact mapping result project_id mismatch")
        if mapping_definition.project_id != pid:
            raise ProvenanceError(
                "CanonicalFact mapping definition project_id mismatch"
            )
        if mapping_definition.source_revision_id != source.revision_id:
            raise ProvenanceError(
                "CanonicalFact mapping definition source revision mismatch"
            )
        if mapping_definition.identity_algorithm_id != identity_algorithm.algorithm_id:
            raise ProvenanceError(
                "CanonicalFact mapping definition identity algorithm must match"
            )
        if mapping_result.mapping_id != mapping_definition.mapping_id:
            raise ProvenanceError(
                "CanonicalFact mapping result must bind the supplied mapping definition"
            )
        if mapping_result.mapping_definition_digest != mapping_definition.digest:
            raise ProvenanceError(
                "CanonicalFact mapping result does not bind the supplied "
                "mapping definition semantics"
            )
        if mapping_result.snapshot_id != snapshot.snapshot_id:
            raise ProvenanceError(
                "CanonicalFact mapping result must reference the same snapshot"
            )
        if mapping_result.identity_algorithm_id != identity_algorithm.algorithm_id:
            raise ProvenanceError(
                "CanonicalFact mapping result identity algorithm must match"
            )
        if not mapping_definition.fact_type:
            raise ProvenanceError(
                "CanonicalFact mapping definition must declare fact_type"
            )
        if mapping_definition.fact_type.casefold() != fact_type.casefold():
            raise ProvenanceError(
                "CanonicalFact fact_type does not match mapping definition semantics"
            )
        return cls(
            project_id=pid,
            source_revision_id=source.revision_id,
            snapshot_id=snapshot.snapshot_id,
            fact_type=fact_type,
            record_identity_digest=record_identity.digest,
            identity_algorithm_digest=identity_algorithm.digest,
            mapping_result_id=mapping_result.result_id,
            mapping_definition_digest=mapping_definition.digest,
            payload=deep_freeze_json(payload),
            source_location=deep_freeze_json(source_location),
            created_at=created_at,
            _verified=_authority_token,
        )

    def identity_payload(self) -> Dict[str, Any]:
        """Fields that determine the deterministic fact identity."""
        return {
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "fact_type": self.fact_type,
            "record_identity_digest": self.record_identity_digest,
            "identity_algorithm_digest": self.identity_algorithm_digest,
            "mapping_result_id": self.mapping_result_id,
            "mapping_definition_digest": self.mapping_definition_digest,
            "source_location": dict(self.source_location),
            "payload": dict(self.payload),
        }

    def _derive_fact_id(self) -> str:
        return f"fact-{content_hash(self.identity_payload())}"

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "identity_payload": self.identity_payload(),
            "role": self.role,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# Replace the build-time methods with clean closure-backed public surfaces.
# The token is not exposed in a public signature/default or module attribute;
# only these closures retain it after module initialization.
def _seal_authoritative_surface(authority_token: Any) -> None:
    source_post = SourceRevision.__post_init__
    source_factory = SourceRevision.from_bytes.__func__
    snapshot_post = ListingSnapshot.__post_init__
    snapshot_factory = ListingSnapshot.from_content.__func__
    mapping_post = MappingResult.__post_init__
    mapping_factory = MappingResult.from_verified.__func__
    fact_post = CanonicalFact.__post_init__
    fact_factory = CanonicalFact.from_bundle.__func__

    def checked_source_post(self, _verified: Any = None) -> None:
        return source_post(self, _verified, authority_token)

    def checked_source_factory(
        cls, revision_id: str, project_id: str, source_type: str, version: str,
        source_bytes: bytes, *, scope: Tuple[Tuple[str, Any], ...] = (),
        valid_from: Optional[str] = None, created_at: str = "",
    ) -> "SourceRevision":
        return source_factory(
            cls, revision_id, project_id, source_type, version, source_bytes,
            scope=scope, valid_from=valid_from, created_at=created_at,
            _authority_token=authority_token,
        )

    def checked_snapshot_post(self, _verified: Any = None) -> None:
        return snapshot_post(self, _verified, authority_token)

    def checked_snapshot_factory(
        cls, snapshot_id: str, project_id: str, revision_id: str,
        snapshot_version: str, rows: Any, *,
        structure: Tuple[Tuple[str, Any], ...] = (),
        is_synthetic: bool = True, created_at: str = "",
    ) -> "ListingSnapshot":
        return snapshot_factory(
            cls, snapshot_id, project_id, revision_id, snapshot_version, rows,
            structure=structure, is_synthetic=is_synthetic,
            created_at=created_at, _authority_token=authority_token,
        )

    def checked_mapping_post(self, _verified: Any = None) -> None:
        return mapping_post(self, _verified, authority_token)

    def checked_mapping_factory(
        cls, result_id: str, project_id: str, snapshot: "ListingSnapshot",
        mapping: "MappingDefinition", identity_algorithm: "IdentityAlgorithm",
        *, record_count: int = 0, identity_digest: str = "",
        is_ambiguous: bool = False, ambiguity_reason: str = "",
        created_at: str = "",
    ) -> "MappingResult":
        return mapping_factory(
            cls, result_id, project_id, snapshot, mapping, identity_algorithm,
            record_count=record_count, identity_digest=identity_digest,
            is_ambiguous=is_ambiguous, ambiguity_reason=ambiguity_reason,
            created_at=created_at, _authority_token=authority_token,
        )

    def checked_fact_post(self, _verified: Any = None) -> None:
        return fact_post(self, _verified, authority_token)

    def checked_fact_factory(
        cls, project: "StudyProject", source: "SourceRevision",
        snapshot: "ListingSnapshot", record_identity: "RecordIdentity",
        identity_algorithm: "IdentityAlgorithm",
        mapping_definition: "MappingDefinition",
        mapping_result: "MappingResult", fact_type: str, *,
        payload: Tuple[Tuple[str, Any], ...] = (),
        source_location: Tuple[Tuple[str, Any], ...] = (),
        created_at: str = "",
    ) -> "CanonicalFact":
        return fact_factory(
            cls, project, source, snapshot, record_identity,
            identity_algorithm, mapping_definition, mapping_result, fact_type,
            payload=payload, source_location=source_location,
            created_at=created_at, _authority_token=authority_token,
        )

    SourceRevision.__post_init__ = checked_source_post
    SourceRevision.from_bytes = classmethod(checked_source_factory)
    ListingSnapshot.__post_init__ = checked_snapshot_post
    ListingSnapshot.from_content = classmethod(checked_snapshot_factory)
    MappingResult.__post_init__ = checked_mapping_post
    MappingResult.from_verified = classmethod(checked_mapping_factory)
    CanonicalFact.__post_init__ = checked_fact_post
    CanonicalFact.from_bundle = classmethod(checked_fact_factory)


_seal_authoritative_surface(_VERIFIED)
del _seal_authoritative_surface
del _VERIFIED
