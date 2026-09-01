"""R4 common coverage contract -- layer namespaces, value objects, and the
expected-set ledger with deterministic canonical hashing.

Frozen source of truth: ``FROZEN_R4_CONTRACT_V1`` (matrix §§3.2-3.4, 6).
This module imports frozen public APIs read-only: R1 ``CoverageUnitStatus``
for L0 values and R2 ``RiskLifecycleState`` for the L3 authority.  It does
not copy or fork lifecycle or normalization authority, and it does not mutate
``sys.path``; the caller/test environment supplies the R1/R2 source roots.

Design constraints enforced here (matrix §3.2-3.4, §6):

1. Five exclusive L1 dispositions; three multi-valued L1b evidence polarities;
   L0 is sourced directly from the frozen R1 ``CoverageUnitStatus`` enum;
   L3 is the frozen R2 ``RiskLifecycleState`` class itself (an identity alias).
2. ``EvaluationUnit.unit_id`` and ``expected_set_hash`` are deterministic
   canonical hashes over the exact frozen dimensions; expected-set hash is
   input-order independent.
3. The ledger fails closed on duplicate/missing/unexpected units, invalid
   evidence joins, false complete coverage, or count contamination.
4. ``is_domain_complete`` fails closed when L0 has partial/truncated/failed/
   missing, any L1 is not-evaluable, provenance is missing, or join/count
   invariants break.  An L0 *reasoned* not-evaluable never proves medical
   completeness.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import (Any, Dict, List, Optional, Protocol, Sequence,
                    Set, Tuple, runtime_checkable)
from collections.abc import Mapping

from ..domain.execution import CoverageUnitStatus as _R1CoverageUnitStatus
from ..domain.risk import (RiskCandidate as _R2RiskCandidate,
                        RiskLifecycleState as _R2RiskLifecycleState)


# ---------------------------------------------------------------------------
# L0 -- execution coverage status, sourced from frozen R1 (matrix §3.2)
# ---------------------------------------------------------------------------
#
# L0 reuses the frozen R1 ``CoverageUnitStatus`` enum.  Every L0 facade value
# and the ``ALL_STATUSES`` membership tuple are derived from the imported enum
# via ``.value``, so R4 holds no independently typed R1 string literals.  L0
# answers execution/input coverage only; it never proves medical evaluability.

class L0CoverageStatus:
    """Execution coverage status namespace sourced from frozen R1 values.

    All string values are derived from the imported R1 ``CoverageUnitStatus``
    enum (``.value``), not independently typed.  L0 says nothing about medical
    evaluability (L1) or risk lifecycle (L3).  See matrix §3.2.
    """

    COVERED = _R1CoverageUnitStatus.COVERED.value
    PARTIAL = _R1CoverageUnitStatus.PARTIAL.value
    TRUNCATED = _R1CoverageUnitStatus.TRUNCATED.value
    NOT_APPLICABLE = _R1CoverageUnitStatus.NOT_APPLICABLE.value
    NOT_EVALUABLE = _R1CoverageUnitStatus.NOT_EVALUABLE.value
    FAILED = _R1CoverageUnitStatus.FAILED.value
    MISSING = _R1CoverageUnitStatus.MISSING.value

    ALL_STATUSES: Tuple[str, ...] = tuple(
        member.value for member in _R1CoverageUnitStatus
    )

    @classmethod
    def passing_for_domain_complete(cls) -> Tuple[str, ...]:
        """L0 values that do NOT block medical domain completeness.

        ``covered`` and ``not_applicable`` are the only L0 statuses that allow
        a domain-complete claim.  ``not_evaluable`` is intentionally absent:
        a *reasoned* L0 gap still means the run cannot prove medical coverage
        (matrix §3.2 last paragraph).
        """
        return (cls.COVERED, cls.NOT_APPLICABLE)

    @classmethod
    def blocks_domain_complete(cls) -> Tuple[str, ...]:
        """L0 values that always block medical domain completeness."""
        return (cls.PARTIAL, cls.TRUNCATED, cls.NOT_EVALUABLE,
                cls.FAILED, cls.MISSING)


L0_PASSING_STATUSES: Tuple[str, ...] = L0CoverageStatus.passing_for_domain_complete()
L0_STATUS_DOMAIN_COMPLETE_BLOCKERS: Tuple[str, ...] = L0CoverageStatus.blocks_domain_complete()



# ---------------------------------------------------------------------------
# L1 -- five exclusive medical dispositions (matrix §3.2, §3.3)
# ---------------------------------------------------------------------------

# NOTE: the boundary token must be a distinct string; see below.


class L1Disposition:
    """Medical evaluation disposition -- exactly one per EvaluationUnit.

    Five exclusive values (matrix §3.3): ``positive``, ``negative``,
    ``boundary``, ``not_applicable``, ``not_evaluable``.  "Non-problem" is not
    a disposition; it is ``negative`` + counterevidence + adjudication
    rationale.
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"

    ALL: Tuple[str, ...] = (
        POSITIVE, NEGATIVE, BOUNDARY, NOT_APPLICABLE, NOT_EVALUABLE,
    )

    @classmethod
    def is_exclusive_member(cls, value: str) -> bool:
        return value in cls.ALL

    @classmethod
    def is_evaluable(cls, value: str) -> bool:
        """A disposition that represents a completed medical evaluation.

        ``not_applicable`` is treated as evaluable (the unit was assessed and
        found out of scope with authority); ``not_evaluable`` is not.
        """
        return value in (cls.POSITIVE, cls.NEGATIVE, cls.BOUNDARY,
                         cls.NOT_APPLICABLE)


