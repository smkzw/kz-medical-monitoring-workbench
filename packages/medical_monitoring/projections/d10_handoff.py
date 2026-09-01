"""R2 handoff and complete project projection orchestration."""

from .d10_core import *
from .d10_identity import *
from .d10_query import *
from .d10_change import *

# ---------------------------------------------------------------------------
# Replay-stable R2 lifecycle handoff (contract section 10)
# ---------------------------------------------------------------------------


def _completeness_decision_ref(typed: D10TypedInput,
                               result: D10RunResult) -> str:
    return d10_content_hash({
        "disposition_or_gate": result.disposition_or_gate,
        "primary_reason": result.primary_reason,
        "coverage_state": _coverage_state(typed),
        "denominator_state": typed.denominator.denominator_state,
    })


def _no_auto_close_reasons(typed: D10TypedInput,
                           result: D10RunResult) -> Tuple[str, ...]:
    """Closed no-auto-close reasons (contract section 10): high-priority
    members, carry-forward, broken coverage and hidden planes never propose
    closure."""
    reasons: List[str] = []
    members = typed.members
    if any(getattr(m, "monitoring_priority", None) == "high"
           for m in members):
        reasons.append("存在高监察优先级成员")
    if typed.change_decision is not None \
            and typed.change_decision.carry_forward_state == "active":
        reasons.append("本次可评价范围不完整，需维持进行中")
    if _coverage_state(typed) != "complete":
        reasons.append("覆盖不完整，需维持进行中")
    visibility = typed.visibility_decision
    if visibility.hidden_member_refs or visibility.hidden_site_refs:
        reasons.append("存在受限可见成员或中心，需维持进行中")
    return tuple(reasons)


def _max_member_priority(typed: D10TypedInput) -> Optional[str]:
    priorities = [m.monitoring_priority for m in typed.members
                  if getattr(m, "monitoring_priority", None)]
    if "high" in priorities:
        return "high"
    if "medium" in priorities:
        return "medium"
    return None


def _change_decision_hash(typed: D10TypedInput) -> str:
    ch = typed.change_decision
    if ch is None:
        return d10_content_hash({
            "execution_basis": "full", "comparison_state": "initial_full",
        })
    ca = ch.cutoff_advance
    return d10_content_hash({
        "execution_basis": ch.execution_basis,
        "comparison_state": ch.comparison_state,
        "prior_snapshot_ref_or_none": ch.prior_snapshot_ref_or_none,
        "data_change_refs": sorted(ch.data_change_refs),
        "denominator_change_refs": sorted(ch.denominator_change_refs),
        "coverage_change_refs": sorted(ch.coverage_change_refs),
        "knowledge_change_refs": sorted(ch.knowledge_change_refs),
        "rule_change_refs": sorted(ch.rule_change_refs),
        "mapping_change_refs": sorted(ch.mapping_change_refs),
        "model_change_refs": sorted(ch.model_change_refs),
        "method_change_refs": sorted(ch.method_change_refs),
        "population_change_refs": sorted(ch.population_change_refs),
        "visibility_change_refs": sorted(ch.visibility_change_refs),
        "mode_change_refs": sorted(ch.mode_change_refs),
        "data_change_kind": ch.data_change_kind,
        "lineage_relation": ch.lineage_relation,
        "r2_action": ch.r2_action,
        "r2_prior_ref_or_none": ch.r2_prior_ref_or_none,
        "carry_forward_state": ch.carry_forward_state,
        "cutoff_advance": {
            "decision_state": ca.decision_state if ca else None,
            "strict_advance_predicate_passed":
                ca.strict_advance_predicate_passed if ca else False,
            "policy_semantic_hash_equal":
                ca.policy_semantic_hash_equal if ca else False,
            "prior_boundary_value": ca.prior_boundary_value if ca else None,
            "current_boundary_value": ca.current_boundary_value if ca else None,
        },
    })


