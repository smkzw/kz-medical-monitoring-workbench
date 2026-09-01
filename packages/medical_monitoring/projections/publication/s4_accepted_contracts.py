"""S4 externally accepted authority-anchor contracts."""

from .s4_contract_core import *
from .s4_packet_contracts import *

# ---------------------------------------------------------------------------
# External accepted-authority anchor typed objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class S4AcceptedHistoryState:
    """One accepted per-state history anchor.

    Errata: ``hash`` is ``genesis_or_sha`` -- only ``seq=0`` and
    ``head='genesis'`` allow ``hash='genesis'``; every other state must be a
    SHA-256.
    """

    seq: int
    head: str
    hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_int(
            self.seq, "S4AcceptedHistoryState.seq"))
        if self.seq < 0:
            raise S4RuntimeContractError(
                f"S4AcceptedHistoryState.seq must be >= 0, got {self.seq!r}")
        object.__setattr__(self, "head", _check_str(
            self.head, "S4AcceptedHistoryState.head"))
        if self.seq == 0 and self.head == GENESIS_HASH:
            if self.hash != GENESIS_HASH:
                raise S4RuntimeContractError(
                    "S4AcceptedHistoryState.hash must be 'genesis' when "
                    "seq=0 and head='genesis'")
        else:
            if not is_sha256_hex(self.hash):
                raise S4RuntimeContractError(
                    f"S4AcceptedHistoryState.hash {self.hash!r} must be a "
                    "sha256 hex for seq>0")


@dataclass(frozen=True)
class S4SourceRevisionPair:
    """One source revision -> content hash binding (packet/audit)."""

    revision_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", _check_str(
            self.revision_id, "S4SourceRevisionPair.revision_id"))
        object.__setattr__(self, "content_hash", _check_hash(
            self.content_hash, "S4SourceRevisionPair.content_hash"))


@dataclass(frozen=True)
class S4AcceptedAdjudicatorBinding:
    """Externally accepted adjudication binding identity."""

    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    outcome: str
    independent_context_hash: str

    def __post_init__(self) -> None:
        for name in ("binding_id", "session_id", "model_id", "model_version"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedAdjudicatorBinding.{name}"))
        object.__setattr__(self, "outcome", _check_closed(
            self.outcome, "S4AcceptedAdjudicatorBinding.outcome",
            ADJUDICATION_OUTCOMES))
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "S4AcceptedAdjudicatorBinding.independent_context_hash"))


@dataclass(frozen=True)
class S4AcceptedBaselineItem:
    """Externally accepted reference-baseline item (never packet-defined)."""

    item_id: str
    source_kind: str
    source_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    claimed_identity: str
    temporal_window: str
    claimed_content_hash: str
    origin_artifact_hash: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    source_revision: str

    def __post_init__(self) -> None:
        for name in ("item_id", "source_kind", "source_revision_id",
                     "snapshot_id", "claimed_identity", "temporal_window",
                     "project_ref", "run_ref", "snapshot_ref",
                     "source_revision"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedBaselineItem.{name}"))
        object.__setattr__(self, "source_locator_ids", _freeze_str_tuple(
            self.source_locator_ids, "S4AcceptedBaselineItem.source_locator_ids"))
        _require_nonempty_tuple(self.source_locator_ids,
                                "S4AcceptedBaselineItem.source_locator_ids")
        object.__setattr__(self, "claimed_content_hash", _check_hash(
            self.claimed_content_hash,
            "S4AcceptedBaselineItem.claimed_content_hash"))
        object.__setattr__(self, "origin_artifact_hash", _check_hash(
            self.origin_artifact_hash,
            "S4AcceptedBaselineItem.origin_artifact_hash"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "S4AcceptedBaselineItem.cutoff_ref"))


@dataclass(frozen=True)
class S4AcceptedQueryDraft:
    """Externally accepted three-part draft-only Query."""

    query_draft_id: str
    risk_ref: str
    basis_zh: str
    finding_zh: str
    action_zh: str
    source_locator_refs: Tuple[str, ...]
    pd_wording_state: str
    content_hash: str
    draft_only: bool

    def __post_init__(self) -> None:
        for name in ("query_draft_id", "basis_zh", "finding_zh", "action_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedQueryDraft.{name}"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "S4AcceptedQueryDraft.risk_ref"))
        if not is_marker_ref(self.risk_ref):
            raise S4RuntimeContractError(
                f"S4AcceptedQueryDraft.risk_ref {self.risk_ref!r} must be a "
                "marker")
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "S4AcceptedQueryDraft.source_locator_refs"))
        _require_nonempty_tuple(self.source_locator_refs,
                                "S4AcceptedQueryDraft.source_locator_refs")
        object.__setattr__(self, "pd_wording_state", _check_closed(
            self.pd_wording_state, "S4AcceptedQueryDraft.pd_wording_state",
            PD_WORDING_STATES))
        object.__setattr__(self, "content_hash", _check_hash(
            self.content_hash, "S4AcceptedQueryDraft.content_hash"))
        object.__setattr__(self, "draft_only", _check_bool(
            self.draft_only, "S4AcceptedQueryDraft.draft_only"))
        if not self.draft_only:
            raise S4RuntimeContractError(
                "S4AcceptedQueryDraft.draft_only must be True")


