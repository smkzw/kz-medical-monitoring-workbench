"""Phase C C1: format-neutral structure profile and exact source-cell locator
round-trip tests.

All fixtures are generated non-real files (synthetic CSV/XLSX written into a
temporary directory); no real project directory is read or written.  The
profile/locator layer consumes already-parsed tables, so both the stdlib CSV
path, the openpyxl XLSX path (via the existing listing parse authority) and
plain mapping input must produce identical deterministic profiles for
identical cell content.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from packages.medical_monitoring.domain.entities import (
    ListingSnapshot,
    SourceRevision,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.intelligence.structure_profile import (
    ColumnProfile,
    ListingStructureProfile,
    MAX_SAMPLES,
    ResolvedCell,
    SourceCellLocator,
    StructureProfileError,
    TableProfile,
    build_listing_profile,
    build_sheet_locators,
    build_table_locators,
    build_table_snapshot,
    canonical_listing_content,
    execution_source_revision,
    resolve_locator,
    resolve_locator_from_store,
    table_rows_from_sheet,
)

PROJECT_ID = "proj_c1_profile_demo"
REVISION_ID = "srcc1_profile_demo_0001"

CSV_HEADERS = ["subject_id", "visit", "record_date", "result_value", "unit"]
CSV_ROWS = [
    ["S001", "V1", "2026-01-05", "42", "U/L"],
    ["S002", "V1", "2026-01-06", "", "mg/dL"],
    ["S001", "V2", "2026-02-07", "47.5", "U/L"],
]


def _csv_bytes() -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    writer.writerows(CSV_ROWS)
    return buf.getvalue().encode("utf-8")


def _write_csv(tmp_path: Path) -> Path:
    path = tmp_path / "admission-listing.csv"
    path.write_bytes(_csv_bytes())
    return path


def _parse(path: Path, content: bytes):
    from services.api.app.listing_file_parser import parse_listing_file

    return parse_listing_file(path.name, content)


def _mapping_tables() -> list[dict]:
    """The same cell content as the CSV fixture, as plain mapping input with
    a non-string numeric column (format neutrality beyond the parser)."""
    rows = [
        {"subject_id": "S001", "visit": "V1", "record_date": "2026-01-05", "result_value": 42, "unit": "U/L"},
        {"subject_id": "S002", "visit": "V1", "record_date": "2026-01-06", "result_value": None, "unit": "mg/dL"},
        {"subject_id": "S001", "visit": "V2", "record_date": "2026-02-07", "result_value": 47.5, "unit": "U/L"},
    ]
    return [{"table_name": "admission-listing", "headers": list(CSV_HEADERS), "rows": rows}]


def _admitted(store: Store, tmp_path: Path, tables=None):
    """Admit the generated CSV through the full C1 identity chain and return
    (profile, locators, snapshot, file path)."""
    path = _write_csv(tmp_path)
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    revision = SourceRevision.from_bytes(
        REVISION_ID, PROJECT_ID, "listing", "v1", content,
        scope=(("source_file", path.name),),
    )
    sheets = tables if tables is not None else _parse(path, content)
    profile = build_listing_profile(PROJECT_ID, REVISION_ID, path.name, digest, sheets)
    table_name, headers, rows, row_numbers = table_rows_from_sheet(sheets[0])
    snapshot = build_table_snapshot(PROJECT_ID, REVISION_ID, "v1", table_name, headers, rows)
    locators = build_table_locators(
        PROJECT_ID, REVISION_ID, snapshot.snapshot_id, path.name, digest,
        table_name, headers, rows, row_numbers,
    )
    store.create_project(PROJECT_ID, "C1 Profile Demo")
    store.add_source_revision(execution_source_revision(revision))
    store.add_listing_snapshot(snapshot, canonical_listing_content(sheets))
    return profile, locators, snapshot, path


# ---------------------------------------------------------------------------
# Structure profile
# ---------------------------------------------------------------------------

def test_profile_is_deterministic_and_content_hashed(tmp_path: Path) -> None:
    path = _write_csv(tmp_path)
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    sheets = _parse(path, content)
    first = build_listing_profile(PROJECT_ID, REVISION_ID, path.name, digest, sheets)
    second = build_listing_profile(PROJECT_ID, REVISION_ID, path.name, digest, sheets)
    assert first == second
    assert first.content_hash == second.content_hash
    assert first.profile_id == second.profile_id
    assert first.profile_id.startswith("strcprof_")
    assert len(first.content_hash) == 64


def test_profile_records_generic_structure_signals(tmp_path: Path) -> None:
    profile, _, _, path = _admitted(Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path)
    assert profile.project_id == PROJECT_ID
    assert profile.source_revision_id == REVISION_ID
    assert profile.source_file == "admission-listing.csv"
    assert profile.source_file_digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(profile.tables) == 1
    table: TableProfile = profile.tables[0]
    assert table.table_name == "admission-listing"
    assert table.row_count == 3
    assert table.column_count == 5
    assert table.headers == tuple(CSV_HEADERS)
    assert table.first_row_number == 2 and table.last_row_number == 4
    by_name: dict[str, ColumnProfile] = {c.name: c for c in table.columns}
    subject = by_name["subject_id"]
    assert subject.is_subject_key_candidate
    assert any("subject" in reason for reason in subject.candidate_reasons)
    assert subject.distinct_count == 2
    visit = by_name["visit"]
    assert visit.is_visit_candidate and not visit.is_subject_key_candidate
    date_column = by_name["record_date"]
    assert date_column.is_date_candidate
    assert date_column.inferred_type == "date"
    assert date_column.date_range == {"min": "2026-01-05", "max": "2026-02-07", "parsed_count": 3}
    value = by_name["result_value"]
    assert value.inferred_type == "number"
    assert value.missing_count == 1
    assert value.samples == ("42", "47.5")
    unit = by_name["unit"]
    assert unit.inferred_type == "text"
    assert len(unit.samples) == 2
    for column in table.columns:
        assert len(column.samples) <= MAX_SAMPLES


def test_profile_is_format_neutral_across_parser_and_mapping_input(tmp_path: Path) -> None:
    path = _write_csv(tmp_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    from_csv = build_listing_profile(
        PROJECT_ID, REVISION_ID, path.name, digest, _parse(path, path.read_bytes())
    )
    from_mapping = build_listing_profile(
        PROJECT_ID, REVISION_ID, path.name, digest, _mapping_tables()
    )
    # Cell content is identical; the numeric column's lexical difference
    # ("42" vs 42) may only surface in bounded sample text, never structure.
    assert from_csv.tables[0].row_count == from_mapping.tables[0].row_count
    assert from_csv.tables[0].headers == from_mapping.tables[0].headers
    assert [c.inferred_type for c in from_csv.tables[0].columns] == [
        c.inferred_type for c in from_mapping.tables[0].columns
    ]
    assert [c.is_subject_key_candidate for c in from_mapping.tables[0].columns][0]
    assert from_mapping.tables[0].columns[3].missing_count == 1
    assert from_mapping.tables[0].columns[3].date_range is None


def test_profile_from_xlsx_matches_csv_profile_for_identical_cells(
    tmp_path: Path,
) -> None:
    pytest.importorskip("openpyxl")
    import openpyxl

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "vitals"
    sheet.append(CSV_HEADERS)
    for row in CSV_ROWS:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    content = buffer.getvalue()
    path = tmp_path / "admission-listing.xlsx"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    sheets = _parse(path, content)
    profile = build_listing_profile(PROJECT_ID, REVISION_ID, path.name, digest, sheets)
    table = profile.tables[0]
    assert table.table_name == "vitals"
    assert table.row_count == 3
    assert [c.inferred_type for c in table.columns] == [
        "text", "text", "date", "number", "text"
    ]
    assert table.columns[2].date_range["min"] == "2026-01-05"


def test_profile_payload_is_jsonable_and_path_free(tmp_path: Path) -> None:
    profile, _, _, _ = _admitted(
        Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path
    )
    payload = json.loads(json.dumps(profile.to_payload(), ensure_ascii=False))
    assert payload["profile_version"] == "1"
    assert str(tmp_path) not in json.dumps(payload)
    assert "/" not in payload["source_file"]
    assert payload["tables"][0]["columns"][2]["date_range"]["parsed_count"] == 3


def test_profile_rejects_path_like_source_file_and_bad_digest(tmp_path: Path) -> None:
    sheets = _mapping_tables()
    digest = "a" * 64
    with pytest.raises(StructureProfileError):
        build_listing_profile(PROJECT_ID, REVISION_ID, "../escape.csv", digest, sheets)
    # Digest shape is delegated to the primitives authority and fails closed
    # as a plain ValueError (StructureProfileError is also a ValueError).
    with pytest.raises(ValueError):
        build_listing_profile(
            PROJECT_ID, REVISION_ID, "ok.csv", "/Users/attacker/escape.csv", sheets
        )
    with pytest.raises(ValueError):
        build_listing_profile(PROJECT_ID, REVISION_ID, "ok.csv", "nothex", sheets)


def test_profile_rejects_duplicate_headers_and_misaligned_rows(tmp_path: Path) -> None:
    digest = "b" * 64
    with pytest.raises(StructureProfileError):
        build_listing_profile(
            PROJECT_ID, REVISION_ID, "ok.csv", digest,
            [{"table_name": "T", "headers": ["a", "a"], "rows": [{"a": 1}]}],
        )
    with pytest.raises(StructureProfileError):
        build_listing_profile(
            PROJECT_ID, REVISION_ID, "ok.csv", digest,
            [{"table_name": "T", "headers": ["a"], "rows": [{"a": 1}],
              "row_numbers": [2, 3]}],
        )
    with pytest.raises(StructureProfileError):
        build_listing_profile(
            PROJECT_ID, REVISION_ID, "ok.csv", digest,
            [{"table_name": "T", "headers": ["a", "b"], "rows": [{"a": 1, "b": 2}, "not-a-mapping"]}],
        )


# ---------------------------------------------------------------------------
# Source-cell locators
# ---------------------------------------------------------------------------

def test_locators_are_deterministic_and_match_source_cells(tmp_path: Path) -> None:
    profile, locators, snapshot, path = _admitted(
        Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path
    )
    assert snapshot.snapshot_id.startswith("snapc1_")
    assert len(locators) == 3 * 5
    first = locators[0]
    assert first.locator_id.startswith("srccell_")
    assert first.raw_value == "S001"
    assert first.row_index == 0 and first.row_number == 2
    assert first.column == "subject_id" and first.column_index == 0
    assert first.source_file == "admission-listing.csv"
    assert first.snapshot_id == snapshot.snapshot_id
    # Deterministic rebuild
    rebuilt = build_sheet_locators(
        PROJECT_ID, REVISION_ID, snapshot.snapshot_id, path.name,
        hashlib.sha256(path.read_bytes()).hexdigest(),
        _parse(path, path.read_bytes())[0],
    )
    assert [loc.locator_id for loc in rebuilt] == [loc.locator_id for loc in locators]
    # Cell-level spot check against the generated file content
    empty_value_locator = next(
        loc for loc in locators if loc.row_index == 1 and loc.column == "result_value"
    )
    assert empty_value_locator.raw_value == ""
    date_locator = next(
        loc for loc in locators if loc.row_index == 2 and loc.column == "record_date"
    )
    assert date_locator.raw_value == "2026-02-07" and date_locator.row_number == 4


def test_locator_rejects_supplied_id_that_does_not_match_identity(tmp_path: Path) -> None:
    digest = "c" * 64
    with pytest.raises(StructureProfileError):
        SourceCellLocator(
            project_id=PROJECT_ID,
            source_revision_id=REVISION_ID,
            snapshot_id="snapc1_x",
            source_file="ok.csv",
            source_file_digest=digest,
            table_name="T",
            row_index=0,
            row_number=2,
            column="a",
            column_index=0,
            raw_value="x",
            locator_id="srccell_forged",
        )


# ---------------------------------------------------------------------------
# Store-backed round trip
# ---------------------------------------------------------------------------

def test_full_admission_round_trip_through_store(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    profile, locators, snapshot, path = _admitted(store, tmp_path)
    # The authoritative snapshot identity verifies against its own content.
    assert snapshot.content_hash == snapshot.compute_hash()
    stored_snapshot = store.get_listing_snapshot(snapshot.snapshot_id)
    assert stored_snapshot.row_count == 3
    assert stored_snapshot.revision_id == REVISION_ID
    stored_revision = store.get_source_revision(REVISION_ID)
    assert stored_revision.content_hash  # identity carried from the authority

    resolved: ResolvedCell = resolve_locator_from_store(
        store, locators[7], expected_locator_id=locators[7].locator_id,
        source_bytes=path.read_bytes(),
    )
    assert resolved.raw_value == locators[7].raw_value
    assert resolved.table_name == "admission-listing"
    assert resolved.row_number == locators[7].row_number
    assert resolved.column == locators[7].column
    # Bounded neighbor context: one row before and after where available.
    assert len(resolved.context_before) == 1
    assert len(resolved.context_after) == 1
    assert resolved.context_before[0]["subject_id"] == "S001"
    assert resolved.context_after[0]["subject_id"] == "S001"

    # Every locator of the admission resolves to its exact original cell.
    content = store.load_listing_content(snapshot.snapshot_id)
    for locator in locators:
        cell = resolve_locator(locator, content)
        assert cell.raw_value == locator.raw_value
        assert cell.row_index == locator.row_index


def test_snapshot_id_is_content_deterministic_and_idempotent_in_store(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    _, _, snapshot, path = _admitted(store, tmp_path)
    sheets = _parse(path, path.read_bytes())
    table_name, headers, rows, _ = table_rows_from_sheet(sheets[0])
    rebuilt = build_table_snapshot(PROJECT_ID, REVISION_ID, "v1", table_name, headers, rows)
    assert rebuilt.snapshot_id == snapshot.snapshot_id
    assert rebuilt.content_hash == snapshot.content_hash
    replayed = store.add_listing_snapshot(rebuilt, canonical_listing_content(sheets))
    assert replayed.snapshot_id == snapshot.snapshot_id
    # Same id with different content fails closed.
    conflicting = ListingSnapshot.from_content(
        snapshot.snapshot_id, PROJECT_ID, REVISION_ID, "v1",
        [{"subject_id": "S999", "visit": "V1", "record_date": "2026-01-05",
          "result_value": "42", "unit": "U/L"}],
        structure=dict(rebuilt.structure),
    )
    from packages.medical_monitoring.domain.execution import IdempotencyConflictError

    with pytest.raises(IdempotencyConflictError):
        store.add_listing_snapshot(conflicting, {"admission-listing": [
            {"subject_id": "S999", "visit": "V1", "record_date": "2026-01-05",
             "result_value": "42", "unit": "U/L"},
        ]})


def test_multi_table_admission_resolves_per_table_snapshots(tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    import openpyxl

    workbook = openpyxl.Workbook()
    vitals = workbook.active
    vitals.title = "vitals"
    vitals.append(["subject_id", "record_date"])
    vitals.append(["S001", "2026-01-05"])
    vitals.append(["S002", "2026-01-06"])
    labs = workbook.create_sheet("labs")
    labs.append(["subject_id", "panel", "result_value"])
    labs.append(["S001", "CHEM", "13"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    content = buffer.getvalue()
    path = tmp_path / "multi-sheet-listing.xlsx"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    sheets = _parse(path, content)
    assert len(sheets) == 2

    revision = SourceRevision.from_bytes(
        "srcc1_multi_demo_0001", PROJECT_ID, "listing", "v1", content
    )
    profile = build_listing_profile(PROJECT_ID, revision.revision_id, path.name, digest, sheets)
    assert [t.table_name for t in profile.tables] == ["vitals", "labs"]

    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    store.create_project(PROJECT_ID, "C1 Profile Demo")
    store.add_source_revision(execution_source_revision(revision))
    snapshot_ids = {}
    for sheet in sheets:
        table_name, headers, rows, row_numbers = table_rows_from_sheet(sheet)
        snapshot = build_table_snapshot(
            PROJECT_ID, revision.revision_id, "v1", table_name, headers, rows
        )
        store.add_listing_snapshot(snapshot, canonical_listing_content([sheet]))
        snapshot_ids[table_name] = snapshot.snapshot_id
        for locator in build_table_locators(
            PROJECT_ID, revision.revision_id, snapshot.snapshot_id, path.name,
            digest, table_name, headers, rows, row_numbers,
        ):
            cell = resolve_locator_from_store(store, locator)
            assert cell.raw_value == locator.raw_value
    assert snapshot_ids["vitals"] != snapshot_ids["labs"]
    stored = store.get_listing_snapshot(snapshot_ids["labs"])
    assert stored.row_count == 1


def test_empty_table_yields_empty_snapshot_and_no_locators(tmp_path: Path) -> None:
    tables = [{"table_name": "screening", "headers": ["subject_id"], "rows": []}]
    profile = build_listing_profile(PROJECT_ID, REVISION_ID, "empty.csv", "d" * 64, tables)
    assert profile.tables[0].row_count == 0
    assert profile.tables[0].columns[0].inferred_type == "empty"
    snapshot = build_table_snapshot(
        PROJECT_ID, REVISION_ID, "v1", "screening", ["subject_id"], []
    )
    assert snapshot.row_count == 0
    locators = build_table_locators(
        PROJECT_ID, REVISION_ID, snapshot.snapshot_id, "empty.csv", "d" * 64,
        "screening", ["subject_id"], [],
    )
    assert locators == ()
    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    store.create_project(PROJECT_ID, "C1 Profile Demo")
    revision = SourceRevision.from_bytes(REVISION_ID, PROJECT_ID, "listing", "v1", b"empty-bytes")
    store.add_source_revision(execution_source_revision(revision))
    store.add_listing_snapshot(snapshot, canonical_listing_content(tables))
    assert store.load_listing_content(snapshot.snapshot_id) == {"screening": []}


# ---------------------------------------------------------------------------
# Fail-closed resolution
# ---------------------------------------------------------------------------

def test_resolution_fails_closed_on_tampered_content(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    _, locators, snapshot, _ = _admitted(store, tmp_path)
    content = store.load_listing_content(snapshot.snapshot_id)
    target = locators[0]
    tampered = [dict(row) for row in content["admission-listing"]]
    tampered[0]["subject_id"] = "SXXX"
    with pytest.raises(StructureProfileError):
        resolve_locator(target, {"admission-listing": tampered})


def test_resolution_fails_closed_on_missing_table_or_column(tmp_path: Path) -> None:
    _, locators, _, _ = _admitted(
        Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path
    )
    target = locators[0]
    with pytest.raises(StructureProfileError):
        resolve_locator(target, {"other-table": []})
    with pytest.raises(StructureProfileError):
        resolve_locator(target, {"admission-listing": []})


def test_resolution_fails_closed_on_wrong_source_bytes(tmp_path: Path) -> None:
    _, locators, _, _ = _admitted(
        Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path
    )
    with pytest.raises(StructureProfileError):
        resolve_locator(
            locators[0],
            canonical_listing_content(_mapping_tables()),
            source_bytes=b"tampered-bytes",
        )


def test_resolution_fails_closed_on_citation_id_mismatch(tmp_path: Path) -> None:
    _, locators, _, _ = _admitted(
        Store(tmp_path / "db.sqlite3", tmp_path / "artifacts"), tmp_path
    )
    with pytest.raises(StructureProfileError):
        resolve_locator(locators[0], canonical_listing_content(_mapping_tables()),
                        expected_locator_id="srccell_stale_citation")


def test_resolution_fails_closed_on_foreign_snapshot_binding(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite3", tmp_path / "artifacts")
    _, locators, _, _ = _admitted(store, tmp_path)
    foreign_revision = "srcc1_foreign_demo_0002"
    revision = SourceRevision.from_bytes(
        foreign_revision, PROJECT_ID, "listing", "v2", b"foreign-bytes"
    )
    store.add_source_revision(execution_source_revision(revision))
    foreign_snapshot = build_table_snapshot(
        PROJECT_ID, foreign_revision, "v2", "admission-listing",
        list(CSV_HEADERS), [
            {header: row for header, row in zip(CSV_HEADERS, values)}
            for values in CSV_ROWS
        ],
    )
    store.add_listing_snapshot(foreign_snapshot, canonical_listing_content(_mapping_tables()))
    # Locator binds the v1 snapshot id but the row cells still exist in the
    # v2 snapshot; resolution must verify the revision binding, not just data.
    rebound = SourceCellLocator(
        project_id=PROJECT_ID,
        source_revision_id=foreign_revision,
        snapshot_id=foreign_snapshot.snapshot_id,
        source_file=locators[0].source_file,
        source_file_digest=locators[0].source_file_digest,
        table_name="admission-listing",
        row_index=0,
        row_number=2,
        column="subject_id",
        column_index=0,
        raw_value="S001",
    )
    assert resolve_locator_from_store(store, rebound).raw_value == "S001"
    # A locator pointing at snapshot of another project fails closed.
    other_project = "proj_c1_other"
    store.create_project(other_project, "Other")
    other_revision = SourceRevision.from_bytes(
        "srcc1_other_demo_0003", other_project, "listing", "v1", b"other-bytes"
    )
    store.add_source_revision(execution_source_revision(other_revision))
    other_snapshot = build_table_snapshot(
        other_project, other_revision.revision_id, "v1", "admission-listing",
        list(CSV_HEADERS), [
            {header: row for header, row in zip(CSV_HEADERS, values)}
            for values in CSV_ROWS
        ],
    )
    store.add_listing_snapshot(other_snapshot, canonical_listing_content(_mapping_tables()))
    forged = SourceCellLocator(
        project_id=PROJECT_ID,
        source_revision_id=REVISION_ID,
        snapshot_id=other_snapshot.snapshot_id,
        source_file=locators[0].source_file,
        source_file_digest=locators[0].source_file_digest,
        table_name="admission-listing",
        row_index=0,
        row_number=2,
        column="subject_id",
        column_index=0,
        raw_value="S001",
    )
    with pytest.raises(StructureProfileError):
        resolve_locator_from_store(store, forged)


def test_row_numbers_default_to_header_plus_offset(tmp_path: Path) -> None:
    tables = [{"table_name": "T", "headers": ["a"], "rows": [{"a": "1"}, {"a": "2"}]}]
    locators = build_table_locators(
        PROJECT_ID, REVISION_ID, "snapc1_rows", "rows.csv", "e" * 64, "T", ["a"],
        [{"a": "1"}, {"a": "2"}],
    )
    assert [loc.row_number for loc in locators] == [2, 3]
    profile = build_listing_profile(PROJECT_ID, REVISION_ID, "rows.csv", "e" * 64, tables)
    assert profile.tables[0].first_row_number == 2
    assert profile.tables[0].last_row_number == 3


if __name__ == "__main__":
    import unittest

    unittest.main()
