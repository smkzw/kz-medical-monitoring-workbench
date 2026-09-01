"""Protocol unit materialization and slice orchestration."""

from __future__ import annotations

import datetime
import itertools
from dataclasses import dataclass
from types import MappingProxyType
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Set,
                    Tuple)

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from ..intelligence.normalization import normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    EvaluationUnit,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)

from .protocol_contracts import *
from .protocol_contracts import _GAP_LABELS, _canonical_sorted, _validate_nonempty
from .protocol_applicability import *
from .protocol_evidence import *
from .protocol_evidence import _gap_notice
from .protocol_component_evaluation import *
from .protocol_risk_projection import *
from .protocol_risk_projection import (
    _build_d04_candidate, _build_query_ref, _component_assessment,
    _evaluate_gate_unit, _evaluation_window_id, _make_source_record_ref,
)

# ---------------------------------------------------------------------------
# Core evaluation: evaluate_protocol_unit
# ---------------------------------------------------------------------------

def evaluate_protocol_unit(
    *,
    project_id: str,
    expanded: ProtocolUnitExpanded,
    bindings: Sequence[RuleEvidenceBinding] = (),
    coverage_complete_roles: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcomes: Optional[Mapping[str, RetestOutcome]] = None,
    enrollment_context: Optional[EnrollmentContext] = None,
    priority_policy: Optional[D04PriorityPolicy] = None,
    snapshot_id: str = "",
) -> ProtocolUnitResult:
    """Evaluate one D04 expanded unit (§5, §6).

    * applicability/routing gates produce subject-level blocking units
      (no candidate/risk/Query);
    * atomic roots evaluate their single component;
    * package roots evaluate every component then run the parent issue
      expression over feasible uncertain assignments;
    * positive units carry at most one candidate + one Query (deciding
      components listed, unresolved gaps preserved); negative units carry
      none; boundary units carry a clue candidate only; not_evaluable
      units carry zero candidate/risk/Query plus a coverage-gap notice;
    * L0/L1 are orthogonal: a determinate L1 with an unresolved component
      gap keeps L0 partial and blocks domain completeness.
    """
    coverage = dict(coverage_complete_roles or {})
    retests = dict(retest_outcomes or {})
    unit = expanded.build_unit(project_id)
    unit_id = unit.unit_id

    if expanded.evaluation_node_id in (NODE_APPLICABILITY_GATE,
                                       NODE_ROUTING_GATE):
        return _evaluate_gate_unit(project_id=project_id, expanded=expanded)

    assert expanded.control_point is not None
    cp = expanded.control_point
    rule_lineage = (
        expanded.plan.rule_content_hash or D04_RULE_LINEAGE_DEFAULT)
    window = expanded.window
    window_id = _evaluation_window_id(
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity)

    if expanded.control_point_not_applicable:
        return _not_applicable_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window_id=window_id, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)

    # -- atomic root ------------------------------------------------------
    if expanded.evaluation_node_id == NODE_ATOMIC:
        assert cp.structured_rule is not None
        component = ProtocolComponent(
            component_id=cp.control_point_id,
            control_point_id=cp.control_point_id,
            official_criterion_id=cp.official_criterion_id,
            parent_rule_id=cp.parent_rule_id,
            display_order=cp.display_order,
            nesting_path=cp.nesting_path,
            verbatim_text=cp.verbatim_text,
            source_locator=cp.source_locator,
            source_revision_hash=cp.source_revision_hash,
            structured_rule=cp.structured_rule,
            verification_status=cp.verification_status)
        component_bindings = _bindings_for_component(
            component.component_id, bindings, expanded)
        requirement = _requirement_for_component(
            component.component_id, expanded)
        outcome = evaluate_component_condition(
            unit_id=unit_id, component=component,
            bindings=component_bindings,
            coverage_complete_roles=coverage,
            exceptions=exceptions,
            unit_conversion_rules=unit_conversion_rules,
            retest_outcome=retests.get(component.component_id),
            subject_ref=expanded.subject_ref, site_ref=expanded.site_ref,
            evidence_requirement=requirement)
        predicate = component_issue_predicate(
            cp.control_point_type, outcome.verdict)
        if predicate == ISSUE_NOT_APPLICABLE:
            if expanded.control_point_not_applicable:
                return _not_applicable_unit(
                    project_id=project_id, expanded=expanded,
                    unit_id=unit_id, cp=cp, window_id=window_id,
                    rule_lineage=rule_lineage, snapshot_id=snapshot_id)
            predicate = ISSUE_NOT_EVALUABLE
        if predicate == ISSUE_TRUE:
            disposition = L1Disposition.POSITIVE
        elif predicate == ISSUE_FALSE:
            disposition = L1Disposition.NEGATIVE
        else:
            disposition = predicate  # boundary/not_evaluable share L1 tokens
        affected_ids = ((component.component_id,)
                        if predicate in (ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY)
                        else ())
        missing_roles = _missing_evidence_roles(
            expanded=expanded, affected_component_ids=affected_ids,
            bindings=bindings, coverage=coverage)
        assessment = _component_assessment(
            unit_id=unit_id, component=component, predicate=predicate,
            outcome=outcome, rule_lineage=rule_lineage)
        return _materialize_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window=window, window_id=window_id,
            predicate=disposition, assessments=(assessment,),
            outcomes=(outcome,), decisive_ids=(),
            unresolved_ids=(
                (component.component_id,) if predicate in (
                    ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY) else ()),
            rule_lineage=rule_lineage, snapshot_id=snapshot_id,
            enrollment_context=enrollment_context,
            priority_policy=priority_policy,
            missing_evidence_roles=missing_roles)

    # -- package root -----------------------------------------------------
    assert expanded.issue_expression is not None
    if expanded.plan.verification_status != "verified":
        # Original 任一/全部/至少 N semantics not unambiguously resolved:
        # the whole root is not_evaluable; AND/OR is never defaulted
        # (challenge 82).
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_RULE_NOT_VERIFIED,
            protocol_locator_ids=(cp.source_locator.locator_id(),),
            reachable_source_locator_ids=(cp.source_locator.locator_id(),))
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=(
                "规则抽取未经验证，任一/全部/至少 N 关系无法无歧义确定，"
                "禁止默认组合关系"),
            source_record_refs=(_make_source_record_ref(cp.source_locator),),
            coverage_gap_notices=(notice,),
            unresolved_component_ids=tuple(expanded.component_ids),
            protocol_locator_ids=(cp.source_locator.locator_id(),),
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    component_results: Dict[str, str] = {}
    assessments: List[ProtocolComponentAssessment] = []
    outcomes_by_id: Dict[str, ComponentConditionOutcome] = {}
    for cid in expanded.component_ids:
        component = _require_component(cid, expanded)
        component_bindings = _bindings_for_component(
            cid, bindings, expanded)
        requirement = _requirement_for_component(cid, expanded)
        outcome = evaluate_component_condition(
            unit_id=unit_id, component=component,
            bindings=component_bindings,
            coverage_complete_roles=coverage,
            exceptions=exceptions,
            unit_conversion_rules=unit_conversion_rules,
            retest_outcome=retests.get(cid),
            subject_ref=expanded.subject_ref, site_ref=expanded.site_ref,
            evidence_requirement=requirement)
        predicate = component_issue_predicate(
            cp.control_point_type, outcome.verdict)
        if predicate == ISSUE_NOT_APPLICABLE and not expanded.control_point_not_applicable:
            predicate = ISSUE_NOT_EVALUABLE
        component_results[cid] = predicate
        outcomes_by_id[cid] = outcome
        assessments.append(_component_assessment(
            unit_id=unit_id, component=component, predicate=predicate,
            outcome=outcome, rule_lineage=rule_lineage))

    expr_eval = evaluate_issue_expression(
        expanded.issue_expression, component_results,
        all_not_applicable=all(
            r == ISSUE_NOT_APPLICABLE for r in component_results.values()),
        control_point_authoritatively_not_applicable=(
            expanded.control_point_not_applicable))
    affected_ids = tuple(
        cid for cid, r in component_results.items()
        if r in (ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY))
    missing_roles = _missing_evidence_roles(
        expanded=expanded, affected_component_ids=affected_ids,
        bindings=bindings, coverage=coverage)
    return _materialize_unit(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        cp=cp, window=window, window_id=window_id,
        predicate=expr_eval.disposition, assessments=tuple(assessments),
        outcomes=tuple(outcomes_by_id[cid]
                       for cid in expanded.component_ids),
        decisive_ids=expr_eval.decisive_component_ids,
        unresolved_ids=expr_eval.gap_component_ids,
        rule_lineage=rule_lineage, snapshot_id=snapshot_id,
        enrollment_context=enrollment_context,
        priority_policy=priority_policy,
        forced_reason=(
            expr_eval.reason
            if expr_eval.disposition == L1Disposition.NOT_EVALUABLE
            else ""),
        missing_evidence_roles=missing_roles)


