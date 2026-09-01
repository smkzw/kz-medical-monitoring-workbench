"""Synthetic/offline tests for the application-owned R1 controller."""

from __future__ import annotations

import json
import threading

import pytest

import mm_r1.controller as controller_module
from mm_r1.adapters import AdapterState, ImmutableAdapterBinding
from mm_r1.capability_runtime import (
    ApiCapabilityRuntime,
    CapabilityRequest,
    ExecutionProfile,
    InvocationVersions,
    TransportKind,
)
from mm_r1.controller import (
    ASSIGNMENT_KIND,
    CapabilityWorkUnitController,
)
from mm_r1.domain import (
    CoverageUnit,
    ExecutionBasis,
    ExecutionManifest,
    IdempotencyConflictError,
    ManifestNode,
    ManifestWorkUnit,
    MonitoringRun,
    NodeStatus,
    NodeType,
    RunMode,
    SourceRevision,
    StoreError,
    content_hash,
)
from mm_r1.store import Store


RUN_ID = "synthetic-controller-run"
NODE_ID = "risk-analysis"
WORK_UNIT_ID = "risk-S001-AE"


def _prepare(store: Store) -> None:
    store.create_project("synthetic-controller-project", "Synthetic controller project")
    store.add_source_revision(SourceRevision(
        revision_id="synthetic-controller-source",
        project_id="synthetic-controller-project",
        source_type="listing",
        version="synthetic-v1",
        content_hash=content_hash({"fixture": "controller"}),
    ))
    store.create_run(MonitoringRun(
        run_id=RUN_ID,
        project_id="synthetic-controller-project",
        mode=RunMode.DAILY,
        data_cutoff="2026-08-09",
        source_revision_id="synthetic-controller-source",
        execution_basis=ExecutionBasis.FULL,
    ))
    store.set_manifest(ExecutionManifest(
        run_id=RUN_ID,
        nodes=[ManifestNode(NODE_ID, NodeType.AI_CANDIDATE)],
        work_units=[ManifestWorkUnit(
            work_unit_id=WORK_UNIT_ID,
            node_id=NODE_ID,
            label="分析受试者 S001 的 AE 风险",
            stage="风险分析",
            scope="risk_domain",
            target_ref="S001/AE",
            ordinal=1,
        )],
        graph_version="synthetic-controller-v1",
        schema_version="synthetic-schema-v1",
    ))


def _profile(profile_id: str = "synthetic-controller-profile") -> ExecutionProfile:
    binding = ImmutableAdapterBinding(
        binding_id="synthetic-controller-binding",
        capability="risk-analysis",
        provider="user-selected-provider",
        model="user-selected-model",
        selector="user-selected-selector",
        effort="user-selected-effort",
        adapter_version="controller-r1",
        allowed_tools=("read_synthetic_input",),
        isolation="fresh_context",
        endpoint="external",
    )
    return ExecutionProfile(
        profile_id=profile_id,
        transport=TransportKind.API,
        binding=binding,
        api_route="user-configured://risk-analysis",
        credential_ref="opaque-local-reference",
        runtime_revision="synthetic-runtime-v1",
        timeout_seconds=5,
    )


def _versions() -> InvocationVersions:
    return InvocationVersions(
        source_revision_id="synthetic-controller-source",
        rule_version="synthetic-rule-v1",
        knowledge_version="synthetic-knowledge-v1",
        graph_version="synthetic-controller-v1",
        schema_version="synthetic-schema-v1",
    )


def _success(request):
    coverage = dict(request["params"]["expected_coverage"][0])
    coverage["status"] = "covered"
    return {
        "jsonrpc": "2.0",
        "id": request["id"],
        "execution_id": "synthetic-controller-execution",
        "result": {
            "status": "complete",
            "execution_identity": request["params"]["execution_identity"],
            "candidate_payload": {"risk": "synthetic AE review item"},
            "produced_units": [coverage],
        },
    }


class RecordingTransport:
    def __init__(self, callback=None):
        self.callback = callback
        self.calls = []

    def __call__(self, request, profile):
        self.calls.append((request, profile))
        return self.callback(request) if self.callback else _success(request)


def _runtime(store, transport, profile=None):
    return ApiCapabilityRuntime(
        profile or _profile(),
        transport,
        manifest_revision_reader=lambda run_id: store.get_run(run_id).manifest_revision,
        attempt_journal=store,
        journal_owner_token="synthetic-controller-owner",
    )


