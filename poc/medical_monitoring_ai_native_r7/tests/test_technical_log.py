"""Focused synthetic/offline tests for the bounded technical log sink."""

from __future__ import annotations

import fcntl
import json
import logging
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mm_r7.technical_log import (
    ACTIVE_MAX_BYTES,
    ARCHIVE_RETENTION_SECONDS,
    DEGRADED_RING_SIZE,
    FILE_MODE,
    MAX_RECORD_BYTES,
    TECHNICAL_LOG_FIELDS,
    BoundedTechnicalLogHandler,
)


FIXED_TIME = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc)


def make_handler(root: Path, *, protected_roots=()) -> BoundedTechnicalLogHandler:
    return BoundedTechnicalLogHandler(
        root,
        protected_roots=protected_roots,
        clock=lambda: FIXED_TIME,
    )


def write_private(path: Path, data: bytes) -> None:
    fd = os.open(os.fspath(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def test_jsonl_has_exact_nine_fields_and_never_copies_message(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    record = logging.LogRecord(
        name="audit",
        level=logging.INFO,
        pathname="/should-not-be-recorded",
        lineno=7,
        msg="raw output /secret/path token=do-not-copy",
        args=(),
        exc_info=None,
    )
    record.event = "append"
    record.outcome = "ok"
    record.duration_ms = 12.5
    record.degraded = False
    record.created = FIXED_TIME.timestamp()

    assert handler.handle(record) is True
    line = handler.active_path.read_bytes()
    payload = json.loads(line)

    assert tuple(payload) == tuple(sorted(TECHNICAL_LOG_FIELDS))
    assert set(payload) == set(TECHNICAL_LOG_FIELDS)
    assert payload["schema"] == "mm-r7-slice09c-technical-log-v1"
    assert payload["timestamp"] == "2026-08-30T12:00:00.000000Z"
    assert payload["duration_ms"] == 12.5
    assert b"raw output" not in line
    assert b"secret" not in line
    assert b"pathname" not in line
    assert len(line) <= MAX_RECORD_BYTES


def test_record_with_unsafe_path_or_payload_tokens_is_dropped(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)

    assert not handler.log_event(
        severity="info",
        component="audit",
        event="/tmp/private",
        outcome="ok",
    )
    assert not handler.log_event(
        severity="info",
        component="audit",
        event="raw_output",
        outcome="ok",
    )
    assert handler.active_path.exists() is False
    assert handler.degraded is False
    assert handler.dropped_count == 2


def test_oversized_serialized_record_is_dropped_without_a_partial_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler = make_handler(tmp_path)
    monkeypatch.setattr(
        handler,
        "_serialize_with_segment_size",
        lambda body, current_size: b"x" * (MAX_RECORD_BYTES + 1),
    )

    assert not handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )
    assert not handler.active_path.exists()
    assert handler.degraded is False
    assert handler.dropped_count == 1


def test_one_byte_over_active_limit_rotates_before_writing(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    write_private(handler.active_path, b"x" * (ACTIVE_MAX_BYTES - 1))

    assert handler.log_event(
        severity="info",
        component="rotation",
        event="append",
        outcome="ok",
    )
    assert handler.active_path.stat().st_size < ACTIVE_MAX_BYTES
    assert handler.archive_paths[0].read_bytes() == b"x" * (ACTIVE_MAX_BYTES - 1)
    payload = json.loads(handler.active_path.read_text(encoding="utf-8"))
    assert payload["segment_bytes"] == handler.active_path.stat().st_size


def test_four_archives_are_bounded_and_unknown_entries_are_untouched(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    unknown_file = handler.log_dir / "do-not-touch"
    unknown_dir = handler.log_dir / "do-not-touch-dir"
    unknown_link = handler.log_dir / "do-not-touch-link"
    unknown_file.write_bytes(b"unknown")
    unknown_dir.mkdir()
    (unknown_dir / "nested").write_bytes(b"nested")
    unknown_link.symlink_to(unknown_file)

    # Repeatedly seed an almost-full active segment.  Each normal write causes
    # one rotation while keeping the operation small and deterministic.
    for index in range(6):
        write_private(handler.active_path, bytes([65 + index]) * (ACTIVE_MAX_BYTES - 1))
        assert handler.initialize()
        assert handler.log_event(
            severity="info",
            component="rotation",
            event="append",
            outcome="ok",
        )

    assert len(tuple(handler.log_dir.iterdir())) <= 1 + 4 + 1 + 3
    assert unknown_file.read_bytes() == b"unknown"
    assert unknown_dir.is_dir()
    assert (unknown_dir / "nested").read_bytes() == b"nested"
    assert unknown_link.is_symlink()
    assert all(path.exists() for path in handler.archive_paths)


def test_archive_older_than_seven_days_is_pruned_but_boundary_is_retained(
    tmp_path: Path,
) -> None:
    handler = make_handler(tmp_path)
    old_archive = handler.archive_paths[0]
    boundary_archive = handler.archive_paths[1]
    write_private(old_archive, b"old")
    write_private(boundary_archive, b"boundary")
    old_timestamp = FIXED_TIME.timestamp() - ARCHIVE_RETENTION_SECONDS - 1
    boundary_timestamp = FIXED_TIME.timestamp() - ARCHIVE_RETENTION_SECONDS
    os.utime(old_archive, (old_timestamp, old_timestamp), follow_symlinks=False)
    os.utime(boundary_archive, (boundary_timestamp, boundary_timestamp), follow_symlinks=False)

    assert handler.initialize()
    assert not old_archive.exists()
    assert boundary_archive.read_bytes() == b"boundary"


def test_known_symlink_degrades_without_touching_target(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    target = tmp_path / "outside-target"
    target.write_bytes(b"keep")
    handler.active_path.symlink_to(target)

    assert not handler.initialize()
    assert handler.degraded
    assert not handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )
    assert target.read_bytes() == b"keep"
    assert handler.active_path.is_symlink()


def test_protected_root_and_reserved_evidence_components_are_rejected(tmp_path: Path) -> None:
    project_workspace = tmp_path / "canonical-project"
    project_workspace.mkdir()
    handler = make_handler(tmp_path / "runtime", protected_roots=(project_workspace,))
    assert not handler.degraded
    assert handler.log_dir != project_workspace

    protected_handler = make_handler(project_workspace, protected_roots=(project_workspace,))
    assert protected_handler.degraded
    assert not protected_handler.log_dir.exists()
    assert not protected_handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )

    runs_handler = make_handler(tmp_path / "runs")
    assert runs_handler.degraded


def test_lock_contention_is_nonblocking_and_reinitialize_recovers(tmp_path: Path) -> None:
    first = make_handler(tmp_path)
    second = make_handler(tmp_path)
    fd = os.open(os.fspath(first.lock_path), os.O_WRONLY, FILE_MODE)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not second.log_event(
            severity="info",
            component="audit",
            event="append",
            outcome="ok",
        )
        assert second.degraded
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    assert second.initialize()
    assert not second.degraded
    assert second.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )


def test_two_processes_rotate_and_append_without_truncated_jsonl(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    assert handler.log_event(
        severity="info",
        component="seed",
        event="append",
        outcome="ok",
    )
    seed_line = handler.active_path.read_bytes()
    seeded = seed_line * ((ACTIVE_MAX_BYTES - 1) // len(seed_line))
    write_private(handler.active_path, seeded)

    script = r"""
import sys, time
from datetime import datetime, timezone
from pathlib import Path
from mm_r7.technical_log import BoundedTechnicalLogHandler

root = Path(sys.argv[1])
worker = sys.argv[2]
handler = BoundedTechnicalLogHandler(
    root,
    clock=lambda: datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc),
)
(root / ("ready-" + worker)).write_text("ready", encoding="utf-8")
deadline = time.monotonic() + 5
while len(tuple(root.glob("ready-worker_*"))) < 2 and time.monotonic() < deadline:
    time.sleep(0.005)
for _ in range(500):
    if handler.log_event(
        severity="info",
        component=worker,
        event="append",
        outcome="ok",
    ):
        raise SystemExit(0)
    handler.initialize()
    time.sleep(0.002)
raise SystemExit(3)
"""
    env = os.environ.copy()
    source_root = Path(__file__).resolve().parents[1] / "src"
    env["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(source_root), env.get("PYTHONPATH", "")) if value
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(tmp_path), worker],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for worker in ("worker_a", "worker_b")
    ]
    results = [process.communicate(timeout=15) for process in processes]
    assert [process.returncode for process in processes] == [0, 0], results

    payloads = []
    for path in (handler.active_path, *handler.archive_paths):
        if not path.exists():
            continue
        data = path.read_bytes()
        assert data.endswith(b"\n")
        payloads.extend(json.loads(line) for line in data.splitlines())
    components = [payload["component"] for payload in payloads]
    assert components.count("worker_a") == 1
    assert components.count("worker_b") == 1


def test_io_failure_enters_bounded_degraded_until_explicit_initialize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler = make_handler(tmp_path)
    original_fsync = os.fsync

    def fail_fsync(fd: int) -> None:
        raise OSError("injected fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    assert not handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )
    assert handler.degraded
    dropped_after_failure = handler.dropped_count
    assert not handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )
    for _ in range(DEGRADED_RING_SIZE + 4):
        assert not handler.log_event(
            severity="info",
            component="audit",
            event="append",
            outcome="ok",
        )
    assert len(handler.degraded_reasons) == DEGRADED_RING_SIZE
    assert handler.dropped_count == dropped_after_failure + 1 + DEGRADED_RING_SIZE + 4

    monkeypatch.setattr(os, "fsync", original_fsync)
    assert handler.initialize()
    assert not handler.degraded
    assert handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )


def test_new_files_remain_private_under_both_umasks(tmp_path: Path) -> None:
    original_umask = os.umask(0o022)
    try:
        handler = make_handler(tmp_path / "umask-022")
        assert handler.log_event(
            severity="info",
            component="audit",
            event="append",
            outcome="ok",
        )
    finally:
        os.umask(original_umask)
    assert stat.S_IMODE(handler.active_path.stat().st_mode) == FILE_MODE
    assert stat.S_IMODE(handler.lock_path.stat().st_mode) == FILE_MODE

    original_umask = os.umask(0o077)
    try:
        second = make_handler(tmp_path / "umask-077")
        assert second.log_event(
            severity="info",
            component="audit",
            event="append",
            outcome="ok",
        )
    finally:
        os.umask(original_umask)
    assert stat.S_IMODE(second.active_path.stat().st_mode) == FILE_MODE
    assert stat.S_IMODE(second.lock_path.stat().st_mode) == FILE_MODE


def test_fixed_clock_and_sequence_are_byte_deterministic(tmp_path: Path) -> None:
    first = make_handler(tmp_path / "first")
    second = make_handler(tmp_path / "second")
    events = (
        ("info", "audit", "append", "ok", 1),
        ("warning", "rotation", "rotate", "completed", 2.5),
        ("error", "recovery", "retry", "blocked", 3),
    )
    for values in events:
        assert first.log_event(
            severity=values[0],
            component=values[1],
            event=values[2],
            outcome=values[3],
            duration_ms=values[4],
        )
        assert second.log_event(
            severity=values[0],
            component=values[1],
            event=values[2],
            outcome=values[3],
            duration_ms=values[4],
        )
    assert first.active_path.read_bytes() == second.active_path.read_bytes()


def test_close_is_bounded_and_does_not_emit_after_close(tmp_path: Path) -> None:
    handler = make_handler(tmp_path)
    handler.close()
    assert not handler.log_event(
        severity="info",
        component="audit",
        event="append",
        outcome="ok",
    )
    assert handler.dropped_count == 1
