"""Tests for the worker_01 public contract: orthogonal states, snapshot
acceptance chain, artifact coverage, Graph IR + ports, SQLite authoritative
store, audit chain, idempotency and recovery.

Run only from the POC root:
    ../../.venv/bin/python -m pytest tests/test_domain_store_graph.py -q
All runtime products land in pytest tmp dirs.
"""

from __future__ import annotations

import getpass
import sqlite3
from pathlib import Path

import pytest

from mm_r1 import domain
from mm_r1.domain import (
    ACCEPTANCE_CHAIN,
    NODE_TYPES,
    AnalysisState,
    ArtifactCompleteness,
    ArtifactEnvelope,
    CanonicalFact,
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
    ReviewState,
    RiskLifecycleState,
    RunMode,
    SnapshotAcceptanceState,
    SourceRevision,
    UserDisposition,
    canonical_json,
    content_hash,
)
from mm_r1.graph import (
    Graph,
    GraphEdge,
    GraphNode,
    GraphPort,
    LocalGraphPort,
    NodeContext,
    NodeOutcome,
)
from mm_r1.store import (
    AcceptanceChainError,
    AmbiguityBlocksAcceptanceError,
    ArtifactCollisionError,
    CompletionGateError,
    IdempotencyConflictError,
    NodeTerminalError,
    PromotionForbiddenError,
    StaleCallbackError,
    Store,
    StoreError,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def full_coverage(keys, extra_expected=()):
    """Reconciled coverage manifest: every expected unit covered."""
    expected = [CoverageUnit(scope=domain.SCOPE_SUBJECT, key=k) for k in list(keys) + list(extra_expected)]
    produced = [CoverageUnit(scope=domain.SCOPE_SUBJECT, key=k, status=CoverageUnitStatus.COVERED)
                for k in keys]
    cov = CoverageManifest(expected=expected, produced=produced)
    return cov.reconcile()


def make_env(run_id, node_id, node_type=NodeType.DETERMINISTIC_SERVICE, payload=None,
             completeness=ArtifactCompleteness.COMPLETE, keys=("S001",),
             role=domain.PAYLOAD_ROLE_INFERENCE):
    return ArtifactEnvelope(
        artifact_type="analysis", version="1", run_id=run_id, node_id=node_id,
        node_type=node_type, payload=dict(payload or {"note": "synthetic"}),
        payload_role=role, coverage=full_coverage(keys), completeness=completeness,
    )


def make_project(store, pid="PROJ-R1-SYN"):
    return store.create_project(pid, f"Synthetic project {pid}")


def make_revision(store, pid, rid="rev-1"):
    return store.add_source_revision(SourceRevision(
        revision_id=rid, project_id=pid, source_type="listing", version="1.0",
        content_hash=content_hash({"rev": rid, "project": pid, "synthetic": True}),
    ))


def make_snapshot(store, pid, snapshot_id="snap-N", version="N", rows=None,
                  revision_id="rev-1"):
    data = rows if rows is not None else {
        "ae": [{"subject_id": "S001", "ae_term": "Headache", "onset": "2026-01-10"}],
    }
    return store.add_listing_snapshot(
        ListingSnapshot(snapshot_id=snapshot_id, project_id=pid, revision_id=revision_id,
                        snapshot_version=version, is_synthetic=True),
        data,
    )


def accept_chain(store, snapshot_id, accepted_by="system_policy"):
    st = SnapshotAcceptanceState
    for target in ACCEPTANCE_CHAIN[1:]:
        store.transition_snapshot_acceptance(snapshot_id, target, accepted_by=accepted_by,
                                             reason=f"to {target.value}")


def make_run(store, pid, run_id="run-1", mode=RunMode.DAILY, revision_id="rev-1"):
    return store.create_run(MonitoringRun(
        run_id=run_id, project_id=pid, mode=mode, data_cutoff="2026-01-31",
        source_revision_id=revision_id, execution_basis=ExecutionBasis.FULL,
    ))


def frozen_run(store, pid, run_id="run-1", nodes=None, snapshot_id="snap-N",
               revision_id="rev-1"):
    """Project + revision + snapshot + run + manifest; returns run_id."""
    make_project(store, pid)
    make_revision(store, pid, revision_id)
    make_snapshot(store, pid, snapshot_id, revision_id=revision_id)
    make_run(store, pid, run_id, revision_id=revision_id)
    manifest = ExecutionManifest(run_id=run_id, nodes=[
        ManifestNode(node_id=n, node_type=NodeType.DETERMINISTIC_SERVICE, handler="h")
        for n in (nodes or ["n1"])
    ], identity_algorithm="identity-v1", graph_version="graph-v1", schema_version="schema-v1")
    store.set_manifest(manifest)
    return run_id


def run_node(store, run_id, node_id="n1", node_type=NodeType.DETERMINISTIC_SERVICE,
             key="k1", status=NodeStatus.PASSED, envelope=None, output=None,
             payload_hash=None, error=None):
    store.begin_node_run(run_id, node_id, node_type, key)
    return store.complete_node_run(run_id, node_id, key, status, envelope=envelope,
                                   output=output, payload_hash=payload_hash, error=error)


def complete_run(store, run_id, evidence=EvidenceState.COMPLETE):
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING, evidence=evidence)
    return store.complete_analysis(run_id)


# ---------------------------------------------------------------------------
# orthogonal states
# ---------------------------------------------------------------------------

def test_orthogonal_states_are_distinct():
    """analysis/evidence/review/output are independent; no single complete flag."""
    run = MonitoringRun(run_id="r", project_id="p", mode=RunMode.DAILY, data_cutoff="",
                        source_revision_id="", execution_basis=ExecutionBasis.FULL)
    assert run.analysis_state == AnalysisState.NOT_STARTED
    assert run.evidence_state == EvidenceState.NOT_EVALUABLE
    assert run.review_state == ReviewState.NOT_REQUIRED
    assert run.output_state == OutputState.NOT_PUBLISHED
    # one axis complete leaves the others untouched
    run.analysis_state = AnalysisState.COMPLETE
    assert run.evidence_state == EvidenceState.NOT_EVALUABLE
    assert run.review_state == ReviewState.NOT_REQUIRED
    assert run.output_state == OutputState.NOT_PUBLISHED


def test_analysis_state_transition_rules(r1_store):
    pid = "P-ORTHO"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_run(r1_store, pid, "r-ortho")
    store = r1_store
    with pytest.raises(StoreError):
        store.update_run_state("r-ortho", analysis=AnalysisState.COMPLETE)  # skip RUNNING
    store.update_run_state("r-ortho", analysis=AnalysisState.RUNNING)
    store.update_run_state("r-ortho", analysis=AnalysisState.BLOCKED)
    store.update_run_state("r-ortho", analysis=AnalysisState.RUNNING)  # resume
    store.update_run_state("r-ortho", analysis=AnalysisState.FAILED)
    with pytest.raises(StoreError):
        store.update_run_state("r-ortho", analysis=AnalysisState.RUNNING)  # FAILED terminal


def test_review_state_transition_rules(r1_store):
    pid = "P-REV"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_run(r1_store, pid, "r-rev")
    store = r1_store
    with pytest.raises(StoreError):
        store.update_run_state("r-rev", review=ReviewState.USER_CONFIRMED)  # needs prior state
    store.update_run_state("r-rev", review=ReviewState.DETERMINISTIC_VERIFIED)
    store.update_run_state("r-rev", review=ReviewState.NEEDS_USER_ATTENTION)
    store.update_run_state("r-rev", review=ReviewState.USER_CONFIRMED)
    with pytest.raises(StoreError):
        store.update_run_state("r-rev", review=ReviewState.NEEDS_USER_ATTENTION)  # confirmed terminal


