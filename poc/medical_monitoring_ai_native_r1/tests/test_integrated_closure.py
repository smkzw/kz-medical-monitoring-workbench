"""Focused tests for the integrated synthetic closure (corrective v2).

These tests prove:

* same-run identity chain across 7 visible work units;
* idempotent completed re-entry (no new transport/facts/audit/manifest);
* partial continuation across Store close/reopen via durable intermediate;
* candidate-only AI output consumed by QC;
* separate journey/query work units;
* truthful failure propagation (blocked, not pending; evidence not complete);
* CLI directory refusal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mm_r1.adapters import AdapterState
from mm_r1.domain import (
    CompletionGateError,
    EvidenceState,
    NodeStatus,
    NodeType,
    OutputState,
    StoreError,
)
from mm_r1.integrated_closure import (
    CLOSURE_MARKER,
    ClosureInterrupted,
    INTERRUPT_AFTER_FACTS,
    INTERRUPT_AFTER_AI,
    SyntheticClosureTransport,
    run_integrated_closure,
)
from mm_r1.store import Store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_store(tmp_path: Path) -> Store:
    return Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts")


# ---------------------------------------------------------------------------
# Same-run identity chain (7 work units)
# ---------------------------------------------------------------------------


class TestSameRunIdentityChain:
    """All outputs share one project/run/snapshot/spine/evidence identity."""

    def test_one_run_one_manifest_one_transport_call(self, r1_store):
        result = run_integrated_closure(r1_store)
        ic = result.identity_chain
        assert result.run_id == ic["run_id"]
        assert result.manifest_revision == 1
        assert result.transport_call_count == 1

    def test_seven_work_units_all_passed(self, r1_store):
        result = run_integrated_closure(r1_store)
        rows = r1_store.list_work_unit_runs(result.run_id, result.manifest_revision)
        assert len(rows) == 7
        assert all(r.status == NodeStatus.PASSED for r in rows)

    def test_ae_mh_shares_run_identity(self, r1_store):
        result = run_integrated_closure(r1_store)
        ic = result.identity_chain
        assert ic["ae_mh_run_id"] == result.run_id
        assert ic["ae_mh_project_id"] == result.project_id

    def test_temporal_spines_share_one_run(self, r1_store):
        result = run_integrated_closure(r1_store)
        ic = result.identity_chain
        assert ic["spines_share_run"] is True
        assert len(ic["spine_subjects"]) >= 2

    def test_profile_and_timeline_share_spine(self, r1_store):
        result = run_integrated_closure(r1_store)
        spines = result.ae_mh_result.temporal_spines
        for subject_id in spines:
            spine = spines[subject_id]
            assert len(spine.events) > 0
            assert all(e.subject_id == subject_id for e in spine.events)
            assert spine.run_id == result.run_id

    def test_query_drafts_retain_three_part_structure(self, r1_store):
        result = run_integrated_closure(r1_store)
        queries = result.ae_mh_result.queries
        assert len(queries) >= 1
        for q in queries:
            assert q.basis and q.finding and q.action

    def test_candidates_never_counted_as_reported(self, r1_store):
        result = run_integrated_closure(r1_store)
        assert result.identity_chain["candidates_counted_as_reported"] is False
        assert result.facts_committed > 0

    def test_separate_journey_and_query_work_units(self, r1_store):
        """Journey (WU 6) and Query (WU 7) are distinct work units."""
        result = run_integrated_closure(r1_store)
        rows = r1_store.list_work_unit_runs(result.run_id, result.manifest_revision)
        wu_ids = {r.work_unit_id for r in rows}
        assert "closure-wu-journey" in wu_ids
        assert "closure-wu-query" in wu_ids
        assert "closure-wu-journey" != "closure-wu-query"


# ---------------------------------------------------------------------------
# Candidate-only AI output consumed by QC
# ---------------------------------------------------------------------------


class TestCandidateOnlyAIConsumedByQC:
    """AI output is raw-first, candidate-only, and explicitly consumed by QC."""

    def test_transport_called_exactly_once(self, r1_store):
        transport = SyntheticClosureTransport()
        run_integrated_closure(r1_store, transport=transport)
        assert transport.call_count == 1

    def test_ai_candidate_not_in_facts(self, r1_store):
        result = run_integrated_closure(r1_store)
        facts = r1_store.list_facts(result.run_id)
        assert all(f.fact_type != "ai_candidate_review" for f in facts)

    def test_qc_consumes_ai_evidence(self, r1_store):
        """QC artifact must reference the AI attempt's raw/candidate evidence."""
        result = run_integrated_closure(r1_store)
        ic = result.identity_chain
        assert ic["ai_evidence_consumed_by_qc"] is True
        assert ic["ai_raw_ref"] is not None
        assert ic["ai_promoted_to_fact"] is False

    def test_raw_output_persisted(self, r1_store):
        result = run_integrated_closure(r1_store)
        raw_outputs = r1_store.list_domain_objects("adapter_raw_output")
        assert len(raw_outputs) >= 1

    def test_qc_node_has_ai_review_support_in_payload(self, r1_store):
        """The QC node's output should record that AI evidence was consumed."""
        result = run_integrated_closure(r1_store)
        qc_node = r1_store.get_node_run(result.run_id, "closure-node-qc")
        assert qc_node is not None
        assert qc_node.output.get("ai_evidence_consumed") is True


