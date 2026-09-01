"""Immutable typed objects for the exact R5 publication contract."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from .contracts_core import (
    APPLICABILITY_STATES, AXIS_MODES, CHANGE_CAUSES, CHANGE_KINDS,
    COVERAGE_STATES, DATE_STATES, DENOMINATOR_KINDS, DENOMINATOR_STATES,
    DOMAINS, DOMAIN_SUBTYPE_MATRIX, EVENT_FORBIDDEN_SHAPES, EVENT_SHAPES,
    JOURNEY_SUBTYPES, LEGACY_MAPPING_STATES, LEGACY_TREATMENT_KINDS,
    LINE_STYLES, MATCH_STATES, MEASURE_UNITS, NUMERATOR_KINDS,
    PENDING_ITEM_KINDS, PROJECTION_KINDS, RATE_STATES, RISK_OVERLAY_SHAPE,
    R5ContractError, SEVERITIES, SORT_DIRECTIONS, SORT_KEYS,
    SYMPTOM_EFFICACY_SUBTYPES, VISIT_KINDS, WORKSPACE_VIEWS,
    _check_bool, _check_closed, _check_date_geometry, _check_decimal,
    _check_denominator_rate, _check_hash, _check_int, _check_no_duplicates,
    _check_nonneg_int, _check_optional_date, _check_optional_decimal,
    _check_optional_str, _check_str, _check_window_order,
    _freeze_closed_tuple, _freeze_hash_tuple, _freeze_obj_tuple,
    _freeze_str_tuple, _require_disjoint, _verify_content_hash,
    severity_to_zh,
)

# ---------------------------------------------------------------------------
# Typed objects (exact keys/cardinality/nullability from exact_contract.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceRevisionContentPair:
    """One source revision -> content hash binding (R4 authority value)."""

    revision_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id",
                           _check_str(self.revision_id,
                                      "SourceRevisionContentPair.revision_id"))
        # Opaque R4-derived hash: shape-checked, never recomputed locally.
        object.__setattr__(self, "content_hash",
                           _check_hash(self.content_hash,
                                       "SourceRevisionContentPair.content_hash"))


@dataclass(frozen=True)
class R5AEMHMatchHistory:
    """Append-only AE/MH later-recorded matching history (deferred leaf)."""

    candidate_ref: str
    from_snapshot_ref: str
    history_content_hash: str
    identity_evidence_refs: Tuple[str, ...]
    later_fact_ref: Optional[str]
    match_state: str
    to_snapshot_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_ref", _check_str(
            self.candidate_ref, "R5AEMHMatchHistory.candidate_ref"))
        object.__setattr__(self, "from_snapshot_ref", _check_str(
            self.from_snapshot_ref, "R5AEMHMatchHistory.from_snapshot_ref"))
        object.__setattr__(self, "to_snapshot_ref", _check_str(
            self.to_snapshot_ref, "R5AEMHMatchHistory.to_snapshot_ref"))
        object.__setattr__(self, "later_fact_ref", _check_optional_str(
            self.later_fact_ref, "R5AEMHMatchHistory.later_fact_ref"))
        object.__setattr__(self, "match_state", _check_closed(
            self.match_state, "R5AEMHMatchHistory.match_state", MATCH_STATES))
        object.__setattr__(self, "identity_evidence_refs", _freeze_str_tuple(
            self.identity_evidence_refs,
            "R5AEMHMatchHistory.identity_evidence_refs"))
        _verify_content_hash(self, "history_content_hash")


@dataclass(frozen=True)
class R5AudienceEncodingRegistry:
    """Frozen audience encoding: domain shapes/labels, severity lexicon,
    legacy-treatment mapping and the risk overlay shape."""

    domain_items: Tuple["R5DomainEncodingItem", ...]
    legacy_treatment_mapping: Tuple["R5LegacyTreatmentMappingItem", ...]
    risk_overlay_shape: str
    severity_items: Tuple["R5SeverityLexiconItem", ...]
    symptom_efficacy_subtypes: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_items", _freeze_obj_tuple(
            self.domain_items, "R5AudienceEncodingRegistry.domain_items",
            R5DomainEncodingItem))
        object.__setattr__(self, "legacy_treatment_mapping", _freeze_obj_tuple(
            self.legacy_treatment_mapping,
            "R5AudienceEncodingRegistry.legacy_treatment_mapping",
            R5LegacyTreatmentMappingItem))
        if self.risk_overlay_shape != RISK_OVERLAY_SHAPE:
            raise R5ContractError(
                "R5AudienceEncodingRegistry.risk_overlay_shape must be "
                f"{RISK_OVERLAY_SHAPE!r}, got {self.risk_overlay_shape!r}")
        object.__setattr__(self, "severity_items", _freeze_obj_tuple(
            self.severity_items,
            "R5AudienceEncodingRegistry.severity_items",
            R5SeverityLexiconItem))
        object.__setattr__(self, "symptom_efficacy_subtypes",
                           _freeze_closed_tuple(
                               self.symptom_efficacy_subtypes,
                               "R5AudienceEncodingRegistry."
                               "symptom_efficacy_subtypes",
                               SYMPTOM_EFFICACY_SUBTYPES))
        # Invariants ``severity_lexicon_bijection`` and ``risk_overlay_unique``.
        severities_seen: Dict[str, str] = {}
        for item in self.severity_items:
            expected_zh = severity_to_zh(item.severity)
            if item.label_zh != expected_zh:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.severity_items label "
                    f"{item.label_zh!r} for severity {item.severity!r} must "
                    f"be {expected_zh!r}")
            if item.severity in severities_seen:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.severity_items must contain "
                    f"severity {item.severity!r} exactly once")
            severities_seen[item.severity] = item.label_zh
        if set(severities_seen) != set(SEVERITIES):
            raise R5ContractError(
                "R5AudienceEncodingRegistry.severity_items must cover "
                f"exactly {SEVERITIES!r}, got {sorted(severities_seen)!r}")
        domains_seen: Dict[str, R5DomainEncodingItem] = {}
        for item in self.domain_items:
            if item.domain in domains_seen:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry.domain_items must contain "
                    f"domain {item.domain!r} exactly once")
            domains_seen[item.domain] = item
            if item.event_shape in EVENT_FORBIDDEN_SHAPES:
                raise R5ContractError(
                    "R5AudienceEncodingRegistry risk overlay shape "
                    f"{item.event_shape!r} is forbidden on events "
                    "(risk_overlay_unique)")
        if set(domains_seen) != set(DOMAINS):
            raise R5ContractError(
                "R5AudienceEncodingRegistry.domain_items must cover exactly "
                f"{DOMAINS!r}, got {sorted(domains_seen)!r}")
        symptom_encoding = domains_seen["symptom_efficacy"]
        if (symptom_encoding.event_shape, symptom_encoding.line_style) != (
                "circle", "trend"):
            raise R5ContractError(
                "symptom_efficacy encoding must be circle + trend")


@dataclass(frozen=True)
class R5AudienceLexicon:
    """Frozen audience lexicon: allowed/forbidden terms and their fixed
    audience labels."""

    content_hash: str
    forbidden_terms: Tuple[str, ...]
    items: Tuple["R5LexiconItem", ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "forbidden_terms", _freeze_str_tuple(
            self.forbidden_terms, "R5AudienceLexicon.forbidden_terms"))
        object.__setattr__(self, "items", _freeze_obj_tuple(
            self.items, "R5AudienceLexicon.items", R5LexiconItem))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5AuthorityReceipt:
    """Per-leaf authority receipt: every binding identity, evaluation
    content identity, visibility decision and source revision-content pair
    of one public projection.  Hash fields are R4-authoritative values
    (shape-checked here, verified against R4 by the W2 adapter)."""

    audience_contract_id: str
    cutoff_ref: Optional[str]
    evaluation_content_identities: Tuple[str, ...]
    project_ref: str
    public_projection_content_hash: str
    public_projection_id: str
    public_projection_kind: str
    run_ref: str
    snapshot_ref: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    visibility_decision_hash: str
    visibility_decision_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "audience_contract_id", _check_str(
            self.audience_contract_id,
            "R5AuthorityReceipt.audience_contract_id"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "R5AuthorityReceipt.cutoff_ref"))
        object.__setattr__(self, "project_ref", _check_str(
            self.project_ref, "R5AuthorityReceipt.project_ref"))
        object.__setattr__(self, "run_ref", _check_str(
            self.run_ref, "R5AuthorityReceipt.run_ref"))
        object.__setattr__(self, "snapshot_ref", _check_str(
            self.snapshot_ref, "R5AuthorityReceipt.snapshot_ref"))
        object.__setattr__(self, "public_projection_id", _check_str(
            self.public_projection_id,
            "R5AuthorityReceipt.public_projection_id"))
        object.__setattr__(self, "public_projection_kind", _check_closed(
            self.public_projection_kind,
            "R5AuthorityReceipt.public_projection_kind", PROJECTION_KINDS))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5AuthorityReceipt.visibility_decision_id"))
        object.__setattr__(self, "public_projection_content_hash",
                           _check_hash(
                               self.public_projection_content_hash,
                               "R5AuthorityReceipt."
                               "public_projection_content_hash"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5AuthorityReceipt.visibility_decision_hash"))
        object.__setattr__(self, "evaluation_content_identities",
                           _freeze_hash_tuple(
                               self.evaluation_content_identities,
                               "R5AuthorityReceipt."
                               "evaluation_content_identities"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "R5AuthorityReceipt."
                               "source_revision_content_pairs",
                               SourceRevisionContentPair))


@dataclass(frozen=True)
class R5CenterMapCell:
    """One center x domain cell of the center risk map."""

    domain: str
    individual_risk_refs: Tuple[str, ...]
    measure_refs: Tuple[str, ...]
    pattern_refs: Tuple[str, ...]
    severity: str
    site_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5CenterMapCell.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5CenterMapCell.severity", SEVERITIES))
        object.__setattr__(self, "site_ref", _check_str(
            self.site_ref, "R5CenterMapCell.site_ref"))
        object.__setattr__(self, "individual_risk_refs", _freeze_str_tuple(
            self.individual_risk_refs,
            "R5CenterMapCell.individual_risk_refs"))
        object.__setattr__(self, "measure_refs", _freeze_str_tuple(
            self.measure_refs, "R5CenterMapCell.measure_refs"))
        object.__setattr__(self, "pattern_refs", _freeze_str_tuple(
            self.pattern_refs, "R5CenterMapCell.pattern_refs"))


@dataclass(frozen=True)
class R5CenterMapProjection:
    """Center risk map projection: cells, replay instance and the stable
    (non-punitive) site ordering."""

    cells: Tuple[R5CenterMapCell, ...]
    content_hash: str
    projection_instance: "R5ProjectionInstance"
    stable_site_order: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", _freeze_obj_tuple(
            self.cells, "R5CenterMapProjection.cells", R5CenterMapCell))
        if not isinstance(self.projection_instance, R5ProjectionInstance):
            raise R5ContractError(
                "R5CenterMapProjection.projection_instance must be an "
                f"R5ProjectionInstance, got {type(self.projection_instance).__name__}")
        if not isinstance(self.stable_site_order, (list, tuple)):
            raise R5ContractError(
                "R5CenterMapProjection.stable_site_order must be a "
                f"list/tuple, got {type(self.stable_site_order).__name__}")
        # Stable ordering is ORDER-SIGNIFICANT: preserved verbatim, unique.
        object.__setattr__(self, "stable_site_order", tuple(
            _check_str(site, "R5CenterMapProjection.stable_site_order[]")
            for site in self.stable_site_order))
        _check_no_duplicates(
            self.stable_site_order,
            "R5CenterMapProjection.stable_site_order")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5ChangeBand:
    """One risk's change band: closed kind plus the cause plane."""

    authority_receipt_ref: str
    change_cause: Optional[str]
    change_kind: str
    current_snapshot_ref: str
    prior_snapshot_ref: Optional[str]
    risk_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5ChangeBand.authority_receipt_ref"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5ChangeBand.risk_ref"))
        object.__setattr__(self, "current_snapshot_ref", _check_str(
            self.current_snapshot_ref,
            "R5ChangeBand.current_snapshot_ref"))
        object.__setattr__(self, "prior_snapshot_ref", _check_optional_str(
            self.prior_snapshot_ref, "R5ChangeBand.prior_snapshot_ref"))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "R5ChangeBand.change_kind", CHANGE_KINDS))
        if self.change_cause is not None:
            object.__setattr__(self, "change_cause", _check_closed(
                self.change_cause, "R5ChangeBand.change_cause", CHANGE_CAUSES))