def test_output_state_monotonic(r1_store):
    pid = "P-OUT"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_run(r1_store, pid, "r-out")
    store = r1_store
    with pytest.raises(StoreError):
        store.update_run_state("r-out", output=OutputState.DASHBOARD_VISIBLE)  # analysis not done
    store.update_run_state("r-out", output=OutputState.NOT_PUBLISHED)  # no-op
    with pytest.raises(StoreError):
        store.update_run_state("r-out", output=OutputState.EXPORTED)  # jump


def test_user_disposition_requires_actor(r1_store):
    pid = "P-DISP"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_run(r1_store, pid, "r-disp")
    store = r1_store
    with pytest.raises(StoreError):
        store.update_run_state("r-disp", user_disposition=UserDisposition.CONFIRMED)
    with pytest.raises(StoreError):
        store.update_run_state("r-disp", user_disposition=UserDisposition.CONFIRMED, actor="not-a-user")
    store.update_run_state("r-disp", user_disposition=UserDisposition.CONFIRMED,
                           actor=getpass.getuser())
    assert store.get_run("r-disp").user_disposition == UserDisposition.CONFIRMED


def test_complete_analysis_gate_fail_closed(r1_store):
    run_id = frozen_run(r1_store, "P-GATE", run_id="r-gate")
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING)
    # evidence incomplete -> gate refuses, states untouched
    with pytest.raises(CompletionGateError):
        store.complete_analysis(run_id)
    run = store.get_run(run_id)
    assert run.analysis_state == AnalysisState.RUNNING
    assert run.output_state == OutputState.NOT_PUBLISHED
    # mandatory node still missing -> still refused
    store.update_run_state(run_id, evidence=EvidenceState.COMPLETE)
    with pytest.raises(CompletionGateError):
        store.complete_analysis(run_id)
    # failing the mandatory node -> refused
    run_node(store, run_id, status=NodeStatus.FAILED, error="boom")
    with pytest.raises(CompletionGateError):
        store.complete_analysis(run_id)
    assert store.get_run(run_id).analysis_state == AnalysisState.RUNNING


def test_complete_analysis_success_publishes_dashboard(r1_store):
    run_id = frozen_run(r1_store, "P-OK", run_id="r-ok")
    store = r1_store
    run_node(store, run_id, envelope=make_env(run_id, "n1"))
    run = complete_run(store, run_id)
    assert run.analysis_state == AnalysisState.COMPLETE
    assert run.output_state == OutputState.DASHBOARD_VISIBLE
    # idempotent: re-calling does not change anything
    again = store.complete_analysis(run_id)
    assert again.updated_at == run.updated_at


def test_publish_gates_and_export(r1_store):
    run_id = frozen_run(r1_store, "P-PUB", run_id="r-pub")
    store = r1_store
    run_node(store, run_id, envelope=make_env(run_id, "n1"))
    complete_run(store, run_id)
    store.publish(run_id, OutputState.DRAFT_EXPORTABLE)
    with pytest.raises(CompletionGateError):
        store.publish(run_id, OutputState.EXPORTED)  # actor missing
    store.publish(run_id, OutputState.EXPORTED, actor=getpass.getuser())
    run = store.get_run(run_id)
    assert run.output_state == OutputState.EXPORTED
    assert run.user_disposition == UserDisposition.EXPORTED


def test_update_run_state_cannot_export_even_with_valid_actor(r1_store):
    """publish() is the only EXPORTED route; update_run_state must fail closed."""
    run_id = frozen_run(r1_store, "P-NO-EXPORT-URS", run_id="r-no-export-urs")
    store = r1_store
    run_node(store, run_id, envelope=make_env(run_id, "n1"))
    complete_run(store, run_id)
    store.publish(run_id, OutputState.DRAFT_EXPORTABLE)
    before = store.get_run(run_id)
    with pytest.raises(StoreError, match="only allowed via Store.publish"):
        store.update_run_state(
            run_id,
            output=OutputState.EXPORTED,
            actor="arbitrary-forged-actor",
        )
    with pytest.raises(StoreError, match="only allowed via Store.publish"):
        store.update_run_state(
            run_id,
            output=OutputState.EXPORTED,
            actor=getpass.getuser(),
        )
    after = store.get_run(run_id)
    assert after.output_state == OutputState.DRAFT_EXPORTABLE
    assert after.user_disposition is None
    assert after.output_state == before.output_state
    published = store.publish(run_id, OutputState.EXPORTED, actor=getpass.getuser())
    assert published.output_state == OutputState.EXPORTED
    assert published.user_disposition == UserDisposition.EXPORTED


# ---------------------------------------------------------------------------
# snapshot acceptance chain
# ---------------------------------------------------------------------------

def test_acceptance_chain_to_baseline_eligible(r1_store):
    make_project(r1_store, "P-ACC")
    make_revision(r1_store, "P-ACC")
    make_snapshot(r1_store, "P-ACC", "snap-acc")
    accept_chain(r1_store, "snap-acc")
    acc = r1_store.get_acceptance("snap-acc")
    assert acc.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
    assert acc.accepted_by == "system_policy"


def test_acceptance_jump_and_rewind_rejected(r1_store):
    make_project(r1_store, "P-JUMP")
    make_revision(r1_store, "P-JUMP")
    make_snapshot(r1_store, "P-JUMP", "snap-jump")
    store = r1_store
    with pytest.raises(AcceptanceChainError):
        store.transition_snapshot_acceptance("snap-jump", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                                             accepted_by="system_policy")
    store.transition_snapshot_acceptance("snap-jump", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                                         accepted_by="system_policy")
    with pytest.raises(AcceptanceChainError):
        store.transition_snapshot_acceptance("snap-jump", SnapshotAcceptanceState.IMPORTED)


def test_ambiguity_blocks_acceptance_fail_closed(r1_store):
    make_project(r1_store, "P-AMB")
    make_revision(r1_store, "P-AMB")
    make_snapshot(r1_store, "P-AMB", "snap-amb")
    store = r1_store
    store.transition_snapshot_acceptance("snap-amb", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                                         accepted_by="system_policy")
    store.transition_snapshot_acceptance("snap-amb", SnapshotAcceptanceState.MAPPING_REVIEWED,
                                         accepted_by="system_policy")
    store.set_acceptance_ambiguity("snap-amb", {"identity": "subject S003 maps to two records"})
    with pytest.raises(AmbiguityBlocksAcceptanceError):
        store.transition_snapshot_acceptance("snap-amb", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                                             accepted_by="system_policy")
    acc = store.get_acceptance("snap-amb")
    assert acc.blocked and acc.state == SnapshotAcceptanceState.MAPPING_REVIEWED
    # after clear, acceptance proceeds
    store.clear_acceptance_ambiguity("snap-amb", accepted_by="system_policy")
    store.transition_snapshot_acceptance("snap-amb", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                                         accepted_by="system_policy")
    assert store.get_acceptance("snap-amb").state == SnapshotAcceptanceState.SNAPSHOT_ACCEPTED


def test_accepted_by_validation(r1_store):
    make_project(r1_store, "P-SUBJ")
    make_revision(r1_store, "P-SUBJ")
    make_snapshot(r1_store, "P-SUBJ", "snap-subj")
    store = r1_store
    st = SnapshotAcceptanceState
    store.transition_snapshot_acceptance("snap-subj", st.STRUCTURALLY_VALID, accepted_by="system_policy")
    store.transition_snapshot_acceptance("snap-subj", st.MAPPING_REVIEWED, accepted_by="system_policy")
    with pytest.raises(StoreError):
        store.transition_snapshot_acceptance("snap-subj", st.SNAPSHOT_ACCEPTED, accepted_by=None)
    with pytest.raises(StoreError):
        store.transition_snapshot_acceptance("snap-subj", st.SNAPSHOT_ACCEPTED, accepted_by="someone-else")
    store.transition_snapshot_acceptance("snap-subj", st.SNAPSHOT_ACCEPTED, accepted_by=getpass.getuser())
    assert store.get_acceptance("snap-subj").accepted_by == getpass.getuser()


