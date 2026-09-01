"""Offline R1 contract tests for user-configured API/harness execution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import mm_r1.capability_runtime as capability_runtime
from mm_r1.adapters import (
    AdapterState,
    ImmutableAdapterBinding,
    load_persisted_raw_output,
)
from mm_r1.capability_runtime import (
    ApiCapabilityRuntime,
    AttemptIdentityError,
    AttemptStage,
    CapabilityRequest,
    CapabilityRuntimeError,
    ExecutionProfile,
    HarnessCapabilityRuntime,
    HarnessIsolationPolicy,
    InvocationVersions,
    StaleAttemptError,
    TransportKind,
    persist_capability_attempt,
)
from mm_r1.domain import (
    AnalysisState,
    CoverageUnit,
    ExecutionBasis,
    ExecutionManifest,
    IdempotencyConflictError,
    ManifestNode,
    MonitoringRun,
    NodeType,
    RunMode,
    SourceRevision,
    StaleCallbackError,
    StoreError,
    content_hash,
)
from mm_r1.store import Store


def test_lifecycle_observer_is_exposed_by_the_public_package_surface():
    import mm_r1
    from mm_r1.capability_runtime import AttemptLifecycleObserver

    assert mm_r1.AttemptLifecycleObserver is AttemptLifecycleObserver


def _journal(store: Store):
    """Synthetic test access to the private runtime mutation facade."""

    return store._runtime_attempt_journal()


def _binding(endpoint="external", binding_id="binding-api"):
    return ImmutableAdapterBinding(
        binding_id=binding_id,
        capability="risk-candidate-generation",
        provider="user-selected-provider",
        model="user-selected-model",
        selector="user-selected-selector",
        effort="user-selected-effort",
        adapter_version="capability-runtime-r1",
        allowed_tools=("read_synthetic_input",),
        isolation="fresh_context",
        endpoint=endpoint,
    )


def _api_profile(**overrides):
    values = dict(
        profile_id="profile-api-1",
        transport=TransportKind.API,
        binding=_binding(),
        api_route="user-configured://risk-analysis",
        credential_ref="opaque-keychain-reference",
        runtime_revision="user-configured-api-revision-1",
        timeout_seconds=5,
    )
    values.update(overrides)
    return ExecutionProfile(**values)


def _harness_profile(argv, **overrides):
    values = dict(
        profile_id="profile-harness-1",
        transport=TransportKind.HARNESS,
        binding=_binding("local", "binding-harness"),
        argv=tuple(argv),
        working_directory=str(Path.cwd()),
        timeout_seconds=2,
    )
    values.update(overrides)
    return ExecutionProfile(**values)


def _python_executable_closure():
    executable = Path(sys.executable)
    resolved = executable.resolve()
    values = [str(executable), str(resolved)]
    app_executable = resolved.parent.parent / "Resources/Python.app/Contents/MacOS/Python"
    if app_executable.is_file():
        values.append(str(app_executable))
    return tuple(dict.fromkeys(values))


def _python_runtime_read_roots():
    """Declare a virtualenv as runtime input when the test interpreter uses one.

    Seatbelt correctly denies user-directory content unless declared.  A venv
    stores ``pyvenv.cfg`` and site-packages below such a directory, so its root
    must be part of the frozen read-only runtime closure.  System Python needs
    no additional root because its files live in the system-read baseline.
    """
    prefix = Path(sys.prefix)
    if sys.prefix != sys.base_prefix and (prefix / "pyvenv.cfg").is_file():
        return (str(prefix),)
    return ()


def _isolated_harness_profile(argv, *, readable_roots, writable_roots=(), **overrides):
    policy = HarnessIsolationPolicy(
        readable_roots=tuple(dict.fromkeys(
            tuple(str(value) for value in readable_roots) + _python_runtime_read_roots()
        )),
        writable_roots=tuple(str(value) for value in writable_roots),
        allowed_executables=_python_executable_closure(),
    )
    return _harness_profile(argv, harness_isolation=policy, **overrides)


def _versions():
    return InvocationVersions(
        source_revision_id="synthetic-revision-2",
        rule_version="synthetic-rules-1",
        knowledge_version="synthetic-knowledge-1",
        graph_version="synthetic-graph-1",
        schema_version="synthetic-schema-1",
        mapping_version="synthetic-mapping-1",
    )


def _units():
    return (CoverageUnit(scope="subject", key="SYN-S001"),)


def _invoke(
    runtime,
    attempt_id="attempt-001",
    payload=None,
    manifest_revision=1,
    monitoring_run_id="monitoring-run-1",
):
    return runtime.invoke(
        attempt_id=attempt_id,
        monitoring_run_id=monitoring_run_id,
        node_id="ai-risk-node",
        manifest_revision=manifest_revision,
        versions=_versions(),
        payload=payload or {"subject_id": "SYN-S001"},
        expected_units=_units(),
    )


def _success_response(request, status="complete", produced_status="covered", payload=None):
    unit = dict(request["params"]["expected_coverage"][0])
    unit["status"] = produced_status
    return {
        "jsonrpc": "2.0",
        "id": request["id"],
        "execution_id": "synthetic-execution-1",
        "result": {
            "status": status,
            "execution_identity": request["params"]["execution_identity"],
            "candidate_payload": payload or {"risk": "synthetic candidate"},
            "produced_units": [unit],
        },
    }


def _revision_one(run_id):
    return 1


def _api_runtime(transport, profile=None, revision_reader=_revision_one, **runtime_kwargs):
    return ApiCapabilityRuntime(
        profile or _api_profile(),
        transport,
        manifest_revision_reader=revision_reader,
        **runtime_kwargs,
    )


def _harness_runtime(profile, revision_reader=_revision_one, **runtime_kwargs):
    return HarnessCapabilityRuntime(
        profile,
        manifest_revision_reader=revision_reader,
        **runtime_kwargs,
    )


class RecordingTransport:
    def __init__(self, response=None, callback=None):
        self.response = response
        self.callback = callback
        self.calls = []

    def __call__(self, request, profile):
        self.calls.append((request, profile))
        if self.callback is not None:
            return self.callback(request, profile)
        if self.response is not None:
            return self.response
        return _success_response(request)


def _write_harness(tmp_path, body, name="synthetic_harness.py"):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def _prepare_journal_store(store):
    project_id = "synthetic-journal-project"
    revision_id = "synthetic-journal-revision"
    run_id = "monitoring-run-1"
    store.create_project(project_id, "SYNTHETIC journal project")
    store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTHETIC-JOURNAL-1",
            content_hash=content_hash({"revision": revision_id}),
        )
    )
    store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-CUTOFF-JOURNAL",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    store.set_manifest(
        ExecutionManifest(
            run_id=run_id,
            graph_id="synthetic-capability-journal-graph",
            nodes=[ManifestNode(node_id="ai-risk-node", node_type=NodeType.AI_CANDIDATE)],
        )
    )
    return run_id


def test_execution_profile_is_frozen_fingerprinted_and_does_not_expose_credential_value(tmp_path):
    profile = _api_profile()
    assert profile.fingerprint == content_hash(profile.public_dict())
    assert profile.public_dict()["credential_ref_present"] is True
    assert "opaque-keychain-reference" not in json.dumps(profile.public_dict())
    assert _api_profile(credential_ref="another-opaque-reference").fingerprint != profile.fingerprint
    with pytest.raises(FrozenInstanceError):
        profile.api_route = "changed"
    with pytest.raises(ValueError, match="absolute"):
        _harness_profile(("python", "worker.py"))
    with pytest.raises(ValueError, match="non-empty absolute directory"):
        ExecutionProfile(
            profile_id="missing-harness-cwd",
            transport=TransportKind.HARNESS,
            binding=_binding("local", "binding-missing-cwd"),
            argv=(sys.executable, "worker.py"),
        )
    with pytest.raises(ValueError, match="requires api_route"):
        ExecutionProfile(
            profile_id="bad-api",
            transport=TransportKind.API,
            binding=_binding(),
        )
    with pytest.raises(ValueError, match="query"):
        _api_profile(api_route="https://example.invalid/analyze?api_key=SYNTHETIC_SECRET")
    harness = _harness_profile((sys.executable, "--token", "SYNTHETIC_SECRET"))
    assert "SYNTHETIC_SECRET" not in json.dumps(harness.public_dict())
    with pytest.raises(ValueError, match="manifest_revision_reader"):
        ApiCapabilityRuntime(_api_profile(), RecordingTransport())


def test_api_and_harness_request_contract_freezes_user_choice_versions_and_coverage():
    transport = RecordingTransport()
    result = _invoke(_api_runtime(transport))
    request = result.request.to_jsonrpc()
    assert request["jsonrpc"] == "2.0"
    assert request["id"] == "attempt-001"
    assert request["method"] == "medical_monitoring.analyze"
    assert request["params"]["binding"]["provider"] == "user-selected-provider"
    assert request["params"]["versions"] == _versions().to_dict()
    assert request["params"]["expected_coverage"][0]["key"] == "SYN-S001"
    assert result.request.profile_fingerprint == result.profile.fingerprint
    assert result.request.input_hash == result.adapter_run.binding.input_hash


def test_api_complete_is_candidate_only_with_raw_output_and_structured_work_events():
    result = _invoke(_api_runtime(RecordingTransport()))
    assert result.status == AdapterState.COMPLETE
    assert result.adapter_run.is_complete_and_covered()
    assert result.adapter_run.is_candidate_only()
    assert result.adapter_run.can_promote is False
    assert result.adapter_run.raw_output.source == "api_transport"
    assert [item.stage for item in result.work_events] == [
        AttemptStage.DECLARED,
        AttemptStage.STARTED,
        AttemptStage.RAW_SEALED,
        AttemptStage.PARSE_CLASSIFIED,
        AttemptStage.CANDIDATE_REGISTERED,
        AttemptStage.TERMINAL,
    ]


def test_api_incomplete_coverage_and_explicit_truncation_fail_closed():
    partial_transport = RecordingTransport(callback=lambda request, profile: _success_response(
        request, status="complete", produced_status="partial"
    ))
    partial = _invoke(_api_runtime(partial_transport))
    assert partial.status == AdapterState.PARTIAL
    assert not partial.adapter_run.is_complete_and_covered()
    assert partial.adapter_run.candidate_artifact.is_publishable()[0] is False

    truncated_transport = RecordingTransport(callback=lambda request, profile: _success_response(
        request, status="truncated", produced_status="truncated"
    ))
    truncated = _invoke(_api_runtime(truncated_transport), attempt_id="attempt-truncated")
    assert truncated.status == AdapterState.TRUNCATED
    assert truncated.adapter_run.candidate_artifact.is_publishable()[0] is False


def test_transport_cannot_self_declare_complete_with_missing_or_not_evaluable_coverage():
    def missing_status(request, profile):
        response = _success_response(request)
        response["result"]["produced_units"][0].pop("status")
        return response

    missing = _invoke(_api_runtime(RecordingTransport(callback=missing_status)))
    assert missing.status == AdapterState.FAILED
    assert missing.adapter_run.candidate_artifact is None
    assert "explicit status" in missing.adapter_run.failure_reason

    not_evaluable = _invoke(
        _api_runtime(
            RecordingTransport(
                callback=lambda request, profile: _success_response(
                    request, produced_status="not_evaluable"
                )
            )
        ),
        attempt_id="attempt-not-evaluable",
    )
    assert not_evaluable.status == AdapterState.PARTIAL
    assert not not_evaluable.adapter_run.is_complete_and_covered()
    assert not_evaluable.adapter_run.candidate_artifact.is_publishable()[0] is False


def test_expected_coverage_denominator_rejects_preclassified_status_or_reason():
    runtime = _api_runtime(RecordingTransport())
    for unit in (
        CoverageUnit(
            scope="subject",
            key="SYN-S001",
            status="not_evaluable",
            reason="caller attempted to preclassify denominator",
        ),
        CoverageUnit(scope="subject", key="SYN-S001", expected=False),
    ):
        with pytest.raises(ValueError, match="denominator"):
            runtime.invoke(
                attempt_id="attempt-denominator-%s" % str(unit.expected),
                monitoring_run_id="monitoring-run-1",
                node_id="ai-risk-node",
                manifest_revision=1,
                versions=_versions(),
                payload={"subject_id": "SYN-S001"},
                expected_units=(unit,),
            )


@pytest.mark.parametrize("response", [
    {"jsonrpc": "2.0", "id": "wrong", "result": {}},
    {"jsonrpc": "2.0", "id": "attempt-001", "error": {"code": -32000, "message": "provider unavailable"}},
    {"jsonrpc": "2.0", "id": "attempt-001", "result": "not-an-object"},
])
def test_api_malformed_or_error_response_is_failed_and_raw_is_preserved(response):
    result = _invoke(_api_runtime(RecordingTransport(response=response)))
    assert result.status == AdapterState.FAILED
    assert result.adapter_run.candidate_artifact is None
    assert result.adapter_run.raw_output is not None
    assert result.adapter_run.failure_reason


def test_response_execution_identity_must_match_frozen_profile():
    def wrong_identity(request, profile):
        response = _success_response(request)
        response["result"]["execution_identity"]["model"] = "silently-substituted-model"
        return response

    result = _invoke(_api_runtime(RecordingTransport(callback=wrong_identity)))
    assert result.status == AdapterState.FAILED
    assert result.adapter_run.candidate_artifact is None
    assert "execution identity" in result.adapter_run.failure_reason


def test_duplicate_attempt_is_idempotent_but_conflicting_reuse_fails():
    transport = RecordingTransport()
    runtime = _api_runtime(transport)
    first = _invoke(runtime)
    replay = _invoke(runtime)
    assert replay is first
    assert len(transport.calls) == 1
    with pytest.raises(AttemptIdentityError):
        _invoke(runtime, payload={"subject_id": "SYN-DIFFERENT"})


def test_nonterminal_transport_status_is_classified_failed_and_replay_does_not_wait():
    transport = RecordingTransport(
        callback=lambda request, profile: _success_response(request, status="running")
    )
    runtime = _api_runtime(transport)
    first = _invoke(runtime, attempt_id="attempt-running")
    replay = _invoke(runtime, attempt_id="attempt-running")
    assert first.status == AdapterState.FAILED
    assert replay is first
    assert len(transport.calls) == 1


def test_concurrent_duplicate_attempt_waits_for_one_execution_and_reuses_result():
    entered = threading.Event()
    release = threading.Event()

    def delayed(request, profile):
        entered.set()
        assert release.wait(timeout=2)
        return _success_response(request)

    transport = RecordingTransport(callback=delayed)
    runtime = _api_runtime(transport)
    results = []

    def invoke():
        results.append(_invoke(runtime, attempt_id="attempt-concurrent"))

    first = threading.Thread(target=invoke)
    second = threading.Thread(target=invoke)
    first.start()
    assert entered.wait(timeout=1)
    second.start()
    time.sleep(0.03)
    assert len(transport.calls) == 1
    release.set()
    first.join(timeout=2)
    second.join(timeout=2)
    assert len(results) == 2
    assert results[0] is results[1]
    assert len(transport.calls) == 1


def test_manifest_revision_is_checked_before_and_after_transport():
    state = {"revision": 2}
    transport = RecordingTransport()
    runtime = _api_runtime(transport, revision_reader=lambda run_id: state["revision"])
    with pytest.raises(StaleAttemptError):
        _invoke(runtime, manifest_revision=1)
    assert transport.calls == []

    state["revision"] = 1

    def mutate_revision(request, profile):
        state["revision"] = 2
        return _success_response(request)

    late = _invoke(
        _api_runtime(
            RecordingTransport(callback=mutate_revision),
            profile=_api_profile(profile_id="profile-api-2"),
            revision_reader=lambda run_id: state["revision"],
        ),
        attempt_id="attempt-late",
    )
    assert late.status == AdapterState.FAILED
    assert late.adapter_run.candidate_artifact is None
    assert "stale manifest" in late.adapter_run.failure_reason


def test_resume_rejects_changed_manifest_before_transport_dispatch():
    transport = RecordingTransport(
        callback=lambda request, profile: _success_response(
            request, status="partial", produced_status="partial"
        )
    )
    runtime = _api_runtime(transport)
    first = _invoke(runtime, attempt_id="attempt-resume-source")
    assert first.status == AdapterState.PARTIAL
    with pytest.raises(AttemptIdentityError, match="original manifest"):
        runtime.resume("attempt-resume-source", attempt_id="attempt-resume-wrong", manifest_revision=2)
    assert len(transport.calls) == 1


def test_api_timeout_and_cancel_share_terminal_lifecycle_contract():
    timed = _api_runtime(
        RecordingTransport(callback=lambda request, profile: (time.sleep(0.08), _success_response(request))[1]),
        profile=_api_profile(profile_id="profile-api-timeout", timeout_seconds=0.02),
    )
    started = time.monotonic()
    timeout_result = _invoke(timed, attempt_id="attempt-api-timeout")
    assert timeout_result.status == AdapterState.TIMEOUT
    assert time.monotonic() - started < 0.07

    entered = threading.Event()
    release = threading.Event()

    def blocked(request, profile):
        entered.set()
        release.wait(timeout=2)
        return _success_response(request)

    runtime = _api_runtime(
        RecordingTransport(callback=blocked),
        profile=_api_profile(profile_id="profile-api-cancel", timeout_seconds=5),
    )
    box = {}
    thread = threading.Thread(
        target=lambda: box.setdefault("result", _invoke(runtime, attempt_id="attempt-api-cancel"))
    )
    thread.start()
    assert entered.wait(timeout=1)
    assert runtime.cancel("attempt-api-cancel")
    thread.join(timeout=1)
    release.set()
    assert not thread.is_alive()
    assert box["result"].status == AdapterState.CANCELLED
    assert box["result"].adapter_run.candidate_artifact is None


def test_real_harness_process_uses_shared_contract_without_shell(tmp_path):
    script = _write_harness(
        tmp_path,
        """import json, sys