def _execute(controller, runtime, attempt_id="controller-attempt-1", payload=None):
    return controller.execute(
        runtime,
        work_unit_id=WORK_UNIT_ID,
        attempt_id=attempt_id,
        monitoring_run_id=RUN_ID,
        node_id=NODE_ID,
        manifest_revision=1,
        versions=_versions(),
        payload=payload or {"subject_id": "S001", "domain": "AE"},
        expected_units=(CoverageUnit(scope="subject", key="S001"),),
    )


def _request(runtime, attempt_id="controller-attempt-1", payload=None):
    return CapabilityRequest.build(
        attempt_id=attempt_id,
        monitoring_run_id=RUN_ID,
        node_id=NODE_ID,
        manifest_revision=1,
        profile=runtime.profile,
        versions=_versions(),
        payload=payload or {"subject_id": "S001", "domain": "AE"},
        expected_units=(CoverageUnit(scope="subject", key="S001"),),
    )


def test_controller_binds_real_running_state_before_transport_and_closes_after_persistence(
    r1_store,
):
    _prepare(r1_store)
    observed = {}

    class RecordingController(CapabilityWorkUnitController):
        def on_attempt_prepared(self, request, *, replaying):
            super().on_attempt_prepared(request, replaying=replaying)
            row = r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID)
            observed["status"] = row.status
            observed["detail"] = row.detail
            observed["assignment_count"] = len(
                r1_store.list_domain_objects(ASSIGNMENT_KIND)
            )

    transport = RecordingTransport()
    controller = RecordingController(r1_store)
    result = _execute(controller, _runtime(r1_store, transport))

    assert result.status == AdapterState.COMPLETE
    assert observed == {
        "status": NodeStatus.RUNNING,
        "detail": "正在分析受试者 S001 的 AE 风险",
        "assignment_count": 1,
    }
    row = r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID)
    assert row.status == NodeStatus.PASSED
    assert row.detail == "已完成：分析受试者 S001 的 AE 风险"
    assert row.evidence_count > 0
    assert r1_store.list_facts(RUN_ID) == []
    assert r1_store.list_domain_objects("adapter_raw_output")
    assert r1_store.list_domain_objects("adapter_attempt_request")
    assert r1_store.structured_progress(RUN_ID)["percent"] == 100.0


def test_terminal_persistence_failure_leaves_running_then_reconciles_without_transport(
    r1_store, monkeypatch,
):
    _prepare(r1_store)
    controller = CapabilityWorkUnitController(r1_store)
    first_transport = RecordingTransport()
    profile = _profile("synthetic-persistence-recovery-profile")
    original = controller_module.persist_capability_attempt

    def fail_persistence(store, result):
        raise RuntimeError("synthetic persistence interruption")

    monkeypatch.setattr(controller_module, "persist_capability_attempt", fail_persistence)
    with pytest.raises(RuntimeError, match="persistence interruption"):
        _execute(controller, _runtime(r1_store, first_transport, profile=profile))
    assert len(first_transport.calls) == 1
    attempt = r1_store.get_capability_attempt("controller-attempt-1")
    assert attempt["terminal"] is True
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.RUNNING

    monkeypatch.setattr(controller_module, "persist_capability_attempt", original)
    replay_transport = RecordingTransport()
    replay_runtime = _runtime(r1_store, replay_transport, profile=profile)
    replay = controller.reconcile(replay_runtime, "controller-attempt-1")
    assert replay.status == AdapterState.COMPLETE
    assert replay_transport.calls == []
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PASSED


def test_transport_failure_is_sealed_and_closes_as_failed_with_evidence(r1_store):
    _prepare(r1_store)

    def fail_transport(request):
        raise RuntimeError("synthetic provider unavailable")

    result = _execute(
        CapabilityWorkUnitController(r1_store),
        _runtime(r1_store, RecordingTransport(fail_transport)),
    )
    assert result.status == AdapterState.FAILED
    assert result.adapter_run.raw_output is not None
    row = r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID)
    assert row.status == NodeStatus.FAILED
    assert row.detail == "未完成：分析受试者 S001 的 AE 风险"
    assert row.evidence_count > 0
    assert r1_store.list_facts(RUN_ID) == []


