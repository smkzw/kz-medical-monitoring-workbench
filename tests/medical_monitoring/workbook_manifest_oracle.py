"""Independent OOXML oracle for the C3 workbook physical-integrity matrix.

Derives every matrix-relevant physical fact straight from the raw package
(workbook.xml, worksheet parts, rels, table parts, styles) using only the
standard library, so the oracle cannot share a defect with the openpyxl
builder path or with the parser under test.
"""

from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Mapping, Optional, Tuple

from openpyxl.utils import column_index_from_string, get_column_letter


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
DOC_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
BUILTIN_NUMBER_FORMATS: Dict[int, str] = {
    0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00",
    9: "0%", 10: "0.00%", 11: "0.00E+00", 12: "# ?/?", 13: "# ??/??",
    14: "mm-dd-yy", 15: "d-mmm-yy", 16: "d-mmm", 17: "mmm-yy",
    18: "h:mm AM/PM", 19: "h:mm:ss AM/PM", 20: "h:mm", 21: "h:mm:ss",
    22: "m/d/yy h:mm", 37: "#,##0 ;(#,##0)", 38: "#,##0 ;[Red](#,##0)",
    39: "#,##0.00;(#,##0.00)", 40: "#,##0.00;[Red](#,##0.00)",
    45: "mm:ss", 46: "[h]:mm:ss", 47: "mmss.0", 48: "##0.0E+0", 49: "@",
}
_COORDINATE_PATTERN = re.compile(r"^([A-Z]+)(\d+)$")


def _resolve_part(target: str, base_dir: str) -> str:
    clean = target.lstrip("/")
    if clean.startswith("xl/"):
        return clean
    segments: List[str] = []
    for segment in f"{base_dir}/{clean}".split("/"):
        if segment == "..":
            segments.pop()
        elif segment not in ("", "."):
            segments.append(segment)
    return "/".join(segments)


def _load_relationships(parts: Mapping[str, bytes], rels_path: Optional[str]) -> Dict[str, str]:
    if rels_path is None or rels_path not in parts:
        return {}
    relationships: Dict[str, str] = {}
    for node in ET.fromstring(parts[rels_path]).findall(f"{RELS_NS}Relationship"):
        relationships[node.get("Id")] = node.get("Target")
    return relationships


def _load_format_resolver(styles_bytes: Optional[bytes]):
    custom = dict(BUILTIN_NUMBER_FORMATS)
    xfs: List[int] = []
    if styles_bytes is not None:
        root = ET.fromstring(styles_bytes)
        for node in root.iter(f"{MAIN_NS}numFmt"):
            custom[int(node.get("numFmtId"))] = node.get("formatCode")
        cell_xfs = root.find(f"{MAIN_NS}cellXfs")
        if cell_xfs is not None:
            xfs = [int(xf.get("numFmtId", "0")) for xf in cell_xfs.findall(f"{MAIN_NS}xf")]

    def resolve(style_index: Optional[str]) -> str:
        index = int(style_index) if style_index else 0
        num_fmt_id = xfs[index] if index < len(xfs) else 0
        return custom.get(num_fmt_id, f"unresolved:{num_fmt_id}")

    return resolve