request = json.load(sys.stdin)
unit = dict(request['params']['expected_coverage'][0])
unit['status'] = 'covered'
print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': {
    'status': 'complete',
    'execution_identity': request['params']['execution_identity'],
    'candidate_payload': {'risk': 'synthetic harness candidate'},
    'produced_units': [unit],
}}, ensure_ascii=False))
""",
    )
    profile = _harness_profile((sys.executable, str(script)), working_directory=str(tmp_path))
    result = _invoke(_harness_runtime(profile), attempt_id="attempt-harness")
    assert result.status == AdapterState.COMPLETE
    assert result.adapter_run.raw_output.source == "harness_process"
    assert result.transport_execution.return_code == 0
    assert result.adapter_run.candidate_artifact.payload["candidate_payload"]["risk"] == "synthetic harness candidate"


def test_harness_invalid_json_and_nonzero_exit_preserve_raw_and_fail(tmp_path):
    invalid = _write_harness(tmp_path, "print('not-json')\n", "invalid.py")
    result = _invoke(
        _harness_runtime(_harness_profile((sys.executable, str(invalid)))),
        attempt_id="attempt-invalid",
    )
    assert result.status == AdapterState.FAILED
    assert result.adapter_run.raw_output is not None
    assert "not valid JSON" in result.adapter_run.failure_reason

    nonzero = _write_harness(tmp_path, "import sys\nprint('{}')\nsys.exit(7)\n", "nonzero.py")
    failed = _invoke(
        _harness_runtime(_harness_profile((sys.executable, str(nonzero)))),
        attempt_id="attempt-nonzero",
    )
    assert failed.status == AdapterState.FAILED
    assert "code 7" in failed.adapter_run.failure_reason


def test_harness_timeout_and_output_limit_are_distinct_terminal_states(tmp_path):
    sleeper = _write_harness(tmp_path, "import time\ntime.sleep(1)\n", "timeout.py")
    timed_out = _invoke(
        _harness_runtime(_harness_profile((sys.executable, str(sleeper)), timeout_seconds=0.05)),
        attempt_id="attempt-timeout",
    )
    assert timed_out.status == AdapterState.TIMEOUT
    assert timed_out.transport_execution.timed_out

    noisy = _write_harness(tmp_path, "print('x' * 2000)\n", "noisy.py")
    truncated = _invoke(
        _harness_runtime(
            _harness_profile((sys.executable, str(noisy)), output_limit_chars=100)
        ),
        attempt_id="attempt-output-limit",
    )
    assert truncated.status == AdapterState.TRUNCATED
    assert truncated.transport_execution.output_truncated
    raw = json.loads(truncated.adapter_run.raw_output.raw_output_json)["stdout"]
    assert len(raw) > 100


def test_harness_file_identity_drift_fails_before_process_dispatch(tmp_path):
    script = _write_harness(tmp_path, "print('{}')\n", "mutable.py")
    profile = _harness_profile((sys.executable, str(script)))
    runtime = _harness_runtime(profile)
    script.write_text("print('changed')\n", encoding="utf-8")
    with pytest.raises(Exception, match="execution file changed"):
        _invoke(runtime, attempt_id="attempt-drift")


def test_allowlisted_environment_is_frozen_hashed_and_never_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("MM_SYNTHETIC_SECRET", "SYNTHETIC_SECRET_VALUE")
    script = _write_harness(tmp_path, "print('{}')\n", "environment.py")
    profile = _harness_profile(
        (sys.executable, str(script)),
        environment_keys=("MM_SYNTHETIC_SECRET",),
    )
    assert profile.execution_environment()["MM_SYNTHETIC_SECRET"] == "SYNTHETIC_SECRET_VALUE"
    assert "SYNTHETIC_SECRET_VALUE" not in json.dumps(profile.public_dict())
    runtime = _harness_runtime(profile)
    monkeypatch.setenv("MM_SYNTHETIC_SECRET", "CHANGED_AFTER_FREEZE")
    with pytest.raises(Exception, match="environment values changed"):
        _invoke(runtime, attempt_id="attempt-environment-drift")


def test_harness_cancel_is_idempotent_and_does_not_create_candidate(tmp_path):
    sleeper = _write_harness(tmp_path, "import time\ntime.sleep(5)\n", "cancel.py")
    runtime = _harness_runtime(
        _harness_profile((sys.executable, str(sleeper)), timeout_seconds=10)
    )
    box = {}

    def run():
        box["result"] = _invoke(runtime, attempt_id="attempt-cancel")

    thread = threading.Thread(target=run)
    thread.start()
    cancelled = False
    for _ in range(100):
        if runtime.cancel("attempt-cancel"):
            cancelled = True
            break
        time.sleep(0.01)
    thread.join(timeout=3)
    assert cancelled
    assert not thread.is_alive()
    assert box["result"].status == AdapterState.CANCELLED
    assert box["result"].adapter_run.candidate_artifact is None
    assert runtime.cancel("attempt-cancel") is False


def test_resume_creates_new_attempt_with_same_input_identity_and_preserves_history():
    calls = {"count": 0}

    def sequence(request, profile):
        calls["count"] += 1
        if calls["count"] == 1:
            return _success_response(request, status="partial", produced_status="partial")
        return _success_response(request)

    runtime = _api_runtime(RecordingTransport(callback=sequence))
    first = _invoke(runtime, attempt_id="attempt-partial")
    resumed = runtime.resume("attempt-partial", attempt_id="attempt-resumed", manifest_revision=1)
    assert first.status == AdapterState.PARTIAL
    assert resumed.status == AdapterState.COMPLETE
    assert resumed.request.continued_from == first.request.attempt_id
    assert resumed.request.input_hash == first.request.input_hash
    assert first.status == AdapterState.PARTIAL


def test_persistence_uses_shared_store_is_idempotent_and_never_promotes_facts(r1_store):
    project_id = "synthetic-capability-project"
    revision_id = "synthetic-capability-revision"
    run_id = "monitoring-run-1"
    r1_store.create_project(project_id, "SYNTHETIC capability project")
    r1_store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTHETIC-1",
            content_hash=content_hash({"revision": revision_id}),
        )
    )
    r1_store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-CUTOFF-1",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    result = _invoke(_api_runtime(RecordingTransport()))
    receipt = persist_capability_attempt(r1_store, result)
    replay = persist_capability_attempt(r1_store, result)
    assert receipt.adapter.artifact_id == replay.adapter.artifact_id
    assert r1_store.verify_artifact(receipt.adapter.artifact_id)
    assert r1_store.list_facts(run_id) == []
    assert r1_store.list_domain_objects("execution_profile")
    assert r1_store.list_domain_objects("adapter_attempt_request")
    assert len(r1_store.list_domain_objects("adapter_work_event")) == len(result.work_events)
    run = r1_store.get_run(run_id)
    assert run.analysis_state == AnalysisState.NOT_STARTED
    assert run.output_state.value == "not_published"
    public_profiles = r1_store.list_domain_objects("execution_profile")
    assert "opaque-keychain-reference" not in json.dumps(public_profiles)


def test_raw_provenance_persistence_precedes_candidate_commit():
    result = _invoke(_api_runtime(RecordingTransport()), attempt_id="attempt-order")
    events = []

    class RejectRawStore:
        def put_domain_object(self, kind, *args, **kwargs):
            events.append(kind)
            if kind == "adapter_raw_output":
                raise RuntimeError("injected raw persistence failure")
            return 1

        def stage_artifact(self, *args, **kwargs):
            events.append("stage_candidate")
            return "staged"

        def commit_artifact(self, *args, **kwargs):
            events.append("commit_candidate")
            return args[-1]

        def verify_adapter_raw_output(self, *args, **kwargs):
            return False

    with pytest.raises(RuntimeError, match="raw persistence"):
        persist_capability_attempt(RejectRawStore(), result)
    assert events == ["adapter_raw_output"]


def test_domain_object_read_rejects_outer_content_hash_corruption(r1_store):
    version = r1_store.put_domain_object(
        "synthetic_integrity_probe",
        "synthetic-integrity-object",
        {"fixture_marker": "SYNTHETIC", "value": 1},
    )
    assert version == 1
    r1_store._conn.execute(
        "UPDATE domain_objects SET object_json=? WHERE kind=? AND object_id=? AND version=?",
        (
            json.dumps({"fixture_marker": "SYNTHETIC", "value": 2}),
            "synthetic_integrity_probe",
            "synthetic-integrity-object",
            version,
        ),
    )
    with pytest.raises(StoreError, match="domain object content hash mismatch"):
        r1_store.get_domain_object(
            "synthetic_integrity_probe", "synthetic-integrity-object", version=version
        )


def test_raw_output_idempotency_replay_rejects_deleted_authoritative_row(r1_store):
    result = _invoke(
        _api_runtime(RecordingTransport()),
        attempt_id="attempt-raw-deleted-replay",
    )
    raw = result.adapter_run.raw_output
    object_id = "adapter-raw:%s" % raw.raw_output_ref
    idempotency_key = "adapter-persist:%s:adapter_raw_output" % result.adapter_run.run_id

    assert r1_store.put_domain_object(
        "adapter_raw_output",
        object_id,
        raw,
        idempotency_key=idempotency_key,
    ) == 1
    r1_store._conn.execute(
        "DELETE FROM domain_objects WHERE kind='adapter_raw_output' AND object_id=?",
        (object_id,),
    )

    with pytest.raises(StoreError, match="idempotency replay references a missing record"):
        r1_store.put_domain_object(
            "adapter_raw_output",
            object_id,
            raw,
            idempotency_key=idempotency_key,
        )
    assert r1_store._conn.execute(
        "SELECT COUNT(*) FROM domain_objects WHERE kind='adapter_raw_output' AND object_id=?",
        (object_id,),
    ).fetchone()[0] == 0
    assert r1_store.verify_adapter_raw_output(raw.raw_output_ref) is False


def test_raw_output_read_time_integrity_blocks_candidate_and_recovery_does_not_repair(r1_store):
    project_id = "synthetic-raw-integrity-project"
    revision_id = "synthetic-raw-integrity-revision"
    run_id = "synthetic-raw-integrity-run"
    r1_store.create_project(project_id, "SYNTHETIC raw integrity project")
    r1_store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTHETIC-RAW-1",
            content_hash=content_hash({"revision": revision_id}),
        )
    )
    r1_store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-RAW-CUTOFF",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    result = _invoke(
        _api_runtime(RecordingTransport()),
        attempt_id="attempt-raw-read-integrity",
        monitoring_run_id=run_id,
    )
    receipt = persist_capability_attempt(r1_store, result)
    raw_ref = result.adapter_run.raw_output.raw_output_ref
    version, loaded = load_persisted_raw_output(r1_store, raw_ref)
    assert version == 1
    assert loaded == result.adapter_run.raw_output
    assert r1_store.verify_adapter_raw_output(raw_ref) is True
    assert r1_store.verify_artifact(receipt.adapter.artifact_id) is True

    object_id = "adapter-raw:%s" % raw_ref
    row = r1_store._conn.execute(
        "SELECT object_json FROM domain_objects WHERE kind='adapter_raw_output'"
        " AND object_id=? AND version=1",
        (object_id,),
    ).fetchone()
    damaged = json.loads(row[0])
    damaged["raw_output_json"] = json.dumps(
        {"fixture_marker": "SYNTHETIC", "tampered": True}, sort_keys=True
    )
    r1_store._conn.execute(
        "UPDATE domain_objects SET object_json=?, content_hash=?"
        " WHERE kind='adapter_raw_output' AND object_id=? AND version=1",
        (json.dumps(damaged), content_hash(damaged), object_id),
    )

    with pytest.raises(StoreError, match="nested content hash"):
        load_persisted_raw_output(r1_store, raw_ref)

    damaged["raw_output_json"] = "NaN"
    r1_store._conn.execute(
        "UPDATE domain_objects SET object_json=?, content_hash=?"
        " WHERE kind='adapter_raw_output' AND object_id=? AND version=1",
        (json.dumps(damaged), content_hash(damaged), object_id),
    )
    with pytest.raises(StoreError, match="nested content hash is invalid"):
        load_persisted_raw_output(r1_store, raw_ref)
    noncanonical_recovery = r1_store.recover()
    assert any(
        item.startswith("domain object adapter_raw_output/%s@1" % object_id)
        for item in noncanonical_recovery.integrity_violations
    )
    assert r1_store._conn.execute(
        "SELECT COUNT(*) FROM domain_objects WHERE kind='adapter_raw_output' AND object_id=?",
        (object_id,),
    ).fetchone()[0] == 1
    assert r1_store.verify_adapter_raw_output(raw_ref) is False
    assert r1_store.verify_artifact(receipt.adapter.artifact_id) is False
    with pytest.raises(IdempotencyConflictError, match="raw output is immutable"):
        persist_capability_attempt(r1_store, result)

    recovery = r1_store.recover()
    assert any(
        item.startswith("domain object adapter_raw_output/%s@1" % object_id)
        for item in recovery.integrity_violations
    )
    assert "artifact %s" % receipt.adapter.artifact_id in recovery.integrity_violations
    assert r1_store._conn.execute(
        "SELECT COUNT(*) FROM domain_objects WHERE kind='adapter_raw_output' AND object_id=?",
        (object_id,),
    ).fetchone()[0] == 1
    with pytest.raises(StoreError, match="nested content hash is invalid"):
        load_persisted_raw_output(r1_store, raw_ref)


def test_durable_journal_replays_terminal_after_store_reopen_without_transport(tmp_path):
    db_path = tmp_path / "journal.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    profile = _api_profile(profile_id="profile-journal-replay")
    first_transport = RecordingTransport()
    first_store = Store(db_path, artifact_dir)
    _prepare_journal_store(first_store)
    first_runtime = _api_runtime(
        first_transport,
        profile=profile,
        revision_reader=lambda run_id: first_store.get_run(run_id).manifest_revision,
        attempt_journal=first_store,
        journal_owner_token="owner-first-process",
    )
    first = _invoke(first_runtime, attempt_id="attempt-durable-replay")
    assert first.status == AdapterState.COMPLETE
    assert len(first_transport.calls) == 1
    terminal = first_store.get_capability_attempt("attempt-durable-replay")
    assert terminal["terminal"] is True
    assert terminal["result_hash"]
    first_store.close()

    reopened = Store(db_path, artifact_dir)
    replay_transport = RecordingTransport()
    replay_runtime = _api_runtime(
        replay_transport,
        profile=profile,
        revision_reader=lambda run_id: reopened.get_run(run_id).manifest_revision,
        attempt_journal=reopened,
        journal_owner_token="owner-restarted-process",
    )
    replay = _invoke(replay_runtime, attempt_id="attempt-durable-replay")
    assert replay.status == AdapterState.COMPLETE
    assert replay.adapter_run.raw_output.content_hash == first.adapter_run.raw_output.content_hash
    assert replay_transport.calls == []
    reopened.close()


def test_durable_journal_result_corruption_fails_closed(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-journal-corruption")
    runtime = _api_runtime(
        RecordingTransport(),
        profile=profile,
        revision_reader=lambda run_id: r1_store.get_run(run_id).manifest_revision,
        attempt_journal=r1_store,
        journal_owner_token="owner-corruption-test",
    )
    _invoke(runtime, attempt_id="attempt-corruption")
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET result_json=? WHERE attempt_id=?",
        (json.dumps({"tampered": True}), "attempt-corruption"),
    )
    with pytest.raises(StoreError, match="result hash mismatch"):
        r1_store.get_capability_attempt("attempt-corruption")


def test_durable_journal_terminal_status_corruption_fails_closed(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-journal-status-corruption")
    runtime = _api_runtime(
        RecordingTransport(),
        profile=profile,
        revision_reader=lambda run_id: r1_store.get_run(run_id).manifest_revision,
        attempt_journal=r1_store,
        journal_owner_token="owner-status-corruption-test",
    )
    _invoke(runtime, attempt_id="attempt-status-corruption")
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET status='failed' WHERE attempt_id=?",
        ("attempt-status-corruption",),
    )
    with pytest.raises(StoreError, match="result hash mismatch"):
        r1_store.get_capability_attempt("attempt-status-corruption")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("id", "different-attempt"),
        ("monitoring_run_id", "different-run"),
        ("node_id", "different-node"),
        ("manifest_revision", 2),
        ("continued_from", "different-parent"),
        ("execution_profile_fingerprint", "different-profile"),
        ("binding_input_hash", "different-input"),
    ),
)
def test_durable_journal_request_metadata_mismatch_fails_closed(r1_store, field, value):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-journal-metadata")
    request = CapabilityRequest.build(
        attempt_id="attempt-metadata-integrity",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(r1_store).declare_capability_attempt(
        attempt_id=request.attempt_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        request_hash=request.request_hash,
        request=request.to_jsonrpc(),
        profile_fingerprint=request.profile_fingerprint,
        manifest_revision=request.manifest_revision,
        input_hash=request.input_hash,
    )
    damaged = request.to_jsonrpc()
    if field == "id":
        damaged["id"] = value
    elif field == "execution_profile_fingerprint":
        damaged["params"]["execution_identity"]["profile_fingerprint"] = value
    elif field == "binding_input_hash":
        damaged["params"]["binding"]["input_hash"] = value
    else:
        damaged["params"][field] = value
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET request_json=?, request_hash=? WHERE attempt_id=?",
        (json.dumps(damaged), content_hash(damaged), request.attempt_id),
    )
    with pytest.raises(StoreError, match="request identity mismatch"):
        r1_store.get_capability_attempt(request.attempt_id)


def test_two_sqlite_connections_prevent_duplicate_transport_dispatch(tmp_path):
    db_path = tmp_path / "journal.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    first_store = Store(db_path, artifact_dir)
    second_store = Store(db_path, artifact_dir)
    _prepare_journal_store(first_store)
    profile = _api_profile(profile_id="profile-journal-concurrent")
    second_transport = RecordingTransport()
    second_runtime = _api_runtime(
        second_transport,
        profile=profile,
        revision_reader=lambda run_id: second_store.get_run(run_id).manifest_revision,
        attempt_journal=second_store,
        journal_owner_token="owner-second-connection",
        journal_lease_seconds=60,
    )

    request = CapabilityRequest.build(
        attempt_id="attempt-cross-connection",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(first_store).declare_capability_attempt(
        attempt_id=request.attempt_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        request_hash=request.request_hash,
        request=request.to_jsonrpc(),
        profile_fingerprint=request.profile_fingerprint,
        manifest_revision=request.manifest_revision,
        input_hash=request.input_hash,
    )
    _journal(first_store).claim_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "owner-first-connection",
        lease_seconds=60,
    )
    with pytest.raises(StoreError, match="leased by another process"):
        _invoke(second_runtime, attempt_id="attempt-cross-connection")
    assert second_transport.calls == []
    first_store.close()
    second_store.close()


def test_expired_attempt_recovered_by_new_process_and_late_completion_rejected(tmp_path):
    db_path = tmp_path / "journal.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    store = Store(db_path, artifact_dir)
    _prepare_journal_store(store)
    profile = _api_profile(profile_id="profile-journal-recovery")
    request = CapabilityRequest.build(
        attempt_id="attempt-interrupted",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(store).declare_capability_attempt(
        attempt_id=request.attempt_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        request_hash=request.request_hash,
        request=request.to_jsonrpc(),
        profile_fingerprint=request.profile_fingerprint,
        manifest_revision=request.manifest_revision,
        input_hash=request.input_hash,
    )
    _journal(store).claim_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "owner-crashed-process",
        lease_seconds=1,
        now_epoch=10,
    )

    recovery_script = _write_harness(
        tmp_path,
        """import json, os, sys
