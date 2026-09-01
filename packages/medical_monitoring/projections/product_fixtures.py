"""Synthetic R5 authority provider and packet assembly.

Provider contract plus packet identities/variants. The source records come
from the external fixture (``product_fixture_records``); the density packet
stays programmatic (``product_fixtures_density``).
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import Optional

from .product_fixture_records import base_records_from_fixture, flow_records_from_fixture
from .product_fixtures_density import build_density_records
from .product_types import (
    R5AuthorityPacket,
    R5FlowStageRecord,
    R5ProductAdapterError,
    R5SourceRevisionPair,
    R5SubjectFlowPathRecord,
    R5_FLOW_AUTHORITY_CONTRACT_VERSION,
    SYNTHETIC_CUTOFF_REF,
    SYNTHETIC_FIXTURE_MODE,
    SYNTHETIC_PROJECT_REF,
    SYNTHETIC_RUN_REF,
    canonical_sha256,
)

_BASE_SNAPSHOTS = {
    "s7-snapshot-current-001",
    "s7-snapshot-comparable-001",
    "s7-snapshot-not-comparable-001",
    "s7-snapshot-date-edge-001",
    "s7-snapshot-aemh-001",
}

class R5AuthorityProvider:
    """Provider contract used by the router; it must return a typed packet."""

    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        raise NotImplementedError


class SyntheticR5AuthorityProvider(R5AuthorityProvider):
    """Explicitly isolated, deterministic S7 fixture provider."""

    fixture_mode = True

    @lru_cache(maxsize=16)
    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        return build_synthetic_r5_authority_packet(
            project_ref=project_ref,
            run_ref=run_ref,
            snapshot_ref=snapshot_ref,
            cutoff_ref=cutoff_ref,
        )


def build_synthetic_r5_authority_packet(
    *,
    project_ref: str = SYNTHETIC_PROJECT_REF,
    run_ref: Optional[str] = SYNTHETIC_RUN_REF,
    snapshot_ref: Optional[str] = "s7-snapshot-current-001",
    cutoff_ref: Optional[str] = SYNTHETIC_CUTOFF_REF,
) -> R5AuthorityPacket:
    """Build an isolated S7 fixture; callers must explicitly opt into it."""

    if project_ref != SYNTHETIC_PROJECT_REF:
        raise R5ProductAdapterError("PROJECT_NOT_IN_SYNTHETIC_PACKET")
    if run_ref not in {None, SYNTHETIC_RUN_REF}:
        raise R5ProductAdapterError("RUN_NOT_IN_SYNTHETIC_PACKET")
    snapshot = snapshot_ref or "s7-snapshot-current-001"
    if snapshot == "s7-snapshot-density-001":
        cutoff = cutoff_ref or "2026-12-31"
        records = build_density_records(snapshot)
    elif snapshot in _BASE_SNAPSHOTS:
        cutoff = cutoff_ref or SYNTHETIC_CUTOFF_REF
        records = base_records_from_fixture(snapshot)
    else:
        raise R5ProductAdapterError("SNAPSHOT_NOT_IN_SYNTHETIC_PACKET")
    flow_stages: tuple[R5FlowStageRecord, ...] = ()
    flow_paths: tuple[R5SubjectFlowPathRecord, ...] = ()
    if snapshot != "s7-snapshot-density-001":
        # The density fixture stays a legacy-shape packet on purpose so the
        # not_provided projection state stays reachable offline.
        flow_stages, flow_paths = flow_records_from_fixture()
    if cutoff != cutoff_ref and cutoff_ref is not None:
        raise R5ProductAdapterError("CUTOFF_IDENTITY_MISMATCH")
    sources, sites, subjects, events, visits, risks, histories = records
    if snapshot == "s7-snapshot-aemh-001":
        subjects = tuple(item for item in subjects if item.subject_ref == "s7-subject-06021")
        events = tuple(item for item in events if item.subject_ref == "s7-subject-06021")
        visits = tuple(item for item in visits if item.subject_ref == "s7-subject-06021")
        risks = tuple(item for item in risks if item.subject_ref == "s7-subject-06021")
        sites = tuple(item for item in sites if item.site_ref == "s7-site-006")
    if snapshot == "s7-snapshot-not-comparable-001":
        risks = tuple(
            replace(
                item,
                change_kind="not_comparable",
                change_cause="coverage",
                prior_snapshot_ref="s7-snapshot-prior-001",
            )
            for item in risks
        )
    revision_pairs = tuple(
        R5SourceRevisionPair(
            revision_id=item.source_revision_ref,
            content_hash=item.source_revision_content_hash,
            locator_refs=(item.locator_ref,),
        )
        for item in sources
    )
    return R5AuthorityPacket(
        project_ref=project_ref,
        run_ref=run_ref or SYNTHETIC_RUN_REF,
        snapshot_ref=snapshot,
        cutoff_state="present",
        cutoff_ref=cutoff,
        project_label="S7 医学监查合成项目",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version=(
            R5_FLOW_AUTHORITY_CONTRACT_VERSION if flow_stages else "2026-08-26.1"
        ),
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id=f"s7-visibility:{snapshot}",
        visibility_decision_hash=canonical_sha256({"snapshot_ref": snapshot, "projectable": True, "source_count": len(sources)}),
        evaluation_content_identities=(canonical_sha256({"snapshot_ref": snapshot, "kind": "evaluation"}),),
        source_revision_content_pairs=revision_pairs,
        sources=sources,
        sites=sites,
        subjects=subjects,
        events=events,
        visits=visits,
        risks=risks,
        histories=histories if snapshot == "s7-snapshot-aemh-001" else (),
        flow_stages=flow_stages,
        subject_flow_paths=flow_paths,
        synthetic=True,
        data_mode=SYNTHETIC_FIXTURE_MODE,
    )


def build_synthetic_r5_authority_provider() -> SyntheticR5AuthorityProvider:
    return SyntheticR5AuthorityProvider()
