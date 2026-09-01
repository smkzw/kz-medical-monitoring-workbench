"""R3-C integration test: snapshot diff + rule lifecycle + impact propagation.

Exercises the full R3-C flow end-to-end on synthetic data, proving the
contracts compose correctly:

1. Build facts from two snapshots using R3-B identity.
2. Diff them; classify changes.
3. Propagate clinical impact.
4. Draft a natural-language rule; simulate; activate with a frozen scope.
5. Verify the rule evaluation + diff + impact compose without contract breaks.

This test also proves the three heterogeneous listing shapes from R3-A
fixtures work with R3-C diff and rules without project/path hardcoding.
"""

from __future__ import annotations

import pytest

from mm_r3.identity import IdentityAlgorithm
from mm_r3.rules import (
    ConditionOperator,
    EvaluationScope,
    EvaluationScopeKind,
    RuleCondition,
    RuleDraft,
    RuleDraftStatus,
    activate_rule,
    simulate_rule,
)
from mm_r3.snapshot_diff import (
    ChangeKind,
    ImpactKind,
    ScopeCoverageNote,
    build_snapshot_facts,
    diff_snapshots,
    propagate_impact,
)


# ===========================================================================
# Full lifecycle integration
# ===========================================================================

class TestFullLifecycleIntegration:
    """End-to-end: snapshot → diff → impact → rule draft → simulate → activate."""

    def setup_method(self):
        self.alg = IdentityAlgorithm(
            "subject_event", ["SUBJECT", "EVENT"], key_normalize="display"
        )
        # baseline: two records
        self.baseline_rows = [
            {"_row_index": i, "SUBJECT": s, "EVENT": e, "VALUE": v, "DOMAIN": d}
            for i, (s, e, v, d) in enumerate([
                ("S001", "AE001", 3, "AE"),
                ("S002", "AE002", 1, "AE"),
            ])
        ]
        # current: S001 modified, S002 disappeared, S003 added
        self.current_rows = [
            {"SUBJECT": "S001", "EVENT": "AE001", "VALUE": 5, "DOMAIN": "AE"},
            {"SUBJECT": "S003", "EVENT": "AE003", "VALUE": 4, "DOMAIN": "AE"},
        ]

    def test_full_diff_and_impact(self):
        base, res_b = build_snapshot_facts(
            "proj-synth", "rev-base", self.alg, self.baseline_rows,
            coverage_scope={"domain": "ae"},
        )
        assert res_b.is_clean

        curr, res_c = build_snapshot_facts(
            "proj-synth", "rev-curr", self.alg, self.current_rows,
            coverage_scope={"domain": "ae"},
        )
        assert res_c.is_clean

        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1
        assert diff.n_disappeared == 1  # S002 absent, no coverage note
        assert diff.n_added == 1       # S003
        assert diff.n_unchanged == 0

        impact = propagate_impact(diff)
        assert impact.n_data_correction == 1
        assert impact.n_potential_loss == 1
        assert impact.n_new_finding == 1
        assert impact.requires_review_count == 3

    def test_rule_lifecycle_after_diff(self):
        """Draft a rule, simulate against current records, activate."""
        base, _ = build_snapshot_facts(
            "proj-synth", "rev-base", self.alg, self.baseline_rows
        )
        curr, _ = build_snapshot_facts(
            "proj-synth", "rev-curr", self.alg, self.current_rows
        )
        diff = diff_snapshots(base, curr)

        # Draft a rule: flag VALUE >= 4
        draft = RuleDraft(
            draft_id="draft-sev",
            project_id="proj-synth",
            rule_name="high_severity_flag",
            natural_language="Flag any event with VALUE >= 4",
            conditions=(
                RuleCondition("VALUE", ConditionOperator.GE, 4,
                              extracted_from="VALUE >= 4"),
            ),
            source_revision_id="rev-base",
            domain_hint="AE",
            severity_hint="high",
        )
        assert draft.status == RuleDraftStatus.DRAFT

        # Simulate against the current snapshot's records
        records = [
            {"_record_id": f"rec-{d}", **dict(p)}
            for d, p in curr.records
        ]
        sim = simulate_rule(draft, records)
        assert sim.outcome.n_total == 2
        # S001 has VALUE=5 (>=4), S003 has VALUE=4 (>=4)
        assert sim.outcome.n_matched == 2

        # Activate with full-history scope
        scope = EvaluationScope(
            scope_kind=EvaluationScopeKind.FULL_HISTORY,
            domain_scope=("AE",),
        )
        activation = activate_rule(
            draft, sim, version="1", evaluation_scope=scope,
            activated_by="local_test_user",
            is_machine=False,
            user_confirmed=True,
        )
        assert activation.version == "1"
        assert activation.user_confirmed
        assert activation.draft_content_hash == draft.content_hash
        assert scope.is_full_history
        assert scope.applies_to_domain("AE")

    def test_disappeared_with_confirmed_coverage_becomes_removed(self):
        """Full integration of coverage note → removed → confirmed_removal impact."""
        base, _ = build_snapshot_facts(
            "proj-synth", "rev-base", self.alg, self.baseline_rows
        )
        curr, _ = build_snapshot_facts(
            "proj-synth", "rev-curr", self.alg, self.current_rows
        )
        # Find S002's record id
        target = [d for d, p in base.records if p.get("SUBJECT") == "S002"][0]
        note = ScopeCoverageNote(
            record_id=f"rec-{target}",
            covered=True,
            basis="export confirmed full AE domain coverage",
            confirmed_by="snapshot_coverage_check",
        )
        diff = diff_snapshots(base, curr, coverage_notes=[note])
        assert diff.n_removed == 1
        assert diff.n_disappeared == 0

        impact = propagate_impact(diff)
        assert impact.n_confirmed_removal == 1
        cr = [i for i in impact.items if i.impact_kind == ImpactKind.CONFIRMED_REMOVAL][0]
        assert not cr.requires_review

    def test_content_hash_chain_reproducible(self):
        """The entire pipeline produces identical hashes on re-run."""
        base, _ = build_snapshot_facts(
            "proj-synth", "rev-base", self.alg, self.baseline_rows
        )
        curr, _ = build_snapshot_facts(
            "proj-synth", "rev-curr", self.alg, self.current_rows
        )
        d1 = diff_snapshots(base, curr)
        i1 = propagate_impact(d1)

        d2 = diff_snapshots(base, curr)
        i2 = propagate_impact(d2)

        assert d1.content_hash == d2.content_hash
        assert i1.content_hash == i2.content_hash
        assert i1.diff_content_hash == d1.content_hash


