"""Source-to-profile manifest reconciliation and fail-closed gate tests.

Synthetic admission records only: no real project, service or model is
invoked.  The matrix proves the mapping bridge refuses every unexplained
input (missing manifest, digest drift, hidden data dropped, emitted claims
without tables, tables without manifest backing) and that a complete,
explained record is bound into the harness input via ``input_completeness``.

The manifest payloads mirror the parse authority's
``WorkbookPhysicalManifest`` contract exactly.
"""

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from packages.medical_monitoring.admission import (
    DataAdmissionPipeline,
    MappingBridgeError,
    SOURCE_PROFILE_GATE_SCHEMA_VERSION,
    WORKBOOK_MANIFEST_SCHEMA_VERSION,
    WORKBOOK_PHYSICAL_EVIDENCE_VERSION,
    WorkbookManifestError,
    admission_record_to_harness_input,
    enforce_source_to_profile_gate,
    reconcile_source_to_profile,
    validate_workbook_manifest_bundle,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION,
)
from packages.medical_monitoring.admission.workbook_manifest import (
    SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
    manifest_unavailable_summary,
)
from packages.medical_monitoring.intelligence.primitives import content_hash

PROJECT_ID = "c3-source-reconciliation-demo"
ATTEMPT_ID = "stg-source-reconciliation"
DIGEST = hashlib.sha256(b"synthetic-listing-bytes").hexdigest()


_UNSET = object()


def _sheet(
    name: str,
    index: int,
    *,
    visibility: str = "visible",
    content_kind: str = "data",
    emitted: bool = True,
    reason: Any = _UNSET,
) -> dict[str, Any]:
    if reason is _UNSET:
        reason = None if emitted else "no_usable_headers"
    return {
        "sheet_index": index,
        "sheet_name": name,
        "visibility": visibility,
        "used_range": None if content_kind == "empty" else "A1:B3",
        "used_row_count": 0 if content_kind == "empty" else 3,
        "used_column_count": 0 if content_kind == "empty" else 2,
        "content_kind": content_kind,
        "emitted": emitted,
        "omission_reason": reason,
        "hidden_row_count": 0,
        "hidden_column_count": 0,
        "merged_region_count": 0,
        "named_table_count": 0,
        "formula_cell_count": 0,
        "uncached_formula_cell_count": None,
        "uncached_scan_truncated": False,
    }


def _file_entry(
    sheets: list[dict[str, Any]],
    *,
    source_file: str = "listing.xlsx",
    sha256: str = DIGEST,
    content_sha256: str | None = None,
    manifest_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "evidence_version": WORKBOOK_PHYSICAL_EVIDENCE_VERSION,
        "parser_version": "listing_file_parser_synthetic_test",
        "source_format": "xlsx",
        "content_sha256": content_sha256 if content_sha256 is not None else DIGEST,
        "sheet_count": len(sheets),
        "emitted_sheet_count": sum(1 for sheet in sheets if sheet["emitted"]),
        "sheets": sheets,
        "evidence_limitations": [],
    }
    manifest.update(manifest_overrides or {})
    return {
        "source_file": source_file,
        "source_file_sha256": sha256,
        "manifest": manifest,
    }


def _table(
    name: str = "生命体征",
    *,
    source_file: str = "listing.xlsx",
    row_count: int = 2,
) -> dict[str, Any]:
    return {
        "name": name,
        "source_file": source_file,
        "row_count": row_count,
        "column_count": 2,
        "columns": [
            {
                "name": "SUBJID",
                "source_label": "受试者编号(SUBJID)",
                "inferred_type": "text",
                "missing_count": 0,
                "distinct_count": row_count,
                "samples": [f"S{index:03d}" for index in range(1, row_count + 1)],
                "date_range": None,
                "suggested_roles": ["受试者标识"],
            },
            {
                "name": "SYSBP",
                "source_label": "收缩压(SYSBP)",
                "inferred_type": "number",
                "missing_count": 0,
                "distinct_count": row_count,
                "samples": ["120", "118"][:row_count],
                "date_range": None,
                "suggested_roles": [],
            },
        ],
        "needs_confirmation": 1,
    }


