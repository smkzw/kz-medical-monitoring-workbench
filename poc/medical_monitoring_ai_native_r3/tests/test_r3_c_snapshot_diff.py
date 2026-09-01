"""R3-C snapshot diff and clinical impact propagation tests.

Proves:
* Full-snapshot input contract (no incremental patches).
* Deterministic diff: same snapshots -> same diff; row/column order
  independence.
* Change kinds: added / removed / disappeared / unchanged / modified.
* Disappeared records are never silently resolved (Design §6.2).
* Impact propagation classifies changes with explicit uncertainty.
* Content-addressed invariants and derived tally integrity.
* Algorithm/project mismatch rejected.
"""

from __future__ import annotations

import pytest

from mm_r3.identity import IdentityAlgorithm
from mm_r3.snapshot_diff import (
    CHANGE_KINDS,
    ChangeKind,
    ChangeRecord,
    IMPACT_KINDS,
    ImpactItem,
    ImpactKind,
    ImpactPropagation,
    ScopeCoverageNote,
    SnapshotDiff,
    SnapshotDiffError,
    SnapshotFacts,
    build_snapshot_facts,
    diff_snapshots,
    propagate_impact,
)


# ===========================================================================
# Helpers
# ===========================================================================

ALG = IdentityAlgorithm("subject_ae", ["SUBJECT", "AE_TERM"], key_normalize="display")
ALG_ALT = IdentityAlgorithm("subject_ae_alt", ["SUBJECT", "AE_TERM"], key_normalize="strict")


def _rows(*specs):
    """Build rows from (subject, ae_term, **extra) specs."""
    out = []
    for i, s in enumerate(specs):
        row = {"_row_index": i, "SUBJECT": s[0], "AE_TERM": s[1]}
        row.update(s[2] if len(s) > 2 else {})
        out.append(row)
    return out


# ===========================================================================
# SnapshotFacts
# ===========================================================================

