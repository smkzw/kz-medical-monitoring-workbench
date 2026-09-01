"""S4 packet, audience, audit, verification, and history contracts."""

from .s4_contract_core import *

# ---------------------------------------------------------------------------
# Packet typed objects (exact keys from the accepted machine schema)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S4RiskIdentity:
    """Root risk identity (audience/root plane).  ``risk_identity_hash`` is
    the externally accepted R4 public risk identity hash (accepted leaf; the
    runtime treats the external anchor instance as authoritative)."""

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
            self.risk_ref, "R5S4RiskIdentity.risk_ref"))
        object.__setattr__(self, "risk_identity_hash", _check_hash(
            self.risk_identity_hash, "R5S4RiskIdentity.risk_identity_hash"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5S4RiskIdentity.domain", DOMAINS))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority,
            "R5S4RiskIdentity.monitoring_priority", MONITORING_PRIORITIES))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5S4RiskIdentity.severity", SEVERITIES))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "R5S4RiskIdentity.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "change_cause", _check_closed(
            self.change_cause, "R5S4RiskIdentity.change_cause", CHANGE_CAUSES))
        for name in ("project_ref", "run_ref", "snapshot_ref", "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4RiskIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4RiskIdentity.{name}"))
        if self.domain_zh != DOMAIN_ZH[self.domain]:
            raise S4RuntimeContractError(
                f"R5S4RiskIdentity.domain_zh {self.domain_zh!r} must be the "
                f"closed projection of domain {self.domain!r}")
        if self.severity_zh != SEVERITY_ZH_BY_SEVERITY[self.severity]:
            raise S4RuntimeContractError(
                f"R5S4RiskIdentity.severity_zh {self.severity_zh!r} must be "
                f"the closed projection of severity {self.severity!r}")


@dataclass(frozen=True)
class R5S4WorkerView:
    """One worker attempt's audit view (audit plane)."""

    attempt_id: str
    ordinal: int
    ordinal_zh: str
    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    role: str
    independent_context_hash: str
    input_content_hash: str
    output_artifact_ref: str
    declared_output_hash: str
    claimed_date_window: str
    claimed_unit_contract: str
    claimed_source_revision: str
    claimed_rule_id: str
    claimed_rule_version: str
    assessment_row_refs: Tuple[str, ...]
    finding_ids: Tuple[str, ...]
    gap_ids: Tuple[str, ...]
    raw_artifact_ref: str
    verification_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4WorkerView.attempt_id"))
        object.__setattr__(self, "ordinal", _check_int(
            self.ordinal, "R5S4WorkerView.ordinal"))
        if not (1 <= self.ordinal <= len(ORDINAL_ZH)):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.ordinal must be 1..{len(ORDINAL_ZH)}, got "
                f"{self.ordinal!r}")
        if self.ordinal_zh != ORDINAL_ZH[self.ordinal - 1]:
            raise S4RuntimeContractError(
                f"R5S4WorkerView.ordinal_zh {self.ordinal_zh!r} must be the "
                f"closed label of ordinal {self.ordinal}")
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4WorkerView.role", ATTEMPT_ROLES))
        if self.role != "worker":
            raise S4RuntimeContractError(
                "R5S4WorkerView.role must be 'worker', got "
                f"{self.role!r}")
        for name in ("binding_id", "session_id", "model_id", "model_version",
                     "claimed_date_window", "claimed_unit_contract",
                     "claimed_source_revision", "claimed_rule_id",
                     "claimed_rule_version", "output_artifact_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4WorkerView.{name}"))
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "R5S4WorkerView.independent_context_hash"))
        object.__setattr__(self, "input_content_hash", _check_hash(
            self.input_content_hash, "R5S4WorkerView.input_content_hash"))
        object.__setattr__(self, "declared_output_hash", _check_hash(
            self.declared_output_hash, "R5S4WorkerView.declared_output_hash"))
        for name in ("assessment_row_refs", "finding_ids", "gap_ids"):
            object.__setattr__(self, name, _freeze_str_tuple(
                getattr(self, name), f"R5S4WorkerView.{name}"))
        if not matches_grammar(self.raw_artifact_ref, "raw"):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.raw_artifact_ref {self.raw_artifact_ref!r} "
                f"must match raw:<ref>")
        if not matches_grammar(self.verification_ref, "verification"):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.verification_ref {self.verification_ref!r} "
                f"must match verification:<ref>")


@dataclass(frozen=True)
class R5S4RawOutputArtifact:
    """One raw-byte artifact (raw/parsed hash strictly separated)."""

    artifact_id: str
    attempt_id: str
    raw_format: str
    raw_bytes_b64: str
    raw_bytes_sha256: str
    parsed_output_hash: str
    declared_output_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_id", _check_str(
            self.artifact_id, "R5S4RawOutputArtifact.artifact_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4RawOutputArtifact.attempt_id"))
        object.__setattr__(self, "raw_format", _check_closed(
            self.raw_format, "R5S4RawOutputArtifact.raw_format",
            RAW_OUTPUT_FORMATS))
        object.__setattr__(self, "raw_bytes_b64", _check_str(
            self.raw_bytes_b64, "R5S4RawOutputArtifact.raw_bytes_b64"))
        object.__setattr__(self, "parsed_output_hash", _check_hash(
            self.parsed_output_hash,
            "R5S4RawOutputArtifact.parsed_output_hash"))
        object.__setattr__(self, "declared_output_hash", _check_hash(
            self.declared_output_hash,
            "R5S4RawOutputArtifact.declared_output_hash"))
        if self.declared_output_hash != self.parsed_output_hash:
            raise S4RuntimeContractError(
                "R5S4RawOutputArtifact.declared_output_hash must equal "
                "parsed_output_hash")
        # raw_bytes_sha256 is the canonical sha of the decoded raw bytes.
        try:
            raw_bytes = base64.b64decode(self.raw_bytes_b64, validate=True)
        except Exception as exc:
            raise S4RuntimeContractError(
                "R5S4RawOutputArtifact.raw_bytes_b64 is not valid base64: "
                f"{exc}") from None
        expected_sha = hashlib.sha256(raw_bytes).hexdigest()
        object.__setattr__(self, "raw_bytes_sha256", _check_hash(
            self.raw_bytes_sha256,
            "R5S4RawOutputArtifact.raw_bytes_sha256"))
        if self.raw_bytes_sha256 != expected_sha:
            raise S4RuntimeContractError(
                f"R5S4RawOutputArtifact.raw_bytes_sha256 "
                f"{self.raw_bytes_sha256!r} does not match "
                f"sha256(raw bytes) {expected_sha!r}")