def _bindings_for_component(
    component_id: str, bindings: Sequence[RuleEvidenceBinding],
    expanded: ProtocolUnitExpanded,
) -> Tuple[RuleEvidenceBinding, ...]:
    """Select bindings for one component (§4.2).

    Bindings for another subject/site/control point are ordinary
    non-matching evidence in a multi-subject accepted listing and are
    excluded, never a fatal kernel error.  When no valid required
    evidence remains the operator evaluation fails closed to
    ``not_evaluable`` with a missing-role/identity coverage notice and
    zero candidate/risk/Query.  Unconfirmed cross-domain relations are
    still handled explicitly inside the component evaluator.
    """
    matched: List[RuleEvidenceBinding] = []
    for b in bindings:
        if b.component_id != component_id:
            continue
        if (b.control_point_id
                != (expanded.control_point.control_point_id
                    if expanded.control_point is not None else "")):
            continue
        if (b.subject_ref != expanded.subject_ref
                or b.site_ref != expanded.site_ref):
            continue
        matched.append(b)
    return tuple(matched)


def _require_component(
    component_id: str, expanded: ProtocolUnitExpanded,
) -> ProtocolComponent:
    if not expanded.components:
        raise ProtocolSliceError(
            f"package {expanded.control_point.control_point_id} has no "
            f"component map; supply components to expand_protocol_expected_set")
    component = expanded.components.get(component_id)
    if component is None:
        raise ProtocolSliceError(
            f"unknown component {component_id!r} for package unit")
    return component


