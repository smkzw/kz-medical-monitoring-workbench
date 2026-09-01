"""Framework-neutral domain schema for the medical monitoring R1 POC.

Worker_01 public contract (see context/medical_monitoring_ai_native_r1_slice1_20260809_execution_context.md):

* Orthogonal states: ``analysis_state``, ``evidence_state``, ``review_state``,
  ``output_state`` -- never folded into a single done/complete flag.
* Snapshot acceptance chain: ``imported -> structurally_valid -> mapping_reviewed
  -> snapshot_accepted -> baseline_eligible``; ambiguity fails closed.
* ``ArtifactEnvelope`` carries expected/produced coverage and
  ``complete|partial|truncated|not_evaluable|failed``; incomplete artifacts are
  never publishable.
* Graph IR node types fixed to ``deterministic_service|ai_candidate|
  human_decision|projection``.
* Canonical JSON content addressing; SQLite is the authoritative state.

This module is pure schema + serialization: no storage, no execution, no
framework types.  All domain objects round-trip through :func:`to_jsonable` /
:func:`from_jsonable` so the SQLite store can persist them as canonical JSON.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import typing
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """UTC ISO-8601 timestamp used across the POC (lexicographically sortable)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def new_id(prefix: str = "") -> str:
    """Short random identifier; optional prefix for debuggability."""
    return (prefix + uuid.uuid4().hex)[:64]


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8.

    This is THE canonical form used for content addressing and audit payloads.
    Non-finite floats (NaN/Infinity) are rejected (allow_nan=False): they are
    not valid JSON and must never enter authoritative hashes.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(obj: Any) -> str:
    """Content address of any JSON-able object (sha256 of canonical JSON)."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))


# ---------------------------------------------------------------------------
# Orthogonal states (Design v1.1 section 5.1)
# ---------------------------------------------------------------------------

class AnalysisState(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    FAILED = "failed"


class EvidenceState(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    NOT_EVALUABLE = "not_evaluable"
    CONFLICTED = "conflicted"


class ReviewState(str, Enum):
    NOT_REQUIRED = "not_required"
    DETERMINISTIC_VERIFIED = "deterministic_verified"
    INDEPENDENT_AI_REVIEWED = "independent_ai_reviewed"
    NEEDS_USER_ATTENTION = "needs_user_attention"
    USER_CONFIRMED = "user_confirmed"


class OutputState(str, Enum):
    NOT_PUBLISHED = "not_published"
    DASHBOARD_VISIBLE = "dashboard_visible"
    DRAFT_EXPORTABLE = "draft_exportable"
    EXPORTED = "exported"


class UserDisposition(str, Enum):
    """Recorded ONLY when the user actually confirms/edits/rejects/exports."""
    CONFIRMED = "confirmed"
    EDITED = "edited"
    REJECTED = "rejected"
    EXPORTED = "exported"


# ---------------------------------------------------------------------------
# Snapshot acceptance chain (Design v1.1 section 6.2)
# ---------------------------------------------------------------------------

class SnapshotAcceptanceState(str, Enum):
    IMPORTED = "imported"
    STRUCTURALLY_VALID = "structurally_valid"
    MAPPING_REVIEWED = "mapping_reviewed"
    SNAPSHOT_ACCEPTED = "snapshot_accepted"
    BASELINE_ELIGIBLE = "baseline_eligible"


ACCEPTANCE_CHAIN: List[SnapshotAcceptanceState] = [
    SnapshotAcceptanceState.IMPORTED,
    SnapshotAcceptanceState.STRUCTURALLY_VALID,
    SnapshotAcceptanceState.MAPPING_REVIEWED,
    SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
    SnapshotAcceptanceState.BASELINE_ELIGIBLE,
]

# Acceptance subjects (Design v1.1 section 6.2 / conference disposition 3.2)
ACCEPTED_BY_SYSTEM_POLICY = "system_policy"


# ---------------------------------------------------------------------------
# Artifact coverage (Design v1.1 sections 5, 12; execution context contract)
# ---------------------------------------------------------------------------

class ArtifactCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    NOT_EVALUABLE = "not_evaluable"
    FAILED = "failed"


class CoverageUnitStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    FAILED = "failed"
    MISSING = "missing"


# Coverage scopes required by Design v1.1 section 12 (at least):
# source/table/row/subject/site/risk-domain.
SCOPE_SOURCE = "source"
SCOPE_TABLE = "table"
SCOPE_ROW = "row"
SCOPE_SUBJECT = "subject"
SCOPE_SITE = "site"
SCOPE_RISK_DOMAIN = "risk_domain"
SCOPE_REPORT_UNIT = "report_unit"
SCOPE_OTHER = "other"

# Artifact payload roles: candidates must never be promoted to facts.
PAYLOAD_ROLE_FACTS = "facts"
PAYLOAD_ROLE_INFERENCE = "inference"
PAYLOAD_ROLE_CANDIDATE = "candidate"
PAYLOAD_ROLE_SUGGESTION = "suggestion"
PAYLOAD_ROLE_QUERY_DRAFT = "query_draft"
PAYLOAD_ROLE_PROJECTION = "projection"
PAYLOAD_ROLE_RAW_MODEL_OUTPUT = "raw_model_output"
PAYLOAD_ROLE_LEDGER = "ledger"
PAYLOAD_ROLE_REPORT = "report"

# Risk candidate types (Design v1.1 section 10.3).  Candidates are risk
# candidates, NEVER formal AE/MH facts.
RISK_TYPE_POTENTIAL_UNREPORTED_AE = "potential_unreported_ae"
RISK_TYPE_POTENTIAL_UNREPORTED_MH = "potential_unreported_mh"


# ---------------------------------------------------------------------------
# Graph node types (Design v1.1 section 5.2 / 8.2) and node statuses
# ---------------------------------------------------------------------------

class NodeType(str, Enum):
    DETERMINISTIC_SERVICE = "deterministic_service"
    AI_CANDIDATE = "ai_candidate"
    HUMAN_DECISION = "human_decision"
    PROJECTION = "projection"


NODE_TYPES: Tuple[NodeType, ...] = (
    NodeType.DETERMINISTIC_SERVICE,
    NodeType.AI_CANDIDATE,
    NodeType.HUMAN_DECISION,
    NodeType.PROJECTION,
)


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    REUSED = "reused"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"
    FAILED = "failed"


TERMINAL_NODE_STATUSES: Tuple[NodeStatus, ...] = (
    NodeStatus.PASSED,
    NodeStatus.REUSED,
    NodeStatus.SKIPPED,
    NodeStatus.NOT_APPLICABLE,
    NodeStatus.BLOCKED,
    NodeStatus.FAILED,
)

# Statuses that satisfy a dependent node's precondition.
DEPENDENCY_SATISFYING_STATUSES: Tuple[NodeStatus, ...] = (
    NodeStatus.PASSED,
    NodeStatus.REUSED,
    NodeStatus.SKIPPED,
    NodeStatus.NOT_APPLICABLE,
)


class RunMode(str, Enum):
    DAILY = "daily"
    PRE_LOCK = "pre_lock"
    POST_LOCK_PRE_CFDI = "post_lock_pre_cfdi"


class ExecutionBasis(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class RiskLifecycleState(str, Enum):
    ESTABLISHED = "established"
    ESCALATED = "escalated"
    DE_ESCALATED = "de_escalated"
    CLOSED = "closed"
    REOPENED = "reopened"
    SUPERSEDED = "superseded"
    NOT_EVALUABLE = "not_evaluable"
    RESOLVED_BY_DATA = "resolved_by_data"


# ---------------------------------------------------------------------------
# Audit event types (append-only, hash-chained)
# ---------------------------------------------------------------------------

EVENT_PROJECT_CREATED = "project_created"
EVENT_SOURCE_ADDED = "source_added"
EVENT_SNAPSHOT_ADDED = "snapshot_added"
EVENT_ACCEPTANCE_TRANSITION = "snapshot_acceptance_transition"
EVENT_ACCEPTANCE_AMBIGUITY_SET = "snapshot_acceptance_ambiguity_set"
EVENT_ACCEPTANCE_AMBIGUITY_CLEARED = "snapshot_acceptance_ambiguity_cleared"
EVENT_ACCEPTANCE_REJECTED = "snapshot_acceptance_rejected"
EVENT_RUN_CREATED = "run_created"
EVENT_RUN_STATE_CHANGED = "run_state_changed"
EVENT_MANIFEST_SET = "manifest_set"
EVENT_NODE_BEGIN = "node_begin"
EVENT_NODE_COMPLETE = "node_complete"
EVENT_NODE_REJECTED = "node_rejected"
EVENT_WORK_UNIT_BEGIN = "work_unit_begin"
EVENT_WORK_UNIT_ATTEMPT_BOUND = "work_unit_attempt_bound"
EVENT_WORK_UNIT_COMPLETE = "work_unit_complete"
EVENT_CAPABILITY_ATTEMPT_DECLARED = "capability_attempt_declared"
EVENT_CAPABILITY_ATTEMPT_CLAIMED = "capability_attempt_claimed"
EVENT_CAPABILITY_ATTEMPT_INTERRUPTED = "capability_attempt_interrupted"
EVENT_CAPABILITY_ATTEMPT_TERMINAL = "capability_attempt_terminal"
EVENT_CAPABILITY_ATTEMPT_REJECTED = "capability_attempt_rejected"
EVENT_ARTIFACT_COMMITTED = "artifact_committed"
EVENT_FACT_COMMITTED = "fact_committed"
EVENT_DOMAIN_OBJECT_PUT = "domain_object_put"
EVENT_CHECKPOINT_SAVED = "checkpoint_saved"
EVENT_PUBLISH_ADVANCED = "publish_advanced"
EVENT_ORPHAN_CLEANUP = "orphan_cleanup"
EVENT_RECOVERY = "recovery"
EVENT_IDEMPOTENT_REPLAY = "idempotent_replay"
EVENT_IDEMPOTENCY_CONFLICT = "idempotency_conflict"
EVENT_PROMOTION_REJECTED = "promotion_rejected"


# ---------------------------------------------------------------------------
# Exceptions (public contract; storage/execution layers raise these)
# ---------------------------------------------------------------------------

class MmR1Error(Exception):
    """Base class for all POC errors."""


class StoreError(MmR1Error):
    """Generic authoritative-store violation."""


class AcceptanceChainError(StoreError):
    """Illegal snapshot acceptance transition (jump/rewind)."""


class AmbiguityBlocksAcceptanceError(StoreError):
    """Identity/mapping/source-scope ambiguity blocks snapshot acceptance."""


class CompletionGateError(StoreError):
    """analysis_complete / publication gate failed; fail closed, no state change."""

    def __init__(self, reasons: List[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons) or "completion gate failed")


class StaleCallbackError(StoreError):
    """Attempt callback arrived after the node was already closed/terminal."""


class NodeTerminalError(StoreError):
    """Node already terminal; re-execution requires an explicit manifest revision."""


class IdempotencyConflictError(StoreError):
    """Same idempotency key replayed with different payload -- never overwrite."""


class ArtifactCollisionError(StoreError):
    """Same content address produced different bytes (corruption / collision)."""


class PromotionForbiddenError(StoreError):
    """AI/adapter node attempted to promote facts/baseline/user-confirmation."""


class GraphValidationError(MmR1Error):
    """Graph IR structure or handler registration violation."""


# ---------------------------------------------------------------------------
# JSON codec (canonical, dataclass/enum aware)
# ---------------------------------------------------------------------------

def to_jsonable(obj: Any) -> Any:
    """Convert domain objects/enums/collections to plain JSON-able structures."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Mapping):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    raise TypeError(
        f"object of type {type(obj).__name__!r} is not JSON-able; refusing to stringify "
        "it into an authoritative hash"
    )


