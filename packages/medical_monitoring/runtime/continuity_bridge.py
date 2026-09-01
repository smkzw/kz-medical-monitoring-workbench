"""Slice-08B authority, R6 mode output, and R1 artifact bridge for R7 continuity.

This module is the single narrow bridge seam for R7 Slice-08B.
It strictly reuses:
1. R5 typed packet: ``mm_r5.r5_publication_authority.R5AuthorityPacket``
2. R6 frozen ModeContract/validators: ``mm_r6.mode_output``
3. R1 Store & ArtifactEnvelope: ``mm_r1.domain.ArtifactEnvelope``, ``mm_r1.store.Store``
4. R7 continuity domain core: ``mm_r7.continuity``

It implements:
- R5 typed packet validation and member closure extraction
- R6 four outputs verification, cross-output set checks, and atomic item extraction
- R1 ArtifactEnvelope staging, committing, and byte-level verification
- Calculation of r6_output_set_digest, artifact_member_ids, artifact_member_set_digest
- 7-step carry-forward continuity verification and machine-computed CarryForwardItem construction
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

from ..domain.execution import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    ExecutionBasis,
    MonitoringRun,
    NodeType,
    PAYLOAD_ROLE_INFERENCE,
    RunMode,
    SourceRevision,
    StoreError,
)
from ..graph.store import Store
from ..projections.publication.r5_publication_authority import (
    R5AuthorityPacket,
    R5PublicationAuthorityError,
)
from ..reports import mode_output as mo
try:
    from .continuity import (
        OBJECT_TYPES,
        CarryForwardItem,
        determine_disposition,
    )
    from .launch_registry import content_digest
except ImportError:
    from mm_r7.continuity import (
        CarryForwardItem,
        determine_disposition,
    )
    from mm_r7.launch_registry import content_digest


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ContinuityBridgeError(ValueError):
    """Base error for all Slice-08B continuity bridge operations."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = code
        self.message = message or code
        super().__init__(f"{code}: {self.message}" if message else code)

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class R5AuthorityVerificationError(ContinuityBridgeError):
    """R5 publication authority packet failed validation or drifted."""


class R6OutputVerificationError(ContinuityBridgeError):
    """R6 ModeOutput envelope, output set, or post-lock set failed validation."""


class R1ArtifactVerificationError(ContinuityBridgeError):
    """R1 Store artifact staging, committing, or byte verification failed."""


class AtomicExtractionError(ContinuityBridgeError):
    """Extraction of atomic sub-items from R6 output failed closed."""


class ContinuityIntegrityError(ContinuityBridgeError):
    """Steps 1-6 continuity integrity verification failed closed."""


# ---------------------------------------------------------------------------
# Frozen Data Structures (DTOs)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedAtom:
    """Frozen DTO for an extracted atomic sub-item from an R6 ModeOutput."""

    object_type: str
    object_id: str
    output_kind: str
    output_id: str
    artifact_id: str = ""
    item_digest: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "output_kind": self.output_kind,
            "output_id": self.output_id,
            "artifact_id": self.artifact_id,
            "item_digest": self.item_digest,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class R5MemberClosure:
    """Frozen projection of authoritative members from an R5AuthorityPacket."""

    project_ref: str
    run_ref: str
    public_run_token: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_refs: Tuple[str, ...]
    risk_refs: Tuple[str, ...]
    subject_refs: Tuple[str, ...]
    s4_packet_ids: Tuple[str, ...]
    s4_packet_digests: Tuple[str, ...]

    def contains_risk(self, risk_id: str) -> bool:
        return risk_id in self.risk_refs

    def contains_subject(self, subject_id: str) -> bool:
        return subject_id in self.subject_refs

    def contains_site(self, site_id: str) -> bool:
        return site_id in self.site_refs


@dataclass(frozen=True)
class CommittedModeOutputSet:
    """Verified and committed set of four R6 ModeOutputs in R1 Store."""

    mode: str
    run_id: str
    outputs: Tuple[Mapping[str, Any], ...]
    envelopes: Tuple[ArtifactEnvelope, ...]
    output_records: Tuple[Mapping[str, str], ...]
    r6_output_set_digest: str
    artifact_member_ids: Tuple[str, ...]
    artifact_member_set_digest: str
    extracted_atoms: Tuple[ExtractedAtom, ...]


@dataclass(frozen=True)
class ContinuityVerificationResult:
    """Structured result of 7-step carry-forward verification."""

    item: CarryForwardItem
    integrity_ok: bool
    verified_disposition: str
    reasons: Tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Digest Helpers
# ---------------------------------------------------------------------------


def compute_r6_output_set_digest(
    output_records: Iterable[Mapping[str, str]],
) -> str:
    """Compute the canonical output-set digest for an R6 output set.

    Canonical contract:
    content_digest([
      {"artifact_id": artifact_id, "output_id": output_id, "output_kind": output_kind},
      ...sorted by (output_kind, output_id)
    ])
    """
    records = []
    for rec in output_records:
        if not isinstance(rec, Mapping):
            raise R6OutputVerificationError("INVALID_RECORD_MAPPING")
        art_id = str(rec.get("artifact_id", "")).strip()
        out_id = str(rec.get("output_id", "")).strip()
        out_kind = str(rec.get("output_kind", "")).strip()
        if not art_id or not out_id or not out_kind:
            raise R6OutputVerificationError("OUTPUT_RECORD_INCOMPLETE")
        records.append({
            "artifact_id": art_id,
            "output_id": out_id,
            "output_kind": out_kind,
        })
    sorted_records = sorted(records, key=lambda x: (x["output_kind"], x["output_id"]))
    return content_digest(sorted_records)


