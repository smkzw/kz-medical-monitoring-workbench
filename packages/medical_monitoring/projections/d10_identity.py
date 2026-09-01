"""Projection version, public risk identity, hotspots, and deep links."""

from .d10_core import *

# ---------------------------------------------------------------------------
# Projection version (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectionVersion:
    """Versioned projection identity.

    Binds the projection to the authoritative evaluation content identity,
    the measure ledger, the stable risk core, the visibility decision set
    and the frozen audience contract.  Opaque run/snapshot ids are audit
    refs only and never enter the content hash.
    """

    projection_version_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    source_evaluation_content_identities: Tuple[str, ...]
    source_ledger_hashes: Tuple[str, ...]
    source_risk_refs: Tuple[str, ...]
    visibility_decision_refs: Tuple[str, ...]
    audience_contract_ref: str
    supersedes_projection_ref: Optional[str]
    projection_content_hash: str
    projection_version_content_hash: str


def _measure_ledger_ref(typed: D10TypedInput,
                        result: D10RunResult) -> str:
    unit = result.unit
    return d10_content_hash({
        "denominator_kind": typed.denominator.denominator_kind,
        "denominator_value": typed.denominator.denominator_value,
        "denominator_state": typed.denominator.denominator_state,
        "individual_risk_count": unit.individual_risk_count if unit else 0,
        "affected_subject_count": unit.affected_subject_count if unit else 0,
        "event_or_outcome_count": unit.event_or_outcome_count if unit else 0,
        "center_pattern_count": unit.center_pattern_count if unit else 0,
        "affected_site_count": unit.affected_site_count if unit else 0,
        "numerator_member_count": unit.numerator_member_count if unit else 0,
    })