def test_snapshot_identity_distinct_from_blob_dedupe(r1_store):
    """Snapshot identity is the snapshot_id; identical bytes may share one
    content-addressed blob but never collapse two snapshots into one."""
    pid = "P-SNAP"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    store = r1_store
    rows = {"ae": [{"subject_id": "S001", "term": "Headache", "onset": "2026-01-10"}]}
    s1 = store.add_listing_snapshot(
        ListingSnapshot(snapshot_id="snap-N", project_id=pid, revision_id="rev-1",
                        snapshot_version="N", is_synthetic=True), rows)
    s2 = store.add_listing_snapshot(
        ListingSnapshot(snapshot_id="snap-N+1", project_id=pid, revision_id="rev-1",
                        snapshot_version="N+1", is_synthetic=True), rows)
    # distinct N/N+1 identities with byte-identical content
    assert s1.snapshot_id == "snap-N" and s2.snapshot_id == "snap-N+1"
    assert s1.content_hash == s2.content_hash
    assert store.get_listing_snapshot("snap-N").snapshot_id == "snap-N"
    assert store.get_listing_snapshot("snap-N+1").snapshot_id == "snap-N+1"
    # one blob on disk for both snapshots
    assert (store.artifact_dir / f"{s1.content_hash}.json").exists()
    assert store.load_listing_content("snap-N") == store.load_listing_content("snap-N+1")
    # separate acceptance records, each independently accepted to baseline
    accept_chain(store, "snap-N")
    accept_chain(store, "snap-N+1")
    assert store.get_acceptance("snap-N").state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
    assert store.get_acceptance("snap-N+1").state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
    # replay: same id + same content/metadata -> existing snapshot, no new row
    s1_again = store.add_listing_snapshot(
        ListingSnapshot(snapshot_id="snap-N", project_id=pid, revision_id="rev-1",
                        snapshot_version="N", is_synthetic=True), rows)
    assert s1_again.snapshot_id == "snap-N" and s1_again.content_hash == s1.content_hash
    # conflict: same id + different content -> error, never silent collapse
    with pytest.raises(IdempotencyConflictError):
        store.add_listing_snapshot(
            ListingSnapshot(snapshot_id="snap-N", project_id=pid, revision_id="rev-1",
                            snapshot_version="N", is_synthetic=True),
            {"ae": [{"subject_id": "S002"}]})
    # conflict: same id + different metadata (version) -> error
    with pytest.raises(IdempotencyConflictError):
        store.add_listing_snapshot(
            ListingSnapshot(snapshot_id="snap-N", project_id=pid, revision_id="rev-1",
                            snapshot_version="N+9", is_synthetic=True), rows)
    # non-synthetic rejected (POC guard)
    with pytest.raises(StoreError):
        store.add_listing_snapshot(
            ListingSnapshot(snapshot_id="snap-bad", project_id=pid, revision_id="rev-1",
                            snapshot_version="N", is_synthetic=False),
            {"ae": []},
        )


# ---------------------------------------------------------------------------
# artifact coverage / publication gate
# ---------------------------------------------------------------------------

def test_envelope_publishable_when_complete():
    env = make_env("r", "n")
    ok, reasons = env.is_publishable()
    assert ok and not reasons


@pytest.mark.parametrize("completeness", [
    ArtifactCompleteness.PARTIAL,
    ArtifactCompleteness.TRUNCATED,
    ArtifactCompleteness.NOT_EVALUABLE,
    ArtifactCompleteness.FAILED,
])
def test_incomplete_envelopes_never_publishable(completeness):
    env = make_env("r", "n", completeness=completeness)
    ok, reasons = env.is_publishable()
    assert not ok and reasons


def test_missing_expected_unit_blocks_publication():
    env = ArtifactEnvelope(
        artifact_type="analysis", version="1", run_id="r", node_id="n",
        node_type=NodeType.DETERMINISTIC_SERVICE, payload={},
        coverage=CoverageManifest(
            expected=[CoverageUnit(scope=domain.SCOPE_SITE, key="SITE-01"),
                      CoverageUnit(scope=domain.SCOPE_SITE, key="SITE-02")],
            produced=[CoverageUnit(scope=domain.SCOPE_SITE, key="SITE-01",
                                   status=CoverageUnitStatus.COVERED)],
        ).reconcile(),
    )
    assert env.derive_completeness() == ArtifactCompleteness.PARTIAL
    ok, reasons = env.is_publishable()
    assert not ok
    assert any("SITE-02" in r for r in reasons)


def test_not_applicable_requires_reason():
    na_ok = ArtifactEnvelope(
        artifact_type="t", version="1", run_id="r", node_id="n",
        node_type=NodeType.DETERMINISTIC_SERVICE, payload={},
        coverage=CoverageManifest(
            expected=[CoverageUnit(scope=domain.SCOPE_RISK_DOMAIN, key="cm_ip",
                                   status=CoverageUnitStatus.NOT_APPLICABLE,
                                   reason="not in R1 scope")],
            produced=[],
        ).reconcile(),
    )
    ok, _ = na_ok.is_publishable()
    assert ok
    na_bad = ArtifactEnvelope(
        artifact_type="t", version="1", run_id="r", node_id="n",
        node_type=NodeType.DETERMINISTIC_SERVICE, payload={},
        coverage=CoverageManifest(
            expected=[CoverageUnit(scope=domain.SCOPE_RISK_DOMAIN, key="cm_ip",
                                   status=CoverageUnitStatus.NOT_EVALUABLE, reason=None)],
            produced=[],
        ).reconcile(),
    )
    ok, reasons = na_bad.is_publishable()
    assert not ok and any("without reason" in r for r in reasons)


def test_content_addressing_and_immutability(r1_store):
    pid = "P-CA"
    run_id = frozen_run(r1_store, pid, "r-ca", nodes=["n1"])
    store = r1_store
    env = make_env(run_id, "n1", payload={"x": 1})
    node = run_node(store, run_id, node_id="n1", key="k1", envelope=env)
    aid = node.artifact_id
    # re-staging the same content yields the same address and no new row
    staged = store.stage_artifact(env)
    assert staged == aid
    committed = store.commit_artifact(staged, env)
    assert committed.artifact_id == aid
    assert len(store.list_artifacts(run_id)) == 1
    # tampering with the file is detected
    path = store.artifact_dir / f"{aid}.json"
    path.write_text(path.read_text("utf-8").replace('"x":1', '"x":2'), "utf-8")
    assert store.verify_artifact(aid) is False
    # different content -> different address (fresh node)
    env2 = make_env(run_id, "n2", payload={"x": 2})
    node2 = run_node(store, run_id, node_id="n2", key="k2", envelope=env2)
    assert node2.artifact_id != aid


def test_derive_completeness_deterministic():
    assert make_env("r", "n").derive_completeness() == ArtifactCompleteness.COMPLETE
    trunc = make_env("r", "n")
    trunc.coverage.expected = [
        CoverageUnit(scope=u.scope, key=u.key, expected=u.expected,
                     status=CoverageUnitStatus.TRUNCATED, reason=u.reason)
        for u in trunc.coverage.expected
    ]
    assert trunc.derive_completeness() == ArtifactCompleteness.TRUNCATED


# ---------------------------------------------------------------------------
# graph IR + ports
# ---------------------------------------------------------------------------

def test_node_types_fixed():
    assert [t.value for t in NODE_TYPES] == [
        "deterministic_service", "ai_candidate", "human_decision", "projection",
    ]
    with pytest.raises(ValueError):
        NodeType("free_agent")


def test_graph_validation_cycle_and_missing_edge():
    g = Graph(graph_id="g1")
    g.add_node(GraphNode("a", NodeType.DETERMINISTIC_SERVICE))
    g.add_node(GraphNode("b", NodeType.DETERMINISTIC_SERVICE))
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    with pytest.raises(Exception) as ei:
        g.validate()
    assert "cycle" in str(ei.value)
    g2 = Graph(graph_id="g2")
    g2.add_node(GraphNode("a", NodeType.DETERMINISTIC_SERVICE))
    g2.add_edge("missing", "a")
    with pytest.raises(Exception):
        g2.validate()