def compute_artifact_member_set_digest(
    artifact_member_ids: Iterable[str],
) -> str:
    """Compute the canonical member-set digest from sorted, unique artifact IDs."""
    members = tuple(sorted(set(str(item).strip() for item in artifact_member_ids if str(item).strip())))
    return content_digest(list(members))


# ---------------------------------------------------------------------------
# R5 Authority Packet Validation & Member Extraction
# ---------------------------------------------------------------------------


def validate_r5_authority_packet(
    packet: Any,
    *,
    run_binding: Optional[Mapping[str, Any]] = None,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    public_run_token: Optional[str] = None,
    snapshot_id: Optional[str] = None,
    data_cutoff: Optional[str] = None,
) -> R5AuthorityPacket:
    """Verify an R5AuthorityPacket against itself and optional run binding facts."""
    if not isinstance(packet, R5AuthorityPacket):
        raise R5AuthorityVerificationError(
            "R5_PACKET_TYPE_INVALID",
            f"expected R5AuthorityPacket, got {type(packet).__name__}",
        )

    expected_identity = "r5-publication-authority:" + packet.packet_digest
    if packet.packet_identity != expected_identity:
        raise R5AuthorityVerificationError(
            "R5_IDENTITY_MISMATCH",
            f"packet_identity {packet.packet_identity} does not match expected {expected_identity}",
        )

    if packet.authority_hash != packet.packet_digest:
        raise R5AuthorityVerificationError(
            "R5_AUTHORITY_HASH_MISMATCH",
            f"authority_hash {packet.authority_hash} does not match packet_digest {packet.packet_digest}",
        )

    try:
        # Reconstruct through the public frozen dataclass contract so R5 owns
        # member canonicalisation and digest validation.  This detects an
        # illicit ``object.__setattr__`` mutation without importing R5 private
        # hash helpers into the R7 bridge.
        replace(packet)
    except R5PublicationAuthorityError as exc:
        raise R5AuthorityVerificationError(
            "R5_PACKET_DIGEST_DRIFT",
            "typed R5 packet no longer validates against its members",
        ) from exc

    # Check against run_binding or explicit parameters
    binding = run_binding or {}
    expected_proj = binding.get("project_id") or project_id
    if expected_proj and packet.project_ref != expected_proj:
        raise R5AuthorityVerificationError(
            "R5_PROJECT_MISMATCH",
            f"R5 project {packet.project_ref} != expected {expected_proj}",
        )

    expected_run = binding.get("run_id") or run_id
    if expected_run and packet.run_ref != expected_run:
        raise R5AuthorityVerificationError(
            "R5_RUN_MISMATCH",
            f"R5 run {packet.run_ref} != expected {expected_run}",
        )

    expected_token = binding.get("public_run_token") or public_run_token
    if expected_token and packet.public_run_token != expected_token:
        raise R5AuthorityVerificationError(
            "R5_TOKEN_MISMATCH",
            f"R5 public token {packet.public_run_token} != expected {expected_token}",
        )

    expected_snap = (
        binding.get("snapshot_token")
        or binding.get("snapshot_id")
        or binding.get("snapshot_ref")
        or snapshot_id
    )
    if expected_snap and packet.snapshot_ref != expected_snap and packet.snapshot_token != expected_snap:
        raise R5AuthorityVerificationError(
            "R5_SNAPSHOT_MISMATCH",
            f"R5 snapshot {packet.snapshot_ref} != expected {expected_snap}",
        )

    expected_cutoff = binding.get("data_cutoff") or binding.get("cutoff_ref") or data_cutoff
    if expected_cutoff and packet.cutoff_ref != expected_cutoff:
        raise R5AuthorityVerificationError(
            "R5_CUTOFF_MISMATCH",
            f"R5 cutoff {packet.cutoff_ref} != expected {expected_cutoff}",
        )

    return packet


def extract_r5_member_closure(packet: R5AuthorityPacket) -> R5MemberClosure:
    """Extract authoritative member sets from an R5AuthorityPacket."""
    validate_r5_authority_packet(packet)

    risk_refs: Set[str] = set()
    for r in packet.risks:
        for attr in ("risk_id", "risk_ref", "risk_key", "risk_instance_ref", "risk_anchor_ref"):
            val = getattr(r, attr, None) if not isinstance(r, Mapping) else r.get(attr)
            if val and isinstance(val, str) and val.strip():
                risk_refs.add(val.strip())
    for s4 in packet.s4_packets:
        identity = getattr(s4, "risk_identity", None)
        if identity is not None:
            for attr in ("risk_ref", "risk_id"):
                val = getattr(identity, attr, None)
                if val and isinstance(val, str) and val.strip():
                    risk_refs.add(val.strip())

    subject_refs: Set[str] = set()
    for s in packet.subjects:
        for attr in ("subject_ref", "subject_id"):
            val = getattr(s, attr, None) if not isinstance(s, Mapping) else s.get(attr)
            if val and isinstance(val, str) and val.strip():
                subject_refs.add(val.strip())
    for s4 in packet.s4_packets:
        identity = getattr(s4, "risk_identity", None)
        if identity is not None:
            val = getattr(identity, "subject_ref", None)
            if val and isinstance(val, str) and val.strip():
                subject_refs.add(val.strip())

    site_refs: Set[str] = set(packet.site_refs)
    for site in packet.sites:
        for attr in ("site_ref", "site_id"):
            val = getattr(site, attr, None) if not isinstance(site, Mapping) else site.get(attr)
            if val and isinstance(val, str) and val.strip():
                site_refs.add(val.strip())
    for s4 in packet.s4_packets:
        identity = getattr(s4, "risk_identity", None)
        if identity is not None:
            val = getattr(identity, "site_ref", None)
            if val and isinstance(val, str) and val.strip():
                site_refs.add(val.strip())

    return R5MemberClosure(
        project_ref=packet.project_ref,
        run_ref=packet.run_ref,
        public_run_token=packet.public_run_token,
        snapshot_ref=packet.snapshot_ref,
        cutoff_ref=packet.cutoff_ref,
        site_refs=tuple(sorted(site_refs)),
        risk_refs=tuple(sorted(risk_refs)),
        subject_refs=tuple(sorted(subject_refs)),
        s4_packet_ids=tuple(sorted(packet.s4_packet_ids)),
        s4_packet_digests=tuple(sorted(packet.s4_packet_digests)),
    )


