"""D02 unit and rule evaluation authority."""

from .cm_types import *
from .cm_expected import *
from .cm_results import *

# ---------------------------------------------------------------------------
# Core evaluation: evaluate_cm_unit
# ---------------------------------------------------------------------------

def evaluate_cm_unit(
    *, project_id: str, expanded: CMUnitExpanded,
    evidence_records: Sequence[CMSemanticRecord] = (),
    strategy: Optional[MedicationMatchStrategy] = None,
    priority_policy: Optional[D02PriorityPolicy] = None,
    snapshot_id: str = "",
    ip_exposure_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
    relationship_coverage_complete: bool = False,
) -> CMUnitResult:
    """Evaluate one D02 CM expanded unit (frozen D02 §5).

    ``linkage_coverage_complete`` (default False = fail-closed) is the
    explicit accepted proof that the relevant AE/MH/diagnosis source
    coverage for this subject is complete.  An empty ``evidence_records``
    alone cannot prove a complete search with no matching event; a
    positive or definitive-negative indication conclusion requires this
    proof (frozen D02 §8).

    ``relationship_coverage_complete`` independently proves that the
    relevant accepted AE/MH/IP action sources are complete before an
    action-relationship rule may conclude positive or negative.  Explicit
    stable CM linkage, subject/site identity and a comparable day-level
    event date remain mandatory.
    """
    if strategy is None:
        raise CMSliceError("strategy is required for evaluate_cm_unit")
    episode = expanded.episode
    identity_binding = episode.identity_binding
    interval = expanded.interval
    unit = expanded.build_unit(project_id, strategy)
    unit_id = unit.unit_id

    # -- ingredient_resolution: mandatory not_evaluable, no candidate --
    if expanded.is_ingredient_resolution:
        src_ref = _make_source_record_ref(episode.source_locator)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=(
                "复方药物的某项成分尚未确认，无法评价该成分是否命中"
                "禁用或限制用药规则"),
            source_record_refs=(src_ref,))

    # -- CM/IP role conflict check (frozen D02 §3.1) --
    for ip_rec in ip_exposure_records:
        if ip_rec.locator.record_id == episode.source_locator.record_id:
            src_ref = _make_source_record_ref(episode.source_locator)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=(
                    "同一来源行同时映射为 CM 与 IP/EX，角色互斥冲突"),
                source_record_refs=(src_ref,))

    rule = expanded.rule
    if rule is not None:
        return _evaluate_rule_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, identity_binding=identity_binding,
            interval=interval, rule=rule, strategy=strategy,
            snapshot_id=snapshot_id,
            evidence_records=tuple(evidence_records)
                + tuple(ip_exposure_records),
            relationship_coverage_complete=relationship_coverage_complete)

    if expanded.risk_family == "indication_check":
        return _evaluate_indication_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, identity_binding=identity_binding,
            interval=interval, strategy=strategy,
            priority_policy=priority_policy, snapshot_id=snapshot_id,
            evidence_records=evidence_records,
            linkage_coverage_complete=linkage_coverage_complete)

    src_ref = _make_source_record_ref(episode.source_locator)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=(
            f"未识别的用药核查类型 {expanded.risk_family!r}，当前无法评价"),
        source_record_refs=(src_ref,))