L1_DISPOSITIONS: Tuple[str, ...] = L1Disposition.ALL


# ---------------------------------------------------------------------------
# L1b -- three multi-valued evidence polarities (matrix §3.2, §3.3)
# ---------------------------------------------------------------------------

class L1bEvidencePolarity:
    """Evidence polarity relative to an EvaluationUnit, clue, or risk.

    Multi-valued (set-valued): a unit can carry ``supporting`` AND
    ``counterevidence`` at the same time.  Counterevidence is not a sixth L1
    disposition and may coexist with negative, positive, or boundary (matrix
    §3.2).
    """

    SUPPORTING = "supporting"
    COUNTEREVIDENCE = "counterevidence"
    CONTEXT = "context"

    ALL: Tuple[str, ...] = (SUPPORTING, COUNTEREVIDENCE, CONTEXT)

    @classmethod
    def is_member(cls, value: str) -> bool:
        return value in cls.ALL


L1B_POLARITIES: Tuple[str, ...] = L1bEvidencePolarity.ALL
# Alias kept for clarity at the module surface.
L1B_EVIDENCE_POLARITIES = L1B_POLARITIES


# ---------------------------------------------------------------------------
# L2 -- four separately-counted domain object types (matrix §3.2, §3.4)
# ---------------------------------------------------------------------------

class L2ObjectType:
    """L2 domain objects, counted separately and never inter-derived.

    Source records, unverified clue candidates, established risk instances,
    and Query drafts each have their own counter.  Candidate clues must never
    enter the recorded source-record count, and Query counts must not enter
    the risk count (matrix §3.4 invariants).
    """

    SOURCE_RECORD = "source_record"
    RISK_CANDIDATE = "risk_candidate"
    RISK_INSTANCE = "risk_instance"
    QUERY_DRAFT = "query_draft"

    ALL: Tuple[str, ...] = (SOURCE_RECORD, RISK_CANDIDATE,
                            RISK_INSTANCE, QUERY_DRAFT)


L2_COUNTED_TYPES: Tuple[str, ...] = L2ObjectType.ALL


# ---------------------------------------------------------------------------
# L3 -- risk lifecycle authority (matrix §3.2, §3.6)
# ---------------------------------------------------------------------------
#
# R2 ``RiskLifecycle`` / ``RiskLifecycleState`` is the sole lifecycle
# authority.  ``L3RiskStateRef`` IS the frozen R2 ``RiskLifecycleState``
# class (an identity alias), not a copy.  R4 never owns lifecycle
# transitions; lifecycle behavior must come from R2.  This guarantees that
# any future R2 lifecycle change is reflected without divergence.

L3RiskStateRef = _R2RiskLifecycleState
"""L3 risk-state authority -- the frozen R2 ``RiskLifecycleState`` class itself.

Use ``L3RiskStateRef`` to reference R2 lifecycle state constants (e.g.
``L3RiskStateRef.ESTABLISHED``, ``L3RiskStateRef.terminal_states()``).  R4
adds no state constants of its own.
"""

L3_TERMINAL_STATES: Tuple[str, ...] = _R2RiskLifecycleState.terminal_states()

RiskCandidate = _R2RiskCandidate
"""R2 ``RiskCandidate`` -- the unverified risk clue class (L2 risk_candidate).

Re-exported on the neutral contract surface so the frozen
``RiskDomainUnitResult`` Protocol can type its ``r2_candidates`` field with
the exact public R2 type instead of ``Any`` (frozen D02 contract §2).
R4 holds no candidate type of its own.
"""


# ---------------------------------------------------------------------------
# Monitoring priority (matrix §3.5) -- neutral domain-shared surface
# ---------------------------------------------------------------------------
#
# These constants live on the neutral common surface (frozen D02 contract
# §2): the lifecycle adapter reads monitoring priority off any
# ``RiskDomainUnitResult`` without importing a domain-specific result type,
# and every concrete domain result (D01 ``AEMHUnitResult``, D02 CM result)
# projects the same token here.  ``aemh.py`` re-exports them for backward
# compatibility.

MONITORING_PRIORITY_HIGH = "high"
MONITORING_PRIORITY_MEDIUM = "medium"
MONITORING_PRIORITY_LOW = "low"
MONITORING_PRIORITY_UNKNOWN = "unknown"

#: Canonical ordering of the four monitoring-priority tiers.
MONITORING_PRIORITIES: Tuple[str, ...] = (
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_UNKNOWN,
)

#: Validation tuple used by concrete domain results to guard their
#: ``monitoring_priority`` field.
VALID_MONITORING_PRIORITIES: Tuple[str, ...] = MONITORING_PRIORITIES


# ---------------------------------------------------------------------------
# Canonical hashing (deterministic, sorted-key JSON + SHA-256)
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class HashingError(Exception):
    """Canonical hashing violation."""


