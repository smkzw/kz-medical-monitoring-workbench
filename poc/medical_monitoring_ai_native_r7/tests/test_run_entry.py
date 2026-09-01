"""R7 slice-02 MonitoringRunEntry / ProductRunEntry contract tests (worker_03).

Accepts both dataclass envelopes (``BootstrapResult`` / ``BindRunResult``) and
plain public dicts so mid-pass peer API churn does not invalidate the gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

from conftest import POC_ROOT, SRC_DIR, WORKBENCH_ROOT

R6_SRC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r6" / "src"

from mm_r7 import profile_store as ps  # noqa: E402
from mm_r7 import run_entry as re  # noqa: E402

REQUIRED_RUN_ENTRY_APIS = (
    "RunEntryError",
    "MonitoringRunEntry",
    "ProductRunEntry",
    "RunEntry",
    "API_PREFIX",
    "BUILTIN_DEFAULT_USER_CONFIG_NAME",
    "BUILTIN_DEFAULT_REASONING_EFFORT",
)

REQUIRED_ENTRY_METHODS = (
    "bootstrap_workspace",
    "append_execution_profile",
    "get_execution_profile",
    "resolve_scope_layers",
    "freeze_effective_profile_for_scopes",
    "bind_run",
    "get_run",
    "reopen_and_validate_run",
    "close",
    "reopen",
)

MTPLX_CONFIG = "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
DEEPSEEK_CONFIG = "deepseek/DeepSeek V4 flash"

FORBIDDEN_RESPONSE_TOKENS = (
    "credential_value",
    "sk-",
    "modeoutput",
    "risk_instance",
    "patientjourney",
    "query_draft",
    "canonical_fact",
    "report_claim",
    "super-secret-value",
)

_REPRO_PROBE = r"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from mm_r7 import run_entry as re

ws = Path(tempfile.mkdtemp()) / "ws"
ws.mkdir()
Entry = getattr(re, "MonitoringRunEntry", None) or re.ProductRunEntry
entry = Entry(ws)

def public(result):
    if isinstance(result, dict):
        return dict(result)
    binding = getattr(result, "binding", None)
    if isinstance(binding, dict):
        body = dict(binding)
        body["replayed"] = bool(getattr(result, "replayed", False))
        body["binding_digest"] = getattr(result, "binding_digest", body.get("binding_digest"))
        return body
    profile = getattr(result, "profile", None)
    if isinstance(profile, dict):
        body = dict(profile)
        if hasattr(result, "replayed"):
            body["replayed"] = bool(result.replayed)
        if hasattr(result, "revision"):
            body["revision"] = result.revision
        if hasattr(result, "record_id"):
            body["record_id"] = result.record_id
        return body
    raise TypeError(type(result))

first = public(entry.bootstrap_workspace())
second = public(entry.bootstrap_workspace())
entry.append_execution_profile(
    "project",
    "proj-repro",
    {"timeout_seconds": 90, "credential_ref": "env:OMP_CREDENTIAL_REF"},
)
bound = public(entry.bind_run(
    run_id="run-repro-s02",
    project_id="proj-repro",
    mode="daily",
    execution_basis="full",
    data_cutoff="cutoff-sha256:repro-s02",
    source_revision_id="src-sha256:repro-s02",
    prior_accepted_snapshot_ref=None,
    project_scope_key="proj-repro",
))
again = public(entry.bind_run(
    run_id="run-repro-s02",
    project_id="proj-repro",
    mode="daily",
    execution_basis="full",
    data_cutoff="cutoff-sha256:repro-s02",
    source_revision_id="src-sha256:repro-s02",
    prior_accepted_snapshot_ref=None,
    project_scope_key="proj-repro",
))
got = entry.get_run("run-repro-s02")
entry.close()
print(json.dumps({
    "bootstrap_first_replayed": bool(first.get("replayed")),
    "bootstrap_second_replayed": bool(second.get("replayed")),
    "bootstrap_revision": first.get("revision"),
    "bootstrap_revision_replay": second.get("revision"),
    "bootstrap_record_id": first.get("record_id"),
    "bind_first_replayed": bool(bound.get("replayed")),
    "bind_second_replayed": bool(again.get("replayed")),
    "binding_digest": bound.get("binding_digest"),
    "binding_digest_replay": again.get("binding_digest"),
    "run_id": got.get("run_id"),
    "user_config_name": got.get("user_config_name"),
    "mode": got.get("mode"),
    "execution_basis": got.get("execution_basis"),
}, sort_keys=True, ensure_ascii=False))
"""


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _entry_cls():
    return re.MonitoringRunEntry


