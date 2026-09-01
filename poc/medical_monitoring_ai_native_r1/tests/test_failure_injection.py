"""Black-box failure injection and cross-module R1 acceptance cases.

These tests intentionally exercise the public Store/Graph/adapter/AE-MH/report
contracts together.  They do not patch implementation files.  A failing test
is evidence for the execution manager, not a reason for this worker to cross
the worker_01-03 ownership boundary.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Optional, Sequence, Tuple

import pytest

from mm_r1 import domain
from mm_r1.adapters import (
    AdapterState,
    ImmutableAdapterBinding,
    ScriptedAdapter,
    ScriptedOutput,
    persist_adapter_run,
)
from mm_r1.ae_mh import (
    merge_risk_identities,
    reconcile_risk_lifecycle,
    run_ae_mh_vertical_slice,
    split_risk_identity,
)
from mm_r1.domain import (
    AnalysisState,
    ArtifactCompleteness,
    ArtifactEnvelope,
    CoverageManifest,
    CoverageUnit,
    CoverageUnitStatus,
    EvidenceState,
    ExecutionBasis,
    ExecutionManifest,
    ListingSnapshot,
    ManifestNode,
    MonitoringRun,
    NodeStatus,
    NodeType,
    OutputState,
    RiskCandidate,
    RiskIdentity,
    RiskLifecycleState,
    RunMode,
    SnapshotAcceptance,
    SnapshotAcceptanceState,
    SnapshotBaselineProof,
    SourceRevision,
    content_hash,
)
from mm_r1.fixtures import seed_synthetic_snapshots
from mm_r1.graph import Graph, GraphNode, LocalGraphPort, NodeContext, NodeOutcome
from mm_r1.report_review import review_report, synthetic_report_fixture
from mm_r1.store import CompletionGateError, StaleCallbackError


def _coverage(
    key: str,
    status: CoverageUnitStatus = CoverageUnitStatus.COVERED,
) -> CoverageManifest:
    expected = CoverageUnit(scope=domain.SCOPE_SUBJECT, key=key)
    produced = CoverageUnit(scope=domain.SCOPE_SUBJECT, key=key, status=status)
    return CoverageManifest(expected=[expected], produced=[produced]).reconcile()


def _envelope(
    run_id: str,
    node_id: str,
    *,
    completeness: ArtifactCompleteness = ArtifactCompleteness.COMPLETE,
    coverage_status: CoverageUnitStatus = CoverageUnitStatus.COVERED,
    payload: Optional[Mapping[str, Any]] = None,
    node_type: NodeType = NodeType.DETERMINISTIC_SERVICE,
) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_type="synthetic-analysis",
        version="r1",
        run_id=run_id,
        node_id=node_id,
        node_type=node_type,
        payload=dict(payload or {"fixture_marker": "SYNTHETIC", "node_id": node_id}),
        coverage=_coverage("SYNTHETIC-SUBJECT-001", coverage_status),
        completeness=completeness,
    )


def _prepare_run(store: Any, run_id: str, node_ids: Sequence[str] = ()) -> str:
    """Create a synthetic project/revision/run without production fixtures."""
    project_id = "SYNTHETIC-PROJECT-" + run_id
    revision_id = "SYNTHETIC-REVISION-" + run_id
    store.create_project(project_id, "SYNTHETIC worker04 project")
    store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTHETIC-1",
            content_hash=content_hash({"fixture_marker": "SYNTHETIC", "revision": revision_id}),
        )
    )
    store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-CUTOFF-1",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    if node_ids:
        store.set_manifest(
            ExecutionManifest(
                run_id=run_id,
                nodes=[
                    ManifestNode(
                        node_id=node_id,
                        node_type=NodeType.DETERMINISTIC_SERVICE,
                    )
                    for node_id in node_ids
                ],
                identity_algorithm="SYNTHETIC-IDENTITY-V1",
                graph_version="SYNTHETIC-GRAPH-V1",
                schema_version="SYNTHETIC-SCHEMA-V1",
            )
        )
    return project_id


def _complete_node(
    store: Any,
    run_id: str,
    node_id: str,
    key: str,
    *,
    envelope: Optional[ArtifactEnvelope] = None,
    node_type: NodeType = NodeType.DETERMINISTIC_SERVICE,
    output: Optional[Mapping[str, Any]] = None,
) -> Any:
    store.begin_node_run(run_id, node_id, node_type, key)
    return store.complete_node_run(
        run_id,
        node_id,
        key,
        NodeStatus.PASSED,
        envelope=envelope,
        output=output,
    )


def _nonaccepted_snapshot_pair(store: Any) -> Tuple[Any, Any, str]:
    bundle = seed_synthetic_snapshots(store)
    unaccepted_id = "SYNTHETIC-SNAPSHOT-UNACCEPTED"
    store.add_listing_snapshot(
        ListingSnapshot(
            snapshot_id=unaccepted_id,
            project_id=bundle.project_id,
            revision_id=bundle.revision_n1.revision_id,
            snapshot_version="SYNTHETIC-N1-UNACCEPTED",
            structure=dict(bundle.snapshot_n1.structure),
            is_synthetic=True,
        ),
        bundle.listing_n1,
    )
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-N",
        snapshot_version="SYNTHETIC-N",
        current_snapshot_baseline_eligible=True,
    )
    return bundle, result_n, unaccepted_id


def _candidate(identity: str, concept: str, run_id: str, severity: str) -> RiskCandidate:
    risk_identity = RiskIdentity(
        project_id="SYNTHETIC-PROJECT-LINEAGE",
        scope="subject",
        subject_id="SYNTHETIC-SUBJECT-001",
        site_id="SYNTHETIC-SITE-A",
        risk_domain="potential_unreported_ae",
        event_identity=identity,
        normalized_concept=concept,
        temporal_window="SYNTHETIC-2026-01-01..SYNTHETIC-2026-01-02",
        lineage="SYNTHETIC-RULE-V1",
        algorithm_version="SYNTHETIC-IDENTITY-V1",
    )
    return RiskCandidate(
        candidate_id="SYNTHETIC-CANDIDATE-" + identity + "-" + run_id,
        run_id=run_id,
        node_id="SYNTHETIC-AE-MH-NODE",
        risk_type="potential_unreported_ae",
        risk_domain="potential_unreported_ae",
        subject_id="SYNTHETIC-SUBJECT-001",
        site_id="SYNTHETIC-SITE-A",
        identity=risk_identity,
        severity=severity,
        evidence_refs=["SYNTHETIC|row=" + identity],
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_crash_after_artifact_stage_before_db_commit_is_orphan_only(r1_store, monkeypatch):
    """A commit-boundary crash must not create an authoritative artifact row."""
    run_id = "SYNTHETIC-RUN-W04-CRASH"
    _prepare_run(r1_store, run_id, ["SYNTHETIC-NODE-CRASH"])
    r1_store.update_run_state(run_id, analysis=AnalysisState.RUNNING)
    envelope = _envelope(run_id, "SYNTHETIC-NODE-CRASH")
    staged_hash = r1_store.stage_artifact(envelope)

    def injected_db_crash(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("SYNTHETIC injected DB commit crash")

    monkeypatch.setattr(r1_store, "_insert_artifact_row", injected_db_crash)
    with pytest.raises(RuntimeError, match="injected DB commit crash"):
        r1_store.commit_artifact(staged_hash, envelope)

    assert r1_store.get_artifact_by_hash(staged_hash) is None
    assert r1_store.get_run(run_id).output_state == OutputState.NOT_PUBLISHED
    assert staged_hash + ".json" in r1_store.find_orphan_artifacts()
    recovery = r1_store.recover()
    assert recovery.audit_ok is True
    assert staged_hash + ".json" in recovery.orphan_artifacts


@pytest.mark.parametrize("advance_api", ("publish", "update_run_state"))
def test_tampered_artifact_after_analysis_complete_blocks_later_publication(
    r1_store,
    advance_api: str,
):
    """Later output advancement must re-check bytes after analysis completion."""
    run_id = "SYNTHETIC-RUN-W04-TAMPER-" + advance_api
    _prepare_run(r1_store, run_id, ["SYNTHETIC-NODE-TAMPER"])
    r1_store.update_run_state(
        run_id,
        analysis=AnalysisState.RUNNING,
        evidence=EvidenceState.COMPLETE,
    )
    node = _complete_node(
        r1_store,
        run_id,
        "SYNTHETIC-NODE-TAMPER",
        "SYNTHETIC-TAMPER-KEY",
        envelope=_envelope(run_id, "SYNTHETIC-NODE-TAMPER"),
    )
    r1_store.complete_analysis(run_id)
    artifact_path = r1_store.artifact_dir / (node.artifact_id + ".json")
    artifact_path.write_text("{}", encoding="utf-8")
    assert r1_store.verify_artifact(node.artifact_id) is False

    try:
        if advance_api == "publish":
            r1_store.publish(run_id, OutputState.DRAFT_EXPORTABLE)
        else:
            r1_store.update_run_state(run_id, output=OutputState.DRAFT_EXPORTABLE)
    except CompletionGateError:
        pass
    else:
        pytest.fail(
            "%s accepted tampered artifact: output_state=%s verify_artifact=%s"
            % (advance_api, r1_store.get_run(run_id).output_state.value,
               r1_store.verify_artifact(node.artifact_id))
        )
    assert r1_store.get_run(run_id).output_state == OutputState.DASHBOARD_VISIBLE


def test_store_derived_nonaccepted_snapshot_blocks_lifecycle_resolution(r1_store):
    bundle, result_n, snapshot_id = _nonaccepted_snapshot_pair(r1_store)
    accepted = r1_store.get_acceptance(snapshot_id)
    store_derived_eligibility = accepted.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
    assert accepted.state == SnapshotAcceptanceState.IMPORTED
    assert store_derived_eligibility is False

    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-N1-STORE-DERIVED",
        snapshot_version="SYNTHETIC-N1-UNACCEPTED",
        previous_result=result_n,
        current_snapshot_baseline_eligible=store_derived_eligibility,
    )
    assert all(
        instance.lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
        for instance in result_n1.lifecycle.instances
    )


def test_caller_baseline_assertion_cannot_override_store_rejection(r1_store):
    """A caller cannot self-attest acceptance with a bare True."""
    bundle, result_n, snapshot_id = _nonaccepted_snapshot_pair(r1_store)
    assert r1_store.get_acceptance(snapshot_id).state != SnapshotAcceptanceState.BASELINE_ELIGIBLE
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-N1-CALLER-ASSERTED",
        snapshot_version="SYNTHETIC-N1-UNACCEPTED",
        previous_result=result_n,
        current_snapshot_baseline_eligible=True,
    )
    resolved = [
        (instance.identity_key, instance.lifecycle_state.value)
        for instance in result_n1.lifecycle.instances
        if instance.lifecycle_state == RiskLifecycleState.RESOLVED_BY_DATA
    ]
    assert not resolved, (
        "caller assertion overrode Store rejection: snapshot=%s acceptance=%s resolved=%s"
        % (snapshot_id, r1_store.get_acceptance(snapshot_id).state.value, resolved)
    )


def test_manufactured_baseline_proof_cannot_authorize_without_store(r1_store):
    """from_acceptance / constructor proofs are projection-only without Store lookup."""
    bundle, result_n, snapshot_id = _nonaccepted_snapshot_pair(r1_store)
    forged_acceptance = SnapshotAcceptance(
        snapshot_id=snapshot_id,
        state=SnapshotAcceptanceState.BASELINE_ELIGIBLE,
        accepted_by="system_policy",
        blocked=False,
        reason="SYNTHETIC forged acceptance",
    )
    forged_proof = SnapshotBaselineProof.from_acceptance(forged_acceptance)
    assert forged_proof.store_verified is True
    assert forged_proof.is_baseline_eligible is True

    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-N1-FORGED-PROOF",
        snapshot_version="SYNTHETIC-N1-UNACCEPTED",
        previous_result=result_n,
        current_snapshot_baseline_eligible=forged_proof,
    )
    assert result_n1.snapshot_baseline_eligible is False
    assert all(
        instance.lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
        for instance in result_n1.lifecycle.instances
    )

    merge_result = merge_risk_identities(
        [_candidate("SYNTHETIC-FORGE-MERGE", "synthetic forge", "SYNTHETIC-RUN-W04-FORGE", "medium")],
        [_candidate("SYNTHETIC-FORGE-PRIOR", "synthetic prior", "SYNTHETIC-RUN-PREV", "medium")],
        _candidate("SYNTHETIC-FORGE-MERGE", "synthetic forge", "SYNTHETIC-RUN-W04-FORGE", "medium").identity.stable_key(),
        [_candidate("SYNTHETIC-FORGE-PRIOR", "synthetic prior", "SYNTHETIC-RUN-PREV", "medium").identity.stable_key()],
        current_run_id="SYNTHETIC-RUN-W04-FORGE",
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=forged_proof,
    )
    assert all(
        instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
        for instance in merge_result.instances
    )
    assert not any(transition.kind == "merge" for transition in merge_result.transitions)


def test_manufactured_proof_cannot_override_imported_store_snapshot(r1_store):
    """Even with store+snapshot_id, a forged eligible proof cannot override imported."""
    bundle, result_n, snapshot_id = _nonaccepted_snapshot_pair(r1_store)
    assert r1_store.get_acceptance(snapshot_id).state == SnapshotAcceptanceState.IMPORTED
    forged_proof = SnapshotBaselineProof.from_acceptance(
        SnapshotAcceptance(
            snapshot_id=snapshot_id,
            state=SnapshotAcceptanceState.BASELINE_ELIGIBLE,
            accepted_by="system_policy",
        )
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-N1-FORGED-OVERRIDE",
        snapshot_version="SYNTHETIC-N1-UNACCEPTED",
        previous_result=result_n,
        current_snapshot_baseline_eligible=forged_proof,
        store=r1_store,
        snapshot_id=snapshot_id,
    )
    assert result_n1.snapshot_baseline_eligible is False
    assert all(
        instance.lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
        for instance in result_n1.lifecycle.instances
    )
    split_result = split_risk_identity(
        [
            _candidate("SYNTHETIC-FORGE-SPLIT-L", "left", "SYNTHETIC-RUN-W04-FORGE", "medium"),
            _candidate("SYNTHETIC-FORGE-SPLIT-R", "right", "SYNTHETIC-RUN-W04-FORGE", "medium"),
        ],
        [_candidate("SYNTHETIC-FORGE-SPLIT-SRC", "source", "SYNTHETIC-RUN-PREV", "high")],
        _candidate("SYNTHETIC-FORGE-SPLIT-SRC", "source", "SYNTHETIC-RUN-PREV", "high").identity.stable_key(),
        [
            _candidate("SYNTHETIC-FORGE-SPLIT-L", "left", "SYNTHETIC-RUN-W04-FORGE", "medium").identity.stable_key(),
            _candidate("SYNTHETIC-FORGE-SPLIT-R", "right", "SYNTHETIC-RUN-W04-FORGE", "medium").identity.stable_key(),
        ],
        current_run_id="SYNTHETIC-RUN-W04-FORGE",
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=forged_proof,
        store=r1_store,
        snapshot_id=snapshot_id,
    )
    assert all(
        instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
        for instance in split_result.instances
    )
    assert not any(transition.kind == "split" for transition in split_result.transitions)


def test_eligible_snapshot_from_another_project_cannot_authorize_resolution(r1_store):
    """A live eligible Store row is insufficient when its project is different."""
    bundle = seed_synthetic_snapshots(r1_store)
    other_bundle = seed_synthetic_snapshots(
        r1_store, project_id="SYNTHETIC-PROJECT-CROSS-BOUNDARY"
    )
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-CROSS-N",
        snapshot_version=bundle.snapshot_n.snapshot_version,
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-CROSS-N1",
        snapshot_version=bundle.snapshot_n1.snapshot_version,
        previous_result=result_n,
        store=r1_store,
        snapshot_id=other_bundle.snapshot_n1.snapshot_id,
    )
    assert result_n1.snapshot_baseline_eligible is False
    assert all(
        instance.lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
        for instance in result_n1.lifecycle.instances
    )


def test_eligible_snapshot_version_mismatch_cannot_authorize_resolution(r1_store):
    """The Store snapshot must be the exact version analyzed, not only same-project."""
    bundle = seed_synthetic_snapshots(r1_store)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-VERSION-N",
        snapshot_version=bundle.snapshot_n.snapshot_version,
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-W04-VERSION-N1",
        snapshot_version=bundle.snapshot_n1.snapshot_version,
        previous_result=result_n,
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    assert result_n1.snapshot_baseline_eligible is False
    assert all(
        instance.lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
        for instance in result_n1.lifecycle.instances
    )


def test_adapter_persistence_is_candidate_only_and_state_neutral(r1_store):
    run_id = "SYNTHETIC-RUN-W04-ADAPTER"
    _prepare_run(r1_store, run_id)
    before = r1_store.get_run(run_id)
    unit = CoverageUnit(scope=domain.SCOPE_SUBJECT, key="SYNTHETIC-SUBJECT-001")
    adapter = ScriptedAdapter(
        ImmutableAdapterBinding(
            binding_id="SYNTHETIC-BINDING-W04",
            capability="synthetic-risk-candidate",
            provider="deterministic-script",
            model="synthetic-model",
            selector="synthetic-selector",
            effort="fixed",
            isolation="fresh_context",
        ),
        [
            ScriptedOutput(
                status=AdapterState.COMPLETE,
                payload={"fixture_marker": "SYNTHETIC", "candidate": True},
                raw_output={"fixture_marker": "SYNTHETIC", "candidate": True},
                expected_units=(unit,),
                produced_units=(
                    CoverageUnit(
                        scope=unit.scope,
                        key=unit.key,
                        status=CoverageUnitStatus.COVERED,
                    ),
                ),
            )
        ],
    )
    adapter_run = adapter.run(
        {"fixture_marker": "SYNTHETIC"},
        monitoring_run_id=run_id,
        node_id="SYNTHETIC-AI-CANDIDATE",
    )
    receipt = persist_adapter_run(r1_store, adapter_run)
    replay = persist_adapter_run(r1_store, adapter_run)
    after = r1_store.get_run(run_id)

    assert receipt.candidate_only is True
    assert all(value is False for value in receipt.authority.__dict__.values())
    assert replay.artifact_id == receipt.artifact_id
    assert r1_store.list_facts(run_id) == []
    assert (after.analysis_state, after.evidence_state, after.review_state, after.output_state) == (
        before.analysis_state,
        before.evidence_state,
        before.review_state,
        before.output_state,
    )
    assert len(r1_store.list_artifacts(run_id)) == 1
    assert all(len(r1_store.list_domain_objects(kind)) == 1 for kind in (
        "adapter_binding",
        "adapter_run",
        "adapter_analysis",
        "adapter_raw_output",
    ))


def test_incomplete_merge_split_persist_lineage_without_rewriting_identities(r1_store):
    run_id = "SYNTHETIC-RUN-W04-LINEAGE"
    _prepare_run(r1_store, run_id)
    prior_left = _candidate("SYNTHETIC-MERGE-LEFT", "synthetic left", "SYNTHETIC-RUN-PREV", "medium")
    prior_right = _candidate("SYNTHETIC-MERGE-RIGHT", "synthetic right", "SYNTHETIC-RUN-PREV", "medium")
    current_merge = _candidate("SYNTHETIC-MERGE-CURRENT", "synthetic merged", run_id, "medium")
    merge_result = merge_risk_identities(
        [current_merge],
        [prior_left, prior_right],
        current_merge.identity.stable_key(),
        [prior_left.identity.stable_key(), prior_right.identity.stable_key()],
        current_run_id=run_id,
        current_coverage_complete=False,
        current_snapshot_baseline_eligible=True,
    )

    prior_split = _candidate("SYNTHETIC-SPLIT-SOURCE", "synthetic source", "SYNTHETIC-RUN-PREV", "high")
    current_split_left = _candidate("SYNTHETIC-SPLIT-LEFT", "synthetic left", run_id, "medium")
    current_split_right = _candidate("SYNTHETIC-SPLIT-RIGHT", "synthetic right", run_id, "medium")
    split_result = split_risk_identity(
        [current_split_left, current_split_right],
        [prior_split],
        prior_split.identity.stable_key(),
        [current_split_left.identity.stable_key(), current_split_right.identity.stable_key()],
        current_run_id=run_id,
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=False,
    )

    for result in (merge_result, split_result):
        assert all(instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
                   for instance in result.instances)
        assert not any(transition.kind in {"merge", "split"}
                       for transition in result.transitions)
        assert all(value not in {"merge_target", "merge_source", "split_target", "split_source"}
                   for value in result.relation_by_identity.values())
        for transition in result.transitions:
            r1_store.put_domain_object(
                "risk_transition",
                transition.transition_id,
                transition,
                run_id=run_id,
                idempotency_key="SYNTHETIC-TRANSITION-" + transition.transition_id,
            )
    persisted = [
        r1_store.get_domain_object("risk_transition", object_id)[1]
        for object_id, _version in r1_store.list_domain_objects("risk_transition")
    ]
    assert persisted
    assert all(item["kind"] not in {"merge", "split"} for item in persisted)


def test_invalid_report_ledger_cannot_complete_or_publish_run(r1_store):
    run_id = "SYNTHETIC-RUN-W04-REPORT"
    _prepare_run(r1_store, run_id, ["SYNTHETIC-REPORT-NODE"])
    r1_store.update_run_state(
        run_id,
        analysis=AnalysisState.RUNNING,
        evidence=EvidenceState.COMPLETE,
    )
    fixture = synthetic_report_fixture(run_id=run_id)
    invalid = review_report(fixture, list(review_report(fixture).ledger.entries)[:-1])
    envelope = invalid.ledger.to_artifact_envelope(node_id="SYNTHETIC-REPORT-NODE")
    assert invalid.full_report_reviewed is False
    assert envelope.is_publishable()[0] is False
    _complete_node(
        r1_store,
        run_id,
        "SYNTHETIC-REPORT-NODE",
        "SYNTHETIC-REPORT-KEY",
        envelope=envelope,
    )
    with pytest.raises(CompletionGateError):
        r1_store.complete_analysis(run_id)
    assert r1_store.get_run(run_id).analysis_state == AnalysisState.RUNNING
    assert r1_store.get_run(run_id).output_state == OutputState.NOT_PUBLISHED


def test_manifest_replay_preserves_progress_denominator_and_side_effect_count(r1_store):
    run_id = "SYNTHETIC-RUN-W04-REPLAY"
    _prepare_run(r1_store, run_id)
    graph = Graph(graph_id="SYNTHETIC-GRAPH-W04")
    graph.add_node(
        GraphNode(
            "SYNTHETIC-CANDIDATE-NODE",
            NodeType.DETERMINISTIC_SERVICE,
            handler="candidate",
        )
    )
    graph.add_node(
        GraphNode(
            "SYNTHETIC-QC-NODE",
            NodeType.DETERMINISTIC_SERVICE,
            handler="qc",
            artifact_required=False,
        )
    )
    graph.add_edge("SYNTHETIC-CANDIDATE-NODE", "SYNTHETIC-QC-NODE")
    manifest = graph.to_manifest(
        run_id,
        identity_algorithm="SYNTHETIC-IDENTITY-W04",
        graph_version="SYNTHETIC-GRAPH-V1",
        schema_version="SYNTHETIC-SCHEMA-V1",
    )
    first_revision = r1_store.set_manifest(manifest)

    def candidate_handler(ctx: NodeContext) -> NodeOutcome:
        return NodeOutcome(
            status=NodeStatus.PASSED,
            artifact=_envelope(ctx.run_id, ctx.node_id),
            output={"fixture_marker": "SYNTHETIC", "candidate_ran": True},
        )

    def qc_handler(ctx: NodeContext) -> NodeOutcome:
        ctx.store.update_run_state(ctx.run_id, evidence=EvidenceState.COMPLETE)
        return NodeOutcome(status=NodeStatus.PASSED, output={"qc": "passed"})

    port = LocalGraphPort(r1_store, {"candidate": candidate_handler, "qc": qc_handler})
    first = port.run(graph, run_id)
    progress_before = r1_store.manifest_progress(run_id)
    artifacts_before = len(r1_store.list_artifacts(run_id))
    node_complete_before = sum(
        event.event_type == domain.EVENT_NODE_COMPLETE for event in r1_store.audit_trail()
    )
    replay_revision = r1_store.set_manifest(manifest)
    replayed = port.replay(run_id)

    assert first.status == "complete"
    assert replay_revision == first_revision == 1
    assert r1_store.list_manifest_revisions(run_id) == [1]
    assert progress_before == {"completed": 2, "total": 2, "by_status": {"passed": 2}}
    assert r1_store.manifest_progress(run_id) == progress_before
    assert replayed.status == "complete"
    assert all(result.reused for result in replayed.node_results)
    assert len(r1_store.list_artifacts(run_id)) == artifacts_before == 1
    assert sum(event.event_type == domain.EVENT_NODE_COMPLETE
               for event in r1_store.audit_trail()) == node_complete_before


def test_duplicate_and_late_callbacks_keep_one_attempt_and_one_artifact(r1_store):
    run_id = "SYNTHETIC-RUN-W04-CALLBACK"
    _prepare_run(r1_store, run_id, ["SYNTHETIC-CALLBACK-NODE"])
    envelope = _envelope(run_id, "SYNTHETIC-CALLBACK-NODE")
    first = _complete_node(
        r1_store,
        run_id,
        "SYNTHETIC-CALLBACK-NODE",
        "SYNTHETIC-CALLBACK-KEY",
        envelope=envelope,
    )
    replay = r1_store.complete_node_run(
        run_id,
        "SYNTHETIC-CALLBACK-NODE",
        "SYNTHETIC-CALLBACK-KEY",
        NodeStatus.PASSED,
        envelope=envelope,
    )
    with pytest.raises(StaleCallbackError):
        r1_store.complete_node_run(
            run_id,
            "SYNTHETIC-CALLBACK-NODE",
            "SYNTHETIC-LATE-KEY",
            NodeStatus.PASSED,
            envelope=_envelope(run_id, "SYNTHETIC-CALLBACK-NODE", payload={"late": True}),
        )
    assert replay.artifact_id == first.artifact_id
    assert len(r1_store.list_node_attempts(run_id, "SYNTHETIC-CALLBACK-NODE")) == 1
    assert len(r1_store.list_artifacts(run_id)) == 1
    assert r1_store.find_orphan_artifacts() == []
    assert any(
        event.event_type == domain.EVENT_NODE_REJECTED
        and event.payload.get("reason") == "stale_callback"
        for event in r1_store.audit_trail()
    )


@pytest.mark.parametrize(
    ("completeness", "coverage_status"),
    (
        (ArtifactCompleteness.PARTIAL, CoverageUnitStatus.PARTIAL),
        (ArtifactCompleteness.TRUNCATED, CoverageUnitStatus.TRUNCATED),
    ),
)
def test_partial_or_truncated_artifact_cannot_complete_analysis(
    r1_store,
    completeness: ArtifactCompleteness,
    coverage_status: CoverageUnitStatus,
):
    run_id = "SYNTHETIC-RUN-W04-" + completeness.value
    _prepare_run(r1_store, run_id, ["SYNTHETIC-INCOMPLETE-NODE"])
    r1_store.update_run_state(
        run_id,
        analysis=AnalysisState.RUNNING,
        evidence=EvidenceState.COMPLETE,
    )
    _complete_node(
        r1_store,
        run_id,
        "SYNTHETIC-INCOMPLETE-NODE",
        "SYNTHETIC-INCOMPLETE-KEY",
        envelope=_envelope(
            run_id,
            "SYNTHETIC-INCOMPLETE-NODE",
            completeness=completeness,
            coverage_status=coverage_status,
        ),
    )
    with pytest.raises(CompletionGateError):
        r1_store.complete_analysis(run_id)
    run = r1_store.get_run(run_id)
    assert run.analysis_state == AnalysisState.RUNNING
    assert run.output_state == OutputState.NOT_PUBLISHED


def test_audit_tampering_blocks_recovery_event_append(r1_store):
    run_id = "SYNTHETIC-RUN-W04-AUDIT"
    _prepare_run(r1_store, run_id, ["SYNTHETIC-AUDIT-NODE"])
    _complete_node(
        r1_store,
        run_id,
        "SYNTHETIC-AUDIT-NODE",
        "SYNTHETIC-AUDIT-KEY",
        envelope=_envelope(run_id, "SYNTHETIC-AUDIT-NODE"),
    )
    before_count = len(r1_store.audit_trail())
    conn = sqlite3.connect(str(r1_store.db_path))
    conn.execute("UPDATE audit_events SET payload_json=? WHERE seq=1", ('{"tampered":true}',))
    conn.commit()
    conn.close()

    recovery = r1_store.recover()
    assert recovery.audit_ok is False
    assert recovery.audit_first_bad_seq == 1
    assert len(r1_store.audit_trail()) == before_count
    assert not any(event.event_type == domain.EVENT_RECOVERY
                   for event in r1_store.audit_trail())
    assert r1_store.get_artifact_by_hash("SYNTHETIC-NONEXISTENT-HASH") is None