# ---------------------------------------------------------------------------
# Atomic Item Extraction (5 Paths)
# ---------------------------------------------------------------------------


def _check_draft_only(item: Mapping[str, Any]) -> None:
    """Ensure query draft fields strictly represent unsent, unclosed, unconfirmed draft."""
    status = item.get("status") or item.get("query_status") or "draft"
    if status != "draft":
        raise AtomicExtractionError(
            "QUERY_DRAFT_STATUS_NOT_DRAFT",
            f"query draft status is '{status}', must be 'draft'",
        )
    for forbidden_true in (
        "is_sent",
        "sent",
        "is_closed",
        "closed",
        "is_user_confirmed",
        "user_confirmed",
    ):
        if item.get(forbidden_true) is True:
            raise AtomicExtractionError(
                "QUERY_DRAFT_FORBIDDEN_FLAG",
                f"query draft has forbidden flag {forbidden_true}=True",
            )


def extract_atomic_items(
    outputs: Sequence[Mapping[str, Any]],
    *,
    mode: Optional[str] = None,
    output_artifact_map: Optional[Mapping[str, str]] = None,
    r5_packet: Optional[R5AuthorityPacket] = None,
) -> Tuple[ExtractedAtom, ...]:
    """Extract atomic sub-items strictly via the 5 authorized paths in Slice-08B.

    Paths:
    1. daily -> current_full_risk.payload.risks[] -> risk_instance (risk_id)
    2. daily -> affected_query_draft.payload.query_drafts[] -> query_draft (query_draft_id)
    3. pre_lock -> full_risk.payload.risks[] -> risk_instance (risk_id)
    4. post_lock_pre_cfdi -> site_materials.payload.materials[] -> mode_output_item (site_material_id)
    5. post_lock_pre_cfdi -> subject_materials.payload.materials[] -> mode_output_item (subject_material_id)
    """
    closure = extract_r5_member_closure(r5_packet) if r5_packet is not None else None
    artifact_map = output_artifact_map or {}
    atoms: List[ExtractedAtom] = []
    seen_identities: Set[Tuple[str, str]] = set()

    for output in outputs:
        if not isinstance(output, Mapping):
            raise AtomicExtractionError("INVALID_OUTPUT_MAPPING")
        output_kind = str(output.get("output_kind", "")).strip()
        output_id = str(output.get("output_id", "")).strip()
        if not output_kind or not output_id:
            raise AtomicExtractionError("OUTPUT_IDENTITY_MISSING")

        payload = output.get("payload")
        if not isinstance(payload, Mapping):
            raise AtomicExtractionError(
                "OUTPUT_PAYLOAD_INVALID",
                f"output {output_kind} payload must be a mapping",
            )

        artifact_id = artifact_map.get(output_id, "")

        # Path 1 & Path 3: risk_instance
        if output_kind in ("current_full_risk", "full_risk"):
            risks = payload.get("risks", [])
            if not isinstance(risks, Sequence) or isinstance(risks, (str, bytes)):
                raise AtomicExtractionError("RISKS_PAYLOAD_INVALID")
            for r in risks:
                if not isinstance(r, Mapping):
                    raise AtomicExtractionError("RISK_ITEM_INVALID")
                risk_id = str(r.get("risk_id", "")).strip()
                if not risk_id:
                    raise AtomicExtractionError("RISK_ID_MISSING")
                if closure is not None and not closure.contains_risk(risk_id):
                    raise AtomicExtractionError(
                        "RISK_NOT_IN_R5_AUTHORITY",
                        f"extracted risk_id {risk_id} not in R5 authority closure",
                    )
                ident = ("risk_instance", risk_id)
                if ident in seen_identities:
                    raise AtomicExtractionError(
                        "DUPLICATE_OBJECT_ID",
                        f"duplicate object identity {ident}",
                    )
                seen_identities.add(ident)
                digest = content_digest(r)
                atoms.append(
                    ExtractedAtom(
                        object_type="risk_instance",
                        object_id=risk_id,
                        output_kind=output_kind,
                        output_id=output_id,
                        artifact_id=artifact_id,
                        item_digest=digest,
                        payload=r,
                    )
                )

        # Path 2: query_draft
        elif output_kind == "affected_query_draft":
            drafts = payload.get("query_drafts", [])
            if not isinstance(drafts, Sequence) or isinstance(drafts, (str, bytes)):
                raise AtomicExtractionError("QUERY_DRAFTS_PAYLOAD_INVALID")
            for q in drafts:
                if not isinstance(q, Mapping):
                    raise AtomicExtractionError("QUERY_DRAFT_ITEM_INVALID")
                qid = str(q.get("query_draft_id", "")).strip()
                if not qid:
                    raise AtomicExtractionError("QUERY_DRAFT_ID_MISSING")
                _check_draft_only(q)
                if closure is not None:
                    q_risk = str(q.get("risk_id", "")).strip()
                    q_subj = str(q.get("subject_id", "")).strip()
                    q_site = str(q.get("site_id", "")).strip()
                    if q_risk and not closure.contains_risk(q_risk):
                        raise AtomicExtractionError(
                            "QUERY_DRAFT_RISK_NOT_IN_R5",
                            f"query draft {qid} references risk {q_risk} outside R5",
                        )
                    if q_subj and not closure.contains_subject(q_subj):
                        raise AtomicExtractionError(
                            "QUERY_DRAFT_SUBJECT_NOT_IN_R5",
                            f"query draft {qid} references subject {q_subj} outside R5",
                        )
                    if q_site and not closure.contains_site(q_site):
                        raise AtomicExtractionError(
                            "QUERY_DRAFT_SITE_NOT_IN_R5",
                            f"query draft {qid} references site {q_site} outside R5",
                        )
                ident = ("query_draft", qid)
                if ident in seen_identities:
                    raise AtomicExtractionError(
                        "DUPLICATE_OBJECT_ID",
                        f"duplicate object identity {ident}",
                    )
                seen_identities.add(ident)
                digest = content_digest(q)
                atoms.append(
                    ExtractedAtom(
                        object_type="query_draft",
                        object_id=qid,
                        output_kind=output_kind,
                        output_id=output_id,
                        artifact_id=artifact_id,
                        item_digest=digest,
                        payload=q,
                    )
                )

        # Path 4: site_materials
        elif output_kind == "site_materials":
            materials = payload.get("materials", [])
            if not isinstance(materials, Sequence) or isinstance(materials, (str, bytes)):
                raise AtomicExtractionError("SITE_MATERIALS_PAYLOAD_INVALID")
            for m in materials:
                if not isinstance(m, Mapping):
                    raise AtomicExtractionError("MATERIAL_ITEM_INVALID")
                mid = str(m.get("site_material_id", "")).strip()
                if not mid:
                    raise AtomicExtractionError("SITE_MATERIAL_ID_MISSING")
                if closure is not None:
                    site_id = str(m.get("site_id", "")).strip()
                    if site_id and not closure.contains_site(site_id):
                        raise AtomicExtractionError(
                            "MATERIAL_SITE_NOT_IN_R5",
                            f"material {mid} references site {site_id} outside R5",
                        )
                ident = ("mode_output_item", mid)
                if ident in seen_identities:
                    raise AtomicExtractionError(
                        "DUPLICATE_OBJECT_ID",
                        f"duplicate object identity {ident}",
                    )
                seen_identities.add(ident)
                digest = content_digest(m)
                atoms.append(
                    ExtractedAtom(
                        object_type="mode_output_item",
                        object_id=mid,
                        output_kind=output_kind,
                        output_id=output_id,
                        artifact_id=artifact_id,
                        item_digest=digest,
                        payload=m,
                    )
                )

        # Path 5: subject_materials
        elif output_kind == "subject_materials":
            materials = payload.get("materials", [])
            if not isinstance(materials, Sequence) or isinstance(materials, (str, bytes)):
                raise AtomicExtractionError("SUBJECT_MATERIALS_PAYLOAD_INVALID")
            for m in materials:
                if not isinstance(m, Mapping):
                    raise AtomicExtractionError("MATERIAL_ITEM_INVALID")
                mid = str(m.get("subject_material_id", "")).strip()
                if not mid:
                    raise AtomicExtractionError("SUBJECT_MATERIAL_ID_MISSING")
                if closure is not None:
                    subj_id = str(m.get("subject_id", "")).strip()
                    if subj_id and not closure.contains_subject(subj_id):
                        raise AtomicExtractionError(
                            "MATERIAL_SUBJECT_NOT_IN_R5",
                            f"material {mid} references subject {subj_id} outside R5",
                        )
                ident = ("mode_output_item", mid)
                if ident in seen_identities:
                    raise AtomicExtractionError(
                        "DUPLICATE_OBJECT_ID",
                        f"duplicate object identity {ident}",
                    )
                seen_identities.add(ident)
                digest = content_digest(m)
                atoms.append(
                    ExtractedAtom(
                        object_type="mode_output_item",
                        object_id=mid,
                        output_kind=output_kind,
                        output_id=output_id,
                        artifact_id=artifact_id,
                        item_digest=digest,
                        payload=m,
                    )
                )

    return tuple(sorted(atoms, key=lambda a: (a.object_type, a.object_id)))


