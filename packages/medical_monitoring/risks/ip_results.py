"""IP risk identity, expected-set and unit-result construction."""

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

# ---------------------------------------------------------------------------
# Identity helpers (frozen D03 §4)
# ---------------------------------------------------------------------------

def _d03_risk_classifier(
    *, episode: IPExposureEpisode, control_token: str,
    risk_family: str, signal_type: str,
) -> str:
    """Deterministic D03 classifier (stable; no versions/hashes/snapshots)."""
    return "|".join((
        "d03", risk_family, episode.episode_key,
        episode.actual_treatment_role or "none",
        control_token, signal_type,
    ))


def _d03_risk_scope(
    *, episode: IPExposureEpisode, window: IPWindowDescriptor,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
) -> List[str]:
    """Deterministic D03 scope/lineage dimensions (site, time precision,
    treatment role, phase, assignment/rule/mapping/algorithm version+hash)."""
    span_start = window.normalized_span_start()
    dp = span_start.detail if span_start else "none"
    parts: Set[str] = {
        f"site:{episode.site_ref}" if episode.site_ref else "site:",
        f"tw:{window.temporal_window_descriptor()}",
        f"dp:{dp}",
        f"role:{episode.actual_treatment_role or 'none'}",
        f"ph:{episode.study_phase or 'none'}",
        f"ua:{D03_UNIT_ALGO_VERSION}",
    }
    if assignment is not None:
        parts.add(f"asg:{assignment.assignment_id}/"
                  f"{assignment.content_hash}/"
                  f"{assignment.assignment_lineage}")
    else:
        parts.add("asg:none")
    if binding_mapping is not None:
        parts.add(f"map:{binding_mapping.version}/"
                  f"{binding_mapping.content_hash}")
    else:
        parts.add("map:none")
    if rule is not None:
        parts.add(f"rule:{rule.rule_id}/{rule.rule_version}/"
                  f"{rule.rule_content_hash}/{rule.rule_lineage}")
    else:
        parts.add("rule:none")
    if algorithm is not None:
        parts.add(f"alg:{algorithm.algorithm_id}/{algorithm.version}/"
                  f"{algorithm.content_hash}")
    else:
        parts.add("alg:none")
    return sorted(parts)


def _build_d03_risk_identity(
    *, project_id: str, episode: IPExposureEpisode,
    window: IPWindowDescriptor, control_token: str,
    risk_family: str, signal_type: str,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
) -> RiskIdentity:
    classifier = _d03_risk_classifier(
        episode=episode, control_token=control_token,
        risk_family=risk_family, signal_type=signal_type)
    scope = _d03_risk_scope(
        episode=episode, window=window, assignment=assignment,
        rule=rule, algorithm=algorithm, binding_mapping=binding_mapping)
    return make_risk_identity(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D03_DOMAIN, scope=scope, classifier=classifier)


def _d03_identity_detail(
    *, episode: IPExposureEpisode, identity: RiskIdentity,
    control_token: str, risk_family: str, signal_type: str,
) -> Dict[str, Any]:
    return {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": _d03_risk_classifier(
            episode=episode, control_token=control_token,
            risk_family=risk_family, signal_type=signal_type),
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_ip_episode_key": episode.episode_key,
        "full_locator_id": episode.source_locator.locator_id(),
    }


