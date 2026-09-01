"""S4 runtime input, build-state, history, and source contracts."""

from .s4_contract_core import *
from .s4_packet_contracts import *
from .s4_accepted_contracts import *

# ---------------------------------------------------------------------------
# Runtime-only wrappers (typed runtime input / build state)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S4RawOutputInput:
    """Raw-byte input (attempt + artifact identity, format, injected bytes)."""

    attempt_id: str
    artifact_id: str
    raw_format: str
    raw_bytes: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4RawOutputInput.attempt_id"))
        object.__setattr__(self, "artifact_id", _check_str(
            self.artifact_id, "R5S4RawOutputInput.artifact_id"))
        object.__setattr__(self, "raw_format", _check_closed(
            self.raw_format, "R5S4RawOutputInput.raw_format",
            RAW_OUTPUT_FORMATS))
        if not isinstance(self.raw_bytes, bytes):
            raise S4RuntimeContractError(
                "R5S4RawOutputInput.raw_bytes must be bytes")


@dataclass(frozen=True)
class R5S4AdjudicatorInput:
    """Runtime-only adjudicator wrapper: the R4 binding plus the S4 sealed
    independent context hash."""

    binding: AdjudicationBinding
    independent_context_hash: str

    def __post_init__(self) -> None:
        _check_obj_type(self.binding, AdjudicationBinding,
                        "R5S4AdjudicatorInput.binding")
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "R5S4AdjudicatorInput.independent_context_hash"))


@dataclass(frozen=True)
class R5S4SyntheticAudienceLabels:
    """Synthetic/offline display labels.  These affect display text only and
    never risk identity/domain/severity/verification/conflict/adjudication/
    Query/authority/hash semantics."""

    risk_title_zh: str
    project_display_zh: str
    center_display_zh: str
    subject_display_zh: str
    cutoff_display_zh: str

    def __post_init__(self) -> None:
        for name in ("risk_title_zh", "project_display_zh", "center_display_zh",
                     "subject_display_zh", "cutoff_display_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4SyntheticAudienceLabels.{name}"))


@dataclass(frozen=True)
class R5S4SourceInput:
    """Runtime-only source input.

    ``locatable`` must carry a non-null resolution and a null reason;
    ``unavailable`` must carry a null resolution and a non-null closed reason.
    No third combination is allowed.
    """

    availability_state: str
    resolution: Optional[R5S2SourceResolution]
    unavailable_reason: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "availability_state", _check_closed(
            self.availability_state, "R5S4SourceInput.availability_state",
            SOURCE_AVAILABILITY_STATES))
        if self.resolution is not None:
            _check_obj_type(self.resolution, R5S2SourceResolution,
                            "R5S4SourceInput.resolution")
        object.__setattr__(self, "unavailable_reason", _check_optional_str(
            self.unavailable_reason, "R5S4SourceInput.unavailable_reason"))
        if self.availability_state == "locatable":
            if self.resolution is None or self.unavailable_reason is not None:
                raise S4RuntimeContractError(
                    "locatable requires non-null resolution and null "
                    "unavailable_reason")
        else:  # unavailable
            if self.resolution is not None or \
                    self.unavailable_reason is None or \
                    self.unavailable_reason not in UNAVAILABLE_REASONS:
                raise S4RuntimeContractError(
                    "unavailable requires null resolution and a closed "
                    "unavailable_reason")


def validate_source_input_shape(source_input: "R5S4SourceInput") -> None:
    """Explicit shape gate for the runtime source input (fail closed on the
    third combination)."""
    if source_input.availability_state == "locatable":
        if source_input.resolution is None or \
                source_input.unavailable_reason is not None:
            raise S4RuntimeContractError(
                "R5S4SourceInput locatable requires resolution and no reason")
    elif source_input.availability_state == "unavailable":
        if source_input.resolution is not None or \
                source_input.unavailable_reason is None or \
                source_input.unavailable_reason not in UNAVAILABLE_REASONS:
            raise S4RuntimeContractError(
                "R5S4SourceInput unavailable requires reason and no resolution")
    else:
        raise S4RuntimeContractError(
            f"unknown availability_state {source_input.availability_state!r}")


