"""Data Listing file parser with workbook physical-integrity evidence.

Parses CSV / XLS / XLSX listing files into :class:`ListingSheetPayload`
records.  Besides the interpreted rows, the parser records a reconcilable
physical manifest of the workbook (``WorkbookPhysicalManifest`` attached to
every emitted payload) so downstream admission can verify that dual-model
runs only see fully interpreted inputs:

* workbook sheet order, visibility (``visible`` / ``hidden`` / ``veryHidden``)
  and used range for *every* sheet, including sheets that produce no payload
  (empty sheets, or sheets without usable headers) — recorded with an
  explicit omission reason;
* hidden rows / columns, merged regions, named tables (ListObjects) and
  autofilter ranges per sheet;
* the located header rows (multi-row headers) and the first data row as
  1-based worksheet row numbers, following the same positional convention
  as ``row_numbers``;
* formula evidence: formula-cell count, bounded formula-text samples, and
  the count of formula cells whose cached value is missing (those silently
  become empty cells under ``data_only`` parsing);
* distinct non-``General`` number formats per column.

Evidence semantics: a field set to ``None`` means "not captured" (format
limitation or evidence-pass failure, recorded in ``evidence_limitations``);
an empty list means "captured, none present".  All evidence lists are
bounded; counts always reflect the true totals and ``*_truncated`` flags
mark bounded lists.

XLSX evidence comes from a full-fidelity ``openpyxl`` load (``data_only=
False``) of the same autofilter-recovered bytes the values pass reads, plus
a conditional streaming pass that resolves formula cached-state when a
sheet contains formulas.  XLS evidence is limited by the ``xlrd`` binary
API (no formula text, number formats, named tables or autofilter); CSV has
no workbook layout concepts.  The interpreted rows, headers and row numbers
produced by this parser are unchanged by evidence capture.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import openpyxl
import xlrd
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.worksheet.filters import AutoFilter

from packages.contracts.workbench_contracts import (
    ListingSheetPayload,
    WorkbookPhysicalManifest,
    WorkbookSheetFact,
)


SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx", ".xlsm"}
LISTING_PARSER_VERSION = "listing_file_parser_v3_ooxml_metadata_recovery"
WORKBOOK_PHYSICAL_EVIDENCE_VERSION = "workbook_physical_evidence_v1"
INVALID_AUTOFILTER_WARNING = (
    "worksheet_autofilter_ignored: invalid range metadata ignored; cell values preserved"
)
AUTOFILTER_ELEMENT_PATTERN = re.compile(
    rb"<autoFilter\b[^>]*/>|<autoFilter\b[^>]*>.*?</autoFilter>",
    re.DOTALL,
)
AUTOFILTER_REF_PATTERN = re.compile(rb"""\bref=(["'])(.*?)\1""")

#: Bounded evidence list sizes; true totals are always recorded separately.
MAX_EVIDENCE_HIDDEN_ROWS = 200
MAX_EVIDENCE_HIDDEN_COLUMNS = 100
MAX_EVIDENCE_MERGED_REGIONS = 100
MAX_EVIDENCE_NAMED_TABLES = 20
MAX_EVIDENCE_TABLE_COLUMNS = 50
MAX_EVIDENCE_FORMULA_SAMPLES = 10
MAX_EVIDENCE_FORMULA_TEXT_CHARS = 200
MAX_EVIDENCE_FORMULA_COORDS = 100_000
MAX_EVIDENCE_FORMAT_COLUMNS = 100
MAX_EVIDENCE_DISTINCT_FORMATS = 3
MAX_EVIDENCE_LEADING_ZERO_TEXT_CELLS = 1000

XLSX_SHEET_EVIDENCE_DEGRADED = "xlsx_sheet_evidence_degraded"
XLS_LAYOUT_METADATA_UNAVAILABLE = "xls_hidden_and_merged_metadata_unavailable"
XLS_FORMULA_LIMITATION = "xls_formula_text_and_cached_state_not_captured"
XLS_NUMBER_FORMAT_LIMITATION = "xls_number_formats_not_captured"
XLS_LAYOUT_LIMITATION = "xls_named_tables_and_autofilter_not_captured"
CSV_LAYOUT_LIMITATION = "csv_workbook_layout_metadata_not_applicable"

XLS_VISIBILITY = {0: "visible", 1: "hidden", 2: "veryHidden"}

RANGE_BOUNDS_PATTERN = re.compile(r"^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$")

COMMON_CHINESE_HEADER_ALIASES = {
    "项目编号": "STUDYID",
    "表单编号": "FORMOID",
    "受试者编号": "SUBJID",
    "受试者筛选号": "SUBJID",
    "受试者": "SUBJID",
    "姓名缩写": "SUBJINI",
    "受试者状态": "SUBJSTA",
    "试验中心编号": "SITEID",
    "中心编号": "SITEID",
    "试验中心名称": "SITENM",
    "研究中心": "SITENM",
    "中心名称": "SITENM",
    "数据节": "VISIT",
    "访视名称": "VISIT",
    "访视号": "VISTREP",
    "Instance顺序号": "VISTREP",
    "数据块": "FORMNM",
    "数据页": "FORMNM",
    "页面名称": "FORMNM",
    "页面号": "FORMREP",
    "最后修改时间": "PAGELMDT",
    "页面最近修改时间": "PAGELMDT",
    "行号": "RECREP",
    "记录号": "RECREP",
    "随机号": "RANDNO",
    "随机时间": "RANDDTC",
    "研究分组": "ARM",
    "性别": "SEX",
}

HEADER_CODE_PATTERN = re.compile(r"[（(]([A-Za-z][A-Za-z0-9_]{1,31})[）)]")
ASCII_CODE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,31}$")


