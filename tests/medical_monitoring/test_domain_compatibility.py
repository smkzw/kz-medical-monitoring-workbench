"""Consolidated domain modules remain identical through temporary POC shims."""

from packages.medical_monitoring.domain import acceptance, entities, execution
from packages.medical_monitoring.domain import identity, risk, schema_registry, schema_shape
from packages.medical_monitoring.graph import engine, store
from packages.medical_monitoring.intelligence import normalization, primitives
from packages.medical_monitoring.intelligence import schema_registry as intelligence_schemas
from packages.medical_monitoring.runtime import adapters, background, capability, controller, progress
from packages.medical_monitoring.risks import contracts as risk_contracts
from packages.medical_monitoring.risks import coverage as risk_coverage
from packages.medical_monitoring.risks import lifecycle as risk_lifecycle

from mm_r1 import adapters as legacy_r1_adapters
from mm_r1 import audience_progress as legacy_r1_progress
from mm_r1 import background_progress as legacy_r1_background
from mm_r1 import capability_runtime as legacy_r1_capability
from mm_r1 import controller as legacy_r1_controller
from mm_r1 import domain as legacy_r1_domain
from mm_r1 import graph as legacy_r1_graph
from mm_r1 import schema_shape as legacy_r1_schema_shape
from mm_r1 import store as legacy_r1_store
from mm_r2 import acceptance as legacy_r2_acceptance
from mm_r2 import domain as legacy_r2_domain
from mm_r2 import identity as legacy_r2_identity
from mm_r2 import risk as legacy_r2_risk
from mm_r2 import schema_registry as legacy_r2_schema_registry
from mm_r3 import normalization as legacy_r3_normalization
from mm_r3 import primitives as legacy_r3_primitives
from mm_r3 import schema_registry as legacy_r3_schema_registry
from mm_r4 import contracts as legacy_r4_contracts
from mm_r4 import coverage as legacy_r4_coverage
from mm_r4 import lifecycle as legacy_r4_lifecycle


def test_r1_shims_resolve_to_package_authorities() -> None:
    assert legacy_r1_domain.MonitoringRun is execution.MonitoringRun
    assert legacy_r1_domain.RiskCandidate is execution.RiskCandidate
    assert legacy_r1_schema_shape.connection_shape is schema_shape.connection_shape
    assert legacy_r1_graph.LocalGraphPort is engine.LocalGraphPort
    assert legacy_r1_store.Store is store.Store
    assert legacy_r1_adapters.ScriptedAdapter is adapters.ScriptedAdapter
    assert legacy_r1_capability.CapabilityRuntime is capability.CapabilityRuntime
    assert legacy_r1_controller.CapabilityWorkUnitController is controller.CapabilityWorkUnitController
    assert legacy_r1_progress.project_audience_progress is progress.project_audience_progress
    assert legacy_r1_background.BackgroundProgressFacade is background.BackgroundProgressFacade


def test_r2_shims_resolve_to_package_authorities() -> None:
    assert legacy_r2_schema_registry.SchemaRegistry is schema_registry.SchemaRegistry
    assert legacy_r2_domain.CanonicalFact is entities.CanonicalFact
    assert legacy_r2_identity.RecordIdentity is identity.RecordIdentity
    assert legacy_r2_acceptance.AcceptanceService is acceptance.AcceptanceService
    assert legacy_r2_risk.RiskLifecycle is risk.RiskLifecycle


def test_r3_shims_resolve_to_package_authorities() -> None:
    assert legacy_r3_primitives.content_hash is primitives.content_hash
    assert legacy_r3_normalization.normalize_value is normalization.normalize_value
    assert legacy_r3_schema_registry.SchemaRegistry is intelligence_schemas.SchemaRegistry


def test_r4_risk_foundation_shims_resolve_to_package_authorities() -> None:
    assert legacy_r4_contracts.EvaluationUnit is risk_contracts.EvaluationUnit
    assert legacy_r4_coverage.CoverageLedger is risk_coverage.CoverageLedger
    assert legacy_r4_lifecycle.R4LifecycleAdapter is risk_lifecycle.R4LifecycleAdapter