def _build_d03_candidate(
    *, project_id: str, episode: IPExposureEpisode,
    window: IPWindowDescriptor, control_token: str,
    risk_family: str, signal_type: str,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
    snapshot_id: str, monitoring_priority: str,
    match_reason: str, positive_subtype: str = "",
    audience_label: str = "",
) -> Tuple[RiskCandidate, RiskIdentity]:
    identity = _build_d03_risk_identity(
        project_id=project_id, episode=episode, window=window,
        control_token=control_token, risk_family=risk_family,
        signal_type=signal_type, assignment=assignment, rule=rule,
        algorithm=algorithm, binding_mapping=binding_mapping)
    detail: Dict[str, Any] = {
        "risk_family": risk_family,
        "control_item": control_token.split(":", 1)[0],
        "control_token": control_token,
        "signal_type": signal_type,
        "monitoring_priority": monitoring_priority,
        "match_reason": match_reason,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "treatment_role": episode.actual_treatment_role,
        "phase": episode.study_phase,
        "dose": episode.dose,
        "dose_unit": episode.dose_unit,
        "route": episode.route,
        "frequency": episode.frequency,
        "locator_id": episode.source_locator.locator_id(),
    }
    if assignment is not None:
        detail.update({
            "assignment_id": assignment.assignment_id,
            "assignment_lineage": assignment.assignment_lineage,
            "display_role_label": assignment.display_role_label,
        })
    if rule is not None:
        detail.update({
            "rule_id": rule.rule_id,
            "rule_version": rule.rule_version,
            "rule_clause_locator": rule.clause_locator,
            "rule_type": rule.rule_type,
        })
    if algorithm is not None:
        detail.update({
            "algorithm_id": algorithm.algorithm_id,
            "algorithm_version": algorithm.version,
            "metric_kind": algorithm.metric_kind,
            "window_id": algorithm.window_id,
        })
    detail.update(_d03_identity_detail(
        episode=episode, identity=identity, control_token=control_token,
        risk_family=risk_family, signal_type=signal_type))
    rule_lineage = (rule.rule_lineage if rule is not None
                    else D03_RULE_LINEAGE_DEFAULT)
    candidate = RiskCandidate.from_signal(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D03_DOMAIN, signal_type=signal_type,
        source_snapshot_id=snapshot_id, rule_activation_id=rule_lineage,
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)
    return candidate, identity


# ---------------------------------------------------------------------------
# Expected-set expansion (frozen D03 §4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPUnitExpanded:
    """One expanded expected EvaluationUnit seed for D03."""

    episode: IPExposureEpisode
    control_item: str
    control_token: str
    risk_family: str
    resolution: AssignmentResolution
    assignment: Optional[PlannedTreatmentAssignment] = None
    rule: Optional[ProtocolExposureRule] = None
    algorithm: Optional[AdherenceAlgorithm] = None
    action_type: str = ""
    trigger_key: str = ""
    window_override: Optional[IPWindowDescriptor] = None
    binding_mapping: Optional[AssignmentBindingMapping] = None

    @property
    def window(self) -> IPWindowDescriptor:
        if self.window_override is not None:
            return self.window_override
        return _episode_window(self.episode)

    def signal_type(self) -> str:
        return self.risk_family

    def build_unit(
        self, project_id: str,
        binding_mapping: Optional[AssignmentBindingMapping] = None,
    ) -> EvaluationUnit:
        if binding_mapping is None:
            binding_mapping = self.binding_mapping
        norm_concept = "|".join((
            self.episode.episode_key,
            self.episode.actual_treatment_role or "none",
            self.control_token,
            self.risk_family,
        ))
        scope_lineage = "|".join(_d03_risk_scope(
            episode=self.episode, window=self.window,
            assignment=self.assignment, rule=self.rule,
            algorithm=self.algorithm, binding_mapping=binding_mapping))
        return EvaluationUnit(
            project_id=project_id, domain_id=D03_DOMAIN,
            scope_type="subject", scope_key=self.episode.subject_ref,
            normalized_concept_or_rule_item=norm_concept,
            temporal_window=self.window.temporal_window_descriptor(),
            rule_or_knowledge_lineage=scope_lineage,
            unit_algorithm_version=D03_UNIT_ALGO_VERSION)


@dataclass(frozen=True)
class IPExpectedSetExpansion:
    """Result of expanding episodes + control items into the expected set."""

    units: Tuple[IPUnitExpanded, ...]
    project_id: str
    binding_mapping: Optional[AssignmentBindingMapping]
    unit_ids: Tuple[str, ...] = ()
    expected_set_hash: str = ""

    def __post_init__(self) -> None:
        ids = tuple(
            u.build_unit(self.project_id).unit_id
            for u in self.units)
        object.__setattr__(self, "unit_ids", ids)
        object.__setattr__(self, "expected_set_hash", _expected_set_hash(ids))

    @property
    def count(self) -> int:
        return len(self.units)


def _expected_set_hash(unit_ids: Sequence[str]) -> str:
    return "d03-eset-" + content_hash(sorted(set(unit_ids)))