def _clean_header(value: Any, index: int) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return f"UNNAMED_{index + 1}"
    if text in COMMON_CHINESE_HEADER_ALIASES:
        return COMMON_CHINESE_HEADER_ALIASES[text]
    code_match = HEADER_CODE_PATTERN.search(text)
    if code_match:
        return code_match.group(1).upper()
    return text


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _dedupe_headers(headers: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    deduped: List[str] = []
    for header in headers:
        seen[header] = seen.get(header, 0) + 1
        deduped.append(header if seen[header] == 1 else f"{header}__{seen[header]}")
    return deduped


def _is_ascii_code(value: Any) -> bool:
    text = "" if value is None else str(value).strip()
    return bool(ASCII_CODE_PATTERN.match(text)) and text == text.upper()


def _non_empty_count(values: Any) -> int:
    return sum(1 for value in values if _cell_text(value))


def _looks_like_variable_header(values: Any) -> bool:
    non_empty = _non_empty_count(values)
    if non_empty < 3:
        return False
    ascii_codes = sum(1 for value in values if _is_ascii_code(value))
    return ascii_codes >= 3 and ascii_codes / max(non_empty, 1) >= 0.6


def _looks_like_header(values: Any) -> bool:
    headers = [_cell_text(value) for value in values]
    if _non_empty_count(headers) < 2:
        return False
    markers = {
        "受试者",
        "受试者编号",
        "受试者筛选号",
        "中心编号",
        "研究中心",
        "试验中心编号",
        "项目编号",
        "表单编号",
        "访视名称",
        "数据节",
        "SUBJID",
        "SITEID",
        "VISIT",
    }
    return any(header in markers or HEADER_CODE_PATTERN.search(header) for header in headers)


def _header_and_data_rows(
    raw_rows: List[List[Any]],
) -> tuple[List[str], List[str], List[List[Any]], int, List[int]]:
    """Locate the header block and return parsed header rows plus data.

    Returns ``(headers, source_headers, data_rows, data_start, header_indexes)``
    where ``header_indexes`` lists the raw-row indexes consumed as header rows
    (one row, or two rows when an EDC variable-name row follows the label row)
    and ``data_start`` is the raw-row index of the first data row.
    """
    header_index = None
    scan_limit = min(25, len(raw_rows))
    for index in range(scan_limit):
        if _looks_like_header(raw_rows[index]):
            header_index = index
            break
    if header_index is None:
        header_index = 0

    source_header_values = raw_rows[header_index]
    header_values = source_header_values
    data_start = header_index + 1
    header_indexes = [header_index]
    if data_start < len(raw_rows) and _looks_like_variable_header(raw_rows[data_start]):
        header_values = [
            raw_rows[data_start][index] if index < len(raw_rows[data_start]) and _cell_text(raw_rows[data_start][index]) else value
            for index, value in enumerate(header_values)
        ]
        header_indexes.append(data_start)
        data_start += 1

    headers = _dedupe_headers([_clean_header(value, index) for index, value in enumerate(header_values)])
    source_headers = [
        _cell_text(
            source_header_values[index]
            if index < len(source_header_values)
            else None
        )
        or header
        for index, header in enumerate(headers)
    ]
    return headers, source_headers, raw_rows[data_start:], data_start, header_indexes


def _build_rows(
    headers: List[str],
    data_rows: List[List[Any]],
    data_start: int,
) -> tuple[List[Dict[str, str]], List[int]]:
    rows: List[Dict[str, str]] = []
    row_numbers: List[int] = []
    for offset, values in enumerate(data_rows):
        row = {
            headers[index]: _cell_text(values[index] if index < len(values) else "")
            for index in range(len(headers))
        }
        if any(value for value in row.values()):
            rows.append(row)
            row_numbers.append(data_start + offset + 1)
    return rows, row_numbers


def _has_usable_headers(headers: List[str]) -> bool:
    return sum(1 for header in headers if not header.startswith("UNNAMED_")) >= 2


def _sheet_content_kind(raw_rows: List[List[Any]], data_start: int) -> str:
    """Classify a sheet physically: empty, header-only, or carrying data."""
    if not any(_cell_text(value) for row in raw_rows for value in row):
        return "empty"
    for row in raw_rows[data_start:]:
        if any(_cell_text(value) for value in row):
            return "data"
    return "header_only"


def _parse_range_bounds(range_text: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not range_text:
        return None, None
    match = RANGE_BOUNDS_PATTERN.match(range_text.strip().upper())
    if not match:
        return None, None
    last_row = int(match.group(4) or match.group(2))
    last_col = column_index_from_string(match.group(3) or match.group(1))
    return last_row, last_col


def _header_rows_with_merged_groups(
    header_indexes: List[int],
    sheet_evidence: Dict[str, Any],
) -> List[int]:
    """Include contiguous merged group-label rows above the detected header."""

    rows = {index + 1 for index in header_indexes}
    if not rows:
        return []
    first = min(rows)
    merged_rows: Set[int] = set()
    for region in sheet_evidence.get("merged_regions") or []:
        match = RANGE_BOUNDS_PATTERN.match(str(region).upper())
        if not match:
            continue
        start_row = int(match.group(2))
        end_row = int(match.group(4) or start_row)
        merged_rows.update(range(start_row, end_row + 1))
    candidate = first - 1
    while candidate >= 1 and candidate in merged_rows:
        rows.add(candidate)
        candidate -= 1
    return sorted(rows)


def _formula_text(value: Any) -> str:
    text = getattr(value, "text", value)
    text = str(text)
    if len(text) > MAX_EVIDENCE_FORMULA_TEXT_CHARS:
        return text[:MAX_EVIDENCE_FORMULA_TEXT_CHARS]
    return text


def _dimension_span(dimension: Any, default_index: int) -> Tuple[int, int]:
    lo = getattr(dimension, "min", None)
    hi = getattr(dimension, "max", None)
    if isinstance(lo, int) and isinstance(hi, int) and lo >= 1 and hi >= lo:
        return lo, hi
    return default_index, default_index


def _hidden_index_evidence(
    dimensions: Any,
    key_to_index: Any,
    cap: int,
) -> Tuple[List[int], int, bool]:
    """Collect hidden row/column indexes from openpyxl dimension metadata.

    Returns bounded sorted indexes, the true hidden count, and whether the
    bounded list is truncated.
    """
    spans: List[Tuple[int, int]] = []
    total = 0
    for key, dimension in dict(dimensions).items():
        if not getattr(dimension, "hidden", False):
            continue
        try:
            default_index = int(key_to_index(key))
        except (TypeError, ValueError):
            continue
        lo, hi = _dimension_span(dimension, default_index)
        if hi < lo:
            continue
        spans.append((lo, hi))
        total += hi - lo + 1
    if total <= cap:
        indexes: List[int] = []
        for lo, hi in sorted(spans):
            indexes.extend(range(lo, hi + 1))
        return indexes, total, False
    indexes = []
    for lo, hi in sorted(spans):
        for value in range(lo, hi + 1):
            if len(indexes) >= cap:
                return indexes, total, True
            indexes.append(value)
    return indexes, total, True


def parse_listing_file(filename: str, content: bytes) -> List[ListingSheetPayload]:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported listing file type: {suffix or 'unknown'}")
    if suffix == ".csv":
        return [_parse_csv_listing(filename, content)]
    if suffix == ".xls":
        return _parse_xls_listing(content)
    return _parse_xlsx_listing(content)


def _parse_csv_listing(filename: str, content: bytes) -> ListingSheetPayload:
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    raw_rows = [list(row) for row in reader]
    if not raw_rows:
        raise ValueError("csv listing has no header row")
    headers, source_headers, data_rows, data_start, header_indexes = _header_and_data_rows(raw_rows)
    rows, row_numbers = _build_rows(headers, data_rows, data_start)
    sheet_name = Path(filename or "CSV").stem or "CSV"
    used_columns = max((len(row) for row in raw_rows), default=0)
    used_rows = len(raw_rows)
    used_range = f"A1:{get_column_letter(used_columns)}{used_rows}" if used_columns else None
    content_kind = _sheet_content_kind(raw_rows, data_start)
    manifest = WorkbookPhysicalManifest(
        evidence_version=WORKBOOK_PHYSICAL_EVIDENCE_VERSION,
        parser_version=LISTING_PARSER_VERSION,
        source_format="csv",
        content_sha256=hashlib.sha256(content).hexdigest(),
        sheet_count=1,
        emitted_sheet_count=1,
        sheets=[
            WorkbookSheetFact(
                sheet_index=1,
                sheet_name=sheet_name,
                visibility="visible",
                used_range=used_range,
                used_row_count=used_rows,
                used_column_count=used_columns,
                content_kind=content_kind,
                emitted=True,
            )
        ],
        evidence_limitations=[CSV_LAYOUT_LIMITATION],
    )
    return ListingSheetPayload(
        sheet_name=sheet_name,
        headers=headers,
        source_headers=source_headers,
        rows=rows,
        row_numbers=row_numbers,
        parser_version=LISTING_PARSER_VERSION,
        sheet_index=1,
        sheet_visibility="visible",
        sheet_content_kind=content_kind,
        used_range=used_range,
        used_row_count=used_rows,
        used_column_count=used_columns,
        header_row_numbers=[index + 1 for index in header_indexes],
        data_start_row_number=data_start + 1,
        workbook_manifest=manifest,
    )


def _parse_xlsx_listing(content: bytes) -> List[ListingSheetPayload]:
    readable_content, invalid_autofilter_paths = _ignore_invalid_autofilter_metadata(content)
    physical_evidence = _collect_xlsx_physical_evidence(readable_content)
    physical_by_name: Dict[str, Dict[str, Any]] = {}
    if physical_evidence is not None:
        physical_by_name = {
            str(entry.get("sheet_name")): entry
            for entry in physical_evidence.get("sheets", [])
        }
    workbook = openpyxl.load_workbook(
        io.BytesIO(readable_content),
        read_only=True,
        data_only=True,
    )
    try:
        sheets: List[ListingSheetPayload] = []
        parse_facts: Dict[str, Dict[str, Any]] = {}
        for position, worksheet in enumerate(workbook.worksheets, start=1):
            parser_warnings: List[str] = []
            if worksheet._worksheet_path in invalid_autofilter_paths:
                parser_warnings.append(INVALID_AUTOFILTER_WARNING)
            if (
                worksheet.calculate_dimension() in {"A1", "A1:A1"}
                and hasattr(worksheet, "reset_dimensions")
            ):
                worksheet.reset_dimensions()
                parser_warnings.append(
                    "worksheet_dimension_reset: declared A1:A1; parsed from worksheet XML bounds"
                )
            sheet_evidence = physical_by_name.get(worksheet.title) or {}
            used_range = sheet_evidence.get("used_range")
            if used_range is None:
                try:
                    used_range = worksheet.calculate_dimension()
                except Exception:
                    used_range = None
            used_rows, used_columns = _parse_range_bounds(used_range)
            visibility = str(getattr(worksheet, "sheet_state", "unknown") or "unknown")
            raw_rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
            if not raw_rows:
                # OOXML commonly declares A1:A1 even when the worksheet has no
                # cells. The manifest records physical content, not that
                # placeholder dimension.
                parse_facts[worksheet.title] = {
                    "sheet_index": position,
                    "visibility": visibility,
                    "used_range": None,
                    "used_row_count": 0,
                    "used_column_count": 0,
                    "content_kind": "empty",
                    "emitted": False,
                    "omission_reason": "empty_sheet",
                    "header_row_numbers": [],
                    "data_start_row_number": None,
                }
                continue
            headers, source_headers, data_rows, data_start, header_indexes = _header_and_data_rows(raw_rows)
            rows, row_numbers = _build_rows(headers, data_rows, data_start)
            usable = bool(rows) or _has_usable_headers(headers)
            parse_facts[worksheet.title] = {
                "sheet_index": position,
                "visibility": visibility,
                "used_range": used_range,
                "used_row_count": used_rows,
                "used_column_count": used_columns,
                "content_kind": _sheet_content_kind(raw_rows, data_start),
                "emitted": usable,
                "omission_reason": None if usable else "no_usable_headers",
                "header_row_numbers": _header_rows_with_merged_groups(
                    header_indexes,
                    sheet_evidence,
                ),
                "data_start_row_number": data_start + 1,
            }
            if usable:
                sheets.append(
                    ListingSheetPayload(
                        sheet_name=worksheet.title,
                        headers=headers,
                        source_headers=source_headers,
                        rows=rows,
                        row_numbers=row_numbers,
                        parser_warnings=parser_warnings,
                    )
                )
        if not sheets:
            raise ValueError("xlsx listing has no non-empty sheets")
        manifest, sheet_evidence = _build_workbook_manifest(
            source_format="xlsx",
            content=content,
            parse_facts=parse_facts,
            physical=physical_evidence,
            limitations=[],
        )
        for payload in sheets:
            _attach_sheet_evidence(
                payload,
                parse_facts[payload.sheet_name],
                sheet_evidence.get(payload.sheet_name),
            )
            payload.workbook_manifest = manifest
        return sheets
    finally:
        workbook.close()


def _build_workbook_manifest(
    source_format: str,
    content: bytes,
    parse_facts: Dict[str, Dict[str, Any]],
    physical: Optional[Dict[str, Any]],
    limitations: List[str],
) -> Tuple[WorkbookPhysicalManifest, Dict[str, Dict[str, Any]]]:
    """Assemble the workbook manifest from parse facts plus rich evidence."""
    sheet_evidence: Dict[str, Dict[str, Any]] = {}
    evidence_limitations = list(limitations)
    if physical is None:
        evidence_limitations.append(f"{source_format}_physical_evidence_capture_failed")
    else:
        evidence_limitations.extend(physical.get("limitations", []))
        sheet_evidence = {
            str(entry.get("sheet_name")): entry
            for entry in physical.get("sheets", [])
        }
    facts: List[WorkbookSheetFact] = []
    emitted_count = 0
    for sheet_name, fact_data in parse_facts.items():
        evidence = sheet_evidence.get(sheet_name) or {}
        formula_evidence = evidence.get("formula_evidence") or {}
        emitted = bool(fact_data.get("emitted"))
        emitted_count += 1 if emitted else 0
        facts.append(
            WorkbookSheetFact(
                sheet_index=int(fact_data["sheet_index"]),
                sheet_name=sheet_name,
                visibility=str(fact_data.get("visibility") or "unknown"),
                used_range=fact_data.get("used_range"),
                used_row_count=fact_data.get("used_row_count"),
                used_column_count=fact_data.get("used_column_count"),
                content_kind=fact_data.get("content_kind"),
                emitted=emitted,
                omission_reason=fact_data.get("omission_reason"),
                hidden_row_count=int(evidence.get("hidden_row_count") or 0),
                hidden_column_count=int(evidence.get("hidden_column_count") or 0),
                merged_region_count=int(evidence.get("merged_region_count") or 0),
                named_table_count=int(evidence.get("named_table_count") or 0),
                formula_cell_count=int(formula_evidence.get("formula_cell_count") or 0),
                uncached_formula_cell_count=formula_evidence.get("uncached_formula_cell_count"),
                uncached_scan_truncated=bool(formula_evidence.get("uncached_scan_truncated")),
            )
        )
    manifest = WorkbookPhysicalManifest(
        evidence_version=WORKBOOK_PHYSICAL_EVIDENCE_VERSION,
        parser_version=LISTING_PARSER_VERSION,
        source_format=source_format,
        content_sha256=hashlib.sha256(content).hexdigest(),
        sheet_count=len(facts),
        emitted_sheet_count=emitted_count,
        sheets=facts,
        evidence_limitations=sorted(set(evidence_limitations)),
    )
    return manifest, sheet_evidence


def _attach_sheet_evidence(
    payload: ListingSheetPayload,
    fact_data: Dict[str, Any],
    evidence: Optional[Dict[str, Any]],
) -> None:
    payload.parser_version = LISTING_PARSER_VERSION
    payload.sheet_index = int(fact_data["sheet_index"])
    payload.sheet_visibility = str(fact_data.get("visibility") or "unknown")
    payload.sheet_content_kind = fact_data.get("content_kind")
    payload.used_range = fact_data.get("used_range")
    payload.used_row_count = fact_data.get("used_row_count")
    payload.used_column_count = fact_data.get("used_column_count")
    payload.header_row_numbers = list(fact_data.get("header_row_numbers") or [])
    payload.data_start_row_number = fact_data.get("data_start_row_number")
    if not evidence:
        return
    payload.hidden_rows = list(evidence.get("hidden_rows") or [])
    payload.hidden_row_count = evidence.get("hidden_row_count") or 0
    payload.hidden_rows_truncated = bool(evidence.get("hidden_rows_truncated"))
    payload.hidden_columns = list(evidence.get("hidden_columns") or [])
    payload.hidden_column_count = evidence.get("hidden_column_count") or 0
    payload.hidden_columns_truncated = bool(evidence.get("hidden_columns_truncated"))
    payload.merged_regions = list(evidence.get("merged_regions") or [])
    payload.merged_region_count = evidence.get("merged_region_count") or 0
    payload.merged_regions_truncated = bool(evidence.get("merged_regions_truncated"))
    payload.named_tables = list(evidence.get("named_tables") or [])
    payload.named_table_count = evidence.get("named_table_count") or 0
    payload.autofilter = evidence.get("autofilter")
    payload.formula_evidence = evidence.get("formula_evidence")
    payload.number_formats = evidence.get("number_formats")
    payload.leading_zero_text_cells = list(
        evidence.get("leading_zero_text_cells") or []
    )


def _collect_xlsx_physical_evidence(readable_content: bytes) -> Optional[Dict[str, Any]]:
    """Best-effort physical evidence pass over the recovered workbook bytes.

    Loads the workbook at full fidelity (``data_only=False``) to capture
    layout metadata, formula text and number formats, then optionally runs a
    streaming read-only pass to resolve formula cached-state.  Returns
    ``None`` when the full-fidelity load fails; the values parse never
    depends on this pass.
    """
    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(readable_content),
            read_only=False,
            data_only=False,
        )
    except Exception:
        return None
    sheets: List[Dict[str, Any]] = []
    limitations: List[str] = []
    try:
        for worksheet in workbook.worksheets:
            try:
                sheets.append(_xlsx_sheet_physical_evidence(worksheet))
            except Exception:
                limitations.append(XLSX_SHEET_EVIDENCE_DEGRADED)
                sheets.append(_degraded_sheet_evidence(worksheet))
    finally:
        workbook.close()
    _resolve_xlsx_cached_formula_state(readable_content, sheets)
    return {"sheets": sheets, "limitations": limitations}


def _degraded_sheet_evidence(worksheet: Any) -> Dict[str, Any]:
    return {
        "sheet_name": str(getattr(worksheet, "title", "")),
        "hidden_rows": [],
        "hidden_row_count": 0,
        "hidden_rows_truncated": False,
        "hidden_columns": [],
        "hidden_column_count": 0,
        "hidden_columns_truncated": False,
        "merged_regions": [],
        "merged_region_count": 0,
        "merged_regions_truncated": False,
        "named_tables": [],
        "named_table_count": 0,
        "autofilter": None,
        "formula_evidence": {
            "formula_cell_count": 0,
            "uncached_formula_cell_count": None,
            "uncached_scan_truncated": True,
            "samples": [],
        },
        "number_formats": {
            "columns": {},
            "mixed_format_columns": [],
            "truncated": False,
        },
        "leading_zero_text_cells": [],
    }


def _xlsx_sheet_physical_evidence(worksheet: Any) -> Dict[str, Any]:
    hidden_row_indexes, hidden_row_total, hidden_rows_truncated = _hidden_index_evidence(
        worksheet.row_dimensions, int, MAX_EVIDENCE_HIDDEN_ROWS
    )
    hidden_column_indexes, hidden_column_total, hidden_columns_truncated = _hidden_index_evidence(
        worksheet.column_dimensions, column_index_from_string, MAX_EVIDENCE_HIDDEN_COLUMNS
    )
    merged_ranges = sorted(
        worksheet.merged_cells.ranges,
        key=lambda rng: (rng.min_row, rng.min_col, str(rng)),
    )
    merged_regions = [str(rng) for rng in merged_ranges[:MAX_EVIDENCE_MERGED_REGIONS]]
    named_tables: List[Dict[str, Any]] = []
    for table in sorted(
        worksheet.tables.values(),
        key=lambda table: str(getattr(table, "name", "")),
    )[:MAX_EVIDENCE_NAMED_TABLES]:
        named_tables.append(
            {
                "name": str(getattr(table, "name", "")),
                "ref": str(getattr(table, "ref", "")),
                "columns": [
                    str(column)
                    for column in (getattr(table, "column_names", None) or [])[:MAX_EVIDENCE_TABLE_COLUMNS]
                ],
            }
        )
    autofilter_ref = getattr(worksheet.auto_filter, "ref", None) if worksheet.auto_filter else None
    autofilter = (
        {
            "ref": str(autofilter_ref),
            "filter_column_count": len(worksheet.auto_filter.filterColumn or []),
        }
        if autofilter_ref
        else None
    )

    try:
        used_range: Optional[str] = worksheet.calculate_dimension() or None
    except Exception:
        used_range = None

    formula_cell_count = 0
    formula_coords: List[Tuple[int, int]] = []
    formula_samples: List[Dict[str, Any]] = []
    coords_truncated = False
    format_buckets: Dict[int, Set[str]] = {}
    mixed_format_columns: Set[int] = set()
    leading_zero_text_cells: List[Dict[str, Any]] = []
    for row in worksheet.iter_rows():
        for cell in row:
            if getattr(cell, "data_type", None) == "f" and cell.value is not None:
                formula_cell_count += 1
                if len(formula_coords) < MAX_EVIDENCE_FORMULA_COORDS:
                    formula_coords.append((cell.row, cell.column))
                else:
                    coords_truncated = True
                if len(formula_samples) < MAX_EVIDENCE_FORMULA_SAMPLES:
                    formula_samples.append(
                        {"cell": cell.coordinate, "formula": _formula_text(cell.value)}
                    )
                continue
            if cell.value is None:
                continue
            if (
                isinstance(cell.value, str)
                and len(cell.value) > 1
                and cell.value.startswith("0")
                and len(leading_zero_text_cells)
                < MAX_EVIDENCE_LEADING_ZERO_TEXT_CELLS
            ):
                leading_zero_text_cells.append({
                    "cell": cell.coordinate,
                    "value_sha256": hashlib.sha256(
                        cell.value.encode("utf-8")
                    ).hexdigest(),
                    "length": len(cell.value),
                })
            number_format = getattr(cell, "number_format", None)
            if not number_format or number_format == "General":
                continue
            bucket = format_buckets.setdefault(cell.column, set())
            if number_format not in bucket:
                if len(bucket) >= MAX_EVIDENCE_DISTINCT_FORMATS:
                    mixed_format_columns.add(cell.column)
                else:
                    bucket.add(number_format)
                if len(bucket) > 1:
                    mixed_format_columns.add(cell.column)

    reported_format_indexes = sorted(format_buckets)[:MAX_EVIDENCE_FORMAT_COLUMNS]
    mixed_reported = sorted(mixed_format_columns)[:MAX_EVIDENCE_FORMAT_COLUMNS]
    format_columns: Dict[str, str] = {}
    for index in reported_format_indexes:
        bucket = format_buckets[index]
        if len(bucket) == 1:
            format_columns[get_column_letter(index)] = sorted(bucket)[0]
    mixed_letters = [get_column_letter(index) for index in mixed_reported]

    formula_evidence: Dict[str, Any] = {
        "formula_cell_count": formula_cell_count,
        "samples": formula_samples,
    }
    if formula_cell_count == 0:
        formula_evidence["uncached_formula_cell_count"] = 0
        formula_evidence["uncached_scan_truncated"] = False
    else:
        formula_evidence["uncached_formula_cell_count"] = None
        formula_evidence["uncached_scan_truncated"] = True

    return {
        "sheet_name": str(worksheet.title),
        "used_range": used_range,
        "hidden_rows": hidden_row_indexes,
        "hidden_row_count": hidden_row_total,
        "hidden_rows_truncated": hidden_rows_truncated,
        "hidden_columns": [get_column_letter(index) for index in hidden_column_indexes],
        "hidden_column_count": hidden_column_total,
        "hidden_columns_truncated": hidden_columns_truncated,
        "merged_regions": merged_regions,
        "merged_region_count": len(merged_ranges),
        "merged_regions_truncated": len(merged_ranges) > MAX_EVIDENCE_MERGED_REGIONS,
        "named_tables": named_tables,
        "named_table_count": len(worksheet.tables),
        "autofilter": autofilter,
        "formula_evidence": formula_evidence,
        "number_formats": {
            "columns": format_columns,
            "mixed_format_columns": mixed_letters,
            "truncated": len(format_buckets) > MAX_EVIDENCE_FORMAT_COLUMNS,
        },
        "leading_zero_text_cells": leading_zero_text_cells,
        "_formula_coords": formula_coords,
        "_formula_coords_truncated": coords_truncated,
    }


def _coordinate_key(coordinate: str) -> Tuple[int, int]:
    letters = "".join(character for character in coordinate if character.isalpha())
    digits = "".join(character for character in coordinate if character.isdigit())
    return int(digits), column_index_from_string(letters)


def _resolve_xlsx_cached_formula_state(
    readable_content: bytes,
    sheets: List[Dict[str, Any]],
) -> None:
    """Fill cached-state counts by streaming the values-only view of formulas."""
    targets: Dict[str, Dict[str, Any]] = {}
    for sheet in sheets:
        coords = sheet.pop("_formula_coords", [])
        coords_truncated = bool(sheet.pop("_formula_coords_truncated", False))
        if not coords:
            continue
        sample_coords = {}
        for sample in sheet["formula_evidence"]["samples"]:
            try:
                sample_coords[_coordinate_key(str(sample["cell"]))] = sample
            except (ValueError, TypeError):
                continue
        targets[sheet["sheet_name"]] = {
            "coords": set(coords),
            "coords_truncated": coords_truncated,
            "sample_coords": sample_coords,
            "uncached": 0,
        }
    if not targets:
        return
    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(readable_content),
            read_only=True,
            data_only=True,
        )
    except Exception:
        for sheet in sheets:
            formula_evidence = sheet["formula_evidence"]
            formula_evidence["uncached_formula_cell_count"] = None
            formula_evidence["uncached_scan_truncated"] = True
        return
    try:
        for worksheet in workbook.worksheets:
            target = targets.get(worksheet.title)
            if target is None:
                continue
            for row_position, row in enumerate(worksheet.iter_rows(), start=1):
                if not target["coords"]:
                    break
                for column_position, cell in enumerate(row, start=1):
                    row_number = getattr(cell, "row", None)
                    column_number = getattr(cell, "column", None)
                    if not isinstance(row_number, int) or not isinstance(column_number, int):
                        # EmptyCell padding in read-only mode has no coordinates.
                        row_number, column_number = row_position, column_position
                    key = (row_number, column_number)
                    if key not in target["coords"]:
                        continue
                    target["coords"].discard(key)
                    cached_present = cell.value is not None and str(cell.value).strip() != ""
                    if not cached_present:
                        target["uncached"] += 1
                    sample = target["sample_coords"].get(key)
                    if sample is not None:
                        sample["cached_present"] = cached_present
    finally:
        workbook.close()
    for sheet in sheets:
        target = targets.get(sheet["sheet_name"])
        if target is None:
            continue
        formula_evidence = sheet["formula_evidence"]
        unresolved = bool(target["coords"]) or target["coords_truncated"]
        if unresolved:
            formula_evidence["uncached_formula_cell_count"] = None
            formula_evidence["uncached_scan_truncated"] = True
        else:
            formula_evidence["uncached_formula_cell_count"] = target["uncached"]
            formula_evidence["uncached_scan_truncated"] = False
        for sample in formula_evidence["samples"]:
            sample.setdefault("cached_present", None)


