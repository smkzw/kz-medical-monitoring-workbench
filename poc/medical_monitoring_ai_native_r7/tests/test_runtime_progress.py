"""Slice-04 offline tests for the R7 durable progress adapter.

These tests use only temporary R7/R1 SQLite stores and direct Store callbacks.
They do not start a service, invoke a model, execute a real project, or touch
the frontend / medical-writing trees.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping

import pytest

from mm_r7.run_entry import MonitoringRunEntry
from mm_r7.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
    RuntimeProgressError,
)
from mm_r1.domain import IdempotencyConflictError, NodeStatus, StaleCallbackError
from mm_r1.store import Store


PROJECT_ID = "r7-slice04-project"
RUN_ID = "r7-slice04-run"


def _units(prefix: str = "u") -> list[dict[str, Any]]:
    return [
        {
            "work_unit_id": f"{prefix}-1",
            "stage": "资料准备",
            "label": "核对合成研究资料清单",
            "scope": "source",
            "target_ref": "SYN-DOC-1",
            "ordinal": 1,
            "mandatory": True,
            "depends_on": [],
        },
        {
            "work_unit_id": f"{prefix}-2",
            "stage": "数据解构",
            "label": "整理受试者访视数据",
            "scope": "subject",
            "target_ref": "SYN-001",
            "ordinal": 2,
            "mandatory": True,
            "depends_on": [f"{prefix}-1"],
        },
        {
            "work_unit_id": f"{prefix}-3",
            "stage": "风险分析",
            "label": "分析受试者安全性记录",
            "scope": "risk_domain",
            "target_ref": "SYN-001/AE",
            "ordinal": 3,
            "mandatory": False,
            "depends_on": [f"{prefix}-2"],
        },
    ]


def _flat_units(prefix: str = "u", count: int = 8) -> list[dict[str, Any]]:
    stages = (
        "资料准备",
        "数据解构",
        "风险分析",
        "质量检查",
        "结果汇总",
        "核查准备",
        "医学复核",
        "范围确认",
    )
    scopes = (
        "source",
        "subject",
        "risk_domain",
        "qc",
        "project",
        "document",
        "report_section",
        "site",
    )
    return [
        {
            "work_unit_id": f"{prefix}-{index}",
            "stage": stages[index - 1],
            "label": f"完成合成监查第{index}项",
            "scope": scopes[index - 1],
            "target_ref": f"SYN-{index:03d}",
            "ordinal": index,
            "mandatory": True,
            "depends_on": [],
        }
        for index in range(1, count + 1)
    ]


def _bind(
    workspace: Path,
    *,
    run_id: str = RUN_ID,
    project_id: str = PROJECT_ID,
    mode: str = "daily",
    execution_basis: str = "full",
    data_cutoff: str = "2026-08-28",
    source_revision_id: str | None = None,
) -> None:
    entry = MonitoringRunEntry(workspace)
    try:
        entry.bootstrap_workspace()
        entry.bind_run(
            run_id=run_id,
            project_id=project_id,
            mode=mode,
            execution_basis=execution_basis,
            data_cutoff=data_cutoff,
            source_revision_id=source_revision_id or f"source-{run_id}",
            prior_accepted_snapshot_ref=(
                "snapshot-synthetic-1" if execution_basis == "incremental" else None
            ),
        )
    finally:
        entry.close()


def _adapter(workspace: Path, project_id: str = PROJECT_ID) -> RuntimeProgressAdapter:
    return RuntimeProgressAdapter(workspace, canonical_project_id=project_id)


def _prepare(
    workspace: Path,
    *,
    units: list[dict[str, Any]] | None = None,
    run_id: str = RUN_ID,
    project_id: str = PROJECT_ID,
    mode: str = "daily",
) -> tuple[RuntimeProgressAdapter, dict[str, Any]]:
    _bind(workspace, run_id=run_id, project_id=project_id, mode=mode)
    adapter = _adapter(workspace, project_id)
    return adapter, adapter.prepare(run_id, units or _units())


def _public_texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _public_texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _public_texts(item)]
    return []


def _assert_public_clean(payload: Mapping[str, Any]) -> None:
    forbidden = (
        "run_id",
        "node_id",
        "work_unit_id",
        "attempt_id",
        "manifest_revision",
        "provider",
        "model",
        "selector",
        "adapter",
        "harness",
        "backend",
        "binding",
        "audit",
        "sqlite",
        "database",
        "正式事实",
        "候选信号",
        "只读",
    )
    for key in payload:
        assert str(key).casefold() not in forbidden
    text = "\n".join(_public_texts(payload)).casefold()
    for token in forbidden:
        assert token.casefold() not in text


_BUSINESS_TABLES = (
    "projects",
    "source_revisions",
    "monitoring_runs",
    "run_manifests",
    "work_unit_runs",
    "manifest_node_progress",
    "node_runs",
    "node_attempts",
    "capability_attempt_journal",
    "work_unit_capability_attempts",
    "artifacts",
    "audit_events",
    "audit_chain_head",
    "checkpoints",
    "domain_objects",
    "idempotency_ledger",
)


def _db_snapshot(path: Path) -> dict[str, tuple[tuple[Any, ...], ...]]:
    uri = f"file:{path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        return {
            table: tuple(
                tuple(row)
                for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")
            )
            for table in _BUSINESS_TABLES
        }
    finally:
        connection.close()


def _artifact_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_invalid_work_units_fail_before_runtime_creation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _bind(workspace)
    base = _units()
    invalid = []

    invalid.append([])
    invalid.append([{**base[0], "unexpected": True}])
    invalid.append([base[0], {**base[1], "work_unit_id": base[0]["work_unit_id"]}])
    invalid.append([base[0], {**base[1], "ordinal": base[0]["ordinal"]}])
    invalid.append([{**base[0], "depends_on": ["missing-unit"]}])
    invalid.append(
        [
            {**base[0], "depends_on": [base[1]["work_unit_id"]]},
            {**base[1], "depends_on": [base[0]["work_unit_id"]]},
            base[2],
        ]
    )
    invalid.append([{**base[0], "stage": "Preparation"}])
    invalid.append([{**base[0], "label": "Prepare synthetic data"}])

    adapter = _adapter(workspace)
    for payload in invalid:
        with pytest.raises(RuntimeProgressError) as raised:
            adapter.prepare(RUN_ID, payload)
        assert raised.value.code == "invalid_work_units"
        assert not (workspace / RUNTIME_DIR_NAME).exists()


@pytest.mark.parametrize(
    ("mode", "mode_text"),
    (
        ("daily", "日常监查"),
        ("pre_lock", "锁库前监查"),
        ("post_lock_pre_cfdi", "核查前监查"),
    ),
)
def test_first_prepare_is_pending_and_publicly_wrapped(
    tmp_path: Path, mode: str, mode_text: str
) -> None:
    workspace = tmp_path / mode
    adapter, first = _prepare(workspace, mode=mode)

    assert set(first) == {
        "replayed",
        "scope_version_text",
        "total",
        "data_cutoff_text",
        "mode_text",
        "basis_text",
    }
    assert first == {
        "replayed": False,
        "scope_version_text": "第 1 版监查范围",
        "total": 3,
        "data_cutoff_text": "2026-08-28",
        "mode_text": mode_text,
        "basis_text": "全量",
    }
    _assert_public_clean(first)

    runtime = workspace / RUNTIME_DIR_NAME
    assert (runtime / RUNTIME_DB_NAME).is_file()
    assert (runtime / ARTIFACT_DIR_NAME).is_dir()
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        run = store.get_run(RUN_ID)
        assert run.manifest_revision == 1
        assert store.list_manifest_revisions(RUN_ID) == [1]
        assert all(
            row.status is NodeStatus.PENDING
            for row in store.list_work_unit_runs(RUN_ID, 1)
        )

    replay = adapter.prepare(RUN_ID, _units())
    assert replay == {**first, "replayed": True}
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        assert store.list_manifest_revisions(RUN_ID) == [1]
        assert len(store.list_work_unit_runs(RUN_ID, 1)) == 3


@pytest.mark.parametrize("mode", ["daily", "pre_lock"])
def test_daily_and_pre_lock_append_new_scope_and_reject_a_to_b_to_a(
    tmp_path: Path, mode: str
) -> None:
    workspace = tmp_path / mode
    adapter, first = _prepare(workspace, mode=mode)
    second = adapter.prepare(RUN_ID, _units("b"))

    assert first["scope_version_text"] == "第 1 版监查范围"
    assert second["scope_version_text"] == "第 2 版监查范围"
    assert second["replayed"] is False
    with pytest.raises(RuntimeProgressError) as raised:
        adapter.prepare(RUN_ID, _units())
    assert raised.value.code == "superseded_scope_replay_forbidden"

    with Store(
        workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME,
    ) as store:
        assert store.list_manifest_revisions(RUN_ID) == [1, 2]
        assert store.get_run(RUN_ID).manifest_revision == 2
        assert all(
            row.status is NodeStatus.PENDING
            for row in store.list_work_unit_runs(RUN_ID, 2)
        )


def test_post_lock_scope_is_frozen_after_first_prepare(tmp_path: Path) -> None:
    workspace = tmp_path / "post-lock"
    adapter, first = _prepare(workspace, mode="post_lock_pre_cfdi")
    replay = adapter.prepare(RUN_ID, _units())
    assert replay["replayed"] is True
    assert replay["scope_version_text"] == first["scope_version_text"]

    with pytest.raises(RuntimeProgressError) as raised:
        adapter.prepare(RUN_ID, _units("changed"))
    assert raised.value.code == "frozen_scope_revision_forbidden"


def test_all_authoritative_statuses_project_to_chinese_progress(tmp_path: Path) -> None:
    workspace = tmp_path / "status-matrix"
    units = _flat_units()
    adapter, _ = _prepare(workspace, units=units)
    statuses = {
        "u-1": NodeStatus.PENDING,
        "u-2": NodeStatus.RUNNING,
        "u-3": NodeStatus.PASSED,
        "u-4": NodeStatus.REUSED,
        "u-5": NodeStatus.SKIPPED,
        "u-6": NodeStatus.NOT_APPLICABLE,
        "u-7": NodeStatus.BLOCKED,
        "u-8": NodeStatus.FAILED,
    }
    runtime = workspace / RUNTIME_DIR_NAME
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        for unit_id, status in statuses.items():
            if status is NodeStatus.PENDING:
                continue
            key = f"slice04:{unit_id}"
            store.begin_work_unit(
                RUN_ID,
                unit_id,
                key,
                "正在处理合成监查工作",
            )
            if status is not NodeStatus.RUNNING:
                store.complete_work_unit(
                    RUN_ID,
                    unit_id,
                    key,
                    status,
                    "已记录合成监查结果",
                )

    view = adapter.progress(RUN_ID)
    _assert_public_clean(view)
    assert view["completed"] == 6
    assert view["total"] == 8
    assert view["percent"] == 75.0
    assert view["headline"] == "医学监查进行中"
    assert {
        item["state_label"]: item["count"] for item in view["status_overview"]
    } == {
        "等待开始": 1,
        "进行中": 1,
        "已完成": 1,
        "已沿用已有结果": 1,
        "本次无需处理": 1,
        "本研究不适用": 1,
        "暂时受阻": 1,
        "未完成": 1,
    }
    assert {
        item["stage"]: (item["processed"], item["total"])
        for item in view["stage_progress"]
    } == {
        unit["stage"]: (int(statuses[unit["work_unit_id"]] in {
            NodeStatus.PASSED,
            NodeStatus.REUSED,
            NodeStatus.SKIPPED,
            NodeStatus.NOT_APPLICABLE,
            NodeStatus.BLOCKED,
            NodeStatus.FAILED,
        }), 1)
        for unit in units
    }
    assert len(view["current_work"]) == 1
    assert view["current_work"][0]["state_label"] == "进行中"
    assert {item["state_label"] for item in view["latest_updates"]} >= {
        "进行中",
        "已完成",
        "已沿用已有结果",
        "本次无需处理",
        "本研究不适用",
        "暂时受阻",
        "未完成",
    }


def test_prepared_get_rebuilds_without_business_or_artifact_writes(tmp_path: Path) -> None:
    workspace = tmp_path / "read-only"
    adapter, _ = _prepare(workspace)
    runtime = workspace / RUNTIME_DIR_NAME
    before_db = _db_snapshot(runtime / RUNTIME_DB_NAME)
    before_artifacts = _artifact_snapshot(runtime / ARTIFACT_DIR_NAME)

    first = adapter.progress(RUN_ID)
    second = adapter.progress(RUN_ID)

    assert first == second
    assert _db_snapshot(runtime / RUNTIME_DB_NAME) == before_db
    assert _artifact_snapshot(runtime / ARTIFACT_DIR_NAME) == before_artifacts


def test_unprepared_and_unbound_paths_have_zero_runtime_io(tmp_path: Path) -> None:
    workspace = tmp_path / "zero-io"
    _bind(workspace)
    adapter = _adapter(workspace)
    with pytest.raises(RuntimeProgressError) as unprepared:
        adapter.progress(RUN_ID)
    assert unprepared.value.code == "execution_not_prepared"
    assert not (workspace / RUNTIME_DIR_NAME).exists()

    unbound_workspace = tmp_path / "unbound"
    entry = MonitoringRunEntry(unbound_workspace)
    try:
        entry.bootstrap_workspace()
    finally:
        entry.close()
    unbound = _adapter(unbound_workspace)
    with pytest.raises(RuntimeProgressError) as missing:
        unbound.prepare("run-not-bound", _units())
    assert missing.value.code == "run_binding_not_found"
    assert not (unbound_workspace / RUNTIME_DIR_NAME).exists()


def test_existing_identity_mismatch_fails_before_set_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "identity-mismatch"
    adapter, _ = _prepare(workspace)
    runtime = workspace / RUNTIME_DIR_NAME
    binding_source = f"source-{RUN_ID}"
    with sqlite3.connect(runtime / RUNTIME_DB_NAME) as connection:
        connection.execute(
            "UPDATE source_revisions SET version=? WHERE revision_id=?",
            ("tampered-version", binding_source),
        )

    calls: list[bool] = []
    original = Store.set_manifest

    def tracked_set_manifest(self: Store, *args: Any, **kwargs: Any) -> int:
        calls.append(True)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Store, "set_manifest", tracked_set_manifest)
    with pytest.raises(RuntimeProgressError) as raised:
        adapter.prepare(RUN_ID, _units("new"))
    assert raised.value.code == "runtime_identity_mismatch"
    assert calls == []


def test_old_revision_callbacks_are_rejected_by_r1_store(tmp_path: Path) -> None:
    workspace = tmp_path / "stale-callback"
    adapter, _ = _prepare(workspace, units=_units("a"))
    adapter.prepare(RUN_ID, _units("b"))
    runtime = workspace / RUNTIME_DIR_NAME
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        with pytest.raises(StaleCallbackError):
            store.begin_work_unit(
                RUN_ID,
                "a-1",
                "stale-begin",
                "开始处理旧版工作",
                manifest_revision=1,
            )
        with pytest.raises(StaleCallbackError):
            store.complete_work_unit(
                RUN_ID,
                "a-1",
                "stale-begin",
                NodeStatus.PASSED,
                "完成旧版工作",
                manifest_revision=1,
            )


def test_current_revision_conflicting_callback_is_rejected_by_r1_store(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "idempotency-conflict"
    _prepare(workspace)
    runtime = workspace / RUNTIME_DIR_NAME
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        store.begin_work_unit(RUN_ID, "u-1", "stable-key", "正在核对合成资料")
        store.complete_work_unit(
            RUN_ID,
            "u-1",
            "stable-key",
            NodeStatus.PASSED,
            "已完成合成资料核对",
        )
        with pytest.raises(IdempotencyConflictError):
            store.complete_work_unit(
                RUN_ID,
                "u-1",
                "stable-key",
                NodeStatus.PASSED,
                "冲突的完成内容",
            )


@pytest.mark.parametrize("tamper", ["ledger", "audit"])
def test_ledger_or_audit_tamper_fails_closed_without_partial_progress(
    tmp_path: Path, tamper: str
) -> None:
    workspace = tmp_path / tamper
    adapter, _ = _prepare(workspace)
    runtime = workspace / RUNTIME_DIR_NAME
    with sqlite3.connect(runtime / RUNTIME_DB_NAME) as connection:
        if tamper == "ledger":
            connection.execute(
                "UPDATE work_unit_runs SET status=? WHERE run_id=? AND work_unit_id=?",
                (NodeStatus.PASSED.value, RUN_ID, "u-1"),
            )
        else:
            connection.execute(
                "UPDATE audit_events SET payload_json=? WHERE seq=1", ("{}",)
            )

    with pytest.raises(RuntimeProgressError) as raised:
        adapter.progress(RUN_ID)
    assert raised.value.code == "runtime_integrity_failed"