def _coerce_field(ftype: Any, value: Any) -> Any:
    origin = typing.get_origin(ftype)
    if origin is Union:
        args = [a for a in typing.get_args(ftype) if a is not type(None)]
        if len(args) == 1:
            return _coerce_field(args[0], value)
        return value
    if origin in (list, typing.List):
        args = typing.get_args(ftype)
        if args:
            return [_coerce_field(args[0], v) for v in value]
        return list(value)
    if origin in (dict, typing.Dict):
        return dict(value)
    if isinstance(ftype, type):
        if issubclass(ftype, Enum):
            return ftype(value)
        if dataclasses.is_dataclass(ftype):
            return from_jsonable(ftype, value)
    return value


def from_jsonable(cls: Any, data: Any) -> Any:
    """Reconstruct a domain object from JSON-able data (inverse of to_jsonable)."""
    if data is None:
        return None
    if isinstance(cls, type):
        if issubclass(cls, Enum):
            return cls(data)
        if dataclasses.is_dataclass(cls):
            hints = typing.get_type_hints(cls)
            kwargs: Dict[str, Any] = {}
            for f in dataclasses.fields(cls):
                if f.name in data and data[f.name] is not None:
                    kwargs[f.name] = _coerce_field(hints.get(f.name, f.type), data[f.name])
            return cls(**kwargs)
    return data


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageUnit:
    scope: str                      # SCOPE_SOURCE / SCOPE_TABLE / SCOPE_ROW / SCOPE_SUBJECT / SCOPE_SITE / SCOPE_RISK_DOMAIN / SCOPE_REPORT_UNIT / SCOPE_OTHER
    key: str                        # unit identifier within the scope
    expected: bool = True           # True when declared as an expected input unit
    status: Optional[CoverageUnitStatus] = None
    reason: Optional[str] = None    # mandatory for NOT_APPLICABLE / NOT_EVALUABLE