def _open_entry(workspace: Path):
    cls = _entry_cls()
    # Prefer workspace directory (current worker_01 shape). If the ctor treats the
    # argument as a sqlite file path, fall back to an explicit file under it.
    try:
        return cls(workspace)
    except (TypeError, OSError, re.RunEntryError):
        return cls(workspace / "mm_r7_product.sqlite3")


def _public(result: Any) -> dict:
    if isinstance(result, Mapping):
        return dict(result)
    binding = getattr(result, "binding", None)
    if isinstance(binding, Mapping):
        body = dict(binding)
        if hasattr(result, "replayed"):
            body["replayed"] = bool(result.replayed)
        digest = getattr(result, "binding_digest", None)
        if digest:
            body["binding_digest"] = digest
        epd = getattr(result, "execution_profile_digest", None)
        if epd:
            body["execution_profile_digest"] = epd
        return body
    profile = getattr(result, "profile", None)
    if isinstance(profile, Mapping):
        body = dict(profile)
        if hasattr(result, "replayed"):
            body["replayed"] = bool(result.replayed)
        if hasattr(result, "revision"):
            body["revision"] = result.revision
        if hasattr(result, "record_id"):
            body["record_id"] = result.record_id
        return body
    raise AssertionError(f"unsupported run_entry result type: {type(result)!r}")


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _assert_stable_error(exc: BaseException) -> None:
    assert isinstance(exc, re.RunEntryError)
    assert isinstance(exc.code, str) and exc.code.strip()
    assert isinstance(exc.message, str) and exc.message.strip()
    assert _has_chinese(exc.message), f"message must be Chinese: {exc.message!r}"
    blob = f"{exc.code}\n{exc.message}".lower()
    for token in FORBIDDEN_RESPONSE_TOKENS:
        assert token not in blob


