#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯标准库 synthetic source/output manifest 与 revision replay。

本模块只处理可重放的 JSON 证据结构，不读取项目目录、不调用模型、不启动服务，
也不绑定任何真实项目、医学词典或真实端口。所有摘要使用同一份版本化的
canonical JSON 规范；manifest 的自摘要字段被明确排除后再计算。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from canonical_evidence import (
    bytes_digest_ref,
    canonical_digest,
    canonical_json,
    canonical_json_bytes,
    canonical_value,
    digest_ref,
)


CANONICAL_JSON_SCHEMA = "mm-monitoring-r8-g2-canonical-json-v1"
DIGEST_SPEC_SCHEMA = "mm-monitoring-r8-g2-digest-spec-v1"
SOURCE_MANIFEST_SCHEMA = "mm-monitoring-r8-g2-source-manifest-v1"
OUTPUT_MANIFEST_SCHEMA = "mm-monitoring-r8-g2-output-manifest-v1"
MANIFEST_CHAIN_SCHEMA = "mm-monitoring-r8-g2-manifest-chain-v1"
SERIALIZER_ID = "python-json-canonical"
SERIALIZER_VERSION = "1"
HASH_ALGORITHM = "sha256"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA256_REF_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
_SAFE_REF_RE = re.compile(r"^[^\x00-\x1f\x7f/\\]+$")
_BIDI_OR_CONTROL = frozenset(
    {
        "\u061c",
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
        "\u206a",
        "\u206b",
        "\u206c",
        "\u206d",
        "\u206e",
        "\u206f",
        "\u200b",
        "\u200c",
        "\u200d",
        "\ufeff",
    }
)


class ManifestError(ValueError):
    """合成 manifest、摘要输入或 revision 链无效。"""


ManifestValidationError = ManifestError
RevisionReplayError = ManifestError


@dataclass(frozen=True)
class DigestSpec:
    """Frozen description of one named digest input."""

    name: str
    schema: str
    field_scope: str
    fields: Tuple[str, ...]
    excluded_fields: Tuple[str, ...]
    array_sort_keys: Tuple[Tuple[str, str], ...]
    default_rules: str = "omitted fields are absent; null is preserved explicitly"
    string_normalization: str = "NFC"
    serializer_id: str = SERIALIZER_ID
    serializer_version: str = SERIALIZER_VERSION
    hash_algorithm: str = HASH_ALGORITHM

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "field_scope": self.field_scope,
            "fields": list(self.fields),
            "excluded_fields": list(self.excluded_fields),
            "array_sort_keys": [
                {"path": path, "key": key} for path, key in self.array_sort_keys
            ],
            "default_rules": self.default_rules,
            "string_normalization": self.string_normalization,
            "serializer": {
                "id": self.serializer_id,
                "version": self.serializer_version,
            },
            "hash_algorithm": self.hash_algorithm,
        }
 

def _digest_spec(
    name: str,
    fields: Sequence[str],
    *,
    excluded_fields: Sequence[str] = (),
    array_sort_keys: Sequence[Tuple[str, str]] = (),
    default_rules: str = "omitted fields are absent; null is preserved explicitly",
) -> DigestSpec:
    return DigestSpec(
        name=name,
        schema=DIGEST_SPEC_SCHEMA,
        field_scope="exactly the listed top-level fields; self digest fields are excluded",
        fields=tuple(fields),
        excluded_fields=tuple(excluded_fields),
        array_sort_keys=tuple(array_sort_keys),
        default_rules=default_rules,
    )



# This is the normative table. ``fields`` are the exact stable top-level
# field names. Digest inputs reject undeclared fields, remove only the listed
# self-digest fields, then apply the declared array-order rules.
_DIGEST_SPECS: Tuple[DigestSpec, ...] = (
    _digest_spec(
        "contract",
        (
            "contract_id",
            "contract_version",
            "schema",
            "schema_version",
            "contract_digest",
            "terms",
        ),
    ),
    _digest_spec(
        "binding",
        (
            "binding_id",
            "project_ref",
            "admission_id",
            "provider",
            "model",
            "adapter",
            "profile",
            "toolchain",
            "parameters",
            "timeout_seconds",
            "fallback_policy",
        ),
    ),
    _digest_spec(
        "source_manifest",
        (
            "schema",
            "schema_version",
            "contract_ref",
            "policy",
            "toolchain",
            "project_ref",
            "source_root_ref",
            "output_root_ref",
            "admission_id",
            "binding_digest",
            "source_scope_spec_digest",
            "snapshots",
            "role_availability",
            "duplicates_conflicts",
            "stability",
            "zero_write",
            "independent_verification",
            "status",
            "manifest_digest",
            "source_manifest_digest",
        ),
        excluded_fields=("manifest_digest", "source_manifest_digest"),
        array_sort_keys=(
            ("snapshots.*.entries", "relative_path"),
            ("role_availability", "role"),
            ("duplicates_conflicts.duplicates", "relative_path"),
            ("duplicates_conflicts.conflicts", "relative_path"),
        ),
    ),
    _digest_spec(
        "input",
        (
            "run_ref",
            "source_manifest_digest",
            "binding_digest",
            "source_revision_ref",
            "artifact_refs",
            "unit_set_digest",
            "selection_policy",
            "input_digest",
        ),
        excluded_fields=("input_digest",),
        array_sort_keys=(("artifact_refs", "artifact_id"),),
    ),
    _digest_spec(
        "unit_set",
        ("unit_set_id", "units", "coverage_policy", "unit_set_digest"),
        excluded_fields=("unit_set_digest",),
        array_sort_keys=(("units", "unit_id"),),
    ),
    _digest_spec(
        "prompt_frame",
        (
            "prompt_frame_id",
            "version",
            "template_digest",
            "schema_digest",
            "coverage_policy_digest",
            "anchor_policy_digest",
            "normalization_policy",
            "locale",
            "prompt_frame_digest",
        ),
        excluded_fields=("prompt_frame_digest",),
    ),
    _digest_spec(
        "execution_profile",
        (
            "profile_id",
            "profile_version",
            "binding_digest",
            "toolchain_digest",
            "parameters",
            "timeout_seconds",
            "recovery_policy",
            "execution_profile_digest",
        ),
        excluded_fields=("execution_profile_digest",),
    ),
    _digest_spec(
        "raw",
        (
            "artifact_id",
            "sha256",
            "media_type",
            "length_bytes",
            "received_as_is",
            "terminal_status",
            "raw_digest",
        ),
        excluded_fields=("raw_digest",),
    ),
    _digest_spec(
        "parsed",
        (
            "artifact_id",
            "sha256",
            "parser_id",
            "parser_version",
            "schema_status",
            "unknown_fields",
            "parsed_digest",
        ),
        excluded_fields=("parsed_digest",),
        array_sort_keys=(("unknown_fields", "field"),),
    ),
    _digest_spec(
        "coverage",
        (
            "expected_units",
            "processed_units",
            "skipped_units",
            "failed_units",
            "status",
            "reasons",
            "coverage_digest",
        ),
        excluded_fields=("coverage_digest",),
        array_sort_keys=(
            ("expected_units", "unit_id"),
            ("processed_units", "unit_id"),
            ("skipped_units", "unit_id"),
            ("failed_units", "unit_id"),
        ),
    ),
    _digest_spec(
        "source_anchors",
        (
            "source_revision_ref",
            "anchors",
            "anchor_policy_version",
            "source_anchors_digest",
        ),
        excluded_fields=("source_anchors_digest",),
        array_sort_keys=(("anchors", "anchor_id"),),
    ),
    _digest_spec(
        "validation",
        (
            "validator_id",
            "validator_version",
            "checks",
            "findings",
            "status",
            "validation_digest",
        ),
        excluded_fields=("validation_digest",),
        array_sort_keys=(
            ("checks", "check_id"),
            ("findings", "finding_id"),
        ),
    ),
    _digest_spec(
        "output_manifest",
        (
            "schema",
            "schema_version",
            "contract_ref",
            "project_ref",
            "admission_id",
            "run_ref",
            "binding_digest",
            "emitted_by_binding_digest",
            "source_manifest_digest",
            "source_access_profile_digest",
            "input_digest",
            "prompt_frame_digest",
            "schema_digest",
            "execution_profile_digest",
            "output_root_ref",
            "artifacts",
            "lineage",
            "publication_status",
            "manifest_revision",
            "parent_manifest_digest",
            "manifest_digest",
            "output_manifest_digest",
        ),
        excluded_fields=("manifest_digest", "output_manifest_digest"),
        array_sort_keys=(("artifacts", "artifact_id"),),
    ),
)