def _record(
    file_entries: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    *,
    files: list[dict[str, Any]] | None = None,
    stored_reconciliation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    files = files if files is not None else [
        {
            "path": entry["source_file"],
            "size": 128,
            "sha256": entry["source_file_sha256"],
        }
        for entry in file_entries
    ]
    bundle = {
        "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
        "files": file_entries,
    }
    technical: dict[str, Any] = {
        "manifest_hash": DIGEST[:16],
        "files": files,
        "revision_ids": ["srcc1_a" for _ in files],
        "snapshot_ids": [f"snapc1_{index}" for index, _ in enumerate(tables)],
        "locator_index_ids": [f"snapc1_{index}" for index, _ in enumerate(tables)],
        "profile_ids": ["strcprof_a" for _ in files],
    }
    if stored_reconciliation is None:
        stored_reconciliation = reconcile_source_to_profile(
            validate_workbook_manifest_bundle(bundle),
            technical_files=files,
            tables=tables,
        )
    technical["physical_manifest"] = bundle
    technical["source_profile_reconciliation"] = stored_reconciliation
    return {
        "attempt_id": ATTEMPT_ID,
        "project_id": PROJECT_ID,
        "state": "profile_ready",
        "tables": tables,
        "technical_details": technical,
    }


def _bridged(record: dict[str, Any]) -> dict[str, Any]:
    return admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=ATTEMPT_ID,
        record=record,
    ).field_profile


def _gate_error(record: dict[str, Any]) -> WorkbookManifestError:
    with pytest.raises(WorkbookManifestError) as exc_info:
        enforce_source_to_profile_gate(record)
    return exc_info.value


def _bridge_error(record: dict[str, Any]) -> MappingBridgeError:
    with pytest.raises(MappingBridgeError) as exc_info:
        _bridged(record)
    return exc_info.value


def _finding_codes(error: WorkbookManifestError) -> set[str]:
    return {item["code"] for item in error.findings}


def test_gate_passes_complete_record_and_binds_input_completeness() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet("空表", 2, content_kind="empty", emitted=False, reason="empty_sheet"),
    ])]
    record = _record(entries, [_table()])
    reconciliation = enforce_source_to_profile_gate(record)
    assert reconciliation["complete"] is True
    assert reconciliation["status"] == "complete"
    profile = _bridged(record)
    completeness = profile["input_completeness"]
    assert completeness["gate_schema_version"] == SOURCE_PROFILE_GATE_SCHEMA_VERSION
    assert completeness["manifest_schema_version"] == WORKBOOK_MANIFEST_SCHEMA_VERSION
    assert completeness["reconciliation"]["complete"] is True
    assert completeness["manifest_sha256"] == reconciliation["manifest_sha256"]
    # The completeness binding participates in the harness input hash.
    expected_input_sha256 = content_hash({
        "mapping_cohort_schema_version": MONITORING_C3_MAPPING_COHORT_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "attempt_id": ATTEMPT_ID,
        "sources": profile["source_bindings"],
        "table_bindings": profile["table_bindings"],
        "fields": profile["fields"],
        "input_completeness": completeness,
        # Relationship evidence sections are always part of the frozen input
        # digest; without a profiler they are explicitly empty.
        "relationship_profile": {},
        "relationships": [],
        "cross_table_relationships": [],
    })
    assert profile["input_sha256"] == expected_input_sha256


def test_gate_fails_closed_without_physical_manifest() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    record = _record(entries, [_table()])
    del record["technical_details"]["physical_manifest"]
    assert _bridge_error(record).code == "mapping_source_manifest_missing"

    record = _record(entries, [_table()])
    del record["technical_details"]["source_profile_reconciliation"]
    assert _bridge_error(record).code == "mapping_source_manifest_missing"

    record = _record(entries, [_table()])
    record["technical_details"]["physical_manifest"] = None
    record["technical_details"]["source_profile_reconciliation"] = (
        manifest_unavailable_summary()
    )
    assert _bridge_error(record).code == "mapping_source_manifest_missing"


def test_emitted_claim_without_table_never_auto_passes() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet("DroppedSheet", 2),
    ])]
    record = _record(entries, [_table()])
    error = _gate_error(record)
    assert error.code == "mapping_source_incomplete"
    assert "emitted_sheet_without_table" in _finding_codes(error)


def test_hidden_data_sheet_blocks_even_with_reason() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet(
            "历史备份",
            2,
            visibility="hidden",
            emitted=False,
            reason="legacy hidden export",
        ),
    ])]
    record = _record(entries, [_table()])
    error = _gate_error(record)
    assert error.code == "mapping_source_incomplete"
    assert "hidden_data_not_admitted" in _finding_codes(error)


