"""R5-S5 subject-temporal public-authority producer.

Only ``AuthorityBundleV02`` is accepted at the public builder boundary.  The
builder reconstructs the packet from the frozen source graph and never accepts
an output packet, external path, or prior-stage runtime object as authority.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional, Tuple

from mm_r5.public_authority_common import (
    APPLICABILITY_STATES,
    AXIS_MODES,
    AuthorityBundleV02,
    DATE_GEOMETRIES,
    DATE_STATES,
    DAY_ZERO_CONVENTIONS,
    DOMAINS,
    EndpointInputV02,
    FALLBACK_POLICY,
    IdentityScopeInputV02,
    JOURNEY_SUBTYPES,
    PENDING_ITEM_KINDS,
    PublicAuthorityReceipt,
    PublicAuthorityValidationIssue,
    PublicAuthorityValidationResult,
    PublicScopeIdentity,
    PublicSourceLocator,
    SourceRevisionContentPair,
    SubjectFullGraphInputV02,
    SEVERITIES,
    authority_issues,
    canonical_sha256,
    fail,
    issue,
    make_receipt,
    make_scope_identity,
    make_source_locator,
    make_source_pairs,
    validation_result,
)


@dataclass(frozen=True)
class TemporalDateEndpoint:
    candidate_values: Tuple[str, ...]
    endpoint_content_hash: str
    exact_date: Optional[str]
    main_axis_projectable: bool
    range_end: Optional[str]
    range_projection_authorized: bool
    range_start: Optional[str]
    source_locator_refs: Tuple[str, ...]
    state: str
    study_day: Optional[int]


@dataclass(frozen=True)
class TemporalAxisBasis:
    axis_content_hash: str
    axis_ref: str
    cutoff_endpoint: TemporalDateEndpoint
    default_axis_mode: Literal["calendar", "study_day"]
    source_locator_refs: Tuple[str, ...]
    study_day_anchor_event_ref: Optional[str]
    study_day_zero_exists: Optional[bool]
    timezone: str


@dataclass(frozen=True)
class TemporalDomainTrack:
    applicability_state: str
    domain: str
    event_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]
    track_content_hash: str


@dataclass(frozen=True)
class TemporalEvent:
    applicability_state: str
    domain: str
    end_endpoint: TemporalDateEndpoint
    event_content_hash: str
    event_content_identity: str
    event_ref: str
    geometry: str
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    start_endpoint: TemporalDateEndpoint
    subtype: str
    visit_ref: Optional[str]


@dataclass(frozen=True)
class TemporalMembershipIndex:
    event_refs: Tuple[str, ...]
    membership_content_hash: str
    pending_date_refs: Tuple[str, ...]
    phase_refs: Tuple[str, ...]
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    visit_refs: Tuple[str, ...]


@dataclass(frozen=True)
class TemporalPendingDateItem:
    domain: Optional[str]
    end_endpoint: TemporalDateEndpoint
    item_kind: Literal["visit", "event", "risk", "phase"]
    item_ref: str
    pending_content_hash: str
    pending_ref: str
    source_locator_refs: Tuple[str, ...]
    start_endpoint: TemporalDateEndpoint
    target_content_hash: str


@dataclass(frozen=True)
class TemporalPhaseBand:
    end_endpoint: TemporalDateEndpoint
    geometry: str
    phase_content_hash: str
    phase_label_zh: str
    phase_ref: str
    source_locator_refs: Tuple[str, ...]
    start_endpoint: TemporalDateEndpoint


@dataclass(frozen=True)
class TemporalRiskAnchor:
    domain: str
    end_endpoint: TemporalDateEndpoint
    event_ref: Optional[str]
    geometry: str
    risk_anchor_content_hash: str
    risk_anchor_ref: str
    risk_content_identity: str
    risk_ref: str
    risk_type_zh: str
    severity: str
    source_locator_refs: Tuple[str, ...]
    start_endpoint: TemporalDateEndpoint
    visit_ref: Optional[str]


@dataclass(frozen=True)
class TemporalVisit:
    accepted_assignment_ref: Optional[str]
    actual_encounter_ref: Optional[str]
    actual_endpoint: Optional[TemporalDateEndpoint]
    nominal_endpoint: Optional[TemporalDateEndpoint]
    phase_ref: Optional[str]
    planned_visit_ref: Optional[str]
    source_locator_refs: Tuple[str, ...]
    visit_content_hash: str
    visit_kind: Literal["nominal", "actual", "unscheduled"]
    visit_ref: str


@dataclass(frozen=True)
class SubjectTemporalPublicProjection:
    axis_basis: TemporalAxisBasis
    contract_id: str
    domain_tracks: Tuple[TemporalDomainTrack, ...]
    events: Tuple[TemporalEvent, ...]
    fallback_policy: Literal["fail_closed_no_nearest"]
    membership_index: TemporalMembershipIndex
    pending_date_items: Tuple[TemporalPendingDateItem, ...]
    phase_bands: Tuple[TemporalPhaseBand, ...]
    projection_content_hash: str
    projection_id: str
    receipt_ref: str
    risk_anchors: Tuple[TemporalRiskAnchor, ...]
    schema_version: str
    scope_identity: PublicScopeIdentity
    source_locators: Tuple[PublicSourceLocator, ...]
    visits: Tuple[TemporalVisit, ...]


@dataclass(frozen=True)
class SubjectTemporalAuthorityPacket:
    packet_content_hash: str
    projection: SubjectTemporalPublicProjection
    receipt: PublicAuthorityReceipt


def _endpoint(spec: EndpointInputV02) -> TemporalDateEndpoint:
    core = {
        "state": spec.state,
        "exact_date": spec.exact_date,
        "range_start": spec.range_start,
        "range_end": spec.range_end,
        "candidate_values": tuple(sorted(spec.candidates)),
        "source_locator_refs": tuple(sorted(spec.locator_refs)),
        "main_axis_projectable": spec.projectable,
        "range_projection_authorized": spec.range_authorized,
        "study_day": spec.study_day,
    }
    return TemporalDateEndpoint(
        candidate_values=core["candidate_values"],
        endpoint_content_hash=canonical_sha256(core),
        exact_date=spec.exact_date,
        main_axis_projectable=spec.projectable,
        range_end=spec.range_end,
        range_projection_authorized=spec.range_authorized,
        range_start=spec.range_start,
        source_locator_refs=core["source_locator_refs"],
        state=spec.state,
        study_day=spec.study_day,
    )


def _endpoint_specs(source: SubjectFullGraphInputV02) -> Tuple[EndpointInputV02, ...]:
    values = [source.visit.nominal, source.visit.actual]
    values.extend(endpoint for event in source.events for endpoint in (event.start, event.end))
    values.extend((source.risk.start, source.risk.end, source.phase.start, source.phase.end))
    return tuple(values)


def _derived_study_day(anchor_date: str, target_date: str, day_zero: bool) -> int:
    delta = (date.fromisoformat(target_date) - date.fromisoformat(anchor_date)).days
    return delta if day_zero or delta < 0 else delta + 1


def _date_parseable(value: Optional[str]) -> bool:
    if value is None:
        return True
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _partial_date_bounds(value: str) -> Optional[Tuple[date, date]]:
    parts = value.split("-")
    try:
        if len(parts) == 1 and len(parts[0]) == 4:
            first = date(int(parts[0]), 1, 1)
            return first, date(int(parts[0]), 12, 31)
        if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 2:
            year, month = int(parts[0]), int(parts[1])
            first = date(year, month, 1)
            return first, date(year, month, calendar.monthrange(year, month)[1])
        if len(parts) == 3 and all(len(part) == 2 for part in parts[1:]):
            exact = date.fromisoformat(value)
            return exact, exact
    except (TypeError, ValueError):
        return None
    return None


def _endpoint_input_issues(
    endpoint: EndpointInputV02,
    path: str,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = []
    if tuple(endpoint.candidates) != tuple(sorted(set(endpoint.candidates))):
        issues.append(issue("PUB_SET_ORDER_OR_DUPLICATE", path + "/candidates", priority=19))
    if endpoint.state not in DATE_STATES:
        issues.append(issue("PUB_DATE_STATE_INVALID", path + "/state", priority=20))
        return tuple(issues)
    if not _date_parseable(endpoint.exact_date):
        issues.append(issue("PUB_DATE_INVALID", path + "/exact_date", priority=20))
    if not _date_parseable(endpoint.range_start) or not _date_parseable(endpoint.range_end):
        issues.append(issue("PUB_DATE_INVALID", path + "/range", priority=20))
    if (
        endpoint.range_start is not None
        and endpoint.range_end is not None
        and _date_parseable(endpoint.range_start)
        and _date_parseable(endpoint.range_end)
        and date.fromisoformat(endpoint.range_start) > date.fromisoformat(endpoint.range_end)
    ):
        issues.append(issue("PUB_DATE_RANGE_ORDER", path + "/range", priority=29))
    if endpoint.state == "exact":
        if (
            endpoint.exact_date is None
            or endpoint.range_start is not None
            or endpoint.range_end is not None
            or endpoint.candidates
        ):
            issues.append(issue("PUB_DATE_STATE_INVALID", path, priority=20))
        if not endpoint.projectable or not endpoint.range_authorized:
            issues.append(issue("PUB_DATE_PROJECTABILITY_MISMATCH", path, priority=33))
    elif endpoint.state == "partial":
        if (
            endpoint.exact_date is not None
            or endpoint.range_start is None
            or endpoint.range_end is None
            or not endpoint.candidates
        ):
            issues.append(issue("PUB_DATE_STATE_INVALID", path, priority=20))
        if not endpoint.projectable or not endpoint.range_authorized:
            issues.append(issue("PUB_DATE_PROJECTABILITY_MISMATCH", path, priority=33))
    elif endpoint.state == "conflicted":
        if (
            endpoint.exact_date is not None
            or endpoint.range_start is not None
            or endpoint.range_end is not None
            or len(endpoint.candidates) < 2
        ):
            issues.append(issue("PUB_DATE_STATE_INVALID", path, priority=20))
        if endpoint.projectable or endpoint.range_authorized:
            issues.append(issue("PUB_DATE_PROJECTABILITY_MISMATCH", path, priority=33))
    else:
        if (
            endpoint.exact_date is not None
            or endpoint.range_start is not None
            or endpoint.range_end is not None
            or endpoint.candidates
        ):
            issues.append(issue("PUB_DATE_STATE_INVALID", path, priority=20))
        if endpoint.projectable or endpoint.range_authorized:
            issues.append(issue("PUB_DATE_PROJECTABILITY_MISMATCH", path, priority=33))
    if endpoint.state in ("partial", "conflicted"):
        if (
            endpoint.range_start is not None
            and endpoint.range_end is not None
            and _date_parseable(endpoint.range_start)
            and _date_parseable(endpoint.range_end)
        ):
            lower = date.fromisoformat(endpoint.range_start)
            upper = date.fromisoformat(endpoint.range_end)
            candidate_bounds = tuple(_partial_date_bounds(candidate) for candidate in endpoint.candidates)
            if (
                any(bounds is None for bounds in candidate_bounds)
                or any(
                    bounds[0] < lower or bounds[1] > upper
                    for bounds in candidate_bounds
                    if bounds is not None
                )
                or not candidate_bounds
                or min(bounds[0] for bounds in candidate_bounds if bounds is not None) != lower
                or max(bounds[1] for bounds in candidate_bounds if bounds is not None) != upper
            ):
                issues.append(issue("PUB_DATE_CANDIDATE_RANGE_MISMATCH", path, priority=30))
    if endpoint.state != "exact" and endpoint.study_day is not None:
        issues.append(issue("PUB_STUDY_DAY_VALUE_MISMATCH", path + "/study_day", priority=38))
    return tuple(issues)


def _geometry_input_issues(
    geometry: str,
    start: EndpointInputV02,
    end: EndpointInputV02,
    path: str,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    if geometry not in DATE_GEOMETRIES:
        return (issue("PUB_DATE_GEOMETRY_INVALID", path, priority=32),)
    if geometry == "point":
        if (
            start.state != "exact"
            or end.state != "exact"
            or start.exact_date != end.exact_date
        ):
            return (issue("PUB_DATE_GEOMETRY_INVALID", path, priority=35),)
    elif geometry == "closed_interval":
        if start.state != "exact" or end.state != "exact":
            return (issue("PUB_DATE_GEOMETRY_INVALID", path, priority=35),)
        if start.exact_date == end.exact_date:
            return (issue("PUB_DATE_GEOMETRY_DEGENERATE", path, priority=32),)
        if (
            start.exact_date is not None
            and end.exact_date is not None
            and _date_parseable(start.exact_date)
            and _date_parseable(end.exact_date)
            and date.fromisoformat(start.exact_date) > date.fromisoformat(end.exact_date)
        ):
            return (issue("PUB_INTERVAL_ORDER", path, priority=31),)
    elif geometry == "open_start":
        if start.state == "exact" or end.state != "exact":
            return (issue("PUB_DATE_GEOMETRY_INVALID", path, priority=35),)
    elif geometry == "open_end":
        if start.state == "missing" or end.state == "exact":
            return (issue("PUB_DATE_GEOMETRY_INVALID", path, priority=35),)
    return ()


def _revision_partition_issues(
    locator_specs: Tuple[object, ...],
    revision_specs: Tuple[object, ...],
    path_prefix: str,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = []
    locator_by_ref = {row.locator_ref: row for row in locator_specs}
    owner_by_locator = {}
    revision_refs = tuple(row.revision_ref for row in revision_specs)
    revision_ref_set = set(revision_refs)
    if len(revision_refs) != len(set(revision_refs)):
        issues.append(issue("PUB_SOURCE_REVISION_DUPLICATE", path_prefix + "/revisions", priority=20))
    locator_refs = tuple(row.locator_ref for row in locator_specs)
    if len(locator_refs) != len(set(locator_refs)):
        issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", path_prefix + "/locators", priority=20))
    for revision in revision_specs:
        if not revision.locator_refs:
            issues.append(issue("PUB_SOURCE_REVISION_EMPTY", path_prefix + "/revisions", priority=20))
        if len(revision.locator_refs) != len(set(revision.locator_refs)):
            issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", path_prefix + "/revisions", priority=30))
        for locator_ref in revision.locator_refs:
            if locator_ref not in locator_by_ref:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/revisions", priority=30))
            elif locator_ref in owner_by_locator:
                issues.append(issue("PUB_SOURCE_REVISION_OVERLAP", path_prefix + "/revisions", priority=30))
            else:
                owner_by_locator[locator_ref] = revision.revision_ref
    if set(owner_by_locator) != set(locator_by_ref):
        issues.append(issue("PUB_SOURCE_LOCATOR_UNUSED", path_prefix + "/locators", priority=29))
    for locator in locator_specs:
        if locator.locator_ref not in owner_by_locator:
            if locator.revision_ref not in revision_ref_set:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/locators", priority=30))
        elif owner_by_locator[locator.locator_ref] != locator.revision_ref:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/locators", priority=30))
    return tuple(issues)


def _subject_input_issues(authority: AuthorityBundleV02) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = list(authority_issues(authority, "subject-temporal-public-v1"))
    if issues or not isinstance(authority.source, SubjectFullGraphInputV02):
        return tuple(issues)
    source = authority.source
    if len(source.events) != 2:
        issues.append(issue("PUB_CARDINALITY_MISMATCH", "/source/events", priority=20))
    if len(source.domain_applicability) != len(DOMAINS) or tuple(row.domain for row in source.domain_applicability) != DOMAINS:
        issues.append(issue("PUB_DOMAIN_COVERAGE_MISMATCH", "/source/domain_applicability", priority=20))
    if source.axis.mode not in AXIS_MODES or source.axis.day_zero_convention not in DAY_ZERO_CONVENTIONS:
        issues.append(issue("PUB_AXIS_INVALID", "/source/axis", priority=20))
    if not source.axis.timezone:
        issues.append(issue("PUB_AXIS_INVALID", "/source/axis/timezone", priority=20))
    if source.axis.mode == "study_day" and not source.axis.study_day_enabled:
        issues.append(issue("PUB_AXIS_INVALID", "/source/axis/study_day_enabled", priority=20))
    if not source.axis.study_day_enabled and source.axis.anchor_event_ref is not None:
        issues.append(issue("PUB_STUDY_DAY_ANCHOR_MISSING", "/source/axis/anchor_event_ref", priority=20))
    binding = source.cutoff_binding
    binding_ok = (
        binding.state == "present"
        and binding.exact_date is not None
        and bool(binding.source_locator_refs)
    ) or (
        binding.state == "absent"
        and binding.exact_date is None
        and not binding.source_locator_refs
    )
    if not binding_ok:
        issues.append(issue("PUB_CUTOFF_BINDING_INVALID", "/source/cutoff_binding", priority=20))
    if binding.exact_date is not None:
        if not _date_parseable(binding.exact_date):
            issues.append(issue("PUB_DATE_INVALID", "/source/cutoff_binding/exact_date", priority=20))
    locator_refs = tuple(row.locator_ref for row in source.locator_specs)
    if len(locator_refs) != len(set(locator_refs)):
        issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", "/source/locator_specs", priority=20))
    locator_by_ref = {row.locator_ref: row for row in source.locator_specs}
    revision_by_ref = {row.revision_ref: row for row in source.revision_specs}
    used_locator_refs = set()
    unresolved_locator_ref = False
    issues.extend(_revision_partition_issues(
        source.locator_specs,
        source.revision_specs,
        "/source",
    ))
    for locator in source.locator_specs:
        if locator.snapshot_ref != source.scope.snapshot_ref:
            issues.append(issue("PUB_IDENTITY_SNAPSHOT_MISMATCH", "/source/locator_specs", priority=30))
        if locator.revision_ref not in revision_by_ref:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/locator_specs", priority=30))
        elif locator.locator_ref not in revision_by_ref[locator.revision_ref].locator_refs:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/locator_specs", priority=30))
        if locator.revision_content_identity != canonical_sha256({"revision": locator.revision_ref, "accepted": True}):
            issues.append(issue("PUB_SOURCE_REVISION_HASH_MISMATCH", "/source/locator_specs", priority=30))
    for revision in source.revision_specs:
        if revision.revision_content_identity != canonical_sha256({"revision": revision.revision_ref, "accepted": True}):
            issues.append(issue("PUB_SOURCE_REVISION_HASH_MISMATCH", "/source/revision_specs", priority=30))
        for locator_ref in revision.locator_refs:
            if locator_ref not in locator_by_ref:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/revision_specs", priority=30))

    def check_locator_refs(refs: Tuple[str, ...], path: str) -> None:
        nonlocal unresolved_locator_ref
        if tuple(refs) != tuple(sorted(set(refs))):
            issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", path, priority=20))
        for locator_ref in refs:
            if locator_ref not in locator_by_ref:
                unresolved_locator_ref = True
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path, priority=30))
            else:
                used_locator_refs.add(locator_ref)

    check_locator_refs(source.cutoff_binding.source_locator_refs, "/source/cutoff_binding/source_locator_refs")
    check_locator_refs(source.visit.locator_refs, "/source/visit/locator_refs")
    check_locator_refs(source.phase.locator_refs, "/source/phase/locator_refs")
    check_locator_refs(source.risk.locator_refs, "/source/risk/locator_refs")
    endpoint_specs = _endpoint_specs(source)
    for endpoint in endpoint_specs:
        check_locator_refs(endpoint.locator_refs, "/source/endpoint/locator_refs")
        issues.extend(_endpoint_input_issues(endpoint, "/source/endpoint"))
    event_refs = {event.event_ref for event in source.events}
    event_by_ref = {event.event_ref: event for event in source.events}
    if len(event_refs) != len(source.events):
        issues.append(issue("PUB_SOURCE_EVENT_DUPLICATE", "/source/events", priority=20))
    domain_states = {row.domain: row.state for row in source.domain_applicability}
    for row in source.domain_applicability:
        expected_event_refs = tuple(sorted(
            event.event_ref for event in source.events if event.domain == row.domain
        ))
        expected_risk_refs = (
            (source.risk.risk_anchor_ref,)
            if source.risk.domain == row.domain
            else ()
        )
        if tuple(row.event_refs) != tuple(sorted(set(row.event_refs))) or tuple(row.risk_refs) != tuple(sorted(set(row.risk_refs))):
            issues.append(issue("PUB_SET_ORDER_OR_DUPLICATE", "/source/domain_applicability", priority=19))
        if row.state not in APPLICABILITY_STATES:
            issues.append(issue("PUB_DOMAIN_APPLICABILITY_INVALID", "/source/domain_applicability", priority=20))
        elif row.state == "applicable":
            if (not expected_event_refs and not expected_risk_refs) or tuple(row.event_refs) != expected_event_refs or tuple(row.risk_refs) != expected_risk_refs:
                issues.append(issue("PUB_DOMAIN_APPLICABILITY_MISMATCH", "/source/domain_applicability", priority=42))
        elif expected_event_refs or expected_risk_refs or row.event_refs or row.risk_refs:
            issues.append(issue("PUB_DOMAIN_APPLICABILITY_MISMATCH", "/source/domain_applicability", priority=42))
    for event in source.events:
        check_locator_refs(event.locator_refs, "/source/events/locator_refs")
        if event.subtype not in JOURNEY_SUBTYPES:
            issues.append(issue("PUB_EVENT_SUBTYPE_INVALID", "/source/events/subtype", priority=20))
        if event.domain not in domain_states:
            issues.append(issue("PUB_DOMAIN_COVERAGE_MISMATCH", "/source/events/domain", priority=20))
        elif domain_states[event.domain] != "applicable":
            issues.append(issue("PUB_DOMAIN_APPLICABILITY_MISMATCH", "/source/events/domain", priority=42))
        if event.visit_ref is not None and event.visit_ref != source.visit.visit_ref:
            issues.append(issue("PUB_REFERENCE_VISIT_MISMATCH", "/source/events/visit_ref", priority=30))
        if any(risk_ref not in {source.risk.risk_anchor_ref} for risk_ref in event.risk_refs):
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/events/risk_refs", priority=30))
        issues.extend(_geometry_input_issues(
            event.geometry,
            event.start,
            event.end,
            "/source/events/geometry",
        ))
        for risk_ref in event.risk_refs:
            if risk_ref == source.risk.risk_anchor_ref and source.risk.domain != event.domain:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/events/risk_refs", priority=30))
    for domain in source.domain_applicability:
        if any(event_ref not in event_refs for event_ref in domain.event_refs):
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/domain_applicability/event_refs", priority=30))
        if any(risk_ref not in {source.risk.risk_anchor_ref} for risk_ref in domain.risk_refs):
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/domain_applicability/risk_refs", priority=30))
    if source.risk.event_ref not in event_refs:
        issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/risk/event_ref", priority=30))
    else:
        if event_by_ref[source.risk.event_ref].domain != source.risk.domain:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/risk/event_ref", priority=30))
    if source.risk.visit_ref != source.visit.visit_ref:
        issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/risk/visit_ref", priority=30))
    if source.visit.phase_ref != source.phase.phase_ref:
        issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/visit/phase_ref", priority=30))
    if source.risk.severity not in SEVERITIES:
        issues.append(issue("SEM_AUTHORITY_MISMATCH", "/source/risk/severity", origin="semantic_delta", priority=40))
    if source.risk.domain not in domain_states or domain_states[source.risk.domain] != "applicable":
        issues.append(issue("PUB_DOMAIN_APPLICABILITY_MISMATCH", "/source/risk/domain", priority=42))
    issues.extend(_geometry_input_issues(
        source.risk.geometry,
        source.risk.start,
        source.risk.end,
        "/source/risk/geometry",
    ))
    issues.extend(_geometry_input_issues(
        source.phase.geometry,
        source.phase.start,
        source.phase.end,
        "/source/phase/geometry",
    ))
    if source.axis.study_day_enabled:
        if source.axis.anchor_event_ref is None:
            issues.append(issue("PUB_STUDY_DAY_ANCHOR_MISSING", "/source/axis/anchor_event_ref", priority=20))
        else:
            anchors = [row for row in source.events if row.event_ref == source.axis.anchor_event_ref]
            if len(anchors) != 1:
                issues.append(issue("PUB_STUDY_DAY_ANCHOR_MISSING", "/source/axis/anchor_event_ref", priority=20))
            else:
                anchor = anchors[0].start
                if anchor.state != "exact" or anchor.exact_date is None or not anchor.projectable:
                    issues.append(issue("PUB_STUDY_DAY_ANCHOR_INVALID", "/source/events", priority=20))
                else:
                    day_zero = source.axis.day_zero_convention == "anchor_day_zero"
                    try:
                        for endpoint in _endpoint_specs(source):
                            expected = (
                                _derived_study_day(anchor.exact_date, endpoint.exact_date, day_zero)
                                if endpoint.state == "exact" and endpoint.exact_date is not None
                                else None
                            )
                            if endpoint.study_day != expected:
                                issues.append(issue("PUB_STUDY_DAY_VALUE_MISMATCH", "/source", priority=38))
                                break
                    except ValueError:
                        issues.append(issue("PUB_DATE_INVALID", "/source", priority=20))
    elif source.axis.anchor_event_ref is not None or any(endpoint.study_day is not None for endpoint in _endpoint_specs(source)):
        issues.append(issue("PUB_STUDY_DAY_VALUE_MISMATCH", "/source/axis", priority=38))
    if tuple(row.domain for row in source.events) != ("ae", "mh"):
        issues.append(issue("PUB_DOMAIN_COVERAGE_MISMATCH", "/source/events", priority=20))
    if source.risk.domain != "ae" or source.risk.severity not in {"critical", "high", "medium", "low"}:
        issues.append(issue("SEM_AUTHORITY_MISMATCH", "/source/risk", origin="semantic_delta", priority=40))
    if used_locator_refs != set(locator_by_ref) and not unresolved_locator_ref:
        issues.append(issue("PUB_SOURCE_LOCATOR_UNUSED", "/source/locator_specs", priority=29))
    return tuple(issues)


def _scope(source: SubjectFullGraphInputV02) -> PublicScopeIdentity:
    scope: IdentityScopeInputV02 = source.scope
    binding = source.cutoff_binding
    return make_scope_identity(
        project_ref=scope.project_ref,
        run_ref=scope.run_ref,
        site_ref=scope.site_ref,
        snapshot_ref=scope.snapshot_ref,
        spine_ref=scope.spine_ref,
        subject_ref=scope.subject_ref,
        cutoff_state=binding.state,
        cutoff_ref=binding.exact_date,
    )


def _locator_ref_key(row: PublicSourceLocator) -> str:
    return row.locator_ref


def _event_ref_key(row: TemporalEvent) -> str:
    return row.event_ref


def _pending_item(
    item_kind: Literal["visit", "event", "risk", "phase"],
    item_ref: str,
    domain: Optional[str],
    start_endpoint: TemporalDateEndpoint,
    end_endpoint: TemporalDateEndpoint,
    target_content_hash: str,
    source_locator_refs: Tuple[str, ...],
) -> TemporalPendingDateItem:
    if item_kind not in PENDING_ITEM_KINDS:
        raise ValueError("PUB_PENDING_ITEM_KIND_INVALID")
    pending_ref = "pending::" + item_ref
    core = {
        "pending_ref": pending_ref,
        "item_kind": item_kind,
        "item_ref": item_ref,
        "target_content_hash": target_content_hash,
        "domain": domain,
        "start_endpoint": start_endpoint,
        "end_endpoint": end_endpoint,
        "source_locator_refs": tuple(sorted(source_locator_refs)),
    }
    return TemporalPendingDateItem(
        domain=domain,
        end_endpoint=end_endpoint,
        item_kind=item_kind,
        item_ref=item_ref,
        pending_content_hash=canonical_sha256(core),
        pending_ref=pending_ref,
        source_locator_refs=core["source_locator_refs"],
        start_endpoint=start_endpoint,
        target_content_hash=target_content_hash,
    )


def _subject_evaluation(
    projection: SubjectTemporalPublicProjection,
    pairs: Tuple[SourceRevisionContentPair, ...],
) -> Tuple[str, ...]:
    values = [
        projection.projection_content_hash,
        projection.scope_identity.identity_content_hash,
        projection.membership_index.membership_content_hash,
        projection.axis_basis.axis_content_hash,
        *(pair.accepted_content_hash for pair in pairs),
        *(visit.visit_content_hash for visit in projection.visits),
    ]
    for event in projection.events:
        values.extend((event.event_content_identity, event.event_content_hash))
    for risk in projection.risk_anchors:
        values.extend((risk.risk_content_identity, risk.risk_anchor_content_hash))
    values.extend(item.pending_content_hash for item in projection.pending_date_items)
    values.extend(phase.phase_content_hash for phase in projection.phase_bands)
    values.extend(track.track_content_hash for track in projection.domain_tracks)
    values.extend(locator.locator_content_hash for locator in projection.source_locators)
    return tuple(sorted(set(values)))


def _build_subject(authority: AuthorityBundleV02) -> SubjectTemporalAuthorityPacket:
    source = authority.source
    if not isinstance(source, SubjectFullGraphInputV02):
        fail(validation_result((issue("PUB_TYPE_MISMATCH", "/source", origin="parent", priority=1),)))
    scope = _scope(source)
    locators = tuple(sorted((make_source_locator(row) for row in source.locator_specs), key=_locator_ref_key))
    pairs = make_source_pairs(source.revision_specs)

    visit_spec = source.visit
    visit_core = {
        "visit_ref": visit_spec.visit_ref,
        "visit_kind": "actual",
        "planned_visit_ref": visit_spec.planned_visit_ref,
        "actual_encounter_ref": visit_spec.actual_encounter_ref,
        "accepted_assignment_ref": visit_spec.assignment_ref,
        "phase_ref": visit_spec.phase_ref,
        "nominal_endpoint": _endpoint(visit_spec.nominal),
        "actual_endpoint": _endpoint(visit_spec.actual),
        "source_locator_refs": tuple(sorted(visit_spec.locator_refs)),
    }
    visit = TemporalVisit(
        accepted_assignment_ref=visit_spec.assignment_ref,
        actual_encounter_ref=visit_spec.actual_encounter_ref,
        actual_endpoint=visit_core["actual_endpoint"],
        nominal_endpoint=visit_core["nominal_endpoint"],
        phase_ref=visit_spec.phase_ref,
        planned_visit_ref=visit_spec.planned_visit_ref,
        source_locator_refs=visit_core["source_locator_refs"],
        visit_content_hash=canonical_sha256(visit_core),
        visit_kind="actual",
        visit_ref=visit_spec.visit_ref,
    )

    domain_states = {row.domain: row.state for row in source.domain_applicability}
    events = []
    for spec in source.events:
        core = {
            "event_ref": spec.event_ref,
            "event_content_identity": spec.content_identity,
            "domain": spec.domain,
            "subtype": spec.subtype,
            "applicability_state": domain_states[spec.domain],
            "visit_ref": spec.visit_ref,
            "geometry": spec.geometry,
            "start_endpoint": _endpoint(spec.start),
            "end_endpoint": _endpoint(spec.end),
            "risk_anchor_refs": tuple(sorted(spec.risk_refs)),
            "source_locator_refs": tuple(sorted(spec.locator_refs)),
        }
        events.append(TemporalEvent(
            applicability_state=domain_states[spec.domain],
            domain=spec.domain,
            end_endpoint=core["end_endpoint"],
            event_content_hash=canonical_sha256(core),
            event_content_identity=spec.content_identity,
            event_ref=spec.event_ref,
            geometry=spec.geometry,
            risk_anchor_refs=core["risk_anchor_refs"],
            source_locator_refs=core["source_locator_refs"],
            start_endpoint=core["start_endpoint"],
            subtype=spec.subtype,
            visit_ref=spec.visit_ref,
        ))
    events = tuple(sorted(events, key=_event_ref_key))

    risk_spec = source.risk
    risk_core = {
        "risk_anchor_ref": risk_spec.risk_anchor_ref,
        "risk_ref": risk_spec.risk_ref,
        "risk_content_identity": risk_spec.content_identity,
        "domain": risk_spec.domain,
        "severity": risk_spec.severity,
        "risk_type_zh": risk_spec.risk_type_zh,
        "event_ref": risk_spec.event_ref,
        "visit_ref": risk_spec.visit_ref,
        "geometry": risk_spec.geometry,
        "start_endpoint": _endpoint(risk_spec.start),
        "end_endpoint": _endpoint(risk_spec.end),
        "source_locator_refs": tuple(sorted(risk_spec.locator_refs)),
    }
    risk = TemporalRiskAnchor(
        domain=risk_spec.domain,
        end_endpoint=risk_core["end_endpoint"],
        event_ref=risk_spec.event_ref,
        geometry=risk_spec.geometry,
        risk_anchor_content_hash=canonical_sha256(risk_core),
        risk_anchor_ref=risk_spec.risk_anchor_ref,
        risk_content_identity=risk_spec.content_identity,
        risk_ref=risk_spec.risk_ref,
        risk_type_zh=risk_spec.risk_type_zh,
        severity=risk_spec.severity,
        source_locator_refs=risk_core["source_locator_refs"],
        start_endpoint=risk_core["start_endpoint"],
        visit_ref=risk_spec.visit_ref,
    )

    phase_spec = source.phase
    phase_core = {
        "phase_ref": phase_spec.phase_ref,
        "phase_label_zh": phase_spec.label_zh,
        "geometry": phase_spec.geometry,
        "start_endpoint": _endpoint(phase_spec.start),
        "end_endpoint": _endpoint(phase_spec.end),
        "source_locator_refs": tuple(sorted(phase_spec.locator_refs)),
    }
    phase = TemporalPhaseBand(
        end_endpoint=phase_core["end_endpoint"],
        geometry=phase_spec.geometry,
        phase_content_hash=canonical_sha256(phase_core),
        phase_label_zh=phase_spec.label_zh,
        phase_ref=phase_spec.phase_ref,
        source_locator_refs=phase_core["source_locator_refs"],
        start_endpoint=phase_core["start_endpoint"],
    )

    pending_values = []
    if visit.nominal_endpoint.state != "exact" or visit.actual_endpoint.state != "exact":
        pending_values.append(_pending_item(
            "visit",
            visit.visit_ref,
            None,
            visit.nominal_endpoint,
            visit.actual_endpoint,
            visit.visit_content_hash,
            visit.source_locator_refs,
        ))
    for event in events:
        if event.start_endpoint.state != "exact" or event.end_endpoint.state != "exact":
            pending_values.append(_pending_item(
                "event",
                event.event_ref,
                event.domain,
                event.start_endpoint,
                event.end_endpoint,
                event.event_content_hash,
                event.source_locator_refs,
            ))
    if risk.start_endpoint.state != "exact" or risk.end_endpoint.state != "exact":
        pending_values.append(_pending_item(
            "risk",
            risk.risk_ref,
            risk.domain,
            risk.start_endpoint,
            risk.end_endpoint,
            risk.risk_anchor_content_hash,
            risk.source_locator_refs,
        ))
    if phase.start_endpoint.state != "exact" or phase.end_endpoint.state != "exact":
        pending_values.append(_pending_item(
            "phase",
            phase.phase_ref,
            None,
            phase.start_endpoint,
            phase.end_endpoint,
            phase.phase_content_hash,
            phase.source_locator_refs,
        ))
    pending = tuple(pending_values)

    tracks = tuple(
        TemporalDomainTrack(
            applicability_state=row.state,
            domain=row.domain,
            event_refs=tuple(sorted(row.event_refs)),
            risk_anchor_refs=tuple(sorted(row.risk_refs)),
            track_content_hash=canonical_sha256({
                "domain": row.domain,
                "applicability_state": row.state,
                "event_refs": tuple(sorted(row.event_refs)),
                "risk_anchor_refs": tuple(sorted(row.risk_refs)),
            }),
        )
        for row in source.domain_applicability
    )
    membership_core = {
        "visit_refs": (visit.visit_ref,),
        "event_refs": tuple(event.event_ref for event in events),
        "risk_anchor_refs": (risk.risk_anchor_ref,),
        "pending_date_refs": tuple(item.pending_ref for item in pending),
        "phase_refs": (phase.phase_ref,),
        "source_locator_refs": tuple(locator.locator_ref for locator in locators),
    }
    membership = TemporalMembershipIndex(
        event_refs=membership_core["event_refs"],
        membership_content_hash=canonical_sha256(membership_core),
        pending_date_refs=membership_core["pending_date_refs"],
        phase_refs=membership_core["phase_refs"],
        risk_anchor_refs=membership_core["risk_anchor_refs"],
        source_locator_refs=membership_core["source_locator_refs"],
        visit_refs=membership_core["visit_refs"],
    )

    binding = source.cutoff_binding
    cutoff_spec = EndpointInputV02(
        candidates=(),
        exact_date=binding.exact_date,
        locator_refs=tuple(binding.source_locator_refs),
        projectable=binding.state == "present",
        range_authorized=binding.state == "present",
        range_end=None,
        range_start=None,
        state="exact" if binding.state == "present" else "missing",
        study_day=None,
    )
    cutoff_endpoint = _endpoint(cutoff_spec)
    axis_spec = source.axis
    axis_core = {
        "axis_ref": axis_spec.axis_ref,
        "default_axis_mode": axis_spec.mode,
        "timezone": axis_spec.timezone,
        "study_day_anchor_event_ref": axis_spec.anchor_event_ref if axis_spec.study_day_enabled else None,
        "study_day_zero_exists": (
            axis_spec.day_zero_convention == "anchor_day_zero"
            if axis_spec.study_day_enabled
            else None
        ),
        "cutoff_endpoint": cutoff_endpoint,
        "source_locator_refs": tuple(sorted(binding.source_locator_refs)),
    }
    axis = TemporalAxisBasis(
        axis_content_hash=canonical_sha256(axis_core),
        axis_ref=axis_spec.axis_ref,
        cutoff_endpoint=cutoff_endpoint,
        default_axis_mode=axis_spec.mode,
        source_locator_refs=axis_core["source_locator_refs"],
        study_day_anchor_event_ref=axis_core["study_day_anchor_event_ref"],
        study_day_zero_exists=axis_core["study_day_zero_exists"],
        timezone=axis_spec.timezone,
    )

    projection_id = canonical_sha256({
        "contract_id": "subject-temporal-public-v1",
        "schema_version": "2026-08-19.1",
        "scope_identity_hash": scope.identity_content_hash,
        "membership_index_hash": membership.membership_content_hash,
        "axis_basis_hash": axis.axis_content_hash,
    })
    receipt_id = canonical_sha256({
        "receipt_variant": "subject_temporal",
        "authority_contract_id": "subject-temporal-public-v1",
        "scope_identity_hash": scope.identity_content_hash,
        "public_projection_id": projection_id,
    })
    projection_core = {
        "contract_id": "subject-temporal-public-v1",
        "schema_version": "2026-08-19.1",
        "projection_id": projection_id,
        "receipt_ref": receipt_id,
        "scope_identity": scope,
        "fallback_policy": FALLBACK_POLICY,
        "axis_basis": axis,
        "visits": (visit,),
        "events": events,
        "risk_anchors": (risk,),
        "pending_date_items": pending,
        "phase_bands": (phase,),
        "domain_tracks": tracks,
        "source_locators": locators,
        "membership_index": membership,
    }
    projection_hash = canonical_sha256(projection_core)
    projection = SubjectTemporalPublicProjection(
        axis_basis=axis,
        contract_id="subject-temporal-public-v1",
        domain_tracks=tracks,
        events=events,
        fallback_policy=FALLBACK_POLICY,
        membership_index=membership,
        pending_date_items=pending,
        phase_bands=(phase,),
        projection_content_hash=projection_hash,
        projection_id=projection_id,
        receipt_ref=receipt_id,
        risk_anchors=(risk,),
        schema_version="2026-08-19.1",
        scope_identity=scope,
        source_locators=locators,
        visits=(visit,),
    )
    evaluation = _subject_evaluation(projection, pairs)
    receipt = make_receipt(
        receipt_variant="subject_temporal",
        authority_contract_id="subject-temporal-public-v1",
        scope=scope,
        projection_id=projection_id,
        projection_content_hash=projection_hash,
        evaluation_content_identities=evaluation,
        source_revision_content_pairs=pairs,
    )
    packet_hash = canonical_sha256({
        "receipt_content_hash": receipt.receipt_content_hash,
        "projection_content_hash": projection.projection_content_hash,
    })
    return SubjectTemporalAuthorityPacket(
        packet_content_hash=packet_hash,
        projection=projection,
        receipt=receipt,
    )


def build_subject_temporal_authority(
    source: AuthorityBundleV02,
) -> SubjectTemporalAuthorityPacket:
    """Build one packet from frozen AuthorityBundleV02 authority only."""
    issues = _subject_input_issues(source)
    if issues:
        fail(validation_result(issues))
    try:
        return _build_subject(source)
    except (KeyError, StopIteration, ValueError, TypeError):
        fail(validation_result((issue("PUB_CONSTRUCTION_FAILED", "/authority", priority=50),)))


def validate_subject_temporal_authority(
    candidate: SubjectTemporalAuthorityPacket,
    source: AuthorityBundleV02,
) -> PublicAuthorityValidationResult:
    """Rebuild and compare a candidate without treating it as authority."""
    issues = list(_subject_input_issues(source))
    if not isinstance(candidate, SubjectTemporalAuthorityPacket):
        issues.append(issue("PUB_TYPE_MISMATCH", "/candidate", origin="parent", priority=1))
        return validation_result(issues)
    if issues:
        return validation_result(issues)
    try:
        expected = _build_subject(source)
    except (AssertionError, KeyError, StopIteration, ValueError, TypeError):
        return validation_result((issue("PUB_HASH_MISMATCH", "/candidate", priority=50),))
    if candidate != expected:
        return validation_result((issue("PUB_HASH_MISMATCH", "/candidate", priority=50),))
    return validation_result(())