# ---------------------------------------------------------------------------
# R1 Store Integration & Artifact Commitment
# ---------------------------------------------------------------------------


def build_mode_output_envelope(
    output: Mapping[str, Any],
    *,
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
) -> ArtifactEnvelope:
    """Construct an immutable ArtifactEnvelope for one R6 ModeOutput.

    Conforms to Contract v0.2 §16:
    - version = CONTRACT_VERSION
    - node_id = output["output_id"]
    - node_type = NodeType.DETERMINISTIC_SERVICE
    - payload = output
    - payload_role = PAYLOAD_ROLE_INFERENCE
    - input_hashes = [mode_contract_digest]
    - coverage = None
    - completeness = COMPLETE
    - evidence_refs = raw-output refs if provided
    """
    mc_digest = mo.mode_contract_digest(mode_contract)
    output_id = str(output.get("output_id", "")).strip()
    if not output_id:
        raise R6OutputVerificationError("OUTPUT_ID_MISSING")
    run_id = str(run_binding.get("run_id", "")).strip()
    if not run_id:
        raise R6OutputVerificationError("RUN_ID_MISSING")

    evidence_refs = list(output.get("evidence_refs") or [])
    return ArtifactEnvelope(
        artifact_type="r6_mode_output",
        version=mo.CONTRACT_VERSION,
        run_id=run_id,
        node_id=output_id,
        node_type=NodeType.DETERMINISTIC_SERVICE,
        payload=dict(output),
        payload_role=PAYLOAD_ROLE_INFERENCE,
        input_hashes=[mc_digest],
        evidence_refs=evidence_refs,
        coverage=None,
        completeness=ArtifactCompleteness.COMPLETE,
    )