def _ignore_invalid_autofilter_metadata(content: bytes) -> Tuple[bytes, Set[str]]:
    """Remove unreadable worksheet filter metadata from an in-memory OOXML copy."""

    affected_paths: Set[str] = set()
    output = io.BytesIO()
    changed = False
    with zipfile.ZipFile(io.BytesIO(content), "r") as source:
        with zipfile.ZipFile(output, "w") as target:
            for entry in source.infolist():
                payload = source.read(entry.filename)
                if entry.filename.startswith("xl/worksheets/") and entry.filename.endswith(".xml"):
                    worksheet_changed = False

                    def replace_autofilter(match: re.Match[bytes]) -> bytes:
                        nonlocal worksheet_changed
                        ref_match = AUTOFILTER_REF_PATTERN.search(match.group(0))
                        if ref_match is None:
                            return match.group(0)
                        ref = ref_match.group(2).decode("utf-8", errors="replace")
                        try:
                            AutoFilter(ref=ref)
                        except ValueError:
                            worksheet_changed = True
                            return b""
                        return match.group(0)

                    payload = AUTOFILTER_ELEMENT_PATTERN.sub(replace_autofilter, payload)
                    if worksheet_changed:
                        changed = True
                        affected_paths.add(entry.filename)
                target.writestr(entry, payload)
    return (output.getvalue(), affected_paths) if changed else (content, affected_paths)


