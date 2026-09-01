"""R3-A knowledge domain: source classification, version/valid-time/scope,
Study Knowledge Pack, claim authority matrix, and source conflict/resolution
(Design 5, 7; plan R3 step 1-3).

Design principles (from the system design and user revisions):
- **来源优先 (source-first)**: project files take precedence within their
  claim scope; nothing overrides a project source inside its declared scope
  without an auditable resolution.
- **冲突不静默覆盖**: a source conflict is recorded as a ``SourceConflict``
  and resolved only via an explicit ``ConflictResolution`` that names the
  winning source, the basis, and the residual uncertainty.  There is no
  "last writer wins" path.
- **claim authority is layered**: the four knowledge layers
  (general medical, drug/mechanism, project documents, activated rules)
  each declare an authority level; a claim records every supporting source
  so the authority matrix is auditable.
- **immutable + content-addressed**: every entity is a frozen dataclass; a
  content digest binds real content bytes so a fabricated digest cannot bless
  an unverified source.
- **scope is explicit**: a source without a declared scope is
  ``scope_unspecified`` and never silently treated as "covers everything".

This module is R3-internal and never imports the frozen R2 package.
"""

from __future__ import annotations

from dataclasses import dataclass, field, InitVar
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .primitives import (
    ImmutableDict,
    canonical_json,
    content_hash,
    deep_freeze_json,
    now_iso,
    new_id,
    sha256_hex,
    validate_iso_date,
    validate_nonempty_str,
    validate_sha256_hex,
)
from .schema_registry import default_registry

