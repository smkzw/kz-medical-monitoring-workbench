"""Batch C: R1 read-only legacy adapter tests."""

import sqlite3

import pytest

from helpers_c import build_legacy_fixture

from mm_r2.legacy_adapter import (
    DiffStatus, DualReadDiff, LegacyAdapterError, LegacyProjection,
    R1LegacyAdapter, R2DualReadState,
)


@pytest.fixture
def legacy_db(tmp_path):
    return build_legacy_fixture(tmp_path / "legacy.db")


@pytest.fixture
def adapter(legacy_db):
    a = R1LegacyAdapter(legacy_db)
    yield a
    a.close()


class TestReadOnly:
    def test_opens_in_read_only_mode(self, legacy_db):
        adapter = R1LegacyAdapter(legacy_db)
        # Any write attempt through the underlying connection must fail
        with pytest.raises(sqlite3.OperationalError):
            adapter._conn.execute("INSERT INTO projects VALUES ('x','y',1,'{}','z')")
        adapter.close()

    def test_has_no_write_method(self):
        """The adapter class exposes no public write methods."""
        write_methods = [
            name for name in dir(R1LegacyAdapter)
            if not name.startswith("_")
            and callable(getattr(R1LegacyAdapter, name))
            and any(kw in name.lower() for kw in (
                "save", "write", "insert", "update", "delete", "create",
                "put", "set", "add", "record", "transition", "advance",
            ))
        ]
        assert write_methods == [], f"unexpected write-like methods: {write_methods}"

    def test_rejects_missing_fixture(self, tmp_path):
        with pytest.raises(LegacyAdapterError):
            R1LegacyAdapter(tmp_path / "nonexistent.db")

    def test_rejects_fixture_missing_monitoring_runs(self, tmp_path):
        db_path = tmp_path / "missing-runs.db"
        conn = sqlite3.connect(str(db_path))
        for table in (
            "projects", "source_revisions", "listing_snapshots",
            "canonical_facts", "domain_objects",
        ):
            conn.execute(f"CREATE TABLE {table}(id TEXT)")
        conn.close()
        with pytest.raises(LegacyAdapterError, match="monitoring_runs"):
            R1LegacyAdapter(db_path)

    def test_rejects_non_synthetic_fixture(self, legacy_db):
        conn = sqlite3.connect(str(legacy_db))
        conn.execute("UPDATE projects SET is_synthetic=0")
        conn.commit()
        conn.close()
        with pytest.raises(LegacyAdapterError, match="synthetic fixtures only"):
            R1LegacyAdapter(legacy_db)

    def test_rejects_non_synthetic_snapshot(self, legacy_db):
        conn = sqlite3.connect(str(legacy_db))
        conn.execute("UPDATE listing_snapshots SET is_synthetic=0")
        conn.commit()
        conn.close()
        with pytest.raises(LegacyAdapterError, match="synthetic snapshots only"):
            R1LegacyAdapter(legacy_db)


class TestProjections:
    def test_project_ids(self, adapter):
        ids = adapter.project_ids()
        assert "legacy-p1" in ids

    def test_sources(self, adapter):
        sources = adapter.sources("legacy-p1")
        assert len(sources) == 1
        assert sources[0].revision_id == "legacy-rev-1"
        assert sources[0].content_hash

    def test_snapshots(self, adapter):
        snaps = adapter.snapshots("legacy-p1")
        assert len(snaps) == 1
        assert snaps[0].snapshot_id == "legacy-snap-1"

    def test_facts(self, adapter):
        facts = adapter.facts("legacy-p1")
        assert len(facts) == 1
        assert facts[0].fact_type == "ae"
        assert facts[0].subject_id == "S01"

    def test_risks(self, adapter):
        risks = adapter.risks("legacy-p1")
        assert len(risks) == 1
        assert risks[0].kind == "risk_identity"

    def test_projection(self, adapter):
        proj = adapter.projection("legacy-p1")
        assert proj.project_id == "legacy-p1"
        assert len(proj.sources) == 1
        assert len(proj.snapshots) == 1
        assert len(proj.facts) == 1
        assert len(proj.risks) == 1

    def test_unknown_project_raises(self, adapter):
        with pytest.raises(LegacyAdapterError):
            adapter.projection("nonexistent")


