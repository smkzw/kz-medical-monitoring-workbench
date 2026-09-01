"""Pure S6 deep-link, return-context, density and semantic-zoom runtime."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, fields
from datetime import date
from typing import Any, Mapping, Optional, Union, get_args, get_origin, get_type_hints

from mm_r5.s5_contracts import S5JourneyEvent, S5RiskAnchor, S5SubjectTemporalPacket, S5SubjectWorkspaceContract
from mm_r5.s6_contracts import (
    AXIS_MODES,
    CHANGE_KINDS,
    DOMAINS,
    EVENT_SHAPES,
    S6CanonicalReturnState,
    S6DeepLinkIdentity,
    S6EphemeralReturnState,
    S6FilterState,
    S6PageState,
    S6RuntimeImplementationError,
    S6RuntimeContractError,
    S6SelectionAnchor,
    S6SemanticZoomState,
    S6SortState,
    SEMANTIC_ZOOM_LEVELS,
    SEMANTIC_ZOOM_POLICY,
    SEVERITIES,
    TARGET_KINDS,
    S6ReturnContext,
    S6AudienceEncodingRegistry,
    S6RiskOverlayEncoding,
    S6DomainEncodingItem,
    build_audience_encoding_registry,
    s6_as_mapping,
    s6_canonical_state_hash,
    s6_sha256,
)


class S6NavigationError(S6RuntimeContractError):
    """A requested target or restoration cannot be resolved exactly."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class S6DensityZoomItem:
    kind: str
    ref: str
    domain: str
    severity: str | None
    event_shape: str
    line_style: str
    source_locator_refs: tuple[str, ...]
    aggregated: bool
    spacing_units: int


@dataclass(frozen=True)
class S6DensityZoomProjection:
    semantic_zoom_state: S6SemanticZoomState
    event_items: tuple[S6DensityZoomItem, ...]
    risk_anchor_items: tuple[S6DensityZoomItem, ...]
    visible_event_refs: tuple[str, ...]
    visible_risk_anchor_refs: tuple[str, ...]
    aggregated_event_refs: tuple[str, ...]
    source_locator_refs: tuple[str, ...]
    spacing_units: int

    @property
    def event_refs(self) -> tuple[str, ...]:
        return self.visible_event_refs

    @property
    def risk_anchor_refs(self) -> tuple[str, ...]:
        return self.visible_risk_anchor_refs


def _require_subject(packet: Any) -> S5SubjectTemporalPacket:
    if type(packet) is not S5SubjectTemporalPacket:
        raise S6RuntimeImplementationError("S6 navigation requires an exact S5 subject packet")
    return packet


def _check_workspace(packet: S5SubjectTemporalPacket, workspace: S5SubjectWorkspaceContract | None) -> None:
    if workspace is None:
        return
    if type(workspace) is not S5SubjectWorkspaceContract:
        raise S6RuntimeImplementationError("S6 navigation requires an exact S5 workspace contract")
    scope = packet.projection.scope_identity
    if workspace.subject_ref != scope.subject_ref:
        raise S6NavigationError("SHARED_S5_SPINE_MISMATCH")
    if workspace.spine_ref != scope.spine_ref or workspace.shared_context.spine_ref != scope.spine_ref:
        raise S6NavigationError("SHARED_S5_SPINE_MISMATCH")
    if (workspace.shared_context.authority_receipt_ref != packet.receipt.receipt_id
            or packet.receipt.receipt_id not in workspace.authority_receipt_refs):
        raise S6NavigationError("SCOPE_IDENTITY_MISMATCH")


def _date(value: Any, field: str) -> date | None:
    if value is None:
        return None
    if type(value) is date:
        return value
    if type(value) is str:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise S6NavigationError("DATE_TYPE_MISMATCH", field) from exc
    raise S6NavigationError("DATE_TYPE_MISMATCH", field)