def test_topological_order_and_conditional_edge():
    g = Graph(graph_id="g3")
    g.add_node(GraphNode("a", NodeType.DETERMINISTIC_SERVICE))
    g.add_node(GraphNode("b", NodeType.AI_CANDIDATE))
    g.add_node(GraphNode("c", NodeType.PROJECTION))
    g.add_edge("a", "b")
    g.add_edge("b", "c", condition="full_run")
    order = g.topological_order()
    assert order.index("a") < order.index("b") < order.index("c")


def _silent_handler(payload=None, role=domain.PAYLOAD_ROLE_INFERENCE, keys=("S001",),
                    output=None, status=NodeStatus.PASSED):
    def handler(ctx: NodeContext) -> NodeOutcome:
        env = ArtifactEnvelope(
            artifact_type="analysis", version="1", run_id=ctx.run_id, node_id=ctx.node_id,
            node_type=ctx.node_type, payload=dict(payload or {"node": ctx.node_id}),
            payload_role=role, coverage=full_coverage(keys),
        )
        return NodeOutcome(status=status, artifact=env,
                           output=dict(output or {"ran": ctx.node_id}))
    return handler


def _qc_handler(ctx: NodeContext) -> NodeOutcome:
    """Deterministic QC node: declares evidence complete (needed for the
    analysis_complete gate)."""
    ctx.store.update_run_state(ctx.run_id, evidence=EvidenceState.COMPLETE,
                               reason="qc passed")
    return NodeOutcome(status=NodeStatus.PASSED, output={"qc": "passed"})


def test_local_graph_port_run_persists(r1_store):
    pid = "P-GRAPH"
    run_id = frozen_run(r1_store, pid, "r-graph", nodes=["ingest", "analyze", "project", "qc"])
    store = r1_store
    graph = Graph(graph_id="g-run")
    graph.add_node(GraphNode("ingest", NodeType.DETERMINISTIC_SERVICE, handler="h"))
    graph.add_node(GraphNode("analyze", NodeType.AI_CANDIDATE, handler="h"))
    graph.add_node(GraphNode("project", NodeType.PROJECTION, handler="h"))
    graph.add_node(GraphNode("qc", NodeType.DETERMINISTIC_SERVICE, handler="qc",
                             artifact_required=False))  # state-only QC node
    graph.add_edge("ingest", "analyze")
    graph.add_edge("analyze", "project")
    graph.add_edge("project", "qc")
    port = LocalGraphPort(store, {"h": _silent_handler(), "qc": _qc_handler})
    # freeze the manifest from the graph (replaces the generic one)
    store.set_manifest(graph.to_manifest(run_id, identity_algorithm="identity-v1",
                                         graph_version="graph-v1", schema_version="schema-v1"))
    result = port.run(graph, run_id)
    assert result.status == "complete"
    assert [r.status for r in result.node_results] == [NodeStatus.PASSED] * 4
    # ingest/analyze/project carry artifacts; qc is a state-only node
    assert sum(1 for nr in result.node_results if nr.artifact_id) == 3
    run = store.get_run(run_id)
    assert run.analysis_state == AnalysisState.COMPLETE
    assert run.output_state == OutputState.DASHBOARD_VISIBLE
    assert store.manifest_progress(run_id)["completed"] == 4
    assert result.context["ran"] == "project"


def test_resume_reuses_committed_nodes(r1_store):
    pid = "P-RESUME"
    run_id = frozen_run(r1_store, pid, "r-resume", nodes=["n1", "n2", "qc"])
    store = r1_store
    calls = {"count": 0}

    def counting(ctx):
        calls["count"] += 1
        return _silent_handler()(ctx)

    graph = Graph(graph_id="g-resume")
    graph.add_node(GraphNode("n1", NodeType.DETERMINISTIC_SERVICE, handler="h"))
    graph.add_node(GraphNode("n2", NodeType.DETERMINISTIC_SERVICE, handler="h"))
    graph.add_node(GraphNode("qc", NodeType.DETERMINISTIC_SERVICE, handler="qc",
                             artifact_required=False))  # state-only QC node
    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "qc")
    port = LocalGraphPort(store, {"h": counting, "qc": _qc_handler})
    store.set_manifest(graph.to_manifest(run_id, identity_algorithm="identity-v1",
                                         graph_version="graph-v1", schema_version="schema-v1"))
    first = port.run(graph, run_id)
    assert first.status == "complete" and calls["count"] == 2
    # resume = replay over committed state: handlers not re-invoked
    calls["count"] = 0
    resumed = port.resume(run_id)
    assert resumed.status == "complete"
    assert all(r.reused for r in resumed.node_results)
    assert calls["count"] == 0
    assert len(store.list_artifacts(run_id)) == 2  # n1+n2; qc is state-only, no duplicate side effects


def test_replay_is_idempotent(r1_store):
    pid = "P-REPLAY"
    run_id = frozen_run(r1_store, pid, "r-replay", nodes=["n1", "qc"])
    store = r1_store
    graph = Graph(graph_id="g-replay")
    graph.add_node(GraphNode("n1", NodeType.DETERMINISTIC_SERVICE, handler="h"))
    graph.add_node(GraphNode("qc", NodeType.DETERMINISTIC_SERVICE, handler="qc",
                             artifact_required=False))  # state-only QC node
    graph.add_edge("n1", "qc")
    port = LocalGraphPort(store, {"h": _silent_handler(), "qc": _qc_handler})
    store.set_manifest(graph.to_manifest(run_id, identity_algorithm="identity-v1",
                                         graph_version="graph-v1", schema_version="schema-v1"))
    port.run(graph, run_id)
    replayed = port.replay(run_id)
    assert all(r.reused for r in replayed.node_results)
    assert len(store.list_artifacts(run_id)) == 1


def test_retry_after_handler_failure(r1_store):
    pid = "P-RETRY"
    run_id = frozen_run(r1_store, pid, "r-retry", nodes=["n1", "qc"])
    store = r1_store
    state = {"fails": 1}
    node = GraphNode("n1", NodeType.DETERMINISTIC_SERVICE, handler="h", max_attempts=3)

    def flaky(ctx):
        if state["fails"] > 0:
            state["fails"] -= 1
            raise RuntimeError("transient failure")
        return _silent_handler()(ctx)

    graph = Graph(graph_id="g-retry")
    graph.add_node(node)
    graph.add_node(GraphNode("qc", NodeType.DETERMINISTIC_SERVICE, handler="qc",
                             artifact_required=False))  # state-only QC node
    graph.add_edge("n1", "qc")
    port = LocalGraphPort(store, {"h": flaky, "qc": _qc_handler})
    store.set_manifest(graph.to_manifest(run_id, identity_algorithm="identity-v1",
                                         graph_version="graph-v1", schema_version="schema-v1"))
    result = port.run(graph, run_id)
    assert result.status == "complete"
    nr = store.get_node_run(run_id, "n1")
    assert nr.status == NodeStatus.PASSED and nr.attempts == 2


def test_checkpoint_port(r1_store):
    pid = "P-CP"
    run_id = frozen_run(r1_store, pid, "r-cp", nodes=["n1"])
    store = r1_store
    cp = store.save_checkpoint(run_id, "n1", {"phase": "mapping", "seen": 3})
    assert cp.content_hash
    loaded = store.load_checkpoint(run_id, "n1")
    assert loaded.state == {"phase": "mapping", "seen": 3}
    assert len(store.list_checkpoints(run_id)) == 1
    # same content -> dedupe
    store.save_checkpoint(run_id, "n1", {"phase": "mapping", "seen": 3})
    assert len(store.list_checkpoints(run_id)) == 1
    # different content -> additional checkpoint
    store.save_checkpoint(run_id, "n1", {"phase": "mapping", "seen": 4})
    assert len(store.list_checkpoints(run_id)) == 2