@dataclass
class CoverageManifest:
    """Deterministic expected/produced coverage reconciliation (Design 5/12)."""
    expected: List[CoverageUnit] = field(default_factory=list)
    produced: List[CoverageUnit] = field(default_factory=list)
    reconciled: bool = False

    def reconcile(self) -> "CoverageManifest":
        """Map produced units onto expected units; unreasoned gaps become MISSING.

        Deterministic and fail-closed: an expected unit with no produced
        counterpart (and no explicit status) is MISSING.
        """
        produced_by_key: Dict[Tuple[str, str], CoverageUnit] = {}
        for u in self.produced:
            produced_by_key.setdefault((u.scope, u.key), u)
        rebuilt: List[CoverageUnit] = []
        for e in self.expected:
            if e.status is not None:
                rebuilt.append(e)
                continue
            p = produced_by_key.get((e.scope, e.key))
            if p is not None:
                rebuilt.append(CoverageUnit(
                    scope=e.scope, key=e.key, expected=True,
                    status=p.status or CoverageUnitStatus.COVERED, reason=p.reason,
                ))
            else:
                rebuilt.append(CoverageUnit(
                    scope=e.scope, key=e.key, expected=True,
                    status=CoverageUnitStatus.MISSING, reason=None,
                ))
        self.expected = rebuilt
        self.reconciled = True
        return self

    def uncovered_units(self) -> List[CoverageUnit]:
        return [u for u in self.expected if not self._unit_ok(u)]

    def is_fully_covered(self) -> Tuple[bool, List[str]]:
        if not self.reconciled:
            return False, ["coverage manifest not reconciled"]
        reasons: List[str] = []
        for u in self.expected:
            if u.status in (CoverageUnitStatus.PARTIAL, CoverageUnitStatus.TRUNCATED,
                            CoverageUnitStatus.FAILED, CoverageUnitStatus.MISSING):
                reasons.append(f"{u.scope}:{u.key} -> {u.status.value}")
            elif u.status in (CoverageUnitStatus.NOT_APPLICABLE, CoverageUnitStatus.NOT_EVALUABLE) and not u.reason:
                reasons.append(f"{u.scope}:{u.key} -> {u.status.value} without reason")
        return (len(reasons) == 0), reasons

    @staticmethod
    def _unit_ok(u: CoverageUnit) -> bool:
        if u.status in (CoverageUnitStatus.COVERED,):
            return True
        if u.status in (CoverageUnitStatus.NOT_APPLICABLE, CoverageUnitStatus.NOT_EVALUABLE):
            return bool(u.reason)
        return False


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    content_hash: str