def _control_token_for(
    control_item: str, *, episode: IPExposureEpisode,
    rule: Optional[ProtocolExposureRule] = None,
    algorithm: Optional[AdherenceAlgorithm] = None,
    assignment: Optional[PlannedTreatmentAssignment] = None,
    action_type: str = "",
    trigger_key: str = "",
) -> str:
    if control_item == CONTROL_ROLE_PHASE:
        assignment_id = (assignment.assignment_id
                         if assignment is not None else "none")
        return f"role_phase:{assignment_id}"
    if control_item == CONTROL_PLAN_ACTUAL:
        return f"plan_actual:{rule.rule_id}"
    if control_item == CONTROL_ADHERENCE:
        return f"adherence:{algorithm.algorithm_id}:{algorithm.window_id}"
    if control_item == CONTROL_ALLOWED_ACTION:
        return f"allowed_action:{rule.rule_id}:{action_type}"
    if control_item == CONTROL_MEDICAL_ACTION:
        return f"medical_action:{rule.rule_id}:{trigger_key}"
    if control_item == CONTROL_ACCOUNTABILITY:
        return (f"accountability:{algorithm.algorithm_id}:"
                f"{algorithm.window_id}")
    raise IPSliceError(f"unknown control item {control_item!r}")


def expand_ip_expected_set(
    *, project_id: str,
    episodes: Sequence[IPExposureEpisode],
    assignments: Sequence[PlannedTreatmentAssignment] = (),
    active_rules: Sequence[ProtocolExposureRule] = (),
    adherence_algorithms: Sequence[AdherenceAlgorithm] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    binding_mapping: Optional[AssignmentBindingMapping] = None,
) -> IPExpectedSetExpansion:
    """Expand D03 episodes + activated control items into the expected unit
    set (frozen D03 §4).  Every episode expands independently: role_phase
    (assignment), then each activated plan_actual rule, adherence/account-
    ability algorithm, allowed_action rule x action type, and medical_action
    rule x trigger event key.  No merging of roles/phases into one unit.
    """
    if not project_id.strip():
        raise IPSliceError("project_id is required")
    expanded: List[IPUnitExpanded] = []
    for episode in episodes:
        resolution = resolve_episode_assignment(
            episode=episode, assignments=assignments,
            binding_mapping=binding_mapping)
        assignment = resolution.assignment
        # 1. role_phase:<assignment_id>
        expanded.append(IPUnitExpanded(
            episode=episode, control_item=CONTROL_ROLE_PHASE,
            control_token=_control_token_for(
                CONTROL_ROLE_PHASE, episode=episode, assignment=assignment),
            risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ROLE_PHASE],
            resolution=resolution, assignment=assignment,
            binding_mapping=binding_mapping))
        # 2. plan_actual:<rule_id>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_PLAN_ACTUAL:
                continue
            expanded.append(IPUnitExpanded(
                episode=episode, control_item=CONTROL_PLAN_ACTUAL,
                control_token=_control_token_for(
                    CONTROL_PLAN_ACTUAL, episode=episode, rule=rule),
                risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_PLAN_ACTUAL],
                resolution=resolution, assignment=assignment, rule=rule,
                window_override=_rule_window(episode, rule),
                binding_mapping=binding_mapping))
        # 3./6. adherence / accountability per algorithm.
        for algorithm in adherence_algorithms:
            if algorithm.is_accountability_proxy:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ACCOUNTABILITY,
                    control_token=_control_token_for(
                        CONTROL_ACCOUNTABILITY, episode=episode,
                        algorithm=algorithm),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ACCOUNTABILITY],
                    resolution=resolution, assignment=assignment,
                    algorithm=algorithm,
                    window_override=_algorithm_window(episode, algorithm),
                    binding_mapping=binding_mapping))
            else:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ADHERENCE,
                    control_token=_control_token_for(
                        CONTROL_ADHERENCE, episode=episode,
                        algorithm=algorithm),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ADHERENCE],
                    resolution=resolution, assignment=assignment,
                    algorithm=algorithm,
                    window_override=_algorithm_window(episode, algorithm),
                    binding_mapping=binding_mapping))
        # 4. allowed_action:<rule_id>:<action>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_ALLOWED_ACTION:
                continue
            for action_type in rule.allowed_action_types:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ALLOWED_ACTION,
                    control_token=_control_token_for(
                        CONTROL_ALLOWED_ACTION, episode=episode, rule=rule,
                        action_type=action_type),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ALLOWED_ACTION],
                    resolution=resolution, assignment=assignment, rule=rule,
                    action_type=action_type,
                    window_override=_rule_window(episode, rule),
                    binding_mapping=binding_mapping))
        # 5. medical_action:<rule_id>:<source_event_key>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_MEDICAL_ACTION:
                continue
            keys = sorted({
                ev.stable_source_event_key for ev in action_evidence
                if ev.source_role == rule.trigger_role})
            if not keys:
                keys = ["none"]
            for key in keys:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_MEDICAL_ACTION,
                    control_token=_control_token_for(
                        CONTROL_MEDICAL_ACTION, episode=episode, rule=rule,
                        trigger_key=key),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_MEDICAL_ACTION],
                    resolution=resolution, assignment=assignment, rule=rule,
                    trigger_key=key,
                    window_override=_rule_window(episode, rule),
                    binding_mapping=binding_mapping))
    return IPExpectedSetExpansion(
        units=tuple(expanded), project_id=project_id,
        binding_mapping=binding_mapping)


