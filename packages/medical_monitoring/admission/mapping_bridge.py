"""C3 adapter from an admitted C1 profile to the existing mapping harness.

The adapter only reshapes deterministic column statistics. It does not
interpret clinical meaning, create mapping decisions, or materialize facts.

Entry to the harness is gated: ``admission_record_to_harness_input`` first
enforces the fail-closed source-to-profile reconciliation
(:mod:`admission.workbook_manifest`), so the dual models can only run on an
input whose physical workbook manifest is present, digest-bound to the
staged files, and fully explained against the admitted tables.

When a deterministic relationship profiler is supplied, the adapter also
embeds its fail-closed relationship evidence
(:mod:`admission.relationship_profile_gate`): same-table pair evidence joins
the harness ``relationships`` channel, cross-table same-name evidence joins
the read-only ``cross_table_relationships`` context, and the whole evidence
payload is content-bound into ``input_sha256`` / ``profile_sha256`` so the
frozen input revision covers it. Mapping submission paths must never run
without that evidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from ..intelligence.primitives import content_hash
from .document_evidence import (
    DocumentEvidenceError,
    validate_document_evidence_packet,
)
from .mapping_gate import MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION
from .relationship_profile_gate import (
    RELATIONSHIP_PROFILE_SCHEMA_VERSION,
    RelationshipProfileGateError,
    cross_table_relationship_entries,
    relationship_input_binding_sha256,
    relationship_rows_by_domain,
    same_table_relationship_entries,
    validate_relationship_profile,
)
from .workbook_manifest import (
    SOURCE_PROFILE_GATE_SCHEMA_VERSION,
    WorkbookManifestError,
    enforce_source_to_profile_gate,
    validate_workbook_manifest_bundle,
)


MAPPING_BRIDGE_SCHEMA_VERSION = "mm-c3-mapping-profile-bridge-v8"
_LEGACY_MAPPING_BRIDGE_SCHEMA_VERSION = "mm-c3-mapping-profile-bridge-v7"
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


def _is_non_bool_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


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
    revisions_by_basename: dict[str, set[str]] = {}
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
        revisions_by_basename.setdefault(path.rsplit("/", 1)[-1], set()).add(
            revision
        )
    for basename, revisions in revisions_by_basename.items():
        if len(revisions) == 1:
            revision_by_file[basename] = next(iter(revisions))
    return bindings, revision_by_file


def _sheet_indexes(
    technical: Mapping[str, Any],
    revision_by_file: Mapping[str, str],
) -> dict[tuple[str, str], int]:
    bundle = validate_workbook_manifest_bundle(technical.get("physical_manifest"))
    result: dict[tuple[str, str], int] = {}
    for entry in bundle["files"]:
        source_file = str(entry["source_file"])
        revision_id = revision_by_file.get(
            source_file,
            revision_by_file.get(source_file.rsplit("/", 1)[-1], ""),
        )
        if not revision_id:
            raise MappingBridgeError("manifest source identity is ambiguous")
        for sheet in entry["manifest"]["sheets"]:
            key = (revision_id, str(sheet["sheet_name"]))
            if key in result:
                raise MappingBridgeError("manifest sheet identity is ambiguous")
            result[key] = int(sheet["sheet_index"])
    return result


def _table_bindings(
    tables: Sequence[Mapping[str, Any]],
    technical: Mapping[str, Any],
    revision_by_file: Mapping[str, str],
    sheet_indexes: Mapping[tuple[str, str], int],
) -> list[dict[str, Any]]:
    snapshot_ids = technical.get("snapshot_ids")
    if not isinstance(snapshot_ids, list) or len(snapshot_ids) != len(tables):
        raise MappingBridgeError("admission table identity is inconsistent")
    result: list[dict[str, str]] = []
    for table, snapshot_id in zip(tables, snapshot_ids):
        domain = str(table.get("name") or table.get("table_name") or "").strip()
        source_file = str(table.get("source_file") or "").strip()
        revision_id = revision_by_file.get(source_file, "")
        snapshot = str(snapshot_id or "").strip()
        sheet_index = sheet_indexes.get((revision_id, domain))
        if (
            not domain or not source_file or not revision_id or not snapshot
            or not _is_non_bool_int(sheet_index) or sheet_index < 1
        ):
            raise MappingBridgeError("admission table identity is incomplete")
        binding_id = "mmtable_" + content_hash({
            "source_revision_id": revision_id,
            "sheet_index": sheet_index,
            "sheet_name": domain,
            "snapshot_id": snapshot,
        })[:28]
        result.append({
            "table_binding_id": binding_id,
            "domain": domain,
            "source_file": source_file,
            "source_revision_id": revision_id,
            "snapshot_id": snapshot,
            "sheet_index": sheet_index,
        })
    return result


def _date_range_payload(column: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    raw = column.get("date_range")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise MappingBridgeError("admission field date range is malformed")
    minimum = str(raw.get("min") or "").strip()
    maximum = str(raw.get("max") or "").strip()
    parsed_count = int(raw.get("parsed_count") or 0)
    if not minimum or not maximum or parsed_count <= 0:
        raise MappingBridgeError("admission field date range is incomplete")
    return {"min": minimum, "max": maximum, "parsed_count": parsed_count}


def _field_payload(
    table: Mapping[str, Any],
    column: Mapping[str, Any],
    column_index: int,
    rows: Sequence[Mapping[str, Any]],
    columns: Sequence[Mapping[str, Any]],
    table_binding: Mapping[str, Any],
) -> dict[str, Any]:
    domain = str(table.get("name") or table.get("table_name") or "").strip()
    field = str(column.get("name") or "").strip()
    row_count = int(table.get("row_count") or 0)
    missing_count = int(column.get("missing_count") or 0)
    if not domain or not field or row_count < 0 or not 0 <= missing_count <= row_count:
        raise MappingBridgeError("admission field statistics are invalid")
    if not _is_non_bool_int(column_index) or column_index < 0:
        raise MappingBridgeError("admission field position is invalid")
    suggested_roles = column.get("suggested_roles") or []
    identifier = (
        isinstance(suggested_roles, list) and _SUBJECT_ROLE in suggested_roles
    )
    observed = [
        row.get(field)
        for row in rows
        if row.get(field) is not None and str(row.get(field)).strip()
    ]
    if not observed:
        observed = [
            value
            for value in (column.get("samples") or [])
            if value is not None and str(value).strip()
        ]
    frequencies = Counter(str(value)[:160] for value in observed)
    top_values = (
        [{"value": {"redacted": "identifier"}, "count": len(observed)}]
        if identifier and observed
        else [
            {"value": value, "count": count}
            for value, count in sorted(
                frequencies.items(), key=lambda item: (-item[1], item[0])
            )[:10]
        ]
    )
    representative_values = (
        [{"redacted": "identifier"}]
        if identifier and observed
        else [item["value"] for item in top_values[:5]]
    )
    same_row_examples = _same_row_examples(
        field=field,
        column_index=column_index,
        columns=columns,
        rows=rows,
    )
    return {
        "field_binding_id": "mmfield_" + content_hash({
            "table_binding_id": table_binding["table_binding_id"],
            "column_index": column_index,
            "field": field,
        })[:28],
        "table_binding_id": table_binding["table_binding_id"],
        "source_revision_id": table_binding["source_revision_id"],
        "sheet_index": table_binding["sheet_index"],
        "domain": domain,
        "field": field,
        "source_label": str(column.get("source_label") or field).strip(),
        "column_index": column_index,
        "total_rows": row_count,
        "non_empty_count": row_count - missing_count,
        "null_rate": (
            round(missing_count / row_count, 6) if row_count else 1.0
        ),
        "inferred_type": _TYPE_MAP.get(
            str(column.get("inferred_type") or "").strip(), "string"
        ),
        "unique_value_count": int(column.get("distinct_count") or 0),
        "values_redacted": identifier,
        "top_values": top_values,
        "representative_values": representative_values,
        "representative_sample_count": len(representative_values),
        "date_range": _date_range_payload(column),
        "anomaly_examples": [],
        "same_row_examples": same_row_examples,
    }


def _same_row_examples(
    *,
    field: str,
    column_index: int,
    columns: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return bounded, desensitized neighbouring values from real rows.

    These examples preserve the relationship between one value and its table
    context without sending subject identifiers or entire rows to the model.
    Selection is deterministic and generic: first, middle and last populated
    rows, with two source columns on either side of the target column.
    """

    populated = [
        row for row in rows
        if row.get(field) is not None and str(row.get(field)).strip()
    ]
    if not populated:
        return []
    positions = sorted({0, len(populated) // 2, len(populated) - 1})
    start = max(0, column_index - 2)
    end = min(len(columns), column_index + 3)
    visible_columns = columns[start:end]
    result: list[dict[str, Any]] = []
    for position in positions:
        row = populated[position]
        values = []
        for column in visible_columns:
            name = str(column.get("name") or "").strip()
            value = row.get(name)
            if value is None or not str(value).strip():
                continue
            roles = column.get("suggested_roles") or []
            is_identifier = isinstance(roles, list) and _SUBJECT_ROLE in roles
            values.append({
                "field": name,
                "value": (
                    {"redacted": "identifier"}
                    if is_identifier
                    else str(value)[:160]
                ),
            })
        if values:
            result.append({"nearby_values": values})
    return result


def admission_record_to_harness_input(
    *,
    project_id: str,
    attempt_id: str,
    record: Mapping[str, Any],
    table_rows_by_snapshot: Optional[
        Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]]
    ] = None,
    relationship_profiler: Optional[Callable[..., Any]] = None,
    require_document_evidence: bool = False,
) -> MappingHarnessInput:
    """Build the exact input accepted by ``MonitoringAiService``.

    The record must first pass the fail-closed source-to-profile gate: the
    dual models never see an input whose physical workbook manifest is
    missing, mutated after admission, or not fully reconciled with the
    admitted tables.  The reconciliation summary is bound into the harness
    profile via ``input_completeness`` and participates in ``input_sha256``.

    When ``relationship_profiler`` is provided it must be a pure deterministic
    callable invoked as ``profiler(rows_by_domain=..., table_field_order=...,
    input_binding_sha256=...)`` returning the payload contract of
    :mod:`admission.relationship_profile_gate`. The evidence is validated
    fail-closed and bound into the frozen input digests; a missing, malformed
    or unbound payload refuses the whole mapping input. Submission paths
    (the admission mapping pipeline) must always supply the profiler; the
    parameter stays optional only for the pure-adapter recovery paths.
    """
    if record.get("project_id") != project_id or record.get("attempt_id") != attempt_id:
        raise MappingBridgeError("admission identity does not match mapping request")
    try:
        completeness = enforce_source_to_profile_gate(record)
    except WorkbookManifestError as exc:
        error = MappingBridgeError(
            f"source-to-profile gate refused the mapping input: {exc}"
        )
        error.code = exc.code
        error.findings = exc.findings
        raise error from exc
    tables = record.get("tables")
    technical = record.get("technical_details")
    if not isinstance(tables, list) or not tables or not isinstance(technical, Mapping):
        raise MappingBridgeError("admission profile is incomplete")
    source_bindings, revision_by_file = _source_bindings(technical)
    sheet_indexes = _sheet_indexes(technical, revision_by_file)
    table_bindings = _table_bindings(
        tables, technical, revision_by_file, sheet_indexes
    )
    fields = []
    table_field_order: Dict[str, list[str]] = {}
    snapshot_ids = technical.get("snapshot_ids") or []
    if len(snapshot_ids) != len(tables):
        raise MappingBridgeError("admission table snapshot binding is incomplete")
    rows_by_snapshot = dict(table_rows_by_snapshot or {})
    for table_index, table in enumerate(tables):
        domain = str(table.get("name") or table.get("table_name") or "").strip()
        columns = table.get("columns") or []
        if not isinstance(columns, Sequence) or isinstance(columns, (str, bytes)):
            raise MappingBridgeError("admission table columns are malformed")
        snapshot_id = str(snapshot_ids[table_index] or "")
        snapshot_content = rows_by_snapshot.get(snapshot_id, {})
        rows = snapshot_content.get(domain, []) if isinstance(snapshot_content, Mapping) else []
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise MappingBridgeError("admission table content is malformed")
        table_field_order[domain] = [
            str(column.get("name") or "").strip()
            for column in columns
            if isinstance(column, Mapping)
        ]
        for column_index, column in enumerate(columns):
            if isinstance(column, Mapping):
                fields.append(
                    _field_payload(
                        table,
                        column,
                        column_index,
                        rows,
                        columns,
                        table_bindings[table_index],
                    )
                )
    if not fields:
        raise MappingBridgeError("admission profile has no fields")
    field_pairs = [(item["domain"], item["field"]) for item in fields]
    if len(field_pairs) != len(set(field_pairs)):
        raise MappingBridgeError("admission profile field identity is ambiguous")
    if any(
        len(order) != len(set(order)) or "" in order
        for order in table_field_order.values()
    ):
        raise MappingBridgeError("admission profile table field order is ambiguous")
    domains = list(dict.fromkeys(item["domain"] for item in fields))
    source_sha256s = [item["source_content_sha256"] for item in source_bindings]
    raw_document_evidence = technical.get("monitoring_document_evidence")
    document_evidence: dict[str, Any] = {}
    if raw_document_evidence is not None:
        try:
            document_evidence = validate_document_evidence_packet(
                raw_document_evidence,
                project_id=project_id,
                require_mapping_context=require_document_evidence,
            )
        except DocumentEvidenceError as exc:
            error = MappingBridgeError(
                f"document evidence gate refused the mapping input: {exc.code}"
            )
            error.code = exc.code
            raise error from exc
    elif require_document_evidence:
        error = MappingBridgeError(
            "document evidence gate refused the mapping input: "
            "mapping_document_evidence_missing"
        )
        error.code = "mapping_document_evidence_missing"
        raise error
    input_completeness = {
        "gate_schema_version": SOURCE_PROFILE_GATE_SCHEMA_VERSION,
        "manifest_schema_version": completeness["manifest_schema_version"],
        "manifest_sha256": completeness["manifest_sha256"],
        "reconciliation": completeness,
    }
    relationship_summary: dict[str, Any] = {}
    relationship_sections: dict[str, Any] = {}
    if relationship_profiler is not None:
        try:
            evidence_rows_by_domain = relationship_rows_by_domain(
                table_bindings,
                rows_by_snapshot,
            )
            input_binding_sha256 = relationship_input_binding_sha256(
                rows_by_snapshot
            )
            payload = validate_relationship_profile(
                relationship_profiler(
                    rows_by_domain=evidence_rows_by_domain,
                    table_field_order=table_field_order,
                    input_binding_sha256=input_binding_sha256,
                ),
                fields_by_domain={
                    domain: set(order)
                    for domain, order in table_field_order.items()
                },
                rows_by_domain=evidence_rows_by_domain,
                input_binding_sha256=input_binding_sha256,
            )
        except RelationshipProfileGateError as exc:
            error = MappingBridgeError(
                f"relationship profile gate refused the mapping input: {exc.code}"
            )
            error.code = exc.code
            raise error from exc
        except Exception as exc:
            error = MappingBridgeError(
                "relationship profiler failed before the evidence could be gated"
            )
            error.code = "relationship_profiler_failed"
            raise error from exc
        same_table_entries = same_table_relationship_entries(payload)
        cross_table_entries = cross_table_relationship_entries(payload)
        relationship_summary = {
            "schema_version": RELATIONSHIP_PROFILE_SCHEMA_VERSION,
            "profiler_contract": payload["profiler_contract"],
            "input_binding_sha256": payload["input_binding_sha256"],
            "evidence_sha256": content_hash(payload),
            "same_table_pair_count": len(same_table_entries),
            "cross_table_entry_count": len(cross_table_entries),
        }
        relationship_sections = {
            "relationships": same_table_entries,
            "cross_table_relationships": cross_table_entries,
            "relationship_profile": relationship_summary,
        }
    input_sha256 = content_hash({
        "mapping_cohort_schema_version": MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION,
        "project_id": project_id,
        "attempt_id": attempt_id,
        "sources": source_bindings,
        "table_bindings": table_bindings,
        "fields": fields,
        "input_completeness": input_completeness,
        "relationship_profile": relationship_summary,
        "relationships": relationship_sections.get("relationships", []),
        "cross_table_relationships": relationship_sections.get(
            "cross_table_relationships",
            [],
        ),
        "document_evidence": document_evidence,
    })
    profile: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "bridge_schema_version": (
            MAPPING_BRIDGE_SCHEMA_VERSION
            if document_evidence
            else _LEGACY_MAPPING_BRIDGE_SCHEMA_VERSION
        ),
        "mapping_cohort_schema_version": MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION,
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
        "relationships": relationship_sections.get("relationships", []),
        "table_bindings": table_bindings,
        "table_field_order": [
            {"domain": domain, "field_order": order}
            for domain, order in table_field_order.items()
        ],
        "input_completeness": input_completeness,
        "document_evidence": document_evidence,
        "payload_policy": (
            "bounded_full_column_statistics_source_labels_"
            "redacted_row_context_and_relationship_profile_v4"
        ),
    }
    if relationship_sections:
        profile.update(relationship_sections)
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
