"""S6 keyboard and non-colour audience encodings."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Mapping

from mm_r5.s5_contracts import S5JourneyEvent, S5RiskAnchor
from mm_r5.s6_contracts import (
    DOMAIN_ENCODING,
    DOMAIN_SUBTYPE_MATRIX,
    DOMAINS,
    EVENT_FORBIDDEN_SHAPES,
    FORBIDDEN_AUDIENCE_TERMS,
    KEYBOARD_SCOPES,
    RISK_OVERLAY_SHAPE,
    RISK_OVERLAY_TEXT_PATTERN,
    SEMANTIC_ZOOM_LEVELS,
    SEVERITY_ZH,
    S6AudienceEncodingRegistry,
    S6CanonicalReturnState,
    S6EphemeralReturnState,
    S6KeyboardBinding,
    S6KeyboardContract,
    S6RuntimeContractError,
    S6RuntimeImplementationError,
    S6SemanticZoomState,
    build_audience_encoding_registry,
)
from mm_r5.s6_navigation import build_ephemeral_return_state, build_semantic_zoom_state


class S6AccessibilityError(S6RuntimeContractError):
    """A keyboard or audience encoding request is outside the closed set."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class S6KeyboardResult:
    key: str
    scope: str
    action: str
    prevent_default: bool
    medical_state_mutation: bool
    canonical: S6CanonicalReturnState
    ephemeral: S6EphemeralReturnState
    changed: bool


@dataclass(frozen=True)
class S6EventEncoding:
    domain: str
    subtype: str
    short_label_zh: str
    event_shape: str
    line_style: str
    colour_is_auxiliary_only: bool = True


@dataclass(frozen=True)
class S6RiskEncoding:
    domain: str
    severity: str
    short_label_zh: str
    severity_zh: str
    shape: str
    outer_ring: bool
    text: str
    colour_only: bool

    @property
    def colour_is_auxiliary_only(self) -> bool:
        return not self.colour_only


def build_keyboard_contract() -> S6KeyboardContract:
    """Build the frozen 16-binding keyboard contract."""
    rows = (
        ("Tab", "focus_next_region", "global", False),
        ("Shift+Tab", "focus_previous_region", "global", False),
        ("Enter", "activate_focused_target", "global", True),
        ("Space", "toggle_focused_control", "global", True),
        ("Escape", "close_ephemeral_surface", "global", True),
        ("ArrowUp", "move_previous", "risk_list", True),
        ("ArrowDown", "move_next", "risk_list", True),
        ("ArrowUp", "move_previous", "center_map", True),
        ("ArrowDown", "move_next", "center_map", True),
        ("ArrowLeft", "move_previous", "temporal_spine", True),
        ("ArrowRight", "move_next", "temporal_spine", True),
        ("Home", "focus_first", "workspace", True),
        ("End", "focus_last", "workspace", True),
        ("+", "semantic_zoom_in", "temporal_spine", True),
        ("-", "semantic_zoom_out", "temporal_spine", True),
        ("0", "semantic_zoom_reset", "temporal_spine", True),
    )
    bindings = tuple(S6KeyboardBinding(
        key=key, action=action, scope=scope, prevent_default=prevent_default,
        medical_state_mutation=False,
    ) for key, action, scope, prevent_default in rows)
    return S6KeyboardContract(
        region_order=("risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"),
        bindings=bindings,
        focus_policy="one visible roving focus target per region; Tab crosses regions in region_order; hidden or non-projectable targets are not focusable",
        selection_policy="activation selects only a verified projectable target and preserves canonical identity; no key creates, edits, closes or regrades medical state",
    )


def keyboard_binding(key: str, scope: str = "global") -> S6KeyboardBinding:
    if scope not in KEYBOARD_SCOPES:
        raise S6AccessibilityError("KEYBOARD_BINDING_NOT_FOUND")
    contract = build_keyboard_contract()
    for binding in contract.bindings:
        if binding.key == key and binding.scope == scope:
            return binding
    for binding in contract.bindings:
        if binding.key == key and binding.scope == "global":
            return binding
    raise S6AccessibilityError("KEYBOARD_BINDING_NOT_FOUND")


def _reseal_canonical(canonical: S6CanonicalReturnState, zoom: S6SemanticZoomState) -> S6CanonicalReturnState:
    from mm_r5.s6_contracts import s6_canonical_state_hash

    core = {field.name: getattr(canonical, field.name) for field in dataclasses.fields(canonical)
            if field.name != "canonical_state_hash"}
    core["semantic_zoom_state"] = zoom
    return S6CanonicalReturnState(**core, canonical_state_hash=s6_canonical_state_hash(core))


def _move_focus(current: str | None, choices: tuple[str, ...], forward: bool) -> str | None:
    if not choices:
        return None
    if current not in choices:
        return choices[0] if forward else choices[-1]
    index = choices.index(current)
    return choices[(index + (1 if forward else -1)) % len(choices)]


