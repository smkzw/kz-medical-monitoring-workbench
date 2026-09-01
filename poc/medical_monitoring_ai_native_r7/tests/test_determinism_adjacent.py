"""R7 slice-01/08D determinism and adjacent R6/boundary protection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import POC_ROOT, SRC_DIR, WORKBENCH_ROOT

R6_POC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r6"
R6_SRC = R6_POC / "src"

R6_PINNED_SHA256 = {
    "src/mm_r6/agent_harness.py": (
        "0546c10c51a57795c521b2f605276e02c06c676bfe8625268863d8ddc961a515"
    ),
    "src/mm_r6/__init__.py": (
        "644def45333cc3e04b7f334948f2fc7a13573e3bab82bcd806175c7fff786af3"
    ),
    "tests/test_agent_harness.py": (
        "57326dced117c1ae29499b265bdd7a1859ae375e05b56e094843725141147155"
    ),
    "evidence/r6_agent_harness_runtime_receipt.json": (
        "fd61f5483360476d4f76d6a9f61642fe83aa69799a64f7aefb36cd44c126d98d"
    ),
}

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 443
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "394746881c0b8b312805ee6e22047f6e32b66559d76987a7337ab151ed04a1c1"
)
PROTECTED_PORTS = (8911, 5174, 8984)

R7_CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r7/__init__.py",
        "src/mm_r7/profile_store.py",
        "src/mm_r7/run_binding.py",
        "src/mm_r7/run_entry.py",
        "src/mm_r7/api.py",
        "src/mm_r7/runtime_progress.py",
        "src/mm_r7/background_recovery.py",
        "src/mm_r7/harness_runtime.py",
        "src/mm_r7/migration.py",
        "src/mm_r7/project_lifecycle.py",
        "src/mm_r7/schema_manifest.py",
        "src/mm_r7/launch_schema.py",
        "src/mm_r7/run_setup.py",
        "src/mm_r7/launch_registry.py",
        "src/mm_r7/continuity.py",
        "src/mm_r7/continuity_bridge.py",
        "src/mm_r7/maintenance_gate.py",
        "src/mm_r7/project_backup.py",
        "src/mm_r7/project_audit.py",
        "src/mm_r7/project_verifier.py",
        "src/mm_r7/technical_log.py",
        "src/mm_r7/root_ledger_schema.py",
        "tests/conftest.py",
        "tests/fake_harness.py",
        "tests/test_profile_store.py",
        "tests/test_run_binding.py",
        "tests/test_determinism_adjacent.py",
        "tests/test_run_entry.py",
        "tests/test_api.py",
        "tests/test_runtime_progress.py",
        "tests/test_background_recovery.py",
        "tests/test_harness_runtime.py",
        "tests/fixtures_run_setup.py",
        "tests/test_run_setup.py",
        "tests/test_launch_registry.py",
        "tests/test_continuity.py",
        "tests/test_continuity_registry.py",
        "tests/test_continuity_bridge.py",
        "tests/test_slice08d_three_mode_matrix.py",
        "tests/test_project_backup.py",
        "tests/fixtures_schema_manifest.py",
        "tests/test_project_lifecycle.py",
        "tests/test_schema_manifest.py",
        "tests/test_schema_migration.py",
        "tests/test_project_backup_adversarial.py",
        "tests/test_project_audit.py",
        "tests/test_project_verifier.py",
        "tests/test_technical_log.py",
        "evidence/r7_execution_profile_run_binding_receipt.json",
        "evidence/r7_product_api_run_entry_receipt.json",
        "evidence/r7_product_mount_receipt.json",
        "evidence/r7_durable_progress_receipt.json",
        "evidence/r7_background_recovery_receipt.json",
        "evidence/r7_harness_attempt_recovery_receipt.json",
        "evidence/r7_slice07c1_run_setup_receipt.json",
        "evidence/r7_slice07c2_prepare_start_receipt.json",
        "README.md",
    }
)

_REPRO_PROBE = r"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from mm_r7 import run_binding as rb

db = Path(tempfile.mkdtemp()) / "repro.sqlite3"
binder = rb.RunBindingStore(db)
mtplx = rb.freeze_default_mtplx_effective_profile(run_id="repro")
deepseek = rb.freeze_deepseek_flash_max_effective_profile(run_id="repro")
binding = binder.bind(
    run_id="run-repro-bind",
    project_id="proj-repro",
    mode="daily",
    execution_basis="full",
    data_cutoff="cutoff-sha256:repro",
    source_revision_id="src-sha256:repro",
    frozen=mtplx,
    prior_accepted_snapshot_ref=None,
)
print(json.dumps({
    "mtplx_digest": mtplx.execution_profile_digest,
    "mtplx_id": mtplx.execution_profile_id,
    "deepseek_digest": deepseek.execution_profile_digest,
    "deepseek_id": deepseek.execution_profile_id,
    "binding_digest": binding.binding_digest,
    "effective_profile_digest": binding.execution_profile_digest,
}, sort_keys=True))
binder.close()
"""

