#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G2 共享 canonical JSON 与 SHA-256 工具。"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from typing import Any, Dict, Mapping


def _canonical_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return unicodedata.normalize("NFC", value) if isinstance(value, str) else value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("canonical JSON does not allow non-finite numbers")
        return 0.0 if value == 0.0 else value
    if isinstance(value, Mapping):
        normalized: Dict[str, Any] = {}
        for raw_key, item in value.items():
            if not isinstance(raw_key, str):
                raise TypeError("canonical mappings require string keys")
            key = unicodedata.normalize("NFC", raw_key)
            if key in normalized:
                raise TypeError("canonical mapping has colliding normalized keys")
            normalized[key] = _canonical_value(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    raise TypeError("unsupported canonical value: %s" % type(value).__name__)


canonical_value = _canonical_value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def digest_ref(value: Any) -> str:
    return "sha256:" + canonical_digest(value)


def bytes_digest_ref(value: bytes) -> str:
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("bytes_digest_ref requires bytes")
    return "sha256:" + hashlib.sha256(bytes(value)).hexdigest()
