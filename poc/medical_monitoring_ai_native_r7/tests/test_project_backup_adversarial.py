"""Independent stdlib oracle and adversarial matrix for R7 Slice-09A.

The oracle in this module reads the frozen input workspace with sqlite3,
json, hashlib and zipfile only.  It intentionally does not call project
backup helpers, manifest builders, DTO projections, or product code to derive
expected values.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import sqlite3
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import pytest

from mm_r1.domain import (
    AnalysisState,
    ArtifactEnvelope,
    ExecutionBasis,
    MonitoringRun,
    NodeType,
    RunMode,
    SourceRevision,
)
from mm_r1.store import Store
from mm_r7 import project_backup as pb
from mm_r7.maintenance_gate import ProjectBusyError, ProjectMaintenanceGate
from mm_r7.profile_store import ProfileStore
from mm_r7.run_binding import RunBindingStore


PROJECT_ID = "project-a"
PROFILE_DB = "execution_profiles.sqlite3"
BINDING_DB = "monitoring_run_bindings.sqlite3"
LAUNCH_DB = "launch_registry.sqlite3"
RISK_DB = "risk_rules.sqlite3"
RUNTIME_DB = "runtime/monitoring_runtime.sqlite3"
ARTIFACT_PREFIX = "runtime/artifacts/"
ROOT_DB_NAMES = (PROFILE_DB, BINDING_DB, LAUNCH_DB, RISK_DB)


# ---------------------------------------------------------------------------
# Independent input-side oracle
# ---------------------------------------------------------------------------


def _oracle_json_bytes(value: Any) -> bytes:
    """Canonical JSON implemented independently from mm_r7.project_backup."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _oracle_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _oracle_tables(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _oracle_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    escaped = table.replace('"', '""')
    return {
        str(row[1])
        for row in conn.execute(f'PRAGMA table_info("{escaped}")').fetchall()
    }


def _oracle_schema(conn: sqlite3.Connection, relative: str) -> str:
    name = Path(relative).name
    if name == PROFILE_DB:
        return str(
            conn.execute(
                "SELECT value FROM profile_store_meta WHERE key='schema_version'"
            ).fetchone()[0]
        )
    if name == BINDING_DB:
        return "r7-slice01-run-binding-v1"
    if name == LAUNCH_DB:
        return str(
            conn.execute(
                "SELECT value FROM r7_launch_registry_meta WHERE key='schema_version'"
            ).fetchone()[0]
        )
    if name == RISK_DB:
        return "mm-r7-risk-rule-v1"
    if name == Path(RUNTIME_DB).name:
        return str(
            conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
        )
    raise AssertionError(f"unexpected sqlite member: {relative}")


def _oracle_project_ids(conn: sqlite3.Connection) -> set[str]:
    project_ids: set[str] = set()
    for table in sorted(_oracle_tables(conn)):
        if "project_id" not in _oracle_columns(conn, table):
            continue
        escaped = table.replace('"', '""')
        project_ids.update(
            str(row[0])
            for row in conn.execute(
                f'SELECT DISTINCT "project_id" FROM "{escaped}"'
            ).fetchall()
        )
    return project_ids


def _oracle_workspace_member_names(workspace: Path) -> list[str]:
    names = [name for name in ROOT_DB_NAMES if (workspace / name).is_file()]
    if (workspace / RUNTIME_DB).is_file():
        names.append(RUNTIME_DB)
    artifact_dir = workspace / "runtime" / "artifacts"
    if artifact_dir.is_dir():
        names.extend(
            f"{ARTIFACT_PREFIX}{child.name}"
            for child in artifact_dir.iterdir()
            if child.is_file() and child.suffix == ".json"
        )
    return sorted(names, key=lambda value: value.encode("utf-8"))