from pathlib import Path
from mm_r1.store import Store
store = Store(Path(sys.argv[1]), Path(sys.argv[2]))
recovered = store.recover_expired_capability_attempts(now_epoch=12)
print(json.dumps({'pid': os.getpid(), 'recovered': recovered}))
store.close()
""",
        "recover_attempt.py",
    )
    source_root = Path(__file__).resolve().parents[1] / "src"
    completed = subprocess.run(
        [sys.executable, str(recovery_script), str(db_path), str(artifact_dir)],
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(source_root)},
    )
    recovered = json.loads(completed.stdout)
    assert recovered["pid"] != os.getpid()
    assert recovered["recovered"] == [request.attempt_id]
    interrupted = store.get_capability_attempt(request.attempt_id)
    assert interrupted["status"] == "interrupted"
    assert interrupted["terminal"] is False

    with pytest.raises(StaleCallbackError, match="stale/interrupted"):
        _journal(store).complete_capability_attempt(
            request.attempt_id,
            request.request_hash,
            "owner-crashed-process",
            status="complete",
            result={"late": True},
        )
    runtime = _api_runtime(
        RecordingTransport(),
        profile=profile,
        revision_reader=lambda run_id: store.get_run(run_id).manifest_revision,
        attempt_journal=store,
        journal_owner_token="owner-recovery-process",
    )
    resumed = runtime.resume(
        request.attempt_id,
        attempt_id="attempt-after-interruption",
        manifest_revision=1,
    )
    assert resumed.status == AdapterState.COMPLETE
    assert resumed.request.continued_from == request.attempt_id
    assert resumed.request.input_hash == request.input_hash
    assert store.get_capability_attempt(request.attempt_id)["status"] == "interrupted"
    assert store.get_capability_attempt("attempt-after-interruption")["terminal"] is True
    rejected = [
        event for event in store.audit_trail()
        if event.event_type == "capability_attempt_rejected"
    ]
    assert rejected[-1].payload["reason"] == "stale_or_interrupted_callback"
    store.close()


def test_expired_lease_fails_closed_without_recovery_and_same_owner_cannot_redispatch(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-expired-lease")
    request = CapabilityRequest.build(
        attempt_id="attempt-expired-without-recovery",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(r1_store).declare_capability_attempt(
        attempt_id=request.attempt_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        request_hash=request.request_hash,
        request=request.to_jsonrpc(),
        profile_fingerprint=request.profile_fingerprint,
        manifest_revision=request.manifest_revision,
        input_hash=request.input_hash,
    )
    _journal(r1_store).claim_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "same-owner",
        lease_seconds=1,
        now_epoch=10,
    )
    interrupted = _journal(r1_store).claim_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "same-owner",
        lease_seconds=1,
        now_epoch=12,
    )
    assert interrupted["status"] == "interrupted"
    with pytest.raises(StaleCallbackError, match="stale/interrupted"):
        _journal(r1_store).complete_capability_attempt(
            request.attempt_id,
            request.request_hash,
            "same-owner",
            status="complete",
            result={"late": True},
            now_epoch=12,
        )

    second_request = CapabilityRequest.build(
        attempt_id="attempt-expired-late-completion",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S002"},
        expected_units=(CoverageUnit(scope="subject", key="SYN-S002"),),
    )
    _journal(r1_store).declare_capability_attempt(
        attempt_id=second_request.attempt_id,
        run_id=second_request.monitoring_run_id,
        node_id=second_request.node_id,
        request_hash=second_request.request_hash,
        request=second_request.to_jsonrpc(),
        profile_fingerprint=second_request.profile_fingerprint,
        manifest_revision=second_request.manifest_revision,
        input_hash=second_request.input_hash,
    )
    _journal(r1_store).claim_capability_attempt(
        second_request.attempt_id,
        second_request.request_hash,
        "late-owner",
        lease_seconds=1,
        now_epoch=20,
    )
    with pytest.raises(StaleCallbackError, match="stale/interrupted"):
        _journal(r1_store).complete_capability_attempt(
            second_request.attempt_id,
            second_request.request_hash,
            "late-owner",
            status="complete",
            result={"late": True},
            now_epoch=22,
        )
    assert r1_store.get_capability_attempt(second_request.attempt_id)["status"] == "interrupted"


def test_journal_rejects_nonterminal_or_status_changed_terminal_completion(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-terminal-status")
    request = CapabilityRequest.build(
        attempt_id="attempt-terminal-status",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(r1_store).declare_capability_attempt(
        attempt_id=request.attempt_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        request_hash=request.request_hash,
        request=request.to_jsonrpc(),
        profile_fingerprint=request.profile_fingerprint,
        manifest_revision=request.manifest_revision,
        input_hash=request.input_hash,
    )
    _journal(r1_store).claim_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "terminal-owner",
        lease_seconds=60,
        now_epoch=10,
    )
    with pytest.raises(StoreError, match="non-terminal capability status"):
        _journal(r1_store).complete_capability_attempt(
            request.attempt_id,
            request.request_hash,
            "terminal-owner",
            status="running",
            result={"value": 1},
            now_epoch=11,
        )
    assert r1_store.get_capability_attempt(request.attempt_id)["status"] == "running"
    _journal(r1_store).complete_capability_attempt(
        request.attempt_id,
        request.request_hash,
        "terminal-owner",
        status="complete",
        result={"value": 1},
        now_epoch=11,
    )
    with pytest.raises(IdempotencyConflictError, match="immutable"):
        _journal(r1_store).complete_capability_attempt(
            request.attempt_id,
            request.request_hash,
            "terminal-owner",
            status="failed",
            result={"value": 1},
            now_epoch=11,
        )


def test_resume_revalidates_journal_input_identity_before_transport_dispatch(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-resume-preflight")
    original = CapabilityRequest.build(
        attempt_id="attempt-resume-damaged-source",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    damaged_rpc = original.to_jsonrpc()
    damaged_rpc["params"]["input_hash"] = "internally-consistent-but-not-derived"
    damaged_rpc["params"]["binding"]["input_hash"] = "internally-consistent-but-not-derived"
    damaged_hash = content_hash(damaged_rpc)
    _journal(r1_store).declare_capability_attempt(
        attempt_id=original.attempt_id,
        run_id=original.monitoring_run_id,
        node_id=original.node_id,
        request_hash=damaged_hash,
        request=damaged_rpc,
        profile_fingerprint=original.profile_fingerprint,
        manifest_revision=original.manifest_revision,
        input_hash="internally-consistent-but-not-derived",
    )
    _journal(r1_store).claim_capability_attempt(
        original.attempt_id,
        damaged_hash,
        "damaged-owner",
        lease_seconds=60,
    )
    _journal(r1_store).interrupt_capability_attempt(
        original.attempt_id,
        damaged_hash,
        "damaged-owner",
        reason="synthetic interruption",
    )
    transport = RecordingTransport()
    runtime = _api_runtime(
        transport,
        profile=profile,
        revision_reader=lambda run_id: r1_store.get_run(run_id).manifest_revision,
        attempt_journal=r1_store,
        journal_owner_token="resume-owner",
    )
    with pytest.raises(AttemptIdentityError, match="identity changed"):
        runtime.resume(
            original.attempt_id,
            attempt_id="attempt-resume-must-not-dispatch",
            manifest_revision=1,
        )
    assert transport.calls == []
    assert r1_store.get_capability_attempt("attempt-resume-must-not-dispatch") is None


def test_resume_rejects_journal_manifest_metadata_mismatch_before_transport_dispatch(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-resume-manifest-integrity")
    original = CapabilityRequest.build(
        attempt_id="attempt-resume-manifest-source",
        monitoring_run_id="monitoring-run-1",
        node_id="ai-risk-node",
        manifest_revision=1,
        profile=profile,
        versions=_versions(),
        payload={"subject_id": "SYN-S001"},
        expected_units=_units(),
    )
    _journal(r1_store).declare_capability_attempt(
        attempt_id=original.attempt_id,
        run_id=original.monitoring_run_id,
        node_id=original.node_id,
        request_hash=original.request_hash,
        request=original.to_jsonrpc(),
        profile_fingerprint=original.profile_fingerprint,
        manifest_revision=original.manifest_revision,
        input_hash=original.input_hash,
    )
    _journal(r1_store).claim_capability_attempt(
        original.attempt_id,
        original.request_hash,
        "manifest-owner",
        lease_seconds=60,
    )
    _journal(r1_store).interrupt_capability_attempt(
        original.attempt_id,
        original.request_hash,
        "manifest-owner",
        reason="synthetic interruption",
    )
    damaged = original.to_jsonrpc()
    damaged["params"]["manifest_revision"] = 2
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET request_json=?, request_hash=? WHERE attempt_id=?",
        (json.dumps(damaged), content_hash(damaged), original.attempt_id),
    )
    transport = RecordingTransport()
    runtime = _api_runtime(
        transport,
        profile=profile,
        revision_reader=lambda run_id: r1_store.get_run(run_id).manifest_revision,
        attempt_journal=r1_store,
        journal_owner_token="resume-manifest-owner",
    )
    with pytest.raises(StoreError, match="request identity mismatch"):
        runtime.resume(
            original.attempt_id,
            attempt_id="attempt-resume-manifest-must-not-dispatch",
            manifest_revision=1,
        )
    assert transport.calls == []
    assert r1_store._conn.execute(
        "SELECT 1 FROM capability_attempt_journal WHERE attempt_id=?",
        ("attempt-resume-manifest-must-not-dispatch",),
    ).fetchone() is None


def test_same_runtime_resume_cannot_bypass_corrupted_durable_journal(r1_store):
    _prepare_journal_store(r1_store)
    profile = _api_profile(profile_id="profile-same-runtime-journal-integrity")
    calls = {"count": 0}

    def sequence(request, selected_profile):
        calls["count"] += 1
        if calls["count"] == 1:
            return _success_response(request, status="partial", produced_status="partial")
        return _success_response(request)

    transport = RecordingTransport(callback=sequence)
    runtime = _api_runtime(
        transport,
        profile=profile,
        revision_reader=lambda run_id: r1_store.get_run(run_id).manifest_revision,
        attempt_journal=r1_store,
        journal_owner_token="same-runtime-owner",
    )
    first = _invoke(runtime, attempt_id="attempt-same-runtime-source")
    assert first.status == AdapterState.PARTIAL
    damaged = first.request.to_jsonrpc()
    damaged["params"]["manifest_revision"] = 2
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET request_json=?, request_hash=? WHERE attempt_id=?",
        (json.dumps(damaged), content_hash(damaged), first.request.attempt_id),
    )
    with pytest.raises(StoreError, match="request identity mismatch"):
        runtime.resume(
            first.request.attempt_id,
            attempt_id="attempt-same-runtime-must-not-dispatch",
            manifest_revision=1,
        )
    assert len(transport.calls) == 1
    assert r1_store._conn.execute(
        "SELECT 1 FROM capability_attempt_journal WHERE attempt_id=?",
        ("attempt-same-runtime-must-not-dispatch",),
    ).fetchone() is None


def test_harness_process_envelope_enforces_fixed_cwd_and_environment_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("MM_ALLOWED_CONTEXT", "allowed-value")
    monkeypatch.setenv("MM_FORBIDDEN_CONTEXT", "must-not-be-inherited")
    script = _write_harness(
        tmp_path,
        """import json, os, sys
