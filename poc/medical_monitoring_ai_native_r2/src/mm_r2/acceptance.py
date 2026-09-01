"""SnapshotAcceptance state chain for the R2 kernel (Design v1.1 section 6.2;
plan R2 step 3).

State chain (exact, no skipping/reversal)::

    imported -> structurally_valid -> mapping_reviewed
            -> snapshot_accepted -> baseline_eligible

Rules
-----
* Transitions are forward-only and one-step.  Any jump or rewind raises
  :class:`AcceptanceChainError`.
* ``baseline_eligible`` is the terminal, gating state.  A snapshot may only
  become eligible when affirmative current :class:`AcceptanceEvidence` is
  provided that binds: source coverage (no critical gaps), critical mapping
  review (clean), identity review (clean), and -- when actor is
  ``system_policy`` -- approved scope plus deterministic/high-confidence
  mapping evidence.  Missing evidence fails closed; omitted evidence is
  never treated as complete.
* Every transition (including rejected/blocked ones) is recorded as an
  :class:`AcceptanceDecisionRecord` -- an auditable, hash-chained decision.
* The authoritative :class:`SnapshotAcceptanceRecord` is **frozen**.
  External callers receive frozen copies; they cannot mutate state or bypass
  transitions.

Binding and authority
---------------------
The :class:`AcceptanceService` is the only authority.  Registration binds a
real, verified :class:`SnapshotBinding` (snapshot + source + identity
algorithm + mapping definitions/results + identity resolution), not just IDs.
Evidence is **issued by the service** (:meth:`AcceptanceService.evidence`)
and is bound to the exact registered binding fingerprint.  A caller cannot
fabricate an :class:`AcceptanceEvidence` with invented booleans/digests: the
public constructor has no issuance input and always rejects direct calls; at
advance time the service
re-derives the critical/identity/deterministic properties from the registered
binding and rejects any mismatch.

The service uses copy-on-write: each transition produces a new frozen record
that replaces the previous one.  Batch C wires this into the atomic SQLite
store transaction.
"""

from __future__ import annotations

import getpass
from dataclasses import InitVar, dataclass, field, replace
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    MmR2Error,
    SourceRevision,
    content_hash,
    new_id,
    now_iso,
)
from .identity import IdentityResolution

__all__ = [
    "SnapshotAcceptanceState",
    "ACCEPTANCE_CHAIN",
    "ACCEPTED_BY_SYSTEM_POLICY",
    "AcceptanceChainError",
    "EligibilityBlockedError",
    "CoverageGap",
    "SnapshotBinding",
    "AcceptanceEvidence",
    "AcceptanceDecisionRecord",
    "SnapshotAcceptanceRecord",
    "AcceptanceService",
    "AcceptanceProof",
]


# ---------------------------------------------------------------------------
# State enum + chain
# ---------------------------------------------------------------------------

class SnapshotAcceptanceState(str, Enum):
    """Exact acceptance chain (Design 6.2).  Order is load-bearing."""

    IMPORTED = "imported"
    STRUCTURALLY_VALID = "structurally_valid"
    MAPPING_REVIEWED = "mapping_reviewed"
    SNAPSHOT_ACCEPTED = "snapshot_accepted"
    BASELINE_ELIGIBLE = "baseline_eligible"


# The canonical ordered chain.  Index arithmetic enforces one-step forward.
ACCEPTANCE_CHAIN: Tuple[SnapshotAcceptanceState, ...] = (
    SnapshotAcceptanceState.IMPORTED,
    SnapshotAcceptanceState.STRUCTURALLY_VALID,
    SnapshotAcceptanceState.MAPPING_REVIEWED,
    SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
    SnapshotAcceptanceState.BASELINE_ELIGIBLE,
)

ACCEPTED_BY_SYSTEM_POLICY = "system_policy"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class AcceptanceChainError(MmR2Error):
    """Illegal acceptance transition (skip, rewind, unknown target, or
    unauthorized actor)."""


class EligibilityBlockedError(AcceptanceChainError):
    """baseline_eligible blocked by coverage/identity/mapping ambiguity or missing evidence."""

    def __init__(self, reasons: List[str]) -> None:
        self.reasons: List[str] = list(reasons)
        super().__init__("; ".join(self.reasons) or "eligibility blocked")


# ---------------------------------------------------------------------------
# Coverage gap
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageGap:
    """One declared coverage gap that blocks baseline eligibility.

    ``scope`` is one of the Design-12 coverage scopes (source/table/row/
    subject/site/risk_domain/report_unit/other).  ``severity`` is ``critical``
    (blocks) or ``minor`` (advisory; does not block alone).
    """

    scope: str
    severity: str           # critical | minor
    detail: str = ""

    def __post_init__(self) -> None:
        if self.scope not in (
            "source", "table", "row", "subject", "site",
            "risk_domain", "report_unit", "other",
        ):
            raise DomainValidationError(f"CoverageGap.scope {self.scope!r} invalid")
        if self.severity not in ("critical", "minor"):
            raise DomainValidationError(
                f"CoverageGap.severity {self.severity!r} invalid"
            )
        if not self.detail:
            raise DomainValidationError("CoverageGap.detail is required")


