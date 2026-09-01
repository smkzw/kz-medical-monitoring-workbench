"""Authoritative manifest work-unit ledger and structured progress tests.

All fixtures are synthetic/offline.  No service, provider or real project is
used by this module.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import threading
from pathlib import Path

import pytest

from mm_r1.domain import (
    ExecutionBasis,
    ExecutionManifest,
    ManifestNode,
    ManifestWorkUnit,
    MonitoringRun,
    NodeStatus,
    NodeType,
    RunMode,
    SourceRevision,
    content_hash,
)
from mm_r1 import domain
from mm_r1.store import (
    CompletionGateError,
    IdempotencyConflictError,
    StaleCallbackError,
    Store,
    StoreError,
)


def _stage_runtime_copy(tmp_path: Path, source: Path, operation_id: str) -> Path:
    staged_dir = tmp_path / ".migration-staging" / operation_id / "workspace"
    staged_dir.mkdir(parents=True, exist_ok=True)
    staged = staged_dir / source.name
    shutil.copy2(source, staged)
    return staged


def _migrate_runtime_staging(staged: Path, source_version: str) -> None:
    r7_source = Path(__file__).resolve().parents[2] / (
        "medical_monitoring_ai_native_r7"
    ) / "src"
    if str(r7_source) not in sys.path:
        sys.path.insert(0, str(r7_source))
    from mm_r7.migration import migrate_runtime_staging

    migrate_runtime_staging(staged, source_version)


def _journal(store: Store):
    """Synthetic test access to the private runtime mutation facade."""

    return store._runtime_attempt_journal()


def _base_run(store: Store, run_id: str = "run-progress") -> str:
    project_id = f"project-{run_id}"
    revision_id = f"source-{run_id}"
    store.create_project(project_id, "Synthetic progress project")
    store.add_source_revision(SourceRevision(
        revision_id=revision_id,
        project_id=project_id,
        source_type="listing",
        version="synthetic-v1",
        content_hash=content_hash({"run_id": run_id, "synthetic": True}),
    ))
    store.create_run(MonitoringRun(
        run_id=run_id,
        project_id=project_id,
        mode=RunMode.DAILY,
        data_cutoff="2026-08-09",
        source_revision_id=revision_id,
        execution_basis=ExecutionBasis.FULL,
    ))
    return run_id


def _manifest(run_id: str, *, second: bool = True) -> ExecutionManifest:
    nodes = [ManifestNode("extract", NodeType.DETERMINISTIC_SERVICE)]
    units = [ManifestWorkUnit(
        work_unit_id="extract-S001",
        node_id="extract",
        label="提取受试者 S001 数据",
        stage="数据解构",
        scope="subject",
        target_ref="S001",
        ordinal=1,
    )]
    if second:
        nodes.append(ManifestNode("risk", NodeType.AI_CANDIDATE, depends_on=["extract"]))
        units.append(ManifestWorkUnit(
            work_unit_id="risk-S001-AE",
            node_id="risk",
            label="分析受试者 S001 AE 风险",
            stage="风险分析",
            scope="risk_domain",
            target_ref="S001/AE",
            ordinal=2,
            depends_on=["extract-S001"],
        ))
    return ExecutionManifest(
        run_id=run_id,
        nodes=nodes,
        work_units=units,
        graph_version="synthetic-progress-v1",
        schema_version="synthetic-schema-v1",
    )


def _frozen(store: Store, run_id: str = "run-progress", *, second: bool = True) -> int:
    _base_run(store, run_id)
    return store.set_manifest(_manifest(run_id, second=second))


def _ai_manifest(run_id: str, *, two_units: bool = False) -> ExecutionManifest:
    units = [ManifestWorkUnit(
        work_unit_id="risk-S001-AE",
        node_id="risk",
        label="分析受试者 S001 AE 风险",
        stage="风险分析",
        scope="risk_domain",
        target_ref="S001/AE",
        ordinal=1,
    )]
    if two_units:
        units.append(ManifestWorkUnit(
            work_unit_id="risk-S002-AE",
            node_id="risk",
            label="分析受试者 S002 AE 风险",
            stage="风险分析",
            scope="risk_domain",
            target_ref="S002/AE",
            ordinal=2,
        ))
    return ExecutionManifest(
        run_id=run_id,
        nodes=[ManifestNode("risk", NodeType.AI_CANDIDATE)],
        work_units=units,
        graph_version="synthetic-ai-progress-v1",
        schema_version="synthetic-schema-v1",
    )


def _frozen_ai(
    store: Store, run_id: str = "run-progress", *, two_units: bool = False,
) -> int:
    _base_run(store, run_id)
    return store.set_manifest(_ai_manifest(run_id, two_units=two_units))


def _declare_ai_attempt(
    store: Store,
    *,
    run_id: str = "run-progress",
    attempt_id: str = "attempt-risk-1",
    node_id: str = "risk",
    manifest_revision: int = 1,
    continued_from: str = "",
    provider: str = "synthetic-provider",
    claim_for_binding: bool = True,
    register_assignment: bool = True,
) -> dict:
    profile_fingerprint = content_hash({"profile": provider, "attempt": attempt_id})
    input_hash = content_hash({"attempt": attempt_id, "synthetic": True})
    binding = {
        "binding_id": f"binding-{attempt_id}",
        "capability": "synthetic-risk-analysis",
        "provider": provider,
        "model": "synthetic-model",
        "selector": "synthetic-selector",
        "effort": "test",
        "adapter_version": "synthetic-adapter-v1",
        "input_hash": input_hash,
        "allowed_tools": [],
        "isolation": "fresh_context",
        "timeout_seconds": 10,
        "endpoint": "external",
        "created_at": "2026-08-09T00:00:00+00:00",
    }
    execution_identity = {
        "profile_fingerprint": profile_fingerprint,
        "binding_id": binding["binding_id"],
        "provider": binding["provider"],
        "model": binding["model"],
        "selector": binding["selector"],
        "adapter_version": binding["adapter_version"],
    }
    request = {
        "jsonrpc": "2.0",
        "id": attempt_id,
        "method": "medical_monitoring.analyze",
        "params": {
            "monitoring_run_id": run_id,
            "node_id": node_id,
            "manifest_revision": manifest_revision,
            "profile_fingerprint": profile_fingerprint,
            "binding": binding,
            "execution_identity": execution_identity,
            "versions": {
                "source_revision_id": "revision-progress",
                "rule_version": "synthetic-rule-v1",
                "knowledge_version": "synthetic-knowledge-v1",
                "graph_version": "synthetic-ai-progress-v1",
                "schema_version": "synthetic-schema-v1",
                "mapping_version": "",
            },
            "input_hash": input_hash,
            "input": {"synthetic": True},
            "expected_coverage": [{"scope": "subject", "key": "S001"}],
            "continued_from": continued_from or None,
        },
    }
    if register_assignment:
        manifest = store.get_manifest(run_id, manifest_revision)
        assert manifest is not None
        unit = next(item for item in manifest.work_units if item.node_id == node_id)
        label = " ".join(unit.label.split())
        assignment = {
            "schema_version": "mm-capability-work-assignment-r1",
            "attempt_id": attempt_id,
            "run_id": run_id,
            "manifest_revision": manifest_revision,
            "work_unit_id": unit.work_unit_id,
            "node_id": node_id,
            "profile_fingerprint": profile_fingerprint,
            "request_hash": content_hash(request),
            "request": request,
            "running_detail": f"正在{label}",
            "passed_detail": f"已完成：{label}",
            "failed_detail": f"未完成：{label}",
            "blocked_detail": f"已暂停：{label}",
        }
        store.put_domain_object(
            "capability_work_assignment",
            f"capability-work-assignment:{attempt_id}",
            assignment,
            run_id=run_id,
            idempotency_key=f"controller-assignment:{attempt_id}:{content_hash(request)}",
        )
    journal = _journal(store)
    declared = journal.declare_capability_attempt(
        attempt_id=attempt_id,
        run_id=run_id,
        node_id=node_id,
        request_hash=content_hash(request),
        request=request,
        profile_fingerprint=profile_fingerprint,
        manifest_revision=manifest_revision,
        input_hash=input_hash,
        continued_from=continued_from,
    )
    if not claim_for_binding:
        return declared
    return journal.claim_capability_attempt(
        attempt_id,
        declared["request_hash"],
        "owner-%s" % attempt_id,
        lease_seconds=100,
        now_epoch=1000,
    )


def _terminal_ai_attempt(
    store: Store, attempt_id: str, *, status: str = "complete",
    persist_for_completion: bool = True,
) -> dict:
    attempt = store.get_capability_attempt(attempt_id)
    assert attempt is not None
    params = attempt["request"]["params"]
    raw_payload = {
        "attempt_id": attempt_id,
        "execution_identity": params["execution_identity"],
        "status": status,
        "synthetic": True,
    }
    raw_hash = content_hash({"raw_output": raw_payload})
    raw_ref = f"raw-output:{attempt_id}:{raw_hash}"
    analysis = {
        "analysis_id": attempt_id,
        "binding_id": params["binding"]["binding_id"],
        "run_id": attempt["run_id"],
        "node_id": attempt["node_id"],
        "input_hash": attempt["input_hash"],
        "raw_output_ref": raw_ref,
        "parse_state": status,
        "coverage": None,
        "failure_reason": None if status == "complete" else f"synthetic {status}",
        "created_at": "2026-08-09T00:00:00+00:00",
    }
    candidate = None
    if status in {"complete", "partial", "truncated"}:
        candidate = {
            "artifact_type": "synthetic_risk_candidate",
            "version": "synthetic-v1",
            "run_id": attempt["run_id"],
            "node_id": attempt["node_id"],
            "node_type": "ai_candidate",
            "payload": {"candidate": "synthetic risk item"},
            "payload_role": "candidate",
            "input_hashes": [attempt["input_hash"]],
            "evidence_refs": [raw_ref],
            "coverage": None,
            "completeness": status,
            "supersedes": None,
            "qc_status": "candidate_only; not_authoritative",
            "artifact_id": "",
            "content_hash": "",
            "created_at": "",
        }
    runtime_result = {
        "adapter_run": {
            "run_id": attempt_id,
            "binding": params["binding"],
            "status": status,
            "analysis": analysis,
            "raw_output": {
                "raw_output_ref": raw_ref,
                "content_hash": raw_hash,
                "run_id": attempt_id,
                "binding_id": params["binding"]["binding_id"],
                "input_hash": attempt["input_hash"],
                "raw_output_json": domain.canonical_json(raw_payload),
                "immutable": True,
            },
            "coverage": None,
            "candidate_artifact": candidate,
            "failure_reason": analysis["failure_reason"],
            "monitoring_run_id": attempt["run_id"],
            "node_id": attempt["node_id"],
            "independent": True,
            "continued_from": attempt["continued_from"] or None,
            "created_at": "2026-08-09T00:00:00+00:00",
            "finished_at": "2026-08-09T00:00:01+00:00",
        },
        "work_events": [
            {
                "sequence": 1,
                "attempt_id": attempt_id,
                "stage": "attempt_declared",
                "status": "ready",
            },
            {
                "sequence": 2,
                "attempt_id": attempt_id,
                "stage": "attempt_terminal",
                "status": status,
            },
        ],
        "transport_execution": {"raw_output": raw_payload},
    }
    owner = attempt.get("owner_token") or f"owner-{attempt_id}"
    journal = _journal(store)
    if attempt["status"] == "declared":
        journal.claim_capability_attempt(
            attempt_id, attempt["request_hash"], owner,
            lease_seconds=100, now_epoch=1000,
        )
    completed = journal.complete_capability_attempt(
        attempt_id, attempt["request_hash"], owner,
        status=status, result=runtime_result, now_epoch=1001,
    )
    if persist_for_completion:
        _persist_ai_attempt_evidence(store, attempt_id)
    return completed


def _persist_ai_attempt_evidence(store: Store, attempt_id: str) -> None:
    """Mirror the production persistence footprint for Store-only tests."""

    attempt = store.get_capability_attempt(attempt_id)
    assert attempt is not None and attempt["terminal"]
    result = attempt["result"]
    adapter_run = result["adapter_run"]
    binding = adapter_run["binding"]
    analysis = adapter_run["analysis"]
    raw = adapter_run["raw_output"]
    store.put_domain_object(
        "adapter_raw_output", f"adapter-raw:{raw['raw_output_ref']}", raw,
        run_id=attempt["run_id"],
    )
    store.put_domain_object(
        "adapter_binding",
        f"adapter-binding:{binding['binding_id']}:{binding['input_hash']}",
        binding,
        run_id=attempt["run_id"],
    )
    store.put_domain_object(
        "adapter_analysis", f"adapter-analysis:{analysis['analysis_id']}", analysis,
        run_id=attempt["run_id"],
    )
    artifact_id = None
    if adapter_run["candidate_artifact"] is not None:
        envelope = domain.from_jsonable(
            domain.ArtifactEnvelope, adapter_run["candidate_artifact"]
        )
        staged = store.stage_artifact(envelope)
        artifact_id = store.commit_artifact(staged, envelope).artifact_id
    run_snapshot = {
        "adapter_run_id": attempt_id,
        "monitoring_run_id": adapter_run["monitoring_run_id"],
        "node_id": adapter_run["node_id"],
        "status": adapter_run["status"],
        "binding_id": binding["binding_id"],
        "input_hash": binding["input_hash"],
        "analysis_id": analysis["analysis_id"],
        "raw_output_ref": raw["raw_output_ref"],
        "candidate_artifact_id": artifact_id,
        "failure_reason": adapter_run["failure_reason"],
        "independent": adapter_run["independent"],
        "continued_from": adapter_run["continued_from"],
        "created_at": adapter_run["created_at"],
        "finished_at": adapter_run["finished_at"],
    }
    store.put_domain_object(
        "adapter_run", f"adapter-run:{attempt_id}", run_snapshot,
        run_id=attempt["run_id"],
    )
    profile_payload = {
        "profile": binding["provider"],
        "attempt": attempt_id,
    }
    assert content_hash(profile_payload) == attempt["profile_fingerprint"]
    store.put_domain_object(
        "execution_profile",
        f"execution-profile:{attempt['profile_fingerprint']}",
        profile_payload,
        run_id=attempt["run_id"],
    )
    params = attempt["request"]["params"]
    request_identity = {
        "attempt_id": attempt_id,
        "monitoring_run_id": attempt["run_id"],
        "node_id": attempt["node_id"],
        "manifest_revision": attempt["manifest_revision"],
        "profile_fingerprint": attempt["profile_fingerprint"],
        "binding_id": binding["binding_id"],
        "input_hash": attempt["input_hash"],
        "versions": params["versions"],
        "expected_units": params["expected_coverage"],
        "continued_from": attempt["continued_from"],
        "request_hash": attempt["request_hash"],
    }
    store.put_domain_object(
        "adapter_attempt_request", f"adapter-attempt-request:{attempt_id}",
        request_identity, run_id=attempt["run_id"],
    )
    for event in result["work_events"]:
        store.put_domain_object(
            "adapter_work_event",
            f"adapter-work-event:{attempt_id}:{event['sequence']:03d}",
            event,
            run_id=attempt["run_id"],
        )


def _interrupt_ai_attempt(store: Store, attempt_id: str) -> dict:
    attempt = store.get_capability_attempt(attempt_id)
    assert attempt is not None
    owner = attempt.get("owner_token") or f"owner-{attempt_id}"
    journal = _journal(store)
    if attempt["status"] == "declared":
        journal.claim_capability_attempt(
            attempt_id, attempt["request_hash"], owner,
            lease_seconds=100, now_epoch=1000,
        )
    return journal.interrupt_capability_attempt(
        attempt_id, attempt["request_hash"], owner, reason="synthetic interruption"
    )


def test_public_store_has_no_capability_lifecycle_mutation_surface(
    r1_store: Store,
) -> None:
    for method_name in (
        "declare_capability_attempt",
        "claim_capability_attempt",
        "interrupt_capability_attempt",
        "complete_capability_attempt",
    ):
        assert not hasattr(r1_store, method_name)


@pytest.mark.parametrize(
    "event_type",
    (
        domain.EVENT_CAPABILITY_ATTEMPT_DECLARED,
        domain.EVENT_CAPABILITY_ATTEMPT_CLAIMED,
        domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
        domain.EVENT_CAPABILITY_ATTEMPT_TERMINAL,
    ),
)
def test_public_audit_cannot_forge_capability_lifecycle(
    r1_store: Store, event_type: str,
) -> None:
    with pytest.raises(StoreError, match="reserved"):
        r1_store.append_audit(event_type, {"attempt_id": "forged"})


def test_rehashed_terminal_journal_without_audit_event_fails_closed(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store)
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    )
    forged = {"forged": True}
    forged_hash = content_hash({"status": "complete", "result": forged})
    r1_store._conn.execute(
        "UPDATE capability_attempt_journal SET status='complete', terminal=1,"
        " owner_token=NULL, lease_expires_at=NULL, result_json=?, result_hash=?,"
        " terminal_at=?, updated_at=? WHERE attempt_id=?",
        (
            domain.canonical_json(forged), forged_hash,
            "2026-08-09T00:00:01+00:00", "2026-08-09T00:00:01+00:00",
            "attempt-risk-1",
        ),
    )
    with pytest.raises(StoreError, match="audit lifecycle"):
        r1_store.get_capability_attempt("attempt-risk-1")
    with pytest.raises(StoreError, match="audit lifecycle"):
        r1_store.structured_progress("run-progress")


def test_terminal_attempt_without_runtime_evidence_cannot_bind_authoritative_progress(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store, claim_for_binding=False)
    attempt = r1_store.get_capability_attempt("attempt-risk-1")
    assert attempt is not None
    journal = _journal(r1_store)
    journal.claim_capability_attempt(
        attempt["attempt_id"], attempt["request_hash"], "forged-owner",
        lease_seconds=60, now_epoch=10,
    )
    journal.complete_capability_attempt(
        attempt["attempt_id"], attempt["request_hash"], "forged-owner",
        status="complete", result={"forged": True}, now_epoch=11,
    )
    with pytest.raises(StoreError, match="runtime evidence envelope"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "伪造执行已完成"
        )


def test_declared_attempt_cannot_forge_running_work_unit_without_claim(r1_store: Store) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store, claim_for_binding=False)
    with pytest.raises(StoreError, match="must be claimed"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
        )
    assert r1_store.get_work_unit_run(
        "run-progress", 1, "risk-S001-AE"
    ).status == NodeStatus.PENDING


def test_claimed_attempt_cannot_bind_without_controller_assignment(r1_store: Store) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store, register_assignment=False)
    with pytest.raises(StoreError, match="no pre-registered work assignment"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
        )
    assert r1_store.get_work_unit_run(
        "run-progress", 1, "risk-S001-AE"
    ).status == NodeStatus.PENDING


def test_manifest_initializes_authoritative_pending_denominator(r1_store: Store) -> None:
    revision = _frozen(r1_store)

    assert revision == 1
    assert r1_store.manifest_progress("run-progress") == {
        "completed": 0,
        "total": 2,
        "by_status": {"pending": 2},
    }
    snapshot = r1_store.structured_progress("run-progress")
    assert snapshot["manifest_revision"] == 1
    assert snapshot["is_current_revision"] is True
    assert snapshot["percent"] == 0.0
    assert len(snapshot["denominator_hash"]) == 64
    assert snapshot["running"] == []
    assert snapshot["feed"] == []


def test_structured_transitions_drive_counts_current_work_and_feed(r1_store: Store) -> None:
    _frozen(r1_store)
    identity = {"provider": "synthetic", "model": "fixture-model"}

    r1_store.begin_work_unit(
        "run-progress", "extract-S001", "wu-extract",
        "正在提取受试者 S001 的访视与事件数据", identity,
    )
    running = r1_store.structured_progress("run-progress")
    assert running["by_status"] == {"pending": 1, "running": 1}
    assert running["running"][0]["detail"] == "正在提取受试者 S001 的访视与事件数据"
    assert running["running"][0]["execution_identity"] == identity
    assert running["running"][0]["elapsed_seconds"] >= 0

    r1_store.complete_work_unit(
        "run-progress", "extract-S001", "wu-extract", NodeStatus.PASSED,
        "已完成受试者 S001 数据提取", evidence_count=7,
    )
    completed = r1_store.structured_progress("run-progress")
    assert completed["completed"] == 1
    assert completed["total"] == 2
    assert completed["percent"] == 50.0
    assert completed["by_status"] == {"passed": 1, "pending": 1}
    assert [event["event_type"] for event in completed["feed"]] == [
        "work_unit_begin", "work_unit_complete",
    ]
    assert completed["feed"][-1]["evidence_count"] == 7
    assert "raw_log" not in completed["feed"][-1]
    assert [event["event_type"] for event in r1_store.structured_progress(
        "run-progress", feed_limit=1
    )["feed"]] == ["work_unit_complete"]


def test_dependencies_and_node_completion_fail_closed(r1_store: Store) -> None:
    _frozen(r1_store)
    _declare_ai_attempt(r1_store)
    with pytest.raises(StoreError, match="dependencies are not satisfied"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
        )

    r1_store.begin_node_run(
        "run-progress", "extract", NodeType.DETERMINISTIC_SERVICE, "node-extract"
    )
    with pytest.raises(CompletionGateError, match="not terminal"):
        r1_store.complete_node_run(
            "run-progress", "extract", "node-extract", NodeStatus.PASSED
        )

    r1_store.begin_work_unit(
        "run-progress", "extract-S001", "wu-extract", "正在提取受试者数据"
    )
    r1_store.complete_work_unit(
        "run-progress", "extract-S001", "wu-extract", NodeStatus.PASSED,
        "已完成受试者数据提取",
    )
    assert r1_store.complete_node_run(
        "run-progress", "extract", "node-extract", NodeStatus.PASSED
    ).status == NodeStatus.PASSED
    assert r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    ).status == NodeStatus.RUNNING


def test_successful_node_rejects_failed_work_unit(r1_store: Store) -> None:
    _frozen(r1_store, second=False)
    r1_store.begin_node_run(
        "run-progress", "extract", NodeType.DETERMINISTIC_SERVICE, "node-extract"
    )
    r1_store.begin_work_unit(
        "run-progress", "extract-S001", "wu-extract", "正在提取受试者数据"
    )
    r1_store.complete_work_unit(
        "run-progress", "extract-S001", "wu-extract", NodeStatus.FAILED,
        "受试者数据结构无法解析",
    )
    with pytest.raises(CompletionGateError, match="conflicts"):
        r1_store.complete_node_run(
            "run-progress", "extract", "node-extract", NodeStatus.PASSED
        )
    assert r1_store.complete_node_run(
        "run-progress", "extract", "node-extract", NodeStatus.FAILED,
        error="synthetic parse failure",
    ).status == NodeStatus.FAILED


def test_revision_change_preserves_history_and_rejects_stale_callbacks(r1_store: Store) -> None:
    revision_one = _frozen(r1_store, second=False)
    r1_store.begin_work_unit(
        "run-progress", "extract-S001", "rev1-key", "正在提取第一版数据"
    )
    r1_store.complete_work_unit(
        "run-progress", "extract-S001", "rev1-key", NodeStatus.PASSED,
        "已完成第一版数据提取",
    )
    revision_two = r1_store.set_manifest(_manifest("run-progress", second=True))

    assert (revision_one, revision_two) == (1, 2)
    assert r1_store.set_manifest(r1_store.get_manifest("run-progress")) == revision_two
    assert r1_store.list_manifest_revisions("run-progress") == [1, 2]
    assert r1_store.manifest_progress("run-progress") == {
        "completed": 0, "total": 2, "by_status": {"pending": 2},
    }
    old = r1_store.structured_progress("run-progress", manifest_revision=1)
    assert old["is_current_revision"] is False
    assert old["completed"] == old["total"] == 1
    assert len(old["feed"]) == 2
    with pytest.raises(StaleCallbackError, match="stale"):
        r1_store.begin_work_unit(
            "run-progress", "extract-S001", "late-rev1", "迟到的第一版回调",
            manifest_revision=1,
        )


def test_replays_are_idempotent_and_conflicts_do_not_duplicate_feed(r1_store: Store) -> None:
    _frozen(r1_store, second=False)
    first = r1_store.begin_work_unit(
        "run-progress", "extract-S001", "stable-key", "正在提取受试者数据"
    )
    replay = r1_store.begin_work_unit(
        "run-progress", "extract-S001", "stable-key", "正在提取受试者数据"
    )
    assert replay == first
    r1_store.complete_work_unit(
        "run-progress", "extract-S001", "stable-key", NodeStatus.PASSED,
        "已完成受试者数据提取", evidence_count=3,
    )
    same = r1_store.complete_work_unit(
        "run-progress", "extract-S001", "stable-key", NodeStatus.PASSED,
        "已完成受试者数据提取", evidence_count=3,
    )
    assert same.status == NodeStatus.PASSED
    assert r1_store.begin_work_unit(
        "run-progress", "extract-S001", "stable-key", "正在提取受试者数据"
    ).status == NodeStatus.PASSED
    with pytest.raises(IdempotencyConflictError, match="conflicting begin replay"):
        r1_store.begin_work_unit(
            "run-progress", "extract-S001", "stable-key", "冲突的开始内容",
            {"model": "another-model"},
        )
    with pytest.raises(IdempotencyConflictError, match="conflicting replay"):
        r1_store.complete_work_unit(
            "run-progress", "extract-S001", "stable-key", NodeStatus.PASSED,
            "冲突的完成内容", evidence_count=3,
        )
    assert len(r1_store.structured_progress("run-progress")["feed"]) == 2


def test_manifest_and_progress_payload_validation(r1_store: Store) -> None:
    _base_run(r1_store)
    invalid = _manifest("run-progress", second=True)
    invalid.work_units[1] = ManifestWorkUnit(
        work_unit_id="risk-S001-AE", node_id="risk", label="分析 AE 风险",
        stage="风险分析", scope="risk_domain", target_ref="S001/AE", ordinal=2,
        depends_on=["risk-S001-AE"],
    )
    with pytest.raises(StoreError, match="depend on itself"):
        r1_store.set_manifest(invalid)

    r1_store.set_manifest(_manifest("run-progress", second=False))
    with pytest.raises(StoreError, match="not allowed"):
        r1_store.begin_work_unit(
            "run-progress", "extract-S001", "unsafe-key", "正在提取数据",
            {"api_token": "must-not-enter-feed"},
        )
    with pytest.raises(StoreError, match="feed_limit"):
        r1_store.structured_progress("run-progress", feed_limit=0)
    with pytest.raises(StoreError, match="reserved"):
        r1_store.append_audit(
            domain.EVENT_WORK_UNIT_BEGIN,
            {"raw_log": "must-not-enter-feed"},
            "run-progress",
        )


def test_structured_progress_rejects_ledger_and_audit_corruption(r1_store: Store) -> None:
    _frozen(r1_store, run_id="run-ledger-corrupt", second=False)
    r1_store._conn.execute(
        "DELETE FROM work_unit_runs WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
        ("run-ledger-corrupt", 1, "extract-S001"),
    )
    r1_store._conn.execute(
        "INSERT INTO work_unit_runs(run_id, manifest_revision, work_unit_id, node_id,"
        " status, updated_at) VALUES (?,?,?,?,?,?)",
        ("run-ledger-corrupt", 1, "forged-unit", "extract", "pending",
         "2026-08-09T00:00:00+00:00"),
    )
    with pytest.raises(StoreError, match="ledger does not match"):
        r1_store.manifest_progress("run-ledger-corrupt")
    with pytest.raises(StoreError, match="ledger does not match"):
        r1_store.structured_progress("run-ledger-corrupt")

    _frozen(r1_store, run_id="run-audit-corrupt", second=False)
    r1_store.begin_work_unit(
        "run-audit-corrupt", "extract-S001", "audit-key", "正在提取受试者数据"
    )
    r1_store._conn.execute(
        "UPDATE audit_events SET payload_json='{}' WHERE run_id=? AND event_type=?",
        ("run-audit-corrupt", domain.EVENT_WORK_UNIT_BEGIN),
    )
    with pytest.raises(StoreError, match="audit chain is invalid"):
        r1_store.structured_progress("run-audit-corrupt")


def test_structured_progress_rejects_audit_tail_truncation(r1_store: Store) -> None:
    _frozen(r1_store, run_id="run-audit-tail", second=False)
    r1_store.begin_work_unit(
        "run-audit-tail", "extract-S001", "audit-tail-key", "正在提取受试者数据"
    )
    last_seq = r1_store._conn.execute(
        "SELECT MAX(seq) FROM audit_events"
    ).fetchone()[0]
    r1_store._conn.execute("DELETE FROM audit_events WHERE seq=?", (last_seq,))

    ok, first_bad_seq, _ = r1_store.verify_audit_chain()
    assert ok is False
    assert first_bad_seq == last_seq
    with pytest.raises(StoreError, match="audit chain is invalid"):
        r1_store.structured_progress("run-audit-tail")


def test_progress_reconciles_ledger_definition_and_transition_history(
    r1_store: Store,
) -> None:
    _frozen(r1_store, run_id="run-node-binding", second=False)
    r1_store._conn.execute(
        "UPDATE work_unit_runs SET node_id=? WHERE run_id=?"
        " AND manifest_revision=? AND work_unit_id=?",
        ("forged-node", "run-node-binding", 1, "extract-S001"),
    )
    with pytest.raises(StoreError, match="definition does not match"):
        r1_store.manifest_progress("run-node-binding")
    with pytest.raises(StoreError, match="definition does not match"):
        r1_store.structured_progress("run-node-binding")

    _frozen(r1_store, run_id="run-status-binding", second=False)
    r1_store.begin_work_unit(
        "run-status-binding", "extract-S001", "status-binding-key",
        "正在提取受试者数据",
    )
    r1_store._conn.execute(
        "UPDATE work_unit_runs SET status='passed' WHERE run_id=?"
        " AND manifest_revision=? AND work_unit_id=?",
        ("run-status-binding", 1, "extract-S001"),
    )
    with pytest.raises(StoreError, match="status does not match"):
        r1_store.manifest_progress("run-status-binding")
    with pytest.raises(StoreError, match="status does not match"):
        r1_store.structured_progress("run-status-binding")


def test_concurrent_same_manifest_is_one_atomic_revision(tmp_path: Path) -> None:
    db_path = tmp_path / "concurrent.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as setup:
        _base_run(setup, "run-concurrent")
    manifest = _manifest("run-concurrent", second=False)
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def _set_from_independent_connection() -> None:
        try:
            with Store(db_path, artifact_dir) as store:
                barrier.wait()
                results.append(store.set_manifest(manifest))
        except BaseException as exc:  # test captures worker errors for the main assertion
            errors.append(exc)

    threads = [threading.Thread(target=_set_from_independent_connection) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert sorted(results) == [1, 1]
    with Store(db_path, artifact_dir) as verified:
        assert verified.list_manifest_revisions("run-concurrent") == [1]


def test_legacy_manifest_keeps_exact_node_level_progress_shape(r1_store: Store) -> None:
    _base_run(r1_store)
    r1_store.set_manifest(ExecutionManifest(
        run_id="run-progress",
        nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
    ))
    assert r1_store.manifest_progress("run-progress") == {
        "completed": 0, "total": 1, "by_status": {"pending": 1},
    }
    r1_store.begin_node_run(
        "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "legacy-key"
    )
    r1_store.complete_node_run(
        "run-progress", "legacy", "legacy-key", NodeStatus.PASSED
    )
    assert r1_store.manifest_progress("run-progress") == {
        "completed": 1, "total": 1, "by_status": {"passed": 1},
    }
    revision_two = r1_store.set_manifest(ExecutionManifest(
        run_id="run-progress",
        nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
        graph_version="legacy-revision-two",
    ))
    assert revision_two == 2
    assert r1_store.manifest_progress("run-progress") == {
        "completed": 0, "total": 1, "by_status": {"pending": 1},
    }
    old = r1_store.structured_progress("run-progress", manifest_revision=1)
    assert old["is_current_revision"] is False
    assert old["completed"] == old["total"] == 1
    assert old["by_status"] == {"passed": 1}


def test_legacy_node_callbacks_are_bound_to_the_opening_revision(
    r1_store: Store,
) -> None:
    _base_run(r1_store)
    revision_one = r1_store.set_manifest(ExecutionManifest(
        run_id="run-progress",
        nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
    ))
    r1_store.begin_node_run(
        "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "revision-one-key"
    )
    revision_two = r1_store.set_manifest(ExecutionManifest(
        run_id="run-progress",
        nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
        graph_version="legacy-revision-two",
    ))

    with pytest.raises(StaleCallbackError, match="stale"):
        r1_store.complete_node_run(
            "run-progress", "legacy", "revision-one-key", NodeStatus.PASSED
        )
    assert r1_store.structured_progress(
        "run-progress", manifest_revision=revision_one
    )["by_status"] == {"running": 1}
    assert r1_store.structured_progress(
        "run-progress", manifest_revision=revision_two
    )["by_status"] == {"pending": 1}

    reopened = r1_store.begin_node_run(
        "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "revision-two-key"
    )
    assert reopened.manifest_revision == revision_two
    assert r1_store.complete_node_run(
        "run-progress", "legacy", "revision-two-key", NodeStatus.PASSED
    ).status == NodeStatus.PASSED
    assert r1_store.manifest_progress("run-progress")["by_status"] == {"passed": 1}


def test_work_unit_ledger_survives_store_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "progress.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as store:
        _frozen(store, second=False)
        store.begin_work_unit(
            "run-progress", "extract-S001", "persistent-key", "正在提取受试者数据"
        )
    with Store(db_path, artifact_dir) as reopened:
        snapshot = reopened.structured_progress("run-progress")
        assert snapshot["by_status"] == {"running": 1}
        assert len(snapshot["running"]) == 1
        assert snapshot["feed"][0]["event_type"] == "work_unit_begin"
        assert reopened._conn.execute(  # schema migration record is authoritative
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0] == "6"


def test_legacy_marker_three_is_rejected_without_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-migration.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as store:
        _base_run(store)
        store.set_manifest(ExecutionManifest(
            run_id="run-progress",
            nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
        ))
        store.begin_node_run(
            "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "legacy-migrate"
        )
        store.complete_node_run(
            "run-progress", "legacy", "legacy-migrate", NodeStatus.PASSED
        )
        store.set_manifest(ExecutionManifest(
            run_id="run-progress",
            nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
            graph_version="legacy-migration-two",
        ))

    connection = sqlite3.connect(db_path)
    connection.execute("DROP TABLE manifest_node_progress")
    connection.execute("DROP TABLE audit_chain_head")
    connection.execute("UPDATE meta SET value='3' WHERE key='schema_version'")
    connection.commit()
    connection.close()

    before = db_path.read_bytes()
    with pytest.raises(StoreError, match="unsupported schema"):
        Store(db_path, artifact_dir)
    assert db_path.read_bytes() == before


def test_explicit_v4_migration_does_not_rebind_old_node_state_to_current_revision(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "node-revision-migration.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as store:
        _base_run(store)
        revision_one = store.set_manifest(ExecutionManifest(
            run_id="run-progress",
            nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
        ))
        store.begin_node_run(
            "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "old-node"
        )
        store.complete_node_run(
            "run-progress", "legacy", "old-node", NodeStatus.PASSED,
            output={"old": "output"},
        )
        revision_two = store.set_manifest(ExecutionManifest(
            run_id="run-progress",
            nodes=[ManifestNode("legacy", NodeType.DETERMINISTIC_SERVICE)],
            graph_version="node-revision-migration-two",
        ))

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute("DROP INDEX IF EXISTS idx_node_runs_run")
    connection.execute("DROP INDEX IF EXISTS idx_attempts_run")
    connection.execute("ALTER TABLE node_runs RENAME TO node_runs_v5")
    connection.execute(
        "CREATE TABLE node_runs ("
        "run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),"
        "node_id TEXT NOT NULL, node_type TEXT NOT NULL, status TEXT NOT NULL,"
        "idempotency_key TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,"
        "artifact_id TEXT, output_json TEXT NOT NULL DEFAULT '{}', error TEXT,"
        "reason TEXT, started_at TEXT, finished_at TEXT,"
        "PRIMARY KEY (run_id, node_id))"
    )
    connection.execute(
        "INSERT INTO node_runs(run_id,node_id,node_type,status,idempotency_key,"
        "attempts,artifact_id,output_json,error,reason,started_at,finished_at)"
        " SELECT run_id,node_id,node_type,status,idempotency_key,attempts,artifact_id,"
        "output_json,error,reason,started_at,finished_at FROM node_runs_v5"
    )
    connection.execute("DROP TABLE node_runs_v5")
    connection.execute("CREATE INDEX idx_node_runs_run ON node_runs(run_id)")
    connection.execute("ALTER TABLE node_attempts RENAME TO node_attempts_v5")
    connection.execute(
        "CREATE TABLE node_attempts ("
        "run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),"
        "node_id TEXT NOT NULL, attempt_seq INTEGER NOT NULL,"
        "idempotency_key TEXT NOT NULL, logical_key TEXT NOT NULL,"
        "status TEXT NOT NULL, payload_hash TEXT, created_at TEXT NOT NULL,"
        "PRIMARY KEY (run_id,node_id,attempt_seq), UNIQUE(idempotency_key))"
    )
    connection.execute(
        "INSERT INTO node_attempts(run_id,node_id,attempt_seq,idempotency_key,"
        "logical_key,status,payload_hash,created_at)"
        " SELECT run_id,node_id,attempt_seq,idempotency_key,logical_key,status,"
        "payload_hash,created_at FROM node_attempts_v5"
    )
    connection.execute("DROP TABLE node_attempts_v5")
    connection.execute("CREATE INDEX idx_attempts_run ON node_attempts(run_id)")
    connection.execute("UPDATE meta SET value='4' WHERE key='schema_version'")
    connection.commit()
    connection.close()

    before = db_path.read_bytes()
    with pytest.raises(StoreError, match="unsupported schema"):
        Store(db_path, artifact_dir)
    assert db_path.read_bytes() == before

    staged = _stage_runtime_copy(
        tmp_path, db_path, "explicit-node-revision-migration"
    )
    _migrate_runtime_staging(staged, "4")
    with Store(staged, tmp_path / "staged-artifacts") as migrated:
        node = migrated.get_node_run("run-progress", "legacy")
        attempts = migrated.list_node_attempts("run-progress", "legacy")
        assert node.manifest_revision == revision_one
        assert [attempt.manifest_revision for attempt in attempts] == [revision_one]
        assert migrated.structured_progress(
            "run-progress", manifest_revision=revision_two
        )["by_status"] == {"pending": 1}
        reopened = migrated.begin_node_run(
            "run-progress", "legacy", NodeType.DETERMINISTIC_SERVICE, "new-node"
        )
        assert reopened.manifest_revision == revision_two
        assert reopened.output == {}


def test_ai_work_unit_identity_is_journal_derived_and_direct_bypass_is_rejected(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store)

    with pytest.raises(StoreError, match="must begin through"):
        r1_store.begin_work_unit(
            "run-progress", "risk-S001-AE", "caller-key", "正在分析 AE 风险",
            {"provider": "forged-provider", "attempt_id": "forged-attempt"},
        )

    running = r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    )
    assert running.execution_identity == {
        "provider": "synthetic-provider",
        "model": "synthetic-model",
        "selector": "synthetic-selector",
        "adapter": "synthetic-adapter-v1",
        "profile_fingerprint": content_hash({
            "profile": "synthetic-provider", "attempt": "attempt-risk-1",
        }),
        "attempt_id": "attempt-risk-1",
    }
    assert r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    ) == running
    with pytest.raises(IdempotencyConflictError, match="changed its progress detail"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "冲突的进度说明"
        )
    with pytest.raises(StoreError, match="must complete through"):
        r1_store.complete_work_unit(
            "run-progress", "risk-S001-AE", "caller-key", NodeStatus.PASSED,
            "调用方试图绕过 capability 终态",
        )
    with pytest.raises(StoreError, match="terminal or interrupted"):
        r1_store.complete_capability_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "尚未完成"
        )

    _terminal_ai_attempt(r1_store, "attempt-risk-1")
    completed = r1_store.complete_capability_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1",
        "已完成 AE 风险分析",
    )
    assert completed.status == NodeStatus.PASSED
    assert [item["event_type"] for item in r1_store.structured_progress(
        "run-progress"
    )["feed"]] == ["work_unit_begin", "work_unit_complete"]
    assert r1_store.complete_capability_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1",
        "已完成 AE 风险分析",
    ) == completed


def test_terminal_attempt_cannot_close_before_persistence(r1_store: Store) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store)
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    )
    _terminal_ai_attempt(
        r1_store, "attempt-risk-1", persist_for_completion=False,
    )
    with pytest.raises(StoreError, match="not fully persisted"):
        r1_store.complete_capability_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-1", "伪造已完成",
            evidence_count=0,
        )
    row = r1_store.get_work_unit_run("run-progress", 1, "risk-S001-AE")
    assert row.status == NodeStatus.RUNNING
    assert r1_store.structured_progress("run-progress")["percent"] == 0.0


@pytest.mark.parametrize(
    ("attempt_status", "expected"),
    (
        ("complete", NodeStatus.PASSED),
        ("failed", NodeStatus.FAILED),
        ("timeout", NodeStatus.FAILED),
        ("cancelled", NodeStatus.FAILED),
        ("partial", NodeStatus.FAILED),
        ("truncated", NodeStatus.FAILED),
        ("interrupted", NodeStatus.BLOCKED),
    ),
)
def test_capability_outcome_maps_fail_closed_to_work_unit_status(
    r1_store: Store, attempt_status: str, expected: NodeStatus,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store)
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 AE 风险"
    )
    if attempt_status == "interrupted":
        _interrupt_ai_attempt(r1_store, "attempt-risk-1")
    else:
        _terminal_ai_attempt(r1_store, "attempt-risk-1", status=attempt_status)
    completed = r1_store.complete_capability_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "本次分析已结束"
    )
    assert completed.status == expected
    assert r1_store.structured_progress("run-progress")["by_status"] == {
        expected.value: 1,
    }


def test_capability_retry_chain_updates_current_identity_and_preserves_history(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store, attempt_id="attempt-risk-1")
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在进行首次风险分析"
    )
    _interrupt_ai_attempt(r1_store, "attempt-risk-1")
    _declare_ai_attempt(
        r1_store, attempt_id="attempt-risk-2",
        continued_from="attempt-risk-1", provider="synthetic-provider-2",
    )
    retried = r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-2", "正在继续风险分析"
    )
    assert retried.execution_identity["attempt_id"] == "attempt-risk-2"
    assert retried.execution_identity["provider"] == "synthetic-provider-2"
    feed = r1_store.structured_progress("run-progress")["feed"]
    assert [item["event_type"] for item in feed] == [
        "work_unit_begin", "work_unit_attempt_bound",
    ]
    assert feed[-1]["attempt_ordinal"] == 2
    assert feed[-1]["continued_from"] == "attempt-risk-1"
    bindings = r1_store._list_work_unit_capability_attempts(
        "run-progress", 1, "risk-S001-AE"
    )
    assert [item["attempt_id"] for item in bindings] == [
        "attempt-risk-1", "attempt-risk-2",
    ]
    _terminal_ai_attempt(r1_store, "attempt-risk-2")
    assert r1_store.complete_capability_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-2", "已完成继续分析"
    ).status == NodeStatus.PASSED


def test_capability_retry_rejects_broken_chain_and_duplicate_work_unit_use(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store, two_units=True)
    _declare_ai_attempt(r1_store, attempt_id="attempt-risk-1")
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-1", "正在分析 S001"
    )
    with pytest.raises(IdempotencyConflictError, match="another work unit"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S002-AE", "attempt-risk-1", "正在分析 S002"
        )
    _interrupt_ai_attempt(r1_store, "attempt-risk-1")
    _declare_ai_attempt(
        r1_store, attempt_id="attempt-risk-wrong", continued_from="unknown-attempt"
    )
    with pytest.raises(StaleCallbackError, match="latest bound attempt"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-wrong", "错误续接"
        )


def test_capability_binding_rejects_cross_revision_and_detects_binding_corruption(
    r1_store: Store,
) -> None:
    _frozen_ai(r1_store)
    _declare_ai_attempt(r1_store, attempt_id="attempt-risk-old")
    revision_two_manifest = _ai_manifest("run-progress")
    revision_two_manifest.graph_version = "synthetic-ai-progress-v2"
    assert r1_store.set_manifest(revision_two_manifest) == 2
    with pytest.raises(StaleCallbackError, match="does not match the work unit"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "risk-S001-AE", "attempt-risk-old", "迟到的第一版分析",
        )

    _declare_ai_attempt(
        r1_store, attempt_id="attempt-risk-current", manifest_revision=2,
    )
    r1_store.bind_capability_attempt_to_work_unit(
        "run-progress", "risk-S001-AE", "attempt-risk-current", "正在分析第二版数据"
    )
    forged = dict(r1_store.get_work_unit_run(
        "run-progress", 2, "risk-S001-AE"
    ).execution_identity)
    forged["provider"] = "forged-provider"
    r1_store._conn.execute(
        "UPDATE work_unit_capability_attempts SET execution_identity_json=?, identity_hash=?"
        " WHERE attempt_id=?",
        (domain.canonical_json(forged), content_hash(forged),
         "attempt-risk-current"),
    )
    with pytest.raises(StoreError, match="does not match the attempt journal"):
        r1_store.structured_progress("run-progress")


def test_explicit_v5_migration_creates_empty_binding_ledger_without_changing_deterministic_history(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "binding-v5.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as store:
        _frozen(store, second=False)
        store.begin_work_unit(
            "run-progress", "extract-S001", "deterministic-key", "正在提取数据"
        )
        store.complete_work_unit(
            "run-progress", "extract-S001", "deterministic-key", NodeStatus.PASSED,
            "已完成数据提取",
        )
    connection = sqlite3.connect(db_path)
    connection.execute("DROP TABLE work_unit_capability_attempts")
    connection.execute("UPDATE meta SET value='5' WHERE key='schema_version'")
    connection.commit()
    connection.close()
    before = db_path.read_bytes()
    with pytest.raises(StoreError, match="unsupported schema"):
        Store(db_path, artifact_dir)
    assert db_path.read_bytes() == before

    staged = _stage_runtime_copy(tmp_path, db_path, "explicit-binding-migration")
    _migrate_runtime_staging(staged, "5")
    with Store(staged, tmp_path / "staged-artifacts") as migrated:
        assert migrated._conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0] == "6"
        assert migrated._conn.execute(
            "SELECT COUNT(*) FROM work_unit_capability_attempts"
        ).fetchone()[0] == 0
        assert migrated.structured_progress("run-progress")["by_status"] == {
            "passed": 1,
        }


def test_capability_attempt_cannot_bind_a_deterministic_work_unit(
    r1_store: Store,
) -> None:
    _frozen(r1_store, second=False)
    _declare_ai_attempt(r1_store, node_id="extract")
    with pytest.raises(StoreError, match="only to AI candidate"):
        r1_store.bind_capability_attempt_to_work_unit(
            "run-progress", "extract-S001", "attempt-risk-1", "错误绑定"
        )


def test_concurrent_attempt_binding_has_one_authoritative_work_unit(tmp_path: Path) -> None:
    db_path = tmp_path / "concurrent-attempt-binding.sqlite3"
    artifact_dir = tmp_path / "artifacts"
    with Store(db_path, artifact_dir) as setup:
        _frozen_ai(setup, run_id="run-concurrent-binding", two_units=True)
        _declare_ai_attempt(
            setup, run_id="run-concurrent-binding", attempt_id="attempt-shared"
        )
    barrier = threading.Barrier(2)
    successes = []
    errors = []

    def _bind(work_unit_id: str) -> None:
        try:
            with Store(db_path, artifact_dir) as store:
                barrier.wait()
                result = store.bind_capability_attempt_to_work_unit(
                    "run-concurrent-binding", work_unit_id, "attempt-shared",
                    f"正在处理 {work_unit_id}",
                )
                successes.append(result.work_unit_id)
        except BaseException as exc:  # main thread asserts the exact losing class
            errors.append(exc)

    threads = [
        threading.Thread(target=_bind, args=("risk-S001-AE",)),
        threading.Thread(target=_bind, args=("risk-S002-AE",)),
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
        assert verified._conn.execute(
            "SELECT COUNT(*) FROM work_unit_capability_attempts WHERE attempt_id=?",
            ("attempt-shared",),
        ).fetchone()[0] == 1
        snapshot = verified.structured_progress("run-concurrent-binding")
        assert snapshot["by_status"] == {"pending": 1, "running": 1}