def _evaluate_rule_unit(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy, snapshot_id: str,
    evidence_records: Sequence[CMSemanticRecord],
    relationship_coverage_complete: bool,
) -> CMUnitResult:
    """Evaluate a rule-match unit (prohibited/restricted/etc.).

    Phase applicability (§5.5): a confirmed study phase that is outside
    the rule's ``applicable_phases`` is ``not_applicable`` with no
    candidate/Query.  A missing or unconfirmed phase is ``not_evaluable``.
    Identity non-match (§6): a confirmed ingredient-exact binding that
    differs from an ingredient-exact rule target is a deterministic
    ``negative`` with a complete identity binding; category/product-type
    absence remains fail-closed.
    """
    ingredient = _find_ingredient(expanded, identity_binding)
    src_ref = _make_source_record_ref(episode.source_locator)
    rule_lineage = rule.rule_lineage

    # -- Phase applicability (§5.5): fail closed for every inconsistent
    # -- or unconfirmed phase state.  Only (confirmed=True, phase non-empty)
    # -- may proceed; confirmed phase outside applicable_phases is
    # -- not_applicable; all other states are not_evaluable.
    if episode.study_phase_confirmed and episode.study_phase.strip():
        if episode.study_phase.strip() not in rule.applicable_phases:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-phase-na",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=(
                    f"已确认研究阶段 {episode.study_phase!r} 不在规则 "
                    f"{rule.rule_id} 适用阶段 {list(rule.applicable_phases)} 内"))
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
    else:
        # Every other combination is not_evaluable: phase missing,
        # blank, or confirmed flag inconsistent with phase content.
        if not episode.study_phase.strip():
            phase_note = "研究阶段缺失或为空，无法判定规则适用性"
        else:
            phase_note = (
                f"研究阶段 {episode.study_phase!r} 未获确认，"
                f"无法判定规则适用性")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-phase-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=phase_note)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=phase_note,
            evidence=(ev,), source_record_refs=(src_ref,))

    match = _match_rule_to_ingredient(rule, ingredient)

    # Fail-closed: target granularity not satisfiable -> not_evaluable.
    if not match.target_granularity_satisfied:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-granularity",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=identity_binding.evidence_locator,
            evidence_role="medication_identity",
            rule_lineage=rule_lineage,
            uncertainty_note=match.fail_closed_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=match.fail_closed_reason,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Definitive ingredient-exact non-match -> negative (complete identity).
    if not match.matched and rule.target_kind == TARGET_KIND_INGREDIENT:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-exact-nomatch",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"已确认成分 {ingredient.ingredient!r} 与规则目标成分 "
                f"{rule.target_value!r} 精确不同，身份完整可核实"))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    if not match.matched:
        overlap = _compare_interval_to_window(interval, rule)
        if (overlap.comparable and overlap.outside
                and not overlap.possibly_overlap):
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-outside",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=overlap.boundary_reason or "窗口外")
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NEGATIVE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
        ne_reason = (
            f"类别/产品类型未命中规则 {rule.rule_id}，"
            f"但身份不足以判 negative：{match.match_reason}")
        if not overlap.comparable:
            ne_reason = overlap.boundary_reason
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-unmatched",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # A blocking restricted-condition coverage gap outranks a temporal
    # boundary.  Check only the fail-closed state here; confirmed met/unmet
    # remains materialized after the interval is known to overlap.
    if rule.is_restricted:
        cond_state, cond_reason = _check_restricted_conditions(rule, episode)
        if cond_state == RESTRICTED_COND_UNEVALUABLE:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ne",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=cond_reason)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=cond_reason,
                evidence=(ev,), source_record_refs=(src_ref,))
        if cond_state == RESTRICTED_COND_BOUNDARY:
            return _build_rule_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                episode=episode, rule=rule, strategy=strategy,
                identity_binding=identity_binding, interval=interval,
                boundary_reason=cond_reason, src_ref=src_ref,
                rule_lineage=rule_lineage, snapshot_id=snapshot_id)

    # Matched: check interval overlap.
    overlap = _compare_interval_to_window(interval, rule)
    if not overlap.comparable:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-interval-ne",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=overlap.boundary_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=overlap.boundary_reason,
            evidence=(ev,), source_record_refs=(src_ref,))
    if overlap.possibly_overlap and not overlap.inside:
        return _build_rule_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            boundary_reason=overlap.boundary_reason,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)
    if overlap.outside:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-outside-matched",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note="命中成分/类别但区间在适用窗外")
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Matched AND inside window: evaluate the rule-specific medical contract.
    if rule.is_record_consistency:
        return _evaluate_record_consistency_rule(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)
    if rule.is_action_relationship:
        return _evaluate_action_relationship_rule(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id, evidence_records=evidence_records,
            relationship_coverage_complete=relationship_coverage_complete)

    # Matched AND inside window: positive (prohibited) or check conditions
    # (restricted/allowed-condition rules).
    return _build_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        match_reason=match.match_reason, src_ref=src_ref,
        rule_lineage=rule_lineage, snapshot_id=snapshot_id)


def _canonical_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _canonical_record_value(field_name: str, value: str) -> Optional[str]:
    """Return a comparable canonical value or None when it is insufficient."""
    if not value.strip():
        return None
    if field_name in ("start", "end"):
        if field_name == "end" and _canonical_text(value) == "ongoing":
            return "ongoing"
        normalized = normalize_partial_date(value)
        if not normalized.normalized or _nv_precision(normalized) != "day":
            return None
        return str(normalized.normalized)
    return _canonical_text(value)