def _json_plain(obj: Any) -> Any:
    """Convert Mapping/tuple/list/frozenset/set/dataclass to plain JSON-able.

    Sets/frozensets are sorted so hash input is input-order independent.
    """
    if isinstance(obj, Mapping):
        return {k: _json_plain(obj[k]) for k in obj}
    if isinstance(obj, (list, tuple)):
        return [_json_plain(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        # Sort mixed-type sets deterministically by canonical string key.
        members: List[Any] = list(obj)
        try:
            members_sorted = sorted(members)
        except TypeError:
            members_sorted = sorted(members, key=lambda v: json.dumps(
                _json_plain(v), sort_keys=True, ensure_ascii=False,
                allow_nan=False))
        return [_json_plain(v) for v in members_sorted]
    # dataclasses without slots: convert via __dict__-free path.
    if hasattr(obj, "__dataclass_fields__"):
        return {f: _json_plain(getattr(obj, f))
                for f in obj.__dataclass_fields__}
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    raise HashingError(
        f"unsupported leaf type {type(obj).__name__}: {obj!r}")


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8, no NaN.

    This mirrors the R2/R3 canonicalization contract exactly so hashes are
    comparable across the frozen layers without cross-importing.
    """
    return json.dumps(_json_plain(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(obj: Any) -> str:
    """Content address of any JSON-able object (sha256 of canonical JSON)."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class CoverageValidationError(Exception):
    """A value object failed invariant validation."""


class UnitJoinError(CoverageValidationError):
    """An EvaluationUnit evidence/candidate/risk/query join invariant failed."""




# ---------------------------------------------------------------------------
# EvaluationUnit canonical hash dimensions (matrix §3.4)
# ---------------------------------------------------------------------------
#
# unit_id = hash(
#   project_id, domain_id, scope_type, scope_key,
#   normalized_concept_or_rule_item, temporal_window,
#   rule_or_knowledge_lineage, unit_algorithm_version
# )
#
# The eight dimensions are frozen.  Any dimension change MUST change unit_id.

_UNIT_HASH_DIMENSIONS: Tuple[str, ...] = (
    "project_id",
    "domain_id",
    "scope_type",
    "scope_key",
    "normalized_concept_or_rule_item",
    "temporal_window",
    "rule_or_knowledge_lineage",
    "unit_algorithm_version",
)


def _validate_nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageValidationError(
            f"{field_name} is required and must be a non-empty string")
    return value


def _validate_optional_str(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise CoverageValidationError(f"{field_name} must be a string or None")
    return value


def _freeze_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise CoverageValidationError(
            f"{field_name} must be a sequence, not a string")
    try:
        result: Tuple[str, ...] = tuple(value)
    except TypeError:
        raise CoverageValidationError(f"{field_name} must be iterable")
    for item in result:
        if not isinstance(item, str):
            raise CoverageValidationError(
                f"{field_name} members must be strings, got {type(item).__name__}")
    return result


def _canonical_sorted_tuple(value: Sequence[str]) -> Tuple[str, ...]:
    """Return a deterministically-sorted tuple of strings."""
    return tuple(sorted(value))


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceLocator:
    """Row-level source locator for evidence and unit provenance.

    A source locator binds a finding to an accepted snapshot, a source table
    semantic, and a row-level address (record id + optional column/anchor).
    No fixed table name is hardcoded; ``table_semantic`` is a semantic role
    from the active mapping, not an SDTM domain name (matrix §3.6, §4 D01).
    """

    snapshot_id: str
    source_revision_id: str
    table_semantic: str          # semantic role, e.g. "reported_ae"; never a fixed SDTM name
    record_id: str
    column_or_anchor: str = ""
    raw_payload_hash: str = ""   # optional content hash of the raw row bytes

    def __post_init__(self) -> None:
        _validate_nonempty(self.snapshot_id, "SourceLocator.snapshot_id")
        _validate_nonempty(self.source_revision_id,
                           "SourceLocator.source_revision_id")
        _validate_nonempty(self.table_semantic, "SourceLocator.table_semantic")
        _validate_nonempty(self.record_id, "SourceLocator.record_id")
        _validate_optional_str(self.column_or_anchor,
                               "SourceLocator.column_or_anchor")
        if self.raw_payload_hash:
            if not _SHA256_RE.match(self.raw_payload_hash):
                raise CoverageValidationError(
                    "SourceLocator.raw_payload_hash must be a 64-char "
                    "lowercase hex SHA-256 digest")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "source_revision_id": self.source_revision_id,
            "table_semantic": self.table_semantic,
            "record_id": self.record_id,
            "column_or_anchor": self.column_or_anchor,
            "raw_payload_hash": self.raw_payload_hash,
        }

    def content_digest(self) -> str:
        return content_hash(self.canonical_payload())

    def locator_id(self) -> str:
        """Deterministic locator id derived from the content digest."""
        return f"loc-{self.content_digest()}"


@dataclass(frozen=True)
class EvidenceItem:
    """One piece of evidence bound to a polarity, provenance, and locator.

    An evidence item carries an L1b polarity (supporting/counterevidence/
    context), a row-level source locator, a rule/knowledge/mapping lineage,
    and optional uncertainty.  It is never a reported source fact on its own;
    it is an evaluation-time assertion (matrix §3.6).
    """

    evidence_id: str
    polarity: str                # L1bEvidencePolarity member
    locator: SourceLocator
    evidence_role: str = ""      # e.g. "reported_ae", "lab_finding" (semantic role)
    rule_lineage: str = ""       # versioned rule/knowledge/mapping lineage
    uncertainty_note: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise CoverageValidationError(
                "EvidenceItem.evidence_id is required")
        if not L1bEvidencePolarity.is_member(self.polarity):
            raise CoverageValidationError(
                f"EvidenceItem.polarity={self.polarity!r} is not a valid L1b "
                f"polarity {L1B_POLARITIES}")
        if not isinstance(self.locator, SourceLocator):
            raise CoverageValidationError(
                "EvidenceItem.locator must be a SourceLocator")
        _validate_optional_str(self.evidence_role, "EvidenceItem.evidence_role")
        _validate_optional_str(self.rule_lineage, "EvidenceItem.rule_lineage")
        _validate_optional_str(self.uncertainty_note,
                               "EvidenceItem.uncertainty_note")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "polarity": self.polarity,
            "locator": self.locator.canonical_payload(),
            "evidence_role": self.evidence_role,
            "rule_lineage": self.rule_lineage,
            "uncertainty_note": self.uncertainty_note,
        }


@dataclass(frozen=True)
class EvaluationUnit:
    """The smallest versioned denominator unit of medical evaluation.

    ``unit_id`` is a deterministic canonical hash over the eight frozen
    dimensions (matrix §3.4).  Units are immutable; a changed dimension
    produces a different ``unit_id`` and therefore a different expected-set.
    """

    project_id: str
    domain_id: str
    scope_type: str              # subject | site | center | project | domain
    scope_key: str               # e.g. subject ref or center id
    normalized_concept_or_rule_item: str
    temporal_window: str         # versioned temporal window descriptor
    rule_or_knowledge_lineage: str
    unit_algorithm_version: str
    unit_id: str = ""            # if empty, derived from the dimensions

    def __post_init__(self) -> None:
        _validate_nonempty(self.project_id, "EvaluationUnit.project_id")
        _validate_nonempty(self.domain_id, "EvaluationUnit.domain_id")
        _validate_nonempty(self.scope_type, "EvaluationUnit.scope_type")
        _validate_nonempty(self.scope_key, "EvaluationUnit.scope_key")
        _validate_nonempty(self.normalized_concept_or_rule_item,
                           "EvaluationUnit.normalized_concept_or_rule_item")
        _validate_nonempty(self.temporal_window,
                           "EvaluationUnit.temporal_window")
        _validate_nonempty(self.rule_or_knowledge_lineage,
                           "EvaluationUnit.rule_or_knowledge_lineage")
        _validate_nonempty(self.unit_algorithm_version,
                           "EvaluationUnit.unit_algorithm_version")
        expected = self.compute_unit_id()
        if self.unit_id and self.unit_id != expected:
            raise CoverageValidationError(
                f"EvaluationUnit.unit_id {self.unit_id!r} does not match the "
                f"deterministic hash {expected!r}")
        object.__setattr__(self, "unit_id", expected)

    def canonical_dimensions(self) -> Dict[str, str]:
        """The eight frozen hash dimensions, in canonical key order."""
        return {
            "project_id": self.project_id,
            "domain_id": self.domain_id,
            "scope_type": self.scope_type,
            "scope_key": self.scope_key,
            "normalized_concept_or_rule_item":
                self.normalized_concept_or_rule_item,
            "temporal_window": self.temporal_window,
            "rule_or_knowledge_lineage": self.rule_or_knowledge_lineage,
            "unit_algorithm_version": self.unit_algorithm_version,
        }

    def compute_unit_id(self) -> str:
        return "unit-" + content_hash(self.canonical_dimensions())

    def requires_rule_lineage(self) -> bool:
        return bool(self.rule_or_knowledge_lineage)


def unit_id_hash(
    project_id: str,
    domain_id: str,
    scope_type: str,
    scope_key: str,
    normalized_concept_or_rule_item: str,
    temporal_window: str,
    rule_or_knowledge_lineage: str,
    unit_algorithm_version: str,
) -> str:
    """Compute a deterministic EvaluationUnit id from the eight dimensions."""
    return EvaluationUnit(
        project_id=project_id,
        domain_id=domain_id,
        scope_type=scope_type,
        scope_key=scope_key,
        normalized_concept_or_rule_item=normalized_concept_or_rule_item,
        temporal_window=temporal_window,
        rule_or_knowledge_lineage=rule_or_knowledge_lineage,
        unit_algorithm_version=unit_algorithm_version,
    ).unit_id


# ---------------------------------------------------------------------------
# L2 reference stubs (full L2 objects are worker_02/worker_03 territory)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceRecordRef:
    """Reference to an accepted source record counted under L2 source_record."""

    record_id: str
    locator: SourceLocator

    def __post_init__(self) -> None:
        _validate_nonempty(self.record_id, "SourceRecordRef.record_id")
        if not isinstance(self.locator, SourceLocator):
            raise CoverageValidationError(
                "SourceRecordRef.locator must be a SourceLocator")
        if self.record_id != self.locator.record_id:
            raise CoverageValidationError(
                "SourceRecordRef.record_id must match locator.record_id")


@dataclass(frozen=True)
class RiskCandidateRef:
    """Reference to an unverified risk clue counted under L2 risk_candidate.

    Candidate clues are never recorded source facts (matrix §3.4, §3.6).
    """

    candidate_id: str
    risk_identity_id: str = ""
    locator: Optional[SourceLocator] = None

    def __post_init__(self) -> None:
        _validate_nonempty(self.candidate_id, "RiskCandidateRef.candidate_id")
        _validate_optional_str(self.risk_identity_id,
                               "RiskCandidateRef.risk_identity_id")
        if self.locator is not None and not isinstance(self.locator,
                                                       SourceLocator):
            raise CoverageValidationError(
                "RiskCandidateRef.locator must be a SourceLocator or None")


@dataclass(frozen=True)
class RiskInstanceRef:
    """Reference to an established risk counted under L2 risk_instance.

    ``risk_state`` is an explicit R2 lifecycle reference (L3RiskStateRef),
    NOT an L0/L1 status (matrix §3.2, §3.6).
    """

    risk_instance_id: str
    risk_identity_id: str
    risk_state: str              # L3RiskStateRef member

    def __post_init__(self) -> None:
        _validate_nonempty(self.risk_instance_id,
                           "RiskInstanceRef.risk_instance_id")
        _validate_nonempty(self.risk_identity_id,
                           "RiskInstanceRef.risk_identity_id")
        if self.risk_state not in L3RiskStateRef.all_states():
            raise CoverageValidationError(
                f"RiskInstanceRef.risk_state={self.risk_state!r} is not a "
                f"valid R2 lifecycle state {L3RiskStateRef.all_states()}")


@dataclass(frozen=True)
class QueryDraftRef:
    """Reference to a three-part Query draft counted under L2 query_draft.

    A Query is basis + finding + action, linked to source/EvaluationUnit/
    candidate or risk.  It never means "sent" (matrix §3.4, §5.1).
    """

    query_id: str
    unit_id: str
    basis: str
    finding: str
    action: str
    source_locator_ids: Tuple[str, ...]
    linked_candidate_id: str = ""
    linked_risk_instance_id: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.query_id, "QueryDraftRef.query_id")
        _validate_nonempty(self.unit_id, "QueryDraftRef.unit_id")
        _validate_nonempty(self.basis, "QueryDraftRef.basis")
        _validate_nonempty(self.finding, "QueryDraftRef.finding")
        _validate_nonempty(self.action, "QueryDraftRef.action")
        locator_ids = _freeze_tuple(
            self.source_locator_ids, "QueryDraftRef.source_locator_ids")
        if not locator_ids:
            raise CoverageValidationError(
                "QueryDraftRef must link at least one source locator")
        if any(not locator_id.strip() for locator_id in locator_ids):
            raise CoverageValidationError(
                "QueryDraftRef.source_locator_ids members must be non-empty")
        if len(set(locator_ids)) != len(locator_ids):
            raise CoverageValidationError(
                "QueryDraftRef.source_locator_ids contains duplicates")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted_tuple(locator_ids))
        if not self.linked_candidate_id and not self.linked_risk_instance_id:
            raise CoverageValidationError(
                "QueryDraftRef must link to a candidate or a risk instance "
                "(matrix §3.4: every Query must associate with a clue or risk)")
        _validate_optional_str(self.linked_candidate_id,
                               "QueryDraftRef.linked_candidate_id")
        _validate_optional_str(self.linked_risk_instance_id,
                               "QueryDraftRef.linked_risk_instance_id")


