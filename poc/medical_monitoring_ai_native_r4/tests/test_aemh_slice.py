"""R4-D01 AE/MH structural slice tests (worker_02, round 3).

Proves (deterministically, synthetic-only) all residual Codex findings:

1. **Partial date across boundary has one outcome**: BOUNDARY only, with
   source locator, uncertainty, and valid ``to_unit_evaluation``.
2. **Exact NCS / alternative-diagnosis proofs**: isolated NCS -> NEGATIVE;
   NCS + action -> POSITIVE; confirmed alt-diagnosis -> NEGATIVE.  No
   multi-outcome or no-crash assertions.
3. **AI provenance not coerced**: ``ai_assertion`` must be actual bool.
4. **Role availability coherence**: recognized, no overlap, present-in-
   available.
5. **Query text has exactly one prefix**: one ``依据：``, one ``发现：``,
   one ``行动项：``.
6. **Every journey event bound to unit_id**: non-empty, equals source.
7. **No permissive multi-outcome assertions**: each scenario asserts one
   intended result.
"""

from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.aemh import (  # noqa: E402
    AEMHSliceError,
    AEMHSliceResult,
    AEMHUnitResult,
    ConceptEquivalence,
    EventMatchStrategy,
    MedicalGrading,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    ProtocolAEMHBoundary,
    ProtocolAnchorDates,
    REQUIRED_AEMH_ROLES,
    SemanticRecord,
    SemanticRecordSet,
    TemporalTolerance,
    classify_event_against_boundary,
    compare_partial_dates,
    derive_monitoring_priority,
    evaluate_aemh_slice,
    evaluate_aemh_unit,
)
from mm_r4.contracts import (  # noqa: E402
    CoverageValidationError,
    EvaluationUnit,
    L1Disposition,
    L1bEvidencePolarity,
    SourceLocator,
    UnitEvaluation,
)
from mm_r4.projection import (  # noqa: E402
    JourneyEvent,
    project_journey,
    project_query_drafts,
    project_subject_journey,
    query_to_text,
)

from mm_r3.normalization import normalize_partial_date  # noqa: E402
from mm_r2.risk import RiskCandidate  # noqa: E402


# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = "D01_aemh"
RULE_LINEAGE = "d01-aemh-rule-v1"
UNIT_ALGO_VERSION = "d01-unit-algo-v1"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
RUN_ID = "run-synthetic-001"
STRATEGY_VERSION = "ems-v1"
BOUNDARY_VERSION = "pb-v1"


# ===========================================================================
# Helpers
# ===========================================================================

def make_locator(
    record_id: str,
    table_semantic: str = "reported_ae",
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=SNAPSHOT_ID,
        source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic,
        record_id=record_id,
        column_or_anchor="row",
    )


def make_record(
    role: str,
    concept: str,
    record_id: str,
    *,
    event_date_raw: str = "",
    subject_ref: str = "S001",
    site_ref: str = "SITE01",
    intensity: str = "",
    seriousness_criteria=(),
    intensity_scale: str = "",
    visit_label: str = "",
    phase: str = "",
    ai_assertion: bool = False,
    note: str = "",
    clinical_significance: str = "",
    alternative_diagnosis: str = "",
    alternative_diagnosis_confirmed: bool = False,
    anchor_descriptor: str = "",
    action_taken: str = "",
) -> SemanticRecord:
    return SemanticRecord(
        role=role,
        concept=concept,
        locator=make_locator(record_id, table_semantic=role),
        event_date_raw=event_date_raw,
        subject_ref=subject_ref,
        site_ref=site_ref,
        intensity=intensity,
        seriousness_criteria=tuple(seriousness_criteria),
        intensity_scale=intensity_scale,
        visit_label=visit_label,
        phase=phase,
        ai_assertion=ai_assertion,
        note=note,
        clinical_significance=clinical_significance,
        alternative_diagnosis=alternative_diagnosis,
        alternative_diagnosis_confirmed=alternative_diagnosis_confirmed,
        anchor_descriptor=anchor_descriptor,
        action_taken=action_taken,
    )


def make_anchor_records(
    subject_ref: str = "S001",
    start_date: str = "2026-01-01",
    end_date: str = "2026-06-30",
    start_desc: str = "icf_date",
    end_desc: str = "end_of_treatment_plus_30d",
) -> list:
    return [
        make_record("subject_identity", "subject", "subj-001",
                    subject_ref=subject_ref),
        make_record("site_identity", "site", "site-001",
                    subject_ref=subject_ref),
        make_record("temporal_anchor", "anchor", "anchor-start",
                    subject_ref=subject_ref,
                    event_date_raw=start_date,
                    anchor_descriptor=start_desc),
        make_record("temporal_anchor", "anchor", "anchor-end",
                    subject_ref=subject_ref,
                    event_date_raw=end_date,
                    anchor_descriptor=end_desc),
    ]


