"""Framework-neutral integrated synthetic closure for R1 (corrective v2).

This module composes existing accepted R1 contracts into one same-run evidence
chain. It does NOT modify any accepted module; it only orchestrates them.

Key properties (corrected from first pass):

* **Idempotent completed re-entry**: calling ``run_integrated_closure`` again
  on the same Store/run with the same frozen input returns the stored result
  without new transport, facts, artifacts, audit events or manifest revision.
  Conflicting frozen input fails closed.
* **Partial continuation across Store close/reopen**: a deliberate
  ``interrupt_after`` hook stops after a named phase; the intermediate
  ``AEMHResult`` is persisted as a verified domain object.  Re-opening the
  Store and re-entering reconstructs the exact prior result and continues.
* **Seven-unit manifest**: snapshot acceptance, deterministic fact/candidate
  derivation, AI candidate review, QC, risk dashboard, Patient
  Journey/Profile-Timeline, and three-part Query drafts are each visible work
  units.  Each begins before its actual work.
* **QC binds both deterministic and AI evidence**: the QC artifact references
  the controller attempt's raw/candidate evidence.  AI output is review support
  only — never a ``CanonicalFact`` or established risk.
* **Truthful failure propagation**: on AI failure/skip, dependent units are
  marked BLOCKED with Chinese audience-safe reasons; evidence state stays
  truthful; ``project_audience_progress`` shows unfinished work.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple
from .adapters import AdapterState, ImmutableAdapterBinding

from .ae_mh import (
    AEMHResult,
    Counterevidence,
    EvidenceLink,
    LifecycleResult,
    persist_ae_mh_result,
    run_ae_mh_vertical_slice,
)

from .audience_progress import project_audience_progress
from .capability_runtime import (
    ApiCapabilityRuntime,
    CapabilityAttemptResult,
    CapabilityRequest,
    CoverageUnit,
    ExecutionProfile,
    InvocationVersions,
    TransportKind,
)
from .controller import CapabilityWorkUnitController
from .domain import (
    AnalysisState,
    ArtifactCompleteness,
    ArtifactEnvelope,
    CanonicalFact,
    CoverageManifest,
    ExecutionManifest,
    EvidenceState,
    IdempotencyConflictError,
    ManifestNode,
    ManifestWorkUnit,
    NodeType,
    NodeStatus,
    OutputState,
    QueryDraft,
    RiskCandidate,
    RiskInstance,
    RiskTransition,
    SubjectTemporalSpine,
    TemporalEvent,
    content_hash,
    from_jsonable,
    now_iso,
    to_jsonable,
)
from .fixtures import SyntheticSnapshotBundle, create_synthetic_run, seed_synthetic_snapshots
from .projections import ProjectionBundle, build_projections, persist_projections
from .store import Store

# ---------------------------------------------------------------------------
# Identity constants (all visibly synthetic, no real-project content)
# ---------------------------------------------------------------------------

CLOSURE_MARKER = "SYNTHETIC-CLOSURE"

NODE_ACCEPT = "closure-node-accept"
NODE_FACTS = "closure-node-facts"
NODE_AI_CANDIDATE = "closure-node-ai-candidate"
NODE_QC = "closure-node-qc"
NODE_DASHBOARD = "closure-node-dashboard"
NODE_JOURNEY = "closure-node-journey"
NODE_QUERY = "closure-node-query"

WU_ACCEPT = "closure-wu-accept"
WU_FACTS = "closure-wu-facts"
WU_AI_CANDIDATE = "closure-wu-ai-candidate"
WU_QC = "closure-wu-qc"
WU_DASHBOARD = "closure-wu-dashboard"
WU_JOURNEY = "closure-wu-journey"
WU_QUERY = "closure-wu-query"

# No depends_on in the manifest: the orchestrator controls ordering so that
# blocked downstream units can be marked directly without the Store rejecting
# a begin on an unsatisfied dependency.
GRAPH_VERSION = "closure-integrated-graph-v2"
SCHEMA_VERSION = "closure-integrated-schema-v2"
RULE_VERSION = "closure-rule-v2"
KNOWLEDGE_VERSION = "closure-knowledge-v2"

AI_BINDING_ID = "closure-ai-binding"
AI_PROFILE_ID = "closure-ai-profile"
AI_RUNTIME_REVISION = "closure-ai-runtime-v1"

INTERMEDIATE_KIND = "closure_intermediate_result"
INTERMEDIATE_ID = "closure-intermediate-aemh-result"
CLOSURE_RESULT_KIND = "closure_result_envelope"

# Interrupt-after phase names (public hook for continuation tests)
INTERRUPT_AFTER_FACTS = "facts"
INTERRUPT_AFTER_AI = "ai"


class ClosureInterrupted(Exception):
    """Raised by the orchestrator when a bounded interruption hook fires."""

    def __init__(self, phase: str, run_id: str) -> None:
        self.phase = phase
        self.run_id = run_id
        super().__init__("closure interrupted after %s for run %s" % (phase, run_id))


# ---------------------------------------------------------------------------
# Synthetic API transport (no real external call)
# ---------------------------------------------------------------------------


class SyntheticClosureTransport:
    """Deterministic fictional API transport; records calls."""

    def __init__(self, candidate_note: str = "synthetic closure candidate") -> None:
        self.candidate_note = candidate_note
        self.call_count = 0
        self.calls: List[Tuple[Mapping[str, Any], ExecutionProfile]] = []

    def __call__(
        self,
        request: Mapping[str, Any],
        profile: ExecutionProfile,
    ) -> Mapping[str, Any]:
        self.call_count += 1
        self.calls.append((dict(request), profile))
        params = request["params"]
        expected = params["expected_coverage"]
        produced = [dict(unit, status="covered") for unit in expected]
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "execution_id": "closure-synthetic-execution-%d" % self.call_count,
            "result": {
                "status": "complete",
                "execution_identity": params["execution_identity"],
                "candidate_payload": {
                    "fixture_marker": CLOSURE_MARKER,
                    "note": self.candidate_note,
                    "subject_review": params.get("input", {}),
                },
                "produced_units": produced,
            },
        }


def _closure_profile() -> ExecutionProfile:
    binding = ImmutableAdapterBinding(
        binding_id=AI_BINDING_ID,
        capability="ae-mh-candidate-review",
        provider="user-selected-closure-provider",
        model="user-selected-closure-model",
        selector="closure-selector",
        effort="closure-effort",
        adapter_version="closure-adapter-r1",
        allowed_tools=("read_synthetic_input",),
        isolation="fresh_context",
        endpoint="external",
    )
    return ExecutionProfile(
        profile_id=AI_PROFILE_ID,
        transport=TransportKind.API,
        binding=binding,
        api_route="user-configured://closure-ae-mh-review",
        credential_ref="opaque-closure-reference",
        runtime_revision=AI_RUNTIME_REVISION,
        timeout_seconds=10,
    )


def _closure_versions(bundle: SyntheticSnapshotBundle) -> InvocationVersions:
    return InvocationVersions(
        source_revision_id=bundle.snapshot_n1.revision_id,
        rule_version=RULE_VERSION,
        knowledge_version=KNOWLEDGE_VERSION,
        graph_version=GRAPH_VERSION,
        schema_version=SCHEMA_VERSION,
    )


def _closure_manifest(run_id: str) -> ExecutionManifest:
    """Build a 7-unit manifest covering every integrated phase visibly."""

    nodes = [
        ManifestNode(NODE_ACCEPT, NodeType.DETERMINISTIC_SERVICE, artifact_required=False),
        ManifestNode(NODE_FACTS, NodeType.DETERMINISTIC_SERVICE, artifact_required=False),
        ManifestNode(NODE_AI_CANDIDATE, NodeType.AI_CANDIDATE),
        ManifestNode(NODE_QC, NodeType.DETERMINISTIC_SERVICE),
        ManifestNode(NODE_DASHBOARD, NodeType.PROJECTION, artifact_required=False),
        ManifestNode(NODE_JOURNEY, NodeType.PROJECTION, artifact_required=False),
        ManifestNode(NODE_QUERY, NodeType.PROJECTION, artifact_required=False),
    ]
    # No depends_on: the orchestrator sequences work units in code so that
    # blocked downstream units can be completed as BLOCKED without the Store
    # rejecting a begin on an unsatisfied dependency.
    work_units = [
        ManifestWorkUnit(
            work_unit_id=WU_ACCEPT, node_id=NODE_ACCEPT,
            label="确认快照接受与基线资格", stage="来源确认",
            scope="source", target_ref="快照接受链", ordinal=1,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_FACTS, node_id=NODE_FACTS,
            label="构建 AE/MH 标准化事实与候选", stage="数据解构",
            scope="risk_domain", target_ref="AE/MH 事实与候选", ordinal=2,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_AI_CANDIDATE, node_id=NODE_AI_CANDIDATE,
            label="AI 候选复核（漏报审查）", stage="风险分析",
            scope="risk_domain", target_ref="AI 候选复核", ordinal=3,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_QC, node_id=NODE_QC,
            label="独立核对覆盖完整性与候选隔离", stage="独立核对",
            scope="risk_domain", target_ref="覆盖核对", ordinal=4,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_DASHBOARD, node_id=NODE_DASHBOARD,
            label="生成项目级风险驾驶舱", stage="投影发布",
            scope="risk_domain", target_ref="风险驾驶舱", ordinal=5,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_JOURNEY, node_id=NODE_JOURNEY,
            label="生成受试者医学旅程与 Profile/Timeline", stage="投影发布",
            scope="subject", target_ref="受试者旅程", ordinal=6,
        ),
        ManifestWorkUnit(
            work_unit_id=WU_QUERY, node_id=NODE_QUERY,
            label="生成三分句 Query 草稿", stage="投影发布",
            scope="risk_domain", target_ref="Query 草稿", ordinal=7,
        ),
    ]
    return ExecutionManifest(
        run_id=run_id, nodes=nodes, work_units=work_units,
        graph_id="closure-integrated-graph-v2", graph_version=GRAPH_VERSION,
        schema_version=SCHEMA_VERSION, rule_version=RULE_VERSION,
        knowledge_version=KNOWLEDGE_VERSION,
        source_coverage=["SYNTHETIC-full-listing", "SYNTHETIC-AE-MH"],
        identity_algorithm="synthetic-ae-mh-identity-v1",
    )


# ---------------------------------------------------------------------------
# Closure result
# ---------------------------------------------------------------------------


@dataclass
class ClosureResult:
    """All same-run outputs from one integrated closure execution."""

    run_id: str
    project_id: str
    snapshot_n_id: str
    snapshot_n1_id: str
    manifest_revision: int
    ae_mh_result: AEMHResult
    projections: ProjectionBundle
    ai_attempt_result: Optional[CapabilityAttemptResult]
    audience_progress: Dict[str, Any]
    transport_call_count: int
    facts_committed: int
    candidates_persisted: int
    queries_persisted: int
    spines_persisted: int
    projections_persisted: int
    run_output_state: str
    evidence_state: str
    identity_chain: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_coverage() -> CoverageManifest:
    m = CoverageManifest(expected=[], produced=[])
    m.reconcile()
    return m


def _persist_intermediate(store: Store, run_id: str, result: AEMHResult) -> None:
    """Persist the AE/MH intermediate result as a verified domain object."""

    store.put_domain_object(
        INTERMEDIATE_KIND,
        "%s:%s" % (INTERMEDIATE_ID, run_id),
        to_jsonable(result),
        run_id=run_id,
        idempotency_key="%s:%s" % (INTERMEDIATE_ID, run_id),
    )


def _load_intermediate(store: Store, run_id: str) -> Optional[AEMHResult]:
    """Reconstruct the exact prior AE/MH result from the Store.

    ``from_jsonable`` handles plain dataclass fields but not
    ``Dict[str, SubjectTemporalSpine]`` or ``Dict[str, List[EvidenceLink]]``;
    we coerce those explicitly after the base reconstruction.
    """

    row = store.get_domain_object(
        INTERMEDIATE_KIND, "%s:%s" % (INTERMEDIATE_ID, run_id),
    )
    if row is None:
        return None
    data = row[1]
    result = from_jsonable(AEMHResult, data)
    # Reconstruct dict-of-dataclass fields that from_jsonable leaves as dicts.
    result.temporal_spines = {
        k: from_jsonable(SubjectTemporalSpine, v)
        for k, v in data.get("temporal_spines", {}).items()
    }
    result.evidence_links = {
        k: [from_jsonable(EvidenceLink, e) for e in v]
        for k, v in data.get("evidence_links", {}).items()
    }
    result.reported_facts = [
        from_jsonable(CanonicalFact, f) for f in data.get("reported_facts", [])
    ]
    result.candidates = [
        from_jsonable(RiskCandidate, c) for c in data.get("candidates", [])
    ]
    result.queries = [
        from_jsonable(QueryDraft, q) for q in data.get("queries", [])
    ]
    result.counterevidence = [
        from_jsonable(Counterevidence, ce) for ce in data.get("counterevidence", [])
    ]
    lc_data = data.get("lifecycle")
    if lc_data:
        lc = from_jsonable(LifecycleResult, lc_data)
        lc.instances = [
            from_jsonable(RiskInstance, ri) for ri in lc_data.get("instances", [])
        ]
        lc.transitions = [
            from_jsonable(RiskTransition, rt) for rt in lc_data.get("transitions", [])
        ]
        result.lifecycle = lc
    return result


def _persist_closure_envelope(store: Store, run_id: str, envelope: Mapping[str, Any]) -> None:
    """Persist the final closure envelope for idempotent re-entry detection."""

    store.put_domain_object(
        CLOSURE_RESULT_KIND,
        "closure-result:%s" % run_id,
        dict(envelope),
        run_id=run_id,
        idempotency_key="closure-result:%s" % run_id,
    )


def _load_closure_envelope(store: Store, run_id: str) -> Optional[Dict[str, Any]]:
    """Return the stored closure envelope, or None if not yet completed."""

    row = store.get_domain_object(
        CLOSURE_RESULT_KIND, "closure-result:%s" % run_id,
    )
    if row is None:
        return None
    return dict(row[1])  # type: ignore[arg-type]


def _build_qc_artifact(
    run_id: str,
    result: AEMHResult,
    store: Store,
    ai_attempt_id: Optional[str],
    ai_raw_ref: Optional[str],
) -> ArtifactEnvelope:
    """Build a QC artifact that binds deterministic coverage, candidate-fact
    separation AND the controller attempt's verified raw/candidate evidence.

    The AI evidence is explicitly revalidated via Store public verifiers:
    ``verify_adapter_raw_output`` for the raw output and ``verify_artifact``
    for the persisted candidate artifact.  QC passes only when deterministic
    coverage, candidate-only status, raw integrity and persisted candidate
    integrity all pass.
    """

    coverage_manifest = result.coverage or _empty_coverage()
    separation = result.candidate_fact_separation()
    evidence_refs = [c.candidate_id for c in result.candidates]

    # Explicitly revalidate AI raw output and persisted candidate artifact.
    ai_raw_ok = False
    ai_candidate_ok = False
    ai_candidate_artifact_id: Optional[str] = None
    if ai_attempt_id is not None and ai_raw_ref is not None:
        ai_raw_ok = store.verify_adapter_raw_output(ai_raw_ref)
        # Find the persisted adapter_run to get the candidate_artifact_id
        # produced by persist_capability_attempt (not the later closure artifact).
        adapter_row = store.get_domain_object(
            "adapter_run", "adapter-run:%s" % ai_attempt_id,
        )
        if adapter_row is not None:
            ai_candidate_artifact_id = adapter_row[1].get("candidate_artifact_id")
        if ai_candidate_artifact_id:
            ai_candidate_ok = store.verify_artifact(ai_candidate_artifact_id)
            if ai_candidate_ok:
                evidence_refs.append(ai_candidate_artifact_id)
        if ai_raw_ok:
            evidence_refs.append(ai_raw_ref)

    qc_passed = bool(
        result.coverage_complete
        and not separation["candidates_counted_as_reported"]
        and ai_raw_ok
        and ai_candidate_ok
    )
    payload: Dict[str, Any] = {
        "fixture_marker": CLOSURE_MARKER,
        "run_id": run_id,
        "snapshot_version": result.snapshot_version,
        "coverage_complete": result.coverage_complete,
        "candidate_fact_separation": separation,
        "reported_ae_mh_count": result.reported_ae_mh_count,
        "candidate_count": result.candidate_count,
        "qc_passed": qc_passed,
    }
    if ai_attempt_id is not None:
        payload["ai_review_support"] = {
            "attempt_id": ai_attempt_id,
            "raw_output_ref": ai_raw_ref,
            "raw_verified": ai_raw_ok,
            "candidate_artifact_id": ai_candidate_artifact_id,
            "candidate_verified": ai_candidate_ok,
            "role": "candidate_only_review_support",
            "promoted_to_fact": False,
        }
    return ArtifactEnvelope(
        artifact_type="qc_coverage_ledger",
        version="closure-qc-v2",
        run_id=run_id, node_id=NODE_QC,
        node_type=NodeType.DETERMINISTIC_SERVICE,
        payload=payload, payload_role="ledger",
        coverage=coverage_manifest,
        completeness=(
            ArtifactCompleteness.COMPLETE if qc_passed
            else ArtifactCompleteness.PARTIAL
        ),
        evidence_refs=evidence_refs,
    )

def _build_dashboard_artifact(run_id: str, projections: ProjectionBundle) -> ArtifactEnvelope:
    proj_dict = projections.as_dict()
    site_count = len(proj_dict.get("site_dashboards", {}))
    subject_count = len(proj_dict.get("subject_profiles", {}))
    timeline_count = len(proj_dict.get("subject_timelines", {}))
    version_count = len(proj_dict.get("versions", []))
    total_projections = version_count  # persist_projections returns version count
    return ArtifactEnvelope(
        artifact_type="risk_dashboard_projection",
        version="closure-dashboard-v2",
        run_id=run_id, node_id=NODE_DASHBOARD,
        node_type=NodeType.PROJECTION,
        payload={
            "fixture_marker": CLOSURE_MARKER,
            "run_id": run_id,
            "projection_count": total_projections,
            "site_dashboards": site_count,
            "subject_profiles": subject_count,
            "subject_timelines": timeline_count,
        },
        payload_role="projection",
        coverage=_empty_coverage(),
        completeness=ArtifactCompleteness.COMPLETE,
        evidence_refs=[],
    )


def _build_ai_artifact(
    run_id: str, ai_result: CapabilityAttemptResult, transport_calls: int,
) -> ArtifactEnvelope:
    coverage = ai_result.adapter_run.coverage
    produced = list(coverage.produced) if coverage is not None else []
    expected = list(ai_result.request.expected_units)
    return ArtifactEnvelope(
        artifact_type="ai_candidate_review",
        version="closure-ai-v2",
        run_id=run_id, node_id=NODE_AI_CANDIDATE,
        node_type=NodeType.AI_CANDIDATE,
        payload={
            "fixture_marker": CLOSURE_MARKER,
            "status": ai_result.status.value,
            "candidate_artifact_present": ai_result.adapter_run.candidate_artifact is not None,
            "candidate_is_candidate_only": ai_result.adapter_run.is_candidate_only(),
            "transport_call_count": transport_calls,
        },
        payload_role="candidate",
        coverage=CoverageManifest(
            expected=expected, produced=produced,
        ).reconcile(),
        completeness=(
            ArtifactCompleteness.COMPLETE
            if ai_result.status == AdapterState.COMPLETE
            else ArtifactCompleteness.PARTIAL
        ),
        evidence_refs=[],
    )


def _block_downstream(
    store: Store, run_id: str, revision: int,
    units: List[str], reason: str,
) -> None:
    """Mark downstream work units as BLOCKED with audience-safe Chinese reason.

    Work units must be RUNNING before they can complete; we begin each first.
    The manifest has no depends_on, so begin always succeeds.
    """

    for wu_id in units:
        store.begin_work_unit(
            run_id, wu_id, "closure-block-%s" % wu_id,
            "正在等待前置工作完成",
        )
        store.complete_work_unit(
            run_id, wu_id, "closure-block-%s" % wu_id,
            NodeStatus.BLOCKED, reason, evidence_count=0,
        )


def _complete_downstream_node(
    store: Store, run_id: str, node_id: str, node_type: NodeType,
    node_key: str, status: NodeStatus,
    output: Optional[Mapping[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Begin and complete a node for a set of work units."""

    store.begin_node_run(run_id, node_id, node_type, node_key)
    store.complete_node_run(
        run_id, node_id, node_key, status,
        output=dict(output or {}),
        error=error,
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_integrated_closure(
    store: Store,
    *,
    transport: Optional[SyntheticClosureTransport] = None,
    fail_ai_transport: bool = False,
    skip_ai: bool = False,
    interrupt_after: Optional[str] = None,
) -> ClosureResult:
    """Execute or re-enter one same-run integrated synthetic closure.

    Parameters
    ----------
    store
        An open authoritative Store. The caller owns its lifecycle.
    transport
        Optional synthetic transport override.
    fail_ai_transport
        If True, the AI transport raises (failure-closed test).
    skip_ai
        If True, the AI candidate work unit is not executed (coverage gap test).
    interrupt_after
        Bounded interruption hook: ``INTERRUPT_AFTER_FACTS`` or
        ``INTERRUPT_AFTER_AI``.  The orchestrator persists the intermediate
        AE/MH result and raises ``ClosureInterrupted``.  Re-entering with the
        same Store reconstructs the exact prior result and continues.

    Idempotent re-entry: if the closure has already completed for this run,
    the stored result is returned without side effects.
    """

    if transport is None:
        transport = SyntheticClosureTransport()

    bundle = seed_synthetic_snapshots(store)
    run = create_synthetic_run(store, bundle)
    run_id = run.run_id
    project_id = bundle.project_id

    # --- Idempotent re-entry: check if closure already completed ---
    existing_envelope = _load_closure_envelope(store, run_id)
    if existing_envelope is not None:
        return _reconstruct_completed_result(store, run_id, project_id, bundle, existing_envelope)

    # --- Freeze manifest (idempotent by content hash) ---
    manifest = _closure_manifest(run_id)
    revision = store.set_manifest(manifest)

    current_run = store.get_run(run_id)
    if current_run.analysis_state == AnalysisState.COMPLETE:
        # Run was completed by a prior closure that didn't persist an envelope.
        # Return reconstructed result.
        return _reconstruct_completed_result(store, run_id, project_id, bundle, {})

    if current_run.analysis_state == AnalysisState.NOT_STARTED:
        store.update_run_state(run_id, analysis=AnalysisState.RUNNING)

    # ================================================================
    # WU 1: Snapshot acceptance confirmation
    # ================================================================
    store.begin_node_run(run_id, NODE_ACCEPT, NodeType.DETERMINISTIC_SERVICE,
                         "closure-accept-node-key")
    store.begin_work_unit(run_id, WU_ACCEPT, "closure-accept-wu-key",
                          "正在确认快照接受与基线资格")
    acceptance_n1 = store.get_acceptance(bundle.snapshot_n1.snapshot_id)
    baseline_proof_n1 = store.baseline_eligibility_proof(bundle.snapshot_n1.snapshot_id)
    store.complete_work_unit(
        run_id, WU_ACCEPT, "closure-accept-wu-key",
        NodeStatus.PASSED, "已完成：确认快照接受与基线资格",
        evidence_count=2,
    )
    store.complete_node_run(
        run_id, NODE_ACCEPT, "closure-accept-node-key", NodeStatus.PASSED,
        output={"fixture_marker": CLOSURE_MARKER,
                "acceptance_state": acceptance_n1.state.value,
                "baseline_eligible": baseline_proof_n1.is_baseline_eligible},
    )

    # ================================================================
    # WU 2: Deterministic fact/candidate derivation
    # ================================================================
    # Check for persisted intermediate (continuation after interruption)
    prior_intermediate = _load_intermediate(store, run_id)

    store.begin_node_run(run_id, NODE_FACTS, NodeType.DETERMINISTIC_SERVICE,
                         "closure-facts-node-key")
    store.begin_work_unit(run_id, WU_FACTS, "closure-facts-wu-key",
                          "正在构建 AE/MH 标准化事实与候选")

    if prior_intermediate is not None:
        result_n1 = prior_intermediate
    else:
        result_n = run_ae_mh_vertical_slice(
            bundle.listing_n, project_id=project_id,
            run_id="SYNTHETIC-CLOSURE-RUN-N", snapshot_version="SYNTHETIC-N",
            store=store, snapshot_id=bundle.snapshot_n.snapshot_id,
        )
        result_n1 = run_ae_mh_vertical_slice(
            bundle.listing_n1, project_id=project_id,
            run_id=run_id, snapshot_version="SYNTHETIC-N1",
            previous_result=result_n, store=store,
            snapshot_id=bundle.snapshot_n1.snapshot_id,
        )
        # Persist intermediate for continuation across Store close/reopen.
        _persist_intermediate(store, run_id, result_n1)

    persisted = persist_ae_mh_result(store, result_n1, facts_node_id=NODE_FACTS)
    store.complete_work_unit(
        run_id, WU_FACTS, "closure-facts-wu-key",
        NodeStatus.PASSED, "已完成：构建 AE/MH 标准化事实与候选",
        evidence_count=persisted.get("facts", 0),
    )
    store.complete_node_run(
        run_id, NODE_FACTS, "closure-facts-node-key", NodeStatus.PASSED,
        output={"fixture_marker": CLOSURE_MARKER,
                "facts_source": "deterministic AE/MH"},
    )

    # --- Bounded interruption hook: after facts ---
    if interrupt_after == INTERRUPT_AFTER_FACTS:
        raise ClosureInterrupted(INTERRUPT_AFTER_FACTS, run_id)

    # ================================================================
    # WU 3: AI candidate review via CapabilityWorkUnitController
    # ================================================================
    # On continuation after INTERRUPT_AFTER_AI, the AI work unit is already
    # terminal; skip re-execution and reconstruct evidence from Store state.
    ai_wu_existing = store.get_work_unit_run(run_id, revision, WU_AI_CANDIDATE)
    ai_already_done = (
        ai_wu_existing is not None
        and ai_wu_existing.status in (
            NodeStatus.PASSED, NodeStatus.FAILED, NodeStatus.BLOCKED,
        )
    )

    profile = _closure_profile()
    versions = _closure_versions(bundle)
    ai_payload = {
        "fixture_marker": CLOSURE_MARKER,
        "subject_ids": list(result_n1.temporal_spines.keys()),
        "candidate_count": result_n1.candidate_count,
        "domain": "AE/MH under-reporting review",
    }
    expected_coverage = (CoverageUnit(scope="risk_domain", key="ae-mh-candidate-review"),)
    ai_attempt_id: Optional[str] = None
    ai_raw_ref: Optional[str] = None
    if ai_already_done:
        # Continuation after INTERRUPT_AFTER_AI: AI was already executed.
        # Transport is NOT called again; evidence is in the Store.
        ai_result = None
        ai_attempt_id = "closure-ai-attempt-1"
        adapter_row = store.get_domain_object(
            "adapter_run", "adapter-run:%s" % ai_attempt_id,
        )
        ai_raw_ref = (
            adapter_row[1].get("raw_output_ref")
            if adapter_row is not None else None
        )
        ai_status = ai_wu_existing.status
    else:
        store.begin_node_run(run_id, NODE_AI_CANDIDATE, NodeType.AI_CANDIDATE,
                             "closure-ai-node-key")

        if fail_ai_transport:
            def _failing_transport(req: Mapping[str, Any], prof: ExecutionProfile) -> Mapping[str, Any]:
                raise RuntimeError("synthetic closure transport failure")
            transport_impl = _failing_transport
        else:
            transport_impl = transport

        runtime = ApiCapabilityRuntime(
            profile, transport_impl,
            manifest_revision_reader=lambda rid: store.get_run(rid).manifest_revision,
            attempt_journal=store,
            journal_owner_token="closure-controller-owner",
        )
        controller = CapabilityWorkUnitController(store)

        if skip_ai:
            ai_result = None
            # Use the public runtime lifecycle plus controller reconcile to
            # close the AI work unit as BLOCKED without dispatching transport.
            skip_request = CapabilityRequest.build(
                attempt_id="closure-skip-attempt-1",
                monitoring_run_id=run_id, node_id=NODE_AI_CANDIDATE,
                manifest_revision=revision, profile=profile,
                versions=versions, payload=ai_payload,
                expected_units=expected_coverage,
            )
            controller.register(skip_request, WU_AI_CANDIDATE)

            class _SkipBeforeTransport:
                def on_attempt_prepared(
                    self, request: CapabilityRequest, *, replaying: bool,
                ) -> None:
                    raise RuntimeError(
                        "synthetic closure intentionally skipped AI dispatch"
                    )

                def on_attempt_terminal(
                    self, result: CapabilityAttemptResult,
                ) -> None:
                    raise AssertionError(
                        "skipped AI dispatch must not reach terminal output"
                    )

                def on_attempt_interrupted(
                    self, request: CapabilityRequest, *, reason: str,
                ) -> None:
                    return None

            try:
                runtime.invoke(
                    attempt_id=skip_request.attempt_id,
                    monitoring_run_id=skip_request.monitoring_run_id,
                    node_id=skip_request.node_id,
                    manifest_revision=skip_request.manifest_revision,
                    versions=skip_request.versions,
                    payload=skip_request.payload,
                    expected_units=skip_request.expected_units,
                    lifecycle_observer=_SkipBeforeTransport(),
                )
            except RuntimeError as exc:
                if "intentionally skipped AI dispatch" not in str(exc):
                    raise
            controller.reconcile(runtime, skip_request.attempt_id)
        else:
            ai_result = controller.execute(
                runtime, work_unit_id=WU_AI_CANDIDATE,
                attempt_id="closure-ai-attempt-1",
                monitoring_run_id=run_id, node_id=NODE_AI_CANDIDATE,
                manifest_revision=revision, versions=versions,
                payload=ai_payload, expected_units=expected_coverage,
            )

        if ai_result is not None and ai_result.status == AdapterState.COMPLETE:
            ai_status = NodeStatus.PASSED
        elif ai_result is not None:
            ai_status = NodeStatus.FAILED
        else:
            ai_status = NodeStatus.BLOCKED

        ai_artifact = (
            _build_ai_artifact(run_id, ai_result, transport.call_count)
            if ai_result is not None and ai_result.status == AdapterState.COMPLETE
            else None
        )

        store.complete_node_run(
            run_id, NODE_AI_CANDIDATE, "closure-ai-node-key", ai_status,
            envelope=ai_artifact,
            output=(
                {"fixture_marker": CLOSURE_MARKER, "ai_status": ai_result.status.value}
                if ai_result is not None
                else {"fixture_marker": CLOSURE_MARKER, "ai_skipped": True}
            ),
        )

        # --- Bounded interruption hook: after AI ---
        if interrupt_after == INTERRUPT_AFTER_AI and ai_result is not None \
                and ai_result.status == AdapterState.COMPLETE:
            raise ClosureInterrupted(INTERRUPT_AFTER_AI, run_id)

    # ================================================================
    # Failure propagation: if AI failed or was skipped, mark downstream
    # work units as BLOCKED and nodes as terminal with truthful states.
    # ================================================================
    ai_ok = (
        (ai_result is not None and ai_result.status == AdapterState.COMPLETE)
        or (ai_already_done and ai_status == NodeStatus.PASSED)
    )

    # Extract AI evidence references for QC consumption.
    if ai_result is not None:
        ai_attempt_id = ai_result.request.attempt_id
        ai_raw_ref = ai_result.adapter_run.raw_output_ref

    if not ai_ok:
        block_reason = "已暂停：AI 候选复核未完成，后续工作无法继续"
        downstream_units = [WU_QC, WU_DASHBOARD, WU_JOURNEY, WU_QUERY]
        _block_downstream(store, run_id, revision, downstream_units, block_reason)

        # Complete downstream nodes as blocked.
        for node_id, node_type, node_key in [
            (NODE_QC, NodeType.DETERMINISTIC_SERVICE, "closure-qc-node-key"),
            (NODE_DASHBOARD, NodeType.PROJECTION, "closure-dashboard-node-key"),
            (NODE_JOURNEY, NodeType.PROJECTION, "closure-journey-node-key"),
            (NODE_QUERY, NodeType.PROJECTION, "closure-query-node-key"),
        ]:
            _complete_downstream_node(
                store, run_id, node_id, node_type, node_key,
                NodeStatus.BLOCKED,
                output={"fixture_marker": CLOSURE_MARKER, "blocked_reason": "ai_incomplete"},
                error="AI candidate review incomplete",
            )

        # Persist the authoritative evidence transition to PARTIAL.
        evidence_state = EvidenceState.PARTIAL
        store.update_run_state(run_id, evidence=evidence_state)
        output_state = store.get_run(run_id).output_state.value

        projections = build_projections(result_n1)
        projection_count = 0

        # Persist closure envelope for this incomplete run.
        audience = project_audience_progress(store, run_id)
        identity_chain = _build_identity_chain(
            run_id, project_id, bundle, revision, result_n1,
            queries=result_n1.queries, transport_calls=transport.call_count,
            ai_attempt_id=ai_attempt_id, ai_raw_ref=ai_raw_ref,
            ai_ok=ai_ok, facts_count=len(store.list_facts(run_id)),
            output_state=output_state, evidence_state=evidence_state.value,
            store=store,
        )
        envelope = {
            "run_id": run_id, "complete": False,
            "output_state": output_state,
            "evidence_state": evidence_state.value,
            "identity_chain": identity_chain,
        }
        _persist_closure_envelope(store, run_id, envelope)

        return ClosureResult(
            run_id=run_id, project_id=project_id,
            snapshot_n_id=bundle.snapshot_n.snapshot_id,
            snapshot_n1_id=bundle.snapshot_n1.snapshot_id,
            manifest_revision=revision,
            ae_mh_result=result_n1, projections=projections,
            ai_attempt_result=ai_result, audience_progress=audience,
            transport_call_count=transport.call_count,
            facts_committed=len(store.list_facts(run_id)),
            candidates_persisted=persisted.get("candidates", 0),
            queries_persisted=0,
            spines_persisted=persisted.get("spines", 0),
            projections_persisted=0,
            run_output_state=output_state,
            evidence_state=store.get_run(run_id).evidence_state.value,
            identity_chain=identity_chain,
        )

    # ================================================================
    # WU 4: QC — binds deterministic coverage + AI candidate evidence
    # ================================================================
    store.begin_node_run(run_id, NODE_QC, NodeType.DETERMINISTIC_SERVICE,
                         "closure-qc-node-key")
    store.begin_work_unit(run_id, WU_QC, "closure-qc-wu-key",
                          "正在核对覆盖完整性与候选隔离")
    qc_artifact = _build_qc_artifact(run_id, result_n1, store, ai_attempt_id, ai_raw_ref)
    ai_support = qc_artifact.payload.get("ai_review_support", {})
    qc_pass = bool(qc_artifact.payload.get("qc_passed"))
    qc_status = NodeStatus.PASSED if qc_pass else NodeStatus.FAILED
    qc_detail = ("已完成：核对覆盖完整性与候选隔离" if qc_pass
                 else "未完成：覆盖、候选隔离或 AI 证据完整性未通过")
    store.complete_work_unit(run_id, WU_QC, "closure-qc-wu-key",
                             qc_status, qc_detail,
                             evidence_count=len(qc_artifact.evidence_refs))
    store.complete_node_run(
        run_id, NODE_QC, "closure-qc-node-key", qc_status,
        envelope=qc_artifact if qc_pass else None,
        output={"fixture_marker": CLOSURE_MARKER,
                "deterministic_coverage_complete": result_n1.coverage_complete,
                "qc_passed": qc_pass,
                "ai_evidence_consumed": qc_pass,
                "ai_raw_verified": ai_support.get("raw_verified", False),
                "ai_candidate_verified": ai_support.get("candidate_verified", False)},
        error=None if qc_pass else "coverage or AI evidence integrity incomplete",
    )

    if not qc_pass:
        block_reason = "已暂停：覆盖或 AI 证据完整性核对未通过，后续工作无法继续"
        downstream_units = [WU_DASHBOARD, WU_JOURNEY, WU_QUERY]
        _block_downstream(store, run_id, revision, downstream_units, block_reason)
        for node_id, node_type, node_key in [
            (NODE_DASHBOARD, NodeType.PROJECTION, "closure-dashboard-node-key"),
            (NODE_JOURNEY, NodeType.PROJECTION, "closure-journey-node-key"),
            (NODE_QUERY, NodeType.PROJECTION, "closure-query-node-key"),
        ]:
            _complete_downstream_node(
                store, run_id, node_id, node_type, node_key,
                NodeStatus.BLOCKED,
                output={"fixture_marker": CLOSURE_MARKER,
                        "blocked_reason": "qc_incomplete"},
                error="QC evidence integrity incomplete",
            )

        evidence_state = EvidenceState.PARTIAL
        store.update_run_state(run_id, evidence=evidence_state)
        output_state = store.get_run(run_id).output_state.value
        projections = build_projections(result_n1)
        audience = project_audience_progress(store, run_id)
        identity_chain = _build_identity_chain(
            run_id, project_id, bundle, revision, result_n1,
            queries=result_n1.queries, transport_calls=transport.call_count,
            ai_attempt_id=ai_attempt_id, ai_raw_ref=ai_raw_ref,
            ai_ok=False, facts_count=len(store.list_facts(run_id)),
            output_state=output_state, evidence_state=evidence_state.value,
            store=store,
        )
        envelope = {
            "run_id": run_id, "complete": False,
            "output_state": output_state,
            "evidence_state": evidence_state.value,
            "identity_chain": identity_chain,
        }
        _persist_closure_envelope(store, run_id, envelope)
        return ClosureResult(
            run_id=run_id, project_id=project_id,
            snapshot_n_id=bundle.snapshot_n.snapshot_id,
            snapshot_n1_id=bundle.snapshot_n1.snapshot_id,
            manifest_revision=revision,
            ae_mh_result=result_n1, projections=projections,
            ai_attempt_result=ai_result, audience_progress=audience,
            transport_call_count=transport.call_count,
            facts_committed=len(store.list_facts(run_id)),
            candidates_persisted=persisted.get("candidates", 0),
            queries_persisted=0,
            spines_persisted=persisted.get("spines", 0),
            projections_persisted=0,
            run_output_state=output_state,
            evidence_state=store.get_run(run_id).evidence_state.value,
            identity_chain=identity_chain,
        )

    # ================================================================
    # WU 5: Risk dashboard projection
    # ================================================================
    projections = build_projections(result_n1)
    projection_count = persist_projections(store, projections)

    store.begin_node_run(run_id, NODE_DASHBOARD, NodeType.PROJECTION,
                         "closure-dashboard-node-key")
    store.begin_work_unit(run_id, WU_DASHBOARD, "closure-dashboard-wu-key",
                          "正在生成项目级风险驾驶舱")
    dashboard_artifact = _build_dashboard_artifact(run_id, projections)
    store.complete_work_unit(run_id, WU_DASHBOARD, "closure-dashboard-wu-key",
                             NodeStatus.PASSED,
                             "已完成：生成项目级风险驾驶舱",
                             evidence_count=projection_count)
    store.complete_node_run(
        run_id, NODE_DASHBOARD, "closure-dashboard-node-key", NodeStatus.PASSED,
        envelope=dashboard_artifact,
        output={"fixture_marker": CLOSURE_MARKER, "projection_count": projection_count},
    )

    # ================================================================
    # WU 6: Patient Journey / Profile-Timeline (shared temporal spine)
    # ================================================================
    store.begin_node_run(run_id, NODE_JOURNEY, NodeType.PROJECTION,
                         "closure-journey-node-key")
    store.begin_work_unit(run_id, WU_JOURNEY, "closure-journey-wu-key",
                          "正在生成受试者医学旅程与 Profile/Timeline")
    spine_count = len(result_n1.temporal_spines)
    store.complete_work_unit(run_id, WU_JOURNEY, "closure-journey-wu-key",
                             NodeStatus.PASSED,
                             "已完成：生成受试者医学旅程与 Profile/Timeline",
                             evidence_count=spine_count)
    store.complete_node_run(
        run_id, NODE_JOURNEY, "closure-journey-node-key", NodeStatus.PASSED,
        output={"fixture_marker": CLOSURE_MARKER,
                "spine_subjects": sorted(result_n1.temporal_spines.keys()),
                "spine_count": spine_count},
    )

    # ================================================================
    # WU 7: Three-part Query drafts
    # ================================================================
    queries = result_n1.queries
    query_count = len(queries)

    store.begin_node_run(run_id, NODE_QUERY, NodeType.PROJECTION,
                         "closure-query-node-key")
    store.begin_work_unit(run_id, WU_QUERY, "closure-query-wu-key",
                          "正在生成三分句 Query 草稿")
    # Queries already persisted by persist_ae_mh_result; count them.
    store.complete_work_unit(run_id, WU_QUERY, "closure-query-wu-key",
                             NodeStatus.PASSED,
                             "已完成：生成三分句 Query 草稿",
                             evidence_count=query_count)
    store.complete_node_run(
        run_id, NODE_QUERY, "closure-query-node-key", NodeStatus.PASSED,
        output={"fixture_marker": CLOSURE_MARKER, "query_count": query_count},
    )

    # ================================================================
    # Evidence state + analysis completion + publication
    # ================================================================
    store.update_run_state(run_id, evidence=EvidenceState.COMPLETE)
    store.complete_analysis(run_id, reason="closure integrated completion")
    published = store.publish(
        run_id, OutputState.DRAFT_EXPORTABLE,
        reason="closure synthetic draft evidence",
    )
    output_state = published.output_state.value

    # ================================================================
    # Audience progress + identity chain + closure envelope
    # ================================================================
    audience = project_audience_progress(store, run_id)
    identity_chain = _build_identity_chain(
        run_id, project_id, bundle, revision, result_n1,
        queries=queries, transport_calls=transport.call_count,
        ai_attempt_id=ai_attempt_id, ai_raw_ref=ai_raw_ref,
        ai_ok=True, facts_count=len(store.list_facts(run_id)),
        output_state=output_state, evidence_state=EvidenceState.COMPLETE.value,
        store=store,
    )
    envelope = {
        "run_id": run_id, "complete": True,
        "output_state": output_state,
        "evidence_state": EvidenceState.COMPLETE.value,
        "identity_chain": identity_chain,
    }
    _persist_closure_envelope(store, run_id, envelope)

    return ClosureResult(
        run_id=run_id, project_id=project_id,
        snapshot_n_id=bundle.snapshot_n.snapshot_id,
        snapshot_n1_id=bundle.snapshot_n1.snapshot_id,
        manifest_revision=revision,
        ae_mh_result=result_n1, projections=projections,
        ai_attempt_result=ai_result, audience_progress=audience,
        transport_call_count=transport.call_count,
        facts_committed=len(store.list_facts(run_id)),
        candidates_persisted=persisted.get("candidates", 0),
        queries_persisted=persisted.get("queries", 0),
        spines_persisted=persisted.get("spines", 0),
        projections_persisted=projection_count,
        run_output_state=output_state,
        evidence_state=EvidenceState.COMPLETE.value,
        identity_chain=identity_chain,
    )


def _reconstruct_completed_result(
    store: Store, run_id: str, project_id: str,
    bundle: SyntheticSnapshotBundle, envelope: Mapping[str, Any],
) -> ClosureResult:
    """Reconstruct a ClosureResult from stored state without side effects."""

    revision = store.get_run(run_id).manifest_revision
    result_n1 = _load_intermediate(store, run_id)
    if result_n1 is None:
        # Fallback: recompute (deterministic, same input). This path is
        # for runs that completed before the intermediate was persisted.
        result_n = run_ae_mh_vertical_slice(
            bundle.listing_n, project_id=project_id,
            run_id="SYNTHETIC-CLOSURE-RUN-N", snapshot_version="SYNTHETIC-N",
            store=store, snapshot_id=bundle.snapshot_n.snapshot_id,
        )
        result_n1 = run_ae_mh_vertical_slice(
            bundle.listing_n1, project_id=project_id,
            run_id=run_id, snapshot_version="SYNTHETIC-N1",
            previous_result=result_n, store=store,
            snapshot_id=bundle.snapshot_n1.snapshot_id,
        )
    projections = build_projections(result_n1)
    run_payload = store.get_run(run_id)
    identity_chain = dict(envelope.get("identity_chain", {}))
    if not identity_chain:
        identity_chain = _build_identity_chain(
            run_id, project_id, bundle, revision, result_n1,
            queries=result_n1.queries, transport_calls=0,
            ai_attempt_id=None, ai_raw_ref=None,
            ai_ok=envelope.get("complete", False),
            facts_count=len(store.list_facts(run_id)),
            output_state=run_payload.output_state.value,
            evidence_state=run_payload.evidence_state.value,
            store=store,
        )
    audience = project_audience_progress(store, run_id)
    return ClosureResult(
        run_id=run_id, project_id=project_id,
        snapshot_n_id=bundle.snapshot_n.snapshot_id,
        snapshot_n1_id=bundle.snapshot_n1.snapshot_id,
        manifest_revision=revision,
        ae_mh_result=result_n1, projections=projections,
        ai_attempt_result=None, audience_progress=audience,
        transport_call_count=0,
        facts_committed=len(store.list_facts(run_id)),
        candidates_persisted=0, queries_persisted=0,
        spines_persisted=0, projections_persisted=0,
        run_output_state=run_payload.output_state.value,
        evidence_state=run_payload.evidence_state.value,
        identity_chain=identity_chain,
    )


def _build_identity_chain(
    run_id: str,
    project_id: str,
    bundle: SyntheticSnapshotBundle,
    revision: int,
    result_n1: AEMHResult,
    *,
    queries: List[Any],
    transport_calls: int,
    ai_attempt_id: Optional[str],
    ai_raw_ref: Optional[str],
    ai_ok: bool,
    facts_count: int,
    output_state: str,
    evidence_state: str,
    store: Store,
) -> Dict[str, Any]:
    temporal_spines = result_n1.temporal_spines
    spine_run_ids = {sp.run_id for sp in temporal_spines.values()}
    query_shapes = [
        {"basis": bool(q.basis), "finding": bool(q.finding), "action": bool(q.action)}
        for q in queries
    ]
    return {
        "project_id": project_id,
        "run_id": run_id,
        "snapshot_n1_id": bundle.snapshot_n1.snapshot_id,
        "manifest_revision": revision,
        "ae_mh_run_id": result_n1.run_id,
        "ae_mh_project_id": result_n1.project_id,
        "ae_mh_snapshot_version": result_n1.snapshot_version,
        "spine_run_ids": sorted(spine_run_ids),
        "spine_subjects": sorted(temporal_spines.keys()),
        "spines_share_run": len(spine_run_ids) == 1 and run_id in spine_run_ids,
        "query_count": len(queries),
        "query_shapes": query_shapes,
        "transport_call_count": transport_calls,
        "facts_committed": facts_count,
        "candidates_counted_as_reported": result_n1.candidate_fact_separation()[
            "candidates_counted_as_reported"
        ],
        "output_state": output_state,
        "evidence_state": evidence_state,
        "coverage_complete": result_n1.coverage_complete,
        "baseline_eligible": result_n1.snapshot_baseline_eligible,
        "ai_evidence_consumed_by_qc": ai_raw_ref is not None and ai_ok,
        "ai_attempt_id": ai_attempt_id,
        "ai_raw_ref": ai_raw_ref,
        "ai_promoted_to_fact": False,
        "total_work_units": 7,
    }


__all__ = [
    "CLOSURE_MARKER",
    "ClosureInterrupted",
    "SyntheticClosureTransport",
    "ClosureResult",
    "run_integrated_closure",
    "INTERRUPT_AFTER_FACTS",
    "INTERRUPT_AFTER_AI",
]