# ---------------------------------------------------------------------------
# Evidence / source-record / Query helpers
# ---------------------------------------------------------------------------

def _make_evidence_item(
    *, evidence_id: str, polarity: str, locator: SourceLocator,
    evidence_role: str, rule_lineage: str,
    uncertainty_note: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id, polarity=polarity, locator=locator,
        evidence_role=evidence_role, rule_lineage=rule_lineage,
        uncertainty_note=uncertainty_note)


def _dedup_locator_ids(*locators: Optional[SourceLocator]) -> Tuple[str, ...]:
    """Return deduplicated sorted locator ids, skipping None."""
    ids: List[str] = []
    for loc in locators:
        if loc is not None:
            ids.append(loc.locator_id())
    return tuple(sorted(set(ids)))


def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _canonical_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _canonical_dose(value: str) -> Optional[Decimal]:
    """Parse a dose value as Decimal (exact), or None when unparseable."""
    if not value.strip():
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _canonical_record_value(field_name: str, value: str) -> Optional[str]:
    """Return a comparable canonical value or None when insufficient."""
    if not value.strip():
        return None
    if field_name in ("dose", "dose_after", "dose_before"):
        dec = _canonical_dose(value)
        if dec is None:
            return None
        return str(dec)
    return _canonical_text(value)


def _journey_marker(
    *, episode: IPExposureEpisode, unit_id: str,
    assignment: Optional[PlannedTreatmentAssignment],
    risk_family: str, audience_label: str, monitoring_priority: str,
    positive_subtype: str = "",
) -> Dict[str, Any]:
    return {
        "domain_track": "ip", "event_id": episode.episode_key,
        "subject_ref": episode.subject_ref,
        "start": episode.span_start, "end": episode.span_end,
        "ongoing": episode.span_ongoing,
        "episode_id": episode.episode_key, "unit_id": unit_id,
        "assignment_id": (assignment.assignment_id
                          if assignment is not None else ""),
        "treatment_role_token": episode.actual_treatment_role,
        "display_role_label": (assignment.display_role_label
                               if assignment is not None else ""),
        "disclosure_state": episode.disclosure_state,
        "dose": episode.dose, "dose_unit": episode.dose_unit,
        "route": episode.route, "frequency": episode.frequency,
        "risk_family": risk_family, "audience_label": audience_label,
        "monitoring_priority": monitoring_priority,
        "positive_subtype": positive_subtype,
        "source_locator_id": episode.source_locator.locator_id(),
    }