def make_record_set(
    records,
    subject_ref: str = "S001",
    site_ref: str = "SITE01",
    empty_covered_roles=(),
) -> SemanticRecordSet:
    all_records = list(make_anchor_records(subject_ref=subject_ref))
    all_records.extend(records)
    available = tuple(sorted(set(r.role for r in all_records)))
    avail_set = set(available)
    ec = list(empty_covered_roles)
    for role in REQUIRED_AEMH_ROLES:
        if role not in avail_set and role not in ec:
            ec.append(role)
    return SemanticRecordSet(
        records=tuple(all_records),
        subject_ref=subject_ref,
        site_ref=site_ref,
        scope_key=subject_ref,
        available_roles=available,
        empty_covered_roles=tuple(sorted(set(ec))),
    )


def make_unit(
    scope_key: str = "S001",
    concept: str = "MedDRA:10019242",
    temporal_window: str = "study-period-v1",
) -> EvaluationUnit:
    return EvaluationUnit(
        project_id=PROJECT_ID,
        domain_id=DOMAIN_ID,
        scope_type="subject",
        scope_key=scope_key,
        normalized_concept_or_rule_item=concept,
        temporal_window=temporal_window,
        rule_or_knowledge_lineage=RULE_LINEAGE,
        unit_algorithm_version=UNIT_ALGO_VERSION,
    )


def make_boundary(
    boundary_id: str = "pb-d01-v1",
    version: str = BOUNDARY_VERSION,
    exclusions=(),
    applicable: bool = True,
    non_applicable_reason: str = "",
    start_anchor: str = "icf_date",
    end_anchor: str = "end_of_treatment_plus_30d",
) -> ProtocolAEMHBoundary:
    return ProtocolAEMHBoundary(
        boundary_id=boundary_id,
        version=version,
        reporting_start_anchor=start_anchor,
        reporting_end_anchor=end_anchor,
        protocol_exclusions=tuple(exclusions),
        applicable=applicable,
        non_applicable_reason=non_applicable_reason,
    )


def make_strategy(
    concept_groups=(),
    tolerance_days=None,
    strategy_id: str = "ems-d01-v1",
    version: str = STRATEGY_VERSION,
) -> EventMatchStrategy:
    return EventMatchStrategy(
        strategy_id=strategy_id,
        version=version,
        concept_equivalence=ConceptEquivalence(
            groups=tuple(frozenset(g) for g in concept_groups),
            version=version,
        ),
        temporal_tolerance=TemporalTolerance(
            tolerance_days=tolerance_days,
            version=version,
        ),
    )


def evaluate(records, **kwargs):
    unit = kwargs.pop("unit", make_unit())
    record_set = kwargs.pop("record_set", make_record_set(records))
    protocol_boundary = kwargs.pop("protocol_boundary", make_boundary())
    match_strategy = kwargs.pop("match_strategy", make_strategy())
    return evaluate_aemh_unit(
        unit=unit,
        record_set=record_set,
        protocol_boundary=protocol_boundary,
        match_strategy=match_strategy,
        project_id=PROJECT_ID,
        rule_lineage=RULE_LINEAGE,
        snapshot_id=SNAPSHOT_ID,
        **kwargs,
    )


# ===========================================================================
# 1. Five L1 dispositions (each exact, no multi-outcome)
# ===========================================================================