@dataclass
class RetryPolicy:
    max_attempts: int = 1


@dataclass
class Checkpoint:
    checkpoint_id: str = ""
    run_id: str = ""
    node_id: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    created_at: str = ""


# ---------------------------------------------------------------------------
# Source / snapshot entities
# ---------------------------------------------------------------------------

@dataclass
class StudyProject:
    project_id: str
    name: str
    is_synthetic: bool = True       # POC guard: only SYNTHETIC fixtures allowed
    created_at: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceRevision:
    revision_id: str
    project_id: str
    source_type: str                # protocol | ib | listing | report | other
    version: str
    content_hash: str = ""
    valid_from: Optional[str] = None
    scope: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class ListingSnapshot:
    snapshot_id: str
    project_id: str
    revision_id: str
    snapshot_version: str
    content_hash: str = ""
    row_count: int = 0
    structure: Dict[str, Any] = field(default_factory=dict)
    is_synthetic: bool = True
    created_at: str = ""


@dataclass
class SnapshotAcceptance:
    snapshot_id: str
    state: SnapshotAcceptanceState
    accepted_by: Optional[str] = None
    ambiguity: Optional[Dict[str, Any]] = None
    blocked: bool = False
    reason: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class SnapshotBaselineProof:
    """Projection of a snapshot acceptance record for dashboards/audit exports.

    This object is **not** an authority token.  Public AE/MH entry points
    (``run_ae_mh_vertical_slice``, ``merge_risk_identities``,
    ``split_risk_identity``) authorize baseline-dependent resolution/merge/split
    only by reading the live Store acceptance row via ``store`` + ``snapshot_id``.
    A proof built by :meth:`from_acceptance`, by the dataclass constructor, or by
    any helper—including one with ``store_verified=True``—must fail closed when
    used alone and must never override a non-eligible Store record.
    """

    snapshot_id: str
    state: SnapshotAcceptanceState
    accepted_by: Optional[str] = None
    blocked: bool = False
    ambiguity: Optional[Dict[str, Any]] = None
    reason: str = ""
    evidence_hash: str = ""
    store_verified: bool = False

    @classmethod
    def from_acceptance(cls, acceptance: "SnapshotAcceptance") -> "SnapshotBaselineProof":
        """Project an acceptance record into a portable evidence view.

        Does not grant lifecycle authority.  ``store_verified`` here means
        "derived from an acceptance dataclass", not "consulted the Store".
        """
        payload = {
            "snapshot_id": acceptance.snapshot_id,
            "state": acceptance.state.value,
            "accepted_by": acceptance.accepted_by,
            "blocked": acceptance.blocked,
            "ambiguity": acceptance.ambiguity,
            "reason": acceptance.reason,
        }
        return cls(
            snapshot_id=acceptance.snapshot_id,
            state=acceptance.state,
            accepted_by=acceptance.accepted_by,
            blocked=acceptance.blocked,
            ambiguity=dict(acceptance.ambiguity) if acceptance.ambiguity else None,
            reason=acceptance.reason or "",
            evidence_hash=content_hash(payload),
            store_verified=True,
        )

    @property
    def is_baseline_eligible(self) -> bool:
        """Projected eligibility view only; not an authority decision."""
        return (
            not self.blocked
            and self.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
        )


