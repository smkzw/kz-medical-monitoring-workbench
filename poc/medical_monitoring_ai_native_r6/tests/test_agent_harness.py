"""R6 slice-07 Agent Harness offline acceptance matrix (worker_03 lead).

Covers contract §7 offline determinism, fail-closed gates, argv/receipt
coverage, adjacent protection, and PYTHONHASHSEED/-O/-OO identity stability.
Controlled real-model smokes are executed outside pytest and recorded in
``evidence/r6_agent_harness_runtime_receipt.json``.
"""

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
from typing import Any, Optional

import pytest

from mm_r6 import agent_harness as ah
from mm_r6 import contracts

POC_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = POC_ROOT / "src"
WORKBENCH_ROOT = contracts.WORKBENCH_ROOT

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 542
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
)
PROTECTED_PORTS = (8911, 5174)

SLICE07_CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "src/mm_r6/report_review.py",
        "src/mm_r6/report_bundle.py",
        "src/mm_r6/mode_output.py",
        "src/mm_r6/agent_harness.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "tests/test_report_review.py",
        "tests/test_report_bundle.py",
        "tests/test_mode_output.py",
        "tests/test_agent_harness.py",
        "evidence/r6_contract_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
        "README.md",
    }
)

REQUIRED_HARNESS_APIS = (
    "ALIAS_REGISTRY",
    "OmpPrintAdapter",
    "freeze_default_mtplx_profile",
    "freeze_deepseek_flash_max_profile",
    "freeze_execution_profile",
    "merge_profile_layers",
    "resolve_alias",
    "project_user_progress",
    "evaluate_analysis_complete",
    "synthetic_catalog_for_provider",
    "sanitize_text",
    "content_digest",
)


class _FakeProc:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
        timeout: bool = False,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self._timeout = timeout
        self.pid = 4242

    def communicate(self, input: Any = None, timeout: Optional[float] = None):
        if self._timeout and not getattr(self, "_timed_once", False):
            self._timed_once = True
            raise subprocess.TimeoutExpired(cmd=["omp"], timeout=timeout or 0)
        return self._stdout, self._stderr

    def poll(self):
        return self.returncode

    def wait(self, timeout: Optional[float] = None):
        return self.returncode

    def terminate(self) -> None:
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


def _adapter_with_catalog(provider_payloads=None, popen=None, executable="/usr/bin/true"):
    payloads = provider_payloads or {
        "mtplx": ah.synthetic_catalog_for_provider("mtplx"),
        "deepseek": ah.synthetic_catalog_for_provider("deepseek"),
    }

    def loader(provider: str):
        return payloads.get(provider, {"models": []})

    return ah.OmpPrintAdapter(
        executable=executable,
        catalog_loader=loader,
        popen_factory=popen,
    )


def _factory(stdout: bytes, code, timeout: bool = False):
    def factory(*_a, **_k):
        return _FakeProc(stdout=stdout, returncode=code, timeout=timeout)

    return factory


def _poc_files() -> set:
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        if "__pycache__" in rel.split("/") or ".pytest_cache" in rel.split("/"):
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
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
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


# ---------------------------------------------------------------------------
# API surface + profile identity
# ---------------------------------------------------------------------------


def test_required_harness_apis_present():
    missing = [name for name in REQUIRED_HARNESS_APIS if not hasattr(ah, name)]
    assert missing == []


def test_default_mtplx_and_deepseek_identities_exact():
    mtplx = ah.freeze_default_mtplx_profile(run_id="offline-matrix")
    deepseek = ah.freeze_deepseek_flash_max_profile(run_id="offline-matrix")
    assert mtplx.profile_id == ah.PROFILE_DEFAULT_ID
    assert mtplx.user_config_name == ah.USER_NAME_MTPLX
    assert mtplx.effective_selector == ah.EFFECTIVE_SELECTOR_MTPLX
    assert mtplx.reasoning_effort == "medium"
    assert mtplx.adapter_id == ah.ADAPTER_ID
    assert mtplx.fallback_profile_ids == ()
    assert deepseek.profile_id == ah.PROFILE_DEEPSEEK_ID
    assert deepseek.user_config_name == ah.USER_NAME_DEEPSEEK
    assert deepseek.effective_selector == ah.EFFECTIVE_SELECTOR_DEEPSEEK
    assert deepseek.reasoning_effort == "max"
    assert deepseek.fallback_profile_ids == ()
    assert mtplx.execution_profile_digest != deepseek.execution_profile_digest


