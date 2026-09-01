"""Batch B diff tests: real AcceptanceService/BaselineService binding, derived
mappings, key rejection, partial dates, full semantic hashing, config separation,
taxonomy, provenance, and VETO 1+2 regressions."""

from __future__ import annotations
import pytest

from mm_r2.domain import ListingSnapshot
from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY, AcceptanceChainError, AcceptanceService,
    SnapshotAcceptanceState,
)
from mm_r2.baselines import BaselineService
from mm_r2.diff import (
    ConfigChange, ConfigChangeKind, ConfigChangeSet,
    DiffEntry, DiffEntryKind, DiffError, DiffService, FieldChange, SnapshotDiff,
)
from helpers_b import make_accepted_snapshot


def _setup_two(svc_acc, bsvc, rows_a, rows_b):
    snap_a = make_accepted_snapshot(svc_acc, sid="s1", rows=rows_a)
    snap_b = make_accepted_snapshot(svc_acc, rid="rev-2", sid="s2", rows=rows_b)
    bl = bsvc.set_data_baseline(svc_acc, snap_a)
    return snap_a, snap_b, bl


# VETO 2-9,10: Diff authority
class TestDiffAuthority:
    def test_incremental_with_real_baseline(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "S01", "ae": "V"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        assert d.n_changed == 1

    def test_unregistered_snapshot_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows_a)
        bl = bsvc.set_data_baseline(svc, snap_a)
        snap_fake = ListingSnapshot.from_content("fake", "p1", "rev-2", "c2",
                                                   [{"subject": "S01"}])
        ds = DiffService()
        with pytest.raises(DiffError, match="not registered"):
            ds.diff_incremental("p1", bl, snap_fake, rows_a, [{"subject": "S01"}], svc, bsvc)

    def test_no_acceptance_service_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows_a)
        bl = bsvc.set_data_baseline(svc, snap_a)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=[{"subject": "S01"}])
        ds = DiffService()
        with pytest.raises(DiffError, match="AcceptanceService"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, [{"subject": "S01"}], None, bsvc)

    def test_duck_typed_service_rejected(self):
        """VETO 2-10: duck-typed fake AcceptanceService rejected."""
        ds = DiffService()
        class FakeSvc:
            def get(self, sid): pass
            def binding(self, sid): pass
        with pytest.raises(DiffError, match="real AcceptanceService"):
            ds.diff_full("p1", None, None, [], [], FakeSvc())

    def test_hostile_acceptance_subclass_rejected(self):
        class HostileAcceptance(AcceptanceService):
            def get(self, snapshot_id):
                raise AssertionError("hostile override must not run")

        with pytest.raises(DiffError, match="real AcceptanceService"):
            DiffService().diff_full(
                "p1", None, None, [], [],
                HostileAcceptance(local_user="test"),
            )

    def test_incremental_requires_real_baseline_service(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows_a)
        bl = bsvc.set_data_baseline(svc, snap_a)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=[{"subject": "S01"}])
        ds = DiffService()
        with pytest.raises(DiffError, match="real BaselineService"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, [{"subject": "S01"}], svc, None)

    def test_incremental_rejects_hostile_baseline_subclass(self):
        class HostileBaseline(BaselineService):
            def get_baseline(self, baseline_id):
                raise AssertionError("hostile override must not run")

        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows)
        baseline = bsvc.set_data_baseline(svc, snap_a)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=rows)
        with pytest.raises(DiffError, match="real BaselineService"):
            DiffService().diff_incremental(
                "p1", baseline, snap_b, rows, rows, svc,
                HostileBaseline(),
            )

    def test_incremental_rejects_blocked_live_baseline(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows)
        baseline = bsvc.set_data_baseline(svc, snap_a)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=rows)
        with pytest.raises(AcceptanceChainError):
            svc.advance(
                "s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                ACCEPTED_BY_SYSTEM_POLICY,
            )
        with pytest.raises(DiffError, match="blocked"):
            DiffService().diff_incremental(
                "p1", baseline, snap_b, rows, rows, svc, bsvc,
            )

    def test_incremental_rejects_unregistered_baseline(self):
        """VETO 2: DataBaseline not registered in the supplied BaselineService."""
        svc1 = AcceptanceService(local_user="test")
        svc2 = AcceptanceService(local_user="test")
        bsvc1 = BaselineService()
        bsvc2 = BaselineService()
        rows_a = [{"subject": "S01"}]
        snap_a = make_accepted_snapshot(svc1, sid="s1", rows=rows_a)
        bl = bsvc1.set_data_baseline(svc1, snap_a)
        # bl is registered in bsvc1, not bsvc2.
        snap_b = make_accepted_snapshot(svc2, rid="rev-2", sid="s2", rows=[{"subject": "S01"}])
        ds = DiffService()
        with pytest.raises(DiffError, match="not registered"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, [{"subject": "S01"}], svc2, bsvc2)

    def test_same_id_different_content_rejected(self):
        """VETO 2-9: same snapshot ID with different content fails."""
        svc = AcceptanceService(local_user="test")
        rows_a = [{"subject": "S01", "ae": "N"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows_a)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2",
                                        rows=[{"subject": "S01", "ae": "V"}])
        ds = DiffService()
        # Create a fake snap with same ID as snap_a but different content.
        snap_fake = ListingSnapshot.from_content("s1", "p1", "rev-1", "cutoff-s1",
                                                  [{"subject": "S01", "ae": "DIFFERENT"}])
        with pytest.raises(DiffError, match="content_hash"):
            ds.diff_full("p1", snap_fake, snap_b, rows_a, [{"subject": "S01", "ae": "V"}], svc)


