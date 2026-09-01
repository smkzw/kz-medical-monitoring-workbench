"""R5 canonical serialization and content addressing.

Implements the frozen ``canonical_content_hash`` invariant of the exact R5
contract (``artifacts/.../exact_contract.json``, schema
``medical-monitoring-r5-exact-contract-v0.3.1``):

    content_hash == sha256(canonical JSON of all non-hash fields,
                           sorted unordered refs)

Rules
-----
* Canonical JSON mirrors the R4/R2/R3 family convention: Unicode NFC
  normalization, sorted keys, compact separators, ``ensure_ascii=False``,
  ``allow_nan=False``.
* Any field declared ``sha256`` by the exact contract is a *hash field* and
  is excluded from its object's canonical core ("non-hash fields").
* Every many-cardinality reference collection is an *unordered* set: it is
  sorted before serialization, so input ordering can never change the
  content hash.  Fields whose order is semantically significant (currently
  only ``R5CenterMapProjection.stable_site_order``) are registered as
  ordered and preserved verbatim.
* ``datetime.date`` serializes as ``YYYY-MM-DD``; ``decimal.Decimal``
  serializes as a normalized plain-notation string (finite only).
* Objects of unknown/unregistered type are rejected (fail closed) rather
  than silently serialized.

The schema is declared statically by :mod:`mm_r5.contracts`; nothing here
is generated at runtime from filenames, fixtures, case ids or test ids.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, FrozenSet, List, Tuple

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class R5CanonicalError(Exception):
    """A value cannot be canonicalized (unknown type, non-finite decimal,
    unregistered object) or is not a valid sha256 hex string."""


# ---------------------------------------------------------------------------
# Per-class field metadata (registered statically by mm_r5.contracts)
# ---------------------------------------------------------------------------

#: class name -> (hash fields excluded from the canonical core,
#:               ordered fields preserved verbatim instead of sorted)
_R5_CLASS_FIELDS: Dict[str, Tuple[FrozenSet[str], FrozenSet[str]]] = {}


def register_object_fields(
    class_name: str,
    hash_fields: Tuple[str, ...] = (),
    ordered_fields: Tuple[str, ...] = (),
) -> None:
    """Declare the canonical-field roles of one R5 object class.

    ``hash_fields``: sha256-typed fields of the exact contract, excluded
    from the canonical core.  ``ordered_fields``: many-cardinality fields
    whose order is semantically significant and must be preserved.
    Registration is static and idempotent; duplicate registration of the
    same class with different metadata is rejected.
    """
    if class_name in _R5_CLASS_FIELDS:
        previous = _R5_CLASS_FIELDS[class_name]
        current = (frozenset(hash_fields), frozenset(ordered_fields))
        if previous != current:
            raise R5CanonicalError(
                f"conflicting canonical field registration for {class_name!r}: "
                f"{previous!r} vs {current!r}")
        return
    _R5_CLASS_FIELDS[class_name] = (
        frozenset(hash_fields), frozenset(ordered_fields))


# ---------------------------------------------------------------------------
# Leaf canonicalization
# ---------------------------------------------------------------------------


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise R5CanonicalError(
            f"non-finite decimal cannot be canonicalized: {value!r}")
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    return format(normalized, "f")


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _to_plain(value: Any, ordered: bool) -> Any:
    """Recursively convert an R5 value to a plain JSON-able structure.

    Unordered collections are sorted by their own canonical JSON so the
    result is independent of input ordering.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return _canonical_decimal(value)
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        items: List[Any] = [_to_plain(item, False) for item in value]
        if not ordered:
            items.sort(key=_sort_key)
        return items
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): _to_plain(v, False)
                for key, v in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        class_name = type(value).__name__
        meta = _R5_CLASS_FIELDS.get(class_name)
        if meta is None:
            raise R5CanonicalError(
                f"unregistered R5 object type {class_name!r}; "
                "refusing to canonicalize")
        hash_fields, ordered_fields = meta
        out: Dict[str, Any] = {}
        for field in fields(value):
            if field.name in hash_fields:
                continue
            out[field.name] = _to_plain(
                getattr(value, field.name),
                field.name in ordered_fields)
        return out
    raise R5CanonicalError(
        f"unsupported leaf type {type(value).__name__}: {value!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def canonical_json(value: Any) -> str:
    """Deterministic canonical JSON of any R5 object or plain value."""
    return json.dumps(_to_plain(value, False), ensure_ascii=False,
                      sort_keys=True, separators=(",", ":"), allow_nan=False)


def object_to_core(obj: Any) -> Dict[str, Any]:
    """Plain-dict projection of one R5 object (non-hash fields, unordered
    collections sorted).  Deterministic and machine-readable."""
    core = _to_plain(obj, False)
    if not isinstance(core, dict):
        raise R5CanonicalError(
            f"object_to_core expects an R5 object, got {type(obj).__name__}")
    return core


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(value: Any) -> str:
    """Content address of any R5 object or plain value."""
    return sha256_hex(canonical_json(value).encode("utf-8"))


def canonical_object_hash(obj: Any) -> str:
    """Deterministic content hash of one R5 typed object.

    Excludes the object's declared sha256 hash fields, sorts unordered
    reference collections and preserves ordered fields verbatim.
    """
    return content_hash(obj)


def is_sha256_hex(value: Any) -> bool:
    """True iff ``value`` is a 64-char lowercase hex sha256 string."""
    return isinstance(value, str) and bool(_SHA256_RE.match(value))
