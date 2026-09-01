"""Protocol risk, query and unit-result projections."""

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
from .protocol_contracts import _ANCHOR_LABELS, _canonical_sorted, _validate_nonempty
from .protocol_applicability import *
from .protocol_evidence import *
from .protocol_evidence import _gap_notice
from .protocol_component_evaluation import *

def _evaluation_window_id(
    *, eval_anchor_kind: str, window_start: str, window_end: str,
    precision: str, endpoint_inclusivity: str,
) -> str:
    """Stable canonical window id (no Run/snapshot/revision).  Two
    disjoint windows under the same anchor kind get different ids and
    therefore different risk identities (challenge 68)."""
    return "d04-window-" + content_hash({
        "eval_anchor_kind": eval_anchor_kind,
        "window_start": window_start,
        "window_end": window_end,
        "precision": precision,
        "endpoint_inclusivity": endpoint_inclusivity,
    })


def _d04_risk_classifier(
    *, subject_ref: str, control_point_id: str, evaluation_node_id: str,
    signal_type: str, eval_anchor_kind: str, evaluation_window_id: str,
) -> str:
    """Classifier/stable-core (frozen §5): never contains protocol version,
    snapshot/revision, mutable free text or Query."""
    return content_hash({
        "subject_ref": subject_ref,
        "control_point_id": control_point_id,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
        "eval_anchor_kind": eval_anchor_kind,
        "evaluation_window_id": evaluation_window_id,
    })


def _d04_risk_scope(
    *, site_ref: str, protocol_id: str, protocol_version: str,
    amendment_id_or_hash: str, cohort: str, phase: str,
    rule_content_hash: str, date_precision: str, mapping_version: str,
    unit_term_policy_version: str,
) -> List[str]:
    """Canonical sorted scope/lineage payload (§5)."""
    parts: Set[str] = {
        f"site:{site_ref}" if site_ref else "site:",
        f"protocol:{protocol_id}/{protocol_version}/{amendment_id_or_hash}",
        f"cohort:{cohort}" if cohort else "cohort:",
        f"phase:{phase}" if phase else "phase:",
        f"rule:{rule_content_hash}",
        f"dp:{date_precision}",
        f"mapping:{mapping_version}",
        f"utp:{unit_term_policy_version}",
        f"ua:{D04_UNIT_ALGO_VERSION}",
    }
    return sorted(parts)


def _build_d04_candidate(
    *, project_id: str, subject_ref: str, site_ref: str,
    control_point: ProtocolControlPoint, evaluation_node_id: str,
    signal_type: str, window: EvaluationWindowSpec,
    plan: ProtocolRuleEvaluationPlan, applicability: ProtocolApplicabilityDecision,
    snapshot_id: str, monitoring_priority: str, positive_subtype: str,
    audience_label: str, match_reason: str,
    decisive_component_ids: Sequence[str] = (),
    unresolved_component_ids: Sequence[str] = (),
    rights_or_safety_critical: bool = False,
    machine_close_forbidden: bool = False,
) -> Tuple[RiskCandidate, RiskIdentity]:
    """Build the D04 R2 candidate (public make_risk_identity only)."""
    window_id = _evaluation_window_id(
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity)
    classifier = _d04_risk_classifier(
        subject_ref=subject_ref,
        control_point_id=control_point.control_point_id,
        evaluation_node_id=evaluation_node_id,
        signal_type=signal_type,
        eval_anchor_kind=window.eval_anchor_kind,
        evaluation_window_id=window_id)
    scope = _d04_risk_scope(
        site_ref=site_ref, protocol_id=applicability.protocol_id,
        protocol_version=applicability.protocol_version,
        amendment_id_or_hash=applicability.amendment_id_or_hash,
        cohort=applicability.cohort, phase=applicability.phase,
        rule_content_hash=plan.rule_content_hash,
        date_precision=window.precision,
        mapping_version=plan.mapping_version,
        unit_term_policy_version=plan.unit_term_policy_version)
    identity = make_risk_identity(
        project_id=project_id, subject_ref=subject_ref,
        domain=D04_DOMAIN, scope=scope, classifier=classifier)
    stable_event_key = (
        f"protocol:{control_point.control_point_id}:{window_id}")
    detail: Dict[str, Any] = {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": classifier,
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": stable_event_key,
        "full_locator_id": control_point.source_locator.locator_id(),
        "risk_family": signal_type,
        "control_point_id": control_point.control_point_id,
        "control_point_type": control_point.control_point_type,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "eval_anchor_kind": window.eval_anchor_kind,
        "evaluation_window_id": window_id,
        "monitoring_priority": monitoring_priority,
        "decisive_component_ids": sorted(set(decisive_component_ids)),
        "unresolved_component_ids": sorted(set(unresolved_component_ids)),
        "match_reason": match_reason,
        "protocol_id": applicability.protocol_id,
        "protocol_version": applicability.protocol_version,
        "amendment_id_or_hash": applicability.amendment_id_or_hash,
        "locator_id": control_point.source_locator.locator_id(),
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
    }
    candidate = RiskCandidate.from_signal(
        project_id=project_id, subject_ref=subject_ref,
        domain=D04_DOMAIN, signal_type=positive_subtype,
        source_snapshot_id=snapshot_id,
        rule_activation_id=(
            plan.rule_content_hash or D04_RULE_LINEAGE_DEFAULT),
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)
    return candidate, identity