DIGEST_SPEC_TABLE: Tuple[Dict[str, Any], ...] = tuple(
    spec.as_dict() for spec in _DIGEST_SPECS
)
CANONICAL_DIGEST_SPEC_TABLE = DIGEST_SPEC_TABLE
_DIGEST_SPEC_BY_NAME = {spec.name: spec for spec in _DIGEST_SPECS}
CANONICAL_DIGEST_SPEC: Dict[str, Any] = {
    "schema": DIGEST_SPEC_SCHEMA,
    "canonical_json": {
        "schema": CANONICAL_JSON_SCHEMA,
        "encoding": "UTF-8",
        "object_keys": "Unicode code-point ascending",
        "arrays": "preserve input order unless the named table row declares a sort key",
        "strings": "NFC",
        "numbers": "finite JSON numbers; negative zero normalized to 0.0",
        "null": "preserved",
        "serializer": {"id": SERIALIZER_ID, "version": SERIALIZER_VERSION},
        "hash_algorithm": HASH_ALGORITHM,
    },
    "entries": {spec.name: spec.as_dict() for spec in _DIGEST_SPECS},
}

CANONICAL_DIGEST_SPEC_DIGEST = digest_ref(CANONICAL_DIGEST_SPEC)
DIGEST_SPEC_DIGEST = CANONICAL_DIGEST_SPEC_DIGEST


def digest_spec(name: str) -> DigestSpec:
    try:
        return _DIGEST_SPEC_BY_NAME[str(name)]
    except KeyError as exc:
        raise ManifestError("unknown_digest_spec:%s" % name) from exc


def _path_rule(path: Tuple[str, ...], rules: Sequence[Tuple[str, str]]) -> Optional[str]:
    for raw_path, key in rules:
        pieces = tuple(raw_path.split(".")) if raw_path else ()
        if len(pieces) != len(path):
            continue
        if all(expected == "*" or expected == actual for expected, actual in zip(pieces, path)):
            return key
    return None


def _sort_for_digest(value: Any, path: Tuple[str, ...], rules: Sequence[Tuple[str, str]]) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _sort_for_digest(item, path + (key,), rules)
            for key, item in value.items()
        }
    if isinstance(value, list):
        items = [_sort_for_digest(item, path, rules) for item in value]
        key_name = _path_rule(path, rules)
        if key_name is None:
            return items
        try:
            return sorted(
                items,
                key=lambda item: canonical_json_bytes(item[key_name]),
            )
        except (KeyError, TypeError) as exc:
            raise ManifestError(
                "digest_array_sort_key_missing:%s:%s" % (".".join(path), key_name)
            ) from exc
    return value


