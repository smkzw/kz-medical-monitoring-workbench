"""Manifest contract, fail-closed gate, and live-surface adapter for the C3
workbook physical-integrity matrix.

``evaluate_manifest_completeness`` is the structural gate: a manifest that
omits any required evidence key, carries an out-of-enum visibility, or types
a field wrongly can never evaluate complete.
``reconcile_manifest_against_observation`` proves the manifest explains every
fact the :mod:`~tests.medical_monitoring.workbook_manifest_oracle` observes in
the raw OOXML; omitted evidence therefore cannot auto-pass.
``build_manifest_via_contract`` is the single seam to the landed work item 1
surface: when worker_01 moves the accessor, adapt that one function.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Mapping, Tuple

from tests.medical_monitoring.workbook_manifest_fixtures import WorkbookCase
from tests.medical_monitoring.workbook_manifest_oracle import (
    _column_format_view,
    _split_coordinate,
)

MANIFEST_CONTRACT_VERSION = "workbook_physical_evidence_v1"
VISIBILITY_STATES = ("visible", "hidden", "veryHidden")
REQUIRED_MANIFEST_KEYS = ("manifest_version", "source_file", "workbook", "sheets")
REQUIRED_WORKBOOK_INFO_KEYS = ("sheet_count", "sheet_order")
REQUIRED_SHEET_KEYS = (
    "sheet_name",
    "sheet_index",
    "visibility",
    "used_range",
    "physical_row_count",
    "physical_column_count",
    "is_empty",
    "is_header_only",
    "header_row_numbers",
    "merged_cell_ranges",
    "hidden_row_numbers",
    "hidden_column_letters",
    "named_tables",
    "autofilter_ref",
    "formula_cells",
    "number_format_columns",
    "leading_zero_text_cells",
    "duplicate_source_headers",
)
#: Per-sheet keys the oracle derives from raw OOXML (the physical projection
#: the fixture self-check compares against the declared ground truth).
OBSERVED_PHYSICAL_KEYS = (
    "used_range",
    "physical_row_count",
    "physical_column_count",
    "merged_cell_ranges",
    "hidden_row_numbers",
    "hidden_column_letters",
    "named_tables",
    "autofilter_ref",
    "formula_cells",
    "number_format_cells",
    "leading_zero_text_cells",
    "duplicate_source_headers",
)


def declared_physical_projection(ground_truth: Mapping[str, Any]) -> Dict[str, Any]:
    """The oracle-comparable subset of a case's declared ground truth."""
    return {
        "sheet_order": list(ground_truth["sheet_order"]),
        "sheet_visibility": dict(ground_truth["sheet_visibility"]),
        "sheets": {
            name: {key: sheet[key] for key in OBSERVED_PHYSICAL_KEYS}
            for name, sheet in ground_truth["sheets"].items()
        },
    }


def check_declared_intent_consistency(ground_truth: Mapping[str, Any]) -> List[str]:
    """Cross-check declared semantic fields (header rows, header-only) against
    the oracle-derivable bounds; returns violations.  Sheets without declared
    intent (visibility / empty-sheet cases) are skipped."""
    violations: List[str] = []
    sheets = ground_truth["sheets"]
    header_rows_by_sheet: Mapping[str, List[int]] = ground_truth.get("header_row_numbers", {})
    header_only_by_sheet: Mapping[str, bool] = ground_truth.get("is_header_only", {})
    for name, header_rows in header_rows_by_sheet.items():
        observed = sheets[name]
        if header_rows and max(header_rows) > observed["physical_row_count"]:
            violations.append(
                f"{name}: declared header rows {header_rows} exceed physical rows "
                f"{observed['physical_row_count']}"
            )
    for name, is_header_only in header_only_by_sheet.items():
        header_rows = header_rows_by_sheet.get(name)
        if header_rows is None:
            continue
        if is_header_only != (
            sheets[name]["physical_row_count"] == max(header_rows) and bool(header_rows)
        ):
            violations.append(
                f"{name}: is_header_only={is_header_only} contradicts physical rows "
                f"{sheets[name]['physical_row_count']} and header rows {header_rows}"
            )
    return violations


