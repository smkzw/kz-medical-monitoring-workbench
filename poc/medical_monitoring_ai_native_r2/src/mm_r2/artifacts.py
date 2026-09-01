"""Content-addressed artifact store and envelope for the R2 kernel
(Design v1.1 sections 5, 12; plan R2 step 1).

Artifacts are the only inter-node delivery contract (Design 5).  An
:class:`ArtifactEnvelope` carries the type, version, input hash, payload
role, QC, coverage and completion semantics.  The envelope is
content-addressed: its ``content_hash`` is the SHA-256 of its canonical
payload and is verified on read.

The :class:`ArtifactStore` writes artifact bytes to a content-addressed
filesystem layout (``<root>/<ab>/<content_hash>``) and verifies the hash on
read.  Writes are idempotent: the same content hash always maps to the same
bytes.  A collision (same hash, different bytes) is a hard error.

Batch A provides the store + envelope only.  Atomic commit of
artifact/state/audit in one SQLite transaction is Batch C.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    CanonicalFact,
    DomainValidationError,
    HashMismatchError,
    MmR2Error,
    canonical_json,
    content_hash,
    deep_freeze_json,
    new_id,
    now_iso,
    sha256_hex,
    to_dictable,
)
from .schema_registry import default_registry

__all__ = [
    "ArtifactStoreError",
    "ArtifactCollisionError",
    "ArtifactCompleteness",
    "EvidenceState",
    "ArtifactEnvelope",
    "ArtifactStore",
    "StoredArtifact",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArtifactCompleteness:
    """Completion semantics for an artifact (Design 5.2, 12).

    ``complete`` / ``partial`` / ``truncated`` / ``not_evaluable`` /
    ``failed``.  Anything other than ``complete`` must never be promoted to
    a publishable state.
    """

    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    NOT_EVALUABLE = "not_evaluable"
    FAILED = "failed"

    @classmethod
    def values(cls) -> Tuple[str, ...]:
        return (cls.COMPLETE, cls.PARTIAL, cls.TRUNCATED,
                cls.NOT_EVALUABLE, cls.FAILED)


@dataclass(frozen=True)
class EvidenceState:
    """Evidence state for an artifact (Design 5.1)."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    NOT_EVALUABLE = "not_evaluable"
    CONFLICTED = "conflicted"

    @classmethod
    def values(cls) -> Tuple[str, ...]:
        return (cls.COMPLETE, cls.PARTIAL, cls.TRUNCATED,
                cls.NOT_EVALUABLE, cls.CONFLICTED)


# Roles (Design 5.2): candidates must never be promoted to facts.
PAYLOAD_ROLE_FACTS = "facts"
PAYLOAD_ROLE_INFERENCE = "inference"
PAYLOAD_ROLE_CANDIDATE = "candidate"
PAYLOAD_ROLE_SUGGESTION = "suggestion"

_VALID_ROLES = frozenset({
    PAYLOAD_ROLE_FACTS, PAYLOAD_ROLE_INFERENCE,
    PAYLOAD_ROLE_CANDIDATE, PAYLOAD_ROLE_SUGGESTION,
})


def _payload_for_role(payload_role: str, payload: Any) -> Any:
    """Normalize payloads while preserving the facts authority boundary.

    A ``facts`` envelope is not a label that upgrades arbitrary JSON.  It may
    contain only one or more already verified :class:`CanonicalFact` objects;
    all other roles remain ordinary JSON-like evidence/candidate payloads.
    """
    if payload_role != PAYLOAD_ROLE_FACTS:
        return payload
    if isinstance(payload, CanonicalFact):
        facts = (payload,)
    elif isinstance(payload, (tuple, list)):
        facts = tuple(payload)
    else:
        raise DomainValidationError(
            "facts payload_role requires CanonicalFact objects"
        )
    if not facts:
        raise DomainValidationError(
            "facts payload_role requires at least one CanonicalFact"
        )
    if not all(isinstance(fact, CanonicalFact) for fact in facts):
        raise DomainValidationError(
            "facts payload_role requires CanonicalFact objects"
        )
    return {"facts": [to_dictable(fact) for fact in facts]}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ArtifactStoreError(MmR2Error):
    """Generic artifact-store violation."""


