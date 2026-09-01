"""Focused R8 G6 actual-entry, frozen-manifest, and lifecycle checks.

These tests stay offline: they validate the bundle and deterministic lifecycle
replay, and exercise failure paths before a server bind.  Browser/visual and
full synthetic fixture acceptance are separate governed packets.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest


WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import actual_app as app  # noqa: E402
import g6_manifests as manifests  # noqa: E402


@pytest.fixture()
def frozen_manifests() -> dict[str, dict[str, object]]:
    return manifests.load_all_manifests(base_dir=DEPLOY_DIR, release_root=DEPLOY_DIR)


def test_frozen_manifests_validate_against_actual_bundle(frozen_manifests: dict[str, dict[str, object]]) -> None:
    entry = frozen_manifests["entry"]
    assert entry["schema"] == manifests.ENTRY_SCHEMA
    assert entry["entry"]["type"] == "macos_application_bundle"
    assert entry["entry"]["relative_path"] == "MedicalMonitoring.app"
    assert entry["entry"]["executable_relative_path"].endswith("Contents/MacOS/MedicalMonitoring")
    assert entry["window_identity"]["identity"] == "medical-monitoring-synthetic"

    boundary = frozen_manifests["execution_boundary"]
    assert boundary["synthetic_only"] is True
    assert boundary["network"]["allow_dns"] is False
    assert boundary["network"]["allow_external"] is False
    assert boundary["owned_process_tree"]["allow_orphan_adoption"] is False

    viewport = frozen_manifests["viewport_layout"]
    dimensions = {
        (row["css_viewport"]["width"], row["css_viewport"]["height"])
        for row in viewport["viewports"]
    }
    assert dimensions == {(1920, 1080), (2560, 1440), (3840, 2160)}
    assert viewport["baseline_state"] == "frozen_before_visual_baseline"
    assert viewport["browser_zoom_percent"] == 100


def test_manifest_self_digest_and_bundle_digest_are_not_placeholders(
    frozen_manifests: dict[str, dict[str, object]],
) -> None:
    for payload in frozen_manifests.values():
        assert payload["manifest_digest"].startswith("sha256:")
        assert "PLACEHOLDER" not in json.dumps(payload, ensure_ascii=False)
    entry = frozen_manifests["entry"]["entry"]
    assert entry["file_digest"].startswith("sha256:")
    assert entry["directory_digest"].startswith("sha256:")
    assert frozen_manifests["execution_boundary"]["synthetic_binding"]["binding_digest"].startswith("sha256:")


def test_manifest_tampering_fails_closed(frozen_manifests: dict[str, dict[str, object]]) -> None:
    tampered = copy.deepcopy(frozen_manifests["execution_boundary"])
    tampered["network"]["allow_external"] = True
    with pytest.raises(manifests.ManifestError, match="manifest_digest_mismatch"):
        manifests.validate_execution_boundary_manifest(tampered)


def test_boundary_rejects_non_loopback_and_adapter_fallback(
    frozen_manifests: dict[str, dict[str, object]],
) -> None:
    non_loopback = copy.deepcopy(frozen_manifests["execution_boundary"])
    non_loopback["network"]["allowed_endpoints"][0]["host"] = "example.invalid"
    with pytest.raises(manifests.ManifestError, match="manifest_digest_mismatch"):
        manifests.validate_execution_boundary_manifest(non_loopback)

    fallback = copy.deepcopy(frozen_manifests["execution_boundary"])
    fallback["adapters"][0]["fallback"] = True
    with pytest.raises(manifests.ManifestError, match="manifest_digest_mismatch"):
        manifests.validate_execution_boundary_manifest(fallback)


def test_viewport_manifest_enforces_three_wide_contract(
    frozen_manifests: dict[str, dict[str, object]],
) -> None:
    tampered = copy.deepcopy(frozen_manifests["viewport_layout"])
    tampered["viewports"][0]["css_viewport"]["width"] = 1280
    with pytest.raises(manifests.ManifestError, match="manifest_digest_mismatch"):
        manifests.validate_viewport_layout_manifest(tampered)


def test_actual_app_self_check_is_non_running_and_user_safe() -> None:
    completed = subprocess.run(
        [sys.executable, str(DEPLOY_DIR / "actual_app.py"), "--self-check"],
        cwd=str(WORKBENCH_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == "医学监查工作台版本校验通过。"
    assert completed.stderr == ""


def test_bundle_is_the_entry_not_manager_or_terminal_alias() -> None:
    executable = DEPLOY_DIR / "MedicalMonitoring.app" / "Contents" / "MacOS" / "MedicalMonitoring"
    assert executable.is_file()
    assert executable.stat().st_mode & 0o111
    text = executable.read_text(encoding="utf-8")
    assert "actual_app.py" in text
    assert "manage.py" not in text
    assert "8911" not in text
    assert "5174" not in text
    assert "8984" not in text


@pytest.mark.parametrize("scenario", app.SCENARIOS)
def test_all_nine_lifecycle_scenarios_have_closed_outcomes(scenario: str) -> None:
    evidence = app.run_lifecycle_scenario(scenario)
    assert evidence["schema"] == app.LIFECYCLE_SCHEMA
    assert evidence["scenario"] == scenario
    assert evidence["postconditions"]["unknown_process_adopted"] is False
    if scenario in {"cold_start", "duplicate_start", "restart"}:
        assert evidence["status"] == "ready"
        assert evidence["postconditions"]["owned_processes"] == 1
    elif scenario == "orphan_before_start":
        assert evidence["status"] == "blocked"
        assert evidence["postconditions"]["can_cold_start_again"] is False
    elif scenario == "normal_close":
        assert evidence["status"] == "stopped"
        assert evidence["postconditions"]["owned_processes"] == 0
        assert evidence["postconditions"]["loopback_listeners"] == 0
    else:
        assert evidence["status"] == "failed"
        assert evidence["postconditions"]["owned_processes"] == 0
        assert evidence["postconditions"]["loopback_listeners"] == 0


def test_lifecycle_replay_is_independent_and_tamper_rejects() -> None:
    evidence = app.run_lifecycle_scenario("restart")
    replay = app.replay_lifecycle_evidence(evidence, strict=True)
    assert replay.status == "valid"

    tampered = copy.deepcopy(evidence)
    tampered["events"][2]["run_reused"] = False
    with pytest.raises(app.ActualAppError):
        app.replay_lifecycle_evidence(tampered, strict=True)


def test_fault_injection_cleans_before_ready_without_binding_service(tmp_path: Path) -> None:
    for fault, expected in (
        ("main_crash", app.MSG_MAIN_FAILED),
        ("ready_timeout", app.MSG_READY_TIMEOUT),
        ("health_failure", app.MSG_HEALTH_FAILED),
    ):
        runtime_root = tmp_path / fault
        controller = app.LifecycleController(
            runtime_root=runtime_root,
            require_window=False,
        )
        result = controller.start(fault=fault)
        assert result.status == "failed"
        assert result.message == expected
        assert not (runtime_root / "app_state.json").exists()
        # The lock inode is retained deliberately to avoid an unlock/unlink
        # race; no process or listener remains.


def test_missing_static_surface_blocks_actual_start(tmp_path: Path) -> None:
    controller = app.LifecycleController(runtime_root=tmp_path / "missing-surface", require_window=False)
    result = controller.start()
    assert result.status == "failed"
    assert result.message == app.MSG_START_FAILED
    assert result.machine["reason"] == "static_surface_missing"
    assert result.machine["cleaned"] is True
    assert not controller.paths.state_path.exists()


def test_runtime_root_outside_closed_set_is_rejected() -> None:
    with pytest.raises(app.ActualAppError, match="运行目录不可用"):
        app.LifecycleController(runtime_root=WORKBENCH_ROOT, require_window=False)


def test_duplicate_actual_entry_is_successful_focus(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class ExistingController:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def start(self, *, fault: object = None) -> app.LifecycleResult:
            return app.LifecycleResult("focused_existing", app.MSG_FOCUSED, {"reason": "duplicate_start"})

    monkeypatch.setattr(app, "LifecycleController", ExistingController)
    assert app.main(["--launch", "--no-browser"]) == 0
    assert capsys.readouterr().out.strip() == app.MSG_FOCUSED


def test_live_unknown_state_is_blocked_without_adoption(tmp_path: Path) -> None:
    runtime_root = tmp_path / "orphan"
    runtime_root.mkdir()
    (runtime_root / "app_state.json").write_text(
        json.dumps(
            {
                "schema": app.STATE_SCHEMA,
                "app_schema": manifests.APP_SCHEMA,
                "protocol_version": app.APP_PROTOCOL_VERSION,
                "status": "starting",
                "pid": 1,
                "port": 8946,
            }
        ),
        encoding="utf-8",
    )
    controller = app.LifecycleController(runtime_root=runtime_root, require_window=False)
    result = controller.start()
    assert result.status == "blocked"
    assert result.message == app.MSG_ORPHAN_BLOCKED
    assert (runtime_root / "app_state.json").exists()
