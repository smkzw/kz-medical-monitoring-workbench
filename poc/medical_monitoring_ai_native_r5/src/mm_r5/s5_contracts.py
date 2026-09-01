"""R5-S5 Subject Workspace renderer-neutral typed contracts.

This module is intentionally small and offline.  The two accepted public
authority producers remain the only source of clinical facts; these records
only give the S5 consumer a lossless, typed boundary and deterministic
navigation hashes.  No file, network, service, model, or UI dependency is
allowed here.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, fields
from datetime import date
from typing import Any, Literal, Mapping, Optional, Tuple, Union, get_args, get_origin, get_type_hints


S5_SCHEMA = "medical-monitoring-r5-s5-subject-workspace-exact-contract-v0.1"
S5_SCHEMA_VERSION = "2026-08-26.1"
S5_CONTRACT_ID = "medical-monitoring-r5-s5-subject-workspace-contract-v0.1"
S5_CONTRACT_CONTENT_HASH = "803757c2993109b681b6facefc8c28e88bf2076e75950798abcce3e50d716e91"
S5_ACCEPTANCE_TOKEN = "ACCEPT_R5_S5_CONTRACT"
S5_AUTHORITY_MODE = "synthetic_offline_test_only"
S5_FALLBACK_POLICY = "fail_closed_no_nearest"
S5_PUBLIC_SCHEMA_VERSION = "2026-08-19.1"

AEMH_DOMAINS = ("ae", "mh")
APPLICABILITY_STATES = ("applicable", "not_applicable", "not_provided")
AXIS_MODES = ("calendar", "study_day")
CUTOFF_ENDPOINT_STATES = ("present", "absent")
CUTOFF_STATES = ("present", "absent")
DATE_GEOMETRIES = ("point", "closed_interval", "open_start", "open_end")
DATE_STATES = ("exact", "partial", "conflicted", "missing")
DOMAINS = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance",
)
EVENT_SHAPES = (
    "rounded_rect", "bookmark", "capsule", "hexagon", "square",
    "doorframe", "circle", "triangle", "single_flag",
)
FALLBACK_POLICIES = ("fail_closed_no_nearest",)
HISTORY_EVENT_KINDS = ("reminder_created", "match_decided", "withdrawn", "reappeared")
IDENTITY_EVIDENCE_KINDS = ("candidate", "later_fact", "considered_fact")
JOURNEY_SUBTYPES = (
    "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
    "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
    "scale", "outcome", "trend", "protocol_deviation",
)
LEGACY_MAPPING_STATES = ("mapped", "unmapped_fail_closed")
LEGACY_TREATMENT_KINDS = ("background_treatment", "non_drug_treatment")
LINE_STYLES = ("solid", "dashed", "dot_dash", "step", "trend", "bracket")
MATCH_STATES = ("exact", "ambiguous", "rejected")
PENDING_ITEM_KINDS = ("event", "risk", "visit", "phase")
RECEIPT_VARIANTS = ("subject_temporal", "aemh_match_history")
RISK_LIFECYCLE_EFFECTS = ("none",)
S5_ANCHOR_KINDS = ("none", "event", "risk_anchor", "visit", "source_locator")
S5_PROJECTION_KINDS = ("subject_temporal", "aemh_history")
S5_VIEWS = ("journey", "profile", "timeline")
SEVERITIES = ("critical", "high", "medium", "low")
SOURCE_LOCATOR_VARIANTS = ("r4_source_locator", "d08_source_locator")
SYMPTOM_EFFICACY_SUBTYPES = ("symptom", "efficacy", "scale", "outcome", "trend")
VISIBILITY_STATES = ("projectable", "hidden", "not_evaluable")
VISIT_KINDS = ("nominal", "actual", "unscheduled")

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
RISK_OVERLAY_SHAPE = "double_chevron_badge"
SEVERITY_ZH = {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}
FORBIDDEN_AUDIENCE_TERMS = (
    "已记录事项", "正式事实", "候选信号", "通用风险点", "只读xx", "Checklist", "待行动", "未读",
)
LEGACY_SEVERITY_MAPPING = {"severe": "high", "moderate": "medium", "mild": "low"}


class S5RuntimeContractError(Exception):
    """A candidate S5 record violates a closed contract or invariant."""


class S5RuntimeImplementationError(Exception):
    """The trusted source or caller violates the implementation boundary."""


class S5AuthorityAdapterError(S5RuntimeImplementationError):
    """A typed public-authority packet could not be adapted."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