@dataclass(frozen=True)
class R5S4BaselineItemProjection:
    """One packet baseline item: the imported R4 ``ReferenceBaselineItem``
    leaves plus the five approved import-extension fields
    (``project_ref``/``run_ref``/``snapshot_ref``/``cutoff_ref``/
    ``source_revision``) declared by the accepted machine schema's
    ``import_extensions``.  This is the exact typed shape a packet
    ``baseline_items`` entry must carry so the packet dict matches the machine
    schema."""

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
                     "snapshot_id", "claimed_identity", "temporal_window"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4BaselineItemProjection.{name}"))
        object.__setattr__(self, "source_locator_ids", _freeze_str_tuple(
            self.source_locator_ids,
            "R5S4BaselineItemProjection.source_locator_ids"))
        object.__setattr__(self, "claimed_content_hash", _check_hash(
            self.claimed_content_hash,
            "R5S4BaselineItemProjection.claimed_content_hash"))
        object.__setattr__(self, "origin_artifact_hash", _check_hash(
            self.origin_artifact_hash,
            "R5S4BaselineItemProjection.origin_artifact_hash"))
        for name, grammar in (("project_ref", PROJECT_REF_GRAMMAR),
                              ("run_ref", RUN_REF_GRAMMAR),
                              ("snapshot_ref", SNAPSHOT_REF_GRAMMAR),
                              ("source_revision", SOURCE_REVISION_GRAMMAR)):
            value = _check_str(getattr(self, name),
                               f"R5S4BaselineItemProjection.{name}")
            if not grammar.match(value):
                raise S4RuntimeContractError(
                    f"R5S4BaselineItemProjection.{name} {value!r} must match "
                    f"{grammar.pattern}")
            object.__setattr__(self, name, value)
        if self.cutoff_ref is not None:
            cutoff = _check_str(self.cutoff_ref,
                                "R5S4BaselineItemProjection.cutoff_ref")
            if not CUTOFF_REF_GRAMMAR.match(cutoff):
                raise S4RuntimeContractError(
                    f"R5S4BaselineItemProjection.cutoff_ref {cutoff!r} must "
                    f"match {CUTOFF_REF_GRAMMAR.pattern}")
            object.__setattr__(self, "cutoff_ref", cutoff)


@dataclass(frozen=True)
class R5S4BaselineRow:
    """One item x attempt six-state recheck row."""

    row_ref: str
    item_id: str
    attempt_id: str
    state: str
    reason_codes: Tuple[str, ...]
    source_recheck_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    recheck_complete: bool

    def __post_init__(self) -> None:
        if not matches_grammar(self.row_ref, "baseline_row"):
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.row_ref {self.row_ref!r} must match "
                f"baseline-row:<item_id>:<attempt_id>")
        parts = self.row_ref.split(":", 2)
        if len(parts) != 3 or parts[1] != self.item_id \
                or parts[2] != self.attempt_id:
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.row_ref {self.row_ref!r} must be "
                f"baseline-row:{self.item_id}:{self.attempt_id}")
        object.__setattr__(self, "item_id", _check_str(
            self.item_id, "R5S4BaselineRow.item_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4BaselineRow.attempt_id"))
        object.__setattr__(self, "state", _check_closed(
            self.state, "R5S4BaselineRow.state", BASELINE_STATES))
        object.__setattr__(self, "reason_codes", _freeze_closed_tuple(
            self.reason_codes, "R5S4BaselineRow.reason_codes",
            ASSESSMENT_REASON_CODES))
        object.__setattr__(self, "source_recheck_locator_ids",
                           _freeze_str_tuple(
                               self.source_recheck_locator_ids,
                               "R5S4BaselineRow.source_recheck_locator_ids"))
        object.__setattr__(self, "source_revision_id", _check_str(
            self.source_revision_id, "R5S4BaselineRow.source_revision_id"))
        object.__setattr__(self, "snapshot_id", _check_str(
            self.snapshot_id, "R5S4BaselineRow.snapshot_id"))
        object.__setattr__(self, "recheck_complete", _check_bool(
            self.recheck_complete, "R5S4BaselineRow.recheck_complete"))
        if self.state in RECHECK_REQUIRED_STATES and \
                not self.source_recheck_locator_ids:
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.state {self.state!r} requires non-empty "
                "source_recheck_locator_ids (recheck_required_implies_locators)")


@dataclass(frozen=True)
class R5S4ConflictRow:
    """One cross-attempt disagreement kept visible after merge."""

    conflict_id: str
    relation: str
    display_state: str
    hidden: bool
    monitoring_priority: str
    member_attempt_ids: Tuple[str, ...]
    ordinal_labels_zh: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_id", _check_str(
            self.conflict_id, "R5S4ConflictRow.conflict_id"))
        object.__setattr__(self, "relation", _check_closed(
            self.relation, "R5S4ConflictRow.relation", CONFLICT_RELATIONS))
        object.__setattr__(self, "display_state", _check_closed(
            self.display_state, "R5S4ConflictRow.display_state",
            CONFLICT_DISPLAY_STATES))
        object.__setattr__(self, "hidden", _check_bool(
            self.hidden, "R5S4ConflictRow.hidden"))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority, "R5S4ConflictRow.monitoring_priority",
            MONITORING_PRIORITIES))
        object.__setattr__(self, "member_attempt_ids", _freeze_str_tuple(
            self.member_attempt_ids, "R5S4ConflictRow.member_attempt_ids"))
        _require_nonempty_tuple(self.member_attempt_ids,
                                "R5S4ConflictRow.member_attempt_ids")
        object.__setattr__(self, "ordinal_labels_zh", _freeze_str_tuple(
            self.ordinal_labels_zh, "R5S4ConflictRow.ordinal_labels_zh"))
        _require_nonempty_tuple(self.ordinal_labels_zh,
                                "R5S4ConflictRow.ordinal_labels_zh")
        if self.relation in NON_HIDEABLE_RELATIONS and self.hidden:
            raise S4RuntimeContractError(
                f"R5S4ConflictRow.relation {self.relation!r} is "
                "non-hideable (hidden must be False)")


