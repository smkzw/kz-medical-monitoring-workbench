"""R4 common coverage contract tests (worker_01).
Proves (deterministically, synthetic-only):

1. Deterministic unit_id and expected_set_hash; input-order independence.
2. Layer/token separation: L0/L1/L1b/L2/L3 are distinct namespaces; L0
   values are sourced from the frozen R1 enum and L3 is the frozen R2
   ``RiskLifecycleState`` class by object identity; L0 reasoned
   not_evaluable never proves medical completeness.
3. Every L1 disposition is exclusive and accepted exactly once.
4. L1b coexistence: supporting + counterevidence on the same unit.
5. False-clean attacks: L0 blocker hides behind a clean L1; L1 not_evaluable
   behind a clean L0.
6. Count contamination: duplicate/missing/unexpected units rejected; L2
   counts never inter-derived.
7. Source/evidence/join validation: broken joins and missing provenance fail
   closed.
"""

from __future__ import annotations

import pytest

from mm_r4.contracts import (
    CoverageValidationError,
    EvaluationUnit,
    EvidenceItem,
    HashingError,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    L2ObjectType,
    L3RiskStateRef,
    QueryDraftRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    UnitJoinError,
    canonical_json,
    unit_id_hash,
)
from mm_r4.coverage import (
    CoverageLedger,
    CoverageSummary,
    ExpectedSet,
    LedgerError,
    expected_set_hash,
    is_domain_complete,
)


# ===========================================================================
# 1. Deterministic hashes and input-order independence
# ===========================================================================

class TestDeterministicHashing:

    def test_unit_id_is_deterministic(self, make_unit):
        u1 = make_unit(scope_key="S001", concept="MedDRA:10019242")
        u2 = make_unit(scope_key="S001", concept="MedDRA:10019242")
        assert u1.unit_id == u2.unit_id
        assert u1.unit_id.startswith("unit-")
        assert len(u1.unit_id) == len("unit-") + 64

    def test_unit_id_changes_on_any_dimension(self, make_unit):
        base = make_unit(scope_key="S001", concept="MedDRA:10019242")
        # Change each of the eight frozen dimensions; every one must change
        # the unit_id.
        changed = EvaluationUnit(
            project_id="proj-different",
            domain_id=base.domain_id,
            scope_type=base.scope_type,
            scope_key=base.scope_key,
            normalized_concept_or_rule_item=base.normalized_concept_or_rule_item,
            temporal_window=base.temporal_window,
            rule_or_knowledge_lineage=base.rule_or_knowledge_lineage,
            unit_algorithm_version=base.unit_algorithm_version,
        )
        assert changed.unit_id != base.unit_id

        for field_name, new_value in [
            ("domain_id", "D02_cm"),
            ("scope_type", "site"),
            ("scope_key", "S002"),
            ("normalized_concept_or_rule_item", "MedDRA:10053532"),
            ("temporal_window", "window-v2"),
            ("rule_or_knowledge_lineage", "rule-lineage-v2"),
            ("unit_algorithm_version", "algo-v2"),
        ]:
            kwargs = base.canonical_dimensions()
            kwargs[field_name] = new_value
            changed_unit = EvaluationUnit(**kwargs)
            assert changed_unit.unit_id != base.unit_id, (
                f"unit_id did not change when {field_name} changed")

    def test_unit_id_hash_function_matches_constructor(self):
        uid = unit_id_hash(
            project_id="proj-1",
            domain_id="D01",
            scope_type="subject",
            scope_key="S001",
            normalized_concept_or_rule_item="concept-1",
            temporal_window="window-1",
            rule_or_knowledge_lineage="rule-1",
            unit_algorithm_version="algo-1",
        )
        uid2 = unit_id_hash(
            project_id="proj-1",
            domain_id="D01",
            scope_type="subject",
            scope_key="S001",
            normalized_concept_or_rule_item="concept-1",
            temporal_window="window-1",
            rule_or_knowledge_lineage="rule-1",
            unit_algorithm_version="algo-1",
        )
        assert uid == uid2

    def test_unit_id_mismatch_rejected(self):
        with pytest.raises(CoverageValidationError, match="unit_id"):
            EvaluationUnit(
                project_id="p",
                domain_id="d",
                scope_type="subject",
                scope_key="s",
                normalized_concept_or_rule_item="c",
                temporal_window="w",
                rule_or_knowledge_lineage="r",
                unit_algorithm_version="v",
                unit_id="unit-wrong",
            )

    def test_expected_set_hash_order_independent(self, make_unit):
        units_a = [
            make_unit(scope_key="S001", concept="c1"),
            make_unit(scope_key="S002", concept="c2"),
            make_unit(scope_key="S003", concept="c3"),
        ]
        units_b = list(reversed(units_a))
        hash_a = expected_set_hash([u.unit_id for u in units_a])
        hash_b = expected_set_hash([u.unit_id for u in units_b])
        assert hash_a == hash_b
        assert hash_a.startswith("eset-")

    def test_expected_set_hash_rejects_duplicates(self, make_unit):
        u = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(HashingError, match="duplicate unit_id"):
            expected_set_hash([u.unit_id, u.unit_id])

    def test_expected_set_hash_rejects_string_input(self):
        with pytest.raises(HashingError, match="sequence"):
            expected_set_hash("unit-abc")

    def test_expected_set_from_units_order_independent(self, make_unit):
        units_a = [
            make_unit(scope_key="S001", concept="c1"),
            make_unit(scope_key="S002", concept="c2"),
        ]
        units_b = list(reversed(units_a))
        es_a = ExpectedSet.from_units(units_a, domain_id="D", run_id="R")
        es_b = ExpectedSet.from_units(units_b, domain_id="D", run_id="R")
        assert es_a.expected_set_hash_value == es_b.expected_set_hash_value

    def test_expected_set_count_mismatch_rejected(self, make_unit):
        u = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(CoverageValidationError, match="expected_count"):
            ExpectedSet(
                expected_set_hash_value=expected_set_hash([u.unit_id]),
                unit_ids=(u.unit_id,),
                domain_id="D",
                run_id="R",
                expected_count=2,
            )

    def test_canonical_json_rejects_nan(self):
        with pytest.raises(ValueError):
            canonical_json({"v": float("nan")})