# Slice-08D §13: same input-side fixture across PYTHONHASHSEED × -O/-OO.
_CONTINUITY_REPRO_PROBE = r"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from uuid import UUID
from mm_r7.continuity import build_carry_forward_item, build_carry_forward_plan
import mm_r7.launch_registry as launch_registry
from mm_r7.launch_registry import (
    BASIS_FULL,
    CONTINUITY_PLAN_STATE_VERIFIED,
    LaunchRegistry,
    LaunchRegistryError,
    content_digest,
)

# Pin uuid4 so run_id/publication identity stay byte-stable across hash seeds.
_FIXED_UUID = UUID("01234567-89ab-cdef-0123-456789abcdef")
launch_registry.uuid4 = lambda: _FIXED_UUID

PROJECT_ID = "synthetic-r7-07c1-project"
NOW = "2026-08-29T04:00:00.000+00:00"
db = Path(tempfile.mkdtemp()) / "continuity-repro.sqlite3"
registry = LaunchRegistry(db, project_id=PROJECT_ID)
try:
    launch = registry.reserve(
        PROJECT_ID,
        idempotency_key="08d-determinism-key",
        mode="daily",
        execution_basis=BASIS_FULL,
        current_snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
        comparison_range="合成完整范围",
    )
    item = build_carry_forward_item(
        {
            "object_type": "risk_instance",
            "object_ref": "risk-001",
            "data_change_kind": "revised",
            "reason": "本轮数据修订变化",
            "target_run_id": launch.run_id,
            "target_project_id": PROJECT_ID,
            "target_mode": "daily",
        }
    )
    plan = build_carry_forward_plan(
        project_id=PROJECT_ID,
        mode="daily",
        execution_basis=BASIS_FULL,
        target_run_id=launch.run_id,
        target_snapshot_id="snapshot-target",
        target_data_cutoff="2026-08-29",
        target_decision_version="decision-target",
        r5_authority_digest="r5-target",
        r6_publication_digest="r6-target",
        r6_receipt_digest="receipt-target",
        r6_output_set_digest="6" * 64,
        items=(item,),
        created_at=NOW,
    )
    staged = registry.save_continuity_plan(plan)
    verified = registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
    publication = registry.reserve_publication(
        PROJECT_ID,
        launch.run_id,
        idempotency_key="publication-" + launch.run_id,
        request_fingerprint="r6-target",
        snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
    )
    registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
    members = ("art-1", "art-2", "art-3", "art-4")
    member_set_digest = content_digest(list(members))
    finalized = registry.finalize_publication(
        PROJECT_ID,
        launch.run_id,
        r5_authority_packet_digest="r5-target",
        receipt_set_digest="receipt-target",
        r6_output_set_digest="6" * 64,
        artifact_member_ids=members,
        artifact_member_set_digest=member_set_digest,
    )
    stable_error = None
    try:
        registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r6_output_set_digest="1" * 64,
        )
    except LaunchRegistryError as exc:
        stable_error = exc.code
    public = {
        "plan_digest": staged.plan_digest,
        "verified_status": verified.status,
        "item_digests": [entry.item_digest for entry in staged.items],
        "item_ordinals": [entry.ordinal for entry in staged.items],
        "publication_id": publication.publication_id,
        "publication_fingerprint": publication.request_fingerprint,
        "final_state": finalized.publication_state,
        "r6_output_set_digest": finalized.r6_output_set_digest,
        "artifact_member_set_digest": finalized.artifact_member_set_digest,
        "artifact_member_ids": list(finalized.artifact_member_ids),
        "result_available": registry.get(
            launch.run_id, project_id=PROJECT_ID
        ).result_available,
        "continuity_status": registry.get_continuity_plan(
            PROJECT_ID, launch.run_id
        ).status,
        "history_count": len(registry.list_history(PROJECT_ID)),
        "stable_error": stable_error,
        "verified_equals_expected": (
            verified.status == CONTINUITY_PLAN_STATE_VERIFIED
            or verified.status == "published"
        ),
    }
    print(json.dumps(public, sort_keys=True, ensure_ascii=False))
finally:
    registry.close()