def build_d10_projection_version(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectionVersion:
    """Build the versioned projection identity for one run."""
    _assert_authoritative_result(typed, result)
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    content_identity = result.evaluation_content_identity
    # (the strengthened authoritative binding guarantees the result identity
    # is a non-empty 64-hex digest equal to its trace leaf content identity)
    stable_core = result.stable_core_ref or ""
    measure_ref = _measure_ledger_ref(typed, result)
    visibility = typed.visibility_decision
    supersedes = None
    if typed.change_decision is not None:
        supersedes = typed.change_decision.prior_snapshot_ref_or_none
    content_core = {
        "project_ref": typed.project_ref,
        "source_evaluation_content_identities": [content_identity],
        "source_ledger_hashes": [measure_ref],
        "source_risk_refs": [stable_core] if stable_core else [],
        "visibility_decision_refs": [visibility.decision_id],
        "audience_contract_ref": typed.audience_text.audience_contract_id,
        "supersedes_projection_ref": supersedes,
        "algorithm_version": _ALGORITHM_VERSION,
    }
    projection_content_hash = d10_content_hash(content_core)
    version_identity_content = {
        "project_ref": typed.project_ref,
        "run_ref": typed.run_ref,
        "snapshot_ref": typed.snapshot_ref,
        "cutoff_ref": window.cutoff_ref if window else None,
        "projection_content_hash": projection_content_hash,
    }
    projection_version_id = d10_content_hash(version_identity_content)
    return D10ProjectionVersion(
        projection_version_id=projection_version_id,
        project_ref=typed.project_ref,
        run_ref=typed.run_ref,
        snapshot_ref=typed.snapshot_ref,
        cutoff_ref=window.cutoff_ref if window else None,
        source_evaluation_content_identities=(content_identity,),
        source_ledger_hashes=(measure_ref,),
        source_risk_refs=(stable_core,) if stable_core else (),
        visibility_decision_refs=(visibility.decision_id,),
        audience_contract_ref=typed.audience_text.audience_contract_id,
        supersedes_projection_ref=supersedes,
        projection_content_hash=projection_content_hash,
        projection_version_content_hash=projection_version_id,
    )


# ---------------------------------------------------------------------------
# Project-signal risk marker (contract section 10)
# ---------------------------------------------------------------------------


def d10_public_risk_identity(typed: D10TypedInput) -> Dict[str, Any]:
    """Stable public D10 risk identity (contract section 10 canonical
    tuple): excludes run/snapshot ids, computed dates, revisions and display
    text; never merges with D01-D09 public identities."""
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    return {
        "project_ref": typed.project_ref,
        "domain_id": D10_DOMAIN_ID,
        "scope_type": "project",
        "stable_source_or_event_identity": (
            typed.signal_definition.signal_definition_id,
            window.analysis_window_stable_id if window else "",
            typed.stratum.stratum_key,
            typed.comparison_gate.comparison_reference_stable_id,
        ),
        "normalized_concept": (
            typed.signal_definition.signal_kind,
            typed.signal_definition.signal_definition_id,
        ),
        "temporal_window": (
            window.window_kind if window else None,
            window.window_definition_id if window else None,
        ),
        "public_identity_version": _PUBLIC_IDENTITY_VERSION,
        "scope_binding_id": typed.project_scope_binding.scope_binding_id,
    }


@dataclass(frozen=True)
class D10RiskMarker:
    """Project-signal RiskInstance marker (contract section 10).

    An audience projection: references only the resolved projectable
    member/locator set.  The public identity is revision-free and replay
    stable; run/snapshot ids never enter it."""

    marker_id: str
    public_risk_identity: Dict[str, Any]
    stable_core: str
    risk_owner: str
    risk_kind: str
    aggregation_level: str
    member_refs: Tuple[str, ...]
    source_locator_ids: Tuple[str, ...]
    content_hash: str


def build_d10_risk_marker(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Optional[D10RiskMarker]:
    """Build the project-signal risk marker for the run's positive unit.

    Returns ``None`` unless the run carries exactly one positive project
    signal with at least one projectable member.  Boundary/negative/
    not-applicable/not-evaluable and gate runs never get a marker.
    """
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return None
    public_identity = d10_public_risk_identity(typed)
    # The marker references only the pair-visible member set: members of a
    # hidden site are never exposed through the marker or its locators.
    members = _pair_visible_members(typed, result)
    if not members:
        return None
    member_refs = tuple(sorted(m.member_ref for m in members))
    locators = tuple(sorted({locator
                             for m in members
                             for locator in m.source_locator_refs
                             if _member_locator(m) is not None}))
    marker_id = d10_content_hash({
        "public_d10_risk_identity": public_identity,
        "stable_core": unit.stable_core_ref,
        "member_refs": list(member_refs),
    })
    core = {
        "marker_id": marker_id,
        "public_risk_identity": public_identity,
        "stable_core": unit.stable_core_ref,
        "risk_owner": "D10",
        "risk_kind": "project_signal",
        "aggregation_level": "project_signal",
        "member_refs": list(member_refs),
        "source_locator_ids": list(locators),
    }
    return D10RiskMarker(
        marker_id=marker_id,
        public_risk_identity=public_identity,
        stable_core=unit.stable_core_ref,
        risk_owner="D10",
        risk_kind="project_signal",
        aggregation_level="project_signal",
        member_refs=member_refs,
        source_locator_ids=locators,
        content_hash=d10_content_hash(core),
    )


# ---------------------------------------------------------------------------
# Hotspot subject rows (contract section 7/10/12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10HotspotProjection:
    """One hotspot subject row.

    A projection only -- never an L1 unit and never a RiskInstance.  Only
    pair-visible members are referenced; hidden members and members of
    hidden sites never appear in rows, anchors, locators or ordering.
    Order is subject stable identity ascending -- never a punitive risk
    ranking and never a black-box score.
    """

    projection_id: str
    site_ref: str
    evaluation_window_instance_ref: str
    subject_ref: str
    member_refs: Tuple[str, ...]
    monitoring_priority: Optional[str]
    source_locator_refs: Tuple[str, ...]
    projectability_decision_ref: str


def build_d10_hotspots(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10HotspotProjection, ...]:
    """List hotspot subject rows (contract sections 7/10/12).

    The typed ``Hotspot`` member set is the authoritative high-risk hotspot
    fact (the evaluator already fails closed when a hidden-in-display
    hotspot is submitted).  Rows are projected on positive runs only, over
    the pair-visible member plane: the single high-risk subject is always
    preserved and is never hidden behind a low project proportion or a
    small-sample note.
    """
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return ()
    hotspot = typed.hotspot
    if hotspot is None or not hotspot.hotspot_member_refs:
        return ()
    if hotspot.hidden_in_display:
        raise D10ProjectionError("hidden-in-display hotspot must fail closed")
    member_by_ref = {m.member_ref: m for m in typed.members}
    pair_visible = _pair_visible_members(typed, result)
    pair_visible_refs = {m.member_ref for m in pair_visible}
    window_instance = _evaluation_window_instance_ref(typed)
    rows_by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for ref in hotspot.hotspot_member_refs:
        member = member_by_ref.get(ref)
        if member is None:
            raise D10ProjectionError(
                f"hotspot member ref {ref!r} has no typed member object")
        if ref not in pair_visible_refs:
            # the evaluator already rejects hidden member leakage; a member
            # of a hidden site is not pair-visible and must not surface
            raise D10ProjectionError(
                f"hotspot member {ref!r} is not pair-visible")
        key = (member.subject_stable_id or "", member.site_stable_id or "")
        row = rows_by_pair.setdefault(key, {
            "members": [],
            "locators": [],
            "priorities": [],
        })
        row["members"].append(ref)
        locator = _member_locator(member)
        if locator is not None and locator not in row["locators"]:
            row["locators"].append(locator)
        row["priorities"].append(member.monitoring_priority)
    rows: List[D10HotspotProjection] = []
    for key in sorted(rows_by_pair):
        subject, site = key
        row = rows_by_pair[key]
        priorities = [p for p in row["priorities"] if p]
        priority = ("high" if "high" in priorities
                    else "medium" if "medium" in priorities else None)
        member_refs = tuple(sorted(row["members"]))
        projection_id = d10_content_hash({
            "site_ref": site,
            "window_instance": window_instance,
            "subject_ref": subject,
            "member_refs": list(member_refs),
            "monitoring_priority": priority,
        })
        rows.append(D10HotspotProjection(
            projection_id=projection_id,
            site_ref=site,
            evaluation_window_instance_ref=window_instance,
            subject_ref=subject,
            member_refs=member_refs,
            monitoring_priority=priority,
            source_locator_refs=tuple(sorted(row["locators"])),
            projectability_decision_ref=(
                typed.visibility_decision.audience_scope_id),
        ))
    rows.sort(key=lambda row: (_PRIORITY_RANK.get(row.monitoring_priority, 99),
                               row.subject_ref))
    return tuple(rows)


# ---------------------------------------------------------------------------
# Verified one-hop deep links (contract sections 11/12/13)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10DeepLinkTarget:
    """One verified one-hop deep-link target.

    ``target_kind`` is one of ``member`` / ``site`` / ``subject_site_pair``
    and the target is bound to the exact typed eligible set, subject-site
    pair and visibility decision of the envelope (the evaluator already
    rejected any violation).  ``target_state`` is ``locatable`` only when
    the source locator resolves; otherwise it is ``unavailable`` with
    ``unavailable_message == 来源暂无法定位`` and no fabricated jump.
    ``return_state_key`` restores the originating projection state.
    """

    link_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    signal_definition_ref: str
    evaluation_window_instance_ref: str
    target_kind: str
    site_ref: Optional[str]
    subject_ref: Optional[str]
    member_object_ref: Optional[str]
    source_locator: Optional[str]
    locator_resolution_state: str
    target_state: str
    unavailable_message: Optional[str]
    visibility_decision_ref: str
    visibility_decision_hash: str
    return_state_key: str


def _deep_link_eligible_members(typed: D10TypedInput) -> Tuple[str, ...]:
    return tuple(sorted(set(
        typed.visibility_decision.deep_link_eligible_member_refs or ())))


def _deep_link_eligible_sites(typed: D10TypedInput) -> Tuple[str, ...]:
    return tuple(sorted(set(
        typed.visibility_decision.deep_link_eligible_site_refs or ())))


def _deep_link_eligible_pairs(
    typed: D10TypedInput,
) -> Tuple[Tuple[str, str], ...]:
    return tuple(sorted(set(
        tuple(p) for p in
        typed.visibility_decision.deep_link_eligible_subject_site_pairs or ())))


def build_d10_deep_links(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10DeepLinkTarget, ...]:
    """Project the typed deep-link targets (contract sections 11/12/13).

    The envelope's ``deep_links`` are the authoritative link set already
    validated against the visibility algebra by the deterministic
    evaluator.  This projection re-verifies the exact eligible-set /
    subject-site / visibility binding and emits an immutable target per
    link; unresolvable locators produce ``来源暂无法定位`` with no
    fabricated jump.  A submitted link that violates the eligible sets or
    the pair binding fails closed.
    """
    _assert_authoritative_result(typed, result)
    if result.unit is None:
        return ()
    member_by_ref = {m.member_ref: m for m in typed.members}
    eligible_members = set(_deep_link_eligible_members(typed))
    eligible_sites = set(_deep_link_eligible_sites(typed))
    eligible_pairs = set(_deep_link_eligible_pairs(typed))
    _eval_sites, proj_sites, _hidden_sites = _resolve_visibility_sites(typed, result)
    proj_site_set = set(proj_sites)
    window_instance = _evaluation_window_instance_ref(typed)
    visibility = typed.visibility_decision
    links: List[D10DeepLinkTarget] = []
    for link in typed.deep_links:
        if link.visibility_decision_ref != visibility.decision_id:
            raise D10ProjectionError(
                "deep link not bound to the current visibility decision")
        site_ref = link.site_ref
        subject_ref = link.subject_ref
        member_ref = link.member_object_ref
        member = member_by_ref.get(member_ref) if member_ref else None
        if link.target_kind == "member":
            if member_ref not in eligible_members or member is None:
                raise D10ProjectionError(
                    "member deep link outside the eligible member set")
            if member.site_stable_id not in proj_site_set:
                raise D10ProjectionError(
                    "member deep link targets a hidden site")
            if link.subject_ref != member.subject_stable_id \
                    or link.site_ref != member.site_stable_id:
                raise D10ProjectionError(
                    "member deep link subject/site mismatch")
            locator_state = getattr(member, "locator_resolution_state",
                                    "locatable")
            locator = _member_locator(member)
        elif link.target_kind == "site":
            if site_ref not in eligible_sites or site_ref not in proj_site_set:
                raise D10ProjectionError(
                    "site deep link outside the eligible/projectable site set")
            if subject_ref is not None or member_ref is not None:
                raise D10ProjectionError("site deep link carries extra refs")
            locator_state = "locatable"
            locator = None
        else:
            if (
                    subject_ref is None or site_ref is None
                    or (subject_ref, site_ref) not in eligible_pairs):
                raise D10ProjectionError(
                    "subject-site deep link outside the eligible pair set")
            if member_ref is not None:
                raise D10ProjectionError(
                    "subject-site deep link carries a member ref")
            potential = [m for m in typed.members
                         if m.subject_stable_id == subject_ref
                         and m.site_stable_id == site_ref]
            if not potential:
                raise D10ProjectionError(
                    "subject-site deep link has no resolvable member")
            locator_state = getattr(potential[0], "locator_resolution_state",
                                    "locatable")
            locator = _member_locator(potential[0])
        locatable = locator is not None and locator_state == "locatable"
        exposed_locator = locator if locatable else None
        link_id = d10_content_hash({
            "target_kind": link.target_kind,
            "site_ref": site_ref or "",
            "subject_ref": subject_ref or "",
            "member_ref": member_ref or "",
            "window_instance": window_instance,
            "locator": exposed_locator or "",
            "return_state_key": link.return_state_key,
            "visibility_decision_ref": visibility.decision_id,
        })
        links.append(D10DeepLinkTarget(
            link_id=link_id,
            project_ref=typed.project_ref,
            run_ref=typed.run_ref,
            snapshot_ref=typed.snapshot_ref,
            signal_definition_ref=typed.signal_definition.signal_definition_id,
            evaluation_window_instance_ref=window_instance,
            target_kind=link.target_kind,
            site_ref=site_ref,
            subject_ref=subject_ref,
            member_object_ref=member_ref,
            source_locator=exposed_locator,
            locator_resolution_state=locator_state,
            target_state="locatable" if locatable else "unavailable",
            unavailable_message=None if locatable else UNAVAILABLE_SOURCE_ZH,
            visibility_decision_ref=visibility.decision_id,
            visibility_decision_hash=visibility.decision_id,
            return_state_key=link.return_state_key,
        ))
    links.sort(key=lambda item: (
        item.target_kind, item.link_id))
    return tuple(links)


__all__ = [name for name in globals() if not name.startswith("__")]
