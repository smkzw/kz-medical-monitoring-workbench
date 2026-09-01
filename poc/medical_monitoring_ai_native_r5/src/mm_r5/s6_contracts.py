"""R5-S6 renderer-neutral contracts.

The module contains only frozen values and deterministic helpers.  It does not
read the S6 JSON artifacts: the accepted contract bytes are represented by
constants here, while typed S5 packets remain the only runtime authority.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import types
import unicodedata
from dataclasses import dataclass, fields
from datetime import date
from typing import Any, Literal, Mapping, Optional, Tuple, Union, get_args, get_origin, get_type_hints


S6_SCHEMA = "medical-monitoring-r5-s6-navigation-density-accessibility-exact-contract-v0.1"
S6_SCHEMA_VERSION = "2026-08-26.1"
S6_CONTRACT_ID = "medical-monitoring-r5-s6-navigation-density-accessibility-contract-v0.1"
S6_CONTRACT_CONTENT_HASH = "ba083b9a60b09560a045ef03ce7df73196467e2473ba19a9e8c7ff747ec6f4ec"
S6_ACCEPTANCE_TOKEN = "ACCEPT_R5_S6_CONTRACT_V0_1"
S6_UNLOCK_TOKEN = "ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT"
S6_AUTHORITY_MODE = "synthetic_offline_test_only"
S6_FALLBACK_POLICY = "none"
S6_AUDIENCE_ENCODING_CONTENT_HASH = "16e22812c22380eba16dfb3cfa3a0d610a52db0d7e84cf2843bee70a1e68f247"
S6_PERFORMANCE_REGISTRY_CONTENT_HASH = "d36719fe3766125e1550faba54cc6cae7a88ebd81ac6baa76c48fd75b58be9e7"
S6_CORPUS_CONTENT_HASH = "6b94a83fa3507b3c0ec0030f6b84e3916e081c436d2af771e8e5dbf46d85463b"
S6_SCHEMA_CONTENT_HASH = "5a2e58fd7a2f4f37ce66fe58ce43522d7ef833802e140b10477b62d2081b3cf6"
S6_MIN_VIEWPORT = (1440, 900)

AGGREGATION_POLICIES = ("low_risk_by_domain_window", "none", "none_source_expanded")
AXIS_MODES = ("calendar", "study_day")
BENCHMARK_STATISTICS = ("p95_nearest_rank", "p05_nearest_rank")
CHANGE_KINDS = (
    "initial_current", "new", "upgraded", "continued", "downgraded",
    "resolved", "reopened", "superseded", "not_evaluable", "not_comparable",
)
CUTOFF_STATES = ("present", "absent")
DATE_STATES = ("exact", "partial", "conflicted", "missing")
DENSITY_MODES = ("standard", "high")
DOMAINS = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance",
)
EVENT_SHAPES = (
    "rounded_rect", "bookmark", "capsule", "hexagon", "square",
    "doorframe", "circle", "triangle", "single_flag",
)
FALLBACK_POLICIES = ("none",)
JOURNEY_SUBTYPES = (
    "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
    "lab", "exam", "hospitalization", "procedure", "protocol_deviation",
    "scale", "symptom", "efficacy", "outcome", "trend",
)
KEYBOARD_ACTIONS = (
    "focus_next_region", "focus_previous_region", "activate_focused_target",
    "toggle_focused_control", "close_ephemeral_surface", "move_previous",
    "move_next", "focus_first", "focus_last", "semantic_zoom_in",
    "semantic_zoom_out", "semantic_zoom_reset",
)
KEYBOARD_KEYS = (
    "Tab", "Shift+Tab", "Enter", "Space", "Escape", "ArrowUp", "ArrowDown",
    "ArrowLeft", "ArrowRight", "Home", "End", "+", "-", "0",
)
KEYBOARD_SCOPES = (
    "global", "risk_list", "center_map", "inspector", "workspace",
    "temporal_spine", "source_drawer",
)
LINE_STYLES = ("solid", "dashed", "dot_dash", "step", "trend", "bracket")
PERFORMANCE_MODES = ("cold", "warm")
PERFORMANCE_RESULT_STATES = ("unmeasured_contract_only", "measured_pass", "measured_fail")
RESTORATION_OUTCOMES = ("restored", "not_restored")
RISK_VISIBILITY_POLICIES = ("all_critical_high_medium", "all_projectable")
SEMANTIC_ZOOM_LEVELS = ("overview", "detail", "evidence")
SEVERITIES = ("critical", "high", "medium", "low")
SORT_DIRECTIONS = ("asc", "desc")
SORT_KEYS = ("priority", "change", "evidence", "site_stable")
SOURCE_LOCATOR_POLICIES = ("risk_only", "event_and_risk", "all_projectable")
TARGET_KINDS = ("subject_workspace", "risk_inspector", "source_locator")
VIEWS = ("journey", "profile", "timeline")

DOMAIN_SUBTYPE_MATRIX = {
    "ae": ("ae",),
    "mh": ("mh",),
    "cm": ("concomitant_medication",),
    "ip": ("ip_dose", "ip_pause", "ip_resume"),
    "lab_exam": ("lab", "exam"),
    "hospital_procedure": ("hospitalization", "procedure"),
    "symptom_efficacy": ("symptom", "efficacy", "scale", "outcome", "trend"),
    "protocol_compliance": ("protocol_deviation",),
}
DOMAIN_ENCODING = {
    "ae": ("rounded_rect", "solid", "AE"),
    "mh": ("bookmark", "dot_dash", "MH"),
    "cm": ("capsule", "solid", "合并用药"),
    "ip": ("hexagon", "step", "试验药"),
    "lab_exam": ("square", "trend", "检验/检查"),
    "hospital_procedure": ("doorframe", "solid", "住院/操作"),
    "symptom_efficacy": ("circle", "trend", "症状/疗效"),
    "protocol_compliance": ("single_flag", "bracket", "方案符合"),
}
SEVERITY_ZH = {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}
FORBIDDEN_AUDIENCE_TERMS = (
    "已记录事项", "正式事实", "候选信号", "通用风险点", "只读xx", "Checklist", "待行动", "未读",
)
RISK_OVERLAY_SHAPE = "double_chevron_badge"
RISK_OVERLAY_TEXT_PATTERN = "{domain_short_label}·{severity_zh}"
EVENT_FORBIDDEN_SHAPES = (RISK_OVERLAY_SHAPE,)
SEMANTIC_ZOOM_POLICY = {
    "overview": {
        "aggregation_policy": "low_risk_by_domain_window",
        "risk_visibility_policy": "all_critical_high_medium",
        "source_locator_policy": "risk_only",
    },
    "detail": {
        "aggregation_policy": "none",
        "risk_visibility_policy": "all_critical_high_medium",
        "source_locator_policy": "event_and_risk",
    },
    "evidence": {
        "aggregation_policy": "none_source_expanded",
        "risk_visibility_policy": "all_projectable",
        "source_locator_policy": "all_projectable",
    },
}


class S6RuntimeContractError(Exception):
    """A typed S6 value violates a closed contract or hash invariant."""


class S6RuntimeImplementationError(Exception):
    """A trusted S5 input or implementation precondition is invalid."""


class S6HashMismatchError(S6RuntimeContractError):
    """A hash-bearing S6 value is not sealed from its own fields."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNION_ORIGINS = (Union,) + ((types.UnionType,) if hasattr(types, "UnionType") else ())