# ---------------------------------------------------------------------------
# Run / manifest / node entities
# ---------------------------------------------------------------------------

@dataclass
class MonitoringRun:
    run_id: str
    project_id: str
    mode: RunMode
    data_cutoff: str
    source_revision_id: str
    execution_basis: ExecutionBasis
    analysis_state: AnalysisState = AnalysisState.NOT_STARTED
    evidence_state: EvidenceState = EvidenceState.NOT_EVALUABLE
    review_state: ReviewState = ReviewState.NOT_REQUIRED
    output_state: OutputState = OutputState.NOT_PUBLISHED
    user_disposition: Optional[UserDisposition] = None
    manifest_revision: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ManifestNode:
    node_id: str
    node_type: NodeType
    handler: str = ""
    description: str = ""
    mandatory: bool = True
    max_attempts: int = 1          # retry policy frozen into the manifest
    artifact_required: bool = True  # state-only/QC nodes opt out explicitly
    depends_on: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ManifestWorkUnit:
    """Audience-readable, manifest-frozen unit used as the progress denominator.

    A work unit is deliberately smaller than a graph node: subjects, sites,
    risk domains and report/QC sections can each be counted independently.
    Runtime state is stored separately and is always bound to one manifest
    revision.
    """

    work_unit_id: str
    node_id: str
    label: str
    stage: str
    scope: str
    target_ref: str
    ordinal: int
    mandatory: bool = True
    depends_on: List[str] = field(default_factory=list)


@dataclass
class ExecutionManifest:
    run_id: str
    nodes: List[ManifestNode]
    work_units: List[ManifestWorkUnit] = field(default_factory=list)
    revision: int = 0
    graph_id: str = ""              # frozen Graph IR identity (idempotency key prefix)
    edges: List[Dict[str, Any]] = field(default_factory=list)  # {src, dst, condition}
    source_coverage: List[str] = field(default_factory=list)
    identity_algorithm: str = ""
    knowledge_version: str = ""
    rule_version: str = ""
    graph_version: str = ""
    schema_version: str = ""
    adapter_profile: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def total_units(self) -> int:
        return len(self.work_units) if self.work_units else len(self.nodes)

    def node_ids(self) -> List[str]:
        return [n.node_id for n in self.nodes]


