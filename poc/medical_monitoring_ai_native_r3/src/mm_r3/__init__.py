"""mm_r3 -- R3 Study Intelligence kernel for the medical monitoring AI-native
POC (synthetic fixtures only).

R3-A (worker_01) owns the package scaffold, the R3 schema registry seed, and
the knowledge/source-authority contracts:

* schema registry (this module, via ``schema_registry``)
* source classification, version, valid-time and scope (``knowledge``)
* Study Knowledge Pack with claim authority (``knowledge``)
* source conflict and conflict resolution contracts (``knowledge``)
* synthetic fixtures (``fixtures``)

R3-B (worker_02) owns the listing/mapping/identity/normalization contracts:

* workbook/table/field structure profiles (``listing``)
* semantic mapping candidates/confidence/dependencies/decisions (``mapping``)
* stable record identity + ambiguity (``identity``)
* date/unit/coding/partial/missing/duplicate normalization (``normalization``)

R3-C (worker_03) appends snapshot diff / impact propagation and the
natural-language rule lifecycle (draft → simulate → versioned activation
with frozen evaluation scope):

* snapshot diff, change kinds, clinical impact propagation (``snapshot_diff``)
* rule draft / simulation / versioned activation / evaluation scope (``rules``)

Later workers may append coherent public exports/documentation to this module;
they must not overwrite earlier contracts.
"""

from __future__ import annotations

from .schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaVersion,
    default_registry,
)
from .identity import (
    AmbiguousIdentity,
    IdentityAlgorithm,
    IdentityResolution,
    RecordIdentity,
)
from .listing import (
    FieldProfile,
    TableProfile,
    WorkbookProfile,
)
from .mapping import (
    FieldMapping,
    MappingCandidate,
    MappingDecision,
    MappingResult,
    SystemPolicy,
    TargetConcept,
)
from .normalization import (
    NormalizationKind,
    NormalizedValue,
    ValueQuality,
)
from .snapshot_diff import (
    ChangeKind,
    ChangeRecord,
    ImpactItem,
    ImpactPropagation,
    SnapshotDiff,
    SnapshotFacts,
)
from .rules import (
    EvaluationScope,
    EvaluationScopeKind,
    RuleActivation,
    RuleDraft,
    RuleSimulation,
)

__all__ = [
    "SchemaRegistry",
    "SchemaRegistryError",
    "SchemaVersion",
    "default_registry",
    # R3-B
    "AmbiguousIdentity",
    "IdentityAlgorithm",
    "IdentityResolution",
    "RecordIdentity",
    "FieldProfile",
    "TableProfile",
    "WorkbookProfile",
    "FieldMapping",
    "MappingCandidate",
    "MappingDecision",
    "MappingResult",
    "SystemPolicy",
    "TargetConcept",
    "NormalizationKind",
    "NormalizedValue",
    "ValueQuality",
    # R3-C
    "ChangeKind",
    "ChangeRecord",
    "ImpactItem",
    "ImpactPropagation",
    "SnapshotDiff",
    "SnapshotFacts",
    "EvaluationScope",
    "EvaluationScopeKind",
    "RuleActivation",
    "RuleDraft",
    "RuleSimulation",
]

__version__ = "0.4.0"