# ---------------------------------------------------------------------------
# Query drafts (§8.3) -- three-part Chinese wording, context-conditional
# ---------------------------------------------------------------------------

def _anchor_label(anchor_kind: str) -> str:
    return _ANCHOR_LABELS.get(anchor_kind, anchor_kind)


def _action_suffix(query_context: str) -> str:
    if query_context == QUERY_CONTEXT_NOT_OCCURRED:
        return "请核实入排结果、筛选结论或数据记录，并补充或更正相应记录。"
    if query_context == QUERY_CONTEXT_ENROLLED:
        return ("请核实、说明、补充或更正相应记录；如确认不符合方案，"
                "请评估是否构成方案偏离并按相应流程处理。")
    return ("请先核实是否已随机/入组/接受研究干预及事件时序；"
            "当前资料不足，暂无法确认是否符合方案。")


def _build_query_ref(
    *, query_id: str, unit_id: str, subject_ref: str,
    subtype: str, control_point: ProtocolControlPoint,
    plan: ProtocolRuleEvaluationPlan, applicability: ProtocolApplicabilityDecision,
    window: EvaluationWindowSpec, enrollment_context: EnrollmentContext,
    decisive_ids: Sequence[str], unresolved_ids: Sequence[str],
    finding_facts: Sequence[str],
    candidate_id: str, source_locator_ids: Sequence[str],
) -> QueryDraftRef:
    basis = (
        f"依据：方案 {plan.protocol_id} {applicability.protocol_version}"
        f"（修订 {applicability.amendment_id_or_hash or '无'}）"
        f"{control_point.official_section_id} "
        f"{control_point.official_criterion_id}（{control_point.official_heading}）"
        f"；适用时点 {_anchor_label(window.eval_anchor_kind)}。")
    if finding_facts:
        facts = "；".join(finding_facts)
    else:
        facts = "当前支持依据与排除依据均需进一步核实"
    decisive_txt = "、".join(sorted(set(decisive_ids))) if decisive_ids else ""
    unresolved_txt = (
        "、".join(sorted(set(unresolved_ids))) if unresolved_ids else "")
    scope_txt = ""
    if decisive_txt:
        scope_txt += f"决定性子条件：{decisive_txt}。"
    if unresolved_txt:
        scope_txt += f"未决子条件：{unresolved_txt}（资料不足，完整性受阻）。"
    finding = (
        f"发现：参与者 {subject_ref} {facts}。{scope_txt}"
        f"支持依据定位 {', '.join(sorted(source_locator_ids))}。")
    action = f"行动项：{_action_suffix(enrollment_context.query_context)}"
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=basis, finding=finding, action=action,
        source_locator_ids=tuple(_canonical_sorted(source_locator_ids)),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# ProtocolUnitResult (§2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolUnitResult:
    """The evaluation outcome for one D04 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol and can
    materialize a full ``UnitEvaluation`` for the CoverageLedger.
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    monitoring_priority: str
    l0_status: str = L0CoverageStatus.COVERED
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    not_evaluable_reason: str = ""
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    coverage_gap_notices: Tuple[ProtocolCoverageGapNotice, ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""
    query_context: str = ""
    decisive_component_ids: Tuple[str, ...] = ()
    unresolved_component_ids: Tuple[str, ...] = ()
    component_assessments: Tuple[ProtocolComponentAssessment, ...] = ()
    journey_markers: Tuple[ProtocolRiskMarker, ...] = ()
    protocol_locator_ids: Tuple[str, ...] = ()
    eval_anchor_kind: str = ""
    window_start: str = ""
    window_end: str = ""
    precision: str = ""
    endpoint_inclusivity: str = ""
    evaluation_window_id: str = ""
    control_point_id: str = ""
    evaluation_node_id: str = ""
    signal_type: str = ""
    protocol_version: str = ""
    amendment_id_or_hash: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise ProtocolSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        if self.l0_status not in L0CoverageStatus.ALL_STATUSES:
            raise ProtocolSliceError(
                f"l0_status={self.l0_status!r} invalid")
        if self.query_context and self.query_context not in QUERY_CONTEXTS:
            raise ProtocolSliceError(
                f"query_context={self.query_context!r} invalid")
        object.__setattr__(self, "r2_candidates",
                           tuple(self.r2_candidates))
        object.__setattr__(self, "risk_candidate_refs",
                           tuple(self.risk_candidate_refs))
        object.__setattr__(self, "risk_instance_refs",
                           tuple(self.risk_instance_refs))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "source_record_refs",
                           tuple(self.source_record_refs))
        object.__setattr__(self, "query_refs", tuple(self.query_refs))
        object.__setattr__(self, "coverage_gap_notices",
                           tuple(self.coverage_gap_notices))
        object.__setattr__(self, "component_assessments",
                           tuple(self.component_assessments))
        object.__setattr__(self, "journey_markers",
                           tuple(self.journey_markers))
        object.__setattr__(self, "protocol_locator_ids",
                           _canonical_sorted(self.protocol_locator_ids))
        object.__setattr__(self, "decisive_component_ids",
                           _canonical_sorted(self.decisive_component_ids))
        object.__setattr__(self, "unresolved_component_ids",
                           _canonical_sorted(self.unresolved_component_ids))

    def all_source_locator_ids(self) -> Tuple[str, ...]:
        ids: List[str] = []
        for ref in self.source_record_refs:
            ids.append(ref.locator.locator_id())
        for item in self.evidence:
            ids.append(item.locator.locator_id())
        for ref in self.risk_candidate_refs:
            if ref.locator is not None:
                ids.append(ref.locator.locator_id())
        return tuple(sorted(set(ids)))

    def to_unit_evaluation(
        self, *, provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity not in polarities:
                polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=self.l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(sorted(polarities)),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Unit-level evaluation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolComponentAssessment:
    """One component's issue predicate plus gaps and counterevidence."""

    assessment_id: str
    unit_id: str
    component_id: str
    official_criterion_id: str
    issue_predicate_result: str
    evidence: Tuple[EvidenceItem, ...] = ()
    counterevidence: Tuple[EvidenceItem, ...] = ()
    gaps: Tuple[str, ...] = ()
    gap_reason_codes: Tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(
            self.assessment_id, "ProtocolComponentAssessment.assessment_id"
        )
        _validate_nonempty(self.unit_id, "ProtocolComponentAssessment.unit_id")
        _validate_nonempty(
            self.component_id, "ProtocolComponentAssessment.component_id"
        )
        if self.issue_predicate_result not in ISSUE_RESULTS:
            raise ProtocolSliceError(
                f"issue_predicate_result={self.issue_predicate_result!r} invalid"
            )
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "counterevidence", tuple(self.counterevidence))
        object.__setattr__(self, "gaps", tuple(self.gaps))
        object.__setattr__(self, "gap_reason_codes", tuple(self.gap_reason_codes))
        if self.assessment_id.startswith(("unit-", "d04-eset-")):
            raise ProtocolSliceError(
                "component assessment id must never disguise as a unit id"
            )