@dataclass(frozen=True)
class R5CurrentRiskSet:
    """Current high/medium full set, low-risk cluster and resolved history
    refs.  Planes are mutually exclusive (invariant
    ``unique_reference_sets``)."""

    authority_receipt_ref: str
    high_risk_refs: Tuple[str, ...]
    low_risk_cluster_refs: Tuple[str, ...]
    medium_risk_refs: Tuple[str, ...]
    resolved_history_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5CurrentRiskSet.authority_receipt_ref"))
        object.__setattr__(self, "high_risk_refs", _freeze_str_tuple(
            self.high_risk_refs, "R5CurrentRiskSet.high_risk_refs"))
        object.__setattr__(self, "medium_risk_refs", _freeze_str_tuple(
            self.medium_risk_refs, "R5CurrentRiskSet.medium_risk_refs"))
        object.__setattr__(self, "low_risk_cluster_refs", _freeze_str_tuple(
            self.low_risk_cluster_refs,
            "R5CurrentRiskSet.low_risk_cluster_refs"))
        object.__setattr__(self, "resolved_history_refs", _freeze_str_tuple(
            self.resolved_history_refs,
            "R5CurrentRiskSet.resolved_history_refs"))
        _require_disjoint("R5CurrentRiskSet", (
            ("high_risk", self.high_risk_refs),
            ("medium_risk", self.medium_risk_refs),
            ("low_risk_cluster", self.low_risk_cluster_refs),
            ("resolved_history", self.resolved_history_refs),
        ))


