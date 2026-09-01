"""Synthetic fixtures for the R3 POC (worker_01-owned, R3-A).

All fixtures are **synthetic**.  No real-project paths, real project
names, credentials, or network.  These factories build the
R3-A domain objects (source revisions, classifications, knowledge packs,
claims, conflicts) from deterministic synthetic content so that tests and
downstream workers (R3-B, R3-C) have a stable, reproducible evidence base.

The fixture builders here produce at least three heterogeneous listing
*source* shapes so that later workers can prove no project/path hardcoding.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from .knowledge import (
    Claim,
    ClaimAuthority,
    ClaimStatus,
    ConflictResolution,
    ConflictResolutionLog,
    ConflictType,
    KnowledgeLayer,
    ResolutionOutcome,
    SourceClassification,
    SourceConflict,
    SourceRevision,
    StudyKnowledgePack,
)
from .primitives import new_id, now_iso

__all__ = [
    "make_protocol_revision",
    "make_ib_revision",
    "make_listing_revision",
    "make_report_revision",
    "make_amendment_revision",
    "make_classification",
    "make_knowledge_pack",
    "make_claim",
    "make_conflicting_claims",
    "make_authority",
    "make_conflict",
    "make_resolution",
    "make_resolution_log",
    "make_three_heterogeneous_listing_sources",
    "SYNTHETIC_PROJECT_IDS",
]


#: Synthetic project ids that are deliberately generic (no real-project name).
SYNTHETIC_PROJECT_IDS: Tuple[str, ...] = ("proj-alpha", "proj-beta", "proj-gamma")


# ---------------------------------------------------------------------------
# Source revisions (synthetic content)
# ---------------------------------------------------------------------------

def make_protocol_revision(
    project_id: str = "proj-alpha",
    revision_id: str = "rev-protocol-1",
    *,
    content: bytes = b"synthetic-protocol-v1",
    version: str = "1.0",
    valid_from: str = "2026-01-01",
    valid_until: Optional[str] = None,
    scope: Tuple[Tuple[str, Any], ...] = (("domain", "study_design"),),
) -> SourceRevision:
    return SourceRevision.from_bytes(
        revision_id=revision_id,
        project_id=project_id,
        source_type="protocol",
        version=version,
        source_bytes=content,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def make_ib_revision(
    project_id: str = "proj-alpha",
    revision_id: str = "rev-ib-1",
    *,
    content: bytes = b"synthetic-ib-v1",
    version: str = "1.0",
    valid_from: str = "2026-01-01",
    valid_until: Optional[str] = None,
    scope: Tuple[Tuple[str, Any], ...] = (("domain", "safety"),),
) -> SourceRevision:
    return SourceRevision.from_bytes(
        revision_id=revision_id,
        project_id=project_id,
        source_type="ib",
        version=version,
        source_bytes=content,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def make_listing_revision(
    project_id: str = "proj-alpha",
    revision_id: str = "rev-listing-ae-1",
    *,
    content: bytes = b"synthetic-ae-listing-v1",
    version: str = "2026-06-01",
    valid_from: str = "2026-06-01",
    valid_until: Optional[str] = None,
    scope: Tuple[Tuple[str, Any], ...] = (("domain", "ae"), ("dataset", "AE")),
) -> SourceRevision:
    return SourceRevision.from_bytes(
        revision_id=revision_id,
        project_id=project_id,
        source_type="listing",
        version=version,
        source_bytes=content,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def make_report_revision(
    project_id: str = "proj-alpha",
    revision_id: str = "rev-report-1",
    *,
    content: bytes = b"synthetic-dmb-report-v1",
    version: str = "2026-06-15",
    valid_from: str = "2026-06-15",
    valid_until: Optional[str] = None,
    scope: Tuple[Tuple[str, Any], ...] = (("domain", "safety"),),
) -> SourceRevision:
    return SourceRevision.from_bytes(
        revision_id=revision_id,
        project_id=project_id,
        source_type="report",
        version=version,
        source_bytes=content,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def make_amendment_revision(
    project_id: str = "proj-alpha",
    revision_id: str = "rev-amendment-1",
    *,
    content: bytes = b"synthetic-protocol-amendment-v2",
    version: str = "2.0",
    valid_from: str = "2026-03-01",
    valid_until: Optional[str] = None,
    scope: Tuple[Tuple[str, Any], ...] = (("domain", "study_design"),),
) -> SourceRevision:
    return SourceRevision.from_bytes(
        revision_id=revision_id,
        project_id=project_id,
        source_type="protocol_amendment",
        version=version,
        source_bytes=content,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
    )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def make_classification(
    revision: SourceRevision,
    *,
    knowledge_layer: str = KnowledgeLayer.PROJECT_DOCUMENTS,
    is_primary_project_document: bool = True,
    classification_id: str = "",
    authority_level: str = "",
    classification_basis: str = "synthetic fixture",
) -> SourceClassification:
    return SourceClassification.for_revision(
        revision,
        knowledge_layer=knowledge_layer,
        is_primary_project_document=is_primary_project_document,
        classification_id=classification_id or new_id("cls-"),
        authority_level=authority_level,
        classification_basis=classification_basis,
    )


# ---------------------------------------------------------------------------
# Knowledge pack
# ---------------------------------------------------------------------------

def make_knowledge_pack(
    project_id: str = "proj-alpha",
    pack_id: str = "kp-1",
    *,
    source_revisions: List[SourceRevision],
    version: str = "1",
    general_layer: Optional[Mapping[str, Any]] = None,
    drug_layer: Optional[Mapping[str, Any]] = None,
    project_layer: Optional[Mapping[str, Any]] = None,
    rules_layer: Optional[Mapping[str, Any]] = None,
    claim_scope: Tuple[str, ...] = ("ae", "dosing"),
) -> StudyKnowledgePack:
    if any(r.project_id != project_id for r in source_revisions):
        raise ValueError("all knowledge-pack source revisions must belong to project_id")
    layers: List[Tuple[str, Any]] = []
    if general_layer is not None:
        layers.append(("general_medical", dict(general_layer)))
    if drug_layer is not None:
        layers.append(("drug_mechanism", dict(drug_layer)))
    if project_layer is not None:
        layers.append(("project_documents", dict(project_layer)))
    if rules_layer is not None:
        layers.append(("activated_rules", dict(rules_layer)))
    return StudyKnowledgePack(
        pack_id=pack_id,
        project_id=project_id,
        version=version,
        source_revision_ids=tuple(r.revision_id for r in source_revisions),
        layers=tuple(layers),
        claim_scope=claim_scope,
    )


# ---------------------------------------------------------------------------
# Claims + authority
# ---------------------------------------------------------------------------

def make_claim(
    source_revision: SourceRevision,
    *,
    claim_scope: str,
    statement: str,
    raw_value: Any = None,
    status: str = ClaimStatus.SUPPORTED,
    locator: Tuple[Tuple[str, Any], ...] = (("section", "general"),),
    claim_id: str = "",
) -> Claim:
    return Claim(
        claim_id=claim_id or new_id("claim-"),
        project_id=source_revision.project_id,
        source_revision_id=source_revision.revision_id,
        claim_scope=claim_scope,
        statement=statement,
        locator=locator,
        raw_value=raw_value,
        status=status,
    )


def make_conflicting_claims(
    source_a: SourceRevision,
    source_b: SourceRevision,
    *,
    claim_scope: str,
    value_a: Any,
    value_b: Any,
    statement_a: str = "claim A",
    statement_b: str = "claim B",
) -> Tuple[Claim, Claim]:
    """Two claims on the same scope with different raw values."""
    return (
        make_claim(
            source_a,
            claim_scope=claim_scope,
            statement=statement_a,
            raw_value=value_a,
            locator=(("section", "A"),),
        ),
        make_claim(
            source_b,
            claim_scope=claim_scope,
            statement=statement_b,
            raw_value=value_b,
            locator=(("section", "B"),),
        ),
    )


def make_authority(
    claims: List[Claim],
    *,
    classifications: Optional[Mapping[str, SourceClassification]] = None,
    authority_id: str = "",
) -> ClaimAuthority:
    return ClaimAuthority.from_claims(
        claims,
        authority_id=authority_id,
        classifications=classifications,
    )


# ---------------------------------------------------------------------------
# Conflict + resolution
# ---------------------------------------------------------------------------

def make_conflict(
    claims: List[Claim],
    *,
    conflict_type: str = ConflictType.CONTRADICTION,
    detail: str = "synthetic conflict",
    conflict_id: str = "",
) -> SourceConflict:
    return SourceConflict.between(
        claims,
        conflict_type=conflict_type,
        detail=detail,
        conflict_id=conflict_id or new_id("conf-"),
    )


def make_resolution(
    conflict: SourceConflict,
    winning_claim_id: str,
    *,
    winning_source_revision_id: str = "",
    outcome: str = ResolutionOutcome.PROJECT_SOURCE_WINS,
    basis: str = "project source wins within scope",
    residual_uncertainty: str = "",
    resolved_by: str = "local_test_user",
    is_machine_resolution: bool = True,
    resolution_id: str = "",
) -> ConflictResolution:
    if winning_claim_id and not winning_source_revision_id:
        winning_source_revision_id = conflict.source_revision_id_for_claim(
            winning_claim_id
        )
    return ConflictResolution(
        resolution_id=resolution_id or new_id("res-"),
        conflict_id=conflict.conflict_id,
        outcome=outcome,
        winning_claim_id=winning_claim_id,
        winning_source_revision_id=winning_source_revision_id,
        basis=basis,
        residual_uncertainty=residual_uncertainty,
        resolved_by=resolved_by,
        is_machine_resolution=is_machine_resolution,
        user_confirmed=not is_machine_resolution,
    )


def make_resolution_log(
    project_id: str = "proj-alpha",
    *,
    conflicts: Optional[List[SourceConflict]] = None,
    resolutions: Optional[List[ConflictResolution]] = None,
) -> ConflictResolutionLog:
    log = ConflictResolutionLog(project_id=project_id)
    for c in (conflicts or []):
        log.record_conflict(c)
    for r in (resolutions or []):
        log.resolve(r)
    return log


# ---------------------------------------------------------------------------
# Three heterogeneous listing source shapes (anti-hardcoding)
# ---------------------------------------------------------------------------

def make_three_heterogeneous_listing_sources(
    project_id: str = "proj-alpha",
) -> Tuple[SourceRevision, SourceRevision, SourceRevision]:
    """Three listing sources with deliberately different structural shapes.

    Shape 1: wide/tabular AE listing (many columns, subject-keyed).
    Shape 2: narrow/vertical labs listing (key-value long form).
    Shape 3: multi-table workbook (domain-tagged scope).

    The byte content and scope facets differ so that downstream profiling /
    mapping / identity tests cannot hardcode one shape or path.
    """
    shape1 = SourceRevision.from_bytes(
        revision_id="rev-listing-wide-ae",
        project_id=project_id,
        source_type="listing",
        version="2026-06-01",
        source_bytes=(
            b"SUBJECT,AE_TERM,AE_START,AE_END,SEVERITY,SERIOUS\n"
            b"S001,Nausea,2026-02-01,2026-02-03,Mild,No\n"
            b"S002,Headache,2026-02-02,,Moderate,No\n"
        ),
        scope=(("shape", "wide_tabular"), ("domain", "ae"), ("dataset", "AE")),
        valid_from="2026-06-01",
    )
    shape2 = SourceRevision.from_bytes(
        revision_id="rev-listing-long-labs",
        project_id=project_id,
        source_type="listing",
        version="2026-06-01",
        source_bytes=(
            b"SUBJECT,PARAM,PARAMCD,VAL,UNIT,DAY\n"
            b"S001,ALT,ALT,45,U/L,1\n"
            b"S001,AST,AST,30,U/L,1\n"
        ),
        scope=(("shape", "long_keyvalue"), ("domain", "labs"), ("dataset", "LB")),
        valid_from="2026-06-01",
    )
    shape3 = SourceRevision.from_bytes(
        revision_id="rev-listing-workbook-multi",
        project_id=project_id,
        source_type="listing",
        version="2026-06-01",
        source_bytes=(
            b"[DM]\nSUBJECT,SEX,AGE\nS001,F,42\n"
            b"[AE]\nSUBJECT,AE_TERM\nS001,Fatigue\n"
        ),
        scope=(
            ("shape", "multi_table_workbook"),
            ("domain", "demography_ae"),
            ("dataset", "DM_AE"),
        ),
        valid_from="2026-06-01",
    )
    return shape1, shape2, shape3
