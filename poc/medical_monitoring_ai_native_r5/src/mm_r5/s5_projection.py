"""Renderer-neutral S5 workspace projection over typed public packets."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from mm_r5 import public_authority_common as common
from mm_r5.s5_authority_adapter import (
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
)
from mm_r5.s5_contracts import (
    AXIS_MODES,
    S5AEMHPacket,
    S5AuthorityReceipt,
    S5SubjectTemporalPacket,
    S5SubjectWorkspaceContract,
    S5SelectionAnchor,
    S5SharedTemporalContext,
    S5ViewBinding,
    build_audience_encoding_registry,
    build_audience_lexicon,
    s5_context_ref,
    s5_navigation_content_hash,
    s5_sha256,
)


class S5ProjectionError(ValueError):
    """A typed packet cannot be projected into a shared S5 workspace."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


def _require_subject(packet: Any) -> S5SubjectTemporalPacket:
    if type(packet) is not S5SubjectTemporalPacket:
        raise S5ProjectionError("SUBJECT_PACKET_TYPE_MISMATCH")
    return packet


def _require_aemh(packet: Any) -> S5AEMHPacket:
    if packet is None:
        raise S5ProjectionError("AEMH_PACKET_REQUIRED")
    if type(packet) is not S5AEMHPacket:
        raise S5ProjectionError("AEMH_PACKET_TYPE_MISMATCH")
    return packet


def _scope_matches(subject: S5SubjectTemporalPacket, aemh: S5AEMHPacket) -> None:
    left = subject.projection.scope_identity
    right = aemh.projection.scope_identity
    if left != right:
        if left.spine_ref != right.spine_ref:
            raise S5ProjectionError("SHARED_SPINE_MISMATCH")
        raise S5ProjectionError("SCOPE_IDENTITY_MISMATCH")


def _member_refs(packet: S5SubjectTemporalPacket) -> dict[str, set[str]]:
    projection = packet.projection
    return {
        "event": {item.event_ref for item in projection.events},
        "risk_anchor": {item.risk_anchor_ref for item in projection.risk_anchors},
        "visit": {item.visit_ref for item in projection.visits},
        "source_locator": {item.locator_ref for item in projection.source_locators},
    }


def build_selection_anchor(
    packet: S5SubjectTemporalPacket,
    *,
    anchor_kind: str = "none",
    anchor_ref: Optional[str] = None,
    source_locator_ref: Optional[str] = None,
) -> S5SelectionAnchor:
    """Create a selection anchor only when its reference is a packet member."""
    _require_subject(packet)
    if anchor_kind not in ("none", "event", "risk_anchor", "visit", "source_locator"):
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    if anchor_kind == "none":
        if anchor_ref is not None or source_locator_ref is not None:
            raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    elif anchor_ref not in _member_refs(packet)[anchor_kind]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    if source_locator_ref is not None and source_locator_ref not in _member_refs(packet)["source_locator"]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    return _sealed_selection_anchor(anchor_kind, anchor_ref, source_locator_ref)


def _sealed_selection_anchor(
    anchor_kind: str, anchor_ref: Optional[str], source_locator_ref: Optional[str]
) -> S5SelectionAnchor:
    # The constructor verifies the navigation recipe.  Build the content hash
    # from the exact non-hash fields without a temporary invalid object.
    content = s5_sha256({
        "anchor_kind": anchor_kind,
        "anchor_ref": anchor_ref,
        "source_locator_ref": source_locator_ref,
    })
    return S5SelectionAnchor(
        anchor_kind=anchor_kind,
        anchor_ref=anchor_ref,
        content_hash=content,
        source_locator_ref=source_locator_ref,
    )


def _date(value: Optional[date], field: str) -> Optional[date]:
    if value is not None and type(value) is not date:
        raise S5ProjectionError("DATE_TYPE_MISMATCH", field)
    return value


def _make_context(
    subject: S5SubjectTemporalPacket,
    *,
    axis_mode: str,
    window_start: Optional[date],
    window_end: Optional[date],
    selection_anchor: S5SelectionAnchor,
    selected_event_ref: Optional[str],
    selected_risk_anchor_ref: Optional[str],
    selected_visit_ref: Optional[str],
) -> S5SharedTemporalContext:
    if axis_mode not in AXIS_MODES:
        raise S5ProjectionError("AXIS_MODE_MISMATCH")
    if axis_mode == "study_day" and (
        subject.projection.axis_basis.study_day_anchor_event_ref is None
        or subject.projection.axis_basis.study_day_zero_exists is None
    ):
        raise S5ProjectionError("STUDY_DAY_ANCHOR_MISSING")
    window_start = _date(window_start, "window_start")
    window_end = _date(window_end, "window_end")
    if window_start is not None and window_end is not None and window_start > window_end:
        raise S5ProjectionError("SHARED_WINDOW_MISMATCH")
    refs = _member_refs(subject)
    if selected_event_ref is not None and selected_event_ref not in refs["event"]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    if selected_risk_anchor_ref is not None and selected_risk_anchor_ref not in refs["risk_anchor"]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    if selected_visit_ref is not None and selected_visit_ref not in refs["visit"]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    context_ref = s5_context_ref(
        subject.receipt.receipt_id,
        subject.projection.scope_identity.spine_ref,
        axis_mode,
        window_start,
        window_end,
        selection_anchor,
        selected_event_ref,
        selected_risk_anchor_ref,
        selected_visit_ref,
    )
    context_fields = {
        "authority_receipt_ref": subject.receipt.receipt_id,
        "axis_mode": axis_mode,
        "content_hash": "0" * 64,
        "context_ref": context_ref,
        "selected_event_ref": selected_event_ref,
        "selected_risk_anchor_ref": selected_risk_anchor_ref,
        "selected_visit_ref": selected_visit_ref,
        "selection_anchor": selection_anchor,
        "spine_ref": subject.projection.scope_identity.spine_ref,
        "window_end": window_end,
        "window_start": window_start,
    }
    return S5SharedTemporalContext(
        authority_receipt_ref=context_fields["authority_receipt_ref"],
        axis_mode=context_fields["axis_mode"],
        content_hash=s5_navigation_content_hash(context_fields),
        context_ref=context_fields["context_ref"],
        selected_event_ref=context_fields["selected_event_ref"],
        selected_risk_anchor_ref=context_fields["selected_risk_anchor_ref"],
        selected_visit_ref=context_fields["selected_visit_ref"],
        selection_anchor=context_fields["selection_anchor"],
        spine_ref=context_fields["spine_ref"],
        window_end=context_fields["window_end"],
        window_start=context_fields["window_start"],
    )