def test_unknown_visibility_data_sheet_blocks() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet(
            "旧格式表",
            2,
            visibility="unknown",
            emitted=False,
            reason="no_usable_headers",
        ),
    ])]
    record = _record(entries, [_table()])
    error = _gate_error(record)
    assert "unknown_visibility_data_omission" in _finding_codes(error)


def test_explained_visible_data_exclusion_passes_and_is_surfaced() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet(
            "说明页",
            2,
            emitted=False,
            reason="cover notes sheet, not listing data",
        ),
    ])]
    record = _record(entries, [_table()])
    reconciliation = enforce_source_to_profile_gate(record)
    assert reconciliation["complete"] is True
    assert reconciliation["status"] == "explained_exclusions"
    codes = {item["code"] for item in reconciliation["findings"]}
    assert "explained_data_exclusion" in codes
    profile = _bridged(record)
    surfaced = {
        item["code"]
        for item in profile["input_completeness"]["reconciliation"]["findings"]
    }
    assert "explained_data_exclusion" in surfaced


def test_staged_digest_mismatch_blocks_the_gate() -> None:
    entries = [_file_entry(
        [_sheet("生命体征", 1)],
        sha256="0" * 64,
    )]
    record = _record(
        entries,
        [_table()],
        files=[{"path": "listing.xlsx", "size": 128, "sha256": DIGEST}],
    )
    error = _gate_error(record)
    assert error.code == "mapping_source_incomplete"
    assert "manifest_digest_mismatch" in _finding_codes(error)


def test_content_digest_not_binding_staged_bytes_blocks() -> None:
    entries = [_file_entry(
        [_sheet("生命体征", 1)],
        content_sha256="f" * 64,
    )]
    record = _record(
        entries,
        [_table()],
        files=[{"path": "listing.xlsx", "size": 128, "sha256": DIGEST}],
    )
    error = _gate_error(record)
    assert "manifest_digest_mismatch" in _finding_codes(error)


def test_table_without_emitted_sheet_blocks_the_gate() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    record = _record(entries, [_table(), _table("实验室检查")])
    error = _gate_error(record)
    assert error.code == "mapping_source_incomplete"
    assert "table_without_emitted_sheet" in _finding_codes(error)


def test_tampered_stored_reconciliation_fails_closed() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    tampered = dict(
        reconcile_source_to_profile(
            validate_workbook_manifest_bundle({
                "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
                "files": entries,
            }),
            technical_files=[{
                "path": "listing.xlsx", "size": 128, "sha256": DIGEST,
            }],
            tables=[_table()],
        )
    )
    tampered["manifest_sha256"] = "f" * 64
    record = _record(
        entries,
        [_table()],
        stored_reconciliation=tampered,
    )
    assert _gate_error(record).code == "mapping_source_manifest_invalid"


def test_invalid_manifest_schema_fails_closed() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    entries[0]["manifest"]["sheets"][0]["visibility"] = "archived"
    record = _record(
        entries,
        [_table()],
        # The stored summary cannot be derived from an invalid manifest.
        stored_reconciliation={
            "schema_version": SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
            "manifest_sha256": None,
        },
    )
    assert _gate_error(record).code == "mapping_source_manifest_invalid"
    assert _bridge_error(record).code == "mapping_source_manifest_invalid"


def test_unknown_sheet_fact_field_fails_schema() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    entries[0]["manifest"]["sheets"][0]["cell_widths"] = [12]
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_wrong_evidence_version_fails_schema() -> None:
    entries = [_file_entry(
        [_sheet("生命体征", 1)],
        manifest_overrides={"evidence_version": "workbook_physical_evidence_v0"},
    )]
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_emitted_count_mismatch_fails_schema() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    entries[0]["manifest"]["emitted_sheet_count"] = 3
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_sheet_count_mismatch_fails_schema() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    entries[0]["manifest"]["sheet_count"] = 3
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_sheet_order_gap_is_a_blocking_finding() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet("实验室检查", 3),
    ])]
    record = _record(entries, [_table(), _table("实验室检查")])
    error = _gate_error(record)
    assert error.code == "mapping_source_incomplete"
    assert "sheet_order_invalid" in _finding_codes(error)


