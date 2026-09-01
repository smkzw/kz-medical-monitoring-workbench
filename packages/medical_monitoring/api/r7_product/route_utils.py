"""Small route identity and workspace-path helpers for the R7 product API."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import Request

from ...runtime.run_entry import PROFILE_DB_NAME, RUN_BINDING_DB_NAME

R7_WORKSPACE_ROOT_NAME = "medical_monitoring_r7"


def _request_id(request: Request) -> str:
    supplied = str(request.headers.get("X-Request-ID", "") or "").strip()
    if supplied and len(supplied) <= 200 and all(
        char.isalnum() or char in "._:/-" for char in supplied
    ):
        return supplied
    return f"r7-request:{uuid4().hex}"


def _workspace_dir(runtime_dir: Path, canonical_project_id: str) -> Path:
    return Path(runtime_dir) / R7_WORKSPACE_ROOT_NAME / canonical_project_id


def _workspace_is_ready(workspace: Path) -> bool:
    return all(
        (workspace / database_name).is_file()
        for database_name in (PROFILE_DB_NAME, RUN_BINDING_DB_NAME)
    )


__all__ = [
    "R7_WORKSPACE_ROOT_NAME",
    "_request_id",
    "_workspace_dir",
    "_workspace_is_ready",
]