@dataclass(frozen=True)
class R5DeepLinkState:
    """Canonical deep-link state: authoritative identities plus the
    canonical view/axis/window."""

    axis_mode: str
    cutoff_ref: str
    event_ref: Optional[str]
    project_ref: str
    return_context_key: str
    risk_anchor_ref: str
    risk_ref: str
    run_ref: str
    site_ref: Optional[str]
    snapshot_ref: str
    source_locator_ref: Optional[str]
    spine_ref: str
    subject_ref: str
    view: str
    visit_ref: Optional[str]
    window_end: Optional[date]
    window_start: Optional[date]

    def __post_init__(self) -> None:
        object.__setattr__(self, "axis_mode", _check_closed(
            self.axis_mode, "R5DeepLinkState.axis_mode", AXIS_MODES))
        object.__setattr__(self, "view", _check_closed(
            self.view, "R5DeepLinkState.view", WORKSPACE_VIEWS))
        for name in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                     "return_context_key", "risk_anchor_ref", "risk_ref",
                     "spine_ref", "subject_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5DeepLinkState.{name}"))
        for name in ("event_ref", "site_ref", "source_locator_ref",
                     "visit_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5DeepLinkState.{name}"))
        object.__setattr__(self, "window_start", _check_optional_date(
            self.window_start, "R5DeepLinkState.window_start"))
        object.__setattr__(self, "window_end", _check_optional_date(
            self.window_end, "R5DeepLinkState.window_end"))
        _check_window_order(self.window_start, self.window_end,
                            "R5DeepLinkState")