def _not_evaluable_rule_result(
    *, unit_id: str, episode: MedicationEpisode, src_ref: SourceRecordRef,
    rule_lineage: str, reason: str, locator: Optional[SourceLocator] = None,
    evidence_role: str = "recorded_cm",
) -> CMUnitResult:
    ev = _make_evidence_item(
        evidence_id=f"ev-{unit_id}-rule-ne",
        polarity=L1bEvidencePolarity.CONTEXT,
        locator=locator or episode.source_locator,
        evidence_role=evidence_role, rule_lineage=rule_lineage,
        uncertainty_note=reason)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=reason, evidence=(ev,),
        source_record_refs=(src_ref,))


def _negative_rule_result(
    *, unit_id: str, episode: MedicationEpisode, src_ref: SourceRecordRef,
    rule_lineage: str, reason: str,
    evidence_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    evidence: List[EvidenceItem] = [
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-rule-negative",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator, evidence_role="recorded_cm",
            rule_lineage=rule_lineage, uncertainty_note=reason)
    ]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-related-negative-{index}",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=reason)
        for index, record in enumerate(evidence_records)
    )
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NEGATIVE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        evidence=tuple(evidence), source_record_refs=(src_ref,))


def _evaluate_record_consistency_rule(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str,
) -> CMUnitResult:
    actual_raw = _episode_record_value(episode, rule.comparison_field)
    actual = _canonical_record_value(rule.comparison_field, actual_raw)
    expected = tuple(
        _canonical_record_value(rule.comparison_field, value)
        for value in rule.expected_values)
    if actual is None or any(value is None for value in expected):
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"{label}缺失或精度不足，无法与方案要求可靠比较")
    if actual in expected:
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        return _negative_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"{label}与方案规则 {rule.rule_id} 的要求一致")
    label = _RECORD_FIELD_LABELS[rule.comparison_field]
    reason = (
        f"{label}记录为 {actual_raw!r}，与方案规则 {rule.rule_id} 的"
        f"允许值 {list(rule.expected_values)!r} 明确不一致")
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id,
        subtype=POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY,
        match_reason=reason)


def _record_inside_episode_window(
    record: CMSemanticRecord, interval: CMIntervalDescriptor,
) -> Optional[bool]:
    event = record.normalized_date()
    start = interval.normalized_start()
    end = interval.normalized_end()
    if any(value is None or _nv_precision(value) != "day"
           for value in (event, start, end)):
        return None
    event_value = str(event.normalized)
    return str(start.normalized) <= event_value <= str(end.normalized)


def _evaluate_action_relationship_rule(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str,
    evidence_records: Sequence[CMSemanticRecord],
    relationship_coverage_complete: bool,
) -> CMUnitResult:
    if not relationship_coverage_complete:
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason="AE/MH/IP 处置关系来源覆盖不完整，无法作出确定结论")

    related_by_locator: Dict[str, CMSemanticRecord] = {}
    for record in evidence_records:
        if (record.subject_ref == episode.subject_ref
                and record.site_ref == episode.site_ref
                and record.role == rule.related_role
                and record.linked_cm_source_event_key
                    == episode.stable_cm_source_event_key
                and (not rule.related_concept
                     or record.concept == rule.related_concept)):
            related_by_locator[record.locator.locator_id()] = record
    related = tuple(related_by_locator[key]
                    for key in sorted(related_by_locator))
    if not related:
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=("未找到带有明确 CM 关联键的处置记录，不能把缺少关联"
                    "自动判为处置关系冲突"))
    for record in related:
        if record.relationship_confirmation != CONFIRMATION_CONFIRMED:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="处置记录与 CM 的关联尚未确认，无法评价",
                locator=record.locator, evidence_role=record.role)
        inside = _record_inside_episode_window(record, interval)
        if inside is None:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="处置记录日期缺失或精度不足，无法确认同一时间窗",
                locator=record.locator, evidence_role=record.role)
        if not inside:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="关联处置记录不在本次用药时间窗内，无法判定同窗关系",
                locator=record.locator, evidence_role=record.role)

    expected = {_canonical_text(action) for action in rule.expected_actions}
    matching = tuple(
        record for record in related
        if _canonical_text(record.action_value) in expected)
    conflicting = tuple(record for record in related if record not in matching)
    if matching and conflicting:
        reason = "同一用药关联中同时存在一致与冲突的处置记录，当前无法唯一判断"
        return _build_rule_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            boundary_reason=reason, src_ref=src_ref,
            rule_lineage=rule_lineage, snapshot_id=snapshot_id,
            related_records=related)
    if matching:
        return _negative_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"用药与 {rule.related_role} 处置记录关系一致",
            evidence_records=matching)

    actual_actions = sorted({record.action_value for record in conflicting})
    reason = (
        f"同一用药及时间窗内的 {rule.related_role} 处置记录为"
        f" {actual_actions!r}，与规则 {rule.rule_id} 要求的"
        f" {list(rule.expected_actions)!r} 明确冲突")
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id,
        subtype=POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT,
        match_reason=reason, related_records=conflicting)