def _assert_public_clean(payload: Mapping[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_RESPONSE_TOKENS:
        assert token not in blob
    assert "effective_selector" not in payload
    assert "requested_provider" not in payload
    assert "requested_model" not in payload


def _project_fields(**overrides: Any) -> dict:
    base = {
        "timeout_seconds": 80,
        "credential_ref": "env:OMP_CREDENTIAL_REF",
    }
    base.update(overrides)
    return base


def _deepseek_fields() -> dict:
    return {
        "profile_id": "monitoring_harness_deepseek_v4_flash_max",
        "capability_id": "medical_monitoring_harness",
        "user_config_name": DEEPSEEK_CONFIG,
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-flash",
        "reasoning_effort": "max",
        "timeout_seconds": 120,
        "allowed_tools": ["read"],
        "context_isolation": "omp_print_no_session_no_skills_no_rules",
        "credential_ref": "env:OMP_CREDENTIAL_REF",
        "adapter_id": "omp_print_v1",
        "adapter_version": "1.0.0",
        "fallback_profile_ids": [],
    }


def _bind_kwargs(**overrides: Any) -> dict:
    base = {
        "run_id": "run-s02-001",
        "project_id": "proj-s02",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "cutoff-sha256:s02-aaa",
        "source_revision_id": "src-sha256:s02-bbb",
        "prior_accepted_snapshot_ref": None,
    }
    base.update(overrides)
    return base


def test_required_run_entry_apis_present():
    missing = [name for name in REQUIRED_RUN_ENTRY_APIS if not hasattr(re, name)]
    assert missing == []
    assert re.API_PREFIX == "/api/medical-monitoring/r7"
    assert re.MonitoringRunEntry is re.ProductRunEntry is re.RunEntry
    assert re.BUILTIN_DEFAULT_USER_CONFIG_NAME == MTPLX_CONFIG
    assert re.BUILTIN_DEFAULT_REASONING_EFFORT == "medium"
    missing_methods = [
        name
        for name in REQUIRED_ENTRY_METHODS
        if not callable(getattr(re.MonitoringRunEntry, name, None))
    ]
    assert missing_methods == []


def test_constructor_does_not_seed_global_default(workspace: Path):
    entry = _open_entry(workspace)
    try:
        with pytest.raises(re.RunEntryError) as raised:
            entry.get_execution_profile(ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY)
        _assert_stable_error(raised.value)
        assert raised.value.code == "profile_layer_not_found"
    finally:
        entry.close()


def test_constructor_rejects_sqlite_filename(tmp_path: Path):
    with pytest.raises(re.RunEntryError) as caught:
        re.MonitoringRunEntry(tmp_path / "workspace.sqlite3")
    assert caught.value.code == "invalid_workspace_path"


def test_bootstrap_replays_seed_after_global_overlay(workspace: Path):
    entry = _open_entry(workspace)
    try:
        first = _public(entry.bootstrap_workspace())
        entry.append_execution_profile(
            ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY, {"timeout_seconds": 55}
        )
        replay = _public(entry.bootstrap_workspace())
        assert replay["replayed"] is True
        assert replay["record_id"] == first["record_id"]
        frozen = entry.freeze_effective_profile_for_scopes(run_id="run-global-overlay")
        assert frozen.timeout_seconds == 55
    finally:
        entry.close()


def test_bootstrap_idempotent_and_mtplx_default(workspace: Path):
    entry = _open_entry(workspace)
    try:
        first = _public(entry.bootstrap_workspace())
        second = _public(entry.bootstrap_workspace())
        _assert_public_clean(first)
        _assert_public_clean(second)
        assert first.get("replayed") is False
        assert second.get("replayed") is True
        assert first.get("revision") == second.get("revision")
        assert first.get("record_id") == second.get("record_id")
        assert first.get("layer_kind") == ps.LAYER_GLOBAL_DEFAULT
        assert first.get("scope_key") == ps.GLOBAL_SCOPE_KEY
        assert first.get("user_config_name") == MTPLX_CONFIG
        assert first.get("reasoning_effort") == "medium"
        hist = entry.profile_store.list_revisions(
            ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY
        )
        assert len(hist) == 1
    finally:
        entry.close()


def test_explicit_deepseek_via_layer_not_auto_fallback(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        default_run = _public(
            entry.bind_run(**_bind_kwargs(run_id="run-mtplx-default"))
        )
        _assert_public_clean(default_run)
        assert default_run.get("user_config_name") == MTPLX_CONFIG

        entry.append_execution_profile(
            ps.LAYER_RUN_OVERRIDE, "run-ds-explicit", _deepseek_fields()
        )
        ds = _public(
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-ds-explicit",
                    project_id="proj-ds",
                    data_cutoff="cutoff-sha256:ds",
                    source_revision_id="src-sha256:ds",
                    run_override_scope_key="run-ds-explicit",
                )
            )
        )
        _assert_public_clean(ds)
        assert ds.get("user_config_name") == DEEPSEEK_CONFIG
        assert ds.get("binding_digest") != default_run.get("binding_digest")
    finally:
        entry.close()


def test_four_layer_precedence_via_run_entry(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        entry.append_execution_profile(
            ps.LAYER_CAPABILITY_AGENT,
            "medical_monitoring_harness",
            _project_fields(timeout_seconds=100),
        )
        entry.append_execution_profile(
            ps.LAYER_PROJECT, "proj-prec", _project_fields(timeout_seconds=80)
        )
        entry.append_execution_profile(
            ps.LAYER_RUN_OVERRIDE,
            "run-prec",
            _project_fields(timeout_seconds=60),
        )
        frozen = entry.freeze_effective_profile_for_scopes(
            run_id="run-prec",
            capability_scope_key="medical_monitoring_harness",
            project_scope_key="proj-prec",
            run_override_scope_key="run-prec",
        )
        assert frozen.timeout_seconds == 60
        assert MTPLX_CONFIG in frozen.user_config_name
        bound = _public(
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-prec",
                    project_id="proj-prec",
                    data_cutoff="cutoff-sha256:prec",
                    source_revision_id="src-sha256:prec",
                    capability_scope_key="medical_monitoring_harness",
                    project_scope_key="proj-prec",
                    run_override_scope_key="run-prec",
                )
            )
        )
        _assert_public_clean(bound)
        assert bound.get("run_id") == "run-prec"
    finally:
        entry.close()