# ---------------------------------------------------------------------------
# Manifest contract: completeness gate + OOXML reconciliation
# ---------------------------------------------------------------------------

class ManifestIncompleteError(AssertionError):
    """A manifest is missing required physical evidence: fail closed."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_mapping_list(
    container: Any,
    container_label: str,
    required_fields: Mapping[str, str],
) -> List[str]:
    violations: List[str] = []
    if not isinstance(container, list):
        return [f"{container_label} must be a list"]
    for index, entry in enumerate(container):
        label = f"{container_label}[{index}]"
        if not isinstance(entry, Mapping):
            violations.append(f"{label} must be a mapping")
            continue
        for field, expectation in required_fields.items():
            if field not in entry:
                violations.append(f"{label} missing key: {field}")
                continue
            value = entry[field]
            if expectation == "non_empty_str" and not (
                isinstance(value, str) and value.strip()
            ):
                violations.append(f"{label}.{field} must be a non-empty string")
            elif expectation == "int_list" and not (
                isinstance(value, list)
                and all(_is_int(item) and item >= 1 for item in value)
            ):
                violations.append(f"{label}.{field} must be a list of positive integers")
            elif expectation == "bool" and type(value) is not bool:
                violations.append(f"{label}.{field} must be a boolean")
            elif expectation == "nullable_str" and value is not None and not (
                isinstance(value, str) and value.strip()
            ):
                violations.append(f"{label}.{field} must be a non-empty string or null")
    return violations


def evaluate_manifest_completeness(manifest: Any) -> List[str]:
    """Structural completeness gate over ``MANIFEST_CONTRACT``.

    A manifest that omits any required evidence key, carries an out-of-enum
    visibility, or types a field wrongly is reported as incomplete.  Empty
    lists are legal evidence ("none observed") — whether that is true for a
    given workbook is the oracle's job, not the gate's.
    """
    violations: List[str] = []
    if not isinstance(manifest, Mapping):
        return ["manifest must be a mapping"]
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            violations.append(f"missing manifest key: {key}")
    if not isinstance(manifest.get("manifest_version"), str) or not manifest["manifest_version"].strip():
        violations.append("manifest_version must be a non-empty string")
    if not isinstance(manifest.get("source_file"), str) or not manifest["source_file"].strip():
        violations.append("source_file must be a non-empty string")

    workbook = manifest.get("workbook")
    if not isinstance(workbook, Mapping):
        violations.append("workbook must be a mapping")
    else:
        for key in REQUIRED_WORKBOOK_INFO_KEYS:
            if key not in workbook:
                violations.append(f"missing workbook key: {key}")
        if "sheet_order" in workbook:
            sheet_order = workbook["sheet_order"]
            if (
                not isinstance(sheet_order, list)
                or not sheet_order
                or not all(isinstance(name, str) and name.strip() for name in sheet_order)
                or len(set(sheet_order)) != len(sheet_order)
            ):
                violations.append("workbook.sheet_order must be unique non-empty strings")
        if "sheet_count" in workbook and not (_is_int(workbook["sheet_count"]) and workbook["sheet_count"] >= 1):
            violations.append("workbook.sheet_count must be a positive integer")

    sheets = manifest.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        violations.append("sheets must be a non-empty list")
        return violations
    if isinstance(workbook, Mapping) and isinstance(workbook.get("sheet_count"), int):
        if len(sheets) != workbook["sheet_count"]:
            violations.append(
                "sheets length must equal workbook.sheet_count "
                f"({len(sheets)} != {workbook['sheet_count']})"
            )
    names_seen: List[str] = []
    for index, sheet in enumerate(sheets):
        label = f"sheets[{index}]"
        if not isinstance(sheet, Mapping):
            violations.append(f"{label} must be a mapping")
            continue
        for key in REQUIRED_SHEET_KEYS:
            if key not in sheet:
                violations.append(f"{label} missing key: {key}")
        if not isinstance(sheet.get("sheet_name"), str) or not sheet["sheet_name"].strip():
            violations.append(f"{label}.sheet_name must be a non-empty string")
        else:
            names_seen.append(sheet["sheet_name"])
        if not (_is_int(sheet.get("sheet_index")) and sheet["sheet_index"] >= 1):
            violations.append(f"{label}.sheet_index must be a positive integer")
        if sheet.get("visibility") not in VISIBILITY_STATES:
            violations.append(
                f"{label}.visibility must be one of {VISIBILITY_STATES}; "
                f"got {sheet.get('visibility')!r}"
            )
        used_range = sheet.get("used_range", "")
        if used_range is not None and not (isinstance(used_range, str) and used_range.strip()):
            violations.append(f"{label}.used_range must be a non-empty string or null")
        for count_key in ("physical_row_count", "physical_column_count"):
            if not (_is_int(sheet.get(count_key)) and sheet[count_key] >= 0):
                violations.append(f"{label}.{count_key} must be a non-negative integer")
        for bool_key in ("is_empty", "is_header_only"):
            if type(sheet.get(bool_key)) is not bool:
                violations.append(f"{label}.{bool_key} must be a boolean")
        for list_key, element_kind in (
            ("header_row_numbers", "positive_int"),
            ("hidden_row_numbers", "positive_int"),
            ("merged_cell_ranges", "non_empty_str"),
            ("hidden_column_letters", "non_empty_str"),
        ):
            entries = sheet.get(list_key)
            if not isinstance(entries, list):
                violations.append(f"{label}.{list_key} must be a list")
            elif element_kind == "positive_int" and not all(
                _is_int(item) and item >= 1 for item in entries
            ):
                violations.append(f"{label}.{list_key} must contain positive integers")
            elif element_kind == "non_empty_str" and not all(
                isinstance(item, str) and item.strip() for item in entries
            ):
                violations.append(f"{label}.{list_key} must contain non-empty strings")
        violations.extend(_check_mapping_list(
            sheet.get("named_tables"), f"{label}.named_tables",
            {"name": "non_empty_str", "ref": "non_empty_str"},
        ))
        autofilter_ref = sheet.get("autofilter_ref", "")
        if autofilter_ref is not None and not (
            isinstance(autofilter_ref, str) and autofilter_ref.strip()
        ):
            violations.append(f"{label}.autofilter_ref must be a non-empty string or null")
        violations.extend(_check_mapping_list(
            sheet.get("formula_cells"), f"{label}.formula_cells",
            {"coordinate": "non_empty_str", "formula_text": "non_empty_str",
             "cached_value_present": "bool", "cached_value": "nullable_str"},
        ))
        for index_, entry in enumerate(sheet.get("formula_cells") or []):
            if isinstance(entry, Mapping) and type(entry.get("cached_value_present")) is not bool:
                violations.append(
                    f"{label}.formula_cells[{index_}].cached_value_present must be a boolean"
                )
        if not isinstance(sheet.get("number_format_columns"), Mapping):
            violations.append(
                f"{label}.number_format_columns must be a mapping with 'columns' and 'mixed'"
            )
        else:
            format_view = sheet["number_format_columns"]
            columns = format_view.get("columns")
            if not isinstance(columns, Mapping):
                violations.append(f"{label}.number_format_columns['columns'] must be a mapping")
            else:
                for column_letters, format_code in columns.items():
                    if not (isinstance(column_letters, str) and column_letters.strip()):
                        violations.append(
                            f"{label}.number_format_columns['columns'] keys must be column letters"
                        )
                    if not (isinstance(format_code, str) and format_code.strip()):
                        violations.append(
                            f"{label}.number_format_columns['columns'][{column_letters!r}] "
                            "must be a non-empty string"
                        )
            mixed_columns = format_view.get("mixed")
            if not isinstance(mixed_columns, list) or not all(
                isinstance(item, str) and item.strip() for item in mixed_columns
            ):
                violations.append(
                    f"{label}.number_format_columns['mixed'] must be a list of column letters"
                )
        leading_rows = sheet.get("leading_zero_text_cells")
        if not isinstance(leading_rows, list):
            violations.append(f"{label}.leading_zero_text_cells must be a list")
        else:
            for position, entry in enumerate(leading_rows):
                item_label = f"{label}.leading_zero_text_cells[{position}]"
                if not isinstance(entry, Mapping):
                    violations.append(f"{item_label} must be a mapping")
                    continue
                if not isinstance(entry.get("coordinate"), str) or not entry["coordinate"].strip():
                    violations.append(f"{item_label}.coordinate must be a non-empty string")
                has_raw = isinstance(entry.get("value"), str) and bool(entry["value"])
                has_hash = (
                    isinstance(entry.get("value_sha256"), str)
                    and len(entry["value_sha256"]) == 64
                    and isinstance(entry.get("length"), int)
                    and entry["length"] > 1
                )
                if not (has_raw or has_hash):
                    violations.append(
                        f"{item_label} must carry raw test value or hashed product evidence"
                    )
        violations.extend(_check_mapping_list(
            sheet.get("duplicate_source_headers"), f"{label}.duplicate_source_headers",
            {"header_text": "non_empty_str", "column_numbers": "int_list"},
        ))
    if len(names_seen) != len(set(names_seen)):
        violations.append("sheets must carry unique sheet_name values")
    return violations


def assert_manifest_complete(manifest: Any) -> None:
    violations = evaluate_manifest_completeness(manifest)
    if violations:
        raise ManifestIncompleteError(
            "manifest is incomplete; omitted evidence cannot auto-pass: "
            + "; ".join(violations)
        )


def reconcile_manifest_against_observation(
    manifest: Any,
    observed: Mapping[str, Any],
) -> List[str]:
    """Prove the manifest explains every oracle-observed physical fact.

    Any missing sheet, wrong visibility, dropped merge, unreported hidden
    row/column/table/autofilter/formula/format/leading-zero cell or duplicate
    column is a violation: an under-explained manifest can never reconcile,
    so it cannot auto-pass into the mapping stage.
    """
    violations = list(evaluate_manifest_completeness(manifest))
    if violations:
        return violations
    if manifest["manifest_version"] != MANIFEST_CONTRACT_VERSION:
        violations.append(
            f"manifest_version must be {MANIFEST_CONTRACT_VERSION!r}; "
            f"got {manifest['manifest_version']!r}"
        )
    manifest_order = manifest["workbook"]["sheet_order"]
    if manifest_order != observed["sheet_order"]:
        violations.append(
            f"sheet_order mismatch: manifest {manifest_order} != observed {observed['sheet_order']}"
        )
    manifest_sheets: Dict[str, Mapping[str, Any]] = {}
    for sheet in manifest["sheets"]:
        if sheet["sheet_name"] in manifest_sheets:
            violations.append(f"duplicate manifest entry for sheet {sheet['sheet_name']!r}")
        manifest_sheets[sheet["sheet_name"]] = sheet
    for position, name in enumerate(observed["sheet_order"], start=1):
        if name not in manifest_sheets:
            violations.append(f"manifest is missing observed sheet {name!r}")
            continue
        sheet = manifest_sheets[name]
        observed_sheet = observed["sheets"][name]
        if sheet["sheet_index"] != position:
            violations.append(
                f"{name}: sheet_index mismatch: {sheet['sheet_index']} != workbook position {position}"
            )
        if sheet["visibility"] != observed["sheet_visibility"][name]:
            violations.append(
                f"{name}: visibility mismatch: manifest {sheet['visibility']!r} != "
                f"observed {observed['sheet_visibility'][name]!r}"
            )
        for scalar_key in ("used_range", "physical_row_count", "physical_column_count", "autofilter_ref"):
            if sheet[scalar_key] != observed_sheet[scalar_key]:
                violations.append(
                    f"{name}: {scalar_key} mismatch: "
                    f"{sheet[scalar_key]!r} != {observed_sheet[scalar_key]!r}"
                )
        for sorted_list_key in ("merged_cell_ranges", "hidden_row_numbers", "hidden_column_letters"):
            if sorted(sheet[sorted_list_key]) != observed_sheet[sorted_list_key]:
                violations.append(
                    f"{name}: {sorted_list_key} mismatch: {sheet[sorted_list_key]!r} != "
                    f"{observed_sheet[sorted_list_key]!r}"
                )
        manifest_tables = {
            (table["name"], table["ref"]) for table in sheet["named_tables"]
        }
        observed_tables = {
            (table["name"], table["ref"]) for table in observed_sheet["named_tables"]
        }
        if manifest_tables != observed_tables:
            violations.append(
                f"{name}: named_tables mismatch: {sorted(manifest_tables)} != "
                f"{sorted(observed_tables)}"
            )
        manifest_formulas = {
            (entry["coordinate"], entry["formula_text"], entry["cached_value_present"])
            for entry in sheet["formula_cells"]
        }
        observed_formulas = {
            (entry["coordinate"], entry["formula_text"], entry["cached_value_present"])
            for entry in observed_sheet["formula_cells"]
        }
        if manifest_formulas != observed_formulas:
            violations.append(
                f"{name}: formula_cells mismatch: {sorted(manifest_formulas)} != "
                f"{sorted(observed_formulas)}"
            )
        violations.extend(_reconcile_number_format_columns(
            name, sheet["number_format_columns"], observed_sheet["number_format_cells"],
        ))
        manifest_leading = {
            (
                entry["coordinate"],
                entry.get("value_sha256")
                or hashlib.sha256(entry["value"].encode("utf-8")).hexdigest(),
                entry.get("length") or len(entry["value"]),
            )
            for entry in sheet["leading_zero_text_cells"]
        }
        observed_leading = {
            (
                entry["coordinate"],
                hashlib.sha256(entry["value"].encode("utf-8")).hexdigest(),
                len(entry["value"]),
            )
            for entry in observed_sheet["leading_zero_text_cells"]
        }
        if manifest_leading != observed_leading:
            violations.append(
                f"{name}: leading_zero_text_cells mismatch: {sorted(manifest_leading)} != "
                f"{sorted(observed_leading)}"
            )
        manifest_duplicates = {
            (entry["header_text"], tuple(entry["column_numbers"]))
            for entry in sheet["duplicate_source_headers"]
        }
        observed_duplicates = {
            (entry["header_text"], tuple(entry["column_numbers"]))
            for entry in observed_sheet["duplicate_source_headers"]
        }
        if manifest_duplicates != observed_duplicates:
            violations.append(
                f"{name}: duplicate_source_headers mismatch: {sorted(manifest_duplicates)} != "
                f"{sorted(observed_duplicates)}"
            )
    observed_names = set(observed["sheet_order"])
    for name in manifest_sheets:
        if name not in observed_names:
            violations.append(f"manifest invents sheet {name!r} absent from the workbook")
    return violations




def _reconcile_number_format_columns(
    sheet_name: str,
    manifest_view: Mapping[str, Any],
    observed_per_cell: Mapping[str, str],
) -> List[str]:
    """Bridge the landed per-column format evidence against the oracle's
    per-cell facts.  Uniform columns must match the observed format (or be
    flagged mixed); every oracle-mixed column must be flagged; invented
    columns are violations."""
    uniform, mixed = _column_format_view(observed_per_cell)
    manifest_columns = dict(manifest_view.get("columns") or {})
    manifest_mixed = set(manifest_view.get("mixed") or [])
    violations: List[str] = []
    for letters, format_code in sorted(uniform.items()):
        if letters in manifest_mixed:
            continue
        if manifest_columns.get(letters) != format_code:
            violations.append(
                f"{sheet_name}: number format for column {letters} mismatch: "
                f"{manifest_columns.get(letters)!r} != {format_code!r}"
            )
    for letters in mixed:
        if letters not in manifest_mixed:
            violations.append(
                f"{sheet_name}: mixed-format column {letters} not flagged "
                f"(observed multiple formats in {sorted(set(observed_per_cell[c] for c in observed_per_cell if _split_coordinate(c)[0] == letters))})"
            )
    for letters in sorted(manifest_mixed):
        if letters not in mixed:
            violations.append(
                f"{sheet_name}: column {letters} flagged mixed but the workbook shows uniform formats"
            )
    for letters in sorted(manifest_columns):
        if letters not in uniform and letters not in mixed:
            violations.append(
                f"{sheet_name}: number format evidence invented for unformatted column {letters}"
            )
    return violations


def build_manifest_via_contract(filename: str, content: bytes) -> Dict[str, Any]:
    """Single adapter seam from the landed work item 1 surface to the matrix
    contract shape.

    The landed surface (2026-09-03 worktree): ``parse_listing_file`` attaches
    a ``WorkbookPhysicalManifest`` plus per-sheet evidence fields to every
    emitted ``ListingSheetPayload``.  This adapter normalizes those objects
    into the matrix contract dict, deriving duplicate source columns from the
    preserved ``source_headers``/deduped ``headers`` pair.  Evidence the
    landed surface does not provide (leading-zero text cells) is emitted
    empty so the reconciliation reports the gap instead of hiding it.  When
    worker_01 moves the surface, adapt this one function and nothing else in
    the matrix.
    """
    from services.api.app.listing_file_parser import parse_listing_file

    payloads = parse_listing_file(filename, content)
    manifest = next(
        (payload.workbook_manifest for payload in payloads if payload.workbook_manifest is not None),
        None,
    )
    if manifest is None:
        raise ManifestSurfaceUnavailable(
            "parse_listing_file attached no workbook_manifest to any payload; "
            "the work item 1 physical-evidence surface is not landed"
        )
    payloads_by_index = {
        payload.sheet_index: payload
        for payload in payloads
        if payload.sheet_index is not None
    }
    sheets: List[Dict[str, Any]] = []
    for fact in manifest.sheets:
        payload = payloads_by_index.get(fact.sheet_index)
        formula_samples = list((payload.formula_evidence or {}).get("samples", [])) if payload else []
        format_view = dict((payload.number_formats or {}).get("columns", {})) if payload else {}
        mixed_formats = sorted((payload.number_formats or {}).get("mixed_format_columns", [])) if payload else []
        source_headers = list(payload.source_headers or []) if payload else []
        header_groups: Dict[str, List[int]] = {}
        for column_number, text in enumerate(source_headers, start=1):
            if text:
                header_groups.setdefault(text, []).append(column_number)
        sheets.append({
            "sheet_name": fact.sheet_name,
            "sheet_index": fact.sheet_index,
            "visibility": fact.visibility,
            "used_range": fact.used_range,
            "physical_row_count": fact.used_row_count or 0,
            "physical_column_count": fact.used_column_count or 0,
            "is_empty": fact.content_kind == "empty" or not fact.used_row_count,
            "is_header_only": fact.content_kind == "header_only",
            "header_row_numbers": list(payload.header_row_numbers or []) if payload else [],
            "merged_cell_ranges": list(payload.merged_regions or []) if payload else [],
            "hidden_row_numbers": list(payload.hidden_rows or []) if payload else [],
            "hidden_column_letters": list(payload.hidden_columns or []) if payload else [],
            "named_tables": [
                {"name": table.get("name"), "ref": table.get("ref")}
                for table in (payload.named_tables or [])
            ] if payload else [],
            "autofilter_ref": (payload.autofilter or {}).get("ref") if payload else None,
            "formula_cells": [
                {
                    "coordinate": sample["cell"],
                    "formula_text": sample["formula"],
                    "cached_value_present": bool(sample.get("cached_present")),
                    "cached_value": None,
                }
                for sample in formula_samples
            ],
            "number_format_columns": {"columns": format_view, "mixed": mixed_formats},
            "leading_zero_text_cells": [
                {
                    "coordinate": entry["cell"],
                    "value_sha256": entry["value_sha256"],
                    "length": entry["length"],
                }
                for entry in (payload.leading_zero_text_cells or [])
            ] if payload else [],
            "duplicate_source_headers": [
                {"header_text": text, "column_numbers": sorted(columns_)}
                for text, columns_ in sorted(header_groups.items())
                if len(columns_) > 1
            ],
        })
    return {
        "manifest_version": manifest.evidence_version,
        "source_file": filename,
        "workbook": {
            "sheet_count": manifest.sheet_count,
            "sheet_order": [fact.sheet_name for fact in manifest.sheets],
        },
        "sheets": sheets,
    }




def reference_manifest_from_ground_truth(case: WorkbookCase) -> Dict[str, Any]:
    """Project a case's declared ground truth into the ``MANIFEST_CONTRACT``
    shape.

    This is NOT the work item 1 implementation: it is the contract-shaped
    reference used to verify the completeness gate and the OOXML reconciler
    today, and to show implementers exactly what a complete manifest looks
    like for every matrix case.
    """
    ground_truth = case.ground_truth
    sheets: List[Dict[str, Any]] = []
    for sheet_index, name in enumerate(ground_truth["sheet_order"], start=1):
        facts = ground_truth["sheets"][name]
        sheets.append({
            "sheet_name": name,
            "sheet_index": sheet_index,
            "visibility": ground_truth["sheet_visibility"][name],
            "used_range": facts["used_range"],
            "physical_row_count": facts["physical_row_count"],
            "physical_column_count": facts["physical_column_count"],
            "is_empty": facts["physical_row_count"] == 0,
            "is_header_only": bool(ground_truth.get("is_header_only", {}).get(name, False)),
            "header_row_numbers": list(ground_truth.get("header_row_numbers", {}).get(name, [])),
            "merged_cell_ranges": list(facts["merged_cell_ranges"]),
            "hidden_row_numbers": list(facts["hidden_row_numbers"]),
            "hidden_column_letters": list(facts["hidden_column_letters"]),
            "named_tables": [dict(table) for table in facts["named_tables"]],
            "autofilter_ref": facts["autofilter_ref"],
            "formula_cells": [dict(cell) for cell in facts["formula_cells"]],
            "number_format_columns": (lambda view: {"columns": view[0], "mixed": view[1]})(
                _column_format_view(facts["number_format_cells"])
            ),
            "leading_zero_text_cells": [dict(cell) for cell in facts["leading_zero_text_cells"]],
            "duplicate_source_headers": [
                {"header_text": entry["header_text"], "column_numbers": list(entry["column_numbers"])}
                for entry in facts["duplicate_source_headers"]
            ],
        })
    return {
        "manifest_version": MANIFEST_CONTRACT_VERSION,
        "source_file": case.filename,
        "workbook": {
            "sheet_count": len(sheets),
            "sheet_order": list(ground_truth["sheet_order"]),
        },
        "sheets": sheets,
    }


def minimal_complete_manifest() -> Dict[str, Any]:
    """A hand-built manifest satisfying every required key: the fixed point
    the omission gate tests mutate."""
    sheet: Dict[str, Any] = {
        "sheet_name": "S1",
        "sheet_index": 1,
        "visibility": "visible",
        "used_range": "A1:B2",
        "physical_row_count": 2,
        "physical_column_count": 2,
        "is_empty": False,
        "is_header_only": False,
        "header_row_numbers": [1],
        "merged_cell_ranges": [],
        "hidden_row_numbers": [],
        "hidden_column_letters": [],
        "named_tables": [],
        "autofilter_ref": None,
        "formula_cells": [],
        "number_format_columns": {"columns": {}, "mixed": []},
        "leading_zero_text_cells": [],
        "duplicate_source_headers": [],
    }
    return {
        "manifest_version": MANIFEST_CONTRACT_VERSION,
        "source_file": "minimal.xlsx",
        "workbook": {"sheet_count": 1, "sheet_order": ["S1"]},
        "sheets": [sheet],
    }
