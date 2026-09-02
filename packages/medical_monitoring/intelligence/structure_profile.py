"""C1 deterministic structure profile and exact source-cell locators.

Format-neutral, data-driven admission contract for one staged listing input
(Phase C C1, design §Structure Profile / §Mapping And Fact Boundary):

* The caller supplies already-parsed tables (sheet name, headers, row dicts,
  optional 1-based original file row numbers).  This module never opens or
  parses files, so CSV/XLS/XLSX differences end at the parse authority.
* The profile records only generic structure signals: row/column counts,
  headers, bounded sample values, primitive-type inference (via
  :mod:`intelligence.normalization`), date-range candidates, missingness and
  candidate subject/visit/date keys.  Project-specific semantic meaning is
  never inferred here; keyword heuristics are generic clinical-listing
  tokens, not project constants.
* A :class:`SourceCellLocator` pins one cell to (project, source revision,
  snapshot, source file, table/sheet, row, column) plus the raw value.
  ``resolve_locator`` / ``resolve_locator_from_store`` are the round trip
  back to the exact raw value; any tampering, digest mismatch or store
  binding mismatch fails closed.
* Identity binding stays with the existing authorities:
  ``domain.entities.SourceRevision.from_bytes`` binds the source bytes and
  ``domain.entities.ListingSnapshot.from_content`` binds one table's full
  snapshot rows; :class:`graph.Store` persists both and serves the accepted
  content that locators resolve against.

All objects are frozen, deterministic and content-hashed (canonical JSON via
:mod:`intelligence.primitives`); the profile stores only integers, strings,
booleans and ISO dates, never floats, so hashes are stable.  No absolute
path ever enters a profile or locator: source files are named by their
path-free name relative to the isolated input root.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..domain.entities import ListingSnapshot, SourceRevision
from .normalization import NormalizationKind, is_missing, normalize_date, normalize_value
from .primitives import (
    canonical_json,
    content_hash,
    deep_freeze_json,
    validate_sha256_hex,
)

__all__ = [
    "StructureProfileError",
    "ColumnProfile",
    "TableProfile",
    "ListingStructureProfile",
    "SourceCellLocator",
    "ResolvedCell",
    "PROFILE_VERSION",
    "LOCATOR_VERSION",
    "MAX_SAMPLES",
    "MAX_CONTEXT_ROWS",
    "canonical_listing_content",
    "table_rows_from_sheet",
    "build_listing_profile",
    "build_table_snapshot",
    "build_table_locators",
    "build_sheet_locators",
    "resolve_locator",
    "resolve_locator_from_store",
    "execution_source_revision",
]


class StructureProfileError(ValueError):
    """Fail-closed structure-profile or locator round-trip violation."""


PROFILE_VERSION = "1"
LOCATOR_VERSION = "1"

#: Bounded sample values per column (first-seen distinct non-missing values).
MAX_SAMPLES = 5

#: Bounded neighboring-row context returned with a resolved cell (each side).
MAX_CONTEXT_ROWS = 1

#: Generic clinical-listing header tokens used only to *hint* candidate keys.
#: These are domain-generic terms, not project-specific column names.
_SUBJECT_HEADER_TOKENS: Tuple[str, ...] = ("subject", "subj", "受试者")
_VISIT_HEADER_TOKENS: Tuple[str, ...] = ("visit", "访视")
_DATE_HEADER_TOKENS: Tuple[str, ...] = ("date", "dt", "日期", "时间")


# ---------------------------------------------------------------------------
# Small validation helpers
# ---------------------------------------------------------------------------

def _validate_path_free_name(source_file: str) -> str:
    """Reject absolute paths, separators and traversal in a source file name."""
    if not isinstance(source_file, str) or not source_file.strip():
        raise StructureProfileError("source_file is required")
    name = source_file.strip()
    if name in (".", "..") or "/" in name or "\\" in name or ":" in name:
        raise StructureProfileError(
            "source_file must be a path-free file name relative to the "
            f"isolated input root; got {source_file!r}"
        )
    return name


def _validate_tables_input(tables: Sequence[Any]) -> List[Dict[str, Any]]:
    """Normalize the format-neutral table records and validate their shape.

    Each record needs ``table_name``, ``headers`` and ``rows``; ``row_numbers``
    (1-based original file row numbers, header included) is optional but must
    match ``rows`` when present.
    """
    if not isinstance(tables, (list, tuple)) or not tables:
        raise StructureProfileError("tables must be a non-empty sequence")
    normalized: List[Dict[str, Any]] = []
    seen_names: set = set()
    for table in tables:
        if isinstance(table, Mapping):
            get = table.get
        elif hasattr(table, "sheet_name"):
            # Duck-typed ListingSheetPayload from the listing parse authority;
            # its ``sheet_name`` is the table name here.
            def get(key: str, default: Any = None, _t: Any = table) -> Any:
                if key == "table_name":
                    return getattr(_t, "sheet_name", default)
                return getattr(_t, key, default)
        elif isinstance(table, (list, tuple)) and len(table) >= 2:
            def get(key: str, default: Any = None, _t: Any = table) -> Any:
                if key == "table_name":
                    return _t[0]
                if key == "headers":
                    return _t[1]
                if key == "rows":
                    return _t[2] if len(_t) > 2 else default
                if key == "row_numbers":
                    return _t[3] if len(_t) > 3 else default
                return default
        else:
            raise StructureProfileError(
                "each table must be a mapping with table_name/headers/rows or a "
                "sheet-like object"
            )
        name = get("table_name")
        if isinstance(name, Mapping) or not isinstance(name, str) or not name.strip():
            raise StructureProfileError("table_name must be a non-empty string")
        if name in seen_names:
            raise StructureProfileError(f"duplicate table_name {name!r}")
        seen_names.add(name)
        headers = get("headers")
        rows = get("rows")
        if not isinstance(headers, (list, tuple)) or not headers:
            raise StructureProfileError(f"table {name!r} requires a non-empty headers list")
        clean_headers: List[str] = []
        for index, header in enumerate(headers):
            text = "" if header is None else str(header).strip()
            if not text:
                raise StructureProfileError(
                    f"table {name!r} header {index} is empty; the parse authority "
                    "must supply named columns"
                )
            if text in clean_headers:
                raise StructureProfileError(
                    f"table {name!r} has duplicate header {text!r}"
                )
            clean_headers.append(text)
        if not isinstance(rows, (list, tuple)):
            raise StructureProfileError(f"table {name!r} rows must be a list of dicts")
        clean_rows: List[Dict[str, Any]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise StructureProfileError(
                    f"table {name!r} row {row_index} is not a mapping"
                )
            clean_rows.append({header: row.get(header) for header in clean_headers})
        row_numbers = get("row_numbers")
        if row_numbers is not None:
            if not isinstance(row_numbers, (list, tuple)) or len(row_numbers) != len(rows):
                raise StructureProfileError(
                    f"table {name!r} row_numbers must align with rows"
                )
            for row_index, number in enumerate(row_numbers):
                if not isinstance(number, int) or isinstance(number, bool) or number < 1:
                    raise StructureProfileError(
                        f"table {name!r} row_numbers[{row_index}] must be a "
                        f"positive 1-based integer; got {number!r}"
                    )
            row_numbers = [int(number) for number in row_numbers]
        else:
            # Header occupies file row 1; data rows follow in order.
            row_numbers = [index + 2 for index in range(len(rows))]
        normalized.append({
            "table_name": name,
            "headers": clean_headers,
            "rows": clean_rows,
            "row_numbers": row_numbers,
        })
    return normalized


def _cell_type_counts(rows: Sequence[Mapping[str, Any]], header: str) -> Dict[str, int]:
    """Classify a column's non-missing raw values with integer counts only."""
    date_full = date_partial = number = text = 0
    for row in rows:
        value = row.get(header)
        if is_missing(value):
            continue
        nv = normalize_date(value)
        if nv.kind == NormalizationKind.DATE:
            date_full += 1
        elif nv.kind == NormalizationKind.PARTIAL_DATE:
            date_partial += 1
        elif normalize_value(value, expected_kind=NormalizationKind.NUMBER).kind == NormalizationKind.NUMBER:
            number += 1
        else:
            text += 1
    return {
        "date_full": date_full,
        "date_partial": date_partial,
        "number": number,
        "text": text,
    }


