"""R8 G4 distribution/CLI focused tests (synthetic/offline).

Contract: context/medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1_20260831.md
Covers manage CLI wiring, release_sources inventory, Chinese user copy, synthetic-root
fail-closed gates, anti-overfit static scan, port boundary, and medical_writing isolation.

Does not start 8911/5174/8984, call models, read real project roots, or modify
deploy/medical_writing_local.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
MEDICAL_WRITING_LOCAL = WORKBENCH_ROOT / "deploy" / "medical_writing_local"
R7_SRC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "src"
R7_TESTS = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "tests"

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

PROTECTED_PORTS = (8911, 5174, 8984)
LEAK_TOKENS = ("8911", "5174", "8984", "sqlite", "PID", "pid=", str(WORKBENCH_ROOT))
G4_SOURCE_FILES = (
    DEPLOY_DIR / "synthetic_notification.py",
    DEPLOY_DIR / "synthetic_15_4.py",
)
ANTI_OVERFIT_FORBIDDEN = (
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "康哲",
    "Sheet1",
    "A1:",
    "利拉鲁肽",
    "2型糖尿病",
)
REQUIRED_RUNTIME_DEPENDENCIES = {
    "poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py",
    "poc/medical_monitoring_ai_native_r7/src/mm_r7/profile_store.py",
    "poc/medical_monitoring_ai_native_r7/src/mm_r7/project_verifier.py",
    "poc/medical_monitoring_ai_native_r7/src/mm_r7/run_binding.py",
    "poc/medical_monitoring_ai_native_r7/src/mm_r7/run_setup.py",
    "poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py",
    "poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/schema_shape.py",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py",
}


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


def _assert_chinese_user_copy(text: str) -> None:
    assert "合成离线" in text or "医学监查" in text
    lowered = text.lower()
    for token in LEAK_TOKENS:
        assert token.lower() not in lowered, f"user copy leaked {token!r}: {text!r}"


def _medical_writing_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(MEDICAL_WRITING_LOCAL.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(MEDICAL_WRITING_LOCAL).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def test_ports_stopped() -> None:
    _assert_ports_stopped()


def test_release_sources_lists_g4_modules_and_excludes_writing() -> None:
    payload = json.loads((DEPLOY_DIR / "release_sources.json").read_text(encoding="utf-8"))
    entries = set(payload["entries"])
    assert "deploy/medical_monitoring_local/synthetic_notification.py" in entries
    assert "deploy/medical_monitoring_local/synthetic_15_4.py" in entries
    assert "poc/medical_monitoring_ai_native_r7/tests/fixtures_schema_manifest.py" in entries
    assert {
        "poc/medical_monitoring_ai_native_r7/src/mm_r7",
        "poc/medical_monitoring_ai_native_r6/src/mm_r6",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5",
        "poc/medical_monitoring_ai_native_r4/src/mm_r4",
        "poc/medical_monitoring_ai_native_r3/src/mm_r3",
        "poc/medical_monitoring_ai_native_r3_rule_ai/src/mm_r3_rule_ai",
        "poc/medical_monitoring_ai_native_r2/src/mm_r2",
        "poc/medical_monitoring_ai_native_r1/src/mm_r1",
    } <= entries
    assert not any(item.startswith("deploy/medical_writing_local") for item in entries)
    excludes = payload["scope_declaration"]["excludes"]
    assert "deploy/medical_writing_local" in excludes
    contract = payload["contract_ref"]
    assert contract["r8_g3_notification_contract_version"] == "0.3"
    assert "r8_g4_15_4_implementation_contract" in contract


def test_release_manifest_builds_with_g4_entries() -> None:
    manifest = dist.build_release_manifest(workbench_root=WORKBENCH_ROOT)
    paths = {item["path"] for item in manifest["files"]}
    assert "deploy/medical_monitoring_local/synthetic_notification.py" in paths
    assert "deploy/medical_monitoring_local/synthetic_15_4.py" in paths
    assert "poc/medical_monitoring_ai_native_r7/tests/fixtures_schema_manifest.py" in paths
    assert REQUIRED_RUNTIME_DEPENDENCIES <= paths
    assert not any(path.startswith("deploy/medical_writing_local/") for path in paths)
    assert len(manifest["manifest_sha256"]) == 64


def test_release_inventory_runs_section_15_4_without_workbench_fallback(tmp_path: Path) -> None:
    manifest = dist.build_release_manifest(workbench_root=WORKBENCH_ROOT)
    release_root = tmp_path / "release"
    for item in manifest["files"]:
        relative = item["path"]
        source = WORKBENCH_ROOT / relative
        target = release_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    command = [
        sys.executable,
        "-c",
        (
            "import json, tempfile; from pathlib import Path; "
            "import synthetic_15_4 as s; "
            "root=Path(tempfile.mkdtemp(prefix='mm-release-closure-')); "
            "result=s.run_section_15_4(root, project_id='release-closure'); "
            "assert result['status']=='passed'; "
            "assert len(result['items'])==13; "
            "print(json.dumps({'status': result['status'], 'items': len(result['items'])}))"
        ),
    ]
    deploy = release_root / "deploy" / "medical_monitoring_local"
    completed = subprocess.run(
        command,
        cwd=str(release_root),
        env={"PYTHONPATH": str(deploy)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout.splitlines()[-1]) == {
        "status": "passed",
        "items": 13,
    }


def test_g4_sources_have_no_anti_overfit_literals() -> None:
    for path in G4_SOURCE_FILES:
        source = path.read_text(encoding="utf-8")
        for token in ANTI_OVERFIT_FORBIDDEN:
            assert token not in source, f"{path.name} contains forbidden token {token!r}"


def test_manage_g4_notification_one_click_without_root(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_called(_root: object = None) -> object:
        raise AssertionError("g4 notification must not resolve a distribution root")

    monkeypatch.setattr(manage_mod, "resolve_paths", fail_if_called)
    code = manage_mod.main(["synthetic-g4-notification"])
    out = capsys.readouterr().out
    assert code == manage_mod.EXIT_OK
    assert manage_mod.MSG_SYNTHETIC_G4_NOTIFICATION in out
    _assert_chinese_user_copy(out)
    _assert_ports_stopped()


def test_manage_g4_15_4_run_passes_in_temp_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = manage_mod.main(
        [
            "synthetic-g4-15-4",
            "run",
            "--runtime-root",
            str(tmp_path),
            "--project-id",
            "synth-g4-dist",
        ]
    )
    out = capsys.readouterr().out
    assert code == manage_mod.EXIT_OK
    assert manage_mod.MSG_SYNTHETIC_G4_15_4_PASSED in out
    _assert_chinese_user_copy(out)
    _assert_ports_stopped()


def test_manage_g4_15_4_rejects_distribution_root(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = manage_mod.main(
        [
            "synthetic-g4-15-4",
            "run",
            "--runtime-root",
            str(DEPLOY_DIR),
        ]
    )
    err = capsys.readouterr().err
    assert code == manage_mod.EXIT_PREFLIGHT_OR_ARGS
    assert "临时合成工作区" in err
    _assert_ports_stopped()


def test_manage_g4_15_4_rejects_marked_non_temporary_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside = WORKBENCH_ROOT / ".synthetic-g4-forbidden"
    monkeypatch.setattr(manage_mod.tempfile, "gettempdir", lambda: str(tmp_path))
    assert manage_mod.main(
        ["synthetic-g4-15-4", "run", "--runtime-root", str(outside)]
    ) == manage_mod.EXIT_PREFLIGHT_OR_ARGS
    assert not outside.exists()


def test_manage_g4_15_4_replay_via_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import synthetic_15_4 as s154  # noqa: WPS433

    manifest = s154.run_section_15_4(tmp_path, project_id="synth-g4-replay")
    payload = tmp_path / "manifest.json"
    payload.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    code = manage_mod.main(
        [
            "synthetic-g4-15-4",
            "replay",
            str(payload),
            "--strict",
        ]
    )
    out = capsys.readouterr().out
    assert code == manage_mod.EXIT_OK
    assert "replay 已通过" in out
    _assert_ports_stopped()


def test_manage_zsh_forwards_g4_notification() -> None:
    completed = subprocess.run(
        [str(DEPLOY_DIR / "manage.zsh"), "synthetic-g4-notification"],
        cwd=str(WORKBENCH_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert manage_mod.MSG_SYNTHETIC_G4_NOTIFICATION in completed.stdout
    _assert_ports_stopped()


def test_medical_writing_local_boundary_unchanged() -> None:
    assert MEDICAL_WRITING_LOCAL.is_dir()
    writing_names = {p.name for p in MEDICAL_WRITING_LOCAL.iterdir() if p.is_file()}
    assert "distribution.py" not in writing_names
    assert not (MEDICAL_WRITING_LOCAL / "distribution.py").exists()
    assert not (MEDICAL_WRITING_LOCAL / "synthetic_notification.py").exists()
    assert not (MEDICAL_WRITING_LOCAL / "synthetic_15_4.py").exists()
    assert len(_medical_writing_fingerprint()) == 64