@dataclass(frozen=True)
class R5S4VerificationRow:
    """One attempt's deterministic verification record (recomputed)."""

    verification_id: str
    attempt_id: str
    checked_dimensions: Tuple[str, ...]
    result: str
    failure_reason_codes: Tuple[str, ...]
    recomputed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "verification_id", _check_str(
            self.verification_id, "R5S4VerificationRow.verification_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4VerificationRow.attempt_id"))
        object.__setattr__(self, "checked_dimensions", _freeze_closed_tuple(
            self.checked_dimensions, "R5S4VerificationRow.checked_dimensions",
            VERIFICATION_DIMENSIONS))
        _require_exact_count(self.checked_dimensions, len(SEVEN_DIMENSIONS),
                             "R5S4VerificationRow.checked_dimensions")
        if set(self.checked_dimensions) != SEVEN_DIMENSIONS:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.checked_dimensions must be exactly the "
                "seven frozen dimensions")
        object.__setattr__(self, "result", _check_closed(
            self.result, "R5S4VerificationRow.result", VERIFICATION_RESULTS))
        object.__setattr__(self, "failure_reason_codes", _freeze_closed_tuple(
            self.failure_reason_codes,
            "R5S4VerificationRow.failure_reason_codes",
            VERIFICATION_FAILURE_CODES))
        object.__setattr__(self, "recomputed", _check_bool(
            self.recomputed, "R5S4VerificationRow.recomputed"))
        if not self.recomputed:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.recomputed must be True")
        if self.result == "passed" and self.failure_reason_codes:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.result=passed carries no failure codes")


@dataclass(frozen=True)
class R5S4AdjudicationRow:
    """Independent adjudication record (present only for N>=2)."""

    present: bool
    binding_id: Optional[str]
    session_id: Optional[str]
    model_id: Optional[str]
    model_version: Optional[str]
    independent_context_hash: Optional[str]
    outcome: Optional[str]
    reviewed_artifact_refs: Tuple[str, ...]
    adds_explanation_only: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "present", _check_bool(
            self.present, "R5S4AdjudicationRow.present"))
        object.__setattr__(self, "reviewed_artifact_refs", _freeze_str_tuple(
            self.reviewed_artifact_refs,
            "R5S4AdjudicationRow.reviewed_artifact_refs"))
        object.__setattr__(self, "adds_explanation_only", _check_bool(
            self.adds_explanation_only, "R5S4AdjudicationRow.adds_explanation_only"))
        if not self.adds_explanation_only:
            raise S4RuntimeContractError(
                "R5S4AdjudicationRow.adds_explanation_only must be True")
        required = ("binding_id", "session_id", "model_id", "model_version",
                    "independent_context_hash", "outcome")
        if self.present:
            for name in required:
                value = getattr(self, name)
                if name == "independent_context_hash":
                    object.__setattr__(
                        self, name, _check_hash(value,
                                                f"R5S4AdjudicationRow.{name}"))
                else:
                    object.__setattr__(self, name, _check_str(
                        value, f"R5S4AdjudicationRow.{name}"))
            object.__setattr__(self, "outcome", _check_closed(
                self.outcome, "R5S4AdjudicationRow.outcome",
                ADJUDICATION_OUTCOMES))
            _require_nonempty_tuple(
                self.reviewed_artifact_refs,
                "R5S4AdjudicationRow.reviewed_artifact_refs")
        else:
            # present=False forbids a real value; None and the empty string
            # are both "absent" (the accepted machine shape uses "" for the
            # str fields and None for independent_context_hash).
            for name in required:
                value = getattr(self, name)
                if value not in (None, ""):
                    raise S4RuntimeContractError(
                        f"R5S4AdjudicationRow.{name} must be absent when "
                        "present=False")
            if self.reviewed_artifact_refs:
                raise S4RuntimeContractError(
                    "R5S4AdjudicationRow.reviewed_artifact_refs must be empty "
                    "when present=False")


