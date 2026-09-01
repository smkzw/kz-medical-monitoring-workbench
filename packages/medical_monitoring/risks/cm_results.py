"""D02 unit results, Query drafts, evidence, and Journey markers."""

from .cm_types import *
from .cm_expected import *

# ---------------------------------------------------------------------------
# CMUnitResult (frozen D02 §2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMUnitResult:
    """The evaluation outcome for one D02 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol AND can
    materialize a full ``UnitEvaluation`` for the CoverageLedger.
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
    cross_domain_evidence_refs: Tuple[CrossDomainEvidenceRef, ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise CMSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise CMSliceError(
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
        object.__setattr__(self, "cross_domain_evidence_refs",
                           tuple(self.cross_domain_evidence_refs))

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
# Episode rollup (frozen D02 §4.1 step 4, §11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMEpisodeRollup:
    """Read-only episode rollup preserving all child unit ids and flags."""

    episode_id: str
    subject_ref: str
    child_unit_ids: Tuple[str, ...]
    has_positive: bool
    has_boundary: bool
    has_not_evaluable: bool
    has_negative: bool
    source_record_count: int

# ---------------------------------------------------------------------------
# Query construction (frozen D02 §9.3)
# ---------------------------------------------------------------------------

_RECORD_FIELD_LABELS: Dict[str, str] = {
    "dose": "剂量",
    "dose_unit": "剂量单位",
    "route": "给药途径",
    "frequency": "给药频次",
    "start": "开始日期",
    "end": "结束日期",
    "treatment_role": "治疗角色",
}


def _episode_record_value(episode: MedicationEpisode, field_name: str) -> str:
    if field_name == "start":
        return episode.interval.cm_start
    if field_name == "end":
        return "ongoing" if episode.interval.ongoing else episode.interval.cm_end
    return str(getattr(episode, field_name, ""))


def _target_kind_label(kind: str) -> str:
    return {TARGET_KIND_INGREDIENT: "成分", TARGET_KIND_CATEGORY: "类别",
            TARGET_KIND_PRODUCT_TYPE: "产品类型"}.get(kind, kind)


def _match_reason_finding(rule: ProtocolMedicationRule) -> str:
    if rule.target_kind == TARGET_KIND_INGREDIENT:
        return f"含目标成分 {rule.target_value}"
    if rule.target_kind == TARGET_KIND_CATEGORY:
        return f"属于目标类别 {rule.target_value}"
    if rule.target_kind == TARGET_KIND_PRODUCT_TYPE:
        return f"属于目标产品类型 {rule.target_value}"
    return "命中目标"


def _query_text(
    *, subtype: str, subject_ref: str, episode: MedicationEpisode,
    rule: Optional[ProtocolMedicationRule],
    identity_binding: MedicationIdentityBinding,
    relationship_record: Optional[CMSemanticRecord] = None,
) -> Tuple[str, str, str]:
    """Build the three-part Chinese Query text (frozen D02 §9.3)."""
    interval = episode.interval
    start_txt = interval.cm_start or "（开始日期缺失）"
    end_txt = "持续中" if interval.ongoing else (interval.cm_end or "（结束日期缺失）")
    cm_locator = episode.source_locator.locator_id()
    if subtype in (POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
                   POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH):
        r = rule
        basis = (f"方案规则 {r.rule_id} 规定{r.applicable_phases[0]}阶段"
                 f"{'禁用' if r.is_prohibited else '限制'}目标"
                 f"{_target_kind_label(r.target_kind)}"
                 f"（条款 {r.clause_locator}）。")
        finding = (f"参与者 {subject_ref} 在 {start_txt} 至 {end_txt} 使用"
                   f"{identity_binding.original_name}；受控绑定"
                   f"{identity_binding.dictionary_name}-"
                   f"{identity_binding.dictionary_version} 显示其"
                   f"{_match_reason_finding(r)}，记录定位 {cm_locator}。")
        action = ("请核实该用药是否符合方案要求以及是否构成方案偏离；"
                  "如需，请按相应流程处理。")
        return basis, finding, action
    if subtype in (POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
                   POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED):
        basis = "治疗用药通常应与相应医学事件或诊断记录一致。"
        indication_txt = episode.indication_text or "（适应证未具体记录）"
        finding = (f"参与者 {subject_ref} 在 {start_txt} 至 {end_txt} 使用"
                   f"{identity_binding.original_name} 治疗 {indication_txt}；"
                   f"当前 AE/MH/诊断中未找到可对应记录。"
                   f"记录定位 {cm_locator}。")
        action = ("请核实用药原因及 AE/MH/诊断记录是否完整，"
                  "并按核实结果补充或更正。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY:
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        actual = _episode_record_value(episode, rule.comparison_field)
        expected = "、".join(rule.expected_values)
        basis = (f"方案规则 {rule.rule_id}（条款 {rule.clause_locator}）要求"
                 f"{label}为 {expected}。")
        finding = (f"参与者 {subject_ref} 的 {identity_binding.original_name}"
                   f"{label}记录为 {actual}，与方案要求不一致。"
                   f"记录定位 {cm_locator}。")
        action = ("请核实用药信息是否准确以及是否构成方案偏离；"
                  "如需，请按核实结果更正并按相应流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT:
        expected = "、".join(rule.expected_actions)
        basis = (f"方案规则 {rule.rule_id}（条款 {rule.clause_locator}）要求"
                 f"相关处置为 {expected}。")
        actual = (relationship_record.action_value
                  if relationship_record is not None else "（记录不明确）")
        related_locator = (relationship_record.locator.locator_id()
                           if relationship_record is not None else "未定位")
        finding = (f"参与者 {subject_ref} 的 {identity_binding.original_name} 用药"
                   f"与 {rule.related_role} 处置记录存在冲突；处置记录为"
                   f" {actual}。CM 定位 {cm_locator}，关联记录定位"
                   f" {related_locator}。")
        action = ("请核实用药与处置记录的关系以及是否构成方案偏离；"
                  "如需，请按核实结果补充或更正并按相应流程处理。")
        return basis, finding, action
    raise CMSliceError(f"no Query template for subtype {subtype!r}")


def _build_query_ref(
    *, query_id: str, unit_id: str, subtype: str, subject_ref: str,
    episode: MedicationEpisode, rule: Optional[ProtocolMedicationRule],
    identity_binding: MedicationIdentityBinding, candidate_id: str,
    source_locator_ids: Sequence[str],
    relationship_record: Optional[CMSemanticRecord] = None,
) -> QueryDraftRef:
    basis_body, finding_body, action_body = _query_text(
        subtype=subtype, subject_ref=subject_ref, episode=episode,
        rule=rule, identity_binding=identity_binding,
        relationship_record=relationship_record)
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=f"依据：{basis_body}",
        finding=f"发现：{finding_body}",
        action=f"行动项：{action_body}",
        source_locator_ids=tuple(source_locator_ids),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Cross-domain evidence (frozen D02 §3.3, §8)
# ---------------------------------------------------------------------------

def _build_cm_indication_ref(
    *, evidence_ref_id: str, producer_unit_id: str,
    episode: MedicationEpisode,
    indication_assessment: _IndicationAssessment,
) -> CrossDomainEvidenceRef:
    """Build a CrossDomainEvidenceRef(role=cm_indication) for D01 (§8)."""
    locator = episode.indication_source_locator or episode.source_locator
    context: Dict[str, Any] = {
        "subject_ref": episode.subject_ref,
        "site_ref": episode.site_ref,
        "treatment_role": episode.treatment_role,
        "indication_text": episode.indication_text,
        "indication_concept": indication_assessment.indication_concept,
        "ingredient_status": (
            "confirmed" if episode.identity_binding.confirmed_ingredients
            else "unresolved"),
        "original_name": episode.identity_binding.original_name,
    }
    ch = cross_domain_evidence_content_hash(
        source_locator=locator, evidence_role="cm_indication",
        claim_scope="treatment", context_payload=context)
    return CrossDomainEvidenceRef(
        evidence_ref_id=evidence_ref_id, producer_domain=D02_DOMAIN,
        consumer_domain="D01_aemh", evidence_role="cm_indication",
        source_locator=locator, producer_unit_id=producer_unit_id,
        content_hash=ch, claim_scope="treatment",
        context_payload=tuple(context.items()))


# ---------------------------------------------------------------------------
# Evidence / source-record / journey helpers
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
    """Return deduplicated sorted locator ids from the given locators,
    skipping None.  Used for Query source_locator_ids provenance (§9.3)."""
    ids: List[str] = []
    for loc in locators:
        if loc is not None:
            ids.append(loc.locator_id())
    return tuple(sorted(set(ids)))


def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _journey_marker(
    *, episode: MedicationEpisode, unit_id: str, risk_family: str,
    audience_label: str, monitoring_priority: str,
) -> Dict[str, Any]:
    interval = episode.interval
    return {
        "domain_track": "cm", "event_id": episode.episode_id,
        "subject_ref": episode.subject_ref, "start": interval.cm_start,
        "end": interval.cm_end, "ongoing": interval.ongoing,
        "episode_id": episode.episode_id, "unit_id": unit_id,
        "risk_family": risk_family, "audience_label": audience_label,
        "monitoring_priority": monitoring_priority,
        "source_locator_id": episode.source_locator.locator_id(),
        "display_label": episode.identity_binding.original_name,
    }


__all__ = [name for name in globals() if not name.startswith("__")]