def _requirement_for_component(
    component_id: str, expanded: ProtocolUnitExpanded,
) -> RuleEvidenceRequirement:
    """Return the generated evidence requirement for one component.

    The generated ``evidence_requirements`` are the authoritative
    evidence-role contract (§4.2): evaluation never re-derives a second
    role list from the structured rule.  A missing requirement fails
    closed -- no silent inference.
    """
    for req in expanded.evidence_requirements:
        if req.component_id == component_id:
            return req
    cp_id = (expanded.control_point.control_point_id
             if expanded.control_point is not None else "")
    raise ProtocolSliceError(
        f"no generated RuleEvidenceRequirement for component "
        f"{component_id!r} under control point {cp_id!r}")


def _not_applicable_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded, unit_id: str,
    cp: ProtocolControlPoint, window_id: str, rule_lineage: str,
    snapshot_id: str,
) -> ProtocolUnitResult:
    """Materialize an authoritatively not-applicable control point (§6.5).

    Only active protocol/design, cohort/phase and subject scope jointly
    prove non-applicability; no record, no mapping and "model cannot
    judge" are never not_applicable.
    """
    window = expanded.window
    src_ref = _make_source_record_ref(cp.source_locator)
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.NOT_APPLICABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        l0_status=L0CoverageStatus.NOT_APPLICABLE,
        source_record_refs=(src_ref,),
        protocol_locator_ids=(cp.source_locator.locator_id(),),
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity,
        evaluation_window_id=window_id,
        control_point_id=cp.control_point_id,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type,
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)