@dataclass(frozen=True)
class S4AcceptedRiskIdentity:
    """Externally accepted R5 risk-identity instance (authoritative)."""

    risk_ref: str
    risk_identity_hash: str
    domain: str
    domain_zh: str
    monitoring_priority: str
    severity: str
    severity_zh: str
    change_kind: str
    change_cause: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    spine_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "S4AcceptedRiskIdentity.risk_ref"))
        object.__setattr__(self, "risk_identity_hash", _check_hash(
            self.risk_identity_hash, "S4AcceptedRiskIdentity.risk_identity_hash"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "S4AcceptedRiskIdentity.domain", DOMAINS))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority,
            "S4AcceptedRiskIdentity.monitoring_priority", MONITORING_PRIORITIES))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "S4AcceptedRiskIdentity.severity", SEVERITIES))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "S4AcceptedRiskIdentity.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "change_cause", _check_closed(
            self.change_cause, "S4AcceptedRiskIdentity.change_cause", CHANGE_CAUSES))
        for name in ("project_ref", "run_ref", "snapshot_ref", "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedRiskIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4AcceptedRiskIdentity.{name}"))
        if self.domain_zh != DOMAIN_ZH[self.domain]:
            raise S4RuntimeContractError(
                f"S4AcceptedRiskIdentity.domain_zh {self.domain_zh!r} must be "
                f"the closed projection of domain {self.domain!r}")
        if self.severity_zh != SEVERITY_ZH_BY_SEVERITY[self.severity]:
            raise S4RuntimeContractError(
                f"S4AcceptedRiskIdentity.severity_zh {self.severity_zh!r} "
                f"must be the closed projection of severity {self.severity!r}")


@dataclass(frozen=True)
class S4AttemptAuthorityRow:
    """One accepted per-attempt authority row (input/content/rule binding)."""

    attempt_id: str
    model_id: str
    model_version: str
    input_content_hash: str
    artifact_ref: str
    parsed_output_hash: str
    raw_bytes_sha256: str
    date_window: str
    unit_contract: str
    source_revision: str
    rule_id: str
    rule_version: str

    def __post_init__(self) -> None:
        for name in ("attempt_id", "model_id", "model_version", "artifact_ref",
                     "date_window", "unit_contract", "source_revision",
                     "rule_id", "rule_version"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AttemptAuthorityRow.{name}"))
        for name in ("input_content_hash", "parsed_output_hash",
                     "raw_bytes_sha256"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"S4AttemptAuthorityRow.{name}"))