def _oracle_workspace_state(workspace: Path, project_id: str = PROJECT_ID) -> dict[str, Any]:
    """Rebuild the semantic state from raw sqlite/filesystem input.

    This is intentionally a separate implementation from the product's
    workspace summarizer.  It also closes every read connection before
    returning, so callers can use it as the reopen/reconciliation oracle.
    """

    member_names = _oracle_workspace_member_names(workspace)
    member_hashes = {
        relative: _oracle_sha256((workspace / relative).read_bytes())
        for relative in member_names
    }
    schema_versions: dict[str, str] = {}
    project_ids: set[str] = set()
    project_name = project_id
    runs: list[dict[str, str]] = []
    run_states: list[str] = []
    mode_counts: dict[str, int] = {}
    basis_counts: dict[str, int] = {}
    artifact_hashes: set[str] = set()
    publications = 0
    continuity_plans = 0
    continuity_items = 0
    risk_rules = 0
    launch_active = False
    node_attempts_running = 0
    listing_snapshots = 0

    sqlite_members = [relative for relative in member_names if not relative.endswith(".json")]
    for relative in sqlite_members:
        path = workspace / relative
        conn = sqlite3.connect(str(path))
        try:
            conn.row_factory = sqlite3.Row
            schema_versions[relative] = _oracle_schema(conn, relative)
            project_ids.update(_oracle_project_ids(conn))
            tables = _oracle_tables(conn)
            name = path.name
            if name == Path(RUNTIME_DB).name:
                if "projects" in tables:
                    for row in conn.execute(
                        "SELECT project_id, name, is_synthetic FROM projects ORDER BY project_id"
                    ).fetchall():
                        pid = str(row["project_id"])
                        project_ids.add(pid)
                        if pid == project_id and row["name"]:
                            project_name = str(row["name"])
                        assert bool(row["is_synthetic"]), pid
                if "monitoring_runs" in tables:
                    for row in conn.execute(
                        "SELECT project_id, mode, execution_basis, analysis_state, data_cutoff "
                        "FROM monitoring_runs ORDER BY run_id"
                    ).fetchall():
                        project_ids.add(str(row["project_id"]))
                        mode = str(row["mode"])
                        basis = str(row["execution_basis"])
                        state = str(row["analysis_state"])
                        mode_counts[mode] = mode_counts.get(mode, 0) + 1
                        basis_counts[basis] = basis_counts.get(basis, 0) + 1
                        run_states.append(state)
                        runs.append(
                            {
                                "analysis_state": state,
                                "data_cutoff": str(row["data_cutoff"]),
                                "execution_basis": basis,
                                "mode": mode,
                            }
                        )
                if "node_attempts" in tables:
                    node_attempts_running = int(
                        conn.execute(
                            "SELECT COUNT(*) FROM node_attempts WHERE status='running'"
                        ).fetchone()[0]
                    )
                for table in ("artifacts", "listing_snapshots"):
                    if table in tables:
                        if "content_hash" not in _oracle_columns(conn, table):
                            raise AssertionError(f"{table} lacks content_hash")
                        artifact_hashes.update(
                            str(row[0])
                            for row in conn.execute(
                                f"SELECT content_hash FROM {table}"
                            ).fetchall()
                        )
                if "listing_snapshots" in tables:
                    listing_snapshots = int(
                        conn.execute("SELECT COUNT(*) FROM listing_snapshots").fetchone()[0]
                    )
            elif name == LAUNCH_DB:
                if "r7_launch_registry" in tables:
                    columns = _oracle_columns(conn, "r7_launch_registry")
                    if "run_state" in columns:
                        launch_states = [
                            str(row[0])
                            for row in conn.execute(
                                "SELECT run_state FROM r7_launch_registry ORDER BY sequence"
                            ).fetchall()
                        ]
                        launch_active = any(
                            state in {"waiting_start", "running", "stopping"}
                            for state in launch_states
                        )
                if "r7_result_publications" in tables:
                    publications = int(
                        conn.execute("SELECT COUNT(*) FROM r7_result_publications").fetchone()[0]
                    )
                if "r7_continuity_plans" in tables:
                    continuity_plans = int(
                        conn.execute("SELECT COUNT(*) FROM r7_continuity_plans").fetchone()[0]
                    )
                if "r7_continuity_items" in tables:
                    continuity_items = int(
                        conn.execute("SELECT COUNT(*) FROM r7_continuity_items").fetchone()[0]
                    )
            elif name == RISK_DB:
                if "r7_risk_rule_revisions" in tables:
                    risk_rules = int(
                        conn.execute(
                            "SELECT COUNT(*) FROM r7_risk_rule_revisions"
                        ).fetchone()[0]
                    )
        finally:
            conn.close()

    assert not project_ids or project_ids == {project_id}, sorted(project_ids)
    cutoffs = sorted({item["data_cutoff"] for item in runs if item["data_cutoff"]})
    backup_cutoff = cutoffs[-1] if cutoffs else "未建立监查运行"
    unfinished_states = [
        item["analysis_state"] for item in runs if item["analysis_state"] != "complete"
    ]
    unfinished = bool(unfinished_states or launch_active or node_attempts_running)
    counts = {
        "runs": len(runs),
        "completed_runs": sum(1 for item in runs if item["analysis_state"] == "complete"),
        "unfinished_runs": len(unfinished_states),
        "publications": publications,
        "continuity_plans": continuity_plans,
        "continuity_items": continuity_items,
        "risk_rules": risk_rules,
        "listing_snapshots": listing_snapshots,
        "artifacts": len(artifact_hashes),
    }
    summary: dict[str, Any] = {
        "project_name": project_name,
        "backup_cutoff": backup_cutoff,
        "mode_summary": {key: mode_counts[key] for key in sorted(mode_counts)},
        "execution_basis_summary": {
            key: basis_counts[key] for key in sorted(basis_counts)
        },
        "run_states": sorted(run_states),
        "counts": counts,
        "unfinished_work": unfinished,
        "schema_versions": {
            key: schema_versions[key]
            for key in sorted(schema_versions, key=lambda value: value.encode("utf-8"))
        },
        "artifact_hashes": sorted(artifact_hashes),
    }
    summary["semantic_digest"] = _oracle_sha256(
        _oracle_json_bytes(summary)
    )
    return {"members": member_hashes, "summary": summary}


def _oracle_fingerprint(member_bytes: Mapping[str, bytes]) -> str:
    identity = {
        relative: _oracle_sha256(member_bytes[relative])
        for relative in sorted(member_bytes, key=lambda value: value.encode("utf-8"))
    }
    return _oracle_sha256(_oracle_json_bytes(identity))


def _oracle_set_digest(values: Iterable[str]) -> str:
    return _oracle_sha256(_oracle_json_bytes(sorted(values)))