@dataclass(frozen=True)
class R5S4QueryDraftRow:
    """Three-part draft-only Query (draft_only always True; structural task
    keys forbidden)."""

    query_draft_id: str
    risk_ref: str
    basis_zh: str
    finding_zh: str
    action_zh: str
    source_locator_refs: Tuple[str, ...]
    pd_wording_state: str
    draft_only: bool

    def __post_init__(self) -> None:
        for name in ("query_draft_id", "basis_zh", "finding_zh", "action_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4QueryDraftRow.{name}"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5S4QueryDraftRow.risk_ref"))
        if not is_marker_ref(self.risk_ref):
            raise S4RuntimeContractError(
                f"R5S4QueryDraftRow.risk_ref {self.risk_ref!r} must be a "
                "d09_marker:/d10_marker: marker")
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5S4QueryDraftRow.source_locator_refs"))
        _require_nonempty_tuple(self.source_locator_refs,
                                "R5S4QueryDraftRow.source_locator_refs")
        object.__setattr__(self, "pd_wording_state", _check_closed(
            self.pd_wording_state, "R5S4QueryDraftRow.pd_wording_state",
            PD_WORDING_STATES))
        object.__setattr__(self, "draft_only", _check_bool(
            self.draft_only, "R5S4QueryDraftRow.draft_only"))
        if not self.draft_only:
            raise S4RuntimeContractError(
                "R5S4QueryDraftRow.draft_only must be True")


@dataclass(frozen=True)
class R5S4JourneyLink:
    """Journey deep-link identity (fallback_policy=none; never nearest
    fallback)."""

    deep_link_project_ref: str
    deep_link_run_ref: str
    deep_link_snapshot_ref: str
    deep_link_cutoff_ref: Optional[str]
    deep_link_site_ref: Optional[str]
    deep_link_subject_ref: Optional[str]
    deep_link_risk_ref: str
    deep_link_event_ref: Optional[str]
    deep_link_visit_ref: Optional[str]
    deep_link_spine_ref: str
    deep_link_anchor_ref: str
    deep_link_source_locator_ref: Optional[str]
    fallback_policy: str
    journey_available: bool
    unavailable_reason_zh: Optional[str]

    def __post_init__(self) -> None:
        for name in ("deep_link_project_ref", "deep_link_run_ref",
                     "deep_link_snapshot_ref", "deep_link_risk_ref",
                     "deep_link_spine_ref", "deep_link_anchor_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4JourneyLink.{name}"))
        for name in ("deep_link_cutoff_ref", "deep_link_site_ref",
                     "deep_link_subject_ref", "deep_link_event_ref",
                     "deep_link_visit_ref", "deep_link_source_locator_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4JourneyLink.{name}"))
        object.__setattr__(self, "fallback_policy", _check_closed(
            self.fallback_policy, "R5S4JourneyLink.fallback_policy",
            FALLBACK_POLICIES))
        if self.fallback_policy != "none":
            raise S4RuntimeContractError(
                "R5S4JourneyLink.fallback_policy must be 'none'")
        object.__setattr__(self, "journey_available", _check_bool(
            self.journey_available, "R5S4JourneyLink.journey_available"))
        object.__setattr__(self, "unavailable_reason_zh", _check_optional_str(
            self.unavailable_reason_zh,
            "R5S4JourneyLink.unavailable_reason_zh"))
        if self.journey_available and self.unavailable_reason_zh is not None:
            raise S4RuntimeContractError(
                "R5S4JourneyLink.unavailable_reason_zh must be None when "
                "journey_available=True")


@dataclass(frozen=True)
class R5S4HistoryEntry:
    """One append-only history entry (hash chain includes prior_entry_hash)."""

    entry_id: str
    seq: int
    kind: str
    payload_ref: str
    prior_entry_hash: str
    entry_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_id", _check_str(
            self.entry_id, "R5S4HistoryEntry.entry_id"))
        object.__setattr__(self, "seq", _check_int(
            self.seq, "R5S4HistoryEntry.seq"))
        if self.seq < 1:
            raise S4RuntimeContractError(
                f"R5S4HistoryEntry.seq must be >= 1, got {self.seq!r}")
        object.__setattr__(self, "kind", _check_closed(
            self.kind, "R5S4HistoryEntry.kind", HISTORY_ENTRY_KINDS))
        object.__setattr__(self, "payload_ref", _check_str(
            self.payload_ref, "R5S4HistoryEntry.payload_ref"))
        prior = _check_str(self.prior_entry_hash,
                           "R5S4HistoryEntry.prior_entry_hash")
        if prior != GENESIS_HASH and not is_sha256_hex(prior):
            raise S4RuntimeContractError(
                f"R5S4HistoryEntry.prior_entry_hash {prior!r} must be "
                f"genesis or a sha256 hex")
        object.__setattr__(self, "prior_entry_hash", prior)
        # entry_hash = canonical sha of every leaf except entry_hash; an
        # empty supplied value is computed (builder/projection-friendly).
        expected = compute_history_entry_hash(self)
        if self.entry_hash:
            object.__setattr__(self, "entry_hash", _check_hash(
                self.entry_hash, "R5S4HistoryEntry.entry_hash"))
            if self.entry_hash != expected:
                raise S4RuntimeContractError(
                    f"R5S4HistoryEntry.entry_hash {self.entry_hash!r} does "
                    f"not match the canonical chain hash {expected!r}")
        else:
            object.__setattr__(self, "entry_hash", expected)


@dataclass(frozen=True)
class R5S4HistoryLog:
    """Append-only history log.  Errata: ``entries`` is ``min_items:0``; only
    ``no_ensemble`` may carry an empty log (``head_seq=0``,
    ``head_hash='genesis'``); single/multi remain ``min_items:1``."""

    history_ref: str
    head_seq: int
    head_hash: str
    entries: Tuple[R5S4HistoryEntry, ...]

    def __post_init__(self) -> None:
        if not matches_grammar(self.history_ref, "history"):
            raise S4RuntimeContractError(
                f"R5S4HistoryLog.history_ref {self.history_ref!r} must match "
                f"history:<ref>")
        object.__setattr__(self, "head_seq", _check_int(
            self.head_seq, "R5S4HistoryLog.head_seq"))
        entries = _freeze_obj_tuple(self.entries, "R5S4HistoryLog.entries",
                                    R5S4HistoryEntry)
        object.__setattr__(self, "entries", entries)
        if not entries:
            # Errata: empty chain requires head_seq=0 and head_hash='genesis'.
            if self.head_seq != 0 or self.head_hash != GENESIS_HASH:
                raise S4RuntimeContractError(
                    "R5S4HistoryLog empty entries requires head_seq=0 and "
                    "head_hash='genesis'")
            return
        seqs = [entry.seq for entry in entries]
        if seqs != list(range(1, len(entries) + 1)):
            raise S4RuntimeContractError(
                "R5S4HistoryLog.entries seq must be strictly 1..len(entries)")
        if entries[0].prior_entry_hash != GENESIS_HASH:
            raise S4RuntimeContractError(
                "R5S4HistoryLog first entry prior_entry_hash must be 'genesis'")
        for index in range(1, len(entries)):
            if entries[index].prior_entry_hash != entries[index - 1].entry_hash:
                raise S4RuntimeContractError(
                    "R5S4HistoryLog entries hash chain broken at seq "
                    f"{entries[index].seq}")
        if self.head_seq != len(entries):
            raise S4RuntimeContractError(
                f"R5S4HistoryLog.head_seq {self.head_seq!r} must equal "
                f"len(entries) {len(entries)}")
        if self.head_hash != entries[-1].entry_hash:
            raise S4RuntimeContractError(
                "R5S4HistoryLog.head_hash must equal the last entry's "
                "entry_hash")