def _ensure_store_run(store: Store, run_binding: Mapping[str, Any]) -> None:
    """Ensure the project, source revision, and monitoring run rows exist in R1 Store."""
    project_id = str(run_binding.get("project_id", "")).strip()
    run_id = str(run_binding.get("run_id", "")).strip()
    mode_val = str(run_binding.get("mode", "daily")).strip()
    source_revision_id = str(run_binding.get("source_revision_id", "")).strip()
    data_cutoff = str(run_binding.get("data_cutoff", "")).strip()
    execution_basis_val = str(run_binding.get("execution_basis", "full")).strip()

    if not project_id or not run_id:
        raise R1ArtifactVerificationError(
            "R1_RUN_BINDING_INCOMPLETE", "project_id and run_id are required"
        )

    try:
        store.get_project(project_id)
    except StoreError:
        try:
            store.create_project(project_id, f"Project {project_id}")
        except StoreError as exc:
            raise R1ArtifactVerificationError(
                "R1_PROJECT_BINDING_FAILED", str(exc)
            ) from exc

    if source_revision_id:
        try:
            store.get_source_revision(source_revision_id)
        except StoreError:
            try:
                store.add_source_revision(
                    SourceRevision(
                        revision_id=source_revision_id,
                        project_id=project_id,
                        source_type="listing",
                        version="v1",
                    )
                )
            except StoreError as exc:
                raise R1ArtifactVerificationError(
                    "R1_SOURCE_REVISION_BINDING_FAILED", str(exc)
                ) from exc

    try:
        run = store.get_run(run_id)
    except StoreError:
        run = None

    if run is None:
        try:
            run = store.create_run(
                MonitoringRun(
                    run_id=run_id,
                    project_id=project_id,
                    mode=RunMode(mode_val),
                    data_cutoff=data_cutoff,
                    source_revision_id=source_revision_id,
                    execution_basis=ExecutionBasis(execution_basis_val),
                )
            )
        except (StoreError, ValueError) as exc:
            raise R1ArtifactVerificationError(
                "R1_RUN_BINDING_FAILED", str(exc)
            ) from exc

    expected = (
        project_id,
        RunMode(mode_val),
        data_cutoff,
        source_revision_id,
        ExecutionBasis(execution_basis_val),
    )
    actual = (
        run.project_id,
        run.mode,
        run.data_cutoff,
        run.source_revision_id,
        run.execution_basis,
    )
    if actual != expected:
        raise R1ArtifactVerificationError(
            "R1_RUN_BINDING_CONFLICT",
            "existing R1 run identity does not match the R7 publication binding",
        )