# ---------------------------------------------------------------------------
# UnitEvaluation -- one L1 disposition + L1b evidence set + L2 joins
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UnitEvaluation:
    """The medical evaluation of one EvaluationUnit.

    Exactly one L1 disposition (matrix §3.3) plus a set of L1b evidence
    polarities and the L2 object references joined to this unit.  Join
    invariants are validated at construction time so a malformed evaluation
    cannot enter the ledger (matrix §3.4 invariants).
    """

    unit_id: str
    l0_status: str               # L0CoverageStatus member
    l1_disposition: str          # L1Disposition member (exactly one)
    l1b_polarities: Tuple[str, ...] = ()   # subset of L1bEvidencePolarity
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    provenance_snapshot_id: str = ""
    provenance_rule_lineage: str = ""
    not_evaluable_reason: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.unit_id, "UnitEvaluation.unit_id")
        if self.l0_status not in L0CoverageStatus.ALL_STATUSES:
            raise CoverageValidationError(
                f"UnitEvaluation.l0_status={self.l0_status!r} is not a valid "
                f"L0 coverage status")
        if not L1Disposition.is_exclusive_member(self.l1_disposition):
            raise CoverageValidationError(
                f"UnitEvaluation.l1_disposition={self.l1_disposition!r} is "
                f"not one of the five exclusive L1 dispositions "
                f"{L1_DISPOSITIONS}")
        # L1b polarities: subset check, canonical sort.
        polarities: List[str] = []
        seen: Set[str] = set()
        for pol in self.l1b_polarities:
            if not L1bEvidencePolarity.is_member(pol):
                raise CoverageValidationError(
                    f"UnitEvaluation.l1b_polarities contains invalid "
                    f"polarity {pol!r}")
            if pol in seen:
                continue
            seen.add(pol)
            polarities.append(pol)
        object.__setattr__(self, "l1b_polarities",
                           tuple(sorted(polarities)))
        # Tuple validation for reference containers.
        for ref_tuple, name, expected_type in (
            (self.evidence, "evidence", EvidenceItem),
            (self.source_record_refs, "source_record_refs", SourceRecordRef),
            (self.risk_candidate_refs, "risk_candidate_refs", RiskCandidateRef),
            (self.risk_instance_refs, "risk_instance_refs", RiskInstanceRef),
            (self.query_refs, "query_refs", QueryDraftRef),
        ):
            checked: List[Any] = []
            for item in ref_tuple:
                if not isinstance(item, expected_type):
                    raise CoverageValidationError(
                        f"UnitEvaluation.{name} entries must be "
                        f"{expected_type.__name__}, got "
                        f"{type(item).__name__}")
                checked.append(item)
            object.__setattr__(self, name, tuple(checked))
        # Provenance: positive/boundary and every evaluated unit need a
        # snapshot binding.  L1 not_evaluable may omit it (that is the gap).
        _validate_optional_str(self.provenance_snapshot_id,
                               "UnitEvaluation.provenance_snapshot_id")
        _validate_optional_str(self.provenance_rule_lineage,
                               "UnitEvaluation.provenance_rule_lineage")
        _validate_optional_str(self.not_evaluable_reason,
                               "UnitEvaluation.not_evaluable_reason")
        self._validate_join_invariants()

    def _validate_join_invariants(self) -> None:
        """Enforce the L1↔L2 join invariants (matrix §3.4)."""
        # Each positive unit must carry at least one current clue candidate
        # or an active/ambiguous risk instance.
        if self.l1_disposition == L1Disposition.POSITIVE:
            active_risks = [
                r for r in self.risk_instance_refs
                if r.risk_state in L3RiskStateRef.active_states()
            ]
            if not self.risk_candidate_refs and not active_risks:
                raise UnitJoinError(
                    f"positive unit {self.unit_id!r} must associate with at "
                    f"least one risk_candidate or an active risk instance "
                    f"(matrix §3.4)")
        # Every Query must link this EvaluationUnit, one or more reachable
        # source locators, and a candidate or risk.  QueryDraftRef enforces
        # presence; this join validates exact membership on the unit.
        available_locator_ids = {
            ref.locator.locator_id() for ref in self.source_record_refs
        }
        available_locator_ids.update(
            item.locator.locator_id() for item in self.evidence
        )
        available_locator_ids.update(
            ref.locator.locator_id()
            for ref in self.risk_candidate_refs
            if ref.locator is not None
        )
        for q in self.query_refs:
            if q.unit_id != self.unit_id:
                raise UnitJoinError(
                    f"unit {self.unit_id!r} Query {q.query_id!r} links "
                    f"different unit {q.unit_id!r}")
            unreachable = sorted(
                set(q.source_locator_ids) - available_locator_ids)
            if unreachable:
                raise UnitJoinError(
                    f"unit {self.unit_id!r} Query {q.query_id!r} links "
                    f"source locator(s) not present on unit: {unreachable}")
            if q.linked_candidate_id and not any(
                c.candidate_id == q.linked_candidate_id
                for c in self.risk_candidate_refs
            ):
                raise UnitJoinError(
                    f"unit {self.unit_id!r} Query {q.query_id!r} links "
                    f"candidate {q.linked_candidate_id!r} not present on unit")
            if q.linked_risk_instance_id and not any(
                r.risk_instance_id == q.linked_risk_instance_id
                for r in self.risk_instance_refs
            ):
                raise UnitJoinError(
                    f"unit {self.unit_id!r} Query {q.query_id!r} links risk "
                    f"{q.linked_risk_instance_id!r} not present on unit")
        # Provenance requirement for evaluated (non-not_evaluable) units.
        if self.l1_disposition != L1Disposition.NOT_EVALUABLE:
            if not self.provenance_snapshot_id:
                raise UnitJoinError(
                    f"unit {self.unit_id!r} disposition "
                    f"{self.l1_disposition!r} requires provenance_snapshot_id")
        # Positive/boundary also need rule lineage when the unit requires it.
        if self.l1_disposition in (L1Disposition.POSITIVE,
                                   L1Disposition.BOUNDARY):
            if not self.provenance_rule_lineage:
                raise UnitJoinError(
                    f"unit {self.unit_id!r} disposition "
                    f"{self.l1_disposition!r} requires provenance_rule_lineage")

    def evidence_polarities(self) -> Tuple[str, ...]:
        return self.l1b_polarities

    def has_counterevidence(self) -> bool:
        return L1bEvidencePolarity.COUNTEREVIDENCE in self.l1b_polarities

    def count_l2(self, object_type: str) -> int:
        if object_type == L2ObjectType.SOURCE_RECORD:
            return len(self.source_record_refs)
        if object_type == L2ObjectType.RISK_CANDIDATE:
            return len(self.risk_candidate_refs)
        if object_type == L2ObjectType.RISK_INSTANCE:
            return len(self.risk_instance_refs)
        if object_type == L2ObjectType.QUERY_DRAFT:
            return len(self.query_refs)
        raise CoverageValidationError(
            f"unknown L2 object type {object_type!r}")