@dataclass(frozen=True)
class R5S4AudienceBaselineRow:
    """One audience-plane baseline row (machine-read-only row_ref separate
    from user-facing item_anchor_zh)."""

    row_ref: str
    item_anchor_zh: str
    ordinal_zh: str
    state_zh: str
    recheck_zh: str

    def __post_init__(self) -> None:
        if not matches_grammar(self.row_ref, "baseline_row"):
            raise S4RuntimeContractError(
                f"R5S4AudienceBaselineRow.row_ref {self.row_ref!r} must "
                f"match baseline-row:<item_id>:<attempt_id>")
        object.__setattr__(self, "item_anchor_zh", _check_str(
            self.item_anchor_zh, "R5S4AudienceBaselineRow.item_anchor_zh"))
        object.__setattr__(self, "ordinal_zh", _check_str(
            self.ordinal_zh, "R5S4AudienceBaselineRow.ordinal_zh"))
        if self.ordinal_zh not in ORDINAL_ZH:
            raise S4RuntimeContractError(
                f"R5S4AudienceBaselineRow.ordinal_zh {self.ordinal_zh!r} "
                f"must be a closed ordinal label")
        object.__setattr__(self, "state_zh", _check_str(
            self.state_zh, "R5S4AudienceBaselineRow.state_zh"))
        object.__setattr__(self, "recheck_zh", _check_str(
            self.recheck_zh, "R5S4AudienceBaselineRow.recheck_zh"))


@dataclass(frozen=True)
class R5S4AudienceWorkerSummary:
    """One worker's audience summary (ordinal-sorted)."""

    ordinal_zh: str
    finding_summary_zh: Tuple[str, ...]
    verification_zh: str
    gap_zh: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordinal_zh", _check_str(
            self.ordinal_zh, "R5S4AudienceWorkerSummary.ordinal_zh"))
        if self.ordinal_zh not in ORDINAL_ZH:
            raise S4RuntimeContractError(
                f"R5S4AudienceWorkerSummary.ordinal_zh {self.ordinal_zh!r} "
                f"must be a closed ordinal label")
        object.__setattr__(self, "finding_summary_zh", _freeze_str_tuple(
            self.finding_summary_zh,
            "R5S4AudienceWorkerSummary.finding_summary_zh"))
        object.__setattr__(self, "gap_zh", _freeze_str_tuple(
            self.gap_zh, "R5S4AudienceWorkerSummary.gap_zh"))
        object.__setattr__(self, "verification_zh", _check_str(
            self.verification_zh,
            "R5S4AudienceWorkerSummary.verification_zh"))


