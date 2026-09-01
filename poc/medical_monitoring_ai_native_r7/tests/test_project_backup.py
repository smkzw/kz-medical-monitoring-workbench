"""Focused synthetic/offline tests for the R7 Slice-09A core."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import sqlite3
import zipfile
from pathlib import Path

import pytest

from mm_r1.domain import AnalysisState, ExecutionBasis, MonitoringRun, RunMode, SourceRevision
from mm_r1.store import Store
from mm_r7.profile_store import ProfileStore
from mm_r7.project_backup import (
    BACKUP_SUFFIX,
    CONTRACT_VERSION,
    OP_BACKUP,
    OP_RESTORE,
    OperationLedger,
    ProjectBackupError,
    ProjectBackupManager,
    STATUS_AVAILABLE,
    STATUS_ALREADY_CURRENT,
    STATUS_COMPLETED,
    STATUS_CONFIRMED,
    WorkspaceSnapshot,
    workspace_fingerprint,
)
from mm_r7.run_binding import RunBindingStore
from mm_r7.maintenance_gate import ProjectBusyError, ProjectMaintenanceGate


def _make_workspace(root: Path, project_id: str = "project-a") -> Path:
    workspace = root / project_id
    workspace.mkdir(parents=True)
    ProfileStore(workspace / "execution_profiles.sqlite3").close()
    RunBindingStore(workspace / "monitoring_run_bindings.sqlite3").close()
    runtime = workspace / "runtime"
    runtime.mkdir()
    store = Store(runtime / "monitoring_runtime.sqlite3", runtime / "artifacts")
    store.create_project(project_id, "合成项目 A")
    store.add_source_revision(
        SourceRevision(
            revision_id="revision-a",
            project_id=project_id,
            source_type="listing",
            version="v1",
            content_hash="source-a",
        )
    )
    store.create_run(
        MonitoringRun(
            run_id="run-a",
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="2026-08-30",
            source_revision_id="revision-a",
            execution_basis=ExecutionBasis.FULL,
        )
    )
    store.close()
    return workspace


def test_public_workspace_snapshot_and_artifact_closure_preserve_09a_identity(
    tmp_path: Path,
) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    try:
        snapshot = manager.snapshot_workspace("public-snapshot")
        assert isinstance(snapshot, WorkspaceSnapshot)
        assert snapshot.fingerprint == workspace_fingerprint(snapshot.members)
        assert snapshot.artifact_hashes == ()
        assert manager.artifact_closure() == {}
    finally:
        manager.ledger.close()


def _manager(root: Path, project_id: str = "project-a", **kwargs):
    return ProjectBackupManager(root, project_id, wait_seconds=0.2, **kwargs)


def test_backup_is_deterministic_and_uses_root_ledger(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    first = manager.backup("same-state-1")
    second = manager.backup("same-state-2")
    assert first.package_id == second.package_id
    assert first.package_path is not None
    assert first.package_path.read_bytes() == second.package_path.read_bytes()
    assert first.package_path.suffix == BACKUP_SUFFIX
    assert manager.operations_db_path.name == "backup_operations.sqlite3"
    with zipfile.ZipFile(first.package_path) as archive:
        assert archive.namelist()[0] == "manifest.json"
        assert all(name.startswith("members/") or name == "manifest.json" for name in archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["contract_version"] == CONTRACT_VERSION
        assert "package_id" not in manifest


def test_preflight_restore_switch_reopens_and_replays(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("before-change")

    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    conn.execute("UPDATE projects SET name='更新后的项目' WHERE project_id='project-a'")
    conn.commit()
    conn.close()

    preflight = manager.preflight(backup.package_path, "preflight-1")
    assert preflight.confirmation_required is True
    assert preflight.decision_label in {"可恢复", "需确认回退"}
    with pytest.raises(ProjectBackupError) as not_confirmed:
        manager.restore(backup.package_path, "restore-1", preflight_result=preflight)
    assert not_confirmed.value.code == "restore_confirmation_required"
    restored = manager.restore(
        backup.package_path,
        "restore-1",
        confirmation=True,
        preflight_result=preflight,
    )
    assert restored.operation.status == STATUS_COMPLETED
    assert (workspace / "runtime" / "monitoring_runtime.sqlite3").is_file()
    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    assert conn.execute("SELECT name FROM projects WHERE project_id='project-a'").fetchone()[0] == "合成项目 A"
    conn.close()
    replay = manager.restore(backup.package_path, "restore-1", confirmation=True)
    assert replay.operation.status == STATUS_COMPLETED
    assert replay.operation.operation_id == restored.operation.operation_id



def test_reserved_backup_operation_runs_owner_once(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    ledger = OperationLedger(tmp_path)
    reserved = ledger.create_or_replay(
        OP_BACKUP,
        "reserved-backup",
        "project-a",
    )
    ledger.close()

    manager = _manager(tmp_path)
    result = manager.backup(
        "reserved-backup",
        reserved_operation_id=reserved.operation_id,
    )
    assert result.operation.status == STATUS_AVAILABLE
    replay = manager.backup("reserved-backup")
    assert replay.operation.operation_id == reserved.operation_id
    assert replay.operation.status == STATUS_AVAILABLE


def test_reserved_restore_operation_runs_owner_once(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("reserved-restore-source")
    assert backup.package_id is not None

    ledger = OperationLedger(tmp_path)
    reserved = ledger.create_or_replay(
        OP_RESTORE,
        "reserved-restore",
        "project-a",
        package_id=backup.package_id,
        initial_status=STATUS_CONFIRMED,
    )
    ledger.close()

    restored = manager.restore(
        backup.package_path,
        "reserved-restore",
        confirmation=True,
        reserved_operation_id=reserved.operation_id,
    )
    assert restored.operation.status == STATUS_ALREADY_CURRENT
    replay = manager.restore(
        backup.package_path,
        "reserved-restore",
        confirmation=True,
    )
    assert replay.operation.operation_id == reserved.operation_id
    assert replay.operation.status == STATUS_ALREADY_CURRENT

def test_corrupt_member_and_unknown_workspace_fail_closed(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("corruption-source")
    assert backup.package_path is not None
    broken = tmp_path / "broken.mmbackup"
    with zipfile.ZipFile(backup.package_path) as source, zipfile.ZipFile(broken, "w", compression=zipfile.ZIP_STORED) as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "members/execution_profiles.sqlite3":
                data = data + b"tamper"
            target.writestr(info, data)
    with pytest.raises(ProjectBackupError) as corrupt:
        manager.preflight(broken, "corrupt-preflight")
    assert corrupt.value.code in {"package_corrupt", "manifest_semantic_mismatch"}

    (tmp_path / "project-a" / "unexpected.txt").write_text("reject", encoding="utf-8")
    with pytest.raises(ProjectBackupError) as unknown:
        manager.backup("unknown-workspace")
    assert unknown.value.code == "workspace_unknown_member"


def _hold_shared(root: str, project_id: str, ready, release) -> None:
    gate = ProjectMaintenanceGate(root, project_id, wait_seconds=1)
    with gate.shared():
        ready.set()
        release.wait(3)


def test_exclusive_restore_gate_waits_and_times_out(tmp_path: Path) -> None:
    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    process = multiprocessing.Process(target=_hold_shared, args=(str(tmp_path), "project-a", ready, release))
    process.start()
    assert ready.wait(3)
    gate = ProjectMaintenanceGate(tmp_path, "project-a", wait_seconds=0.05)
    with pytest.raises(ProjectBusyError) as busy:
        gate.exclusive()
    assert busy.value.code == "project_busy_retry_later"
    release.set()
    process.join(3)
    assert process.exitcode == 0


def test_same_key_different_state_is_conflict(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    first = manager.backup("stable-key")
    assert first.operation.status == STATUS_AVAILABLE
    (tmp_path / "project-a" / "extra.sqlite3").touch()
    with pytest.raises(ProjectBackupError) as conflict:
        manager.backup("stable-key")
    assert conflict.value.code in {"backup_operation_conflict", "workspace_unknown_member"}
    record = OperationLedger(tmp_path).get(first.operation_id)
    assert record.status == STATUS_AVAILABLE


def test_artifact_orphan_is_rejected_and_manual_rollback_reopens(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    orphan = workspace / "runtime" / "artifacts" / ("a" * 64 + ".json")
    orphan.write_text("orphan", encoding="utf-8")
    with pytest.raises(ProjectBackupError) as orphan_error:
        manager.backup("orphan-source")
    assert orphan_error.value.code == "artifact_closure_invalid"
    orphan.unlink()

    original = manager.backup("original")
    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    conn.execute("UPDATE projects SET name='较新项目' WHERE project_id='project-a'")
    conn.commit()
    conn.close()
    newer = manager.backup("newer")
    preflight = manager.preflight(original.package_path, "old-preflight")
    restored = manager.restore(
        original.package_path,
        "old-restore",
        confirmation=True,
        preflight_result=preflight,
    )
    assert restored.operation.status == STATUS_COMPLETED
    rolled_back = manager.rollback(restored)
    assert rolled_back.operation.status == STATUS_COMPLETED
    assert newer.package_id is not None
    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    assert conn.execute("SELECT name FROM projects WHERE project_id='project-a'").fetchone()[0] == "较新项目"
    conn.close()


def test_audit_chain_corruption_is_rejected(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    runtime_db = tmp_path / "project-a" / "runtime" / "monitoring_runtime.sqlite3"
    conn = sqlite3.connect(str(runtime_db))
    conn.execute(
        "UPDATE audit_chain_head SET last_chain_hash=? WHERE singleton=1",
        ("0" * 64,),
    )
    conn.commit()
    conn.close()
    with pytest.raises(ProjectBackupError) as corruption:
        manager.backup("audit-corruption")
    assert corruption.value.code == "sqlite_integrity_failed"


def test_failure_hooks_leave_a_complete_live_workspace(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    points = []

    def fail_publish(point: str) -> None:
        points.append(point)
        if point == "backup.package_publish.before":
            raise RuntimeError("injected")

    manager.set_failure_hook(fail_publish)
    with pytest.raises(ProjectBackupError) as backup_error:
        manager.backup("publish-fault")
    assert backup_error.value.code == "injected_failure"
    assert "backup.package_publish.before" in points
    assert workspace.is_dir()
    manager.set_failure_hook(None)
    backup = manager.backup("restore-source")
    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    conn.execute("UPDATE projects SET name='待回退版本' WHERE project_id='project-a'")
    conn.commit()
    conn.close()
    preflight = manager.preflight(backup.package_path, "restore-fault-preflight")

    def fail_switch(point: str) -> None:
        if point == "restore.staging_to_live.before":
            raise RuntimeError("injected")

    manager.set_failure_hook(fail_switch)
    with pytest.raises(ProjectBackupError) as restore_error:
        manager.restore(
            backup.package_path,
            "restore-fault",
            confirmation=True,
            preflight_result=preflight,
        )
    assert restore_error.value.code == "injected_failure"
    manager.set_failure_hook(None)
    conn = sqlite3.connect(str(workspace / "runtime" / "monitoring_runtime.sqlite3"))
    assert conn.execute("SELECT name FROM projects WHERE project_id='project-a'").fetchone()[0] == "待回退版本"
    conn.close()