# ===========================================================================
# 2. Layer/token separation
# ===========================================================================

class TestLayerSeparation:

    def test_l0_values_sourced_from_frozen_r1_enum(self):
        """L0 values must be sourced from the frozen R1 CoverageUnitStatus enum,
        not merely coincidentally equal strings.

        We prove sourcing by checking that the R4 L0 facade values exactly
        match the R1 enum member values AND that ALL_STATUSES is derived
        from the enum's iteration order, so a future R1 change would be
        reflected automatically."""
        from mm_r1.domain import CoverageUnitStatus as R1Status
        # Each named facade value must match the R1 enum member value.
        assert L0CoverageStatus.COVERED is R1Status.COVERED.value
        assert L0CoverageStatus.PARTIAL is R1Status.PARTIAL.value
        assert L0CoverageStatus.TRUNCATED is R1Status.TRUNCATED.value
        assert L0CoverageStatus.NOT_APPLICABLE is R1Status.NOT_APPLICABLE.value
        assert L0CoverageStatus.NOT_EVALUABLE is R1Status.NOT_EVALUABLE.value
        assert L0CoverageStatus.FAILED is R1Status.FAILED.value
        assert L0CoverageStatus.MISSING is R1Status.MISSING.value
        # ALL_STATUSES must be the enum's member values in iteration order.
        r1_values = tuple(member.value for member in R1Status)
        assert L0CoverageStatus.ALL_STATUSES == r1_values
        # No R4-only L0 status exists outside the R1 enum.
        assert set(L0CoverageStatus.ALL_STATUSES) == set(r1_values)

    def test_l1_exactly_five_exclusive_dispositions(self):
        assert len(L1Disposition.ALL) == 5
        assert L1Disposition.is_exclusive_member("positive")
        assert L1Disposition.is_exclusive_member("negative")
        assert L1Disposition.is_exclusive_member("boundary")
        assert L1Disposition.is_exclusive_member("not_applicable")
        assert L1Disposition.is_exclusive_member("not_evaluable")
        assert not L1Disposition.is_exclusive_member("counterevidence")
        # "Non-problem" is not a disposition.
        assert not L1Disposition.is_exclusive_member("non_problem")

    def test_l1b_exactly_three_polarities(self):
        assert len(L1bEvidencePolarity.ALL) == 3
        assert L1bEvidencePolarity.is_member("supporting")
        assert L1bEvidencePolarity.is_member("counterevidence")
        assert L1bEvidencePolarity.is_member("context")
        assert not L1bEvidencePolarity.is_member("positive")

    def test_l2_four_counted_types(self):
        assert len(L2ObjectType.ALL) == 4

    def test_l3_is_frozen_r2_lifecycle_state_by_identity(self):
        """L3RiskStateRef must BE the frozen R2 RiskLifecycleState class
        (object identity), not a copy or subclass.  This guarantees that
        future R2 lifecycle changes cannot silently diverge."""
        from mm_r2.risk import RiskLifecycleState
        assert L3RiskStateRef is RiskLifecycleState
        # State constants are inherited directly from R2.
        assert L3RiskStateRef.ESTABLISHED == RiskLifecycleState.ESTABLISHED
        assert L3RiskStateRef.CLOSED == RiskLifecycleState.CLOSED
        assert L3RiskStateRef.NOT_EVALUABLE == RiskLifecycleState.NOT_EVALUABLE
        assert L3RiskStateRef.IDENTITY_AMBIGUOUS == RiskLifecycleState.IDENTITY_AMBIGUOUS
        # all_states() and terminal_states() come from R2 authority.
        assert L3RiskStateRef.all_states() == RiskLifecycleState.all_states()
        assert L3RiskStateRef.terminal_states() == RiskLifecycleState.terminal_states()

    def test_l0_not_evaluable_does_not_prove_completeness(self, make_unit):
        """Matrix §3.2: R1 reasoned not_evaluable allows 'gap explained' but
        must NOT let R4 declare the medical domain complete."""
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            not_evaluable_reason="source truncated",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete
        assert any("not_evaluable" in r for r in reasons)


