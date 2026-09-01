"""Record and risk identity for the R2 kernel (Design 6.2, 10.1; plan R2 step 3).

Record identity
---------------
A :class:`RecordIdentity` is the stable, deterministic identity of a single
listing row under a frozen :class:`IdentityAlgorithm`.  Two records with the
same digest under the same algorithm are the same record.  When a row maps
to more than one candidate identity (or no identity), the result is an
:class:`AmbiguousIdentity` which must block baseline eligibility.

Risk identity
-------------
A :class:`RiskIdentity` is the stable identity of a clinical risk (Design
10.1).  Risks are append-only: identity is never overwritten.  Merge/split
produce *new* identities that reference the originals; the originals remain
queryable.  This module owns the identity *values* only -- the lifecycle
state machine (established/superseded/...) is Batch B.

All identities are content-addressed (SHA-256 of canonical JSON) and carry
their identity-algorithm digest so reproducibility is one-hop verifiable.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    IdentityAlgorithm,
    content_hash,
    deep_freeze_json,
    now_iso,
    validate_sha256_hex,
)

# Identity authorities use a module-local token captured into the validators
# and factories below.  It is deleted from the module namespace at EOF so a
# caller cannot retrieve it as an ordinary attribute and bless direct input.
_IDENTITY_VERIFIED = object()

__all__ = [
    "IdentityAmbiguityError",
    "RecordIdentity",
    "AmbiguousIdentity",
    "IdentityResolution",
    "RiskIdentity",
    "ResolvedRiskIdentity",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class IdentityAmbiguityError(DomainValidationError):
    """Record/risk identity ambiguity that blocks baseline eligibility."""


# ---------------------------------------------------------------------------
# Record identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecordIdentity:
    """Stable identity of one listing row under a frozen identity algorithm.

    ``digest`` is the content hash of the key fields under the algorithm
    digest; ``algorithm_digest`` binds it to a specific IdentityAlgorithm so
    two digests are only comparable when the algorithms match.
    """

    record_id: str
    project_id: str
    algorithm_digest: str
    key_fields: Tuple[Tuple[str, Any], ...]
    digest: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None,
        _authority_token: Any = _IDENTITY_VERIFIED,
    ) -> None:
        if not self.project_id:
            raise DomainValidationError("RecordIdentity.project_id is required")
        if not self.algorithm_digest:
            raise DomainValidationError(
                "RecordIdentity.algorithm_digest is required"
            )
        if _verified is not _authority_token:
            raise DomainValidationError(
                "RecordIdentity requires a verified algorithm binding; use "
                "RecordIdentity.from_verified(...) or make_record_identity(...)"
            )
        object.__setattr__(self, "key_fields", deep_freeze_json(self.key_fields))
        expected = self.compute_digest()
        if self.digest and self.digest != expected:
            raise DomainValidationError(
                f"RecordIdentity.digest mismatch: declared {self.digest!r} "
                f"!= recomputed {expected!r}"
            )
        object.__setattr__(self, "digest", expected)
        derived_id = f"rec-{expected}"
        if not self.record_id:
            object.__setattr__(self, "record_id", derived_id)
        elif self.record_id != derived_id:
            raise DomainValidationError(
                f"RecordIdentity.record_id {self.record_id!r} does not match "
                f"the deterministic digest-derived id {derived_id!r}"
            )

    @classmethod
    def from_verified(
        cls,
        project_id: str,
        algorithm: IdentityAlgorithm,
        key_fields: Dict[str, Any],
        _authority_token: Any = _IDENTITY_VERIFIED,
    ) -> "RecordIdentity":
        """Authoritative record identity bound to a real IdentityAlgorithm.

        ``key_fields`` are deep-frozen internally; the digest is computed
        from the actual fields under the algorithm's digest.  No arbitrary
        digest/id may be supplied.
        """
        return cls(
            record_id="",
            project_id=project_id,
            algorithm_digest=algorithm.digest,
            key_fields=tuple(sorted(key_fields.items())),
            _verified=_authority_token,
        )
    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "algorithm_digest": self.algorithm_digest,
            "key_fields": dict(self.key_fields),
        }

    def compute_digest(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
class AmbiguousIdentity:
    """A row that resolved to multiple candidate identities or to none.

    ``kind`` is ``multi`` (several candidates) or ``none`` (unresolvable).
    Either kind blocks baseline eligibility (Design 6.2).
    """

    kind: str
    project_id: str
    algorithm_digest: str
    candidate_digests: Tuple[str, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("multi", "none"):
            raise DomainValidationError(
                f"AmbiguousIdentity.kind must be 'multi' or 'none', got {self.kind!r}"
            )
        if not self.project_id:
            raise DomainValidationError("AmbiguousIdentity.project_id is required")
        if not self.algorithm_digest:
            raise DomainValidationError(
                "AmbiguousIdentity.algorithm_digest is required"
            )
        # Canonicalize candidate_digests: copy to a tuple, keep only
        # unique values, sort for determinism, and validate each is a
        # canonical 64-char lowercase hex digest.
        raw = tuple(self.candidate_digests)
        seen = []
        for cd in sorted(raw):
            validate_sha256_hex(cd, "AmbiguousIdentity.candidate_digests")
            if cd not in seen:
                seen.append(cd)
        object.__setattr__(self, "candidate_digests", tuple(seen))
        if self.kind == "multi" and len(self.candidate_digests) < 2:
            raise DomainValidationError(
                "AmbiguousIdentity kind 'multi' requires >=2 unique candidate_digests"
            )
        if not self.reason:
            raise DomainValidationError("AmbiguousIdentity.reason is required")


@dataclass(frozen=True)
class IdentityResolution:
    """Outcome of resolving a set of rows under one identity algorithm.

    Carries the resolved identities plus any ambiguities.  ``is_clean`` is
    True only when there are zero ambiguities -- the property the snapshot
    acceptance chain consults.

    The ``resolved`` and ``ambiguities`` collections are defensively copied
    to tuples at construction and every resolved identity / ambiguity is
    validated against this resolution's algorithm digest and project:
    a resolution can only aggregate identities resolved under the same
    algorithm for the same project, so a caller cannot mix projects or
    algorithms and silently change ``is_clean``.
    """

    algorithm: IdentityAlgorithm
    resolved: Tuple[RecordIdentity, ...] = ()
    ambiguities: Tuple[AmbiguousIdentity, ...] = ()

    def __post_init__(self) -> None:
        if self.algorithm is None:
            raise DomainValidationError(
                "IdentityResolution.algorithm is required"
            )
        alg_digest = self.algorithm.digest
        resolved = tuple(self.resolved)
        ambiguities = tuple(self.ambiguities)
        object.__setattr__(self, "resolved", resolved)
        object.__setattr__(self, "ambiguities", ambiguities)
        for r in resolved:
            if r.algorithm_digest != alg_digest:
                raise DomainValidationError(
                    "IdentityResolution resolved RecordIdentity algorithm "
                    "digest does not match the resolution algorithm"
                )
        for a in ambiguities:
            if a.algorithm_digest != alg_digest:
                raise DomainValidationError(
                    "IdentityResolution AmbiguousIdentity algorithm digest "
                    "does not match the resolution algorithm"
                )
        # Project consistency: every resolved identity and ambiguity must
        # belong to the same project.
        projects = {r.project_id for r in resolved} | {a.project_id for a in ambiguities}
        if len(projects) > 1:
            raise DomainValidationError(
                "IdentityResolution mixes projects: "
                f"{sorted(projects)} (all resolved/ambiguities must share "
                "one project)"
            )

    @property
    def is_clean(self) -> bool:
        return len(self.ambiguities) == 0

    @property
    def algorithm_digest(self) -> str:
        return self.algorithm.digest


# ---------------------------------------------------------------------------
# Risk identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskIdentity:
    """Stable risk identity (Design 10.1).

    Risk identity is content-addressed over the identity dimensions
    (subject, domain, scope, classifier).  Merges and splits create new
    identities whose ``derived_from`` references the originals; the
    originals are never mutated or deleted.
    """

    risk_identity_id: str
    project_id: str
    subject_ref: str
    domain: str            # ae | mh | cm | ip | lab | visit | efficacy | ...
    scope: Tuple[str, ...] = ()
    classifier: str = ""
    derived_from: Tuple[str, ...] = ()   # parent risk_identity_ids for merge/split (sorted)
    created_at: str = ""
    digest: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None,
        _authority_token: Any = _IDENTITY_VERIFIED,
    ) -> None:
        if not self.project_id:
            raise DomainValidationError("RiskIdentity.project_id is required")
        if not self.subject_ref:
            raise DomainValidationError("RiskIdentity.subject_ref is required")
        if not self.domain:
            raise DomainValidationError("RiskIdentity.domain is required")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "RiskIdentity requires verified construction; use "
                "make_risk_identity(...) or RiskIdentity.from_dimensions(...)"
            )
        # Canonicalize lineage: derived_from is a set, so sort it so repeated
        # factory calls cannot drift due only to parent ordering.
        object.__setattr__(self, "scope", deep_freeze_json(self.scope))
        if self.derived_from:
            object.__setattr__(
                self, "derived_from", tuple(sorted(self.derived_from))
            )
        expected = self.compute_digest()
        if self.digest and self.digest != expected:
            raise DomainValidationError(
                f"RiskIdentity.digest mismatch: declared {self.digest!r} "
                f"!= recomputed {expected!r}"
            )
        object.__setattr__(self, "digest", expected)
        derived_id = f"risk-id-{expected}"
        if not self.risk_identity_id:
            object.__setattr__(self, "risk_identity_id", derived_id)
        elif self.risk_identity_id != derived_id:
            raise DomainValidationError(
                f"RiskIdentity.risk_identity_id {self.risk_identity_id!r} "
                f"does not match the deterministic digest-derived id "
                f"{derived_id!r}"
            )

    @classmethod
    def from_dimensions(
        cls,
        project_id: str,
        subject_ref: str,
        domain: str,
        scope: Optional[List[str]] = None,
        classifier: str = "",
        derived_from: Optional[List[str]] = None,
        created_at: str = "",
        _authority_token: Any = _IDENTITY_VERIFIED,
    ) -> "RiskIdentity":
        """Authoritative risk identity constructed from its stable dimensions."""
        return cls(
            risk_identity_id="",
            project_id=project_id,
            subject_ref=subject_ref,
            domain=domain,
            scope=tuple(scope or ()),
            classifier=classifier,
            derived_from=tuple(derived_from or ()),
            created_at=created_at,
            _verified=_authority_token,
        )

    def canonical_payload(self) -> Dict[str, Any]:
        # derived_from is part of the content address so a merge/split-derived
        # identity cannot collapse onto an existing identity with the same
        # dimensions.
        return {
            "project_id": self.project_id,
            "subject_ref": self.subject_ref,
            "domain": self.domain,
            "scope": sorted(self.scope),
            "classifier": self.classifier,
            "derived_from": list(self.derived_from),
        }

    def compute_digest(self) -> str:
        return content_hash(self.canonical_payload())

    @property
    def is_derived(self) -> bool:
        return len(self.derived_from) > 0


@dataclass(frozen=True)
class ResolvedRiskIdentity:
    """A risk identity plus its resolution context (clean vs ambiguous).

    Batch A only provides the identity *value* and a clean/ambiguous flag;
    the lifecycle state machine (established/superseded/not_evaluable) is
    owned by Batch B.
    """

    identity: RiskIdentity
    is_ambiguous: bool = False
    ambiguity_reason: str = ""
    resolved_at: str = ""

    def __post_init__(self) -> None:
        if self.is_ambiguous and not self.ambiguity_reason:
            raise DomainValidationError(
                "ResolvedRiskIdentity.is_ambiguous requires ambiguity_reason"
            )


# ---------------------------------------------------------------------------
# Factory helpers (stable for worker_02 consumption)
# ---------------------------------------------------------------------------

def make_record_identity(
    project_id: str,
    algorithm: IdentityAlgorithm,
    key_fields: Dict[str, Any],
) -> RecordIdentity:
    """Construct a RecordIdentity with a deterministic id under ``algorithm``.

    The public ``record_id`` is derived from the content digest so the same
    (project, algorithm, key_fields) always yields the same stable id; no
    fresh UUID is used.
    """
    return RecordIdentity.from_verified(
        project_id=project_id,
        algorithm=algorithm,
        key_fields=key_fields,
    )

def make_risk_identity(
    project_id: str,
    subject_ref: str,
    domain: str,
    scope: Optional[List[str]] = None,
    classifier: str = "",
    derived_from: Optional[List[str]] = None,
) -> RiskIdentity:
    """Construct a RiskIdentity with a deterministic id.

    The public ``risk_identity_id`` is derived from the content digest (which
    includes ``derived_from``) so the same dimensions always yield the same
    stable id; no fresh UUID is used.
    """
    return RiskIdentity.from_dimensions(
        project_id=project_id,
        subject_ref=subject_ref,
        domain=domain,
        scope=list(scope or ()),
        classifier=classifier,
        derived_from=list(derived_from or ()),
        created_at=now_iso(),
    )


# Replace build-time methods with closure-backed public methods whose
# signatures/defaults do not expose the construction capability.
def _seal_identity_authority(authority_token: Any) -> None:
    record_post = RecordIdentity.__post_init__
    record_factory = RecordIdentity.from_verified.__func__
    risk_post = RiskIdentity.__post_init__
    risk_factory = RiskIdentity.from_dimensions.__func__

    def checked_record_post(self, _verified: Any = None) -> None:
        return record_post(self, _verified, authority_token)

    def checked_record_factory(
        cls, project_id: str, algorithm: IdentityAlgorithm,
        key_fields: Dict[str, Any],
    ) -> "RecordIdentity":
        return record_factory(
            cls, project_id, algorithm, key_fields,
            _authority_token=authority_token,
        )

    def checked_risk_post(self, _verified: Any = None) -> None:
        return risk_post(self, _verified, authority_token)

    def checked_risk_factory(
        cls, project_id: str, subject_ref: str, domain: str,
        scope: Optional[List[str]] = None, classifier: str = "",
        derived_from: Optional[List[str]] = None, created_at: str = "",
    ) -> "RiskIdentity":
        return risk_factory(
            cls, project_id, subject_ref, domain, scope, classifier,
            derived_from, created_at, _authority_token=authority_token,
        )

    RecordIdentity.__post_init__ = checked_record_post
    RecordIdentity.from_verified = classmethod(checked_record_factory)
    RiskIdentity.__post_init__ = checked_risk_post
    RiskIdentity.from_dimensions = classmethod(checked_risk_factory)


_seal_identity_authority(_IDENTITY_VERIFIED)
del _seal_identity_authority
del _IDENTITY_VERIFIED
