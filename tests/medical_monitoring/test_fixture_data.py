"""B5 fixture-contract tests: external synthetic fixture loader behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from packages.medical_monitoring.projections.fixture_data import (
    ENV_FIXTURES_DIR,
    FIXTURE_SCHEMA_ID,
    FixtureDataError,
    fixtures_dir,
    load_r5_fixture,
    load_r7_setup_fixture,
    load_synthetic_run_fixture,
)


def test_default_fixture_dir_resolves_without_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(ENV_FIXTURES_DIR, raising=False)
    assert fixtures_dir() == Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "medical_monitoring"
    assert (fixtures_dir() / "r5_authority_fixture.json").is_file()


def test_load_r5_fixture_roundtrip_keeps_baseline_records() -> None:
    data = load_r5_fixture()
    counts = {key: len(data[key]) for key in (
        "sources", "sites", "subjects", "events", "visits", "risks", "histories", "flow_stages", "flow_paths",
    )}
    assert counts == {
        "sources": 4,
        "sites": 3,
        "subjects": 3,
        "events": 12,
        "visits": 6,
        "risks": 3,
        "histories": 1,
        "flow_stages": 7,
        "flow_paths": 3,
    }
    assert data["fixture_schema"] == FIXTURE_SCHEMA_ID


def test_load_r7_setup_fixture_roundtrip() -> None:
    data = load_r7_setup_fixture()
    assert len(data["snapshots"]) == 2
    assert len(data["baselines"]) == 4
    assert data["snapshots"][0]["snapshot_ref"] == "s7-snapshot-comparable-001"
    assert data["snapshots"][1]["snapshot_ref"] == "s7-snapshot-current-001"
    assert {
        row["site_ref"] for row in data["snapshots"][1]["rows"]
    } == {"s7-site-006", "s7-site-010"}
    assert data["snapshots"][1]["data_cutoff"] == "2026-08-28"


def test_load_synthetic_run_fixture_roundtrip() -> None:
    data = load_synthetic_run_fixture()
    assert data["run_id"] == "s7-run-current-001"
    assert data["mode"] == "daily"
    assert data["data_cutoff"] == "2026-08-28"
    assert data["source_revision_id"] == "synthetic-source-current"
    assert [item["work_unit_id"] for item in data["work_units"]] == ["s7-work-001", "s7-work-002"]


def test_missing_directory_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(tmp_path / "absent"))
    with pytest.raises(FixtureDataError):
        load_r5_fixture()
    with pytest.raises(FixtureDataError):
        load_r7_setup_fixture()
    with pytest.raises(FixtureDataError):
        load_synthetic_run_fixture()


def test_env_override_dir_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    override = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "medical_monitoring"
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    assert fixtures_dir() == override
    assert load_r5_fixture()["fixture_schema"] == FIXTURE_SCHEMA_ID


def _write_override_dir(tmp_path: Path, source_name: str) -> Path:
    override = tmp_path / "fixtures"
    override.mkdir()
    shutil.copy2(
        Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "medical_monitoring" / source_name,
        override / source_name,
    )
    return override


def test_unknown_top_level_key_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = _write_override_dir(tmp_path, "r5_authority_fixture.json")
    path = override / "r5_authority_fixture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["unexpected"] = []
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    with pytest.raises(FixtureDataError):
        load_r5_fixture()


def test_missing_required_key_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = _write_override_dir(tmp_path, "synthetic_run_fixture.json")
    path = override / "synthetic_run_fixture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["source_revision_id"]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    with pytest.raises(FixtureDataError):
        load_synthetic_run_fixture()


def test_wrong_schema_id_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = _write_override_dir(tmp_path, "r7_setup_fixture.json")
    path = override / "r7_setup_fixture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["fixture_schema"] = "some-other-schema"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    with pytest.raises(FixtureDataError):
        load_r7_setup_fixture()


def test_invalid_json_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "fixtures"
    override.mkdir()
    (override / "r5_authority_fixture.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    with pytest.raises(FixtureDataError):
        load_r5_fixture()


def test_env_change_invalidates_cached_parse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_FIXTURES_DIR, raising=False)
    baseline = load_synthetic_run_fixture()["run_id"]
    override = _write_override_dir(tmp_path, "synthetic_run_fixture.json")
    path = override / "synthetic_run_fixture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["run_id"] = "s7-run-override-001"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(override))
    assert load_synthetic_run_fixture()["run_id"] == "s7-run-override-001"
    monkeypatch.delenv(ENV_FIXTURES_DIR, raising=False)
    assert load_synthetic_run_fixture()["run_id"] == baseline