@dataclass(frozen=True)
class S4JourneyTargetIdentity:
    """Accepted Journey target identity (full project/run/snapshot/cutoff/
    site/subject/risk/event/visit/spine/anchor/source)."""

    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    risk_ref: str
    event_ref: Optional[str]
    visit_ref: Optional[str]
    spine_ref: str
    anchor_ref: str
    source_locator_ref: Optional[str]

    def __post_init__(self) -> None:
        for name in ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                     "spine_ref", "anchor_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4JourneyTargetIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref", "event_ref",
                     "visit_ref", "source_locator_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4JourneyTargetIdentity.{name}"))


@dataclass(frozen=True)
class S4ModelEvidencePermit:
    """Externally accepted D10 ModelEvidence permit (covers all 18 upstream
    fields)."""

    model_evidence_id: str
    role: str
    permitted_leaf: str
    model_id: str
    model_version: str
    evaluation_content_identity: str
    input_content_hash: str
    source_revision_content_pairs: Tuple[S4SourceRevisionPair, ...]
    source_refs: Tuple[str, ...]
    independent_context_hash: str
    ensemble_id: str
    ensemble_size: int
    member_analysis_refs: Tuple[str, ...]
    member_analysis_ref_set_hash: str
    output_identity: str
    output_hash: str
    adjudication_state: str
    model_binding_hash: str

    def __post_init__(self) -> None:
        for name in ("model_evidence_id", "role", "permitted_leaf", "model_id",
                     "model_version", "evaluation_content_identity",
                     "ensemble_id", "output_identity"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4ModelEvidencePermit.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "S4ModelEvidencePermit.role", MODEL_EVIDENCE_ROLES))
        object.__setattr__(self, "adjudication_state", _check_closed(
            self.adjudication_state,
            "S4ModelEvidencePermit.adjudication_state",
            MODEL_EVIDENCE_ADJUDICATION_STATES))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "S4ModelEvidencePermit.ensemble_size"))
        if self.ensemble_size < 1:
            raise S4RuntimeContractError(
                "S4ModelEvidencePermit.ensemble_size must be >= 1")
        for name in ("input_content_hash", "independent_context_hash",
                     "member_analysis_ref_set_hash", "output_hash",
                     "model_binding_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"S4ModelEvidencePermit.{name}"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "S4ModelEvidencePermit.source_revision_content_pairs",
                               S4SourceRevisionPair))
        object.__setattr__(self, "source_refs", _freeze_str_tuple(
            self.source_refs, "S4ModelEvidencePermit.source_refs"))
        object.__setattr__(self, "member_analysis_refs", _freeze_str_tuple(
            self.member_analysis_refs,
            "S4ModelEvidencePermit.member_analysis_refs"))


