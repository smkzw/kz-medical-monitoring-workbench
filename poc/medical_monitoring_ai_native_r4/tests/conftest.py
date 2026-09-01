"""Shared pytest fixtures for the R4 POC test suite (worker_01-owned).
All tests run only inside the R4 POC root; the frozen R1, R2 and R3 local
``src`` roots are configured on ``sys.path`` before any ``mm_r4`` import so
R4's read-only authority reuse resolves correctly.  No package installation,
real-project paths, credentials, or network are permitted.  Port 8911 must
remain stopped.
"""

from __future__ import annotations

import sys
from pathlib import Path

POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.contracts import (  # noqa: E402
    EvaluationUnit,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    UnitEvaluation,
)
from mm_r4.coverage import (  # noqa: E402
    CoverageLedger,
    ExpectedSet,
)


# ---------------------------------------------------------------------------
# Constants (not fixtures; imported by tests directly)
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = "D01_aemh"
RUN_ID = "run-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
RULE_LINEAGE = "rule-lineage-v1"
UNIT_ALGO_VERSION = "unit-algo-v1"
TEMPORAL_WINDOW = "study-period-v1"


# ---------------------------------------------------------------------------
# Minimal synthetic helpers -- deterministic, no randomness in the hash path.
# ---------------------------------------------------------------------------

@pytest.fixture
def make_locator():
    def _make(record_id: str, table_semantic: str = "reported_ae") -> SourceLocator:
        return SourceLocator(
            snapshot_id=SNAPSHOT_ID,
            source_revision_id=SOURCE_REV_ID,
            table_semantic=table_semantic,
            record_id=record_id,
            column_or_anchor="row",
        )
    return _make


@pytest.fixture
def make_unit():
    def _make(
        scope_key: str,
        concept: str,
        domain_id: str = DOMAIN_ID,
        scope_type: str = "subject",
        temporal_window: str = TEMPORAL_WINDOW,
        rule_lineage: str = RULE_LINEAGE,
        algo_version: str = UNIT_ALGO_VERSION,
    ) -> EvaluationUnit:
        return EvaluationUnit(
            project_id=PROJECT_ID,
            domain_id=domain_id,
            scope_type=scope_type,
            scope_key=scope_key,
            normalized_concept_or_rule_item=concept,
            temporal_window=temporal_window,
            rule_or_knowledge_lineage=rule_lineage,
            unit_algorithm_version=algo_version,
        )
    return _make


@pytest.fixture
def make_evidence(make_locator):
    def _make(
        evidence_id: str,
        polarity: str = L1bEvidencePolarity.SUPPORTING,
        role: str = "reported_ae",
        record_id: str = "rec-001",
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=evidence_id,
            polarity=polarity,
            locator=make_locator(record_id=record_id, table_semantic=role),
            evidence_role=role,
            rule_lineage=RULE_LINEAGE,
        )
    return _make


@pytest.fixture
def make_candidate(make_locator):
    def _make(candidate_id: str, record_id: str = "rec-cand-001") -> RiskCandidateRef:
        return RiskCandidateRef(
            candidate_id=candidate_id,
            risk_identity_id="risk-id-synthetic",
            locator=make_locator(record_id=record_id, table_semantic="lab_finding"),
        )
    return _make


@pytest.fixture
def make_risk_instance():
    def _make(
        risk_instance_id: str = "ri-001",
        risk_state: str = "established",
    ) -> RiskInstanceRef:
        return RiskInstanceRef(
            risk_instance_id=risk_instance_id,
            risk_identity_id="risk-id-synthetic",
            risk_state=risk_state,
        )
    return _make


@pytest.fixture
def make_query():
    def _make(
        query_id: str,
        unit_id: str,
        source_locator_ids,
        linked_candidate_id: str = "",
        linked_risk_instance_id: str = "",
    ) -> QueryDraftRef:
        return QueryDraftRef(
            query_id=query_id,
            unit_id=unit_id,
            basis="方案要求 AE 收集窗口内全部不良事件须记录",
            finding=f"受试者 {unit_id[:20]} 存在跨表医学事件但无对应 AE 记录",
            action="请核实是否为漏报 AE，并补充原始记录",
            source_locator_ids=tuple(source_locator_ids),
            linked_candidate_id=linked_candidate_id,
            linked_risk_instance_id=linked_risk_instance_id,
        )
    return _make


@pytest.fixture
def make_unit_evaluation():
    def _make(
        unit: EvaluationUnit,
        l0_status: str = L0CoverageStatus.COVERED,
        l1_disposition: str = L1Disposition.NEGATIVE,
        l1b_polarities=(),
        evidence=(),
        source_record_refs=(),
        risk_candidate_refs=(),
        risk_instance_refs=(),
        query_refs=(),
        provenance_snapshot_id: str = SNAPSHOT_ID,
        provenance_rule_lineage: str = RULE_LINEAGE,
        not_evaluable_reason: str = "",
    ) -> UnitEvaluation:
        return UnitEvaluation(
            unit_id=unit.unit_id,
            l0_status=l0_status,
            l1_disposition=l1_disposition,
            l1b_polarities=tuple(l1b_polarities),
            evidence=tuple(evidence),
            source_record_refs=tuple(source_record_refs),
            risk_candidate_refs=tuple(risk_candidate_refs),
            risk_instance_refs=tuple(risk_instance_refs),
            query_refs=tuple(query_refs),
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=not_evaluable_reason,
        )
    return _make


@pytest.fixture
def make_expected_set():
    def _make(units, domain_id: str = DOMAIN_ID, run_id: str = RUN_ID) -> ExpectedSet:
        return ExpectedSet.from_units(units, domain_id=domain_id, run_id=run_id)
    return _make


@pytest.fixture
def make_ledger():
    def _make(expected_set: ExpectedSet) -> CoverageLedger:
        return CoverageLedger(expected_set=expected_set)
    return _make