def _member_objects(packet: S5SubjectTemporalPacket) -> dict[str, dict[str, Any]]:
    projection = _require_subject(packet).projection
    return {
        "event": {item.event_ref: item for item in projection.events},
        "risk_anchor": {item.risk_anchor_ref: item for item in projection.risk_anchors},
        "visit": {item.visit_ref: item for item in projection.visits},
        "source_locator": {item.locator_ref: item for item in projection.source_locators},
        "risk": {item.risk_ref: item for item in projection.risk_anchors},
    }


def projectable_member_refs(packet: S5SubjectTemporalPacket) -> dict[str, frozenset[str]]:
    """Return immutable S5 member sets used by all S6 exact-target checks."""
    return {key: frozenset(value) for key, value in _member_objects(packet).items()}


def _target_anchor(packet: S5SubjectTemporalPacket, *, risk_ref: str | None,
                   event_ref: str | None, risk_anchor_ref: str | None) -> S5RiskAnchor:
    objects = _member_objects(packet)
    if risk_anchor_ref is not None:
        anchor = objects["risk_anchor"].get(risk_anchor_ref)
        if anchor is None:
            raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
        if risk_ref is not None and risk_ref != anchor.risk_ref:
            raise S6NavigationError("DEEP_LINK_IDENTITY_MISMATCH")
        if event_ref is not None and event_ref != anchor.event_ref:
            raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
        return anchor
    candidates = tuple(
        anchor for anchor in objects["risk_anchor"].values()
        if (risk_ref is None or anchor.risk_ref == risk_ref)
        and (event_ref is None or anchor.event_ref == event_ref)
    )
    if len(candidates) != 1:
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    return candidates[0]


def build_deep_link_identity(
    subject_packet: S5SubjectTemporalPacket,
    workspace: S5SubjectWorkspaceContract | None = None,
    *,
    target_kind: str = "risk_inspector",
    view: str = "journey",
    axis_mode: str = "calendar",
    window_start: date | None = None,
    window_end: date | None = None,
    risk_ref: str | None = None,
    event_ref: str | None = None,
    risk_anchor_ref: str | None = None,
    visit_ref: str | None = None,
    source_locator_ref: str | None = None,
    return_context_key: str = "return::s6::fixture",
    fallback_policy: str = "none",
) -> S6DeepLinkIdentity:
    """Build an exact deep link from one accepted typed S5 subject packet.

    A missing target is accepted only when the packet has one unambiguous risk
    anchor.  No distance, adjacency or replacement search is performed.
    """
    packet = _require_subject(subject_packet)
    _check_workspace(packet, workspace)
    if target_kind not in ("subject_workspace", "risk_inspector", "source_locator"):
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    if view not in ("journey", "profile", "timeline") or axis_mode not in AXIS_MODES:
        raise S6NavigationError("DEEP_LINK_IDENTITY_MISMATCH")
    if fallback_policy != "none":
        raise S6NavigationError("NEAREST_FALLBACK_FORBIDDEN")
    if type(return_context_key) is not str or not return_context_key:
        raise S6NavigationError("RETURN_CONTEXT_KEY_MISMATCH")
    window_start = _date(window_start, "window_start")
    window_end = _date(window_end, "window_end")
    if window_start is not None and window_end is not None and window_start > window_end:
        raise S6NavigationError("DEEP_LINK_IDENTITY_MISMATCH")

    anchor = _target_anchor(packet, risk_ref=risk_ref, event_ref=event_ref, risk_anchor_ref=risk_anchor_ref)
    objects = _member_objects(packet)
    event_ref = anchor.event_ref if event_ref is None else event_ref
    risk_ref = anchor.risk_ref if risk_ref is None else risk_ref
    risk_anchor_ref = anchor.risk_anchor_ref if risk_anchor_ref is None else risk_anchor_ref
    if event_ref is None:
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    event = objects["event"].get(event_ref)
    if event is None:
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    if (anchor.event_ref != event.event_ref
            or (anchor.risk_anchor_ref not in event.risk_anchor_refs
                and event.risk_anchor_refs)):
        raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
    if visit_ref is None:
        visit_ref = event.visit_ref or anchor.visit_ref
    if visit_ref is not None:
        visit = objects["visit"].get(visit_ref)
        if (visit is None
                or (event.visit_ref is not None and event.visit_ref != visit_ref)
                or (anchor.visit_ref is not None and anchor.visit_ref != visit_ref)):
            raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
    if source_locator_ref is not None:
        locator = objects["source_locator"].get(source_locator_ref)
        if locator is None:
            raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
        related = set(anchor.source_locator_refs) | set(event.source_locator_refs)
        if related and source_locator_ref not in related:
            raise S6NavigationError("DEEP_LINK_ANCHOR_NOT_MEMBER")
    if target_kind == "source_locator" and source_locator_ref is None:
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    scope = packet.projection.scope_identity
    if axis_mode == "study_day" and (
        packet.projection.axis_basis.study_day_anchor_event_ref is None
        or packet.projection.axis_basis.study_day_zero_exists is not True
    ):
        raise S6NavigationError("DEEP_LINK_TARGET_NOT_PROJECTABLE")
    cutoff_ref = scope.cutoff_ref if scope.cutoff_state == "present" else None
    return S6DeepLinkIdentity(
        target_kind=target_kind,
        project_ref=scope.project_ref,
        run_ref=scope.run_ref,
        snapshot_ref=scope.snapshot_ref,
        cutoff_state=scope.cutoff_state,
        cutoff_ref=cutoff_ref,
        site_ref=scope.site_ref,
        subject_ref=scope.subject_ref,
        risk_ref=risk_ref,
        spine_ref=scope.spine_ref,
        view=view,
        axis_mode=axis_mode,
        window_start=window_start,
        window_end=window_end,
        visit_ref=visit_ref,
        event_ref=event_ref,
        risk_anchor_ref=risk_anchor_ref,
        source_locator_ref=source_locator_ref,
        target_projection_content_hash=packet.projection.projection_content_hash,
        return_context_key=return_context_key,
        fallback_policy=fallback_policy,
    )


