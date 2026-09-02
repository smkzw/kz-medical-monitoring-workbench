"""C3 adapter from an admitted C1 profile to the existing mapping harness.

The adapter only reshapes deterministic column statistics. It does not
interpret clinical meaning, create mapping decisions, or materialize facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence

from ..intelligence.primitives import content_hash


MAPPING_BRIDGE_SCHEMA_VERSION = "mm-c3-mapping-profile-bridge-v1"
PROFILE_SCHEMA_VERSION = "monitoring_ai_field_profile_v3"
_SUBJECT_ROLE = "受试者标识"
_TYPE_MAP = {
    "text": "string",
    "number": "decimal",
    "date": "date",
    "empty": "string",
    "mixed": "string",
}


class MappingBridgeError(ValueError):
    """Fail-closed profile bridge violation."""


@dataclass(frozen=True)
class MappingHarnessInput:
    field_profile: Dict[str, Any]
    input_revision: Dict[str, Any]


def _source_bindings(
    technical: Mapping[str, Any],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    files = technical.get("files")
    revision_ids = technical.get("revision_ids")
    if not isinstance(files, list) or not isinstance(revision_ids, list):
        raise MappingBridgeError("admission source identity is incomplete")
    if not files or len(files) != len(revision_ids):
        raise MappingBridgeError("admission source identity is inconsistent")
    bindings: list[dict[str, str]] = []
    revision_by_file: dict[str, str] = {}
    for file_item, revision_id in zip(files, revision_ids):
        if not isinstance(file_item, Mapping):
            raise MappingBridgeError("admission file identity is malformed")
        path = str(file_item.get("path") or "").strip()
        digest = str(file_item.get("sha256") or "").strip()
        revision = str(revision_id or "").strip()
        if not path or not revision or len(digest) != 64:
            raise MappingBridgeError("admission file identity is malformed")
        bindings.append({
            "source_entry_id": revision,
            "source_content_sha256": digest,
        })
        revision_by_file[path] = revision
        revision_by_file[path.rsplit("/", 1)[-1]] = revision
    return bindings, revision_by_file


def _table_bindings(
    tables: Sequence[Mapping[str, Any]],
    technical: Mapping[str, Any],
    revision_by_file: Mapping[str, str],
) -> list[dict[str, str]]:
    snapshot_ids = technical.get("snapshot_ids")
    if not isinstance(snapshot_ids, list) or len(snapshot_ids) != len(tables):
        raise MappingBridgeError("admission table identity is inconsistent")
    result: list[dict[str, str]] = []
    for table, snapshot_id in zip(tables, snapshot_ids):
        domain = str(table.get("name") or table.get("table_name") or "").strip()
        source_file = str(table.get("source_file") or "").strip()
        revision_id = revision_by_file.get(source_file, "")
        snapshot = str(snapshot_id or "").strip()
        if not domain or not source_file or not revision_id or not snapshot:
            raise MappingBridgeError("admission table identity is incomplete")
        result.append({
            "domain": domain,
            "source_file": source_file,
            "source_revision_id": revision_id,
            "snapshot_id": snapshot,
        })
    return result


def _field_payload(
    table: Mapping[str, Any], column: Mapping[str, Any]
) -> dict[str, Any]:
    domain = str(table.get("name") or table.get("table_name") or "").strip()
    field = str(column.get("name") or "").strip()
    row_count = int(table.get("row_count") or 0)
    missing_count = int(column.get("missing_count") or 0)
    if not domain or not field or row_count <= 0 or not 0 <= missing_count <= row_count:
        raise MappingBridgeError("admission field statistics are invalid")
    suggested_roles = column.get("suggested_roles") or []
    identifier = (
        isinstance(suggested_roles, list) and _SUBJECT_ROLE in suggested_roles
    )
    samples = column.get("samples") or []
    representative_values = (
        [{"redacted": "identifier"}]
        if identifier
        else [str(value)[:160] for value in samples[:5] if value is not None]
    )
    return {
        "domain": domain,
        "field": field,
        "total_rows": row_count,
        "non_empty_count": row_count - missing_count,
        "null_rate": round(missing_count / row_count, 6),
        "inferred_type": _TYPE_MAP.get(
            str(column.get("inferred_type") or "").strip(), "string"
        ),
        "unique_value_count": int(column.get("distinct_count") or 0),
        "values_redacted": identifier,
        "top_values": [],
        "representative_values": representative_values,
        "anomaly_examples": [],
    }


def admission_record_to_harness_input(
    *, project_id: str, attempt_id: str, record: Mapping[str, Any]
) -> MappingHarnessInput:
    """Build the exact input accepted by ``MonitoringAiService``."""
    if record.get("project_id") != project_id or record.get("attempt_id") != attempt_id:
        raise MappingBridgeError("admission identity does not match mapping request")
    tables = record.get("tables")
    technical = record.get("technical_details")
    if not isinstance(tables, list) or not tables or not isinstance(technical, Mapping):
        raise MappingBridgeError("admission profile is incomplete")
    source_bindings, revision_by_file = _source_bindings(technical)
    table_bindings = _table_bindings(tables, technical, revision_by_file)
    fields = [
        _field_payload(table, column)
        for table in tables
        for column in (table.get("columns") or [])
        if isinstance(column, Mapping)
    ]
    if not fields:
        raise MappingBridgeError("admission profile has no fields")
    field_pairs = [(item["domain"], item["field"]) for item in fields]
    if len(field_pairs) != len(set(field_pairs)):
        raise MappingBridgeError("admission profile field identity is ambiguous")
    domains = list(dict.fromkeys(item["domain"] for item in fields))
    source_sha256s = [item["source_content_sha256"] for item in source_bindings]
    input_sha256 = content_hash({
        "project_id": project_id,
        "attempt_id": attempt_id,
        "sources": source_bindings,
        "table_bindings": table_bindings,
        "fields": fields,
    })
    profile: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "bridge_schema_version": MAPPING_BRIDGE_SCHEMA_VERSION,
        "batch_id": attempt_id,
        "project_id": project_id,
        "batch_revision": 1,
        "mapping_revision": None,
        "expected_domains": domains,
        "source_bindings": source_bindings,
        "source_sha256s": source_sha256s,
        "row_count": sum(int(table.get("row_count") or 0) for table in tables),
        "input_sha256": input_sha256,
        "fields": fields,
        "relationships": [],
        "table_bindings": table_bindings,
        "payload_policy": "field_statistics_without_row_or_identifier_values_v1",
    }
    profile["profile_sha256"] = content_hash(profile)
    revision = {
        "project_id": project_id,
        "batch_revision": attempt_id,
        "source_binding_revision": content_hash(source_bindings),
        "sources": source_bindings,
    }
    return MappingHarnessInput(field_profile=profile, input_revision=revision)


__all__ = [
    "MAPPING_BRIDGE_SCHEMA_VERSION",
    "MappingBridgeError",
    "MappingHarnessInput",
    "admission_record_to_harness_input",
]