def test_partial_attempt_can_resume_on_same_work_unit_and_preserve_history(r1_store):
    _prepare(r1_store)
    calls = {"count": 0}

    def partial_then_complete(request):
        calls["count"] += 1
        response = _success(request)
        if calls["count"] == 1:
            response["result"]["status"] = "partial"
            response["result"]["produced_units"][0]["status"] = "partial"
        return response

    transport = RecordingTransport(partial_then_complete)
    runtime = _runtime(r1_store, transport)
    controller = CapabilityWorkUnitController(r1_store)
    first = _execute(controller, runtime, attempt_id="controller-partial-1")
    assert first.status == AdapterState.PARTIAL
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.FAILED

    resumed = controller.resume(
        runtime,
        first.request.attempt_id,
        attempt_id="controller-partial-2",
        manifest_revision=1,
    )
    assert resumed.status == AdapterState.COMPLETE
    assert calls["count"] == 2
    row = r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID)
    assert row.status == NodeStatus.PASSED
    bindings = r1_store._list_work_unit_capability_attempts(
        RUN_ID, 1, WORK_UNIT_ID
    )
    assert [item["attempt_id"] for item in bindings] == [
        "controller-partial-1", "controller-partial-2",
    ]
    feed = r1_store.structured_progress(RUN_ID)["feed"]
    assert [item["event_type"] for item in feed] == [
        "work_unit_begin", "work_unit_complete",
        "work_unit_attempt_bound", "work_unit_complete",
    ]
    assert [item["status"] for item in feed] == [
        "running", "failed", "running", "passed",
    ]


def test_pre_registered_assignment_survives_restart_before_journal_dispatch(tmp_path):
    db_path = tmp_path / "controller.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    first_store = Store(db_path, artifact_dir)
    _prepare(first_store)
    profile = _profile("synthetic-restart-profile")
    runtime = _runtime(first_store, RecordingTransport(), profile=profile)
    controller = CapabilityWorkUnitController(first_store)
    controller.register(_request(runtime, "controller-pre-registered"), WORK_UNIT_ID)
    assert first_store.get_capability_attempt("controller-pre-registered") is None
    first_store.close()

    reopened = Store(db_path, artifact_dir)
    transport = RecordingTransport()
    recovered_runtime = _runtime(reopened, transport, profile=profile)
    recovered = CapabilityWorkUnitController(reopened).reconcile(
        recovered_runtime, "controller-pre-registered"
    )
    assert recovered.status == AdapterState.COMPLETE
    assert len(transport.calls) == 1
    assert reopened.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PASSED
    reopened.close()


def test_terminal_journal_replay_after_crash_persists_and_closes_without_redispatch(r1_store):
    _prepare(r1_store)
    profile = _profile("synthetic-terminal-replay-profile")
    controller = CapabilityWorkUnitController(r1_store)
    first_transport = RecordingTransport()
    first_runtime = _runtime(r1_store, first_transport, profile=profile)
    request = _request(first_runtime, "controller-terminal-before-binding")
    controller.register(request, WORK_UNIT_ID)
    result = first_runtime.invoke(
        attempt_id=request.attempt_id,
        monitoring_run_id=request.monitoring_run_id,
        node_id=request.node_id,
        manifest_revision=request.manifest_revision,
        versions=request.versions,
        payload=request.payload,
        expected_units=request.expected_units,
    )
    assert result.status == AdapterState.COMPLETE
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PENDING

    replay_transport = RecordingTransport()
    replay = controller.reconcile(
        _runtime(r1_store, replay_transport, profile=profile),
        request.attempt_id,
    )
    assert replay.status == AdapterState.COMPLETE
    assert replay_transport.calls == []
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PASSED


def test_interrupted_registered_attempt_reconciles_to_paused_work_unit(r1_store):
    _prepare(r1_store)
    runtime = _runtime(r1_store, RecordingTransport())
    controller = CapabilityWorkUnitController(r1_store)
    request = _request(runtime, "controller-interrupted")
    controller.register(request, WORK_UNIT_ID)

    class FailBeforeTransport:
        def on_attempt_prepared(self, request, *, replaying):
            raise RuntimeError("synthetic controller crash")

        def on_attempt_terminal(self, result):
            raise AssertionError("terminal callback must not run")

        def on_attempt_interrupted(self, request, *, reason):
            pass

    with pytest.raises(RuntimeError, match="controller crash"):
        runtime.invoke(
            attempt_id=request.attempt_id,
            monitoring_run_id=request.monitoring_run_id,
            node_id=request.node_id,
            manifest_revision=request.manifest_revision,
            versions=request.versions,
            payload=request.payload,
            expected_units=request.expected_units,
            lifecycle_observer=FailBeforeTransport(),
        )
    assert r1_store.get_capability_attempt(request.attempt_id)["status"] == "interrupted"
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PENDING

    assert controller.reconcile(runtime, request.attempt_id) is None
    row = r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID)
    assert row.status == NodeStatus.BLOCKED
    assert row.detail == "已暂停：分析受试者 S001 的 AE 风险"

    resumed = controller.resume(
        runtime,
        request.attempt_id,
        attempt_id="controller-interrupted-resumed",
        manifest_revision=1,
    )
    assert resumed.status == AdapterState.COMPLETE
    assert r1_store.get_work_unit_run(
        RUN_ID, 1, WORK_UNIT_ID
    ).status == NodeStatus.PASSED


