"""Synthetic/offline R7 Slice-09B staged migration tests."""

from __future__ import annotations

import hashlib
import errno
import sqlite3
from pathlib import Path

import pytest
import mm_r7.migration as migration_module

from fixtures_schema_manifest import make_project
from mm_r7.migration import (
    MIGRATION_ROLLBACK_DIR_NAME,
    MIGRATION_STAGING_DIR_NAME,
    MigrationError,
    MigrationRunner,
    STATUS_COMPLETED,
    STATUS_LIVE_VERIFYING,
    STATUS_MIGRATION_OPERATION_CONFLICT,
    STATUS_RETAINED_FOR_TRIAGE,
    STATUS_RETRYABLE_FAILED,
    STATUS_ROLLED_BACK,
)
from mm_r7.project_backup import ProjectBackupManager
from mm_r7.schema_manifest import LAUNCH_V1, LAUNCH_V2, LAUNCH_V3, RUNTIME_V4


def _workspace_digest(workspace: Path) -> str:
    names = []
    for path in sorted(workspace.rglob("*"), key=lambda item: str(item.relative_to(workspace))):
        if not path.is_file() or path.name.endswith(("-wal", "-shm", "-journal")):
            continue
        relative = str(path.relative_to(workspace)).replace("\\", "/")
        payload = path.read_bytes()
        names.append((relative, hashlib.sha256(payload).hexdigest()))
    return hashlib.sha256(repr(names).encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"runtime_version": RUNTIME_V4},
        {"runtime_version": "5"},
        {"launch_version": LAUNCH_V1},
        {"launch_version": LAUNCH_V2},
        {"launch_version": LAUNCH_V3},
    ],
)
def test_supported_legacy_migration_is_sibling_staged_and_current(
    tmp_path: Path, kwargs: dict[str, str]
) -> None:
    project = make_project(tmp_path / "project", **kwargs)
    runner = MigrationRunner(tmp_path, "project")
    try:
        result = runner.start_upgrade("upgrade-1")
        assert result.state == STATUS_COMPLETED
        assert result.requires_reopen is True
        assert runner.inspect().classification.value == "current"
        assert not list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/workspace"))
        assert not list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/project-upgrade-1"))
        for path in project.rglob("*"):
            assert not path.name.endswith(("-wal", "-shm"))
    finally:
        runner.close()