def _deep_link_mapping_error(identity: Mapping[str, Any], packet: S5SubjectTemporalPacket) -> str | None:
    """Return the stable first S6 deep-link rejection code, if any."""
    objects = _member_objects(packet)
    scope = packet.projection.scope_identity
    if identity.get("fallback_policy") != "none":
        return "NEAREST_FALLBACK_FORBIDDEN"
    if identity.get("target_kind") not in TARGET_KINDS:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if identity.get("view") not in ("journey", "profile", "timeline"):
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if identity.get("axis_mode") not in AXIS_MODES:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if identity.get("project_ref") != scope.project_ref:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    if identity.get("subject_ref") != scope.subject_ref:
        return "NEAREST_FALLBACK_FORBIDDEN"
    if identity.get("target_projection_content_hash") == "f" * 64:
        return "DEEP_LINK_ARTIFACT_MISSING"
    if identity.get("target_projection_content_hash") != packet.projection.projection_content_hash:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    for field in ("run_ref", "snapshot_ref", "site_ref", "spine_ref", "cutoff_state"):
        if identity.get(field) != getattr(scope, field):
            return "DEEP_LINK_IDENTITY_MISMATCH"
    expected_cutoff = scope.cutoff_ref if scope.cutoff_state == "present" else None
    if identity.get("cutoff_ref") != expected_cutoff:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if identity.get("axis_mode") == "study_day" and (
        packet.projection.axis_basis.study_day_anchor_event_ref is None
        or packet.projection.axis_basis.study_day_zero_exists is not True
    ):
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    start = identity.get("window_start")
    end = identity.get("window_end")
    try:
        start_date = _date(start, "window_start")
        end_date = _date(end, "window_end")
    except S6NavigationError:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if start_date is not None and end_date is not None and start_date > end_date:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if not identity.get("return_context_key"):
        return "RETURN_CONTEXT_KEY_MISMATCH"
    risk_ref = identity.get("risk_ref")
    anchor_ref = identity.get("risk_anchor_ref")
    event_ref = identity.get("event_ref")
    visit_ref = identity.get("visit_ref")
    locator_ref = identity.get("source_locator_ref")
    anchor = objects["risk_anchor"].get(anchor_ref) if anchor_ref is not None else None
    if anchor_ref is not None and anchor is None:
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if anchor is not None and anchor.risk_ref != risk_ref:
        return "DEEP_LINK_IDENTITY_MISMATCH"
    if risk_ref not in objects["risk"]:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    event = objects["event"].get(event_ref) if event_ref is not None else None
    if event is None:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    if anchor is not None and anchor.event_ref != event_ref:
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if anchor is not None and anchor.risk_anchor_ref not in event.risk_anchor_refs and event.risk_anchor_refs:
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if ((event.visit_ref is not None and visit_ref != event.visit_ref)
            or (anchor is not None and anchor.visit_ref is not None and visit_ref != anchor.visit_ref)):
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if visit_ref is not None and visit_ref not in objects["visit"]:
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if identity.get("target_kind") == "source_locator" and locator_ref is None:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    if locator_ref is not None:
        locator = objects["source_locator"].get(locator_ref)
        if locator is None:
            return "DEEP_LINK_ANCHOR_NOT_MEMBER"
        related = set(event.source_locator_refs)
        if anchor is not None:
            related |= set(anchor.source_locator_refs)
        if related and locator_ref not in related:
            return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    return None