# ---------------------------------------------------------------------------
# Neutral candidate identity accessors (matrix §3.6, frozen D02 §2)
# ---------------------------------------------------------------------------
#
# These read the public R2 ``RiskCandidate.detail`` dict that every R4
# domain engine writes (see ``_r4_identity_detail`` in ``aemh.py`` for the
# D01 writer; D02 writes the same keys).  They are intentionally neutral:
# the lifecycle adapter calls them on any candidate without importing a
# domain-specific result type.  Each returns '' or [] when the candidate
# carries no R4 identity detail (e.g. an externally constructed candidate),
# leaving the caller to fail closed on the empty value.

def candidate_identity_classifier(candidate: Any) -> str:
    """Return the public R2 identity classifier stored on the candidate
    detail, or '' when absent.  The caller must fail closed on empty
    (no generic signal_type fallback)."""
    return str(candidate.detail.get("classifier", ""))


def candidate_identity_scope(candidate: Any) -> List[str]:
    """Return the public R2 identity scope stored on the candidate detail
    as a list, or [] when absent."""
    return list(candidate.detail.get("scope", []))


def candidate_stable_core(candidate: Any) -> str:
    """Return the stable-core string (concept + signal + source event)
    stored on the candidate detail, or '' when absent."""
    return str(candidate.detail.get("stable_core", ""))


