"""Slice-09E local distribution focused tests (synthetic/offline).

Contract: reviews/medical_monitoring_r7_slice09e_local_distribution_contract_v0_2_20260831.md
Covers §6 verification matrix, Chinese user copy, exit codes, release inventory
exclusions, acceptance-runner synthetic isolation, and normal/-O/-OO × three
PYTHONHASHSEED determinism for release manifest + uninstall plan digests.

Does not start 8911/5174/8984, call models, read real project roots, or modify
deploy/medical_writing_local.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
R7_SRC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "src"
R7_TESTS = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "tests"
MEDICAL_WRITING_LOCAL = WORKBENCH_ROOT / "deploy" / "medical_writing_local"

for _path in (
    DEPLOY_DIR,
    R7_SRC,
    R7_TESTS,
    *(
        WORKBENCH_ROOT / "poc" / f"medical_monitoring_ai_native_{rev}" / "src"
        for rev in ("r6", "r5", "r4", "r3", "r3_rule_ai", "r2", "r1")
    ),
):
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import distribution as dist  # noqa: E402
import manage as manage_mod  # noqa: E402
from fixtures_schema_manifest import make_project  # noqa: E402
from mm_r7.maintenance_gate import ProjectMaintenanceGate  # noqa: E402

EXIT_OK = 0
EXIT_PREFLIGHT_OR_ARGS = 2
EXIT_PORT_OWNERSHIP = 3
EXIT_UPGRADE_PREP = 4
EXIT_MAINTENANCE_BUSY = 5

PROTECTED_PORTS = (8911, 5174, 8984)
HASH_SEEDS = ("0", "1", "42")
OPT_FLAGS: Tuple[Tuple[str, ...], ...] = ((), ("-O",), ("-OO",))

LEAK_TOKENS = (
    "8911",
    "5174",
    "8984",
    "sqlite",
    "PID",
    "pid=",
    "__pycache__",
    str(WORKBENCH_ROOT),
)


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def _assert_ports_stopped() -> None:
    for port in PROTECTED_PORTS:
        assert _port_connect_ex(port) != 0, f"port {port} unexpectedly listening"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _make_distribution_root(
    tmp_path: Path,
    *,
    with_start_scripts: bool = False,
    aux_enabled: Optional[bool] = None,
    with_runtime_config: bool = True,
    root_name: str = "mm-dist",
) -> manage_mod.Paths:
    root = tmp_path / root_name
    frontend = root / "frontend"
    data_dir = root / "data"
    (frontend / "node_modules").mkdir(parents=True)
    data_dir.mkdir(parents=True)
    (frontend / "package.json").write_text(
        json.dumps({"name": "mm-frontend-synthetic", "private": True}, ensure_ascii=False),
        encoding="utf-8",
    )
    if with_runtime_config:
        runtime = {
            "schema": manage_mod.RUNTIME_SCHEMA,
            "product_name": "医学监查工作台",
            "data_dir": str(data_dir),
        }
        if aux_enabled is True:
            runtime["aux_enabled"] = True
        _write_json(root / manage_mod.RUNTIME_CONFIG_NAME, runtime)
    if with_start_scripts:
        bin_dir = root / "bin"
        bin_dir.mkdir(parents=True)
        for name in ("start_backend.zsh", "start_frontend.zsh", "start_aux.zsh"):
            script = bin_dir / name
            script.write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")
            script.chmod(0o755)
    return manage_mod.resolve_paths(root)


def _fingerprint_workspace(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(workspace.rglob("*"), key=lambda p: p.as_posix().encode("utf-8")):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace).as_posix()
        parts = rel.split("/")
        if "__pycache__" in parts or rel.endswith(".pyc"):
            continue
        # SQLite may create ephemeral -wal/-shm while readers open the DB; exclude them.
        if rel.endswith((".sqlite3-wal", ".sqlite3-shm", "-wal", "-shm")):
            continue
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()

def _no_foreign_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        manage_mod,
        "classify_ports",
        lambda paths: {"owned": [], "foreign": []},
    )


def _patch_classify_ports(
    monkeypatch: pytest.MonkeyPatch,
    paths: manage_mod.Paths,
    *,
    owned_ports: Tuple[int, ...] = (),
    foreign_ports: Tuple[int, ...] = (),
) -> None:
    owned = [
        manage_mod.Listener(port=port, pid=1000 + port, cwd=paths.root)
        for port in owned_ports
    ]
    foreign = [
        manage_mod.Listener(port=port, pid=2000 + port, cwd=paths.root.parent / "foreign-app")
        for port in foreign_ports
    ]
    monkeypatch.setattr(
        manage_mod,
        "classify_ports",
        lambda _paths: {"owned": owned, "foreign": foreign},
    )


def _assert_json_has_no_absolute_paths(payload: Dict[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False)
    assert blob.count("/") == 0 or all(
        token not in blob
        for token in ("/Users/", "/var/", "/private/", "/tmp/", ":\\\\")
    )
    machine = payload.get("machine") or {}
    assert set(machine.keys()) <= {"distribution_root_name", "data_dir_name"}


def _assert_chinese_user_copy(text: str) -> None:
    assert "医学监查" in text or "升级" in text or "卸载" in text or "启动" in text
    lowered = text.lower()
    for token in LEAK_TOKENS:
        assert token.lower() not in lowered, f"user copy leaked {token!r}: {text!r}"


def test_preflight_ok_with_complete_deps_does_not_start_services(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _assert_ports_stopped()
    paths = _make_distribution_root(tmp_path)
    _no_foreign_ports(monkeypatch)
    code = manage_mod.cmd_preflight(paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert manage_mod.MSG_PREFLIGHT_OK in out
    _assert_chinese_user_copy(out)
    _assert_ports_stopped()


@pytest.mark.parametrize(
    "mutate,expected_fragment",
    [
        ("node", "Node.js"),
        ("config", "运行配置"),
        ("data_dir", "数据目录"),
        ("frontend", "前端"),
        ("node_modules", "前端依赖"),
    ],
)
def test_preflight_missing_deps_fail_closed_chinese(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: str,
    expected_fragment: str,
) -> None:
    paths = _make_distribution_root(tmp_path)
    _no_foreign_ports(monkeypatch)
    if mutate == "node":
        monkeypatch.setattr(manage_mod, "_which_node", lambda: None)
    elif mutate == "config":
        paths.runtime_config.unlink()
    elif mutate == "data_dir":
        for child in paths.data_dir.iterdir():
            child.unlink()
        paths.data_dir.rmdir()
    elif mutate == "frontend":
        import shutil

        shutil.rmtree(paths.frontend)
    elif mutate == "node_modules":
        import shutil

        shutil.rmtree(paths.frontend / "node_modules")
    with pytest.raises(manage_mod.ManageError) as raised:
        manage_mod.run_preflight(paths)
    assert raised.value.exit_code == EXIT_PREFLIGHT_OR_ARGS
    assert expected_fragment in raised.value.message
    for token in ("8911", "5174", "8984", str(paths.root)):
        assert token not in raised.value.message


def test_foreign_port_blocks_start_without_killing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path, with_start_scripts=True)
    foreign = manage_mod.Listener(port=8911, pid=424242, cwd=tmp_path / "other-app")
    monkeypatch.setattr(
        manage_mod,
        "classify_ports",
        lambda paths: {"owned": [], "foreign": [foreign]},
    )
    killed: List[int] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append(pid))
    with pytest.raises(manage_mod.ManageError) as raised:
        manage_mod.run_preflight(paths, require_start_scripts=True)
    assert raised.value.exit_code == EXIT_PORT_OWNERSHIP
    assert "其他应用" in raised.value.message
    assert killed == []
    _assert_ports_stopped()


def test_stop_rejects_unowned_listener(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path)
    foreign = manage_mod.Listener(port=5174, pid=777001, cwd=tmp_path / "foreign")
    monkeypatch.setattr(
        manage_mod,
        "classify_ports",
        lambda paths: {"owned": [], "foreign": [foreign]},
    )
    killed: List[int] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append(pid))
    with pytest.raises(manage_mod.ManageError) as raised:
        manage_mod.cmd_stop(paths)
    assert raised.value.exit_code == EXIT_PORT_OWNERSHIP
    assert killed == []


def test_stop_with_root_without_runtime_config_returns_two_without_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path)
    paths.runtime_config.unlink()
    _patch_classify_ports(
        monkeypatch,
        paths,
        owned_ports=(manage_mod.PORT_BACKEND, manage_mod.PORT_FRONTEND),
    )
    killed: List[int] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append(pid))
    code = manage_mod.main(["--root", str(paths.root), "stop"])
    assert code == EXIT_PREFLIGHT_OR_ARGS
    assert killed == []


def test_status_running_when_backend_and_frontend_owned_and_aux_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path, aux_enabled=False)
    _patch_classify_ports(
        monkeypatch,
        paths,
        owned_ports=(manage_mod.PORT_BACKEND, manage_mod.PORT_FRONTEND),
    )
    code = manage_mod.cmd_status(paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert manage_mod.MSG_STATUS_RUNNING in out


def test_status_foreign_aux_blocks_even_when_core_ports_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path, aux_enabled=False)
    _patch_classify_ports(
        monkeypatch,
        paths,
        owned_ports=(manage_mod.PORT_BACKEND, manage_mod.PORT_FRONTEND),
        foreign_ports=(manage_mod.PORT_AUX,),
    )
    with pytest.raises(manage_mod.ManageError) as raised:
        manage_mod.cmd_status(paths)
    assert raised.value.exit_code == EXIT_PORT_OWNERSHIP


def test_status_partial_when_aux_enabled_but_aux_port_not_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path, aux_enabled=True)
    _patch_classify_ports(
        monkeypatch,
        paths,
        owned_ports=(manage_mod.PORT_BACKEND, manage_mod.PORT_FRONTEND),
    )
    code = manage_mod.cmd_status(paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert manage_mod.MSG_STATUS_PARTIAL in out


def test_status_running_when_aux_enabled_and_all_three_ports_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path, aux_enabled=True)
    _patch_classify_ports(
        monkeypatch,
        paths,
        owned_ports=(
            manage_mod.PORT_BACKEND,
            manage_mod.PORT_FRONTEND,
            manage_mod.PORT_AUX,
        ),
    )
    code = manage_mod.cmd_status(paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert manage_mod.MSG_STATUS_RUNNING in out


def test_status_stopped_when_no_owned_listeners(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path)
    _no_foreign_ports(monkeypatch)
    code = manage_mod.cmd_status(paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert manage_mod.MSG_STATUS_STOPPED in out
    _assert_chinese_user_copy(out)

def test_offline_start_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path, with_start_scripts=True)
    _no_foreign_ports(monkeypatch)
    monkeypatch.setenv("MM_MONITORING_OFFLINE", "1")
    with pytest.raises(manage_mod.ManageError) as raised:
        manage_mod.cmd_start(paths)
    assert raised.value.exit_code == EXIT_PREFLIGHT_OR_ARGS
    assert "离线验收" in raised.value.message
    _assert_ports_stopped()


def test_help_and_bare_invocation_are_chinese() -> None:
    code = manage_mod.main([])
    assert code == EXIT_PREFLIGHT_OR_ARGS
    completed = subprocess.run(
        [sys.executable, str(DEPLOY_DIR / "manage.py"), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(WORKBENCH_ROOT),
    )
    assert completed.returncode == 0
    blob = completed.stdout + completed.stderr
    assert "医学监查工作台" in blob
    assert "首次启动检查" in blob or "preflight" in blob


def test_release_manifest_excludes_forbidden_and_is_stable() -> None:
    first = dist.build_release_manifest(workbench_root=WORKBENCH_ROOT)
    second = dist.build_release_manifest(workbench_root=WORKBENCH_ROOT)
    assert first["schema"] == dist.RELEASE_MANIFEST_SCHEMA
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["file_count"] == second["file_count"]
    assert first["files"] == second["files"]
    joined = "\n".join(item["path"] for item in first["files"])
    for banned in (
        "deploy/medical_writing_local",
        ".env",
        "__pycache__",
        "node_modules",
        ".mmbackup",
        ".sqlite3",
        "/cache/",
        "/logs/",
        "credentials",
    ):
        assert banned not in joined
    assert all(
        item["path"].startswith(
            (
                "deploy/medical_monitoring_local/",
                "poc/medical_monitoring_ai_native_r1/",
                "poc/medical_monitoring_ai_native_r2/",
                "poc/medical_monitoring_ai_native_r3/",
                "poc/medical_monitoring_ai_native_r3_rule_ai/",
                "poc/medical_monitoring_ai_native_r4/",
                "poc/medical_monitoring_ai_native_r5/",
                "poc/medical_monitoring_ai_native_r6/",
                "poc/medical_monitoring_ai_native_r7/",
            )
        )
        for item in first["files"]
    )
    assert "真实" not in json.dumps(first, ensure_ascii=False)


def test_release_sources_entries_exist_on_disk() -> None:
    sources = dist._load_release_sources()
    for entry in sources["entries"]:
        assert (WORKBENCH_ROOT / entry).exists(), entry
    assert {
        "deploy/medical_monitoring_local/canonical_evidence.py",
        "deploy/medical_monitoring_local/synthetic_manifest.py",
        "deploy/medical_monitoring_local/source_access_profile.py",
        "deploy/medical_monitoring_local/synthetic_lifecycle.py",
    }.issubset(set(sources["entries"]))


def test_default_uninstall_plan_retains_project_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path)
    out_dir = tmp_path / "uninstall-out"
    sentinel = paths.data_dir / "keep-me.txt"
    sentinel.write_text("retain", encoding="utf-8")
    before = list(paths.data_dir.rglob("*"))
    code = dist.uninstall_plan_main(["--output-dir", str(out_dir)], paths=paths)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert dist.MSG_UNINSTALL_RETAIN in out
    assert "尚未删除任何数据" in out
    _assert_chinese_user_copy(out)
    plan = json.loads((out_dir / "uninstall_plan.json").read_text(encoding="utf-8"))
    assert plan["schema"] == dist.UNINSTALL_PLAN_SCHEMA
    assert plan["disposition_mode"] == "retain_project_data"
    assert plan["deletion_executed"] is False
    assert plan["future_delete_tool_required"] is True
    kinds = {item["kind"] for item in plan["retained_objects"]}
    assert kinds == {"project_data", "backups", "exports", "business_audit"}
    assert len(plan["plan_sha256"]) == 64
    assert int(plan["plan_sha256"], 16) >= 0
    assert "generated_at" in plan
    assert list(paths.data_dir.rglob("*")) == before
    assert sentinel.read_text(encoding="utf-8") == "retain"
    _assert_json_has_no_absolute_paths(plan)


def test_include_project_data_preview_still_does_not_delete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path)
    out_dir = tmp_path / "clear-preview"
    marker = paths.data_dir / "project.bin"
    marker.write_bytes(b"\x00\x01")
    code = dist.uninstall_plan_main(
        ["--include-project-data", "--output-dir", str(out_dir)], paths=paths
    )
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert dist.MSG_UNINSTALL_CLEAR in out
    assert "尚未删除任何数据" in out
    plan = json.loads((out_dir / "uninstall_plan.json").read_text(encoding="utf-8"))
    assert plan["disposition_mode"] == "include_project_data"
    assert plan["retained_objects"] == []
    assert plan["deletion_executed"] is False
    assert marker.is_file()
    assert marker.read_bytes() == b"\x00\x01"
    _assert_json_has_no_absolute_paths(plan)


def test_uninstall_plan_sha_ignores_generated_at(tmp_path: Path) -> None:
    paths = _make_distribution_root(tmp_path)
    a = dist.build_uninstall_plan(
        distribution_root=paths.root,
        data_dir=paths.data_dir,
        include_project_data=False,
    )
    time.sleep(1.05)
    b = dist.build_uninstall_plan(
        distribution_root=paths.root,
        data_dir=paths.data_dir,
        include_project_data=False,
    )
    assert a["plan_sha256"] == b["plan_sha256"]


def test_uninstall_requires_output_dir(tmp_path: Path) -> None:
    paths = _make_distribution_root(tmp_path)
    code = dist.uninstall_plan_main([], paths=paths)
    assert code == EXIT_PREFLIGHT_OR_ARGS


def test_root_identity_and_plan_sha256_differ_for_same_basename_distinct_roots(
    tmp_path: Path,
) -> None:
    root_a = tmp_path / "prefix-a" / "same-leaf"
    root_b = tmp_path / "prefix-b" / "same-leaf"
    data_a = root_a / "data"
    data_b = root_b / "data"
    data_a.mkdir(parents=True)
    data_b.mkdir(parents=True)
    plan_a = dist.build_uninstall_plan(
        distribution_root=root_a,
        data_dir=data_a,
        include_project_data=False,
    )
    plan_b = dist.build_uninstall_plan(
        distribution_root=root_b,
        data_dir=data_b,
        include_project_data=False,
    )
    assert root_a.name == root_b.name == "same-leaf"
    assert root_a.resolve() != root_b.resolve()
    assert plan_a["root_identity_digest"] != plan_b["root_identity_digest"]
    assert plan_a["plan_sha256"] != plan_b["plan_sha256"]
    _assert_json_has_no_absolute_paths(plan_a)
    _assert_json_has_no_absolute_paths(plan_b)
    assert plan_a["machine"]["distribution_root_name"] == "same-leaf"
    assert plan_b["machine"]["distribution_root_name"] == "same-leaf"


def _synthetic_runtime(tmp_path: Path, project_id: str = "proj-syn") -> Path:
    runtime_root = tmp_path / "runtime-root"
    runtime_root.mkdir()
    (runtime_root / ".mm_r7_synthetic").write_text("1\n", encoding="utf-8")
    make_project(runtime_root / project_id)
    return runtime_root


def test_prepare_upgrade_success_keeps_workspace_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-ok"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    workspace = runtime_root / project_id
    before = _fingerprint_workspace(workspace)
    code = dist.prepare_upgrade_main(
        ["--runtime-root", str(runtime_root), "--project-id", project_id]
    )
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert dist.MSG_UPGRADE_OK in out
    _assert_chinese_user_copy(out)
    assert _fingerprint_workspace(workspace) == before
    receipt = runtime_root / dist.PREPARE_STAGING_DIR / project_id / "receipt.json"
    assert receipt.is_file()
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["status"] == "ready"
    assert payload["compatibility"] in {"already_current", "legacy_upgradeable"}
    packages = list(runtime_root.rglob("*.mmbackup"))
    assert packages, "expected 09A backup package evidence"


def test_prepare_upgrade_compat_failure_keeps_backup_drops_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-bad"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    workspace = runtime_root / project_id
    before = _fingerprint_workspace(workspace)

    def _fail(_workspace: Path) -> Tuple[bool, str]:
        return False, "incompatible:corrupt:forced"

    monkeypatch.setattr(dist, "_compatibility_precheck", _fail)
    code = dist.prepare_upgrade_main(
        ["--runtime-root", str(runtime_root), "--project-id", project_id]
    )
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert code == EXIT_UPGRADE_PREP
    assert dist.MSG_UPGRADE_BLOCKED in text
    assert _fingerprint_workspace(workspace) == before
    staging = runtime_root / dist.PREPARE_STAGING_DIR / project_id
    assert not staging.exists()
    assert list(runtime_root.rglob("*.mmbackup")), "backup must be retained on compat block"


def test_prepare_upgrade_backup_failure_no_upgrade_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-backup-fail"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    workspace = runtime_root / project_id
    before = _fingerprint_workspace(workspace)

    class _Boom:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def backup(self, *_a: Any, **_k: Any) -> Any:
            from mm_r7.project_backup import ProjectBackupError

            raise ProjectBackupError("backup_failed_forced", "forced backup failure")

        @property
        def ledger(self) -> Any:
            class _L:
                def close(self) -> None:
                    return None

            return _L()

    import mm_r7.project_backup as pb

    monkeypatch.setattr(pb, "ProjectBackupManager", _Boom)
    code = dist.prepare_upgrade_main(
        ["--runtime-root", str(runtime_root), "--project-id", project_id]
    )
    captured = capsys.readouterr()
    assert code == EXIT_UPGRADE_PREP
    assert dist.MSG_UPGRADE_FAILED in (captured.out + captured.err)
    assert _fingerprint_workspace(workspace) == before
    staging = runtime_root / dist.PREPARE_STAGING_DIR / project_id
    assert not staging.exists()
    assert not list(runtime_root.rglob("*.mmbackup"))


def test_prepare_upgrade_concurrent_second_call_busy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-busy"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    gate = ProjectMaintenanceGate(runtime_root, project_id, wait_seconds=0.0)
    permit = gate.acquire(True)
    try:
        code = dist.prepare_upgrade_main(
            ["--runtime-root", str(runtime_root), "--project-id", project_id]
        )
        captured = capsys.readouterr()
        assert code == EXIT_MAINTENANCE_BUSY
        assert dist.MSG_UPGRADE_BUSY in (captured.out + captured.err)
        staging_root = runtime_root / dist.PREPARE_STAGING_DIR
        if staging_root.exists():
            children = [p for p in staging_root.iterdir() if p.is_dir()]
            assert children == [] or all(
                not (child / "in_progress.json").exists() for child in children
            )
    finally:
        permit.release()


def test_prepare_upgrade_concurrent_live_owner_second_call_busy_retains_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-live-owner"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    staging = runtime_root / dist.PREPARE_STAGING_DIR / project_id
    backup_started = threading.Event()
    allow_backup_finish = threading.Event()
    real_manager_cls = None

    class _SlowManager:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._inner = real_manager_cls(*args, **kwargs)

        def backup(self, idempotency_key: str):
            backup_started.set()
            assert allow_backup_finish.wait(timeout=5.0)
            return self._inner.backup(idempotency_key)

        @property
        def ledger(self):
            return self._inner.ledger

    import mm_r7.project_backup as pb

    real_manager_cls = pb.ProjectBackupManager
    monkeypatch.setattr(pb, "ProjectBackupManager", _SlowManager)

    first_result: Dict[str, Any] = {}

    def _first_call() -> None:
        first_result["code"] = dist.prepare_upgrade_main(
            ["--runtime-root", str(runtime_root), "--project-id", project_id]
        )

    worker = threading.Thread(target=_first_call, daemon=True)
    worker.start()
    assert backup_started.wait(timeout=5.0), "first prepare-upgrade did not reach backup"
    assert (staging / "in_progress.json").is_file()
    marker_before = (staging / "in_progress.json").read_text(encoding="utf-8")

    second_code = dist.prepare_upgrade_main(
        ["--runtime-root", str(runtime_root), "--project-id", project_id]
    )
    captured = capsys.readouterr()
    assert second_code == EXIT_MAINTENANCE_BUSY
    assert dist.MSG_UPGRADE_BUSY in (captured.out + captured.err)
    assert staging.is_dir()
    assert (staging / "in_progress.json").is_file()
    assert (staging / "in_progress.json").read_text(encoding="utf-8") == marker_before
    assert not (staging / "receipt.json").exists()

    allow_backup_finish.set()
    worker.join(timeout=30.0)
    assert not worker.is_alive()
    assert first_result.get("code") == EXIT_OK


def test_prepare_upgrade_reclaims_staging_when_owner_pid_is_dead(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project_id = "proj-dead-marker"
    runtime_root = _synthetic_runtime(tmp_path, project_id)
    staging = runtime_root / dist.PREPARE_STAGING_DIR / project_id
    staging.mkdir(parents=True)
    stale_marker = {
        "schema": "mm-monitoring-local-prepare-upgrade-staging-v1",
        "project_id": project_id,
        "idempotency_key": "stale",
        "status": "in_progress",
        "pid": 999_999_999,
    }
    (staging / "in_progress.json").write_text(
        json.dumps(stale_marker, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (staging / "stale-leftover.txt").write_text("orphan", encoding="utf-8")

    code = dist.prepare_upgrade_main(
        ["--runtime-root", str(runtime_root), "--project-id", project_id]
    )
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert dist.MSG_UPGRADE_OK in out
    assert (staging / "receipt.json").is_file()
    assert not (staging / "stale-leftover.txt").exists()
    assert not (staging / "in_progress.json").exists()


def test_acceptance_runner_rejects_non_synthetic_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MM_09E_ACCEPTANCE_RUNNER", "1")
    realish = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
    code = dist.prepare_upgrade_main(
        ["--runtime-root", str(realish), "--project-id", "nope"]
    )
    assert code == EXIT_PREFLIGHT_OR_ARGS


def test_acceptance_runner_rejects_non_temp_uninstall_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _make_distribution_root(tmp_path)
    monkeypatch.setenv("MM_09E_ACCEPTANCE_RUNNER", "1")
    out = WORKBENCH_ROOT / "artifacts" / "_09e_should_not_write"
    code = dist.uninstall_plan_main(["--output-dir", str(out)], paths=paths)
    assert code == EXIT_PREFLIGHT_OR_ARGS
    assert not out.exists()


def test_acceptance_runner_rejects_non_synthetic_uninstall_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = manage_mod.resolve_paths(WORKBENCH_ROOT / "deploy" / "medical_monitoring_local")
    monkeypatch.setenv("MM_09E_ACCEPTANCE_RUNNER", "1")
    out = tmp_path / "uninstall-out"
    code = dist.uninstall_plan_main(["--output-dir", str(out)], paths=paths)
    assert code == EXIT_PREFLIGHT_OR_ARGS
    assert not out.exists()


_DETERMINISM_PROBE = r"""
import json, sys
from pathlib import Path
wb = Path(sys.argv[1])
sys.path.insert(0, str(wb / "deploy" / "medical_monitoring_local"))
print(json.dumps({
    "manifest_sha256": __import__("distribution").build_release_manifest(workbench_root=wb)["manifest_sha256"],
    "uninstall_retain_sha256": __import__("distribution").build_uninstall_plan(
        distribution_root=wb / "deploy" / "medical_monitoring_local",
        data_dir=wb / "deploy" / "medical_monitoring_local" / "data",
        include_project_data=False,
    )["plan_sha256"],
    "uninstall_clear_sha256": __import__("distribution").build_uninstall_plan(
        distribution_root=wb / "deploy" / "medical_monitoring_local",
        data_dir=wb / "deploy" / "medical_monitoring_local" / "data",
        include_project_data=True,
    )["plan_sha256"],
}, sort_keys=True))
"""


def _run_determinism_probe(hash_seed: str, opt_flag: Tuple[str, ...]) -> Dict[str, str]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env.pop("PYTHONOPTIMIZE", None)
    proc = subprocess.run(
        [sys.executable, *opt_flag, "-c", _DETERMINISM_PROBE, str(WORKBENCH_ROOT)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(WORKBENCH_ROOT),
    )
    return json.loads(proc.stdout.strip())


@pytest.mark.parametrize("hash_seed", list(HASH_SEEDS))
@pytest.mark.parametrize("opt_flag", list(OPT_FLAGS))
def test_manifest_and_uninstall_plan_deterministic_matrix(
    hash_seed: str, opt_flag: Tuple[str, ...]
) -> None:
    payload = _run_determinism_probe(hash_seed, opt_flag)
    baseline = _run_determinism_probe("0", ())
    assert payload == baseline
    assert len(payload["manifest_sha256"]) == 64
    assert len(payload["uninstall_retain_sha256"]) == 64
    assert len(payload["uninstall_clear_sha256"]) == 64
    assert payload["uninstall_retain_sha256"] != payload["uninstall_clear_sha256"]


def test_medical_writing_local_untouched_boundary() -> None:
    assert MEDICAL_WRITING_LOCAL.is_dir()
    managed = {
        "manage.py",
        "manage.zsh",
        "distribution.py",
        "release_sources.json",
        "README.md",
    }
    monitoring_names = {p.name for p in DEPLOY_DIR.iterdir() if p.is_file()}
    writing_names = {p.name for p in MEDICAL_WRITING_LOCAL.iterdir() if p.is_file()}
    assert managed.issubset(monitoring_names)
    assert "distribution.py" not in writing_names
    writing_manage = MEDICAL_WRITING_LOCAL / "manage.zsh"
    assert writing_manage.is_file()
    assert (DEPLOY_DIR / "distribution.py").is_file()
    assert not (MEDICAL_WRITING_LOCAL / "distribution.py").exists()


def test_ports_remain_stopped_after_module_import() -> None:
    _assert_ports_stopped()


def test_manage_zsh_forwards_preflight() -> None:
    zsh = DEPLOY_DIR / "manage.zsh"
    assert zsh.is_file()
    text = zsh.read_text(encoding="utf-8")
    assert "manage.py" in text
    assert "医学监查" in text


def test_cli_uninstall_via_manage_main(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _make_distribution_root(tmp_path)
    out_dir = tmp_path / "via-manage"
    code = manage_mod.main(
        [
            "--root",
            str(paths.root),
            "uninstall-plan",
            "--output-dir",
            str(out_dir),
        ]
    )
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "尚未删除任何数据" in out
    assert (out_dir / "uninstall_plan.json").is_file()