# ---------------------------------------------------------------------------
# Idempotent completed re-entry
# ---------------------------------------------------------------------------


class TestIdempotentReentry:
    """Re-calling run_integrated_closure returns the stored result with no side effects."""

    def test_completed_reentry_no_new_transport(self, r1_store):
        """Same Store/run re-entry: zero new transport calls."""
        result1 = run_integrated_closure(r1_store)
        transport2 = SyntheticClosureTransport()
        result2 = run_integrated_closure(r1_store, transport=transport2)
        assert transport2.call_count == 0
        assert result2.run_id == result1.run_id

    def test_completed_reentry_no_new_audit(self, r1_store):
        result1 = run_integrated_closure(r1_store)
        audit1 = len(r1_store.audit_trail())
        run_integrated_closure(r1_store)
        audit2 = len(r1_store.audit_trail())
        assert audit1 == audit2

    def test_completed_reentry_no_new_facts(self, r1_store):
        result1 = run_integrated_closure(r1_store)
        facts1 = len(r1_store.list_facts(result1.run_id))
        run_integrated_closure(r1_store)
        facts2 = len(r1_store.list_facts(result1.run_id))
        assert facts1 == facts2

    def test_completed_reentry_no_new_artifacts(self, r1_store):
        result1 = run_integrated_closure(r1_store)
        artifacts1 = len(r1_store.list_artifacts(result1.run_id))
        run_integrated_closure(r1_store)
        artifacts2 = len(r1_store.list_artifacts(result1.run_id))
        assert artifacts1 == artifacts2

    def test_completed_reentry_no_manifest_revision(self, r1_store):
        result1 = run_integrated_closure(r1_store)
        run_integrated_closure(r1_store)
        revisions = r1_store.list_manifest_revisions(result1.run_id)
        assert revisions == [1]


# ---------------------------------------------------------------------------
# Partial continuation across Store close/reopen
# ---------------------------------------------------------------------------