# VETO 1-5/VETO 2-5: diff_hash collision
class TestDiffHashFullSemantics:
    def test_field_change_order_is_canonical(self):
        first = FieldChange(
            canonical_field="ae_term", old_value="A", new_value="B",
            mapping_id="m1",
        )
        second = FieldChange(
            canonical_field="severity", old_value="mild", new_value="severe",
            mapping_id="m2",
        )
        left = DiffEntry(
            entry_id="de-1", kind=DiffEntryKind.CHANGE,
            record_key="subject=S01", field_changes=(first, second),
            impact_domains=("mh", "ae"),
        )
        right = DiffEntry(
            entry_id="de-1", kind=DiffEntryKind.CHANGE,
            record_key="subject=S01", field_changes=(second, first),
            impact_domains=("ae", "mh"),
        )
        assert left.field_changes == right.field_changes
        assert left.impact_domains == right.impact_domains
        assert left.entry_hash == right.entry_hash

    def test_different_values_different_hash(self):
        svc1 = AcceptanceService(local_user="test")
        bsvc1 = BaselineService()
        svc2 = AcceptanceService(local_user="test")
        bsvc2 = BaselineService()
        rows_a = [{"subject": "S01", "val": "1"}]
        rows_b1 = [{"subject": "S01", "val": "2"}]
        rows_b2 = [{"subject": "S01", "val": "3"}]
        _, snap_b1, bl1 = _setup_two(svc1, bsvc1, rows_a, rows_b1)
        _, snap_b2, bl2 = _setup_two(svc2, bsvc2, rows_a, rows_b2)
        ds = DiffService()
        d1 = ds.diff_incremental("p1", bl1, snap_b1, rows_a, rows_b1, svc1, bsvc1,
                                  record_key_fields=("subject",))
        d2 = ds.diff_incremental("p1", bl2, snap_b2, rows_a, rows_b2, svc2, bsvc2,
                                  record_key_fields=("subject",))
        assert d1.diff_hash != d2.diff_hash
        assert d1.diff_id != d2.diff_id

    def test_config_change_affects_hash(self):
        svc = AcceptanceService(local_user="test")
        rows = [{"subject": "S01", "ae": "N"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=rows)
        ds = DiffService()
        ccs1 = ConfigChangeSet(changes=(ConfigChange(kind=ConfigChangeKind.RULE, ref_id="r1", detail="v1->v2"),))
        ccs2 = ConfigChangeSet(changes=(ConfigChange(kind=ConfigChangeKind.RULE, ref_id="r1", detail="v1->v3"),))
        d1 = ds.diff_full("p1", snap_a, snap_b, rows, rows, svc, config_changes=ccs1)
        d2 = ds.diff_full("p1", snap_a, snap_b, rows, rows, svc, config_changes=ccs2)
        assert d1.diff_hash != d2.diff_hash

    def test_config_change_order_is_canonical(self):
        a = ConfigChange(
            kind=ConfigChangeKind.RULE, ref_id="r1", detail="v1->v2"
        )
        b = ConfigChange(
            kind=ConfigChangeKind.MAPPING, ref_id="m1", detail="v1->v2"
        )
        left = ConfigChangeSet(changes=(a, b))
        right = ConfigChangeSet(changes=(b, a))
        assert left.changes == right.changes
        assert left.canonical_payload() == right.canonical_payload()


class TestChangeTaxonomy:
    def _diff(self, rows_a, rows_b):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        return ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                   record_key_fields=("subject",))

    def test_add(self):
        d = self._diff([{"subject": "S01", "ae": "N"}],
                       [{"subject": "S01", "ae": "N"}, {"subject": "S02", "ae": "H"}])
        assert d.n_added == 1

    def test_change(self):
        d = self._diff([{"subject": "S01", "ae": "N", "sev": "Mild"}],
                       [{"subject": "S01", "ae": "N", "sev": "Severe"}])
        assert d.n_changed == 1

    def test_disappear(self):
        d = self._diff([{"subject": "S01", "ae": "N"}, {"subject": "S02", "ae": "H"}],
                       [{"subject": "S01", "ae": "N"}])
        assert d.n_disappeared == 1
        assert d.has_disappearances_needing_scope_check

    def test_scope_change(self):
        d = self._diff([{"subject": "S01", "ae": "N"}],
                       [{"subject": "S01", "ae": "N", "new_col": "X"}])
        assert d.n_scope_changed >= 1

    def test_no_changes(self):
        rows = [{"subject": "S01", "ae": "N"}]
        d = self._diff(rows, rows)
        assert not d.has_data_changes

    def test_full_and_incremental_same_taxonomy(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "S02", "ae": "V"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d_full = ds.diff_full("p1", snap_a, snap_b, rows_a, rows_b, svc,
                               record_key_fields=("subject",))
        d_inc = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                    record_key_fields=("subject",))
        assert d_full.n_added == d_inc.n_added
        assert d_full.n_disappeared == d_inc.n_disappeared


