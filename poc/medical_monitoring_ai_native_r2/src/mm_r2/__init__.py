"""mm_r2 -- framework-neutral R2 domain kernel for the medical monitoring
AI-native POC (synthetic fixtures only).

Batch A public surface (worker_01):
* schema registry (:mod:`mm_r2.schema_registry`)
* immutable domain entities (:mod:`mm_r2.domain`)
* record/risk identity (:mod:`mm_r2.identity`)
* content-addressed artifacts (:mod:`mm_r2.artifacts`)
* snapshot acceptance chain (:mod:`mm_r2.acceptance`)

Batches B and C extend this package; only minimal ``__init__`` re-exports
are permitted by downstream workers.
"""

from .schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaVersion,
    default_registry,
)

from .domain import (
    CanonicalFact,
    DomainValidationError,
    HashMismatchError,
    ImmutableDict,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    MmR2Error,
    Provenance,
    ProvenanceError,
    RuleActivation,
    SourceRevision,
    StudyKnowledgePack,
    StudyProject,
    canonical_json,
    content_hash,
    deep_freeze_json,
    from_dictable,
    new_id,
    now_iso,
    sha256_hex,
    to_dictable,
    validate_sha256_hex,
)
from .identity import (
    AmbiguousIdentity,
    IdentityAmbiguityError,
    IdentityResolution,
    RecordIdentity,
    ResolvedRiskIdentity,
    RiskIdentity,
    make_record_identity,
    make_risk_identity,
)

from .artifacts import (
    ArtifactCollisionError,
    ArtifactCompleteness,
    ArtifactEnvelope,
    ArtifactStore,
    ArtifactStoreError,
    EvidenceState,
    StoredArtifact,
    make_envelope,
)

from .acceptance import (
    ACCEPTANCE_CHAIN,
    ACCEPTED_BY_SYSTEM_POLICY,
    AcceptanceChainError,
    AcceptanceDecisionRecord,
    AcceptanceEvidence,
    AcceptanceProof,
    AcceptanceService,
    CoverageGap,
    EligibilityBlockedError,
    SnapshotAcceptanceRecord,
    SnapshotAcceptanceState,
    SnapshotBinding,
)

from .risk import (
    AdjudicationError,
    AdjudicationOutcome,
    AdjudicationRecord,
    CANDIDATE_AUTO_PROMOTE_FORBIDDEN,
    IllegalTransitionError,
    RiskCandidate,
    RiskError,
    RiskInstance,
    RiskLifecycle,
    RiskLifecycleState,
    RiskTransition,
    RiskTransitionType,
)

from .baselines import (
    BaselineError,
    BaselineService,
    DataBaseline,
    MedicalDecisionVersion,
)

from .modes import (
    ExecutionBasis,
    LockedVersionSelection,
    MODE_CONTRACTS,
    ModeContract,
    ModeContractError,
    MonitoringMode,
    MonitoringRun,
    RunManager,
)

from .diff import (
    ConfigChange,
    ConfigChangeKind,
    ConfigChangeSet,
    DiffEntry,
    DiffEntryKind,
    DiffError,
    DiffService,
    FieldChange,
    SnapshotDiff,
)


from .verification import (
    RehydrationError,
    Rehydrator,
    verify_artifact_bytes,
)

from .audit import (
    AUDIT_GENESIS_SEED,
    AuditChain,
    AuditError,
    AuditEvent,
)

from .store import (
    DashboardInputs,
    IdempotencyConflictError,
    R2Store,
    SaveRequest,
    SaveResult,
    StoreError,
)

from .migration import (
    Migration,
    MigrationArchive,
    MigrationError,
)

from .legacy_adapter import (
    DiffEntry,
    DiffStatus,
    DualReadDiff,
    LegacyAdapterError,
    LegacyFactRow,
    LegacyProjection,
    LegacyRiskRow,
    LegacySnapshotRow,
    LegacySourceRow,
    R1LegacyAdapter,
    R2DualReadState,
)

__version__ = "0.2.0"