RESTRICTED_COND_UNEVALUABLE = "unevaluable"
RESTRICTED_COND_MET = "met"
RESTRICTED_COND_UNMET = "unmet"
RESTRICTED_COND_BOUNDARY = "boundary"


def _check_restricted_conditions(
    rule: ProtocolMedicationRule, episode: MedicationEpisode,
) -> Tuple[str, str]:
    """Check restricted-rule allowed conditions (four-state).

    Returns ``(state, reason)`` where state is one of:
    - ``met``: the allowed condition is confirmed satisfied -> negative.
    - ``unmet``: the allowed condition is confirmed NOT satisfied -> positive.
    - ``unevaluable``: role/evidence missing or an unknown condition token
      -> not_evaluable (fail-closed).
    - ``boundary``: stable-treatment and new-start interpretations each have
      versioned source support and cannot yet be uniquely selected.

    Stable treatment requires explicit duration/stability AND
    dose/frequency-unchanged evidence; ``treatment_role_confirmed`` alone
    is insufficient.  Rescue/prophylaxis require a confirmed role.
    Unknown ``allowed_conditions`` tokens fail closed.
    """
    known_tokens = {"stable_treatment", "rescue", "prophylaxis"}
    conditions_to_check: List[str] = []
    if rule.allowed_conditions:
        conditions_to_check = list(rule.allowed_conditions)
        unknown = [c for c in conditions_to_check if c not in known_tokens]
        if unknown:
            return (RESTRICTED_COND_UNEVALUABLE,
                    f"未知的限制条件令牌 {unknown!r}，无法评价")
    elif rule.stable_treatment_exception:
        conditions_to_check = ["stable_treatment"]
    elif rule.rescue_exception:
        conditions_to_check = ["rescue"]
    elif rule.prophylaxis_exception:
        conditions_to_check = ["prophylaxis"]

    for cond in conditions_to_check:
        if cond == "stable_treatment":
            interpretations = {
                item.interpretation
                for item in episode.treatment_interpretation_evidence
            }
            if {"stable_treatment", "new_start"}.issubset(interpretations):
                return (
                    RESTRICTED_COND_BOUNDARY,
                    "稳定治疗与新启用两种解释均有来源支持，当前无法唯一确定",
                )
            if (not episode.treatment_role_confirmed
                    or not episode.stable_treatment_evidence_complete):
                return (RESTRICTED_COND_UNEVALUABLE,
                        "稳定治疗证据不完整（角色/时长/剂量频次未确认）")
            if not episode.stable_treatment_evidence_sufficient:
                return (RESTRICTED_COND_UNMET,
                        "已完成稳定治疗条件核对，但时长、稳定性或剂量频次条件不满足")
        elif cond == "rescue":
            if not episode.treatment_role_confirmed:
                return (RESTRICTED_COND_UNEVALUABLE, "治疗角色未确认")
            if not episode.is_rescue:
                return (RESTRICTED_COND_UNMET, "抢救角色未满足")
        elif cond == "prophylaxis":
            if not episode.treatment_role_confirmed:
                return (RESTRICTED_COND_UNEVALUABLE, "治疗角色未确认")
            if not episode.is_prophylaxis:
                return (RESTRICTED_COND_UNMET, "预防角色未满足")
    return RESTRICTED_COND_MET, ""


