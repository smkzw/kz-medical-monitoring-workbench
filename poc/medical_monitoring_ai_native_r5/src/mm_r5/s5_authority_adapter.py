"""Adapter from the accepted typed public-authority packets to S5 records.

The adapter has one authority boundary: an exact ``AuthorityBundleV02`` from
``public_authority_common``.  It never accepts a candidate packet, mapping,
fixture text, path, or UI state as authority.  The accepted subject and AEMH
producers are called first and their packets are converted field-for-field to
the S5 date/identity types.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mm_r5 import aemh_match_history_public as aemh
from mm_r5 import public_authority_common as common
from mm_r5 import subject_temporal_public as temporal
from mm_r5.s5_contracts import (
    S5AEMHHistoryEntry,
    S5AEMHIdentityEvidence,
    S5AEMHMembershipIndex,
    S5AEMHPacket,
    S5AEMHPrefixAnchor,
    S5AEMHProjection,
    S5AEMHThread,
    S5AuthorityReceipt,
    S5AxisBasis,
    S5CutoffEndpoint,
    S5DateEndpoint,
    S5DomainTrack,
    S5JourneyEvent,
    S5MembershipIndex,
    S5PendingDateItem,
    S5PhaseBand,
    S5RiskAnchor,
    S5ScopeIdentity,
    S5SourceLocator,
    S5SourceRevisionContentPair,
    S5SubjectTemporalPacket,
    S5SubjectTemporalProjection,
    S5VisibilityClosure,
    S5VisitNode,
    S5AuthorityAdapterError,
    S5RuntimeImplementationError,
)


def _date_or_none(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise S5AuthorityAdapterError("DATE_PARSE_FAILED") from exc


def _require_bundle(source: Any, target_contract: str) -> common.AuthorityBundleV02:
    if type(source) is not common.AuthorityBundleV02:
        # This explicit branch keeps a candidate output from being reused as
        # authority, even if it happens to expose the same field names.
        if isinstance(source, (S5SubjectTemporalPacket, S5AEMHPacket)):
            raise S5AuthorityAdapterError("CANDIDATE_OUTPUT_AS_AUTHORITY")
        raise S5AuthorityAdapterError("TYPED_AUTHORITY_REQUIRED")
    if source.target_contract != target_contract:
        raise S5AuthorityAdapterError("AUTHORITY_TARGET_MISMATCH")
    return source


def _public_subject(source: common.AuthorityBundleV02) -> temporal.SubjectTemporalAuthorityPacket:
    try:
        packet = temporal.build_subject_temporal_authority(source)
        checked = temporal.validate_subject_temporal_authority(packet, source)
    except common.PublicAuthorityConstructionError as exc:
        raise S5AuthorityAdapterError(exc.result.primary_code or "PUBLIC_AUTHORITY_REJECTED") from exc
    if not checked.ok:
        raise S5AuthorityAdapterError(checked.primary_code or "PUBLIC_AUTHORITY_REJECTED")
    return packet


def _public_aemh(source: common.AuthorityBundleV02) -> aemh.AEMHMatchHistoryAuthorityPacket:
    try:
        packet = aemh.build_aemh_match_history_authority(source)
        checked = aemh.validate_aemh_match_history_authority(packet, source)
    except common.PublicAuthorityConstructionError as exc:
        raise S5AuthorityAdapterError(exc.result.primary_code or "PUBLIC_AUTHORITY_REJECTED") from exc
    if not checked.ok:
        raise S5AuthorityAdapterError(checked.primary_code or "PUBLIC_AUTHORITY_REJECTED")
    return packet


def _scope(value: common.PublicScopeIdentity) -> S5ScopeIdentity:
    return S5ScopeIdentity(
        cutoff_ref=value.cutoff_ref,
        cutoff_state=value.cutoff_state,
        identity_content_hash=value.identity_content_hash,
        project_ref=value.project_ref,
        run_ref=value.run_ref,
        site_ref=value.site_ref,
        snapshot_ref=value.snapshot_ref,
        spine_ref=value.spine_ref,
        subject_ref=value.subject_ref,
    )


def _locator(value: common.PublicSourceLocator) -> S5SourceLocator:
    return S5SourceLocator(
        authority_entity_kind=value.authority_entity_kind,
        authority_entity_ref=value.authority_entity_ref,
        canonical_location=value.canonical_location,
        column_or_anchor=value.column_or_anchor,
        locator_content_hash=value.locator_content_hash,
        locator_ref=value.locator_ref,
        locator_variant=value.locator_variant,
        raw_payload_hash=value.raw_payload_hash,
        record_ref=value.record_ref,
        snapshot_ref=value.snapshot_ref,
        source_file_ref=value.source_file_ref,
        source_revision_content_hash=value.source_revision_content_hash,
        source_revision_ref=value.source_revision_ref,
        table_semantic=value.table_semantic,
    )


def _revision_pair(value: common.SourceRevisionContentPair) -> S5SourceRevisionContentPair:
    return S5SourceRevisionContentPair(
        accepted_content_hash=value.accepted_content_hash,
        locator_refs=tuple(value.locator_refs),
        pair_content_hash=value.pair_content_hash,
        revision_id=value.revision_id,
    )


def _visibility(value: common.VisibilityClosure) -> S5VisibilityClosure:
    return S5VisibilityClosure(
        closure_content_hash=value.closure_content_hash,
        deep_link_eligible=value.deep_link_eligible,
        evaluation_member_refs=tuple(value.evaluation_member_refs),
        evaluation_site_refs=tuple(value.evaluation_site_refs),
        hidden_member_count=value.hidden_member_count,
        hidden_member_refs=tuple(value.hidden_member_refs),
        hidden_site_count=value.hidden_site_count,
        hidden_site_refs=tuple(value.hidden_site_refs),
        projectable_member_refs=tuple(value.projectable_member_refs),
        projectable_site_refs=tuple(value.projectable_site_refs),
        subject_visibility_state=value.subject_visibility_state,
        visibility_decision_hash=value.visibility_decision_hash,
        visibility_decision_id=value.visibility_decision_id,
    )


def _receipt(value: common.PublicAuthorityReceipt) -> S5AuthorityReceipt:
    return S5AuthorityReceipt(
        audience_contract_id=value.audience_contract_id,
        authority_contract_id=value.authority_contract_id,
        authority_contract_version=value.authority_contract_version,
        evaluation_content_identities=tuple(value.evaluation_content_identities),
        public_projection_content_hash=value.public_projection_content_hash,
        public_projection_id=value.public_projection_id,
        receipt_content_hash=value.receipt_content_hash,
        receipt_id=value.receipt_id,
        receipt_variant=value.receipt_variant,
        scope_identity=_scope(value.scope_identity),
        source_revision_content_pairs=tuple(_revision_pair(item) for item in value.source_revision_content_pairs),
        visibility_closure=_visibility(value.visibility_closure),
    )


def _endpoint(value: temporal.TemporalDateEndpoint) -> S5DateEndpoint:
    return S5DateEndpoint(
        candidate_values=tuple(value.candidate_values),
        endpoint_content_hash=value.endpoint_content_hash,
        exact_date=_date_or_none(value.exact_date),
        main_axis_projectable=value.main_axis_projectable,
        range_end=_date_or_none(value.range_end),
        range_projection_authorized=value.range_projection_authorized,
        range_start=_date_or_none(value.range_start),
        source_locator_refs=tuple(value.source_locator_refs),
        state=value.state,
        study_day=value.study_day,
    )


def _cutoff(value: common.PublicCutoffEndpoint) -> S5CutoffEndpoint:
    return S5CutoffEndpoint(
        cutoff_content_hash=value.cutoff_content_hash,
        exact_date=_date_or_none(value.exact_date),
        source_locator_refs=tuple(value.source_locator_refs),
        state=value.state,
    )


def _temporal_cutoff(value: temporal.TemporalDateEndpoint) -> S5CutoffEndpoint:
    """The subject producer represents cutoff as a temporal endpoint."""
    return S5CutoffEndpoint(
        cutoff_content_hash=value.endpoint_content_hash,
        exact_date=_date_or_none(value.exact_date),
        source_locator_refs=tuple(value.source_locator_refs),
        state="present" if value.exact_date is not None else "absent",
    )


def _subject_projection(value: temporal.SubjectTemporalPublicProjection) -> S5SubjectTemporalProjection:
    return S5SubjectTemporalProjection(
        axis_basis=S5AxisBasis(
            axis_content_hash=value.axis_basis.axis_content_hash,
            axis_ref=value.axis_basis.axis_ref,
            cutoff_endpoint=_endpoint(value.axis_basis.cutoff_endpoint),
            default_axis_mode=value.axis_basis.default_axis_mode,
            source_locator_refs=tuple(value.axis_basis.source_locator_refs),
            study_day_anchor_event_ref=value.axis_basis.study_day_anchor_event_ref,
            study_day_zero_exists=value.axis_basis.study_day_zero_exists,
            timezone=value.axis_basis.timezone,
        ),
        contract_id=value.contract_id,
        domain_tracks=tuple(S5DomainTrack(
            applicability_state=item.applicability_state,
            domain=item.domain,
            event_refs=tuple(item.event_refs),
            risk_anchor_refs=tuple(item.risk_anchor_refs),
            track_content_hash=item.track_content_hash,
        ) for item in value.domain_tracks),
        events=tuple(S5JourneyEvent(
            applicability_state=item.applicability_state,
            domain=item.domain,
            end_endpoint=_endpoint(item.end_endpoint),
            event_content_hash=item.event_content_hash,
            event_content_identity=item.event_content_identity,
            event_ref=item.event_ref,
            geometry=item.geometry,
            risk_anchor_refs=tuple(item.risk_anchor_refs),
            source_locator_refs=tuple(item.source_locator_refs),
            start_endpoint=_endpoint(item.start_endpoint),
            subtype=item.subtype,
            visit_ref=item.visit_ref,
        ) for item in value.events),
        fallback_policy=value.fallback_policy,
        membership_index=S5MembershipIndex(
            event_refs=tuple(value.membership_index.event_refs),
            membership_content_hash=value.membership_index.membership_content_hash,
            pending_date_refs=tuple(value.membership_index.pending_date_refs),
            phase_refs=tuple(value.membership_index.phase_refs),
            risk_anchor_refs=tuple(value.membership_index.risk_anchor_refs),
            source_locator_refs=tuple(value.membership_index.source_locator_refs),
            visit_refs=tuple(value.membership_index.visit_refs),
        ),
        pending_date_items=tuple(S5PendingDateItem(
            domain=item.domain,
            end_endpoint=_endpoint(item.end_endpoint),
            item_kind=item.item_kind,
            item_ref=item.item_ref,
            pending_content_hash=item.pending_content_hash,
            pending_ref=item.pending_ref,
            source_locator_refs=tuple(item.source_locator_refs),
            start_endpoint=_endpoint(item.start_endpoint),
            target_content_hash=item.target_content_hash,
        ) for item in value.pending_date_items),
        phase_bands=tuple(S5PhaseBand(
            end_endpoint=_endpoint(item.end_endpoint),
            geometry=item.geometry,
            phase_content_hash=item.phase_content_hash,
            phase_label_zh=item.phase_label_zh,
            phase_ref=item.phase_ref,
            source_locator_refs=tuple(item.source_locator_refs),
            start_endpoint=_endpoint(item.start_endpoint),
        ) for item in value.phase_bands),
        projection_content_hash=value.projection_content_hash,
        projection_id=value.projection_id,
        receipt_ref=value.receipt_ref,
        risk_anchors=tuple(S5RiskAnchor(
            domain=item.domain,
            end_endpoint=_endpoint(item.end_endpoint),
            event_ref=item.event_ref,
            geometry=item.geometry,
            risk_anchor_content_hash=item.risk_anchor_content_hash,
            risk_anchor_ref=item.risk_anchor_ref,
            risk_content_identity=item.risk_content_identity,
            risk_ref=item.risk_ref,
            risk_type_zh=item.risk_type_zh,
            severity=item.severity,
            source_locator_refs=tuple(item.source_locator_refs),
            start_endpoint=_endpoint(item.start_endpoint),
            visit_ref=item.visit_ref,
        ) for item in value.risk_anchors),
        schema_version=value.schema_version,
        scope_identity=_scope(value.scope_identity),
        source_locators=tuple(_locator(item) for item in value.source_locators),
        visits=tuple(S5VisitNode(
            accepted_assignment_ref=item.accepted_assignment_ref,
            actual_encounter_ref=item.actual_encounter_ref,
            actual_endpoint=_endpoint(item.actual_endpoint) if item.actual_endpoint is not None else None,
            nominal_endpoint=_endpoint(item.nominal_endpoint) if item.nominal_endpoint is not None else None,
            phase_ref=item.phase_ref,
            planned_visit_ref=item.planned_visit_ref,
            source_locator_refs=tuple(item.source_locator_refs),
            visit_content_hash=item.visit_content_hash,
            visit_kind=item.visit_kind,
            visit_ref=item.visit_ref,
        ) for item in value.visits),
    )


def adapt_subject_temporal_authority(source: common.AuthorityBundleV02) -> S5SubjectTemporalPacket:
    """Build an S5 subject packet from typed authority only."""
    source = _require_bundle(source, common.SUBJECT_CONTRACT_ID)
    packet = _public_subject(source)
    return S5SubjectTemporalPacket(
        packet_content_hash=packet.packet_content_hash,
        projection=_subject_projection(packet.projection),
        receipt=_receipt(packet.receipt),
    )


def _aemh_entry(value: aemh.AEMHMatchHistoryEntry) -> S5AEMHHistoryEntry:
    return S5AEMHHistoryEntry(
        entry_hash=value.entry_hash,
        entry_id=value.entry_id,
        event_kind=value.event_kind,
        identity_evidence=tuple(S5AEMHIdentityEvidence(
            entity_content_identity=item.entity_content_identity,
            entity_ref=item.entity_ref,
            evidence_content_hash=item.evidence_content_hash,
            evidence_kind=item.evidence_kind,
            evidence_ref=item.evidence_ref,
            source_locator_content_hash=item.source_locator_content_hash,
            source_locator_ref=item.source_locator_ref,
            source_raw_payload_hash=item.source_raw_payload_hash,
        ) for item in value.identity_evidence),
        identity_evidence_refs=tuple(value.identity_evidence_refs),
        later_fact_content_identities=tuple(value.later_fact_content_identities),
        later_fact_refs=tuple(value.later_fact_refs),
        match_state=value.match_state,
        prior_entry_hash=value.prior_entry_hash,
        reason_code=value.reason_code,
        retained_evidence_locator_refs=tuple(value.retained_evidence_locator_refs),
        risk_lifecycle_effect=value.risk_lifecycle_effect,
        seq=value.seq,
        snapshot_ref=value.snapshot_ref,
    )


def _aemh_projection(value: aemh.AEMHMatchHistoryPublicProjection) -> S5AEMHProjection:
    return S5AEMHProjection(
        accepted_thread_prefixes=tuple(S5AEMHPrefixAnchor(
            accepted_prefix_head_hash=item.accepted_prefix_head_hash,
            accepted_prefix_seq=item.accepted_prefix_seq,
            prefix_content_hash=item.prefix_content_hash,
            previous_thread_content_hash=item.previous_thread_content_hash,
            thread_ref=item.thread_ref,
        ) for item in value.accepted_thread_prefixes),
        contract_id=value.contract_id,
        cutoff_endpoint=_cutoff(value.cutoff_endpoint),
        fallback_policy=value.fallback_policy,
        membership_index=S5AEMHMembershipIndex(
            candidate_refs=tuple(value.membership_index.candidate_refs),
            later_fact_refs=tuple(value.membership_index.later_fact_refs),
            membership_content_hash=value.membership_index.membership_content_hash,
            source_locator_refs=tuple(value.membership_index.source_locator_refs),
            thread_refs=tuple(value.membership_index.thread_refs),
        ),
        previous_projection_content_hash=value.previous_projection_content_hash,
        previous_projection_ref=value.previous_projection_ref,
        projection_content_hash=value.projection_content_hash,
        projection_id=value.projection_id,
        receipt_ref=value.receipt_ref,
        schema_version=value.schema_version,
        scope_identity=_scope(value.scope_identity),
        source_locators=tuple(_locator(item) for item in value.source_locators),
        threads=tuple(S5AEMHThread(
            candidate_content_identity=item.candidate_content_identity,
            domain=item.domain,
            evidence_locator_refs=tuple(item.evidence_locator_refs),
            history_entries=tuple(_aemh_entry(entry) for entry in item.history_entries),
            original_candidate_ref=item.original_candidate_ref,
            original_reminder_ref=item.original_reminder_ref,
            project_ref=item.project_ref,
            site_ref=item.site_ref,
            subject_ref=item.subject_ref,
            thread_content_hash=item.thread_content_hash,
            thread_ref=item.thread_ref,
        ) for item in value.threads),
    )


def adapt_aemh_match_history_authority(source: common.AuthorityBundleV02) -> S5AEMHPacket:
    """Build an S5 AE/MH history packet from typed authority only."""
    source = _require_bundle(source, common.AEMH_CONTRACT_ID)
    packet = _public_aemh(source)
    return S5AEMHPacket(
        packet_content_hash=packet.packet_content_hash,
        projection=_aemh_projection(packet.projection),
        receipt=_receipt(packet.receipt),
    )


def build_subject_temporal_packet(source: common.AuthorityBundleV02) -> S5SubjectTemporalPacket:
    return adapt_subject_temporal_authority(source)


def build_aemh_match_history_packet(source: common.AuthorityBundleV02) -> S5AEMHPacket:
    return adapt_aemh_match_history_authority(source)


def build_s5_authority_packet(source: common.AuthorityBundleV02) -> S5SubjectTemporalPacket | S5AEMHPacket:
    if type(source) is not common.AuthorityBundleV02:
        return _require_bundle(source, "")  # raises a stable boundary error
    if source.target_contract == common.SUBJECT_CONTRACT_ID:
        return adapt_subject_temporal_authority(source)
    if source.target_contract == common.AEMH_CONTRACT_ID:
        return adapt_aemh_match_history_authority(source)
    raise S5AuthorityAdapterError("AUTHORITY_TARGET_MISMATCH")


# Short aliases are useful to callers while the explicit names remain the
# source-facing API used by the accepted contract.
adapt_subject_authority = adapt_subject_temporal_authority
adapt_aemh_authority = adapt_aemh_match_history_authority
build_subject_packet = build_subject_temporal_packet
build_aemh_packet = build_aemh_match_history_packet
build_s5_subject_temporal_packet = build_subject_temporal_packet
build_s5_aemh_match_history_packet = build_aemh_match_history_packet
build_s5_subject_temporal_authority = adapt_subject_temporal_authority
build_s5_aemh_match_history_authority = adapt_aemh_match_history_authority


__all__ = [
    "S5AuthorityAdapterError",
    "adapt_subject_temporal_authority", "adapt_aemh_match_history_authority",
    "adapt_subject_authority", "adapt_aemh_authority",
    "build_subject_temporal_packet", "build_aemh_match_history_packet",
    "build_subject_packet", "build_aemh_packet", "build_s5_authority_packet",
    "build_s5_subject_temporal_packet", "build_s5_aemh_match_history_packet",
    "build_s5_subject_temporal_authority", "build_s5_aemh_match_history_authority",
]
