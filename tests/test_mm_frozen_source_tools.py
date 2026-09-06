"""Frozen evidence tools exercise actual admission stores, never real projects."""
from pathlib import Path

import pytest

from packages.medical_monitoring.admission.pipeline import DataAdmissionPipeline, LOCATOR_INDEX_KIND
from packages.medical_monitoring.admission.source_tools import FrozenListingEvidenceTools, SourceToolError
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime.runtime_progress import RUNTIME_DIR_NAME, RUNTIME_DB_NAME, ARTIFACT_DIR_NAME


@pytest.fixture
def evidence(tmp_path: Path):
    source = tmp_path / "synthetic-source"
    source.mkdir()
    (source / "listing.csv").write_text("synthetic fixture")
    rows = [{"A": index, "B": [None, 0, -1, "<5", "mg/L"][index % 5]} for index in range(45)]
    def parser(*_):
        return [{"table_name": "Observations", "headers": ["A", "B"],
                 "rows": rows, "row_numbers": list(range(4, 49))}]
    workspace = tmp_path / "workspace"
    record = DataAdmissionPipeline(parser).create_attempt(
        project_id="tool-study", source_dir=source, workspace_dir=workspace)
    technical = record["technical_details"]
    binding = {"table_binding_id": "table-one", "domain": "Observations",
               "snapshot_id": technical["snapshot_ids"][0],
               "source_revision_id": technical["revision_ids"][0], "sheet_index": 1}
    profile = {"project_id": "tool-study", "table_bindings": [binding],
               "source_bindings": [{"source_entry_id": binding["source_revision_id"],
                                    "source_content_sha256": technical["files"][0]["sha256"]}]}
    store = Store(workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
                  workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME)
    try:
        yield FrozenListingEvidenceTools(store, project_id="tool-study", input_revision="f" * 64,
                                         field_profile=profile), store, binding
    finally:
        store.close()


def test_region_reads_preserve_physical_rows_and_zero_missing_inequality(evidence):
    tools, _, _ = evidence
    result = tools.read_source_region(table_binding_id="table-one", row_count=5, column_indexes=[1])
    cells = result["data"]["cells"]
    assert [cell["raw_value"] for cell in cells] == [None, 0, -1, "<5", "mg/L"]
    assert [cell["row_number"] for cell in cells] == [4, 5, 6, 7, 8]
    assert len({cell["locator_id"] for cell in cells}) == 5
    assert result["data"]["coverage"] == "partial"
    assert result["data"]["next_row_start"] == 5
    assert result["input_revision_sha256"] == "f" * 64


def test_region_pages_do_not_claim_whole_table_read(evidence):
    tools, _, _ = evidence
    first = tools.read_source_region(table_binding_id="table-one", row_count=40, column_indexes=[0, 1])
    second = tools.read_source_region(table_binding_id="table-one", row_start=40, row_count=40, column_indexes=[0, 1])
    assert len(first["data"]["cells"]) + len(second["data"]["cells"]) == 90
    assert second["data"]["next_row_start"] is None
    assert second["data"]["coverage"] == "partial"


def test_full_distribution_has_pagination_and_type_preservation(evidence):
    tools, _, _ = evidence
    result = tools.get_column_profile(table_binding_id="table-one", column_index=1, limit=2)
    assert result["data"]["unique_value_count"] == 5
    assert result["data"]["distribution_scanned_rows"] == 45
    assert result["data"]["next_offset"] == 2
    assert result["data"]["coverage"] == "partial"
    complete = tools.get_column_profile(table_binding_id="table-one", column_index=1)
    assert complete["data"]["coverage"] == "complete"
    assert complete["data"]["coverage_scope"] == "column_value_distribution"
    assert all(item["count"] == 9 for item in complete["data"]["values"])


def test_changed_content_cannot_be_read_as_frozen(evidence):
    tools, store, binding = evidence
    snapshot = store.get_listing_snapshot(binding["snapshot_id"])
    store._content_path(snapshot.content_hash).write_text('{"Observations": []}')
    with pytest.raises(SourceToolError, match="source_content_changed"):
        tools.read_source_region(table_binding_id="table-one", column_indexes=[0])


def test_wrong_cell_locator_cannot_be_cited(evidence):
    tools, store, binding = evidence
    index = dict(store.get_domain_object(LOCATOR_INDEX_KIND, binding["snapshot_id"])[1])
    index["locator_ids"] = list(index["locator_ids"])
    index["locator_ids"][0] = "srccell_wrong"
    store.put_domain_object(LOCATOR_INDEX_KIND, binding["snapshot_id"], index)
    with pytest.raises(ValueError, match="does not match"):
        tools.read_source_region(table_binding_id="table-one", column_indexes=[0])


@pytest.mark.parametrize("columns", [[True], [-1], [2], [0, 0], [{}]])
def test_invalid_physical_column_selection_is_rejected(evidence, columns):
    tools, _, _ = evidence
    with pytest.raises(SourceToolError):
        tools.read_source_region(table_binding_id="table-one", column_indexes=columns)


def test_unknown_table_never_uses_a_similar_name(evidence):
    tools, _, _ = evidence
    with pytest.raises(SourceToolError, match="source_table_not_bound"):
        tools.read_source_region(table_binding_id="table-on", column_indexes=[0])


def test_exact_value_sampling_reads_nonadjacent_context_without_type_coercion(evidence):
    reader, _, _ = evidence
    from services.api.app.monitoring_evidence_toolset import MonitoringEvidenceToolset
    toolkit = MonitoringEvidenceToolset(reader)
    args = dict(table_binding_id="table-one", filter_column_index=1,
                raw_value=0, column_indexes=[0, 1], limit=2)
    first = toolkit.execute("sample_rows", args)["data"]
    assert first["matching_row_count"] == 9
    assert first["next_offset"] == 2
    assert [c["row_number"] for c in first["cells"]] == [5, 5, 10, 10]
    last = toolkit.execute("sample_rows", {**args, "offset": 8})["data"]
    assert last["next_offset"] is None
    assert last["coverage"] == "partial"
    for value in (False, "0"):
        absent = toolkit.execute("sample_rows", {**args, "raw_value": value})["data"]
        assert absent["matching_row_count"] == 0
        assert absent["absence_claim_supported"] is False


def test_toolset_marks_failed_reads_unavailable_not_empty_evidence(evidence):
    from services.api.app.monitoring_evidence_toolset import MonitoringEvidenceToolset
    reader, _, _ = evidence
    toolkit = MonitoringEvidenceToolset(reader)
    result = toolkit.execute("read_source_region", {"table_binding_id": "missing", "column_indexes": [0]})
    assert result["status"] == "unavailable"
    assert result["coverage"] == "none"
    assert result["absence_claim_supported"] is False
    assert result["failure_code"] == "source_table_not_bound"
    with pytest.raises(SourceToolError, match="arguments_invalid"):
        toolkit.execute("read_source_region", {"table_binding_id": "table-one", "column_indexes": [0], "path": "/tmp/other"})