# ---------------------------------------------------------------------------
# IPUnitResult (frozen D03 §2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPUnitResult:
    """The evaluation outcome for one D03 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol AND can
    materialize a full ``UnitEvaluation`` for the ``CoverageLedger``.
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    monitoring_priority: str
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    not_evaluable_reason: str = ""
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    journey_markers: Tuple[Dict[str, Any], ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise IPSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise IPSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        object.__setattr__(self, "r2_candidates", tuple(self.r2_candidates))
        object.__setattr__(self, "risk_candidate_refs",
                           tuple(self.risk_candidate_refs))
        object.__setattr__(self, "risk_instance_refs",
                           tuple(self.risk_instance_refs))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "source_record_refs",
                           tuple(self.source_record_refs))
        object.__setattr__(self, "query_refs", tuple(self.query_refs))
        object.__setattr__(self, "journey_markers",
                           tuple(self.journey_markers))

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
        self, *, l0_status: str = L0CoverageStatus.COVERED,
        provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity in (L1bEvidencePolarity.SUPPORTING,
                               L1bEvidencePolarity.COUNTEREVIDENCE,
                               L1bEvidencePolarity.CONTEXT):
                if ev.polarity not in polarities:
                    polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(polarities),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Query construction (frozen D03 §8)
# ---------------------------------------------------------------------------

def _display_label(
    assignment: Optional[PlannedTreatmentAssignment],
) -> str:
    if assignment is not None and assignment.display_role_label.strip():
        return assignment.display_role_label.strip()
    return "研究药物"


def _query_text(
    *, subtype: str, subject_ref: str, episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    match_reason: str,
) -> Tuple[str, str, str]:
    """Build the three-part Chinese Query text (frozen D03 §8)."""
    label = _display_label(assignment)
    loc_id = episode.source_locator.locator_id()
    if subtype == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定计划剂量/剂型/途径/频次及给药"
                 f"窗口。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际暴露记录与方案计划"
                   f"不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实实际给药记录与方案计划；如属实，请确认是否构成"
                  "方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH:
        basis = (f"随机/治疗分组由 assignment {assignment.assignment_id}"
                 f"（版本 {assignment.assignment_lineage}）定义：治疗角色"
                 f"{assignment.treatment_role_token}，研究阶段"
                 f"{assignment.study_phase}。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际暴露角色或阶段与"
                   f"分组计划不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实受试者实际分组、随机信息与暴露记录；如属实，请确认"
                  "是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE:
        basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                 f"{algorithm.version}，窗口 {algorithm.window_id}）规定"
                 f"允许范围与计算口径。")
        finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} 的依从性"
                   f"计算结果超出允许范围：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实实际给药记录、算法分子分母及原始记录；如属实，请"
                  "确认是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定允许的给药调整及条件。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际给药调整与方案允许"
                   f"条件不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实给药调整的原因、前后剂量及方案允许条件；如属实，请"
                  "确认是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定医学触发事件 {rule.trigger_concept}"
                 f" 对应的预期处置。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际处置与医学触发事件"
                   f"不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实医学事件与给药处置记录的关系；如属实，请确认是否"
                  "构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY:
        if algorithm is not None and algorithm.is_accountability_proxy:
            basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                     f"{algorithm.version}，窗口 {algorithm.window_id}）将"
                     f"发放回收核算作为独立控制项，结果{ACCOUNTABILITY_PROXY_ANNOTATION}。")
            finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} "
                       f"按发放/回收核算，发放、回收与记录给药核算不一致："
                       f"{match_reason}。记录定位 {loc_id}。")
        else:
            basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                     f"{algorithm.version}，窗口 {algorithm.window_id}）将发放"
                     f"回收核算作为独立控制项。")
            finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} 的发放、"
                       f"回收与记录给药核算不一致：{match_reason}。记录定位 "
                       f"{loc_id}。")
        action = ("请核实发放、回收与实际给药记录；如属实，请确认是否构成"
                  "方案偏离并按项目流程处理。")
        return basis, finding, action
    raise IPSliceError(f"no Query template for subtype {subtype!r}")


def _build_query_ref(
    *, query_id: str, unit_id: str, subtype: str, subject_ref: str,
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    candidate_id: str,
    source_locator_ids: Sequence[str],
    match_reason: str,
) -> QueryDraftRef:
    basis_body, finding_body, action_body = _query_text(
        subtype=subtype, subject_ref=subject_ref, episode=episode,
        assignment=assignment, rule=rule, algorithm=algorithm,
        match_reason=match_reason)
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=f"依据：{basis_body}",
        finding=f"发现：{finding_body}",
        action=f"行动项：{action_body}",
        source_locator_ids=tuple(source_locator_ids),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Positive/boundary materialization helpers
# ---------------------------------------------------------------------------

def _build_positive_result(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    subtype: str, match_reason: str, snapshot_id: str,
    monitoring_priority: str, rule_lineage: str,
    source_locators: Sequence[SourceLocator],
    extra_evidence: Sequence[EvidenceItem] = (),
) -> IPUnitResult:
    """Materialize a D03 positive with complete provenance."""
    audience = positive_subtype_audience_label(subtype)
    episode = expanded.episode
    candidate, identity = _build_d03_candidate(
        project_id=project_id, episode=episode, window=expanded.window,
        control_token=expanded.control_token,
        risk_family=expanded.risk_family, signal_type=subtype,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        binding_mapping=expanded.binding_mapping, snapshot_id=snapshot_id,
        monitoring_priority=monitoring_priority,
        match_reason=match_reason, positive_subtype=subtype,
        audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-match",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=episode.source_locator,
            evidence_role="ip_exposure", rule_lineage=rule_lineage,
            uncertainty_note=match_reason),
    ]
    evidence.extend(extra_evidence)
    extra_locs: List[SourceLocator] = []
    seen_locs: Set[str] = {episode.source_locator.locator_id()}
    if expanded.assignment is not None \
            and expanded.assignment.source_locator is not None:
        extra_locs.append(expanded.assignment.source_locator)
        seen_locs.add(expanded.assignment.source_locator.locator_id())
    for loc in source_locators:
        if loc.locator_id() not in seen_locs:
            extra_locs.append(loc)
            seen_locs.add(loc.locator_id())
    for index, loc in enumerate(extra_locs):
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-src-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage,
            uncertainty_note="来源记录定位"))
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, *extra_locs)
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids, match_reason=match_reason)
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, assignment=expanded.assignment,
        risk_family=expanded.risk_family, audience_label=audience,
        monitoring_priority=monitoring_priority, positive_subtype=subtype)
    src_ref = _make_source_record_ref(episode.source_locator)
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=monitoring_priority,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=(src_ref,),
        query_refs=(query,), journey_markers=(jm,),
        positive_subtype=subtype, audience_label=audience)


def _build_boundary_result(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    boundary_reason: str, snapshot_id: str,
    rule_lineage: str, audience_suffix: str,
    source_locators: Sequence[SourceLocator] = (),
    extra_evidence: Sequence[EvidenceItem] = (),
) -> IPUnitResult:
    """Materialize a D03 boundary with a candidate and no Query."""
    episode = expanded.episode
    risk_family = expanded.risk_family
    signal_type = f"{risk_family}_boundary"
    audience = f"{audience_suffix}（边界）"
    candidate, identity = _build_d03_candidate(
        project_id=project_id, episode=episode, window=expanded.window,
        control_token=expanded.control_token,
        risk_family=risk_family, signal_type=signal_type,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        binding_mapping=expanded.binding_mapping, snapshot_id=snapshot_id,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        match_reason=boundary_reason, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-boundary",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=boundary_reason)]
    evidence.extend(extra_evidence)
    extra_locs: List[SourceLocator] = []
    seen_locs: Set[str] = {episode.source_locator.locator_id()}
    if expanded.assignment is not None \
            and expanded.assignment.source_locator is not None:
        extra_locs.append(expanded.assignment.source_locator)
        seen_locs.add(expanded.assignment.source_locator.locator_id())
    for loc in source_locators:
        if loc.locator_id() not in seen_locs:
            extra_locs.append(loc)
            seen_locs.add(loc.locator_id())
    for index, loc in enumerate(extra_locs):
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-bnd-src-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=boundary_reason))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, assignment=expanded.assignment,
        risk_family=risk_family, audience_label=audience,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN)
    src_ref = _make_source_record_ref(episode.source_locator)
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.BOUNDARY,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=(src_ref,),
        journey_markers=(jm,), boundary_reason=boundary_reason,
        audience_label=audience)


def _not_evaluable_result(
    *, unit_id: str, episode: IPExposureEpisode,
    reason: str, rule_lineage: str,
    extra_locators: Sequence[SourceLocator] = (),
) -> IPUnitResult:
    """Materialize a D03 not_evaluable (no candidate/Query)."""
    src_ref = _make_source_record_ref(episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-ne",
        polarity=L1bEvidencePolarity.CONTEXT,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=reason)]
    for index, loc in enumerate(extra_locators):
        if loc.locator_id() == episode.source_locator.locator_id():
            continue
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-ne-src-{index}",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=reason))
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=reason, evidence=tuple(evidence),
        source_record_refs=(src_ref,))


def _negative_result(
    *, unit_id: str, episode: IPExposureEpisode,
    rule_lineage: str, reason: str,
    extra_locators: Sequence[SourceLocator] = (),
) -> IPUnitResult:
    """Materialize a D03 negative with counterevidence."""
    src_ref = _make_source_record_ref(episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-negative",
        polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=reason)]
    for index, loc in enumerate(extra_locators):
        if loc.locator_id() == episode.source_locator.locator_id():
            continue
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-neg-src-{index}",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=reason))
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NEGATIVE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        evidence=tuple(evidence), source_record_refs=(src_ref,))
