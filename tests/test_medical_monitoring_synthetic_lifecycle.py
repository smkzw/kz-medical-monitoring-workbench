"""R8 G2 synthetic/offline one-click lifecycle tests.

The adapter is memory-only.  These tests never read a project root, call a
model, start a service, or bind an operating-system endpoint.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import manage as manage_mod  # noqa: E402
import synthetic_lifecycle as sl  # noqa: E402


@pytest.mark.parametrize(
    ("scenario", "status", "postcondition"),
    [
        ("start-stop-restart", "ready", "ready"),
        ("ready", "ready", "ready"),
        ("failure", "failed", "stopped"),
        ("partial", "partial", "partial"),
        ("foreign-ownership", "foreign_ownership", "foreign_ownership"),
    ],
)
def test_all_lifecycle_outcomes_are_adapter_driven(
    scenario: str, status: str, postcondition: str
) -> None:
    evidence = sl.run_synthetic_lifecycle(scenario)

    assert evidence["synthetic"] is True
    assert evidence["offline"] is True
    assert evidence["adapter"]["id"] == sl.ADAPTER_ID
    assert evidence["adapter"]["state_store"] == "memory"
    assert evidence["final"]["status"] == status
    assert evidence["final"]["postcondition_status"] == postcondition
    assert evidence["checks"]["external_processes_started"] == 0
    assert evidence["checks"]["network_calls"] == 0
    assert evidence["checks"]["model_calls"] == 0
    assert evidence["checks"]["filesystem_reads"] == 0
    assert evidence["checks"]["filesystem_writes"] == 0
    assert evidence["checks"]["no_half_initialized_state"] is True
    assert sl.replay_synthetic_lifecycle(evidence, strict=True).valid is True


def test_start_stop_restart_has_ready_stop_and_restart_steps() -> None:
    evidence = sl.run_synthetic_lifecycle("start-stop-restart")

    assert [step["operation"] for step in evidence["steps"]] == [
        "start",
        "stop",
        "restart",
    ]
    assert [step["status"] for step in evidence["steps"]] == [
        "ready",
        "stopped",
        "ready",
    ]
    assert evidence["final"]["ready_signal"] is True
    assert evidence["final"]["failure_signal"] is False
    assert evidence["checks"]["manual_endpoint_configuration"] is False


def test_failure_signal_rolls_back_every_started_endpoint() -> None:
    adapter = sl.SyntheticLifecycleAdapter(failure_endpoint="frontend")

    result = adapter.start()

    assert result["status"] == "failed"
    assert result["signal"] == "failure"
    assert result["failure_signal"] is True
    assert result["postcondition_status"] == "stopped"
    assert result["rollback_complete"] is True
    assert result["after"] == {endpoint: "stopped" for endpoint in sl.ENDPOINTS}
    assert any(event["kind"] == "rollback_complete" for event in adapter.events)


def test_partial_and_foreign_ownership_fail_closed_without_mutation() -> None:
    partial = sl.SyntheticLifecycleAdapter(initial_states={"backend": "ready"})
    partial_before = partial.states
    partial_result = partial.start()
    assert partial_result["status"] == "partial"
    assert partial_result["reason"] == "partial_runtime"
    assert partial.states == partial_before

    foreign = sl.SyntheticLifecycleAdapter(foreign_endpoints=("backend",))
    foreign_before = foreign.states
    foreign_result = foreign.restart()
    assert foreign_result["status"] == "foreign_ownership"
    assert foreign_result["reason"] == "foreign_ownership"
    assert foreign_result["foreign_preserved"] is True
    assert foreign.states == foreign_before


def test_replay_rejects_tampering_even_when_digest_is_resigned() -> None:
    evidence = sl.run_synthetic_lifecycle("ready")
    tampered = json.loads(json.dumps(evidence, ensure_ascii=False))
    tampered["final"]["status"] = "failed"
    tampered["lifecycle_digest"] = sl.digest_ref(
        {**tampered, "lifecycle_digest": ""}
    )

    replay = sl.replay_synthetic_lifecycle(tampered)

    assert replay.valid is False
    assert "scenario_replay_mismatch" in replay.errors
    with pytest.raises(sl.SyntheticLifecycleError, match="scenario_replay_mismatch"):
        sl.replay_synthetic_lifecycle(tampered, strict=True)


def test_cli_run_and_independent_replay_are_json_only(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DEPLOY_DIR / "synthetic_lifecycle.py"),
            "run",
            "--scenario",
            "start-stop-restart",
        ],
        cwd=str(WORKBENCH_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    evidence = json.loads(completed.stdout)
    assert evidence["final"]["status"] == "ready"

    evidence_path = tmp_path / "synthetic-lifecycle.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
    replay = subprocess.run(
        [
            sys.executable,
            str(DEPLOY_DIR / "synthetic_lifecycle.py"),
            "replay",
            str(evidence_path),
            "--strict",
        ],
        cwd=str(WORKBENCH_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert replay.returncode == 0
    assert replay.stderr == ""
    result = json.loads(replay.stdout)
    assert result == {
        "errors": [],
        "scenario": "start-stop-restart",
        "status": "ready",
        "valid": True,
    }


def test_synthetic_module_has_no_protected_runtime_literals() -> None:
    source = (DEPLOY_DIR / "synthetic_lifecycle.py").read_text(encoding="utf-8")
    for forbidden in ("8911", "5174", "8984", "socket", "subprocess"):
        assert forbidden not in source

def test_manage_one_click_does_not_resolve_or_read_a_root(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    def fail_if_called(_root: object = None) -> object:
        raise AssertionError("synthetic command must not resolve a distribution root")

    monkeypatch.setattr(manage_mod, "resolve_paths", fail_if_called)

    code = manage_mod.main(
        [
            "--root",
            str(tmp_path / "not-a-real-distribution"),
            "synthetic-lifecycle",
            "--scenario",
            "foreign-ownership",
        ]
    )

    assert code == 0
    assert "外部归属拒绝信号" in capsys.readouterr().out


def test_manage_one_click_does_not_read_runtime_or_root_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class GuardedEnvironment(dict):
        def get(self, key: object, *args: object, **kwargs: object) -> object:
            forbidden = {
                "MM_MONITORING_LOCAL_ROOT",
                "MM_MONITORING_OFFLINE",
                "MM_PYTHON",
                "MM_NODE",
                "VITE_API_BASE_URL",
            }
            if str(key) in forbidden:
                raise AssertionError("synthetic lifecycle must not read runtime environment variables")
            return super().get(key, *args, **kwargs)

    monkeypatch.setattr(manage_mod.os, "environ", GuardedEnvironment(manage_mod.os.environ))

    code = manage_mod.main(["synthetic-lifecycle", "--scenario", "ready"])

    assert code == 0
    assert "就绪信号" in capsys.readouterr().out


def test_repeated_start_is_idempotent_and_keeps_ready_signal() -> None:
    adapter = sl.SyntheticLifecycleAdapter()

    first = adapter.start()
    second = adapter.start()

    assert first["status"] == "ready"
    assert second["status"] == "ready"
    assert second["reason"] == "already_ready"
    assert second["changed"] is False
    assert second["after"] == first["after"]