@dataclass
class NodeRun:
    run_id: str
    node_id: str
    node_type: NodeType
    manifest_revision: int = 0
    status: NodeStatus = NodeStatus.PENDING
    idempotency_key: str = ""
    attempts: int = 0
    artifact_id: Optional[str] = None
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    reason: Optional[str] = None
    started_at: str = ""
    finished_at: str = ""


@dataclass
class NodeAttempt:
    run_id: str
    node_id: str
    attempt_seq: int
    idempotency_key: str          # attempt-scoped key ("<logical>#a<seq>")
    status: NodeStatus
    manifest_revision: int = 0
    payload_hash: Optional[str] = None   # canonical outcome fingerprint
    created_at: str = ""
    logical_key: str = ""          # stable logical node-operation key (replay identity)


@dataclass
class WorkUnitRun:
    run_id: str
    manifest_revision: int
    work_unit_id: str
    node_id: str
    status: NodeStatus = NodeStatus.PENDING
    idempotency_key: str = ""
    begin_hash: str = ""
    detail: str = ""
    execution_identity: Dict[str, str] = field(default_factory=dict)
    evidence_count: int = 0
    completion_hash: str = ""
    started_at: str = ""
    finished_at: str = ""
    updated_at: str = ""


# ---------------------------------------------------------------------------
# Artifact envelope (Design v1.1 sections 5, 12; execution context contract)
# ---------------------------------------------------------------------------

@dataclass
class ArtifactEnvelope:
    artifact_type: str
    version: str
    run_id: str
    node_id: str
    node_type: NodeType
    payload: Dict[str, Any]
    payload_role: str = PAYLOAD_ROLE_INFERENCE
    input_hashes: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    coverage: Optional[CoverageManifest] = None
    completeness: ArtifactCompleteness = ArtifactCompleteness.COMPLETE
    supersedes: Optional[str] = None
    qc_status: Optional[str] = None
    artifact_id: str = ""           # assigned at commit (== content_hash)
    content_hash: str = ""          # assigned at commit
    created_at: str = ""            # assigned at commit

    def content_dict(self) -> Dict[str, Any]:
        """Canonical content: everything except commit-assigned fields."""
        return {
            "artifact_type": self.artifact_type,
            "version": self.version,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "payload": to_jsonable(self.payload),
            "payload_role": self.payload_role,
            "input_hashes": list(self.input_hashes),
            "evidence_refs": list(self.evidence_refs),
            "coverage": to_jsonable(self.coverage),
            "completeness": self.completeness.value,
            "supersedes": self.supersedes,
            "qc_status": self.qc_status,
        }

    def canonical_hash(self) -> str:
        return content_hash(self.content_dict())

    def derive_completeness(self) -> ArtifactCompleteness:
        """Deterministic completeness derived from the reconciled coverage."""
        cov = self.coverage
        if cov is None or not cov.reconciled:
            return ArtifactCompleteness.NOT_EVALUABLE
        statuses = [u.status for u in cov.expected]
        # NOTE: statuses hold CoverageUnitStatus values, not ArtifactCompleteness.
        if CoverageUnitStatus.FAILED in statuses:
            return ArtifactCompleteness.FAILED
        if CoverageUnitStatus.TRUNCATED in statuses:
            return ArtifactCompleteness.TRUNCATED
        if CoverageUnitStatus.PARTIAL in statuses or CoverageUnitStatus.MISSING in statuses:
            return ArtifactCompleteness.PARTIAL
        if any(u.status == CoverageUnitStatus.NOT_EVALUABLE and not u.reason for u in cov.expected):
            return ArtifactCompleteness.NOT_EVALUABLE
        return ArtifactCompleteness.COMPLETE

    def is_publishable(self) -> Tuple[bool, List[str]]:
        """Publication gate: BOTH declared and derived completeness must be complete.

        Fail closed: partial/truncated/not_evaluable/failed envelopes are never
        publishable, and unreconciled or gap-ridden coverage blocks publication.
        """
        reasons: List[str] = []
        if self.completeness != ArtifactCompleteness.COMPLETE:
            reasons.append(f"declared completeness is '{self.completeness.value}'")
        derived = self.derive_completeness()
        if derived != ArtifactCompleteness.COMPLETE:
            reasons.append(f"derived completeness is '{derived.value}'")
        if self.coverage is not None:
            ok, cov_reasons = self.coverage.is_fully_covered()
            if not ok:
                reasons.extend(cov_reasons)
        return (len(reasons) == 0), reasons