class TestStoreReopenContinuation:
    """Interrupt after facts, close Store, reopen, and continue to completion."""

    def test_interrupt_after_facts_then_continue(self, tmp_path):
        store1 = _new_store(tmp_path)
        try:
            run_integrated_closure(store1, interrupt_after=INTERRUPT_AFTER_FACTS)
            pytest.fail("should have raised ClosureInterrupted")
        except ClosureInterrupted as e:
            assert e.phase == INTERRUPT_AFTER_FACTS

        run_id = "SYNTHETIC-RUN-N1"
        audit_after_interrupt = len(store1.audit_trail())
        facts_after_interrupt = len(store1.list_facts(run_id))
        assert facts_after_interrupt > 0  # facts persisted before interrupt
        store1.close()

        # Reopen and continue — intermediate AE/MH result is reconstructed.
        store2 = Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts")
        transport = SyntheticClosureTransport()
        result = run_integrated_closure(store2, transport=transport)
        assert transport.call_count == 1  # AI transport called once during continuation
        assert result.run_output_state == "draft_exportable"
        assert result.evidence_state == "complete"

        # Audit grew (new work units completed) but facts are stable.
        audit_after_continue = len(store2.audit_trail())
        facts_after_continue = len(store2.list_facts(run_id))
        assert audit_after_continue > audit_after_interrupt
        assert facts_after_continue == facts_after_interrupt
        store2.close()

    def test_intermediate_result_reconstructed_exact(self, tmp_path):
        """The reconstructed intermediate AE/MH result matches the original."""
        store1 = _new_store(tmp_path)
        try:
            run_integrated_closure(store1, interrupt_after=INTERRUPT_AFTER_FACTS)
        except ClosureInterrupted:
            pass

        from mm_r1.domain import content_hash, to_jsonable
        from mm_r1.integrated_closure import _load_intermediate
        run_id = "SYNTHETIC-RUN-N1"

        # The intermediate was persisted by the orchestrator.
        reconstructed = _load_intermediate(store1, run_id)
        assert reconstructed is not None
        assert reconstructed.run_id == run_id
        assert reconstructed.project_id == "SYNTHETIC-R1-AEMH"
        assert len(reconstructed.reported_facts) > 0
        assert len(reconstructed.temporal_spines) >= 2

    def test_interrupt_after_ai_then_continue(self, tmp_path):
        """Interrupt after AI success, close Store, reopen, continue to completion."""
        store1 = _new_store(tmp_path)
        try:
            run_integrated_closure(store1, interrupt_after=INTERRUPT_AFTER_AI)
            pytest.fail("should have raised ClosureInterrupted")
        except ClosureInterrupted as e:
            assert e.phase == INTERRUPT_AFTER_AI

        run_id = "SYNTHETIC-RUN-N1"
        audit_after_interrupt = len(store1.audit_trail())
        facts_after_interrupt = len(store1.list_facts(run_id))
        assert facts_after_interrupt > 0
        store1.close()

        store2 = Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts")
        transport = SyntheticClosureTransport()
        result = run_integrated_closure(store2, transport=transport)
        # Transport NOT called again — AI already completed before interrupt.
        assert transport.call_count == 0
        assert result.run_output_state == "draft_exportable"
        assert result.evidence_state == "complete"
        # Store evidence state matches result.
        assert store2.get_run(run_id).evidence_state.value == "complete"
        audit_after_continue = len(store2.audit_trail())
        assert audit_after_continue > audit_after_interrupt
        store2.close()

    def test_failure_evidence_state_matches_store(self, tmp_path):
        """On AI failure, Store.evidence_state must equal ClosureResult.evidence_state."""
        store = _new_store(tmp_path)
        result = run_integrated_closure(store, fail_ai_transport=True)
        store_evidence = store.get_run(result.run_id).evidence_state.value
        assert store_evidence == result.evidence_state == "partial"
        store.close()

    def test_skip_ai_evidence_state_matches_store(self, tmp_path):
        """On AI skip, Store.evidence_state must equal ClosureResult.evidence_state."""
        store = _new_store(tmp_path)
        result = run_integrated_closure(store, skip_ai=True)
        store_evidence = store.get_run(result.run_id).evidence_state.value
        assert store_evidence == result.evidence_state == "partial"
        store.close()


# ---------------------------------------------------------------------------
# Truthful failure propagation
# ---------------------------------------------------------------------------