def _missing_evidence_roles(
    *,
    expanded: ProtocolUnitExpanded,
    affected_component_ids: Sequence[str],
    bindings: Sequence[RuleEvidenceBinding],
    coverage: Mapping[str, bool],
) -> Tuple[str, ...]:
    """Semantic evidence roles required by the affected components that
    are absent or uncovered for this specific unit (§6.4).

    The role contract comes exclusively from the generated
    ``RuleEvidenceRequirement`` for each affected component -- never from
    a role list re-derived off the structured rule during evaluation.  A
    missing requirement fails closed.  Only real evidence roles are
    returned -- never reason codes, gap tokens or component ids.  A gap
    with no missing role (e.g. an ambiguous expression) returns an empty
    tuple.  ``coverage`` decides "uncovered": a role is missing when no
    identity-matched binding for the affected component carries it or the
    role's accepted-source coverage is not complete (unless the
    requirement explicitly waives completeness).
    """
    required: Set[str] = set()
    cp_id = (expanded.control_point.control_point_id
             if expanded.control_point is not None else "")
    for cid in affected_component_ids:
        requirement = _requirement_for_component(cid, expanded)
        matched_roles: Set[str] = {
            b.source_role for b in bindings
            if b.component_id == cid
            and b.control_point_id == cp_id
            and b.subject_ref == expanded.subject_ref
            and b.site_ref == expanded.site_ref
        }
        for role in requirement.required_evidence_roles:
            if role in matched_roles and (
                    coverage.get(role, False)
                    or not requirement.coverage_complete_required):
                continue
            required.add(role)
    return tuple(sorted(required))