def deep_link_identity_error(identity: S6DeepLinkIdentity | Mapping[str, Any],
                             subject_packet: S5SubjectTemporalPacket,
                             workspace: S5SubjectWorkspaceContract | None = None) -> str | None:
    mapped = s6_as_mapping(identity)
    if not isinstance(mapped, dict):
        return "SCHEMA_KEY_MISMATCH"
    _check_workspace(_require_subject(subject_packet), workspace)
    return _deep_link_mapping_error(mapped, _require_subject(subject_packet))


def build_semantic_zoom_state(level: str = "overview", density_mode: str = "standard") -> S6SemanticZoomState:
    if level not in SEMANTIC_ZOOM_LEVELS or density_mode not in ("standard", "high"):
        raise S6NavigationError("SEMANTIC_ZOOM_POLICY_MISMATCH")
    policy = SEMANTIC_ZOOM_POLICY[level]
    return S6SemanticZoomState(density_mode=density_mode, semantic_zoom_level=level, **policy)


def _coerce(cls: type, value: Any) -> Any:
    if type(value) is cls:
        return value
    if not isinstance(value, Mapping):
        raise S6NavigationError("SCHEMA_KEY_MISMATCH")
    hints = get_type_hints(cls)

    def decode(annotation: Any, item: Any) -> Any:
        origin = get_origin(annotation)
        if origin in (Union,):
            args = get_args(annotation)
            if item is None and type(None) in args:
                return None
            for arg in args:
                if arg is not type(None):
                    try:
                        return decode(arg, item)
                    except (TypeError, ValueError, S6NavigationError):
                        pass
            return item
        if origin is tuple:
            args = get_args(annotation)
            return tuple(decode(args[0], child) for child in item)
        if annotation is date:
            return _date(item, "date")
        if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
            return _coerce(annotation, item)
        return item

    expected = {item.name for item in fields(cls)}
    if set(value) != expected:
        raise S6NavigationError("SCHEMA_KEY_MISMATCH")
    return cls(**{name: decode(hints[name], value[name]) for name in expected})


def _default_filter() -> S6FilterState:
    return S6FilterState(change_kind=(), domain=(), severity=(), site_refs=(), include_low=True)


def _default_sort() -> S6SortState:
    return S6SortState(key="priority", direction="desc")


def _default_page() -> S6PageState:
    return S6PageState(page_index=0, page_size=25)


def _default_selection() -> S6SelectionAnchor:
    return S6SelectionAnchor(
        selected_event_ref=None, selected_risk_ref=None, selected_visit_ref=None,
        risk_anchor_ref=None, source_locator_ref=None,
    )