__all__ = [
    "MmR3Error",
    "DomainValidationError",
    "ProvenanceError",
    "HashMismatchError",
    "ConflictError",
    "SourceType",
    "KnowledgeLayer",
    "ClaimStatus",
    "ConflictType",
    "ResolutionOutcome",
    "SourceRevision",
    "SourceClassification",
    "StudyKnowledgePack",
    "Claim",
    "ClaimAuthority",
    "SourceConflict",
    "ConflictResolution",
    "ConflictResolutionLog",
    "SUPPORTED_SOURCE_TYPES",
    "KNOWLEDGE_LAYERS",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class MmR3Error(Exception):
    """Base class for all R3 POC errors."""


class DomainValidationError(MmR3Error):
    """An entity failed invariant validation."""


class ProvenanceError(MmR3Error):
    """Missing or inconsistent provenance binding."""


class HashMismatchError(MmR3Error):
    """A content hash did not match the recomputed canonical hash."""


class ConflictError(MmR3Error):
    """A source conflict invariant was violated."""


# ---------------------------------------------------------------------------
# Authority token (captured into factories, deleted from module namespace)
# ---------------------------------------------------------------------------

# Like R2, a construction capability is captured into the authoritative
# factories below and removed from the module namespace, so a public caller
# cannot retrieve it as an ordinary attribute and bless fabricated content.
_VERIFIED = object()


# ---------------------------------------------------------------------------
# Enumerations (as tuples of string constants; frozen dataclasses validate)
# ---------------------------------------------------------------------------

SUPPORTED_SOURCE_TYPES: Tuple[str, ...] = (
    "protocol",
    "protocol_amendment",
    "ib",
    "rsi",
    "sap",
    "project_plan",
    "listing",
    "report",
    "external_evidence",
    "other",
)

#: Four-layer knowledge (Design 7).  Ordered low -> high precedence within a
#: claim scope, but project documents (layer 3) win inside their scope.
KNOWLEDGE_LAYERS: Tuple[str, ...] = (
    "general_medical",
    "drug_mechanism",
    "project_documents",
    "activated_rules",
)

#: Authority level of a knowledge layer.  ``activated_rules`` are derived
#: artifacts (not primary medical truth) so they carry the lowest authority
#: *unless* the user explicitly activated them; the authority matrix records
#: the actual level per source, not a blanket rank.
_LAYER_DEFAULT_AUTHORITY: Dict[str, str] = {
    "general_medical": "reference",
    "drug_mechanism": "reference",
    "project_documents": "project_authoritative",
    "activated_rules": "derived",
}


def _validate_enum(value: str, allowed: Tuple[str, ...], field_name: str) -> str:
    if value not in allowed:
        raise DomainValidationError(
            f"{field_name} must be one of {allowed}, got {value!r}"
        )
    return value


class SourceType:
    """Namespace for source_type string constants."""

    PROTOCOL = "protocol"
    PROTOCOL_AMENDMENT = "protocol_amendment"
    IB = "ib"
    RSI = "rsi"
    SAP = "sap"
    PROJECT_PLAN = "project_plan"
    LISTING = "listing"
    REPORT = "report"
    EXTERNAL_EVIDENCE = "external_evidence"
    OTHER = "other"


class KnowledgeLayer:
    """Namespace for knowledge-layer string constants."""

    GENERAL_MEDICAL = "general_medical"
    DRUG_MECHANISM = "drug_mechanism"
    PROJECT_DOCUMENTS = "project_documents"
    ACTIVATED_RULES = "activated_rules"


class ClaimStatus:
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONFLICTED = "conflicted"
    NOT_EVALUABLE = "not_evaluable"


CLAIM_STATUSES: Tuple[str, ...] = (
    ClaimStatus.SUPPORTED,
    ClaimStatus.PARTIALLY_SUPPORTED,
    ClaimStatus.UNSUPPORTED,
    ClaimStatus.CONFLICTED,
    ClaimStatus.NOT_EVALUABLE,
)


class ConflictType:
    CONTRADICTION = "contradiction"
    VERSION_MISMATCH = "version_mismatch"
    SCOPE_OVERLAP = "scope_overlap"
    TEMPORAL = "temporal"
    PARTIAL_DATE = "partial_date"
    UNIT = "unit"
    CODING = "coding"
    OTHER = "other"


CONFLICT_TYPES: Tuple[str, ...] = (
    ConflictType.CONTRADICTION,
    ConflictType.VERSION_MISMATCH,
    ConflictType.SCOPE_OVERLAP,
    ConflictType.TEMPORAL,
    ConflictType.PARTIAL_DATE,
    ConflictType.UNIT,
    ConflictType.CODING,
    ConflictType.OTHER,
)


class ResolutionOutcome:
    PROJECT_SOURCE_WINS = "project_source_wins"
    LATER_REVISION_WINS = "later_revision_wins"
    EXPLICIT_SCOPE_WINS = "explicit_scope_wins"
    USER_ADJUDICATED = "user_adjudicated"
    UNRESOLVED = "unresolved"
    NOT_EVALUABLE = "not_evaluable"


RESOLUTION_OUTCOMES: Tuple[str, ...] = (
    ResolutionOutcome.PROJECT_SOURCE_WINS,
    ResolutionOutcome.LATER_REVISION_WINS,
    ResolutionOutcome.EXPLICIT_SCOPE_WINS,
    ResolutionOutcome.USER_ADJUDICATED,
    ResolutionOutcome.UNRESOLVED,
    ResolutionOutcome.NOT_EVALUABLE,
)


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Source revision (immutable, content-addressed, version/valid-time/scope)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceRevision:
    """Immutable source revision: protocol/IB/listing/report/other.

    Carries version, valid-time window (``valid_from``/``valid_until``) and
    an explicit scope.  ``content_digest`` is a real SHA-256 over the actual
    immutable source bytes (computed by :meth:`from_bytes`).  ``content_hash``
    is the full identity binding (metadata fingerprint + content digest).

    A source with an empty ``scope`` is ``scope_unspecified`` and never
    silently treated as covering everything (Design: 来源优先).
    """

    schema_name: str = "r3_source_revision"
    schema_version: str = "1"
    revision_id: str = ""
    project_id: str = ""
    source_type: str = ""
    version: str = ""
    content_digest: str = ""
    content_hash: str = ""
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    scope: Tuple[Tuple[str, Any], ...] = ()
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self,
        _verified: Any = None,
        _authority_token: Any = _VERIFIED,
    ) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.revision_id, "SourceRevision.revision_id")
        validate_nonempty_str(self.project_id, "SourceRevision.project_id")
        _validate_enum(self.source_type, SUPPORTED_SOURCE_TYPES, "SourceRevision.source_type")
        validate_nonempty_str(self.version, "SourceRevision.version")
        validate_sha256_hex(self.content_digest, "SourceRevision.content_digest")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "SourceRevision requires verified source bytes; use "
                "SourceRevision.from_bytes(...) (digest-only construction is "
                "unavailable to public callers)"
            )
        if self.valid_from is not None:
            validate_iso_date(self.valid_from, "SourceRevision.valid_from")
        if self.valid_until is not None:
            validate_iso_date(self.valid_until, "SourceRevision.valid_until")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise DomainValidationError(
                "SourceRevision.valid_until must not precede valid_from"
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
        valid_until: Optional[str] = None,
        created_at: str = "",
        _authority_token: Any = _VERIFIED,
    ) -> "SourceRevision":
        """Authoritative constructor: receives actual immutable source bytes,
        computes ``content_digest`` internally, verifies the identity binding.
        Digest-only construction is unavailable to public callers.
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
            scope=scope,
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=created_at,
            _verified=_authority_token,
        )

    # -- scope semantics ---------------------------------------------------

    @property
    def scope_unspecified(self) -> bool:
        """True when no scope facet was declared."""
        return len(self.scope) == 0

    def scope_get(self, key: str, default: Any = None) -> Any:
        """Read a scope facet by key (scope is a frozen tuple of pairs)."""
        for k, v in self.scope:
            if k == key:
                return v
        return default

    def scope_contains(self, key: str, value: Any) -> bool:
        """True if the declared scope has ``key == value``."""
        for k, v in self.scope:
            if k == key and v == value:
                return True
        return False

    def overlaps_scope(self, other: "SourceRevision", key: str) -> bool:
        """Both sources declare the same ``key`` facet value.

        Two ``scope_unspecified`` sources are NOT considered overlapping:
        an unspecified scope never silently matches another.
        """
        if self.scope_unspecified or other.scope_unspecified:
            return False
        return self.scope_get(key) is not None and self.scope_get(key) == other.scope_get(key)

    def is_valid_at(self, when: str) -> bool:
        """True if ``when`` (YYYY-MM-DD) is inside the valid-time window."""
        validate_iso_date(when, "when")
        if self.valid_from is not None and when < self.valid_from:
            return False
        if self.valid_until is not None and when > self.valid_until:
            return False
        return True

    # -- hashing -----------------------------------------------------------

    def metadata_payload(self) -> Dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "project_id": self.project_id,
            "source_type": self.source_type,
            "version": self.version,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
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


# ---------------------------------------------------------------------------
# Source classification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceClassification:
    """Classification of one source revision into a knowledge layer and
    authority level.

    Maps a :class:`SourceRevision` to one of the four knowledge layers and an
    authority level, and records whether it is a primary project document
    (which wins inside its scope) or a reference/derived source.
    """

    schema_name: str = "r3_source_classification"
    schema_version: str = "1"
    classification_id: str = ""
    revision_id: str = ""
    knowledge_layer: str = ""
    authority_level: str = ""
    is_primary_project_document: bool = False
    classification_basis: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.classification_id, "SourceClassification.classification_id")
        validate_nonempty_str(self.revision_id, "SourceClassification.revision_id")
        _validate_enum(self.knowledge_layer, KNOWLEDGE_LAYERS, "SourceClassification.knowledge_layer")
        if not self.authority_level:
            # default by layer, but must be non-empty after defaulting
            object.__setattr__(
                self,
                "authority_level",
                _LAYER_DEFAULT_AUTHORITY.get(self.knowledge_layer, "reference"),
            )
        if self.is_primary_project_document and self.knowledge_layer != "project_documents":
            raise DomainValidationError(
                "a primary project document must be in the "
                "'project_documents' knowledge layer"
            )

    @property
    def is_project_authoritative(self) -> bool:
        return self.authority_level == "project_authoritative"

    @classmethod
    def for_revision(
        cls,
        revision: SourceRevision,
        *,
        knowledge_layer: str,
        classification_id: str = "",
        authority_level: str = "",
        is_primary_project_document: bool = False,
        classification_basis: str = "",
        created_at: str = "",
    ) -> "SourceClassification":
        """Build a classification bound to a real revision id."""
        _validate_enum(knowledge_layer, KNOWLEDGE_LAYERS, "knowledge_layer")
        return cls(
            classification_id=classification_id or new_id("cls-"),
            revision_id=revision.revision_id,
            knowledge_layer=knowledge_layer,
            authority_level=authority_level or _LAYER_DEFAULT_AUTHORITY.get(knowledge_layer, "reference"),
            is_primary_project_document=is_primary_project_document,
            classification_basis=classification_basis,
            created_at=created_at or now_iso(),
        )


# ---------------------------------------------------------------------------
# Study Knowledge Pack (versioned, four-layer, content-addressed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StudyKnowledgePack:
    """Project Study Knowledge Pack (Design 5, 7).

    Versioned; binds the project + source revision + four-layer knowledge
    content.  ``content_hash`` makes the full knowledge content reproducible.
    Project documents take precedence *within their claim scope*; the pack
    records each layer's contributions but does not flatten authority.
    """

    schema_name: str = "r3_knowledge_pack"
    schema_version: str = "1"
    pack_id: str = ""
    project_id: str = ""
    version: str = ""
    source_revision_ids: Tuple[str, ...] = ()
    layers: Tuple[Tuple[str, Any], ...] = ()
    claim_scope: Tuple[str, ...] = ()
    content_hash: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.pack_id, "StudyKnowledgePack.pack_id")
        validate_nonempty_str(self.project_id, "StudyKnowledgePack.project_id")
        validate_nonempty_str(self.version, "StudyKnowledgePack.version")
        if not self.source_revision_ids:
            raise ProvenanceError(
                "StudyKnowledgePack must bind at least one source_revision_id"
            )
        object.__setattr__(self, "source_revision_ids", deep_freeze_json(self.source_revision_ids))
        object.__setattr__(self, "layers", deep_freeze_json(self.layers))
        object.__setattr__(self, "claim_scope", deep_freeze_json(self.claim_scope))
        # validate layer keys
        for layer_key, _ in self.layers:
            _validate_enum(layer_key, KNOWLEDGE_LAYERS, "StudyKnowledgePack layer key")
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"StudyKnowledgePack.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def layer(self, key: str) -> Any:
        """Return the (frozen) content of one knowledge layer, or None."""
        for k, v in self.layers:
            if k == key:
                return v
        return None

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "project_id": self.project_id,
            "version": self.version,
            "source_revision_ids": list(self.source_revision_ids),
            "layers": dict(self.layers),
            "claim_scope": list(self.claim_scope),
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Claim + claim authority matrix
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Claim:
    """An atomic, traceable claim extracted from one source.

    A claim is scoped (e.g. ``ae_grading``, ``dosing``, ``endpoint``) and
    bound to exactly one source revision + locator so its authority can be
    audited.  Claims never auto-promote; they feed the authority matrix.
    """

    schema_name: str = "r3_claim"
    schema_version: str = "1"
    claim_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    claim_scope: str = ""
    statement: str = ""
    locator: Tuple[Tuple[str, Any], ...] = ()
    raw_value: Any = None
    status: str = ClaimStatus.SUPPORTED
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.claim_id, "Claim.claim_id")
        validate_nonempty_str(self.project_id, "Claim.project_id")
        validate_nonempty_str(self.source_revision_id, "Claim.source_revision_id")
        validate_nonempty_str(self.claim_scope, "Claim.claim_scope")
        validate_nonempty_str(self.statement, "Claim.statement")
        _validate_enum(self.status, CLAIM_STATUSES, "Claim.status")
        object.__setattr__(self, "locator", deep_freeze_json(self.locator))
        object.__setattr__(self, "raw_value", deep_freeze_json(self.raw_value))

    def locator_get(self, key: str, default: Any = None) -> Any:
        for k, v in self.locator:
            if k == key:
                return v
        return default


@dataclass(frozen=True)
class ClaimAuthority:
    """Claim authority matrix: one claim scoped across multiple sources.

    Records every supporting claim and the authority level of each source so
    that precedence is auditable rather than implicit.  Status is *derived*
    from the contributing claims, not declared by the caller:

    * no claims -> ``not_evaluable``
    * any contributing claim is ``conflicted`` or two claims with different
      raw values on the same scope -> ``conflicted``
    * all supporting claims agree -> ``supported``
    * partial agreement -> ``partially_supported``
    * none support -> ``unsupported``

    The highest authority contributor wins inside its scope; but a conflict
    is never silently overwritten -- it is surfaced for explicit resolution.
    """

    schema_name: str = "r3_claim_authority"
    schema_version: str = "1"
    authority_id: str = ""
    project_id: str = ""
    claim_scope: str = ""
    contributions: Tuple[Tuple[str, Any], ...] = ()
    derived_status: str = ClaimStatus.NOT_EVALUABLE
    content_hash: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.authority_id, "ClaimAuthority.authority_id")
        validate_nonempty_str(self.project_id, "ClaimAuthority.project_id")
        validate_nonempty_str(self.claim_scope, "ClaimAuthority.claim_scope")
        object.__setattr__(self, "contributions", deep_freeze_json(self.contributions))
        _validate_enum(self.derived_status, CLAIM_STATUSES, "ClaimAuthority.derived_status")
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise HashMismatchError(
                f"ClaimAuthority.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "project_id": self.project_id,
            "claim_scope": self.claim_scope,
            "contributions": dict(self.contributions),
            "derived_status": self.derived_status,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())

    @classmethod
    def from_claims(
        cls,
        claims: List[Claim],
        *,
        authority_id: str = "",
        classifications: Optional[Mapping[str, "SourceClassification"]] = None,
        created_at: str = "",
    ) -> "ClaimAuthority":
        """Build the authority matrix from contributing claims.

        ``classifications`` maps ``source_revision_id`` -> classification so
        each contribution records the knowledge layer / authority level /
        is-primary flag.  Missing classifications default to ``reference``.
        """
        if not claims:
            raise DomainValidationError(
                "ClaimAuthority.from_claims requires at least one claim"
            )
        project_id = claims[0].project_id
        claim_scope = claims[0].claim_scope
        for c in claims:
            if c.project_id != project_id or c.claim_scope != claim_scope:
                raise DomainValidationError(
                    "ClaimAuthority.from_claims claims must share "
                    "project_id and claim_scope"
                )
        classifications = classifications or {}
        contributions = {}
        for c in claims:
            cls_ = classifications.get(c.source_revision_id)
            if cls_ is not None and cls_.revision_id != c.source_revision_id:
                raise ProvenanceError(
                    "classification revision_id does not match the claim source_revision_id"
                )
            contributions[c.claim_id] = {
                "source_revision_id": c.source_revision_id,
                "knowledge_layer": cls_.knowledge_layer if cls_ else "general_medical",
                "authority_level": cls_.authority_level if cls_ else "reference",
                "is_primary_project_document": cls_.is_primary_project_document if cls_ else False,
                "raw_value": c.raw_value,
                "locator": dict(c.locator),
                "status": c.status,
            }
        derived = _derive_authority_status(list(contributions.values()))
        return cls(
            authority_id=authority_id or new_id("auth-"),
            project_id=project_id,
            claim_scope=claim_scope,
            contributions=tuple(contributions.items()),
            derived_status=derived,
            created_at=created_at or now_iso(),
        )


def _derive_authority_status(contribs: List[Dict[str, Any]]) -> str:
    """Derive the authority status from contributions (never silently overwrite)."""
    if not contribs:
        return ClaimStatus.NOT_EVALUABLE
    statuses = [c["status"] for c in contribs]
    if any(s == ClaimStatus.CONFLICTED for s in statuses):
        return ClaimStatus.CONFLICTED
    if any(s == ClaimStatus.NOT_EVALUABLE for s in statuses) and len(contribs) == 1:
        return ClaimStatus.NOT_EVALUABLE
    raw_values = [c["raw_value"] for c in contribs]
    distinct = set(canonical_json(v) for v in raw_values)
    if len(distinct) > 1:
        return ClaimStatus.CONFLICTED
    if all(s == ClaimStatus.SUPPORTED for s in statuses):
        return ClaimStatus.SUPPORTED
    if any(s == ClaimStatus.SUPPORTED for s in statuses):
        return ClaimStatus.PARTIALLY_SUPPORTED
    return ClaimStatus.UNSUPPORTED


# ---------------------------------------------------------------------------
# Source conflict + resolution
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceConflict:
    """A recorded conflict between two or more source claims (Design 7).

    A conflict is *surfaced*, never silently overwritten.  It records the
    conflicting claim ids, the conflict type, and the scope in which the
    conflict occurs.  Resolution happens separately and explicitly.
    """

    schema_name: str = "r3_source_conflict"
    schema_version: str = "1"
    conflict_id: str = ""
    project_id: str = ""
    claim_scope: str = ""
    conflict_type: str = ""
    claim_ids: Tuple[str, ...] = ()
    claim_source_revision_ids: Tuple[Tuple[str, str], ...] = ()
    detail: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.conflict_id, "SourceConflict.conflict_id")
        validate_nonempty_str(self.project_id, "SourceConflict.project_id")
        validate_nonempty_str(self.claim_scope, "SourceConflict.claim_scope")
        _validate_enum(self.conflict_type, CONFLICT_TYPES, "SourceConflict.conflict_type")
        if len(self.claim_ids) < 2:
            raise DomainValidationError(
                "SourceConflict requires at least two claim_ids"
            )
        if len(set(self.claim_ids)) != len(self.claim_ids):
            raise DomainValidationError(
                "SourceConflict claim_ids must be unique"
            )
        claim_ids = deep_freeze_json(self.claim_ids)
        source_pairs = deep_freeze_json(self.claim_source_revision_ids)
        source_map = dict(source_pairs)
        if set(source_map) != set(claim_ids) or len(source_pairs) != len(claim_ids):
            raise ProvenanceError(
                "SourceConflict must bind every claim_id to exactly one source_revision_id"
            )
        for claim_id, revision_id in source_pairs:
            validate_nonempty_str(claim_id, "SourceConflict claim source claim_id")
            validate_nonempty_str(revision_id, "SourceConflict claim source revision_id")
        object.__setattr__(self, "claim_ids", claim_ids)
        object.__setattr__(self, "claim_source_revision_ids", source_pairs)

    def source_revision_id_for_claim(self, claim_id: str) -> str:
        return dict(self.claim_source_revision_ids).get(claim_id, "")

    @classmethod
    def between(
        cls,
        claims: List[Claim],
        *,
        conflict_type: str,
        conflict_id: str = "",
        detail: str = "",
        created_at: str = "",
    ) -> "SourceConflict":
        if len(claims) < 2:
            raise DomainValidationError(
                "SourceConflict.between requires at least two claims"
            )
        project_id = claims[0].project_id
        claim_scope = claims[0].claim_scope
        for c in claims:
            if c.project_id != project_id or c.claim_scope != claim_scope:
                raise DomainValidationError(
                    "SourceConflict.between claims must share project/scope"
                )
        return cls(
            conflict_id=conflict_id or new_id("conf-"),
            project_id=project_id,
            claim_scope=claim_scope,
            conflict_type=conflict_type,
            claim_ids=tuple(c.claim_id for c in claims),
            claim_source_revision_ids=tuple(
                (c.claim_id, c.source_revision_id) for c in claims
            ),
            detail=detail,
            created_at=created_at or now_iso(),
        )


@dataclass(frozen=True)
class ConflictResolution:
    """An explicit, auditable resolution of a :class:`SourceConflict`.

    Records the outcome, the winning source/claim, the basis, and the
    residual uncertainty.  ``UNRESOLVED`` / ``NOT_EVALUABLE`` outcomes never
    declare a winner.  A machine resolution cannot set ``user_confirmed``.
    """

    schema_name: str = "r3_conflict_resolution"
    schema_version: str = "1"
    resolution_id: str = ""
    conflict_id: str = ""
    outcome: str = ""
    winning_claim_id: str = ""
    winning_source_revision_id: str = ""
    basis: str = ""
    residual_uncertainty: str = ""
    resolved_by: str = ""
    is_machine_resolution: bool = True
    user_confirmed: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.resolution_id, "ConflictResolution.resolution_id")
        validate_nonempty_str(self.conflict_id, "ConflictResolution.conflict_id")
        _validate_enum(self.outcome, RESOLUTION_OUTCOMES, "ConflictResolution.outcome")
        validate_nonempty_str(self.resolved_by, "ConflictResolution.resolved_by")
        no_winner = self.outcome in (
            ResolutionOutcome.UNRESOLVED,
            ResolutionOutcome.NOT_EVALUABLE,
        )
        if no_winner and (self.winning_claim_id or self.winning_source_revision_id):
            raise DomainValidationError(
                f"outcome {self.outcome!r} must not declare a winner"
            )
        if not no_winner and not self.winning_claim_id:
            raise DomainValidationError(
                f"outcome {self.outcome!r} requires winning_claim_id"
            )
        if not no_winner and not self.winning_source_revision_id:
            raise DomainValidationError(
                f"outcome {self.outcome!r} requires winning_source_revision_id"
            )
        if self.is_machine_resolution and self.user_confirmed:
            raise DomainValidationError(
                "a machine resolution cannot declare user_confirmed=True"
            )
        if not self.is_machine_resolution and not self.user_confirmed:
            raise DomainValidationError(
                "a user resolution must declare user_confirmed=True"
            )


# ---------------------------------------------------------------------------
# Conflict resolution log (append-only, auditable)
# ---------------------------------------------------------------------------

@dataclass
class ConflictResolutionLog:
    """Append-only log of conflicts and their resolutions for one project.

    A conflict may have zero or one *current* resolution.  Recording a new
    resolution for an already-resolved conflict supersedes the prior one
    (append-only history is preserved).  ``unresolved_conflicts`` exposes
    conflicts that still need attention.
    """

    project_id: str = ""
    _conflicts: List[SourceConflict] = field(default_factory=list)
    _resolutions: List[ConflictResolution] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_nonempty_str(self.project_id, "ConflictResolutionLog.project_id")

    def record_conflict(self, conflict: SourceConflict) -> SourceConflict:
        if conflict.project_id != self.project_id:
            raise ConflictError(
                "conflict project_id does not match this log"
            )
        if any(c.conflict_id == conflict.conflict_id for c in self._conflicts):
            raise ConflictError(
                f"duplicate conflict_id {conflict.conflict_id!r}"
            )
        self._conflicts.append(conflict)
        return conflict

    def resolve(self, resolution: ConflictResolution) -> ConflictResolution:
        # the conflict must exist
        if not any(c.conflict_id == resolution.conflict_id for c in self._conflicts):
            raise ConflictError(
                f"cannot resolve unknown conflict {resolution.conflict_id!r}"
            )
        # winner claim must be among the conflict's claims (when a winner)
        if resolution.winning_claim_id:
            conflict = self._find_conflict(resolution.conflict_id)
            if resolution.winning_claim_id not in conflict.claim_ids:
                raise ConflictError(
                    "winning_claim_id is not among the conflict's claims"
                )
            expected_source_revision_id = conflict.source_revision_id_for_claim(
                resolution.winning_claim_id
            )
            if resolution.winning_source_revision_id != expected_source_revision_id:
                raise ConflictError(
                    "winning_source_revision_id does not match the winning claim"
                )
        self._resolutions.append(resolution)
        return resolution

    def _find_conflict(self, conflict_id: str) -> SourceConflict:
        for c in self._conflicts:
            if c.conflict_id == conflict_id:
                return c
        raise ConflictError(f"unknown conflict {conflict_id!r}")

    def current_resolution(self, conflict_id: str) -> Optional[ConflictResolution]:
        """The most recent resolution for a conflict, or None."""
        latest = None
        for r in self._resolutions:
            if r.conflict_id == conflict_id:
                latest = r  # append-only; last wins as current
        return latest

    @property
    def conflicts(self) -> Tuple[SourceConflict, ...]:
        return tuple(self._conflicts)

    @property
    def resolutions(self) -> Tuple[ConflictResolution, ...]:
        return tuple(self._resolutions)

    def unresolved_conflicts(self) -> Tuple[SourceConflict, ...]:
        """Conflicts with no resolution, or whose latest resolution is
        unresolved/not_evaluable."""
        out: List[SourceConflict] = []
        for c in self._conflicts:
            r = self.current_resolution(c.conflict_id)
            if r is None or r.outcome in (
                ResolutionOutcome.UNRESOLVED,
                ResolutionOutcome.NOT_EVALUABLE,
            ):
                out.append(c)
        return tuple(out)


# The authoritative constructor and __post_init__ captured this capability in
# their default arguments.  Remove the ordinary module attribute so callers
# cannot use a private-but-reachable token to fabricate a source revision.
del _VERIFIED