@pytest.mark.parametrize("mode", ["daily", "pre_lock", "post_lock_pre_cfdi"])
def test_three_modes_full_basis(workspace: Path, mode: str):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        bound = _public(
            entry.bind_run(
                **_bind_kwargs(
                    run_id=f"run-mode-{mode}",
                    mode=mode,
                    execution_basis="full",
                    prior_accepted_snapshot_ref=None,
                )
            )
        )
        assert bound.get("mode") == mode
        assert bound.get("execution_basis") == "full"
        assert bound.get("replayed") is False
    finally:
        entry.close()


def test_incremental_requires_prior_full_forbids_prior(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        ok = _public(
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-incr-ok",
                    execution_basis="incremental",
                    prior_accepted_snapshot_ref="snap-accepted-001",
                )
            )
        )
        assert ok.get("execution_basis") == "incremental"
        assert ok.get("prior_accepted_snapshot_ref") == "snap-accepted-001"

        with pytest.raises(re.RunEntryError) as missing_prior:
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-incr-bad",
                    execution_basis="incremental",
                    prior_accepted_snapshot_ref=None,
                )
            )
        _assert_stable_error(missing_prior.value)

        with pytest.raises(re.RunEntryError) as full_with_prior:
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-full-bad-prior",
                    execution_basis="full",
                    prior_accepted_snapshot_ref="snap-should-not",
                )
            )
        _assert_stable_error(full_with_prior.value)
    finally:
        entry.close()