def is_sha256_hex(value: Any) -> bool:
    return type(value) is str and bool(_SHA256_RE.fullmatch(value))


def _canonicalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {item.name: _canonicalize(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {
            unicodedata.normalize("NFC", str(key)): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    return value


def s6_canonical_bytes(value: Any) -> bytes:
    """S6 canonical JSON: sorted keys, NFC strings, compact JSON and newline."""
    return (json.dumps(_canonicalize(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def s6_canonical_json(value: Any) -> str:
    return s6_canonical_bytes(value).decode("utf-8")


def s6_sha256(value: Any) -> str:
    return hashlib.sha256(s6_canonical_bytes(value)).hexdigest()


def s6_as_mapping(value: Any) -> Any:
    return _canonicalize(value)


def _without_field(value: Any, field_name: str) -> dict[str, Any]:
    mapped = s6_as_mapping(value)
    if not isinstance(mapped, dict):
        raise TypeError("hash input must be an object")
    return {key: item for key, item in mapped.items() if key != field_name}


def s6_canonical_state_hash(value: Any) -> str:
    return s6_sha256(_without_field(value, "canonical_state_hash"))


def s6_corpus_identity_hash(value: Any) -> str:
    mapped = s6_as_mapping(value)
    if not isinstance(mapped, dict):
        raise TypeError("corpus identity must be an object")
    payload = {
        "schema": "medical-monitoring-r5-s6-offline-performance-corpus-v0.1",
        "corpus_id": mapped["corpus_id"],
        "schema_version": mapped["schema_version"],
        "event_count": mapped["event_count"],
        "indicator_count": mapped["indicator_count"],
        "risk_anchor_count": mapped["risk_anchor_count"],
        "record_order": mapped["record_order"],
        "identity_recipe": {
            "record_key_fields": ["record_kind", "ordinal"],
            "ordinal_base": 0,
            "content_fields": ["record_kind", "ordinal", "domain", "source_locator_ref"],
            "ordinal_is_not_medical_authority": True,
            "fixture_name_and_row_count_are_not_authority": True,
        },
    }
    return s6_sha256(payload)


def _audience_identity_payload(value: Any) -> dict[str, Any]:
    mapped = s6_as_mapping(value)
    if not isinstance(mapped, dict):
        raise TypeError("audience registry must be an object")
    return {
        "schema": "medical-monitoring-r5-s6-audience-encoding-registry-v0.1",
        "schema_version": S6_SCHEMA_VERSION,
        "contract_id": S6_CONTRACT_ID,
        "domain_items": mapped["domain_items"],
        "severity_items": mapped["severity_items"],
        "risk_overlay": mapped["risk_overlay"],
        "event_forbidden_shapes": mapped["event_forbidden_shapes"],
        "forbidden_terms": mapped["forbidden_terms"],
        "severity_rules": {
            "critical_authority_required": True,
            "high_must_not_promote_to_critical": True,
            "legacy_mapping": {"mild": "low", "moderate": "medium", "severe": "high"},
            "unmapped_legacy_value": "fail_closed",
        },
        "domain_rules": {
            "exact_domain_count": 8,
            "unknown_domain": "fail_closed_to_domain_confirmation_surface",
            "other_domain": "forbidden",
            "unlisted_domain_subtype_pair": "fail_closed",
            "symptom_efficacy_is_one_domain": True,
        },
    }


def s6_audience_encoding_hash(value: Any) -> str:
    return s6_sha256(_audience_identity_payload(value))


def _annotation_valid(annotation: Any, value: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Literal:
        return value in get_args(annotation)
    if origin in _UNION_ORIGINS:
        args = get_args(annotation)
        return any(item is type(None) and value is None or item is not type(None) and _annotation_valid(item, value)
                   for item in args)
    if origin in (tuple, Tuple):
        if type(value) is not tuple:
            return False
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_annotation_valid(args[0], item) for item in value)
        return len(args) == len(value) and all(_annotation_valid(item_type, item) for item_type, item in zip(args, value))
    if annotation is str:
        return type(value) is str
    if annotation is int:
        return type(value) is int
    if annotation is bool:
        return type(value) is bool
    if annotation is date:
        return type(value) is date
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return type(value) is annotation
    return True


def _validate_object_shape(instance: Any) -> None:
    hints = get_type_hints(type(instance))
    for item in fields(instance):
        value = getattr(instance, item.name)
        if not _annotation_valid(hints[item.name], value):
            raise S6RuntimeContractError(f"{type(instance).__name__}.{item.name}: invalid typed value")
        if item.name.endswith("hash") and not is_sha256_hex(value):
            raise S6RuntimeContractError(f"{type(instance).__name__}.{item.name}: expected lowercase sha256")


class _Checked:
    def __post_init__(self) -> None:
        _validate_object_shape(self)


@dataclass(frozen=True)
class S6DeepLinkIdentity(_Checked):
    target_kind: Literal["subject_workspace", "risk_inspector", "source_locator"]
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_state: Literal["present", "absent"]
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: str
    risk_ref: str
    spine_ref: str
    view: Literal["journey", "profile", "timeline"]
    axis_mode: Literal["calendar", "study_day"]
    window_start: Optional[date]
    window_end: Optional[date]
    visit_ref: Optional[str]
    event_ref: Optional[str]
    risk_anchor_ref: Optional[str]
    source_locator_ref: Optional[str]
    target_projection_content_hash: str
    return_context_key: str
    fallback_policy: Literal["none"]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.cutoff_state == "absent" and self.cutoff_ref is not None:
            raise S6RuntimeContractError("S6DeepLinkIdentity absent cutoff must not carry cutoff_ref")
        if (self.window_start is not None and self.window_end is not None
                and self.window_start > self.window_end):
            raise S6RuntimeContractError("S6DeepLinkIdentity window bounds are invalid")


@dataclass(frozen=True)
class S6FilterState(_Checked):
    change_kind: Tuple[Literal[
        "initial_current", "new", "upgraded", "continued", "downgraded", "resolved",
        "reopened", "superseded", "not_evaluable", "not_comparable",
    ], ...]
    domain: Tuple[Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance",
    ], ...]
    severity: Tuple[Literal["critical", "high", "medium", "low"], ...]
    site_refs: Tuple[str, ...]
    include_low: bool


@dataclass(frozen=True)
class S6SortState(_Checked):
    key: Literal["priority", "change", "evidence", "site_stable"]
    direction: Literal["asc", "desc"]


@dataclass(frozen=True)
class S6PageState(_Checked):
    page_index: int
    page_size: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.page_index < 0 or self.page_size <= 0:
            raise S6RuntimeContractError("S6PageState page bounds are invalid")


@dataclass(frozen=True)
class S6SelectionAnchor(_Checked):
    selected_event_ref: Optional[str]
    selected_risk_ref: Optional[str]
    selected_visit_ref: Optional[str]
    risk_anchor_ref: Optional[str]
    source_locator_ref: Optional[str]


@dataclass(frozen=True)
class S6SemanticZoomState(_Checked):
    density_mode: Literal["standard", "high"]
    semantic_zoom_level: Literal["overview", "detail", "evidence"]
    aggregation_policy: Literal["low_risk_by_domain_window", "none", "none_source_expanded"]
    risk_visibility_policy: Literal["all_critical_high_medium", "all_projectable"]
    source_locator_policy: Literal["risk_only", "event_and_risk", "all_projectable"]


@dataclass(frozen=True)
class S6CanonicalReturnState(_Checked):
    deep_link_identity: S6DeepLinkIdentity
    filter_state: S6FilterState
    sort_state: S6SortState
    page_state: S6PageState
    selection_anchor: S6SelectionAnchor
    semantic_zoom_state: S6SemanticZoomState
    axis_mode: Literal["calendar", "study_day"]
    window_start: Optional[date]
    window_end: Optional[date]
    canonical_state_hash: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.canonical_state_hash != s6_canonical_state_hash(self):
            raise S6HashMismatchError("S6CanonicalReturnState.canonical_state_hash")


@dataclass(frozen=True)
class S6EphemeralReturnState(_Checked):
    scroll_refs: Tuple[str, ...]
    inspector_width: int
    inspector_expanded: bool
    temporary_expansion_refs: Tuple[str, ...]
    focus_ref: Optional[str]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.inspector_width <= 0:
            raise S6RuntimeContractError("S6EphemeralReturnState inspector width is invalid")


@dataclass(frozen=True)
class S6ReturnContext(_Checked):
    return_context_key: str
    canonical: S6CanonicalReturnState
    ephemeral: S6EphemeralReturnState
    restoration_outcome: Literal["restored", "not_restored"]


@dataclass(frozen=True)
class S6KeyboardBinding(_Checked):
    key: Literal[
        "Tab", "Shift+Tab", "Enter", "Space", "Escape", "ArrowUp", "ArrowDown",
        "ArrowLeft", "ArrowRight", "Home", "End", "+", "-", "0",
    ]
    action: Literal[
        "focus_next_region", "focus_previous_region", "activate_focused_target",
        "toggle_focused_control", "close_ephemeral_surface", "move_previous", "move_next",
        "focus_first", "focus_last", "semantic_zoom_in", "semantic_zoom_out", "semantic_zoom_reset",
    ]
    scope: Literal["global", "risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"]
    prevent_default: bool
    medical_state_mutation: bool


@dataclass(frozen=True)
class S6KeyboardContract(_Checked):
    region_order: Tuple[Literal["global", "risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"], ...]
    bindings: Tuple[S6KeyboardBinding, ...]
    focus_policy: str
    selection_policy: str


@dataclass(frozen=True)
class S6DomainEncodingItem(_Checked):
    domain: Literal["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"]
    short_label_zh: str
    event_shape: Literal["rounded_rect", "bookmark", "capsule", "hexagon", "square", "doorframe", "circle", "triangle", "single_flag"]
    line_style: Literal["solid", "dashed", "dot_dash", "step", "trend", "bracket"]
    subtypes: Tuple[Literal[
        "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume", "lab", "exam",
        "hospitalization", "procedure", "protocol_deviation", "scale", "symptom", "efficacy", "outcome", "trend",
    ], ...]


@dataclass(frozen=True)
class S6SeverityEncodingItem(_Checked):
    severity: Literal["critical", "high", "medium", "low"]
    label_zh: str


@dataclass(frozen=True)
class S6RiskOverlayEncoding(_Checked):
    shape: str
    outer_ring: bool
    text_pattern: str
    colour_only: bool


@dataclass(frozen=True)
class S6AudienceEncodingRegistry(_Checked):
    domain_items: Tuple[S6DomainEncodingItem, ...]
    severity_items: Tuple[S6SeverityEncodingItem, ...]
    risk_overlay: S6RiskOverlayEncoding
    event_forbidden_shapes: Tuple[str, ...]
    forbidden_terms: Tuple[str, ...]
    content_hash: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.content_hash != s6_audience_encoding_hash(self):
            raise S6HashMismatchError("S6AudienceEncodingRegistry.content_hash")


@dataclass(frozen=True)
class S6PerformanceCorpusIdentity(_Checked):
    corpus_id: str
    schema_version: str
    event_count: int
    indicator_count: int
    risk_anchor_count: int
    record_order: Tuple[str, ...]
    content_hash: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_count < 0 or self.indicator_count < 0 or self.risk_anchor_count < 0:
            raise S6RuntimeContractError("S6PerformanceCorpusIdentity counts are invalid")
        if self.content_hash != s6_corpus_identity_hash(self):
            raise S6HashMismatchError("S6PerformanceCorpusIdentity.content_hash")


@dataclass(frozen=True)
class S6PerformanceThresholds(_Checked):
    cold_interactive_ms_p95: int
    warm_interactive_ms_p95: int
    brush_zoom_select_ms_p95: int
    pan_fps_p05: int


@dataclass(frozen=True)
class S6PerformanceMarks(_Checked):
    interactive_start: str
    interactive_end: str
    response_start: str
    response_end: str


@dataclass(frozen=True)
class S6PerformanceProfile(_Checked):
    corpus: S6PerformanceCorpusIdentity
    modes: Tuple[Literal["cold", "warm"], ...]
    samples_per_mode: int
    latency_statistic: Literal["p95_nearest_rank", "p05_nearest_rank"]
    fps_statistic: Literal["p95_nearest_rank", "p05_nearest_rank"]
    thresholds: S6PerformanceThresholds
    viewport: Tuple[int, ...]
    marks: S6PerformanceMarks
    result_state: Literal["unmeasured_contract_only", "measured_pass", "measured_fail"]


def build_audience_encoding_registry() -> S6AudienceEncodingRegistry:
    domains = tuple(
        S6DomainEncodingItem(
            domain=domain,
            short_label_zh=values[2],
            event_shape=values[0],
            line_style=values[1],
            subtypes=DOMAIN_SUBTYPE_MATRIX[domain],
        )
        for domain, values in DOMAIN_ENCODING.items()
    )
    severities = tuple(S6SeverityEncodingItem(severity=level, label_zh=SEVERITY_ZH[level]) for level in SEVERITIES)
    return S6AudienceEncodingRegistry(
        domain_items=domains,
        severity_items=severities,
        risk_overlay=S6RiskOverlayEncoding(
            shape=RISK_OVERLAY_SHAPE,
            outer_ring=True,
            text_pattern=RISK_OVERLAY_TEXT_PATTERN,
            colour_only=False,
        ),
        event_forbidden_shapes=EVENT_FORBIDDEN_SHAPES,
        forbidden_terms=FORBIDDEN_AUDIENCE_TERMS,
        content_hash=S6_AUDIENCE_ENCODING_CONTENT_HASH,
    )


def build_audience_encoding_registry_mapping() -> dict[str, Any]:
    """Return the frozen machine-registry shape for offline validation."""
    registry = build_audience_encoding_registry()
    return {
        "schema": "medical-monitoring-r5-s6-audience-encoding-registry-v0.1",
        "schema_version": S6_SCHEMA_VERSION,
        "contract_id": S6_CONTRACT_ID,
        "domain_items": s6_as_mapping(registry.domain_items),
        "severity_items": s6_as_mapping(registry.severity_items),
        "risk_overlay": s6_as_mapping(registry.risk_overlay),
        "event_forbidden_shapes": list(registry.event_forbidden_shapes),
        "forbidden_terms": list(registry.forbidden_terms),
        "severity_rules": {
            "critical_authority_required": True,
            "high_must_not_promote_to_critical": True,
            "legacy_mapping": {"mild": "low", "moderate": "medium", "severe": "high"},
            "unmapped_legacy_value": "fail_closed",
        },
        "domain_rules": {
            "exact_domain_count": 8,
            "unknown_domain": "fail_closed_to_domain_confirmation_surface",
            "other_domain": "forbidden",
            "unlisted_domain_subtype_pair": "fail_closed",
            "symptom_efficacy_is_one_domain": True,
        },
        "content_hash": S6_AUDIENCE_ENCODING_CONTENT_HASH,
    }


def build_density_semantic_zoom_contract() -> dict[str, Any]:
    return {
        "desktop_min_viewport": [1440, 900],
        "density_modes": {
            "standard": "preserve all contract content with normal spacing",
            "high": "reduce redundant spacing only; never hide, relabel or demote a required risk",
        },
        "semantic_zoom_levels": {
            "overview": {
                "aggregation_policy": "low_risk_by_domain_window",
                "content_omission_policy": "low_risk_only",
                "risk_visibility_policy": "all_critical_high_medium",
                "source_locator_policy": "risk_only",
            },
            "detail": {
                "aggregation_policy": "none",
                "content_omission_policy": "none",
                "risk_visibility_policy": "all_critical_high_medium",
                "source_locator_policy": "event_and_risk",
            },
            "evidence": {
                "aggregation_policy": "none_source_expanded",
                "content_omission_policy": "none",
                "risk_visibility_policy": "all_projectable",
                "source_locator_policy": "all_projectable",
            },
        },
        "invariants": [
            "all critical/high/medium risk anchors remain individually represented at every semantic zoom level",
            "overview aggregation is limited to low-risk ordinary events within one domain and time window",
            "detail and evidence do not aggregate events or risk anchors",
            "semantic zoom changes representation, not identity, membership, authority or canonical return state",
            "density changes spacing only and cannot be used as an omission or fallback mechanism",
        ],
    }


def build_protected_boundary() -> dict[str, Any]:
    return {
        "protected_boundaries": {
            "port_8911": "stopped_required",
            "medical_writing_file_count": 542,
            "medical_writing_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
            "accepted_r1_r5_inputs_immutable": True,
            "production_paths_written": False,
        },
        "manifest": {"acceptance_token_emitted": False},
    }


def build_performance_corpus_identity() -> S6PerformanceCorpusIdentity:
    return S6PerformanceCorpusIdentity(
        corpus_id="r5-s6-offline-density-performance-corpus-v0.1",
        schema_version=S6_SCHEMA_VERSION,
        event_count=1000,
        indicator_count=40,
        risk_anchor_count=300,
        record_order=("event", "indicator", "risk_anchor"),
        content_hash=S6_CORPUS_CONTENT_HASH,
    )


def build_performance_profile() -> S6PerformanceProfile:
    return S6PerformanceProfile(
        corpus=build_performance_corpus_identity(),
        modes=("cold", "warm"),
        samples_per_mode=7,
        latency_statistic="p95_nearest_rank",
        fps_statistic="p05_nearest_rank",
        thresholds=S6PerformanceThresholds(
            cold_interactive_ms_p95=2500,
            warm_interactive_ms_p95=1500,
            brush_zoom_select_ms_p95=100,
            pan_fps_p05=30,
        ),
        viewport=S6_MIN_VIEWPORT,
        marks=S6PerformanceMarks(
            interactive_start="navigationStart",
            interactive_end="risk-list, center-map, inspector and journey controls enabled",
            response_start="trusted pointer or keyboard event",
            response_end="next painted frame with updated canonical selection",
        ),
        result_state="unmeasured_contract_only",
    )


def build_performance_registry() -> dict[str, Any]:
    """Return the frozen offline registry shape without reading its artifact."""
    corpus = {
        "schema": "medical-monitoring-r5-s6-offline-performance-corpus-v0.1",
        "corpus_id": "r5-s6-offline-density-performance-corpus-v0.1",
        "schema_version": S6_SCHEMA_VERSION,
        "event_count": 1000,
        "indicator_count": 40,
        "risk_anchor_count": 300,
        "record_order": ["event", "indicator", "risk_anchor"],
        "identity_recipe": {
            "record_key_fields": ["record_kind", "ordinal"],
            "ordinal_base": 0,
            "content_fields": ["record_kind", "ordinal", "domain", "source_locator_ref"],
            "ordinal_is_not_medical_authority": True,
            "fixture_name_and_row_count_are_not_authority": True,
        },
        "content_hash": S6_CORPUS_CONTENT_HASH,
    }
    return {
        "content_hash": S6_PERFORMANCE_REGISTRY_CONTENT_HASH,
        "contract_id": S6_CONTRACT_ID,
        "corpus": corpus,
        "fps_statistic": "p05_nearest_rank",
        "latency_statistic": "p95_nearest_rank",
        "marks": {
            "interactive_end": "risk-list, center-map, inspector and journey controls enabled",
            "interactive_start": "navigationStart",
            "response_end": "next painted frame with updated canonical selection",
            "response_start": "trusted pointer or keyboard event",
        },
        "modes": ["cold", "warm"],
        "offline_boundary": {
            "browser_acceptance": "S7_only",
            "real_model": False,
            "real_project": False,
            "result_state_at_contract_stage": "unmeasured_contract_only",
            "starts_8911": False,
            "synthetic_only": True,
        },
        "required_workloads": [
            "cold_interactive", "warm_interactive", "brush_response", "zoom_response",
            "selection_response", "pan_fps", "high_risk_visibility", "layout_overflow",
        ],
        "result_state": "unmeasured_contract_only",
        "samples_per_mode": 7,
        "schema": "medical-monitoring-r5-s6-performance-profile-v0.1",
        "schema_version": S6_SCHEMA_VERSION,
        "thresholds": {
            "brush_zoom_select_ms_p95": 100,
            "cold_interactive_ms_p95": 2500,
            "pan_fps_p05": 30,
            "warm_interactive_ms_p95": 1500,
        },
        "viewport": [1440, 900],
    }


# Familiar aliases keep the S6 surface consistent with the earlier R5 slices.
canonical_json = s6_canonical_json
canonical_bytes = s6_canonical_bytes
canonical_sha256 = s6_sha256
content_hash = s6_sha256
s6_packet_as_mapping = s6_as_mapping
S6_CONTRACT_SCHEMA_ID = S6_SCHEMA
S6_RUNTIME_CONTRACT_ID = S6_CONTRACT_ID
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"


__all__ = [name for name in globals() if name.startswith("S6") or name in {
    "AGGREGATION_POLICIES", "AXIS_MODES", "BENCHMARK_STATISTICS", "CHANGE_KINDS", "CUTOFF_STATES",
    "DATE_STATES", "DENSITY_MODES", "DOMAINS", "DOMAIN_ENCODING", "DOMAIN_SUBTYPE_MATRIX", "EVENT_SHAPES",
    "EVENT_FORBIDDEN_SHAPES", "FALLBACK_POLICIES", "FORBIDDEN_AUDIENCE_TERMS", "JOURNEY_SUBTYPES",
    "KEYBOARD_ACTIONS", "KEYBOARD_KEYS", "KEYBOARD_SCOPES", "LINE_STYLES", "PERFORMANCE_MODES",
    "PERFORMANCE_RESULT_STATES", "RESTORATION_OUTCOMES", "RISK_OVERLAY_SHAPE", "RISK_VISIBILITY_POLICIES",
    "SEMANTIC_ZOOM_LEVELS", "SEMANTIC_ZOOM_POLICY", "SEVERITIES", "SEVERITY_ZH", "SORT_DIRECTIONS",
    "SORT_KEYS", "SOURCE_LOCATOR_POLICIES", "TARGET_KINDS", "VIEWS", "build_audience_encoding_registry",
    "build_performance_corpus_identity", "build_performance_profile", "canonical_bytes", "canonical_json",
    "build_performance_registry", "build_audience_encoding_registry_mapping", "build_density_semantic_zoom_contract",
    "build_protected_boundary",
    "canonical_sha256", "content_hash", "is_sha256_hex", "s6_as_mapping", "s6_audience_encoding_hash",
    "s6_canonical_bytes", "s6_canonical_json", "s6_canonical_state_hash", "s6_corpus_identity_hash", "s6_packet_as_mapping",
    "s6_sha256", "HASH_CANONICALIZATION",
}]