def test_readonly_legacy_start_does_not_change_project_bytes(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", runtime_version="5")
    before = _workspace_digest(project)
    runner = MigrationRunner(tmp_path, "project")
    try:
        result = runner.start_upgrade("upgrade-1", confirmation=False)
        assert result.state == "legacy_readonly"
        assert result.operation is None
        assert _workspace_digest(project) == before
    finally:
        runner.close()


def test_marker_failure_rolls_back_staging_step_and_same_key_replays(
    tmp_path: Path,
) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    fired = False

    def fail_once(point: str) -> None:
        nonlocal fired
        if point == "migration.runtime.marker.before" and not fired:
            fired = True
            raise RuntimeError("injected marker fault")

    runner = MigrationRunner(tmp_path, "project", failure_hook=fail_once)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        assert runner.ledger.list_for_project("project")[-1].status == STATUS_RETRYABLE_FAILED
        assert list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/workspace"))
    finally:
        runner.close()

    retry = MigrationRunner(tmp_path, "project")
    try:
        assert retry.start_upgrade("upgrade-1").state == STATUS_COMPLETED
        assert retry.inspect().members["runtime"].schema_version == "6"
    finally:
        retry.close()


def test_commit_after_failure_is_recovered_without_repeating_step(tmp_path: Path) -> None:
    make_project(tmp_path / "project", runtime_version="5")

    def crash(point: str) -> None:
        if point == "migration.runtime.commit.after":
            raise RuntimeError("simulated crash")

    runner = MigrationRunner(tmp_path, "project", failure_hook=crash)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        assert runner.inspect().members["runtime"].schema_version == "5"
        record = runner.ledger.list_for_project("project")[0]
        assert record.status == "migrating"
    finally:
        runner.close()

    retry = MigrationRunner(tmp_path, "project")
    try:
        result = retry.start_upgrade("upgrade-1")
        assert result.state == STATUS_COMPLETED
        assert retry.inspect().members["runtime"].schema_version == "6"
    finally:
        retry.close()


@pytest.mark.parametrize(
    "point",
    ["migration.switch.live_to_rollback.after", "migration.switch.staging_to_live.before"],
)
def test_switch_failure_restores_one_complete_live_workspace(
    tmp_path: Path, point: str
) -> None:
    make_project(tmp_path / "project", runtime_version="5")

    def fail(target: str) -> None:
        if target == point:
            raise RuntimeError(target)

    runner = MigrationRunner(tmp_path, "project", failure_hook=fail)
    try:
        result = runner.start_upgrade("upgrade-1")
        assert result.state == STATUS_ROLLED_BACK
        assert runner.inspect().members["runtime"].schema_version == "5"
        records = runner.ledger.list_for_project("project")
        assert records[-1].status == STATUS_ROLLED_BACK
    finally:
        runner.close()


def test_rollback_failure_retains_directories_and_blocks_replay(tmp_path: Path) -> None:
    make_project(tmp_path / "project", runtime_version="5")

    def fail(point: str) -> None:
        if point in {
            "migration.switch.staging_to_live.after",
            "migration.rollback.before",
        }:
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=fail)
    try:
        with pytest.raises(MigrationError) as exc_info:
            runner.start_upgrade("upgrade-1")
        assert exc_info.value.code == "migration_rollback_failed"
        record = runner.ledger.list_for_project("project")[-1]
        assert record.status == STATUS_RETAINED_FOR_TRIAGE
        assert list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/"))
        assert list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
        with pytest.raises(MigrationError) as replay_error:
            runner.start_upgrade("upgrade-1")
        assert replay_error.value.code == "migration_rollback_failed"
        with pytest.raises(MigrationError) as new_operation_error:
            runner.start_upgrade("upgrade-2")
        assert new_operation_error.value.code == "migration_rollback_failed"
        with pytest.raises(MigrationError) as open_error:
            runner.open_project()
        assert open_error.value.code == "migration_rollback_failed"
    finally:
        runner.close()


def test_source_drift_same_key_conflicts_without_second_operation(tmp_path: Path) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    fired = False

    def stop_before_switch(point: str) -> None:
        nonlocal fired
        if point == "migration.runtime.marker.before" and not fired:
            fired = True
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=stop_before_switch)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        runtime = tmp_path / "project" / "runtime" / "monitoring_runtime.sqlite3"
        connection = sqlite3.connect(runtime)
        connection.execute("UPDATE meta SET value='drifted-store' WHERE key='store_id'")
        connection.commit()
        connection.close()
        # The non-marker store identity above is synthetic source drift;
        # same-key replay must not silently create a replacement backup.
        with pytest.raises(MigrationError) as conflict:
            runner.start_upgrade("upgrade-1")
        assert conflict.value.code == STATUS_MIGRATION_OPERATION_CONFLICT
        assert len(runner.ledger.list_for_project("project")) == 1
    finally:
        runner.close()


def test_directory_switch_crash_after_old_rename_recovers_to_rollback(
    tmp_path: Path,
) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    runner: MigrationRunner

    def crash(point: str) -> None:
        if point != "migration.ledger_commit.after":
            return
        records = runner.ledger.list_for_project("project")
        if records and records[-1].directory_switch_stage == "live_to_rollback":
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=crash)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        assert not (tmp_path / "project").exists()
        assert list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
    finally:
        runner.close()

    retry = MigrationRunner(tmp_path, "project")
    try:
        result = retry.start_upgrade("upgrade-1")
        assert result.state == STATUS_ROLLED_BACK
        assert retry.inspect().members["runtime"].schema_version == "5"
        assert retry.start_upgrade("upgrade-2").state == STATUS_COMPLETED
    finally:
        retry.close()