def _archive_state(package_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(str(package_path), "r") as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        members = {
            info.filename[len("members/") :]: archive.read(info.filename)
            for info in archive.infolist()
            if info.filename != "manifest.json"
        }
    return {
        "members": {relative: _oracle_sha256(data) for relative, data in members.items()},
        "summary": manifest["project_summary"],
    }


# ---------------------------------------------------------------------------
# Synthetic input fixture and archive mutation helpers
# ---------------------------------------------------------------------------


def _make_workspace(
    root: Path,
    project_id: str = PROJECT_ID,
    *,
    include_artifact: bool = False,
) -> Path:
    workspace = root / project_id
    workspace.mkdir(parents=True)
    ProfileStore(workspace / PROFILE_DB).close()
    RunBindingStore(workspace / BINDING_DB).close()
    runtime = workspace / "runtime"
    runtime.mkdir()
    store = Store(runtime / "monitoring_runtime.sqlite3", runtime / "artifacts")
    store.create_project(project_id, "合成项目 A")
    store.add_source_revision(
        SourceRevision(
            revision_id="revision-a",
            project_id=project_id,
            source_type="listing",
            version="v1",
            content_hash="source-a",
        )
    )
    store.create_run(
        MonitoringRun(
            run_id="run-a",
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="2026-08-30",
            source_revision_id="revision-a",
            execution_basis=ExecutionBasis.FULL,
            analysis_state=AnalysisState.NOT_STARTED,
        )
    )
    if include_artifact:
        envelope = ArtifactEnvelope(
            artifact_type="synthetic_result",
            version="v1",
            run_id="run-a",
            node_id="node-a",
            node_type=NodeType.DETERMINISTIC_SERVICE,
            payload={"value": "synthetic"},
        )
        staged_hash = store.stage_artifact(envelope)
        store.commit_artifact(staged_hash, envelope)
    store.close()
    return workspace


def _manager(root: Path, project_id: str = PROJECT_ID, **kwargs: Any) -> pb.ProjectBackupManager:
    return pb.ProjectBackupManager(root, project_id, wait_seconds=0.2, **kwargs)


def _update_project_name(workspace: Path, name: str) -> None:
    path = workspace / RUNTIME_DB
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "UPDATE projects SET name=? WHERE project_id=?", (name, PROJECT_ID)
        )
        conn.commit()
    finally:
        conn.close()


def _read_archive_entries(package_path: Path) -> list[tuple[zipfile.ZipInfo, bytes]]:
    with zipfile.ZipFile(str(package_path), "r") as archive:
        return [(info, archive.read(info.filename)) for info in archive.infolist()]


def _write_archive(path: Path, entries: Iterable[tuple[zipfile.ZipInfo, bytes]]) -> None:
    with zipfile.ZipFile(
        str(path), "w", compression=zipfile.ZIP_STORED, allowZip64=False
    ) as archive:
        for info, data in entries:
            archive.writestr(info, data)