def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _component_assessment(
    *, unit_id: str, component: ProtocolComponent,
    predicate: str, outcome: ComponentConditionOutcome,
    rule_lineage: str,
) -> ProtocolComponentAssessment:
    assessment_id = "d04-ca-" + content_hash({
        "unit_id": unit_id,
        "component_id": component.component_id,
        "issue_predicate_result": predicate,
        "gaps": list(_canonical_sorted(outcome.gap_codes)),
        "evidence_ids": sorted(
            ev.evidence_id
            for ev in outcome.supporting + outcome.counterevidence
            + outcome.context),
    })
    return ProtocolComponentAssessment(
        assessment_id=assessment_id, unit_id=unit_id,
        component_id=component.component_id,
        official_criterion_id=component.official_criterion_id,
        issue_predicate_result=predicate,
        evidence=outcome.supporting + outcome.context,
        counterevidence=outcome.counterevidence,
        gaps=outcome.gaps,
        gap_reason_codes=outcome.gap_codes,
        rationale=outcome.reason)


def _evaluate_gate_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded,
) -> ProtocolUnitResult:
    """Applicability/routing gate evaluation (§5).

    Gates are subject-level blocking units: they carry no R2 risk
    identity (the frozen classifier covers only atomic|package nodes),
    no candidate and no Query.  ``multi_feasible_boundary`` -> boundary;
    ``not_evaluable`` / routing gaps -> not_evaluable with a coverage-gap
    notice.  Affected control point ids stay in the decision context and
    never pollute the L1 denominator (challenges 60/67/71).
    """
    unit = expanded.build_unit(project_id)
    unit_id = unit.unit_id
    protocol_loc = tuple(
        sorted({loc.locator_id()
                for loc in expanded.applicability.source_locators}))
    if expanded.evaluation_node_id == NODE_ROUTING_GATE:
        reason = expanded.not_evaluable_reason_hint or (
            "控制点归属路由无法唯一确定，禁止在多个域各建风险")
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_ROUTING_UNRESOLVED,
            protocol_locator_ids=protocol_loc,
            reachable_source_locator_ids=protocol_loc)
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=reason,
            coverage_gap_notices=(notice,),
            protocol_locator_ids=protocol_loc,
            evaluation_node_id=NODE_ROUTING_GATE,
            signal_type=SIGNAL_PROTOCOL_ROUTING,
            control_point_id=(
                expanded.control_point.control_point_id
                if expanded.control_point is not None
                else "protocol_routing"),
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)
    # applicability gate
    if expanded.applicability.decision_status == (
            APPLICABILITY_MULTI_FEASIBLE_BOUNDARY):
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.BOUNDARY,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.PARTIAL,
            boundary_reason=expanded.not_evaluable_reason_hint or (
                "多个可行方案版本均有依据，适用性存在边界"),
            protocol_locator_ids=protocol_loc,
            eval_anchor_kind=ANCHOR_OTHER,
            precision=PRECISION_UNKNOWN,
            endpoint_inclusivity=INCLUSIVITY_GATE,
            evaluation_node_id=NODE_APPLICABILITY_GATE,
            signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
            control_point_id="protocol_applicability",
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)
    reason = expanded.not_evaluable_reason_hint or (
        "批准/启用/过渡条款/重新知情/事件关键日期缺失或冲突，"
        "无法确定适用方案版本")
    notice = _gap_notice(
        unit_id=unit_id, reason_code=GAP_APPLICABILITY_UNDETERMINED,
        protocol_locator_ids=protocol_loc,
        reachable_source_locator_ids=protocol_loc)
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        l0_status=L0CoverageStatus.NOT_EVALUABLE,
        not_evaluable_reason=reason,
        coverage_gap_notices=(notice,),
        protocol_locator_ids=protocol_loc,
        eval_anchor_kind=ANCHOR_OTHER,
        precision=PRECISION_UNKNOWN,
        endpoint_inclusivity=INCLUSIVITY_GATE,
        evaluation_node_id=NODE_APPLICABILITY_GATE,
        signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
        control_point_id="protocol_applicability",
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)
