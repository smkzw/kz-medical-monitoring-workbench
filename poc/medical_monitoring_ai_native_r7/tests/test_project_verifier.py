"""Focused synthetic/offline tests for Slice-09C verification wiring."""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mm_r1.store import Store
from mm_r7.launch_registry import LaunchRegistry, content_digest
from mm_r7.project_audit import ProjectAuditLedger
from mm_r7.project_backup import OperationLedger
from mm_r7.project_verifier import (
    ProjectVerifier,
    RecoveryCoordinator,
    RESULT_ANOMALY,
    RESULT_RECORD_COMPLETE,
    RESULT_RECOVERY_REQUIRED,
)
from fixtures_schema_manifest import make_project



def _current_project(tmp_path: Path, project_id: str = "synthetic-09c") -> tuple[Path, Path]:
    runtime_root = tmp_path / "medical_monitoring_r7"
    workspace = runtime_root / project_id
    make_project(workspace)
    return runtime_root, workspace


def _add_available_publication(workspace: Path, project_id: str) -> str:
    registry = LaunchRegistry(workspace / "launch_registry.sqlite3", project_id=project_id)
    try:
        launch = registry.reserve(
            project_id,
            idempotency_key="launch-09c",
            mode="daily",
            execution_basis="full",
            current_snapshot_token="snapshot-09c",
            data_cutoff="2026-08-30",
            comparison_range="合成全量范围",
        )
        registry.reserve_publication(
            project_id,
            launch.run_id,
            idempotency_key="publication-09c",
            request_fingerprint="fingerprint-09c",
            snapshot_token="snapshot-09c",
            data_cutoff="2026-08-30",
        )
        registry.mark_completed(launch.run_id, project_id=project_id)
        members = ("artifact-a", "artifact-b", "artifact-c", "artifact-d")
        registry.finalize_publication(
            project_id,
            launch.run_id,
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=content_digest(list(members)),
        )
        return launch.run_id
    finally:
        registry.close()



def test_verifier_records_pair_reuses_public_r1_chain_and_stable_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root, workspace = _current_project(tmp_path)
    calls: list[str] = []
    original = Store.verify_audit_chain
    caller_thread = threading.current_thread()

    def spy(store: Store):  # type: ignore[no-untyped-def]
        # Adjacent product-router tests may still be draining an accepted
        # background worker.  Count only this verifier invocation's thread.
        if threading.current_thread() is caller_thread:
            calls.append("verify_audit_chain")
        return original(store)

    monkeypatch.setattr(Store, "verify_audit_chain", spy)
    verifier = ProjectVerifier(runtime_root, "synthetic-09c", project_dir=workspace)
    first = verifier.verify()
    fingerprint = verifier.snapshot_fingerprint()
    second = verifier.verify()
    verifier.close()

    assert first.result == RESULT_RECORD_COMPLETE
    assert second.result == RESULT_RECORD_COMPLETE
    assert first.snapshot_fingerprint == second.snapshot_fingerprint == fingerprint
    assert first.started_event_id and first.completed_event_id
    assert second.started_event_id and second.completed_event_id
    assert len(calls) == 2
    assert set(first.as_public_dict()) == {"result", "message", "nextAction"}

    ledger = ProjectAuditLedger(runtime_root)
    events = ledger.events("synthetic-09c")
    assert [event.event_kind for event in events] == [
        "verification_started",
        "verification_completed",
        "verification_started",
        "verification_completed",
    ]
    assert ledger.verify_chain("synthetic-09c")[0] is True
    ledger.close()

    # Workspace mutation changes the fingerprint without exposing a path in
    # the DTO; this file is synthetic evidence, not a business write.
    (workspace / "runtime" / "artifacts" / "fingerprint-change.bin").write_bytes(b"changed")
    verifier = ProjectVerifier(runtime_root, "synthetic-09c", project_dir=workspace)
    changed = verifier.snapshot_fingerprint()
    verifier.close()
    assert changed != fingerprint



def test_verifier_tampered_r1_chain_is_anomaly(tmp_path: Path) -> None:
    runtime_root, workspace = _current_project(tmp_path, "tampered-09c")
    runtime = workspace / "runtime" / "monitoring_runtime.sqlite3"
    store = Store(runtime, workspace / "artifacts")
    store.append_audit("synthetic_check", {"value": "before-tamper"})
    store.close()

    connection = sqlite3.connect(str(runtime))
    try:
        connection.execute("UPDATE audit_events SET payload_json=? WHERE seq=1", ("{}",))
        connection.commit()
    finally:
        connection.close()

    verifier = ProjectVerifier(runtime_root, "tampered-09c", project_dir=workspace)
    result = verifier.verify()
    verifier.close()
    assert result.result == RESULT_ANOMALY
    assert result.reason_enum == "r1_audit_chain_mismatch"