def _replace_manifest(
    source: Path,
    destination: Path,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    entries = _read_archive_entries(source)
    rewritten: list[tuple[zipfile.ZipInfo, bytes]] = []
    for info, data in entries:
        if info.filename == "manifest.json":
            manifest = json.loads(data.decode("utf-8"))
            mutate(manifest)
            data = _oracle_json_bytes(manifest) + b"\n"
        rewritten.append((info, data))
    _write_archive(destination, rewritten)


def _fixed_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.create_version = 20
    info.extract_version = 20
    info.extra = b""
    info.comment = b""
    info.external_attr = 0o100644 << 16
    info.internal_attr = 0
    info.flag_bits = 0x800
    return info


def _hostile_archive(path: Path, name: str, *, symlink: bool = False) -> None:
    info = _fixed_info(name)
    if symlink:
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(
        str(path), "w", compression=zipfile.ZIP_STORED, allowZip64=False
    ) as archive:
        archive.writestr(info, b"hostile")


def _assert_archive_matches_oracle(
    package_path: Path,
    input_state: Mapping[str, Any],
    project_id: str = PROJECT_ID,
) -> None:
    package_bytes = package_path.read_bytes()
    with zipfile.ZipFile(str(package_path), "r") as archive:
        infos = archive.infolist()
        assert infos
        assert infos[0].filename == "manifest.json"
        assert all(
            info.filename == "manifest.json" or info.filename.startswith("members/")
            for info in infos
        )
        for info in infos:
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.create_system == 3
            assert info.create_version == 20
            assert info.extract_version == 20
            assert info.extra == b""
            assert info.comment == b""
            assert info.external_attr == 0o100644 << 16
        manifest_raw = archive.read("manifest.json")
        manifest = json.loads(manifest_raw.decode("utf-8"))
        assert manifest_raw == _oracle_json_bytes(manifest) + b"\n"
        member_bytes = {
            info.filename[len("members/") :]: archive.read(info.filename)
            for info in infos
            if info.filename != "manifest.json"
        }

    expected_relative = sorted(
        input_state["members"], key=lambda value: value.encode("utf-8")
    )
    assert list(member_bytes) == expected_relative
    expected_descriptors = [
        {
            "path": f"members/{relative}",
            "size": len(member_bytes[relative]),
            "sha256": _oracle_sha256(member_bytes[relative]),
        }
        for relative in expected_relative
    ]
    assert manifest["members"] == expected_descriptors
    assert manifest["canonical_project_id"] == project_id
    assert manifest["project_summary"] == input_state["summary"]
    assert manifest["project_name"] == input_state["summary"]["project_name"]
    assert manifest["backup_cutoff"] == input_state["summary"]["backup_cutoff"]
    assert manifest["source_workspace_fingerprint"] == _oracle_fingerprint(member_bytes)
    artifact_hashes = input_state["summary"]["artifact_hashes"]
    assert manifest["artifact_closure"] == {
        "content_hashes": artifact_hashes,
        "count": len(artifact_hashes),
        "set_digest": _oracle_set_digest(artifact_hashes),
    }
    digest_body = {
        key: manifest[key] for key in sorted(manifest) if key != "content_digest"
    }
    digest_payload = _oracle_json_bytes(digest_body) + b"".join(
        member_bytes[relative] for relative in expected_relative
    )
    assert manifest["content_digest"] == _oracle_sha256(digest_payload)
    assert _oracle_sha256(package_bytes) == package_path.stem.removesuffix(
        pb.BACKUP_SUFFIX
    )


# ---------------------------------------------------------------------------
# Determinism, closure, corruption and identity
# ---------------------------------------------------------------------------


def test_independent_oracle_reconstructs_deterministic_package(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path, include_artifact=True)
    expected = _oracle_workspace_state(workspace)
    manager = _manager(tmp_path)
    first = manager.backup("oracle-deterministic-1")
    second = manager.backup("oracle-deterministic-2")
    assert first.package_path is not None
    assert second.package_path is not None
    assert first.package_id == second.package_id
    assert first.package_path.read_bytes() == second.package_path.read_bytes()
    assert first.package_id == _oracle_sha256(first.package_path.read_bytes())
    _assert_archive_matches_oracle(first.package_path, expected)
    assert manager.ledger.get(first.operation_id).progress_percent == 100


def test_deterministic_package_survives_hashseed_optimization_and_locale_grid(
    tmp_path: Path,
) -> None:
    _make_workspace(tmp_path, include_artifact=True)
    manager = _manager(tmp_path)
    baseline = manager.backup("oracle-grid-baseline")
    assert baseline.package_path is not None
    baseline_bytes = baseline.package_path.read_bytes()
    manager.ledger.close()
    script = """
import os
import sys
from mm_r7.project_backup import ProjectBackupManager
os.umask(int(os.environ['TEST_UMASK'], 8))
manager = ProjectBackupManager(sys.argv[1], sys.argv[2], wait_seconds=0.2)
result = manager.backup(sys.argv[3])
assert result.package_path is not None
sys.stdout.write(result.package_path.read_bytes().hex())
manager.ledger.close()
"""
    r7_src = Path(__file__).resolve().parents[1] / "src"
    for seed in ("0", "1", "17", "42", "31415926"):
        for optimize in (None, "-O", "-OO"):
            for timezone in ("UTC", "Asia/Shanghai"):
                env = os.environ.copy()
                env["PYTHONHASHSEED"] = seed
                env["LC_ALL"] = "C.UTF-8"
                env["TZ"] = timezone
                env["TEST_UMASK"] = "022" if seed in {"0", "17", "31415926"} else "077"
                env["PYTHONPATH"] = os.pathsep.join(
                    part for part in (str(r7_src), env.get("PYTHONPATH", "")) if part
                )
                command = [sys.executable]
                if optimize:
                    command.append(optimize)
                command.extend(
                    [
                        "-c",
                        script,
                        str(tmp_path),
                        PROJECT_ID,
                        f"oracle-grid-{seed}-{optimize}-{timezone}",
                    ]
                )
                completed = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                assert bytes.fromhex(completed.stdout.strip()) == baseline_bytes


@pytest.mark.parametrize("mutation", ["missing_manifest", "missing_member", "extra_member", "tampered_member"])
def test_member_closure_and_byte_corruption_fail_closed(
    tmp_path: Path,
    mutation: str,
) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup(f"closure-source-{mutation}")
    assert backup.package_path is not None
    entries = _read_archive_entries(backup.package_path)
    if mutation == "missing_manifest":
        entries = [(info, data) for info, data in entries if info.filename != "manifest.json"]
    elif mutation == "missing_member":
        entries = entries[:-1]
    elif mutation == "extra_member":
        entries.append((_fixed_info("members/unlisted.bin"), b"unlisted"))
    else:
        info, data = entries[-1]
        entries[-1] = (info, data + b"tamper")
    broken = tmp_path / f"{mutation}.mmbackup"
    _write_archive(broken, entries)
    with pytest.raises(pb.ProjectBackupError) as exc_info:
        manager.preflight(broken, f"closure-preflight-{mutation}")
    assert exc_info.value.code in {"package_corrupt", "manifest_semantic_mismatch"}
    assert not (tmp_path / pb.STAGING_DIR_NAME).exists() or all(
        path.name != f"closure-preflight-{mutation}"
        for path in (tmp_path / pb.STAGING_DIR_NAME).iterdir()
    )


@pytest.mark.parametrize(
    "name",
    [
        "/absolute/path",
        "../escape",
        "members/../escape",
        "members\\escape",
        "members/./escape",
    ],
)
def test_zip_path_traversal_and_absolute_names_are_rejected(
    tmp_path: Path,
    name: str,
) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    hostile = tmp_path / ("hostile-" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:8] + ".mmbackup")
    _hostile_archive(hostile, name)
    with pytest.raises(pb.ProjectBackupError) as exc_info:
        manager.preflight(hostile, f"hostile-preflight-{name.replace('/', '_')}")
    assert exc_info.value.code == "package_corrupt"