def _materialize_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded, unit_id: str,
    cp: ProtocolControlPoint, window: EvaluationWindowSpec, window_id: str,
    predicate: str, assessments: Tuple[ProtocolComponentAssessment, ...],
    outcomes: Tuple[ComponentConditionOutcome, ...],
    decisive_ids: Sequence[str], unresolved_ids: Sequence[str],
    rule_lineage: str, snapshot_id: str,
    enrollment_context: Optional[EnrollmentContext],
    priority_policy: Optional[D04PriorityPolicy],
    forced_reason: str = "",
    missing_evidence_roles: Sequence[str] = (),
) -> ProtocolUnitResult:
    """Materialize the final ProtocolUnitResult for one evaluation root
    (§6).  L0/L1 orthogonality: determinate L1 with unresolved component
    gaps keeps L0 partial + a coverage-gap notice; L1 not_evaluable
    carries zero candidate/risk/Query."""
    subtype = cp.positive_subtype()
    audience = SUBTYPE_LABELS[subtype]
    decisive = _canonical_sorted(decisive_ids)
    unresolved = _canonical_sorted(unresolved_ids)
    protocol_loc_ids = _canonical_sorted(
        (cp.source_locator.locator_id(),))

    # -- evidence aggregation ---------------------------------------------
    evidence: List[EvidenceItem] = []
    gap_codes: Set[str] = set()
    gaps: Set[str] = set()
    fact_parts: List[str] = []
    for outcome in outcomes:
        evidence.extend(outcome.supporting)
        evidence.extend(outcome.counterevidence)
        evidence.extend(outcome.context)
        gap_codes.update(outcome.gap_codes)
        gaps.update(outcome.gaps)
        if outcome.reason:
            fact_parts.append(outcome.reason)

    # -- source records ---------------------------------------------------
    # Every unique accepted evidence locator plus the protocol control-point
    # locator becomes a SourceRecordRef, deterministically deduplicated by
    # locator id.  Source/evidence/candidate/risk/Query counts stay separate
    # (§11).
    loc_by_id: Dict[str, SourceLocator] = {
        cp.source_locator.locator_id(): cp.source_locator}
    for ev in evidence:
        loc_by_id.setdefault(ev.locator.locator_id(), ev.locator)
    src_refs: List[SourceRecordRef] = [
        _make_source_record_ref(loc_by_id[lid])
        for lid in sorted(loc_by_id)]

    l0 = _l0_for(predicate=predicate, unresolved_ids=unresolved)

    if predicate == L1Disposition.NOT_APPLICABLE:
        return _not_applicable_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window_id=window_id, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)

    # -- coverage-gap notice ----------------------------------------------
    # ``missing_evidence_roles`` holds only real semantic evidence roles
    # (absent/uncovered for this unit); reason codes stay in
    # ``reason_code`` and unresolved component ids in
    # ``unresolved_component_ids`` -- never mixed into the role field
    # (§6.4, finding 2).
    notices: List[ProtocolCoverageGapNotice] = []
    if predicate == L1Disposition.NOT_EVALUABLE:
        reason_code = _primary_gap_code(gap_codes)
        notice = _gap_notice(
            unit_id=unit_id, reason_code=reason_code,
            missing_evidence_roles=tuple(
                _canonical_sorted(missing_evidence_roles)),
            protocol_locator_ids=protocol_loc_ids,
            reachable_source_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})) or protocol_loc_ids,
            audience_text=(
                _GAP_LABELS.get(reason_code, "资料不足，暂无法核实")))
        notices.append(notice)
    elif predicate in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE) \
            and unresolved:
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_COMPONENT_GAP_DETERMINATE,
            missing_evidence_roles=tuple(
                _canonical_sorted(missing_evidence_roles)),
            protocol_locator_ids=protocol_loc_ids,
            reachable_source_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})) or protocol_loc_ids)
        notices.append(notice)

    # -- result per disposition -------------------------------------------
    if predicate == L1Disposition.NEGATIVE:
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=l0, evidence=tuple(evidence),
            source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    if predicate == L1Disposition.BOUNDARY:
        # Boundary: a clue candidate (uncertainty preserved), no Query.
        priority = MONITORING_PRIORITY_UNKNOWN
        candidate, identity = _build_d04_candidate(
            project_id=project_id, subject_ref=expanded.subject_ref,
            site_ref=expanded.site_ref, control_point=cp,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type, window=window,
            plan=expanded.plan, applicability=expanded.applicability,
            snapshot_id=snapshot_id, monitoring_priority=priority,
            positive_subtype=subtype,
            audience_label=f"{audience}（边界）",
            match_reason="边界：真/假均可行，需进一步核实",
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved)
        cand_ref = RiskCandidateRef(
            candidate_id=candidate.candidate_id,
            risk_identity_id=identity.risk_identity_id,
            locator=cp.source_locator)
        marker = ProtocolRiskMarker(
            marker_id=f"marker-{unit_id}",
            risk_family=expanded.signal_type,
            audience_label=f"{audience}（边界）",
            monitoring_priority=priority,
            anchor_kind=window.eval_anchor_kind,
            anchor_start=window.window_start, anchor_end=window.window_end,
            date_precision=window.precision,
            unit_id=unit_id,
            candidate_or_risk_id=candidate.candidate_id,
            protocol_locator_ids=protocol_loc_ids,
            supporting_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})),
            counterevidence_locator_ids=tuple(sorted({
                ev.locator.locator_id()
                for ev in outcomes
                for ev in ev.counterevidence})),
            coverage_gap=bool(unresolved))
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.BOUNDARY,
            monitoring_priority=priority, l0_status=l0,
            r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
            evidence=tuple(evidence), source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            boundary_reason="边界：多个可行解释均有来源支持或阈值/端点未定义",
            audience_label=f"{audience}（边界）",
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            journey_markers=(marker,),
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    if predicate == L1Disposition.NOT_EVALUABLE:
        parts = [forced_reason] if forced_reason else []
        parts.extend(sorted(gaps))
        reason = "；".join(parts) if parts else "资料不足，暂无法核实"
        if forced_reason and not gaps:
            reason = forced_reason
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=reason,
            evidence=tuple(evidence), source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    # -- positive ---------------------------------------------------------
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(subtype)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    critical = (
        priority_policy.critical_for_subtype(subtype)
        if priority_policy is not None else False)
    close_forbidden = (
        priority_policy.machine_close_forbidden_for_subtype(subtype)
        if priority_policy is not None else False)
    candidate, identity = _build_d04_candidate(
        project_id=project_id, subject_ref=expanded.subject_ref,
        site_ref=expanded.site_ref, control_point=cp,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type, window=window,
        plan=expanded.plan, applicability=expanded.applicability,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        positive_subtype=subtype, audience_label=audience,
        match_reason="；".join(fact_parts) or "方案要求与已接受数据不一致",
        decisive_component_ids=decisive,
        unresolved_component_ids=unresolved,
        rights_or_safety_critical=critical,
        machine_close_forbidden=close_forbidden)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=cp.source_locator)

    ctx = enrollment_context
    if ctx is None:
        ctx = EnrollmentContext(
            subject_ref=expanded.subject_ref,
            query_context=QUERY_CONTEXT_UNRESOLVED,
            rationale="未提供入组情境，默认资料不足")
    query_loc_ids = _canonical_sorted({
        ref.locator.locator_id() for ref in src_refs
    } | {ev.locator.locator_id() for ev in evidence}
      | set(protocol_loc_ids))
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id,
        subject_ref=expanded.subject_ref, subtype=subtype,
        control_point=cp, plan=expanded.plan,
        applicability=expanded.applicability, window=window,
        enrollment_context=ctx, decisive_ids=decisive,
        unresolved_ids=unresolved, finding_facts=fact_parts,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids)
    marker = ProtocolRiskMarker(
        marker_id=f"marker-{unit_id}", risk_family=expanded.signal_type,
        audience_label=audience, monitoring_priority=priority,
        anchor_kind=window.eval_anchor_kind,
        anchor_start=window.window_start, anchor_end=window.window_end,
        date_precision=window.precision,
        unit_id=unit_id, candidate_or_risk_id=candidate.candidate_id,
        protocol_locator_ids=protocol_loc_ids,
        supporting_locator_ids=tuple(sorted({
            ev.locator.locator_id() for ev in evidence})),
        counterevidence_locator_ids=tuple(sorted({
            loc_id for outcome in outcomes
            for loc_id in (
                ev.locator.locator_id()
                for ev in outcome.counterevidence)})),
        query_ids=(query.query_id,),
        coverage_gap=bool(unresolved))
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, l0_status=l0,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=tuple(src_refs),
        query_refs=(query,), coverage_gap_notices=tuple(notices),
        positive_subtype=subtype, audience_label=audience,
        query_context=ctx.query_context,
        decisive_component_ids=decisive,
        unresolved_component_ids=unresolved,
        component_assessments=assessments,
        journey_markers=(marker,),
        protocol_locator_ids=protocol_loc_ids,
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity,
        evaluation_window_id=window_id,
        control_point_id=cp.control_point_id,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type,
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)