def test_available_publication_is_verified_and_scope_mismatch_is_anomaly(
    tmp_path: Path,
) -> None:
    project_id = "publication-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    run_id = _add_available_publication(workspace, project_id)

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    healthy = verifier.verify()
    verifier.close()
    assert healthy.result == RESULT_RECORD_COMPLETE

    connection = sqlite3.connect(str(workspace / "launch_registry.sqlite3"))
    try:
        connection.execute(
            "UPDATE r7_result_publications SET project_id=? WHERE run_id=?",
            ("other-project", run_id),
        )
        connection.commit()
    finally:
        connection.close()

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    mismatch = verifier.verify()
    verifier.close()
    assert mismatch.result == RESULT_ANOMALY
    assert mismatch.reason_enum == "publication_scope_mismatch"


def test_available_publication_missing_artifact_digest_is_anomaly(tmp_path: Path) -> None:
    project_id = "publication-anchor-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    run_id = _add_available_publication(workspace, project_id)
    connection = sqlite3.connect(str(workspace / "launch_registry.sqlite3"))
    try:
        connection.execute(
            "UPDATE r7_result_publications SET artifact_member_set_digest=NULL "
            "WHERE run_id=?",
            (run_id,),
        )
        connection.commit()
    finally:
        connection.close()

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    result = verifier.verify()
    verifier.close()
    assert result.result == RESULT_ANOMALY
    assert result.reason_enum == "publication_anchor_missing"


def test_verifier_maps_root_head_tamper_to_anomaly(tmp_path: Path) -> None:
    project_id = "root-head-tamper-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    baseline = verifier.verify()
    verifier.close()
    assert baseline.result == RESULT_RECORD_COMPLETE

    ledger = ProjectAuditLedger(runtime_root)
    try:
        ledger.connection.execute(
            "UPDATE project_audit_heads SET head_hash=? "
            "WHERE canonical_project_id=?",
            ("0" * 64, project_id),
        )
        ledger.connection.commit()
    finally:
        ledger.close()

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    result = verifier.verify()
    verifier.close()
    assert result.result == RESULT_ANOMALY
    assert result.reason_enum == "root_audit_chain_mismatch"

    ledger = ProjectAuditLedger(runtime_root)
    try:
        assert len(ledger.events(project_id)) == 2
        assert ledger.verify_chain(project_id)[0] is False
    finally:
        ledger.close()