def _inferred_type(counts: Mapping[str, int]) -> str:
    non_missing = sum(counts.values())
    if non_missing == 0:
        return "empty"
    if counts["date_full"] + counts["date_partial"] == non_missing:
        return "date"
    if counts["number"] == non_missing:
        return "number"
    if counts["text"] == non_missing:
        return "text"
    return "mixed"


def _date_range(rows: Sequence[Mapping[str, Any]], header: str) -> Optional[Dict[str, Any]]:
    """Min/max full-date ISO range for one column; None when no full dates."""
    parsed: List[str] = []
    for row in rows:
        value = row.get(header)
        if is_missing(value):
            continue
        nv = normalize_date(value)
        if nv.kind == NormalizationKind.DATE and nv.normalized:
            parsed.append(str(nv.normalized))
    if not parsed:
        return None
    return {"min": min(parsed), "max": max(parsed), "parsed_count": len(parsed)}


def _matches_any_token(header: str, tokens: Sequence[str]) -> bool:
    lowered = header.lower()
    return any(token in lowered for token in tokens)


# ---------------------------------------------------------------------------
# Profile value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnProfile:
    """Deterministic generic profile of one column."""

    column_index: int
    name: str
    missing_count: int
    distinct_count: int
    inferred_type: str
    type_counts: Dict[str, int]
    samples: Tuple[str, ...]
    date_range: Optional[Dict[str, str]]
    is_subject_key_candidate: bool = False
    is_visit_candidate: bool = False
    is_date_candidate: bool = False
    candidate_reasons: Tuple[str, ...] = ()

    def to_payload(self) -> Dict[str, Any]:
        return {
            "column_index": self.column_index,
            "name": self.name,
            "missing_count": self.missing_count,
            "distinct_count": self.distinct_count,
            "inferred_type": self.inferred_type,
            "type_counts": dict(self.type_counts),
            "samples": list(self.samples),
            "date_range": dict(self.date_range) if self.date_range else None,
            "is_subject_key_candidate": self.is_subject_key_candidate,
            "is_visit_candidate": self.is_visit_candidate,
            "is_date_candidate": self.is_date_candidate,
            "candidate_reasons": list(self.candidate_reasons),
        }