def test_header_only_emitted_sheet_passes_with_zero_row_table() -> None:
    entries = [_file_entry([
        _sheet("未采集检查", 1, content_kind="header_only"),
    ])]
    record = _record(entries, [_table("未采集检查", row_count=0)])
    reconciliation = enforce_source_to_profile_gate(record)
    assert reconciliation["complete"] is True
    codes = {item["code"] for item in reconciliation["findings"]}
    assert "profiled_header_only_sheet" in codes


def test_header_only_sheet_with_data_rows_blocks() -> None:
    entries = [_file_entry([
        _sheet("未采集检查", 1, content_kind="header_only"),
    ])]
    record = _record(entries, [_table("未采集检查", row_count=4)])
    error = _gate_error(record)
    assert "header_only_row_count_conflict" in _finding_codes(error)


def test_empty_sheet_matched_to_table_blocks() -> None:
    entries = [_file_entry([_sheet("生命体征", 1, content_kind="empty")])]
    record = _record(entries, [_table("生命体征")])
    error = _gate_error(record)
    assert "empty_sheet_matched_to_table" in _finding_codes(error)


def test_unemitted_sheet_without_reason_fails_schema() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1),
        _sheet("空表", 2, content_kind="empty", emitted=False, reason=None),
    ])]
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_emitted_sheet_with_reason_fails_schema() -> None:
    entries = [_file_entry([
        _sheet("生命体征", 1, reason="should not be here"),
    ])]
    with pytest.raises(WorkbookManifestError) as exc_info:
        validate_workbook_manifest_bundle({
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": entries,
        })
    assert exc_info.value.code == "manifest_schema_invalid"


def test_profiled_hidden_sheet_is_surfaced_as_information() -> None:
    entries = [_file_entry([
        _sheet("历史备份", 1, visibility="hidden"),
    ])]
    record = _record(entries, [_table("历史备份")])
    reconciliation = enforce_source_to_profile_gate(record)
    assert reconciliation["complete"] is True
    codes = {item["code"] for item in reconciliation["findings"]}
    assert "profiled_hidden_sheet" in codes
    summary = reconciliation["files"][0]
    assert summary["profiled_hidden_sheets"] == 1


def test_staged_file_without_manifest_entry_blocks() -> None:
    entries = [_file_entry([_sheet("生命体征", 1)])]
    record = _record(
        entries,
        [_table()],
        files=[
            {"path": "listing.xlsx", "size": 128, "sha256": DIGEST},
            {"path": "other.xlsx", "size": 128, "sha256": DIGEST},
        ],
    )
    error = _gate_error(record)
    assert "staged_file_without_manifest" in _finding_codes(error)


# ---------------------------------------------------------------------------
# Pipeline integration (synthetic workbooks only)
# ---------------------------------------------------------------------------

def _workbook_bytes(include_hidden_data: bool = False) -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    import io

    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = "生命体征"
    first.append(["受试者编号(SUBJID)", "收缩压(SYSBP)"])
    first.append(["S001", 120])
    second = workbook.create_sheet("实验室检查")
    second.append(["受试者编号(SUBJID)", "检查结果(LBORRES)"])
    second.append(["S001", "正常"])
    if include_hidden_data:
        hidden = workbook.create_sheet("历史备份")
        hidden.append(["受试者编号(SUBJID)", "备注"])
        hidden.append(["S001", "复查"])
        hidden.sheet_state = "hidden"
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _admit(tmp_path, *, provider=None) -> dict[str, Any]:
    from services.api.app.listing_file_parser import parse_listing_file

    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.xlsx").write_bytes(_workbook_bytes())
    workspace = tmp_path / "runtime" / PROJECT_ID
    pipeline = DataAdmissionPipeline(
        parse_listing_file,
        manifest_provider=provider,
    )
    return pipeline.create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )


def test_pipeline_persists_reconciled_manifest_in_technical_details(tmp_path) -> None:
    result = _admit(tmp_path)
    technical = result["technical_details"]
    bundle = technical["physical_manifest"]
    assert bundle["schema_version"] == WORKBOOK_MANIFEST_SCHEMA_VERSION
    entry = bundle["files"][0]
    assert entry["source_file"] == "listing.xlsx"
    manifest = entry["manifest"]
    assert manifest["evidence_version"] == WORKBOOK_PHYSICAL_EVIDENCE_VERSION
    assert manifest["sheet_count"] == 2
    assert manifest["emitted_sheet_count"] == 2
    assert {sheet["sheet_name"] for sheet in manifest["sheets"]} == {
        "生命体征",
        "实验室检查",
    }
    # The manifest content digest binds the staged file bytes.
    staged = {item["path"]: item["sha256"] for item in technical["files"]}
    assert entry["source_file_sha256"] == staged["listing.xlsx"]
    assert manifest["content_sha256"] == staged["listing.xlsx"]
    reconciliation = technical["source_profile_reconciliation"]
    assert reconciliation["schema_version"] == SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION
    assert reconciliation["complete"] is True
    assert reconciliation["manifest_sha256"]


def test_pipeline_manifest_tracks_hidden_data_sheet(tmp_path) -> None:
    from services.api.app.listing_file_parser import parse_listing_file

    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.xlsx").write_bytes(_workbook_bytes(include_hidden_data=True))
    workspace = tmp_path / "runtime" / PROJECT_ID
    result = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )
    manifest = result["technical_details"]["physical_manifest"]["files"][0]["manifest"]
    assert manifest["sheet_count"] == 3
    hidden = [
        sheet for sheet in manifest["sheets"] if sheet["visibility"] == "hidden"
    ]
    assert [sheet["sheet_name"] for sheet in hidden] == ["历史备份"]
    assert all(sheet["emitted"] for sheet in hidden)
    reconciliation = result["technical_details"]["source_profile_reconciliation"]
    assert reconciliation["complete"] is True
    assert reconciliation["files"][0]["profiled_hidden_sheets"] == 1


def test_pipeline_without_manifest_records_manifest_unavailable(tmp_path) -> None:
    result = _admit(tmp_path, provider=lambda filename, content: None)
    technical = result["technical_details"]
    assert technical["physical_manifest"] is None
    reconciliation = technical["source_profile_reconciliation"]
    assert reconciliation["status"] == "manifest_unavailable"
    assert reconciliation["complete"] is False
    with pytest.raises(MappingBridgeError) as exc_info:
        admission_record_to_harness_input(
            project_id=PROJECT_ID,
            attempt_id=str(result["attempt_id"]),
            record={
                "attempt_id": str(result["attempt_id"]),
                "project_id": PROJECT_ID,
                "tables": result["tables"],
                "technical_details": technical,
            },
        )
    assert exc_info.value.code == "mapping_source_manifest_missing"


@pytest.mark.parametrize(
    "limitation",
    [
        "xlsx_physical_evidence_capture_failed",
        "xlsx_sheet_evidence_degraded",
    ],
)
def test_gate_blocks_degraded_xlsx_physical_evidence(limitation: str) -> None:
    record = _record(
        [_file_entry([_sheet("生命体征", 1)])],
        [_table("生命体征")],
    )
    record["technical_details"]["physical_manifest"]["files"][0][
        "manifest"
    ]["evidence_limitations"] = [limitation]
    record["technical_details"]["source_profile_reconciliation"] = (
        reconcile_source_to_profile(
            record["technical_details"]["physical_manifest"],
            technical_files=record["technical_details"]["files"],
            tables=record["tables"],
        )
    )

    with pytest.raises(WorkbookManifestError) as exc_info:
        enforce_source_to_profile_gate(record)

    assert exc_info.value.code == "mapping_source_incomplete"
    assert limitation.split("xlsx_")[-1] in str(exc_info.value.findings)


def test_pipeline_rejects_failing_manifest_provider(tmp_path) -> None:
    def broken_provider(filename: str, content: bytes) -> dict[str, Any]:
        raise ValueError("manifest builder exploded")

    with pytest.raises(Exception) as exc_info:
        _admit(tmp_path, provider=broken_provider)
    assert getattr(exc_info.value, "code", "") == "admission_profile_unavailable"


def test_pipeline_rejects_schema_invalid_manifest(tmp_path) -> None:
    def invalid_provider(filename: str, content: bytes) -> dict[str, Any]:
        return {"evidence_version": "unknown-evidence", "sheets": []}

    with pytest.raises(Exception) as exc_info:
        _admit(tmp_path, provider=invalid_provider)
    assert getattr(exc_info.value, "code", "") == "admission_profile_unavailable"
