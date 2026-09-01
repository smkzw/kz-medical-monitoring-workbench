"""IP unit and slice orchestration."""

from __future__ import annotations

from .ip_types import *
from .ip_types import (
    _prec_rank,
    _nv_precision,
    _to_day,
    _day_range,
)
from .ip_resolution import *
from .ip_resolution import (
    _WindowOverlap,
    _compare_windows,
    _episode_window,
    _rule_window,
    _algorithm_window,
)
from .ip_results import *
from .ip_results import (
    _d03_risk_classifier,
    _d03_risk_scope,
    _build_d03_risk_identity,
    _d03_identity_detail,
    _build_d03_candidate,
    _expected_set_hash,
    _control_token_for,
    _make_evidence_item,
    _dedup_locator_ids,
    _make_source_record_ref,
    _canonical_text,
    _canonical_dose,
    _canonical_record_value,
    _journey_marker,
    _display_label,
    _query_text,
    _build_query_ref,
    _build_positive_result,
    _build_boundary_result,
    _not_evaluable_result,
    _negative_result,
)
from .ip_evaluation import *
from .ip_evaluation import (
    _required_roles_for,
    _audience_suffix_for,
    _binding_gate_result,
    _evaluate_role_phase_unit,
    _rule_phase_applicability,
    _evaluate_plan_actual_unit,
    _field_label,
    _occurrence_days_in_rule_window,
    _RatioOutcome,
    _round_ratio,
    _threshold_fraction,
    _check_ratio_against_thresholds,
    _window_day_count,
    _days_in_window,
    _planned_pause_day_count,
    _observation_for,
    _convert_unit,
    _evaluate_adherence_unit,
)
from .ip_actions import *
from .ip_actions import (
    _evaluate_allowed_action_unit,
    _evaluate_medical_action_unit,
    _amount_decimal,
    _record_totals,
    _evaluate_accountability_unit,
)

# ---------------------------------------------------------------------------
# Core evaluation: evaluate_ip_unit
# ---------------------------------------------------------------------------

def evaluate_ip_unit(
    *, project_id: str, expanded: IPUnitExpanded,
    occurrences: Sequence[ExposureOccurrence] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
    cm_conflict_rows: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    aggregation_policy: Optional[ExposureAggregationPolicy] = None,
    action_coverage_complete: bool = False,
    trigger_coverage_complete: bool = False,
    protocol_return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Optional[D03PriorityPolicy] = None,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = "",
) -> IPUnitResult:
    """Evaluate one D03 expanded unit (frozen D03 §5).

    Coverage gates are explicit and fail closed: ``role_coverage`` proves
    the semantic roles this unit kind requires; ``action_coverage_complete``
    proves all actual-action rows were read; ``trigger_coverage_complete``
    proves the medical-trigger sources were read; ``protocol_return_
    expectation`` drives the §5.4 return decision table.  An empty record
    sequence alone never proves a complete search.
    """
    if not isinstance(expanded, IPUnitExpanded):
        raise IPSliceError("expanded must be an IPUnitExpanded")
    episode = expanded.episode
    coverage: Mapping[str, bool] = (
        role_coverage if role_coverage is not None else {})
    if binding_mapping is None:
        binding_mapping = expanded.binding_mapping
    unit = expanded.build_unit(project_id, binding_mapping)
    unit_id = unit.unit_id

    # -- CM/IP mutual exclusion (frozen D03 §3.1) --------------------------
    for cm_row in cm_conflict_rows:
        if cm_row.locator.record_id == episode.source_locator.record_id:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="同一来源行同时映射为 CM 与 IP，角色互斥冲突",
                rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    # -- Required semantic-role coverage gate (§3.1) -----------------------
    gap = _required_roles_for(expanded, coverage)
    if gap is not None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=gap,
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    # -- Role/phase confirmation gate (§4) ---------------------------------
    if not episode.role_confirmed or not episode.actual_treatment_role.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少已确认的治疗角色，不得合并角色/阶段建立单元结论",
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)
    if expanded.resolution.is_bound and expanded.assignment is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="episode 已绑定但缺少 assignment 对象，无法评价",
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    rule_lineage = (expanded.rule.rule_lineage if expanded.rule is not None
                    else D03_RULE_LINEAGE_DEFAULT)

    if (expanded.control_item in (CONTROL_PLAN_ACTUAL,
                                  CONTROL_ALLOWED_ACTION,
                                  CONTROL_MEDICAL_ACTION)
            and expanded.rule is None):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少适用的方案规则，当前无法评价",
            rule_lineage=rule_lineage)
    if (expanded.control_item in (CONTROL_ADHERENCE, CONTROL_ACCOUNTABILITY)
            and expanded.algorithm is None):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少适用的依从性算法，当前无法评价",
            rule_lineage=rule_lineage)

    if expanded.control_item == CONTROL_ROLE_PHASE:
        return _evaluate_role_phase_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_PLAN_ACTUAL:
        return _evaluate_plan_actual_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            occurrences=occurrences,
            aggregation_policy=aggregation_policy,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ADHERENCE:
        return _evaluate_adherence_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            occurrences=occurrences,
            aggregation_policy=aggregation_policy,
            observations=observations,
            planned_actions=planned_actions,
            action_coverage_complete=action_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ALLOWED_ACTION:
        return _evaluate_allowed_action_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            planned_actions=planned_actions,
            actual_actions=actual_actions,
            action_coverage_complete=action_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_MEDICAL_ACTION:
        return _evaluate_medical_action_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            action_evidence=action_evidence,
            trigger_coverage_complete=trigger_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ACCOUNTABILITY:
        return _evaluate_accountability_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            return_records=return_records,
            dispense_records=dispense_records,
            observations=observations,
            protocol_return_expectation=protocol_return_expectation,
            priority_policy=priority_policy)

    return _not_evaluable_result(
        unit_id=unit_id, episode=episode,
        reason=f"未识别的控制项 {expanded.control_item!r}，当前无法评价",
        rule_lineage=rule_lineage)