def _parse_xls_listing(content: bytes) -> List[ListingSheetPayload]:
    workbook = xlrd.open_workbook(file_contents=content, on_demand=True)
    layout_evidence = _collect_xls_layout_evidence(content)
    limitations = [
        XLS_FORMULA_LIMITATION,
        XLS_NUMBER_FORMAT_LIMITATION,
        XLS_LAYOUT_LIMITATION,
    ]
    if layout_evidence is None:
        limitations.append(XLS_LAYOUT_METADATA_UNAVAILABLE)
    try:
        sheets: List[ListingSheetPayload] = []
        parse_facts: Dict[str, Dict[str, Any]] = {}
        for position, sheet_name in enumerate(workbook.sheet_names(), start=1):
            worksheet = workbook.sheet_by_name(sheet_name)
            visibility = XLS_VISIBILITY.get(int(getattr(worksheet, "visibility", -1)), "unknown")
            used_rows = int(worksheet.nrows)
            used_columns = int(worksheet.ncols)
            used_range = (
                f"A1:{get_column_letter(used_columns)}{used_rows}"
                if used_rows and used_columns
                else None
            )
            raw_rows = [
                [_xls_cell_text(workbook, worksheet, row_index, col_index) for col_index in range(worksheet.ncols)]
                for row_index in range(worksheet.nrows)
            ]
            if not raw_rows:
                parse_facts[sheet_name] = {
                    "sheet_index": position,
                    "visibility": visibility,
                    "used_range": used_range,
                    "used_row_count": used_rows,
                    "used_column_count": used_columns,
                    "content_kind": "empty",
                    "emitted": False,
                    "omission_reason": "empty_sheet",
                    "header_row_numbers": [],
                    "data_start_row_number": None,
                }
                continue
            headers, source_headers, data_rows, data_start, header_indexes = _header_and_data_rows(raw_rows)
            rows, row_numbers = _build_rows(headers, data_rows, data_start)
            usable = bool(rows) or _has_usable_headers(headers)
            parse_facts[sheet_name] = {
                "sheet_index": position,
                "visibility": visibility,
                "used_range": used_range,
                "used_row_count": used_rows,
                "used_column_count": used_columns,
                "content_kind": _sheet_content_kind(raw_rows, data_start),
                "emitted": usable,
                "omission_reason": None if usable else "no_usable_headers",
                "header_row_numbers": [index + 1 for index in header_indexes],
                "data_start_row_number": data_start + 1,
            }
            if usable:
                sheets.append(
                    ListingSheetPayload(
                        sheet_name=sheet_name,
                        headers=headers,
                        source_headers=source_headers,
                        rows=rows,
                        row_numbers=row_numbers,
                    )
                )
        if not sheets:
            raise ValueError("xls listing has no non-empty sheets")
        manifest, sheet_evidence = _build_workbook_manifest(
            source_format="xls",
            content=content,
            parse_facts=parse_facts,
            physical=(
                {
                    "sheets": [
                        {"sheet_name": name, **metadata}
                        for name, metadata in layout_evidence.items()
                    ]
                }
                if layout_evidence is not None
                else None
            ),
            limitations=limitations,
        )
        for payload in sheets:
            _attach_sheet_evidence(
                payload,
                parse_facts[payload.sheet_name],
                sheet_evidence.get(payload.sheet_name),
            )
            payload.workbook_manifest = manifest
        return sheets
    finally:
        workbook.release_resources()