@dataclass(frozen=True)
class R5DomainEncodingItem:
    """One domain's audience encoding: event shape, line style and the
    fixed Chinese short label (stage contract v0.3 §8)."""

    domain: str
    event_shape: str
    line_style: str
    short_label_zh: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5DomainEncodingItem.domain", DOMAINS))
        object.__setattr__(self, "event_shape", _check_closed(
            self.event_shape, "R5DomainEncodingItem.event_shape",
            EVENT_SHAPES))
        object.__setattr__(self, "line_style", _check_closed(
            self.line_style, "R5DomainEncodingItem.line_style", LINE_STYLES))
        object.__setattr__(self, "short_label_zh", _check_str(
            self.short_label_zh, "R5DomainEncodingItem.short_label_zh"))
        if self.event_shape in EVENT_FORBIDDEN_SHAPES:
            raise R5ContractError(
                "R5DomainEncodingItem.event_shape "
                f"{self.event_shape!r} is forbidden on events "
                "(risk_overlay_unique)")


@dataclass(frozen=True)
class R5FilterState:
    """Ephemeral filter state of one view."""

    change_kind: Tuple[str, ...]
    domain: Tuple[str, ...]
    include_low: bool
    severity: Tuple[str, ...]
    site_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "change_kind", _freeze_closed_tuple(
            self.change_kind, "R5FilterState.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "domain", _freeze_closed_tuple(
            self.domain, "R5FilterState.domain", DOMAINS))
        object.__setattr__(self, "severity", _freeze_closed_tuple(
            self.severity, "R5FilterState.severity", SEVERITIES))
        object.__setattr__(self, "site_refs", _freeze_str_tuple(
            self.site_refs, "R5FilterState.site_refs"))
        object.__setattr__(self, "include_low", _check_bool(
            self.include_low, "R5FilterState.include_low"))


@dataclass(frozen=True)
class R5JourneyEvent:
    """One journey event on its owning domain track (deferred leaf)."""

    date_state: str
    domain: str
    end: Optional[date]
    event_ref: str
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    start: Optional[date]
    subtype: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5JourneyEvent.domain", DOMAINS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5JourneyEvent.date_state", DATE_STATES))
        object.__setattr__(self, "subtype", _check_closed(
            self.subtype, "R5JourneyEvent.subtype", JOURNEY_SUBTYPES))
        if self.subtype not in DOMAIN_SUBTYPE_MATRIX[self.domain]:
            raise R5ContractError(
                "R5JourneyEvent.domain_subtype_matrix violation: subtype "
                f"{self.subtype!r} does not belong to domain "
                f"{self.domain!r}")
        object.__setattr__(self, "event_ref", _check_str(
            self.event_ref, "R5JourneyEvent.event_ref"))
        object.__setattr__(self, "risk_anchor_refs", _freeze_str_tuple(
            self.risk_anchor_refs, "R5JourneyEvent.risk_anchor_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5JourneyEvent.source_locator_refs"))
        object.__setattr__(self, "start", _check_optional_date(
            self.start, "R5JourneyEvent.start"))
        object.__setattr__(self, "end", _check_optional_date(
            self.end, "R5JourneyEvent.end"))
        _check_date_geometry(self.date_state, self.start, self.end,
                             "R5JourneyEvent")
        _check_window_order(self.start, self.end, "R5JourneyEvent")


