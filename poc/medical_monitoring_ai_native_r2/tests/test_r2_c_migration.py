"""Batch C: export/import/backup/restore/rollback migration tests."""

import json

import pytest

from mm_r2.artifacts import ArtifactCompleteness
from mm_r2.domain import canonical_json, content_hash, sha256_hex
from mm_r2.migration import Migration, MigrationArchive, MigrationError
from mm_r2.store import R2Store, SaveRequest, StoreError


def make_request(key="idem-1", payload=None,
                 completeness=ArtifactCompleteness.COMPLETE):
    return SaveRequest(
        run_id="run-1", project_id="p1", snapshot_id="s1",
        source_revision_id="rev-1",
        payload=payload or {"summary": "monitoring result"},
        idempotency_key=key, completeness=completeness,
        facts=(("fact-1", "hash-1"),),
        risks=(("risk-1", "established"),),
        actor="local_test_user",
    )


def rebuild_archive(archive, *, tables=None, artifacts=None):
    new_tables = tables if tables is not None else archive.tables
    new_artifacts = artifacts if artifacts is not None else archive.artifacts
    return MigrationArchive(
        store_id=archive.store_id,
        exported_at=archive.exported_at,
        tables=new_tables,
        artifacts=new_artifacts,
        archive_hash=content_hash({
            "archive_type": Migration.ARCHIVE_TYPE,
            "archive_version": Migration.ARCHIVE_VERSION,
            "store_id": archive.store_id,
            "tables": new_tables,
            "artifacts": new_artifacts,
        }),
    )


@pytest.fixture
def store(tmp_path):
    s = R2Store(
        tmp_path / "src.db", tmp_path / "art",
        local_user="local_test_user",
    )
    yield s
    s.close()