def test_bind_replay_and_conflict(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        first = _public(entry.bind_run(**_bind_kwargs()))
        second = _public(entry.bind_run(**_bind_kwargs()))
        assert first.get("replayed") is False
        assert second.get("replayed") is True
        assert first.get("binding_digest") == second.get("binding_digest")

        with pytest.raises(re.RunEntryError) as conflict:
            entry.bind_run(**_bind_kwargs(data_cutoff="cutoff-sha256:CHANGED"))
        _assert_stable_error(conflict.value)

        entry.append_execution_profile(
            ps.LAYER_RUN_OVERRIDE, "run-s02-001", _deepseek_fields()
        )
        with pytest.raises(re.RunEntryError) as profile_conflict:
            entry.bind_run(
                **_bind_kwargs(run_override_scope_key="run-s02-001")
            )
        _assert_stable_error(profile_conflict.value)
    finally:
        entry.close()


def test_close_reopen_parity(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        bound = _public(entry.bind_run(**_bind_kwargs(run_id="run-reopen-s02")))
        public = entry.get_run("run-reopen-s02")
        digest = bound.get("binding_digest")
    finally:
        entry.close()

    entry2 = _open_entry(workspace)
    try:
        entry2.reopen()
        again = entry2.reopen_and_validate_run("run-reopen-s02")
        assert again.get("run_id") == public.get("run_id")
        assert again.get("mode") == public.get("mode")
        assert again.get("user_config_name") == public.get("user_config_name")
        assert again.get("data_cutoff") == bound.get("data_cutoff")
        assert entry2.run_binding_store.get("run-reopen-s02").binding_digest == digest
    finally:
        entry2.close()


def test_missing_profile_and_illegal_secret_fields_fail_closed(workspace: Path):
    entry = _open_entry(workspace)
    try:
        entry.bootstrap_workspace()
        with pytest.raises(re.RunEntryError) as missing:
            entry.get_execution_profile(ps.LAYER_PROJECT, "no-such-project")
        _assert_stable_error(missing.value)

        with pytest.raises(re.RunEntryError) as secret:
            entry.append_execution_profile(
                ps.LAYER_PROJECT,
                "proj-secret",
                {
                    "timeout_seconds": 70,
                    "credential_ref": "env:OMP_CREDENTIAL_REF",
                    "credential_value": "super-secret-value",
                },
            )
        _assert_stable_error(secret.value)
        assert secret.value.code in {
            "forbidden_secret_field",
            "credential_value_field_forbidden",
        }

        with pytest.raises(re.RunEntryError) as bad_mode:
            entry.bind_run(**_bind_kwargs(run_id="run-bad-mode", mode="weekly"))
        _assert_stable_error(bad_mode.value)

        bare_ws = workspace.with_name("bare-no-boot")
        bare_ws.mkdir(exist_ok=True)
        bare = _open_entry(bare_ws)
        try:
            with pytest.raises(re.RunEntryError) as no_global:
                bare.bind_run(**_bind_kwargs(run_id="run-no-global"))
            _assert_stable_error(no_global.value)
            assert no_global.value.code == "global_default_missing"
        finally:
            bare.close()
    finally:
        entry.close()


def test_public_projection_has_no_medical_or_secret_leakage(workspace: Path):
    entry = _open_entry(workspace)
    try:
        boot = _public(entry.bootstrap_workspace())
        written = _public(
            entry.append_execution_profile(
                ps.LAYER_PROJECT, "proj-leak", _project_fields()
            )
        )
        bound = _public(
            entry.bind_run(
                **_bind_kwargs(
                    run_id="run-leak-s02",
                    project_id="proj-leak",
                    data_cutoff="cutoff-sha256:leak",
                    source_revision_id="src-sha256:leak",
                    project_scope_key="proj-leak",
                )
            )
        )
        got = entry.get_run("run-leak-s02")
        for payload in (boot, written, bound, got):
            _assert_public_clean(payload)
    finally:
        entry.close()


@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
@pytest.mark.parametrize("opt_flag", [(), ("-O",), ("-OO",)])
def test_slice02_bootstrap_bind_digest_matrix(hash_seed, opt_flag):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [
        sys.executable,
        *opt_flag,
        "-c",
        _REPRO_PROBE,
        str(SRC_DIR),
        str(R6_SRC),
    ]
    proc = subprocess.run(
        cmd, check=True, capture_output=True, text=True, env=env, cwd=str(POC_ROOT)
    )
    payload = json.loads(proc.stdout.strip())
    baseline = json.loads(
        subprocess.run(
            [sys.executable, "-c", _REPRO_PROBE, str(SRC_DIR), str(R6_SRC)],
            check=True,
            capture_output=True,
            text=True,
            env={**env, "PYTHONHASHSEED": "0"},
            cwd=str(POC_ROOT),
        ).stdout.strip()
    )
    assert payload == baseline
    assert payload["bootstrap_first_replayed"] is False
    assert payload["bootstrap_second_replayed"] is True
    assert payload["bootstrap_revision"] == payload["bootstrap_revision_replay"]
    assert payload["bind_first_replayed"] is False
    assert payload["bind_second_replayed"] is True
    assert payload["binding_digest"] == payload["binding_digest_replay"]
    assert payload["run_id"] == "run-repro-s02"
    assert payload["user_config_name"] == MTPLX_CONFIG
