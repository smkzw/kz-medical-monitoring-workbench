"""R4 coverage ledger -- expected-set, evaluation ledger, summary and the
fail-closed medical-completeness predicate.

This module builds on :mod:`mm_r4.contracts` (layer namespaces, value objects,
canonical hashing) and owns the expected-set ledger with its join/count
invariants (matrix §3.4, §6).  It is stdlib-only and does not touch R2
lifecycle or R3 normalization authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .contracts import (
    CoverageValidationError,
    EvaluationUnit,
    HashingError,
    L0_STATUS_DOMAIN_COMPLETE_BLOCKERS,
    L0CoverageStatus,
    L1_DISPOSITIONS,
    L1B_POLARITIES,
    L1Disposition,
    L2_COUNTED_TYPES,
    L2ObjectType,
    UnitEvaluation,
    content_hash,
)

__all__ = [
    "CoverageLedger",
    "CoverageSummary",
    "ExpectedSet",
    "expected_set_hash",
    "is_domain_complete",
    "LedgerError",
]


class LedgerError(CoverageValidationError):
    """The expected-set ledger rejected a duplicate/missing/unexpected/count
    contamination."""


# ---------------------------------------------------------------------------
# Expected-set hash (input-order independent) + ExpectedSet
# ---------------------------------------------------------------------------

def expected_set_hash(unit_ids: Sequence[str]) -> str:
    """Deterministic, input-order-independent hash of a set of unit ids.

    Duplicate unit ids are rejected: an expected-set must contain each unit
    exactly once (matrix §3.4: "each unit_id appears exactly once").
    """
    if isinstance(unit_ids, str):
        raise HashingError("expected_set_hash requires a sequence, not a string")
    seen: Set[str] = set()
    for uid in unit_ids:
        if not isinstance(uid, str) or not uid.strip():
            raise HashingError(
                "expected_set_hash unit ids must be non-empty strings")
        if uid in seen:
            raise HashingError(
                f"duplicate unit_id {uid!r} in expected set "
                f"(matrix §3.4: each unit_id appears exactly once)")
        seen.add(uid)
    # Sort so the hash is independent of input order.
    return "eset-" + content_hash(sorted(seen))


def _validate_nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageValidationError(
            f"{field_name} is required and must be a non-empty string")
    return value


def _canonical_sorted_tuple(value: Sequence[str]) -> Tuple[str, ...]:
    """Return a deterministically-sorted tuple of strings."""
    return tuple(sorted(value))


@dataclass(frozen=True)
class ExpectedSet:
    """The frozen expected-set of EvaluationUnits for one Run/domain.

    The set is content-addressed by ``expected_set_hash`` over the member
    ``unit_id`` values; construction validates uniqueness and consistency
    (matrix §3.4: expected units are generated from accepted snapshot +
    active mapping + applicability + frozen algorithm only).
    """

    expected_set_hash_value: str
    unit_ids: Tuple[str, ...]
    domain_id: str
    run_id: str
    expected_count: int

    def __post_init__(self) -> None:
        _validate_nonempty(self.expected_set_hash_value,
                           "ExpectedSet.expected_set_hash_value")
        _validate_nonempty(self.domain_id, "ExpectedSet.domain_id")
        _validate_nonempty(self.run_id, "ExpectedSet.run_id")
        frozen_ids = _canonical_sorted_tuple(self.unit_ids)
        object.__setattr__(self, "unit_ids", frozen_ids)
        recomputed = expected_set_hash(list(frozen_ids))
        if recomputed != self.expected_set_hash_value:
            raise CoverageValidationError(
                f"ExpectedSet hash mismatch: declared "
                f"{self.expected_set_hash_value!r} != recomputed "
                f"{recomputed!r}")
        if self.expected_count != len(frozen_ids):
            raise CoverageValidationError(
                f"ExpectedSet.expected_count={self.expected_count} != "
                f"len(unit_ids)={len(frozen_ids)} (matrix §3.4 count equation)")

    @classmethod
    def from_units(
        cls,
        units: Sequence[EvaluationUnit],
        domain_id: str,
        run_id: str,
    ) -> "ExpectedSet":
        unit_ids = [u.unit_id for u in units]
        return cls(
            expected_set_hash_value=expected_set_hash(unit_ids),
            unit_ids=tuple(unit_ids),
            domain_id=domain_id,
            run_id=run_id,
            expected_count=len(unit_ids),
        )

    def contains(self, unit_id: str) -> bool:
        return unit_id in self.unit_ids

    def count(self) -> int:
        return len(self.unit_ids)


# ---------------------------------------------------------------------------
# CoverageLedger -- the append-only evaluation ledger with invariants
# ---------------------------------------------------------------------------

@dataclass
class CoverageLedger:
    """Append-only ledger that reconciles expected units against evaluations.

    The ledger enforces the matrix §3.4 invariants at assignment time:

    * every unit_id appears exactly once (no duplicates);
    * no evaluation for a unit not in the expected-set;
    * no expected unit left without an evaluation at close;
    * the exact count equation
      ``expected_units = positive + negative + boundary + not_applicable +
      not_evaluable``;
    * L0 blocking statuses are tracked separately from L1;
    * L2 object counts (source/candidate/risk/query) are kept separate and
      never inter-derived.

    The ledger is mutable but append-only: once a unit is assigned it cannot
    be reassigned.  Call :meth:`close_and_summarize` to finalize and obtain a
    :class:`CoverageSummary`.
    """

    expected_set: ExpectedSet
    _evaluations: Dict[str, UnitEvaluation] = field(default_factory=dict)
    _closed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.expected_set, ExpectedSet):
            raise CoverageValidationError(
                "CoverageLedger.expected_set must be an ExpectedSet")

    # -- assignment --------------------------------------------------------

    def assign(self, evaluation: UnitEvaluation) -> None:
        if self._closed:
            raise LedgerError("ledger is closed; cannot assign more units")
        if not isinstance(evaluation, UnitEvaluation):
            raise LedgerError("assign requires a UnitEvaluation")
        uid = evaluation.unit_id
        if not self.expected_set.contains(uid):
            raise LedgerError(
                f"unexpected unit {uid!r}: not in expected-set "
                f"{self.expected_set.expected_set_hash_value!r} (matrix §3.4)")
        if uid in self._evaluations:
            raise LedgerError(
                f"duplicate unit {uid!r}: already assigned "
                f"(matrix §3.4: each unit_id appears exactly once)")
        self._evaluations[uid] = evaluation

    def close(self) -> None:
        """Finalize the ledger, enforcing the completeness invariants."""
        if self._closed:
            return
        expected = set(self.expected_set.unit_ids)
        assigned = set(self._evaluations.keys())
        missing = expected - assigned
        if missing:
            raise LedgerError(
                f"missing evaluations for {len(missing)} unit(s) "
                f"(matrix §3.4: every expected unit must receive exactly one "
                f"L1 disposition); first missing: {sorted(missing)[:3]}")
        self._validate_count_equation()
        self._closed = True

    def _validate_count_equation(self) -> None:
        counts: Dict[str, int] = {d: 0 for d in L1_DISPOSITIONS}
        for ev in self._evaluations.values():
            counts[ev.l1_disposition] += 1
        expected_total = self.expected_set.expected_count
        actual_total = sum(counts.values())
        if actual_total != expected_total:
            raise LedgerError(
                f"count equation violated: sum(L1)={actual_total} != "
                f"expected_units={expected_total}; breakdown={counts}")

    # -- queries -----------------------------------------------------------

    @property
    def is_closed(self) -> bool:
        return self._closed

    def assigned_count(self) -> int:
        return len(self._evaluations)

    def evaluation_for(self, unit_id: str) -> Optional[UnitEvaluation]:
        return self._evaluations.get(unit_id)

    def all_evaluations(self) -> Tuple[UnitEvaluation, ...]:
        return tuple(self._evaluations[uid]
                     for uid in self.expected_set.unit_ids
                     if uid in self._evaluations)

    def l1_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {d: 0 for d in L1_DISPOSITIONS}
        for ev in self._evaluations.values():
            counts[ev.l1_disposition] += 1
        return counts

    def l0_status_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s: 0 for s in L0CoverageStatus.ALL_STATUSES}
        for ev in self._evaluations.values():
            counts[ev.l0_status] += 1
        return counts

    def l1b_polarity_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {p: 0 for p in L1B_POLARITIES}
        for ev in self._evaluations.values():
            for pol in ev.l1b_polarities:
                counts[pol] += 1
        return counts

    def l2_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {t: 0 for t in L2_COUNTED_TYPES}
        for ev in self._evaluations.values():
            counts[L2ObjectType.SOURCE_RECORD] += ev.count_l2(
                L2ObjectType.SOURCE_RECORD)
            counts[L2ObjectType.RISK_CANDIDATE] += ev.count_l2(
                L2ObjectType.RISK_CANDIDATE)
            counts[L2ObjectType.RISK_INSTANCE] += ev.count_l2(
                L2ObjectType.RISK_INSTANCE)
            counts[L2ObjectType.QUERY_DRAFT] += ev.count_l2(
                L2ObjectType.QUERY_DRAFT)
        return counts

    def close_and_summarize(self) -> "CoverageSummary":
        self.close()
        l1 = self.l1_counts()
        l0 = self.l0_status_counts()
        l1b = self.l1b_polarity_counts()
        l2 = self.l2_counts()
        return CoverageSummary(
            expected_set_hash=self.expected_set.expected_set_hash_value,
            domain_id=self.expected_set.domain_id,
            run_id=self.expected_set.run_id,
            expected_units=self.expected_set.expected_count,
            assigned_units=self.assigned_count(),
            l1_counts=dict(l1),
            l0_status_counts=dict(l0),
            l1b_polarity_counts=dict(l1b),
            l2_counts=dict(l2),
        )


# ---------------------------------------------------------------------------
# CoverageSummary -- separate source/evidence/candidate/risk/Query counts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageSummary:
    """Separate-count summary of one domain's coverage ledger.

    Counts are never inter-derived: the Query count is not the risk count,
    the candidate count is not the source-record count (matrix §3.4, §6 #10).
    """

    expected_set_hash: str
    domain_id: str
    run_id: str
    expected_units: int
    assigned_units: int
    l1_counts: Mapping[str, int] = field(default_factory=dict)
    l0_status_counts: Mapping[str, int] = field(default_factory=dict)
    l1b_polarity_counts: Mapping[str, int] = field(default_factory=dict)
    l2_counts: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_nonempty(self.expected_set_hash,
                           "CoverageSummary.expected_set_hash")
        _validate_nonempty(self.domain_id, "CoverageSummary.domain_id")
        _validate_nonempty(self.run_id, "CoverageSummary.run_id")
        # Deep-freeze the count mappings (immutable view).
        object.__setattr__(self, "l1_counts", dict(self.l1_counts))
        object.__setattr__(self, "l0_status_counts", dict(self.l0_status_counts))
        object.__setattr__(self, "l1b_polarity_counts",
                           dict(self.l1b_polarity_counts))
        object.__setattr__(self, "l2_counts", dict(self.l2_counts))
        self._validate_count_equation()

    def _validate_count_equation(self) -> None:
        expected = self.expected_units
        l1 = self.l1_counts
        actual = sum(l1.get(d, 0) for d in L1_DISPOSITIONS)
        if actual != expected:
            raise CoverageValidationError(
                f"CoverageSummary count equation violated: sum(L1)={actual} "
                f"!= expected_units={expected}")
        if self.assigned_units != expected:
            raise CoverageValidationError(
                f"CoverageSummary.assigned_units={self.assigned_units} != "
                f"expected_units={expected}")

    # -- accessors ---------------------------------------------------------

    def not_evaluable_count(self) -> int:
        return self.l1_counts.get(L1Disposition.NOT_EVALUABLE, 0)

    def has_l0_blocker(self) -> bool:
        return any(self.l0_status_counts.get(s, 0) > 0
                   for s in L0_STATUS_DOMAIN_COMPLETE_BLOCKERS)

    def source_record_count(self) -> int:
        return self.l2_counts.get(L2ObjectType.SOURCE_RECORD, 0)

    def risk_candidate_count(self) -> int:
        return self.l2_counts.get(L2ObjectType.RISK_CANDIDATE, 0)

    def risk_instance_count(self) -> int:
        return self.l2_counts.get(L2ObjectType.RISK_INSTANCE, 0)

    def query_draft_count(self) -> int:
        return self.l2_counts.get(L2ObjectType.QUERY_DRAFT, 0)

    def evidence_count_by_polarity(self) -> Dict[str, int]:
        return dict(self.l1b_polarity_counts)


# ---------------------------------------------------------------------------
# is_domain_complete -- fail-closed medical-completeness predicate
# ---------------------------------------------------------------------------

def is_domain_complete(summary: CoverageSummary) -> Tuple[bool, List[str]]:
    """Fail-closed predicate for medical domain completeness.

    Returns ``(True, [])`` only when every invariant holds.  Returns
    ``(False, reasons)`` otherwise.  This predicate NEVER infers completeness
    from run success, R1 coverage acknowledgement, a model "complete" output,
    or a zero risk count (matrix §6 final paragraph).

    Blocking conditions (any one blocks):

    1. L0 has any partial/truncated/failed/missing status;
    2. any L1 unit is ``not_evaluable``;
    3. the count equation is broken (caught earlier, but checked defensively);
    4. the expected-set hash or provenance is missing;
    5. any positive unit lacks a required L2 join (checked at UnitEvaluation
       construction; the summary would already be unbuildable).

    A *reasoned* L0 ``not_evaluable`` does NOT prove completeness -- it is a
    blocking status here (matrix §3.2 last paragraph).
    """
    reasons: List[str] = []

    # 1. L0 blocking statuses.
    for blocker in L0_STATUS_DOMAIN_COMPLETE_BLOCKERS:
        n = summary.l0_status_counts.get(blocker, 0)
        if n > 0:
            reasons.append(
                f"L0 status {blocker!r} present ({n} unit(s)); "
                f"cannot claim medical domain completeness")

    # 2. L1 not_evaluable.
    ne = summary.not_evaluable_count()
    if ne > 0:
        reasons.append(
            f"L1 not_evaluable present ({ne} unit(s)); "
            f"dashboard must show coverage gap and must not declare the "
            f"medical domain complete")

    # 3. Count equation -- enforced in CoverageSummary construction; re-check
    # defensively in case a caller constructed a summary by hand.
    l1_total = sum(summary.l1_counts.get(d, 0) for d in L1_DISPOSITIONS)
    if l1_total != summary.expected_units:
        reasons.append(
            f"count equation broken: sum(L1)={l1_total} != "
            f"expected_units={summary.expected_units}")

    if summary.assigned_units != summary.expected_units:
        reasons.append(
            f"assigned_units={summary.assigned_units} != "
            f"expected_units={summary.expected_units}")

    # 4. Provenance / expected-set hash presence.
    if not summary.expected_set_hash:
        reasons.append("expected_set_hash is missing")

    if reasons:
        return False, reasons
    return True, []
