"""Batch C: end-to-end functional test.

Saves a synthetic monitoring result, closes/reopens the repository, reads
the current dashboard inputs, applies an idempotent retry, and rolls back
to the previous published revision.
"""

import pytest

from helpers_c import (
    make_algo, make_fact, make_mapping, make_mapping_result, make_project,
    make_record_id, make_snapshot, make_source,
)

from mm_r2.artifacts import ArtifactCompleteness
from mm_r2.domain import to_dictable
from mm_r2.migration import Migration
from mm_r2.store import R2Store, SaveRequest
from mm_r2.verification import Rehydrator


@pytest.fixture
def store(tmp_path):
    s = R2Store(
        tmp_path / "e2e.db", tmp_path / "art",
        local_user="local_test_user",
    )
    yield s
    s.close()


def build_synthetic_result():
    """Build a verified synthetic monitoring result bundle."""
    project = make_project("e2e-p1")
    source = make_source(pid="e2e-p1", rid="e2e-rev-1")
    snap = make_snapshot(pid="e2e-p1", rid="e2e-rev-1", sid="e2e-snap-1")
    algo = make_algo()
    mapping = make_mapping(pid="e2e-p1", rid="e2e-rev-1")
    result = make_mapping_result(pid="e2e-p1", snap=snap, mapping=mapping, algo=algo)
    record = make_record_id(pid="e2e-p1", algo=algo)
    fact = make_fact(
        pid="e2e-p1", project=project, source=source, snap=snap,
        mapping=mapping, result=result, algo=algo, record=record,
    )
    return {
        "project": project,
        "source": source,
        "snap": snap,
        "algo": algo,
        "mapping": mapping,
        "result": result,
        "record": record,
        "fact": fact,
    }