def commit_mode_outputs(
    store: Store,
    outputs: Sequence[Mapping[str, Any]],
    *,
    run_binding: Mapping[str, Any],
    r5_packet: Optional[R5AuthorityPacket] = None,
) -> CommittedModeOutputSet:
    """Validate four ModeOutputs, stage and commit envelopes into R1 Store, and compute digests."""
    mode = str(run_binding.get("mode", "")).strip()
    run_id = str(run_binding.get("run_id", "")).strip()
    if mode not in mo.MODES:
        raise R6OutputVerificationError("UNSUPPORTED_MODE", f"mode '{mode}' not supported")

    mode_contract = mo.build_mode_contract(mode)
    contract_issues = mo.validate_mode_contract(mode_contract)
    if contract_issues:
        raise R6OutputVerificationError(
            "MODE_CONTRACT_INVALID",
            f"mode_contract failed validation: {contract_issues}",
        )
    _ensure_store_run(store, run_binding)


    # Validate R5 packet if passed
    if r5_packet is not None:
        validate_r5_authority_packet(r5_packet, run_binding=run_binding)

    # Check 4 required outputs
    if mode == "daily":
        expected_kinds = mo.DAILY_OUTPUT_KINDS
    elif mode == "pre_lock":
        expected_kinds = mo.PRE_LOCK_OUTPUT_KINDS
    elif mode == "post_lock_pre_cfdi":
        expected_kinds = mo.POST_LOCK_OUTPUT_KINDS
    else:
        raise R6OutputVerificationError("UNSUPPORTED_MODE")

    if len(outputs) != len(expected_kinds):
        raise R6OutputVerificationError(
            "OUTPUT_COUNT_MISMATCH",
            f"expected {len(expected_kinds)} outputs, got {len(outputs)}",
        )

    by_kind: Dict[str, Mapping[str, Any]] = {}
    for out in outputs:
        kind = out.get("output_kind")
        if kind in by_kind:
            raise R6OutputVerificationError("DUPLICATE_OUTPUT_KIND", f"duplicate kind {kind}")
        by_kind[kind] = out

    missing = set(expected_kinds) - set(by_kind)
    if missing:
        raise R6OutputVerificationError("MISSING_REQUIRED_OUTPUTS", f"missing kinds: {sorted(missing)}")
    extra = set(by_kind) - set(expected_kinds)
    if extra:
        raise R6OutputVerificationError("EXTRA_OUTPUTS_FORBIDDEN", f"extra kinds: {sorted(extra)}")

    # Validate each ModeOutput
    for out in outputs:
        issues = mo.validate_mode_output(out, run_binding, mode_contract)
        if issues:
            raise R6OutputVerificationError(
                "MODE_OUTPUT_INVALID",
                f"output {out.get('output_kind')} failed validation: {issues}",
            )

    # Validate post_lock cross-output set
    if mode == "post_lock_pre_cfdi":
        set_issues = mo.validate_post_lock_output_set(
            by_kind["full_project_report"],
            by_kind["site_materials"],
            by_kind["subject_materials"],
            by_kind["checklist"],
        )
        if set_issues:
            raise R6OutputVerificationError(
                "POST_LOCK_SET_INVALID",
                f"post_lock output set failed cross-output validation: {set_issues}",
            )

    # Stage & commit envelopes
    committed_envelopes: List[ArtifactEnvelope] = []
    output_records: List[Dict[str, str]] = []
    output_artifact_map: Dict[str, str] = {}

    for out in outputs:
        envelope = build_mode_output_envelope(
            out,
            run_binding=run_binding,
            mode_contract=mode_contract,
        )
        staged_hash = store.stage_artifact(envelope)
        committed = store.commit_artifact(staged_hash, envelope)
        if not store.verify_artifact(committed.artifact_id):
            raise R1ArtifactVerificationError(
                "ARTIFACT_VERIFICATION_FAILED",
                f"newly committed artifact {committed.artifact_id} failed verification",
            )
        committed_envelopes.append(committed)
        output_artifact_map[committed.node_id] = committed.artifact_id
        output_records.append({
            "artifact_id": committed.artifact_id,
            "output_id": committed.node_id,
            "output_kind": str(out["output_kind"]),
        })

    output_set_digest = compute_r6_output_set_digest(output_records)
    member_ids = tuple(sorted(set(r["artifact_id"] for r in output_records)))
    member_set_digest = compute_artifact_member_set_digest(member_ids)

    # Extract atoms
    atoms = extract_atomic_items(
        outputs,
        mode=mode,
        output_artifact_map=output_artifact_map,
        r5_packet=r5_packet,
    )

    return CommittedModeOutputSet(
        mode=mode,
        run_id=run_id,
        outputs=tuple(outputs),
        envelopes=tuple(committed_envelopes),
        output_records=tuple(sorted(output_records, key=lambda x: (x["output_kind"], x["output_id"]))),
        r6_output_set_digest=output_set_digest,
        artifact_member_ids=member_ids,
        artifact_member_set_digest=member_set_digest,
        extracted_atoms=atoms,
    )


# ---------------------------------------------------------------------------
# 7-Step Carry-Forward Verification & Machine-Computed Item Construction
# ---------------------------------------------------------------------------