def test_zip_duplicate_symlink_and_resource_limits_are_rejected(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    duplicate = tmp_path / "duplicate.mmbackup"
    info_a = _fixed_info("members/a")
    info_b = _fixed_info("members/a")
    _write_archive(duplicate, [(info_a, b"a"), (info_b, b"b")])
    with pytest.raises(pb.ProjectBackupError) as duplicate_error:
        manager.preflight(duplicate, "hostile-duplicate")
    assert duplicate_error.value.code == "package_corrupt"

    symlink = tmp_path / "symlink.mmbackup"
    _hostile_archive(symlink, "members/link", symlink=True)
    with pytest.raises(pb.ProjectBackupError) as symlink_error:
        manager.preflight(symlink, "hostile-symlink")
    assert symlink_error.value.code == "package_corrupt"

    backup = manager.backup("resource-source")
    assert backup.package_path is not None
    small_count_manager = _manager(tmp_path, max_archive_members=1)
    with pytest.raises(pb.ProjectBackupError) as count_error:
        small_count_manager.preflight(backup.package_path, "hostile-count")
    assert count_error.value.code == "package_corrupt"
    small_member_manager = _manager(tmp_path, max_member_bytes=1)
    with pytest.raises(pb.ProjectBackupError) as size_error:
        small_member_manager.preflight(backup.package_path, "hostile-size")
    assert size_error.value.code == "package_corrupt"


def test_manifest_semantics_contract_and_schema_rejections_are_stable(
    tmp_path: Path,
) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("manifest-source")
    assert backup.package_path is not None

    unsupported = tmp_path / "unsupported.mmbackup"
    _replace_manifest(
        backup.package_path,
        unsupported,
        lambda manifest: manifest.__setitem__("contract_version", "future-contract"),
    )
    with pytest.raises(pb.ProjectBackupError) as unsupported_error:
        manager.preflight(unsupported, "manifest-unsupported")
    assert unsupported_error.value.code == "unsupported_contract"

    semantic = tmp_path / "semantic.mmbackup"
    def tamper_summary(manifest: dict[str, Any]) -> None:
        manifest["project_summary"] = dict(manifest["project_summary"])
        manifest["project_summary"]["counts"] = dict(
            manifest["project_summary"]["counts"]
        )
        manifest["project_summary"]["counts"]["runs"] += 1

    _replace_manifest(backup.package_path, semantic, tamper_summary)
    with pytest.raises(pb.ProjectBackupError) as semantic_error:
        manager.preflight(semantic, "manifest-semantic")
    assert semantic_error.value.code == "manifest_semantic_mismatch"


def test_sqlite_corruption_is_rejected_without_partial_backup(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    before = _oracle_workspace_state(workspace)
    runtime_db = workspace / RUNTIME_DB
    runtime_db.write_bytes(runtime_db.read_bytes()[:64])
    with pytest.raises(pb.ProjectBackupError) as corruption:
        manager.backup("sqlite-corruption")
    assert corruption.value.code == "sqlite_integrity_failed"
    assert workspace.is_dir()
    # The operation must not publish a package from the damaged input.
    assert not list((tmp_path / "backups").glob("*.mmbackup"))
    # The input-side oracle still identifies the expected member set; the
    # damaged runtime is not silently replaced by a partial workspace.
    assert before["members"].keys() == set(_oracle_workspace_member_names(workspace))


def test_artifact_missing_tampered_and_extra_files_fail_closed(tmp_path: Path) -> None:
    for mutation in ("missing", "tampered", "extra"):
        case_root = tmp_path / mutation
        case_root.mkdir()
        workspace = _make_workspace(case_root, include_artifact=True)
        artifact_dir = workspace / "runtime" / "artifacts"
        artifact = next(artifact_dir.glob("*.json"))
        if mutation == "missing":
            artifact.unlink()
        elif mutation == "tampered":
            artifact.write_bytes(artifact.read_bytes() + b"tamper")
        else:
            orphan_data = b'{"orphan":true}'
            orphan = case_root / "orphan-hash.json"
            orphan.write_bytes(orphan_data)
            orphan_hash = _oracle_sha256(orphan_data)
            (artifact_dir / f"{orphan_hash}.json").write_bytes(orphan_data)
        manager = _manager(case_root)
        with pytest.raises(pb.ProjectBackupError) as exc_info:
            manager.backup(f"artifact-{mutation}")
        assert exc_info.value.code == "artifact_closure_invalid"
        assert not list((case_root / "backups").glob("*.mmbackup"))


def test_cross_project_and_exact_manifest_identity_are_rejected(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("identity-source")
    assert backup.package_path is not None

    other = _manager(tmp_path, "project-b")
    with pytest.raises(pb.ProjectBackupError) as cross_project:
        other.preflight(backup.package_path, "identity-cross-project")
    assert cross_project.value.code == "package_identity_mismatch"

    rewritten = tmp_path / "identity-uppercase.mmbackup"
    _replace_manifest(
        backup.package_path,
        rewritten,
        lambda manifest: manifest.__setitem__("canonical_project_id", "PROJECT-A"),
    )
    with pytest.raises(pb.ProjectBackupError) as exact_identity:
        manager.preflight(rewritten, "identity-uppercase")
    assert exact_identity.value.code == "package_identity_mismatch"


def test_workspace_with_second_project_identity_is_rejected(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    conn = sqlite3.connect(str(workspace / RUNTIME_DB))
    try:
        conn.execute(
            "INSERT INTO projects(project_id,name,is_synthetic,config_json,created_at) "
            "VALUES (?,?,?,?,?)",
            ("project-b", "错误项目", 1, "{}", "2026-08-30"),
        )
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(pb.ProjectBackupError) as exc_info:
        _manager(tmp_path).backup("identity-workspace")
    assert exc_info.value.code == "package_identity_mismatch"


# ---------------------------------------------------------------------------
# Replay, writer race, source drift and atomic switch/rollback
# ---------------------------------------------------------------------------


def test_same_key_replay_conflict_and_single_package_identity(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    first = manager.backup("same-key")
    replay = manager.backup("same-key")
    assert replay.operation_id == first.operation_id
    assert replay.package_id == first.package_id
    assert replay.package_path is not None
    assert first.package_path is not None
    original_bytes = first.package_path.read_bytes()
    _update_project_name(workspace, "状态已改变")
    with pytest.raises(pb.ProjectBackupError) as conflict:
        manager.backup("same-key")
    assert conflict.value.code == "backup_operation_conflict"
    assert first.package_path.read_bytes() == original_bytes
    assert manager.ledger.get(first.operation_id).status == pb.STATUS_AVAILABLE
 
def test_restore_same_key_replay_and_different_package_conflict(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    original = manager.backup("restore-replay-original")
    assert original.package_path is not None
    _update_project_name(workspace, "较新项目")
    newer = manager.backup("restore-replay-newer")
    assert newer.package_path is not None
    preflight = manager.preflight(original.package_path, "restore-replay-preflight")
    restored = manager.restore(
        original.package_path,
        "restore-replay-key",
        confirmation=True,
        preflight_result=preflight,
    )
    replay = manager.restore(
        original.package_path,
        "restore-replay-key",
        confirmation=True,
    )
    assert replay.operation_id == restored.operation_id
    assert replay.operation.status == pb.STATUS_COMPLETED
    with pytest.raises(pb.ProjectBackupError) as conflict:
        manager.restore(
            newer.package_path,
            "restore-replay-key",
            confirmation=True,
        )
    assert conflict.value.code == "backup_operation_conflict"
    assert _oracle_workspace_state(workspace)["summary"]["project_name"] == "合成项目 A"


def _backup_child(
    root: str,
    project_id: str,
    key: str,
    result_queue: Any,
    delay: bool,
) -> None:
    def hook(point: str) -> None:
        if delay and point == "backup.sqlite_snapshot.before":
            time.sleep(0.15)

    manager = _manager(Path(root), project_id, failure_hook=hook if delay else None)
    try:
        result = manager.backup(key)
        result_queue.put(("ok", result.operation_id, result.package_id))
    except Exception as exc:  # pragma: no cover - surfaced by parent assertion
        result_queue.put(("error", type(exc).__name__, str(exc)))
    finally:
        manager.ledger.close()


def test_concurrent_same_key_backup_replays_original_operation(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    queue: Any = multiprocessing.Queue()
    first = multiprocessing.Process(
        target=_backup_child,
        args=(str(tmp_path), PROJECT_ID, "concurrent-same-key", queue, True),
    )
    second = multiprocessing.Process(
        target=_backup_child,
        args=(str(tmp_path), PROJECT_ID, "concurrent-same-key", queue, False),
    )
    first.start()
    time.sleep(0.03)
    second.start()
    first.join(10)
    second.join(10)
    assert first.exitcode == 0
    assert second.exitcode == 0
    results = [queue.get(timeout=2), queue.get(timeout=2)]
    assert all(result[0] == "ok" for result in results), results
    assert results[0][1] == results[1][1]
    assert results[0][2] == results[1][2]


def _hold_writer(root: str, project_id: str, ready: Any, release: Any) -> None:
    gate = ProjectMaintenanceGate(root, project_id, wait_seconds=2)
    with gate.shared():
        conn = sqlite3.connect(str(Path(root) / project_id / RUNTIME_DB))
        try:
            conn.execute("BEGIN IMMEDIATE")
            ready.set()
            release.wait(5)
            conn.rollback()
        finally:
            conn.close()


def test_active_writer_blocks_restore_without_switch_and_retry_switches_once(
    tmp_path: Path,
) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("writer-source")
    assert backup.package_path is not None
    _update_project_name(workspace, "恢复前版本")
    preflight = manager.preflight(backup.package_path, "writer-preflight")
    current = _oracle_workspace_state(workspace)
    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    writer = multiprocessing.Process(
        target=_hold_writer,
        args=(str(tmp_path), PROJECT_ID, ready, release),
    )
    writer.start()
    assert ready.wait(3)
    try:
        with pytest.raises(pb.ProjectBackupError) as busy:
            manager.restore(
                backup.package_path,
                "writer-restore",
                confirmation=True,
                preflight_result=preflight,
            )
        assert busy.value.code == "project_busy_retry_later"
        failed = manager.get_operation(
            manager.ledger.list_for_project(PROJECT_ID)[-1].operation_id
        )
        assert failed.status == pb.STATUS_FAILED
        assert failed.error_code == "project_busy_retry_later"
        assert _oracle_workspace_state(workspace)["members"] == current["members"]
    finally:
        release.set()
        writer.join(5)
    assert writer.exitcode == 0

    retried = manager.restore(
        backup.package_path,
        "writer-restore",
        confirmation=True,
        preflight_result=preflight,
    )
    assert retried.operation.status == pb.STATUS_COMPLETED
    assert retried.rollback_path is not None
    assert retried.rollback_path.is_dir()
    assert _oracle_workspace_state(workspace)["members"] == _archive_state(
        backup.package_path
    )["members"]


def test_restore_preflight_state_drift_never_switches_directory(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("drift-source")
    assert backup.package_path is not None
    _update_project_name(workspace, "预检时版本")
    preflight = manager.preflight(backup.package_path, "drift-preflight")
    before_drift = _oracle_workspace_state(workspace)
    _update_project_name(workspace, "预检后漂移版本")
    after_drift = _oracle_workspace_state(workspace)
    with pytest.raises(pb.ProjectBackupError) as drift:
        manager.restore(
            backup.package_path,
            "drift-restore",
            confirmation=True,
            preflight_result=preflight,
        )
    assert drift.value.code == "restore_source_changed"
    assert _oracle_workspace_state(workspace)["members"] == after_drift["members"]
    assert _oracle_workspace_state(workspace)["members"] != before_drift["members"]
    assert not list(tmp_path.glob(".rollback-*"))


def test_switch_failure_rolls_back_to_one_complete_live_workspace(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path, include_artifact=True)
    manager = _manager(tmp_path)
    backup = manager.backup("switch-fault-source")
    assert backup.package_path is not None
    _update_project_name(workspace, "切换前版本")
    current = _oracle_workspace_state(workspace)
    preflight = manager.preflight(backup.package_path, "switch-fault-preflight")

    def fail_switch(point: str) -> None:
        if point == "restore.staging_to_live.before":
            raise RuntimeError("switch fault")

    manager.set_failure_hook(fail_switch)
    with pytest.raises(pb.ProjectBackupError) as switch_error:
        manager.restore(
            backup.package_path,
            "switch-fault-restore",
            confirmation=True,
            preflight_result=preflight,
        )
    assert switch_error.value.code == "injected_failure"
    assert _oracle_workspace_state(workspace)["members"] == current["members"]
    record = manager.ledger.list_for_project(PROJECT_ID)[-1]
    assert record.status == pb.STATUS_FAILED
    assert record.error_code == "injected_failure"


def test_automatic_rollback_failure_retains_triage_directories(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("rollback-fault-source")
    assert backup.package_path is not None
    _update_project_name(workspace, "回退前版本")
    current = _oracle_workspace_state(workspace)
    target = _archive_state(backup.package_path)
    preflight = manager.preflight(backup.package_path, "rollback-fault-preflight")

    def fail_rollback(point: str) -> None:
        if point in {"restore.staging_to_live.after", "restore.rollback.before"}:
            raise RuntimeError("rollback fault")

    manager.set_failure_hook(fail_rollback)
    with pytest.raises(pb.ProjectBackupError) as rollback_error:
        manager.restore(
            backup.package_path,
            "rollback-fault-restore",
            confirmation=True,
            preflight_result=preflight,
        )
    assert rollback_error.value.code == "restore_rollback_failed"
    record = manager.ledger.list_for_project(PROJECT_ID)[-1]
    assert record.status == pb.STATUS_RETAINED_FOR_TRIAGE
    assert record.error_code == "restore_rollback_failed"
    assert record.rollback_path is not None
    assert Path(record.rollback_path).is_dir()
    assert record.staging_path is not None
    assert Path(record.staging_path).is_dir()
    actual_members = tuple(_oracle_workspace_state(workspace)["members"].items())
    assert actual_members in {
        tuple(current["members"].items()),
        tuple(target["members"].items()),
    }


def test_rollback_after_failure_keeps_rollback_pointer_resolvable(tmp_path: Path) -> None:
    """Contract probe: a retained triage record must retain both directories."""

    workspace = _make_workspace(tmp_path)
    manager = _manager(tmp_path)
    backup = manager.backup("rollback-after-source")
    assert backup.package_path is not None
    _update_project_name(workspace, "回退后钩子前版本")
    preflight = manager.preflight(backup.package_path, "rollback-after-preflight")

    def fail_after(point: str) -> None:
        if point in {"restore.staging_to_live.after", "restore.rollback.after"}:
            raise RuntimeError("rollback after fault")

    manager.set_failure_hook(fail_after)
    with pytest.raises(pb.ProjectBackupError) as exc_info:
        manager.restore(
            backup.package_path,
            "rollback-after-restore",
            confirmation=True,
            preflight_result=preflight,
        )
    assert exc_info.value.code == "restore_rollback_failed"
    record = manager.ledger.list_for_project(PROJECT_ID)[-1]
    assert record.status == pb.STATUS_RETAINED_FOR_TRIAGE
    assert record.rollback_path is not None
    # v0.3 requires retained_for_triage to preserve the rollback material.
    assert Path(record.rollback_path).is_dir()


def test_restore_reopen_matches_input_oracle_and_manual_rollback_reconciles(
    tmp_path: Path,
) -> None:
    workspace = _make_workspace(tmp_path, include_artifact=True)
    baseline = _oracle_workspace_state(workspace)
    manager = _manager(tmp_path)
    backup = manager.backup("reopen-source")
    assert backup.package_path is not None
    target = _archive_state(backup.package_path)
    _update_project_name(workspace, "更新后的项目")
    _manager_current = _oracle_workspace_state(workspace)
    preflight = manager.preflight(backup.package_path, "reopen-preflight")
    restored = manager.restore(
        backup.package_path,
        "reopen-restore",
        confirmation=True,
        preflight_result=preflight,
    )
    assert restored.operation.status == pb.STATUS_COMPLETED
    assert _oracle_workspace_state(workspace)["members"] == target["members"]
    assert _oracle_workspace_state(workspace)["summary"] == baseline["summary"]
    manager.ledger.close()

    reopened = _manager(tmp_path)
    after_reopen = _oracle_workspace_state(workspace)
    assert after_reopen["members"] == target["members"]
    assert after_reopen["summary"] == baseline["summary"]
    rolled_back = reopened.rollback(restored.operation_id)
    assert rolled_back.operation.status == pb.STATUS_COMPLETED
    assert _oracle_workspace_state(workspace)["members"] == _manager_current["members"]


# ---------------------------------------------------------------------------
# Source-enumerated fault hook coverage
# ---------------------------------------------------------------------------


def _assert_live_is_complete_variant(
    workspace: Path,
    before: Mapping[str, Any],
    target: Mapping[str, Any],
) -> None:
    actual = _oracle_workspace_state(workspace)
    actual_members = tuple(actual["members"].items())
    assert actual_members in {
        tuple(before["members"].items()),
        tuple(target["members"].items()),
    }


@pytest.mark.parametrize("hook", tuple(pb.FAILURE_HOOK_POINTS))
def test_every_source_enumerated_failure_hook_is_hit_atomically(
    tmp_path: Path,
    hook: str,
) -> None:
    if hook.startswith("backup."):
        workspace = _make_workspace(tmp_path, include_artifact=True)
        before = _oracle_workspace_state(workspace)
        manager = _manager(tmp_path)
        seen: list[str] = []

        def fail(point: str) -> None:
            seen.append(point)
            if point == hook:
                raise RuntimeError("declared backup fault")

        manager.set_failure_hook(fail)
        with pytest.raises(pb.ProjectBackupError):
            manager.backup("hook-backup")
        assert hook in seen
        assert _oracle_workspace_state(workspace)["members"] == before["members"]
        return

    if hook.startswith("preflight."):
        workspace = _make_workspace(tmp_path, include_artifact=True)
        before = _oracle_workspace_state(workspace)
        manager = _manager(tmp_path)
        backup = manager.backup("hook-preflight-source")
        assert backup.package_path is not None
        seen = []

        def fail(point: str) -> None:
            seen.append(point)
            if point == hook:
                raise RuntimeError("declared preflight fault")

        manager.set_failure_hook(fail)
        with pytest.raises(pb.ProjectBackupError):
            manager.preflight(backup.package_path, "hook-preflight")
        assert hook in seen
        assert _oracle_workspace_state(workspace)["members"] == before["members"]
        return

    assert hook.startswith("restore.")
    workspace = _make_workspace(tmp_path, include_artifact=True)
    before = _oracle_workspace_state(workspace)
    manager = _manager(tmp_path)
    backup = manager.backup("hook-restore-source")
    assert backup.package_path is not None
    target = _archive_state(backup.package_path)
    _update_project_name(workspace, "故障注入前版本")
    before_restore = _oracle_workspace_state(workspace)
    preflight = manager.preflight(backup.package_path, "hook-restore-preflight")
    seen = []
    primary = "restore.staging_to_live.after" if hook.startswith("restore.rollback.") else None

    def fail(point: str) -> None:
        seen.append(point)
        if point == hook or (primary is not None and point == primary):
            raise RuntimeError("declared restore fault")

    manager.set_failure_hook(fail)
    with pytest.raises(pb.ProjectBackupError):
        manager.restore(
            backup.package_path,
            "hook-restore",
            confirmation=True,
            preflight_result=preflight,
        )
    assert hook in seen
    _assert_live_is_complete_variant(workspace, before_restore, target)
    # The initial fixture state remains independently valid; no test-side
    # product helper is used to establish the live-state invariant.
    assert before["members"].keys() == before_restore["members"].keys()


# Keep the imported exception exercised in the matrix's bounded gate checks.
def test_gate_busy_error_is_stable_and_fd_releases(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    gate = ProjectMaintenanceGate(tmp_path, PROJECT_ID, wait_seconds=0)
    with gate.shared():
        competing = ProjectMaintenanceGate(tmp_path, PROJECT_ID, wait_seconds=0)
        with pytest.raises(ProjectBusyError) as exc_info:
            competing.exclusive()
        assert exc_info.value.code == "project_busy_retry_later"
    with ProjectMaintenanceGate(tmp_path, PROJECT_ID, wait_seconds=0).exclusive():
        pass