@dataclass(frozen=True)
class R5JourneyTrack:
    """One domain track of the subject journey (deferred leaf)."""

    applicability_state: str
    content_hash: str
    domain: str
    event_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "applicability_state", _check_closed(
            self.applicability_state, "R5JourneyTrack.applicability_state",
            APPLICABILITY_STATES))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5JourneyTrack.domain", DOMAINS))
        object.__setattr__(self, "event_refs", _freeze_str_tuple(
            self.event_refs, "R5JourneyTrack.event_refs"))
        object.__setattr__(self, "risk_anchor_refs", _freeze_str_tuple(
            self.risk_anchor_refs, "R5JourneyTrack.risk_anchor_refs"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5LegacyTreatmentMappingItem:
    """Frozen legacy treatment domain mapping item.  Without a frozen
    project mapping the item stays ``unmapped_fail_closed`` with all
    targets null (invariant ``legacy_treatment_fail_closed``)."""

    legacy_kind: str
    mapping_authority_ref: Optional[str]
    mapping_state: str
    target_domain: Optional[str]
    target_subtype: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "legacy_kind", _check_closed(
            self.legacy_kind, "R5LegacyTreatmentMappingItem.legacy_kind",
            LEGACY_TREATMENT_KINDS))
        object.__setattr__(self, "mapping_state", _check_closed(
            self.mapping_state, "R5LegacyTreatmentMappingItem.mapping_state",
            LEGACY_MAPPING_STATES))
        object.__setattr__(self, "mapping_authority_ref", _check_optional_str(
            self.mapping_authority_ref,
            "R5LegacyTreatmentMappingItem.mapping_authority_ref"))
        if self.target_domain is not None:
            object.__setattr__(self, "target_domain", _check_closed(
                self.target_domain,
                "R5LegacyTreatmentMappingItem.target_domain", DOMAINS))
        if self.target_subtype is not None:
            object.__setattr__(self, "target_subtype", _check_closed(
                self.target_subtype,
                "R5LegacyTreatmentMappingItem.target_subtype",
                JOURNEY_SUBTYPES))
        if self.mapping_state == "mapped":
            if (self.mapping_authority_ref is None
                    or self.target_domain is None
                    or self.target_subtype is None):
                raise R5ContractError(
                    "R5LegacyTreatmentMappingItem mapped requires "
                    "mapping_authority_ref, target_domain and "
                    "target_subtype")
        else:  # unmapped_fail_closed
            if (self.mapping_authority_ref is not None
                    or self.target_domain is not None
                    or self.target_subtype is not None):
                raise R5ContractError(
                    "R5LegacyTreatmentMappingItem unmapped_fail_closed "
                    "requires all targets null (enters domain-confirmation "
                    "surface)")


@dataclass(frozen=True)
class R5LexiconItem:
    """One lexicon token with its audience label and allow flag."""

    audience_allowed: bool
    label_zh: str
    token: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "token", _check_str(
            self.token, "R5LexiconItem.token"))
        object.__setattr__(self, "label_zh", _check_str(
            self.label_zh, "R5LexiconItem.label_zh"))
        object.__setattr__(self, "audience_allowed", _check_bool(
            self.audience_allowed, "R5LexiconItem.audience_allowed"))


@dataclass(frozen=True)
class R5PageState:
    """Ephemeral pagination state."""

    page_index: int
    page_size: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "page_index", _check_nonneg_int(
            self.page_index, "R5PageState.page_index"))
        object.__setattr__(self, "page_size", _check_int(
            self.page_size, "R5PageState.page_size"))
        if self.page_size < 1:
            raise R5ContractError(
                f"R5PageState.page_size must be >= 1, got {self.page_size!r}")


