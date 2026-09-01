"""人工构造的 ``SYNTHETIC`` R1 AE/MH 全量快照。

本模块只提供隔离 POC 数据，不读取项目文件，也不模拟任何真实项目的
路径、中心或受试者编号。``seed_synthetic_snapshots`` 使用 worker_01 的
内容寻址快照和严格 acceptance API，把 N 与 N+1 作为两个独立的全量
listing 保存；两个快照即使有相同表和记录，也不会把 snapshot identity
折叠成同一个对象。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from .domain import (
    ACCEPTANCE_CHAIN,
    ExecutionBasis,
    ListingSnapshot,
    MonitoringRun,
    RunMode,
    SnapshotAcceptanceState,
    SourceRevision,
    StudyProject,
    content_hash,
)


SYNTHETIC_MARKER = "SYNTHETIC"
SYNTHETIC_PROJECT_ID = "SYNTHETIC-R1-AEMH"
SYNTHETIC_REVISION_N = "SYNTHETIC-REV-N"
SYNTHETIC_REVISION_N1 = "SYNTHETIC-REV-N1"
SYNTHETIC_SNAPSHOT_N = "SYNTHETIC-SNAPSHOT-N"
SYNTHETIC_SNAPSHOT_N1 = "SYNTHETIC-SNAPSHOT-N1"
SYNTHETIC_RUN_N = "SYNTHETIC-RUN-N"
SYNTHETIC_RUN_N1 = "SYNTHETIC-RUN-N1"

SYNTHETIC_SUBJECT_001 = "SYNTHETIC-SUBJECT-001"
SYNTHETIC_SUBJECT_002 = "SYNTHETIC-SUBJECT-002"
SYNTHETIC_SUBJECT_003 = "SYNTHETIC-SUBJECT-003"
SYNTHETIC_SITE_A = "SYNTHETIC-SITE-A"
SYNTHETIC_SITE_B = "SYNTHETIC-SITE-B"


def _row(record_id: str, subject_id: str, site_id: str, **fields: Any) -> Dict[str, Any]:
    """Build a visibly synthetic row with a stable row identity."""
    return {
        "record_id": record_id,
        "subject_id": subject_id,
        "site_id": site_id,
        "fixture_marker": SYNTHETIC_MARKER,
        **fields,
    }


def _listing_n() -> Dict[str, List[Dict[str, Any]]]:
    """N: a complete, multi-domain synthetic listing."""
    return {
        # Formal AE/MH facts.  These rows provide direct matches/counterevidence
        # for symptom, CM and dosing signals below.
        "ae": [
            _row(
                "SYNTHETIC-AE-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Headache", event_identity="headache-20260108",
                onset="2026-01-08", severity="mild", status="reported",
            ),
            _row(
                "SYNTHETIC-AE-N-002", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Nausea", event_identity="nausea-20260110",
                onset="2026-01-10", severity="moderate", status="reported",
            ),
        ],
        "mh": [
            _row(
                "SYNTHETIC-MH-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Hypertension", event_identity="hypertension-baseline",
                onset="2025-12-01", severity="moderate", status="reported",
            ),
        ],
        # Multiple evidence domains point at the same synthetic rash event.
        "symptoms": [
            _row(
                "SYNTHETIC-SYM-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Headache", event_identity="headache-20260108",
                actual_date="2026-01-08", signal_type="symptom",
                candidate_signal=True, severity="low",
            ),
            _row(
                "SYNTHETIC-SYM-N-002", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Skin rash", event_identity="rash-20260115",
                actual_date="2026-01-15", signal_type="symptom",
                candidate_signal=True, severity="high",
            ),
            _row(
                "SYNTHETIC-SYM-N-003", SYNTHETIC_SUBJECT_003, SYNTHETIC_SITE_B,
                concept="Dizziness", event_identity="dizziness-20260118",
                actual_date="2026-01-18", signal_type="symptom",
                candidate_signal=True, severity="medium",
            ),
            _row(
                "SYNTHETIC-SYM-N-004", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Fatigue", event_identity="fatigue-20260125",
                actual_date="2026-01-25", signal_type="symptom",
                candidate_signal=True, severity="medium",
            ),
        ],
        "labs": [
            _row(
                "SYNTHETIC-LAB-N-001", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="ALT elevation", event_identity="alt-20260116",
                actual_date="2026-01-16", value="synthetic-high",
                signal_type="laboratory", candidate_signal=True, severity="medium",
            ),
            _row(
                "SYNTHETIC-LAB-N-002", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Routine marker", event_identity="routine-20260112",
                actual_date="2026-01-12", value="synthetic-normal",
                signal_type="laboratory", candidate_signal=False,
            ),
        ],
        "examinations": [
            _row(
                "SYNTHETIC-EXAM-N-001", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Skin rash", event_identity="rash-20260115",
                actual_date="2026-01-15", signal_type="examination",
                candidate_signal=True, severity="high",
            ),
        ],
        "hospitalizations": [
            _row(
                "SYNTHETIC-HOSP-N-001", SYNTHETIC_SUBJECT_003, SYNTHETIC_SITE_B,
                concept="Unplanned admission", event_identity="admission-20260120",
                actual_date="2026-01-20", signal_type="hospitalization",
                candidate_signal=True, severity="severe",
            ),
        ],
        "procedures": [
            _row(
                "SYNTHETIC-PROC-N-001", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Skin rash evaluation", event_identity="rash-20260115",
                actual_date="2026-01-16", signal_type="procedure",
                candidate_signal=True, severity="high",
            ),
        ],
        "concomitant_medications": [
            _row(
                "SYNTHETIC-CM-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Hypertension", indication="Hypertension",
                event_identity="hypertension-baseline", actual_date="2026-01-05",
                signal_type="cm_indication", risk_type="potential_unreported_mh",
                candidate_signal=True, severity="medium",
            ),
            _row(
                "SYNTHETIC-CM-N-002", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Nausea", indication="Nausea",
                event_identity="nausea-20260110", actual_date="2026-01-10",
                signal_type="cm_indication", candidate_signal=True, severity="medium",
            ),
        ],
        "dosing": [
            _row(
                "SYNTHETIC-DOSE-N-001", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Skin rash", event_identity="rash-20260115",
                actual_date="2026-01-17", action="dose held",
                signal_type="dose_action", candidate_signal=True, severity="high",
            ),
        ],
        "serious_events": [
            _row(
                "SYNTHETIC-SERIOUS-N-001", SYNTHETIC_SUBJECT_003, SYNTHETIC_SITE_B,
                concept="Unplanned admission", event_identity="admission-20260120",
                actual_date="2026-01-20", signal_type="serious_event",
                candidate_signal=True, severity="severe",
            ),
        ],
    }


def _listing_n1() -> Dict[str, List[Dict[str, Any]]]:
    """N+1: a second complete listing with explicit disappearance and change."""
    return {
        # The already reported records remain in the full listing.
        "ae": [
            _row(
                "SYNTHETIC-AE-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Headache", event_identity="headache-20260108",
                onset="2026-01-08", severity="mild", status="reported",
            ),
            _row(
                "SYNTHETIC-AE-N-002", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="Nausea", event_identity="nausea-20260110",
                onset="2026-01-10", severity="moderate", status="reported",
            ),
        ],
        "mh": [
            _row(
                "SYNTHETIC-MH-N-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Hypertension", event_identity="hypertension-baseline",
                onset="2025-12-01", severity="moderate", status="reported",
            ),
        ],
        "symptoms": [
            _row(
                "SYNTHETIC-SYM-N1-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Headache", event_identity="headache-20260108",
                actual_date="2026-01-08", signal_type="symptom",
                candidate_signal=True, severity="low",
            ),
            # The prior high-risk rash and medium-risk dizziness are absent from
            # N+1; lifecycle code must distinguish them from resolved data.
            _row(
                "SYNTHETIC-SYM-N1-002", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Fatigue", event_identity="fatigue-20260125",
                actual_date="2026-01-25", signal_type="symptom",
                candidate_signal=True, severity="medium",
            ),
        ],
        "labs": [
            _row(
                "SYNTHETIC-LAB-N1-001", SYNTHETIC_SUBJECT_002, SYNTHETIC_SITE_A,
                concept="ALT", event_identity="alt-20260116",
                actual_date="2026-01-25", value="synthetic-normal",
                signal_type="laboratory", candidate_signal=False,
                counterevidence_for="alt-20260116",
            ),
            _row(
                "SYNTHETIC-LAB-N1-002", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Routine marker", event_identity="routine-20260125",
                actual_date="2026-01-25", value="synthetic-normal",
                signal_type="laboratory", candidate_signal=False,
            ),
        ],
        "examinations": [],
        "hospitalizations": [],
        "procedures": [],
        "concomitant_medications": [
            _row(
                "SYNTHETIC-CM-N1-001", SYNTHETIC_SUBJECT_001, SYNTHETIC_SITE_A,
                concept="Hypertension", indication="Hypertension",
                event_identity="hypertension-baseline", actual_date="2026-01-25",
                signal_type="cm_indication", risk_type="potential_unreported_mh",
                candidate_signal=True, severity="medium",
            ),
        ],
        "dosing": [],
        "serious_events": [],
    }


def synthetic_listing_n() -> Dict[str, List[Dict[str, Any]]]:
    """Return a deep copy of the synthetic N full listing."""
    return copy.deepcopy(_listing_n())


def synthetic_listing_n1() -> Dict[str, List[Dict[str, Any]]]:
    """Return a deep copy of the synthetic N+1 full listing."""
    return copy.deepcopy(_listing_n1())


# Short aliases keep callers readable while retaining explicit full-listing
# names for hidden/manager checks.
listing_n = synthetic_listing_n
listing_n1 = synthetic_listing_n1


@dataclass
class SyntheticSnapshotBundle:
    marker: str
    project: StudyProject
    revision_n: SourceRevision
    revision_n1: SourceRevision
    snapshot_n: ListingSnapshot
    snapshot_n1: ListingSnapshot
    listing_n: Dict[str, List[Dict[str, Any]]]
    listing_n1: Dict[str, List[Dict[str, Any]]]

    @property
    def project_id(self) -> str:
        return self.project.project_id

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "marker": self.marker,
            "project": self.project,
            "revision_n": self.revision_n,
            "revision_n1": self.revision_n1,
            "snapshot_n": self.snapshot_n,
            "snapshot_n1": self.snapshot_n1,
            "listing_n": copy.deepcopy(self.listing_n),
            "listing_n1": copy.deepcopy(self.listing_n1),
        }


def _require_synthetic(value: str, label: str) -> None:
    if SYNTHETIC_MARKER not in value:
        raise ValueError(f"{label} must contain the {SYNTHETIC_MARKER} marker")


def _scoped_fixture_id(base: str, project_id: str) -> str:
    """Keep the default public IDs readable and avoid cross-project clashes."""
    if project_id == SYNTHETIC_PROJECT_ID:
        return base
    return f"{base}-{content_hash(project_id)[:10]}"


def _accept_snapshot(store: Any, snapshot_id: str) -> None:
    for target in ACCEPTANCE_CHAIN[1:]:
        store.transition_snapshot_acceptance(
            snapshot_id,
            target,
            accepted_by="system_policy",
            reason=f"{SYNTHETIC_MARKER} full-listing fixture acceptance: {target.value}",
        )


def seed_synthetic_snapshots(
    store: Any,
    project_id: str = SYNTHETIC_PROJECT_ID,
) -> SyntheticSnapshotBundle:
    """Persist independent N/N+1 full-listing snapshots in ``store``.

    The helper is idempotent for the same store and identifiers.  It uses only
    worker_01 public Store methods and accepts both snapshots through the full
    chain, so callers can safely test diff/lifecycle behavior without a service.
    """
    _require_synthetic(project_id, "project_id")
    listing_n_data = synthetic_listing_n()
    listing_n1_data = synthetic_listing_n1()
    revision_n_id = _scoped_fixture_id(SYNTHETIC_REVISION_N, project_id)
    revision_n1_id = _scoped_fixture_id(SYNTHETIC_REVISION_N1, project_id)
    snapshot_n_id = _scoped_fixture_id(SYNTHETIC_SNAPSHOT_N, project_id)
    snapshot_n1_id = _scoped_fixture_id(SYNTHETIC_SNAPSHOT_N1, project_id)
    project = store.create_project(
        project_id,
        f"{SYNTHETIC_MARKER} R1 AE/MH vertical slice",
        config={
            "fixture_marker": SYNTHETIC_MARKER,
            "listing_mode": "full_snapshot",
            "tables": sorted(listing_n_data),
        },
        is_synthetic=True,
    )
    revision_n = store.add_source_revision(SourceRevision(
        revision_id=revision_n_id,
        project_id=project_id,
        source_type="listing",
        version=f"{SYNTHETIC_MARKER}-N",
        content_hash=content_hash({"marker": SYNTHETIC_MARKER, "snapshot": "N", "tables": listing_n_data}),
        scope={"marker": SYNTHETIC_MARKER, "coverage": "full_listing"},
    ))
    revision_n1 = store.add_source_revision(SourceRevision(
        revision_id=revision_n1_id,
        project_id=project_id,
        source_type="listing",
        version=f"{SYNTHETIC_MARKER}-N1",
        content_hash=content_hash({"marker": SYNTHETIC_MARKER, "snapshot": "N+1", "tables": listing_n1_data}),
        scope={"marker": SYNTHETIC_MARKER, "coverage": "full_listing"},
    ))
    snapshot_n = store.add_listing_snapshot(ListingSnapshot(
        snapshot_id=snapshot_n_id,
        project_id=project_id,
        revision_id=revision_n.revision_id,
        snapshot_version=f"{SYNTHETIC_MARKER}-N",
        structure={
            "marker": SYNTHETIC_MARKER,
            "kind": "full_listing",
            "tables": sorted(listing_n_data),
            "snapshot_label": "N",
        },
        is_synthetic=True,
    ), listing_n_data)
    snapshot_n1 = store.add_listing_snapshot(ListingSnapshot(
        snapshot_id=snapshot_n1_id,
        project_id=project_id,
        revision_id=revision_n1.revision_id,
        snapshot_version=f"{SYNTHETIC_MARKER}-N1",
        structure={
            "marker": SYNTHETIC_MARKER,
            "kind": "full_listing",
            "tables": sorted(listing_n1_data),
            "snapshot_label": "N+1",
        },
        is_synthetic=True,
    ), listing_n1_data)
    if store.get_acceptance(snapshot_n.snapshot_id).state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
        _accept_snapshot(store, snapshot_n.snapshot_id)
    if store.get_acceptance(snapshot_n1.snapshot_id).state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
        _accept_snapshot(store, snapshot_n1.snapshot_id)
    return SyntheticSnapshotBundle(
        marker=SYNTHETIC_MARKER,
        project=project,
        revision_n=revision_n,
        revision_n1=revision_n1,
        snapshot_n=snapshot_n,
        snapshot_n1=snapshot_n1,
        listing_n=listing_n_data,
        listing_n1=listing_n1_data,
    )


def create_synthetic_run(
    store: Any,
    bundle: SyntheticSnapshotBundle,
    run_id: str = SYNTHETIC_RUN_N1,
    mode: RunMode = RunMode.DAILY,
) -> MonitoringRun:
    """Create a synthetic full run bound to the N+1 source revision."""
    if run_id == SYNTHETIC_RUN_N1 and bundle.project_id != SYNTHETIC_PROJECT_ID:
        run_id = _scoped_fixture_id(run_id, bundle.project_id)
    _require_synthetic(run_id, "run_id")
    return store.create_run(MonitoringRun(
        run_id=run_id,
        project_id=bundle.project_id,
        mode=mode,
        data_cutoff=f"{SYNTHETIC_MARKER}-N1-CUTOFF",
        source_revision_id=bundle.revision_n1.revision_id,
        execution_basis=ExecutionBasis.FULL,
    ))


def build_synthetic_bundle(store: Any) -> SyntheticSnapshotBundle:
    """Compatibility alias used by the vertical-slice test and demo code."""
    return seed_synthetic_snapshots(store)


@dataclass
class SyntheticVerticalSlice:
    """N, N+1, lifecycle and projections in one resumable test object."""

    bundle: SyntheticSnapshotBundle
    result_n: Any
    result_n1: Any
    projections: Any


def run_synthetic_vertical_slice(
    store: Any,
    project_id: str = SYNTHETIC_PROJECT_ID,
) -> SyntheticVerticalSlice:
    """Build the complete isolated N→N+1 AE/MH slice without a service."""
    from .ae_mh import run_ae_mh_vertical_slice
    from .projections import build_projections

    bundle = seed_synthetic_snapshots(store, project_id=project_id)
    run_n = _scoped_fixture_id(SYNTHETIC_RUN_N, bundle.project_id)
    run_n1 = _scoped_fixture_id(SYNTHETIC_RUN_N1, bundle.project_id)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id=run_n,
        snapshot_version=f"{SYNTHETIC_MARKER}-N",
        store=store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id=run_n1,
        snapshot_version=f"{SYNTHETIC_MARKER}-N1",
        previous_result=result_n,
        store=store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    return SyntheticVerticalSlice(
        bundle=bundle,
        result_n=result_n,
        result_n1=result_n1,
        projections=build_projections(result_n1),
    )
