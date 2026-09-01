"""Stdlib-only POSIX maintenance gates for one synthetic R7 project.

The gate deliberately has one responsibility: coordinate project writers and
backup/restore operations with an advisory ``fcntl.flock``.  Ownership is the
open file descriptor, not a PID, heartbeat, or expiry timestamp.  A shared
lock is used by normal writers; an exclusive lock is used by backup/restore.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Optional, Union


DEFAULT_WAIT_SECONDS = 30.0
MAX_WAIT_SECONDS = 120.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.01


class MaintenanceGateError(RuntimeError):
    """Stable maintenance-gate failure."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = str(code)
        self.message = message or {
            "invalid_project_id": "医学监查项目标识无效。",
            "invalid_wait_timeout": "项目维护等待时间无效。",
            "project_busy_retry_later": "项目正在处理数据，请稍后重试",
            "maintenance_gate_unavailable": "项目维护门暂不可用。",
            "maintenance_gate_reentrant": "项目维护门重复获取。",
        }.get(self.code, "项目维护操作未能完成。")
        super().__init__(self.code)

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class ProjectBusyError(MaintenanceGateError):
    """The bounded wait elapsed before an exclusive/shared lock was acquired."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__("project_busy_retry_later", message)


def _canonical_project_id(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise MaintenanceGateError("invalid_project_id")
    if value != value.strip() or "\x00" in value:
        raise MaintenanceGateError("invalid_project_id")
    if any(ord(char) < 32 for char in value):
        raise MaintenanceGateError("invalid_project_id")
    # The lock filename is derived from the exact bytes, but a project path is
    # also used by callers.  Reject path syntax here rather than normalizing it.
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise MaintenanceGateError("invalid_project_id")
    return value


def lock_file_name(canonical_project_id: str) -> str:
    """Return the internal lock filename for the exact project identity."""

    project = _canonical_project_id(canonical_project_id)
    digest = hashlib.sha256(project.encode("utf-8")).hexdigest()
    return digest + ".lock"


class MaintenancePermit:
    """One releasable acquisition returned by :class:`ProjectMaintenanceGate`."""

    def __init__(self, gate: "ProjectMaintenanceGate", exclusive: bool) -> None:
        self._gate = gate
        self.exclusive = bool(exclusive)
        self._released = False

    @property
    def acquired(self) -> bool:
        return not self._released and self._gate.held

    def release(self) -> None:
        if not self._released:
            self._released = True
            self._gate.release()

    def __enter__(self) -> "MaintenancePermit":
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()


class ProjectMaintenanceGate:
    """A bounded, advisory shared/exclusive lock for one canonical project.

    ``root`` is the immutable runtime root containing ``.maintenance-locks``.
    The constructor does not open the lock.  ``shared()`` and ``exclusive()``
    return context-manager permits, while ``acquire`` is available to callers
    that need an explicitly held permit.
    """

    def __init__(
        self,
        root: Union[str, Path],
        canonical_project_id: str,
        *,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        timeout_seconds: Optional[float] = None,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.root = Path(root)
        self.canonical_project_id = _canonical_project_id(canonical_project_id)
        chosen_wait = wait_seconds if timeout_seconds is None else timeout_seconds
        try:
            wait = float(chosen_wait)
            poll = float(poll_interval_seconds)
        except (TypeError, ValueError) as exc:
            raise MaintenanceGateError("invalid_wait_timeout") from exc
        if wait < 0 or wait > MAX_WAIT_SECONDS or poll <= 0:
            raise MaintenanceGateError("invalid_wait_timeout")
        self.wait_seconds = wait
        self.poll_interval_seconds = min(poll, 0.25)
        self._event_callback = event_callback
        self._fd: Optional[int] = None
        self._exclusive: Optional[bool] = None
        self._depth = 0

    @property
    def lock_path(self) -> Path:
        """Internal lock path; never intended for a public product DTO."""

        return self.root / ".maintenance-locks" / lock_file_name(
            self.canonical_project_id
        )

    @property
    def held(self) -> bool:
        return self._fd is not None and self._depth > 0

    @property
    def exclusive_held(self) -> bool:
        return self.held and bool(self._exclusive)

    def _emit(self, event: str) -> None:
        callback = self._event_callback
        if callback is not None:
            callback(str(event))

    def acquire(
        self,
        exclusive: bool = True,
        *,
        mode: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> MaintenancePermit:
        """Acquire a shared or exclusive permit with monotonic bounded wait."""

        if mode is not None:
            if mode not in {"shared", "exclusive"}:
                raise MaintenanceGateError("maintenance_gate_unavailable")
            exclusive = mode == "exclusive"
        exclusive = bool(exclusive)
        if self.held:
            if self._exclusive != exclusive:
                raise MaintenanceGateError("maintenance_gate_reentrant")
            self._depth += 1
            return MaintenancePermit(self, exclusive)
        if not hasattr(fcntl, "flock"):
            raise MaintenanceGateError("maintenance_gate_unavailable")
        if timeout_seconds is None:
            wait = self.wait_seconds
        else:
            try:
                wait = float(timeout_seconds)
            except (TypeError, ValueError) as exc:
                raise MaintenanceGateError("invalid_wait_timeout") from exc
            if wait < 0 or wait > MAX_WAIT_SECONDS:
                raise MaintenanceGateError("invalid_wait_timeout")

        lock_path = self.lock_path
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            raise MaintenanceGateError("maintenance_gate_unavailable") from exc

        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        self._emit("waiting_for_project")
        deadline = time.monotonic() + wait
        try:
            while True:
                try:
                    fcntl.flock(fd, operation | fcntl.LOCK_NB)
                    self._fd = fd
                    self._exclusive = exclusive
                    self._depth = 1
                    self._emit("maintenance_acquired")
                    return MaintenancePermit(self, exclusive)
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EAGAIN):
                        raise MaintenanceGateError(
                            "maintenance_gate_unavailable"
                        ) from exc
                    if time.monotonic() >= deadline:
                        self._emit("maintenance_timeout")
                        raise ProjectBusyError()
                    time.sleep(min(self.poll_interval_seconds, max(0.0, deadline - time.monotonic())))
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise

    def release(self) -> None:
        """Release one nested permit; close the fd at the outermost release."""

        if not self.held:
            return
        self._depth -= 1
        if self._depth > 0:
            return
        fd = self._fd
        self._fd = None
        self._exclusive = None
        try:
            if fd is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            self._emit("maintenance_released")

    def shared(self) -> MaintenancePermit:
        return self.acquire(False)

    def exclusive(self) -> MaintenancePermit:
        return self.acquire(True)

    @contextmanager
    def lock(self, *, exclusive: bool = True) -> Iterator[MaintenancePermit]:
        permit = self.acquire(exclusive)
        try:
            yield permit
        finally:
            permit.release()

    def __enter__(self) -> "ProjectMaintenanceGate":
        self.acquire(True)
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()


@contextmanager
def project_maintenance_lock(
    root: Union[str, Path],
    canonical_project_id: str,
    *,
    exclusive: bool = True,
    wait_seconds: float = DEFAULT_WAIT_SECONDS,
    event_callback: Optional[Callable[[str], None]] = None,
) -> Iterator[MaintenancePermit]:
    """Convenience context manager for product write and maintenance paths."""

    gate = ProjectMaintenanceGate(
        root,
        canonical_project_id,
        wait_seconds=wait_seconds,
        event_callback=event_callback,
    )
    with gate.lock(exclusive=exclusive) as permit:
        yield permit


MaintenanceGate = ProjectMaintenanceGate
acquire_project_maintenance = project_maintenance_lock


__all__ = [
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "DEFAULT_WAIT_SECONDS",
    "MAX_WAIT_SECONDS",
    "MaintenanceGate",
    "MaintenanceGateError",
    "MaintenancePermit",
    "ProjectBusyError",
    "ProjectMaintenanceGate",
    "acquire_project_maintenance",
    "lock_file_name",
    "project_maintenance_lock",
]
