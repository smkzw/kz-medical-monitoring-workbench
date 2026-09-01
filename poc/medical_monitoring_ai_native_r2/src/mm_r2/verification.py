"""Verified rehydration adapter for the R2 kernel (Batch C; Design v1.1 section 12).

Batch A deliberately provides **no** digest-only rehydration path for
authoritative / content-addressed entities (``SourceRevision``,
``ListingSnapshot``, ``MappingResult``, ``CanonicalFact``,
``RecordIdentity``, ``RiskIdentity``).  Reconstructing one from arbitrary
serialized data would trust a caller-chosen digest -- a public
trust-escalation hole.

This module is the single permitted rehydration path.  It reconstructs an
authoritative object **only after verifying the actual stored artifact
bytes** against the content hash the object claims, then rebuilds it via
the real public factory (``from_bytes`` / ``from_content`` / ``from_verified``
/ ``from_bundle`` / ``make_*``).  A caller cannot forge a hash: the
:class:`~mm_r2.artifacts.ArtifactStore` recomputes SHA-256 on read and a
mismatch is a :class:`~mm_r2.domain.HashMismatchError`.

Non-authoritative entities (plain dataclasses without ``_verified``)
round-trip normally through :func:`~mm_r2.domain.to_dictable` /
:func:`~mm_r2.domain.from_dictable`.

Security note (out of scope): hashes here are functional data-integrity /
recovery mechanisms, not a security control.  Adversarial tamper resistance
is explicitly excluded from this batch per user directive.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    CanonicalFact,
    DomainValidationError,
    HashMismatchError,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    MmR2Error,
    ProvenanceError,
    SourceRevision,
    StudyProject,
    canonical_json,
    content_hash,
    from_dictable,
    sha256_hex,
    to_dictable,
    validate_sha256_hex,
)
from .identity import (
    IdentityResolution,
    RecordIdentity,
    RiskIdentity,
    make_record_identity,
    make_risk_identity,
)

__all__ = [
    "RehydrationError",
    "Rehydrator",
    "verify_artifact_bytes",
]


class RehydrationError(MmR2Error):
    """A verified rehydration failed: missing bytes, hash mismatch, or an
    inconsistent reconstructed object."""


# ---------------------------------------------------------------------------
# Low-level byte/hash verification
# ---------------------------------------------------------------------------

def verify_artifact_bytes(
    stored_bytes: Optional[bytes],
    expected_hash: str,
    *,
    field_name: str = "content_hash",
) -> bytes:
    """Return ``stored_bytes`` only if its SHA-256 equals ``expected_hash``.

    Raises :class:`RehydrationError` if bytes are missing, and
    :class:`HashMismatchError` if the recomputed hash differs.  The
    expected hash is validated to be a canonical 64-char lowercase hex
    digest first so a malformed serialized hash cannot silently pass.
    """
    validate_sha256_hex(expected_hash, field_name)
    if stored_bytes is None:
        raise RehydrationError(
            f"cannot rehydrate: artifact bytes for {field_name}={expected_hash!r} "
            f"are missing"
        )
    if not isinstance(stored_bytes, (bytes, bytearray)):
        raise RehydrationError(
            f"cannot rehydrate: stored payload for {field_name} is not bytes"
        )
    actual = sha256_hex(stored_bytes)
    if actual != expected_hash:
        raise HashMismatchError(
            f"rehydration hash mismatch for {field_name}: recomputed "
            f"{actual!r} != expected {expected_hash!r}"
        )
    return bytes(stored_bytes)


# ---------------------------------------------------------------------------
# Rehydrator
# ---------------------------------------------------------------------------

class Rehydrator:
    """Rebuild authoritative R2 entities from verified stored data.

    Every ``rehydrate_*`` method takes the serialized dict form (produced by
    :func:`to_dictable`) PLUS the raw stored artifact bytes + their claimed
    content hash.  It verifies the bytes first, then reconstructs the
    authoritative object via the real public factory.  A mismatched or
    missing byte payload fails closed.

    The rehydrator holds an :class:`~mm_r2.artifacts.ArtifactStore`
    reference so callers can rehydrate by content hash alone (the store
    reads + verifies the bytes).  Callers may also pass raw bytes directly
    when they already hold them (e.g. from a migration archive).
    """

    def __init__(self, artifact_store: Any = None) -> None:
        self._store = artifact_store

    # -- byte retrieval ----------------------------------------------------

    def _bytes_for(self, content_hash_value: str, *, explicit: Optional[bytes] = None,
                   field_name: str = "content_hash") -> bytes:
        """Resolve and verify the bytes for one content hash.

        Explicit bytes (caller-held, e.g. from a migration archive) take
        precedence; otherwise the artifact store is consulted.  Either way
        the hash is verified.
        """
        if explicit is not None:
            return verify_artifact_bytes(explicit, content_hash_value,
                                         field_name=field_name)
        if self._store is None:
            raise RehydrationError(
                f"cannot rehydrate {field_name}={content_hash_value!r}: no "
                f"artifact store and no explicit bytes"
            )
        # The store recomputes + verifies on read.
        data = self._store.get(content_hash_value)
        # Defensive double-check: the store already verifies, but an explicit
        # verify here keeps this method correct independent of store internals.
        return verify_artifact_bytes(data, content_hash_value, field_name=field_name)

    # -- SourceRevision ----------------------------------------------------

    def rehydrate_source_revision(
        self,
        data: Dict[str, Any],
        *,
        source_bytes: Optional[bytes] = None,
    ) -> SourceRevision:
        """Rebuild a :class:`SourceRevision` from verified source bytes.

        ``data`` is the :func:`to_dictable` dict form.  ``source_bytes`` is
        the raw immutable source content; if omitted, the artifact store is
        consulted using ``data['content_digest']``.
        """
        if data.get("__r2_dataclass__") != "SourceRevision":
            raise RehydrationError("payload is not a SourceRevision dict")
        f = data.get("fields", {})
        content_digest = f.get("content_digest", "")
        validate_sha256_hex(content_digest, "SourceRevision.content_digest")
        verified_bytes = self._bytes_for(
            content_digest, explicit=source_bytes,
            field_name="SourceRevision.content_digest",
        )
        scope = _tuple_of_tuples(f.get("scope"))
        return SourceRevision.from_bytes(
            revision_id=f["revision_id"],
            project_id=f["project_id"],
            source_type=f["source_type"],
            version=f["version"],
            source_bytes=verified_bytes,
            scope=scope,
            valid_from=f.get("valid_from"),
            created_at=f.get("created_at", ""),
        )

    # -- ListingSnapshot ---------------------------------------------------

    def rehydrate_listing_snapshot(
        self,
        data: Dict[str, Any],
        *,
        snapshot_rows: Optional[Any] = None,
        snapshot_bytes: Optional[bytes] = None,
    ) -> ListingSnapshot:
        """Rebuild a :class:`ListingSnapshot` from verified full-listing content.

        The caller may supply either ``snapshot_rows`` (the original row
        structure) or ``snapshot_bytes`` (the canonical JSON of those rows).
        If neither is supplied, the artifact store is consulted using
        ``data['content_digest']``.  The recomputed digest of the supplied
        content must equal the snapshot's ``content_digest``.
        """
        if data.get("__r2_dataclass__") != "ListingSnapshot":
            raise RehydrationError("payload is not a ListingSnapshot dict")
        f = data.get("fields", {})
        content_digest = f.get("content_digest", "")
        validate_sha256_hex(content_digest, "ListingSnapshot.content_digest")

        if snapshot_rows is not None:
            # Recompute the canonical digest of the rows and verify.
            recomputed = content_hash(_json_freeze(snapshot_rows))
            if recomputed != content_digest:
                raise HashMismatchError(
                    f"ListingSnapshot rehydration: recomputed row digest "
                    f"{recomputed!r} != declared {content_digest!r}"
                )
            rows = snapshot_rows
        elif snapshot_bytes is not None:
            verified = verify_artifact_bytes(
                snapshot_bytes, content_digest,
                field_name="ListingSnapshot.content_digest",
            )
            rows = json.loads(verified.decode("utf-8"))
        else:
            verified = self._bytes_for(
                content_digest, field_name="ListingSnapshot.content_digest",
            )
            rows = json.loads(verified.decode("utf-8"))

        structure = _tuple_of_tuples(f.get("structure"))
        return ListingSnapshot.from_content(
            snapshot_id=f["snapshot_id"],
            project_id=f["project_id"],
            revision_id=f["revision_id"],
            snapshot_version=f["snapshot_version"],
            rows=rows,
            structure=structure,
            is_synthetic=bool(f.get("is_synthetic", True)),
            created_at=f.get("created_at", ""),
        )

    # -- MappingResult -----------------------------------------------------

    def rehydrate_mapping_result(
        self,
        data: Dict[str, Any],
        mapping: MappingDefinition,
        snapshot: ListingSnapshot,
        identity_algorithm: IdentityAlgorithm,
    ) -> MappingResult:
        """Rebuild a :class:`MappingResult` bound to real verified objects.

        ``MappingResult`` does not carry independent content bytes; its
        authority is the verified (snapshot, mapping, identity_algorithm)
        triple.  Rehydration re-binds that triple via the real
        :meth:`MappingResult.from_verified` factory, which re-derives the
        mapping definition digest from the supplied mapping.  A caller
        cannot substitute a different mapping: the factory checks the digest.
        """
        if data.get("__r2_dataclass__") != "MappingResult":
            raise RehydrationError("payload is not a MappingResult dict")
        f = data.get("fields", {})
        # The declared mapping_definition_digest must match the real mapping.
        declared_digest = f.get("mapping_definition_digest", "")
        if declared_digest and declared_digest != mapping.digest:
            raise RehydrationError(
                "MappingResult rehydration: declared mapping_definition_digest "
                f"{declared_digest!r} does not match the supplied mapping "
                f"digest {mapping.digest!r}"
            )
        return MappingResult.from_verified(
            result_id=f["result_id"],
            project_id=f["project_id"],
            snapshot=snapshot,
            mapping=mapping,
            identity_algorithm=identity_algorithm,
            record_count=int(f.get("record_count", 0)),
            identity_digest=f.get("identity_digest", "") or "",
            is_ambiguous=bool(f.get("is_ambiguous", False)),
            ambiguity_reason=f.get("ambiguity_reason", "") or "",
            created_at=f.get("created_at", ""),
        )

    # -- RecordIdentity ----------------------------------------------------

    def rehydrate_record_identity(
        self,
        data: Dict[str, Any],
        identity_algorithm: IdentityAlgorithm,
    ) -> RecordIdentity:
        """Rebuild a :class:`RecordIdentity` under a verified identity algorithm.

        The identity digest is recomputed from the key fields under the
        algorithm's digest; a caller cannot supply an arbitrary digest.
        """
        if data.get("__r2_dataclass__") != "RecordIdentity":
            raise RehydrationError("payload is not a RecordIdentity dict")
        f = data.get("fields", {})
        project_id = f["project_id"]
        declared_digest = f.get("digest", "")
        key_fields = dict(f.get("key_fields", {}))
        ri = make_record_identity(project_id, identity_algorithm, key_fields)
        if declared_digest and ri.digest != declared_digest:
            raise RehydrationError(
                "RecordIdentity rehydration: declared digest "
                f"{declared_digest!r} != recomputed {ri.digest!r}"
            )
        return ri

    # -- RiskIdentity ------------------------------------------------------

    def rehydrate_risk_identity(self, data: Dict[str, Any]) -> RiskIdentity:
        """Rebuild a :class:`RiskIdentity` from its stable dimensions.

        The identity digest is recomputed from the dimensions; a caller
        cannot supply an arbitrary digest.
        """
        if data.get("__r2_dataclass__") != "RiskIdentity":
            raise RehydrationError("payload is not a RiskIdentity dict")
        f = data.get("fields", {})
        declared_digest = f.get("digest", "")
        ri = make_risk_identity(
            project_id=f["project_id"],
            subject_ref=f["subject_ref"],
            domain=f["domain"],
            scope=list(f.get("scope", ())) or None,
            classifier=f.get("classifier", "") or "",
            derived_from=list(f.get("derived_from", ())) or None,
        )
        if declared_digest and ri.digest != declared_digest:
            raise RehydrationError(
                "RiskIdentity rehydration: declared digest "
                f"{declared_digest!r} != recomputed {ri.digest!r}"
            )
        return ri

    # -- CanonicalFact -----------------------------------------------------

    def rehydrate_canonical_fact(
        self,
        data: Dict[str, Any],
        project: StudyProject,
        source: SourceRevision,
        snapshot: ListingSnapshot,
        record_identity: RecordIdentity,
        identity_algorithm: IdentityAlgorithm,
        mapping_definition: MappingDefinition,
        mapping_result: MappingResult,
    ) -> CanonicalFact:
        """Rebuild a :class:`CanonicalFact` from a verified reference bundle.

        The fact is re-created via :meth:`CanonicalFact.from_bundle`, which
        re-validates the full cross-project/snapshot/source/mapping
        consistency and re-derives the deterministic fact_id and content
        hash.  A caller cannot forge a fact_id or content_hash.
        """
        if data.get("__r2_dataclass__") != "CanonicalFact":
            raise RehydrationError("payload is not a CanonicalFact dict")
        f = data.get("fields", {})
        required_identity_fields = (
            "schema_name", "schema_version", "fact_id", "project_id",
            "source_revision_id", "snapshot_id", "fact_type",
            "record_identity_digest", "identity_algorithm_digest",
            "mapping_result_id", "mapping_definition_digest", "role",
            "content_hash",
        )
        missing = [name for name in required_identity_fields if not f.get(name)]
        if missing:
            raise RehydrationError(
                "CanonicalFact rehydration is missing declared identity fields: "
                f"{missing}"
            )
        rebuilt = CanonicalFact.from_bundle(
            project=project,
            source=source,
            snapshot=snapshot,
            record_identity=record_identity,
            identity_algorithm=identity_algorithm,
            mapping_definition=mapping_definition,
            mapping_result=mapping_result,
            fact_type=f["fact_type"],
            payload=_tuple_of_tuples(f.get("payload")),
            source_location=_tuple_of_tuples(f.get("source_location")),
            created_at=f.get("created_at", ""),
        )
        for field_name in required_identity_fields:
            declared = f[field_name]
            actual = getattr(rebuilt, field_name)
            if actual != declared:
                raise RehydrationError(
                    f"CanonicalFact rehydration: declared {field_name} "
                    f"{declared!r} != recomputed {actual!r}"
                )
        return rebuilt

    # -- non-authoritative passthrough ------------------------------------

    def rehydrate_plain(self, data: Any) -> Any:
        """Rehydrate a non-authoritative entity via the generic codec.

        Authoritative entities (those with a ``_verified`` InitVar) are
        rejected by :func:`from_dictable`; use the specific
        ``rehydrate_*`` methods for those.
        """
        return from_dictable(data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tuple_of_tuples(value: Any) -> Tuple[Tuple[str, Any], ...]:
    """Normalize a JSON-like mapping/list into a tuple-of-tuples for deep-freeze."""
    if value is None:
        return ()
    if isinstance(value, dict):
        return tuple(sorted((str(k), v) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_tuple_of_tuples_item(x) for x in value)
    return ()


def _tuple_of_tuples_item(value: Any) -> Tuple[str, Any]:
    if isinstance(value, dict) and len(value) == 1:
        k, v = next(iter(value.items()))
        return (str(k), v)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (str(value[0]), value[1])
    # Fall back to a single-key wrapper.
    return ("value", value)


def _json_freeze(value: Any) -> Any:
    """Canonicalize a JSON-like value for digest recomputation.

    The listing snapshot's content_digest is computed over
    ``deep_freeze_json(rows)`` then ``content_hash``.  To recompute the same
    digest we must apply the same canonicalization.  We reuse
    :func:`canonical_json` on the plain (un-frozen) rows after converting
    tuples/ImmutableDict to plain structures, which is what
    ``content_hash(frozen_rows)`` effectively does.
    """
    return to_dictable(value)