def verify_carry_forward_item(
    item: CarryForwardItem,
    *,
    store: Store,
    publication: Mapping[str, Any],
    r5_packet: Optional[R5AuthorityPacket] = None,
    current_facts: Optional[Mapping[str, Any]] = None,
    current_rule_revision_ids: Optional[Sequence[str]] = None,
    reused_risk_ids: Optional[Iterable[str]] = None,
) -> ContinuityVerificationResult:
    """Execute the 7-step carry-forward verification algorithm (Contract v0.1 §5 + v0.2 §12).

    Steps 1-6 are evidence integrity checks: any failure raises ContinuityIntegrityError.
    Step 7 evaluates business applicability and computes the resulting disposition.
    """
    if not isinstance(item, CarryForwardItem):
        raise ContinuityBridgeError("INVALID_ITEM_TYPE", "expected CarryForwardItem")

    # Step 1: Publication baseline check
    pub_state = publication.get("publication_state")
    if pub_state != "available":
        raise ContinuityIntegrityError(
            "SOURCE_PUBLICATION_NOT_AVAILABLE",
            f"publication state is '{pub_state}', must be 'available'",
        )
    pub_proj = publication.get("project_id")
    if item.source_project_id and pub_proj != item.source_project_id:
        raise ContinuityIntegrityError(
            "PUBLICATION_PROJECT_MISMATCH",
            f"publication project {pub_proj} != item source_project {item.source_project_id}",
        )
    pub_mode = publication.get("mode")
    if item.source_mode and pub_mode != item.source_mode:
        raise ContinuityIntegrityError(
            "PUBLICATION_MODE_MISMATCH",
            f"publication mode {pub_mode} != item source_mode {item.source_mode}",
        )

    # Step 2: Member check
    member_ids_raw = publication.get("artifact_member_ids")
    if member_ids_raw is None:
        raw_json = publication.get("artifact_member_ids_json") or "[]"
        try:
            member_ids = set(json.loads(raw_json))
        except (json.JSONDecodeError, TypeError):
            member_ids = set()
    else:
        member_ids = set(member_ids_raw)

    if not item.source_artifact_id or item.source_artifact_id not in member_ids:
        raise ContinuityIntegrityError(
            "ARTIFACT_NOT_IN_PUBLICATION_MEMBERS",
            f"artifact {item.source_artifact_id} not in publication member IDs",
        )

    # Step 3: R1 Store envelope check
    envelope = store.get_artifact(item.source_artifact_id)
    if envelope is None:
        raise ContinuityIntegrityError(
            "ARTIFACT_NOT_FOUND_IN_STORE",
            f"artifact {item.source_artifact_id} not found in store",
        )
    if item.source_run_id and envelope.run_id != item.source_run_id:
        raise ContinuityIntegrityError(
            "ARTIFACT_RUN_ID_MISMATCH",
            f"envelope run_id {envelope.run_id} != item source_run_id {item.source_run_id}",
        )
    if envelope.artifact_type != "r6_mode_output":
        raise ContinuityIntegrityError(
            "ARTIFACT_TYPE_MISMATCH",
            f"envelope artifact_type {envelope.artifact_type} != 'r6_mode_output'",
        )
    if envelope.artifact_id != item.source_artifact_id:
        raise ContinuityIntegrityError("ARTIFACT_ID_MISMATCH")
    if item.source_artifact_sha256 and envelope.content_hash != item.source_artifact_sha256:
        raise ContinuityIntegrityError(
            "ARTIFACT_HASH_MISMATCH",
            f"content_hash {envelope.content_hash} != {item.source_artifact_sha256}",
        )

    # Step 4: R1 Store verification (content file bytes + raw evidence)
    if not store.verify_artifact(item.source_artifact_id):
        raise ContinuityIntegrityError(
            "ARTIFACT_STORE_VERIFICATION_FAILED",
            f"store.verify_artifact failed for {item.source_artifact_id}",
        )

    # Step 5: Inner ModeOutput R6 validator check
    mode_contract = mo.build_mode_contract(item.source_mode or pub_mode)
    out_binding = {
        "project_id": item.source_project_id or pub_proj,
        "run_id": item.source_run_id or publication.get("run_id", ""),
        "mode": item.source_mode or pub_mode,
        "execution_basis": envelope.payload.get("execution_basis", "full"),
        "data_cutoff": envelope.payload.get("data_cutoff", ""),
        "source_revision_id": envelope.payload.get("source_revision_id", ""),
        "knowledge_pack_version": envelope.payload.get("knowledge_pack_version", ""),
        "rule_activation_version": envelope.payload.get("rule_activation_version", ""),
        "mapping_version": envelope.payload.get("mapping_version", ""),
        "identity_algorithm_digest": envelope.payload.get("identity_algorithm_digest", ""),
    }
    mode_output_issues = mo.validate_mode_output(envelope.payload, out_binding, mode_contract)
    if mode_output_issues:
        raise ContinuityIntegrityError(
            "MODE_OUTPUT_REVALIDATION_FAILED",
            f"inner ModeOutput failed R6 validation: {mode_output_issues}",
        )

    # Step 6: Re-extract atomic sub-item & verify item_digest
    re_extracted = extract_atomic_items(
        [envelope.payload],
        mode=item.source_mode or pub_mode,
        output_artifact_map={envelope.node_id: envelope.artifact_id},
        r5_packet=r5_packet,
    )
    matching_atom = next(
        (a for a in re_extracted if a.object_type == item.object_type and a.object_id == item.source_object_id),
        None,
    )
    if matching_atom is None:
        raise ContinuityIntegrityError(
            "OBJECT_NOT_FOUND_IN_OUTPUT",
            f"object ({item.object_type}, {item.source_object_id}) not found in re-extracted output",
        )

    if item.source_identity and matching_atom.item_digest != item.source_identity:
        raise ContinuityIntegrityError(
            "ITEM_SOURCE_IDENTITY_MISMATCH",
            f"extracted item_digest {matching_atom.item_digest} != item.source_identity {item.source_identity}",
        )

    # Step 7: 08A Business applicability evaluation
    same_project = (item.source_project_id == item.target_project_id) if (item.source_project_id and item.target_project_id) else True
    same_mode = (item.source_mode == item.target_mode) if (item.source_mode and item.target_mode) else True

    # Section 12: Query draft dependency check
    query_risk_reused = True
    if item.object_type == "query_draft" and reused_risk_ids is not None:
        # Check if the query's associated risk is in reused_risk_ids
        q_payload = matching_atom.payload
        q_risk_id = str(q_payload.get("risk_id", "")).strip()
        if q_risk_id and q_risk_id not in set(reused_risk_ids):
            query_risk_reused = False

    prior_uncertain = not query_risk_reused

    disposition = determine_disposition(
        object_type=item.object_type,
        data_change_kind=item.data_change_kind,
        current_present=item.current_present,
        prior_risk_state=item.prior_risk_state,
        prior_severity=item.prior_severity,
        governing_rule_revision_ids=item.governing_rule_revision_ids,
        changed_applicable_rule_ids=item.changed_applicable_rule_ids,
        rule_applicability_known=item.rule_applicability_known,
        prior_uncertain=prior_uncertain,
        identity_compatible=item.identity_compatible,
        source_compatible=item.source_compatible,
        output_contract_compatible=item.output_contract_compatible,
        source_publication_state="available",
        same_project=same_project,
        same_mode=same_mode,
        source_artifact_id=item.source_artifact_id,
        source_artifact_sha256=item.source_artifact_sha256,
        artifact_verified=True,
        artifact_member_verified=True,
        reuse_reviewed=(not prior_uncertain and item.data_change_kind == "unchanged" and item.current_present),
        closure_evidence_refs=item.closure_evidence_refs,
        closure_allowed=item.closure_allowed,
        current_listing_complete=item.current_listing_complete,
        baseline_eligible=item.baseline_eligible,
        query_status=item.query_status,
        query_is_sent=item.query_is_sent,
        query_is_closed=item.query_is_closed,
        query_is_user_confirmed=item.query_is_user_confirmed,
    )

    return ContinuityVerificationResult(
        item=item,
        integrity_ok=True,
        verified_disposition=disposition,
        reasons=(),
        details={"matching_atom": matching_atom.as_dict()},
    )