@dataclass(frozen=True)
class R5S4AudienceInspector:
    """The plain-Chinese audience plane (exact keys; no audit leaf)."""

    audience_contract_id: str
    risk_title_zh: str
    domain_zh: str
    severity_zh: str
    change_state_zh: str
    subject_display_zh: str
    center_display_zh: str
    project_display_zh: str
    cutoff_display_zh: str
    basis_zh: str
    support_evidence_zh: Tuple[str, ...]
    counterevidence_zh: Tuple[str, ...]
    source_one_hop_zh: str
    baseline_rows_zh: Tuple[R5S4AudienceBaselineRow, ...]
    worker_ordinal_summaries: Tuple[R5S4AudienceWorkerSummary, ...]
    consensus_zh: str
    adjudication_status_zh: str
    adjudication_explanation_zh: Optional[str]
    query_basis_zh: Optional[str]
    query_finding_zh: Optional[str]
    query_action_zh: Optional[str]
    query_pd_wording_zh: Optional[str]
    history_summary_zh: str
    journey_available: bool
    journey_link_zh: Optional[str]
    journey_unavailable_reason_zh: Optional[str]

    def __post_init__(self) -> None:
        if self.audience_contract_id != AUDIENCE_CONTRACT_ID:
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.audience_contract_id must be "
                f"{AUDIENCE_CONTRACT_ID!r}")
        if self.domain_zh not in DOMAIN_ZH.values():
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.domain_zh {self.domain_zh!r} must be "
                "a closed domain label")
        if self.severity_zh not in SEVERITY_ZH_BY_SEVERITY.values():
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.severity_zh {self.severity_zh!r} "
                "must be a closed severity label")
        for name in ("risk_title_zh", "change_state_zh", "subject_display_zh",
                     "center_display_zh", "project_display_zh",
                     "cutoff_display_zh", "basis_zh", "consensus_zh",
                     "adjudication_status_zh", "history_summary_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4AudienceInspector.{name}"))
        # source_one_hop_zh is a str that MAY be empty: the one-hop summary
        # is "" when no locator is projectable (contract section 6.1:
        # 一跳摘要为空时 ``""``).  It is never null, but empty is legal.
        if not isinstance(self.source_one_hop_zh, str):
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.source_one_hop_zh must be a str, got "
                f"{type(self.source_one_hop_zh).__name__}")
        object.__setattr__(self, "source_one_hop_zh",
                           unicodedata.normalize("NFC", self.source_one_hop_zh))
        object.__setattr__(self, "support_evidence_zh", _freeze_str_tuple(
            self.support_evidence_zh,
            "R5S4AudienceInspector.support_evidence_zh"))
        object.__setattr__(self, "counterevidence_zh", _freeze_str_tuple(
            self.counterevidence_zh,
            "R5S4AudienceInspector.counterevidence_zh"))
        object.__setattr__(self, "baseline_rows_zh", _freeze_obj_tuple(
            self.baseline_rows_zh, "R5S4AudienceInspector.baseline_rows_zh",
            R5S4AudienceBaselineRow))
        object.__setattr__(self, "worker_ordinal_summaries", _freeze_obj_tuple(
            self.worker_ordinal_summaries,
            "R5S4AudienceInspector.worker_ordinal_summaries",
            R5S4AudienceWorkerSummary))
        object.__setattr__(self, "adjudication_explanation_zh",
                           _check_optional_str(
                               self.adjudication_explanation_zh,
                               "R5S4AudienceInspector.adjudication_explanation_zh"))
        for name in ("query_basis_zh", "query_finding_zh", "query_action_zh",
                     "query_pd_wording_zh"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4AudienceInspector.{name}"))
        object.__setattr__(self, "journey_available", _check_bool(
            self.journey_available, "R5S4AudienceInspector.journey_available"))
        object.__setattr__(self, "journey_link_zh", _check_optional_str(
            self.journey_link_zh, "R5S4AudienceInspector.journey_link_zh"))
        object.__setattr__(
            self, "journey_unavailable_reason_zh", _check_optional_str(
                self.journey_unavailable_reason_zh,
                "R5S4AudienceInspector.journey_unavailable_reason_zh"))


@dataclass(frozen=True)
class R5S4AuditWorkerRow:
    """One audit-plane worker row (mirror of the root worker view + raw)."""

    attempt_id: str
    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    role: str
    independent_context_hash: str
    input_content_hash: str
    output_artifact_ref: str
    declared_output_hash: str
    raw_bytes_sha256: str
    parsed_output_hash: str

    def __post_init__(self) -> None:
        for name in ("attempt_id", "binding_id", "session_id", "model_id",
                     "model_version", "output_artifact_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4AuditWorkerRow.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4AuditWorkerRow.role", ATTEMPT_ROLES))
        if self.role != "worker":
            raise S4RuntimeContractError(
                "R5S4AuditWorkerRow.role must be 'worker'")
        for name in ("independent_context_hash", "input_content_hash",
                     "declared_output_hash", "raw_bytes_sha256",
                     "parsed_output_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"R5S4AuditWorkerRow.{name}"))


@dataclass(frozen=True)
class R5S4VerificationAuditRow:
    """One audit-plane verification row (recompute trace)."""

    verification_id: str
    attempt_id: str
    checked_dimensions: Tuple[str, ...]
    result: str
    failure_reason_codes: Tuple[str, ...]
    recomputed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "verification_id", _check_str(
            self.verification_id, "R5S4VerificationAuditRow.verification_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4VerificationAuditRow.attempt_id"))
        object.__setattr__(self, "checked_dimensions", _freeze_closed_tuple(
            self.checked_dimensions,
            "R5S4VerificationAuditRow.checked_dimensions",
            VERIFICATION_DIMENSIONS))
        _require_exact_count(self.checked_dimensions, len(SEVEN_DIMENSIONS),
                             "R5S4VerificationAuditRow.checked_dimensions")
        object.__setattr__(self, "result", _check_closed(
            self.result, "R5S4VerificationAuditRow.result",
            VERIFICATION_RESULTS))
        object.__setattr__(self, "failure_reason_codes", _freeze_closed_tuple(
            self.failure_reason_codes,
            "R5S4VerificationAuditRow.failure_reason_codes",
            VERIFICATION_FAILURE_CODES))
        object.__setattr__(self, "recomputed", _check_bool(
            self.recomputed, "R5S4VerificationAuditRow.recomputed"))
        if not self.recomputed:
            raise S4RuntimeContractError(
                "R5S4VerificationAuditRow.recomputed must be True")


@dataclass(frozen=True)
class R5S4DigestContextView:
    """Audit-plane view of the R4 ``EvidenceDigestContext``."""

    input_content_hash: str
    output_digests: Mapping[str, str]
    evidence_digests: Tuple[str, ...]
    expected_ensemble_identity: str
    artifact_date_windows: Mapping[str, str]
    artifact_unit_contracts: Mapping[str, str]
    artifact_source_versions: Mapping[str, str]
    artifact_model_versions: Mapping[str, str]
    artifact_rule_ids: Mapping[str, str]
    artifact_rule_versions: Mapping[str, str]
    artifact_finding_identities: Mapping[str, Tuple[str, ...]]
    artifact_authorized_source_locators: Mapping[str, Tuple[str, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_content_hash", _check_hash(
            self.input_content_hash,
            "R5S4DigestContextView.input_content_hash"))
        object.__setattr__(self, "expected_ensemble_identity", _check_str(
            self.expected_ensemble_identity,
            "R5S4DigestContextView.expected_ensemble_identity"))
        object.__setattr__(self, "output_digests", self._check_str_sha_map(
            self.output_digests, "output_digests"))
        object.__setattr__(self, "evidence_digests", _freeze_hash_tuple(
            self.evidence_digests, "R5S4DigestContextView.evidence_digests"))
        for name in ("artifact_date_windows", "artifact_unit_contracts",
                     "artifact_source_versions", "artifact_model_versions",
                     "artifact_rule_ids", "artifact_rule_versions"):
            object.__setattr__(self, name, self._check_str_map(
                getattr(self, name), name))
        object.__setattr__(
            self, "artifact_finding_identities",
            self._check_str_strset_map(self.artifact_finding_identities,
                                       "artifact_finding_identities"))
        object.__setattr__(
            self, "artifact_authorized_source_locators",
            self._check_str_strset_map(
                self.artifact_authorized_source_locators,
                "artifact_authorized_source_locators"))

    @staticmethod
    def _check_str_map(value: Any, name: str) -> Mapping[str, str]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _check_str(val, f"R5S4DigestContextView.{name}[]")
        return result

    @classmethod
    def _check_str_sha_map(cls, value: Any, name: str) -> Mapping[str, str]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _check_hash(val, f"R5S4DigestContextView.{name}[]")
        return result

    @staticmethod
    def _check_str_strset_map(value: Any, name: str) -> Mapping[str, Tuple[str, ...]]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _freeze_str_tuple(val, f"R5S4DigestContextView.{name}[]")
        return result