# ---------------------------------------------------------------------------
# Snapshot binding (real, verified objects; never just IDs)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SnapshotBinding:
    """The real, verified bundle a snapshot acceptance record is bound to.

    Registration and evidence issuance consume actual :class:`ListingSnapshot`,
    :class:`SourceRevision`, :class:`IdentityAlgorithm`,
    :class:`MappingDefinition`, :class:`MappingResult` and
    :class:`IdentityResolution` objects -- not caller-declared strings.  The
    binding validates cross-project / source / snapshot / algorithm
    consistency and one-to-one mapping consistency at construction:

    * snapshot and source must belong to the same project and source revision;
    * at least one mapping definition/result is REQUIRED (mapping review
      cannot be waived by any actor);
    * an explicit :class:`IdentityResolution` bound to the same identity
      algorithm is REQUIRED (identity review cannot be waived; a zero-row
      snapshot may use an explicit empty-but-clean resolution);
    * every mapping result must reference a registered mapping definition
      (no missing / extra / substituted / duplicated mappings);
    * every mapping definition must carry the same ``version``
      (no version mismatch);
    * every mapping result must reference the same project/snapshot/identity
      algorithm as its definition.

    ``fingerprint`` is a content hash over the FULL canonical immutable
    contents of every bound mapping definition, mapping result and the
    identity-resolution outcome (not merely IDs/clean booleans), so two
    bindings with the same IDs but different material semantics produce
    different fingerprints.  A caller-supplied nonempty fingerprint is
    validated against the recomputed value.
    """

    project_id: str
    snapshot: ListingSnapshot
    source: SourceRevision
    identity_algorithm: IdentityAlgorithm
    mapping_definitions: Tuple[MappingDefinition, ...] = ()
    mapping_results: Tuple[MappingResult, ...] = ()
    identity_resolution: Optional[IdentityResolution] = None
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.project_id:
            raise DomainValidationError("SnapshotBinding.project_id is required")
        if not self.snapshot or not self.source or not self.identity_algorithm:
            raise DomainValidationError(
                "SnapshotBinding requires snapshot, source and identity_algorithm"
            )
        pid = self.project_id
        if self.snapshot.project_id != pid:
            raise DomainValidationError(
                "SnapshotBinding snapshot project_id mismatch"
            )
        if self.source.project_id != pid:
            raise DomainValidationError(
                "SnapshotBinding source project_id mismatch"
            )
        if self.snapshot.revision_id != self.source.revision_id:
            raise DomainValidationError(
                "SnapshotBinding snapshot revision_id must match source revision_id"
            )

        # At least one consistent mapping definition/result is REQUIRED: a
        # baseline-eligible binding must have mapping review evidence.  A
        # local user cannot waive this.
        if not self.mapping_definitions:
            raise DomainValidationError(
                "SnapshotBinding requires at least one mapping definition "
                "(mapping review cannot be waived)"
            )

        defs = tuple(sorted(self.mapping_definitions, key=lambda m: m.mapping_id))
        results = tuple(sorted(self.mapping_results, key=lambda r: r.result_id))
        object.__setattr__(self, "mapping_definitions", defs)
        object.__setattr__(self, "mapping_results", results)

        # One-to-one mapping consistency: reject missing/extra/substituted/
        # duplicated/version-mismatched mappings.
        def_by_id: Dict[str, MappingDefinition] = {}
        for m in defs:
            if m.mapping_id in def_by_id:
                raise DomainValidationError(
                    f"SnapshotBinding duplicate mapping_definition {m.mapping_id!r}"
                )
            if m.project_id != pid:
                raise DomainValidationError(
                    f"SnapshotBinding mapping {m.mapping_id!r} project_id mismatch"
                )
            if m.source_revision_id != self.source.revision_id:
                raise DomainValidationError(
                    f"SnapshotBinding mapping {m.mapping_id!r} source_revision mismatch"
                )
            if m.identity_algorithm_id != self.identity_algorithm.algorithm_id:
                raise DomainValidationError(
                    f"SnapshotBinding mapping {m.mapping_id!r} identity algorithm mismatch"
                )
            def_by_id[m.mapping_id] = m

        versions = {m.version for m in def_by_id.values()}
        if len(versions) > 1:
            raise DomainValidationError(
                f"SnapshotBinding mapping version mismatch: {sorted(versions)}"
            )

        result_by_mapping: Dict[str, MappingResult] = {}
        seen_result_ids = set()
        for r in results:
            if r.result_id in seen_result_ids:
                raise DomainValidationError(
                    f"SnapshotBinding duplicate mapping_result {r.result_id!r}"
                )
            seen_result_ids.add(r.result_id)
            if r.project_id != pid:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} project_id mismatch"
                )
            if r.snapshot_id != self.snapshot.snapshot_id:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} snapshot mismatch"
                )
            if r.identity_algorithm_id != self.identity_algorithm.algorithm_id:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} identity algorithm mismatch"
                )
            if r.record_count != self.snapshot.row_count:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} record_count "
                    f"{r.record_count} does not cover snapshot row_count "
                    f"{self.snapshot.row_count}"
                )
            if r.mapping_id not in def_by_id:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} references an "
                    f"unknown mapping {r.mapping_id!r} (extra/substituted mapping)"
                )
            if r.mapping_definition_digest != def_by_id[r.mapping_id].digest:
                raise DomainValidationError(
                    f"SnapshotBinding result {r.result_id!r} mapping semantics "
                    "do not match the registered mapping definition"
                )
            if r.mapping_id in result_by_mapping:
                raise DomainValidationError(
                    f"SnapshotBinding multiple results for mapping {r.mapping_id!r}"
                )
            result_by_mapping[r.mapping_id] = r

        # Every definition must have exactly one result (no missing mapping).
        missing = [mid for mid in def_by_id if mid not in result_by_mapping]
        if missing:
            raise DomainValidationError(
                f"SnapshotBinding missing result(s) for mapping(s): {sorted(missing)}"
            )

        # An explicit IdentityResolution is REQUIRED: identity review cannot
        # be waived.  A zero-row snapshot may still use an explicit
        # empty-but-clean IdentityResolution (resolved=(), ambiguities=()).
        if self.identity_resolution is None:
            raise DomainValidationError(
                "SnapshotBinding requires an explicit IdentityResolution "
                "bound to the same identity algorithm (identity review cannot "
                "be waived)"
            )
        if self.identity_resolution.algorithm_digest != self.identity_algorithm.digest:
            raise DomainValidationError(
                "SnapshotBinding identity_resolution algorithm digest mismatch"
            )
        resolution_projects = {
            r.project_id for r in self.identity_resolution.resolved
        } | {
            a.project_id for a in self.identity_resolution.ambiguities
        }
        if any(project_id != pid for project_id in resolution_projects):
            raise DomainValidationError(
                "SnapshotBinding identity_resolution project_id mismatch: "
                f"expected {pid!r}, found {sorted(resolution_projects)!r}"
            )
        identity_coverage = (
            len(self.identity_resolution.resolved)
            + len(self.identity_resolution.ambiguities)
        )
        if identity_coverage != self.snapshot.row_count:
            raise DomainValidationError(
                "SnapshotBinding identity_resolution coverage "
                f"{identity_coverage} does not match snapshot row_count "
                f"{self.snapshot.row_count}"
            )
        resolved_digests = [
            identity.digest for identity in self.identity_resolution.resolved
        ]
        if len(resolved_digests) != len(set(resolved_digests)):
            raise DomainValidationError(
                "SnapshotBinding identity_resolution contains duplicate "
                "resolved identities"
            )

        ambiguity_payloads = [
            {
                "kind": a.kind,
                "project_id": a.project_id,
                "algorithm_digest": a.algorithm_digest,
                "candidate_digests": list(a.candidate_digests),
                "reason": a.reason,
            }
            for a in self.identity_resolution.ambiguities
        ]
        ambiguity_payloads.sort(
            key=lambda item: (
                item["kind"],
                item["project_id"],
                item["algorithm_digest"],
                tuple(item["candidate_digests"]),
                item["reason"],
            )
        )

        # Fingerprint: bind the FULL canonical immutable contents of every
        # mapping definition and result, plus the identity-resolution outcome
        # (resolved digests + ambiguity digests/kinds), not merely IDs or
        # clean booleans.  Two bindings with the same IDs but different
        # source_field/canonical_field/confidence/ambiguity/record_count or
        # identity resolution MUST have different fingerprints.
        fp = content_hash({
            "project_id": pid,
            "snapshot_hash": self.snapshot.content_hash,
            "source_hash": self.source.content_hash,
            "algorithm_digest": self.identity_algorithm.digest,
            "mapping_version": self.mapping_version,
            "mapping_definitions": [
                {
                    "mapping_id": m.mapping_id,
                    "source_field": m.source_field,
                    "canonical_field": m.canonical_field,
                    "confidence": m.confidence,
                    "is_critical": m.is_critical,
                    "version": m.version,
                }
                for m in defs
            ],
            "mapping_results": [
                {
                    "result_id": r.result_id,
                    "mapping_id": r.mapping_id,
                    "record_count": r.record_count,
                    "identity_digest": r.identity_digest,
                    "is_ambiguous": r.is_ambiguous,
                    "ambiguity_reason": r.ambiguity_reason,
                }
                for r in results
            ],
            "identity_resolution": {
                "algorithm_digest": self.identity_algorithm.digest,
                "resolved": sorted(
                    (
                        {
                            "record_id": r.record_id,
                            "project_id": r.project_id,
                            "algorithm_digest": r.algorithm_digest,
                            "key_fields": dict(r.key_fields),
                            "digest": r.digest,
                        }
                        for r in self.identity_resolution.resolved
                    ),
                    key=lambda item: (
                        item["project_id"], item["algorithm_digest"],
                        item["digest"], item["record_id"],
                    ),
                ),
                "ambiguities": ambiguity_payloads,
            },
        })
        # A caller-supplied nonempty fingerprint must be validated against the
        # recomputed value, not silently overwritten.
        if self.fingerprint and self.fingerprint != fp:
            raise DomainValidationError(
                "SnapshotBinding.fingerprint mismatch: declared "
                f"{self.fingerprint!r} != recomputed {fp!r}"
            )
        object.__setattr__(self, "fingerprint", fp)

    @property
    def mapping_version(self) -> str:
        if not self.mapping_definitions:
            return ""
        return self.mapping_definitions[0].version

    @property
    def identity_clean(self) -> bool:
        """Identity review is clean when the (required) explicit
        IdentityResolution is clean.  There is no "no resolution" waiver."""
        if self.identity_resolution is None:
            return False
        return self.identity_resolution.is_clean

    @property
    def critical_results(self) -> Tuple[MappingResult, ...]:
        """Mapping results whose definition is critical."""
        def_by_id = {m.mapping_id: m for m in self.mapping_definitions}
        return tuple(
            r for r in self.mapping_results
            if def_by_id[r.mapping_id].is_critical
        )

    @property
    def critical_mapping_clean(self) -> bool:
        """Critical mapping review is clean when every critical mapping result
        is unambiguous.  (Definition confidence is a separate axis gated by
        ``deterministic_mapping`` for system_policy, not by mapping review.)"""
        for r in self.critical_results:
            if r.is_ambiguous:
                return False
        return True

    @property
    def deterministic_mapping(self) -> bool:
        """System-policy deterministic evidence requires at least one critical
        mapping and every critical definition at confidence exactly 1.0."""
        criticals = [m for m in self.mapping_definitions if m.is_critical]
        if not criticals:
            return False
        return all(m.confidence == 1.0 for m in criticals)


