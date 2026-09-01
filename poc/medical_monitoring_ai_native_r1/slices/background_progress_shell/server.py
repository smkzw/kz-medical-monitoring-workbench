"""Ephemeral loopback server exposing the audience progress shell.

Standard-library only.  The server binds ``127.0.0.1:0`` (OS-assigned
ephemeral port) and is meant to be closed right after each test or demo
session.  ``/progress`` reconstructs the audience view from SQLite on every
request via ``audience_snapshot``; the server never caches counts, so a
browser refresh always re-derives the authoritative view.

This is an isolated R1 POC integration seam, not a production local-server
decision.
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import urlsplit

SLICE_ROOT = Path(__file__).resolve().parent
POC_ROOT = SLICE_ROOT.parents[1]
SRC_ROOT = POC_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mm_r1.background_progress import audience_snapshot  # noqa: E402

_STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}


class ProgressShellServer:
    """Serve the shell page and the audience-only ``/progress`` endpoint."""

    def __init__(
        self,
        db_path: Any,
        artifact_dir: Any,
        run_id: str,
        *,
        feed_limit: int = 20,
    ) -> None:
        self.db_path = db_path
        self.artifact_dir = artifact_dir
        self.run_id = run_id
        self.feed_limit = feed_limit
        server = self

        class _Handler(BaseHTTPRequestHandler):
            server_version = "MMR1BackgroundProgressShell/1"

            def log_message(self, *args: Any) -> None:  # keep test output clean
                pass

            def do_GET(self) -> None:  # noqa: N802 - stdlib contract
                server._handle(self)

            def do_POST(self) -> None:  # noqa: N802
                self.send_error(405, "method not allowed")

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._httpd.daemon_threads = True
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        return int(self._httpd.server_address[1])

    @property
    def base_url(self) -> str:
        return "http://127.0.0.1:%d" % self.port

    def start(self) -> "ProgressShellServer":
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="mm-r1-progress-shell-http",
            daemon=True,
        )
        self._thread.start()
        return self

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def __enter__(self) -> "ProgressShellServer":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------- dispatch

    def _handle(self, handler: BaseHTTPRequestHandler) -> None:
        path = urlsplit(handler.path).path
        if path == "/progress":
            self._serve_progress(handler)
            return
        static = _STATIC_FILES.get(path)
        if static is not None:
            self._serve_static(handler, static)
            return
        handler.send_error(404, "not found")

    def _serve_progress(self, handler: BaseHTTPRequestHandler) -> None:
        try:
            view = audience_snapshot(
                self.db_path, self.artifact_dir, self.run_id,
                feed_limit=self.feed_limit,
            )
        except Exception:  # noqa: BLE001 - any projection failure stays unavailable
            payload = json.dumps(
                {"ok": False, "message": "暂时无法显示最新进度"},
                ensure_ascii=False,
            ).encode("utf-8")
            handler.send_response(503)
            handler.send_header("Content-Type", "application/json; charset=utf-8")
            handler.send_header("Cache-Control", "no-store")
            handler.send_header("Content-Length", str(len(payload)))
            handler.end_headers()
            handler.wfile.write(payload)
            return
        payload = json.dumps(view, ensure_ascii=False).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)

    def _serve_static(
        self, handler: BaseHTTPRequestHandler, static: Tuple[str, str],
    ) -> None:
        file_name, content_type = static
        body = (SLICE_ROOT / file_name).read_bytes()
        handler.send_response(200)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


__all__ = ["ProgressShellServer", "SLICE_ROOT"]
