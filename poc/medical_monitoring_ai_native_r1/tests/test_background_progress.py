"""Focused tests for the synthetic background-progress facade and shell.

Covers: background work without a page, single audience projection source,
audience-only HTTP schema, leave/return, refresh and facade reconstruction
without duplicate dispatch, truthful failed/blocked states, and a real
browser pass on an ephemeral 127.0.0.1:0 port closed after the test.
Synthetic/offline only: no product code, real projects, providers or 8911.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from mm_r1.audience_progress import project_audience_progress
from mm_r1.background_progress import (
    BackgroundProgressError,
    BackgroundProgressFacade,
    SHELL_RUN_ID,
    SHELL_UNITS,
    audience_snapshot,
    prepare_synthetic_shell,
)
from mm_r1.store import Store

SLICE_ROOT = (
    Path(__file__).resolve().parents[1] / "slices" / "background_progress_shell"
)
if str(SLICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SLICE_ROOT))

from server import ProgressShellServer  # noqa: E402

TOTAL_UNITS = len(SHELL_UNITS)
AUDIENCE_KEYS = {
    "headline", "completed", "total", "percent", "progress_text",
    "status_overview", "stage_progress", "current_work", "latest_updates",
}
FORBIDDEN_SERIALIZED_TOKENS = (
    "provider", "model", "selector", "attempt", "backend", "node", "binding",
    "audit", "log", "hash", "runtime", "manifest", "revision", "api", "url",
    "raw", "sql", "cache", "token", "session", "pid", "work_unit",
    "work unit", "run_id", "run-", "http://", "127.0.0.1", "只读投影",
    "候选信号", "正式事实",
)


def _prepare(tmp_path):
    store = Store(tmp_path / "shell.sqlite3", tmp_path / "artifacts")
    prepare_synthetic_shell(store)
    return store


def _facade(store, **kwargs):
    return BackgroundProgressFacade(
        store, SHELL_RUN_ID, step_seconds=0.005, sweep_seconds=0.01, **kwargs,
    )


def _audit_counts(store):
    events = store.audit_trail()
    begins = [
        event for event in events if event.event_type == "work_unit_begin"
    ]
    completes = [
        event for event in events if event.event_type == "work_unit_complete"
    ]
    return len(begins), len(completes), events[-1].seq if events else 0


def _wait_until(predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_shell_preparation_is_idempotent(r1_store) -> None:
    first = prepare_synthetic_shell(r1_store)
    second = prepare_synthetic_shell(r1_store)
    assert first == second == 1
    rows = r1_store.list_work_unit_runs(SHELL_RUN_ID, 1)
    assert len(rows) == TOTAL_UNITS
    assert all(row.status.value == "pending" for row in rows)


def test_background_work_finishes_without_any_page_or_polling(r1_store) -> None:
    prepare_synthetic_shell(r1_store)
    facade = _facade(r1_store)
    facade.start()
    assert facade.wait(timeout=10) is True
    facade.stop()

    view = facade.snapshot()
    assert view["completed"] == TOTAL_UNITS
    assert view["total"] == TOTAL_UNITS
    assert view["percent"] == 100.0
    assert view["headline"] == "本次监查已结束，部分工作未完成"
    by_label = {item["state_label"]: item["count"] for item in view["status_overview"]}
    assert by_label == {"已完成": 6, "未完成": 1, "暂时受阻": 1}
    assert sum(stage["processed"] for stage in view["stage_progress"]) == TOTAL_UNITS


def test_failed_and_blocked_units_are_reported_truthfully(r1_store) -> None:
    prepare_synthetic_shell(r1_store)
    facade = _facade(r1_store)
    facade.start()
    assert facade.wait(timeout=10) is True
    facade.stop()
    view = facade.snapshot()
    messages = [item["message"] for item in view["latest_updates"]]
    assert any(message.startswith("未完成：核查合成数据完整性") for message in messages)
    assert any(message.startswith("暂时受阻：汇总本次合成监查结果") for message in messages)
    assert not any(message.startswith("已完成：核查合成数据完整性") for message in messages)


def test_snapshot_is_read_only_and_matches_direct_projection(tmp_path) -> None:
    store = _prepare(tmp_path)
    facade = _facade(store)
    facade.start()
    assert facade.wait(timeout=10) is True
    facade.stop()

    _, _, seq_before = _audit_counts(store)
    statuses_before = [
        row.status.value
        for row in sorted(store.list_work_unit_runs(SHELL_RUN_ID, 1),
                          key=lambda row: row.work_unit_id)
    ]
    view = audience_snapshot(store.db_path, store.artifact_dir, SHELL_RUN_ID)
    direct = project_audience_progress(store, SHELL_RUN_ID)
    assert view == direct
    _, _, seq_after = _audit_counts(store)
    statuses_after = [
        row.status.value
        for row in sorted(store.list_work_unit_runs(SHELL_RUN_ID, 1),
                          key=lambda row: row.work_unit_id)
    ]
    assert seq_before == seq_after
    assert statuses_before == statuses_after
    store.close()


def test_reconstruction_and_refresh_do_not_duplicate_dispatch(tmp_path) -> None:
    store = _prepare(tmp_path)
    facade = _facade(store)
    facade.start()
    assert facade.wait(timeout=10) is True
    facade.stop()
    begins, completes, _ = _audit_counts(store)
    assert begins == TOTAL_UNITS
    assert completes == TOTAL_UNITS

    # Facade reconstruction against the same SQLite file (refresh/return).
    rebuilt = BackgroundProgressFacade(
        store, SHELL_RUN_ID, step_seconds=0.001, sweep_seconds=0.01,
    )
    rebuilt.start()
    assert rebuilt.wait(timeout=10) is True
    rebuilt.stop()
    begins_after, completes_after, _ = _audit_counts(store)
    assert (begins_after, completes_after) == (TOTAL_UNITS, TOTAL_UNITS)
    view = rebuilt.snapshot()
    assert view["completed"] == TOTAL_UNITS
    store.close()


def test_concurrent_facades_do_not_repeat_the_actual_unit_action(tmp_path) -> None:
    store = _prepare(tmp_path)
    calls = []
    calls_lock = threading.Lock()

    def step(unit, idempotency_key):
        assert idempotency_key.endswith(":" + unit.work_unit_id)
        with calls_lock:
            calls.append(unit.work_unit_id)
        time.sleep(0.01)
        from mm_r1.background_progress import synthetic_shell_outcome
        return synthetic_shell_outcome(unit, idempotency_key)

    facades = [_facade(store, unit_step=step) for _ in range(3)]
    for facade in facades:
        facade.start()
    assert all(facade.wait(timeout=10) for facade in facades)
    for facade in facades:
        facade.stop()
    begins, completes, _ = _audit_counts(store)
    assert (begins, completes) == (TOTAL_UNITS, TOTAL_UNITS)
    assert sorted(calls) == sorted(unit_id for unit_id, *_ in SHELL_UNITS)
    assert store.get_work_unit_run(SHELL_RUN_ID, 1, "shell-6").status.value == "failed"
    store.close()


def test_store_failure_is_recorded_and_retried_with_at_least_once_semantics(
    tmp_path, monkeypatch,
) -> None:
    store = _prepare(tmp_path)
    calls = []
    keys = []
    original_complete = Store.complete_work_unit
    failed_once = False

    def step(unit, idempotency_key):
        calls.append(unit.work_unit_id)
        keys.append(idempotency_key)
        from mm_r1.background_progress import synthetic_shell_outcome
        return synthetic_shell_outcome(unit, idempotency_key)

    def flaky_complete(self, *args, **kwargs):
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            from mm_r1.domain import StoreError
            raise StoreError("synthetic transient Store failure")
        return original_complete(self, *args, **kwargs)

    monkeypatch.setattr(Store, "complete_work_unit", flaky_complete)
    facade = _facade(store, unit_step=step)
    facade.start()
    assert facade.wait(timeout=10) is True
    facade.stop()

    assert facade.running() is False
    assert facade.errors and facade.errors[0][0] == "background-worker"
    assert calls.count("shell-1") == 2
    assert keys[0] == keys[1] == "background-progress:1:shell-1"
    assert sorted(set(calls)) == sorted(unit_id for unit_id, *_ in SHELL_UNITS)
    begins, completes, _ = _audit_counts(store)
    assert (begins, completes) == (TOTAL_UNITS, TOTAL_UNITS)
    assert facade.snapshot()["completed"] == TOTAL_UNITS
    store.close()


def test_leave_and_return_resumes_the_same_ledger(tmp_path) -> None:
    store = _prepare(tmp_path)
    facade = BackgroundProgressFacade(
        store, SHELL_RUN_ID, step_seconds=0.02, sweep_seconds=0.01,
    )
    facade.start()
    assert _wait_until(
        lambda: audience_snapshot(
            store.db_path, store.artifact_dir, SHELL_RUN_ID,
        )["completed"] > 0
    )
    facade.stop()  # user leaves the page; the ledger keeps partial progress
    stopped_view = project_audience_progress(store, SHELL_RUN_ID)
    assert 0 < stopped_view["completed"] < TOTAL_UNITS

    returned = BackgroundProgressFacade(
        store, SHELL_RUN_ID, step_seconds=0.005, sweep_seconds=0.01,
    )
    returned.start()
    assert returned.wait(timeout=10) is True
    returned.stop()
    begins, completes, _ = _audit_counts(store)
    assert (begins, completes) == (TOTAL_UNITS, TOTAL_UNITS)
    final = project_audience_progress(store, SHELL_RUN_ID)
    assert final["completed"] == TOTAL_UNITS
    assert final["headline"] == "本次监查已结束，部分工作未完成"
    store.close()


def test_facade_rejects_unsafe_configuration(tmp_path) -> None:
    store = _prepare(tmp_path)
    with pytest.raises(TypeError):
        BackgroundProgressFacade(object(), SHELL_RUN_ID)  # type: ignore[arg-type]
    with pytest.raises(BackgroundProgressError):
        BackgroundProgressFacade(store, SHELL_RUN_ID, step_seconds=-1)

    other = Store(tmp_path / "bare.sqlite3", tmp_path / "bare-artifacts")
    from mm_r1.domain import (
        ExecutionBasis, MonitoringRun, RunMode, SourceRevision, content_hash,
    )
    other.create_project("project-bare", "合成空批次项目")
    other.add_source_revision(SourceRevision(
        revision_id="source-bare", project_id="project-bare",
        source_type="listing", version="synthetic-bare-v1",
        content_hash=content_hash({"bare": True}),
    ))
    other.create_run(MonitoringRun(
        run_id="run-bare", project_id="project-bare", mode=RunMode.DAILY,
        data_cutoff="2026-08-09", source_revision_id="source-bare",
        execution_basis=ExecutionBasis.FULL,
    ))
    with pytest.raises(BackgroundProgressError):
        BackgroundProgressFacade(other, "run-bare")
    other.close()
    store.close()


def test_http_progress_schema_is_audience_only_and_port_closes(tmp_path) -> None:
    store = _prepare(tmp_path)
    facade = _facade(store)
    facade.start()
    with ProgressShellServer(store.db_path, store.artifact_dir, SHELL_RUN_ID) as server:
        host, port = server._httpd.server_address
        assert host == "127.0.0.1"
        assert port > 0

        with urllib.request.urlopen(server.base_url + "/progress", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert set(payload) == AUDIENCE_KEYS
        for stage in payload["stage_progress"]:
            assert set(stage) == {"stage", "processed", "total", "progress_text"}
        for update in payload["latest_updates"]:
            assert set(update) == {"time_text", "stage", "label", "state_label", "message"}
        for item in payload["status_overview"]:
            assert set(item) == {"state_label", "count"}
        serialized = json.dumps(payload, ensure_ascii=False)
        lowered = serialized.casefold()
        for token in FORBIDDEN_SERIALIZED_TOKENS:
            assert token not in lowered, token

        with urllib.request.urlopen(server.base_url + "/", timeout=5) as response:
            page = response.read().decode("utf-8")
        assert "医学监查进度" in page
        assert "您可以离开此页面" in page

        request = urllib.request.Request(server.base_url + "/progress", method="POST")
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        assert error.value.code == 405

    facade.stop()
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
    finally:
        probe.close()
    store.close()


def test_refresh_during_run_reads_the_same_sqlite_state(tmp_path) -> None:
    store = _prepare(tmp_path)
    facade = _facade(store)
    facade.start()
    with ProgressShellServer(store.db_path, store.artifact_dir, SHELL_RUN_ID) as server:

        seen = []
        while True:
            with urllib.request.urlopen(server.base_url + "/progress", timeout=5) as response:
                view = json.loads(response.read().decode("utf-8"))
            seen.append(view["completed"])
            if view["completed"] == view["total"]:
                break
            if len(seen) > 500:
                raise AssertionError("background work did not finish in time")
            time.sleep(0.01)
        assert seen == sorted(seen)
    facade.stop()
    store.close()


def test_browser_shell_progress_recovery_and_language_contract(tmp_path) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        executable = playwright.chromium.executable_path
        if not executable or not Path(executable).exists():
            pytest.skip("chromium browser is not installed")

        store = _prepare(tmp_path)
        facade = BackgroundProgressFacade(
            store, SHELL_RUN_ID, step_seconds=0.05, sweep_seconds=0.02,
        )
        facade.start()
        with ProgressShellServer(store.db_path, store.artifact_dir, SHELL_RUN_ID) as server:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(server.base_url + "/")
                page.wait_for_selector("body[data-shell-state='ready']", timeout=10000)

                body_text = page.evaluate("() => document.body.innerText")
                assert "医学监查进度" in body_text
                assert "您可以离开此页面" in body_text
                assert "已处理" in body_text
                assert page.locator("#stage-list li").count() >= 1
                assert page.locator("#update-list li").count() >= 1

                # Leave the page; background work must continue anyway.
                page.goto("about:blank")
                assert _wait_until(
                    lambda: audience_snapshot(
                        store.db_path, store.artifact_dir, SHELL_RUN_ID,
                    )["completed"] == TOTAL_UNITS,
                    timeout=15,
                )

                # Return, then refresh: both must rebuild from SQLite.
                page.goto(server.base_url + "/")
                page.wait_for_selector("body[data-shell-state='ready']", timeout=10000)
                page.reload()
                page.wait_for_selector("body[data-shell-state='ready']", timeout=10000)
                final_text = page.evaluate("() => document.body.innerText")
                assert "本次监查已结束，部分工作未完成" in final_text
                assert "已处理 8/8 项" in final_text
                assert page.evaluate("() => Math.round(document.getElementById('overall-bar').getAttribute('aria-valuenow'))") == 100
                page.wait_for_function(
                    "() => { const track = document.getElementById('overall-bar').getBoundingClientRect(); const fill = document.getElementById('overall-bar-fill').getBoundingClientRect(); return track.width > 0 && fill.width / track.width >= 0.99; }",
                    timeout=5000,
                )
                assert page.evaluate(
                    "() => Array.from(document.querySelectorAll('.stages__bar')).every((track) => { const fill = track.querySelector('.stages__bar-fill'); return track.getBoundingClientRect().width > 0 && fill.getBoundingClientRect().width / track.getBoundingClientRect().width >= 0.99; })"
                )
                lowered = final_text.casefold()
                for token in ("provider", "attempt", "backend", "manifest",
                              "work_unit", "只读投影", "候选信号", "正式事实"):
                    assert token not in lowered, token

                evidence_dir = SLICE_ROOT / "evidence"
                evidence_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(evidence_dir / "final_state.png"), full_page=True)
            finally:
                browser.close()
        facade.stop()
        begins, completes, _ = _audit_counts(store)
        assert (begins, completes) == (TOTAL_UNITS, TOTAL_UNITS)
        store.close()
