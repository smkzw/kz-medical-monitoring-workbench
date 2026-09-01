"""Bounded, stdlib-only technical diagnostics for synthetic R7 runs.

This sink is deliberately separate from the project audit ledger.  It accepts
only a small enum-shaped record, emits one canonical JSON object per line, and
never exposes the logging message supplied by :mod:`logging`.  Sink failures
are process-local and bounded: callers receive ``False`` for a dropped record
and the logging handler never raises an I/O error into business code.
"""

from __future__ import annotations

import errno
import fcntl
import json
import logging
import math
import os
import re
import stat
import threading
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Deque, Iterable, Iterator, Mapping, Optional, Union


TECHNICAL_LOG_SCHEMA_VERSION = "mm-r7-slice09c-technical-log-v1"
SCHEMA_VERSION = TECHNICAL_LOG_SCHEMA_VERSION
TECHNICAL_LOG_DIR_NAME = ".technical-logs"
TECHNICAL_LOG_FILENAME = "medical-monitoring.jsonl"
TECHNICAL_LOG_LOCK_FILENAME = ".lock"
ACTIVE_MAX_BYTES = 1 * 1024 * 1024
ARCHIVE_COUNT = 4
MAX_RECORD_BYTES = 8 * 1024
ARCHIVE_RETENTION_DAYS = 7
ARCHIVE_RETENTION_SECONDS = ARCHIVE_RETENTION_DAYS * 24 * 60 * 60
FILE_MODE = 0o600
DIRECTORY_MODE = 0o700
DEGRADED_RING_SIZE = 16

# Explicit field order is useful to readers; ``sort_keys=True`` below makes
# the serialized representation canonical independent of insertion order.
TECHNICAL_LOG_FIELDS = (
    "schema",
    "timestamp",
    "severity",
    "component",
    "event",
    "outcome",
    "duration_ms",
    "segment_bytes",
    "degraded",
)
LOG_FIELDS = TECHNICAL_LOG_FIELDS

_SEVERITIES = frozenset({"debug", "info", "warning", "error", "critical"})
_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
# Technical component/event/outcome values are intentionally enum-shaped.  A
# token containing any of these segments would be an unsafe place to carry
# business identifiers or raw diagnostic content.
_SENSITIVE_TOKEN_SEGMENTS = frozenset(
    {
        "path",
        "paths",
        "workspace",
        "project",
        "subject",
        "center",
        "visit",
        "risk",
        "token",
        "prompt",
        "raw",
        "output",
        "model",
        "provider",
        "exception",
        "trace",
        "stack",
        "secret",
        "password",
        "sqlite",
        "database",
        "operation",
        "session",
        "eventid",
        "hash",
        "identifier",
    }
)
_PROTECTED_COMPONENTS = frozenset(
    {
        "runs",
        "run",
        "execution",
        "conference",
        "artifact",
        "artifacts",
        "evidence",
        "staging",
        "rollback",
        "backups",
        "backup-package",
        "workspace",
    }
)

PathLike = Union[str, os.PathLike[str]]
Clock = Callable[[], Union[datetime, float, int]]


class _SinkFailure(OSError):
    """Internal marker for an environmental sink failure."""


class _LockBusy(_SinkFailure):
    """The independent technical-log lock is currently held elsewhere."""


class _UnsafeLayout(_SinkFailure):
    """A known log path is not a safe regular file under the log directory."""