def test_unknown_alias_fail_closed():
    with pytest.raises(ah.AgentHarnessError, match="unknown_alias"):
        ah.resolve_alias("mtplx/not-a-real-model")


def test_fail_closed_effort_capability_timeout_tools():
    with pytest.raises(ah.AgentHarnessError, match="illegal_effort"):
        ah.freeze_execution_profile(ah.ExecutionProfileLayer(reasoning_effort="ultra"))
    with pytest.raises(ah.AgentHarnessError, match="empty_capability_id"):
        ah.freeze_execution_profile(ah.ExecutionProfileLayer(capability_id=""))
    with pytest.raises(ah.AgentHarnessError, match="illegal_timeout"):
        ah.freeze_execution_profile(ah.ExecutionProfileLayer(timeout_seconds=0))
    with pytest.raises(ah.AgentHarnessError, match="tool_overreach"):
        ah.freeze_execution_profile(
            ah.ExecutionProfileLayer(allowed_tools=("read", "bash"))
        )
    with pytest.raises(ah.AgentHarnessError, match="effort_profile_inconsistent"):
        ah.freeze_execution_profile(ah.ExecutionProfileLayer(reasoning_effort="max"))


def test_profile_id_only_rebases_registered_template():
    frozen = ah.freeze_execution_profile(
        ah.ExecutionProfileLayer(profile_id=ah.PROFILE_DEEPSEEK_ID)
    )
    assert frozen.effective_selector == ah.EFFECTIVE_SELECTOR_DEEPSEEK
    assert frozen.reasoning_effort == "max"


# ---------------------------------------------------------------------------
# Catalog / preflight / argv
# ---------------------------------------------------------------------------


def test_catalog_public_fields_only_no_secrets():
    dirty = ah.synthetic_catalog_for_provider("mtplx")
    dirty["models"][0]["api_key"] = "sk-SECRET-SHOULD-NOT-LEAK"
    dirty["models"][0]["env"] = {"OMP_API_KEY": "leak"}
    adapter = _adapter_with_catalog({"mtplx": dirty})
    public = adapter.catalog_snapshot("mtplx").to_public_dict()
    blob = json.dumps(public)
    assert "sk-SECRET" not in blob
    assert "OMP_API_KEY" not in blob
    assert "api_key" not in blob
    assert "medium" in public["models"][0]["thinking"]


def test_catalog_deepseek_supports_max():
    model = _adapter_with_catalog().catalog_snapshot("deepseek").find_selector(
        ah.EFFECTIVE_SELECTOR_DEEPSEEK
    )
    assert model is not None
    assert "max" in model.thinking


def test_preflight_ok_and_selector_missing():
    adapter = _adapter_with_catalog()
    ok = adapter.preflight(ah.freeze_default_mtplx_profile())
    assert ok.ok is True
    bad = _adapter_with_catalog({"mtplx": {"models": []}})
    result = bad.preflight(ah.freeze_default_mtplx_profile())
    assert result.ok is False
    assert "selector_not_in_catalog" in result.reasons


def test_preflight_rejects_forged_identity_and_catalog_provider():
    frozen = ah.freeze_default_mtplx_profile()
    forged = ah.FrozenExecutionProfile(
        **{**frozen.__dict__, "execution_profile_digest": "0" * 64}
    )
    adapter = _adapter_with_catalog()
    assert adapter.preflight(forged).ok is False

    dirty = ah.synthetic_catalog_for_provider("mtplx")
    dirty["models"][0]["provider"] = "other"
    result = _adapter_with_catalog({"mtplx": dirty}).preflight(frozen)
    assert result.ok is False
    assert "catalog_model_provider_mismatch" in result.reasons

    dirty = ah.synthetic_catalog_for_provider("mtplx")
    dirty["models"][0]["id"] = "other-model"
    result = _adapter_with_catalog({"mtplx": dirty}).preflight(frozen)
    assert result.ok is False
    assert "catalog_model_id_mismatch" in result.reasons