def candidate_lineage_fingerprint(candidate: Any) -> str:
    """Return the lineage-fingerprint string stored on the candidate
    detail, or '' when absent."""
    return str(candidate.detail.get("lineage_fingerprint", ""))


def _candidate_strict_bool(candidate: Any, key: str) -> bool:
    """Strict boolean reader for a frozen candidate-detail flag.

    Frozen D04 contract §8.1/§10: ``rights_or_safety_critical`` and
    ``machine_close_forbidden`` are frozen boolean keys on the public R2
    ``RiskCandidate.detail`` dict.  Missing → ``False``; a literal bool is
    returned unchanged; any *present* non-bool (including ``int`` 0/1,
    strings, ``None``, lists) fails closed with the public
    :class:`CoverageValidationError` family so a malformed producer value
    can never be coerced into a less-conservative reading.
    """
    value = candidate.detail.get(key, False)
    if type(value) is not bool:
        raise CoverageValidationError(
            f"candidate detail {key!r} must be a literal bool when present, "
            f"got {type(value).__name__}: {value!r}")
    return value


def candidate_rights_or_safety_critical(candidate: Any) -> bool:
    """Strict boolean read of the frozen ``rights_or_safety_critical``
    candidate-detail flag (frozen D04 §8.1, §10.4).

    Missing → ``False``; literal bool → returned as-is; any present
    non-bool → :class:`CoverageValidationError` (fail closed).
    """
    return _candidate_strict_bool(candidate, "rights_or_safety_critical")