class BoundedTechnicalLogHandler(logging.Handler):
    """A bounded JSONL handler with non-blocking cross-process locking.

    ``runtime_root`` is the only writable root.  The handler creates exactly
    ``<runtime_root>/.technical-logs/medical-monitoring.jsonl`` plus at most
    four numbered archives and one lock file.  ``protected_roots`` should
    include any canonical project workspace or evidence roots known by the
    caller; all paths are compared after ``realpath`` resolution.

    The handler has no public payload channel.  ``emit`` reads only
    ``severity``, ``component``, ``event``, ``outcome``, ``duration_ms`` and
    ``degraded`` attributes from a ``LogRecord`` and never calls
    ``record.getMessage()``.
    """

    def __init__(
        self,
        runtime_root: PathLike,
        *,
        protected_roots: Iterable[PathLike] = (),
        protected_paths: Iterable[PathLike] = (),
        canonical_project_workspace: Optional[PathLike] = None,
        workspace_root: Optional[PathLike] = None,
        clock: Optional[Clock] = None,
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level=level)
        self._closed = False
        self.runtime_root = Path(os.path.realpath(os.fspath(runtime_root)))
        self.root = self.runtime_root
        self._protected_roots = self._coerce_protected_roots(
            protected_roots,
            protected_paths,
            canonical_project_workspace,
            workspace_root,
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._state_lock = threading.RLock()
        self._degraded = False
        self._dropped_count = 0
        self._degraded_ring: Deque[str] = deque(maxlen=DEGRADED_RING_SIZE)
        # Construction is the first explicit initialization.  Environmental
        # failures are represented in state rather than raised to callers.
        self.initialize()

    @staticmethod
    def _coerce_protected_roots(
        *groups: Union[Iterable[PathLike], Optional[PathLike]],
    ) -> tuple[Path, ...]:
        paths: list[Path] = []
        for group in groups:
            if group is None:
                continue
            if isinstance(group, (str, os.PathLike)):
                values: Iterable[PathLike] = (group,)
            else:
                values = group
            for value in values:
                if value is None:
                    continue
                try:
                    paths.append(Path(value))
                except (TypeError, ValueError):
                    # Invalid protection input makes the layout unusable; a
                    # sentinel path keeps this constructor non-throwing while
                    # initialize() records the degraded state.
                    paths.append(Path("\0"))
        return tuple(paths)

    @property
    def log_dir(self) -> Path:
        """The contract-defined technical-log directory."""

        return self.runtime_root / TECHNICAL_LOG_DIR_NAME

    @property
    def active_path(self) -> Path:
        return self.log_dir / TECHNICAL_LOG_FILENAME

    @property
    def archive_paths(self) -> tuple[Path, ...]:
        return tuple(self.log_dir / f"{TECHNICAL_LOG_FILENAME}.{i}" for i in range(1, ARCHIVE_COUNT + 1))

    @property
    def lock_path(self) -> Path:
        return self.log_dir / TECHNICAL_LOG_LOCK_FILENAME

    @property
    def degraded(self) -> bool:
        with self._state_lock:
            return self._degraded

    @property
    def is_degraded(self) -> bool:
        return self.degraded

    @property
    def dropped_count(self) -> int:
        with self._state_lock:
            return self._dropped_count

    @property
    def degraded_reasons(self) -> tuple[str, ...]:
        with self._state_lock:
            return tuple(self._degraded_ring)

    def status(self) -> Mapping[str, Any]:
        """Return bounded sink state without paths or record content."""

        with self._state_lock:
            return {
                "degraded": self._degraded,
                "dropped_count": self._dropped_count,
                "degraded_reasons": tuple(self._degraded_ring),
            }

    def initialize(self) -> bool:
        """Retry safe layout setup and clear degraded mode on success.

        Initialization is the only operation that exits degraded mode.  It
        takes the same non-blocking lock used by writes before pruning stale
        archives, so a concurrent process is never waited on or modified.
        """

        with self._state_lock:
            if self._closed:
                self._remember_drop("closed")
                return False
            try:
                self._prepare_layout()
                with self._cross_process_lock():
                    self._validate_known_entries(include_lock=True)
                    self._prune_expired_archives(self._now_seconds())
                self._degraded = False
                return True
            except _LockBusy:
                self._set_degraded("lock_busy")
            except _UnsafeLayout:
                self._set_degraded("unsafe_layout")
            except (OSError, ValueError, TypeError):
                self._set_degraded("initialize_failed")
            except Exception:
                self._set_degraded("initialize_failed")
            return False

    # Explicit spelling for callers that prefer the lifecycle name.
    reinitialize = initialize

    def emit(self, record: logging.LogRecord) -> bool:
        """Write one bounded record, returning ``False`` when it is dropped."""

        with self._state_lock:
            if self._closed:
                self._remember_drop("closed")
                return False
            if self._degraded:
                self._remember_drop("degraded")
                return False
            try:
                body = self._record_body(record)
            except (TypeError, ValueError, OverflowError):
                self._remember_drop("invalid_record")
                return False
            except Exception:
                self._remember_drop("invalid_record")
                return False

            try:
                with self._cross_process_lock():
                    self._validate_known_entries(include_lock=True)
                    self._prune_expired_archives(self._now_seconds())
                    current_size = self._active_size()
                    line = self._serialize_with_segment_size(body, current_size)
                    if len(line) > MAX_RECORD_BYTES:
                        self._remember_drop("record_too_large")
                        return False
                    if current_size + len(line) > ACTIVE_MAX_BYTES:
                        self._rotate()
                        current_size = self._active_size()
                        line = self._serialize_with_segment_size(body, current_size)
                        if len(line) > MAX_RECORD_BYTES:
                            self._remember_drop("record_too_large")
                            return False
                    self._write_active(line)
                    return True
            except _LockBusy:
                self._set_degraded("lock_busy", count=True)
            except _UnsafeLayout:
                self._set_degraded("unsafe_layout", count=True)
            except (OSError, ValueError, TypeError, OverflowError):
                self._set_degraded("sink_failed", count=True)
            except Exception:
                self._set_degraded("sink_failed", count=True)
            return False

    def log_event(
        self,
        *,
        severity: str,
        component: str,
        event: str,
        outcome: str,
        duration_ms: Union[int, float] = 0,
        degraded: bool = False,
        timestamp: Optional[Union[datetime, float, int, str]] = None,
    ) -> bool:
        """Emit a record using only the fixed nine-field contract."""

        try:
            record = logging.LogRecord(
                name=str(component) if isinstance(component, str) else "invalid",
                level=logging.NOTSET,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None,
            )
            record.levelname = str(severity)
            record.severity = severity
            record.component = component
            record.event = event
            record.outcome = outcome
            record.duration_ms = duration_ms
            record.degraded = degraded
            record.technical_timestamp = self._clock() if timestamp is None else timestamp
            return self.emit(record)
        except Exception:
            with self._state_lock:
                self._remember_drop("invalid_record")
            return False

    emit_event = log_event
    write_event = log_event

    def handleError(self, record: logging.LogRecord) -> None:  # noqa: N802
        """Never route sink failures to stderr/stdout via logging."""

        return None

    def flush(self) -> None:
        # Each successful write fsyncs the active file before returning.
        return None
    def close(self) -> None:
        with self._state_lock:
            self._closed = True
            super().close()


    def _record_body(self, record: logging.LogRecord) -> dict[str, Any]:
        severity = getattr(record, "severity", None)
        if severity is None:
            severity = getattr(record, "levelname", "")
        severity = self._normalize_severity(severity)

        component = self._normalize_token(
            getattr(record, "component", getattr(record, "name", "")),
            "component",
        )
        event = self._normalize_token(
            getattr(record, "event", getattr(record, "event_name", "record")),
            "event",
        )
        outcome = self._normalize_token(
            getattr(record, "outcome", "ok"),
            "outcome",
        )
        duration_ms = self._normalize_duration(getattr(record, "duration_ms", 0))
        degraded = getattr(record, "degraded", False)
        if not isinstance(degraded, bool):
            raise ValueError("degraded must be bool")

        timestamp_value = getattr(record, "technical_timestamp", None)
        if timestamp_value is None:
            timestamp_value = getattr(record, "created", None)
        timestamp = self._normalize_timestamp(timestamp_value)
        return {
            "schema": TECHNICAL_LOG_SCHEMA_VERSION,
            "timestamp": timestamp,
            "severity": severity,
            "component": component,
            "event": event,
            "outcome": outcome,
            "duration_ms": duration_ms,
            "segment_bytes": 0,
            "degraded": degraded,
        }

    @staticmethod
    def _normalize_severity(value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("invalid severity")
        normalized = value.strip().lower()
        if normalized == "warn":
            normalized = "warning"
        if normalized not in _SEVERITIES:
            raise ValueError("invalid severity")
        return normalized

    @staticmethod
    def _normalize_token(value: Any, field: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"invalid {field}")
        if not _TOKEN_RE.fullmatch(value):
            raise ValueError(f"invalid {field}")
        segments = set(re.split(r"[_.-]", value.lower()))
        if segments & _SENSITIVE_TOKEN_SEGMENTS:
            raise ValueError(f"unsafe {field}")
        return value

    @staticmethod
    def _normalize_duration(value: Any) -> Union[int, float]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("invalid duration")
        if not math.isfinite(float(value)) or value < 0:
            raise ValueError("invalid duration")
        if float(value) > 2**31:
            raise ValueError("invalid duration")
        if isinstance(value, int) or float(value).is_integer():
            return int(value)
        return float(value)

    def _normalize_timestamp(self, value: Any) -> str:
        if value is None:
            value = self._clock()
        if isinstance(value, datetime):
            moment = value
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            moment = moment.astimezone(timezone.utc)
        elif isinstance(value, str):
            try:
                text = value.strip()
                if text.endswith("Z"):
                    text = text[:-1] + "+00:00"
                moment = datetime.fromisoformat(text)
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=timezone.utc)
                moment = moment.astimezone(timezone.utc)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid timestamp") from exc
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(float(value)):
                raise ValueError("invalid timestamp")
            moment = datetime.fromtimestamp(float(value), tz=timezone.utc)
        else:
            raise ValueError("invalid timestamp")
        return moment.isoformat(timespec="microseconds").replace("+00:00", "Z")

    @staticmethod
    def _serialize_with_segment_size(body: dict[str, Any], current_size: int) -> bytes:
        candidate = max(0, int(current_size))
        line = b""
        # The decimal width of segment_bytes makes this a tiny fixed-point
        # calculation; three iterations are normally sufficient.
        for _ in range(8):
            body["segment_bytes"] = candidate
            line = (
                json.dumps(
                    body,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
                + b"\n"
            )
            next_candidate = max(0, int(current_size)) + len(line)
            if next_candidate == candidate:
                return line
            candidate = next_candidate
        body["segment_bytes"] = candidate
        return (
            json.dumps(
                body,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )

    def _now_seconds(self) -> float:
        value = self._clock()
        if isinstance(value, datetime):
            moment = value
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            return moment.timestamp()
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if math.isfinite(float(value)):
                return float(value)
        raise ValueError("invalid clock")

    def _prepare_layout(self) -> None:
        runtime = Path(os.path.realpath(os.fspath(self.runtime_root)))
        expected = runtime / TECHNICAL_LOG_DIR_NAME
        # Check the canonical destination before creating either the runtime
        # root or its technical-log child.  A protected/evidence path must not
        # be touched merely because a handler was constructed there.
        self._assert_unprotected_location(runtime)
        self._assert_unprotected_location(expected)
        if not runtime.exists():
            runtime.mkdir(parents=True, mode=DIRECTORY_MODE)
        if not runtime.is_dir():
            raise _UnsafeLayout("runtime root is not a directory")

        try:
            info = os.lstat(expected)
        except FileNotFoundError:
            os.mkdir(expected, DIRECTORY_MODE)
        else:
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise _UnsafeLayout("technical log directory is unsafe")

        expected_real = Path(os.path.realpath(os.fspath(expected)))
        if expected_real != expected:
            raise _UnsafeLayout("technical log directory realpath changed")
        if not self._is_within(expected_real, runtime):
            raise _UnsafeLayout("technical log directory escaped runtime root")
        self._assert_unprotected_location(expected_real)

    def _assert_unprotected_location(self, path: Path) -> None:
        for protected in self._protected_roots:
            protected_real = Path(os.path.realpath(os.fspath(protected)))
            if self._is_within(path, protected_real):
                raise _UnsafeLayout("technical log location is protected")
        if any(part.lower() in _PROTECTED_COMPONENTS for part in path.parts):
            raise _UnsafeLayout("technical log location is protected")

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            return os.path.commonpath((os.fspath(path), os.fspath(root))) == os.fspath(root)
        except (TypeError, ValueError):
            return False


    def _validate_known_entries(self, *, include_lock: bool) -> None:
        paths = (self.active_path, *self.archive_paths)
        if include_lock:
            paths += (self.lock_path,)
        for path in paths:
            self._validate_known_entry(path)

    def _validate_known_entry(self, path: Path) -> Optional[os.stat_result]:
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise _UnsafeLayout("known path cannot be inspected") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise _UnsafeLayout("known path is not a regular file")
        if stat.S_IMODE(info.st_mode) != FILE_MODE:
            raise _UnsafeLayout("known path has unsafe mode")
        real = Path(os.path.realpath(os.fspath(path)))
        if real != path or not self._is_within(real, Path(os.path.realpath(os.fspath(self.log_dir)))):
            raise _UnsafeLayout("known path realpath escaped log directory")
        return info

    def _open_lock(self) -> int:
        self._prepare_layout()
        flags = os.O_WRONLY | os.O_CREAT
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(os.fspath(self.lock_path), flags, FILE_MODE)
        except OSError as exc:
            raise _SinkFailure("lock open failed") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != FILE_MODE:
                raise _UnsafeLayout("lock file is unsafe")
            if Path(os.path.realpath(os.fspath(self.lock_path))) != self.lock_path:
                raise _UnsafeLayout("lock realpath escaped")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise _LockBusy("technical log lock is busy") from exc
                raise _SinkFailure("lock acquire failed") from exc
            return fd
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise

    @contextmanager
    def _cross_process_lock(self) -> Iterator[None]:
        fd = self._open_lock()
        try:
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                # Unlock errors still make the sink unhealthy, but must never
                # leak into the business caller during context cleanup.
                self._set_degraded("lock_release_failed")
            finally:
                try:
                    os.close(fd)
                except OSError:
                    self._set_degraded("lock_close_failed")

    def _active_size(self) -> int:
        info = self._validate_known_entry(self.active_path)
        return 0 if info is None else int(info.st_size)

    def _prune_expired_archives(self, now_seconds: float) -> None:
        cutoff = float(now_seconds) - ARCHIVE_RETENTION_SECONDS
        changed = False
        for path in self.archive_paths:
            info = self._validate_known_entry(path)
            if info is None:
                continue
            if float(info.st_mtime) < cutoff:
                try:
                    os.unlink(os.fspath(path))
                except OSError as exc:
                    raise _SinkFailure("archive cleanup failed") from exc
                changed = True
        if changed:
            self._fsync_directory()

    def _rotate(self) -> None:
        active_info = self._validate_known_entry(self.active_path)
        if active_info is None or active_info.st_size <= 0:
            return
        # Validate every known destination before making any change.  This is
        # what prevents a symlink, directory, or insecure file from being
        # overwritten during a normal rotation.
        self._validate_known_entries(include_lock=True)
        paths = self.archive_paths
        if self._validate_known_entry(paths[-1]) is not None:
            self._safe_unlink(paths[-1])
        for index in range(ARCHIVE_COUNT - 1, 0, -1):
            source = paths[index - 1]
            destination = paths[index]
            if self._validate_known_entry(source) is None:
                continue
            if self._validate_known_entry(destination) is not None:
                self._safe_unlink(destination)
            try:
                os.rename(os.fspath(source), os.fspath(destination))
            except OSError as exc:
                raise _SinkFailure("archive rename failed") from exc
        try:
            if self._validate_known_entry(self.active_path) is not None:
                if self._validate_known_entry(paths[0]) is not None:
                    self._safe_unlink(paths[0])
                os.rename(os.fspath(self.active_path), os.fspath(paths[0]))
        except OSError as exc:
            raise _SinkFailure("active rename failed") from exc
        self._fsync_directory()

    def _safe_unlink(self, path: Path) -> None:
        info = self._validate_known_entry(path)
        if info is None:
            return
        try:
            os.unlink(os.fspath(path))
        except OSError as exc:
            raise _SinkFailure("safe unlink failed") from exc

    def _open_active_for_append(self) -> int:
        self._prepare_layout()
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(os.fspath(self.active_path), flags, FILE_MODE)
        except OSError as exc:
            raise _SinkFailure("active open failed") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != FILE_MODE:
                raise _UnsafeLayout("active file is unsafe")
            if Path(os.path.realpath(os.fspath(self.active_path))) != self.active_path:
                raise _UnsafeLayout("active realpath escaped")
            return fd
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise

    def _write_active(self, line: bytes) -> None:
        if len(line) > MAX_RECORD_BYTES:
            raise ValueError("record exceeds bound")
        fd = self._open_active_for_append()
        before = 0
        complete = False
        try:
            before = int(os.fstat(fd).st_size)
            if before + len(line) > ACTIVE_MAX_BYTES:
                raise _SinkFailure("active segment capacity changed")
            offset = 0
            try:
                while offset < len(line):
                    written = os.write(fd, line[offset:])
                    if written <= 0:
                        raise OSError(errno.EIO, "short technical log write")
                    offset += written
            except BaseException:
                try:
                    os.ftruncate(fd, before)
                except OSError:
                    pass
                raise
            complete = True
            os.fsync(fd)
            if int(os.fstat(fd).st_size) != before + len(line):
                raise _SinkFailure("active size mismatch")
        finally:
            try:
                os.close(fd)
            except OSError:
                if complete:
                    raise _SinkFailure("active close failed")

    def _fsync_directory(self) -> None:
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        try:
            fd = os.open(os.fspath(self.log_dir), flags)
        except OSError as exc:
            raise _SinkFailure("log directory open failed") from exc
        try:
            os.fsync(fd)
        except OSError as exc:
            raise _SinkFailure("log directory fsync failed") from exc
        finally:
            try:
                os.close(fd)
            except OSError as exc:
                raise _SinkFailure("log directory close failed") from exc

    def _remember_drop(self, reason: str) -> None:
        self._dropped_count += 1
        self._degraded_ring.append(str(reason))

    def _set_degraded(self, reason: str, *, count: bool = False) -> None:
        self._degraded = True
        self._degraded_ring.append(str(reason))
        if count:
            self._dropped_count += 1


TechnicalLogHandler = BoundedTechnicalLogHandler
TechnicalLog = BoundedTechnicalLogHandler


def create_technical_log_handler(
    runtime_root: PathLike,
    **kwargs: Any,
) -> BoundedTechnicalLogHandler:
    """Construct a bounded handler without exposing a logging payload API."""

    return BoundedTechnicalLogHandler(runtime_root, **kwargs)


__all__ = [
    "ACTIVE_MAX_BYTES",
    "ARCHIVE_COUNT",
    "ARCHIVE_RETENTION_DAYS",
    "ARCHIVE_RETENTION_SECONDS",
    "BoundedTechnicalLogHandler",
    "DEGRADED_RING_SIZE",
    "DIRECTORY_MODE",
    "FILE_MODE",
    "LOG_FIELDS",
    "MAX_RECORD_BYTES",
    "SCHEMA_VERSION",
    "TECHNICAL_LOG_DIR_NAME",
    "TECHNICAL_LOG_FILENAME",
    "TECHNICAL_LOG_FIELDS",
    "TECHNICAL_LOG_LOCK_FILENAME",
    "TECHNICAL_LOG_SCHEMA_VERSION",
    "TechnicalLog",
    "TechnicalLogHandler",
    "create_technical_log_handler",
]