@dataclass(frozen=True)
class TableProfile:
    """Deterministic generic profile of one table/sheet."""

    table_name: str
    row_count: int
    column_count: int
    headers: Tuple[str, ...]
    first_row_number: int
    last_row_number: int
    columns: Tuple[ColumnProfile, ...]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "headers": list(self.headers),
            "first_row_number": self.first_row_number,
            "last_row_number": self.last_row_number,
            "columns": [column.to_payload() for column in self.columns],
        }


@dataclass(frozen=True)
class ListingStructureProfile:
    """Frozen, content-hashed structure profile of one staged listing input."""

    project_id: str
    source_revision_id: str
    source_file: str
    source_file_digest: str
    tables: Tuple[TableProfile, ...]

    def __post_init__(self) -> None:
        if not self.project_id:
            raise StructureProfileError("project_id is required")
        if not self.source_revision_id:
            raise StructureProfileError("source_revision_id is required")
        _validate_path_free_name(self.source_file)
        validate_sha256_hex(self.source_file_digest, "source_file_digest")
        object.__setattr__(self, "tables", tuple(self.tables))

    def to_payload(self) -> Dict[str, Any]:
        return {
            "profile_version": PROFILE_VERSION,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "source_file": self.source_file,
            "source_file_digest": self.source_file_digest,
            "tables": [table.to_payload() for table in self.tables],
        }

    @property
    def content_hash(self) -> str:
        return content_hash(self.to_payload())

    @property
    def profile_id(self) -> str:
        return f"strcprof_{self.content_hash[:24]}"


# ---------------------------------------------------------------------------
# Profile builder
# ---------------------------------------------------------------------------