def project_subject_workspace(
    subject_packet: S5SubjectTemporalPacket,
    aemh_packet: Optional[S5AEMHPacket] = None,
    *,
    axis_mode: str = "calendar",
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    selection_anchor: Optional[S5SelectionAnchor] = None,
    selected_event_ref: Optional[str] = None,
    selected_risk_anchor_ref: Optional[str] = None,
    selected_visit_ref: Optional[str] = None,
) -> S5SubjectWorkspaceContract:
    """Bind journey/profile/timeline to one subject authority spine."""
    subject_packet = _require_subject(subject_packet)
    if aemh_packet is not None:
        aemh_packet = _require_aemh(aemh_packet)
        _scope_matches(subject_packet, aemh_packet)
    if selection_anchor is None:
        selection_anchor = _sealed_selection_anchor("none", None, None)
    if type(selection_anchor) is not S5SelectionAnchor:
        raise S5ProjectionError("SELECTION_ANCHOR_TYPE_MISMATCH")
    refs = _member_refs(subject_packet)
    if selection_anchor.anchor_kind != "none":
        if selection_anchor.anchor_ref not in refs[selection_anchor.anchor_kind]:
            raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    if selection_anchor.source_locator_ref is not None and selection_anchor.source_locator_ref not in refs["source_locator"]:
        raise S5ProjectionError("SELECTION_ANCHOR_NOT_MEMBER")
    context = _make_context(
        subject_packet,
        axis_mode=axis_mode,
        window_start=window_start,
        window_end=window_end,
        selection_anchor=selection_anchor,
        selected_event_ref=selected_event_ref,
        selected_risk_anchor_ref=selected_risk_anchor_ref,
        selected_visit_ref=selected_visit_ref,
    )
    receipts = [subject_packet.receipt.receipt_id]
    if aemh_packet is not None:
        receipts.append(aemh_packet.receipt.receipt_id)
    receipts_tuple = tuple(receipts)
    bindings = []
    for view in ("journey", "profile", "timeline"):
        binding_fields = {
            "anchor_ref": selection_anchor.anchor_ref,
            "authority_projection_id": subject_packet.projection.projection_id,
            "content_hash": "0" * 64,
            "shared_context_ref": context.context_ref,
            "spine_ref": context.spine_ref,
            "view": view,
        }
        bindings.append(S5ViewBinding(
            anchor_ref=binding_fields["anchor_ref"],
            authority_projection_id=binding_fields["authority_projection_id"],
            content_hash=s5_navigation_content_hash(binding_fields),
            shared_context_ref=binding_fields["shared_context_ref"],
            spine_ref=binding_fields["spine_ref"],
            view=binding_fields["view"],
        ))
    workspace_fields = {
        "authority_receipt_refs": receipts_tuple,
        "content_hash": "0" * 64,
        "shared_context": context,
        "spine_ref": context.spine_ref,
        "subject_ref": subject_packet.projection.scope_identity.subject_ref,
        "view_bindings": tuple(bindings),
    }
    return S5SubjectWorkspaceContract(
        authority_receipt_refs=workspace_fields["authority_receipt_refs"],
        content_hash=s5_sha256({
            "authority_receipt_refs": workspace_fields["authority_receipt_refs"],
            "shared_context": workspace_fields["shared_context"],
            "spine_ref": workspace_fields["spine_ref"],
            "subject_ref": workspace_fields["subject_ref"],
            "view_bindings": sorted(workspace_fields["view_bindings"], key=lambda item: item.view),
        }),
        shared_context=workspace_fields["shared_context"],
        spine_ref=workspace_fields["spine_ref"],
        subject_ref=workspace_fields["subject_ref"],
        view_bindings=workspace_fields["view_bindings"],
    )


def build_subject_workspace(
    subject_source: common.AuthorityBundleV02,
    aemh_source: common.AuthorityBundleV02 | None = None,
    **kwargs: Any,
) -> S5SubjectWorkspaceContract:
    subject = adapt_subject_temporal_authority(subject_source)
    aemh_packet = adapt_aemh_match_history_authority(aemh_source) if aemh_source is not None else None
    return project_subject_workspace(subject, aemh_packet, **kwargs)


def project_subject_temporal(packet: S5SubjectTemporalPacket) -> S5SubjectTemporalPacket:
    return _require_subject(packet)


def project_aemh_history(packet: S5AEMHPacket) -> S5AEMHPacket:
    return _require_aemh(packet)


build_s5_subject_workspace = build_subject_workspace
project_workspace = project_subject_workspace


__all__ = [
    "S5ProjectionError", "build_selection_anchor", "project_subject_workspace",
    "build_subject_workspace", "project_subject_temporal", "project_aemh_history",
    "build_s5_subject_workspace", "project_workspace",
    "build_audience_encoding_registry", "build_audience_lexicon",
]