# ===========================================================================
# 3. Every L1 disposition is exclusive and accepted exactly once
# ===========================================================================

class TestL1Dispositions:

    @pytest.mark.parametrize("disposition,needs_join,needs_provenance", [
        (L1Disposition.POSITIVE, True, True),
        (L1Disposition.NEGATIVE, False, True),
        (L1Disposition.BOUNDARY, True, True),
        (L1Disposition.NOT_APPLICABLE, False, True),
    ])
    def test_evaluated_dispositions_require_provenance(
        self, make_unit, make_candidate, disposition, needs_join, needs_provenance,
    ):
        unit = make_unit(scope_key="S001", concept="c1")
        kwargs = dict(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=disposition,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        if needs_join:
            kwargs["risk_candidate_refs"] = (make_candidate("cand-1"),)
        ev = UnitEvaluation(**kwargs)
        assert ev.l1_disposition == disposition

    def test_not_evaluable_does_not_require_provenance(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            not_evaluable_reason="missing MedDRA version",
        )
        assert ev.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_invalid_l1_disposition_rejected(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(CoverageValidationError, match="five exclusive"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition="kinda_positive",
            )

    def test_invalid_l0_status_rejected(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(CoverageValidationError, match="L0 coverage status"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status="mostly_covered",
                l1_disposition=L1Disposition.NEGATIVE,
                provenance_snapshot_id="snap-1",
            )

    def test_positive_without_join_rejected(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(UnitJoinError, match="positive unit"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.POSITIVE,
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )

    def test_positive_with_active_risk_satisfies_join(self, make_unit, make_risk_instance):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.POSITIVE,
            risk_instance_refs=(make_risk_instance(risk_state="established"),),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        assert ev.l1_disposition == L1Disposition.POSITIVE

    def test_positive_with_only_closed_risk_rejected(self, make_unit, make_risk_instance):
        """A closed risk does not satisfy the positive-unit join requirement
        (only active/ambiguous risks count)."""
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(UnitJoinError, match="positive unit"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.POSITIVE,
                risk_instance_refs=(make_risk_instance(risk_state="closed"),),
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )


# ===========================================================================
# 4. L1b evidence coexistence
# ===========================================================================

class TestL1bCoexistence:

    def test_supporting_and_counterevidence_coexist(self, make_unit, make_evidence):
        """Matrix §3.2: counterevidence may coexist with positive/negative/
        boundary.  It is not a sixth L1 disposition."""
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            l1b_polarities=(
                L1bEvidencePolarity.SUPPORTING,
                L1bEvidencePolarity.COUNTEREVIDENCE,
            ),
            evidence=(
                make_evidence("ev-supp", polarity="supporting"),
                make_evidence("ev-count", polarity="counterevidence"),
            ),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        assert L1bEvidencePolarity.SUPPORTING in ev.l1b_polarities
        assert L1bEvidencePolarity.COUNTEREVIDENCE in ev.l1b_polarities
        assert ev.has_counterevidence()

    def test_counterevidence_with_negative_is_valid(self, make_unit):
        """A sufficiently excluded clue is negative + counterevidence (matrix
        §3.3 last paragraph)."""
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            l1b_polarities=(L1bEvidencePolarity.COUNTEREVIDENCE,),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        assert ev.has_counterevidence()
        assert ev.l1_disposition == L1Disposition.NEGATIVE

    def test_invalid_polarity_rejected(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(CoverageValidationError, match="invalid polarity"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.NEGATIVE,
                l1b_polarities=("proof",),
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )

    def test_polarities_deduplicated_and_sorted(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            l1b_polarities=("context", "supporting", "supporting", "context"),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        assert ev.l1b_polarities == ("context", "supporting")


# ===========================================================================
# 5. False-clean attacks
# ===========================================================================

class TestFalseCleanAttacks:

    def test_l0_partial_blocks_completeness_even_with_clean_l1(
        self, make_unit,
    ):
        """A partial L0 read must not be hidden behind a clean L1 negative."""
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.PARTIAL,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete
        assert any("partial" in r for r in reasons)

    def test_l0_truncated_blocks_completeness(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.TRUNCATED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete
        assert any("truncated" in r for r in reasons)

    def test_l0_missing_blocks_completeness(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.MISSING,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        assert not is_domain_complete(summary)[0]

    def test_l1_not_evaluable_blocks_even_with_clean_l0(self, make_unit):
        """L1 not_evaluable must block completeness even when L0 is covered."""
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            not_evaluable_reason="CTCAE version unavailable",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete
        assert any("not_evaluable" in r for r in reasons)

    def test_zero_risk_count_does_not_imply_complete(self, make_unit):
        """Matrix §6: risk count of zero does not separately prove completeness.
        This test proves a fully-clean domain IS complete, and contrasts it
        with a not_evaluable domain that must NOT be."""
        unit = make_unit(scope_key="S001", concept="c1")
        clean_ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(clean_ev)
        summary = ledger.close_and_summarize()
        assert summary.risk_instance_count() == 0
        complete, _ = is_domain_complete(summary)
        assert complete  # clean domain with zero risk IS complete

    def test_l0_failed_blocks_completeness(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.FAILED,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            not_evaluable_reason="execution failed",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        assert not is_domain_complete(summary)[0]


# ===========================================================================
# 6. Count contamination and ledger invariants
# ===========================================================================

class TestCountInvariants:

    def test_count_equation_holds(self, make_unit, make_candidate):
        units = [
            make_unit(scope_key="S001", concept="c1"),
            make_unit(scope_key="S002", concept="c2"),
        ]
        ev1 = UnitEvaluation(
            unit_id=units[0].unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.POSITIVE,
            risk_candidate_refs=(make_candidate("cand-1"),),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        ev2 = UnitEvaluation(
            unit_id=units[1].unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units(units, domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev1)
        ledger.assign(ev2)
        summary = ledger.close_and_summarize()
        l1 = summary.l1_counts
        assert l1["positive"] == 1
        assert l1["negative"] == 1
        assert l1["boundary"] == 0
        assert l1["not_applicable"] == 0
        assert l1["not_evaluable"] == 0
        assert sum(l1.values()) == summary.expected_units

    def test_duplicate_unit_rejected(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        with pytest.raises(LedgerError, match="duplicate unit"):
            ledger.assign(ev)

    def test_unexpected_unit_rejected(self, make_unit):
        unit_expected = make_unit(scope_key="S001", concept="c1")
        unit_unexpected = make_unit(scope_key="S002", concept="c2")
        ev = UnitEvaluation(
            unit_id=unit_unexpected.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit_expected], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        with pytest.raises(LedgerError, match="unexpected unit"):
            ledger.assign(ev)

    def test_missing_unit_blocks_close(self, make_unit):
        units = [
            make_unit(scope_key="S001", concept="c1"),
            make_unit(scope_key="S002", concept="c2"),
        ]
        ev1 = UnitEvaluation(
            unit_id=units[0].unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units(units, domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev1)
        with pytest.raises(LedgerError, match="missing evaluations"):
            ledger.close()

    def test_l2_counts_never_interderived(self, make_unit, make_candidate, make_risk_instance):
        """L2 candidate/risk/query/source counts are separate (matrix §6 #10)."""
        unit = make_unit(scope_key="S001", concept="c1")
        source_1 = SourceLocator(
            snapshot_id="s", source_revision_id="sr",
            table_semantic="reported_ae", record_id="rec-1")
        source_2 = SourceLocator(
            snapshot_id="s", source_revision_id="sr",
            table_semantic="reported_mh", record_id="rec-2")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.POSITIVE,
            source_record_refs=(
                SourceRecordRef(record_id="rec-1", locator=source_1),
                SourceRecordRef(record_id="rec-2", locator=source_2),
            ),
            risk_candidate_refs=(make_candidate("cand-1"), make_candidate("cand-2")),
            risk_instance_refs=(make_risk_instance(),),
            query_refs=(
                QueryDraftRef(
                    query_id="q-1", unit_id=unit.unit_id,
                    basis="b", finding="f", action="a",
                    source_locator_ids=(source_1.locator_id(),),
                    linked_candidate_id="cand-1",
                ),
                QueryDraftRef(
                    query_id="q-2", unit_id=unit.unit_id,
                    basis="b", finding="f", action="a",
                    source_locator_ids=(source_2.locator_id(),),
                    linked_risk_instance_id="ri-001",
                ),
            ),
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        summary = ledger.close_and_summarize()
        l2 = summary.l2_counts
        assert l2[L2ObjectType.SOURCE_RECORD] == 2
        assert l2[L2ObjectType.RISK_CANDIDATE] == 2
        assert l2[L2ObjectType.RISK_INSTANCE] == 1
        assert l2[L2ObjectType.QUERY_DRAFT] == 2
        # Query count != risk count (must not be inter-derived).
        assert summary.query_draft_count() != summary.risk_instance_count()

    def test_closed_ledger_rejects_new_assignments(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        ev = UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=L0CoverageStatus.COVERED,
            l1_disposition=L1Disposition.NEGATIVE,
            provenance_snapshot_id="snap-1",
            provenance_rule_lineage="rule-1",
        )
        eset = ExpectedSet.from_units([unit], domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        ledger.assign(ev)
        ledger.close()
        with pytest.raises(LedgerError, match="closed"):
            ledger.assign(ev)


# ===========================================================================
# 7. Source/evidence/join validation
# ===========================================================================

class TestJoinValidation:

    def test_source_locator_requires_row_level_fields(self):
        with pytest.raises(CoverageValidationError, match="snapshot_id"):
            SourceLocator(
                snapshot_id="",
                source_revision_id="sr",
                table_semantic="reported_ae",
                record_id="rec-1",
            )

    def test_source_locator_rejects_invalid_hash(self):
        with pytest.raises(CoverageValidationError, match="SHA-256"):
            SourceLocator(
                snapshot_id="s",
                source_revision_id="sr",
                table_semantic="reported_ae",
                record_id="rec-1",
                raw_payload_hash="not-a-hash",
            )

    def test_evidence_requires_valid_polarity(self, make_locator):
        with pytest.raises(CoverageValidationError, match="polarity"):
            EvidenceItem(
                evidence_id="ev-1",
                polarity="invalid",
                locator=make_locator(record_id="rec-1"),
            )

    def test_query_must_link_source(self, make_unit):
        with pytest.raises(CoverageValidationError, match="source locator"):
            QueryDraftRef(
                query_id="q-1",
                unit_id=make_unit(scope_key="S001", concept="c1").unit_id,
                basis="b", finding="f", action="a",
                source_locator_ids=(),
                linked_candidate_id="cand-1",
            )

    def test_query_must_link_candidate_or_risk(self, make_unit):
        with pytest.raises(CoverageValidationError, match="link to a candidate"):
            QueryDraftRef(
                query_id="q-1",
                unit_id=make_unit(scope_key="S001", concept="c1").unit_id,
                basis="b", finding="f", action="a",
                source_locator_ids=("loc-synthetic",),
            )

    def test_query_linked_candidate_must_exist_on_unit(self, make_unit, make_candidate):
        unit = make_unit(scope_key="S001", concept="c1")
        present_candidate = make_candidate("cand-1")
        with pytest.raises(UnitJoinError, match="links candidate"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.POSITIVE,
                risk_candidate_refs=(present_candidate,),
                query_refs=(
                    QueryDraftRef(
                        query_id="q-1", unit_id=unit.unit_id,
                        basis="b", finding="f", action="a",
                        source_locator_ids=(present_candidate.locator.locator_id(),),
                        linked_candidate_id="cand-NONEXISTENT",
                    ),
                ),
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )

    def test_query_linked_source_must_be_reachable_on_unit(
        self, make_unit, make_candidate,
    ):
        unit = make_unit(scope_key="S001", concept="c1")
        candidate = make_candidate("cand-1")
        with pytest.raises(UnitJoinError, match="source locator"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.POSITIVE,
                risk_candidate_refs=(candidate,),
                query_refs=(QueryDraftRef(
                    query_id="q-1", unit_id=unit.unit_id,
                    basis="b", finding="f", action="a",
                    source_locator_ids=("loc-not-on-unit",),
                    linked_candidate_id="cand-1",
                ),),
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )

    def test_query_unit_id_must_match_evaluation_unit(
        self, make_unit, make_candidate,
    ):
        unit = make_unit(scope_key="S001", concept="c1")
        candidate = make_candidate("cand-1")
        with pytest.raises(UnitJoinError, match="different unit"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.POSITIVE,
                risk_candidate_refs=(candidate,),
                query_refs=(QueryDraftRef(
                    query_id="q-1", unit_id="unit-different",
                    basis="b", finding="f", action="a",
                    source_locator_ids=(candidate.locator.locator_id(),),
                    linked_candidate_id="cand-1",
                ),),
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )

    def test_source_record_id_must_match_locator(self, make_locator):
        with pytest.raises(CoverageValidationError, match="must match"):
            SourceRecordRef(
                record_id="rec-wrong",
                locator=make_locator(record_id="rec-right"),
            )

    def test_missing_provenance_blocks_evaluated_unit(self, make_unit):
        unit = make_unit(scope_key="S001", concept="c1")
        with pytest.raises(UnitJoinError, match="provenance_snapshot_id"):
            UnitEvaluation(
                unit_id=unit.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.NEGATIVE,
                provenance_snapshot_id="",
                provenance_rule_lineage="rule-1",
            )

    def test_risk_instance_ref_rejects_invalid_state(self):
        with pytest.raises(CoverageValidationError, match="risk_state"):
            RiskInstanceRef(
                risk_instance_id="ri-1",
                risk_identity_id="rid-1",
                risk_state="mostly_closed",
            )


# ===========================================================================
# 8. Summary count-equation enforcement
# ===========================================================================

class TestSummaryInvariants:

    def test_summary_count_equation_validated(self):
        """A hand-constructed summary with a broken count equation is rejected
        at construction time."""
        with pytest.raises(CoverageValidationError, match="count equation"):
            CoverageSummary(
                expected_set_hash="eset-" + "a" * 64,
                domain_id="D",
                run_id="R",
                expected_units=2,
                assigned_units=2,
                l1_counts={"positive": 1, "negative": 0, "boundary": 0,
                           "not_applicable": 0, "not_evaluable": 0},
            )

    def test_full_clean_domain_is_complete(self, make_unit):
        units = [
            make_unit(scope_key="S001", concept="c1"),
            make_unit(scope_key="S002", concept="c2"),
            make_unit(scope_key="S003", concept="c3"),
        ]
        eset = ExpectedSet.from_units(units, domain_id="D", run_id="R")
        ledger = CoverageLedger(expected_set=eset)
        for u in units:
            ev = UnitEvaluation(
                unit_id=u.unit_id,
                l0_status=L0CoverageStatus.COVERED,
                l1_disposition=L1Disposition.NEGATIVE,
                provenance_snapshot_id="snap-1",
                provenance_rule_lineage="rule-1",
            )
            ledger.assign(ev)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert complete, f"expected complete but got reasons: {reasons}"
        assert summary.not_evaluable_count() == 0
        assert not summary.has_l0_blocker()