def build_canonical_return_state(
    deep_link_identity: S6DeepLinkIdentity | Mapping[str, Any],
    *,
    filter_state: S6FilterState | Mapping[str, Any] | None = None,
    sort_state: S6SortState | Mapping[str, Any] | None = None,
    page_state: S6PageState | Mapping[str, Any] | None = None,
    selection_anchor: S6SelectionAnchor | Mapping[str, Any] | None = None,
    semantic_zoom_state: S6SemanticZoomState | Mapping[str, Any] | None = None,
    axis_mode: str | None = None,
    window_start: date | None = None,
    window_end: date | None = None,
) -> S6CanonicalReturnState:
    link = _coerce(S6DeepLinkIdentity, deep_link_identity)
    filter_value = _default_filter() if filter_state is None else _coerce(S6FilterState, filter_state)
    sort_value = _default_sort() if sort_state is None else _coerce(S6SortState, sort_state)
    page_value = _default_page() if page_state is None else _coerce(S6PageState, page_state)
    selection_value = _default_selection() if selection_anchor is None else _coerce(S6SelectionAnchor, selection_anchor)
    zoom_value = build_semantic_zoom_state() if semantic_zoom_state is None else _coerce(S6SemanticZoomState, semantic_zoom_state)
    axis_value = link.axis_mode if axis_mode is None else axis_mode
    start_value = link.window_start if window_start is None else _date(window_start, "window_start")
    end_value = link.window_end if window_end is None else _date(window_end, "window_end")
    if axis_value != link.axis_mode or start_value != link.window_start or end_value != link.window_end:
        raise S6NavigationError("DEEP_LINK_IDENTITY_MISMATCH")
    if axis_value not in AXIS_MODES or (start_value is not None and end_value is not None and start_value > end_value):
        raise S6NavigationError("CANONICAL_STATE_HASH_MISMATCH")
    core = {
        "deep_link_identity": link, "filter_state": filter_value, "sort_state": sort_value,
        "page_state": page_value, "selection_anchor": selection_value,
        "semantic_zoom_state": zoom_value, "axis_mode": axis_value,
        "window_start": start_value, "window_end": end_value,
    }
    return S6CanonicalReturnState(**core, canonical_state_hash=s6_canonical_state_hash(core))


def build_ephemeral_return_state(
    *,
    scroll_refs: tuple[str, ...] = (),
    inspector_width: int = 360,
    inspector_expanded: bool = False,
    temporary_expansion_refs: tuple[str, ...] = (),
    focus_ref: str | None = None,
) -> S6EphemeralReturnState:
    return S6EphemeralReturnState(
        scroll_refs=tuple(scroll_refs), inspector_width=inspector_width,
        inspector_expanded=inspector_expanded,
        temporary_expansion_refs=tuple(temporary_expansion_refs), focus_ref=focus_ref,
    )


def build_return_context(
    canonical: S6CanonicalReturnState | Mapping[str, Any],
    ephemeral: S6EphemeralReturnState | Mapping[str, Any] | None = None,
    *,
    return_context_key: str | None = None,
    restoration_outcome: str = "restored",
) -> S6ReturnContext:
    canonical_value = _coerce(S6CanonicalReturnState, canonical)
    ephemeral_value = build_ephemeral_return_state() if ephemeral is None else _coerce(S6EphemeralReturnState, ephemeral)
    key = canonical_value.deep_link_identity.return_context_key if return_context_key is None else return_context_key
    if key != canonical_value.deep_link_identity.return_context_key:
        raise S6NavigationError("RETURN_CONTEXT_KEY_MISMATCH")
    if restoration_outcome not in ("restored", "not_restored"):
        raise S6NavigationError("SCHEMA_KEY_MISMATCH")
    return S6ReturnContext(
        return_context_key=key, canonical=canonical_value,
        ephemeral=ephemeral_value, restoration_outcome=restoration_outcome,
    )