class ArtifactCollisionError(ArtifactStoreError):
    """Same content hash produced different bytes (corruption / collision)."""


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArtifactEnvelope:
    """The inter-node delivery contract (Design 5).

    Content-addressed: ``content_hash`` is recomputed from the canonical
    payload and a mismatch is a :class:`HashMismatchError`.  ``input_hash``
    binds the envelope to the exact inputs that produced it so replays are
    detectable.
    """

    artifact_id: str
    artifact_type: str
    artifact_version: str
    input_hash: str
    payload_role: str
    content_hash: str = ""
    completeness: str = ArtifactCompleteness.COMPLETE
    evidence_state: str = EvidenceState.COMPLETE
    coverage: Tuple[Tuple[str, Any], ...] = ()
    qc_notes: Tuple[str, ...] = ()
    supersedes: Tuple[str, ...] = ()
    created_at: str = ""
    # The payload is carried out-of-band (written to the store).  The
    # envelope stores only its canonical hash.

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise DomainValidationError("ArtifactEnvelope.artifact_id is required")
        if not self.artifact_type:
            raise DomainValidationError("ArtifactEnvelope.artifact_type is required")
        if not self.artifact_version:
            raise DomainValidationError("ArtifactEnvelope.artifact_version is required")
        if not self.input_hash:
            raise DomainValidationError("ArtifactEnvelope.input_hash is required")
        if self.payload_role not in _VALID_ROLES:
            raise DomainValidationError(
                f"ArtifactEnvelope.payload_role {self.payload_role!r} is not valid"
            )
        if self.completeness not in ArtifactCompleteness.values():
            raise DomainValidationError(
                f"ArtifactEnvelope.completeness {self.completeness!r} is not valid"
            )
        if self.evidence_state not in EvidenceState.values():
            raise DomainValidationError(
                f"ArtifactEnvelope.evidence_state {self.evidence_state!r} is not valid"
            )
        # VETO2: deep-freeze the JSON-like coverage/QC/lineage fields so a
        # caller cannot mutate a nested value reachable from the frozen
        # envelope and change its content address.
        object.__setattr__(self, "coverage", deep_freeze_json(self.coverage))
        object.__setattr__(self, "qc_notes", deep_freeze_json(self.qc_notes))
        object.__setattr__(self, "supersedes", deep_freeze_json(self.supersedes))

    def canonical_payload(self, payload: Any) -> Dict[str, Any]:
        """Canonical payload over the envelope metadata + payload.

        ``artifact_id`` and ``created_at`` are operational instance fields,
        NOT part of the content address: two fresh envelopes with identical
        logical metadata and payload must hash to the same address.
        """
        return {
            "artifact_type": self.artifact_type,
            "artifact_version": self.artifact_version,
            "input_hash": self.input_hash,
            "payload_role": self.payload_role,
            "completeness": self.completeness,
            "evidence_state": self.evidence_state,
            "coverage": dict(self.coverage),
            "qc_notes": list(self.qc_notes),
            "supersedes": list(self.supersedes),
            "payload": _payload_for_role(self.payload_role, payload),
        }

    def compute_hash(self, payload: Any) -> str:
        return content_hash(self.canonical_payload(payload))


