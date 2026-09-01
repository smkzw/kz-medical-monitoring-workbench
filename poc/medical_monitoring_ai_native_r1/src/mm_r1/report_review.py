"""Synthetic report-review fixtures and fail-closed claim coverage logic.

The report review layer records whether every expected body/table/figure/
footnote unit was processed.  It does not change a report, user disposition,
review authority, or publication state.  Evidence comparisons are separate
from coverage: an unsupported claim can be fully reviewed and remain an
explicit issue, while missing/partial/truncated/unreasoned coverage or a
cutoff mismatch prevents the special ``full report reviewed`` claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .domain import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    ClaimCoverageEntry as DomainClaimCoverageEntry,
    ClaimCoverageLedger as DomainClaimCoverageLedger,
    CoverageManifest,
    CoverageUnit,
    CoverageUnitStatus,
    NodeType,
    PAYLOAD_ROLE_LEDGER,
    ReportClaim,
    ReportUnitRef,
    SCOPE_REPORT_UNIT,
    canonical_json,
    content_hash,
    to_jsonable,
)


REPORT_UNIT_TYPES = frozenset(("body", "table", "figure", "footnote"))
CLAIM_COVERAGE_STATUSES = frozenset(("claimed", "no_claim", "not_evaluable", "partial", "truncated"))
EVIDENCE_STATUSES = frozenset(
    (
        "supported",
        "partially_supported",
        "unsupported",
        "outdated_wrong_cutoff",
        "overstated",
        "understated",
        "internally_inconsistent",
        "not_evaluable",
    )
)

# Deliberate R1 POC boundary: the minimal ledger models zero or one atomic
# claim per expected report unit.  It must not be read as a general multi-claim
# report parser; a later slice needs a claim-to-unit relation table.
POC_SCHEMA_LIMITATION = (
    "R1 POC supports zero or one AtomicClaim per expected report unit; "
    "arbitrary multi-claim units require a later relation schema"
)


@dataclass(frozen=True)
class AtomicClaim:
    """One independently reviewable report claim tied to one report unit."""

    claim_id: str
    unit_type: str
    unit_id: str
    text: str
    cutoff: str

    def __post_init__(self) -> None:
        if self.unit_type not in REPORT_UNIT_TYPES:
            raise ValueError("unsupported report unit type: %s" % self.unit_type)
        if not self.claim_id or not self.unit_id or not self.text or not self.cutoff:
            raise ValueError("atomic claims require id, unit, text and cutoff")

    @property
    def unit_key(self) -> Tuple[str, str]:
        return (self.unit_type, self.unit_id)

    def to_domain(self, status: str = "not_evaluable", evidence_refs: Sequence[str] = ()) -> ReportClaim:
        return ReportClaim(
            claim_id=self.claim_id,
            text=self.text,
            status=status,
            evidence_refs=list(evidence_refs),
        )


@dataclass(frozen=True)
class EvidenceRecord:
    """Deterministic evidence row used by the synthetic comparison."""

    evidence_id: str
    claim_id: str
    cutoff: str
    status: str = "supported"
    note: str = ""

    def __post_init__(self) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError("unsupported evidence status: %s" % self.status)
        if not self.evidence_id or not self.claim_id or not self.cutoff:
            raise ValueError("evidence requires id, claim id and cutoff")


@dataclass(frozen=True)
class EvidenceComparison:
    claim_id: str
    expected_cutoff: str
    claim_cutoff: str
    evidence_ids: Tuple[str, ...] = ()
    evidence_cutoffs: Tuple[str, ...] = ()
    status: str = "not_evaluable"
    reasons: Tuple[str, ...] = ()
    wrong_cutoff: bool = False

    def __post_init__(self) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError("unsupported comparison status: %s" % self.status)
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "evidence_cutoffs", tuple(self.evidence_cutoffs))
        object.__setattr__(self, "reasons", tuple(self.reasons))


@dataclass(frozen=True)
class ReportReviewFixture:
    """Synthetic report fixture with an explicit one-claim-per-unit boundary.

    Orphan claims and unknown evidence references are retained as input so the
    ledger can report them as blocking errors instead of silently dropping
    them.  Duplicate claims for one unit remain invalid under the R1 POC
    limitation.
    """

    report_artifact_id: str
    run_id: str
    cutoff: str
    units: Tuple[ReportUnitRef, ...]
    claims: Tuple[AtomicClaim, ...]
    evidence: Tuple[EvidenceRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "units", tuple(self.units))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        unit_keys = [(unit.unit_type, unit.unit_id) for unit in self.units]
        if len(unit_keys) != len(set(unit_keys)):
            raise ValueError("report fixture contains duplicate expected units")
        if any(unit.unit_type not in REPORT_UNIT_TYPES for unit in self.units):
            raise ValueError("report fixture contains an unsupported unit type")
        claim_keys = [claim.unit_key for claim in self.claims]
        if len(claim_keys) != len(set(claim_keys)):
            raise ValueError("each report unit may have at most one synthetic atomic claim")

    def unit(self, unit_type: str, unit_id: str) -> ReportUnitRef:
        for unit in self.units:
            if (unit.unit_type, unit.unit_id) == (unit_type, unit_id):
                return unit
        raise KeyError("unknown report unit: %s:%s" % (unit_type, unit_id))

    @property
    def validation_issues(self) -> Tuple[str, ...]:
        """Return fixture-level integrity issues without dropping input rows."""

        expected_keys = {(unit.unit_type, unit.unit_id) for unit in self.units}
        issues: List[str] = []
        for claim in self.claims:
            if claim.unit_key not in expected_keys:
                issues.append(
                    "orphan claim %s for unexpected report unit: %s:%s"
                    % (claim.claim_id, claim.unit_type, claim.unit_id)
                )
        claim_ids = {claim.claim_id for claim in self.claims}
        for evidence in self.evidence:
            if evidence.claim_id not in claim_ids:
                issues.append(
                    "evidence %s references unknown claim %s"
                    % (evidence.evidence_id, evidence.claim_id)
                )
        return tuple(issues)


@dataclass(frozen=True)
class ClaimCoverageLedger:
    """Immutable report coverage ledger with an explicit expected-unit set.

    The ledger keeps fixture evidence even when it is invalid.  This makes an
    unknown evidence claim observable and fail closed at ``is_complete``.
    """

    ledger_id: str
    run_id: str
    report_artifact_id: str
    expected_units: Tuple[ReportUnitRef, ...]
    entries: Tuple[DomainClaimCoverageEntry, ...]
    claims: Tuple[AtomicClaim, ...] = ()
    comparisons: Tuple[EvidenceComparison, ...] = ()
    expected_cutoff: str = ""
    report_cutoff: str = ""
    evidence: Tuple[EvidenceRecord, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_units", tuple(self.expected_units))
        object.__setattr__(self, "entries", tuple(self.entries))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "comparisons", tuple(self.comparisons))
        object.__setattr__(self, "evidence", tuple(self.evidence))

    @property
    def entry_map(self) -> Dict[Tuple[str, str], DomainClaimCoverageEntry]:
        return {(entry.unit.unit_type, entry.unit.unit_id): entry for entry in self.entries}

    @property
    def claim_map(self) -> Dict[str, AtomicClaim]:
        return {claim.claim_id: claim for claim in self.claims}

    @property
    def comparison_map(self) -> Dict[str, EvidenceComparison]:
        return {comparison.claim_id: comparison for comparison in self.comparisons}

    def is_complete(self) -> Tuple[bool, List[str]]:
        """Coverage completeness; missing or ambiguous coverage fails closed."""

        reasons: List[str] = []
        if not self.expected_units:
            reasons.append("expected report unit set is missing")
        expected_keys = {(unit.unit_type, unit.unit_id) for unit in self.expected_units}
        claim_unit_keys = [claim.unit_key for claim in self.claims]
        if len(claim_unit_keys) != len(set(claim_unit_keys)):
            reasons.append(POC_SCHEMA_LIMITATION)
        claim_id_values = [claim.claim_id for claim in self.claims]
        if len(claim_id_values) != len(set(claim_id_values)):
            reasons.append("duplicate atomic claim id")
        for claim in self.claims:
            if claim.unit_key not in expected_keys:
                reasons.append(
                    "orphan claim %s for unexpected report unit: %s:%s"
                    % (claim.claim_id, claim.unit_type, claim.unit_id)
                )
        entries = self.entry_map
        if len(entries) != len(self.entries):
            reasons.append("duplicate report coverage unit")
        for unit in self.expected_units:
            key = (unit.unit_type, unit.unit_id)
            entry = entries.get(key)
            if entry is None:
                reasons.append("missing expected report unit: %s:%s" % key)
                continue
            status = entry.status
            if status not in CLAIM_COVERAGE_STATUSES:
                reasons.append("invalid report coverage status: %s:%s -> %s" % (key[0], key[1], status))
            elif status in ("partial", "truncated"):
                reasons.append("%s:%s -> %s" % (key[0], key[1], status))
            elif status == "not_evaluable" and not entry.reason:
                reasons.append("%s:%s -> not_evaluable without reason" % key)
            elif status == "claimed":
                if not entry.claim_id:
                    reasons.append("%s:%s -> claimed without claim_id" % key)
                elif entry.claim_id not in self.claim_map:
                    reasons.append("%s:%s -> unknown claim %s" % (key[0], key[1], entry.claim_id))
                elif entry.claim_id not in self.comparison_map:
                    reasons.append("%s:%s -> missing evidence comparison" % key)
            elif status == "no_claim":
                if entry.claim_id:
                    reasons.append("%s:%s -> no_claim has claim_id" % key)
                if any(claim.unit_key == key for claim in self.claims):
                    reasons.append("%s:%s -> no_claim despite extracted claim" % key)
        for entry in self.entries:
            key = (entry.unit.unit_type, entry.unit.unit_id)
            if key not in expected_keys:
                reasons.append("unexpected report unit: %s:%s" % key)
        claim_ids = set(self.claim_map)
        for evidence in self.evidence:
            if evidence.claim_id not in claim_ids:
                reasons.append(
                    "evidence %s references unknown claim %s"
                    % (evidence.evidence_id, evidence.claim_id)
                )
        for comparison in self.comparisons:
            if comparison.claim_id not in claim_ids:
                reasons.append("comparison references unknown claim %s" % comparison.claim_id)
        for comparison in self.comparisons:
            if comparison.wrong_cutoff or comparison.status == "outdated_wrong_cutoff":
                reasons.append("claim %s -> wrong cutoff" % comparison.claim_id)
        if self.expected_cutoff and self.report_cutoff and self.expected_cutoff != self.report_cutoff:
            reasons.append("report cutoff does not match expected cutoff")
        return (not reasons, reasons)

    def can_claim_full_report_reviewed(self) -> bool:
        ok, _ = self.is_complete()
        return ok

    def is_full_report_reviewed(self) -> bool:
        return self.can_claim_full_report_reviewed()

    @property
    def full_report_reviewed(self) -> bool:
        return self.can_claim_full_report_reviewed()

    def full_report_reviewed_claim(self) -> Optional[str]:
        return "full report reviewed" if self.can_claim_full_report_reviewed() else None

    def coverage_manifest(self) -> CoverageManifest:
        expected = [
            CoverageUnit(
                scope=SCOPE_REPORT_UNIT,
                key="%s:%s" % (unit.unit_type, unit.unit_id),
            )
            for unit in self.expected_units
        ]
        produced: List[CoverageUnit] = []
        for entry in self.entries:
            key = "%s:%s" % (entry.unit.unit_type, entry.unit.unit_id)
            status = {
                "claimed": CoverageUnitStatus.COVERED,
                "no_claim": CoverageUnitStatus.COVERED,
                "not_evaluable": CoverageUnitStatus.NOT_EVALUABLE,
                "partial": CoverageUnitStatus.PARTIAL,
                "truncated": CoverageUnitStatus.TRUNCATED,
            }.get(entry.status, CoverageUnitStatus.FAILED)
            produced.append(CoverageUnit(scope=SCOPE_REPORT_UNIT, key=key, status=status, reason=entry.reason))
        return CoverageManifest(expected=expected, produced=produced).reconcile()

    def to_domain(self) -> DomainClaimCoverageLedger:
        return DomainClaimCoverageLedger(
            ledger_id=self.ledger_id,
            run_id=self.run_id,
            report_artifact_id=self.report_artifact_id,
            entries=list(self.entries),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "run_id": self.run_id,
            "report_artifact_id": self.report_artifact_id,
            "expected_units": [to_jsonable(unit) for unit in self.expected_units],
            "entries": [to_jsonable(entry) for entry in self.entries],
            "claims": [to_jsonable(claim) for claim in self.claims],
            "comparisons": [to_jsonable(comparison) for comparison in self.comparisons],
            "evidence": [to_jsonable(item) for item in self.evidence],
            "expected_cutoff": self.expected_cutoff,
            "report_cutoff": self.report_cutoff,
            "full_report_reviewed": self.can_claim_full_report_reviewed(),
        }

    def to_artifact_envelope(self, *, node_id: str = "report-claim-coverage") -> ArtifactEnvelope:
        coverage = self.coverage_manifest()
        ledger_complete, _ = self.is_complete()
        envelope = ArtifactEnvelope(
            artifact_type="report_claim_coverage_ledger",
            version="r1",
            run_id=self.run_id,
            node_id=node_id,
            node_type=NodeType.DETERMINISTIC_SERVICE,
            payload=self.to_dict(),
            payload_role=PAYLOAD_ROLE_LEDGER,
            input_hashes=[content_hash({"report_artifact_id": self.report_artifact_id, "cutoff": self.report_cutoff})],
            evidence_refs=[self.report_artifact_id],
            coverage=coverage,
            completeness=(
                ArtifactCompleteness.COMPLETE
                if ledger_complete
                else ArtifactCompleteness.PARTIAL
            ),
            qc_status="full_report_reviewed=%s" % self.can_claim_full_report_reviewed(),
        )
        # Coverage can further downgrade an otherwise valid ledger, but it
        # must never upgrade a ledger-integrity failure.  Expected-unit
        # coverage may be complete even when supplied claims or evidence are
        # orphaned or otherwise inconsistent.
        coverage_completeness = envelope.derive_completeness()
        if ledger_complete:
            envelope.completeness = coverage_completeness
        elif coverage_completeness != ArtifactCompleteness.COMPLETE:
            envelope.completeness = coverage_completeness
        return envelope


@dataclass(frozen=True)
class ReportReviewResult:
    ledger: ClaimCoverageLedger
    comparisons: Tuple[EvidenceComparison, ...]
    full_report_reviewed: bool
    reasons: Tuple[str, ...]


def compare_claim_to_evidence(
    claim: AtomicClaim,
    evidence: Sequence[EvidenceRecord],
    *,
    expected_cutoff: str,
) -> EvidenceComparison:
    """Compare one atomic claim to deterministic evidence without rewriting it."""

    matching = tuple(item for item in evidence if item.claim_id == claim.claim_id)
    reasons: List[str] = []
    wrong_cutoff = claim.cutoff != expected_cutoff
    if wrong_cutoff:
        reasons.append("claim cutoff does not match expected cutoff")
    if not matching:
        reasons.append("no evidence is linked to claim")
        return EvidenceComparison(
            claim_id=claim.claim_id,
            expected_cutoff=expected_cutoff,
            claim_cutoff=claim.cutoff,
            status="not_evaluable",
            reasons=tuple(reasons),
            wrong_cutoff=wrong_cutoff,
        )
    evidence_cutoffs = tuple(item.cutoff for item in matching)
    if any(item.cutoff != expected_cutoff for item in matching):
        wrong_cutoff = True
        reasons.append("evidence cutoff does not match expected cutoff")
    statuses = {item.status for item in matching}
    if wrong_cutoff:
        status = "outdated_wrong_cutoff"
    elif "unsupported" in statuses:
        status = "unsupported"
    elif "partially_supported" in statuses:
        status = "partially_supported"
    elif "overstated" in statuses:
        status = "overstated"
    elif "understated" in statuses:
        status = "understated"
    elif "internally_inconsistent" in statuses:
        status = "internally_inconsistent"
    elif "not_evaluable" in statuses:
        status = "not_evaluable"
    else:
        status = "supported"
    return EvidenceComparison(
        claim_id=claim.claim_id,
        expected_cutoff=expected_cutoff,
        claim_cutoff=claim.cutoff,
        evidence_ids=tuple(item.evidence_id for item in matching),
        evidence_cutoffs=evidence_cutoffs,
        status=status,
        reasons=tuple(reasons),
        wrong_cutoff=wrong_cutoff,
    )


def _coerce_entry(value: Union[DomainClaimCoverageEntry, Mapping[str, Any]]) -> DomainClaimCoverageEntry:
    if isinstance(value, DomainClaimCoverageEntry):
        return value
    unit_value = value.get("unit", {})
    if isinstance(unit_value, ReportUnitRef):
        unit = unit_value
    else:
        unit = ReportUnitRef(
            unit_type=str(unit_value.get("unit_type", "")),
            unit_id=str(unit_value.get("unit_id", "")),
            page=unit_value.get("page"),
            anchor=str(unit_value.get("anchor", "")),
        )
    return DomainClaimCoverageEntry(
        unit=unit,
        claim_id=value.get("claim_id"),
        status=str(value.get("status", "no_claim")),
        evidence_refs=list(value.get("evidence_refs", ())),
        reason=value.get("reason"),
    )


def build_claim_coverage_ledger(
    fixture: ReportReviewFixture,
    entries: Optional[Sequence[Union[DomainClaimCoverageEntry, Mapping[str, Any]]]] = None,
    *,
    comparisons: Optional[Sequence[EvidenceComparison]] = None,
    expected_cutoff: Optional[str] = None,
    report_cutoff: Optional[str] = None,
) -> ClaimCoverageLedger:
    """Build a ledger while preserving absent expected units as absent.

    In particular, this function does not silently synthesize a covered entry
    for a unit that was omitted by a caller.
    """

    resolved_expected_cutoff = expected_cutoff if expected_cutoff is not None else fixture.cutoff
    resolved_report_cutoff = report_cutoff if report_cutoff is not None else fixture.cutoff
    resolved_comparisons = tuple(
        comparisons
        if comparisons is not None
        else (
            compare_claim_to_evidence(
                claim,
                fixture.evidence,
                expected_cutoff=resolved_expected_cutoff,
            )
            for claim in fixture.claims
        )
    )
    if entries is None:
        comparison_map = {item.claim_id: item for item in resolved_comparisons}
        claim_map = {claim.unit_key: claim for claim in fixture.claims}
        generated: List[DomainClaimCoverageEntry] = []
        for unit in fixture.units:
            claim = claim_map.get((unit.unit_type, unit.unit_id))
            if claim is None:
                generated.append(DomainClaimCoverageEntry(unit=unit, status="no_claim"))
                continue
            comparison = comparison_map.get(claim.claim_id)
            if comparison is None:
                generated.append(
                    DomainClaimCoverageEntry(
                        unit=unit,
                        claim_id=claim.claim_id,
                        status="not_evaluable",
                        reason="evidence comparison missing",
                    )
                )
            elif comparison.status == "not_evaluable":
                generated.append(
                    DomainClaimCoverageEntry(
                        unit=unit,
                        claim_id=claim.claim_id,
                        status="not_evaluable",
                        evidence_refs=list(comparison.evidence_ids),
                        reason="; ".join(comparison.reasons) or "evidence not evaluable",
                    )
                )
            else:
                generated.append(
                    DomainClaimCoverageEntry(
                        unit=unit,
                        claim_id=claim.claim_id,
                        status="claimed",
                        evidence_refs=list(comparison.evidence_ids),
                    )
                )
        resolved_entries = tuple(generated)
    else:
        resolved_entries = tuple(_coerce_entry(item) for item in entries)
    ledger_identity = {
        "report_artifact_id": fixture.report_artifact_id,
        "run_id": fixture.run_id,
        "expected_units": [to_jsonable(item) for item in fixture.units],
        "claims": [to_jsonable(item) for item in fixture.claims],
        "evidence": [to_jsonable(item) for item in fixture.evidence],
        "comparisons": [to_jsonable(item) for item in resolved_comparisons],
        "expected_cutoff": resolved_expected_cutoff,
        "report_cutoff": resolved_report_cutoff,
        "entries": [to_jsonable(item) for item in resolved_entries],
    }
    return ClaimCoverageLedger(
        ledger_id=content_hash(ledger_identity),
        run_id=fixture.run_id,
        report_artifact_id=fixture.report_artifact_id,
        expected_units=fixture.units,
        entries=resolved_entries,
        claims=fixture.claims,
        comparisons=resolved_comparisons,
        evidence=fixture.evidence,
        expected_cutoff=resolved_expected_cutoff,
        report_cutoff=resolved_report_cutoff,
    )


def review_report(
    fixture: ReportReviewFixture,
    entries: Optional[Sequence[Union[DomainClaimCoverageEntry, Mapping[str, Any]]]] = None,
    *,
    expected_cutoff: Optional[str] = None,
    report_cutoff: Optional[str] = None,
) -> ReportReviewResult:
    ledger = build_claim_coverage_ledger(
        fixture,
        entries,
        expected_cutoff=expected_cutoff,
        report_cutoff=report_cutoff,
    )
    ok, reasons = ledger.is_complete()
    return ReportReviewResult(
        ledger=ledger,
        comparisons=ledger.comparisons,
        full_report_reviewed=ok,
        reasons=tuple(reasons),
    )


def synthetic_report_fixture(
    *,
    run_id: str = "synthetic-report-run",
    report_artifact_id: str = "synthetic-report-artifact",
    cutoff: str = "SYNTHETIC-CUTOFF-1",
) -> ReportReviewFixture:
    """Return a four-unit, non-clinical fixture for deterministic tests."""

    units = (
        ReportUnitRef(unit_type="body", unit_id="body-1", page="1", anchor="body-anchor"),
        ReportUnitRef(unit_type="table", unit_id="table-1", page="2", anchor="table-anchor"),
        ReportUnitRef(unit_type="figure", unit_id="figure-1", page="3", anchor="figure-anchor"),
        ReportUnitRef(unit_type="footnote", unit_id="footnote-1", page="3", anchor="footnote-anchor"),
    )
    claims = (
        AtomicClaim("claim-body-1", "body", "body-1", "Synthetic body statement", cutoff),
        AtomicClaim("claim-table-1", "table", "table-1", "Synthetic table statement", cutoff),
        AtomicClaim("claim-figure-1", "figure", "figure-1", "Synthetic figure statement", cutoff),
    )
    evidence = tuple(
        EvidenceRecord(
            evidence_id="evidence-%s" % claim.claim_id,
            claim_id=claim.claim_id,
            cutoff=cutoff,
            status="supported",
            note="synthetic evidence comparison",
        )
        for claim in claims
    )
    return ReportReviewFixture(
        report_artifact_id=report_artifact_id,
        run_id=run_id,
        cutoff=cutoff,
        units=units,
        claims=claims,
        evidence=evidence,
    )


make_synthetic_report_fixture = synthetic_report_fixture
build_ledger = build_claim_coverage_ledger


__all__ = [
    "AtomicClaim",
    "CLAIM_COVERAGE_STATUSES",
    "ClaimCoverageLedger",
    "EvidenceComparison",
    "EvidenceRecord",
    "ReportReviewFixture",
    "ReportReviewResult",
    "REPORT_UNIT_TYPES",
    "POC_SCHEMA_LIMITATION",
    "build_claim_coverage_ledger",
    "build_ledger",
    "compare_claim_to_evidence",
    "make_synthetic_report_fixture",
    "review_report",
    "synthetic_report_fixture",
]
