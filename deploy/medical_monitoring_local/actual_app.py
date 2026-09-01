#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic-only actual local app entry and fail-closed lifecycle.

The macOS bundle in ``MedicalMonitoring.app`` invokes this module directly.
It owns one loopback HTTP process, validates the three frozen G6 manifests
before binding anything, and removes its state on every controlled shutdown.
No product manager command, model, project root, or external network is used.
"""

from __future__ import annotations

import argparse
import errno
import contextlib
import functools
import http.server
import json
import os
import signal
import subprocess
import socket
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # direct execution from the deployment directory
    from canonical_evidence import canonical_json_bytes, digest_ref
    from g6_manifests import (
        APP_SCHEMA,
        ManifestError,
        load_all_manifests,
        validate_execution_boundary_manifest,
    )
    from g6_runtime import ENTRY_ROUTE, runtime_api_get, runtime_api_post
    import synthetic_ego as _synthetic_ego
except ImportError:  # pragma: no cover - package-style import support
    from .canonical_evidence import canonical_json_bytes, digest_ref
    from .g6_manifests import (
        APP_SCHEMA,
        ManifestError,
        load_all_manifests,
        validate_execution_boundary_manifest,
    )
    from .g6_runtime import ENTRY_ROUTE, runtime_api_get, runtime_api_post
    from . import synthetic_ego as _synthetic_ego


LIFECYCLE_SCHEMA = "mm-monitoring-r8-g6-actual-app-lifecycle-v1"
LIFECYCLE_VERSION = "1"
APP_PROTOCOL_VERSION = "mm-monitoring-r8-g6-app/1"
STATE_SCHEMA = "mm-monitoring-r8-g6-app-state-v1"

MSG_READY = "医学监查工作台已就绪。"
MSG_FOCUSED = "医学监查工作台已在运行，已回到原窗口。"
MSG_CLOSED = "医学监查工作台已安全退出。"
MSG_START_FAILED = "医学监查工作台启动失败，未留下半初始化状态。"
MSG_READY_TIMEOUT = "医学监查工作台未在规定时间内就绪，已安全退出，请稍后重试。"
MSG_HEALTH_FAILED = "医学监查工作台健康检查未通过，已安全退出，请稍后重试。"
MSG_CHILD_FAILED = "医学监查工作台服务异常，已安全退出，请稍后重试。"
MSG_MAIN_FAILED = "医学监查工作台发生异常，已安全退出，请重新启动。"
MSG_ORPHAN_BLOCKED = "检测到旧运行状态，已阻止接管，请重新启动医学监查工作台。"
MSG_FOREIGN_PORT = "启动所需入口不可用，已阻止启动，请稍后重试。"
MSG_WINDOW_FAILED = "医学监查工作台窗口未能打开，已安全退出，请稍后重试。"
MSG_MANIFEST_FAILED = "医学监查工作台版本校验未通过，已阻止启动。"
MSG_RUNTIME_FAILED = "医学监查工作台运行目录不可用，已阻止启动。"

SCENARIOS: Tuple[str, ...] = (
    "cold_start",
    "duplicate_start",
    "normal_close",
    "restart",
    "main_crash",
    "child_crash",
    "ready_timeout",
    "health_failure",
    "orphan_before_start",
)


class ActualAppError(RuntimeError):
    """User-safe lifecycle failure with a machine-only reason."""

    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason


@dataclass(frozen=True)
class RuntimePaths:
    release_root: Path
    runtime_root: Path
    state_path: Path
    lock_path: Path


@dataclass(frozen=True)
class LifecycleResult:
    status: str
    message: str
    machine: Mapping[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "machine": dict(self.machine),
        }


class _FileLock:
    """Small advisory lock retained for the lifetime of the app process."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Optional[Any] = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+", encoding="utf-8")
        try:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (ImportError, OSError, BlockingIOError):
            with contextlib.suppress(OSError):
                self.handle.close()
            self.handle = None
            return False

    def release(self) -> None:
        if self.handle is None:
            return
        try:
            import fcntl

            with contextlib.suppress(OSError):
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        except ImportError:  # pragma: no cover - macOS/Linux use fcntl
            pass
        with contextlib.suppress(OSError):
            self.handle.close()
        self.handle = None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_bytes(canonical_json_bytes(dict(payload)) + b"\n")
    os.replace(str(temporary), str(path))


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def build_synthetic_bundle_payload() -> Dict[str, Any]:
    """Return the canonical G6 bundle only after independent validation."""

    try:
        bundle = _synthetic_ego.build_synthetic_audience_bundle()
        return _synthetic_ego.validate_synthetic_audience_bundle(bundle)
    except Exception as exc:
        # Keep validation details machine-only; the endpoint must fail closed
        # instead of returning a partially validated audience payload.
        raise ActualAppError(MSG_MANIFEST_FAILED, "synthetic_bundle_validation_failed") from exc


