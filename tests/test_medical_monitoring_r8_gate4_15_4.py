"""R8 G4 §15.4 synthetic orchestration focused tests (synthetic/offline).

Contract: context/medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1_20260831.md
Covers thirteen fixed-order checks, canonical manifest digest, independent replay,
tamper rejection, and boundary gates.

Does not start 8911/5174/8984, call models, read real project roots, or modify
deploy/medical_writing_local.
"""

from __future__ import annotations

import copy
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Tuple

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
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

import synthetic_15_4 as s154  # noqa: E402

PROJECT_ID = "synth-154-test"
HASH_SEEDS = ("0", "1", "42")
OPT_FLAGS: Tuple[Tuple[str, ...], ...] = ((), ("-O",), ("-OO",))


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def test_ports_stopped() -> None:
    for port in (8911, 5174, 8984):
        assert _port_connect_ex(port) != 0


def test_item_specs_fixed_thirteen_in_order() -> None:
    assert len(s154.ITEM_SPECS) == 13
    for index, spec in enumerate(s154.ITEM_SPECS, start=1):
        assert spec["index"] == index
    keys = [spec["key"] for spec in s154.ITEM_SPECS]
    assert len(keys) == len(set(keys))


def test_run_section_15_4_all_items_pass_in_temp_root(tmp_path: Path) -> None:
    manifest = s154.run_section_15_4(tmp_path, project_id=PROJECT_ID)
    assert manifest["schema"] == s154.SECTION_15_4_SCHEMA
    assert manifest["status"] == s154.RESULT_PASSED
    assert len(manifest["items"]) == 13
    assert all(item["result"] == s154.RESULT_PASSED for item in manifest["items"])
    validated = s154.validate_evidence_manifest(manifest)
    assert validated["manifest_digest"] == manifest["manifest_digest"]
    replay = s154.replay_section_15_4(manifest)
    assert replay.valid is True
    assert replay.status == s154.RESULT_PASSED


def test_run_section_15_4_rejects_non_temporary_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    outside = WORKBENCH_ROOT / ".synthetic-15-4-forbidden"
    monkeypatch.setattr(s154.tempfile, "gettempdir", lambda: str(tmp_path))
    with pytest.raises(s154.Section154Error, match="runtime_root_not_temporary"):
        s154.run_section_15_4(outside, project_id=PROJECT_ID)
    assert not outside.exists()


@pytest.mark.parametrize("project_id", ("../escape", "/absolute", "bad/name", ""))
def test_run_section_15_4_rejects_unsafe_project_id(tmp_path: Path, project_id: str) -> None:
    with pytest.raises(s154.Section154Error, match="project_id"):
        s154.run_section_15_4(tmp_path / "safe-root", project_id=project_id)
    assert not (tmp_path / "escape").exists()


def test_explicit_clear_requires_matching_plan_and_preserves_cancel(tmp_path: Path) -> None:
    import distribution as dist

    root = tmp_path / "clear"
    s154._mark_synthetic_root(root)
    paths = s154._make_distribution_root(root)
    sentinel = paths.data_dir / "sentinel.bin"
    sentinel.write_bytes(b"retain-on-cancel")
    plan = dist.build_uninstall_plan(
        distribution_root=paths.root,
        data_dir=paths.data_dir,
        include_project_data=True,
    )
    assert s154._apply_synthetic_clear(
        paths.root, paths.data_dir, plan, confirmed=False
    ) == "cancelled"
    assert sentinel.read_bytes() == b"retain-on-cancel"

    tampered = dict(plan)
    tampered["plan_sha256"] = "0" * 64
    with pytest.raises(s154.Section154Error, match="clear_plan_mismatch"):
        s154._apply_synthetic_clear(
            paths.root, paths.data_dir, tampered, confirmed=True
        )
    assert sentinel.exists()

    assert s154._apply_synthetic_clear(
        paths.root, paths.data_dir, plan, confirmed=True
    ) == "confirmed_and_cleared"
    assert not paths.data_dir.exists()