def test_argv_no_shell_no_prompt_flags_exact():
    adapter = _adapter_with_catalog()
    mtplx = ah.freeze_default_mtplx_profile()
    argv = adapter.build_start_command(mtplx, executable="/usr/bin/true")
    assert argv[0] == "/usr/bin/true"
    assert ah.EFFECTIVE_SELECTOR_MTPLX in argv
    assert argv[argv.index("--thinking") + 1] == "medium"
    assert "--mode" in argv and "json" in argv
    assert "--print" in argv
    assert "--no-session" in argv and "--no-skills" in argv and "--no-rules" in argv
    assert argv[argv.index("--tools") + 1] == "read"
    assert "&&" not in " ".join(argv)
    assert argv[-1] == str(mtplx.timeout_seconds)
    ds_argv = adapter.build_start_command(
        ah.freeze_deepseek_flash_max_profile(), executable="/usr/bin/true"
    )
    assert ah.EFFECTIVE_SELECTOR_DEEPSEEK in ds_argv
    assert ds_argv[ds_argv.index("--thinking") + 1] == "max"


# ---------------------------------------------------------------------------
# Invoke / receipt / coverage / JSONL
# ---------------------------------------------------------------------------


def test_invoke_complete_sets_analysis_complete(tmp_path: Path):
    payload = {"unit_a": 1, "unit_b": 2, "produced_units": ["unit_a", "unit_b"]}
    adapter = _adapter_with_catalog(
        popen=_factory(json.dumps(payload).encode("utf-8"), 0)
    )
    receipt = adapter.invoke(
        ah.freeze_default_mtplx_profile(run_id="inv1"),
        prompt="synthetic non-medical ping",
        output_dir=tmp_path,
        expected_units=["unit_a", "unit_b"],
    )
    assert receipt.state == "complete"
    assert receipt.parse_state == "parsed"
    assert receipt.missing_units == ()
    assert receipt.analysis_complete is True
    assert receipt.fallback_used is False
    blob = json.dumps(receipt.to_public_dict())
    assert "api_key" not in blob.lower()
    assert "sk-" not in blob


def test_invoke_rejects_preflight_bypass_and_unsafe_identity(tmp_path: Path):
    profile = ah.freeze_default_mtplx_profile()
    injected = ah.PreflightResult(
        ok=True,
        executable="/usr/bin/true",
        selector=ah.EFFECTIVE_SELECTOR_DEEPSEEK,
        effort="max",
        allowed_tools=("read",),
        timeout_seconds=profile.timeout_seconds,
    )
    adapter = _adapter_with_catalog(
        popen=_factory(json.dumps({"produced_units": ["u1"]}).encode(), 0)
    )
    receipt = adapter.invoke(
        profile,
        prompt="offline",
        output_dir=tmp_path,
        expected_units=["u1"],
        preflight_result=injected,
    )
    assert receipt.state == "failed"
    assert receipt.analysis_complete is False
    with pytest.raises(ah.AgentHarnessError, match="invalid_invocation_id"):
        adapter.invoke(
            profile,
            prompt="offline",
            output_dir=tmp_path,
            expected_units=["u1"],
            invocation_id="../escape",
        )
    with pytest.raises(ah.AgentHarnessError, match="invalid_expected_units"):
        adapter.invoke(
            profile,
            prompt="offline",
            output_dir=tmp_path,
            expected_units=["u1", "u1"],
        )


def test_receipt_state_matrix_fail_closed(tmp_path: Path):
    cases = (
        (
            "gap",
            json.dumps({"produced_units": ["unit_a"]}).encode(),
            0,
            False,
            "partial",
        ),
        (
            "trunc",
            json.dumps({"state": "truncated", "produced_units": ["unit_a"]}).encode(),
            0,
            False,
            "truncated",
        ),
        ("badjson", b"{", 0, False, "failed"),
        ("empty", b"", 1, False, "failed"),
        ("timeout", b"", None, True, "timed_out"),
        (
            "partial_hint",
            json.dumps(
                {"status": "partial", "produced_units": ["unit_a", "unit_b"]}
            ).encode(),
            0,
            False,
            "partial",
        ),
    )
    for label, stdout, code, timeout, exp_state in cases:
        adapter = _adapter_with_catalog(popen=_factory(stdout, code, timeout))
        receipt = adapter.invoke(
            ah.freeze_default_mtplx_profile(),
            prompt="offline",
            output_dir=tmp_path / label,
            expected_units=["unit_a", "unit_b"],
        )
        assert receipt.state == exp_state, label
        assert receipt.analysis_complete is False, label
        assert receipt.fallback_used is False, label