def test_verifier_maps_root_payload_tamper_to_anomaly(tmp_path: Path) -> None:
    project_id = "root-payload-tamper-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    baseline = verifier.verify()
    verifier.close()
    assert baseline.result == RESULT_RECORD_COMPLETE

    ledger = ProjectAuditLedger(runtime_root)
    try:
        event = ledger.events(project_id)[0]
        tampered_payload = dict(event.payload)
        tampered_payload["before_digest"] = "f" * 64
        payload_json = json.dumps(
            tampered_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        ledger.connection.execute("DROP TRIGGER project_audit_events_no_update")
        ledger.connection.execute(
            "UPDATE project_audit_events SET payload_json=? "
            "WHERE canonical_project_id=? AND project_seq=?",
            (payload_json, project_id, event.project_seq),
        )
        ledger.connection.commit()
    finally:
        ledger.close()

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    result = verifier.verify()
    verifier.close()
    assert result.result == RESULT_ANOMALY
    assert result.reason_enum == "root_audit_chain_mismatch"

    ledger = ProjectAuditLedger(runtime_root)
    try:
        assert len(ledger.events(project_id)) == 2
        assert ledger.verify_chain(project_id)[0] is False
    finally:
        ledger.close()



def test_recovery_evidence_is_reported_without_cleanup(tmp_path: Path) -> None:
    runtime_root, workspace = _current_project(tmp_path, "recovery-09c")
    staging = runtime_root / ".migration-staging"
    staging.mkdir()
    marker = staging / "durable-marker"
    marker.write_text("pending", encoding="utf-8")

    verifier = ProjectVerifier(runtime_root, "recovery-09c", project_dir=workspace)
    result = verifier.verify()
    verifier.close()

    assert result.result == RESULT_RECOVERY_REQUIRED
    assert result.reason_enum == "recovery_evidence_present"
    assert marker.read_text(encoding="utf-8") == "pending"


@pytest.mark.parametrize(
    ("kind", "expected_result", "expected_reason"),
    (
        ("directory", RESULT_RECOVERY_REQUIRED, "recovery_evidence_present"),
        ("symlink", RESULT_ANOMALY, "evidence_symlink"),
        ("file", RESULT_ANOMALY, "evidence_not_directory"),
    ),
)
def test_restore_rollback_sibling_evidence_is_classified(
    tmp_path: Path,
    kind: str,
    expected_result: str,
    expected_reason: str,
) -> None:
    project_id = "rollback-scan-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    rollback = runtime_root / ".rollback-synthetic-operation"
    if kind == "directory":
        rollback.mkdir()
        (rollback / "member").write_text("retained", encoding="utf-8")
    elif kind == "symlink":
        target = tmp_path / "outside-rollback"
        target.mkdir()
        rollback.symlink_to(target)
    else:
        rollback.write_text("invalid", encoding="utf-8")

    verifier = ProjectVerifier(runtime_root, project_id, project_dir=workspace)
    result = verifier.verify()
    verifier.close()
    assert result.result == expected_result
    assert result.reason_enum == expected_reason
    assert rollback.exists() or rollback.is_symlink()



def test_boundary_retry_is_idempotent_and_updates_root_projection_atomically(
    tmp_path: Path,
) -> None:
    runtime_root, workspace = _current_project(tmp_path, "boundary-09c")
    operations = OperationLedger(runtime_root)
    operation = operations.create_or_replay("backup", "same-key", "boundary-09c")
    operations.close()

    coordinator = RecoveryCoordinator(runtime_root, "boundary-09c", project_dir=workspace)
    first = coordinator.begin_boundary(
        operation.operation_id,
        operation_kind="backup",
        expected_state=operation.status,
        before_digest="a" * 64,
        boundary_token="boundary-token",
    )
    replay = coordinator.begin_boundary(
        operation.operation_id,
        operation_kind="backup",
        expected_state=operation.status,
        before_digest="a" * 64,
        boundary_token="boundary-token",
    )
    coordinator.mark_committed(
        first,
        observed_durable_phase="available",
        after_digest="b" * 64,
        operation_update={
            "status": "available",
            "progress_percent": 100,
            "terminal_outcome": "available",
        },
    )
    coordinator.mark_verified(
        first,
        verifier_outcome=RESULT_RECORD_COMPLETE,
        after_digest="b" * 64,
    )
    coordinator.close()

    assert replay.intent_event_id == first.intent_event_id
    audit = ProjectAuditLedger(runtime_root)
    events = audit.events("boundary-09c")
    assert [event.event_kind for event in events].count("boundary_intent") == 1
    assert audit.verify_chain("boundary-09c")[0] is True
    audit.close()

    operations = OperationLedger(runtime_root)
    projection = operations.get(operation.operation_id)
    operations.close()
    assert projection.status == "available"
    assert projection.progress_percent == 100
    assert projection.terminal_outcome == "available"



def test_rollback_release_failure_retains_evidence_then_success_clears_projection(
    tmp_path: Path,
) -> None:
    runtime_root, workspace = _current_project(tmp_path, "rollback-09c")
    operations = OperationLedger(runtime_root)
    operation = operations.create_or_replay(
        "restore", "restore-key", "rollback-09c", initial_status="completed"
    )
    operations.close()
    rollback = runtime_root / "rollback-evidence"
    rollback.mkdir()
    (rollback / "member").write_text("evidence", encoding="utf-8")
    operations = OperationLedger(runtime_root)
    operations.update(operation.operation_id, rollback_path=str(rollback))
    operations.close()

    coordinator = RecoveryCoordinator(runtime_root, "rollback-09c", project_dir=workspace)
    receipt = coordinator.begin_boundary(
        operation.operation_id,
        operation_kind="restore",
        expected_state="completed",
        before_digest="a" * 64,
        boundary_token="rollback-boundary",
    )
    coordinator.mark_committed(
        receipt, observed_durable_phase="completed", after_digest="b" * 64
    )
    verified = coordinator.mark_verified(
        receipt, verifier_outcome=RESULT_RECORD_COMPLETE, after_digest="b" * 64
    )
    assert coordinator.release_rollback_evidence(
        operation.operation_id,
        verified_event_id=verified.event_id,
        rollback_digest="c" * 64,
        release=lambda: (_ for _ in ()).throw(OSError("injected")),
        operation_kind="restore",
    ) is False
    assert rollback.exists()
    assert coordinator.release_rollback_evidence(
        operation.operation_id,
        verified_event_id=verified.event_id,
        rollback_digest="c" * 64,
        release=lambda: shutil.rmtree(rollback),
        operation_kind="restore",
        operation_update={"rollback_path": ""},
    ) is True
    coordinator.close()

    assert not rollback.exists()
    operations = OperationLedger(runtime_root)
    assert operations.get(operation.operation_id).rollback_path is None
    operations.close()
    audit = ProjectAuditLedger(runtime_root)
    kinds = [event.event_kind for event in audit.events("rollback-09c")]
    assert "rollback_evidence_release_failed" in kinds
    assert "rollback_evidence_released" in kinds
    assert audit.verify_chain("rollback-09c")[0] is True
    audit.close()


def test_startup_scan_reports_only_09a_public_recovery_states(tmp_path: Path) -> None:
    project_id = "startup-recovery-09c"
    runtime_root, workspace = _current_project(tmp_path, project_id)
    operations = OperationLedger(runtime_root)
    pending = operations.create_or_replay(
        "restore",
        "pending-restore",
        project_id,
        initial_status="staging",
    )
    operations.create_or_replay(
        "restore",
        "triage-restore",
        project_id,
        initial_status="retained_for_triage",
    )
    operations.create_or_replay(
        "restore",
        "failed-restore",
        project_id,
        initial_status="failed",
    )
    operations.close()

    coordinator = RecoveryCoordinator(runtime_root, project_id, project_dir=workspace)
    recovered = coordinator.startup_recovery_scan()
    coordinator.close()
    backup_records = [
        record for record in recovered if getattr(record, "operation_kind", "") == "restore"
    ]
    assert [record.operation_id for record in backup_records] == [pending.operation_id]
    assert backup_records[0].status == "staging"



def test_product_audit_route_returns_only_minimal_dto(tmp_path: Path) -> None:
    project_id = "route-09c"
    runtime_dir = tmp_path / "runtime"
    workspace = runtime_dir / "medical_monitoring_r7" / project_id
    make_project(workspace)
    app = FastAPI()
    from services.api.app.medical_monitoring_r7_product_router import (
        create_medical_monitoring_r7_product_router,
    )

    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=runtime_dir,
            require_server_principal=False,
        )
    )
    client = TestClient(app)
    response = client.get(
        f"/api/projects/{project_id}/modules/medical-monitoring/r7/project/audit/verify"
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"result", "message", "nextAction"}
    assert body["result"] == RESULT_RECORD_COMPLETE
    assert not any(
        token in json.dumps(body, ensure_ascii=False).lower()
        for token in (
            "operation_id",
            "event_id",
            "project_seq",
            "path",
            "workspace",
            "traceback",
        )
    )


def test_product_router_startup_scans_only_canonical_project_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_root = runtime_dir / "medical_monitoring_r7"
    make_project(runtime_root / "project-a")
    make_project(runtime_root / "project-b")
    (runtime_root / ".migration-staging").mkdir()
    (runtime_root / "not-a-project").write_text("ignore", encoding="utf-8")
    calls: list[tuple[str, str]] = []

    class FakeCoordinator:
        def __init__(self, root, project_id, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("init", str(project_id)))

        def startup_recovery_scan(self):  # type: ignore[no-untyped-def]
            calls.append(("scan", calls[-1][1]))
            return ()

        def close(self) -> None:
            calls.append(("close", calls[-1][1]))

    from services.api.app import medical_monitoring_r7_product_router as product_router

    monkeypatch.setattr(product_router, "RecoveryCoordinator", FakeCoordinator)
    app = FastAPI()
    app.include_router(
        product_router.create_medical_monitoring_r7_product_router(
            runtime_dir=runtime_dir,
            require_server_principal=False,
        )
    )
    with TestClient(app):
        pass

    scanned = [project for action, project in calls if action == "scan"]
    assert sorted(set(scanned)) == ["project-a", "project-b"]
    assert scanned.count("project-a") == scanned.count("project-b")