# ---------------------------------------------------------------------------
# store atomicity / idempotency / audit / recovery
# ---------------------------------------------------------------------------

def test_duplicate_commit_no_duplicate_side_effects(r1_store):
    pid = "P-DUP"
    run_id = frozen_run(r1_store, pid, "r-dup", nodes=["n1"])
    store = r1_store
    env = make_env(run_id, "n1")
    first = run_node(store, run_id, key="dup-key", envelope=env, payload_hash="h1")
    second = run_node(store, run_id, key="dup-key", envelope=env, payload_hash="h1")
    assert first.artifact_id == second.artifact_id
    assert store.get_node_run(run_id, "n1").attempts == 1
    assert len(store.list_artifacts(run_id)) == 1
    events = [e.event_type for e in store.audit_trail()]
    assert events.count(domain.EVENT_NODE_COMPLETE) == 1
    assert domain.EVENT_IDEMPOTENT_REPLAY in events


def test_same_key_different_outcome_conflict_without_caller_hash(r1_store):
    """Outcome fingerprint is derived inside the Store (status + envelope +
    output + error/reason); a conflicting same-key callback is rejected BEFORE
    any artifact staging, with no caller-supplied payload hash needed."""
    pid = "P-CONF"
    run_id = frozen_run(r1_store, pid, "r-conf", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k", envelope=make_env(run_id, "n1"))
    with pytest.raises(IdempotencyConflictError):
        store.complete_node_run(run_id, "n1", "k", NodeStatus.PASSED,
                                envelope=make_env(run_id, "n1", payload={"other": 1}))
    assert store.get_node_run(run_id, "n1").status == NodeStatus.PASSED  # history intact
    assert not store.find_orphan_artifacts()          # nothing was staged
    conflicts = [e for e in store.audit_trail()
                 if e.event_type == domain.EVENT_IDEMPOTENCY_CONFLICT]
    assert len(conflicts) == 1
    # duplicate identical callback stays side-effect free
    replay = store.complete_node_run(run_id, "n1", "k", NodeStatus.PASSED,
                                     envelope=make_env(run_id, "n1"))
    assert replay.artifact_id == store.get_node_run(run_id, "n1").artifact_id
    assert len(store.list_artifacts(run_id)) == 1


def test_late_callback_rejected_and_audited(r1_store):
    pid = "P-LATE"
    run_id = frozen_run(r1_store, pid, "r-late", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k1", envelope=make_env(run_id, "n1"))
    # a callback with a key that is not the open attempt must be rejected
    with pytest.raises(StaleCallbackError):
        store.complete_node_run(run_id, "n1", "k2", NodeStatus.PASSED,
                                envelope=make_env(run_id, "n1"))
    node = store.get_node_run(run_id, "n1")
    assert node.status == NodeStatus.PASSED and node.artifact_id  # not overwritten
    assert not store.find_orphan_artifacts()   # stale callback staged nothing
    rejected = [e for e in store.audit_trail() if e.event_type == domain.EVENT_NODE_REJECTED]
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "stale_callback"


def test_begin_after_terminal_requires_revision(r1_store):
    pid = "P-TERM"
    run_id = frozen_run(r1_store, pid, "r-term", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k1", envelope=make_env(run_id, "n1"))
    with pytest.raises(NodeTerminalError):
        store.begin_node_run(run_id, "n1", NodeType.DETERMINISTIC_SERVICE, "k-other")


def test_no_published_state_before_commit(r1_store):
    pid = "P-ATOM"
    run_id = frozen_run(r1_store, pid, "r-atom", nodes=["n1"])
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING)
    env = make_env(run_id, "n1")
    staged = store.stage_artifact(env)          # file written, no txn
    assert store.get_run(run_id).output_state == OutputState.NOT_PUBLISHED
    with pytest.raises(StoreError):
        store.get_artifact(staged)               # not authoritative
    report = store.recover()
    assert staged + ".json" in report.orphan_artifacts
    # commit then complete: only now does the pointer advance
    store.commit_artifact(staged, env)
    run_node(store, run_id, key="k1", envelope=env)
    complete_run(store, run_id)
    assert store.get_run(run_id).output_state == OutputState.DASHBOARD_VISIBLE
    assert not store.find_orphan_artifacts()


def test_orphan_cleanup_is_audited_and_never_authoritative(r1_store, tmp_path):
    pid = "P-ORPH"
    run_id = frozen_run(r1_store, pid, "r-orph", nodes=["n1"])
    store = r1_store
    staged = store.stage_artifact(make_env(run_id, "n1"))
    store.stage_artifact(make_env(run_id, "n1", payload={"second": True}))
    quarantine = tmp_path / "quarantine"
    moved = store.cleanup_orphan_artifacts(quarantine)
    assert len(moved) == 2
    assert not store.find_orphan_artifacts()
    assert len(list(quarantine.glob("*.json"))) == 2
    events = [e for e in store.audit_trail() if e.event_type == domain.EVENT_ORPHAN_CLEANUP]
    assert len(events) == 2
    with pytest.raises(StoreError):
        store.get_artifact(staged)


def test_audit_chain_verify_and_tamper_detection(r1_store):
    pid = "P-AUDIT"
    run_id = frozen_run(r1_store, pid, "r-audit", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k1", envelope=make_env(run_id, "n1"))
    ok, first_bad, count = store.verify_audit_chain()
    assert ok and first_bad is None and count >= 6
    before = store.audit_trail()
    # tamper: rewrite an audit payload via direct SQL (chain commits to the
    # payload hash, so content tampering must be detected)
    conn = sqlite3.connect(str(store.db_path))
    conn.execute("UPDATE audit_events SET payload_json='{\"tampered\":true}' WHERE seq=1")
    conn.commit()
    conn.close()
    ok, first_bad, count = store.verify_audit_chain()
    assert not ok and first_bad == 1
    # restore payload, then delete a row -> gap detection (row seq 3 sits at position 2)
    conn = sqlite3.connect(str(store.db_path))
    conn.execute("UPDATE audit_events SET payload_json=? WHERE seq=1",
                 (canonical_json(before[0].payload),))
    conn.execute("DELETE FROM audit_events WHERE seq=2")
    conn.commit()
    conn.close()
    ok, first_bad, _ = store.verify_audit_chain()
    assert not ok and first_bad == 3


def test_manifest_revision_idempotent_and_append(r1_store):
    pid = "P-MAN"
    run_id = frozen_run(r1_store, pid, "r-man", nodes=["n1"])
    store = r1_store
    assert store.list_manifest_revisions(run_id) == [1]  # frozen by helper
    rev1 = store.set_manifest(ExecutionManifest(
        run_id=run_id, nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE)],
        identity_algorithm="identity-v1", graph_version="graph-v1", schema_version="schema-v1"))
    rev1_again = store.set_manifest(ExecutionManifest(
        run_id=run_id, nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE)],
        identity_algorithm="identity-v1", graph_version="graph-v1", schema_version="schema-v1"))
    assert rev1 == rev1_again == 2                       # idempotent by content
    rev2 = store.set_manifest(ExecutionManifest(
        run_id=run_id, nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE),
                               ManifestNode("n2", NodeType.PROJECTION)],
        identity_algorithm="identity-v1", graph_version="graph-v1", schema_version="schema-v1"))
    assert rev2 == 3                                     # append-only revision
    assert store.list_manifest_revisions(run_id) == [1, 2, 3]
    assert store.get_run(run_id).manifest_revision == 3
    with pytest.raises(StoreError):
        store.set_manifest(ExecutionManifest(run_id=run_id, nodes=[
            ManifestNode("dup", NodeType.DETERMINISTIC_SERVICE),
            ManifestNode("dup", NodeType.DETERMINISTIC_SERVICE)]))


