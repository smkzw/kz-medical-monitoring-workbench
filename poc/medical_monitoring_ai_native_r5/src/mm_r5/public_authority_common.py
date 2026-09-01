"""Immutable R5-S5 public-authority primitives.

The public producers consume one frozen ``AuthorityBundleV02``.  This module
contains the lossless typed input records, the shared packet records, and the
small canonical/hash helpers used by the two producers.  It deliberately has
no file, network, subprocess, reflection, or prior-stage runtime dependency.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Tuple, Union


SUBJECT_CONTRACT_ID = "subject-temporal-public-v1"
AEMH_CONTRACT_ID = "aemh-match-history-public-v1"
PUBLIC_SCHEMA_VERSION = "2026-08-19.1"
TEMPORAL_V02_CONTRACT_ID = "r5-s5-temporal-projection-authority-delta-v0.2"
TEMPORAL_V02_SCHEMA_VERSION = "2026-08-21.1"
TEMPORAL_V01_MANIFEST_SHA256 = (
    "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97"
)
AUDIENCE_CONTRACT_ID = "contract.s4.1"
FALLBACK_POLICY = "fail_closed_no_nearest"

DOMAINS: Tuple[str, ...] = (
    "ae",
    "mh",
    "cm",
    "ip",
    "lab_exam",
    "hospital_procedure",
    "symptom_efficacy",
    "protocol_compliance",
)
AEMH_DOMAINS: Tuple[str, ...] = ("ae", "mh")
AEMH_EVENT_KINDS: Tuple[str, ...] = (
    "reminder_created",
    "match_decided",
    "withdrawn",
    "reappeared",
)
AEMH_MATCH_STATES: Tuple[str, ...] = ("exact", "ambiguous", "rejected")
AXIS_MODES: Tuple[str, ...] = ("calendar", "study_day")
DAY_ZERO_CONVENTIONS: Tuple[str, ...] = ("anchor_day_zero", "anchor_day_one")
CUTOFF_BINDING_STATES: Tuple[str, ...] = ("present", "absent")
DATE_STATES: Tuple[str, ...] = ("exact", "partial", "conflicted", "missing")
DATE_GEOMETRIES: Tuple[str, ...] = (
    "point",
    "closed_interval",
    "open_start",
    "open_end",
)
APPLICABILITY_STATES: Tuple[str, ...] = (
    "applicable",
    "not_applicable",
    "not_provided",
)
JOURNEY_SUBTYPES: Tuple[str, ...] = (
    "ae",
    "mh",
    "concomitant_medication",
    "ip_dose",
    "ip_pause",
    "ip_resume",
    "lab",
    "exam",
    "hospitalization",
    "procedure",
    "symptom",
    "efficacy",
    "scale",
    "outcome",
    "trend",
    "protocol_deviation",
)
PENDING_ITEM_KINDS: Tuple[str, ...] = ("visit", "event", "risk", "phase")
SEVERITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")


# ---------------------------------------------------------------------------
# Frozen AuthorityBundleV02 input records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AEMHDecisionInputV02:
    considered_fact_refs: Tuple[str, ...]
    decision_ref: str
    event_kind: Literal["reminder_created", "match_decided", "withdrawn", "reappeared"]
    fact_refs: Tuple[str, ...]
    match_state: Optional[Literal["exact", "ambiguous", "rejected"]]
    reason_code: str
    thread_ref: str


@dataclass(frozen=True)
class AEMHThreadInputV02:
    candidate_locator_ref: str
    candidate_ref: str
    domain: Literal["ae", "mh"]
    reminder_reason: str
    thread_ref: str


@dataclass(frozen=True)
class AxisInputV02:
    anchor_event_ref: Optional[str]
    axis_ref: str
    day_zero_convention: Literal["anchor_day_zero", "anchor_day_one"]
    mode: Literal["calendar", "study_day"]
    study_day_enabled: bool
    timezone: str


@dataclass(frozen=True)
class CutoffEndpointBindingV02:
    exact_date: Optional[str]
    source_locator_refs: Tuple[str, ...]
    state: Literal["present", "absent"]


@dataclass(frozen=True)
class DomainInputV02:
    domain: Literal[
        "ae",
        "mh",
        "cm",
        "ip",
        "lab_exam",
        "hospital_procedure",
        "symptom_efficacy",
        "protocol_compliance",
    ]
    event_refs: Tuple[str, ...]
    risk_refs: Tuple[str, ...]
    state: str


@dataclass(frozen=True)
class EndpointInputV02:
    candidates: Tuple[str, ...]
    exact_date: Optional[str]
    locator_refs: Tuple[str, ...]
    projectable: bool
    range_authorized: bool
    range_end: Optional[str]
    range_start: Optional[str]
    state: str
    study_day: Optional[int]


@dataclass(frozen=True)
class IdentityScopeInputV02:
    project_ref: str
    run_ref: str
    site_ref: str
    snapshot_ref: str
    spine_ref: str
    subject_ref: str


@dataclass(frozen=True)
class LocatorInputV02:
    anchor: str
    authority_domain: Optional[str]
    authority_thread_ref: Optional[str]
    entity_kind: Optional[str]
    entity_ref: Optional[str]
    locator_ref: str
    record_ref: str
    revision_content_identity: str
    revision_ref: str
    snapshot_ref: str


@dataclass(frozen=True)
class PhaseInputV02:
    end: EndpointInputV02
    geometry: str
    label_zh: str
    locator_refs: Tuple[str, ...]
    phase_ref: str
    start: EndpointInputV02


@dataclass(frozen=True)
class RevisionInputV02:
    locator_refs: Tuple[str, ...]
    revision_content_identity: str
    revision_ref: str


@dataclass(frozen=True)
class RiskInputV02:
    content_identity: str
    domain: Literal[
        "ae",
        "mh",
        "cm",
        "ip",
        "lab_exam",
        "hospital_procedure",
        "symptom_efficacy",
        "protocol_compliance",
    ]
    end: EndpointInputV02
    event_ref: str
    geometry: str
    locator_refs: Tuple[str, ...]
    risk_anchor_ref: str
    risk_ref: str
    risk_type_zh: str
    severity: str
    start: EndpointInputV02
    visit_ref: str


@dataclass(frozen=True)
class ScopeInputV02:
    cutoff_ref: str
    project_ref: str
    run_ref: str
    site_ref: str
    snapshot_ref: str
    spine_ref: str
    subject_ref: str


@dataclass(frozen=True)
class SubjectEventInputV02:
    content_identity: str
    domain: Literal[
        "ae",
        "mh",
        "cm",
        "ip",
        "lab_exam",
        "hospital_procedure",
        "symptom_efficacy",
        "protocol_compliance",
    ]
    end: EndpointInputV02
    event_ref: str
    geometry: str
    locator_refs: Tuple[str, ...]
    risk_refs: Tuple[str, ...]
    start: EndpointInputV02
    subtype: str
    visit_ref: Optional[str]


@dataclass(frozen=True)
class VisitInputV02:
    actual: EndpointInputV02
    actual_encounter_ref: str
    assignment_ref: str
    locator_refs: Tuple[str, ...]
    nominal: EndpointInputV02
    phase_ref: str
    planned_visit_ref: str
    visit_ref: str


@dataclass(frozen=True)
class SubjectFullGraphInputV02:
    axis: AxisInputV02
    cutoff_binding: CutoffEndpointBindingV02
    domain_applicability: Tuple[DomainInputV02, ...]
    events: Tuple[SubjectEventInputV02, ...]
    locator_specs: Tuple[LocatorInputV02, ...]
    phase: PhaseInputV02
    revision_specs: Tuple[RevisionInputV02, ...]
    risk: RiskInputV02
    scope: IdentityScopeInputV02
    visit: VisitInputV02


@dataclass(frozen=True)
class AEMHFullGraphInputV02:
    current_locator_specs: Tuple[LocatorInputV02, ...]
    current_revision_specs: Tuple[RevisionInputV02, ...]
    current_scope: ScopeInputV02
    decision_records: Tuple[AEMHDecisionInputV02, ...]
    previous_locator_specs: Tuple[LocatorInputV02, ...]
    previous_revision_specs: Tuple[RevisionInputV02, ...]
    previous_scope: ScopeInputV02
    thread_specs: Tuple[AEMHThreadInputV02, ...]


@dataclass(frozen=True)
class AuthorityBundleV02:
    authority_scope: Literal["synthetic_test_only"]
    bundle_content_identity: str
    contract_id: str
    execution_profile: Literal["full_parent_graph"]
    schema_version: str
    source: Union[SubjectFullGraphInputV02, AEMHFullGraphInputV02]
    target_contract: Literal["subject-temporal-public-v1", "aemh-match-history-public-v1"]
    temporal_v01_manifest_sha256: str


# ---------------------------------------------------------------------------
# Shared public packet records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicScopeIdentity:
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
class PublicCutoffEndpoint:
    cutoff_content_hash: str
    exact_date: Optional[str]
    source_locator_refs: Tuple[str, ...]
    state: Literal["present", "absent"]


@dataclass(frozen=True)
class PublicSourceLocator:
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
class SourceRevisionContentPair:
    accepted_content_hash: str
    locator_refs: Tuple[str, ...]
    pair_content_hash: str
    revision_id: str


@dataclass(frozen=True)
class VisibilityClosure:
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
class PublicAuthorityReceipt:
    audience_contract_id: str
    authority_contract_id: str
    authority_contract_version: str
    evaluation_content_identities: Tuple[str, ...]
    public_projection_content_hash: str
    public_projection_id: str
    receipt_content_hash: str
    receipt_id: str
    receipt_variant: Literal["subject_temporal", "aemh_match_history"]
    scope_identity: PublicScopeIdentity
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    visibility_closure: VisibilityClosure


# ---------------------------------------------------------------------------
# Validation result records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicAuthorityValidationIssue:
    code: str
    path: str
    message: str
    origin: Literal["parent", "semantic_delta", "temporal_delta", "consumer"]
    priority: int


@dataclass(frozen=True)
class PublicAuthorityValidationResult:
    ok: bool
    primary_code: Optional[str]
    issues: Tuple[PublicAuthorityValidationIssue, ...]
    packet_emitted: bool


@dataclass(frozen=True)
class PublicAuthorityConstructionError(RuntimeError):
    result: PublicAuthorityValidationResult

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.result.primary_code or "PUBLIC_AUTHORITY_CONSTRUCTION_FAILED")


# ---------------------------------------------------------------------------
# Canonical helpers
# ---------------------------------------------------------------------------


def _canonicalize(value: object) -> object:
    if dataclasses.is_dataclass(value):
        return _canonicalize(dataclasses.asdict(value))
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): _canonicalize(value[key])
            for key in sorted(value, key=_canonical_key)
        }
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    return value


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _canonical_key(value: object) -> str:
    return str(value)


def without_field(value: object, field_name: str) -> object:
    """Return a canonical-hash input with one dataclass/dict field removed."""
    if dataclasses.is_dataclass(value):
        mapped = dataclasses.asdict(value)
        return {
            key: mapped[key]
            for key in mapped
            if key != field_name
        }
    if isinstance(value, dict):
        return {key: value[key] for key in value if key != field_name}
    raise TypeError("hash input must be a dataclass or dict")


def validation_result(
    issues: Iterable[PublicAuthorityValidationIssue],
) -> PublicAuthorityValidationResult:
    ordered = tuple(sorted(issues, key=_issue_key))
    return PublicAuthorityValidationResult(
        ok=not ordered,
        primary_code=ordered[0].code if ordered else None,
        issues=ordered,
        packet_emitted=not ordered,
    )


def issue(
    code: str,
    path: str,
    *,
    origin: Literal["parent", "semantic_delta", "temporal_delta", "consumer"] = "temporal_delta",
    priority: int = 100,
) -> PublicAuthorityValidationIssue:
    return PublicAuthorityValidationIssue(
        code=code,
        path=path,
        message=f"{origin}:{code}:fail_closed",
        origin=origin,
        priority=priority,
    )


def _issue_key(item: PublicAuthorityValidationIssue) -> tuple:
    return (item.priority, item.path, item.code, item.origin, item.message)


def fail(result: PublicAuthorityValidationResult) -> None:
    raise PublicAuthorityConstructionError(result)


def _text(value: object) -> bool:
    return type(value) is str


def _optional_text(value: object) -> bool:
    return value is None or type(value) is str


def _bool(value: object) -> bool:
    return type(value) is bool


def _optional_int(value: object) -> bool:
    return value is None or type(value) is int


def _text_tuple(value: object) -> bool:
    return type(value) is tuple and all(_text(item) for item in value)


def _enum(value: object, values: Tuple[str, ...]) -> bool:
    return type(value) is str and value in values


def _optional_enum(value: object, values: Tuple[str, ...]) -> bool:
    return value is None or _enum(value, values)


def _sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _shape_endpoint(value: object) -> bool:
    if type(value) is not EndpointInputV02:
        return False
    return (
        _text_tuple(value.candidates)
        and _optional_text(value.exact_date)
        and _text_tuple(value.locator_refs)
        and _bool(value.projectable)
        and _bool(value.range_authorized)
        and _optional_text(value.range_end)
        and _optional_text(value.range_start)
        and _text(value.state)
        and _optional_int(value.study_day)
    )


def _shape_locator(value: object) -> bool:
    if type(value) is not LocatorInputV02:
        return False
    return (
        _text(value.anchor)
        and _optional_text(value.authority_domain)
        and _optional_text(value.authority_thread_ref)
        and _optional_text(value.entity_kind)
        and _optional_text(value.entity_ref)
        and _text(value.locator_ref)
        and _text(value.record_ref)
        and _sha256(value.revision_content_identity)
        and _text(value.revision_ref)
        and _text(value.snapshot_ref)
    )


def _shape_revision(value: object) -> bool:
    if type(value) is not RevisionInputV02:
        return False
    return (
        _text_tuple(value.locator_refs)
        and _sha256(value.revision_content_identity)
        and _text(value.revision_ref)
    )


def _shape_scope(value: object) -> bool:
    if type(value) is not ScopeInputV02:
        return False
    return (
        _text(value.cutoff_ref)
        and _text(value.project_ref)
        and _text(value.run_ref)
        and _text(value.site_ref)
        and _text(value.snapshot_ref)
        and _text(value.spine_ref)
        and _text(value.subject_ref)
    )


def _shape_identity_scope(value: object) -> bool:
    if type(value) is not IdentityScopeInputV02:
        return False
    return (
        _text(value.project_ref)
        and _text(value.run_ref)
        and _text(value.site_ref)
        and _text(value.snapshot_ref)
        and _text(value.spine_ref)
        and _text(value.subject_ref)
    )


def _shape_axis(value: object) -> bool:
    if type(value) is not AxisInputV02:
        return False
    return (
        _optional_text(value.anchor_event_ref)
        and _text(value.axis_ref)
        and _enum(value.day_zero_convention, DAY_ZERO_CONVENTIONS)
        and _enum(value.mode, AXIS_MODES)
        and _bool(value.study_day_enabled)
        and _text(value.timezone)
    )


def _shape_cutoff(value: object) -> bool:
    if type(value) is not CutoffEndpointBindingV02:
        return False
    return (
        _optional_text(value.exact_date)
        and _text_tuple(value.source_locator_refs)
        and _enum(value.state, CUTOFF_BINDING_STATES)
    )


def _shape_domain(value: object) -> bool:
    if type(value) is not DomainInputV02:
        return False
    return (
        _enum(value.domain, DOMAINS)
        and _text_tuple(value.event_refs)
        and _text_tuple(value.risk_refs)
        and _text(value.state)
    )


def _shape_phase(value: object) -> bool:
    if type(value) is not PhaseInputV02:
        return False
    return (
        _shape_endpoint(value.end)
        and _text(value.geometry)
        and _text(value.label_zh)
        and _text_tuple(value.locator_refs)
        and _text(value.phase_ref)
        and _shape_endpoint(value.start)
    )


def _shape_risk(value: object) -> bool:
    if type(value) is not RiskInputV02:
        return False
    return (
        _sha256(value.content_identity)
        and _enum(value.domain, DOMAINS)
        and _shape_endpoint(value.end)
        and _text(value.event_ref)
        and _text(value.geometry)
        and _text_tuple(value.locator_refs)
        and _text(value.risk_anchor_ref)
        and _text(value.risk_ref)
        and _text(value.risk_type_zh)
        and _text(value.severity)
        and _shape_endpoint(value.start)
        and _text(value.visit_ref)
    )


def _shape_event(value: object) -> bool:
    if type(value) is not SubjectEventInputV02:
        return False
    return (
        _sha256(value.content_identity)
        and _enum(value.domain, DOMAINS)
        and _shape_endpoint(value.end)
        and _text(value.event_ref)
        and _text(value.geometry)
        and _text_tuple(value.locator_refs)
        and _text_tuple(value.risk_refs)
        and _shape_endpoint(value.start)
        and _text(value.subtype)
        and _optional_text(value.visit_ref)
    )


def _shape_visit(value: object) -> bool:
    if type(value) is not VisitInputV02:
        return False
    return (
        _shape_endpoint(value.actual)
        and _text(value.actual_encounter_ref)
        and _text(value.assignment_ref)
        and _text_tuple(value.locator_refs)
        and _shape_endpoint(value.nominal)
        and _text(value.phase_ref)
        and _text(value.planned_visit_ref)
        and _text(value.visit_ref)
    )


def _shape_decision(value: object) -> bool:
    if type(value) is not AEMHDecisionInputV02:
        return False
    return (
        _text_tuple(value.considered_fact_refs)
        and _text(value.decision_ref)
        and _enum(value.event_kind, AEMH_EVENT_KINDS)
        and _text_tuple(value.fact_refs)
        and _optional_enum(value.match_state, AEMH_MATCH_STATES)
        and _text(value.reason_code)
        and _text(value.thread_ref)
    )


def _shape_thread(value: object) -> bool:
    if type(value) is not AEMHThreadInputV02:
        return False
    return (
        _text(value.candidate_locator_ref)
        and _text(value.candidate_ref)
        and _enum(value.domain, AEMH_DOMAINS)
        and _text(value.reminder_reason)
        and _text(value.thread_ref)
    )


def _shape_subject(value: object) -> bool:
    if type(value) is not SubjectFullGraphInputV02:
        return False
    return (
        _shape_axis(value.axis)
        and _shape_cutoff(value.cutoff_binding)
        and type(value.domain_applicability) is tuple
        and all(_shape_domain(item) for item in value.domain_applicability)
        and type(value.events) is tuple
        and all(_shape_event(item) for item in value.events)
        and type(value.locator_specs) is tuple
        and all(_shape_locator(item) for item in value.locator_specs)
        and _shape_phase(value.phase)
        and type(value.revision_specs) is tuple
        and all(_shape_revision(item) for item in value.revision_specs)
        and _shape_risk(value.risk)
        and _shape_identity_scope(value.scope)
        and _shape_visit(value.visit)
    )


def _shape_aemh(value: object) -> bool:
    if type(value) is not AEMHFullGraphInputV02:
        return False
    return (
        type(value.current_locator_specs) is tuple
        and all(_shape_locator(item) for item in value.current_locator_specs)
        and type(value.current_revision_specs) is tuple
        and all(_shape_revision(item) for item in value.current_revision_specs)
        and _shape_scope(value.current_scope)
        and type(value.decision_records) is tuple
        and all(_shape_decision(item) for item in value.decision_records)
        and type(value.previous_locator_specs) is tuple
        and all(_shape_locator(item) for item in value.previous_locator_specs)
        and type(value.previous_revision_specs) is tuple
        and all(_shape_revision(item) for item in value.previous_revision_specs)
        and _shape_scope(value.previous_scope)
        and type(value.thread_specs) is tuple
        and all(_shape_thread(item) for item in value.thread_specs)
    )


def _authority_shape_ok(value: object) -> bool:
    if type(value) is not AuthorityBundleV02:
        return False
    return (
        _enum(value.authority_scope, ("synthetic_test_only",))
        and _sha256(value.bundle_content_identity)
        and _text(value.contract_id)
        and _enum(value.execution_profile, ("full_parent_graph",))
        and _text(value.schema_version)
        and (_shape_subject(value.source) or _shape_aemh(value.source))
        and _enum(value.target_contract, (SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID))
        and _sha256(value.temporal_v01_manifest_sha256)
    )


def authority_issues(
    authority: object,
    target_contract: str,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    if type(authority) is not AuthorityBundleV02:
        return (issue("PUB_TYPE_MISMATCH", "/authority", origin="parent", priority=1),)
    if not _authority_shape_ok(authority):
        return (issue("PUB_TYPE_MISMATCH", "/authority", origin="parent", priority=1),)
    checks = (
        (authority.target_contract == target_contract, "PUB_TARGET_CONTRACT_MISMATCH", "/target_contract"),
        (authority.contract_id == TEMPORAL_V02_CONTRACT_ID, "PUB_AUTHORITY_CONTRACT_MISMATCH", "/contract_id"),
        (authority.schema_version == TEMPORAL_V02_SCHEMA_VERSION, "PUB_AUTHORITY_SCHEMA_MISMATCH", "/schema_version"),
        (authority.authority_scope == "synthetic_test_only", "PUB_AUTHORITY_SCOPE_MISMATCH", "/authority_scope"),
        (authority.execution_profile == "full_parent_graph", "PUB_AUTHORITY_PROFILE_MISMATCH", "/execution_profile"),
        (authority.temporal_v01_manifest_sha256 == TEMPORAL_V01_MANIFEST_SHA256, "PUB_AUTHORITY_PIN_MISMATCH", "/temporal_v01_manifest_sha256"),
        (len(authority.bundle_content_identity) == 64 and authority.bundle_content_identity == canonical_sha256(without_field(authority, "bundle_content_identity")), "PUB_AUTHORITY_IDENTITY_MISMATCH", "/bundle_content_identity"),
    )
    result = [issue(code, path, origin="temporal_delta", priority=10) for ok, code, path in checks if not ok]
    if target_contract == SUBJECT_CONTRACT_ID and not isinstance(authority.source, SubjectFullGraphInputV02):
        result.append(issue("PUB_TYPE_MISMATCH", "/source", origin="parent", priority=1))
    if target_contract == AEMH_CONTRACT_ID and not isinstance(authority.source, AEMHFullGraphInputV02):
        result.append(issue("PUB_TYPE_MISMATCH", "/source", origin="parent", priority=1))
    return tuple(result)


def make_scope_identity(
    *,
    project_ref: str,
    run_ref: str,
    site_ref: str,
    snapshot_ref: str,
    spine_ref: str,
    subject_ref: str,
    cutoff_state: Literal["present", "absent"],
    cutoff_ref: Optional[str],
) -> PublicScopeIdentity:
    core = {
        "project_ref": project_ref,
        "run_ref": run_ref,
        "site_ref": site_ref,
        "snapshot_ref": snapshot_ref,
        "spine_ref": spine_ref,
        "subject_ref": subject_ref,
        "cutoff_state": cutoff_state,
        "cutoff_ref": cutoff_ref,
    }
    return PublicScopeIdentity(
        cutoff_ref=cutoff_ref,
        cutoff_state=cutoff_state,
        identity_content_hash=canonical_sha256(core),
        project_ref=project_ref,
        run_ref=run_ref,
        site_ref=site_ref,
        snapshot_ref=snapshot_ref,
        spine_ref=spine_ref,
        subject_ref=subject_ref,
    )


def make_source_locator(spec: LocatorInputV02) -> PublicSourceLocator:
    raw_payload_hash = canonical_sha256({"record": spec.record_ref, "anchor": spec.anchor})
    core = {
        "locator_ref": spec.locator_ref,
        "locator_variant": "r4_source_locator",
        "snapshot_ref": spec.snapshot_ref,
        "source_revision_ref": spec.revision_ref,
        "source_revision_content_hash": spec.revision_content_identity,
        "source_file_ref": None,
        "table_semantic": "synthetic_listing",
        "record_ref": spec.record_ref,
        "authority_entity_kind": spec.entity_kind,
        "authority_entity_ref": spec.entity_ref,
        "column_or_anchor": spec.anchor,
        "canonical_location": None,
        "raw_payload_hash": raw_payload_hash,
    }
    return PublicSourceLocator(
        authority_entity_kind=spec.entity_kind,
        authority_entity_ref=spec.entity_ref,
        canonical_location=None,
        column_or_anchor=spec.anchor,
        locator_content_hash=canonical_sha256(core),
        locator_ref=spec.locator_ref,
        locator_variant="r4_source_locator",
        raw_payload_hash=raw_payload_hash,
        record_ref=spec.record_ref,
        snapshot_ref=spec.snapshot_ref,
        source_file_ref=None,
        source_revision_content_hash=spec.revision_content_identity,
        source_revision_ref=spec.revision_ref,
        table_semantic="synthetic_listing",
    )


def make_source_pairs(
    specs: Tuple[RevisionInputV02, ...],
) -> Tuple[SourceRevisionContentPair, ...]:
    values = []
    seen_revision_refs = set()
    seen_locator_refs = set()
    for spec in specs:
        if spec.revision_ref in seen_revision_refs:
            raise ValueError("PUB_SOURCE_REVISION_DUPLICATE")
        seen_revision_refs.add(spec.revision_ref)
        locator_refs = tuple(sorted(spec.locator_refs))
        if not locator_refs:
            raise ValueError("PUB_SOURCE_REVISION_EMPTY")
        if len(locator_refs) != len(set(locator_refs)):
            raise ValueError("PUB_SOURCE_LOCATOR_DUPLICATE")
        if any(locator_ref in seen_locator_refs for locator_ref in locator_refs):
            raise ValueError("PUB_SOURCE_REVISION_OVERLAP")
        seen_locator_refs.update(locator_refs)
        core = {
            "revision_id": spec.revision_ref,
            "accepted_content_hash": spec.revision_content_identity,
            "locator_refs": locator_refs,
        }
        values.append(SourceRevisionContentPair(
            accepted_content_hash=spec.revision_content_identity,
            locator_refs=locator_refs,
            pair_content_hash=canonical_sha256(core),
            revision_id=spec.revision_ref,
        ))
    return tuple(sorted(values, key=_revision_pair_key))


def _revision_pair_key(item: SourceRevisionContentPair) -> str:
    return item.revision_id


def make_visibility(scope: PublicScopeIdentity) -> VisibilityClosure:
    core = {
        "visibility_decision_id": f"visibility::{scope.subject_ref}::{scope.snapshot_ref}",
        "visibility_decision_hash": canonical_sha256({
            "project_ref": scope.project_ref,
            "run_ref": scope.run_ref,
            "snapshot_ref": scope.snapshot_ref,
            "cutoff_state": scope.cutoff_state,
            "cutoff_ref": scope.cutoff_ref,
            "site_ref": scope.site_ref,
            "subject_ref": scope.subject_ref,
            "spine_ref": scope.spine_ref,
            "state": "projectable",
        }),
        "evaluation_member_refs": (scope.subject_ref,),
        "evaluation_site_refs": (scope.site_ref,),
        "projectable_member_refs": (scope.subject_ref,),
        "projectable_site_refs": (scope.site_ref,),
        "hidden_member_refs": (),
        "hidden_site_refs": (),
        "hidden_member_count": 0,
        "hidden_site_count": 0,
        "subject_visibility_state": "projectable",
        "deep_link_eligible": True,
    }
    return VisibilityClosure(
        closure_content_hash=canonical_sha256(core),
        deep_link_eligible=True,
        evaluation_member_refs=(scope.subject_ref,),
        evaluation_site_refs=(scope.site_ref,),
        hidden_member_count=0,
        hidden_member_refs=(),
        hidden_site_count=0,
        hidden_site_refs=(),
        projectable_member_refs=(scope.subject_ref,),
        projectable_site_refs=(scope.site_ref,),
        subject_visibility_state="projectable",
        visibility_decision_hash=core["visibility_decision_hash"],
        visibility_decision_id=core["visibility_decision_id"],
    )


def make_receipt(
    *,
    receipt_variant: Literal["subject_temporal", "aemh_match_history"],
    authority_contract_id: str,
    scope: PublicScopeIdentity,
    projection_id: str,
    projection_content_hash: str,
    evaluation_content_identities: Tuple[str, ...],
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...],
) -> PublicAuthorityReceipt:
    receipt_id = canonical_sha256({
        "receipt_variant": receipt_variant,
        "authority_contract_id": authority_contract_id,
        "scope_identity_hash": scope.identity_content_hash,
        "public_projection_id": projection_id,
    })
    visibility = make_visibility(scope)
    core = {
        "receipt_id": receipt_id,
        "receipt_variant": receipt_variant,
        "authority_contract_id": authority_contract_id,
        "authority_contract_version": PUBLIC_SCHEMA_VERSION,
        "scope_identity": scope,
        "public_projection_id": projection_id,
        "public_projection_content_hash": projection_content_hash,
        "evaluation_content_identities": evaluation_content_identities,
        "visibility_closure": visibility,
        "source_revision_content_pairs": source_revision_content_pairs,
        "audience_contract_id": AUDIENCE_CONTRACT_ID,
    }
    return PublicAuthorityReceipt(
        audience_contract_id=AUDIENCE_CONTRACT_ID,
        authority_contract_id=authority_contract_id,
        authority_contract_version=PUBLIC_SCHEMA_VERSION,
        evaluation_content_identities=evaluation_content_identities,
        public_projection_content_hash=projection_content_hash,
        public_projection_id=projection_id,
        receipt_content_hash=canonical_sha256(core),
        receipt_id=receipt_id,
        receipt_variant=receipt_variant,
        scope_identity=scope,
        source_revision_content_pairs=source_revision_content_pairs,
        visibility_closure=visibility,
    )