request = json.load(sys.stdin)
unit = dict(request['params']['expected_coverage'][0])
unit['status'] = 'covered'
payload = {
    'cwd': os.getcwd(),
    'allowed': os.environ.get('MM_ALLOWED_CONTEXT'),
    'forbidden': os.environ.get('MM_FORBIDDEN_CONTEXT'),
    'environment_keys': sorted(os.environ),
}
print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': {
    'status': 'complete',
    'execution_identity': request['params']['execution_identity'],
    'candidate_payload': payload,
    'produced_units': [unit],
}}))
""",
        "process_envelope.py",
    )
    profile = _harness_profile(
        (sys.executable, str(script)),
        working_directory=str(tmp_path),
        environment_keys=("MM_ALLOWED_CONTEXT",),
    )
    result = _invoke(_harness_runtime(profile), attempt_id="attempt-process-envelope")
    payload = result.adapter_run.candidate_artifact.payload["candidate_payload"]
    assert payload["cwd"] == str(tmp_path)
    assert payload["allowed"] == "allowed-value"
    assert payload["forbidden"] is None
    assert "MM_ALLOWED_CONTEXT" in payload["environment_keys"]
    assert "MM_FORBIDDEN_CONTEXT" not in payload["environment_keys"]
    assert set(payload["environment_keys"]) <= {
        "LC_CTYPE",
        "MM_ALLOWED_CONTEXT",
        "__CF_USER_TEXT_ENCODING",
    }


def test_harness_working_directory_disappearance_fails_before_process_dispatch(tmp_path):
    working_directory = tmp_path / "fixed-cwd"
    working_directory.mkdir()
    profile = _harness_profile(
        (sys.executable, "-c", "raise SystemExit('must not execute')"),
        working_directory=str(working_directory),
    )
    working_directory.rmdir()
    runtime = _harness_runtime(profile)
    with pytest.raises(CapabilityRuntimeError, match="working_directory is no longer"):
        _invoke(runtime, attempt_id="attempt-missing-fixed-cwd")
    assert runtime.attempts == ()


@pytest.mark.skipif(sys.platform != "darwin", reason="R1 backend is macOS Seatbelt only")
def test_requested_seatbelt_identity_is_frozen_and_unavailable_backend_fails_closed(
    tmp_path, monkeypatch
):
    script = _write_harness(tmp_path, "print('{}')\n", "seatbelt_identity.py")
    profile = _isolated_harness_profile(
        (sys.executable, str(script)),
        readable_roots=(tmp_path,),
        working_directory=str(tmp_path),
    )
    policy = profile.harness_isolation
    assert policy is not None
    assert policy.fingerprint == content_hash(policy.public_dict())
    assert profile.public_dict()["harness_isolation"]["backend"] == "macos_seatbelt_r1"
    assert str(capability_runtime._SANDBOX_EXEC_PATH) in dict(profile.execution_file_hashes)
    with pytest.raises(ValueError, match="forbids harness_isolation"):
        _api_profile(harness_isolation=policy)
    with pytest.raises(ValueError, match="too broad"):
        HarnessIsolationPolicy(
            readable_roots=("/",),
            allowed_executables=_python_executable_closure(),
        )

    runtime = _harness_runtime(profile)
    monkeypatch.setattr(capability_runtime, "_SANDBOX_EXEC_PATH", tmp_path / "missing-sandbox-exec")
    with pytest.raises(CapabilityRuntimeError, match="backend is unavailable"):
        _invoke(runtime, attempt_id="attempt-isolation-unavailable")
    assert runtime.attempts == ()


@pytest.mark.skipif(sys.platform != "darwin", reason="R1 backend is macOS Seatbelt only")
def test_seatbelt_harness_enforces_declared_files_network_exec_and_environment(
    tmp_path, monkeypatch
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    private_dir = tmp_path / "private"
    input_dir.mkdir()
    output_dir.mkdir()
    private_dir.mkdir()
    allowed_file = input_dir / "allowed.txt"
    denied_file = private_dir / "denied.txt"
    denied_write = private_dir / "must-not-exist.txt"
    output_file = output_dir / "result.txt"
    allowed_file.write_text("SYNTHETIC_ALLOWED", encoding="utf-8")
    denied_file.write_text("SYNTHETIC_DENIED", encoding="utf-8")
    monkeypatch.setenv("MM_PARENT_ONLY_SECRET", "MUST_NOT_BE_INHERITED")

    script = _write_harness(
        input_dir,
        """import errno, json, os, socket, subprocess, sys