class TestMissingKeyComponents:
    def test_missing_key_field_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"ae": "N"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        with pytest.raises(DiffError, match="missing"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))

    def test_unknown_key_value_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "UNK", "ae": "N"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        with pytest.raises(DiffError, match="unknown"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))

    def test_case_insensitive_unknown_key_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "unk", "ae": "N"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        with pytest.raises(DiffError, match="unknown"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))

    def test_empty_key_fields_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, [{"subject": "S01", "ae": "V"}])
        ds = DiffService()
        with pytest.raises(DiffError, match="non-empty"):
            ds.diff_incremental("p1", bl, snap_b, rows_a, [{"subject": "S01", "ae": "V"}],
                                svc, bsvc, record_key_fields=())

    def test_duplicate_key_rejected(self):
        """The diff rejects duplicate record keys within a single snapshot."""
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "S02", "ae": "N"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        # Pass rows_b with duplicate key to the diff (different from snap_b's
        # actual rows).  This will be caught by the duplicate-key check before
        # the content digest check (the digest check is on the declared rows,
        # but the duplicate key check runs on the same declared rows).
        # Since we can't mismatch rows vs digest, we test the duplicate key
        # by using rows that themselves contain duplicate keys.  But the
        # binding won't accept those.  Instead, test the _index_rows directly.
        with pytest.raises(DiffError, match="duplicate"):
            ds._index_rows(
                [{"subject": "S01"}, {"subject": "S01"}],
                ("subject",),
            )