@dataclass(frozen=True)
class R5S4RuntimeInput:
    """The single legal runtime input: typed external anchor + R4/R5 public
    typed objects + raw bytes + accepted history + synthetic labels."""

    anchor: S4AcceptedAuthorityAnchor
    authority_receipt: R5AuthorityReceipt
    upstream_inspector: R5RiskInspectorProjection
    change_band: R5ChangeBand
    deep_link_state: R5DeepLinkState
    source_input: R5S4SourceInput
    attempts: Tuple[AnalysisAttempt, ...]
    worker_outputs: Tuple[WorkerAnalysisOutput, ...]
    raw_outputs: Tuple[R5S4RawOutputInput, ...]
    baseline_items: Tuple[ReferenceBaselineItem, ...]
    digest_context: Optional[EvidenceDigestContext]
    adjudicator: Optional[R5S4AdjudicatorInput]
    model_evidence: Optional[ModelEvidence]
    query_draft: Optional[D10QueryDraft]
    history_log: R5S4HistoryLog
    audience_labels: R5S4SyntheticAudienceLabels

    def __post_init__(self) -> None:
        _check_obj_type(self.anchor, S4AcceptedAuthorityAnchor,
                        "R5S4RuntimeInput.anchor")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4RuntimeInput.authority_receipt")
        _check_obj_type(self.upstream_inspector, R5RiskInspectorProjection,
                        "R5S4RuntimeInput.upstream_inspector")
        _check_obj_type(self.change_band, R5ChangeBand,
                        "R5S4RuntimeInput.change_band")
        _check_obj_type(self.deep_link_state, R5DeepLinkState,
                        "R5S4RuntimeInput.deep_link_state")
        _check_obj_type(self.source_input, R5S4SourceInput,
                        "R5S4RuntimeInput.source_input")
        object.__setattr__(self, "attempts", _freeze_obj_tuple(
            self.attempts, "R5S4RuntimeInput.attempts", AnalysisAttempt))
        object.__setattr__(self, "worker_outputs", _freeze_obj_tuple(
            self.worker_outputs, "R5S4RuntimeInput.worker_outputs",
            WorkerAnalysisOutput))
        object.__setattr__(self, "raw_outputs", _freeze_obj_tuple(
            self.raw_outputs, "R5S4RuntimeInput.raw_outputs",
            R5S4RawOutputInput))
        object.__setattr__(self, "baseline_items", _freeze_obj_tuple(
            self.baseline_items, "R5S4RuntimeInput.baseline_items",
            ReferenceBaselineItem))
        if self.digest_context is not None:
            _check_obj_type(self.digest_context, EvidenceDigestContext,
                            "R5S4RuntimeInput.digest_context")
        if self.adjudicator is not None:
            _check_obj_type(self.adjudicator, R5S4AdjudicatorInput,
                            "R5S4RuntimeInput.adjudicator")
        if self.model_evidence is not None:
            _check_obj_type(self.model_evidence, ModelEvidence,
                            "R5S4RuntimeInput.model_evidence")
        if self.query_draft is not None:
            _check_obj_type(self.query_draft, D10QueryDraft,
                            "R5S4RuntimeInput.query_draft")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4RuntimeInput.history_log")
        _check_obj_type(self.audience_labels, R5S4SyntheticAudienceLabels,
                        "R5S4RuntimeInput.audience_labels")
        validate_source_input_shape(self.source_input)


@dataclass(frozen=True)
class R5S4BuildState:
    """Internal immutable build state produced by the builder and consumed by
    the projector/validator.  It never stores a candidate audience, audit or
    candidate hash; every repeated field is a tuple."""

    anchor: S4AcceptedAuthorityAnchor
    authority_receipt: R5AuthorityReceipt
    upstream_inspector: R5RiskInspectorProjection
    change_band: R5ChangeBand
    deep_link_state: R5DeepLinkState
    source_input: R5S4SourceInput
    risk_identity: R5S4RiskIdentity
    ensemble_id: str
    ensemble_projection_state: str
    input_content_hash: Optional[str]
    attempts: Tuple[AnalysisAttempt, ...]
    worker_outputs: Tuple[WorkerAnalysisOutput, ...]
    worker_views: Tuple[R5S4WorkerView, ...]
    raw_artifacts: Tuple[R5S4RawOutputArtifact, ...]
    baseline_items: Tuple[R5S4BaselineItemProjection, ...]
    baseline_rows: Tuple[R5S4BaselineRow, ...]
    verification_rows: Tuple[R5S4VerificationRow, ...]
    conflict_rows: Tuple[R5S4ConflictRow, ...]
    adjudication_row: R5S4AdjudicationRow
    query_draft_row: Optional[R5S4QueryDraftRow]
    journey_link: R5S4JourneyLink
    history_log: R5S4HistoryLog
    digest_context: Optional[EvidenceDigestContext]
    model_evidence: Optional[ModelEvidence]
    audience_labels: R5S4SyntheticAudienceLabels

    def __post_init__(self) -> None:
        _check_obj_type(self.anchor, S4AcceptedAuthorityAnchor,
                        "R5S4BuildState.anchor")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4BuildState.authority_receipt")
        _check_obj_type(self.risk_identity, R5S4RiskIdentity,
                        "R5S4BuildState.risk_identity")
        _check_obj_type(self.adjudication_row, R5S4AdjudicationRow,
                        "R5S4BuildState.adjudication_row")
        _check_obj_type(self.journey_link, R5S4JourneyLink,
                        "R5S4BuildState.journey_link")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4BuildState.history_log")


# ---------------------------------------------------------------------------
# History / source semantic helpers (shared by projection and validator)
# ---------------------------------------------------------------------------


def history_chain_valid(entries: Tuple[R5S4HistoryEntry, ...]) -> bool:
    """True iff the entry chain is contiguous and well-formed: seq strictly
    ``1..len``, first ``prior_entry_hash == 'genesis'``, every later
    ``prior_entry_hash`` equals the previous ``entry_hash``, and every
    ``entry_hash`` is the canonical chain hash."""
    if not entries:
        return True
    seqs = [entry.seq for entry in entries]
    if seqs != list(range(1, len(entries) + 1)):
        return False
    if entries[0].prior_entry_hash != GENESIS_HASH:
        return False
    for index in range(1, len(entries)):
        if entries[index].prior_entry_hash != entries[index - 1].entry_hash:
            return False
    for entry in entries:
        if entry.entry_hash != compute_history_entry_hash(entry):
            return False
    return True


def history_log_valid(log: R5S4HistoryLog) -> bool:
    """True iff the history log obeys the append-only + errata rules."""
    if not log.entries:
        return log.head_seq == 0 and log.head_hash == GENESIS_HASH
    if not history_chain_valid(log.entries):
        return False
    return log.head_seq == len(log.entries) and \
        log.head_hash == log.entries[-1].entry_hash


__all__ = [name for name in globals() if not name.startswith("__")]