"""

_SLICE09C_REPRO_PROBE = r"""
import hashlib, json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

src = Path(sys.argv[1])
sys.path.insert(0, str(src))
sys.path.insert(0, str(src.parent / "tests"))
workbench = src.parents[2]
for revision in ("r6", "r5", "r4", "r3", "r3_rule_ai", "r2", "r1"):
    adjacent = workbench / "poc" / ("medical_monitoring_ai_native_" + revision) / "src"
    if adjacent.exists():
        sys.path.insert(0, str(adjacent))
from fixtures_schema_manifest import make_project
from mm_r7.project_audit import ProjectAuditLedger
from mm_r7.project_verifier import ProjectVerifier
from mm_r7.technical_log import BoundedTechnicalLogHandler

root = Path(tempfile.mkdtemp())
project_id = "slice09c-repro"
workspace = root / project_id
make_project(workspace)

event_ids = iter(("event-started", "event-completed"))
ledger = ProjectAuditLedger(
    root,
    clock=lambda: "2026-08-30T12:00:00Z",
    event_id_factory=lambda: next(event_ids),
)
started = ledger.append_event(
    project_id,
    "verification_started",
    {
        "verifier_version": "verifier-v1",
        "snapshot_fingerprint": "snapshot-09c",
        "before_digest": "before-09c",
    },
    principal_snapshot_hash="p" * 64,
    authorization_decision_hash="a" * 64,
)
completed = ledger.append_event(
    project_id,
    "verification_completed",
    {
        "verifier_version": "verifier-v1",
        "snapshot_fingerprint": "snapshot-09c",
        "verification_result": "record_complete",
    },
    principal_snapshot_hash="p" * 64,
    authorization_decision_hash="a" * 64,
)
chain = ledger.verify_chain(project_id)
ledger.close()

verifier = ProjectVerifier(root, project_id, project_dir=workspace)
fingerprint = verifier.snapshot_fingerprint()
verifier.close()

log_root = root / "technical-runtime"
handler = BoundedTechnicalLogHandler(
    log_root,
    clock=lambda: datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc),
)
written = handler.log_event(
    severity="info",
    component="audit",
    event="append",
    outcome="ok",
    duration_ms=1,
)
if not written:
    raise RuntimeError("technical_log_write_failed")