def _collect_xls_layout_evidence(content: bytes) -> Optional[Dict[str, Dict[str, Any]]]:
    """Best-effort hidden/merged metadata for legacy XLS via ``formatting_info``."""
    try:
        book = xlrd.open_workbook(file_contents=content, formatting_info=True)
    except Exception:
        return None
    try:
        result: Dict[str, Dict[str, Any]] = {}
        for sheet in book.sheets():
            hidden_rows = sorted(
                row_index
                for row_index, info in (getattr(sheet, "rowinfo_map", None) or {}).items()
                if getattr(info, "hidden", False)
            )
            hidden_columns = sorted(
                column_index
                for column_index, info in (getattr(sheet, "colinfo_map", None) or {}).items()
                if getattr(info, "hidden", False)
            )
            merged_regions = sorted(
                f"{get_column_letter(clo + 1)}{rlo + 1}:{get_column_letter(chi)}{rhi}"
                for rlo, rhi, clo, chi in (getattr(sheet, "merged_cells", None) or [])
            )
            result[str(sheet.name)] = {
                "hidden_rows": hidden_rows[:MAX_EVIDENCE_HIDDEN_ROWS],
                "hidden_row_count": len(hidden_rows),
                "hidden_rows_truncated": len(hidden_rows) > MAX_EVIDENCE_HIDDEN_ROWS,
                "hidden_columns": [
                    get_column_letter(column_index)
                    for column_index in hidden_columns[:MAX_EVIDENCE_HIDDEN_COLUMNS]
                ],
                "hidden_column_count": len(hidden_columns),
                "hidden_columns_truncated": len(hidden_columns) > MAX_EVIDENCE_HIDDEN_COLUMNS,
                "merged_regions": merged_regions[:MAX_EVIDENCE_MERGED_REGIONS],
                "merged_region_count": len(merged_regions),
                "merged_regions_truncated": len(merged_regions) > MAX_EVIDENCE_MERGED_REGIONS,
            }
        return result
    except Exception:
        return None
    finally:
        book.release_resources()


def _xls_cell_text(workbook: xlrd.book.Book, worksheet: xlrd.sheet.Sheet, row_index: int, col_index: int) -> str:
    cell = worksheet.cell(row_index, col_index)
    if cell.ctype == xlrd.XL_CELL_DATE:
        try:
            dt = xlrd.xldate.xldate_as_datetime(cell.value, workbook.datemode)
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                return dt.date().isoformat()
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(cell.value).strip()
    return _cell_text(cell.value)