def _l0_for(*, predicate: str, unresolved_ids: Sequence[str]) -> str:
    if predicate == L1Disposition.NOT_EVALUABLE:
        return L0CoverageStatus.NOT_EVALUABLE
    if predicate == L1Disposition.NOT_APPLICABLE:
        return L0CoverageStatus.NOT_APPLICABLE
    if predicate == L1Disposition.BOUNDARY:
        return L0CoverageStatus.PARTIAL
    if unresolved_ids:
        # Determinate L1 with an unresolved component gap: L0 partial,
        # domain completeness blocked (§6.1/§6.2).
        return L0CoverageStatus.PARTIAL
    return L0CoverageStatus.COVERED


def _primary_gap_code(gap_codes: Set[str]) -> str:
    if GAP_SOURCE_ROLE_NOT_COVERED in gap_codes:
        return GAP_SOURCE_ROLE_NOT_COVERED
    if GAP_RULE_NOT_VERIFIED in gap_codes:
        return GAP_RULE_NOT_VERIFIED
    if GAP_EXPRESSION_INCOMPLETE in gap_codes:
        return GAP_EXPRESSION_INCOMPLETE
    if gap_codes:
        return sorted(gap_codes)[0]
    return GAP_SOURCE_ROLE_NOT_COVERED


# ---------------------------------------------------------------------------
# Slice-level evaluation (§11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolSliceResult:
    """Aggregate D04 result for one subject with separate counts."""

    subject_ref: str
    unit_results: Tuple[ProtocolUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""
    delegated_control_points: Tuple[ProtocolDelegatedControlPoint, ...] = ()
    producer_references: Tuple[ProtocolProducerReference, ...] = ()
    expected_units: int = 0

    @property
    def positive_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_APPLICABLE)

    @property
    def coverage_gap_count(self) -> int:
        """Coverage-gap notices counted separately -- never in Query count
        (§11)."""
        return sum(len(r.coverage_gap_notices) for r in self.unit_results)

    @property
    def query_draft_count(self) -> int:
        return sum(len(r.query_refs) for r in self.unit_results)

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def assigned_units(self) -> int:
        return len(self.unit_results)

    def verify_count_invariants(self) -> None:
        """expected_units = positive + negative + boundary + not_applicable
        + not_evaluable; each unit id appears exactly once (§11)."""
        total = (self.positive_count + self.negative_count
                 + self.boundary_count + self.not_applicable_count
                 + self.not_evaluable_count)
        if total != self.expected_units:
            raise ProtocolSliceError(
                f"count equation violated: sum(L1)={total} != "
                f"expected_units={self.expected_units}")
        if len(self.unit_results) != self.expected_units:
            raise ProtocolSliceError(
                "assigned unit results must equal expected_units")
        seen: Set[str] = set()
        for r in self.unit_results:
            if r.unit_id in seen:
                raise ProtocolSliceError(
                    f"duplicate unit id {r.unit_id!r} in slice result")
            seen.add(r.unit_id)