class TestEndToEnd:
    def test_save_reopen_retry_rollback(self, store, tmp_path):
        """The complete acceptance scenario."""
        db_path = store.db_path
        art_path = store.artifact_dir
        bundle = build_synthetic_result()
        fact = bundle["fact"]
        snap = bundle["snap"]
        source = bundle["source"]

        # 1. Save a synthetic monitoring result (revision 1)
        req1 = SaveRequest(
            run_id="e2e-run-1",
            project_id="e2e-p1",
            snapshot_id=snap.snapshot_id,
            source_revision_id=source.revision_id,
            payload={
                "summary": "Q1 monitoring result",
                "metrics": {"ae_count": 1, "subject_count": 1},
            },
            idempotency_key="e2e-key-1",
            completeness=ArtifactCompleteness.COMPLETE,
            facts=((fact.fact_id, fact.content_hash),),
            risks=(("e2e-risk-1", "established"),),
            actor="local_test_user",
        )
        result1 = store.save(req1)
        assert result1.published is True
        assert result1.revision >= 1

        # 2. Save a second revision (revision 2)
        req2 = SaveRequest(
            run_id="e2e-run-1",
            project_id="e2e-p1",
            snapshot_id=snap.snapshot_id,
            source_revision_id=source.revision_id,
            payload={
                "summary": "Q2 monitoring result",
                "metrics": {"ae_count": 2, "subject_count": 1},
            },
            idempotency_key="e2e-key-2",
            completeness=ArtifactCompleteness.COMPLETE,
            facts=((fact.fact_id, fact.content_hash),),
            risks=(("e2e-risk-1", "escalated"),),
            actor="local_test_user",
        )
        result2 = store.save(req2)
        assert result2.revision > result1.revision

        # 3. Close and reopen the repository
        store.close()
        store_reopened = R2Store(db_path, art_path, local_user="local_test_user")

        # 4. Read the current dashboard inputs
        inputs = store_reopened.dashboard_inputs("e2e-p1")
        assert inputs.revision == result2.revision
        assert inputs.content_hash == result2.content_hash
        assert inputs.run_id == "e2e-run-1"
        assert inputs.snapshot_id == snap.snapshot_id
        assert len(inputs.facts) == 1
        assert inputs.facts[0][0] == fact.fact_id

        # The artifact bytes are readable and verified
        artifact_bytes = store_reopened.read_artifact(inputs.content_hash)
        assert artifact_bytes

        # 5. Apply an idempotent retry (same key, same request)
        retry_result = store_reopened.save(req2)
        assert retry_result.revision == result2.revision
        assert retry_result.content_hash == result2.content_hash
        assert retry_result.idempotent_replay is True

        # No duplicate history
        history = store_reopened.revision_history("e2e-p1")
        assert len(history) == 2

        # 6. Roll back to the previous published revision (revision 1)
        rolled_back = store_reopened.rollback_to_published_revision(
            "e2e-p1", result1.revision, actor="local_test_user",
        )
        assert rolled_back == result1.revision

        # Dashboard now reads revision 1
        inputs_after_rollback = store_reopened.dashboard_inputs("e2e-p1")
        assert inputs_after_rollback.revision == result1.revision
        assert inputs_after_rollback.content_hash == result1.content_hash

        # History is still intact (both revisions remain)
        history_after = store_reopened.revision_history("e2e-p1")
        assert len(history_after) == 2

        # Audit chain is intact
        assert store_reopened.audit.verify_chain() is True

        store_reopened.close()

    def test_export_import_preserves_full_state(self, store, tmp_path):
        """Export -> import round-trips the full committed state."""
        bundle = build_synthetic_result()
        fact = bundle["fact"]
        snap = bundle["snap"]
        source = bundle["source"]

        req = SaveRequest(
            run_id="e2e-run-2",
            project_id="e2e-p2",
            snapshot_id=snap.snapshot_id,
            source_revision_id=source.revision_id,
            payload={"summary": "export-import test"},
            idempotency_key="e2e-key-exp",
            facts=((fact.fact_id, fact.content_hash),),
            actor="local_test_user",
        )
        result = store.save(req)

        # Export
        archive = Migration.export_snapshot(store)
        store.close()

        # Import into a new store
        new_store = Migration.import_snapshot(
            archive,
            tmp_path / "e2e-imported.db",
            tmp_path / "e2e-imported-art",
            local_user="local_test_user",
        )
        assert Migration.verify_import(new_store, archive) is True
        inputs = new_store.dashboard_inputs("e2e-p2")
        assert inputs.revision == result.revision
        assert inputs.content_hash == result.content_hash
        new_store.close()

    def test_verified_rehydration_round_trips(self, store, tmp_path):
        """Verified entities rehydrate correctly from the artifact store."""
        bundle = build_synthetic_result()
        source = bundle["source"]
        snap = bundle["snap"]

        # Rehydrate source from explicit bytes
        rh = Rehydrator(store.artifact_store)
        source_data = to_dictable(source)
        rebuilt = rh.rehydrate_source_revision(
            source_data, source_bytes=b"synthetic-source-bytes",
        )
        assert rebuilt.content_hash == source.content_hash
        assert rebuilt.revision_id == source.revision_id

        # Rehydrate snapshot from its rows
        snap_data = to_dictable(snap)
        rebuilt_snap = rh.rehydrate_listing_snapshot(
            snap_data, snapshot_rows=[{"subject": "S01", "ae": "Nausea"}],
        )
        assert rebuilt_snap.content_hash == snap.content_hash

    def test_incomplete_result_never_published(self, store, tmp_path):
        """A NOT_EVALUABLE result can never become the current published
        result, even if it's the most recent save."""
        # First: save a COMPLETE result
        store.save(SaveRequest(
            run_id="e2e-run-3", project_id="e2e-p3", snapshot_id="s1",
            source_revision_id="rev-1", payload={"v": 1},
            idempotency_key="e2e-key-3a",
            completeness=ArtifactCompleteness.COMPLETE,
            actor="local_test_user",
        ))
        # Then: save a NOT_EVALUABLE result
        not_eval_result = store.save(SaveRequest(
            run_id="e2e-run-3", project_id="e2e-p3", snapshot_id="s1",
            source_revision_id="rev-1", payload={"v": 2},
            idempotency_key="e2e-key-3b",
            completeness=ArtifactCompleteness.NOT_EVALUABLE,
            actor="local_test_user",
        ))
        assert not_eval_result.published is False

        # Dashboard still shows the COMPLETE result (revision 1)
        inputs = store.dashboard_inputs("e2e-p3")
        assert inputs.completeness == ArtifactCompleteness.COMPLETE