# ---------------------------------------------------------------------------
# Slice-level evaluation (frozen D03 §4, §10)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPEpisodeRollup:
    """Read-only episode rollup preserving all child unit ids and flags."""

    episode_key: str
    subject_ref: str
    child_unit_ids: Tuple[str, ...]
    has_positive: bool
    has_boundary: bool
    has_not_evaluable: bool
    has_negative: bool
    source_record_count: int


@dataclass(frozen=True)
class IPSliceResult:
    """Aggregate result of evaluating one or more D03 units for a subject."""

    subject_ref: str
    unit_results: Tuple[IPUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

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

    def episode_rollups(
        self, expansions: IPExpectedSetExpansion,
    ) -> Tuple[IPEpisodeRollup, ...]:
        """Build read-only episode rollups preserving all child unit ids."""
        unit_by_expanded: Dict[str, IPUnitResult] = {
            r.unit_id: r for r in self.unit_results}
        rollups: List[IPEpisodeRollup] = []
        by_episode: Dict[str, List[IPUnitExpanded]] = {}
        for eu in expansions.units:
            by_episode.setdefault(eu.episode.episode_key, []).append(eu)
        for ep_key, eus in by_episode.items():
            child_ids: List[str] = []
            has_pos = has_bnd = has_ne = has_neg = False
            src_loc_ids: Set[str] = set()
            for eu in eus:
                unit = eu.build_unit(expansions.project_id)
                uid = unit.unit_id
                child_ids.append(uid)
                r = unit_by_expanded.get(uid)
                if r is None:
                    continue
                if r.l1_disposition == L1Disposition.POSITIVE:
                    has_pos = True
                elif r.l1_disposition == L1Disposition.BOUNDARY:
                    has_bnd = True
                elif r.l1_disposition == L1Disposition.NOT_EVALUABLE:
                    has_ne = True
                elif r.l1_disposition == L1Disposition.NEGATIVE:
                    has_neg = True
                for sref in r.source_record_refs:
                    src_loc_ids.add(sref.locator.locator_id())
            rollups.append(IPEpisodeRollup(
                episode_key=ep_key,
                subject_ref=eus[0].episode.subject_ref,
                child_unit_ids=tuple(sorted(set(child_ids))),
                has_positive=has_pos, has_boundary=has_bnd,
                has_not_evaluable=has_ne, has_negative=has_neg,
                source_record_count=len(src_loc_ids)))
        return tuple(rollups)


def evaluate_ip_slice(
    *, project_id: str, episodes: Sequence[IPExposureEpisode],
    assignments: Sequence[PlannedTreatmentAssignment] = (),
    active_rules: Sequence[ProtocolExposureRule] = (),
    adherence_algorithms: Sequence[AdherenceAlgorithm] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    occurrences: Sequence[ExposureOccurrence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
    cm_conflict_rows: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    aggregation_policy: Optional[ExposureAggregationPolicy] = None,
    action_coverage_complete: bool = False,
    trigger_coverage_complete: bool = False,
    protocol_return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Optional[D03PriorityPolicy] = None,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = "",
) -> Dict[str, IPSliceResult]:
    """Evaluate multiple D03 units, grouped by subject (frozen D03 §4, §11).

    Returns a mapping of subject_ref -> IPSliceResult.  Each unit gets
    exactly one L1 disposition; episode rollups are read-only views that
    preserve sibling flags (positive/boundary/not_evaluable independent).
    """
    expansions = expand_ip_expected_set(
        project_id=project_id, episodes=episodes,
        assignments=assignments, active_rules=active_rules,
        adherence_algorithms=adherence_algorithms,
        action_evidence=action_evidence,
        binding_mapping=binding_mapping)
    results: List[IPUnitResult] = []
    for eu in expansions.units:
        r = evaluate_ip_unit(
            project_id=project_id, expanded=eu,
            occurrences=occurrences, action_evidence=action_evidence,
            planned_actions=planned_actions, actual_actions=actual_actions,
            observations=observations,
            return_records=return_records,
            dispense_records=dispense_records,
            cm_conflict_rows=cm_conflict_rows,
            role_coverage=role_coverage,
            aggregation_policy=aggregation_policy,
            action_coverage_complete=action_coverage_complete,
            trigger_coverage_complete=trigger_coverage_complete,
            protocol_return_expectation=protocol_return_expectation,
            priority_policy=priority_policy,
            binding_mapping=binding_mapping, snapshot_id=snapshot_id)
        results.append(r)
    by_subject: Dict[str, List[IPUnitResult]] = {}
    for r in results:
        by_subject.setdefault(r.subject_ref, []).append(r)
    out: Dict[str, IPSliceResult] = {}
    for subj, urs in by_subject.items():
        subj_cands = [c for r in urs for c in r.r2_candidates]
        out[subj] = IPSliceResult(
            subject_ref=subj, unit_results=tuple(urs),
            r2_candidates=tuple(subj_cands),
            expected_set_hash=expansions.expected_set_hash,
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)
    return out
