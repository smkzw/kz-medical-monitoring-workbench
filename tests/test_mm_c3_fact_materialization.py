"""Focused C3 deterministic fact materialization tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.fact_materialization import (
    FACT_MATERIALIZATION_KIND,
    FACT_SET_KIND,
    FactMaterializationError,
    FactMaterializationService,
    load_fact_set,
    locator_from_fact,
)
from packages.medical_monitoring.admission.pipeline import (
    ADMISSION_RECORD_KIND,
    DataAdmissionPipeline,
)
from packages.medical_monitoring.domain.execution import SnapshotAcceptanceState
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.intelligence.structure_profile import (
    SourceCellLocator,
    resolve_locator_from_store,
)
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
)

PROJECT_ID = "c3-fact-project"


def _parser(_name: str, _content: bytes):
    return [{
        "table_name": "AE",
        "headers": ["SUBJID", "VISIT", "AESTDAT", "AETERM", "IGNORED"],
        "rows": [
            {
                "SUBJID": "S001",
                "VISIT": "V1",
                "AESTDAT": "2026-01-05",
                "AETERM": " Headache ",
                "IGNORED": "export-only",
            },
            {
                "SUBJID": "S002",
                "VISIT": "V2",
                "AESTDAT": "2026-02",
                "AETERM": "",
                "IGNORED": "export-only",
            },
        ],
        "row_numbers": [4, 6],
    }]


def _mapping(attempt_id: str):
    fields = []
    for source_field, role, kind in (
        ("SUBJID", "subject_identifier", "source_collected"),
        ("VISIT", "visit_name", "source_collected"),
        ("AESTDAT", "ae_start_date", "source_collected"),
        ("AETERM", "ae_reported_term", "source_collected"),
        ("IGNORED", "clinical.source_other", "unmapped"),
    ):
        fields.append({
            "domain": "AE",
            "source_field": source_field,
            "recommended_role": role,
            "field_kind": kind,
        })
    revision = {
        "mapping_revision": "monmaprev_test",
        "project_id": PROJECT_ID,
        "batch_id": attempt_id,
        "fields": fields,
    }
    return SimpleNamespace(
        find_draft_for_batch=lambda project_id, batch_id: {
            "project_id": project_id,
            "batch_id": batch_id,
            "status": "confirmed",
            "confirmed_revision_id": "monmaprev_test",
        },
        get_revision=lambda _project_id, _revision_id: revision,
    )


def _admit(tmp_path: Path, parser=_parser):
    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.csv").write_text("synthetic", encoding="utf-8")
    workspace = tmp_path / "workspace"
    result = DataAdmissionPipeline(parser).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )
    return workspace, result["attempt_id"]


def _store(workspace: Path) -> Store:
    return Store(
        workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME,
    )


def test_materializes_idempotent_row_facts_with_exact_cell_locators(tmp_path: Path) -> None:
    workspace, attempt_id = _admit(tmp_path)
    service = FactMaterializationService(_mapping(attempt_id))

    first = service.materialize(
        project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
    )
    second = service.materialize(
        project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
    )

    assert first == second
    assert first["facts_generated"] is True
    assert first["summary"] == {
        "tables": 1,
        "rows": 2,
        "values": 8,
        "source_values_verified": 8,
    }
    store = _store(workspace)
    try:
        summary = store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id)
        assert summary is not None and summary[0] == 1
        assert summary[1]["summary"]["unmapped_values_skipped"] == 2
        assert summary[1]["summary"]["derived_values_skipped"] == 0
        fact_set_id = summary[1]["fact_set_ids"][0]
        fact_set = store.get_domain_object(FACT_SET_KIND, fact_set_id)
        assert fact_set is not None and fact_set[0] == 1
        fact_payload = load_fact_set(workspace, fact_set[1])
        facts = fact_payload["row_facts"]
        assert [fact["row_number"] for fact in facts] == [4, 6]
        date_value = next(
            value for value in facts[0]["values"] if value["source_field"] == "AESTDAT"
        )
        locator = locator_from_fact(fact_payload, facts[0], date_value)
        resolved = resolve_locator_from_store(
            store, locator, expected_locator_id=locator.locator_id
        )
        assert resolved.raw_value == "2026-01-05"
        snapshot_id = fact_payload["snapshot_id"]
        assert store.get_acceptance(snapshot_id).state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
    finally:
        store.close()


def test_rejects_incomplete_mapping_without_creating_ready_summary(tmp_path: Path) -> None:
    workspace, attempt_id = _admit(tmp_path)
    repository = _mapping(attempt_id)
    revision = repository.get_revision(PROJECT_ID, "monmaprev_test")
    revision["fields"] = revision["fields"][:-1]
    service = FactMaterializationService(repository)

    with pytest.raises(FactMaterializationError) as exc:
        service.materialize(
            project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
        )
    assert exc.value.code == "facts_mapping_incomplete"
    store = _store(workspace)
    try:
        assert store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id) is None
    finally:
        store.close()


def test_later_table_failure_does_not_advance_earlier_snapshot(tmp_path: Path) -> None:
    def two_tables(name: str, content: bytes):
        return [
            *_parser(name, content),
            {
                "table_name": "CM",
                "headers": ["SUBJID", "CMTRT"],
                "rows": [{"SUBJID": "S001", "CMTRT": "Medicine"}],
                "row_numbers": [3],
            },
        ]

    workspace, attempt_id = _admit(tmp_path, two_tables)
    service = FactMaterializationService(_mapping(attempt_id))

    with pytest.raises(FactMaterializationError) as exc:
        service.materialize(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert exc.value.code == "facts_mapping_incomplete"

    store = _store(workspace)
    try:
        record = store.get_domain_object(ADMISSION_RECORD_KIND, attempt_id)
        assert record is not None
        for snapshot_id in record[1]["technical_details"]["snapshot_ids"]:
            assert (
                store.get_acceptance(snapshot_id).state
                != SnapshotAcceptanceState.BASELINE_ELIGIBLE
            )
        assert store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id) is None
    finally:
        store.close()


def test_status_is_project_scoped_and_reports_not_generated(tmp_path: Path) -> None:
    workspace, attempt_id = _admit(tmp_path)
    service = FactMaterializationService(_mapping(attempt_id))
    assert service.status(
        project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
    ) == {
        "state": "not_generated",
        "facts_generated": False,
    }
    with pytest.raises(FactMaterializationError) as exc:
        service.status(
            project_id="other-project", attempt_id=attempt_id, workspace_dir=workspace
        )
    assert exc.value.code == "facts_admission_not_found"


def test_ready_status_rejects_a_changed_fact_artifact(tmp_path: Path) -> None:
    workspace, attempt_id = _admit(tmp_path)
    service = FactMaterializationService(_mapping(attempt_id))
    service.materialize(
        project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
    )
    artifact = next(
        (workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME / "canonical_fact_sets").glob("*.json.gz")
    )
    artifact.write_bytes(artifact.read_bytes() + b"changed")
    with pytest.raises(FactMaterializationError) as exc:
        service.status(
            project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
        )
    assert exc.value.code == "facts_snapshot_digest_mismatch"


def test_ready_status_rejects_summary_counts_that_do_not_match_fact_sets(
    tmp_path: Path,
) -> None:
    workspace, attempt_id = _admit(tmp_path)
    service = FactMaterializationService(_mapping(attempt_id))
    service.materialize(
        project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
    )
    store = _store(workspace)
    try:
        persisted = store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id)
        assert persisted is not None
        payload = dict(persisted[1])
        payload["summary"] = {**payload["summary"], "values": 9}
        store.put_domain_object(FACT_MATERIALIZATION_KIND, attempt_id, payload)
    finally:
        store.close()

    with pytest.raises(FactMaterializationError) as exc:
        service.status(
            project_id=PROJECT_ID, attempt_id=attempt_id, workspace_dir=workspace
        )
    assert exc.value.code == "facts_snapshot_digest_mismatch"