def candidate_machine_close_forbidden(candidate: Any) -> bool:
    """Strict boolean read of the frozen ``machine_close_forbidden``
    candidate-detail flag (frozen D04 §8.1, §10.4).

    Missing → ``False``; literal bool → returned as-is; any present
    non-bool → :class:`CoverageValidationError` (fail closed).
    """
    return _candidate_strict_bool(candidate, "machine_close_forbidden")


# ---------------------------------------------------------------------------
# RiskDomainUnitResult -- neutral lifecycle-input Protocol (frozen D02 §2)
# ---------------------------------------------------------------------------
#
# The frozen eight fields are the lifecycle-input contract only -- not a
# complete ledger object.  Each concrete domain result (D01
# ``AEMHUnitResult``, D02 CM result) must ALSO materialize a full
# ``UnitEvaluation`` (evidence/source/candidate/risk/Query refs, snapshot
# provenance, rule lineage) to enter the ``CoverageLedger``; this Protocol
# captures just what ``R4LifecycleAdapter`` needs for candidate-identity
# pre-checks and priority projection.  ``monitoring_priority`` is read off
# the result so the adapter never imports a domain-specific grading type.

@runtime_checkable
class RiskDomainUnitResult(Protocol):
    """Neutral structural protocol for a per-domain unit result that the
    R4 lifecycle adapter consumes.

    Frozen fields (frozen D02 contract §2)::

        unit_id: str
        subject_ref: str
        l1_disposition: str
        monitoring_priority: str
        r2_candidates: Sequence[RiskCandidate]
        risk_candidate_refs: Sequence[RiskCandidateRef]
        risk_instance_refs: Sequence[RiskInstanceRef]
        not_evaluable_reason: str

    ``evidence``/``source_record_refs``/``query_refs``/``boundary_reason``/
    ``journey_markers`` are domain-result and ledger/projection fields and
    do not participate in the lifecycle candidate-identity pre-check, so
    they are intentionally absent from this Protocol.
    """

    @property
    def unit_id(self) -> str: ...

    @property
    def subject_ref(self) -> str: ...

    @property
    def l1_disposition(self) -> str: ...

    @property
    def monitoring_priority(self) -> str: ...

    @property
    def r2_candidates(self) -> Sequence[RiskCandidate]: ...

    @property
    def risk_candidate_refs(self) -> Sequence[RiskCandidateRef]: ...

    @property
    def risk_instance_refs(self) -> Sequence[RiskInstanceRef]: ...

    @property
    def not_evaluable_reason(self) -> str: ...


# ---------------------------------------------------------------------------
# CrossDomainEvidenceRef -- neutral read-only source reference (D02 §3.3)
# ---------------------------------------------------------------------------
#
# A neutral, immutable, read-only source reference -- NOT a
# candidate/risk/Query.  It MUST NOT carry consumer candidate/risk/Query id,
# consumer L1 disposition, or any lifecycle state.  A producer domain (D02)
# emits it; a consumer domain (D01) may turn it into its own
# ``SemanticRecord(role=cm_indication)`` after consuming it.