@dataclass(frozen=True)
class R5PendingDateItem:
    """One item parked in the date-confirmation area: its date is never
    exact and never fabricated on the main axis (deferred leaf)."""

    candidate_date_refs: Tuple[str, ...]
    date_state: str
    domain: str
    item_kind: str
    item_ref: str
    source_locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_kind", _check_closed(
            self.item_kind, "R5PendingDateItem.item_kind",
            PENDING_ITEM_KINDS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5PendingDateItem.date_state", DATE_STATES))
        if self.date_state == "exact":
            raise R5ContractError(
                "R5PendingDateItem.date_state must not be exact: a pending "
                "item never carries a precise main-axis date "
                "(date_geometry_consistency)")
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5PendingDateItem.domain", DOMAINS))
        object.__setattr__(self, "item_ref", _check_str(
            self.item_ref, "R5PendingDateItem.item_ref"))
        object.__setattr__(self, "candidate_date_refs", _freeze_str_tuple(
            self.candidate_date_refs,
            "R5PendingDateItem.candidate_date_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "R5PendingDateItem.source_locator_refs"))


@dataclass(frozen=True)
class R5ProjectCockpitProjection:
    """Project risk cockpit projection: current risk set, change bands,
    measures and center map bound to one replay instance."""

    center_map_ref: str
    change_band_refs: Tuple[str, ...]
    content_hash: str
    current_risk_set_ref: str
    measure_refs: Tuple[str, ...]
    projection_instance: R5ProjectionInstance
    selected_risk_ref: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "center_map_ref", _check_str(
            self.center_map_ref, "R5ProjectCockpitProjection.center_map_ref"))
        object.__setattr__(self, "current_risk_set_ref", _check_str(
            self.current_risk_set_ref,
            "R5ProjectCockpitProjection.current_risk_set_ref"))
        object.__setattr__(self, "selected_risk_ref", _check_optional_str(
            self.selected_risk_ref,
            "R5ProjectCockpitProjection.selected_risk_ref"))
        object.__setattr__(self, "change_band_refs", _freeze_str_tuple(
            self.change_band_refs,
            "R5ProjectCockpitProjection.change_band_refs"))
        object.__setattr__(self, "measure_refs", _freeze_str_tuple(
            self.measure_refs, "R5ProjectCockpitProjection.measure_refs"))
        if not isinstance(self.projection_instance, R5ProjectionInstance):
            raise R5ContractError(
                "R5ProjectCockpitProjection.projection_instance must be an "
                "R5ProjectionInstance, got "
                f"{type(self.projection_instance).__name__}")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5ProjectionInstance:
    """Separate opaque run/snapshot audit identity and replay-stable
    content identity.  ``content_hash`` covers the non-hash fields
    (invariant ``canonical_content_hash``); ``replay_content_identity`` is
    an R4-derived opaque value (shape-checked, not recomputed)."""

    authority_receipt_ref: str
    content_hash: str
    opaque_run_ref: str
    opaque_snapshot_ref: str
    replay_content_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5ProjectionInstance.authority_receipt_ref"))
        object.__setattr__(self, "opaque_run_ref", _check_str(
            self.opaque_run_ref, "R5ProjectionInstance.opaque_run_ref"))
        object.__setattr__(self, "opaque_snapshot_ref", _check_str(
            self.opaque_snapshot_ref,
            "R5ProjectionInstance.opaque_snapshot_ref"))
        object.__setattr__(self, "replay_content_identity", _check_hash(
            self.replay_content_identity,
            "R5ProjectionInstance.replay_content_identity"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5QuantitativeMeasure:
    """One quantitative measure projected verbatim from R4 authority:
    numerator/denominator member refs, value, unit, rate state, coverage,
    cutoff and evaluation limits.  R5 never recomputes (deferred leaf)."""

    authoritative_value_ref: str
    authority_receipt_ref: str
    coverage_state: str
    cutoff_ref: str
    denominator_exclusion_refs: Tuple[str, ...]
    denominator_kind: str
    denominator_member_refs: Tuple[str, ...]
    denominator_state: str
    denominator_value: Optional[Decimal]
    evaluation_limit_refs: Tuple[str, ...]
    numerator_kind: str
    numerator_member_refs: Tuple[str, ...]
    numerator_value: Decimal
    rate_state: str
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authoritative_value_ref", _check_str(
            self.authoritative_value_ref,
            "R5QuantitativeMeasure.authoritative_value_ref"))
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5QuantitativeMeasure.authority_receipt_ref"))
        object.__setattr__(self, "cutoff_ref", _check_str(
            self.cutoff_ref, "R5QuantitativeMeasure.cutoff_ref"))
        object.__setattr__(self, "coverage_state", _check_closed(
            self.coverage_state, "R5QuantitativeMeasure.coverage_state",
            COVERAGE_STATES))
        object.__setattr__(self, "denominator_kind", _check_closed(
            self.denominator_kind,
            "R5QuantitativeMeasure.denominator_kind", DENOMINATOR_KINDS))
        object.__setattr__(self, "denominator_state", _check_closed(
            self.denominator_state,
            "R5QuantitativeMeasure.denominator_state", DENOMINATOR_STATES))
        object.__setattr__(self, "numerator_kind", _check_closed(
            self.numerator_kind, "R5QuantitativeMeasure.numerator_kind",
            NUMERATOR_KINDS))
        object.__setattr__(self, "rate_state", _check_closed(
            self.rate_state, "R5QuantitativeMeasure.rate_state", RATE_STATES))
        object.__setattr__(self, "unit", _check_closed(
            self.unit, "R5QuantitativeMeasure.unit", MEASURE_UNITS))
        object.__setattr__(self, "numerator_value", _check_decimal(
            self.numerator_value, "R5QuantitativeMeasure.numerator_value"))
        object.__setattr__(self, "denominator_value", _check_optional_decimal(
            self.denominator_value,
            "R5QuantitativeMeasure.denominator_value"))
        object.__setattr__(self, "numerator_member_refs", _freeze_str_tuple(
            self.numerator_member_refs,
            "R5QuantitativeMeasure.numerator_member_refs"))
        object.__setattr__(self, "denominator_member_refs", _freeze_str_tuple(
            self.denominator_member_refs,
            "R5QuantitativeMeasure.denominator_member_refs"))
        object.__setattr__(self, "denominator_exclusion_refs",
                           _freeze_str_tuple(
                               self.denominator_exclusion_refs,
                               "R5QuantitativeMeasure."
                               "denominator_exclusion_refs"))
        object.__setattr__(self, "evaluation_limit_refs", _freeze_str_tuple(
            self.evaluation_limit_refs,
            "R5QuantitativeMeasure.evaluation_limit_refs"))
        _check_denominator_rate(self)


@dataclass(frozen=True)
class R5ReturnContext:
    """Return context: canonical URL state plus ephemeral client state.
    ``canonical_state_hash`` covers the non-hash fields (invariant
    ``canonical_content_hash``)."""

    canonical_state_hash: str
    deep_link_state: R5DeepLinkState
    filter_state: R5FilterState
    inspector_width: int
    page_state: R5PageState
    scroll_state: "R5ScrollState"
    sort_state: "R5SortState"
    temporary_expansion_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name, cls in (
                ("deep_link_state", R5DeepLinkState),
                ("filter_state", R5FilterState),
                ("page_state", R5PageState),
                ("scroll_state", R5ScrollState),
                ("sort_state", R5SortState)):
            value = getattr(self, name)
            if not isinstance(value, cls):
                raise R5ContractError(
                    f"R5ReturnContext.{name} must be a {cls.__name__}, got "
                    f"{type(value).__name__}")
        object.__setattr__(self, "inspector_width", _check_nonneg_int(
            self.inspector_width, "R5ReturnContext.inspector_width"))
        object.__setattr__(self, "temporary_expansion_refs",
                           _freeze_str_tuple(
                               self.temporary_expansion_refs,
                               "R5ReturnContext.temporary_expansion_refs"))
        _verify_content_hash(self, "canonical_state_hash")


@dataclass(frozen=True)
class R5RiskAnchor:
    """One risk anchor on the temporal spine (deferred leaf)."""

    date_state: str
    domain: str
    event_ref: Optional[str]
    risk_ref: str
    risk_type_zh: str
    severity: str
    visit_ref: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5RiskAnchor.date_state", DATE_STATES))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5RiskAnchor.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5RiskAnchor.severity", SEVERITIES))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5RiskAnchor.risk_ref"))
        object.__setattr__(self, "risk_type_zh", _check_str(
            self.risk_type_zh, "R5RiskAnchor.risk_type_zh"))
        object.__setattr__(self, "event_ref", _check_optional_str(
            self.event_ref, "R5RiskAnchor.event_ref"))
        object.__setattr__(self, "visit_ref", _check_optional_str(
            self.visit_ref, "R5RiskAnchor.visit_ref"))