def test_fact_promotion_gate(r1_store):
    pid = "P-FACT"
    run_id = frozen_run(r1_store, pid, "r-fact", nodes=["ai", "det"])
    store = r1_store
    store.begin_node_run(run_id, "ai", NodeType.AI_CANDIDATE, "k-ai")
    facts = [CanonicalFact(fact_type="ae_record", body={"term": "Headache"}, subject_id="S001")]
    with pytest.raises(PromotionForbiddenError):
        store.commit_facts(run_id, "ai", "k-ai", facts)
    store.begin_node_run(run_id, "det", NodeType.DETERMINISTIC_SERVICE, "k-det")
    n = store.commit_facts(run_id, "det", "k-det", facts)
    assert n == 1
    n_again = store.commit_facts(run_id, "det", "k-det", facts)  # idempotent
    assert n_again == 1
    assert len(store.list_facts(run_id)) == 1


def test_domain_object_versioning(r1_store):
    pid = "P-DOBJ"
    run_id = frozen_run(r1_store, pid, "r-dobj", nodes=["n1"])
    store = r1_store
    v1 = store.put_domain_object("risk_instance", "ri-1",
                                 {"identity_key": "k", "lifecycle": RiskLifecycleState.ESTABLISHED.value},
                                 run_id=run_id)
    v1_again = store.put_domain_object("risk_instance", "ri-1",
                                       {"identity_key": "k", "lifecycle": RiskLifecycleState.ESTABLISHED.value},
                                       run_id=run_id)
    assert v1 == v1_again == 1
    v2 = store.put_domain_object("risk_instance", "ri-1",
                                 {"identity_key": "k", "lifecycle": RiskLifecycleState.CLOSED.value},
                                 run_id=run_id)
    assert v2 == 2
    version, obj = store.get_domain_object("risk_instance", "ri-1")
    assert version == 2 and obj["lifecycle"] == RiskLifecycleState.CLOSED.value
    _, old = store.get_domain_object("risk_instance", "ri-1", version=1)
    assert old["lifecycle"] == RiskLifecycleState.ESTABLISHED.value  # history intact


def test_recovery_reports_incomplete_runs(r1_store):
    pid = "P-REC"
    run_id = frozen_run(r1_store, pid, "r-rec", nodes=["n1", "n2"])
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING)
    run_node(store, run_id, node_id="n1", key="k1", envelope=make_env(run_id, "n1"))
    # simulate crash: n2 opened but never completed
    store.begin_node_run(run_id, "n2", NodeType.DETERMINISTIC_SERVICE, "k2")
    report = store.recover()
    assert report.audit_ok
    assert report.integrity_violations == []
    assert not report.orphan_artifacts
    assert any(rs.run_id == run_id and rs.open_attempts == 1 for rs in report.incomplete_runs)
    assert store.get_run(run_id).analysis_state == AnalysisState.RUNNING  # never auto-completed
    # resume completes it
    store.complete_node_run(run_id, "n2", "k2", NodeStatus.PASSED, envelope=make_env(run_id, "n2"))
    store.update_run_state(run_id, evidence=EvidenceState.COMPLETE)
    store.complete_analysis(run_id)
    assert store.get_run(run_id).analysis_state == AnalysisState.COMPLETE


def test_audit_append_only_and_events_cover_actions(r1_store):
    pid = "P-EVENTS"
    run_id = frozen_run(r1_store, pid, "r-events", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k1", envelope=make_env(run_id, "n1"))
    run = complete_run(store, run_id)
    types = [e.event_type for e in store.audit_trail()]
    for expected in (domain.EVENT_PROJECT_CREATED, domain.EVENT_SNAPSHOT_ADDED,
                     domain.EVENT_RUN_CREATED, domain.EVENT_MANIFEST_SET,
                     domain.EVENT_NODE_BEGIN, domain.EVENT_ARTIFACT_COMMITTED,
                     domain.EVENT_NODE_COMPLETE, domain.EVENT_PUBLISH_ADVANCED):
        assert expected in types
    assert run.output_state == OutputState.DASHBOARD_VISIBLE


def test_json_roundtrip_of_domain_objects():
    from mm_r1.domain import from_jsonable, to_jsonable
    env = make_env("r", "n", completeness=ArtifactCompleteness.TRUNCATED)
    restored = from_jsonable(ArtifactEnvelope, to_jsonable(env))
    assert restored.canonical_hash() == env.canonical_hash()
    assert restored.completeness == ArtifactCompleteness.TRUNCATED
    assert restored.coverage.reconciled
    run = MonitoringRun(run_id="r", project_id="p", mode=RunMode.PRE_LOCK, data_cutoff="2026-02-01",
                        source_revision_id="rev-1", execution_basis=ExecutionBasis.INCREMENTAL)
    assert from_jsonable(MonitoringRun, to_jsonable(run)) == run
    # manifest round-trips the frozen graph IR (graph_id, conditional edges,
    # retry/artifact policy)
    man = ExecutionManifest(run_id="r", graph_id="g-x", nodes=[
        ManifestNode("a", NodeType.DETERMINISTIC_SERVICE, max_attempts=3),
        ManifestNode("qc", NodeType.DETERMINISTIC_SERVICE, artifact_required=False)],
        edges=[{"src": "a", "dst": "qc", "condition": "full_run"}])
    restored_man = from_jsonable(ExecutionManifest, to_jsonable(man))
    assert restored_man.graph_id == "g-x"
    assert restored_man.edges == [{"src": "a", "dst": "qc", "condition": "full_run"}]
    assert restored_man.nodes[0].max_attempts == 3
    assert restored_man.nodes[1].artifact_required is False


# ---------------------------------------------------------------------------
# follow-up regression tests: fail-closed publication, snapshot identity,
# frozen-graph recovery, callback idempotency, immutable retries, generic
# idempotency conflicts, recovery/durability, provenance, serialization
# ---------------------------------------------------------------------------

def test_gate_blocks_node_without_artifact_even_with_manual_evidence(r1_store):
    """A manual evidence_state=complete change can never bypass the gate: a
    mandatory node that passed without an artifact (manifest default requires
    one) blocks analysis_complete."""
    run_id = frozen_run(r1_store, "P-GATENA", run_id="r-gatena")
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING,
                           evidence=EvidenceState.COMPLETE)
    run_node(store, run_id, status=NodeStatus.PASSED)  # no artifact
    with pytest.raises(CompletionGateError) as ei:
        store.complete_analysis(run_id)
    assert any("produced no artifact" in r for r in ei.value.reasons)
    run = store.get_run(run_id)
    assert run.analysis_state == AnalysisState.RUNNING
    assert run.output_state == OutputState.NOT_PUBLISHED


def test_gate_blocks_partial_artifact_even_with_manual_evidence(r1_store):
    run_id = frozen_run(r1_store, "P-GATEP", run_id="r-gatep")
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING,
                           evidence=EvidenceState.COMPLETE)
    run_node(store, run_id, envelope=make_env(run_id, "n1",
                                              completeness=ArtifactCompleteness.PARTIAL))
    with pytest.raises(CompletionGateError) as ei:
        store.complete_analysis(run_id)
    assert any("not publishable" in r for r in ei.value.reasons)
    assert store.get_run(run_id).output_state == OutputState.NOT_PUBLISHED
    # the manual state-transition shortcut is gated the same way
    with pytest.raises(CompletionGateError):
        store.update_run_state(run_id, analysis=AnalysisState.COMPLETE)
    assert store.get_run(run_id).analysis_state == AnalysisState.RUNNING
    # ... and publishing is impossible without the gate
    with pytest.raises(CompletionGateError):
        store.publish(run_id, OutputState.DASHBOARD_VISIBLE)