@pytest.mark.parametrize("tamper", ("manifest_digest", "item_summary", "item_order", "item_result"))
def test_replay_rejects_tampered_manifest(tmp_path: Path, tamper: str) -> None:
    manifest = s154.run_section_15_4(tmp_path, project_id=PROJECT_ID)
    mutated = copy.deepcopy(manifest)
    if tamper == "manifest_digest":
        mutated["manifest_digest"] = "sha256:" + ("f" * 64)
    elif tamper == "item_summary":
        mutated["items"][2]["summary"] = "被篡改摘要"
        mutated["items"][2]["item_digest"] = "sha256:" + ("a" * 64)
    elif tamper == "item_order":
        mutated["items"] = list(reversed(mutated["items"]))
    else:
        mutated["items"][0]["result"] = s154.RESULT_FAILED
        mutated["items"][0]["summary"] = "被篡改的结果摘要"
        mutated["status"] = s154.RESULT_FAILED
    replay = s154.replay_section_15_4(mutated)
    assert replay.valid is False
    assert replay.errors


def test_overall_status_fails_when_any_item_not_passed() -> None:
    items = [
        s154._passed(spec, "test:ref", "合成摘要通过")
        for spec in s154.ITEM_SPECS[:-1]
    ]
    items.append(
        s154._failed(s154.ITEM_SPECS[-1], "test:ref", "最后一项失败")
    )
    manifest = s154.build_evidence_manifest(items)
    assert manifest["status"] == s154.RESULT_FAILED
    replay = s154.replay_section_15_4(manifest)
    assert replay.valid is True
    assert replay.status == s154.RESULT_FAILED


def test_summaries_contain_no_paths() -> None:
    manifest = s154.build_evidence_manifest(
        [s154._passed(spec, "test:ref", "仅含中文与模块引用") for spec in s154.ITEM_SPECS]
    )
    for item in manifest["items"]:
        assert "/" not in item["summary"]
        assert "\\" not in item["summary"]


def test_manifest_digest_deterministic_across_pythonhashseed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digests = set()
    for seed in HASH_SEEDS:
        case = tmp_path / f"seed-{seed}"
        monkeypatch.setenv("PYTHONHASHSEED", seed)
        manifest = s154.run_section_15_4(case, project_id=PROJECT_ID)
        digests.add(manifest["manifest_digest"])
    assert len(digests) == 1


def test_subprocess_replay_matches_inprocess(tmp_path: Path) -> None:
    manifest = s154.run_section_15_4(tmp_path, project_id=PROJECT_ID)
    payload = tmp_path / "manifest.json"
    payload.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, %r)\n"
        "import synthetic_15_4 as s154\n"
        "data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))\n"
        "result = s154.replay_section_15_4(data)\n"
        "print(json.dumps(result.as_dict(), ensure_ascii=False))\n"
    ) % str(DEPLOY_DIR)
    completed = subprocess.run(
        [sys.executable, "-c", script, str(payload)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload_result = json.loads(completed.stdout.strip())
    assert payload_result["valid"] is True


@pytest.mark.parametrize("optimize", OPT_FLAGS)
def test_subprocess_run_is_deterministic_for_digest(
    tmp_path: Path, optimize: Tuple[str, ...]
) -> None:
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, %r)\n"
        "import synthetic_15_4 as s154\n"
        "manifest = s154.run_section_15_4(Path(sys.argv[1]), project_id=%r)\n"
        "print(manifest['manifest_digest'])\n"
    ) % (str(DEPLOY_DIR), PROJECT_ID)
    digests = set()
    for index in range(2):
        case = tmp_path / ("opt-%d-%s" % (index, "none" if not optimize else optimize[0].replace("-", "")))
        command = [sys.executable, *optimize, "-c", script, str(case)]
        digest = subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()
        digests.add(digest)
    assert len(digests) == 1