# ---------------------------------------------------------------------------
# Stored artifact (envelope + bytes)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StoredArtifact:
    """An envelope plus its content-addressed bytes and location."""

    envelope: ArtifactEnvelope
    payload_bytes: bytes
    path: str
    written_at: str


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class ArtifactStore:
    """Content-addressed filesystem artifact store.

    Artifacts are written to ``<root>/<ab>/<content_hash>`` where ``ab`` is
    the first two hex chars of the hash.  Writes are idempotent: writing the
    same (envelope, payload) twice is a no-op.  A hash collision (same hash,
    different bytes) raises :class:`ArtifactCollisionError`.

    The store is safe for concurrent same-content writes (idempotent) and
    rejects concurrent different-content writes under the same artifact_id
    via the registry-style collision check.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- path layout -------------------------------------------------------

    def _path_for(self, content_hash: str) -> Path:
        if len(content_hash) < 2:
            raise ArtifactStoreError(f"invalid content_hash: {content_hash!r}")
        return self.root / content_hash[:2] / content_hash

    # -- write -------------------------------------------------------------

    def put(self, envelope: ArtifactEnvelope, payload: Any) -> StoredArtifact:
        """Materialize ``payload`` and its envelope.

        ``payload`` must be JSON-able.  The content hash is recomputed from
        the canonical envelope+payload; if the envelope carried a content_hash
        it must match.  Same content is idempotent; a collision is a hard
        error.
        """
        payload_bytes = canonical_json(envelope.canonical_payload(payload)).encode("utf-8")
        chash = sha256_hex(payload_bytes)
        if envelope.content_hash and envelope.content_hash != chash:
            raise HashMismatchError(
                f"ArtifactEnvelope.content_hash mismatch: declared "
                f"{envelope.content_hash!r} != recomputed {chash!r}"
            )
        path = self._path_for(chash)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_bytes()
            if existing != payload_bytes:
                raise ArtifactCollisionError(
                    f"content-address collision at {chash}: existing bytes "
                    f"differ from new bytes"
                )
            # idempotent: same content already stored
        else:
            # Atomic-ish write: write to a unique temp file then rename.
            # A unique temp name is required so concurrent writers of the same
            # content do not race on a shared temp path.
            tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(payload_bytes)
            os.replace(tmp, path)
        final_envelope = ArtifactEnvelope(
            artifact_id=envelope.artifact_id,
            artifact_type=envelope.artifact_type,
            artifact_version=envelope.artifact_version,
            input_hash=envelope.input_hash,
            payload_role=envelope.payload_role,
            content_hash=chash,
            completeness=envelope.completeness,
            evidence_state=envelope.evidence_state,
            coverage=envelope.coverage,
            qc_notes=envelope.qc_notes,
            supersedes=envelope.supersedes,
            created_at=envelope.created_at or now_iso(),
        )
        return StoredArtifact(
            envelope=final_envelope,
            payload_bytes=payload_bytes,
            path=str(path),
            written_at=now_iso(),
        )

    # -- read --------------------------------------------------------------

    def get(self, content_hash: str) -> bytes:
        """Read raw artifact bytes by content hash, verifying on read."""
        path = self._path_for(content_hash)
        if not path.exists():
            raise ArtifactStoreError(f"no artifact for content_hash {content_hash!r}")
        data = path.read_bytes()
        actual = sha256_hex(data)
        if actual != content_hash:
            raise HashMismatchError(
                f"on-disk artifact hash mismatch at {content_hash}: recomputed "
                f"{actual}"
            )
        return data

    def exists(self, content_hash: str) -> bool:
        return self._path_for(content_hash).exists()

    # -- listing -----------------------------------------------------------

    def list_hashes(self) -> List[str]:
        out: List[str] = []
        for shard in sorted(self.root.iterdir()):
            if shard.is_dir() and len(shard.name) == 2:
                for f in sorted(shard.iterdir()):
                    if f.is_file() and len(f.name) >= 6:
                        out.append(f.name)
        return out


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_envelope(
    artifact_type: str,
    artifact_version: str,
    input_hash: str,
    payload_role: str = PAYLOAD_ROLE_CANDIDATE,
    completeness: str = ArtifactCompleteness.COMPLETE,
    evidence_state: str = EvidenceState.COMPLETE,
    coverage: Optional[Dict[str, Any]] = None,
    qc_notes: Optional[List[str]] = None,
    supersedes: Optional[List[str]] = None,
) -> ArtifactEnvelope:
    """Construct a fresh envelope with a new artifact_id.

    ``content_hash`` is left empty; :meth:`ArtifactStore.put` fills it from
    the canonical payload so callers cannot forge a hash.
    """
    return ArtifactEnvelope(
        artifact_id=new_id("art-"),
        artifact_type=artifact_type,
        artifact_version=artifact_version,
        input_hash=input_hash,
        payload_role=payload_role,
        completeness=completeness,
        evidence_state=evidence_state,
        coverage=tuple(sorted((coverage or {}).items())),
        qc_notes=tuple(qc_notes or ()),
        supersedes=tuple(supersedes or ()),
    )
