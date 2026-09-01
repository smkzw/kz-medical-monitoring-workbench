"""R3-B stable record identity.

A record identity is a stable, deterministic digest over a row's *identity
key fields* under a frozen :class:`IdentityAlgorithm`.  The identity is stable
under:

* row (record) ordering -- digest is order-independent over the row set;
* column (field) ordering -- key fields are sorted before hashing;
* display-only changes -- whitespace trim + case-fold on string keys, so
  ``"S001"`` and ``" s001 "`` share an identity;

but it does **not** collapse genuinely distinct records or ambiguous partial
identities (Design: record identity 稳定 under 行顺序/列顺序/显示格式变化；
真正内容/键变化产生可解释新身份或歧义，不误合并).

This module is R3-native: it does not import the frozen R2 package.  The
contract is compatible in spirit with R2's ``RecordIdentity``/
``IdentityResolution`` but lives in its own namespace with its own schemas.
"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .normalization import is_missing, normalize_value
from .primitives import (
    canonical_json,
    content_hash,
    deep_freeze_json,
    new_id,
    validate_nonempty_str,
    validate_sha256_hex,
)
from .schema_registry import default_registry

__all__ = [
    "IdentityAlgorithm",
    "RecordIdentity",
    "AmbiguousIdentity",
    "IdentityResolution",
    "IdentityAmbiguityKind",
    "resolve_rows",
    "make_record_identity",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class IdentityError(Exception):
    """Record identity violation."""


# ---------------------------------------------------------------------------
# IdentityAlgorithm (frozen, content-addressed)
# ---------------------------------------------------------------------------

#: Allowed key-normalization modes.  These control how key-field *strings*
#: are canonicalized before hashing, so that display-only differences do not
#: invent new identities.
KEY_NORMALIZE_MODES: Tuple[str, ...] = (
    "strict",       # no canonicalization; bytes-exact
    "display",      # trim whitespace + case-fold (default for stability)
    "display_keep_case",  # trim whitespace only
)


class IdentityAlgorithm:
    """A frozen, content-addressed record-identity algorithm.

    An algorithm is defined by:

    * ``name`` -- a human-readable discriminator (e.g. ``"subject_ae"``);
    * ``key_fields`` -- the ordered list of field names that constitute the
      identity key (order is *declarative* only; the digest sorts keys so
      column-order changes do not change the identity);
    * ``key_normalize`` -- how string key values are canonicalized before
      hashing (default ``display``: trim + case-fold, so display-only changes
      are stable).

    The ``digest`` binds an identity to one algorithm instance; two records'
    digests are only comparable when their ``algorithm_digest`` matches.
    """

    __slots__ = ("_name", "_key_fields", "_key_normalize", "_digest")

    def __init__(
        self,
        name: str,
        key_fields: Sequence[str],
        *,
        key_normalize: str = "display",
    ) -> None:
        validate_nonempty_str(name, "IdentityAlgorithm.name")
        if not key_fields:
            raise IdentityError("IdentityAlgorithm.key_fields must be non-empty")
        for kf in key_fields:
            if not isinstance(kf, str) or not kf.strip():
                raise IdentityError(
                    "IdentityAlgorithm.key_fields must be non-empty strings"
                )
        if key_normalize not in KEY_NORMALIZE_MODES:
            raise IdentityError(
                f"key_normalize={key_normalize!r} not in {KEY_NORMALIZE_MODES}"
            )
        # de-duplicate field names while preserving declared order
        seen: List[str] = []
        for kf in key_fields:
            if kf not in seen:
                seen.append(kf)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_key_fields", tuple(seen))
        object.__setattr__(self, "_key_normalize", key_normalize)
        object.__setattr__(self, "_digest", self._compute_digest())

    # __setattr__ / __delattr__ frozen
    def __setattr__(self, key: str, value: Any) -> None:
        raise IdentityError("IdentityAlgorithm is frozen")

    def __delattr__(self, key: str) -> None:
        raise IdentityError("IdentityAlgorithm is frozen")

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, IdentityAlgorithm) and self.digest == other.digest

    def __hash__(self) -> int:
        return hash(self.digest)

    def __repr__(self) -> str:
        return (
            f"IdentityAlgorithm(name={self._name!r}, "
            f"key_fields={self._key_fields!r}, "
            f"key_normalize={self._key_normalize!r}, "
            f"digest={self._digest[:12]}...)"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def key_fields(self) -> Tuple[str, ...]:
        return self._key_fields

    @property
    def key_normalize(self) -> str:
        return self._key_normalize

    @property
    def digest(self) -> str:
        return self._digest

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "key_fields": list(self._key_fields),
            "key_normalize": self._key_normalize,
        }

    def _compute_digest(self) -> str:
        return content_hash(self.canonical_payload())

    # -- key canonicalization --------------------------------------------

    def canonicalize_key_value(self, value: Any) -> Any:
        """Canonicalize one key value per ``key_normalize``.

        * ``strict`` -- value unchanged (deep-frozen).
        * ``display`` -- strings are trimmed + ASCII-case-folded.
        * ``display_keep_case`` -- strings are trimmed only.

        Missing values canonicalize to ``None`` so that two missing keys do
        not invent distinct identities, but a missing vs present key stays
        distinct (``None`` != ``"x"``).
        """
        if is_missing(value):
            return None
        if self._key_normalize == "strict":
            return value
        if isinstance(value, str):
            s = value.strip()
            if self._key_normalize == "display":
                return s.casefold()
            return s
        return value


# ---------------------------------------------------------------------------
# RecordIdentity (immutable, schema-validated, digest-derived id)
# ---------------------------------------------------------------------------

class IdentityAmbiguityKind:
    MULTI = "multi"     # several candidate identities
    NONE = "none"       # unresolvable (e.g. all keys missing)


@dataclass(frozen=True)
class RecordIdentity:
    """Stable identity of one listing row under one :class:`IdentityAlgorithm`.

    ``record_id`` is derived deterministically from the digest (``rec-<digest>``)
    so callers cannot fabricate ids.  ``digest`` binds the project, frozen
    algorithm and canonical key fields.  ``source_revision_id`` remains
    lineage only: including it in the digest would make the same clinical
    record look new in every full-listing export and would break incremental
    comparison across snapshots.
    """
    schema_name: str = "r3_record_identity"
    schema_version: str = "1"
    record_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    algorithm_digest: str = ""
    key_fields: Tuple[Tuple[str, Any], ...] = ()
    digest: str = ""
    row_index: Optional[int] = None

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.project_id, "RecordIdentity.project_id")
        validate_nonempty_str(self.source_revision_id, "RecordIdentity.source_revision_id")
        validate_sha256_hex(self.algorithm_digest, "RecordIdentity.algorithm_digest")
        object.__setattr__(self, "key_fields", deep_freeze_json(self.key_fields))
        expected = self.compute_digest()
        if self.digest and self.digest != expected:
            raise IdentityError(
                f"RecordIdentity.digest mismatch: declared {self.digest!r} "
                f"!= recomputed {expected!r}"
            )
        object.__setattr__(self, "digest", expected)
        derived_id = f"rec-{expected}"
        if not self.record_id:
            object.__setattr__(self, "record_id", derived_id)
        elif self.record_id != derived_id:
            raise IdentityError(
                f"RecordIdentity.record_id {self.record_id!r} does not match "
                f"the deterministic digest-derived id {derived_id!r}"
            )

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "algorithm_digest": self.algorithm_digest,
            "key_fields": dict(self.key_fields),
        }

    def compute_digest(self) -> str:
        return content_hash(self.canonical_payload())

    @property
    def key_field_names(self) -> Tuple[str, ...]:
        return tuple(k for k, _ in self.key_fields)


@dataclass(frozen=True)
class AmbiguousIdentity:
    """A row that resolved to multiple candidate identities or to none.

    ``kind`` is ``multi`` (several candidates) or ``none`` (unresolvable).
    Either blocks baseline eligibility (Design 6.2; identity ambiguity blocks).
    """
    kind: str
    project_id: str
    source_revision_id: str = ""
    algorithm_digest: str = ""
    candidate_digests: Tuple[str, ...] = ()
    reason: str = ""
    row_index: Optional[int] = None

    def __post_init__(self) -> None:
        if self.kind not in (IdentityAmbiguityKind.MULTI, IdentityAmbiguityKind.NONE):
            raise IdentityError(
                f"AmbiguousIdentity.kind must be 'multi' or 'none', got {self.kind!r}"
            )
        validate_nonempty_str(self.project_id, "AmbiguousIdentity.project_id")
        validate_nonempty_str(self.reason, "AmbiguousIdentity.reason")
        if self.algorithm_digest:
            validate_sha256_hex(
                self.algorithm_digest, "AmbiguousIdentity.algorithm_digest"
            )
        # canonicalize candidate_digests: unique + sorted + validated
        raw = tuple(self.candidate_digests)
        seen: List[str] = []
        for cd in sorted(raw):
            validate_sha256_hex(cd, "AmbiguousIdentity.candidate_digests")
            if cd not in seen:
                seen.append(cd)
        object.__setattr__(self, "candidate_digests", tuple(seen))
        if self.kind == IdentityAmbiguityKind.MULTI and len(self.candidate_digests) < 2:
            raise IdentityError(
                "AmbiguousIdentity kind 'multi' requires >=2 unique candidate_digests"
            )


@dataclass(frozen=True)
class IdentityResolution:
    """Outcome of resolving a set of rows under one :class:`IdentityAlgorithm`.

    Carries resolved identities plus ambiguities.  ``is_clean`` is True only
    when there are zero ambiguities -- the property downstream baseline
    eligibility consults (Design: identity ambiguity blocks baseline).
    """
    schema_name: str = "r3_identity_resolution"
    schema_version: str = "1"
    algorithm: IdentityAlgorithm = None  # type: ignore[assignment]
    project_id: str = ""
    source_revision_id: str = ""
    resolved: Tuple[RecordIdentity, ...] = ()
    ambiguities: Tuple[AmbiguousIdentity, ...] = ()

    def __post_init__(self) -> None:
        _validate_schema(self)
        if self.algorithm is None:
            raise IdentityError("IdentityResolution.algorithm is required")
        alg_digest = self.algorithm.digest
        resolved = tuple(self.resolved)
        ambiguities = tuple(self.ambiguities)
        object.__setattr__(self, "resolved", resolved)
        object.__setattr__(self, "ambiguities", ambiguities)
        for r in resolved:
            if r.algorithm_digest != alg_digest:
                raise IdentityError(
                    "IdentityResolution resolved RecordIdentity algorithm "
                    "digest does not match the resolution algorithm"
                )
            if r.project_id != self.project_id:
                raise IdentityError(
                    "IdentityResolution resolved RecordIdentity project_id "
                    "does not match the resolution project_id"
                )
            if r.source_revision_id != self.source_revision_id:
                raise IdentityError(
                    "IdentityResolution resolved RecordIdentity source_revision_id "
                    "does not match the resolution source_revision_id"
                )
        for a in ambiguities:
            if a.algorithm_digest and a.algorithm_digest != alg_digest:
                raise IdentityError(
                    "IdentityResolution AmbiguousIdentity algorithm digest "
                    "does not match the resolution algorithm"
                )
            if a.project_id != self.project_id:
                raise IdentityError(
                    "IdentityResolution AmbiguousIdentity project_id does "
                    "not match the resolution project_id"
                )
            if a.source_revision_id != self.source_revision_id:
                raise IdentityError(
                    "IdentityResolution AmbiguousIdentity source_revision_id "
                    "does not match the resolution source_revision_id"
                )

    @property
    def is_clean(self) -> bool:
        """True iff there are zero ambiguities."""
        return len(self.ambiguities) == 0

    @property
    def algorithm_digest(self) -> str:
        return self.algorithm.digest  # type: ignore[union-attr]

    @property
    def has_duplicates(self) -> bool:
        """True iff two resolved rows share the same digest (duplicate keys)."""
        digests = [r.digest for r in self.resolved]
        return len(set(digests)) != len(digests)

    def duplicate_groups(self) -> Tuple[Tuple[RecordIdentity, ...], ...]:
        """Groups of resolved identities that share a digest (size >= 2)."""
        by_digest: Dict[str, List[RecordIdentity]] = {}
        for r in self.resolved:
            by_digest.setdefault(r.digest, []).append(r)
        return tuple(
            tuple(g) for g in by_digest.values() if len(g) >= 2
        )


# ---------------------------------------------------------------------------
# Row resolution
# ---------------------------------------------------------------------------

def _row_key_payload(
    row: Mapping[str, Any],
    algorithm: IdentityAlgorithm,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Build the canonical key payload for one row.

    Returns ``(payload, missing_key_fields)``.  ``payload`` is None when *all*
    key fields are missing (unresolvable -> ``none`` ambiguity).  Otherwise it
    is the canonical dict of key-field -> canonicalized value.
    """
    canonical: Dict[str, Any] = {}
    missing: List[str] = []
    for kf in algorithm.key_fields:
        raw = row.get(kf)
        canon = algorithm.canonicalize_key_value(raw)
        if canon is None:
            missing.append(kf)
        canonical[kf] = canon
    if not canonical or all(v is None for v in canonical.values()):
        return None, missing
    return canonical, missing


