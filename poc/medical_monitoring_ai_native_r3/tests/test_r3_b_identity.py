"""R3-B record identity tests.

Proves the identity is stable under row/column ordering and display-only
changes, but does not collapse genuinely distinct records or ambiguous
partial identities (Design: 不误合并).
"""

from __future__ import annotations

import pytest

from mm_r3.identity import (
    AmbiguousIdentity,
    IdentityAlgorithm,
    IdentityAmbiguityKind,
    IdentityError,
    IdentityResolution,
    RecordIdentity,
    make_record_identity,
    resolve_rows,
)


# ===========================================================================
# IdentityAlgorithm
# ===========================================================================

class TestIdentityAlgorithm:
    def test_basic_construction(self):
        algo = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        assert algo.name == "subj_ae"
        assert algo.key_fields == ("SUBJECT", "AE_TERM")
        assert algo.key_normalize == "display"
        assert len(algo.digest) == 64

    def test_digest_stable(self):
        a1 = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        a2 = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        assert a1.digest == a2.digest
        assert a1 == a2
        assert hash(a1) == hash(a2)

    def test_different_fields_different_digest(self):
        a1 = IdentityAlgorithm("x", ["SUBJECT", "AE_TERM"])
        a2 = IdentityAlgorithm("x", ["SUBJECT", "MH_TERM"])
        assert a1.digest != a2.digest

    def test_dedup_key_fields_preserving_order(self):
        algo = IdentityAlgorithm("x", ["SUBJECT", "AE_TERM", "SUBJECT"])
        assert algo.key_fields == ("SUBJECT", "AE_TERM")

    def test_empty_key_fields_rejected(self):
        with pytest.raises(IdentityError):
            IdentityAlgorithm("x", [])

    def test_normalize_mode_validated(self):
        with pytest.raises(IdentityError):
            IdentityAlgorithm("x", ["SUBJECT"], key_normalize="bogus")

    def test_frozen(self):
        algo = IdentityAlgorithm("x", ["SUBJECT"])
        with pytest.raises(IdentityError):
            algo.name = "y"  # type: ignore[misc]

    def test_canonicalize_display_mode(self):
        algo = IdentityAlgorithm("x", ["SUBJECT"], key_normalize="display")
        assert algo.canonicalize_key_value(" S001 ") == "s001"
        assert algo.canonicalize_key_value("S001") == "s001"
        assert algo.canonicalize_key_value("UNK") is None  # missing
        assert algo.canonicalize_key_value(None) is None

    def test_canonicalize_strict_mode(self):
        algo = IdentityAlgorithm("x", ["SUBJECT"], key_normalize="strict")
        assert algo.canonicalize_key_value("S001") == "S001"
        assert algo.canonicalize_key_value("s001") == "s001"  # not folded

    def test_canonicalize_keep_case_mode(self):
        algo = IdentityAlgorithm("x", ["SUBJECT"], key_normalize="display_keep_case")
        assert algo.canonicalize_key_value(" S001 ") == "S001"


# ===========================================================================
# RecordIdentity
# ===========================================================================