@dataclass(frozen=True)
class R5S4ModelEvidenceRef:
    """Packet/audit-only D10 ModelEvidence provenance (18 bound fields; never
    on the audience plane)."""

    model_evidence_id: str
    role: str
    permitted_leaf: str
    model_id: str
    model_version: str
    evaluation_content_identity: str
    input_content_hash: str
    source_revision_content_pairs: Tuple["S4SourceRevisionPair", ...]
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
                getattr(self, name), f"R5S4ModelEvidenceRef.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4ModelEvidenceRef.role", MODEL_EVIDENCE_ROLES))
        object.__setattr__(self, "adjudication_state", _check_closed(
            self.adjudication_state, "R5S4ModelEvidenceRef.adjudication_state",
            MODEL_EVIDENCE_ADJUDICATION_STATES))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "R5S4ModelEvidenceRef.ensemble_size"))
        if self.ensemble_size < 1:
            raise S4RuntimeContractError(
                "R5S4ModelEvidenceRef.ensemble_size must be >= 1")
        for name in ("input_content_hash", "independent_context_hash",
                     "member_analysis_ref_set_hash", "output_hash",
                     "model_binding_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"R5S4ModelEvidenceRef.{name}"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "R5S4ModelEvidenceRef.source_revision_content_pairs",
                               S4SourceRevisionPair))
        object.__setattr__(self, "source_refs", _freeze_str_tuple(
            self.source_refs, "R5S4ModelEvidenceRef.source_refs"))
        object.__setattr__(self, "member_analysis_refs", _freeze_str_tuple(
            self.member_analysis_refs,
            "R5S4ModelEvidenceRef.member_analysis_refs"))


@dataclass(frozen=True)
class R5S4AuditInspector:
    """The audit plane (private; excludes packet_fingerprints from its own
    content hash)."""

    authority_receipt_ref: str
    receipt_content_hash: str
    digest_context: Optional[R5S4DigestContextView]
    worker_audit_rows: Tuple[R5S4AuditWorkerRow, ...]
    verification_audit_rows: Tuple[R5S4VerificationAuditRow, ...]
    adjudication_audit: Tuple[str, ...]
    conflict_audit: Tuple[str, ...]
    history_audit: Tuple[str, ...]
    model_evidence: Optional[R5S4ModelEvidenceRef]
    packet_fingerprints: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not matches_grammar(self.authority_receipt_ref, "receipt"):
            raise S4RuntimeContractError(
                f"R5S4AuditInspector.authority_receipt_ref "
                f"{self.authority_receipt_ref!r} must match receipt:<sha256>")
        object.__setattr__(self, "receipt_content_hash", _check_hash(
            self.receipt_content_hash,
            "R5S4AuditInspector.receipt_content_hash"))
        if self.digest_context is not None:
            _check_obj_type(self.digest_context, R5S4DigestContextView,
                            "R5S4AuditInspector.digest_context")
        object.__setattr__(self, "worker_audit_rows", _freeze_obj_tuple(
            self.worker_audit_rows, "R5S4AuditInspector.worker_audit_rows",
            R5S4AuditWorkerRow))
        object.__setattr__(self, "verification_audit_rows", _freeze_obj_tuple(
            self.verification_audit_rows,
            "R5S4AuditInspector.verification_audit_rows",
            R5S4VerificationAuditRow))
        for name in ("adjudication_audit", "conflict_audit", "history_audit"):
            object.__setattr__(self, name, _freeze_str_tuple(
                getattr(self, name), f"R5S4AuditInspector.{name}"))
        if self.model_evidence is not None:
            _check_obj_type(self.model_evidence, R5S4ModelEvidenceRef,
                            "R5S4AuditInspector.model_evidence")
        object.__setattr__(self, "packet_fingerprints", _freeze_str_tuple(
            self.packet_fingerprints, "R5S4AuditInspector.packet_fingerprints"))
        _require_min_count(self.packet_fingerprints, 4,
                           "R5S4AuditInspector.packet_fingerprints")