def resolve_rows(
    project_id: str,
    source_revision_id: str,
    algorithm: IdentityAlgorithm,
    rows: Sequence[Mapping[str, Any]],
    *,
    partial_keys_allowed: bool = False,
) -> IdentityResolution:
    """Resolve a sequence of rows into identities + ambiguities.

    * **Order independence**: the per-row digest does not depend on row order.
      Two row sets with the same content but different order yield the same
      set of identities; ``row_index`` is retained only as source lineage.
    * **Column-order independence**: the key payload is built from named fields;
      a row is a mapping, so column order is irrelevant.
    * **Display-only stability**: string keys are canonicalized per the
      algorithm's ``key_normalize`` (default trim+casefold).
    * **Ambiguity surfacing**: a row whose keys are *all* missing is a ``none``
      ambiguity; when ``partial_keys_allowed`` is False, a row with *some*
      missing keys is a ``none`` ambiguity (partial identities are not silently
      accepted -- Design: 不误合并).
    * **Duplicate detection**: duplicate key digests within the same source are
      *surfaced* via :meth:`IdentityResolution.has_duplicates`/
      :meth:`IdentityResolution.duplicate_groups` but do not raise -- the
      caller decides whether duplicates block baseline (they typically do).

    ``rows`` may be plain dicts; each row *should* carry an ``"_row_index"``
    int, otherwise the enumeration index is used.
    """
    validate_nonempty_str(project_id, "resolve_rows.project_id")
    validate_nonempty_str(source_revision_id, "resolve_rows.source_revision_id")
    if algorithm is None:
        raise IdentityError("resolve_rows requires an IdentityAlgorithm")
    if not rows:
        return IdentityResolution(
            algorithm=algorithm,
            project_id=project_id,
            source_revision_id=source_revision_id,
        )

    resolved: List[RecordIdentity] = []
    ambiguities: List[AmbiguousIdentity] = []
    for i, row in enumerate(rows):
        idx = row.get("_row_index", i) if isinstance(row, Mapping) else i
        if not isinstance(idx, int) or isinstance(idx, bool) or idx < 0:
            raise IdentityError(
                "row _row_index must be a non-negative integer"
            )
        payload, missing = _row_key_payload(row, algorithm)
        if payload is None:
            ambiguities.append(AmbiguousIdentity(
                kind=IdentityAmbiguityKind.NONE,
                project_id=project_id,
                source_revision_id=source_revision_id,
                algorithm_digest=algorithm.digest,
                reason=f"all identity key fields missing: {sorted(algorithm.key_fields)}",
                row_index=idx,
            ))
            continue
        if missing and not partial_keys_allowed:
            ambiguities.append(AmbiguousIdentity(
                kind=IdentityAmbiguityKind.NONE,
                project_id=project_id,
                source_revision_id=source_revision_id,
                algorithm_digest=algorithm.digest,
                reason=f"partial identity keys missing: {sorted(missing)}",
                row_index=idx,
            ))
            continue
        ri = RecordIdentity(
            project_id=project_id,
            source_revision_id=source_revision_id,
            algorithm_digest=algorithm.digest,
            key_fields=tuple(sorted(payload.items())),
            row_index=idx,
        )
        resolved.append(ri)

    return IdentityResolution(
        algorithm=algorithm,
        project_id=project_id,
        source_revision_id=source_revision_id,
        resolved=tuple(resolved),
        ambiguities=tuple(ambiguities),
    )


def make_record_identity(
    project_id: str,
    source_revision_id: str,
    algorithm: IdentityAlgorithm,
    key_fields: Mapping[str, Any],
) -> RecordIdentity:
    """Construct a single :class:`RecordIdentity` for direct/test use."""
    canonical = {
        kf: algorithm.canonicalize_key_value(key_fields.get(kf))
        for kf in algorithm.key_fields
    }
    return RecordIdentity(
        project_id=project_id,
        source_revision_id=source_revision_id,
        algorithm_digest=algorithm.digest,
        key_fields=tuple(sorted(canonical.items())),
    )