@dataclass(frozen=True)
class D10R2RiskHandoff:
    """Replay-stable R2 lifecycle handoff (contract section 10).

    ``handoff_id`` and ``idempotency_key`` are equal and derive from the
    public D10 risk identity, the current evaluation content identity, the
    action, the prior instance ref, the lineage relation and the change/
    completeness hashes -- never from opaque run/snapshot ids.

    Action constraints (closed): ``create`` is the only action without a
    prior ref and requires a create-legal lineage; every other action
    requires BOTH the prior instance ref and a compatible lineage.  The
    handoff is emitted for positive units only and never proposes closure
    for high-priority/carry-forward/coverage-restricted states.  No R2
    lifecycle object is created or updated -- the handoff is a contract
    emission only.
    """

    handoff_id: str
    idempotency_key: str
    public_d10_risk_identity: Dict[str, Any]
    stable_core_ref: str
    current_evaluation_content_ref: str
    run_snapshot_audit_refs: Tuple[str, ...]
    prior_risk_instance_ref: Optional[str]
    action: str
    lineage_relation: str
    change_decision_ref: str
    completeness_decision_ref: str
    member_refs: Tuple[str, ...]
    measure_ledger_ref: str
    monitoring_priority: Optional[str]
    no_auto_close_reasons: Tuple[str, ...]


