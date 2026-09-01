"""R7 slice-01 immutable versioned ExecutionProfile layer persistence.

Stdlib-only SQLite store for the four harness profile layers (precedence):

    global_default < capability_agent < project < run_override

Records are append-only versions. A new revision inserts a new row; prior
revisions remain readable. Public serialization accepts credential references
only and never a credential value field. Public and audit projections never
emit credential *values* (opaque ``credential_ref`` strings are allowed).

Effective freeze and Monitoring Run binding live in ``mm_r7.run_binding``
(worker_02). This module persists layer overrides and projects them.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "mm-r7-profile-store-v1"

LAYER_GLOBAL_DEFAULT = "global_default"
LAYER_CAPABILITY_AGENT = "capability_agent"
LAYER_PROJECT = "project"
LAYER_RUN_OVERRIDE = "run_override"

LAYER_PRECEDENCE: Tuple[str, ...] = (
    LAYER_GLOBAL_DEFAULT,
    LAYER_CAPABILITY_AGENT,
    LAYER_PROJECT,
    LAYER_RUN_OVERRIDE,
)

LAYER_KINDS: Tuple[str, ...] = LAYER_PRECEDENCE

# Global default uses the sentinel scope key ``*`` (contract tests / freeze).
GLOBAL_SCOPE_KEY = "*"

# Mirrors R6 ExecutionProfileLayer registered fields (accepted adapter).
_LAYER_FIELDS: Tuple[str, ...] = (
    "profile_id",
    "profile_revision",
    "capability_id",
    "requested_provider",
    "requested_model",
    "user_config_name",
    "effective_selector",
    "reasoning_effort",
    "timeout_seconds",
    "allowed_tools",
    "context_isolation",
    "credential_ref",
    "adapter_id",
    "adapter_version",
    "fallback_profile_ids",
)

_LAYER_FIELD_SET = frozenset(_LAYER_FIELDS)

_TUPLE_FIELDS = frozenset({"allowed_tools", "fallback_profile_ids"})

# Reject explicit secret-value field names at the persistence boundary.
_FORBIDDEN_VALUE_FIELDS = frozenset(
    {
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
)

# Scalar fields that must not be empty string when explicitly supplied.
_NON_EMPTY_WHEN_SET = frozenset(
    {
        "profile_id",
        "profile_revision",
        "capability_id",
        "user_config_name",
        "context_isolation",
        "credential_ref",
        "adapter_id",
        "adapter_version",
        "requested_provider",
        "requested_model",
        "effective_selector",
        "reasoning_effort",
    }
)

_SECRET_REF_TOKENS = ("sk-", "api_key=", "bearer ", "password=", "token=")

_DDL = """
CREATE TABLE IF NOT EXISTS profile_store_meta (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_layer_versions (
    layer_kind TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    revision INTEGER NOT NULL,
    record_id TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    PRIMARY KEY (layer_kind, scope_key, revision)
);

CREATE INDEX IF NOT EXISTS idx_profile_layer_latest
    ON profile_layer_versions (layer_kind, scope_key, revision);
"""


class ProfileStoreError(RuntimeError):
    """Fail-closed error for profile-layer persistence or projection."""


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def canonical_json_bytes(obj: Any) -> bytes:
    """Stable UTF-8 JSON bytes (sorted keys, compact separators)."""
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_hex(data: Union[bytes, str]) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def content_digest(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def _normalize_scope_key(layer_kind: str, scope_key: Any) -> str:
    if not isinstance(scope_key, str):
        raise ProfileStoreError("illegal_scope_key_type")
    raw = scope_key
    if layer_kind == LAYER_GLOBAL_DEFAULT:
        # Canonical global scope is ``*``; empty/"global" normalize to ``*``.
        if raw in ("", "global", GLOBAL_SCOPE_KEY):
            return GLOBAL_SCOPE_KEY
        raise ProfileStoreError("global_default_scope_must_be_star")
    if raw == "" or raw != raw.strip() or "\x00" in raw:
        raise ProfileStoreError("empty_or_illegal_scope_key")
    return raw


def _reject_secret_ref(credential_ref: str) -> None:
    lowered = credential_ref.lower()
    if any(token in lowered for token in _SECRET_REF_TOKENS):
        raise ProfileStoreError("credential_ref_must_not_be_secret_value")


def _normalize_fields(fields: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and canonicalize an override payload.

    ``None`` values are omitted (inherit). Empty string is kept only when the
    field allows it; required identity fields fail closed when empty.
    Unknown fields and credential-value fields fail closed.
    """
    if not isinstance(fields, Mapping):
        raise ProfileStoreError("invalid_payload_type")
    for key in fields.keys():
        name = str(key)
        lowered = name.lower()
        if lowered in _FORBIDDEN_VALUE_FIELDS or name in _FORBIDDEN_VALUE_FIELDS:
            raise ProfileStoreError("credential_value_field_forbidden:%s" % name)
        if name not in _LAYER_FIELD_SET:
            raise ProfileStoreError("unknown_override_field:%s" % name)

    out: Dict[str, Any] = {}
    for name in _LAYER_FIELDS:
        if name not in fields:
            continue
        value = fields[name]
        if value is None:
            continue
        if name in _TUPLE_FIELDS:
            if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
                raise ProfileStoreError("illegal_tuple_field:%s" % name)
            normalized = tuple(str(v) for v in value)
            if any(not t or t != t.strip() or " " in t or "," in t for t in normalized):
                raise ProfileStoreError("illegal_tool_or_fallback_token:%s" % name)
            out[name] = list(normalized)
            continue
        if name == "timeout_seconds":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ProfileStoreError("illegal_timeout")
            if value <= 0:
                raise ProfileStoreError("illegal_timeout")
            out[name] = value
            continue
        if name == "credential_ref":
            text = str(value)
            if text == "" or text != text.strip():
                raise ProfileStoreError("empty_credential_ref")
            _reject_secret_ref(text)
            out[name] = text
            continue
        text = str(value)
        if name in _NON_EMPTY_WHEN_SET and (
            text == "" or text != text.strip()
        ):
            raise ProfileStoreError("empty_required_field:%s" % name)
        out[name] = text
    return out


def _record_id_for(
    layer_kind: str, scope_key: str, revision: int, digest: str
) -> str:
    body = {
        "content_digest": digest,
        "layer_kind": layer_kind,
        "revision": revision,
        "scope_key": scope_key,
        "schema_version": SCHEMA_VERSION,
    }
    return "plv_%s" % content_digest(body)[:32]


# ---------------------------------------------------------------------------
# Record + projections
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProfileLayerRecord:
    """One immutable versioned profile-layer row."""

    layer_kind: str
    scope_key: str
    revision: int
    record_id: str
    fields: Dict[str, Any]
    content_digest: str

    def as_override_dict(self) -> Dict[str, Any]:
        """Return freeze-ready overrides (tuples restored for list fields)."""
        out: Dict[str, Any] = {}
        for key, value in self.fields.items():
            if key in _TUPLE_FIELDS:
                out[key] = tuple(value)
            else:
                out[key] = value
        return out


def _row_to_record(row: sqlite3.Row) -> ProfileLayerRecord:
    try:
        payload = json.loads(row["payload_json"])
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProfileStoreError("corrupt_payload_json:%s" % exc) from exc
    if not isinstance(payload, dict):
        raise ProfileStoreError("corrupt_payload_json")
    normalized = _normalize_fields(payload)
    if normalized != payload:
        raise ProfileStoreError("stored_payload_not_canonical")
    digest = content_digest(payload)
    if digest != row["content_digest"]:
        raise ProfileStoreError("content_digest_mismatch")
    expected_id = _record_id_for(
        row["layer_kind"], row["scope_key"], int(row["revision"]), digest
    )
    if expected_id != row["record_id"]:
        raise ProfileStoreError("record_id_mismatch")
    return ProfileLayerRecord(
        layer_kind=str(row["layer_kind"]),
        scope_key=str(row["scope_key"]),
        revision=int(row["revision"]),
        record_id=str(row["record_id"]),
        fields=dict(payload),
        content_digest=str(row["content_digest"]),
    )


def _public_projection_body(record: ProfileLayerRecord) -> Dict[str, Any]:
    """API-ready public view: user-facing names; credential_ref as reference only."""
    fields = record.fields
    body: Dict[str, Any] = {
        "layer_kind": record.layer_kind,
        "scope_key": record.scope_key,
        "revision": record.revision,
        "record_id": record.record_id,
        "content_digest": record.content_digest,
        "schema_version": SCHEMA_VERSION,
    }
    # Public: user_config_name and other config; omit provider/model/selector.
    for name in (
        "profile_id",
        "profile_revision",
        "capability_id",
        "user_config_name",
        "reasoning_effort",
        "timeout_seconds",
        "allowed_tools",
        "context_isolation",
        "credential_ref",
        "adapter_id",
        "adapter_version",
        "fallback_profile_ids",
    ):
        if name not in fields:
            continue
        value = fields[name]
        body[name] = list(value) if name in _TUPLE_FIELDS else value
    return {k: body[k] for k in sorted(body.keys())}


def _audit_projection_body(record: ProfileLayerRecord) -> Dict[str, Any]:
    """Audit view: may include selector/provider/model and digests."""
    fields = record.fields
    body: Dict[str, Any] = {
        "layer_kind": record.layer_kind,
        "scope_key": record.scope_key,
        "revision": record.revision,
        "record_id": record.record_id,
        "content_digest": record.content_digest,
        "revision_digest": record.content_digest,
        "schema_version": SCHEMA_VERSION,
    }
    for name in _LAYER_FIELDS:
        if name not in fields:
            continue
        value = fields[name]
        body[name] = list(value) if name in _TUPLE_FIELDS else value
    return {k: body[k] for k in sorted(body.keys())}


def assert_projection_has_no_credential_values(projection: Mapping[str, Any]) -> None:
    """Fail closed if a projection appears to carry credential values."""
    forbidden = _FORBIDDEN_VALUE_FIELDS | {"credential_value"}
    for key in projection.keys():
        if str(key).lower() in forbidden or str(key) in forbidden:
            raise ProfileStoreError("projection_contains_credential_value_field:%s" % key)
    cred = projection.get("credential_ref")
    if isinstance(cred, str) and cred:
        _reject_secret_ref(cred)
    blob = canonical_json_bytes(dict(projection)).decode("utf-8").lower()
    if re.search(r"sk-[a-z0-9]{8,}", blob):
        raise ProfileStoreError("projection_leaks_secret_pattern")


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


def _assert_current_schema(path: Path) -> None:
    """Reject an existing non-current file before any writable SQLite call."""
    if not path.exists():
        return
    from .schema_manifest import SchemaClassification, inspect_member

    report = inspect_member(path, "profile_store")
    if report.classification is not SchemaClassification.CURRENT:
        raise ProfileStoreError(
            "unsupported_schema_version:%s" % report.reason_code
        )


class ProfileStore:
    """Append-only SQLite persistence for versioned profile layers."""

    def __init__(self, db_path: Union[str, Path]) -> None:
        self._path = Path(db_path)
        _assert_current_schema(self._path)
        if self._path.parent and str(self._path.parent) not in ("", "."):
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self.open()

    @property
    def path(self) -> Path:
        return self._path

    def open(self) -> None:
        if self._conn is not None:
            return
        _assert_current_schema(self._path)
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(_DDL)
        row = conn.execute(
            "SELECT value FROM profile_store_meta WHERE key = ?",
            ("schema_version",),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO profile_store_meta (key, value) VALUES (?, ?)",
                ("schema_version", SCHEMA_VERSION),
            )
            conn.commit()
        elif str(row["value"]) != SCHEMA_VERSION:
            conn.close()
            raise ProfileStoreError(
                "unsupported_schema_version:%s" % row["value"]
            )
        self._conn = conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def reopen(self) -> None:
        """Close and reopen the same database path (reopen-parity helper)."""
        self.close()
        self.open()

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise ProfileStoreError("store_closed")
        return self._conn

    def append_revision(
        self,
        layer_kind: str,
        scope_key: str,
        fields: Mapping[str, Any],
    ) -> ProfileLayerRecord:
        """Append a new immutable revision for ``(layer_kind, scope_key)``."""
        kind = str(layer_kind)
        if kind not in LAYER_KINDS:
            raise ProfileStoreError("unknown_layer_kind:%s" % kind)
        scope = _normalize_scope_key(kind, scope_key)
        payload = _normalize_fields(fields)
        if not payload:
            raise ProfileStoreError("empty_override_payload")
        digest = content_digest(payload)
        conn = self._require_conn()
        latest = conn.execute(
            "SELECT MAX(revision) AS m FROM profile_layer_versions "
            "WHERE layer_kind = ? AND scope_key = ?",
            (kind, scope),
        ).fetchone()
        next_rev = 1 if latest["m"] is None else int(latest["m"]) + 1
        record_id = _record_id_for(kind, scope, next_rev, digest)
        payload_json = canonical_json_bytes(payload).decode("utf-8")
        try:
            conn.execute(
                "INSERT INTO profile_layer_versions "
                "(layer_kind, scope_key, revision, record_id, "
                "payload_json, content_digest) VALUES (?, ?, ?, ?, ?, ?)",
                (kind, scope, next_rev, record_id, payload_json, digest),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ProfileStoreError("append_conflict:%s" % exc) from exc
        return ProfileLayerRecord(
            layer_kind=kind,
            scope_key=scope,
            revision=next_rev,
            record_id=record_id,
            fields=payload,
            content_digest=digest,
        )

    # Alias retained for earlier draft call sites.
    def append_layer(
        self,
        layer_kind: str,
        fields: Mapping[str, Any],
        *,
        scope_key: str = GLOBAL_SCOPE_KEY,
    ) -> ProfileLayerRecord:
        return self.append_revision(layer_kind, scope_key, fields)

    def get_revision(
        self, layer_kind: str, scope_key: str, revision: int
    ) -> ProfileLayerRecord:
        kind = str(layer_kind)
        if kind not in LAYER_KINDS:
            raise ProfileStoreError("unknown_layer_kind:%s" % kind)
        scope = _normalize_scope_key(kind, scope_key)
        if not isinstance(revision, int) or isinstance(revision, bool) or revision <= 0:
            raise ProfileStoreError("illegal_revision")
        conn = self._require_conn()
        row = conn.execute(
            "SELECT * FROM profile_layer_versions "
            "WHERE layer_kind = ? AND scope_key = ? AND revision = ?",
            (kind, scope, revision),
        ).fetchone()
        if row is None:
            raise ProfileStoreError(
                "revision_not_found:%s:%s:%s" % (kind, scope, revision)
            )
        return _row_to_record(row)

    def latest_revision(
        self, layer_kind: str, scope_key: str
    ) -> Optional[ProfileLayerRecord]:
        kind = str(layer_kind)
        if kind not in LAYER_KINDS:
            raise ProfileStoreError("unknown_layer_kind:%s" % kind)
        scope = _normalize_scope_key(kind, scope_key)
        conn = self._require_conn()
        row = conn.execute(
            "SELECT * FROM profile_layer_versions "
            "WHERE layer_kind = ? AND scope_key = ? "
            "ORDER BY revision DESC LIMIT 1",
            (kind, scope),
        ).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def get_latest(
        self, layer_kind: str, *, scope_key: str = GLOBAL_SCOPE_KEY
    ) -> Optional[ProfileLayerRecord]:
        return self.latest_revision(layer_kind, scope_key)

    def list_revisions(
        self, layer_kind: str, scope_key: str
    ) -> Tuple[ProfileLayerRecord, ...]:
        kind = str(layer_kind)
        if kind not in LAYER_KINDS:
            raise ProfileStoreError("unknown_layer_kind:%s" % kind)
        scope = _normalize_scope_key(kind, scope_key)
        conn = self._require_conn()
        rows = conn.execute(
            "SELECT * FROM profile_layer_versions "
            "WHERE layer_kind = ? AND scope_key = ? "
            "ORDER BY revision ASC",
            (kind, scope),
        ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def public_projection(self, record: ProfileLayerRecord) -> Dict[str, Any]:
        body = _public_projection_body(record)
        assert_projection_has_no_credential_values(body)
        return body

    def audit_projection(self, record: ProfileLayerRecord) -> Dict[str, Any]:
        body = _audit_projection_body(record)
        assert_projection_has_no_credential_values(body)
        return body

    def load_precedence_layers(
        self,
        *,
        capability_scope: str = "",
        project_scope: str = "",
        run_scope: str = "",
    ) -> Tuple[Optional[ProfileLayerRecord], ...]:
        """Return latest layers in ``LAYER_PRECEDENCE`` order (None if absent)."""
        global_rec = self.latest_revision(LAYER_GLOBAL_DEFAULT, GLOBAL_SCOPE_KEY)
        cap_rec = (
            self.latest_revision(LAYER_CAPABILITY_AGENT, capability_scope)
            if capability_scope
            else None
        )
        proj_rec = (
            self.latest_revision(LAYER_PROJECT, project_scope)
            if project_scope
            else None
        )
        run_rec = (
            self.latest_revision(LAYER_RUN_OVERRIDE, run_scope) if run_scope else None
        )
        return (global_rec, cap_rec, proj_rec, run_rec)

    def seed_builtin_global_default(self) -> ProfileLayerRecord:
        """Append R6 default MTPLX medium fields as global_default if empty."""
        existing = self.latest_revision(LAYER_GLOBAL_DEFAULT, GLOBAL_SCOPE_KEY)
        if existing is not None:
            return existing
        try:
            from mm_r6 import agent_harness as ah
        except ImportError as exc:
            raise ProfileStoreError(
                "mm_r6_unavailable_for_builtin_seed"
            ) from exc
        layer = ah.registered_profile_layer(ah.PROFILE_DEFAULT_ID)
        return self.append_revision(
            LAYER_GLOBAL_DEFAULT, GLOBAL_SCOPE_KEY, layer.as_override_dict()
        )

    def seed_deepseek_capability_layer(
        self, *, scope_key: str = "medical_monitoring_harness"
    ) -> ProfileLayerRecord:
        """Append explicit DeepSeek V4 Flash max as a capability_agent layer."""
        try:
            from mm_r6 import agent_harness as ah
        except ImportError as exc:
            raise ProfileStoreError(
                "mm_r6_unavailable_for_builtin_seed"
            ) from exc
        layer = ah.deepseek_profile_layer()
        return self.append_revision(
            LAYER_CAPABILITY_AGENT, scope_key, layer.as_override_dict()
        )


# Module-level projection helpers (same bodies as store methods).
def public_projection(record: ProfileLayerRecord) -> Dict[str, Any]:
    body = _public_projection_body(record)
    assert_projection_has_no_credential_values(body)
    return body


def audit_projection(record: ProfileLayerRecord) -> Dict[str, Any]:
    body = _audit_projection_body(record)
    assert_projection_has_no_credential_values(body)
    return body


__all__ = [
    "SCHEMA_VERSION",
    "LAYER_GLOBAL_DEFAULT",
    "LAYER_CAPABILITY_AGENT",
    "LAYER_PROJECT",
    "LAYER_RUN_OVERRIDE",
    "LAYER_PRECEDENCE",
    "LAYER_KINDS",
    "GLOBAL_SCOPE_KEY",
    "ProfileStoreError",
    "ProfileLayerRecord",
    "ProfileStore",
    "canonical_json_bytes",
    "sha256_hex",
    "content_digest",
    "public_projection",
    "audit_projection",
    "assert_projection_has_no_credential_values",
]