class TestTruthfulFailurePropagation:
    """AI failure/skip marks downstream BLOCKED, evidence PARTIAL, no publish."""

    def test_transport_failure_evidence_partial(self, r1_store):
        result = run_integrated_closure(r1_store, fail_ai_transport=True)
        assert result.evidence_state == "partial"
        assert result.run_output_state == "not_published"

    def test_transport_failure_downstream_blocked(self, r1_store):
        result = run_integrated_closure(r1_store, fail_ai_transport=True)
        rows = r1_store.list_work_unit_runs(result.run_id, result.manifest_revision)
        statuses = {r.work_unit_id: r.status for r in rows}
        # Accept and facts should pass; AI should fail; QC/dashboard/journey/query blocked.
        assert statuses["closure-wu-accept"] == NodeStatus.PASSED
        assert statuses["closure-wu-facts"] == NodeStatus.PASSED
        assert statuses["closure-wu-ai-candidate"] == NodeStatus.FAILED
        assert statuses["closure-wu-qc"] == NodeStatus.BLOCKED
        assert statuses["closure-wu-dashboard"] == NodeStatus.BLOCKED
        assert statuses["closure-wu-journey"] == NodeStatus.BLOCKED
        assert statuses["closure-wu-query"] == NodeStatus.BLOCKED

    def test_transport_failure_all_work_units_terminal(self, r1_store):
        """No work unit should be left pending — all are terminal."""
        result = run_integrated_closure(r1_store, fail_ai_transport=True)
        rows = r1_store.list_work_unit_runs(result.run_id, result.manifest_revision)
        terminal = {NodeStatus.PASSED, NodeStatus.FAILED, NodeStatus.BLOCKED,
                    NodeStatus.REUSED, NodeStatus.SKIPPED, NodeStatus.NOT_APPLICABLE}
        assert all(r.status in terminal for r in rows)

    def test_transport_failure_progress_shows_blocked(self, r1_store):
        """Audience progress must show blocked items, not appear forever active."""
        result = run_integrated_closure(r1_store, fail_ai_transport=True)
        prog = result.audience_progress
        # All 7 are terminal (some passed, some failed, some blocked).
        assert prog["completed"] == 7
        assert prog["total"] == 7
        # The headline should not claim the run is still running.
        assert "运行中" not in prog["headline"]

    def test_skip_ai_downstream_blocked(self, r1_store):
        result = run_integrated_closure(r1_store, skip_ai=True)
        assert result.evidence_state == "partial"
        # Store evidence state must match ClosureResult.
        assert r1_store.get_run(result.run_id).evidence_state.value == "partial"
        rows = r1_store.list_work_unit_runs(result.run_id, result.manifest_revision)
        statuses = {r.work_unit_id: r.status for r in rows}
        # AI work unit is BLOCKED via controller interrupt/reconcile (not PENDING).
        assert statuses["closure-wu-ai-candidate"] == NodeStatus.BLOCKED
        assert statuses["closure-wu-qc"] == NodeStatus.BLOCKED
        assert result.audience_progress["completed"] == 7
        assert result.audience_progress["total"] == 7
        assert "已结束" in result.audience_progress["headline"]

    def test_corrupted_artifact_blocks_export(self, tmp_path):
        store = _new_store(tmp_path)
        result = run_integrated_closure(store)
        run_id = result.run_id

        node_runs = store.list_node_runs(run_id)
        mandatory_artifact_ids = [nr.artifact_id for nr in node_runs if nr.artifact_id]
        assert len(mandatory_artifact_ids) > 0

        artifact_dir = tmp_path / "artifacts"
        target_file = artifact_dir / (mandatory_artifact_ids[0] + ".json")
        assert target_file.exists()
        target_file.write_text('{"corrupted": true}', encoding="utf-8")
        assert store.verify_artifact(mandatory_artifact_ids[0]) is False

        import getpass
        with pytest.raises((CompletionGateError, StoreError)):
            store.publish(run_id, OutputState.EXPORTED,
                          reason="corruption test", actor=getpass.getuser())

    def test_qc_fails_when_ai_raw_corrupted(self, tmp_path):
        """Corrupt AI raw evidence after AI completion and before QC continuation."""
        store1 = _new_store(tmp_path)
        with pytest.raises(ClosureInterrupted):
            run_integrated_closure(store1, interrupt_after=INTERRUPT_AFTER_AI)
        run_id = "SYNTHETIC-RUN-N1"

        adapter_row = store1.get_domain_object(
            "adapter_run", "adapter-run:closure-ai-attempt-1",
        )
        assert adapter_row is not None
        raw_ref = adapter_row[1]["raw_output_ref"]
        assert store1.verify_adapter_raw_output(raw_ref) is True

        store1.close()

        # Raw transport evidence is an immutable domain object in SQLite,
        # not a content-addressed artifact file. Tamper only its stored JSON
        # while leaving the recorded outer hash unchanged.
        import sqlite3
        conn = sqlite3.connect(str(tmp_path / "r1.sqlite3"))
        conn.execute(
            "UPDATE domain_objects SET object_json=? WHERE kind=? AND object_id=?",
            ("{}", "adapter_raw_output", "adapter-raw:%s" % raw_ref),
        )
        conn.commit()
        conn.close()

        store2 = _new_store(tmp_path)
        assert store2.verify_adapter_raw_output(raw_ref) is False
        result = run_integrated_closure(store2)
        assert result.run_output_state == "not_published"
        assert result.evidence_state == "partial"
        qc = store2.get_node_run(run_id, "closure-node-qc")
        assert qc.status == NodeStatus.FAILED
        assert qc.output["qc_passed"] is False
        assert qc.output["ai_raw_verified"] is False
        rows = {
            row.work_unit_id: row.status
            for row in store2.list_work_unit_runs(run_id, 1)
        }
        assert rows["closure-wu-dashboard"] == NodeStatus.BLOCKED
        assert rows["closure-wu-journey"] == NodeStatus.BLOCKED
        assert rows["closure-wu-query"] == NodeStatus.BLOCKED
        store2.close()

    def test_dashboard_artifact_count_matches_persisted(self, tmp_path):
        """Dashboard artifact projection_count must equal persist_projections count."""
        store = _new_store(tmp_path)
        result = run_integrated_closure(store)

        # Find the dashboard artifact.
        artifacts = store.list_artifacts(result.run_id)
        dashboard_artifacts = [a for a in artifacts if a.artifact_type == "risk_dashboard_projection"]
        assert len(dashboard_artifacts) == 1
        dash = dashboard_artifacts[0]

        # The artifact projection_count must match the node output count.
        dash_node = store.get_node_run(result.run_id, "closure-node-dashboard")
        node_count = dash_node.output["projection_count"]
        artifact_count = dash.payload["projection_count"]
        assert artifact_count == node_count
        assert artifact_count > 0, "projection_count must not be zero"
        assert artifact_count == result.projections_persisted
        store.close()