def _derive_r2_handoff_action(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[Optional[str], str, Optional[str]]:
    """Derive ``(action, lineage_relation, prior_risk_instance_ref)`` for a
    positive unit (contract section 10).

    Every positive D10 unit emits an R2 handoff:

    * a declared ``r2_action`` on the typed change decision is authoritative
      (its consistency with the prior ref and lineage was already validated
      by the deterministic evaluator; any contradiction is an integrity
      gate);
    * an initial-full (or data-revision / strict cutoff-advance) positive
      with no prior R2 risk and no explicit transition derives ``create``
      with the create-legal lineage --- ``create`` is never mapped to a
      ``新增`` R5 display and never invents a prior;
    * a positive unit with a prior instance and no declared action derives
      ``continue`` (the signal persists on the same public identity).

    The derivation reads only the authoritative result and typed facts; it
    never re-runs the medical evaluator.
    """
    ch = typed.change_decision
    declared = ch.r2_action if ch else ""
    prior = ch.r2_prior_ref_or_none if ch else None
    lineage = ch.lineage_relation if ch else ""
    if declared:
        return declared, lineage, prior
    if ch is None or (prior is None
                      and _non_data_change_ref_count(ch) == 0
                      and ch.comparison_state != "not_comparable"):
        lineage = lineage or ("initial_full_snapshot"
                              if ch is None or ch.execution_basis == "full"
                              else "continued_from_data_revision")
        return "create", lineage, None
    lineage = lineage or "continued_from_data_revision"
    return "continue", lineage, prior


def build_d10_r2_handoff(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Optional[D10R2RiskHandoff]:
    """Build the R2 lifecycle handoff for a positive unit.

    Every positive D10 unit emits exactly one handoff (contract section 10).
    The action is derived deterministically: a declared ``r2_action`` is
    authoritative, otherwise an initial-full positive derives ``create``
    and a prior-bearing positive derives ``continue``.  The closed action
    x lineage x prior matrix is re-checked from the typed facts and fails
    closed on any contradiction (the evaluator already rejected them at
    evaluation time).  Non-positive runs and all gates emit no handoff."""
    _assert_authoritative_result(typed, result)
    unit = result.unit
    if unit is None or unit.l1_disposition != "positive":
        return None
    action, lineage, prior = _derive_r2_handoff_action(typed, result)
    ch = typed.change_decision
    if action != "create":
        if prior is None:
            raise D10ProjectionError(
                f"non-create action {action!r} without a prior instance ref")
    else:
        if prior is not None:
            raise D10ProjectionError(
                "create action with a prior instance ref")
        if lineage not in (
                "initial_full_snapshot",
                "continued_from_data_revision",
                "continued_from_cutoff_advance"):
            raise D10ProjectionError(
                f"create action with create-illegal lineage {lineage!r}")
        if (ch is not None
                and (_non_data_change_ref_count(ch) > 0
                     or ch.comparison_state == "not_comparable")):
            raise D10ProjectionError(
                "create action with non-data change or non-comparable state")
        if lineage == "continued_from_cutoff_advance":
            ca = ch.cutoff_advance
            if ca is None or ca.decision_state != "strict_advance" \
                    or not ca.strict_advance_predicate_passed \
                    or not ca.policy_semantic_hash_equal:
                raise D10ProjectionError(
                    "cutoff-advance create without a strictly advanced "
                    "derived cutoff decision")
    if action == "supersede":
        if not (lineage.startswith("superseded_by_")
                or lineage == "coverage_regressed"):
            raise D10ProjectionError(
                f"supersede action with non-superseded lineage {lineage!r}")
    if action in ("continue", "update", "propose_close", "reopen"):
        if lineage not in ("continued_from_data_revision",
                           "continued_from_cutoff_advance", "none", ""):
            raise D10ProjectionError(
                f"{action} action with incompatible lineage {lineage!r}")
    public_identity = d10_public_risk_identity(typed)
    evaluation_content = result.evaluation_content_identity
    member_refs = tuple(sorted(
        set(m.member_ref for m in typed.members)))
    measure_ledger_ref = _measure_ledger_ref(typed, result)
    completeness_ref = _completeness_decision_ref(typed, result)
    change_ref = _change_decision_hash(typed)
    no_auto_close = _no_auto_close_reasons(typed, result)
    monitoring_priority = _max_member_priority(typed)
    handoff_id = d10_content_hash({
        "public_d10_risk_identity": public_identity,
        "evaluation_content_identity": evaluation_content,
        "action": action,
        "lineage_relation": lineage,
        "prior_risk_instance_ref": prior,
        "change_decision_hash": change_ref,
        "completeness_decision_hash": completeness_ref,
    })
    return D10R2RiskHandoff(
        handoff_id=handoff_id,
        idempotency_key=handoff_id,
        public_d10_risk_identity=public_identity,
        stable_core_ref=unit.stable_core_ref,
        current_evaluation_content_ref=evaluation_content,
        run_snapshot_audit_refs=(typed.run_ref, typed.snapshot_ref),
        prior_risk_instance_ref=prior,
        action=action,
        lineage_relation=lineage,
        change_decision_ref=change_ref,
        completeness_decision_ref=completeness_ref,
        member_refs=member_refs,
        measure_ledger_ref=measure_ledger_ref,
        monitoring_priority=monitoring_priority,
        no_auto_close_reasons=no_auto_close,
    )


def validate_d10_r2_handoff(
    handoff: D10R2RiskHandoff,
    typed: D10TypedInput,
    result: D10RunResult,
) -> Dict[str, Any]:
    """Closed validation of a D10 R2 handoff (contract section 10)."""
    reasons: List[str] = []
    try:
        _assert_authoritative_result(typed, result)
    except D10ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    if result.unit is None or result.unit.l1_disposition != "positive":
        reasons.append("handoff_requires_positive_unit")
    expected_action, expected_lineage, expected_prior = \
        _derive_r2_handoff_action(typed, result)
    if handoff.action != expected_action:
        reasons.append(f"action_mismatch:{handoff.action}")
    if handoff.lineage_relation != expected_lineage:
        reasons.append("lineage_relation_mismatch")
    if handoff.prior_risk_instance_ref != expected_prior:
        reasons.append("prior_ref_mismatch")
    if handoff.action not in (
            "create", "continue", "update", "propose_close", "reopen",
            "supersede"):
        reasons.append(f"action_not_d10_vocabulary:{handoff.action}")
    if handoff.action == "create":
        if handoff.prior_risk_instance_ref is not None:
            reasons.append("create_with_prior_ref")
        if expected_lineage not in (
                "initial_full_snapshot", "continued_from_data_revision",
                "continued_from_cutoff_advance"):
            reasons.append("create_with_illegal_lineage")
    else:
        if handoff.prior_risk_instance_ref is None:
            reasons.append("non_create_without_prior_ref")
        if handoff.action == "supersede":
            if not expected_lineage.startswith("superseded_by_") \
                    and expected_lineage != "coverage_regressed":
                reasons.append("supersede_without_superseded_lineage")
        if handoff.action in ("continue", "update", "propose_close",
                              "reopen"):
            if expected_lineage not in (
                    "continued_from_data_revision",
                    "continued_from_cutoff_advance", "none", ""):
                reasons.append("incompatible_continuation_lineage")
    expected_handoff_id = d10_content_hash({
        "public_d10_risk_identity": d10_public_risk_identity(typed),
        "evaluation_content_identity": result.evaluation_content_identity,
        "action": handoff.action,
        "lineage_relation": handoff.lineage_relation,
        "prior_risk_instance_ref": handoff.prior_risk_instance_ref,
        "change_decision_hash": _change_decision_hash(typed),
        "completeness_decision_hash": _completeness_decision_ref(typed, result),
    })
    if handoff.handoff_id != expected_handoff_id:
        reasons.append("handoff_id_stale")
    if handoff.idempotency_key != handoff.handoff_id:
        reasons.append("idempotency_key_mismatch")
    if handoff.current_evaluation_content_ref \
            != result.evaluation_content_identity:
        reasons.append("evaluation_content_identity_stale")
    if handoff.public_d10_risk_identity != d10_public_risk_identity(typed):
        reasons.append("public_risk_identity_stale")
    if handoff.stable_core_ref != (result.unit.stable_core_ref
                                   if result.unit is not None else ""):
        reasons.append("stable_core_stale")
    if handoff.change_decision_ref != _change_decision_hash(typed):
        reasons.append("change_decision_hash_stale")
    if handoff.completeness_decision_ref \
            != _completeness_decision_ref(typed, result):
        reasons.append("completeness_decision_hash_stale")
    if handoff.run_snapshot_audit_refs != (typed.run_ref, typed.snapshot_ref):
        reasons.append("run_snapshot_audit_refs_mismatch")
    expected_member_refs = tuple(sorted(
        set(m.member_ref for m in typed.members)))
    if handoff.member_refs != expected_member_refs:
        reasons.append("member_refs_mismatch")
    if handoff.measure_ledger_ref != _measure_ledger_ref(typed, result):
        reasons.append("measure_ledger_ref_mismatch")
    if handoff.monitoring_priority != _max_member_priority(typed):
        reasons.append("monitoring_priority_mismatch")
    if handoff.no_auto_close_reasons != _no_auto_close_reasons(typed, result):
        reasons.append("no_auto_close_reasons_mismatch")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Project projection and bundle (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectProjection:
    """The complete project projection for one run (contract section 12).

    Immutable and renderer-neutral: change section, center distribution,
    trend surface, warnings, hotspot refs, count-surface ref, deep links,
    Query draft and R2 handoff refs are bound to one projection version and
    content hash.  R5 may render this object; it must never recompute the
    underlying numbers."""

    projection_id: str
    projection_version_ref: str
    change_section: D10ChangeSection
    center_distribution: Tuple[D10CenterPatternRow, ...]
    trend_surface: D10TrendSurface
    warning_markers: Tuple[D10WarningMarker, ...]
    risk_marker_ref: Optional[str]
    hotspot_site_refs: Tuple[str, ...]
    hotspot_subject_refs: Tuple[str, ...]
    count_surface_ref: str
    coverage_refs: Tuple[str, ...]
    deep_link_target_refs: Tuple[str, ...]
    query_draft_ref: Optional[str]
    r2_handoff_ref: Optional[str]
    audience_text_ref: str
    projection_content_hash: str


def build_d10_project_projection(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectProjection:
    """Build the complete project projection (contract section 12)."""
    _assert_authoritative_result(typed, result)
    version = build_d10_projection_version(typed, result)
    counts = build_d10_count_surface(typed, result)
    change = build_d10_change_section(typed, result)
    centers = build_d10_center_distribution(typed, result)
    trend = build_d10_trend_surface(typed, result)
    warnings = build_d10_warnings(typed, result)
    hotspots = build_d10_hotspots(typed, result)
    links = build_d10_deep_links(typed, result)
    query = build_d10_query_draft(typed, result)
    handoff = build_d10_r2_handoff(typed, result)
    risk = build_d10_risk_marker(typed, result)
    coverage_refs = tuple(sorted(set(
        locator for c in typed.coverage for locator in c.coverage_locator_ids)))
    count_surface_ref = d10_content_hash({
        "evaluation_window_instance_ref": counts.evaluation_window_instance_ref,
        "individual_risk_count": counts.individual_risk_count,
        "affected_subject_count": counts.affected_subject_count,
        "event_or_outcome_count": counts.event_or_outcome_count,
        "center_pattern_count": counts.center_pattern_count,
        "affected_site_count": counts.affected_site_count,
        "project_signal_count": counts.project_signal_count,
        "clue_count": counts.clue_count,
        "query_count": counts.query_count,
        "hidden_member_count": counts.hidden_member_count,
        "hidden_site_count": counts.hidden_site_count,
    })
    projection_core = {
        "change_kind": change.change_kind,
        "center_site_refs": [row.site_ref for row in centers],
        "trend_surface_present": trend.trend_surface_present,
        "warning_refs": [w.reason_code for w in warnings],
        "risk_marker_ref": risk.marker_id if risk else None,
        "hotspot_refs": [h.projection_id for h in hotspots],
        "count_surface_ref": count_surface_ref,
        "coverage_refs": list(coverage_refs),
        "deep_link_refs": [link.link_id for link in links],
        "query_draft_id": query.query_draft_id if query else None,
        "r2_handoff_id": handoff.handoff_id if handoff else None,
        "audience_text_ref": typed.audience_text.audience_contract_id,
        "algorithm_version": _ALGORITHM_VERSION,
    }
    projection_content_hash = d10_content_hash(projection_core)
    projection_id = d10_content_hash({
        "projection_version_id": version.projection_version_id,
        "projection_content_hash": projection_content_hash,
    })
    return D10ProjectProjection(
        projection_id=projection_id,
        projection_version_ref=version.projection_version_id,
        change_section=change,
        center_distribution=centers,
        trend_surface=trend,
        warning_markers=warnings,
        risk_marker_ref=risk.marker_id if risk else None,
        hotspot_site_refs=tuple(sorted({
            h.site_ref for h in hotspots})),
        hotspot_subject_refs=tuple(sorted({
            h.subject_ref for h in hotspots})),
        count_surface_ref=count_surface_ref,
        coverage_refs=coverage_refs,
        deep_link_target_refs=tuple(link.link_id for link in links),
        query_draft_ref=query.query_draft_id if query else None,
        r2_handoff_ref=handoff.handoff_id if handoff else None,
        audience_text_ref=typed.audience_text.audience_contract_id,
        projection_content_hash=projection_content_hash,
    )


def validate_d10_project_projection(
    projection: D10ProjectProjection,
    typed: D10TypedInput,
    result: D10RunResult,
) -> Dict[str, Any]:
    """Closed authoritative rebuild of the project projection: the
    submitted object must equal a fresh rebuild of every leaf surface, so a
    re-signed tampered projection cannot pass."""
    reasons: List[str] = []
    try:
        expected = build_d10_project_projection(typed, result)
    except D10ProjectionError as error:
        return {"valid": False, "reasons": [str(error)]}
    if projection != expected:
        reasons.append("project_projection_not_exact_authoritative_rebuild")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10ProjectionBundle:
    """Complete renderer-neutral projection of one run."""

    audience: D10AudienceProjection
    counts: D10ProjectionCountSurface
    version: D10ProjectionVersion
    change_section: D10ChangeSection
    center_distribution: Tuple[D10CenterPatternRow, ...]
    trend_surface: D10TrendSurface
    warning_markers: Tuple[D10WarningMarker, ...]
    risk_marker: Optional[D10RiskMarker]
    hotspots: Tuple[D10HotspotProjection, ...]
    deep_links: Tuple[D10DeepLinkTarget, ...]
    query_draft: Optional[D10QueryDraft]
    r2_handoff: Optional[D10R2RiskHandoff]
    project_projection: D10ProjectProjection


def project_d10_run(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ProjectionBundle:
    """Project a validated typed run onto all renderer-neutral surfaces."""
    return D10ProjectionBundle(
        audience=build_d10_audience_projection(typed, result),
        counts=build_d10_count_surface(typed, result),
        version=build_d10_projection_version(typed, result),
        change_section=build_d10_change_section(typed, result),
        center_distribution=build_d10_center_distribution(typed, result),
        trend_surface=build_d10_trend_surface(typed, result),
        warning_markers=build_d10_warnings(typed, result),
        risk_marker=build_d10_risk_marker(typed, result),
        hotspots=build_d10_hotspots(typed, result),
        deep_links=build_d10_deep_links(typed, result),
        query_draft=build_d10_query_draft(typed, result),
        r2_handoff=build_d10_r2_handoff(typed, result),
        project_projection=build_d10_project_projection(typed, result),
    )


__all__ = [name for name in globals() if not name.startswith("__")]
