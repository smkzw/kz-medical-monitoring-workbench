"""Exact listing evidence reads for the product's independent model harness.

This module returns observations and physical locators, never semantic decisions.
The caller supplies the job's frozen profile and owns the store lifetime.
"""

from __future__ import annotations

import json

from collections import Counter
from copy import deepcopy
from typing import Any, Mapping

from ..intelligence.primitives import canonical_json, content_hash
from ..intelligence.structure_profile import SourceCellLocator
from .pipeline import LOCATOR_INDEX_KIND


class SourceToolError(ValueError):
    pass


def _integer(value: Any, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SourceToolError("invalid_source_read_range")
    return value


class FrozenListingEvidenceTools:
    """Read only tables explicitly bound to one immutable mapping input."""

    def __init__(self, store: Any, *, project_id: str, input_revision: str,
                 field_profile: Mapping[str, Any]):
        self.store = store
        self.project_id = project_id
        self.input_revision = input_revision
        self.profile = deepcopy(dict(field_profile))
        if self.profile.get("project_id") != project_id or not input_revision:
            raise SourceToolError("source_read_identity_mismatch")

    def _table(self, table_binding_id: str):
        bindings = [item for item in self.profile.get("table_bindings", [])
                    if item.get("table_binding_id") == table_binding_id]
        if len(bindings) != 1:
            raise SourceToolError("source_table_not_bound")
        binding = bindings[0]
        snapshot = self.store.get_listing_snapshot(binding["snapshot_id"])
        if (snapshot.project_id != self.project_id
                or snapshot.revision_id != binding["source_revision_id"]):
            raise SourceToolError("source_read_identity_mismatch")
        content = self.store.load_listing_content(snapshot.snapshot_id)
        if content_hash(content) != snapshot.content_hash:
            raise SourceToolError("source_content_changed")
        persisted = self.store.get_domain_object(LOCATOR_INDEX_KIND, snapshot.snapshot_id)
        if persisted is None:
            raise SourceToolError("source_locator_missing")
        index = persisted[1]
        digests = {item["source_entry_id"]: item["source_content_sha256"]
                   for item in self.profile.get("source_bindings", [])}
        if (index.get("project_id") != self.project_id
                or index.get("snapshot_id") != snapshot.snapshot_id
                or index.get("source_revision_id") != snapshot.revision_id
                or index.get("table_name") != binding["domain"]
                or index.get("source_file_digest") != digests.get(snapshot.revision_id)):
            raise SourceToolError("source_locator_identity_mismatch")
        rows = content.get(index["table_name"])
        columns = index.get("columns", [])
        if (not isinstance(rows, list) or len(rows) != snapshot.row_count
                or len(index.get("row_numbers", [])) != len(rows)
                or len(index.get("locator_ids", [])) != len(rows) * len(columns)):
            raise SourceToolError("source_locator_incomplete")
        return binding, snapshot, index, rows, columns

    def read_source_region(self, *, table_binding_id: str, row_start: int = 0,
                           row_count: int = 20, column_indexes: list[int]):
        binding, snapshot, index, rows, columns = self._table(table_binding_id)
        start = _integer(row_start, minimum=0, maximum=len(rows))
        count = _integer(row_count, minimum=1, maximum=40)
        if (not isinstance(column_indexes, list) or not 1 <= len(column_indexes) <= 12):
            raise SourceToolError("invalid_source_columns")
        selected = [_integer(value, minimum=0, maximum=len(columns) - 1)
                    for value in column_indexes]
        if len(set(selected)) != len(selected):
            raise SourceToolError("invalid_source_columns")
        end = min(len(rows), start + count)
        cells = self._cells(snapshot, index, rows, columns, range(start, end), selected)
        return self._result(binding, snapshot, {
            "coverage_scope": "canonical_table_cells",
            "cells": cells, "total_rows": len(rows), "total_columns": len(columns),
            "row_start": start, "row_end_exclusive": end, "column_indexes": selected,
            "next_row_start": end if end < len(rows) else None,
            "coverage": "complete" if start == 0 and end == len(rows) and len(selected) == len(columns) else "partial",
        })

    def _cells(self, snapshot, index, rows, columns, row_indexes, selected):
        cells = []
        for row_index in row_indexes:
            for column_index in selected:
                column = columns[column_index]
                locator = SourceCellLocator(
                    project_id=self.project_id, source_revision_id=snapshot.revision_id,
                    snapshot_id=snapshot.snapshot_id, source_file=index["source_file"],
                    source_file_digest=index["source_file_digest"], table_name=index["table_name"],
                    row_index=row_index, row_number=index["row_numbers"][row_index],
                    column=column, column_index=column_index, raw_value=rows[row_index][column],
                    locator_id=index["locator_ids"][row_index * len(columns) + column_index],
                )
                cells.append({**locator.identity_payload(), "locator_id": locator.locator_id})
        return cells

    def sample_rows(self, *, table_binding_id: str, filter_column_index: int,
                    raw_value: Any, column_indexes: list[int], offset: int = 0, limit: int = 12):
        """Locate exact typed values across the full table and read their row context."""
        binding, snapshot, index, rows, columns = self._table(table_binding_id)
        filter_index = _integer(filter_column_index, minimum=0, maximum=len(columns) - 1)
        limit = _integer(limit, minimum=1, maximum=12)
        if not isinstance(column_indexes, list) or not 1 <= len(column_indexes) <= 12:
            raise SourceToolError("invalid_source_columns")
        selected = [_integer(value, minimum=0, maximum=len(columns) - 1)
                    for value in column_indexes]
        if len(set(selected)) != len(selected):
            raise SourceToolError("invalid_source_columns")
        encoded = canonical_json(raw_value)
        matches = [i for i, row in enumerate(rows)
                   if canonical_json(row[columns[filter_index]]) == encoded]
        offset = _integer(offset, minimum=0, maximum=len(matches))
        end = min(len(matches), offset + limit)
        return self._result(binding, snapshot, {
            "coverage_scope": "exact_value_row_context", "coverage": "partial",
            "filter_column_index": filter_index, "raw_value": raw_value,
            "scanned_rows": len(rows), "matching_row_count": len(matches),
            "column_indexes": selected, "offset": offset,
            "next_offset": end if end < len(matches) else None,
            "cells": self._cells(snapshot, index, rows, columns, matches[offset:end], selected),
            "absence_claim_supported": False,
        })

    def get_column_profile(self, *, table_binding_id: str, column_index: int,
                           offset: int = 0, limit: int = 20):
        binding, snapshot, index, rows, columns = self._table(table_binding_id)
        column_index = _integer(column_index, minimum=0, maximum=len(columns) - 1)
        limit = _integer(limit, minimum=1, maximum=100)
        values = Counter(canonical_json(row[columns[column_index]]) for row in rows)
        ordered = sorted(values.items(), key=lambda item: (-item[1], item[0]))
        offset = _integer(offset, minimum=0, maximum=len(ordered))
        end = min(len(ordered), offset + limit)
        return self._result(binding, snapshot, {
            "coverage_scope": "column_value_distribution",
            "column_index": column_index, "column": columns[column_index],
            "total_rows": len(rows), "unique_value_count": len(ordered),
            "values": [{"value": json.loads(value), "count": count} for value, count in ordered[offset:end]],
            "distribution_scanned_rows": len(rows),
            "next_offset": end if end < len(ordered) else None,
            "coverage": "complete" if offset == 0 and end == len(ordered) else "partial",
        })

    def _result(self, binding, snapshot, body):
        result = {
            "schema_version": "mm-frozen-listing-tool-v1",
            "project_id": self.project_id, "input_revision_sha256": self.input_revision,
            "table_binding_id": binding["table_binding_id"],
            "source_revision_id": snapshot.revision_id, "snapshot_id": snapshot.snapshot_id,
            "snapshot_content_sha256": snapshot.content_hash,
            "sheet_index": binding["sheet_index"], "data": body,
        }
        if len(canonical_json(result).encode("utf-8")) > 256_000:
            raise SourceToolError("source_result_too_large_request_smaller_region")
        return {**result, "result_sha256": content_hash(result)}