def _observe_sheet(
    parts: Mapping[str, bytes],
    sheet_path: str,
    resolve_format,
) -> Dict[str, Any]:
    root = ET.fromstring(parts[sheet_path])
    cells: Dict[str, Dict[str, Any]] = {}
    hidden_rows: List[int] = []
    for row_node in root.iter(f"{MAIN_NS}row"):
        if row_node.get("hidden") == "1":
            hidden_rows.append(int(row_node.get("r")))
        for cell_node in row_node.findall(f"{MAIN_NS}c"):
            coordinate = cell_node.get("r")
            text_node = cell_node.find(f"{MAIN_NS}v")
            inline_node = cell_node.find(f"{MAIN_NS}is")
            formula_node = cell_node.find(f"{MAIN_NS}f")
            inline_text = (
                "".join(
                    t.text or ""
                    for t in inline_node.iter(f"{MAIN_NS}t")
                )
                if inline_node is not None
                else None
            )
            cells[coordinate] = {
                "type": cell_node.get("t", "n"),
                "text": inline_text,
                "cached": None if text_node is None else (text_node.text or ""),
                "style": cell_node.get("s"),
                "formula": None if formula_node is None else (formula_node.text or ""),
            }

    hidden_columns: List[str] = []
    for col_node in root.iter(f"{MAIN_NS}col"):
        if col_node.get("hidden") == "1":
            for index in range(int(col_node.get("min")), int(col_node.get("max")) + 1):
                hidden_columns.append(get_column_letter(index))

    rows = [_split_coordinate(c)[1] for c in cells]
    columns = [column_index_from_string(_split_coordinate(c)[0]) for c in cells]
    if cells:
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(columns), max(columns)
        used_range = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"
    else:
        min_row = max_row = min_col = max_col = 0
        used_range = None

    merges = sorted(
        node.get("ref") for node in root.iter(f"{MAIN_NS}mergeCell")
    )
    autofilter_node = root.find(f"{MAIN_NS}autoFilter")
    autofilter_ref = autofilter_node.get("ref") if autofilter_node is not None else None

    formula_cells = sorted(
        (
            {
                "coordinate": coordinate,
                "formula_text": "=" + cell["formula"],
                "cached_value_present": bool(cell["cached"]),
                "cached_value": cell["cached"] if cell["cached"] else None,
            }
            for coordinate, cell in cells.items()
            if cell["formula"] is not None
        ),
        key=lambda entry: entry["coordinate"],
    )
    number_format_cells = {
        coordinate: resolve_format(cell["style"])
        for coordinate, cell in sorted(cells.items())
        if resolve_format(cell["style"]) != "General"
    }
    leading_zero_text_cells = [
        {"coordinate": coordinate, "value": cell["text"]}
        for coordinate, cell in sorted(cells.items())
        if cell["type"] in ("inlineStr", "s")
        and cell["text"]
        and cell["text"].startswith("0")
        and len(cell["text"]) > 1
    ]

    first_row_texts: Dict[int, str] = {}
    for coordinate, cell in cells.items():
        letters, row = _split_coordinate(coordinate)
        if row == 1 and cell["text"]:
            first_row_texts[column_index_from_string(letters)] = cell["text"]
    header_groups: Dict[str, List[int]] = {}
    for column_index, text in first_row_texts.items():
        header_groups.setdefault(text, []).append(column_index)
    duplicate_source_headers = [
        {"header_text": text, "column_numbers": sorted(columns_)}
        for text, columns_ in sorted(header_groups.items())
        if len(columns_) > 1
    ]

    rels = _load_relationships(
        parts,
        f"xl/worksheets/_rels/{sheet_path.rsplit('/', 1)[-1]}.rels",
    )
    named_tables = []
    for relationship_id, target in rels.items():
        if not target.split(".")[-1].startswith("xml") or "tables/" not in target:
            continue
        table_root = ET.fromstring(parts[_resolve_part(target, "xl/worksheets")])
        named_tables.append({"name": table_root.get("name"), "ref": table_root.get("ref")})
    named_tables.sort(key=lambda entry: entry["name"])

    return {
        "used_range": used_range,
        "physical_row_count": (max_row - min_row + 1) if cells else 0,
        "physical_column_count": (max_col - min_col + 1) if cells else 0,
        "merged_cell_ranges": merges,
        "hidden_row_numbers": sorted(hidden_rows),
        "hidden_column_letters": sorted(set(hidden_columns)),
        "named_tables": named_tables,
        "autofilter_ref": autofilter_ref,
        "formula_cells": formula_cells,
        "number_format_cells": number_format_cells,
        "leading_zero_text_cells": leading_zero_text_cells,
        "duplicate_source_headers": duplicate_source_headers,
    }


def _split_coordinate(coordinate: str) -> Tuple[str, int]:
    match = _COORDINATE_PATTERN.match(coordinate)
    if not match:
        raise ValueError(f"malformed cell coordinate {coordinate!r}")
    return match.group(1), int(match.group(2))


def observe_physical_facts(content: bytes) -> Dict[str, Any]:
    """Derive every matrix-relevant physical fact straight from the OOXML
    package (workbook.xml, worksheet parts, rels, tables, styles) without
    openpyxl, so the oracle cannot share a defect with the builder path."""
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    workbook_root = ET.fromstring(parts["xl/workbook.xml"])
    relationships = _load_relationships(parts, "xl/_rels/workbook.xml.rels")
    resolve_format = _load_format_resolver(parts.get("xl/styles.xml"))
    sheet_order: List[str] = []
    sheet_visibility: Dict[str, str] = {}
    sheet_paths: Dict[str, str] = {}
    for node in workbook_root.find(f"{MAIN_NS}sheets"):
        name = node.get("name")
        sheet_order.append(name)
        sheet_visibility[name] = node.get("state") or "visible"
        sheet_paths[name] = _resolve_part(
            relationships[node.get(f"{DOC_REL_NS}id")], "xl"
        )
    return {
        "sheet_order": sheet_order,
        "sheet_visibility": sheet_visibility,
        "sheets": {
            name: _observe_sheet(parts, sheet_paths[name], resolve_format)
            for name in sheet_order
        },
    }




def _column_format_view(per_cell: Mapping[str, str]) -> Tuple[Dict[str, str], List[str]]:
    """Collapse per-cell ``{coordinate: format}`` into a per-column view:
    ``(uniform_columns, mixed_columns)``.  A column is mixed when its formatted
    cells carry more than one distinct format string."""
    by_column: Dict[str, List[str]] = {}
    for coordinate, format_code in per_cell.items():
        letters = _split_coordinate(coordinate)[0]
        by_column.setdefault(letters, []).append(format_code)
    mixed = sorted(letters for letters, formats in by_column.items() if len(set(formats)) > 1)
    uniform = {
        letters: formats[0]
        for letters, formats in by_column.items()
        if len(set(formats)) == 1
    }
    return uniform, mixed