@dataclass(frozen=True)
class R5RiskInspectorProjection:
    """Risk Inspector evidence binding: baseline, attempts, verification,
    conflict, adjudication and source refs.  Support and counterevidence
    are exclusive planes (invariant ``unique_reference_sets``)."""

    adjudication_ref: Optional[str]
    analysis_attempt_refs: Tuple[str, ...]
    authority_receipt_ref: str
    baseline_assessment_refs: Tuple[str, ...]
    baseline_item_refs: Tuple[str, ...]
    conflict_refs: Tuple[str, ...]
    counterevidence_refs: Tuple[str, ...]
    domain: str
    query_draft_ref: Optional[str]
    risk_ref: str
    severity: str
    source_locator_refs: Tuple[str, ...]
    support_evidence_refs: Tuple[str, ...]
    verification_refs: Tuple[str, ...]
    worker_output_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5RiskInspectorProjection.domain", DOMAINS))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5RiskInspectorProjection.severity", SEVERITIES))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5RiskInspectorProjection.risk_ref"))
        object.__setattr__(self, "authority_receipt_ref", _check_str(
            self.authority_receipt_ref,
            "R5RiskInspectorProjection.authority_receipt_ref"))
        object.__setattr__(self, "adjudication_ref", _check_optional_str(
            self.adjudication_ref,
            "R5RiskInspectorProjection.adjudication_ref"))
        object.__setattr__(self, "query_draft_ref", _check_optional_str(
            self.query_draft_ref,
            "R5RiskInspectorProjection.query_draft_ref"))
        object.__setattr__(self, "analysis_attempt_refs", _freeze_str_tuple(
            self.analysis_attempt_refs,
            "R5RiskInspectorProjection.analysis_attempt_refs"))
        object.__setattr__(self, "baseline_assessment_refs",
                           _freeze_str_tuple(
                               self.baseline_assessment_refs,
                               "R5RiskInspectorProjection."
                               "baseline_assessment_refs"))
        object.__setattr__(self, "baseline_item_refs", _freeze_str_tuple(
            self.baseline_item_refs,
            "R5RiskInspectorProjection.baseline_item_refs"))
        object.__setattr__(self, "conflict_refs", _freeze_str_tuple(
            self.conflict_refs, "R5RiskInspectorProjection.conflict_refs"))
        object.__setattr__(self, "counterevidence_refs", _freeze_str_tuple(
            self.counterevidence_refs,
            "R5RiskInspectorProjection.counterevidence_refs"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "R5RiskInspectorProjection.source_locator_refs"))
        object.__setattr__(self, "support_evidence_refs", _freeze_str_tuple(
            self.support_evidence_refs,
            "R5RiskInspectorProjection.support_evidence_refs"))
        object.__setattr__(self, "verification_refs", _freeze_str_tuple(
            self.verification_refs,
            "R5RiskInspectorProjection.verification_refs"))
        object.__setattr__(self, "worker_output_refs", _freeze_str_tuple(
            self.worker_output_refs,
            "R5RiskInspectorProjection.worker_output_refs"))
        overlap = set(self.support_evidence_refs) & set(
            self.counterevidence_refs)
        if overlap:
            raise R5ContractError(
                "R5RiskInspectorProjection support/counterevidence planes "
                f"overlap: {sorted(overlap)!r}")


@dataclass(frozen=True)
class R5ScrollState:
    """Ephemeral scroll offsets of the three surfaces."""

    center_map_y: int
    project_list_y: int
    workspace_y: int

    def __post_init__(self) -> None:
        for name in ("center_map_y", "project_list_y", "workspace_y"):
            object.__setattr__(self, name, _check_nonneg_int(
                getattr(self, name), f"R5ScrollState.{name}"))


@dataclass(frozen=True)
class R5SeverityLexiconItem:
    """One severity's fixed audience label and line weight."""

    label_zh: str
    line_weight: int
    severity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5SeverityLexiconItem.severity", SEVERITIES))
        object.__setattr__(self, "label_zh", _check_str(
            self.label_zh, "R5SeverityLexiconItem.label_zh"))
        object.__setattr__(self, "line_weight", _check_nonneg_int(
            self.line_weight, "R5SeverityLexiconItem.line_weight"))