def test_gate_blocks_corrupt_artifact(r1_store):
    run_id = frozen_run(r1_store, "P-GATEC", run_id="r-gatec")
    store = r1_store
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING,
                           evidence=EvidenceState.COMPLETE)
    node = run_node(store, run_id, envelope=make_env(run_id, "n1"))
    path = store.artifact_dir / f"{node.artifact_id}.json"
    path.write_text(path.read_text("utf-8").replace('"note":"synthetic"', '"note":"tampered"'),
                    "utf-8")
    with pytest.raises(CompletionGateError) as ei:
        store.complete_analysis(run_id)
    assert any("integrity" in r for r in ei.value.reasons)
    assert store.get_run(run_id).analysis_state == AnalysisState.RUNNING


def test_state_only_node_explicit_opt_out_passes_gate(r1_store):
    """A mandatory state-only/QC node passes the gate without an artifact only
    when the frozen manifest declares artifact_required=False."""
    pid = "P-SONLY"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_snapshot(r1_store, pid)
    make_run(r1_store, pid, "r-sonly")
    store = r1_store
    store.set_manifest(ExecutionManifest(run_id="r-sonly", nodes=[
        ManifestNode("qc", NodeType.DETERMINISTIC_SERVICE, artifact_required=False)]))
    store.update_run_state("r-sonly", analysis=AnalysisState.RUNNING,
                           evidence=EvidenceState.COMPLETE)
    run_node(store, "r-sonly", node_id="qc", key="qc-key", status=NodeStatus.PASSED)
    run = store.complete_analysis("r-sonly")
    assert run.analysis_state == AnalysisState.COMPLETE
    assert run.output_state == OutputState.DASHBOARD_VISIBLE


def test_frozen_graph_resume_fidelity(r1_store):
    """A frozen conditional/retry graph resumes from a fresh port with the SAME
    graph id, idempotency keys and conditions: committed nodes are reused, the
    open node continues from its checkpoint, no duplicate artifacts."""
    pid = "P-FROZEN"
    run_id = "r-frozen"
    make_project(r1_store, pid)
    make_revision(r1_store, pid)
    make_snapshot(r1_store, pid)
    make_run(r1_store, pid, run_id)
    store = r1_store
    graph = Graph(graph_id="g-frozen")
    graph.add_node(GraphNode("config", NodeType.DETERMINISTIC_SERVICE, handler="cfg"))
    graph.add_node(GraphNode("ingest", NodeType.DETERMINISTIC_SERVICE, handler="h"))
    graph.add_node(GraphNode("analyze", NodeType.AI_CANDIDATE, handler="cp", max_attempts=2))
    graph.add_node(GraphNode("qc", NodeType.DETERMINISTIC_SERVICE, handler="qc",
                             artifact_required=False))
    graph.add_edge("config", "ingest")
    graph.add_edge("ingest", "analyze", condition="full_run")
    graph.add_edge("analyze", "qc")
    store.set_manifest(graph.to_manifest(run_id, identity_algorithm="identity-v1",
                                         graph_version="graph-v1", schema_version="schema-v1"))
    store.update_run_state(run_id, analysis=AnalysisState.RUNNING)

    def cfg(ctx):
        return NodeOutcome(status=NodeStatus.PASSED, output={"full_run": True})

    def cp(ctx):
        loaded = ctx.load_checkpoint()
        return NodeOutcome(status=NodeStatus.PASSED,
                           artifact=make_env(run_id, "analyze", node_type=NodeType.AI_CANDIDATE,
                                             payload={"phase": loaded.state.get("phase")
                                                      if loaded else "new"}),
                           output={"analysis": "done"})

    handlers = {"cfg": cfg, "h": _silent_handler(), "cp": cp, "qc": _qc_handler}
    key_cfg, key_ing, key_an = ("g:g-frozen:config:r1", "g:g-frozen:ingest:r1",
                                "g:g-frozen:analyze:r1")
    # partial run: config + ingest committed; analyze opened + checkpointed,
    # then "crash" before its completion callback.
    store.begin_node_run(run_id, "config", NodeType.DETERMINISTIC_SERVICE, key_cfg)
    store.complete_node_run(run_id, "config", key_cfg, NodeStatus.PASSED,
                            envelope=make_env(run_id, "config"), output={"full_run": True})
    store.begin_node_run(run_id, "ingest", NodeType.DETERMINISTIC_SERVICE, key_ing)
    store.complete_node_run(run_id, "ingest", key_ing, NodeStatus.PASSED,
                            envelope=make_env(run_id, "ingest"), output={"ran": "ingest"})
    store.begin_node_run(run_id, "analyze", NodeType.AI_CANDIDATE, key_an)
    store.save_checkpoint(run_id, "analyze", {"phase": "mapping", "seen": 3})

    # fresh process: new LocalGraphPort over the frozen manifest
    port2 = LocalGraphPort(store, handlers)
    resumed = port2.resume(run_id)
    assert resumed.status == "complete"
    by_id = {r.node_id: r for r in resumed.node_results}
    assert by_id["config"].reused and by_id["ingest"].reused
    assert not by_id["analyze"].reused and by_id["analyze"].status == NodeStatus.PASSED
    assert by_id["qc"].status == NodeStatus.PASSED
    # logical idempotency keys are stable across the crash
    assert store.get_node_run(run_id, "config").idempotency_key == key_cfg
    assert store.get_node_run(run_id, "ingest").idempotency_key == key_ing
    assert store.get_node_run(run_id, "analyze").idempotency_key == key_an
    # exactly one artifact per artifact node (no duplicate side effects)
    assert len(store.list_artifacts(run_id)) == 3
    # the open node continued from its checkpoint
    analyze_env = store.get_artifact(store.get_node_run(run_id, "analyze").artifact_id)
    assert analyze_env.payload["phase"] == "mapping"
    # manifest + restore round-trip the full IR
    man = store.get_manifest(run_id)
    assert man.graph_id == "g-frozen"
    assert man.edges == [{"src": "config", "dst": "ingest", "condition": None},
                         {"src": "ingest", "dst": "analyze", "condition": "full_run"},
                         {"src": "analyze", "dst": "qc", "condition": None}]
    restored = Graph.from_manifest(man)
    assert restored.graph_id == "g-frozen"
    assert restored.nodes["analyze"].max_attempts == 2
    assert restored.nodes["qc"].artifact_required is False
    cond = [e for e in restored.edges if e.src == "ingest" and e.dst == "analyze"][0]
    assert cond.condition == "full_run"
    # gate passed on resume: analysis complete + published
    assert store.get_run(run_id).analysis_state == AnalysisState.COMPLETE
    assert store.get_run(run_id).output_state == OutputState.DASHBOARD_VISIBLE


def test_retry_history_immutable(r1_store):
    """Each retry gets a NEW immutable attempt record; the prior terminal
    attempt is never mutated back to RUNNING."""
    pid = "P-HIST"
    run_id = frozen_run(r1_store, pid, "r-hist", nodes=["n1"])
    store = r1_store
    store.begin_node_run(run_id, "n1", NodeType.DETERMINISTIC_SERVICE, "hist-key")
    store.complete_node_run(run_id, "n1", "hist-key", NodeStatus.FAILED, error="boom")
    # reopen for retry with the SAME logical key
    store.begin_node_run(run_id, "n1", NodeType.DETERMINISTIC_SERVICE, "hist-key")
    store.complete_node_run(run_id, "n1", "hist-key", NodeStatus.PASSED,
                            envelope=make_env(run_id, "n1"))
    attempts = store.list_node_attempts(run_id, "n1")
    assert [a.attempt_seq for a in attempts] == [1, 2]
    assert attempts[0].status == NodeStatus.FAILED      # immutable, never reverted
    assert attempts[0].payload_hash                      # fingerprint recorded
    assert attempts[1].status == NodeStatus.PASSED
    assert attempts[1].idempotency_key != attempts[0].idempotency_key  # distinct keys
    assert attempts[0].logical_key == attempts[1].logical_key == "hist-key"
    node = store.get_node_run(run_id, "n1")
    assert node.status == NodeStatus.PASSED and node.attempts == 2