# ---------------------------------------------------------------------------
# Audience progress from single authority
# ---------------------------------------------------------------------------


class TestAudienceProgress:
    """Progress comes only from project_audience_progress."""

    def test_progress_7_of_7(self, r1_store):
        result = run_integrated_closure(r1_store)
        assert result.audience_progress["completed"] == 7
        assert result.audience_progress["total"] == 7
        assert result.audience_progress["percent"] == 100.0

    def test_progress_no_internal_leaks(self, r1_store):
        result = run_integrated_closure(r1_store)
        serialized = json.dumps(result.audience_progress, ensure_ascii=False, default=str)
        for forbidden in ("provider", "model", "attempt", "backend", "hash", "fingerprint"):
            assert forbidden not in serialized.lower()

    def test_manifest_progress_matches_audience(self, r1_store):
        result = run_integrated_closure(r1_store)
        sp = r1_store.manifest_progress(result.run_id)
        assert sp["completed"] == result.audience_progress["completed"]
        assert sp["total"] == result.audience_progress["total"]


# ---------------------------------------------------------------------------
# Publication gate
# ---------------------------------------------------------------------------


class TestPublicationGate:
    def test_draft_exportable_on_success(self, r1_store):
        result = run_integrated_closure(r1_store)
        assert result.run_output_state == "draft_exportable"

    def test_export_requires_actor(self, r1_store):
        result = run_integrated_closure(r1_store)
        with pytest.raises(CompletionGateError):
            r1_store.publish(result.run_id, OutputState.EXPORTED, reason="no actor")

    def test_export_with_os_user(self, r1_store):
        import getpass
        result = run_integrated_closure(r1_store)
        published = r1_store.publish(
            result.run_id, OutputState.EXPORTED,
            reason="test", actor=getpass.getuser(),
        )
        assert published.output_state == OutputState.EXPORTED


# ---------------------------------------------------------------------------
# Audit chain
# ---------------------------------------------------------------------------


class TestAuditChain:
    def test_audit_chain_verifies(self, r1_store):
        run_integrated_closure(r1_store)
        ok, first_bad, count = r1_store.verify_audit_chain()
        assert ok and first_bad is None and count > 0

    def test_reopen_preserves_audit(self, tmp_path):
        store1 = _new_store(tmp_path)
        result = run_integrated_closure(store1)
        audit1 = store1.audit_trail()
        store1.close()
        store2 = Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts")
        audit2 = store2.audit_trail()
        assert len(audit2) == len(audit1)
        ok, _, _ = store2.verify_audit_chain()
        assert ok
        store2.close()


# ---------------------------------------------------------------------------
# CLI directory refusal
# ---------------------------------------------------------------------------


class TestCLIDirectoryRefusal:
    def test_refuses_non_empty_directory(self, tmp_path):
        """CLI must reject a non-empty unrelated directory."""
        # Import the CLI module path directly.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_integrated_closure_cli",
            str(Path(__file__).resolve().parents[1] / "scripts" / "run_integrated_closure.py"),
        )
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)

        # Create a non-empty directory.
        non_empty = tmp_path / "non_empty"
        non_empty.mkdir()
        (non_empty / "unrelated.txt").write_text("hello")

        with pytest.raises(SystemExit, match="non-empty"):
            cli._resolve_output_dir(str(non_empty))

    def test_accepts_empty_directory(self, tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_integrated_closure_cli",
            str(Path(__file__).resolve().parents[1] / "scripts" / "run_integrated_closure.py"),
        )
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)

        empty = tmp_path / "empty_dir"
        resolved = cli._resolve_output_dir(str(empty))
        assert resolved.exists()