def build_listing_profile(
    project_id: str,
    source_revision_id: str,
    source_file: str,
    source_file_digest: str,
    tables: Sequence[Any],
) -> ListingStructureProfile:
    """Build the deterministic format-neutral structure profile.

    ``tables`` accepts plain mappings (``table_name`` / ``headers`` / ``rows``
    / optional ``row_numbers``) or sheet-like objects from the listing parse
    authority.  The same input always produces the same profile content hash.
    """
    _validate_path_free_name(source_file)
    validate_sha256_hex(source_file_digest, "source_file_digest")
    normalized_tables = _validate_tables_input(tables)
    table_profiles: List[TableProfile] = []
    for table in normalized_tables:
        headers: List[str] = table["headers"]
        rows: List[Dict[str, Any]] = table["rows"]
        row_numbers: List[int] = table["row_numbers"]
        columns: List[ColumnProfile] = []
        for column_index, header in enumerate(headers):
            missing = sum(1 for row in rows if is_missing(row.get(header)))
            distinct_values = []
            seen = set()
            for row in rows:
                value = row.get(header)
                if is_missing(value):
                    continue
                key = canonical_json(deep_freeze_json(value))
                if key not in seen:
                    seen.add(key)
                    if len(distinct_values) < MAX_SAMPLES:
                        distinct_values.append(value)
            distinct_count = len(seen)
            counts = _cell_type_counts(rows, header)
            non_missing = sum(counts.values())
            date_range = _date_range(rows, header)
            is_subject = _matches_any_token(header, _SUBJECT_HEADER_TOKENS)
            is_visit = _matches_any_token(header, _VISIT_HEADER_TOKENS)
            # Integer-only threshold: at least 3/5 of non-missing values parse
            # as full dates and at least two exist.
            is_date = date_range is not None and date_range["parsed_count"] * 5 >= non_missing * 3 and date_range["parsed_count"] >= 2
            # A subject-key candidate is a generic-token header, or a fully
            # distinct non-numeric text column (typical subject identifier).
            is_subject_candidate = is_subject or (
                distinct_count == non_missing and distinct_count >= 3 and counts["text"] == non_missing
            )
            reasons: List[str] = []
            if is_subject:
                reasons.append("header matches generic subject token")
            elif is_subject_candidate:
                reasons.append("all non-missing values are distinct non-numeric text")
            if is_visit:
                reasons.append("header matches generic visit token")
            if is_date:
                reasons.append("most non-missing values parse as full dates")
            columns.append(ColumnProfile(
                column_index=column_index,
                name=header,
                missing_count=missing,
                distinct_count=distinct_count,
                inferred_type=_inferred_type(counts),
                type_counts=counts,
                samples=tuple(
                    value if isinstance(value, str) else canonical_json(deep_freeze_json(value))
                    for value in distinct_values
                ),
                date_range=date_range,
                is_subject_key_candidate=is_subject_candidate,
                is_visit_candidate=is_visit,
                is_date_candidate=bool(is_date),
                candidate_reasons=tuple(reasons),
            ))
        table_profiles.append(TableProfile(
            table_name=table["table_name"],
            row_count=len(rows),
            column_count=len(headers),
            headers=tuple(headers),
            first_row_number=row_numbers[0] if row_numbers else 0,
            last_row_number=row_numbers[-1] if row_numbers else 0,
            columns=tuple(columns),
        ))
    return ListingStructureProfile(
        project_id=project_id,
        source_revision_id=source_revision_id,
        source_file=source_file.strip(),
        source_file_digest=source_file_digest,
        tables=tuple(table_profiles),
    )


# ---------------------------------------------------------------------------
# Snapshot / locator construction
# ---------------------------------------------------------------------------

