"""Unit and slice orchestration for the AE/MH risk domain."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from ..domain.risk import RiskCandidate
from .aemh_matching import (
    _ReportedMatchOutcome, _assess_counterevidence, _build_journey_marker,
    _match_evidence_to_reported, _query_action_text,
    _query_basis_text, _query_finding_text,
)
from .aemh_results import (
    AEMHSliceError, AEMHSliceResult, AEMHUnitResult, _build_r2_candidate,
    _concept, _make_evidence_item, _make_source_record_ref,
)
from .aemh_temporal import (
    ProtocolAnchorDates, _resolve_protocol_anchors,
    classify_event_against_boundary,
)
from .aemh_types import (
    EventMatchStrategy, MedicalGrading, ProtocolAEMHBoundary, SemanticRecord,
    SemanticRecordSet, derive_monitoring_priority,
)
from .contracts import (
    EvaluationUnit, EvidenceItem, L1Disposition, L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM, MONITORING_PRIORITY_UNKNOWN, QueryDraftRef,
    RiskCandidateRef, RiskInstanceRef, SourceRecordRef,
)

# ---------------------------------------------------------------------------

def evaluate_aemh_unit(
    unit: EvaluationUnit,
    record_set: SemanticRecordSet,
    protocol_boundary: ProtocolAEMHBoundary,
    match_strategy: EventMatchStrategy,
    *,
    project_id: str,
    rule_lineage: str,
    run_id: str = "",
    snapshot_id: str = "",
    unit_algorithm_version: str = "",
    existing_risk_instances: Sequence[RiskInstanceRef] = (),
) -> AEMHUnitResult:
    """Evaluate one D01 AE/MH :class:`EvaluationUnit`.

    Produces one L1 disposition with source-linked evidence, candidates,
    Query refs and journey markers.  The function never establishes or
    closes R2 lifecycle; it produces R2 :class:`RiskCandidate` values for
    worker_03 / ``RiskLifecycle`` to register.
    """
    # -- Validate required inputs -------------------------------------------
    if not isinstance(unit, EvaluationUnit):
        raise AEMHSliceError("unit must be an EvaluationUnit")
    if not isinstance(record_set, SemanticRecordSet):
        raise AEMHSliceError("record_set must be a SemanticRecordSet")
    if not isinstance(protocol_boundary, ProtocolAEMHBoundary):
        raise AEMHSliceError(
            "protocol_boundary must be a ProtocolAEMHBoundary")
    if not isinstance(match_strategy, EventMatchStrategy):
        raise AEMHSliceError("match_strategy must be an EventMatchStrategy")

    unit_id = unit.unit_id
    subject_ref = record_set.subject_ref

    # -- Finding 1: Check all five required roles are satisfied -------------
    missing_roles = record_set.missing_required_roles()
    if missing_roles:
        missing_str = "、".join(missing_roles)
        return AEMHUnitResult(
            unit_id=unit_id,
            subject_ref=subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            medical_grading=MedicalGrading(),
            not_evaluable_reason=(
                f"必需语义角色缺失或未覆盖：{missing_str}，"
                f"无法完成 AE/MH 评价"),
        )

    # -- Finding 3: versioned explicit non-applicability --------------------
    if not protocol_boundary.applicable:
        return AEMHUnitResult(
            unit_id=unit_id,
            subject_ref=subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            medical_grading=MedicalGrading(),
        )

    # -- Finding 2: Resolve protocol anchors --------------------------------
    anchors = _resolve_protocol_anchors(record_set, protocol_boundary)

    evidence_records = record_set.evidence_records
    reported = record_set.reported_source_records

    # -- Collect evidence items and source-record refs ----------------------
    evidence_items: List[EvidenceItem] = []
    source_refs: List[SourceRecordRef] = []
    candidate_refs: List[RiskCandidateRef] = []
    query_refs: List[QueryDraftRef] = []
    journey_markers: List[Dict[str, Any]] = []
    r2_candidates: List[RiskCandidate] = []
    candidate_locator_ids: Set[str] = set()
    boundary_support_locator_ids: Set[str] = set()
    boundary_event_reasons: List[str] = []

    # Reported AE/MH become source-record refs + context evidence.
    for idx, rep in enumerate(reported):
        source_refs.append(_make_source_record_ref(rep))
        norm = rep.normalized_date()
        uncertainty = norm.uncertainty if norm else ""
        grading = MedicalGrading(
            intensity=rep.intensity,
            intensity_scale=rep.intensity_scale,
            seriousness_criteria=rep.seriousness_criteria,
            monitoring_priority=derive_monitoring_priority(
                rep.intensity, rep.seriousness_criteria))
        journey_markers.append(
            _build_journey_marker(rep, grading, unit_id, uncertainty))
        evidence_items.append(_make_evidence_item(
            evidence_id=f"ev-rep-{unit_id[:16]}-{idx}",
            polarity=L1bEvidencePolarity.CONTEXT,
            record=rep,
            rule_lineage=rule_lineage,
            uncertainty_note=uncertainty,
        ))

    # -- Scan evidence records for under-reporting clues --------------------
    unmatched_evidence: List[Tuple[SemanticRecord, _ReportedMatchOutcome]] = []
    matched_evidence: List[Tuple[SemanticRecord, SemanticRecord]] = []

    for ev in evidence_records:
        # Protocol exclusion check (concept explicitly excluded from AE).
        if protocol_boundary.is_excluded_concept(_concept(ev)):
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-exc-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.CONTEXT,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note="protocol-excluded concept",
            ))
            grading = MedicalGrading(
                intensity=ev.intensity,
                intensity_scale=ev.intensity_scale,
                seriousness_criteria=ev.seriousness_criteria,
                monitoring_priority=derive_monitoring_priority(
                    ev.intensity, ev.seriousness_criteria))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, "protocol-excluded"))
            continue

        # Finding 2: classify event against the protocol boundary.
        ev_norm = ev.normalized_date()
        boundary_cls = classify_event_against_boundary(ev_norm, anchors)
        if boundary_cls.classification == "not_evaluable":
            return AEMHUnitResult(
                unit_id=unit_id,
                subject_ref=subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                medical_grading=MedicalGrading(),
                evidence=tuple(evidence_items),
                source_record_refs=tuple(source_refs),
                journey_markers=tuple(journey_markers),
                not_evaluable_reason=boundary_cls.reason,
            )

        # Events outside the reporting window at sufficient precision are
        # not AE/MH under-reporting clues; they become context evidence.
        if boundary_cls.classification == "outside":
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-out-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.CONTEXT,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note="事件在方案报告窗口外",
            ))
            grading = MedicalGrading(
                intensity=ev.intensity,
                intensity_scale=ev.intensity_scale,
                seriousness_criteria=ev.seriousness_criteria,
                monitoring_priority=derive_monitoring_priority(
                    ev.intensity, ev.seriousness_criteria))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, "事件在方案报告窗口外"))
            continue

        is_boundary_event = boundary_cls.classification == "boundary"
        if is_boundary_event:
            boundary_support_locator_ids.add(ev.locator.locator_id())
            if boundary_cls.reason:
                boundary_event_reasons.append(boundary_cls.reason)

        match_outcome = _match_evidence_to_reported(
            ev, reported, match_strategy, protocol_boundary)

        grading = MedicalGrading(
            intensity=ev.intensity,
            intensity_scale=ev.intensity_scale,
            seriousness_criteria=ev.seriousness_criteria,
            monitoring_priority=derive_monitoring_priority(
                ev.intensity, ev.seriousness_criteria))

        if match_outcome.matched and match_outcome.matched_record is not None:
            matched_evidence.append((ev, match_outcome.matched_record))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-mat-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=is_boundary_event))
            continue

        # Finding 6: NCS / alternative-diagnosis counterevidence.
        ce_assessment = _assess_counterevidence(ev, grading)
        if ce_assessment.is_combination_counterevidence:
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-ce-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=ce_assessment.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, ce_assessment.reason,
                    is_boundary_support=is_boundary_event))
            continue

        if match_outcome.not_evaluable:
            unmatched_evidence.append((ev, match_outcome))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-ne-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.SUPPORTING,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=is_boundary_event))
            continue

        if match_outcome.boundary:
            unmatched_evidence.append((ev, match_outcome))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-bnd-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.SUPPORTING,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=True))
            continue

        # No match found: this is a potential under-reporting clue.
        # Finding 4 + identity integration: build the real R2
        # RiskCandidate once with its public R2 RiskIdentity.
        r2_cand, r2_identity = _build_r2_candidate(
            project_id=project_id,
            subject_ref=subject_ref,
            record=ev,
            grading=grading,
            match_reason=match_outcome.reason,
            snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            unit=unit,
        )
        r2_candidates.append(r2_cand)
        cand_ref = RiskCandidateRef(
            candidate_id=r2_cand.candidate_id,
            risk_identity_id=r2_identity.risk_identity_id,
            locator=ev.locator,
        )
        candidate_refs.append(cand_ref)
        candidate_locator_ids.add(ev.locator.locator_id())
        evidence_items.append(_make_evidence_item(
            evidence_id=f"ev-clue-{unit_id[:16]}-{ev.locator.record_id}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            record=ev,
            rule_lineage=rule_lineage,
            uncertainty_note="no matching reported AE/MH found",
        ))
        journey_markers.append(
            _build_journey_marker(
                ev, grading, unit_id, "potential under-reporting clue",
                is_candidate=True,
                is_boundary_support=is_boundary_event))
        unmatched_evidence.append((ev, match_outcome))

    # -- Determine L1 disposition -------------------------------------------
    l1_disposition, boundary_reason, ne_reason = _determine_l1_disposition(
        unmatched_evidence=unmatched_evidence,
        matched_evidence=matched_evidence,
        candidate_refs=candidate_refs,
        reported=reported,
        evidence_records=evidence_records,
        protocol_boundary=protocol_boundary,
        anchors=anchors,
        record_set=record_set,
        boundary_support_locator_ids=boundary_support_locator_ids,
        boundary_event_reasons=boundary_event_reasons,
    )

    # Finding 9: Build Query drafts with audience-readable basis and
    # minimal locator sets.
    if l1_disposition in (L1Disposition.POSITIVE, L1Disposition.BOUNDARY):
        basis_text = _query_basis_text(protocol_boundary, match_strategy)
        for cand_ref in candidate_refs:
            # Minimal locator set: candidate locator + its supporting
            # evidence locator only.
            ev_for_cand = [
                item for item in evidence_items
                if item.locator.locator_id() == cand_ref.locator.locator_id()]
            minimal_locators: Set[str] = {cand_ref.locator.locator_id()}
            for item in ev_for_cand:
                minimal_locators.add(item.locator.locator_id())
            # Find concept by matching locator in record_set.
            ev_concept = "医学事件"
            for rec in record_set.records:
                if rec.locator.locator_id() == cand_ref.locator.locator_id():
                    ev_concept = _concept(rec)
                    break
            query_refs.append(QueryDraftRef(
                query_id=f"qry-{cand_ref.candidate_id[:28]}",
                unit_id=unit_id,
                basis=basis_text,
                finding=_query_finding_text(subject_ref, ev_concept),
                action=_query_action_text(),
                source_locator_ids=tuple(sorted(minimal_locators)),
                linked_candidate_id=cand_ref.candidate_id,
            ))

    # -- Compute aggregate grading ------------------------------------------
    all_grading_signals = (
        [(r.intensity, r.seriousness_criteria) for r in reported]
        + [(r.intensity, r.seriousness_criteria) for r in evidence_records])
    best_intensity = ""
    all_seriousness: Tuple[str, ...] = ()
    best_priority = MONITORING_PRIORITY_UNKNOWN
    for intensity, seriousness in all_grading_signals:
        if seriousness:
            all_seriousness = all_seriousness + tuple(seriousness)
        pri = derive_monitoring_priority(intensity, seriousness)
        if pri == MONITORING_PRIORITY_HIGH:
            best_priority = MONITORING_PRIORITY_HIGH
        elif (pri == MONITORING_PRIORITY_MEDIUM
              and best_priority != MONITORING_PRIORITY_HIGH):
            best_priority = MONITORING_PRIORITY_MEDIUM
        elif (pri == MONITORING_PRIORITY_LOW
              and best_priority not in (
                  MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_MEDIUM)):
            best_priority = MONITORING_PRIORITY_LOW
        if intensity and not best_intensity:
            best_intensity = intensity

    aggregate_grading = MedicalGrading(
        intensity=best_intensity,
        seriousness_criteria=all_seriousness,
        monitoring_priority=best_priority,
    )

    return AEMHUnitResult(
        unit_id=unit_id,
        subject_ref=subject_ref,
        l1_disposition=l1_disposition,
        medical_grading=aggregate_grading,
        evidence=tuple(evidence_items),
        source_record_refs=tuple(source_refs),
        risk_candidate_refs=tuple(candidate_refs),
        risk_instance_refs=tuple(existing_risk_instances),
        query_refs=tuple(query_refs),
        journey_markers=tuple(journey_markers),
        r2_candidates=tuple(r2_candidates),
        not_evaluable_reason=ne_reason,
        boundary_reason=boundary_reason,
    )

def _determine_l1_disposition(
    *,
    unmatched_evidence: Sequence[Tuple[SemanticRecord, _ReportedMatchOutcome]],
    matched_evidence: Sequence[Tuple[SemanticRecord, SemanticRecord]],
    candidate_refs: Sequence[RiskCandidateRef],
    reported: Sequence[SemanticRecord],
    evidence_records: Sequence[SemanticRecord],
    protocol_boundary: ProtocolAEMHBoundary,
    anchors: ProtocolAnchorDates,
    record_set: SemanticRecordSet,
    boundary_support_locator_ids: Set[str],
    boundary_event_reasons: Sequence[str],
) -> Tuple[str, str, str]:
    """Determine the L1 disposition and return (disposition, boundary_reason,
    not_evaluable_reason)."""
    # (has_subject / has_temporal / required-role checks are handled earlier
    # in evaluate_aemh_unit, before this function is called.)

    # Check for not_evaluable date conflicts.
    has_ne = any(
        outcome.not_evaluable for _, outcome in unmatched_evidence)
    if has_ne:
        reasons = [
            outcome.reason for _, outcome in unmatched_evidence
            if outcome.not_evaluable]
        return (
            L1Disposition.NOT_EVALUABLE, "",
            "；".join(reasons))

    # Check for boundary date conflicts from match outcomes.
    has_match_boundary = any(
        outcome.boundary for _, outcome in unmatched_evidence)

    # F1: Check if any candidate was created from a boundary-classified
    # event.  If so, the unit disposition must be BOUNDARY, not POSITIVE.
    has_boundary_event_candidate = any(
        cand.locator is not None
        and cand.locator.locator_id() in boundary_support_locator_ids
        for cand in candidate_refs)

    # If there are unmatched clues (candidates), the unit is positive or
    # boundary.
    if candidate_refs:
        if has_match_boundary or has_boundary_event_candidate:
            specific_reasons = list(dict.fromkeys(
                list(boundary_event_reasons) + [
                    outcome.reason for _, outcome in unmatched_evidence
                    if outcome.boundary and outcome.reason
                ]
            ))
            return (
                L1Disposition.BOUNDARY,
                "；".join(specific_reasons) if specific_reasons else (
                    "存在疑似 AE/MH 漏报线索，同时部分日期精度不足以确定"
                    "是否在方案报告窗口内或与已记录事件匹配"
                ),
                "")
        return (L1Disposition.POSITIVE, "", "")

    # No unmatched clues. Check if all evidence was matched or excluded.
    if has_match_boundary or has_boundary_event_candidate:
        boundary_reasons = [
            outcome.reason for _, outcome in unmatched_evidence
            if outcome.boundary]
        return (
            L1Disposition.BOUNDARY,
            "；".join(boundary_reasons) if boundary_reasons
            else "部分日期跨界，尚不能确定匹配关系",
            "")

    # All evidence matched or no evidence records.
    if evidence_records and not unmatched_evidence:
        # All evidence matched to reported records.
        return (L1Disposition.NEGATIVE, "", "")

    if not evidence_records and reported:
        # No evidence roles, only reported records -- the unit evaluated
        # the reported records and found nothing to flag.
        return (L1Disposition.NEGATIVE, "", "")

    if not evidence_records and not reported:
        # No records at all for this unit.  This is not_evaluable unless
        # the protocol proves the unit is out of scope.
        return (
            L1Disposition.NOT_EVALUABLE, "",
            "该评价单元无 AE/MH 记录且无证据记录，无法完成评价")

    # Default: negative (all evidence matched or explained).
    return (L1Disposition.NEGATIVE, "", "")


# ---------------------------------------------------------------------------
# Slice-level evaluation
# ---------------------------------------------------------------------------

def evaluate_aemh_slice(
    units: Sequence[EvaluationUnit],
    record_sets: Mapping[str, SemanticRecordSet],
    protocol_boundary: ProtocolAEMHBoundary,
    match_strategy: EventMatchStrategy,
    *,
    project_id: str,
    rule_lineage: str,
    run_id: str = "",
    snapshot_id: str = "",
    unit_algorithm_version: str = "",
) -> Dict[str, AEMHSliceResult]:
    """Evaluate multiple D01 units, one per subject.

    Returns a mapping of ``subject_ref -> AEMHSliceResult``.  Each unit is
    evaluated independently; the function does not merge or split risk
    identities (that is worker_03 / R2 lifecycle territory).
    """
    if not isinstance(protocol_boundary, ProtocolAEMHBoundary):
        raise AEMHSliceError(
            "protocol_boundary must be a ProtocolAEMHBoundary")
    if not isinstance(match_strategy, EventMatchStrategy):
        raise AEMHSliceError("match_strategy must be an EventMatchStrategy")

    results: Dict[str, AEMHSliceResult] = {}
    for unit in units:
        scope_key = unit.scope_key
        record_set = record_sets.get(scope_key)
        if record_set is None:
            # No records for this subject -- still produce a result.
            record_set = SemanticRecordSet(
                records=(),
                subject_ref=scope_key,
                scope_key=scope_key,
            )
        unit_result = evaluate_aemh_unit(
            unit=unit,
            record_set=record_set,
            protocol_boundary=protocol_boundary,
            match_strategy=match_strategy,
            project_id=project_id,
            rule_lineage=rule_lineage,
            run_id=run_id,
            snapshot_id=snapshot_id,
            unit_algorithm_version=unit_algorithm_version,
        )
        existing_results = results.get(unit_result.subject_ref)
        unit_results: Tuple[AEMHUnitResult, ...]
        r2_candidates: Tuple[RiskCandidate, ...]
        if existing_results is not None:
            unit_results = existing_results.unit_results + (unit_result,)
            # Finding 4: aggregate all R2 candidates from each unit result.
            r2_candidates = (
                existing_results.r2_candidates + unit_result.r2_candidates)
        else:
            unit_results = (unit_result,)
            r2_candidates = unit_result.r2_candidates
        results[unit_result.subject_ref] = AEMHSliceResult(
            subject_ref=unit_result.subject_ref,
            unit_results=unit_results,
            r2_candidates=r2_candidates,
            protocol_boundary=protocol_boundary,
            match_strategy=match_strategy,
            rule_lineage=rule_lineage,
        )
    return results