def dispatch_keyboard(
    canonical: S6CanonicalReturnState,
    ephemeral: S6EphemeralReturnState,
    key: str,
    scope: str = "global",
    *,
    focus_refs: tuple[str, ...] = (),
) -> S6KeyboardResult:
    """Apply a keyboard view action immutably; never mutate medical state."""
    if type(canonical) is not S6CanonicalReturnState or type(ephemeral) is not S6EphemeralReturnState:
        raise S6RuntimeImplementationError("keyboard dispatch requires typed S6 return state")
    binding = keyboard_binding(key, scope)
    next_canonical = canonical
    next_ephemeral = ephemeral
    choices = tuple(focus_refs) or build_keyboard_contract().region_order
    if binding.action == "focus_next_region":
        next_ephemeral = dataclasses.replace(ephemeral, focus_ref=_move_focus(ephemeral.focus_ref, choices, True))
    elif binding.action == "focus_previous_region":
        next_ephemeral = dataclasses.replace(ephemeral, focus_ref=_move_focus(ephemeral.focus_ref, choices, False))
    elif binding.action in {"move_previous", "move_next"}:
        next_ephemeral = dataclasses.replace(
            ephemeral, focus_ref=_move_focus(ephemeral.focus_ref, choices, binding.action == "move_next")
        )
    elif binding.action == "focus_first":
        next_ephemeral = dataclasses.replace(ephemeral, focus_ref=choices[0] if choices else None)
    elif binding.action == "focus_last":
        next_ephemeral = dataclasses.replace(ephemeral, focus_ref=choices[-1] if choices else None)
    elif binding.action == "close_ephemeral_surface":
        next_ephemeral = build_ephemeral_return_state()
    elif binding.action == "semantic_zoom_in":
        level = SEMANTIC_ZOOM_LEVELS[min(SEMANTIC_ZOOM_LEVELS.index(canonical.semantic_zoom_state.semantic_zoom_level) + 1, 2)]
        next_canonical = _reseal_canonical(canonical, build_semantic_zoom_state(level, canonical.semantic_zoom_state.density_mode))
    elif binding.action == "semantic_zoom_out":
        level = SEMANTIC_ZOOM_LEVELS[max(SEMANTIC_ZOOM_LEVELS.index(canonical.semantic_zoom_state.semantic_zoom_level) - 1, 0)]
        next_canonical = _reseal_canonical(canonical, build_semantic_zoom_state(level, canonical.semantic_zoom_state.density_mode))
    elif binding.action == "semantic_zoom_reset":
        next_canonical = _reseal_canonical(canonical, build_semantic_zoom_state("overview", canonical.semantic_zoom_state.density_mode))
    # Enter/Space intentionally leave state unchanged until a caller supplies
    # a separately verified projectable target.
    return S6KeyboardResult(
        key=key, scope=scope, action=binding.action,
        prevent_default=binding.prevent_default,
        medical_state_mutation=binding.medical_state_mutation,
        canonical=next_canonical, ephemeral=next_ephemeral,
        changed=(next_canonical != canonical or next_ephemeral != ephemeral),
    )


def encode_event(event_or_domain: S5JourneyEvent | Mapping[str, Any] | str,
                 subtype: str | None = None) -> S6EventEncoding:
    if isinstance(event_or_domain, S5JourneyEvent):
        domain, subtype_value = event_or_domain.domain, event_or_domain.subtype
    elif isinstance(event_or_domain, Mapping):
        domain, subtype_value = event_or_domain.get("domain"), event_or_domain.get("subtype")
    else:
        domain, subtype_value = event_or_domain, subtype
    if domain not in DOMAINS:
        raise S6AccessibilityError("UNKNOWN_DOMAIN_FAIL_CLOSED")
    if subtype_value not in DOMAIN_SUBTYPE_MATRIX[domain]:
        raise S6AccessibilityError("DOMAIN_SUBTYPE_MISMATCH" if subtype_value in sum(DOMAIN_SUBTYPE_MATRIX.values(), ()) else "UNKNOWN_SUBTYPE_FAIL_CLOSED")
    shape, line, label = DOMAIN_ENCODING[domain]
    return S6EventEncoding(domain, subtype_value, label, shape, line)


def encode_risk(risk_or_domain: S5RiskAnchor | Mapping[str, Any] | str,
                severity: str | None = None) -> S6RiskEncoding:
    if isinstance(risk_or_domain, S5RiskAnchor):
        domain, severity_value = risk_or_domain.domain, risk_or_domain.severity
    elif isinstance(risk_or_domain, Mapping):
        domain, severity_value = risk_or_domain.get("domain"), risk_or_domain.get("severity")
    else:
        domain, severity_value = risk_or_domain, severity
    if domain not in DOMAINS:
        raise S6AccessibilityError("UNKNOWN_DOMAIN_FAIL_CLOSED")
    if severity_value not in SEVERITY_ZH:
        raise S6AccessibilityError("UNKNOWN_SEVERITY_FAIL_CLOSED")
    shape, _line, label = DOMAIN_ENCODING[domain]
    return S6RiskEncoding(
        domain=domain, severity=severity_value, short_label_zh=label,
        severity_zh=SEVERITY_ZH[severity_value], shape=RISK_OVERLAY_SHAPE,
        outer_ring=True,
        text=RISK_OVERLAY_TEXT_PATTERN.format(domain_short_label=label, severity_zh=SEVERITY_ZH[severity_value]),
        colour_only=False,
    )


def validate_keyboard_non_mutating(contract: S6KeyboardContract | None = None) -> bool:
    value = build_keyboard_contract() if contract is None else contract
    return type(value) is S6KeyboardContract and all(not item.medical_state_mutation for item in value.bindings)


build_s6_keyboard_contract = build_keyboard_contract
handle_keyboard = dispatch_keyboard
event_encoding = encode_event
risk_encoding = encode_risk
build_non_colour_registry = build_audience_encoding_registry


__all__ = [
    "S6AccessibilityError", "S6KeyboardResult", "S6EventEncoding", "S6RiskEncoding",
    "build_keyboard_contract", "build_s6_keyboard_contract", "keyboard_binding", "dispatch_keyboard",
    "handle_keyboard", "encode_event", "event_encoding", "encode_risk", "risk_encoding",
    "validate_keyboard_non_mutating", "build_audience_encoding_registry", "build_non_colour_registry",
]