class TestExportImport:
    def test_export_round_trips_state(self, store, tmp_path):
        r1 = store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        archive = Migration.export_snapshot(store)
        assert archive.archive_hash
        assert len(archive.tables.get("r2_publication_revisions", [])) == 2
        # Artifacts included
        assert r1.content_hash in archive.artifacts

    def test_import_rebuilds_store_with_same_publication(self, store, tmp_path):
        store.save(make_request(key="k1", payload={"v": 1}))
        r2 = store.save(make_request(key="k2", payload={"v": 2}))
        archive = Migration.export_snapshot(store)
        store.close()

        new_store = Migration.import_snapshot(
            archive,
            tmp_path / "imported.db",
            tmp_path / "imported-art",
            local_user="local_test_user",
        )
        inputs = new_store.dashboard_inputs("p1")
        assert inputs.revision == r2.revision
        assert inputs.content_hash == r2.content_hash
        # History preserved
        history = new_store.revision_history("p1")
        assert len(history) == 2
        new_store.close()

    def test_import_preserves_idempotency_ledger(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        store.close()

        new_store = Migration.import_snapshot(
            archive, tmp_path / "imp.db", tmp_path / "imp-art",
            local_user="local_test_user",
        )
        # Replaying the same key should return idempotent_replay
        result = new_store.save(make_request(key="k1"))
        assert result.idempotent_replay is True
        new_store.close()

    def test_import_preserves_audit_chain(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        store.close()

        new_store = Migration.import_snapshot(
            archive, tmp_path / "imp.db", tmp_path / "imp-art",
            local_user="local_test_user",
        )
        assert new_store.audit.verify_chain() is True
        new_store.close()

    def test_verify_import_confirms_fidelity(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        store.close()

        new_store = Migration.import_snapshot(
            archive, tmp_path / "imp.db", tmp_path / "imp-art",
            local_user="local_test_user",
        )
        assert Migration.verify_import(new_store, archive) is True
        new_store.close()

    def test_import_rejects_corrupt_artifact_bytes(self, tmp_path):
        store = R2Store(tmp_path / "src.db", tmp_path / "art",
                        local_user="local_test_user")
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        store.close()
        # Corrupt one artifact's bytes
        corrupt = MigrationArchive(
            store_id=archive.store_id,
            exported_at=archive.exported_at,
            tables=archive.tables,
            artifacts={
                k: ("ff" * len(v) if i == 0 else v)
                for i, (k, v) in enumerate(archive.artifacts.items())
            },
            archive_hash=archive.archive_hash,
        )
        with pytest.raises((MigrationError, Exception)):
            Migration.import_snapshot(
                corrupt, tmp_path / "imp.db", tmp_path / "imp-art",
                local_user="local_test_user",
            )

    def test_import_rejects_inconsistent_archive_tables(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        altered_tables = {
            name: [dict(row) for row in rows]
            for name, rows in archive.tables.items()
        }
        altered_tables["r2_publication_revisions"][0]["project_id"] = "other"
        inconsistent = MigrationArchive(
            store_id=archive.store_id,
            exported_at=archive.exported_at,
            tables=altered_tables,
            artifacts=archive.artifacts,
            archive_hash=archive.archive_hash,
        )
        with pytest.raises(MigrationError, match="archive hash mismatch"):
            Migration.import_snapshot(
                inconsistent, tmp_path / "bad.db", tmp_path / "bad-art",
                local_user="local_test_user",
            )

    def test_import_rejects_self_consistent_archive_missing_revision_artifact(
        self, store, tmp_path,
    ):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        missing_artifact = MigrationArchive(
            store_id=archive.store_id,
            exported_at=archive.exported_at,
            tables=archive.tables,
            artifacts={},
            archive_hash="",
        )
        object.__setattr__(missing_artifact, "archive_hash", content_hash({
            "archive_type": Migration.ARCHIVE_TYPE,
            "archive_version": Migration.ARCHIVE_VERSION,
            "store_id": missing_artifact.store_id,
            "tables": missing_artifact.tables,
            "artifacts": missing_artifact.artifacts,
        }))
        with pytest.raises(MigrationError, match="missing artifacts"):
            Migration.import_snapshot(
                missing_artifact, tmp_path / "missing.db",
                tmp_path / "missing-art", local_user="local_test_user",
            )

    @pytest.mark.parametrize("missing_table", [
        "r2_publication_pointer", "r2_idempotency_ledger",
    ])
    def test_import_rejects_self_consistent_archive_missing_required_state(
        self, store, tmp_path, missing_table,
    ):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        altered_tables = {
            name: [dict(row) for row in rows]
            for name, rows in archive.tables.items()
        }
        altered_tables[missing_table] = []
        altered = MigrationArchive(
            store_id=archive.store_id,
            exported_at=archive.exported_at,
            tables=altered_tables,
            artifacts=archive.artifacts,
            archive_hash=content_hash({
                "archive_type": Migration.ARCHIVE_TYPE,
                "archive_version": Migration.ARCHIVE_VERSION,
                "store_id": archive.store_id,
                "tables": altered_tables,
                "artifacts": archive.artifacts,
            }),
        )
        with pytest.raises(MigrationError):
            Migration.import_snapshot(
                altered, tmp_path / f"{missing_table}.db",
                tmp_path / f"{missing_table}-art", local_user="local_test_user",
            )

    def test_import_rejects_existing_database_target(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        target_db = tmp_path / "existing.db"
        target = R2Store(
            target_db, tmp_path / "existing-art", local_user="local_test_user",
        )
        target.close()
        with pytest.raises(MigrationError, match="fresh database target"):
            Migration.import_snapshot(
                archive, target_db, tmp_path / "new-art",
                local_user="local_test_user",
            )

    def test_import_rejects_duplicate_publication_pointer(self, store, tmp_path):
        first = store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        archive = Migration.export_snapshot(store)
        tables = {name: [dict(row) for row in rows]
                  for name, rows in archive.tables.items()}
        duplicate = dict(tables["r2_publication_pointer"][0])
        duplicate["current_revision"] = first.revision
        tables["r2_publication_pointer"].append(duplicate)
        altered = rebuild_archive(archive, tables=tables)
        with pytest.raises(MigrationError, match="more than one current"):
            Migration.import_snapshot(
                altered, tmp_path / "dup-pointer.db", tmp_path / "dup-pointer-art",
                local_user="local_test_user",
            )

    def test_import_rejects_duplicate_revision_identity(self, store, tmp_path):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        tables = {name: [dict(row) for row in rows]
                  for name, rows in archive.tables.items()}
        tables["r2_publication_revisions"].append(
            dict(tables["r2_publication_revisions"][0])
        )
        altered = rebuild_archive(archive, tables=tables)
        with pytest.raises(MigrationError, match="duplicate revision"):
            Migration.import_snapshot(
                altered, tmp_path / "dup-rev.db", tmp_path / "dup-rev-art",
                local_user="local_test_user",
            )

    def test_import_rejects_ledger_result_bound_to_wrong_revision(
        self, store, tmp_path,
    ):
        store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        archive = Migration.export_snapshot(store)
        tables = {name: [dict(row) for row in rows]
                  for name, rows in archive.tables.items()}
        first_result = tables["r2_idempotency_ledger"][0]["result_json"]
        tables["r2_idempotency_ledger"][1]["result_json"] = first_result
        altered = rebuild_archive(archive, tables=tables)
        with pytest.raises(MigrationError, match="binding is inconsistent"):
            Migration.import_snapshot(
                altered, tmp_path / "bad-ledger.db", tmp_path / "bad-ledger-art",
                local_user="local_test_user",
            )

    def test_import_rejects_history_row_missing_from_business_history(
        self, store, tmp_path,
    ):
        first = store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        archive = Migration.export_snapshot(store)
        tables = {name: [dict(row) for row in rows]
                  for name, rows in archive.tables.items()}
        tables["r2_publication_revisions"] = [
            row for row in tables["r2_publication_revisions"]
            if int(row["revision"]) != first.revision
        ]
        tables["r2_idempotency_ledger"] = [
            row for row in tables["r2_idempotency_ledger"]
            if int(json.loads(row["result_json"])["revision"]) != first.revision
        ]
        altered = rebuild_archive(archive, tables=tables)
        with pytest.raises(MigrationError, match="business history"):
            Migration.import_snapshot(
                altered, tmp_path / "missing-history.db",
                tmp_path / "missing-history-art", local_user="local_test_user",
            )

    def test_import_rejects_partial_artifact_for_complete_revision(
        self, store, tmp_path,
    ):
        store.save(make_request(key="k1"))
        archive = Migration.export_snapshot(store)
        tables = {name: [dict(row) for row in rows]
                  for name, rows in archive.tables.items()}
        _, old_hex = next(iter(archive.artifacts.items()))
        contract = json.loads(bytes.fromhex(old_hex).decode("utf-8"))
        contract["completeness"] = ArtifactCompleteness.PARTIAL
        new_bytes = canonical_json(contract).encode("utf-8")
        new_hash = sha256_hex(new_bytes)
        revision = tables["r2_publication_revisions"][0]
        revision["content_hash"] = new_hash
        artifact_ref = tables["r2_artifact_refs"][0]
        artifact_ref["content_hash"] = new_hash
        envelope = json.loads(artifact_ref["envelope_json"])
        envelope["fields"]["content_hash"] = new_hash
        artifact_ref["envelope_json"] = canonical_json(envelope)
        ledger = tables["r2_idempotency_ledger"][0]
        result = json.loads(ledger["result_json"])
        result["content_hash"] = new_hash
        ledger["result_json"] = json.dumps(
            result, sort_keys=True, ensure_ascii=False,
        )
        altered = rebuild_archive(
            archive, tables=tables, artifacts={new_hash: new_bytes.hex()},
        )
        with pytest.raises(MigrationError, match="artifact bytes"):
            Migration.import_snapshot(
                altered, tmp_path / "partial-contract.db",
                tmp_path / "partial-contract-art", local_user="local_test_user",
            )


class TestBackupRestore:
    def test_backup_and_restore_preserves_state(self, store, tmp_path):
        r1 = store.save(make_request(key="k1", payload={"v": 1}))
        backup_dir = Migration.backup(store, tmp_path / "backup")

        restored = Migration.restore(
            backup_dir, tmp_path / "restored.db", tmp_path / "restored-art",
            local_user="local_test_user",
        )
        inputs = restored.dashboard_inputs("p1")
        assert inputs.revision == r1.revision
        assert inputs.content_hash == r1.content_hash
        restored.close()

    def test_restore_preserves_artifact_bytes(self, store, tmp_path):
        r1 = store.save(make_request(key="k1"))
        backup_dir = Migration.backup(store, tmp_path / "backup")
        restored = Migration.restore(
            backup_dir, tmp_path / "restored.db", tmp_path / "restored-art",
            local_user="local_test_user",
        )
        data = restored.read_artifact(r1.content_hash)
        assert data
        restored.close()

    def test_backup_then_rollback_then_restore(self, store, tmp_path):
        r1 = store.save(make_request(key="k1", payload={"v": 1}))
        r2 = store.save(make_request(key="k2", payload={"v": 2}))
        # Rollback before backup
        store.rollback_to_published_revision(
            "p1", r1.revision, actor="local_test_user",
        )
        backup_dir = Migration.backup(store, tmp_path / "backup")
        restored = Migration.restore(
            backup_dir, tmp_path / "r.db", tmp_path / "r-art",
            local_user="local_test_user",
        )
        inputs = restored.dashboard_inputs("p1")
        assert inputs.revision == r1.revision
        restored.close()


class TestRollbackMigration:
    def test_migration_rollback_delegates_to_store(self, store):
        r1 = store.save(make_request(key="k1"))
        store.save(make_request(key="k2"))
        new_rev = Migration.rollback(
            store, "p1", r1.revision, actor="local_test_user",
        )
        assert new_rev == r1.revision
        assert store.current_revision("p1") == r1.revision