# ---------------------------------------------------------------------------
# Evidence contract (service-issued, frozen, affirmative)
# ---------------------------------------------------------------------------

# Build-time token captured into the sealed service issuer at module
# initialization, then removed from the module namespace.
_EVIDENCE_OK = object()


@dataclass(frozen=True)
class AcceptanceEvidence:
    """Explicit frozen evidence required to advance acceptance transitions.

    Evidence is **issued by the service** and bound to the exact registered
    :class:`SnapshotBinding` via ``binding_fingerprint``.  The critical
    mapping / identity / deterministic properties are **derived from the
    bound objects** by the service -- a caller cannot declare
    ``critical_mapping_clean`` or ``deterministic_mapping`` directly.

    Direct construction is unavailable to public callers (the public
    constructor always rejects and exposes no issuance input).  Use
    :meth:`AcceptanceService.evidence`.
    """

    binding_fingerprint: str
    actor: str
    produced_at: str
    structural_validation_complete: bool = False
    source_coverage_complete: bool = False
    coverage_gaps: Tuple[CoverageGap, ...] = ()
    approved_scope: bool = False
    # Derived by the service from the bound binding (never caller-set):
    critical_mapping_clean: bool = False
    identity_review_clean: bool = False
    deterministic_mapping: bool = False
    evidence_hash: str = ""
    _issued: InitVar[Any] = None

    def __post_init__(
        self, _issued: Any = None, _authority_token: Any = _EVIDENCE_OK,
    ) -> None:
        if _issued is not _authority_token:
            raise DomainValidationError(
                "AcceptanceEvidence cannot be constructed directly; use "
                "AcceptanceService.evidence(...) to obtain service-issued "
                "evidence bound to a registered snapshot binding"
            )
        if not self.binding_fingerprint:
            raise DomainValidationError(
                "AcceptanceEvidence.binding_fingerprint is required"
            )
        if not self.actor:
            raise DomainValidationError("AcceptanceEvidence.actor is required")
        object.__setattr__(self, "coverage_gaps", tuple(self.coverage_gaps))
        eh = self.compute_evidence_hash()
        if self.evidence_hash and self.evidence_hash != eh:
            raise DomainValidationError(
                f"AcceptanceEvidence.evidence_hash mismatch: declared "
                f"{self.evidence_hash!r} != recomputed {eh!r}"
            )
        object.__setattr__(self, "evidence_hash", eh)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "binding_fingerprint": self.binding_fingerprint,
            "actor": self.actor,
            "produced_at": self.produced_at,
            "structural_validation_complete": self.structural_validation_complete,
            "source_coverage_complete": self.source_coverage_complete,
            "coverage_gaps": [
                {"scope": g.scope, "severity": g.severity, "detail": g.detail}
                for g in self.coverage_gaps
            ],
            "approved_scope": self.approved_scope,
            "critical_mapping_clean": self.critical_mapping_clean,
            "identity_review_clean": self.identity_review_clean,
            "deterministic_mapping": self.deterministic_mapping,
        }

    def compute_evidence_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Decision record (auditable, append-only, hash-chained)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceDecisionRecord:
    """Auditable record of one acceptance decision."""

    record_id: str
    snapshot_id: str
    project_id: str
    from_state: str
    to_state: str
    actor: str
    decision: str               # transition | rejected | eligibility_blocked | transition_blocked
    evidence_hash: str = ""
    reasons: Tuple[str, ...] = ()
    prev_hash: str = ""
    record_hash: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.record_id:
            raise DomainValidationError("record_id required")
        if not self.snapshot_id:
            raise DomainValidationError("snapshot_id required")
        if not self.project_id:
            raise DomainValidationError("project_id required")
        if self.decision not in ("transition", "rejected", "eligibility_blocked", "transition_blocked"):
            raise DomainValidationError(
                f"decision {self.decision!r} invalid"
            )
        expected = self.compute_hash()
        if self.record_hash and self.record_hash != expected:
            raise DomainValidationError(
                f"record_hash mismatch: declared {self.record_hash!r} "
                f"!= recomputed {expected!r}"
            )
        object.__setattr__(self, "record_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "snapshot_id": self.snapshot_id,
            "project_id": self.project_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "actor": self.actor,
            "decision": self.decision,
            "evidence_hash": self.evidence_hash,
            "reasons": list(self.reasons),
            "prev_hash": self.prev_hash,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Acceptance record (FROZEN authority object)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SnapshotAcceptanceRecord:
    """Live acceptance state for one snapshot.

    **Frozen.** External callers receive this frozen record and cannot mutate
    state, lists, or decision records.  The :class:`AcceptanceService` uses
    copy-on-write: each transition produces a new frozen record via
    :func:`dataclasses.replace`.
    """

    snapshot_id: str
    project_id: str
    state: SnapshotAcceptanceState = SnapshotAcceptanceState.IMPORTED
    accepted_by: Optional[str] = None
    blocked: bool = False
    block_reasons: Tuple[str, ...] = ()
    coverage_gaps: Tuple[CoverageGap, ...] = ()
    critical_mapping_ambiguous: bool = False
    identity_ambiguous: bool = False
    evidence: Optional[AcceptanceEvidence] = None
    updated_at: str = ""
    records: Tuple[AcceptanceDecisionRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raise DomainValidationError("snapshot_id required")
        if not self.project_id:
            raise DomainValidationError("project_id required")

    @property
    def is_baseline_eligible(self) -> bool:
        return (
            self.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
            and not self.blocked
        )


# ---------------------------------------------------------------------------
# Proof (read-only projection, never an authority token)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceProof:
    """Read-only projection of an acceptance record.

    Like R1's SnapshotBaselineProof, this is **not** an authority token.
    Baseline-dependent code must read the live service state, not a proof.
    """

    snapshot_id: str
    project_id: str
    state: SnapshotAcceptanceState
    accepted_by: Optional[str] = None
    blocked: bool = False
    evidence_hash: str = ""

    @classmethod
    def from_record(cls, rec: SnapshotAcceptanceRecord) -> "AcceptanceProof":
        payload = {
            "snapshot_id": rec.snapshot_id,
            "state": rec.state.value,
            "accepted_by": rec.accepted_by,
            "blocked": rec.blocked,
        }
        return cls(
            snapshot_id=rec.snapshot_id,
            project_id=rec.project_id,
            state=rec.state,
            accepted_by=rec.accepted_by,
            blocked=rec.blocked,
            evidence_hash=content_hash(payload),
        )

    @property
    def is_baseline_eligible(self) -> bool:
        """Projected view only; not an authority decision."""
        return (
            not self.blocked
            and self.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
        )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AcceptanceService:
    """Sole authority over :class:`SnapshotAcceptanceRecord` transitions.

    The record is frozen; the service uses copy-on-write (``replace``) on every
    transition so external callers who hold a stale reference cannot observe
    or mutate the new state.  ``get`` returns the frozen record directly --
    since it is frozen, callers cannot mutate it.

    Actor gate: the service is initialized with the current local OS user
    (synthetic fixture name in tests).  Transitions are allowed only by that
    user or by ``system_policy``; any other actor is rejected and audited.

    Authority: registration binds a real :class:`SnapshotBinding`.  Evidence
    is issued by :meth:`evidence` and bound to the registered binding
    fingerprint; the critical/identity/deterministic properties are re-derived
    at advance time from the registered binding, so a caller cannot claim them.
    """

    def __init__(self, local_user: Optional[str] = None) -> None:
        self._local_user = local_user if local_user is not None else getpass.getuser()
        self._records: Dict[str, SnapshotAcceptanceRecord] = {}
        self._bindings: Dict[str, SnapshotBinding] = {}
        self._chain_head: Dict[str, str] = {}   # project_id -> last record_hash

    @property
    def local_user(self) -> str:
        return self._local_user

    # -- actor gate --------------------------------------------------------

    def _check_actor(self, actor: str) -> None:
        """Reject any actor that is neither the local OS user nor system_policy."""
        if actor == ACCEPTED_BY_SYSTEM_POLICY:
            return
        if actor == self._local_user:
            return
        raise AcceptanceChainError(
            f"actor {actor!r} is not the local user {self._local_user!r} "
            f"nor system_policy"
        )

    def _is_trusted_actor(self, actor: str) -> bool:
        return actor == ACCEPTED_BY_SYSTEM_POLICY or actor == self._local_user

    # -- registration ------------------------------------------------------

    def register(self, binding: SnapshotBinding, actor: str) -> SnapshotAcceptanceRecord:
        """Create a fresh acceptance record bound to a real verified binding.

        Resolves snapshot/project from the binding itself (never from caller
        strings).  The binding must be consistent (validated at construction)
        and is retained so evidence can be cross-checked against it.
        """
        if not isinstance(binding, SnapshotBinding):
            raise AcceptanceChainError(
                "register requires a SnapshotBinding of real verified objects"
            )
        if not self._is_trusted_actor(actor):
            raise AcceptanceChainError(
                f"actor {actor!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            )
        snapshot_id = binding.snapshot.snapshot_id
        project_id = binding.project_id
        if snapshot_id in self._records:
            raise AcceptanceChainError(
                f"snapshot {snapshot_id!r} already registered"
            )
        dr = self._make_record(
            snapshot_id, project_id,
            from_state=SnapshotAcceptanceState.IMPORTED,
            to_state=SnapshotAcceptanceState.IMPORTED,
            actor=actor, decision="transition",
            evidence_hash="", reasons=(),
        )
        rec = SnapshotAcceptanceRecord(
            snapshot_id=snapshot_id,
            project_id=project_id,
            state=SnapshotAcceptanceState.IMPORTED,
            accepted_by=actor,
            updated_at=now_iso(),
            records=(dr,),
        )
        self._records[snapshot_id] = rec
        self._bindings[snapshot_id] = binding
        return rec

    def get(self, snapshot_id: str) -> SnapshotAcceptanceRecord:
        """Return the **frozen** authoritative record (cannot be mutated)."""
        rec = self._records.get(snapshot_id)
        if rec is None:
            raise AcceptanceChainError(f"unknown snapshot {snapshot_id!r}")
        return rec

    def binding(self, snapshot_id: str) -> SnapshotBinding:
        """Return the registered real binding for a snapshot."""
        if snapshot_id not in self._bindings:
            raise AcceptanceChainError(f"unknown snapshot {snapshot_id!r}")
        return self._bindings[snapshot_id]

    def proof(self, snapshot_id: str) -> AcceptanceProof:
        return AcceptanceProof.from_record(self.get(snapshot_id))

    # -- evidence issuance (service-controlled) ----------------------------

    def evidence(
        self,
        snapshot_id: str,
        actor: str,
        *,
        structural_validation_complete: bool = False,
        source_coverage_complete: bool = False,
        coverage_gaps: Tuple[CoverageGap, ...] = (),
        approved_scope: bool = False,
        produced_at: str = "",
    ) -> AcceptanceEvidence:
        """Issue service-controlled evidence bound to the registered binding.

        Only the per-step human/system decisions (structural validation,
        source coverage, approved scope, coverage gaps) are caller-selected.
        The critical mapping / identity / deterministic properties are
        **derived from the registered binding** and stamped into the
        evidence; a caller cannot declare them.
        """
        if not self._is_trusted_actor(actor):
            raise AcceptanceChainError(
                f"actor {actor!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            )
        binding = self.binding(snapshot_id)
        ev = AcceptanceEvidence(
            binding_fingerprint=binding.fingerprint,
            actor=actor,
            produced_at=produced_at or now_iso(),
            structural_validation_complete=structural_validation_complete,
            source_coverage_complete=source_coverage_complete,
            coverage_gaps=coverage_gaps,
            approved_scope=approved_scope,
            critical_mapping_clean=binding.critical_mapping_clean,
            identity_review_clean=binding.identity_clean,
            deterministic_mapping=binding.deterministic_mapping,
            _issued=_EVIDENCE_OK,
        )
        return ev

    # -- evidence binding --------------------------------------------------

    def _evidence_binding_reasons(
        self, rec: SnapshotAcceptanceRecord, ev: AcceptanceEvidence
    ) -> List[str]:
        """Cross-check that evidence is bound to the exact registered
        snapshot/project/binding.  Returns blocking reasons, or [] if the
        evidence matches the registered binding."""
        reasons: List[str] = []
        if ev.actor != rec.accepted_by and ev.actor != ACCEPTED_BY_SYSTEM_POLICY:
            # The evidence actor must be a trusted actor (checked elsewhere);
            # here we only bind it to the record.
            pass
        binding = self._bindings.get(rec.snapshot_id)
        if binding is None:
            reasons.append("record has no registered binding")
            return reasons
        if ev.binding_fingerprint != binding.fingerprint:
            reasons.append(
                "evidence binding_fingerprint does not match the registered "
                "snapshot binding"
            )
        # Re-derive the derived properties from the registered binding and
        # reject any mismatch (prevents a caller-issued or tampered evidence
        # from claiming a different critical/identity/deterministic state).
        expect = {
            "critical_mapping_clean": binding.critical_mapping_clean,
            "identity_review_clean": binding.identity_clean,
            "deterministic_mapping": binding.deterministic_mapping,
        }
        got = {
            "critical_mapping_clean": ev.critical_mapping_clean,
            "identity_review_clean": ev.identity_review_clean,
            "deterministic_mapping": ev.deterministic_mapping,
        }
        for k, expected in expect.items():
            if got[k] != expected:
                reasons.append(
                    f"evidence {k} ({got[k]}) does not match the registered "
                    f"binding-derived value ({expected})"
                )
        return reasons

    # -- transition core ---------------------------------------------------

    def _forward_error(self, current: SnapshotAcceptanceState, target: SnapshotAcceptanceState) -> Optional[str]:
        if target not in ACCEPTANCE_CHAIN:
            return f"unknown target state {target!r}"
        ci = ACCEPTANCE_CHAIN.index(current)
        ti = ACCEPTANCE_CHAIN.index(target)
        if ti <= ci:
            return f"illegal rewind/stay: {current.value} -> {target.value}"
        if ti != ci + 1:
            return (
                f"illegal skip: {current.value} -> {target.value} "
                f"(must advance one step)"
            )
        return None

    def _append_blocked(
        self,
        rec: SnapshotAcceptanceRecord,
        target: SnapshotAcceptanceState,
        actor: str,
        ev: Optional[AcceptanceEvidence],
        reasons: List[str],
        decision: str = "transition_blocked",
    ) -> SnapshotAcceptanceRecord:
        """Append a blocked decision record without changing the accepted state."""
        dr = self._make_record(
            rec.snapshot_id, rec.project_id,
            from_state=rec.state, to_state=target,
            actor=actor, decision=decision,
            evidence_hash=ev.evidence_hash if ev else "",
            reasons=tuple(reasons),
        )
        blocked_rec = replace(
            rec, blocked=True, block_reasons=tuple(reasons),
            evidence=ev, updated_at=now_iso(),
            records=rec.records + (dr,),
        )
        self._records[rec.snapshot_id] = blocked_rec
        return blocked_rec

    def advance(
        self,
        snapshot_id: str,
        target: SnapshotAcceptanceState,
        actor: str,
        evidence: Optional[AcceptanceEvidence] = None,
    ) -> SnapshotAcceptanceRecord:
        """Advance one step toward ``target``.

        Every step has step-specific affirmative evidence gates; missing
        evidence fails closed.  Unauthorized actors, evidence bound to a
        different binding, and illegal skip/rewind/stay transitions are all
        rejected **and audited** (a blocked/rejected decision record is
        appended) without changing the accepted state.
        """
        rec = self.get(snapshot_id)

        # 1) actor gate
        if not self._is_trusted_actor(actor):
            reasons = [
                f"unauthorized actor {actor!r}; only local user "
                f"{self._local_user!r} or system_policy may transition"
            ]
            self._append_blocked(rec, target, actor, None,
                                 reasons, decision="rejected")
            raise AcceptanceChainError(
                f"actor {actor!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            )

        # 2) forward-only check FIRST (VETO5): illegal skip/rewind/stay is
        #    always audited with target/reasons/actor regardless of evidence.
        fwd_err = self._forward_error(rec.state, target)
        if fwd_err is not None:
            self._append_blocked(rec, target, actor, evidence, [fwd_err])
            raise AcceptanceChainError(fwd_err)

        # 3) evidence must be service-issued and bound to the registered binding
        if evidence is None:
            reasons = ["evidence is missing (must be service-issued and bound)"]
            self._append_blocked(rec, target, actor, None, reasons)
            raise AcceptanceChainError("evidence mismatch: " + "; ".join(reasons))
        binding_reasons = self._evidence_binding_reasons(rec, evidence)
        if binding_reasons:
            self._append_blocked(rec, target, actor, evidence, binding_reasons)
            raise AcceptanceChainError(
                f"evidence mismatch: {'; '.join(binding_reasons)}"
            )
        if evidence.actor != actor:
            binding_reasons = [
                f"evidence actor {evidence.actor!r} does not match transition "
                f"actor {actor!r}"
            ]
            self._append_blocked(rec, target, actor, evidence, binding_reasons)
            raise AcceptanceChainError(
                f"evidence mismatch: {'; '.join(binding_reasons)}"
            )

        reasons = self._step_reasons(target, evidence, actor)
        if reasons:
            self._append_blocked(rec, target, actor, evidence, reasons)
            if target == SnapshotAcceptanceState.BASELINE_ELIGIBLE:
                raise EligibilityBlockedError(reasons)
            raise AcceptanceChainError(
                f"{target.value} blocked: {'; '.join(reasons)}"
            )

        dr = self._make_record(
            snapshot_id, rec.project_id,
            from_state=rec.state, to_state=target,
            actor=actor, decision="transition",
            evidence_hash=evidence.evidence_hash, reasons=(),
        )
        new_rec = replace(
            rec,
            state=target,
            accepted_by=actor,
            updated_at=now_iso(),
            blocked=False,
            block_reasons=(),
            coverage_gaps=evidence.coverage_gaps,
            critical_mapping_ambiguous=not evidence.critical_mapping_clean,
            identity_ambiguous=not evidence.identity_review_clean,
            evidence=evidence,
            records=rec.records + (dr,),
        )
        self._records[snapshot_id] = new_rec
        return new_rec

    def reject(
        self,
        snapshot_id: str,
        reason: str,
        actor: str,
        target: SnapshotAcceptanceState,
    ) -> SnapshotAcceptanceRecord:
        """Record a rejected transition attempt without changing state.

        An unauthorized actor's reject attempt is itself audited (a
        ``rejected`` decision record is appended) and the accepted state is
        unchanged -- matching the post-registration audit guarantee.
        """
        rec = self.get(snapshot_id)
        if not self._is_trusted_actor(actor):
            reasons = [
                f"unauthorized actor {actor!r}; only local user "
                f"{self._local_user!r} or system_policy may reject"
            ]
            dr = self._make_record(
                snapshot_id, rec.project_id,
                from_state=rec.state, to_state=target,
                actor=actor, decision="rejected",
                evidence_hash="", reasons=tuple(reasons),
            )
            new_rec = replace(rec, updated_at=now_iso(),
                              records=rec.records + (dr,))
            self._records[snapshot_id] = new_rec
            raise AcceptanceChainError(
                f"actor {actor!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            )
        if not reason:
            raise DomainValidationError("reject requires a reason")
        dr = self._make_record(
            snapshot_id, rec.project_id,
            from_state=rec.state, to_state=target,
            actor=actor, decision="rejected",
            evidence_hash="", reasons=(reason,),
        )
        new_rec = replace(rec, updated_at=now_iso(), records=rec.records + (dr,))
        self._records[snapshot_id] = new_rec
        return new_rec

    # -- step-specific gates ------------------------------------------------

    @staticmethod
    def _step_reasons(
        target: SnapshotAcceptanceState,
        ev: AcceptanceEvidence,
        actor: str,
    ) -> List[str]:
        """Return blocking reasons for the *target* step, or [] if clear."""
        reasons: List[str] = []
        if target == SnapshotAcceptanceState.STRUCTURALLY_VALID:
            if not ev.structural_validation_complete:
                reasons.append(
                    "structural validation evidence is missing/incomplete"
                )
        elif target == SnapshotAcceptanceState.MAPPING_REVIEWED:
            if not ev.critical_mapping_clean:
                reasons.append("critical mapping review is missing/ambiguous")
            if not ev.identity_review_clean:
                reasons.append("identity review is missing/ambiguous")
        elif target == SnapshotAcceptanceState.SNAPSHOT_ACCEPTED:
            if not ev.approved_scope:
                reasons.append(
                    "accepted scope is not explicit (approved_scope required)"
                )
            if actor == ACCEPTED_BY_SYSTEM_POLICY:
                if not ev.deterministic_mapping:
                    reasons.append(
                        "system_policy requires deterministic (confidence=1.0) "
                        "critical mapping evidence"
                    )
        elif target == SnapshotAcceptanceState.BASELINE_ELIGIBLE:
            # baseline_eligible requires current source coverage plus all
            # prior gates remain affirmative.
            if not ev.source_coverage_complete:
                reasons.append(
                    "source coverage evidence is missing/incomplete"
                )
            critical = [g for g in ev.coverage_gaps if g.severity == "critical"]
            if critical:
                reasons.append(
                    "critical coverage gap(s): "
                    + ", ".join(
                        sorted(f"{g.scope}:{g.detail}" for g in critical)
                    )
                )
            if not ev.critical_mapping_clean:
                reasons.append("critical mapping review is missing/ambiguous")
            if not ev.identity_review_clean:
                reasons.append("identity review is missing/ambiguous")
            if not ev.approved_scope:
                reasons.append(
                    "accepted scope is not explicit (approved_scope required)"
                )
            if actor == ACCEPTED_BY_SYSTEM_POLICY:
                if not ev.deterministic_mapping:
                    reasons.append(
                        "system_policy requires deterministic (confidence=1.0) "
                        "critical mapping evidence"
                    )
        return reasons

    def can_advance(
        self,
        snapshot_id: str,
        target: SnapshotAcceptanceState,
        evidence: Optional[AcceptanceEvidence] = None,
        actor: str = "",
    ) -> Tuple[bool, List[str]]:
        """Non-mutating step-gate preview for *any* target step."""
        rec = self.get(snapshot_id)
        # forward-only check
        fwd_err = self._forward_error(rec.state, target)
        if fwd_err is not None:
            return False, [fwd_err]
        a = actor or rec.accepted_by or ""
        if not self._is_trusted_actor(a):
            return False, [
                f"actor {a!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            ]
        if evidence is None:
            return False, ["evidence is missing (must be service-issued and bound)"]
        binding = self._evidence_binding_reasons(rec, evidence)
        if binding:
            return False, binding
        if evidence.actor != a:
            return False, [
                f"evidence actor {evidence.actor!r} does not match actor {a!r}"
            ]
        reasons = self._step_reasons(target, evidence, a)
        return (len(reasons) == 0), reasons

    def can_advance_to_eligible(
        self,
        snapshot_id: str,
        evidence: Optional[AcceptanceEvidence] = None,
        actor: str = "",
    ) -> Tuple[bool, List[str]]:
        """Non-mutating baseline-eligibility preview (backward compat)."""
        rec = self.get(snapshot_id)
        if rec.state != SnapshotAcceptanceState.SNAPSHOT_ACCEPTED:
            return False, [
                f"current state is {rec.state.value}, not snapshot_accepted"
            ]
        a = actor or rec.accepted_by or ""
        if not self._is_trusted_actor(a):
            return False, [
                f"actor {a!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            ]
        if evidence is None:
            return False, ["evidence is missing (must be service-issued and bound)"]
        binding = self._evidence_binding_reasons(rec, evidence)
        if binding:
            return False, binding
        if evidence.actor != a:
            return False, [
                f"evidence actor {evidence.actor!r} does not match actor {a!r}"
            ]
        reasons = self._step_reasons(
            SnapshotAcceptanceState.BASELINE_ELIGIBLE, evidence, a
        )
        return (len(reasons) == 0), reasons

    # -- decision-record chain --------------------------------------------

    def _make_record(
        self,
        snapshot_id: str,
        project_id: str,
        from_state: SnapshotAcceptanceState,
        to_state: SnapshotAcceptanceState,
        actor: str,
        decision: str,
        evidence_hash: str,
        reasons: Tuple[str, ...],
    ) -> AcceptanceDecisionRecord:
        prev_hash = self._chain_head.get(project_id, "")
        dr = AcceptanceDecisionRecord(
            record_id=new_id("adr-"),
            snapshot_id=snapshot_id,
            project_id=project_id,
            from_state=from_state.value,
            to_state=to_state.value,
            actor=actor,
            decision=decision,
            evidence_hash=evidence_hash,
            reasons=reasons,
            prev_hash=prev_hash,
            created_at=now_iso(),
        )
        self._chain_head[project_id] = dr.record_hash
        return dr

    def decision_records(self, snapshot_id: str) -> List[AcceptanceDecisionRecord]:
        return list(self.get(snapshot_id).records)

    def verify_chain(self, project_id: str) -> bool:
        """Verify the hash-chain of decision records for one project."""
        seen: List[AcceptanceDecisionRecord] = []
        for rec in self._records.values():
            if rec.project_id == project_id:
                seen.extend(rec.records)
        seen.sort(key=lambda r: r.created_at)
        prev = ""
        for r in seen:
            if r.prev_hash != prev:
                return False
            if r.record_hash != r.compute_hash():
                return False
            prev = r.record_hash
        return True


# Seal evidence issuance after both classes exist.  Direct construction has a
# clean public signature with no authority input and always fails.  The service
# issuer alone retains the original generated dataclass initializer and the
# build-time capability in this closure.
def _seal_evidence_issuance(authority_token: Any) -> None:
    generated_init = AcceptanceEvidence.__init__
    original_post = AcceptanceEvidence.__post_init__

    def checked_post(self, _issued: Any = None) -> None:
        return original_post(self, _issued, authority_token)

    def blocked_direct_init(
        self, binding_fingerprint: str, actor: str, produced_at: str,
        structural_validation_complete: bool = False,
        source_coverage_complete: bool = False,
        coverage_gaps: Tuple[CoverageGap, ...] = (),
        approved_scope: bool = False,
        critical_mapping_clean: bool = False,
        identity_review_clean: bool = False,
        deterministic_mapping: bool = False,
        evidence_hash: str = "",
    ) -> None:
        raise DomainValidationError(
            "AcceptanceEvidence cannot be constructed directly; use "
            "AcceptanceService.evidence(...) to obtain service-issued evidence"
        )

    def service_evidence(
        self, snapshot_id: str, actor: str, *,
        structural_validation_complete: bool = False,
        source_coverage_complete: bool = False,
        coverage_gaps: Tuple[CoverageGap, ...] = (),
        approved_scope: bool = False,
        produced_at: str = "",
    ) -> AcceptanceEvidence:
        if not self._is_trusted_actor(actor):
            raise AcceptanceChainError(
                f"actor {actor!r} is not the local user {self._local_user!r} "
                f"nor system_policy"
            )
        binding = self.binding(snapshot_id)
        evidence = object.__new__(AcceptanceEvidence)
        generated_init(
            evidence,
            binding_fingerprint=binding.fingerprint,
            actor=actor,
            produced_at=produced_at or now_iso(),
            structural_validation_complete=structural_validation_complete,
            source_coverage_complete=source_coverage_complete,
            coverage_gaps=coverage_gaps,
            approved_scope=approved_scope,
            critical_mapping_clean=binding.critical_mapping_clean,
            identity_review_clean=binding.identity_clean,
            deterministic_mapping=binding.deterministic_mapping,
            _issued=authority_token,
        )
        return evidence

    AcceptanceEvidence.__post_init__ = checked_post
    AcceptanceEvidence.__init__ = blocked_direct_init
    AcceptanceService.evidence = service_evidence


_seal_evidence_issuance(_EVIDENCE_OK)
del _seal_evidence_issuance
del _EVIDENCE_OK