class S5HashMismatchError(S5RuntimeContractError):
    """A navigation object's content hash does not match its fields."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def is_sha256_hex(value: Any) -> bool:
    return type(value) is str and bool(_SHA256_RE.fullmatch(value))


def _canonicalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _canonicalize(getattr(value, field.name)) for field in fields(value)}
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


def s5_canonical_json(value: Any) -> str:
    return json.dumps(_canonicalize(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def s5_canonical_bytes(value: Any) -> bytes:
    return s5_canonical_json(value).encode("utf-8")


def s5_sha256(value: Any) -> str:
    return hashlib.sha256(s5_canonical_bytes(value)).hexdigest()


def s5_canonical_hash(value: Any) -> str:
    return s5_sha256(value)


def s5_as_mapping(value: Any) -> Any:
    """Losslessly serialize an S5 object for tests, logs, and comparisons."""
    return _canonicalize(value)


def packet_as_mapping(value: Any) -> Any:
    return s5_as_mapping(value)


def _without_field(value: Any, name: str) -> dict[str, Any]:
    mapped = s5_as_mapping(value)
    if not isinstance(mapped, dict):
        raise TypeError("hash input must be an object")
    return {key: item for key, item in mapped.items() if key != name}


def s5_navigation_content_hash(value: Any) -> str:
    return s5_sha256(_without_field(value, "content_hash"))


def s5_view_binding_hash(value: Any) -> str:
    return s5_sha256(_without_field(value, "content_hash"))


def s5_workspace_hash(value: Any) -> str:
    mapped = _without_field(value, "content_hash")
    bindings = mapped.get("view_bindings")
    if isinstance(bindings, list):
        mapped["view_bindings"] = sorted(bindings, key=lambda item: item.get("view", ""))
    return s5_sha256(mapped)


def s5_context_ref(
    authority_receipt_ref: str,
    spine_ref: str,
    axis_mode: str,
    window_start: Optional[date],
    window_end: Optional[date],
    selection_anchor: Any,
    selected_event_ref: Optional[str],
    selected_risk_anchor_ref: Optional[str],
    selected_visit_ref: Optional[str],
) -> str:
    return s5_sha256({
        "authority_receipt_ref": authority_receipt_ref,
        "spine_ref": spine_ref,
        "axis_mode": axis_mode,
        "window_start": window_start,
        "window_end": window_end,
        "selection_anchor": selection_anchor,
        "selected_event_ref": selected_event_ref,
        "selected_risk_anchor_ref": selected_risk_anchor_ref,
        "selected_visit_ref": selected_visit_ref,
    })


def _annotation_valid(annotation: Any, value: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Literal:
        return value in get_args(annotation)
    if origin in (tuple, Tuple):
        if type(value) is not tuple:
            return False
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_annotation_valid(args[0], item) for item in value)
        return len(args) == len(value) and all(
            _annotation_valid(item_type, item) for item_type, item in zip(args, value)
        )
    if origin is Union:
        args = get_args(annotation)
        return any(item is type(None) and value is None or item is not type(None) and _annotation_valid(item, value)
                   for item in args)
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


_HASH_FIELD_RE = re.compile(r"(?:_hash|_content_identity)$")


def _validate_object_shape(instance: Any) -> None:
    hints = get_type_hints(type(instance))
    for field in fields(instance):
        value = getattr(instance, field.name)
        if not _annotation_valid(hints[field.name], value):
            raise S5RuntimeContractError(
                f"{type(instance).__name__}.{field.name}: invalid typed value"
            )
        if _HASH_FIELD_RE.search(field.name) and value is not None and not is_sha256_hex(value):
            raise S5RuntimeContractError(
                f"{type(instance).__name__}.{field.name}: expected lowercase sha256"
            )
        if field.name.endswith("_content_identities") and (
            type(value) is not tuple or not all(is_sha256_hex(item) for item in value)
        ):
            raise S5RuntimeContractError(
                f"{type(instance).__name__}.{field.name}: expected sha256 identities"
            )


class _Checked:
    def __post_init__(self) -> None:
        _validate_object_shape(self)


@dataclass(frozen=True)
class S5AEMHIdentityEvidence(_Checked):
    entity_content_identity: str
    entity_ref: str
    evidence_content_hash: str
    evidence_kind: Literal["candidate", "later_fact", "considered_fact"]
    evidence_ref: str
    source_locator_content_hash: str
    source_locator_ref: str
    source_raw_payload_hash: str


@dataclass(frozen=True)
class S5AEMHHistoryEntry(_Checked):
    entry_hash: str
    entry_id: str
    event_kind: Literal["reminder_created", "match_decided", "withdrawn", "reappeared"]
    identity_evidence: Tuple[S5AEMHIdentityEvidence, ...]
    identity_evidence_refs: Tuple[str, ...]
    later_fact_content_identities: Tuple[str, ...]
    later_fact_refs: Tuple[str, ...]
    match_state: Optional[Literal["exact", "ambiguous", "rejected"]]
    prior_entry_hash: Optional[str]
    reason_code: str
    retained_evidence_locator_refs: Tuple[str, ...]
    risk_lifecycle_effect: Literal["none"]
    seq: int
    snapshot_ref: str


@dataclass(frozen=True)
class S5AEMHMembershipIndex(_Checked):
    candidate_refs: Tuple[str, ...]
    later_fact_refs: Tuple[str, ...]
    membership_content_hash: str
    source_locator_refs: Tuple[str, ...]
    thread_refs: Tuple[str, ...]


@dataclass(frozen=True)
class S5AEMHPrefixAnchor(_Checked):
    accepted_prefix_head_hash: Optional[str]
    accepted_prefix_seq: int
    prefix_content_hash: str
    previous_thread_content_hash: Optional[str]
    thread_ref: str


@dataclass(frozen=True)
class S5AEMHThread(_Checked):
    candidate_content_identity: str
    domain: Literal["ae", "mh"]
    evidence_locator_refs: Tuple[str, ...]
    history_entries: Tuple[S5AEMHHistoryEntry, ...]
    original_candidate_ref: str
    original_reminder_ref: str
    project_ref: str
    site_ref: str
    subject_ref: str
    thread_content_hash: str
    thread_ref: str


@dataclass(frozen=True)
class S5ScopeIdentity(_Checked):
    cutoff_ref: Optional[str]
    cutoff_state: Literal["present", "absent"]
    identity_content_hash: str
    project_ref: str
    run_ref: str
    site_ref: str
    snapshot_ref: str
    spine_ref: str
    subject_ref: str


@dataclass(frozen=True)
class S5SourceLocator(_Checked):
    authority_entity_kind: Optional[str]
    authority_entity_ref: Optional[str]
    canonical_location: Optional[str]
    column_or_anchor: str
    locator_content_hash: str
    locator_ref: str
    locator_variant: Literal["r4_source_locator", "d08_source_locator"]
    raw_payload_hash: str
    record_ref: str
    snapshot_ref: str
    source_file_ref: Optional[str]
    source_revision_content_hash: str
    source_revision_ref: str
    table_semantic: Optional[str]


@dataclass(frozen=True)
class S5SourceRevisionContentPair(_Checked):
    accepted_content_hash: str
    locator_refs: Tuple[str, ...]
    pair_content_hash: str
    revision_id: str


@dataclass(frozen=True)
class S5VisibilityClosure(_Checked):
    closure_content_hash: str
    deep_link_eligible: bool
    evaluation_member_refs: Tuple[str, ...]
    evaluation_site_refs: Tuple[str, ...]
    hidden_member_count: int
    hidden_member_refs: Tuple[str, ...]
    hidden_site_count: int
    hidden_site_refs: Tuple[str, ...]
    projectable_member_refs: Tuple[str, ...]
    projectable_site_refs: Tuple[str, ...]
    subject_visibility_state: Literal["projectable", "hidden", "not_evaluable"]
    visibility_decision_hash: str
    visibility_decision_id: str


@dataclass(frozen=True)
class S5AuthorityReceipt(_Checked):
    audience_contract_id: str
    authority_contract_id: str
    authority_contract_version: str
    evaluation_content_identities: Tuple[str, ...]
    public_projection_content_hash: str
    public_projection_id: str
    receipt_content_hash: str
    receipt_id: str
    receipt_variant: Literal["subject_temporal", "aemh_match_history"]
    scope_identity: S5ScopeIdentity
    source_revision_content_pairs: Tuple[S5SourceRevisionContentPair, ...]
    visibility_closure: S5VisibilityClosure


@dataclass(frozen=True)
class S5DateEndpoint(_Checked):
    candidate_values: Tuple[str, ...]
    endpoint_content_hash: str
    exact_date: Optional[date]
    main_axis_projectable: bool
    range_end: Optional[date]
    range_projection_authorized: bool
    range_start: Optional[date]
    source_locator_refs: Tuple[str, ...]
    state: Literal["exact", "partial", "conflicted", "missing"]
    study_day: Optional[int]


@dataclass(frozen=True)
class S5CutoffEndpoint(_Checked):
    cutoff_content_hash: str
    exact_date: Optional[date]
    source_locator_refs: Tuple[str, ...]
    state: Literal["present", "absent"]


@dataclass(frozen=True)
class S5AxisBasis(_Checked):
    axis_content_hash: str
    axis_ref: str
    cutoff_endpoint: S5DateEndpoint
    default_axis_mode: Literal["calendar", "study_day"]
    source_locator_refs: Tuple[str, ...]
    study_day_anchor_event_ref: Optional[str]
    study_day_zero_exists: Optional[bool]
    timezone: str


@dataclass(frozen=True)
class S5DomainTrack(_Checked):
    applicability_state: Literal["applicable", "not_applicable", "not_provided"]
    domain: Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]
    event_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]
    track_content_hash: str


@dataclass(frozen=True)
class S5JourneyEvent(_Checked):
    applicability_state: Literal["applicable", "not_applicable", "not_provided"]
    domain: Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]
    end_endpoint: S5DateEndpoint
    event_content_hash: str
    event_content_identity: str
    event_ref: str
    geometry: Literal["point", "closed_interval", "open_start", "open_end"]
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    start_endpoint: S5DateEndpoint
    subtype: Literal[
        "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
        "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
        "scale", "outcome", "trend", "protocol_deviation",
    ]
    visit_ref: Optional[str]


@dataclass(frozen=True)
class S5MembershipIndex(_Checked):
    event_refs: Tuple[str, ...]
    membership_content_hash: str
    pending_date_refs: Tuple[str, ...]
    phase_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    visit_refs: Tuple[str, ...]


@dataclass(frozen=True)
class S5PendingDateItem(_Checked):
    domain: Optional[Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]]
    end_endpoint: S5DateEndpoint
    item_kind: Literal["event", "risk", "visit", "phase"]
    item_ref: str
    pending_content_hash: str
    pending_ref: str
    source_locator_refs: Tuple[str, ...]
    start_endpoint: S5DateEndpoint
    target_content_hash: str


@dataclass(frozen=True)
class S5PhaseBand(_Checked):
    end_endpoint: S5DateEndpoint
    geometry: Literal["point", "closed_interval", "open_start", "open_end"]
    phase_content_hash: str
    phase_label_zh: str
    phase_ref: str
    source_locator_refs: Tuple[str, ...]
    start_endpoint: S5DateEndpoint


@dataclass(frozen=True)
class S5RiskAnchor(_Checked):
    domain: Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]
    end_endpoint: S5DateEndpoint
    event_ref: Optional[str]
    geometry: Literal["point", "closed_interval", "open_start", "open_end"]
    risk_anchor_content_hash: str
    risk_anchor_ref: str
    risk_content_identity: str
    risk_ref: str
    risk_type_zh: str
    severity: Literal["critical", "high", "medium", "low"]
    source_locator_refs: Tuple[str, ...]
    start_endpoint: S5DateEndpoint
    visit_ref: Optional[str]


@dataclass(frozen=True)
class S5VisitNode(_Checked):
    accepted_assignment_ref: Optional[str]
    actual_encounter_ref: Optional[str]
    actual_endpoint: Optional[S5DateEndpoint]
    nominal_endpoint: Optional[S5DateEndpoint]
    phase_ref: Optional[str]
    planned_visit_ref: Optional[str]
    source_locator_refs: Tuple[str, ...]
    visit_content_hash: str
    visit_kind: Literal["nominal", "actual", "unscheduled"]
    visit_ref: str


@dataclass(frozen=True)
class S5SubjectTemporalProjection(_Checked):
    axis_basis: S5AxisBasis
    contract_id: str
    domain_tracks: Tuple[S5DomainTrack, ...]
    events: Tuple[S5JourneyEvent, ...]
    fallback_policy: Literal["fail_closed_no_nearest"]
    membership_index: S5MembershipIndex
    pending_date_items: Tuple[S5PendingDateItem, ...]
    phase_bands: Tuple[S5PhaseBand, ...]
    projection_content_hash: str
    projection_id: str
    receipt_ref: str
    risk_anchors: Tuple[S5RiskAnchor, ...]
    schema_version: str
    scope_identity: S5ScopeIdentity
    source_locators: Tuple[S5SourceLocator, ...]
    visits: Tuple[S5VisitNode, ...]


@dataclass(frozen=True)
class S5SubjectTemporalPacket(_Checked):
    packet_content_hash: str
    projection: S5SubjectTemporalProjection
    receipt: S5AuthorityReceipt


@dataclass(frozen=True)
class S5AEMHProjection(_Checked):
    accepted_thread_prefixes: Tuple[S5AEMHPrefixAnchor, ...]
    contract_id: str
    cutoff_endpoint: S5CutoffEndpoint
    fallback_policy: Literal["fail_closed_no_nearest"]
    membership_index: S5AEMHMembershipIndex
    previous_projection_content_hash: Optional[str]
    previous_projection_ref: Optional[str]
    projection_content_hash: str
    projection_id: str
    receipt_ref: str
    schema_version: str
    scope_identity: S5ScopeIdentity
    source_locators: Tuple[S5SourceLocator, ...]
    threads: Tuple[S5AEMHThread, ...]


@dataclass(frozen=True)
class S5AEMHPacket(_Checked):
    packet_content_hash: str
    projection: S5AEMHProjection
    receipt: S5AuthorityReceipt


@dataclass(frozen=True)
class S5DomainEncodingItem(_Checked):
    domain: Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]
    event_shape: Literal[
        "rounded_rect", "bookmark", "capsule", "hexagon", "square",
        "doorframe", "circle", "triangle", "single_flag",
    ]
    line_style: Literal["solid", "dashed", "dot_dash", "step", "trend", "bracket"]
    short_label_zh: str


@dataclass(frozen=True)
class S5SeverityEncoding(_Checked):
    label_zh: str
    line_weight: Optional[int]
    severity: Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True)
class S5LegacyTreatmentMapping(_Checked):
    legacy_kind: Literal["background_treatment", "non_drug_treatment"]
    mapping_authority_ref: Optional[str]
    mapping_state: Literal["mapped", "unmapped_fail_closed"]
    target_domain: Optional[Literal[
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    ]]
    target_subtype: Optional[Literal[
        "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
        "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
        "scale", "outcome", "trend", "protocol_deviation",
    ]]


@dataclass(frozen=True)
class S5AudienceEncodingRegistry(_Checked):
    domain_items: Tuple[S5DomainEncodingItem, ...]
    legacy_treatment_mapping: Tuple[S5LegacyTreatmentMapping, ...]
    risk_overlay_shape: str
    severity_items: Tuple[S5SeverityEncoding, ...]
    symptom_efficacy_subtypes: Tuple[Literal["symptom", "efficacy", "scale", "outcome", "trend"], ...]


@dataclass(frozen=True)
class S5AudienceLexicon(_Checked):
    content_hash: str
    domain_items: Tuple[S5DomainEncodingItem, ...]
    forbidden_terms: Tuple[str, ...]
    severity_items: Tuple[S5SeverityEncoding, ...]
    symptom_efficacy_subtypes: Tuple[Literal["symptom", "efficacy", "scale", "outcome", "trend"], ...]


@dataclass(frozen=True)
class S5SelectionAnchor(_Checked):
    anchor_kind: Literal["none", "event", "risk_anchor", "visit", "source_locator"]
    anchor_ref: Optional[str]
    content_hash: str
    source_locator_ref: Optional[str]

    def __post_init__(self) -> None:
        super().__post_init__()
        expected = s5_navigation_content_hash(self)
        if self.content_hash != expected:
            raise S5HashMismatchError("S5SelectionAnchor.content_hash")


@dataclass(frozen=True)
class S5SharedTemporalContext(_Checked):
    authority_receipt_ref: str
    axis_mode: Literal["calendar", "study_day"]
    content_hash: str
    context_ref: str
    selected_event_ref: Optional[str]
    selected_risk_anchor_ref: Optional[str]
    selected_visit_ref: Optional[str]
    selection_anchor: S5SelectionAnchor
    spine_ref: str
    window_end: Optional[date]
    window_start: Optional[date]

    def __post_init__(self) -> None:
        super().__post_init__()
        expected_ref = s5_context_ref(
            self.authority_receipt_ref, self.spine_ref, self.axis_mode,
            self.window_start, self.window_end, self.selection_anchor,
            self.selected_event_ref, self.selected_risk_anchor_ref, self.selected_visit_ref,
        )
        if self.context_ref != expected_ref:
            raise S5HashMismatchError("S5SharedTemporalContext.context_ref")
        if self.content_hash != s5_navigation_content_hash(self):
            raise S5HashMismatchError("S5SharedTemporalContext.content_hash")


@dataclass(frozen=True)
class S5ViewBinding(_Checked):
    anchor_ref: Optional[str]
    authority_projection_id: str
    content_hash: str
    shared_context_ref: str
    spine_ref: str
    view: Literal["journey", "profile", "timeline"]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.content_hash != s5_view_binding_hash(self):
            raise S5HashMismatchError("S5ViewBinding.content_hash")


@dataclass(frozen=True)
class S5SubjectWorkspaceContract(_Checked):
    authority_receipt_refs: Tuple[str, ...]
    content_hash: str
    shared_context: S5SharedTemporalContext
    spine_ref: str
    subject_ref: str
    view_bindings: Tuple[S5ViewBinding, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.content_hash != s5_workspace_hash(self):
            raise S5HashMismatchError("S5SubjectWorkspaceContract.content_hash")


def build_audience_encoding_registry() -> S5AudienceEncodingRegistry:
    domains = tuple(
        S5DomainEncodingItem(domain=domain, event_shape=shape, line_style=line, short_label_zh=label)
        for domain, (shape, line, label) in DOMAIN_ENCODING.items()
    )
    severities = tuple(S5SeverityEncoding(label_zh=SEVERITY_ZH[level], line_weight=None, severity=level)
                       for level in SEVERITIES)
    treatment = tuple(S5LegacyTreatmentMapping(
        legacy_kind=kind, mapping_authority_ref=None,
        mapping_state="unmapped_fail_closed", target_domain=None, target_subtype=None,
    ) for kind in LEGACY_TREATMENT_KINDS)
    return S5AudienceEncodingRegistry(
        domain_items=domains,
        legacy_treatment_mapping=treatment,
        risk_overlay_shape=RISK_OVERLAY_SHAPE,
        severity_items=severities,
        symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES,
    )


def build_audience_lexicon() -> S5AudienceLexicon:
    registry = build_audience_encoding_registry()
    return S5AudienceLexicon(
        content_hash=s5_sha256({
            "domain_items": registry.domain_items,
            "forbidden_terms": FORBIDDEN_AUDIENCE_TERMS,
            "severity_items": registry.severity_items,
            "symptom_efficacy_subtypes": registry.symptom_efficacy_subtypes,
        }),
        domain_items=registry.domain_items,
        forbidden_terms=FORBIDDEN_AUDIENCE_TERMS,
        severity_items=registry.severity_items,
        symptom_efficacy_subtypes=registry.symptom_efficacy_subtypes,
    )


# Familiar names used by the earlier R5 typed-contract slices.  They are
# aliases only; there is still one canonicalization implementation above.
canonical_json = s5_canonical_json
canonical_sha256 = s5_sha256
content_hash = s5_sha256
s5_packet_as_mapping = s5_as_mapping
S5_CONTRACT_SCHEMA_ID = S5_SCHEMA
S5_RUNTIME_CONTRACT_ID = S5_CONTRACT_ID
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json"


__all__ = [name for name in globals() if name.startswith("S5") or name in {
    "AEMH_DOMAINS", "APPLICABILITY_STATES", "AXIS_MODES", "CUTOFF_ENDPOINT_STATES",
    "CUTOFF_STATES", "DATE_GEOMETRIES", "DATE_STATES", "DOMAINS", "EVENT_SHAPES",
    "FALLBACK_POLICIES", "HISTORY_EVENT_KINDS", "IDENTITY_EVIDENCE_KINDS", "JOURNEY_SUBTYPES",
    "LEGACY_MAPPING_STATES", "LEGACY_SEVERITY_MAPPING", "LEGACY_TREATMENT_KINDS",
    "LINE_STYLES", "MATCH_STATES", "PENDING_ITEM_KINDS", "RECEIPT_VARIANTS",
    "RISK_LIFECYCLE_EFFECTS", "S5_ANCHOR_KINDS", "S5_PROJECTION_KINDS", "S5_VIEWS",
    "SEVERITIES", "SEVERITY_ZH", "SOURCE_LOCATOR_VARIANTS", "SYMPTOM_EFFICACY_SUBTYPES",
    "VISIBILITY_STATES", "VISIT_KINDS", "DOMAIN_SUBTYPE_MATRIX", "DOMAIN_ENCODING",
    "RISK_OVERLAY_SHAPE", "FORBIDDEN_AUDIENCE_TERMS", "s5_canonical_json", "s5_canonical_bytes",
    "s5_sha256", "s5_canonical_hash", "s5_as_mapping", "packet_as_mapping",
    "s5_packet_as_mapping", "canonical_json", "canonical_sha256", "content_hash",
    "s5_navigation_content_hash", "s5_view_binding_hash", "s5_workspace_hash", "s5_context_ref",
    "is_sha256_hex", "build_audience_encoding_registry", "build_audience_lexicon",
    "S5_CONTRACT_SCHEMA_ID", "S5_RUNTIME_CONTRACT_ID", "HASH_CANONICALIZATION",
}]