class TestSnapshotFacts:
    def test_build_from_rows(self):
        rows = _rows(
            ("S001", "Nausea"),
            ("S002", "Headache"),
        )
        facts, resolution = build_snapshot_facts(
            "proj-alpha", "rev-1", ALG, rows,
            coverage_scope={"domain": "ae"},
        )
        assert facts.project_id == "proj-alpha"
        assert facts.source_revision_id == "rev-1"
        assert facts.algorithm_digest == ALG.digest
        assert facts.n_records == 2
        assert resolution.is_clean
        assert not facts.scope_unspecified
        assert facts.scope_get("domain") == "ae"

    def test_content_hash_deterministic(self):
        rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        f1, _ = build_snapshot_facts("p", "r", ALG, rows)
        f2, _ = build_snapshot_facts("p", "r", ALG, rows)
        assert f1.content_hash == f2.content_hash

    def test_row_order_independence(self):
        """Row order must not change the facts identity (digests are per-record)."""
        rows_a = _rows(("S001", "Nausea"), ("S002", "Headache"))
        rows_b = _rows(("S002", "Headache"), ("S001", "Nausea"))
        fa, _ = build_snapshot_facts("p", "r", ALG, rows_a)
        fb, _ = build_snapshot_facts("p", "r", ALG, rows_b)
        # same set of digests -> same content hash
        assert fa.content_hash == fb.content_hash

    def test_display_only_stability(self):
        """Whitespace/case differences in keys should not change the digest set."""
        rows_a = _rows(("S001", "Nausea"))
        rows_b = _rows((" s001 ", "nausea"))
        fa, _ = build_snapshot_facts("p", "r", ALG, rows_a)
        fb, _ = build_snapshot_facts("p", "r", ALG, rows_b)
        digests_a = {k for k, _ in fa.records}
        digests_b = {k for k, _ in fb.records}
        assert digests_a == digests_b

    def test_different_content_different_hash(self):
        rows_a = _rows(("S001", "Nausea"))
        rows_b = _rows(("S001", "Vomiting"))
        fa, _ = build_snapshot_facts("p", "r", ALG, rows_a)
        fb, _ = build_snapshot_facts("p", "r", ALG, rows_b)
        assert fa.content_hash != fb.content_hash

    def test_scope_unspecified_default(self):
        rows = _rows(("S001", "Nausea"))
        f, _ = build_snapshot_facts("p", "r", ALG, rows)
        assert f.scope_unspecified

    def test_declared_hash_mismatch_rejected(self):
        rows = _rows(("S001", "Nausea"))
        with pytest.raises(SnapshotDiffError, match="content_hash mismatch"):
            SnapshotFacts(
                facts_id="x",
                project_id="p",
                source_revision_id="r",
                algorithm_digest=ALG.digest,
                records=(),
                content_hash="0" * 64,
            )

    def test_duplicate_identity_keys_block_snapshot(self):
        rows = _rows(("S001", "Nausea"), ("S001", "Nausea"))
        with pytest.raises(SnapshotDiffError, match="duplicate identity keys"):
            build_snapshot_facts("p", "r", ALG, rows)

    def test_external_source_row_numbers_do_not_select_wrong_payload(self):
        rows = [
            {"_row_index": 101, "SUBJECT": "S001", "AE_TERM": "Nausea"},
            {"_row_index": 205, "SUBJECT": "S002", "AE_TERM": "Headache"},
        ]
        facts, _ = build_snapshot_facts("p", "r", ALG, rows)
        payloads = [dict(payload) for _, payload in facts.records]
        assert {p["SUBJECT"] for p in payloads} == {"S001", "S002"}
        assert {p["AE_TERM"] for p in payloads} == {"Nausea", "Headache"}

    def test_pipeline_record_id_is_not_clinical_payload_or_false_diff(self):
        base, _ = build_snapshot_facts(
            "p", "r1", ALG,
            [{"_record_id": "transient-a", "SUBJECT": "S001", "AE_TERM": "Nausea"}],
        )
        current, _ = build_snapshot_facts(
            "p", "r2", ALG,
            [{"_record_id": "transient-b", "SUBJECT": "S001", "AE_TERM": "Nausea"}],
        )
        assert "_record_id" not in dict(base.records[0][1])
        diff = diff_snapshots(base, current)
        assert diff.n_unchanged == 1
        assert diff.n_modified == 0

    def test_bad_algorithm_digest_rejected(self):
        with pytest.raises(Exception):
            SnapshotFacts(
                facts_id="x",
                project_id="p",
                source_revision_id="r",
                algorithm_digest="not-a-hash",
                records=(),
            )


# ===========================================================================
# diff_snapshots -- change kinds
# ===========================================================================