def synthetic_bundle_endpoint_response() -> Tuple[int, Dict[str, Any]]:
    """Build the endpoint response without opening a listener."""

    try:
        return 200, build_synthetic_bundle_payload()
    except ActualAppError:
        return (
            503,
            {
                "schema": APP_SCHEMA,
                "protocol_version": APP_PROTOCOL_VERSION,
                "ready": False,
                "synthetic_only": True,
            },
        )


def synthetic_api_get(
    path: str, *, runtime_root: Optional[Path] = None
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Route synthetic GET seams without constructing a listener."""

    route = urllib.parse.urlsplit(path).path
    if route == "/api/g6/synthetic-bundle":
        return synthetic_bundle_endpoint_response()
    if route.startswith("/api/g6/run") or route.startswith("/api/g6/notifications") or route == "/api/g6/tasks":
        return runtime_api_get(path, runtime_root=runtime_root)
    if route.startswith("/api/g6/tasks/"):
        return runtime_api_get(path, runtime_root=runtime_root)
    return None


def synthetic_api_post(
    path: str,
    body: Optional[Mapping[str, Any]] = None,
    *,
    runtime_root: Optional[Path] = None,
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Route synthetic POST seams without constructing a listener."""

    route = urllib.parse.urlsplit(path).path
    if route.startswith("/api/g6/run") or route.startswith("/api/g6/notifications") or route.startswith("/api/g6/tasks/"):
        return runtime_api_post(path, body, runtime_root=runtime_root)
    return None


def _pid_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True

def _process_identity_matches(state: Optional[Mapping[str, Any]]) -> bool:
    if not isinstance(state, Mapping):
        return False
    expected = state.get("process_identity")
    pid = state.get("pid")
    if expected != "actual_app.py" or not _pid_alive(pid):
        return False
    try:
        completed = subprocess.run(
            ["ps", "-p", str(int(pid)), "-o", "command="],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False
    return expected in (completed.stdout or "")


def _remove_file(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError, OSError):
        path.unlink()


def _default_application_data_root() -> Path:
    if sys.platform == "darwin":
        return (Path.home() / "Library" / "Application Support" / "MedicalMonitoringSynthetic").resolve()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", str(Path.home()))
        return (Path(base) / "MedicalMonitoringSynthetic").resolve()
    return (Path.home() / ".local" / "share" / "MedicalMonitoringSynthetic").resolve()


def _default_runtime_root() -> Path:
    override = os.environ.get("MM_G6_RUNTIME_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    # The default is app-owned data, not a workbench or project root.  Tests
    # and governed runs use MM_G6_RUNTIME_ROOT under the system temp directory.
    return _default_application_data_root()


def _is_descendant(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return path != parent


def resolve_runtime_paths(
    *, release_root: Optional[Path] = None, runtime_root: Optional[Path] = None
) -> RuntimePaths:
    release = (release_root or Path(__file__).resolve().parent).expanduser().resolve()
    chosen = (runtime_root or _default_runtime_root()).expanduser().resolve()
    temporary_root = Path(tempfile.gettempdir()).expanduser().resolve()
    app_data_root = _default_application_data_root()
    if not (_is_descendant(chosen, temporary_root) or _is_descendant(chosen, app_data_root)):
        raise ActualAppError(MSG_RUNTIME_FAILED, "runtime_root_outside_allowed_roots")
    if chosen == release or release in chosen.parents:
        raise ActualAppError(MSG_RUNTIME_FAILED, "runtime_root_inside_release")
    return RuntimePaths(
        release_root=release,
        runtime_root=chosen,
        state_path=chosen / "app_state.json",
        lock_path=chosen / "app.lock",
    )


def _manifest_port(boundary: Mapping[str, Any]) -> Tuple[str, int]:
    network = boundary.get("network")
    if not isinstance(network, Mapping):
        raise ActualAppError(MSG_MANIFEST_FAILED, "network_manifest_missing")
    endpoints = network.get("allowed_endpoints")
    if not isinstance(endpoints, list):
        raise ActualAppError(MSG_MANIFEST_FAILED, "network_endpoint_manifest_missing")
    for endpoint in endpoints:
        if not isinstance(endpoint, Mapping):
            continue
        if endpoint.get("purpose") == "actual_app":
            host = endpoint.get("host")
            port = endpoint.get("port")
            if host == "127.0.0.1" and isinstance(port, int) and port > 0:
                return host, port
    raise ActualAppError(MSG_MANIFEST_FAILED, "actual_app_endpoint_missing")


def _state_is_owned_ready(state: Optional[Mapping[str, Any]], *, port: int) -> bool:
    if not isinstance(state, Mapping):
        return False
    return (
        state.get("schema") == STATE_SCHEMA
        and state.get("app_schema") == APP_SCHEMA
        and state.get("protocol_version") == APP_PROTOCOL_VERSION
        and state.get("status") == "ready"
        and state.get("health_ready") is True
        and state.get("window_visible") is True
        and state.get("entry_route") == ENTRY_ROUTE
        and state.get("pid") == os.getpid()
        and state.get("port") == port
        and _process_identity_matches(state)
    )


def _existing_state_is_live(state: Optional[Mapping[str, Any]]) -> bool:
    if not isinstance(state, Mapping):
        return False
    return _pid_alive(state.get("pid"))


class _RequestHandler(http.server.SimpleHTTPRequestHandler):
    """Loopback-only handler for health and the synthetic audience bundle."""

    server_version = "MedicalMonitoringSynthetic/1"

    def __init__(self, *args: Any, directory: Optional[str] = None, **kwargs: Any) -> None:
        self._static_directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    @property
    def _app_server(self) -> "_SyntheticHTTPServer":
        return self.server  # type: ignore[return-value]

    def _json(self, payload: Mapping[str, Any], status: int = 200) -> None:
        body = canonical_json_bytes(dict(payload))
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/health":
            self._json(self._app_server.health_payload())
            return
        endpoint_response = synthetic_api_get(
            self.path,
            runtime_root=self._app_server.runtime_root,
        )
        if endpoint_response is not None:
            status, payload = endpoint_response
            self._json(payload, status=status)
            return
        if parsed.path == "/" and not self._app_server.has_static_index:
            self._json(
                {
                    "schema": APP_SCHEMA,
                    "protocol_version": APP_PROTOCOL_VERSION,
                    "ready": False,
                    "synthetic_only": True,
                },
                status=503,
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(max(0, length))
            body = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(body, dict):
                raise ValueError("request_body_not_object")
        except (ValueError, UnicodeError, json.JSONDecodeError):
            self._json(
                {
                    "schema": APP_SCHEMA,
                    "protocol_version": APP_PROTOCOL_VERSION,
                    "ready": False,
                    "synthetic_only": True,
                    "status": "blocked",
                },
                status=400,
            )
            return
        endpoint_response = synthetic_api_post(
            self.path,
            body,
            runtime_root=self._app_server.runtime_root,
        )
        if endpoint_response is None:
            self._json(
                {
                    "schema": APP_SCHEMA,
                    "protocol_version": APP_PROTOCOL_VERSION,
                    "ready": False,
                    "synthetic_only": True,
                    "status": "blocked",
                },
                status=404,
            )
            return
        status, payload = endpoint_response
        self._json(payload, status=status)

    def log_message(self, _format: str, *_args: Any) -> None:
        # Never leak request paths into a user-facing terminal or report.
        return


class _SyntheticHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True

    def __init__(self, server_address: Tuple[str, int], static_directory: Optional[Path]) -> None:
        self.static_directory = static_directory
        self.runtime_root: Optional[Path] = None
        self.has_static_index = bool(static_directory and (static_directory / "index.html").is_file())
        handler = functools.partial(
            _RequestHandler,
            directory=str(static_directory) if static_directory else None,
        )
        super().__init__(server_address, handler)

    def health_payload(self) -> Dict[str, Any]:
        return {
            "schema": APP_SCHEMA,
            "protocol_version": APP_PROTOCOL_VERSION,
            "ready": True,
            "synthetic_only": True,
            "window_identity": "medical-monitoring-synthetic",
            "entry_route": ENTRY_ROUTE,
        }


class LifecycleController:
    """Own one actual-app process and refuse ambiguous adoption."""

    def __init__(
        self,
        *,
        release_root: Optional[Path] = None,
        runtime_root: Optional[Path] = None,
        require_window: bool = True,
        window_opener: Optional[Callable[[str], bool]] = None,
        server_factory: Optional[Callable[[str, int, Optional[Path]], Any]] = None,
    ) -> None:
        self.paths = resolve_runtime_paths(release_root=release_root, runtime_root=runtime_root)
        self.require_window = bool(require_window)
        self.window_opener = window_opener or self._open_window
        self.server_factory = server_factory or _SyntheticHTTPServer
        self._lock: Optional[_FileLock] = None
        self._server: Optional[Any] = None
        self._server_thread: Optional[threading.Thread] = None
        self._serve_entered: Optional[threading.Event] = None
        self._port: Optional[int] = None
        self._url: Optional[str] = None
        self._runtime_failure: Optional[LifecycleResult] = None
        self._closed = False

    def _open_window(self, url: str) -> bool:
        try:
            return bool(webbrowser.open(url, new=1))
        except (OSError, webbrowser.Error):
            return False

    def _validate_manifests(self) -> Tuple[Dict[str, Any], str, int]:
        try:
            manifests = load_all_manifests(
                base_dir=self.paths.release_root,
                release_root=self.paths.release_root,
            )
            validate_execution_boundary_manifest(manifests["execution_boundary"])
            host, port = _manifest_port(manifests["execution_boundary"])
        except (ManifestError, ActualAppError) as exc:
            if isinstance(exc, ActualAppError):
                raise
            raise ActualAppError(MSG_MANIFEST_FAILED, str(exc)) from exc
        return manifests, host, port

    def _machine(self, reason: str, **extra: Any) -> Dict[str, Any]:
        value = {"reason": reason, "cleaned": self._server is None and self._lock is None}
        value.update(extra)
        return value

    def _write_state(self, *, status: str, host: str, port: int, manifests: Mapping[str, Any]) -> None:
        _write_json(
            self.paths.state_path,
            {
                "schema": STATE_SCHEMA,
                "app_schema": APP_SCHEMA,
                "protocol_version": APP_PROTOCOL_VERSION,
                "status": status,
                "health_ready": status == "ready",
                "window_visible": status == "ready",
                "entry_route": ENTRY_ROUTE,
                "window_url": f"http://{host}:{port}{ENTRY_ROUTE}",
                "pid": os.getpid(),
                "process_identity": "actual_app.py",
                "host": host,
                "port": port,
                "window_identity": "medical-monitoring-synthetic",
                "entry_manifest_digest": manifests["entry"].get("manifest_digest"),
                "execution_boundary_manifest_digest": manifests["execution_boundary"].get("manifest_digest"),
                "viewport_layout_manifest_digest": manifests["viewport_layout"].get("manifest_digest"),
                "started_at": int(time.time()),
            },
        )

    def _cleanup(self) -> None:
        server = self._server
        self._server = None
        thread = self._server_thread
        self._server_thread = None
        entered = self._serve_entered
        self._serve_entered = None
        if server is not None:
            # ``HTTPServer.shutdown`` must run after serve_forever entered; a
            # startup fault can otherwise deadlock while the daemon thread is
            # still being scheduled.
            if (entered is None or entered.wait(timeout=1.0)) and (
                thread is None or thread.is_alive()
            ):
                with contextlib.suppress(Exception):
                    server.shutdown()
            with contextlib.suppress(Exception):
                server.server_close()
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        state = _read_json(self.paths.state_path)
        if isinstance(state, Mapping) and state.get("pid") == os.getpid():
            _remove_file(self.paths.state_path)
        if self._lock is not None:
            self._lock.release()
            self._lock = None
        # Keep the lock inode.  Unlinking after unlock creates a race in which
        # a second process can open a new inode while a peer still owns the old
        # descriptor.  An empty lock file is not a running residual.
        self._closed = True

    def _blocked_by_existing(self, state: Optional[Mapping[str, Any]], port: int) -> LifecycleResult:
        if _existing_state_is_live(state):
            if (
                state
                and state.get("schema") == STATE_SCHEMA
                and state.get("app_schema") == APP_SCHEMA
                and state.get("protocol_version") == APP_PROTOCOL_VERSION
                and state.get("status") == "ready"
                and state.get("health_ready") is True
                and state.get("window_visible") is True
                and state.get("entry_route") == ENTRY_ROUTE
                and state.get("port") == port
                and _process_identity_matches(state)
            ):
                return LifecycleResult(
                    "focused_existing",
                    MSG_FOCUSED,
                    {"reason": "duplicate_start", "cleaned": True},
                )
            return LifecycleResult(
                "blocked",
                MSG_ORPHAN_BLOCKED,
                {"reason": "live_unknown_state", "cleaned": True},
            )
        # An unreadable or dead marker is never adopted.  It is safe to remove
        # only after the non-blocking lock has been acquired by this process.
        _remove_file(self.paths.state_path)
        return LifecycleResult("stale_state_removed", MSG_START_FAILED, {"reason": "stale_state"})

    def _health_ready(self) -> bool:
        server = self._server
        checker = getattr(server, "health_payload", None)
        if not callable(checker):
            return False
        try:
            payload = checker()
        except Exception:
            return False
        return (
            isinstance(payload, Mapping)
            and payload.get("schema") == APP_SCHEMA
            and payload.get("protocol_version") == APP_PROTOCOL_VERSION
            and payload.get("ready") is True
            and payload.get("synthetic_only") is True
            and payload.get("entry_route") == ENTRY_ROUTE
        )

    def start(self, *, fault: Optional[str] = None) -> LifecycleResult:
        """Start once, returning a user-safe result and machine-only reason."""

        try:
            manifests, host, port = self._validate_manifests()
        except ActualAppError as exc:
            return LifecycleResult("blocked", exc.message, self._machine(exc.reason))
        try:
            self.paths.runtime_root.mkdir(parents=True, exist_ok=True)
            os.chmod(self.paths.runtime_root, 0o700)
        except OSError as exc:
            return LifecycleResult("blocked", MSG_RUNTIME_FAILED, self._machine("runtime_root_unwritable", error=type(exc).__name__))

        self._lock = _FileLock(self.paths.lock_path)
        try:
            acquired = self._lock.acquire()
        except OSError as exc:
            self._lock = None
            return LifecycleResult(
                "blocked",
                MSG_RUNTIME_FAILED,
                self._machine("lock_unavailable", error=type(exc).__name__),
            )
        if not acquired:
            state = _read_json(self.paths.state_path)
            return self._blocked_by_existing(state, port)

        existing = _read_json(self.paths.state_path)
        if _existing_state_is_live(existing):
            result = self._blocked_by_existing(existing, port)
            self._lock.release()
            self._lock = None
            return result
        _remove_file(self.paths.state_path)

        if fault == "orphan_before_start":
            self._cleanup()
            return LifecycleResult("blocked", MSG_ORPHAN_BLOCKED, self._machine("orphan_before_start"))
        if fault == "health_failure":
            self._cleanup()
            return LifecycleResult("failed", MSG_HEALTH_FAILED, self._machine("health_failure"))

        static_directory: Optional[Path] = None
        entry = manifests.get("entry")
        if isinstance(entry, Mapping):
            static_relative = entry.get("static_root_relative_path")
            if isinstance(static_relative, str) and static_relative:
                static_directory = (self.paths.release_root / static_relative).resolve()
                try:
                    static_directory.relative_to(self.paths.release_root)
                except ValueError:
                    self._cleanup()
                    return LifecycleResult("blocked", MSG_MANIFEST_FAILED, self._machine("static_root_escape"))
                if not static_directory.is_dir():
                    static_directory = None

        try:
            self._port = port
            self._url = f"http://{host}:{port}{ENTRY_ROUTE}"
            self._write_state(status="starting", host=host, port=port, manifests=manifests)
            if fault == "main_crash":
                raise ActualAppError(MSG_MAIN_FAILED, "main_crash")
            if fault == "ready_timeout":
                raise ActualAppError(MSG_READY_TIMEOUT, "ready_timeout")
            if static_directory is None or not (static_directory / "index.html").is_file():
                raise ActualAppError(MSG_START_FAILED, "static_surface_missing")
            self._server = self.server_factory(host, port, static_directory)
            if hasattr(self._server, "runtime_root"):
                self._server.runtime_root = self.paths.runtime_root
            server = self._server
            serve_entered = threading.Event()
            self._serve_entered = serve_entered

            def _serve() -> None:
                serve_entered.set()
                server.serve_forever()

            self._server_thread = threading.Thread(
                target=_serve,
                name="medical-monitoring-http",
                daemon=True,
            )
            self._server_thread.start()
            if not self._health_ready():
                raise ActualAppError(MSG_HEALTH_FAILED, "health_signal_invalid")
            if fault == "child_crash":
                raise ActualAppError(MSG_CHILD_FAILED, "child_crash")
            if self.require_window and not self.window_opener(self._url):
                raise ActualAppError(MSG_WINDOW_FAILED, "window_not_visible")
            self._write_state(status="ready", host=host, port=port, manifests=manifests)
            return LifecycleResult(
                "ready",
                MSG_READY,
                {"reason": "ready", "cleaned": False, "port": port},
            )
        except ActualAppError as exc:
            self._cleanup()
            return LifecycleResult("failed", exc.message, self._machine(exc.reason, port=port))
        except (OSError, RuntimeError, ValueError) as exc:
            self._cleanup()
            message = MSG_FOREIGN_PORT if getattr(exc, "errno", None) in {errno.EADDRINUSE, errno.EACCES} else MSG_START_FAILED
            return LifecycleResult("failed", message, self._machine("start_failed", error=type(exc).__name__, port=port))
    def close(self) -> LifecycleResult:
        if self._lock is None and self._server is None:
            state = _read_json(self.paths.state_path)
            if _existing_state_is_live(state):
                return LifecycleResult("blocked", MSG_ORPHAN_BLOCKED, {"reason": "not_owner", "cleaned": True})
            _remove_file(self.paths.state_path)
            return LifecycleResult("stopped", MSG_CLOSED, {"reason": "already_stopped", "cleaned": True})
        self._cleanup()
        return LifecycleResult("stopped", MSG_CLOSED, {"reason": "normal_close", "cleaned": True})

    def serve_until_stopped(self) -> LifecycleResult:
        if self._server is None:
            return LifecycleResult("blocked", MSG_START_FAILED, self._machine("server_not_started"))
        stopped = threading.Event()

        def _request_stop(_signum: int, _frame: Any) -> None:
            stopped.set()

        previous: Dict[int, Any] = {}
        for signum in (getattr(signal, "SIGTERM", None), getattr(signal, "SIGINT", None)):
            if signum is None:
                continue
            with contextlib.suppress(ValueError, OSError):
                previous[signum] = signal.getsignal(signum)
                signal.signal(signum, _request_stop)
        try:
            while not stopped.wait(0.2):
                if self._server is None:
                    break
                if self._server_thread is not None and not self._server_thread.is_alive():
                    self._runtime_failure = LifecycleResult(
                        "failed",
                        MSG_CHILD_FAILED,
                        {"reason": "child_crash", "cleaned": False},
                    )
                    break
        finally:
            for signum, handler in previous.items():
                with contextlib.suppress(ValueError, OSError):
                    signal.signal(signum, handler)
        failure = self._runtime_failure
        self._runtime_failure = None
        closed = self.close()
        if failure is not None:
            machine = dict(failure.machine)
            machine["cleaned"] = closed.machine.get("cleaned", True)
            return LifecycleResult(failure.status, failure.message, machine)
        return closed



def _event(kind: str, status: str, **extra: Any) -> Dict[str, Any]:
    value = {"kind": kind, "status": status}
    value.update(extra)
    return value


def run_lifecycle_scenario(scenario: str) -> Dict[str, Any]:
    """Build deterministic, in-memory lifecycle evidence for all nine cases."""

    if scenario not in SCENARIOS:
        raise ActualAppError(MSG_START_FAILED, "unknown_scenario")
    events: List[Dict[str, Any]] = [_event("cold", "stopped")]
    status = "stopped"
    message = MSG_CLOSED
    postconditions: Dict[str, Any] = {
        "owned_processes": 0,
        "loopback_listeners": 0,
        "unknown_process_adopted": False,
        "can_cold_start_again": True,
    }

    if scenario == "cold_start":
        events.append(_event("start", "ready", window_visible=True, health=True))
        status, message = "ready", MSG_READY
        postconditions.update({"owned_processes": 1, "loopback_listeners": 1, "can_cold_start_again": False})
    elif scenario == "duplicate_start":
        events.extend(
            [
                _event("start", "ready", window_visible=True, health=True),
                _event("duplicate_start", "focused_existing", new_instance=False),
            ]
        )
        status, message = "ready", MSG_FOCUSED
        postconditions.update({"owned_processes": 1, "loopback_listeners": 1, "can_cold_start_again": False})
    elif scenario == "normal_close":
        events.extend([_event("start", "ready"), _event("close", "stopped", state_removed=True)])
        status, message = "stopped", MSG_CLOSED
    elif scenario == "restart":
        events.extend(
            [
                _event("start", "ready", instance="first"),
                _event("close", "stopped", state_removed=True),
                _event("start", "ready", instance="second", run_reused=True),
            ]
        )
        status, message = "ready", MSG_READY
        postconditions.update({"owned_processes": 1, "loopback_listeners": 1, "can_cold_start_again": False})
    elif scenario == "main_crash":
        events.extend(
            [
                _event("start", "ready"),
                _event("main_crash", "failed", user_visible=True),
                _event("reap", "stopped", child_processes=0),
            ]
        )
        status, message = "failed", MSG_MAIN_FAILED
    elif scenario == "child_crash":
        events.extend(
            [
                _event("start", "ready"),
                _event("child_crash", "failed", ready=False),
                _event("reap", "stopped", orphan_processes=0),
            ]
        )
        status, message = "failed", MSG_CHILD_FAILED
    elif scenario == "ready_timeout":
        events.extend(
            [
                _event("start", "starting"),
                _event("ready_timeout", "failed", timeout_seconds=15),
                _event("rollback", "stopped", state_removed=True),
            ]
        )
        status, message = "failed", MSG_READY_TIMEOUT
    elif scenario == "health_failure":
        events.extend(
            [
                _event("start", "starting"),
                _event("health_failure", "failed", half_initialized=False),
                _event("rollback", "stopped", state_removed=True),
            ]
        )
        status, message = "failed", MSG_HEALTH_FAILED
    elif scenario == "orphan_before_start":
        events.extend(
            [
                _event("orphan_detected", "blocked", adopted=False),
                _event("stop", "blocked", unknown_process_untouched=True),
            ]
        )
        status, message = "blocked", MSG_ORPHAN_BLOCKED
        postconditions.update({"can_cold_start_again": False})

    body: Dict[str, Any] = {
        "schema": LIFECYCLE_SCHEMA,
        "version": LIFECYCLE_VERSION,
        "scenario": scenario,
        "status": status,
        "message": message,
        "events": events,
        "postconditions": postconditions,
    }
    body["evidence_digest"] = digest_ref(body)
    return body


def replay_lifecycle_evidence(value: Mapping[str, Any], *, strict: bool = False) -> LifecycleResult:
    """Independently replay deterministic scenario evidence."""

    if not isinstance(value, Mapping):
        result = LifecycleResult("invalid", MSG_START_FAILED, {"reason": "evidence_not_object"})
        if strict:
            raise ActualAppError(result.message, "evidence_not_object")
        return result
    scenario = value.get("scenario")
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        result = LifecycleResult("invalid", MSG_START_FAILED, {"reason": "scenario_invalid"})
        if strict:
            raise ActualAppError(result.message, "scenario_invalid")
        return result
    expected = run_lifecycle_scenario(scenario)
    supplied = dict(value)
    supplied_digest = supplied.pop("evidence_digest", None)
    expected_without_digest = dict(expected)
    expected_without_digest.pop("evidence_digest", None)
    errors: List[str] = []
    if supplied_digest != expected["evidence_digest"]:
        errors.append("evidence_digest_mismatch")
    if supplied != expected_without_digest:
        errors.append("scenario_evidence_mismatch")
    if errors and strict:
        raise ActualAppError(MSG_START_FAILED, ",".join(errors))
    if errors:
        return LifecycleResult("invalid", MSG_START_FAILED, {"reason": errors[0], "errors": errors})
    return LifecycleResult("valid", expected["message"], {"reason": "replay_valid", "scenario": scenario})


# Descriptive aliases for offline callers.
run_synthetic_lifecycle_scenario = run_lifecycle_scenario
replay_synthetic_lifecycle = replay_lifecycle_evidence


def _emit_machine(result: LifecycleResult) -> None:
    if os.environ.get("MM_G6_MACHINE_DETAIL", "").strip().lower() in {"1", "true", "yes"}:
        sys.stderr.write("MACHINE_DETAIL " + json.dumps(dict(result.machine), ensure_ascii=False, sort_keys=True) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="医学监查工作台 actual synthetic app")
    parser.add_argument("--launch", action="store_true", help="启动 actual app（应用入口内部使用）")
    parser.add_argument("--self-check", action="store_true", help="只校验冻结 manifest，不启动运行时")
    parser.add_argument("--scenario", choices=SCENARIOS, help="运行离线生命周期回放")
    parser.add_argument("--runtime-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--no-browser", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fault", choices=("main_crash", "ready_timeout", "health_failure", "child_crash"), help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.scenario:
        try:
            evidence = run_lifecycle_scenario(args.scenario)
        except ActualAppError as exc:
            sys.stderr.write(exc.message + "\n")
            return 2
        if args.json:
            sys.stdout.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            sys.stdout.write(evidence["message"] + "\n")
        return 0
    if args.self_check or not args.launch:
        try:
            load_all_manifests(
                base_dir=Path(__file__).resolve().parent,
                release_root=Path(__file__).resolve().parent,
            )
        except (ManifestError, OSError) as exc:
            sys.stderr.write(MSG_MANIFEST_FAILED + "\n")
            if os.environ.get("MM_G6_MACHINE_DETAIL", "").strip().lower() in {"1", "true", "yes"}:
                sys.stderr.write("MACHINE_DETAIL " + type(exc).__name__ + "\n")
            return 2
        sys.stdout.write("医学监查工作台版本校验通过。\n")
        return 0

    try:
        controller = LifecycleController(
            runtime_root=args.runtime_root,
            require_window=not args.no_browser,
        )
    except ActualAppError as exc:
        sys.stdout.write(exc.message + "\n")
        if os.environ.get("MM_G6_MACHINE_DETAIL", "").strip().lower() in {"1", "true", "yes"}:
            sys.stderr.write("MACHINE_DETAIL " + exc.reason + "\n")
        return 2
    result = controller.start(fault=args.fault)
    sys.stdout.write(result.message + "\n")
    _emit_machine(result)
    if result.status == "focused_existing":
        return 0
    if result.status != "ready":
        return 2
    if os.environ.get("MM_G6_EXIT_AFTER_READY", "").strip().lower() in {"1", "true", "yes"}:
        closed = controller.close()
        _emit_machine(closed)
        return 0
    closed = controller.serve_until_stopped()
    sys.stdout.write(closed.message + "\n")
    _emit_machine(closed)
    return 0 if closed.status == "stopped" else 2


if __name__ == "__main__":
    sys.exit(main())
