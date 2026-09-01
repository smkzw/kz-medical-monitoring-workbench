"""R7 slice-01 Monitoring Run binding contract tests (worker_03).

Aligned to worker_02 module-level freeze + ``RunBindingStore.bind`` surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest

from mm_r6.agent_harness import ExecutionProfileLayer
from mm_r7 import profile_store as ps
from mm_r7 import run_binding as rb

REQUIRED_RUN_BINDING_APIS = (
    "RunBindingStore",
    "RunBindingError",
    "MonitoringRunBinding",
    "ALLOWED_MONITORING_MODES",
    "ALLOWED_EXECUTION_BASES",
    "freeze_effective_profile",
    "freeze_default_mtplx_effective_profile",
    "freeze_deepseek_flash_max_effective_profile",
    "bind_monitoring_run",
    "public_projection",
    "audit_projection",
    "validate_binding_against_frozen",
)


def _layer_from_record(rec: Optional[ps.ProfileLayerRecord]) -> Optional[ExecutionProfileLayer]:
    if rec is None:
        return None
    kwargs = dict(rec.as_override_dict())
    return ExecutionProfileLayer(**kwargs)


def _global_fields(**overrides: Any) -> dict:
    base = {
        "profile_id": "monitoring_harness_default_mtplx_qwen38_medium",
        "capability_id": "medical_monitoring_harness",
        "user_config_name": (
            "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
        ),
        "requested_provider": "mtplx",
        "requested_model": "Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality",
        "reasoning_effort": "medium",
        "timeout_seconds": 120,
        "allowed_tools": ["read"],
        "context_isolation": "omp_print_no_session_no_skills_no_rules",
        "credential_ref": "env:OMP_CREDENTIAL_REF",
        "adapter_id": "omp_print_v1",
        "adapter_version": "1.0.0",
        "fallback_profile_ids": [],
    }
    base.update(overrides)
    return base


def _deepseek_fields() -> dict:
    return {
        "profile_id": "monitoring_harness_deepseek_v4_flash_max",
        "capability_id": "medical_monitoring_harness",
        "user_config_name": "deepseek/DeepSeek V4 flash",
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


def test_required_run_binding_apis_present():
    missing = [name for name in REQUIRED_RUN_BINDING_APIS if not hasattr(rb, name)]
    assert missing == []
    assert set(rb.ALLOWED_MONITORING_MODES) == {
        "daily",
        "pre_lock",
        "post_lock_pre_cfdi",
    }
    assert set(rb.ALLOWED_EXECUTION_BASES) == {"full", "incremental"}


def test_default_mtplx_and_explicit_deepseek_freeze():
    mtplx = rb.freeze_default_mtplx_effective_profile(run_id="offline")
    deepseek = rb.freeze_deepseek_flash_max_effective_profile(run_id="offline")
    assert mtplx.reasoning_effort == "medium"
    assert deepseek.reasoning_effort == "max"
    assert mtplx.adapter_id == rb.ADAPTER_ID
    assert mtplx.execution_profile_digest != deepseek.execution_profile_digest
    assert list(deepseek.fallback_profile_ids) == []
    with pytest.raises(rb.RunBindingError):
        rb.assert_no_auto_fallback("must not auto-fallback")


def test_four_layer_precedence_merge(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        store.append_revision(
            ps.LAYER_GLOBAL_DEFAULT, "*", _global_fields(timeout_seconds=120)
        )
        store.append_revision(
            ps.LAYER_CAPABILITY_AGENT,
            "medical_monitoring_harness",
            {"timeout_seconds": 100, "credential_ref": "env:OMP_CREDENTIAL_REF"},
        )
        store.append_revision(
            ps.LAYER_PROJECT,
            "proj-prec",
            {"timeout_seconds": 80, "credential_ref": "env:OMP_CREDENTIAL_REF"},
        )
        store.append_revision(
            ps.LAYER_RUN_OVERRIDE,
            "run-prec",
            {"timeout_seconds": 60, "credential_ref": "env:OMP_CREDENTIAL_REF"},
        )
        layers = tuple(
            _layer_from_record(r)
            for r in store.load_precedence_layers(
                capability_scope="medical_monitoring_harness",
                project_scope="proj-prec",
                run_scope="run-prec",
            )
        )
        frozen = rb.freeze_effective_profile(*layers, run_id="run-prec")
        assert frozen.timeout_seconds == 60
        assert "mtplx" in frozen.user_config_name.lower()
    finally:
        store.close()


def _bind_kwargs(**overrides: Any) -> dict:
    base = {
        "run_id": "run-bind-001",
        "project_id": "proj-bind",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "cutoff-sha256:aaa",
        "source_revision_id": "src-sha256:bbb",
        "prior_accepted_snapshot_ref": None,
    }
    base.update(overrides)
    return base


def test_idempotent_bind_and_conflict_fail_closed(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-bind-001")
        first = binder.bind(frozen=frozen, **_bind_kwargs())
        second = binder.bind(frozen=frozen, **_bind_kwargs())
        assert first.binding_digest == second.binding_digest
        assert first.execution_profile_digest == frozen.execution_profile_digest
        assert first.adapter_id == rb.ADAPTER_ID

        with pytest.raises(rb.RunBindingError):
            binder.bind(
                frozen=frozen,
                **_bind_kwargs(data_cutoff="cutoff-sha256:CHANGED"),
            )

        other = rb.freeze_deepseek_flash_max_effective_profile(run_id="run-bind-001")
        assert other.execution_profile_digest != frozen.execution_profile_digest
        with pytest.raises(rb.RunBindingError):
            binder.bind(frozen=other, **_bind_kwargs())
    finally:
        binder.close()


def test_forged_frozen_profile_rejected(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        good = rb.freeze_default_mtplx_effective_profile(run_id="run-forge")
        forged = rb.FrozenExecutionProfile(
            profile_id=good.profile_id,
            profile_revision=good.profile_revision,
            capability_id=good.capability_id,
            requested_provider=good.requested_provider,
            requested_model=good.requested_model,
            user_config_name=good.user_config_name,
            effective_selector="deepseek/deepseek-v4-flash",
            reasoning_effort=good.reasoning_effort,
            timeout_seconds=good.timeout_seconds,
            allowed_tools=good.allowed_tools,
            context_isolation=good.context_isolation,
            credential_ref=good.credential_ref,
            adapter_id=good.adapter_id,
            adapter_version=good.adapter_version,
            fallback_profile_ids=good.fallback_profile_ids,
            execution_profile_id=good.execution_profile_id,
            execution_profile_digest=good.execution_profile_digest,
        )
        with pytest.raises(rb.RunBindingError):
            binder.bind(
                frozen=forged,
                **_bind_kwargs(run_id="run-forge", project_id="proj-forge"),
            )
    finally:
        binder.close()


@pytest.mark.parametrize(
    "mode,basis,prior,ok",
    [
        ("daily", "full", None, True),
        ("pre_lock", "full", None, True),
        ("post_lock_pre_cfdi", "full", None, True),
        ("daily", "incremental", "snap-accepted-001", True),
        ("daily", "incremental", None, False),
        ("daily", "incremental", "", False),
        ("daily", "full", "snap-should-not-be-basis", False),
        ("weekly", "full", None, False),
        ("daily", "delta", None, False),
    ],
)
def test_mode_and_basis_rules(db_path: Path, mode, basis, prior, ok):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id=f"run-{mode}")
        kwargs = _bind_kwargs(
            run_id=f"run-{mode}-{basis}-{prior}",
            project_id="proj-mode",
            mode=mode,
            execution_basis=basis,
            prior_accepted_snapshot_ref=prior,
        )
        if ok:
            binding = binder.bind(frozen=frozen, **kwargs)
            assert binding.mode == mode
            assert binding.execution_basis == basis
        else:
            with pytest.raises(rb.RunBindingError):
                binder.bind(frozen=frozen, **kwargs)
    finally:
        binder.close()


def test_binding_reopen_validates_r6_digest(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-reopen")
        binding = binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-reopen", project_id="proj-reopen"),
        )
        digest = binding.binding_digest
        profile_digest = binding.execution_profile_digest
        public = rb.public_projection(binding)
        audit = rb.audit_projection(binding)
    finally:
        binder.close()

    binder2 = rb.RunBindingStore(db_path)
    try:
        again = binder2.get("run-reopen")
        assert again.binding_digest == digest
        assert again.execution_profile_digest == profile_digest
        again2 = binder2.reopen_and_validate("run-reopen")
        assert again2.binding_digest == digest
        assert rb.public_projection(again) == public
        assert rb.audit_projection(again) == audit
        assert again.data_cutoff
        assert again.source_revision_id
        _, frozen2 = binder2.get_with_frozen("run-reopen")
        rb.validate_binding_against_frozen(again, frozen2)
    finally:
        binder2.close()


@pytest.mark.parametrize(
    "column,value,error",
    [
        ("profile_id", "forged-profile", "profile_id_mismatch"),
        (
            "effective_selector",
            "deepseek/deepseek-v4-flash",
            "effective_selector_mismatch",
        ),
    ],
)
def test_reopen_rejects_stored_profile_projection_drift(
    db_path: Path, column: str, value: str, error: str
):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-drift")
        binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-drift", project_id="proj-drift"),
        )
        binder._conn.execute(
            f"UPDATE monitoring_run_bindings SET {column} = ? WHERE run_id = ?",
            (value, "run-drift"),
        )
        binder._conn.commit()
        with pytest.raises(rb.RunBindingError, match=error):
            binder.reopen_and_validate("run-drift")
    finally:
        binder.close()


def test_reopen_rejects_record_json_drift(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-record")
        binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-record", project_id="proj-record"),
        )
        binder._conn.execute(
            "UPDATE monitoring_run_bindings SET record_json = ? WHERE run_id = ?",
            ('{"run_id":"run-record"}', "run-record"),
        )
        binder._conn.commit()
        with pytest.raises(rb.RunBindingError, match="record_json_mismatch"):
            binder.reopen_and_validate("run-record")
    finally:
        binder.close()


def test_reopen_rejects_malformed_stored_json(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-json")
        binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-json", project_id="proj-json"),
        )
        binder._conn.execute(
            "UPDATE monitoring_run_bindings SET frozen_profile_json = ? WHERE run_id = ?",
            ("{", "run-json"),
        )
        binder._conn.commit()
        with pytest.raises(rb.RunBindingError, match="corrupt_run_binding_json"):
            binder.reopen_and_validate("run-json")
    finally:
        binder.close()


def test_projections_and_no_medical_object_leakage(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-leak")
        binding = binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-leak", project_id="proj-leak"),
        )
        public = rb.public_projection(binding)
        audit = rb.audit_projection(binding)
        joined = "\n".join(
            [
                json.dumps(public, ensure_ascii=False),
                json.dumps(audit, ensure_ascii=False),
            ]
        ).lower()
        for medical_key in (
            "modeoutput",
            "risk_instance",
            "patientjourney",
            "query_draft",
            "timeline",
            "canonical_fact",
            "report_claim",
        ):
            assert medical_key not in joined
        assert "credential_value" not in joined
        assert "credential_ref" not in joined
        assert "sk-" not in joined
        assert "user_config_name" in public
        assert "effective_selector" not in public
        assert "effective_selector" in audit
        assert "execution_profile_digest" in audit
        assert "binding_digest" in audit
    finally:
        binder.close()


def test_empty_cutoff_or_source_revision_fail_closed(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        frozen = rb.freeze_default_mtplx_effective_profile(run_id="run-empty")
        with pytest.raises(rb.RunBindingError):
            binder.bind(
                frozen=frozen,
                **_bind_kwargs(run_id="run-empty-c", data_cutoff=""),
            )
        with pytest.raises(rb.RunBindingError):
            binder.bind(
                frozen=frozen,
                **_bind_kwargs(run_id="run-empty-s", source_revision_id=""),
            )
    finally:
        binder.close()


def test_bind_monitoring_run_convenience(db_path: Path):
    binder = rb.RunBindingStore(db_path)
    try:
        binding = rb.bind_monitoring_run(
            binder,
            run_id="run-convenience",
            project_id="proj-convenience",
            mode="daily",
            execution_basis="full",
            data_cutoff="cutoff-sha256:conv",
            source_revision_id="src-sha256:conv",
            layers=(ExecutionProfileLayer(**_global_fields()),),
        )
        assert binding.run_id == "run-convenience"
        assert binding.binding_digest
    finally:
        binder.close()


def test_store_layers_plus_deepseek_run_override(db_path: Path):
    store = ps.ProfileStore(db_path)
    binder = rb.RunBindingStore(db_path.with_name("bindings.sqlite3"))
    try:
        store.append_revision(ps.LAYER_GLOBAL_DEFAULT, "*", _global_fields())
        store.append_revision(
            ps.LAYER_RUN_OVERRIDE, "run-ds", _deepseek_fields()
        )
        layers = tuple(
            _layer_from_record(r)
            for r in store.load_precedence_layers(run_scope="run-ds")
        )
        frozen = rb.freeze_effective_profile(*layers, run_id="run-ds")
        assert frozen.reasoning_effort == "max"
        binding = binder.bind(
            frozen=frozen,
            **_bind_kwargs(run_id="run-ds", project_id="proj-ds"),
        )
        assert binding.execution_profile_digest == frozen.execution_profile_digest
    finally:
        binder.close()
        store.close()