from pathlib import Path

request = json.load(sys.stdin)
allowed_file = Path(%s)
denied_file = Path(%s)
denied_write = Path(%s)
output_file = Path(%s)

try:
    denied_file.read_text(encoding='utf-8')
    denied_read_errno = 0
except OSError as exc:
    denied_read_errno = exc.errno
try:
    denied_write.write_text('forbidden', encoding='utf-8')
    denied_write_errno = 0
except OSError as exc:
    denied_write_errno = exc.errno
sock = socket.socket()
try:
    network_errno = sock.connect_ex(('127.0.0.1', 9))
except OSError as exc:
    network_errno = exc.errno
finally:
    sock.close()
try:
    subprocess.run(['/usr/bin/true'], check=True)
    child_exec_errno = 0
except OSError as exc:
    child_exec_errno = exc.errno

output_file.write_text('SYNTHETIC_OUTPUT', encoding='utf-8')
unit = dict(request['params']['expected_coverage'][0])
unit['status'] = 'covered'
payload = {
    'allowed_read': allowed_file.read_text(encoding='utf-8'),
    'denied_read_errno': denied_read_errno,
    'denied_write_errno': denied_write_errno,
    'network_errno': network_errno,
    'child_exec_errno': child_exec_errno,
    'parent_secret': os.environ.get('MM_PARENT_ONLY_SECRET'),
}
print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': {
    'status': 'complete',
    'execution_identity': request['params']['execution_identity'],
    'candidate_payload': payload,
    'produced_units': [unit],
}}))
""" % (
            json.dumps(str(allowed_file)),
            json.dumps(str(denied_file)),
            json.dumps(str(denied_write)),
            json.dumps(str(output_file)),
        ),
        "seatbelt_boundaries.py",
    )
    profile = _isolated_harness_profile(
        (sys.executable, str(script)),
        readable_roots=(input_dir,),
        writable_roots=(output_dir,),
        working_directory=str(input_dir),
    )
    result = _invoke(_harness_runtime(profile), attempt_id="attempt-seatbelt-boundaries")
    assert result.status == AdapterState.COMPLETE
    payload = result.adapter_run.candidate_artifact.payload["candidate_payload"]
    assert payload == {
        "allowed_read": "SYNTHETIC_ALLOWED",
        "denied_read_errno": 1,
        "denied_write_errno": 1,
        "network_errno": 1,
        "child_exec_errno": 1,
        "parent_secret": None,
    }
    assert output_file.read_text(encoding="utf-8") == "SYNTHETIC_OUTPUT"
    assert not denied_write.exists()
    assert result.transport_execution.isolation_backend == "macos_seatbelt_r1"
    assert result.transport_execution.isolation_policy_fingerprint == profile.harness_isolation.fingerprint


@pytest.mark.skipif(sys.platform != "darwin", reason="R1 backend is macOS Seatbelt only")
@pytest.mark.parametrize("terminal_action", ("timeout", "cancel"))
def test_isolated_harness_timeout_and_cancel_kill_the_entire_process_group(
    tmp_path, terminal_action
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    marker = output_dir / ("%s-child-survived.txt" % terminal_action)
    ready = output_dir / ("%s-child-started.txt" % terminal_action)
    script = _write_harness(
        input_dir,
        """import subprocess, sys, time
