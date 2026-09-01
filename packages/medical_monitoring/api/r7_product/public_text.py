"""Audience-text sanitization for the R7 product API."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from ...runtime.run_entry import RunEntryError
from .contracts import ProductPublicationError

_SECRET_FIELDS = {
    "credential",
    "credential_value",
    "credential_secret",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "authorization",
    "bearer",
    "access_token",
    "secret_key",
}
_FORBIDDEN_PUBLIC = _SECRET_FIELDS | {
    "modeoutput",
    "risk_instance",
    "patientjourney",
    "query_draft",
    "timeline",
    "canonical_fact",
    "report_claim",
}
_SECRET_VALUE = re.compile(r"(?i)(sk-[a-z0-9]{8,}|bearer\s+\S+|api_key=|password=|token=)")
_RUNTIME_INTERNAL_TOKENS = (
    "owner",
    "lease",
    "generation",
    "thread",
    "pid",
    "token",
    "sqlite",
    "provider",
    "model",
    "manifest_revision",
    "run_id",
    "project_id",
)

def _public_continuity_text(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.casefold()
    if _SECRET_VALUE.search(text) or any(
        marker in lowered
        for marker in (
            "run_id",
            "run_ref",
            "snapshot_ref",
            "cutoff_ref",
            "packet_digest",
            "authority_hash",
            "artifact_member",
            "source_snapshot_sha256",
            "file://",
            "/users/",
            "traceback",
            "stdout",
            "stderr",
        )
    ):
        raise ProductPublicationError("continuity_unavailable")
    return text

def _projection(result: Any, *, replayed: bool = False) -> dict[str, Any]:
    if isinstance(result, Mapping):
        body = dict(result)
    else:
        value = getattr(result, "profile", None)
        if not isinstance(value, Mapping):
            value = getattr(result, "binding", None)
        if not isinstance(value, Mapping):
            raise RunEntryError("internal_error")
        body = dict(value)
        if replayed:
            body["replayed"] = bool(getattr(result, "replayed"))
    lowered_keys = {str(key).lower() for key in body}
    if lowered_keys & _FORBIDDEN_PUBLIC:
        raise RunEntryError("internal_error")
    blob = json.dumps(body, ensure_ascii=False)
    if _SECRET_VALUE.search(blob) or "credential_value" in blob.lower():
        raise RunEntryError("internal_error")
    return body

__all__ = [
    "_SECRET_FIELDS",
    "_FORBIDDEN_PUBLIC",
    "_SECRET_VALUE",
    "_RUNTIME_INTERNAL_TOKENS",
    "_public_continuity_text",
    "_projection",
]

