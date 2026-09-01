"""Shared primitive helpers for the R3 kernel.

Re-implements the small set of deterministic primitives the R3 POC needs so
that the R3 package is self-contained and never imports from (or mutates)
the frozen R2 package.  Every helper is pure and stdlib-only.
"""

from __future__ import annotations

import datetime
import hashlib
import math
import re as _re
import uuid
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Dict, Tuple

__all__ = [
    "ImmutableDict",
    "canonical_json",
    "content_hash",
    "deep_freeze_json",
    "now_iso",
    "new_id",
    "sha256_hex",
    "validate_sha256_hex",
    "validate_iso_date",
    "validate_nonempty_str",
]


def now_iso() -> str:
    """UTC ISO-8601 timestamp, lexicographically sortable."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def new_id(prefix: str = "") -> str:
    """Short random identifier; optional prefix for debuggability (<=64 chars)."""
    return (prefix + uuid.uuid4().hex)[:64]


_SHA256_RE = _re.compile(r"^[0-9a-f]{64}$")


def validate_sha256_hex(value: str, field_name: str = "content_digest") -> str:
    """Validate a canonical 64-char lowercase hex SHA-256 digest."""
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise ValueError(f"{field_name} must be 64-char lowercase hex sha256, got {value!r}")
    return value


_DATE_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_iso_date(value: str, field_name: str = "date") -> str:
    """Validate a ``YYYY-MM-DD`` calendar date string."""
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(f"{field_name} must be YYYY-MM-DD, got {value!r}")
    y, m, d = int(value[0:4]), int(value[5:7]), int(value[8:10])
    datetime.date(y, m, d)  # raises on impossible calendar dates
    return value


def validate_nonempty_str(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required and must be non-empty")
    return value


class ImmutableDict(Mapping):
    """A genuinely immutable mapping with no reachable mutable backing."""

    __slots__ = ("_m", "_hash")

    def __init__(self, data):
        if isinstance(data, MappingProxyType):
            backing = data
        elif isinstance(data, Mapping):
            backing = MappingProxyType(dict(data))
        else:
            backing = MappingProxyType(dict(data))
        object.__setattr__(self, "_m", backing)
        object.__setattr__(self, "_hash", None)

    def __getitem__(self, key):
        return self._m[key]

    def __iter__(self):
        return iter(self._m)

    def __len__(self):
        return len(self._m)

    def __contains__(self, key):
        return key in self._m

    def __eq__(self, other):
        if isinstance(other, Mapping):
            return dict(self) == dict(other)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self):
        h = self._hash
        if h is None:
            h = hash(canonical_json(dict(self)))
            object.__setattr__(self, "_hash", h)
        return h

    def __repr__(self):
        return f"ImmutableDict({dict(self._m)!r})"


def _freeze_scalar(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValueError("non-finite numbers are not JSON-compatible")
        return value
    if isinstance(value, str):
        return value
    raise ValueError(f"unsupported leaf type {type(value).__name__}: {value!r}")


def deep_freeze_json(value: Any) -> Any:
    """Deep-freeze a JSON-like structure into immutable containers.

    dict -> ImmutableDict; list/tuple -> tuple of frozen; scalars validated.
    Returns the frozen structure.  A tuple input with zero elements returns
    ``()``; a non-empty tuple is recursively frozen element-wise.
    """
    if isinstance(value, Mapping):
        return ImmutableDict({
            k: deep_freeze_json(v) for k, v in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(deep_freeze_json(v) for v in value)
    return _freeze_scalar(value)


def _json_plain(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {k: _json_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_plain(v) for v in obj]
    return obj


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8, no NaN."""
    import json
    return json.dumps(
        _json_plain(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(obj: Any) -> str:
    """Content address of any JSON-able object."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))