def canonical_listing_content(tables: Sequence[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """The canonical per-table content shape the Store persists and locators
    resolve against: ``{table_name: [row dicts]}`` with fixed column order.

    Accepts the same table records as :func:`build_listing_profile`.
    """
    content: Dict[str, List[Dict[str, Any]]] = {}
    for table in _validate_tables_input(tables):
        headers = table["headers"]
        content[table["table_name"]] = [
            {header: row[header] for header in headers} for row in table["rows"]
        ]
    return content


def table_rows_from_sheet(sheet: Any) -> Tuple[str, List[str], List[Dict[str, Any]], List[int]]:
    """Extract ``(table_name, headers, rows, row_numbers)`` from a sheet record
    (mapping or sheet-like object) using the shared validation."""
    normalized = _validate_tables_input([sheet])
    table = normalized[0]
    return table["table_name"], table["headers"], table["rows"], table["row_numbers"]


def build_table_snapshot(
    project_id: str,
    revision_id: str,
    snapshot_version: str,
    table_name: str,
    headers: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
    *,
    is_synthetic: bool = True,
    created_at: str = "",
) -> ListingSnapshot:
    """Authoritative full snapshot of one table via the ListingSnapshot
    authority.  ``snapshot_id`` is deterministic from project/revision/table
    and the canonical row content, so re-admitting identical content replays
    idempotently in the Store."""
    if not snapshot_version:
        raise StructureProfileError("snapshot_version is required")
    normalized = _validate_tables_input([{
        "table_name": table_name,
        "headers": list(headers),
        "rows": list(rows),
    }])[0]
    canonical_rows = [{header: row[header] for header in normalized["headers"]}
                      for row in normalized["rows"]]
    rows_digest = content_hash(deep_freeze_json(canonical_rows))
    snapshot_id = "snapc1_" + content_hash({
        "project_id": project_id,
        "revision_id": revision_id,
        "table_name": normalized["table_name"],
        "rows_digest": rows_digest,
        "snapshot_version": snapshot_version,
    })[:24]
    structure = {
        # Flat scalar values only: the Store's snapshot replay comparison
        # round-trips structure through JSON, so nested sequences here would
        # never compare equal after a freeze/serialize cycle.  The full
        # header and row-number detail is carried by the structure profile
        # and the locators; these digests pin the same information.
        "table_name": normalized["table_name"],
        "row_count": len(normalized["rows"]),
        "headers_digest": content_hash(list(normalized["headers"])),
        "row_numbers_digest": content_hash(list(normalized["row_numbers"])),
    }
    return ListingSnapshot.from_content(
        snapshot_id,
        project_id,
        revision_id,
        snapshot_version,
        canonical_rows,
        structure=structure,
        is_synthetic=is_synthetic,
        created_at=created_at,
    )


def build_table_locators(
    project_id: str,
    source_revision_id: str,
    snapshot_id: str,
    source_file: str,
    source_file_digest: str,
    table_name: str,
    headers: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
    row_numbers: Optional[Sequence[int]] = None,
) -> Tuple["SourceCellLocator", ...]:
    """Build one exact locator per cell-safe row for a table.

    A locator is emitted for every (row, column) pair of the table so any
    canonical fact derived later can cite its exact source cell.
    """
    normalized = _validate_tables_input([{
        "table_name": table_name,
        "headers": list(headers),
        "rows": list(rows),
        "row_numbers": list(row_numbers) if row_numbers is not None else None,
    }])[0]
    _validate_path_free_name(source_file)
    validate_sha256_hex(source_file_digest, "source_file_digest")
    if not snapshot_id:
        raise StructureProfileError("snapshot_id is required")
    locators: List[SourceCellLocator] = []
    for row_index, row in enumerate(normalized["rows"]):
        for column_index, header in enumerate(normalized["headers"]):
            locators.append(SourceCellLocator(
                project_id=project_id,
                source_revision_id=source_revision_id,
                snapshot_id=snapshot_id,
                source_file=source_file.strip(),
                source_file_digest=source_file_digest,
                table_name=normalized["table_name"],
                row_index=row_index,
                row_number=normalized["row_numbers"][row_index],
                column=header,
                column_index=column_index,
                raw_value=row[header],
            ))
    return tuple(locators)


def build_sheet_locators(
    project_id: str,
    source_revision_id: str,
    snapshot_id: str,
    source_file: str,
    source_file_digest: str,
    sheet: Any,
) -> Tuple["SourceCellLocator", ...]:
    """Convenience wrapper building all locators for one parsed sheet."""
    table_name, headers, rows, row_numbers = table_rows_from_sheet(sheet)
    return build_table_locators(
        project_id,
        source_revision_id,
        snapshot_id,
        source_file,
        source_file_digest,
        table_name,
        headers,
        rows,
        row_numbers,
    )


# ---------------------------------------------------------------------------
# Locator value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceCellLocator:
    """Exact, path-free source-cell locator with the raw value bound in.

    ``row_index`` resolves against the canonical per-table content; ``row_number``
    is the 1-based original file row (header included) for human display.
    ``locator_id`` is deterministic from the identity fields; a supplied id
    must match exactly, so a held citation can never be silently rebound to
    different fields.
    """

    project_id: str
    source_revision_id: str
    snapshot_id: str
    source_file: str
    source_file_digest: str
    table_name: str
    row_index: int
    row_number: int
    column: str
    column_index: int
    raw_value: Any
    locator_id: str = ""

    def __post_init__(self) -> None:
        if not self.project_id:
            raise StructureProfileError("project_id is required")
        if not self.source_revision_id:
            raise StructureProfileError("source_revision_id is required")
        if not self.snapshot_id:
            raise StructureProfileError("snapshot_id is required")
        _validate_path_free_name(self.source_file)
        validate_sha256_hex(self.source_file_digest, "source_file_digest")
        if not self.table_name:
            raise StructureProfileError("table_name is required")
        for field_name, value in (("row_index", self.row_index), ("row_number", self.row_number)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise StructureProfileError(f"{field_name} must be a non-negative integer")
        if self.row_number < 1:
            raise StructureProfileError("row_number must be 1-based (>= 1)")
        if not self.column:
            raise StructureProfileError("column is required")
        if not isinstance(self.column_index, int) or isinstance(self.column_index, bool) or self.column_index < 0:
            raise StructureProfileError("column_index must be a non-negative integer")
        object.__setattr__(self, "raw_value", deep_freeze_json(self.raw_value))
        derived = "srccell_" + self.content_hash[:24]
        if not self.locator_id:
            object.__setattr__(self, "locator_id", derived)
        elif self.locator_id != derived:
            raise StructureProfileError(
                f"locator_id {self.locator_id!r} does not match the deterministic "
                f"identity-derived id {derived!r}"
            )

    def identity_payload(self) -> Dict[str, Any]:
        """Fields that determine the deterministic locator identity."""
        return {
            "locator_version": LOCATOR_VERSION,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "source_file": self.source_file,
            "source_file_digest": self.source_file_digest,
            "table_name": self.table_name,
            "row_index": self.row_index,
            "row_number": self.row_number,
            "column": self.column,
            "column_index": self.column_index,
            "raw_value": self.raw_value,
        }

    @property
    def content_hash(self) -> str:
        return content_hash(self.identity_payload())

    def to_payload(self) -> Dict[str, Any]:
        return {
            "locator_id": self.locator_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "source_file": self.source_file,
            "source_file_digest": self.source_file_digest,
            "table_name": self.table_name,
            "row_index": self.row_index,
            "row_number": self.row_number,
            "column": self.column,
            "column_index": self.column_index,
            "raw_value": self.raw_value,
        }


@dataclass(frozen=True)
class ResolvedCell:
    """Round-trip result: the exact raw value plus bounded neighbor context."""

    locator_id: str
    table_name: str
    row_index: int
    row_number: int
    column: str
    raw_value: Any
    context_before: Tuple[Dict[str, Any], ...]
    context_after: Tuple[Dict[str, Any], ...]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "locator_id": self.locator_id,
            "table_name": self.table_name,
            "row_index": self.row_index,
            "row_number": self.row_number,
            "column": self.column,
            "raw_value": self.raw_value,
            "context_before": [dict(row) for row in self.context_before],
            "context_after": [dict(row) for row in self.context_after],
        }


# ---------------------------------------------------------------------------
# Resolution (round trip)
# ---------------------------------------------------------------------------

def resolve_locator(
    locator: SourceCellLocator,
    listing_content: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    expected_locator_id: Optional[str] = None,
    source_bytes: Optional[bytes] = None,
    context_rows: int = MAX_CONTEXT_ROWS,
) -> ResolvedCell:
    """Resolve a locator back to the exact raw cell value; fail closed.

    ``listing_content`` is the canonical ``{table: [rows]}`` content (from the
    Store's accepted snapshot).  When ``expected_locator_id`` is given (the id
    a fact or UI citation holds), it must match the locator exactly.  When
    ``source_bytes`` is provided, its SHA-256 must equal the locator's bound
    file digest.
    """
    if not isinstance(locator, SourceCellLocator):
        raise StructureProfileError("locator must be a SourceCellLocator")
    if expected_locator_id is not None and expected_locator_id != locator.locator_id:
        raise StructureProfileError(
            f"locator id mismatch: citation holds {expected_locator_id!r}, "
            f"locator carries {locator.locator_id!r}"
        )
    if source_bytes is not None:
        actual = hashlib.sha256(source_bytes).hexdigest()
        if actual != locator.source_file_digest:
            raise StructureProfileError(
                "source bytes do not match the locator's bound file digest"
            )
    if not isinstance(listing_content, Mapping) or locator.table_name not in listing_content:
        raise StructureProfileError(
            f"listing content has no table {locator.table_name!r}"
        )
    rows = listing_content[locator.table_name]
    if not isinstance(rows, (list, tuple)) or not (0 <= locator.row_index < len(rows)):
        raise StructureProfileError(
            f"row index {locator.row_index} is out of range for table "
            f"{locator.table_name!r} ({len(rows)} rows)"
        )
    row = rows[locator.row_index]
    if not isinstance(row, Mapping) or locator.column not in row:
        raise StructureProfileError(
            f"column {locator.column!r} is missing from table "
            f"{locator.table_name!r} row {locator.row_index}"
        )
    actual_value = deep_freeze_json(row[locator.column])
    if actual_value != locator.raw_value:
        raise StructureProfileError(
            "resolved raw value does not match the locator: "
            f"{actual_value!r} != {locator.raw_value!r}"
        )
    before = tuple(
        dict(rows[i])
        for i in range(max(0, locator.row_index - max(0, context_rows)), locator.row_index)
    )
    after = tuple(
        dict(rows[i])
        for i in range(
            locator.row_index + 1,
            min(len(rows), locator.row_index + 1 + max(0, context_rows)),
        )
    )
    return ResolvedCell(
        locator_id=locator.locator_id,
        table_name=locator.table_name,
        row_index=locator.row_index,
        row_number=locator.row_number,
        column=locator.column,
        raw_value=actual_value,
        context_before=before,
        context_after=after,
    )


def resolve_locator_from_store(
    store: Any,
    locator: SourceCellLocator,
    *,
    expected_locator_id: Optional[str] = None,
    source_bytes: Optional[bytes] = None,
    context_rows: int = MAX_CONTEXT_ROWS,
) -> ResolvedCell:
    """Resolve a locator against the Store's accepted snapshot content.

    Verifies that the persisted snapshot binds the locator's project and
    source revision before loading the content, so a locator can never be
    resolved against a foreign snapshot.
    """
    snapshot = store.get_listing_snapshot(locator.snapshot_id)
    if snapshot.project_id != locator.project_id:
        raise StructureProfileError(
            f"snapshot {locator.snapshot_id!r} belongs to project "
            f"{snapshot.project_id!r}, locator binds {locator.project_id!r}"
        )
    if snapshot.revision_id != locator.source_revision_id:
        raise StructureProfileError(
            f"snapshot {locator.snapshot_id!r} belongs to revision "
            f"{snapshot.revision_id!r}, locator binds {locator.source_revision_id!r}"
        )
    listing_content = store.load_listing_content(locator.snapshot_id)
    return resolve_locator(
        locator,
        listing_content,
        expected_locator_id=expected_locator_id,
        source_bytes=source_bytes,
        context_rows=context_rows,
    )


# ---------------------------------------------------------------------------
# Authority bridge helpers
# ---------------------------------------------------------------------------

def execution_source_revision(revision: SourceRevision) -> Any:
    """Project an authoritative SourceRevision onto the execution-layer record
    the Store persists, carrying the full identity content hash unchanged."""
    from ..domain.execution import SourceRevision as ExecutionSourceRevision

    return ExecutionSourceRevision(
        revision_id=revision.revision_id,
        project_id=revision.project_id,
        source_type=revision.source_type,
        version=revision.version,
        content_hash=revision.content_hash,
        valid_from=revision.valid_from,
        scope=dict(revision.scope),
        created_at=revision.created_at,
    )
