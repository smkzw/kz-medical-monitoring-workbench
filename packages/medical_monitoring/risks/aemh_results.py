"""AE/MH evaluation results and risk-candidate construction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from .aemh_types import (
    CLINICAL_FLAG_TOKENS, EventMatchStrategy, MedicalGrading,
    ProtocolAEMHBoundary, SemanticRecord, _CLINICAL_FLAG_TOKENS,
    _SAE_CRITERIA_TOKENS,
)
from .contracts import (
    EvaluationUnit, EvidenceItem, L0CoverageStatus, L1Disposition,
    L1bEvidencePolarity, QueryDraftRef, RiskCandidateRef, RiskInstanceRef,
    SourceRecordRef, UnitEvaluation,
)

# ---------------------------------------------------------------------------

class AEMHSliceError(Exception):
    """An AE/MH slice evaluation invariant was violated."""


@dataclass(frozen=True)
class AEMHUnitResult:
    """The evaluation outcome for one D01 EvaluationUnit.

    Bundles the L1 disposition, L1b evidence items, source-record refs,
    candidate refs, risk-instance refs, query refs, journey markers and
    the medical grading -- all bound to the same ``unit_id`` and source
    locators.
    """
    unit_id: str
    subject_ref: str
    l1_disposition: str
    medical_grading: MedicalGrading
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    journey_markers: Tuple[Dict[str, Any], ...] = ()
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    not_evaluable_reason: str = ""
    boundary_reason: str = ""

    @property
    def monitoring_priority(self) -> str:
        """Neutral monitoring-priority accessor (frozen D02 contract §2):
        projects ``medical_grading.monitoring_priority`` so the lifecycle
        adapter and ``RiskDomainUnitResult`` consumers read priority off
        any domain result without importing a domain-specific grading
        type.  D01 behavior is unchanged -- this is a read-only view of
        the existing field."""
        return self.medical_grading.monitoring_priority

    def all_source_locator_ids(self) -> Tuple[str, ...]:
        ids: List[str] = []
        for ref in self.source_record_refs:
            ids.append(ref.locator.locator_id())
        for item in self.evidence:
            ids.append(item.locator.locator_id())
        for ref in self.risk_candidate_refs:
            if ref.locator is not None:
                ids.append(ref.locator.locator_id())
        return tuple(sorted(set(ids)))

    def to_unit_evaluation(
        self,
        *,
        l0_status: str = L0CoverageStatus.COVERED,
        provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        """Build a worker_01 :class:`UnitEvaluation` from this result using
        caller-supplied L0/provenance (finding 5).

        This is a bounded conversion/validation surface that exercises the
        real common-contract join invariants.  The caller must supply
        ``provenance_snapshot_id`` for non-not_evaluable dispositions and
        ``provenance_rule_lineage`` for positive/boundary dispositions.
        """
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity in (
                    L1bEvidencePolarity.SUPPORTING,
                    L1bEvidencePolarity.COUNTEREVIDENCE,
                    L1bEvidencePolarity.CONTEXT):
                if ev.polarity not in polarities:
                    polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id,
            l0_status=l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(polarities),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason,
        )


@dataclass(frozen=True)
class AEMHSliceResult:
    """Aggregate result of evaluating one or more D01 units for a subject."""

    subject_ref: str
    unit_results: Tuple[AEMHUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    protocol_boundary: ProtocolAEMHBoundary = None  # type: ignore[assignment]
    match_strategy: EventMatchStrategy = None  # type: ignore[assignment]
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def positive_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NOT_APPLICABLE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_evidence_item(
    evidence_id: str,
    polarity: str,
    record: SemanticRecord,
    rule_lineage: str,
    uncertainty_note: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        polarity=polarity,
        locator=record.locator,
        evidence_role=record.role,
        rule_lineage=rule_lineage,
        uncertainty_note=uncertainty_note,
    )


def _make_source_record_ref(record: SemanticRecord) -> SourceRecordRef:
    return SourceRecordRef(
        record_id=record.locator.record_id,
        locator=record.locator,
    )


def _signal_type_for(record: SemanticRecord, grading: MedicalGrading) -> str:
    """R2 RiskCandidate.signal_type for a D01 clue.

    R2 derives the independent SAE/AESI ``clinical_risk_flags`` from this
    public signal surface.  Encode only the flags actually supported by the
    record's seriousness criteria; do not infer AESI merely because the
    semantic role is ``seriousness_clue``.
    """
    if record.role == "symptom_event":
        base = "potential_unreported_ae_symptom"
    elif record.role == "healthcare_encounter":
        base = "potential_unreported_ae_hospitalization"
    elif record.role == "death_event":
        base = "potential_unreported_death_event"
    elif record.role == "seriousness_clue":
        base = "potential_seriousness_clue"
    else:
        base = f"potential_unreported_aemh_{record.role}"

    criteria = set(grading.seriousness_criteria)
    flags: List[str] = []
    if criteria.intersection(_SAE_CRITERIA_TOKENS):
        flags.append("sae")
    if "aesi" in criteria:
        flags.append("aesi")
    if flags:
        return base + "_" + "_".join(flags)
    return base


def _candidate_detail_payload(
    record: SemanticRecord,
    grading: MedicalGrading,
    match_reason: str,
) -> Dict[str, Any]:
    """Detail payload for R2 RiskCandidate, keeping clinical flags separate
    from monitoring priority."""
    return {
        "role": record.role,
        "concept": record.concept,
        "intensity": grading.intensity,
        "intensity_scale": grading.intensity_scale,
        "seriousness_criteria": list(grading.seriousness_criteria),
        "monitoring_priority": grading.monitoring_priority,
        "clinical_risk_flags": sorted(
            set(grading.seriousness_criteria) & set(_CLINICAL_FLAG_TOKENS)),
        "ai_assertion": record.ai_assertion,
        "match_reason": match_reason,
        "locator_id": record.locator.locator_id(),
    }


def _r4_risk_scope(
    *,
    record: SemanticRecord,
    unit: EvaluationUnit,
    rule_lineage: str,
) -> List[str]:
    """Deterministic R4 scope list for a D01 risk identity (matrix §3.6).

    Scope carries the dimensions that, together with the classifier, make
    the public R2 identity exact and stable.  Lineage/version inputs live
    in the scope so a rule/mapping/knowledge/algorithm change produces a
    *different* identity for the same stable clinical event (detectable
    as a supersede), while a different concept or source event changes
    the classifier (genuinely different identity).
    """
    norm = record.normalized_date()
    date_detail = norm.detail if norm else "none"
    return sorted({
        f"site:{record.site_ref}" if record.site_ref else "site:",
        f"tw:{unit.temporal_window}",
        f"dp:{date_detail}",
        f"ul:{unit.rule_or_knowledge_lineage}",
        f"ua:{unit.unit_algorithm_version}",
        f"rl:{rule_lineage}",
    })


def _stable_source_event_key(record: SemanticRecord) -> str:
    """Stable source/event identity key that survives snapshot/revision
    changes (Codex round-3 finding 1).

    Binds the semantic source role (``table_semantic``) and the stable
    record/event id (``record_id``) -- never ``snapshot_id`` or
    ``source_revision_id``, which change on every export.  This keeps
    the same stable clinical/source event at the same identity across
    N→N+1 exports.  The full locator is kept separately in candidate
    detail for provenance.
    """
    return f"{record.locator.table_semantic}:{record.locator.record_id}"


def _r4_risk_classifier(
    *,
    record: SemanticRecord,
    signal_type: str,
) -> str:
    """Deterministic R4 classifier for a D01 risk identity (matrix §3.6).

    Binds the normalized medical concept, the candidate signal type and
    a *stable* source/event key (semantic role + record/event id) that
    excludes ``snapshot_id`` and ``source_revision_id``.  Two clues with
    the same classifier are the same stable clinical/source event across
    exports; a different concept or different record/event id is a
    genuinely different identity and must NOT keep an old risk alive.
    """
    return "|".join((
        "d01",
        _concept(record),
        signal_type,
        _stable_source_event_key(record),
    ))


def _build_r4_risk_identity(
    *,
    project_id: str,
    subject_ref: str,
    record: SemanticRecord,
    signal_type: str,
    unit: EvaluationUnit,
    rule_lineage: str,
) -> RiskIdentity:
    """Build the *public* R2 :class:`RiskIdentity` for a D01 candidate.

    Uses only :func:`mm_r2.identity.make_risk_identity`.  The same
    dimensions always yield the same deterministic
    ``risk_identity_id``; R4 holds no parallel identity hash.
    """
    return make_risk_identity(
        project_id=project_id,
        subject_ref=subject_ref,
        domain="D01_aemh",
        scope=_r4_risk_scope(record=record, unit=unit, rule_lineage=rule_lineage),
        classifier=_r4_risk_classifier(record=record, signal_type=signal_type),
    )


def _r4_identity_detail(
    *,
    record: SemanticRecord,
    identity: RiskIdentity,
    signal_type: str,
) -> Dict[str, Any]:
    """Identity components stored on the R2 candidate ``detail`` so the
    lifecycle adapter can compare stable cores and lineage fingerprints
    and re-establish with the *exact* public scope/classifier, without
    re-deriving a parallel identity (matrix §3.6).  The full locator is
    kept separately for provenance; it does not enter the identity."""
    return {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": _r4_risk_classifier(
            record=record, signal_type=signal_type),
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": _stable_source_event_key(record),
        "full_locator_id": record.locator.locator_id(),
    }

def _build_r2_candidate(
    *,
    project_id: str,
    subject_ref: str,
    record: SemanticRecord,
    grading: MedicalGrading,
    match_reason: str,
    snapshot_id: str,
    rule_lineage: str,
    unit: EvaluationUnit,
) -> Tuple[RiskCandidate, RiskIdentity]:
    """Construct the real R2 :class:`RiskCandidate` and its public
    :class:`RiskIdentity` (finding 4 + identity integration).

    The candidate ``detail`` carries the identity components so the
    lifecycle adapter can compare stable cores and lineage fingerprints
    without a parallel identity hash.  No candidate is established here.
    """
    signal_type = _signal_type_for(record, grading)
    identity = _build_r4_risk_identity(
        project_id=project_id,
        subject_ref=subject_ref,
        record=record,
        signal_type=signal_type,
        unit=unit,
        rule_lineage=rule_lineage,
    )
    detail = _candidate_detail_payload(record, grading, match_reason)
    detail.update(_r4_identity_detail(
        record=record, identity=identity, signal_type=signal_type))
    candidate = RiskCandidate.from_signal(
        project_id=project_id,
        subject_ref=subject_ref,
        domain="D01_aemh",
        signal_type=signal_type,
        source_snapshot_id=snapshot_id,
        rule_activation_id=rule_lineage,
        severity_hint=grading.severity_hint,
        confidence_hint=0.0,
        detail=detail,
    )
    return candidate, identity



def _concept(record: SemanticRecord) -> str:
    return record.concept.strip()