class TestDiffChangeKinds:
    def test_identical_snapshots_all_unchanged(self):
        rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_unchanged == 2
        assert diff.n_added == 0
        assert diff.n_removed == 0
        assert diff.n_modified == 0
        assert diff.n_disappeared == 0
        assert not diff.has_changes

    def test_added_record(self):
        base_rows = _rows(("S001", "Nausea"))
        curr_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_added == 1
        added = diff.changes_of(ChangeKind.ADDED)
        assert len(added) == 1
        assert "S002" in dict(added[0].new_payload).get("SUBJECT", "")

    def test_modified_record_fields_changed(self):
        base_rows = _rows(("S001", "Nausea", {"SEVERITY": "Mild"}))
        curr_rows = _rows(("S001", "Nausea", {"SEVERITY": "Severe"}))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1
        mod = diff.changes_of(ChangeKind.MODIFIED)[0]
        assert "SEVERITY" in mod.fields_changed

    def test_modified_payload_whitespace_only_not_a_change(self):
        """Whitespace-only difference in a non-key field is not a modification."""
        base_rows = _rows(("S001", "Nausea", {"NOTES": "  some note  "}))
        curr_rows = _rows(("S001", "Nausea", {"NOTES": "some note"}))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_unchanged == 1
        assert diff.n_modified == 0

    def test_disappeared_without_coverage_note(self):
        """Baseline record absent from current, no coverage note -> disappeared."""
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_disappeared == 1
        assert diff.n_removed == 0
        assert diff.has_disappearances
        disp = diff.changes_of(ChangeKind.DISAPPEARED)[0]
        assert "coverage" in disp.uncertainty.lower() or "scope" in disp.uncertainty.lower()

    def test_removed_with_coverage_note(self):
        """Baseline record absent from current, confirmed coverage -> removed."""
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        # find the record_id of S002/Headache
        target_digest = None
        for d, payload in base.records:
            if payload.get("SUBJECT") == "S002":
                target_digest = d
                break
        assert target_digest is not None
        rid = f"rec-{target_digest}"
        note = ScopeCoverageNote(
            record_id=rid,
            covered=True,
            basis="current snapshot export confirmed in scope",
            confirmed_by="snapshot_coverage_check",
        )
        diff = diff_snapshots(base, curr, coverage_notes=[note])
        assert diff.n_removed == 1
        assert diff.n_disappeared == 0

    def test_coverage_note_not_covered_still_disappeared(self):
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        target_digest = [d for d, p in base.records if p.get("SUBJECT") == "S002"][0]
        note = ScopeCoverageNote(
            record_id=f"rec-{target_digest}",
            covered=False,
            basis="export scope changed; coverage unconfirmed",
        )
        diff = diff_snapshots(base, curr, coverage_notes=[note])
        assert diff.n_disappeared == 1
        assert diff.n_removed == 0

    def test_confirmed_coverage_requires_named_confirmation_source(self):
        with pytest.raises(ValueError, match="confirmed_by"):
            ScopeCoverageNote(
                record_id="rec-" + "a" * 64,
                covered=True,
                basis="export scope checked",
            )

    def test_duplicate_coverage_note_rejected(self):
        base, _ = build_snapshot_facts(
            "p", "r1", ALG, _rows(("S001", "Nausea"), ("S002", "Headache"))
        )
        curr, _ = build_snapshot_facts("p", "r2", ALG, _rows(("S001", "Nausea")))
        digest = [d for d, p in base.records if p.get("SUBJECT") == "S002"][0]
        note = ScopeCoverageNote(
            record_id=f"rec-{digest}", covered=False,
            basis="export coverage is still uncertain",
        )
        with pytest.raises(SnapshotDiffError, match="duplicate coverage note"):
            diff_snapshots(base, curr, coverage_notes=[note, note])

    def test_coverage_note_for_present_or_unknown_record_rejected(self):
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, rows)
        note = ScopeCoverageNote(
            record_id="rec-" + "a" * 64,
            covered=False,
            basis="not an absent baseline record",
        )
        with pytest.raises(SnapshotDiffError, match="only refer to baseline records absent"):
            diff_snapshots(base, curr, coverage_notes=[note])


# ===========================================================================
# diff_snapshots -- determinism and invariants
# ===========================================================================