def test_directory_switch_crash_after_new_rename_recovers_to_completion(
    tmp_path: Path,
) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    runner: MigrationRunner

    def crash(point: str) -> None:
        if point != "migration.ledger_commit.after":
            return
        records = runner.ledger.list_for_project("project")
        if records and records[-1].directory_switch_stage == "staging_to_live":
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=crash)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        assert runner.inspect().members["runtime"].schema_version == "6"
        assert list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
    finally:
        runner.close()

    retry = MigrationRunner(tmp_path, "project")
    try:
        opened = retry.open_project()
        assert opened.classification.value == "current"
        assert retry.ledger.list_for_project("project")[0].status == STATUS_COMPLETED
        assert retry.inspect().classification.value == "current"
        assert not list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
    finally:
        retry.close()


def test_cross_filesystem_switch_failure_is_typed_and_restores_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    original_replace = migration_module.os.replace

    def fail_stage_switch(source: str, destination: str) -> None:
        source_path = Path(source)
        if (
            source_path.name == "workspace"
            and source_path.parent.parent.name == MIGRATION_STAGING_DIR_NAME
        ):
            raise OSError(errno.EXDEV, "synthetic cross-device rename")
        original_replace(source, destination)

    monkeypatch.setattr(migration_module.os, "replace", fail_stage_switch)
    runner = MigrationRunner(tmp_path, "project")
    try:
        result = runner.start_upgrade("upgrade-1")
        assert result.state == STATUS_ROLLED_BACK
        assert (
            runner.ledger.list_for_project("project")[-1].error_code
            == "cross_filesystem_staging_not_supported"
        )
        assert runner.inspect().members["runtime"].schema_version == "5"
    finally:
        runner.close()


def test_completed_ledger_crash_cleans_switch_evidence_on_replay(tmp_path: Path) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    runner: MigrationRunner

    def crash_after_terminal_commit(point: str) -> None:
        if point != "migration.ledger_commit.after":
            return
        records = runner.ledger.list_for_project("project")
        if records and records[-1].status == STATUS_COMPLETED:
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=crash_after_terminal_commit)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
        assert runner.inspect().classification.value == "current"
        assert list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
        assert list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/"))
    finally:
        runner.close()

    retry = MigrationRunner(tmp_path, "project")
    try:
        result = retry.start_upgrade("upgrade-1")
        assert result.state == STATUS_COMPLETED
        assert not list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
        assert not list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/"))
    finally:
        retry.close()

def test_recovery_scan_entry_resumes_interrupted_staging_operation(
    tmp_path: Path,
) -> None:
    make_project(tmp_path / "project", runtime_version="5")

    def crash_after_step_commit(point: str) -> None:
        if point == "migration.runtime.commit.after":
            raise RuntimeError(point)

    runner = MigrationRunner(tmp_path, "project", failure_hook=crash_after_step_commit)
    try:
        with pytest.raises(MigrationError):
            runner.start_upgrade("upgrade-1")
    finally:
        runner.close()

    recovery = MigrationRunner(tmp_path, "project")
    try:
        results = recovery.recover()
        assert len(results) == 1
        assert results[0].state == STATUS_COMPLETED
        assert recovery.inspect().classification.value == "current"
    finally:
        recovery.close()