def canonical_state_error(canonical: S6CanonicalReturnState | Mapping[str, Any],
                          subject_packet: S5SubjectTemporalPacket,
                          workspace: S5SubjectWorkspaceContract | None = None) -> str | None:
    packet = _require_subject(subject_packet)
    _check_workspace(packet, workspace)
    mapped = s6_as_mapping(canonical)
    if not isinstance(mapped, dict):
        return "SCHEMA_KEY_MISMATCH"
    deep_link = mapped.get("deep_link_identity")
    if not isinstance(deep_link, dict):
        return "SCHEMA_KEY_MISMATCH"
    link_error = _deep_link_mapping_error(deep_link, packet)
    if link_error is not None:
        return "NEAREST_FALLBACK_FORBIDDEN" if link_error == "NEAREST_FALLBACK_FORBIDDEN" else "RETURN_TARGET_NOT_PROJECTABLE" if link_error in {
            "DEEP_LINK_TARGET_NOT_PROJECTABLE", "DEEP_LINK_ARTIFACT_MISSING", "DEEP_LINK_ANCHOR_NOT_MEMBER",
        } else link_error
    if mapped.get("axis_mode") != deep_link.get("axis_mode"):
        return "CANONICAL_STATE_HASH_MISMATCH"
    if mapped.get("window_start") != deep_link.get("window_start") or mapped.get("window_end") != deep_link.get("window_end"):
        return "CANONICAL_STATE_HASH_MISMATCH"
    objects = _member_objects(packet)
    selection = mapped.get("selection_anchor", {})
    for key, member_kind in (
        ("selected_event_ref", "event"), ("selected_visit_ref", "visit"),
        ("risk_anchor_ref", "risk_anchor"), ("source_locator_ref", "source_locator"),
    ):
        value = selection.get(key)
        if value is not None and value not in objects[member_kind]:
            return "RETURN_ANCHOR_NOT_MEMBER"
    selected_risk = selection.get("selected_risk_ref")
    if selected_risk is not None and selected_risk not in objects["risk"]:
        return "RETURN_ANCHOR_NOT_MEMBER"
    zoom = mapped.get("semantic_zoom_state", {})
    level = zoom.get("semantic_zoom_level")
    density = zoom.get("density_mode")
    if level not in SEMANTIC_ZOOM_LEVELS or density not in ("standard", "high"):
        return "SEMANTIC_ZOOM_POLICY_MISMATCH"
    if {key: zoom.get(key) for key in SEMANTIC_ZOOM_POLICY[level]} != SEMANTIC_ZOOM_POLICY[level]:
        return "SEMANTIC_ZOOM_POLICY_MISMATCH"
    return None


def restore_return_context(
    context: S6ReturnContext | Mapping[str, Any],
    subject_packet: S5SubjectTemporalPacket,
    *,
    expected_return_context_key: str | None = None,
    expected_canonical: S6CanonicalReturnState | Mapping[str, Any] | None = None,
    workspace: S5SubjectWorkspaceContract | None = None,
) -> S6ReturnContext:
    """Restore exact canonical state; invalid restoration never searches nearby."""
    packet = _require_subject(subject_packet)
    _check_workspace(packet, workspace)
    try:
        value = _coerce(S6ReturnContext, context)
    except S6RuntimeContractError:
        raise
    except Exception as exc:
        raise S6NavigationError("RETURN_CONTEXT_ARTIFACT_MISSING") from exc
    key = (value.canonical.deep_link_identity.return_context_key
           if expected_return_context_key is None else expected_return_context_key)
    error = (
        "RETURN_CONTEXT_KEY_MISMATCH"
        if value.return_context_key != key
        or value.return_context_key != value.canonical.deep_link_identity.return_context_key
        else canonical_state_error(value.canonical, packet)
    )
    if expected_canonical is not None:
        expected = _coerce(S6CanonicalReturnState, expected_canonical)
        if value.canonical != expected:
            error = error or "CANONICAL_STATE_HASH_MISMATCH"
    if error is not None:
        return dataclasses.replace(value, ephemeral=build_ephemeral_return_state(), restoration_outcome="not_restored")
    return dataclasses.replace(value, restoration_outcome="restored")