def evaluate_protocol_slice(
    *,
    project_id: str,
    applicability: ProtocolApplicabilityDecision,
    control_points: Sequence[ProtocolControlPoint],
    plan: ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    routing_records: Optional[Sequence[ProtocolControlRoutingRecord]] = None,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]] = None,
    bindings: Sequence[RuleEvidenceBinding] = (),
    coverage_complete_roles: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcomes: Optional[Mapping[str, RetestOutcome]] = None,
    enrollment_context: Optional[EnrollmentContext] = None,
    priority_policy: Optional[D04PriorityPolicy] = None,
    producer_references: Sequence[ProtocolProducerReference] = (),
    snapshot_id: str = "",
) -> ProtocolSliceResult:
    """Evaluate the D04 slice for one subject (§11).

    Expands the expected set (routing first), evaluates every unit, and
    aggregates separate counts: the five L1 buckets, coverage-gap notices
    (never Query count), Query drafts (never risk count), candidates and
    delegated producer-owned control points.
    """
    expansion = expand_protocol_expected_set(
        project_id=project_id, applicability=applicability,
        control_points=control_points, plan=plan,
        components=components, routing_records=routing_records,
        window_by_control_point=window_by_control_point)
    results: List[ProtocolUnitResult] = []
    for expanded in expansion.units:
        results.append(evaluate_protocol_unit(
            project_id=project_id, expanded=expanded,
            bindings=bindings, coverage_complete_roles=coverage_complete_roles,
            exceptions=exceptions, unit_conversion_rules=unit_conversion_rules,
            retest_outcomes=retest_outcomes,
            enrollment_context=enrollment_context,
            priority_policy=priority_policy, snapshot_id=snapshot_id))
    all_cands: List[RiskCandidate] = []
    for r in results:
        all_cands.extend(r.r2_candidates)
    slice_result = ProtocolSliceResult(
        subject_ref=applicability.subject_ref,
        unit_results=tuple(results),
        r2_candidates=tuple(all_cands),
        expected_set_hash=expansion.expected_set_hash,
        rule_lineage=D04_RULE_LINEAGE_DEFAULT,
        delegated_control_points=expansion.delegated_control_points,
        producer_references=tuple(producer_references),
        expected_units=expansion.count)
    slice_result.verify_count_invariants()
    return slice_result