def test_omp_jsonl_stdout_classifies_complete(tmp_path: Path):
    events = "\n".join(
        [
            json.dumps({"type": "session", "id": "x"}),
            json.dumps(
                {
                    "type": "message_start",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    '{"smoke_unit":"ok",'
                                    '"produced_units":["smoke_unit"]}'
                                ),
                            }
                        ],
                    },
                }
            ),
        ]
    )
    adapter = _adapter_with_catalog(popen=_factory(events.encode("utf-8"), 0))
    receipt = adapter.invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="synthetic",
        output_dir=tmp_path,
        expected_units=["smoke_unit"],
    )
    assert receipt.state == "complete"
    assert receipt.parse_state == "parsed"
    assert receipt.analysis_complete is True


def _assistant_event(text: str) -> str:
    return json.dumps(
        {
            "type": "message_end",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
            },
        }
    )


def test_omp_jsonl_last_valid_assistant_object_wins(tmp_path: Path):
    events = "\n".join(
        [
            json.dumps({"type": "session", "id": "x"}),
            _assistant_event('{"produced_units":["smoke_unit"]}'),
            _assistant_event('{"produced_units":[],"final":"retracted"}'),
        ]
    )
    receipt = _adapter_with_catalog(
        popen=_factory(events.encode("utf-8"), 0)
    ).invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="synthetic",
        output_dir=tmp_path,
        expected_units=["smoke_unit"],
    )
    assert receipt.state == "partial"
    assert receipt.analysis_complete is False


def test_omp_jsonl_ignores_incidental_json_in_prose(tmp_path: Path):
    events = "\n".join(
        [
            json.dumps({"type": "session", "id": "x"}),
            _assistant_event(
                'I failed. toy {"produced_units":["smoke_unit"]} not my answer.'
            ),
        ]
    )
    receipt = _adapter_with_catalog(
        popen=_factory(events.encode("utf-8"), 0)
    ).invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="synthetic",
        output_dir=tmp_path,
        expected_units=["smoke_unit"],
    )
    assert receipt.state == "partial"
    assert receipt.analysis_complete is False


def test_single_omp_event_envelope_extracts_assistant_payload(tmp_path: Path):
    event = _assistant_event(
        '{"smoke_unit":"ok","produced_units":["smoke_unit"]}'
    )
    receipt = _adapter_with_catalog(
        popen=_factory(event.encode("utf-8"), 0)
    ).invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="synthetic",
        output_dir=tmp_path,
        expected_units=["smoke_unit"],
    )
    assert receipt.state == "complete"
    assert receipt.analysis_complete is True


def test_exit_code_none_never_completes(tmp_path: Path):
    receipt = _adapter_with_catalog(
        popen=_factory(
            json.dumps({"produced_units": ["smoke_unit"]}).encode(), None
        )
    ).invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="synthetic",
        output_dir=tmp_path,
        expected_units=["smoke_unit"],
    )
    assert receipt.state == "failed"
    assert receipt.analysis_complete is False