@dataclass(frozen=True)
class R5SortState:
    """Ephemeral sort state of one view."""

    direction: str
    key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _check_closed(
            self.key, "R5SortState.key", SORT_KEYS))
        object.__setattr__(self, "direction", _check_closed(
            self.direction, "R5SortState.direction", SORT_DIRECTIONS))


@dataclass(frozen=True)
class R5SubjectWorkspaceState:
    """Subject Workspace shared state: one temporal spine, one window and
    one selection across the three views."""

    active_view: str
    axis_mode: str
    content_hash: str
    selected_event_ref: Optional[str]
    selected_risk_ref: Optional[str]
    selected_visit_ref: Optional[str]
    spine_ref: str
    subject_ref: str
    window_end: Optional[date]
    window_start: Optional[date]

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_view", _check_closed(
            self.active_view, "R5SubjectWorkspaceState.active_view",
            WORKSPACE_VIEWS))
        object.__setattr__(self, "axis_mode", _check_closed(
            self.axis_mode, "R5SubjectWorkspaceState.axis_mode", AXIS_MODES))
        object.__setattr__(self, "subject_ref", _check_str(
            self.subject_ref, "R5SubjectWorkspaceState.subject_ref"))
        object.__setattr__(self, "spine_ref", _check_str(
            self.spine_ref, "R5SubjectWorkspaceState.spine_ref"))
        object.__setattr__(self, "selected_event_ref", _check_optional_str(
            self.selected_event_ref,
            "R5SubjectWorkspaceState.selected_event_ref"))
        object.__setattr__(self, "selected_risk_ref", _check_optional_str(
            self.selected_risk_ref,
            "R5SubjectWorkspaceState.selected_risk_ref"))
        object.__setattr__(self, "selected_visit_ref", _check_optional_str(
            self.selected_visit_ref,
            "R5SubjectWorkspaceState.selected_visit_ref"))
        object.__setattr__(self, "window_start", _check_optional_date(
            self.window_start, "R5SubjectWorkspaceState.window_start"))
        object.__setattr__(self, "window_end", _check_optional_date(
            self.window_end, "R5SubjectWorkspaceState.window_end"))
        _check_window_order(self.window_start, self.window_end,
                            "R5SubjectWorkspaceState")
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5TemporalSpineProjection:
    """Temporal spine: visits, events and pending-date refs on one shared
    spine (deferred leaf)."""

    content_hash: str
    cutoff_ref: str
    event_refs: Tuple[str, ...]
    pending_date_refs: Tuple[str, ...]
    phase_band_refs: Tuple[str, ...]
    spine_ref: str
    subject_ref: str
    visit_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "spine_ref", _check_str(
            self.spine_ref, "R5TemporalSpineProjection.spine_ref"))
        object.__setattr__(self, "subject_ref", _check_str(
            self.subject_ref, "R5TemporalSpineProjection.subject_ref"))
        object.__setattr__(self, "cutoff_ref", _check_str(
            self.cutoff_ref, "R5TemporalSpineProjection.cutoff_ref"))
        object.__setattr__(self, "event_refs", _freeze_str_tuple(
            self.event_refs, "R5TemporalSpineProjection.event_refs"))
        object.__setattr__(self, "pending_date_refs", _freeze_str_tuple(
            self.pending_date_refs,
            "R5TemporalSpineProjection.pending_date_refs"))
        object.__setattr__(self, "phase_band_refs", _freeze_str_tuple(
            self.phase_band_refs,
            "R5TemporalSpineProjection.phase_band_refs"))
        object.__setattr__(self, "visit_refs", _freeze_str_tuple(
            self.visit_refs, "R5TemporalSpineProjection.visit_refs"))
        _verify_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5VisitNode:
    """One visit node on the temporal spine (deferred leaf)."""

    actual_date: Optional[date]
    date_state: str
    nominal_date: Optional[date]
    phase_ref: Optional[str]
    source_locator_refs: Tuple[str, ...]
    visit_kind: str
    visit_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "visit_ref", _check_str(
            self.visit_ref, "R5VisitNode.visit_ref"))
        object.__setattr__(self, "visit_kind", _check_closed(
            self.visit_kind, "R5VisitNode.visit_kind", VISIT_KINDS))
        object.__setattr__(self, "date_state", _check_closed(
            self.date_state, "R5VisitNode.date_state", DATE_STATES))
        object.__setattr__(self, "actual_date", _check_optional_date(
            self.actual_date, "R5VisitNode.actual_date"))
        object.__setattr__(self, "nominal_date", _check_optional_date(
            self.nominal_date, "R5VisitNode.nominal_date"))
        object.__setattr__(self, "phase_ref", _check_optional_str(
            self.phase_ref, "R5VisitNode.phase_ref"))
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5VisitNode.source_locator_refs"))
        if self.date_state == "missing" and (
                self.actual_date is not None or self.nominal_date is not None):
            raise R5ContractError(
                "R5VisitNode date_state=missing must carry no fabricated "
                "main-axis date (date_geometry_consistency)")
        if self.date_state == "exact" and (
                self.actual_date is None and self.nominal_date is None):
            raise R5ContractError(
                "R5VisitNode date_state=exact requires a precise date "
                "(date_geometry_consistency)")


