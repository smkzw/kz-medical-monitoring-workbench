"""R7 Slice-06 offline harness bridge, failure, lease and retry tests."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any, Mapping

import pytest

from mm_r7.background_recovery import (
    BackgroundRecoveryAdapter,
    ExecutionControlState,
    continuable_ai_unit,
)
from mm_r7.harness_runtime import (
    HarnessCapabilityRuntime,
    ProfileBridgeError,
    _r6_invocation_id,
    build_profile_receipt_bridge,
    build_r1_execution_profile,
    renew_inflight_lease,
)
from mm_r7.run_entry import MonitoringRunEntry
from mm_r7.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
)

from mm_r6.agent_harness import (
    AgentHarnessError,
    OmpPrintAdapter,
    PreflightResult,
    freeze_deepseek_flash_max_profile,
    freeze_default_mtplx_profile,
)
from mm_r1.capability_runtime import (
    InvocationVersions,
    _normalize_transport_result,
)
from mm_r1.controller import CapabilityWorkUnitController
from mm_r1.domain import (
    EVENT_CAPABILITY_ATTEMPT_CLAIMED,
    EVENT_CAPABILITY_ATTEMPT_DECLARED,
    EVENT_CAPABILITY_ATTEMPT_TERMINAL,
    EVENT_DOMAIN_OBJECT_PUT,
    EVENT_WORK_UNIT_BEGIN,
    EVENT_WORK_UNIT_COMPLETE,
    CoverageUnit,
    NodeStatus,
)
from mm_r1.store import Store

try:
    from .fake_harness import FakeCatalog, FakeHarnessAdapter
except ImportError:  # pytest collects the POC tests as a plain directory
    from fake_harness import FakeCatalog, FakeHarnessAdapter


PROJECT_ID = "r7-slice06-project"
RUN_ID = "r7-slice06-run"
NODE_ID = "r7-offline-monitor"


def _units(prefix: str = "ai", count: int = 1) -> list[dict[str, Any]]:
    return [
        {
            "work_unit_id": f"{prefix}-{index}",
            "stage": "风险分析" if index == 1 else "质量检查",
            "label": f"完成合成 AI 监查第{index}项",
            "scope": "subject",
            "target_ref": f"SYN-{index:03d}",
            "ordinal": index,
            "mandatory": True,
            "depends_on": [],
        }
        for index in range(1, count + 1)
    ]


def _bind(workspace: Path, *, run_id: str = RUN_ID) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    entry = MonitoringRunEntry(workspace)
    try:
        entry.bootstrap_workspace()
        entry.bind_run(
            run_id=run_id,
            project_id=PROJECT_ID,
            mode="daily",
            execution_basis="full",
            data_cutoff="2026-08-28",
            source_revision_id=f"source-{run_id}",
        )
    finally:
        entry.close()


def _prepare_harness(
    workspace: Path,
    fake: FakeHarnessAdapter,
    *,
    catalog: FakeCatalog | None = None,
    run_id: str = RUN_ID,
    units: list[dict[str, Any]] | None = None,
) -> RuntimeProgressAdapter:
    _bind(workspace, run_id=run_id)
    adapter = RuntimeProgressAdapter(
        workspace,
        canonical_project_id=PROJECT_ID,
        harness_adapter=fake,
        harness_catalog=catalog or FakeCatalog(),
    )
    adapter.prepare_execution(
        run_id,
        units or _units(),
        execution_kind="harness",
    )
    return adapter


def _wait(workspace: Path, run_id: str = RUN_ID, timeout: float = 5.0) -> None:
    waiter = BackgroundRecoveryAdapter(
        runtime_dir=workspace / RUNTIME_DIR_NAME,
        canonical_project_id=PROJECT_ID,
    )
    assert waiter.wait(run_id, timeout=timeout)


def _runtime_db(workspace: Path) -> Path:
    return workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME


def _store(workspace: Path) -> Store:
    runtime = workspace / RUNTIME_DIR_NAME
    return Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)


def _attempt_bindings(workspace: Path, work_unit_id: str) -> list[tuple[Any, ...]]:
    with sqlite3.connect(_runtime_db(workspace)) as connection:
        return list(
            connection.execute(
                "SELECT b.attempt_ordinal, b.attempt_id, j.continued_from "
                "FROM work_unit_capability_attempts AS b "
                "JOIN capability_attempt_journal AS j ON j.attempt_id=b.attempt_id "
                "WHERE b.run_id=? AND b.work_unit_id=? ORDER BY b.attempt_ordinal",
                (RUN_ID, work_unit_id),
            )
        )


def _event_types(workspace: Path) -> list[str]:
    with sqlite3.connect(_runtime_db(workspace)) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT event_type FROM audit_events WHERE run_id=? ORDER BY seq",
                (RUN_ID,),
            )
        ]


def _bridge(tmp_path: Path, *, deepseek: bool = False):
    profile = (
        freeze_deepseek_flash_max_profile(run_id="slice06")
        if deepseek
        else freeze_default_mtplx_profile(run_id="slice06")
    )
    cwd = tmp_path / ("deepseek-cwd" if deepseek else "mtplx-cwd")
    cwd.mkdir()
    r1 = build_r1_execution_profile(
        profile,
        executable=sys.executable,
        working_directory=cwd,
    )
    return profile, build_profile_receipt_bridge(profile, r1)


def _low_level_result(
    tmp_path: Path,
    state: str,
    *,
    receipt_overrides: Mapping[str, Any] | None = None,
):
    profile, bridge = _bridge(tmp_path)
    fake = FakeHarnessAdapter(
        states=(state,),
        receipt_overrides=receipt_overrides,
    )
    runtime = HarnessCapabilityRuntime(
        bridge,
        adapter=fake,
        catalog=FakeCatalog(),
        manifest_revision_reader=lambda _run_id: 1,
    )
    assert runtime.preflight().ok
    result = runtime.invoke(
        attempt_id="slice06-attempt-1",
        monitoring_run_id="slice06-run",
        node_id=NODE_ID,
        manifest_revision=1,
        versions=InvocationVersions(
            source_revision_id="synthetic-source",
            rule_version="slice06-rule-v1",
            knowledge_version="slice06-knowledge-v1",
            graph_version="slice06-graph-v1",
            schema_version="slice06-schema-v1",
        ),
        payload={"fixture": "synthetic", "state": state},
        expected_units=(CoverageUnit("subject", "SYN-001"),),
    )
    return profile, bridge, fake, result


@pytest.mark.parametrize(
    ("r6_state", "r1_state"),
    [
        ("complete", "complete"),
        ("partial", "partial"),
        ("truncated", "truncated"),
        ("timed_out", "timeout"),
        ("failed", "failed"),
        ("not_evaluable", "failed"),
    ],
)
def test_fake_receipts_use_parent_classifier_and_preserve_raw_evidence(
    tmp_path: Path, r6_state: str, r1_state: str
) -> None:
    _profile, bridge, fake, result = _low_level_result(tmp_path, r6_state)

    assert result.status.value == r1_state
    assert len(fake.invoke_calls) == 1
    assert fake.preflight_calls == 1
    assert len(fake.preflight_results) == 1
    assert fake.invoke_preflight_results[0] is fake.preflight_results[0]
    assert fake.invoke_calls[0]["catalog_name"] == "synthetic-catalog"
    assert fake.invoke_calls[0]["preflight_selector"] == bridge.effective_selector
    assert fake.invoke_calls[0]["preflight_effort"] == bridge.reasoning_effort
    assert re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",
        fake.invoke_calls[0]["invocation_id"],
    )
    assert fake.invoke_calls[0]["invocation_id"] != result.request.attempt_id
    assert '"status":"complete"' in fake.invoke_calls[0]["prompt"]
    assert '"produced_units"' in fake.invoke_calls[0]["prompt"]
    assert "subject:SYN-001" in fake.invoke_calls[0]["prompt"]
    assert bridge.effective_selector not in fake.invoke_calls[0]["prompt"]
    assert bridge.reasoning_effort not in fake.invoke_calls[0]["prompt"]
    envelope = json.loads(result.transport_execution.stdout)
    assert envelope["jsonrpc"] == "2.0"
    assert envelope["id"] == result.request.attempt_id
    assert envelope["result"]["execution_identity"] == bridge.r1_profile.response_identity()
    assert result.transport_execution.raw_output["state"] == r6_state
    assert result.transport_execution.raw_output["stdout_path"] == ""
    assert "super-secret-value" not in json.dumps(
        result.transport_execution.raw_output, ensure_ascii=False
    )

    # The R1 classifier remains the status authority; this test does not
    # replace it with an R7 status shortcut.
    normalized = _normalize_transport_result(result.request, result.transport_execution)
    assert normalized.status.value == r1_state
    if r6_state == "timed_out":
        assert result.transport_execution.timed_out is True
        assert result.transport_execution.output_truncated is False


def test_colon_delimited_r1_attempt_id_maps_to_stable_r6_invocation_id(
    tmp_path: Path,
) -> None:
    profile, bridge = _bridge(tmp_path)
    fake = FakeHarnessAdapter()
    runtime = HarnessCapabilityRuntime(
        bridge,
        adapter=fake,
        catalog=FakeCatalog(),
        manifest_revision_reader=lambda _run_id: 1,
    )
    assert runtime.preflight().ok
    attempt_id = "r7-capability:matrix14-mtplx-run:1:ai-1:attempt-1"

    result = runtime.invoke(
        attempt_id=attempt_id,
        monitoring_run_id="matrix14-run",
        node_id=NODE_ID,
        manifest_revision=1,
        versions=InvocationVersions(
            source_revision_id="synthetic-source",
            rule_version="slice06-rule-v1",
            knowledge_version="slice06-knowledge-v1",
            graph_version="slice06-graph-v1",
            schema_version="slice06-schema-v1",
        ),
        payload={"fixture": "synthetic"},
        expected_units=(CoverageUnit("subject", "SYN-MATRIX14-001"),),
    )

    invocation_id = fake.invoke_calls[0]["invocation_id"]
    assert result.status.value == "complete"
    assert invocation_id == "r7_9a1aababc709935a59ed1229968a07b1"
    assert invocation_id == _r6_invocation_id(attempt_id)
    assert invocation_id == _r6_invocation_id(attempt_id)
    assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", invocation_id)
    assert result.transport_execution.execution_id == invocation_id
    assert json.loads(result.transport_execution.stdout)["id"] == attempt_id


def test_frozen_r6_adapter_rejects_raw_attempt_id_and_accepts_mapped_id(
    tmp_path: Path,
) -> None:
    profile = freeze_default_mtplx_profile(run_id="matrix14-adapter-grammar")
    adapter = OmpPrintAdapter(executable=sys.executable)
    preflight = PreflightResult(
        ok=False,
        executable="",
        selector=profile.effective_selector,
        effort=profile.reasoning_effort,
        allowed_tools=profile.allowed_tools,
        timeout_seconds=profile.timeout_seconds,
        reasons=("offline_grammar_probe",),
    )
    attempt_id = "r7-capability:matrix14-mtplx-run:1:ai-1:attempt-1"
    expected = ("subject:SYN-MATRIX14-001",)

    with pytest.raises(AgentHarnessError, match="invalid_invocation_id"):
        adapter.invoke(
            profile,
            "synthetic",
            output_dir=tmp_path / "raw",
            expected_units=expected,
            invocation_id=attempt_id,
            preflight_result=preflight,
        )

    mapped = _r6_invocation_id(attempt_id)
    receipt = adapter.invoke(
        profile,
        "synthetic",
        output_dir=tmp_path / "mapped",
        expected_units=expected,
        invocation_id=mapped,
        preflight_result=preflight,
    )
    assert receipt.invocation_id == mapped
    assert receipt.failure_reason == "preflight_failed"


def test_complete_receipt_with_invalid_coverage_is_not_promoted(
    tmp_path: Path,
) -> None:
    _profile, _bridge, _fake, result = _low_level_result(
        tmp_path,
        "complete",
        receipt_overrides={
            "produced_units": ("risk_domain:UNKNOWN",),
            "missing_units": (),
        },
    )
    assert result.status.value == "failed"
    assert json.loads(result.transport_execution.stdout)["result"]["status"] == "failed"


def test_profile_bridge_keeps_default_and_explicit_deepseek_identities_separate(
    tmp_path: Path,
) -> None:
    mtplx, mtplx_bridge = _bridge(tmp_path)
    deepseek, deepseek_bridge = _bridge(tmp_path, deepseek=True)

    assert mtplx.effective_selector.endswith("Qwen3.8-27B-MTPLX-Optimized-Quality")
    assert mtplx.reasoning_effort == "medium"
    assert deepseek.effective_selector == "deepseek/deepseek-v4-flash"
    assert deepseek.reasoning_effort == "max"
    assert mtplx_bridge.r6_execution_profile_digest != deepseek_bridge.r6_execution_profile_digest
    assert mtplx_bridge.r1_profile_fingerprint != deepseek_bridge.r1_profile_fingerprint
    assert mtplx_bridge.bridge_digest != deepseek_bridge.bridge_digest
    for bridge in (mtplx_bridge, deepseek_bridge):
        body = bridge.to_dict()
        assert "credential_ref" not in json.dumps(body).lower()
        assert body["r6_execution_profile_digest"] != body["r1_profile_fingerprint"]

    with pytest.raises(ProfileBridgeError, match="profile_mapping_mismatch"):
        bad_r1 = build_r1_execution_profile(
            mtplx,
            executable=sys.executable,
            working_directory=tmp_path,
        )
        from dataclasses import replace

        build_profile_receipt_bridge(
            mtplx,
            replace(
                bad_r1,
                binding=replace(bad_r1.binding, effort="max"),
            ),
        )


def test_preflight_failure_has_zero_assignment_attempt_and_transport(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "preflight-failure"
    fake = FakeHarnessAdapter(catalog_ok=True)
    progress = _prepare_harness(
        workspace,
        fake,
        catalog=FakeCatalog(valid=False, failure_reason="catalog_missing"),
    )
    progress.start_execution(RUN_ID)
    _wait(workspace)

    assert fake.preflight_calls == 1
    assert fake.invoke_calls == []
    with _store(workspace) as store:
        row = store.get_work_unit_run(RUN_ID, 1, "ai-1")
        assert row is not None and row.status is NodeStatus.PENDING
        assert store.list_domain_objects("capability_work_assignment") == []
        diagnoses = store.list_domain_objects("r7_preflight_diagnosis")
        assert len(diagnoses) == 1
        _, payload = store.get_domain_object("r7_preflight_diagnosis", diagnoses[0][0])
        assert payload["ok"] is False
        assert payload["reason_codes"] == ["catalog_missing"]
    control = BackgroundRecoveryAdapter(
        runtime_dir=workspace / RUNTIME_DIR_NAME,
        canonical_project_id=PROJECT_ID,
    ).get_control(RUN_ID)
    assert control.state is ExecutionControlState.INTERRUPTED


def test_preflight_exception_is_cached_and_keeps_zero_dispatch_and_safe_diagnosis(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "preflight-exception"
    fake = FakeHarnessAdapter(
        preflight_exception=RuntimeError(
            "catalog_probe_failed: token=super-secret-value"
        )
    )
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    assert fake.preflight_calls == 1
    assert fake.preflight_results == []
    assert fake.invoke_calls == []
    with _store(workspace) as store:
        assert store.list_domain_objects("capability_work_assignment") == []
        assert store.list_domain_objects("capability_attempt_journal") == []
        diagnoses = store.list_domain_objects("r7_preflight_diagnosis")
        assert len(diagnoses) == 1
        _, payload = store.get_domain_object(
            "r7_preflight_diagnosis", diagnoses[0][0]
        )
        assert payload["reason_codes"] == ["catalog_probe_failed"]
        audit = json.dumps(
            [event.payload for event in store.audit_trail()], ensure_ascii=False
        )
        assert "super-secret-value" not in audit
    assert progress.progress(RUN_ID)["run_status_text"] == "已停止，可继续"


def test_successful_dispatch_seals_assignment_before_attempt_and_completion(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "dispatch-order"
    fake = FakeHarnessAdapter()
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    with _store(workspace) as store:
        events = store.audit_trail()
        positions: dict[str, int] = {}
        for index, event in enumerate(events):
            if event.event_type == EVENT_DOMAIN_OBJECT_PUT and event.payload.get("kind") == "capability_work_assignment":
                positions["assignment"] = index
            elif event.event_type == EVENT_CAPABILITY_ATTEMPT_DECLARED:
                positions["declared"] = index
            elif event.event_type == EVENT_CAPABILITY_ATTEMPT_CLAIMED:
                positions["claimed"] = index
            elif event.event_type == EVENT_WORK_UNIT_BEGIN:
                positions["begin"] = index
            elif event.event_type == EVENT_CAPABILITY_ATTEMPT_TERMINAL:
                positions["terminal"] = index
            elif event.event_type == EVENT_WORK_UNIT_COMPLETE:
                positions["complete"] = index
        assert list(sorted(positions, key=positions.get)) == [
            "assignment", "declared", "claimed", "begin", "terminal", "complete"
        ]
        attempt_id = "r7-capability:%s:1:ai-1:attempt-1" % RUN_ID
        attempt = store.get_capability_attempt(attempt_id)
        assert attempt is not None and attempt["status"] == "complete"
        assert attempt["terminal"] is True
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED


def test_two_connections_dispatch_one_ai_attempt_and_one_transport_call(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "concurrent-ai"
    fake = FakeHarnessAdapter(block=True)
    first = _prepare_harness(workspace, fake)
    second = RuntimeProgressAdapter(
        workspace,
        canonical_project_id=PROJECT_ID,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(),
    )
    first.start_execution(RUN_ID)
    assert fake.entered.wait(5.0)
    replay = second.start_execution(RUN_ID)
    assert replay["replayed"] is True
    assert len(fake.invoke_calls) == 1
    fake.release.set()
    _wait(workspace)
    assert len(_attempt_bindings(workspace, "ai-1")) == 1
    assert _event_types(workspace).count(EVENT_WORK_UNIT_BEGIN) == 1


def test_two_simultaneous_background_claimers_serialize_one_ai_dispatch(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "simultaneous-ai"
    fake = FakeHarnessAdapter(block=True)
    progress = _prepare_harness(workspace, fake)
    runners = [progress._background(), progress._background()]
    barrier = threading.Barrier(2)
    responses: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def start(runner: BackgroundRecoveryAdapter) -> None:
        try:
            barrier.wait(5.0)
            responses.append(runner.start_execution(RUN_ID))
        except BaseException as exc:  # pragma: no cover - assertion below
            errors.append(exc)

    threads = [threading.Thread(target=start, args=(runner,)) for runner in runners]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5.0)
    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert len(responses) == 2
    assert sorted(response["replayed"] for response in responses) == [False, True]
    assert fake.entered.wait(5.0)
    assert len(fake.invoke_calls) == 1
    fake.release.set()
    _wait(workspace)
    assert len(_attempt_bindings(workspace, "ai-1")) == 1
    assert _event_types(workspace).count(EVENT_WORK_UNIT_BEGIN) == 1


def test_inflight_lease_renews_during_block_and_cancelling_owner_cannot_claim_next(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "lease-block"
    fake = FakeHarnessAdapter(block=True)
    progress = _prepare_harness(
        workspace,
        fake,
        units=_units(count=2),
    )
    frozen = progress._harness_profiles[RUN_ID]
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / RUNTIME_DIR_NAME,
        canonical_project_id=PROJECT_ID,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(),
        harness_profile_factory=lambda _run_id: frozen,
        lease_seconds=0.15,
        heartbeat_seconds=0.02,
        sweep_seconds=0.001,
    )
    runner.start_execution(RUN_ID)
    assert fake.entered.wait(5.0)
    before = runner.get_control(RUN_ID)
    time.sleep(0.24)
    after = runner.get_control(RUN_ID)
    assert after.state is ExecutionControlState.RUNNING
    assert after.lease_expires_at is not None
    assert before.lease_expires_at is not None
    assert after.lease_expires_at > before.lease_expires_at
    assert runner.renew_inflight_lease(
        RUN_ID,
        after.manifest_revision,
        after.generation,
        after.owner_token,
    ) is True

    stopped = runner.cancel_execution(RUN_ID)
    assert stopped["run_status_text"] == "正在停止，当前分析可能完成；系统不会开始下一项工作。"
    cancelling = runner.get_control(RUN_ID)
    assert cancelling.state is ExecutionControlState.CANCELLING
    assert renew_inflight_lease(
        _runtime_db(workspace),
        RUN_ID,
        cancelling.manifest_revision,
        cancelling.generation,
        cancelling.owner_token,
        lease_seconds=0.15,
    ) is True
    fake.release.set()
    _wait(workspace)

    assert len(fake.invoke_calls) == 1
    with _store(workspace) as store:
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED
        assert store.get_work_unit_run(RUN_ID, 1, "ai-2").status is NodeStatus.PENDING


def test_retry_is_once_linked_and_preserves_input_profile_and_no_session(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "retry-chain"
    fake = FakeHarnessAdapter(states=("partial", "complete", "complete"))
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    bindings = _attempt_bindings(workspace, "ai-1")
    assert len(bindings) == 2
    assert bindings[0][2] == ""
    assert bindings[1][2] == bindings[0][1]
    assert len(fake.invoke_calls) == 2
    assert "session" not in json.dumps(fake.invoke_calls).lower()
    with _store(workspace) as store:
        first = store.get_capability_attempt(bindings[0][1])
        second = store.get_capability_attempt(bindings[1][1])
        assert first is not None and second is not None
        assert first["status"] == "partial"
        assert second["status"] == "complete"
        assert first["input_hash"] == second["input_hash"]
        assert first["profile_fingerprint"] == second["profile_fingerprint"]
        assert second["continued_from"] == first["attempt_id"]
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED
    with _store(workspace) as store:
        assert not continuable_ai_unit(store, RUN_ID, 1, "ai-1")


def test_retry_cap_and_failed_identity_do_not_self_spin(tmp_path: Path) -> None:
    workspace = tmp_path / "retry-cap"
    fake = FakeHarnessAdapter(states=("partial", "partial", "complete"))
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)
    assert len(fake.invoke_calls) == 2
    bindings = _attempt_bindings(workspace, "ai-1")
    assert [row[0] for row in bindings] == [1, 2]
    with _store(workspace) as store:
        assert not continuable_ai_unit(store, RUN_ID, 1, "ai-1")

    workspace_failed = tmp_path / "failed-no-retry"
    failed = FakeHarnessAdapter(
        states=("complete", "complete"),
        receipt_overrides={"unsupported_operation": "cancel"},
    )
    failed_progress = _prepare_harness(workspace_failed, failed)
    failed_progress.start_execution(RUN_ID)
    _wait(workspace_failed)
    assert len(failed.invoke_calls) == 1
    assert len(_attempt_bindings(workspace_failed, "ai-1")) == 1


@pytest.mark.parametrize("first_state", ["timed_out", "truncated"])
def test_timeout_and_truncated_attempts_get_one_linked_retry(
    tmp_path: Path, first_state: str
) -> None:
    workspace = tmp_path / ("retry-" + first_state)
    fake = FakeHarnessAdapter(states=(first_state, "complete"))
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    bindings = _attempt_bindings(workspace, "ai-1")
    assert len(bindings) == 2
    assert len(fake.invoke_calls) == 2
    with _store(workspace) as store:
        first = store.get_capability_attempt(bindings[0][1])
        second = store.get_capability_attempt(bindings[1][1])
        assert first is not None and second is not None
        assert first["status"] == ("timeout" if first_state == "timed_out" else "truncated")
        assert second["status"] == "complete"
        assert second["continued_from"] == first["attempt_id"]
        assert not continuable_ai_unit(store, RUN_ID, 1, "ai-1")
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile_digest", "0" * 64),
        ("input_digest", "0" * 64),
        ("fallback_used", True),
    ],
)
def test_timeout_with_identity_drift_fails_without_linked_retry(
    tmp_path: Path, field: str, value: Any
) -> None:
    workspace = tmp_path / ("timeout-identity-" + field)
    fake = FakeHarnessAdapter(
        states=("timed_out", "complete"),
        receipt_overrides={field: value},
    )
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    assert len(fake.invoke_calls) == 1
    bindings = _attempt_bindings(workspace, "ai-1")
    assert len(bindings) == 1
    with _store(workspace) as store:
        attempt = store.get_capability_attempt(bindings[0][1])
        assert attempt is not None and attempt["status"] == "failed"
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.FAILED


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile_digest", "0" * 64),
        ("invocation_id", "wrong-invocation"),
        ("input_digest", "0" * 64),
        ("fallback_used", True),
        ("unsupported_operation", "cancel"),
        ("analysis_complete", False),
    ],
)
def test_receipt_identity_and_transport_faults_fail_closed_without_retry(
    tmp_path: Path, field: str, value: Any
) -> None:
    _profile, _bridge, fake, result = _low_level_result(
        tmp_path,
        "complete",
        receipt_overrides={field: value},
    )
    assert result.status.value == "failed"
    assert len(fake.invoke_calls) == 1
    raw = json.dumps(result.transport_execution.raw_output, ensure_ascii=False)
    assert "super-secret-value" not in raw
    assert "super-secret-path.stdout.json" not in raw
    envelope = json.loads(result.transport_execution.stdout)
    assert envelope["result"]["status"] == "failed"


def test_transport_exception_is_failed_once_and_secret_free(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "transport-failure"
    fake = FakeHarnessAdapter(raise_on_invoke=True)
    progress = _prepare_harness(workspace, fake)
    progress.start_execution(RUN_ID)
    _wait(workspace)

    assert len(fake.invoke_calls) == 1
    assert len(_attempt_bindings(workspace, "ai-1")) == 1
    with _store(workspace) as store:
        attempt = store.get_capability_attempt(
            "r7-capability:%s:1:ai-1:attempt-1" % RUN_ID
        )
        assert attempt is not None
        assert attempt["status"] == "failed"
        assert attempt["terminal"] is True
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.FAILED
        audit = json.dumps(
            [event.payload for event in store.audit_trail()], ensure_ascii=False
        ).lower()
        assert "super-secret-value" not in audit


def test_run_owner_drift_rejects_late_terminal_before_retry_or_progress(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "late-terminal"
    fake = FakeHarnessAdapter(block=True)
    progress = _prepare_harness(workspace, fake)
    runner = progress._background()
    runner.start_execution(RUN_ID)
    assert fake.entered.wait(5.0)
    control = runner.get_control(RUN_ID)
    with sqlite3.connect(_runtime_db(workspace)) as connection:
        connection.execute(
            "UPDATE r7_execution_control SET owner_token=? WHERE run_id=?",
            ("drifted-owner", RUN_ID),
        )
        connection.commit()
    fake.release.set()
    _wait(workspace)

    assert len(fake.invoke_calls) == 1
    assert len(_attempt_bindings(workspace, "ai-1")) == 1
    with _store(workspace) as store:
        attempt_id = "r7-capability:%s:1:ai-1:attempt-1" % RUN_ID
        attempt = store.get_capability_attempt(attempt_id)
        assert attempt is not None
        assert attempt["status"] == "interrupted"
        assert attempt["terminal"] is False
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.BLOCKED
    assert control.owner_token != runner.get_control(RUN_ID).owner_token


def test_attempt_lease_drift_rejects_late_terminal_and_links_one_retry(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "late-attempt-lease"
    fake = FakeHarnessAdapter(block=True)
    progress = _prepare_harness(workspace, fake)
    runner = progress._background()
    runner.start_execution(RUN_ID)
    assert fake.entered.wait(5.0)
    attempt_id = "r7-capability:%s:1:ai-1:attempt-1" % RUN_ID
    with sqlite3.connect(_runtime_db(workspace)) as connection:
        status, owner = connection.execute(
            "SELECT status, owner_token FROM capability_attempt_journal "
            "WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
        assert status == "running" and owner
        connection.execute(
            "UPDATE capability_attempt_journal SET lease_expires_at=0 "
            "WHERE attempt_id=?",
            (attempt_id,),
        )
        connection.commit()
    fake.release.set()
    _wait(workspace)

    with _store(workspace) as store:
        attempt = store.get_capability_attempt(attempt_id)
        assert attempt is not None
        assert attempt["status"] == "interrupted"
        assert attempt["terminal"] is False
        bindings = _attempt_bindings(workspace, "ai-1")
        assert len(bindings) == 2
        second = store.get_capability_attempt(bindings[1][1])
        assert second is not None
        assert second["status"] == "complete"
        assert second["continued_from"] == attempt_id
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED
    assert len(fake.invoke_calls) == 2


def test_claimed_unbound_interruption_is_bound_then_resumed_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "claimed-unbound-recovery"
    fake = FakeHarnessAdapter(states=("complete",))
    progress = _prepare_harness(workspace, fake)
    original = CapabilityWorkUnitController.on_attempt_prepared

    def crash_before_bind(self, request, *, replaying):
        raise RuntimeError("synthetic crash after claim before bind")

    with monkeypatch.context() as scoped:
        scoped.setattr(
            CapabilityWorkUnitController,
            "on_attempt_prepared",
            crash_before_bind,
        )
        progress.start_execution(RUN_ID)
        _wait(workspace)

    attempt_id = "r7-capability:%s:1:ai-1:attempt-1" % RUN_ID
    with _store(workspace) as store:
        attempt = store.get_capability_attempt(attempt_id)
        assert attempt is not None and attempt["status"] == "interrupted"
        assert _attempt_bindings(workspace, "ai-1") == []
    assert fake.invoke_calls == []

    progress.resume_execution(RUN_ID)
    _wait(workspace)

    bindings = _attempt_bindings(workspace, "ai-1")
    assert [row[0] for row in bindings] == [1, 2]
    assert bindings[1][2] == attempt_id
    assert len(fake.invoke_calls) == 1
    with _store(workspace) as store:
        assert store.get_capability_attempt(attempt_id)["status"] == "interrupted"
        assert store.get_capability_attempt(bindings[1][1])["status"] == "complete"
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.PASSED


def test_retry_exhausted_unit_does_not_hide_continue_for_pending_work(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "retry-exhausted-with-pending"
    fake = FakeHarnessAdapter(states=("partial", "partial"))
    progress = _prepare_harness(workspace, fake, units=_units(count=2))
    runner = progress._background()
    original = runner._process_ai_unit

    def stop_after_first(store, claim, unit, stop_event):
        processed = original(store, claim, unit, stop_event)
        runner._release_claim(claim, interrupted=True)
        return False if processed else processed

    runner._process_ai_unit = stop_after_first
    runner.start_execution(RUN_ID)
    assert runner.wait(RUN_ID, timeout=5.0)

    snapshot = runner.progress(RUN_ID)
    assert snapshot["run_status_text"] == "本项分析未完成，已达到本次重试上限。"
    assert snapshot["available_actions"] == ["继续"]
    assert snapshot["run_state"] == "interrupted_resumable"
    with _store(workspace) as store:
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.FAILED
        assert store.get_work_unit_run(RUN_ID, 1, "ai-2").status is NodeStatus.PENDING


def test_retry_exhausted_without_remaining_work_is_stable_failed_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "retry-exhausted-failed"
    fake = FakeHarnessAdapter(states=("partial", "partial"))
    progress = _prepare_harness(workspace, fake)
    runner = progress._background()
    runner.start_execution(RUN_ID)
    assert runner.wait(RUN_ID, timeout=5.0)

    assert runner.get_control(RUN_ID).state is ExecutionControlState.FINISHED
    snapshot = runner.progress(RUN_ID)
    # Exhausted retries with no server-offered action are the stable failed
    # state; the run is never re-labelled as completed.
    assert snapshot["run_state"] == "failed"
    assert snapshot["run_status_text"] == "本项分析未完成，已达到本次重试上限。"
    assert snapshot["available_actions"] == []
    with _store(workspace) as store:
        assert store.get_work_unit_run(RUN_ID, 1, "ai-1").status is NodeStatus.FAILED