class TestDualReadDiff:
    def test_all_matched_when_hashes_match(self, adapter):
        legacy = adapter.projection("legacy-p1")
        r2_state = R2DualReadState(
            sources={s.revision_id: s.content_hash for s in legacy.sources},
            snapshots={s.snapshot_id: s.content_hash for s in legacy.snapshots},
            facts={
                adapter.fact_identity_key(f.run_id, f.fact_hash): f.fact_hash
                for f in legacy.facts
            },
            risks={
                adapter.risk_identity_key(r.kind, r.object_id, r.version): r.content_hash
                for r in legacy.risks
            },
        )
        diff = adapter.dual_read_diff("legacy-p1", r2_state)
        assert diff.is_clean is True
        assert len(diff.matched) > 0
        assert len(diff.unmatched) == 0
        assert len(diff.ambiguous) == 0

    def test_ambiguous_when_content_differs(self, adapter):
        legacy = adapter.projection("legacy-p1")
        # R2 has the same identity keys but different content hashes
        r2_state = R2DualReadState(
            sources={s.revision_id: "0" * 64 for s in legacy.sources},
            snapshots={s.snapshot_id: s.content_hash for s in legacy.snapshots},
            facts={
                adapter.fact_identity_key(f.run_id, f.fact_hash): f.fact_hash
                for f in legacy.facts
            },
            risks={
                adapter.risk_identity_key(r.kind, r.object_id, r.version): r.content_hash
                for r in legacy.risks
            },
        )
        diff = adapter.dual_read_diff("legacy-p1", r2_state)
        assert len(diff.ambiguous) >= 1
        assert any(
            e.entity_kind == "source" and e.status == DiffStatus.AMBIGUOUS
            for e in diff.entries
        )

    def test_unmatched_legacy_only(self, adapter):
        # R2 has nothing
        r2_state = R2DualReadState()
        diff = adapter.dual_read_diff("legacy-p1", r2_state)
        assert len(diff.unmatched) > 0
        assert all(
            e.status == DiffStatus.UNMATCHED_LEGACY_ONLY for e in diff.unmatched
        )

    def test_unmatched_r2_only(self, adapter):
        # R2 has extra entities not in legacy
        r2_state = R2DualReadState(
            sources={"r2-extra": "0" * 64},
        )
        diff = adapter.dual_read_diff("legacy-p1", r2_state)
        r2_only = [e for e in diff.entries if e.status == DiffStatus.UNMATCHED_R2_ONLY]
        assert len(r2_only) >= 1

    def test_diff_entry_fields(self, adapter):
        legacy = adapter.projection("legacy-p1")
        r2_state = R2DualReadState(
            sources={s.revision_id: s.content_hash for s in legacy.sources},
        )
        diff = adapter.dual_read_diff("legacy-p1", r2_state)
        for e in diff.matched:
            assert e.legacy_hash == e.r2_hash
            assert e.entity_kind
            assert e.identity_key

    def test_fact_identity_keeps_same_hash_in_different_runs_distinct(
        self, legacy_db,
    ):
        conn = sqlite3.connect(str(legacy_db))
        fact_hash, fact_json = conn.execute(
            "SELECT fact_hash, fact_json FROM canonical_facts LIMIT 1"
        ).fetchone()
        conn.execute(
            "INSERT INTO monitoring_runs(run_id, project_id, mode, data_cutoff,"
            " source_revision_id, execution_basis, analysis_state, evidence_state,"
            " review_state, output_state, manifest_revision, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("legacy-run-2", "legacy-p1", "daily", "cutoff-1", "legacy-rev-1",
             "full", "complete", "complete", "not_required", "dashboard_visible",
             1, "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        conn.execute(
            "INSERT INTO canonical_facts(run_id, fact_hash, fact_id, node_id,"
            " fact_json, created_at) VALUES (?,?,?,?,?,?)",
            ("legacy-run-2", fact_hash, "legacy-fact-2", "ae_mh", fact_json,
             "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with R1LegacyAdapter(legacy_db) as adapter:
            legacy = adapter.projection("legacy-p1")
            state = R2DualReadState(facts={
                adapter.fact_identity_key(f.run_id, f.fact_hash): f.fact_hash
                for f in legacy.facts
            })
            fact_entries = [
                e for e in adapter.dual_read_diff("legacy-p1", state).entries
                if e.entity_kind == "fact"
            ]
            assert len(fact_entries) == 2
            assert all(e.status == DiffStatus.MATCHED for e in fact_entries)

    def test_risk_identity_keeps_kind_and_version_distinct(self, legacy_db):
        conn = sqlite3.connect(str(legacy_db))
        payload = conn.execute(
            "SELECT object_json FROM domain_objects LIMIT 1"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO domain_objects(kind, object_id, version, object_json,"
            " content_hash, created_at) VALUES (?,?,?,?,?,?)",
            ("risk_candidate", "legacy-risk-1", 2, payload, "f" * 64,
             "2026-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        with R1LegacyAdapter(legacy_db) as adapter:
            legacy = adapter.projection("legacy-p1")
            state = R2DualReadState(risks={
                adapter.risk_identity_key(r.kind, r.object_id, r.version): r.content_hash
                for r in legacy.risks
            })
            risk_entries = [
                e for e in adapter.dual_read_diff("legacy-p1", state).entries
                if e.entity_kind == "risk"
            ]
            assert len(risk_entries) == 2
            assert all(e.status == DiffStatus.MATCHED for e in risk_entries)