# ===========================================================================
# Three heterogeneous shapes integration
# ===========================================================================

class TestThreeHeterogeneousShapesIntegration:
    """Prove R3-C works on all three R3-A heterogeneous listing shapes."""

    def test_wide_ae_shape_diff(self):
        """Wide AE listing: SUBJECT + AE_TERM key."""
        alg = IdentityAlgorithm("wide_ae", ["SUBJECT", "AE_TERM"], key_normalize="display")
        base_rows = [
            {"SUBJECT": "S001", "AE_TERM": "Nausea", "SEVERITY": "Mild"},
            {"SUBJECT": "S002", "AE_TERM": "Headache", "SEVERITY": "Moderate"},
        ]
        curr_rows = [
            {"SUBJECT": "S001", "AE_TERM": "Nausea", "SEVERITY": "Severe"},
            {"SUBJECT": "S003", "AE_TERM": "Rash", "SEVERITY": "Mild"},
        ]
        base, _ = build_snapshot_facts("p", "r1", alg, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", alg, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1  # S001 severity changed
        assert diff.n_disappeared == 1  # S002 gone
        assert diff.n_added == 1  # S003 new

    def test_long_labs_shape_diff(self):
        """Long labs: SUBJECT + PARAM key."""
        alg = IdentityAlgorithm("long_labs", ["SUBJECT", "PARAM"], key_normalize="display")
        base_rows = [
            {"SUBJECT": "S001", "PARAM": "ALT", "VAL": 45},
            {"SUBJECT": "S001", "PARAM": "AST", "VAL": 30},
        ]
        curr_rows = [
            {"SUBJECT": "S001", "PARAM": "ALT", "VAL": 55},  # modified
            {"SUBJECT": "S001", "PARAM": "AST", "VAL": 30},  # unchanged
        ]
        base, _ = build_snapshot_facts("p", "r1", alg, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", alg, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1
        assert diff.n_unchanged == 1

    def test_multi_table_workbook_shape_diff(self):
        """Multi-table workbook: use a composite key spanning domains."""
        alg = IdentityAlgorithm(
            "wb_key", ["SUBJECT", "DOMAIN_TAG"], key_normalize="display"
        )
        base_rows = [
            {"SUBJECT": "S001", "DOMAIN_TAG": "DM", "SEX": "F", "AGE": 42},
            {"SUBJECT": "S001", "DOMAIN_TAG": "AE", "AE_TERM": "Fatigue"},
        ]
        curr_rows = [
            {"SUBJECT": "S001", "DOMAIN_TAG": "DM", "SEX": "F", "AGE": 43},  # age changed
            {"SUBJECT": "S001", "DOMAIN_TAG": "AE", "AE_TERM": "Fatigue"},  # unchanged
        ]
        base, _ = build_snapshot_facts("p", "r1", alg, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", alg, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1
        assert diff.n_unchanged == 1