# ---------------------------------------------------------------------------
# Facts / risks / queries / projections
# ---------------------------------------------------------------------------

@dataclass
class CanonicalFact:
    fact_type: str
    body: Dict[str, Any]
    subject_id: Optional[str] = None
    site_id: Optional[str] = None
    source_refs: List[str] = field(default_factory=list)
    fact_id: str = ""
    fact_hash: str = ""

    def content_dict(self) -> Dict[str, Any]:
        return {
            "fact_type": self.fact_type,
            "subject_id": self.subject_id,
            "site_id": self.site_id,
            "body": to_jsonable(self.body),
        }

    def canonical_hash(self) -> str:
        return content_hash(self.content_dict())


@dataclass(frozen=True)
class RiskIdentity:
    """Stable risk identity (Design v1.1 section 10.1)."""
    project_id: str
    scope: str                      # subject | site | project
    subject_id: Optional[str]
    site_id: Optional[str]
    risk_domain: str
    event_identity: str
    normalized_concept: str
    temporal_window: str
    lineage: str
    algorithm_version: str

    def stable_key(self) -> str:
        return content_hash(to_jsonable(self))


@dataclass
class RiskCandidate:
    """Risk candidate -- NEVER a formal AE/MH fact (Design v1.1 section 10.3)."""
    candidate_id: str
    run_id: str
    node_id: str
    risk_type: str                  # RISK_TYPE_POTENTIAL_UNREPORTED_AE / _MH / ...
    risk_domain: str
    subject_id: Optional[str]
    site_id: Optional[str]
    identity: RiskIdentity
    severity: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class RiskInstance:
    instance_id: str
    run_id: str
    identity_key: str
    lifecycle_state: RiskLifecycleState
    identity_ambiguous: bool = False
    current_severity: Optional[str] = None
    opened_at: str = ""
    updated_at: str = ""


