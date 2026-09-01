"""Batch C: R2Store persistence, atomic commit, idempotency, publication
read-consistency, reopen, and rollback tests."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from mm_r2.artifacts import ArtifactCompleteness
from mm_r2.store import (
    DashboardInputs, IdempotencyConflictError, R2Store, SaveRequest,
    SaveResult, StoreError,
)


@pytest.fixture
def store(tmp_path):
    s = R2Store(
        tmp_path / "test.db",
        tmp_path / "artifacts",
        local_user="local_test_user",
    )
    yield s
    s.close()


def make_request(run_id="run-1", project_id="p1", snapshot_id="s1",
                 source_revision_id="rev-1", key="idem-1",
                 completeness=ArtifactCompleteness.COMPLETE,
                 payload=None):
    return SaveRequest(
        run_id=run_id,
        project_id=project_id,
        snapshot_id=snapshot_id,
        source_revision_id=source_revision_id,
        payload=payload or {"summary": "monitoring result"},
        idempotency_key=key,
        completeness=completeness,
        facts=(("fact-1", "hash-1"),),
        risks=(("risk-1", "established"),),
        actor="local_test_user",
    )


class TestSaveAndPersist:
    def test_save_returns_committed_result(self, store):
        req = make_request()
        result = store.save(req)
        assert result.revision >= 1
        assert result.content_hash
        assert result.published is True
        assert result.idempotent_replay is False

    def test_dashboard_inputs_reads_committed_state(self, store):
        store.save(make_request(payload={"summary": "v1"}))
        inputs = store.dashboard_inputs("p1")
        assert inputs.project_id == "p1"
        assert inputs.snapshot_id == "s1"
        assert inputs.revision >= 1

    def test_read_artifact_verifies_hash(self, store):
        result = store.save(make_request())
        data = store.read_artifact(result.content_hash)
        assert data  # non-empty verified bytes

    def test_reopen_returns_same_committed_snapshot(self, tmp_path):
        db = tmp_path / "reopen.db"
        art = tmp_path / "art"
        s1 = R2Store(db, art, local_user="local_test_user")
        result = s1.save(make_request(payload={"summary": "persisted"}))
        s1.close()
        # Reopen
        s2 = R2Store(db, art, local_user="local_test_user")
        inputs = s2.dashboard_inputs("p1")
        assert inputs.content_hash == result.content_hash
        assert inputs.snapshot_id == "s1"
        data = s2.read_artifact(result.content_hash)
        assert data
        s2.close()

    def test_same_content_reuses_registered_artifact_reference(self, store):
        first = store.save(make_request(key="same-content-1"))
        second = store.save(make_request(key="same-content-2"))
        assert first.content_hash == second.content_hash
        assert first.artifact_id == second.artifact_id
        assert store._conn.execute(
            "SELECT COUNT(*) FROM r2_artifact_refs WHERE content_hash=?",
            (second.content_hash,),
        ).fetchone()[0] == 1
        assert store._conn.execute(
            "SELECT COUNT(*) FROM r2_artifact_refs WHERE artifact_id=?",
            (second.artifact_id,),
        ).fetchone()[0] == 1

    def test_dashboard_rejects_missing_published_artifact(self, store):
        result = store.save(make_request())
        store.artifact_store._path_for(result.content_hash).unlink()
        with pytest.raises(StoreError, match="artifact is not readable"):
            store.dashboard_inputs("p1")


class TestIdempotency:
    def test_duplicate_key_returns_same_result(self, store):
        req = make_request()
        result1 = store.save(req)
        result2 = store.save(req)
        assert result1.revision == result2.revision
        assert result1.content_hash == result2.content_hash
        assert result2.idempotent_replay is True

    def test_duplicate_key_with_different_request_rejected(self, store):
        store.save(make_request(payload={"v": 1}))
        with pytest.raises(IdempotencyConflictError):
            store.save(make_request(payload={"v": 2}))

    def test_duplicate_key_with_different_actor_rejected(self, store):
        original = make_request()
        store.save(original)
        changed_actor = make_request()
        object.__setattr__(changed_actor, "actor", "different_user")
        with pytest.raises(IdempotencyConflictError):
            store.save(changed_actor)

    def test_post_commit_retry_returns_same_result(self, tmp_path):
        db = tmp_path / "retry.db"
        art = tmp_path / "art"
        s1 = R2Store(db, art, local_user="local_test_user")
        result1 = s1.save(make_request())
        s1.close()
        # Reopen and retry with the same key
        s2 = R2Store(db, art, local_user="local_test_user")
        result2 = s2.save(make_request())
        assert result1.revision == result2.revision
        assert result2.idempotent_replay is True
        s2.close()

    def test_concurrent_same_request_replays_without_duplicate_history(
        self, tmp_path,
    ):
        db = tmp_path / "concurrent.db"
        art = tmp_path / "concurrent-art"
        seed = R2Store(db, art, local_user="local_test_user")
        seed.close()

        def save_once():
            local = R2Store(db, art, local_user="local_test_user")
            try:
                return local.save(make_request(key="concurrent-key"))
            finally:
                local.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: save_once(), range(2)))
        assert {result.revision for result in results} == {1}
        assert sorted(result.idempotent_replay for result in results) == [False, True]
        reopened = R2Store(db, art, local_user="local_test_user")
        assert len(reopened.revision_history("p1")) == 1
        reopened.close()

    def test_pre_commit_interruption_leaves_no_authoritative_state(self, tmp_path):
        db = tmp_path / "interrupt.db"
        art = tmp_path / "art"
        s1 = R2Store(db, art, local_user="local_test_user")
        # Simulate a pre-commit crash
        s1.simulate_pre_commit_interruption()
        # The interrupted row should NOT exist (transaction rolled back)
        rows = list(s1._conn.execute(
            "SELECT * FROM r2_publication_revisions WHERE run_id='interrupted'"
        ).fetchall())
        assert len(rows) == 0
        # Now a real save with a fresh key should succeed
        result = s1.save(make_request(key="k-after-interrupt"))
        assert result.published is True
        s1.close()


class TestPublicationReadConsistency:
    def test_partial_cannot_become_current(self, store):
        req = make_request(completeness=ArtifactCompleteness.PARTIAL)
        result = store.save(req)
        assert result.published is False
        # Nothing should be published
        with pytest.raises(StoreError):
            store.dashboard_inputs("p1")

    def test_truncated_cannot_become_current(self, store):
        req = make_request(completeness=ArtifactCompleteness.TRUNCATED)
        result = store.save(req)
        assert result.published is False

    def test_not_evaluable_cannot_become_current(self, store):
        req = make_request(completeness=ArtifactCompleteness.NOT_EVALUABLE)
        result = store.save(req)
        assert result.published is False

    def test_failed_cannot_become_current(self, store):
        req = make_request(completeness=ArtifactCompleteness.FAILED)
        result = store.save(req)
        assert result.published is False

    def test_complete_advances_pointer(self, store):
        store.save(make_request(payload={"v": 1}))
        assert store.current_revision("p1") is not None
        inputs = store.dashboard_inputs("p1")
        assert inputs.completeness == ArtifactCompleteness.COMPLETE


class TestRevisionHistory:
    def test_history_preserves_all_revisions(self, store):
        store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        history = store.revision_history("p1")
        assert len(history) == 2

    def test_published_history(self, store):
        # Save a partial result (not published)
        store.save(make_request(
            key="k-partial",
            completeness=ArtifactCompleteness.PARTIAL,
        ))
        # Save a complete result (published)
        store.save(make_request(key="k-complete"))
        published = store.published_history("p1")
        assert len(published) == 1  # only the complete one


class TestRollback:
    def test_rollback_to_previous_published_revision(self, store):
        r1 = store.save(make_request(key="k1", payload={"v": 1}))
        r2 = store.save(make_request(key="k2", payload={"v": 2}))
        # Current should be r2
        assert store.current_revision("p1") == r2.revision
        # Roll back to r1
        new_rev = store.rollback_to_published_revision(
            "p1", r1.revision, actor="local_test_user",
        )
        assert new_rev == r1.revision
        assert store.current_revision("p1") == r1.revision
        # Dashboard reads the rolled-back state
        inputs = store.dashboard_inputs("p1")
        assert inputs.revision == r1.revision

    def test_rollback_rejects_unpublished_revision(self, store):
        # Save a partial result (not published)
        inc = store.save(make_request(
            key="k-inc", completeness=ArtifactCompleteness.PARTIAL,
        ))
        # Save a complete result (published)
        store.save(make_request(key="k-comp"))
        with pytest.raises(StoreError):
            store.rollback_to_published_revision(
                "p1", inc.revision, actor="local_test_user",
            )

    def test_rollback_rejects_unknown_revision(self, store):
        store.save(make_request())
        with pytest.raises(StoreError):
            store.rollback_to_published_revision(
                "p1", 99999, actor="local_test_user",
            )

    def test_rollback_preserves_history(self, store):
        r1 = store.save(make_request(key="k1"))
        r2 = store.save(make_request(key="k2"))
        store.rollback_to_published_revision(
            "p1", r1.revision, actor="local_test_user",
        )
        # Both revisions still exist
        history = store.revision_history("p1")
        assert len(history) == 2

    def test_rollback_rejects_unreadable_published_revision(self, store):
        first = store.save(make_request(key="k1", payload={"v": 1}))
        store.save(make_request(key="k2", payload={"v": 2}))
        store.artifact_store._path_for(first.content_hash).unlink()
        with pytest.raises(StoreError, match="artifact is not readable"):
            store.rollback_to_published_revision(
                "p1", first.revision, actor="local_test_user",
            )


class TestRequestValidation:
    def test_rejects_missing_actor(self, store):
        req = make_request()
        object.__setattr__(req, 'actor', '')
        with pytest.raises(StoreError):
            store.save(req)

    def test_rejects_missing_key(self, store):
        req = make_request()
        object.__setattr__(req, 'idempotency_key', '')
        with pytest.raises(StoreError):
            store.save(req)