def test_prompt_on_stdin_not_argv_and_no_shell(tmp_path: Path):
    seen: dict = {}

    def factory(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["shell"] = kwargs.get("shell")
        return _FakeProc(
            stdout=json.dumps({"produced_units": ["u1"]}).encode(),
            returncode=0,
        )

    adapter = _adapter_with_catalog(popen=factory)
    prompt = "UNIQUE_PROMPT_TOKEN_NOT_ON_ARGV"
    adapter.invoke(
        ah.freeze_default_mtplx_profile(),
        prompt=prompt,
        output_dir=tmp_path,
        expected_units=["u1"],
    )
    assert seen["shell"] is False
    assert all(prompt not in str(tok) for tok in seen["argv"])


def test_stderr_redaction_and_unsupported_lifecycle(tmp_path: Path):
    adapter = _adapter_with_catalog(
        popen=_factory(
            json.dumps({"produced_units": ["u1"]}).encode(),
            0,
        )
    )
    # Force stderr via custom factory
    def factory(*_a, **_k):
        return _FakeProc(
            stdout=json.dumps({"produced_units": ["u1"]}).encode(),
            stderr=b"Authorization: Bearer sk-ABCDEFGHIJKLMNOP password=supersecret",
            returncode=0,
        )

    adapter = _adapter_with_catalog(popen=factory)
    receipt = adapter.invoke(
        ah.freeze_default_mtplx_profile(),
        prompt="ping",
        output_dir=tmp_path,
        expected_units=["u1"],
    )
    assert "sk-ABCDEF" not in receipt.stderr_summary
    assert "supersecret" not in receipt.stderr_summary
    assert "[REDACTED]" in receipt.stderr_summary
    bare = _adapter_with_catalog()
    assert bare.continue_session()["status"] == "unsupported"
    assert bare.resume_session()["status"] == "unsupported"
    assert bare.cancel()["status"] == "unsupported"


def test_user_progress_projection_no_internal_terms():
    with pytest.raises(ah.AgentHarnessError, match="progress_leaks_internal_term"):
        ah.project_user_progress(
            completed_nodes=1,
            total_nodes=2,
            current_work="calling deepseek model",
            result_available=False,
        )
    proj = ah.project_user_progress(
        completed_nodes=1,
        total_nodes=2,
        current_work="正在生成监查摘要",
        result_available=True,
    )
    blob = json.dumps(proj, ensure_ascii=False).lower()
    for term in ("provider", "model", "selector", "effort", "adapter", "mtplx", "omp"):
        assert term not in blob


# ---------------------------------------------------------------------------
# Determinism matrix (hash seed × optimizer)
# ---------------------------------------------------------------------------

_REPRO_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from mm_r6 import agent_harness as ah
mtplx = ah.freeze_default_mtplx_profile(run_id="repro")
deepseek = ah.freeze_deepseek_flash_max_profile(run_id="repro")
adapter = ah.OmpPrintAdapter(
    executable="/usr/bin/true",
    catalog_loader=ah.synthetic_catalog_for_provider,
)
print(json.dumps({
    "mtplx_digest": mtplx.execution_profile_digest,
    "mtplx_id": mtplx.execution_profile_id,
    "deepseek_digest": deepseek.execution_profile_digest,
    "deepseek_id": deepseek.execution_profile_id,
    "argv_m": adapter.build_start_command(mtplx, executable="/usr/bin/true"),
    "argv_d": adapter.build_start_command(deepseek, executable="/usr/bin/true"),
}, sort_keys=True))
"""


@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
@pytest.mark.parametrize("opt_flag", [(), ("-O",), ("-OO",)])
def test_identity_and_argv_deterministic_matrix(hash_seed, opt_flag):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [sys.executable, *opt_flag, "-c", _REPRO_PROBE, str(SRC_DIR)]
    proc = subprocess.run(
        cmd, check=True, capture_output=True, text=True, env=env, cwd=str(POC_ROOT)
    )
    payload = json.loads(proc.stdout.strip())
    baseline = json.loads(
        subprocess.run(
            [sys.executable, "-c", _REPRO_PROBE, str(SRC_DIR)],
            check=True,
            capture_output=True,
            text=True,
            env={**env, "PYTHONHASHSEED": "0"},
            cwd=str(POC_ROOT),
        ).stdout.strip()
    )
    assert payload == baseline
    assert payload["mtplx_digest"] != payload["deepseek_digest"]
    assert "medium" in payload["argv_m"]
    assert "max" in payload["argv_d"]


# ---------------------------------------------------------------------------
# Adjacent protection
# ---------------------------------------------------------------------------


def test_medical_writing_aggregate_unchanged():
    boundary = _medical_writing_boundary(WORKBENCH_ROOT)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


def test_slice07_create_only_allowlist():
    found = _poc_files()
    optional_receipts = {
        "evidence/r6_agent_harness_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
    }
    extras = found - SLICE07_CREATE_ONLY_RELATIVE
    missing_required = (SLICE07_CREATE_ONLY_RELATIVE - optional_receipts) - found
    assert extras == set(), f"unexpected POC files: {sorted(extras)}"
    assert missing_required == set(), f"missing required: {sorted(missing_required)}"


def test_adjacent_modules_importable_product_untouched():
    from mm_r6 import mode_output as mo
    from mm_r6 import report_bundle as rb
    from mm_r6 import report_review as rr

    assert hasattr(rr, "build_report_review_matrix")
    assert hasattr(rb, "build_report_review_bundle")
    assert hasattr(mo, "build_mode_output")
    assert (WORKBENCH_ROOT / "services").is_dir()
    assert (WORKBENCH_ROOT / "frontend").is_dir()
    assert not (POC_ROOT / "real_projects").exists()