@dataclass(frozen=True)
class CrossDomainEvidenceRef:
    """Neutral immutable read-only cross-domain evidence reference.

    Carries only producer provenance and a content address; it never holds
    a consumer candidate/risk/Query id, consumer L1 disposition, or
    lifecycle state (frozen D02 contract §3.3).  ``content_hash`` is the
    canonical SHA-256 of ``stable source event key + evidence_role +
    claim_scope + sorted context_payload`` and excludes snapshot/revision
    id; the full locator is retained separately for source drill-back.
    """

    evidence_ref_id: str
    producer_domain: str
    consumer_domain: str
    evidence_role: str
    source_locator: SourceLocator
    producer_unit_id: str
    content_hash: str
    claim_scope: str = ""
    context_payload: Tuple[Tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.evidence_ref_id,
                           "CrossDomainEvidenceRef.evidence_ref_id")
        _validate_nonempty(self.producer_domain,
                           "CrossDomainEvidenceRef.producer_domain")
        _validate_nonempty(self.consumer_domain,
                           "CrossDomainEvidenceRef.consumer_domain")
        if self.producer_domain == self.consumer_domain:
            raise CoverageValidationError(
                "CrossDomainEvidenceRef producer_domain must differ from "
                "consumer_domain")
        _validate_nonempty(self.evidence_role,
                           "CrossDomainEvidenceRef.evidence_role")
        if not isinstance(self.source_locator, SourceLocator):
            raise CoverageValidationError(
                "CrossDomainEvidenceRef.source_locator must be a SourceLocator")
        _validate_nonempty(self.producer_unit_id,
                           "CrossDomainEvidenceRef.producer_unit_id")
        if not _SHA256_RE.match(self.content_hash):
            raise CoverageValidationError(
                "CrossDomainEvidenceRef.content_hash must be a 64-char "
                "lowercase hex SHA-256 digest")
        _validate_optional_str(self.claim_scope,
                               "CrossDomainEvidenceRef.claim_scope")
        # Validate context_payload entries, then freeze into canonical
        # key-sorted order so the stored payload is order-independent and
        # the canonical hash is reproducible from the frozen fields alone.
        seen_keys: Set[str] = set()
        validated: List[Tuple[str, Any]] = []
        for item in self.context_payload:
            if not isinstance(item, tuple) or len(item) != 2:
                raise CoverageValidationError(
                    "CrossDomainEvidenceRef.context_payload entries must be "
                    "(key, value) tuples")
            key, value = item
            if not isinstance(key, str) or not key:
                raise CoverageValidationError(
                    "CrossDomainEvidenceRef.context_payload keys must be "
                    "non-empty str")
            if key in seen_keys:
                raise CoverageValidationError(
                    f"CrossDomainEvidenceRef.context_payload duplicate key "
                    f"{key!r}")
            seen_keys.add(key)
            validated.append((key, value))
        object.__setattr__(
            self, "context_payload", tuple(sorted(validated, key=lambda kv: kv[0])))
        # Enforce that the supplied content_hash is the canonical hash of
        # the determinant fields (frozen D02 §3.3).  A well-formed but
        # non-canonical 64-char hash is rejected: an immutable ref must not
        # be constructed with a mismatched content address.
        canonical = self.compute_content_hash()
        if self.content_hash != canonical:
            raise CoverageValidationError(
                "CrossDomainEvidenceRef.content_hash is not the canonical "
                "hash of its determinant fields (stable source event key + "
                "evidence_role + claim_scope + sorted context_payload); "
                f"got {self.content_hash!r}, expected {canonical!r}")

    def canonical_payload(self) -> Dict[str, Any]:
        """Payload that determines the content address (excludes the full
        locator/snapshot/revision id; those live on ``source_locator`` for
        drill-back only)."""
        return {
            "stable_source_event_key": _stable_event_key(self.source_locator),
            "evidence_role": self.evidence_role,
            "claim_scope": self.claim_scope,
            "context_payload": [
                [k, v] for k, v in sorted(self.context_payload)],
        }

    def compute_content_hash(self) -> str:
        """Recompute the canonical content_hash from the payload."""
        return content_hash(self.canonical_payload())

    def verify_content_hash(self) -> bool:
        """True when the stored ``content_hash`` equals the recomputed
        canonical hash."""
        return self.content_hash == self.compute_content_hash()


def _stable_event_key(locator: SourceLocator) -> str:
    """Stable source event key = ``table_semantic:record_id`` (excludes
    snapshot/revision id).  Frozen D02 contract §3.3: the dedup/content
    hash key uses the stable source event key, never the full locator."""
    return f"{locator.table_semantic}:{locator.record_id}"


def cross_domain_evidence_content_hash(
    *,
    source_locator: SourceLocator,
    evidence_role: str,
    claim_scope: str,
    context_payload: Optional[Mapping[str, Any]] = None,
) -> str:
    """Compute the canonical ``CrossDomainEvidenceRef.content_hash`` from
    its determinant fields (frozen D02 §3.3).

    The hash is the SHA-256 of the canonical JSON of ``stable source event
    key + evidence_role + claim_scope + sorted context_payload``, excluding
    snapshot/revision id.  A clinical-claim content change MUST yield a new
    hash.
    """
    payload = {
        "stable_source_event_key": _stable_event_key(source_locator),
        "evidence_role": evidence_role,
        "claim_scope": claim_scope,
        "context_payload": [] if context_payload is None else
            [[k, context_payload[k]] for k in sorted(context_payload)],
    }
    return content_hash(payload)