def _build_explicit_rule_positive_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str, subtype: str,
    match_reason: str,
    related_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    """Materialize a rule-backed positive with complete provenance."""
    audience = positive_subtype_audience_label(subtype)
    priority = rule.priority_on_hit
    risk_family = _rule_risk_family(rule)
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=subtype,
        rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
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
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=match_reason),
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-identity",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=identity_binding.evidence_locator,
            evidence_role="medication_identity", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"词典 {identity_binding.dictionary_name}/"
                f"{identity_binding.dictionary_version}")),
    ]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-related-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=match_reason)
        for index, record in enumerate(related_records)
    )
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, identity_binding.evidence_locator,
        *(record.locator for record in related_records))
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode, rule=rule,
        identity_binding=identity_binding,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids,
        relationship_record=(related_records[0] if related_records else None))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=tuple(evidence),
        source_record_refs=(src_ref,), query_refs=(query,),
        journey_markers=(jm,), positive_subtype=subtype,
        audience_label=audience)


def _build_rule_positive_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, match_reason: str,
    src_ref: SourceRecordRef, rule_lineage: str, snapshot_id: str,
) -> CMUnitResult:
    """Build a positive result for a matched prohibited/restricted rule."""
    if rule.is_prohibited:
        subtype = POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH
    elif rule.is_restricted:
        cond_state, cond_reason = _check_restricted_conditions(rule, episode)
        if cond_state == RESTRICTED_COND_UNEVALUABLE:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ne",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=cond_reason)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=cond_reason,
                evidence=(ev,), source_record_refs=(src_ref,))
        if cond_state == RESTRICTED_COND_BOUNDARY:
            return _build_rule_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                episode=episode, rule=rule, strategy=strategy,
                identity_binding=identity_binding, interval=interval,
                boundary_reason=cond_reason, src_ref=src_ref,
                rule_lineage=rule_lineage, snapshot_id=snapshot_id)
        if cond_state == RESTRICTED_COND_MET:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ok",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note="限制规则允许条件已满足")
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NEGATIVE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
        # cond_state == RESTRICTED_COND_UNMET -> positive
        subtype = POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH
    else:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-rule-allowed",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=f"规则类型 {rule.rule_type} 允许")
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id, subtype=subtype,
        match_reason=match_reason)


def _build_rule_boundary_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, boundary_reason: str,
    src_ref: SourceRecordRef, rule_lineage: str, snapshot_id: str,
    related_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    """Build a boundary result for a matched rule with an unresolved interval."""
    risk_family = _rule_risk_family(rule)
    signal_type = (f"{rule.rule_type}_boundary")
    priority = MONITORING_PRIORITY_UNKNOWN
    if rule.is_prohibited:
        audience = "禁用药使用待核实（边界）"
    elif rule.is_restricted:
        audience = "限制用药条件待核实（边界）"
    elif rule.is_record_consistency:
        audience = "用药信息待核实（边界）"
    else:
        audience = "用药与处置记录关系待核实（边界）"
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type,
        rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        match_reason=boundary_reason, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-boundary",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="recorded_cm", rule_lineage=rule_lineage,
        uncertainty_note=boundary_reason)]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-boundary-related-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=boundary_reason)
        for index, record in enumerate(related_records))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.BOUNDARY,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=tuple(evidence),
        source_record_refs=(src_ref,), journey_markers=(jm,),
        boundary_reason=boundary_reason, audience_label=audience)