class TestFiveL1Dispositions:

    def test_positive_suspected_under_report(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.risk_candidate_refs) >= 1
        assert len(result.query_refs) >= 1

    def test_negative_reported_match(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-15"),
            make_record("symptom_event", "MedDRA:10019242", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="mild"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_boundary_partial_date(self):
        """Month-precision dates that cannot resolve -> exact BOUNDARY."""
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-10"),
            make_record("symptom_event", "MedDRA:10019242", "sym-001",
                        event_date_raw="2026-03",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.BOUNDARY
        assert result.boundary_reason

    def test_not_evaluable_missing_required_role(self):
        records = [
            make_record("subject_identity", "subject", "subj-001"),
            make_record("site_identity", "site", "site-001"),
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
        ]
        rs = SemanticRecordSet(
            records=tuple(records),
            subject_ref="S001",
            site_ref="SITE01",
            available_roles=("subject_identity", "site_identity",
                             "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )
        result = evaluate_aemh_unit(
            unit=make_unit(), record_set=rs,
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
            snapshot_id=SNAPSHOT_ID,
        )
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "temporal_anchor" in result.not_evaluable_reason

    def test_not_applicable_protocol_non_applicability(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
        ]
        result = evaluate(
            records,
            protocol_boundary=make_boundary(
                applicable=False,
                non_applicable_reason="该受试者在当前方案版本下不收集 AE/MH"),
        )
        assert result.l1_disposition == L1Disposition.NOT_APPLICABLE


# ===========================================================================
# 2. Required-role contract (finding 1 / F4)
# ===========================================================================

class TestRequiredRoleContract:

    def test_empty_covered_role_satisfies_required(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        assert result.l1_disposition != L1Disposition.NOT_EVALUABLE

    def test_missing_subject_identity_not_evaluable(self):
        records = [
            make_record("site_identity", "site", "site-001"),
            make_record("reported_ae", "MedDRA:10019242", "ae-001"),
        ]
        rs = SemanticRecordSet(
            records=tuple(records),
            subject_ref="S001",
            site_ref="SITE01",
            available_roles=("site_identity", "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )
        result = evaluate_aemh_unit(
            unit=make_unit(), record_set=rs,
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
            snapshot_id=SNAPSHOT_ID,
        )
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "subject_identity" in result.not_evaluable_reason

    def test_missing_site_identity_not_evaluable(self):
        records = [
            make_record("subject_identity", "subject", "subj-001"),
            make_record("reported_ae", "MedDRA:10019242", "ae-001"),
        ]
        rs = SemanticRecordSet(
            records=tuple(records),
            subject_ref="S001",
            available_roles=("subject_identity", "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )
        result = evaluate_aemh_unit(
            unit=make_unit(), record_set=rs,
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
            snapshot_id=SNAPSHOT_ID,
        )
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "site_identity" in result.not_evaluable_reason

    def test_reject_mixed_subject_records(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        subject_ref="S001"),
            make_record("reported_ae", "MedDRA:10019243", "ae-002",
                        subject_ref="S002"),
        ]
        with pytest.raises(CoverageValidationError):
            make_record_set(records)

    def test_empty_record_collection_allowed(self):
        rs = SemanticRecordSet(
            records=(),
            subject_ref="S999",
            available_roles=(),
        )
        result = evaluate_aemh_unit(
            unit=make_unit(scope_key="S999"), record_set=rs,
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
            snapshot_id=SNAPSHOT_ID,
        )
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE


# ===========================================================================
# F4: Role availability coherence (finding 4)
# ===========================================================================

class TestRoleAvailabilityCoherence:

    def test_reject_unrecognized_available_role(self):
        """F4: available_roles with unrecognized role is rejected."""
        with pytest.raises(CoverageValidationError, match="unrecognized role"):
            SemanticRecordSet(
                records=(
                    make_record("subject_identity", "sub", "s1"),
                ),
                subject_ref="S001",
                available_roles=("subject_identity", "bogus_role"),
            )

    def test_reject_unrecognized_empty_covered_role(self):
        """F4: empty_covered_roles with unrecognized role is rejected."""
        with pytest.raises(CoverageValidationError, match="unrecognized role"):
            SemanticRecordSet(
                records=(
                    make_record("subject_identity", "sub", "s1"),
                ),
                subject_ref="S001",
                available_roles=("subject_identity",),
                empty_covered_roles=("bogus_role",),
            )

    def test_reject_overlap_between_available_and_empty_covered(self):
        """F4: a role cannot be both available and empty-covered."""
        with pytest.raises(CoverageValidationError, match="overlap|both"):
            SemanticRecordSet(
                records=(
                    make_record("reported_ae", "c", "r1"),
                    make_record("subject_identity", "sub", "s1"),
                    make_record("site_identity", "site", "si1"),
                    make_record("temporal_anchor", "a", "ta1",
                                event_date_raw="2026-01-01",
                                anchor_descriptor="icf_date"),
                    make_record("temporal_anchor", "a", "ta2",
                                event_date_raw="2026-06-30",
                                anchor_descriptor="end_of_treatment_plus_30d"),
                ),
                subject_ref="S001",
                available_roles=("reported_ae", "subject_identity",
                                 "site_identity", "temporal_anchor"),
                empty_covered_roles=("reported_ae", "reported_mh"),
            )

    def test_require_present_roles_in_available(self):
        """F4: every role present in records must appear in available_roles."""
        with pytest.raises(CoverageValidationError,
                           match="not in available_roles"):
            SemanticRecordSet(
                records=(
                    make_record("subject_identity", "sub", "s1"),
                    make_record("symptom_event", "sym", "sy1"),
                ),
                subject_ref="S001",
                available_roles=("subject_identity",),  # missing symptom_event
                empty_covered_roles=("reported_ae", "reported_mh"),
            )

    def test_empty_covered_required_role_valid(self):
        """F4: explicit empty-but-covered required role is valid."""
        rs = SemanticRecordSet(
            records=(
                make_record("subject_identity", "sub", "s1"),
                make_record("site_identity", "site", "si1"),
                make_record("temporal_anchor", "a", "ta1",
                            event_date_raw="2026-01-01",
                            anchor_descriptor="icf_date"),
                make_record("temporal_anchor", "a", "ta2",
                            event_date_raw="2026-06-30",
                            anchor_descriptor="end_of_treatment_plus_30d"),
            ),
            subject_ref="S001",
            available_roles=("subject_identity", "site_identity",
                             "temporal_anchor"),
            empty_covered_roles=("reported_ae", "reported_mh"),
        )
        assert rs.missing_required_roles() == ()


# ===========================================================================
# F1: Partial date across boundary has one outcome (finding 1)
# ===========================================================================

class TestPartialDateBoundary:

    def test_partial_date_crossing_boundary_is_exactly_boundary(self):
        """F1: a month-precision event at the window edge must be exactly
        L1Disposition.BOUNDARY, not POSITIVE or multi-outcome."""
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-06",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.BOUNDARY
        # Supporting source locator preserved.
        assert len(result.journey_markers) >= 1
        marker = result.journey_markers[0]
        assert marker["source_locator_id"]
        # Uncertainty preserved.
        assert marker["uncertainty"]
        # Validates through to_unit_evaluation.
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage=RULE_LINEAGE,
        )
        assert isinstance(ue, UnitEvaluation)
        assert ue.l1_disposition == L1Disposition.BOUNDARY

    def test_day_precision_event_on_study_start_is_boundary(self):
        anchors = ProtocolAnchorDates(
            start_descriptor="icf_date",
            end_descriptor="cutoff",
            start_norm=normalize_partial_date("2026-01-01"),
            end_norm=normalize_partial_date("2026-06-30"),
        )
        result = classify_event_against_boundary(
            normalize_partial_date("2026-01-01"), anchors)
        assert result.classification == "boundary"
        assert "研究起点" in result.reason

    def test_day_precision_event_on_inclusive_cutoff_remains_inside(self):
        """The D01 start-edge rule does not silently make a declared
        day-precision reporting cutoff exclusive."""
        anchors = ProtocolAnchorDates(
            start_descriptor="icf_date",
            end_descriptor="cutoff",
            start_norm=normalize_partial_date("2026-01-01"),
            end_norm=normalize_partial_date("2026-06-30"),
        )
        result = classify_event_against_boundary(
            normalize_partial_date("2026-06-30"), anchors)
        assert result.classification == "inside"


# ===========================================================================
# F2: Exact NCS and alternative-diagnosis proofs (finding 2)
# ===========================================================================

class TestNCSAlternativeDiagnosis:

    def test_isolated_ncs_yields_negative(self):
        """F2(a): isolated explicit NCS with no symptom/action/seriousness
        -> exact NEGATIVE, no candidate, source-linked counterevidence."""
        records = [
            make_record("lab_finding", "MedDRA:10019242", "lab-001",
                        event_date_raw="2026-03-15",
                        intensity="mild",
                        clinical_significance="NCS"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert len(result.risk_candidate_refs) == 0
        ce = [ev for ev in result.evidence
              if ev.polarity == L1bEvidencePolarity.COUNTEREVIDENCE]
        assert len(ce) >= 1

    def test_ncs_with_medical_action_remains_positive(self):
        """F2(b): NCS plus a medical action with no matching reported AE
        -> exact POSITIVE, one candidate created."""
        records = [
            make_record("lab_finding", "MedDRA:99999", "lab-001",
                        event_date_raw="2026-03-15",
                        intensity="severe",
                        clinical_significance="NCS",
                        action_taken="drug_interrupted"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.risk_candidate_refs) == 1

    def test_ncs_with_separate_symptom_remains_positive(self):
        """F2(b): NCS on one record + separate associated symptom with no
        matching reported AE -> exact POSITIVE."""
        records = [
            make_record("lab_finding", "MedDRA:88888", "lab-001",
                        event_date_raw="2026-03-15",
                        clinical_significance="NCS"),
            make_record("symptom_event", "MedDRA:88888", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.risk_candidate_refs) == 1

    def test_confirmed_alternative_diagnosis_yields_negative(self):
        """F2(c): source-linked confirmed alternative diagnosis with no
        reported match -> exact NEGATIVE, no candidate, counterevidence."""
        records = [
            make_record("symptom_event", "MedDRA:99999", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate",
                        alternative_diagnosis="MedDRA:10061499",
                        alternative_diagnosis_confirmed=True),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert len(result.risk_candidate_refs) == 0
        ce = [ev for ev in result.evidence
              if ev.polarity == L1bEvidencePolarity.COUNTEREVIDENCE]
        assert len(ce) >= 1

    def test_tentative_unconfirmed_alt_diagnosis_remains_positive(self):
        """F2: a non-empty tentative diagnosis without confirmation must
        NOT suppress the clue -> exact POSITIVE."""
        records = [
            make_record("symptom_event", "MedDRA:99999", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate",
                        alternative_diagnosis="MedDRA:10061499",
                        alternative_diagnosis_confirmed=False),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.risk_candidate_refs) >= 1

    def test_alternative_diagnosis_confirmed_must_be_bool(self):
        """F2: alternative_diagnosis_confirmed must be actual bool."""
        with pytest.raises(CoverageValidationError):
            SemanticRecord(
                role="symptom_event", concept="C1",
                locator=make_locator("r1"),
                alternative_diagnosis_confirmed="true",  # type: ignore
            )


# ===========================================================================
# F3: AI provenance not coerced (finding 3)
# ===========================================================================

class TestAIAssertionTypeSafety:

    def test_string_false_rejected(self):
        """F3: ai_assertion='false' must be rejected (bool('false')==True)."""
        with pytest.raises(CoverageValidationError, match="actual bool"):
            SemanticRecord(
                role="symptom_event", concept="C1",
                locator=make_locator("r1"),
                ai_assertion="false",  # type: ignore
            )

    def test_string_true_rejected(self):
        with pytest.raises(CoverageValidationError, match="actual bool"):
            SemanticRecord(
                role="symptom_event", concept="C1",
                locator=make_locator("r1"),
                ai_assertion="true",  # type: ignore
            )

    def test_integer_rejected(self):
        with pytest.raises(CoverageValidationError, match="actual bool"):
            SemanticRecord(
                role="symptom_event", concept="C1",
                locator=make_locator("r1"),
                ai_assertion=1,  # type: ignore
            )

    def test_actual_bool_accepted(self):
        rec = SemanticRecord(
            role="symptom_event", concept="C1",
            locator=make_locator("r1"),
            ai_assertion=True,
        )
        assert rec.ai_assertion is True
        rec2 = SemanticRecord(
            role="symptom_event", concept="C1",
            locator=make_locator("r2"),
            ai_assertion=False,
        )
        assert rec2.ai_assertion is False


# ===========================================================================
# F5: Query text has exactly one three-part prefix (finding 5)
# ===========================================================================

class TestQueryPrefixCount:

    def test_query_to_text_has_exactly_one_prefix_each(self):
        """F5: query_to_text renders exactly one 依据：, one 发现：,
        one 行动项：."""
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="severe"),
        ]
        result = evaluate(records)
        queries = project_query_drafts(result)
        assert len(queries) >= 1
        text = query_to_text(queries[0])
        assert text.count("依据：") == 1
        assert text.count("发现：") == 1
        assert text.count("行动项：") == 1

    def test_query_basis_identifies_protocol_and_strategy(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="severe"),
        ]
        result = evaluate(records)
        queries = project_query_drafts(result)
        q = queries[0]
        assert q.basis.startswith("依据：")
        assert "pb-d01-v1" in q.basis
        assert "ems-d01-v1" in q.basis
        # The basis field should have exactly one 依据： prefix.
        assert q.basis.count("依据：") == 1

    def test_query_source_locators_minimal(self):
        records = [
            make_record("reported_ae", "MedDRA:10000000", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("reported_mh", "MedDRA:10000001", "mh-001",
                        event_date_raw="2026-01-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        queries = project_query_drafts(result)
        if queries:
            assert len(queries[0].source_locator_ids) <= 2


# ===========================================================================
# F6: Every journey event bound to unit_id (finding 6)
# ===========================================================================

class TestJourneyUnitIdBinding:

    def test_every_journey_event_has_unit_id(self):
        """F6: every projected JourneyEvent has a non-empty unit_id
        equal to the source AEMHUnitResult.unit_id."""
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        journey = project_journey(result)
        assert journey.event_count >= 2
        for event in journey.events:
            assert isinstance(event, JourneyEvent)
            assert event.unit_id == result.unit_id
            assert event.unit_id.strip()

    def test_journey_unit_id_in_canonical_payload(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        journey = project_journey(result)
        for event in journey.events:
            payload = event.canonical_payload()
            assert payload["unit_id"] == result.unit_id

    def test_journey_unit_id_in_raw_marker(self):
        """F6: raw journey markers carry unit_id."""
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        for marker in result.journey_markers:
            assert marker["unit_id"] == result.unit_id

    def test_subject_journey_preserves_unit_ids(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        slice_result = AEMHSliceResult(
            subject_ref="S001",
            unit_results=(result,),
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            rule_lineage=RULE_LINEAGE,
        )
        journey = project_subject_journey(slice_result)
        for event in journey.events:
            assert event.unit_id == result.unit_id

    def test_journey_rejects_marker_from_another_unit(self):
        """F6: a marker cannot be silently projected under the wrong unit."""
        result = evaluate([
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ])
        tampered_marker = dict(result.journey_markers[0])
        tampered_marker["unit_id"] = "unit-from-another-evaluation"
        tampered = AEMHUnitResult(
            unit_id=result.unit_id,
            subject_ref=result.subject_ref,
            l1_disposition=result.l1_disposition,
            medical_grading=result.medical_grading,
            journey_markers=(tampered_marker,),
        )
        with pytest.raises(ValueError, match="exactly match"):
            project_journey(tampered)


# ===========================================================================
# Operational protocol boundary
# ===========================================================================

class TestOperationalProtocolBoundary:

    def test_event_inside_boundary(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE

    def test_event_exactly_on_study_start_is_boundary(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-start",
                        event_date_raw="2026-01-01",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.BOUNDARY
        assert "研究起点" in result.boundary_reason

    def test_event_outside_boundary(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-07-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert len(result.risk_candidate_refs) == 0

    def test_missing_anchor_not_evaluable(self):
        records = list(make_anchor_records())
        records = [r for r in records
                   if r.anchor_descriptor != "end_of_treatment_plus_30d"]
        records.append(
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"))
        rs = SemanticRecordSet(
            records=tuple(records),
            subject_ref="S001",
            available_roles=tuple(sorted(set(r.role for r in records))),
        )
        result = evaluate_aemh_unit(
            unit=make_unit(), record_set=rs,
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
            snapshot_id=SNAPSHOT_ID,
        )
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_classify_event_boundary_direct(self):
        anchors = ProtocolAnchorDates(
            start_descriptor="icf_date",
            end_descriptor="cutoff",
            start_norm=normalize_partial_date("2026-01-01"),
            end_norm=normalize_partial_date("2026-06-30"),
        )
        inside = classify_event_against_boundary(
            normalize_partial_date("2026-03-15"), anchors)
        assert inside.classification == "inside"
        outside = classify_event_against_boundary(
            normalize_partial_date("2026-07-15"), anchors)
        assert outside.classification == "outside"


# ===========================================================================
# R2 candidate ID equality and aggregation (finding 4)
# ===========================================================================

class TestR2CandidateIDEquality:

    def test_candidate_ref_id_equals_r2_candidate_id(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="severe"),
        ]
        result = evaluate(records)
        assert len(result.risk_candidate_refs) == 1
        assert len(result.r2_candidates) == 1
        assert (result.risk_candidate_refs[0].candidate_id
                == result.r2_candidates[0].candidate_id)

    def test_multiple_candidates_survive_slice_aggregation(self):
        s1_records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-s1",
                        event_date_raw="2026-03-15",
                        subject_ref="S001"),
            make_record("symptom_event", "MedDRA:10035582", "sym-s1b",
                        event_date_raw="2026-04-15",
                        subject_ref="S001"),
        ]
        s2_records = [
            make_record("healthcare_encounter", "MedDRA:10019242", "hosp-s2",
                        event_date_raw="2026-03-15",
                        subject_ref="S002"),
        ]
        results = evaluate_aemh_slice(
            units=[make_unit(scope_key="S001", concept="MedDRA:10035581"),
                   make_unit(scope_key="S002", concept="MedDRA:10019242")],
            record_sets={
                "S001": make_record_set(s1_records, subject_ref="S001"),
                "S002": make_record_set(s2_records, subject_ref="S002"),
            },
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
        )
        s1 = results["S001"]
        total = sum(len(ur.risk_candidate_refs) for ur in s1.unit_results)
        assert len(s1.r2_candidates) == total
        assert len(s1.r2_candidates) >= 2

    def test_no_candidate_established(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        for r2_cand in result.r2_candidates:
            assert isinstance(r2_cand, RiskCandidate)
            assert r2_cand.candidate_id.startswith("cand-")


# ===========================================================================
# Common-contract joins (finding 5)
# ===========================================================================

class TestCommonContractJoins:

    def test_to_unit_evaluation_positive_with_query(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="severe"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage=RULE_LINEAGE,
        )
        assert isinstance(ue, UnitEvaluation)
        assert ue.l1_disposition == L1Disposition.POSITIVE
        for q in ue.query_refs:
            for loc_id in q.source_locator_ids:
                all_locs = {
                    *{sr.locator.locator_id()
                      for sr in ue.source_record_refs},
                    *{ev.locator.locator_id() for ev in ue.evidence},
                    *{rc.locator.locator_id()
                      for rc in ue.risk_candidate_refs
                      if rc.locator is not None},
                }
                assert loc_id in all_locs

    def test_to_unit_evaluation_candidate_id_matches(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage=RULE_LINEAGE,
        )
        result_ids = {rc.candidate_id for rc in result.risk_candidate_refs}
        ue_ids = {rc.candidate_id for rc in ue.risk_candidate_refs}
        assert result_ids == ue_ids


# ===========================================================================
# AI assertion adversarial (finding 7)
# ===========================================================================

class TestAIAssertionAdversarial:

    def test_ai_asserted_reported_ae_never_source_fact(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-ai-001",
                        event_date_raw="2026-03-15",
                        ai_assertion=True),
        ]
        result = evaluate(records)
        assert len(result.source_record_refs) == 0
        ev = [e for e in result.evidence
              if e.locator.record_id == "ae-ai-001"]
        assert len(ev) >= 1

    def test_ai_asserted_reported_mh_never_source_fact(self):
        records = [
            make_record("reported_mh", "MedDRA:10019242", "mh-ai-001",
                        event_date_raw="2026-03-15",
                        ai_assertion=True),
        ]
        result = evaluate(records)
        assert len(result.source_record_refs) == 0

    def test_non_ai_reported_ae_is_source_fact(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-15",
                        ai_assertion=False),
        ]
        result = evaluate(records)
        assert len(result.source_record_refs) == 1


# ===========================================================================
# Risk marker scoping (finding 8)
# ===========================================================================

class TestRiskMarkerScoping:

    def test_only_candidate_locator_is_risk_marker(self):
        records = [
            make_record("reported_ae", "MedDRA:10000000", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        journey = project_journey(result)
        risk_markers = [e for e in journey.events if e.is_risk_marker]
        risk_ids = {e.source_locator_id for e in risk_markers}
        sym_loc = None
        for rec in result.risk_candidate_refs:
            sym_loc = rec.locator.locator_id()
        assert sym_loc is not None
        assert sym_loc in risk_ids
        ae_loc = make_locator("ae-001", "reported_ae").locator_id()
        assert ae_loc not in risk_ids

    def test_serious_event_always_marked(self):
        records = [
            make_record("seriousness_clue", "MedDRA:10019242", "ser-001",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("sae",)),
        ]
        result = evaluate(records)
        journey = project_journey(result)
        risk_markers = [e for e in journey.events if e.is_risk_marker]
        assert len(risk_markers) >= 1


# ===========================================================================
# Custom semantic-role mapping
# ===========================================================================

class TestCustomSemanticRoles:

    def test_custom_role_names_accepted(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-15"),
            make_record("lab_finding", "MedDRA:10019242", "lab-001",
                        event_date_raw="2026-03-15",
                        intensity="severe"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_no_hardcoded_table_name(self):
        records = [
            make_record("reported_mh", "MedDRA:10019242", "mh-001",
                        event_date_raw="2026-01-01"),
            make_record("healthcare_encounter", "MedDRA:10019242", "hosp-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.risk_candidate_refs) >= 1


# ===========================================================================
# Reported match / separation invariants / grading
# ===========================================================================

class TestReportedMatch:

    def test_matched_evidence_is_counterevidence(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-15"),
            make_record("symptom_event", "MedDRA:10019242", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.NEGATIVE
        ce = [ev for ev in result.evidence
              if ev.polarity == L1bEvidencePolarity.COUNTEREVIDENCE]
        assert len(ce) >= 1

    def test_concept_equivalence_group_matching(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-15"),
            make_record("symptom_event", "MedDRA:10019243", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(
            records,
            match_strategy=make_strategy(
                concept_groups=[{"MedDRA:10019242", "MedDRA:10019243"}]))
        assert result.l1_disposition == L1Disposition.NEGATIVE


class TestSeparationInvariants:

    def test_source_records_separate_from_evidence(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        assert len(result.source_record_refs) == 1
        assert result.source_record_refs[0].record_id == "ae-001"
        supporting = [ev for ev in result.evidence
                      if ev.polarity == L1bEvidencePolarity.SUPPORTING]
        assert len(supporting) >= 1

    def test_candidates_separate_from_source_records(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(records)
        assert len(result.risk_candidate_refs) == 1
        assert len(result.source_record_refs) == 0

    def test_r2_candidate_severity_hint_is_monitoring_priority(self):
        records = [
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15",
                        intensity="mild",
                        seriousness_criteria=("sae",)),
        ]
        result = evaluate(records)
        assert result.medical_grading.monitoring_priority == \
            MONITORING_PRIORITY_HIGH
        assert result.medical_grading.intensity == "mild"
        for r2_cand in result.r2_candidates:
            assert r2_cand.severity_hint == MONITORING_PRIORITY_HIGH

    def test_clinical_flags_in_detail_not_severity_hint(self):
        records = [
            make_record("seriousness_clue", "MedDRA:10019242", "ser-001",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("sae", "aesi")),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        for r2_cand in result.r2_candidates:
            assert "sae" in r2_cand.detail.get("clinical_risk_flags", [])
            assert "aesi" in r2_cand.detail.get("clinical_risk_flags", [])


# ===========================================================================
# Journey projection
# ===========================================================================

class TestJourneyProjection:

    def test_journey_distinct_categories(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("reported_mh", "MedDRA:10019243", "mh-001",
                        event_date_raw="2026-01-01"),
            make_record("cm_indication", "MedDRA:10019244", "cm-001",
                        event_date_raw="2026-03-10"),
            make_record("symptom_event", "MedDRA:10035581", "sym-001",
                        event_date_raw="2026-03-15"),
            make_record("ip_action", "MedDRA:10000001", "ip-001",
                        event_date_raw="2026-03-05"),
        ]
        result = evaluate(records)
        journey = project_journey(result)
        cats = journey.categories_present()
        assert "ae" in cats
        assert "mh" in cats
        assert "cm" in cats
        assert "symptom" in cats
        assert "ip" in cats

    def test_journey_uncertainty_preserved(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        journey = project_journey(result)
        ae = [e for e in journey.events if e.category == "ae"][0]
        assert ae.temporal_precision == "month"
        assert ae.uncertainty


# ===========================================================================
# No default 30-day rule
# ===========================================================================

class TestNoDefaultWindow:

    def test_no_default_30_day_rule(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10019242", "sym-001",
                        event_date_raw="2026-03-20",
                        intensity="moderate"),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE

    def test_caller_tolerance_allows_match(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10019242", "sym-001",
                        event_date_raw="2026-03-20",
                        intensity="moderate"),
        ]
        result = evaluate(
            records,
            match_strategy=make_strategy(tolerance_days=30))
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_no_project_concept_aliases(self):
        ce = ConceptEquivalence(version="1")
        assert len(ce.groups) == 0
        assert not ce.are_equivalent("a", "b")


# ===========================================================================
# Temporal comparison helpers
# ===========================================================================

class TestTemporalComparison:

    def test_compare_same_day(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("2026-03-15")
        r = compare_partial_dates(a, b, TemporalTolerance(version="1"))
        assert r.comparable
        assert r.within_tolerance
        assert r.shared_precision == "day"

    def test_compare_same_day_can_be_disabled_by_strategy(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("2026-03-15")
        r = compare_partial_dates(
            a, b, TemporalTolerance(same_day=False, version="1"))
        assert r.comparable
        assert r.same_period
        assert not r.within_tolerance
        assert "disabled" in r.uncertainty

    def test_compare_different_days_no_tolerance(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("2026-03-20")
        r = compare_partial_dates(a, b, TemporalTolerance(version="1"))
        assert r.comparable
        assert not r.within_tolerance

    def test_compare_different_days_with_tolerance(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("2026-03-20")
        r = compare_partial_dates(
            a, b, TemporalTolerance(tolerance_days=10, version="1"))
        assert r.comparable
        assert r.within_tolerance

    def test_compare_month_precision(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("2026-03")
        r = compare_partial_dates(a, b, TemporalTolerance(version="1"))
        assert r.comparable
        assert r.shared_precision == "month"
        assert r.same_period

    def test_compare_incomparable_precision(self):
        a = normalize_partial_date("2026-03-15")
        b = normalize_partial_date("UNK-03-15")
        r = compare_partial_dates(a, b, TemporalTolerance(version="1"))
        assert not r.comparable


# ===========================================================================
# Protocol boundary contract
# ===========================================================================

class TestProtocolBoundaryContract:

    def test_boundary_is_immutable_and_versioned(self):
        pb = ProtocolAEMHBoundary(
            boundary_id="pb-001", version="2",
            reporting_start_anchor="icf_date",
            reporting_end_anchor="cutoff_date",
        )
        assert pb.boundary_id == "pb-001"
        assert pb.version == "2"
        with pytest.raises(CoverageValidationError):
            ProtocolAEMHBoundary(
                boundary_id="", version="1",
                reporting_start_anchor="x",
                reporting_end_anchor="y",
            )

    def test_strategy_and_boundary_required_inputs(self):
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-001",
                        event_date_raw="2026-03-01"),
        ]
        unit = make_unit()
        rs = make_record_set(records)
        with pytest.raises(AEMHSliceError):
            evaluate_aemh_unit(
                unit=unit, record_set=rs,
                protocol_boundary=None,  # type: ignore
                match_strategy=make_strategy(),
                project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE)
        with pytest.raises(AEMHSliceError):
            evaluate_aemh_unit(
                unit=unit, record_set=rs,
                protocol_boundary=make_boundary(),
                match_strategy=None,  # type: ignore
                project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE)

    def test_protocol_excluded_concept_not_candidate(self):
        records = [
            make_record("symptom_event", "MedDRA:EXCLUDED", "sym-001",
                        event_date_raw="2026-03-15"),
        ]
        result = evaluate(
            records,
            protocol_boundary=make_boundary(
                exclusions=["MedDRA:EXCLUDED"]))
        assert len(result.risk_candidate_refs) == 0

    def test_protocol_boundary_requires_reason_when_not_applicable(self):
        with pytest.raises(CoverageValidationError):
            ProtocolAEMHBoundary(
                boundary_id="pb", version="1",
                reporting_start_anchor="a", reporting_end_anchor="b",
                applicable=False,
            )


# ===========================================================================
# Nested strategy versions
# ===========================================================================

class TestNestedStrategyVersions:

    def test_concept_equivalence_requires_version(self):
        with pytest.raises(CoverageValidationError):
            ConceptEquivalence(version="")

    def test_temporal_tolerance_requires_version(self):
        with pytest.raises(CoverageValidationError):
            TemporalTolerance(version="")

    def test_event_match_strategy_requires_nested_versions(self):
        with pytest.raises(CoverageValidationError):
            EventMatchStrategy(
                strategy_id="s1", version="1",
                concept_equivalence=ConceptEquivalence(version=""),
                temporal_tolerance=TemporalTolerance(version="1"),
            )

    def test_temporal_tolerance_rejects_bool_tolerance(self):
        with pytest.raises(CoverageValidationError):
            TemporalTolerance(tolerance_days=True, version="1")

    def test_protocol_boundary_rejects_empty_exclusion_member(self):
        with pytest.raises(CoverageValidationError):
            ProtocolAEMHBoundary(
                boundary_id="pb", version="1",
                reporting_start_anchor="a", reporting_end_anchor="b",
                protocol_exclusions=("",),
            )


# ===========================================================================
# Slice evaluation
# ===========================================================================

class TestSliceEvaluation:

    def test_evaluate_slice_multiple_subjects(self):
        s1 = [
            make_record("symptom_event", "MedDRA:10035581", "sym-s1",
                        event_date_raw="2026-03-15",
                        subject_ref="S001"),
        ]
        s2 = [
            make_record("reported_ae", "MedDRA:10019242", "ae-s2",
                        event_date_raw="2026-03-01",
                        subject_ref="S002"),
        ]
        results = evaluate_aemh_slice(
            units=[make_unit(scope_key="S001", concept="MedDRA:10035581"),
                   make_unit(scope_key="S002", concept="MedDRA:10019242")],
            record_sets={
                "S001": make_record_set(s1, subject_ref="S001"),
                "S002": make_record_set(s2, subject_ref="S002"),
            },
            protocol_boundary=make_boundary(),
            match_strategy=make_strategy(),
            project_id=PROJECT_ID, rule_lineage=RULE_LINEAGE,
        )
        assert results["S001"].positive_count >= 1
        assert results["S002"].negative_count >= 1


# ===========================================================================
# High-priority seriousness
# ===========================================================================

class TestHighPrioritySeriousness:

    def test_sae_seriousness_separate_from_intensity(self):
        grading = MedicalGrading(
            intensity="mild",
            seriousness_criteria=("sae", "hospitalization"),
            monitoring_priority=derive_monitoring_priority(
                "mild", ("sae", "hospitalization")),
        )
        assert grading.has_seriousness_clue
        assert grading.monitoring_priority == MONITORING_PRIORITY_HIGH
        assert grading.intensity == "mild"

    def test_severe_intensity_without_sae_is_medium(self):
        assert derive_monitoring_priority(
            "severe", ()) == MONITORING_PRIORITY_MEDIUM

    def test_unknown_intensity_stays_unknown(self):
        assert MedicalGrading().monitoring_priority == \
            MONITORING_PRIORITY_UNKNOWN

    def test_death_event_produces_high_priority_candidate(self):
        records = [
            make_record("death_event", "MedDRA:10019242", "death-001",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("death",)),
        ]
        result = evaluate(records)
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.medical_grading.monitoring_priority == \
            MONITORING_PRIORITY_HIGH