class TestPartialDateExpansion:
    def _diff(self, rows_a, rows_b):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        return ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                   record_key_fields=("subject",))

    def test_yyyy_partial_date(self):
        d = self._diff([{"subject": "S01", "date": "2025"}],
                       [{"subject": "S01", "date": "2026-01-15"}])
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].is_partial_date

    def test_yyyy_mm_partial_date(self):
        d = self._diff([{"subject": "S01", "date": "2026-01"}],
                       [{"subject": "S01", "date": "2026-01-15"}])
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].is_partial_date

    def test_unk_component_partial_date(self):
        d = self._diff([{"subject": "S01", "date": "2026-UNK-01"}],
                       [{"subject": "S01", "date": "2026-01-15"}])
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].is_partial_date

    def test_case_insensitive_unk_partial_date(self):
        d = self._diff([{"subject": "S01", "date": "2026-unk-01"}],
                       [{"subject": "S01", "date": "2026-01-15"}])
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].is_partial_date

    def test_unknown_field_detected(self):
        d = self._diff([{"subject": "S01", "ae": "UNK"}],
                       [{"subject": "S01", "ae": "Nausea"}])
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].is_unknown_field

    def test_unknown_to_unknown_no_change(self):
        d = self._diff([{"subject": "S01", "ae": "UNK"}],
                       [{"subject": "S01", "ae": "UNK"}])
        assert not d.has_data_changes


class TestMappingProvenanceAndConfigSeparation:
    def test_mapping_provenance_derived_from_binding(self):
        """VETO 2: mapping IDs derived from the accepted binding, not caller."""
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        # Binding has source_field=AETERM, canonical_field=ae_term, mapping_id=m1.
        rows_a = [{"subject": "S01", "AETERM": "N"}]
        rows_b = [{"subject": "S01", "AETERM": "V"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        assert chg[0].field_changes[0].mapping_id == "m1"
        assert chg[0].field_changes[0].canonical_field == "ae_term"

    def test_unmapped_field_gets_marker(self):
        """Unmapped changed field gets UNMAPPED marker and is_unknown_field=True."""
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        # The binding maps AETERM->ae_term. 'subject' is a key field, not mapped.
        # 'random_field' is not mapped.
        rows_a = [{"subject": "S01", "AETERM": "N", "random_field": "A"}]
        rows_b = [{"subject": "S01", "AETERM": "N", "random_field": "B"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        chg = [e for e in d.data_changes if e.kind == DiffEntryKind.CHANGE]
        # Find the random_field change.
        fc = [f for f in chg[0].field_changes if "random_field" in f.canonical_field]
        assert len(fc) == 1
        assert fc[0].mapping_id == "UNMAPPED"
        assert fc[0].is_unknown_field

    def test_config_not_mislabeled_as_data(self):
        svc = AcceptanceService(local_user="test")
        rows = [{"subject": "S01", "ae": "N"}]
        snap_a = make_accepted_snapshot(svc, sid="s1", rows=rows)
        snap_b = make_accepted_snapshot(svc, rid="rev-2", sid="s2", rows=rows)
        ccs = ConfigChangeSet(changes=(ConfigChange(kind=ConfigChangeKind.RULE, ref_id="r1", detail="updated"),))
        ds = DiffService()
        d = ds.diff_full("p1", snap_a, snap_b, rows, rows, svc, config_changes=ccs)
        assert d.has_config_changes
        assert not d.has_data_changes
        assert d.config_changes.kinds() == ("rule_change",)

    def test_all_config_kinds(self):
        for kind in ConfigChangeKind.all_kinds():
            ConfigChange(kind=kind, ref_id="x", detail="d")


class TestDiffDeterminism:
    def test_diff_hash_valid(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "S01", "ae": "V"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        assert d.diff_hash == d.compute_hash()
        assert len(d.diff_hash) == 64

    def test_entry_hash_valid(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N"}]
        rows_b = [{"subject": "S01", "ae": "V"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        for e in d.data_changes:
            assert e.entry_hash == e.compute_hash()
            assert len(e.entry_hash) == 64

    def test_impact_inputs_emitted(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        rows_a = [{"subject": "S01", "ae": "N", "sev": "Mild"}]
        rows_b = [{"subject": "S01", "ae": "N", "sev": "Severe"}]
        snap_a, snap_b, bl = _setup_two(svc, bsvc, rows_a, rows_b)
        ds = DiffService()
        d = ds.diff_incremental("p1", bl, snap_b, rows_a, rows_b, svc, bsvc,
                                record_key_fields=("subject",))
        assert len(d.impact_inputs) > 0
        for inp in d.impact_inputs:
            assert len(inp) == 3
