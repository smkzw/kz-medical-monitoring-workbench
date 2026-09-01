"""Consolidated domain modules remain identical through temporary POC shims."""

from packages.medical_monitoring.domain import acceptance, entities, execution
from packages.medical_monitoring.domain import identity, risk, schema_registry, schema_shape
from packages.medical_monitoring.graph import engine, store

from mm_r1 import domain as legacy_r1_domain
from mm_r1 import graph as legacy_r1_graph
from mm_r1 import schema_shape as legacy_r1_schema_shape
from mm_r1 import store as legacy_r1_store
from mm_r2 import acceptance as legacy_r2_acceptance
from mm_r2 import domain as legacy_r2_domain
from mm_r2 import identity as legacy_r2_identity
from mm_r2 import risk as legacy_r2_risk
from mm_r2 import schema_registry as legacy_r2_schema_registry


def test_r1_shims_resolve_to_package_authorities() -> None:
    assert legacy_r1_domain.MonitoringRun is execution.MonitoringRun
    assert legacy_r1_domain.RiskCandidate is execution.RiskCandidate
    assert legacy_r1_schema_shape.connection_shape is schema_shape.connection_shape
    assert legacy_r1_graph.LocalGraphPort is engine.LocalGraphPort
    assert legacy_r1_store.Store is store.Store


def test_r2_shims_resolve_to_package_authorities() -> None:
    assert legacy_r2_schema_registry.SchemaRegistry is schema_registry.SchemaRegistry
    assert legacy_r2_domain.CanonicalFact is entities.CanonicalFact
    assert legacy_r2_identity.RecordIdentity is identity.RecordIdentity
    assert legacy_r2_acceptance.AcceptanceService is acceptance.AcceptanceService
    assert legacy_r2_risk.RiskLifecycle is risk.RiskLifecycle