def test_assignment_conflict_and_profile_mismatch_fail_before_transport(r1_store):
    _prepare(r1_store)
    controller = CapabilityWorkUnitController(r1_store)
    transport = RecordingTransport()
    runtime = _runtime(r1_store, transport)
    controller.register(_request(runtime), WORK_UNIT_ID)
    with pytest.raises(IdempotencyConflictError, match="different frozen request"):
        controller.register(
            _request(runtime, payload={"subject_id": "S001", "domain": "CM"}),
            WORK_UNIT_ID,
        )
    assert len(r1_store.list_domain_objects(ASSIGNMENT_KIND)) == 1
    assert transport.calls == []

    wrong_runtime = _runtime(
        r1_store,
        transport,
        profile=_profile("different-controller-profile"),
    )
    with pytest.raises(IdempotencyConflictError, match="execution profile"):
        controller.reconcile(wrong_runtime, "controller-attempt-1")
    assert transport.calls == []


def test_concurrent_conflicting_assignment_keeps_one_recoverable_version(tmp_path):
    db_path = tmp_path / "controller-concurrent.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as setup:
        _prepare(setup)
    profile = _profile("synthetic-concurrent-assignment-profile")
    barrier = threading.Barrier(2)
    successes = []
    errors = []

    def register(domain):
        try:
            with Store(db_path, artifact_dir) as store:
                runtime = _runtime(store, RecordingTransport(), profile=profile)
                request = _request(
                    runtime,
                    "controller-concurrent-attempt",
                    payload={"subject_id": "S001", "domain": domain},
                )
                barrier.wait()
                assignment = CapabilityWorkUnitController(store).register(
                    request, WORK_UNIT_ID
                )
                successes.append(assignment.request_hash)
        except BaseException as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=register, args=("AE",)),
        threading.Thread(target=register, args=("CM",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert len(successes) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], IdempotencyConflictError)

    with Store(db_path, artifact_dir) as verified:
        row = verified.get_domain_object(
            ASSIGNMENT_KIND,
            "capability-work-assignment:controller-concurrent-attempt",
        )
        assert row is not None and row[0] == 1
        controller = CapabilityWorkUnitController(verified)
        assert controller.registered_attempts() == (
            "controller-concurrent-attempt",
        )


def test_rehashed_assignment_tamper_is_rejected_against_audit_evidence(r1_store):
    _prepare(r1_store)
    controller = CapabilityWorkUnitController(r1_store)
    runtime = _runtime(r1_store, RecordingTransport())
    assignment = controller.register(_request(runtime, "controller-tamper"), WORK_UNIT_ID)
    damaged = assignment.to_dict()
    damaged["blocked_detail"] = "已暂停：被篡改的工作项"
    r1_store._conn.execute(
        "UPDATE domain_objects SET object_json=?, content_hash=?"
        " WHERE kind=? AND object_id=? AND version=1",
        (
            json.dumps(damaged, ensure_ascii=False),
            content_hash(damaged),
            ASSIGNMENT_KIND,
            assignment.object_id,
        ),
    )
    with pytest.raises(StoreError, match="audit evidence"):
        controller.reconcile(runtime, assignment.attempt_id)


def test_cached_runtime_replay_reapplies_idempotent_controller_callbacks(r1_store):
    _prepare(r1_store)
    transport = RecordingTransport()
    runtime = _runtime(r1_store, transport)
    controller = CapabilityWorkUnitController(r1_store)
    first = _execute(controller, runtime)
    replay = _execute(controller, runtime)
    assert replay == first
    assert len(transport.calls) == 1
    assert r1_store.get_work_unit_run(RUN_ID, 1, WORK_UNIT_ID).status == NodeStatus.PASSED