@dataclass
class RiskTransition:
    transition_id: str
    instance_id: str
    from_state: Optional[RiskLifecycleState]
    to_state: RiskLifecycleState
    kind: str                       # establish|escalate|de_escalate|close|reopen|merge|split|supersede|not_evaluable|resolve
    reason: str
    evidence_refs: List[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class QueryDraft:
    """Three-part Query (Design v1.1 section 10.2): basis + finding + action."""
    query_id: str
    run_id: str
    basis: str
    finding: str
    action: str
    subject_id: Optional[str] = None
    site_id: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    status: str = "draft"           # draft | user_confirmed | exported
    created_at: str = ""


@dataclass
class TemporalEvent:
    event_id: str
    subject_id: str
    event_type: str
    actual_date: Optional[str] = None
    study_day: Optional[int] = None
    visit_label: Optional[str] = None
    phase: Optional[str] = None
    source_refs: List[str] = field(default_factory=list)


@dataclass
class SubjectTemporalSpine:
    subject_id: str
    run_id: str
    events: List[TemporalEvent] = field(default_factory=list)

    def chronological(self) -> List[TemporalEvent]:
        return sorted(self.events, key=lambda e: (e.actual_date is None, e.actual_date or "", e.event_id))


@dataclass
class ReferenceBaselineEntry:
    entry_id: str
    risk_identity_key: str
    evaluation: str                 # confirmed|partially_supported|unsupported|outdated|insufficient_evidence|not_applicable
    evidence_refs: List[str] = field(default_factory=list)
    note: str = ""


@dataclass
class ReferenceBaseline:
    run_id: str
    entries: List[ReferenceBaselineEntry] = field(default_factory=list)


@dataclass
class ProjectionVersion:
    projection_id: str
    run_id: str
    project_id: str
    kind: str                       # dashboard|site|subject_profile|subject_timeline|report|export
    version: int
    subject_id: Optional[str] = None
    site_id: Optional[str] = None
    artifact_ref: Optional[str] = None
    source_hash: str = ""
    created_at: str = ""


# ---------------------------------------------------------------------------
# Mode contract (Design v1.1 section 6.4; worker_03 implements the modes)
# ---------------------------------------------------------------------------

@dataclass
class ModeContract:
    mode: RunMode
    entry_conditions: List[str]
    cutoff_policy: str
    revision_policy: str
    carry_forward_policy: str
    output_eligibility: List[str]
    immutable: bool = True          # mode cannot change in place; change => new run

    def validate_run(self, run: MonitoringRun) -> List[str]:
        """Fail-closed compatibility check between a run and this contract."""
        problems: List[str] = []
        if run.mode != self.mode:
            problems.append(f"run mode '{run.mode.value}' != contract mode '{self.mode.value}'")
        if run.mode == RunMode.POST_LOCK_PRE_CFDI and run.manifest_revision > 1:
            problems.append("post-lock/pre-CFDI runs must not revise the frozen manifest in place")
        return problems


# ---------------------------------------------------------------------------
# AI capability adapter contract (Design v1.1 section 9; worker_03 implements)
# ---------------------------------------------------------------------------

@dataclass
class AdapterBinding:
    binding_id: str
    capability: str
    provider: str
    model: str
    selector: str = ""
    effort: str = ""
    adapter_version: str = ""
    input_hash: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    isolation: str = ""
    timeout_seconds: Optional[int] = None
    endpoint: str = "local"         # local | external (user-chosen execution endpoint)
    created_at: str = ""


@dataclass
class ModelAnalysis:
    analysis_id: str
    binding_id: str
    run_id: str
    node_id: str
    input_hash: str
    raw_output_ref: str = ""        # artifact id of the raw output (never rewritten)
    parse_state: str = "complete"   # complete|partial|truncated|failed|cancelled|timeout
    coverage: Optional[CoverageManifest] = None
    failure_reason: Optional[str] = None
    created_at: str = ""


@dataclass
class AdapterContract:
    binding: AdapterBinding
    status: str = "configured"      # configured|running|complete|partial|truncated|failed|cancelled|timeout
    analysis: Optional[ModelAnalysis] = None

    def candidate_only(self) -> bool:
        """Adapters may only produce candidate artifacts -- never facts."""
        return True


# ---------------------------------------------------------------------------
# Report claim coverage (Design v1.1 section 13; worker_03 implements logic)
# ---------------------------------------------------------------------------

REPORT_UNIT_BODY = "body"
REPORT_UNIT_TABLE = "table"
REPORT_UNIT_FIGURE = "figure"
REPORT_UNIT_FOOTNOTE = "footnote"


@dataclass
class ReportUnitRef:
    unit_type: str                  # body|table|figure|footnote
    unit_id: str
    page: Optional[str] = None
    anchor: str = ""


@dataclass
class ClaimCoverageEntry:
    unit: ReportUnitRef
    claim_id: Optional[str] = None
    status: str = "no_claim"        # claimed|no_claim|not_evaluable|partial|truncated
    evidence_refs: List[str] = field(default_factory=list)
    reason: Optional[str] = None


@dataclass
class ClaimCoverageLedger:
    ledger_id: str
    run_id: str
    report_artifact_id: str = ""
    entries: List[ClaimCoverageEntry] = field(default_factory=list)

    def is_complete(self) -> Tuple[bool, List[str]]:
        """Fail closed: any partial/truncated entry, or unreasoned not_evaluable,
        blocks the 'full report reviewed' claim."""
        reasons: List[str] = []
        for e in self.entries:
            if e.status in ("partial", "truncated"):
                reasons.append(f"{e.unit.unit_type}:{e.unit.unit_id} -> {e.status}")
            elif e.status == "not_evaluable" and not e.reason:
                reasons.append(f"{e.unit.unit_type}:{e.unit.unit_id} -> not_evaluable without reason")
        return (len(reasons) == 0), reasons


@dataclass
class ReportClaim:
    claim_id: str
    text: str
    status: str                     # supported|partially_supported|unsupported|outdated_wrong_cutoff|overstated|understated|internally_inconsistent|not_evaluable
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class ReviewIssue:
    issue_id: str
    claim_id: str
    issue_type: str
    severity: str = "info"
    anchor: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    note: str = ""


@dataclass
class AuditEvent:
    seq: int
    event_type: str
    payload: Dict[str, Any]
    payload_hash: str
    prev_hash: str
    chain_hash: str
    run_id: Optional[str] = None
    created_at: str = ""