from pathlib import Path

marker = sys.argv[1]
ready = Path(sys.argv[2])
subprocess.Popen([
    sys.executable,
    '-c',
    "import sys, time; from pathlib import Path; time.sleep(0.6); Path(sys.argv[1]).write_text('survived')",
    marker,
])
ready.write_text('started', encoding='utf-8')
time.sleep(5)
""",
        "process_group.py",
    )
    profile = _isolated_harness_profile(
        (sys.executable, str(script), str(marker), str(ready)),
        readable_roots=(input_dir,),
        writable_roots=(output_dir,),
        working_directory=str(input_dir),
        timeout_seconds=0.2 if terminal_action == "timeout" else 5,
    )
    runtime = _harness_runtime(profile)
    if terminal_action == "timeout":
        result = _invoke(runtime, attempt_id="attempt-isolated-timeout")
        assert result.status == AdapterState.TIMEOUT
    else:
        box = {}
        thread = threading.Thread(
            target=lambda: box.setdefault(
                "result", _invoke(runtime, attempt_id="attempt-isolated-cancel")
            )
        )
        thread.start()
        for _ in range(200):
            if ready.exists():
                break
            time.sleep(0.01)
        assert ready.exists()
        assert runtime.cancel("attempt-isolated-cancel")
        thread.join(timeout=3)
        assert not thread.is_alive()
        result = box["result"]
        assert result.status == AdapterState.CANCELLED
    time.sleep(0.8)
    assert not marker.exists()
