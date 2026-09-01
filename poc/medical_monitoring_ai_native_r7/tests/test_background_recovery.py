"""Slice-05 synthetic/offline background execution and recovery tests.

All fixtures use a temporary R7 workspace and the accepted R1 SQLite Store.
The tests do not import the product main module, start 8911/5174, invoke a
model/provider/harness, or use a real project.  R1 remains the source of
work-unit status/counts; R7 is tested only for control, lease, scheduling and
the public Chinese overlay.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from mm_r7.background_recovery import (
    BackgroundOutcome,
    BackgroundRecoveryAdapter,
    ExecutionControl,
    ExecutionControlError,
    ExecutionControlState,
    _public_overlay,
)
from mm_r7.run_entry import MonitoringRunEntry
from mm_r7.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
    RuntimeProgressError,
)
from mm_r1.domain import (
    IdempotencyConflictError,
    NodeStatus,
    StaleCallbackError,
)
from mm_r1.store import Store


PROJECT_ID = "r7-slice05-project"
RUN_ID = "r7-slice05-run"


class ManualClock:
    """Thread-safe injectable wall clock for lease boundary tests."""

    def __init__(self, value: float = 1000.0) -> None:
        self._value = float(value)
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._value

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._value += float(seconds)


def _units(
    prefix: str = "u", count: int = 3, *, chain: bool = False
) -> list[dict[str, Any]]:
    stages = (
        "资料准备",
        "数据解构",
        "风险分析",
        "质量检查",
        "结果汇总",
        "核查准备",
    )
    scopes = ("source", "subject", "risk_domain", "qc", "project", "document")
    return [
        {
            "work_unit_id": f"{prefix}-{index}",
            "stage": stages[(index - 1) % len(stages)],
            "label": f"完成合成监查第{index}项",
            "scope": scopes[(index - 1) % len(scopes)],
            "target_ref": f"SYN-{index:03d}",
            "ordinal": index,
            "mandatory": True,
            "depends_on": [f"{prefix}-{index - 1}"]
            if chain and index > 1
            else [],
        }
        for index in range(1, count + 1)
    ]


def _bind(
    workspace: Path,
    *,
    run_id: str = RUN_ID,
    project_id: str = PROJECT_ID,
) -> None:
    entry = MonitoringRunEntry(workspace)
    try:
        entry.bootstrap_workspace()
        entry.bind_run(
            run_id=run_id,
            project_id=project_id,
            mode="daily",
            execution_basis="full",
            data_cutoff="2026-08-28",
            source_revision_id=f"source-{run_id}",
        )
    finally:
        entry.close()


def _prepare(
    workspace: Path,
    *,
    units: list[dict[str, Any]] | None = None,
    run_id: str = RUN_ID,
    project_id: str = PROJECT_ID,
) -> RuntimeProgressAdapter:
    _bind(workspace, run_id=run_id, project_id=project_id)
    adapter = RuntimeProgressAdapter(workspace, canonical_project_id=project_id)
    adapter.prepare(run_id, units or _units())
    return adapter


def _background(
    workspace: Path,
    *,
    project_id: str = PROJECT_ID,
    unit_step: Callable[[Any, str], BackgroundOutcome] | None = None,
    clock: Callable[[], float] = time.time,
    lease_seconds: float = 15.0,
    heartbeat_seconds: float = 5.0,
    step_seconds: float = 0.0,
    sweep_seconds: float = 0.001,
) -> BackgroundRecoveryAdapter:
    return BackgroundRecoveryAdapter(
        runtime_dir=workspace / RUNTIME_DIR_NAME,
        canonical_project_id=project_id,
        unit_step=unit_step,
        clock=clock,
        lease_seconds=lease_seconds,
        heartbeat_seconds=heartbeat_seconds,
        step_seconds=step_seconds,
        sweep_seconds=sweep_seconds,
    )


def _runtime(workspace: Path) -> Path:
    return workspace / RUNTIME_DIR_NAME


def _rows(workspace: Path, run_id: str = RUN_ID, revision: int = 1) -> dict[str, Any]:
    runtime = _runtime(workspace)
    with Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME) as store:
        return {
            row.work_unit_id: row
            for row in store.list_work_unit_runs(run_id, revision)
        }


def _event_types(workspace: Path, run_id: str = RUN_ID) -> list[str]:
    with sqlite3.connect(_runtime(workspace) / RUNTIME_DB_NAME) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT event_type FROM audit_events WHERE run_id=? ORDER BY seq",
                (run_id,),
            )
        ]


def _wait_terminal(adapter: BackgroundRecoveryAdapter, run_id: str = RUN_ID) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        control = adapter.get_control(run_id)
        if control.state in {
            ExecutionControlState.INTERRUPTED,
            ExecutionControlState.FINISHED,
        } and not adapter.running(run_id):
            return
        time.sleep(0.002)
    assert not adapter.running(run_id), "synthetic worker did not stop in time"
    assert adapter.get_control(run_id).state in {
        ExecutionControlState.INTERRUPTED,
        ExecutionControlState.FINISHED,
    }


def test_prepare_and_progress_do_not_start_a_thread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started: list[bool] = []

    def forbidden_start(_thread: threading.Thread, *args: Any, **kwargs: Any) -> None:
        started.append(True)
        raise AssertionError("prepare/progress must not start a worker")

    monkeypatch.setattr(threading.Thread, "start", forbidden_start)
    workspace = tmp_path / "no-thread"
    adapter = _prepare(workspace, units=_units(count=2))

    view = adapter.progress(RUN_ID)
    assert view["run_status_text"] == "等待开始医学监查"
    assert view["available_actions"] == ["开始"]
    assert view["run_state"] == "waiting_start"
    assert view["completed"] == 0
    assert view["total"] == 2
    assert started == []


def test_start_completes_without_client_polling_and_rebuilds_from_sqlite(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "offline-complete"
    _prepare(workspace, units=_units(count=4))
    first = _background(workspace)

    response = first.start_execution(RUN_ID)
    assert response == {
        "replayed": False,
        "run_status_text": "医学监查进行中",
        "available_actions": ["停止"],
    }
    _wait_terminal(first)

    rebuilt = _background(workspace)
    view = rebuilt.snapshot(RUN_ID)
    assert view["completed"] == 4
    assert view["total"] == 4
    assert view["percent"] == 100.0
    assert view["run_status_text"] == "本次监查已完成"
    assert view["available_actions"] == []
    assert all(row.status is NodeStatus.PASSED for row in _rows(workspace).values())
    assert _event_types(workspace).count("work_unit_begin") == 4
    assert _event_types(workspace).count("work_unit_complete") == 4


def test_snapshot_keeps_r1_counts_and_r7_overlay_in_one_read_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "consistent-snapshot"
    _prepare(workspace, units=_units(count=2))
    entered = threading.Event()
    release = threading.Event()

    def blocked_step(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=blocked_step)
    runner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    try:
        running_view = runner.snapshot(RUN_ID)
        assert running_view["completed"] == 0
        assert running_view["total"] == 2
        assert running_view["percent"] == 0.0
        assert running_view["run_status_text"] == "医学监查进行中"
        assert running_view["available_actions"] == ["停止"]
        assert running_view["run_state"] == "running"
        assert running_view["current_work"]
        assert all(
            item["state_label"] == "进行中"
            for item in running_view["current_work"]
        )
    finally:
        release.set()
    _wait_terminal(runner)
    finished_view = runner.snapshot(RUN_ID)
    assert finished_view["completed"] == finished_view["total"] == 2
    assert finished_view["percent"] == 100.0
    assert finished_view["run_status_text"] == "本次监查已完成"
    assert finished_view["available_actions"] == []
    assert finished_view["run_state"] == "completed"


def test_two_sqlite_connections_share_one_start_lease_and_one_history(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "two-connections"
    _prepare(workspace, units=_units(count=1))
    entered = threading.Event()
    release = threading.Event()
    calls: list[str] = []
    calls_lock = threading.Lock()

    def blocked_step(unit: Any, _key: str) -> BackgroundOutcome:
        with calls_lock:
            calls.append(unit.work_unit_id)
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    first = _background(workspace, unit_step=blocked_step)
    second = _background(workspace, unit_step=blocked_step)
    responses: dict[str, Any] = {}
    errors: list[BaseException] = []

    def invoke_first() -> None:
        try:
            responses["first"] = first.start_execution(RUN_ID)
        except BaseException as exc:  # pragma: no cover - failure diagnostics
            errors.append(exc)

    thread = threading.Thread(target=invoke_first, name="test-r7-start-1")
    thread.start()
    assert entered.wait(5.0)
    try:
        responses["second"] = second.start_execution(RUN_ID)
    finally:
        release.set()
        thread.join(5.0)
        _wait_terminal(first)

    assert errors == []
    assert responses["first"]["replayed"] is False
    assert responses["second"]["replayed"] is True
    assert calls == ["u-1"]
    assert _event_types(workspace).count("work_unit_begin") == 1
    assert _event_types(workspace).count("work_unit_complete") == 1


def test_expired_lease_resume_replays_stable_key_without_duplicate_history(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "lease-recovery"
    _prepare(workspace, units=_units(count=1))
    clock = ManualClock()
    entered = threading.Event()
    release = threading.Event()

    def interrupted_step(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    owner = _background(
        workspace,
        unit_step=interrupted_step,
        clock=clock,
        lease_seconds=1.0,
        heartbeat_seconds=0.1,
    )
    response = owner.start_execution(RUN_ID)
    assert response["replayed"] is False
    assert entered.wait(5.0)
    before = owner.get_control(RUN_ID)
    assert before.state is ExecutionControlState.RUNNING

    clock.advance(2.0)
    recovered = _background(workspace, clock=clock, lease_seconds=1.0)
    after_recovery = recovered.recover_expired_lease(RUN_ID)
    assert after_recovery.state is ExecutionControlState.INTERRUPTED
    assert after_recovery.generation == before.generation + 1
    assert owner.heartbeat(
        RUN_ID,
        before.manifest_revision,
        before.generation,
        before.owner_token,
    ) is False

    release.set()
    _wait_terminal(owner)
    resumed = recovered.resume_execution(RUN_ID)
    assert resumed["replayed"] is False
    _wait_terminal(recovered)

    row = _rows(workspace)["u-1"]
    assert row.status is NodeStatus.PASSED
    assert row.idempotency_key == f"r7-background:{RUN_ID}:1:u-1"
    event_types = _event_types(workspace)
    assert event_types.count("work_unit_begin") == 1
    assert event_types.count("work_unit_complete") == 1

    # The old generation's same-key completion is absorbed by R1; a
    # different terminal fingerprint remains an idempotency conflict.
    with Store(_runtime(workspace) / RUNTIME_DB_NAME, _runtime(workspace) / ARTIFACT_DIR_NAME) as store:
        store.begin_work_unit(
            RUN_ID,
            "u-1",
            row.idempotency_key,
            "正在完成合成监查第1项",
        )
        store.complete_work_unit(
            RUN_ID,
            "u-1",
            row.idempotency_key,
            NodeStatus.PASSED,
            "已完成：完成合成监查第1项",
        )
        with pytest.raises(IdempotencyConflictError):
            store.complete_work_unit(
                RUN_ID,
                "u-1",
                row.idempotency_key,
                NodeStatus.PASSED,
                "冲突的旧代完成回调",
            )
    assert _event_types(workspace).count("work_unit_begin") == 1
    assert _event_types(workspace).count("work_unit_complete") == 1


def test_injected_complete_failure_interrupts_then_resume_replays_same_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "complete-failure-injection"
    _prepare(workspace, units=_units(count=1))
    original_complete = Store.complete_work_unit
    failures_left = [True]

    def fail_once(self: Store, *args: Any, **kwargs: Any) -> Any:
        if failures_left:
            failures_left.pop()
            raise RuntimeError("injected complete failure")
        return original_complete(self, *args, **kwargs)

    monkeypatch.setattr(Store, "complete_work_unit", fail_once)
    runner = _background(workspace)
    runner.start_execution(RUN_ID)
    _wait_terminal(runner)
    assert runner.get_control(RUN_ID).state is ExecutionControlState.INTERRUPTED
    assert _rows(workspace)["u-1"].status is NodeStatus.RUNNING
    assert _event_types(workspace).count("work_unit_begin") == 1
    assert _event_types(workspace).count("work_unit_complete") == 0

    resumed = runner.resume_execution(RUN_ID)
    assert resumed["replayed"] is False
    _wait_terminal(runner)
    assert runner.get_control(RUN_ID).state is ExecutionControlState.FINISHED
    assert _rows(workspace)["u-1"].status is NodeStatus.PASSED
    assert _event_types(workspace).count("work_unit_begin") == 1
    assert _event_types(workspace).count("work_unit_complete") == 1


def test_stop_finishes_current_unit_then_interrupts_and_resume_keeps_revision(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "stop-resume"
    _prepare(workspace, units=_units(count=3))
    entered = threading.Event()
    release = threading.Event()

    def stoppable_step(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    first = _background(workspace, unit_step=stoppable_step)
    second = _background(workspace)
    first.start_execution(RUN_ID)
    assert entered.wait(5.0)
    before = first.get_control(RUN_ID)
    stop_response = second.cancel_execution(RUN_ID)
    assert stop_response == {
        "replayed": False,
        "run_status_text": "正在停止医学监查",
        "available_actions": [],
    }
    assert second.get_control(RUN_ID).state is ExecutionControlState.CANCELLING
    stopping_view = second.snapshot(RUN_ID)
    assert stopping_view["run_state"] == "stopping"
    assert stopping_view["run_status_text"] == "正在停止医学监查"
    assert stopping_view["available_actions"] == []

    release.set()
    _wait_terminal(first)
    interrupted = second.get_control(RUN_ID)
    assert interrupted.state is ExecutionControlState.INTERRUPTED
    assert interrupted.manifest_revision == before.manifest_revision == 1
    rows = _rows(workspace)
    assert rows["u-1"].status is NodeStatus.PASSED
    assert rows["u-2"].status is NodeStatus.PENDING
    assert rows["u-3"].status is NodeStatus.PENDING
    assert _event_types(workspace).count("work_unit_begin") == 1

    stopped_view = second.snapshot(RUN_ID)
    assert stopped_view["run_status_text"] == "已停止，可继续"
    assert stopped_view["available_actions"] == ["继续"]
    assert stopped_view["run_state"] == "interrupted_resumable"
    assert stopped_view["completed"] == 1
    assert stopped_view["total"] == 3

    resumed = second.resume_execution(RUN_ID)
    assert resumed["replayed"] is False
    _wait_terminal(second)
    finished = second.get_control(RUN_ID)
    assert finished.state is ExecutionControlState.FINISHED
    assert finished.manifest_revision == 1
    assert finished.generation == interrupted.generation + 1
    assert all(row.status is NodeStatus.PASSED for row in _rows(workspace).values())
    assert _event_types(workspace).count("work_unit_begin") == 3
    assert _event_types(workspace).count("work_unit_complete") == 3


def test_cancel_after_expired_lease_durably_interrupts_and_is_idempotent(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "expired-stop"
    _prepare(workspace, units=_units(count=2))
    clock = ManualClock()
    entered = threading.Event()
    release = threading.Event()

    def blocked(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    owner = _background(
        workspace,
        unit_step=blocked,
        clock=clock,
        lease_seconds=1.0,
        heartbeat_seconds=0.1,
    )
    controller = _background(workspace, clock=clock, lease_seconds=1.0)
    owner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    before = owner.get_control(RUN_ID)
    clock.advance(2.0)

    stopped = controller.cancel_execution(RUN_ID)
    after = controller.get_control(RUN_ID)
    assert stopped == {
        "replayed": True,
        "run_status_text": "已停止，可继续",
        "available_actions": ["继续"],
    }
    assert after.state is ExecutionControlState.INTERRUPTED
    assert after.generation == before.generation + 1
    assert after.owner_token == ""
    assert after.lease_expires_at is None

    repeated = controller.cancel_execution(RUN_ID)
    assert repeated == stopped
    assert controller.get_control(RUN_ID) == after
    release.set()
    _wait_terminal(owner)

    resumed = controller.resume_execution(RUN_ID)
    assert resumed["replayed"] is False
    _wait_terminal(controller)
    assert controller.get_control(RUN_ID).state is ExecutionControlState.FINISHED
    assert all(row.status is NodeStatus.PASSED for row in _rows(workspace).values())
    events = _event_types(workspace)
    assert events.count("work_unit_begin") == 2
    assert events.count("work_unit_complete") == 2


def test_progress_reconciles_expired_lease_without_starting_a_worker(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "expired-progress-rebuild"
    _prepare(workspace, units=_units(count=1))
    clock = ManualClock()
    entered = threading.Event()
    release = threading.Event()

    def blocked(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    owner = _background(
        workspace,
        unit_step=blocked,
        clock=clock,
        lease_seconds=1.0,
        heartbeat_seconds=0.1,
    )
    rebuilt = _background(workspace, clock=clock, lease_seconds=1.0)
    owner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    before = owner.get_control(RUN_ID)
    clock.advance(2.0)
    worker_ids_before = {
        thread.ident
        for thread in threading.enumerate()
        if thread.name == "mm-r7-background-worker"
    }

    view = rebuilt.snapshot(RUN_ID)
    after = rebuilt.get_control(RUN_ID)
    assert view["run_status_text"] == "已停止，可继续"
    assert view["available_actions"] == ["继续"]
    assert after.state is ExecutionControlState.INTERRUPTED
    assert after.generation == before.generation + 1
    assert after.owner_token == ""
    assert {
        thread.ident
        for thread in threading.enumerate()
        if thread.name == "mm-r7-background-worker"
    } == worker_ids_before
    release.set()
    _wait_terminal(owner)


def test_stop_on_last_unit_finishes_without_false_continue_action(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "last-unit-stop"
    _prepare(workspace, units=_units(count=1))
    entered = threading.Event()
    release = threading.Event()

    def blocked(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=blocked)
    runner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    runner.cancel_execution(RUN_ID)
    release.set()
    _wait_terminal(runner)

    assert runner.get_control(RUN_ID).state is ExecutionControlState.FINISHED
    view = runner.snapshot(RUN_ID)
    assert view["completed"] == view["total"] == 1
    assert view["run_status_text"] == "本次监查已完成"
    assert view["available_actions"] == []
    replayed_stop = runner.cancel_execution(RUN_ID)
    assert replayed_stop["replayed"] is True
    assert replayed_stop["run_status_text"] == "本次监查已完成"
    assert replayed_stop["available_actions"] == []


def test_dependency_is_not_started_until_upstream_passes(tmp_path: Path) -> None:
    workspace = tmp_path / "dependency-order"
    _prepare(workspace, units=_units(count=2, chain=True))
    entered = threading.Event()
    release = threading.Event()
    calls: list[str] = []

    def ordered_step(unit: Any, _key: str) -> BackgroundOutcome:
        calls.append(unit.work_unit_id)
        if unit.work_unit_id == "u-1":
            entered.set()
            assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=ordered_step)
    runner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    assert calls == ["u-1"]
    assert _rows(workspace)["u-2"].status is NodeStatus.PENDING
    release.set()
    _wait_terminal(runner)
    assert calls == ["u-1", "u-2"]
    assert all(row.status is NodeStatus.PASSED for row in _rows(workspace).values())


def test_failed_dependency_closes_finished_without_spinning_or_resume(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "dependency-failure"
    _prepare(workspace, units=_units(count=2, chain=True))
    calls: list[str] = []

    def fail_upstream(unit: Any, _key: str) -> BackgroundOutcome:
        calls.append(unit.work_unit_id)
        if unit.work_unit_id == "u-1":
            return BackgroundOutcome(NodeStatus.FAILED, "未完成：上游合成检查失败")
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=fail_upstream)
    runner.start_execution(RUN_ID)
    _wait_terminal(runner)
    assert runner.get_control(RUN_ID).state is ExecutionControlState.FINISHED
    assert calls == ["u-1"]
    rows = _rows(workspace)
    assert rows["u-1"].status is NodeStatus.FAILED
    assert rows["u-2"].status is NodeStatus.PENDING
    with pytest.raises(ExecutionControlError) as raised:
        runner.resume_execution(RUN_ID)
    assert raised.value.code == "nothing_to_resume"
    view = runner.snapshot(RUN_ID)
    assert view["completed"] == 1
    assert view["total"] == 2
    assert view["run_status_text"] == "本次监查已结束，部分工作未完成"
    assert view["available_actions"] == []
    assert view["run_state"] == "ended_incomplete"


def test_prepare_scope_change_is_rejected_while_running_and_old_revision_is_stale(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "scope-boundary"
    _prepare(workspace, units=_units("a", count=1))
    entered = threading.Event()
    release = threading.Event()

    def blocked(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=blocked)
    runner.start_execution(RUN_ID)
    assert entered.wait(5.0)
    progress = RuntimeProgressAdapter(workspace, canonical_project_id=PROJECT_ID)
    with pytest.raises(RuntimeProgressError) as raised:
        progress.prepare(RUN_ID, _units("b", count=1))
    assert raised.value.code == "prepare_while_running"
    assert _rows(workspace, revision=1)["a-1"].status is NodeStatus.RUNNING

    release.set()
    _wait_terminal(runner)
    second = progress.prepare(RUN_ID, _units("b", count=1))
    assert second["scope_version_text"] == "第 2 版监查范围"
    with Store(_runtime(workspace) / RUNTIME_DB_NAME, _runtime(workspace) / ARTIFACT_DIR_NAME) as store:
        with pytest.raises(StaleCallbackError):
            store.begin_work_unit(
                RUN_ID,
                "a-1",
                "stale-old-revision",
                "正在处理旧版工作",
                manifest_revision=1,
            )


def test_harness_running_overlay_does_not_double_prefix_正在() -> None:
    control = ExecutionControl(
        run_id=RUN_ID,
        manifest_revision=1,
        generation=1,
        state=ExecutionControlState.RUNNING,
        owner_token="owner",
        lease_expires_at=None,
        cancel_requested=False,
        created_at="t0",
        updated_at="t0",
    )
    plain = _public_overlay(
        control,
        {"current_work": [{"label": "核对合成监查第1项资料"}]},
        harness=True,
    )
    prefixed = _public_overlay(
        control,
        {"current_work": [{"label": "正在核对合成监查第1项资料"}]},
        harness=True,
    )
    assert plain["run_status_text"] == "正在分析：核对合成监查第1项资料。"
    assert prefixed["run_status_text"] == "正在分析：核对合成监查第1项资料。"
    assert "正在分析：正在" not in plain["run_status_text"]
    assert "正在分析：正在" not in prefixed["run_status_text"]


@pytest.mark.parametrize("tamper", ["audit", "control"])
def test_integrity_tamper_blocks_start_before_any_background_action(
    tmp_path: Path, tamper: str
) -> None:
    workspace = tmp_path / f"tamper-{tamper}"
    _prepare(workspace, units=_units(count=1))
    runtime = _runtime(workspace)
    if tamper == "audit":
        with sqlite3.connect(runtime / RUNTIME_DB_NAME) as connection:
            connection.execute(
                "UPDATE audit_events SET payload_json=? WHERE seq=1", ("{}",)
            )
    else:
        with sqlite3.connect(runtime / RUNTIME_DB_NAME) as connection:
            connection.execute(
                "UPDATE r7_execution_control SET owner_token=? WHERE run_id=?",
                ("tampered-owner", RUN_ID),
            )

    calls: list[str] = []

    def should_not_run(unit: Any, _key: str) -> BackgroundOutcome:
        calls.append(unit.work_unit_id)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    runner = _background(workspace, unit_step=should_not_run)
    with pytest.raises(ExecutionControlError) as raised:
        runner.start_execution(RUN_ID)
    assert raised.value.code == "runtime_integrity_failed"
    assert calls == []
    with sqlite3.connect(runtime / RUNTIME_DB_NAME) as connection:
        state, owner = connection.execute(
            "SELECT state, owner_token FROM r7_execution_control WHERE run_id=?",
            (RUN_ID,),
        ).fetchone()
    assert state == "prepared"
    if tamper == "audit":
        assert owner == ""
    else:
        assert owner == "tampered-owner"


def test_missing_binding_or_project_fails_closed_without_worker_start(
    tmp_path: Path,
) -> None:
    missing = _background(tmp_path / "missing")
    with pytest.raises(ExecutionControlError) as unprepared:
        missing.start_execution(RUN_ID)
    assert unprepared.value.code == "execution_not_prepared"

    workspace = tmp_path / "identity-boundary"
    _prepare(workspace, units=_units(count=1))
    wrong_project = _background(workspace, project_id="not-canonical")
    with pytest.raises(ExecutionControlError) as project_error:
        wrong_project.start_execution(RUN_ID)
    assert project_error.value.code == "run_binding_not_found"

    wrong_run = _background(workspace)
    with pytest.raises(ExecutionControlError) as run_error:
        wrong_run.start_execution("not-bound")
    assert run_error.value.code == "runtime_integrity_failed"
    assert wrong_run.get_control(RUN_ID).state is ExecutionControlState.PREPARED


def test_control_table_shape_is_single_run_level_record_without_progress_fields(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "control-shape"
    _prepare(workspace, units=_units(count=2))
    with sqlite3.connect(_runtime(workspace) / RUNTIME_DB_NAME) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(r7_execution_control)")
        }
        rows = connection.execute(
            "SELECT run_id, manifest_revision, generation, state, owner_token,"
            " lease_expires_at, cancel_requested, created_at, updated_at"
            " FROM r7_execution_control"
        ).fetchall()
    assert columns == {
        "run_id",
        "manifest_revision",
        "generation",
        "state",
        "owner_token",
        "lease_expires_at",
        "cancel_requested",
        "created_at",
        "updated_at",
    }
    assert rows == [(RUN_ID, 1, 0, "prepared", "", None, 0, rows[0][7], rows[0][8])]