def _evaluate_indication_unit(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, strategy: MedicationMatchStrategy,
    priority_policy: Optional[D02PriorityPolicy],
    snapshot_id: str, evidence_records: Sequence[CMSemanticRecord],
    linkage_coverage_complete: bool = False,
) -> CMUnitResult:
    """Evaluate an indication-check unit (frozen D02 §5.1, §8).

    Required-phase gate: a missing, blank, or unconfirmed research phase
    is ``not_evaluable``; no candidate/Query/cross-domain ref is produced
    until the stage is a verifiable input (§5.1/§5.2/§5.4).

    Coverage gate: ``linkage_coverage_complete`` must be True for a
    positive or definitive-negative indication conclusion.  An empty
    ``evidence_records`` alone cannot prove a complete search.

    Role gate: prophylaxis/rescue can be negative only when the role is
    confirmed; an unconfirmed treatment role is ``not_evaluable``.

    Subtypes (§5.1): ``treatment_without_event_record`` (subtype 2)
    requires explicit evidence that the purpose is treatment of a
    study-period new/worsened event plus complete linkage coverage;
    other confirmed mappable role-confirmed but unexplained indications
    use ``medication_indication_unexplained`` (subtype 1).  Subtype 2
    takes precedence only when its stronger facts are present.
    """
    src_ref = _make_source_record_ref(episode.source_locator)
    rule_lineage = D02_RULE_LINEAGE_DEFAULT

    # Required-phase gate (§5.1/§5.2/§5.4): a missing, blank, or
    # unconfirmed research phase is not_evaluable; no candidate, Query,
    # or cross-domain ref may be produced until the stage is verifiable.
    if not (episode.study_phase_confirmed and episode.study_phase.strip()):
        if not episode.study_phase.strip():
            ne_reason = "研究阶段缺失或为空，无法评价用药依据"
        else:
            ne_reason = (
                f"研究阶段 {episode.study_phase!r} 未获确认，无法评价用药依据")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-phase-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    assessment = _assess_indication(episode, evidence_records, strategy)

    # Temporally uninterpretable same-concept record -> not_evaluable.
    if assessment.temporally_uninterpretable:
        ne_reason = (
            "存在与适应证同概念的记录，但其日期无法解析，"
            "不能确定时间关系，暂无法评价")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-temporal-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # No mappable indication: coverage gap / not_evaluable.
    if not assessment.has_mappable_indication:
        if not episode.indication_text.strip():
            ne_reason = "适应证信息缺失，不等于无适应证，不自动生成无用药依据结论"
        elif assessment.indication_vague:
            ne_reason = "适应证记录不具体（笼统/不可映射），不反向判漏报"
        else:
            ne_reason = "适应证不可映射，无法判定用药依据"
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-indication-gap",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Coverage gate: incomplete relevant-source coverage -> not_evaluable.
    if not linkage_coverage_complete:
        ne_reason = (
            "相关 AE/MH/诊断来源覆盖不完整，不能证明已完整检索，"
            "暂无法对用药依据作出确定结论")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-coverage-incomplete",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Mappable indication WITH matching same-subject event record -> negative.
    if assessment.matching_event_records:
        match_evs = tuple(
            _make_evidence_item(
                evidence_id=f"ev-{unit_id}-match-{i}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=rec.locator, evidence_role=rec.role,
                rule_lineage=rule_lineage,
                uncertainty_note="适应证与已记录医学事件一致")
            for i, rec in enumerate(assessment.matching_event_records))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=match_evs, source_record_refs=(src_ref,))

    # Mappable indication, NO matching event record, coverage complete.
    # Role gate: unconfirmed treatment role -> not_evaluable.
    if not assessment.treatment_role_confirmed:
        ne_reason = "治疗角色未确认，无法判定用药依据是否成立"
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-role-unconfirmed",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Confirmed prophylaxis/rescue role -> negative, no auto under-reporting.
    if assessment.is_prophylaxis_or_rescue:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-prophylaxis",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"治疗角色为 {episode.treatment_role}，不因缺 AE/MH 自动判漏报"))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Determine subtype: subtype 2 requires explicit treatment-of-study-event
    # evidence; otherwise subtype 1 (§5.1 precedence rule).
    if assessment.is_treatment_of_study_event:
        subtype = POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD
    else:
        subtype = POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED
    audience = positive_subtype_audience_label(subtype)
    risk_family = "indication_check"
    signal_type = subtype
    # Priority: from versioned policy when supplied; else unknown (not medium).
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(subtype)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type,
        rule=None, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        match_reason=(
            f"用药适应证 {assessment.indication_concept} 无对应 AE/MH/诊断记录"),
        positive_subtype=subtype, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    ev = _make_evidence_item(
        evidence_id=f"ev-{unit_id}-indication-positive",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="recorded_cm", rule_lineage=rule_lineage,
        uncertainty_note=(
            f"用药 {identity_binding.original_name} 对应适应证 "
            f"{assessment.indication_concept}，未找到对应 AE/MH/诊断"))
    # Query provenance: CM source + identity evidence + indication locator.
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, identity_binding.evidence_locator,
        episode.indication_source_locator)
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode, rule=None,
        identity_binding=identity_binding,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids)
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    cm_ref = _build_cm_indication_ref(
        evidence_ref_id=f"cer-{unit_id}", producer_unit_id=unit_id,
        episode=episode, indication_assessment=assessment)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=(ev,),
        source_record_refs=(src_ref,), query_refs=(query,),
        journey_markers=(jm,),
        cross_domain_evidence_refs=(cm_ref,),
        positive_subtype=subtype, audience_label=audience)


__all__ = [name for name in globals() if not name.startswith("__")]