@dataclass(frozen=True)
class R5S4AuthorityPacket:
    """The root packet (six-node acyclic hash DAG; no root content hash)."""

    packet_id: str
    schema: str
    status: str
    authority_mode: str
    authority_anchor_ref: str
    anchor_identity_hash: str
    ensemble_projection_state: str
    ensemble_id: str
    ensemble_size: int
    input_content_hash: Optional[str]
    risk_identity: R5S4RiskIdentity
    authority_receipt: R5AuthorityReceipt
    receipt_content_hash: str
    baseline_items: Tuple[R5S4BaselineItemProjection, ...]
    baseline_rows: Tuple[R5S4BaselineRow, ...]
    worker_views: Tuple[R5S4WorkerView, ...]
    raw_artifacts: Tuple[R5S4RawOutputArtifact, ...]
    verification_rows: Tuple[R5S4VerificationRow, ...]
    conflict_rows: Tuple[R5S4ConflictRow, ...]
    adjudication_row: R5S4AdjudicationRow
    query_draft_row: Optional[R5S4QueryDraftRow]
    journey_link: R5S4JourneyLink
    history_log: R5S4HistoryLog
    audience_inspector: R5S4AudienceInspector
    audit_inspector: R5S4AuditInspector
    audience_content_hash: str
    audit_content_hash: str
    packet_integrity_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "packet_id", _check_str(
            self.packet_id, "R5S4AuthorityPacket.packet_id"))
        if not matches_grammar(self.packet_id, "packet_id"):
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.packet_id {self.packet_id!r} must match "
                f"r5-s4-contract:<audience_content_hash>")
        if self.schema != S4_PACKET_SCHEMA_ID:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.schema must be {S4_PACKET_SCHEMA_ID!r}")
        if self.status != S4_STATUS:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.status must be {S4_STATUS!r}")
        if self.authority_mode != S4_AUTHORITY_MODE:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.authority_mode must be "
                f"{S4_AUTHORITY_MODE!r}")
        if not matches_grammar(self.authority_anchor_ref, "anchor"):
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.authority_anchor_ref "
                f"{self.authority_anchor_ref!r} must match anchor:<sha256>")
        object.__setattr__(self, "anchor_identity_hash", _check_hash(
            self.anchor_identity_hash,
            "R5S4AuthorityPacket.anchor_identity_hash"))
        object.__setattr__(self, "ensemble_projection_state", _check_closed(
            self.ensemble_projection_state,
            "R5S4AuthorityPacket.ensemble_projection_state",
            ENSEMBLE_PROJECTION_STATES))
        object.__setattr__(self, "ensemble_id", _check_str(
            self.ensemble_id, "R5S4AuthorityPacket.ensemble_id"))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "R5S4AuthorityPacket.ensemble_size"))
        state = self.ensemble_projection_state
        if state == "no_ensemble":
            if self.ensemble_size != 0:
                raise S4RuntimeContractError(
                    "no_ensemble requires ensemble_size=0")
            if self.input_content_hash is not None:
                raise S4RuntimeContractError(
                    "no_ensemble forbids input_content_hash")
        else:
            if self.ensemble_size < 1:
                raise S4RuntimeContractError(
                    f"{state} requires ensemble_size >= 1")
            object.__setattr__(self, "input_content_hash", _check_hash(
                self.input_content_hash,
                "R5S4AuthorityPacket.input_content_hash"))
        _check_obj_type(self.risk_identity, R5S4RiskIdentity,
                        "R5S4AuthorityPacket.risk_identity")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4AuthorityPacket.authority_receipt")
        object.__setattr__(self, "receipt_content_hash", _check_hash(
            self.receipt_content_hash,
            "R5S4AuthorityPacket.receipt_content_hash"))
        object.__setattr__(self, "baseline_items", _freeze_obj_tuple(
            self.baseline_items, "R5S4AuthorityPacket.baseline_items",
            R5S4BaselineItemProjection))
        object.__setattr__(self, "baseline_rows", _freeze_obj_tuple(
            self.baseline_rows, "R5S4AuthorityPacket.baseline_rows",
            R5S4BaselineRow))
        object.__setattr__(self, "worker_views", _freeze_obj_tuple(
            self.worker_views, "R5S4AuthorityPacket.worker_views",
            R5S4WorkerView))
        object.__setattr__(self, "raw_artifacts", _freeze_obj_tuple(
            self.raw_artifacts, "R5S4AuthorityPacket.raw_artifacts",
            R5S4RawOutputArtifact))
        object.__setattr__(self, "verification_rows", _freeze_obj_tuple(
            self.verification_rows, "R5S4AuthorityPacket.verification_rows",
            R5S4VerificationRow))
        object.__setattr__(self, "conflict_rows", _freeze_obj_tuple(
            self.conflict_rows, "R5S4AuthorityPacket.conflict_rows",
            R5S4ConflictRow))
        _check_obj_type(self.adjudication_row, R5S4AdjudicationRow,
                        "R5S4AuthorityPacket.adjudication_row")
        if self.query_draft_row is not None:
            _check_obj_type(self.query_draft_row, R5S4QueryDraftRow,
                            "R5S4AuthorityPacket.query_draft_row")
        _check_obj_type(self.journey_link, R5S4JourneyLink,
                        "R5S4AuthorityPacket.journey_link")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4AuthorityPacket.history_log")
        _check_obj_type(self.audience_inspector, R5S4AudienceInspector,
                        "R5S4AuthorityPacket.audience_inspector")
        _check_obj_type(self.audit_inspector, R5S4AuditInspector,
                        "R5S4AuthorityPacket.audit_inspector")
        object.__setattr__(self, "audience_content_hash", _check_hash(
            self.audience_content_hash,
            "R5S4AuthorityPacket.audience_content_hash"))
        object.__setattr__(self, "audit_content_hash", _check_hash(
            self.audit_content_hash, "R5S4AuthorityPacket.audit_content_hash"))
        object.__setattr__(self, "packet_integrity_hash", _check_hash(
            self.packet_integrity_hash,
            "R5S4AuthorityPacket.packet_integrity_hash"))
        # Six-node acyclic hash DAG (each node rebuilt; none includes itself).
        if self.audience_content_hash != audience_content_hash_of(
                self.audience_inspector):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.audience_content_hash does not match "
                "canonical(audience_inspector)")
        if self.audit_content_hash != audit_content_hash_of(self.audit_inspector):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.audit_content_hash does not match "
                "canonical(audit_inspector excluding packet_fingerprints)")
        if self.receipt_content_hash != receipt_content_hash_of(
                self.authority_receipt):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.receipt_content_hash does not match "
                "canonical(authority_receipt)")
        expected_pid = compute_packet_id(self.audience_content_hash)
        if self.packet_id != expected_pid:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.packet_id {self.packet_id!r} must be "
                f"{expected_pid!r}")
        expected_fps = compute_packet_fingerprints(
            self.audience_content_hash, self.receipt_content_hash,
            self.packet_id, self.risk_identity.risk_identity_hash)
        if self.audit_inspector.packet_fingerprints != expected_fps:
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket audit packet_fingerprints do not match "
                "the frozen recipe")
        if self.packet_integrity_hash != compute_packet_integrity_hash(
                packet_as_mapping(self)):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.packet_integrity_hash does not match the "
                "canonical integrity body")


def packet_as_mapping(packet: "R5S4AuthorityPacket") -> Dict[str, Any]:
    """Canonical plain-dict projection of a packet (asdict of every field)."""
    return {field.name: _to_plain(getattr(packet, field.name))
            for field in fields(packet)}


__all__ = [name for name in globals() if not name.startswith("__")]