def test_idempotency_scope_and_request_conflict(r1_store):
    """Generic idempotency guards scope + request hash: same key/same request
    replays; same key with a different scope or request conflicts."""
    pid = "P-IDEM"
    run_id_a = frozen_run(r1_store, pid, "r-ida", nodes=["n1"])
    store = r1_store
    m_a = ExecutionManifest(run_id="r-ida",
                            nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE)],
                            identity_algorithm="identity-v1", graph_version="graph-v1",
                            schema_version="schema-v1")
    rev = store.set_manifest(m_a, idempotency_key="shared-key")
    assert store.set_manifest(m_a, idempotency_key="shared-key") == rev  # replay
    with pytest.raises(IdempotencyConflictError):
        store.set_manifest(ExecutionManifest(run_id="r-ida", nodes=[
            ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE),
            ManifestNode("n2", NodeType.PROJECTION)],
            identity_algorithm="identity-v1", graph_version="graph-v1",
            schema_version="schema-v1"), idempotency_key="shared-key")
    # same key reused in a different scope (another run) -> conflict
    pid2 = "P-IDEM2"
    run_id_b = frozen_run(r1_store, pid2, "r-idb", nodes=["n1"], snapshot_id="snap-NB",
                          revision_id="rev-1b")
    m_b = ExecutionManifest(run_id="r-idb",
                            nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE)],
                            identity_algorithm="identity-v1", graph_version="graph-v1",
                            schema_version="schema-v1")
    with pytest.raises(IdempotencyConflictError):
        store.set_manifest(m_b, idempotency_key="shared-key")
    # domain-object path: same key + same object replays, different object conflicts
    v1 = store.put_domain_object("risk_instance", "ri-x", {"identity_key": "k"},
                                 run_id=run_id_a, idempotency_key="do-key")
    assert store.put_domain_object("risk_instance", "ri-x", {"identity_key": "k"},
                                   run_id=run_id_a, idempotency_key="do-key") == v1
    with pytest.raises(IdempotencyConflictError):
        store.put_domain_object("risk_instance", "ri-x", {"identity_key": "k2"},
                                run_id=run_id_a, idempotency_key="do-key")
    # facts path: same key + same facts replays, different facts conflicts
    store.begin_node_run(run_id_a, "det2", NodeType.DETERMINISTIC_SERVICE, "det2-key")
    inserted = store.commit_facts(run_id_a, "det2", "fact-key",
                                  [CanonicalFact(fact_type="ae_record",
                                                 body={"term": "Headache"}, subject_id="S001")])
    assert inserted == 1
    assert store.commit_facts(run_id_a, "det2", "fact-key",
                              [CanonicalFact(fact_type="ae_record",
                                             body={"term": "Headache"}, subject_id="S001")]) == 1
    with pytest.raises(IdempotencyConflictError):
        store.commit_facts(run_id_a, "det2", "fact-key",
                           [CanonicalFact(fact_type="ae_record",
                                          body={"term": "Nausea"}, subject_id="S001")])
    assert len(store.list_facts(run_id_a)) == 1  # no partial side effects


def test_recover_fails_closed_on_broken_chain(r1_store):
    """recover() must fail closed on a broken audit chain and must NOT append a
    recovery event onto the broken chain."""
    pid = "P-RECB"
    run_id = frozen_run(r1_store, pid, "r-recb", nodes=["n1"])
    store = r1_store
    run_node(store, run_id, key="k1", envelope=make_env(run_id, "n1"))
    before_count = len(store.audit_trail())
    conn = sqlite3.connect(str(store.db_path))
    conn.execute("UPDATE audit_events SET payload_json='{\"tampered\":true}' WHERE seq=1")
    conn.commit()
    conn.close()
    report = store.recover()
    assert report.audit_ok is False and report.audit_first_bad_seq == 1
    assert report.integrity_violations == []          # only the chain is broken
    events = [e for e in store.audit_trail() if e.event_type == domain.EVENT_RECOVERY]
    assert events == []                                # nothing appended
    assert len(store.audit_trail()) == before_count
    ok, _, _ = store.verify_audit_chain()
    assert ok is False
    assert store.get_run(run_id).analysis_state == AnalysisState.NOT_STARTED


def test_content_write_durable_no_tmp_residue(r1_store):
    """Content-addressed writes leave no .tmp residue; every committed file
    matches its content address."""
    pid = "P-DURA"
    run_id = frozen_run(r1_store, pid, "r-dura", nodes=["n1", "n2", "n3"])
    store = r1_store
    for i, nid in enumerate(["n1", "n2", "n3"]):
        store.begin_node_run(run_id, nid, NodeType.DETERMINISTIC_SERVICE, f"dk{i}")
        store.complete_node_run(run_id, nid, f"dk{i}", NodeStatus.PASSED,
                                envelope=make_env(run_id, nid, payload={"i": i}))
    make_snapshot(store, pid, "snap-dura", "N", rows={"ae": [{"subject_id": "S001"}]})
    assert list(store.artifact_dir.glob("*.tmp")) == []
    for env in store.list_artifacts(run_id):
        assert store.verify_artifact(env.artifact_id)
    snap = store.get_listing_snapshot("snap-dura")
    assert (store.artifact_dir / f"{snap.content_hash}.json").exists()
    assert list(store.artifact_dir.glob("*.tmp")) == []
    assert store.recover().audit_ok


def test_provenance_and_authority_invariants(r1_store):
    """FK enforcement + explicit project/revision consistency checks."""
    store = r1_store
    make_project(store, "P-PA")
    with pytest.raises(StoreError):
        store.add_source_revision(SourceRevision(revision_id="rev-x", project_id="P-NOPE",
                                                 source_type="listing", version="1.0"))
    make_project(store, "P-PB")
    make_revision(store, "P-PA", "rev-a")
    # a revision id must never be reused across projects (fail closed)
    with pytest.raises(IdempotencyConflictError):
        make_revision(store, "P-PB", "rev-a")
    with pytest.raises(StoreError):
        store.add_listing_snapshot(
            ListingSnapshot(snapshot_id="s-x", project_id="P-PB", revision_id="rev-a",
                            snapshot_version="N", is_synthetic=True),
            {"ae": []})
    with pytest.raises(StoreError):
        store.create_run(MonitoringRun(run_id="r-x", project_id="P-PB", mode=RunMode.DAILY,
                                       data_cutoff="2026-01-31", source_revision_id="rev-a",
                                       execution_basis=ExecutionBasis.FULL))
    with pytest.raises(StoreError):
        store.set_manifest(ExecutionManifest(run_id="no-such-run",
                                             nodes=[ManifestNode("n1", NodeType.DETERMINISTIC_SERVICE)]))
    # FK backstop on a raw connection: no orphan rows may reference unknown projects
    conn = sqlite3.connect(str(store.db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO source_revisions(revision_id, project_id, source_type,"
                     " version, content_hash, scope_json, created_at)"
                     " VALUES ('r-fk','P-NOPE','listing','1','h','{}','now')")
    conn.close()


def test_derive_completeness_failed_coverage():
    env = make_env("r", "n")
    env.coverage.expected = [
        CoverageUnit(scope=u.scope, key=u.key, expected=True,
                     status=CoverageUnitStatus.FAILED, reason="extraction crashed")
        for u in env.coverage.expected
    ]
    assert env.derive_completeness() == ArtifactCompleteness.FAILED
    ok, reasons = env.is_publishable()
    assert not ok and reasons


def test_canonical_json_rejects_non_finite_and_unsupported():
    with pytest.raises(ValueError):
        canonical_json({"x": float("nan")})
    with pytest.raises(ValueError):
        canonical_json({"x": float("inf")})
    with pytest.raises(ValueError):
        content_hash({"x": float("-inf")})
    with pytest.raises(TypeError):
        domain.to_jsonable({1, 2})
    with pytest.raises(TypeError):
        content_hash({"payload": {"tags": {"a", "b"}}})

    class Weird:
        pass

    with pytest.raises(TypeError):
        domain.to_jsonable(Weird())
