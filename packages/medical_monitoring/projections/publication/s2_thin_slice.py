"""R5 S2 W3 -- renderer-neutral offline thin-slice projection chain.

Projects one frozen ``R5S2AuthorityPacket`` (W2) onto the R5 public typed
surface (S0/S1 contracts) as the first offline thin vertical slice:

    project risk -> center cell -> Risk Inspector -> subject Workspace /
    deep link -> visit / event / risk anchor -> exact source

with a canonical return context and NO nearest fallback.

The projection is pure and fail-closed.  Every hop re-derives its identity
from the real packet objects (receipt, D10 risk marker, pattern / individual
members, deep-link target, source evidence) and rejects any inconsistency,
any non-empty S3/S4/S5 deferred leaf (``measure_refs``, Inspector
worker/support/counter refs and ``query_draft_ref``, temporal
``pending_date_refs``/``phase_band_refs``), any non-exact date, and any
nearest / snapped fallback.  No file IO, no network, no case / fixture /
test-id / sentinel branching.

Scope: this is synthetic/offline supplemental test authority under
``authority_mode = synthetic_offline_test_only``.  It never claims clinical
truth, real-project, product or production authority and never writes back
to R4 risk, visibility, denominator, adjudication or lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional, Tuple

from .contracts import (
    R5CenterMapCell,
    R5DeepLinkState,
    R5FilterState,
    R5JourneyEvent,
    R5PageState,
    R5ReturnContext,
    R5RiskAnchor,
    R5RiskInspectorProjection,
    R5ScrollState,
    R5SortState,
    R5SubjectWorkspaceState,
    R5TemporalSpineProjection,
    R5VisitNode,
)
from .s2_contracts import (
    AUTHORITY_MODE_S2,
    R5S2AuthorityPacket,
    R5S2ProjectRiskBinding,
    S2_DOMAINS,
    S2_SEVERITIES,
    s2_content_hash_excluding,
    s2_object_content_hash,
)

# ---------------------------------------------------------------------------
# Module identity / frozen scope
# ---------------------------------------------------------------------------

#: Self-declared projection schema id.  This value is NOT pinned by an
#: accepted S0/S2 artifact (unlike the packet schema id); it is a local
#: module identity so the projection record can be recognized on replay.
THIN_SLICE_SCHEMA_ID = "medical-monitoring-r5-s2-thin-slice-v0.1"

#: Closed severity precedence reused to re-derive the center severity from
#: the real typed members (high > medium > low; unknown/critical fail closed
#: because the S2 packet vocabulary is narrower than the R5 surface).
_SEVERITY_RANK: Dict[str, int] = {"high": 2, "medium": 1, "low": 0}


class ThinSliceProjectionError(Exception):
    """Fail-closed projection gate: a hop of the S2 thin-slice chain cannot
    be derived from the packet, or the derived chain is inconsistent.  No
    partial projection is emitted."""


# ---------------------------------------------------------------------------
# Renderer-neutral R5 presentation defaults (NOT packet-derived)
# ---------------------------------------------------------------------------

#: The subject Workspace opens on the journey view of the calendar axis for
#: a temporal deep link.  These are renderer-neutral R5 defaults -- not a
#: clinical fact and not derived from any packet id -- so they are pinned
#: here with provenance instead of being branched on at runtime.
R5_WORKSPACE_VIEW = "journey"
R5_WORKSPACE_AXIS = "calendar"
#: Neutral canonical return-context values (ephemeral client state, no
#: layout or filtering claim).
INSPECTOR_WIDTH_DEFAULT = 0
PAGE_SIZE_DEFAULT = 50
RETURN_SORT_KEY = "priority"
RETURN_SORT_DIRECTION = "asc"


# ---------------------------------------------------------------------------
# Deterministic evaluation window (frozen synthetic envelope authority)
# ---------------------------------------------------------------------------


def _parse_window_bound(text: str, name: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ThinSliceProjectionError(
            f"{name} is not an ISO-8601 date: {text!r}") from None


def _evaluation_window(
    packet: R5S2AuthorityPacket,
) -> Tuple[date, date]:
    """Read the exact window committed into the packet baseline item.

    W2 derives this value from the sole real R4 analysis window.  W3 never
    imports a builder date constant, guesses a nearby window or silently
    substitutes a renderer default.
    """
    if len(packet.reference_baseline_items) != 1:
        raise ThinSliceProjectionError(
            "the S2 packet must contain exactly one baseline temporal window")
    item, = packet.reference_baseline_items
    separator = ".." if ".." in item.temporal_window else "/"
    bounds = item.temporal_window.split(separator)
    if len(bounds) != 2:
        raise ThinSliceProjectionError(
            "baseline temporal_window must be one exact ISO date range")
    start = _parse_window_bound(bounds[0], "evaluation window start")
    end = _parse_window_bound(bounds[1], "evaluation window end")
    if end < start:
        raise ThinSliceProjectionError(
            "evaluation window end precedes start "
            f"({start.isoformat()} > {end.isoformat()})")
    return start, end


# ---------------------------------------------------------------------------
# Fail-closed packet / temporal pre-checks
# ---------------------------------------------------------------------------


def _require_packet(value: Any) -> R5S2AuthorityPacket:
    if not isinstance(value, R5S2AuthorityPacket):
        raise ThinSliceProjectionError(
            "the thin-slice chain requires an R5S2AuthorityPacket, got "
            f"{type(value).__name__}")
    return value


def _check_temporal_shape(packet: R5S2AuthorityPacket) -> None:
    """Every hop that touches the temporal chain re-verifies that the real
    packet identities agree (subject, risk, cutoff, source locator, exact
    anchors) so a tampered binding cannot silently project a wrong chain."""
    temporal = packet.temporal_binding
    link = packet.deep_link_target
    if link.subject_ref is None or temporal.subject_ref != link.subject_ref:
        raise ThinSliceProjectionError(
            "temporal subject_ref must equal the deep-link target subject_ref")
    if temporal.risk_ref != packet.project_risk_binding.risk_ref:
        raise ThinSliceProjectionError(
            "temporal risk_ref must equal the project-risk binding risk_ref")
    if temporal.cutoff_ref != packet.authority_receipt.cutoff_ref:
        raise ThinSliceProjectionError(
            "temporal cutoff_ref must equal the receipt cutoff_ref")
    if temporal.source_locator_ref != packet.source_binding.locator_id:
        raise ThinSliceProjectionError(
            "temporal source_locator_ref must equal the one-hop source "
            "locator id")
    for name in ("event_ref", "visit_ref", "risk_anchor_ref"):
        if not getattr(temporal, name):
            raise ThinSliceProjectionError(
                f"temporal {name} must be non-empty for the exact anchor chain")


# ---------------------------------------------------------------------------
# Hop 1: project risk -> center cell
# ---------------------------------------------------------------------------


def project_center_cell(packet: R5S2AuthorityPacket) -> R5CenterMapCell:
    """Center-cell hop of the chain.

    Re-derives the closed domain/severity from the real pattern/individual
    typed members and the center binding, and rejects any identity break:
    domain r4 == r5, individual refs == the pattern descendant refs == the
    real individual member refs, pattern/site == the real pattern member,
    severity == closed priority precedence, ``measure_refs`` empty (S3)."""
    _require_packet(packet)
    binding = packet.center_binding
    pattern = packet.center_pattern_member
    individuals = packet.individual_members

    if binding.r5_domain != binding.r4_risk_or_outcome_domain:
        raise ThinSliceProjectionError(
            "center r5_domain must equal r4_risk_or_outcome_domain "
            f"({binding.r5_domain!r} != {binding.r4_risk_or_outcome_domain!r})")
    if binding.r5_domain not in S2_DOMAINS:
        raise ThinSliceProjectionError(
            f"center domain {binding.r5_domain!r} is not a closed S2 domain")
    if binding.pattern_ref != pattern.member_ref:
        raise ThinSliceProjectionError(
            "center pattern_ref must equal the pattern member_ref "
            f"({binding.pattern_ref!r} != {pattern.member_ref!r})")
    if binding.site_ref != pattern.site_stable_id:
        raise ThinSliceProjectionError(
            "center site_ref must equal the pattern member site_stable_id")
    if set(binding.individual_risk_refs) != set(
            binding.pattern_descendant_member_refs):
        raise ThinSliceProjectionError(
            "center individual_risk_refs must equal the pattern descendant "
            "member refs")
    expected_refs = tuple(sorted(m.member_ref for m in individuals))
    if binding.individual_risk_refs != expected_refs:
        raise ThinSliceProjectionError(
            "center individual_risk_refs must equal the real individual "
            "member refs")

    priorities = [pattern.monitoring_priority] + [
        member.monitoring_priority for member in individuals]
    for priority in priorities:
        if priority not in S2_SEVERITIES:
            raise ThinSliceProjectionError(
                f"member monitoring_priority {priority!r} is not a closed "
                "S2 severity")
    derived_severity = max(
        priorities, key=lambda value: _SEVERITY_RANK[value])
    if derived_severity != binding.r5_severity:
        raise ThinSliceProjectionError(
            "center severity must equal the closed priority precedence "
            f"({derived_severity!r} != {binding.r5_severity!r})")
    if binding.measure_refs:
        raise ThinSliceProjectionError(
            "center measure_refs must stay empty (S3)")

    return R5CenterMapCell(
        domain=binding.r5_domain,
        individual_risk_refs=binding.individual_risk_refs,
        measure_refs=(),
        pattern_refs=(binding.pattern_ref,),
        severity=binding.r5_severity,
        site_ref=binding.site_ref,
    )


# ---------------------------------------------------------------------------
# Hop 2: Risk Inspector
# ---------------------------------------------------------------------------


def project_inspector(packet: R5S2AuthorityPacket) -> R5RiskInspectorProjection:
    """Risk-Inspector hop of the chain.

    Every public ref is re-derived from the real packet objects and the
    S4-deferred leaves are forced exactly empty/null.  The inspector
    authority receipt ref must equal the canonical receipt hash; domain and
    severity must equal the center cell; baseline refs must equal the
    sorted-unique reference-item ids (never attempt ids)."""
    _require_packet(packet)
    binding = packet.inspector_binding
    receipt = packet.authority_receipt
    center = packet.center_binding
    source = packet.source_binding
    evidence = packet.source_evidence
    risk = packet.project_risk_binding
    temporal = packet.temporal_binding

    if binding.authority_receipt_ref != s2_object_content_hash(receipt):
        raise ThinSliceProjectionError(
            "inspector authority_receipt_ref must equal the canonical "
            "receipt hash")
    if binding.risk_ref != risk.risk_ref or binding.risk_ref != temporal.risk_ref:
        raise ThinSliceProjectionError(
            "inspector risk_ref must equal the project/temporal risk ref")
    if binding.domain != center.r5_domain:
        raise ThinSliceProjectionError(
            "inspector domain must equal the center domain")
    if binding.severity != center.r5_severity:
        raise ThinSliceProjectionError(
            "inspector severity must equal the center severity")

    if binding.worker_output_refs or binding.support_evidence_refs or \
            binding.counterevidence_refs:
        raise ThinSliceProjectionError(
            "inspector worker/support/counterevidence refs must stay empty "
            "(S4)")
    if binding.query_draft_ref is not None:
        raise ThinSliceProjectionError(
            "inspector query_draft_ref must stay null (S4)")

    item_ids = tuple(sorted({item.item_id
                             for item in packet.reference_baseline_items}))
    if binding.baseline_assessment_refs != item_ids or \
            binding.baseline_item_refs != item_ids:
        raise ThinSliceProjectionError(
            "inspector baseline refs must equal the sorted-unique reference "
            "item ids (never attempt ids)")
    attempt_ids = tuple(sorted(a.attempt_id
                               for a in packet.analysis_attempts))
    if binding.analysis_attempt_refs != attempt_ids:
        raise ThinSliceProjectionError(
            "inspector analysis_attempt_refs must equal the real attempt ids")
    if tuple(binding.conflict_refs) != (packet.conflict.conflict_id,):
        raise ThinSliceProjectionError(
            "inspector conflict_refs must equal the real conflict id")
    if tuple(binding.verification_refs) != tuple(
            sorted(v.verification_id for v in packet.verifications)):
        raise ThinSliceProjectionError(
            "inspector verification_refs must equal the real verification "
            "ids")
    if binding.adjudication_ref != packet.adjudication.binding_id:
        raise ThinSliceProjectionError(
            "inspector adjudication_ref must equal the adjudication binding "
            "id")
    # The S2 conflict must stay visible and the adjudicator must stay
    # independent of both workers (mirrors the packet invariants so a
    # tampered packet cannot project a hidden/colliding Inspector).
    if packet.conflict.hidden or \
            packet.conflict.display_state != "visible_conflict":
        raise ThinSliceProjectionError(
            "the S2 conflict must be visible (never hidden)")
    worker_bindings = {attempt.binding_id
                       for attempt in packet.analysis_attempts}
    worker_sessions = {attempt.session_id
                       for attempt in packet.analysis_attempts}
    if packet.adjudication.binding_id in worker_bindings or \
            packet.adjudication.session_id in worker_sessions:
        raise ThinSliceProjectionError(
            "the adjudicator binding/session must differ from both workers")
    if source.locator_id != evidence.locator_id or \
            source.locator_id not in binding.source_locator_refs:
        raise ThinSliceProjectionError(
            "inspector source_locator_refs must include the exact one-hop "
            "source locator")

    return R5RiskInspectorProjection(
        adjudication_ref=binding.adjudication_ref,
        analysis_attempt_refs=binding.analysis_attempt_refs,
        authority_receipt_ref=binding.authority_receipt_ref,
        baseline_assessment_refs=binding.baseline_assessment_refs,
        baseline_item_refs=binding.baseline_item_refs,
        conflict_refs=binding.conflict_refs,
        counterevidence_refs=(),
        domain=binding.domain,
        query_draft_ref=None,
        risk_ref=binding.risk_ref,
        severity=binding.severity,
        source_locator_refs=binding.source_locator_refs,
        support_evidence_refs=(),
        verification_refs=binding.verification_refs,
        worker_output_refs=(),
    )


# ---------------------------------------------------------------------------
# Hop 3: subject Workspace + deep link
# ---------------------------------------------------------------------------


def project_workspace(packet: R5S2AuthorityPacket) -> R5SubjectWorkspaceState:
    """Subject-Workspace hop: one spine, one window and the exact anchor
    selection on the deep-link subject.  No nearest fallback; the selected
    visit/event/risk refs are the real temporal anchors."""
    _require_packet(packet)
    temporal = packet.temporal_binding
    _check_temporal_shape(packet)
    window_start, window_end = _evaluation_window(packet)
    return R5SubjectWorkspaceState(
        active_view=R5_WORKSPACE_VIEW,
        axis_mode=R5_WORKSPACE_AXIS,
        content_hash="",
        selected_event_ref=temporal.event_ref,
        selected_risk_ref=temporal.risk_ref,
        selected_visit_ref=temporal.visit_ref,
        spine_ref=temporal.spine_ref,
        subject_ref=temporal.subject_ref,
        window_end=window_end,
        window_start=window_start,
    )


def project_deep_link_state(packet: R5S2AuthorityPacket) -> R5DeepLinkState:
    """Workspace deep-link hop: the canonical state restoring the subject
    Workspace at the exact visit/event/risk anchor and the exact one-hop
    source locator.  An unavailable (non-locatable) target or a missing
    exact anchor fails closed -- never a nearest/snapped jump."""
    _require_packet(packet)
    risk = packet.project_risk_binding
    temporal = packet.temporal_binding
    link = packet.deep_link_target
    center = packet.center_binding
    source = packet.source_binding
    _check_temporal_shape(packet)

    if link.target_state != "locatable" or \
            link.locator_resolution_state != "locatable":
        raise ThinSliceProjectionError(
            "deep-link target must be locatable (no nearest fallback)")
    if link.source_locator is None or link.source_locator != source.locator_id:
        raise ThinSliceProjectionError(
            "deep-link source_locator must equal the one-hop source locator")
    if temporal.event_ref is None or temporal.visit_ref is None:
        raise ThinSliceProjectionError(
            "deep link requires the exact visit/event anchors")

    window_start, window_end = _evaluation_window(packet)
    return R5DeepLinkState(
        axis_mode=R5_WORKSPACE_AXIS,
        cutoff_ref=risk.cutoff_ref,
        event_ref=temporal.event_ref,
        project_ref=risk.project_ref,
        return_context_key=link.return_state_key,
        risk_anchor_ref=temporal.risk_anchor_ref,
        risk_ref=risk.risk_ref,
        run_ref=risk.run_ref,
        site_ref=center.site_ref,
        snapshot_ref=risk.snapshot_ref,
        source_locator_ref=source.locator_id,
        spine_ref=temporal.spine_ref,
        subject_ref=temporal.subject_ref,
        view=R5_WORKSPACE_VIEW,
        visit_ref=temporal.visit_ref,
        window_end=window_end,
        window_start=window_start,
    )


# ---------------------------------------------------------------------------
# Hop 4: visit / event / risk anchor (exact-date temporal chain)
# ---------------------------------------------------------------------------


def project_temporal_spine(
    packet: R5S2AuthorityPacket,
) -> R5TemporalSpineProjection:
    """Temporal spine hop: one exact visit, one event and one risk anchor on
    one shared subject spine.  ``pending_date_refs``/``phase_band_refs`` stay
    empty (S5)."""
    _require_packet(packet)
    temporal = packet.temporal_binding
    _check_temporal_shape(packet)
    return R5TemporalSpineProjection(
        content_hash="",
        cutoff_ref=temporal.cutoff_ref,
        event_refs=(temporal.event_ref,),
        pending_date_refs=(),
        phase_band_refs=(),
        spine_ref=temporal.spine_ref,
        subject_ref=temporal.subject_ref,
        visit_refs=(temporal.visit_ref,),
    )


def project_visit_node(packet: R5S2AuthorityPacket) -> R5VisitNode:
    """Visit-anchor hop: an exact actual-date visit; the nominal date never
    replaces the actual date and no nearest visit matching is allowed."""
    _require_packet(packet)
    temporal = packet.temporal_binding
    _check_temporal_shape(packet)
    if temporal.date_state != "exact":
        raise ThinSliceProjectionError(
            "visit date_state must be exact for the single temporal chain")
    if temporal.actual_date is None:
        raise ThinSliceProjectionError(
            "visit date_state=exact requires actual_date (no nearest "
            "fallback)")
    if temporal.actual_date != temporal.event_start:
        raise ThinSliceProjectionError(
            "visit actual_date must equal the event start (no snapped or "
            "fabricated date)")
    if temporal.nominal_date is not None and temporal.actual_date is None:
        raise ThinSliceProjectionError(
            "nominal_date must never replace the actual_date")
    return R5VisitNode(
        actual_date=temporal.actual_date,
        date_state=temporal.date_state,
        nominal_date=temporal.nominal_date,
        phase_ref=temporal.phase_ref,
        source_locator_refs=(temporal.source_locator_ref,),
        visit_kind=temporal.visit_kind,
        visit_ref=temporal.visit_ref,
    )


def project_journey_event(packet: R5S2AuthorityPacket) -> R5JourneyEvent:
    """Event-anchor hop: the exact event window bound to the center domain
    and the one-hop source locator."""
    _require_packet(packet)
    temporal = packet.temporal_binding
    _check_temporal_shape(packet)
    if temporal.event_start is None:
        raise ThinSliceProjectionError(
            "event date_state=exact requires event_start (no nearest "
            "fallback)")
    if (temporal.event_end is not None
            and temporal.event_end < temporal.event_start):
        raise ThinSliceProjectionError(
            "event_end must not precede event_start")
    return R5JourneyEvent(
        date_state=temporal.date_state,
        domain=temporal.domain,
        end=temporal.event_end,
        event_ref=temporal.event_ref,
        risk_anchor_refs=(temporal.risk_anchor_ref,),
        source_locator_refs=(temporal.source_locator_ref,),
        start=temporal.event_start,
        subtype=temporal.event_subtype,
    )


def project_risk_anchor(packet: R5S2AuthorityPacket) -> R5RiskAnchor:
    """Risk-anchor hop: the center-domain risk anchored at the exact event
    and visit of the deep-link subject."""
    _require_packet(packet)
    temporal = packet.temporal_binding
    _check_temporal_shape(packet)
    return R5RiskAnchor(
        date_state=temporal.date_state,
        domain=temporal.domain,
        event_ref=temporal.event_ref,
        risk_ref=temporal.risk_ref,
        risk_type_zh=temporal.risk_type_zh,
        severity=temporal.severity,
        visit_ref=temporal.visit_ref,
    )


# ---------------------------------------------------------------------------
# Hop 5: exact source (one-hop) + canonical return context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S2SourceResolution:
    """The exact one-hop source of the chain: the locatable synthetic
    deep-link locator bound to one typed ``EvidenceRef`` and one receipt
    source revision-content pair, with ``fallback_policy=none``."""

    content_hash: str
    fallback_policy: str
    lineage_ref: str
    locator_id: str
    locator_kind: str
    resolution_state: str
    revision_content_hash: str
    revision_id: str
    row_or_cell_ref: str
    source_file: str

    def __post_init__(self) -> None:
        for name in ("locator_id", "locator_kind", "source_file",
                     "row_or_cell_ref", "lineage_ref", "revision_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ThinSliceProjectionError(
                    f"R5S2SourceResolution.{name} must be a non-empty str")
        object.__setattr__(self, "fallback_policy", _check_closed_s2(
            self.fallback_policy, "R5S2SourceResolution.fallback_policy",
            ("none",)))
        object.__setattr__(self, "resolution_state", _check_closed_s2(
            self.resolution_state, "R5S2SourceResolution.resolution_state",
            ("locatable",)))
        _check_hash_str(self.revision_content_hash,
                        "R5S2SourceResolution.revision_content_hash")
        object.__setattr__(
            self, "content_hash",
            s2_content_hash_excluding(self, ("content_hash",)))


@dataclass(frozen=True)
class R5S2ThinSliceProjection:
    """The renderer-neutral projection chain of one thin-slice packet:
    project risk -> center cell -> Inspector -> Workspace/deep link ->
    visit/event/risk anchor -> exact source, plus the canonical return
    context.  ``content_hash`` covers every non-hash field."""

    center_cell: R5CenterMapCell
    content_hash: str
    deep_link_state: R5DeepLinkState
    inspector: R5RiskInspectorProjection
    journey_event: R5JourneyEvent
    project_risk: R5S2ProjectRiskBinding
    return_context: R5ReturnContext
    risk_anchor: R5RiskAnchor
    source: R5S2SourceResolution
    temporal_spine: R5TemporalSpineProjection
    visit_node: R5VisitNode
    workspace: R5SubjectWorkspaceState

    def __post_init__(self) -> None:
        _check_obj_type(self.center_cell, R5CenterMapCell,
                        "R5S2ThinSliceProjection.center_cell")
        _check_obj_type(self.deep_link_state, R5DeepLinkState,
                        "R5S2ThinSliceProjection.deep_link_state")
        _check_obj_type(self.inspector, R5RiskInspectorProjection,
                        "R5S2ThinSliceProjection.inspector")
        _check_obj_type(self.journey_event, R5JourneyEvent,
                        "R5S2ThinSliceProjection.journey_event")
        _check_obj_type(self.project_risk, R5S2ProjectRiskBinding,
                        "R5S2ThinSliceProjection.project_risk")
        _check_obj_type(self.return_context, R5ReturnContext,
                        "R5S2ThinSliceProjection.return_context")
        _check_obj_type(self.risk_anchor, R5RiskAnchor,
                        "R5S2ThinSliceProjection.risk_anchor")
        _check_obj_type(self.source, R5S2SourceResolution,
                        "R5S2ThinSliceProjection.source")
        _check_obj_type(self.temporal_spine, R5TemporalSpineProjection,
                        "R5S2ThinSliceProjection.temporal_spine")
        _check_obj_type(self.visit_node, R5VisitNode,
                        "R5S2ThinSliceProjection.visit_node")
        _check_obj_type(self.workspace, R5SubjectWorkspaceState,
                        "R5S2ThinSliceProjection.workspace")
        object.__setattr__(
            self, "content_hash",
            s2_content_hash_excluding(self, ("content_hash",)))


def resolve_exact_source(packet: R5S2AuthorityPacket) -> R5S2SourceResolution:
    """Source hop: resolve the deep-link source locator to the exact typed
    ``EvidenceRef`` and the receipt's single source revision-content pair.
    Absence, ambiguity, a non-locatable target or a nearest fallback fails
    closed."""
    _require_packet(packet)
    source = packet.source_binding
    evidence = packet.source_evidence
    link = packet.deep_link_target

    if source.locator_id != evidence.locator_id:
        raise ThinSliceProjectionError(
            "source binding locator_id must equal the EvidenceRef locator_id")
    if link.source_locator is None or link.source_locator != source.locator_id:
        raise ThinSliceProjectionError(
            "deep-link source_locator must equal the source binding locator "
            "id")
    if source.fallback_policy != "none":
        raise ThinSliceProjectionError(
            "fallback_policy must be none (no nearest fallback)")
    if source.resolution_state != "locatable":
        raise ThinSliceProjectionError(
            "source resolution_state must be locatable")
    if source.lineage_ref != evidence.lineage_ref or \
            source.locator_kind != evidence.locator_kind or \
            source.row_or_cell_ref != evidence.row_or_cell_ref or \
            source.source_file != evidence.source_file:
        raise ThinSliceProjectionError(
            "source lineage/row/cell/file must equal the EvidenceRef")
    pairs = packet.authority_receipt.source_revision_content_pairs
    if len(pairs) != 1:
        raise ThinSliceProjectionError(
            "source revision-content pair must equal the receipt's single "
            "pair")
    pair, = pairs
    if pair.revision_id != source.revision_id or \
            pair.content_hash != source.revision_content_hash:
        raise ThinSliceProjectionError(
            "source revision-content pair must equal the receipt's single "
            "pair")

    return R5S2SourceResolution(
        content_hash="",
        fallback_policy=source.fallback_policy,
        lineage_ref=source.lineage_ref,
        locator_id=source.locator_id,
        locator_kind=source.locator_kind,
        resolution_state=source.resolution_state,
        revision_content_hash=source.revision_content_hash,
        revision_id=source.revision_id,
        row_or_cell_ref=source.row_or_cell_ref,
        source_file=source.source_file,
    )


def project_return_context(
    packet: R5S2AuthorityPacket,
    deep_link_state: Optional[R5DeepLinkState] = None,
) -> R5ReturnContext:
    """Canonical return context wrapping the projected deep-link state plus
    neutral ephemeral client state.  ``canonical_state_hash`` is the
    deterministic canonical hash of the non-hash fields."""
    _require_packet(packet)
    if deep_link_state is None:
        deep_link_state = project_deep_link_state(packet)
    if not isinstance(deep_link_state, R5DeepLinkState):
        raise ThinSliceProjectionError(
            "return context requires an R5DeepLinkState, got "
            f"{type(deep_link_state).__name__}")
    filter_state = R5FilterState(
        change_kind=(), domain=(), include_low=False, severity=(),
        site_refs=())
    page_state = R5PageState(page_index=0, page_size=PAGE_SIZE_DEFAULT)
    scroll_state = R5ScrollState(
        center_map_y=0, project_list_y=0, workspace_y=0)
    sort_state = R5SortState(
        direction=RETURN_SORT_DIRECTION, key=RETURN_SORT_KEY)
    return R5ReturnContext(
        canonical_state_hash="",
        deep_link_state=deep_link_state,
        filter_state=filter_state,
        inspector_width=INSPECTOR_WIDTH_DEFAULT,
        page_state=page_state,
        scroll_state=scroll_state,
        sort_state=sort_state,
        temporary_expansion_refs=(),
    )


# ---------------------------------------------------------------------------
# Chain composition + fail-closed re-verification
# ---------------------------------------------------------------------------


def validate_thin_slice(projection: R5S2ThinSliceProjection) -> Dict[str, Any]:
    """Fail-closed re-verification of one projected chain.  Returns
    ``{"valid": bool, "reasons": tuple[str, ...]}``; an invalid chain must
    never be accepted.  Mirrors the packet validator contract."""
    if not isinstance(projection, R5S2ThinSliceProjection):
        return {"valid": False,
                "reasons": ("projection_type_mismatch",)}
    reasons: list = []
    center = projection.center_cell
    inspector = projection.inspector
    anchor = projection.risk_anchor
    event = projection.journey_event
    visit = projection.visit_node
    spine = projection.temporal_spine
    deep = projection.deep_link_state
    workspace = projection.workspace
    risk = projection.project_risk
    source = projection.source

    # Deferred leaves stay exactly empty/null.
    if inspector.worker_output_refs or inspector.support_evidence_refs or \
            inspector.counterevidence_refs:
        reasons.append("s4_public_inspector_refs_leak")
    if inspector.query_draft_ref is not None:
        reasons.append("s4_query_draft_leak")
    if center.measure_refs:
        reasons.append("s3_measure_refs_leak")
    if spine.pending_date_refs or spine.phase_band_refs:
        reasons.append("s5_temporal_deferred_leak")

    # Identity closure across the whole chain.
    if not (center.domain == inspector.domain == anchor.domain == event.domain):
        reasons.append("domain_closure_mismatch")
    if not (center.severity == inspector.severity == anchor.severity):
        reasons.append("severity_closure_mismatch")
    if not (risk.risk_ref == inspector.risk_ref == anchor.risk_ref
            == deep.risk_ref):
        reasons.append("risk_identity_closure_mismatch")
    if not (risk.project_ref == deep.project_ref
            and risk.run_ref == deep.run_ref
            and risk.snapshot_ref == deep.snapshot_ref
            and risk.cutoff_ref == deep.cutoff_ref):
        reasons.append("run_snapshot_closure_mismatch")
    if not (deep.event_ref == event.event_ref == anchor.event_ref
            and deep.visit_ref == visit.visit_ref == anchor.visit_ref):
        reasons.append("anchor_closure_mismatch")
    if not (workspace.subject_ref == deep.subject_ref == spine.subject_ref):
        reasons.append("subject_closure_mismatch")
    if not (workspace.spine_ref == deep.spine_ref == spine.spine_ref):
        reasons.append("spine_closure_mismatch")
    if workspace.selected_event_ref != deep.event_ref or \
            workspace.selected_visit_ref != deep.visit_ref:
        reasons.append("workspace_selection_closure_mismatch")
    if event.event_ref not in spine.event_refs or \
            visit.visit_ref not in spine.visit_refs:
        reasons.append("spine_refs_closure_mismatch")

    # Exact source / deep-link round trip (no nearest fallback).
    if source.locator_id != deep.source_locator_ref:
        reasons.append("source_deeplink_roundtrip_mismatch")
    if source.fallback_policy != "none":
        reasons.append("nearest_fallback_forbidden")
    if source.locator_id not in inspector.source_locator_refs:
        reasons.append("inspector_source_ref_missing")

    # No date fabrication / no nearest fallback on the exact chain.
    if visit.actual_date is None or event.start is None:
        reasons.append("missing_exact_anchor_date")
    if visit.actual_date != event.start:
        reasons.append("anchor_date_mismatch")
    if deep.window_start is not None and event.start is not None:
        if not (deep.window_start <= event.start <= deep.window_end):
            reasons.append("anchor_outside_evaluation_window")

    # Canonical return context round trip.
    if projection.return_context.deep_link_state is not deep:
        reasons.append("return_context_deeplink_roundtrip_mismatch")

    return {"valid": not reasons, "reasons": tuple(reasons)}


def project_thin_slice(packet: R5S2AuthorityPacket) -> R5S2ThinSliceProjection:
    """Project the whole thin-slice chain from one frozen packet.  Any hop
    failure or cross-hop inconsistency raises ``ThinSliceProjectionError``
    and no partial projection is emitted."""
    _require_packet(packet)
    center_cell = project_center_cell(packet)
    inspector = project_inspector(packet)
    workspace = project_workspace(packet)
    temporal_spine = project_temporal_spine(packet)
    visit_node = project_visit_node(packet)
    journey_event = project_journey_event(packet)
    risk_anchor = project_risk_anchor(packet)
    deep_link_state = project_deep_link_state(packet)
    return_context = project_return_context(packet, deep_link_state)
    source = resolve_exact_source(packet)
    projection = R5S2ThinSliceProjection(
        content_hash="",
        center_cell=center_cell,
        deep_link_state=deep_link_state,
        inspector=inspector,
        journey_event=journey_event,
        project_risk=packet.project_risk_binding,
        return_context=return_context,
        risk_anchor=risk_anchor,
        source=source,
        temporal_spine=temporal_spine,
        visit_node=visit_node,
        workspace=workspace,
    )
    result = validate_thin_slice(projection)
    if not result["valid"]:
        raise ThinSliceProjectionError(
            "thin-slice chain invalid: " + "; ".join(result["reasons"]))
    return projection


def is_thin_slice_projection(value: Any) -> bool:
    """True iff ``value`` is a projected ``R5S2ThinSliceProjection``."""
    return isinstance(value, R5S2ThinSliceProjection)


# ---------------------------------------------------------------------------
# Shared fail-closed shape helpers
# ---------------------------------------------------------------------------


def _check_closed_s2(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise ThinSliceProjectionError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_hash_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
            ch not in "0123456789abcdef" for ch in value):
        raise ThinSliceProjectionError(
            f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_obj_type(value: Any, cls: type, name: str) -> None:
    if not isinstance(value, cls):
        raise ThinSliceProjectionError(
            f"{name} must be a {cls.__name__}, got {type(value).__name__}")


__all__ = [
    "AUTHORITY_MODE_S2",
    "INSPECTOR_WIDTH_DEFAULT",
    "PAGE_SIZE_DEFAULT",
    "R5S2SourceResolution",
    "R5S2ThinSliceProjection",
    "R5_WORKSPACE_AXIS",
    "R5_WORKSPACE_VIEW",
    "RETURN_SORT_DIRECTION",
    "RETURN_SORT_KEY",
    "THIN_SLICE_SCHEMA_ID",
    "ThinSliceProjectionError",
    "is_thin_slice_projection",
    "project_center_cell",
    "project_deep_link_state",
    "project_inspector",
    "project_journey_event",
    "project_return_context",
    "project_risk_anchor",
    "project_temporal_spine",
    "project_thin_slice",
    "project_visit_node",
    "project_workspace",
    "resolve_exact_source",
    "validate_thin_slice",
]
