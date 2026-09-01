"""Shared Batch B test helpers for acceptance fixture creation."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mm_r2.domain import (
    IdentityAlgorithm, ListingSnapshot, MappingDefinition, MappingResult,
    SourceRevision,
)
from mm_r2.identity import IdentityResolution, make_record_identity
from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY, AcceptanceService,
    SnapshotAcceptanceState, SnapshotBinding,
)


def make_accepted_snapshot(svc, pid="p1", rid="rev-1", sid="s1",
                           rows=None, eligible=True):
    """Build a snapshot, register it, advance to accepted/baseline_eligible."""
    rows = rows if rows is not None else [{"subject": "S01", "ae": "Nausea"}]
    source = SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="v1", source_bytes=b"synthetic",
    )
    snap = ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version=f"cutoff-{sid}", rows=rows,
    )
    algo = IdentityAlgorithm(algorithm_id="alg-1", name="record-id", version="1")
    mapping = MappingDefinition(
        mapping_id="m1", project_id=pid, source_revision_id=rid,
        identity_algorithm_id="alg-1", source_field="AETERM",
        canonical_field="ae_term", version="1", confidence=1.0,
        is_critical=True,
    )
    result = MappingResult.from_verified(
        result_id="mr1", project_id=pid, snapshot=snap,
        mapping=mapping, identity_algorithm=algo, record_count=len(rows),
    )
    subjects = [r.get("subject", "S01") for r in rows]
    rec_ids = [make_record_identity(pid, algo, {"subject": s}) for s in subjects]
    resolution = IdentityResolution(algorithm=algo, resolved=tuple(rec_ids))
    binding = SnapshotBinding(
        project_id=pid, snapshot=snap, source=source,
        identity_algorithm=algo, mapping_definitions=(mapping,),
        mapping_results=(result,), identity_resolution=resolution,
    )
    svc.register(binding, ACCEPTED_BY_SYSTEM_POLICY)
    actor = ACCEPTED_BY_SYSTEM_POLICY
    svc.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                evidence=svc.evidence(sid, actor, structural_validation_complete=True))
    svc.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                evidence=svc.evidence(sid, actor))
    svc.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                evidence=svc.evidence(sid, actor, approved_scope=True))
    if eligible:
        svc.advance(sid, SnapshotAcceptanceState.BASELINE_ELIGIBLE, actor,
                    evidence=svc.evidence(sid, actor, source_coverage_complete=True,
                                          approved_scope=True))
    return snap