def build_verified_carry_forward_item(
    item_or_mapping: Union[CarryForwardItem, Mapping[str, Any]],
    *,
    store: Store,
    publication: Mapping[str, Any],
    r5_packet: Optional[R5AuthorityPacket] = None,
    current_facts: Optional[Mapping[str, Any]] = None,
    current_rule_revision_ids: Optional[Sequence[str]] = None,
    reused_risk_ids: Optional[Iterable[str]] = None,
    ordinal: Optional[int] = None,
) -> CarryForwardItem:
    """Run full 7-step verification and return an immutable CarryForwardItem with machine-computed verification flags."""
    if isinstance(item_or_mapping, Mapping):
        data = dict(item_or_mapping)
        if ordinal is not None:
            data["ordinal"] = ordinal
        if not data.get("disposition"):
            data["disposition"] = "reuse_unchanged"
        item = CarryForwardItem(**data)
    elif isinstance(item_or_mapping, CarryForwardItem):
        item = item_or_mapping
    else:
        raise ContinuityBridgeError("INVALID_ITEM_INPUT")

    result = verify_carry_forward_item(
        item,
        store=store,
        publication=publication,
        r5_packet=r5_packet,
        current_facts=current_facts,
        current_rule_revision_ids=current_rule_revision_ids,
        reused_risk_ids=reused_risk_ids,
    )

    item_dict = item.as_dict(include_digest=False)
    matching_atom = result.details["matching_atom"]
    item_dict["source_object_id"] = matching_atom["object_id"]
    item_dict["source_identity"] = matching_atom["item_digest"]
    item_dict["target_object_id"] = item.target_object_id or item.object_ref
    item_dict["artifact_verified"] = True
    item_dict["artifact_member_verified"] = True
    item_dict["reuse_reviewed"] = (result.verified_disposition == "reuse_unchanged")
    item_dict["disposition"] = result.verified_disposition
    if ordinal is not None:
        item_dict["ordinal"] = ordinal

    return CarryForwardItem(**item_dict)


def build_verified_carry_forward_items(
    items: Iterable[Union[CarryForwardItem, Mapping[str, Any]]],
    *,
    store: Store,
    publication: Mapping[str, Any],
    r5_packet: Optional[R5AuthorityPacket] = None,
    current_facts: Optional[Mapping[str, Any]] = None,
    current_rule_revision_ids: Optional[Sequence[str]] = None,
) -> Tuple[CarryForwardItem, ...]:
    """Verify a collection of items in sequence, resolving cross-object risk dependencies for queries."""
    input_items = list(items)

    # First pass: identify which risk items will achieve reuse_unchanged
    reused_risk_ids: Set[str] = set()
    for item in input_items:
        obj_type = item.object_type if isinstance(item, CarryForwardItem) else item.get("object_type")
        obj_id = item.source_object_id if isinstance(item, CarryForwardItem) else item.get("source_object_id")
        if obj_type == "risk_instance":
            try:
                verified_risk = build_verified_carry_forward_item(
                    item,
                    store=store,
                    publication=publication,
                    r5_packet=r5_packet,
                    current_facts=current_facts,
                    current_rule_revision_ids=current_rule_revision_ids,
                )
                if verified_risk.disposition == "reuse_unchanged":
                    reused_risk_ids.add(obj_id)
            except ContinuityIntegrityError:
                pass

    # Second pass: build all items with reused_risk_ids context
    out_items: List[CarryForwardItem] = []
    for ord_idx, item in enumerate(input_items):
        verified = build_verified_carry_forward_item(
            item,
            store=store,
            publication=publication,
            r5_packet=r5_packet,
            current_facts=current_facts,
            current_rule_revision_ids=current_rule_revision_ids,
            reused_risk_ids=reused_risk_ids,
            ordinal=ord_idx,
        )
        out_items.append(verified)

    return tuple(out_items)


__all__ = [
    "AtomicExtractionError",
    "CommittedModeOutputSet",
    "ContinuityBridgeError",
    "ContinuityIntegrityError",
    "ContinuityVerificationResult",
    "ExtractedAtom",
    "R1ArtifactVerificationError",
    "R5AuthorityVerificationError",
    "R5MemberClosure",
    "R6OutputVerificationError",
    "build_mode_output_envelope",
    "build_verified_carry_forward_item",
    "build_verified_carry_forward_items",
    "commit_mode_outputs",
    "compute_artifact_member_set_digest",
    "compute_r6_output_set_digest",
    "extract_atomic_items",
    "extract_r5_member_closure",
    "validate_r5_authority_packet",
    "verify_carry_forward_item",
]