class TestRecordIdentity:
    def test_id_derived_from_digest(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        ri = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S001"})
        assert ri.record_id == f"rec-{ri.digest}"
        assert len(ri.digest) == 64

    def test_id_stable_under_display_change(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        r1 = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S001"})
        r2 = make_record_identity("proj", "rev1", algo, {"SUBJECT": " s001 "})
        assert r1.digest == r2.digest
        assert r1.record_id == r2.record_id

    def test_id_differs_for_distinct_keys(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        r1 = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S001"})
        r2 = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S002"})
        assert r1.digest != r2.digest

    def test_id_stable_across_full_listing_revisions(self):
        """Snapshot lineage must not redefine the underlying clinical record."""
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        r1 = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S001"})
        r2 = make_record_identity("proj", "rev2", algo, {"SUBJECT": "S001"})
        assert r1.source_revision_id != r2.source_revision_id
        assert r1.digest == r2.digest
        assert r1.record_id == r2.record_id

    def test_id_remains_project_scoped(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        r1 = make_record_identity("proj-1", "rev1", algo, {"SUBJECT": "S001"})
        r2 = make_record_identity("proj-2", "rev1", algo, {"SUBJECT": "S001"})
        assert r1.record_id != r2.record_id

    def test_fabricated_id_rejected(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        with pytest.raises(IdentityError):
            RecordIdentity(
                record_id="rec-fake",
                project_id="proj",
                source_revision_id="rev1",
                algorithm_digest=algo.digest,
                key_fields=(("SUBJECT", "s001"),),
            )

    def test_declared_digest_mismatch_rejected(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        with pytest.raises(IdentityError):
            RecordIdentity(
                project_id="proj",
                source_revision_id="rev1",
                algorithm_digest=algo.digest,
                key_fields=(("SUBJECT", "s001"),),
                digest="0" * 64,
            )

    def test_immutable(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        ri = make_record_identity("proj", "rev1", algo, {"SUBJECT": "S001"})
        with pytest.raises(Exception):
            ri.record_id = "x"  # type: ignore[misc]


# ===========================================================================
# resolve_rows: stability under row / column / display changes
# ===========================================================================

class TestResolveRowsStability:
    def setup_method(self):
        self.algo = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        self.rows = [
            {"SUBJECT": "S001", "AE_TERM": "Nausea", "_row_index": 0},
            {"SUBJECT": "S002", "AE_TERM": "Headache", "_row_index": 1},
            {"SUBJECT": "S003", "AE_TERM": "Fatigue", "_row_index": 2},
        ]

    def test_row_order_independent(self):
        r1 = resolve_rows("p", "rev1", self.algo, self.rows)
        r2 = resolve_rows("p", "rev1", self.algo, list(reversed(self.rows)))
        ids1 = sorted(r.record_id for r in r1.resolved)
        ids2 = sorted(r.record_id for r in r2.resolved)
        assert ids1 == ids2

    def test_column_order_independent(self):
        # rows are mappings; adding/reordering extra columns does not change id
        rows_extra_col = [
            {**r, "SEVERITY": "Mild", "SERIOUS": "No"} for r in self.rows
        ]
        r1 = resolve_rows("p", "rev1", self.algo, self.rows)
        r2 = resolve_rows("p", "rev1", self.algo, rows_extra_col)
        assert sorted(r.record_id for r in r1.resolved) == sorted(r.record_id for r in r2.resolved)

    def test_display_only_change_stable(self):
        rows_display = [
            {"SUBJECT": " S001 ", "AE_TERM": " nausea ", "_row_index": 0},
            {"SUBJECT": "S002", "AE_TERM": "Headache", "_row_index": 1},
            {"SUBJECT": "S003", "AE_TERM": "Fatigue", "_row_index": 2},
        ]
        r1 = resolve_rows("p", "rev1", self.algo, self.rows)
        r2 = resolve_rows("p", "rev1", self.algo, rows_display)
        # S001+Nausea should match despite case/whitespace
        assert sorted(r.record_id for r in r1.resolved) == sorted(r.record_id for r in r2.resolved)

    def test_genuinely_distinct_not_collapsed(self):
        rows_distinct = list(self.rows) + [
            {"SUBJECT": "S001", "AE_TERM": "Rash", "_row_index": 3}  # new AE for S001
        ]
        r1 = resolve_rows("p", "rev1", self.algo, self.rows)
        r2 = resolve_rows("p", "rev1", self.algo, rows_distinct)
        assert len(r2.resolved) == len(r1.resolved) + 1

    def test_empty_rows_clean(self):
        res = resolve_rows("p", "rev1", self.algo, [])
        assert res.is_clean is True
        assert len(res.resolved) == 0


# ===========================================================================
# Ambiguity surfacing
# ===========================================================================

class TestAmbiguity:
    def test_all_keys_missing_is_none_ambiguity(self):
        algo = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        rows = [
            {"SUBJECT": "", "AE_TERM": "", "_row_index": 0},
        ]
        res = resolve_rows("p", "rev1", algo, rows)
        assert res.is_clean is False
        assert len(res.ambiguities) == 1
        assert res.ambiguities[0].kind == IdentityAmbiguityKind.NONE

    def test_partial_keys_blocked_by_default(self):
        algo = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        rows = [
            {"SUBJECT": "S001", "AE_TERM": "", "_row_index": 0},
        ]
        res = resolve_rows("p", "rev1", algo, rows)
        assert res.is_clean is False
        assert res.ambiguities[0].kind == IdentityAmbiguityKind.NONE
        assert "partial" in res.ambiguities[0].reason

    def test_partial_keys_allowed_when_opted_in(self):
        algo = IdentityAlgorithm("subj_ae", ["SUBJECT", "AE_TERM"])
        rows = [
            {"SUBJECT": "S001", "AE_TERM": "", "_row_index": 0},
        ]
        res = resolve_rows("p", "rev1", algo, rows, partial_keys_allowed=True)
        assert res.is_clean is True
        assert len(res.resolved) == 1

    def test_resolution_project_consistency(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        ri = make_record_identity("p1", "rev1", algo, {"SUBJECT": "S001"})
        with pytest.raises(IdentityError):
            IdentityResolution(
                algorithm=algo, project_id="p2", source_revision_id="rev1",
                resolved=(ri,),
            )

    def test_resolution_source_revision_consistency(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        ri = make_record_identity("p1", "rev1", algo, {"SUBJECT": "S001"})
        with pytest.raises(IdentityError, match="source_revision_id"):
            IdentityResolution(
                algorithm=algo, project_id="p1", source_revision_id="rev2",
                resolved=(ri,),
            )


# ===========================================================================
# Duplicate detection (surfaces, does not merge)
# ===========================================================================

class TestDuplicateDetection:
    def test_duplicates_surfaced(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        rows = [
            {"SUBJECT": "S001", "_row_index": 0},
            {"SUBJECT": "S001", "_row_index": 1},  # duplicate key
        ]
        res = resolve_rows("p", "rev1", algo, rows)
        assert res.has_duplicates is True
        groups = res.duplicate_groups()
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_distinct_no_duplicates(self):
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        rows = [
            {"SUBJECT": "S001", "_row_index": 0},
            {"SUBJECT": "S002", "_row_index": 1},
        ]
        res = resolve_rows("p", "rev1", algo, rows)
        assert res.has_duplicates is False
        assert res.duplicate_groups() == ()

    def test_duplicates_not_collapsed(self):
        # two rows with the same key produce two identities (not merged)
        algo = IdentityAlgorithm("subj", ["SUBJECT"])
        rows = [
            {"SUBJECT": "S001", "_row_index": 0},
            {"SUBJECT": "S001", "_row_index": 1},
        ]
        res = resolve_rows("p", "rev1", algo, rows)
        assert len(res.resolved) == 2
        assert all(r.digest == res.resolved[0].digest for r in res.resolved)


# ===========================================================================
# AmbiguousIdentity invariants
# ===========================================================================

class TestAmbiguousIdentityInvariants:
    def test_multi_requires_two_candidates(self):
        with pytest.raises(IdentityError):
            AmbiguousIdentity(
                kind=IdentityAmbiguityKind.MULTI,
                project_id="p",
                algorithm_digest="a" * 64,
                candidate_digests=["b" * 64],  # only one
                reason="x",
            )

    def test_none_kind_ok_with_zero_candidates(self):
        a = AmbiguousIdentity(
            kind=IdentityAmbiguityKind.NONE,
            project_id="p",
            reason="unresolvable",
        )
        assert a.candidate_digests == ()

    def test_invalid_kind_rejected(self):
        with pytest.raises(IdentityError):
            AmbiguousIdentity(kind="bogus", project_id="p", reason="x")

    def test_candidate_digests_sorted_and_unique(self):
        b = "b" * 64
        c = "c" * 64
        a = AmbiguousIdentity(
            kind=IdentityAmbiguityKind.MULTI,
            project_id="p",
            algorithm_digest="a" * 64,
            candidate_digests=[c, b, c],  # dup + unsorted
            reason="multi",
        )
        assert a.candidate_digests == (b, c)