@dataclass(frozen=True)
class S4AcceptedAuthorityAnchor:
    """The external accepted-authority anchor (separate input; never packet-
    defined truth).  ``anchor_identity_hash`` is the R4-style canonical self
    hash excluding itself."""

    schema: str
    status: str
    authority_mode: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    risk_ref: str
    spine_ref: str
    risk_priority_authority: str
    severity_authority: str
    critical_severity_authority: Optional[str]
    accepted_receipt_content_hash: str
    accepted_receipt_identity: str
    accepted_risk_identity_hash: str
    accepted_risk_identity: S4AcceptedRiskIdentity
    accepted_adjudicator_binding: S4AcceptedAdjudicatorBinding
    accepted_baseline_items: Tuple[S4AcceptedBaselineItem, ...]
    accepted_query_draft: Optional[S4AcceptedQueryDraft]
    accepted_journey_target: S4JourneyTargetIdentity
    accepted_history_no_ensemble: S4AcceptedHistoryState
    accepted_history_single_analysis: S4AcceptedHistoryState
    accepted_history_multi_analysis: S4AcceptedHistoryState
    attempt_authority_rows: Tuple[S4AttemptAuthorityRow, ...]
    model_evidence_permits: Tuple[S4ModelEvidencePermit, ...]
    anchor_identity_hash: str

    def __post_init__(self) -> None:
        if self.schema != "medical-monitoring-r5-s4-authority-anchor-v0.1":
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor.schema must be "
                "medical-monitoring-r5-s4-authority-anchor-v0.1")
        if self.status != S4_STATUS:
            raise S4RuntimeContractError(
                f"S4AcceptedAuthorityAnchor.status must be {S4_STATUS!r}")
        if self.authority_mode != S4_AUTHORITY_MODE:
            raise S4RuntimeContractError(
                f"S4AcceptedAuthorityAnchor.authority_mode must be "
                f"{S4_AUTHORITY_MODE!r}")
        for name in ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                     "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedAuthorityAnchor.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref",
                     "critical_severity_authority"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4AcceptedAuthorityAnchor.{name}"))
        object.__setattr__(self, "risk_priority_authority", _check_closed(
            self.risk_priority_authority,
            "S4AcceptedAuthorityAnchor.risk_priority_authority",
            MONITORING_PRIORITIES))
        object.__setattr__(self, "severity_authority", _check_closed(
            self.severity_authority,
            "S4AcceptedAuthorityAnchor.severity_authority", SEVERITIES))
        if self.severity_authority == "critical" and \
                not self.critical_severity_authority:
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor requires critical_severity_authority "
                "when severity_authority is critical")
        object.__setattr__(self, "accepted_receipt_content_hash", _check_hash(
            self.accepted_receipt_content_hash,
            "S4AcceptedAuthorityAnchor.accepted_receipt_content_hash"))
        object.__setattr__(self, "accepted_receipt_identity", _check_str(
            self.accepted_receipt_identity,
            "S4AcceptedAuthorityAnchor.accepted_receipt_identity"))
        object.__setattr__(self, "accepted_risk_identity_hash", _check_hash(
            self.accepted_risk_identity_hash,
            "S4AcceptedAuthorityAnchor.accepted_risk_identity_hash"))
        _check_obj_type(self.accepted_risk_identity, S4AcceptedRiskIdentity,
                        "S4AcceptedAuthorityAnchor.accepted_risk_identity")
        _check_obj_type(self.accepted_adjudicator_binding,
                        S4AcceptedAdjudicatorBinding,
                        "S4AcceptedAuthorityAnchor.accepted_adjudicator_binding")
        object.__setattr__(self, "accepted_baseline_items", _freeze_obj_tuple(
            self.accepted_baseline_items,
            "S4AcceptedAuthorityAnchor.accepted_baseline_items",
            S4AcceptedBaselineItem))
        if self.accepted_query_draft is not None:
            _check_obj_type(self.accepted_query_draft, S4AcceptedQueryDraft,
                            "S4AcceptedAuthorityAnchor.accepted_query_draft")
        _check_obj_type(self.accepted_journey_target, S4JourneyTargetIdentity,
                        "S4AcceptedAuthorityAnchor.accepted_journey_target")
        for state_name in ("accepted_history_no_ensemble",
                           "accepted_history_single_analysis",
                           "accepted_history_multi_analysis"):
            _check_obj_type(getattr(self, state_name), S4AcceptedHistoryState,
                            f"S4AcceptedAuthorityAnchor.{state_name}")
        object.__setattr__(self, "attempt_authority_rows", _freeze_obj_tuple(
            self.attempt_authority_rows,
            "S4AcceptedAuthorityAnchor.attempt_authority_rows",
            S4AttemptAuthorityRow))
        object.__setattr__(self, "model_evidence_permits", _freeze_obj_tuple(
            self.model_evidence_permits,
            "S4AcceptedAuthorityAnchor.model_evidence_permits",
            S4ModelEvidencePermit))
        object.__setattr__(self, "anchor_identity_hash", _check_hash(
            self.anchor_identity_hash,
            "S4AcceptedAuthorityAnchor.anchor_identity_hash"))
        body = packet_as_mapping(self)
        if self.anchor_identity_hash != compute_anchor_identity_hash(body):
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor.anchor_identity_hash does not "
                "match the canonical self hash (excluding itself)")


__all__ = [name for name in globals() if not name.startswith("__")]