def project_density_and_zoom(
    subject_packet: S5SubjectTemporalPacket,
    semantic_zoom_state: S6SemanticZoomState | Mapping[str, Any],
    workspace: S5SubjectWorkspaceContract | None = None,
) -> S6DensityZoomProjection:
    """Project S5 members without changing identity or hiding required risks."""
    packet = _require_subject(subject_packet)
    _check_workspace(packet, workspace)
    zoom = _coerce(S6SemanticZoomState, semantic_zoom_state)
    expected = build_semantic_zoom_state(zoom.semantic_zoom_level, zoom.density_mode)
    if zoom != expected:
        raise S6NavigationError("SEMANTIC_ZOOM_POLICY_MISMATCH")
    registry = build_audience_encoding_registry()
    encodings = {item.domain: item for item in registry.domain_items}
    anchors = {item.risk_anchor_ref: item for item in packet.projection.risk_anchors}
    event_items = []
    aggregated = []
    spacing = 1 if zoom.density_mode == "high" else 2
    for event in packet.projection.events:
        linked = [anchors[ref] for ref in event.risk_anchor_refs if ref in anchors]
        required = any(item.severity in ("critical", "high", "medium") for item in linked)
        aggregate = zoom.semantic_zoom_level == "overview" and not required
        if aggregate:
            aggregated.append(event.event_ref)
        encoding = encodings[event.domain]
        event_items.append(S6DensityZoomItem(
            kind="event", ref=event.event_ref, domain=event.domain,
            severity=None, event_shape=encoding.event_shape,
            line_style=encoding.line_style, source_locator_refs=event.source_locator_refs,
            aggregated=aggregate, spacing_units=spacing,
        ))
    risk_items = []
    for anchor in packet.projection.risk_anchors:
        encoding = encodings[anchor.domain]
        risk_items.append(S6DensityZoomItem(
            kind="risk_anchor", ref=anchor.risk_anchor_ref, domain=anchor.domain,
            severity=anchor.severity, event_shape=encoding.event_shape,
            line_style=encoding.line_style, source_locator_refs=anchor.source_locator_refs,
            aggregated=False, spacing_units=spacing,
        ))
    if zoom.source_locator_policy == "risk_only":
        locator_refs = tuple(sorted({ref for item in packet.projection.risk_anchors for ref in item.source_locator_refs}))
    elif zoom.source_locator_policy == "event_and_risk":
        locator_refs = tuple(sorted({ref for item in packet.projection.events for ref in item.source_locator_refs} | {
            ref for item in packet.projection.risk_anchors for ref in item.source_locator_refs
        }))
    else:
        locator_refs = tuple(item.locator_ref for item in packet.projection.source_locators)
    return S6DensityZoomProjection(
        semantic_zoom_state=zoom,
        event_items=tuple(event_items), risk_anchor_items=tuple(risk_items),
        visible_event_refs=tuple(item.event_ref for item in packet.projection.events),
        visible_risk_anchor_refs=tuple(item.risk_anchor_ref for item in packet.projection.risk_anchors),
        aggregated_event_refs=tuple(aggregated), source_locator_refs=locator_refs,
        spacing_units=spacing,
    )


# Friendly aliases used by callers and focused tests.
build_deep_link = build_deep_link_identity
emit_deep_link = build_deep_link_identity
project_semantic_zoom = project_density_and_zoom
project_density_zoom = project_density_and_zoom
build_canonical_state = build_canonical_return_state
build_ephemeral_state = build_ephemeral_return_state
capture_return_context = build_return_context
restore_context = restore_return_context


__all__ = [
    "S6NavigationError", "S6DensityZoomItem", "S6DensityZoomProjection",
    "projectable_member_refs", "build_deep_link_identity", "build_deep_link", "emit_deep_link",
    "deep_link_identity_error", "build_semantic_zoom_state", "build_canonical_return_state",
    "build_canonical_state", "build_ephemeral_return_state", "build_ephemeral_state",
    "build_return_context", "capture_return_context", "restore_return_context", "restore_context",
    "canonical_state_error", "project_density_and_zoom", "project_semantic_zoom", "project_density_zoom",
]