log_bytes = handler.active_path.read_bytes()
print(json.dumps({
    "started_payload_hash": started.payload_hash,
    "started_chain_hash": started.chain_hash,
    "completed_payload_hash": completed.payload_hash,
    "completed_chain_hash": completed.chain_hash,
    "chain": list(chain),
    "snapshot_fingerprint": fingerprint,
    "technical_log_sha256": hashlib.sha256(log_bytes).hexdigest(),
    "technical_log": json.loads(log_bytes),
}, sort_keys=True, ensure_ascii=False))
"""

_HASH_SEEDS_08D = ("0", "1", "17", "42", "31415926")
_OPT_FLAGS_08D = ((), ("-O",), ("-OO",))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _poc_files() -> set:
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        parts = rel.split("/")
        if "__pycache__" in parts or ".pytest_cache" in parts:
            continue
        if rel.endswith(".pyc"):
            continue
        found.add(rel)
    return found


def _medical_writing_boundary(root: Path) -> dict:
    matched = {}
    errors = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        base = root / root_relative
        if not base.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, dirnames, filenames in os.walk(
            base, topdown=True, followlinks=False
        ):
            dirnames[:] = [
                name for name in dirnames if name not in {"__pycache__", ".pytest_cache"}
            ]
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                if filename.endswith(".pyc"):
                    continue
                path = Path(directory) / filename
                relative = path.relative_to(root).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(
                        f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}"
                    )
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched[relative] = (
                        hashlib.sha256(path.read_bytes()).hexdigest().lower()
                    )
                except (OSError, UnicodeError) as exc:
                    errors.append(
                        f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}"
                    )
    aggregate = hashlib.sha256()
    for relative in sorted(matched, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "file_count": len(matched),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def _run_probe(
    probe: str,
    *,
    hash_seed: str,
    opt_flag: tuple,
    env_overrides: dict[str, str] | None = None,
) -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env.pop("PYTHONOPTIMIZE", None)
    env.update(env_overrides or {})
    cmd = [
        sys.executable,
        *opt_flag,
        "-c",
        probe,
        str(SRC_DIR),
        str(R6_SRC),
    ]
    proc = subprocess.run(
        cmd, check=True, capture_output=True, text=True, env=env, cwd=str(POC_ROOT)
    )
    return json.loads(proc.stdout.strip())


@pytest.mark.parametrize("hash_seed", list(_HASH_SEEDS_08D))
@pytest.mark.parametrize("opt_flag", list(_OPT_FLAGS_08D))
def test_effective_and_binding_digest_deterministic_matrix(hash_seed, opt_flag):
    payload = _run_probe(_REPRO_PROBE, hash_seed=hash_seed, opt_flag=opt_flag)
    baseline = _run_probe(_REPRO_PROBE, hash_seed="0", opt_flag=())
    assert payload == baseline
    assert payload["mtplx_digest"] != payload["deepseek_digest"]
    assert payload["binding_digest"]
    assert payload["binding_digest"] == (
        "1164d4e1d05cef028f7edce530f03c38c699de07517414ea62ee326182b59e71"
    )
    assert payload["effective_profile_digest"] == payload["mtplx_digest"]


@pytest.mark.parametrize("hash_seed", list(_HASH_SEEDS_08D))
@pytest.mark.parametrize("opt_flag", list(_OPT_FLAGS_08D))
def test_continuity_plan_publication_deterministic_15_grid(hash_seed, opt_flag):
    """08D fixed 15-cell grid: seeds × normal/-O/-OO in independent subprocesses."""
    payload = _run_probe(
        _CONTINUITY_REPRO_PROBE, hash_seed=hash_seed, opt_flag=opt_flag
    )
    baseline = _run_probe(_CONTINUITY_REPRO_PROBE, hash_seed="0", opt_flag=())
    assert payload == baseline
    assert payload["plan_digest"]
    assert payload["item_digests"]
    assert payload["item_ordinals"] == sorted(payload["item_ordinals"])
    assert payload["final_state"] == "available"
    assert payload["result_available"] is True
    assert payload["continuity_status"] == "published"
    assert payload["history_count"] == 1
    assert payload["stable_error"] in (
        "publication_cas_conflict",
        "continuity_publication_conflict",
    )
    assert len(payload["artifact_member_ids"]) == 4
    assert payload["artifact_member_ids"] == sorted(payload["artifact_member_ids"])


@pytest.mark.parametrize("hash_seed", list(_HASH_SEEDS_08D))
@pytest.mark.parametrize("opt_flag", list(_OPT_FLAGS_08D))
def test_slice09c_audit_fingerprint_and_jsonl_deterministic_15_grid(
    hash_seed,
    opt_flag,
):
    index = _HASH_SEEDS_08D.index(hash_seed)
    environments = (
        {"TZ": "UTC", "LANG": "C", "LC_ALL": "C"},
        {"TZ": "Asia/Shanghai", "LANG": "POSIX", "LC_ALL": "POSIX"},
        {"TZ": "America/New_York", "LANG": "C", "LC_ALL": "C"},
    )
    payload = _run_probe(
        _SLICE09C_REPRO_PROBE,
        hash_seed=hash_seed,
        opt_flag=opt_flag,
        env_overrides=environments[index % len(environments)],
    )
    baseline = _run_probe(
        _SLICE09C_REPRO_PROBE,
        hash_seed="0",
        opt_flag=(),
        env_overrides=environments[0],
    )
    assert payload == baseline
    assert payload["chain"] == [True, None, 2]
    assert payload["snapshot_fingerprint"]
    assert payload["technical_log"]["segment_bytes"] > 0


def test_r6_pinned_sources_unchanged():
    for rel, expected in R6_PINNED_SHA256.items():
        path = R6_POC / rel
        assert path.is_file(), f"missing R6 pin target: {rel}"
        assert _sha256_file(path) == expected, f"R6 bytes changed: {rel}"


def test_medical_writing_aggregate_unchanged():
    boundary = _medical_writing_boundary(WORKBENCH_ROOT)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


def test_r7_create_only_allowlist():
    found = _poc_files()
    optional = {"evidence/r7_execution_profile_run_binding_receipt.json"}
    extras = found - R7_CREATE_ONLY_RELATIVE
    missing_required = (R7_CREATE_ONLY_RELATIVE - optional) - found
    assert extras == set(), f"unexpected POC files: {sorted(extras)}"
    assert missing_required == set(), f"missing required: {sorted(missing_required)}"


def test_adjacent_r6_importable_product_untouched():
    from mm_r6 import agent_harness as ah
    from mm_r6 import mode_output as mo

    assert hasattr(ah, "freeze_execution_profile")
    assert hasattr(mo, "build_mode_output")
    assert (WORKBENCH_ROOT / "services").is_dir()
    assert (WORKBENCH_ROOT / "frontend").is_dir()
    assert not (POC_ROOT / "real_projects").exists()