@pytest.mark.parametrize(
    "recovery_entrypoint",
    (
        "recover",
        "recover_operation",
        "recover_pending",
        "startup_recovery_scan",
        "open_project",
        "start_upgrade",
    ),
)
def test_live_verifying_crash_recovers_through_each_fresh_entrypoint(
    tmp_path: Path,
    recovery_entrypoint: str,
) -> None:
    project = make_project(tmp_path / "project", runtime_version="5")
    runtime = project / "runtime" / "monitoring_runtime.sqlite3"
    connection = sqlite3.connect(runtime)
    try:
        connection.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
            ("live_verifying_sentinel", "sentinel-v1"),
        )
        connection.commit()
        source_audit_count = int(
            connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        )
    finally:
        connection.close()

    source_probe = ProjectBackupManager(tmp_path, "project")
    try:
        source_fingerprint = source_probe.snapshot_workspace("source-before").fingerprint
    finally:
        source_probe.ledger.close()

    fired = False
    seen_points: list[str] = []
    runner: MigrationRunner

    def crash_after_live_verifying(point: str) -> None:
        nonlocal fired
        seen_points.append(point)
        if point != "migration.ledger_commit.after" or fired:
            return
        records = runner.ledger.list_for_project("project")
        if records and records[-1].status == STATUS_LIVE_VERIFYING:
            fired = True
            raise RuntimeError(point)

    runner = MigrationRunner(
        tmp_path,
        "project",
        failure_hook=crash_after_live_verifying,
    )
    try:
        with pytest.raises(MigrationError) as injected:
            runner.start_upgrade("upgrade-1")
        assert injected.value.code == "injected_failure"
        assert fired
        assert "migration.ledger_commit.after" in seen_points
        interrupted = runner.ledger.list_for_project("project")
        assert len(interrupted) == 1
        record = interrupted[0]
        assert record.status == STATUS_LIVE_VERIFYING
        assert record.directory_switch_stage == "staging_to_live"
        assert record.source_workspace_fingerprint == source_fingerprint
        assert project.is_dir()
        assert record.rollback_path is not None
        assert Path(record.rollback_path).is_dir()
        assert record.staging_path is not None
        assert not (Path(record.staging_path) / "workspace").exists()
        assert runner.inspect().classification.value == "current"
    finally:
        runner.close()

    recovery = MigrationRunner(tmp_path, "project")
    try:
        if recovery_entrypoint == "recover":
            recovered = recovery.recover()
            assert len(recovered) == 1
            observed_state = recovered[0].state
        elif recovery_entrypoint == "recover_operation":
            recovered = recovery.recover(record.operation_id)
            assert len(recovered) == 1
            observed_state = recovered[0].state
        elif recovery_entrypoint in {"recover_pending", "startup_recovery_scan"}:
            recovered = getattr(recovery, recovery_entrypoint)()
            assert len(recovered) == 1
            observed_state = recovered[0].state
        elif recovery_entrypoint == "open_project":
            opened = recovery.open_project()
            assert opened.classification.value == "current"
            observed_state = recovery.ledger.get(record.operation_id).status
        else:
            observed_state = recovery.start_upgrade("upgrade-1").state

        assert observed_state in {STATUS_COMPLETED, STATUS_RETAINED_FOR_TRIAGE}
        final_records = recovery.ledger.list_for_project("project")
        assert len(final_records) == 1
        final_record = final_records[0]
        assert final_record.status == observed_state
        assert final_record.source_workspace_fingerprint == source_fingerprint
        assert final_record.canonical_project_id == "project"
        assert recovery.inspect().classification.value == "current"
        assert project.is_dir()
        connection = sqlite3.connect(runtime)
        try:
            assert connection.execute(
                "SELECT value FROM meta WHERE key=?",
                ("live_verifying_sentinel",),
            ).fetchone() == ("sentinel-v1",)
            assert int(
                connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
            ) == source_audit_count
        finally:
            connection.close()
        if observed_state == STATUS_COMPLETED:
            assert final_record.directory_switch_stage == "verified"
            assert not list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
            assert not list((tmp_path / MIGRATION_STAGING_DIR_NAME).glob("*/"))
        else:
            assert final_record.directory_switch_stage == "retained_for_triage"
            assert list((tmp_path / MIGRATION_ROLLBACK_DIR_NAME).glob("*/"))
    finally:
        recovery.close()

def test_late_ledger_callback_is_fenced_by_plan_and_state(tmp_path: Path) -> None:
    make_project(tmp_path / "project", runtime_version="5")
    runner = MigrationRunner(tmp_path, "project")
    try:
        result = runner.start_upgrade("upgrade-1")
        assert result.operation is not None
        operation = result.operation
        assert operation.plan_digest is not None
        with pytest.raises(MigrationError) as conflict:
            runner.apply_callback(
                operation.operation_id,
                plan_digest=operation.plan_digest,
                expected_state="migrating",
                status=STATUS_ROLLED_BACK,
            )
        assert conflict.value.code == STATUS_MIGRATION_OPERATION_CONFLICT
        assert runner.ledger.get(operation.operation_id).status == STATUS_COMPLETED
    finally:
        runner.close()
...