def _digest_projection(name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
    spec = digest_spec(name)
    if not isinstance(payload, Mapping):
        raise ManifestError("digest_input_must_be_object:%s" % name)
    normalized = canonical_value(payload)
    assert isinstance(normalized, dict)
    unknown = set(normalized) - set(spec.fields)
    if unknown:
        raise ManifestError(
            "digest_input_unknown_fields:%s:%s"
            % (name, ",".join(sorted(map(str, unknown))))
        )
    for field in spec.excluded_fields:
        normalized.pop(field, None)
    projected = _sort_for_digest(normalized, (), spec.array_sort_keys)
    assert isinstance(projected, dict)
    return projected


def digest_named(name: str, payload: Mapping[str, Any]) -> str:
    """Digest a named, versioned input according to ``DIGEST_SPEC_TABLE``."""
    return canonical_digest(_digest_projection(name, payload))


# Explicit aliases make the independent replay entry point discoverable without
# introducing another implementation or a compatibility shim in production code.
canonical_digest_for = digest_named


def _copy_json(value: Any) -> Any:
    try:
        return canonical_value(value)
    except (TypeError, ValueError) as exc:
        raise ManifestError("value_not_canonical") from exc


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError("%s_must_be_object" % field)
    return value


def _require_string(value: Any, field: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise ManifestError("%s_must_be_string" % field)
    normalized = unicodedata.normalize("NFC", value)
    if nonempty and not normalized:
        raise ManifestError("%s_must_not_be_empty" % field)
    if normalized != normalized.strip():
        raise ManifestError("%s_must_not_have_outer_whitespace" % field)
    return normalized


def _require_safe_ref(value: Any, field: str, prefix: Optional[str] = None) -> str:
    normalized = _require_string(value, field)
    if prefix is not None and not normalized.startswith(prefix):
        raise ManifestError("%s_invalid_prefix" % field)
    if not _SAFE_REF_RE.fullmatch(normalized):
        raise ManifestError("%s_contains_path_or_control" % field)
    if any(char.isspace() for char in normalized):
        raise ManifestError("%s_contains_whitespace" % field)
    if any(char in _BIDI_OR_CONTROL for char in normalized):
        raise ManifestError("%s_contains_invisible_control" % field)
    return normalized


def _require_opaque_ref(value: Any, field: str, kind: str) -> str:
    return _require_safe_ref(value, field, "opaque-%s:" % kind)


def _require_positive_int(value: Any, field: str, *, zero_allowed: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError("%s_must_be_integer" % field)
    if value < 0 or (value == 0 and not zero_allowed):
        raise ManifestError("%s_must_be_positive" % field)
    return int(value)


def _require_sha256_ref(value: Any, field: str) -> str:
    normalized = _require_string(value, field)
    match = _SHA256_REF_RE.fullmatch(normalized)
    if match:
        return "sha256:" + match.group(1)
    if _SHA256_RE.fullmatch(normalized):
        return "sha256:" + normalized
    raise ManifestError("%s_must_be_sha256" % field)


def _optional_sha256_ref(value: Any, field: str) -> Optional[str]:
    if value is None:
        return None
    return _require_sha256_ref(value, field)




def _require_enum(value: Any, field: str, allowed: Iterable[str]) -> str:
    normalized = _require_string(value, field)
    if normalized not in set(allowed):
        raise ManifestError("%s_invalid_value" % field)
    return normalized


def _normalize_contract_ref(value: Any) -> Any:
    if isinstance(value, str):
        return _require_safe_ref(value, "contract_ref")
    body = dict(_require_mapping(value, "contract_ref"))
    if "id" in body:
        body["id"] = _require_safe_ref(body["id"], "contract_ref.id")
    if "version" in body:
        body["version"] = _require_string(body["version"], "contract_ref.version")
    if not body:
        raise ManifestError("contract_ref_must_not_be_empty")
    return _copy_json(body)


def _normalize_status_object(value: Any, field: str, default: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    if value is None:
        return _copy_json(default or {})
    return dict(_copy_json(_require_mapping(value, field)))


def _normalize_zero_write(value: Any) -> Dict[str, Any]:
    if value is None:
        return {
            "status": "not_evaluable",
            "profile_digest": None,
            "before_tree_digest": None,
            "after_tree_digest": None,
            "reasons": ["source_access_evidence_missing"],
            "evidence": None,
        }
    raw = dict(_require_mapping(value, "zero_write"))
    if set(raw) != {"status", "evidence"}:
        raise ManifestError("zero_write_fields_mismatch")
    try:
        from source_access_profile import validate_source_access_evidence

        evidence = validate_source_access_evidence(
            _require_mapping(raw["evidence"], "zero_write.evidence")
        )
    except (TypeError, ValueError) as exc:
        raise ManifestError("zero_write_evidence_invalid:%s" % exc) from exc
    status = _require_enum(raw["status"], "zero_write.status", {"evaluable", "not_evaluable"})
    if status != evidence["status"]:
        raise ManifestError("zero_write_status_mismatch")
    return {
        "status": status,
        "profile_digest": evidence["profile_digest"],
        "before_tree_digest": evidence["source"]["before"]["tree_digest"],
        "after_tree_digest": evidence["source"]["after"]["tree_digest"],
        "reasons": list(evidence["not_evaluable_reasons"]),
        "evidence": evidence,
    }


def _validate_relative_path(value: Any, field: str) -> str:
    path = _require_string(value, field)
    if path.startswith("/") or "\\" in path or "\x00" in path:
        raise ManifestError("%s_must_be_root_relative_posix" % field)
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ManifestError("%s_contains_escape_segment" % field)
    if any(char in _BIDI_OR_CONTROL or ord(char) < 0x20 or ord(char) == 0x7F for char in path):
        raise ManifestError("%s_contains_control" % field)
    return unicodedata.normalize("NFC", path)


_SOURCE_ENTRY_ALLOWED = frozenset(
    {
        "relative_path",
        "raw_path_digest",
        "entry_kind",
        "size_bytes",
        "mtime_ns",
        "content_hash",
        "snapshot_role",
        "read_status",
        "evidence_ids",
        "container_ref",
        "member_count",
    }
)
_ENTRY_KINDS = frozenset(
    {"directory", "regular_file", "package", "archive", "symlink", "special", "unreadable"}
)
_SNAPSHOT_ROLES = frozenset(
    {"protocol", "ib", "listing", "grouping", "report", "supporting", "container", "excluded", "not_evaluable"}
)
_READ_STATUSES = frozenset({"read", "not_read", "failed", "not_evaluable", "blocked"})


def _normalize_source_entry(value: Any, index: int) -> Dict[str, Any]:
    raw = dict(_require_mapping(value, "snapshot.entry[%d]" % index))
    unknown = set(raw) - _SOURCE_ENTRY_ALLOWED
    if unknown:
        raise ManifestError("snapshot_entry_unknown_fields:%s" % ",".join(sorted(map(str, unknown))))
    result: Dict[str, Any] = {
        "relative_path": _validate_relative_path(raw.get("relative_path"), "snapshot.entry.relative_path"),
        "entry_kind": _require_enum(raw.get("entry_kind"), "snapshot.entry.entry_kind", _ENTRY_KINDS),
        "size_bytes": _require_positive_int(raw.get("size_bytes"), "snapshot.entry.size_bytes", zero_allowed=True),
        "mtime_ns": _require_positive_int(raw.get("mtime_ns"), "snapshot.entry.mtime_ns", zero_allowed=True),
        "content_hash": _require_sha256_ref(raw.get("content_hash"), "snapshot.entry.content_hash"),
        "snapshot_role": _require_enum(raw.get("snapshot_role"), "snapshot.entry.snapshot_role", _SNAPSHOT_ROLES),
        "read_status": _require_enum(raw.get("read_status"), "snapshot.entry.read_status", _READ_STATUSES),
    }
    if "raw_path_digest" in raw:
        result["raw_path_digest"] = _require_sha256_ref(raw["raw_path_digest"], "snapshot.entry.raw_path_digest")
    evidence = raw.get("evidence_ids", ())
    if not isinstance(evidence, (list, tuple)):
        raise ManifestError("snapshot.entry.evidence_ids_must_be_array")
    result["evidence_ids"] = sorted(
        {_require_safe_ref(item, "snapshot.entry.evidence_ids[]") for item in evidence},
        key=lambda item: item.encode("utf-8"),
    )
    if "container_ref" in raw and raw["container_ref"] is not None:
        result["container_ref"] = _require_safe_ref(raw["container_ref"], "snapshot.entry.container_ref")
    if "member_count" in raw:
        result["member_count"] = _require_positive_int(raw["member_count"], "snapshot.entry.member_count", zero_allowed=True)
    return result


def _normalize_snapshot(value: Any, label: str) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        body = dict(value)
        entries = body.pop("entries", None)
        if entries is None:
            raise ManifestError("snapshot.%s.entries_missing" % label)
        allowed = {"snapshot_id", "captured_at", "entries", "tree_digest", "status"}
        unknown = set(body) - (allowed - {"entries"})
        if unknown:
            raise ManifestError("snapshot_unknown_fields:%s" % ",".join(sorted(map(str, unknown))))
    else:
        body = {}
        entries = value
    if not isinstance(entries, (list, tuple)):
        raise ManifestError("snapshot.%s.entries_must_be_array" % label)
    normalized_entries = [_normalize_source_entry(item, index) for index, item in enumerate(entries)]
    seen_paths = set()
    for entry in normalized_entries:
        path = entry["relative_path"]
        if path in seen_paths:
            raise ManifestError("snapshot.%s.normalized_path_collision" % label)
        seen_paths.add(path)
    normalized_entries.sort(key=lambda item: item["relative_path"].encode("utf-8"))
    result: Dict[str, Any] = {
        "snapshot_id": _require_string(body.get("snapshot_id", label), "snapshot.snapshot_id"),
        "entries": normalized_entries,
    }
    for key in ("captured_at", "status"):
        if key in body:
            result[key] = _require_string(body[key], "snapshot.%s" % key)
    if "tree_digest" in body:
        result["tree_digest"] = _require_sha256_ref(body["tree_digest"], "snapshot.tree_digest")
    return result


def _normalize_snapshots(value: Any) -> Dict[str, Dict[str, Any]]:
    body = _require_mapping(value, "snapshots")
    if set(body) != {"A", "B"}:
        raise ManifestError("snapshots_must_contain_A_and_B")
    return {label: _normalize_snapshot(body[label], label) for label in ("A", "B")}


def _normalize_role_availability(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        rows: List[Dict[str, Any]] = []
        for role, data in value.items():
            row = dict(_require_mapping(data, "role_availability.%s" % role))
            row["role"] = _require_enum(role, "role_availability.role", _SNAPSHOT_ROLES)
            if "required" in row:
                if not isinstance(row["required"], bool):
                    raise ManifestError("role_availability.required_must_be_boolean")
            if "available" in row and not isinstance(row["available"], bool):
                raise ManifestError("role_availability.available_must_be_boolean")
            rows.append(_copy_json(row))
    elif isinstance(value, (list, tuple)):
        rows = []
        for row_value in value:
            row = dict(_require_mapping(row_value, "role_availability[]"))
            row["role"] = _require_enum(row.get("role"), "role_availability.role", _SNAPSHOT_ROLES)
            rows.append(_copy_json(row))
    else:
        raise ManifestError("role_availability_must_be_object_or_array")
    rows.sort(key=lambda row: str(row["role"]).encode("utf-8"))
    seen = set()
    for row in rows:
        if row["role"] in seen:
            raise ManifestError("role_availability_duplicate_role")
        seen.add(row["role"])
    return rows


def _normalize_duplicate_conflicts(value: Any) -> Dict[str, Any]:
    body = dict(_normalize_status_object(value, "duplicates_conflicts", {"duplicates": [], "conflicts": []}))
    for key in ("duplicates", "conflicts"):
        rows = body.get(key, [])
        if not isinstance(rows, (list, tuple)):
            raise ManifestError("duplicates_conflicts.%s_must_be_array" % key)
        normalized_rows: List[Any] = []
        for row in rows:
            if isinstance(row, Mapping) and "relative_path" in row:
                item = dict(row)
                item["relative_path"] = _validate_relative_path(
                    item["relative_path"], "duplicates_conflicts.%s.relative_path" % key
                )
                normalized_rows.append(_copy_json(item))
            else:
                normalized_rows.append(_copy_json(row))
        normalized_rows.sort(key=canonical_json_bytes)
        body[key] = normalized_rows
    return body


def build_source_manifest(
    *,
    contract_ref: Any,
    binding_digest: Any,
    project_ref: Any,
    source_root_ref: Any,
    output_root_ref: Any,
    admission_id: Any,
    source_scope_spec_digest: Any,
    snapshots: Mapping[str, Any],
    policy: Optional[Mapping[str, Any]] = None,
    toolchain: Optional[Mapping[str, Any]] = None,
    role_availability: Any = None,
    duplicates_conflicts: Any = None,
    stability: Any = None,
    zero_write: Any = None,
    independent_verification: Any = None,
    status: str = "not_evaluable",
) -> Dict[str, Any]:
    """Build and validate a deterministic synthetic source manifest.

    A and B are supplied as synthetic snapshots only; this function never reads
    either root. The default status is fail-closed ``not_evaluable``.
    """
    body: Dict[str, Any] = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "schema_version": "1",
        "contract_ref": _normalize_contract_ref(contract_ref),
        "policy": _copy_json(policy or {}),
        "toolchain": _copy_json(toolchain or {}),
        "project_ref": _require_opaque_ref(project_ref, "project_ref", "project"),
        "source_root_ref": _require_opaque_ref(source_root_ref, "source_root_ref", "root"),
        "output_root_ref": _require_opaque_ref(output_root_ref, "output_root_ref", "output"),
        "admission_id": _require_opaque_ref(admission_id, "admission_id", "admission"),
        "binding_digest": _require_sha256_ref(binding_digest, "binding_digest"),
        "source_scope_spec_digest": _require_sha256_ref(
            source_scope_spec_digest, "source_scope_spec_digest"
        ),
        "snapshots": _normalize_snapshots(snapshots),
        "role_availability": _normalize_role_availability(role_availability),
        "duplicates_conflicts": _normalize_duplicate_conflicts(duplicates_conflicts),
        "stability": _normalize_status_object(stability, "stability", {"status": "not_evaluable"}),
        "zero_write": _normalize_zero_write(zero_write),
        "independent_verification": _normalize_status_object(
            independent_verification,
            "independent_verification",
            {"status": "not_evaluable"},
        ),
        "status": _require_enum(
            status,
            "status",
            {"evaluable", "not_evaluable", "conflict", "parse_failed", "blocked"},
        ),
    }
    if body["source_root_ref"] == body["output_root_ref"]:
        raise ManifestError("source_and_output_roots_must_be_distinct")
    body["manifest_digest"] = digest_ref(_digest_projection("source_manifest", body))
    body["source_manifest_digest"] = body["manifest_digest"]
    return validate_source_manifest(body)


def validate_source_manifest(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate, canonicalize, and verify a source manifest digest."""
    raw = dict(_require_mapping(value, "source_manifest"))
    allowed = set(digest_spec("source_manifest").fields)
    unknown = set(raw) - allowed
    if unknown:
        raise ManifestError("source_manifest_unknown_fields:%s" % ",".join(sorted(map(str, unknown))))
    required = {
        "schema",
        "schema_version",
        "contract_ref",
        "policy",
        "toolchain",
        "project_ref",
        "source_root_ref",
        "output_root_ref",
        "admission_id",
        "binding_digest",
        "source_scope_spec_digest",
        "snapshots",
        "role_availability",
        "duplicates_conflicts",
        "stability",
        "zero_write",
        "independent_verification",
        "status",
        "manifest_digest",
    }
    missing = required - set(raw)
    if missing:
        raise ManifestError("source_manifest_missing_fields:%s" % ",".join(sorted(missing)))
    schema = _require_string(raw["schema"], "source_manifest.schema")
    if schema != SOURCE_MANIFEST_SCHEMA:
        raise ManifestError("source_manifest_schema_mismatch")
    if _require_string(raw["schema_version"], "source_manifest.schema_version") != "1":
        raise ManifestError("source_manifest_schema_version_mismatch")
    body: Dict[str, Any] = {
        "schema": schema,
        "schema_version": "1",
        "contract_ref": _normalize_contract_ref(raw["contract_ref"]),
        "policy": _copy_json(_require_mapping(raw["policy"], "source_manifest.policy")),
        "toolchain": _copy_json(_require_mapping(raw["toolchain"], "source_manifest.toolchain")),
        "project_ref": _require_opaque_ref(raw["project_ref"], "source_manifest.project_ref", "project"),
        "source_root_ref": _require_opaque_ref(raw["source_root_ref"], "source_manifest.source_root_ref", "root"),
        "output_root_ref": _require_opaque_ref(raw["output_root_ref"], "source_manifest.output_root_ref", "output"),
        "admission_id": _require_opaque_ref(raw["admission_id"], "source_manifest.admission_id", "admission"),
        "binding_digest": _require_sha256_ref(raw["binding_digest"], "source_manifest.binding_digest"),
        "source_scope_spec_digest": _require_sha256_ref(
            raw["source_scope_spec_digest"], "source_manifest.source_scope_spec_digest"
        ),
        "snapshots": _normalize_snapshots(raw["snapshots"]),
        "role_availability": _normalize_role_availability(raw["role_availability"]),
        "duplicates_conflicts": _normalize_duplicate_conflicts(raw["duplicates_conflicts"]),
        "stability": _normalize_status_object(raw["stability"], "source_manifest.stability"),
        "zero_write": _normalize_zero_write(
            None
            if raw["zero_write"] == {
                "status": "not_evaluable",
                "profile_digest": None,
                "before_tree_digest": None,
                "after_tree_digest": None,
                "reasons": ["source_access_evidence_missing"],
                "evidence": None,
            }
            else {
                "status": _require_mapping(raw["zero_write"], "source_manifest.zero_write").get("status"),
                "evidence": _require_mapping(raw["zero_write"], "source_manifest.zero_write").get("evidence"),
            }
        ),
        "independent_verification": _normalize_status_object(
            raw["independent_verification"], "source_manifest.independent_verification"
        ),
        "status": _require_enum(
            raw["status"],
            "source_manifest.status",
            {"evaluable", "not_evaluable", "conflict", "parse_failed", "blocked"},
        ),
    }
    if body["source_root_ref"] == body["output_root_ref"]:
        raise ManifestError("source_and_output_roots_must_be_distinct")
    expected = digest_ref(_digest_projection("source_manifest", body))
    actual = _require_sha256_ref(raw["manifest_digest"], "source_manifest.manifest_digest")
    if actual != expected:
        raise ManifestError("source_manifest_digest_mismatch")
    if "source_manifest_digest" in raw:
        alias = _require_sha256_ref(raw["source_manifest_digest"], "source_manifest.source_manifest_digest")
        if alias != actual:
            raise ManifestError("source_manifest_digest_alias_mismatch")
    body["manifest_digest"] = actual
    body["source_manifest_digest"] = actual
    return body


_OUTPUT_ARTIFACT_ALLOWED = frozenset(
    {
        "artifact_id",
        "id",
        "sha256",
        "content_hash",
        "media_type",
        "length_bytes",
        "trusted",
        "received_as_is",
        "stage",
    }
)
_LINEAGE_STAGES = (
    "raw_output",
    "envelope",
    "parsed_output",
    "validation",
    "adjudication",
    "disposition",
)
_OUTPUT_STATUSES = frozenset({"untrusted", "quarantine", "candidate", "published", "not_published"})


def _normalize_artifacts(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ManifestError("artifacts_must_be_array")
    rows: List[Dict[str, Any]] = []
    seen = set()
    for index, item_value in enumerate(value):
        item = dict(_require_mapping(item_value, "artifacts[%d]" % index))
        unknown = set(item) - _OUTPUT_ARTIFACT_ALLOWED
        if unknown:
            raise ManifestError("artifact_unknown_fields:%s" % ",".join(sorted(map(str, unknown))))
        artifact_id = item.get("artifact_id", item.get("id"))
        artifact_id = _require_safe_ref(artifact_id, "artifacts[%d].artifact_id")
        if artifact_id in seen:
            raise ManifestError("duplicate_artifact_id:%s" % artifact_id)
        seen.add(artifact_id)
        digest = item.get("sha256", item.get("content_hash"))
        row: Dict[str, Any] = {
            "artifact_id": artifact_id,
            "sha256": _require_sha256_ref(digest, "artifacts[%d].sha256" % index),
            "media_type": _require_string(item.get("media_type"), "artifacts[%d].media_type" % index),
            "length_bytes": _require_positive_int(
                item.get("length_bytes"), "artifacts[%d].length_bytes" % index, zero_allowed=True
            ),
        }
        for key in ("trusted", "received_as_is"):
            if key in item:
                if not isinstance(item[key], bool):
                    raise ManifestError("artifacts[%d].%s_must_be_boolean" % (index, key))
                row[key] = item[key]
        if "stage" in item:
            row["stage"] = _require_enum(item["stage"], "artifacts[%d].stage" % index, _LINEAGE_STAGES)
        rows.append(row)
    rows.sort(key=lambda row: row["artifact_id"].encode("utf-8"))
    return rows


def _artifact_ref_from_mapping(value: Mapping[str, Any], side: str) -> Dict[str, str]:
    artifact_id = value.get("artifact_id", value.get("id"))
    digest = value.get("sha256", value.get("content_hash"))
    return {
        "artifact_id": _require_safe_ref(artifact_id, "%s.artifact_id" % side),
        "sha256": _require_sha256_ref(digest, "%s.sha256" % side),
    }


def _normalize_lineage(value: Any, artifacts: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    if isinstance(value, Mapping):
        # Accept {stage: {artifact_id, sha256}} as a compact input form.
        nodes = []
        for stage in _LINEAGE_STAGES:
            if stage not in value:
                raise ManifestError("lineage_missing_stage:%s" % stage)
            node = dict(_require_mapping(value[stage], "lineage.%s" % stage))
            ref = _artifact_ref_from_mapping(node, "lineage.%s" % stage)
            nodes.append({"stage": stage, **ref})
        value = nodes
    if not isinstance(value, (list, tuple)):
        raise ManifestError("lineage_must_be_array_or_object")
    if not value:
        raise ManifestError("lineage_must_not_be_empty")
    first = value[0]
    if isinstance(first, Mapping) and "stage" in first:
        nodes: List[Dict[str, Any]] = []
        for index, item_value in enumerate(value):
            item = dict(_require_mapping(item_value, "lineage[%d]" % index))
            stage = _require_enum(item.get("stage"), "lineage[%d].stage" % index, _LINEAGE_STAGES)
            ref = _artifact_ref_from_mapping(item, "lineage[%d]" % index)
            nodes.append({"stage": stage, **ref})
        if [row["stage"] for row in nodes] != list(_LINEAGE_STAGES):
            raise ManifestError("lineage_stage_order_mismatch")
        edges = []
        for index in range(len(nodes) - 1):
            left, right = nodes[index], nodes[index + 1]
            edges.append(
                {
                    "sequence": index + 1,
                    "from_stage": left["stage"],
                    "from_artifact_id": left["artifact_id"],
                    "from_sha256": left["sha256"],
                    "to_stage": right["stage"],
                    "to_artifact_id": right["artifact_id"],
                    "to_sha256": right["sha256"],
                }
            )
        return edges
    edges = []
    for index, item_value in enumerate(value):
        item = dict(_require_mapping(item_value, "lineage[%d]" % index))
        required = {
            "from_stage",
            "from_artifact_id",
            "from_sha256",
            "to_stage",
            "to_artifact_id",
            "to_sha256",
        }
        if not required <= set(item):
            raise ManifestError("lineage_edge_missing_fields:%d" % index)
        edges.append(
            {
                "sequence": _require_positive_int(
                    item.get("sequence", index + 1), "lineage[%d].sequence" % index
                ),
                "from_stage": _require_enum(item["from_stage"], "lineage.from_stage", _LINEAGE_STAGES),
                "from_artifact_id": _require_safe_ref(item["from_artifact_id"], "lineage.from_artifact_id"),
                "from_sha256": _require_sha256_ref(item["from_sha256"], "lineage.from_sha256"),
                "to_stage": _require_enum(item["to_stage"], "lineage.to_stage", _LINEAGE_STAGES),
                "to_artifact_id": _require_safe_ref(item["to_artifact_id"], "lineage.to_artifact_id"),
                "to_sha256": _require_sha256_ref(item["to_sha256"], "lineage.to_sha256"),
            }
        )
    edges.sort(key=lambda row: row["sequence"])
    if [row["sequence"] for row in edges] != list(range(1, len(edges) + 1)):
        raise ManifestError("lineage_sequence_mismatch")
    expected_pairs = list(zip(_LINEAGE_STAGES, _LINEAGE_STAGES[1:]))
    actual_pairs = [(row["from_stage"], row["to_stage"]) for row in edges]
    if actual_pairs != expected_pairs:
        raise ManifestError("lineage_stage_order_mismatch")
    return edges


def _validate_lineage_references(
    lineage: Sequence[Mapping[str, Any]], artifacts: Sequence[Mapping[str, Any]]
) -> None:
    by_id = {str(row["artifact_id"]): str(row["sha256"]) for row in artifacts}
    for edge in lineage:
        for id_key, hash_key in (
            ("from_artifact_id", "from_sha256"),
            ("to_artifact_id", "to_sha256"),
        ):
            artifact_id = str(edge[id_key])
            if artifact_id not in by_id:
                raise ManifestError("lineage_artifact_missing:%s" % artifact_id)
            if by_id[artifact_id] != edge[hash_key]:
                raise ManifestError("lineage_artifact_digest_mismatch:%s" % artifact_id)


def build_output_manifest(
    *,
    contract_ref: Any,
    project_ref: Any,
    admission_id: Any,
    run_ref: Any,
    binding_digest: Any,
    source_manifest_digest: Any,
    source_access_profile_digest: Any,
    input_digest: Any,
    prompt_frame_digest: Any,
    schema_digest: Any,
    execution_profile_digest: Any,
    output_root_ref: Any,
    artifacts: Sequence[Mapping[str, Any]],
    lineage: Any,
    publication_status: str = "quarantine",
    manifest_revision: int = 1,
    parent_manifest_digest: Any = None,
    emitted_by_binding_digest: Any = None,
) -> Dict[str, Any]:
    binding = _require_sha256_ref(binding_digest, "binding_digest")
    emitted = binding if emitted_by_binding_digest is None else _require_sha256_ref(
        emitted_by_binding_digest, "emitted_by_binding_digest"
    )
    if emitted != binding:
        raise ManifestError("emitted_binding_digest_mismatch")
    revision = _require_positive_int(manifest_revision, "manifest_revision")
    parent = _optional_sha256_ref(parent_manifest_digest, "parent_manifest_digest")
    if revision == 1 and parent is not None:
        raise ManifestError("first_manifest_must_not_have_parent")
    if revision > 1 and parent is None:
        raise ManifestError("later_manifest_requires_parent")
    normalized_artifacts = _normalize_artifacts(artifacts)
    body: Dict[str, Any] = {
        "schema": OUTPUT_MANIFEST_SCHEMA,
        "schema_version": "1",
        "contract_ref": _normalize_contract_ref(contract_ref),
        "project_ref": _require_opaque_ref(project_ref, "project_ref", "project"),
        "admission_id": _require_opaque_ref(admission_id, "admission_id", "admission"),
        "run_ref": _require_opaque_ref(run_ref, "run_ref", "run"),
        "binding_digest": binding,
        "emitted_by_binding_digest": emitted,
        "source_manifest_digest": _require_sha256_ref(source_manifest_digest, "source_manifest_digest"),
        "source_access_profile_digest": _require_sha256_ref(
            source_access_profile_digest, "source_access_profile_digest"
        ),
        "input_digest": _require_sha256_ref(input_digest, "input_digest"),
        "prompt_frame_digest": _require_sha256_ref(prompt_frame_digest, "prompt_frame_digest"),
        "schema_digest": _require_sha256_ref(schema_digest, "schema_digest"),
        "execution_profile_digest": _require_sha256_ref(
            execution_profile_digest, "execution_profile_digest"
        ),
        "output_root_ref": _require_opaque_ref(output_root_ref, "output_root_ref", "output"),
        "artifacts": normalized_artifacts,
        "lineage": _normalize_lineage(lineage, normalized_artifacts),
        "publication_status": _require_enum(
            publication_status, "publication_status", _OUTPUT_STATUSES
        ),
        "manifest_revision": revision,
        "parent_manifest_digest": parent,
    }
    _validate_lineage_references(body["lineage"], normalized_artifacts)
    body["manifest_digest"] = digest_ref(_digest_projection("output_manifest", body))
    body["output_manifest_digest"] = body["manifest_digest"]
    return validate_output_manifest(body)


def validate_output_manifest(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate, canonicalize, and verify one output manifest revision."""
    raw = dict(_require_mapping(value, "output_manifest"))
    allowed = set(digest_spec("output_manifest").fields)
    unknown = set(raw) - allowed
    if unknown:
        raise ManifestError("output_manifest_unknown_fields:%s" % ",".join(sorted(map(str, unknown))))
    required = {
        "schema",
        "schema_version",
        "contract_ref",
        "project_ref",
        "admission_id",
        "run_ref",
        "binding_digest",
        "emitted_by_binding_digest",
        "source_manifest_digest",
        "source_access_profile_digest",
        "input_digest",
        "prompt_frame_digest",
        "schema_digest",
        "execution_profile_digest",
        "output_root_ref",
        "artifacts",
        "lineage",
        "publication_status",
        "manifest_revision",
        "parent_manifest_digest",
        "manifest_digest",
    }
    missing = required - set(raw)
    if missing:
        raise ManifestError("output_manifest_missing_fields:%s" % ",".join(sorted(missing)))
    if _require_string(raw["schema"], "output_manifest.schema") != OUTPUT_MANIFEST_SCHEMA:
        raise ManifestError("output_manifest_schema_mismatch")
    if _require_string(raw["schema_version"], "output_manifest.schema_version") != "1":
        raise ManifestError("output_manifest_schema_version_mismatch")
    binding = _require_sha256_ref(raw["binding_digest"], "output_manifest.binding_digest")
    emitted = _require_sha256_ref(
        raw["emitted_by_binding_digest"], "output_manifest.emitted_by_binding_digest"
    )
    if binding != emitted:
        raise ManifestError("emitted_binding_digest_mismatch")
    revision = _require_positive_int(raw["manifest_revision"], "output_manifest.manifest_revision")
    parent = _optional_sha256_ref(raw["parent_manifest_digest"], "output_manifest.parent_manifest_digest")
    if revision == 1 and parent is not None:
        raise ManifestError("first_manifest_must_not_have_parent")
    if revision > 1 and parent is None:
        raise ManifestError("later_manifest_requires_parent")
    artifacts = _normalize_artifacts(raw["artifacts"])
    lineage = _normalize_lineage(raw["lineage"], artifacts)
    _validate_lineage_references(lineage, artifacts)
    body: Dict[str, Any] = {
        "schema": OUTPUT_MANIFEST_SCHEMA,
        "schema_version": "1",
        "contract_ref": _normalize_contract_ref(raw["contract_ref"]),
        "project_ref": _require_opaque_ref(raw["project_ref"], "output_manifest.project_ref", "project"),
        "admission_id": _require_opaque_ref(raw["admission_id"], "output_manifest.admission_id", "admission"),
        "run_ref": _require_opaque_ref(raw["run_ref"], "output_manifest.run_ref", "run"),
        "binding_digest": binding,
        "emitted_by_binding_digest": emitted,
        "source_manifest_digest": _require_sha256_ref(
            raw["source_manifest_digest"], "output_manifest.source_manifest_digest"
        ),
        "source_access_profile_digest": _require_sha256_ref(
            raw["source_access_profile_digest"],
            "output_manifest.source_access_profile_digest",
        ),
        "input_digest": _require_sha256_ref(raw["input_digest"], "output_manifest.input_digest"),
        "prompt_frame_digest": _require_sha256_ref(
            raw["prompt_frame_digest"], "output_manifest.prompt_frame_digest"
        ),
        "schema_digest": _require_sha256_ref(raw["schema_digest"], "output_manifest.schema_digest"),
        "execution_profile_digest": _require_sha256_ref(
            raw["execution_profile_digest"], "output_manifest.execution_profile_digest"
        ),
        "output_root_ref": _require_opaque_ref(
            raw["output_root_ref"], "output_manifest.output_root_ref", "output"
        ),
        "artifacts": artifacts,
        "lineage": lineage,
        "publication_status": _require_enum(
            raw["publication_status"], "output_manifest.publication_status", _OUTPUT_STATUSES
        ),
        "manifest_revision": revision,
        "parent_manifest_digest": parent,
    }
    actual = _require_sha256_ref(raw["manifest_digest"], "output_manifest.manifest_digest")
    expected = digest_ref(_digest_projection("output_manifest", body))
    if actual != expected:
        raise ManifestError("output_manifest_digest_mismatch")
    if "output_manifest_digest" in raw:
        alias = _require_sha256_ref(raw["output_manifest_digest"], "output_manifest.output_manifest_digest")
        if alias != actual:
            raise ManifestError("output_manifest_digest_alias_mismatch")
    body["manifest_digest"] = actual
    body["output_manifest_digest"] = actual
    return body


@dataclass(frozen=True)
class ReplayResult:
    valid: bool
    schema: str
    admission_id: Optional[str]
    binding_digest: Optional[str]
    current_revision: Optional[int]
    current_manifest_digest: Optional[str]
    revisions: Tuple[int, ...]
    errors: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "schema": self.schema,
            "admission_id": self.admission_id,
            "binding_digest": self.binding_digest,
            "current_revision": self.current_revision,
            "current_manifest_digest": self.current_manifest_digest,
            "revisions": list(self.revisions),
            "errors": list(self.errors),
        }

    def __bool__(self) -> bool:
        return self.valid


def _result_error(
    errors: List[str], message: str, *, strict: bool
) -> None:
    errors.append(message)
    if strict:
        raise RevisionReplayError(message)


def replay_revision_chain(
    value: Any,
    *,
    expected_admission_id: Optional[str] = None,
    expected_binding_digest: Optional[str] = None,
    strict: bool = False,
) -> ReplayResult:
    """Independently replay and verify a serialized chain or manifest sequence.

    The verifier rebuilds every manifest digest and checks revision/parent order;
    it never trusts a chain object's current pointer or a caller's cached digest.
    """
    errors: List[str] = []
    schema = MANIFEST_CHAIN_SCHEMA
    admission: Optional[str] = None
    binding: Optional[str] = None
    current_revision: Optional[int] = None
    current_digest: Optional[str] = None
    revisions: List[int] = []
    try:
        if isinstance(value, (list, tuple)):
            manifests_raw = list(value)
            wrapper: Mapping[str, Any] = {}
        else:
            wrapper = _require_mapping(value, "manifest_chain")
            schema = str(wrapper.get("schema", ""))
            if schema != MANIFEST_CHAIN_SCHEMA:
                _result_error(errors, "manifest_chain_schema_mismatch", strict=strict)
            manifests_raw = wrapper.get("manifest_revisions", wrapper.get("manifests", []))
            if not isinstance(manifests_raw, (list, tuple)):
                _result_error(errors, "manifest_chain_revisions_must_be_array", strict=strict)
                manifests_raw = []
            if wrapper.get("admission_id") is not None:
                admission = _require_opaque_ref(wrapper["admission_id"], "manifest_chain.admission_id", "admission")
            if wrapper.get("binding_digest") is not None:
                binding = _require_sha256_ref(wrapper["binding_digest"], "manifest_chain.binding_digest")
        if expected_admission_id is not None:
            expected = _require_opaque_ref(expected_admission_id, "expected_admission_id", "admission")
            if admission is not None and admission != expected:
                _result_error(errors, "expected_admission_mismatch", strict=strict)
            admission = expected
        if expected_binding_digest is not None:
            expected = _require_sha256_ref(expected_binding_digest, "expected_binding_digest")
            if binding is not None and binding != expected:
                _result_error(errors, "expected_binding_mismatch", strict=strict)
            binding = expected
        previous_digest: Optional[str] = None
        seen_digests = set()
        for index, raw_manifest in enumerate(manifests_raw):
            try:
                manifest = validate_output_manifest(_require_mapping(raw_manifest, "manifest_revisions[]"))
            except ManifestError as exc:
                _result_error(errors, "revision_%d_invalid:%s" % (index + 1, exc), strict=strict)
                continue
            revision = int(manifest["manifest_revision"])
            digest = str(manifest["manifest_digest"])
            revisions.append(revision)
            if revision != index + 1:
                _result_error(errors, "revision_not_monotonic:%d" % revision, strict=strict)
            if revision in revisions[:-1]:
                _result_error(errors, "revision_duplicate:%d" % revision, strict=strict)
            if digest in seen_digests:
                _result_error(errors, "manifest_digest_duplicate:%s" % digest, strict=strict)
            seen_digests.add(digest)
            if previous_digest != manifest["parent_manifest_digest"]:
                _result_error(errors, "parent_manifest_digest_mismatch:%d" % revision, strict=strict)
            previous_digest = digest
            item_admission = str(manifest["admission_id"])
            item_binding = str(manifest["binding_digest"])
            if admission is None:
                admission = item_admission
            elif admission != item_admission:
                _result_error(errors, "cross_admission_reuse:%d" % revision, strict=strict)
            if binding is None:
                binding = item_binding
            elif binding != item_binding:
                _result_error(errors, "cross_binding_reuse:%d" % revision, strict=strict)
        if manifests_raw:
            if revisions:
                current_revision = revisions[-1]
                current_digest = previous_digest
            pointer = wrapper.get("current_pointer") if isinstance(wrapper, Mapping) else None
            if pointer is not None:
                pointer_body = _require_mapping(pointer, "manifest_chain.current_pointer")
                pointer_revision = _require_positive_int(
                    pointer_body.get("manifest_revision"), "manifest_chain.current_pointer.manifest_revision"
                )
                pointer_digest = _require_sha256_ref(
                    pointer_body.get("manifest_digest"), "manifest_chain.current_pointer.manifest_digest"
                )
                if pointer_revision != current_revision or pointer_digest != current_digest:
                    _result_error(errors, "current_pointer_mismatch", strict=strict)
        else:
            if isinstance(wrapper, Mapping) and wrapper.get("current_pointer") is not None:
                _result_error(errors, "empty_chain_has_current_pointer", strict=strict)
        if isinstance(wrapper, Mapping):
            if wrapper.get("current_manifest_digest") is not None:
                wrapped_digest = _require_sha256_ref(
                    wrapper["current_manifest_digest"], "manifest_chain.current_manifest_digest"
                )
                if wrapped_digest != current_digest:
                    _result_error(errors, "current_digest_mismatch", strict=strict)
            if wrapper.get("manifest_revision") is not None:
                wrapped_revision = _require_positive_int(
                    wrapper["manifest_revision"], "manifest_chain.manifest_revision"
                )
                if wrapped_revision != current_revision:
                    _result_error(errors, "current_revision_mismatch", strict=strict)
    except (ManifestError, TypeError, ValueError) as exc:
        _result_error(errors, "replay_input_invalid:%s" % exc, strict=strict)
    return ReplayResult(
        valid=not errors,
        schema=schema,
        admission_id=admission,
        binding_digest=binding,
        current_revision=current_revision,
        current_manifest_digest=current_digest,
        revisions=tuple(revisions),
        errors=tuple(errors),
    )


independent_replay = replay_revision_chain
replay_output_manifest_chain = replay_revision_chain
replay_manifest_chain = replay_revision_chain
REVISION_CHAIN_SCHEMA = MANIFEST_CHAIN_SCHEMA
SOURCE_SCHEMA = SOURCE_MANIFEST_SCHEMA
OUTPUT_SCHEMA = OUTPUT_MANIFEST_SCHEMA


def verify_revision_chain(value: Any, **kwargs: Any) -> ReplayResult:
    result = replay_revision_chain(value, strict=True, **kwargs)
    if not result.valid:  # strict mode raises first error; retained for type clarity.
        raise RevisionReplayError("manifest_chain_invalid")
    return result


class ManifestRevisionChain:
    """In-memory immutable-by-copy revision chain for synthetic evidence."""

    def __init__(
        self,
        *,
        admission_id: Any,
        binding_digest: Any,
        manifests: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> None:
        self.admission_id = _require_opaque_ref(admission_id, "admission_id", "admission")
        self.binding_digest = _require_sha256_ref(binding_digest, "binding_digest")
        self._manifests: List[Dict[str, Any]] = []
        if manifests:
            for manifest in manifests:
                self.append(manifest)

    @property
    def manifests(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._manifests)

    @property
    def revisions(self) -> Tuple[int, ...]:
        return tuple(int(item["manifest_revision"]) for item in self._manifests)

    @property
    def current(self) -> Optional[Dict[str, Any]]:
        return _copy_json(self._manifests[-1]) if self._manifests else None

    @property
    def current_revision(self) -> Optional[int]:
        return self.revisions[-1] if self._manifests else None

    @property
    def current_manifest_digest(self) -> Optional[str]:
        return str(self._manifests[-1]["manifest_digest"]) if self._manifests else None

    def append(self, manifest: Mapping[str, Any]) -> Dict[str, Any]:
        candidate = validate_output_manifest(manifest)
        expected_revision = len(self._manifests) + 1
        if candidate["admission_id"] != self.admission_id:
            raise RevisionReplayError("cross_admission_reuse")
        if candidate["binding_digest"] != self.binding_digest:
            raise RevisionReplayError("cross_binding_reuse")
        if candidate["manifest_revision"] != expected_revision:
            raise RevisionReplayError("revision_not_monotonic")
        expected_parent = self.current_manifest_digest
        if candidate["parent_manifest_digest"] != expected_parent:
            raise RevisionReplayError("parent_manifest_digest_mismatch")
        if candidate["manifest_digest"] in {item["manifest_digest"] for item in self._manifests}:
            raise RevisionReplayError("manifest_digest_duplicate")
        self._manifests.append(candidate)
        return _copy_json(candidate)

    append_manifest = append

    def append_revision(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = dict(kwargs)
        kwargs.setdefault("admission_id", self.admission_id)
        kwargs.setdefault("binding_digest", self.binding_digest)
        kwargs.setdefault("manifest_revision", len(self._manifests) + 1)
        kwargs.setdefault("parent_manifest_digest", self.current_manifest_digest)
        return self.append(build_output_manifest(**kwargs))

    def as_dict(self) -> Dict[str, Any]:
        pointer = None
        if self._manifests:
            pointer = {
                "manifest_revision": self.current_revision,
                "manifest_digest": self.current_manifest_digest,
            }
        return {
            "schema": MANIFEST_CHAIN_SCHEMA,
            "schema_version": "1",
            "admission_id": self.admission_id,
            "binding_digest": self.binding_digest,
            "manifest_revision": self.current_revision,
            "current_manifest_digest": self.current_manifest_digest,
            "current_pointer": pointer,
            "manifest_revisions": [self._copy_manifest(item) for item in self._manifests],
        }

    @staticmethod
    def _copy_manifest(value: Mapping[str, Any]) -> Dict[str, Any]:
        return _copy_json(value)

    def replay(self, *, strict: bool = False) -> ReplayResult:
        return replay_revision_chain(self.as_dict(), strict=strict)


# Small construction aliases used by focused tests and offline callers.
create_source_manifest = build_source_manifest
create_output_manifest = build_output_manifest
make_source_manifest = build_source_manifest
make_output_manifest = build_output_manifest


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ManifestError("cannot_read_json:%s" % path.name) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="医学监查 synthetic manifest 独立摘要与 revision replay（离线、无服务）"
    )
    sub = parser.add_subparsers(dest="command")
    replay = sub.add_parser("replay", help="独立验证 manifest revision chain JSON")
    replay.add_argument("chain", type=Path, help="chain JSON 文件")
    replay.add_argument("--strict", action="store_true", help="首个错误即失败")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.command != "replay":
        parser.print_help(sys.stdout)
        return 2
    try:
        result = replay_revision_chain(_load_json(args.chain), strict=bool(args.strict))
    except ManifestError as exc:
        sys.stderr.write("独立回放失败：%s\n" % exc)
        return 2
    sys.stdout.write(canonical_json(result.as_dict()) + "\n")
    return 0 if result.valid else 2


if __name__ == "__main__":
    sys.exit(main())