class TestDiffDeterminism:
    def test_same_inputs_same_diff(self):
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"), ("S003", "Rash"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        d1 = diff_snapshots(base, curr)
        d2 = diff_snapshots(base, curr)
        assert d1.content_hash == d2.content_hash

    def test_changes_sorted_by_record_id(self):
        rows_base = _rows(("S003", "C"), ("S001", "A"), ("S002", "B"))
        rows_curr = _rows(("S001", "A"), ("S002", "B"), ("S003", "C"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows_base)
        curr, _ = build_snapshot_facts("p", "r2", ALG, rows_curr)
        diff = diff_snapshots(base, curr)
        ids = [c.record_id for c in diff.changes]
        assert ids == sorted(ids)

    def test_project_mismatch_rejected(self):
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p1", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p2", "r2", ALG, rows)
        with pytest.raises(SnapshotDiffError, match="project_id must match"):
            diff_snapshots(base, curr)

    def test_algorithm_mismatch_rejected(self):
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG_ALT, rows)
        with pytest.raises(SnapshotDiffError, match="algorithm_digest must match"):
            diff_snapshots(base, curr)

    def test_declared_hash_mismatch_rejected(self):
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, rows)
        with pytest.raises(SnapshotDiffError, match="content_hash mismatch"):
            SnapshotDiff(
                diff_id="x",
                project_id="p",
                baseline_source_revision_id="r1",
                current_source_revision_id="r2",
                algorithm_digest=ALG.digest,
                changes=(),
                content_hash="f" * 64,
            )

    def test_tallies_derived_not_declared(self):
        """Passing wrong tallies to the constructor must be corrected."""
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, _rows(("S001", "Nausea"), ("S002", "X")))
        diff = diff_snapshots(base, curr)
        # n_added is 1, not the fake 99 we would try to pass
        d2 = SnapshotDiff(
            diff_id="x",
            project_id="p",
            baseline_source_revision_id="r1",
            current_source_revision_id="r2",
            algorithm_digest=ALG.digest,
            changes=diff.changes,
            n_added=99,  # should be overridden
        )
        assert d2.n_added == 1


# ===========================================================================
# Impact propagation
# ===========================================================================

class TestImpactPropagation:
    def test_added_becomes_new_finding(self):
        base_rows = _rows(("S001", "Nausea"))
        curr_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.n_new_finding == 1
        nf = [i for i in impact.items if i.impact_kind == ImpactKind.NEW_FINDING]
        assert len(nf) == 1
        assert nf[0].requires_review

    def test_modified_becomes_data_correction(self):
        base_rows = _rows(("S001", "Nausea", {"SEVERITY": "Mild"}))
        curr_rows = _rows(("S001", "Nausea", {"SEVERITY": "Severe"}))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.n_data_correction == 1

    def test_disappeared_becomes_potential_loss(self):
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.n_potential_loss == 1
        pl = [i for i in impact.items if i.impact_kind == ImpactKind.POTENTIAL_LOSS]
        assert pl[0].requires_review
        assert "must not auto-resolve" in pl[0].uncertainty

    def test_removed_becomes_confirmed_removal(self):
        base_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        curr_rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        target_digest = [d for d, p in base.records if p.get("SUBJECT") == "S002"][0]
        note = ScopeCoverageNote(
            record_id=f"rec-{target_digest}",
            covered=True,
            basis="confirmed",
            confirmed_by="snapshot_coverage_check",
        )
        diff = diff_snapshots(base, curr, coverage_notes=[note])
        impact = propagate_impact(diff)
        assert impact.n_confirmed_removal == 1
        cr = [i for i in impact.items if i.impact_kind == ImpactKind.CONFIRMED_REMOVAL][0]
        assert not cr.requires_review

    def test_unchanged_becomes_none(self):
        rows = _rows(("S001", "Nausea"))
        base, _ = build_snapshot_facts("p", "r1", ALG, rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.n_none == 1
        assert impact.requires_review_count == 0

    def test_impact_content_hash_deterministic(self):
        base_rows = _rows(("S001", "Nausea"))
        curr_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        i1 = propagate_impact(diff)
        i2 = propagate_impact(diff)
        assert i1.content_hash == i2.content_hash

    def test_impact_binds_to_diff_hash(self):
        base_rows = _rows(("S001", "Nausea"))
        curr_rows = _rows(("S001", "Nausea"), ("S002", "Headache"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.diff_content_hash == diff.content_hash

    def test_subject_extraction(self):
        base_rows = _rows(("S001", "Nausea"))
        curr_rows = _rows(("S001", "Nausea"), ("S099", "Rash"))
        base, _ = build_snapshot_facts("p", "r1", ALG, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", ALG, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        nf = [i for i in impact.items if i.impact_kind == ImpactKind.NEW_FINDING][0]
        assert "S099" in nf.affected_subjects
